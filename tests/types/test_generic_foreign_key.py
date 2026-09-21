"""DjangoType tests for GenericForeignKey rejection and GenericRelation support.

``content_object`` auto-map refusal is class-creation time. Reverse GenericRelation
payloads over HTTP live in
``examples/fakeshop/test_query/test_library_api.py``
(``test_generic_relation_tags_resolve_over_http_with_optimizer``). This module
keeps the GFK auto-map refusal, exclude-and-finalize field set, and the
``list[TaggedItemType]`` annotation rewrite.
"""

import pytest
from apps.library.models import Branch, TaggedItem
from django.contrib.contenttypes.models import ContentType

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def test_generic_foreign_key_raises_configuration_error():
    with pytest.raises(ConfigurationError, match="cannot be auto-mapped to a single GraphQL type"):

        class TaggedItemType(DjangoType):
            class Meta:
                model = TaggedItem
                fields = "__all__"


def test_generic_foreign_key_works_if_excluded():
    class ContentTypeType(DjangoType):
        class Meta:
            model = ContentType
            fields = ("id", "app_label", "model")

    class TaggedItemType(DjangoType):
        class Meta:
            model = TaggedItem
            exclude = ("content_object",)

    finalize_django_types()

    assert hasattr(TaggedItemType, "__strawberry_definition__")
    field_names = {field.python_name for field in TaggedItemType.__strawberry_definition__.fields}
    assert "content_object" not in field_names
    assert {
        "id",
        "tag",
        "content_type",
        "object_id",
    } <= field_names


def test_generic_relation_reverse_side_finalizes_to_list_target():
    class BranchType(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name", "tags")

    class TaggedItemType(DjangoType):
        class Meta:
            model = TaggedItem
            fields = ("id", "tag")

    finalize_django_types()
    assert BranchType.__annotations__["tags"] == list[TaggedItemType]
