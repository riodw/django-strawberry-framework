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
import strawberry
from apps.products.models import Category, Item, Property
from django.db import models
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import TypeRegistry, registry
from django_strawberry_framework.types import finalizer as finalizer_module
from django_strawberry_framework.types.relations import PendingRelation, PendingRelationAnnotation
from django_strawberry_framework.utils.relations import relation_kind


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

    ``DjangoOptimizerExtension`` resolves GraphQL return types with
    ``unwrap_graphql_type`` and then calls ``model_for_type``; the registry
    must accept a missing origin without raising.
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
    with pytest.raises(
        ConfigurationError,
        match="Category.status is already registered as StatusA",
    ):
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


def test_register_definition_rejects_different_definition_for_same_type(fresh_registry):
    """A type class cannot be rebound to a different collected definition."""

    class CategoryType:
        pass

    original_definition = object()
    fresh_registry.register_definition(CategoryType, original_definition)
    fresh_registry.register_definition(CategoryType, original_definition)

    with pytest.raises(
        ConfigurationError,
        match="CategoryType already has a registered DjangoTypeDefinition",
    ):
        fresh_registry.register_definition(CategoryType, object())

    assert fresh_registry.get_definition(CategoryType) is original_definition


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


def test_finalize_discards_consumer_authored_pending_relation_without_rewriting_annotation():
    """Consumer-authored relation annotations are not rewritten if a stale pending record exists."""

    try:

        class ManualPendingCategoryType(DjangoType):
            items: list["ManualPendingItemType"]

            class Meta:
                model = Category
                fields = ("id", "name", "items")

        definition = registry.get_definition(ManualPendingCategoryType)
        assert definition is not None
        assert definition.consumer_authored_fields == frozenset({"items"})

        field = Category._meta.get_field("items")
        kind = relation_kind(field)
        registry.add_pending_relation(
            PendingRelation(
                source_type=ManualPendingCategoryType,
                source_model=Category,
                field_name="items",
                django_field=field,
                related_model=Item,
                relation_kind=kind,
                # Many-side cardinalities (reverse FK / M2M) force ``False``;
                # matches the cardinality-gated rule in
                # ``FieldMeta.from_django_field`` and ``_record_pending_relation``.
                nullable=(
                    False
                    if kind in ("many", "reverse_many_to_one")
                    else kind == "reverse_one_to_one" or bool(getattr(field, "null", False))
                ),
            ),
        )

        class ManualPendingItemType(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name")

        globals()["ManualPendingItemType"] = ManualPendingItemType

        finalize_django_types()

        annotation = ManualPendingCategoryType.__annotations__["items"]
        assert getattr(annotation, "__args__", ()) == ("ManualPendingItemType",)
        assert list(registry.iter_pending_relations()) == []
    finally:
        globals().pop("ManualPendingItemType", None)


def test_finalize_skips_definitions_marked_finalized_when_registry_is_unfinalized(monkeypatch):
    """Definition-level finalized flags prevent duplicate resolver and Strawberry mutation."""
    attach_calls = []
    type_calls = []

    def counting_attach(*args, **kwargs):
        attach_calls.append((args, kwargs))

    def counting_type(type_cls, **kwargs):
        type_calls.append((type_cls, kwargs))

    monkeypatch.setattr(finalizer_module, "_attach_relation_resolvers", counting_attach)
    monkeypatch.setattr(finalizer_module.strawberry, "type", counting_type)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    definition = registry.get_definition(CategoryType)
    assert definition is not None
    definition.finalized = True

    finalize_django_types()

    assert attach_calls == []
    assert type_calls == []
    assert registry.is_finalized() is True


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


def test_registry_clear_allows_fresh_relay_declared_type_to_finalize():
    """``registry.clear()`` lets a fresh Relay-declared ``DjangoType`` finalize cleanly.

    Pins the lifecycle contract that the same model can be re-bound to a
    fresh Relay-declared type after the previous one was dropped via
    ``clear()``. The fresh class must end up with ``relay.Node`` in its
    MRO plus the four ``resolve_*`` classmethods injected.
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryNode]:
            return []

    finalize_django_types()
    strawberry.Schema(query=Query)
    registry.clear()

    class FreshCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query2:
        @strawberry.field
        def all_categories(self) -> list[FreshCategoryNode]:
            return []

    finalize_django_types()
    strawberry.Schema(query=Query2)
    assert registry.is_finalized() is True
    assert registry.get(Category) is FreshCategoryNode
    assert relay.Node in FreshCategoryNode.__mro__
    for attr in (
        "resolve_id",
        "resolve_id_attr",
        "resolve_node",
        "resolve_nodes",
    ):
        assert attr in FreshCategoryNode.__dict__


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
            fields = (
                "id",
                "name",
                "items",
                "properties",
            )

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


def test_discard_pending_uses_identity_match_with_real_pending_relation(fresh_registry):
    """``discard_pending`` removes the exact records handed back by the caller.

    Pins the identity-based contract so this module does not couple to
    ``PendingRelation``'s ``__eq__``/``__hash__`` semantics.  Builds two
    equal-by-value records and asserts that discarding one leaves the
    other in place.
    """
    field = Category._meta.get_field("items")
    kind = relation_kind(field)
    source_type = type("SharedSource", (), {})
    common_kwargs = {
        "source_type": source_type,
        "source_model": Category,
        "field_name": "items",
        "django_field": field,
        "related_model": Item,
        "relation_kind": kind,
        "nullable": False,
    }
    record_a = PendingRelation(**common_kwargs)
    record_b = PendingRelation(**common_kwargs)
    # Sanity-check: distinct objects, equal by dataclass value. This is
    # the shape that would let an equality-based ``discard_pending`` drop
    # both — the identity contract drops only the exact instance passed.
    assert record_a is not record_b
    assert record_a == record_b
    fresh_registry.add_pending_relation(record_a)
    fresh_registry.add_pending_relation(record_b)
    fresh_registry.discard_pending([record_a])
    remaining = list(fresh_registry.iter_pending_relations())
    assert len(remaining) == 1
    assert remaining[0] is record_b


def test_discard_pending_tolerates_non_hashable_django_field(fresh_registry):
    """``discard_pending`` removes pending records by identity without hashing them."""

    class _NonHashableField:
        __hash__ = None  # type: ignore[assignment]

    pending = PendingRelation(
        source_type=type("Src", (), {}),
        source_model=Category,
        field_name="items",
        django_field=_NonHashableField(),  # type: ignore[arg-type]
        related_model=Item,
        relation_kind="reverse_many_to_one",
        nullable=False,
    )

    fresh_registry.add_pending_relation(pending)
    fresh_registry.discard_pending([pending])

    assert list(fresh_registry.iter_pending_relations()) == []


def test_mutators_reject_calls_after_mark_finalized(fresh_registry):
    """After ``mark_finalized``, every mutator raises ``ConfigurationError``.

    Defense-in-depth: ``DjangoType.__init_subclass__`` already rejects
    new subclasses post-finalization, but the registry boundary itself
    must also fail loud so out-of-band mutators (late imports, manual
    test harnesses) cannot silently corrupt the finalized snapshot.
    """

    class CategoryType:
        pass

    class Status(Enum):
        ACTIVE = "active"

    fresh_registry.mark_finalized()
    field = Category._meta.get_field("items")
    pending = PendingRelation(
        source_type=CategoryType,
        source_model=Category,
        field_name="items",
        django_field=field,
        related_model=Item,
        relation_kind=relation_kind(field),
        nullable=False,
    )

    with pytest.raises(ConfigurationError, match="finalized"):
        fresh_registry.register(Category, CategoryType)
    with pytest.raises(ConfigurationError, match="finalized"):
        fresh_registry.register_definition(CategoryType, object())
    with pytest.raises(ConfigurationError, match="finalized"):
        fresh_registry.add_pending_relation(pending)
    with pytest.raises(ConfigurationError, match="finalized"):
        fresh_registry.discard_pending([pending])
    with pytest.raises(ConfigurationError, match="finalized"):
        fresh_registry.register_enum(Category, "status", Status)


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


def test_register_with_definition_rolls_back_register_on_definition_failure(fresh_registry):
    """``register_with_definition`` is atomic across the pair.

    If ``register_definition`` raises after ``register`` succeeded, the
    model->type mapping must not persist. Otherwise a subsequent attempt
    to register the type would surface "already registered" instead of
    the real underlying failure.
    """

    class CategoryType:
        pass

    sentinel = object()
    fresh_registry.register_definition(CategoryType, sentinel)

    with pytest.raises(ConfigurationError, match="already has a registered DjangoTypeDefinition"):
        fresh_registry.register_with_definition(Category, CategoryType, object())

    assert fresh_registry.get(Category) is None
    assert fresh_registry.model_for_type(CategoryType) is None
    # The pre-existing definition pin survives the rollback.
    assert fresh_registry.get_definition(CategoryType) is sentinel

    # Re-registration after the rollback now sees a clean slate for the model.
    fresh_registry.register_with_definition(Category, CategoryType, sentinel)
    assert fresh_registry.get(Category) is CategoryType


# ---------------------------------------------------------------------------
# Slice 1 (spec-018-meta_primary-0_0_6.md) — multi-type storage + primary
# tracking. Tests below exercise the new contract through ``register`` /
# ``register_with_definition`` directly with plain test classes (no
# ``DjangoType`` subclasses) per spec slice-1 paragraph at ``spec:656``.
# ---------------------------------------------------------------------------


def test_register_two_types_same_model_without_primary_allows_both_in_types_for(fresh_registry):
    """Two types for one model without ``primary`` co-exist; both appear in ``types_for``."""

    class ItemTypeA:
        pass

    class ItemTypeB:
        pass

    fresh_registry.register(Item, ItemTypeA)
    fresh_registry.register(Item, ItemTypeB)
    assert fresh_registry.types_for(Item) == (ItemTypeA, ItemTypeB)
    assert fresh_registry.primary_for(Item) is None


def test_register_second_type_for_same_model_no_longer_raises_collision(fresh_registry):
    """Second type for an existing model no longer raises (collision path retired)."""

    class ItemTypeA:
        pass

    class ItemTypeB:
        pass

    fresh_registry.register(Item, ItemTypeA)
    try:
        fresh_registry.register(Item, ItemTypeB)
    except ConfigurationError:
        pytest.fail("Slice 1: second registration without primary must not raise")


def test_register_same_type_twice_is_idempotent(fresh_registry):
    """Calling ``register(Model, T)`` twice is a no-op for the second call."""

    class ItemType:
        pass

    fresh_registry.register(Item, ItemType)
    second = fresh_registry.register(Item, ItemType)
    assert second is False
    assert fresh_registry.types_for(Item) == (ItemType,)


def test_register_primary_flag_sets_primary_for(fresh_registry):
    """``primary=True`` populates ``_primaries`` and ``primary_for`` reads it back."""

    class ItemType:
        pass

    fresh_registry.register(Item, ItemType, primary=True)
    assert fresh_registry.primary_for(Item) is ItemType
    assert fresh_registry.get(Item) is ItemType
    assert fresh_registry.types_for(Item) == (ItemType,)


def test_register_two_primaries_for_same_model_raises_configuration_error(fresh_registry):
    """Second ``primary=True`` on the same model raises naming attempt, model, and incumbent primary.

    Pins all three load-bearing identifiers in the error message so a future
    cosmetic refactor can't silently drop the attempt name (``AdminItemType``),
    the model name (``Item``), or the incumbent primary (``ItemType``) — the
    grep-from-a-stack-trace triage path needs each one.
    """

    class ItemType:
        pass

    class AdminItemType:
        pass

    fresh_registry.register(Item, ItemType, primary=True)
    with pytest.raises(
        ConfigurationError,
        match=r"Cannot register AdminItemType as primary for Item;.*ItemType is already the primary type",
    ):
        fresh_registry.register(Item, AdminItemType, primary=True)
    # The duplicate-primary attempt did not append AdminItemType.
    assert fresh_registry.types_for(Item) == (ItemType,)
    assert fresh_registry.primary_for(Item) is ItemType


def test_register_same_type_re_register_with_flipped_primary_false_raises(fresh_registry):
    """Flip of stored ``primary=True`` to ``primary=False`` raises (M1 regression)."""

    class ItemType:
        pass

    fresh_registry.register(Item, ItemType, primary=True)
    with pytest.raises(ConfigurationError, match="primary flag cannot be flipped"):
        fresh_registry.register(Item, ItemType, primary=False)


def test_register_same_type_re_register_with_flipped_primary_true_raises(fresh_registry):
    """Flip of stored ``primary=False`` to ``primary=True`` raises (symmetric guard)."""

    class ItemType:
        pass

    fresh_registry.register(Item, ItemType)
    with pytest.raises(ConfigurationError, match="primary flag cannot be flipped"):
        fresh_registry.register(Item, ItemType, primary=True)


def test_register_with_definition_rollback_clears_primary(fresh_registry):
    """``register_with_definition`` rolls back ``_primaries`` for state it added."""

    class ItemType:
        pass

    # Pre-poison ``register_definition`` for ItemType so the second
    # ``register_with_definition`` call raises after ``register`` succeeded.
    sentinel = object()
    fresh_registry.register_definition(ItemType, sentinel)

    with pytest.raises(ConfigurationError, match="already has a registered DjangoTypeDefinition"):
        fresh_registry.register_with_definition(Item, ItemType, object(), primary=True)

    assert fresh_registry.types_for(Item) == ()
    assert fresh_registry.model_for_type(ItemType) is None
    assert fresh_registry.primary_for(Item) is None
    # Pre-existing definition pin survives.
    assert fresh_registry.get_definition(ItemType) is sentinel


def test_register_with_definition_rollback_restores_pre_existing_primary(fresh_registry):
    """Rollback restores ``_primaries[model]`` to the pre-existing primary.

    Pins the ``else: self._primaries[model] = pre_primary`` branch of the
    rollback in ``register_with_definition``: when a model already has a
    primary set and a NEW non-primary type's ``register()`` succeeds, then
    ``register_definition`` raises, the rollback must restore the
    pre-existing primary rather than popping it.
    """

    class ItemType:
        pass

    class AdminItemType:
        pass

    # Set up a pre-existing primary on Item.
    fresh_registry.register_with_definition(Item, ItemType, object(), primary=True)
    assert fresh_registry.primary_for(Item) is ItemType

    # Pre-poison the definition for AdminItemType so register_definition raises
    # AFTER register() succeeds (appended=True for the new non-primary type).
    sentinel = object()
    fresh_registry.register_definition(AdminItemType, sentinel)

    with pytest.raises(ConfigurationError, match="already has a registered DjangoTypeDefinition"):
        fresh_registry.register_with_definition(Item, AdminItemType, object())

    # AdminItemType was rolled back from ``_types`` and ``_models``.
    assert fresh_registry.types_for(Item) == (ItemType,)
    assert fresh_registry.model_for_type(AdminItemType) is None
    # ``_primaries[Item]`` is still ``ItemType`` — the else-branch restore ran.
    assert fresh_registry.primary_for(Item) is ItemType


def test_register_with_definition_idempotent_re_register_does_not_corrupt_state(fresh_registry):
    """A re-register-with-different-definition failure leaves pre-existing state intact."""

    class ItemType:
        pass

    def1 = object()
    def2 = object()
    assert def2 is not def1

    fresh_registry.register_with_definition(Item, ItemType, def1)

    with pytest.raises(ConfigurationError, match="already has a registered DjangoTypeDefinition"):
        fresh_registry.register_with_definition(Item, ItemType, def2)

    assert fresh_registry.types_for(Item) == (ItemType,)
    assert fresh_registry.model_for_type(ItemType) is Item
    assert fresh_registry.get_definition(ItemType) is def1
    assert fresh_registry.primary_for(Item) is None


def test_register_with_definition_idempotent_re_register_preserves_primary(fresh_registry):
    """Primary-preservation corollary: the pre-existing primary survives a re-register failure."""

    class ItemType:
        pass

    def1 = object()
    def2 = object()
    fresh_registry.register_with_definition(Item, ItemType, def1, primary=True)
    assert fresh_registry.primary_for(Item) is ItemType

    with pytest.raises(ConfigurationError, match="already has a registered DjangoTypeDefinition"):
        fresh_registry.register_with_definition(Item, ItemType, def2, primary=True)

    assert fresh_registry.primary_for(Item) is ItemType
    assert fresh_registry.types_for(Item) == (ItemType,)


def test_register_returns_true_for_new_state(fresh_registry):
    """First registration returns ``True`` (state was added)."""

    class ItemType:
        pass

    assert fresh_registry.register(Item, ItemType) is True


def test_register_returns_false_for_idempotent_re_register(fresh_registry):
    """Idempotent re-register returns ``False`` (no state added)."""

    class ItemType:
        pass

    fresh_registry.register(Item, ItemType)
    assert fresh_registry.register(Item, ItemType) is False


def test_get_returns_single_type_when_one_registered_no_primary(fresh_registry):
    """``get(Model)`` returns the lone type even when ``primary`` is not declared."""

    class ItemType:
        pass

    fresh_registry.register(Item, ItemType)
    assert fresh_registry.get(Item) is ItemType


def test_get_returns_primary_when_multiple_and_primary_declared(fresh_registry):
    """``get(Model)`` returns the explicit primary when multiple types are registered."""

    class ItemType:
        pass

    class AdminItemType:
        pass

    fresh_registry.register(Item, ItemType, primary=True)
    fresh_registry.register(Item, AdminItemType)
    assert fresh_registry.get(Item) is ItemType


def test_get_returns_none_when_multiple_and_no_primary(fresh_registry):
    """``get(Model)`` returns ``None`` when multi-type and no primary declared."""

    class ItemType:
        pass

    class AdminItemType:
        pass

    fresh_registry.register(Item, ItemType)
    fresh_registry.register(Item, AdminItemType)
    assert fresh_registry.get(Item) is None
    # Distinguishing path: types_for still surfaces the registered pair.
    assert fresh_registry.types_for(Item) == (ItemType, AdminItemType)


def test_primary_for_returns_none_when_only_implicit_single_type(fresh_registry):
    """``primary_for`` is strictly ``_primaries``; the single-type convenience lives on ``get``."""

    class ItemType:
        pass

    fresh_registry.register(Item, ItemType)
    assert fresh_registry.primary_for(Item) is None
    assert fresh_registry.get(Item) is ItemType


def test_types_for_preserves_registration_order(fresh_registry):
    """``types_for`` returns registrations in the order they happened."""

    class A:
        pass

    class B:
        pass

    class C:
        pass

    fresh_registry.register(Item, A)
    fresh_registry.register(Item, B)
    fresh_registry.register(Item, C)
    assert fresh_registry.types_for(Item) == (A, B, C)


def test_iter_types_yields_each_type_once_when_multiple_registered_for_same_model(fresh_registry):
    """``iter_types`` yields one pair per registered type; multi-type models appear repeatedly."""

    class A:
        pass

    class B:
        pass

    fresh_registry.register(Item, A, primary=True)
    fresh_registry.register(Item, B)
    pairs = list(fresh_registry.iter_types())
    assert pairs == [(Item, A), (Item, B)]


def test_register_same_type_against_two_models_still_raises(fresh_registry):
    """Reverse-collision contract is preserved after the Slice 1 rewrite (spec:108)."""

    class SharedType:
        pass

    fresh_registry.register(Category, SharedType)
    with pytest.raises(ConfigurationError, match="already registered against Category"):
        fresh_registry.register(Item, SharedType)


def test_clear_resets_primaries(fresh_registry):
    """``clear()`` wipes ``_primaries`` alongside the other registry maps."""

    class ItemType:
        pass

    fresh_registry.register(Item, ItemType, primary=True)
    fresh_registry.clear()
    assert fresh_registry.primary_for(Item) is None
    assert fresh_registry.types_for(Item) == ()


def test_models_with_multiple_types_yields_only_models_with_two_or_more(fresh_registry):
    """``models_with_multiple_types`` reports only models with ``>= 2`` registered types."""

    class CategoryType:
        pass

    class ItemTypeA:
        pass

    class ItemTypeB:
        pass

    class PropertyTypeA:
        pass

    class PropertyTypeB:
        pass

    class PropertyTypeC:
        pass

    fresh_registry.register(Category, CategoryType)
    fresh_registry.register(Item, ItemTypeA)
    fresh_registry.register(Item, ItemTypeB)
    fresh_registry.register(Property, PropertyTypeA)
    fresh_registry.register(Property, PropertyTypeB)
    fresh_registry.register(Property, PropertyTypeC)
    multi = sorted(fresh_registry.models_with_multiple_types(), key=lambda m: m.__name__)
    assert multi == [Item, Property]


# ---------------------------------------------------------------------------
# Slice 3 (spec-018-meta_primary-0_0_6.md) — finalize-time ambiguity audit.
# Tests below cover ``_audit_primary_ambiguity()`` running inside
# ``finalize_django_types()``. The audit-success and audit-vs-unresolved
# tests live in ``tests/types/test_definition_order.py``; this file hosts
# the raise-at-finalize and once-per-build regression coverage.
# ---------------------------------------------------------------------------


def test_finalize_raises_when_model_has_multiple_types_no_primary():
    """``finalize_django_types`` raises when a model has 2+ types and no primary."""

    class ItemTypeA(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class ItemTypeB(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "Models with multiple registered DjangoType subclasses and no primary" in msg
    assert "Item" in msg
    assert "ItemTypeA" in msg
    assert "ItemTypeB" in msg


def test_finalize_ambiguity_error_message_contains_actionable_fix():
    """The ambiguity error message ends with the actionable ``Declare Meta.primary`` sentence."""

    class ItemTypeA(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class ItemTypeB(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    assert (
        "Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."
    ) in str(
        exc_info.value,
    )


def test_audit_runs_once_per_build(monkeypatch):
    """The ambiguity audit runs exactly once per finalize-cycle build (M1 regression).

    Pins that ``_audit_primary_ambiguity`` sits *below* the
    ``registry.is_finalized()`` short-circuit in ``finalize_django_types``;
    a second ``finalize_django_types()`` call must short-circuit without
    re-auditing.
    """
    calls = []
    original = registry.models_with_multiple_types

    def spy():
        calls.append(None)
        return original()

    monkeypatch.setattr(registry, "models_with_multiple_types", spy)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()
    finalize_django_types()  # second call must hit the is_finalized() guard

    assert len(calls) == 1


# ---------------------------------------------------------------------------
# L1 (docs/plan-registry-helpers.md) — unregister public helper. Tests below
# exercise the new public surface that replaces the direct private-map
# pokes in Slice 4 walker/extension fixtures and the older
# check_schema-audit fixtures (types list, model index, primary slot, and
# definition map).
# ---------------------------------------------------------------------------


def test_unregister_removes_from_types_models_primaries_definitions(fresh_registry):
    """``unregister`` drops the type from every registry map."""

    class ItemType:
        pass

    sentinel = object()
    fresh_registry.register(Item, ItemType, primary=True)
    fresh_registry.register_definition(ItemType, sentinel)

    fresh_registry.unregister(ItemType)

    assert fresh_registry.types_for(Item) == ()
    assert fresh_registry.model_for_type(ItemType) is None
    assert fresh_registry.primary_for(Item) is None
    assert fresh_registry.get_definition(ItemType) is None


def test_unregister_removes_pending_relations_sourced_from_type(fresh_registry):
    """``unregister`` discards pending relations whose ``source_type`` matches."""

    class CategoryType:
        pass

    class ItemType:
        pass

    fresh_registry.register(Category, CategoryType)
    fresh_registry.register(Item, ItemType)
    field = Category._meta.get_field("items")
    kind = relation_kind(field)
    pending_keep = PendingRelation(
        source_type=CategoryType,
        source_model=Category,
        field_name="items",
        django_field=field,
        related_model=Item,
        relation_kind=kind,
        nullable=False,
    )
    pending_drop = PendingRelation(
        source_type=ItemType,
        source_model=Item,
        field_name="category",
        django_field=Item._meta.get_field("category"),
        related_model=Category,
        relation_kind=relation_kind(Item._meta.get_field("category")),
        nullable=False,
    )
    fresh_registry.add_pending_relation(pending_keep)
    fresh_registry.add_pending_relation(pending_drop)

    fresh_registry.unregister(ItemType)

    remaining = list(fresh_registry.iter_pending_relations())
    assert remaining == [pending_keep]


def test_unregister_keeps_siblings_intact_in_multi_type_case(fresh_registry):
    """``unregister`` of one type for a model leaves siblings registered.

    When the unregistered type was the primary, the model loses its
    primary slot — the caller is responsible for re-declaring a primary
    via a fresh registration cycle. Siblings stay in ``types_for`` in
    their original registration order.
    """

    class ItemTypeA:
        pass

    class ItemTypeB:
        pass

    class ItemTypeC:
        pass

    fresh_registry.register(Item, ItemTypeA, primary=True)
    fresh_registry.register(Item, ItemTypeB)
    fresh_registry.register(Item, ItemTypeC)

    fresh_registry.unregister(ItemTypeA)

    assert fresh_registry.types_for(Item) == (ItemTypeB, ItemTypeC)
    assert fresh_registry.primary_for(Item) is None
    assert fresh_registry.model_for_type(ItemTypeB) is Item
    assert fresh_registry.model_for_type(ItemTypeC) is Item


def test_unregister_of_primary_leaves_state_that_audit_rejects():
    """``unregister(primary_for_multi)`` leaves a state the finalize audit refuses.

    Pins the contract narrated by ``unregister``'s docstring at
    ``django_strawberry_framework/registry.py::TypeRegistry.unregister #"When ``type_cls`` is the primary for its model"``: when ``type_cls`` is the primary for its
    model, the model loses its primary even if siblings remain — the
    caller must re-declare a primary via a fresh registration cycle.
    Concretely: register three types against the same model with the
    first as primary, unregister the primary, then call
    ``finalize_django_types()`` and confirm it raises the canonical
    ambiguity error. Prevents a future maintainer from "helpfully"
    auto-promoting the next sibling to primary on unregister, which
    would silently change the relation-resolution target.
    """

    class ItemTypeA(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class ItemTypeB(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class ItemTypeC(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.primary_for(Item) is ItemTypeA
    assert registry.types_for(Item) == (ItemTypeA, ItemTypeB, ItemTypeC)

    registry.unregister(ItemTypeA)

    assert registry.primary_for(Item) is None
    assert registry.types_for(Item) == (ItemTypeB, ItemTypeC)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "Models with multiple registered DjangoType subclasses and no primary" in msg
    assert "Item" in msg
    assert "ItemTypeB" in msg
    assert "ItemTypeC" in msg
    assert (
        "Declare Meta.primary = True on exactly one of the registered DjangoType subclasses." in msg
    )


def test_unregister_is_noop_on_unknown_type(fresh_registry):
    """``unregister`` returns silently when ``type_cls`` was never registered."""

    class NotRegistered:
        pass

    fresh_registry.unregister(NotRegistered)  # no raise

    assert fresh_registry.types_for(Item) == ()


def test_unregister_raises_after_finalize():
    """``unregister`` honours ``_check_mutable``: post-finalize calls raise.

    The finalized registry is the runtime lookup source for optimizer
    planning, the schema audit, and relation-target resolution. Removing
    entries after ``finalize_django_types()`` would silently disable
    planning for types still present in the built Strawberry schema, so
    the public mutator refuses to corrupt the snapshot.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()
    with pytest.raises(ConfigurationError, match="finalized"):
        registry.unregister(CategoryType)


def test_clear_tolerates_unimportable_filter_submodules(fresh_registry):
    """Both ``except ImportError`` guards in ``clear()`` are best-effort.

    The filter-namespace co-clear uses cycle-safe local imports. If either
    submodule cannot be imported (forced here by poisoning ``sys.modules``),
    ``clear()`` skips that block and still clears the registry's own state
    rather than raising.
    """
    import sys

    inputs_name = "django_strawberry_framework.filters.inputs"
    filters_name = "django_strawberry_framework.filters"
    saved = {name: sys.modules.get(name) for name in (inputs_name, filters_name)}

    class CategoryType:
        pass

    try:
        # ``None`` in ``sys.modules`` makes ``from <name> import ...`` raise
        # ImportError, exercising both guards.
        sys.modules[inputs_name] = None
        sys.modules[filters_name] = None
        fresh_registry.register(Category, CategoryType)
        # Must not raise even though neither submodule can be imported.
        fresh_registry.clear()
        assert fresh_registry.get(Category) is None
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def test_clear_tolerates_unimportable_order_submodules(fresh_registry):
    """Both order-side ``except ImportError`` guards in ``clear()`` are best-effort.

    Order twin of ``test_clear_tolerates_unimportable_filter_submodules``. The
    order-namespace co-clear (``clear_order_input_namespace`` +
    ``_helper_referenced_ordersets.clear()``) uses cycle-safe local imports per
    spec-028 Decision 9. If either order submodule cannot be imported (forced
    here by poisoning ``sys.modules``), ``clear()`` skips that block and still
    clears the registry's own state rather than raising.
    """
    import sys

    inputs_name = "django_strawberry_framework.orders.inputs"
    orders_name = "django_strawberry_framework.orders"
    saved = {name: sys.modules.get(name) for name in (inputs_name, orders_name)}

    class CategoryType:
        pass

    try:
        # ``None`` in ``sys.modules`` makes ``from <name> import ...`` raise
        # ImportError, exercising both order-side guards.
        sys.modules[inputs_name] = None
        sys.modules[orders_name] = None
        fresh_registry.register(Category, CategoryType)
        # Must not raise even though neither order submodule can be imported.
        fresh_registry.clear()
        assert fresh_registry.get(Category) is None
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
