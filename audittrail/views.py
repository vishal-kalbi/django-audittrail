try:
    from django.contrib.contenttypes.models import ContentType
    from rest_framework import permissions, status
    from rest_framework.decorators import action
    from rest_framework.response import Response
    from rest_framework.viewsets import GenericViewSet
    from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

    from audittrail.models import AuditLog
    from audittrail.serializers import AuditLogSerializer

    class AuditLogViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
        """Read-only viewset for browsing audit logs via API.

        Supports filtering via query params:
            ?action=create|update|delete
            ?actor=<user_id>
            ?object_pk=<pk>
            ?content_type=<app_label>.<model>
            ?from=<iso_datetime>
            ?to=<iso_datetime>

        Include in your router:
            from audittrail.views import AuditLogViewSet
            router.register('audit-logs', AuditLogViewSet, basename='auditlog')
        """

        serializer_class = AuditLogSerializer
        permission_classes = [permissions.IsAdminUser]

        def get_queryset(self):
            qs = AuditLog.objects.select_related("actor", "content_type").all()
            params = self.request.query_params

            if action_filter := params.get("action"):
                qs = qs.filter(action=action_filter)

            if actor_id := params.get("actor"):
                qs = qs.filter(actor_id=actor_id)

            if object_pk := params.get("object_pk"):
                qs = qs.filter(object_pk=object_pk)

            if content_type_str := params.get("content_type"):
                parts = content_type_str.split(".")
                if len(parts) == 2:
                    try:
                        ct = ContentType.objects.get(
                            app_label=parts[0], model=parts[1]
                        )
                        qs = qs.filter(content_type=ct)
                    except ContentType.DoesNotExist:
                        qs = qs.none()

            if from_dt := params.get("from"):
                qs = qs.filter(timestamp__gte=from_dt)

            if to_dt := params.get("to"):
                qs = qs.filter(timestamp__lte=to_dt)

            return qs

        @action(detail=False, methods=["get"], url_path="for-instance")
        def for_instance(self, request):
            """Get audit logs for a specific object.

            Query params:
                content_type: <app_label>.<model>  (required)
                object_pk: <pk>                     (required)
            """
            content_type_str = request.query_params.get("content_type")
            object_pk = request.query_params.get("object_pk")

            if not content_type_str or not object_pk:
                return Response(
                    {"detail": "Both 'content_type' and 'object_pk' query params are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            parts = content_type_str.split(".")
            if len(parts) != 2:
                return Response(
                    {"detail": "content_type must be in 'app_label.model' format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                ct = ContentType.objects.get(app_label=parts[0], model=parts[1])
            except ContentType.DoesNotExist:
                return Response(
                    {"detail": f"Unknown content type: {content_type_str}"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            qs = AuditLog.objects.filter(content_type=ct, object_pk=object_pk)
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)

        @action(detail=False, methods=["get"], url_path="by-user/(?P<user_pk>[^/.]+)")
        def by_user(self, request, user_pk=None):
            """Get all audit logs for a specific user."""
            qs = AuditLog.objects.filter(actor_id=user_pk)
            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)

    class AuditedModelViewSet:
        """Mixin for DRF ViewSets that automatically passes request context.

        Usage:
            class PatientViewSet(AuditedModelViewSet, ModelViewSet):
                queryset = Patient.objects.all()
                serializer_class = PatientSerializer

        This ensures the middleware context (user, IP) is available
        for audit logging on creates/updates/deletes through the API.
        """
        pass  # Middleware already handles context — this is a semantic marker

except ImportError:
    pass
