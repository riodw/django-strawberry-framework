"""Relation-field resolvers for ``DjangoType`` relation annotations.

Strawberry's default resolver for an annotated class attribute does
``getattr(source, name)``. For Django relations that returns a
``RelatedManager`` (M2M, reverse FK), which Strawberry rejects with
"Expected Iterable" for list-typed fields. This module attaches a
cardinality-aware resolver per relation field at ``DjangoType``
finalization time so Strawberry's iteration / scalar resolution sees
the right shape.

Forward FK / OneToOne fields would technically work without a custom
resolver (``getattr`` returns the related instance), but they get the
same treatment for consistency and to centralize the prefetch-cache
contract used by the optimizer.

Layered as a sibling of ``types.base`` so the ``DjangoType.__init_subclass__``
pipeline can import ``_attach_relation_resolvers`` without a circular
back-reference (``resolvers.py`` imports nothing from ``base.py``; the
caller pre-computes the field list with
``base._select_fields(model, fields_spec, exclude_spec)`` and passes it in).
"""

from collections.abc import Callable
from typing import Any

import strawberry
from django.db import router
from strawberry.types import Info

from ..exceptions import OptimizerError

# Share the optimizer subpackage's logger so consumers configuring
# "django_strawberry_framework" see N+1 warnings. The optimizer subpackage
# owns the canonical N+1-warning logger; this module re-exports it under a
# "_resolver_logger" alias so the surfacing site reads explicitly as
# "_resolver_logger.warning(...)" rather than as "logger.warning(...)"
# (which would mask the cross-subpackage origin).
from ..optimizer import logger as _resolver_logger
from ..optimizer._context import (
    DST_OPTIMIZER_FK_ID_ELISIONS,
    DST_OPTIMIZER_PLANNED,
    DST_OPTIMIZER_STRICTNESS,
)
from ..optimizer._context import (
    get_context_value as _get_context_value,
)
from ..optimizer.field_meta import FieldMeta
from ..optimizer.plans import resolver_key, runtime_path_from_info
from ..registry import registry
from ..utils.relations import instance_accessor, is_many_side_relation_kind

# Module-level immutable sentinel for the "no elisions registered" branch so
# the forward-resolver dispatch does not allocate a fresh empty set per call.
_EMPTY_ELISIONS: frozenset[str] = frozenset()

# Sentinel distinguishing "caller did not read the PLAN sentinel" from a real
# ``planned is None``. ``forward_resolver`` reads the plan once and threads it
# (plus the resolver key) into ``_check_n1`` so the runtime-path walk is not
# repeated when both the FK-id-elision and N+1 checks need it (feedback L3).
_PLAN_UNREAD: Any = object()

# Sentinel returned by ``_build_fk_id_stub`` when the FK ``attname`` is deferred
# on ``root`` (spec-035 Decision 5). FK-id elision reads the FK column off the
# parent row; G2 guarantees the row loads for OPTIMIZER-owned projections, but a
# consumer-returned ``.only(...)`` survives B8 consumer-wins diffing and can
# defer the FK column while the plan still carries the elision. Reading the
# deferred column here would silently lazy-load per row - and because the
# relation is recorded as planned, strictness would never see it. The stub
# signals "elision unsafe" instead of reading the column; ``forward_resolver``
# treats the sentinel as not-elided and falls through to the normal
# related-object resolve so ``_check_n1`` (strictness) sees the access.
_FK_ELISION_UNSAFE: Any = object()


