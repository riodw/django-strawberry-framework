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

import inspect
from typing import TYPE_CHECKING, Any, get_origin

import strawberry
from strawberry import relay
from strawberry.types.base import StrawberryList

from ..exceptions import ConfigurationError
from ..registry import registry
from ..utils.querysets import SyncMisuseError
from ..utils.typing import unwrap_return_type
from .inputs import (
    CREATE,
    PARTIAL,
    build_mutation_input,
    build_payload_type,
    editable_input_fields,
    materialize_mutation_input_class,
    mutation_input_shape,
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


def _normalize_field_sequence(value: Any, *, label: str = "fields") -> tuple[str, ...] | None:
    """Return ``Meta.fields`` / ``Meta.exclude`` as a tuple of names, or ``None``.

    ``None`` means "unset". A non-``None`` value is coerced to a tuple so the
    bind and the generator see one shape (``editable_input_fields`` accepts a
    tuple). A bare string is a common mistake (it would iterate as characters),
    so it is rejected here at class creation. A duplicate name (e.g.
    ``("name", "name", "category")``) is also rejected here: the duplicate would
    otherwise collapse silently when the effective field set is taken as a
    ``frozenset``, masking a malformed declaration, so it fails loud naming the
    repeated field(s). ``label`` names which key (``fields`` / ``exclude``) is at
    fault in the message.
    """
    if value is None:
        return None
    if isinstance(value, str):
        raise ConfigurationError(
            "DjangoMutation Meta.fields / Meta.exclude must be a sequence of field "
            f"names, not a bare string: {value!r}.",
        )
    names = tuple(value)
    seen: set[str] = set()
    duplicates = sorted({name for name in names if name in seen or seen.add(name)})
    if duplicates:
        raise ConfigurationError(
            f"DjangoMutation Meta.{label} declares duplicate field name(s): "
            f"{duplicates!r}. Each field may appear at most once.",
        )
    return names


def _validate_permission_classes(mutation_name: str, value: Any) -> list[Any]:
    """Validate + normalize ``Meta.permission_classes`` at class creation (feedback P2).

    The DoD says an invalid ``permission_classes`` entry is rejected at
    class-creation, not deferred to a request-time ``TypeError`` /
    ``AttributeError`` inside ``DjangoMutation.check_permission`` (which does
    ``permission_class().has_permission(...)``). So:

    - ``None`` (unset) -> the ``[DjangoModelPermission]`` default seam.
    - a bare ``str`` / ``bytes`` (a single name) or a bare class (forgot the
      enclosing sequence) -> ``ConfigurationError``: the contract is a *sequence*
      of permission classes.
    - any other non-iterable -> ``ConfigurationError``.
    - each entry must be a **class exposing a callable ``has_permission``** (the
      shape ``check_permission`` instantiates + calls); an instance, a non-class
      value, or a class without ``has_permission`` -> ``ConfigurationError``
      naming the offending entry.

    Returns the normalized ``list`` the snapshot stores (so ``check_permission``
    iterates a known list, never a raw consumer value).
    """
    if value is None:
        return [DjangoModelPermission]
    if isinstance(value, (str, bytes, type)):
        raise ConfigurationError(
            f"DjangoMutation {mutation_name}.Meta.permission_classes must be a sequence of "
            f"permission classes (e.g. [DjangoModelPermission]); got {value!r}.",
        )
    try:
        classes = list(value)
    except TypeError as exc:
        raise ConfigurationError(
            f"DjangoMutation {mutation_name}.Meta.permission_classes must be a sequence of "
            f"permission classes (e.g. [DjangoModelPermission]); got {value!r}.",
        ) from exc
    for entry in classes:
        if not isinstance(entry, type) or not callable(getattr(entry, "has_permission", None)):
            raise ConfigurationError(
                f"DjangoMutation {mutation_name}.Meta.permission_classes entry {entry!r} is not a "
                "permission class exposing has_permission; each entry must be a class with a "
                "has_permission(info, mutation, operation, data, instance) method.",
            )
    return classes


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

    ``permission_classes`` is validated + normalized by
    ``_validate_permission_classes`` (feedback P2): it defaults to
    ``[DjangoModelPermission]`` when unset, must otherwise be a *sequence* of
    classes each exposing a callable ``has_permission``, and a bad entry is
    rejected here at class creation rather than as a request-time ``TypeError`` /
    ``AttributeError`` inside ``check_permission`` (spec-036 Decision 15 - the
    write-auth seam; the enforcement runs in Slice 3's resolver).
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

    fields = _normalize_field_sequence(getattr(meta, "fields", None), label="fields")
    exclude = _normalize_field_sequence(getattr(meta, "exclude", None), label="exclude")
    if fields is not None and exclude is not None:
        raise ConfigurationError(
            f"DjangoMutation {name}.Meta declares both `fields` and `exclude`; "
            "supply at most one.",
        )
    if operation == "delete" and (fields is not None or exclude is not None):
        # A ``delete`` is ``id:``-only and materializes NO input (spec-036 Decision
        # 14), so ``fields`` / ``exclude`` have no effect. Because delete skips
        # input generation, an unknown / malformed name in them is never validated
        # by ``editable_input_fields`` either, so a typo'd field silently finalizes.
        # Reject the inapplicable keys outright: declaring them on a delete is a
        # configuration mistake regardless of whether the names are valid.
        raise ConfigurationError(
            f"DjangoMutation {name}.Meta.operation is 'delete', which is id-only and "
            "takes no input; remove the inapplicable Meta.fields / Meta.exclude.",
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

    permission_classes = _validate_permission_classes(
        name,
        getattr(meta, "permission_classes", None),
    )

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

        An ``async def has_permission`` entry returns a coroutine, which is truthy:
        a naive ``if not has_permission(...)`` would never deny it, so an async
        deny-check would be silently treated as ALLOW - an authorization bypass
        (feedback). The pipeline is synchronous (Decision 15), so the coroutine can
        never be awaited here; it is closed and raised as a ``SyncMisuseError``,
        the same discipline ``apply_type_visibility_sync`` applies to an async
        ``get_queryset``. (An async ``check_permission`` override is caught by the
        resolver's ``_authorize_or_raise`` one level up.)
        """
        meta = type(self)._mutation_meta
        for permission_class in meta.permission_classes:
            allowed = permission_class().has_permission(
                info,
                type(self),
                operation,
                data,
                instance,
            )
            if inspect.iscoroutine(allowed):
                allowed.close()
                raise SyncMisuseError(
                    f"{permission_class.__name__}.has_permission returned a coroutine in a "
                    "sync mutation context. A DjangoMutation runs its permission check "
                    "synchronously, so it cannot await an async permission hook; redefine "
                    "has_permission / check_permission as a sync method returning a bool.",
                )
            if not allowed:
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


def _materialize_input_for(
    mutation_name: str,
    meta: _ValidatedMutationMeta,
    primary_type: type,
) -> type | None:
    """Build + materialize the operation's input class, or return ``None`` for ``delete``.

    ``create`` builds the ``<Model>Input`` (``CREATE`` kind); ``update`` builds the
    ``<Model>PartialInput`` (``PARTIAL`` kind); ``delete`` is ``id:``-only and
    needs no input (spec-036 Decision 14). A consumer ``input_class`` /
    ``partial_input_class`` is **merged** with the generated input, NOT a wholesale
    replacement (the spec-010 relation-override contract, spec-036 DoD line 51 /
    line 336 / AR-M2): the consumer declares the field(s) it wants to customize
    (using the generated naming scheme - validated at class creation), the
    generator fills the rest of the editable shape, and the consumer's fields are
    honored, never clobbered. See ``_materialize_merged_input``.

    Identical generated shapes dedupe to one class object: the shape identity is
    ``(model, operation kind, frozenset(effective field names))`` (spec-036
    Decision 6). The first mutation with a given shape builds + caches the class in
    ``_shape_build_cache``; a later mutation with the identical shape reuses that
    cached object, so ``materialize_mutation_input_class`` sees the SAME class
    twice and dedupes idempotently (rather than a fresh, name-colliding object). A
    consumer-merged input is materialized under the SAME canonical shape name (it
    customizes representations of existing columns, it does not change the field
    set), so two mutations resolving the same shape to two DIFFERENT representations
    still raise the AR-M6 collision.
    """
    operation_kind = _OPERATION_INPUT_KIND.get(meta.operation)
    if operation_kind is None:
        return None  # delete: id-only, no input.

    consumer_input = meta.input_class if operation_kind == CREATE else meta.partial_input_class
    if consumer_input is not None:
        return _materialize_merged_input(
            mutation_name,
            meta,
            primary_type,
            operation_kind,
            consumer_input,
        )

    # Derive the shape ONCE (DRY-1): ``mutation_input_shape`` single-sources the
    # cache key (the EFFECTIVE field set, NOT the raw ``(fields, exclude)``
    # spelling - two narrowings to one effective shape must dedupe, spec-036
    # Edge cases line 509) AND the generated name, so the bind cache key and the
    # generated type name cannot drift. The same descriptor is handed to
    # ``build_mutation_input`` so it does not re-walk the editable fields.
    shape = mutation_input_shape(
        meta.model,
        operation_kind,
        fields=meta.fields,
        exclude=meta.exclude,
    )
    input_cls = _shape_build_cache.get(shape.cache_key)
    if input_cls is None:
        input_cls = build_mutation_input(
            meta.model,
            operation_kind=operation_kind,
            primary_type=primary_type,
            fields=meta.fields,
            exclude=meta.exclude,
            shape=shape,
        )
        _shape_build_cache[shape.cache_key] = input_cls
    materialize_mutation_input_class(input_cls.__name__, input_cls)
    return input_cls


def _materialize_merged_input(
    mutation_name: str,
    meta: _ValidatedMutationMeta,
    primary_type: type,
    operation_kind: str,
    consumer_input: type,
) -> type:
    """Merge a consumer ``input_class`` with the generated remainder (spec-010 / AR-M2).

    The consumer-authored ``@strawberry.input`` declares only the field(s) it
    customizes (a custom scalar, validator, alias, description), using the
    generated naming scheme (``_validate_input_class`` already pinned ``supplied
    expected``). Those python-attr names are passed to ``build_mutation_input`` as
    ``overrides`` so the generator emits every OTHER editable column and SKIPS the
    consumer-authored ones - the generated remainder. The two are combined by
    **class inheritance** (``strawberry.input(type(name, (consumer, remainder),
    {}))``): Strawberry collects the union of both bases' fields, the consumer base
    takes MRO precedence, and the consumer's field definitions are preserved
    EXACTLY (annotation, default / required-ness, ``name=`` alias, description,
    directives) rather than reconstructed from triples. Because ``overrides``
    guarantees the two field sets are disjoint, there is no duplicate-field clash.

    The merged class is named + materialized under the **canonical shape name**
    (``shape.type_name`` from the shared ``mutation_input_shape`` descriptor, DRY-1
    - derived from the full selected field set, which still includes the overridden
    columns, so it is the same ``<Model>Input`` / shape-derived name the
    all-generated path uses): the consumer customizes representations of existing
    columns, it does NOT change the shape identity ``(model, operation kind,
    frozenset(effective names))``. A merged input is therefore NOT cached in
    ``_shape_build_cache`` (it is mutation-specific), and if two mutations resolve
    the same shape to two different representations they collide on that name and
    raise the AR-M6 ``ConfigurationError`` at ``materialize_mutation_input_class`` -
    the same fail-loud the all-generated collision uses.
    """
    consumer_attrs = frozenset(
        field.python_name for field in consumer_input.__strawberry_definition__.fields
    )
    shape = mutation_input_shape(
        meta.model,
        operation_kind,
        fields=meta.fields,
        exclude=meta.exclude,
    )
    _validate_relation_override_types(
        mutation_name,
        consumer_input,
        shape,
        attr_name="input_class" if operation_kind == CREATE else "partial_input_class",
    )
    remainder = build_mutation_input(
        meta.model,
        operation_kind=operation_kind,
        primary_type=primary_type,
        fields=meta.fields,
        exclude=meta.exclude,
        overrides=consumer_attrs,
        shape=shape,
    )
    merged = strawberry.input(type(shape.type_name, (consumer_input, remainder), {}))
    materialize_mutation_input_class(shape.type_name, merged)
    return merged


def _validate_relation_override_types(
    mutation_name: str,
    consumer_input: type,
    shape: Any,
    *,
    attr_name: str,
) -> None:
    """Type- and shape-lock a consumer relation override to the generated id (AR-M2 / Decision 10).

    A relation column whose related model HAS a primary Relay-Node type generates a
    ``relay.GlobalID`` (forward FK / OneToOne) or ``list[relay.GlobalID]`` (M2M) input
    whose decode is **type-checked against the relation target** (spec-036 AR-H4) AND
    **visibility-checked through the related type's ``get_queryset``** (spec-036
    Decision 10 / feedback P1) - so a permitted writer cannot attach a row they could
    not *see*. Both guarantees ride the EXACT generated shape:
    ``resolvers.py::_decode_relation_id_set`` only type/visibility-checks a value that
    ``isinstance(_, relay.GlobalID)`` (the FK path unwraps a one-element list, the M2M
    path iterates a flat list) and passes anything else through as a raw pk.

    The naming half of AR-M2 (``_validate_input_class``) lets a consumer override a
    relation field's *representation* under its generated ``<field>_id`` / ``list``
    name, but it name-checks only - so a consumer could declare a divergent TYPE or
    CONTAINER SHAPE and the CR-2 merge would honor it, defeating the decode:

    - ``category_id: int`` (raw pk core) - the value is seen as a non-``GlobalID`` raw
      pk and passed through, bypassing both the AR-H4 type-check and the visibility
      contract (attach-by-raw-pk to an unseeable row);
    - ``genres: relay.GlobalID`` (M2M overridden as a SCALAR) - the resolver wraps the
      scalar in a one-element list and decodes it as a single membership, or the
      generated M2M list contract is violated, a top-level resolver / ORM error;
    - ``genres: list[list[relay.GlobalID]]`` (NESTED list) - the inner lists are not
      ``relay.GlobalID`` instances, so each is passed through as a raw pk into the M2M
      ``.set(...)``, a top-level ORM error;
    - ``category_id: list[relay.GlobalID]`` (FK overridden as a LIST) - the resolver
      stores the list as the ``<field>_id`` attr and Django raises against the scalar
      FK column under the MODEL field name, not the ``categoryId`` input field.

    So a relation override MUST keep BOTH the generated ``relay.GlobalID`` core AND its
    container shape (scalar for FK / OneToOne, one-level ``list`` for M2M); any
    divergence in core type or list depth is a fail-loud ``ConfigurationError`` (the
    AR-M2 posture), caught at the bind rather than crashing a request.

    Enforced at the phase-2.5 bind, NOT at class creation: whether the related model
    has a primary Relay-Node type is a ``registry.get`` lookup only reliably populated
    at finalization (this is exactly why ``_validate_input_class`` passes
    ``related_primary_type=None`` - the python-attr name is registry-independent, the
    id *type* is not). The expected shape is single-sourced with the generator by
    reading ``relation_input_annotation``'s emitted annotation (core via
    ``_annotation_core_is_global_id``, list depth via ``get_origin(...) is list``), so
    "GlobalID iff Relay-Node primary" and "list iff M2M" cannot drift from what
    ``build_mutation_input`` produces. A raw-pk relation (a non-Relay target) carries
    no visibility contract to defeat, so an override there is left alone.
    """
    consumer_fields = {
        field.python_name: field for field in consumer_input.__strawberry_definition__.fields
    }
    for field in shape.selected:
        if not getattr(field, "is_relation", False):
            continue
        python_attr, _graphql_name, annotation = relation_input_annotation(
            field,
            related_primary_type=registry.get(field.related_model),
        )
        if not _annotation_core_is_global_id(annotation):
            continue  # raw-pk relation (non-Relay target): no visibility contract to bypass.
        consumer_field = consumer_fields.get(python_attr)
        if consumer_field is None:
            continue  # not overridden; the generated GlobalID remainder is used.
        expected_depth = 1 if get_origin(annotation) is list else 0
        consumer_depth, consumer_core = _strawberry_field_shape(consumer_field)
        if consumer_core is not relay.GlobalID or consumer_depth != expected_depth:
            expected = "list[relay.GlobalID]" if expected_depth else "relay.GlobalID"
            kind = "M2M" if expected_depth else "forward FK/OneToOne"
            raise ConfigurationError(
                f"DjangoMutation {mutation_name}.Meta.{attr_name} overrides relation field "
                f"{python_attr!r} with an id type/shape that diverges from the generated input. "
                f"{field.related_model.__name__} has a primary Relay-Node type, so the {kind} "
                f"relation input is {expected} - type- and visibility-checked at decode (spec-036 "
                "AR-H4 / Decision 10). A divergent core type or container shape would be passed "
                "through unchecked (bypassing the relation visibility contract) or crash the "
                f"resolver / ORM. Declare {python_attr!r} as {expected}.",
            )


def _annotation_core_is_global_id(annotation: Any) -> bool:
    """Return whether a generated relation annotation's core id type is ``relay.GlobalID``.

    ``relation_input_annotation`` emits ``relay.GlobalID`` (forward FK / OneToOne) or
    ``list[relay.GlobalID]`` (M2M) for a Relay-Node-primary target, and the related
    model's raw pk scalar (or ``list[<scalar>]``) otherwise. This peels the M2M ``list``
    wrapper via ``utils/typing.py::unwrap_return_type`` (the shared one-layer list /
    Strawberry-list peeler) and compares the core against ``relay.GlobalID`` so both id
    shapes are recognized from the one generator-emitted annotation (no separate
    Relay-vs-pk re-derivation).
    """
    return unwrap_return_type(annotation) is relay.GlobalID


def _strawberry_field_shape(field: Any) -> tuple[int, Any]:
    """Return a consumer field's ``(list_depth, core_type)``, peeling Strawberry wrappers.

    A consumer relation override resolves to nested ``StrawberryOptional`` /
    ``StrawberryList`` wrappers around a core type: ``relay.GlobalID | None`` is a
    ``StrawberryOptional(GlobalID)`` (depth 0), ``list[relay.GlobalID]`` is a
    ``StrawberryList(GlobalID)`` (depth 1), ``list[list[relay.GlobalID]]`` is depth 2.
    Optional wrappers are nullability (ignored for the shape); each ``StrawberryList``
    counts one level of list depth. Returning ``(depth, core)`` lets the shape-lock
    compare BOTH the core identity (``is relay.GlobalID``) and the list depth against
    the generated relation annotation, so a wrong core (``int`` / ``strawberry.ID``), a
    scalar-for-M2M, a list-for-FK, or a nested list are all caught.
    """
    type_ = field.type
    depth = 0
    seen: set[int] = set()
    while hasattr(type_, "of_type") and id(type_) not in seen:
        seen.add(id(type_))
        if isinstance(type_, StrawberryList):
            depth += 1
        type_ = type_.of_type
    return depth, type_


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

    input_cls = _materialize_input_for(mutation_cls.__name__, meta, primary_type)

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
