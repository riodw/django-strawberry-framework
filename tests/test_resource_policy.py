"""``ResourcePolicy`` construction, narrowing, threading, and walker edge cases (spec-047).

The package tier of the resource policy: everything a live ``/graphql/`` request
cannot reach. The boundaries themselves - what a real document, a real variable
payload, and a real upload are charged - are pinned over HTTP in
``examples/fakeshop/test_query/test_resource_policy_api.py``, because that is
where they matter. What is left here is the surface a request cannot express:

- policy construction and per-bound validation, including the ``bool`` trap
  (``True`` is an ``int``) and the deadline's separate domain;
- the precedence ladder (constructor argument > setting > package default) and
  the settings-shape rejections;
- the narrowing rule, which no request can exercise because it is a
  build-time contract between a field and the schema policy;
- context threading against the frozen / dict / object context shapes, and the
  fail-closed default a missing stash produces;
- the walker's degenerate inputs - a malformed document, an unknown fragment, a
  cyclic fragment set, an operation the request did not name, an untyped
  container, an upload that cannot report its size - which a valid request
  cannot produce but a hostile or unusual one can;
- the value walker's IDENTITY contracts, which need constructed object graphs a
  JSON body cannot express: a container referenced twice charged twice, two
  distinct-but-equal containers both charged, and cycles closing onto a parent
  and onto a grandparent through both container families; and
- the connection SHAPE test from both sides, against probe types that borrow the
  ``edges`` name without the edge shape - which the example schema, having only
  real connections, cannot supply.
"""

from __future__ import annotations

import time
from types import MappingProxyType, SimpleNamespace
from typing import Any

import pytest
import strawberry
from graphql import GraphQLError, parse

from django_strawberry_framework import Upload
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions.resource_policy import (
    DjangoResourcePolicyExtension,
    charge_document,
    scan_document_text,
)
from django_strawberry_framework.resource_policy import (
    DEFAULT_RESOURCE_POLICY,
    DST_RESOURCE_DEADLINE,
    DST_RESOURCE_POLICY,
    ResourceLimitExceeded,
    ResourcePolicy,
    bounded_rows,
    check_deadline,
    clear_resource_context,
    effective_bound,
    policy_from_info,
    resolve_resource_policy,
    stash_resource_policy,
    validate_collection_bound,
)
from django_strawberry_framework.schema import _with_resource_policy_extension

# ---------------------------------------------------------------------------
# Construction and validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
        "5",
        1.5,
        None,
        True,
    ],
    ids=[
        "zero",
        "negative",
        "string",
        "float",
        "none",
        "bool",
    ],
)
def test_a_non_positive_integer_bound_is_rejected_at_construction(value):
    """``True`` is in this list on purpose: ``isinstance(True, int)`` is ``True``.

    A bound accepting ``True`` would silently become ``1``, which is a bound so
    tight it looks like a different bug entirely.
    """
    with pytest.raises(ConfigurationError, match="max_page_size must be a positive integer"):
        ResourcePolicy(max_page_size=value)


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
        "5",
        True,
    ],
    ids=[
        "zero",
        "negative",
        "string",
        "bool",
    ],
)
def test_an_invalid_execution_deadline_is_rejected(value):
    with pytest.raises(ConfigurationError, match="execution_deadline_seconds"):
        ResourcePolicy(execution_deadline_seconds=value)


@pytest.mark.parametrize("value", [None, 1, 0.5])
def test_a_valid_execution_deadline_is_accepted(value):
    """The deadline is the one optional bound, and it accepts a float."""
    assert ResourcePolicy(execution_deadline_seconds=value).execution_deadline_seconds == value


def test_the_package_default_policy_is_bounded_on_every_axis():
    """The fail-closed claim, asserted rather than assumed.

    There is no spelling of a bound that disables it, so the default policy must
    carry a positive integer on every axis except the deadline.
    """
    for name, value in vars(DEFAULT_RESOURCE_POLICY).items():
        if name == "execution_deadline_seconds":
            assert value is None
            continue
        assert isinstance(value, int) and value >= 1, name


def test_a_policy_is_frozen():
    with pytest.raises(Exception, match="cannot assign to field"):
        DEFAULT_RESOURCE_POLICY.max_page_size = 1


