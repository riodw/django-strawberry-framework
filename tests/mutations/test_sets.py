"""``DjangoMutation`` base, ``Meta`` validation, registration, and the phase-2.5 bind.

Covers the spec-036 Slice 2 surface (``django_strawberry_framework/mutations/sets.py``):

- the ``Meta`` validation matrix at class creation (unknown key; no-resolvable-model
  via ``_resolve_model``; bad / missing ``operation``; ``fields`` + ``exclude``
  both supplied; ``input_class`` not a ``@strawberry.input`` type; the AR-M2
  diverging-field-name rejection - the Slice-1-deferred half);
- ``permission_classes`` defaulting to ``[DjangoModelPermission]`` (and an explicit
  override honored);
- the ``_resolve_model`` overridable seam;
- declaration registration (concrete registered, abstract base not, post-finalize
  rejected);
- the phase-2.5 bind - the finalize-time materialize trigger Slice 1 deferred:
  generated ``<Model>Input`` / ``<Model>PartialInput`` / ``<Name>Payload`` become
  module globals of ``mutations.inputs``, identical shapes dedupe, distinct shapes
  colliding on one generated name raise ``ConfigurationError`` (AR-M6), and the
  ``registry.clear()`` co-clear resets both the input/payload ledger and the
  declaration registry;
- the no-registered-primary-type finalize error (zero-type vs ambiguous phrasings);
- the namespace-isolation contract (a mutation ``Meta`` key is not a ``DjangoType``
  ``Meta`` key, Decision 12).

System-under-test is the metaclass / validation / bind. The realistic products
``Item`` / ``Category`` FK fixtures cover the happy path; package-local fixture
models cover the no-primary / ambiguous cases products lacks.
"""

from __future__ import annotations

import itertools
import sys

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from django.db import models
from strawberry import relay

