"""Generated-input construction and lifecycle primitives shared by set and write families.

The filter and order subsystems each build real Strawberry input classes as
module globals (``strawberry.lazy(...)`` resolves through ``module.__dict__``),
keep class-level factory caches, detect duplicate generated input names, and
reset stale binding state during ``registry.clear()``. spec-027 and spec-028
grew those mechanics as parallel copies; this module single-sites the NEUTRAL
machinery so a fix to the materialization ledger, the BFS collision check, or
the namespace-clear lifecycle lands once instead of being hand-mirrored.

What lives here is mechanics only. Domain semantics stay at the call sites:
``filters/inputs.py`` keeps ``convert_filter_to_input_annotation`` /
``normalize_input_value`` and the operator-bag / logic-field builders;
``orders/inputs.py`` keeps ``convert_order_field_to_input_annotation`` /
``normalize_input_value`` and the ``Ordering`` enum. The two ``inputs`` modules
re-export the helpers below under their spec-named aliases (``FieldSpec`` /
``build_input_class`` / ``_camel_case`` / ``_iter_*set_subclasses`` /
``_input_type_name_for``) so existing imports and the test suite keep addressing
them on the family module. Set-family Decision-9 ledgers ride
``make_set_input_namespace`` (heavy clear); write flavors ride
``make_input_namespace`` (light clear). Layer-6 dynamic-set caches ride
``make_dynamic_set_getter`` (hashing / normalize / ``type(...)`` skeleton);
each family keeps its own cache dict and base class. Set-family ``Meta.fields``
fingerprints ride ``resolve_set_meta_fields`` (synonym rule),
``promote_set_meta_fields`` (class-Meta write-back), ``read_set_meta_fields``
(expansion / apply read), and ``canonicalize_set_meta_fields`` (unordered
shapes). FilterSet uses ``FILTERSET_FIELDS_ALIAS``; OrderSet has no synonym.

This module depends on neither family package, so both can import it without a
cycle (same contract as ``utils/connections.py``).
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Annotated, Any, ClassVar

import strawberry
from django.db import models as django_models

from ..exceptions import ConfigurationError, _safe_arg_repr, _safe_type_name
from .imports import import_attr_if_importable

# ``utils/strings.py`` is the owner of ``graphql_camel_name``;
# re-imported here (the ``as`` form marks the explicit re-export) so existing
# ``from ..utils.inputs import graphql_camel_name`` consumers keep their import
# path.
from .strings import flatten_lookup_path
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


def set_input_type_name(set_class: type) -> str:
    """Return the canonical Strawberry input-class name for a set-family class.

    Thin delegate to ``ClassBasedTypeNameMixin.type_name_for()``: every
    ``FilterSet`` / ``OrderSet`` subclass ``Foo`` produces ``FooInputType``.
    Both family ``inputs`` modules re-export this as ``_input_type_name_for``
    so spec-027 / spec-028 callers stay pinned to one derivation site rather
    than each wrapping ``type_name_for`` again.
    """
    return set_class.type_name_for()


def optional_field_kwargs(python_attr: str, graphql_name: str) -> dict[str, Any]:
    """Return the optional default plus any non-identity GraphQL alias.

    Every generated filter / order input field is optional-with-``None``: an
    omitted ``default`` means REQUIRED under ``build_strawberry_input_class``'s
    required-vs-optional contract, so the explicit ``default: None`` keeps the
    field omittable. ``build_strawberry_input_class`` pins the package-derived
    name when this helper does not need to carry an alias, so Strawberry never
    re-derives the wire name through a different converter.
    """
    kwargs: dict[str, Any] = {"default": None}
    if python_attr != graphql_name:
        kwargs["name"] = graphql_name
    return kwargs


def optional_input_field(
    annotation: Any,
    *,
    python_attr: str,
    graphql_name: str,
    widen: bool,
) -> tuple[Any, dict[str, Any]]:
    """Apply the write-input optional-widening tail to one field.

    The per-field tail the form and serializer input builders share, seated
    beside ``build_strawberry_input_class`` whose required-vs-optional contract
    (the presence of a ``default``) it exists to satisfy: carry any ``name=``
    alias, and - when ``widen`` is set (the form's ``not required``, the
    serializer's ``allow_null``-or-optional nullability rule, each computed at
    its call site) - widen the annotation to ``T | None`` and default it to
    ``strawberry.UNSET`` so the field is OMITTABLE. A non-widened field gets NO
    default, so GraphQL enforces presence. Returns the ``(annotation,
    field_kwargs)`` pair; a flavor may add further kwargs (the serializer's SDL
    ``description``) on top.

    ``build_strawberry_input_class`` pins the package-derived name when no alias
    is needed, keeping Strawberry's converter out of generated-input naming.
    """
    field_kwargs: dict[str, Any] = {}
    if python_attr != graphql_name:
        field_kwargs["name"] = graphql_name
    if widen:
        annotation = annotation | None
        field_kwargs["default"] = strawberry.UNSET
    return annotation, field_kwargs


def emit_set_input_field_triples(
    set_cls: type,
    entries: Iterator[tuple[str, Any]] | list[tuple[str, Any]],
    *,
    related_target_of: Callable[[str, Any], tuple[bool, Any]],
    related_source_path_of: Callable[[str, Any], str],
    leaf_of: Callable[[str, str, Any], tuple[Any, str]],
    input_type_name_for: Callable[[type], str],
    module_path: str,
    field_specs: dict[tuple[type, str], GeneratedInputFieldSpec],
) -> list[tuple[str, Any, dict[str, Any]]]:
    """Emit the per-field input triples + ``FieldSpec`` rows for one set class.

    The triple-emission scaffold the filter and order ``_build_input_fields``
    grew separately: for each ``(top_name, entry)`` pair derive the python attr
    (``flatten_lookup_path``) + camel-cased GraphQL name + the
    ``optional_field_kwargs`` shape, then branch:

    - **related** (``related_target_of`` says so): a ``Related*(None, ...)``
      placeholder target skips silently; otherwise emit the lazy forward-ref
      ``Annotated[<target input name>, strawberry.lazy(module_path)] | None``
      and record ``related_source_path_of``'s path (``top_name`` for filters;
      ``field_name or top_name`` for orders).
    - **leaf**: ``leaf_of`` owns the family's leaf semantics (the filter side's
      operator-bag class build + declared-vs-autogen source rule; the order
      side's fixed ``Ordering | None``) and returns the final
      ``(annotation, django_source_path)``.

    Each emitted field also lands its ``GeneratedInputFieldSpec`` in the
    family's ``field_specs`` provenance table keyed ``(set_cls, python_attr)``
    (what the runtime normalizers walk). Family-specific PRE-filtering (the
    filter side's expanded-child grouping and ``HIDE_FLAT_FILTERS`` skip)
    happens in ``entries`` before this scaffold - the same
    parameterization split ``GeneratedInputArgumentsFactory`` proved out for
    the BFS: mechanics here, semantics at the call site.

    Fails loud on a generated-field collision. Two set members whose paths
    flatten (``__`` -> ``_`` via ``flatten_lookup_path``) to one python attr --
    e.g. a relation traversal ``branch__name`` beside a declared / scalar
    ``branch_name`` -- or that camel-case to one GraphQL name
    (``foo_bar`` / ``fooBar``) would make ``build_strawberry_input_class``
    silently overwrite one field in the generated input dataclass, dropping a
    filter / ordering the consumer declared from the public schema with NO
    error. The type surface
    (``types/finalizer.py::_audit_field_surface``) and the write-input surfaces
    (``iter_input_field_collisions``) already reject this class of silent drop;
    this is the parity guard for the filter / order generated-input surfaces,
    which both route their emission through here.
    """
    triples: list[tuple[str, Any, dict[str, Any]]] = []
    seen_attr: dict[str, str] = {}
    seen_graphql: dict[str, str] = {}
    for top_name, entry in entries:
        python_attr = flatten_lookup_path(top_name)
        graphql_name = graphql_camel_name(python_attr)
        field_kwargs = optional_field_kwargs(python_attr, graphql_name)
        is_related, target = related_target_of(top_name, entry)
        if is_related:
            if target is None:
                # ``Related*(None, ...)`` placeholder - skip silently.
                continue
            target_name = input_type_name_for(target)
            inner = Annotated[target_name, strawberry.lazy(module_path)]
            annotation: Any = inner | None
            django_source_path = related_source_path_of(top_name, entry)
        else:
            annotation, django_source_path = leaf_of(top_name, python_attr, entry)
        # Reject the silent-overwrite collision BEFORE it reaches the input
        # dataclass / ``field_specs`` (both keyed by ``python_attr``, both of
        # which the later member would clobber). Checked only for emitted fields
        # -- placeholder skips above never reach here.
        prior_attr = seen_attr.get(python_attr)
        if prior_attr is not None:
            raise ConfigurationError(
                f"{set_cls.__qualname__}: members {prior_attr!r} and {top_name!r} both "
                f"generate the input attribute {python_attr!r} (Django path separators "
                "flatten to '_'), so one would silently overwrite the other in the "
                "generated input type. Rename one member or drop one via "
                "Meta.fields / Meta.exclude.",
            )
        prior_graphql = seen_graphql.get(graphql_name)
        if prior_graphql is not None:
            raise ConfigurationError(
                f"{set_cls.__qualname__}: members {prior_graphql!r} and {top_name!r} both "
                f"generate the GraphQL input field name {graphql_name!r} under package "
                "camel-casing, so one would silently overwrite the other in the generated "
                "input type. Rename one member or drop one via Meta.fields / Meta.exclude.",
            )
        seen_attr[python_attr] = top_name
        seen_graphql[graphql_name] = top_name
        triples.append((python_attr, annotation, field_kwargs))
        field_specs[(set_cls, python_attr)] = GeneratedInputFieldSpec(
            python_attr=python_attr,
            graphql_name=graphql_name,
            django_source_path=django_source_path,
        )
    return triples


# The decode-kind vocabulary the write-flavor converters + resolvers share
#: one conceptual enum, previously declared per-flavor in
# ``forms/converter.py`` and ``rest_framework/serializer_converter.py``.
# Single-sourced here next to ``InputFieldSpec`` (their type-level consumer);
# the serializer flavor extends with its ``NESTED_SINGLE`` / ``NESTED_MULTI``
# pair (nested writes are DRF-only). Each flavor's converter module re-exports
# them so existing ``from .converter import SCALAR`` consumers keep their path.
SCALAR: str = "scalar"
RELATION_SINGLE: str = "relation_single"
RELATION_MULTI: str = "relation_multi"
FILE: str = "file"


class FieldConversionBase:
    """The annotation + decode kind + required-ness value object.

    The shared shape behind ``forms/converter.py::FormFieldConversion`` and
    ``rest_framework/serializer_converter.py::SerializerFieldConversion``:
    ``required`` is the flavor field's own ``field.required``; ``annotation`` is
    the resolved Strawberry annotation for a ``SCALAR`` field, while a relation
    / file (/ nested) field carries ``annotation=None`` here - the annotation is
    finalized at the flavor's build site, so only the ``kind`` is authoritative.
    ``kind`` defaults to ``SCALAR`` so a consumer-registered converter
    can return a conversion without importing the kind
    constant; the internal relation / file constructions pass ``kind``
    explicitly. Flavor tables do not construct this shape by hand: they store
    ``utils/converters.py::make_scalar_converter`` /
    ``make_kind_converter`` callables so the VALUE shape stays one site.
    """

    __slots__ = ("annotation", "kind", "required")

    def __init__(
        self,
        *,
        annotation: Any,
        kind: str = SCALAR,
        required: bool,
    ) -> None:
        self.annotation = annotation
        self.kind = kind
        self.required = required


@dataclass(frozen=True)
class InputFieldSpec:
    """Unified per-generated-input-field reverse-map record.

    One reverse-map record for every write flavor that decodes a generated GraphQL
    input back to a framework write target. ``target_name`` is the neutral
    decode key (the bound form field name on the form path; the declared
    serializer field name on the DRF path). Serializer-only axes stay optional
    defaults so the form path never carries unused mode flags:

    - ``input_attr`` - the generated Strawberry dataclass attr (``category_id``
      for an FK relation, ``name`` for a scalar).
    - ``graphql_name`` - the camel-cased GraphQL wire name (``categoryId``).
    - ``target_name`` - the per-flavor decode key. For the form flavor this is the
      form's declared field name (``category``); for the serializer flavor this is
      the DECLARED serializer field name (``category_pk``), which the framework
      supplies in the serializer's input ``data`` before DRF maps it through
      ``source`` into ``validated_data``. Never the ``<name>_id`` relation attr.
    - ``kind`` - one of the flavor's decode kinds (``scalar`` /
      ``relation_single`` / ``relation_multi`` / ``file``; serializer also uses
      nested kinds).
    - ``source`` - the serializer-only extra axis: the one-segment ``source`` the
      backing ``models.Field`` was resolved through (``category`` for a
      ``category_pk`` field declared ``source="category"``). ``None`` for forms and
      for a serializer field whose ``source`` equals its declared name.
    - ``related_model`` - the Django target model a relation field decodes its
      id(s) against (``Category`` for a ``category`` / ``category_pk`` relation),
      recorded at BUILD/BIND time so the decode never re-discovers the
      related model per request. ``None`` for a non-relation
      (``scalar`` / ``file``) field.
    - ``nested_specs`` - the serializer-only nested-serializer axis: the
      ordered reverse-map ``InputFieldSpec`` tuple of the NESTED input's
      OWN fields, recorded for a ``nested_single`` / ``nested_multi`` field so the
      the decode recurses into the nested input dataclass with the SAME
      per-field machinery (scalar / relation / file / deeper-nested) the top level
      uses. ``None`` for every non-nested field (including every form field). A
      tuple of frozen ``InputFieldSpec`` is hashable, so it participates in the
      frozen descriptor identity + the per-shape build cache key like any other
      axis.
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
    modules share. Before spec-039 ``mutations/inputs.py`` and
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


