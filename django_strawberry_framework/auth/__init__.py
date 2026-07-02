"""Opt-in session-auth field factories (spec-040).

The package root intentionally does not import or re-export this module
(spec-040 Decision 3 - the opt-in is structural, and a consumer who doesn't use
auth never pays the ``django.contrib.auth`` import). Consumers opt in with::

    from django_strawberry_framework.auth import (
        current_user, login_mutation, logout_mutation, register_mutation,
    )
"""

from .mutations import login_mutation, logout_mutation, register_mutation
from .queries import current_user

__all__ = (
    "current_user",
    "login_mutation",
    "logout_mutation",
    "register_mutation",
)
