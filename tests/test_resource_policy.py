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
- the walker's degenerate inputs - an unknown fragment, a cyclic fragment set,
  an operation the request did not name, an untyped container, an upload that
  cannot report its size - which a valid request cannot produce but a hostile or
  unusual one can (a malformed document IS expressible over the wire, so the
  swallow-the-lexer-error pair lives in the live suite);
- the value walker's IDENTITY contracts, which need constructed object graphs a
  JSON body cannot express: a container referenced twice charged twice, two
  distinct-but-equal containers both charged, and cycles closing onto a parent
  and onto a grandparent through both container families;
- the connection SHAPE test from both sides, against probe types that borrow the
  ``edges`` name without the edge shape - which the example schema, having only
  real connections, cannot supply; and
- the ID-scalar FALLBACK half of the relation-list classification, which a
  mutation the package did not generate (no bind specs) rides - the example
  schema's writes are all package-generated, so their spec-keyed twins are
  pinned live.
"""

from __future__ import annotations

import asyncio
import contextlib
import copy
import math
import pickle
import time
from collections.abc import AsyncGenerator
from types import MappingProxyType, SimpleNamespace
from typing import Any

import pytest
import strawberry
from graphql import GraphQLError, parse
from graphql.language.token_kind import TokenKind
from strawberry.extensions import ValidationCache
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.types import Info

from django_strawberry_framework import DjangoSchema, Upload
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions.resource_policy import (
    _CLOSE_TOKEN_KINDS,
    _OPEN_TOKEN_KINDS,
    _STRUCTURAL_DELIMITER_PAIRS,
    DjangoResourcePolicyExtension,
    _AdmissionGuard,
    charge_document,
    scan_document_text,
)
from django_strawberry_framework.resource_policy import (
    DEFAULT_RESOURCE_POLICY,
    DST_RESOURCE_DEADLINE,
    DST_RESOURCE_POLICY,
    MAX_RESOURCE_BOUND,
    ResourceLimitExceeded,
    ResourcePolicy,
    _cleanup_rejected_async_iterable,
    _windowed_rows,
    _windowed_rows_async,
    admission_rejection,
    begin_resource_budget,
    bounded_rows,
    bounded_rows_async,
    check_deadline,
    clear_resource_context,
    effective_bound,
    end_resource_budget,
    policy_from_info,
    record_admission_rejection,
    resolve_resource_policy,
    stash_resource_policy,
    validate_collection_bound,
    validate_trusted_flag,
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
        math.inf,
        math.nan,
        10**400,
    ],
    ids=[
        "zero",
        "negative",
        "string",
        "bool",
        "infinity",
        "nan",
        "oversized-integer",
    ],
)
def test_an_invalid_execution_deadline_is_rejected(value):
    with pytest.raises(ConfigurationError, match="execution_deadline_seconds"):
        ResourcePolicy(execution_deadline_seconds=value)


@pytest.mark.parametrize("value", [None, 1, 0.5])
def test_a_valid_execution_deadline_is_accepted(value):
    """The deadline is the one optional bound, and it accepts a float.

    The positive control for ``_is_valid_deadline``: without it the rejection
    tests above would still pass if the domain check refused everything.
    """
    assert ResourcePolicy(execution_deadline_seconds=value).execution_deadline_seconds == value


def test_a_hostile_numeric_deadline_subclass_is_typed_rejected():
    """A deployment-supplied numeric SUBCLASS whose comparison raises is a hostile
    configuration object: the domain check cannot classify it, so the answer is
    the typed ``ConfigurationError``, never the raw arithmetic error leaking out
    of schema construction.
    """

    class HostileFloat(float):
        def __gt__(self, other):
            raise RuntimeError("hostile __gt__ detonated")

    with pytest.raises(ConfigurationError, match="execution_deadline_seconds"):
        ResourcePolicy(execution_deadline_seconds=HostileFloat(1.0))


def test_a_huge_int_deadline_overflows_the_finite_check_into_the_typed_rejection():
    """``isfinite(float(10**600))`` overflows; the rejection must stay typed."""
    with pytest.raises(ConfigurationError, match="execution_deadline_seconds"):
        ResourcePolicy(execution_deadline_seconds=10**600)


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


def test_a_bound_at_the_representable_maximum_is_accepted_and_can_reject():
    """The largest accepted bound must still reach SQL and render its own rejection.

    A ceiling is only real if the configuration at it works end to end, so this
    row builds the policy AND renders the typed rejection the bound drives -
    which is where an over-large value fails, inside CPython's integer-to-string
    conversion limit, rather than at construction.
    """
    policy = ResourcePolicy(max_list_rows=MAX_RESOURCE_BOUND)
    assert policy.max_list_rows == MAX_RESOURCE_BOUND
    rejection = ResourceLimitExceeded(
        "max_list_rows",
        policy.max_list_rows,
        policy.max_list_rows + 1,
        "detail",
    )
    assert str(MAX_RESOURCE_BOUND) in rejection.message
    assert rejection.extensions["limit"] == MAX_RESOURCE_BOUND


@pytest.mark.parametrize(
    "value",
    [MAX_RESOURCE_BOUND + 1, 10**10000],
    ids=["one-past-the-maximum", "unrenderable-magnitude"],
)
def test_a_bound_past_the_representable_maximum_is_rejected_at_construction(value):
    """A bound no query and no rejection can carry fails the deployment at startup.

    ``10**10000`` is the shape that made this a defect rather than a curiosity:
    it passes a "positive integer" test, then the first request over the bound
    raises a bare ``ValueError`` out of the constructor of the typed error the
    deployment configured the bound to produce.
    """
    with pytest.raises(ConfigurationError, match="must be at most"):
        ResourcePolicy(max_list_rows=value)


def test_a_field_declared_collection_bound_shares_the_representable_maximum():
    """The two spellings of one bound domain reject the same magnitudes."""
    validate_collection_bound(MAX_RESOURCE_BOUND, field="max_rows")
    with pytest.raises(ConfigurationError, match="must be at most"):
        validate_collection_bound(MAX_RESOURCE_BOUND + 1, field="max_rows")


# ---------------------------------------------------------------------------
# The precedence ladder
# ---------------------------------------------------------------------------


def test_an_explicit_policy_instance_is_taken_as_a_private_duplicate():
    """The argument supplies values; the object every bound is read from is the package's."""
    policy = ResourcePolicy(max_depth=3)
    resolved = resolve_resource_policy(policy)
    assert resolved == policy
    assert resolved is not policy


def test_an_explicit_mapping_is_applied_over_the_package_defaults():
    policy = resolve_resource_policy({"max_depth": 3})
    assert policy.max_depth == 3
    assert policy.max_page_size == DEFAULT_RESOURCE_POLICY.max_page_size


def test_no_source_at_all_resolves_to_the_package_defaults():
    assert resolve_resource_policy(None) is DEFAULT_RESOURCE_POLICY


def test_an_instance_through_the_setting_slot_resolves_on_the_same_terms(settings):
    """The setting slot and the explicit argument are one ladder with two spellings.

    A ``ResourcePolicy`` behind ``RESOURCE_POLICY`` is the same declaration the
    ``DjangoSchema(resource_policy=...)`` argument accepts, so it is admitted -
    and, being admitted, it is duplicated rather than enforced in place: a
    module-level settings object outlives every schema built from it. (Probed by
    the hunt: rejecting it here produced a typed message naming
    ``ResourcePolicy`` as the received type while claiming the value must be a
    ``ResourcePolicy``.)
    """
    policy = ResourcePolicy(max_depth=3)
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RESOURCE_POLICY": policy}
    resolved = resolve_resource_policy(None)
    assert resolved == policy
    assert resolved is not policy


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


def test_a_non_mapping_policy_argument_is_rejected():
    with pytest.raises(ConfigurationError, match="must be a ResourcePolicy or a mapping"):
        resolve_resource_policy(12)  # type: ignore[arg-type]


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


def test_narrowing_validates_override_domains_before_comparing_them():
    """An invalid override is a configuration error, not a comparison ``TypeError``."""
    with pytest.raises(ConfigurationError, match="max_page_size must be a positive integer"):
        DEFAULT_RESOURCE_POLICY.narrowed(max_page_size="five")


def test_effective_bound_takes_the_tighter_of_the_two_unless_trusted():
    assert effective_bound(100, None) == 100
    assert effective_bound(100, 5) == 5
    assert effective_bound(5, 100) == 5
    assert effective_bound(5, 100, trusted=True) == 100


@pytest.mark.parametrize(
    "trusted",
    [
        "false",
        "True",
        1,
        [0],
        object(),
    ],
)
def test_only_the_literal_true_widens_a_declared_bound_past_the_request_policy(trusted):
    """A merely TRUTHY opt-in narrows like every other caller.

    This is the one primitive whose answer may exceed the request's own
    ``ResourcePolicy``, so the value that reaches the widening branch is exactly
    ``True``. A misspelled flag - the string ``"false"``, a stray ``1``, any
    object with a truthy ``__bool__`` - takes the narrowing branch instead of
    silently raising every request's row ceiling.
    """
    assert effective_bound(5, 100, trusted=trusted) == 5


@pytest.mark.parametrize(
    "trusted",
    [
        0,
        "",
        None,
        [],
    ],
)
def test_a_falsy_non_bool_opt_in_also_narrows(trusted):
    """The narrowing answer is the same for every non-``True`` value, truthy or not."""
    assert effective_bound(5, 100, trusted=trusted) == 5


@pytest.mark.parametrize(
    "value",
    [
        "false",
        "True",
        1,
        0,
        None,
        [],
    ],
)
def test_a_trusted_flag_must_be_exactly_true_or_false(value):
    with pytest.raises(
        ConfigurationError,
        match="probe trusted_max_rows must be exactly True or False",
    ):
        validate_trusted_flag(value, field="probe trusted_max_rows")


@pytest.mark.parametrize("value", [True, False])
def test_an_exact_boolean_trusted_flag_is_accepted(value):
    assert validate_trusted_flag(value, field="probe trusted_max_rows") is None


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
    assert read in (policy, DEFAULT_RESOURCE_POLICY)


def test_clearing_the_context_restores_the_default_policy():
    context = SimpleNamespace()
    stash_resource_policy(context, ResourcePolicy(max_depth=3))
    clear_resource_context(context)
    assert policy_from_info(SimpleNamespace(context=context)) == DEFAULT_RESOURCE_POLICY
    assert not hasattr(context, DST_RESOURCE_POLICY)
    assert not hasattr(context, DST_RESOURCE_DEADLINE)


def test_a_non_policy_value_under_the_key_is_ignored():
    """A consumer key collision must not become "the request has no bounds"."""
    context = {DST_RESOURCE_POLICY: "not a policy"}
    assert policy_from_info(SimpleNamespace(context=context)) == DEFAULT_RESOURCE_POLICY


def test_nested_sync_schema_restores_the_outer_policy_and_deadline():
    """An inner schema must not widen later outer collection work."""

    @strawberry.type
    class InnerQuery:
        @strawberry.field
        def ping(self) -> str:
            return "pong"

    @strawberry.type
    class OuterQuery:
        @strawberry.field
        def nested(self, info: Info) -> str:
            before = policy_from_info(info)
            inner = DjangoSchema(query=InnerQuery)
            inner_result = inner.execute_sync("{ ping }", context_value=info.context)
            after = policy_from_info(info)
            rows = bounded_rows(list(range(10)), info)
            return (
                f"{before.max_list_rows}:{after.max_list_rows}:{len(rows)}:"
                f"{before.execution_deadline_seconds}:{after.execution_deadline_seconds}:"
                f"{inner_result.errors}"
            )

    schema = DjangoSchema(
        query=OuterQuery,
        resource_policy=ResourcePolicy(max_list_rows=1, execution_deadline_seconds=60),
    )
    result = schema.execute_sync("{ nested }", context_value={})

    assert result.errors is None, result.errors
    assert result.data["nested"] == "1:1:1:60:60:None"