def make_set_input_namespace(
    module_path: str,
    family_label: str,
    *,
    factory_module: str,
    factory_class_name: str,
    collision_registry_attr: str,
    set_module: str,
    set_class_name: str,
) -> tuple[
    dict[str, type],
    dict[tuple[type, str], GeneratedInputFieldSpec],
    Callable[[str, type], None],
    Callable[[], None],
]:
    """Return the set-family ``(ledger, field_specs, materialize_fn, clear_fn)`` quartet.

    The heavy Decision-9 sibling of ``make_input_namespace``. Filter and order
    ``inputs`` modules grew the same four-part shape (a ``_materialized_names``
    ledger, a ``_field_specs`` provenance table, a ``materialize_input_class``
    wrapper, a ``clear_*_input_namespace`` that resets factory caches +
    ``_lifecycle`` binding). This single-sites it:

    - ``ledger`` - ``name -> input_class`` dict the caller stores as
      ``_materialized_names``.
    - ``field_specs`` - ``(set_cls, python_attr) -> GeneratedInputFieldSpec``
      provenance table the caller stores as ``_field_specs``.
    - ``materialize_fn(name, cls)`` - pins ``cls`` as a real global of
      ``module_path`` via ``materialize_generated_input_class``.
    - ``clear_fn()`` - the HEAVY clear: both dicts plus the arguments-factory
      caches and per-set ``_lifecycle`` binding state named by the factory /
      set kwargs. Materialized class objects stay PARKED.

    Write flavors keep using ``make_input_namespace`` (light ``ledger.clear()``
    only): they have neither a BFS factory cache nor per-set lifecycle state.
    """
    ledger: dict[str, type] = {}
    field_specs: dict[tuple[type, str], GeneratedInputFieldSpec] = {}

    def materialize_fn(name: str, cls: type) -> None:
        materialize_generated_input_class(
            name,
            cls,
            module_path=module_path,
            family_label=family_label,
            ledger=ledger,
        )

    def clear_fn() -> None:
        clear_generated_input_namespace(
            materialized_names=ledger,
            field_specs=field_specs,
            factory_module=factory_module,
            factory_class_name=factory_class_name,
            collision_registry_attr=collision_registry_attr,
            set_module=set_module,
            set_class_name=set_class_name,
        )

    return ledger, field_specs, materialize_fn, clear_fn


