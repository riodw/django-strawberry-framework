"""``SerializerMutation`` base, ``Meta`` validation, and the phase-2.5 bind (spec-039 Slice 2).

Covers ``django_strawberry_framework/rest_framework/sets.py``:

- the serializer ``Meta`` validation matrix at class creation (missing /
  wrong-type ``serializer_class``; a plain ``serializers.Serializer`` with no
  model rejected; a ``ModelSerializer`` with no ``Meta.model`` rejected;
  ``operation = "delete"`` rejected; missing ``operation`` rejected;
  ``serializer_class`` accepted as a known key; ``fields`` + ``exclude`` both set;
  bare-string ``optional_fields``; unknown key);
- the public surface (``from django_strawberry_framework import SerializerMutation``
  resolves through the root ``__getattr__``; NOT in ``__all__`` - F1);
- declaration registration (the serializer flavor rides the ``DjangoMutation``
  registry, NOT the plain-form registry; the abstract base registers nowhere;
  late declaration after finalize rejected);
- the phase-2.5 bind (the ``bind_mutations()`` path - the serializer-derived input
  materializes into ``rest_framework.inputs``, the model-backed ``<Name>Payload``
  into ``mutations.inputs``);
- the retry-idempotence seam lock (the serializer ledger clears in the pre-bind
  reset via ``register_subsystem_clear``, not a per-pass clear);
- the ``build_input`` create-required guard + ``get_serializer_kwargs`` waiver
  (the guard fires through ``build_input`` at finalize when a required writable
  field is narrowed away on create; a ``get_serializer_kwargs`` override waives
  it; and - the load-bearing per-declaration property - a waiving declaration
  that materializes a narrowed shape FIRST does NOT poison the per-shape build
  cache for a later non-waiving declaration over the same shape);
- the no-registered-primary-type finalize error;
- the model-flavor seam defaults unchanged (the base is unregressed).

System-under-test is the base / validation / bind, run against the products
``Item`` / ``Category`` FK fixtures + package-local ``ModelSerializer`` fixtures.
Mirrors ``tests/forms/test_sets.py`` fixture posture. Build-time invalid configs
never reach a resolver, so this matrix is correctly owned here (package-internal),
not live.
"""

from __future__ import annotations

import pytest
import strawberry
from apps.products import models as product_models
from rest_framework import serializers

