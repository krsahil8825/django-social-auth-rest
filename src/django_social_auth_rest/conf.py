"""
django_social_auth_rest.conf
===============================

This module defines the configuration settings for the django_social_auth_rest app.
"""

from django.conf import settings as django_settings


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


# GitHub OAuth configuration
GITHUB_CLIENT_ID = getattr(django_settings, "GITHUB_CLIENT_ID", None)
GITHUB_CLIENT_SECRET = getattr(django_settings, "GITHUB_CLIENT_SECRET", None)
ENABLE_GITHUB_AUTH = getattr(django_settings, "ENABLE_GITHUB_AUTH", True)

if ENABLE_GITHUB_AUTH and (not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET):
    raise ValueError(
        "GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be set if ENABLE_GITHUB_AUTH is True"
    )


# Google OAuth configuration
GOOGLE_CLIENT_ID = getattr(django_settings, "GOOGLE_CLIENT_ID", None)
ENABLE_GOOGLE_AUTH = getattr(django_settings, "ENABLE_GOOGLE_AUTH", False)

if ENABLE_GOOGLE_AUTH and not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID must be set if ENABLE_GOOGLE_AUTH is True")