def _opaque_meta_value(value: Any) -> tuple[str, int, int]:
    """Return an identity token for a value whose structure cannot be inspected."""
    return ("__unhashable_meta_value__", id(type(value)), id(value))


def _meta_sort_key(value: Any) -> tuple[str, int, int]:
    """Return a total, hostile-repr-safe ordering key for metadata values."""
    return (_safe_arg_repr(value), id(type(value)), id(value))


def _base_meta_values(value: Any) -> tuple[Any, ...]:
    """Read a built-in container through its base iterator, not an override."""
    if isinstance(value, dict):
        return tuple(dict.items(value))
    if isinstance(value, set):
        return tuple(set.__iter__(value))
    if isinstance(value, frozenset):
        return tuple(frozenset.__iter__(value))
    if isinstance(value, list):
        return tuple(list.__iter__(value))
    if isinstance(value, tuple):
        return tuple(tuple.__iter__(value))
    return tuple(value)


def _sorted_meta_values(value: Any) -> list[Any]:
    """Sort a metadata container without trusting iteration or representation hooks."""
    try:
        return sorted(_base_meta_values(value), key=_meta_sort_key)
    except BaseException as exc:
        raise ConfigurationError(
            f"Generated set metadata contains an unreadable {_safe_type_name(value)} container.",
        ) from exc


def make_hashable_meta_value(v: Any) -> Any:
    """Recursively convert unhashable objects into hashable cache-key parts.

    ``dict`` and ``set`` / ``frozenset`` are *unordered* containers, so their
    hashable form is sorted - two structurally-equal inputs must collapse to one
    cache key regardless of source iteration order. ``list`` / ``tuple`` are
    *ordered* (a list-shaped ``Meta.fields`` defines field order), so their order
    is preserved. Both unordered branches sort by ``repr`` rather than by the
    values themselves so they stay total-ordered even for mixed,
    mutually-unorderable member or key types (e.g. ``{1, "a"}`` or
    ``{"a": 1, 0: 2}``); equal members produce equal reprs, so the canonical
    order is stable.

    Opaque values that refuse ``hash()`` (or raise from ``__hash__``) have no
    safe structural canonical form. Those land as
    ``("__unhashable_meta_value__", id(type(v)), id(v))`` so reuse of the same
    object still hits the cache while distinct objects cannot alias.
    """
    if isinstance(v, dict):
        try:
            pairs = tuple(
                (make_hashable_meta_value(key), make_hashable_meta_value(value))
                for key, value in dict.items(v)
            )
            return tuple(sorted(pairs, key=_meta_sort_key))
        except BaseException:
            return _opaque_meta_value(v)
    if isinstance(v, (set, frozenset)):
        try:
            values = (make_hashable_meta_value(item) for item in _base_meta_values(v))
            return tuple(sorted(values, key=_meta_sort_key))
        except BaseException:
            return _opaque_meta_value(v)
    if isinstance(v, (list, tuple)):
        try:
            return tuple(make_hashable_meta_value(item) for item in _base_meta_values(v))
        except BaseException:
            return _opaque_meta_value(v)
    try:
        hash(v)
    except BaseException:
        return _opaque_meta_value(v)
    return v


