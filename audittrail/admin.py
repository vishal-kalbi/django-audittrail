import json

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html

from audittrail.models import AuditLog


class AuditLogInline(admin.TabularInline):
    """Inline admin to show audit history on a model's change page.

    Usage in your admin:
        class MyModelAdmin(admin.ModelAdmin):
            inlines = [AuditLogInline]
    """

    model = AuditLog
    extra = 0
    readonly_fields = (
        "action",
        "actor_username",
        "remote_addr",
        "changes_display",
        "timestamp",
    )
    fields = readonly_fields
    ordering = ("-timestamp",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("actor")

    def changes_display(self, obj):
        if not obj.changes:
            return "-"
        formatted = json.dumps(obj.changes, indent=2, default=str)
        return format_html("<pre style='margin:0;max-height:200px;overflow:auto'>{}</pre>", formatted)

    changes_display.short_description = "Changes"

    def get_parent_object(self, request, obj=None):
        """Helper to get the parent object from the URL."""
        return None

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "content_type":
            kwargs["queryset"] = ContentType.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AuditLogModelAdmin:
    """Mixin for ModelAdmin that adds an inline audit history tab.

    Usage:
        @admin.register(MyModel)
        class MyModelAdmin(AuditLogModelAdmin, admin.ModelAdmin):
            pass
    """

    def get_inlines(self, request, obj=None):
        inlines = list(super().get_inlines(request, obj))
        if obj is not None:
            # Only show inline on existing objects (not on add page)
            inlines.append(_ObjectAuditLogInline)
        return inlines


class _ObjectAuditLogInline(admin.TabularInline):
    """Internal inline that filters audit logs to the parent object."""

    model = AuditLog
    extra = 0
    readonly_fields = (
        "action",
        "actor_username",
        "remote_addr",
        "request_method",
        "request_path",
        "changes_display",
        "timestamp",
    )
    fields = readonly_fields
    ordering = ("-timestamp",)
    verbose_name = "audit log entry"
    verbose_name_plural = "audit history"
    fk_name = "content_type"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Filtering happens in the parent ModelAdmin via get_inlines
        return qs.select_related("actor").order_by("-timestamp")

    def changes_display(self, obj):
        if not obj.changes:
            return "-"
        formatted = json.dumps(obj.changes, indent=2, default=str)
        return format_html("<pre style='margin:0;max-height:200px;overflow:auto'>{}</pre>", formatted)

    changes_display.short_description = "Changes"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Standalone admin view for browsing all audit logs."""

    list_display = (
        "timestamp",
        "action",
        "content_type",
        "object_repr",
        "actor_username",
        "remote_addr",
    )
    list_filter = ("action", "content_type", "timestamp")
    search_fields = ("object_repr", "actor_username", "object_pk")
    readonly_fields = (
        "action",
        "content_type",
        "object_pk",
        "object_repr",
        "actor",
        "actor_username",
        "remote_addr",
        "request_path",
        "request_method",
        "changes_display",
        "timestamp",
    )
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True  # allow viewing detail page

    def has_delete_permission(self, request, obj=None):
        return False

    def changes_display(self, obj):
        if not obj.changes:
            return "-"
        formatted = json.dumps(obj.changes, indent=2, default=str)
        return format_html("<pre style='margin:0;max-height:300px;overflow:auto'>{}</pre>", formatted)

    changes_display.short_description = "Changes"
