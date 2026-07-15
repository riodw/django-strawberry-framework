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
- the ``build_input`` create-required guard (the guard fires through ``build_input``
  at finalize when a required writable field is narrowed away on create; a
  ``get_serializer_kwargs`` override no longer waives it - ``Meta.injected_fields``
  is the only subtraction; and - the load-bearing per-declaration property - an
  injecting declaration that materializes a narrowed shape FIRST does NOT poison
  the per-shape build cache for a later non-injecting declaration over the same
  shape);
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
    DjangoMutationField,
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
    NestedSerializerConfig,
)
from django_strawberry_framework.rest_framework.inputs import (
    _materialized_names as serializer_materialized_names,
)
from django_strawberry_framework.rest_framework.sets import _validate_serializer_nested_fields


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
                permission_classes = []


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
# build_input create-required guard (Meta.injected_fields is the only subtraction)
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


def test_get_serializer_kwargs_override_no_longer_waives_create_required_guard():
    """Overriding ``get_serializer_kwargs`` does NOT waive the create-required guard (hardened).

    The old blanket waiver (``_hook_overridden`` skipping the guard) let a constructor hook
    silently own required-field coverage - the exact bypass the hardening pass removes. The
    same narrowed shape that raises without an override still raises WITH one; the sanctioned
    path is ``Meta.injected_fields`` + ``get_serializer_injected_data``.
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
            return {"context": {"extra": "x"}}

    with pytest.raises(ConfigurationError, match="confirm"):
        finalize_django_types()


def test_build_input_runs_required_guard_per_declaration():
    """An injecting declaration that builds the narrowed shape FIRST must not let a later non-injecting declaration skip the guard (Finding 5 / Decision 7).

    The serializer twin of
    ``tests/forms/test_sets.py::test_cached_build_form_input_runs_required_guard_per_declaration``.
    The per-shape build cache (``_serializer_shape_build_cache``) is keyed on the
    ``SerializerInputShape`` DESCRIPTOR - NOT on the injection state. ``build_input`` runs the
    create-required guard PER declaration, BEFORE building + deduping the shape, so a
    declaration whose ``Meta.injected_fields`` subtracts the dropped field and materializes
    the narrowed shape FIRST must not poison the cache for a later declaration over the SAME
    serializer + effective set WITHOUT the injection: the second still raises (its guard runs
    before its build, so the cached shape is irrelevant). Were the guard tied to the built
    shape instead of the declaration, the cache hit would silently skip it.

    Driven at the ``finalize_django_types()`` integration level, with BOTH declarations
    in the same build so they share the per-shape cache.
    """
    _declare_products_primaries()
    serializer_cls = _item_serializer_with_required_extra()

    # The INJECTING declaration narrows `confirm` away and (because injected_fields
    # subtracts it from the guard) materializes the narrowed `ItemSerializerInput`
    # shape first, populating the per-shape build cache.
    class InjectingCreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"
            fields = ("name", "category")
            injected_fields = ("confirm",)

        def get_serializer_injected_data(
            self,
            info,
            *,
            data,
            instance=None,
        ):
            return {"confirm": "x"}

    # A NON-injecting declaration over the SAME serializer + effective set. It
    # declares no injected_fields, so its guard must still fire - the cached
    # shape must not suppress it (guard-before-cache-lookup, per declaration).
    class GuardedCreateItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"
            fields = ("name", "category")

    with pytest.raises(ConfigurationError, match="confirm"):
        finalize_django_types()


def test_meta_injected_field_still_in_input_raises_at_class_creation():
    """An injected field still present in the generated GraphQL input fails loud (hardened).

    An injected field is server-supplied by definition; leaving it in the input would make
    the client's value and the hook's value compete for one serializer key, so the overlap
    is rejected at class creation.
    """
    with pytest.raises(ConfigurationError, match="still in the generated GraphQL input"):

        class OverlapInject(SerializerMutation):
            class Meta:
                serializer_class = _item_serializer()
                operation = "create"
                injected_fields = ("name",)  # `name` is NOT narrowed out of the input
                permission_classes = []


@pytest.mark.parametrize(
    "field",
    [serializers.CharField(read_only=True), serializers.HiddenField(default="server")],
)
def test_meta_injected_field_must_be_writable_at_class_creation(field):
    """Injected fields use the generated input's writable schema-time basis."""

    class NonWritableInjectedSerializer(serializers.ModelSerializer):
        server_value = field

        class Meta:
            model = product_models.Item
            fields = ("name", "category", "server_value")

    with pytest.raises(ConfigurationError, match="unknown or non-writable at schema time"):

        class NonWritableInjectedMutation(SerializerMutation):
            class Meta:
                serializer_class = NonWritableInjectedSerializer
                operation = "create"
                fields = ("name", "category")
                injected_fields = ("server_value",)
                permission_classes = []


