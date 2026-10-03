"""Parent/child join-condition taxonomy for nested-connection fetch planning.

The shared vocabulary for HOW a child row joins back to its parent, classified
once per relation field instead of re-derived from ``relation_kind`` string
checks at each consumer. Modeled on graph-node's join-condition taxonomy (its
RFC-0001 "types A-D": derived vs stored x scalar vs list), translated to the
four Django relation shapes the package plans:

======================  =====================  ==========================
Django relation          graph-node analog      join shape
======================  =====================  ==========================
reverse ``ForeignKey``   B (child stores one    ``DIRECT_FK`` - the child
(``reverse_many_to_one``) parent id)            table carries the parent id
reverse ``OneToOne``     B, scalar cardinality  ``DIRECT_FK``
forward ``M2M`` /        A (child derives a     ``THROUGH_TABLE`` - the
reverse ``M2M``          parent-id list)        join table owns the attach
forward FK / O2O         D (parent stores the   ``UNSUPPORTED`` - single-
(``forward_single``)     child id)              valued; nothing to window
``GenericRelation``      B (child stores a      ``DIRECT_FK`` - the child
(``generic``)            parent id + a morph    ``object_id`` column carries
                         content type)          the parent id; the content
                                                type is a constant WHERE, and
                                                ``parent_link_field`` stays
                                                ``None`` so lateral degrades
                                                to the windowed body
======================  =====================  ==========================

One classification (``classify_relation_join``) carries every join-derived
fact the fetch strategies need:

- ``windowable`` + ``partition_expr`` - the windowed-prefetch strategy's
  ``PARTITION BY`` input.
- ``parent_join_columns`` - the child-side columns Django needs loaded to
  attach prefetched rows to parents.
- ``through_model`` + ``lateral_shape`` - the Postgres LATERAL strategy's
  join-SQL selector (``optimizer/lateral_fetch.py``: a ``DIRECT_FK`` shape
  correlates the child table directly; a ``THROUGH_TABLE`` shape joins the
  M2M through table inside the lateral subquery; ``UNSUPPORTED`` never
  plans).

A ``DIRECT_FK`` link's columns come from one reader,
``utils/relations.py::relation_link``: a relation's ``attname`` is its carrier
column only for a ``ForeignKey``, never for a plain ``ForeignObject``, so the
partition, the attach columns and the correlated-fetch link field all derive
from the link's carrier fields instead, and a forward relation's attach
columns from the link's target fields (never Django's single-target
``target_field``, which a multi-column ``ForeignObject`` does not have).

The planner classifies the RAW Django relation field (or rel descriptor): the
forward-M2M reverse query name lives only on ``field.remote_field``. A
``FieldMeta`` classifies too (the projection writers hand one in), reading its
precomputed ``link_carrier_attnames`` / ``link_target_attnames`` slots; it
carries no link field, so its ``parent_link_field`` stays ``None``.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from ..utils.relations import (
    RelationKind,
    is_single_column_foreign_key,
    m2m_through_link_fields,
    m2m_through_model,
    relation_attr,
    relation_bool,
    relation_kind,
    relation_link,
    safe_truthy,
)

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from django.db import models

    from ..utils.typing import ForeignKeyField, ModelField
    from .field_meta import FieldMeta


class LateralJoinShape(enum.Enum):
    """How a lateral (or correlated) child subquery would join to one parent."""

    DIRECT_FK = "direct_fk"
    THROUGH_TABLE = "through_table"
    UNSUPPORTED = "unsupported"


# The relation kinds a windowed prefetch can partition: every many-valued
# shape plus the reverse one-to-one (whose child row also carries the parent
# id). Single-valued FORWARD relations have no windowable parent partition.
WINDOWABLE_RELATION_KINDS: frozenset[RelationKind] = frozenset(
    {
        "many",
        "reverse_many_to_one",
        "reverse_one_to_one",
        "generic",
    },
)


# This module's never-raises contract is a stated MODE of the shared
# relation readers rather than a parallel family beside them: one read body,
# one truth test, two failure policies. The local names stay so the call
# sites below read as taxonomy code, and so the lenient policy is declared once
# here instead of at each of them.
def _safe_getattr(value: object, name: str, default: object = None) -> object:
    """Read a descriptor attribute without letting malformed doubles escape."""
    return relation_attr(value, name, default, lenient=True)


_safe_truthy = safe_truthy


def _safe_flag(value: object, name: str) -> bool:
    """Read a boolean relation flag, guarding both the read and its truth test."""
    return relation_bool(value, name, False, lenient=True)


def _first_truthy(*values: object) -> object:
    """The first value that tests true, a raising truth test counting as false."""
    for value in values:
        if _safe_truthy(value):
            return value
    return None


@dataclass(frozen=True)
class RelationJoinDescriptor:
    """Everything join-shaped one relation field implies for fetch planning.

    ``partition_expr`` is the parent-side partition the windowed strategy
    hands to ``PARTITION BY`` (``None`` when not ``windowable``);
    ``parent_join_columns`` are the child-side connector columns the prefetch
    attach reads (one per link carrier; ``()`` when none resolves - the caller
    logs and degrades); ``through_model`` is the M2M join table when
    ``lateral_shape`` is ``THROUGH_TABLE``.

    ``parent_link_field`` / ``through_child_field`` are the resolved LINK
    FIELD OBJECTS a correlated fetch joins on (the lateral backend today;
    any future strategy or the polymorphic work reads the same resolved
    facts instead of re-walking ``remote_field`` / ``m2m_field_name``):
    for ``DIRECT_FK`` the child-side FK whose column carries the parent id
    (``through_child_field`` is ``None``), set only when that link passes
    ``utils/relations.py::is_single_column_foreign_key`` (a ``ForeignObject``
    link of any width has no single ``column`` / ``db_type`` to join or cast on,
    so the correlated strategies refuse it and the windowed body serves it); for
    ``THROUGH_TABLE`` the through table's parent-side FK and child-side FK
    respectively; ``None`` when the shape is ``UNSUPPORTED`` or the field cannot
    resolve them (synthetic doubles - the classifier never raises).

    ``content_type_column`` is the child ``content_type_id`` attname a
    ``GenericRelation`` needs alongside the ``object_id`` connector: Django's
    prefetch attach key is ``(object_id, content_type_id)``, and the composite-
    index advisory recommends ``(content_type_id, object_id, ...)`` because
    every generic query also carries a constant morph WHERE. ``None`` for every
    non-generic shape and for a synthetic generic double that cannot resolve
    it - the classifier never raises.

    ``prefetch_attach_columns`` is the derived attach-complete set projection
    writers must ``.only()`` (every connector, plus morph when present) so
    attach never deferred-refetches any part of the key.
    """

    kind: RelationKind
    windowable: bool
    partition_expr: str | None
    parent_join_columns: tuple[str, ...]
    through_model: type[models.Model] | None
    lateral_shape: LateralJoinShape
    parent_link_field: ForeignKeyField | None = None
    through_child_field: ForeignKeyField | None = None
    content_type_column: str | None = None

    @property
    def prefetch_attach_columns(self) -> tuple[str, ...]:
        """Child columns Django's prefetch attach reads on each related row.

        Every ``parent_join_columns`` entry (a multi-column ``ForeignObject``
        attaches on all of its carriers); for a ``GenericRelation`` also
        ``content_type_column`` - ``GenericRelatedObjectManager.
        get_prefetch_querysets`` builds ``rel_obj_attr`` as
        ``(object_id, content_type_id)``. Empty when neither resolves (callers
        log and degrade). Order matches the attach key, not the index-advisory
        equality prefix (morph-first there).
        """
        if self.content_type_column is None:
            return self.parent_join_columns
        return (*self.parent_join_columns, self.content_type_column)


def _partition_expr(field: object) -> str | None:
    """The parent-side partition expression Django's M2M prefetch attach uses.

    ``remote_field.attname or remote_field.name`` - exactly what upstream's
    ``_optimize_prefetch_queryset`` partitions by (spec-033 Decision 4): the
    child's forward M2M field name for a reverse M2M (``"genres"``), and the
    target's reverse query name for a forward M2M (``"books"`` - NOT the
    accessor when ``related_name`` is absent).
    """
    remote_field = _safe_getattr(field, "remote_field")
    # A relation's ``attname`` / ``name`` slots hold strings.
    return cast(
        "str | None",
        _first_truthy(
            _safe_getattr(remote_field, "attname"),
            _safe_getattr(remote_field, "name"),
        ),
    )


def _precomputed_attnames(field: object, slot: str) -> tuple[str, ...]:
    """A ``FieldMeta`` link slot stamped from ``relation_link``; ``()`` if absent or malformed."""
    precomputed = _safe_getattr(field, slot)
    if isinstance(precomputed, tuple) and all(
        isinstance(attname, str) for attname in cast("tuple[object, ...]", precomputed)
    ):
        return cast("tuple[str, ...]", precomputed)
    return ()


def _carrier_attnames(field: object) -> tuple[str, ...]:
    """The child columns carrying the parent key of a reverse FK / reverse O2O link.

    A raw rel descriptor answers through ``utils/relations.py::relation_link``
    (``("shelf_id",)`` for a reverse ``ForeignKey``, one entry per
    ``from_fields`` member for a reverse ``ForeignObject``); a ``FieldMeta``
    answers from its ``link_carrier_attnames`` slot, which its builder fills
    from the same reader. ``()`` when neither resolves.
    """
    carriers = relation_link(field, lenient=True).carrier_attnames
    if carriers:
        return carriers
    return _precomputed_attnames(field, "link_carrier_attnames")


def _forward_join_columns(field: object) -> tuple[str, ...]:
    """The related-model columns a forward single-valued relation's link targets.

    Django's prefetch attach for a forward relation keys each related row by
    these columns (the target pk, a ``to_field``, every ``to_fields`` member of
    a ``ForeignObject``), so a prefetched related queryset must load them all. A
    raw field answers through ``utils/relations.py::relation_link``; a
    ``FieldMeta`` from its ``link_target_attnames`` slot, which its builder fills
    from the same reader. ``()`` when neither resolves.
    """
    targets = relation_link(field, lenient=True).target_attnames
    if targets:
        return targets
    return _precomputed_attnames(field, "link_target_attnames")


def _m2m_join_columns(field: object) -> tuple[str, ...]:
    """The related model's pk attname: the join table owns an M2M attach."""
    related_model: Any = _safe_getattr(field, "related_model")
    if related_model is None:
        return ()
    try:
        return (cast("str", related_model._meta.pk.attname),)
    except BaseException:
        return ()


