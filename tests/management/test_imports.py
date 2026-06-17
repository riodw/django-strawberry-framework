"""Tests for the shared ``import_or_command_error`` management-command helper.

The helper backs three call sites across ``export_schema`` and
``inspect_django_type`` (their per-command tests exercise the live importer
branches via ``call_command``); these pin the helper's contract directly: it
catches ``ImportError`` AND ``AttributeError``, re-raises ``CommandError`` with
the original ``str(e)`` message and ``__cause__`` chaining, and passes the
importer's return value through unchanged (the discard site simply ignores it).
"""

import pytest
from django.core.management import CommandError

from django_strawberry_framework.management.commands._imports import import_or_command_error


def test_import_or_command_error_passes_through_return_value():
    sentinel = object()
    assert import_or_command_error(lambda: sentinel) is sentinel


def test_import_or_command_error_wraps_import_error():
    original = ImportError("No module named 'nope'")

    def importer():
        raise original

    with pytest.raises(CommandError, match="No module named 'nope'") as exc_info:
        import_or_command_error(importer)
    assert exc_info.value.__cause__ is original


def test_import_or_command_error_wraps_attribute_error():
    original = AttributeError("module 'm' has no attribute 'x'")

    def importer():
        raise original

    with pytest.raises(CommandError, match="has no attribute 'x'") as exc_info:
        import_or_command_error(importer)
    assert str(exc_info.value) == str(original)
    assert exc_info.value.__cause__ is original


def test_import_or_command_error_does_not_swallow_other_exceptions():
    def importer():
        raise ValueError("unrelated")

    with pytest.raises(ValueError, match="unrelated"):
        import_or_command_error(importer)
