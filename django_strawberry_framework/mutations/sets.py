"""``DjangoMutation`` base + metaclass + ``Meta`` validation + the phase-2.5 bind (spec-036).

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
  Built by ``make_meta_validating_metaclass(register)`` beside
  ``make_declaration_registry`` so the plain-form flavor shares the lifecycle.
- the declaration registry (``register_mutation`` / ``clear_mutation_registry`` /
  ``iter_mutations``) the finalizer bind drains. ``register_mutation`` rejects a
  late declaration after ``registry.mark_finalized()`` (spec-036 Edge cases).
- ``bind_mutations()`` - the phase-2.5 entry point the finalizer calls. For each
  registered mutation it resolves the model's primary ``DjangoType`` (spec-036
  Decision 11), builds + materializes the generated ``Input`` / ``PartialInput``
  classes (``create`` / ``update``) and the ``<Name>Payload`` (every operation)
  as module globals of ``mutations.inputs`` before ``strawberry.Schema(...)`` runs
  (spec-036 Decision 12), raising ``ConfigurationError`` on a no-primary target or
  a duplicate generated GraphQL name.

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
here.** Those live in ``resolvers.py`` + ``fields.py``. A ``DjangoMutation``
declared here is inert until a field exposes it: registered + bound at finalize,
never resolved.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple, get_origin

import strawberry
from django.db import models
from strawberry import relay
from strawberry.types.base import StrawberryList

from ..exceptions import ConfigurationError, _safe_arg_repr, _safe_class_name
from ..registry import register_subsystem_clear, registry
from ..utils.imports import import_attr
from ..utils.inputs import (
    get_or_store_shape_build,
    make_shape_build_cache,
    normalize_field_name_sequence,
)
from ..utils.typing import unwrap_return_type
from .inputs import (
    CREATE,
    INPUTS_MODULE_PATH,
    build_mutation_input,
    build_payload_type,
    editable_input_fields,
    materialize_mutation_input_class,
    mutation_input_field_specs,
    mutation_input_shape,
    relation_input_annotation,
)
from .operations import (
    _OPERATION_INPUT_OVERRIDE_ATTR,
    _VALID_OPERATIONS,
    NON_DELETE_OPERATION_INPUT_KIND,
    NON_DELETE_WRITE_OPERATIONS,
    non_delete_operation_error,
)
from .permissions import DjangoModelPermission, run_permission_classes

#: Common Meta keys accepted by every write-flavor Mutation.Meta (fields, exclude, permission_classes).
COMMON_WRITE_META_KEYS: frozenset[str] = frozenset(
    {"fields", "exclude", "permission_classes"},
)

#: Common Meta keys accepted by every model-backed write-flavor Mutation.Meta
#: (DjangoMutation, ModelForm, Serializer).
MODEL_BACKED_WRITE_META_KEYS: frozenset[str] = COMMON_WRITE_META_KEYS | frozenset(
    {"operation", "select_for_update"},
)

# The mutation ``Meta``'s own allowed-key set (spec-036 Decision 12). Disjoint
# from ``types/base.py::ALLOWED_META_KEYS``: a mutation
# ``Meta`` is the mutation class's own namespace, composed from the shared
# ``MODEL_BACKED_WRITE_META_KEYS`` plus model-flavor specific keys.
_ALLOWED_MUTATION_META_KEYS: frozenset[str] = MODEL_BACKED_WRITE_META_KEYS | frozenset(
    {"model", "input_class", "partial_input_class"},
)


def _safe_frozenset_membership(value: Any, choices: frozenset[str]) -> bool:
    """Return ``value in choices``, answering ``False`` when hashing ``value`` raises.

    ``Meta.operation`` is consumer-supplied: a ``str`` subclass may define a
    raising ``__hash__`` (or one that turns hostile after its first call), and
    frozenset containment hashes its probe FIRST, so the raw ``RuntimeError``
    would escape the very validation raise that exists to reject the value -
    the hostile-Meta containment parity ``_validate_permission_classes``
    already applies to its own consumer-supplied containers. A value that
    cannot be hashed cannot be a validated operation anyway, so answering
    ``False`` routes it to the ordinary typed reject, whose ``_safe_arg_repr``
    render is itself hostile-proof.
    """
    try:
        return value in choices
    except BaseException:
        # Deliberately ``BaseException`` (the package's hostile-dunder convention):
        # a display-adjacent probe must never propagate ``SystemExit`` /
        # ``KeyboardInterrupt`` past the typed reject.
        return False


def require_non_delete_operation(base_label: str, name: str, meta: type) -> str:
    """Return ``Meta.operation`` if it is create/update, else raise the shared reject.

    The getattr + membership check both model-backed form and serializer
    ``_validate_meta`` share after their type-gates. The error body is
    ``non_delete_operation_error``; this owns the lookup so a new non-delete
    verb cannot leave one flavor still spelling the membership test. The
    model-less plain form does NOT call this (it rejects ANY ``operation`` key).
    """
    operation = getattr(meta, "operation", None)
    if not isinstance(operation, str) or not _safe_frozenset_membership(
        operation,
        NON_DELETE_WRITE_OPERATIONS,
    ):
        raise non_delete_operation_error(base_label, name, operation)
    return operation


def reject_unknown_meta_keys(name: str, meta: type, allowed: frozenset[str]) -> None:
    """Raise the ``Meta``-typo guard if ``meta`` declares a key outside ``allowed``.

    The ``unknown = sorted(declared - allowed)`` typo guard every ``_validate_meta``
    computes inline (model / modelform / plain-form / serializer): promoted so each
    flavor calls it with its OWN allowed-key frozenset rather than re-spelling the
    own-keys-only (no MRO walk) ``vars(meta)`` scan + the reject. ``declared`` is the
    public own-keys of ``meta`` (skipping dunders); a declared key outside ``allowed``
    raises ``ConfigurationError`` naming the offending key(s). Mirrors
    ``types/base.py::_validate_meta``'s own-keys-only posture.
    """
    if not isinstance(meta, type):
        raise ConfigurationError(f"{name}.Meta must be a class; got {_safe_arg_repr(meta)}.")
    declared = {key for key in vars(meta) if not (isinstance(key, str) and key.startswith("_"))}
    unknown = sorted(
        declared - allowed,
        key=lambda k: (not isinstance(k, str), str(k)),
    )
    if unknown:
        raise ConfigurationError(f"{name}.Meta has unknown keys: {unknown}.")


def normalize_meta_field_selection(
    meta: type,
    *,
    flavor: str,
) -> tuple[tuple[str, ...] | None, tuple[str, ...] | None]:
    """Return ``(fields, exclude)`` after the shared sequence-shape normalize.

    Every write-flavor ``_validate_meta`` runs this pair so a new flavor cannot
    normalize one key and forget the other (the serializer flavor included -
    ``rest_framework/sets.py`` materializes its selectors at class creation and
    re-normalizes inside ``resolve_effective_serializer_fields`` at the bind).
    Existence / mutual-exclusion / empty-set checks stay at the
    caller: the model flavor's delete-inapplicable rule and the form flavor's
    ``resolve_effective_form_fields`` walk are different jobs.
    """
    fields = normalize_field_name_sequence(
        getattr(meta, "fields", None),
        label="fields",
        flavor=flavor,
    )
    exclude = normalize_field_name_sequence(
        getattr(meta, "exclude", None),
        label="exclude",
        flavor=flavor,
    )
    return fields, exclude


def _hook_overridden(cls: type, base: type, name: str) -> bool:
    """Return whether ``cls`` overrides the ``name`` method relative to ``base``.

    The identity check ``forms/sets.py::_form_kwargs_overridden`` uses for the
    form construction-hook waiver (``get_form_kwargs`` / ``get_form``). Both
    hooks are plain instance methods, so ``getattr(cls, name)`` resolves to the
    unbound function; a concrete override makes it ``is not`` the base's.
    Serializer mutations do NOT ride this primitive: they waive create-required
    only via auditable ``Meta.injected_fields``, never a constructor-hook
    override (spec-039 Decision 7).
    """
    return getattr(cls, name) is not getattr(base, name)


def cached_build_input(
    cache: dict[Any, tuple[type, Any]],
    shape_key: Any,
    *,
    guard: Callable[[], None],
    build_fn: Callable[[], tuple[type, Any]],
) -> tuple[type, Any]:
    """Run the per-declaration guard, THEN the per-shape cache lookup.

    The promoted guard-before-cache-lookup core for flavors whose cache key is
    known BEFORE the build (today: the form ``build_input`` seam). The
    load-bearing ordering (spec-038 Decision 7 / spec-039 Decision 7): the
    create-required-narrowing ``guard`` runs PER declaration, BEFORE the
    per-shape cache lookup, so a waiving mutation (guard a no-op, having
    overridden the construction hook) that materializes a narrowed shape FIRST
    cannot suppress the guard for a later non-waiving mutation reusing the
    cached shape - the cache key (``shape_key``) excludes the waiver, so the
    guard is tied to the declaration, not the built shape.

    The get-or-store itself rides ``utils/inputs.py::get_or_store_shape_build``
    (the same spine serializer ``dedupe_serializer_input_shape`` uses after
    its walk). The serializer flavor deliberately does NOT call this helper:
    its cache key is the post-build ``SerializerInputShape`` descriptor, so
    ``rest_framework/sets.py`` preserves the same guard-before-dedupe
    discipline inline. The materialize-then-stash tail both flavors still
    share is ``build_and_stash_input``.

    On a cache miss ``build_fn()`` returns ``(input_cls, payload)`` where
    ``payload`` is the per-flavor stash value (the form's ``field_specs``
    list). ``cache`` is the FLAVOR's own per-pass ``make_shape_build_cache()``
    dict (passed in, not owned here) so the mutation / form caches stay
    disjoint - each is registered + cleared separately.
    """
    guard()
    return get_or_store_shape_build(cache, shape_key, build_fn)


def build_and_stash_input(
    cls: type,
    *,
    build: Callable[[], tuple[type, Any]],
    materialize: Callable[[str, type], None],
    specs_of: Callable[[Any], Any],
) -> type:
    """Materialize a built input + stash its reverse map on the mutation.

    The materialize-then-stash tail the form + serializer ``build_input`` seams
    share: ``build()`` returns ``(input_cls, payload)`` (the per-flavor stash value),
    ``materialize(input_cls.__name__, input_cls)`` pins it as a module global of the
    flavor's input namespace, ``cls._input_field_specs = specs_of(payload)`` records
    the reverse map for the decode, and the class is returned.
    ``specs_of`` extracts the reverse-map specs from the per-flavor payload (the form
    payload IS the specs list - identity; the serializer payload is the shape, from
    which ``shape.field_specs`` is read), so the one tail serves both flavors.
    """
    input_cls, payload = build()
    materialize(input_cls.__name__, input_cls)
    cls._input_field_specs = specs_of(payload)
    return input_cls


def construction_kwargs(*, instance: Any = None, **base: Any) -> dict[str, Any]:
    """Build a construction-hook kwargs dict, adding ``instance`` only when non-``None`` (spec-039 Md7).

    The default construction-kwargs hooks share the ``{...base...}`` +
    ``if instance is not None: kwargs["instance"] = instance`` shape: the form
    ``_default_get_form_kwargs`` passes ``base={"data": ..., "files": ...}``, the
    serializer ``get_serializer_kwargs`` passes ``base={"data": ...}``. Single-sites
    the "add ``instance`` only for update" clause (create / plain pass
    ``instance=None`` so no ``instance=`` key is emitted) so a new flavor's default
    hook reuses it rather than re-spelling the guard.
    """
    kwargs = dict(base)
    if instance is not None:
        kwargs["instance"] = instance
    return kwargs


def require_backing_class(
    name: str,
    meta: type,
    *,
    key: str,
    base_label: str,
    expected_label: str,
) -> Any:
    """Return ``Meta.<key>`` or raise the shared "declares no backing class" error.

    The presence check both the form + serializer ``_validate_meta`` prologues share:
    an unset / ``None`` ``Meta.<key>`` (``form_class`` / ``serializer_class``) is a
    clean ``ConfigurationError`` naming the key + the expected base, never a
    downstream ``AttributeError`` on a missing class. ``base_label`` names the
    offending base (``DjangoModelFormMutation`` / ``DjangoFormMutation`` /
    ``SerializerMutation``); ``expected_label`` is the base type named in the message
    (``forms.ModelForm`` / ``forms.Form`` / ``serializers.ModelSerializer``). The
    per-flavor TYPE-gate is ``require_subclass`` (shared ``must be a <label>
    subclass; got <value>`` template + ``_safe_arg_repr``); call it AFTER this
    presence check. The serializer's second, ModelSerializer-specific gate stays
    at that call site - its message names ``Meta.model``, not the shared
    subclass template. This helper owns only the shared presence clause.
    """
    backing = getattr(meta, key, None)
    if backing is None:
        raise ConfigurationError(
            f"{base_label} {name}.Meta declares no {key}; set Meta.{key} to a "
            f"{expected_label} subclass.",
        )
    return backing


def require_subclass(
    name: str,
    value: Any,
    *,
    base_label: str,
    key: str,
    expected: type,
    expected_label: str,
    note: str = "",
) -> Any:
    """Return ``value`` if it is an ``expected`` subclass, else raise the shared type-gate.

    The ``must be a <expected_label> subclass; got <value>`` clause both form
    type-gates and the serializer ``Serializer`` gate share. Presence is
    ``require_backing_class`` (a missing key names the flavor's *contract* class,
    which can be narrower than this type-gate - serializer missing-key names
    ``ModelSerializer`` while this gate first names ``Serializer``). Hostile
    ``__repr__`` is rendered through ``_safe_arg_repr`` so a broken value cannot
    replace the ``ConfigurationError``. ``note`` is an optional second sentence
    (the ModelForm-vs-plain-Form redirect).
    """
    if isinstance(value, type) and issubclass(value, expected):
        return value
    message = (
        f"{base_label} {name}.Meta.{key} must be a {expected_label} subclass; "
        f"got {_safe_arg_repr(value)}."
    )
    if note:
        message = f"{message} {note}"
    raise ConfigurationError(message)


def require_model_class(name: str, model: Any, *, base_label: str) -> Any:
    """Return ``model`` if it is a Django model class, else raise.

    The class-creation type-gate ``DjangoMutation._validate_meta`` runs after
    resolving ``Meta.model``. ModelForm / serializer ``_validate_meta``
    override the whole matrix and previously skipped this gate, so a
    non-model ``Meta.model`` would snapshot and crash at bind. One helper
    keeps the fail-loud on every model-backed flavor. ``base_label`` names
    the offending base so the model flavor's pinned
    ``DjangoMutation {name} resolved model must be a Django model class``
    message stays byte-identical.
    """
    if isinstance(model, type) and issubclass(model, models.Model):
        return model
    raise ConfigurationError(
        f"{base_label} {name} resolved model must be a Django model class; got {_safe_arg_repr(model)}.",
    )


def resolve_meta_model(meta: type, *, key: str, meta_attr: str) -> Any:
    """Resolve a backing class's ``Meta.model`` via the shared three-getattr chain.

    The ``getattr(meta, key) -> getattr(backing, meta_attr) -> getattr(backing_meta,
    "model")`` chain both flavors' ``_resolve_model`` overrides walk, differing only
    in ``key`` (``form_class`` / ``serializer_class``) and ``meta_attr`` (a
    ``ModelForm``'s ``_meta`` vs a serializer's ``Meta``). Returns ``None`` for any
    missing link (no backing class, no meta, no model), so the caller's base
    validation raises the clean "resolves no model" error rather than an
    ``AttributeError``.
    """
    backing = getattr(meta, key, None)
    backing_meta = getattr(backing, meta_attr, None)
    return getattr(backing_meta, "model", None)


def resolve_backed_model_or_raise(
    cls: type,
    meta: type,
    *,
    base_label: str,
    key: str,
    noun: str,
) -> Any:
    """Return ``cls._resolve_model(meta)`` or raise the shared "resolves no model" error.

    The no-model raise both flavors' ``_validate_meta`` share, run AFTER the backing
    class is type-validated (so ``Meta.<key>`` is a real class with a ``.__name__``).
    ``base_label`` / ``key`` / ``noun`` (``ModelForm`` / ``ModelSerializer``) are the
    only per-flavor axes; the message is otherwise byte-identical across flavors.
    """
    model = cls._resolve_model(meta)
    if model is None:
        backing = getattr(meta, key)
        raise ConfigurationError(
            f"{base_label} {_safe_class_name(cls)}.Meta.{key} {_safe_class_name(backing)} resolves no model; "
            f"a {noun} must set Meta.model so the mutation has a model + a DjangoType to return.",
        )
    return model


def resolver_seams(
    module_path: str,
    sync_name: str,
    async_name: str,
    *,
    with_id: bool = True,
) -> tuple[Any, Any]:
    """Build the ``(resolve_sync, resolve_async)`` classmethod pair a mutation base exposes.

    Every write-flavor base (``DjangoMutation`` / ``DjangoModelFormMutation`` /
    ``DjangoFormMutation`` / ``SerializerMutation``) exposes an identical
    ``resolve_sync`` / ``resolve_async`` seam: a function-local import of the flavor's
    resolver module (the cycle guard - the import runs at RESOLVE time, not class /
    module load) then a delegate to that module's entry with the GraphQL ``data`` /
    ``id`` kwargs. Single-sites the eight bodies as one factory: ``module_path`` is
    the flavor's resolver module, ``sync_name`` / ``async_name`` the entries it
    delegates to, and ``with_id`` is ``False`` for the model-LESS plain
    ``DjangoFormMutation`` (whose seam signature is ``(info, *, data)`` - no ``id``).

    Each call produces FRESH classmethod objects, so ``SubclassA.resolve_sync.__func__
    is BaseA.resolve_sync.__func__`` (inheritance) while ``BaseA.resolve_sync.__func__
    is not BaseB.resolve_sync.__func__`` (distinct factory calls) - the identities the
    field factory's routing tests assert. Assign the pair in the class body via
    ``resolve_sync, resolve_async = resolver_seams(...)`` so both land in the class
    ``__dict__``.
    """
    if with_id:

        @classmethod
        def resolve_sync(
            cls: type,
            info: Any,
            *,
            data: Any,
            id: Any,  # noqa: A002
        ) -> Any:
            """Delegate to the flavor's sync resolver entry (function-local import cycle guard)."""
            return import_attr(module_path, sync_name)(cls, info, data=data, id=id)

        @classmethod
        def resolve_async(
            cls: type,
            info: Any,
            *,
            data: Any,
            id: Any,  # noqa: A002
        ) -> Any:
            """Delegate to the flavor's async resolver entry (function-local import cycle guard)."""
            return import_attr(module_path, async_name)(cls, info, data=data, id=id)

    else:

        @classmethod
        def resolve_sync(cls: type, info: Any, *, data: Any) -> Any:
            """Delegate to the flavor's sync resolver entry (no ``id`` - model-less flavor)."""
            return import_attr(module_path, sync_name)(cls, info, data=data)

        @classmethod
        def resolve_async(cls: type, info: Any, *, data: Any) -> Any:
            """Delegate to the flavor's async resolver entry (no ``id`` - model-less flavor)."""
            return import_attr(module_path, async_name)(cls, info, data=data)

    return resolve_sync, resolve_async


