"""Optimizer <-> resolver context hand-off: the optimizer's stash keys and its per-execution frame.

The shape-agnostic read / write / delete dispatch lives in
``utils/context.py`` and is shared with the request resource policy
(``resource_policy.py``); this module owns the optimizer's key vocabulary, its
start-of-execution reset, and the per-execution frame every other module in the
subpackage reads its own scratch out of. ``get_context_value`` and
``stash_on_context`` are re-exported here because the optimizer subpackage and
its tests have always reached for them at this path.

The frame is here rather than in ``extension.py`` because its readers cannot
import that module: the walker, the selection adapter and the nested-fetch
strategy are all below the extension in the dependency order, and each used to
own a ``ContextVar`` of its own for state whose lifetime was the extension's to
decide. One frame, opened and closed at ``on_execute``, is that lifetime written
once.
"""

from __future__ import annotations

import contextlib
from contextvars import ContextVar
from typing import Any, NamedTuple

from ..utils.context import clear_context_key, get_context_value, stash_on_context
from ..utils.operation_lease import OperationLease

__all__ = (
    "DST_OPTIMIZER_FK_ID_ELISIONS",
    "DST_OPTIMIZER_KEYS",
    "DST_OPTIMIZER_LOOKUP_PATHS",
    "DST_OPTIMIZER_PLAN",
    "DST_OPTIMIZER_PLANNED",
    "DST_OPTIMIZER_STRICTNESS",
    "active_nested_strategy",
    "active_optimizer",
    "active_strictness",
    "begin_execution_frame",
    "cache_key_parts_memo",
    "clear_optimizer_context",
    "converted_selections_memo",
    "end_execution_frame",
    "execution_plan_memo",
    "get_context_value",
    "operation_publishes_to_context",
    "optimizer_value",
    "publish_scoped_relations",
    "relation_is_optimizer_scoped",
    "stash_for_optimizer",
    "stash_on_context",
)

DST_OPTIMIZER_PLAN = "dst_optimizer_plan"
DST_OPTIMIZER_FK_ID_ELISIONS = "dst_optimizer_fk_id_elisions"
DST_OPTIMIZER_PLANNED = "dst_optimizer_planned"
DST_OPTIMIZER_LOOKUP_PATHS = "dst_optimizer_lookup_paths"
DST_OPTIMIZER_STRICTNESS = "dst_optimizer_strictness"

