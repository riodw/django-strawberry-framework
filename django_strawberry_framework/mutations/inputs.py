"""Generated mutation-input namespace, the public ``FieldError`` envelope, and the payload wrapper.

This is the generation substrate for the write side (spec-036 Slice 1). It is
pure, finalizer-free machinery: given a Django model + an operation kind + an
effective field set + the resolved primary ``DjangoType``, it produces the
``<Model>Input`` / ``<Model>PartialInput`` ``@strawberry.input`` classes, the
public ``FieldError`` ``@strawberry.type``, and a generated ``<Name>Payload``
``@strawberry.type``. No metaclass, no resolver, no finalizer wiring lives here
- those are Slice 2 (``sets.py`` + the phase-2.5 bind) and Slice 3
(``resolvers.py`` + ``fields.py``). The generators here are callable and
unit-testable in isolation; Slice 2 calls them from the bind.

Generated input classes MUST become real globals of this module because
``strawberry.lazy("django_strawberry_framework.mutations.inputs")`` resolves
through ``module.__dict__`` (the same contract ``filters/inputs.py`` /
``orders/inputs.py`` rely on). The ``materialize_mutation_input_class`` /
``clear_mutation_input_namespace`` pair owns that lifecycle; Slice 2's
phase-2.5 bind is the only caller of ``materialize_mutation_input_class`` and
``registry.clear()`` is the only caller of ``clear_mutation_input_namespace``.

The materialize / build / camel-name / collision mechanics are single-sited in
``utils/inputs.py`` (the 0.0.9 DRY pass); this module is a thin domain wrapper,
in the spirit of ``orders/inputs.py`` (the ``mutations/`` module names differ
from ``orders/`` per spec-036 Decision 4). The divergence from the set families:
mutation inputs derive from one model's editable columns, not a related-set BFS,
so there is no ``GeneratedInputArgumentsFactory`` subclass and no per-set
``_lifecycle`` binding state - ``clear_mutation_input_namespace`` clears only the
module-level ledger it owns (it does NOT call ``clear_generated_input_namespace``,
which assumes a factory + a set-base ``_lifecycle``).

The scalar / relation mapping routes through the SAME read-side converters
(``types/converters.py``), so a column resolves to the identical GraphQL scalar /
enum on the read ``DjangoType`` and the write input - the wire contract is
symmetric by construction (spec-036 Decision 6).
"""

from __future__ import annotations

from typing import Any, NamedTuple

import strawberry
from django.core.exceptions import NON_FIELD_ERRORS
from django.db import models
from strawberry import relay

from ..exceptions import ConfigurationError
from ..registry import registry
from ..scalars import Upload
from ..types.converters import convert_scalar, scalar_for_field
from ..types.relay import implements_relay_node
from ..utils.inputs import (
    build_strawberry_input_class,
    graphql_camel_name,
    materialize_generated_input_class,
)
from ..utils.relations import is_forward_many_to_many

# Module path the ``strawberry.lazy(...)`` marker references; pinned as a
# single constant so any forward-ref and ``materialize_mutation_input_class``
# stay in sync. Mirrors
# ``django_strawberry_framework/orders/inputs.py::INPUTS_MODULE_PATH``.
INPUTS_MODULE_PATH: str = "django_strawberry_framework.mutations.inputs"

# The non-field error key Django's ``full_clean`` uses for model-wide
# (multi-field-constraint) errors (Django's ``"__all__"`` sentinel). Pinned here
# as the single source of truth so Slice 3's resolver keys a
# multi-field-constraint ``ValidationError`` to the same sentinel the read of
# ``error_dict`` produces (spec-036 AR-M3).
NON_FIELD_ERROR_KEY: str = NON_FIELD_ERRORS

