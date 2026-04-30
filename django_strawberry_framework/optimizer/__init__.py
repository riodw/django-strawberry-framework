"""Optimizer subsystem: ``DjangoOptimizerExtension`` (N+1 prevention).

Re-exports the consumer-facing ``DjangoOptimizerExtension`` and the
module-level ``logger`` so ``from django_strawberry_framework.optimizer
import logger`` (used by the optimizer pass-through tests) keeps
working after the flat ``optimizer.py`` module was promoted to a
subpackage.

``OptimizationPlan`` and ``plan_optimizations`` live at their dotted
module paths (``optimizer.plans`` and ``optimizer.walker``) and are
not re-exported here — they are internal implementation details
consumed by ``extension.py`` and tests, not consumer-facing API.
"""

from .extension import DjangoOptimizerExtension, logger

__all__ = ("DjangoOptimizerExtension", "logger")
