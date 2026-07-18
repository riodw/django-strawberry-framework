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
  ``PARTITION BY`` input (previously derived ad hoc by
  ``plans.py::window_partition_for_prefetch``, now a shim over this module).
- ``parent_join_column`` - the child-side column Django needs loaded to
  attach prefetched rows to parents (previously
  ``nested_planner.py::_connector_only_field``, now a shim too).
- ``through_model`` + ``lateral_shape`` - the Postgres LATERAL strategy's
  join-SQL selector (``optimizer/lateral_fetch.py``: a ``DIRECT_FK`` shape
  correlates the child table directly; a ``THROUGH_TABLE`` shape joins the
  M2M through table inside the lateral subquery; ``UNSUPPORTED`` never
  plans).

The classifier takes the RAW Django relation field (or rel descriptor), not a
``FieldMeta``: the forward-M2M reverse query name lives only on
``field.remote_field``. Defensive ``getattr`` fallbacks preserve the exact
test-double contract the two shims' direct callers rely on
(``reverse_connector_attname`` / ``target_field_attname`` synthetic shapes).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any

from ..utils.relations import RelationKind, relation_kind


class LateralJoinShape(enum.Enum):
    """How a lateral (or correlated) child subquery would join to one parent."""

    DIRECT_FK = "direct_fk"
    THROUGH_TABLE = "through_table"
    UNSUPPORTED = "unsupported"


# The relation kinds a windowed prefetch can partition: every many-valued
# shape plus the reverse one-to-one (whose child row also carries the parent
# id). Single-valued FORWARD relations have no windowable parent partition.
# Public so the historical raise-contract shim
# (``plans.py::window_partition_for_prefetch``) can distinguish "wrong kind"
# from "kind OK, partition unresolved" without re-listing the set.
WINDOWABLE_RELATION_KINDS: frozenset[RelationKind] = frozenset(
    {
        "many",
        "reverse_many_to_one",
        "reverse_one_to_one",
        "generic",
    },
)


@dataclass(frozen=True)
class RelationJoinDescriptor:
    """Everything join-shaped one relation field implies for fetch planning.

    ``partition_expr`` is the parent-side partition the windowed strategy
    hands to ``PARTITION BY`` (``None`` when not ``windowable``);
    ``parent_join_column`` is the child-side connector column the prefetch
    attach reads (``None`` when no column resolves - the caller logs and
    degrades); ``through_model`` is the M2M join table when
    ``lateral_shape`` is ``THROUGH_TABLE``.

    ``parent_link_field`` / ``through_child_field`` are the resolved LINK
    FIELD OBJECTS a correlated fetch joins on (the lateral backend today;
    any future strategy or the polymorphic work reads the same resolved
    facts instead of re-walking ``remote_field`` / ``m2m_field_name``):
    for ``DIRECT_FK`` the child-side FK whose column carries the parent id
    (``through_child_field`` is ``None``); for ``THROUGH_TABLE`` the through
    table's parent-side FK and child-side FK respectively; ``None`` when the
    shape is ``UNSUPPORTED`` or the field cannot resolve them (synthetic
    doubles - the classifier never raises).

    ``content_type_column`` is the child ``content_type_id`` attname a
    ``GenericRelation`` window constrains by equality alongside the
    ``object_id`` connector (every generic query carries a constant morph
    predicate, so ``(content_type_id, object_id, ...)`` is the useful
    composite-index prefix, not ``object_id`` alone). ``None`` for every
    non-generic shape and for a synthetic generic double that cannot resolve
    it - the classifier never raises.
    """

    kind: RelationKind
    windowable: bool
    partition_expr: str | None
    parent_join_column: str | None
    through_model: type | None
    lateral_shape: LateralJoinShape
    parent_link_field: Any = None
    through_child_field: Any = None
    content_type_column: str | None = None


def _partition_expr(field: Any) -> str | None:
    """The parent-side partition expression Django's prefetch attach uses.

    ``remote_field.attname or remote_field.name`` - exactly what upstream's
    ``_optimize_prefetch_queryset`` partitions by (spec-033 Decision 4):
    child FK attname for reverse FK / reverse O2O (``"shelf_id"``), the
    child's forward M2M field name for a reverse M2M (``"genres"``), and the
    target's reverse query name for a forward M2M (``"books"`` - NOT the
    accessor when ``related_name`` is absent).
    """
    remote_field = getattr(field, "remote_field", None)
    return getattr(remote_field, "attname", None) or getattr(remote_field, "name", None)


def _parent_join_column(field: Any, kind: RelationKind) -> str | None:
    """The child-side column Django needs loaded to attach rows to parents.

    The relation-kind-specific connector
    (``nested_planner.py::_connector_only_field``): the child FK
    attname for a reverse FK / reverse one-to-one, the target field's attname
    for a forward single-valued relation, and the related model's pk attname
    for an M2M (the join table owns the attach, so the child only needs its
    pk). ``getattr`` fallbacks keep the synthetic test-double contract.
    """
    if getattr(field, "one_to_many", False) or kind == "reverse_one_to_one":
        return getattr(getattr(field, "field", None), "attname", None) or getattr(
            field,
            "reverse_connector_attname",
            None,
        )
    if not getattr(field, "many_to_many", False):
        return getattr(getattr(field, "target_field", None), "attname", None) or getattr(
            field,
            "target_field_attname",
            None,
        )
    related_model = getattr(field, "related_model", None)
    if related_model is None:
        return None
    return related_model._meta.pk.attname


