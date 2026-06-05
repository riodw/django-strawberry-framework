"""Tests for django_strawberry_framework.management.commands.inspect_django_type.

Failure-mode coverage for the ``CommandError`` paths not reachable from a live
registered type, mirroring ``tests/management/test_export_schema.py``'s
``_make_test_module`` + ``monkeypatch.setitem(sys.modules, ...)`` pattern.
"""

import sys
import types

import pytest
from apps.products.models import Category, Item
from django.core.management import CommandError, call_command

from django_strawberry_framework import DjangoType
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
