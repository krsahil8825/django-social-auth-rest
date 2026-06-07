"""
django_social_auth_rest.tokens
=============================

Utilities for generating and validating signed tokens used by the
social authentication workflow.
"""

from django.core import signing
from django.core.signing import BadSignature, SignatureExpired

from . import conf
from .models import SocialAccountProvider


def generate_state_token(provider: SocialAccountProvider) -> str:
    """
    Generate a signed OAuth state token for the given provider.
    """

    data = {
        "provider": provider.value,
        "purpose": "social_auth_state",
        "version": 1,
    }

    return signing.dumps(
        data,
        salt=conf.SOCIAL_AUTH_STATE_SALT,
    )


def verify_state_token(token: str, provider_value: str) -> None:
    """
    Validate a signed OAuth state token and ensure it matches the
    expected provider.
    """

    try:
        data = signing.loads(
            token,
            salt=conf.SOCIAL_AUTH_STATE_SALT,
            max_age=conf.SOCIAL_AUTH_STATE_MAX_AGE,
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
