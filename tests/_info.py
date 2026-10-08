"""Real Strawberry ``Info`` objects for tests that call a resolver-side entry point directly.

A package entry point that takes ``strawberry.Info`` reads it the way a resolver does:
``context``, ``selected_fields``, ``path``, ``schema`` (and its config), ``field_name``,
``variable_values``. ``make_info`` builds the object Strawberry's resolver wrapper builds,
the schema's ``info_class`` over a graphql-core ``GraphQLResolveInfo`` and a
``StrawberryField``, from a one-field operation parsed (not validated) against a small
schema, so each test states only what it varies. ``response_path`` builds the graphql-core
response path a resolver several levels deep sees.

The operation keyword (``query`` / ``mutation`` / ``subscription``) and a whole document with
several operations are both accepted: the document is parsed, never validated, so the
small schema needs no mutation or subscription root. Every built info's ``parent_type`` is
that schema's query root, which carries Strawberry's definition backref for the default
field ``field`` only.

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
    FragmentSpreadNode,
    GraphQLResolveInfo,
    InlineFragmentNode,
    OperationDefinitionNode,
    OperationType,
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
    field_name: str | None = None,
    selections: str = "",
    fragments: str = "",
    path: Path | None = None,
    variables: Mapping[str, object] | None = None,
    config: StrawberryConfig | None = None,
    operation: OperationType = OperationType.QUERY,
    document: str | None = None,
    operation_name: str | None = None,
) -> strawberry.Info[object, object]:
    """Build the ``Info`` a resolver for ``field_name`` receives.

    ``selections`` is the GraphQL selection set under the field (``"{ edges totalCount }"``),
    read back through ``Info.selected_fields``; ``fragments`` holds the fragment definitions
    its spreads name. ``operation`` is the operation keyword the one-field document opens
    with. ``document`` replaces that one-field document with a whole document (fragments
    included): the info belongs to the operation ``operation_name`` names (the first one
    when ``None``) and to that operation's first root field (reached through any root
    fragment spread), whose name is the ``field_name`` unless one is given. ``path``
    defaults to the root field's own path. ``variables`` are the operation's variable
    values. ``config`` builds a schema of its own, so ``info.schema.config`` carries it (for
    example ``relay_max_results``).
    """
    schema = _DEFAULT_SCHEMA if config is None else strawberry.Schema(query=_Query, config=config)
    if document is None:
        assert operation_name is None, "operation_name picks an operation out of a document"
        resolved_name = field_name or "field"
        document = f"{operation.value} {{ {resolved_name} {selections} }} {fragments}"
    else:
        assert not (selections or fragments), "a whole document carries its own selections"
        assert operation is OperationType.QUERY, "a whole document spells its own operations"
    parsed = parse(document)
    operation_node = next(
        definition
        for definition in parsed.definitions
        if isinstance(definition, OperationDefinitionNode)
        and (operation_name is None or getattr(definition.name, "value", None) == operation_name)
    )
    fragment_map = {
        definition.name.value: definition
        for definition in parsed.definitions
        if isinstance(definition, FragmentDefinitionNode)
    }
    field_node = _first_root_field(operation_node, fragment_map)
    resolved_name = field_name or field_node.name.value
    graphql_schema = schema._schema
    query_type = graphql_schema.query_type
    assert query_type is not None
    raw_info = GraphQLResolveInfo(
        resolved_name,
        [field_node],
        query_type.fields["field"].type,
        query_type,
        path or response_path(resolved_name),
        graphql_schema,
        fragment_map,
        None,
        operation_node,
        dict(variables or {}),
        context,
        is_awaitable,
    )
    field = StrawberryField(python_name=resolved_name, type_annotation=StrawberryAnnotation(str))
    return schema.config.info_class(_raw_info=raw_info, _field=field)


def _first_root_field(
    operation: OperationDefinitionNode,
    fragments: Mapping[str, FragmentDefinitionNode],
) -> FieldNode:
    """The operation's first root field, looking through root fragment spreads and inline ones."""
    selections = list(operation.selection_set.selections)
    while selections:
        selection = selections.pop(0)
        if isinstance(selection, FieldNode):
            return selection
        if isinstance(selection, FragmentSpreadNode):
            selections[:0] = fragments[selection.name.value].selection_set.selections
        else:
            assert isinstance(selection, InlineFragmentNode)
            selections[:0] = selection.selection_set.selections
    raise AssertionError("the operation selects no root field")


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
