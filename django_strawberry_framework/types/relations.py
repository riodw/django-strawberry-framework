"""Pending relation records for definition-order-independent ``DjangoType`` finalization."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import models

from ..utils.relations import RelationKind


@dataclass(frozen=True)
class PendingRelation:
    """Relation field whose target ``DjangoType`` was not registered during collection.

    Fields must remain hashable because ``TypeRegistry.discard_pending()`` builds
    ``set(resolved)`` when removing records after successful finalization. The
    ``__post_init__`` hash probe surfaces a non-hashable ``django_field`` at the
    registration call site rather than deep inside finalization.
    """

    source_type: type
    source_model: type[models.Model]
    field_name: str
    django_field: models.Field | models.ForeignObjectRel
    related_model: type[models.Model]
    relation_kind: RelationKind
    nullable: bool

    def __post_init__(self) -> None:
        """Probe ``django_field`` hashability so non-hashable surrogates fail here.

        Frozen-dataclass auto-``__hash__`` hashes every field; raising at
        construction surfaces the contract break at the registration call
        site rather than inside ``set(resolved)`` during
        ``TypeRegistry.discard_pending()`` finalization.
        """
        hash(self.django_field)


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
