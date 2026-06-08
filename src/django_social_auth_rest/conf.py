"""
django_social_auth_rest.conf
============================

Centralized configuration for django_social_auth_rest.

Settings are loaded from Django's settings module, validated where
necessary, and exposed as normalized constants for internal use.
"""

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
import warnings

from .models import SocialAccountProvider


# ===========================================================
# Throttle settings
# ===========================================================

SOCIAL_AUTH_THROTTLE_RATE = getattr(
    django_settings,
    "SOCIAL_AUTH_THROTTLE_RATE",
    "10/minute",
)

# ===========================================================
# State parameter settings
# ===========================================================

_salt = getattr(django_settings, "SOCIAL_AUTH_STATE_SALT", None)
if not _salt and not getattr(django_settings, "DEBUG", False):
    raise ImproperlyConfigured(
        "SOCIAL_AUTH_STATE_SALT must be set in your Django settings. "
        "Use a long, random secret value such as "
        "secrets.token_hex(32)."
    )

if _salt and len(_salt) < 32:
    warnings.warn(
        "SOCIAL_AUTH_STATE_SALT is shorter than 32 characters. "
        "Consider using a higher-entropy value.",
        stacklevel=2,
    )

SOCIAL_AUTH_STATE_SALT = _salt

_max_age = getattr(django_settings, "SOCIAL_AUTH_STATE_MAX_AGE", 300)
if not isinstance(_max_age, int) or _max_age <= 0 or _max_age > 3600:
    raise ImproperlyConfigured(
        "SOCIAL_AUTH_STATE_MAX_AGE must be a positive integer not greater than 3600."
    )

SOCIAL_AUTH_STATE_MAX_AGE = _max_age


# ===========================================================
# User model settings
# ===========================================================

SOCIAL_AUTH_USER_DELETED_FIELD = getattr(
    django_settings,
    "SOCIAL_AUTH_USER_DELETED_FIELD",
    None,
)
"""
Optional user model field used to identify soft-deleted accounts.

Example:
    SOCIAL_AUTH_USER_DELETED_FIELD = "is_deleted"
"""


# ===========================================================
# OAuth provider settings
# ===========================================================

GITHUB_CLIENT_ID = getattr(
    django_settings,
    "GITHUB_CLIENT_ID",
    None,
)

GITHUB_CLIENT_SECRET = getattr(
    django_settings,
    "GITHUB_CLIENT_SECRET",
    None,
)

ENABLE_GITHUB_AUTH = bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)

GOOGLE_CLIENT_ID = getattr(
    django_settings,
    "GOOGLE_CLIENT_ID",
    None,
)

ENABLE_GOOGLE_AUTH = bool(GOOGLE_CLIENT_ID)


# ===========================================================
# Enabled providers
# ===========================================================

PROVIDER_ENABLED = {
    SocialAccountProvider.GITHUB: ENABLE_GITHUB_AUTH,
    SocialAccountProvider.GOOGLE: ENABLE_GOOGLE_AUTH,
}

ENABLED_PROVIDERS = tuple(
    provider for provider, enabled in PROVIDER_ENABLED.items() if enabled
)
