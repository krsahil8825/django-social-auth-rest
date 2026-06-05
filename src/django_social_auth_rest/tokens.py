"""
accounts.tokens
================

This module defines token generation and verification functions
"""

from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
from django.conf import settings as django_settings

from .models import SocialAccountProvider


SOCIAL_AUTH_STATE_SALT = getattr(
    django_settings, "SOCIAL_AUTH_STATE_SALT", "social-auth-state-salt"
)

SOCIAL_AUTH_STATE_MAX_AGE = getattr(
    django_settings, "SOCIAL_AUTH_STATE_MAX_AGE", 300
)  # 5 minutes


def generate_state_token(provider: SocialAccountProvider) -> str:
    """Generate signed OAuth state token."""

    data = {
        "provider": provider.value,
        "purpose": "social_auth_state",
        "version": 1,
    }

    return signing.dumps(
        data,
        salt=SOCIAL_AUTH_STATE_SALT,
    )


def verify_state_token(token: str, provider_value: str) -> None:
    """Verify signed OAuth state token."""

    try:
        data = signing.loads(
            token,
            salt=SOCIAL_AUTH_STATE_SALT,
            max_age=SOCIAL_AUTH_STATE_MAX_AGE,
        )

    except SignatureExpired as exc:
        raise SignatureExpired("State token has expired.") from exc

    except BadSignature as exc:
        raise BadSignature("Invalid or tampered state token.") from exc

    if data.get("purpose") != "social_auth_state":
        raise BadSignature("Invalid token purpose.")

    if data.get("version") != 1:
        raise BadSignature("Unsupported token version.")

    provider = data.get("provider")

    if provider not in SocialAccountProvider.values:
        raise BadSignature("Invalid provider.")

    if provider != provider_value:
        raise BadSignature("Invalid provider.")
