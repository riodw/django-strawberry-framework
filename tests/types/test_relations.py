"""PendingRelation tests for hash consistency and dataclass field contracts.

The ``@dataclass(frozen=True)`` decorator synthesizes value-based equality.
``django_field`` may be a Django rel descriptor whose ``__hash__`` is
``None`` (non-hashable), so ``PendingRelation.__hash__`` uses guarded hash
components that keep equal records equal in sets without requiring the
descriptor itself to be hashable. ``TypeRegistry.discard_pending`` still
matches records by identity, independently of equality or hashing.
"""

from dataclasses import FrozenInstanceError

import pytest
from apps.products.models import Category, Item

from django_strawberry_framework.types.relations import (
    PendingRelation,
    PendingRelationAnnotation,
)


class _NonHashableField:
    """Stand-in for a Django rel descriptor whose ``__hash__`` is ``None``."""

    __hash__ = None  # type: ignore[assignment]


def _build_pending() -> PendingRelation:
    return PendingRelation(
        source_type=type("Src", (), {}),
        source_model=Category,
        field_name="items",
        django_field=_NonHashableField(),  # type: ignore[arg-type]
        related_model=Item,
        relation_kind="reverse_many_to_one",
        nullable=False,
    )


def test_pending_relation_hash_supports_non_hashable_django_field():
    """``hash(pending)`` does not require a hashable Django relation field.

    Pins the guarded hash implementation at ``types/relations.py``: without
    it the dataclass-synthesized hash would raise ``TypeError`` for a
    non-hashable rel descriptor.
    """
    pending = _build_pending()

    assert isinstance(hash(pending), int)


def test_pending_relation_equality_still_works_with_non_hashable_django_field():
    """Dataclass-synthesized ``__eq__`` survives the ``__hash__`` override."""
    pending = _build_pending()

    # Identity equality (used by ``discard_pending``) and reflexive value
    # equality must both hold; the existing
    # ``tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation #"assert record_a == record_b"``
    # test relies on value equality across
    # two distinct instances built from the same kwargs.
    assert pending == pending


def test_pending_relation_is_set_member_with_non_hashable_django_field():
    """``set([pending])`` and set membership work without raising."""
    pending = _build_pending()

    bucket = {pending}

    assert pending in bucket
    assert len(bucket) == 1


def test_equal_pending_relations_have_equal_hashes():
    """Value equality and hashing remain consistent for duplicate records."""
    first = _build_pending()
    second = PendingRelation(
        source_type=first.source_type,
        source_model=first.source_model,
        field_name=first.field_name,
        django_field=first.django_field,
        related_model=first.related_model,
        relation_kind=first.relation_kind,
        nullable=first.nullable,
    )

    assert first == second
    assert hash(first) == hash(second)
    assert {first, second} == {first}


def test_pending_relation_hash_falls_back_when_value_and_type_hashing_fail():
    """A field whose value AND type both refuse hashing degrades to ``id(type(value))``.

    Pins the third rung of the ``_hash_component`` ladder specifically: the
    expected hash is rebuilt with ``id(type(field))`` in the hostile slot, so a
    regression that stopped at the second rung (``hash(type(value))``) cannot
    pass by merely returning some integer.
    """

    class _HostileType(type):
        def __hash__(cls):
            raise RuntimeError("hostile type hash")

    class _HostileField(metaclass=_HostileType):
        def __hash__(self):
            raise RuntimeError("hostile value hash")

    source_type = type("Src", (), {})
    pending = PendingRelation(
        source_type=source_type,
        source_model=Category,
        field_name="items",
        django_field=_HostileField(),  # type: ignore[arg-type]
        related_model=Item,
        relation_kind="reverse_many_to_one",
        nullable=False,
    )

    assert hash(pending) == hash(
        (
            hash(source_type),
            hash(Category),
            hash("items"),
            id(_HostileField),
            hash(Item),
            hash("reverse_many_to_one"),
            hash(False),
        ),
    )


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