async def test_nested_async_schema_restores_the_outer_policy_and_deadline():
    """The same context restoration contract holds across awaited inner execution."""

    @strawberry.type
    class InnerQuery:
        @strawberry.field
        async def ping(self) -> str:
            return "pong"

    @strawberry.type
    class OuterQuery:
        @strawberry.field
        async def nested(self, info: Info) -> str:
            before = policy_from_info(info)
            inner = DjangoSchema(query=InnerQuery)
            inner_result = await inner.execute("{ ping }", context_value=info.context)
            after = policy_from_info(info)
            rows = bounded_rows(list(range(10)), info)
            return (
                f"{before.max_list_rows}:{after.max_list_rows}:{len(rows)}:"
                f"{before.execution_deadline_seconds}:{after.execution_deadline_seconds}:"
                f"{inner_result.errors}"
            )

    schema = DjangoSchema(
        query=OuterQuery,
        resource_policy=ResourcePolicy(max_list_rows=1, execution_deadline_seconds=60),
    )
    result = await schema.execute("{ nested }", context_value={})

    assert result.errors is None, result.errors
    assert result.data["nested"] == "1:1:1:60:60:None"


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


def test_a_numeric_subclass_deadline_fails_closed_instead_of_being_asked():
    """A numeric SUBCLASS cannot certify a budget, so it is never asked to.

    The deadline stash is a process-internal derived value, but the context is
    consumer-owned, so a numeric subclass can sit under the key - one whose
    every comparison is consumer code, and which a seam that asked it would
    either believe or crash on. It is outside the deadline domain, and a value
    the seam cannot place on the clock fails closed on the same typed path a
    passed deadline takes.
    """

    class HostileFloat(float):
        def __gt__(self, other):
            raise RuntimeError("hostile __gt__")

        def __lt__(self, other):
            raise RuntimeError("hostile __lt__")

        def __le__(self, other):
            # ``monotonic >= stash`` dispatches to the REFLECTED ``__le__``
            # first (a float subclass wins the reversed slot), so this is the
            # dunder a seam that compared the value would run.
            raise RuntimeError("hostile __le__ detonated")

        def __ge__(self, other):
            raise RuntimeError("hostile __ge__ detonated")

    context = {DST_RESOURCE_DEADLINE: HostileFloat(time.monotonic())}
    with pytest.raises(ResourceLimitExceeded) as caught:
        check_deadline(SimpleNamespace(context=context))
    assert caught.value.bound == "execution_deadline_seconds"
    assert caught.value.limit == 0
    assert "unknown" in caught.value.message


def test_an_integer_deadline_too_large_for_the_clock_fails_closed():
    """An instant the conversion to a double overflows is one no comparison can place."""
    context = {DST_RESOURCE_DEADLINE: 10**400}
    with pytest.raises(ResourceLimitExceeded) as caught:
        check_deadline(SimpleNamespace(context=context))
    assert caught.value.bound == "execution_deadline_seconds"


def test_a_benign_comparison_int_subclass_is_still_refused_a_policy_field():
    """Rejecting only the subclasses that DETONATE would store the quiet ones.

    A subclass whose ``<`` answers normally passes a value check and is then
    carried by the policy into every later use of the bound: ``narrowed``'s
    comparison, and the ``limit`` / ``charged`` values every
    ``ResourceLimitExceeded`` formats into its message and ``extensions``. The
    domain is therefore the built-in type, not "an int that behaves today".
    """

    class QuietInt(int):
        def __format__(self, spec):
            raise RuntimeError("hostile __format__ detonated")

    with pytest.raises(ConfigurationError, match="max_list_rows must be a positive integer"):
        ResourcePolicy(max_list_rows=QuietInt(2))
    with pytest.raises(ConfigurationError, match="probe max_rows must be a positive integer"):
        validate_collection_bound(QuietInt(2), field="probe max_rows")


def test_a_hostile_int_subclass_narrowing_a_bound_is_typed_rejected():
    """The narrowing comparison runs on values the policy owns, so it cannot detonate."""

    class HostileInt(int):
        def __gt__(self, other):
            raise RuntimeError("hostile __gt__ detonated")

        def __lt__(self, other):
            raise RuntimeError("hostile __lt__ detonated")

    with pytest.raises(ConfigurationError, match="max_list_rows must be a positive integer"):
        ResourcePolicy(max_list_rows=2).narrowed(max_list_rows=HostileInt(3))


def test_a_float_subclass_cannot_reach_the_derived_deadline_arithmetic():
    """A reflected ``__radd__`` wins over ``float``'s, so it must never be stored.

    ``stash_resource_policy`` derives the absolute deadline as
    ``time.monotonic() + seconds``. Python gives a SUBCLASS's reflected operand
    priority, so a subclass that survived construction could hand that addition
    back a ``nan`` - and a ``nan`` deadline compares false against every clock
    reading, silently disarming the budget of a policy the deployment believes
    it configured.
    """

    class PoisonFloat(float):
        def __radd__(self, other):
            return math.nan

    with pytest.raises(ConfigurationError, match="execution_deadline_seconds"):
        ResourcePolicy(execution_deadline_seconds=PoisonFloat(0.001))

    context: dict[str, Any] = {}
    stash_resource_policy(context, ResourcePolicy(execution_deadline_seconds=0.001))
    assert math.isfinite(context[DST_RESOURCE_DEADLINE])


@pytest.mark.parametrize(
    "written",
    [math.nan, math.inf, -math.inf],
    ids=["nan", "infinity", "negative-infinity"],
)
def test_a_non_finite_deadline_with_no_budget_armed_fails_closed(written):
    """No configured policy derives these, and no comparison can certify them.

    A ``nan`` is neither absent nor non-numeric: it compares false against every
    clock reading, so treating it as an ordinary future instant is how a guard
    whose documented stance is fail-closed ends up permitting the request.
    """
    context = {DST_RESOURCE_DEADLINE: written}
    with pytest.raises(ResourceLimitExceeded) as caught:
        check_deadline(SimpleNamespace(context=context))
    assert caught.value.bound == "execution_deadline_seconds"


# ---------------------------------------------------------------------------
# The armed budget
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _armed(context: Any, policy: ResourcePolicy) -> Any:
    """Run the body with ``policy`` armed as the operation budget, as the extension does."""
    token = begin_resource_budget(context, policy)
    try:
        yield
    finally:
        end_resource_budget(token)


def test_an_armed_budget_outranks_a_policy_a_resolver_writes_over_it():
    """The published key is a mirror; replacing it does not move any bound.

    ``info.context`` belongs to the consumer, so every resolver in the request
    can write ``DST_RESOURCE_POLICY``. If that key were the authority, a
    resolver could hand itself a wider ``max_list_rows`` - and with it the
    ``offset`` ceiling ``list_field.py`` derives from the same field - for the
    rest of the operation without ever passing ``narrowed``.
    """
    context: dict[str, Any] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(max_list_rows=5)):
        context[DST_RESOURCE_POLICY] = ResourcePolicy(max_list_rows=999)
        assert policy_from_info(info).max_list_rows == 5
        assert len(bounded_rows(list(range(1000)), info)) == 5


def test_a_policy_written_without_arming_one_still_answers():
    """The mirror is the fallback where nothing armed a budget.

    A plain ``strawberry.Schema`` that never installed the extension, and a
    direct ``stash_resource_policy`` call, both leave the seams on this path -
    a context none of the package's own collection resolvers runs inside.
    """
    context: dict[str, Any] = {}
    stash_resource_policy(context, ResourcePolicy(max_list_rows=5))
    assert policy_from_info(SimpleNamespace(context=context)).max_list_rows == 5


@pytest.mark.parametrize(
    "written",
    [None, math.nan, math.inf],
    ids=["cleared", "nan", "infinity"],
)
def test_an_armed_deadline_cannot_be_widened_or_cleared_from_the_context(written):
    """A resolver cannot buy itself more wall clock by writing the deadline key."""
    context: dict[str, Any] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(execution_deadline_seconds=0.001)):
        time.sleep(0.01)
        context[DST_RESOURCE_DEADLINE] = written
        with pytest.raises(ResourceLimitExceeded) as caught:
            check_deadline(info)
    assert caught.value.bound == "execution_deadline_seconds"
    assert caught.value.limit == 1


def test_deleting_the_deadline_key_outright_does_not_disarm_the_budget():
    """Absent is not "no deadline" while a budget is armed; it is no narrowing."""
    context: dict[str, Any] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(execution_deadline_seconds=0.001)):
        time.sleep(0.01)
        del context[DST_RESOURCE_DEADLINE]
        with pytest.raises(ResourceLimitExceeded):
            check_deadline(info)


def test_a_resolver_may_shorten_its_own_request():
    """The positive control for the narrowing rule, and what the live async row rides.

    Without it the widening refusals above would still pass if the seam simply
    ignored the context key, which would take a legitimate consumer narrowing
    with it.
    """
    context: dict[str, Any] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(execution_deadline_seconds=30)):
        check_deadline(info)
        context[DST_RESOURCE_DEADLINE] = time.monotonic() - 1
        with pytest.raises(ResourceLimitExceeded) as caught:
            check_deadline(info)
    assert caught.value.limit == 30


def test_a_narrowing_deadline_arrives_where_the_operation_configured_none():
    """A budget armed with no deadline still honours a consumer that sets one."""
    context: dict[str, Any] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy()):
        check_deadline(info)
        context[DST_RESOURCE_DEADLINE] = time.monotonic() - 1
        with pytest.raises(ResourceLimitExceeded) as caught:
            check_deadline(info)
    assert "unknown" in caught.value.message


class _UnorderableDeadline(float):
    """A written deadline no comparison can order against the armed one."""

    def __lt__(self, other):
        raise RuntimeError("hostile __lt__ detonated")


class _NarrowsThenNeverExpires(float):
    """Orders as EARLIER than the armed instant, then as one that has not passed.

    Both answers come out of the same object, which is the whole escape: it is
    admitted as a narrowing and then refuses to read as expired.
    """

    def __lt__(self, other):
        return True

    def __le__(self, other):
        # ``time.monotonic() >= deadline`` dispatches to the REFLECTED operand
        # first, so this is the comparison that decides whether time is up.
        return False


_HOSTILE_DEADLINE_SUBCLASSES = [_UnorderableDeadline, _NarrowsThenNeverExpires]
_HOSTILE_DEADLINE_IDS = ["unorderable", "narrows-then-never-expires"]


@pytest.mark.parametrize(
    "hostile",
    _HOSTILE_DEADLINE_SUBCLASSES,
    ids=_HOSTILE_DEADLINE_IDS,
)
def test_a_numeric_subclass_written_deadline_leaves_the_armed_ceiling_standing(hostile):
    """A value outside the deadline domain cannot be shown to narrow the budget."""
    context: dict[str, Any] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(execution_deadline_seconds=30)):
        context[DST_RESOURCE_DEADLINE] = hostile(time.monotonic() - 1)
        check_deadline(info)


@pytest.mark.parametrize(
    "hostile",
    _HOSTILE_DEADLINE_SUBCLASSES,
    ids=_HOSTILE_DEADLINE_IDS,
)
def test_a_numeric_subclass_written_deadline_cannot_outlive_an_expired_budget(hostile):
    """The escape a narrowing rule alone leaves open once the domain is not exact.

    A subclass answers BOTH comparisons this seam makes - the one deciding
    whether the written instant narrows the armed one, and the one deciding
    whether that instant has passed - so a value that presents as a narrowing on
    the way in can answer every later reading as time remaining. Admitted as the
    effective deadline it buys the rest of the operation unbounded wall clock
    off a budget that has already run out.
    """
    context: dict[str, Any] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(execution_deadline_seconds=0.001)):
        time.sleep(0.01)
        context[DST_RESOURCE_DEADLINE] = hostile(time.monotonic() - 1)
        with pytest.raises(ResourceLimitExceeded) as caught:
            check_deadline(info)
    assert caught.value.bound == "execution_deadline_seconds"


def test_ending_a_budget_restores_the_one_it_was_opened_inside():
    """A nested execution must hand the outer operation its own budget back."""
    context: dict[str, Any] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(max_list_rows=3)):
        with _armed(context, ResourcePolicy(max_list_rows=2)):
            assert policy_from_info(info).max_list_rows == 2
        assert policy_from_info(info).max_list_rows == 3
    # Outside every armed scope the seams fall back to the published mirror,
    # whose cleanup belongs to the extension's ``restored_context_keys`` rather
    # than to the budget token.
    assert policy_from_info(info).max_list_rows == 2
    clear_resource_context(context)
    assert policy_from_info(info) == DEFAULT_RESOURCE_POLICY


