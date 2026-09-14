"""``ResourcePolicy`` - the one immutable execution resource budget for a request.

Spec: ``docs/SPECS/spec-047-resource_policy-0_0_14.md``.
Target release: ``0.0.14``.

A GraphQL endpoint's cost is not bounded by its schema. A single small document
can ask for an unbounded number of rows, and a single small *variable* payload
can ask for an unbounded number of ids, filter terms, or upload bytes. Both
halves of that are bounded here, by one object rather than by settings reads
scattered across resolvers:

- the **document budget** - tokens, structural nesting depth, expanded selection
  and alias counts, and the aggregate collection cost the document would drive;
- the **value budget** - total input nodes, container nesting depth, container
  width, membership-list items, node-refetch ids, per-mutation and per-request
  relation ids, nested input rows, upload count / per-file bytes / aggregate
  bytes, and scalar byte size; and
- the **collection bounds** the fields themselves enforce - maximum page size for
  a connection, maximum rows for a raw list.

Three properties are contractual:

**Normalized once.** ``resolve_resource_policy`` validates every bound at schema
construction (``schema.py::DjangoSchema``), so an invalid deployment fails at
startup and no resolver re-reads or re-validates a setting per request.

**Immutable and armed for the whole operation.** The resolved policy is armed as
the operation's authoritative budget by ``begin_resource_budget`` and read back
by ``policy_from_info`` and ``check_deadline``. The object is a frozen
dataclass, so a resolver cannot widen the request's own budget by mutating it,
and the authority is a ``ContextVar`` rather than a request-context key, so a
resolver cannot widen it by REPLACING it either. The same call publishes the
policy and its derived deadline under ``DST_RESOURCE_POLICY`` /
``DST_RESOURCE_DEADLINE``, mirroring the optimizer's ``DST_OPTIMIZER_*`` context
seam; those keys are a consumer-readable mirror, and no enforcement seam trusts
them while a budget is armed.

**Narrowing-only per field.** ``effective_bound`` is how a field applies its own
declared maximum: the tighter of the field's value and the request policy wins.
The schema-construction policy IS the trusted declaration - it is the only place
that may widen a package default - and a per-field value may widen it only under
an explicit ``trusted=True`` opt-in at the call site.

Fail-closed defaults. Every bound is a positive integer with a package default;
there is no "disable this bound" spelling, and a context with no stashed policy
reads back ``DEFAULT_RESOURCE_POLICY`` rather than "unbounded". The one optional
bound is ``execution_deadline_seconds``, which defaults to ``None`` because a
wall-clock deadline that a deployment did not choose is a correctness hazard, not
a safety one.
"""

from __future__ import annotations

import math
import time
from collections.abc import Mapping
from contextvars import ContextVar
from dataclasses import dataclass, fields, replace
from itertools import islice
from typing import Any

from graphql import GraphQLError

from .conf import resource_policy_setting
from .exceptions import ConfigurationError, DjangoStrawberryFrameworkError, describe_value
from .utils.context import clear_context_key, get_context_value, stash_on_context
from .utils.errors import coded_error_extensions
from .utils.policies import resolve_policy
from .utils.querysets import is_async_only_iterable

__all__ = (
    "DEFAULT_RESOURCE_POLICY",
    "DST_RESOURCE_DEADLINE",
    "DST_RESOURCE_POLICY",
    "RESOURCE_LIMIT_ERROR_CODE",
    "ResourceLimitExceeded",
    "ResourcePolicy",
    "begin_resource_budget",
    "bounded_rows",
    "bounded_rows_async",
    "check_deadline",
    "clear_resource_context",
    "effective_bound",
    "end_resource_budget",
    "policy_from_info",
    "resolve_resource_policy",
    "stash_resource_policy",
    "validate_collection_bound",
    "validate_trusted_flag",
)


#: The single wire-visible ``extensions.code`` every resource rejection carries.
#: Sync HTTP, async HTTP, and WebSocket queries / mutations all route through
#: Strawberry's ``execute``, which renders the rejection as an ordinary GraphQL
#: error entry, so one code is what makes them recognizable as the same failure
#: rather than three. A rejected WebSocket SUBSCRIPTION is refused just as
#: hard - nothing is executed - but Strawberry's ``subscribe`` path does not
#: convert a pre-execution exception into an error entry, so that client sees
#: the operation complete without data instead of this code.
RESOURCE_LIMIT_ERROR_CODE = "RESOURCE_LIMIT_EXCEEDED"

#: Request-context keys, mirroring the optimizer's ``DST_OPTIMIZER_*`` seam.
DST_RESOURCE_POLICY = "dst_resource_policy"
DST_RESOURCE_DEADLINE = "dst_resource_deadline"


