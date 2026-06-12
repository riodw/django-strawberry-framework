from types import SimpleNamespace

from django_strawberry_framework.utils import (
    RelationKind,
    is_many_side_relation_kind,
    relation_kind,
)
from django_strawberry_framework.utils.relations import (
    RelationKind as _RelationKindSubmodule,
)
from django_strawberry_framework.utils.relations import (
    instance_accessor,
)
from django_strawberry_framework.utils.relations import (
    is_many_side_relation_kind as _is_many_side_relation_kind_submodule,
)
from django_strawberry_framework.utils.relations import (
    relation_kind as _relation_kind_submodule,
)


def test_relation_kind_classifies_many_to_many_as_many():
    field = SimpleNamespace(
        many_to_many=True,
        one_to_many=False,
        one_to_one=False,
        auto_created=False,
    )

    assert relation_kind(field) == "many"


def test_relation_kind_classifies_one_to_many_as_many():
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=True,
        one_to_one=False,
        auto_created=False,
    )

    assert relation_kind(field) == "many"


def test_relation_kind_classifies_auto_created_one_to_many_as_reverse_many_to_one():
    """Reverse-FK descriptor (Django ``ManyToOneRel``): ``one_to_many`` + ``auto_created``."""
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=True,
        one_to_one=False,
        auto_created=True,
    )

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
    assert is_many_side_relation_kind is _is_many_side_relation_kind_submodule


def test_is_many_side_relation_kind_matches_list_valued_shapes():
    assert is_many_side_relation_kind("many") is True
    assert is_many_side_relation_kind("reverse_many_to_one") is True
    assert is_many_side_relation_kind("reverse_one_to_one") is False
    assert is_many_side_relation_kind("forward_single") is False
    assert is_many_side_relation_kind(None) is False


def test_relation_kind_classifies_auto_created_one_to_one_as_reverse():
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=True,
    )

    assert relation_kind(field) == "reverse_one_to_one"


def test_relation_kind_classifies_forward_single_relations():
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=False,
    )

    assert relation_kind(field) == "forward_single"


def test_instance_accessor_uses_get_accessor_name_for_reverse_relations():
    """A reverse rel's instance attribute is ``get_accessor_name()``, not ``name``.

    For a reverse FK declared without ``related_name``, Django's
    ``ForeignObjectRel.name`` is the related QUERY name (``"book"``) while the
    instance attribute is ``"book_set"`` - the Round-4 S3 split.
    """
    rel = SimpleNamespace(name="book", get_accessor_name=lambda: "book_set")
    assert instance_accessor(rel) == "book_set"


def test_instance_accessor_falls_back_to_name_for_forward_fields():
    """Forward fields have no ``get_accessor_name``; ``name`` IS the attribute."""
    field = SimpleNamespace(name="genres")
    assert instance_accessor(field) == "genres"


def test_instance_accessor_prefers_precomputed_field_meta_slot():
    """A ``FieldMeta``-style ``accessor_name`` slot wins over any live lookup.

    ``FieldMeta`` cannot answer ``get_accessor_name()`` (it is a frozen
    snapshot), so the builders precompute the accessor into ``accessor_name``
    and this helper reads it first - the optimizer walker passes ``FieldMeta``
    values, not raw descriptors.
    """
    meta_like = SimpleNamespace(
        name="book",
        accessor_name="book_set",
        get_accessor_name=lambda: "WRONG-not-consulted",
    )
    assert instance_accessor(meta_like) == "book_set"
