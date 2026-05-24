"""Tests for the django_strawberry_framework package init."""

import logging

import django_strawberry_framework
from django_strawberry_framework import __version__, logger
from django_strawberry_framework.optimizer import logger as optimizer_logger


def test_version():
    assert __version__ == "0.0.7"


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
    # names only land when a future spec adds them; routine slices
    # bump ``__version__`` without widening the surface.
    assert django_strawberry_framework.__all__ == (
        "BigInt",
        "DjangoListField",
        "DjangoOptimizerExtension",
        "DjangoType",
        "OptimizerHint",
        "__version__",
        "auto",
        "finalize_django_types",
    )
