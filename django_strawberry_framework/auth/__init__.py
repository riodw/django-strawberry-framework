"""Opt-in session-auth field factories planned by spec-040.

The package root intentionally does not import or re-export this module. Consumers
opt in with ``from django_strawberry_framework.auth import ...`` after Slice 1/2
replace the fail-loud placeholders in ``mutations.py`` and ``queries.py``.
"""

from .mutations import login_mutation, logout_mutation, register_mutation
from .queries import current_user

__all__ = (
    "current_user",
    "login_mutation",
    "logout_mutation",
    "register_mutation",
)
