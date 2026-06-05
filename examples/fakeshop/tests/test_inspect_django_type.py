"""Project-level inspect_django_type command tests for the fakeshop schema.

Happy-path coverage via in-process ``call_command``. Bare-name resolution needs
a finalized registry, so the bare-name tests run under a registry-clear +
reload fixture mirroring
``examples/fakeshop/test_query/test_library_api.py::_reload_library_project_schema``;
the cold-path ``--schema`` test instead simulates a cold CLI process by evicting
the schema modules from ``sys.modules`` so the ``--schema`` import re-runs
registration + finalization on its own.
"""

import importlib
import sys
from io import StringIO

import pytest
from django.core.management import call_command

from django_strawberry_framework.registry import registry


def _field_row(text: str, field_name: str) -> str:
    """Return the single table row whose first token is ``field_name``.

    The command renders one row per selected field with a leading two-space
    indent, the field name in a left-justified column, then the django field
    type / graphql type / nullable / converter columns. Splitting on the row's
    first whitespace token isolates the row so per-row substring assertions
    (e.g. ``String`` vs ``String!``) cannot false-green against another row.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.split(" ", 1)[:1] == [field_name]:
            return line
    raise AssertionError(f"no row for field {field_name!r} in:\n{text}")


_SCHEMA_MODULES = (
    "config.schema",
    "apps.library.schema",
    "apps.products.schema",
    "apps.scalars.schema",
    "apps.kanban.schema",
    "apps.glossary.schema",
)


def _reload_inspect_schema() -> None:
    """Clear the registry and reload the library + project schema modules.

    Mirrors ``test_library_api.py``'s reload pattern so bare-name resolution
    is order-independent: a test run alone behaves identically to one run after
    a sibling package test cleared the global registry.
    """
    registry.clear()
    for name in ("apps.library.schema", "config.schema"):
        module = sys.modules.get(name)
        if module is None:
            importlib.import_module(name)
        else:
            importlib.reload(module)


@pytest.fixture
def reload_inspect_schema():
    """Recreate the project schema around package-test registry clears."""
    _reload_inspect_schema()


def test_inspect_by_registered_name(reload_inspect_schema):
    out = StringIO()
    call_command("inspect_django_type", "BookType", stdout=out)
    text = out.getvalue()
    assert "BookType" in text
    # Non-Relay pk renders as a plain Int!, NOT GlobalID! (BookType declares no interfaces).
    assert "id" in text
    assert "Int!" in text
    assert "GlobalID!" not in text
    # Per-row assertions so ``subtitle``'s String intent cannot false-green
    # against the ``title`` row's ``String!`` (``String`` is a substring of it).
    title_row = _field_row(text, "title")
    assert "String!" in title_row
    assert " no " in title_row
    subtitle_row = _field_row(text, "subtitle")
    assert "String" in subtitle_row
    assert "String!" not in subtitle_row
    assert " yes " in subtitle_row
    assert "circulation_status" in text
    assert "choice enum" in text
    assert "genres" in text
    assert "[GenreType!]!" in text


def test_inspect_by_dotted_path(reload_inspect_schema):
    out = StringIO()
    call_command("inspect_django_type", "apps.library.schema.BookType", stdout=out)
    text = out.getvalue()
    assert "BookType" in text
    assert "Int!" in text
    assert "title" in text
    assert "String!" in text
    assert "subtitle" in text
    assert "circulation_status" in text
    assert "choice enum" in text


@pytest.mark.parametrize("selector", ["config.schema", "config.schema:schema"])
def test_inspect_with_schema_option(selector):
    """Cold path: --schema must register + finalize on its own.

    An in-process ``registry.clear()`` alone is not a cold start because
    ``import_module_symbol`` returns the cached module without re-running its
    import-time side effects. Evict the schema modules from ``sys.modules`` so
    the ``--schema`` import re-executes class registration + finalize.
    """
    for name in _SCHEMA_MODULES:
        sys.modules.pop(name, None)
    registry.clear()

    out = StringIO()
    call_command("inspect_django_type", "BookType", "--schema", selector, stdout=out)
    text = out.getvalue()
    assert "BookType" in text
    assert "title" in text
    assert "String!" in text
    assert "subtitle" in text
    assert "circulation_status" in text
    assert "choice enum" in text


def test_inspect_choice_field_row(reload_inspect_schema):
    out = StringIO()
    call_command("inspect_django_type", "BookType", stdout=out)
    text = out.getvalue()
    assert "circulation_status" in text
    assert "BookTypeCirculationStatusEnum" in text
    assert "choice enum" in text


def test_inspect_relation_field_rows(reload_inspect_schema):
    out = StringIO()
    call_command("inspect_django_type", "BookType", stdout=out)
    text = out.getvalue()
    # Forward FK, M2M, and reverse FK render their resolved list / type annotations.
    assert "shelf" in text
    assert "ShelfType!" in text
    assert "genres" in text
    assert "[GenreType!]!" in text
    assert "loans" in text
    assert "[LoanType!]!" in text


def test_inspect_relay_node_pk_row(reload_inspect_schema):
    """GenreType declares ``interfaces = (relay.Node,)`` — its pk is suppressed.

    The pk row must report the interface-supplied ``GlobalID!`` / ``relay.Node
    id``, sourced from the interface rather than indexing
    ``origin.__annotations__[pk_name]`` (which would ``KeyError``).
    """
    out = StringIO()
    call_command("inspect_django_type", "GenreType", stdout=out)
    text = out.getvalue()
    assert "GenreType" in text
    assert "GlobalID!" in text
    assert "relay.Node id" in text


def test_inspect_reads_resolved_annotation_not_field_null(reload_inspect_schema):
    """The command reports the post-override nullability for the Slice-3 acceptance type.

    Cross-slice (Slice-2 command over the Slice-3 ``NullabilityOverrideBookType``
    type), deferred from the Slice 2 cycle to here because the type did not yet
    exist. ``title`` is a ``NOT NULL`` column flipped to ``String`` by
    ``nullable_overrides``; ``subtitle`` is a ``null=True`` column flipped to
    ``String!`` by ``required_overrides``. The command reads the resolved
    annotation from ``origin.__annotations__`` (which the override bakes in),
    NOT a ``convert_scalar`` re-run — a re-run would reproduce the column-native
    ``field.null`` and report the OPPOSITE result, so this distinguishes the two.
    """
    out = StringIO()
    call_command("inspect_django_type", "NullabilityOverrideBookType", stdout=out)
    text = out.getvalue()
    assert "NullabilityOverrideBookType" in text
    # title: forced nullable -> reported String (NOT String!) and nullable=yes.
    title_row = _field_row(text, "title")
    assert "String" in title_row
    assert "String!" not in title_row
    assert " yes " in title_row
    # subtitle: forced required -> reported String! and nullable=no.
    subtitle_row = _field_row(text, "subtitle")
    assert "String!" in subtitle_row
    assert " no " in subtitle_row
