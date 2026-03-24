import logging

logger = logging.getLogger("audittrail")


def _get_audit_config(sender):
    """Extract AuditTrail config from the model class."""
    audit_trail = getattr(sender, "AuditTrail", None)
    exclude_fields = set(getattr(audit_trail, "exclude_fields", []))
    mask_fields = set(getattr(audit_trail, "mask_fields", []))
    return exclude_fields, mask_fields


def _build_log_entry(instance, action, changes):
    """Build an AuditLog entry without saving it."""
    from django.contrib.contenttypes.models import ContentType

    from audittrail.context import (
        get_current_ip,
        get_current_request_method,
        get_current_request_path,
        get_current_user,
    )
    from audittrail.models import AuditLog

    user = get_current_user()
    ct = ContentType.objects.get_for_model(instance)

    try:
        object_repr = str(instance)[:200]
    except Exception:
        object_repr = f"{instance.__class__.__name__} pk={instance.pk}"

    return AuditLog(
        action=action,
        content_type=ct,
        object_pk=str(instance.pk),
        object_repr=object_repr,
        actor=user,
        actor_username=getattr(user, "username", "") if user else "",
        remote_addr=get_current_ip(),
        request_path=get_current_request_path(),
        request_method=get_current_request_method(),
        changes=changes,
    )


def handle_post_init(sender, instance, **kwargs):
    """Snapshot field values when a model instance is initialized."""
    from audittrail.diff import snapshot_fields

    try:
        exclude_fields, _ = _get_audit_config(sender)
        instance._audit_original_state = snapshot_fields(
            instance, exclude_fields=exclude_fields
        )
    except Exception:
        logger.exception("audittrail: failed to snapshot on post_init for %s", sender)


def handle_post_save(sender, instance, created, **kwargs):
    """Create an audit log entry after a model is saved."""
    from audittrail.context import is_audit_disabled
    from audittrail.diff import compute_create_snapshot, compute_diff, snapshot_fields
    from audittrail.models import AuditAction

    if is_audit_disabled():
        return

    try:
        exclude_fields, mask_fields = _get_audit_config(sender)
        current_state = snapshot_fields(instance, exclude_fields=exclude_fields)

        if created:
            changes = compute_create_snapshot(current_state, mask_fields=mask_fields)
            action = AuditAction.CREATE
        else:
            old_state = getattr(instance, "_audit_original_state", {})
            changes = compute_diff(old_state, current_state, mask_fields=mask_fields)
            if not changes:
                return  # no actual changes, skip logging
            action = AuditAction.UPDATE

        entry = _build_log_entry(instance, action, changes)
        entry.save()

        # Refresh snapshot after successful save
        instance._audit_original_state = current_state

    except Exception:
        logger.exception("audittrail: failed to create audit log for %s", sender)


def handle_post_delete(sender, instance, **kwargs):
    """Create an audit log entry after a model is deleted."""
    from audittrail.context import is_audit_disabled
    from audittrail.diff import compute_delete_snapshot, snapshot_fields
    from audittrail.models import AuditAction

    if is_audit_disabled():
        return

    try:
        exclude_fields, mask_fields = _get_audit_config(sender)
        old_state = getattr(instance, "_audit_original_state", {})
        if not old_state:
            old_state = snapshot_fields(instance, exclude_fields=exclude_fields)

        changes = compute_delete_snapshot(old_state, mask_fields=mask_fields)
        entry = _build_log_entry(instance, AuditAction.DELETE, changes)
        entry.save()

    except Exception:
        logger.exception("audittrail: failed to create delete audit log for %s", sender)