FILTERSET_FIELDS_ALIAS = "filter_fields"


def _set_meta_has(source: Any, key: str) -> bool:
    """Return whether a Meta class or kwargs mapping carries ``key``.

    Mappings use own-key membership (Layer-6 factory kwargs). Anything else
    uses ``hasattr`` so inherited Meta attributes count -- the
    ``FilterSetMetaclass`` contract. Switching the class path to ``__dict__``
    would promote ``filter_fields`` onto a subclass Meta that inherits
    ``fields``, which is shipped behavior this helper must not change.
    """
    if isinstance(source, dict):
        return key in source
    return hasattr(source, key)


def _set_meta_get(source: Any, key: str) -> Any:
    """Read ``key`` from a Meta class or kwargs mapping."""
    if isinstance(source, dict):
        return source[key]
    return getattr(source, key)


def resolve_set_meta_fields(source: Any, *, fields_alias: str | None = None) -> tuple[Any, bool]:
    """Return ``(fields_value, from_alias)`` under the set-family synonym rule.

    ``fields`` wins when present. Otherwise ``fields_alias``
    (``FILTERSET_FIELDS_ALIAS`` / ``filter_fields`` on FilterSet; ``None`` on
    OrderSet) is the cookbook / graphene-django synonym. ``from_alias`` is True
    only when the caller should populate ``fields`` from the synonym.

    This is the one fingerprint both set families apply so a fields
    declaration cannot mean one thing at class creation and another in the
    Layer-6 cache key. Write-back is ``promote_set_meta_fields`` (class Meta
    copies onto ``.fields`` and leaves the consumer alias in place). Dict
    alias dropping stays in ``normalize_set_meta_for_factory`` so the synonym
    cannot split a cache slot via extras. Expansion reads
    ``read_set_meta_fields`` (resolve + canonicalize, no mutation).
    """
    if source is None:
        return None, False
    if _set_meta_has(source, "fields"):
        return _set_meta_get(source, "fields"), False
    if fields_alias is not None and _set_meta_has(source, fields_alias):
        return _set_meta_get(source, fields_alias), True
    return None, False


def canonicalize_set_meta_fields(fields: Any) -> Any:
    """Return unordered ``Meta.fields`` shapes in the Layer-6 cache-stable form.

    ``set`` / ``frozenset`` become ``repr``-sorted lists so class-Meta expansion
    and factory cache keys agree across ``PYTHONHASHSEED``. Dict-shaped lookup
    bags keep key insertion order and sort set-valued lookup lists. Ordered
    ``list`` / ``tuple`` and scalar ``"__all__"`` pass through unchanged.
    """
    if isinstance(fields, (set, frozenset)):
        return _sorted_meta_values(fields)
    if isinstance(fields, dict):
        return {
            key: (_sorted_meta_values(value) if isinstance(value, (set, frozenset)) else value)
            for key, value in dict.items(fields)
        }
    return fields


def promote_set_meta_fields(source: Any, *, fields_alias: str | None = None) -> Any:
    """Resolve ``fields`` and copy an alias onto class Meta when needed.

    Returns the resolved fields value. A class Meta that supplied only
    ``fields_alias`` gets ``.fields`` written so django-filter / OrderSet
    expansion see one key; the consumer alias attribute stays in place.
    Dict sources are not mutated -- ``normalize_set_meta_for_factory`` owns
    dict promotion and alias dropping for cache keys.

    ``FilterSetMetaclass`` and ``OrderSetMetaclass`` both call this so the
    write-back rule cannot drift. OrderSet passes ``fields_alias=None`` (no
    cookbook synonym); the call is then a pure read.
    """
    fields, from_alias = resolve_set_meta_fields(source, fields_alias=fields_alias)
    if from_alias and not isinstance(source, dict):
        source.fields = fields
    return fields


def read_set_meta_fields(source: Any, *, fields_alias: str | None = None) -> Any:
    """Return resolved, cache-stable ``Meta.fields`` without mutating ``source``.

    The expansion / apply reader: ``resolve_set_meta_fields`` then
    ``canonicalize_set_meta_fields``. Class-declared ``set``-shaped fields
    therefore expand in the same order Layer-6 factory kwargs hash and store
    onto a generated Meta.
    """
    fields, _from_alias = resolve_set_meta_fields(source, fields_alias=fields_alias)
    return canonicalize_set_meta_fields(fields)


def make_set_meta_cache_key(safe_meta: dict[str, Any]) -> tuple:
    """Build a hashable ``(model, fields_key, extra)`` cache key from Meta kwargs.

    ``model`` is the primary discriminator. ``fields`` may be ``"__all__"``, a
    list of field names, or a dict mapping field -> list of lookups -- all
    serialised into a hashable form so identical declarations share a class.
    Extra meta keys ride ``make_hashable_meta_value``. Callers should pass meta
    already run through ``normalize_set_meta_for_factory`` so a fields-alias
    synonym and unordered ``set`` / ``frozenset`` shapes have been
    canonicalized; the branches below still accept those shapes directly as
    defense in depth.

    Ordered ``list`` / ``tuple`` ``fields`` preserve declaration order.
    Dict-shaped ``fields`` keys sort via ``key=repr`` so mixed,
    mutually-unorderable key types cannot ``TypeError`` the key.
    """
    if not isinstance(safe_meta, dict):
        raise ConfigurationError(
            f"Generated set metadata must be a mapping; got {_safe_type_name(safe_meta)}.",
        )
    model = dict.get(safe_meta, "model")
    fields = dict.get(safe_meta, "fields")
    if isinstance(fields, dict):
        fields_key: tuple = ("dict", make_hashable_meta_value(fields))
    elif isinstance(fields, (list, tuple)):
        fields_key = (
            "seq",
            tuple(make_hashable_meta_value(item) for item in _base_meta_values(fields)),
        )
    elif isinstance(fields, (set, frozenset)):
        fields_key = (
            "seq",
            tuple(
                sorted(
                    (make_hashable_meta_value(item) for item in _base_meta_values(fields)),
                    key=_meta_sort_key,
                ),
            ),
        )
    else:
        fields_key = ("raw", make_hashable_meta_value(fields))
    extra = make_hashable_meta_value(
        {key: value for key, value in dict.items(safe_meta) if key not in {"model", "fields"}},
    )
    return (make_hashable_meta_value(model), fields_key, extra)


