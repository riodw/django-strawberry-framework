from types import SimpleNamespace

from django_strawberry_framework.utils.relations import relation_kind


def test_relation_kind_classifies_many_to_many_as_many():
    field = SimpleNamespace(many_to_many=True, one_to_many=False, one_to_one=False, auto_created=False)

    assert relation_kind(field) == "many"


def test_relation_kind_classifies_one_to_many_as_many():
    field = SimpleNamespace(many_to_many=False, one_to_many=True, one_to_one=False, auto_created=False)

    assert relation_kind(field) == "many"


def test_relation_kind_classifies_auto_created_one_to_one_as_reverse():
    field = SimpleNamespace(many_to_many=False, one_to_many=False, one_to_one=True, auto_created=True)

    assert relation_kind(field) == "reverse_one_to_one"


def test_relation_kind_classifies_forward_single_relations():
    field = SimpleNamespace(many_to_many=False, one_to_many=False, one_to_one=True, auto_created=False)

    assert relation_kind(field) == "forward_single"
