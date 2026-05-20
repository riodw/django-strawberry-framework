"""Pending relation records for definition-order-independent ``DjangoType`` finalization.

This module owns the two scaffolding objects that close the import-order trap
addressed by spec-014 H1: ``PendingRelation`` (a frozen dataclass capturing a
relation field whose target ``DjangoType`` was not yet registered at collection
time) and ``PendingRelationAnnotation`` (the sentinel installed in
``cls.__annotations__`` until the target type registers). The producer is
``_build_annotations`` (``types/base.py:_build_annotations``), which records a
``PendingRelation`` and installs the sentinel for every auto-synthesized
relation. The consumer is ``finalize_django_types``
(``types/finalizer.py:finalize_django_types``), which rewrites the sentinel via
``resolved_relation_annotation`` and hands the original ``PendingRelation``
record instance back to ``TypeRegistry.discard_pending()``. ``discard_pending``
uses identity (``id()``) rather than equality or hash, so callers may pass back
the same object even when ``django_field`` is non-hashable.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db import models

from ..utils.relations import RelationKind


@dataclass(frozen=True)
class PendingRelation:
    """Relation field whose target ``DjangoType`` was not registered during collection.

    Constructed by ``_build_annotations`` (``types/base.py:_build_annotations``)
    when a relation target type is not yet registered; resolved by
    ``finalize_django_types`` (``types/finalizer.py:finalize_django_types``)
    after every ``DjangoType`` has registered.

    Finalization passes the original record instances back to
    ``TypeRegistry.discard_pending()``, which removes resolved records by
    identity rather than equality or hash semantics.

    ``field_name`` is the raw Django ``field.name`` as stored on the model; the
    snake-cased form used as a ``field_map`` key is rebuilt at the consumer via
    ``snake_case(pending.field_name)``. ``nullable`` and ``relation_kind`` are
    snapshot fields kept for self-contained record introspection; the
    production consumer reads the live ``FieldMeta`` from
    ``DjangoTypeDefinition.field_map`` instead.
    """

    source_type: type
    source_model: type[models.Model]
    field_name: str
    django_field: models.Field | models.ForeignObjectRel
    related_model: type[models.Model]
    relation_kind: RelationKind
    nullable: bool

    __hash__ = object.__hash__  # identity-based hash; django_field may be unhashable


class _PendingRelationAnnotationMeta(type):
    """Metaclass that gives the sentinel a useful schema-construction error repr."""

    # The sentinel exists only to be rewritten by ``finalize_django_types()`` in
    # ``types/finalizer.py`` (see ``resolved_relation_annotation`` rewrite of
    # ``source_type.__annotations__``) before ``strawberry.type`` ever sees the
    # class. This __repr__ shapes the Strawberry-side schema-construction
    # ``TypeError`` message that fires when that rewrite was skipped.

    def __repr__(cls) -> str:
        return (
            "<unfinalized DjangoType relation; call finalize_django_types() before constructing "
            "strawberry.Schema>"
        )


class PendingRelationAnnotation(metaclass=_PendingRelationAnnotationMeta):
    """Sentinel annotation rewritten before ``strawberry.type`` sees the class.

    Carries ``_PendingRelationAnnotationMeta`` so the schema-construction
    ``TypeError`` (raised when ``finalize_django_types()`` was skipped and
    Strawberry sees the un-rewritten sentinel) reports a useful class repr
    instead of ``<class '...PendingRelationAnnotation'>``.
    """
