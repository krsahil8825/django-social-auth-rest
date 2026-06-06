"""
django_social_auth_rest.conf
===============================

This module defines the configuration settings for the django_social_auth_rest app.
"""

from django.conf import settings as django_settings
from .models import SocialAccountProvider

# ============================================
# General configuration
# ============================================

# Throttling configuration
SOCIAL_AUTH_THROTTLE_RATE = getattr(
    django_settings, "SOCIAL_AUTH_THROTTLE_RATE", "10/minute"
)


# state token configuration
SOCIAL_AUTH_STATE_SALT = getattr(
    django_settings, "SOCIAL_AUTH_STATE_SALT", "social-auth-state-salt"
)
SOCIAL_AUTH_STATE_MAX_AGE = getattr(
    django_settings, "SOCIAL_AUTH_STATE_MAX_AGE", 300
)  # 5 minutes


# ============================================
# Email configuration
# ============================================

SOCIAL_AUTH_ACCOUNT_CREATION_EMAIL_CLASS = getattr(
    django_settings,
    "SOCIAL_AUTH_ACCOUNT_CREATION_EMAIL_CLASS",
    None,
)
"""
Path to the email class that should be used when a new user account is created.

Djoser users can use:
    djoser.email.ConfirmationEmail

Expected usage:

    Email(`
        request=request,
        context={"user": user},
    ).send(
        to=[user.email]
    )

Example:

    SOCIAL_AUTH_ACCOUNT_CREATION_EMAIL_CLASS = (
        "myapp.emails.CustomConfirmationEmail"
    )
"""


# ===========================================
# Provider-specific configuration
# ===========================================


# GitHub OAuth configuration
GITHUB_CLIENT_ID = getattr(django_settings, "GITHUB_CLIENT_ID", None)
GITHUB_CLIENT_SECRET = getattr(django_settings, "GITHUB_CLIENT_SECRET", None)
ENABLE_GITHUB_AUTH = True if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET else False


# Google OAuth configuration
GOOGLE_CLIENT_ID = getattr(django_settings, "GOOGLE_CLIENT_ID", None)
ENABLE_GOOGLE_AUTH = True if GOOGLE_CLIENT_ID else False


# Provider enablement configuration
PROVIDER_ENABLED = {
    SocialAccountProvider.GITHUB: ENABLE_GITHUB_AUTH,
    SocialAccountProvider.GOOGLE: ENABLE_GOOGLE_AUTH,
}
