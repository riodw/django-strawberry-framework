"""``DjangoDebugExtension`` - Django query-log SQL and execution exceptions in the response.

A Strawberry :class:`~strawberry.extensions.SchemaExtension` that captures the
Django-recorded query-log SQL and the execution exceptions for the in-flight
GraphQL operation and attaches them to the response's ``extensions`` map under
the ``debug`` key - the in-response counterpart to the server-side
debug-toolbar middleware (``middleware/debug_toolbar.py``), porting the
capability of graphene-django's ``DjangoDebug`` subsystem into the engine's
native response-extensions seam.

Off by default, and **fails closed under ``settings.DEBUG = False``**: an
instance constructed without the ``allow_unsafe_production=True``
acknowledgement withholds the whole payload on a non-debug deployment and logs
the misconfiguration, so a single production schema-list entry can no longer
silently publish the disclosure. The payload is also capped - bounded row
counts and a bounded serialized size, with deterministic marked truncation - so
the diagnostic cannot amplify a large operation into an enormous response.

The opt-in is passing the **class** in ``strawberry.Schema``'s
``extensions=`` list (one fresh instance per operation - requires the
package's ``strawberry-graphql>=0.316.0`` floor)::

    _optimizer = DjangoOptimizerExtension()
    schema = strawberry.Schema(
        query=Query,
        config=strawberry_config(),
        extensions=[
            lambda: _optimizer,     # singleton-in-a-factory: preserves the plan cache
            DjangoDebugExtension,   # the CLASS: one fresh instance per operation
        ],
    )

Every executed operation then carries ``extensions["debug"]`` with two lists,
both always present: ``sql`` rows (``vendor`` / ``alias`` / ``sql`` /
``duration`` / ``isSlow`` / ``isSelect`` - graphene's wire names) and
``exceptions`` rows (``excType`` / ``message`` / ``stack``). Parse and
validation failures carry **no** ``debug`` key: nothing executed, and the
engine reads extension results before this hook's teardown on those paths.

Security - development schemas ONLY, never internet-facing production:

* ``exceptions`` rows expose the **unmasked** exception type, message, and
  full traceback (with server filesystem/source paths) even when a masking
  extension sanitized ``errors``.
* ``sql`` strings are Django's ``last_executed_query`` output, which
  **interpolates parameter values** - secrets, tokens, email addresses, and
  other PII included.
* the response carrying both is routinely copied downstream (browser
  DevTools, HTTP logs, tracing systems, caches, bug reports, test
  snapshots), and captured rows also persist in Django's in-process
  per-connection query log after the response (over HTTP the
  ``request_started`` signal resets the log before the next view; non-HTTP
  in-process execution has no such reset).

Capture mechanism and its documented boundaries:

* SQL fidelity is Django's own debug cursor: each configured database
  connection's ``force_debug_cursor`` is enabled for the operation through a
  module-private, lock-protected, reference-counted coordinator (the
  ``CaptureQueriesContext`` mechanism, made overlap-safe), so capture works
  independent of ``settings.DEBUG``. The saved flag value is restored - not
  ``False`` - so the bracket nests inside a consumer's own capture context.
* Django selects the cursor wrapper at ``connection.cursor()`` time and never
  re-checks: a normal cursor opened **before** the operation stays silent
  inside it, and a debug cursor retained past teardown keeps logging after
  the flag restores. Short-lived cursors (every ordinary ORM call) are the
  guaranteed case.
* ``CursorDebugWrapper`` does not instrument ``callproc()``; stored-procedure
  calls produce no row.
* Transaction rows (``BEGIN`` / ``COMMIT`` / savepoints) appear only when
  their logging completes while the hook is active: a resolver-owned
  ``atomic()`` block is in scope, an enclosing ``ATOMIC_REQUESTS`` /
  middleware transaction is not.
* The per-connection ``queries_log`` is a bounded deque (default 9000);
  slicing from a length snapshot is best effort after rollover.
* Nested same-thread sync operations share one wrapper and log: restoration
  stays correct, but the outer payload intentionally includes the inner
  operation's rows.
* Async execution: exception capture is color-agnostic, but Django
  connections are per-thread, so ``sync_to_async`` executor-thread queries
  escape a bracket set on the event-loop thread - expect an **empty** ``sql``
  list under async execution. Overlapping async operations restore safely
  when they share pre-materialized wrapper objects; rows are not
  operation-local on a shared log.
* Ordering with a masking extension is load-bearing: ``on_operation``
  teardowns unwind LIFO and ``MaskErrors`` strips ``original_error`` in its
  teardown, so list ``DjangoDebugExtension`` **after** the masking extension
  (torn down first, reading the originals). Listed before it, ``exceptions``
  reads ``[]``.
"""