# Operation kinds the input GENERATOR understands. ``CREATE`` honors the
# per-field required rule; ``PARTIAL`` forces every field optional (the
# ``update`` shape). The mutation ``operation`` ``Meta`` value ("create" /
# "update" / "delete") is Slice 2's namespace; the generator only distinguishes
# "build a create input" from "build a partial input".
CREATE: str = "create"
PARTIAL: str = "partial"


@strawberry.type
class FieldError:
    """A field-keyed validation error in the shared mutation error envelope.

    The single public symbol this slice exports. Every mutation flavor returns
    ``errors: list[FieldError]`` on its generated payload; a ``FieldError``
    carries a ``field`` path (a model field name, or the ``"__all__"`` sentinel
    for a model-wide / multi-field-constraint error) and the list of human
    messages for that field. Defined and frozen here (spec-036 Decision 7) so
    the form-based (0.0.12) and DRF-serializer / auth (0.0.13) flavor cards
    reuse the byte-identical type. Mirrors graphene-django's ``ErrorType``.
    """

    field: str
    messages: list[str]


# Ledger of materialized mutation-input class names. ``materialize_mutation_input_class``
# writes a ``name -> input_class`` entry; ``registry.clear()`` (wired in Slice 2)
# routes through ``clear_mutation_input_namespace`` to reset it. Module globals
# stay parked per the shared parked-globals lifecycle. Mirrors
# ``orders/inputs.py::_materialized_names`` but in a disjoint per-subsystem
# namespace.
_materialized_names: dict[str, type] = {}


def materialize_mutation_input_class(name: str, input_cls: type) -> None:
    """Set ``input_cls`` as a real module global of ``mutations.inputs`` under ``name``.

    Thin family wrapper over ``utils/inputs.py::materialize_generated_input_class``
    pinning the mutation-side module path, family label, and ledger. See that
    helper for the Strawberry ``LazyType.resolve_type`` contract, the
    ``(name, input_cls)`` idempotency clause (re-materializing the same class
    under the same name is a no-op, so identical shapes dedupe), and the
    distinct-class collision raise (a second, DIFFERENT class under one name
    raises ``ConfigurationError`` - the spec-036 AR-H1 / AR-M6 collision raise).

    Defined here; called only by Slice 2's phase-2.5 bind.
    """
    materialize_generated_input_class(
        name,
        input_cls,
        module_path=INPUTS_MODULE_PATH,
        family_label="DjangoMutation",
        ledger=_materialized_names,
    )


def clear_mutation_input_namespace() -> None:
    """Reset the mutation-input ledger for a fresh build.

    Clears ``_materialized_names`` so ``materialize_mutation_input_class``
    re-emits on the next finalize. **Materialized class objects are
    intentionally left parked** in ``mutations.inputs.__dict__`` per the shared
    parked-globals lifecycle: ``materialize_mutation_input_class`` overwrites the
    module global via ``setattr`` on the next finalize, so a parked class is
    replaced in place once the rebuild runs. Stripping it via ``delattr`` would
    break any ``strawberry.lazy(...)`` LazyType held by a consumer module whose
    autouse-reload fixture did NOT also reload the holder.

    Unlike ``orders/inputs.py::clear_order_input_namespace``, this does NOT
    delegate to ``utils/inputs.py::clear_generated_input_namespace``: that helper
    resets an arguments-factory cache and per-set ``_lifecycle`` binding state,
    and the mutation subsystem has neither (input fields come from one model's
    columns, not a related-set graph). Reuse the *pattern* (ledger-only,
    best-effort), not the helper. Slice 2 wires this into ``registry.clear()``.
    """
    _materialized_names.clear()


