import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("create", "Create"),
                            ("update", "Update"),
                            ("delete", "Delete"),
                        ],
                        db_index=True,
                        max_length=10,
                    ),
                ),
                ("object_pk", models.CharField(max_length=255)),
                ("object_repr", models.CharField(blank=True, max_length=200)),
                ("actor_username", models.CharField(blank=True, max_length=150)),
                (
                    "remote_addr",
                    models.GenericIPAddressField(blank=True, null=True),
                ),
                ("request_path", models.CharField(blank=True, max_length=500)),
                ("request_method", models.CharField(blank=True, max_length=10)),
                ("changes", models.JSONField(default=dict)),
                (
                    "timestamp",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="audit_logs",
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={
                "verbose_name": "audit log",
                "verbose_name_plural": "audit logs",
                "ordering": ["-timestamp"],
                "default_permissions": ("add", "view"),
            },
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["content_type", "object_pk"],
                name="audittrail__content_87c4e1_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["actor", "timestamp"],
                name="audittrail__actor_i_a3f2b1_idx",
            ),
        ),
    ]