# Per-finalize-pass build cache keyed by generated-input shape identity
# (``(model, operation_kind, frozenset(effective field names))``, spec-036
# Decision 6 #"Type identity and naming"). The key is the EFFECTIVE field set, NOT the raw
# ``(fields, exclude)`` declaration: two declarations that resolve to the same
# effective shape via different ``fields`` / ``exclude`` spellings (e.g.
# ``fields=("name",)`` vs the complementary ``exclude=(<the rest>)``, or a
# ``fields`` list naming the full editable set vs an un-narrowed create) must
# dedupe to one type (spec-036 Edge cases #"Two mutations over one model").
# Keying on the effective set mirrors
# ``mutations.inputs.mutation_input_shape``'s identity tuple (cache_key /
# type_name), so the cache key, the generated name, the field name seam, and the
# spec identity are single-sourced and cannot drift - two mutations with the same
# effective shape reuse one class object so the materialize ledger dedupes
# idempotently instead of seeing two distinct same-named classes.
#
# The ``(cache, clear)`` pair rides ``utils/inputs.py::make_shape_build_cache``,
# the same factory forms + serializer use, so the three write
# flavors share one dict-plus-clear shape while staying disjoint. Cleared at the
# start of ``bind_mutations()`` AND co-cleared from ``registry.clear()`` so a
# stale class from a prior (failed or re-run) finalize never leaks across a
# clear that does not itself re-bind.
_shape_build_cache, clear_mutation_shape_build_cache = make_shape_build_cache()
register_subsystem_clear(clear_mutation_shape_build_cache, owner="mutations.shape_cache")