def editable_input_fields(
    model: type[models.Model],
    *,
    fields: tuple[str, ...] | None = None,
    exclude: tuple[str, ...] | None = None,
) -> list[models.Field]:
    """Return the model's editable, settable input columns (spec-036 Decision 6 / Medium-4).

    The write-side counterpart to ``orders/inputs.py::_get_concrete_field_names_for_order``
    - deliberately the OPPOSITE selection: writes EXCLUDE read-only timestamps
    (``editable=False`` covers ``auto_now`` / ``auto_now_add``) and INCLUDE M2M,
    where the order side does the reverse. So this is a genuinely new selector,
    not a duplication; it borrows the ``model._meta.get_fields()`` +
    ``hasattr(f, "column")`` idiom and the M2M caveat documented there.

    Kept (in declaration order): concrete editable columns whose ``editable``
    flag is ``True`` and that are not the primary key, plus forward M2M fields.
    Dropped: the primary key (Django's auto ``AutoField`` reports
    ``editable=True``, so the ``primary_key`` flag - not ``editable`` - is what
    drops it; a write never sets the pk, FK targets come via ``<field>_id``),
    every ``editable=False`` column (the ``auto_now`` / ``auto_now_add``
    timestamps and any consumer ``editable=False`` column), and reverse
    relations (no ``column`` attribute and not ``many_to_many``).

    Then narrowed by the mutation's own ``fields`` / ``exclude`` (at most one
    may be supplied; ``ConfigurationError`` names any unknown field so a typo
    fails loud rather than silently dropping a column).
    """
    if fields is not None and exclude is not None:
        raise ConfigurationError(
            f"DjangoMutation for {model.__name__} declares both `fields` and `exclude`; "
            "supply at most one.",
        )

    selected: list[models.Field] = []
    for field in model._meta.get_fields():
        if getattr(field, "many_to_many", False):
            # Forward M2M only: a forward ``ManyToManyField`` is concrete and
            # writable; an auto-created reverse M2M accessor is not.
            if is_forward_many_to_many(field):
                selected.append(field)
            continue
        # Concrete column-backed fields only (``hasattr(f, "column")`` is the
        # cookbook idiom); reverse FKs have no ``column``. Drop the pk
        # (``primary_key`` - the auto ``AutoField`` is ``editable=True``) and
        # every ``editable=False`` column (the ``auto_now`` / ``auto_now_add``
        # timestamps among them).
        if (
            hasattr(field, "column")
            and getattr(field, "editable", False)
            and not getattr(field, "primary_key", False)
        ):
            selected.append(field)

    by_name = {field.name: field for field in selected}
    if fields is not None:
        unknown = [name for name in fields if name not in by_name]
        if unknown:
            raise ConfigurationError(
                f"DjangoMutation for {model.__name__} declares `fields` naming "
                f"non-editable or unknown field(s): {sorted(unknown)!r}.",
            )
        return [by_name[name] for name in fields]
    if exclude is not None:
        unknown = [name for name in exclude if name not in by_name]
        if unknown:
            raise ConfigurationError(
                f"DjangoMutation for {model.__name__} declares `exclude` naming "
                f"non-editable or unknown field(s): {sorted(unknown)!r}.",
            )
        excluded = set(exclude)
        return [field for field in selected if field.name not in excluded]
    return selected


def input_field_required(field: models.Field) -> bool:
    """Return whether a create-input field is required (spec-036 Major-1 rule).

    A field is required **only when it has no usable default**: no Django
    ``default`` (``field.has_default()`` is ``False``), ``null=False``, and -
    where ``blank`` is a meaningful "may be omitted" signal - ``blank=False``.
    So ``description`` (``blank=True, default=""``) and ``is_private``
    (``default=False``) are OPTIONAL even in the create input, matching DRF's
    "required is derived from ``default`` / ``blank`` / ``null``" rule, while
    ``name`` / ``category_id`` stay required.

    The ``update`` / partial input forces every field optional regardless, so
    this predicate is consulted only by the create-input generator.
    """
    if field.has_default() or field.null:
        return False
    return not field.blank


def _is_relation(field: models.Field) -> bool:
    """Return whether ``field`` is a forward FK / OneToOne / M2M relation column."""
    return bool(getattr(field, "is_relation", False))


