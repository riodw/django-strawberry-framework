"""Generated-input substrate shared by the filter and order set families.

The filter and order subsystems each build real Strawberry input classes as
module globals (``strawberry.lazy(...)`` resolves through ``module.__dict__``),
keep class-level factory caches, detect duplicate generated input names, and
reset stale binding state during ``registry.clear()``. spec-027 and spec-028
grew those mechanics as parallel copies; this module single-sites the NEUTRAL
machinery so a fix to the materialization ledger, the BFS collision check, or
the namespace-clear lifecycle lands once instead of being hand-mirrored (the
0.0.9 DRY pass, ``docs/feedback.md`` Major 1).

What lives here is mechanics only. Domain semantics stay at the call sites:
``filters/inputs.py`` keeps ``convert_filter_to_input_annotation`` /
``normalize_input_value`` and the operator-bag / logic-field builders;
``orders/inputs.py`` keeps ``convert_order_field_to_input_annotation`` /
``normalize_input_value`` and the ``Ordering`` enum. The two ``inputs`` modules
re-export the helpers below under their spec-named aliases (``FieldSpec`` /
``build_input_class`` / ``_camel_case`` / ``_iter_*set_subclasses``) so existing
imports and the test suite keep addressing them on the family module.

This module depends on neither family package, so both can import it without a
cycle (same contract as ``utils/connections.py``).
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Annotated, Any, ClassVar

import strawberry

from ..exceptions import ConfigurationError
from .imports import import_attr_if_importable

# ``utils/strings.py`` is the owner of ``graphql_camel_name`` (feedback P2.1);
# re-imported here (the ``as`` form marks the explicit re-export) so existing
# ``from ..utils.inputs import graphql_camel_name`` consumers keep their import
# path.
from .strings import graphql_camel_name as graphql_camel_name


@dataclass(frozen=True)
class GeneratedInputFieldSpec:
    """Per-generated-input-field metadata shared across the set families.

    Carries the three names the runtime normalizers need to map between the
    Strawberry input dataclass field, the GraphQL wire-format name, and the
    Django ORM lookup path. Re-exported as ``FieldSpec`` by both
    ``filters/inputs.py`` and ``orders/inputs.py``.
    """

    python_attr: str
    graphql_name: str
    django_source_path: str


@dataclass(frozen=True)
class InputFieldSpec:
    """Unified per-generated-input-field reverse-map record (spec-039 P2.1).

    The ``038`` ``forms/converter.py::FormInputFieldSpec`` generalized with the
    serializer-only ``source`` axis. Where ``FormInputFieldSpec`` carried a
    ``form_field_name`` (the bound form's own key), this carries the neutral
    ``target_name`` - the per-flavor write-back key the Slice 3 resolver decodes
    the generated GraphQL field back to:

    - ``input_attr`` - the generated Strawberry dataclass attr (``category_id``
      for an FK relation, ``name`` for a scalar).
    - ``graphql_name`` - the camel-cased GraphQL wire name (``categoryId``).
    - ``target_name`` - the per-flavor decode key. For the serializer flavor this
      is the DECLARED serializer field name (``category_pk``), the key a built
      ``validated_data`` payload is keyed by; for a form it would be the form
      field name. Never the ``<name>_id`` relation attr.
    - ``kind`` - one of the flavor's decode kinds (``scalar`` /
      ``relation_single`` / ``relation_multi`` / ``file``).
    - ``source`` - the serializer-only extra axis: the one-segment ``source`` the
      backing ``models.Field`` was resolved through (``category`` for a
      ``category_pk`` field declared ``source="category"``). ``None`` for a flavor
      with no ``source`` concept (forms) or a serializer field whose ``source``
      equals its declared name.
    - ``related_model`` - the Django target model a relation field decodes its
      id(s) against (``Category`` for a ``category`` / ``category_pk`` relation),
      recorded at BIND time so the Slice-3 decode never re-discovers the
      serializer's schema-time field set per request (spec-039 H4). ``None`` for a
      non-relation (``scalar`` / ``file``) field.
    - ``nested_specs`` - the serializer-only nested-serializer axis (spec-039 rev6
      #17): the ordered reverse-map ``InputFieldSpec`` tuple of the NESTED input's
      OWN fields, recorded for a ``nested_single`` / ``nested_multi`` field so the
      Slice-3 decode recurses into the nested input dataclass with the SAME
      per-field machinery (scalar / relation / file / deeper-nested) the top level
      uses. ``None`` for every non-nested field. A tuple of frozen
      ``InputFieldSpec`` is hashable, so it participates in the frozen descriptor
      identity + the per-shape build cache key like any other axis.

    The form flavor keeps its own ``FormInputFieldSpec`` (no ``source`` /
    ``nested`` axis, its suite stays byte-equivalent); the serializer reverse-map
    uses this directly (spec-039 D1 - the minimal-blast-radius unification: site
    the serializer spec here, leave the form spec untouched).
    """

    input_attr: str
    graphql_name: str
    target_name: str
    kind: str
    source: str | None = None
    related_model: type | None = None
    nested_specs: tuple[InputFieldSpec, ...] | None = None


def make_input_namespace(
    module_path: str,
    family_label: str,
) -> tuple[dict[str, type], Callable[[str, type], None], Callable[[], None]]:
    """Return the ``(ledger, materialize_fn, clear_fn)`` trio for a generated-input namespace.

    The promoted ONE-LEDGER lifecycle the mutation + form + serializer input
    modules share (spec-039 P2.2). Before spec-039 ``mutations/inputs.py`` and
    ``forms/inputs.py`` hand-mirrored the same four-part shape (a module-level
    ``_materialized_names`` dict, a ``materialize_*`` wrapper over
    ``materialize_generated_input_class``, a ``clear_*`` that calls
    ``_materialized_names.clear()``); a serializer flavor would have been the
    third copy. This single-sites it:

    - ``ledger`` - a fresh ``name -> input_class`` dict the caller stores as its
      module-level ledger (so any direct ``_materialized_names`` reference in the
      caller's tests keeps addressing the same object).
    - ``materialize_fn(name, cls)`` - pins ``cls`` as a real global of
      ``module_path`` under ``name`` via
      ``materialize_generated_input_class(..., family_label=family_label,
      ledger=ledger)``. Inherits that helper's ``(name, cls)`` idempotency clause
      and distinct-class collision raise (the finalize-time collision, named by
      ``family_label``).
    - ``clear_fn()`` - resets the ledger via ``ledger.clear()`` ONLY.

    This is deliberately the LIGHT clear shape, NOT
    ``clear_generated_input_namespace`` (which also resets an arguments-factory
    cache + per-set ``_lifecycle`` binding state): the mutation / form / serializer
    flavors derive their input fields from one declaration's field set, not a
    related-set BFS graph, so they have neither a factory cache nor per-set
    lifecycle state to reset. Materialized class objects stay PARKED in the
    module ``__dict__`` per the shared parked-globals lifecycle - ``materialize_fn``
    overwrites the global via ``setattr`` on the next finalize, so stripping it
    via ``delattr`` would break any ``strawberry.lazy(...)`` LazyType a consumer
    module still holds.
    """
    ledger: dict[str, type] = {}

    def materialize_fn(name: str, cls: type) -> None:
        materialize_generated_input_class(
            name,
            cls,
            module_path=module_path,
            family_label=family_label,
            ledger=ledger,
        )

    def clear_fn() -> None:
        ledger.clear()

    return ledger, materialize_fn, clear_fn


def make_shape_build_cache() -> tuple[dict[Any, Any], Callable[[], None]]:
    """Return the ``(cache, clear_fn)`` pair for a per-shape build cache (spec-039 P1.3).

    The promoted plumbing the mutation + form (Slice 2) + serializer (Slice 2)
    bind caches share: ``mutations/sets.py::_shape_build_cache`` and
    ``forms/sets.py::_form_shape_build_cache`` hand-mirror a module-level cache
    dict plus a ``clear`` that empties it. This single-sites that pair:

    - ``cache`` - a fresh dict the bind keys on its shape identity
      (``(declaration_class, operation_kind, effective field set)`` for the
      forms / mutation flavors; the ``SerializerInputShape`` descriptor for the
      serializer flavor) so identical shapes build once.
    - ``clear_fn()`` - empties the cache (registered into ``registry.clear()`` via
      ``register_subsystem_clear`` by the CONSUMING slice, not here).

    Pure plumbing; no registration. Slice 1 authors the helper (and unit-tests
    it); the serializer cache CONSUMER (``rest_framework/sets.py``) and the
    ``forms/sets.py`` re-point are Slice 2 (spec-039 SR-1 - the helper is
    authored here, the serializer cache is consumed there, matching the spec-038
    "generators in the inputs slice, cache consumer in the sets slice" split).
    """
    cache: dict[Any, Any] = {}

    def clear_fn() -> None:
        cache.clear()

    return cache, clear_fn


def pascalize_token(name: str) -> str:
    """Encode one field name as a single ``[A-Z][a-z0-9]*`` token for an input-name suffix.

    A single leading capital with a fully-lowercased tail and underscores removed
    (``is_private`` -> ``Isprivate``, ``category`` -> ``Category``). This shape is
    load-bearing for the bare-concatenation suffix the three generated-input
    type-name derivers use (``mutation_input_type_name`` / ``form_input_type_name`` /
    ``serializer_input_type_name``): because each token has NO interior capital and
    NO underscore, the concatenation of tokens is uniquely decomposable at uppercase
    boundaries, so distinct field sets never collide on one generated name.

    Deliberately NOT ``pascal_case`` (which collapses underscores across the whole
    name and per-segment-capitalizes) - an interior capital would make ``IsPrivate``
    ambiguously re-decompose as the two fields ``is`` + ``private``, the exact
    collision this guards against (``("a_b", "c")`` -> ``AbC`` vs ``("a", "b_c")`` ->
    ``ABc``, distinct). It also stays underscore-free so Strawberry's GraphQL name
    converter leaves a PascalCase class name unchanged (an underscore would be
    mangled into a lowercased segment tail in the GraphQL type name).

    Promoted here from ``mutations/inputs.py`` (spec-039 P2.3 kept it sited there at
    two consumers; at three - model + form + serializer - it graduates to the shared
    input-name machinery, kept visibly distinct from ``pascal_case``). The old
    ``mutations/inputs.py::_pascalize_token`` name remains as an import alias.
    """
    return name.replace("_", "").capitalize()


def generated_input_type_name(
    base_name: str,
    *,
    is_partial: bool,
    is_full_shape: bool,
    token: str,
) -> str:
    """Return a generated input-class name from its shape components (spec-039 M6).

    The load-bearing skeleton the three flavors' input-name derivers share
    (``mutations/inputs.py::mutation_input_type_name`` /
    ``forms/inputs.py::form_input_type_name`` /
    ``rest_framework/inputs.py::serializer_input_type_name``): a
    ``PartialInput`` / ``Input`` suffix, the canonical ``<Base><suffix>`` for the
    full shape, and a deterministic ``<Base><token><suffix>`` for any divergent
    shape. Single-sited so the suffix rule + the full-vs-derived branching cannot
    drift between flavors; each flavor still computes its OWN ``token`` (a
    ``pascalize_token`` concatenation for the model / form name-set shapes, a
    descriptor digest for the serializer) and its OWN ``is_full_shape`` /
    ``is_partial`` decision, so the injective-token contract stays with the caller.
    """
    suffix = "PartialInput" if is_partial else "Input"
    if is_full_shape:
        return f"{base_name}{suffix}"
    return f"{base_name}{token}{suffix}"


def normalize_field_name_sequence(
    value: Any,
    *,
    label: str = "fields",
    flavor: str,
) -> tuple[str, ...] | None:
    """Return a ``Meta.fields`` / ``Meta.exclude`` value as a tuple of names, or ``None``.

    The flavor-agnostic body all three write flavors call DIRECTLY - the model
    (``mutations/sets.py::DjangoMutation._validate_meta``), the form
    (``forms/inputs.py::resolve_effective_form_fields``), and the serializer
    (``rest_framework/inputs.py::resolve_effective_serializer_fields``) - passing
    their own ``flavor`` label (spec-038 integration Finding I1; spec-039 Mn3 inlined
    the former per-flavor ``_normalize_field_sequence`` / ``normalize_form_field_sequence``
    re-binding wrappers). Each site normalizes a declared field sequence the same
    way; they differ only in the human flavor label interpolated into the two
    ``ConfigurationError`` messages, so that single divergence is hoisted to the
    ``flavor`` parameter -- mirroring how ``mutations/sets.py::make_declaration_registry``
    already parameterizes its reject wording by a flavor label. The
    field-existence-basis check (a name not in the model's editable columns /
    the form's ``base_fields``) stays at each call site; this helper only validates
    the SHAPE of the declared sequence.

    ``None`` means "unset". A non-``None`` value is coerced to a tuple so the bind
    and the generator see one shape. A bare string is rejected (it would iterate
    as characters); a duplicate name is rejected (it would collapse silently when
    the effective field set is taken as a ``frozenset``, masking a malformed
    declaration), failing loud naming the repeated field(s). ``label`` names which
    key (``fields`` / ``exclude``) is at fault; ``flavor`` names the mutation
    base(s) in the message (e.g. ``"DjangoMutation"`` or
    ``"DjangoFormMutation / DjangoModelFormMutation"``).
    """
    if value is None:
        return None
    if isinstance(value, str):
        raise ConfigurationError(
            f"{flavor} Meta.fields / Meta.exclude must be a sequence of field "
            f"names, not a bare string: {value!r}.",
        )
    names = tuple(value)
    seen: set[str] = set()
    duplicates = sorted({name for name in names if name in seen or seen.add(name)})
    if duplicates:
        raise ConfigurationError(
            f"{flavor} Meta.{label} declares duplicate field name(s): "
            f"{duplicates!r}. Each field may appear at most once.",
        )
    return names


def resolve_effective_fields(
    basis: dict[str, Any],
    *,
    fields: Any,
    exclude: Any,
    subject: str,
    seq_flavor: str,
    unknown_noun: str,
    empty_message: str,
) -> dict[str, Any]:
    """Return the effective ``{name: field}`` dict after ``fields`` / ``exclude`` narrowing (spec-039 M4).

    The narrowing spine both ``forms/inputs.py::resolve_effective_form_fields`` and
    ``rest_framework/inputs.py::resolve_effective_serializer_fields`` share: normalize
    ``fields`` + ``exclude`` (via ``normalize_field_name_sequence`` under ``seq_flavor``)
    -> mutual-exclusion raise -> ``fields``-branch unknown-name raise ->
    ``exclude``-branch unknown-name raise (the identical ``[name for name in fields if
    name not in basis]`` loop) -> empty-effective-set raise. Preserves ``basis``
    insertion order for the ``exclude`` / un-narrowed cases and the caller's order for
    ``fields``.

    The only per-flavor divergences are threaded in as the four message knobs
    (``subject`` = the ``"<Flavor> for <Name>"`` prefix, ``seq_flavor`` = the
    ``normalize_field_name_sequence`` flavor label, ``unknown_noun`` = the
    ``"unknown ... field(s)"`` clause, ``empty_message`` = the fully-formed no-fields
    error) and the ``basis`` dict itself - the caller computes its basis (the form's
    ``base_fields``, the serializer's read-only-filtered ``writable`` map) so the
    "basis is the only structural divergence" shape holds. Each flavor keeps a thin
    wrapper that supplies these, so the pinned error wording stays byte-identical.
    """
    fields = normalize_field_name_sequence(fields, label="fields", flavor=seq_flavor)
    exclude = normalize_field_name_sequence(exclude, label="exclude", flavor=seq_flavor)
    if fields is not None and exclude is not None:
        raise ConfigurationError(
            f"{subject} declares both `fields` and `exclude`; supply at most one.",
        )
    if fields is not None:
        unknown = [name for name in fields if name not in basis]
        if unknown:
            raise ConfigurationError(
                f"{subject} declares `fields` naming {unknown_noun}: {sorted(unknown)!r}.",
            )
        effective = {name: basis[name] for name in fields}
    elif exclude is not None:
        unknown = [name for name in exclude if name not in basis]
        if unknown:
            raise ConfigurationError(
                f"{subject} declares `exclude` naming {unknown_noun}: {sorted(unknown)!r}.",
            )
        excluded = set(exclude)
        effective = {name: field for name, field in basis.items() if name not in excluded}
    else:
        effective = dict(basis)

    if not effective:
        raise ConfigurationError(empty_message)
    return effective


def guard_dropped_required(
    required_field_names: Any,
    effective_field_names: Any,
    *,
    waived: Any = (),
    make_error: Callable[[list[str]], Exception],
) -> None:
    """Raise if a create narrowing drops a still-required field not covered by ``waived`` (spec-039 Md1).

    The set-arithmetic core the form + serializer create-required guards share:
    ``sorted(required - effective - waived)``; a non-empty dropped set raises the
    flavor's ``make_error(dropped)`` (a ``ConfigurationError`` either way). The form
    flavor passes no ``waived`` (it has no injected-field mechanism); the serializer
    passes ``Meta.injected_fields``. The MESSAGE stays flavor-specific (built by
    ``make_error`` over the sorted dropped list) so each pinned wording is
    byte-preserved; only the drop-detection is single-sited.
    """
    dropped = sorted(set(required_field_names) - set(effective_field_names) - set(waived))
    if dropped:
        raise make_error(dropped)


def iter_provided_input_fields(data: Any) -> Iterator[tuple[str, Any, Any]]:
    """Yield ``(python_name, value, field)`` for each PROVIDED field of a bound input (spec-039 M2).

    The ``UNSET``-strip walk every write-flavor decoder opens with - the model
    ``mutations/resolvers.py::_decode_relations``, the form
    ``forms/resolvers.py::_decode_form_data``, and the serializer
    ``rest_framework/resolvers.py::_decode_input_object``: iterate
    ``data.__strawberry_definition__.fields``, read each field's value off the input
    dataclass, and skip any left ``strawberry.UNSET`` (an OMITTED field, distinct from
    an explicit ``None`` which is kept as a provided value). Single-sited so the three
    decoders share ONE definition of "which fields did the client provide" - and a
    fourth write flavor gets the blessed walk for free. The per-field decode (kind
    branch, spec lookup, short-circuit protocol) stays at each call site: this owns
    only the walk, not the routing.
    """
    for field in data.__strawberry_definition__.fields:
        python_name = field.python_name
        value = getattr(data, python_name, strawberry.UNSET)
        if value is strawberry.UNSET:
            continue
        yield python_name, value, field


def build_strawberry_input_class(
    name: str,
    field_specs: list[tuple[str, Any, dict[str, Any] | None]],
) -> type:
    """Construct a ``@strawberry.input``-decorated dataclass.

    ``field_specs`` is a list of ``(python_attr, annotation, field_kwargs)``
    triples. ``field_kwargs`` may carry ``name=`` for the GraphQL alias,
    ``default=`` for the dataclass default, and ``description=`` for the
    Strawberry field description.

    **A triple that OMITS ``default`` builds a REQUIRED field**: no class
    default is set, so ``@strawberry.input`` renders the field non-null and
    rejects an omitted value at GraphQL coercion. A bare ``None`` default
    (the prior behavior) renders non-null SDL *yet still accepts omission*,
    delivering ``None`` to the resolver and masking the missing-input error
    (``docs/feedback.md`` Finding 2). An OPTIONAL field must therefore pass an
    explicit ``default`` - ``strawberry.UNSET`` for the mutation / form
    ``annotation | None`` widening, ``None`` for the filter / order optional
    inputs (Strawberry tolerates a required field after a defaulted one; its
    inputs are keyword-only).

    The class is constructed via ``type(name, (), namespace)`` rather than
    ``dataclasses.make_dataclass`` because ``make_dataclass`` replaces any
    ``strawberry.field(...)`` default with a plain ``dataclasses.Field`` and
    strips the strawberry-specific metadata (the ``name=`` alias would be
    lost). Setting the ``strawberry.field`` as a class-level attribute
    alongside ``__annotations__`` preserves the metadata through the
    ``@strawberry.input`` decoration.
    """
    namespace: dict[str, Any] = {"__annotations__": {}}
    for python_attr, annotation, raw_kwargs in field_specs:
        kwargs = dict(raw_kwargs or {})
        # The PRESENCE of ``default`` (not its value) decides required-vs-optional:
        # a required field gets NO class default at all, so ``None`` is a legal
        # explicit default for an optional field rather than the required sentinel.
        has_default = "default" in kwargs
        default = kwargs.pop("default", None)
        strawberry_field_kwargs: dict[str, Any] = {}
        if "name" in kwargs:
            strawberry_field_kwargs["name"] = kwargs.pop("name")
        if "description" in kwargs:
            strawberry_field_kwargs["description"] = kwargs.pop("description")
        namespace["__annotations__"][python_attr] = annotation
        if strawberry_field_kwargs:
            # An aliased / described field still needs a ``strawberry.field``;
            # pass ``default`` only when one was supplied so a required aliased
            # field (e.g. a required FK ``categoryId``) stays non-null.
            namespace[python_attr] = (
                strawberry.field(default=default, **strawberry_field_kwargs)
                if has_default
                else strawberry.field(**strawberry_field_kwargs)
            )
        elif has_default:
            namespace[python_attr] = default
        # else: a required, un-aliased field -> NO class attribute, so
        # ``@strawberry.input`` renders it non-null and coercion rejects omission.
    cls = type(name, (), namespace)
    return strawberry.input(cls)


def materialize_generated_input_class(
    name: str,
    cls: type,
    *,
    module_path: str,
    family_label: str,
    ledger: dict[str, type],
) -> None:
    """Pin ``cls`` as a real module global of ``module_path`` under ``name``.

    Strawberry's ``LazyType.resolve_type`` reads
    ``sys.modules[<module>].__dict__[name]`` to materialize an
    ``Annotated[<name>, strawberry.lazy(<module>)]`` reference; this is the
    single entry point that pins ``cls`` at the matching ``__dict__`` slot
    (spec-027 / spec-028 Decision 9).

    Idempotent on the ``(name, cls)`` pair: re-materializing the same class
    under the same name is a no-op (the Decision 9 lifecycle clause -- supports
    partial-finalize recovery without a sentinel pass). A collision against a
    different class under the same ``name`` raises ``ConfigurationError`` naming
    both qualified class names plus the ``family_label`` (``FilterSet`` /
    ``OrderSet``) so the consumer sees the offending pair and family instead of
    a cryptic schema-build error.
    """
    existing = ledger.get(name)
    if existing is cls:
        return
    if existing is not None:
        raise ConfigurationError(
            f"{name!r} is materialized by two distinct {family_label} input classes: "
            f"{existing.__module__}.{existing.__qualname__} vs "
            f"{cls.__module__}.{cls.__qualname__}. Rename one {family_label.lower()} "
            "so its class-derived input type name is unique.",
        )
    module = sys.modules[module_path]
    setattr(module, name, cls)
    ledger[name] = cls


def build_lazy_input_annotation(
    set_class: type,
    *,
    expected_base: type,
    family_name: str,
    expected_label: str,
    ledger: set[type],
    input_type_name_for: Callable[[type], str],
    module_path: str,
) -> object:
    """Return the ``Annotated[..., strawberry.lazy(...)]`` forward-ref for a set's input class.

    The Decision-11 consumer-helper body shared by
    ``filters/__init__.py::filter_input_type`` and
    ``orders/__init__.py::order_input_type`` (the 0.0.9 DRY pass). Validates
    ``set_class`` is an ``expected_base`` subclass -- raising ``TypeError`` with
    the family's wording (``family_name`` + ``expected_label``, e.g.
    ``"filter_input_type() requires a FilterSet subclass; got ..."``) so consumers
    catch misuse at the resolver-declaration site rather than schema-build time --
    records it in the family ``ledger`` (the finalizer's orphan check reads this),
    and builds the canonical Strawberry forward-reference.

    The ForwardRef-wrapped ``Annotated[<runtime str>, strawberry.lazy(<module>)]``
    form is load-bearing: ``LazyType.resolve_type`` resolves it via
    ``module.__dict__`` at schema build, by which point ``finalize_django_types()``
    has materialized the input class as a module global. The type name is passed
    as a runtime-computed string into ``Annotated[...]`` (NOT interpolated into a
    literal outside the call) so the ForwardRef wrapping holds.
    """
    if not (isinstance(set_class, type) and issubclass(set_class, expected_base)):
        raise TypeError(f"{family_name}() requires {expected_label} subclass; got {set_class!r}")
    ledger.add(set_class)
    return Annotated[input_type_name_for(set_class), strawberry.lazy(module_path)]


def iter_set_subclasses(root: type) -> list[type]:
    """Return every concrete subclass of ``root`` (depth-first, dedup by identity).

    Uses ``type.__subclasses__()`` which only yields LIVE subclasses;
    garbage-collected definitions silently drop. That is the correct contract
    for a test-isolation clear -- a definition that has already been collected
    has no binding state to reset.
    """
    seen: set[type] = set()
    result: list[type] = []
    stack: list[type] = list(root.__subclasses__())
    while stack:
        cls = stack.pop()
        if cls in seen:
            continue
        seen.add(cls)
        result.append(cls)
        stack.extend(cls.__subclasses__())
    return result


def _safe_import(module_path: str, attr: str) -> Any:
    """Cycle-safe import of ``module_path.attr`` returning ``None`` on ImportError.

    Encapsulates the "best-effort, skip and continue" pattern the
    ``registry.clear()`` lifecycle relies on: a partial-load environment (one
    submodule reachable, another not) still clears whatever IS reachable. A
    ``None`` entry in ``sys.modules`` (the test-isolation way of simulating an
    unimportable submodule) raises ``ImportError`` here, same as the previous
    inline ``from .submodule import X`` guards. Delegates to
    ``utils/imports.py::import_attr_if_importable`` but preserves this wrapper's
    attr-lenient shape (a missing attr is ``None``, not ``AttributeError``) for
    the partial-load lifecycle callers.
    """
    try:
        return import_attr_if_importable(module_path, attr)
    except AttributeError:
        return None


def clear_generated_input_namespace(
    *,
    materialized_names: dict[str, type],
    field_specs: dict[Any, Any],
    factory_module: str,
    factory_class_name: str,
    collision_registry_attr: str,
    set_module: str,
    set_class_name: str,
) -> None:
    """Reset a family's generated-input ledger and per-set binding state.

    Clears the bookkeeping that prevents stale-state leakage across
    consumer-side autouse-reload fixtures:

    - ``materialized_names`` -- forces the materialization helper to re-emit on
      the next finalize.
    - ``field_specs`` -- per-(set, field) provenance for the runtime normalizer.
    - the arguments factory's class-level caches (``input_object_types`` and the
      family collision registry named by ``collision_registry_attr``).
    - every set subclass's phase-2.5 binding state. The reset attrs come from the
      resolved set base's ``_lifecycle`` descriptor (``SetLifecycleAttrs``) rather
      than a re-spelled tuple, so the family names them in ONE place (the 0.0.9
      DRY pass, ``docs/feedback.md`` Major 3).

    **Materialized class objects are intentionally left parked** in the family
    ``inputs`` module ``__dict__``: the materialization helper overwrites the
    module global via ``setattr`` on the next finalize, so a parked class is
    replaced in place once the rebuild runs. Stripping it via ``delattr`` here
    would break any ``strawberry.lazy(...)`` LazyType held by a consumer module
    whose autouse-reload fixture did NOT also reload the holder.

    Each subsystem lookup is best-effort (``_safe_import``): an unreachable
    factory / set module never prevents the reachable ledger reset. The two
    lookups are independent so a partial-load build state still clears whatever
    is reachable.
    """
    materialized_names.clear()
    field_specs.clear()

    factory_cls = _safe_import(factory_module, factory_class_name)
    if factory_cls is not None:
        factory_cls.input_object_types.clear()
        getattr(factory_cls, collision_registry_attr).clear()

    set_root = _safe_import(set_module, set_class_name)
    if set_root is not None:
        # The per-family binding-state attrs (owner / expansion cache / reentry
        # guard) come from the set base's ``_lifecycle`` descriptor, so the names
        # are not re-spelled at the call site.
        binding_attrs = set_root._lifecycle.binding_attrs
        for subclass in iter_set_subclasses(set_root):
            # ``delattr`` on the subclass so an inherited default (the set
            # base's ``_owner_definition = None``) is restored rather than
            # masked. Each attribute is removed only when set directly on the
            # subclass (``in subclass.__dict__``) so a subclass that never had
            # a binding tolerates the clear.
            for attr in binding_attrs:
                if attr in subclass.__dict__:
                    delattr(subclass, attr)


class GeneratedInputArgumentsFactory:
    """BFS-build every reachable Strawberry input class for a set-family root.

    Shared substrate for ``filters/factories.py::FilterArgumentsFactory`` and
    ``orders/factories.py::OrderArgumentsFactory`` (and the cookbook's parallel
    ``*_arguments_factory.py`` BFS algorithm). The BFS walk, the per-class
    collision check, the idempotent cache, and the subclass-rejection guard are
    single-sited here; each family factory subclasses this DIRECTLY and supplies
    its own caches plus the family hook attributes below.

    Required per-family class attributes:

    - ``input_object_types: dict[str, type]`` -- class-name -> built input
      class. A fresh dict per family (filter and order builds must never share
      a namespace); the base declares it annotation-only so a family that
      forgets to redefine it fails loud at first use rather than sharing.
    - the collision registry named by ``_collision_registry_attr`` -- a fresh
      dict per family. Kept spec-named (``_type_filterset_registry`` /
      ``_type_orderset_registry``) so ``registry.clear()`` and the test suite
      address it directly; the base reaches it through the
      ``_collision_registry`` property.
    - ``_factory_label`` / ``_family_label`` / ``_rename_noun`` -- collision
      error wording so the message still names ``FilterArgumentsFactory`` /
      ``FilterSet`` / ``filterset`` vs the order equivalents.
    - ``_related_attr`` / ``_related_target_attr`` -- the related-collection
      attribute (``related_filters`` / ``related_orders``) and the attribute on
      each related entry that resolves the target set class (``filterset`` /
      ``orderset``).

    Subclassing a CONCRETE family factory is rejected at class-creation time:
    the class-level caches are mutable dicts a grand-subclass would inherit
    rather than isolate, silently cross-contaminating builds. Extend by
    composition (wrap an instance), not inheritance.
    """

    # Per-family caches -- declared annotation-only; each family factory MUST
    # redefine ``input_object_types`` and its named collision registry as fresh
    # dicts. No default here, so a forgetful subclass AttributeErrors loudly
    # instead of silently sharing the base's namespace.
    input_object_types: ClassVar[dict[str, type]]
    _collision_registry_attr: ClassVar[str]
    _factory_label: ClassVar[str]
    _family_label: ClassVar[str]
    _rename_noun: ClassVar[str]
    _related_attr: ClassVar[str]
    _related_target_attr: ClassVar[str]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Allow the direct family factories; reject any deeper subclassing."""
        super().__init_subclass__(**kwargs)
        # The two family factories subclass this base directly. A class whose
        # bases do NOT include the base is a grand-subclass of a concrete
        # factory -- reject it (its caches would be the family's, not its own).
        if GeneratedInputArgumentsFactory not in cls.__bases__:
            parent = cls.__bases__[0]
            raise TypeError(
                f"{parent.__name__} does not support subclassing "
                f"(attempted by {cls.__name__!r}): its class-level caches are shared "
                "mutable dicts a subclass would inherit rather than isolate, silently "
                "cross-contaminating builds. Extend it by composition (wrap an "
                "instance), not inheritance.",
            )

    def __init__(self, set_class: type) -> None:
        """Store the root set class and its class-derived input type name."""
        self.set_class = set_class
        self.input_type_name = set_class.type_name_for()

    @property
    def _collision_registry(self) -> dict[str, type]:
        """The family collision registry, addressed through its spec-named attr."""
        return getattr(type(self), self._collision_registry_attr)

    @property
    def arguments(self) -> type:
        """BFS-build the root set and return its input class.

        Idempotent: subsequent reads against the same set hit the cache.
        """
        self._ensure_built()
        return self.input_object_types[self.input_type_name]

    def _ensure_built(self) -> None:
        """BFS-walk the root set + every reachable related target.

        Cycles (``A -> B -> A``) are handled naturally by the enqueue-time
        ``target not in seen`` gate. Builds each set exactly once; subsequent
        visits hit the cache. FIFO queue (``pending.pop(0)``) gives a
        deterministic breadth-first build order across both subsystems.
        Collision detection raises when two distinct sets claim the same name.
        """
        pending: list[type] = [self.set_class]
        seen: set[type] = set()
        while pending:
            set_cls = pending.pop(0)
            if set_cls in seen:
                continue
            seen.add(set_cls)

            target_name = set_cls.type_name_for()
            existing_owner = self._collision_registry.get(target_name)
            if existing_owner is not None and existing_owner is not set_cls:
                raise ConfigurationError(
                    f"{self._factory_label}: input type name {target_name!r} is claimed "
                    f"by two distinct {self._family_label} classes: "
                    f"{existing_owner.__module__}.{existing_owner.__qualname__} vs "
                    f"{set_cls.__module__}.{set_cls.__qualname__}. Rename one "
                    f"{self._rename_noun} so its class-derived input type name is unique.",
                )

            if target_name not in self.input_object_types:
                self._build_class_type(set_cls)

            for related in getattr(set_cls, self._related_attr, {}).values():
                target = getattr(related, self._related_target_attr)
                # ``Related*(None, ...)`` placeholder -- skip silently.
                if target is not None and target not in seen:
                    pending.append(target)

    def _build_class_type(self, set_cls: type) -> None:
        """Build the root input class for ``set_cls`` and stash it in the cache."""
        type_name = set_cls.type_name_for()
        owner_definition = getattr(set_cls, "_owner_definition", None)
        triples = self._build_input_triples(set_cls, type_name, owner_definition)
        input_cls = build_strawberry_input_class(type_name, triples)
        self.input_object_types[type_name] = input_cls
        self._collision_registry[type_name] = set_cls

    def _build_input_triples(
        self,
        set_cls: type,
        type_name: str,
        owner_definition: Any,
    ) -> list[tuple[str, Any, dict[str, Any]]]:
        """Return the input-field triples for ``set_cls`` (family hook).

        The filter family appends ``_build_logic_fields`` (the ``and_`` /
        ``or_`` / ``not_`` operator bag); the order family returns the field
        triples as-is (no operator bag, Spec Decision 8).
        """
        raise NotImplementedError  # family hook
