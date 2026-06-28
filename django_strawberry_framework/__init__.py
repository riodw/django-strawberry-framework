"""Public API of django-strawberry-framework, a DRF-inspired Django integration for Strawberry GraphQL."""

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

from .connection import DjangoConnection, DjangoConnectionField  # noqa: E402
from .forms import DjangoFormMutation, DjangoModelFormMutation  # noqa: E402
from .list_field import DjangoListField  # noqa: E402
from .mutations import (  # noqa: E402
    DjangoModelPermission,
    DjangoMutation,
    DjangoMutationField,
    FieldError,
)
from .optimizer import DjangoOptimizerExtension  # noqa: E402
from .optimizer.hints import OptimizerHint  # noqa: E402
from .permissions import (  # noqa: E402
    aapply_cascade_permissions,
    apply_cascade_permissions,
)
from .relay import DjangoNodeField, DjangoNodesField  # noqa: E402
from .scalars import BigInt, Upload, strawberry_config  # noqa: E402
from .types import DjangoType, SyncMisuseError, finalize_django_types  # noqa: E402
from .types.converters import DjangoFileType, DjangoImageType  # noqa: E402

__version__ = "0.0.12"


def __getattr__(name: str) -> type:
    """Resolve ``SerializerMutation`` lazily through the DRF soft-import guard (spec-039 Decision 12).

    PEP 562 module-level ``__getattr__``: ``from django_strawberry_framework import
    SerializerMutation`` resolves by NAME through ``rest_framework.require_drf()``
    (the shared DRF guard), so a DRF-absent consumer gets the install-hint
    ``ImportError`` only when they reach for the name - ``import
    django_strawberry_framework`` itself never eagerly imports ``rest_framework/`` and
    succeeds without DRF. Every OTHER attribute miss raises the normal
    ``AttributeError`` so unrelated typos behave as usual.

    **Non-memoizing (Decision 12).** The resolved class is NOT written into the
    module ``globals()`` - each access re-fires the guard, so the absent-DRF test can
    evict ``rest_framework*`` / ``django_strawberry_framework.rest_framework*`` from
    ``sys.modules`` and re-hit the guard on the next access without a stale binding.
    ``SerializerMutation`` is deliberately ABSENT from ``__all__`` (F1) so ``from
    django_strawberry_framework import *`` stays DRF-free and never trips the guard.
    """
    if name == "SerializerMutation":
        from .rest_framework import require_drf

        require_drf()
        from .rest_framework.sets import SerializerMutation

        return SerializerMutation
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = (
    "BigInt",
    "DjangoConnection",
    "DjangoConnectionField",
    "DjangoFileType",
    "DjangoFormMutation",
    "DjangoImageType",
    "DjangoListField",
    "DjangoModelFormMutation",
    "DjangoModelPermission",
    "DjangoMutation",
    "DjangoMutationField",
    "DjangoNodeField",
    "DjangoNodesField",
    "DjangoOptimizerExtension",
    "DjangoType",
    "FieldError",
    "OptimizerHint",
    "SyncMisuseError",
    "Upload",
    "__version__",
    "aapply_cascade_permissions",
    "apply_cascade_permissions",
    "auto",
    "finalize_django_types",
    "strawberry_config",
)