class ResourceLimitExceeded(GraphQLError, DjangoStrawberryFrameworkError):  # noqa: N818 - the wire-visible name of a bound rejection, not an internal error class
    """A request exceeded one of its resource bounds; nothing was executed.

    Multiple-inherits ``GraphQLError`` (so the rejection travels the wire as a
    normal error entry carrying ``extensions.code`` wherever Strawberry renders
    a pre-execution failure into the response envelope, which is every transport
    except a WebSocket subscription - see ``RESOURCE_LIMIT_ERROR_CODE``) and the
    package base (so a consumer can
    ``except DjangoStrawberryFrameworkError`` alongside every other framework
    error). The ``SyncMisuseError`` precedent.

    ``bound`` names the ``ResourcePolicy`` field that rejected, ``limit`` is its
    configured value, and ``charged`` is the amount the request asked for. All
    three ride in ``extensions`` so a client can act on the rejection without
    parsing prose.
    """

    def __init__(
        self,
        bound: str,
        limit: int,
        charged: int,
        detail: str,
    ) -> None:
        super().__init__(
            f"Request exceeds the {bound} resource bound: {detail} "
            f"({charged} charged, {limit} allowed).",
            extensions=coded_error_extensions(
                RESOURCE_LIMIT_ERROR_CODE,
                bound=bound,
                limit=limit,
                charged=charged,
            ),
        )
        self.bound = bound
        self.limit = limit
        self.charged = charged
        self.detail = detail

    def __reduce__(self) -> tuple[object, ...]:
        """Preserve constructor arguments and instance state across pickle roundtrips."""
        return (
            self.__class__,
            (
                self.bound,
                self.limit,
                self.charged,
                self.detail,
            ),
            self.__dict__,
        )


def _is_valid_deadline(value: Any) -> bool:
    """Whether ``value`` sits in the deadline domain (``None`` is decided by the caller).

    The type test is EXACT, not ``isinstance``. The value is
    deployment-supplied, and a numeric SUBCLASS is a hostile configuration
    object whose dunders are consumer code the policy would then carry
    everywhere it uses the deadline: a raising ``__le__`` / ``__gt__`` replaces
    the typed ``ConfigurationError`` with a raw error out of schema
    construction, a raising ``__ceil__`` / ``__format__`` replaces the typed
    ``ResourceLimitExceeded`` with one out of a collection resolver, a lying
    ``__float__`` answers this very check for a value it does not hold, and a
    reflected ``__radd__`` - which takes priority over ``float``'s own - turns
    ``stash_resource_policy``'s ``time.monotonic() + deadline`` into ``nan``,
    silently disarming the deadline of a policy that was accepted. Admitting
    only the built-in types is what keeps every later comparison, conversion,
    arithmetic and format on a value the package owns.
    """
    if type(value) is not int and type(value) is not float:
        return False
    try:
        return math.isfinite(value) and value > 0
    except OverflowError:
        # ``isfinite`` overflows converting a huge int, which is therefore not
        # classifiable as a positive number of seconds: the domain check answers
        # False and the typed rejection fires at the caller.
        return False


def _require_positive_int(value: Any, label: str) -> None:
    """Reject a non-positive-integer bound under whatever name declared it.

    The package's bound-domain rule, stated once for the two spellings of the
    same rule: a ``ResourcePolicy`` field validated at construction and a
    field-declared collection bound validated at its factory line.

    The type test is EXACT, which is what rejects ``True``
    (``isinstance(True, int)`` is ``True``, and a bound of ``True`` would
    silently become ``1``) and equally what keeps a hostile ``int`` subclass out
    of a policy. A subclass whose ``__lt__`` raises would replace this typed
    rejection with a raw error; worse, one whose ``__lt__`` answers normally
    would be STORED, and every later use of the bound then dispatches consumer
    dunders - ``narrowed``'s ``>`` comparison, and the ``limit`` / ``charged``
    values ``ResourceLimitExceeded`` formats into the message and ``extensions``
    of every rejection the bound drives. Admitting only the built-in type is
    what keeps those on values the package owns.
    """
    if type(value) is not int or value < 1:
        raise ConfigurationError(
            f"{label} must be a positive integer; got {describe_value(value)}.",
        )


