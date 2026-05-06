"""django-strawberry-framework.

A DRF-inspired Django integration framework for Strawberry GraphQL.
"""

# `auto` is re-exported so consumers can write `from django_strawberry_framework import auto`
# without importing strawberry directly; this is part of the DRF-shaped public surface.
from strawberry import auto

from .optimizer import DjangoOptimizerExtension
from .optimizer.hints import OptimizerHint
from .types import DjangoType

__version__ = "0.0.3"

__all__ = (
    "DjangoOptimizerExtension",
    "DjangoType",
    "OptimizerHint",
    "__version__",
    "auto",
)
