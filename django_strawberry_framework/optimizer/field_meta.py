"""``FieldMeta`` — precomputed Django field metadata for the optimizer walker.

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
``DjangoTypeDefinition.field_map``. The O2 walker reads the cached map
instead of calling ``model._meta.get_fields()`` on every walk,
eliminating per-request Django introspection overhead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from django_strawberry_framework.exceptions import OptimizerError
from django_strawberry_framework.utils.relations import RelationKind, relation_kind

if TYPE_CHECKING:  # pragma: no cover
    from django.db import models


@runtime_checkable
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
            is never ``None`` — the rendered GraphQL annotation is
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
        target_field_name: The target model field name a FK points at,
            or ``None`` for non-FK fields.
        target_field_attname: The target model column attname a FK
            points at, preserving non-PK ``to_field`` connector rules.
        reverse_connector_attname: For reverse FK relations, the forward
            FK column on the related model that points back to the
            parent model.
        auto_created: ``True`` for reverse-side auto-created fields.
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
    reverse_connector_attname: str | None = None
    auto_created: bool = False

    @property
    def relation_kind(self) -> RelationKind:
        """Return this relation's GraphQL/runtime cardinality classifier."""
        if self.many_to_many:
            return "many"
        if self.one_to_many:
            if self.auto_created:
                return "reverse_many_to_one"
            return "many"
        if self.one_to_one and self.auto_created:
            return "reverse_one_to_one"
        return "forward_single"

    @property
    def is_many_side(self) -> bool:
        """Return whether this relation resolves as a GraphQL list."""
        return self.relation_kind in {"many", "reverse_many_to_one"}

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
                explicit guard converts an otherwise late
                ``AttributeError`` deep inside the optimizer walker
                into a typed, call-site failure naming the bad input.
        """
        if not hasattr(field, "name") or not hasattr(field, "is_relation"):
            raise OptimizerError(
                f"FieldMeta.from_django_field expected a Django field descriptor "
                f"exposing 'name' and 'is_relation'; got {field!r}",
            )
        # Read ``target_field`` once — it is consulted twice below to
        # extract both ``name`` and ``attname``.
        target_field = getattr(field, "target_field", None)
        is_m2m = bool(getattr(field, "many_to_many", False))
        is_o2m = bool(getattr(field, "one_to_many", False))
        # Many-side cardinalities (reverse FK / M2M, forward or reverse)
        # resolve to a manager / queryset that may be empty but is never
        # ``None``, so the rendered GraphQL annotation is
        # ``list[target_type]`` regardless of any Django ``null`` flag.
        # Force ``nullable=False`` for those shapes BEFORE consulting
        # ``field.null`` — Django's ``ForeignObjectRel`` (parent of
        # ``ManyToOneRel`` / ``ManyToManyRel``) proxies the forward FK's
        # ``null`` flag, so a reverse-FK descriptor for a nullable
        # forward FK would otherwise read ``True`` here. Reverse
        # OneToOne short-circuits to ``True`` because the related row
        # may legitimately be absent; every other single-relation shape
        # follows ``field.null`` with the ``getattr`` default of
        # ``False`` for descriptors that omit it.
        if is_m2m or is_o2m:
            nullable = False
        else:
            nullable = relation_kind(field) == "reverse_one_to_one" or bool(getattr(field, "null", False))
        return cls(
            name=field.name,
            is_relation=bool(field.is_relation),
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
