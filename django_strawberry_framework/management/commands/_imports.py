"""Shared importer-to-``CommandError`` helper for the framework's management commands.

Both ``export_schema`` and ``inspect_django_type`` resolve a consumer-supplied
dotted path/selector and must turn an import failure into a clean
``CommandError`` rather than a raw traceback. The catch-and-rewrap tail
(``except (ImportError, AttributeError) as e: raise CommandError(str(e)) from e``)
was byte-identical across three call sites that use two different importers
(Strawberry's ``import_module_symbol`` vs Django's ``import_string``) and where
one site discards the resolved value (import-for-side-effect). The helper takes
the importer as a zero-arg callable so each call site keeps its own importer and
arguments visible while sharing one error-handling shape.
"""

from collections.abc import Callable
from typing import TypeVar

from django.core.management.base import CommandError

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