class DeclarationRegistry(NamedTuple):
    """The ``(register, clear, iter, store)`` quad ``make_declaration_registry`` returns.

    A flat named bundle (not a tuple of bare callables) so a caller assigns the
    three public functions to module-level names AND keeps a handle on the backing
    ``store`` list for the tests that introspect it directly (e.g. the
    ``_mutation_registry.count(...)`` idempotency assertion). ``register`` /
    ``clear`` / ``iter_`` carry the dedup / clear / snapshot mechanics; ``store``
    is the disjoint ``list[type]`` they close over.
    """

    register: Any
    clear: Any
    iter_: Any
    store: list[type]


def make_declaration_registry(label: str) -> DeclarationRegistry:
    """Build a fresh declaration registry + its ``(register, clear, iter)`` callables.

    The Decision-13 shared-mechanics factory: given a human ``label``
    (``"DjangoMutation"`` / ``"DjangoFormMutation"``), create a private
    ``list[type]`` and return callables bound over it -

    - ``register`` records a class for the phase-2.5 bind, idempotent by identity
      (a class re-imported under a module reload is recorded once) and rejecting a
      declaration after ``registry.mark_finalized()`` / ``finalize_django_types()``
      (spec-036 Edge cases) - the bind has already run, so a late declaration would
      never be materialized; failing loud mirrors ``TypeRegistry._check_mutable``.
      ``label`` names the flavor in the reject message.
    - ``clear`` drops every recorded declaration (the ``registry.clear()`` co-clear
      hook) so a fresh finalize starts empty.
    - ``iter_`` returns every recorded declaration in registration order.

    The model flavor and the plain-form flavor (``forms/sets.py``) each instantiate
    this over their OWN list, so the dedup / reject / clear logic is single-sourced
    while the two ledgers stay disjoint (different ``bind_*`` bodies, different
    ``registry.clear()`` rows - the over-consolidation trap spec-038 Decision 13
    names is avoided by keeping the storage separate).
    """
    store: list[type] = []

    def register(declaration_cls: type) -> None:
        if registry.is_finalized():
            raise ConfigurationError(
                f"Cannot declare {label} {_safe_class_name(declaration_cls)} after finalization; "
                "mutation declarations are import-time only (call registry.clear() first).",
            )
        # Identity-scan dedup (NOT ``not in``): the ledger contract is idempotence
        # by identity, and ``list.__contains__`` dispatches each stored entry's
        # ``__eq__`` - which a consumer-supplied metaclass may override with a
        # raising or lying body, letting a hostile ``RuntimeError`` escape class
        # creation raw. An ``is`` scan is exactly the default semantics for every
        # honest class (``type.__eq__`` IS identity) while never dispatching
        # consumer-controlled dunders - the same containment parity the
        # ``Meta.operation`` membership tests apply.
        if not any(declaration_cls is stored for stored in store):
            store.append(declaration_cls)

    def clear() -> None:
        store.clear()

    def iter_() -> tuple[type, ...]:
        return tuple(store)

    return DeclarationRegistry(register=register, clear=clear, iter_=iter_, store=store)


