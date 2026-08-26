"""``FieldMeta`` - precomputed Django field metadata for the optimizer walker.

``FieldMeta`` is the canonical single source of truth for relation
shape across the package: ``is_relation``, cardinality flags
(``many_to_many`` / ``one_to_many`` / ``one_to_one``), ``attname``,
``nullable``, ``related_model``, and the FK target columns. Every consumer of
"relation cardinality + nullable + attname" should read from a
``FieldMeta`` instance (via ``DjangoTypeDefinition.field_map`` or a
fresh ``FieldMeta.from_django_field(...)`` call) rather than
re-deriving the shape through raw ``getattr`` on a Django field
descriptor.

Built once per ``DjangoType`` at class-creation time (in
``__init_subclass__``) and stored canonically on
``DjangoTypeDefinition.field_map``. The walker reads that cached map
for registered types; the unregistered fallback stamps the same
``FieldMeta`` shape via ``from_django_field`` rather than leaking raw
Django descriptors into the walk.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from ..exceptions import OptimizerError, _safe_type_name
from ..utils.relations import (
    _relation_attr,
    _relation_bool,
    _relation_name,
    has_composite_pk,
    instance_accessor,
    is_many_side_relation_kind,
    relation_kind,
)

if TYPE_CHECKING:  # pragma: no cover
    from django.db import models

    from ..utils.relations import RelationKind


class _DjangoFieldLike(Protocol):
    """Structural contract for the inputs ``from_django_field`` accepts.

    Every Django ``Field`` and reverse-relation descriptor surfaced by
    ``Model._meta.get_field`` / ``Model._meta.get_fields`` guarantees
    ``name`` and ``is_relation``; the remaining attributes
    (``many_to_many``, ``attname``, ``target_field``, ``field``, ...)
    are read defensively with ``getattr`` defaults so the four documented
    input shapes (forward field, reverse FK, M2M, O2O) all build cleanly
    without per-shape branching.
    """

    name: str
    is_relation: bool


@dataclass(frozen=True, slots=True)
class FieldMeta:
    """Lightweight snapshot of a Django field's optimizer-relevant attributes.

    Attributes:
        name: The Django field name (snake_case).
        is_relation: Whether the field is a relation.
        many_to_many: ``True`` for M2M fields.
        one_to_many: ``True`` for reverse FK fields.
        one_to_one: ``True`` for OneToOne fields (forward or reverse).
        nullable: Single-relation nullability rule, cardinality-gated.
            Many-side cardinalities (forward M2M, reverse FK, reverse
            M2M) short-circuit to ``False`` because a manager / queryset
            is never ``None`` - the rendered GraphQL annotation is
            ``list[target_type]`` regardless of any underlying Django
            ``null`` flag. Reverse OneToOne short-circuits to ``True``
            because the related row may legitimately be absent. Every
            other single-relation shape follows Django's ``field.null``
            flag (with ``getattr`` defaulting to ``False`` for
            descriptors that omit it). The cardinality gate is applied
            in ``from_django_field`` so consumers can read ``nullable``
            directly without re-checking ``many_to_many`` /
            ``one_to_many`` first; this defends future
            schema work against corruption from ``ForeignObjectRel``'s class-level
            ``null=True`` default leaking through.
        related_model: The target model class for relations, or ``None``.
        attname: The DB column name (e.g., ``category_id`` for a FK).
            ``None`` for reverse relations and non-FK fields.
        target_field_name: The target model field name a FK or forward
            M2M points at (Django's ``ManyToManyField`` descriptor
            exposes ``target_field`` pointing at the target model's PK,
            so forward M2M resolves to ``"id"`` here, not ``None``), or
            ``None`` for descriptors whose ``target_field`` attribute is
            absent (most reverse-relation descriptors).
        target_field_attname: The target model column attname a FK or
            forward M2M points at, preserving non-PK ``to_field``
            connector rules; ``None`` for descriptors whose
            ``target_field`` attribute is absent.
        target_pk_name: The related model's concrete primary-key field
            name, or ``None`` for non-relations / unresolved relation
            targets.
        fk_id_elision_eligible: Whether a forward single relation can
            satisfy an id-only child selection from the source row's
            local FK column without loading the related object. This is
            false for many-side relations, reverse relations, non-PK
            ``to_field`` relations, unresolved targets, and composite
            primary keys.
        reverse_connector_attname: For reverse FK relations, the forward
            FK column on the related model that points back to the
            parent model.
        auto_created: Django's auto-created flag. ``True`` for reverse
            descriptors and concrete MTI parent links.
        accessor_name: The attribute name relation rows are reached
            through on a model INSTANCE (``utils.relations
            .instance_accessor``). Diverges from ``name`` for reverse
            relations without ``related_name`` (query name ``"book"`` vs
            accessor ``"book_set"``); the optimizer's prefetch lookups
            and the strictness cache probes consume this slot because
            ``FieldMeta`` carries no ``get_accessor_name`` to ask live.
            ``None`` only on hand-built instances; both builders always
            populate it.
        concrete: Whether the field stores a column on the source model.
            Distinguishes a concrete auto-created MTI parent link from a
            non-concrete reverse ``OneToOneRel`` when this snapshot is
            reclassified by ``relation_kind``.
        content_type_field_name: For a ``contenttypes`` ``GenericRelation``,
            the name of the child model's content-type FK
            (``getattr(field, "content_type_field_name", None)``); ``None``
            for every other field shape. Populated so ``relation_kind`` sees
            the same ``"generic"`` classification whether it is handed the raw
            ``GenericRelation`` or this ``FieldMeta`` snapshot of it (the
            duck-typed detector reads non-``None`` slots, not ``hasattr``).
        object_id_field_name: For a ``GenericRelation``, the name of the child
            model's object-id column (``getattr(field, "object_id_field_name",
            None)``); ``None`` otherwise. The optimizer partitions the
            windowed prefetch by this column's attname.
    """

    name: str
    is_relation: bool = False
    many_to_many: bool = False
    one_to_many: bool = False
    one_to_one: bool = False
    nullable: bool = False
    related_model: type[models.Model] | None = None
    attname: str | None = None
    target_field_name: str | None = None
    target_field_attname: str | None = None
    target_pk_name: str | None = None
    fk_id_elision_eligible: bool = False
    reverse_connector_attname: str | None = None
    auto_created: bool = False
    accessor_name: str | None = None
    concrete: bool = False
    content_type_field_name: str | None = None
    object_id_field_name: str | None = None

    @property
    def relation_kind(self) -> RelationKind:
        """Return this relation's GraphQL/runtime cardinality classifier."""
        return relation_kind(self)

    @property
    def is_many_side(self) -> bool:
        """Return whether this relation resolves as a GraphQL list."""
        return is_many_side_relation_kind(self.relation_kind)

    @classmethod
    def from_django_field(cls, field: _DjangoFieldLike) -> FieldMeta:
        """Build a ``FieldMeta`` from a Django field descriptor.

        ``field.name`` and ``field.is_relation`` are the two load-bearing
        attributes every Django ``Field`` / reverse-relation descriptor
        guarantees; the rest are read with ``getattr`` defaults so
        forward fields, reverse relations, and the various M2M shapes
        all build cleanly without per-shape branching.

        Raises:
            OptimizerError: if ``field`` does not expose the two
                required attributes ``name`` and ``is_relation``. The
                explicit guard converts a malformed descriptor into a
                typed failure at stamp time (``DjangoType`` construction
                or the walker's unregistered fallback map-build) rather
                than a late ``AttributeError`` mid-walk.
        """
        try:
            field_name = field.name
            # Inside the guard: reading ``is_relation`` and asking it for its
            # truth value are one operation from the caller's side, and a
            # descriptor whose ``__bool__`` raises is as malformed as one whose
            # attribute access does.
            is_relation = bool(field.is_relation)
        except BaseException as exc:
            raise OptimizerError(
                f"FieldMeta.from_django_field expected a Django field descriptor "
                f"exposing 'name' and 'is_relation'; got {_safe_type_name(field)}.",
            ) from exc
        if not isinstance(field_name, str):
            raise OptimizerError(
                f"FieldMeta.from_django_field expected a string field name; "
                f"got {_safe_type_name(field_name)}.",
            )
        return cls._from_field_shape(field, is_relation=is_relation, field_name=field_name)

    @classmethod
    def _from_field_shape(
        cls,
        field: Any,
        *,
        is_relation: bool,
        field_name: str | None = None,
    ) -> FieldMeta:
        """Build a ``FieldMeta`` from a guard-cleared field-shaped descriptor.

        Internal helper shared by the canonical ``from_django_field``
        entry point and ``types/resolvers.py::_field_meta_for_resolver``'s
        test-double fallback. Both call sites have already established
        that the input exposes the field-shaped attribute surface
        (``name`` plus the ``getattr``-defaulted cardinality / target /
        related-model attributes); they differ only in how
        ``is_relation`` is determined - ``from_django_field`` reads
        ``bool(field.is_relation)``, the resolver-side fallback fires
        only when the field lacks the ``is_relation`` attribute and the
        caller is by definition asking about a relation (``True``).

        The cardinality-gated nullable rule (many-side -> ``False``;
        reverse OneToOne -> ``True``; otherwise ``field.null``) and the
        ``getattr``-defaulted relation-shape reads and the derived FK-id
        elision metadata live here so the two call sites cannot drift.
        """
        if field_name is None:
            field_name = _relation_attr(field, "name", None)
        if not isinstance(field_name, str):
            raise OptimizerError(
                f"FieldMeta expected a string field name; got {_safe_type_name(field_name)}.",
            )
        target_field = _relation_attr(field, "target_field", None)
        related_model = _relation_attr(field, "related_model", None)
        target_pk_name = _target_pk_name(related_model)
        target_field_name = (
            _relation_attr(target_field, "name", None) if target_field is not None else None
        )
        if target_field_name is not None and not isinstance(target_field_name, str):
            target_field_name = None
        target_field_attname = (
            _relation_attr(target_field, "attname", None) if target_field is not None else None
        )
        if target_field_attname is not None and not isinstance(target_field_attname, str):
            target_field_attname = None
        is_m2m = _relation_bool(field, "many_to_many", False)
        is_o2m = _relation_bool(field, "one_to_many", False)
        is_o2o = _relation_bool(field, "one_to_one", False)
        attname = _relation_attr(field, "attname", None)
        if attname is not None and not isinstance(attname, str):
            attname = None
        auto_created = _relation_bool(field, "auto_created", False)
        concrete = _relation_bool(field, "concrete", False)
        content_type_field_name = _relation_name(field, "content_type_field_name")
        object_id_field_name = _relation_name(field, "object_id_field_name")
        kind = relation_kind(field)

        # Cardinality-gated nullable rule - see ``nullable`` field docstring above for the full rationale.
        if is_many_side_relation_kind(kind):
            nullable = False
        elif kind == "reverse_one_to_one":
            nullable = True
        else:
            nullable = _relation_bool(field, "null", False)

        field_rel = _relation_attr(field, "field", None)
        reverse_connector_attname = (
            _relation_attr(field_rel, "attname", None) if field_rel is not None else None
        )
        if reverse_connector_attname is not None and not isinstance(
            reverse_connector_attname,
            str,
        ):
            reverse_connector_attname = None

        accessor_name = instance_accessor(field)

        return cls(
            name=field_name,
            is_relation=is_relation,
            many_to_many=is_m2m,
            one_to_many=is_o2m,
            one_to_one=is_o2o,
            nullable=nullable,
            related_model=related_model,
            attname=attname,
            target_field_name=target_field_name,
            target_field_attname=target_field_attname,
            target_pk_name=target_pk_name,
            fk_id_elision_eligible=(
                attname is not None
                and related_model is not None
                and target_pk_name is not None
                and target_field_name == target_pk_name
                and kind == "forward_single"
                and not has_composite_pk(related_model)
            ),
            reverse_connector_attname=reverse_connector_attname,
            auto_created=auto_created,
            accessor_name=accessor_name,
            concrete=concrete,
            content_type_field_name=content_type_field_name,
            object_id_field_name=object_id_field_name,
        )


def _target_pk_name(model: type[models.Model] | None) -> str | None:
    """Return ``model``'s concrete primary-key field name, or ``None``.

    Reads ``_meta`` defensively: ``FieldMeta`` is also built from fabricated
    field shapes on the resolver path (``_field_meta_for_resolver``), whose
    ``related_model`` may be a lightweight stand-in without ``_meta``. A
    missing ``_meta`` simply means "no resolvable target pk", which disables
    FK-id elision rather than raising.
    """
    if model is None:
        return None
    try:
        meta = getattr(model, "_meta", None)
        if meta is None:
            return None
        pk = getattr(meta, "pk", None)
        if pk is None:
            return None
        pk_name = getattr(pk, "name", None)
        return pk_name if isinstance(pk_name, str) else None
    except BaseException:
        return None
