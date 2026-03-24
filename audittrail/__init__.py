from audittrail.context import disabled

__all__ = ["AuditableMixin", "disabled"]
__version__ = "0.1.0"

default_app_config = "audittrail.apps.AuditTrailConfig"


def __getattr__(name):
    if name == "AuditableMixin":
        from audittrail.mixins import AuditableMixin
        return AuditableMixin
    raise AttributeError(f"module 'audittrail' has no attribute {name}")