def normalize_set_meta_for_factory(
    meta: dict[str, Any],
    *,
    reserved_keys: frozenset[str],
    fields_alias: str | None = None,
) -> dict[str, Any]:
    """Normalize Meta kwargs before cache keying and dynamic class creation.

    Two equivalences must collapse onto one cache slot (and one generated set
    class) or the BFS factory's duplicate-``__name__`` check fires against two
    ``<Model>Auto*`` classes that are the same declaration arrived via different
    surface shapes:

    - ``fields_alias`` (``FILTERSET_FIELDS_ALIAS`` on the filter side; ``None``
      on orders) is the metaclass synonym for ``fields``. Promotion is
      ``resolve_set_meta_fields``; this helper then drops the alias so it is
      not an extras discriminator. Unordered ``fields`` shapes then ride
      ``canonicalize_set_meta_fields`` (the same helper OrderSet expansion
      reads).
    - Top-level ``set`` / ``frozenset`` ``fields`` (and set-valued lookup bags
      under a dict-shaped ``fields``) are unordered; canonicalize them to
      ``repr``-sorted lists so cache keys and generated field order are stable
      across ``PYTHONHASHSEED``. Ordered ``list`` / ``tuple`` ``fields`` keep
      their declaration order.
    - ``exclude`` is a set of names semantically, even though django-filter
      accepts any sequence; canonicalize every list / tuple / set-shaped
      declaration to the same ``repr``-sorted list so equivalent exclusions
      cannot mint duplicate ``<Model>Auto*`` classes.
    """
    if not isinstance(meta, dict):
        raise ConfigurationError(
            f"Generated set metadata must be a mapping; got {_safe_type_name(meta)}.",
        )
    try:
        safe_meta = {key: value for key, value in dict.items(meta) if key not in reserved_keys}
    except BaseException as exc:
        raise ConfigurationError(
            "Generated set metadata entries could not be read.",
        ) from exc
    fields, from_alias = resolve_set_meta_fields(safe_meta, fields_alias=fields_alias)
    if from_alias:
        safe_meta["fields"] = fields
    if fields_alias is not None:
        # ``fields`` wins (metaclass alias rule); drop the synonym so it
        # cannot split an otherwise-identical cache slot via extras.
        safe_meta.pop(fields_alias, None)
    fields = safe_meta.get("fields")
    canonical_fields = canonicalize_set_meta_fields(fields)
    if canonical_fields is not fields:
        safe_meta["fields"] = canonical_fields
    exclude = safe_meta.get("exclude")
    if isinstance(
        exclude,
        (
            list,
            tuple,
            set,
            frozenset,
        ),
    ):
        safe_meta["exclude"] = _sorted_meta_values(exclude)
    return safe_meta


def create_dynamic_set_class(
    safe_meta: dict[str, Any],
    *,
    set_base_class: type,
    auto_name_suffix: str,
    getter_name: str,
    explicit_param: str,
) -> type:
    """Build a synthetic set-family subclass from a ``Meta`` dict.

    Replaces graphene-django's ``custom_filterset_factory`` (which the cookbook
    reaches for) with a plain ``type(name, (set_base_class,), {"Meta": meta})``
    call. Spec-027 line 247 explicitly drops the ``replace_csv_filters`` rewrap
    -- Strawberry's typed input handles ``list[T]`` natively. The order twin
    uses the same ``type(...)`` construction (no cookbook counterpart).
    """
    model = safe_meta.get("model")
    if model is None:
        raise ConfigurationError(
            f"{getter_name} requires `model` when called without an explicit "
            f"{explicit_param}; received meta without a `model` key.",
        )
    if not isinstance(model, type) or not issubclass(model, django_models.Model):
        raise ConfigurationError(
            f"{getter_name} requires `model` to be a Django model class when called "
            f"without an explicit {explicit_param}; got {model!r}.",
        )
    meta_attrs = dict(safe_meta)
    name = f"{model.__name__}{auto_name_suffix}"
    meta_class = type("Meta", (object,), meta_attrs)
    return type(name, (set_base_class,), {"Meta": meta_class})


def make_dynamic_set_getter(
    *,
    cache: dict[tuple, type],
    set_base_class: type,
    auto_name_suffix: str,
    getter_name: str,
    reserved_keys: frozenset[str],
    explicit_param: str,
    fields_alias: str | None = None,
) -> Callable[..., type]:
    """Return a Layer-6 ``get_<family>set_class`` getter over a family cache.

    Filter and order factories keep disjoint caches and base classes; this
    single-sites the lookup / normalize / key / ``type(...)`` skeleton so a
    cache-key fix cannot drift between families. ``fields_alias`` is the
    metaclass synonym (``FILTERSET_FIELDS_ALIAS`` on the filter side; ``None``
    on orders, which has no synonym) resolved by ``resolve_set_meta_fields``.
    """

    def get_set_class(explicit: type | None, **meta: Any) -> type:
        if explicit is not None:
            return explicit
        safe_meta = normalize_set_meta_for_factory(
            meta,
            reserved_keys=reserved_keys,
            fields_alias=fields_alias,
        )
        cache_key = make_set_meta_cache_key(safe_meta)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        generated = create_dynamic_set_class(
            safe_meta,
            set_base_class=set_base_class,
            auto_name_suffix=auto_name_suffix,
            getter_name=getter_name,
            explicit_param=explicit_param,
        )
        cache[cache_key] = generated
        return generated

    get_set_class.__name__ = getter_name
    get_set_class.__qualname__ = getter_name
    return get_set_class


