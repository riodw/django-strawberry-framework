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
from products.models import Category, Item, Property

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import TypeRegistry, registry
from django_strawberry_framework.types import finalizer as finalizer_module
from django_strawberry_framework.types.relations import PendingRelationAnnotation


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


def test_register_same_class_against_two_models_raises(fresh_registry):
    """Registering the same ``type_cls`` against two models raises ``ConfigurationError``.

    Pins the reverse-direction guard: ``_models[type_cls]`` must not be
    silently overwritten when the same class is reused for a different
    model, because that would leave ``model_for_type`` returning the
    wrong model for the original registration.
    """

    class SharedType:
        pass

    fresh_registry.register(Category, SharedType)
    with pytest.raises(ConfigurationError, match="already registered against Category"):
        fresh_registry.register(Item, SharedType)
    # Original mapping is preserved.
    assert fresh_registry.model_for_type(SharedType) is Category


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


def test_register_enum_same_class_is_idempotent(fresh_registry):
    """Re-registering the *same* enum class for the same key is a no-op.

    Pins the convert_choices_to_enum cache pattern: the call site reads
    ``get_enum`` first, so a redundant ``register_enum`` with the same
    class must not raise.
    """

    class Status(Enum):
        ACTIVE = "active"

    fresh_registry.register_enum(Category, "status", Status)
    fresh_registry.register_enum(Category, "status", Status)
    assert fresh_registry.get_enum(Category, "status") is Status


def test_register_enum_different_class_for_same_key_raises(fresh_registry):
    """Registering a *different* enum class for an existing key raises."""

    class StatusA(Enum):
        ACTIVE = "active"

    class StatusB(Enum):
        ACTIVE = "active"

    fresh_registry.register_enum(Category, "status", StatusA)
    with pytest.raises(ConfigurationError, match="Category.status is already registered as StatusA"):
        fresh_registry.register_enum(Category, "status", StatusB)
    # Original cache is preserved.
    assert fresh_registry.get_enum(Category, "status") is StatusA


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


def test_iter_types_yields_registered_pairs(fresh_registry):
    """``iter_types()`` yields ``(model, type_cls)`` for each registration."""

    class CategoryType:
        pass

    class ItemType:
        pass

    fresh_registry.register(Category, CategoryType)
    fresh_registry.register(Item, ItemType)
    result = dict(fresh_registry.iter_types())
    assert result == {Category: CategoryType, Item: ItemType}


def test_iter_types_empty_on_fresh_registry(fresh_registry):
    """``iter_types()`` yields nothing when no types are registered."""
    assert list(fresh_registry.iter_types()) == []


def test_global_registry_is_a_type_registry_instance():
    """The ``registry`` module-level singleton is a ``TypeRegistry``."""
    assert isinstance(registry, TypeRegistry)
    # Sanity: still bound to the Django models module (smoke check that
    # the type signature didn't drift to a different shape).
    assert isinstance(Category, type) and issubclass(Category, models.Model)


def test_finalize_is_idempotent(monkeypatch):
    """Calling finalize twice mutates type classes only once."""
    calls = []
    original_type = finalizer_module.strawberry.type

    def counting_type(type_cls, **kwargs):
        calls.append(type_cls)
        return original_type(type_cls, **kwargs)

    monkeypatch.setattr(finalizer_module.strawberry, "type", counting_type)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()
    finalize_django_types()

    assert calls == [CategoryType]


def test_registering_concrete_type_after_finalization_raises():
    """A finalized registry rejects new concrete DjangoType classes."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()

    with pytest.raises(ConfigurationError, match=r"finalize_django_types\(\) already ran"):

        class ItemType(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name")


def test_registry_clear_allows_fresh_type_classes_to_finalize_again():
    """clear() resets registry state for newly declared type classes."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()
    registry.clear()

    class FreshCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()

    assert registry.is_finalized() is True
    assert registry.get(Category) is FreshCategoryType


def test_phase_1_failure_is_atomic_and_retryable_after_missing_target_registers():
    """Unresolved targets fail before class mutation and can retry after the target appears."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    with pytest.raises(ConfigurationError):
        finalize_django_types()

    definition = registry.get_definition(ItemType)
    assert registry.is_finalized() is False
    assert definition is not None
    assert definition.finalized is False
    assert not hasattr(ItemType, "__strawberry_definition__")
    assert list(registry.iter_pending_relations())

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()

    assert registry.is_finalized() is True
    assert ItemType.__annotations__["category"] is CategoryType
    assert list(registry.iter_pending_relations()) == []


def test_phase_1_failure_does_not_rewrite_any_pending_annotations_when_one_target_is_missing():
    """A mixed pending set stays untouched until every relation target resolves."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items", "properties")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert CategoryType.__annotations__["items"] is PendingRelationAnnotation
    assert CategoryType.__annotations__["properties"] is PendingRelationAnnotation

    with pytest.raises(ConfigurationError, match="Category.properties -> Property"):
        finalize_django_types()

    pending_names = [pending.field_name for pending in registry.iter_pending_relations()]
    category_definition = registry.get_definition(CategoryType)
    item_definition = registry.get_definition(ItemType)
    assert registry.is_finalized() is False
    assert category_definition is not None
    assert item_definition is not None
    assert category_definition.finalized is False
    assert item_definition.finalized is False
    assert not hasattr(CategoryType, "__strawberry_definition__")
    assert not hasattr(ItemType, "__strawberry_definition__")
    assert pending_names == ["items", "properties"]
    assert CategoryType.__annotations__["items"] is PendingRelationAnnotation
    assert CategoryType.__annotations__["properties"] is PendingRelationAnnotation

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")

    finalize_django_types()

    assert registry.is_finalized() is True
    assert CategoryType.__annotations__["items"] == list[ItemType]
    assert CategoryType.__annotations__["properties"] == list[PropertyType]
    assert list(registry.iter_pending_relations()) == []


def test_phase_3_failure_leaves_registry_unfinalized_and_requires_fresh_classes(monkeypatch):
    """A Strawberry-side failure is recovered by clear() plus fresh class recreation."""
    original_type = finalizer_module.strawberry.type

    def failing_type(type_cls, **kwargs):
        type_cls.__partial_strawberry_mutation__ = True
        raise TypeError("simulated Strawberry failure")

    monkeypatch.setattr(finalizer_module.strawberry, "type", failing_type)

    class BrokenCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    with pytest.raises(TypeError):
        finalize_django_types()

    definition = registry.get_definition(BrokenCategoryType)
    assert registry.is_finalized() is False
    assert definition is not None
    assert definition.finalized is False
    assert BrokenCategoryType.__partial_strawberry_mutation__ is True

    registry.clear()
    monkeypatch.setattr(finalizer_module.strawberry, "type", original_type)

    class FreshCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()

    assert registry.get(Category) is FreshCategoryType
    assert registry.is_finalized() is True


def test_pending_set_is_cleaned_after_success_and_retained_after_phase_1_failure():
    """Pending records remain after unresolved failure but disappear after success."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    with pytest.raises(ConfigurationError):
        finalize_django_types()

    assert [pending.field_name for pending in registry.iter_pending_relations()] == ["category"]

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()

    assert ItemType.__annotations__["category"] is CategoryType
    assert list(registry.iter_pending_relations()) == []


def test_clear_does_not_remove_mutation_from_previously_finalized_classes():
    """clear() resets the registry, not already-mutated class objects."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()
    definition = CategoryType.__django_strawberry_definition__
    registry.clear()

    assert registry.is_finalized() is False
    assert hasattr(CategoryType, "__strawberry_definition__")
    assert CategoryType.__django_strawberry_definition__ is definition
