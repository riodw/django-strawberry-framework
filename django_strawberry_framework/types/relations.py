"""Pending relation records for definition-order-independent ``DjangoType`` finalization."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import models

from ..utils.relations import RelationKind


@dataclass(frozen=True)
class PendingRelation:
    """Relation field whose target ``DjangoType`` was not registered during collection.

    Finalization passes the original record instances back to
    ``TypeRegistry.discard_pending()``, which removes resolved records by
    identity rather than equality or hash semantics.
    """

    source_type: type
    source_model: type[models.Model]
    field_name: str
    django_field: models.Field | models.ForeignObjectRel
    related_model: type[models.Model]
    relation_kind: RelationKind
    nullable: bool


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
    """Sentinel annotation rewritten before ``strawberry.type`` sees the class."""
