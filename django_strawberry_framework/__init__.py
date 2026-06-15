"""Public API of django-strawberry-framework, a DRF-inspired Django integration for Strawberry GraphQL."""

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

from .connection import DjangoConnection, DjangoConnectionField  # noqa: E402
from .list_field import DjangoListField  # noqa: E402
from .optimizer import DjangoOptimizerExtension  # noqa: E402
from .optimizer.hints import OptimizerHint  # noqa: E402
from .relay import DjangoNodeField, DjangoNodesField  # noqa: E402
from .scalars import BigInt, strawberry_config  # noqa: E402
from .types import DjangoType, SyncMisuseError, finalize_django_types  # noqa: E402

# TODO(spec-034 Slice 1): export the cascade-permission pair from the package root
# (the card DoD's import line `from django_strawberry_framework import
# apply_cascade_permissions`). Uncomment WITH the matching `__all__` members and
# the `tests/base/test_init.py` exports pin in the same change (Decision 4):
#
#     from .permissions import (
#         aapply_cascade_permissions,
#         apply_cascade_permissions,
#     )

__version__ = "0.0.9"

__all__ = (
    # TODO(spec-034 Slice 1): add "aapply_cascade_permissions" and
    # "apply_cascade_permissions" here (alphabetically) when the import above is
    # uncommented; update tests/base/test_init.py's exports pin to match.
    "BigInt",
    "DjangoConnection",
    "DjangoConnectionField",
    "DjangoListField",
    "DjangoNodeField",
    "DjangoNodesField",
    "DjangoOptimizerExtension",
    "DjangoType",
    "OptimizerHint",
    "SyncMisuseError",
    "__version__",
    "auto",
    "finalize_django_types",
    "strawberry_config",
)