def make_shape_build_cache() -> tuple[dict[Any, Any], Callable[[], None]]:
    """Return the ``(cache, clear_fn)`` pair for a per-shape build cache.

    The promoted plumbing the mutation + form + serializer bind caches share:
    each consuming subsystem calls this factory for a fresh ``(cache, clear_fn)``
    pair and registers ``clear_fn`` into ``registry.clear()``. This single-sites
    that pair:

    - ``cache`` - a fresh dict the bind keys on its shape identity
      (``(declaration_class, operation_kind, effective field set)`` for the
      forms / mutation flavors; the ``SerializerInputShape`` descriptor for the
      serializer flavor) so identical shapes build once.
    - ``clear_fn()`` - empties the cache (registered into ``registry.clear()`` via
      ``register_subsystem_clear`` by the CONSUMING subsystem, not here).

    Pure plumbing; no registration. This module owns the helper (and unit-tests
    it). Each flavor still owns its cache dict and its key type. The get-or-store
    walk those caches share is ``get_or_store_shape_build``.
    """
    cache: dict[Any, Any] = {}

    def clear_fn() -> None:
        cache.clear()

    return cache, clear_fn


def get_or_store_shape_build(cache: dict[Any, Any], key: Any, factory: Callable[[], Any]) -> Any:
    """Return the cached value for ``key``, storing ``factory()`` on a miss.

    The get-or-store spine the three write-flavor shape caches share:

    - model bind (``mutations/sets.py::_materialize_input_for``) keys
      ``MutationInputShape.cache_key`` and puts ``build_mutation_input`` in
      the factory so a hit never re-walks editable columns;
    - form ``cached_build_input`` keys the pre-build name-set after the
      per-declaration guard;
    - serializer ``dedupe_serializer_input_shape`` keys the post-build
      ``SerializerInputShape`` descriptor (nested opt-in and top-level bind).

    ``factory`` is how timing differs without a mode flag: a pre-build key
    puts the generator in the factory; a post-build key puts the already
    walked ``(cls, shape)`` pair in the factory (cheap). Descriptor-vs-name-set
    identity and each flavor's cache dict stay at the call site.
    """
    cached = cache.get(key)
    if cached is not None:
        return cached
    built = factory()
    cache[key] = built
    return built


def pascalize_token(name: str) -> str:
    """Encode one exact field name as one injective, leading-capital suffix token.

    Tokens contain exactly one uppercase character, at their start, so a sorted
    concatenation remains uniquely separable at uppercase boundaries. Inside a
    token, lowercase ASCII letters and digits pass through; underscores escape
    as ``_u`` and uppercase letters as ``_c<lower>``. Leading non-lowercase
    characters use distinct ``X_*`` escapes. Other Unicode characters use their
    code point. The escapes are necessary because collapsing underscores or
    lowercasing capitals maps legal distinct Django names such as ``a_b`` /
    ``ab``, ``field2_x`` / ``field2x``, and ``fooBar`` / ``foobar`` to one type
    name.

    Examples: ``category`` -> ``Category``, ``is_private`` ->
    ``Is_uprivate``, ``field_2`` -> ``Field_u2``, and ``fooBar`` ->
    ``Foo_cbar``. Retained underscores are valid GraphQL name characters, and
    ``build_strawberry_input_class`` pins the finished name explicitly.

    Promoted here from ``mutations/inputs.py`` (spec-039 P2.3 kept it sited there at
    two consumers; at three - model + form + serializer - it graduates to the shared
    input-name machinery, kept visibly distinct from ``pascal_case``). The old
    ``mutations/inputs.py::_pascalize_token`` name remains as an import alias.
    """
    if not name:
        return ""

    def _tail_char(char: str) -> str:
        if "a" <= char <= "z" or "0" <= char <= "9":
            return char
        if char == "_":
            return "_u"
        if "A" <= char <= "Z":
            return f"_c{char.lower()}"
        return f"_x{ord(char):x}_"

    first, tail = name[0], name[1:]
    if "a" <= first <= "z":
        head = first.upper()
    elif "A" <= first <= "Z":
        head = f"X_h{first.lower()}"
    elif first == "_":
        head = "X_l"
    elif "0" <= first <= "9":
        head = f"X_d{first}"
    else:
        head = f"X_z{ord(first):x}_"
    return head + "".join(_tail_char(char) for char in tail)


def generated_input_type_name(
    base_name: str,
    *,
    is_partial: bool,
    is_full_shape: bool,
    token: str,
) -> str:
    """Return a generated input-class name from its shape components.

    The load-bearing skeleton the three flavors' input-name derivers share
    (``name_set_input_type_name`` for model / form name-set shapes,
    ``rest_framework/inputs.py::serializer_input_type_name`` for descriptor
    identity): a ``PartialInput`` / ``Input`` suffix, the canonical
    ``<Base><suffix>`` for the full shape, and a deterministic
    ``<Base><token><suffix>`` for any divergent shape. Single-sited so the
    suffix rule + the full-vs-derived branching cannot drift between flavors.
    Name-set flavors compute token + full-shape via ``name_set_input_type_name``;
    the serializer still supplies its own descriptor digest and full-shape
    decision.
    """
    suffix = "PartialInput" if is_partial else "Input"
    if is_full_shape:
        return f"{base_name}{suffix}"
    return f"{base_name}{token}{suffix}"