# ---------------------------------------------------------------------------
# The precedence ladder
# ---------------------------------------------------------------------------


def test_an_explicit_policy_instance_is_used_as_is():
    policy = ResourcePolicy(max_depth=3)
    assert resolve_resource_policy(policy) is policy


def test_an_explicit_mapping_is_applied_over_the_package_defaults():
    policy = resolve_resource_policy({"max_depth": 3})
    assert policy.max_depth == 3
    assert policy.max_page_size == DEFAULT_RESOURCE_POLICY.max_page_size


def test_no_source_at_all_resolves_to_the_package_defaults():
    assert resolve_resource_policy(None) is DEFAULT_RESOURCE_POLICY


def test_the_setting_supplies_the_policy_when_no_argument_does(settings):
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RESOURCE_POLICY": {"max_depth": 4}}
    assert resolve_resource_policy(None).max_depth == 4


def test_an_explicit_argument_outranks_the_setting(settings):
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RESOURCE_POLICY": {"max_depth": 4}}
    assert resolve_resource_policy({"max_depth": 9}).max_depth == 9


def test_a_non_mapping_policy_setting_is_rejected(settings):
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RESOURCE_POLICY": 12}
    with pytest.raises(ConfigurationError, match="must be a ResourcePolicy or a mapping"):
        resolve_resource_policy(None)


def test_an_unknown_bound_name_is_rejected_with_the_valid_vocabulary():
    """Naming the valid bounds in the message is what makes a typo self-correcting."""
    with pytest.raises(ConfigurationError, match="Unknown resource-policy bound\\(s\\): max_deth"):
        resolve_resource_policy({"max_deth": 3})


# ---------------------------------------------------------------------------
# The narrowing rule
# ---------------------------------------------------------------------------


def test_narrowing_a_bound_returns_a_tighter_policy():
    assert DEFAULT_RESOURCE_POLICY.narrowed(max_page_size=5).max_page_size == 5


def test_widening_a_bound_is_refused():
    with pytest.raises(ConfigurationError, match="may only be narrowed"):
        DEFAULT_RESOURCE_POLICY.narrowed(max_page_size=10_000)


def test_narrowing_an_unknown_bound_is_refused():
    with pytest.raises(ConfigurationError, match="no bound named 'nope'"):
        DEFAULT_RESOURCE_POLICY.narrowed(nope=1)


def test_a_deadline_narrows_from_absent_to_present_but_never_back():
    """``None`` means "no deadline", so restoring it is the widest move there is."""
    with_deadline = DEFAULT_RESOURCE_POLICY.narrowed(execution_deadline_seconds=5)
    assert with_deadline.execution_deadline_seconds == 5
    assert with_deadline.narrowed(execution_deadline_seconds=2).execution_deadline_seconds == 2
    with pytest.raises(ConfigurationError, match="may only be narrowed"):
        with_deadline.narrowed(execution_deadline_seconds=None)
    with pytest.raises(ConfigurationError, match="may only be narrowed"):
        with_deadline.narrowed(execution_deadline_seconds=6)


def test_effective_bound_takes_the_tighter_of_the_two_unless_trusted():
    assert effective_bound(100, None) == 100
    assert effective_bound(100, 5) == 5
    assert effective_bound(5, 100) == 5
    assert effective_bound(5, 100, trusted=True) == 100


@pytest.mark.parametrize(
    "value",
    [
        0,
        -3,
        True,
        "9",
    ],
)
def test_a_field_declared_collection_bound_must_be_a_positive_integer(value):
    with pytest.raises(ConfigurationError, match="probe max_rows must be a positive integer"):
        validate_collection_bound(value, field="probe max_rows")


# ---------------------------------------------------------------------------
# Context threading
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "context_factory",
    [SimpleNamespace, dict, lambda: MappingProxyType({})],
    ids=["object", "dict", "frozen"],
)
def test_the_policy_round_trips_or_fails_closed_on_every_context_shape(context_factory):
    """A frozen context cannot hold the stash, and still gets a BOUNDED policy.

    That is the whole point of the fail-closed miss path: an unwritable context
    degrades to the package defaults, never to "no policy".
    """
    context = context_factory()
    policy = ResourcePolicy(max_depth=3)
    stash_resource_policy(context, policy)
    read = policy_from_info(SimpleNamespace(context=context))
    assert read is policy or read is DEFAULT_RESOURCE_POLICY


