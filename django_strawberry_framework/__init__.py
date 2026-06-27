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

# TODO(spec-039 Slice 2): Export `SerializerMutation` through a root `__getattr__`
# instead of an eager import so `import django_strawberry_framework` keeps working
# without DRF installed. Keep it OUT of `__all__` while DRF is a soft dependency:
# named imports resolve lazily, but star imports must stay DRF-free and must not
# bind `SerializerMutation`.
# Pseudo flow:
#   - On root `__getattr__`, reject every name except `SerializerMutation` with
#     the normal `AttributeError`.
#   - Import and run `rest_framework.require_drf()` before importing the class.
#   - Import `rest_framework.sets.SerializerMutation` only after the guard passes,
#     then return that class to the caller.
#   - Leave `__all__` unchanged; do not add `SerializerMutation` until DRF becomes
#     a hard runtime dependency.
#
# Do not memoize the resolved class into `globals()`; the absent-DRF test must be
# able to evict modules and re-hit the guard on every access.
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