@dataclass(frozen=True)
class ResourcePolicy:
    """The immutable per-request resource budget.

    Constructed once (``resolve_resource_policy``) and read many times. Every
    field is a positive ``int`` except ``execution_deadline_seconds``, which is
    ``None`` (no deadline) or a positive number of seconds.

    The document bounds:

    ``max_document_tokens``
        Lexical tokens in the raw document, counted before it is parsed. The
        first bound a request meets, and the only one that can protect
        graphql-core's own recursive parser.
    ``max_depth``
        Maximum structural nesting - ``{``, ``(``, ``[`` - again counted before
        the parse. Input-object and argument nesting therefore count toward
        depth alongside selection-set nesting; the bound is deliberately
        structural rather than selection-only because a bound applied after the
        parse cannot stop the parse from recursing.
    ``max_selections``
        Field selections after fragment expansion, summed across the operation.
        A fragment spread is charged wherever it is spread, so spreading one
        fragment ten times costs ten times.
    ``max_aliases``
        Aliased field selections after fragment expansion. The same expensive
        field under many aliases is charged once per alias.
    ``max_collection_cost``
        The multiplicative row cost of the document: every collection selection
        contributes the product of its own page bound and those of its
        ancestors. This is the bound that sees "100 categories x 100 items each",
        and it is the only bound that grows with NESTING rather than with any one
        collection. It is a SHAPE bound, not a row-count promise: the rows a
        request can actually return are bounded per collection by
        ``max_page_size`` / ``max_list_rows``, and this bound exists to stop the
        product of those from compounding without limit down a deep document. Its
        default is correspondingly generous - a legitimate four-level document
        whose pages are all left unspecified already charges 10**8 - because a
        bound that rejects ordinary documents gets raised to infinity by the
        first deployment that meets it.

    The collection bounds fields enforce at resolve time:

    ``max_page_size``
        Ceiling on a connection's effective ``relay_max_results``.
    ``max_list_rows``
        Ceiling on the returned rows and accepted skip (``offset``) for a
        raw (non-Relay) list field. This is an accepted-coordinate and
        returned-row ceiling, not a guarantee on total physical database
        rows scanned.

    The value bounds, charged over coerced-shape input before any id is decoded
    and before any queryset is built:

    ``max_input_nodes``
        Every scalar, list, and object node in the request's argument values.
    ``max_container_width``
        The widest single list or input object.
    ``max_value_depth``
        The deepest chain of nested lists / input objects in one argument value.
        ``max_depth`` bounds nesting spelled out in the document TEXT; a value
        arriving through a variable never passes that scan, so a 10,000-deep
        list-of-list-of-... payload is bounded here or nowhere. It is what stops
        a value the walker must traverse from being arbitrarily deep even while
        each level stays narrow and the node total stays small.
    ``max_membership_items``
        Items in one membership list (an ``in`` lookup and its relatives).
    ``max_node_ids``
        Ids in one Relay node-refetch list.
    ``max_relation_ids_per_mutation`` / ``max_relation_ids_total``
        Relation ids in one mutation field, and across the whole request.
    ``max_nested_rows``
        Rows in one nested input-object list (a nested serializer / formset
        payload).
    ``max_upload_count`` / ``max_upload_file_bytes`` / ``max_upload_total_bytes``
        Files in the request, bytes in the largest file, and bytes in all of
        them. The transport body cap (``MAX_REQUEST_BODY_BYTES``) does not cover
        these: a multipart body is deliberately never materialized there.
    ``max_scalar_bytes``
        UTF-8 bytes in one scalar value, for the parsers and validators whose
        cost is superlinear in their input length.

    ``execution_deadline_seconds``
        Optional wall-clock budget for the operation. Cooperative: every seam
        that is about to hand work to the database calls ``check_deadline``
        first - ``bounded_rows`` (both raw-list spellings),
        ``connection.py::DjangoConnection.resolve_connection`` (the head every
        connection shape passes through), the Relay refetch fields
        (``relay.py::DjangoNodeField`` / ``DjangoNodesField``), and the write
        pipelines (``mutations/resolvers.py::run_write_pipeline_sync``) before
        their transaction opens. It is not a preemptive
        timeout and does not claim to be one - nothing in-process can interrupt
        a query already handed to the database driver, so what the deadline buys
        is that the request starts no MORE work.
    """

    max_document_tokens: int = 4_000
    max_depth: int = 20
    max_selections: int = 500
    max_aliases: int = 100
    max_collection_cost: int = 1_000_000_000
    max_page_size: int = 100
    max_list_rows: int = 100
    max_input_nodes: int = 5_000
    max_container_width: int = 1_000
    max_value_depth: int = 20
    max_membership_items: int = 500
    max_node_ids: int = 200
    max_relation_ids_per_mutation: int = 200
    max_relation_ids_total: int = 1_000
    max_nested_rows: int = 200
    max_upload_count: int = 10
    max_upload_file_bytes: int = 10 * 1024 * 1024
    max_upload_total_bytes: int = 25 * 1024 * 1024
    max_scalar_bytes: int = 65_536
    execution_deadline_seconds: float | None = None

    def __post_init__(self) -> None:
        """Validate every bound at construction, so an invalid policy cannot exist.

        Validation lives in ``__post_init__`` rather than in the settings reader
        because a policy built directly (``DjangoSchema(resource_policy=...)``,
        or a ``narrowed`` copy) must be validated on exactly the same terms as
        one built from settings - one gate, not two that can drift.
        """
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name == "execution_deadline_seconds":
                if value is None or _is_valid_deadline(value):
                    continue
                raise ConfigurationError(
                    "ResourcePolicy.execution_deadline_seconds must be None or a "
                    f"positive number of seconds; got {describe_value(value)}.",
                )
            _require_positive_int(value, f"ResourcePolicy.{field.name}")

    def narrowed(self, **overrides: Any) -> ResourcePolicy:
        """Return a copy with ``overrides`` applied, rejecting any that widen a bound.

        The narrowing contract in one place: a caller that holds a policy may
        tighten it freely and may never loosen it. Used by any surface that
        derives a stricter budget from the request's own - the schema policy
        stays the ceiling.

        ``execution_deadline_seconds`` narrows from ``None`` (no deadline) to any
        positive value, and from a value only downward; widening it back to
        ``None`` is a widening like any other.
        """
        known = {field.name for field in fields(self)}
        for name in overrides:
            if name not in known:
                raise ConfigurationError(
                    f"ResourcePolicy has no bound named {name!r}.",
                )
        candidate = replace(self, **overrides)
        for name in overrides:
            current = getattr(self, name)
            value = getattr(candidate, name)
            if name == "execution_deadline_seconds":
                widens = value is None and current is not None
                widens = widens or (value is not None and current is not None and value > current)
            else:
                widens = value is not None and current is not None and value > current
            if widens:
                raise ConfigurationError(
                    f"ResourcePolicy.{name} may only be narrowed: the request policy "
                    f"allows {current!r} and the override asks for {value!r}. Widen the "
                    "schema-construction policy instead.",
                )
        return candidate


