"""Tests for the example schemas — both products and project schemas exercised via GraphQL execution.

Per AGENTS.md: schema is tested via ``schema.execute_sync`` with a real
GraphQL query string, never by calling resolver methods directly.
"""

import strawberry
from fakeshop.products.schema import Query as ProductsQuery
from fakeshop.schema import schema as project_schema


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