def relation_input_annotation(
    field: models.Field,
    *,
    related_primary_type: type | None,
) -> tuple[str, str, Any]:
    """Map a relation field to its ``(python_attr, graphql_name, annotation)`` triple.

    Forward FK / OneToOne become a single ``<field>_id`` input; M2M becomes
    ``list[<id>]`` (spec-036 Decision 6). The id type is ``relay.GlobalID`` when
    the related model's primary ``DjangoType`` is Relay-Node-shaped (the same
    wire-input the filter side uses for a GlobalID-shaped field), else the
    related model's raw pk scalar via ``scalar_for_field``.

    The python attr is ``<field.name>_id`` for FK / OneToOne so Slice 3's
    resolver maps it back to the column with no per-field declaration (and a
    custom ``input_class`` must follow the same scheme - spec-036 AR-M2). The
    GraphQL alias camel-cases that attr (``category_id`` -> ``categoryId``). M2M
    keeps the plain field name (``genres``) - it is already a collection of ids.

    ``related_primary_type`` is the resolved primary ``DjangoType`` of the
    related model (the Slice-2 bind looks it up via ``registry.get`` after the
    registry is fully populated); ``None`` means no primary is registered, in
    which case the raw pk scalar is used.
    """
    related_model = field.related_model
    if related_primary_type is not None and implements_relay_node(related_primary_type):
        id_scalar: Any = relay.GlobalID
    else:
        id_scalar = scalar_for_field(related_model._meta.pk)

    if getattr(field, "many_to_many", False):
        python_attr = field.name
        annotation: Any = list[id_scalar]
    else:
        python_attr = f"{field.name}_id"
        annotation = id_scalar
    graphql_name = graphql_camel_name(python_attr)
    return python_attr, graphql_name, annotation


def _scalar_input_annotation(field: models.Field, type_name: str) -> Any:
    """Return the base scalar / enum annotation for a non-relation column.

    Routes through ``convert_scalar(..., force_nullable=False)`` so the column
    resolves to the SAME scalar / choice-enum the read ``DjangoType`` synthesizes
    (a symmetric wire contract), with ``force_nullable=False`` suppressing the
    column's own ``field.null`` widening so the GENERATOR owns nullability via
    the required/optional rule (spec-036 Decision 6; the documented
    ``force_nullable`` tri-state use). A ``FileField`` / ``ImageField`` never
    reaches this helper: the caller maps it to the ``Upload`` scalar in its own
    branch (spec-037).
    """
    return convert_scalar(field, type_name, force_nullable=False)


def _pascalize_token(name: str) -> str:
    """Encode one field name as a single ``[A-Z][a-z0-9]*`` token for the input-name suffix.

    A single leading capital with a fully-lowercased tail and underscores removed
    (``is_private`` -> ``Isprivate``, ``category`` -> ``Category``). This shape is
    load-bearing for the bare-concatenation suffix in ``mutation_input_type_name``:
    because each token has NO interior capital and NO underscore, the concatenation
    of tokens is uniquely decomposable at uppercase boundaries, so distinct field
    sets never collide on one generated name.

    Not ``utils/strings.py::pascal_case`` (which collapses underscores across the
    whole name) and deliberately NOT the per-segment-capitalize form ``IsPrivate``:
    an interior capital would make ``IsPrivate`` ambiguously re-decompose as the two
    fields ``is`` + ``private``, which is the exact collision this guards against
    (``("a_b", "c")`` -> ``AbC`` vs ``("a", "b_c")`` -> ``ABc``, distinct). It also
    stays underscore-free so Strawberry's GraphQL name converter leaves a
    PascalCase class name unchanged (an underscore would be mangled into a lowercased
    segment tail in the GraphQL type name).
    """
    return name.replace("_", "").capitalize()


