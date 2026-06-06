"""Tests for django_strawberry_framework.management.commands.inspect_django_type.

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

Finally, holds the consumer-authored-field command tests (assigned scalar,
annotation-only scalar whose type differs from the Django field converter,
annotation-only forced-optional scalar, and annotation-only override of an
*unsupported* Django field type). The fakeshop schema exercises only the
assigned-*relation* corner live (``BranchType.shelves``, pinned in
``examples/fakeshop/tests/test_inspect_django_type.py``); the other three corners
are not present on any fakeshop ``DjangoType``, and the unsupported-field corner
fundamentally needs a synthetic ``models.Field`` subclass with no ``SCALAR_MAP``
ancestor -- so they are earned here against finalize-in-test types, mirroring
``tests/types/test_definition_order.py``'s ``_FakeUnsupportedField`` pattern.
"""

import sys
import types
from io import StringIO

import pytest
import strawberry
from apps.products.models import Category, Item
from django.core.management import CommandError, call_command
from django.db import models

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.management.commands.inspect_django_type import (
    _matched_scalar_key,
    _render_annotation,
)
from django_strawberry_framework.registry import registry


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


def _field_row(text: str, field_name: str) -> str:
    """Return the single rendered table row whose first token is ``field_name``.

    Mirrors ``examples/fakeshop/tests/test_inspect_django_type.py::_field_row`` so
    per-row substring assertions (e.g. ``String`` vs ``String!``, or ``yes`` vs
    ``no``) cannot false-green against another field's row.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.split(" ", 1)[:1] == [field_name]:
            return line
    raise AssertionError(f"no row for field {field_name!r} in:\n{text}")


def test_bad_dotted_path_raises_command_error():
    # The original import error surfaces — it is NOT swallowed and retried as a
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


def test_render_annotation_renders_multi_member_union():
    # A consumer-authored union annotation (>1 non-None member) renders each
    # member name joined by " | " with no trailing "!" on the members.
    assert _render_annotation(int | str) == "Int | String"


def test_inspect_consumer_authored_scalar_fields():
    """The command labels each consumer-authored scalar corner by its true row.

    Three scalar corners on one finalized type:

    - ``name`` is an assigned ``@strawberry.field`` resolver -> the resolved type
      reads from the finalized Strawberry field metadata (``String!``), labelled
      ``consumer strawberry.field (scalar)`` (NOT the ``SCALAR_MAP[TextField]``
      row, which never fired for it).
    - ``description`` is an annotation-only override whose ``int`` differs from
      the Django ``TextField`` converter -> ``Int!`` / ``consumer annotation
      (scalar)`` (NOT ``SCALAR_MAP[TextField]``).
    - ``is_private`` is an annotation-only override forcing the ``NOT NULL``
      ``BooleanField`` optional -> ``Boolean`` (no ``!``), nullable ``yes``,
      ``consumer annotation (scalar)`` (exercises the ``StrawberryOptional`` path).
    """

    class ConsumerScalarOverrideType(DjangoType):
        description: int
        is_private: bool | None

        @strawberry.field
        def name(self) -> str:
            return "overridden"

        class Meta:
            model = Category
            fields = (
                "id",
                "name",
                "description",
                "is_private",
            )

    finalize_django_types()
    out = StringIO()
    call_command("inspect_django_type", "ConsumerScalarOverrideType", stdout=out)
    text = out.getvalue()

    name_row = _field_row(text, "name")
    assert "String!" in name_row
    assert " no " in name_row
    assert "consumer strawberry.field (scalar)" in name_row
    assert "SCALAR_MAP" not in name_row

    description_row = _field_row(text, "description")
    assert "Int!" in description_row
    assert " no " in description_row
    assert "consumer annotation (scalar)" in description_row
    assert "SCALAR_MAP" not in description_row

    is_private_row = _field_row(text, "is_private")
    assert "Boolean" in is_private_row
    assert "Boolean!" not in is_private_row
    assert " yes " in is_private_row
    assert "consumer annotation (scalar)" in is_private_row


def test_inspect_consumer_annotation_over_unsupported_field():
    """An annotation override of an unsupported column renders, never crashing.

    ``myfield`` is a ``models.Field`` subclass with no ``SCALAR_MAP`` ancestor; a
    bare-synthesis type over it raises ``ConfigurationError`` at construction. A
    consumer ``myfield: str`` annotation makes it build, and the command must read
    the consumer type (``String!`` / ``consumer annotation (scalar)``) rather than
    routing through ``_scalar_row`` -> ``_matched_scalar_key`` (whose fallback the
    review flagged as wrongly reachable on a finalized type). Routing
    consumer-authored fields away from the scalar branch keeps that fallback
    unreachable.
    """

    class _UnsupportedField(models.Field):
        pass

    class UnsupportedFieldOwner(models.Model):
        myfield = _UnsupportedField()

        class Meta:
            app_label = "test_inspect_unsupported_field"

    class UnsupportedAnnotationType(DjangoType):
        myfield: str

        class Meta:
            model = UnsupportedFieldOwner
            fields = ("myfield",)

    finalize_django_types()
    out = StringIO()
    call_command("inspect_django_type", "UnsupportedAnnotationType", stdout=out)
    text = out.getvalue()

    myfield_row = _field_row(text, "myfield")
    assert "String!" in myfield_row
    assert "consumer annotation (scalar)" in myfield_row
    assert "SCALAR_MAP" not in myfield_row


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


def test_inspect_consumer_annotation_plus_assigned_field_labels_both():
    """A field that is BOTH annotated and assigned is labelled as the overlap.

    ``name: str = strawberry.field(resolver=...)`` records ``name`` in both the
    annotated set (the ``: str`` fixes the GraphQL type) and the assigned set (the
    ``strawberry.field`` supplies the resolver). The converter column must name
    both rows that contributed -- ``consumer annotation + strawberry.field
    (scalar)`` -- rather than hiding the assignment behind an annotation-only label.
    """

    class BothOverrideType(DjangoType):
        name: str = strawberry.field(resolver=lambda root: "x")

        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()
    out = StringIO()
    call_command("inspect_django_type", "BothOverrideType", stdout=out)

    name_row = _field_row(out.getvalue(), "name")
    assert "String!" in name_row
    assert "consumer annotation + strawberry.field (scalar)" in name_row