#: The package's fail-closed baseline, used whenever no policy has been resolved
#: onto the request context (a plain ``strawberry.Schema``, a resolver invoked
#: outside an operation, a frozen context that refused the stash).
DEFAULT_RESOURCE_POLICY = ResourcePolicy()


def resolve_resource_policy(explicit: ResourcePolicy | Mapping[str, Any] | None) -> ResourcePolicy:
    """Normalize the deployment's policy once, at schema construction.

    Precedence, highest first: the ``DjangoSchema(resource_policy=...)``
    argument, the ``DJANGO_STRAWBERRY_FRAMEWORK["RESOURCE_POLICY"]`` mapping, and
    the package defaults. A ``ResourcePolicy`` instance passed explicitly is used
    as-is (it has already validated itself); a mapping from either source is
    applied over the package defaults so a deployment overrides only the bounds
    it cares about.

    Both override sources are *trusted declarations* and may therefore widen a
    package default - that is the distinction the narrowing rule draws between a
    deployment's deliberate choice and a per-field value.

    The normalization contract itself is the shared
    ``utils/policies.py::resolve_policy``, stated once alongside
    ``error_policy.py::resolve_error_policy``, which resolves by the same
    ladder.
    """
    return resolve_policy(
        explicit,
        policy_cls=ResourcePolicy,
        default=DEFAULT_RESOURCE_POLICY,
        read_setting=resource_policy_setting,
        display_name="resource policy",
        unit="bound",
    )


@dataclass(frozen=True)
class _RequestBudget:
    """One operation's authoritative budget: its policy and its absolute deadline.

    Both are established once, at ``on_operation`` entry, and travel together so
    that no seam can read a deadline derived from a policy other than the one it
    is about to enforce.
    """

    policy: ResourcePolicy
    deadline: float | None


#: The budget in force for the CURRENT operation, or ``None`` when nothing armed
#: one here.
#:
#: The published ``DST_RESOURCE_*`` keys cannot be the authority, because they
#: live on the CONSUMER's ``info.context`` and every resolver in the request can
#: write it. Replacing ``DST_RESOURCE_DEADLINE`` with a future scalar disarms
#: ``check_deadline``; replacing ``DST_RESOURCE_POLICY`` with a wider
#: ``ResourcePolicy`` widens ``max_list_rows`` - both the returned-row bound and
#: the accepted ``offset`` ceiling ``list_field.py`` derives from it - and
#: ``max_page_size``, for the rest of the operation and without passing
#: ``narrowed``. Neither needs hostile intent: an application context key or a
#: middleware that reuses a generic string name collides just as effectively.
#:
#: A ``ContextVar`` is not reachable by writing the request context, is scoped
#: per task under asyncio and per thread otherwise, and propagates across
#: ``sync_to_async`` / ``async_to_sync``, so it is armed wherever the package's
#: own collection seams run. The ``ContextVar``-over-stash idiom is the
#: optimizer's (``optimizer/_context.py``'s ``_active_strictness``), adopted for
#: the same reason: a per-execution answer a context stash cannot be trusted to
#: give.
#:
#: The published keys stay exactly as spec-047 shipped them, as a mirror a
#: consumer can read; they are also the fallback for a caller that publishes a
#: policy without arming one (a direct ``stash_resource_policy``, or a plain
#: ``strawberry.Schema`` with no extension), which is a context no resolver of
#: this package's is running inside.
_active_budget: ContextVar[_RequestBudget | None] = ContextVar(
    "django_strawberry_framework_resource_budget",
    default=None,
)


def _absolute_deadline(policy: ResourcePolicy) -> float | None:
    """The monotonic instant ``policy``'s budget ends, or ``None`` for no deadline.

    ``execution_deadline_seconds`` is an exact built-in by construction
    (:func:`_is_valid_deadline`), so this addition is plain ``float``
    arithmetic and cannot be redirected through a consumer's ``__radd__``.
    """
    seconds = policy.execution_deadline_seconds
    return None if seconds is None else time.monotonic() + seconds


def _publish_budget_mirror(context: Any, policy: ResourcePolicy, deadline: float | None) -> None:
    """Write the consumer-readable mirror of a budget onto the request context."""
    stash_on_context(context, DST_RESOURCE_POLICY, policy)
    stash_on_context(context, DST_RESOURCE_DEADLINE, deadline)


