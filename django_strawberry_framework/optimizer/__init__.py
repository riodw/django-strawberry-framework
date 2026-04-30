"""Optimizer subsystem: ``DjangoOptimizerExtension`` (N+1 prevention).

Re-exports the consumer-facing ``DjangoOptimizerExtension`` and the
module-level ``logger`` so ``from django_strawberry_framework.optimizer
import logger`` (used by the optimizer pass-through tests) keeps
working after the flat ``optimizer.py`` module was promoted to a
subpackage.
"""

from .extension import DjangoOptimizerExtension, logger

__all__ = ("DjangoOptimizerExtension", "logger")
