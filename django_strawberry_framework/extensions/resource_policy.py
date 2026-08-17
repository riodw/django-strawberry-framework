"""``DjangoResourcePolicyExtension`` - the request-side enforcement of ``ResourcePolicy``.

Spec: ``docs/SPECS/spec-047-resource_policy-0_0_14.md``.
Target release: ``0.0.14``.

``resource_policy.py`` owns the budget object; this module is the one place that
spends it. ``DjangoSchema`` installs the extension automatically, so a schema
built through this package is bounded without opt-in boilerplate.

Three passes, in the order a request meets them:

1. **Pre-parse text scan** (``on_operation``). One lexer sweep over the raw
   document counts tokens and structural nesting. It must run before the parse
   because graphql-core's parser is recursive-descent: a bound applied after the
   parse cannot stop the parse from exhausting the interpreter's stack.
2. **Document budget** (``on_execute``, before execution). One iterative,
   fragment-expanding walk over the validated AST charges expanded selections,
   aliases, and the multiplicative collection cost. Fragment spreads are charged
   at every spread site and cycle-guarded by the spread path, so neither a
   fragment nor a directive can hide a selection from accounting.
3. **Value budget** (the same walk). Every argument's value - literal, variable,
   or a literal object with variables spliced into it - is charged against the
   input-cardinality bounds, typed by the argument's own GraphQL input type. The
   walk is iterative and every container is cycle-guarded against its own
   ancestor path, so a self-referential value cannot spin it while every
   reference is still charged; it runs entirely on coerced-shape input, so no id
   is decoded and no queryset is built before it either passes or rejects.

Where each pass reaches, stated as the boundary rather than as parity:

- Passes 2 and 3 run on **every** operation, on every transport: Strawberry
  enters the ``on_execute`` hook for HTTP execution and for a WebSocket
  subscribe alike.
- Pass 1 likewise runs on every operation that carries a document, which is
  every operation the package's transports accept.
- The **rendering** of a rejection is where the transports differ, and only for
  subscriptions. Sync HTTP, async HTTP, and WebSocket queries / mutations all
  route through Strawberry's ``execute``, which turns a pre-execution exception
  into an ordinary ``errors`` entry - so a ``ResourceLimitExceeded``, being a
  ``GraphQLError``, needs no per-transport translation. Strawberry's
  ``subscribe`` path has no such conversion: a rejected WebSocket subscription
  is refused just as hard, but its client observes the operation completing
  without data rather than an error entry carrying ``extensions.code``.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from graphql import (
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLError,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    InlineFragmentNode,
    OperationDefinitionNode,
    OperationType,
    SchemaMetaFieldDef,
    TypeMetaFieldDef,
    TypeNameMetaFieldDef,
    get_named_type,
)
from graphql.language.lexer import Lexer
from graphql.language.source import Source
from graphql.language.token_kind import TokenKind
from graphql.utilities import value_from_ast_untyped
from strawberry.extensions.base_extension import SchemaExtension

from ..resource_policy import (
    DEFAULT_RESOURCE_POLICY,
    DST_RESOURCE_DEADLINE,
    DST_RESOURCE_POLICY,
    ResourceLimitExceeded,
    ResourcePolicy,
    stash_resource_policy,
)
from ..utils.context import clear_context_key, get_context_value, stash_on_context

__all__ = ("DjangoResourcePolicyExtension",)


#: Token kinds that open and close a structural nesting level. Counting all
#: three bracket families - not just selection-set braces - is deliberate: the
#: scan runs before the parse, where the only thing distinguishing an argument
#: list from a selection set is the bracket itself, and the parser recurses on
#: every one of them.
_OPEN_TOKEN_KINDS = frozenset({TokenKind.BRACE_L, TokenKind.PAREN_L, TokenKind.BRACKET_L})
_CLOSE_TOKEN_KINDS = frozenset({TokenKind.BRACE_R, TokenKind.PAREN_R, TokenKind.BRACKET_R})

#: The GraphQL scalar names the value budget classifies by name rather than by
#: Python shape. ``ID`` is every Relay ``GlobalID`` on the wire; ``Upload`` is
#: this package's file scalar.
_ID_SCALAR_NAME = "ID"
_UPLOAD_SCALAR_NAME = "Upload"

#: The argument name that marks a Relay node-refetch id list
#: (``relay.py::DjangoNodesField``'s ``nodes(ids: [ID!]!)``).
_NODE_IDS_ARGUMENT = "ids"

#: The connection-shape marker fields ``_is_connection_type`` requires: an
#: ``edges`` list whose item type carries ``node`` and ``cursor``. ``edges`` is
#: also the connection's own list field, which ``_collection_rows`` exempts.
_CONNECTION_MARKER_FIELD = "edges"
_EDGE_MARKER_FIELDS = frozenset({"node", "cursor"})

#: The introspection meta-fields, resolved by ``_field_definition`` the way
#: graphql-core's executor resolves them.
_SCHEMA_META_FIELD = "__schema"
_TYPE_META_FIELD = "__type"
_TYPENAME_META_FIELD = "__typename"
_MISSING_CONTEXT_VALUE = object()


def scan_document_text(policy: ResourcePolicy, query: str | None) -> None:
    """Charge a raw document's tokens and structural nesting, before it is parsed.

    A malformed document is left to the real parser: a ``GraphQLSyntaxError``
    raised by the lexer here means the request is going to fail validation with a
    precise syntax error anyway, and swallowing it keeps this pass from
    substituting a resource rejection for the accurate diagnostic.

    Two consequences of that, stated as they are rather than as a stronger
    promise:

    - The bounds are checked as each token is read, so a document whose size or
      nesting passes its bound BEFORE the malformed token is rejected on the
      bound. A document whose garbage comes first is not scanned past it at all -
      it is answered with the syntax error, and nothing executes, so the tokens
      the scan never reached are tokens no pass had to spend.
    - ``depth`` is a running bracket balance, so it is a true nesting depth only
      for a balanced document. An unbalanced one is a syntax error by
      construction and is answered as one.
    """
    if not query:
        return
    lexer = Lexer(Source(query))
    tokens = 0
    depth = 0
    try:
        token = lexer.advance()
        while token.kind is not TokenKind.EOF:
            tokens += 1
            if tokens > policy.max_document_tokens:
                raise ResourceLimitExceeded(
                    "max_document_tokens",
                    policy.max_document_tokens,
                    tokens,
                    "the document carries more lexical tokens than the policy allows",
                )
            if token.kind in _OPEN_TOKEN_KINDS:
                depth += 1
                if depth > policy.max_depth:
                    raise ResourceLimitExceeded(
                        "max_depth",
                        policy.max_depth,
                        depth,
                        "the document nests deeper than the policy allows",
                    )
            elif token.kind in _CLOSE_TOKEN_KINDS:
                depth -= 1
            token = lexer.advance()
    except GraphQLError as exc:
        if isinstance(exc, ResourceLimitExceeded):
            raise
        return


def _closes_a_cycle(container: Any, path: tuple[Any, ...]) -> bool:
    """``True`` when ``container`` is one of the containers it hangs under.

    Identity by ``is``, never by ``==`` or by ``id()``: an input value's
    ``__eq__`` is arbitrary consumer / library code (two distinct equal lists are
    not a cycle), and an ``id()`` is unique only among objects that are still
    alive - which the path's strong references are exactly what guarantees for
    the ancestors, and which nothing guarantees for an object the walk has
    already left.
    """
    return any(container is ancestor for ancestor in path)


class _ValueBudget:
    """Running charges for one request's argument values.

    One instance per operation walk. ``charge`` is iterative, so a deep value
    cannot recurse it, and every container is cycle-guarded against its own
    ANCESTOR PATH - the chain of containers it hangs under, held by strong
    reference and compared by ``is`` - which is the same shape
    ``charge_document`` uses for fragment spreads, with object identity in place
    of fragment names.

    **Every reference is charged.** A container reached twice - through two
    variable references, two fields of one input object, or two arguments - is
    two references' worth of work for the walkers, the coercer, and the ORM, and
    is charged twice. Only the one reference that closes a cycle back onto an
    ancestor is not: that object is already accounted for on this path, and
    following it is what would not terminate.

    Why not a request-lifetime set of already-charged ``id()`` values (which is
    what this walker used to keep): an ``id()`` is only unique among LIVE
    objects, and the coerced values this walk reads are temporaries. Freeing one
    list lets the next same-sized list reuse its address, so a set of ints keyed
    on ``id()`` silently reports a fresh container as already charged - measured
    as thousands of relation ids charged as dozens. A cycle guard needs
    ancestor-scoped lifetime and owning references; a charge-once cache needs
    neither, because charging once is not the contract.
    """

    def __init__(self, policy: ResourcePolicy) -> None:
        self.policy = policy
        self.nodes = 0
        self.relation_ids_total = 0
        self.relation_ids_this_field = 0
        self.upload_count = 0
        self.upload_bytes = 0

    def _reject(
        self,
        bound: str,
        charged: int,
        detail: str,
    ) -> None:
        limit = getattr(self.policy, bound)
        if charged > limit:
            raise ResourceLimitExceeded(bound, limit, charged, detail)

    def begin_mutation_field(self) -> None:
        """Reset the per-mutation-field relation-id counter.

        Called as each top-level mutation field is entered, so
        ``max_relation_ids_per_mutation`` bounds one write and
        ``max_relation_ids_total`` bounds the request that batches several.
        """
        self.relation_ids_this_field = 0

    def charge(
        self,
        input_type: Any,
        value: Any,
        *,
        in_mutation: bool,
        argument: str,
    ) -> None:
        """Charge one argument's whole value tree against every value bound.

        Each stack entry carries the ANCESTOR PATH of the value it describes -
        the tuple of containers it hangs under - which is both the cycle guard
        and the value's nesting depth. The path is bounded by
        ``max_value_depth``, so the identity scan a container performs over it is
        bounded too, and the total number of entries the walk ever pops is
        bounded by ``max_input_nodes``: a value that reaches the same container
        through many references pays a node per reference and runs out of node
        budget rather than running long.
        """
        stack: list[tuple[Any, Any, tuple[Any, ...]]] = [(input_type, value, ())]
        while stack:
            node_type, node_value, path = stack.pop()
            self.nodes += 1
            self._reject(
                "max_input_nodes",
                self.nodes,
                "the request's argument values carry more input nodes than the policy allows",
            )
            self._reject(
                "max_value_depth",
                len(path),
                "an argument value nests lists or input objects deeper than the policy allows",
            )
            while isinstance(node_type, GraphQLNonNull):
                node_type = node_type.of_type
            if node_value is None:
                continue
            if isinstance(node_type, GraphQLList):
                if not self._charge_container(
                    node_value,
                    stack,
                    node_type,
                    path,
                    in_mutation,
                    argument,
                ):
                    # GraphQL coerces a bare value supplied for a list input into a
                    # one-item list. Charge that synthetic container just as the
                    # coerced value will be walked, including list-family bounds
                    # and one level of value depth. ``max_container_width`` is not
                    # charged: it is validated at or above 1, so a one-item
                    # container can never exceed it.
                    self.nodes += 1
                    self._reject(
                        "max_input_nodes",
                        self.nodes,
                        "the request's argument values carry more input nodes than the policy allows",
                    )
                    self._charge_list_family(
                        node_type.of_type,
                        1,
                        in_mutation=in_mutation,
                        argument=argument,
                    )
                    stack.append((node_type.of_type, node_value, (*path, object())))
                continue
            if isinstance(node_value, (list, tuple, Mapping)):
                # An untyped container: a JSON-shaped custom scalar, or a value
                # whose Python shape does not match its declared input type.
                # Charged for width and nodes, with no family classification -
                # the family bounds are type-driven and there is no type here.
                self._charge_container(node_value, stack, node_type, path, in_mutation, argument)
                continue
            self._charge_leaf(node_type, node_value)

    def _charge_container(
        self,
        value: Any,
        stack: list[tuple[Any, Any, tuple[Any, ...]]],
        node_type: Any,
        path: tuple[Any, ...],
        in_mutation: bool,
        argument: str,
    ) -> bool:
        """Charge a list or mapping's width and queue its children; ``False`` if neither.

        A container that IS one of its own ancestors closes a cycle: it is not
        charged again and its children are not queued, which is the only thing
        keeping a self-referential value from spinning the walk. Every other
        reference to a container - including a second reference to one already
        charged elsewhere in the request - is charged in full.
        """
        if isinstance(value, Mapping):
            if _closes_a_cycle(value, path):
                return True
            self._reject(
                "max_container_width",
                len(value),
                "an input object carries more fields than the policy allows",
            )
            item_type = node_type.fields if isinstance(node_type, GraphQLInputObjectType) else None
            child_path = (*path, value)
            for name, item in value.items():
                field_def = item_type.get(name) if item_type is not None else None
                stack.append((getattr(field_def, "type", None), item, child_path))
            return True
        if not isinstance(value, (list, tuple)):
            return False
        if _closes_a_cycle(value, path):
            return True
        width = len(value)
        self._reject(
            "max_container_width",
            width,
            "a list argument is wider than the policy allows",
        )
        item_type = node_type.of_type if isinstance(node_type, GraphQLList) else None
        self._charge_list_family(item_type, width, in_mutation=in_mutation, argument=argument)
        child_path = (*path, value)
        stack.extend((item_type, item, child_path) for item in value)
        return True

    def _charge_list_family(
        self,
        item_type: Any,
        width: int,
        *,
        in_mutation: bool,
        argument: str,
    ) -> None:
        """Charge a list against the input family its item type places it in.

        The classification is type-driven, and stated once so it cannot drift:

        - a list of input objects is a **nested row set** (a nested serializer or
          formset payload);
        - a list of ``ID`` inside a **mutation** operation is a **relation id
          set**, charged both against the current mutation field and against the
          request's aggregate;
        - a list of ``ID`` under an argument named ``ids`` in a **query** is a
          **node-refetch id set**;
        - every other list is a **membership list** (an ``in`` lookup and its
          relatives).
        """
        named = get_named_type(item_type) if item_type is not None else None
        if isinstance(named, GraphQLInputObjectType):
            self._reject(
                "max_nested_rows",
                width,
                "a nested input-object list carries more rows than the policy allows",
            )
            return
        if named is not None and named.name == _ID_SCALAR_NAME:
            if in_mutation:
                self.relation_ids_this_field += width
                self.relation_ids_total += width
                self._reject(
                    "max_relation_ids_per_mutation",
                    self.relation_ids_this_field,
                    "one mutation field carries more relation ids than the policy allows",
                )
                self._reject(
                    "max_relation_ids_total",
                    self.relation_ids_total,
                    "the request carries more relation ids in aggregate than the policy allows",
                )
                return
            if argument == _NODE_IDS_ARGUMENT:
                self._reject(
                    "max_node_ids",
                    width,
                    "a node-refetch id list is longer than the policy allows",
                )
                return
        self._reject(
            "max_membership_items",
            width,
            "a membership list carries more items than the policy allows",
        )

    def _charge_leaf(self, node_type: Any, value: Any) -> None:
        """Charge a scalar or enum leaf for its byte size, or a file for its bytes.

        ``max_scalar_bytes`` measures TEXT, because the superlinear parsers and
        validators it exists for take text. A numeric leaf is not measured here
        and is not claimed to be. What actually bounds a huge integer is CPython's
        own ``sys.get_int_max_str_digits`` conversion limit (4300 digits by
        default): a variable's digits raise while the request body is parsed, and
        a document literal's raise at the ``int()`` inside graphql-core's own
        value coercion. Either way the request is refused rather than executed,
        but it is refused as a malformed-input failure, not as a
        package-configured resource rejection - stating the reach honestly is
        the point, since a bound the package does not own is not a bound it can
        promise.
        """
        named = get_named_type(node_type) if node_type is not None else None
        if named is not None and named.name == _UPLOAD_SCALAR_NAME:
            self._charge_upload(value)
            return
        if isinstance(value, str):
            self._reject(
                "max_scalar_bytes",
                len(value.encode("utf-8", errors="surrogatepass")),
                "a scalar value is larger than the policy allows",
            )

    def _charge_upload(self, value: Any) -> None:
        """Charge one uploaded file against the count, per-file, and aggregate bounds.

        The size is read from the file object and must BE a size: an upload whose
        ``size`` is absent, ``None``, non-integral, or negative is unmeasurable,
        and an unmeasurable file is rejected rather than charged as zero bytes.
        Charging the answer instead of one spelling of the missing input is what
        keeps a stream the framework cannot measure out of the permit path.
        """
        self.upload_count += 1
        self._reject(
            "max_upload_count",
            self.upload_count,
            "the request carries more files than the policy allows",
        )
        try:
            size = getattr(value, "size", None)
        except Exception as exc:
            raise ResourceLimitExceeded(
                "max_upload_file_bytes",
                self.policy.max_upload_file_bytes,
                self.policy.max_upload_file_bytes + 1,
                "an uploaded file does not report a usable size, so its bytes cannot be bounded",
            ) from exc
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ResourceLimitExceeded(
                "max_upload_file_bytes",
                self.policy.max_upload_file_bytes,
                self.policy.max_upload_file_bytes + 1,
                "an uploaded file does not report a usable size, so its bytes cannot be bounded",
            )
        self._reject(
            "max_upload_file_bytes",
            size,
            "an uploaded file is larger than the policy allows",
        )
        self.upload_bytes += size
        self._reject(
            "max_upload_total_bytes",
            self.upload_bytes,
            "the request's uploads exceed the aggregate byte budget the policy allows",
        )


class _DocumentBudget:
    """Running charges for one request's document shape."""

    def __init__(self, policy: ResourcePolicy) -> None:
        self.policy = policy
        self.selections = 0
        self.aliases = 0
        self.cost = 0

    def charge_selection(self, aliased: bool) -> None:
        """Charge one expanded field selection, and its alias when it has one."""
        self.selections += 1
        if self.selections > self.policy.max_selections:
            raise ResourceLimitExceeded(
                "max_selections",
                self.policy.max_selections,
                self.selections,
                "the document selects more fields after fragment expansion than the policy allows",
            )
        if not aliased:
            return
        self.aliases += 1
        if self.aliases > self.policy.max_aliases:
            raise ResourceLimitExceeded(
                "max_aliases",
                self.policy.max_aliases,
                self.aliases,
                "the document carries more aliases after fragment expansion than the policy allows",
            )

    def charge_collection(self, rows: int) -> None:
        """Charge one collection selection's multiplicative row cost."""
        self.cost += rows
        if self.cost > self.policy.max_collection_cost:
            raise ResourceLimitExceeded(
                "max_collection_cost",
                self.policy.max_collection_cost,
                self.cost,
                "the document's collections would fetch more rows in aggregate "
                "than the policy allows",
            )


