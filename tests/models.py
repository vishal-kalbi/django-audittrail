from django.db import models

from audittrail import AuditableMixin


class SimpleModel(AuditableMixin, models.Model):
    """A simple test model with basic fields."""
    name = models.CharField(max_length=200)
    value = models.IntegerField(default=0)

    class Meta:
        app_label = "tests"

    def __str__(self):
        return self.name


class SensitiveModel(AuditableMixin, models.Model):
    """Test model with masked and excluded fields."""
    name = models.CharField(max_length=200)
    ssn = models.CharField(max_length=11)
    password = models.CharField(max_length=128)
    updated_at = models.DateTimeField(auto_now=True)

    class AuditTrail:
        exclude_fields = ["updated_at"]
        mask_fields = ["ssn", "password"]

    class Meta:
        app_label = "tests"

    def __str__(self):
        return self.name


class FKModel(AuditableMixin, models.Model):
    """Test model with a ForeignKey field."""
    name = models.CharField(max_length=200)
    related = models.ForeignKey(
        SimpleModel, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        app_label = "tests"

    def __str__(self):
        return self.name


class JsonFieldModel(AuditableMixin, models.Model):
    """Test model with a JSONField."""
    name = models.CharField(max_length=200)
    data = models.JSONField(default=dict)

    class Meta:
        app_label = "tests"

    def __str__(self):
        return self.name
