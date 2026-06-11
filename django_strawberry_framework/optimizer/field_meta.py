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
``DjangoTypeDefinition.field_map``. The O2 walker reads the cached map
instead of calling ``model._meta.get_fields()`` on every walk,
eliminating per-request Django introspection overhead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from ..exceptions import OptimizerError
from ..utils.relations import is_many_side_relation_kind, relation_kind

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
    target_pk_name: str | None = None
    fk_id_elision_eligible: bool = False
    reverse_connector_attname: str | None = None
    auto_created: bool = False

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
                explicit guard converts an otherwise late
                ``AttributeError`` deep inside the optimizer walker
                into a typed, call-site failure naming the bad input.
        """
        if not hasattr(field, "name") or not hasattr(field, "is_relation"):
            raise OptimizerError(
                f"FieldMeta.from_django_field expected a Django field descriptor "
                f"exposing 'name' and 'is_relation'; got {field!r}",
            )
        return cls._from_field_shape(field, is_relation=bool(field.is_relation))

    @classmethod
    def _from_field_shape(cls, field: Any, *, is_relation: bool) -> FieldMeta:
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
        # Read ``target_field`` once - it is consulted twice below to
        # extract both ``name`` and ``attname``.
        target_field = getattr(field, "target_field", None)
        related_model = getattr(field, "related_model", None)
        target_pk_name = _target_pk_name(related_model)
        target_field_name = getattr(target_field, "name", None)
        is_m2m = bool(getattr(field, "many_to_many", False))
        is_o2m = bool(getattr(field, "one_to_many", False))
        attname = getattr(field, "attname", None)
        auto_created = bool(getattr(field, "auto_created", False))
        # Cardinality-gated nullable rule - see ``nullable`` field docstring above for the full rationale.
        if is_m2m or is_o2m:
            nullable = False
        else:
            nullable = relation_kind(field) == "reverse_one_to_one" or bool(
                getattr(field, "null", False),
            )
        return cls(
            name=field.name,
            is_relation=is_relation,
            many_to_many=is_m2m,
            one_to_many=is_o2m,
            one_to_one=bool(getattr(field, "one_to_one", False)),
            nullable=nullable,
            related_model=related_model,
            attname=attname,
            target_field_name=target_field_name,
            target_field_attname=getattr(target_field, "attname", None),
            target_pk_name=target_pk_name,
            fk_id_elision_eligible=(
                attname is not None
                and related_model is not None
                and target_pk_name is not None
                and target_field_name == target_pk_name
                and not is_m2m
                and not is_o2m
                and not auto_created
                and not _has_composite_pk(related_model)
            ),
            reverse_connector_attname=getattr(getattr(field, "field", None), "attname", None),
            auto_created=auto_created,
        )


def _target_pk_name(model: type[models.Model] | None) -> str | None:
    """Return ``model``'s concrete primary-key field name, or ``None``."""
    if model is None:
        return None
    return model._meta.pk.name


def _has_composite_pk(model: type[models.Model]) -> bool:
    """Return whether ``model`` declares a Django 5.2+ composite primary key."""
    pk_fields = getattr(model._meta, "pk_fields", None)
    return pk_fields is not None and len(pk_fields) > 1