def _generic_child_attname(field: object, name_attr: str) -> str | None:
    """The child column attname a ``GenericRelation`` names via ``name_attr``.

    A ``GenericForeignKey`` stores the parent id in an ordinary column
    (``object_id`` by default) and pairs it with a content-type FK; the
    ``GenericRelation`` names both via ``object_id_field_name`` /
    ``content_type_field_name``, and this resolves either name to the child
    column's attname. The windowed prefetch partitions by the ``object_id``
    attname (the content type is a constant WHERE, not part of the partition -
    Laravel morphMany precedent) and constrains the ``content_type`` attname by
    EQUALITY (Django's alias-late morph WHERE), so the content-type column
    belongs ahead of ``object_id`` in a covering composite index even though it
    is not part of the partition. ``None`` when the related model or the field
    name is missing (synthetic doubles) - the classifier never raises.
    ``get_field`` resolves for a genuine ``GenericRelation``, so no defensive
    ``FieldDoesNotExist`` swallow is needed once both inputs exist.
    """
    related_model: Any = _safe_getattr(field, "related_model")
    child_field_name = _safe_getattr(field, name_attr)
    if related_model is None or child_field_name is None:
        return None
    try:
        # A resolved child field's ``attname`` is its column name, a string.
        return cast("str", related_model._meta.get_field(child_field_name).attname)
    except BaseException:
        return None