import threading
import traceback
from collections.abc import Mapping
from contextlib import ExitStack
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypedDict

from django.conf import settings
from django.db import connections
from graphql import ExecutionResult as GraphQLExecutionResult
from graphql import GraphQLError
from strawberry.extensions import SchemaExtension

from .. import logger
from ..exceptions import ConfigurationError, describe_value

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from django.db.backends.base.base import BaseDatabaseWrapper

__all__ = ["DjangoDebugExtension"]

# graphene's slow-query threshold (``DjangoDebugSQL.is_slow`` is
# ``duration > 10``), kept verbatim so a graphene migrant's tooling reads the
# same ``isSlow`` semantics.
_SLOW_QUERY_SECONDS = 10

# Ceiling for the nested ``GraphQLError.original_error`` walk -
# ``utils/typing.py``'s ``_MAX_TYPE_WRAPPER_DEPTH`` ceiling re-spelled locally
# (deliberately NOT imported: the walk's failure policy differs - stop and
# keep the best-effort terminal instead of raising - so it stays a local
# helper until a fourth chain-peel motivates a shared extraction).
_MAX_ORIGINAL_ERROR_HOPS = 64

# Payload caps (spec-048 Decision 6). Module constants, not settings keys: a
# diagnostic's ceiling is a package invariant, and a deployment that wants a
# different one is a deployment running this extension in production, which is
# the thing the fail-closed gate exists to stop.
#
# Row counts bound how many rows a single operation can publish; the per-row
# character limits bound one row's variable-length text; and the payload budget
# bounds all of them together, so a thousand short rows cannot evade the per-row
# limits. Every limit counts CHARACTERS - the payload is JSON-encoded downstream,
# where one character is at least one byte, so a character ceiling is a byte
# ceiling that does not depend on the encoder.
#
# ``_MAX_PAYLOAD_TEXT_CHARS`` is named for exactly what it measures: the summed
# length of the rows' variable-length STRING values (``_row_cost``). It is not a
# ceiling on the encoded payload's own size - the fixed cost of a row's keys,
# quoting, separators, and numeric values is excluded, because that cost is a
# property of the wire encoder rather than of the diagnostic, and counting it
# would make the budget move whenever the encoder did. The variable text is what
# an operation can inflate without bound, and it is what this bounds.
_MAX_SQL_ROWS = 100
_MAX_EXCEPTION_ROWS = 25
_MAX_SQL_TEXT_CHARS = 4096
_MAX_EXCEPTION_MESSAGE_CHARS = 4096
_MAX_EXCEPTION_STACK_CHARS = 16384
_MAX_PAYLOAD_TEXT_CHARS = 262144

# The single marker appended to every truncated string, so a consumer reading
# the payload can always tell a cut value from a short one.
_TRUNCATION_MARKER = "... [truncated]"


class _DebugSQLRow(TypedDict):
    """One captured Django query-log entry, in graphene's wire casing."""

    vendor: str
    alias: str
    sql: str
    duration: float
    isSlow: bool
    isSelect: bool


class _DebugExceptionRow(TypedDict):
    """One captured execution exception, in graphene's wire casing."""

    excType: str
    message: str
    stack: str


class _DebugPayload(TypedDict):
    """The completed ``extensions["debug"]`` map - both lists always present."""

    sql: "list[_DebugSQLRow]"
    exceptions: "list[_DebugExceptionRow]"


@dataclass(frozen=True)
class _CaptureToken:
    """Names the exact concrete database connection wrapper one acquire bracketed."""

    database_connection: "BaseDatabaseWrapper"