def test_clearing_the_context_restores_the_default_policy():
    context = SimpleNamespace()
    stash_resource_policy(context, ResourcePolicy(max_depth=3))
    clear_resource_context(context)
    assert policy_from_info(SimpleNamespace(context=context)) is DEFAULT_RESOURCE_POLICY
    assert not hasattr(context, DST_RESOURCE_POLICY)
    assert not hasattr(context, DST_RESOURCE_DEADLINE)


def test_a_non_policy_value_under_the_key_is_ignored():
    """A consumer key collision must not become "the request has no bounds"."""
    context = {DST_RESOURCE_POLICY: "not a policy"}
    assert policy_from_info(SimpleNamespace(context=context)) is DEFAULT_RESOURCE_POLICY


# ---------------------------------------------------------------------------
# The cooperative deadline
# ---------------------------------------------------------------------------


def test_no_stashed_deadline_leaves_the_request_running():
    check_deadline(SimpleNamespace(context={}))


def test_a_non_numeric_stashed_deadline_leaves_the_request_running():
    check_deadline(SimpleNamespace(context={DST_RESOURCE_DEADLINE: True}))


def test_a_future_deadline_leaves_the_request_running():
    context = {}
    stash_resource_policy(context, ResourcePolicy(execution_deadline_seconds=60))
    check_deadline(SimpleNamespace(context=context))


def test_a_passed_deadline_reports_the_configured_seconds_not_the_clock():
    """``limit`` is the bound the deployment configured, never a monotonic timestamp.

    The elapsed time and the absolute deadline are process-internal timings a
    client can neither verify nor act on, and a wire field named ``limit``
    carrying a monotonic clock reading reads as a bound nobody configured.
    """
    context = {}
    stash_resource_policy(context, ResourcePolicy(execution_deadline_seconds=2.5))
    context[DST_RESOURCE_DEADLINE] = time.monotonic() - 1
    with pytest.raises(ResourceLimitExceeded) as caught:
        check_deadline(SimpleNamespace(context=context))
    assert caught.value.bound == "execution_deadline_seconds"
    assert caught.value.limit == 3
    assert caught.value.charged == 4
    assert "2.5 seconds" in caught.value.message


def test_a_passed_deadline_with_no_policy_behind_it_still_rejects():
    """A hand-written deadline key has no configured budget to report - and still rejects.

    Fail-closed: the deadline HAS passed, so the answer is a rejection whose
    budget is stated as unknown rather than a number the deployment never chose.
    """
    context = {DST_RESOURCE_DEADLINE: time.monotonic() - 1}
    with pytest.raises(ResourceLimitExceeded) as caught:
        check_deadline(SimpleNamespace(context=context))
    assert caught.value.limit == 0
    assert "unknown" in caught.value.message


# ---------------------------------------------------------------------------
# ``bounded_rows``
# ---------------------------------------------------------------------------


def test_bounded_rows_slices_a_sequence_to_the_policy_bound():
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    assert bounded_rows(list(range(10)), info) == [0, 1]


def test_bounded_rows_bounds_a_non_subscriptable_iterable():
    """The unsliceable shape must still be bounded, not waved through."""
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))

    class _Rows:
        def __iter__(self):
            return iter(range(10))

    assert bounded_rows(_Rows(), info) == [0, 1]


def test_bounded_rows_honours_a_trusted_widening():
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    assert bounded_rows(list(range(10)), info, 4, trusted=True) == [
        0,
        1,
        2,
        3,
    ]


# ---------------------------------------------------------------------------
# The pre-parse text scan
# ---------------------------------------------------------------------------


def test_an_absent_document_charges_nothing():
    scan_document_text(DEFAULT_RESOURCE_POLICY, None)
    scan_document_text(DEFAULT_RESOURCE_POLICY, "")


def test_a_malformed_document_is_left_to_the_real_parser():
    """Swallowing the lexer error keeps the accurate syntax diagnostic."""
    scan_document_text(DEFAULT_RESOURCE_POLICY, "{ foo(bar: 'single quotes') }")