def _root_type(graphql_schema: Any, operation: OperationType) -> Any:
    """Return the schema root type for an operation kind, or ``None`` if absent."""
    if operation is OperationType.MUTATION:
        return graphql_schema.mutation_type
    if operation is OperationType.SUBSCRIPTION:
        return graphql_schema.subscription_type
    return graphql_schema.query_type


def _field_definition(graphql_schema: Any, parent_type: Any, name: str) -> Any:
    """Return a field definition on an object / interface parent, or ``None``.

    The introspection meta-fields are resolved the way graphql-core's own
    executor resolves them - ``__schema`` and ``__type`` only on the query root,
    ``__typename`` on any composite parent - because they are real fields with
    real cost: ``__schema`` opens a subtree over every type, field, argument and
    enum value in the schema, and a walk that answered ``None`` for it charged
    the whole of introspection as one selection and then stopped descending
    (``field_def is None`` ends the branch), so introspection was the one
    document shape no depth, selection, or collection bound could see.

    ``None`` is left for a parent that is not a composite type at all - the
    "selection under a leaf" shape only an unvalidated document can present.
    """
    if name == _TYPENAME_META_FIELD:
        return TypeNameMetaFieldDef
    if graphql_schema.query_type is parent_type:
        if name == _SCHEMA_META_FIELD:
            return SchemaMetaFieldDef
        if name == _TYPE_META_FIELD:
            return TypeMetaFieldDef
    if not isinstance(parent_type, (GraphQLObjectType, GraphQLInterfaceType)):
        return None
    return parent_type.fields.get(name)