def stash_resource_policy(context: Any, policy: ResourcePolicy) -> None:
    """Publish ``policy`` (and its derived deadline) onto the request context.

    The consumer-readable mirror, and only that. :func:`begin_resource_budget`
    is what arms the budget the enforcement seams actually read; a caller that
    publishes without arming leaves the seams on their fallback, which reads
    this mirror back.
    """
    _publish_budget_mirror(context, policy, _absolute_deadline(policy))


def begin_resource_budget(context: Any, policy: ResourcePolicy) -> Any:
    """Arm ``policy`` as this operation's budget and publish it; returns the reset token.

    One derived absolute deadline reaches both the armed budget and the
    published mirror, so the authority and the mirror cannot disagree about when
    the operation's budget ends. :func:`end_resource_budget` closes the scope,
    restoring whatever budget an enclosing operation had armed.
    """
    deadline = _absolute_deadline(policy)
    _publish_budget_mirror(context, policy, deadline)
    return _active_budget.set(_RequestBudget(policy, deadline))


def end_resource_budget(token: Any) -> None:
    """Disarm the budget armed by :func:`begin_resource_budget`."""
    _active_budget.reset(token)


def _effective_deadline(armed: float | None, mirror: Any) -> Any:
    """The tighter of the operation's own deadline and a consumer-written one.

    The narrowing rule the rest of the module already states for bounds
    (``effective_bound``, ``ResourcePolicy.narrowed``), applied to the one piece
    of budget state a consumer can write: a resolver that stashes an EARLIER
    instant under ``DST_RESOURCE_DEADLINE`` is shortening its own request, which
    it is always entitled to do; one that stashes a later instant, clears the
    key, or writes a value no comparison can order is asking to run past the
    budget the operation started with, which no caller is entitled to. The armed
    value is the ceiling either way, so the seam cannot be widened by anything
    reachable from ``info.context``.
    """
    if not isinstance(mirror, (int, float)) or isinstance(mirror, bool):
        return armed
    if armed is None:
        return mirror
    try:
        return mirror if mirror < armed else armed
    except Exception:
        # A hostile numeric SUBCLASS cannot be ordered against the armed
        # deadline, so it cannot be shown to narrow it: the operation keeps the
        # deadline it started with rather than adopting an unorderable one.
        return armed


def clear_resource_context(context: Any) -> None:
    """Remove both resource keys, so a reused ``context_value`` cannot leak a deadline."""
    clear_context_key(context, DST_RESOURCE_POLICY)
    clear_context_key(context, DST_RESOURCE_DEADLINE)


def policy_from_info(info: Any) -> ResourcePolicy:
    """Return the request's policy, or the package default when none was published.

    The armed budget outranks the published mirror, and is consulted without
    reference to ``info`` at all: a resolver that rewrites ``DST_RESOURCE_POLICY``
    to widen ``max_list_rows`` for the rest of its own operation changes nothing
    that any bound reads. The mirror answers only where no budget is armed,
    which is a context none of this package's collection seams runs inside.

    Fail-closed by construction: the miss path returns
    ``DEFAULT_RESOURCE_POLICY``, never ``None``. A field consulting the policy is
    therefore always bounded, including under a plain ``strawberry.Schema`` that
    never installed the extension, and never needs a ``None`` branch of its own.
    """
    budget = _active_budget.get()
    if budget is not None:
        return budget.policy
    value = get_context_value(getattr(info, "context", None), DST_RESOURCE_POLICY)
    return value if isinstance(value, ResourcePolicy) else DEFAULT_RESOURCE_POLICY


def check_deadline(info: Any) -> None:
    """Raise if the operation's optional wall-clock deadline has already passed.

    Cooperative and called at the collection resolvers' pre-query seam, which is
    the last point before the request hands work to the database. The armed
    budget is the ceiling: a resolver may SHORTEN its own request by stashing an
    earlier instant under ``DST_RESOURCE_DEADLINE``, and cannot lengthen or
    clear it (:func:`_effective_deadline`). Where no budget is armed, the
    published mirror is all there is and answers alone.

    Guarding the *answer* rather than a spelling of the input: only a deadline
    that is a real number leaves the request running, so an absent, cleared, or
    non-numeric one leaves it running rather than rejecting it, while a deadline
    that has passed - and equally one that is numeric but NOT FINITE, which no
    configured policy can derive and which no comparison can certify the request
    is inside - always rejects.

    The rejection reports the CONFIGURED budget, never the clock: ``limit`` is
    the policy's own ``execution_deadline_seconds`` and ``charged`` is one second
    past it (the "exceeded an unmeasurable-in-integers budget" spelling this
    module already uses for an upload whose size cannot be read). The monotonic
    deadline and the overrun are process-internal timings a client can neither
    act on nor verify, and a wire field named ``limit`` carrying a monotonic
    timestamp is worse than useless - it reads as a bound the deployment never
    configured.
    """
    budget = _active_budget.get()
    mirror = get_context_value(getattr(info, "context", None), DST_RESOURCE_DEADLINE)
    deadline = mirror if budget is None else _effective_deadline(budget.deadline, mirror)
    if not isinstance(deadline, (int, float)) or isinstance(deadline, bool):
        return
    try:
        expired = not math.isfinite(deadline) or time.monotonic() >= deadline
    except Exception:
        # A numeric SUBCLASS whose conversion or comparison raises is a hostile
        # mirror shape: the seam cannot certify the request inside its budget,
        # so it fails closed on the same typed path a passed deadline takes
        # rather than leaking the raw arithmetic error out of a collection
        # resolver.
        expired = True
    if not expired:
        return
    source = budget.policy if budget is not None else policy_from_info(info)
    configured = source.execution_deadline_seconds
    # A stashed deadline whose policy carries none is only reachable by writing
    # the key by hand: reject (the deadline HAS passed) and say the budget is
    # unknown rather than inventing a number for it.
    seconds = math.ceil(configured) if configured is not None else 0
    budget = f"{configured} seconds" if configured is not None else "unknown"
    raise ResourceLimitExceeded(
        "execution_deadline_seconds",
        seconds,
        seconds + 1,
        f"the operation exceeded its configured execution deadline ({budget}) "
        "before this collection reached the database",
    )


