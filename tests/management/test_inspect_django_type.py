"""Management command tests for inspect_django_type field-resolution tables.

Failure-mode coverage for the ``CommandError`` paths not reachable from a live
registered type, mirroring ``tests/management/test_export_schema.py``'s
``_make_test_module`` + ``monkeypatch.setitem(sys.modules, ...)`` pattern. The
happy-path command behavior is earned against the real fakeshop schema in
``examples/fakeshop/tests/test_inspect_django_type.py`` (a management command is
not reachable over ``/graphql/``, so the in-process example tier is its home).

Also holds direct unit tests for the module's internal helpers
(``_matched_scalar_key``, ``_render_annotation``) whose distinguishing branches
-- a consumer field subclass resolving to a supported MRO ancestor, and a
multi-member union annotation -- are unreachable from the fakeshop schema's live
surface and so are earned here in the package tier.

Finally, holds the one consumer-authored-field command test that is genuinely
unreachable from the live example surface: an annotation-only relation whose
forward reference cannot resolve from the type's module namespace, so Strawberry
leaves ``field.type`` as its ``UNRESOLVED`` sentinel after ``finalize_django_types()``
alone. It needs a type defined in a non-importable (function-local) scope, so it is
earned here. Every *resolvable* consumer-override corner -- assigned scalar,
annotation-only scalar (incl. the forced-optional and unsupported-field cases),
the ``annotation + strawberry.field`` overlap, and the assigned relation -- is
demonstrated live and inspected from the example tier against
``OverriddenScalarSpecimenType`` / ``BranchType`` in
``examples/fakeshop/tests/test_inspect_django_type.py`` (the scalars app's
``Base36Field`` supplies the unsupported column).

Also holds the ``relation_shapes = {<rel>: "connection"}`` regression: no example
type declares a connection-only relation shape, and adding one to an existing
example type would drop its list field from the SDL and break the live API /
relation-row coverage that asserts the list form. So the connection-only shape is
pinned here against real fakeshop models, finalized in registry isolation.
"""

import sys
import types
from io import StringIO

