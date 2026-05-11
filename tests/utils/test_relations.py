from types import SimpleNamespace

from django_strawberry_framework.utils import RelationKind, relation_kind
from django_strawberry_framework.utils.relations import (
    RelationKind as _RelationKindSubmodule,
)
from django_strawberry_framework.utils.relations import (
    relation_kind as _relation_kind_submodule,
)


def test_relation_kind_classifies_many_to_many_as_many():
    field = SimpleNamespace(many_to_many=True, one_to_many=False, one_to_one=False, auto_created=False)

    assert relation_kind(field) == "many"


def test_relation_kind_classifies_one_to_many_as_many():
    field = SimpleNamespace(many_to_many=False, one_to_many=True, one_to_one=False, auto_created=False)

    assert relation_kind(field) == "many"


def test_relation_kind_classifies_auto_created_one_to_many_as_reverse_many_to_one():
    """Reverse-FK descriptor (Django ``ManyToOneRel``): ``one_to_many`` + ``auto_created``."""
    field = SimpleNamespace(many_to_many=False, one_to_many=True, one_to_one=False, auto_created=True)

    assert relation_kind(field) == "reverse_many_to_one"


def test_relation_kind_reverse_many_to_one_is_in_literal():
    """The ``RelationKind`` alias enumerates ``"reverse_many_to_one"``.

    ``tests/test_registry.py`` constructs a ``PendingRelation`` with this
    value against the typed ``relation_kind`` field; the alias must list
    it so the contract and the call sites agree.
    """
    import typing

    assert "reverse_many_to_one" in typing.get_args(RelationKind)


def test_utils_init_reexports_match_submodule():
    """``utils.relation_kind`` / ``utils.RelationKind`` re-export the submodule contract."""
    assert relation_kind is _relation_kind_submodule
    assert RelationKind is _RelationKindSubmodule


def test_relation_kind_classifies_auto_created_one_to_one_as_reverse():
    field = SimpleNamespace(many_to_many=False, one_to_many=False, one_to_one=True, auto_created=True)

    assert relation_kind(field) == "reverse_one_to_one"


def test_relation_kind_classifies_forward_single_relations():
    field = SimpleNamespace(many_to_many=False, one_to_many=False, one_to_one=True, auto_created=False)

    assert relation_kind(field) == "forward_single"
