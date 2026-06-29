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
from dataclasses import dataclass
from typing import Any

import strawberry
from rest_framework import serializers

from ..exceptions import ConfigurationError
from ..mutations.inputs import CREATE, PARTIAL, _pascalize_token
from ..registry import register_subsystem_clear
from ..utils.inputs import (
    InputFieldSpec,
    build_strawberry_input_class,
    make_input_namespace,
    make_shape_build_cache,
    normalize_field_name_sequence,
)
from .serializer_converter import resolve_serializer_field

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

    Defined here; called by Slice 2's phase-2.5 bind.
    """
    _materialize_input(name, input_cls)


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
    state. Wired into ``registry.clear()`` in Slice 2 (spec-039).
    """
    _clear_input_namespace()


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


def normalize_serializer_field_sequence(
    value: Any,
    *,
    label: str = "fields",
) -> tuple[str, ...] | None:
    """Return ``Meta.fields`` / ``Meta.exclude`` as a tuple of names, or ``None``.

    The serializer-flavor entry point: delegates to the shared
    ``utils/inputs.py::normalize_field_name_sequence`` with the serializer-mutation
    flavor label, so a bare string (incl. ``"__all__"``) and a duplicate name are
    rejected loudly. The field-existence basis (a name not in the serializer's
    schema-time field set) is checked separately in
    ``resolve_effective_serializer_fields``.
    """
    return normalize_field_name_sequence(value, label=label, flavor="SerializerMutation")


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
       exclusive; bare-string incl. ``"__all__"`` / duplicate rejection via
       ``normalize_serializer_field_sequence``; an unknown name raises);
    4. an empty effective set raises (the ``036`` / ``038`` empty-input guard).

    ``Meta.fields`` / ``Meta.exclude`` are validated against the WRITABLE field set
    (after the read-only drop) - so naming a ``read_only`` field in ``fields`` is an
    unknown-name error, and excluding one is a no-op (it was already dropped).
    """
    fields = normalize_serializer_field_sequence(fields, label="fields")
    exclude = normalize_serializer_field_sequence(exclude, label="exclude")
    if fields is not None and exclude is not None:
        raise ConfigurationError(
            f"SerializerMutation for {serializer_class.__name__} declares both `fields` and "
            "`exclude`; supply at most one.",
        )

    discovered = get_serializer_for_schema(serializer_class) if field_map is None else field_map
    # Drop read-only + HiddenField: neither is an input field. ``read_only``
    # covers explicit ``read_only=True`` fields; ``HiddenField`` is read_only=False
    # but never accepts client input (it injects a fixed value), so it is dropped
    # by class too.
    writable = {
        name: field
        for name, field in discovered.items()
        if not field.read_only and not isinstance(field, serializers.HiddenField)
    }

    if fields is not None:
        unknown = [name for name in fields if name not in writable]
        if unknown:
            raise ConfigurationError(
                f"SerializerMutation for {serializer_class.__name__} declares `fields` naming "
                f"unknown or non-writable serializer field(s): {sorted(unknown)!r}.",
            )
        effective = {name: writable[name] for name in fields}
    elif exclude is not None:
        unknown = [name for name in exclude if name not in writable]
        if unknown:
            raise ConfigurationError(
                f"SerializerMutation for {serializer_class.__name__} declares `exclude` naming "
                f"unknown or non-writable serializer field(s): {sorted(unknown)!r}.",
            )
        excluded = set(exclude)
        effective = {name: field for name, field in writable.items() if name not in excluded}
    else:
        effective = dict(writable)

    if not effective:
        raise ConfigurationError(
            f"SerializerMutation input for {serializer_class.__name__} has no fields; "
            "Meta.fields / Meta.exclude narrowed the writable serializer field set to empty "
            "(or the serializer declares no writable fields). A serializer input must define "
            "at least one field.",
        )
    return effective


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
    via ``normalize_serializer_field_sequence`` (a bare string incl. ``"__all__"`` -
    no ``"__all__"`` sentinel for field SELECTORS - and a duplicate are rejected),
    then an unknown name (not in the effective field set) raises. ``None`` (unset)
    yields the empty set.
    """
    names = normalize_serializer_field_sequence(optional_fields, label="optional_fields")
    if names is None:
        return frozenset()
    unknown = [name for name in names if name not in set(effective_field_names)]
    if unknown:
        raise ConfigurationError(
            f"SerializerMutation for {serializer_class.__name__} declares `optional_fields` "
            f"naming field(s) not in the effective input set: {sorted(unknown)!r}.",
        )
    return frozenset(names)


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
    - ``annotations`` - the ordered tuple of each emitted field's stringified base
      annotation, so two hook-returned shapes with the SAME names but DIFFERENT
      annotations (a ``CharField`` vs an ``IntegerField`` under one name) diverge.
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
    """Encode one emitted field's descriptor state as an injective name token.

    Reuses ``mutations/inputs.py::_pascalize_token`` (P2.3) for the field-name
    component so the bare concatenation of per-field tokens stays uniquely
    decomposable (no third PascalCase encoder). The FULL field-spec identity the
    runtime behavior depends on is folded into the token via a stable ``hash``-free
    digest - the annotation, requiredness, kind, ``input_attr``, ``graphql_name``,
    ``source``, AND the relation ``related_model`` - so two same-name shapes that
    differ in ANY of those still produce DISTINCT divergent names (spec-039 - the
    descriptor identity drives the name, not just the name set; the cache key folds
    in ``related_model`` via the frozen ``field_specs``, so the name must too).
    """
    base = _pascalize_token(spec.target_name)
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
    # A short STABLE hex digest of the discriminant (``hashlib``, NOT the
    # process-salted builtin ``hash``, so the generated name is deterministic
    # across processes - load-bearing for the materialize-ledger dedupe). Six
    # lowercase hex chars give 24 bits of discrimination; the digest is appended
    # to the single-leading-capital ``_pascalize_token`` base, and because it is
    # all-lowercase-hex with NO interior capital and NO underscore the combined
    # ``<Base><digest>`` token keeps the same single-leading-capital /
    # underscore-free shape - so the bare concatenation of per-field tokens stays
    # uniquely decomposable at uppercase boundaries and Strawberry leaves the name
    # unchanged. The digest is left as-is (lowercase): the base already supplies
    # the single leading capital, and uppercasing the digest head would introduce
    # an interior boundary, breaking decomposition. No PascalCase encoder is
    # re-spelt here - only ``_pascalize_token`` (imported) shapes the field token.
    digest = hashlib.sha1(discriminant.encode()).hexdigest()[:6]
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
    base = serializer_class.__name__
    suffix = "PartialInput" if operation_kind == PARTIAL else "Input"
    if is_full_shape:
        return f"{base}{suffix}"
    token = "".join(
        _shape_token(spec, ann, req)
        for spec, ann, req in zip(field_specs, annotations, required_state, strict=True)
    )
    return f"{base}{token}{suffix}"


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

    Factored out so the Slice-2 bind's per-shape build cache can run it PER
    mutation DECLARATION rather than only on the first build of a given shape: the
    cache key (the ``SerializerInputShape`` descriptor) excludes ``guard_required``,
    so a waiving mutation (``guard_required=False``, having overridden
    ``get_serializer_kwargs`` to inject the values) that materializes a shape FIRST
    must not suppress the guard for a later non-waiving mutation reusing the same
    cached shape. The guard is tied to the declaration, not the built input shape
    (the ``forms/inputs.py::guard_create_required_fields`` per-declaration precedent).
    """
    dropped_required = sorted(
        _required_writable_field_names(serializer_class, field_map=field_map)
        - set(effective_field_names),
    )
    if dropped_required:
        raise ConfigurationError(
            f"SerializerMutation create input for {serializer_class.__name__} drops required "
            f"serializer field(s) {dropped_required!r} via Meta.fields / Meta.exclude; the "
            "serializer can never validate without them. Keep them in the input, or override "
            "get_serializer_kwargs to supply them (which waives this guard).",
        )


def _guard_serializer_input_attr_collisions(
    serializer_class: type[serializers.BaseSerializer],
    field_specs: list[InputFieldSpec],
) -> None:
    """Raise if two serializer fields collide on input attr / GraphQL name / writable source.

    Three ways two serializer fields collapse to one generated input field (or one
    model attr), all of which would otherwise SILENTLY drop / double-write - so all
    fail loud here (the package's fail-loud contract):

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
      only the writable-vs-writable collision raises. (The DRF ``source``-collision
      arm is new - forms have no ``source`` axis.)
    """
    seen_attr: dict[str, str] = {}
    seen_graphql: dict[str, str] = {}
    seen_source: dict[str, str] = {}
    for spec in field_specs:
        prior_attr = seen_attr.get(spec.input_attr)
        if prior_attr is not None:
            raise ConfigurationError(
                f"SerializerMutation for {serializer_class.__name__!r} generates two input "
                f"fields with the same attribute {spec.input_attr!r}: serializer fields "
                f"{prior_attr!r} and {spec.target_name!r} collide (a relation field remaps to "
                "'<name>_id', clashing with a field literally named that). Rename one, or drop "
                "one via Meta.fields / Meta.exclude.",
            )
        prior_graphql = seen_graphql.get(spec.graphql_name)
        if prior_graphql is not None:
            raise ConfigurationError(
                f"SerializerMutation for {serializer_class.__name__!r} generates two input "
                f"fields with the same GraphQL name {spec.graphql_name!r}: serializer fields "
                f"{prior_graphql!r} and {spec.target_name!r} collide under default camel-casing "
                "(or the id-like-suffix rule). Rename one, or drop one via Meta.fields / "
                "Meta.exclude.",
            )
        # The write-back source: the resolved one-segment source, or the declared
        # name when no source was given (the column a write would set).
        write_source = spec.source if spec.source is not None else spec.target_name
        prior_source = seen_source.get(write_source)
        if prior_source is not None:
            raise ConfigurationError(
                f"SerializerMutation for {serializer_class.__name__!r} has two writable fields "
                f"{prior_source!r} and {spec.target_name!r} sharing one source {write_source!r}; "
                "they would double-write one model attribute. Give each a distinct source, or "
                "drop one via Meta.fields / Meta.exclude.",
            )
        seen_attr[spec.input_attr] = spec.target_name
        seen_graphql[spec.graphql_name] = spec.target_name
        seen_source[write_source] = spec.target_name


def _walk_serializer_fields(
    effective: dict[str, serializers.Field],
    model: Any,
    provisional_name: str,
    *,
    is_partial: bool,
    optional_fields: frozenset[str],
) -> tuple[list[InputFieldSpec], list[str], list[bool], list[tuple[str, Any, dict[str, Any]]]]:
    """Resolve an effective field dict to the per-field build state (spec-039).

    Returns ``(field_specs, annotation_reprs, required_state, triples)``:

    - ``field_specs`` - the ordered reverse-map ``InputFieldSpec`` per emitted field;
    - ``annotation_reprs`` - each field's BASE (non-widened) annotation ``repr``;
    - ``required_state`` - each field's effective requiredness (create honors
      ``field.required`` minus ``optional_fields``; partial forces every field
      optional - M2: requiredness is orthogonal to nullability);
    - ``triples`` - the ``build_strawberry_input_class`` ``(python_attr, annotation,
      field_kwargs)`` triples (a nullable field widens to ``T | None`` AND carries
      ``strawberry.UNSET`` so it is OMITTABLE - spec-039 M2 / H3).

    Factored out so the canonical-name gate can re-walk the DEFAULT full shape with
    the exact same logic, rather than the name choice drifting from the build walk.
    """
    field_specs: list[InputFieldSpec] = []
    annotation_reprs: list[str] = []
    required_state: list[bool] = []
    triples: list[tuple[str, Any, dict[str, Any]]] = []
    for name, field in effective.items():
        python_attr, annotation, spec = resolve_serializer_field(field, model, provisional_name)
        field_specs.append(spec)
        annotation_reprs.append(repr(annotation))

        required = False if is_partial else (field.required and name not in optional_fields)
        required_state.append(required)

        # Nullability (M2): the annotation is widened ``T | None`` when the field is
        # ``allow_null`` OR is optional; a nullable field is ALWAYS omittable (default
        # ``UNSET``), even when DRF ``required=True`` (H3 - GraphQL cannot express
        # required-AND-nullable, so omission is allowed at coercion and the resolver
        # strips ``UNSET`` -> DRF raises its own field-keyed required error in-band). A
        # non-nullable required field gets NO default, so GraphQL enforces presence.
        nullable = getattr(field, "allow_null", False) or not required
        field_kwargs: dict[str, Any] = {}
        if python_attr != spec.graphql_name:
            field_kwargs["name"] = spec.graphql_name
        if nullable:
            annotation = annotation | None
            field_kwargs["default"] = strawberry.UNSET
        triples.append((python_attr, annotation, field_kwargs))
    return field_specs, annotation_reprs, required_state, triples


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

    Returns ``None`` when the default discovery cannot run - a serializer whose
    ``.fields`` are not materializable no-arg, which REQUIRES a
    ``get_serializer_for_schema`` override. Such a serializer has no default full shape
    to reserve the canonical name, so every shape over it takes a descriptor-derived
    name (and overriding mutations stay collision-free via the per-field token).
    """
    try:
        default_effective = resolve_effective_serializer_fields(serializer_class)
    except ConfigurationError:
        return None
    field_specs, annotation_reprs, required_state, _triples = _walk_serializer_fields(
        default_effective,
        model,
        provisional_name,
        is_partial=is_partial,
        optional_fields=frozenset(),
    )
    return (tuple(field_specs), tuple(annotation_reprs), tuple(required_state))