def _page_bound(policy: ResourcePolicy, node: FieldNode, variables: Mapping[str, Any]) -> int:
    """Return the row bound one connection selection would fetch.

    A ``first`` / ``last`` argument narrows the bound; anything else - absent,
    non-integral, out of range, or supplied through a variable that is not an
    integer - falls back to the policy's own page ceiling, which is the
    conservative answer rather than the permissive one.
    """
    for argument in node.arguments:
        if argument.name.value not in ("first", "last"):
            continue
        value = value_from_ast_untyped(argument.value, variables)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return min(value, policy.max_page_size)
    return policy.max_page_size


def _collection_rows(
    policy: ResourcePolicy,
    parent_type: Any,
    field_type: Any,
    node: FieldNode,
    variables: Mapping[str, Any],
) -> int | None:
    """Return the rows a field selection can fetch, or ``None`` when it is not a collection.

    A connection's own ``edges`` list is NOT a second collection: the connection
    field above it already charged the page, and charging the list again would
    multiply every connection in the document by a full page for free. This is
    the one structural exception, and it is keyed on the parent being
    connection-shaped rather than on the field name alone.
    """
    if node.name.value == _CONNECTION_MARKER_FIELD and _is_connection_type(parent_type):
        return None
    unwrapped = field_type
    while isinstance(unwrapped, GraphQLNonNull):
        unwrapped = unwrapped.of_type
    if isinstance(unwrapped, GraphQLList):
        return policy.max_list_rows
    if _is_connection_type(get_named_type(unwrapped)):
        return _page_bound(policy, node, variables)
    return None


