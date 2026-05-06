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
caller pre-computes the field list with ``base._select_fields(meta)`` and
passes it in).
"""

from typing import Any

import strawberry
from django.db import router
from strawberry.types import Info

from ..optimizer import logger as _resolver_logger
from ..optimizer._context import (
    DST_OPTIMIZER_FK_ID_ELISIONS,
    DST_OPTIMIZER_PLANNED,
    DST_OPTIMIZER_STRICTNESS,
)
from ..optimizer._context import (
    get_context_value as _get_context_value,
)
from ..optimizer.plans import resolver_key, runtime_path_from_info
from ..utils.relations import relation_kind


def _is_fk_id_elided(info: Any, field_name: str, parent_type: type | None = None) -> bool:
    """Return ``True`` if B2 marked this forward relation as FK-id elided."""
    elisions = _get_context_value(
        getattr(info, "context", None),
        DST_OPTIMIZER_FK_ID_ELISIONS,
        set(),
    )
    key = resolver_key(parent_type, field_name, runtime_path_from_info(info))
    return key in elisions


def _build_fk_id_stub(root: Any, field: Any) -> Any:
    """Build a target-model stub from ``root.<attname>`` for B2 id-only selections."""
    related_id = getattr(root, field.attname)
    if related_id is None:
        return None
    stub = field.related_model(pk=related_id)
    state = getattr(stub, "_state", None)
    if state is not None:
        state.adding = False
        instance = root if hasattr(root, "_state") else None
        state.db = router.db_for_read(field.related_model, instance=instance)
    return stub


def _will_lazy_load(root: Any, field_name: str) -> bool:
    """Return ``True`` if accessing ``field_name`` on ``root`` would trigger a query.

    Checks Django's caching mechanisms:
    - Forward FK / OneToOne: cached if ``field_name`` is in ``root.__dict__``
      (Django stores the loaded related object there after the first access
      or after ``select_related``).
    - Many-side (reverse FK, M2M): cached if ``field_name`` is in
      ``root._prefetched_objects_cache`` (populated by ``prefetch_related``).
    """
    # Forward FK / OneToOne: Django caches the related instance in __dict__.
    if field_name in getattr(root, "__dict__", {}):
        return False
    # Many-side: Django caches prefetched querysets in _prefetched_objects_cache.
    prefetch_cache = getattr(root, "_prefetched_objects_cache", {})
    return field_name not in prefetch_cache


def _check_n1(
    info: Any,
    root: Any,
    field_name: str,
    parent_type: type | None = None,
) -> None:
    """B3: warn or raise if the relation is not planned and would lazy-load."""
    from ..exceptions import OptimizerError

    context = getattr(info, "context", None)
    planned = _get_context_value(context, DST_OPTIMIZER_PLANNED)
    if planned is None:
        return
    key = resolver_key(parent_type, field_name, runtime_path_from_info(info))
    if key in planned:
        return
    # Only warn/raise if the access would actually trigger a lazy load.
    if not _will_lazy_load(root, field_name):
        return
    strictness = _get_context_value(context, DST_OPTIMIZER_STRICTNESS, "off")
    if strictness == "raise":
        raise OptimizerError(f"Unplanned N+1: {field_name}")
    if strictness == "warn":
        _resolver_logger.warning("Potential N+1 on %s", field_name)


def _make_relation_resolver(field: Any, parent_type: type | None = None) -> Any:
    """Generate a resolver for a Django relation field.

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
    is present on ``info.context``.
    """
    field_name = field.name
    kind = relation_kind(field)

    if kind == "many":

        def many_resolver(root: Any, info: Info) -> Any:
            _check_n1(info, root, field_name, parent_type)
            return list(getattr(root, field_name).all())

        many_resolver.__name__ = f"resolve_{field_name}"
        return many_resolver

    if kind == "reverse_one_to_one":
        related_does_not_exist = field.related_model.DoesNotExist

        def reverse_one_to_one_resolver(root: Any, info: Info) -> Any:
            _check_n1(info, root, field_name, parent_type)
            try:
                return getattr(root, field_name)
            except related_does_not_exist:
                return None

        reverse_one_to_one_resolver.__name__ = f"resolve_{field_name}"
        return reverse_one_to_one_resolver

    attname = getattr(field, "attname", None)

    def forward_resolver(root: Any, info: Info) -> Any:
        if attname is not None and _is_fk_id_elided(info, field_name, parent_type):
            return _build_fk_id_stub(root, field)
        _check_n1(info, root, field_name, parent_type)
        return getattr(root, field_name)

    forward_resolver.__name__ = f"resolve_{field_name}"
    return forward_resolver


def _attach_relation_resolvers(cls: type, fields: list[Any]) -> None:
    """Attach a resolver per relation in the pre-selected ``fields`` list.

    The caller (``DjangoType.__init_subclass__``) computes
    ``base._select_fields(meta)`` once and passes the result here so the
    field walk is not duplicated between annotation building and resolver
    attachment, and so this module avoids importing from ``types.base``
    (which would create a circular dependency).
    """
    for field in fields:
        if not field.is_relation:
            continue
        resolver = _make_relation_resolver(field, parent_type=cls)
        setattr(cls, field.name, strawberry.field(resolver=resolver))