def test_hidden_field_source_collision_with_client_input_raises_at_class_creation():
    """A HiddenField default cannot silently replace a client's value for the same source."""

    class HiddenCollisionSerializer(serializers.ModelSerializer):
        hidden_name = serializers.HiddenField(default="server", source="name")

        class Meta:
            model = product_models.Item
            fields = ("name", "category", "hidden_name")

    with pytest.raises(ConfigurationError, match="HiddenField"):

        class HiddenCollisionMutation(SerializerMutation):
            class Meta:
                serializer_class = HiddenCollisionSerializer
                operation = "create"
                permission_classes = []


def test_narrowed_default_field_source_collision_raises_at_class_creation():
    """A narrowed-out defaulted field remains part of DRF's validated-data write surface."""

    class DefaultCollisionSerializer(serializers.ModelSerializer):
        server_name = serializers.CharField(default="server", source="name")

        class Meta:
            model = product_models.Item
            fields = ("name", "category", "server_name")

    with pytest.raises(ConfigurationError, match="narrowed-out field defaults"):

        class DefaultCollisionMutation(SerializerMutation):
            class Meta:
                serializer_class = DefaultCollisionSerializer
                operation = "create"
                fields = ("name", "category")
                permission_classes = []


def _dup_source_serializer():
    """A serializer where `summary` (source=) and `description` feed ONE model attribute."""

    class DupSourceSer(serializers.ModelSerializer):
        summary = serializers.CharField(source="description")

        class Meta:
            model = product_models.Item
            fields = (
                "name",
                "category",
                "summary",
                "description",
            )

    return DupSourceSer


def test_duplicate_source_across_input_and_injected_raises_at_class_creation():
    """A client input field and an injected field binding ONE source fail loud (hardened).

    The name-disjointness check cannot see a ``source=`` alias: two differently-named
    fields feeding the same model attribute make DRF's ``to_internal_value``
    last-write-wins, so the injected value would silently replace the client's validated
    value. Rejected at class creation.
    """
    with pytest.raises(ConfigurationError, match="bind one serializer source"):

        class DupBoundaryMut(SerializerMutation):
            class Meta:
                serializer_class = _dup_source_serializer()
                operation = "create"
                fields = ("name", "category", "summary")
                injected_fields = ("description",)
                permission_classes = []


def test_star_source_fields_are_exempt_from_the_source_collision_guard():
    """``source="*"`` (whole-object) fields never falsely collide at class creation.

    ``"*"`` is not a model attribute two fields could compete for; the serializer
    converter separately rejects a ``source="*"`` model-column field at finalize, so the
    class-creation guard must not preempt it with a misleading collision error.
    """

    class StarSer(serializers.ModelSerializer):
        alpha = serializers.CharField(source="*")
        beta = serializers.CharField(source="*")

        class Meta:
            model = product_models.Item
            fields = (
                "name",
                "category",
                "alpha",
                "beta",
            )

    class StarMut(SerializerMutation):  # no raise: the guard skips "*"
        class Meta:
            serializer_class = StarSer
            operation = "create"
            permission_classes = []

    assert StarMut is not None


