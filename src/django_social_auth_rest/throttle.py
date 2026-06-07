"""
django_social_auth_rest.throttle
================================

Throttle classes used by social authentication endpoints.
"""

from rest_framework.throttling import UserRateThrottle

from . import conf


class SocialAuthThrottle(UserRateThrottle):
    """
    Rate throttle for social authentication requests.
    """

    rate = conf.SOCIAL_AUTH_THROTTLE_RATE
