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
2. **Document budget** (``on_parse``, after the parse). One iterative,
   fragment-expanding walk over the parsed AST charges expanded selections,
   aliases, and the multiplicative collection cost. Fragment spreads are charged
   at every spread site and cycle-guarded by the spread path, so neither a
   fragment nor a directive can hide a selection from accounting.
3. **Value budget** (the same walk). Every value validation converts is
   charged before validation runs, because graphql-core's
   ``ValuesOfCorrectTypeRule`` parses each literal through the scalar it is
   typed as: every field and directive argument in every definition, and every
   variable-definition default. The selected operation is charged per
   reference with its variables resolved; other operations and unspread
   fragments are charged for values only, and a default no use site charged is
   charged once at its definition. Every value is typed by the GraphQL input
   type of its position and, for a package-generated write input, by the
   bind-time field specs the owning mutation stashed. The specs are what classify a RELATION list: a
   multi-relation write input is charged against the relation-id bounds
   whether its ids render as Relay ``GlobalID``s or as raw pks, which a
   scalar-name rule cannot see (a raw-pk relation list is ``[Int!]`` on the
   wire). The walk is iterative and every container is cycle-guarded against
   its own ancestor path, so a self-referential value cannot spin it while
   every reference is still charged; it runs entirely on coerced-shape input,
   so no id is decoded and no queryset is built before it either passes or
   rejects.

Where each pass reaches, stated as the boundary rather than as parity:

- Passes 2 and 3 run on **every** operation, on every transport: Strawberry
  enters the ``on_parse`` hook for HTTP execution and for a WebSocket subscribe
  alike, and enters it whether or not that operation has validation rules to
  run.
- Pass 1 likewise runs on every operation that carries a document, which is
  every operation the package's transports accept.
- Admission is AHEAD of the validation-extension chain, not a member of it.
  Strawberry finishes every extension's parsing hook before it begins any
  validation hook, so no consumer entry can be ordered in front of this stage,
  and a document this stage refused is one no validation extension gets to walk.
  That boundary is load-bearing rather than tidy: an installed validation
  extension that runs its own pass - Strawberry's ``ValidationCache`` does -
  parses every literal argument through the scalar it is typed as, which is the
  conversion pass 3 exists to charge for BEFORE it happens.
- A rejection is rendered the same way on every transport, because pass 2 does
  not raise it: it publishes the ``ResourceLimitExceeded`` as the operation's
  pre-execution error. That is the shape every transport already renders into
  an ``errors`` entry carrying ``extensions.code``, the subscribe path
  included, and it is also what makes graphql-core's validation stand down. The
  published error is not the record of the verdict, though - it is an ordinary
  mutable field, and a validation extension assigning its own result over it
  would erase the refusal - so the verdict is recorded where only this package
  writes (``resource_policy.py::admission_rejection``). Upstream decides whether
  to execute from INSIDE the validation stage, so restating it has to happen as
  a validation hook sets up and the last one to do so has the last word:
  ``schema.py::DjangoSchema`` appends :class:`_AdmissionGuard` behind every
  consumer entry for exactly that position. It is read once more at the hook
  execution begins from, so a plain ``strawberry.Schema`` whose consumer placed a
  validation cache after this extension, which the pre-execution check then
  waves through, still meets it there.
- Pass 1 is the one that still raises, because its whole job is to refuse
  before the parser runs and a published error does not stop a parse. On a
  transport whose streaming path has no conversion for an exception out of that
  hook, a subscription over the token or structural-depth bound is refused just
  as hard - nothing parses, nothing executes - but its client sees the
  operation complete without data rather than an error entry.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar, cast

from graphql import (
    DirectiveNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLError,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLObjectType,
    InlineFragmentNode,
    ListValueNode,
    Node,
    ObjectValueNode,
    OperationDefinitionNode,
    OperationType,
    SchemaMetaFieldDef,
    TypeMetaFieldDef,
    TypeNameMetaFieldDef,
    VariableNode,
    get_named_type,
    is_input_type,
    type_from_ast,
)
from graphql.language.lexer import Lexer
from graphql.language.source import Source
from graphql.language.token_kind import TokenKind
from graphql.utilities import value_from_ast_untyped
from strawberry.extensions.base_extension import SchemaExtension
from typing_extensions import override

from ..mutations.fields import MUTATION_CLASS_MARKER
from ..resource_policy import (
    _PACKAGE_RESOURCE_POLICY,
    DST_RESOURCE_DEADLINE,
    DST_RESOURCE_POLICY,
    ResourceLimitExceeded,
    ResourcePolicy,
    _operation_policy,
    admission_rejection,
    adopt_budget_binding,
    armed_resource_policy,
    begin_resource_budget,
    budget_resume_binding,
    end_resource_budget,
    record_admission_rejection,
)
from ..utils.context import (
    restored_context_keys,
)
from ..utils.inputs import RELATION_MULTI
from ..utils.policies import copy_policy
from ..utils.private_state import PrivateAuthority
from ..utils.typing import unwrap_non_null
from .operation_state import OperationState, _OperationBoundExtension

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from graphql import (
        ArgumentNode,
        DocumentNode,
        GraphQLArgument,
        GraphQLField,
        GraphQLInputField,
        GraphQLInputFieldMap,
        GraphQLNamedType,
        GraphQLSchema,
        GraphQLType,
        SelectionNode,
        TypeNode,
        ValueNode,
        VariableDefinitionNode,
    )
    from strawberry.types import ExecutionContext

    from ..utils.inputs import InputFieldSpec

    #: One pending input node: its declared type, its value, the containers it sits
    #: in, and the mutation input spec (and nested spec map) it decodes through.
    _ValueFrame = tuple[
        GraphQLType | None,
        object,
        tuple[object, ...],
        InputFieldSpec | None,
        Mapping[str, InputFieldSpec] | None,
    ]

#: The member type a bounded container enumeration yields.
_MemberT = TypeVar("_MemberT")

__all__ = ("DjangoResourcePolicyExtension",)


#: Structural delimiter families (opening token, closing token) that define
#: nesting levels. Counting all three bracket families - not just selection-set
#: braces - is deliberate: the scan runs before the parse, where the only thing
#: distinguishing an argument list from a selection set is the bracket itself,
#: and the parser recurses on every one of them.
_STRUCTURAL_DELIMITER_PAIRS: tuple[tuple[TokenKind, TokenKind], ...] = (
    (TokenKind.BRACE_L, TokenKind.BRACE_R),
    (TokenKind.PAREN_L, TokenKind.PAREN_R),
    (TokenKind.BRACKET_L, TokenKind.BRACKET_R),
)

#: Opening and closing delimiter sets derived from ``_STRUCTURAL_DELIMITER_PAIRS``.
_OPEN_TOKEN_KINDS: frozenset[TokenKind] = frozenset(
    open_kind for open_kind, _ in _STRUCTURAL_DELIMITER_PAIRS
)
_CLOSE_TOKEN_KINDS: frozenset[TokenKind] = frozenset(
    close_kind for _, close_kind in _STRUCTURAL_DELIMITER_PAIRS
)