def test_duplicate_source_between_two_input_fields_raises_at_class_creation():
    """Two CLIENT input fields sharing one source are rejected too (same last-write-wins hazard)."""
    with pytest.raises(ConfigurationError, match="bind one serializer source"):

        class DupInputMut(SerializerMutation):
            class Meta:
                serializer_class = _dup_source_serializer()
                operation = "create"
                permission_classes = []


# ---------------------------------------------------------------------------
# Meta.optional_fields is the MUTATION's key (Critical-1)
# ---------------------------------------------------------------------------


def _input_fields(input_cls):
    """Return ``python_name -> StrawberryField`` for a materialized input class."""
    return {f.python_name: f for f in input_cls.__strawberry_definition__.fields}


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


# NOTE: the same-serializer hook-shape collision (two mutations over one serializer whose
# hooks return the same field names with different relation targets must finalize to
# DISTINCT descriptor-derived names, not collide on the canonical one) is now earned LIVE
# over ``/graphql/`` per the ``test_query`` live-first rule, by
# ``examples/fakeshop/test_query/test_library_api.py``
# ``::test_serializer_hook_same_serializer_different_targets_distinct_inputs_and_decode_over_http``
# (``TargetedShelfSerializer`` + two hooks pointing a shared WRITE-ONLY ``target`` at
# different models, which also pins the differentiating runtime relation decode). The former
# package-only finalize-level ``test_hook_varied_relation_targets_bind_to_distinct_input_names``
# was retired with that promotion; the surgical pure-function name derivation it leaned on
# stays unit-tested by
# ``tests/rest_framework/test_inputs.py::test_descriptor_name_distinguishes_relation_target_model``.


def test_subclass_redefining_serializer_validates_against_child_serializer():
    """A subclass redefining ``Meta.serializer_class`` validates against the CHILD serializer, not an inherited parent snapshot (spec-039 Medium).

    The metaclass assigns ``_mutation_meta`` AFTER ``_validate_meta`` runs, so during the
    child's validation ``cls._mutation_meta`` resolves up the MRO to the PARENT's
    snapshot. The default ``get_serializer_for_schema`` reading that inherited snapshot
    would discover the PARENT serializer's fields - rejecting a child-only field
    (``category``, absent from ``CategorySer``) as unknown at the child's class creation.
    Reading the OWN snapshot via ``cls.__dict__`` (``None`` until assigned) falls back to
    ``cls.Meta``, so the child validates against its OWN serializer.
    """
    _declare_products_primaries()

    class CategorySer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Category
            fields = ("name",)

    class ItemSer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class CreateCategory(SerializerMutation):
        class Meta:
            serializer_class = CategorySer
            operation = "create"

    # The subclass redefines serializer_class to ItemSer and names ``category`` - an
    # ItemSer field that is NOT a CategorySer field. Under the inherited-snapshot bug the
    # default hook would read the parent (Category) field set and reject ``category`` as
    # unknown at THIS class's creation; the fix validates against the child serializer.
    class CreateItemViaSubclass(CreateCategory):
        class Meta:
            serializer_class = ItemSer
            operation = "create"
            fields = ("name", "category")

    assert CreateItemViaSubclass._mutation_meta.serializer_class is ItemSer
    assert CreateItemViaSubclass._mutation_meta.model is product_models.Item

    finalize_django_types()
    field_names = set(_input_fields(CreateItemViaSubclass._input_class))
    assert "category_id" in field_names  # the child serializer's FK, the 036 <name>_id scheme


# ---------------------------------------------------------------------------
# Base unregressed (the model flavor seam defaults unchanged)
# ---------------------------------------------------------------------------


def test_model_flavor_base_unregressed():
    """A model-flavor ``DjangoMutation`` still validates + binds; the allowed-key set is unchanged."""
    from django_strawberry_framework import DjangoMutation
    from django_strawberry_framework.mutations.sets import _ALLOWED_MUTATION_META_KEYS

    # The model allowed-key set gained only the shared ``select_for_update``
    # (BETA-055); no serializer-only keys leaked in.
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
                "select_for_update",
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