async def test_the_armed_budget_reaches_a_sync_to_async_worker_thread():
    """The bound must not evaporate where a resolver hands work to the executor.

    ``sync_to_async`` runs its callable in a worker thread, which is exactly
    where a per-thread stash would read back empty; the ``ContextVar`` is copied
    into that thread, so the seam there enforces the operation's own policy
    rather than falling back to a context the resolver can write.
    """
    from asgiref.sync import sync_to_async

    context: dict[str, Any] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(max_list_rows=7)):
        context[DST_RESOURCE_POLICY] = ResourcePolicy(max_list_rows=999)
        rows = await sync_to_async(lambda: bounded_rows(list(range(100)), info))()
    assert len(rows) == 7


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


@pytest.mark.parametrize(
    "mapping_cls",
    [dict, None],
    ids=["plain-dict", "guarded-mapping-subclass"],
)
def test_bounded_rows_bounds_a_mapping_shaped_result(mapping_cls):
    """A MAPPING-shaped result is bounded via ``islice``, never a raw ``KeyError``.

    A mapping answers a slice subscript with ``KeyError`` on interpreters where
    slices hash - a plain ``dict`` there, and a dict subclass whose
    ``__getitem__`` guards its keys everywhere - so the unsliceable fallback
    must absorb ``KeyError`` alongside ``TypeError``. The alternative was a raw
    ``KeyError`` escaping a collection resolver exactly because the result was a
    shape nobody anticipated, which is the same "bound silently stops applying"
    failure the fallback exists to prevent.
    """

    class _GuardedDict(dict):
        def __getitem__(self, key):
            raise KeyError("guarded")

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    source = (
        _GuardedDict({"a": 1, "b": 2, "c": 3})
        if mapping_cls is None
        else mapping_cls({"a": 1, "b": 2, "c": 3})
    )
    assert bounded_rows(source, info) == ["a", "b"]


@pytest.mark.parametrize("container", [list, tuple], ids=["list", "tuple"])
def test_bounded_rows_does_not_let_a_sequence_subclass_answer_its_own_slice(container):
    """A sequence type may override ``__getitem__``; the bound must not run through it.

    ``result[:limit]`` is the operation the raw-list ceiling is made of, and on a
    ``list`` or ``tuple`` SUBCLASS that operation is consumer code. One that
    ignores the slice and answers with every row it was asked to drop turns the
    only thing standing between a client and the whole table into a call the
    client's own object gets to decide the result of.
    """

    class _Escape(container):
        def __getitem__(self, key):
            if isinstance(key, slice):
                return container(self)
            return super().__getitem__(key)

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    assert bounded_rows(_Escape(range(10)), info) == [0, 1]


@pytest.mark.parametrize(
    ("offset", "limit", "expected"),
    [(1, 1, [1]), (0, 0, []), (2, None, [2, 3])],
    ids=["window", "zero-width-window", "offset-to-the-ceiling"],
)
def test_a_windowed_sequence_subclass_is_bounded_on_every_coordinate(offset, limit, expected):
    """The offset window and the zero-width window bound the hostile shape too.

    ``result[start:start]`` is as much a consumer call as ``result[start:stop]``,
    so a zero-row window is a place a hostile subscript can put rows into a
    response that contractually carries none.
    """

    class _Escape(list):
        def __getitem__(self, key):
            if isinstance(key, slice):
                return list(self)
            return super().__getitem__(key)

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    assert (
        _windowed_rows(_Escape(range(10)), info, offset=offset, requested_limit=limit) == expected
    )


def test_bounded_rows_bounds_a_hostile_mapping_subclass():
    """A ``dict`` subclass is counted, never subscripted, so its guard cannot matter."""

    class _Escape(dict):
        def __getitem__(self, key):
            return list(self)

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    assert bounded_rows(_Escape({"a": 1, "b": 2, "c": 3}), info) == ["a", "b"]


def test_bounded_rows_honours_a_trusted_widening():
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    assert bounded_rows(list(range(10)), info, 4, trusted=True) == [
        0,
        1,
        2,
        3,
    ]


@pytest.mark.parametrize("color", ["sync", "async"], ids=["sync", "async"])
@pytest.mark.parametrize(
    "coordinate",
    ["offset", "requested_limit"],
    ids=["offset", "requested-limit"],
)
async def test_the_exported_raw_list_bound_takes_no_client_window(color, coordinate):
    """A client page window is not on the exported surface, so an importer cannot widen it.

    A supplied window is a claim the bounding seam cannot check, and the one that
    matters here is the wide one: a caller asking for more rows than the request
    policy allows would get them, from the helper whose whole contract is that
    nothing a caller passes can widen its bound. The argument normalizer owns
    that check and rejects an over-ceiling value with a typed, argument-named
    error long before the private window seam sees it, so the pair stays off this
    signature.
    """
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    if color == "sync":
        with pytest.raises(TypeError):
            bounded_rows(list(range(10)), info, **{coordinate: 10})
        assert bounded_rows(list(range(10)), info) == [0, 1]
        return
    with pytest.raises(TypeError):
        await bounded_rows_async(list(range(10)), info, **{coordinate: 10})
    assert await bounded_rows_async(list(range(10)), info) == [0, 1]


async def test_bounded_rows_async_closes_after_the_effective_prefix():
    class Rows:
        def __init__(self):
            self.value = 0
            self.closed = False

        def __aiter__(self):
            return self

        async def __anext__(self):
            value = self.value
            self.value += 1
            return value

        async def aclose(self):
            self.closed = True

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    rows = Rows()

    assert await bounded_rows_async(rows, info) == [0, 1]
    assert rows.closed is True


async def test_bounded_rows_async_preserves_source_errors_when_cleanup_fails():
    class BrokenRows:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise ValueError("source failed")

        async def aclose(self):
            raise RuntimeError("cleanup failed")

    with pytest.raises(ValueError, match="source failed") as caught:
        await bounded_rows_async(BrokenRows(), SimpleNamespace(context={}))

    # The source error stays primary AND the masked cleanup failure rides along as
    # a note -- the half that separates this from a plain re-raise.
    assert any("cleanup failed" in note for note in getattr(caught.value, "__notes__", []))


async def test_bounded_rows_async_survives_a_hostile_notes_list_on_the_source_error():
    """A hostile non-iterable ``__notes__`` on the source error must not mask it.

    The cleanup failure is attached as a note so the source error stays primary;
    the attachment is a diagnostic, so a hostile note surface (an int where the
    note protocol wants a list) must be swallowed rather than replace the source
    error with the attachment's own ``TypeError``. The assertion inspects the
    caught error's own attributes rather than ``pytest.raises(match=...)``:
    pytest's matcher stringifies ``__notes__`` too, so handing it this hostile
    surface would detonate the matcher, not the seam under test.
    """

    class HostileNotesRows:
        def __aiter__(self):
            return self

        async def __anext__(self):
            error = ValueError("source failed")
            error.__notes__ = 42  # hostile: not a list
            raise error

        async def aclose(self):
            raise RuntimeError("cleanup failed")

    with pytest.raises(ValueError) as caught:
        await bounded_rows_async(HostileNotesRows(), SimpleNamespace(context={}))
    assert str(caught.value) == "source failed"
    # The hostile surface itself survived untouched: the containment swallowed
    # its own TypeError without ever writing over the source error's notes.
    assert caught.value.__notes__ == 42


async def test_bounded_rows_async_hostile_notes_property_getter_does_not_mask_the_source():
    """An unreadable ``__notes__`` descriptor must not replace the source error."""

    class HostileError(Exception):
        __notes__ = property(lambda self: (_ for _ in ()).throw(RuntimeError("getter")))  # type: ignore[assignment]

    class BrokenRows:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise HostileError("source failed")

        async def aclose(self):
            raise RuntimeError("cleanup failed")

    # No ``match=`` here for the same reason: pytest's matcher reads
    # ``__notes__`` to render the exception, and this surface raises on read.
    with pytest.raises(HostileError) as caught:
        await bounded_rows_async(BrokenRows(), SimpleNamespace(context={}))
    assert str(caught.value) == "source failed"


async def test_bounded_rows_async_surfaces_cleanup_failure_without_a_source_error():
    class BrokenCleanupRows:
        def __init__(self):
            self.value = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            self.value += 1
            return self.value

        async def aclose(self):
            raise RuntimeError("cleanup failed")

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=1))
    with pytest.raises(RuntimeError, match="cleanup failed"):
        await bounded_rows_async(BrokenCleanupRows(), info)


async def test_bounded_rows_async_hostile_aclose_lookup_does_not_mask_the_source():
    """A hostile aclose attribute lookup must not replace the source error."""

    class HostileAcloseLookupRows:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise ValueError("source failed")

        def __getattribute__(self, name: str):
            if name == "aclose":
                raise RuntimeError("hostile aclose lookup")
            return super().__getattribute__(name)

    with pytest.raises(ValueError, match="source failed") as caught:
        await bounded_rows_async(HostileAcloseLookupRows(), SimpleNamespace(context={}))

    assert any("hostile aclose lookup" in note for note in getattr(caught.value, "__notes__", []))


async def test_bounded_rows_async_hostile_aclose_lookup_surfaces_without_source_error():
    """A hostile aclose attribute lookup raises directly when iteration succeeded."""

    class HostileAcloseLookupRows:
        def __init__(self):
            self.value = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            self.value += 1
            return self.value

        def __getattribute__(self, name: str):
            if name == "aclose":
                raise RuntimeError("hostile aclose lookup")
            return super().__getattribute__(name)

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=1))
    with pytest.raises(RuntimeError, match="hostile aclose lookup"):
        await bounded_rows_async(HostileAcloseLookupRows(), info)


def test_bounded_rows_preserves_none():
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    assert bounded_rows(None, info) is None


def test_bounded_rows_checks_deadline_before_preserving_none():
    info = SimpleNamespace(context={})
    stash_resource_policy(
        info.context,
        ResourcePolicy(max_list_rows=2, execution_deadline_seconds=1),
    )
    info.context[DST_RESOURCE_DEADLINE] = time.monotonic() - 1

    with pytest.raises(ResourceLimitExceeded, match="execution_deadline_seconds"):
        bounded_rows(None, info)


async def test_bounded_rows_async_closes_a_source_the_deadline_rejects_before_any_row():
    """A passed deadline abandons the source, so the seam closes it on the way out.

    The clock is read after the resolver has already produced its source, so this
    rejection owns an iterator that has never been advanced and that no later
    seam will see. Zero advances and exactly one close is the whole claim; the
    consumer-visible half rides live in
    ``examples/fakeshop/test_query/test_list_field_async_api.py::test_async_deadline_rejection_closes_the_source_it_never_advanced``.
    """

    class Rows:
        def __init__(self):
            self.advances = 0
            self.closes = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            self.advances += 1
            raise StopAsyncIteration

        async def aclose(self):
            self.closes += 1

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(execution_deadline_seconds=1))
    info.context[DST_RESOURCE_DEADLINE] = time.monotonic() - 1
    rows = Rows()

    with pytest.raises(ResourceLimitExceeded) as caught:
        await bounded_rows_async(rows, info)

    assert caught.value.extensions["bound"] == "execution_deadline_seconds"
    assert rows.advances == 0
    assert rows.closes == 1


