"""DRF-serializer-derived ``@strawberry.input`` generation substrate (spec-039 Slice 1).

Pure, finalizer-free machinery: given a DRF ``Serializer`` / ``ModelSerializer``
class + an effective field set (after ``Meta.fields`` / ``Meta.exclude``), it
builds the ``<Serializer>Input`` (create) / ``<Serializer>PartialInput`` (update)
``@strawberry.input`` classes from the serializer's SCHEMA-TIME field set. No
metaclass, no resolver, no finalizer wiring lives here - those are Slice 2 (the
``SerializerMutation`` base + the phase-2.5 bind) and Slice 3 (the resolver
pipeline). The generators here are callable and unit-testable in isolation;
Slice 2 calls them from the bind. This is exactly the role ``forms/inputs.py``
plays for the form flavor.

Generated input classes MUST become real globals of this module because
``strawberry.lazy("django_strawberry_framework.rest_framework.inputs")`` resolves
through ``module.__dict__`` (the same contract ``mutations/inputs.py`` /
``forms/inputs.py`` rely on). ``materialize_serializer_input_class`` /
``clear_serializer_input_namespace`` (from the shared
``utils/inputs.py::make_input_namespace`` trio) own that lifecycle.

The shape is the ``038`` form discipline adapted to DRF (spec-039 Decision 7):

- The input derives from the serializer's SCHEMA-TIME field set, discovered via
  the overridable ``get_serializer_for_schema()`` hook (default: no-arg
  ``serializer_class()``, read ``.fields``). DRF builds ``.fields`` LAZILY, so the
  loud-rejection guard wraps the ``.fields`` materialization, NOT the constructor
  (Decision 7: a context-requiring serializer raises at first ``.fields`` access,
  not at construction).
- ``read_only`` / ``HiddenField`` fields are dropped from the input;
  ``Meta.optional_fields`` forces a create field optional.
- Where a ``ModelSerializer`` field has a backing model column (resolved via the
  field's ``source``), the annotation routes through the read-side converters so
  the wire contract is symmetric with the read ``DjangoType``; a serializer-only
  field uses ``convert_serializer_field`` (the model-less table). The two key
  spaces (DRF ``serializers.Field`` / ``models.Field``) stay strictly separate.
- Shape identity is the ``SerializerInputShape`` DESCRIPTOR (NOT the ``036`` /
  ``038`` name-only key): the ordered tuple of each emitted field's ``(input_attr,
  GraphQL annotation, required/default state, serializer_field_name, source,
  kind)`` plus the normalized ``optional_fields`` set, so two same-name-set inputs
  that differ in requiredness (``optional_fields``) or hook-returned field specs
  get DISTINCT deterministic names, never silent reuse. The canonical
  ``<Serializer>Input`` / ``<Serializer>PartialInput`` name is reserved for the
  DEFAULT full shape (the default discovery's full field set - NOT an arbitrary
  hook-returned "full" shape, which diverges and takes a descriptor-derived name);
  any divergence takes a deterministic descriptor-derived name; identical
  descriptors dedupe, two distinct descriptors on one name raise
  ``ConfigurationError`` at materialize (for free from the ``utils/inputs.py``
  ledger).
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from rest_framework import serializers

from ..exceptions import ConfigurationError
from ..mutations.inputs import CREATE, PARTIAL
from ..registry import register_subsystem_clear
from ..utils.inputs import (
    InputFieldSpec,
    build_strawberry_input_class,
    generated_input_type_name,
    guard_dropped_required,
    iter_input_field_collisions,
    make_input_namespace,
    make_shape_build_cache,
    normalize_field_name_sequence,
    optional_input_field,
    pascalize_token,
    resolve_effective_fields,
)
from ..utils.strings import graphql_camel_name
from .serializer_converter import (
    NESTED_MULTI,
    NESTED_SINGLE,
    is_nested_serializer_field,
    nested_serializer_child,
    resolve_serializer_field,
    serializer_field_description,
)

# Module path the ``strawberry.lazy(...)`` marker references for the SERIALIZER
# input namespace; pinned as a single constant so any forward-ref and
# ``materialize_serializer_input_class`` stay in sync. A namespace distinct from
# ``mutations.inputs`` / ``forms.inputs`` so the three ``<X>Input`` families never
# share a module ``__dict__`` slot. Mirrors ``forms/inputs.py::INPUTS_MODULE_PATH``.
SERIALIZER_INPUTS_MODULE_PATH: str = "django_strawberry_framework.rest_framework.inputs"

# The serializer-input namespace lifecycle trio, single-sited via
# ``utils/inputs.py::make_input_namespace`` (spec-039 P2.2 - the one-ledger shape
# the mutation, form, and serializer flavors share). ``_materialized_names`` is the
# ``name -> input_class`` ledger ``materialize_serializer_input_class`` writes;
# ``registry.clear()`` (wired in Slice 2) routes through
# ``clear_serializer_input_namespace`` to reset it. The public ``materialize_*`` /
# ``clear_*`` names below stay thin wrappers so callers + tests address them
# unchanged.
_materialized_names, _materialize_input, _clear_input_namespace = make_input_namespace(
    SERIALIZER_INPUTS_MODULE_PATH,
    "SerializerMutation",
)


def materialize_serializer_input_class(name: str, input_cls: type) -> None:
    """Set ``input_cls`` as a real module global of ``rest_framework.inputs`` under ``name``.

    Thin family wrapper over the ``make_input_namespace`` materializer (which
    delegates to ``utils/inputs.py::materialize_generated_input_class`` pinning the
    serializer-side module path, family label, and ledger). See that helper for
    the Strawberry ``LazyType.resolve_type`` contract, the ``(name, input_cls)``
    idempotency clause (re-materializing the same class under the same name is a
    no-op, so identical descriptors dedupe), and the distinct-class collision
    raise (a second, DIFFERENT class under one name raises ``ConfigurationError``).

    Defined here; called by Slice 2's phase-2.5 bind. On a distinct-class name COLLISION the
    raised message is ENRICHED with the shape registered under ``name`` (rev6 #15's
    ``describe_serializer_input``), so a clash between two descriptor-derived shapes is
    diagnosable (which serializer / operation / fields produced the contested name).
    """
    try:
        _materialize_input(name, input_cls)
    except ConfigurationError as exc:
        debug = describe_serializer_input(name)
        if debug is None:
            raise
        raise ConfigurationError(f"{exc}\n\nShape registered under {name!r}:\n{debug}") from exc


def clear_serializer_input_namespace() -> None:
    """Reset the serializer-input ledger for a fresh build.

    Clears ``_materialized_names`` (via the ``make_input_namespace`` clear) so
    ``materialize_serializer_input_class`` re-emits on the next finalize.
    **Materialized class objects are intentionally left parked** in
    ``rest_framework.inputs.__dict__`` per the shared parked-globals lifecycle:
    the materializer overwrites the module global via ``setattr`` on the next
    finalize, so a parked class is replaced in place once the rebuild runs.
    Stripping it via ``delattr`` would break any ``strawberry.lazy(...)`` LazyType
    held by a consumer module whose autouse-reload fixture did NOT also reload the
    holder. Like ``clear_mutation_input_namespace`` (and unlike the set families'
    clear), this resets only the module-level ledger it owns - the serializer
    subsystem has no arguments-factory cache and no per-set ``_lifecycle`` binding
    state. Wired into ``registry.clear()`` in Slice 2 (spec-039). Also resets the rev6 #15
    shape debug registry (same build lifecycle).
    """
    _clear_input_namespace()
    _SERIALIZER_SHAPE_REGISTRY.clear()


# Register the serializer input-namespace clear as a canonical PRE-BIND clear
# (spec-039 P1.6 / M4 - the seam centerpiece). The row is a static STRING pair, so
# registration imports no DRF (F10); importing THIS module only ever happens with
# DRF present (it ``import``s ``rest_framework`` at module top), so the row is
# recorded exactly when the serializer subsystem has clearable state. The
# ``finalize_django_types`` pre-bind reset + ``TypeRegistry.clear()`` iterate the
# canonical list via ``_clear_if_importable``, so a DRF-ABSENT build (which never
# imports this module, never registers the row) skips the serializer clear as a
# correct no-op - the soft-dep asymmetry the seam removes.
register_subsystem_clear(SERIALIZER_INPUTS_MODULE_PATH, "clear_serializer_input_namespace")


# The maximum serializer nesting DEPTH the opt-in nested build will descend (spec-039 rev6
# #17). Recursion is already bounded by the finite, immutable ``NestedSerializerConfig`` tree
# (a consumer opts in each level EXPLICITLY, and a frozen dataclass cannot contain itself) AND
# by the on-path cycle guard (a serializer class that reappears on the recursion path fails
# loud). This numeric cap is the additional POLICY backstop: a legitimately-but-absurdly deep
# nesting (distinct serializers, no cycle) is rejected rather than silently generating a wall
# of nested input types. Generous by default; most nested write APIs are one or two deep.
_NESTED_MAX_DEPTH: int = 5


@dataclass(frozen=True)
class NestedSerializerConfig:
    """Explicit opt-in configuration for ONE nested serializer input field (spec-039 rev6 #17).

    The descriptor-keyed contract that turns the framework's default fail-loud rejection of a
    nested ``Serializer`` / ``ListSerializer`` field into a supported, RECURSIVE input:
    ``Meta.nested_fields = {"items": NestedSerializerConfig(...)}`` opts the ``items`` nested
    field in. A nested field NOT named in ``Meta.nested_fields`` still fails loud
    (``serializer_converter.py::_reject_nested_serializer``) - nesting is never implicit.

    graphene-django converts nested serializers automatically and caches the generated input by
    the serializer's CLASS NAME (conflating two shapes of one class) with little write-contract
    validation. This is the fail-loud counterpart: opt-in only, descriptor-keyed (folded into the
    ``SerializerInputShape`` identity so two nested shapes never collide on one name), recursively
    fingerprinted (a nondeterministic hook that changes a nested shape is caught), depth / cycle
    guarded, and - crucially - the framework NEVER auto-saves the nested relation: the decoded
    nested data is passed to the parent serializer's OWN ``create()`` / ``update()`` (which the
    mutation's ``Meta`` validation requires the serializer to override), so the nested write is
    the serializer author's, done correctly, inside the pipeline transaction.

    Fields (all optional):

    - ``fields`` / ``exclude`` - narrow the NESTED input's field set, validated against the
      nested serializer's writable fields by the SAME ``resolve_effective_serializer_fields``
      machinery the top level uses (mutually exclusive; an unknown / non-writable name fails
      loud). ``None`` uses the nested serializer's full writable set.
    - ``optional_fields`` - force named nested CREATE fields optional (the nested analog of the
      mutation's ``Meta.optional_fields``).
    - ``nested_fields`` - the DEEPER opt-in: a ``{field_name: NestedSerializerConfig}`` map for a
      nested serializer that itself contains a nested serializer field. This is how multi-level
      nesting opts in - each level names its own children; a deeper nested field with no covering
      entry fails loud. The immutable, finite tree bounds the recursion (with the cycle / depth
      guards as backstops).
    """

    fields: Any = None
    exclude: Any = None
    optional_fields: Any = None
    nested_fields: Mapping[str, NestedSerializerConfig] | None = None


def get_serializer_for_schema(
    serializer_class: type[serializers.BaseSerializer],
) -> dict[str, serializers.Field]:
    """Return the serializer's schema-time field dict, materializing ``.fields`` loudly.

    Default discovery (spec-039 Decision 7): construct ``serializer_class()`` with
    NO args, then read ``.fields``. DRF builds ``.fields`` LAZILY (the field map is
    assembled on first access, not at construction), so the loud-rejection guard
    wraps the ``.fields`` read, NOT the constructor: a serializer requiring
    constructor kwargs raises at ``serializer_class()``, and a serializer whose
    ``get_fields()`` reads ``self.context`` raises at ``.fields`` access - both
    surface here as a ``ConfigurationError`` pointing at the
    ``get_serializer_for_schema()`` override contract.

    A serializer whose field set varies per request must override the Slice-2
    ``get_serializer_for_schema()`` classmethod hook to return a stable,
    request-independent field map; this module-level function is the DEFAULT the
    hook delegates to. The returned dict's fields are BOUND (``field_name`` /
    ``source`` / ``source_attrs`` populated) - DRF binds them during ``.fields``
    materialization - which the converter's ``source``-axis resolution relies on.
    """
    try:
        serializer = serializer_class()
        fields = serializer.fields
    except Exception as exc:
        raise ConfigurationError(
            f"Could not materialize the schema-time field set for serializer "
            f"{serializer_class.__name__!r}: {type(exc).__name__}: {exc}. The default "
            "discovery constructs the serializer with no args and reads `.fields`; a "
            "serializer requiring constructor context or a request-dependent field set "
            "must override get_serializer_for_schema() to return a stable, "
            "request-independent field map.",
        ) from exc
    return dict(fields)


def _fingerprint_relation_target(field: serializers.Field) -> str | None:
    """Return a relation field's target model qualname for the fingerprint, or ``None``.

    Peels a ``ManyRelatedField`` to its ``child_relation`` and reads the relation's
    ``queryset.model``; a non-relation field yields ``None``.
    """
    if isinstance(field, serializers.ManyRelatedField):
        field = field.child_relation
    if isinstance(field, serializers.RelatedField):
        model = getattr(getattr(field, "queryset", None), "model", None)
        if model is not None:
            return f"{model.__module__}.{model.__qualname__}"
    return None


def _fingerprint_choices(field: serializers.Field) -> tuple[str, ...] | None:
    """Return a ``ChoiceField``'s choice VALUES for the fingerprint, else ``None``.

    The generated enum's members come from the choice VALUES (rev6 #6), so a hook that changes
    the choices changes the SDL enum - folded into the fingerprint (rev2 P2). Every
    ``ChoiceField`` (incl. ``FilePathField``, whose choices are filesystem-dynamic but stable
    within a single process between the two hook reads) is fingerprinted; a non-choice field
    yields ``None``.
    """
    if isinstance(field, serializers.ChoiceField):
        return tuple(str(value) for value in field.choices)
    return None


def _fingerprint_converter_extra(field: serializers.Field) -> str | None:
    """Return converter-affecting discriminants (``ModelField`` wrapped / ``ListField`` child), else ``None``.

    A ``ModelField``'s wrapped ``model_field`` and a ``ListField``'s ``child`` determine the
    generated annotation, so a hook that swaps them changes the SDL - folded into the fingerprint
    (rev2 P2).
    """
    if isinstance(field, serializers.ModelField):
        return type(getattr(field, "model_field", None)).__name__
    if isinstance(field, serializers.ListField):
        return type(getattr(field, "child", None)).__name__
    return None


def _fingerprint_nested(
    field: serializers.Field,
    field_name: str,
    seen: frozenset[type],
    nested_configs: Mapping[str, NestedSerializerConfig] | None,
) -> tuple[Any, ...] | None:
    """Return a fingerprint of a nested serializer field, else ``None`` (rev6 #17 / review P2).

    A nested ``Serializer`` / ``ListSerializer`` field's generated input derives from the NESTED
    serializer's fields, so a hook that changes an OPTED-IN nested shape changes the SDL - folded
    into the fingerprint recursively so the phase-2.5 drift guard is sensitive to nested changes
    too. The recursion is bounded by the visited-class ``seen`` set: a serializer class already on
    the recursion path yields a terminal cycle marker instead of recursing forever (a
    self-referential nested serializer terminates). A non-nested field yields ``None``.

    **Gated on the opt-in tree (rev6 #17 review P2).** A nested field is descended into ONLY when it
    is declared in ``nested_configs`` (this level's ``Meta.nested_fields`` / the parent
    ``NestedSerializerConfig.nested_fields``) - the SAME tree the input builder walks. A nested
    field NOT opted in produces NO nested input (nesting is opt-in only; the field walk raises the
    canonical opt-in error), so its child shape cannot affect the SDL - it records a SHALLOW marker
    (class name + many-ness) WITHOUT reading the child's ``.fields``. This matters because an
    unopted, context-sensitive nested serializer's ``get_fields()`` may raise; descending into it
    here would surface a misleading "opted in via Meta.nested_fields" materialization error at
    class validation, shadowing the canonical opt-in error the field walk would raise. The shallow
    marker still changes if the hook flips a field between nested and scalar, so drift is detected.

    Reads an OPTED-IN nested serializer's ``.fields`` lazily; one that cannot materialize its fields
    no-arg (a context-requiring nested ``get_fields()``) raises through the fingerprint, so the raw
    exception is translated to a ``ConfigurationError`` naming the hook contract rather than leaking
    (rev6 #17 review P1). Only WRITABLE nested fields ever reach here - the caller
    (``_fingerprint_field_map``) drops ``read_only`` / ``HiddenField`` fields BEFORE fingerprinting,
    so a read-only nested output field is never descended into (its ``.fields`` never read).
    """
    if not is_nested_serializer_field(field):
        return None
    child, many = nested_serializer_child(field)
    child_class = type(child)
    nested_config = nested_configs.get(field_name) if nested_configs else None
    if nested_config is None:
        # Not opted in: no nested input is built (opt-in only), so the child shape cannot affect
        # the SDL and the field walk raises the canonical opt-in error. Record a shallow marker
        # WITHOUT reading child.fields (an unopted context-sensitive child may raise) - rev6 #17 P2.
        return ("<unopted-nested>", child_class.__name__, many)
    if child_class in seen:
        return ("<cycle>", child_class.__name__, many)
    try:
        child_field_map = dict(child.fields)
    except ConfigurationError:
        raise
    except Exception as exc:  # any DRF/consumer failure -> a clear config error.
        raise ConfigurationError(
            f"Could not materialize the nested serializer {child_class.__name__!r}'s fields for the "
            f"determinism fingerprint: {type(exc).__name__}: {exc}. A nested serializer opted in via "
            "Meta.nested_fields must expose a stable, request-independent no-arg .fields (override "
            "get_serializer_for_schema() on the mutation to return a stable field map).",
        ) from exc
    child_fingerprint = _fingerprint_field_map(
        child_field_map,
        seen | {child_class},
        nested_config.nested_fields,
    )
    return (many, child_fingerprint)


def _fingerprint_field_map(
    field_map: dict[str, serializers.Field],
    seen: frozenset[type],
    nested_configs: Mapping[str, NestedSerializerConfig] | None = None,
) -> tuple[tuple[Any, ...], ...]:
    """The recursive fingerprint core (spec-039 rev6 #10 / #17 - the nested recursion).

    Captures every SDL-affecting axis per WRITABLE field (see ``serializer_schema_fingerprint``),
    plus the recursive nested fingerprint for OPTED-IN nested fields (rev6 #17). ``seen`` carries
    the serializer classes already on the recursion path so a nested cycle terminates;
    ``nested_configs`` is THIS level's opt-in tree (``Meta.nested_fields`` at the top, the parent
    ``NestedSerializerConfig.nested_fields`` deeper) - only fields it names are descended into
    (rev6 #17 review P2), so an unopted nested field's ``.fields`` is never read.

    **Scoped to the writable field set (rev6 #17 review P1).** ``read_only`` / ``HiddenField``
    fields are DROPPED - they never produce an input field at any nesting level (the input builder
    drops them too), so their nested structure cannot affect the SDL, and fingerprinting them
    would needlessly read a read-only nested serializer's ``.fields`` (a context-sensitive nested
    OUTPUT serializer's ``get_fields()`` may raise). A field flipping read-only<->writable between
    hook reads still changes the fingerprint (it appears / disappears), so drift is still detected.
    The top-level callers additionally pass the NARROWED effective map, so a nested field narrowed
    away by ``Meta.fields`` / ``Meta.exclude`` is likewise never descended into.
    """
    return tuple(
        (
            name,
            type(field).__name__,
            field.source,
            bool(getattr(field, "write_only", False)),
            bool(field.required),
            bool(getattr(field, "allow_null", False)),
            _fingerprint_relation_target(field),
            serializer_field_description(field),
            _fingerprint_choices(field),
            _fingerprint_converter_extra(field),
            _fingerprint_nested(field, name, seen, nested_configs),
        )
        for name, field in field_map.items()
        if not field.read_only and not isinstance(field, serializers.HiddenField)
    )


def serializer_schema_fingerprint(
    field_map: dict[str, serializers.Field],
    *,
    nested_configs: Mapping[str, NestedSerializerConfig] | None = None,
) -> tuple[tuple[Any, ...], ...]:
    """Return a stable, request-independent fingerprint of a schema-time field map (spec-039 rev6 #10 / #17).

    ``get_serializer_for_schema()`` must return a STABLE, request-independent field shape (the
    input is generated once at finalization, BEFORE any request), but the hook is called at
    class validation AND again at the phase-2.5 bind - a NONDETERMINISTIC hook could validate
    one shape and bind another. This captures EVERY axis the generated input / SDL / reverse map
    depends on, so the bind can recompute it and raise if the hook DRIFTED (turning the spec's
    stable-shape promise into an enforced contract, rev2 P2): each WRITABLE field's name, class,
    source, write flag, required, allow_null, relation target model, the description inputs
    (``help_text`` + the constraint summary - rev6 #9), the enumerable choice members (rev6 #6),
    the converter discriminants (``ModelField`` wrapped field / ``ListField`` child), and - for an
    OPTED-IN nested serializer field - a RECURSIVE fingerprint of the nested serializer's own field
    map (rev6 #17, bounded by an on-path cycle guard).

    **Gated on the opt-in tree (rev6 #17 review P2).** ``nested_configs`` is the mutation's
    ``Meta.nested_fields`` map - the SAME opt-in tree the input builder walks. Only nested fields it
    names are descended into; an unopted nested field records a shallow marker WITHOUT reading its
    ``.fields`` (nesting is opt-in only, so it produces no nested input and the field walk raises the
    canonical opt-in error - descending here would surface a misleading materialization error that
    shadows it). Callers pass ``Meta.nested_fields`` so class-validation and the bind fingerprint the
    identical opt-in structure.

    **Scoped to the writable set (rev6 #17 review P1).** ``read_only`` / ``HiddenField`` fields are
    dropped (they never produce an input), so this must be fed the SAME field set the input build
    uses: the callers pass the NARROWED effective map (post ``Meta.fields`` / ``Meta.exclude``), and
    ``_fingerprint_field_map`` drops read-only / hidden at every nesting level - so a read-only or
    narrowed-away nested serializer (whose ``.fields`` may not even be materializable no-arg) is
    never descended into. Deterministic + hashable; the ordered tuple preserves field order (which
    drives the descriptor identity).
    """
    return _fingerprint_field_map(field_map, frozenset(), nested_configs)


def _serializer_meta_value(serializer_class: type[serializers.BaseSerializer], name: str) -> Any:
    """Return ``serializer_class.Meta.<name>`` if declared, else ``None``.

    DRF serializers carry their own ``Meta`` (``model`` / ``fields`` / ``exclude``);
    the package reads only the backing ``model`` from it (the narrowing /
    ``optional_fields`` keys are the MUTATION's ``Meta``, not the serializer's -
    spec-039 Critical-1). A serializer with no ``Meta`` (a bare ``Serializer``)
    yields ``None`` for every key.
    """
    meta = getattr(serializer_class, "Meta", None)
    return getattr(meta, name, None)


def _serializer_model(serializer_class: type[serializers.BaseSerializer]) -> Any:
    """Return the ``ModelSerializer``'s ``Meta.model``, or ``None`` for a plain serializer.

    The backing model is what the converter resolves a field's ``source`` against
    for the read-side ``models.Field``-keyed converters. A plain ``Serializer``
    (no ``Meta.model``) routes every field through the model-less path.
    """
    return _serializer_meta_value(serializer_class, "model")


def resolve_effective_serializer_fields(
    serializer_class: type[serializers.BaseSerializer],
    *,
    fields: Any = None,
    exclude: Any = None,
    field_map: dict[str, serializers.Field] | None = None,
) -> dict[str, serializers.Field]:
    """Return the effective ``{name: serializers.Field}`` dict after dropping + narrowing.

    Builds the input field set (spec-039 Decision 7):

    1. discover the schema-time field set - the caller-supplied ``field_map`` (the
       ``SerializerMutation.get_serializer_for_schema()`` classmethod hook's result,
       threaded so the bind consults the OVERRIDABLE hook once rather than each
       helper re-instantiating the serializer), else the default module-level
       ``get_serializer_for_schema`` discovery when called in isolation;
    2. DROP ``read_only`` and ``HiddenField`` fields (graphene's
       ``fields_for_serializer(is_input=True)`` parity - they are not input
       fields);
    3. normalize + fail-loud ``Meta.fields`` / ``Meta.exclude`` (mutually
       exclusive; bare-string incl. ``"__all__"`` / duplicate rejection via the shared
       ``normalize_field_name_sequence(flavor="SerializerMutation")`` - called directly,
       no per-flavor wrapper, spec-039 P2.7; an unknown name raises);
    4. an empty effective set raises (the ``036`` / ``038`` empty-input guard).

    ``Meta.fields`` / ``Meta.exclude`` are BOTH validated against the WRITABLE field set
    (after the read-only / ``HiddenField`` drop) - so naming a ``read_only`` (or
    ``HiddenField``) field in EITHER ``fields`` or ``exclude`` is an unknown-or-non-writable
    error: the dropped field is simply not in the writable set the narrowing is checked
    against. Excluding a read-only field is NOT a silent no-op - a read-only field is never
    an input field, so neither selecting nor excluding it is meaningful, and both fail loud.
    """
    discovered = get_serializer_for_schema(serializer_class) if field_map is None else field_map
    # Drop read-only + HiddenField: neither is an input field. ``read_only``
    # covers explicit ``read_only=True`` fields; ``HiddenField`` is read_only=False
    # but never accepts client input (it injects a fixed value), so it is dropped
    # by class too. The narrowing spine + the pinned error wording are single-sited
    # in ``utils/inputs.py::resolve_effective_fields`` (spec-039 M4), shared with the
    # form flavor; this wrapper supplies the WRITABLE basis + the serializer message
    # knobs so the read-only drop stays intrinsic to the serializer flavor.
    writable = {
        name: field
        for name, field in discovered.items()
        if not field.read_only and not isinstance(field, serializers.HiddenField)
    }
    return resolve_effective_fields(
        writable,
        fields=fields,
        exclude=exclude,
        subject=f"SerializerMutation for {serializer_class.__name__}",
        seq_flavor="SerializerMutation",
        unknown_noun="unknown or non-writable serializer field(s)",
        empty_message=(
            f"SerializerMutation input for {serializer_class.__name__} has no fields; "
            "Meta.fields / Meta.exclude narrowed the writable serializer field set to empty "
            "(or the serializer declares no writable fields). A serializer input must define "
            "at least one field."
        ),
    )


def resolve_optional_fields(
    serializer_class: type[serializers.BaseSerializer],
    optional_fields: Any,
    effective_field_names: tuple[str, ...],
) -> frozenset[str]:
    """Return the normalized ``optional_fields`` set (create-only requiredness override).

    The mutation's ``Meta.optional_fields`` (spec-039 Decision 7 / Critical-1 - the
    PUBLIC key lives on ``SerializerMutation.Meta``, NOT the serializer's own
    ``Meta``) forces the named create fields optional regardless of
    ``field.required``. ``optional_fields`` is the consumer value (or the
    ``_ValidatedMutationMeta``-stored normalized tuple); it is normalized + fail-loud
    via the shared ``normalize_field_name_sequence(flavor="SerializerMutation")`` (called
    directly, no per-flavor wrapper - spec-039 P2.7) (a bare string incl. ``"__all__"`` -
    no ``"__all__"`` sentinel for field SELECTORS - and a duplicate are rejected),
    then an unknown name (not in the effective field set) raises. ``None`` (unset)
    yields the empty set.
    """
    names = normalize_field_name_sequence(
        optional_fields,
        label="optional_fields",
        flavor="SerializerMutation",
    )
    if names is None:
        return frozenset()
    unknown = [name for name in names if name not in set(effective_field_names)]
    if unknown:
        raise ConfigurationError(
            f"SerializerMutation for {serializer_class.__name__} declares `optional_fields` "
            f"naming field(s) not in the effective input set: {sorted(unknown)!r}.",
        )
    return frozenset(names)


def resolve_injected_field_specs(
    serializer_class: type[serializers.BaseSerializer],
    field_map: dict[str, serializers.Field],
    injected_fields: Any,
) -> list[InputFieldSpec]:
    """Resolve the schema-time ``InputFieldSpec`` for each ``Meta.injected_fields`` name (rev6 rev2 P1).

    ``Meta.injected_fields`` names required schema-time fields a ``get_serializer_kwargs``
    override supplies (they are NARROWED OUT of the generated input, so their specs are NOT in
    ``_input_field_specs``). This resolves their schema-time specs from the SAME field map the
    input build used, so the Slice-3 resolver can hold each injected field to the SAME
    present / writable / source / kind / relation-model runtime-agreement contract an
    input-exposed field gets - proving the runtime serializer will actually validate + save the
    injected value, not merely that its key is present in ``data``. ``None`` / empty yields
    ``[]``. Each name is already validated to exist in ``field_map`` at class creation; resolving
    an unsupported injected field here fails loud (the same fail-loud the input walk applies).
    """
    if not injected_fields:
        return []
    model = _serializer_model(serializer_class)
    provisional_name = f"{serializer_class.__name__}Input"
    specs: list[InputFieldSpec] = []
    for name in injected_fields:
        _python_attr, _annotation, spec = resolve_serializer_field(
            field_map[name],
            model,
            provisional_name,
        )
        specs.append(spec)
    return specs


@dataclass(frozen=True)
class SerializerInputShape:
    """The single derived identity of a generated serializer-input shape (spec-039 Decision 7).

    The descriptor identity (NOT the ``036`` / ``038`` name-only ``(class, op,
    frozenset(names))`` key, which is insufficient here for two reasons: (1)
    ``optional_fields`` changes requiredness without changing the name set, and (2)
    the schema-time hook can return same-named fields with different
    classes/``source``/kind). Bundles every value that derives from the shape so
    the generator, the bind cache, and the materialize collision check read ONE
    source of truth:

    - ``serializer_class`` / ``operation_kind`` - the declaration identity + the
      ``Input`` / ``PartialInput`` suffix.
    - ``field_specs`` - the ordered tuple of each emitted field's reverse-map
      ``InputFieldSpec`` (input_attr / graphql_name / target_name / kind / source).
    - ``annotations`` - the ordered tuple of each emitted field's stringified EMITTED
      annotation (post-nullable-widening - M2 / High), so two hook-returned shapes with
      the SAME names but a DIFFERENT emitted annotation diverge: a ``CharField`` vs an
      ``IntegerField`` (different base type) under one name, AND a ``required=True,
      allow_null=False`` (``str``) vs ``required=True, allow_null=True`` (``str | None``)
      field under one name (same base type, different generated nullability).
    - ``required_state`` - the ordered tuple of each emitted field's effective
      requiredness (``field.required`` minus ``optional_fields`` for create; all
      ``False`` for partial), so an ``optional_fields`` difference diverges.
    - ``optional_fields`` - the normalized create ``optional_fields`` set.

    ``type_name`` - the generated GraphQL/class name (canonical
    ``<Serializer>Input`` for the DEFAULT full shape only - a hook-returned "full"
    shape that differs from the default discovery takes a deterministic
    descriptor-derived name, never the canonical one - and a descriptor-derived name
    for any narrowed / ``optional_fields`` divergence). ``cache_key`` is the
    descriptor itself (it is frozen + hashable), the ``make_shape_build_cache`` key
    the Slice-2 bind dedupes on.
    """

    serializer_class: type[serializers.BaseSerializer]
    operation_kind: str
    field_specs: tuple[InputFieldSpec, ...]
    annotations: tuple[str, ...]
    required_state: tuple[bool, ...]
    optional_fields: frozenset[str]
    type_name: str

    @property
    def cache_key(self) -> SerializerInputShape:
        """The per-shape build-cache key (the frozen descriptor is its own key)."""
        return self


# spec-039 rev6 #15: the generated-input-name -> ``SerializerInputShape`` debug registry.
# ``build_serializer_input_class`` records each shape it produces here (keyed by the generated
# type name), so ``describe_serializer_input`` can explain WHY a (deliberately opaque,
# descriptor-derived) input has its shape / name - the fields, sources, relation targets,
# requiredness, and whether the canonical name was used. Reset by ``registry.clear()`` through
# ``clear_serializer_input_namespace`` (the same lifecycle as the materialize ledger).
_SERIALIZER_SHAPE_REGISTRY: dict[str, SerializerInputShape] = {}


def describe_serializer_input(name: str) -> str | None:
    """Return a human-readable description of a generated serializer input shape (spec-039 rev6 #15).

    Given a generated input class name (e.g. a descriptor-derived
    ``NoteShelfSerializerCode...Note...Input``), returns a multi-line summary of its
    ``SerializerInputShape`` - the backing serializer, operation, per-field
    (declared name -> GraphQL name, emitted annotation, kind, source, relation target,
    requiredness), and whether the CANONICAL ``<Serializer>Input`` name was used or a
    descriptor-derived name (a narrowing / ``optional_fields`` / hook divergence). Returns
    ``None`` for an unregistered name. graphene-django's class-name cache can silently conflate
    shapes; this makes the package's stronger descriptor-based identity easy to inspect (and is
    folded into the materialize-collision error message so a name clash is diagnosable).
    """
    shape = _SERIALIZER_SHAPE_REGISTRY.get(name)
    if shape is None:
        return None
    canonical_suffix = "PartialInput" if shape.operation_kind == PARTIAL else "Input"
    canonical_name = f"{shape.serializer_class.__name__}{canonical_suffix}"
    name_note = (
        "canonical (the DEFAULT full shape)"
        if name == canonical_name
        else "descriptor-derived (a narrowing / optional_fields / hook divergence)"
    )
    lines = [
        f"SerializerMutation input {name!r}:",
        f"  serializer: {shape.serializer_class.__module__}.{shape.serializer_class.__qualname__}",
        f"  operation: {shape.operation_kind}",
        f"  name: {name_note}",
        "  fields:",
    ]
    for spec, annotation, required in zip(
        shape.field_specs,
        shape.annotations,
        shape.required_state,
        strict=True,
    ):
        extra = ""
        if spec.source is not None:
            extra += f", source={spec.source!r}"
        if spec.related_model is not None:
            extra += f", relation_target={spec.related_model.__name__}"
        if spec.nested_specs is not None:
            # rev6 #17: name the nested input's own fields so a nested shape is inspectable
            # (the recursive reverse map, one level - deeper levels have their own registry rows).
            nested_names = ", ".join(child.target_name for child in spec.nested_specs)
            extra += f", nested_fields=[{nested_names}]"
        lines.append(
            f"    - {spec.target_name!r} -> {spec.graphql_name!r}: {annotation} "
            f"(kind={spec.kind}, required={required}{extra})",
        )
    return "\n".join(lines)


def _related_model_token(related_model: type | None) -> str:
    """Return a stable, process-independent identifier for a relation target model.

    Folded into ``_shape_token`` so two relation shapes that differ ONLY in their
    target model (same declared field name, same GraphQL id annotation - e.g. a
    ``target`` ``PrimaryKeyRelatedField`` a schema hook points at different models)
    produce DISTINCT descriptor-derived names. The descriptor cache key already
    separates them (``InputFieldSpec.related_model`` is part of the frozen
    ``field_specs`` tuple), so the generated NAME must separate them too, or two
    distinct descriptors collide on one materialized name (spec-039). ``None`` (a
    non-relation field) yields the literal ``"None"``; the module + qualname pair
    is deterministic across processes (unlike ``id()`` / the salted builtin
    ``hash``), load-bearing for the materialize-ledger dedupe.
    """
    if related_model is None:
        return "None"
    return f"{related_model.__module__}.{related_model.__qualname__}"


def _shape_token(spec: InputFieldSpec, annotation: str, required: bool) -> str:
    """Encode one emitted field's descriptor state as a collision-resistant name token.

    Reuses ``utils/inputs.py::pascalize_token`` (promoted from ``mutations/inputs.py``
    - spec-039 Md5) for the field-name component so the bare concatenation of
    per-field tokens stays uniquely decomposable (no third PascalCase encoder). The
    FULL field-spec identity the
    runtime behavior depends on is folded into the token via a stable ``hash``-free
    digest - the EMITTED annotation (post-nullable-widening, so a ``T`` vs ``T | None``
    nullability difference diverges - M2 / High), requiredness, kind, ``input_attr``,
    ``graphql_name``, ``source``, AND the relation ``related_model`` - so two same-name
    shapes that differ in ANY of those still produce DISTINCT divergent names (spec-039 -
    the descriptor identity drives the name, not just the name set; the cache key folds
    in ``related_model`` via the frozen ``field_specs``, so the name must too).

    The digest is collision-RESISTANT, not provably injective: a hash of arbitrary
    discriminants cannot be injective into a fixed-width hex string. The materialize
    ledger is the actual injectivity backstop - two distinct descriptors that hashed to
    one name would collide there as a loud ``ConfigurationError`` (never a silent reuse),
    so the contract a consumer relies on ("distinct descriptors -> distinct types, or a
    loud error") holds regardless. A wide digest just makes that ledger collision
    astronomically unlikely in practice (a large hook matrix would otherwise reject two
    otherwise-valid distinct shapes).
    """
    base = pascalize_token(spec.target_name)
    discriminant = "|".join(
        (
            annotation,
            str(required),
            spec.kind,
            spec.input_attr,
            spec.graphql_name,
            str(spec.source),
            _related_model_token(spec.related_model),
        ),
    )
    # A STABLE hex digest of the discriminant (``hashlib``, NOT the process-salted
    # builtin ``hash``, so the generated name is deterministic across processes -
    # load-bearing for the materialize-ledger dedupe). Sixteen lowercase hex chars
    # give 64 bits of discrimination (up from a 24-bit six-char digest, which a large
    # consumer schema / generated hook matrix could realistically collide); the digest
    # is appended to the single-leading-capital ``_pascalize_token`` base, and because
    # it is all-lowercase-hex with NO interior capital and NO underscore the combined
    # ``<Base><digest>`` token keeps the same single-leading-capital / underscore-free
    # shape - so the bare concatenation of per-field tokens stays uniquely decomposable
    # at uppercase boundaries and Strawberry leaves the name unchanged. The digest is
    # left as-is (lowercase): the base already supplies the single leading capital, and
    # uppercasing the digest head would introduce an interior boundary, breaking
    # decomposition. No PascalCase encoder is re-spelt here - only ``pascalize_token``
    # (imported) shapes the field token.
    digest = hashlib.sha1(discriminant.encode()).hexdigest()[:16]
    return f"{base}{digest}"


def serializer_input_type_name(
    serializer_class: type[serializers.BaseSerializer],
    operation_kind: str,
    *,
    is_full_shape: bool,
    field_specs: tuple[InputFieldSpec, ...],
    annotations: tuple[str, ...],
    required_state: tuple[bool, ...],
) -> str:
    """Return the generated input-class name for a serializer shape (spec-039 Decision 7).

    The caller sets ``is_full_shape`` True ONLY for the DEFAULT full shape (the shape
    the default module-level discovery produces with no narrowing + no
    ``optional_fields`` - NOT an arbitrary hook-returned "full" shape), which takes
    the stable ``<Serializer>Input`` / ``<Serializer>PartialInput`` name. ANY divergent
    shape (a ``Meta.fields`` / ``Meta.exclude`` narrowing, an ``optional_fields``
    override, or a schema hook returning same-named fields with different
    annotations / source / kind / relation target) takes a deterministic
    DESCRIPTOR-derived name, so two descriptors that differ get distinct names
    (dedupe via the materialize ledger) while identical descriptors produce the same
    name.

    The divergent-shape suffix is the per-field tokens concatenated, each token a
    single-leading-capital ``_pascalize_token`` of the field name plus a digest of
    its full field-spec identity (annotation / requiredness / kind / input_attr /
    graphql_name / source / related_model), so a same-name-set divergence in any of
    those still produces a distinct name.
    """
    token = "".join(
        _shape_token(spec, ann, req)
        for spec, ann, req in zip(field_specs, annotations, required_state, strict=True)
    )
    return generated_input_type_name(
        serializer_class.__name__,
        is_partial=operation_kind == PARTIAL,
        is_full_shape=is_full_shape,
        token=token,
    )


def _required_writable_field_names(
    serializer_class: type[serializers.BaseSerializer],
    *,
    field_map: dict[str, serializers.Field] | None = None,
) -> set[str]:
    """Return the names of every WRITABLE serializer field that is required-with-no-default.

    A DRF field is required-with-no-default when ``field.required`` is True (DRF
    derives ``required`` from ``required`` / ``default`` / ``read_only`` itself, so
    a field with a ``default`` reports ``required=False``). ``read_only`` /
    ``HiddenField`` fields are excluded (they are not input fields). This is the
    create-required-narrowing guard's basis. ``field_map`` is the schema-time hook's
    result threaded from the bind (else the default module discovery in isolation).
    """
    discovered = get_serializer_for_schema(serializer_class) if field_map is None else field_map
    return {
        name
        for name, field in discovered.items()
        if field.required
        and not field.read_only
        and not isinstance(field, serializers.HiddenField)
    }


def guard_create_required_serializer_fields(
    serializer_class: type[serializers.BaseSerializer],
    effective_field_names: Any,
    *,
    injected_fields: Any = None,
    field_map: dict[str, serializers.Field] | None = None,
) -> None:
    """Raise if a create narrowing drops a still-declared required writable serializer field.

    A serializer's ``is_valid()`` fails for any ``field.required`` writable field
    absent from the validated input, so a create whose effective field set (after
    ``Meta.fields`` / ``Meta.exclude``) omits a still-declared required writable
    field would compile to a schema that looks valid but can never succeed. This
    raises ``ConfigurationError`` naming the dropped required field(s), covering
    both ``Meta.fields`` and ``Meta.exclude``. ``read_only`` / ``HiddenField``
    fields are exempt (already dropped, never required input).

    **The explicit injection contract (spec-039 rev6 #2).** ``injected_fields`` names the
    fields a ``get_serializer_kwargs`` override supplies into ``data`` (``Meta.injected_fields``);
    they are SUBTRACTED from the dropped-required set, so a required field a narrowing drops
    but that is DECLARED injected does not raise, while a dropped required field NOT declared
    injected STILL raises. This replaces the old blanket "overriding ``get_serializer_kwargs``
    waives ALL required-field coverage" waiver with an auditable, per-field declaration (the
    broad waiver survives only as an explicitly-named unsafe legacy path in ``build_input``).

    Factored out so the Slice-2 bind's per-shape build cache can run it PER
    mutation DECLARATION rather than only on the first build of a given shape: the
    cache key (the ``SerializerInputShape`` descriptor) excludes the waiver / injection
    state, so a waiving mutation that materializes a shape FIRST must not suppress the guard
    for a later non-waiving mutation reusing the same cached shape. The guard is tied to the
    declaration, not the built input shape (the
    ``forms/inputs.py::guard_create_required_fields`` per-declaration precedent).
    """
    # The drop-detection (``required - effective - waived``) is single-sited in
    # ``utils/inputs.py::guard_dropped_required`` (spec-039 Md1), shared with the form
    # create guard; the serializer passes ``Meta.injected_fields`` as ``waived`` and
    # keeps its own pinned error wording.
    guard_dropped_required(
        _required_writable_field_names(serializer_class, field_map=field_map),
        effective_field_names,
        waived=injected_fields or (),
        make_error=lambda dropped: ConfigurationError(
            f"SerializerMutation create input for {serializer_class.__name__} drops required "
            f"serializer field(s) {dropped!r} via Meta.fields / Meta.exclude; the "
            "serializer can never validate without them. Keep them in the input, or declare them "
            "in Meta.injected_fields and supply them from a get_serializer_kwargs override.",
        ),
    )


def _collect_input_attr_collision_messages(
    serializer_class: type[serializers.BaseSerializer],
    field_specs: list[InputFieldSpec],
) -> list[str]:
    """Return every input-attr / GraphQL-name / writable-source collision message (spec-039 rev6 #5).

    Three ways two serializer fields collapse to one generated input field (or one
    model attr), all of which would otherwise SILENTLY drop / double-write - so all
    fail loud (the package's fail-loud contract). Formerly this RAISED on the FIRST
    collision; it now COLLECTS every collision message and returns them, so the caller
    (``_walk_serializer_fields``) can aggregate them with the per-field conversion errors
    into ONE ``ConfigurationError`` (rev6 #5 - report all actionable problems at once,
    not one-fix-rerun-per-field). The message wording is byte-unchanged, so a consumer
    (and the tests) still see the same per-collision sentence, now as one bullet in the
    aggregate:

    * ``input_attr`` clash - a relation field ``category`` remaps to input attr
      ``category_id``, so a serializer declaring BOTH a relation ``category`` AND a
      field literally named ``category_id`` produces two specs with
      ``input_attr == "category_id"``; ``build_strawberry_input_class`` would write
      the second over the first.
    * ``graphql_name`` clash - two distinct names that default-camel-case to ONE
      GraphQL name (``foo_bar`` + ``fooBar`` -> ``fooBar``; or ``category`` ->
      ``categoryId`` vs a literal ``category_id`` -> ``categoryId``). Strawberry
      would collapse the two onto one schema field. Mirrors the read-type guard
      ``types/finalizer.py::_audit_field_surface``.
    * ``source`` clash - two WRITABLE fields sharing one one-segment ``source``
      would double-write one model attr. A ``read_only`` field sharing a ``source``
      with a writable one is fine (read-only is dropped before this is reached), so
      only the writable-vs-writable collision is reported. (The DRF ``source``-collision
      arm is new - forms have no ``source`` axis.)

    The seen-dict walk + the three collision arms are single-sited in
    ``utils/inputs.py::iter_input_field_collisions`` (DRY review A3); the
    serializer flavor collects every yielded message for aggregation (the form
    raises on the first instead), with byte-stable wording via the threaded
    serializer nouns (incl. the id-like-suffix ``camel_case_note`` and the
    serializer-only ``source_of`` arm).
    """
    return list(
        iter_input_field_collisions(
            field_specs,
            subject=f"SerializerMutation for {serializer_class.__name__!r}",
            field_noun="serializer fields",
            rename_clause="Rename one,",
            name_of=lambda spec: spec.target_name,
            camel_case_note=" (or the id-like-suffix rule)",
            # The write-back source: the resolved one-segment source, or the declared
            # name when no source was given (the column a write would set).
            source_of=lambda spec: spec.source if spec.source is not None else spec.target_name,
        ),
    )


def _aggregate_field_problems(
    serializer_class: type[serializers.BaseSerializer],
    messages: list[str],
) -> ConfigurationError:
    """Build ONE ``ConfigurationError`` from all collected schema-time problems (spec-039 rev6 #5).

    A SINGLE problem is raised VERBATIM (so the precise per-field / per-collision wording -
    and every ``pytest.raises(match=...)`` substring - is preserved unchanged); TWO OR MORE
    are grouped under a header with one bullet each, so a consumer with several bad fields
    fixes them all in one pass instead of fix-one-field-rerun-discover-the-next.
    """
    if len(messages) == 1:
        return ConfigurationError(messages[0])
    bullets = "\n".join(f"  - {message}" for message in messages)
    return ConfigurationError(
        f"SerializerMutation input for {serializer_class.__name__} has "
        f"{len(messages)} schema-time problem(s):\n{bullets}",
    )


def _walk_serializer_fields(
    effective: dict[str, serializers.Field],
    model: Any,
    provisional_name: str,
    *,
    serializer_class: type[serializers.BaseSerializer],
    is_partial: bool,
    optional_fields: frozenset[str],
    nested_configs: Mapping[str, NestedSerializerConfig] | None = None,
    nested_path: tuple[type, ...] = (),
) -> tuple[list[InputFieldSpec], list[str], list[bool], list[tuple[str, Any, dict[str, Any]]]]:
    """Resolve an effective field dict to the per-field build state (spec-039).

    Returns ``(field_specs, annotation_reprs, required_state, triples)``:

    - ``field_specs`` - the ordered reverse-map ``InputFieldSpec`` per emitted field;
    - ``annotation_reprs`` - each field's EMITTED (post-nullable-widening) annotation
      ``repr`` (so the descriptor identity reflects the generated GraphQL nullability -
      ``allow_null`` widening included - M2 / High);
    - ``required_state`` - each field's effective requiredness (create honors
      ``field.required`` minus ``optional_fields``; partial forces every field
      optional - M2: requiredness is orthogonal to nullability);
    - ``triples`` - the ``build_strawberry_input_class`` ``(python_attr, annotation,
      field_kwargs)`` triples (a nullable field widens to ``T | None`` AND carries
      ``strawberry.UNSET`` so it is OMITTABLE - spec-039 M2 / H3; each also carries a
      ``description`` threaded from the DRF field's metadata - rev6 #9).

    Factored out so the canonical-name gate can re-walk the DEFAULT full shape with
    the exact same logic, rather than the name choice drifting from the build walk.

    **Aggregate diagnostics (spec-039 rev6 #5).** Every per-field conversion error
    (unsupported field, non-PK relation, missing relation-primary, dotted / star source,
    the model-backed type-override conflict) is COLLECTED rather than raised on the first,
    then combined with the input-attr / GraphQL-name / source collision messages and raised
    as ONE ``ConfigurationError`` (a bullet list when there is more than one). So a
    real serializer with several bad fields surfaces them ALL at once instead of
    fix-one-rerun-discover-the-next. A single problem is raised verbatim, so the precise
    per-field wording (and every ``pytest.raises(match=...)`` substring) is preserved.
    """
    # rev6 #17: nested op kind mirrors the top-level operation - a create builds
    # ``CREATE``-shaped nested inputs (required nested fields required), an update builds
    # ``PARTIAL``-shaped ones (all optional). Derived from ``is_partial`` so the walk needs no
    # extra operation param.
    nested_operation_kind = PARTIAL if is_partial else CREATE
    field_specs: list[InputFieldSpec] = []
    annotation_reprs: list[str] = []
    required_state: list[bool] = []
    triples: list[tuple[str, Any, dict[str, Any]]] = []
    field_errors: list[str] = []
    for name, field in effective.items():
        try:
            if is_nested_serializer_field(field) and nested_configs and name in nested_configs:
                # rev6 #17: an EXPLICITLY-opted-in nested serializer field builds a nested input
                # RECURSIVELY (never routed through ``resolve_serializer_field``, which would
                # reject it). A nested field NOT in ``nested_configs`` falls through to the
                # converter, which fails loud (nesting is opt-in only).
                python_attr, annotation, spec = _resolve_nested_field(
                    field,
                    name,
                    nested_configs[name],
                    operation_kind=nested_operation_kind,
                    nested_path=nested_path,
                )
            else:
                python_attr, annotation, spec = resolve_serializer_field(
                    field,
                    model,
                    provisional_name,
                )
        except ConfigurationError as exc:
            # rev6 #5: collect the per-field conversion error (prefixed with the field
            # name) and keep walking so the aggregate names every bad field at once.
            field_errors.append(f"{name}: {exc}")
            continue
        field_specs.append(spec)

        required = False if is_partial else (field.required and name not in optional_fields)
        required_state.append(required)

        # Nullability (M2): the annotation is widened ``T | None`` when the field is
        # ``allow_null`` OR is optional; a nullable field is ALWAYS omittable (default
        # ``UNSET``), even when DRF ``required=True`` (H3 - GraphQL cannot express
        # required-AND-nullable, so omission is allowed at coercion and the resolver
        # strips ``UNSET`` -> DRF raises its own field-keyed required error in-band). A
        # non-nullable required field gets NO default, so GraphQL enforces presence.
        # The widening tail itself is single-sited in
        # ``utils/inputs.py::optional_input_field`` (DRY review A10).
        nullable = getattr(field, "allow_null", False) or not required
        annotation, field_kwargs = optional_input_field(
            annotation,
            python_attr=python_attr,
            graphql_name=spec.graphql_name,
            widen=nullable,
        )
        # rev6 #9: thread the DRF field's help_text + a validation-constraint summary into
        # the generated input field's SDL description (documentation only - DRF still owns
        # runtime validation). Deterministic from the field, so it never varies independently
        # of the descriptor identity (identical descriptors share identical descriptions).
        description = serializer_field_description(field)
        if description is not None:
            field_kwargs["description"] = description
        # Record the EMITTED (post-widening) annotation repr - NOT the base annotation
        # (spec-039 High / M2). The descriptor identity + the name token must reflect the
        # GraphQL nullability actually generated: two same-name hook shapes differing ONLY
        # in ``allow_null`` (``required=True, allow_null=False`` -> ``T`` vs
        # ``required=True, allow_null=True`` -> ``T | None``) emit DIFFERENT nullability,
        # so their descriptors must compare UNEQUAL - else the second declaration silently
        # reuses the first's cached input class (the per-shape build cache hit), giving one
        # mutation the other's nullability. Folding the widened annotation in is what the
        # descriptor cache key + ``_shape_token`` need; ``required_state`` records
        # requiredness, which is orthogonal (it does not move with ``allow_null`` here).
        annotation_reprs.append(repr(annotation))
        triples.append((python_attr, annotation, field_kwargs))

    # rev6 #5: fold the collision messages (over the fields that DID resolve) in with the
    # per-field errors, then raise ONE aggregated ConfigurationError if anything failed.
    all_problems = field_errors + _collect_input_attr_collision_messages(
        serializer_class,
        field_specs,
    )
    if all_problems:
        raise _aggregate_field_problems(serializer_class, all_problems)
    return field_specs, annotation_reprs, required_state, triples


def _guard_nested_recursion(
    nested_class: type,
    nested_path: tuple[type, ...],
    field_name: str,
) -> None:
    """Fail loud on a nested-serializer CYCLE or excessive DEPTH (spec-039 rev6 #17).

    ``nested_path`` is the tuple of serializer classes already on the recursion path (the
    parent chain, including the serializer whose ``field_name`` field is being descended into).
    A ``nested_class`` already on the path is a CYCLE (a serializer that nests itself directly or
    transitively - recursion would never terminate); a path at or beyond ``_NESTED_MAX_DEPTH`` is
    the DEPTH cap (an absurdly deep but acyclic nesting). Both are class-creation / bind-time
    configuration errors, not silent truncation.
    """
    if nested_class in nested_path:
        raise ConfigurationError(
            f"Nested serializer field {field_name!r} re-enters {nested_class.__name__}, which is "
            "already on the nesting path (a nested-serializer cycle); the recursive input build "
            "would never terminate. Break the cycle, or drop the field from Meta.nested_fields.",
        )
    if len(nested_path) >= _NESTED_MAX_DEPTH:
        raise ConfigurationError(
            f"Nested serializer field {field_name!r} exceeds the maximum nesting depth "
            f"({_NESTED_MAX_DEPTH}); flatten the nested write or reduce Meta.nested_fields depth.",
        )


def _dedupe_and_materialize_nested(
    nested_cls: type,
    nested_shape: SerializerInputShape,
) -> tuple[type, SerializerInputShape]:
    """Dedupe a nested input on its descriptor, materialize it, return the canonical pair (rev6 #17).

    Two references to the SAME nested shape (within one build or across two top-level mutations)
    must resolve to ONE class object, or Strawberry rejects two distinct types under one GraphQL
    name. The nested build rides the SAME per-shape build cache the top level uses (keyed on the
    frozen ``SerializerInputShape`` descriptor - nested and top-level keys never collide because
    the descriptors differ), and materializes through the SAME ledger, so a genuine
    distinct-class-same-name clash (an astronomically-unlikely digest collision) still fails loud
    at materialize. Identical descriptors return the cached class; a first sighting is cached +
    materialized.
    """
    cached = _serializer_shape_build_cache.get(nested_shape.cache_key)
    if cached is not None:
        return cached
    _serializer_shape_build_cache[nested_shape.cache_key] = (nested_cls, nested_shape)
    materialize_serializer_input_class(nested_shape.type_name, nested_cls)
    return nested_cls, nested_shape


def _resolve_nested_field(
    field: serializers.Field,
    field_name: str,
    nested_config: NestedSerializerConfig,
    *,
    operation_kind: str,
    nested_path: tuple[type, ...],
) -> tuple[str, Any, InputFieldSpec]:
    """Resolve ONE opted-in nested serializer field to ``(python_attr, annotation, spec)`` (rev6 #17).

    Builds the nested input RECURSIVELY from the nested serializer's OWN bound field map (read
    off the nested serializer instance - ``.child`` for a ``many=True`` ``ListSerializer``, the
    field itself for a single nested serializer), threading the ``NestedSerializerConfig``'s
    ``fields`` / ``exclude`` / ``optional_fields`` / deeper ``nested_fields`` into the SAME
    ``build_serializer_input_class`` the top level uses. The nested input is deduped +
    materialized (so identical nested shapes share one type), and the returned
    ``InputFieldSpec`` records ``nested_specs`` (the nested input's own reverse map) so the
    Slice-3 decode recurses with the same per-field machinery. The annotation is the nested
    input class (single) or ``list[<nested input>]`` (many); the caller applies the
    required / ``allow_null`` widening. The cycle / depth guard runs BEFORE the recursion.

    **The ``source`` axis (rev6 #17 review P1).** A nested field with a DRF ``source=`` records
    the same normalized one-segment source scalar / relation fields do (``renamed =
    ChildSerializer(source="actual")`` -> ``source="actual"``), so the runtime schema/runtime
    agreement guard's source comparison matches instead of failing every invocation. A dotted
    source / ``source="*"`` has no single write-back attribute for a nested write, so it fails
    loud here (the same fail-loud source policy the model-column path applies).
    """
    child_serializer, many = nested_serializer_child(field)
    nested_class = type(child_serializer)
    _guard_nested_recursion(nested_class, nested_path, field_name)
    # rev6 #17 review P1: the source axis. A dotted / star source (source_attrs != 1 segment) has
    # no single write-back attribute for the nested write; reject it (the model-column-path policy).
    source_attrs = getattr(field, "source_attrs", None)
    if source_attrs is not None and len(source_attrs) != 1:
        raise ConfigurationError(
            f"Nested serializer field {field_name!r} declares a dotted source / source='*' "
            f"({field.source!r}); a nested write must map to a single attribute (omit source, or "
            "use a one-segment source).",
        )
    source = field.source if (field.source and field.source != field_name) else None
    nested_field_map = dict(child_serializer.fields)
    nested_cls, nested_shape = build_serializer_input_class(
        nested_class,
        operation_kind=operation_kind,
        fields=nested_config.fields,
        exclude=nested_config.exclude,
        optional_fields=nested_config.optional_fields,
        field_map=nested_field_map,
        nested_configs=nested_config.nested_fields,
        _nested_path=nested_path,
    )
    nested_cls, nested_shape = _dedupe_and_materialize_nested(nested_cls, nested_shape)
    kind = NESTED_MULTI if many else NESTED_SINGLE
    annotation: Any = list[nested_cls] if many else nested_cls
    spec = InputFieldSpec(
        input_attr=field_name,
        graphql_name=graphql_camel_name(field_name),
        target_name=field_name,
        kind=kind,
        source=source,
        related_model=None,
        nested_specs=tuple(nested_shape.field_specs),
    )
    return field_name, annotation, spec


def _validate_nested_config_keys(
    serializer_class: type[serializers.BaseSerializer],
    effective: dict[str, serializers.Field],
    nested_configs: Mapping[str, NestedSerializerConfig] | None,
) -> None:
    """Fail loud if a ``nested_fields`` key does not name an effective NESTED serializer field (rev6 #17).

    Runs at EVERY nesting level (so a typo in a deeper ``NestedSerializerConfig.nested_fields``
    fails loud, not silently ignored): each key must be in the effective input set (not narrowed
    away by ``fields`` / ``exclude``) AND be a nested ``Serializer`` / ``ListSerializer`` field -
    configuring nesting for a scalar / relation field, an excluded field, or a typo is a
    configuration error.
    """
    if not nested_configs:
        return
    for name in nested_configs:
        field = effective.get(name)
        if field is None:
            raise ConfigurationError(
                f"SerializerMutation for {serializer_class.__name__} declares nested_fields for "
                f"{name!r}, which is not in the effective input set (unknown, read-only, or "
                "narrowed away by Meta.fields / Meta.exclude).",
            )
        if not is_nested_serializer_field(field):
            raise ConfigurationError(
                f"SerializerMutation for {serializer_class.__name__} declares nested_fields for "
                f"{name!r}, but it is a {type(field).__name__}, not a nested serializer. "
                "nested_fields is only for nested Serializer / ListSerializer fields.",
            )


def _default_full_shape_identity(
    serializer_class: type[serializers.BaseSerializer],
    model: Any,
    provisional_name: str,
    *,
    is_partial: bool,
) -> tuple[tuple[InputFieldSpec, ...], tuple[str, ...], tuple[bool, ...]] | None:
    """Return the per-field identity of the DEFAULT full shape, or ``None``.

    The canonical ``<Serializer>Input`` / ``<Serializer>PartialInput`` name is reserved
    for the shape the DEFAULT module-level discovery produces with no narrowing and no
    ``optional_fields`` (spec-039). A schema hook returning a "full" shape that DIFFERS
    from this default (e.g. the same ``target`` relation pointed at a different model)
    must NOT also claim the canonical name, or two distinct descriptors collide on it at
    materialize - so the caller grants the canonical name only when the current shape's
    per-field identity equals this default identity, and a divergent shape takes a
    descriptor-derived name instead.

    Returns ``None`` when the DEFAULT full shape cannot be CONSTRUCTED for ANY reason -
    a serializer whose ``.fields`` are not materializable no-arg (REQUIRES a
    ``get_serializer_for_schema`` override), but ALSO one whose default no-arg field map
    is itself unsupported or intentionally different from the hook's (an unsupported /
    non-PK relation field, a missing relation-primary target, a dotted source, an input
    collision). The default shape exists ONLY to reserve the canonical name; when it
    cannot be built it simply does not reserve it, so a VALID hook-provided shape must
    NOT be rejected by a failure converting the default fields. EVERY step - discovery,
    the per-field walk (relation-primary lookup, unsupported-field conversion,
    dotted-source rejection), and any collision check - is therefore inside the guard, so
    such a serializer's shapes always take a descriptor-derived name (overriding mutations
    stay collision-free via the per-field token).
    """
    try:
        default_effective = resolve_effective_serializer_fields(serializer_class)
        field_specs, annotation_reprs, required_state, _triples = _walk_serializer_fields(
            default_effective,
            model,
            provisional_name,
            serializer_class=serializer_class,
            is_partial=is_partial,
            optional_fields=frozenset(),
        )
    except ConfigurationError:
        return None
    return (tuple(field_specs), tuple(annotation_reprs), tuple(required_state))


def build_serializer_input_class(
    serializer_class: type[serializers.BaseSerializer],
    *,
    operation_kind: str,
    fields: Any = None,
    exclude: Any = None,
    optional_fields: Any = None,
    field_map: dict[str, serializers.Field] | None = None,
    nested_configs: Mapping[str, NestedSerializerConfig] | None = None,
    _nested_path: tuple[type, ...] = (),
) -> tuple[type, SerializerInputShape]:
    """Build ONE ``@strawberry.input`` class from a serializer's schema-time fields.

    ``operation_kind`` is ``CREATE`` (each field's requiredness from
    ``field.required`` minus the ``optional_fields`` override) or ``PARTIAL`` (the
    update-shaped input - every field optional). ``optional_fields`` is the
    mutation's ``Meta.optional_fields`` value (spec-039 Critical-1 - the PUBLIC key
    lives on the mutation, NOT the serializer's own ``Meta``); ``field_map`` is the
    ``get_serializer_for_schema()`` hook's result threaded from the bind (else the
    default module discovery when called in isolation).

    ``nested_configs`` is the mutation's ``Meta.nested_fields`` map (spec-039 rev6 #17):
    each named nested serializer field is built RECURSIVELY into a nested input (an
    un-named nested field still fails loud). ``_nested_path`` is the internal
    recursion-path accumulator (serializer classes already descended into) for the cycle /
    depth guard; direct callers omit it.

    A nullable input field (``allow_null=True`` OR optional) widens to
    ``annotation | None`` AND carries a ``strawberry.UNSET`` default so the key is
    OMITTABLE at GraphQL coercion (spec-039 M2 / H3): a ``required=True,
    allow_null=True`` field is nullable-but-must-provide, so the GraphQL field is
    omittable (the resolver strips ``UNSET`` -> DRF sees the key MISSING and raises
    its own field-keyed required error) while still accepting an explicit ``null``.
    A non-nullable required field (``required=True, allow_null=False``) gets NO
    default, so GraphQL itself enforces presence + non-null.

    Returns ``(input_cls, shape)`` - the UNMATERIALIZED ``@strawberry.input`` class
    and the ``SerializerInputShape`` descriptor (which carries the reverse-map
    field specs + the generated name). Slice 2's phase-2.5 bind calls
    ``materialize_serializer_input_class`` to pin the class as a module global.
    Any NESTED input classes are deduped + materialized during the walk (rev6 #17).
    """
    effective = resolve_effective_serializer_fields(
        serializer_class,
        fields=fields,
        exclude=exclude,
        field_map=field_map,
    )
    # rev6 #17: fail loud NOW (at every nesting level) if a ``nested_fields`` key does not name
    # an effective nested serializer field - a typo / excluded / non-nested key is a config error.
    _validate_nested_config_keys(serializer_class, effective, nested_configs)
    optional_fields = resolve_optional_fields(serializer_class, optional_fields, tuple(effective))
    is_partial = operation_kind == PARTIAL
    if is_partial:
        # ``optional_fields`` is a NO-OP on update (spec-039 Decision 7): the partial
        # input is already all-optional, so it must not perturb the partial shape's
        # descriptor identity / name (an update mutation that sets ``optional_fields``
        # still dedupes to the canonical ``<Serializer>PartialInput``). Names were
        # validated above before this is zeroed.
        optional_fields = frozenset()
    model = _serializer_model(serializer_class)

    # The provisional type name (for the choice-enum ``<TypeName><Field>Enum``
    # build) - the canonical name; the descriptor-derived divergent name is
    # computed after the field walk (it needs the resolved specs / annotations).
    provisional_name = f"{serializer_class.__name__}{'PartialInput' if is_partial else 'Input'}"

    # The per-field walk resolves each field, threads DRF metadata into descriptions
    # (rev6 #9), and AGGREGATES every per-field conversion error + input-attr / GraphQL-name
    # / source collision into ONE ``ConfigurationError`` (rev6 #5) - the collision guard is
    # now folded into the walk (no separate call).
    field_specs, annotation_reprs, required_state, triples = _walk_serializer_fields(
        effective,
        model,
        provisional_name,
        serializer_class=serializer_class,
        is_partial=is_partial,
        optional_fields=optional_fields,
        nested_configs=nested_configs,
        nested_path=(*_nested_path, serializer_class),
    )

    # The canonical ``<Serializer>Input`` name is reserved for the DEFAULT full shape
    # ONLY (spec-039): compare this shape's per-field identity against the identity the
    # DEFAULT module-level discovery produces for the full shape. A hook returning a
    # "full" shape that DIFFERS from the default (e.g. a relation pointed at a different
    # model) must NOT also claim the canonical name, or two distinct descriptors collide
    # on it at materialize. A narrowed / ``optional_fields`` / hook-varied shape diverges
    # and takes a deterministic descriptor-derived name. (The ``not optional_fields`` /
    # ``fields is None`` / ``exclude is None`` clauses are retained so ANY explicit
    # narrowing or optional override takes a divergent name even when it happens to
    # reproduce the default identity.)
    current_identity = (tuple(field_specs), tuple(annotation_reprs), tuple(required_state))
    default_identity = _default_full_shape_identity(
        serializer_class,
        model,
        provisional_name,
        is_partial=is_partial,
    )
    is_full_shape = (
        default_identity is not None
        and current_identity == default_identity
        and not optional_fields
        and fields is None
        and exclude is None
    )
    type_name = serializer_input_type_name(
        serializer_class,
        operation_kind,
        is_full_shape=is_full_shape,
        field_specs=tuple(field_specs),
        annotations=tuple(annotation_reprs),
        required_state=tuple(required_state),
    )

    # Rebuild the triples' aliases under the FINAL type name only matters for the
    # choice-enum name; the enum is built off ``provisional_name`` during the walk,
    # which is the canonical name even for a divergent shape (the read DjangoType's
    # enum is cached per (model, field), so the name is stable regardless). No
    # rebuild needed.
    input_cls = build_strawberry_input_class(type_name, triples)
    shape = SerializerInputShape(
        serializer_class=serializer_class,
        operation_kind=operation_kind,
        field_specs=tuple(field_specs),
        annotations=tuple(annotation_reprs),
        required_state=tuple(required_state),
        optional_fields=optional_fields,
        type_name=type_name,
    )
    # rev6 #15: record the shape under its generated name for the debug registry (identical
    # descriptors overwrite harmlessly; a genuine distinct-descriptor name clash is caught by
    # the materialize ledger, whose error is then enriched with this shape's description).
    _SERIALIZER_SHAPE_REGISTRY[type_name] = shape
    return input_cls, shape


def build_serializer_inputs(
    serializer_class: type[serializers.BaseSerializer],
    *,
    fields: Any = None,
    exclude: Any = None,
    optional_fields: Any = None,
    guard_required: bool = True,
    field_map: dict[str, serializers.Field] | None = None,
    nested_configs: Mapping[str, NestedSerializerConfig] | None = None,
) -> tuple[type, SerializerInputShape, type, SerializerInputShape]:
    """Build BOTH the create + partial inputs for a serializer, with the create-required guard.

    Single entry point producing ``(<Serializer>Input, create_shape,
    <Serializer>PartialInput, partial_shape)``. The create input honors
    ``field.required`` minus ``optional_fields`` (the mutation's
    ``Meta.optional_fields`` value, spec-039 Critical-1); the partial input is
    always every-field-optional. ``field_map`` is the
    ``get_serializer_for_schema()`` hook's result threaded from the bind (else the
    default module discovery when called in isolation).

    **The create-required-narrowing guard (spec-039 Decision 7).** When
    ``guard_required`` is True, raises ``ConfigurationError`` naming any required
    writable serializer field dropped by ``Meta.fields`` / ``Meta.exclude`` (the
    serializer can never validate without it). The waiver (``guard_required=False``)
    is the ``get_serializer_kwargs`` override escape hatch (Slice 2): when the
    mutation overrides that hook to inject the values, the guard cannot know which
    fields the override supplies, so it trusts the explicit override - surfaced as
    an explicit parameter so Slice 2 can pass ``guard_required=False``, never
    hard-coded always-on.
    """
    effective = resolve_effective_serializer_fields(
        serializer_class,
        fields=fields,
        exclude=exclude,
        field_map=field_map,
    )
    if guard_required:
        guard_create_required_serializer_fields(serializer_class, effective, field_map=field_map)

    create_cls, create_shape = build_serializer_input_class(
        serializer_class,
        operation_kind=CREATE,
        fields=fields,
        exclude=exclude,
        optional_fields=optional_fields,
        field_map=field_map,
        nested_configs=nested_configs,
    )
    partial_cls, partial_shape = build_serializer_input_class(
        serializer_class,
        operation_kind=PARTIAL,
        fields=fields,
        exclude=exclude,
        optional_fields=optional_fields,
        field_map=field_map,
        nested_configs=nested_configs,
    )
    return create_cls, create_shape, partial_cls, partial_shape


# The serializer per-shape build cache plumbing (spec-039 P1.3). Authored here in
# Slice 1 (the helper + its unit test live in ``utils/inputs.py`` / ``tests/utils``);
# the CONSUMER that keys on ``SerializerInputShape`` and the ``registry.clear()``
# registration are Slice 2 (``rest_framework/sets.py``). Exposed so the Slice-2
# bind imports the ready-made ``(cache, clear)`` pair rather than re-rolling it.
_serializer_shape_build_cache, clear_serializer_shape_build_cache = make_shape_build_cache()
