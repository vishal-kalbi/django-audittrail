from django.db import models
from django.db.models.signals import post_delete, post_init, post_save


class AuditableMixin(models.Model):
    """Mixin that enables automatic audit logging for a Django model.

    Usage:
        class MyModel(AuditableMixin, models.Model):
            name = models.CharField(max_length=200)

            class AuditTrail:
                exclude_fields = ['updated_at']
                mask_fields = ['ssn', 'password']
    """

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Only register signals for concrete (non-abstract) models
        if not getattr(cls, "Meta", None) or not getattr(cls.Meta, "abstract", False):
            cls._register_audit_signals()

    @classmethod
    def _register_audit_signals(cls):
        """Register audit signal handlers for this model class."""
        from audittrail.handlers import (
            handle_post_delete,
            handle_post_init,
            handle_post_save,
        )

        # Use dispatch_uid to prevent duplicate registration
        uid_prefix = f"audittrail_{cls.__module__}_{cls.__qualname__}"

        post_init.connect(
            handle_post_init,
            sender=cls,
            dispatch_uid=f"{uid_prefix}_post_init",
        )
        post_save.connect(
            handle_post_save,
            sender=cls,
            dispatch_uid=f"{uid_prefix}_post_save",
        )
        post_delete.connect(
            handle_post_delete,
            sender=cls,
            dispatch_uid=f"{uid_prefix}_post_delete",
        )