@pytest.mark.parametrize("requested_limit", [None, 0], ids=["default-window", "limit-zero"])
async def test_bounded_rows_async_keeps_the_deadline_primary_when_the_close_fails(
    requested_limit,
):
    """A failing ``aclose`` on the rejected source annotates the rejection, never replaces it.

    The complete resource error is what the client acts on; a cleanup that blows
    up is a diagnostic about the source. ``limit: 0`` is covered beside the
    default window because its empty-window short-circuit sits downstream of the
    clock and therefore never gets to perform its own close.
    """

    class BrokenCleanupRows:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise AssertionError("a rejected source must never be advanced")

        async def aclose(self):
            raise RuntimeError("cleanup failed")

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(execution_deadline_seconds=1))
    info.context[DST_RESOURCE_DEADLINE] = time.monotonic() - 1

    with pytest.raises(ResourceLimitExceeded) as caught:
        await _windowed_rows_async(
            BrokenCleanupRows(),
            info,
            requested_limit=requested_limit,
        )

    assert caught.value.extensions["bound"] == "execution_deadline_seconds"
    assert caught.value.extensions["limit"] == 1
    assert caught.value.extensions["charged"] == 2
    assert any(
        "bounded_rows_async iterator cleanup failed" in note
        for note in getattr(caught.value, "__notes__", [])
    )


async def test_cleanup_rejected_async_iterable_notes_an_iterator_acquisition_failure() -> None:
    """When ``aiter()`` itself fails, the rejection carries the reason as a note.

    The primary error is the rejection the caller is about to raise; a cleanup
    that cannot even acquire the iterator must not replace it, so the acquisition
    failure is attached to it instead.
    """

    class UnacquirableAsyncIterable:
        def __aiter__(self):
            raise RuntimeError("aiter exploded")

    primary = GraphQLError("rejected")
    await _cleanup_rejected_async_iterable(
        UnacquirableAsyncIterable(),
        primary,
        caller="bounded_rows_async",
    )
    assert any(
        "bounded_rows_async iterator acquisition failed" in note for note in primary.__notes__
    )
    assert any("aiter exploded" in note for note in primary.__notes__)


async def test_cleanup_rejected_async_iterable_survives_an_unannotatable_error() -> None:
    """An error that refuses note attachment still leaves the primary error intact.

    Note attachment is best-effort bookkeeping. An exception whose attribute
    writes raise would otherwise turn a clean rejection into an unrelated
    ``RuntimeError`` from the cleanup path.
    """

    class UnacquirableAsyncIterable:
        def __aiter__(self):
            raise RuntimeError("aiter exploded")

    class NoteHostileError(Exception):
        def __setattr__(self, name, value):
            raise RuntimeError("notes refused")

    primary = NoteHostileError("primary")
    await _cleanup_rejected_async_iterable(
        UnacquirableAsyncIterable(),
        primary,
        caller="bounded_rows_async",
    )
    assert not hasattr(primary, "__notes__")


async def test_bounded_rows_async_lets_a_cancellation_during_cleanup_reach_the_task():
    """A cancellation arriving while ``aclose`` runs outranks the source error it interrupts.

    Every other cleanup failure is demoted to a note so the source error stays
    primary. A cancellation is not a cleanup failure: it is the request being
    torn down, and demoting it would let the task finish with an ordinary field
    error, telling the client the operation completed while the source was still
    being closed.
    """
    closing = asyncio.Event()
    source_error = ValueError("source failed")

    class CancelledDuringCleanupRows:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise source_error

        async def aclose(self):
            closing.set()
            await asyncio.sleep(3600)

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    task = asyncio.ensure_future(bounded_rows_async(CancelledDuringCleanupRows(), info))
    await closing.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
    assert task.cancelled() is True
    # The cancellation was not written onto the source error as a diagnostic,
    # which is the shape that would have left the task uncancelled.
    assert not getattr(source_error, "__notes__", [])


async def test_cleanup_rejected_async_iterable_lets_a_cancelled_acquisition_through():
    """Acquisition interrupted by cancellation propagates instead of annotating the rejection.

    The pre-iteration cleanup runs while a rejection is already on its way out,
    so an ordinary acquisition failure becomes a note on it. A control signal
    reaching the same seam means the task is going away, and the caller has to
    see that rather than a rejection reporting a completed request.
    """

    class CancellingAsyncIterable:
        def __aiter__(self):
            raise asyncio.CancelledError

    primary = GraphQLError("rejected")
    with pytest.raises(asyncio.CancelledError):
        await _cleanup_rejected_async_iterable(
            CancellingAsyncIterable(),
            primary,
            caller="bounded_rows_async",
        )
    assert not getattr(primary, "__notes__", [])


async def test_bounded_rows_async_preserves_none():
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    assert await bounded_rows_async(None, info) is None


async def test_bounded_rows_async_exhausted_iterator_without_truncation():
    """An async iterator yielding fewer items than the bound exhausts normally without early aclose."""

    class ShortRows:
        def __init__(self):
            self.items = [1, 2]
            self.closed = False

        def __aiter__(self):
            self.iter = iter(self.items)
            return self

        async def __anext__(self):
            try:
                return next(self.iter)
            except StopIteration:
                raise StopAsyncIteration from None

        async def aclose(self):
            self.closed = True

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=5))
    rows = ShortRows()
    assert await bounded_rows_async(rows, info) == [1, 2]
    assert rows.closed is False


def test_bounded_rows_slices_with_offset_and_requested_limit():
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    data = list(range(10))
    assert _windowed_rows(data, info, offset=2, requested_limit=3) == [2, 3, 4]
    assert _windowed_rows(data, info, offset=None, requested_limit=3) == [0, 1, 2]
    # When requested_limit is None, the policy limit (10) bounds the window:
    assert _windowed_rows(data, info, offset=7, requested_limit=None) == [7, 8, 9]


def test_bounded_rows_slices_unsliceable_iterable_with_offset_and_requested_limit():
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    class _Rows:
        def __iter__(self):
            return iter(range(10))

    assert _windowed_rows(_Rows(), info, offset=3, requested_limit=4) == [
        3,
        4,
        5,
        6,
    ]


def test_bounded_rows_zero_window_does_not_advance_generator():
    """A zero window returns an empty list without consuming or advancing unsliceable iterators."""
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    def _gen():
        yield 1
        yield 2

    g = _gen()
    assert _windowed_rows(g, info, offset=0, requested_limit=0) == []
    # Generator has NOT been advanced:
    assert next(g) == 1

    # Also test sliceable sequence with zero window
    assert _windowed_rows([1, 2, 3], info, offset=1, requested_limit=0) == []


async def test_bounded_rows_async_slices_with_offset_and_requested_limit():
    class Rows:
        def __init__(self):
            self.value = 0
            self.closed = False

        def __aiter__(self):
            return self

        async def __anext__(self):
            value = self.value
            self.value += 1
            return value

        async def aclose(self):
            self.closed = True

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))
    rows = Rows()

    assert await _windowed_rows_async(rows, info, offset=2, requested_limit=3) == [2, 3, 4]
    assert rows.closed is True


async def test_bounded_rows_async_zero_window_closes_without_next():
    """A zero window on an async iterator closes it immediately without calling __anext__."""

    class Rows:
        def __init__(self):
            self.next_called = False
            self.closed = False

        def __aiter__(self):
            return self

        async def __anext__(self):
            self.next_called = True
            return 1

        async def aclose(self):
            self.closed = True

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))
    rows = Rows()

    assert await _windowed_rows_async(rows, info, offset=0, requested_limit=0) == []
    assert rows.next_called is False
    assert rows.closed is True


class _MatrixUnsliceable:
    def __init__(self, items):
        self._items = items

    def __iter__(self):
        return iter(self._items)


@pytest.mark.parametrize(
    "source_factory",
    [list, tuple, _MatrixUnsliceable],
    ids=["list", "tuple", "unsliceable"],
)
@pytest.mark.parametrize(
    (
        "offset",
        "requested_limit",
        "declared",
        "trusted",
        "expected",
    ),
    [
        (
            None,
            None,
            None,
            False,
            list(range(10)),
        ),
        (
            None,
            None,
            5,
            False,
            list(range(5)),
        ),
        (
            3,
            None,
            None,
            False,
            list(range(3, 13)),
        ),
        (
            None,
            4,
            None,
            False,
            list(range(4)),
        ),
        (
            2,
            5,
            None,
            False,
            list(range(2, 7)),
        ),
        (
            50,
            10,
            None,
            False,
            [],
        ),
        (
            2,
            0,
            None,
            False,
            [],
        ),
        (
            2,
            None,
            15,
            True,
            list(range(2, 17)),
        ),
    ],
)
def test_bounded_rows_window_parameter_matrix(
    source_factory,
    offset,
    requested_limit,
    declared,
    trusted,
    expected,
):
    """Parametrize sequences and non-subscriptable iterables across window parameters."""
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))
    items = list(range(30))
    source = source_factory(items)

    result = _windowed_rows(
        source,
        info,
        declared,
        offset=offset,
        requested_limit=requested_limit,
        trusted=trusted,
    )
    assert list(result) == expected

    # Positional 3-argument call still binds declared
    result_positional = bounded_rows(source_factory(list(range(20))), info, 4)
    assert list(result_positional) == list(range(4))


async def test_bounded_rows_async_positive_offset_arithmetic():
    """Positive-offset arithmetic over an async iterator at helper seam (spec-050 Decision 8)."""
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    async def _gen():
        for i in range(20):
            yield i

    res = await _windowed_rows_async(_gen(), info, offset=5, requested_limit=4)
    assert res == [
        5,
        6,
        7,
        8,
    ]


def test_bounded_rows_declined_sync_cleanup_resumable():
    """Pin the declined sync cleanup contract: truncated sync generator stays suspended and resumable."""
    finally_ran = False

    def _sync_gen():
        nonlocal finally_ran
        try:
            yield from range(10)
        finally:
            finally_ran = True

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    g = _sync_gen()
    result = _windowed_rows(g, info, offset=2, requested_limit=3)
    assert result == [2, 3, 4]
    assert finally_ran is False

    # Resumable: can continue reading subsequent values
    assert next(g) == 5
    assert finally_ran is False

    g.close()
    assert finally_ran is True


def test_bounded_rows_unsliceable_iterable_exact_consumption(monkeypatch):
    """Counters around __iter__/__next__ and patched islice seam verify exact consumption."""
    from itertools import islice

    class CountedUnsliceable:
        def __init__(self, count):
            self.count = count
            self.iter_calls = 0
            self.next_calls = 0

        def __iter__(self):
            self.iter_calls += 1
            return self

        def __next__(self):
            if self.next_calls >= self.count:
                raise StopIteration
            val = self.next_calls
            self.next_calls += 1
            return val

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    islice_calls = 0
    orig_islice = islice

    def spy_islice(*args):
        nonlocal islice_calls
        islice_calls += 1
        return orig_islice(*args)

    monkeypatch.setattr("django_strawberry_framework.resource_policy.islice", spy_islice)

    # requested_limit=0 must return [] without constructing islice or advancing
    c0 = CountedUnsliceable(10)
    assert _windowed_rows(c0, info, offset=2, requested_limit=0) == []
    assert c0.next_calls == 0
    assert islice_calls == 0

    # positive window consumes exactly offset + returned rows and never the next item
    c1 = CountedUnsliceable(10)
    islice_calls = 0
    res = _windowed_rows(c1, info, offset=2, requested_limit=3)
    assert res == [2, 3, 4]
    assert islice_calls == 1
    assert c1.next_calls == 5