#: The GraphQL scalar names the value budget classifies by name rather than by
#: Python shape. ``ID`` is every Relay ``GlobalID`` on the wire; ``Upload`` is
#: this package's file scalar. The ``ID`` name is the FALLBACK classification
#: for an id list the package did not generate: a relation's bind specs (see
#: ``_mutation_input_specs``) outrank it, because a raw-pk relation list is
#: typed ``[Int!]`` on the wire and evades a name-keyed rule entirely.
_ID_SCALAR_NAME = "ID"
_UPLOAD_SCALAR_NAME = "Upload"

#: The graphql-core extension key Strawberry writes onto every converted field,
#: argument, and input field, carrying the Strawberry definition backref
#: (``strawberry.schema.schema_converter``). The resource policy reads it to
#: reach a mutation field's owning class, the same bridge
#: ``schema.py::DjangoMutationExecutionContext`` uses for the
#: completion-spanning transaction.
_STRAWBERRY_DEFINITION_BACKREF = "strawberry-definition"

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


def scan_document_text(policy: ResourcePolicy, query: str | None) -> None:
    """Charge a raw document's tokens and structural nesting, before it is parsed.

    Charged over the WHOLE request document, including operations the request did
    not name. Two bounds are scanned here - ``max_document_tokens`` and
    ``max_depth`` - and they are the request-level pair: they exist to bound the
    parse, the parse reads the whole document whatever ``operationName`` says,
    and the operation is not identified until that parse has finished. Charging
    only the named operation would therefore name a cost nobody pays and leave
    the cost somebody does pay unbounded. The shape bounds charged AFTER the
    parse - ``max_selections``, ``max_aliases``, ``max_collection_cost`` - are
    charged against the named operation alone (:func:`charge_document`), which is
    the distinction spec-047 draws between the two halves and not a disagreement
    between them. The value bounds follow validation, which parses every
    literal in the document, so the values of an operation the request did not
    name are charged too. A client sending one persisted document carrying
    several operations is charged for the document it sent.

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

    A value that is not text at all is declined, not scanned: anything that is
    not a ``str`` carries no tokens to charge, and handing it to the lexer would
    raise a raw ``TypeError`` / ``AttributeError`` / ``KeyError`` from inside
    graphql-core at exactly the input the exception-containment invariant says
    must never escape an input decoder. The transports that type-check the query
    before the extension runs (both HTTP views) make this unreachable there; the
    WebSocket path performs no such check, so the decline is the scanner's own
    contract rather than a transport's favor. What the request is answered with
    is then the parse's and the error policy's business, exactly as for any
    other document the scan cannot charge.
    """
    if not isinstance(query, str):
        return
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


def _mutation_input_specs(field_def: object) -> Mapping[str, InputFieldSpec] | None:
    """Return the bound mutation's per-input-field spec map, or ``None``.

    The bridge from the walker's graphql-core view to the bind-time reverse map
    the write flavors stash on their mutation class (``_input_field_specs``):
    the GraphQL field's ``strawberry-definition`` extension carries the
    synthesized resolver the ``DjangoMutationField`` factory stamped with the
    mutation class (``mutations/fields.py::MUTATION_CLASS_MARKER``), and the
    class's spec records carry the decode kind per input field - which is what
    says a list input is a RELATION rather than a membership list, regardless
    of whether the related type renders its ids as ``GlobalID`` (``ID``) or raw
    pks (``Int``). The records are the same ones the request-time decode walks,
    so the budget cannot disagree with the decode about what a field IS.

    ``None`` for any field that is not a package-generated mutation - a query,
    a consumer-written resolver, an unbound target - which leaves the list
    classification to the id scalar name, the only signal left. There is no
    shape under which a spec says one thing and the wire another: the specs are
    recorded from the SAME merged input dataclass the schema materialized.
    """
    strawberry_field: object = (getattr(field_def, "extensions", None) or {}).get(
        _STRAWBERRY_DEFINITION_BACKREF,
    )
    resolver = getattr(getattr(strawberry_field, "base_resolver", None), "wrapped_func", None)
    mutation_cls = getattr(resolver, MUTATION_CLASS_MARKER, None)
    # The marker is stamped by ``mutations/fields.py::DjangoMutationField`` with a
    # package mutation class, which declares ``_input_field_specs`` (``mutations/sets.py``).
    specs: list[InputFieldSpec] | None = getattr(mutation_cls, "_input_field_specs", None)
    if not specs:
        return None
    return {spec.graphql_name: spec for spec in specs}


def _nested_specs_map(spec: InputFieldSpec | None) -> Mapping[str, InputFieldSpec] | None:
    """Return the field-spec map of a NESTED input's own fields, or ``None``.

    A serializer nested-serializer field records its nested rows' own reverse
    map on the enclosing field's spec (``InputFieldSpec.nested_specs``), so a
    relation list one level down - a nested ``altBranches`` raw-pk list - is
    classified by the same bind signal as a top-level one. ``None`` for every
    non-nested field, which is every field of every non-serializer flavor.
    """
    nested: tuple[InputFieldSpec, ...] | None = getattr(spec, "nested_specs", None)
    if not nested:
        return None
    return {nested_spec.graphql_name: nested_spec for nested_spec in nested}


#: The sequence types whose ``__len__`` and iteration are the interpreter's own,
#: so a member list does not have to be built to count them honestly.
_EXACT_SEQUENCE_TYPES = (list, tuple)


