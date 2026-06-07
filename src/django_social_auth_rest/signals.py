"""
django_social_auth_rest.signals
===============================

Signals emitted during social authentication and account management
operations.
"""

from django.dispatch import Signal


new_user_registered = Signal()
"""
Sent when a new user account is created through a social
authentication provider.
"""


login_successful = Signal()
"""
Sent after a user successfully authenticates through a social
authentication provider.
"""


link_account_successful = Signal()
"""
Sent after a social account is successfully linked to an existing
user account.
"""


unlink_account_successful = Signal()
"""
Sent after a social account is successfully unlinked from a user
account.
"""