import django_strawberry_framework
from django_strawberry_framework import (
    DjangoModelPermission,
    DjangoMutation,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations import (
    DjangoModelPermission as DjangoModelPermissionFromPackage,
)
from django_strawberry_framework.mutations import (
    DjangoMutation as DjangoMutationFromPackage,
)
from django_strawberry_framework.mutations.inputs import INPUTS_MODULE_PATH
from django_strawberry_framework.mutations.sets import (
    _mutation_registry,
    iter_mutations,
)
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Reset the registry (now co-clearing the mutation ledger + declaration registry).

    ``registry.clear()`` is wired in this slice to co-clear
    ``clear_mutation_input_namespace`` (input + payload globals ledger) and
    ``clear_mutation_registry`` (the declaration registry), so a single
    ``registry.clear()`` resets every mutation-side ledger. The products
    ``DjangoType``s register on import, so the clear is needed before/after.
    """
    registry.clear()
    yield
    registry.clear()


_app_label_counter = itertools.count(1)


def _unique_app_label() -> str:
    """Return a unique ``app_label`` per call to avoid Django's re-register warning."""
    return f"test_mutation_sets__{next(_app_label_counter)}"


# ---------------------------------------------------------------------------
# Meta validation matrix - class creation, ConfigurationError
# ---------------------------------------------------------------------------


def test_meta_without_model_raises():
    """A ``Meta`` with no resolvable model raises naming ``Meta.model`` (Medium-5 seam)."""
    with pytest.raises(ConfigurationError, match="no resolvable model"):

        class CreateItem(DjangoMutation):
            class Meta:
                operation = "create"


def test_meta_model_string_raises_at_class_creation():
    """A string ``Meta.model`` raises ``ConfigurationError`` at class creation.

    Before the gate, ``Meta.model = "Item"`` snapshotted successfully and the
    phase-2.5 bind crashed with ``AttributeError: 'str' object has no attribute
    '__name__'``. Mirror ``DjangoType``'s ``Meta.model must be a Django model
    class`` posture so a typo'd / lazy string never reaches finalize.
    """
    with pytest.raises(ConfigurationError, match="must be a Django model class"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = "Item"
                operation = "create"


def test_meta_model_instance_raises_at_class_creation():
    """A model *instance* ``Meta.model`` raises at class creation (not finalize)."""
    with pytest.raises(ConfigurationError, match="must be a Django model class"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item()
                operation = "create"


def test_meta_bad_operation_raises():
    """An ``operation`` outside the valid set raises naming the bad value + valid set."""
    with pytest.raises(ConfigurationError, match="operation must be one of"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "upsert"


def test_meta_missing_operation_raises():
    """A missing ``operation`` raises the same operation error (``None`` is not valid)."""
    with pytest.raises(ConfigurationError, match="operation must be one of"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item


def test_meta_unknown_key_raises():
    """A stray ``Meta`` key raises the typo guard (mutation-local allowed set)."""
    with pytest.raises(ConfigurationError, match="unknown keys"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                widget = "nope"


def test_meta_fields_and_exclude_both_raises():
    """Declaring both ``fields`` and ``exclude`` raises (mutual exclusion at creation)."""
    with pytest.raises(ConfigurationError, match="both `fields` and `exclude`"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                fields = ("name",)
                exclude = ("description",)


def test_meta_duplicate_fields_raises():
    """A repeated name in ``Meta.fields`` raises at class creation (feedback - bug 9).

    ``("name", "name", "category")`` would otherwise collapse silently when the
    effective field set is taken as a ``frozenset``, masking the malformed
    declaration. The shared ``normalize_field_name_sequence`` rejects it fail-loud
    naming the repeated field.
    """
    with pytest.raises(ConfigurationError, match="duplicate field name"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                fields = ("name", "name", "category")


def test_meta_duplicate_exclude_raises():
    """A repeated name in ``Meta.exclude`` is rejected the same way, naming ``exclude``."""
    with pytest.raises(ConfigurationError, match="Meta.exclude declares duplicate"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                exclude = ("description", "description")


def test_meta_unknown_fields_raises_at_class_creation():
    """An unknown ``Meta.fields`` name raises at class creation (not finalize).

    ``editable_input_fields`` already rejected unknown names, but only when the
    bind / generator walked the set - so a typo'd create/update ``Meta.fields``
    registered cleanly and failed later. The model ``_validate_meta`` now runs
    that walk at class creation (form-flavor parity).
    """
    with pytest.raises(ConfigurationError, match="non-editable or unknown field"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                fields = ("not_a_real_field",)


def test_meta_empty_fields_raises_at_class_creation():
    """``Meta.fields = ()`` on create/update raises at class creation (empty input)."""
    with pytest.raises(ConfigurationError, match="narrowed the editable column set to empty"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                fields = ()


def test_meta_fields_non_string_entry_raises():
    """A non-string entry in ``Meta.fields`` raises at class creation."""
    with pytest.raises(ConfigurationError, match="non-string entry"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                fields = (1, 2)


def test_meta_delete_with_fields_raises():
    """``operation="delete"`` with ``Meta.fields`` raises at class creation (feedback - bug 7).

    A delete is id-only and materializes NO input, so it never runs the
    ``editable_input_fields`` walk that would otherwise catch an unknown field
    name - a typo'd ``fields`` would finalize silently. Because ``fields`` /
    ``exclude`` have no effect on a delete at all, declaring them is rejected
    outright regardless of whether the names are valid.
    """
    with pytest.raises(ConfigurationError, match="id-only and takes no input"):

        class DeleteItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "delete"
                fields = ("definitely_not_a_field",)


def test_meta_delete_with_exclude_raises():
    """The same rejection applies to ``Meta.exclude`` on a delete operation."""
    with pytest.raises(ConfigurationError, match="id-only and takes no input"):

        class DeleteItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "delete"
                exclude = ("name",)


def test_meta_input_class_not_strawberry_input_raises():
    """A plain (non-``@strawberry.input``) ``input_class`` raises (Error-shapes)."""

    class NotAnInput:
        pass

    with pytest.raises(ConfigurationError, match="@strawberry.input"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                input_class = NotAnInput


def test_meta_input_class_diverging_field_names_raises():
    """An ``input_class`` with names off the generated scheme raises (AR-M2, deferred half).

    The generated scheme: scalars use the model field name, forward FK uses
    ``<field>_id``. A custom input naming a relation field ``category`` (instead of
    ``category_id``) diverges and is rejected at class creation.
    """

    @strawberry.input
    class BadItemInput:
        name: str
        category: int  # should be ``category_id`` per the generated scheme

    with pytest.raises(ConfigurationError, match="diverge from the generated naming scheme"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                input_class = BadItemInput


def test_meta_input_class_following_scheme_validates_clean():
    """A custom ``input_class`` whose names follow the scheme is accepted."""

    @strawberry.input
    class GoodItemInput:
        name: str
        category_id: int

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = GoodItemInput

    assert CreateItem._mutation_meta.input_class is GoodItemInput


@pytest.mark.parametrize(
    ("operation", "override_name", "applies_to"),
    (
        ("delete", "input_class", "create"),
        ("delete", "partial_input_class", "update"),
        ("create", "partial_input_class", "update"),
        ("update", "input_class", "create"),
    ),
)
def test_meta_inapplicable_input_override_raises(operation, override_name, applies_to):
    """Every input override fails loud when its operation cannot consume it."""

    @strawberry.input
    class GoodItemInput:
        name: str
        category_id: int

    mutation_meta = type(
        "Meta",
        (),
        {"model": product_models.Item, "operation": operation, override_name: GoodItemInput},
    )
    with pytest.raises(
        ConfigurationError,
        match=rf"Meta\.{override_name} applies only to operation='{applies_to}'",
    ):

        class MisconfiguredItemMutation(DjangoMutation):
            Meta = mutation_meta


@pytest.mark.parametrize(
    ("operation", "override_name", "other_override_name"),
    (
        ("create", "input_class", "partial_input_class"),
        ("update", "partial_input_class", "input_class"),
    ),
)
def test_meta_applicable_input_override_is_accepted(operation, override_name, other_override_name):
    """Create and update retain the one consumer override each binds."""

    @strawberry.input
    class GoodItemInput:
        name: str
        category_id: int

    mutation_meta = type(
        "Meta",
        (),
        {"model": product_models.Item, "operation": operation, override_name: GoodItemInput},
    )

    class ItemMutation(DjangoMutation):
        Meta = mutation_meta

    assert getattr(ItemMutation._mutation_meta, override_name) is GoodItemInput
    assert getattr(ItemMutation._mutation_meta, other_override_name) is None


# ---------------------------------------------------------------------------
# permission_classes default + override
# ---------------------------------------------------------------------------


def test_permission_classes_defaults_to_django_model_permission():
    """A ``Meta`` with no ``permission_classes`` resolves to ``[DjangoModelPermission]``."""

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    assert CreateItem._mutation_meta.permission_classes == [DjangoModelPermission]


def test_permission_classes_explicit_override_honored():
    """An explicit ``permission_classes`` list is stored verbatim."""

    class AllowAll:
        def has_permission(
            self,
            info,
            mutation,
            operation,
            data,
            instance=None,
        ):
            return True

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = [AllowAll]

    assert CreateItem._mutation_meta.permission_classes == [AllowAll]


def test_permission_classes_tuple_is_normalized_to_list():
    """A tuple ``permission_classes`` is normalized to a list (feedback P2)."""

    class AllowAll:
        def has_permission(
            self,
            info,
            mutation,
            operation,
            data,
            instance=None,
        ):
            return True

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = (AllowAll,)

    assert CreateItem._mutation_meta.permission_classes == [AllowAll]


def test_permission_classes_bare_class_raises():
    """A bare class (not wrapped in a sequence) raises at class creation (feedback P2).

    The contract is a *sequence* of permission classes; a single class would
    iterate as a ``TypeError`` inside ``check_permission`` at request time, so it is
    rejected up front naming the sequence requirement.
    """

    class AllowAll:
        def has_permission(
            self,
            info,
            mutation,
            operation,
            data,
            instance=None,
        ):
            return True

    with pytest.raises(ConfigurationError, match="must be a sequence of"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                permission_classes = AllowAll


def test_permission_classes_bare_string_raises():
    """A bare string ``permission_classes`` raises (would iterate as characters)."""
    with pytest.raises(ConfigurationError, match="must be a sequence of"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                permission_classes = "AllowAll"


def test_permission_classes_instance_entry_raises():
    """An entry that is an INSTANCE (not a class) raises (feedback P2).

    ``check_permission`` does ``permission_class().has_permission(...)`` - it
    INSTANTIATES each entry - so an already-instantiated object is invalid and is
    rejected at class creation rather than as a request-time ``TypeError``.
    """

    class AllowAll:
        def has_permission(
            self,
            info,
            mutation,
            operation,
            data,
            instance=None,
        ):
            return True

    with pytest.raises(ConfigurationError, match="not a permission class exposing has_permission"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                permission_classes = [AllowAll()]  # instance, not the class


def test_permission_classes_entry_without_has_permission_raises():
    """A class entry lacking ``has_permission`` raises at class creation (feedback P2)."""

    class NotAPermission:
        pass

    with pytest.raises(ConfigurationError, match="not a permission class exposing has_permission"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                permission_classes = [NotAPermission]


# ---------------------------------------------------------------------------
# _resolve_model seam (Medium-5)
# ---------------------------------------------------------------------------


def test_resolve_model_seam_lets_subclass_supply_model_without_meta_model():
    """Overriding ``_resolve_model`` supplies the model without a literal ``Meta.model``."""

    class FlavorMutation(DjangoMutation):
        @classmethod
        def _resolve_model(cls, meta):
            # The 0.0.12 / 0.0.13 flavors derive the model from form_class /
            # serializer_class; emulate that here with a stand-in source.
            return getattr(meta, "_model_source", None)

    class CreateItem(FlavorMutation):
        class Meta:
            _model_source = product_models.Item
            operation = "create"

    assert CreateItem._mutation_meta.model is product_models.Item


# ---------------------------------------------------------------------------
# Declaration registration
# ---------------------------------------------------------------------------


def test_concrete_mutation_registers_abstract_base_does_not():
    """A concrete mutation is recorded; the abstract ``DjangoMutation`` base is not."""

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    assert CreateItem in iter_mutations()
    assert DjangoMutation not in iter_mutations()


def test_registration_is_idempotent():
    """Re-recording the same class (identity) does not double-register."""

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    from django_strawberry_framework.mutations.sets import register_mutation

    register_mutation(CreateItem)
    assert _mutation_registry.count(CreateItem) == 1


def test_late_declaration_after_finalize_raises():
    """Declaring a mutation after ``finalize_django_types()`` raises (Edge cases)."""

    class ItemType2(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    finalize_django_types()
    with pytest.raises(ConfigurationError, match="after finalization"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"


# ---------------------------------------------------------------------------
# Phase-2.5 bind - the finalize-time materialize trigger (Slice-1-deferred)
# ---------------------------------------------------------------------------


def _declare_products_primaries():
    """Register primary ``DjangoType``s for ``Item`` and ``Category`` (Relay-shaped)."""

    class CategoryT(DjangoType, strawberry.relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class ItemT(DjangoType, strawberry.relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    return CategoryT, ItemT


def test_bind_materializes_input_and_payload_globals():
    """After finalize, the create/update/delete classes are materialized into inputs.

    The bind is the FIRST caller of ``build_mutation_input`` / ``build_payload_type``
    / ``materialize_mutation_input_class``: pin they fire at finalize. The true
    "materialized at finalize" signal is the ledger ``_materialized_names`` (reset
    by ``registry.clear()``), not ``hasattr`` of the module global - materialized
    classes are deliberately left PARKED in ``__dict__`` across a clear (the
    shared parked-globals lifecycle), so a prior test's parked ``ItemInput`` would
    make a bare ``hasattr`` pass spuriously.
    """
    from django_strawberry_framework.mutations.inputs import _materialized_names

    _declare_products_primaries()

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    class UpdateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"

    class DeleteItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "delete"

    # Ledger empty before finalize: nothing has been materialized this build.
    assert _materialized_names == {}

    finalize_django_types()

    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    # create -> ItemInput; update -> ItemPartialInput; delete -> no input.
    assert "ItemInput" in _materialized_names
    assert "ItemPartialInput" in _materialized_names
    # Every operation gets a payload.
    assert "CreateItemPayload" in _materialized_names
    assert "UpdateItemPayload" in _materialized_names
    assert "DeleteItemPayload" in _materialized_names
    # The materialized class is also a real module global (the lazy-ref contract).
    assert inputs_module.ItemInput is _materialized_names["ItemInput"]

    # The bind stashes forward-compat refs for Slice 3.
    assert CreateItem._input_class is _materialized_names["ItemInput"]
    assert CreateItem._payload_type_name == "CreateItemPayload"
    assert DeleteItem._input_class is None  # delete is id-only
    assert UpdateItem._primary_type is not None


def test_bind_is_retry_idempotent_after_fixable_later_phase_failure(monkeypatch):
    """A re-call after a fixable post-bind finalization failure succeeds, not a masked collision (feedback #6).

    ``finalize_django_types()`` documents recover-in-place: fix the offending
    cause and call again, no ``registry.clear()`` required. But phase 2.5 binds
    mutations (materializing ``ItemInput`` into the ledger) BEFORE the later phases
    that can fail. The prior bind cleared only ``_shape_build_cache``, leaving the
    ledger populated with run-1's class object, so run-2 rebuilt a fresh
    ``ItemInput`` and hit a spurious distinct-class collision in
    ``materialize_generated_input_class`` - masking the original, now-fixed error.
    Resetting the materialization ledgers in ``finalize_django_types`` before the
    bind sequence makes the rerun clean.
    """
    from django_strawberry_framework.mutations.inputs import _materialized_names

    _declare_products_primaries()

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    # A fixable failure in a phase that runs AFTER the mutation bind (orderset bind
    # sits just past ``bind_mutations`` / ``bind_form_mutations`` in phase 2.5).
    def _boom() -> None:
        raise RuntimeError("injected post-bind finalization failure")

    monkeypatch.setattr("django_strawberry_framework.types.finalizer._bind_ordersets", _boom)
    with pytest.raises(RuntimeError, match="injected post-bind"):
        finalize_django_types()
    # The bind already materialized the input before the later phase failed.
    assert "ItemInput" in _materialized_names
    assert registry.is_finalized() is False

    # Fix the cause and re-finalize WITHOUT registry.clear(): the rerun must NOT
    # raise the masking distinct-class collision.
    monkeypatch.undo()
    finalize_django_types()

    assert registry.is_finalized() is True
    assert "ItemInput" in _materialized_names
    assert CreateItem._input_class is _materialized_names["ItemInput"]


def test_bind_merges_consumer_input_class_with_generated_remainder():
    """A consumer ``input_class`` overriding ONE field is MERGED, not a wholesale replace (CR-2).

    The spec-010 relation-override contract (DoD line 51 / line 336, AR-M2): the
    consumer declares only the field it customizes; the generator fills the rest of
    the editable shape, and the consumer's field is honored, not clobbered. A
    partial consumer input must therefore yield the FULL shape - both the
    consumer's ``name`` (with its custom description preserved) AND the generated
    ``category_id`` - under the canonical ``ItemInput`` name, never just ``name``.
    """
    from django_strawberry_framework.mutations.inputs import _materialized_names

    _declare_products_primaries()

    @strawberry.input
    class CustomItemInput:
        # Override ONLY ``name`` (custom description); everything else is generated.
        name: str = strawberry.field(description="A custom-described name")

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = CustomItemInput

    finalize_django_types()

    merged = _materialized_names["ItemInput"]
    assert CreateItem._input_class is merged
    fields = {f.python_name: f for f in merged.__strawberry_definition__.fields}
    # Generated remainder filled in (the partial-replacement bug would drop these).
    assert "category_id" in fields
    assert "is_private" in fields
    # Consumer field honored, not clobbered (its description survives the merge).
    assert fields["name"].description == "A custom-described name"


def test_bind_merges_consumer_partial_input_class_for_update():
    """A consumer ``partial_input_class`` is likewise merged on the update side (CR-2)."""
    from django_strawberry_framework.mutations.inputs import _materialized_names

    _declare_products_primaries()

    @strawberry.input
    class CustomItemPartial:
        name: str | None = strawberry.field(default=strawberry.UNSET, description="custom partial")

    class UpdateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"
            partial_input_class = CustomItemPartial

    finalize_django_types()

    merged = _materialized_names["ItemPartialInput"]
    assert UpdateItem._input_class is merged
    fields = {f.python_name: f for f in merged.__strawberry_definition__.fields}
    assert "category_id" in fields  # generator filled the rest
    assert fields["name"].description == "custom partial"  # consumer field honored


def test_bind_rejects_raw_pk_relation_override_for_relay_target():
    """A raw-pk relation override for a Relay-Node target raises at bind (AR-M2 / Decision 10).

    ``Category`` has a primary Relay-Node type, so the generated ``category_id`` input
    is a ``relay.GlobalID`` that is type-checked (AR-H4) AND visibility-checked through
    ``Category``'s ``get_queryset`` (Decision 10 / feedback P1) at decode. A consumer
    ``input_class`` declaring ``category_id: int`` (a raw pk) would, at decode, be seen
    as a non-``GlobalID`` value and passed through as a raw pk - bypassing both checks
    and letting a permitted writer attach a ``Category`` row they could not *see*. The
    bind rejects it fail-loud (the AR-M2 posture).

    Enforced at finalization, not class creation: whether ``Category`` has a primary
    Relay-Node type is a ``registry.get`` lookup only reliably populated at the
    phase-2.5 bind (``_validate_input_class`` name-checks at class creation but cannot
    know the id type then - it passes ``related_primary_type=None``).
    """
    _declare_products_primaries()

    @strawberry.input
    class RawPkItemInput:
        name: str
        category_id: int  # raw pk: would bypass the GlobalID type/visibility contract

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = RawPkItemInput

    with pytest.raises(ConfigurationError, match="diverges from the generated input"):
        finalize_django_types()


def test_bind_rejects_raw_pk_relation_override_on_partial_input():
    """The type-lock applies to ``partial_input_class`` (update) too (AR-M2 / Decision 10)."""
    _declare_products_primaries()

    @strawberry.input
    class RawPkItemPartial:
        category_id: int | None = strawberry.field(default=strawberry.UNSET)

    class UpdateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"
            partial_input_class = RawPkItemPartial

    with pytest.raises(ConfigurationError, match="diverges from the generated input"):
        finalize_django_types()


def test_bind_accepts_globalid_relation_override_for_relay_target():
    """A relation override that keeps the generated ``GlobalID`` id type binds clean (AR-M2).

    The contract-compliant form: the consumer customizes the relation field's
    representation (here a description) while keeping the ``relay.GlobalID`` id type, so
    the AR-H4 type-check and the Decision-10 visibility contract still ride the merged
    field. The merge honors the consumer's field, and the generator fills the remainder.
    """
    from django_strawberry_framework.mutations.inputs import _materialized_names

    _declare_products_primaries()

    @strawberry.input
    class GidItemInput:
        category_id: strawberry.relay.GlobalID = strawberry.field(
            description="custom category ref",
        )

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = GidItemInput

    finalize_django_types()

    merged = _materialized_names["ItemInput"]
    assert CreateItem._input_class is merged
    fields = {f.python_name: f for f in merged.__strawberry_definition__.fields}
    assert fields["category_id"].description == "custom category ref"  # consumer field honored
    assert "name" in fields  # generator filled the rest


def _declare_book_m2m_primaries():
    """Register Relay-Node primaries for ``Genre`` / ``Shelf`` / ``Book`` (Book has a real M2M).

    The M2M analogue of ``_declare_products_primaries``: ``Book.genres`` is a forward
    M2M to ``Genre`` (a Relay-Node primary), so the generated relation input is
    ``list[relay.GlobalID]`` - the shape an override must keep.
    """

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    class ShelfT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")
            primary = True

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title", "genres")
            primary = True

    return GenreT, ShelfT, BookT


def test_bind_rejects_m2m_relation_override_as_scalar_globalid():
    """An M2M override declared as a SCALAR ``relay.GlobalID`` raises at bind (feedback - bug 1/2).

    ``Book.genres`` generates ``list[relay.GlobalID]``; a consumer ``genres:
    relay.GlobalID`` keeps the GlobalID core but loses the list container, so the
    resolver would mis-handle the scalar (the M2M decode iterates a list). The core-
    only type-lock missed this - the shape-aware lock catches the list-depth mismatch.
    """
    _declare_book_m2m_primaries()

    @strawberry.input
    class BadBookInput:
        genres: relay.GlobalID

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            fields = ("title", "shelf", "genres")
            input_class = BadBookInput

    with pytest.raises(ConfigurationError, match="diverges from the generated input"):
        finalize_django_types()


def test_bind_rejects_m2m_relation_override_as_nested_globalid_list():
    """An M2M override declared as a NESTED ``list[list[relay.GlobalID]]`` raises at bind.

    The nested-list shape has the GlobalID core but list depth 2 vs the generated
    depth 1; the inner lists are not ``relay.GlobalID`` instances, so each would be
    passed through as a raw pk into ``.set(...)`` - a top-level ORM error at runtime.
    The shape-lock rejects the depth mismatch at the bind.
    """
    _declare_book_m2m_primaries()

    @strawberry.input
    class BadBookInput:
        genres: list[list[relay.GlobalID]]

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            fields = ("title", "shelf", "genres")
            input_class = BadBookInput

    with pytest.raises(ConfigurationError, match="diverges from the generated input"):
        finalize_django_types()


def test_bind_rejects_fk_relation_override_as_globalid_list():
    """A forward-FK override declared as a ``list[relay.GlobalID]`` raises at bind (bug 1/2).

    ``Item.category`` generates a SCALAR ``relay.GlobalID``; a ``category_id:
    list[relay.GlobalID]`` has the GlobalID core but list depth 1 vs the generated 0.
    At runtime the list would be stored as the ``category_id`` attr and Django would
    raise against the scalar FK column under the MODEL field name (``category``), not
    the ``categoryId`` input field. The shape-lock rejects it at the bind.
    """
    _declare_products_primaries()

    @strawberry.input
    class BadItemInput:
        category_id: list[relay.GlobalID]

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = BadItemInput

    with pytest.raises(ConfigurationError, match="diverges from the generated input"):
        finalize_django_types()


def test_bind_accepts_m2m_relation_override_as_globalid_list():
    """The contract-compliant M2M override - ``list[relay.GlobalID]`` - binds clean (positive control).

    Proves the shape-lock does not over-reject: an override that keeps BOTH the
    ``relay.GlobalID`` core AND the one-level ``list`` container (here adding a
    description) is honored, and the generator fills the remainder.
    """
    from django_strawberry_framework.mutations.inputs import _materialized_names

    _declare_book_m2m_primaries()

    @strawberry.input
    class GidBookInput:
        genres: list[relay.GlobalID] = strawberry.field(description="custom genres ref")

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            fields = ("title", "shelf", "genres")
            input_class = GidBookInput

    finalize_django_types()

    merged = _materialized_names[CreateBook._input_class.__name__]
    fields = {f.python_name: f for f in merged.__strawberry_definition__.fields}
    assert fields["genres"].description == "custom genres ref"  # consumer field honored
    assert "shelf_id" in fields  # generator filled the FK remainder


def test_bind_dedupes_identical_full_shapes():
    """Two create mutations over the same model with the full shape share one ``ItemInput``."""
    _declare_products_primaries()

    class CreateItemA(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    class CreateItemB(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    finalize_django_types()
    # Both bind to the same materialized ``ItemInput`` (identical shapes dedupe).
    assert CreateItemA._input_class is CreateItemB._input_class
    assert CreateItemA._input_class is sys.modules[INPUTS_MODULE_PATH].ItemInput


def test_bind_dedupes_full_set_fields_with_bare_create():
    """A ``fields`` list naming the full editable set dedupes with a bare create.

    The type identity is the EFFECTIVE field set (spec-036 Decision 6 line 334),
    not the raw ``(fields, exclude)`` declaration. ``Item``'s full editable set is
    ``("name", "description", "category", "attachment", "is_private")``; a
    ``fields`` list naming exactly that set IS the canonical shape, so it must
    resolve to the same materialized ``ItemInput`` as an un-narrowed create
    (spec-036 Edge cases line 509) rather than spuriously raising AR-M6 on a
    same-name collision.
    """
    _declare_products_primaries()

    class CreateBare(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    class CreateFull(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            fields = (
                "name",
                "description",
                "category",
                "attachment",
                "is_private",
            )

    # Reaches finalize without raising; both share the one canonical ``ItemInput``.
    finalize_django_types()
    assert CreateBare._input_class is CreateFull._input_class
    assert CreateBare._input_class is sys.modules[INPUTS_MODULE_PATH].ItemInput


def test_bind_dedupes_fields_with_complementary_exclude():
    """``fields=("name",)`` and the complementary ``exclude`` dedupe to one shape.

    Two narrowings that select the same effective set ``{name}`` via different
    spellings - ``fields=("name",)`` vs ``exclude`` naming every OTHER editable
    column - resolve to the same shape-derived ``<Model>...Input`` name and must
    dedupe to one materialized type (spec-036 Decision 6 line 334 / Edge cases line
    509), not raise a spurious AR-M6 collision on the shared name.
    """
    _declare_products_primaries()

    class CreateViaFields(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            fields = ("name",)

    class CreateViaExclude(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            exclude = (
                "description",
                "category",
                "attachment",
                "is_private",
            )

    # Reaches finalize without raising; both share one shape-derived input type.
    finalize_django_types()
    assert CreateViaFields._input_class is CreateViaExclude._input_class
    # The shared type is a narrowed, shape-derived name (not the canonical
    # ``ItemInput``, since the effective set is only ``{name}``).
    assert CreateViaFields._input_class.__name__ != "ItemInput"


def test_bind_merged_and_generated_same_shape_distinct_representations_raise():
    """Two representations of one input shape claiming the canonical name raise (AR-M6 / CR-2).

    Under the merge contract a consumer ``input_class`` is materialized under the
    canonical SHAPE name (``ItemInput``) - the consumer's Python class name is
    irrelevant, it customizes representations of existing columns, not the shape.
    So two ``Item`` create mutations that resolve the same ``ItemInput`` shape to
    two DIFFERENT representations - one consumer-customized, one plain generated -
    claim one name with two distinct class objects, and the input ledger's
    collision check fires at finalize (the end-to-end AR-M6 input trigger under
    the merge realization; a consumer class name can no longer dodge or forge a
    collision).
    """
    _declare_products_primaries()

    @strawberry.input
    class CustomItemInput:
        name: str = strawberry.field(description="custom")

    class CreateItemCustom(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = CustomItemInput

    class CreateItemPlain(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    with pytest.raises(ConfigurationError, match="ItemInput"):
        finalize_django_types()


def test_bind_duplicate_payload_name_distinct_shapes_raises():
    """Two mutations generating the same ``<Name>Payload`` for distinct shapes raise (AR-M6).

    Same class name in different "modules" -> same ``<Name>Payload`` name but a
    distinct object slot/type, so the payload ledger collision fires at finalize.
    """
    _declare_products_primaries()

    # Two distinct mutation classes that resolve to the same payload name
    # ``CreateThingPayload`` over distinct primary object types (Item vs Category).
    CreateThing1 = type(
        "CreateThing",
        (DjangoMutation,),
        {"Meta": type("Meta", (), {"model": product_models.Item, "operation": "create"})},
    )
    CreateThing2 = type(
        "CreateThing",
        (DjangoMutation,),
        {"Meta": type("Meta", (), {"model": product_models.Category, "operation": "create"})},
    )
    assert CreateThing1 in iter_mutations()
    assert CreateThing2 in iter_mutations()

    with pytest.raises(ConfigurationError, match="CreateThingPayload"):
        finalize_django_types()


def test_registry_clear_co_clears_mutation_namespace_and_declarations():
    """``registry.clear()`` resets the materialized ledger AND the declaration registry."""
    _declare_products_primaries()

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    finalize_django_types()
    assert hasattr(sys.modules[INPUTS_MODULE_PATH], "ItemInput")  # materialized
    assert iter_mutations()  # non-empty before clear

    registry.clear()

    # Declaration registry emptied via ``clear_mutation_registry``; ledger emptied
    # via ``clear_mutation_input_namespace`` so a fresh finalize re-emits cleanly.
    assert iter_mutations() == ()
    from django_strawberry_framework.mutations.inputs import _materialized_names

    assert _materialized_names == {}


# ---------------------------------------------------------------------------
# No-registered-primary-type finalize error (Decision 11 / Error-shapes)
# ---------------------------------------------------------------------------


def test_bind_no_registered_type_raises_no_type_to_return():
    """A mutation over a model with no registered ``DjangoType`` raises at finalize."""

    class Lonely(models.Model):
        name = models.TextField()

        class Meta:
            app_label = _unique_app_label()

    class CreateLonely(DjangoMutation):
        class Meta:
            model = Lonely
            operation = "create"

    with pytest.raises(ConfigurationError, match="no type to return"):
        finalize_django_types()


def test_bind_resolve_primary_distinguishes_ambiguous_from_zero_type():
    """``_resolve_primary_type`` phrases the ambiguity case distinctly from no-type.

    The full ``finalize_django_types()`` path catches a multiple-types-no-primary
    model at the Phase-1 ``_audit_primary_ambiguity`` BEFORE the bind runs (the
    plan's documented note), so the bind's ambiguity branch is exercised here at
    the unit level. The bind consults ``types_for`` (not just ``registry.get``,
    which returns ``None`` for both cases) to phrase the right message.
    """
    from django_strawberry_framework.mutations.sets import _resolve_primary_type

    class Twin(models.Model):
        name = models.TextField()

        class Meta:
            app_label = _unique_app_label()

    class TwinTypeA(DjangoType):
        class Meta:
            model = Twin
            fields = ("id", "name")

    class TwinTypeB(DjangoType):
        class Meta:
            model = Twin
            fields = ("id", "name")

    class CreateTwin(DjangoMutation):
        class Meta:
            model = Twin
            operation = "create"

    with pytest.raises(ConfigurationError, match="multiple registered DjangoTypes"):
        _resolve_primary_type(CreateTwin, Twin)

    # The full finalize path catches this earlier at the Phase-1 ambiguity audit.
    with pytest.raises(ConfigurationError, match="multiple registered DjangoType subclasses"):
        finalize_django_types()


# ---------------------------------------------------------------------------
# Namespace isolation - mutation Meta key is not a DjangoType Meta key (Decision 12)
# ---------------------------------------------------------------------------


def test_mutation_meta_key_rejected_on_django_type_meta():
    """A mutation-only key (``operation``) on a ``DjangoType.Meta`` is an unknown key.

    Proves the two ``Meta`` namespaces are disjoint: ``operation`` is a mutation
    key, not a ``DjangoType`` key, so the ``DjangoType`` typo guard rejects it -
    confirming this slice added no key to ``ALLOWED_META_KEYS`` (Decision 12).
    """
    with pytest.raises(ConfigurationError, match="Unknown Meta keys"):

        class ItemTypeBad(DjangoType):
            class Meta:
                model = product_models.Item
                fields = ("id", "name")
                operation = "create"


def test_deferred_and_allowed_meta_keys_unchanged():
    """The ``DjangoType`` Meta-key sets gained no mutation key (byte-unchanged contract)."""
    from django_strawberry_framework.types.base import (
        ALLOWED_META_KEYS,
        DEFERRED_META_KEYS,
    )

    for mutation_key in (
        "operation",
        "input_class",
        "partial_input_class",
        "permission_classes",
    ):
        assert mutation_key not in ALLOWED_META_KEYS
        assert mutation_key not in DEFERRED_META_KEYS


# ---------------------------------------------------------------------------
# Public export
# ---------------------------------------------------------------------------


def test_django_mutation_and_permission_are_public_exports():
    """``DjangoMutation`` + ``DjangoModelPermission`` are root exports in ``__all__``."""
    assert django_strawberry_framework.DjangoMutation is DjangoMutation
    assert DjangoMutationFromPackage is DjangoMutation
    assert django_strawberry_framework.DjangoModelPermission is DjangoModelPermission
    assert DjangoModelPermissionFromPackage is DjangoModelPermission
    assert "DjangoMutation" in django_strawberry_framework.__all__
    assert "DjangoModelPermission" in django_strawberry_framework.__all__


def test_meta_fields_bare_string_raises():
    """A bare-string ``Meta.fields`` (would iterate as characters) raises at class creation."""
    with pytest.raises(ConfigurationError, match="not a bare string"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                fields = "name"


def test_meta_permission_classes_non_iterable_raises():
    """A non-iterable ``Meta.permission_classes`` (an int) raises via the ``list()`` guard.

    A bare ``str`` / ``bytes`` / class is caught by the explicit ``isinstance`` guard;
    any *other* non-iterable (here an ``int``) trips the ``list(value)`` ``TypeError``
    branch instead, surfacing the same fail-loud ``ConfigurationError`` at class creation.
    """
    with pytest.raises(ConfigurationError, match="must be a sequence of"):

        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                permission_classes = 5


def test_bind_skips_relation_lock_for_non_relay_target():
    """The relation-type-lock skips a relation whose target type is NOT Relay-Node.

    The AR-M2 relation-type-lock only guards a Relay-Node relation's ``GlobalID`` core
    and container shape against a consumer ``input_class`` override. When the FK
    target's ``DjangoType`` is a plain (non-Node) type, the generated ``<field>_id`` is
    a raw pk with no GlobalID visibility contract to defeat, so the lock skips it and
    the consumer ``input_class`` merges with the raw-pk remainder. Products' relation
    targets are all Relay-Node, so this skip branch is earned with a non-Node pair here.
    """

    class NonNodeCategoryType(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")

    class NonNodeItemType(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")

    @strawberry.input
    class CustomItemInput:
        name: str = strawberry.field(description="custom")

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = CustomItemInput

    finalize_django_types()

    from django_strawberry_framework.mutations.inputs import _materialized_names

    merged = _materialized_names["ItemInput"]
    assert CreateItem._input_class is merged
    field_names = {field.python_name for field in merged.__strawberry_definition__.fields}
    assert {"name", "category_id"} <= field_names


# ---------------------------------------------------------------------------
# No-model-flavor-regression: the new seams default to today's model behavior
# (spec-038 Slice 2 / DoD item 6). The 036-surface generalization relocated the
# validation body into ``_validate_meta`` and added ``build_input`` /
# ``input_type_name`` / ``input_module_path`` / ``resolve_*`` seams; these pin
# that the MODEL flavor's behavior is byte-identical to before.
# ---------------------------------------------------------------------------


def test_validate_meta_is_the_relocated_classmethod_seam():
    """The metaclass validates via the ``_validate_meta`` classmethod seam (relocated body).

    The former module-level ``_validate_mutation_meta`` is gone; the validation is
    now ``DjangoMutation._validate_meta``. A model mutation still validates exactly
    as before (a representative case re-pinned), and the seam is a classmethod a
    subclass can override (the form flavor does).
    """
    from django_strawberry_framework.mutations import sets as mutation_sets

    assert not hasattr(mutation_sets, "_validate_mutation_meta")
    assert "_validate_meta" in vars(DjangoMutation)

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    # The relocated body produces the same validated snapshot as before.
    assert CreateItem._mutation_meta.model is product_models.Item
    assert CreateItem._mutation_meta.operation == "create"
    # The net-new form_class slot is None on the model flavor (no regression).
    assert CreateItem._mutation_meta.form_class is None


def test_model_flavor_input_seams_produce_today_defaults():
    """``build_input`` / ``input_type_name`` / ``input_module_path`` default to model behavior.

    The seams exist and, on a plain ``DjangoMutation``, produce the model-column
    input materialized in ``mutations.inputs`` under the canonical ``<Model>Input``
    name - the exact 036 behavior, just reached through the overridable seam.
    """
    from django_strawberry_framework.mutations.inputs import (
        _materialized_names,
        editable_input_fields,
    )

    _declare_products_primaries()

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    # input_module_path defaults to the mutations.inputs namespace.
    assert CreateItem.input_module_path == INPUTS_MODULE_PATH
    # input_type_name returns the canonical model-input name (full shape).
    assert CreateItem.input_type_name(CreateItem._mutation_meta) == "ItemInput"

    finalize_django_types()

    # build_input (via the bind) materialized the model-column input into
    # mutations.inputs under the canonical name (the 036 default).
    assert "ItemInput" in _materialized_names
    materialized = _materialized_names["ItemInput"]
    assert CreateItem._input_class is materialized
    # The input carries the model's editable columns (name + category_id), proving
    # it is the model-column input, not a form-derived one.
    field_names = {f.python_name for f in materialized.__strawberry_definition__.fields}
    editable = {f.name for f in editable_input_fields(product_models.Item)}
    assert "name" in field_names
    assert "category_id" in field_names  # FK -> <field>_id scheme
    assert "name" in editable


def test_model_flavor_resolve_seams_delegate_to_resolver_entry_points():
    """``resolve_sync`` / ``resolve_async`` default to the model resolver entry points.

    The seams delegate to ``mutations/resolvers.py::resolve_mutation_sync`` /
    ``resolve_mutation_async`` (today's model dispatch), so the model resolver path
    is unchanged when Slice 3 rewires ``fields.py::_resolve`` to call them.
    """
    assert "resolve_sync" in vars(DjangoMutation)
    assert "resolve_async" in vars(DjangoMutation)
    from django_strawberry_framework.mutations import resolvers as mutation_resolvers

    assert callable(mutation_resolvers.resolve_mutation_sync)
    assert callable(mutation_resolvers.resolve_mutation_async)


def test_make_declaration_registry_dedupes_and_rejects_post_finalize():
    """The refactored declaration-registry quad behaves as the hand-written one did.

    The ``make_declaration_registry`` factory single-sources the dedup / clear /
    post-finalize reject; a fresh registry over a disjoint list still dedupes by
    identity and rejects a declaration after finalization.
    """
    from django_strawberry_framework.mutations.sets import make_declaration_registry

    reg = make_declaration_registry("ProbeFlavor")

    class Probe:
        pass

    reg.register(Probe)
    reg.register(Probe)  # identity dedup
    assert reg.store.count(Probe) == 1
    assert reg.iter_() == (Probe,)

    reg.clear()
    assert reg.iter_() == ()

    class ItemType(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    finalize_django_types()
    with pytest.raises(ConfigurationError, match="ProbeFlavor .* after finalization"):
        reg.register(Probe)