async def test_bounded_rows_async_exact_consumption_and_cleanup_matrix():
    """Async-only exact consumption, iterator acquisition, and cleanup counts matrix."""

    class TrackedAsyncIterable:
        def __init__(
            self,
            items,
            fail_at=None,
            fail_close=False,
        ):
            self.items = items
            self.fail_at = fail_at
            self.fail_close = fail_close
            self.iter_acquired = 0
            self.anext_calls = 0
            self.aclose_calls = 0

        def __aiter__(self):
            self.iter_acquired += 1
            return self

        async def __anext__(self):
            self.anext_calls += 1
            if self.fail_at is not None and self.anext_calls == self.fail_at:
                raise ValueError("Source failure")
            if self.anext_calls > len(self.items):
                raise StopAsyncIteration
            return self.items[self.anext_calls - 1]

        async def aclose(self):
            self.aclose_calls += 1
            if self.fail_close:
                raise RuntimeError("Cleanup failure")

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    # 1. Zero limit acquires and closes once with zero advances
    src_zero = TrackedAsyncIterable([1, 2, 3])
    res_zero = await _windowed_rows_async(src_zero, info, offset=0, requested_limit=0)
    assert res_zero == []
    assert src_zero.iter_acquired == 1
    assert src_zero.anext_calls == 0
    assert src_zero.aclose_calls == 1

    # 2. Reaching exclusive stop closes
    src_stop = TrackedAsyncIterable(
        [
            1,
            2,
            3,
            4,
            5,
        ],
    )
    res_stop = await _windowed_rows_async(src_stop, info, offset=1, requested_limit=2)
    assert res_stop == [2, 3]
    assert src_stop.anext_calls == 3
    assert src_stop.aclose_calls == 1

    # 3. Source holding EXACTLY offset + limit rows (2 rows, offset=1, limit=1)
    src_exact = TrackedAsyncIterable([10, 20])
    res_exact = await _windowed_rows_async(src_exact, info, offset=1, requested_limit=1)
    assert res_exact == [20]
    assert src_exact.anext_calls == 2
    assert src_exact.aclose_calls == 1

    # 4. Source holding FEWER rows than offset + limit: naturally exhausts, does NOT close
    src_fewer = TrackedAsyncIterable([10])
    res_fewer = await _windowed_rows_async(src_fewer, info, offset=1, requested_limit=2)
    assert res_fewer == []
    assert src_fewer.anext_calls == 2
    assert src_fewer.aclose_calls == 0

    # 5. Offset overshoot that naturally exhausts does not close
    src_over = TrackedAsyncIterable([1, 2])
    res_over = await _windowed_rows_async(src_over, info, offset=5, requested_limit=2)
    assert res_over == []
    assert src_over.anext_calls == 3
    assert src_over.aclose_calls == 0

    # 6. Source failure + cleanup failure keeps source primary with one note
    src_both_fail = TrackedAsyncIterable([1, 2, 3], fail_at=2, fail_close=True)
    with pytest.raises(ValueError, match="Source failure") as exc_info:
        await _windowed_rows_async(src_both_fail, info, offset=0, requested_limit=3)
    notes = getattr(exc_info.value, "__notes__", [])
    assert any("bounded_rows_async iterator cleanup failed" in str(n) for n in notes)

    # 7. Cleanup-only failure remains primary
    src_clean_fail = TrackedAsyncIterable([1, 2, 3], fail_close=True)
    with pytest.raises(RuntimeError, match="Cleanup failure"):
        await _windowed_rows_async(src_clean_fail, info, offset=0, requested_limit=2)


def test_bounded_rows_shared_policy_seams_spy(monkeypatch):
    """Spy on check_deadline and effective_bound at bounded_rows seam."""
    import django_strawberry_framework.resource_policy as rp

    check_deadline_calls = 0
    effective_bound_calls = 0

    orig_check = rp.check_deadline
    orig_bound = rp.effective_bound

    def spy_check(info):
        nonlocal check_deadline_calls
        check_deadline_calls += 1
        return orig_check(info)

    def spy_bound(*args, **kwargs):
        nonlocal effective_bound_calls
        effective_bound_calls += 1
        return orig_bound(*args, **kwargs)

    monkeypatch.setattr(rp, "check_deadline", spy_check)
    monkeypatch.setattr(rp, "effective_bound", spy_bound)

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    # Coordinate-bearing call: calls each seam once before source advance
    check_deadline_calls = 0
    effective_bound_calls = 0
    res = _windowed_rows([1, 2, 3], info, offset=1, requested_limit=1)
    assert res == [2]
    assert check_deadline_calls == 1
    assert effective_bound_calls == 1

    # Relation-list caller with no coordinates: calls each seam once and retains old prefix bound
    check_deadline_calls = 0
    effective_bound_calls = 0
    res_no_coords = bounded_rows(list(range(20)), info)
    assert res_no_coords == list(range(10))
    assert check_deadline_calls == 1
    assert effective_bound_calls == 1


# ---------------------------------------------------------------------------
# The pre-parse text scan
# ---------------------------------------------------------------------------


def test_an_absent_document_charges_nothing():
    scan_document_text(DEFAULT_RESOURCE_POLICY, None)
    scan_document_text(DEFAULT_RESOURCE_POLICY, "")


@pytest.mark.parametrize(
    "hostile",
    [
        123,
        b"{ a }",
        ["{ a }"],
        {"query": "{ a }"},
        3.5,
        object(),
        True,
    ],
    ids=[
        "int",
        "bytes",
        "list",
        "dict",
        "float",
        "object",
        "bool",
    ],
)
def test_a_non_string_query_is_declined_not_scanned(hostile):
    """A non-string query is declined, never handed to the lexer.

    Handing a truthy non-string to the lexer raised a raw ``TypeError`` /
    ``AttributeError`` / ``KeyError`` from inside graphql-core at exactly the
    input the exception-containment invariant says must never escape an input
    decoder. The HTTP transports type-check the query before the extension runs,
    but the WebSocket path does not, so the decline is the scanner's own
    contract: a value that is not text carries no tokens to charge.
    """
    scan_document_text(DEFAULT_RESOURCE_POLICY, hostile)


def test_structural_delimiter_pairs_derivation():
    """_OPEN_TOKEN_KINDS and _CLOSE_TOKEN_KINDS derive from _STRUCTURAL_DELIMITER_PAIRS."""
    assert _STRUCTURAL_DELIMITER_PAIRS == (
        (TokenKind.BRACE_L, TokenKind.BRACE_R),
        (TokenKind.PAREN_L, TokenKind.PAREN_R),
        (TokenKind.BRACKET_L, TokenKind.BRACKET_R),
    )
    assert (
        frozenset(open_kind for open_kind, _ in _STRUCTURAL_DELIMITER_PAIRS) == _OPEN_TOKEN_KINDS
    )
    assert (
        frozenset(close_kind for _, close_kind in _STRUCTURAL_DELIMITER_PAIRS)
        == _CLOSE_TOKEN_KINDS
    )
    assert not (_OPEN_TOKEN_KINDS & _CLOSE_TOKEN_KINDS)


@pytest.mark.parametrize(
    ("doc", "limit", "should_exceed"),
    [
        ("{ a { b { c } } }", 2, True),
        ("{ a { b { c } } }", 3, False),
        ("{ foo(arg: { bar: 1 }) }", 2, True),
        ("{ foo(arg: { bar: 1 }) }", 3, False),
        ("{ foo(filter: [1, 2]) }", 2, True),
        ("{ foo(filter: [1, 2]) }", 3, False),
    ],
    ids=[
        "nested_braces_exceeds",
        "nested_braces_passes",
        "nested_parens_and_braces_exceeds",
        "nested_parens_and_braces_passes",
        "nested_brackets_exceeds",
        "nested_brackets_passes",
    ],
)
def test_pre_parse_scan_depth_across_delimiter_families(doc, limit, should_exceed):
    """The pre-parse scan tracks depth across braces, parens, and brackets."""
    policy = ResourcePolicy(max_depth=limit)
    if should_exceed:
        with pytest.raises(ResourceLimitExceeded) as caught:
            scan_document_text(policy, doc)
        assert caught.value.bound == "max_depth"
    else:
        scan_document_text(policy, doc)


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
class _ProbeEdge:
    node: str
    cursor: str


@strawberry.type
class _ProbeConnection:
    """The whole edge shape ``_is_connection_type`` matches on."""

    edges: list[_ProbeEdge]


@strawberry.type
class _Probe:
    """A minimal schema whose only job is to give the walker real types."""

    fauxes: list[_NotAConnection]
    scalar_edges: _ScalarEdges

    @strawberry.field
    def page(self, first: int | None = None) -> _ProbeConnection:
        return _ProbeConnection(edges=[])

    @strawberry.field
    def echo(self, text: str = "x", tags: list[str] | None = None) -> str:
        return text

    @strawberry.field
    def nested(self, tags: list[list[str]] | None = None) -> str:
        return tags[0][0] if tags else ""

    @strawberry.field
    def blob(self, payload: strawberry.scalars.JSON = None) -> str:
        return "ok"

    @strawberry.field
    def stash(self, document: Upload) -> str:
        return "ok"


_PROBE_SCHEMA = strawberry.Schema(query=_Probe)


@strawberry.type
class _WriteProbe:
    """A plain ``strawberry.Schema`` mutation root - no package bind specs anywhere.

    The ID-scalar fallback in ``_charge_list_family`` exists for exactly this
    schema shape: a mutation the package did not generate carries no
    ``_input_field_specs`` map, so an id list is classified by its scalar name,
    exactly as before the spec signal existed.
    """

    @strawberry.mutation
    def tag(self, tags: list[strawberry.ID] | None = None) -> str:
        return "ok"


_PROBE_WRITE_SCHEMA = strawberry.Schema(query=_Probe, mutation=_WriteProbe)


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


def _charge_write(document, variables=None, policy=None):
    """Charge a mutation document against the plain-schema probe (no bind specs)."""
    charge_document(
        policy or DEFAULT_RESOURCE_POLICY,
        _PROBE_WRITE_SCHEMA._schema,
        parse(document),
        variables or {},
        None,
    )


def test_an_id_list_in_a_plain_mutation_charges_the_relation_fallback():
    """The ID-scalar fallback keeps charging relation ids without bind specs.

    The spec rule only ever ADDS a classification signal for writes the
    package generated; a plain ``strawberry.Schema`` mutation has none, and its
    ``[ID]`` list must keep charging ``max_relation_ids_per_mutation`` by name -
    the same contract the GlobalID twins pin live over the generated write.
    """
    _charge_write("mutation T($tags: [ID!]) { tag(tags: $tags) }", {"tags": ["a", "b"]})
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge_write(
            "mutation T($tags: [ID!]) { tag(tags: $tags) }",
            {"tags": ["x", "y"]},
            policy=ResourcePolicy(max_relation_ids_per_mutation=1),
        )
    assert caught.value.bound == "max_relation_ids_per_mutation"
    assert caught.value.charged == 2


def test_an_absent_optional_argument_value_is_charged_as_nothing():
    """A ``None`` argument value (an omitted optional variable) charges no leaves."""
    _charge("query T($t: [String!]) { echo(tags: $t) }", {"t": None})


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


def test_scalar_list_coercion_charges_synthetic_lists_as_input_nodes():
    """The coerced one-item list itself counts toward the input-node budget."""
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($t: [String!]) { echo(tags: $t) }",
            {"t": "solo"},
            policy=ResourcePolicy(max_input_nodes=1),
        )
    assert caught.value.bound == "max_input_nodes"


def test_scalar_list_coercion_charges_each_declared_list_level():
    """A bare variable is coerced to one item at every declared list level."""
    document = "query T($t: [[String!]]) { nested(tags: $t) }"
    _charge(document, {"t": "solo"}, policy=ResourcePolicy(max_value_depth=2))
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(document, {"t": "solo"}, policy=ResourcePolicy(max_value_depth=1))
    assert caught.value.bound == "max_value_depth"


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


class _AmountNoBoundCanExceed(int):
    """An amount no bound can ever be over, by whichever route it is charged.

    Its ``__gt__`` answers the comparison a rejection is decided by; its
    reflected ``__radd__`` and ``__rmul__`` - which take priority over
    ``int``'s own - decide what a running total and a multiplied bound become
    the moment one of these reaches them, and ``nan`` is over no limit ever
    again.
    """

    def __gt__(self, other):
        return False

    def __radd__(self, other):
        return math.nan

    def __rmul__(self, other):
        return math.nan


def test_a_page_size_variable_outside_the_integers_narrows_nothing():
    """A page bound is a charge, so the value that sets it must be one the package owns.

    ``first`` narrows the rows a connection selection is charged. Supplied as an
    ``int`` SUBCLASS it answers the clamp that would cap it at the page ceiling
    AND, once charged, the reflected addition the running collection cost is
    accumulated through - a page bound that is over every ceiling and a total
    that is under every one. Out of the domain, it narrows nothing and the
    selection is charged the policy's own ceiling.
    """
    document = "query P($n: Int) { page(first: $n) { edges { node } } }"
    policy = ResourcePolicy(max_page_size=50, max_collection_cost=49)
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(document, {"n": _AmountNoBoundCanExceed(10**9)}, policy=policy)
    assert caught.value.bound == "max_collection_cost"
    assert caught.value.charged == 50
    _charge(document, {"n": 10}, policy=policy)


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
# Values the walk cannot take at their word
# ---------------------------------------------------------------------------


