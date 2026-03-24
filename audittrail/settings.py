from django.conf import settings

# Global settings under the AUDITTRAIL key in Django settings
# Example:
#   AUDITTRAIL = {
#       'ENABLED': True,
#       'GLOBAL_EXCLUDE_FIELDS': ['updated_at', 'modified_at'],
#   }

_DEFAULTS = {
    "ENABLED": True,
    "GLOBAL_EXCLUDE_FIELDS": [],
}


def get_setting(key):
    """Get an audittrail setting, falling back to defaults."""
    user_settings = getattr(settings, "AUDITTRAIL", {})
    return user_settings.get(key, _DEFAULTS.get(key))
