"""Real Strawberry ``Info`` objects for tests that call a resolver-side entry point directly.

A package entry point that takes ``strawberry.Info`` reads it the way a resolver does:
``context``, ``selected_fields``, ``path``, ``schema`` (and its config), ``field_name``,
``variable_values``. ``make_info`` builds the object Strawberry's resolver wrapper builds,
the schema's ``info_class`` over a graphql-core ``GraphQLResolveInfo`` and a
``StrawberryField``, from a one-field operation parsed (not validated) against a small
schema, so each test states only what it varies. ``response_path`` builds the graphql-core
response path a resolver several levels deep sees.

``unread_info`` is a real ``Info`` that refuses every attribute read. A test whose claim is
that the path under test never reads ``info`` passes it: any read fails the test with the
attribute's name, where a placeholder ``None`` would only fail on some reads and pass a
``getattr`` default through.
"""

from collections.abc import Mapping

import strawberry
from graphql import (
    FieldNode,
    FragmentDefinitionNode,
    GraphQLResolveInfo,
    OperationDefinitionNode,
    parse,
)
from graphql.pyutils import Path, is_awaitable
from strawberry.annotation import StrawberryAnnotation
from strawberry.schema.config import StrawberryConfig
from strawberry.types.field import StrawberryField
from typing_extensions import override


@strawberry.type
class _Query:
    """The query root every built ``Info`` hangs off; no test resolves its one field."""

    field: str = ""


_DEFAULT_SCHEMA = strawberry.Schema(query=_Query)


def response_path(*keys: str | int) -> Path:
    """Build the graphql-core response path ``keys`` names, outermost key first."""
    path: Path | None = None
    for key in keys:
        path = Path(path, key, None)
    assert path is not None, "a response path needs at least one key"
    return path


def make_info(
    *,
    context: object = None,
    field_name: str = "field",
    selections: str = "",
    fragments: str = "",
    path: Path | None = None,
    variables: Mapping[str, object] | None = None,
    config: StrawberryConfig | None = None,
) -> strawberry.Info[object, object]:
    """Build the ``Info`` a resolver for ``field_name`` receives.

    ``selections`` is the GraphQL selection set under the field (``"{ edges totalCount }"``),
    read back through ``Info.selected_fields``; ``fragments`` holds the fragment definitions
    its spreads name. ``path`` defaults to the root field's own path. ``config`` builds a
    schema of its own, so ``info.schema.config`` carries it (for example
    ``relay_max_results``).
    """
    schema = _DEFAULT_SCHEMA if config is None else strawberry.Schema(query=_Query, config=config)
    document = parse(f"query {{ {field_name} {selections} }} {fragments}")
    operation = document.definitions[0]
    assert isinstance(operation, OperationDefinitionNode)
    field_node = operation.selection_set.selections[0]
    assert isinstance(field_node, FieldNode)
    graphql_schema = schema._schema
    query_type = graphql_schema.query_type
    assert query_type is not None
    raw_info = GraphQLResolveInfo(
        field_name,
        [field_node],
        query_type.fields["field"].type,
        query_type,
        path or response_path(field_name),
        graphql_schema,
        {
            definition.name.value: definition
            for definition in document.definitions
            if isinstance(definition, FragmentDefinitionNode)
        },
        None,
        operation,
        dict(variables or {}),
        context,
        is_awaitable,
    )
    field = StrawberryField(python_name=field_name, type_annotation=StrawberryAnnotation(str))
    return schema.config.info_class(_raw_info=raw_info, _field=field)


class _UnreadInfo(strawberry.Info[object, object]):
    """An ``Info`` whose every attribute read fails the test."""

    @override
    def __getattribute__(self, name: str) -> object:
        """Refuse every attribute read; ``type()`` and an exact ``isinstance`` never ask."""
        raise AssertionError(f"read info.{name}; the path under test must not read info")


def unread_info() -> strawberry.Info[object, object]:
    """Build an ``Info`` the path under test must never read (``tests/test_info.py`` proves it)."""
    built = make_info()
    return _UnreadInfo(_raw_info=built._raw_info, _field=built._field)
