"""PendingRelation tests for identity hashing and dataclass field contracts.

The ``@dataclass(frozen=True)`` decorator would normally synthesize a
value-based ``__hash__`` that hashes every field; ``django_field`` may be
a Django rel descriptor whose ``__hash__`` is ``None`` (non-hashable), so
the class explicitly overrides ``__hash__`` with ``object.__hash__`` to
preserve the identity contract that ``TypeRegistry.discard_pending``
relies on while keeping the synthesized value-based ``__eq__``.
"""

from apps.products.models import Category, Item

from django_strawberry_framework.types.relations import PendingRelation


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


def test_pending_relation_hash_is_identity_based_with_non_hashable_django_field():
    """``hash(pending)`` returns the ``id()``-derived value and does not raise.

    Pins the explicit ``__hash__ = object.__hash__`` override at
    ``types/relations.py``: without it the dataclass-synthesized
    ``__hash__`` would hash ``django_field`` and raise ``TypeError`` for
    any non-hashable rel descriptor, contradicting the identity-based
    ``discard_pending`` contract the class docstring names.
    """
    pending = _build_pending()

    # object.__hash__ derives from id(); compare against the same formula.
    assert hash(pending) == object.__hash__(pending)


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