def mutation_input_type_name(
    model: type[models.Model],
    operation_kind: str,
    effective_field_names: tuple[str, ...],
    *,
    full_field_names: tuple[str, ...],
) -> str:
    """Return the generated input-class name for a shape (spec-036 AR-H1 / AR-M6).

    The canonical full editable shape takes the stable ``<Model>Input`` /
    ``<Model>PartialInput`` name; a narrowed shape (``Meta.fields`` /
    ``Meta.exclude``) takes a deterministic shape-derived name so two NARROWINGS
    to the same effective field set produce the same name (dedupe via the
    materialize ledger) while a different shape produces a different name.

    Identity is ``(model, operation_kind, frozenset(effective_field_names))``.
    The narrowed-shape suffix is the sorted-field-name tokens concatenated, each
    token a single-leading-capital ``[A-Z][a-z0-9]*`` form (``_pascalize_token``).
    That token shape makes the bare concatenation INJECTIVE per field set: with no
    interior capital and no underscore in any token, the concatenation decomposes
    uniquely at uppercase boundaries, so ``("a_b", "c")`` -> ``AbC`` and
    ``("a", "b_c")`` -> ``ABc`` produce DISTINCT names (the per-segment-capitalize
    form would collapse both onto ``ABC``, colliding on the generated GraphQL type
    name and tripping the AR-M6 distinct-shape raise at materialize). The full shape
    is detected by comparing the effective set against ``full_field_names`` (the
    complete editable set for the model), so a ``Meta.fields`` that happens to
    name every editable column still resolves to the canonical name.
    """
    base = model.__name__
    suffix = "Input" if operation_kind == CREATE else "PartialInput"
    if frozenset(effective_field_names) == frozenset(full_field_names):
        return f"{base}{suffix}"
    token = "".join(_pascalize_token(name) for name in sorted(effective_field_names))
    return f"{base}{token}{suffix}"


class MutationInputShape(NamedTuple):
    """The single derived identity of a generated input shape (spec-036 Decision 6 / DRY-1).

    Bundles every value that derives from the shape identity tuple ``(model,
    operation_kind, frozenset(effective field names))`` so the generator, the
    bind cache, and the merge path all read ONE computation instead of each
    re-walking ``editable_input_fields`` and reassembling the name / key
    independently (the DRY-1 drift point: a divergent re-spelling could make the
    bind cache key disagree with the generated type name).

    - ``selected`` - the selected editable ``models.Field`` objects (narrowed by
      ``fields`` / ``exclude``), in declaration order, the generator emits from.
    - ``full_field_names`` - the model's COMPLETE editable field-name set (the
      canonical-vs-narrowed comparison basis for the name).
    - ``effective_field_names`` - ``frozenset`` of the selected names (the
      identity component + cache-key component).
    - ``type_name`` - the generated GraphQL/class name (canonical ``<Model>Input``
      for the full shape, deterministic shape-derived name when narrowed).
    - ``cache_key`` - ``(model, operation_kind, effective_field_names)``, the
      ``_shape_build_cache`` key the bind dedupes identical shapes on.
    """

    model: type[models.Model]
    operation_kind: str
    selected: tuple[models.Field, ...]
    full_field_names: tuple[str, ...]
    effective_field_names: frozenset[str]
    type_name: str
    cache_key: tuple[Any, ...]


def mutation_input_shape(
    model: type[models.Model],
    operation_kind: str,
    *,
    fields: tuple[str, ...] | None = None,
    exclude: tuple[str, ...] | None = None,
) -> MutationInputShape:
    """Compute the one shape descriptor the generator + bind + merge all consume (DRY-1).

    Single-sources the editable-field walk (``editable_input_fields`` for the
    selected set AND the full set), the effective-name frozenset, the generated
    ``type_name`` (via ``mutation_input_type_name``), and the
    ``_shape_build_cache`` key. ``build_mutation_input`` calls this for its
    selected fields + name; ``mutations/sets.py``'s bind calls it for the cache key
    and the merged-input name - so the name, the key, and the spec identity tuple
    can never drift apart.
    """
    selected = tuple(editable_input_fields(model, fields=fields, exclude=exclude))
    full_field_names = tuple(field.name for field in editable_input_fields(model))
    effective_field_names = frozenset(field.name for field in selected)
    type_name = mutation_input_type_name(
        model,
        operation_kind,
        tuple(field.name for field in selected),
        full_field_names=full_field_names,
    )
    return MutationInputShape(
        model=model,
        operation_kind=operation_kind,
        selected=selected,
        full_field_names=full_field_names,
        effective_field_names=effective_field_names,
        type_name=type_name,
        cache_key=(model, operation_kind, effective_field_names),
    )