#: One managed execution's scratch, and the lease every reader reaches it through.
#:
#: Eight per-execution values used to be eight ``ContextVar`` entries, each set
#: at ``on_execute`` entry and reset on the way out. Reset is the wrong
#: instrument for every one of them: ``asyncio.create_task`` copies the whole
#: context, a token rewrites only the context that created it, and so a
#: resolver's background task kept reading - and keeping alive - a completed
#: operation's plans, converted selections, cache keys and stashes for as long
#: as it ran. One frame behind one lease
#: (``utils/operation_lease.py::OperationLease``) is the same state with an end:
#: closing it at the end of the execution is observable from every context
#: copied before, so a stale copy answers exactly as a context with no optimizer
#: running does.
#:
#: The frame carries what one execution publishes to itself:
#:
#: - ``optimizer`` is the running extension instance, which
#:   ``apply_connection_optimization`` discovers so a connection field shares
#:   the instance-bound plan cache (spec-030 Decision 11). Its presence is also
#:   the sole "an optimizer is running here" signal, which is why it belongs to
#:   the frame rather than beside it: an instance read out of a copied context
#:   would answer that question with a dead operation's yes.
#: - ``strategy`` is that instance's nested-connection fetch strategy, published
#:   for the walker, which cannot import the extension module (the dependency
#:   points the other way; see ``nested_fetch.py::active_strategy``).
#: - ``strictness`` is armed for the whole operation before any planning runs,
#:   so a relation the walker never planned - including one on an operation it
#:   could not plan at all - is still visible to ``types/resolvers.py``'s N+1
#:   check. Neither a context stash nor the published plan can answer that: the
#:   stash is unavailable to an execution running without a ``context_value``,
#:   and it is written at plan-publish time, which an operation whose root
#:   resolver returns a materialized list never reaches.
#: - ``scoped_relations`` records which relations the walker PLANNED, for the
#:   generated relation resolvers to tell an optimizer-built child cache - one
#:   that therefore passed through the target type's ``get_queryset`` - from one
#:   a consumer populated with its own ``prefetch_related``. A mutable set
#:   updated in place, so a nested connection's fallback publish adds to the
#:   keys rather than replacing them.
#: - ``plans`` memoizes plans this execution BUILT, which is the job the
#:   cross-request plan cache deliberately refuses: an uncacheable plan (one
#:   baking a request-scoped ``get_queryset`` queryset or a consumer
#:   ``Prefetch`` hint) is rebuilt per parent row without it, every row sharing
#:   one cache key. Safe because one execution has a single fixed
#:   ``info.context``, so such a plan filters identically for every parent.
#: - ``key_parts`` memoizes the operation-constant cache-key parts - the
#:   rendered document key and the resolved variable frozenset - keyed by
#:   ``id(operation)``. Reusing one frozenset also means its hash is computed
#:   once, which keeps the per-row plan-cache key cheap.
#: - ``converted`` memoizes the converted-selection tree by field-node ids, so
#:   the per-parent-row ``prime_selected_fields`` calls of a fallback connection
#:   convert once. AST node ids are stable for the frame's whole lifetime
#:   because the document belongs to the execution the frame belongs to.
#: - ``stashes`` is the operation's own optimizer stash store, and the one
#:   member the frame borrows rather than owns: it belongs to the extension's
#:   operation state, which the runner owns and which dies with the request.
#:   The keys it mirrors live on ``info.context``, and that object belongs to
#:   the REQUEST rather than to one operation - a resolver that runs an inner
#:   ``info.schema.execute_sync(..., context_value=info.context)`` would
#:   otherwise hand the inner optimizer the outer operation's store, where its
#:   start-of-execution clear erases the outer plan, the FK-id elisions a stub
#:   read depends on, and the planned-relation keys an N+1 guard reads.
#:
#: ``publishes_to_context`` says whether the operation holding the frame is the
#: one the request context describes. A task's outermost managed operation is,
#: and publishes every stash there as well, because a published plan is
#: introspection a consumer may read off their own request. An operation nested
#: inside that one keeps its publishes to its own mapping, which is what leaves
#: the outer operation's values readable to the outer resolvers that have not
#: run yet - and leaves them readable after the outer operation ends, for the
#: consumer holding the request.
#:
#: Nesting is a fact about the RUNNER that owns the operation
#: (``extensions/operation_state.py::operation_is_nested``), not about which
#: optimizer hook happens to be running: an operation started from a consumer
#: extension's teardown or from result collection begins after the outer
#: optimizer's own executing hook has closed its frame, and is still inside the
#: outer operation. The live-frame check answers the one case the runner cannot,
#: a plain ``strawberry.Schema`` nesting an execution inside a resolver, where
#: no package runner exists on either side.


class _ExecutionFrame:
    """The scratch one managed execution publishes to itself.

    ``__slots__`` because every member is reached from the optimizer's hot path
    and an attribute grown by a typo is a memo nothing would ever read back.
    """

    __slots__ = (
        "converted",
        "key_parts",
        "optimizer",
        "plans",
        "publishes_to_context",
        "scoped_relations",
        "stashes",
        "strategy",
        "strictness",
    )

    def __init__(
        self,
        stashes: dict[str, Any],
        *,
        publishes_to_context: bool,
        optimizer: Any,
        strategy: Any,
        strictness: str | None,
    ) -> None:
        self.stashes = stashes
        self.publishes_to_context = publishes_to_context
        self.optimizer = optimizer
        self.strategy = strategy
        self.strictness = strictness
        self.scoped_relations: set[str] = set()
        self.plans: dict[Any, Any] = {}
        self.key_parts: dict[int, tuple[str, frozenset[tuple[str, Any]]]] = {}
        self.converted: dict[Any, list[Any]] = {}

    def clear(self) -> None:
        """Empty every store this frame owns, at the end of the execution.

        The lease is what stops a copied context reaching the frame at all, so
        this is for the containers themselves: a memo handed to a caller that
        kept it - the walker's converted selections, a built plan - is emptied
        rather than left holding a request's querysets for as long as that
        caller lives.

        ``stashes`` is not emptied. It belongs to the extension's operation
        state, which the runner owns for the whole request and which result
        collection still reads; it ends when the runner does.
        """
        self.scoped_relations.clear()
        self.plans.clear()
        self.key_parts.clear()
        self.converted.clear()


