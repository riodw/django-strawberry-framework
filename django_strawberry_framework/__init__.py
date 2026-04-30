"""django-strawberry-framework.

A DRF-inspired Django integration framework for Strawberry GraphQL.
"""

import logging

from strawberry import auto

from .optimizer import DjangoOptimizerExtension
from .types import DjangoType

__version__ = "0.0.1"

__all__ = (
    "DjangoOptimizerExtension",
    "DjangoType",
    "__version__",
    "auto",
)

logger = logging.getLogger(__name__)