def _fk_attname_is_deferred(root: Any, attname: str) -> bool:
    """Return ``True`` when reading ``root.<attname>`` would trigger a deferred fetch.

    The FK column lives in ``root.__dict__`` on a fully-loaded instance and is
    absent on a deferred one (the ``DeferredAttribute`` descriptor lazy-loads on
    access) - the same loaded signal ``_will_lazy_load_single`` uses, applied to
    the FK *column* attname rather than the relation field name. Absence from
    ``__dict__`` alone is not enough: the resolver's "compatibility for test
    doubles" contract treats a class-attribute-backed value (a plain test
    double, no DB) as loaded, so deferral is confirmed only when ``root`` is a
    real Django instance whose ``get_deferred_fields()`` lists the column. A
    double can simulate the deferred case by exposing a ``get_deferred_fields``
    that returns the attname while keeping it out of ``__dict__``.
    """
    if attname in getattr(root, "__dict__", {}):
        return False
    get_deferred_fields = getattr(root, "get_deferred_fields", None)
    if get_deferred_fields is None:
        return False
    return attname in get_deferred_fields()


def _build_fk_id_stub(root: Any, field_meta: FieldMeta) -> Any:
    """Build a target-model stub from ``root.<attname>`` for B2 id-only selections.

    Returns ``_FK_ELISION_UNSAFE`` when ``field_meta.attname`` is deferred on
    ``root`` (spec-035 Decision 5 - a consumer ``.only(...)`` that dropped the FK
    column survives B8 consumer-wins diffing while the plan still carries the
    elision). In that case the column is NOT read (which would be the silent
    per-row lazy load Decision 5 forbids); the caller falls back loudly so
    strictness sees the access. A fully-loaded column (the
    optimizer-owned-projection norm and the consumer-``.only()``-that-includes-
    the-FK case) builds the stub as before.
    """
    if field_meta.attname is None or field_meta.related_model is None:
        return None
    if _fk_attname_is_deferred(root, field_meta.attname):
        return _FK_ELISION_UNSAFE
    related_id = getattr(root, field_meta.attname)
    if related_id is None:
        return None
    stub = field_meta.related_model(pk=related_id)
    state = getattr(stub, "_state", None)
    if state is not None:
        state.adding = False
        instance = root if hasattr(root, "_state") else None
        state.db = router.db_for_read(field_meta.related_model, instance=instance)
    return stub


def _will_lazy_load_single(root: Any, field_name: str) -> bool:
    """Return ``True`` if a single-valued relation access would trigger a query.

    Forward FK, forward OneToOne, and reverse OneToOne. Django's
    descriptor populates ``root._state.fields_cache`` after a load and
    also stamps ``root.__dict__`` on some access paths (e.g. when the
    related instance has been assigned). Both paths count as cached.
    Synthetic test doubles that pre-populate ``__dict__`` are therefore
    treated as already loaded - matching the resolver's existing
    "compatibility for test doubles" contract.
    """
    if field_name in getattr(root, "__dict__", {}):
        return False
    state = getattr(root, "_state", None)
    fields_cache = getattr(state, "fields_cache", {})
    return field_name not in fields_cache


def _will_lazy_load_many(root: Any, field_name: str) -> bool:
    """Return ``True`` if a many-side relation access would trigger a query.

    Reverse FK and M2M. The only Django-supported cache for the many
    side is ``root._prefetched_objects_cache``; setting
    ``root.<field_name>`` directly does not populate any cache and
    accessing the descriptor still hits the database. The
    ``__dict__`` short-circuit used for single-valued relations is
    intentionally NOT applied here - it would silently exempt the
    many-side strictness path from the optimizer's N+1 contract.
    """
    prefetch_cache = getattr(root, "_prefetched_objects_cache", {})
    return field_name not in prefetch_cache


