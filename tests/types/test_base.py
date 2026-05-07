"""Tests for ``DjangoType`` Meta validation, scalar mapping, relations, registry, and ``get_queryset``.

Slice scope:

- Slice 1 — registry behaviour (``register``, ``get``, collision, ``clear``).
- Slice 2 — Meta validation, scalar field synthesis, default ``get_queryset``,
  Strawberry finalization, ``convert_scalar`` direct unit coverage.
- Slice 3 — relation conversion (forward FK, reverse FK, nullable widening,
  unregistered-target rejection); ``_build_annotations`` dispatch on
  ``field.is_relation`` rather than filtering relations out.

.. todo:: spec-foundation 0.0.4 — the "unregistered-target rejection"
   coverage in this file flips from class-creation failure to
   finalization failure. The ``test_relation_unregistered_target_raises``
   case below and the ``@pytest.mark.skip``ed
   ``test_forward_reference_resolves_when_target_defined_later`` are
   the two slated rewrites called out in ``docs/spec-foundation.md``
   "Existing tests that must change". The new acceptance coverage
   moves to ``tests/types/test_definition_order.py`` /
   ``tests/types/test_definition_order_schema.py`` per the spec's
   "Cyclic acceptance tests" / "End-to-end schema tests" sections.

The ``has_custom_get_queryset`` sentinel and override-detection have
shipped and are tested directly. Optimizer downgrade-to-``Prefetch``
coverage belongs in ``tests/optimizer/``; the full forward-reference /
definition-order independence path remains ``@pytest.mark.skip``.

Where Slice 2 tests originally used ``fields = \"__all__\"`` on ``Category``,
they now either declare related types up front (so the registry resolves
``items`` / ``properties``) or use an explicit fields list to keep the
test focused on the behaviour under examination. ``CATEGORY_SCALAR_FIELDS``
captures the scalar-only field list used in those updated tests.
"""

import datetime

import pytest
from django.db import models
from fakeshop.products.models import Category, Entry, Item, Property

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types import converters
from django_strawberry_framework.types.converters import convert_relation, convert_scalar

CATEGORY_SCALAR_FIELDS = (
    "id",
    "name",
    "description",
    "is_private",
    "created_date",
    "updated_date",
)


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# Slice 1 — registry behaviour
# ---------------------------------------------------------------------------


def test_registry_get_returns_none_for_unregistered_model():
    assert registry.get(Category) is None


