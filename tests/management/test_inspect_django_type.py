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
"""

import sys
import types

import pytest
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