def _check_n1(
    info: Any,
    root: Any,
    field_name: str,
    parent_type: type | None = None,
    *,
    kind: str | None,
    accessor_name: str | None = None,
    to_attr: str | None = None,
    reason: str | None = None,
    planned: Any = _PLAN_UNREAD,
    precomputed_key: str | None = None,
    force_unplanned: bool = False,
) -> None:
    """B3: warn or raise if the relation is not planned and would lazy-load.

    ``kind`` is required (keyword-only) and accepts the ``relation_kind``
    of the field being resolved. ``"many"`` and ``"reverse_many_to_one"``
    use the many-side cache check; the special ``"connection_to_attr"``
    value (spec-033 Decision 8) uses the windowed-prefetch ``to_attr``
    probe; every other known relation shape uses the single-valued cache
    check. Production ``_make_relation_resolver`` always supplies the
    relation kind; the ``kind=None`` fallback is reserved for test-double
    direct callers that exercise the single-valued cache check (see
    ``tests/types/test_resolvers.py::test_check_n1_*``).

    ``field_name`` keys the PLAN lookup (the optimizer walker emits
    resolver keys in field-name vocabulary); ``accessor_name`` keys the
    instance CACHE probes - Django's prefetch/fields caches store under
    the accessor, which diverges from ``field.name`` for reverse
    relations without ``related_name`` (Round-4 S3 follow-up). Production
    callers always supply it; ``None`` falls back to ``field_name`` for
    test-double direct callers.

    Connection contract (spec-033 Decision 8): the synthesized
    relation-connection resolver calls this with ``kind="connection_to_attr"``
    and the windowed-prefetch ``to_attr`` (``_dst_<field>_connection``).
    The access truly queries iff that ``to_attr`` is ABSENT on ``root`` -
    when present, Slice 1's window already served the page, so no lazy load
    happens and the check is silent. ``reason`` (the per-parent-fallback
    cause, supplied by the connection call site) is appended to the
    ``"raise"`` / ``"warn"`` message when present so a flagged fallback
    reads as actionable rather than as an optimizer defect; the
    list-relation calls pass no ``reason`` and produce the byte-identical
    pre-slice message.

    ``planned`` / ``precomputed_key`` (keyword-only, feedback L3): a caller that
    already read the ``DST_OPTIMIZER_PLANNED`` sentinel and computed the resolver
    key (``forward_resolver``) threads both so this function neither re-reads the
    sentinel nor re-walks ``info.path``. Omitting them (every other call site)
    keeps the original read-and-compute behavior.

    ``force_unplanned`` (keyword-only, spec-035 Decision 5): when ``True`` the
    ``key in planned`` short-circuit is bypassed so the lazy-load probe runs even
    for a relation the plan recorded as planned. ``forward_resolver`` sets it when
    FK-id elision turned out unsafe (the consumer ``.only(...)`` deferred the FK
    column): the relation IS in ``planned`` because the elision branch recorded
    it, but the access will genuinely lazy-load, so strictness must see it rather
    than mistake the planned key for a satisfied relation. The loaded common path
    never reaches this call with the flag set, so it stays a no-op there.
    """
    context = getattr(info, "context", None)
    # ``forward_resolver`` may have already read the PLAN sentinel and computed
    # the resolver key; reuse them when threaded so the ``info.path`` walk runs
    # once per row, not once per consumer (feedback L3). Other call sites omit
    # both and get the original read-and-compute behavior.
    if planned is _PLAN_UNREAD:
        planned = _get_context_value(context, DST_OPTIMIZER_PLANNED)
    if planned is None:
        return
    key = (
        precomputed_key
        if precomputed_key is not None
        else resolver_key(parent_type, field_name, runtime_path_from_info(info))
    )
    if key in planned and not force_unplanned:
        return
    if kind == "connection_to_attr":
        # The windowed page already landed under ``to_attr`` when present;
        # only an absent ``to_attr`` means the per-parent pipeline will query.
        lazy = getattr(root, to_attr, None) is None
    else:
        probe_name = accessor_name or field_name
        if is_many_side_relation_kind(kind):
            lazy = _will_lazy_load_many(root, probe_name)
        else:
            lazy = _will_lazy_load_single(root, probe_name)
    if not lazy:
        return
    strictness = _get_context_value(context, DST_OPTIMIZER_STRICTNESS, "off")
    suffix = f" ({reason})" if reason is not None else ""
    if strictness == "raise":
        raise OptimizerError(f"Unplanned N+1: {field_name}{suffix}")
    if strictness == "warn":
        _resolver_logger.warning("Potential N+1 on %s%s", field_name, suffix)


