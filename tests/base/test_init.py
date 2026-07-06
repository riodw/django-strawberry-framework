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
    assert __version__ == "0.0.13"


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
    # names only land when a future spec adds them; version changes are
    # maintainer-commanded and do not imply public-surface widening.
    # The four-symbol mutation surface (spec-036) is complete: ``FieldError``,
    # ``DjangoMutation`` + ``DjangoModelPermission``, and ``DjangoMutationField``.
    # spec-037 Slice 3 adds the three file/upload symbols: ``Upload`` (the
    # re-exported Strawberry scalar) plus ``DjangoFileType`` / ``DjangoImageType``
    # (the structured read-output objects). spec-038 adds two form-mutation
    # symbols (``DjangoFormMutation`` / ``DjangoModelFormMutation``). spec-040 (the
    # auth-mutations card) owns the ``0.0.13`` cut (Decision 12) jointly with the
    # spec-039 serializer flavor, so ``test_version`` is asserted at ``0.0.13``
    # above; the auth surface adds NO package-root exports (submodule-only per
    # Decision 3), so ``__all__`` is unchanged.
    assert django_strawberry_framework.__all__ == (
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


def test_file_upload_exports_resolve_to_their_source_definitions():
    # The three spec-037 Slice 3 root exports are re-exports, not new
    # definitions: ``Upload`` rides through ``.scalars`` (which itself
    # re-exports Strawberry's built-in), and the two output objects are the
    # exact ``types.converters`` classes. Pin the re-export IDENTITY so a stray
    # parallel definition (or a wrong canonical import site) is caught, not just
    # ``__all__`` membership.
    assert Upload is ScalarsUpload
    assert DjangoFileType is converters.DjangoFileType
    assert DjangoImageType is converters.DjangoImageType
