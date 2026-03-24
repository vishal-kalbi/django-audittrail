from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditAction(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"


class AuditQuerySet(models.QuerySet):
    def for_instance(self, obj):
        """Return all audit logs for a specific model instance."""
        ct = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=ct, object_pk=str(obj.pk))

    def by_user(self, user):
        """Return all audit logs created by a specific user."""
        return self.filter(actor=user)

    def for_model(self, model_class):
        """Return all audit logs for a specific model class."""
        ct = ContentType.objects.get_for_model(model_class)
        return self.filter(content_type=ct)

    def between(self, start, end):
        """Return audit logs within a time range (inclusive)."""
        return self.filter(timestamp__gte=start, timestamp__lte=end)

    def creates(self):
        return self.filter(action=AuditAction.CREATE)

    def updates(self):
        return self.filter(action=AuditAction.UPDATE)

    def deletes(self):
        return self.filter(action=AuditAction.DELETE)


class AuditLog(models.Model):
    # What happened
    action = models.CharField(max_length=10, choices=AuditAction.choices, db_index=True)

    # Which object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="audit_logs",
    )
    object_pk = models.CharField(max_length=255)
    object_repr = models.CharField(max_length=200, blank=True)

    # Who did it
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    actor_username = models.CharField(max_length=150, blank=True)

    # Where from
    remote_addr = models.GenericIPAddressField(null=True, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)

    # The diff
    changes = models.JSONField(default=dict)

    # When
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = AuditQuerySet.as_manager()

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["content_type", "object_pk"]),
            models.Index(fields=["actor", "timestamp"]),
        ]
        verbose_name = "audit log"
        verbose_name_plural = "audit logs"
        default_permissions = ("add", "view")  # no change/delete by default

    def __str__(self):
        return f"{self.get_action_display()} {self.object_repr} by {self.actor_username or 'system'}"
