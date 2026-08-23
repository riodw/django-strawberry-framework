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

**Immutable and threaded through the request context.** The resolved policy is
stashed under ``DST_RESOURCE_POLICY`` at the start of every operation, mirroring
the optimizer's ``DST_OPTIMIZER_*`` context seam, and read back by
``policy_from_info``. The object is a frozen dataclass, so a resolver cannot
widen the request's own budget by mutating it.

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
from collections.abc import AsyncIterable, Iterable, Mapping
from dataclasses import dataclass, fields, replace
from itertools import islice
from typing import Any

from graphql import GraphQLError

from .conf import resource_policy_setting
from .exceptions import ConfigurationError, DjangoStrawberryFrameworkError, describe_value
from .utils.context import clear_context_key, get_context_value, stash_on_context

__all__ = (
    "DEFAULT_RESOURCE_POLICY",
    "DST_RESOURCE_DEADLINE",
    "DST_RESOURCE_POLICY",
    "RESOURCE_LIMIT_ERROR_CODE",
    "ResourceLimitExceeded",
    "ResourcePolicy",
    "bounded_rows",
    "bounded_rows_async",
    "check_deadline",
    "clear_resource_context",
    "effective_bound",
    "policy_from_info",
    "resolve_resource_policy",
    "stash_resource_policy",
    "validate_collection_bound",
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
            extensions={
                "code": RESOURCE_LIMIT_ERROR_CODE,
                "bound": bound,
                "limit": limit,
                "charged": charged,
            },
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
        Ceiling on the rows a raw (non-Relay) list field may evaluate.

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
                if value is None:
                    continue
                if isinstance(value, float):
                    finite = math.isfinite(value)
                elif isinstance(value, int):
                    try:
                        finite = math.isfinite(float(value))
                    except OverflowError:
                        finite = False
                else:
                    finite = False
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not finite
                    or value <= 0
                ):
                    raise ConfigurationError(
                        "ResourcePolicy.execution_deadline_seconds must be None or a "
                        f"positive number of seconds; got {describe_value(value)}.",
                    )
                continue
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ConfigurationError(
                    f"ResourcePolicy.{field.name} must be a positive integer; "
                    f"got {describe_value(value)}.",
                )

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
    """
    if isinstance(explicit, ResourcePolicy):
        return explicit
    overrides = explicit if explicit is not None else resource_policy_setting()
    if overrides is None:
        return DEFAULT_RESOURCE_POLICY
    if not isinstance(overrides, Mapping):
        raise ConfigurationError(
            "The resource policy must be a ResourcePolicy or a mapping of bound "
            f"names to values; got {describe_value(overrides)}.",
        )
    known = {field.name for field in fields(ResourcePolicy)}
    unknown = sorted(str(name) for name in overrides if name not in known)
    if unknown:
        raise ConfigurationError(
            f"Unknown resource-policy bound(s): {', '.join(unknown)}. "
            f"Valid bounds: {', '.join(sorted(known))}.",
        )
    return ResourcePolicy(**dict(overrides))


def stash_resource_policy(context: Any, policy: ResourcePolicy) -> None:
    """Publish ``policy`` (and its derived deadline) onto the request context."""
    stash_on_context(context, DST_RESOURCE_POLICY, policy)
    deadline = policy.execution_deadline_seconds
    stash_on_context(
        context,
        DST_RESOURCE_DEADLINE,
        None if deadline is None else time.monotonic() + deadline,
    )


def clear_resource_context(context: Any) -> None:
    """Remove both resource keys, so a reused ``context_value`` cannot leak a deadline."""
    clear_context_key(context, DST_RESOURCE_POLICY)
    clear_context_key(context, DST_RESOURCE_DEADLINE)


def policy_from_info(info: Any) -> ResourcePolicy:
    """Return the request's policy, or the package default when none was published.

    Fail-closed by construction: the miss path returns
    ``DEFAULT_RESOURCE_POLICY``, never ``None``. A field consulting the policy is
    therefore always bounded, including under a plain ``strawberry.Schema`` that
    never installed the extension, and never needs a ``None`` branch of its own.
    """
    value = get_context_value(getattr(info, "context", None), DST_RESOURCE_POLICY)
    return value if isinstance(value, ResourcePolicy) else DEFAULT_RESOURCE_POLICY


def check_deadline(info: Any) -> None:
    """Raise if the operation's optional wall-clock deadline has already passed.

    Cooperative and called at the collection resolvers' pre-query seam, which is
    the last point before the request hands work to the database. Guarding the
    *answer* rather than a spelling of the input: only a stashed deadline that is
    a real number arms the check, so an absent, cleared, or non-numeric stash
    leaves the request running rather than rejecting it, and a stashed deadline
    that HAS passed always rejects.

    The rejection reports the CONFIGURED budget, never the clock: ``limit`` is
    the policy's own ``execution_deadline_seconds`` and ``charged`` is one second
    past it (the "exceeded an unmeasurable-in-integers budget" spelling this
    module already uses for an upload whose size cannot be read). The monotonic
    deadline and the overrun are process-internal timings a client can neither
    act on nor verify, and a wire field named ``limit`` carrying a monotonic
    timestamp is worse than useless - it reads as a bound the deployment never
    configured.
    """
    deadline = get_context_value(getattr(info, "context", None), DST_RESOURCE_DEADLINE)
    if not isinstance(deadline, (int, float)) or isinstance(deadline, bool):
        return
    if time.monotonic() < deadline:
        return
    configured = policy_from_info(info).execution_deadline_seconds
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
    own ``declared`` maximum unless the field declared ``trusted=True``.

    It is applied by SLICING, so a ``QuerySet`` carries the bound into SQL as a
    ``LIMIT`` and is never evaluated unbounded; a value that is already a
    materialized sequence (a consumer resolver's return, or Django's prefetch
    cache) is truncated in Python, which cannot un-fetch those rows but does stop
    the response from serializing them.

    A raw list is the one collection shape Relay pagination does not bound, so
    this is the only thing between a client and the whole table. It is
    unconditional: there is no argument or configuration that turns it off, only
    values that make it larger.
    """
    check_deadline(info)
    if result is None:
        return None
    limit = effective_bound(policy_from_info(info).max_list_rows, declared, trusted=trusted)
    try:
        return result[:limit]
    except TypeError:
        # A relation accessor can hand back a non-subscriptable iterable (a
        # consumer-assigned sequence proxy, a custom manager's cached rows).
        # Falling back to ``islice`` bounds it rather than letting it through:
        # the alternative to slicing an unsliceable value is NOT "return it
        # whole", which would be a bound that silently stops applying to
        # exactly the shapes nobody anticipated.
        return list(islice(result, limit))


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
    source error remains primary and the cleanup failure is attached as a note
    rather than masking the useful failure.
    """
    if not isinstance(result, AsyncIterable) or isinstance(result, Iterable):
        return bounded_rows(result, info, declared, trusted=trusted)
    check_deadline(info)
    limit = effective_bound(policy_from_info(info).max_list_rows, declared, trusted=trusted)
    iterator = aiter(result)
    rows: list[Any] = []
    exhausted = False
    primary_error: BaseException | None = None
    try:
        async for item in iterator:
            rows.append(item)
            if len(rows) >= limit:
                break
        else:
            exhausted = True
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        if not exhausted:
            try:
                close = getattr(iterator, "aclose", None)
                if close is not None:
                    await close()
            except BaseException as close_error:
                if primary_error is None:
                    raise
                # ``BaseException.add_note`` is 3.11+, and this runs inside a
                # ``finally``: on the 3.10 support floor the resulting
                # ``AttributeError`` would REPLACE the source error, masking
                # exactly the failure this branch exists to preserve. Writing
                # the ``__notes__`` list the note protocol is built on is what
                # ``add_note`` does on 3.11+ (same list, same traceback
                # rendering) and is the only form that carries the diagnostic
                # across the whole supported range.
                notes = [*getattr(primary_error, "__notes__", ())]
                notes.append(
                    f"bounded_rows_async iterator cleanup failed: {close_error!r}",
                )
                primary_error.__notes__ = notes
    return rows


def validate_collection_bound(declared: Any, *, field: str) -> None:
    """Reject a field-declared collection bound that is not a positive integer.

    Called at the line that constructs the field, so a typo fails where it was
    written rather than on the first request that reaches the resolver -
    the constructor-site posture the field factories' target guards already take.
    """
    if isinstance(declared, bool) or not isinstance(declared, int) or declared < 1:
        raise ConfigurationError(
            f"{field} must be a positive integer; got {describe_value(declared)}.",
        )


def effective_bound(policy_value: int, declared: int | None, *, trusted: bool = False) -> int:
    """Combine a request bound with a field's own declared maximum.

    The narrowing rule at a field: ``None`` means "the field declares nothing,
    the request policy governs"; a declared value narrows to the tighter of the
    two. ``trusted=True`` is the explicit widening opt-in - the call site is
    stating that this field's maximum is a deliberate declaration that outranks
    the policy, which is exactly the trusted-declaration carve-out and is never
    the default.
    """
    if declared is None:
        return policy_value
    if trusted:
        return declared
    return min(policy_value, declared)