class _CountingList(list):
    """A sequence that reports no members, yields all of them, and counts advances."""

    def __init__(self, members):
        super().__init__(members)
        self.advances = 0

    def __len__(self):
        return 0

    def __iter__(self):
        for member in list.__iter__(self):
            self.advances += 1
            yield member


def test_a_container_is_charged_for_what_it_yields_not_for_what_it_reports():
    """A width-shaped bound must not be settled by the container's own ``__len__``.

    An in-process caller's ``variable_values`` can hand the walk a ``list``
    subclass, and every width the budget charges - the container width here, and
    the membership, node-id, nested-row and relation-id families derived from it
    - was read off that object. One reporting zero while iteration yields a
    hundred members puts a hundred values through the coercer and the ORM at a
    charge of nothing.
    """
    value = _CountingList(range(100))

    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($p: JSON) { blob(payload: $p) }",
            {"p": value},
            policy=ResourcePolicy(max_container_width=1),
        )
    assert caught.value.bound == "max_container_width"
    assert caught.value.charged == 2
    assert value.advances == 2


def test_a_container_within_the_bound_is_charged_the_width_it_yields():
    """Under the bound the charge is the real width, and the walk queues those members.

    The reader stops one past the limit, so a container that fits was read in
    full: what it yielded is both the width charged and the work queued. Three
    members are two nodes short of the node budget here, which is what proves
    the members reached the walk rather than being counted and dropped.
    """
    value = _CountingList(range(3))
    _charge(
        "query T($p: JSON) { blob(payload: $p) }",
        {"p": value},
        policy=ResourcePolicy(max_container_width=3, max_input_nodes=4),
    )
    assert value.advances == 3

    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($p: JSON) { blob(payload: $p) }",
            {"p": _CountingList(range(3))},
            policy=ResourcePolicy(max_container_width=3, max_input_nodes=3),
        )
    assert caught.value.bound == "max_input_nodes"


def test_a_container_is_not_advanced_once_its_width_is_already_proven():
    """Measuring an over-wide container costs what the bound allows, not what it holds.

    Copying the container first charged the request for every member of an input
    it was about to refuse, and made a value whose iterator never ends a walk
    that never returns. What proves the stop is the probe's own log of what it
    handed out, read after the rejection: a reader's refusal cannot be evidence
    about the reader, because an unmeasurable value and an over-wide one are
    deliberately the same typed rejection with the same charge. The poison
    beyond the last member stays as a second signal, not as the witness.
    """
    advances = []

    def _members():
        for member in (1, 2, 3):
            advances.append(member)
            yield member
        raise AssertionError("advanced past the last member")

    class _Endless(list):
        def __iter__(self):
            return _members()

    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($p: JSON) { blob(payload: $p) }",
            {"p": _Endless([1, 2, 3])},
            policy=ResourcePolicy(max_container_width=1),
        )
    assert caught.value.bound == "max_container_width"
    assert caught.value.charged == 2
    assert advances == [1, 2]


@pytest.mark.parametrize(
    "value",
    [_CountingList(()), _CountingList((1, 2))],
    ids=["empty", "members"],
)
def test_a_custom_sequence_is_measurable_at_the_largest_bound_a_policy_admits(value):
    """The reader's lookahead has to reach the whole domain the bound declares.

    ``MAX_RESOURCE_BOUND`` is ``sys.maxsize``, so a reader that asks for one
    member past the limit asks for one past what a stop argument can express.
    Its own argument error would then be caught as an unmeasurable input, and
    every custom sequence in the request would be refused at the setting that
    was supposed to permit everything.
    """
    _charge(
        "query T($p: JSON) { blob(payload: $p) }",
        {"p": value},
        policy=ResourcePolicy(max_container_width=MAX_RESOURCE_BOUND),
    )


def test_a_custom_mapping_is_measurable_at_the_largest_bound_a_policy_admits():
    """The mapping half reads through the same bounded reader and the same bound."""

    class _CountingMapping(dict):
        def items(self):
            yield from dict.items(self)

    _charge(
        "query T($p: JSON) { blob(payload: $p) }",
        {"p": _CountingMapping({"a": 1, "b": 2})},
        policy=ResourcePolicy(max_container_width=MAX_RESOURCE_BOUND),
    )


def test_a_container_that_cannot_be_read_is_refused_rather_than_raised():
    """A member the framework cannot obtain is unmeasurable, which is a refusal."""

    class _Unreadable(list):
        def __iter__(self):
            raise RuntimeError("iteration exploded")

    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($p: JSON) { blob(payload: $p) }",
            {"p": _Unreadable([1, 2])},
            policy=ResourcePolicy(max_container_width=4),
        )
    assert caught.value.bound == "max_container_width"
    assert caught.value.charged == 5


def test_a_container_whose_length_raises_is_still_measured():
    """The width comes from the members, so a raising ``__len__`` is never consulted.

    Materializing the container asked it for a size hint first, which turned a
    hostile ``__len__`` into a raw error out of the value walk - the same shape
    the buffer leaf had. Both verdicts are pinned: within the bound the value
    passes, past it the refusal is typed.
    """

    class _LengthBomb(list):
        def __len__(self):
            raise RuntimeError("length exploded")

    _charge(
        "query T($p: JSON) { blob(payload: $p) }",
        {"p": _LengthBomb([1, 2])},
        policy=ResourcePolicy(max_container_width=2),
    )
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($p: JSON) { blob(payload: $p) }",
            {"p": _LengthBomb([1, 2, 3])},
            policy=ResourcePolicy(max_container_width=2),
        )
    assert caught.value.bound == "max_container_width"
    assert caught.value.charged == 3


def test_a_mapping_is_charged_for_the_entries_the_walk_queues():
    """The mapping half of the same rule, on a ``dict`` subclass."""
    advances = []

    class _LyingWidth(dict):
        def __len__(self):
            return 0

        def items(self):
            for pair in dict.items(self):
                advances.append(pair)
                yield pair

    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($p: JSON) { blob(payload: $p) }",
            {"p": _LyingWidth({str(index): index for index in range(50)})},
            policy=ResourcePolicy(max_container_width=1),
        )
    assert caught.value.bound == "max_container_width"
    assert caught.value.charged == 2
    assert len(advances) == 2


def test_an_ordinary_container_still_charges_its_own_width():
    """The control: an exact ``list`` or ``dict`` is measured by the interpreter.

    At an exact type ``len`` is the package's own answer, so the container is
    charged its real width even when that is far past the bound, and nothing is
    copied to find out.
    """
    _charge(
        "query T($p: JSON) { blob(payload: $p) }",
        {"p": [1, 2]},
        policy=ResourcePolicy(max_container_width=2),
    )
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($p: JSON) { blob(payload: $p) }",
            {"p": {"a": 1, "b": 2, "c": 3}},
            policy=ResourcePolicy(max_container_width=2),
        )
    assert caught.value.charged == 3


def test_a_text_leaf_is_measured_by_the_built_in_encoding_not_its_own():
    """``max_scalar_bytes`` measures the text, not what the text says about itself.

    A ``str`` SUBCLASS carries its own ``encode``, and the byte count the bound
    compares against was that method's return value.
    """

    class _LyingEncode(str):
        def encode(self, *args, **kwargs):
            return b"x"

    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($p: JSON) { blob(payload: $p) }",
            {"p": _LyingEncode("y" * 100)},
            policy=ResourcePolicy(max_scalar_bytes=1),
        )
    assert caught.value.bound == "max_scalar_bytes"
    assert caught.value.charged == 100


def test_a_buffer_leaf_is_measured_through_the_buffer_protocol():
    """A buffer's size comes from the C protocol, never from a Python ``__len__``.

    Reaching for it as ``getattr(value, "nbytes", len(value))`` evaluates the
    default argument first, so a raising ``__len__`` replaced the typed
    rejection with a bare ``RuntimeError`` out of the value walk - before the
    attribute that was supposed to stand in for it was ever looked at.
    """

    class _RaisingLength(bytes):
        def __len__(self):
            raise RuntimeError("length exploded")

    _charge(
        "query T($p: JSON) { blob(payload: $p) }",
        {"p": _RaisingLength(b"ab")},
        policy=ResourcePolicy(max_scalar_bytes=2),
    )
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($p: JSON) { blob(payload: $p) }",
            {"p": _RaisingLength(b"abc")},
            policy=ResourcePolicy(max_scalar_bytes=2),
        )
    assert caught.value.bound == "max_scalar_bytes"
    assert caught.value.charged == 3


@pytest.mark.parametrize(
    ("value", "expected"),
    [(b"abc", 3), (bytearray(b"abcd"), 4), (memoryview(b"abcde"), 5)],
    ids=["bytes", "bytearray", "memoryview"],
)
def test_every_buffer_shape_keeps_charging_its_real_size(value, expected):
    """The control for the three buffer types the leaf charge admits."""
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($p: JSON) { blob(payload: $p) }",
            {"p": value},
            policy=ResourcePolicy(max_scalar_bytes=1),
        )
    assert caught.value.charged == expected


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
    """The admission hook runs even when the parse produced nothing to walk."""
    extension = DjangoResourcePolicyExtension()
    extension.execution_context = SimpleNamespace(
        schema=SimpleNamespace(),
        graphql_document=None,
        variables=None,
        operation_name=None,
    )
    hook = extension.on_parse()
    next(hook)
    with pytest.raises(StopIteration):
        next(hook)


def test_a_verdict_recorded_outside_an_operation_is_not_kept():
    """There is no operation for it to belong to, and no later one inherits it."""
    record_admission_rejection(
        ResourceLimitExceeded("max_container_width", 1, 2, "a list argument is too wide"),
    )
    assert admission_rejection() is None
    with _armed({}, DEFAULT_RESOURCE_POLICY):
        assert admission_rejection() is None


def test_an_operation_the_budget_rejected_does_not_begin_executing():
    """A rejection means nothing runs, restated where running starts.

    Publishing is what makes validation stand down, and every seam that reads a
    pre-execution error stops there - except a streaming path that yields the
    error frame and then executes the operation anyway, which some releases in
    the supported range do. The hook execution begins from is entered only when
    an operation is about to run, so it is where that contradiction is closed.
    What it reads is the recorded verdict rather than the published error,
    because the published error is a field anything in the extension chain
    writes.
    """
    extension = DjangoResourcePolicyExtension()
    rejection = ResourceLimitExceeded("max_container_width", 1, 2, "a list argument is too wide")

    with _armed({}, DEFAULT_RESOURCE_POLICY):
        record_admission_rejection(rejection)
        with pytest.raises(ResourceLimitExceeded) as caught:
            next(extension.on_execute())

    assert caught.value is rejection


def test_an_operation_the_budget_admitted_executes():
    """The other verdict: an admitted operation passes the same hook untouched."""
    extension = DjangoResourcePolicyExtension()

    with _armed({}, DEFAULT_RESOURCE_POLICY):
        hook = extension.on_execute()
        next(hook)
        with pytest.raises(StopIteration):
            next(hook)


class _StreamWitness(SchemaExtension):
    """Record that the executing stage was entered, from ahead of the package's entries."""

    entered: list[str] = []

    def on_execute(self):
        _StreamWitness.entered.append(self.execution_context.query or "")
        yield


@strawberry.type
class _StreamedQuery:
    """One field, so a streaming schema has a query type to be built with."""

    @strawberry.field
    def hello(self) -> str:
        return "ok"


@strawberry.type
class _StreamedSubscription:
    """One subscription whose events only arrive if the operation was admitted."""

    @strawberry.subscription
    async def ticks(self) -> AsyncGenerator[int, None]:
        yield 1


