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

from .list_field import DjangoListField  # noqa: E402
from .optimizer import DjangoOptimizerExtension  # noqa: E402
from .optimizer.hints import OptimizerHint  # noqa: E402
from .scalars import BigInt, strawberry_config  # noqa: E402
from .types import DjangoType, SyncMisuseError, finalize_django_types  # noqa: E402

# TODO(spec-028-orders-0_0_8 Slice 5): bump to ``"0.0.8"`` only if the
# deterministic KANBAN check still shows this is the last ``0.0.8`` card.
__version__ = "0.0.7"

__all__ = (
    "BigInt",
    "DjangoListField",
    "DjangoOptimizerExtension",
    "DjangoType",
    "OptimizerHint",
    "SyncMisuseError",
    "__version__",
    "auto",
    "finalize_django_types",
    "strawberry_config",
)