# ---------------------------------------------------------------------------
# get_serializer_for_schema() determinism fingerprint (spec-039 rev6 #10)
# ---------------------------------------------------------------------------


def test_nondeterministic_schema_hook_raises_at_bind():
    """A ``get_serializer_for_schema()`` that DRIFTS between class validation and bind fails loud (#10)."""
    _declare_products_primaries()
    serializer_cls = _item_serializer()
    drift = {"drop": False}

    class DriftMut(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"
            permission_classes = []

        @classmethod
        def get_serializer_for_schema(cls):
            fields = dict(serializer_cls().fields)
            if drift["drop"]:
                # Drop a field ONLY on the post-validation call -> a nondeterministic shape.
                del fields["description"]
            return fields

    # Class validation captured the fingerprint WITH ``description``; now make the hook drift.
    drift["drop"] = True
    with pytest.raises(ConfigurationError, match="DIFFERENT field shape"):
        finalize_django_types()


def test_deterministic_schema_hook_binds_without_drift_error():
    """A stable ``get_serializer_for_schema()`` binds without the drift error (#10 happy path)."""
    _declare_products_primaries()
    serializer_cls = _item_serializer()

    class StableMut(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"
            permission_classes = []

        @classmethod
        def get_serializer_for_schema(cls):
            return dict(serializer_cls().fields)

    finalize_django_types()  # no raise
    assert StableMut._input_class is not None


# ---------------------------------------------------------------------------
# Meta.injected_fields explicit contract (spec-039 rev6 #2)
# ---------------------------------------------------------------------------


def test_meta_injected_fields_lets_narrowing_drop_required_field():
    """``Meta.injected_fields`` lets a narrowing drop a required field WITHOUT the blanket waiver (rev6 #2)."""
    _declare_products_primaries()
    serializer_cls = _item_serializer()  # `name` + `category` are required.

    class InjectMut(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"
            fields = ("description",)  # drops required `name` + `category`
            injected_fields = ("name", "category")
            permission_classes = []

    finalize_django_types()  # no raise: the guard subtracts the declared injected fields.
    assert InjectMut._input_class is not None


def test_narrowing_dropping_required_without_injected_still_raises():
    """Dropping a required field with NEITHER an override nor ``injected_fields`` still fails loud (rev6 #2)."""
    _declare_products_primaries()

    class BadMut(SerializerMutation):
        class Meta:
            serializer_class = _item_serializer()
            operation = "create"
            fields = ("description",)  # drops required `name` + `category`, nothing injected
            permission_classes = []

    with pytest.raises(ConfigurationError, match="drops required"):
        finalize_django_types()


def test_unknown_injected_fields_meta_key_still_rejected():
    """A typo'd ``Meta`` key adjacent to ``injected_fields`` is still rejected by the typo guard."""
    with pytest.raises(ConfigurationError, match="unknown keys"):

        class TypoMut(SerializerMutation):
            class Meta:
                serializer_class = _item_serializer()
                operation = "create"
                injected_field = ("name",)  # singular typo, not the real key
                permission_classes = []


# ---------------------------------------------------------------------------
# Meta.select_for_update opt-in row lock (spec-039 rev6 #14)
# ---------------------------------------------------------------------------


def test_meta_select_for_update_stored_on_snapshot():
    """``Meta.select_for_update = True`` is validated + stored on the snapshot (rev6 #14)."""

    class LockMut(SerializerMutation):
        class Meta:
            serializer_class = _item_serializer()
            operation = "update"
            select_for_update = True
            permission_classes = []

    assert LockMut._mutation_meta.select_for_update is True


def test_meta_select_for_update_defaults_true():
    """``Meta.select_for_update`` defaults to ``True`` when unset (BETA-055: locked writes).

    The default flipped from opt-in (rev6 #14) to opt-out: the update/delete
    locate and relation-target checks lock through the base manager unless the
    consumer explicitly opts into weaker concurrency with ``False``.
    """

    class PlainMut(SerializerMutation):
        class Meta:
            serializer_class = _item_serializer()
            operation = "update"
            permission_classes = []

    assert PlainMut._mutation_meta.select_for_update is True


def test_meta_select_for_update_explicit_false_opts_out():
    """An explicit ``Meta.select_for_update = False`` opts into unlocked writes (BETA-055)."""

    class UnlockedMut(SerializerMutation):
        class Meta:
            serializer_class = _item_serializer()
            operation = "update"
            permission_classes = []
            select_for_update = False

    assert UnlockedMut._mutation_meta.select_for_update is False


def test_meta_select_for_update_non_bool_raises():
    """A non-bool ``Meta.select_for_update`` fails loud at class creation (rev6 #14)."""
    with pytest.raises(ConfigurationError, match="select_for_update must be a bool"):

        class BadMut(SerializerMutation):
            class Meta:
                serializer_class = _item_serializer()
                operation = "update"
                select_for_update = "yes"
                permission_classes = []


def test_meta_injected_fields_unknown_name_raises_at_class_creation():
    """``Meta.injected_fields`` naming a field not in the schema map fails loud at class creation (rev6 rev2 P1)."""
    with pytest.raises(ConfigurationError, match="schema-time field map"):

        class BadInject(SerializerMutation):
            class Meta:
                serializer_class = _item_serializer()
                operation = "create"
                injected_fields = ("nonexistent_field",)
                permission_classes = []


def test_input_type_name_runs_the_determinism_guard():
    """``input_type_name`` reads the hook through the SAME guarded path; a drifted hook raises (rev6 rev2 P2)."""
    _declare_products_primaries()
    serializer_cls = _item_serializer()
    drift = {"drop": False}

    class DriftNameMut(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"
            permission_classes = []

        @classmethod
        def get_serializer_for_schema(cls):
            fields = dict(serializer_cls().fields)
            if drift["drop"]:
                del fields["description"]
            return fields

    # The class-validation fingerprint captured the full shape; now make the hook drift.
    drift["drop"] = True
    with pytest.raises(ConfigurationError, match="DIFFERENT field shape"):
        DriftNameMut.input_type_name(DriftNameMut._mutation_meta)


def test_input_type_name_reads_bound_name_after_finalize():
    """After bind, ``input_type_name`` reuses the materialized name stashed by ``build_input``."""
    _declare_products_primaries()
    serializer_cls = _item_serializer()

    class CreateItemViaSerializer(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = "create"
            permission_classes = []

    finalize_django_types()

    bound_name = CreateItemViaSerializer.__dict__["_input_type_name"]
    assert bound_name == CreateItemViaSerializer._input_class.__name__
    assert (
        CreateItemViaSerializer.input_type_name(CreateItemViaSerializer._mutation_meta)
        == bound_name
    )


# ---------------------------------------------------------------------------
# Meta.nested_fields validation (spec-039 rev6 #17)
# ---------------------------------------------------------------------------


def _category_field_map(*, with_create=True, with_items=True):
    """Return a ``CategorySerializer``'s bound field map (nested ``items`` list) + the class."""

    class ItemInline(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name",)

    class CategorySer(serializers.ModelSerializer):
        if with_items:
            items = ItemInline(many=True)

        class Meta:
            model = product_models.Category
            fields = ("name", "items") if with_items else ("name",)

        if with_create:

            def create(self, validated_data):
                return None

    return CategorySer, dict(CategorySer().fields)


def test_validate_nested_fields_none_returns_none():
    """An unset ``Meta.nested_fields`` normalizes to ``None`` (rev6 #17)."""
    serializer_cls, field_map = _category_field_map()
    assert (
        _validate_serializer_nested_fields("M", serializer_cls, "create", field_map, None) is None
    )


def test_validate_nested_fields_rejects_non_mapping():
    """A non-mapping ``Meta.nested_fields`` fails loud at class creation (rev6 #17)."""
    serializer_cls, field_map = _category_field_map()
    with pytest.raises(ConfigurationError, match="must be a mapping"):
        _validate_serializer_nested_fields("M", serializer_cls, "create", field_map, ["items"])


def test_validate_nested_fields_rejects_non_config_value():
    """A value that is not a ``NestedSerializerConfig`` fails loud (rev6 #17)."""
    serializer_cls, field_map = _category_field_map()
    with pytest.raises(ConfigurationError, match="must be a NestedSerializerConfig"):
        _validate_serializer_nested_fields(
            "M",
            serializer_cls,
            "create",
            field_map,
            {"items": object()},
        )


def test_validate_nested_fields_rejects_unknown_field():
    """A ``nested_fields`` key not in the serializer's field map fails loud (rev6 #17)."""
    serializer_cls, field_map = _category_field_map()
    with pytest.raises(ConfigurationError, match="not in the serializer's schema-time field map"):
        _validate_serializer_nested_fields(
            "M",
            serializer_cls,
            "create",
            field_map,
            {"ghost": NestedSerializerConfig()},
        )


def test_validate_nested_fields_rejects_non_nested_field():
    """A ``nested_fields`` key naming a scalar (not a nested serializer) fails loud (rev6 #17)."""
    serializer_cls, field_map = _category_field_map()
    with pytest.raises(ConfigurationError, match="not a nested serializer"):
        _validate_serializer_nested_fields(
            "M",
            serializer_cls,
            "create",
            field_map,
            {"name": NestedSerializerConfig()},
        )


def test_validate_nested_fields_requires_create_override():
    """``nested_fields`` on a create op requires the serializer to override ``create()`` (rev6 #17)."""
    serializer_cls, field_map = _category_field_map(with_create=False)
    with pytest.raises(ConfigurationError, match="does not override create"):
        _validate_serializer_nested_fields(
            "M",
            serializer_cls,
            "create",
            field_map,
            {"items": NestedSerializerConfig()},
        )


def test_validate_nested_fields_requires_update_override_for_update_op():
    """``nested_fields`` on an update op requires the serializer to override ``update()`` (rev6 #17)."""
    serializer_cls, field_map = _category_field_map(with_create=True)
    # The class overrides create() but NOT update(); an update op needs update().
    with pytest.raises(ConfigurationError, match="does not override update"):
        _validate_serializer_nested_fields(
            "M",
            serializer_cls,
            "update",
            field_map,
            {"items": NestedSerializerConfig()},
        )


def test_validate_nested_fields_valid_returns_normalized_dict():
    """A valid ``Meta.nested_fields`` normalizes to a plain dict (rev6 #17)."""
    serializer_cls, field_map = _category_field_map()
    config = NestedSerializerConfig()
    result = _validate_serializer_nested_fields(
        "M",
        serializer_cls,
        "create",
        field_map,
        {"items": config},
    )
    assert result == {"items": config}


def test_nested_fields_stored_on_snapshot_and_builds():
    """A declared ``Meta.nested_fields`` is stored on the snapshot and the mutation finalizes (rev6 #17)."""

    class ItemInline(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name",)

    class CategoryWithItems(serializers.ModelSerializer):
        items = ItemInline(many=True)

        class Meta:
            model = product_models.Category
            fields = ("name", "items")

        def create(self, validated_data):
            return None

    class CategoryT(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class CreateCategoryWithItems(SerializerMutation):
        class Meta:
            serializer_class = CategoryWithItems
            operation = "create"
            nested_fields = {"items": NestedSerializerConfig()}
            permission_classes = []

    snapshot = CreateCategoryWithItems._mutation_meta
    assert set(snapshot.nested_fields) == {"items"}

    import strawberry as _sb

    from django_strawberry_framework import DjangoMutationField

    @_sb.type
    class Query:
        @_sb.field
        def ping(self) -> int:
            return 1

    @_sb.type
    class Mutation:
        create_category_with_items = DjangoMutationField(CreateCategoryWithItems)

    del CategoryT
    finalize_django_types()
    sdl = str(_sb.Schema(query=Query, mutation=Mutation))
    # The nested input type is generated (canonical nested name, ItemInline full shape).
    assert "ItemInlineInput" in sdl


def test_nested_hidden_field_source_collision_raises_at_class_creation():
    """An opted-in nested serializer cannot hide a last-write-wins source collision."""

    class ItemInline(serializers.ModelSerializer):
        hidden_name = serializers.HiddenField(default="server", source="name")

        class Meta:
            model = product_models.Item
            fields = ("name", "hidden_name")

    class CategoryWithItems(serializers.ModelSerializer):
        items = ItemInline(many=True)

        class Meta:
            model = product_models.Category
            fields = ("name", "items")

        def create(self, validated_data):
            return None

    with pytest.raises(ConfigurationError, match="nested serializer path 'items'"):

        class CreateCategoryWithCollision(SerializerMutation):
            class Meta:
                serializer_class = CategoryWithItems
                operation = "create"
                nested_fields = {"items": NestedSerializerConfig()}
                permission_classes = []


def test_read_only_nested_serializer_narrowed_away_does_not_break_class_creation():
    """A read-only nested serializer whose fields raise, narrowed away, still validates + binds (rev6 #17 review P1).

    The fingerprint is scoped to the writable + narrowed (effective) set, so a read-only nested
    OUTPUT serializer (whose ``get_fields()`` raises if read) that is narrowed away is never
    descended into - class creation AND the phase-2.5 bind both succeed.
    """
    import strawberry as _sb

    from django_strawberry_framework import DjangoMutationField

    class RaisingChild(serializers.Serializer):
        def get_fields(self):
            raise RuntimeError("child fields should not be read")

    class ShelfWithReadOnlyChild(serializers.ModelSerializer):
        child = RaisingChild(read_only=True)

        class Meta:
            model = product_models.Item
            fields = ("name", "child")

    class ItemT(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    class CreateItemNarrowed(SerializerMutation):
        class Meta:
            serializer_class = ShelfWithReadOnlyChild
            operation = "create"
            fields = ("name",)  # narrows away the read-only nested child
            permission_classes = []

    @_sb.type
    class Query:
        @_sb.field
        def ping(self) -> int:
            return 1

    @_sb.type
    class Mutation:
        create_item_narrowed = DjangoMutationField(CreateItemNarrowed)

    del ItemT
    # No RuntimeError at class creation OR at the bind (the fingerprint never read child.fields).
    finalize_django_types()
    sdl = str(_sb.Schema(query=Query, mutation=Mutation))
    assert "createItemNarrowed" in sdl


def test_narrowed_away_writable_nested_not_fingerprinted():
    """A WRITABLE nested serializer narrowed away by ``Meta.fields`` is not fingerprinted (rev6 #17 review P1).

    Because the fingerprint is over the EFFECTIVE (narrowed) set, a writable nested field whose
    ``.fields`` cannot materialize no-arg does not break class creation when it is narrowed away.
    """

    class RaisingWritableChild(serializers.Serializer):
        def get_fields(self):
            raise RuntimeError("cannot read no-arg")

    class ItemWithWritableChild(serializers.ModelSerializer):
        child = RaisingWritableChild()

        class Meta:
            model = product_models.Item
            fields = ("name", "child")

    # ``child`` is narrowed away, so the effective-scoped fingerprint never reads its .fields.
    class CreateItemNarrowedWritable(SerializerMutation):
        class Meta:
            serializer_class = ItemWithWritableChild
            operation = "create"
            fields = ("name",)
            permission_classes = []

    # Class creation succeeded (no RuntimeError); the snapshot carries the effective fingerprint.
    assert CreateItemNarrowedWritable._mutation_meta.schema_fingerprint is not None


def test_unopted_writable_nested_reports_opt_in_error_not_materialization():
    """An UNOPTED writable nested child that raises from ``get_fields()`` reports the opt-in error (rev6 #17 review P2).

    The prior fingerprint descended into EVERY writable nested serializer, so an unopted,
    context-sensitive child raised a misleading "opted in via Meta.nested_fields..."
    materialization error at class validation - shadowing the canonical opt-in error. The
    fingerprint is now gated on ``Meta.nested_fields`` (the opt-in tree): an unopted nested field
    is a shallow marker, so class creation succeeds and the phase-2.5 bind's field walk raises the
    canonical opt-in error instead.
    """
    _declare_products_primaries()

    class RaisingChild(serializers.Serializer):
        def get_fields(self):
            raise RuntimeError("unopted nested child fields must not be read")

    class ItemWithUnoptedChild(serializers.ModelSerializer):
        child = RaisingChild()

        class Meta:
            model = product_models.Item
            fields = ("name", "child")

    # No Meta.nested_fields -> the nested child is NOT opted in.
    class CreateItemUnopted(SerializerMutation):
        class Meta:
            serializer_class = ItemWithUnoptedChild
            operation = "create"
            permission_classes = []

    # Class creation succeeded: the fingerprint recorded a shallow marker (no RuntimeError, no
    # "Could not materialize..." wrap), and the snapshot carries the fingerprint.
    assert CreateItemUnopted._mutation_meta.schema_fingerprint is not None
    # The phase-2.5 bind's field walk raises the CANONICAL opt-in error (not the materialization wrap).
    with pytest.raises(ConfigurationError, match="opt-in only"):
        finalize_django_types()


# ---------------------------------------------------------------------------
# Per-pass shape-build-cache clear (spec-039 P1.3 - the serializer twin of the
# model / form per-pass clears)
# ---------------------------------------------------------------------------


def _nested_category_serializer():
    """A ``Category`` ``ModelSerializer`` with a nested writable ``items`` list + a ``create`` override."""

    class ItemInline(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name",)

    class CategoryWithItems(serializers.ModelSerializer):
        items = ItemInline(many=True)

        class Meta:
            model = product_models.Category
            fields = ("name", "items")

        def create(self, validated_data):
            return None

    return CategoryWithItems


def test_nested_input_materialized_in_ledger_after_finalize():
    """Pre-bind name discovery cannot make a nested input disappear during finalization."""
    _declare_products_primaries()

    class CreateCategory(SerializerMutation):
        class Meta:
            serializer_class = _nested_category_serializer()
            operation = "create"
            nested_fields = {"items": NestedSerializerConfig()}
            permission_classes = []

    # The field factory discovers the name before finalization and primes both the
    # shape cache and the nested-input ledger.
    @strawberry.type
    class Mutation:
        create_category = DjangoMutationField(CreateCategory)

    assert "ItemInlineInput" in serializer_materialized_names
    prebind_nested = serializer_materialized_names["ItemInlineInput"]
    finalize_django_types()

    top_name = CreateCategory._input_class.__name__
    assert top_name in serializer_materialized_names
    assert "ItemInlineInput" in serializer_materialized_names
    assert serializer_materialized_names["ItemInlineInput"] is not prebind_nested
    assert Mutation.__strawberry_definition__ is not None


def test_nested_input_rematerialized_after_recover_in_place(monkeypatch):
    """A failed finalization cannot leave a cache that suppresses nested re-emission."""
    _declare_products_primaries()  # Category + Item primaries (Category needed for the parent).

    class CreateCategory(SerializerMutation):
        class Meta:
            serializer_class = _nested_category_serializer()
            operation = "create"
            nested_fields = {"items": NestedSerializerConfig()}
            permission_classes = []

    def _boom() -> None:
        raise RuntimeError("injected post-bind finalization failure")

    monkeypatch.setattr("django_strawberry_framework.types.finalizer._bind_ordersets", _boom)
    with pytest.raises(RuntimeError, match="injected post-bind"):
        finalize_django_types()
    assert "ItemInlineInput" in serializer_materialized_names
    first_nested = serializer_materialized_names["ItemInlineInput"]
    assert registry.is_finalized() is False

    monkeypatch.undo()
    finalize_django_types()

    assert registry.is_finalized() is True
    assert "ItemInlineInput" in serializer_materialized_names
    assert serializer_materialized_names["ItemInlineInput"] is not first_nested