@pytest.mark.parametrize(
    "extensions",
    [[], [ValidationCache]],
    ids=["no-cache", "with-a-validation-cache"],
)
@pytest.mark.parametrize("verdict", ["rejected", "admitted"])
async def test_the_streaming_path_carries_the_same_admission_verdict(extensions, verdict):
    """One verdict per request, on the entry point that yields frames rather than a body.

    A streaming transport drives the schema's own generator, so a refusal that
    raised would reach it as an exception with no frame at all - which is why
    admission publishes. The cache row is here because the composed path has to
    answer the same way: what the client receives is one frame carrying the
    typed rejection, and no event from the subscription behind it.
    """
    schema = DjangoSchema(
        query=_StreamedQuery,
        subscription=_StreamedSubscription,
        extensions=[
            _StreamWitness,
            lambda: DjangoResourcePolicyExtension(policy=ResourcePolicy(max_aliases=1)),
            *extensions,
        ],
    )
    query = (
        "subscription { a: ticks b: ticks }"
        if verdict == "rejected"
        else "subscription { a: ticks }"
    )

    _StreamWitness.entered.clear()
    frames = [frame async for frame in await schema.subscribe(query)]

    assert len(frames) == 1
    if verdict == "rejected":
        assert frames[0].data is None
        assert len(frames[0].errors) == 1
        assert frames[0].errors[0].extensions["bound"] == "max_aliases"
        assert _StreamWitness.entered == []
    else:
        assert frames[0].errors is None
        assert frames[0].data == {"a": 1}
        assert _StreamWitness.entered == [query]


@pytest.mark.parametrize(
    "extension_type",
    [DjangoResourcePolicyExtension, _AdmissionGuard],
    ids=["the-enforcing-entry", "the-appended-guard"],
)
def test_a_rejection_an_extension_erased_is_restated_before_execution_is_decided(extension_type):
    """The published error is a mutable field; the verdict is what survives it.

    A validation extension that runs its own pass assigns the result over
    whatever is published - Strawberry's ``ValidationCache`` does exactly that.
    Upstream decides whether to execute from INSIDE the validation stage, so the
    restatement has to happen while the hook is setting up, and the two entries
    that make it are the enforcing one and the guard appended behind every
    consumer entry.
    """
    extension = extension_type()
    rejection = ResourceLimitExceeded("max_aliases", 1, 2, "too many aliases")
    extension.execution_context = SimpleNamespace(pre_execution_errors=[])

    with _armed({}, DEFAULT_RESOURCE_POLICY):
        record_admission_rejection(rejection)
        hook = extension.on_validate()
        next(hook)

        assert extension.execution_context.pre_execution_errors == [rejection]
        with pytest.raises(StopIteration):
            next(hook)


@pytest.mark.parametrize(
    "extension_type",
    [DjangoResourcePolicyExtension, _AdmissionGuard],
    ids=["the-enforcing-entry", "the-appended-guard"],
)
def test_an_admitted_operation_keeps_whatever_validation_published(extension_type):
    """The restatement is a restatement, not an unconditional write."""
    extension = extension_type()
    validation_error = GraphQLError("Cannot query field 'nope'.")
    extension.execution_context = SimpleNamespace(pre_execution_errors=[validation_error])

    with _armed({}, DEFAULT_RESOURCE_POLICY):
        hook = extension.on_validate()
        next(hook)
        with pytest.raises(StopIteration):
            next(hook)

    assert extension.execution_context.pre_execution_errors == [validation_error]


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


class _DriftingPolicy(ResourcePolicy):
    """A valid policy whose first read of a bound is narrow and the rest are wide.

    Every check a ``ResourcePolicy`` performs on itself happens at construction,
    so a subclass answering honestly then and differently afterwards is a policy
    that passed validation and enforces nothing. The drift starts only once
    ``_armed`` is set, which is what lets ``__post_init__`` validate real values.
    """

    def __getattribute__(self, name):
        state = object.__getattribute__(self, "__dict__")
        if name == "max_document_tokens" and state.get("_armed"):
            state["_reads"] = state.get("_reads", 0) + 1
            return 1 if state["_reads"] == 1 else 1_000_000
        return object.__getattribute__(self, name)


def test_an_explicit_extension_policy_is_read_out_once_when_it_is_accepted():
    """One operation is bounded by ONE policy, whatever its configuration answers.

    The extension used to return its explicit ``_policy`` raw from every hook:
    the armed budget got a canonical snapshot, while the pre-parse scan and the
    post-validation document walk each re-read the consumer object. A policy
    whose reads are its own code could hand those hooks a different bound than
    the one the request is actually running under - a one-token budget for the
    snapshot and a million-token budget for the scan that was supposed to
    enforce it.
    """
    drifting = _DriftingPolicy()
    object.__getattribute__(drifting, "__dict__")["_armed"] = True

    @strawberry.type
    class _Query:
        @strawberry.field
        def echo(self) -> str:
            return "ok"

    schema = strawberry.Schema(
        query=_Query,
        extensions=[lambda: DjangoResourcePolicyExtension(policy=drifting)],
    )
    result = schema.execute_sync("{ echo }")
    assert result.data is None
    assert isinstance(result.errors[0], ResourceLimitExceeded)
    assert result.errors[0].bound == "max_document_tokens"
    assert object.__getattribute__(drifting, "__dict__")["_reads"] == 1


def test_an_explicit_extension_policy_is_stored_as_an_exact_policy():
    """What the extension holds after construction is the package's own class."""
    drifting = _DriftingPolicy()
    extension = DjangoResourcePolicyExtension(policy=drifting)
    assert type(extension._policy) is ResourcePolicy
    assert extension._policy is not drifting


def test_an_explicit_extension_policy_cannot_be_replaced_or_written():
    """An accepted instance entry stays reachable, so what it holds cannot be a seam.

    ``info.schema.extensions`` hands every resolver the entries the schema was
    configured with, and an instance entry is the object itself - so the policy
    it answers with bounds the NEXT operation, not the one that reached it.
    Rebinding is refused where it is made, and the object handed out is a
    duplicate, so writing a bound on it changes only the writer's copy.
    """
    extension = DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1))

    with pytest.raises(AttributeError):
        extension._policy = ResourcePolicy(max_list_rows=999)

    handed_out = extension._policy
    handed_out.__dict__["max_list_rows"] = 999

    assert extension._policy.max_list_rows == 1
    assert extension._policy is not handed_out


@pytest.mark.parametrize(
    "attack",
    [
        lambda extension: extension.__dict__.update(
            _explicit_policy=ResourcePolicy(max_list_rows=999),
        ),
        lambda extension: extension.__dict__.clear(),
    ],
    ids=["write-an-attribute", "empty-the-instance-dictionary"],
)
def test_an_accepted_extension_policy_survives_every_write_to_the_instance(attack):
    """The accepted policy is held where no name on the extension answers with it.

    Nothing written onto the instance can stand in for it and nothing removed
    from the instance can lose it, which is the difference between detecting a
    forgery and preserving what was configured: an extension that fell back to
    the schema's policy - or to the package defaults - when its own went missing
    would answer a deleted attribute with a WIDER budget than the deployment
    accepted.
    """
    extension = DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1))
    attack(extension)
    extension.execution_context = SimpleNamespace(schema=SimpleNamespace())

    assert extension._policy.max_list_rows == 1
    assert extension._resolved_policy().max_list_rows == 1


@pytest.mark.parametrize(
    "accepted",
    [ResourcePolicy(max_list_rows=1), None],
    ids=["explicit-policy", "inherited-policy"],
)
def test_an_accepted_extension_cannot_be_reconfigured_by_running_its_constructor(accepted):
    """An accepted entry is reachable from every resolver, and so is its ``__init__``.

    A second call would nominate the budget for every later operation, which is
    the widening no write to the instance achieves either. Both supported
    configurations are closed to it, because construction is what the refusal
    reads and an extension deliberately built with no override is constructed:
    taking the presence of a policy for the record would leave the inheriting
    half of the configuration space - the half a consumer writes when they want
    their schema's bounds - the one that can be handed a ceiling after it was
    accepted.
    """
    extension = DjangoResourcePolicyExtension(policy=accepted)

    with pytest.raises(ConfigurationError, match="configured when it is constructed"):
        extension.__init__(policy=ResourcePolicy(max_list_rows=999))

    assert extension._policy == accepted


def test_an_extension_configured_with_no_policy_reads_the_schemas():
    """The absent case the preservation rule must not swallow."""
    extension = DjangoResourcePolicyExtension()
    extension.execution_context = SimpleNamespace(schema=SimpleNamespace())

    assert extension._policy is None
    assert extension._resolved_policy() is DEFAULT_RESOURCE_POLICY


def test_a_refused_reconstruction_leaves_an_inheriting_extension_inheriting():
    """Closing the constructor must not pin what the extension was never given.

    Recording the construction of an extension that has no override records
    exactly that, so the policy it enforces is still the one its schema resolves
    per operation rather than whatever was in reach when it was built.
    """
    extension = DjangoResourcePolicyExtension()

    with pytest.raises(ConfigurationError, match="configured when it is constructed"):
        extension.__init__(policy=ResourcePolicy(max_list_rows=999))

    extension.execution_context = SimpleNamespace(
        schema=SimpleNamespace(resource_policy=ResourcePolicy(max_list_rows=2)),
    )
    assert extension._policy is None
    assert extension._resolved_policy().max_list_rows == 2


def test_a_factory_entry_is_constructed_fresh_and_configured_for_every_operation():
    """Refusing a SECOND call on one instance is not refusing construction.

    A factory entry is how a consumer configures an extension per operation, so
    each operation must still get an instance of its own that accepts the policy
    it was handed.
    """

    @strawberry.type
    class _Query:
        @strawberry.field
        def rows(self, info: Info) -> list[str]:
            return list(bounded_rows(["a", "b", "c"], info, None))

    built = []

    def factory():
        extension = DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1))
        built.append(extension)
        return extension

    schema = DjangoSchema(query=_Query, extensions=[factory])
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}

    assert len(built) == 2
    assert built[0] is not built[1]
    assert all(extension._policy.max_list_rows == 1 for extension in built)


@pytest.mark.parametrize(
    "supplied",
    [DjangoResourcePolicyExtension, DjangoResourcePolicyExtension()],
    ids=["class", "instance"],
)
def test_a_consumer_supplied_extension_suppresses_the_automatic_one(supplied):
    """Two copies would charge every bound twice against the same budget."""
    assert _with_resource_policy_extension([supplied]) == ([supplied], False)


def test_the_extension_is_appended_as_a_class_when_absent():
    """A class (not an instance) is what gives each request its own charge counters."""
    assert _with_resource_policy_extension(None) == ([DjangoResourcePolicyExtension], True)


def test_extension_installation_does_not_call_consumer_iterable_truthiness():
    """A stateful list subclass cannot suppress or break automatic installation."""

    class _HostileTruthiness(list):
        def __bool__(self):
            raise RuntimeError("bool exploded")

    marker = object()
    installed, appended = _with_resource_policy_extension(_HostileTruthiness([marker]))
    assert installed == [marker, DjangoResourcePolicyExtension]
    assert appended is True


def test_an_unrelated_extension_is_preserved_alongside_the_appended_one():
    marker = object()
    assert _with_resource_policy_extension([marker]) == (
        [marker, DjangoResourcePolicyExtension],
        True,
    )


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


@pytest.mark.parametrize(
    "size",
    [
        None,
        "12",
        -1,
        True,
        _AmountNoBoundCanExceed(10**9),
    ],
    ids=[
        "absent",
        "string",
        "negative",
        "boolean",
        "int-subclass",
    ],
)
def test_an_upload_that_cannot_report_its_size_is_rejected(size):
    """Guard the ANSWER, not one spelling of the missing input.

    An unmeasurable file charged as zero bytes would be an unbounded upload that
    every byte bound reports as free - the fail-open shape this bound exists to
    avoid. ``None``, a non-integer, a negative, ``True``, and an ``int``
    SUBCLASS are all "not a size": the subclass most of all, because its own
    ``__gt__`` answers the per-file bound and its reflected ``__radd__`` decides
    what the aggregate counter becomes for every file that follows it.
    """
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query U($f: Upload!) { stash(document: $f) }",
            {"f": SimpleNamespace(size=size)},
        )
    assert caught.value.bound == "max_upload_file_bytes"


