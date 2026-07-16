"""Optimizer subsystem - selection-driven queryset planning via ``DjangoOptimizerExtension`` (N+1 prevention).

Re-exports the consumer-facing ``DjangoOptimizerExtension`` and the
framework-wide ``logger``. Both are load-bearing: sibling production
modules ``extension.py``, ``walker.py``, and ``nested_planner.py``
consume ``logger`` via ``from . import logger`` through this re-export
as the canonical intra-subpackage logger handle, and the optimizer
pass-through tests reach it via
``from django_strawberry_framework.optimizer import logger`` to pin
the re-export contract after the flat ``optimizer.py`` module was
promoted to a subpackage. Removing the re-export would silently break
those production siblings, not just the tests.

``OptimizationPlan`` and ``plan_optimizations`` live at their dotted
module paths (``optimizer.plans`` and ``optimizer.walker``) and are
not re-exported here - they are internal implementation details
consumed by ``extension.py`` and tests, not consumer-facing API.

The canonical ``logger`` is declared at the top-level package
(``django_strawberry_framework/__init__.py``); this module re-exports
it so the ``"django_strawberry_framework"`` literal lives in exactly
one source location and future subpackages (filters, orders,
aggregates) can pick it up the same way.
"""

from .. import logger
from .extension import DjangoOptimizerExtension

__all__ = ("DjangoOptimizerExtension", "logger")
