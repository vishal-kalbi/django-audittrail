from django.apps import AppConfig


class AuditTrailConfig(AppConfig):
    name = "audittrail"
    verbose_name = "Audit Trail"
    default_auto_field = "django.db.models.BigAutoField"
