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
from enum import Enum
from io import StringIO
from typing import NewType

import pytest
import strawberry
from apps.products.models import Category, Item
from django.core.management import CommandError, call_command
from django.db import models
from django.utils.module_loading import import_string
from strawberry import relay
from strawberry.schema.name_converter import NameConverter

from django_strawberry_framework import DjangoType, finalize_django_types, strawberry_config
from django_strawberry_framework.management.commands.inspect_django_type import (
    Command,
    _matched_scalar_key,
    _render_annotation,
    _scalar_name,
    _sdl_type_name,
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


def test_malformed_dotted_path_raises_command_error():
    with pytest.raises(CommandError, match="module path is empty"):
        call_command("inspect_django_type", ".BookType")


def test_ambiguous_bare_name_lists_copyable_dotted_paths(monkeypatch):
    """Every ambiguity candidate is a directly reusable dotted object path."""
    module_a = types.ModuleType("management_duplicate_types_a")
    module_b = types.ModuleType("management_duplicate_types_b")
    monkeypatch.setitem(sys.modules, module_a.__name__, module_a)
    monkeypatch.setitem(sys.modules, module_b.__name__, module_b)
    meta_a = type("Meta", (), {"model": Category, "fields": ("id", "name")})
    duplicate_a = type(
        "DupType",
        (DjangoType,),
        {"__module__": module_a.__name__, "Meta": meta_a},
    )
    module_a.DupType = duplicate_a
    meta_b = type("Meta", (), {"model": Item, "fields": ("id", "name")})
    duplicate_b = type(
        "DupType",
        (DjangoType,),
        {"__module__": module_b.__name__, "Meta": meta_b},
    )
    module_b.DupType = duplicate_b

    path_a = f"{module_a.__name__}.DupType"
    path_b = f"{module_b.__name__}.DupType"
    with pytest.raises(CommandError, match=r"DupType is ambiguous") as exc_info:
        call_command("inspect_django_type", "DupType")

    message = str(exc_info.value)
    assert f"  - {path_a} (model Category)" in message
    assert f"  - {path_b} (model Item)" in message
    assert import_string(path_a) is duplicate_a
    assert import_string(path_b) is duplicate_b


def test_schema_help_documents_naming_and_cold_process_requirements():
    parser = Command().create_parser("manage.py", "inspect_django_type")
    schema_action = next(
        action for action in parser._actions if "--schema" in action.option_strings
    )

    assert schema_action.help == (
        "Import the project schema first to register and finalize types and use its "
        "naming configuration; required for bare names in a cold process"
    )


def test_schema_option_uses_schema_naming_configuration(monkeypatch):
    """``--schema`` makes object and scalar names match that schema's actual SDL."""

    class PrefixedNames(NameConverter):
        def from_object(self, definition):
            return f"Api{super().from_object(definition)}"

    TokenValue = NewType("TokenValue", str)
    token_definition = strawberry.scalar(name="OpaqueToken", serialize=str)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            primary = True
            fields = ("id", "name")

    class ItemRefType(DjangoType):
        description: TokenValue

        class Meta:
            model = Item
            fields = ("id", "description", "category")

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def item(self) -> ItemRefType:
            raise NotImplementedError

    schema = strawberry.Schema(
        query=Query,
        config=strawberry_config(
            extra_scalar_map={TokenValue: token_definition},
            name_converter=PrefixedNames(),
        ),
    )
    _make_test_module(monkeypatch, schema=schema)
    out = StringIO()
    call_command(
        "inspect_django_type",
        "ItemRefType",
        "--schema",
        "test_module:schema",
        stdout=out,
    )
    rendered = out.getvalue()

    assert "ApiCategoryType!" in _connection_row(rendered, "category")
    assert "OpaqueToken!" in _connection_row(rendered, "description")
    sdl = str(schema)
    assert "category: ApiCategoryType!" in sdl
    assert "description: OpaqueToken!" in sdl


def test_bare_name_resolves_converter_applied_sdl_name_and_titles_it(monkeypatch):
    """A custom ``NameConverter``'s SDL name resolves as a bare name AND titles the table.

    The operator pastes the name they see in the schema (``ApiItemRefType`` under a
    prefixing converter), not the Python class name, and the table title renders
    that same converter-applied name. Both require threading the schema's
    ``NameConverter`` (supplied by ``--schema``) into bare-name resolution and
    table rendering - the pre-fix code matched/titled only ``graphql_type_name``,
    which ignores the converter.
    """

    class PrefixedNames(NameConverter):
        def from_object(self, definition):
            return f"Api{super().from_object(definition)}"

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            primary = True
            fields = ("id", "name")

    class ItemRefType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def item(self) -> ItemRefType:
            raise NotImplementedError

    schema = strawberry.Schema(
        query=Query,
        config=strawberry_config(name_converter=PrefixedNames()),
    )
    _make_test_module(monkeypatch, schema=schema)
    out = StringIO()
    call_command(
        "inspect_django_type",
        "ApiItemRefType",  # the converter-applied SDL name, NOT the Python class name
        "--schema",
        "test_module:schema",
        stdout=out,
    )
    title = out.getvalue().splitlines()[0]
    assert title.startswith("ApiItemRefType  (model:")


def test_bad_schema_selector_raises_command_error():
    # A --schema selector that cannot be imported surfaces as CommandError
    # (the import failure is caught before any type resolution runs).
    with pytest.raises(CommandError, match="No module named"):
        call_command("inspect_django_type", "BookType", "--schema", "nonexistent_xyz_module")


@pytest.mark.parametrize(
    ("selector", "message"),
    [
        ("", "module path is empty"),
        (":schema", "module path is empty"),
        (".config.schema", "relative module paths"),
    ],
)
def test_malformed_schema_selector_raises_command_error(selector, message):
    with pytest.raises(CommandError, match=message):
        call_command("inspect_django_type", "BookType", "--schema", selector)


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


def test_sdl_type_name_ignores_inherited_strawberry_definition():
    """A partially finalized child uses its own pending GraphQL name."""

    @strawberry.type
    class FinalizedParent:
        value: str

    class PendingChild(FinalizedParent):
        pass

    definition = types.SimpleNamespace(graphql_type_name="PendingAlias")

    assert "__strawberry_definition__" not in PendingChild.__dict__
    assert _sdl_type_name(PendingChild, definition, NameConverter()) == "PendingAlias"


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


def test_inspect_uses_sdl_names_for_renamed_relation_and_consumer_enum():
    """Renamed auto-relation and finalized consumer-enum metadata report SDL names."""

    @strawberry.enum(name="PublishedState")
    class State(Enum):
        DRAFT = "draft"

    class RenamedCategoryType(DjangoType):
        class Meta:
            model = Category
            primary = True
            fields = ("id", "name")
            name = "Category"

    class ItemRefType(DjangoType):
        name: State

        class Meta:
            model = Item
            fields = ("id", "name", "category")

    finalize_django_types()
    out = StringIO()
    call_command("inspect_django_type", "ItemRefType", stdout=out)
    text = out.getvalue()

    category_row = _connection_row(text, "category")
    assert "Category!" in category_row
    assert "relation: forward FK" in category_row
    assert "RenamedCategoryType" not in text
    assert "PublishedState!" in _connection_row(text, "name")


def test_bare_name_resolves_meta_name_and_title_uses_graphql_name():
    """Bare lookup + title prefer ``Meta.name`` / ``graphql_type_name`` over ``__name__``."""

    class RenamedCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            name = "Category"

    finalize_django_types()
    out = StringIO()
    # Operator pastes the SDL name from the schema, not the Python class name.
    call_command("inspect_django_type", "Category", stdout=out)
    text = out.getvalue()
    assert text.splitlines()[0].startswith(
        "Category  (model: apps.products.models.Category)",
    )
    assert "RenamedCategoryType" not in text
    # Python class name still resolves (back-compat for call sites / muscle memory).
    out_cls = StringIO()
    call_command("inspect_django_type", "RenamedCategoryType", stdout=out_cls)
    assert out_cls.getvalue().splitlines()[0].startswith("Category  (model:")


def test_bare_name_meta_name_collision_with_python_name_is_ambiguous():
    """``Meta.name`` of one type colliding with another's ``__name__`` is ambiguous."""

    class CategoryView(DjangoType):
        class Meta:
            model = Category
            primary = True
            fields = ("id", "name")
            name = "ItemType"

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    finalize_django_types()
    with pytest.raises(CommandError, match=r"ItemType is ambiguous") as exc_info:
        call_command("inspect_django_type", "ItemType")
    message = str(exc_info.value)
    assert "CategoryView" in message
    assert "ItemType" in message
    assert "fully-dotted object paths" in message


def test_scalar_name_uses_custom_scalar_definition_name():
    """A custom scalar wrapper reports its explicit SDL name, never its object repr."""

    class TokenValue:
        pass

    with pytest.warns(DeprecationWarning):
        token = strawberry.scalar(TokenValue, name="OpaqueToken", serialize=str)

    assert _scalar_name(token) == "OpaqueToken"


def test_scalar_name_uses_named_union_metadata():
    """A finalized named union leaf reports its SDL name, never its object repr."""

    assert _scalar_name(strawberry.union("SearchResult")) == "SearchResult"


def test_scalar_name_falls_back_to_dunder_name_for_definitionless_type():
    """A mapless leaf with no Strawberry definition falls back to ``__name__``."""

    class UnmappedCustomScalar:
        pass

    assert _scalar_name(UnmappedCustomScalar) == "UnmappedCustomScalar"