def make_meta_validating_metaclass(
    register: Callable[[type], None],
    *,
    name: str,
    module: str,
) -> type:
    """Build a metaclass that validates ``Meta`` and registers the concrete subclass.

    The Decision-13 twin of ``make_declaration_registry``: given a ``register``
    callable bound over a disjoint declaration ledger, return a ``type`` subclass
    whose ``__new__`` -

    - builds the class via ``super().__new__``;
    - skips when ``attrs`` has no nested ``Meta`` (the abstract / intermediate
      base guard the set metaclasses rely on);
    - else runs ``new_class._validate_meta(meta)``, stashes ``_mutation_meta``,
      and calls ``register(new_class)``.

    The produced metaclass also SEALS the class head (0.0.15 authorization
    hardening): once a concrete subclass's validated snapshot is stashed, any
    later ``cls._mutation_meta = ...`` write raises ``ConfigurationError``. A
    ``has_permission`` hook receives the mutation class, so a plain attribute
    statement inside the hook could otherwise replace the validated record
    wholesale (an attacker-chosen namespace holding the empty allow-any posture)
    and authorize every later request - the same persistent cross-request
    bypass class the snapshot's own seal closes. The creation-time write in
    ``__new__`` is the one honored write; subsequent rebinding (or deletion) is
    refused. Unrelated class attributes (the bind's ``_primary_type`` /
    ``_input_class`` / ``_payload_type_name`` outputs) are unaffected.

    ``DjangoMutationMetaclass`` and ``DjangoFormMutationMetaclass`` are the two
    consumers (model ledger vs plain-form ledger). ``SerializerMutation`` /
    ``DjangoModelFormMutation`` ride the model metaclass via inheritance - no
    third Meta-validating twin. FilterSet / OrderSet metaclasses collect related
    declarations and are a different contract.

    ``name`` / ``module`` pin the returned class's identity to its public
    binding site: without them every produced metaclass would share the
    function-local ``make_meta_validating_metaclass.<locals>.MetaValidatingMetaclass``
    ``__qualname__`` (and a ``MetaValidatingMetaclass`` ``__name__``), which
    breaks module addressability, ``repr``/introspection, and reference-based
    pickling of the public metaclasses. Each consumer passes its own public
    symbol name and ``module=__name__`` so ``module + __qualname__`` resolves
    back to the bound object (the contract ``pickle`` requires for a class).
    """

    class MetaValidatingMetaclass(type):
        def __new__(
            cls: type,
            name: str,
            bases: tuple,
            attrs: dict,
        ) -> type:
            """Build the class; for a concrete subclass, validate ``Meta`` and register it."""
            new_class = super().__new__(cls, name, bases, attrs)
            meta = attrs.get("Meta")
            if meta is None:
                return new_class
            new_class._mutation_meta = new_class._validate_meta(meta)
            register(new_class)
            return new_class

        def __setattr__(cls, name: str, value: Any) -> None:
            """Keep the validated ``Meta`` snapshot write-once (0.0.15 auth hardening).

            The metaclass stashes ``_mutation_meta`` exactly once at class
            creation; any post-creation rebind of that head would swap the
            mutation's per-request authorization source for a hook-chosen record
            (the persistent bypass class ``_ValidatedMutationMeta``'s seal closes
            at the slot level). First write at class creation is the only allowed
            write; afterwards any attempt raises typed ``ConfigurationError``.
            """
            if name == "_mutation_meta" and "_mutation_meta" in cls.__dict__:
                raise ConfigurationError(
                    f"{cls.__name__}._mutation_meta is sealed and cannot be rebound; the "
                    "validated authorization snapshot is captured once at class creation.",
                )
            super().__setattr__(name, value)

        def __delattr__(cls, name: str) -> None:
            """Refuse deleting the validated ``Meta`` snapshot off a mutation class."""
            if name == "_mutation_meta" and "_mutation_meta" in cls.__dict__:
                raise ConfigurationError(
                    f"{cls.__name__}._mutation_meta is sealed and cannot be deleted; the "
                    "validated authorization snapshot is captured once at class creation.",
                )
            super().__delattr__(name)

    MetaValidatingMetaclass.__name__ = name
    MetaValidatingMetaclass.__qualname__ = name
    MetaValidatingMetaclass.__module__ = module
    return MetaValidatingMetaclass


# The model-flavor declaration registry: every concrete ``DjangoMutation`` records
# itself here at class creation; ``bind_mutations`` drains it at phase 2.5 and
# ``registry.clear()`` resets it via ``clear_mutation_registry``. The list +
# callables come from ``make_declaration_registry`` (spec-038 Decision 13) so the
# plain-form flavor (``forms/sets.py``) instantiates the SAME mechanics over a
# SECOND, disjoint list - the dedup / reject / clear logic is single-sourced while
# the two ledgers stay separate. ``register_mutation`` / ``clear_mutation_registry``
# / ``iter_mutations`` stay the importable public names ``registry.py`` (the
# co-clear), the metaclass, ``mutations/fields.py``, and the tests reference;
# ``_mutation_registry`` stays the backing list the idempotency tests introspect.
_mutation_declaration_registry = make_declaration_registry("DjangoMutation")
register_mutation = _mutation_declaration_registry.register
clear_mutation_registry = _mutation_declaration_registry.clear
iter_mutations = _mutation_declaration_registry.iter_
_mutation_registry = _mutation_declaration_registry.store
register_subsystem_clear(clear_mutation_registry, owner="mutations.declarations")


