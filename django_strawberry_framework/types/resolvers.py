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
# "django_strawberry_framework" see N+1 warnings.
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
from ..utils.relations import is_many_side_relation_kind, relation_kind

# Module-level immutable sentinel for the "no elisions registered" branch so
# the forward-resolver dispatch does not allocate a fresh empty set per call.
_EMPTY_ELISIONS: frozenset[str] = frozenset()


def _is_fk_id_elided(info: Any, field_name: str, parent_type: type | None = None) -> bool:
    """Return ``True`` if B2 marked this forward relation as FK-id elided.

    Relay ``GlobalID`` handling is intentionally kept out of this path —
    Relay id resolution lives in ``types/relay.py`` (``_resolve_id_default``
    and friends). Forward-relation FK-id elision continues to see only the
    Django primary-key column it always saw (spec Decision 7, line 357).
    """
    elisions = _get_context_value(
        getattr(info, "context", None),
        DST_OPTIMIZER_FK_ID_ELISIONS,
        _EMPTY_ELISIONS,
    )
    key = resolver_key(parent_type, field_name, runtime_path_from_info(info))
    return key in elisions


def _build_fk_id_stub(root: Any, field_meta: FieldMeta) -> Any:
    """Build a target-model stub from ``root.<attname>`` for B2 id-only selections."""
    if field_meta.attname is None or field_meta.related_model is None:
        return None
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
    treated as already loaded — matching the resolver's existing
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
    intentionally NOT applied here — it would silently exempt the
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
) -> None:
    """B3: warn or raise if the relation is not planned and would lazy-load.

    ``kind`` is required (keyword-only) and accepts the ``relation_kind``
    of the field being resolved. ``"many"`` and ``"reverse_many_to_one"``
    use the many-side cache check; every other known relation shape uses
    the single-valued cache check. Pass ``kind=None`` only when you
    explicitly want the legacy single-valued check — the absence of
    ``kind`` in a new caller is a programming error, since production
    ``_make_relation_resolver`` always supplies the relation kind.
    """
    context = getattr(info, "context", None)
    planned = _get_context_value(context, DST_OPTIMIZER_PLANNED)
    if planned is None:
        return
    key = resolver_key(parent_type, field_name, runtime_path_from_info(info))
    if key in planned:
        return
    if is_many_side_relation_kind(kind):
        lazy = _will_lazy_load_many(root, field_name)
    else:
        lazy = _will_lazy_load_single(root, field_name)
    if not lazy:
        return
    strictness = _get_context_value(context, DST_OPTIMIZER_STRICTNESS, "off")
    if strictness == "raise":
        raise OptimizerError(f"Unplanned N+1: {field_name}")
    if strictness == "warn":
        _resolver_logger.warning("Potential N+1 on %s", field_name)


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

    The ``None`` default exists for test-double direct calls; production calls always
    supply ``parent_type=cls``.
    """
    if parent_type is not None:
        definition = registry.get_definition(parent_type)
        if definition is not None:
            meta = definition.field_map.get(field.name)
            if meta is not None:
                return meta
    if not hasattr(field, "is_relation"):
        # Mirror the cardinality-gated nullable rule + target-column reads
        # from ``FieldMeta.from_django_field`` (optimizer/field_meta.py:135-170)
        # so the test-double fallback advertises the same shape the canonical
        # builder would. Many-side cardinalities short-circuit to
        # ``nullable=False`` (manager/queryset is never ``None``); reverse
        # OneToOne short-circuits to ``True``; every other single-relation
        # shape follows ``field.null`` via ``getattr`` default ``False``.
        is_m2m = bool(getattr(field, "many_to_many", False))
        is_o2m = bool(getattr(field, "one_to_many", False))
        target_field = getattr(field, "target_field", None)
        if is_m2m or is_o2m:
            nullable = False
        else:
            nullable = relation_kind(field) == "reverse_one_to_one" or bool(getattr(field, "null", False))
        return FieldMeta(
            name=field.name,
            is_relation=True,
            many_to_many=is_m2m,
            one_to_many=is_o2m,
            one_to_one=bool(getattr(field, "one_to_one", False)),
            nullable=nullable,
            related_model=getattr(field, "related_model", None),
            attname=getattr(field, "attname", None),
            target_field_name=getattr(target_field, "name", None),
            target_field_attname=getattr(target_field, "attname", None),
            reverse_connector_attname=getattr(getattr(field, "field", None), "attname", None),
            auto_created=bool(getattr(field, "auto_created", False)),
        )
    return FieldMeta.from_django_field(field)


def _make_relation_resolver(field: Any, parent_type: type | None = None) -> Any:
    """Generate a resolver for a Django relation field.

    The ``None`` default exists for test-double direct calls; production calls always
    supply ``parent_type=cls``.

    Cardinality-specific shapes:

    - Many-side (M2M, reverse FK): ``list(getattr(root, name).all())``.
      ``manager.all()`` is prefetch-aware (returns the cached list when
      the optimizer has prefetched) so the same shape works on or off
      the optimizer. ``list(...)`` materializes the queryset to a Python
      list, matching strawberry-graphql-django's ``get_result`` shape.
    - Reverse OneToOne (``one_to_one`` and ``auto_created``):
      ``getattr(root, name)`` wrapped in ``try/except DoesNotExist`` so
      the resolver returns ``None`` when the reverse row is absent.
    - Forward FK / forward OneToOne: ``getattr(root, name)`` — returns
      the related instance, or ``None`` if the FK is nullable and unset.

    B3: all resolvers now accept ``info`` (Strawberry injects it
    automatically) and call ``_check_n1`` when a strictness sentinel
    is present on ``info.context``. ``_check_n1`` receives a
    ``FieldMeta``-derived relation-kind key so the many-side dispatch uses
    ``_prefetched_objects_cache`` exclusively and does not mis-classify
    a consumer-assigned attribute as "already loaded".
    """
    field_name = field.name
    field_meta = _field_meta_for_resolver(field, parent_type)
    kind = field_meta.relation_kind

    if field_meta.is_many_side:

        def many_resolver(root: Any, info: Info) -> Any:
            _check_n1(info, root, field_name, parent_type, kind=kind)
            return list(getattr(root, field_name).all())

        return _name_resolver(many_resolver, field_name)

    if field_meta.one_to_one and field_meta.auto_created:
        related_does_not_exist = field_meta.related_model.DoesNotExist

        def reverse_one_to_one_resolver(root: Any, info: Info) -> Any:
            _check_n1(info, root, field_name, parent_type, kind=kind)
            try:
                return getattr(root, field_name)
            except related_does_not_exist:
                return None

        return _name_resolver(reverse_one_to_one_resolver, field_name)

    def forward_resolver(root: Any, info: Info) -> Any:
        if field_meta.attname is not None and _is_fk_id_elided(info, field_name, parent_type):
            return _build_fk_id_stub(root, field_meta)
        _check_n1(info, root, field_name, parent_type, kind=kind)
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
