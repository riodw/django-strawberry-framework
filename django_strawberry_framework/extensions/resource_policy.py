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
2. **Document budget** (``on_validate``, before validation). One iterative,
   fragment-expanding walk over the parsed AST charges expanded selections,
   aliases, and the multiplicative collection cost. Fragment spreads are charged
   at every spread site and cycle-guarded by the spread path, so neither a
   fragment nor a directive can hide a selection from accounting.
3. **Value budget** (the same walk). Every argument's value - literal, variable,
   or a literal object with variables spliced into it - is charged against the
   input-cardinality bounds, typed by the argument's own GraphQL input type
   and, for a package-generated write input, by the bind-time field specs the
   owning mutation stashed. The specs are what classify a RELATION list: a
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
  execution begins from, so a streaming path that yields the error frame and
  then executes the operation anyway - which some releases in the supported
  range do - meets it there.
- Pass 1 is the one that still raises, because its whole job is to refuse
  before the parser runs and a published error does not stop a parse. On a
  transport whose streaming path has no conversion for an exception out of that
  hook, a subscription over the token or structural-depth bound is refused just
  as hard - nothing parses, nothing executes - but its client sees the
  operation complete without data rather than an error entry.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from graphql import (
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLError,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
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

from ..mutations.fields import MUTATION_CLASS_MARKER
from ..resource_policy import (
    DEFAULT_RESOURCE_POLICY,
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
from .operation_state import _OperationBoundExtension

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
    the cost somebody does pay unbounded. Every bound charged AFTER the parse -
    ``max_selections``, ``max_aliases``, ``max_collection_cost`` and every value
    bound - is charged against the named operation alone (:func:`charge_document`),
    which is the distinction spec-047 draws between the two halves and not a
    disagreement between them. A client sending one persisted document carrying
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


def _mutation_input_specs(field_def: Any) -> Mapping[str, Any] | None:
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
    strawberry_field = (getattr(field_def, "extensions", None) or {}).get(
        _STRAWBERRY_DEFINITION_BACKREF,
    )
    resolver = getattr(getattr(strawberry_field, "base_resolver", None), "wrapped_func", None)
    mutation_cls = getattr(resolver, MUTATION_CLASS_MARKER, None)
    specs = getattr(mutation_cls, "_input_field_specs", None)
    if not specs:
        return None
    return {spec.graphql_name: spec for spec in specs}


def _nested_specs_map(spec: Any) -> Mapping[str, Any] | None:
    """Return the field-spec map of a NESTED input's own fields, or ``None``.

    A serializer nested-serializer field records its nested rows' own reverse
    map on the enclosing field's spec (``InputFieldSpec.nested_specs``), so a
    relation list one level down - a nested ``altBranches`` raw-pk list - is
    classified by the same bind signal as a top-level one. ``None`` for every
    non-nested field, which is every field of every non-serializer flavor.
    """
    nested = getattr(spec, "nested_specs", None)
    if not nested:
        return None
    return {nested_spec.graphql_name: nested_spec for nested_spec in nested}


#: The sequence types whose ``__len__`` and iteration are the interpreter's own,
#: so a member list does not have to be built to count them honestly.
_EXACT_SEQUENCE_TYPES = (list, tuple)


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
        limit = getattr(self.policy, bound)
        if charged > limit:
            raise ResourceLimitExceeded(bound, limit, charged, detail)

    def _bounded_members(self, members: Callable[[], Any], bound: str) -> list[Any]:
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
        limit = getattr(self.policy, bound)
        collected: list[Any] = []
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
        input_type: Any,
        value: Any,
        *,
        in_mutation: bool,
        argument: str,
        specs: Mapping[str, Any] | None = None,
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
        stack: list[tuple[Any, Any, tuple[Any, ...], Any, Any]] = [
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
                if not self._charge_container(
                    node_value,
                    stack,
                    node_type,
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
                        node_type.of_type,
                        1,
                        in_mutation=in_mutation,
                        argument=argument,
                        spec=spec,
                    )
                    stack.append(
                        (
                            node_type.of_type,
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
        value: Any,
        stack: list[tuple[Any, Any, tuple[Any, ...], Any, Any]],
        node_type: Any,
        path: tuple[Any, ...],
        in_mutation: bool,
        argument: str,
        spec: Any,
        spec_map: Mapping[str, Any] | None,
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
            if _closes_a_cycle(value, path):
                return True
            if type(value) is dict:
                entries: Any = value.items()
                width = len(value)
            else:
                entries = self._bounded_members(lambda: value.items(), "max_container_width")
                width = len(entries)
            self._reject(
                "max_container_width",
                width,
                "an input object carries more fields than the policy allows",
            )
            item_type = node_type.fields if isinstance(node_type, GraphQLInputObjectType) else None
            child_path = (*path, value)
            for name, item in entries:
                field_def = item_type.get(name) if item_type is not None else None
                # Specs resolve only under a declared input object: a hostile
                # mapping parked under a scalar argument is charged, never
                # classified, and a child's own spec map comes from ITS field
                # spec's nested records (``nested_specs``), never inherited.
                field_spec = spec_map.get(name) if item_type is not None and spec_map else None
                stack.append(
                    (
                        getattr(field_def, "type", None),
                        item,
                        child_path,
                        field_spec,
                        _nested_specs_map(field_spec),
                    ),
                )
            return True
        if not isinstance(value, (list, tuple)):
            return False
        if _closes_a_cycle(value, path):
            return True
        if type(value) in _EXACT_SEQUENCE_TYPES:
            members: Any = value
            width = len(value)
        else:
            members = self._bounded_members(lambda: value, "max_container_width")
            width = len(members)
        self._reject(
            "max_container_width",
            width,
            "a list argument is wider than the policy allows",
        )
        if isinstance(node_type, GraphQLList):
            self._charge_list_family(
                node_type.of_type,
                width,
                in_mutation=in_mutation,
                argument=argument,
                spec=spec,
            )
            item_type = node_type.of_type
        else:
            item_type = None
        child_path = (*path, value)
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
        item_type: Any,
        width: int,
        *,
        in_mutation: bool,
        argument: str,
        spec: Any = None,
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

    def _charge_upload(self, value: Any) -> None:
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
    if parent_type is not None and graphql_schema.query_type is parent_type:
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

    "Integral" is the built-in type (``resource_policy.py::_is_builtin_number``),
    so a variable holding an ``int`` SUBCLASS narrows nothing. The bound this
    returns becomes a charge against ``max_collection_cost``, and a subclass
    reaching that counter answers both the ``min`` that would clamp it and the
    reflected ``__radd__`` the running total is accumulated through.
    """
    for argument in node.arguments:
        if argument.name.value not in ("first", "last"):
            continue
        value = value_from_ast_untyped(argument.value, variables)
        if type(value) is int and value >= 0:
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
    unwrapped = unwrap_non_null(field_type)
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
    unwrapped = unwrap_non_null(edges.type)
    if not isinstance(unwrapped, GraphQLList):
        return False
    edge = get_named_type(unwrapped.of_type)
    return isinstance(edge, GraphQLObjectType) and set(edge.fields) >= _EDGE_MARKER_FIELDS


def charge_document(
    policy: ResourcePolicy,
    graphql_schema: Any,
    document: Any,
    variables: Mapping[str, Any] | None = None,
    operation_name: str | None = None,
) -> None:
    """Charge one request's document shape and argument values, iteratively.

    The walk expands fragments at every spread site (so a fragment cannot hide a
    selection, and spreading one fragment ten times costs ten times) and carries
    the spread path so a cyclic fragment set terminates instead of looping.

    Every shape validation would have rejected is a shape this walk meets,
    because it runs BEFORE validation: a cyclic fragment set, a field the parent
    type does not have, a selection under a leaf, an argument the field does not
    take, a variable the operation never defined. None of them is an error here.
    A node the schema cannot type is charged for the selection it is and then
    not descended into, and a value that resolves to nothing is charged as the
    value it resolves to; what rejects such a document is validation, which runs
    next and says so in its own words.
    """
    safe_variables = variables if variables is not None else {}
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
        op_variables = dict(safe_variables)
        for var_def in operation.variable_definitions or ():
            var_name = var_def.variable.name.value
            if var_name not in op_variables and var_def.default_value is not None:
                op_variables[var_name] = value_from_ast_untyped(var_def.default_value)
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
            # A generated top-level mutation field carries its bind-time spec
            # map, which classifies the write input's fields for the whole
            # argument walk below. Resolved per field (not per request) because
            # the map belongs to THE field's mutation class; ``begin_mutation_field``
            # keeps the per-field relation counter scoped to exactly this field.
            field_specs = None
            if in_mutation and parent is root:
                values.begin_mutation_field()
                field_specs = _mutation_input_specs(field_def)
            for argument in node.arguments:
                argument_def = field_def.args.get(argument.name.value)
                if argument_def is None:
                    continue
                values.charge(
                    argument_def.type,
                    value_from_ast_untyped(argument.value, op_variables),
                    in_mutation=in_mutation,
                    argument=argument.name.value,
                    specs=field_specs,
                )
            child_multiplier = multiplier
            rows = _collection_rows(policy, parent, field_def.type, node, op_variables)
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


def restate_admission_verdict(execution_context: Any) -> None:
    """Republish this operation's admission verdict over whatever replaced it.

    One statement of what a rejected operation's pre-execution error is, applied
    at the two positions in the validation stage that can be answered for: the
    enforcing extension's own hook, and the package-appended guard behind every
    consumer entry.
    """
    rejection = admission_rejection()
    if rejection is not None:
        execution_context.pre_execution_errors = [rejection]


class DjangoResourcePolicyExtension(_OperationBoundExtension):
    """Enforce the schema's ``ResourcePolicy`` on every operation.

    Installed automatically by ``schema.py::DjangoSchema``; a consumer building a
    plain ``strawberry.Schema`` adds it explicitly and may hand it its own
    policy::

        schema = strawberry.Schema(
            Query,
            extensions=[lambda: DjangoResourcePolicyExtension(policy=ResourcePolicy(max_depth=8))],
        )

    **The entry is a factory rather than an instance, and that is the supported
    spelling for a plain ``strawberry.Schema``.** Strawberry passes an instance
    entry through unchanged, so one object answers every operation, and only a
    ``DjangoSchema`` builds the runner that gives such an object per-operation
    state (``extensions/operation_state.py``). A factory that returns a new
    extension per call - or the bare class, when no override is needed - is
    operation-local on any schema, because the instance itself is.

    Without an explicit policy the extension reads the one the schema resolved at
    construction, falling back to the package defaults for a schema that carries
    none. There is no configuration under which the extension is installed and
    enforces nothing.

    **On a ``DjangoSchema`` this is not a consumer entry at all.** The schema
    builds its own on every operation from the configuration it was accepted
    with, so an entry that IS this class, or an exact instance of it, is read
    once as a declaration of the schema's bound and does not travel into the
    chain - which is also why no resolver finds one in
    ``info.schema.extensions`` to write through. A subclass is refused at
    construction and a factory resolving to one refuses the operation: both
    would decide enforcement from consumer code on a request already running.
    Configure the bound with ``DjangoSchema(resource_policy=...)``.
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
        schema_policy = getattr(self.execution_context.schema, "resource_policy", None)
        return (
            schema_policy
            if isinstance(schema_policy, ResourcePolicy)
            else (DEFAULT_RESOURCE_POLICY)
        )

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
        # lives. This extension used to mint its own sentinel and hand-roll the
        # round trip, one ``is`` comparison away from restoring a key that was
        # never set.
        with restored_context_keys(context, DST_RESOURCE_POLICY, DST_RESOURCE_DEADLINE):
            scope = begin_resource_budget(context, policy)
            state = self._operation_state()
            if state is not None and state.rebind_on_resume(*budget_resume_binding(scope)):
                adopt_budget_binding(scope)
            try:
                # The ARMED snapshot, not the object it was resolved from: the
                # scan and the seams that run under it must charge one policy.
                scan_document_text(armed_resource_policy(), self.execution_context.query)
                yield
            finally:
                end_resource_budget(scope)

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

    def on_execute(self) -> Iterator[None]:
        """Refuse to begin executing an operation the admission stage rejected.

        A rejection is a statement that nothing runs, and on every seam that
        reads it nothing does. Where a release's streaming path yields the
        pre-execution error and then goes on to execute the operation anyway,
        execution BEGINNING is the contradiction, so the refusal is restated at
        the hook execution starts from - which is the seam that same path
        already converts into an error entry. Raising is correct here and wrong
        at the charging hook: this one is entered only when an operation is
        about to run.
        """
        rejection = admission_rejection()
        if rejection is not None:
            raise rejection
        yield


class _AdmissionGuard(SchemaExtension):
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

    def on_validate(self) -> Iterator[None]:
        """Put the recorded verdict back, last, before the pre-execution check reads it."""
        restate_admission_verdict(self.execution_context)
        yield