import django_strawberry_framework
from django_strawberry_framework import (
    DjangoModelPermission,
    DjangoType,
    SerializerMutation,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms.sets import iter_form_mutations
from django_strawberry_framework.mutations.inputs import (
    _materialized_names as mutation_materialized_names,
)
from django_strawberry_framework.mutations.sets import iter_mutations
from django_strawberry_framework.registry import registry
from django_strawberry_framework.rest_framework.inputs import (
    SERIALIZER_INPUTS_MODULE_PATH,
)
from django_strawberry_framework.rest_framework.inputs import (
    _materialized_names as serializer_materialized_names,
)


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Reset the registry (co-clearing the serializer-input ledger via the seam).

    ``registry.clear()`` is wired this slice to iterate the
    ``register_subsystem_clear`` list, which includes the serializer input ledger,
    plus the serializer shape-cache reset. The products ``DjangoType``s register on
    import, so the clear is needed before/after.
    """
    registry.clear()
    yield
    registry.clear()


def _item_serializer():
    """A ``ModelSerializer`` over products ``Item`` (the serializer-flavor fixture)."""

    class ItemSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = (
                "name",
                "description",
                "category",
                "is_private",
            )

    return ItemSerializer


def _declare_products_primaries():
    """Register primary ``DjangoType``s for ``Item`` + ``Category`` (Relay-shaped)."""

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


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


def test_serializer_mutation_resolves_through_root_getattr():
    """``SerializerMutation`` resolves by name through the root ``__getattr__`` (DRF present)."""
    from django_strawberry_framework.rest_framework.sets import (
        SerializerMutation as SerializerMutationFromSets,
    )

    assert django_strawberry_framework.SerializerMutation is SerializerMutationFromSets


def test_serializer_mutation_not_in_all():
    """``SerializerMutation`` is NOT in ``__all__`` while DRF is soft (F1)."""
    assert "SerializerMutation" not in django_strawberry_framework.__all__


# ---------------------------------------------------------------------------
# Meta validation matrix
# ---------------------------------------------------------------------------


def test_missing_serializer_class_raises():
    """A ``SerializerMutation`` with no ``Meta.serializer_class`` raises naming the key."""
    with pytest.raises(ConfigurationError, match="declares no serializer_class"):

        class CreateItem(SerializerMutation):
            class Meta:
                operation = "create"


def test_non_serializer_value_rejected():
    """A non-``Serializer`` value on ``serializer_class`` raises the broad type gate."""

    class NotASerializer:
        pass

    with pytest.raises(ConfigurationError, match="must be a DRF .*Serializer"):

        class CreateItem(SerializerMutation):
            class Meta:
                serializer_class = NotASerializer
                operation = "create"


def test_plain_serializer_with_no_model_rejected():
    """A plain ``serializers.Serializer`` (no model) is rejected naming the ModelSerializer requirement."""

    class PlainSerializer(serializers.Serializer):
        name = serializers.CharField()

    with pytest.raises(ConfigurationError, match="must be a serializers.ModelSerializer"):

        class CreateThing(SerializerMutation):
            class Meta:
                serializer_class = PlainSerializer
                operation = "create"


def test_modelserializer_with_no_meta_model_rejected():
    """A ``ModelSerializer`` whose ``Meta.model`` is unset raises a clean config error, not AttributeError."""

    class NoModelSerializer(serializers.ModelSerializer):
        name = serializers.CharField()

        class Meta:
            fields = ("name",)

    with pytest.raises(ConfigurationError, match="resolves no model"):

        class CreateThing(SerializerMutation):
            class Meta:
                serializer_class = NoModelSerializer
                operation = "create"


def test_delete_operation_rejected():
    """``operation = "delete"`` is rejected via the shared non-delete message (DRF serializers do not delete)."""
    serializer_cls = _item_serializer()
    with pytest.raises(ConfigurationError, match="operation must be one of"):

        class DeleteItem(SerializerMutation):
            class Meta:
                serializer_class = serializer_cls
                operation = "delete"


def test_missing_operation_rejected():
    """A missing ``operation`` is rejected (``None`` invalid)."""
    serializer_cls = _item_serializer()
    with pytest.raises(ConfigurationError, match="operation must be one of"):

        class CreateItem(SerializerMutation):
            class Meta:
                serializer_class = serializer_cls


def test_serializer_class_accepted_as_known_key():
    """A valid ``SerializerMutation`` declaration does not raise; the snapshot is stamped."""
    serializer_cls = _item_serializer()

    class CreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"

    assert CreateItem._mutation_meta.serializer_class is serializer_cls
    assert CreateItem._mutation_meta.model is product_models.Item
    assert CreateItem._mutation_meta.operation == "create"


def test_unset_permission_classes_keeps_model_permission_default():
    """An unset ``permission_classes`` resolves to ``[DjangoModelPermission]`` (the 036 write-auth seam)."""
    serializer_cls = _item_serializer()

    class CreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"

    assert CreateItem._mutation_meta.permission_classes == [DjangoModelPermission]


def test_permission_classes_accepted_as_known_key():
    """An explicit ``permission_classes`` is preserved (the allowed key is kept, Decision 11)."""
    serializer_cls = _item_serializer()

    class CreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"
            permission_classes = []

    assert CreateItem._mutation_meta.permission_classes == []


def test_fields_and_exclude_both_raises():
    """Declaring both ``fields`` and ``exclude`` raises."""
    serializer_cls = _item_serializer()
    with pytest.raises(ConfigurationError, match="both `fields` and `exclude`"):

        class CreateItem(SerializerMutation):
            class Meta:
                serializer_class = serializer_cls
                operation = "create"
                fields = ("name",)
                exclude = ("description",)


def test_optional_fields_bare_string_rejected_at_class_creation():
    """A bare-string mutation ``Meta.optional_fields`` (incl. ``"__all__"``) is rejected at class creation.

    ``optional_fields`` is the MUTATION's ``Meta`` key (spec-039 Critical-1 - NOT the
    serializer's own ``Meta``); it is normalized at class creation (a bare string would
    iterate as characters; there is no ``"__all__"`` sentinel for field SELECTORS), so
    the reject is immediate, not deferred to finalize.
    """
    serializer_cls = _item_serializer()
    with pytest.raises(ConfigurationError, match="bare string|optional_fields"):

        class CreateItem(SerializerMutation):
            class Meta:
                serializer_class = serializer_cls
                operation = "create"
                optional_fields = "__all__"


def test_unknown_meta_key_raises():
    """A stray ``Meta`` key raises the promoted typo guard."""
    serializer_cls = _item_serializer()
    with pytest.raises(ConfigurationError, match="unknown keys"):

        class CreateItem(SerializerMutation):
            class Meta:
                serializer_class = serializer_cls
                operation = "create"
                widget = "nope"


def test_model_key_is_unknown():
    """``model`` is NOT an allowed serializer key (it dropped from the serializer allowed set)."""
    serializer_cls = _item_serializer()
    with pytest.raises(ConfigurationError, match="unknown keys"):

        class CreateItem(SerializerMutation):
            class Meta:
                serializer_class = serializer_cls
                operation = "create"
                model = product_models.Item


# ---------------------------------------------------------------------------
# Declaration registration
# ---------------------------------------------------------------------------


def test_serializer_mutation_registers_in_mutation_registry():
    """A concrete ``SerializerMutation`` rides the ``DjangoMutation`` declaration registry."""
    serializer_cls = _item_serializer()

    class CreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"

    assert CreateItem in iter_mutations()
    assert CreateItem not in iter_form_mutations()


def test_abstract_base_registers_nowhere():
    """The abstract ``SerializerMutation`` base registers nowhere."""
    assert SerializerMutation not in iter_mutations()
    assert SerializerMutation not in iter_form_mutations()


def test_late_declaration_after_finalize_raises():
    """Declaring a serializer mutation after ``finalize_django_types()`` raises naming the flavor."""

    class ItemType(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    finalize_django_types()
    with pytest.raises(ConfigurationError, match="after finalization"):

        class CreateItem(SerializerMutation):
            class Meta:
                serializer_class = _item_serializer()
                operation = "create"


# ---------------------------------------------------------------------------
# Phase-2.5 bind (the bind_mutations() path)
# ---------------------------------------------------------------------------


def test_bind_materializes_serializer_input_into_rest_framework_namespace():
    """The serializer flavor binds via ``bind_mutations()`` through the ``build_input`` seam.

    The serializer-derived input materializes into ``rest_framework.inputs`` (NOT
    ``mutations.inputs``), and the model-backed ``<Name>Payload`` materializes into
    ``mutations.inputs`` (the ``DjangoMutation`` payload path, with a ``node`` /
    ``result`` slot). The reverse-map ``_input_field_specs`` is stashed for Slice 3.
    """
    import sys

    _declare_products_primaries()
    serializer_cls = _item_serializer()

    class CreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"

    assert serializer_materialized_names == {}
    finalize_django_types()

    serializer_module = sys.modules[SERIALIZER_INPUTS_MODULE_PATH]
    # The serializer-derived input lives in rest_framework.inputs, NOT mutations.inputs.
    assert "ItemSerializerInput" in serializer_materialized_names
    assert "ItemSerializerInput" not in mutation_materialized_names
    assert CreateItem._input_class is serializer_materialized_names["ItemSerializerInput"]
    assert (
        serializer_module.ItemSerializerInput
        is serializer_materialized_names["ItemSerializerInput"]
    )

    # The payload is model-backed (rides the DjangoMutation payload path).
    assert "CreateItemPayload" in mutation_materialized_names
    assert CreateItem._payload_type_name == "CreateItemPayload"
    assert CreateItem._primary_type is not None
    payload = mutation_materialized_names["CreateItemPayload"]
    slots = {f.python_name for f in payload.__strawberry_definition__.fields}
    assert "errors" in slots
    assert "node" in slots  # Item is Relay-shaped -> node slot

    # The Slice-1 reverse map is stashed for the Slice-3 decode (non-None).
    assert CreateItem._input_field_specs is not None
    assert len(CreateItem._input_field_specs) > 0


def test_update_binds_partial_input():
    """An ``update`` serializer mutation materializes the PARTIAL-shaped input."""
    _declare_products_primaries()
    serializer_cls = _item_serializer()

    class UpdateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "update"

    finalize_django_types()
    assert "ItemSerializerPartialInput" in serializer_materialized_names
    assert UpdateItem._input_class is serializer_materialized_names["ItemSerializerPartialInput"]


def test_no_registered_primary_type_raises_at_finalize():
    """A ``SerializerMutation`` whose model has no registered ``DjangoType`` raises at finalize.

    No primary type for the model means the mutation has no type to return - the
    reused ``_resolve_primary_type`` path raises the "no registered DjangoType" /
    "no type to return" error.
    """
    serializer_cls = _item_serializer()

    class CreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"

    # No DjangoType declared for Item this build.
    with pytest.raises(ConfigurationError, match="no registered DjangoType|no type to return"):
        finalize_django_types()


# ---------------------------------------------------------------------------
# Retry-idempotence (the seam lock)
# ---------------------------------------------------------------------------


def test_bind_is_retry_idempotent_after_fixable_later_phase_failure(monkeypatch):
    """A serializer re-finalize after a fixable post-bind failure succeeds, not a masked collision.

    Locks the ``register_subsystem_clear`` seam: ``bind_mutations`` materializes
    ``ItemSerializerInput`` (the serializer ledger) before the later phases.
    Resetting the serializer ledger in ``finalize_django_types`` before the bind
    sequence - through the iterated subsystem-clear list, NOT a per-pass clear -
    makes a recover-in-place re-finalize clean instead of raising a spurious
    distinct-class collision that masks the original error.
    """
    _declare_products_primaries()
    serializer_cls = _item_serializer()

    class CreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"

    def _boom() -> None:
        raise RuntimeError("injected post-bind finalization failure")

    monkeypatch.setattr("django_strawberry_framework.types.finalizer._bind_ordersets", _boom)
    with pytest.raises(RuntimeError, match="injected post-bind"):
        finalize_django_types()
    # The serializer input IS materialized; the registry is NOT finalized.
    assert "ItemSerializerInput" in serializer_materialized_names
    assert registry.is_finalized() is False

    monkeypatch.undo()
    # The serializer ledger is cleared in the pre-bind reset (via the seam), so the
    # second finalize re-materializes cleanly with no stale-input collision.
    finalize_django_types()

    assert registry.is_finalized() is True
    assert "ItemSerializerInput" in serializer_materialized_names
    assert CreateItem._input_class is serializer_materialized_names["ItemSerializerInput"]


# ---------------------------------------------------------------------------
# build_input create-required guard + get_serializer_kwargs waiver
# ---------------------------------------------------------------------------


def _item_serializer_with_required_extra():
    """A ``ModelSerializer`` over ``Item`` with a REQUIRED writable column-less field.

    ``confirm`` has no model column, so narrowing the effective set down to model
    columns drops a still-required writable field - the create-required guard's
    trigger (the schema would compile but ``is_valid()`` could never succeed).
    """

    class ItemSerializer(serializers.ModelSerializer):
        confirm = serializers.CharField()

        class Meta:
            model = product_models.Item
            fields = ("name", "category", "confirm")

    return ItemSerializer


def test_create_required_guard_fires_through_build_input():
    """Narrowing a required writable field away on create raises at finalize via ``build_input``.

    The genuinely-new Slice-2 wiring: ``build_input``'s ``_build`` closure runs
    ``guard_create_required_serializer_fields`` (only on ``CREATE``) BEFORE the
    per-shape descriptor dedupe. Dropping the required column-less ``confirm`` via
    ``Meta.fields`` makes the guard fire.
    """
    _declare_products_primaries()
    serializer_cls = _item_serializer_with_required_extra()

    class CreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"
            fields = ("name", "category")  # drops the still-required `confirm`

    with pytest.raises(ConfigurationError, match="confirm"):
        finalize_django_types()


def test_get_serializer_kwargs_override_waives_create_required_guard():
    """A ``get_serializer_kwargs`` override WAIVES the create-required guard (it injects the value).

    ``build_input`` detects the override via ``_hook_overridden(cls,
    SerializerMutation, "get_serializer_kwargs")`` and skips the guard - the
    override is trusted to supply whatever the narrowing dropped, so the same
    narrowed shape that raised above now binds.
    """
    _declare_products_primaries()
    serializer_cls = _item_serializer_with_required_extra()

    class CreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"
            fields = ("name", "category")  # drops the still-required `confirm`

        def get_serializer_kwargs(
            self,
            info,
            *,
            data,
            instance=None,
        ):
            return {"data": {**data, "confirm": "x"}}

    # The waiver suppresses the guard: finalize binds without raising.
    finalize_django_types()
    assert CreateItem._input_class is not None


def test_build_input_runs_required_guard_per_declaration():
    """A waiving declaration that builds the narrowed shape FIRST must not let a later non-waiving declaration skip the guard (Finding 5 / Decision 7).

    The serializer twin of
    ``tests/forms/test_sets.py::test_cached_build_form_input_runs_required_guard_per_declaration``.
    The per-shape build cache (``_serializer_shape_build_cache``) is keyed on the
    ``SerializerInputShape`` DESCRIPTOR - NOT on whether the guard is waived.
    ``build_input`` runs the create-required guard PER declaration, BEFORE building +
    deduping the shape, so a WAIVING declaration (overriding ``get_serializer_kwargs``)
    that materializes the narrowed shape FIRST must not poison the cache for a later
    NON-waiving declaration over the SAME serializer + effective set: the second still
    raises (its guard runs before its build, so the cached waived shape is irrelevant).
    Were the guard tied to the built shape instead of the declaration, the cache hit
    would silently skip it.

    Driven at the ``finalize_django_types()`` integration level, with BOTH declarations
    in the same build so they share the per-shape cache.
    """
    _declare_products_primaries()
    serializer_cls = _item_serializer_with_required_extra()

    # The WAIVING declaration narrows `confirm` away and (because the override
    # waives the guard) materializes the narrowed `ItemSerializerInput` shape first,
    # populating the per-shape build cache.
    class WaivedCreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"
            fields = ("name", "category")

        def get_serializer_kwargs(
            self,
            info,
            *,
            data,
            instance=None,
        ):
            return {"data": {**data, "confirm": "x"}}

    # A NON-waiving declaration over the SAME serializer + effective set. It does
    # NOT override get_serializer_kwargs, so its guard must still fire - the cached
    # waived shape must not suppress it (guard-before-cache-lookup, per declaration).
    class GuardedCreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"
            fields = ("name", "category")

    with pytest.raises(ConfigurationError, match="confirm"):
        finalize_django_types()


# ---------------------------------------------------------------------------
# Meta.optional_fields is the MUTATION's key (Critical-1)
# ---------------------------------------------------------------------------


def _input_fields(input_cls):
    """Return ``python_name -> StrawberryField`` for a materialized input class."""
    return {f.python_name: f for f in input_cls.__strawberry_definition__.fields}


def test_mutation_optional_fields_forces_create_field_optional():
    """``Meta.optional_fields`` on the MUTATION forces a create input field optional (Critical-1)."""
    _declare_products_primaries()

    class S(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class CreateItem(SerializerMutation):
        class Meta:
            serializer_class = S
            operation = "create"
            optional_fields = ("name",)

    finalize_django_types()
    fields = _input_fields(CreateItem._input_class)
    # ``name`` (a normally-required CharField) is forced optional by the MUTATION's
    # Meta.optional_fields - it carries the UNSET (omittable) default.
    assert fields["name"].default is strawberry.UNSET


def test_serializer_meta_optional_fields_is_not_the_public_api():
    """``optional_fields`` on the SERIALIZER's own ``Meta`` is IGNORED at bind (Critical-1).

    The masking the original implementation relied on: the spec documents
    ``optional_fields`` on the MUTATION's ``Meta``, so a serializer-level key must have
    NO effect on the generated input.
    """
    _declare_products_primaries()

    class S(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")
            optional_fields = ("name",)  # the serializer's own Meta - NOT the input API

    class CreateItem(SerializerMutation):
        class Meta:
            serializer_class = S
            operation = "create"  # no optional_fields on the MUTATION

    finalize_django_types()
    fields = _input_fields(CreateItem._input_class)
    # ``name`` stays REQUIRED: the serializer-level optional_fields has no effect.
    assert fields["name"].default is not strawberry.UNSET


def test_mutation_optional_fields_unknown_name_raises_at_class_creation():
    """A mutation ``Meta.optional_fields`` naming a field not in the effective set raises (Critical-1)."""
    serializer_cls = _item_serializer()
    with pytest.raises(ConfigurationError, match="optional_fields"):

        class CreateItem(SerializerMutation):
            class Meta:
                serializer_class = serializer_cls
                operation = "create"
                optional_fields = ("does_not_exist",)


# ---------------------------------------------------------------------------
# get_serializer_for_schema() classmethod hook + descriptor identity (Critical-2)
# ---------------------------------------------------------------------------


def test_get_serializer_for_schema_classmethod_override_drives_bind():
    """A concrete ``get_serializer_for_schema()`` override drives validation + bind (Critical-2).

    ``CtxItemSerializer.get_fields()`` reads ``self.context``, so DEFAULT no-arg
    discovery raises - overriding the classmethod to return a stable, context-supplied
    field map lets BOTH class-creation validation AND the phase-2.5 bind generate the
    input, proving they consult the OVERRIDABLE classmethod (no monkeypatching of the
    module-level discovery).
    """
    _declare_products_primaries()

    class CtxItemSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def get_fields(self):
            _ = self.context["tenant"]  # KeyError under no-arg default discovery
            return super().get_fields()

    class CreateCtxItem(SerializerMutation):
        class Meta:
            serializer_class = CtxItemSerializer
            operation = "create"

        @classmethod
        def get_serializer_for_schema(cls):
            # The override supplies the context the default no-arg discovery lacks.
            return dict(CtxItemSerializer(context={"tenant": "t"}).fields)

    finalize_django_types()
    assert CreateCtxItem._input_class is not None
    field_names = set(_input_fields(CreateCtxItem._input_class))
    assert "name" in field_names
    assert "category_id" in field_names  # FK relation, the 036 <name>_id scheme


def test_distinct_optional_fields_on_one_serializer_get_distinct_inputs():
    """Two create mutations on the SAME serializer + names but different ``optional_fields`` -> DISTINCT inputs (Critical-2).

    The per-shape build cache keys on the FULL ``SerializerInputShape`` descriptor
    (which folds in ``optional_fields``), NOT a pre-build ``(class, op, names)`` tuple,
    so the second declaration does NOT reuse the first's stale cached class: it gets its
    own deterministically-named input with the correct requiredness.
    """
    _declare_products_primaries()

    class S(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class CreatePlain(SerializerMutation):
        class Meta:
            serializer_class = S
            operation = "create"

    class CreateNameOptional(SerializerMutation):
        class Meta:
            serializer_class = S
            operation = "create"
            optional_fields = ("name",)

    finalize_django_types()
    # Distinct class objects + distinct names (no stale cache reuse on a shared key).
    assert CreatePlain._input_class is not CreateNameOptional._input_class
    assert CreatePlain._input_class.__name__ != CreateNameOptional._input_class.__name__
    # And the requiredness differs: the optional_fields declaration forced `name` optional.
    plain = _input_fields(CreatePlain._input_class)["name"]
    opt = _input_fields(CreateNameOptional._input_class)["name"]
    assert plain.default is not strawberry.UNSET  # required
    assert opt.default is strawberry.UNSET  # forced optional


# ---------------------------------------------------------------------------
# Base unregressed (the model flavor seam defaults unchanged)
# ---------------------------------------------------------------------------


def test_model_flavor_base_unregressed():
    """A model-flavor ``DjangoMutation`` still validates + binds; the allowed-key set is unchanged."""
    from django_strawberry_framework import DjangoMutation
    from django_strawberry_framework.mutations.sets import _ALLOWED_MUTATION_META_KEYS

    # The model allowed-key set is byte-unchanged (no serializer keys leaked in).
    assert (
        frozenset(
            {
                "model",
                "operation",
                "input_class",
                "partial_input_class",
                "fields",
                "exclude",
                "permission_classes",
            },
        )
        == _ALLOWED_MUTATION_META_KEYS
    )

    _declare_products_primaries()

    class DeleteItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "delete"

    # The model flavor still accepts "delete" (the broader _VALID_OPERATIONS set).
    assert DeleteItem._mutation_meta.operation == "delete"
    assert DeleteItem._mutation_meta.serializer_class is None  # net-new slot left None
    finalize_django_types()
    assert registry.is_finalized() is True


def test_deferred_and_allowed_meta_keys_unchanged():
    """``types/base.py``'s ``DEFERRED_META_KEYS`` / ``ALLOWED_META_KEYS`` are untouched (Decision 6)."""
    from django_strawberry_framework.types import base as types_base

    # A serializer-mutation Meta is its OWN validation namespace; the DjangoType
    # Meta sets are not extended by this slice.
    assert "serializer_class" not in types_base.ALLOWED_META_KEYS
    assert "operation" not in types_base.ALLOWED_META_KEYS
