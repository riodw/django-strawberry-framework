"""Optimizer subsystem: ``DjangoOptimizerExtension`` (N+1 prevention).

Re-exports the consumer-facing ``DjangoOptimizerExtension`` and the
framework-wide ``logger`` so ``from django_strawberry_framework.optimizer
import logger`` (used by the optimizer pass-through tests) keeps
working after the flat ``optimizer.py`` module was promoted to a
subpackage.

``OptimizationPlan`` and ``plan_optimizations`` live at their dotted
module paths (``optimizer.plans`` and ``optimizer.walker``) and are
not re-exported here — they are internal implementation details
consumed by ``extension.py`` and tests, not consumer-facing API.

The ``logger`` is defined here (rather than per-module) so the
"django_strawberry_framework" string only appears once in the
subpackage; ``extension.py`` and ``walker.py`` both ``from . import
logger`` to avoid duplicating the literal.
"""

import logging

logger = logging.getLogger("django_strawberry_framework")

from .extension import DjangoOptimizerExtension  # noqa: E402  # logger must exist before this import

__all__ = ("DjangoOptimizerExtension", "logger")
