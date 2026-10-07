"""Smoke tests proving the shared ``tests/_execution.py`` builder hands out what it promises.

``make_execution_context`` is proved by reading back the slots tests vary, and the
defaults the hook-driving tests rely on: a plain ``strawberry.Schema`` (so an assigned
extension holds the context) and no parsed document, errors or result yet.
"""

import strawberry
from graphql import GraphQLError
from strawberry.types.execution import ExecutionContext

from django_strawberry_framework import DjangoSchema
from tests._execution import make_execution_context


@strawberry.type
class _Query:
    """A schema of the test's own, to read back as the context's schema."""

    hello: str = ""


def test_make_execution_context_reads_back_what_the_test_varied():
    """Schema, query, context value and pre-execution errors read back as given."""
    schema = DjangoSchema(query=_Query)
    request = object()
    error = GraphQLError("refused")

    context = make_execution_context(
        schema=schema,
        query="{ hello }",
        context=request,
        pre_execution_errors=[error],
    )

    assert isinstance(context, ExecutionContext)
    assert context.schema is schema
    assert context.query == "{ hello }"
    assert context.context is request
    assert context.pre_execution_errors == [error]


def test_make_execution_context_defaults_to_an_unparsed_plain_schema_request():
    """The default context belongs to no ``DjangoSchema`` and has run no stage yet."""
    context = make_execution_context()

    assert type(context.schema) is strawberry.Schema
    assert context.query == "{ field }"
    assert context.context is None
    assert context.graphql_document is None
    assert context.operation_name is None
    assert context.pre_execution_errors is None
    assert context.result is None
    assert {operation.value for operation in context.allowed_operations} == {
        "query",
        "mutation",
        "subscription",
    }