def name_set_input_type_name(
    base_name: str,
    *,
    is_partial: bool,
    effective_field_names: tuple[str, ...],
    full_field_names: tuple[str, ...],
) -> str:
    """Return the generated input-class name for a name-set write-input shape.

    Model ``mutation_input_type_name`` and form ``form_input_type_name`` both
    name a shape from ``(owner, operation_kind, frozenset(effective names))``.
    This helper owns that shared spine: sorted-name ``pascalize_token``
    concatenation, full-vs-narrowed comparison, and ``generated_input_type_name``.

    Serializer descriptor identity stays at ``serializer_input_type_name``
    (per-field digest, not a name set). ``is_partial`` stays at each flavor
    (model ``operation_kind != CREATE``; form ``operation_kind == PARTIAL``
    because the plain-form ``FORM`` sentinel is create-shaped).
    """
    token = "".join(pascalize_token(name) for name in sorted(effective_field_names))
    return generated_input_type_name(
        base_name,
        is_partial=is_partial,
        is_full_shape=frozenset(effective_field_names) == frozenset(full_field_names),
        token=token,
    )


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
    their own ``flavor`` label (spec-038 integration; spec-039 inlined
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
    as characters); a non-string entry is rejected (it would otherwise surface as a
    confusing "unknown field" later); a duplicate name is rejected (it would
    collapse silently when the effective field set is taken as a ``frozenset``,
    masking a malformed declaration), failing loud naming the repeated field(s).
    ``label`` names which key (``fields`` / ``exclude``) is at fault; ``flavor``
    names the mutation base(s) in the message (e.g. ``"DjangoMutation"`` or
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
    non_strings = [name for name in names if not isinstance(name, str)]
    if non_strings:
        raise ConfigurationError(
            f"{flavor} Meta.{label} must be a sequence of field name strings; "
            f"got non-string entry(ies): {non_strings!r}.",
        )
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
    """Return the effective ``{name: field}`` dict after ``fields`` / ``exclude`` narrowing.

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

    def _reject_unknown(seq: Any, key: str) -> None:
        # The identical unknown-name check both branches spelled separately; the
        # pinned message stays byte-identical via the threaded ``fields`` /
        # ``exclude`` key.
        unknown = [name for name in seq if name not in basis]
        if unknown:
            raise ConfigurationError(
                f"{subject} declares `{key}` naming {unknown_noun}: {sorted(unknown)!r}.",
            )

    if fields is not None:
        _reject_unknown(fields, "fields")
        effective = {name: basis[name] for name in fields}
    elif exclude is not None:
        _reject_unknown(exclude, "exclude")
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
    """Yield ``(python_name, value, field)`` for each PROVIDED field of a bound input.

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
    triples. ``field_kwargs`` may carry ``name=`` for a GraphQL alias,
    ``default=`` for the dataclass default, and ``description=`` for the
    Strawberry field description.

    **A triple that OMITS ``default`` builds a REQUIRED field**: no class
    default is set, so ``@strawberry.input`` renders the field non-null and
    rejects an omitted value at GraphQL coercion. A bare ``None`` default
    (the prior behavior) renders non-null SDL *yet still accepts omission*,
    delivering ``None`` to the resolver and masking the missing-input error.
    An OPTIONAL field must therefore pass an explicit ``default`` -
    ``strawberry.UNSET`` for the mutation / form ``annotation | None``
    widening, ``None`` for the filter / order optional inputs (Strawberry
    tolerates a required field after a defaulted one; its inputs are
    keyword-only).

    Every field receives an explicit GraphQL name. When a triple omits ``name``,
    the package's injective ``graphql_camel_name`` result is pinned rather than
    allowing Strawberry's converter to derive a different wire name. This
    matters at underscore/digit boundaries: the package keeps ``field_2``
    distinct from ``field2``, while Strawberry's default converter maps both to
    ``field2``. Duplicate Python attrs and duplicate effective GraphQL names are
    rejected before namespace construction so a caller can never silently lose
    a field even if it misses its domain-level collision guard.

    The class is constructed via ``type(name, (), namespace)`` rather than
    ``dataclasses.make_dataclass`` because ``make_dataclass`` replaces any
    ``strawberry.field(...)`` default with a plain ``dataclasses.Field`` and
    strips the strawberry-specific metadata (the ``name=`` alias would be
    lost). Setting the ``strawberry.field`` as a class-level attribute
    alongside ``__annotations__`` preserves the metadata through the
    ``@strawberry.input`` decoration.

    The GraphQL **type** name is likewise pinned to ``name`` via
    ``strawberry.input(name=...)``. Strawberry's default type-name converter
    rewrites underscore-digit stems (``...Field_2FilterInputType`` ->
    ``...Field2filterinputtype``), which would again collide with a sibling
    ``...Field2FilterInputType`` after ``pascal_case`` has already kept the
    Python class names distinct. Pinning keeps the package's injective type
    stem on the wire.
    """
    namespace: dict[str, Any] = {"__annotations__": {}}
    seen_graphql_names: dict[str, str] = {}
    for python_attr, annotation, raw_kwargs in field_specs:
        kwargs = dict(raw_kwargs or {})
        if python_attr in namespace["__annotations__"]:
            raise ConfigurationError(
                f"Generated input {name!r} declares input attribute {python_attr!r} more than "
                "once; a later field would silently overwrite the earlier field.",
            )
        requested_name = kwargs.get("name")
        graphql_name = (
            requested_name if requested_name is not None else graphql_camel_name(python_attr)
        )
        if graphql_name in seen_graphql_names:
            prior_attr = seen_graphql_names[graphql_name]
            raise ConfigurationError(
                f"Generated input {name!r} maps input attributes {prior_attr!r} and "
                f"{python_attr!r} to the same GraphQL field name {graphql_name!r}; one would "
                "silently overwrite the other.",
            )
        kwargs["name"] = graphql_name
        seen_graphql_names[graphql_name] = python_attr
        # The PRESENCE of ``default`` (not its value) decides required-vs-optional:
        # a required field gets NO class default at all, so ``None`` is a legal
        # explicit default for an optional field rather than the required sentinel.
        has_default = "default" in kwargs
        default = kwargs.pop("default", None)
        strawberry_field_kwargs: dict[str, Any] = {"name": kwargs.pop("name")}
        if "description" in kwargs:
            strawberry_field_kwargs["description"] = kwargs.pop("description")
        namespace["__annotations__"][python_attr] = annotation
        # Every field carries a pinned ``name``, so it always gets a
        # ``strawberry.field``; pass ``default`` only when one was supplied so
        # a required field (e.g. a required FK ``categoryId``) stays non-null
        # and coercion rejects omission.
        namespace[python_attr] = (
            strawberry.field(default=default, **strawberry_field_kwargs)
            if has_default
            else strawberry.field(**strawberry_field_kwargs)
        )
    cls = type(name, (), namespace)
    return strawberry.input(cls, name=name)


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
            duplicate_name_message(
                "materialized",
                name,
                existing,
                cls,
                family_label=f"{family_label} input",
                rename_noun=family_label.lower(),
            ),
        )
    module = sys.modules[module_path]
    setattr(module, name, cls)
    ledger[name] = cls


def duplicate_name_message(
    verb: str,
    name: str,
    existing: type,
    claimant: type,
    *,
    family_label: str,
    rename_noun: str,
) -> str:
    """Build the "two distinct X claim one name" collision sentence.

    The one skeleton behind every generated-input name collision: ``{name!r} is
    {verb} by two distinct {family_label} classes: A vs B. Rename one
    {rename_noun} so its class-derived input type name is unique.`` - with the
    two ``__module__``.``__qualname__`` interpolations spelled once. The pinned
    per-site wording stays byte-stable via the threaded nouns
    (``materialize_generated_input_class`` passes ``verb="materialized"`` +
    ``family_label="<family> input"``; ``GeneratedInputArgumentsFactory``
    ``verb="claimed"`` + its configured family / rename nouns and prepends its
    factory-label head).
    """
    return (
        f"{name!r} is {verb} by two distinct {family_label} classes: "
        f"{existing.__module__}.{existing.__qualname__} vs "
        f"{claimant.__module__}.{claimant.__qualname__}. Rename one {rename_noun} "
        "so its class-derived input type name is unique."
    )


def iter_input_field_collisions(
    field_specs: list,
    *,
    subject: str,
    field_noun: str,
    rename_clause: str,
    name_of: Callable[[Any], str],
    camel_case_note: str = "",
    source_of: Callable[[Any], str] | None = None,
    check_input_attrs: bool = True,
    check_graphql_names: bool = True,
) -> Iterator[str]:
    """Yield every input-field collision message for one generated write input.

    The seen-dict walk + the collision arms behind the form and serializer
    input-attr guards, single-sited: two specs colliding on the generated
    ``input_attr`` (a relation's ``<name>_id`` remap vs a literal ``<name>_id``
    field) or on the ``graphql_name`` (default camel-casing collapse) would make
    ``build_strawberry_input_class`` / Strawberry SILENTLY drop one - so each
    collision yields a fail-loud message. The per-flavor wording stays
    byte-stable via the threaded nouns: ``subject`` (``"Form 'X'"`` /
    ``"SerializerMutation for 'X'"``), ``field_noun`` (``"form fields"`` /
    ``"serializer fields"``), ``rename_clause``, and the serializer's
    ``camel_case_note`` (the id-like-suffix parenthetical). ``name_of`` reads the
    flavor's display name off a spec (``target_name`` for form / serializer
    write inputs; ``model_field_name`` for the model mutation naming record).

    ``source_of`` enables the serializer-only third arm (two WRITABLE fields
    sharing one one-segment ``source`` would double-write one model attr); forms
    have no ``source`` axis and leave it ``None``. The form guard raises on the
    FIRST yielded message; the serializer aggregates them all - the
    consumption policy stays at each call site.

    ``check_input_attrs`` / ``check_graphql_names`` let a caller audit the two
    axes at different lifecycle points. Model mutation inputs use that split so
    an impossible relation-attr ambiguity is checked across the whole selected
    shape, while a consumer override may legitimately replace a generated
    GraphQL name before the effective wire surface is audited.
    """
    seen_attr: dict[str, str] = {}
    seen_graphql: dict[str, str] = {}
    seen_source: dict[str, str] = {}
    for spec in field_specs:
        current = name_of(spec)
        prior_attr = seen_attr.get(spec.input_attr)
        if check_input_attrs and prior_attr is not None:
            yield (
                f"{subject} generates two input fields with the same attribute "
                f"{spec.input_attr!r}: {field_noun} {prior_attr!r} and {current!r} collide "
                "(a relation field remaps to '<name>_id', clashing with a field literally "
                f"named that). {rename_clause} or drop one via Meta.fields / Meta.exclude."
            )
        prior_graphql = seen_graphql.get(spec.graphql_name)
        if check_graphql_names and prior_graphql is not None:
            yield (
                f"{subject} generates two input fields with the same GraphQL name "
                f"{spec.graphql_name!r}: {field_noun} {prior_graphql!r} and {current!r} collide "
                f"under default camel-casing{camel_case_note}. {rename_clause} or drop one via "
                "Meta.fields / Meta.exclude."
            )
        if source_of is not None:
            write_source = source_of(spec)
            prior_source = seen_source.get(write_source)
            if prior_source is not None:
                yield (
                    f"{subject} has two writable fields {prior_source!r} and {current!r} sharing "
                    f"one source {write_source!r}; they would double-write one model attribute. "
                    "Give each a distinct source, or drop one via Meta.fields / Meta.exclude."
                )
            seen_source[write_source] = current
        seen_attr[spec.input_attr] = current
        seen_graphql[spec.graphql_name] = current


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
    ``orders/__init__.py::order_input_type``. Validates
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
      than a re-spelled tuple, so the family names them in ONE place.

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
        self.input_type_name = set_input_type_name(set_class)

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

            target_name = set_input_type_name(set_cls)
            existing_owner = self._collision_registry.get(target_name)
            if existing_owner is not None and existing_owner is not set_cls:
                # The shared A3/C3 skeleton, with the factory-label head prepended
                # (byte-identical to the pre-promotion wording).
                raise ConfigurationError(
                    f"{self._factory_label}: input type name "
                    + duplicate_name_message(
                        "claimed",
                        target_name,
                        existing_owner,
                        set_cls,
                        family_label=self._family_label,
                        rename_noun=self._rename_noun,
                    ),
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
        type_name = set_input_type_name(set_cls)
        owner_definition = getattr(set_cls, "_owner_definition", None)
        triples = self._build_input_triples(set_cls, type_name, owner_definition)
        if not triples:
            # A set whose Layer-4 expansion is empty -- an ``OrderSet`` with an
            # empty / omitted ``Meta.fields`` and no active ``RelatedOrder``, or a
            # related branch that expands to nothing -- would build a zero-field
            # ``@strawberry.input``. Strawberry rejects that only at ``Schema(...)``
            # build with a raw ``ValueError: Input Object type <Name> must define
            # one or more fields``, naming the GENERATED type rather than the
            # consumer's set class. Fail loud here at the framework boundary with a
            # ``ConfigurationError`` naming the offending set + family, mirroring
            # the write-side empty-input guards (``mutations`` / ``forms`` /
            # ``rest_framework`` ``inputs.py``). The filter family never reaches
            # this branch -- its ``_build_input_triples`` always appends the
            # ``and_`` / ``or_`` / ``not_`` operator bag -- so in practice only the
            # order family (no operator bag, Spec Decision 8) can be empty; the
            # guard lives at this single set-family build site so every present and
            # future family inherits it.
            raise ConfigurationError(
                f"{self._factory_label}: {self._family_label} {set_cls.__qualname__} "
                f"generates the GraphQL input type {type_name!r} with no fields. "
                "Strawberry rejects a zero-field input object at schema build "
                f"('Input Object type {type_name} must define one or more fields'). "
                f"Declare at least one field via the {self._rename_noun}'s Meta.fields "
                "(or add a RelatedOrder / RelatedFilter branch).",
            )
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
