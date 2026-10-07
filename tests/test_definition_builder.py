"""Smoke test proving the shared ``tests/_definition.py`` builder hands out what it promises.

Every test that passes ``make_definition`` to a package seam relies on two properties: the record
is a real ``DjangoTypeDefinition`` carrying exactly the slots the test varied, and building it
leaves the type registry untouched.
"""

from apps.library.models import Book

from django_strawberry_framework import DjangoType
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.definition import DjangoTypeDefinition
from tests._definition import make_definition


def test_make_definition_reads_back_what_the_test_varied_and_registers_nothing():
    """Model, origin, name, cursor field and relation connections read back as given."""
    registry.clear()
    definition = make_definition(
        Book,
        name="ShelvedBook",
        cursor_field=("title", "id"),
        relation_connections={"genres_connection": "genres"},
    )
    assert type(definition) is DjangoTypeDefinition
    assert definition.model is Book
    assert definition.origin is DjangoType
    assert definition.graphql_type_name == "ShelvedBook"
    assert definition.cursor_field == ("title", "id")
    assert definition.relation_connections == {"genres_connection": "genres"}
    assert definition.selected_fields == ()
    assert definition.has_custom_get_queryset is False
    assert registry.types_for(Book) == ()
    assert make_definition(Book).graphql_type_name == "DjangoType"