class _FrameScope(NamedTuple):
    """One execution frame's lease and the token that restores the enclosing one."""

    lease: OperationLease[_ExecutionFrame]
    token: Any


_execution_frames: ContextVar[OperationLease[_ExecutionFrame] | None] = ContextVar(
    "django_strawberry_framework_optimizer_execution_frame",
    default=None,
)


def _active_frame() -> _ExecutionFrame | None:
    """The frame of the execution running here, or ``None``.

    ``None`` for a caller outside every managed execution - a direct call into a
    generated resolver, a test invoking a helper on its own - and ``None`` again
    in a task that copied a frame binding and outlived the execution that made
    it. Every reader in this module goes through here, so no accessor can infer
    that an optimizer is running from a value a copied context still holds.
    """
    lease = _execution_frames.get()
    return None if lease is None else lease.held()


def begin_execution_frame(
    stashes: dict[str, Any],
    *,
    nested: bool,
    optimizer: Any = None,
    strategy: Any = None,
    strictness: str | None = None,
) -> _FrameScope:
    """Open this execution's frame; returns the scope :func:`end_execution_frame` closes.

    ``nested`` is the runner's answer, and an execution that opens a frame while
    another one is still live is nested whatever the runner says. Either way the
    request context object stays the outer operation's medium.
    """
    frame = _ExecutionFrame(
        stashes,
        publishes_to_context=not (nested or _active_frame() is not None),
        optimizer=optimizer,
        strategy=strategy,
        strictness=strictness,
    )
    lease = OperationLease(frame)
    return _FrameScope(lease, _execution_frames.set(lease))


def end_execution_frame(scope: _FrameScope) -> None:
    """Close the frame opened by :func:`begin_execution_frame`.

    Closing first, and unconditionally: it is what every context copied from
    this one observes, and it is the half that works from whichever task is
    running this teardown. The reset is the local half, restoring an enclosing
    execution's frame to this context alone, and a token created in another
    context has nothing here to restore.
    """
    frame = scope.lease.held()
    scope.lease.close()
    if frame is not None:
        frame.clear()
    with contextlib.suppress(ValueError):  # token created in a different Context
        _execution_frames.reset(scope.token)


def active_optimizer() -> Any:
    """The extension instance running this execution, or ``None`` outside one."""
    frame = _active_frame()
    return None if frame is None else frame.optimizer


def active_nested_strategy() -> Any:
    """The nested-connection strategy this execution planned with, or ``None``."""
    frame = _active_frame()
    return None if frame is None else frame.strategy


def active_strictness() -> str | None:
    """Return the strictness in force this execution, or ``None`` if no optimizer runs."""
    frame = _active_frame()
    return None if frame is None else frame.strictness


def execution_plan_memo() -> dict[Any, Any] | None:
    """This execution's built-plan memo, or ``None`` outside a managed execution."""
    frame = _active_frame()
    return None if frame is None else frame.plans


def cache_key_parts_memo() -> dict[int, tuple[str, frozenset[tuple[str, Any]]]] | None:
    """This execution's cache-key-parts memo, or ``None`` outside a managed execution."""
    frame = _active_frame()
    return None if frame is None else frame.key_parts


def converted_selections_memo() -> dict[Any, list[Any]] | None:
    """This execution's converted-selection memo, or ``None`` outside a managed execution."""
    frame = _active_frame()
    return None if frame is None else frame.converted


