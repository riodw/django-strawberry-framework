"""Optimizer <-> resolver context hand-off: the optimizer's own stash keys.

The shape-agnostic read / write / delete dispatch lives in
``utils/context.py`` and is shared with the request resource policy
(``resource_policy.py``); this module owns only the optimizer's key
vocabulary and its start-of-execution reset. ``get_context_value`` and
``stash_on_context`` are re-exported here because the optimizer subpackage and
its tests have always reached for them at this path.
"""

from __future__ import annotations

from typing import Any

from ..utils.context import clear_context_key, get_context_value, stash_on_context

__all__ = (
    "DST_OPTIMIZER_FK_ID_ELISIONS",
    "DST_OPTIMIZER_KEYS",
    "DST_OPTIMIZER_LOOKUP_PATHS",
    "DST_OPTIMIZER_PLAN",
    "DST_OPTIMIZER_PLANNED",
    "DST_OPTIMIZER_STRICTNESS",
    "clear_optimizer_context",
    "get_context_value",
    "stash_on_context",
)

DST_OPTIMIZER_PLAN = "dst_optimizer_plan"
DST_OPTIMIZER_FK_ID_ELISIONS = "dst_optimizer_fk_id_elisions"
DST_OPTIMIZER_PLANNED = "dst_optimizer_planned"
DST_OPTIMIZER_LOOKUP_PATHS = "dst_optimizer_lookup_paths"
DST_OPTIMIZER_STRICTNESS = "dst_optimizer_strictness"

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
    runs so sequential ``execute`` / ``execute_sync`` calls that reuse the
    same ``context_value`` object cannot leak correctness sentinels:

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
