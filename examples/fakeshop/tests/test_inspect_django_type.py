"""Fakeshop project command tests for inspect_django_type against example DjangoTypes.

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
    "apps.accounts.schema",
)


def _reload_inspect_schema() -> None:
    """Clear the registry and reload the library + project schema modules.

    Mirrors ``test_library_api.py``'s reload pattern so bare-name resolution
    is order-independent: a test run alone behaves identically to one run after
    a sibling package test cleared the global registry. ``apps.scalars.schema``
    is reloaded too so the consumer-override demonstration type
    (``OverriddenScalarSpecimenType``) is registered + finalized for bare-name
    inspection alongside the library types. ``apps.accounts.schema`` (spec-040
    Slice 1) is reloaded before ``config.schema`` so its ``UserType`` is
    re-registered after the clear rather than left stranded in ``sys.modules``
    (a foreign worker that already imported it would otherwise leave the cached
    module unrefreshed, and the aggregate ``config.schema`` build would raise
    ``DuplicatedTypeName`` on ``UserType``).
    """
    registry.clear()
    for name in (
        "apps.library.schema",
        "apps.scalars.schema",
        "apps.accounts.schema",
        "config.schema",
    ):
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
    # Relay-Node pk (BookType declares ``interfaces = (relay.Node,)`` since
    # spec-032 Slice 6): the interface-supplied GlobalID!, not a plain Int!.
    assert "id" in text
    assert "GlobalID!" in text
    assert "relay.Node id" in text
    # Per-row assertions so ``subtitle``'s String intent cannot false-green
    # against the ``title`` row's ``String!`` (``String`` is a substring of it).
    title_row = _field_row(text, "title")
    assert "String!" in title_row
    assert " no " in title_row
    # The converter column names the matched SCALAR_MAP row (TextField), the
    # MRO ancestor that fired -- not, in the subclass case, the concrete class.
    assert "SCALAR_MAP[TextField]" in title_row
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
    assert "GlobalID!" in text
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

    The eviction strands a half-registered ``apps.library.schema`` (re-imported by
    the ``--schema`` load but never reset to a complete project schema) in
    ``sys.modules``, which can collide at a later same-worker aggregate build ->
    ``DuplicatedTypeName``. Restore the FULL project schema on teardown via the
    shared ``schema_reload.reload_all_project_schemas`` discipline so this cold-start
    simulation leaves the worker clean for the next test.
    """
    for name in _SCHEMA_MODULES:
        sys.modules.pop(name, None)
    registry.clear()

    try:
        out = StringIO()
        call_command("inspect_django_type", "BookType", "--schema", selector, stdout=out)
        text = out.getvalue()
        assert "BookType" in text
        assert "title" in text
        assert "String!" in text
        assert "subtitle" in text
        assert "circulation_status" in text
        assert "choice enum" in text
    finally:
        from schema_reload import reload_all_project_schemas

        reload_all_project_schemas()


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
    # Forward FK, M2M, and reverse FK render their resolved list / type
    # annotations and the friendly relation label in the converter column.
    shelf_row = _field_row(text, "shelf")
    assert "ShelfType!" in shelf_row
    assert "relation: forward FK" in shelf_row
    genres_row = _field_row(text, "genres")
    assert "[GenreType!]!" in genres_row
    assert "relation: M2M" in genres_row
    loans_row = _field_row(text, "loans")
    assert "[LoanType!]!" in loans_row
    assert "relation: reverse FK" in loans_row


def test_inspect_consumer_authored_relation_field(reload_inspect_schema):
    """A live ``@strawberry.field`` relation override renders from the resolved type.

    ``BranchType.shelves`` (``apps/library/schema.py``) shadows the ``shelves``
    reverse-FK column with a consumer ``@strawberry.field`` resolver, so
    ``_build_annotations`` skips auto-synthesis for it and ``origin.__annotations__``
    holds a ``StrawberryAnnotation`` (not a renderable type). The command must read
    the resolved type from the finalized Strawberry field metadata - printing the
    real ``[ShelfType!]!`` list and the ``consumer strawberry.field (relation)``
    converter, NOT the auto reverse-FK label nor the ``StrawberryAnnotation`` repr.
    """
    out = StringIO()
    call_command("inspect_django_type", "BranchType", stdout=out)
    text = out.getvalue()
    shelves_row = _field_row(text, "shelves")
    assert "[ShelfType!]!" in shelves_row
    assert " no (list) " in shelves_row
    assert "consumer strawberry.field (relation)" in shelves_row
    # The auto reverse-FK converter must NOT fire for the overridden field, and
    # the StrawberryAnnotation repr must never leak into the type column.
    assert "relation: reverse FK" not in shelves_row
    assert "StrawberryAnnotation" not in text


def test_inspect_consumer_authored_scalar_override_matrix(reload_inspect_schema):
    """``OverriddenScalarSpecimenType`` shows every consumer-authored scalar corner live.

    The scalars app's ``OverriddenScalarSpecimenType`` (``apps/scalars/schema.py``)
    overrides four columns four different ways; the command's converter column must
    name the row that actually produced each field, never the auto ``SCALAR_MAP``
    converter that ``_build_annotations`` skipped:

    - ``label`` - assigned ``@strawberry.field`` -> ``consumer strawberry.field (scalar)``
    - ``quantity`` - annotation-only widening (``Int`` column -> nullable ``Float``)
      -> ``consumer annotation (scalar)``, exercising the ``StrawberryOptional`` path
    - ``score`` - ``annotation + strawberry.field`` overlap idiom
    - ``token`` - annotation escape hatch over the unsupported ``Base36Field``

    The ``note`` field is the inverse: declared ``note: auto`` (declare-but-infer),
    so it is *not* a consumer override and its converter column names the auto
    ``SCALAR_MAP`` row exactly as a bare-selected field would.
    """
    out = StringIO()
    call_command("inspect_django_type", "OverriddenScalarSpecimenType", stdout=out)
    text = out.getvalue()

    label_row = _field_row(text, "label")
    assert "String!" in label_row
    assert "consumer strawberry.field (scalar)" in label_row
    assert "SCALAR_MAP" not in label_row

    quantity_row = _field_row(text, "quantity")
    assert "Float" in quantity_row
    assert "Float!" not in quantity_row
    assert " yes " in quantity_row
    assert "consumer annotation (scalar)" in quantity_row

    score_row = _field_row(text, "score")
    assert "Int!" in score_row
    assert "consumer annotation + strawberry.field (scalar)" in score_row

    token_row = _field_row(text, "token")
    assert "String!" in token_row
    assert "consumer annotation (scalar)" in token_row
    assert "SCALAR_MAP" not in token_row

    # ``note: auto`` is declare-but-infer, not an override: the auto SCALAR_MAP
    # converter still produces it, and it never reports a consumer-authored source.
    note_row = _field_row(text, "note")
    assert "String!" in note_row
    assert "SCALAR_MAP" in note_row
    assert "consumer" not in note_row


def test_inspect_relay_node_pk_row(reload_inspect_schema):
    """GenreType declares ``interfaces = (relay.Node,)`` - its pk is suppressed.

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
    NOT a ``convert_scalar`` re-run - a re-run would reproduce the column-native
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