def publish_scoped_relations(keys: Any) -> None:
    """Record ``keys`` as optimizer-planned for this execution (idempotent union)."""
    if not keys:
        return
    frame = _active_frame()
    if frame is not None:
        frame.scoped_relations.update(keys)


def relation_is_optimizer_scoped(key: str) -> bool:
    """Return whether ``key`` names a relation the optimizer planned this execution."""
    frame = _active_frame()
    if frame is None:
        return False
    try:
        return key in frame.scoped_relations
    except TypeError:
        return False


def operation_publishes_to_context() -> bool:
    """Return whether the operation running here is the request context's own.

    ``False`` outside a managed execution, which has no operation to publish
    for: a direct call into a generated resolver reads and writes the context
    object because that is the only store it has, and does so through
    :func:`optimizer_value` and :func:`stash_for_optimizer` rather than through
    this.
    """
    frame = _active_frame()
    return frame is not None and frame.publishes_to_context


def optimizer_value(context: Any, key: str, default: Any = None) -> Any:
    """Read one optimizer stash for the operation running here.

    The running operation's own mapping answers, without falling through to the
    context object: a value another operation published there is not this
    operation's, and a value this operation published is not on the object at
    all when the context is read-only. Outside a managed execution the context
    object answers, which is the only store an unmanaged caller has.
    """
    frame = _active_frame()
    if frame is None:
        return get_context_value(context, key, default)
    return frame.stashes.get(key, default)


def stash_for_optimizer(context: Any, key: str, value: Any) -> None:
    """Publish one optimizer stash for this operation, and on the request context.

    Two destinations with two different jobs: the operation's mapping is what
    the package reads back, and the context object keeps the published values
    visible to a consumer inspecting their own request. Only the operation that
    object describes writes there, so an inner execution sharing it replaces
    nothing the outer one published. A frozen or absent context silently takes
    nothing, exactly as ``stash_on_context`` documents, and the operation still
    has its own copy.
    """
    frame = _active_frame()
    if frame is None:
        stash_on_context(context, key, value)
        return
    frame.stashes[key] = value
    if frame.publishes_to_context:
        stash_on_context(context, key, value)


# Every key ``stash_on_context`` / ``_publish_plan_to_context`` may leave on a
# request context. ``clear_optimizer_context`` removes exactly this set at the
# start of each ``on_execute`` so a reused ``context_value`` cannot carry
# FK-id elisions or planned-resolver sentinels into a later operation.
DST_OPTIMIZER_KEYS: tuple[str, ...] = (
    DST_OPTIMIZER_PLAN,
    DST_OPTIMIZER_FK_ID_ELISIONS,
    DST_OPTIMIZER_PLANNED,
    DST_OPTIMIZER_LOOKUP_PATHS,
    DST_OPTIMIZER_STRICTNESS,
)


def clear_optimizer_context(context: Any) -> None:
    """Remove every optimizer stash key from ``context`` (start-of-execution reset).

    ``DjangoOptimizerExtension.on_execute`` calls this before the operation
    runs, and only for the operation the context object describes, so
    sequential ``execute`` / ``execute_sync`` calls that reuse the same
    ``context_value`` object cannot leak correctness sentinels to a consumer
    reading them - while an operation nested inside another one erases nothing
    the outer operation published there:

    - ``DST_OPTIMIZER_FK_ID_ELISIONS`` retained across executions makes a later
      full-object selection (``category { id name }``) hit the FK-id stub path
      and return empty scalars for fields the stub never loaded.
    - ``DST_OPTIMIZER_PLANNED`` retained across executions masks real N+1s under
      ``strictness="warn"|"raise"`` (keys planned for a prior operation still
      short-circuit ``_check_n1``).

    Intra-execution ``_stash_union`` (parent + nested connection publishes)
    stays correct: the clear runs once at ``on_execute`` entry, then unions
    accumulate only within that operation.

    Per-key deletion is delegated to ``utils/context.py::clear_context_key``,
    whose dispatch mirrors ``stash_on_context``; missing keys and read-only
    contexts are silently skipped there.
    """
    if context is None:
        return
    for key in DST_OPTIMIZER_KEYS:
        clear_context_key(context, key)