def _is_connection_type(candidate: Any) -> bool:
    """``True`` for a Relay connection object type, detected by its whole edge shape.

    The full structural test, not merely "has a field called ``edges``": the
    ``edges`` field must be a LIST whose item type is an object carrying both
    ``node`` and ``cursor``. Matching the shape rather than a ``...Connection``
    name keeps a consumer-renamed connection inside the accounting; matching the
    edge shape rather than the field name alone keeps an ordinary type that
    happens to expose a field named ``edges`` OUT of the one structural
    exception ``_collection_rows`` grants a connection - that exception makes a
    list free, so a loose test hands a free unbounded list to any type that
    picked the name.
    """
    if not isinstance(candidate, GraphQLObjectType):
        return False
    edges = candidate.fields.get(_CONNECTION_MARKER_FIELD)
    if edges is None:
        return False
    unwrapped = edges.type
    while isinstance(unwrapped, GraphQLNonNull):
        unwrapped = unwrapped.of_type
    if not isinstance(unwrapped, GraphQLList):
        return False
    edge = get_named_type(unwrapped.of_type)
    return isinstance(edge, GraphQLObjectType) and set(edge.fields) >= _EDGE_MARKER_FIELDS


def charge_document(
    policy: ResourcePolicy,
    graphql_schema: Any,
    document: Any,
    variables: Mapping[str, Any],
    operation_name: str | None,
) -> None:
    """Charge one request's document shape and argument values, iteratively.

    The walk expands fragments at every spread site (so a fragment cannot hide a
    selection, and spreading one fragment ten times costs ten times) and carries
    the spread path so a cyclic fragment set - which validation rejects, but
    which this pass may meet under a schema that disabled validation - terminates
    instead of looping.
    """
    fragments = {
        definition.name.value: definition
        for definition in document.definitions
        if isinstance(definition, FragmentDefinitionNode)
    }
    budget = _DocumentBudget(policy)
    values = _ValueBudget(policy)
    for operation in document.definitions:
        if not isinstance(operation, OperationDefinitionNode):
            continue
        if operation_name is not None and (
            operation.name is None or operation.name.value != operation_name
        ):
            continue
        root = _root_type(graphql_schema, operation.operation)
        if root is None:
            continue
        in_mutation = operation.operation is OperationType.MUTATION
        # (node, parent type, cost multiplier, fragment spread path)
        stack: list[tuple[Any, Any, int, frozenset[str]]] = [
            (
                selection,
                root,
                1,
                frozenset(),
            )
            for selection in reversed(operation.selection_set.selections)
        ]
        while stack:
            node, parent, multiplier, path = stack.pop()
            if isinstance(node, FragmentSpreadNode):
                name = node.name.value
                fragment = fragments.get(name)
                if fragment is None or name in path:
                    continue
                condition = graphql_schema.get_type(fragment.type_condition.name.value)
                stack.extend(
                    (
                        selection,
                        condition or parent,
                        multiplier,
                        path | {name},
                    )
                    for selection in reversed(fragment.selection_set.selections)
                )
                continue
            if isinstance(node, InlineFragmentNode):
                condition = parent
                if node.type_condition is not None:
                    condition = graphql_schema.get_type(node.type_condition.name.value) or parent
                stack.extend(
                    (
                        selection,
                        condition,
                        multiplier,
                        path,
                    )
                    for selection in reversed(node.selection_set.selections)
                )
                continue
            budget.charge_selection(node.alias is not None)
            field_def = _field_definition(graphql_schema, parent, node.name.value)
            if field_def is None:
                continue
            if in_mutation and parent is root:
                values.begin_mutation_field()
            for argument in node.arguments:
                argument_def = field_def.args.get(argument.name.value)
                if argument_def is None:
                    continue
                values.charge(
                    argument_def.type,
                    value_from_ast_untyped(argument.value, variables),
                    in_mutation=in_mutation,
                    argument=argument.name.value,
                )
            child_multiplier = multiplier
            rows = _collection_rows(policy, parent, field_def.type, node, variables)
            if rows is not None:
                child_multiplier = multiplier * rows
                budget.charge_collection(child_multiplier)
            if node.selection_set is None:
                continue
            child_parent = get_named_type(field_def.type)
            stack.extend(
                (
                    selection,
                    child_parent,
                    child_multiplier,
                    path,
                )
                for selection in reversed(node.selection_set.selections)
            )