def test_a_buffer_that_advertises_its_own_byte_count_is_measured_anyway():
    """A charge is an amount the package produced, never one the value announced.

    An attribute a buffer carries is consumer code answering for a number, and
    the ``>`` that would decide the rejection is then that number's own. The
    size comes through the C buffer protocol instead, which a ``bytes`` subclass
    cannot answer for, so an amount no bound could ever exceed sits on the value
    unread.
    """

    class _Bytes(bytes):
        nbytes = _AmountNoBoundCanExceed(10**9)

    document = "query B($p: JSON!) { blob(payload: $p) }"
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            document,
            {"p": _Bytes(b"0123456789")},
            policy=ResourcePolicy(max_scalar_bytes=4),
        )
    assert caught.value.bound == "max_scalar_bytes"
    assert caught.value.charged == 10


def test_an_upload_size_descriptor_that_raises_is_rejected():
    class BrokenUpload:
        @property
        def size(self):
            raise RuntimeError("size unavailable")

    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query U($f: Upload!) { stash(document: $f) }",
            {"f": BrokenUpload()},
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


def test_resource_limit_exceeded_pickle_and_copy_fidelity():
    """ResourceLimitExceeded roundtrips through pickle, copy, and deepcopy preserving attributes."""
    exc = ResourceLimitExceeded("max_depth", 10, 15, "query depth 15 exceeds 10")
    exc.custom_tag = "tagged"

    # Pickle serialization roundtrip
    restored = pickle.loads(pickle.dumps(exc))
    assert isinstance(restored, ResourceLimitExceeded)
    assert restored.bound == "max_depth"
    assert restored.limit == 10
    assert restored.charged == 15
    assert restored.detail == "query depth 15 exceeds 10"
    assert getattr(restored, "custom_tag", None) == "tagged"
    assert str(restored) == str(exc)

    # copy and deepcopy
    copied = copy.copy(exc)
    assert isinstance(copied, ResourceLimitExceeded)
    assert copied.bound == "max_depth"
    assert copied.limit == 10
    assert copied.charged == 15
    assert copied.detail == "query depth 15 exceeds 10"
    assert getattr(copied, "custom_tag", None) == "tagged"

    deep_copied = copy.deepcopy(exc)
    assert isinstance(deep_copied, ResourceLimitExceeded)
    assert deep_copied.bound == "max_depth"
    assert deep_copied.limit == 10
    assert deep_copied.charged == 15
    assert deep_copied.detail == "query depth 15 exceeds 10"
    assert getattr(deep_copied, "custom_tag", None) == "tagged"


def test_an_untyped_container_list_is_not_classified_as_membership_list():
    """An untyped JSON list is not a typed GraphQL list, so it carries no membership bound."""
    document = "query B($p: JSON!) { blob(payload: $p) }"
    # 4 items > max_membership_items (2), but <= max_container_width (10)
    _charge(
        document,
        {
            "p": [
                1,
                2,
                3,
                4,
            ],
        },
        policy=ResourcePolicy(max_membership_items=2, max_container_width=10),
    )
    # Exceeding max_container_width (3) is rejected under max_container_width
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            document,
            {
                "p": [
                    1,
                    2,
                    3,
                    4,
                ],
            },
            policy=ResourcePolicy(max_membership_items=2, max_container_width=3),
        )
    assert caught.value.bound == "max_container_width"


def test_binary_scalar_values_are_bounded_by_max_scalar_bytes():
    """bytes, bytearray, and memoryview scalar payloads are bounded by byte length."""
    document = "query B($p: JSON!) { blob(payload: $p) }"
    _charge(document, {"p": b"short"}, policy=ResourcePolicy(max_scalar_bytes=10))
    _charge(document, {"p": bytearray(b"short")}, policy=ResourcePolicy(max_scalar_bytes=10))
    _charge(document, {"p": memoryview(b"short")}, policy=ResourcePolicy(max_scalar_bytes=10))

    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(document, {"p": b"0123456789abcde"}, policy=ResourcePolicy(max_scalar_bytes=10))
    assert caught.value.bound == "max_scalar_bytes"

    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            document,
            {"p": bytearray(b"0123456789abcde")},
            policy=ResourcePolicy(max_scalar_bytes=10),
        )
    assert caught.value.bound == "max_scalar_bytes"

    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            document,
            {"p": memoryview(b"0123456789abcde")},
            policy=ResourcePolicy(max_scalar_bytes=10),
        )
    assert caught.value.bound == "max_scalar_bytes"


def test_charge_document_accepts_none_variables():
    """charge_document safely accepts variables=None."""
    charge_document(
        DEFAULT_RESOURCE_POLICY,
        _PROBE_SCHEMA._schema,
        parse("{ echo }"),
        None,
        None,
    )


def test_field_definition_with_none_parent_type():
    """_field_definition safely handles None parent_type when schema query_type is None."""
    from django_strawberry_framework.extensions.resource_policy import _field_definition

    fake_schema = SimpleNamespace(query_type=None)
    assert _field_definition(fake_schema, None, "__schema") is None


def test_variable_default_values_are_charged_when_variable_omitted():
    """Default values declared in operation variable definitions are charged if omitted from runtime variables."""
    document = (
        'query WithDefaults($tags: [String!] = ["a", "b", "c", "d", "e"]) { echo(tags: $tags) }'
    )
    _charge(document, variables={}, policy=ResourcePolicy(max_membership_items=5))
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(document, variables={}, policy=ResourcePolicy(max_membership_items=4))
    assert caught.value.bound == "max_membership_items"
    assert caught.value.charged == 5


def test_variable_default_values_not_used_when_variable_explicitly_passed():
    """When a variable is explicitly provided, its runtime value is charged instead of the default value."""
    document = (
        'query WithDefaults($tags: [String!] = ["a", "b", "c", "d", "e"]) { echo(tags: $tags) }'
    )
    # Explicit 2 items passed should pass max_membership_items=3 even though default is 5:
    _charge(
        document,
        variables={"tags": ["a", "b"]},
        policy=ResourcePolicy(max_membership_items=3),
    )
    # Explicit 4 items passed should fail max_membership_items=3 with charged=4:
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            document,
            variables={
                "tags": [
                    "a",
                    "b",
                    "c",
                    "d",
                ],
            },
            policy=ResourcePolicy(max_membership_items=3),
        )
    assert caught.value.bound == "max_membership_items"
    assert caught.value.charged == 4


def test_memoryview_multibyte_buffer_charged_by_nbytes():
    """Multibyte memoryview payloads are bounded by true byte size (nbytes), not element count."""
    import array

    arr = array.array("i", range(10))  # 10 32-bit ints = 40 bytes
    mv = memoryview(arr)
    assert len(mv) == 10
    assert mv.nbytes == 40

    document = "query B($p: JSON!) { blob(payload: $p) }"
    _charge(document, {"p": mv}, policy=ResourcePolicy(max_scalar_bytes=40))

    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(document, {"p": mv}, policy=ResourcePolicy(max_scalar_bytes=39))
    assert caught.value.bound == "max_scalar_bytes"
    assert caught.value.charged == 40


class _LiesAfterValidating(ResourcePolicy):
    """A policy that validates honestly at construction and answers differently later.

    ``__post_init__`` reads every field through this hook, so the class validates
    itself on real values; flipping ``armed`` afterwards is what a subclass's
    reads actually are - consumer code, running whenever a seam looks at a bound.
    The returned ``int`` subclass then answers the comparison that would have
    caught it with a raw exception.
    """

    armed = False

    def __getattribute__(self, name):
        if name == "max_list_rows" and object.__getattribute__(type(self), "armed"):
            return _AmountNoBoundCanExceed(3)
        return object.__getattribute__(self, name)


class _UnreadablePolicy(ResourcePolicy):
    """A policy whose ``max_list_rows`` read raises, as a property does at any time."""

    @property
    def max_list_rows(self):
        raise RuntimeError("hostile read detonated")


def test_a_policy_subclass_is_replaced_by_an_exact_instance_at_schema_construction():
    """``isinstance`` admits a subclass, whose every field read is consumer code.

    Reading it out once here and building an exact instance is what keeps a read
    that validates honestly and answers differently afterwards from reaching a
    bound: the subclass is discarded and no seam calls it again.
    """
    hostile = _LiesAfterValidating()
    schema = DjangoSchema(query=_Probe, resource_policy=hostile)
    _LiesAfterValidating.armed = True
    try:
        assert type(schema.resource_policy) is ResourcePolicy
        assert schema.resource_policy.max_list_rows == DEFAULT_RESOURCE_POLICY.max_list_rows
    finally:
        _LiesAfterValidating.armed = False


def test_a_policy_whose_bound_cannot_be_read_is_a_typed_configuration_error():
    """A read that raises during canonicalization is a deployment fault, named as one."""
    with pytest.raises(ConfigurationError) as caught:
        DjangoSchema(query=_Probe, resource_policy=object.__new__(_UnreadablePolicy))

    assert "max_list_rows" in str(caught.value)


def test_the_armed_budget_is_not_the_policy_the_caller_armed_it_with():
    """``begin_resource_budget`` snapshots, so the caller keeps no handle on the ceiling."""
    policy = ResourcePolicy(max_list_rows=2)
    context: dict[str, Any] = {}
    token = begin_resource_budget(context, policy)
    try:
        policy.__dict__["max_list_rows"] = 999
        info = SimpleNamespace(context=context)

        assert policy_from_info(info).max_list_rows == 2
    finally:
        end_resource_budget(token)


def test_the_published_mirror_is_not_the_object_any_bound_is_read_from():
    """The mirror is documented for consumers to read, so it cannot be the authority."""
    context: dict[str, Any] = {}
    token = begin_resource_budget(context, ResourcePolicy(max_list_rows=2))
    try:
        context[DST_RESOURCE_POLICY].__dict__["max_list_rows"] = 999
        info = SimpleNamespace(context=context)

        assert policy_from_info(info).max_list_rows == 2
    finally:
        end_resource_budget(token)


def test_policy_from_info_answers_twice_with_two_objects():
    """Every read is a duplicate, so one reader's write is invisible to the next."""
    context: dict[str, Any] = {}
    token = begin_resource_budget(context, ResourcePolicy(max_list_rows=2))
    try:
        info = SimpleNamespace(context=context)
        first = policy_from_info(info)
        first.__dict__["max_list_rows"] = 999

        assert policy_from_info(info).max_list_rows == 2
        assert policy_from_info(info) is not first
    finally:
        end_resource_budget(token)


def test_the_package_default_is_never_the_object_a_miss_hands_back():
    """The fail-closed baseline is process-lived; handing it out would let one write widen it."""
    info = SimpleNamespace(context={})

    answered = policy_from_info(info)
    answered.__dict__["max_list_rows"] = 999

    assert answered is not DEFAULT_RESOURCE_POLICY
    assert policy_from_info(info).max_list_rows == DEFAULT_RESOURCE_POLICY.max_list_rows


def test_a_mirror_holding_a_policy_subclass_reads_back_as_the_package_default():
    """The unarmed fallback admits the exact class only; a subclass's reads are not ours."""
    info = SimpleNamespace(context={DST_RESOURCE_POLICY: _LiesAfterValidating()})

    assert policy_from_info(info) == DEFAULT_RESOURCE_POLICY


def test_the_pre_parse_scan_charges_an_operation_the_request_did_not_name():
    """``max_document_tokens`` is a request-level bound, and says so.

    It exists to bound the parse; the parse reads the whole document whatever
    ``operationName`` says, and no operation is identified until it has finished.
    Charging the named operation alone would name a cost nobody pays and leave the
    one somebody does pay unbounded.
    """
    document = "query Small { echo } query Big { echo echo echo echo }"
    with pytest.raises(ResourceLimitExceeded) as caught:
        scan_document_text(ResourcePolicy(max_document_tokens=6), document)

    assert caught.value.bound == "max_document_tokens"


def test_the_post_parse_walk_charges_only_the_operation_the_request_named():
    """Its counterpart: the bounds charged after the parse do filter by name."""
    document = "query Small { echo } query Big { echo echo echo echo }"
    charge_document(
        ResourcePolicy(max_selections=1),
        DjangoSchema(query=_Probe)._schema,
        parse(document),
        {},
        "Small",
    )