def test_registry_collision_raises_configuration_error():
    class CategoryTypeA(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    with pytest.raises(ConfigurationError, match="already registered"):

        class CategoryTypeB(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS


def test_registry_clear_drops_types_and_enums():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    assert registry.get(Category) is CategoryType
    registry.clear()
    assert registry.get(Category) is None


# ---------------------------------------------------------------------------
# Slice 2 — Meta validation
# ---------------------------------------------------------------------------


def test_subclass_without_meta_passes_through():
    """Intermediate abstract subclasses (no Meta) skip the pipeline."""

    class AbstractType(DjangoType):
        pass

    assert registry.get(Category) is None
    assert not hasattr(AbstractType, "__strawberry_definition__")


def test_meta_required_model_raises_when_missing():
    with pytest.raises(ConfigurationError, match="Meta.model is required"):

        class T(DjangoType):
            class Meta:
                fields = CATEGORY_SCALAR_FIELDS


def test_meta_fields_and_exclude_mutually_exclusive():
    with pytest.raises(ConfigurationError, match="mutually exclusive"):

        class T(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                exclude = ["description"]


@pytest.mark.parametrize(
    "deferred_key",
    [
        "filterset_class",
        "orderset_class",
        "aggregate_class",
        "fields_class",
        "search_fields",
        "interfaces",
    ],
)
def test_meta_rejects_each_deferred_key(deferred_key):
    """Every key in DEFERRED_META_KEYS must raise until the spec that owns it ships."""
    meta_attrs = {"model": Category, "fields": CATEGORY_SCALAR_FIELDS, deferred_key: object()}
    meta_cls = type("Meta", (), meta_attrs)
    with pytest.raises(ConfigurationError, match=deferred_key):
        type("T", (DjangoType,), {"Meta": meta_cls})


def test_meta_rejects_filterset_class():
    """Single-key smoke for the parametrized rejection above; kept for readability."""
    with pytest.raises(ConfigurationError, match="filterset_class"):

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                filterset_class = object


def test_meta_rejects_unknown_key():
    """Typo guard: keys outside the allowed/deferred sets raise."""
    with pytest.raises(ConfigurationError, match="Unknown Meta keys"):

        class T(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                bogus_key = "value"


def test_meta_fields_unknown_name_raises():
    """A typo in ``Meta.fields`` raises ``ConfigurationError`` rather than silently dropping."""
    with pytest.raises(ConfigurationError, match="unknown fields"):

        class T(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "nmae")  # typo: "nmae" instead of "name"


def test_meta_fields_unknown_name_includes_model_and_available():
    """The error names the model and lists available fields so the typo is obvious."""
    with pytest.raises(ConfigurationError) as exc_info:

        class T(DjangoType):
            class Meta:
                model = Category
                fields = ("nope",)

    msg = str(exc_info.value)
    assert "Category.Meta.fields" in msg
    assert "nope" in msg
    # Mentions some real fields so the consumer sees the available surface.
    assert "name" in msg


def test_meta_exclude_unknown_name_raises():
    """A typo in ``Meta.exclude`` raises rather than silently keeping the field."""
    with pytest.raises(ConfigurationError, match="unknown fields"):

        class T(DjangoType):
            class Meta:
                model = Category
                exclude = ("descriptoin",)  # typo


def test_meta_optimizer_hints_for_excluded_field_raises():
    """A hint for a real Django field that is *excluded* from the type raises.

    Pins the Medium fix from ``rev-types__base.md``: without this check
    the consumer's optimization intent is silently dead because the
    walker never visits an excluded field.
    """
    from django_strawberry_framework.optimizer.hints import OptimizerHint

    with pytest.raises(ConfigurationError, match="not in the type's selected fields"):

        class T(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name")
                optimizer_hints = {"items": OptimizerHint.prefetch_related()}


# ---------------------------------------------------------------------------
# Slice 2 — scalar synthesis
# ---------------------------------------------------------------------------


def test_scalar_mapping_against_category_textfields_booleanfields_datetimefields():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    a = CategoryType.__annotations__
    assert a["id"] is int
    assert a["name"] is str
    assert a["description"] is str
    assert a["is_private"] is bool
    assert a["created_date"] is datetime.datetime
    assert a["updated_date"] is datetime.datetime


def test_meta_fields_explicit_list_filters_concrete_fields():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert set(CategoryType.__annotations__) == {"id", "name"}


def test_meta_exclude_filters_concrete_fields():
    """Excluding scalars + reverse rels yields a clean scalar-only annotation set."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            # Exclude scalars under test plus the reverse rels (Item /
            # Property are unregistered in this test, so leaving them
            # selected would trip ``convert_relation``).
            exclude = ("description", "updated_date", "items", "properties")

    a = CategoryType.__annotations__
    assert "description" not in a
    assert "updated_date" not in a
    assert {"id", "name", "is_private", "created_date"} <= set(a)


@pytest.mark.skip(
    reason=(
        "Slice 2 known issue: Strawberry's @strawberry.type decorator regenerates "
        "cls.__annotations__ from its own field metadata after our merge in "
        "DjangoType.__init_subclass__, so the consumer's class-level annotation "
        "loses to the synthesized one. Fix is to bypass strawberry.type's "
        "annotation rewrite or to apply consumer overrides through Strawberry's "
        "own field-customization API. Tracked separately from the optimizer split."
    ),
)
def test_consumer_annotation_overrides_synthesized():
    """A consumer-declared annotation wins over the auto-mapped type."""

    class CategoryType(DjangoType):
        # Illustrative override (str -> int); not idiomatic but exercises the merge.
        description: int

        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    assert CategoryType.__annotations__["description"] is int


# ---------------------------------------------------------------------------
# Slice 2 — Strawberry finalization
# ---------------------------------------------------------------------------


def test_category_type_is_a_strawberry_type():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    assert hasattr(CategoryType, "__strawberry_definition__")
    assert CategoryType.__strawberry_definition__.name == "CategoryType"


def test_meta_name_overrides_graphql_type_name():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            name = "Category"

    assert CategoryType.__strawberry_definition__.name == "Category"


def test_meta_description_threads_through_to_strawberry():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            description = "A Faker provider."

    assert CategoryType.__strawberry_definition__.description == "A Faker provider."


# ---------------------------------------------------------------------------
# Slice 2 — default get_queryset is identity
# ---------------------------------------------------------------------------


def test_get_queryset_default_returns_input_unchanged():
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    qs = Category.objects.all()
    assert CategoryType.get_queryset(qs, info=None) is qs


def test_has_custom_get_queryset_false_when_using_default():
    """A subclass that does not override ``get_queryset`` reports False."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    assert CategoryType._is_default_get_queryset is True
    assert CategoryType.has_custom_get_queryset() is False


def test_has_custom_get_queryset_true_when_overridden():
    """A subclass that overrides ``get_queryset`` flips the sentinel and reports True."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    assert CategoryType._is_default_get_queryset is False
    assert CategoryType.has_custom_get_queryset() is True


def test_has_custom_get_queryset_inherits_through_intermediate_base():
    """A subclass without its own ``get_queryset`` whose parent overrides one still reports True.

    The sentinel sits on the class itself — Python's normal attribute
    lookup walks the MRO, so a child that does not redeclare
    ``get_queryset`` inherits the parent's ``False`` flag through the
    class hierarchy without us writing any MRO-walking code.
    """

    class BaseCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    # Drop the registry collision so we can subclass cleanly.
    registry.clear()

    class ChildCategoryType(BaseCategoryType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    assert ChildCategoryType.has_custom_get_queryset() is True


def test_has_custom_get_queryset_inherits_through_abstract_base_without_meta():
    """A concrete subclass inherits override-detection from an abstract base that has no ``Meta``.

    The abstract-shared-base pattern is documented as supported — the
    ``__init_subclass__`` ``meta is None`` early return notes
    "intermediate abstract subclasses without Meta are allowed". For
    that pattern to work end-to-end with the optimizer's
    downgrade-to-Prefetch rule, the sentinel flip must run regardless
    of whether the abstract base declares its own ``Meta``. Used to be
    a P1 bug: the flip sat after the ``meta is None`` early return, so
    an abstract base that overrode ``get_queryset`` without Meta never
    flipped the flag, and concrete subclasses inheriting from it
    silently reported ``has_custom_get_queryset() is False``.
    """

    class TenantScopedType(DjangoType):
        """Abstract base — no Meta, but defines ``get_queryset``."""

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    # The abstract base flipped its own sentinel even without Meta.
    assert TenantScopedType._is_default_get_queryset is False

    class CategoryType(TenantScopedType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    # Concrete subclass does not redefine ``get_queryset`` itself, but
    # inherits the flipped sentinel via normal attribute lookup.
    assert "get_queryset" not in CategoryType.__dict__
    assert CategoryType.has_custom_get_queryset() is True


# ---------------------------------------------------------------------------
# Slice 2 — convert_scalar direct unit coverage
# ---------------------------------------------------------------------------


def test_convert_scalar_raises_on_unsupported_field_type(monkeypatch):
    """Unsupported field types fail loudly with a message naming the field."""
    monkeypatch.delitem(converters.SCALAR_MAP, models.TextField)
    name_field = Category._meta.get_field("name")
    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        convert_scalar(name_field, "CategoryType")


# ---------------------------------------------------------------------------
# Slice 3 — relation conversion via _build_annotations
# ---------------------------------------------------------------------------


def test_relation_fk_to_target_djangotype():
    """Forward FK on Item maps to the registered ``CategoryType``."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    class ItemType(DjangoType):
        class Meta:
            model = Item
            # Skip ``entries`` reverse rel — Entry is unregistered in this test.
            fields = ("id", "name", "category")

    assert ItemType.__annotations__["category"] is CategoryType


def test_relation_reverse_fk_returns_list():
    """Reverse FK on Category maps to ``list[ItemType]`` and ``list[PropertyType]``."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items", "properties")

    a = CategoryType.__annotations__
    assert a["items"] == list[ItemType]
    assert a["properties"] == list[PropertyType]


def test_relation_meta_default_when_neither_fields_nor_exclude_set():
    """Omitting ``fields``/``exclude`` defaults to ``__all__`` and includes relations."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category

    a = CategoryType.__annotations__
    assert {"id", "name", "items", "properties"} <= set(a)
    assert a["items"] == list[ItemType]
    assert a["properties"] == list[PropertyType]


# TODO(spec-foundation 0.0.4): rewrite this test per
# ``docs/spec-foundation.md`` "Existing tests that must change". After
# the slice, class creation succeeds (the unresolved target becomes a
# pending relation) and the failure moves to ``finalize_django_types()``
# with the canonical unresolved-targets format ("Cannot finalize Django
# types: ... -> Category (no registered DjangoType)"). The match string
# below shifts from ``"not yet registered"`` to ``"Cannot finalize"`` /
# ``"no registered DjangoType"``. Coverage of definition-order success
# (the bidirectional version of this graph) moves to the new file
# ``tests/types/test_definition_order.py``.
def test_relation_unregistered_target_raises():
    """Referencing a model whose DjangoType is not yet registered raises."""
    with pytest.raises(ConfigurationError, match="not yet registered"):

        class ItemType(DjangoType):
            class Meta:
                model = Item
                # Category is not registered, so the FK lookup fails.
                fields = ("id", "name", "category")


def test_relation_full_chain_when_all_targets_registered():
    """Every fakeshop relation resolves cleanly when types are declared in order."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            # Exclude reverse rels; Item / Property come next.
            fields = CATEGORY_SCALAR_FIELDS

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            # category FK + scalars; entries reverse rel waits for EntryType.
            fields = ("id", "name", "category")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value", "property", "item")

    assert PropertyType.__annotations__["category"] is CategoryType
    assert ItemType.__annotations__["category"] is CategoryType
    assert EntryType.__annotations__["property"] is PropertyType
    assert EntryType.__annotations__["item"] is ItemType


def test_convert_relation_nullable_fk_widens_to_optional(monkeypatch):
    """Nullable forward FK widens to ``T | None``.

    No fakeshop FK declares ``null=True``, so monkeypatch the Item.category
    field for the duration of this test. ``convert_relation`` reads
    ``field.null`` directly; the widening branch is exercised without the
    rest of the pipeline.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    item_category = Item._meta.get_field("category")
    monkeypatch.setattr(item_category, "null", True)
    annotation = convert_relation(item_category)
    assert annotation == (CategoryType | None)


# ---------------------------------------------------------------------------
# Slice 3 — placeholders for paths fakeshop does not yet exercise
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="Slice 3+: M2M relation — fakeshop has no M2M field; deferred.")
def test_relation_m2m_returns_list():
    pass


# TODO(spec-foundation 0.0.4): DELETE this skipped placeholder when the
# foundation slice ships. The cyclic-acceptance coverage it stands in
# for moves to ``tests/types/test_definition_order.py`` per
# ``docs/spec-foundation.md`` "Cyclic acceptance tests" — declared in
# either order, FK / reverse FK / OneToOne / reverse OneToOne / M2M
# cardinalities, multi-cycle, unresolved-target failure, and the four
# manual-annotation override shapes. The skip reason mentions
# ``lazy_ref``; that placeholder method is being deleted in the same
# slice (see ``registry.py`` TODO).
@pytest.mark.skip(
    reason=(
        "Slice 3+: forward-reference / definition-order independence. The current "
        "implementation requires targets to be registered first; lazy_ref is pending."
    ),
)
def test_forward_reference_resolves_when_target_defined_later():
    pass
