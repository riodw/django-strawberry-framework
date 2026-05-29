import pytest
import strawberry
from apps.library.models import Branch, TaggedItem
from django.contrib.contenttypes.models import ContentType

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types
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

    @strawberry.type
    class Query:
        @strawberry.field
        def branches(self) -> list[BranchType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ branches { tags { tag } } }")

    assert BranchType.__annotations__["tags"] == list[TaggedItemType]
    assert result.errors is None
    assert result.data == {"branches": []}


@pytest.mark.django_db
def test_generic_relation_executes_with_optimizer_extension():
    branch = Branch.objects.create(name="Central", city="Boston")
    TaggedItem.objects.create(content_object=branch, tag="public")

    class BranchType(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name", "tags")

    class TaggedItemType(DjangoType):
        class Meta:
            model = TaggedItem
            fields = ("id", "tag")

    @strawberry.type
    class Query:
        @strawberry.field
        def branches(self) -> list[BranchType]:
            return Branch.objects.order_by("id")

    finalize_django_types()
    schema = strawberry.Schema(
        query=Query,
        extensions=[DjangoOptimizerExtension()],
    )
    result = schema.execute_sync("{ branches { name tags { tag } } }")

    assert result.errors is None
    assert result.data == {
        "branches": [
            {"name": "Central", "tags": [{"tag": "public"}]},
        ],
    }
