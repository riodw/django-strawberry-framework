"""Public API of django-strawberry-framework, a DRF-inspired Django integration for Strawberry GraphQL."""

from importlib import import_module
from typing import TYPE_CHECKING, Any

# `auto` is re-exported so consumers can write `from django_strawberry_framework import auto`
# without importing strawberry directly; this is part of the DRF-shaped public surface.
from strawberry import auto

# The package logger comes first among the package's own imports (isort sorts ``._logger``
# ahead of every subpackage), since subpackages read it as
# ``from django_strawberry_framework import logger``.
from ._logger import logger as logger
from .connection import DjangoConnection, DjangoConnectionField
from .error_policy import (
    DEFAULT_ERROR_POLICY,
    ErrorPolicy,
)
from .extensions.error_policy import DjangoErrorPolicyExtension
from .extensions.resource_policy import DjangoResourcePolicyExtension
from .forms import DjangoFormMutation, DjangoModelFormMutation
from .list_field import DjangoListField, ListArgumentError
from .mutations import (
    DjangoModelPermission,
    DjangoMutation,
    DjangoMutationField,
    FieldError,
)
from .optimizer import DjangoOptimizerExtension
from .optimizer.hints import OptimizerHint
from .permissions import (
    aapply_cascade_permissions,
    apply_cascade_permissions,
)
from .relay import DjangoNodeField, DjangoNodesField
from .resource_policy import (
    DEFAULT_RESOURCE_POLICY,
    RESOURCE_LIMIT_ERROR_CODE,
    ResourceLimitExceeded,
    ResourcePolicy,
)
from .scalars import BigInt, Upload, strawberry_config
from .schema import (
    SCHEMA_CONFIGURATION_ERROR_CODE,
    DjangoMutationExecutionContext,
    DjangoSchema,
)
from .types import DjangoType, SyncMisuseError, finalize_django_types
from .types.converters import (
    DjangoFilePathType,
    DjangoFileType,
    DjangoImagePathType,
    DjangoImageType,
)
from .utils.connections import PaginationArgumentError

# Do not import or root-export DjangoDebugExtension here: its public
# opt-in remains django_strawberry_framework.extensions.

# The single source of the release. Hatchling derives packaging metadata from
# this literal via ``[tool.hatch.version]`` in pyproject.toml; no second version
# declaration exists anywhere in the repository.
__version__ = "0.0.15"


# The DRF-soft-dependency public names, resolved lazily by NAME through the shared
# ``rest_framework.require_drf()`` guard (spec-039 Decision 12). Each maps a
# public name to its ``(submodule, attr)`` import target; ALL are deliberately ABSENT
# from ``__all__`` so ``from django_strawberry_framework import *`` stays DRF-free.
# ``SerializerMutation`` is the write base; ``register_serializer_field_converter`` +
# ``SerializerFieldConversion`` are the public serializer-field converter-registry
# surface (a consumer registers a converter returning a ``SerializerFieldConversion``);
# ``NestedSerializerConfig`` is the explicit opt-in for nested serializer inputs
# (``Meta.nested_fields = {"items": NestedSerializerConfig(...)}``, spec-039).
_DRF_SOFT_EXPORTS: dict[str, tuple[str, str]] = {
    "SerializerMutation": (".rest_framework.sets", "SerializerMutation"),
    "register_serializer_field_converter": (
        ".rest_framework.serializer_converter",
        "register_serializer_field_converter",
    ),
    "SerializerFieldConversion": (
        ".rest_framework.serializer_converter",
        "SerializerFieldConversion",
    ),
    "describe_serializer_input": (".rest_framework.inputs", "describe_serializer_input"),
    "NestedSerializerConfig": (".rest_framework.inputs", "NestedSerializerConfig"),
    # The frozen hook surface: the context every serializer consumer hook
    # receives instead of the live located instance, and the frozen upload
    # descriptor standing in for file values in hook data views.
    "SerializerHookContext": (".rest_framework.hook_context", "SerializerHookContext"),
    "UploadMetadata": (".rest_framework.hook_context", "UploadMetadata"),
}

