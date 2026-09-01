"""Package init tests for version metadata and public exports."""

import logging

import django_strawberry_framework
from django_strawberry_framework import (
    DjangoFileType,
    DjangoImageType,
    Upload,
    __version__,
    logger,
)
from django_strawberry_framework.optimizer import logger as optimizer_logger
from django_strawberry_framework.scalars import Upload as ScalarsUpload
from django_strawberry_framework.types import converters


def test_version():
    # This version-only change must not widen the package-root __all__;
    # DjangoDebugExtension is a subpackage export.
    assert __version__ == "0.0.15"


def test_logger_name_is_django_strawberry_framework():
    # The logger name is the consumer-visible key used in Django's
    # ``LOGGING`` config dict. Pin the string so an accidental rename
    # (e.g., to ``"djsf"``) is caught at test time.
    assert isinstance(logger, logging.Logger)
    assert logger.name == "django_strawberry_framework"


def test_optimizer_subpackage_reexports_top_level_logger():
    # ``optimizer/__init__.py`` re-exports the top-level package logger
    # rather than declaring a second ``getLogger`` call, so the
    # ``"django_strawberry_framework"`` literal lives in exactly one
    # source location.
    assert optimizer_logger is logger


def test_public_api_surface_is_pinned():
    # Pin ``__all__`` so silent surface widening (e.g., accidental
    # re-export of an internal name) shows up at test time. New public
    # names only land when a future spec adds them; a version bump alone
    # does not imply public-surface widening.
    # The four-symbol mutation surface (spec-036) is complete: ``FieldError``,
    # ``DjangoMutation`` + ``DjangoModelPermission``, and ``DjangoMutationField``.
    # spec-037 adds the three file/upload symbols: ``Upload`` (the
    # re-exported Strawberry scalar) plus ``DjangoFileType`` / ``DjangoImageType``
    # (the structured read-output objects). spec-038 adds two form-mutation
    # symbols (``DjangoFormMutation`` / ``DjangoModelFormMutation``). spec-040 (the
    # auth-mutations card) owns the ``0.0.13`` cut (Decision 12) jointly with the
    # spec-039 serializer flavor; the auth surface adds NO package-root exports
    # (submodule-only per Decision 3). The mutation-atomicity card adds the two
    # schema symbols: ``DjangoSchema`` (the
    # REQUIRED schema class for generated mutations - its execution context holds
    # each mutation's transaction open through response completion) and
    # ``DjangoMutationExecutionContext`` (the subclassing seam for consumers with
    # their own execution context). The resource-policy card (spec-047) adds
    # ``DEFAULT_RESOURCE_POLICY`` / ``RESOURCE_LIMIT_ERROR_CODE`` /
    # ``ResourceLimitExceeded`` / ``ResourcePolicy`` /
    # ``DjangoResourcePolicyExtension``. The secure-output card (spec-048) adds the
    # two opt-in file/image output objects (``DjangoFilePathType`` /
    # ``DjangoImagePathType``, spec-048 Decision 1) and the three
    # production-error-policy symbols (``DEFAULT_ERROR_POLICY`` /
    # ``ErrorPolicy`` / ``DjangoErrorPolicyExtension``, Decision 7). All of these
    # cards shipped in ``0.0.14``; the ``0.0.15`` version cut leaves this
    # public surface unchanged.
    assert django_strawberry_framework.__all__ == (
        "DEFAULT_ERROR_POLICY",
        "DEFAULT_RESOURCE_POLICY",
        "RESOURCE_LIMIT_ERROR_CODE",
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
        "OptimizerHint",
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


def test_file_upload_exports_resolve_to_their_source_definitions():
    # The three spec-037 root exports are re-exports, not new
    # definitions: ``Upload`` rides through ``.scalars`` (which itself
    # re-exports Strawberry's built-in), and the two output objects are the
    # exact ``types.converters`` classes. Pin the re-export IDENTITY so a stray
    # parallel definition (or a wrong canonical import site) is caught, not just
    # ``__all__`` membership.
    assert Upload is ScalarsUpload
    assert DjangoFileType is converters.DjangoFileType
    assert DjangoImageType is converters.DjangoImageType


def test_dynamic_drf_soft_exports_via_getattr():
    """Verify DRF soft exports resolve dynamically through package __getattr__."""
    from django_strawberry_framework import (
        NestedSerializerConfig,
        SerializerFieldConversion,
        SerializerHookContext,
        SerializerMutation,
        UploadMetadata,
        describe_serializer_input,
        register_serializer_field_converter,
    )

    assert SerializerMutation is not None
    assert callable(register_serializer_field_converter)
    assert SerializerFieldConversion is not None
    assert callable(describe_serializer_input)
    assert NestedSerializerConfig is not None
    assert SerializerHookContext is not None
    assert UploadMetadata is not None


def test_dynamic_getattr_non_memoization():
    """Verify package __getattr__ does not pollute module __dict__."""
    _ = django_strawberry_framework.SerializerMutation
    assert "SerializerMutation" not in django_strawberry_framework.__dict__


def test_dynamic_getattr_unknown_attribute_error():
    """Verify unknown attribute access on package root raises AttributeError."""
    import pytest

    with pytest.raises(AttributeError, match="has no attribute 'unregistered_symbol_xyz'"):
        _ = django_strawberry_framework.unregistered_symbol_xyz


def test_star_import_preserves_namespace_hygiene():
    """Verify `from django_strawberry_framework import *` only imports __all__."""
    ns: dict = {}
    exec("from django_strawberry_framework import *", ns)

    assert "SerializerMutation" not in ns
    assert "_DRF_SOFT_EXPORTS" not in ns
    assert "__getattr__" not in ns

    for sym in django_strawberry_framework.__all__:
        assert sym in ns


def test_reexported_types_resolve_to_canonical_subpackage_definitions():
    """Verify all re-exported symbols on root resolve by identity to their defining modules."""
    from django_strawberry_framework import (
        DjangoErrorPolicyExtension,
        DjangoFormMutation,
        DjangoModelFormMutation,
        DjangoModelPermission,
        DjangoMutation,
        DjangoMutationField,
        DjangoOptimizerExtension,
        DjangoResourcePolicyExtension,
        DjangoType,
        FieldError,
        SyncMisuseError,
        finalize_django_types,
    )
    from django_strawberry_framework.extensions import (
        DjangoErrorPolicyExtension as ExtErrorPolicy,
    )
    from django_strawberry_framework.extensions import (
        DjangoResourcePolicyExtension as ExtResourcePolicy,
    )
    from django_strawberry_framework.forms import (
        DjangoFormMutation as FormsDjangoFormMutation,
    )
    from django_strawberry_framework.forms import (
        DjangoModelFormMutation as FormsDjangoModelFormMutation,
    )
    from django_strawberry_framework.mutations import (
        DjangoModelPermission as MutationsDjangoModelPermission,
    )
    from django_strawberry_framework.mutations import (
        DjangoMutation as MutationsDjangoMutation,
    )
    from django_strawberry_framework.mutations import (
        DjangoMutationField as MutationsDjangoMutationField,
    )
    from django_strawberry_framework.mutations import (
        FieldError as MutationsFieldError,
    )
    from django_strawberry_framework.optimizer import (
        DjangoOptimizerExtension as OptDjangoOptimizerExtension,
    )
    from django_strawberry_framework.types import (
        DjangoType as TypesDjangoType,
    )
    from django_strawberry_framework.types import (
        SyncMisuseError as TypesSyncMisuseError,
    )
    from django_strawberry_framework.types import (
        finalize_django_types as types_finalize_django_types,
    )

    assert DjangoType is TypesDjangoType
    assert SyncMisuseError is TypesSyncMisuseError
    assert finalize_django_types is types_finalize_django_types
    assert DjangoOptimizerExtension is OptDjangoOptimizerExtension
    assert DjangoFormMutation is FormsDjangoFormMutation
    assert DjangoModelFormMutation is FormsDjangoModelFormMutation
    assert DjangoModelPermission is MutationsDjangoModelPermission
    assert DjangoMutation is MutationsDjangoMutation
    assert DjangoMutationField is MutationsDjangoMutationField
    assert FieldError is MutationsFieldError
    assert DjangoErrorPolicyExtension is ExtErrorPolicy
    assert DjangoResourcePolicyExtension is ExtResourcePolicy