def _raw_list_bound(info: Any, declared: int | None, *, trusted: bool = False) -> int:
    """Deadline check plus the effective raw-list row bound, spelled once for both colors.

    ``bounded_rows`` and ``bounded_rows_async`` enforce the same seam - the last
    look at the clock before rows are fetched, then the tighter of
    ``max_list_rows`` and the field's own declaration - so neither execution
    color can drift onto a different bound than the other.
    """
    check_deadline(info)
    return effective_bound(policy_from_info(info).max_list_rows, declared, trusted=trusted)


def _windowed_rows(
    result: Any,
    info: Any,
    declared: int | None = None,
    *,
    offset: int | None = None,
    requested_limit: int | None = None,
    trusted: bool = False,
) -> Any:
    """Bound a raw list and window it to coordinates the caller has already validated.

    The seam under ``bounded_rows``: the same ceiling, plus the ``offset`` /
    ``requested_limit`` pair a ``DjangoListField`` request carries. ``offset``
    defines the skip (``start``, defaulting to 0) and ``requested_limit`` the
    returned-row window (defaulting to the effective ``limit``); together they
    name the slice ``start:stop`` where ``stop = start + window``. Those bounds
    are an accepted-coordinate ceiling on skipped and returned items, not a
    guarantee on total physical rows scanned by the underlying database query.

    Package-private because a coordinate pair is a claim this seam cannot check:
    a window wider than the request's own ceiling would silently widen the bound
    ``bounded_rows`` advertises to everyone who imports it.
    ``list_field.py::_normalize_list_arguments`` is the single owner of that
    check - it rejects a non-integer, negative, or over-ceiling value with the
    typed, argument-named error a client can act on, before any of it reaches
    here - so the exported helper stays coordinate-free and unconditionally
    bounded rather than growing a second ceiling with a second error contract.
    """
    limit = _raw_list_bound(info, declared, trusted=trusted)
    if result is None:
        return None
    if offset is None and requested_limit is None:
        try:
            return result[:limit]
        except (TypeError, KeyError):
            # A relation accessor can hand back a non-subscriptable iterable (a
            # consumer-assigned sequence proxy, a custom manager's cached rows).
            # Falling back to ``islice`` bounds it rather than letting it through:
            # the alternative to slicing an unsliceable value is NOT "return it
            # whole", which would be a bound that silently stops applying to
            # exactly the shapes nobody anticipated. ``KeyError`` joins
            # ``TypeError`` because a MAPPING-shaped result - a plain ``dict``, or a
            # dict subclass whose ``__getitem__`` guards its keys - answers a slice
            # subscript with ``KeyError`` on interpreters where slices hash, and a
            # bound seam must never let that raw ``KeyError`` escape a resolver.
            return list(islice(result, limit))

    start = offset if offset is not None else 0
    window = requested_limit if requested_limit is not None else limit
    stop = start + window
    if window == 0:
        try:
            return result[start:start]
        except (TypeError, KeyError):
            return []
    try:
        return result[start:stop]
    except (TypeError, KeyError):
        return list(islice(result, start, stop))


def bounded_rows(
    result: Any,
    info: Any,
    declared: int | None = None,
    *,
    trusted: bool = False,
) -> Any:
    """Apply the request's raw-list row bound to whatever a collection resolver produced.

    The one place a raw (non-Relay) list is bounded, shared by the root
    ``DjangoListField`` and by the generated many-side relation resolvers, so
    both spellings of "a list of rows with no cursor" carry the same ceiling.
    The bound is the tighter of ``ResourcePolicy.max_list_rows`` and the field's
    own ``declared`` maximum unless the field declared ``trusted=True``. It is an
    accepted-row ceiling on what the response can carry, not a guarantee on total
    physical rows scanned by the underlying database query.

    It is applied by SLICING, so a ``QuerySet`` carries the bound into SQL as
    ``LIMIT`` and is never evaluated unbounded; a value that is already a
    materialized sequence (a consumer resolver's return, or Django's prefetch
    cache) is truncated in Python, which cannot un-fetch those rows but does
    stop the response from serializing them. Non-row collections follow standard
    Python slice semantics: sequences like ``str`` or ``bytes`` are sliced directly,
    while mappings (e.g. ``dict``) fall back via ``itertools.islice`` to return a
    sliced list of keys.

    A raw list is the one collection shape Relay pagination does not bound, so
    this is the only thing between a client and the whole table. It is
    unconditional: there is no argument or configuration that turns it off, only
    values that make it larger. Nothing a caller passes here can widen it - the
    client page coordinates a ``DjangoListField`` request carries ride on
    ``_windowed_rows``, below this surface and behind that field's own
    validation.
    """
    return _windowed_rows(result, info, declared, trusted=trusted)