def test_a_document_that_is_both_oversized_and_malformed_is_rejected_on_size():
    """Size is charged per token, so it fires before the lexer reaches the garbage."""
    policy = ResourcePolicy(max_document_tokens=3)
    with pytest.raises(ResourceLimitExceeded) as caught:
        scan_document_text(policy, "{ a b c d e 'garbage' }")
    assert caught.value.bound == "max_document_tokens"


# ---------------------------------------------------------------------------
# Walker degenerate inputs
# ---------------------------------------------------------------------------


@strawberry.type
class _NotAConnection:
    """A type that exposes a field called ``edges`` and is not connection-shaped.

    No ``node`` / ``cursor`` edge type behind it, so the collection-cost
    exemption a real connection's ``edges`` earns must not apply to this list.
    """

    edges: list[str]


@strawberry.type
class _ScalarEdges:
    """``edges`` that is not even a list - the other half of the shape test."""

    edges: str


@strawberry.type
class _Probe:
    """A minimal schema whose only job is to give the walker real types."""

    fauxes: list[_NotAConnection]
    scalar_edges: _ScalarEdges

    @strawberry.field
    def echo(self, text: str = "x", tags: list[str] | None = None) -> str:
        return text

    @strawberry.field
    def blob(self, payload: strawberry.scalars.JSON = None) -> str:
        return "ok"

    @strawberry.field
    def stash(self, document: Upload) -> str:
        return "ok"


_PROBE_SCHEMA = strawberry.Schema(query=_Probe)


def _charge(
    document,
    variables=None,
    operation_name=None,
    policy=None,
):
    charge_document(
        policy or DEFAULT_RESOURCE_POLICY,
        _PROBE_SCHEMA._schema,
        parse(document),
        variables or {},
        operation_name,
    )


def test_only_the_named_operation_is_charged():
    """A document carrying several operations charges the one the request named."""
    document = "query A { echo } query B { echo }"
    _charge(document, operation_name="A")
    with pytest.raises(ResourceLimitExceeded):
        _charge(document, operation_name=None, policy=ResourcePolicy(max_selections=1))


def test_an_operation_kind_the_schema_does_not_define_is_skipped():
    """A mutation against a query-only schema has no root type to walk."""
    _charge("mutation { echo }")


def test_an_unknown_fragment_spread_is_skipped():
    _charge("{ ...Missing }")


def test_a_cyclic_fragment_set_terminates():
    """Validation rejects a fragment cycle; the walker must not depend on that.

    A schema that disabled validation would hand this document straight to the
    walk, and a walk that followed the cycle would never return.
    """
    _charge("{ ...A } fragment A on Query { ...B } fragment B on Query { ...A }")


def test_an_inline_fragment_without_a_type_condition_keeps_its_parent():
    _charge("{ ... { echo } }")


def test_an_inline_fragment_names_its_own_type_condition():
    _charge("{ ... on Query { echo } }")


def test_an_unknown_argument_is_skipped():
    """Validation would reject it; the walker charges only arguments it can type."""
    _charge('{ echo(nope: "x") }')


def test_typename_and_introspection_fields_carry_no_field_definition():
    _charge("{ __typename __schema { queryType { name } } }")


def test_an_untyped_container_inside_a_scalar_is_still_charged():
    """A JSON-shaped scalar's contents are nodes too, or they are a free payload."""
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query B($p: JSON!) { blob(payload: $p) }",
            {"p": {"a": [1, 2, 3], "b": {"c": 4}}},
            policy=ResourcePolicy(max_input_nodes=3),
        )
    assert caught.value.bound == "max_input_nodes"


def test_a_scalar_where_a_list_is_declared_is_charged_as_one_item():
    """GraphQL coerces a bare value into a single-item list; the charge follows."""
    _charge("query T($t: [String!]) { echo(tags: $t) }", {"t": "solo"})


def test_a_container_referenced_twice_is_charged_per_reference():
    """A charge fires per REFERENCE; only a cycle back onto an ancestor is skipped.

    Two references to one list are two lists' worth of work for the coercer, the
    walkers, and the ORM. The shape this pins is the one a request can actually
    build over the wire: one variable spliced into two arguments resolves to the
    same Python object both times.

    ``{"one": shared, "two": shared}`` is 7 nodes charged per reference (the
    mapping, then 1 + 2 for each of the two list references) and would be 5 if
    the second reference were skipped, so a 6-node budget separates the two
    contracts.
    """
    shared = ["a", "b"]
    payload = {"one": shared, "two": shared}
    document = "query B($p: JSON!) { blob(payload: $p) }"
    _charge(document, {"p": payload}, policy=ResourcePolicy(max_input_nodes=7))
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(document, {"p": payload}, policy=ResourcePolicy(max_input_nodes=6))
    assert caught.value.bound == "max_input_nodes"


