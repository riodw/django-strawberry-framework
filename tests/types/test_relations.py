"""PendingRelation tests for identity semantics, frozen fields and the sentinel annotation repr.

``PendingRelation`` is ``@dataclass(frozen=True, eq=False)``, so records compare
and hash by identity: two records built from the same values stay distinct, and a
record whose ``django_field`` refuses ``hash()`` (malformed metadata, such as a
custom field class defining ``__eq__`` without ``__hash__``) still hashes and
joins a set. ``TypeRegistry.discard_pending`` matches records by identity too.

No GraphQL request observes record identity or hashing. Live relation fields
live in ``examples/fakeshop/test_query/test_library_api.py``.
"""

from dataclasses import FrozenInstanceError, replace

import pytest
from apps.products.models import Category, Item

from django_strawberry_framework.types.relations import (
    PendingRelation,
    PendingRelationAnnotation,
)


class _NonHashableField:
    """Stand-in for relation metadata whose ``__hash__`` is ``None``."""

    __hash__ = None  # type: ignore[assignment]


def _build_pending() -> PendingRelation:
    return PendingRelation(
        source_type=type("Src", (), {}),
        source_model=Category,
        field_name="items",
        django_field=_NonHashableField(),  # type: ignore[arg-type]
        related_model=Item,
    )


def test_pending_relation_hash_supports_non_hashable_django_field():
    """``hash(pending)`` does not require a hashable Django relation field.

    Records hash by identity, so the field's own ``__hash__`` is never called;
    a value-based dataclass hash would raise ``TypeError`` for non-hashable
    relation metadata.
    """
    pending = _build_pending()

    assert isinstance(hash(pending), int)


def test_pending_relation_is_set_member_with_non_hashable_django_field():
    """``set([pending])`` and set membership work without raising."""
    pending = _build_pending()

    bucket = {pending}

    assert pending in bucket
    assert len(bucket) == 1


def test_equal_valued_pending_relations_stay_distinct():
    """Two records built from the same values are unequal and occupy two set slots."""
    first = _build_pending()
    second = replace(first)

    assert first != second
    assert len({first, second}) == 2


def test_pending_relation_annotation_repr():
    """``PendingRelationAnnotation`` provides a diagnostic repr for unfinalized schemas."""
    assert (
        repr(PendingRelationAnnotation)
        == "<unfinalized DjangoType relation; call finalize_django_types() before constructing strawberry.Schema>"
    )


def test_pending_relation_is_frozen_dataclass():
    """``PendingRelation`` attributes cannot be mutated post-construction."""
    pending = _build_pending()

    with pytest.raises(FrozenInstanceError):
        pending.field_name = "mutated"  # type: ignore[misc]
