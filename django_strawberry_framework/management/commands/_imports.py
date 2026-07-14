"""Import helpers that translate bad management-command paths to ``CommandError``."""

from collections.abc import Callable
from typing import TypeVar

from django.core.management.base import CommandError
from django.utils.module_loading import import_string
from strawberry.utils.importer import import_module_symbol

T = TypeVar("T")


def import_or_command_error(importer: Callable[[], T]) -> T:
    """Run ``importer`` and re-raise ``ImportError``/``AttributeError`` as ``CommandError``.

    Returns the importer's value unchanged (call sites that import purely for
    side effect simply discard it). The original exception is preserved as the
    ``__cause__`` via ``from e`` and its ``str(e)`` becomes the ``CommandError``
    message, so the consumer sees the underlying import error without a traceback.
    """
    try:
        return importer()
    except (ImportError, AttributeError) as e:
        raise CommandError(str(e)) from e


def _validate_absolute_module_path(value: str, module_path: str, *, label: str) -> None:
    """Reject malformed module paths before ``importlib`` raises an unrelated exception."""
    if not module_path:
        raise CommandError(f"{value!r} is not a valid {label}: the module path is empty.")
    if module_path.startswith("."):
        raise CommandError(
            f"{value!r} is not a valid {label}: relative module paths are not supported.",
        )


def import_module_symbol_or_command_error(selector: str, *, default_symbol_name: str) -> object:
    """Resolve an absolute Strawberry ``module[:symbol]`` selector."""
    module_name = selector.split(":", 1)[0]
    _validate_absolute_module_path(selector, module_name, label="schema selector")
    return import_or_command_error(
        lambda: import_module_symbol(selector, default_symbol_name=default_symbol_name),
    )


def import_string_or_command_error(dotted_path: str) -> object:
    """Resolve an absolute Django dotted object path."""
    module_name, separator, _attribute_name = dotted_path.rpartition(".")
    if not separator:
        raise CommandError(
            f"{dotted_path!r} is not a valid dotted object path: a module path is required.",
        )
    _validate_absolute_module_path(dotted_path, module_name, label="dotted object path")
    return import_or_command_error(lambda: import_string(dotted_path))