def test_a_self_referential_value_terminates():
    payload: dict = {}
    payload["self"] = payload
    _charge("query B($p: JSON!) { blob(payload: $p) }", {"p": payload})


def test_a_self_referential_list_terminates():
    """Both container families are cycle-guarded, not only mappings."""
    payload: list = []
    payload.append(payload)
    _charge("query B($p: JSON!) { blob(payload: $p) }", {"p": payload})


def test_a_cycle_deeper_than_its_own_container_terminates():
    """The guard is the whole ancestor PATH, not just the immediate parent."""
    outer: dict = {"inner": {}}
    outer["inner"]["back"] = outer
    _charge("query B($p: JSON!) { blob(payload: $p) }", {"p": outer})


def test_two_distinct_but_equal_containers_are_both_charged():
    """Identity is by ``is``: equality is arbitrary consumer code, not a cycle."""
    payload = {"one": ["a"], "two": ["a"]}
    with pytest.raises(ResourceLimitExceeded):
        _charge(
            "query B($p: JSON!) { blob(payload: $p) }",
            {"p": payload},
            policy=ResourcePolicy(max_input_nodes=4),
        )


def test_a_deeply_nested_variable_value_is_bounded_by_value_depth():
    """The bound the pre-parse depth scan cannot supply.

    ``max_depth`` counts brackets in the document TEXT, and a variable payload
    has none: this document is three brackets deep however deep its value is.
    """
    payload: Any = "leaf"
    for _ in range(8):
        payload = [payload]
    document = "query B($p: JSON!) { blob(payload: $p) }"
    _charge(document, {"p": payload}, policy=ResourcePolicy(max_value_depth=8))
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(document, {"p": payload}, policy=ResourcePolicy(max_value_depth=4))
    assert caught.value.bound == "max_value_depth"
    assert caught.value.limit == 4


def test_introspection_selections_are_charged_like_any_other():
    """``__schema`` / ``__type`` / ``__typename`` resolve to their meta-field definitions.

    Answering ``None`` for them charged the whole of introspection as one
    selection and then stopped descending, which made introspection the one
    document shape no depth, selection, or collection bound could see.
    """
    _charge("{ __typename __schema { queryType { name } } }")
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "{ __typename __schema { queryType { name } } }",
            policy=ResourcePolicy(max_selections=3),
        )
    assert caught.value.bound == "max_selections"


def test_an_introspection_meta_field_argument_is_charged():
    """``__type(name: ...)`` carries a real typed argument, so its value is charged."""
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge('{ __type(name: "Query") { name } }', policy=ResourcePolicy(max_scalar_bytes=4))
    assert caught.value.bound == "max_scalar_bytes"


def test_a_type_that_merely_has_an_edges_field_is_not_a_connection():
    """The connection exemption makes a list FREE, so it must match the edge shape.

    A connection's own ``edges`` is exempt from collection cost because the
    connection field above it already charged the page. Granting that exemption
    on the field NAME alone hands a free unbounded list to any type that happens
    to expose one called ``edges``: a list of such types charges 100 for the
    outer list and then multiplies it by the inner list's own 100, which is the
    10,100 asserted here and would be a bare 100 if the exemption applied.
    """
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge("{ fauxes { edges } }", policy=ResourcePolicy(max_collection_cost=5_000))
    assert caught.value.bound == "max_collection_cost"
    assert caught.value.charged == 10_100


def test_a_type_whose_edges_field_is_not_a_list_is_not_a_connection():
    """A connection charges a full page; a type that merely borrowed the name must not.

    Charged as a connection, ``scalarEdges`` would cost a whole page against the
    collection budget for selecting one string.
    """
    _charge("{ scalarEdges { edges } }", policy=ResourcePolicy(max_collection_cost=50))


# ---------------------------------------------------------------------------
# The extension's own wiring
# ---------------------------------------------------------------------------


