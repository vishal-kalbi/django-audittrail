try:
    from rest_framework import serializers

    from audittrail.models import AuditLog

    class AuditLogSerializer(serializers.ModelSerializer):
        content_type_name = serializers.SerializerMethodField()

        class Meta:
            model = AuditLog
            fields = [
                "id",
                "action",
                "content_type",
                "content_type_name",
                "object_pk",
                "object_repr",
                "actor",
                "actor_username",
                "remote_addr",
                "request_path",
                "request_method",
                "changes",
                "timestamp",
            ]
            read_only_fields = fields

        def get_content_type_name(self, obj):
            return f"{obj.content_type.app_label}.{obj.content_type.model}"

except ImportError:
    pass
