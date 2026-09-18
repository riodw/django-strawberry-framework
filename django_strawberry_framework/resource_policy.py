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
by ``policy_from_info`` and ``check_deadline``. The authority is a ``ContextVar``
rather than a request-context key, so a resolver cannot widen the budget by
REPLACING it; and the armed object is reachable from no consumer-visible name,
so a resolver cannot widen it by MUTATING it either. Everything a resolver can
reach - the schema attribute, the published mirror, whatever
``policy_from_info`` returns - is a copy (``utils/policies.py::copy_policy``).
The policy those copies are taken from is not an attribute of the schema either
(``schema.py::_SCHEMA_ENFORCEMENT``): ``info.schema`` is handed to every resolver
in every operation, so an ordinary attribute would be reachable by assignment and
through ``schema.__dict__`` past a property that has no setter. Being a frozen
dataclass is not what makes any of it true: frozen rejects ``setattr``
and admits ``__dict__`` writes, so on a process-lived object it would have been
one write away from widening every later request on the process. The same call publishes the
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

from django.db.models import QuerySet
from graphql import GraphQLError

from .conf import resource_policy_setting
from .exceptions import ConfigurationError, DjangoStrawberryFrameworkError, describe_value
from .utils.context import clear_context_key, get_context_value, stash_on_context
from .utils.errors import coded_error_extensions
from .utils.operation_lease import OperationLease
from .utils.policies import canonical_policy, copy_policy, resolve_policy
from .utils.querysets import is_async_only_iterable, normalized_row_source

