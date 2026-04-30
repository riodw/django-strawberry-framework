"""django-strawberry-framework.

A DRF-inspired Django integration framework for Strawberry GraphQL.
"""

import logging

from strawberry import auto

from .optimizer import DjangoOptimizerExtension
from .optimizer.hints import OptimizerHint
from .types import DjangoType

__version__ = "0.0.2"

__all__ = (
    "DjangoOptimizerExtension",
    "DjangoType",
    "OptimizerHint",
    "__version__",
    "auto",
)

logger = logging.getLogger(__name__)
