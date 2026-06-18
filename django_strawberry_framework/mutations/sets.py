"""``DjangoMutation`` base + metaclass + ``Meta`` validation + the phase-2.5 bind (spec-036 Slice 2).

The write-side declarative surface, in the spirit of ``filters/sets.py`` /
``orders/sets.py`` (a base class with a nested ``class Meta``, never a decorator -
spec-036 Decision 3 / START.md). This module owns four concerns:

- ``DjangoMutation`` - the consumer-facing base. A concrete subclass declares a
  nested ``Meta`` (``model`` + ``operation`` + optional ``input_class`` /
  ``partial_input_class`` / ``fields`` / ``exclude`` / ``permission_classes``);
  the metaclass validates it at class creation and registers the declaration.
- ``DjangoMutationMetaclass`` - collects + validates ``Meta`` at class creation
  and registers the concrete subclass (the abstract base carries no ``Meta`` and
  is skipped, the same in-flight-base-class guard the set metaclasses rely on).
- the declaration registry (``register_mutation`` / ``clear_mutation_registry`` /
  ``iter_mutations``) the finalizer bind drains. ``register_mutation`` rejects a
  late declaration after ``registry.mark_finalized()`` (spec-036 Edge cases).
- ``bind_mutations()`` - the phase-2.5 entry point the finalizer calls. For each
  registered mutation it resolves the model's primary ``DjangoType`` (spec-036
  Decision 11), builds + materializes the generated ``Input`` / ``PartialInput``
  classes (``create`` / ``update``) and the ``<Name>Payload`` (every operation)
  as module globals of ``mutations.inputs`` before ``strawberry.Schema(...)`` runs
  (spec-036 Decision 12), raising ``ConfigurationError`` on a no-primary target or
  a duplicate generated GraphQL name (spec-036 AR-M6).

Deliberate divergence from ``_bind_sidecar_sets`` (spec-036 Decision 5): a
``DjangoMutation`` is NOT a ``DjangoType`` sidecar (it has its own ``Meta.model``,
not a ``DjangoType``-definition attr like ``orderset_class``), so the bind iterates
the **mutation-declaration registry**, not ``registry.iter_definitions()``. It is a
sibling of ``_bind_filtersets`` / ``_bind_ordersets`` at the *placement* level
(same phase-2.5 window), not a ``_bind_sidecar_sets`` consumer.

The mutation ``Meta`` is its OWN validation namespace, disjoint from the
``DjangoType`` ``Meta`` (spec-036 Decision 12): this module defines its own
allowed-key set and does NOT import / extend ``types/base.py``'s
``ALLOWED_META_KEYS`` / ``DEFERRED_META_KEYS`` (which stay byte-unchanged).

**No resolver, no ``DjangoMutationField``, no permission *enforcement* lands
here.** Those are Slice 3 (``resolvers.py`` + ``fields.py``). A ``DjangoMutation``
declared in this slice is inert: registered + bound at finalize, never resolved.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..exceptions import ConfigurationError
from ..registry import registry
from .inputs import (
    CREATE,
    PARTIAL,
    build_mutation_input,
    build_payload_type,
    editable_input_fields,
    materialize_mutation_input_class,
    payload_object_slot,
    relation_input_annotation,
)
from .permissions import DjangoModelPermission

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import.
    from django.db import models

# The mutation ``Meta``'s own allowed-key set (spec-036 Slice 2 line 53 +
# Decision 12). Disjoint from ``types/base.py::ALLOWED_META_KEYS``: a mutation
# ``Meta`` is the mutation class's own namespace, so this set is defined here and
# the ``DjangoType`` sets stay byte-unchanged.
_ALLOWED_MUTATION_META_KEYS: frozenset[str] = frozenset(
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

# The three valid ``Meta.operation`` values (spec-036 Decision 5). Single source
# of truth: Slice 3's resolver imports this rather than re-spelling the set.
_VALID_OPERATIONS: frozenset[str] = frozenset({"create", "update", "delete"})

# ``operation`` -> input-generator kind. ``create`` builds the required-aware
# ``<Model>Input`` (``CREATE``); ``update`` builds the all-optional
# ``<Model>PartialInput`` (``PARTIAL``); ``delete`` is ``id:``-only and needs no
# input (spec-036 Decision 14). The bind reads this to know which input(s) to
# materialize per operation.
_OPERATION_INPUT_KIND: dict[str, str] = {"create": CREATE, "update": PARTIAL}


# Declaration registry: every concrete ``DjangoMutation`` records itself here at
# class creation; ``bind_mutations`` drains it at phase 2.5 and
# ``registry.clear()`` resets it via ``clear_mutation_registry`` (wired in this
# slice). A list keeps registration order deterministic; identity dedup keeps a
# re-imported class from double-registering (the set-ledger idempotency contract).
_mutation_registry: list[type] = []

# Per-finalize-pass build cache keyed by generated-input shape identity
# (``(model, operation_kind, frozenset(effective field names))``, spec-036
# Decision 6 line 334). The key is the EFFECTIVE field set, NOT the raw
# ``(fields, exclude)`` declaration: two declarations that resolve to the same
# effective shape via different ``fields`` / ``exclude`` spellings (e.g.
# ``fields=("name",)`` vs the complementary ``exclude=(<the rest>)``, or a
# ``fields`` list naming the full editable set vs an un-narrowed create) must
# dedupe to one type (spec-036 Edge cases line 509). Keying on the effective set
# mirrors ``mutations.inputs.mutation_input_type_name``'s identity tuple and its
# name derivation, so the cache key, the generated name, and the spec identity are
# single-sourced and cannot drift - two mutations with the same effective shape
# reuse one class object so the materialize ledger dedupes idempotently instead of
# seeing two distinct same-named classes. ``bind_mutations`` clears it at the start
# of each pass so a stale class from a prior (failed or re-run) finalize never leaks.
_shape_build_cache: dict[tuple, type] = {}


def register_mutation(mutation_cls: type) -> None:
    """Record a concrete ``DjangoMutation`` for the phase-2.5 bind.

    Idempotent by identity: a class re-imported under a module reload is recorded
    once. Rejects a declaration after ``registry.mark_finalized()`` /
    ``finalize_django_types()`` (spec-036 Edge cases) - the bind has already run,
    so a late mutation would never be materialized; failing loud mirrors
    ``TypeRegistry._check_mutable``.
    """
    if registry.is_finalized():
        raise ConfigurationError(
            f"Cannot declare DjangoMutation {mutation_cls.__name__} after finalization; "
            "mutation declarations are import-time only (call registry.clear() first).",
        )
    if mutation_cls not in _mutation_registry:
        _mutation_registry.append(mutation_cls)


def clear_mutation_registry() -> None:
    """Drop every registered mutation declaration (the ``registry.clear()`` co-clear hook).

    Wired into ``TypeRegistry.clear`` so a fresh finalize starts with an empty
    declaration registry and ``iter_mutations()`` yields nothing until new
    mutations declare. Mirrors the filter / order helper-ledger ``.clear()``.
    """
    _mutation_registry.clear()


def iter_mutations() -> tuple[type, ...]:
    """Return every registered mutation declaration in registration order."""
    return tuple(_mutation_registry)


def _validate_input_class(
    mutation_name: str,
    input_class: Any,
    *,
    attr_name: str,
    model: type[models.Model],
    fields: tuple[str, ...] | None,
    exclude: tuple[str, ...] | None,
) -> None:
    """Validate a consumer ``input_class`` / ``partial_input_class`` (spec-036 AR-M2).

    Two checks (spec-036 Decision 5 error-shapes + Decision 6 line 336 / AR-M2):

    1. It is a ``@strawberry.input``-decorated type - a class carrying
       ``__strawberry_definition__`` with ``is_input`` True. A plain class or a
       non-class value raises ``ConfigurationError``.
    2. Its field names do not diverge from the generated naming scheme. The scheme
       is single-sourced with the generator: the expected python-attr set is
       ``editable_input_fields(model, ...)`` mapped through the SAME
       ``relation_input_annotation`` the generator uses (``<field>_id`` for
       forward FK / OneToOne, the plain field name for a scalar / M2M), so the
       validator's notion of "the scheme" cannot drift from
       ``build_mutation_input``. A field whose python-name is not in that set
       raises ``ConfigurationError`` naming the divergence + the expected scheme.
    """
    definition = getattr(input_class, "__strawberry_definition__", None)
    if definition is None or not getattr(definition, "is_input", False):
        raise ConfigurationError(
            f"DjangoMutation {mutation_name}.Meta.{attr_name} must be a "
            f"@strawberry.input-decorated type; got {input_class!r}.",
        )

    expected = _expected_input_attr_names(model, fields=fields, exclude=exclude)
    supplied = {field.python_name for field in definition.fields}
    diverging = sorted(supplied - expected)
    if diverging:
        raise ConfigurationError(
            f"DjangoMutation {mutation_name}.Meta.{attr_name} declares field(s) "
            f"{diverging!r} that diverge from the generated naming scheme "
            f"(scalars use the model field name, forward FK/OneToOne use "
            f"`<field>_id`, M2M uses the field name). Expected names: "
            f"{sorted(expected)!r}.",
        )


def _expected_input_attr_names(
    model: type[models.Model],
    *,
    fields: tuple[str, ...] | None,
    exclude: tuple[str, ...] | None,
) -> set[str]:
    """Return the python-attr set the generator would emit for ``model`` (spec-036 AR-M2).

    Single-sourced with ``build_mutation_input`` via ``editable_input_fields`` +
    ``relation_input_annotation`` so a custom ``input_class``'s accepted names
    cannot drift from what the generator actually produces. The id-type lookup
    inside ``relation_input_annotation`` is irrelevant to the python-attr (which
    is ``<field>_id`` / the field name regardless of GlobalID-vs-pk), so the
    related-primary argument is passed ``None``.
    """
    names: set[str] = set()
    for field in editable_input_fields(model, fields=fields, exclude=exclude):
        if getattr(field, "is_relation", False):
            python_attr, _graphql_name, _annotation = relation_input_annotation(
                field,
                related_primary_type=None,
            )
            names.add(python_attr)
        else:
            names.add(field.name)
    return names


class _ValidatedMutationMeta:
    """The validated ``Meta`` snapshot the metaclass stashes on a concrete mutation.

    A flat record (not a dataclass, to stay dependency-light) the bind and Slice
    3's resolver read instead of re-walking the raw ``Meta``. Mirrors
    ``types/base.py::_ValidatedMeta`` in role: validation happens once at class
    creation, then every downstream reader trusts this snapshot.
    """

    __slots__ = (
        "exclude",
        "fields",
        "input_class",
        "model",
        "operation",
        "partial_input_class",
        "permission_classes",
    )

    def __init__(
        self,
        *,
        model: type[models.Model],
        operation: str,
        input_class: Any,
        partial_input_class: Any,
        fields: tuple[str, ...] | None,
        exclude: tuple[str, ...] | None,
        permission_classes: list[Any],
    ) -> None:
        self.model = model
        self.operation = operation
        self.input_class = input_class
        self.partial_input_class = partial_input_class
        self.fields = fields
        self.exclude = exclude
        self.permission_classes = permission_classes


def _normalize_field_sequence(value: Any) -> tuple[str, ...] | None:
    """Return ``Meta.fields`` / ``Meta.exclude`` as a tuple of names, or ``None``.

    ``None`` means "unset". A non-``None`` value is coerced to a tuple so the
    bind and the generator see one shape (``editable_input_fields`` accepts a
    tuple). A bare string is a common mistake (it would iterate as characters),
    so it is rejected here at class creation.
    """
    if value is None:
        return None
    if isinstance(value, str):
        raise ConfigurationError(
            "DjangoMutation Meta.fields / Meta.exclude must be a sequence of field "
            f"names, not a bare string: {value!r}.",
        )
    return tuple(value)


def _validate_mutation_meta(mutation_cls: type, meta: type) -> _ValidatedMutationMeta:
    """Validate a concrete mutation's nested ``Meta`` at class creation (spec-036 Decision 5).

    The validation matrix (raising ``ConfigurationError`` naming the offending
    key, all at class-creation per Slice 2 line 53):

    - **unknown ``Meta`` key** - the typo guard over ``_ALLOWED_MUTATION_META_KEYS``
      (own keys only, no MRO walk), mirroring ``types/base.py::_validate_meta``.
    - **no resolvable model** - ``_resolve_model(meta)`` returns ``None`` (in
      0.0.11 a missing ``Meta.model``; the seam lets the 0.0.12 / 0.0.13 flavors
      supply it differently).
    - **bad ``operation``** - missing or not in ``{"create", "update", "delete"}``.
    - **``fields`` + ``exclude`` both supplied** - mutual exclusion.
    - **bad ``input_class`` / ``partial_input_class``** - not a ``@strawberry.input``
      type, or field names diverging from the generated scheme (AR-M2).

    ``permission_classes`` defaults to ``[DjangoModelPermission]`` when unset
    (spec-036 Decision 15 - the write-auth seam default is assigned here; the
    enforcement runs in Slice 3's resolver).
    """
    name = mutation_cls.__name__
    declared = {key for key in vars(meta) if not key.startswith("_")}
    unknown = sorted(declared - _ALLOWED_MUTATION_META_KEYS)
    if unknown:
        raise ConfigurationError(f"DjangoMutation {name}.Meta has unknown keys: {unknown}.")

    model = mutation_cls._resolve_model(meta)
    if model is None:
        raise ConfigurationError(
            f"DjangoMutation {name}.Meta declares no resolvable model; set Meta.model.",
        )

    operation = getattr(meta, "operation", None)
    if operation not in _VALID_OPERATIONS:
        raise ConfigurationError(
            f"DjangoMutation {name}.Meta.operation must be one of "
            f"{sorted(_VALID_OPERATIONS)}; got {operation!r}.",
        )

    fields = _normalize_field_sequence(getattr(meta, "fields", None))
    exclude = _normalize_field_sequence(getattr(meta, "exclude", None))
    if fields is not None and exclude is not None:
        raise ConfigurationError(
            f"DjangoMutation {name}.Meta declares both `fields` and `exclude`; "
            "supply at most one.",
        )

    input_class = getattr(meta, "input_class", None)
    if input_class is not None:
        _validate_input_class(
            name,
            input_class,
            attr_name="input_class",
            model=model,
            fields=fields,
            exclude=exclude,
        )
    partial_input_class = getattr(meta, "partial_input_class", None)
    if partial_input_class is not None:
        _validate_input_class(
            name,
            partial_input_class,
            attr_name="partial_input_class",
            model=model,
            fields=fields,
            exclude=exclude,
        )

    permission_classes = getattr(meta, "permission_classes", None)
    if permission_classes is None:
        permission_classes = [DjangoModelPermission]

    return _ValidatedMutationMeta(
        model=model,
        operation=operation,
        input_class=input_class,
        partial_input_class=partial_input_class,
        fields=fields,
        exclude=exclude,
        permission_classes=permission_classes,
    )


class DjangoMutationMetaclass(type):
    """Collect + validate a concrete ``DjangoMutation``'s ``Meta`` and register it.

    Mirrors ``OrderSetMetaclass.__new__`` in shape (build the class via
    ``super().__new__``, then read the class body), but the body is ``Meta``
    validation + declaration registration rather than related-declaration
    collection. The abstract base ``DjangoMutation`` (no ``Meta``) is skipped -
    the same in-flight-base-class guard the set metaclasses rely on - so only
    concrete subclasses validate + register.
    """

    def __new__(
        cls: type[DjangoMutationMetaclass],
        name: str,
        bases: tuple,
        attrs: dict,
    ) -> DjangoMutationMetaclass:
        """Build the class; for a concrete subclass, validate ``Meta`` and register it."""
        new_class = super().__new__(cls, name, bases, attrs)
        meta = attrs.get("Meta")
        if meta is None:
            # The abstract base ``DjangoMutation`` (or an intermediate base) with
            # no nested ``Meta`` is not a concrete mutation: skip validation /
            # registration, exactly as the set metaclasses skip their bases.
            return new_class
        new_class._mutation_meta = _validate_mutation_meta(new_class, meta)
        register_mutation(new_class)
        return new_class


class DjangoMutation(metaclass=DjangoMutationMetaclass):
    """Consumer-facing write-side base class (spec-036 Decision 3 / Decision 5).

    A concrete mutation declares a nested ``class Meta`` with ``model`` +
    ``operation`` (and optional ``input_class`` / ``partial_input_class`` /
    ``fields`` / ``exclude`` / ``permission_classes``); the metaclass validates it
    at class creation and registers it for the phase-2.5 bind. Uniform with
    ``DjangoType`` / ``FilterSet`` / ``OrderSet`` - a base class with a nested
    ``Meta``, never a decorator.

    In Slice 2 a declared mutation is **inert**: registered + bound at finalize
    (its generated ``Input`` / ``PartialInput`` / ``<Name>Payload`` classes are
    materialized), but never resolved. The resolver pipeline + the
    ``DjangoMutationField`` factory + permission *enforcement* are Slice 3.
    """

    # The validated ``Meta`` snapshot the metaclass stashes on a concrete
    # subclass; the bind and Slice 3's resolver read it. ``None`` on the abstract
    # base (which carries no ``Meta``).
    _mutation_meta: _ValidatedMutationMeta | None = None

    # Bind outputs (forward-compat plumbing for Slice 3). The phase-2.5 bind
    # stashes the resolved primary type, the materialized input class (create /
    # update; ``None`` for delete), and the materialized payload class name here;
    # ``DjangoMutationField`` reads them to synthesize the resolver signature +
    # the ``strawberry.lazy`` payload return-ref. Left ``None`` until the bind runs.
    _primary_type: type | None = None
    _input_class: type | None = None
    _payload_type_name: str | None = None

    @classmethod
    def _resolve_model(cls, meta: type) -> type[models.Model] | None:
        """Resolve the mutation's Django model from ``Meta`` (the Medium-5 seam).

        In 0.0.11 the only source is ``Meta.model``. This is the overridable hook
        the 0.0.12 form flavor (``Meta.form_class._meta.model``) and the 0.0.13
        serializer flavor (``Meta.serializer_class.Meta.model``) replace so they
        supply the model WITHOUT a literal ``Meta.model``, without re-opening the
        base validation (spec-036 Decision 5). A subclass overrides this
        classmethod to change the resolved model.
        """
        return getattr(meta, "model", None)

    def check_permission(
        self,
        info: Any,
        operation: str,
        data: Any,
        instance: Any = None,
    ) -> bool:
        """Return whether the request is authorized for ``operation`` (spec-036 Decision 15).

        The imperative override point: a subclass redefines this to replace /
        extend the class-based check. The default delegates to every
        ``Meta.permission_classes`` entry, returning ``False`` as soon as one
        denies and ``True`` only when all allow. Slice 3's resolver maps a ``False``
        return to a raised ``GraphQLError`` (the top-level authorization failure,
        distinct from the field-keyed validation envelope).

        **Defined here; not invoked in Slice 2.** Slice 3's resolver calls this at
        the pipeline placement spec-036 Decision 8 step 3 / Decision 15 pins
        (before the write for ``create``; after the visibility lookup for
        ``update`` / ``delete``). Slice 2 ships only the default method body + the
        ``permission_classes`` default assignment; the resolver that raises on
        denial is Slice 3.
        """
        meta = type(self)._mutation_meta
        for permission_class in meta.permission_classes:
            if not permission_class().has_permission(
                info,
                type(self),
                operation,
                data,
                instance,
            ):
                return False
        return True


def _resolve_primary_type(mutation_cls: type, model: type[models.Model]) -> type:
    """Resolve ``model``'s primary ``DjangoType`` for a mutation, or raise (spec-036 Decision 11).

    Distinguishes the two finalize-time error cases (spec-036 Error shapes):

    - **no registered type at all** (``types_for(model)`` empty) -> "no type to
      return" - the return payload + relation-id strategy cannot be resolved.
    - **multiple types, no declared primary** (``get`` returns ``None`` but
      ``types_for`` is non-empty) -> the ``Meta.primary`` ambiguity error.

    ``registry.get`` returning ``None`` does not distinguish them, so ``types_for``
    is consulted to phrase the right message. (A model with multiple types and no
    primary already fails the Phase-1 ``_audit_primary_ambiguity`` upstream, but
    the bind raises its own clear message for the zero-type case and stays robust
    if the model reaches the bind unaudited.)
    """
    primary = registry.get(model)
    if primary is not None:
        return primary
    if registry.types_for(model):
        raise ConfigurationError(
            f"DjangoMutation {mutation_cls.__name__} targets {model.__name__}, which has "
            "multiple registered DjangoTypes and no declared primary; set Meta.primary on "
            "one of them so the mutation return type is unambiguous.",
        )
    raise ConfigurationError(
        f"DjangoMutation {mutation_cls.__name__} targets {model.__name__}, which has no "
        "registered DjangoType; the mutation has no type to return. Declare a "
        f"DjangoType for {model.__name__}.",
    )


def _materialize_input_for(meta: _ValidatedMutationMeta, primary_type: type) -> type | None:
    """Build + materialize the operation's input class, or return ``None`` for ``delete``.

    ``create`` builds the ``<Model>Input`` (``CREATE`` kind); ``update`` builds the
    ``<Model>PartialInput`` (``PARTIAL`` kind); ``delete`` is ``id:``-only and
    needs no input (spec-036 Decision 14). A consumer ``input_class`` /
    ``partial_input_class`` substitutes for the generated one (already validated
    at class creation); its field names are passed to ``build_mutation_input`` as
    ``overrides`` so the generated columns it supplies are skipped (the spec-010
    relation-override contract).

    Identical generated shapes dedupe to one class object: the shape identity is
    ``(model, operation kind, frozenset(effective field names))`` (spec-036
    Decision 6). The first mutation with a given shape builds + caches the class in
    ``_shape_build_cache``; a later mutation with the identical shape reuses that
    cached object, so ``materialize_mutation_input_class`` sees the SAME class
    twice and dedupes idempotently (rather than a fresh, name-colliding object). A
    consumer ``input_class`` is materialized under its consumer-chosen name, so a
    clash with a different shape's name still raises the AR-M6 custom-input
    collision.
    """
    operation_kind = _OPERATION_INPUT_KIND.get(meta.operation)
    if operation_kind is None:
        return None  # delete: id-only, no input.

    consumer_input = meta.input_class if operation_kind == CREATE else meta.partial_input_class
    if consumer_input is not None:
        # A fully consumer-authored input replaces the generated one entirely; the
        # bind materializes the consumer class under its own name so the lazy ref
        # resolves and the AR-M6 collision check still covers it.
        materialize_mutation_input_class(consumer_input.__name__, consumer_input)
        return consumer_input

    # Key the cache on the EFFECTIVE field set, not the raw ``(fields, exclude)``
    # declaration: the generated name and the spec's type identity are derived
    # from ``frozenset(effective field names)`` (spec-036 Decision 6 line 334;
    # ``mutations.inputs.mutation_input_type_name``), so two declarations that
    # narrow to the same effective shape via different spellings must dedupe to one
    # type (spec-036 Edge cases line 509). ``editable_input_fields`` is the same
    # selector ``build_mutation_input`` runs, so deriving the effective names here
    # keeps the cache key single-sourced with the name and the identity tuple.
    effective_field_names = frozenset(
        field.name
        for field in editable_input_fields(meta.model, fields=meta.fields, exclude=meta.exclude)
    )
    shape_key = (meta.model, operation_kind, effective_field_names)
    input_cls = _shape_build_cache.get(shape_key)
    if input_cls is None:
        input_cls = build_mutation_input(
            meta.model,
            operation_kind=operation_kind,
            primary_type=primary_type,
            fields=meta.fields,
            exclude=meta.exclude,
        )
        _shape_build_cache[shape_key] = input_cls
    materialize_mutation_input_class(input_cls.__name__, input_cls)
    return input_cls


def _bind_mutation(mutation_cls: type) -> None:
    """Bind one registered mutation at phase 2.5 (spec-036 Decision 12).

    Resolves the model primary type (raising for no-primary / ambiguous), builds +
    materializes the operation's input class (``create`` / ``update``) and the
    per-mutation ``<Name>Payload`` (every operation) as module globals of
    ``mutations.inputs`` before ``strawberry.Schema(...)`` runs, and stashes the
    resolved refs on the mutation class for Slice 3's ``DjangoMutationField``.
    """
    meta = mutation_cls._mutation_meta
    primary_type = _resolve_primary_type(mutation_cls, meta.model)

    input_cls = _materialize_input_for(meta, primary_type)

    payload_cls = build_payload_type(
        mutation_cls.__name__,
        object_type=primary_type,
        object_slot=payload_object_slot(primary_type),
    )
    # Payload classes are also module globals of ``mutations.inputs`` and also
    # need the AR-M6 distinct-shape collision raise, so they route through the
    # SAME ``materialize_mutation_input_class`` ledger as the input classes (one
    # ledger, one collision check, one ``registry.clear()`` co-clear - the
    # preferred one-ledger choice from the plan's discretion item).
    materialize_mutation_input_class(payload_cls.__name__, payload_cls)

    mutation_cls._primary_type = primary_type
    mutation_cls._input_class = input_cls
    mutation_cls._payload_type_name = payload_cls.__name__


def bind_mutations() -> None:
    """Bind every registered ``DjangoMutation`` (the finalizer phase-2.5 entry point).

    Called by ``finalize_django_types`` in the phase-2.5 window, after primary-type
    state is settled and before ``strawberry.type(...)`` freezes the schema
    classes (spec-036 Decision 12). Drains the declaration registry in
    registration order; each ``_bind_mutation`` materializes that mutation's
    generated classes.
    """
    _shape_build_cache.clear()
    for mutation_cls in iter_mutations():
        _bind_mutation(mutation_cls)
