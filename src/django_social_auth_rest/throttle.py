"""
django_social_auth_rest.throttle
================================

This module defines the throttling classes for social authentication-related API actions in the Django application.
"""

from rest_framework.throttling import UserRateThrottle
from . import conf


class SocialAuthThrottle(UserRateThrottle):
    """Apply a configurable rate limit to social authentication-related API actions."""

    rate = conf.SOCIAL_AUTH_THROTTLE_RATE