def _name_resolver(resolver: Callable[..., Any], field_name: str) -> Callable[..., Any]:
    """Stamp ``resolver.__name__`` to ``resolve_<field_name>``.

    Keeps GraphiQL traces readable and centralises the three
    cardinality-branch rename calls in ``_make_relation_resolver``.
    Assumes ``resolver`` is a Python-function callable with a writeable
    ``__name__`` attribute (all production call sites pass a module-local
    ``def`` closure).
    """
    resolver.__name__ = f"resolve_{field_name}"
    return resolver


def _field_meta_for_resolver(field: Any, parent_type: type | None) -> FieldMeta:
    """Return registered ``FieldMeta`` for ``field`` when the parent type exposes it.

    Production callers MUST pass ``parent_type=cls`` so the branch-sensitive
    resolver key matches what the optimizer walker emitted; the ``None`` default
    ONLY supports test-double direct callers exercising the single-valued /
    many-side code paths without a registered ``DjangoType``.
    """
    if parent_type is not None:
        definition = registry.get_definition(parent_type)
        if definition is not None:
            meta = definition.field_map.get(field.name)
            if meta is not None:
                return meta
    if not hasattr(field, "is_relation"):
        # Test-double fallback. The canonical builder
        # ``FieldMeta.from_django_field`` requires ``field.is_relation``;
        # test doubles like ``SimpleNamespace(name=..., many_to_many=...)``
        # lack it. Delegating to the shared shape helper keeps the
        # observable ``FieldMeta`` identical to what the canonical
        # builder would produce on the same descriptor, with
        # ``is_relation=True`` hard-coded because the caller is by
        # definition asking about a relation field.
        return FieldMeta._from_field_shape(field, is_relation=True)
    return FieldMeta.from_django_field(field)


