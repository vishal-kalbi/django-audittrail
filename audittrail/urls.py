try:
    from rest_framework.routers import DefaultRouter

    from audittrail.views import AuditLogViewSet

    router = DefaultRouter()
    router.register("audit-logs", AuditLogViewSet, basename="auditlog")

    urlpatterns = router.urls

except ImportError:
    urlpatterns = []
