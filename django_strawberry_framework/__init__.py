"""django-strawberry-framework.

A DRF-inspired Django integration framework for Strawberry GraphQL.
"""

# `auto` is re-exported so consumers can write `from django_strawberry_framework import auto`
# without importing strawberry directly; this is part of the DRF-shaped public surface.
import logging

# Canonical package logger. Declared at the top-level package so the
# string ``"django_strawberry_framework"`` lives in exactly one source
# location; subpackages re-export this via ``from .. import logger``
# (see ``optimizer/__init__.py``). Consumer-facing: the name is the key
# clients use in Django's ``LOGGING`` config dict, so it is part of the
# public surface even though it is not in ``__all__``.
logger = logging.getLogger("django_strawberry_framework")

from strawberry import auto  # noqa: E402  # logger must exist before subpackage imports

from .optimizer import DjangoOptimizerExtension  # noqa: E402
from .optimizer.hints import OptimizerHint  # noqa: E402
from .types import DjangoType, finalize_django_types  # noqa: E402

__version__ = "0.0.4"
# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# ship Relay interfaces without adding public exports. The only line in
# this file that changes is ``__version__`` (paired with the matching
# bump in ``pyproject.toml`` per AGENTS.md "Versioning"); ``__all__``
# stays at its current six names.

__all__ = (
    "DjangoOptimizerExtension",
    "DjangoType",
    "OptimizerHint",
    "__version__",
    "auto",
    "finalize_django_types",
)