def _attach_cleanup_note(primary_error: BaseException, note: str) -> None:
    """Record a cleanup diagnostic on an error that is already being propagated.

    ``BaseException.add_note`` is 3.11+, and cleanup runs inside ``finally``
    blocks: on the 3.10 support floor the resulting ``AttributeError`` would
    REPLACE the error this call exists to preserve. Writing the ``__notes__``
    list the note protocol is built on is what ``add_note`` does on 3.11+ (same
    list, same traceback rendering) and is the only form that carries the
    diagnostic across the whole supported range.

    The note is an attachment, never a failure of its own: a hostile note
    surface on the primary error (an unreadable or unassignable ``__notes__``)
    must not mask the error the caller is already propagating.
    """
    try:
        notes = [*getattr(primary_error, "__notes__", ())]
        notes.append(note)
        primary_error.__notes__ = notes
    except Exception:
        pass


def _is_cleanup_diagnostic(error: BaseException) -> bool:
    """Say whether a cleanup failure may be demoted to a note on the primary error.

    Only an ordinary ``Exception`` may. ``CancelledError``, ``KeyboardInterrupt``,
    ``SystemExit`` and ``GeneratorExit`` are control signals addressed to the
    task, not diagnostics about a source: demoting one would let a cancelled
    request finish as an ordinary field error, reporting a completed operation
    to a client whose task was torn down mid-cleanup. They keep precedence over
    the primary error, which stays reachable as their ``__context__``.
    """
    return isinstance(error, Exception)


async def _close_async_iterator(
    iterator: Any,
    *,
    primary_error: BaseException | None = None,
    caller: str = "bounded_rows_async",
) -> None:
    """Safely invoke ``iterator.aclose()`` if present.

    When ``primary_error`` is provided (iteration failed), ordinary cleanup
    errors are attached to ``primary_error.__notes__`` rather than replacing the
    primary error. When ``primary_error`` is None (iteration completed normally
    or short-circuited), cleanup errors are propagated directly. A control
    signal raised by ``aclose`` propagates either way.
    """
    try:
        close = getattr(iterator, "aclose", None)
        if close is not None:
            await close()
    except BaseException as close_error:
        if primary_error is None or not _is_cleanup_diagnostic(close_error):
            raise
        _attach_cleanup_note(
            primary_error,
            f"{caller} iterator cleanup failed: {close_error!r}",
        )


async def _cleanup_rejected_async_iterable(
    iterable: Any,
    primary_error: BaseException,
    *,
    caller: str,
) -> None:
    """Close an async-only source that is being rejected before it is ever advanced.

    Sits below every caller that can reject such a source: the list field's
    non-queryset and argument rejections, and this module's own pre-iteration
    bound check. An iterator that has not yet produced an item can still own an
    open external resource, so the rejection owes it a close even though no row
    was ever requested.

    The rejection stays primary throughout. Acquiring the iterator is itself a
    consumer call that can fail, and when it does the failure becomes a note on
    the rejection rather than the error the caller sees - the same posture
    ``_close_async_iterator`` takes for a failing ``aclose``, and for the same
    reason: the caller is already propagating the useful failure. Both notes
    name ``caller``, because more than one seam reaches this one and a note that
    cannot say which produced it describes nothing. A control signal raised by
    acquisition is not that kind of failure and propagates.
    """
    try:
        iterator = aiter(iterable)
    except BaseException as aiter_err:
        if not _is_cleanup_diagnostic(aiter_err):
            raise
        _attach_cleanup_note(
            primary_error,
            f"{caller} iterator acquisition failed: {aiter_err!r}",
        )
        return
    await _close_async_iterator(
        iterator,
        primary_error=primary_error,
        caller=caller,
    )