def _validate_input_class(
    mutation_name: str,
    input_class: Any,
    *,
    attr_name: str,
    model: type[models.Model],
    fields: tuple[str, ...] | None,
    exclude: tuple[str, ...] | None,
) -> None:
    """Validate a consumer ``input_class`` / ``partial_input_class``.

    Two checks (spec-036 Decision 5 error-shapes + Decision 6
    #"Custom inputs follow the generated field-naming scheme"):

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
            f"@strawberry.input-decorated type; got {_safe_arg_repr(input_class)}.",
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
    """Return the python-attr set the generator would emit for ``model``.

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

    A flat record (not a dataclass, to stay dependency-light) the bind and the
    resolver read instead of re-walking the raw ``Meta``. Mirrors
    ``types/base.py::_ValidatedMeta`` in role: validation happens once at class
    creation, then every downstream reader trusts this snapshot.

    The snapshot is SEALED once ``__init__`` finishes (0.0.15 authorization
    hardening): the record is the write side's per-request authorization source
    (``mutations/permissions.py::run_permission_classes`` reads
    ``type(self)._mutation_meta.permission_classes``), and a ``has_permission``
    hook runs INSIDE the walk with the mutation class in hand - a mutable slot
    would let one request's hook rebind the validated set (e.g. to the empty
    allow-any posture) for every later request: a persistent cross-request
    authorization bypass. Any attribute write or delete on a sealed snapshot
    raises ``ConfigurationError``; the validated configuration is immutable for
    the life of the process (a consumer who needs different authorization declares
    a new mutation class).
    """

    __slots__ = (
        "_sealed",
        "exclude",
        "fields",
        "form_class",
        "injected_fields",
        "input_class",
        "model",
        "nested_fields",
        "operation",
        "optional_fields",
        "partial_input_class",
        "permission_classes",
        "schema_fingerprint",
        "select_for_update",
        "serializer_class",
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
        permission_classes: tuple[Any, ...],
        form_class: Any = None,
        serializer_class: Any = None,
        optional_fields: tuple[str, ...] | None = None,
        schema_fingerprint: Any = None,
        injected_fields: tuple[str, ...] | None = None,
        select_for_update: bool = False,
        nested_fields: Any = None,
    ) -> None:
        self._sealed = False
        self.model = model
        self.operation = operation
        self.input_class = input_class
        self.partial_input_class = partial_input_class
        self.fields = fields
        self.exclude = exclude
        self.permission_classes = permission_classes
        # The form-flavor snapshot (spec-038): a ``DjangoModelFormMutation``
        # / ``DjangoFormMutation`` records its ``Meta.form_class`` here so the form
        # ``build_input`` / resolver read one snapshot shape. The model flavor
        # leaves it ``None`` (it has no ``form_class``), so the model path is
        # byte-unchanged - the slot is net-new state never read by the model
        # bind/resolver.
        self.form_class = form_class
        # The serializer-flavor snapshot (spec-039): a ``SerializerMutation``
        # records its ``Meta.serializer_class`` here so the serializer ``build_input``
        # / resolver read one snapshot shape (mirroring ``form_class``). The model +
        # form flavors leave it ``None`` (net-new state, never read off the model /
        # form paths), so they stay byte-unchanged.
        self.serializer_class = serializer_class
        # The serializer-flavor ``Meta.optional_fields`` (spec-039): the
        # create-only force-optional override lives on the MUTATION's ``Meta`` (the
        # documented public key), NOT the serializer's own ``Meta``. Normalized at
        # class creation and stored here as the validated tuple (``None`` when unset);
        # the serializer ``build_input`` threads it into
        # ``build_serializer_input_class`` so it participates in the input shape +
        # descriptor identity. The model + form flavors leave it ``None``.
        self.optional_fields = optional_fields
        # The serializer-flavor schema-hook fingerprint: a stable digest of
        # the ``get_serializer_for_schema()`` field shape captured at class validation, so the
        # phase-2.5 bind can raise on a NONDETERMINISTIC hook that drifted. The model + form
        # flavors leave it ``None`` (net-new state, never read off their paths).
        self.schema_fingerprint = schema_fingerprint
        # The serializer-flavor ``Meta.injected_fields``: the auditable,
        # per-field replacement for the blanket ``get_serializer_kwargs``-override waiver -
        # names the required fields a ``get_serializer_kwargs`` override supplies into ``data``,
        # subtracted from the create-required guard AND verified present at runtime. The model +
        # form flavors leave it ``None``.
        self.injected_fields = injected_fields
        # ``Meta.select_for_update`` (expanded by the 0.0.14 concurrency hardening): the
        # base-manager ``SELECT ... FOR UPDATE`` row lock on the update / delete
        # locate AND every relation-target check, constrained by the visibility pk
        # subquery inside the write transaction. Every model-backed flavor (model /
        # ``ModelForm`` / serializer) validates it via ``validate_select_for_update``
        # (default ``True``; an explicit ``False`` opts into weaker concurrency).
        # Only the model-less plain form leaves the constructor default (``False`` -
        # it locates no row).
        self.select_for_update = select_for_update
        # The serializer-flavor ``Meta.nested_fields``: the explicit opt-in
        # ``{field_name: NestedSerializerConfig}`` map naming the nested serializer fields the
        # generated input builds RECURSIVELY (an un-named nested field fails loud). ``None`` when
        # no nesting is opted in. The model + form flavors leave it ``None``.
        self.nested_fields = nested_fields
        # Seal LAST: every validated slot is set; from here on the record is
        self._sealed = True

    def __setattr__(self, name: str, value: Any) -> None:
        """Reject any attribute write on a sealed validated snapshot."""
        if getattr(self, "_sealed", False):
            raise ConfigurationError(
                f"The validated mutation Meta snapshot is sealed and {name!r} cannot be "
                "reassigned; authorization configuration is captured once at class creation.",
            )
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        raise ConfigurationError(
            "The validated mutation Meta snapshot is sealed; attributes cannot be deleted. "
            "Authorization configuration is captured once at class creation and is immutable.",
        )


def _validate_permission_classes(
    mutation_name: str,
    value: Any,
    *,
    unset_default: tuple[Any, ...] = (DjangoModelPermission,),
    base_label: str = "DjangoMutation",
) -> tuple[Any, ...]:
    """Validate + normalize ``Meta.permission_classes`` at class creation.

    An invalid ``permission_classes`` entry is rejected at
    class-creation, not deferred to a request-time ``TypeError`` /
    ``AttributeError`` inside ``DjangoMutation.check_permission`` (which does
    ``permission_class().has_permission(...)``). So:

    - ``None`` (unset) -> ``tuple(unset_default)``: the model-backed flavors keep
      the ``[DjangoModelPermission]`` default, while the model-less plain
      ``DjangoFormMutation`` passes ``unset_default=(DenyAll,)`` so an unset
      ``permission_classes`` denies rather than crashing in the model-permission
      default (spec-038 Decision 11 - there is no safe model-permission default
      without a model).
    - a bare ``str`` / ``bytes`` (a single name) or a bare class (forgot the
      enclosing sequence) -> ``ConfigurationError``: the contract is a *sequence*
      of permission classes.
    - any other non-iterable -> ``ConfigurationError``.
    - each entry must be a **class exposing a callable ``has_permission``** (the
      shape ``check_permission`` instantiates + calls); an instance, a non-class
      value, or a class without ``has_permission`` -> ``ConfigurationError``
      naming the offending entry.

    Returns the normalized IMMUTABLE tuple the snapshot stores, so the live
    authorization walk (``mutations/permissions.py::run_permission_classes``)
    can never be lengthened or emptied mid-request by a ``has_permission`` hook
    that mutates the class's list (a cleared live list short-circuits the walk
    to "all allowed" - an authorization bypass - and the emptied list would
    persist on the class, authorizing every later request). An explicit ``[]``
    is preserved as the documented allow-any opt-out for BOTH flavors (stored
    as the empty tuple).
    """
    if value is None:
        return tuple(unset_default)
    if isinstance(value, (str, bytes, type)):
        raise ConfigurationError(
            f"{base_label} {mutation_name}.Meta.permission_classes must be a sequence of "
            f"permission classes (e.g. [DjangoModelPermission]); got {_safe_arg_repr(value)}.",
        )
    try:
        classes = list(value)
    except BaseException as exc:
        raise ConfigurationError(
            f"{base_label} {mutation_name}.Meta.permission_classes must be a sequence of "
            f"permission classes (e.g. [DjangoModelPermission]); got {_safe_arg_repr(value)}.",
        ) from exc
    for entry in classes:
        try:
            has_perm = getattr(entry, "has_permission", None)
        except BaseException:
            has_perm = None
        if not isinstance(entry, type) or not callable(has_perm):
            raise ConfigurationError(
                f"{base_label} {mutation_name}.Meta.permission_classes entry "
                f"{_safe_arg_repr(entry)} is not a permission class exposing has_permission; "
                "each entry must be a class with a "
                "has_permission(info, mutation, operation, data, instance) method.",
            )
    # The validated snapshot is stored IMMUTABLE: a mutable list reachable from
    # the mutation class could be emptied or reordered by a ``has_permission``
    # hook (which receives the mutation class), turning deny-closed into the
    # allow-any posture for every later request. The walk reads this snapshot.
    return tuple(classes)


def validate_select_for_update(flavor: str, mutation_name: str, meta: Any) -> bool:
    """Validate ``Meta.select_for_update`` for a model-backed flavor (0.0.14 concurrency hardening).

    Every model-backed write flavor (model / ``ModelForm`` / serializer) shares
    this ONE validator so the key's contract cannot drift: the update / delete
    locate and every relation-target check acquire a base-manager ``SELECT ...
    FOR UPDATE`` (constrained by the visibility pk subquery) inside the write
    transaction. The default is ``True`` - locked writes are the safe posture;
    an explicit ``False`` opts into weaker concurrency (a row located this
    transaction may be concurrently modified, surfacing as the in-band
    ``conflict`` envelope instead of waiting on the lock). On a backend without
    ``FOR UPDATE`` (sqlite) Django skips the clause silently, so ``True`` is
    safe to leave in place regardless of backend. A non-bool is a clear
    class-creation error.
    """
    select_for_update = getattr(meta, "select_for_update", True)
    if not isinstance(select_for_update, bool):
        raise ConfigurationError(
            f"{flavor} {mutation_name}.Meta.select_for_update must be a bool; got "
            f"{_safe_arg_repr(select_for_update)}.",
        )
    return select_for_update


def model_backed_permission_and_lock(
    name: str,
    meta: type,
    *,
    flavor: str,
) -> tuple[tuple[Any, ...], bool]:
    """Return ``(permission_classes, select_for_update)`` for a model-backed write flavor.

    Every model-backed ``_validate_meta`` (model / ModelForm) pairs the
    ``DjangoModelPermission`` default with the ``FOR UPDATE`` lock validator.
    The model-less plain form does NOT call this (DenyAll default, no row to
    lock, plus the extra model-permission reject). The serializer flavor
    interleaves other Meta keys between the lock and the permission walk, so
    it keeps calling the two primitives in that order rather than this pair.
    """
    permission_classes = _validate_permission_classes(
        name,
        getattr(meta, "permission_classes", None),
        base_label=flavor,
    )
    return permission_classes, validate_select_for_update(flavor, name, meta)


# Model-flavor metaclass: validate ``Meta`` + register onto the model declaration
# ledger. Built by ``make_meta_validating_metaclass`` (the Decision-13 twin of
# ``make_declaration_registry``) so the plain-form flavor instantiates the SAME
# validate-then-register lifecycle over ``register_form_mutation``.
DjangoMutationMetaclass = make_meta_validating_metaclass(
    register_mutation,
    name="DjangoMutationMetaclass",
    module=__name__,
)


class DjangoMutation(metaclass=DjangoMutationMetaclass):
    """Consumer-facing write-side base class (spec-036 Decision 3 / Decision 5).

    A concrete mutation declares a nested ``class Meta`` with ``model`` +
    ``operation`` (and optional ``input_class`` / ``partial_input_class`` /
    ``fields`` / ``exclude`` / ``permission_classes``); the metaclass validates it
    at class creation and registers it for the phase-2.5 bind. Uniform with
    ``DjangoType`` / ``FilterSet`` / ``OrderSet`` - a base class with a nested
    ``Meta``, never a decorator.

    A declared mutation is inert until a field exposes it: it is registered +
    bound at finalize (its generated ``Input`` / ``PartialInput`` /
    ``<Name>Payload`` classes are materialized), but never resolved. The
    resolver pipeline, the ``DjangoMutationField`` factory, and permission
    *enforcement* live in ``resolvers.py`` + ``fields.py``.
    """

    # The validated ``Meta`` snapshot the metaclass stashes on a concrete
    # subclass; the bind and the resolver read it. ``None`` on the abstract
    # base (which carries no ``Meta``).
    _mutation_meta: _ValidatedMutationMeta | None = None

    # Bind outputs. The phase-2.5 bind
    # stashes the resolved primary type, the materialized input class (create /
    # update; ``None`` for delete), and the materialized payload class name here;
    # ``DjangoMutationField`` reads them to synthesize the resolver signature +
    # the ``strawberry.lazy`` payload return-ref. Left ``None`` until the bind runs.
    _primary_type: type | None = None
    _input_class: type | None = None
    _payload_type_name: str | None = None
    # Bind-stashed reverse map the model decode rides
    # (``utils/write_values.py::decode_provided_fields``). ``None`` until bind
    # (and stays ``None`` for ``delete``, which has no input). Form / serializer
    # subclasses overwrite ``_input_field_specs`` with their own flavor map.
    _input_field_specs: list | None = None
    _model_fields_by_attr: dict | None = None

    @classmethod
    def _resolve_model(cls, meta: type) -> type[models.Model] | None:
        """Resolve the mutation's Django model from ``Meta`` (the model-resolution seam).

        In 0.0.11 the only source is ``Meta.model``. This is the overridable hook
        the 0.0.12 form flavor (``Meta.form_class._meta.model``) and the 0.0.13
        serializer flavor (``Meta.serializer_class.Meta.model``) replace so they
        supply the model WITHOUT a literal ``Meta.model``, without re-opening the
        base validation (spec-036 Decision 5). A subclass overrides this
        classmethod to change the resolved model.
        """
        return getattr(meta, "model", None)

    @classmethod
    def _validate_meta(cls, meta: type) -> _ValidatedMutationMeta:
        """Validate a concrete mutation's nested ``Meta`` at class creation (spec-036 Decision 5).

        The overridable validation seam the metaclass invokes
        (``DjangoMutationMetaclass.__new__``). This default is the **model flavor**
        (the 0.0.11 body relocated verbatim from the former module-level
        ``_validate_mutation_meta``); the spec-038 form flavors override it with
        their own matrix (``forms/sets.py``). The validation matrix (raising
        ``ConfigurationError`` naming the offending key, all at class-creation):

        - **unknown ``Meta`` key** - the typo guard over
          ``_ALLOWED_MUTATION_META_KEYS`` (own keys only, no MRO walk), mirroring
          ``types/base.py::_validate_meta``.
        - **no resolvable model** - ``cls._resolve_model(meta)`` returns ``None``
          (in 0.0.11 a missing ``Meta.model``; the seam lets the 0.0.12 / 0.0.13
          flavors supply it differently).
        - **resolved model is not a Django model class** - a string name, a model
          instance, or any non-``models.Model`` type (mirrors
          ``types/base.py::_validate_meta``; without this the bind crashes with a
          raw ``AttributeError`` / ``TypeError``).
        - **bad ``operation``** - missing or not in
          ``{"create", "update", "delete"}``.
        - **``fields`` + ``exclude`` both supplied** - mutual exclusion.
        - **unknown / empty ``fields`` / ``exclude`` on create/update** - the
          ``editable_input_fields`` walk the bind uses, so a typo'd name or an
          empty narrowing fails at class creation (not deferred to finalize).
        - **inapplicable consumer input override** - ``input_class`` on anything
          other than create, or ``partial_input_class`` on anything other than
          update; delete accepts neither because it has no input.
        - **bad ``input_class`` / ``partial_input_class``** - not a
          ``@strawberry.input`` type, or field names diverging from the generated
          scheme.

        ``permission_classes`` + ``select_for_update`` are validated by
        ``model_backed_permission_and_lock`` (the ``DjangoModelPermission``
        default when unset, plus the ``FOR UPDATE`` lock). A bad permission
        entry is rejected here at class creation rather than as a request-time
        ``TypeError`` / ``AttributeError`` inside ``check_permission``
        (spec-036 Decision 15 - the write-auth seam; the enforcement runs in
        the resolver).
        """
        name = cls.__name__
        reject_unknown_meta_keys(f"DjangoMutation {name}", meta, _ALLOWED_MUTATION_META_KEYS)

        model = cls._resolve_model(meta)
        if model is None:
            raise ConfigurationError(
                f"DjangoMutation {name}.Meta declares no resolvable model; set Meta.model.",
            )
        # Mirror ``types/base.py::_validate_meta``: a non-model value (a string name,
        # a model *instance*, an unrelated class) must fail at class creation as
        # ``ConfigurationError``. Without this gate the bad value is snapshotted and
        # the phase-2.5 bind crashes with a raw ``AttributeError`` / ``TypeError``
        # (``model.__name__`` / unhashable instance) instead of a typed config error.
        # Shared with ModelForm / serializer ``_validate_meta`` via
        # ``require_model_class`` so those overrides cannot skip the gate.
        model = require_model_class(name, model, base_label="DjangoMutation")

        operation = getattr(meta, "operation", None)
        if not isinstance(operation, str) or not _safe_frozenset_membership(
            operation,
            _VALID_OPERATIONS,
        ):
            raise ConfigurationError(
                f"DjangoMutation {name}.Meta.operation must be one of "
                f"{sorted(_VALID_OPERATIONS)}; got {_safe_arg_repr(operation)}.",
            )

        # The model-flavor field-sequence pair routes through the shared
        # ``normalize_meta_field_selection`` (spec-039 - no per-flavor
        # re-binding wrapper); the ``DjangoMutation`` flavor label keeps the
        # messages byte-identical.
        fields, exclude = normalize_meta_field_selection(meta, flavor="DjangoMutation")
        if fields is not None and exclude is not None:
            raise ConfigurationError(
                f"DjangoMutation {name}.Meta declares both `fields` and `exclude`; "
                "supply at most one.",
            )
        if operation == "delete" and (fields is not None or exclude is not None):
            # A ``delete`` is ``id:``-only and materializes NO input (spec-036
            # Decision 14), so ``fields`` / ``exclude`` have no effect. Because
            # delete skips input generation, an unknown / malformed name in them is
            # never validated by ``editable_input_fields`` either, so a typo'd field
            # silently finalizes. Reject the inapplicable keys outright: declaring
            # them on a delete is a configuration mistake regardless of whether the
            # names are valid.
            raise ConfigurationError(
                f"DjangoMutation {name}.Meta.operation is 'delete', which is id-only and "
                "takes no input; remove the inapplicable Meta.fields / Meta.exclude.",
            )

        # Create / update materialize an input from the editable column set. Run the
        # SAME ``editable_input_fields`` walk the bind / generator use NOW so an
        # unknown / non-editable name and an empty narrowing fail at class creation
        # (the form flavor's posture via ``resolve_effective_form_fields``), not as a
        # deferred finalize-time ``ConfigurationError`` after the class already
        # registered. Delete is excluded above (it takes no input).
        if operation != "delete":
            selected = editable_input_fields(model, fields=fields, exclude=exclude)
            if not selected:
                raise ConfigurationError(
                    f"DjangoMutation {name}.Meta.fields / Meta.exclude narrowed the "
                    f"editable column set to empty (or {_safe_class_name(model)} declares no "
                    f"editable columns). A {operation} mutation input must define at "
                    "least one field.",
                )

        # Reject consumer input overrides that the declared operation cannot use.
        # Delete has no input; create and update each read only their matching
        # override. Without this guard, a valid customization is accepted and then
        # silently discarded at bind time. The same mapping selects the override in
        # ``_materialize_input_for``, so validation cannot drift from materialization.
        for applies_to, override_key in _OPERATION_INPUT_OVERRIDE_ATTR.items():
            if operation != applies_to and getattr(meta, override_key, None) is not None:
                raise ConfigurationError(
                    f"DjangoMutation {name}.Meta.{override_key} applies only to "
                    f"operation='{applies_to}' (it customizes the {applies_to} input); this "
                    f"mutation declares operation={operation!r}, so Meta.{override_key} would be "
                    "silently ignored at the bind. Remove it.",
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

        permission_classes, select_for_update = model_backed_permission_and_lock(
            name,
            meta,
            flavor="DjangoMutation",
        )

        return _ValidatedMutationMeta(
            model=model,
            operation=operation,
            input_class=input_class,
            partial_input_class=partial_input_class,
            fields=fields,
            exclude=exclude,
            permission_classes=permission_classes,
            select_for_update=select_for_update,
        )

    # Module path the generated input class is materialized into - the
    # ``strawberry.lazy`` target ``DjangoMutationField`` references for
    # the ``data:`` argument. The model default is ``mutations.inputs``; the form
    # flavors override it to ``forms.inputs`` (a disjoint namespace). A class
    # attribute (not a classmethod) because it has no per-``Meta`` dependence.
    input_module_path: str = INPUTS_MODULE_PATH

    @classmethod
    def build_input(cls, meta: _ValidatedMutationMeta, primary_type: type) -> type | None:
        """Build + materialize the operation's generated input class (the bind hook seam).

        The overridable input-materialization seam ``_bind_mutation`` calls at
        phase 2.5. The **model default** delegates to ``_materialize_input_for``
        (today's exact model behavior: the model-column ``<Model>Input`` /
        ``<Model>PartialInput`` built from the editable columns, or ``None`` for a
        ``delete``), then stashes ``_input_field_specs`` + ``_model_fields_by_attr``
        for the decode; the form flavors override it to build the form-derived input
        from ``forms/inputs.py`` instead (spec-038 Decision 13). Returning ``None``
        means "no input for this operation" (the model ``delete`` case).
        """
        input_cls = _materialize_input_for(cls.__name__, meta, primary_type)
        if input_cls is not None:
            # The decode's bind-time hand-off: total-coverage specs (merged
            # dataclass, consumer overrides included) + the Django-field index
            # (``relation_field.null`` and the ``_provided_attr_names``
            # FK-to-field-name reversal, spec-036 M3-1).
            cls._input_field_specs, cls._model_fields_by_attr = mutation_input_field_specs(
                meta.model,
                input_cls,
            )
        return input_cls

    @classmethod
    def input_type_name(cls, meta: _ValidatedMutationMeta) -> str:
        """Return the generated input class name for a create / update mutation (the name seam).

        The overridable input-name seam ``mutations/fields.py`` consults
        to synthesize the lazy ``data:`` forward-ref. The **model default** reads
        ``mutation_input_shape(...).type_name`` - the SAME descriptor the bind /
        ``build_mutation_input`` path uses for the materialize name and the shape
        cache key, so the field's lazy ``data:`` ref can never disagree
        with the class the bind pins. The form flavors override it with
        ``forms/inputs.py::form_input_type_name``.

        Spec-038 rewired ``mutations/fields.py::_synthesized_mutation_signature``
        to consult this seam (deleting the transient ``_input_type_name`` twin), so
        this is now the single source for the model ``data:`` lazy-ref name.

        A validated ``delete`` raises the typed ``ConfigurationError`` (never the
        raw ``KeyError`` a direct index leaked): a delete is id-only and
        materializes no input, and the framework never consults this seam for one
        (``operation_takes_data`` gates the ``data:`` ref at the field factory), so
        only a direct consumer call can reach the reject - where it must still fail
        loud as the package's typed error, mirroring ``_materialize_input_for``'s
        ``.get()`` delete short-circuit.
        """
        operation_kind = NON_DELETE_OPERATION_INPUT_KIND.get(meta.operation)
        if operation_kind is None:
            raise ConfigurationError(
                f"DjangoMutation {cls.__name__} declares operation='delete', which is "
                "id-only and materializes no input; input_type_name applies only to "
                "create / update mutations.",
            )
        return mutation_input_shape(
            meta.model,
            operation_kind,
            fields=meta.fields,
            exclude=meta.exclude,
        ).type_name

    # The overridable sync / async resolver-dispatch seams
    # (``mutations/fields.py::_resolve`` calls them). The **model default** delegates
    # to ``mutations/resolvers.py::resolve_mutation_sync`` / ``resolve_mutation_async``
    # (the function-local import inside the generated seam keeps the module-load order
    # independent of ``resolvers.py``); the form + serializer flavors override this
    # pair with their own ``resolver_seams(...)`` call (the eight
    # near-identical seam bodies single-sited as one factory).
    resolve_sync, resolve_async = resolver_seams(
        "django_strawberry_framework.mutations.resolvers",
        "resolve_mutation_sync",
        "resolve_mutation_async",
    )

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
        denies and ``True`` only when all allow. The resolver maps a ``False``
        return to a raised ``GraphQLError`` (the top-level authorization failure,
        distinct from the field-keyed validation envelope).

        **Defined here; invoked only by the resolver**, at
        the pipeline placement spec-036 Decision 8 step 3 / Decision 15 pins
        (before the write for ``create``; after the visibility lookup for
        ``update`` / ``delete``). This module ships only the default method body
        + the ``permission_classes`` default assignment; the raise-on-denial lives
        in ``resolvers.py``.

        An ``async def has_permission`` entry returns a coroutine, which is truthy:
        a naive ``if not has_permission(...)`` would never deny it, so an async
        deny-check would be silently treated as ALLOW - an authorization bypass. The pipeline
        is synchronous (spec-036 Decision 15), so the coroutine can never be awaited here;
        it is closed and raised as a ``SyncMisuseError``, the same discipline
        ``apply_type_visibility_sync`` applies to an async ``get_queryset``. (An async
        ``check_permission`` override is caught by the resolver's ``authorize_or_raise`` one
        level up.)

        The walk body is single-sited in
        ``mutations/permissions.py::run_permission_classes``,
        shared with the plain ``DjangoFormMutation`` (which is not a
        ``DjangoMutation`` subclass), so the authorization seam cannot fork.
        """
        return run_permission_classes(self, info, operation, data, instance)


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
            f"DjangoMutation {_safe_class_name(mutation_cls)} targets {_safe_class_name(model)}, which has "
            "multiple registered DjangoTypes and no declared primary; set Meta.primary on "
            "one of them so the mutation return type is unambiguous.",
        )
    raise ConfigurationError(
        f"DjangoMutation {_safe_class_name(mutation_cls)} targets {_safe_class_name(model)}, which has no "
        "registered DjangoType; the mutation has no type to return. Declare a "
        f"DjangoType for {_safe_class_name(model)}.",
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
    replacement (the spec-010 relation-override contract, spec-036 DoD): the
    consumer declares the field(s) it wants to customize
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
    still raise the collision.
    """
    operation_kind = NON_DELETE_OPERATION_INPUT_KIND.get(meta.operation)
    if operation_kind is None:
        return None  # delete: id-only, no input.

    consumer_input = getattr(meta, _OPERATION_INPUT_OVERRIDE_ATTR[meta.operation])
    if consumer_input is not None:
        return _materialize_merged_input(
            mutation_name,
            meta,
            primary_type,
            operation_kind,
            consumer_input,
        )

    # Derive the shape ONCE: ``mutation_input_shape`` single-sources the
    # cache key (the EFFECTIVE field set, NOT the raw ``(fields, exclude)``
    # spelling - two narrowings to one effective shape must dedupe, spec-036
    # Edge cases #"Two mutations over one model") AND the generated name, so the
    # bind cache key and the generated type name cannot drift. The same
    # descriptor is handed to
    # ``build_mutation_input`` so it does not re-walk the editable fields.
    shape = mutation_input_shape(
        meta.model,
        operation_kind,
        fields=meta.fields,
        exclude=meta.exclude,
    )
    input_cls = get_or_store_shape_build(
        _shape_build_cache,
        shape.cache_key,
        lambda: build_mutation_input(
            meta.model,
            operation_kind=operation_kind,
            primary_type=primary_type,
            fields=meta.fields,
            exclude=meta.exclude,
            shape=shape,
        ),
    )
    materialize_mutation_input_class(input_cls.__name__, input_cls)
    return input_cls


def _materialize_merged_input(
    mutation_name: str,
    meta: _ValidatedMutationMeta,
    primary_type: type,
    operation_kind: str,
    consumer_input: type,
) -> type:
    """Merge a consumer ``input_class`` with the generated remainder (spec-010).

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
    (``shape.type_name`` from the shared ``mutation_input_shape`` descriptor,
    derived from the full selected field set, which still includes the overridden
    columns, so it is the same ``<Model>Input`` / shape-derived name the
    all-generated path uses): the consumer customizes representations of existing
    columns, it does NOT change the shape identity ``(model, operation kind,
    frozenset(effective names))``. A merged input is therefore NOT cached in
    ``_shape_build_cache`` (it is mutation-specific), and if two mutations resolve
    the same shape to two different representations they collide on that name and
    raise the ``ConfigurationError`` at ``materialize_mutation_input_class`` -
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
    """Type- and shape-lock a relation override to the generated id (spec-036 Decision 10).

    A relation column whose related model HAS a primary Relay-Node type generates a
    ``relay.GlobalID`` (forward FK / OneToOne) or ``list[relay.GlobalID]`` (M2M) input
    whose decode is **type-checked against the relation target** AND
    **visibility-checked through the related type's ``get_queryset``** (spec-036
    Decision 10) - so a permitted writer cannot attach a row they could
    not *see*. Both guarantees ride the EXACT generated shape:
    ``utils/write_values.py::decode_visible_relation_ids`` type-checks a
    ``relay.GlobalID`` against the relation target (the FK path unwraps a
    one-element list, the M2M path iterates a flat list) and coerces anything else
    as a raw pk.

    The naming half (``_validate_input_class``) lets a consumer override a
    relation field's *representation* under its generated ``<field>_id`` / ``list``
    name, but it name-checks only - so a consumer could declare a divergent TYPE or
    CONTAINER SHAPE and the merge would honor it, defeating the decode:

    - ``category_id: int`` (raw pk core) - the value is seen as a non-``GlobalID`` raw
      pk and passed through, bypassing both the type-check and the visibility
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
    divergence in core type or list depth is a fail-loud ``ConfigurationError``,
    caught at the bind rather than crashing a request.

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
                f"{_safe_class_name(field.related_model)} has a primary Relay-Node type, so the {kind} "
                f"relation input is {expected} - type- and visibility-checked at decode (spec-036 "
                "Decision 10). A divergent core type or container shape would be passed "
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


def bind_mutation_outputs(
    mutation_cls: type,
    *,
    input_cls: type | None,
    object_type: type | None,
) -> None:
    """Build the payload, materialize it, and stash bind outputs on ``mutation_cls``.

    The payload half of the phase-2.5 bind (the input half is the flavor's
    ``build_input`` seam; the input twin is ``build_and_stash_input``). Both
    declaration ledgers write the same three slots ``DjangoMutationField``
    reads after finalize (``_primary_type`` / ``_input_class`` /
    ``_payload_type_name``):

    - model-backed (``_bind_mutation``): ``object_type`` is the resolved
      primary ``DjangoType``; the payload carries ``payload_object_slot``;
    - model-less (``_bind_form_mutation``): ``object_type`` is ``None`` and
      the payload is the pinned ``{ ok errors }`` shape.

    Auth's login/logout holders use a fixed payload *name* (``"Login"`` /
    ``"Logout"``) rather than ``mutation_cls.__name__`` and do not stash
    ``_input_class``, so they stay local. Payload classes ride the SAME
    ``materialize_mutation_input_class`` ledger as the input classes (one
    ledger, one collision check, one ``registry.clear()`` co-clear).
    """
    payload_cls = build_payload_type(
        mutation_cls.__name__,
        object_type=object_type,
    )
    materialize_mutation_input_class(payload_cls.__name__, payload_cls)
    mutation_cls._primary_type = object_type
    mutation_cls._input_class = input_cls
    mutation_cls._payload_type_name = payload_cls.__name__


def bind_write_declarations(
    *,
    cache: dict,
    iterate: Callable[[], tuple[type, ...]],
    resolve_object_type: Callable[[type, Any], type | None],
) -> None:
    """Drain one write-declaration registry through the phase-2.5 bind.

    The ONE drain both write-declaration ledgers ride - the model-backed
    ``bind_mutations()`` (which the ``ModelForm`` and serializer flavors ride
    too, being ``DjangoMutation`` subclasses) and the model-less
    ``bind_form_mutations()``. ``finalize_django_types`` calls each in the
    phase-2.5 window, after primary-type state is settled and before
    ``strawberry.type(...)`` freezes the schema classes (spec-036 Decision 12).

    Per registered class: resolve the payload's object type, route the input
    materialization through the ``build_input`` seam (spec-038 Decision 13 - the
    model flavor rebuilds the model-column input, the form / serializer flavors
    build their own), and stash both through ``bind_mutation_outputs``.

    ``resolve_object_type`` is the ONLY per-ledger divergence: the model-backed
    drain resolves the primary ``DjangoType`` (raising for no-primary /
    ambiguous), the model-less drain answers ``None`` (which selects the pinned
    ``{ ok errors }`` payload and keeps ``_primary_type`` ``None``). Every
    flavor's ``build_input`` carries the same ``(meta, primary_type)`` signature
    so this one call reaches all of them.

    ``cache`` is the caller's own PER-PASS build cache, cleared at the top so
    each input is rebuilt fresh. The cross-pass materialization ledgers
    (``mutations.inputs`` / ``forms.inputs`` - the ``ModelForm`` flavor rides
    the model pass but writes the FORM ledger) are reset ONCE by
    ``finalize_django_types`` before the bind sequence so a recover-in-place
    re-finalize is retry-idempotent; they are NOT reset here, where a per-pass
    clear would wipe the sibling pass's already-materialized entries.
    """
    cache.clear()
    for mutation_cls in iterate():
        meta = mutation_cls._mutation_meta
        object_type = resolve_object_type(mutation_cls, meta)
        bind_mutation_outputs(
            mutation_cls,
            input_cls=mutation_cls.build_input(meta, object_type),
            object_type=object_type,
        )


def bind_mutations() -> None:
    """Bind every registered ``DjangoMutation`` (the finalizer phase-2.5 entry point).

    The model-backed rider of ``bind_write_declarations``: each declaration's
    payload object type is its resolved primary ``DjangoType``
    (``_resolve_primary_type`` raises for no-primary / ambiguous), so the bind
    materializes the operation's input class (``create`` / ``update``) and the
    per-mutation ``<Name>Payload`` as module globals of ``mutations.inputs``
    before ``strawberry.Schema(...)`` runs.
    """
    bind_write_declarations(
        cache=_shape_build_cache,
        iterate=iter_mutations,
        resolve_object_type=lambda mutation_cls, meta: _resolve_primary_type(
            mutation_cls,
            meta.model,
        ),
    )
