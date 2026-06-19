"""Package init tests for version metadata and public exports."""

# TODO(spec-037 Slice 3/4): pin the public file/upload exports and version cut.
# Pseudo-code:
# - assert __all__ includes Upload, DjangoFileType, and DjangoImageType.
# - assert importing those names from django_strawberry_framework succeeds.
# - update test_version to 0.0.11 only with pyproject.toml, __init__.__version__,
#   uv.lock, and docs/GLOSSARY.md aligned.

import logging

import django_strawberry_framework
from django_strawberry_framework import __version__, logger
from django_strawberry_framework.optimizer import logger as optimizer_logger


def test_version():
    assert __version__ == "0.0.10"


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
    # The four-symbol mutation surface is complete: ``FieldError`` (Slice 1),
    # ``DjangoMutation`` + ``DjangoModelPermission`` (Slice 2), and
    # ``DjangoMutationField`` (Slice 3). ``test_version`` is untouched because the
    # joint 0.0.11 cut owns the version assertion.
    assert django_strawberry_framework.__all__ == (
        "BigInt",
        "DjangoConnection",
        "DjangoConnectionField",
        "DjangoListField",
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
        "__version__",
        "aapply_cascade_permissions",
        "apply_cascade_permissions",
        "auto",
        "finalize_django_types",
        "strawberry_config",
    )