import pytest
from apps.products.models import Category, Item
from django.core.management import CommandError, call_command
from django.db import models
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.management.commands.inspect_django_type import (
    Command,
    _matched_scalar_key,
    _render_annotation,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.converters import DjangoFileType, DjangoImageType


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def _make_test_module(monkeypatch, **attrs):
    module = types.ModuleType("test_module")
    for key, value in attrs.items():
        setattr(module, key, value)
    monkeypatch.setitem(sys.modules, "test_module", module)
    return module


def test_bad_dotted_path_raises_command_error():
    # The original import error surfaces - it is NOT swallowed and retried as a
    # registry miss.
    with pytest.raises(CommandError, match="No module named"):
        call_command("inspect_django_type", "does.not.exist.Type")


def test_ambiguous_bare_name_raises_command_error():
    # Two DjangoType classes against different models sharing one __name__.
    meta_a = type("Meta", (), {"model": Category, "fields": ("id", "name")})
    type("DupType", (DjangoType,), {"Meta": meta_a})
    meta_b = type("Meta", (), {"model": Item, "fields": ("id", "name")})
    type("DupType", (DjangoType,), {"Meta": meta_b})

    with pytest.raises(CommandError, match=r"DupType is ambiguous.*Category.*Item"):
        call_command("inspect_django_type", "DupType")


def test_bad_schema_selector_raises_command_error():
    # A --schema selector that cannot be imported surfaces as CommandError
    # (the import failure is caught before any type resolution runs).
    with pytest.raises(CommandError, match="No module named"):
        call_command("inspect_django_type", "BookType", "--schema", "nonexistent_xyz_module")


def test_unregistered_bare_name_raises_command_error():
    # A bare name with no registry match (registry cleared by the autouse
    # fixture) raises the "import the project schema first" CommandError.
    with pytest.raises(CommandError, match="Import the project schema first"):
        call_command("inspect_django_type", "TotallyUnregisteredType")


def test_non_djangotype_symbol_raises_command_error(monkeypatch):
    _make_test_module(monkeypatch, not_a_type=object())
    with pytest.raises(CommandError, match="is not a DjangoType subclass"):
        call_command("inspect_django_type", "test_module.not_a_type")


def test_abstract_base_without_definition_raises_command_error(monkeypatch):
    # A DjangoType subclass with no Meta never registers a definition.
    class AbstractBase(DjangoType):
        pass

    _make_test_module(monkeypatch, AbstractBase=AbstractBase)
    with pytest.raises(CommandError, match="not a registered DjangoType"):
        call_command("inspect_django_type", "test_module.AbstractBase")


def test_unfinalized_type_raises_command_error(monkeypatch):
    # A concrete registered DjangoType whose definition.finalized is False
    # (finalize_django_types() has not run) is a distinct branch from the
    # no-definition case above.
    class ConcreteType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert ConcreteType.__django_strawberry_definition__.finalized is False
    _make_test_module(monkeypatch, ConcreteType=ConcreteType)
    with pytest.raises(CommandError, match=r"finalize_django_types\(\) has not run"):
        call_command("inspect_django_type", "test_module.ConcreteType")


def test_matched_scalar_key_names_supported_mro_ancestor():
    # A consumer subclass of a supported field must report the SCALAR_MAP row
    # that actually fired (the matched MRO ancestor), not its own concrete class.
    class CustomTextField(models.TextField):
        pass

    assert _matched_scalar_key(CustomTextField()) == "TextField"
    # A directly-supported field reports its own class (ancestor == concrete).
    assert _matched_scalar_key(models.CharField()) == "CharField"


class _FakeOrigin:
    def __init__(self, annotations):
        self.__annotations__ = annotations


class _FakeDefinition:
    def __init__(self, annotations):
        self.origin = _FakeOrigin(annotations)


@pytest.mark.parametrize(
    ("field_cls", "output_type"),
    [(models.FileField, DjangoFileType), (models.ImageField, DjangoImageType)],
)
def test_scalar_row_names_file_output_converter_not_scalar_map(field_cls, output_type):
    """A FileField / ImageField column's converter column names the output-map converter.

    The read-side annotation for a file/image column is the structured
    ``DjangoFileType`` / ``DjangoImageType`` output object, produced by
    ``convert_field_output`` via ``FIELD_OUTPUT_TYPE_MAP`` -- NOT by
    ``SCALAR_MAP`` (whose ``FileField`` / ``ImageField`` rows deliberately stay
    ``str`` for the filter-input path). The converter column previously read
    ``SCALAR_MAP[FileField]`` here, mis-attributing the converter to the row that
    fired only on the filter path while the displayed type came from elsewhere.
    The label must name the converter that actually produced the shown type, and
    an ``ImageField`` (a ``FileField`` subclass) must resolve to ``DjangoImageType``
    via the shared MRO walk, never silently falling through to ``DjangoFileType``.
    """
    field = field_cls()
    field.name = "attachment"
    definition = _FakeDefinition({"attachment": output_type | None})

    graphql_type, nullable, converter = Command._scalar_row(definition, field)

    assert graphql_type == f"{output_type.__name__}"
    assert nullable == "yes"
    assert converter == f"convert_field_output -> {output_type.__name__}"
    assert "SCALAR_MAP" not in converter


def test_render_annotation_renders_multi_member_union():
    # A consumer-authored union annotation (>1 non-None member) renders each
    # member name joined by " | " with no trailing "!" on the members.
    assert _render_annotation(int | str) == "Int | String"


def test_inspect_unresolved_forward_ref_relation_raises_command_error():
    """An annotation-only relation forward ref ``finalize`` can't resolve raises CommandError.

    ``CatType.items: list["ItemType"]`` is an annotation-only relation override.
    Both types are defined in this function's local scope, so the ``"ItemType"``
    forward reference is absent from the type's module globals; Strawberry leaves
    ``field.type`` as its ``UNRESOLVED`` sentinel after ``finalize_django_types()``
    alone (constructing a ``strawberry.Schema`` would force resolution). The
    command must refuse to print the sentinel as a real GraphQL type -- which is
    exactly the field Strawberry itself rejects at schema-build time -- and raise
    ``CommandError`` with a recovery hint instead.
    """

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CatType(DjangoType):
        items: list["ItemType"]

        class Meta:
            model = Category
            fields = ("id", "items")

    finalize_django_types()
    with pytest.raises(CommandError, match=r"unresolved Strawberry forward reference"):
        call_command("inspect_django_type", "CatType")


def _connection_row(text: str, field_name: str) -> str:
    """Return the table row whose first token is ``field_name`` (per-row isolation)."""
    for line in text.splitlines():
        if line.strip().split(" ", 1)[:1] == [field_name]:
            return line
    raise AssertionError(f"no row for field {field_name!r} in:\n{text}")


def test_inspect_connection_only_relation_shape_renders_row():
    """A ``relation_shapes = {<rel>: "connection"}`` relation renders, never KeyErrors.

    The Phase-2.5 synthesizer pops the relation's generated ``list[T]``
    annotation for the ``"connection"`` shape
    (``types/finalizer.py::_suppress_relation_list_form``) while leaving the
    Django field in ``selected_fields``, so ``_relation_row`` used to index
    ``origin.__annotations__[field.name]`` for a key that no longer exists and
    crash with an unhandled ``KeyError`` (a raw traceback, not a clean
    ``CommandError``) on a legitimately finalized, schema-buildable type.

    The row must instead render from the synthesized ``<rel>_connection``
    sibling's authoritative Strawberry field metadata: the resolved connection
    type (``ItemNodeConnection!``) and a converter column naming the
    connection-only shape. Both types are Relay-Node-shaped so the many-side
    relation is eligible for connection synthesis.
    """

    class ItemNode(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")
            interfaces = (relay.Node,)
            relation_shapes = {"items": "connection"}

    finalize_django_types()
    out = StringIO()
    call_command("inspect_django_type", "CategoryNode", stdout=out)
    text = out.getvalue()

    items_row = _connection_row(text, "items")
    # Resolved connection type from the synthesized sibling, not a KeyError and
    # not the suppressed ``[ItemNode!]!`` list form.
    assert "ItemNodeConnection!" in items_row
    assert "[ItemNode!]!" not in items_row
    # The converter names the relation cardinality AND the connection-only shape.
    assert "relation: reverse FK (connection-only)" in items_row
