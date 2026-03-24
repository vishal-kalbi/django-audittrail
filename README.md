# django-audittrail

Automatic model-level change tracking for Django. One mixin, one middleware, zero boilerplate.

Records who changed what, when, from where — with full before/after field diffs.

## Quick Start

### 1. Install

```bash
pip install django-audittrail
```

### 2. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    'audittrail',
]
```

### 3. Add the middleware

```python
MIDDLEWARE = [
    ...
    'audittrail.middleware.AuditMiddleware',  # after SessionMiddleware
    ...
]
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Add the mixin to your models

```python
from audittrail import AuditableMixin

class Patient(AuditableMixin, models.Model):
    name = models.CharField(max_length=200)
    dob = models.DateField()
    ssn = models.CharField(max_length=11)

    class AuditTrail:
        exclude_fields = ['updated_at']
        mask_fields = ['ssn']
```

That's it. Every create, update, and delete on `Patient` is now tracked.

## Querying Audit Logs

```python
from audittrail.models import AuditLog

# All changes to a specific instance
AuditLog.objects.for_instance(patient)

# All changes by a user
AuditLog.objects.by_user(request.user)

# All changes to Patient model
AuditLog.objects.for_model(Patient)

# Time range
AuditLog.objects.between(start_datetime, end_datetime)

# Filter by action
AuditLog.objects.for_model(Patient).creates()
AuditLog.objects.for_model(Patient).updates()
AuditLog.objects.for_model(Patient).deletes()
```

## Diff Format

```python
log = AuditLog.objects.for_instance(patient).first()
print(log.changes)
# {"name": {"old": "John Doe", "new": "Jane Doe"},
#  "dob": {"old": "1990-01-01", "new": "1990-06-15"}}
```

On `CREATE`, all fields have `"old": null`. On `DELETE`, all fields have `"new": null`.

## Temporarily Disable Audit

```python
import audittrail

with audittrail.disabled():
    Patient.objects.bulk_create(patients_list)
```

## Admin Integration

```python
from audittrail.admin import AuditLogModelAdmin

@admin.register(Patient)
class PatientAdmin(AuditLogModelAdmin, admin.ModelAdmin):
    pass
```

## Configuration

### Per-model (via `AuditTrail` inner class)

| Option | Description |
|---|---|
| `exclude_fields` | List of field names to skip in diffs |
| `mask_fields` | List of field names whose values are stored as `"***"` |

### Global (via Django settings)

```python
AUDITTRAIL = {
    'ENABLED': True,
    'GLOBAL_EXCLUDE_FIELDS': ['updated_at', 'modified_at'],
}
```

## Requirements

- Python 3.10+
- Django 4.2+

## Known Limitations

- `QuerySet.update()` and `bulk_create()` bypass Django signals and are not tracked
- Async (ASGI) context propagation is not yet supported

## License

MIT
