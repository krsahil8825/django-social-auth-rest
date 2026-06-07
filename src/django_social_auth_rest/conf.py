"""
django_social_auth_rest.conf
============================

Configuration values used throughout the social authentication package.

All settings can be overridden through the Django settings module.
"""

from django.conf import settings as django_settings

from .models import SocialAccountProvider


# ===========================================================
# General settings
# ===========================================================

# Request throttling
SOCIAL_AUTH_THROTTLE_RATE = getattr(
    django_settings,
    "SOCIAL_AUTH_THROTTLE_RATE",
    "10/minute",
)

# OAuth state token settings
SOCIAL_AUTH_STATE_SALT = getattr(
    django_settings,
    "SOCIAL_AUTH_STATE_SALT",
    "social-auth-state-salt",
)
SOCIAL_AUTH_STATE_MAX_AGE = getattr(
    django_settings,
    "SOCIAL_AUTH_STATE_MAX_AGE",
    300,
)  # 5 minutes


# ===========================================================
# Email settings
# ===========================================================

SOCIAL_AUTH_ACCOUNT_CREATION_EMAIL_CLASS = getattr(
    django_settings,
    "SOCIAL_AUTH_ACCOUNT_CREATION_EMAIL_CLASS",
    None,
)
"""
Import path to the email class used when a new user account is created.

Djoser users can use:

    djoser.email.ConfirmationEmail

The configured class is expected to support the following pattern:

    >>> Email(
    ...     request=request,
    ...     context={"user": user},
    ... ).send(
    ...     to=[user.email]
    ... )

Example:

    >>> SOCIAL_AUTH_ACCOUNT_CREATION_EMAIL_CLASS = (
    ...     "myapp.emails.CustomConfirmationEmail"
    ... )
"""


# ===========================================================
# User model settings
# ===========================================================

SOCIAL_AUTH_USER_DELETED_FIELD = getattr(
    django_settings,
    "SOCIAL_AUTH_USER_DELETED_FIELD",
    None,
)
"""
Optional field on the user model that indicates whether an account
has been soft-deleted.

Example:

    >>> SOCIAL_AUTH_USER_DELETED_FIELD = "is_deleted"

If ``None``, deleted-account checks are disabled.
"""


# ===========================================================
# OAuth provider settings
# ===========================================================

# GitHub OAuth credentials
GITHUB_CLIENT_ID = getattr(django_settings, "GITHUB_CLIENT_ID", None)
GITHUB_CLIENT_SECRET = getattr(django_settings, "GITHUB_CLIENT_SECRET", None)
ENABLE_GITHUB_AUTH = bool(
    GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET
)

# Google OAuth credentials
GOOGLE_CLIENT_ID = getattr(django_settings, "GOOGLE_CLIENT_ID", None)
ENABLE_GOOGLE_AUTH = bool(GOOGLE_CLIENT_ID)


# ===========================================================
# Enabled providers
# ===========================================================

PROVIDER_ENABLED = {
    SocialAccountProvider.GITHUB: ENABLE_GITHUB_AUTH,
    SocialAccountProvider.GOOGLE: ENABLE_GOOGLE_AUTH,
}

ENABLED_PROVIDERS = [
    provider
    for provider, enabled in PROVIDER_ENABLED.items()
    if enabled
]
