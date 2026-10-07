"""Real Strawberry ``ExecutionContext`` objects for tests that drive an extension hook directly.

An extension's hooks and the package runner read the engine context the way an operation
does: ``schema``, ``query``, ``context``, ``graphql_document``, ``pre_execution_errors``,
``result``. ``make_execution_context`` builds the dataclass Strawberry's schema builds for
one request, so each test states only what it varies.

The schema decides which path an operation-bound extension takes when the context is
assigned to it. The default, a plain ``strawberry.Schema``, is the path where the instance
holds the context it was given, which is what a test driving a hook by hand needs. A
``DjangoSchema`` context is the package runner's to bind: assigning one records nothing, so
pass it to ``create_extensions_runner`` and read the extension inside ``runner.operation()``.
"""

import strawberry
from graphql import GraphQLError
from strawberry.types.execution import ExecutionContext
from strawberry.types.graphql import OperationType


@strawberry.type
class _Query:
    """The query root every default context's schema hangs off; no test resolves its field."""

    field: str = ""


_DEFAULT_SCHEMA = strawberry.Schema(query=_Query)


def make_execution_context(
    *,
    schema: strawberry.Schema | None = None,
    query: str | None = "{ field }",
    context: object = None,
    pre_execution_errors: list[GraphQLError] | None = None,
) -> ExecutionContext:
    """Build the ``ExecutionContext`` Strawberry's schema builds for one request.

    ``schema`` defaults to a plain ``strawberry.Schema`` with one ``field``; ``query`` is the
    document text, unparsed (``graphql_document`` stays ``None``, as before the parse
    stage); ``context`` is the request context value resolvers see. Every operation type
    is allowed, as on a schema executed without a restriction. ``result`` starts at
    ``None``, as before execution; a test that drives a teardown assigns it.
    """
    return ExecutionContext(
        query=query,
        schema=_DEFAULT_SCHEMA if schema is None else schema,
        allowed_operations=frozenset(OperationType),
        context=context,
        pre_execution_errors=pre_execution_errors,
    )