def test_an_explicit_policy_outranks_the_schemas():
    extension = DjangoResourcePolicyExtension(policy=ResourcePolicy(max_depth=2))
    extension.execution_context = SimpleNamespace(schema=SimpleNamespace(resource_policy=None))
    assert extension._resolved_policy().max_depth == 2


def test_a_schema_without_a_policy_falls_back_to_the_package_defaults():
    """A plain ``strawberry.Schema`` carries no ``resource_policy`` attribute."""
    extension = DjangoResourcePolicyExtension()
    extension.execution_context = SimpleNamespace(schema=SimpleNamespace())
    assert extension._resolved_policy() is DEFAULT_RESOURCE_POLICY


def test_an_operation_with_no_parsed_document_charges_no_document_budget():
    """``on_execute`` runs even when the parse produced nothing to walk."""
    extension = DjangoResourcePolicyExtension()
    extension.execution_context = SimpleNamespace(
        schema=SimpleNamespace(),
        graphql_document=None,
        variables=None,
        operation_name=None,
    )
    hook = extension.on_execute()
    next(hook)
    with pytest.raises(StopIteration):
        next(hook)


def test_the_context_is_cleared_even_when_the_document_scan_rejects():
    """A rejection must not leave a policy (or a deadline) on a reused context."""
    extension = DjangoResourcePolicyExtension(policy=ResourcePolicy(max_document_tokens=1))
    context = {}
    extension.execution_context = SimpleNamespace(
        schema=SimpleNamespace(),
        context=context,
        query="{ a b c }",
    )
    with pytest.raises(ResourceLimitExceeded):
        next(extension.on_operation())
    assert DST_RESOURCE_POLICY not in context


@pytest.mark.parametrize(
    "supplied",
    [DjangoResourcePolicyExtension, DjangoResourcePolicyExtension()],
    ids=["class", "instance"],
)
def test_a_consumer_supplied_extension_suppresses_the_automatic_one(supplied):
    """Two copies would charge every bound twice against the same budget."""
    assert _with_resource_policy_extension([supplied]) == [supplied]


def test_the_extension_is_appended_as_a_class_when_absent():
    """A class (not an instance) is what gives each request its own charge counters."""
    assert _with_resource_policy_extension(None) == [DjangoResourcePolicyExtension]


def test_an_unrelated_extension_is_preserved_alongside_the_appended_one():
    marker = object()
    assert _with_resource_policy_extension([marker]) == [marker, DjangoResourcePolicyExtension]


def test_a_resource_rejection_is_catchable_as_a_graphql_error():
    """The wire identity: one ``GraphQLError`` needing no per-transport translation."""
    error = ResourceLimitExceeded("max_depth", 1, 2, "detail")
    assert isinstance(error, GraphQLError)
    assert error.extensions["code"] == "RESOURCE_LIMIT_EXCEEDED"


def test_a_selection_under_a_leaf_field_has_no_field_definition_to_charge():
    """Validation rejects it; a walk that ran before validation must not crash on it.

    ``echo`` returns ``String``, so its "children" have a scalar parent - which is
    not a composite type and therefore holds no field definitions.
    """
    _charge("{ echo { nope } }")


def test_an_upload_that_cannot_report_its_size_is_rejected():
    """Guard the ANSWER, not one spelling of the missing input.

    An unmeasurable file charged as zero bytes would be an unbounded upload that
    every byte bound reports as free - the fail-open shape this bound exists to
    avoid. ``None``, a non-integer, a negative, and ``True`` are all "not a size".
    """
    for size in (
        None,
        "12",
        -1,
        True,
    ):
        with pytest.raises(ResourceLimitExceeded) as caught:
            _charge(
                "query U($f: Upload!) { stash(document: $f) }",
                {"f": SimpleNamespace(size=size)},
            )
        assert caught.value.bound == "max_upload_file_bytes"


def test_a_measurable_upload_is_charged_its_bytes():
    _charge("query U($f: Upload!) { stash(document: $f) }", {"f": SimpleNamespace(size=10)})
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query U($f: Upload!) { stash(document: $f) }",
            {"f": SimpleNamespace(size=10)},
            policy=ResourcePolicy(max_upload_file_bytes=9),
        )
    assert caught.value.charged == 10
