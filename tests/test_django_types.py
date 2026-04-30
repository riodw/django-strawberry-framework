"""Tests for ``DjangoType`` Meta validation, scalar mapping, relations, and registry behaviour."""

import pytest
import strawberry
from fakeshop.products import services
from fakeshop.products.models import Category, Item

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    yield
    registry.clear()


# TODO(slice 1): test_registry_collision_raises_configuration_error
# TODO(slice 1): test_registry_clear_drops_types_and_enums
# TODO(slice 1): test_registry_get_returns_none_for_unregistered_model
# TODO(slice 2): test_meta_required_model_raises_when_missing
# TODO(slice 2): test_meta_fields_and_exclude_mutually_exclusive
# TODO(slice 2): test_scalar_mapping_against_category_textfields_booleanfields_datetimefields
# TODO(slice 2): test_get_queryset_default_returns_input_unchanged
# TODO(slice 3): test_relation_fk_to_target_djangotype
# TODO(slice 3): test_relation_reverse_fk_returns_list
# TODO(slice 3): test_relation_m2m_returns_list
# TODO(slice 3): test_forward_reference_resolves_when_target_defined_later


@pytest.mark.skip(reason="TODO(slice 2): __init_subclass__ Meta validation pending")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "deferred_key",
    [
        "filterset_class",
        "orderset_class",
        "aggregate_class",
        "fields_class",
        "search_fields",
    ],
)
def test_meta_rejects_each_deferred_key(deferred_key):
    """Every key in DEFERRED_META_KEYS must raise ConfigurationError.

    Uses ``type(...)`` so the parametrized key is set dynamically without
    five near-identical test functions. The bare class body would also
    work but parametrization keeps the failure messages clear.
    """
    services.seed_data(1)
    meta_attrs = {"model": Category, "fields": "__all__", deferred_key: object}
    meta_cls = type("Meta", (), meta_attrs)
    with pytest.raises(ConfigurationError, match=deferred_key):
        type("CategoryType", (DjangoType,), {"Meta": meta_cls})


@pytest.mark.skip(reason="TODO(slice 2): __init_subclass__ Meta validation pending")
@pytest.mark.django_db
def test_meta_rejects_filterset_class():
    """Single-key smoke for the parametrized rejection above; kept for readability."""
    services.seed_data(1)
    with pytest.raises(ConfigurationError, match="filterset_class"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = "__all__"
                filterset_class = object


@pytest.mark.skip(reason="TODO(slice 6): optimizer downgrade-to-Prefetch rule pending")
@pytest.mark.django_db
def test_optimizer_downgrades_to_prefetch_when_target_has_custom_get_queryset(
    django_assert_num_queries,
):
    """End-to-end: hidden private items must not leak through a select_related join."""
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return list(Category.objects.all())

    schema = strawberry.Schema(
        query=Query,
        extensions=[DjangoOptimizerExtension()],
    )

    with django_assert_num_queries(2):
        result = schema.execute_sync("{ allCategories { id name items { id name } } }")
        assert result.errors is None