class DjangoResourcePolicyExtension(SchemaExtension):
    """Enforce the schema's ``ResourcePolicy`` on every operation.

    Installed automatically by ``schema.py::DjangoSchema``; a consumer building a
    plain ``strawberry.Schema`` adds it explicitly and may hand it its own
    policy::

        schema = strawberry.Schema(
            Query,
            extensions=[DjangoResourcePolicyExtension(policy=ResourcePolicy(max_depth=8))],
        )

    Without an explicit policy the extension reads the one the schema resolved at
    construction, falling back to the package defaults for a schema that carries
    none. There is no configuration under which the extension is installed and
    enforces nothing.
    """

    def __init__(self, *, policy: ResourcePolicy | None = None) -> None:
        self._policy = policy

    def _resolved_policy(self) -> ResourcePolicy:
        """The explicit policy, else the schema's, else the package defaults."""
        if self._policy is not None:
            return self._policy
        schema_policy = getattr(self.execution_context.schema, "resource_policy", None)
        return (
            schema_policy
            if isinstance(schema_policy, ResourcePolicy)
            else (DEFAULT_RESOURCE_POLICY)
        )

    def on_operation(self) -> Iterator[None]:
        """Publish the policy, charge the document, and restore nested context state."""
        policy = self._resolved_policy()
        context = self.execution_context.context
        previous_policy = get_context_value(
            context,
            DST_RESOURCE_POLICY,
            _MISSING_CONTEXT_VALUE,
        )
        previous_deadline = get_context_value(
            context,
            DST_RESOURCE_DEADLINE,
            _MISSING_CONTEXT_VALUE,
        )
        try:
            stash_resource_policy(context, policy)
            scan_document_text(policy, self.execution_context.query)
            yield
        finally:
            self._restore_context_value(context, DST_RESOURCE_POLICY, previous_policy)
            self._restore_context_value(context, DST_RESOURCE_DEADLINE, previous_deadline)

    @staticmethod
    def _restore_context_value(context: Any, key: str, value: Any) -> None:
        """Restore one prior context value or clear it when the key was absent."""
        if value is _MISSING_CONTEXT_VALUE:
            clear_context_key(context, key)
        else:
            stash_on_context(context, key, value)

    def on_execute(self) -> Iterator[None]:
        """Charge the validated document's shape and every argument value, then execute."""
        execution_context = self.execution_context
        document = execution_context.graphql_document
        if document is not None:
            charge_document(
                self._resolved_policy(),
                execution_context.schema._schema,
                document,
                execution_context.variables or {},
                execution_context.operation_name,
            )
        yield
