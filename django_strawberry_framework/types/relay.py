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

    Direct port of ``strawberry_django/type.py:203-211``. Strawberry's
    interface dispatch uses ``is_type_of`` to identify the concrete type
    for a returned ORM instance. Without this borrow, an interface field
    that returns a Django model can fail Strawberry's isinstance check
    and surface as "Cannot determine type for object of model X" at
    runtime (spec Decision 6, line 351).

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
    model = type_cls.__django_strawberry_definition__.model

    def is_type_of(obj: object, info: object) -> bool:
        return isinstance(obj, (type_cls, model))

    type_cls.is_type_of = is_type_of


def apply_interfaces(type_cls: type, definition: DjangoTypeDefinition) -> None:
    """Inject ``definition.interfaces`` into ``type_cls.__bases__`` (Phase 2.5).

    Skips interfaces already in ``type_cls.__mro__`` so a class that
    already inherits a listed interface directly (e.g. consumer wrote
    ``class Foo(DjangoType, relay.Node): class Meta: interfaces =
    (relay.Node,)``) sees no double-injection (spec lines 329, 339,
    458).

    Raises:
        ConfigurationError: a ``TypeError`` from ``cls.__bases__``
            assignment is wrapped with the offending interface named in
            the message so consumers see "cannot add interface X" rather
            than a raw layout TypeError (spec Risk note, lines 540-541).
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

    Decision 2 (spec lines 287, 455, 555): combining ``relay.Node`` with
    a composite-primary-key model is explicitly out of scope for
    ``0.0.5``. Detection uses ``isinstance(model._meta.pk,
    CompositePrimaryKey)`` so the gate aligns with Django 5.2+'s
    native composite-pk type.
    """
    model = type_cls.__django_strawberry_definition__.model
    if isinstance(model._meta.pk, CompositePrimaryKey):
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
    ``strawberry_django/relay/utils.py:285-303``.
    """
    try:
        return super(cls, cls).resolve_id_attr()  # type: ignore[misc]
    except NodeIDAnnotationError:
        return "pk"


def _resolve_id_default(cls: type, root: models.Model, info: Any) -> str:
    """Default ``Node.resolve_id`` with a ``__dict__`` cache check.

    Calls ``cls.resolve_id_attr()`` to derive the column name (handles
    consumer ``relay.NodeID[...]`` overrides and the ``"pk"`` fallback),
    coerces the literal ``"pk"`` to the model's concrete pk ``attname``
    so the dict-cache lookup keys on the real column, then reads from
    ``root.__dict__`` first (avoids an extra ORM hit when the optimizer
    already loaded the row) and falls back to ``getattr(root, id_attr)``
    (spec line 313 / Decision 7's "no avoidable lazy loads on
    ``resolve_id``").
    """
    id_attr = cls.resolve_id_attr()
    if id_attr == "pk":
        id_attr = root.__class__._meta.pk.attname
    try:
        return str(root.__dict__[id_attr])
    except KeyError:
        return str(getattr(root, id_attr))


def _assemble_node_queryset(
    cls: type,
    info: Any,
    id_attr: str,
    *,
    node_id: Any = None,
    node_ids: list[Any] | None = None,
) -> models.QuerySet:
    """Build the per-node-fetch queryset through the documented steps.

    Steps (mirror ``strawberry_django/relay/utils.py:223-279`` and
    ``:144-170``):

    1. ``cls.__django_strawberry_definition__.model._default_manager.all()``
    2. ``cls.get_queryset(qs, info)``
    3. ``qs.filter(...)`` on ``id_attr`` (single ``node_id``) or
       ``id_attr__in`` (``node_ids``)

    The Relay-node-lookup path is not yet on the optimizer's hot path in
    ``0.0.5``; Decision 7's list-path invariants flow through the existing
    root-gated ``DjangoOptimizerExtension``. A future slice can wire an
    optimizer-extension lookup here without changing the four-step shape.
    """
    model = cls.__django_strawberry_definition__.model
    qs = model._default_manager.all()
    qs = cls.get_queryset(qs, info)
    if node_id is not None:
        coerced = node_id.node_id if isinstance(node_id, relay.GlobalID) else node_id
        qs = qs.filter(**{id_attr: coerced})
    elif node_ids is not None:
        coerced_ids = [(nid.node_id if isinstance(nid, relay.GlobalID) else nid) for nid in node_ids]
        qs = qs.filter(**{f"{id_attr}__in": coerced_ids})
    return qs


def _order_nodes(
    cls: type,
    results: list,
    coerced_keys: list[str],
    id_attr: str,
    *,
    required: bool,
) -> list:
    """Re-order ``results`` to match ``coerced_keys`` (port of strawberry-django's map_results).

    Mirrors ``strawberry_django/relay/utils.py:179-189``: build an index
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
    model = cls.__django_strawberry_definition__.model
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
    info: Any,
    node_id: Any,
    required: bool = False,
) -> Any:
    """Default ``Node.resolve_node`` — ``get_queryset`` aware.

    Returns the single matching row (``qs.get()`` when ``required``,
    ``qs.first()`` otherwise). Async path detected via
    ``strawberry.utils.inspect.in_async_context``; uses ``aget`` /
    ``afirst`` directly (Django 5.2+ is the project's lower bound and
    ships both, per ``pyproject.toml``).
    """
    id_attr = cls.resolve_id_attr()
    qs = _assemble_node_queryset(cls, info, id_attr, node_id=node_id)
    if in_async_context():
        return qs.aget() if required else qs.afirst()
    return qs.get() if required else qs.first()


def _resolve_nodes_default(
    cls: type,
    info: Any,
    node_ids: Any = None,
    required: bool = False,
) -> Any:
    """Default ``Node.resolve_nodes`` — order-preserving, missing-aware.

    When ``node_ids`` is ``None`` returns the full filtered queryset (the
    caller materializes via ``async for`` / iteration as needed; the
    queryset itself is lazy and sync-safe in both contexts). When
    ``node_ids`` is provided, returns a list whose indexes correspond 1:1
    with ``node_ids``: ``required=False`` yields ``None`` for missing
    ids, ``required=True`` raises the model's ``DoesNotExist`` for missing
    ids (homogeneous with ``_resolve_node_default``'s ``qs.get()``).
    """
    id_attr = cls.resolve_id_attr()
    if node_ids is None:
        return _assemble_node_queryset(cls, info, id_attr)
    node_ids_list = list(node_ids)
    coerced_keys = [str(nid.node_id if isinstance(nid, relay.GlobalID) else nid) for nid in node_ids_list]
    qs = _assemble_node_queryset(cls, info, id_attr, node_ids=node_ids_list)
    if in_async_context():

        async def _materialize() -> list:
            results = [obj async for obj in qs]
            return _order_nodes(cls, results, coerced_keys, id_attr, required=required)

        return _materialize()
    return _order_nodes(cls, list(qs), coerced_keys, id_attr, required=required)


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

    Direct port of ``strawberry_django/type.py:213-225``. The ``__func__``
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
