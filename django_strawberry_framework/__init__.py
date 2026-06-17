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
from .permissions import (  # noqa: E402
    aapply_cascade_permissions,
    apply_cascade_permissions,
)
from .relay import DjangoNodeField, DjangoNodesField  # noqa: E402
from .scalars import BigInt, strawberry_config  # noqa: E402
from .types import DjangoType, SyncMisuseError, finalize_django_types  # noqa: E402

# TODO(spec-036 Slice 1-3): promote the mutation symbols to the root public
# surface as each owning slice lands.
# Pseudocode:
# - Slice 1 exposes ``FieldError`` from ``django_strawberry_framework.mutations``.
# - Slice 2 exposes ``DjangoMutation`` from the same package.
# - Slice 3 exposes ``DjangoMutationField`` once the field factory exists.
# - Add the three names to ``__all__`` without bumping ``__version__``; the
#   joint 0.0.11 cut shared with the Upload card owns the version files.
__version__ = "0.0.10"

__all__ = (
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
    "aapply_cascade_permissions",
    "apply_cascade_permissions",
    "auto",
    "finalize_django_types",
    "strawberry_config",
)
