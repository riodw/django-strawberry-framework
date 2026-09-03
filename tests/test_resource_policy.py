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

import copy
import math
import pickle
import time
from types import MappingProxyType, SimpleNamespace
from typing import Any

import pytest
import strawberry
from graphql import GraphQLError, parse
from graphql.language.token_kind import TokenKind
from strawberry.types import Info

from django_strawberry_framework import DjangoSchema, Upload
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions.resource_policy import (
    _CLOSE_TOKEN_KINDS,
    _OPEN_TOKEN_KINDS,
    _STRUCTURAL_DELIMITER_PAIRS,
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
    bounded_rows_async,
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


def test_an_instance_through_the_setting_slot_is_used_as_is(settings):
    """The setting slot and the explicit argument are one ladder with two spellings.

    A pre-validated ``ResourcePolicy`` behind ``RESOURCE_POLICY`` is the same
    trusted declaration the ``DjangoSchema(resource_policy=...)`` argument
    accepts, so it must resolve to exactly that instance. (Probed by the hunt:
    rejecting it here produced a typed message naming ``ResourcePolicy`` as the
    received type while claiming the value must be a ``ResourcePolicy``.)
    """
    policy = ResourcePolicy(max_depth=3)
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RESOURCE_POLICY": policy}
    assert resolve_resource_policy(None) is policy


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


def test_a_hostile_deadline_subclass_fails_closed_instead_of_crashing_the_seam():
    """A numeric SUBCLASS whose comparisons raise cannot certify its budget.

    The deadline stash is a process-internal derived value, but the context is
    consumer-owned, so a hostile numeric can sit under the key. The seam must
    fail closed on the same typed path a passed deadline takes rather than leak
    the raw comparison error out of a collection resolver.
    """

    class HostileFloat(float):
        def __gt__(self, other):
            raise RuntimeError("hostile __gt__")

        def __lt__(self, other):
            raise RuntimeError("hostile __lt__")

        def __le__(self, other):
            # ``monotonic >= stash`` dispatches to the REFLECTED ``__le__`` first
            # (a float subclass wins the reversed slot), so this is the dunder
            # that actually detonates inside the seam.
            raise RuntimeError("hostile __le__ detonated")

        def __ge__(self, other):
            raise RuntimeError("hostile __ge__ detonated")

    context = {DST_RESOURCE_DEADLINE: HostileFloat(time.monotonic())}
    with pytest.raises(ResourceLimitExceeded) as caught:
        check_deadline(SimpleNamespace(context=context))
    assert caught.value.bound == "execution_deadline_seconds"
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


def test_bounded_rows_honours_a_trusted_widening():
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    assert bounded_rows(list(range(10)), info, 4, trusted=True) == [
        0,
        1,
        2,
        3,
    ]


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


def test_bounded_rows_preserves_none():
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=2))
    assert bounded_rows(None, info) is None


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


# TODO(spec-050 slice 3): Pin the new offset/requested-limit arms at the shared
# raw-list seam; do not duplicate list-field argument validation here.
#
# Pseudocode:
#
# - Parametrize sequences and non-subscriptable iterables over omitted
#   coordinates, offset only, smaller requested limit, offset + limit, overshoot,
#   and trusted declared widening. Assert exact ``[start:stop]`` results and that
#   the shipped three-positional-argument call still binds ``declared``. Offset
#   ONLY (no requested limit) must stop at ``offset + effective_ceiling``, not
#   only the combined offset+limit shape.
# - Positive-offset arithmetic over an ASYNC iterator belongs here, not live:
#   the public list field rejects positive offset on an async-only source
#   (spec-050 Decision 8) while this seam supports it for shape completeness.
# - Pin the DECLINED sync cleanup contract: a retained sync generator truncated
#   by a window is still suspended and resumable afterward, its ``finally`` not
#   yet run. This card promises early-exit cleanup for async-only sources only,
#   so the assertion exists to make a later symmetric card an explicit flip.
# - Give the unsliceable iterable counters around ``__iter__`` / ``__next__``
#   and a patched ``islice`` seam. ``requested_limit=0`` must return ``[]``
#   without constructing islice or advancing; a positive window consumes
#   exactly offset + returned rows and never the next item.
# - Give the async-only source counters for iterator acquisition, ``__anext__``,
#   and ``aclose``. Zero limit acquires and closes once with zero advances;
#   reaching the exclusive stop closes; offset overshoot that naturally
#   exhausts does not close; source failure plus cleanup failure keeps the
#   source primary with one note; cleanup-only failure remains primary. Cover
#   a source holding EXACTLY ``offset + limit`` rows beside one holding fewer,
#   so an accepted-stop close is distinguished from an observed natural
#   exhaustion. The zero-advance witness is the iterator's OWN ``aclose``
#   counter, never an async generator's body ``finally``: ``aclose()`` before
#   the first advance does not enter the body, so no ``finally`` runs.
# - Spy on ``check_deadline`` and ``effective_bound``. Each coordinate-bearing
#   invocation calls each shared policy seam once before any source advance,
#   and relation-list callers with no coordinates retain the old prefix bound.


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


def test_a_malformed_document_is_left_to_the_real_parser():
    """Swallowing the lexer error keeps the accurate syntax diagnostic."""
    scan_document_text(DEFAULT_RESOURCE_POLICY, "{ foo(bar: 'single quotes') }")


def test_a_document_that_is_both_oversized_and_malformed_is_rejected_on_size():
    """Size is charged per token, so it fires before the lexer reaches the garbage."""
    policy = ResourcePolicy(max_document_tokens=3)
    with pytest.raises(ResourceLimitExceeded) as caught:
        scan_document_text(policy, "{ a b c d e 'garbage' }")
    assert caught.value.bound == "max_document_tokens"


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
class _Probe:
    """A minimal schema whose only job is to give the walker real types."""

    fauxes: list[_NotAConnection]
    scalar_edges: _ScalarEdges

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


def test_extension_installation_does_not_call_consumer_iterable_truthiness():
    """A stateful list subclass cannot suppress or break automatic installation."""

    class _HostileTruthiness(list):
        def __bool__(self):
            raise RuntimeError("bool exploded")

    marker = object()
    installed = _with_resource_policy_extension(_HostileTruthiness([marker]))
    assert installed == [marker, DjangoResourcePolicyExtension]


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