__all__ = (
    "DEFAULT_RESOURCE_POLICY",
    "DST_RESOURCE_DEADLINE",
    "DST_RESOURCE_POLICY",
    "MAX_RESOURCE_BOUND",
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
#: Sync HTTP, async HTTP, WebSocket queries / mutations and a rejected
#: SUBSCRIPTION all render the rejection as an ordinary GraphQL error entry, so
#: one code is what makes them recognizable as the same failure rather than
#: four: the admission stage publishes its verdict as the operation's
#: pre-execution error, and the streaming path yields that as its one frame.
#: The exception is the pre-parse token and structural-depth scan, which has to
#: refuse before a document exists and therefore raises; a streaming caller sees
#: that as an exception out of the operation rather than as this code.
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


def _is_builtin_number(value: Any) -> bool:
    """Whether ``value`` is an exact built-in ``int`` or ``float``.

    The test is EXACT, not ``isinstance``, everywhere a number crosses into the
    budget machinery - a deployment's configured bound, a consumer-written
    deadline mirror, an uploaded file's reported size. A numeric SUBCLASS is
    consumer code wearing a number's type, and every dunder the package then
    reaches for is that code: a raising ``__le__`` / ``__gt__`` replaces a typed
    ``ConfigurationError`` with a raw error out of schema construction, a
    raising ``__ceil__`` / ``__format__`` replaces a typed
    ``ResourceLimitExceeded`` with one out of a collection resolver, a lying
    ``__float__`` answers a domain check for a value it does not hold, a lying
    ``__lt__`` / ``__le__`` makes an expired instant compare as a future one,
    and a reflected ``__radd__`` - which takes priority over the built-in's own
    - turns ``x + value`` into ``nan``, which no later comparison against a
    bound can ever exceed. Admitting only the built-in types is what keeps every
    comparison, conversion, arithmetic and format the package performs on a
    value the package owns.
    """
    return type(value) is int or type(value) is float


def _is_valid_deadline(value: Any) -> bool:
    """Whether ``value`` sits in the deadline domain (``None`` is decided by the caller).

    Exact built-in numbers only (:func:`_is_builtin_number`), finite and
    positive.
    """
    if not _is_builtin_number(value):
        return False
    try:
        return math.isfinite(value) and value > 0
    except OverflowError:
        # ``isfinite`` overflows converting a huge int, which is therefore not
        # classifiable as a positive number of seconds: the domain check answers
        # False and the typed rejection fires at the caller.
        return False


#: The largest value any bound may hold: the signed 64-bit maximum.
#:
#: A bound is not an abstract number. Every collection bound is handed to the
#: database as ``LIMIT`` / ``OFFSET``, where the adapter must bind it as an
#: integer the backend has - SQLite's is 64-bit signed, and PostgreSQL's
#: ``bigint`` is the same width - so a wider one fails inside the driver as a
#: backend error, on the query the bound was supposed to be permitting. Every
#: bound is also rendered into the message and ``extensions`` of the
#: ``ResourceLimitExceeded`` it drives, and CPython refuses to render an integer
#: past ``sys.get_int_max_str_digits`` (4300 digits by default), so a wider one
#: raises a bare ``ValueError`` out of the constructor of the typed rejection
#: that was the deployment's whole reason for configuring it. A bound this
#: package cannot put in a query or in an error is not a looser bound, it is a
#: configuration with no working rejection, and it fails at construction where
#: the deployment can still fix it.
MAX_RESOURCE_BOUND = 2**63 - 1


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

    The domain is bounded ABOVE as well, at :data:`MAX_RESOURCE_BOUND`, because
    a bound is only as configurable as the query and the rejection it has to
    survive.
    """
    if type(value) is not int or value < 1:
        raise ConfigurationError(
            f"{label} must be a positive integer; got {describe_value(value)}.",
        )
    if value > MAX_RESOURCE_BOUND:
        raise ConfigurationError(
            f"{label} must be at most {MAX_RESOURCE_BOUND}, the largest value a bound can "
            f"carry into a database query and into the rejection it drives.",
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
    the package defaults. A ``ResourcePolicy`` instance from either override slot
    supplies its values to a private duplicate that validates them again
    (``utils/policies.py::canonical_policy``), never the object a bound is then
    read from; a mapping from either source is applied over the package defaults
    so a deployment overrides only the bounds it cares about.

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


class _AdmissionVerdict:
    """Whether the admission stage rejected this operation, once it has decided.

    The verdict has to be the package's own, because the shape a rejection
    reaches the client in cannot also be the record of it: a rejection is
    published as ``ExecutionContext.pre_execution_errors``, and that field is an
    ordinary mutable slot every validation extension writes - Strawberry's own
    ``ValidationCache`` assigns its cached result over whatever is there. An
    operation whose rejection was overwritten is still a rejected operation, and
    this is what says so.
    """

    __slots__ = ("rejection",)

    def __init__(self) -> None:
        self.rejection: ResourceLimitExceeded | None = None


@dataclass(frozen=True)
class _RequestBudget:
    """One operation's authoritative budget: its policy, its deadline, its verdict.

    The policy and the absolute deadline are established once, at
    ``on_operation`` entry, and travel together so that no seam can read a
    deadline derived from a policy other than the one it is about to enforce.
    The verdict is decided later, by the admission stage, and travels with them
    so that every stage after it reads one answer for the operation.
    """

    policy: ResourcePolicy
    deadline: float | None
    admission: _AdmissionVerdict


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
#: optimizer's (``optimizer/_context.py``'s execution frame), adopted for the
#: same reason: a per-execution answer a context stash cannot be trusted to
#: give.
#:
#: What the variable holds is a LEASE, never the budget
#: (``utils/operation_lease.py::OperationLease``). Propagation is the same
#: mechanism as leakage: a resolver's background task gets a copy of this
#: context and keeps it for as long as it runs, and no token reset can reach
#: that copy. Closing the lease at the end of the operation is what does reach
#: it, so a seam running in such a task reads no armed budget - falling back
#: exactly as it does where none was ever armed - instead of enforcing a
#: completed request's ceiling on a new one, and the policy, deadline and
#: verdict stop being reachable at that instant rather than when the task
#: finally ends.
#:
#: The published keys stay exactly as spec-047 shipped them, as a mirror a
#: consumer can read; they are also the fallback for a caller that publishes a
#: policy without arming one (a direct ``stash_resource_policy``, or a plain
#: ``strawberry.Schema`` with no extension), which is a context no resolver of
#: this package's is running inside.
_active_budget: ContextVar[OperationLease[_RequestBudget] | None] = ContextVar(
    "django_strawberry_framework_resource_budget",
    default=None,
)


class _BudgetScope:
    """One armed budget's lease, the token that restores the enclosing one, and who owns it.

    The first two answer different questions. The lease is what every context
    holding it - this one and every copy taken from it - reads through, so
    closing it ends the budget everywhere at once. The token is what gives THIS
    context back whatever an enclosing operation had armed, and only this
    context: a task that closes a streamed operation from elsewhere has nothing
    of its own to restore.

    ``adopted`` records that something else took the token over. A streamed
    operation arms its budget inside its first frame, and the resume driving
    that frame takes the binding back when the frame is handed over - so the
    binding ends there, while the budget stays armed for the frames still to
    come. Once that has happened this scope no longer has a binding of its own
    to end, and ending it again would be a used token rather than a restore.

    ``__slots__`` and not a ``NamedTuple``: ownership is settled after the scope
    is built, by whoever adopts it.
    """

    __slots__ = ("adopted", "lease", "token")

    def __init__(self, lease: OperationLease[_RequestBudget], token: Any) -> None:
        self.lease = lease
        self.token = token
        self.adopted = False


def _armed_budget() -> _RequestBudget | None:
    """The budget armed and still open here, or ``None``.

    The one read every seam in this module goes through, so "no budget" and "a
    budget whose operation has ended" cannot be told apart by any of them - the
    second being a context copied out of a request that is over, which is
    entitled to exactly as much as the first.
    """
    lease = _active_budget.get()
    return None if lease is None else lease.held()


def _absolute_deadline(policy: ResourcePolicy) -> float | None:
    """The monotonic instant ``policy``'s budget ends, or ``None`` for no deadline.

    ``execution_deadline_seconds`` is an exact built-in by construction
    (:func:`_is_valid_deadline`), so this addition is plain ``float``
    arithmetic and cannot be redirected through a consumer's ``__radd__``.
    """
    seconds = policy.execution_deadline_seconds
    return None if seconds is None else time.monotonic() + seconds


def _publish_budget_mirror(context: Any, policy: ResourcePolicy, deadline: float | None) -> None:
    """Write the consumer-readable mirror of a budget onto the request context.

    The policy published here is a COPY. The mirror exists to be read by consumer
    code, which means every resolver in the request holds whatever object is put
    under this key; publishing the armed one would make a key documented as a
    mirror into a write seam onto the authority it mirrors.
    """
    stash_on_context(context, DST_RESOURCE_POLICY, copy_policy(policy))
    stash_on_context(context, DST_RESOURCE_DEADLINE, deadline)


def stash_resource_policy(context: Any, policy: ResourcePolicy) -> None:
    """Publish ``policy`` (and its derived deadline) onto the request context.

    The consumer-readable mirror, and only that. :func:`begin_resource_budget`
    is what arms the budget the enforcement seams actually read; a caller that
    publishes without arming leaves the seams on their fallback, which reads
    this mirror back.

    The policy is canonicalized first (:func:`_operation_policy`), because that
    fallback makes what is published here the value a bound is read from, so it
    is admitted on the same terms as an armed one.
    """
    policy = _operation_policy(policy)
    _publish_budget_mirror(context, policy, _absolute_deadline(policy))


def _operation_policy(policy: ResourcePolicy) -> ResourcePolicy:
    """The private, exact policy one operation is bounded by.

    Taken once per operation rather than per bound read, so the per-field seams
    pay nothing for it. ``utils/policies.py::canonical_policy`` establishes both
    properties an armed budget needs: the object is an exact ``ResourcePolicy``,
    so every field read a bound performs is the package's own rather than a
    subclass's, and it is a fresh object no caller of
    :func:`begin_resource_budget` retained a reference to, so the budget cannot
    be widened afterwards by writing the object that was passed in.
    """
    return canonical_policy(policy, policy_cls=ResourcePolicy, display_name="resource policy")


def begin_resource_budget(context: Any, policy: ResourcePolicy) -> Any:
    """Arm ``policy`` as this operation's budget and publish it; returns its scope.

    What is armed is a private snapshot (:func:`_operation_policy`), never the
    object the caller passed: the schema's policy is process-lived and reachable
    from ``info.schema``, so arming it directly would put the operation's ceiling
    behind a name every resolver in every later request can write.

    One derived absolute deadline reaches both the armed budget and the
    published mirror, so the authority and the mirror cannot disagree about when
    the operation's budget ends. :func:`end_resource_budget` closes the scope,
    restoring whatever budget an enclosing operation had armed.

    What comes back is the whole scope rather than a token, because ending one
    is two statements: the lease is closed, which every context that copied this
    one observes, and the binding is reset, which only this context sees.
    """
    armed = _operation_policy(policy)
    deadline = _absolute_deadline(armed)
    _publish_budget_mirror(context, armed, deadline)
    lease = OperationLease(_RequestBudget(armed, deadline, _AdmissionVerdict()))
    return _BudgetScope(lease, _active_budget.set(lease))


def budget_resume_binding(scope: Any) -> tuple[ContextVar[Any], Any, Any]:
    """What a streamed operation has to bind again on resume, and what armed it here.

    An operation's budget is armed once, in the task that started it, and a
    streamed operation's later frames run in whatever task drives them. The
    runner re-binds the variable and the lease around every resumption
    (``extensions/operation_state.py::OperationState.rebind_on_resume``), so a
    frame produced in a second task is bounded by the policy the request was
    admitted under rather than by the fallback. It is the same lease, so the
    close that ends the operation ends it for every task that ever bound it.

    The token goes with them because the arming happens INSIDE the first frame:
    the resume driving that frame has no binding of its own to take back, so
    without this the budget would stay armed in the driving task after the frame
    was handed over - an unrelated call in that task would then be answered by a
    paused operation's ceiling rather than by its own context. The lease is the
    operation's lifetime and the token is one task's binding of it; the resume
    ends the second without touching the first.
    """
    return _active_budget, scope.lease, scope.token


def adopt_budget_binding(scope: Any) -> None:
    """Record that a resume took this scope's binding over.

    Called only when a registrar actually accepted it, so an ordinary operation
    - and a plain ``strawberry.Schema``, which has no runner at all - still ends
    its own binding in :func:`end_resource_budget`.
    """
    scope.adopted = True


def armed_resource_policy() -> ResourcePolicy | None:
    """The snapshot armed for this operation, or ``None`` when nothing armed one.

    The package's own way of asking "which policy is this operation being
    bounded by", for the seams that run inside an armed scope but hold no
    ``info``: :func:`policy_from_info` answers the same question for a resolver
    and falls back to the published mirror, while a caller of this one wants to
    know whether a budget is armed at all.

    What comes back is the armed object itself rather than a copy, and it is not
    exported: it has already been through :func:`_operation_policy`, so its
    fields are the package's own, and the callers are package code charging
    against the budget in force rather than consumer code that could retain it.
    Charging the armed snapshot is what keeps one operation's accounting on ONE
    policy - a hook that re-resolves its configuration per call can be handed a
    different answer each time by a policy object whose reads are consumer code,
    and then the document is scanned against one budget while the request runs
    under another.
    """
    budget = _armed_budget()
    return None if budget is None else budget.policy


def record_admission_rejection(rejection: ResourceLimitExceeded) -> None:
    """Record ``rejection`` as this operation's admission verdict.

    Does nothing when no budget is armed, which is the plain
    ``strawberry.Schema`` case a caller reaches by invoking a hook outside an
    operation scope: there is no operation for a verdict to belong to. An ended
    operation is the same case: a verdict recorded into it would be read by
    nothing.
    """
    budget = _armed_budget()
    if budget is not None:
        budget.admission.rejection = rejection


def admission_rejection() -> ResourceLimitExceeded | None:
    """This operation's admission rejection, or ``None`` if it was admitted.

    The answer every stage after admission reads, in preference to the published
    error it can be told apart from: publishing is how a rejection reaches the
    client, and what is published is writable by anything else in the extension
    chain.
    """
    budget = _armed_budget()
    return None if budget is None else budget.admission.rejection


def end_resource_budget(scope: Any) -> None:
    """Disarm the budget armed by :func:`begin_resource_budget`.

    Closing comes first and is unconditional, because it is the half that works
    from anywhere: it ends the budget in the task that armed it, in every task
    that copied that context, and in whichever task is running this teardown.

    The reset is the local half. A cancelled subscription closes the generator
    driving it from a context that is not the one the operation armed in, and a
    token is resettable only where it was created; the copy that context holds
    is discarded with it, so there is nothing to restore - and raising here
    would replace the cancellation with a ``ValueError`` from teardown.

    Only that condition is ignored. ``ValueError`` also answers a token minted
    by another variable, which is this module's bookkeeping gone wrong rather
    than a fact about where teardown ran, so it is re-raised; a reused token is
    ``RuntimeError`` and is not caught at all.

    An adopted scope has no local half left to do: the resume that took the
    binding over ended it when it handed its frame back
    (:func:`adopt_budget_binding`), and the close is the whole of what remains.
    """
    scope.lease.close()
    if scope.adopted:
        return
    try:
        _active_budget.reset(scope.token)
    except ValueError:
        if scope.token.var is not _active_budget:
            raise


def _effective_deadline(armed: float | None, mirror: Any) -> Any:
    """The tighter of the operation's own deadline and a consumer-written one.

    The narrowing rule the rest of the module already states for bounds
    (``effective_bound``, ``ResourcePolicy.narrowed``), applied to the one piece
    of budget state a consumer can write: a resolver that stashes an EARLIER
    instant under ``DST_RESOURCE_DEADLINE`` is shortening its own request, which
    it is always entitled to do; one that stashes a later instant, clears the
    key, or writes a value outside the deadline domain is asking to run past the
    budget the operation started with, which no caller is entitled to. The armed
    value is the ceiling either way, so the seam cannot be widened by anything
    reachable from ``info.context``.

    The written value is admitted only if it is an exact built-in number
    (:func:`_is_builtin_number`). A numeric SUBCLASS answers the comparison the
    narrowing rule is decided by, so it can present itself as EARLIER than the
    armed instant while answering every later comparison as a future one - a
    narrowing on the way in and a widening on the way out, which is the one
    thing this seam exists to refuse.
    """
    if not _is_builtin_number(mirror):
        return armed
    if armed is None:
        return mirror
    return mirror if mirror < armed else armed


def _deadline_expired(deadline: Any) -> bool | None:
    """Whether ``deadline`` has passed, or ``None`` when it is not a deadline at all.

    Only an exact built-in number is placed against the clock
    (:func:`_is_builtin_number`); a non-finite one is expired, since no
    configured policy derives it and no comparison can certify the request is
    inside it.

    A value that is numeric-SHAPED but outside that domain - an ``int`` or
    ``float`` SUBCLASS, whose comparison, conversion and format are all consumer
    code - is likewise a deadline the seam cannot certify the request is inside,
    and reads as passed rather than being asked. Absent, cleared, ``bool``, or
    anything non-numeric is not a deadline at all and leaves the request
    running.
    """
    if _is_builtin_number(deadline):
        try:
            return not math.isfinite(deadline) or time.monotonic() >= deadline
        except OverflowError:
            # ``isfinite`` overflows converting an integer too large for a
            # double, which is therefore an instant no comparison can place.
            return True
    if isinstance(deadline, bool) or not isinstance(deadline, (int, float)):
        return None
    return True


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

    What comes back is always a COPY, never the armed object or the package
    default singleton. This function is the package's own way of reading a bound
    and it is equally the way a consumer resolver reads one, so whatever it
    returns is in reach of consumer code for the rest of the operation; returning
    the authority would let one ``__dict__`` write on it widen every bound for
    the rest of the request, and returning the singleton would widen them for
    every request the process serves afterwards.

    A mirror value is admitted only when it is an EXACT ``ResourcePolicy``. A
    subclass answers every field read with consumer code, which is the same
    domain rule the module applies to a number crossing into the budget
    (:func:`_is_builtin_number`); an armed budget has been through
    :func:`_operation_policy` already, so this is the one path where a foreign
    object could still arrive.

    Fail-closed by construction: the miss path returns
    ``DEFAULT_RESOURCE_POLICY``, never ``None``. A field consulting the policy is
    therefore always bounded, including under a plain ``strawberry.Schema`` that
    never installed the extension, and never needs a ``None`` branch of its own.

    An ended operation's budget answers nothing, which is what makes the
    ``info`` argument the authority again for a caller running outside every
    operation: a background task that outlived the request it was started from
    reads the context it was handed rather than the ceiling that request had.
    """
    budget = _armed_budget()
    if budget is not None:
        return copy_policy(budget.policy)
    value = get_context_value(getattr(info, "context", None), DST_RESOURCE_POLICY)
    return copy_policy(value if type(value) is ResourcePolicy else DEFAULT_RESOURCE_POLICY)


def check_deadline(info: Any) -> None:
    """Raise if the operation's optional wall-clock deadline has already passed.

    Cooperative and called at the collection resolvers' pre-query seam, which is
    the last point before the request hands work to the database. The armed
    budget is the ceiling: a resolver may SHORTEN its own request by stashing an
    earlier instant under ``DST_RESOURCE_DEADLINE``, and cannot lengthen or
    clear it (:func:`_effective_deadline`). Where no budget is armed, the
    published mirror is all there is and answers alone.

    Guarding the *answer* rather than a spelling of the input
    (:func:`_deadline_expired`): an absent, cleared, or non-numeric deadline
    leaves the request running rather than rejecting it, while one that has
    passed - and equally one that is numeric but not placeable on the clock,
    which no configured policy can derive and which no comparison can certify
    the request is inside - always rejects.

    The rejection reports the CONFIGURED budget, never the clock: ``limit`` is
    the policy's own ``execution_deadline_seconds`` and ``charged`` is one second
    past it (the "exceeded an unmeasurable-in-integers budget" spelling this
    module already uses for an upload whose size cannot be read). The monotonic
    deadline and the overrun are process-internal timings a client can neither
    act on nor verify, and a wire field named ``limit`` carrying a monotonic
    timestamp is worse than useless - it reads as a bound the deployment never
    configured.
    """
    budget = _armed_budget()
    mirror = get_context_value(getattr(info, "context", None), DST_RESOURCE_DEADLINE)
    deadline = mirror if budget is None else _effective_deadline(budget.deadline, mirror)
    if not _deadline_expired(deadline):
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


#: The collection representations whose own slice is the operation that bounds
#: them. An exact ``QuerySet`` is sliced because slicing is the only thing that
#: carries the bound into SQL as ``LIMIT``, so a queryset is never evaluated
#: unbounded; the exact built-in sequences are sliced because at an exact type
#: ``[a:b]`` is the interpreter's own subscript rather than a method the value
#: brought with it. Everything else is bounded by COUNTING instead - see
#: ``_windowed_rows``.
_SLICE_BOUNDED_ROW_TYPES = (
    list,
    tuple,
    str,
    bytes,
    bytearray,
    QuerySet,
)


def _bounds_by_its_own_slice(result: Any) -> bool:
    """Whether slicing ``result`` is an operation this package owns the meaning of.

    Exact types only, and ``type(result)`` rather than ``isinstance``: a subclass
    of any of these brings its own ``__getitem__``, and an ``isinstance`` test
    can be answered by a ``__class__`` property on an object that is none of
    them. A QuerySet subclass does not reach here as itself - it arrives already
    rebuilt into an exact framework-owned queryset by
    ``utils/querysets.py::normalized_row_source``, or not at all.
    """
    return type(result) in _SLICE_BOUNDED_ROW_TYPES


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

    The window is applied with an operation this package owns. Slicing a value
    runs whatever ``__getitem__`` the value brought with it, so on a consumer's
    own sequence type the bound is enforced by consumer code and a slice can
    answer with every row it was asked to drop; ``[start:stop]`` is therefore
    reached only for the exact representations in ``_SLICE_BOUNDED_ROW_TYPES``,
    among them the ``QuerySet`` whose slice is what pushes ``LIMIT`` into SQL.
    Every other shape - a subclass of those types, a mapping, a bare iterable, a
    relation accessor's sequence proxy - is bounded by COUNTING through
    ``islice`` into a list this package built, which cannot return more items
    than it was asked for whatever the source does, and a zero-width window on
    such a shape is the empty list rather than a subscript nobody can predict
    the answer to.

    A ``QuerySet`` SUBCLASS is neither sliced as itself nor demoted to counting:
    ``utils/querysets.py::normalized_row_source`` rebuilds it into a plain
    framework-owned queryset first, so a sealable project subclass keeps its
    ``LIMIT`` in SQL and an unsealable one fails closed. That seam is the only
    thing between "this value is a queryset" and "call its slice", and it runs
    before the shape is classified because the classification is what it
    settles.

    A source that arrives evaluated is windowed from the rows it already holds,
    because ``QuerySet.__getitem__`` reads a populated ``_result_cache`` directly
    and the rebuild carries that cache forward, so the window costs no query for
    the exact shape and for a rebuilt subclass alike.

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
    result = normalized_row_source(result)
    by_slice = _bounds_by_its_own_slice(result)
    if offset is None and requested_limit is None:
        return result[:limit] if by_slice else list(islice(result, limit))

    start = offset if offset is not None else 0
    window = requested_limit if requested_limit is not None else limit
    if window == 0:
        return result[start:start] if by_slice else []
    stop = start + window
    return result[start:stop] if by_slice else list(islice(result, start, stop))


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

    An unevaluated ``QuerySet`` is bounded by SLICING, so it carries the bound
    into SQL as ``LIMIT`` and is never evaluated unbounded; a value whose rows
    are already fetched - a materialized sequence, a consumer resolver's return,
    Django's prefetch cache, or a queryset the consumer evaluated - is windowed
    in Python from the rows it holds, which cannot un-fetch them but does stop
    the response from serializing them and costs no second query.
    Which operation does the truncating follows from what the value IS, never
    from whether a subscript happened to answer: an exact ``list``, ``tuple``,
    ``str``, ``bytes``, ``bytearray`` or ``QuerySet`` is sliced, and every
    other shape - a subclass of one of the sequence types, a mapping, a bare
    iterable - is counted into a fresh list instead, which is how the ceiling
    stays a ceiling on a sequence type whose own ``__getitem__`` is consumer
    code. The slice answers in the sliced value's own type, except on a
    queryset whose rows are already fetched: there ``QuerySet.__getitem__``
    answers from the rows it holds, so the window comes back as a ``list``. A
    mapping therefore still comes back as a bounded list of its keys. A
    ``QuerySet`` subclass is the one shape that is rebuilt rather than
    reclassified: it is sealed into a plain framework-owned queryset and sliced
    there, so an unevaluated one keeps the SQL ``LIMIT`` a counted truncation
    would lose and an evaluated one is windowed from the rows the rebuild
    carried forward; a state that cannot be rebuilt fails closed with a typed
    ``ConfigurationError``.

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
    iterator early without over-requesting subsequent items - the rows it
    returns are collected into a list of its own, so an async source bounds the
    same way a non-sliceable sync one does. Synchronous iterables fall back to
    ``_windowed_rows`` and are bounded there on its terms.
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