@dataclass(frozen=True)
class _ConnectionSnapshot:
    """One acquired database connection plus its query-log length at acquisition."""

    database_connection: "BaseDatabaseWrapper"
    query_log_start: int


@dataclass(frozen=True)
class _ActiveCapture:
    """Coordinator state for one concrete database connection wrapper.

    ``saved_force_debug_cursor`` is the flag value the FIRST overlapping
    bracket saved; ``depth`` counts the currently overlapping brackets. The
    record is immutable - every transition replaces it - so a torn read can
    never observe a half-updated pair.
    """

    saved_force_debug_cursor: bool
    depth: int


class _CursorCaptureCoordinator:
    """Overlap-safe ownership of every bracketed ``force_debug_cursor`` flag.

    The only code that touches the active-capture map, the saved flag values,
    and ``connection.force_debug_cursor`` (its two seams are ``acquire`` /
    ``release``). The map is keyed by the concrete database connection
    wrapper object - never by alias, because one alias names distinct
    per-thread wrapper objects - and the first bracket on a wrapper saves and
    enables the flag, overlapping brackets deepen it, and only the final
    release restores the exact saved value. The lock covers each state
    transition together with its flag write, so overlapping async operation
    teardowns cannot restore out of order.

    The coordinator protects flag **restoration**, not query-row attribution:
    same-thread nested operations share one ``queries_log``, so an outer
    capture intentionally includes the nested interval.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active: dict[BaseDatabaseWrapper, _ActiveCapture] = {}

    def acquire(self, database_connection: "BaseDatabaseWrapper") -> _CaptureToken:
        """Enable debug-cursor logging on ``database_connection`` and return the token."""
        with self._lock:
            state = self._active.get(database_connection)
            if state is None:
                self._active[database_connection] = _ActiveCapture(
                    saved_force_debug_cursor=database_connection.force_debug_cursor,
                    depth=1,
                )
                database_connection.force_debug_cursor = True
            else:
                self._active[database_connection] = _ActiveCapture(
                    saved_force_debug_cursor=state.saved_force_debug_cursor,
                    depth=state.depth + 1,
                )
        return _CaptureToken(database_connection)

    def release(self, token: _CaptureToken) -> None:
        """Release one bracket; the final overlapping release restores the saved flag."""
        database_connection = token.database_connection
        with self._lock:
            state = self._active[database_connection]
            if state.depth > 1:
                self._active[database_connection] = _ActiveCapture(
                    saved_force_debug_cursor=state.saved_force_debug_cursor,
                    depth=state.depth - 1,
                )
            else:
                database_connection.force_debug_cursor = state.saved_force_debug_cursor
                del self._active[database_connection]


_coordinator = _CursorCaptureCoordinator()


def _serialize_sql_row(
    database_connection: "BaseDatabaseWrapper",
    entry: dict[str, Any],
) -> _DebugSQLRow:
    """Serialize one Django query-log ``entry`` to the six-key wire row.

    The wire keys are deliberate literals (a graphene client's existing
    tooling parses these exact bytes - never derive them through a casing
    helper), and ``isSlow`` / ``isSelect`` derive here, never at a call site.
    The logged statement is preserved verbatim: ``execute()`` entries arrive
    interpolated via ``ops.last_executed_query``; ``executemany()`` entries
    keep Django's raw ``"<N> times: <parameterized sql>"`` form (and are
    never a select).
    """
    sql = str(entry["sql"])
    duration = float(entry["time"])
    return {
        "vendor": database_connection.vendor,
        "alias": database_connection.alias,
        "sql": sql,
        "duration": duration,
        "isSlow": duration > _SLOW_QUERY_SECONDS,
        "isSelect": sql.lower().strip().startswith("select"),
    }


def _serialize_exception(exception: BaseException) -> _DebugExceptionRow:
    """Serialize ``exception`` to graphene's ``wrap_exception``-shaped triple.

    The three explicit ``format_exception`` arguments are load-bearing:
    serialization happens after graphql-core's ``except`` block finished, so
    ambient state (``traceback.format_exc()`` / ``sys.exc_info()``) is gone -
    the exception's own ``__traceback__`` is the durable source.
    """
    return {
        "excType": str(type(exception)),
        "message": str(exception),
        "stack": "".join(
            traceback.format_exception(type(exception), exception, exception.__traceback__),
        ),
    }


def _terminal_original_error(error: GraphQLError) -> BaseException:
    """Walk nested ``GraphQLError.original_error`` links to the terminal exception.

    The walk is doubly bounded: an identity set terminates malformed cycles
    and ``_MAX_ORIGINAL_ERROR_HOPS`` bounds a long acyclic chain (an identity
    set alone cannot). The stop behavior is deterministic - return the last
    unique candidate seen before a repeated identity or the hop ceiling - so
    a malformed consumer exception chain degrades to best-effort capture
    instead of failing the response. A terminal ``GraphQLError`` is retained:
    graphql-core uses that exact shape when a resolver explicitly raises
    ``GraphQLError``.
    """
    candidate = error.original_error
    seen_identities = {id(candidate)}
    for _ in range(_MAX_ORIGINAL_ERROR_HOPS):
        if not isinstance(candidate, GraphQLError):
            return candidate
        nested = candidate.original_error
        if nested is None or id(nested) in seen_identities:
            return candidate
        seen_identities.add(id(nested))
        candidate = nested
    return candidate


def _collect_exceptions(execution_result: Any) -> "list[_DebugExceptionRow]":
    """Serialize the execution exceptions represented by ``execution_result``'s errors.

    The single owner of the ``result is None`` / ``errors is None`` guards
    (on the sync parse/validation paths teardown runs before any result
    exists) and the ``original_error is not None`` filter (graphql-core's
    marker distinguishing an execution exception from a pure parse/validation
    error). Result-error order is preserved and distinct outer errors are
    never speculatively deduplicated.
    """
    if execution_result is None:
        return []
    errors = getattr(execution_result, "errors", None)
    if errors is None:
        return []
    rows: list[_DebugExceptionRow] = []
    for error in errors:
        if getattr(error, "original_error", None) is None:
            continue
        rows.append(_serialize_exception(_terminal_original_error(error)))
    return rows


def _query_log_entries_since(snapshot: _ConnectionSnapshot) -> list[dict[str, Any]]:
    """Return the query-log entries appended since ``snapshot`` was taken.

    Materializes the bounded deque (a deque is not sliceable) and clamps the
    start index, mirroring Django's own length-snapshot approach: it cannot
    raise when ``reset_queries()`` shortened the log, and it is explicitly
    **best effort after rollover** - once a full deque evicts old rows while
    staying the same length, a length snapshot cannot distinguish old from
    new entries and may omit some or all operation queries
    (``CaptureQueriesContext`` shares the limitation).
    """
    entries = list(snapshot.database_connection.queries_log)
    start = min(snapshot.query_log_start, len(entries))
    return entries[start:]


def _truncate(text: str, limit: int) -> str:
    """Cut ``text`` to ``limit`` characters, marking it when anything was dropped.

    The one truncation primitive both row families use, so the SQL and
    exception paths cannot drift in either the cut point or the marker.
    """
    if len(text) <= limit:
        return text
    return text[:limit] + _TRUNCATION_MARKER


def _row_cost(row: "Mapping[str, Any]") -> int:
    """The serialized character cost of one row, counting its string values only.

    The numeric and boolean values are bounded by their own types, so the
    variable cost of a row is exactly its strings. Counting anything else would
    make the budget depend on the repr of a float.
    """
    return sum(len(value) for value in row.values() if isinstance(value, str))


def _apply_payload_caps(
    sql_rows: "list[_DebugSQLRow]",
    exception_rows: "list[_DebugExceptionRow]",
) -> _DebugPayload:
    """Bound the assembled rows to the payload caps, deterministically (Decision 6).

    Three passes, in this fixed order, so the same operation always yields the
    same payload:

    1. **Per-row truncation.** Each row's variable-length strings are cut to
       their own limit and marked.
    2. **Row-count caps.** The EARLIEST rows are kept and the tail dropped: the
       first queries are the ones that explain how the operation started, and a
       tail-drop is stable under a re-run in a way that sampling is not.
    3. **One shared text budget.** Exception rows are admitted first because
       they explain a failure, then SQL rows, each row admitted whole while the
       running total of string characters stays within
       ``_MAX_PAYLOAD_TEXT_CHARS``. Admission STOPS at the first row that would
       exceed the budget rather than skipping it and trying the next - skipping
       would make the payload's content depend on individual row sizes rather
       than on their order.

    The two orderings are independent and both are contractual: the row-count
    cap keeps the EARLIEST rows within each list, and the budget spends itself on
    EXCEPTION rows before SQL rows. So a failing operation whose tracebacks
    exhaust the budget publishes no SQL at all, which is the intended trade - the
    exception rows are the ones that explain the failure the reader came for.
    Pass 1 also guarantees no single row can be refused on its own: the per-row
    limits cap one row's text far below the whole budget.

    Both lists are always present in the returned map, cap or no cap, so the
    wire contract is unchanged.
    """
    truncated_sql: list[_DebugSQLRow] = [
        {**row, "sql": _truncate(row["sql"], _MAX_SQL_TEXT_CHARS)}
        for row in sql_rows[:_MAX_SQL_ROWS]
    ]
    truncated_exceptions: list[_DebugExceptionRow] = [
        {
            **row,
            "message": _truncate(row["message"], _MAX_EXCEPTION_MESSAGE_CHARS),
            "stack": _truncate(row["stack"], _MAX_EXCEPTION_STACK_CHARS),
        }
        for row in exception_rows[:_MAX_EXCEPTION_ROWS]
    ]
    remaining = _MAX_PAYLOAD_TEXT_CHARS
    admitted_exceptions: list[_DebugExceptionRow] = []
    for exception_row in truncated_exceptions:
        cost = _row_cost(exception_row)
        if cost > remaining:
            break
        remaining -= cost
        admitted_exceptions.append(exception_row)
    admitted_sql: list[_DebugSQLRow] = []
    for sql_row in truncated_sql:
        cost = _row_cost(sql_row)
        if cost > remaining:
            break
        remaining -= cost
        admitted_sql.append(sql_row)
    return {"sql": admitted_sql, "exceptions": admitted_exceptions}


def _build_payload(snapshots: "list[_ConnectionSnapshot]", execution_result: Any) -> _DebugPayload:
    """Assemble the completed ``debug`` payload - the one place spelling its shape.

    Every call returns fresh list containers. The two collection phases each
    degrade independently - a failure is caught as ``Exception``, logged
    server-side, and costs only its own list - so the wire contract is unchanged
    (both lists are always present) and the operation's real ``data`` / ``errors``
    are never put at risk by a diagnostic. The two degrades are deliberately not
    symmetric, because what survives a failure differs:

    - **SQL collection degrades to the rows serialized so far**, across every
      snapshot already drained and partway through the failing one:
      ``list.extend`` appends each generated row as it is produced, so the rows
      that preceded the failure remain in the list.
    - **Exception collection degrades to an EMPTY list.** ``_collect_exceptions``
      builds and returns its own list, so a failure inside it leaves nothing to
      salvage; there is no partial list to adopt.

    A degraded exception list also hands the whole text budget to the SQL rows,
    since ``_apply_payload_caps`` spends it on exceptions first. The assembled
    rows then pass through that helper, so every payload this function returns is
    already bounded.
    """
    sql_rows: list[_DebugSQLRow] = []
    try:
        for snapshot in snapshots:
            # ``extend`` consumes the generator row by row, so rows serialized
            # before a failure survive the degrade below.
            sql_rows.extend(
                _serialize_sql_row(snapshot.database_connection, entry)
                for entry in _query_log_entries_since(snapshot)
            )
    except Exception:
        logger.exception(
            "DjangoDebugExtension: SQL diagnostic collection failed; the debug payload "
            "degrades to the rows serialized so far. The operation result is unaffected.",
        )
    try:
        exception_rows = _collect_exceptions(execution_result)
    except Exception:
        logger.exception(
            "DjangoDebugExtension: exception diagnostic collection failed; the debug "
            "payload degrades to an empty exceptions list. The operation result is "
            "unaffected.",
        )
        exception_rows = []
    return _apply_payload_caps(sql_rows, exception_rows)


class DjangoDebugExtension(SchemaExtension):
    """Attach Django query-log SQL and execution exceptions to ``extensions["debug"]``.

    Development tool - NEVER enable on an internet-facing schema: the payload
    carries unmasked exception details (type, message, traceback with server
    paths) and interpolated SQL parameter values, and the response containing
    them is routinely copied downstream (see the module docstring for the
    full disclosure surface).

    **Fails closed under ``settings.DEBUG = False``** (spec-048 Decision 5).
    At operation start the extension checks the setting; when it is false and
    the deployment has not acknowledged the disclosure, the extension is inert
    - it acquires no debug cursor, snapshots no query log, builds no payload,
    and ``get_results`` returns ``{}`` - and logs one warning naming the
    misconfiguration. The operation itself still runs normally: a diagnostic
    that refuses to disclose must not also refuse the request.

    Opt-in is the **class** in ``extensions=[..., DjangoDebugExtension]``:
    Strawberry (>=0.316.0) constructs class entries per operation with zero
    arguments and assigns ``execution_context`` afterward, so per-operation
    capture state lives in plain instance attributes. This deliberately
    differs from the optimizer's singleton-in-a-factory shape - the optimizer
    preserves a cross-request plan cache; this extension has no cross-request
    state. The ``__init__`` takes exactly one keyword-only argument,
    ``allow_unsafe_production``, whose ``False`` default is what a zero-argument
    class entry gets; acknowledging the disclosure is spelled as a factory
    entry, ``lambda: DjangoDebugExtension(allow_unsafe_production=True)``,
    which preserves the fresh-per-operation instance. Never pass a pre-built
    instance (the deprecated form the engine warns about at schema
    construction): a shared instance republishes a stale payload on later
    operations and races the engine-assigned ``execution_context``.

    List this class **after** any masking extension (``MaskErrors``):
    teardowns unwind LIFO, and masking strips ``original_error`` in its own
    teardown, so debug must tear down first to read the originals. Listed
    before it, ``exceptions`` reads ``[]``.

    Lifecycle: ``on_operation`` brackets every configured database connection
    with Django's own debug cursor (``force_debug_cursor``, saved-value
    restore, overlap-safe) pre-yield, and at teardown - inside ``finally``,
    so restoration cannot be skipped - slices each database connection's
    query log, serializes the rows and the result's ``original_error``
    chain, and stashes the payload **only when** ``execution_context.result``
    is a graphql-core ``ExecutionResult`` (GraphQL execution ran). Sync
    parse/validation early-returns leave ``result`` as ``None``; the async
    path may assign a strawberry ``PreExecutionError`` before teardown -
    neither is a graphql-core execution result, so the stash stays absent
    and ``get_results`` keeps returning ``{}`` even if the engine's
    early-result plus teardown-failure recovery path calls it a second
    time after teardown. ``get_results`` is a pure, idempotent read of that
    stash: ``{"debug": <payload>}`` once teardown published it, ``{}``
    otherwise.
    """

    # The absent-payload sentinel: one immutable class-level default, read
    # directly by ``get_results`` and shadowed on the INSTANCE only when
    # teardown assigns the completed dict. ``None`` is unambiguous because a
    # completed payload is always a dict, even when both lists are empty.
    _payload: "_DebugPayload | None" = None

    def __init__(self, *, allow_unsafe_production: bool = False) -> None:
        """Record the deployment's acknowledgement, defaulting to the safe answer.

        Keyword-only and defaulting to ``False`` so Strawberry's zero-argument
        construction of a bare class entry produces the fail-closed instance.
        Acknowledging is therefore something a deployment must SPELL, through
        the factory form ``lambda: DjangoDebugExtension(allow_unsafe_production=True)``
        - which keeps the fresh-per-operation instance a bare class entry gives.

        **A security acknowledgement must be a real ``bool``, so a non-bool is a
        ``ConfigurationError`` rather than a truthiness test.** Every string a
        deployment would plausibly reach for here - an environment variable read
        straight through, ``"false"``, ``"0"``, ``"no"`` - is TRUTHY, so accepting
        one would ARM the disclosure precisely in the case the author meant to
        refuse it. The gate that decides whether a production response carries
        unmasked tracebacks and interpolated SQL cannot be the gate that guesses.
        Raised at construction, the same rule and the same failure shape
        ``error_policy.py::ErrorPolicy.__post_init__`` applies to its own
        ``enabled`` flag.
        """
        if not isinstance(allow_unsafe_production, bool):
            raise ConfigurationError(
                "DjangoDebugExtension(allow_unsafe_production=...) must be a bool; got "
                f"{describe_value(allow_unsafe_production)}. A truthy non-bool would arm "
                "the production disclosure, so it is refused rather than interpreted.",
            )
        self.allow_unsafe_production = allow_unsafe_production

    def _disclosure_permitted(self) -> bool:
        """Whether this operation may publish the debug payload (spec-048 Decision 5).

        ``settings.DEBUG`` is read per operation rather than cached on the
        instance: the instance IS per operation, and a test or management
        context may legitimately flip the setting between two of them.
        Only the exact boolean ``True`` opens the development disclosure path;
        malformed truthy values fail closed.
        """
        return self.allow_unsafe_production or settings.DEBUG is True

    def on_operation(self) -> Any:  # type: ignore[override]
        """Bracket the operation with the debug cursor; assemble the payload at teardown.

        One synchronous generator serves both execution colors (the engine
        enters sync generator hooks on the async path too). The fail-closed
        gate is the first thing pre-yield, so a withheld operation pays for no
        bracket and no snapshot. Otherwise, pre-yield,
        ``ExitStack`` acquires a reference-counted bracket token and a
        query-log snapshot for every configured database connection - and
        unwinds the already-acquired connections if a later acquisition fails
        (setup stays fail-loud; nothing executed yet). Post-yield, inside
        ``finally``, the payload builder runs only when
        ``execution_context.result`` is a graphql-core ``ExecutionResult``
        (its diagnostic failures degrade, never raise) and the stack
        releases every token, the last overlapping release restoring each
        database connection's saved ``force_debug_cursor`` value.
        """
        if not self._disclosure_permitted():
            # Fail closed: no bracket is acquired, no query log is snapshotted,
            # no payload is built, and ``get_results`` keeps returning ``{}``.
            # The operation itself is untouched - a diagnostic that refuses to
            # disclose must not also refuse the request.
            logger.warning(
                "DjangoDebugExtension is installed on a schema running with settings.DEBUG "
                "false and no allow_unsafe_production acknowledgement; the debug payload is "
                "withheld. Remove the extension from this schema's extensions list, or pass "
                "lambda: DjangoDebugExtension(allow_unsafe_production=True) if the disclosure "
                "is deliberate.",
            )
            yield
            return
        snapshots: list[_ConnectionSnapshot] = []
        with ExitStack() as stack:
            for database_connection in connections.all():
                token = _coordinator.acquire(database_connection)
                stack.callback(_coordinator.release, token)
                snapshots.append(
                    _ConnectionSnapshot(
                        database_connection=database_connection,
                        query_log_start=len(database_connection.queries_log),
                    ),
                )
            try:
                yield
            finally:
                # Publish only when GraphQL execution assigned a graphql-core
                # ``ExecutionResult``. Parse/validation early-returns leave
                # ``result`` as ``None`` (sync) or a strawberry
                # ``PreExecutionError`` (async ``_handle_execution_result``);
                # stashing an empty payload for those shapes lets the engine's
                # early-return + teardown-failure recovery path's second
                # ``get_results`` call publish ``debug`` for an operation that
                # never executed (the no-``debug``-key contract).
                result = self.execution_context.result
                if isinstance(result, GraphQLExecutionResult):
                    self._payload = _build_payload(snapshots, result)

    def get_results(self) -> dict[str, Any]:
        """Return ``{"debug": <payload>}`` once the stash exists, else ``{}``.

        A pure, idempotent read: never a mutate-or-pop, never a write to
        ``execution_context`` or an existing result-extensions map. Absent
        stash (the parse/validation early-return paths call this before the
        hook's teardown) contributes ``{}`` so no ``debug`` key is published
        for an operation that never executed.
        """
        payload = self._payload
        if payload is None:
            return {}
        return {"debug": payload}
