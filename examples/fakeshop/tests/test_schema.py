"""Tests for the example schemas — both products and project schemas exercised via GraphQL execution.

Per AGENTS.md: schema is tested via ``schema.execute_sync`` with a real
GraphQL query string, never by calling resolver methods directly.
"""

import strawberry
from apps.library import schema as library_schema
from apps.products.schema import Query as ProductsQuery
from config.schema import schema as project_schema

from django_strawberry_framework import DjangoType


def test_products_schema_executes_hello():
    """Build a Strawberry schema from the products Query in isolation and execute it."""
    products_schema = strawberry.Schema(query=ProductsQuery)
    result = products_schema.execute_sync("{ hello }")
    assert result.errors is None
    assert result.data == {"hello": "fakeshop placeholder"}


def test_project_schema_executes_hello():
    """The project-level schema composes ProductsQuery and exposes ``hello`` end-to-end."""
    result = project_schema.execute_sync("{ hello }")
    assert result.errors is None
    assert result.data == {"hello": "fakeshop placeholder"}


def test_project_schema_includes_library_types():
    """The composed project schema exposes the library app's DjangoTypes."""
    result = project_schema.execute_sync(
        """
        query {
          __type(name: "BookType") {
            name
            fields { name }
          }
        }
        """,
    )

    assert result.errors is None
    assert result.data["__type"]["name"] == "BookType"
    assert {"title", "shelf", "genres"} <= {field["name"] for field in result.data["__type"]["fields"]}


def test_library_djangotype_declaration_order_stays_awkward():
    """Pin the real app's intentionally cross-referenced declaration order."""
    declaration_order = [
        name
        for name, value in vars(library_schema).items()
        if isinstance(value, type) and issubclass(value, DjangoType) and value is not DjangoType
    ]

    assert declaration_order.index("LoanType") < declaration_order.index("BookType")
    assert declaration_order.index("LoanType") < declaration_order.index("PatronType")
    assert declaration_order.index("ShelfType") < declaration_order.index("BranchType")
    assert declaration_order.index("MembershipCardType") < declaration_order.index("PatronType")