async def _windowed_rows_async(
    result: Any,
    info: Any,
    declared: int | None = None,
    *,
    offset: int | None = None,
    requested_limit: int | None = None,
    trusted: bool = False,
) -> Any:
    """Bound a possibly async-iterable result and window it to validated coordinates.

    The async seam under ``bounded_rows_async``, carrying the same client page
    coordinates ``_windowed_rows`` does and behind the same caller-owned
    validation. For async-only iterables the coordinates define an
    accepted-coordinate and returned-row ceiling rather than a database
    row-scan guarantee: the helper discards exactly ``offset`` items, collects at
    most ``window`` items (where ``window`` is the prevalidated
    ``requested_limit``, defaulting to the effective limit), and closes the
    iterator early without over-requesting subsequent items. Synchronous
    iterables fall back to ``_windowed_rows``, preserving standard Python slice
    semantics (including character/byte slicing for ``str``/``bytes`` and
    key-slicing fallback for mappings).
    """
    if not is_async_only_iterable(result):
        return _windowed_rows(
            result,
            info,
            declared,
            offset=offset,
            requested_limit=requested_limit,
            trusted=trusted,
        )
    try:
        limit = _raw_list_bound(info, declared, trusted=trusted)
    except BaseException as rejection:
        # The source was handed over before this seam looked at the clock, so a
        # rejection here abandons an iterator the resolver has already built.
        # Nothing has been advanced, but an unadvanced iterator can still hold
        # an open external resource, and no later seam will ever see it again.
        await _cleanup_rejected_async_iterable(
            result,
            rejection,
            caller="bounded_rows_async",
        )
        raise
    start = offset if offset is not None else 0
    window = requested_limit if requested_limit is not None else limit

    iterator = aiter(result)
    if window == 0:
        await _close_async_iterator(iterator)
        return []

    rows: list[Any] = []
    exhausted = False
    primary_error: BaseException | None = None
    skipped = 0
    try:
        async for item in iterator:
            if skipped < start:
                skipped += 1
                continue
            rows.append(item)
            if len(rows) >= window:
                break
        else:
            exhausted = True
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        if not exhausted:
            await _close_async_iterator(
                iterator,
                primary_error=primary_error,
                caller="bounded_rows_async",
            )
    return rows


async def bounded_rows_async(
    result: Any,
    info: Any,
    declared: int | None = None,
    *,
    trusted: bool = False,
) -> Any:
    """Apply a raw-list row bound to a result that may be async-iterable.

    ``graphql-core`` accepts ``AsyncIterable`` list results and materializes
    them during async completion. A synchronous ``bounded_rows`` call cannot
    slice an async generator, however, so an async field must consume only its
    bounded prefix before returning the result to GraphQL. Synchronous
    iterables (including Django ``QuerySet`` objects, which expose both
    protocols) stay on ``bounded_rows`` so lazy querysets retain their SQL
    ``LIMIT`` instead of being materialized through the async iterator.

    When the prefix ends early, the iterator is closed. A cleanup failure is
    raised when iteration itself succeeded; when iteration already failed, the
    source error remains primary and an ordinary cleanup failure is attached as
    a note rather than masking the useful failure. A cancellation arriving
    during cleanup is not demoted that way: it keeps precedence, so a torn-down
    request cannot report itself as an ordinary field error.

    The deadline and row bound are read here, after the resolver has already
    produced its source, so a rejection at that read abandons an async-only
    source the same way an early prefix end does and owes it the same close.
    The rejection keeps precedence over anything acquisition or closure raises.

    Like ``bounded_rows``, this surface carries no client page coordinates:
    ``_windowed_rows_async`` is where a validated ``offset`` / ``limit`` pair
    narrows the window further.
    """
    return await _windowed_rows_async(result, info, declared, trusted=trusted)


def validate_collection_bound(declared: Any, *, field: str) -> None:
    """Reject a field-declared collection bound that is not a positive integer.

    Called at the line that constructs the field, so a typo fails where it was
    written rather than on the first request that reaches the resolver -
    the constructor-site posture the field factories' target guards already take.
    """
    _require_positive_int(declared, field)


def validate_trusted_flag(declared: Any, *, field: str) -> None:
    """Reject a trusted-declaration opt-in that is not exactly ``True`` or ``False``.

    The opt-in that lets a field-declared maximum outrank the request's own
    ``ResourcePolicy`` is a security decision, so the value that makes it is an
    exact ``bool`` and the check fires at the line that constructs the field -
    a misspelled ``trusted_max_rows="false"`` fails where it was written rather
    than silently widening every request the field serves. ``effective_bound``
    independently admits only ``True``, so a caller that bypasses this
    constructor-site check still cannot widen by accident.
    """
    if type(declared) is not bool:
        raise ConfigurationError(
            f"{field} must be exactly True or False; got {describe_value(declared)}.",
        )


def effective_bound(policy_value: int, declared: int | None, *, trusted: bool = False) -> int:
    """Combine a request bound with a field's own declared maximum.

    The narrowing rule at a field: ``None`` means "the field declares nothing,
    the request policy governs"; a declared value narrows to the tighter of the
    two. Only the literal ``True`` widens - the call site is stating that this
    field's maximum is a deliberate declaration that outranks the policy, which
    is exactly the trusted-declaration carve-out and is never the default.

    ``trusted is True``, not ``if trusted:``. This is the one primitive in the
    package whose answer can be WIDER than the request policy, so the condition
    that reaches it admits exactly the one value that means it: a truthy string,
    a non-empty container, or any object whose ``__bool__`` answers ``True``
    narrows like every other non-opt-in caller. The field factories validate the
    flag's type at their own construction line as well
    (:func:`validate_trusted_flag`); the rule is repeated here because this
    primitive must stay safe for an internal caller that has no factory in front
    of it.
    """
    if declared is None:
        return policy_value
    if trusted is True:
        return declared
    return min(policy_value, declared)
