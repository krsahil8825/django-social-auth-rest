"""
django_social_auth_rest.throttle
================================

This module defines the throttling classes for social authentication-related API actions in the Django application.
"""

from django.conf import settings as django_settings
from rest_framework.throttling import UserRateThrottle

THROTTLE_RATE = getattr(django_settings, "SOCIAL_AUTH_THROTTLE_RATE", "10/minute")


class SocialAuthThrottle(UserRateThrottle):
    """Apply a configurable rate limit to social authentication-related API actions."""

    rate = THROTTLE_RATE
