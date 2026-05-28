"""Internal Relay/interface helpers for the 0.0.5 Relay foundation slice.

Slice 2 introduced ``install_is_type_of``; Slice 4 extends this module with
the interface base-class injection step and the four Relay node resolver
defaults. The helpers split by lifecycle phase:

- Class-creation time (``__init_subclass__``): ``install_is_type_of``
  (Slice 2). Discriminator: ``cls.__dict__`` membership.
- Annotation synthesis time (``_build_annotations``): the
  ``relay.Node in interfaces`` tuple-membership check (Slice 3, in
  ``types/base.py``).
- Finalization Phase 2.5 (``finalize_django_types()``): ``apply_interfaces``,
  ``_check_composite_pk_for_relay_node``, ``install_relay_node_resolvers``
  (Slice 4). The last uses the ``__func__`` identity test that distinguishes
  consumer-overridden ``resolve_*`` methods from the ``relay.Node`` defaults
  inherited through MRO.

Direct ports of behavior from ``strawberry_django/type.py`` and
``strawberry_django/relay/utils.py`` cited in the spec; the upstream
package is not imported at runtime.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from django.db import models
from django.db.models import CompositePrimaryKey
from strawberry import relay
from strawberry.relay.exceptions import NodeIDAnnotationError
from strawberry.utils.inspect import in_async_context

from ..exceptions import ConfigurationError

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import (Slice 4 quoted hint).
    from .definition import DjangoTypeDefinition


class SyncMisuseError(ConfigurationError, RuntimeError):
    """Raised when a sync resolver context encounters an async ``get_queryset``.

    Typed marker for the "async ``get_queryset`` hook invoked from a
    sync resolver" misuse. Multiple-inherits ``ConfigurationError``
    AND ``RuntimeError`` so callers catching either base class still
    match:

    - ``except ConfigurationError`` (the package's convention for
      configuration-time errors).
    - ``except RuntimeError`` (the dispatcher branch in
      ``filters/sets.py::FilterSet.apply`` matches the typed subclass
      directly via ``except SyncMisuseError``; consumer code catching
      ``RuntimeError`` after the dispatcher rethrow also continues to
      work).

    Consumers who want a focused catch should match the subclass
    directly. Exported through ``django_strawberry_framework`` so it
    can be imported without reaching into private ``types.relay``.
    """


def implements_relay_node(type_cls: type) -> bool:
    """Return whether ``type_cls`` is a subclass of ``strawberry.relay.Node``.

    Used by ``finalize_django_types()`` Phase 2.5 (after ``__bases__``
    mutation) to decide whether to run the composite-pk gate and the
    four ``resolve_*`` defaults. Distinct from Slice 3's tuple-membership
    check (``relay.Node in interfaces`` at ``types/base.py``), which
    runs pre-base-injection at collection time against the validated
    ``Meta.interfaces`` tuple.
    """
    return issubclass(type_cls, relay.Node)


def install_is_type_of(type_cls: type) -> None:
    """Borrow strawberry-django's ``is_type_of`` virtual-subclass behavior.

    Direct port of ``strawberry_django/type.py::_process_type``
    (the ``if "is_type_of" not in cls.__dict__`` branch). Strawberry's
    interface dispatch uses ``is_type_of`` to identify the concrete type
    for a returned ORM instance. Without this borrow, an interface field
    that returns a Django model can fail Strawberry's isinstance check
    and surface as "Cannot determine type for object of model X" at
    runtime (spec-011 Decision 6 #"injection (Decision-1 borrow) is added unconditionally").

    Preserves a consumer-declared ``is_type_of`` via the ``cls.__dict__``
    membership check (the same discriminator strawberry-django uses); a
    function inherited from a base does not count as "declared on this
    class" and is overwritten by the framework default.

    The upstream ``get_strawberry_type_cast`` branch is intentionally
    omitted — our package does not yet expose ``strawberry.cast(...)``
    integration anywhere else, and adding it now would couple this slice
    to a Strawberry surface we have not committed to. If a future adopter
    needs ``strawberry.cast(...)`` support, a focused follow-up slice can
    add the branch without churn to the rest of the Relay machinery.
    """
    if "is_type_of" in type_cls.__dict__:
        return
    model = _model_for(type_cls)

    def is_type_of(obj: object, info: object) -> bool:
        return isinstance(obj, (type_cls, model))

    type_cls.is_type_of = is_type_of


def apply_interfaces(type_cls: type, definition: DjangoTypeDefinition) -> None:
    """Inject ``definition.interfaces`` into ``type_cls.__bases__`` (Phase 2.5).

    Skips interfaces already in ``type_cls.__mro__`` so a class that
    already inherits a listed interface directly (e.g. consumer wrote
    ``class Foo(DjangoType, relay.Node): class Meta: interfaces =
    (relay.Node,)``) sees no double-injection
    (spec-011 #"A class that already inherits from one of the listed",
    spec-011 #"only those not already present in",
    spec-011 #"Inherited interfaces via parent").

    Raises:
        ConfigurationError: a ``TypeError`` from ``cls.__bases__``
            assignment is wrapped with the offending interface named in
            the message so consumers see "cannot add interface X" rather
            than a raw layout TypeError
            (spec-011 Risk note #"surface any `TypeError` as a `ConfigurationError`").
    """
    additions = tuple(iface for iface in definition.interfaces if iface not in type_cls.__mro__)
    if not additions:
        return
    try:
        type_cls.__bases__ = (*type_cls.__bases__, *additions)
    except TypeError as exc:
        offending = ", ".join(iface.__name__ for iface in additions)
        raise ConfigurationError(
            f"{type_cls.__name__}: cannot add interface(s) {offending} to bases. "
            f"Python rejected the resulting MRO ({exc}). Either drop the "
            "incompatible interface from Meta.interfaces or rework the class "
            "hierarchy.",
        ) from exc


def _check_composite_pk_for_relay_node(type_cls: type) -> None:
    """Raise ``ConfigurationError`` when a Relay-declared type has a composite pk.

    Decision 2 (spec-011 #"Composite primary keys (Django 5.2+) are explicitly out of scope"):
    combining ``relay.Node`` with a composite-primary-key model is explicitly out of scope for
    ``0.0.5``. Detection uses ``isinstance(model._meta.pk,
    CompositePrimaryKey)`` so the gate aligns with Django 5.2+'s
    native composite-pk type.

    The error message proposes "declare an explicit ``id: relay.NodeID[...]``
    annotation" as a remediation; honor that here so a consumer who
    escapes the composite-pk surface with a single-column ``NodeID``
    annotation is not unconditionally rejected. Strawberry's
    ``Node.resolve_id_attr()`` returns the consumer's ``NodeID``
    attribute name when present and raises ``NodeIDAnnotationError``
    otherwise; only the latter case is the contract violation this
    gate is meant to catch.
    """
    model = _model_for(type_cls)
    if not isinstance(model._meta.pk, CompositePrimaryKey):
        return
    # Phase 2.5 ordering note: this calls upstream ``relay.Node.resolve_id_attr``
    # (our default is installed after this gate runs).
    try:
        type_cls.resolve_id_attr()  # type: ignore[attr-defined]
    except NodeIDAnnotationError:
        pass
    else:
        return
    raise ConfigurationError(
        f"{model.__name__}: relay.Node is not supported on models with a "
        "composite primary key. Either declare an explicit id: "
        "relay.NodeID[...] annotation on the DjangoType or remove "
        "relay.Node from Meta.interfaces.",
    )


def _resolve_id_attr_default(cls: type) -> str:
    """Default ``Node.resolve_id_attr`` — falls back to ``"pk"``.

    Calls ``super(cls, cls).resolve_id_attr()`` so a consumer
    ``id: relay.NodeID[...]`` annotation on the class wins; on
    ``NodeIDAnnotationError`` falls back to ``"pk"``. Direct port of
    ``strawberry_django/relay/utils.py::resolve_model_id_attr``.
    """
    try:
        return super(cls, cls).resolve_id_attr()  # type: ignore[misc]
    except NodeIDAnnotationError:
        return "pk"


def _resolve_id_default(cls: type, root: models.Model, *, info: Any) -> str:
    """Default ``Node.resolve_id`` with a ``__dict__`` cache check.

    Signature mirrors ``strawberry.relay.Node.resolve_id`` after
    ``classmethod`` binding: ``(cls, root, *, info)``. ``info`` is
    keyword-only so Strawberry's Relay machinery, which calls
    ``cls.resolve_id(root, info=info)``, lands at the right slot without
    a positional collision (review feedback ``feedback.md`` § High).

    Calls ``cls.resolve_id_attr()`` to derive the column name (handles
    consumer ``relay.NodeID[...]`` overrides and the ``"pk"`` fallback),
    coerces the literal ``"pk"`` to the model's concrete pk ``attname``
    so the dict-cache lookup keys on the real column, then reads from
    ``root.__dict__`` first (avoids an extra ORM hit when the optimizer
    already loaded the row) and falls back to ``getattr(root, id_attr)``
    (spec-011 #"id_attr = cls.resolve_id_attr" / Decision 7's "no
    avoidable lazy loads on ``resolve_id``").

    Keying on ``root.__class__._meta.pk.attname`` is deliberate: the
    alternative ``cls.__django_strawberry_definition__.model._meta.pk.attname``
    would mis-key the ``__dict__`` lookup for proxy-model rows whose actual
    class differs from the declared DjangoType model.
    """
    id_attr = cls.resolve_id_attr()
    if id_attr == "pk":
        id_attr = root.__class__._meta.pk.attname
    try:
        return str(root.__dict__[id_attr])
    except KeyError:
        return str(getattr(root, id_attr))


def _apply_get_queryset_sync(cls: type, qs: models.QuerySet, info: Any) -> models.QuerySet:
    """Run ``cls.get_queryset`` in a sync context; reject async hooks loudly.

    Decision 9 makes a consumer's ``DjangoType.get_queryset`` allowed to
    be sync or async, but a sync resolver context cannot await an async
    hook safely (event-loop edge cases dominate the bridge). On the sync
    path we therefore close the unawaited coroutine to silence the
    "coroutine was never awaited" warning and raise a named
    ``ConfigurationError`` that points the consumer at the async resolver
    path or a sync ``get_queryset`` rewrite (review feedback
    ``feedback.md`` § High "Async ``get_queryset`` is not awaited in
    Relay node defaults").
    """
    result = cls.get_queryset(qs, info)
    if inspect.iscoroutine(result):
        result.close()
        raise SyncMisuseError(
            f"{cls.__name__}.get_queryset returned a coroutine in a sync "
            "resolver context. The Relay node defaults only await async "
            "get_queryset hooks on the async branch; either invoke the "
            "Relay node default from an async resolver, or redefine "
            "get_queryset as a sync method.",
        )
    return result


async def _apply_get_queryset_async(cls: type, qs: models.QuerySet, info: Any) -> models.QuerySet:
    """Run ``cls.get_queryset`` in an async context, awaiting awaitables.

    Sync ``get_queryset`` returns the queryset directly and is passed
    through. Async ``get_queryset`` returns a coroutine which is awaited
    here before the id filter runs — the Decision 9 contract that the
    previous implementation broke (it called the hook synchronously then
    invoked ``.filter`` on a coroutine).
    """
    result = cls.get_queryset(qs, info)
    if inspect.isawaitable(result):
        result = await result
    return result


# TODO(spec-021-filters-0_0_8 Slice 1): Reuse these sync/async visibility
# helpers from FilterSet's related-branch scoping so parent-row filtering
# cannot bypass a target DjangoType.get_queryset hook.
# Pseudocode:
#   child_base = child_model._default_manager.all()  # noqa: ERA001
#   child_qs = _apply_get_queryset_sync(target_type, child_base, info)  # noqa: ERA001
#   child_qs = child_qs & related_filter.queryset if constraint exists
#   parent_qs = parent_qs.filter(**{f"{relation_name}__in": child_qs})  # noqa: ERA001
def _coerce_node_id(node_id: Any) -> Any:
    return node_id.node_id if isinstance(node_id, relay.GlobalID) else node_id


def _coerce_node_ids(node_ids: Any) -> list[Any] | None:
    if node_ids is None:
        return None
    return [_coerce_node_id(node_id) for node_id in node_ids]


def _apply_node_filter(
    qs: models.QuerySet,
    id_attr: str,
    *,
    node_id: Any = None,
    node_ids: list[Any] | None = None,
) -> models.QuerySet:
    """Apply the Relay-id filter to ``qs`` (color-agnostic).

    The lazy ``.filter`` call is identical on sync and async paths; the
    terminal materialization is what differs (``.get``/``.first`` on the
    sync path, ``.aget``/``.afirst`` on the async path).
    """
    if node_id is not None:
        coerced = _coerce_node_id(node_id)
        return qs.filter(**{id_attr: coerced})
    if node_ids is not None:
        return qs.filter(**{f"{id_attr}__in": node_ids})
    return qs


def _model_for(cls: type) -> type[models.Model]:
    """Return the registered model for ``cls.__django_strawberry_definition__``.

    Centralizes the ``cls.__django_strawberry_definition__.model`` lookup
    so model-only reads share one source of truth with the queryset-variant
    lookup in ``_initial_queryset``. Mirrors ``_initial_queryset``'s
    contract: callers are responsible for ``cls`` being a registered
    ``DjangoType``; a missing definition surfaces as a raw ``AttributeError``.
    """
    return cls.__django_strawberry_definition__.model


def _initial_queryset(cls: type) -> models.QuerySet:
    """Return ``model._default_manager.all()`` for the declared model.

    Centralizes the ``cls.__django_strawberry_definition__.model``
    lookup so both the sync and async assembly paths share one source of
    truth for step 1 of the Decision 3 four-step shape.
    """
    return _model_for(cls)._default_manager.all()


def _order_nodes(
    cls: type,
    results: list,
    coerced_keys: list[str],
    id_attr: str,
    *,
    required: bool,
) -> list:
    """Re-order ``results`` to match ``coerced_keys`` (port of strawberry-django's map_results).

    Mirrors ``strawberry_django/relay/utils.py::resolve_model_nodes #"def map_results"``: build an index
    keyed on ``str(getattr(obj, id_attr))`` (so the dict lookup matches
    the ``coerced_keys`` shape — both are ``str``) and emit one entry per
    requested key.

    ``required=True`` raises the model's ``DoesNotExist`` for any missing
    key — homogeneous with ``_resolve_node_default``'s ``qs.get()`` so
    consumers writing visibility-aware exception handling can catch a
    single exception type for the "required missing id" semantic.
    ``required=False`` emits ``None`` for missing keys.
    """
    index = {str(getattr(obj, id_attr)): obj for obj in results}
    output: list = []
    model = _model_for(cls)
    for key in coerced_keys:
        if required:
            try:
                output.append(index[key])
            except KeyError as exc:
                raise model.DoesNotExist(
                    f"{model.__name__}: no row matching {id_attr}={key!r}.",
                ) from exc
        else:
            output.append(index.get(key))
    return output


def _resolve_node_default(
    cls: type,
    node_id: Any,
    *,
    info: Any,
    required: bool = False,
) -> Any:
    """Default ``Node.resolve_node`` — ``get_queryset`` aware.

    Signature mirrors ``strawberry.relay.Node.resolve_node`` after
    ``classmethod`` binding: ``(cls, node_id, *, info, required=False)``.
    ``info`` is keyword-only so Strawberry's runtime call shape
    (``cls.resolve_node(node_id, info=info, required=...)``) lands
    correctly. An earlier draft used ``(cls, info, node_id, ...)`` which
    Strawberry's machinery turned into ``TypeError: got multiple values
    for argument 'info'`` (review feedback ``feedback.md`` § High).

    Returns the single matching row (``qs.get()`` when ``required``,
    ``qs.first()`` otherwise). Async detection uses
    ``strawberry.utils.inspect.in_async_context``; on the async branch
    the returned coroutine awaits ``get_queryset`` (so async
    ``get_queryset`` hooks are honored), applies the id filter, and
    awaits ``aget``/``afirst``. On the sync branch a coroutine returned
    from ``get_queryset`` is rejected with ``ConfigurationError`` rather
    than silently producing ``AttributeError: 'coroutine' object has no
    attribute 'filter'`` (review feedback ``feedback.md`` § High "Async
    ``get_queryset`` is not awaited in Relay node defaults").
    """
    id_attr = cls.resolve_id_attr()
    if in_async_context():
        return _resolve_node_async(cls, id_attr, node_id, info=info, required=required)
    qs = _apply_get_queryset_sync(cls, _initial_queryset(cls), info)
    qs = _apply_node_filter(qs, id_attr, node_id=node_id)
    return qs.get() if required else qs.first()


async def _resolve_node_async(
    cls: type,
    id_attr: str,
    node_id: Any,
    *,
    info: Any,
    required: bool,
) -> Any:
    """Async sibling of ``_resolve_node_default``.

    Awaits the ``get_queryset`` hook (regardless of whether the consumer
    declared it ``def`` or ``async def``) before applying the id filter
    and the final ``aget``/``afirst``. Decision 9 of the spec promises
    both shapes; this is the awaitable that actually delivers on that
    contract.
    """
    qs = await _apply_get_queryset_async(cls, _initial_queryset(cls), info)
    qs = _apply_node_filter(qs, id_attr, node_id=node_id)
    return await (qs.aget() if required else qs.afirst())


def _resolve_nodes_default(
    cls: type,
    *,
    info: Any,
    node_ids: Any = None,
    required: bool = False,
) -> Any:
    """Default ``Node.resolve_nodes`` — order-preserving, missing-aware.

    Signature mirrors ``strawberry.relay.Node.resolve_nodes`` after
    ``classmethod`` binding: ``(cls, *, info, node_ids, required=False)``.
    ``node_ids`` defaults to ``None`` here (Strawberry's upstream slot is
    a required keyword argument) so the package can offer the bulk-fetch
    "no ids -> full queryset" path documented in the spec without
    forcing callers to thread ``node_ids=None`` explicitly.

    When ``node_ids`` is ``None`` returns the filtered queryset (the
    caller materializes via iteration as needed). When ``node_ids`` is
    provided, returns a list whose indexes correspond 1:1 with
    ``node_ids``: ``required=False`` yields ``None`` for missing ids,
    ``required=True`` raises the model's ``DoesNotExist`` for missing
    ids (homogeneous with ``_resolve_node_default``'s ``qs.get()``).

    Async detection routes through ``in_async_context`` so async
    ``get_queryset`` hooks are awaited before the id filter; in the
    async branch the caller must ``await`` the call to obtain either
    the queryset (``node_ids=None``) or the order-preserving list
    (``node_ids`` provided). Sync resolver contexts cannot await an
    async ``get_queryset`` hook and surface ``ConfigurationError``
    instead (review feedback ``feedback.md`` § High).
    """
    id_attr = cls.resolve_id_attr()
    if in_async_context():
        return _resolve_nodes_async(cls, id_attr, node_ids, info=info, required=required)
    qs = _apply_get_queryset_sync(cls, _initial_queryset(cls), info)
    coerced_ids = _coerce_node_ids(node_ids)
    qs = _apply_node_filter(qs, id_attr, node_ids=coerced_ids)
    if coerced_ids is None:
        return qs
    coerced_keys = [str(node_id) for node_id in coerced_ids]
    return _order_nodes(cls, list(qs), coerced_keys, id_attr, required=required)


async def _resolve_nodes_async(
    cls: type,
    id_attr: str,
    node_ids: Any,
    *,
    info: Any,
    required: bool,
) -> Any:
    """Async sibling of ``_resolve_nodes_default``.

    Awaits the ``get_queryset`` hook before applying the id filter so
    async ``get_queryset`` hooks are honored. Returns the queryset
    directly when ``node_ids`` is ``None`` (the caller materializes via
    ``async for``); when ``node_ids`` is provided, materializes via
    ``async for`` and returns the order-preserving list shape.
    """
    qs = await _apply_get_queryset_async(cls, _initial_queryset(cls), info)
    coerced_ids = _coerce_node_ids(node_ids)
    qs = _apply_node_filter(qs, id_attr, node_ids=coerced_ids)
    if coerced_ids is None:
        return qs
    coerced_keys = [str(node_id) for node_id in coerced_ids]
    results = [obj async for obj in qs]
    return _order_nodes(cls, results, coerced_keys, id_attr, required=required)


# Single source of truth for the four Relay resolver method names plus the
# framework default implementation each one maps to. Iterated by
# ``install_relay_node_resolvers``; appears nowhere else.
_RELAY_RESOLVER_DEFAULTS: tuple[tuple[str, Callable[..., Any]], ...] = (
    ("resolve_id", _resolve_id_default),
    ("resolve_id_attr", _resolve_id_attr_default),
    ("resolve_node", _resolve_node_default),
    ("resolve_nodes", _resolve_nodes_default),
)


def install_relay_node_resolvers(type_cls: type) -> None:
    """Inject the four ``resolve_*`` defaults via the ``__func__`` identity test.

    For each ``(name, default)`` pair in ``_RELAY_RESOLVER_DEFAULTS``:

    - Look up the inherited method on ``type_cls`` (resolves through MRO
      to ``relay.Node``'s default if no consumer override exists).
    - Compare ``existing.__func__`` to ``relay.Node.<attr>.__func__``.
      When they match (or ``existing`` is ``None``), the consumer has
      not overridden the method and the framework default is installed
      via ``setattr(type_cls, attr, classmethod(default))``.
    - When they differ, the consumer's override wins and is preserved.

    Direct port of ``strawberry_django/type.py::_process_type``
    (the ``if issubclass(cls, relay.Node)`` branch). The ``__func__``
    discriminator is structurally distinct from Slice 2's ``__dict__``
    membership discriminator (``is_type_of`` injection) and Slice 3's
    tuple-membership discriminator (``relay.Node in interfaces``) — the
    three answer different questions at three lifecycle phases.
    """
    for attr, default_impl in _RELAY_RESOLVER_DEFAULTS:
        existing = getattr(type_cls, attr, None)
        node_default = getattr(relay.Node, attr, None)
        existing_func = getattr(existing, "__func__", None)
        node_func = getattr(node_default, "__func__", None)
        if existing is None or (existing_func is not None and existing_func is node_func):
            setattr(type_cls, attr, classmethod(default_impl))