def build_serializer_input_class(
    serializer_class: type[serializers.BaseSerializer],
    *,
    operation_kind: str,
    fields: Any = None,
    exclude: Any = None,
    optional_fields: Any = None,
    field_map: dict[str, serializers.Field] | None = None,
) -> tuple[type, SerializerInputShape]:
    """Build ONE ``@strawberry.input`` class from a serializer's schema-time fields.

    ``operation_kind`` is ``CREATE`` (each field's requiredness from
    ``field.required`` minus the ``optional_fields`` override) or ``PARTIAL`` (the
    update-shaped input - every field optional). ``optional_fields`` is the
    mutation's ``Meta.optional_fields`` value (spec-039 Critical-1 - the PUBLIC key
    lives on the mutation, NOT the serializer's own ``Meta``); ``field_map`` is the
    ``get_serializer_for_schema()`` hook's result threaded from the bind (else the
    default module discovery when called in isolation).

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
    """
    effective = resolve_effective_serializer_fields(
        serializer_class,
        fields=fields,
        exclude=exclude,
        field_map=field_map,
    )
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

    field_specs, annotation_reprs, required_state, triples = _walk_serializer_fields(
        effective,
        model,
        provisional_name,
        is_partial=is_partial,
        optional_fields=optional_fields,
    )

    _guard_serializer_input_attr_collisions(serializer_class, field_specs)

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
    return input_cls, shape


def build_serializer_inputs(
    serializer_class: type[serializers.BaseSerializer],
    *,
    fields: Any = None,
    exclude: Any = None,
    optional_fields: Any = None,
    guard_required: bool = True,
    field_map: dict[str, serializers.Field] | None = None,
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
    )
    partial_cls, partial_shape = build_serializer_input_class(
        serializer_class,
        operation_kind=PARTIAL,
        fields=fields,
        exclude=exclude,
        optional_fields=optional_fields,
        field_map=field_map,
    )
    return create_cls, create_shape, partial_cls, partial_shape


# The serializer per-shape build cache plumbing (spec-039 P1.3). Authored here in
# Slice 1 (the helper + its unit test live in ``utils/inputs.py`` / ``tests/utils``);
# the CONSUMER that keys on ``SerializerInputShape`` and the ``registry.clear()``
# registration are Slice 2 (``rest_framework/sets.py``). Exposed so the Slice-2
# bind imports the ready-made ``(cache, clear)`` pair rather than re-rolling it.
_serializer_shape_build_cache, clear_serializer_shape_build_cache = make_shape_build_cache()