def _through_model(field: Any) -> type | None:
    """The M2M join table: ``field.through`` (rel side) or ``remote_field.through``."""
    through = getattr(field, "through", None)
    if through is not None:
        return through
    return getattr(getattr(field, "remote_field", None), "through", None)


def _through_link_fields(field: Any, through: type | None) -> tuple[Any, Any]:
    """The M2M through table's (parent-side FK, child-side FK) for ``field``.

    Resolved from the forward ``ManyToManyField``'s own naming
    (``m2m_field_name`` / ``m2m_reverse_field_name``), which stays correct
    for self-referential M2Ms where scanning through-model FKs by target
    would be ambiguous. ``field`` is either the forward field (parent owns
    it) or the ``ManyToManyRel`` (parent is the target; the sides swap).
    ``(None, None)`` when the through model or the naming API is missing
    (synthetic doubles) - the classifier never raises.
    """
    forward_field = getattr(field, "field", None) or field
    if through is None or not hasattr(forward_field, "m2m_field_name"):
        return None, None
    through_meta = through._meta
    source_fk = through_meta.get_field(forward_field.m2m_field_name())
    target_fk = through_meta.get_field(forward_field.m2m_reverse_field_name())
    if forward_field is field:
        return source_fk, target_fk  # forward: parent side is the source FK.
    return target_fk, source_fk  # reverse: parent side is the target FK.


def _generic_object_id_attname(field: Any) -> str | None:
    """The child ``object_id`` column attname a ``GenericRelation`` partitions by.

    A ``GenericForeignKey`` stores the parent id in an ordinary column
    (``object_id`` by default) named on the ``GenericRelation`` via
    ``object_id_field_name``; the windowed prefetch partitions by that
    column's attname (the content type is a constant WHERE, not part of the
    partition - Laravel morphMany precedent). ``None`` when the related model
    or the field name is missing (synthetic doubles) - the classifier never
    raises. ``get_field`` resolves for a genuine ``GenericRelation``, so no
    defensive ``FieldDoesNotExist`` swallow is needed once both inputs exist.
    """
    related_model = getattr(field, "related_model", None)
    object_id_field_name = getattr(field, "object_id_field_name", None)
    if related_model is None or object_id_field_name is None:
        return None
    return related_model._meta.get_field(object_id_field_name).attname


def _generic_content_type_attname(field: Any) -> str | None:
    """The child ``content_type_id`` column attname a ``GenericRelation`` morphs on.

    A ``GenericForeignKey`` pairs the ``object_id`` column with a content-type
    FK named on the ``GenericRelation`` via ``content_type_field_name``. The
    windowed prefetch constrains that column by EQUALITY (Django's alias-late
    morph WHERE), so it belongs ahead of ``object_id`` in a covering composite
    index even though it is not part of the partition. ``None`` when the
    related model or the field name is missing (synthetic doubles) - the
    classifier never raises.
    """
    related_model = getattr(field, "related_model", None)
    content_type_field_name = getattr(field, "content_type_field_name", None)
    if related_model is None or content_type_field_name is None:
        return None
    return related_model._meta.get_field(content_type_field_name).attname


def classify_relation_join(field: Any) -> RelationJoinDescriptor:
    """Classify one raw Django relation field into its join descriptor.

    Pure and side-effect-free; safe to call at plan time on every nested
    connection (the field flag reads are attribute lookups). Never raises -
    an unwindowable or unresolvable shape classifies as
    ``windowable=False`` / ``partition_expr=None`` and the caller decides the
    fallback posture (``window_partition_for_prefetch`` keeps its historical
    ``OptimizerError`` contract on top of this).
    """
    kind = relation_kind(field)
    is_m2m = bool(getattr(field, "many_to_many", False))
    windowable = kind in WINDOWABLE_RELATION_KINDS
    parent_link_field = None
    through_child_field = None
    content_type_column = None
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
        object_id_attname = _generic_object_id_attname(field)
        partition = object_id_attname
        parent_join_column = object_id_attname
        content_type_column = _generic_content_type_attname(field)
        lateral_shape = LateralJoinShape.DIRECT_FK
        through = None
    else:
        partition = _partition_expr(field) if windowable else None
        parent_join_column = _parent_join_column(field, kind)
        if is_m2m:
            lateral_shape = LateralJoinShape.THROUGH_TABLE
            through = _through_model(field)
            parent_link_field, through_child_field = _through_link_fields(field, through)
        elif windowable:
            lateral_shape = LateralJoinShape.DIRECT_FK
            through = None
            # The child-side FK carrying the parent id (a rel descriptor's
            # ``.field``); ``None`` on a synthetic double without one.
            parent_link_field = getattr(field, "field", None)
        else:
            lateral_shape = LateralJoinShape.UNSUPPORTED
            through = None
    return RelationJoinDescriptor(
        kind=kind,
        windowable=windowable and partition is not None,
        partition_expr=partition,
        parent_join_column=parent_join_column,
        through_model=through,
        lateral_shape=lateral_shape,
        parent_link_field=parent_link_field,
        through_child_field=through_child_field,
        content_type_column=content_type_column,
    )
