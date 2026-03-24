import datetime
import decimal
import uuid

from django.db import models
from django.db.models.fields.files import FieldFile


MASK_VALUE = "***"


def snapshot_fields(instance, fields=None, exclude_fields=None):
    """Capture current field values from a model instance.

    Returns a dict of {field_name: serializable_value}.
    """
    exclude_fields = set(exclude_fields or [])
    result = {}

    if fields is not None:
        target_fields = [f for f in instance._meta.concrete_fields if f.name in fields]
    else:
        target_fields = instance._meta.concrete_fields

    for field in target_fields:
        if field.name in exclude_fields:
            continue
        result[field.attname] = _get_field_value(instance, field)
    return result


def compute_diff(old_state, new_state, mask_fields=None):
    """Compute the diff between two field snapshots.

    Returns a dict of changed fields:
        {"field_name": {"old": old_value, "new": new_value}}

    Unchanged fields are excluded.
    """
    mask_fields = set(mask_fields or [])
    changes = {}

    all_keys = set(old_state.keys()) | set(new_state.keys())

    for key in all_keys:
        old_val = old_state.get(key)
        new_val = new_state.get(key)

        if not _values_equal(old_val, new_val):
            if key in mask_fields or key.removesuffix("_id") in mask_fields:
                changes[key] = {"old": MASK_VALUE, "new": MASK_VALUE}
            else:
                changes[key] = {
                    "old": _serialize(old_val),
                    "new": _serialize(new_val),
                }

    return changes


def compute_create_snapshot(new_state, mask_fields=None):
    """Compute snapshot for a CREATE action — all fields are 'new'."""
    mask_fields = set(mask_fields or [])
    changes = {}
    for key, val in new_state.items():
        if key in mask_fields or key.removesuffix("_id") in mask_fields:
            changes[key] = {"old": None, "new": MASK_VALUE}
        else:
            changes[key] = {"old": None, "new": _serialize(val)}
    return changes


def compute_delete_snapshot(old_state, mask_fields=None):
    """Compute snapshot for a DELETE action — all fields are 'old'."""
    mask_fields = set(mask_fields or [])
    changes = {}
    for key, val in old_state.items():
        if key in mask_fields or key.removesuffix("_id") in mask_fields:
            changes[key] = {"old": MASK_VALUE, "new": None}
        else:
            changes[key] = {"old": _serialize(val), "new": None}
    return changes


def _get_field_value(instance, field):
    """Get the raw value of a field from a model instance."""
    value = getattr(instance, field.attname, None)
    return value


def _values_equal(a, b):
    """Compare two values for equality, handling special types."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if type(a) != type(b):
        return _serialize(a) == _serialize(b)
    return a == b


def _serialize(value):
    """Convert a value to a JSON-serializable form."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, FieldFile):
        return value.name if value else None
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, models.Model):
        return value.pk
    return str(value)