def build_mutation_input(
    model: type[models.Model],
    *,
    operation_kind: str,
    primary_type: type,
    fields: tuple[str, ...] | None = None,
    exclude: tuple[str, ...] | None = None,
    overrides: frozenset[str] | None = None,
    shape: MutationInputShape | None = None,
) -> type:
    """Build the ``<Model>Input`` / ``<Model>PartialInput`` ``@strawberry.input`` class.

    ``operation_kind`` is ``CREATE`` (honor the per-field required rule) or
    ``PARTIAL`` (force every field optional). ``primary_type`` is the model's
    resolved primary ``DjangoType`` (threaded for call-site symmetry; the
    relation-id strategy resolves the RELATED model's primary inside
    ``relation_input_annotation`` via the registry at bind time).

    ``overrides`` names python attrs a consumer ``input_class`` supplies
    (spec-036 relation-override / spec-010 contract): a column whose generated
    python attr is in ``overrides`` is SKIPPED so the consumer-authored field is
    honored, not clobbered. ``mutations/sets.py`` wires it from
    ``Meta.input_class`` / ``Meta.partial_input_class``; a direct caller may pass
    it explicitly. File/image columns now participate in this skip like any
    scalar (spec-037 lifted the spec-036 CR-6 carve-out).

    ``shape`` is the precomputed ``MutationInputShape`` (DRY-1): the bind passes
    the one it already computed for the cache key so the selected fields + type
    name are not re-walked; a direct caller omits it and it is derived from
    ``(model, operation_kind, fields, exclude)``. Either way the selected set and
    the generated name come from the SAME ``mutation_input_shape`` computation.

    Returns an UNMATERIALIZED ``@strawberry.input`` class. Slice 2's phase-2.5
    bind calls ``materialize_mutation_input_class`` to pin it as a module global.
    """
    del primary_type  # reserved: relation-id strategy resolves the RELATED primary itself.
    is_create = operation_kind == CREATE
    if shape is None:
        shape = mutation_input_shape(model, operation_kind, fields=fields, exclude=exclude)
    selected = shape.selected
    type_name = shape.type_name
    overrides = overrides or frozenset()

    triples: list[tuple[str, Any, dict[str, Any]]] = []
    for field in selected:
        if _is_relation(field):
            python_attr, graphql_name, annotation = relation_input_annotation(
                field,
                related_primary_type=registry.get(field.related_model),
            )
        elif isinstance(field, (models.FileField, models.ImageField)):
            # A ``FileField`` / ``ImageField`` maps to Strawberry's ``Upload``
            # scalar (spec-037), NOT the read-side ``str`` (``SCALAR_MAP``
            # stays ``str`` for the filter-input path only). A file/image column is a
            # SCALAR input, so the python attr is the plain field name (never
            # ``<name>_id`` - that is the FK relation scheme). The triple falls
            # through to the SAME override-skip / requiredness / ``| None``-widening
            # machinery the scalar branch uses below, which lifts the spec-036 CR-6
            # carve-out (the old ``NotImplementedError`` preceded the override skip,
            # so file columns could not participate in the ``Meta.input_class`` merge
            # override; now they do, like any scalar).
            python_attr = field.name
            graphql_name = graphql_camel_name(python_attr)
            annotation = Upload
        else:
            python_attr = field.name
            graphql_name = graphql_camel_name(python_attr)
            annotation = _scalar_input_annotation(field, type_name)

        if python_attr in overrides:
            continue

        # M2M is ALWAYS optional, even in the create input: a parent row cannot
        # carry M2M rows until it has a pk, and Slice 3's resolver contract is
        # "replace-on-provide / clear-on-empty / unchanged-on-omit" (AR-M1) -
        # which requires the M2M input to be omittable. The per-field required
        # rule (``input_field_required``) is meaningless for M2M (a forward M2M
        # always reports ``null=False, blank=False, has_default()=False``), so it
        # is consulted only for scalar / FK columns.
        is_m2m = getattr(field, "many_to_many", False)
        required = is_create and not is_m2m and input_field_required(field)
        field_kwargs: dict[str, Any] = {}
        if python_attr != graphql_name:
            field_kwargs["name"] = graphql_name
        if not required:
            annotation = annotation | None
            field_kwargs["default"] = strawberry.UNSET
        triples.append((python_attr, annotation, field_kwargs))

    if not triples and not overrides:
        # An empty effective field set (``Meta.fields = ()``, an ``exclude`` that
        # drops every editable column, or a model with no editable columns) would
        # build an empty ``@strawberry.input``, which Strawberry rejects only at
        # ``Schema(...)`` build with a raw ``ValueError: Input Object type
        # <Name> must define one or more fields.`` Fail loud here as a framework
        # ``ConfigurationError`` naming the mutation's model, before the schema
        # build (spec-036 - empty input must fail at the framework boundary). A
        # consumer ``input_class`` supplying field(s) keeps ``overrides`` non-empty,
        # so a merged input whose generated remainder is empty is NOT rejected.
        kind = "create" if operation_kind == CREATE else "update"
        raise ConfigurationError(
            f"DjangoMutation {kind} input for {model.__name__} has no fields; "
            "Meta.fields / Meta.exclude narrowed the editable column set to empty "
            "(or the model declares no editable columns). A mutation input must "
            "define at least one field.",
        )
    return build_strawberry_input_class(type_name, triples)


