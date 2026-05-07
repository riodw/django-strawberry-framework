"""django-strawberry-framework.

A DRF-inspired Django integration framework for Strawberry GraphQL.
"""

# `auto` is re-exported so consumers can write `from django_strawberry_framework import auto`
# without importing strawberry directly; this is part of the DRF-shaped public surface.
from strawberry import auto

from .optimizer import DjangoOptimizerExtension
from .optimizer.hints import OptimizerHint
from .types import DjangoType

# TODO(spec-foundation 0.0.4): re-export ``finalize_django_types`` from
# ``.types`` and add it to ``__all__`` per ``docs/spec-foundation.md``
# "Public API delta". This is the single new public symbol the slice
# adds; consumers import it the same way they import ``DjangoType``.
# Bump ``__version__`` to ``"0.0.4"`` in lockstep with the matching
# bump in ``pyproject.toml`` (versioning rule from ``AGENTS.md``).
__version__ = "0.0.3"

__all__ = (
    "DjangoOptimizerExtension",
    "DjangoType",
    "OptimizerHint",
    "__version__",
    "auto",
)