def _closes_a_cycle(container: object, path: tuple[object, ...]) -> bool:
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

    Why not a request-lifetime set of already-charged ``id()`` values: an
    ``id()`` is only unique among LIVE
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
        """Reject unless ``charged`` is within ``bound``.

        Every amount reaching here is a built-in integer this walk produced - a
        counter it keeps, the length of a list it built, or a size read through
        an operation the type itself defines - and that is a property of the
        measurements, not a check performed here. It has to be: the ``>`` that
        decides this rejection and the ``__format__`` the rejection's own
        message runs are both the amount's own code, so a numeric SUBCLASS
        arriving as a charge would be consumer code answering for whether it is
        over the limit. The one place an amount is read off a value the request
        carried in - an uploaded file's ``size`` - refuses a non-integer where
        it reads it (:meth:`_charge_upload`), which is the only place that can
        say what an unusable answer there means.
        """
        limit: int = getattr(self.policy, bound)
        if charged > limit:
            raise ResourceLimitExceeded(bound, limit, charged, detail)

    def _bounded_members(
        self,
        members: Callable[[], Iterable[_MemberT]],
        bound: str,
    ) -> list[_MemberT]:
        """Read ``members()`` until ``bound`` is proven exceeded, and no further.

        The measurement is itself work the request asked for, so it is bounded
        by the same number the width is bounded by: the read stops one member
        past the limit, which is the smallest count that distinguishes "within"
        from "over". A container that would answer a million members costs two
        advances against a width bound of one.

        Nothing here consults the container's own idea of its size.
        ``list(value)`` would: it asks for a length hint first, so a ``__len__``
        that raises turns a width check into a raw error out of the request,
        and one that lies sizes the allocation. The counter is this walk's own,
        which is also why the full declared bound domain works - ``islice``
        refuses a stop argument above ``sys.maxsize``, and the largest bound a
        policy accepts is exactly ``sys.maxsize``.

        What this cannot bound is ONE advance: a container whose ``__next__``
        blocks or runs forever before yielding anything is inside consumer code
        the framework has no seam under. Every advance after the first is what
        this bounds, and a refusal to measure is a typed rejection of the bound
        being measured rather than whatever the container raised.
        """
        limit: int = getattr(self.policy, bound)
        collected: list[_MemberT] = []
        try:
            for member in members():
                collected.append(member)
                if len(collected) > limit:
                    break
        except Exception as exc:
            raise ResourceLimitExceeded(
                bound,
                limit,
                limit + 1,
                "a value charges this bound by an amount the framework cannot measure",
            ) from exc
        return collected

    def begin_mutation_field(self) -> None:
        """Reset the per-mutation-field relation-id counter.

        Called as each top-level mutation field is entered, so
        ``max_relation_ids_per_mutation`` bounds one write and
        ``max_relation_ids_total`` bounds the request that batches several.
        """
        self.relation_ids_this_field = 0

    def charge(
        self,
        input_type: GraphQLType | None,
        value: object,
        *,
        in_mutation: bool,
        argument: str,
        specs: Mapping[str, InputFieldSpec] | None = None,
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

        Each entry also carries the BIND FIELD-SPEC of the input field whose
        value it is (plus the spec map of the container it hangs under, when
        the declared input type is one the package generated): the field-level
        signal that classifies a list as a relation set rather than a
        membership list, independent of the id scalar's wire name. ``specs``
        seeds the root entry for the one argument a generated mutation's input
        was built for; ``None`` leaves every level classified by type shape
        alone.
        """
        stack: list[_ValueFrame] = [
            (
                input_type,
                value,
                (),
                None,
                specs,
            ),
        ]
        while stack:
            node_type, node_value, path, spec, spec_map = stack.pop()
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
            node_type = unwrap_non_null(node_type)
            if node_value is None:
                continue
            if isinstance(node_type, GraphQLList):
                list_type: GraphQLList[GraphQLType] = node_type
                if not self._charge_container(
                    node_value,
                    stack,
                    list_type,
                    path,
                    in_mutation,
                    argument,
                    spec,
                    spec_map,
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
                        list_type.of_type,
                        1,
                        in_mutation=in_mutation,
                        argument=argument,
                        spec=spec,
                    )
                    stack.append(
                        (
                            list_type.of_type,
                            node_value,
                            (*path, object()),
                            None,
                            _nested_specs_map(spec),
                        ),
                    )
                continue
            if isinstance(node_value, (list, tuple, Mapping)):
                # An untyped container: a JSON-shaped custom scalar, or a value
                # whose Python shape does not match its declared input type.
                # Charged for width and nodes, with no family classification -
                # the family bounds are type-driven and there is no type here.
                self._charge_container(
                    node_value,
                    stack,
                    node_type,
                    path,
                    in_mutation,
                    argument,
                    spec,
                    spec_map,
                )
                continue
            self._charge_leaf(node_type, node_value)

    def _charge_container(
        self,
        value: object,
        stack: list[_ValueFrame],
        node_type: GraphQLType | None,
        path: tuple[object, ...],
        in_mutation: bool,
        argument: str,
        spec: InputFieldSpec | None,
        spec_map: Mapping[str, InputFieldSpec] | None,
    ) -> bool:
        """Charge a list or mapping's width and queue its children; ``False`` if neither.

        A container that IS one of its own ancestors closes a cycle: it is not
        charged again and its children are not queued, which is the only thing
        keeping a self-referential value from spinning the walk. Every other
        reference to a container - including a second reference to one already
        charged elsewhere in the request - is charged in full.

        The width charged is the number of members this walk is about to QUEUE,
        never the number the container reports. At an EXACT ``list``, ``tuple``
        or ``dict`` those are the same thing, because ``len`` is then the
        interpreter's own and the members are already a sequence this package
        can queue from; the container is used exactly as it stands and nothing
        is copied.

        Anything else is read out by :meth:`_bounded_members`, one member past
        the width bound and no further. Such an object's ``__len__`` is consumer
        code answering for the size of work the request is asking for: one that
        says zero while iteration yields a hundred members charges every
        width-shaped bound - the container width itself, and the membership,
        node-id, nested-row and relation-id families ``_charge_list_family``
        derives from it - at a number no part of the request costs. Counting
        what is enumerated is what makes the charge and the queued work the same
        quantity, and stopping one past the bound is what keeps the counting
        itself inside the budget: an over-wide container is refused for what it
        proved, at one past the limit, rather than enumerated in full so the
        refusal can quote an exact size nothing downstream will use.
        """
        if isinstance(value, Mapping):
            mapping: Mapping[object, object] = value
            if _closes_a_cycle(mapping, path):
                return True
            if type(mapping) is dict:
                entries: Collection[tuple[object, object]] = mapping.items()
                width = len(mapping)
            else:
                entries = self._bounded_members(lambda: mapping.items(), "max_container_width")
                width = len(entries)
            self._reject(
                "max_container_width",
                width,
                "an input object carries more fields than the policy allows",
            )
            # graphql-core's ``cached_property`` types ``fields`` ``Any``; the property
            # itself returns a ``GraphQLInputFieldMap``.
            field_map: GraphQLInputFieldMap | None = (
                node_type.fields if isinstance(node_type, GraphQLInputObjectType) else None
            )
            child_path = (*path, mapping)
            for name, item in entries:
                # A key is whatever the value carried, and a lookup by a key that is
                # not a name just misses, so both name-keyed maps are read through
                # object-keyed views.
                field_def = (
                    cast("Mapping[object, GraphQLInputField]", field_map).get(name)
                    if field_map is not None
                    else None
                )
                # Specs resolve only under a declared input object: a hostile
                # mapping parked under a scalar argument is charged, never
                # classified, and a child's own spec map comes from ITS field
                # spec's nested records (``nested_specs``), never inherited.
                field_spec = (
                    cast("Mapping[object, InputFieldSpec]", spec_map).get(name)
                    if field_map is not None and spec_map
                    else None
                )
                field_type: GraphQLType | None = getattr(field_def, "type", None)
                stack.append(
                    (
                        field_type,
                        item,
                        child_path,
                        field_spec,
                        _nested_specs_map(field_spec),
                    ),
                )
            return True
        if not isinstance(value, (list, tuple)):
            return False
        sequence: list[object] | tuple[object, ...] = value
        if _closes_a_cycle(sequence, path):
            return True
        if type(sequence) in _EXACT_SEQUENCE_TYPES:
            members: Collection[object] = sequence
            width = len(sequence)
        else:
            members = self._bounded_members(lambda: sequence, "max_container_width")
            width = len(members)
        self._reject(
            "max_container_width",
            width,
            "a list argument is wider than the policy allows",
        )
        if isinstance(node_type, GraphQLList):
            list_type: GraphQLList[GraphQLType] = node_type
            self._charge_list_family(
                list_type.of_type,
                width,
                in_mutation=in_mutation,
                argument=argument,
                spec=spec,
            )
            item_type: GraphQLType | None = list_type.of_type
        else:
            item_type = None
        child_path = (*path, sequence)
        # List items hang under the FIELD that declared the list, so each item
        # carries that field's spec map: a nested row's own fields classify from
        # the row's own specs. The item itself is not a field value, so its spec
        # is ``None`` and its family comes from the item type.
        item_specs_map = _nested_specs_map(spec)
        stack.extend(
            (
                item_type,
                item,
                child_path,
                None,
                item_specs_map,
            )
            for item in members
        )
        return True

    def _charge_list_family(
        self,
        item_type: GraphQLType | None,
        width: int,
        *,
        in_mutation: bool,
        argument: str,
        spec: InputFieldSpec | None = None,
    ) -> None:
        """Charge a list against the input family its field places it in.

        The classification is driven by the field's bind spec when the field is
        one the package generated (``_mutation_input_specs``), and falls back to
        the item TYPE's name when there is no spec. Stated once so it cannot
        drift:

        - a list of input objects is a **nested row set** (a nested serializer or
          formset payload);
        - a list a bind spec records ``relation_multi`` is a **relation id set**
          whether its ids render as ``GlobalID``s or as raw pks, charged both
          against the current mutation field and against the request's
          aggregate - the spec is the write input's own record of what the
          field IS, and the decode charges itself against the same record, so
          the budget cannot disagree with the decode about what a list is;
        - otherwise a list of ``ID`` inside a **mutation** operation is a
          **relation id set** (the fallback for an id list the package did not
          generate, e.g. a plain ``strawberry.Schema`` input);
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
        if in_mutation and spec is not None and spec.kind == RELATION_MULTI:
            self._charge_relation_ids(width)
            return
        if named is not None and named.name == _ID_SCALAR_NAME:
            if in_mutation:
                self._charge_relation_ids(width)
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

    def _charge_relation_ids(self, width: int) -> None:
        """Charge ``width`` relation ids against the per-field and aggregate bounds.

        One body for both classification signals (the bind spec's
        ``relation_multi`` kind and the ``ID``-scalar fallback) so the two
        counters cannot charge differently under the two spellings of the same
        write.
        """
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

    def _charge_leaf(self, node_type: GraphQLType | None, value: object) -> None:
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

        Both sizes are taken through the operation the type itself defines, not
        through a method the value carries. An in-process caller's
        ``variable_values`` may carry a ``str`` or ``bytes`` SUBCLASS, and on
        one of those ``value.encode(...)`` and ``len(value)`` are consumer code:
        an ``encode`` answering one byte for a hundred thousand characters is a
        charge the bound cannot reject, and a ``__len__`` that raises replaces a
        typed rejection with a raw error out of the value walk. ``str.encode``
        is the unbound built-in applied to the value, and ``memoryview`` reads a
        buffer's size through the C buffer protocol, which a ``bytes`` subclass
        cannot answer for. Neither size is reached for as
        ``getattr(value, "nbytes", len(value))``: that default argument
        evaluates a hostile ``__len__`` before the attribute it stands in for is
        ever looked at.
        """
        named = get_named_type(node_type) if node_type is not None else None
        if named is not None and named.name == _UPLOAD_SCALAR_NAME:
            self._charge_upload(value)
            return
        if isinstance(value, str):
            self._reject(
                "max_scalar_bytes",
                len(str.encode(value, "utf-8", errors="surrogatepass")),
                "a scalar value is larger than the policy allows",
            )
        elif isinstance(value, (bytes, bytearray, memoryview)):
            self._reject(
                "max_scalar_bytes",
                memoryview(value).nbytes,
                "a scalar value is larger than the policy allows",
            )

    def _charge_upload(self, value: object) -> None:
        """Charge one uploaded file against the count, per-file, and aggregate bounds.

        The size is read from the file object and must BE a size: an upload whose
        ``size`` is absent, ``None``, non-integral, or negative is unmeasurable,
        and an unmeasurable file is rejected rather than charged as zero bytes.
        Charging the answer instead of one spelling of the missing input is what
        keeps a stream the framework cannot measure out of the permit path.

        "Integral" is the built-in type, not ``isinstance``
        (``resource_policy.py::_is_builtin_number``): an ``int`` SUBCLASS reports
        a size whose comparisons and arithmetic are the file object's own code,
        and its reflected ``__radd__`` takes priority over ``int``'s in the
        aggregate below - which is how a per-file size that passes every
        per-file bound turns ``upload_bytes`` into a value no aggregate bound
        can ever exceed.
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
        if type(size) is not int or size < 0:
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


def _root_type(
    graphql_schema: GraphQLSchema,
    operation: OperationType,
) -> GraphQLObjectType | None:
    """Return the schema root type for an operation kind, or ``None`` if absent."""
    if operation is OperationType.MUTATION:
        return graphql_schema.mutation_type
    if operation is OperationType.SUBSCRIPTION:
        return graphql_schema.subscription_type
    return graphql_schema.query_type


def _field_definition(
    graphql_schema: GraphQLSchema,
    parent_type: GraphQLNamedType | None,
    name: str,
) -> GraphQLField | None:
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
    if parent_type is not None and graphql_schema.query_type is parent_type:
        if name == _SCHEMA_META_FIELD:
            return SchemaMetaFieldDef
        if name == _TYPE_META_FIELD:
            return TypeMetaFieldDef
    if not isinstance(parent_type, (GraphQLObjectType, GraphQLInterfaceType)):
        return None
    # graphql-core's own ``cached_property`` erases the ``GraphQLFieldMap`` it returns.
    return cast("GraphQLField | None", parent_type.fields.get(name))


def _page_bound(
    policy: ResourcePolicy,
    node: FieldNode,
    variables: dict[str, object] | None,
) -> int:
    """Return the row bound one connection selection would fetch.

    A ``first`` / ``last`` argument narrows the bound; anything else - absent,
    non-integral, out of range, or supplied through a variable that is not an
    integer - falls back to the policy's own page ceiling, which is the
    conservative answer rather than the permissive one.

    "Integral" is the built-in type (``resource_policy.py::_is_builtin_number``),
    so a variable holding an ``int`` SUBCLASS narrows nothing. The bound this
    returns becomes a charge against ``max_collection_cost``, and a subclass
    reaching that counter answers both the ``min`` that would clamp it and the
    reflected ``__radd__`` the running total is accumulated through.
    """
    for argument in node.arguments:
        if argument.name.value not in ("first", "last"):
            continue
        value: object = value_from_ast_untyped(argument.value, variables)
        if type(value) is int and value >= 0:
            return min(value, policy.max_page_size)
    return policy.max_page_size


def _collection_rows(
    policy: ResourcePolicy,
    parent_type: GraphQLNamedType | None,
    field_type: GraphQLType,
    node: FieldNode,
    variables: dict[str, object] | None,
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
    unwrapped = unwrap_non_null(field_type)
    if isinstance(unwrapped, GraphQLList):
        return policy.max_list_rows
    if _is_connection_type(get_named_type(unwrapped)):
        return _page_bound(policy, node, variables)
    return None


def _is_connection_type(candidate: object) -> bool:
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
    # graphql-core's ``cached_property`` types ``fields`` ``Any``; the property itself
    # returns a ``GraphQLFieldMap``.
    edges: GraphQLField | None = candidate.fields.get(_CONNECTION_MARKER_FIELD)
    if edges is None:
        return False
    unwrapped = unwrap_non_null(edges.type)
    if not isinstance(unwrapped, GraphQLList):
        return False
    edge_list: GraphQLList[GraphQLType] = unwrapped
    edge = get_named_type(edge_list.of_type)
    return isinstance(edge, GraphQLObjectType) and set(edge.fields) >= _EDGE_MARKER_FIELDS


def _variable_names(value_node: ValueNode) -> Iterator[str]:
    """Yield the name of every variable a value AST references, iteratively."""
    stack = [value_node]
    while stack:
        node = stack.pop()
        if isinstance(node, VariableNode):
            yield node.name.value
        elif isinstance(node, ListValueNode):
            stack.extend(node.values)
        elif isinstance(node, ObjectValueNode):
            stack.extend(field.value for field in node.fields)


def _type_system_directives(definition: Node) -> Iterator[DirectiveNode]:
    """Yield every directive node inside a type-system definition, iteratively.

    Validation rejects a type-system definition in a request, but only after
    its value pass has parsed each directive argument in it through the type
    the directive declares. Nothing else in such a definition is typed as an
    input, so nothing else in it is converted.
    """
    stack = [definition]
    while stack:
        node = stack.pop()
        if isinstance(node, DirectiveNode):
            yield node
            continue
        for key in node.keys:
            child: object = getattr(node, key, None)
            if isinstance(child, Node):
                stack.append(child)
            elif isinstance(child, (list, tuple)):
                children: list[object] | tuple[object, ...] = child
                stack.extend(item for item in children if isinstance(item, Node))


def _declared_input_type(graphql_schema: GraphQLSchema, type_node: TypeNode) -> GraphQLType | None:
    """The input type a variable definition declares, or ``None`` when it names none."""
    declared = type_from_ast(graphql_schema, type_node)
    return declared if is_input_type(declared) else None


# The fragment-spread path a root's walk starts from: no spread entered yet.
_NO_SPREAD_PATH: frozenset[str] = frozenset()


class _DocumentWalk:
    """One request's walk over its document: both budgets, and the fragments it expanded.

    Each root - an operation, or a fragment definition no spread expanded - is
    walked with its own variable map and mutation-ness. ``variables`` is
    ``None`` where graphql-core coerces no variable (every definition but the
    selected operations), and a reference there is charged as ``None``: one
    node, nothing below it. ``read`` collects the variables a charged value
    referenced, and is kept only while a default is waiting to be told whether
    a use site charged it.
    """

    def __init__(
        self,
        policy: ResourcePolicy,
        graphql_schema: GraphQLSchema,
        fragments: Mapping[str, FragmentDefinitionNode],
    ) -> None:
        self.policy = policy
        self.graphql_schema = graphql_schema
        self.fragments = fragments
        self.budget = _DocumentBudget(policy)
        self.values = _ValueBudget(policy)
        self.expanded: set[str] = set()
        self.variables: dict[str, object] | None = None
        self.read: set[str] | None = None
        self.in_mutation = False

    def charge_arguments(
        self,
        arguments: Iterable[ArgumentNode] | None,
        argument_defs: Mapping[str, GraphQLArgument] | None,
        specs: Mapping[str, InputFieldSpec] | None = None,
    ) -> None:
        """Charge each argument's value, typed where ``argument_defs`` declares it, else untyped."""
        for argument in arguments or ():
            argument_def = argument_defs.get(argument.name.value) if argument_defs else None
            if self.read is not None:
                self.read.update(_variable_names(argument.value))
            carried = self.variables
            if carried is None:
                carried = dict.fromkeys(_variable_names(argument.value))
            self.values.charge(
                None if argument_def is None else argument_def.type,
                value_from_ast_untyped(argument.value, carried),
                in_mutation=self.in_mutation,
                argument=argument.name.value,
                specs=specs,
            )

    def charge_directives(self, directives: Iterable[DirectiveNode] | None) -> None:
        """Charge every directive's arguments, typed by the directive's definition where one exists."""
        for directive in directives or ():
            directive_def = self.graphql_schema.get_directive(directive.name.value)
            self.charge_arguments(
                directive.arguments,
                None if directive_def is None else directive_def.args,
            )

    def operation(
        self,
        operation: OperationDefinitionNode,
        supplied: Mapping[str, object],
        *,
        selected: bool,
    ) -> None:
        """Walk one operation, then charge each default no use site charged, at its definition."""
        graphql_schema = self.graphql_schema
        root = _root_type(graphql_schema, operation.operation)
        definitions = operation.variable_definitions or ()
        defaulted: dict[str, VariableDefinitionNode] = {}
        self.variables = None
        if selected:
            self.variables = dict(supplied)
            for var_def in definitions:
                name = var_def.variable.name.value
                if name not in self.variables and var_def.default_value is not None:
                    self.variables[name] = value_from_ast_untyped(var_def.default_value)
                    defaulted[name] = var_def
        self.read = set() if defaulted else None
        self.in_mutation = operation.operation is OperationType.MUTATION
        for var_def in definitions:
            self.charge_directives(var_def.directives)
        self.charge_directives(operation.directives)
        self.walk(
            operation.selection_set.selections,
            root,
            root,
            shape=selected and root is not None,
        )
        for var_def in definitions:
            name = var_def.variable.name.value
            if var_def.default_value is None or (
                # A default still waiting on its use sites is what kept ``read`` a set.
                defaulted.get(name) is var_def and name in cast("set[str]", self.read)
            ):
                continue
            self.values.charge(
                _declared_input_type(graphql_schema, var_def.type),
                value_from_ast_untyped(var_def.default_value),
                in_mutation=self.in_mutation,
                argument=name,
            )

    def fragment(self, fragment: FragmentDefinitionNode) -> None:
        """Walk a fragment definition no spread expanded, as a root of its own."""
        condition = self.graphql_schema.get_type(fragment.type_condition.name.value)
        self.variables = None
        self.read = None
        self.in_mutation = condition is not None and condition is self.graphql_schema.mutation_type
        self.charge_directives(fragment.directives)
        self.walk(
            fragment.selection_set.selections,
            condition,
            condition,
            shape=False,
            path=frozenset({fragment.name.value}),
        )

    def walk(
        self,
        selections: Sequence[SelectionNode],
        parent: GraphQLNamedType | None,
        root: GraphQLNamedType | None,
        *,
        shape: bool,
        path: frozenset[str] = _NO_SPREAD_PATH,
    ) -> None:
        """Walk one root's selections, charging values everywhere and shape where ``shape``."""
        graphql_schema = self.graphql_schema
        # (node, parent type, cost multiplier, fragment spread path, shape)
        stack: list[tuple[SelectionNode, GraphQLNamedType | None, int, frozenset[str], bool]] = [
            (
                selection,
                parent,
                1,
                path,
                shape,
            )
            for selection in reversed(selections)
        ]
        while stack:
            node, parent, multiplier, path, shape = stack.pop()
            # A spread's own directives are charged before its fragment
            # resolves: validation converts them whether or not the fragment
            # exists or is already expanding on this path.
            self.charge_directives(node.directives)
            if isinstance(node, FragmentSpreadNode):
                name = node.name.value
                fragment = self.fragments.get(name)
                if fragment is None or name in path:
                    continue
                self.expanded.add(name)
                self.charge_directives(fragment.directives)
                condition = graphql_schema.get_type(fragment.type_condition.name.value)
                stack.extend(
                    (
                        selection,
                        condition or parent,
                        multiplier,
                        path | {name},
                        shape,
                    )
                    for selection in reversed(fragment.selection_set.selections)
                )
                continue
            if isinstance(node, InlineFragmentNode):
                condition = parent
                # basedpyright: graphql-core types ``InlineFragmentNode.type_condition``
                # non-optional, but ``Parser.parse_fragment`` stores ``None`` on a typeless
                # inline fragment (``... @include(if: $x) { ... }``)
                if node.type_condition is not None:  # pyright: ignore[reportUnnecessaryComparison]
                    condition = graphql_schema.get_type(node.type_condition.name.value) or parent
                stack.extend(
                    (
                        selection,
                        condition,
                        multiplier,
                        path,
                        shape,
                    )
                    for selection in reversed(node.selection_set.selections)
                )
                continue
            # graphql-core's selection grammar has three node kinds and both fragment
            # kinds continued above, so what remains is a field.
            node = cast("FieldNode", node)
            if shape:
                self.budget.charge_selection(node.alias is not None)
            field_def = _field_definition(graphql_schema, parent, node.name.value)
            # A generated top-level mutation field carries its bind-time spec
            # map, which classifies the write input's fields for the whole
            # argument walk below; ``begin_mutation_field`` keeps the per-field
            # relation counter scoped to exactly this field.
            specs = None
            if self.in_mutation and parent is root:
                self.values.begin_mutation_field()
                specs = _mutation_input_specs(field_def)
            self.charge_arguments(
                node.arguments,
                None if field_def is None else field_def.args,
                specs,
            )
            child_multiplier = multiplier
            if shape and field_def is not None:
                rows = _collection_rows(self.policy, parent, field_def.type, node, self.variables)
                if rows is not None:
                    child_multiplier = multiplier * rows
                    self.budget.charge_collection(child_multiplier)
            if node.selection_set is None:
                continue
            # Below a field the parent does not have nothing is typed and no
            # shape is charged, but values still are: validation parses them.
            child_parent = None if field_def is None else get_named_type(field_def.type)
            stack.extend(
                (
                    selection,
                    child_parent,
                    child_multiplier,
                    path,
                    shape and field_def is not None,
                )
                for selection in reversed(node.selection_set.selections)
            )


def charge_document(
    policy: ResourcePolicy,
    graphql_schema: GraphQLSchema,
    document: DocumentNode,
    variables: Mapping[str, object] | None = None,
    operation_name: str | None = None,
) -> None:
    """Charge one request's document shape and every value validation converts, iteratively.

    ONE walk over every operation in the document. The selected operation
    (every operation, when the request names none) is charged for shape -
    expanded selections, aliases, collection cost - and for values; every other
    operation, the subtree of a field the parent does not have, and each
    fragment definition no spread expanded are charged for values only,
    because validation parses their literals too. Fragments expand at every
    spread site (spreading one ten times costs ten times) and the spread path
    makes a cyclic fragment set terminate.

    Values are charged per reference: every field and directive argument - on
    the operation, a variable definition, a field, a spread (before its
    fragment resolves), an inline fragment, and a fragment definition once per
    expansion - typed by the argument's declared input type, untyped where
    nothing declares one. In a selected operation a variable resolves to the
    supplied value or, failing that, to its default; anywhere else it is
    charged as ``None``, since graphql-core coerces no variable there. A default
    no use site charged - unused, shadowed by a supplied value, or in an
    unselected operation - is charged once at its definition.

    Every shape validation would have rejected is a shape this walk meets,
    because it runs BEFORE validation: a cyclic fragment set, an unknown field,
    fragment, argument or directive, a selection under a leaf, an undefined
    variable. None of them is an error here; what rejects such a document is
    validation, which runs next and says so in its own words.
    """
    fragments = {
        definition.name.value: definition
        for definition in document.definitions
        if isinstance(definition, FragmentDefinitionNode)
    }
    walk = _DocumentWalk(policy, graphql_schema, fragments)
    supplied: Mapping[str, object] = variables if variables is not None else {}
    for definition in document.definitions:
        if isinstance(definition, OperationDefinitionNode):
            selected = operation_name is None or (
                definition.name is not None and definition.name.value == operation_name
            )
            walk.operation(definition, supplied, selected=selected)
        elif not isinstance(definition, FragmentDefinitionNode):
            walk.variables = None
            walk.read = None
            walk.in_mutation = False
            walk.charge_directives(_type_system_directives(definition))
    # A duplicate name is not the definition a spread expands, so it is a root too.
    for definition in document.definitions:
        if isinstance(definition, FragmentDefinitionNode) and (
            fragments[definition.name.value] is not definition
            or definition.name.value not in walk.expanded
        ):
            walk.fragment(definition)


@dataclass(frozen=True)
class _AcceptedPolicy:
    """What one ``DjangoResourcePolicyExtension`` construction settled.

    ``policy`` is the explicit override the extension was handed, or ``None``
    for the supported configuration that has none and reads its schema's policy
    per operation. Either way the record EXISTS, which is what separates an
    extension that was constructed from one that never was; a policy of ints
    and a float points at nothing, so holding this retains nothing but the
    policy.
    """

    policy: ResourcePolicy | None


#: What each constructed extension settled, held here and by nothing else.
#:
#: On a plain ``strawberry.Schema`` an instance entry is accepted as itself, so
#: it stays reachable through ``info.schema.extensions`` for as long as the
#: schema lives, and what it holds is what bounds the NEXT operation. An
#: attribute holding that is a name a resolver writes once - or deletes once,
#: which selects the schema's policy or the package defaults instead, and those
#: may be wider than the policy this extension was configured with. A policy is
#: ints and a float, so holding one here retains nothing but the policy; see
#: ``utils/private_state.py::PrivateAuthority``.
_EXPLICIT_POLICY: PrivateAuthority[_AcceptedPolicy] = PrivateAuthority()


def restate_admission_verdict(execution_context: ExecutionContext) -> None:
    """Republish this operation's admission verdict over whatever replaced it.

    One statement of what a rejected operation's pre-execution error is, applied
    at the two positions in the validation stage that can be answered for: the
    enforcing extension's own hook, and the package-appended guard behind every
    consumer entry.
    """
    rejection = admission_rejection()
    if rejection is not None:
        execution_context.pre_execution_errors = [rejection]


class DjangoResourcePolicyExtension(_OperationBoundExtension[OperationState]):
    """Enforce the schema's ``ResourcePolicy`` on every operation.

    ``schema.py::DjangoSchema`` builds one on every operation from the policy it
    was constructed with, so the bound is configured there, not installed::

        schema = DjangoSchema(
            query=Query,
            config=strawberry_config(),
            resource_policy=ResourcePolicy(max_depth=8),
        )

    **On a ``DjangoSchema`` this is not a consumer entry at all.** An entry that
    IS this class, or an exact instance of it, is read once as a declaration of
    the schema's bound and does not travel into the chain - which is also why no
    resolver finds one in ``info.schema.extensions`` to write through. A subclass
    is refused at construction and a factory resolving to one refuses the
    operation: both would decide enforcement from consumer code on a request
    already running.

    A plain ``strawberry.Schema`` builds none of that, so a consumer on one adds
    the extension explicitly and may hand it its own policy::

        schema = strawberry.Schema(
            query=Query,
            config=strawberry_config(),
            extensions=[lambda: DjangoResourcePolicyExtension(policy=ResourcePolicy(max_depth=8))],
        )

    **The entry is a factory rather than an instance, and that is the supported
    spelling for a plain ``strawberry.Schema``.** Strawberry passes an instance
    entry through unchanged, so one object answers every operation, and only a
    ``DjangoSchema`` builds the runner that gives such an object per-operation
    state (``extensions/operation_state.py``). A factory that returns a new
    extension per call - or the bare class, when no override is needed - is
    operation-local on any schema, because the instance itself is. Copied onto a
    ``DjangoSchema`` the same factory refuses every operation, by the rule above.

    Without an explicit policy the extension reads the one the schema resolved at
    construction, falling back to the package defaults for a schema that carries
    none. There is no configuration under which the extension is installed and
    enforces nothing.
    """

    _reconstruction_refusal = (
        "A resource-policy extension is configured when it is constructed; "
        "re-running its __init__ on an instance a schema is already enforcing "
        "with would replace the policy it was accepted with."
    )

    def __init__(self, *, policy: ResourcePolicy | None = None) -> None:
        # An accepted instance is reachable from every resolver the schema
        # serves, and so is its ``__init__``. Re-running it would nominate a new
        # budget for every later operation, which is the widening no attribute
        # on this object admits either. The base constructor refuses that before
        # either branch here, and answers from the construction record rather
        # than from the policy in it: an extension deliberately constructed
        # WITHOUT an override is configured - it inherits its schema's policy -
        # and reading that as an object nobody ever constructed would leave the
        # one configuration open to being handed a wider ceiling after
        # acceptance.
        super().__init__()
        # An explicit policy is canonicalized HERE, where the configuration is
        # accepted, rather than at each hook that reads it. It arrives straight
        # from a consumer and has been through none of the schema-construction
        # normalization ``DjangoSchema(resource_policy=...)`` applies, so until
        # it is read out once into an exact ``ResourcePolicy`` every bound read
        # off it is consumer code that may answer differently each time it is
        # asked - which is the whole distance between "the extension holds a
        # policy" and "the operation has a budget". No override settles as none:
        # the record says the extension inherits, not that it pinned whatever
        # its schema resolved at the moment it was built.
        _EXPLICIT_POLICY.settle(
            self,
            _AcceptedPolicy(None if policy is None else _operation_policy(policy)),
        )

    @property
    def _policy(self) -> ResourcePolicy | None:
        """The explicit policy this extension was configured with, as a copy.

        An extension instance passed to a plain ``strawberry.Schema``'s
        ``extensions=[...]`` is accepted as the entry itself, so it stays
        reachable through ``info.schema.extensions`` for the life of the schema
        - and what it holds is the authority the NEXT operation is bounded by.
        An ordinary attribute is therefore a seam a resolver widens every later
        request through, by rebinding it, deleting it, or writing a bound on the
        object it answers with. ``DjangoSchema`` reads a direct instance entry
        once and keeps the bound as its own canonical state instead, and this
        property is how it reads it. The configuration
        is held as ``utils/private_state.py::PrivateAuthority`` instead, which
        no name on this object answers with, and each read hands out a
        duplicate. ``None`` here means this extension was given no policy to
        hold - by the construction that settled none, or because nothing ever
        constructed it - and never that one it was given has gone missing.
        """
        accepted = _EXPLICIT_POLICY.recall(self)
        if accepted is None or accepted.policy is None:
            return None
        return copy_policy(accepted.policy)

    def _resolved_policy(self) -> ResourcePolicy:
        """The explicit policy, else the schema's, else the package defaults.

        Consulted once per operation, by :meth:`on_operation`, which arms what
        it returns; every later charge in that operation reads the armed
        snapshot instead (:func:`resource_policy.armed_resource_policy`).
        """
        explicit = self._policy
        if explicit is not None:
            return explicit
        schema_policy: object = getattr(self.execution_context.schema, "resource_policy", None)
        return (
            schema_policy
            if isinstance(schema_policy, ResourcePolicy)
            else (_PACKAGE_RESOURCE_POLICY)
        )

    @override
    def on_operation(self) -> Iterator[None]:
        """Arm the policy, charge the document, and restore nested execution state.

        The one point in the operation where the configuration is consulted.
        What every later charge reads is the snapshot armed here, so the token
        scan, the document walk, the value walk and the per-field collection
        seams cannot be enforcing different budgets within one request.

        Two scopes, closed in the order they were opened: the published context
        mirror is restored by ``restored_context_keys``, and the armed budget -
        the value the enforcement seams actually read - is disarmed by its own
        scope, so a nested execution restores the outer operation's budget
        rather than leaving the inner one armed.

        The budget is armed for the whole operation, which for a streamed one
        means frames produced in tasks this hook never ran in. Registering it on
        the operation state has the runner bind it again around each of them
        (``operation_state.py::OperationState.rebind_on_resume``), so the second
        frame is bounded by the policy the first was admitted under instead of
        falling back to the published mirror every resolver in the request can
        write. A plain ``strawberry.Schema`` has no state to register on and no
        runner to resume anything: its stream keeps upstream's behavior.
        """
        policy = self._resolved_policy()
        context = self.execution_context.context
        # The absent-vs-``None`` distinction and the put-it-back-on-exception
        # rule are ``utils/context.py``'s (``restored_context_keys``), which is
        # where the ``MISSING`` sentinel that decides "clear" from "restore"
        # lives. A sentinel minted here with a hand-rolled round trip would be
        # one ``is`` comparison away from restoring a key that was never set.
        with restored_context_keys(context, DST_RESOURCE_POLICY, DST_RESOURCE_DEADLINE):
            scope = begin_resource_budget(context, policy)
            state = self._operation_state()
            if state is not None and state.rebind_on_resume(*budget_resume_binding(scope)):
                adopt_budget_binding(scope)
            try:
                # The ARMED snapshot, not the object it was resolved from: the
                # scan and the seams that run under it must charge one policy.
                # ``cast``: the budget armed just above is what this reads back.
                scan_document_text(
                    cast("ResourcePolicy", armed_resource_policy()),
                    self.execution_context.query,
                )
                yield
            finally:
                end_resource_budget(scope)

    @override
    def on_parse(self) -> Iterator[None]:
        """Charge the document's shape and every argument value, once it is parsed.

        The admission stage, and it runs HERE because this is the first point at
        which a parsed document exists and the last one before anything else in
        the request can look at it. Validation is already work the request paid
        for: graphql-core's ``ValuesOfCorrectTypeRule`` parses every literal
        argument and every variable default through the scalar it is typed as,
        which for an ordinary custom scalar is the consumer's own
        ``parse_value``. Charging after that would leave three of the four
        places a value enters a request - inline literal, variable default, and
        a nested input object built from either - measured only once their
        conversion had already run.

        Charging at the validation hook instead would put admission INSIDE the
        chain it has to precede. Every extension's parsing hook finishes before
        any validation hook begins, so a validation extension - Strawberry's own
        ``ValidationCache`` among them - cannot be ordered ahead of this one
        whatever position the consumer gives it, and cannot run a validation
        pass over a document this stage has already refused.

        Runs inside :meth:`on_operation`'s scope, so the budget it charges
        against is the one armed there. Re-resolving the configuration at this
        hook would re-read it, and a policy object whose field reads are its own
        code can answer the second read differently from the first: the document
        would then be scanned against a bound the request never has to satisfy.
        A plain ``strawberry.Schema`` whose consumer calls this hook with no
        operation scope around it has nothing armed, and falls back to the
        configuration exactly as the arming hook would have resolved it.

        A rejection is RECORDED and PUBLISHED, and it empties the request's
        validation rules. Publishing is what every transport renders into the
        response envelope - including the streaming one, where an exception out
        of a hook would leave the operation with no frame at all - and what
        makes graphql-core's own validation stand down. Emptying the rules is
        the same statement made to anything that validates the document itself
        rather than leaving it to graphql-core: a rejected operation is not
        validated, so no scalar of the consumer's is asked to parse a value
        belonging to a request that will not run. Recording is what survives
        both, :func:`resource_policy.admission_rejection` being the package's
        own answer rather than a field the rest of the chain writes.
        """
        yield
        execution_context = self.execution_context
        document = execution_context.graphql_document
        if document is None:
            return
        policy = armed_resource_policy()
        try:
            charge_document(
                policy if policy is not None else self._resolved_policy(),
                execution_context.schema._schema,
                document,
                execution_context.variables or {},
                execution_context.operation_name,
            )
        except ResourceLimitExceeded as rejection:
            record_admission_rejection(rejection)
            execution_context.validation_rules = ()
            execution_context.pre_execution_errors = [rejection]

    @override
    def on_validate(self) -> Iterator[None]:
        """Restate a rejection an earlier validation hook's own result replaced.

        ``ExecutionContext.pre_execution_errors`` is where a rejected operation
        is published, and it is an ordinary mutable field: Strawberry's
        ``ValidationCache`` assigns its cached validation result over whatever
        is there, and an operation whose rejection was overwritten is one the
        pre-execution check waves through. That check is made INSIDE the
        validation stage rather than after it, so the last word belongs to
        whichever validation hook SET UP last - which is why this restates
        before yielding rather than after, and why it can only answer for
        entries ahead of this one. ``schema.py::DjangoSchema`` closes the rest
        by appending :class:`_AdmissionGuard` after every consumer entry; a
        plain ``strawberry.Schema`` whose consumer placed a validation cache
        after this extension has :meth:`on_execute` as the backstop instead.
        """
        restate_admission_verdict(self.execution_context)
        yield

    @override
    def on_execute(self) -> Iterator[None]:
        """Refuse to begin executing an operation the admission stage rejected.

        A rejection is a statement that nothing runs. Where a validation hook
        set up after this extension erased the published rejection - a plain
        ``strawberry.Schema`` with a later validation cache, which has no
        appended :class:`_AdmissionGuard` - the pre-execution check waves the
        operation through, and execution BEGINNING is the contradiction, so the
        refusal is restated at the hook execution starts from, which every
        upstream execution path converts into an error entry. Raising is correct
        here and wrong at the charging hook: this one is entered only when an
        operation is about to run.
        """
        rejection = admission_rejection()
        if rejection is not None:
            raise rejection
        yield


# basedpyright: package-internal, not unused: it is imported and appended by
# ``django_strawberry_framework/schema.py::_admitted_chain``
class _AdmissionGuard(SchemaExtension):  # pyright: ignore[reportUnusedClass]
    """Restate the operation's admission verdict after every consumer validation hook.

    Not a second enforcement stage: it charges nothing, arms nothing, and
    changes nothing about what any consumer entry does. It exists because
    upstream decides whether to execute from inside the validation stage, so the
    published rejection has to survive the LAST validation hook to set up, and a
    validation extension that runs the pass itself assigns its own result over
    that field. ``schema.py::DjangoSchema.get_extensions`` appends this after
    every consumer entry, which is the position that answers for all of them
    without moving any of them.
    """

    @override
    def on_validate(self) -> Iterator[None]:
        """Put the recorded verdict back, last, before the pre-execution check reads it."""
        restate_admission_verdict(self.execution_context)
        yield
