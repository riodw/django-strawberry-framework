"""Optimizer <-> resolver context hand-off: the optimizer's own stash keys.

The shape-agnostic read / write / delete dispatch lives in
``utils/context.py`` and is shared with the request resource policy
(``resource_policy.py``); this module owns only the optimizer's key
vocabulary and its start-of-execution reset. ``get_context_value`` and
``stash_on_context`` are re-exported here because the optimizer subpackage and
its tests have always reached for them at this path.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, NamedTuple

from ..utils.context import clear_context_key, get_context_value, stash_on_context

__all__ = (
    "DST_OPTIMIZER_FK_ID_ELISIONS",
    "DST_OPTIMIZER_KEYS",
    "DST_OPTIMIZER_LOOKUP_PATHS",
    "DST_OPTIMIZER_PLAN",
    "DST_OPTIMIZER_PLANNED",
    "DST_OPTIMIZER_STRICTNESS",
    "active_strictness",
    "begin_operation_stashes",
    "begin_scoped_relations",
    "begin_strictness",
    "clear_optimizer_context",
    "end_operation_stashes",
    "end_scoped_relations",
    "end_strictness",
    "get_context_value",
    "optimizer_operation_is_active",
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

#: Resolver keys for relations the optimizer PLANNED, for the CURRENT execution.
#:
#: A generated relation resolver must tell a child cache the optimizer built -
#: and which therefore already passed through the target type's ``get_queryset``
#: - from one a consumer populated with its own ``prefetch_related``, which never
#: saw that hook. Neither request-context sentinel can answer that:
#: ``DST_OPTIMIZER_PLANNED`` carries the right keys but only under a non-default
#: ``strictness``, and every context stash is unavailable to an execution that
#: runs without a ``context_value`` at all. A ``ContextVar`` has neither limit,
#: and it is the mechanism the optimizer already uses to publish per-execution
#: state the walker and connection helper read (``extension.py``'s
#: ``_active_optimizer`` / ``_active_nested_strategy``).
#:
#: A mutable set updated in place, so a nested connection's fallback publish adds
#: to the parent's keys rather than replacing them. ``extension.py::on_execute``
#: owns the per-execution set/reset; ``None`` means no optimizer is running here,
#: which is indistinguishable from "planned nothing" for every reader.
_scoped_relations: ContextVar[set[str] | None] = ContextVar(
    "django_strawberry_framework_optimizer_scoped_relations",
    default=None,
)


def publish_scoped_relations(keys: Any) -> None:
    """Record ``keys`` as optimizer-planned for this execution (idempotent union)."""
    if not keys:
        return
    scoped = _scoped_relations.get()
    if scoped is not None:
        scoped.update(keys)


def relation_is_optimizer_scoped(key: str) -> bool:
    """Return whether ``key`` names a relation the optimizer planned this execution."""
    scoped = _scoped_relations.get()
    if scoped is None:
        return False
    try:
        return key in scoped
    except TypeError:
        return False


#: The strictness in force for the CURRENT execution, or ``None`` when no
#: optimizer is running here.
#:
#: ``_check_n1`` must know whether a consumer armed ``"warn"`` / ``"raise"``
#: before it decides to stay silent. ``DST_OPTIMIZER_STRICTNESS`` cannot answer
#: that on its own: the stash is unavailable to an execution that runs without a
#: ``context_value``, and it is written at plan-publish time, so an operation
#: whose root resolver returns something the walker cannot plan (a materialized
#: list) never publishes it at all. Both shapes leave a configured N+1 guard
#: silently disarmed. A ``ContextVar`` set at ``on_execute`` entry is armed for
#: the whole operation regardless of context shape or planning outcome.
_active_strictness: ContextVar[str | None] = ContextVar(
    "django_strawberry_framework_optimizer_strictness",
    default=None,
)


def active_strictness() -> str | None:
    """Return the strictness in force this execution, or ``None`` if no optimizer runs."""
    return _active_strictness.get()


def begin_strictness(strictness: str) -> Any:
    """Arm ``strictness`` for this execution; returns the reset token."""
    return _active_strictness.set(strictness)


def end_strictness(token: Any) -> None:
    """Disarm the strictness armed by ``begin_strictness``."""
    _active_strictness.reset(token)


def begin_scoped_relations() -> Any:
    """Open a per-execution scoped-relation set; returns the reset token."""
    return _scoped_relations.set(set())


def end_scoped_relations(token: Any) -> None:
    """Close the per-execution scoped-relation set opened by ``begin_scoped_relations``."""
    _scoped_relations.reset(token)


#: The stash store owned by the optimizer operation running in this task.
#:
#: The keys below live on ``info.context``, and that object belongs to the
#: REQUEST rather than to one operation: a resolver that runs an inner
#: ``info.schema.execute_sync(..., context_value=info.context)`` hands the inner
#: optimizer the outer operation's store, where its start-of-execution clear
#: erases the outer plan, the FK-id elisions a stub read depends on, and the
#: planned-relation keys an N+1 guard reads - and its own publishes then answer
#: the outer resolvers that are still running.
#:
#: So the authoritative store for a managed execution is this one, which
#: ``extension.py::DjangoOptimizerExtension.on_execute`` opens from its own
#: operation state and closes by token. ``None`` means no optimizer operation is
#: running here, and the context object answers reads and takes writes exactly
#: as it does for a direct call into a generated resolver.
#:
#: ``publishes_to_context`` says whether the operation holding the store is the
#: one the request context describes. A task's outermost managed operation is,
#: and publishes every stash there as well, because a published plan is
#: introspection a consumer may read off their own request. An operation nested
#: inside that one keeps its publishes to its own mapping, which is what leaves
#: the outer operation's values readable to the outer resolvers that have not
#: run yet.


class _OperationStore(NamedTuple):
    """One managed execution's optimizer stashes, and whether they are the request's."""

    stashes: dict[str, Any]
    publishes_to_context: bool


_operation_stashes: ContextVar[_OperationStore | None] = ContextVar(
    "django_strawberry_framework_optimizer_operation_stashes",
    default=None,
)


def optimizer_operation_is_active() -> bool:
    """Return whether a managed optimizer execution owns the stashes read here."""
    return _operation_stashes.get() is not None


def begin_operation_stashes(stashes: dict[str, Any]) -> Any:
    """Make ``stashes`` this execution's optimizer store; returns the reset token.

    An execution that opens a store while another already holds one runs nested
    inside it, so the request context object stays the outer operation's medium.
    """
    return _operation_stashes.set(
        _OperationStore(stashes, publishes_to_context=not optimizer_operation_is_active()),
    )


def end_operation_stashes(token: Any) -> None:
    """Close the store opened by :func:`begin_operation_stashes`."""
    _operation_stashes.reset(token)


def optimizer_value(context: Any, key: str, default: Any = None) -> Any:
    """Read one optimizer stash for the operation running here.

    The running operation's own mapping answers, without falling through to the
    context object: a value another operation published there is not this
    operation's, and a value this operation published is not on the object at
    all when the context is read-only. Outside a managed execution the context
    object answers, which is the only store an unmanaged caller has.
    """
    store = _operation_stashes.get()
    if store is None:
        return get_context_value(context, key, default)
    return store.stashes.get(key, default)


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
    store = _operation_stashes.get()
    if store is None:
        stash_on_context(context, key, value)
        return
    store.stashes[key] = value
    if store.publishes_to_context:
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
