# Changelog

## [0.1.0] - 2026-03-24

### Added
- `AuditableMixin` — single mixin to enable audit logging on any Django model
- `AuditMiddleware` — captures request context (user, IP, path, method) via thread-local storage
- `AuditLog` model with structured field-level diffs (`{"field": {"old": X, "new": Y}}`)
- Support for `CREATE`, `UPDATE`, and `DELETE` action tracking
- Field masking (`mask_fields`) for sensitive data (passwords, SSNs)
- Field exclusion (`exclude_fields`) to skip noisy fields like `updated_at`
- `disabled()` context manager to suppress audit logging temporarily
- `AuditQuerySet` with `for_instance()`, `by_user()`, `for_model()`, `between()`, `creates()`, `updates()`, `deletes()`
- Django Admin integration: `AuditLogAdmin`, `AuditLogModelAdmin` mixin, `AuditLogInline`
- DRF `AuditLogSerializer` (optional, requires djangorestframework)
- X-Forwarded-For support for reverse proxy deployments
- Comprehensive test suite

### Known Limitations
- `QuerySet.update()` and `bulk_create()` do not trigger Django signals — these operations are not tracked
- Async (ASGI) context propagation not yet supported