# The same names, imported for the type checker only, so a consumer's
# ``from django_strawberry_framework import SerializerMutation`` is the real class
# to it (a typed ``SerializerMutation`` subclass, ``@override`` on its hooks)
# instead of ``__getattr__``'s ``Any``. Runtime never executes this block: the
# names still resolve through the lazy guard below, so ``import
# django_strawberry_framework`` stays DRF-free. The redundant ``as`` aliases mark
# them re-exported. Each line mirrors one ``_DRF_SOFT_EXPORTS`` entry.
if TYPE_CHECKING:
    from .rest_framework.hook_context import SerializerHookContext as SerializerHookContext
    from .rest_framework.hook_context import UploadMetadata as UploadMetadata
    from .rest_framework.inputs import NestedSerializerConfig as NestedSerializerConfig
    from .rest_framework.inputs import describe_serializer_input as describe_serializer_input
    from .rest_framework.serializer_converter import (
        SerializerFieldConversion as SerializerFieldConversion,
    )
    from .rest_framework.serializer_converter import (
        register_serializer_field_converter as register_serializer_field_converter,
    )
    from .rest_framework.sets import SerializerMutation as SerializerMutation


# basedpyright: PEP 562 module __getattr__; a lazy re-export is whatever the named attribute is
def __getattr__(name: str) -> Any:  # pyright: ignore[reportExplicitAny]  # noqa: ANN401 - lazy re-export is whatever the attribute is
    """Resolve the DRF-soft-dependency names lazily through the DRF import guard (spec-039 Decision 12).

    PEP 562 module-level ``__getattr__``: ``from django_strawberry_framework import
    SerializerMutation`` (and ``register_serializer_field_converter`` /
    ``SerializerFieldConversion``, spec-039) resolves by NAME through
    ``rest_framework.require_drf()`` (the shared DRF guard), so a DRF-absent consumer
    gets the install-hint ``ImportError`` only when they reach for one of these names -
    ``import django_strawberry_framework`` itself never eagerly imports
    ``rest_framework/`` and succeeds without DRF. Every OTHER attribute miss raises the
    normal ``AttributeError`` so unrelated typos behave as usual.

    **Non-memoizing (Decision 12).** The resolved object is NOT written into the module
    ``globals()`` - each access re-fires the guard, so the absent-DRF test can evict
    ``rest_framework*`` / ``django_strawberry_framework.rest_framework*`` from
    ``sys.modules`` and re-hit the guard on the next access without a stale binding.
    These names are deliberately ABSENT from ``__all__`` so ``from
    django_strawberry_framework import *`` stays DRF-free and never trips the guard.
    """
    target = _DRF_SOFT_EXPORTS.get(name)
    if target is not None:
        from .rest_framework import require_drf  # noqa: PLC0415 - DRF is optional

        _ = require_drf()
        submodule, attr = target
        return getattr(import_module(submodule, __name__), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = (
    "DEFAULT_ERROR_POLICY",
    "DEFAULT_RESOURCE_POLICY",
    "RESOURCE_LIMIT_ERROR_CODE",
    "SCHEMA_CONFIGURATION_ERROR_CODE",
    "BigInt",
    "DjangoConnection",
    "DjangoConnectionField",
    "DjangoErrorPolicyExtension",
    "DjangoFilePathType",
    "DjangoFileType",
    "DjangoFormMutation",
    "DjangoImagePathType",
    "DjangoImageType",
    "DjangoListField",
    "DjangoModelFormMutation",
    "DjangoModelPermission",
    "DjangoMutation",
    "DjangoMutationExecutionContext",
    "DjangoMutationField",
    "DjangoNodeField",
    "DjangoNodesField",
    "DjangoOptimizerExtension",
    "DjangoResourcePolicyExtension",
    "DjangoSchema",
    "DjangoType",
    "ErrorPolicy",
    "FieldError",
    "ListArgumentError",
    "OptimizerHint",
    "PaginationArgumentError",
    "ResourceLimitExceeded",
    "ResourcePolicy",
    "SyncMisuseError",
    "Upload",
    "__version__",
    "aapply_cascade_permissions",
    "apply_cascade_permissions",
    "auto",
    "finalize_django_types",
    "strawberry_config",
)