def classify_relation_join(field: ModelField | FieldMeta) -> RelationJoinDescriptor:
    """Classify one raw Django relation field into its join descriptor.

    Pure and side-effect-free; safe to call at plan time on every nested
    connection (the field flag reads are attribute lookups). Never raises -
    an unwindowable or unresolvable shape classifies as
    ``windowable=False`` / ``partition_expr=None`` and the caller decides the
    fallback posture (``nested_planner.py::plan_connection_relation`` leaves an
    unwindowable relation unplanned for per-parent resolution).
    """
    try:
        kind = relation_kind(field)
    except BaseException:
        kind = "forward_single"
    is_m2m = _safe_flag(field, "many_to_many")
    windowable = kind in WINDOWABLE_RELATION_KINDS
    parent_link_field = None
    through_child_field = None
    content_type_column = None
    through = None
    partition: str | None = None
    if kind == "generic":
        # GenericRelation: partition by the child ``object_id`` COLUMN and
        # attach on the same column; the content type is an alias-late WHERE
        # Django's ``GenericRelatedObjectManager.get_prefetch_querysets`` adds at
        # fetch time (never the planner - resolving it early is wrong-alias DB I/O;
        # see ``nested_planner.py::plan_connection_relation``), never part of the
        # partition. ``parent_link_field``
        # STAYS None so the lateral backend refuses at ``_build_lateral_spec``
        # and the strategy degrades to the windowed body - no
        # ``LateralJoinShape.GENERIC`` arm exists (or is wanted).
        object_id_attname = _generic_child_attname(field, "object_id_field_name")
        partition = object_id_attname
        parent_join_columns = (object_id_attname,) if object_id_attname is not None else ()
        content_type_column = _generic_child_attname(field, "content_type_field_name")
        lateral_shape = LateralJoinShape.DIRECT_FK
    elif is_m2m:
        partition = _partition_expr(field)
        parent_join_columns = _m2m_join_columns(field)
        lateral_shape = LateralJoinShape.THROUGH_TABLE
        through = m2m_through_model(field, lenient=True)
        parent_link_field, through_child_field = m2m_through_link_fields(field, lenient=True)
    elif windowable:
        # Reverse FK / reverse O2O: the child rows carry the parent key in the
        # link's carrier columns. One carrier partitions the window; a
        # multi-column ``ForeignObject`` has no single partition expression, so
        # it stays unwindowable (spec-033 Decision 4: an underivable partition
        # leaves the relation unplanned for per-parent resolution) while its
        # list prefetch still attaches on every carrier.
        parent_join_columns = _carrier_attnames(field)
        if len(parent_join_columns) == 1:
            partition = parent_join_columns[0]
        lateral_shape = LateralJoinShape.DIRECT_FK
        # The child-side link (a reverse rel descriptor's ``.field``), kept only
        # when it is one column the correlated strategies can join and cast on.
        link = _safe_getattr(field, "field")
        if is_single_column_foreign_key(link):
            parent_link_field = link
    else:
        parent_join_columns = _forward_join_columns(field)
        lateral_shape = LateralJoinShape.UNSUPPORTED
    return RelationJoinDescriptor(
        kind=kind,
        windowable=windowable and partition is not None,
        partition_expr=partition,
        parent_join_columns=parent_join_columns,
        through_model=through,
        lateral_shape=lateral_shape,
        parent_link_field=parent_link_field,
        through_child_field=through_child_field,
        content_type_column=content_type_column,
    )
