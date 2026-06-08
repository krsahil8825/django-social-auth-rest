"""
django_social_auth_rest.throttle
================================

Throttle classes used by social authentication endpoints.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from . import conf


class SocialAuthAnonThrottle(AnonRateThrottle):
    """Rate throttle for unauthenticated social authentication requests"""

    def get_rate(self):
        return conf.SOCIAL_AUTH_THROTTLE_RATE


class SocialAuthUserThrottle(UserRateThrottle):
    """Rate throttle for authenticated social authentication requests"""

    def get_rate(self):
        return conf.SOCIAL_AUTH_THROTTLE_RATE