def _make_relation_resolver(field: Any, parent_type: type | None = None) -> Any:
    """Generate a resolver for a Django relation field.

    Production callers MUST pass ``parent_type=cls`` so the branch-sensitive
    resolver key matches what the optimizer walker emitted; the ``None`` default
    ONLY supports test-double direct callers exercising the single-valued /
    many-side code paths without a registered ``DjangoType``.

    Cardinality-specific shapes:

    - Many-side (M2M, reverse FK): ``list(getattr(root, name).all())``.
      ``manager.all()`` is prefetch-aware (returns the cached list when
      the optimizer has prefetched) so the same shape works on or off
      the optimizer. ``list(...)`` materializes the queryset to a Python
      list, matching strawberry-graphql-django's ``get_result`` shape.
    - Reverse OneToOne (``one_to_one`` and ``auto_created``):
      ``getattr(root, name)`` wrapped in ``try/except DoesNotExist`` so
      the resolver returns ``None`` when the reverse row is absent.
    - Forward FK / forward OneToOne: ``getattr(root, name)`` - returns
      the related instance, or ``None`` if the FK is nullable and unset.

    B3: all resolvers now accept ``info`` (Strawberry injects it
    automatically) and call ``_check_n1`` when a strictness sentinel
    is present on ``info.context``. ``_check_n1`` receives a
    ``FieldMeta``-derived relation-kind key so the many-side dispatch uses
    ``_prefetched_objects_cache`` exclusively and does not mis-classify
    a consumer-assigned attribute as "already loaded".
    """
    field_name = field.name
    # Instance reads go through the accessor; ``field_name`` stays the
    # GraphQL-surface / optimizer-key vocabulary. They diverge for reverse
    # relations without ``related_name`` (Round-4 review S3).
    accessor_name = instance_accessor(field)
    field_meta = _field_meta_for_resolver(field, parent_type)
    kind = field_meta.relation_kind

    if field_meta.is_many_side:

        def many_resolver(root: Any, info: Info) -> Any:
            _check_n1(info, root, field_name, parent_type, kind=kind, accessor_name=accessor_name)
            # Prefetched path (the optimized norm): Django stores the rows under
            # ``_prefetched_objects_cache[accessor_name]`` - the same key the N+1
            # probe above uses. Read it directly and return Django's materialized
            # list, skipping the ``manager.all()`` QuerySet clone and the
            # ``list(...)`` copy this otherwise pays per parent row (feedback H1).
            # Same rows, same order. Any miss falls through to the manager path.
            prefetched = getattr(root, "_prefetched_objects_cache", None)
            if prefetched is not None:
                cached = prefetched.get(accessor_name)
                if cached is not None:
                    result_cache = getattr(cached, "_result_cache", None)
                    return result_cache if result_cache is not None else cached
            return list(getattr(root, accessor_name).all())

        return _name_resolver(many_resolver, field_name)

    if field_meta.one_to_one and field_meta.auto_created:
        related_does_not_exist = field_meta.related_model.DoesNotExist

        def reverse_one_to_one_resolver(root: Any, info: Info) -> Any:
            _check_n1(info, root, field_name, parent_type, kind=kind, accessor_name=accessor_name)
            try:
                return getattr(root, accessor_name)
            except related_does_not_exist:
                return None

        return _name_resolver(reverse_one_to_one_resolver, field_name)

    def forward_resolver(root: Any, info: Info) -> Any:
        context = getattr(info, "context", None)
        # FK-id elision (spec-011 Decision 7) and the N+1 probe both key off the
        # resolver key, which requires an ``info.path`` walk. Read both sentinels
        # first; when neither is active - the common request shape - skip the walk
        # entirely. When at least one is active, walk once and share the key
        # across both checks (feedback L3).
        elisions = (
            _get_context_value(context, DST_OPTIMIZER_FK_ID_ELISIONS, _EMPTY_ELISIONS)
            if field_meta.attname is not None
            else _EMPTY_ELISIONS
        )
        planned = _get_context_value(context, DST_OPTIMIZER_PLANNED)
        if not elisions and planned is None:
            return getattr(root, field_name)
        key = resolver_key(parent_type, field_name, runtime_path_from_info(info))
        elision_unsafe = False
        if elisions and key in elisions:
            # spec-035 Decision 5: ``_build_fk_id_stub`` returns
            # ``_FK_ELISION_UNSAFE`` when the FK column is deferred (a consumer
            # ``.only(...)`` that dropped it). Treat that as not-elided and fall
            # through to the normal resolve so ``_check_n1`` (strictness) sees
            # the access instead of a silent per-row lazy load.
            stub = _build_fk_id_stub(root, field_meta)
            if stub is not _FK_ELISION_UNSAFE:
                return stub
            # The relation is in ``planned`` (the elision branch recorded it), so
            # ``_check_n1`` would short-circuit on the planned key and stay silent.
            # Force the lazy-load probe so the fallback is strictness-visible
            # rather than a silent planned-relation lazy load (Decision 5).
            elision_unsafe = True
        _check_n1(
            info,
            root,
            field_name,
            parent_type,
            kind=kind,
            accessor_name=accessor_name,
            planned=planned,
            precomputed_key=key,
            force_unplanned=elision_unsafe,
        )
        return getattr(root, field_name)

    return _name_resolver(forward_resolver, field_name)


def _attach_relation_resolvers(
    cls: type,
    fields: tuple[Any, ...],
    *,
    skip_field_names: frozenset[str] = frozenset(),
) -> None:
    """Attach a resolver per relation in the pre-selected ``fields`` list.

    ``finalize_django_types()`` passes ``DjangoTypeDefinition.selected_fields``
    here after pending relation annotations are resolved. ``skip_field_names``
    contains consumer-assigned relation fields such as
    ``strawberry.field(resolver=...)`` / ``@strawberry.field`` overrides, which
    must not be clobbered by generated resolvers.
    """
    for field in fields:
        if not field.is_relation:
            continue
        if field.name in skip_field_names:
            continue
        resolver = _make_relation_resolver(field, parent_type=cls)
        setattr(cls, field.name, strawberry.field(resolver=resolver))
