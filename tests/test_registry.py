"""Pure-unit tests for ``django_strawberry_framework.registry.TypeRegistry``.

The integration-flavored registry tests (collision raised by ``DjangoType``
subclassing, enum-caching observed through ``convert_choices_to_enum``)
live alongside their consumers in ``tests/types/test_base.py`` and
``tests/types/test_converters.py``. This module covers the registry's
public contract directly without the ``DjangoType`` wrapper, so the
class can be reasoned about in isolation and so each public method has a
dedicated test that exercises every branch.
"""

from enum import Enum

import pytest
from django.db import models
from fakeshop.products.models import Category, Item

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import TypeRegistry, registry


@pytest.fixture
def fresh_registry() -> TypeRegistry:
    """Return a fresh registry instance per test (the global one is shared)."""
    return TypeRegistry()


@pytest.fixture(autouse=True)
def _isolate_global_registry():
    """Clear the global registry on entry/exit so tests touching it don't leak."""
    registry.clear()
    yield
    registry.clear()


def test_register_and_get_round_trips(fresh_registry):
    """``register(model, type_cls)`` makes ``get(model)`` return ``type_cls``."""

    class CategoryType:
        pass

    fresh_registry.register(Category, CategoryType)
    assert fresh_registry.get(Category) is CategoryType


def test_get_returns_none_for_unregistered_model(fresh_registry):
    """``get`` returns ``None`` rather than raising when the model is unknown."""
    assert fresh_registry.get(Category) is None


def test_register_collision_raises(fresh_registry):
    """Registering twice for the same model raises ``ConfigurationError``."""

    class CategoryTypeA:
        pass

    class CategoryTypeB:
        pass

    fresh_registry.register(Category, CategoryTypeA)
    with pytest.raises(ConfigurationError, match="already registered"):
        fresh_registry.register(Category, CategoryTypeB)


def test_model_for_type_returns_none_for_none(fresh_registry):
    """Passing ``None`` short-circuits to ``None`` so the optimizer can pipeline.

    ``DjangoOptimizerExtension`` chains ``unwrap_return_type`` ->
    ``model_for_type`` and the unwrap can yield ``None`` for opaque
    wrapper types; the registry must accept that without raising.
    """
    assert fresh_registry.model_for_type(None) is None


def test_model_for_type_returns_none_for_unregistered_class(fresh_registry):
    """An unregistered class also returns ``None`` (no exception)."""

    class NotRegistered:
        pass

    assert fresh_registry.model_for_type(NotRegistered) is None


def test_model_for_type_round_trips(fresh_registry):
    """``model_for_type`` reverses ``register``: ``type_cls`` -> ``model``."""

    class CategoryType:
        pass

    fresh_registry.register(Category, CategoryType)
    assert fresh_registry.model_for_type(CategoryType) is Category


def test_register_enum_caches_by_model_field(fresh_registry):
    """``register_enum`` keys on ``(model, field_name)`` and ``get_enum`` retrieves it."""

    class Status(Enum):
        ACTIVE = "active"

    fresh_registry.register_enum(Category, "status", Status)
    assert fresh_registry.get_enum(Category, "status") is Status
    # Distinct ``(model, field_name)`` keys do not collide.
    assert fresh_registry.get_enum(Category, "other_field") is None
    assert fresh_registry.get_enum(Item, "status") is None


def test_clear_drops_all_state(fresh_registry):
    """``clear()`` empties type, model, and enum maps in one call."""

    class CategoryType:
        pass

    class Status(Enum):
        ACTIVE = "active"

    fresh_registry.register(Category, CategoryType)
    fresh_registry.register_enum(Category, "status", Status)
    assert fresh_registry.get(Category) is CategoryType
    assert fresh_registry.get_enum(Category, "status") is Status

    fresh_registry.clear()

    assert fresh_registry.get(Category) is None
    assert fresh_registry.model_for_type(CategoryType) is None
    assert fresh_registry.get_enum(Category, "status") is None


def test_global_registry_is_a_type_registry_instance():
    """The ``registry`` module-level singleton is a ``TypeRegistry``."""
    assert isinstance(registry, TypeRegistry)
    # Sanity: still bound to the Django models module (smoke check that
    # the type signature didn't drift to a different shape).
    assert isinstance(Category, type) and issubclass(Category, models.Model)
