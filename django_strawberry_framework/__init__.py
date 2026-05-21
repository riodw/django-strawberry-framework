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

from .optimizer import DjangoOptimizerExtension  # noqa: E402
from .optimizer.hints import OptimizerHint  # noqa: E402
from .scalars import BigInt  # noqa: E402
from .types import DjangoType, finalize_django_types  # noqa: E402

# TODO(spec-016, Slice 1 — Decision 1 public-export discipline): when
# ``list_field.py`` ships, add::
#
#     from .list_field import DjangoListField  # noqa: E402
#
# in alphabetical position immediately after the ``BigInt`` import above,
# and insert ``"DjangoListField"`` into ``__all__`` between ``BigInt`` and
# ``DjangoOptimizerExtension`` (also alphabetical). The matching assertion
# in ``tests/base/test_init.py`` is updated in the SAME commit so the
# ``__all__`` surface check stays accurate (Slice 1 checkbox).

__version__ = "0.0.6"

__all__ = (
    "BigInt",
    # TODO(spec-016, Slice 1): insert ``"DjangoListField"`` here.
    "DjangoOptimizerExtension",
    "DjangoType",
    "OptimizerHint",
    "__version__",
    "auto",
    "finalize_django_types",
)