def payload_object_slot(primary_type: type) -> str:
    """Return the uniform payload object-slot name for a primary type (spec-036 AR-H5).

    ``"node"`` for a Relay-Node-shaped primary type, ``"result"`` otherwise.
    Single-sited so the payload builder and Slice 3's resolver agree on the slot
    without re-deriving the Relay check.
    """
    return "node" if implements_relay_node(primary_type) else "result"


def build_payload_type(mutation_name: str, *, object_type: type, object_slot: str) -> type:
    """Build the ``<Name>Payload`` ``@strawberry.type`` wrapper (spec-036 Decision 7).

    ``object_slot`` is the UNIFORM object-field name from
    ``payload_object_slot(primary_type)`` - ``"node"`` for a Relay-Node target,
    ``"result"`` otherwise (AR-H5). It is NEVER model-derived, so a ``Property``
    payload exposes ``node`` / ``result``, never a ``property``-named field.

    Fields: ``<object_slot>: object_type | None`` (nullable - ``null`` on a
    validation failure) and ``errors: list[FieldError]`` (the non-null list of
    non-null ``FieldError`` the spec writes ``[FieldError!]!``). ``object_type``
    is referenced directly: by the time Slice 2's phase-2.5 bind calls this, the
    read ``DjangoType`` is a real class, so a direct ``object_type | None``
    annotation resolves at schema build (the genuine import-time forward-ref
    hazard is the ``DjangoMutationField`` resolver return, Slice 3's concern).
    """
    namespace: dict[str, Any] = {
        "__annotations__": {object_slot: object_type | None, "errors": list[FieldError]},
        object_slot: None,
        "errors": strawberry.field(default_factory=list),
    }
    cls = type(f"{mutation_name}Payload", (), namespace)
    return strawberry.type(cls)
