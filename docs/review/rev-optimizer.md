# Folder review: `django_strawberry_framework/optimizer/`

Status: verified

## DRY analysis

- **Existing patterns reused (folder scope).** Every cross-file collaboration inside `optimizer/` already routes through a single documented helper, and no sibling re-implements another sibling's contract:
  - Context read/write contract lives in `_context.py:90-141` with the five `DST_OPTIMIZER_*` constants at `_context.py:34-38`; the two production consumers (`extension.py:46,53` and the resolver-side `types/resolvers.py:31-38` outside this folder) import the symbols rather than redefining the literals. `grep '"dst_optimizer' django_strawberry_framework/optimizer/` shows the bare strings appear nowhere in the folder outside `_context.py`.
  - Plan mutators (`append_unique`, `append_unique_many`, `append_prefetch_unique`) and `OptimizationPlan` itself live in `plans.py:215-243` and are reused at 6+ walker call sites (`walker.py:206,213,298,329,341,353-354,422,497-499,601`) — no sibling carries its own dedupe loop.
  - Plan reconciliation (`diff_plan_for_queryset`), runtime-path extraction (`runtime_path_from_info`, `lookup_paths`), brittle Django-private wrappers (`_lookup_path` for `Prefetch.prefetch_to`, `_consumer_prefetch_lookups` for `QuerySet._prefetch_related_lookups`, `_consumer_only_fields` for `query.deferred_loading`, `_flatten_select_related` for `query.select_related`) all live in `plans.py` and are consumed by `extension.py:57` and `walker.py:18`.
  - Skip-hint identity dispatch is funnelled through `hints.py:129-146` (`hint_is_skip`) and consumed at `walker.py:412` and `extension.py:56,683`; no sibling open-codes the `hint is OptimizerHint.SKIP` check.
  - Cardinality classification is funnelled through `utils/relations.py:39-70` (`relation_kind`, `is_many_side_relation_kind`) and consumed at `walker.py:14,74,433,585` and `field_meta.py:26-30,106,111,161`. Both sites went through the post-Worker-2 DRY consolidation (per `rev-optimizer__field_meta.md` Medium 1).
  - `OptimizerError` / `ConfigurationError` from `exceptions.py` are the only exception types raised inside the folder (`field_meta.py:25,135`, `hints.py:33,84-101`, `walker.py:12,433-435,475,483`); no sibling defines a parallel hierarchy.
  - The folder `logger` is declared once at the top-level package and re-exported by `optimizer/__init__.py:21` so `extension.py:45` and `walker.py:16` import `from . import logger` rather than calling `logging.getLogger(...)` per module. Two sites are the only writers (`walker.py:68,623,693` and `extension.py:552`); the `"django_strawberry_framework"` literal appears in exactly one place in the package.
- **New helpers a fix might justify (folder scope).** None large; the cycle's per-file artifacts already considered the candidates:
  - `_walk_selection_tree(on_node=...)` visitor that would collapse `extension.py:_walk_directives` (`extension.py:91-127`) and `extension.py:_walk_reachable_fragment_definitions` (`extension.py:198-226`). Evaluated below at Low §1 — defer.
  - `RelationPlanCtx` dataclass that would let `walker.py`'s four 9-/10-arg planner call sites collapse. Evaluated below at Low §2 — defer.
  - `_resolve_origin_for_type_name(strawberry_schema, type_name)` shared between `extension.py:_collect_schema_reachable_types._walk_gql_type` (`extension.py:336-363`) and `extension.py:_resolve_model_from_return_type` (`extension.py:389-420`). Two call sites — below the bar; carry forward to project pass if a third lands.
- **Duplication risk across the folder.** The shadow overviews' Repeated-string-literals sections show **no literal appears in two or more sibling overviews**. Every repeated literal listed is intra-file: `_strawberry_schema` (extension 2x, already extracted to the helper pair at `extension.py:300-317`), `reverse_many_to_one` / `reverse_one_to_one` (field_meta 2x each, already verified after the DRY consolidation against `MANY_SIDE_RELATION_KINDS`), `prefetch_to` / `queryset` (plans 2x, already funnelled through `_lookup_path` + `_consumer_prefetch_lookups`), `prefetch` / `selections` / `related_model` / `target_field` / `directives` / `arguments` (walker 2-3x, all in natural docstring/code positions per the walker artifact). The cross-file DRY check is clean: no folder-scope DRY consolidation is needed.

## High:

None.

## Medium:

None.

## Low:

### Parallel AST walker collapse (forwarded from `rev-optimizer__extension.md` L3): defer

The two AST walkers `_walk_directives` (`extension.py:91-127`) and `_walk_reachable_fragment_definitions` (`extension.py:198-226`) share the recursion shape (iterate `_child_selections`, follow fragment spreads via `_unvisited_fragment_definition`, carry the visited-fragments cycle guard). The divergence is the per-node hook (directives-name sweep vs append-to-reachable-list). The folder-pass question is whether a `_walk_selection_tree(node, fragments, visited, *, on_node)` visitor at folder scope is justified.

Decision: **defer**. The parallel walkers already factor their two shared helpers (`_child_selections` at `extension.py:130-144`, `_unvisited_fragment_definition` at `extension.py:147-174`) into one site each, so the remaining duplication is the ~10-line recurse-down-and-resolve-fragment skeleton inside each walker. Introducing a visitor callable today would add an indirection (one more named function in the AST helpers band) without removing meaningful surface — at most ~15 lines net. The visitor pays off only if a third walker lands (e.g., when a future spec needs to gather aliased response keys, argument shapes, or directive arguments from the same traversal). Carry forward to the project pass: if a third walker is introduced anywhere in the package, fold all three through the visitor at that point.

```django_strawberry_framework/optimizer/extension.py:91:127
def _walk_directives(...) -> None:
    ...
    for child in _child_selections(node):
        _walk_directives(child, names, fragments, visited_fragments)
        frag_def = _unvisited_fragment_definition(child, fragments, visited_fragments)
        if frag_def is not None:
            _walk_directives(frag_def, names, fragments, visited_fragments)
```

### `RelationPlanCtx` dataclass evaluation (forwarded from `rev-optimizer__walker.md` L3): defer

`_apply_hint`'s `force_select` and `force_prefetch` branches at `walker.py:427-467` re-pass identical 9-/10-arg positional sequences to `_plan_prefetch_relation` and `_plan_select_relation`, mirroring the default-dispatch call sites at `walker.py:248-273`. The folder-pass question is whether converting the planner signatures to take a `RelationPlanCtx(sel, django_field, django_name, type_cls, target_type, plan, prefix, full_path, info, runtime_paths, resolver_identities)` dataclass is justified at folder scope.

Decision: **defer**. The four call sites that would benefit are all inside `walker.py`; the duplication is mechanical (the planners' positional argument lists *are* the surface) and not cross-file. Introducing a dataclass would touch `_plan_select_relation` and `_plan_prefetch_relation` signatures (both private to `walker.py`), `_walk_selections`'s default dispatch (two call sites at `walker.py:248-273`), and `_apply_hint`'s force branches — five callers within one file. Without an 11th argument the dataclass would not change line count meaningfully; it would mostly shift the positional-vs-keyword surface. The walker artifact's calibration ("the planners' positional argument lists ARE the surface") stands: defer until a planner gains an 11th argument or a third file (outside `walker.py`) needs to construct one of these planner calls. This is recorded as the **trigger condition** for the refactor; no in-cycle action.

```django_strawberry_framework/optimizer/walker.py:427:467
    if hint.force_select:
        ...
        _plan_select_relation(
            sel, django_field, django_name, type_cls, target_type,
            plan, prefix, full_path, info, runtime_paths, resolver_identities,
        )
        return True
    if hint.force_prefetch:
        _plan_prefetch_relation(
            sel, django_field, target_type,
            plan, prefix, full_path, info, runtime_paths, resolver_identities,
        )
        return True
```

### `_context.py` underscore convention scope (forwarded from `rev-optimizer___context.md` L2): keep as a sample of one

`_context.py` is the only leading-underscore module in `optimizer/`. The convention signals "private to the subpackage" — the file holds the read/write helpers for `info.context` and is imported only by `extension.py:46,53` (and the resolver-side `types/resolvers.py:31-38` outside this folder) via fully-qualified `from ..optimizer._context import …`. The folder-pass question is whether the underscore convention should extend to other implementation-detail-only modules in `optimizer/`.

Decision: **keep as a sample of one**. The other five sibling modules (`extension.py`, `field_meta.py`, `hints.py`, `plans.py`, `walker.py`) all have at least one of the following: (a) consumer-visible names already re-exported from the top-level package (`OptimizerHint` from `hints.py`, `DjangoOptimizerExtension` from `extension.py`), (b) names that *could* be imported by future external integrations (`OptimizationPlan` from `plans.py`, `plan_optimizations`/`plan_relation` from `walker.py`), or (c) types that consumer-facing modules document (`FieldMeta` in `field_meta.py` is referenced in `DjangoTypeDefinition.field_map`'s annotation at `types/definition.py:25`). Only `_context.py`'s surface (`get_context_value`, `stash_on_context`, the five sentinel constants) is genuinely cross-subpackage but never consumer-facing — extension and resolvers route through it, but no consumer code or test fixture would meaningfully import from it. The convention is **earned** by the file's actual role and should not be applied retroactively to siblings just for uniformity. Worker 1 calibration: applying the convention more broadly would invite consumers to import the underscore-suffixed names anyway (since Python doesn't enforce the convention at the package boundary), and a single underscore-prefixed file is the right shape for an otherwise-public subpackage with one shared-state module.

```django_strawberry_framework/optimizer/_context.py:1:1
"""Shared context read/write helpers for optimizer ↔ resolver hand-off.
```

### `field_meta.py` uses absolute first-party imports while every other `optimizer/` module uses relative

`field_meta.py:25-30` imports its first-party dependencies via fully-qualified `from django_strawberry_framework.exceptions import OptimizerError` and `from django_strawberry_framework.utils.relations import (...)`. Every other module in the folder uses relative imports: `extension.py:43-58`, `hints.py:33`, `plans.py` (django imports only), and `walker.py:12-18` all use `from ..exceptions`, `from ..registry`, `from ..utils.*`, `from .hints`, etc. The folder's only other absolute-import site is `conf.py` at the package root.

The absolute-vs-relative inconsistency is a maintainability nit: a future renaming of the package would require updating `field_meta.py` separately from the rest of the optimizer subpackage, and a reader skimming the folder for "where does this module sit in the dependency graph" sees one site that reads differently. The runtime behaviour is identical and the package surface is unaffected — flagged Low for the next pass that touches `field_meta.py`'s imports. Recommended change: switch `field_meta.py:25-30` to `from ..exceptions import OptimizerError` and `from ..utils.relations import (RelationKind, is_many_side_relation_kind, relation_kind)` to match the folder convention. No urgency; defer until the file is otherwise touched.

```django_strawberry_framework/optimizer/field_meta.py:25:30
from django_strawberry_framework.exceptions import OptimizerError
from django_strawberry_framework.utils.relations import (
    RelationKind,
    is_many_side_relation_kind,
    relation_kind,
)
```

### `optimizer/__init__.py` re-export contract: matches `AGENTS.md` exactly

The folder's `__init__.py` re-exports two symbols — `DjangoOptimizerExtension` and `logger` — and declares them in `__all__` (`optimizer/__init__.py:21-24`). The contract matches the standing rule from `AGENTS.md:8` ("`__init__.py` re-exports DjangoType and DjangoOptimizerExtension"). The module docstring at `optimizer/__init__.py:9-13` is explicit that `OptimizationPlan` and `plan_optimizations` are intentionally not re-exported because they are internal implementation details consumed by `extension.py` and tests rather than consumer-facing API — this matches the actual import shape (every consumer of `OptimizationPlan` goes through `plans.OptimizationPlan`, and every consumer of `plan_optimizations` goes through `walker.plan_optimizations`).

`logger` is re-exported here so the `"django_strawberry_framework"` literal lives in exactly one source location at the top-level package, and the optimizer pass-through tests can do `from django_strawberry_framework.optimizer import logger`. Both `extension.py:45` and `walker.py:16` then import `from . import logger` (re-using the re-export). Side-effect check: the two imports at `optimizer/__init__.py:21-22` are pure — `from .. import logger` is a logging-handler-less `getLogger` and `from .extension import DjangoOptimizerExtension` triggers `extension.py`'s module body which itself has no side effects beyond `logger = logging.getLogger(...)` (no module-level extension instance, no registry mutation). Recorded as **What looks solid** below; no finding.

```django_strawberry_framework/optimizer/__init__.py:21:24
from .. import logger
from .extension import DjangoOptimizerExtension

__all__ = ("DjangoOptimizerExtension", "logger")
```

## What looks solid

- **No cross-file literal duplication.** Per the seven shadow overviews under `docs/shadow/django_strawberry_framework__optimizer*.overview.md`, every repeated string literal is intra-file and already documented (per-file artifacts pinned each). Cross-file dedupe is clean — no folder-level DRY consolidation is needed.
- **One-way dependency direction inside the folder.** Imports flow `_context.py ← extension.py ← (nothing)`; `hints.py ← extension.py, walker.py`; `plans.py ← extension.py, walker.py`; `field_meta.py ← (nothing in this folder; consumed by `types/`)`; `walker.py ← extension.py`. The dependency graph is a strict DAG with `_context.py`, `hints.py`, `plans.py`, and `field_meta.py` as leaves; `walker.py` depends on `hints.py` + `plans.py`; `extension.py` depends on every other module. No sibling imports from outside the documented boundary except the leaf dependencies (`registry`, `exceptions`, `utils.relations`, `utils.strings`, `utils.typing`) — all routed through the canonical surfaces. No circular import risk introduced by the cycle's fixes.
- **Brittle Django-private accesses are funnelled through single-purpose helpers.** `_lookup_path` (`plans.py:244-251`) for `Prefetch.prefetch_to`, `_consumer_prefetch_lookups` (`plans.py:254-262`) for `QuerySet._prefetch_related_lookups`, `_consumer_only_fields` (`plans.py:265-293`) for `query.deferred_loading`, `_flatten_select_related` (`plans.py:178-208`) for `query.select_related`. Every brittle Django-private surface has exactly one helper, and that helper's docstring names the surface it wraps. The walker spot-check from `worker-memory/worker-1.md`'s carry-forward confirmed: no sibling reaches around these helpers with a direct `getattr(qs, "_prefetch_related_lookups", ...)` or similar.
- **Sentinel discipline is consistent.** The two sentinel patterns in the folder are intentionally distinct: `OptimizerHint.SKIP` (public identity sentinel, dataclass instance, dispatched via `hint_is_skip`) at `hints.py:155` and `_MISSING = object()` (private module-level sentinel, dispatched via `getattr` defaults) at `_context.py:40`. The hints artifact (carry-forward from `worker-memory/worker-1.md`) explicitly calls out that collapsing them into one canonical sentinel helper would couple two unrelated abstractions — they are correctly parallel-by-design.
- **Error handling is consistent.** Every raised exception in the folder uses the two documented types from `exceptions.py`: `ConfigurationError` for consumer-misconfiguration (`hints.py:84-101`, `walker.py:475,483` — and after the M1 logic-pass landing at `walker.py:433-435`) and `OptimizerError` for shape-contract failures during construction (`field_meta.py:135`). No sibling defines a parallel hierarchy or raises stdlib exceptions for consumer-visible failures. The narrow-exception-tuple discipline (`_context.py:117` catches only `(TypeError, AttributeError)`, with a test pinning the exact tuple shape to prevent drift toward `except Exception:`) is the reference pattern for the folder.
- **`logger` discipline is correct.** The `"django_strawberry_framework"` literal lives in exactly one source location (the top-level package); `optimizer/__init__.py:21` re-exports it; `extension.py:45` and `walker.py:16` import `from . import logger`. No sibling calls `logging.getLogger(...)` directly. Four debug-log call sites total (`walker.py:68,623,693`, `extension.py:552`), each with explicit message arguments.
- **Folder comment surface tells one coherent story across files.** After the cycle's comment passes:
  - `_context.py`'s docstring narrates the read/write symmetry contract that `extension.py` and `types/resolvers.py` jointly honour.
  - `extension.py`'s `cache_info` and class docstrings now qualify the cache hit-rate as best-effort under concurrent access (the M3 docstring amendment) while flagging the cache itself as correctness-neutral; `CacheInfo`'s docstring no longer over-promises the `lru_cache` analogy.
  - `field_meta.py`'s factory docstring + the four-branch `relation_kind` delegation comments tell a coherent "Django field descriptor → cached metadata" story.
  - `hints.py`'s `__post_init__` validation prose, `walker.py:402-411`'s post-edit `_apply_hint` docstring (after M2 — four configurable shapes plus the no-op empty form), and `walker.py:104-109`'s `_resolve_field_map` polymorphic-shape paragraph together explain the hint dispatch order and the polymorphic `field_map.values()` contract.
  - `plans.py`'s `diff_plan_for_queryset` docstring now covers the new `only_fields` reconciliation rule (added in that file's logic pass), `apply()`'s docstring remains accurate, and `is_empty`'s docstring now mentions `cacheable` explicitly. The "cache-safety invariant: do not mutate in place" rule is documented in both `plans.py` and `walker.py` and is the same rule.
  - `walker.py:687-690`'s post-edit `_merge_aliased_selections` comment block was trimmed to drop the unanchored "future slice" phrasing (option 2 from L5 in that artifact).
  Comments do not contradict each other across siblings.
- **`optimizer/__init__.py` re-export contract is clean.** Two symbols exported (`DjangoOptimizerExtension`, `logger`), `__all__` declared, side-effect-free imports, docstring explicitly states why `OptimizationPlan` and `plan_optimizations` are deliberately NOT re-exported (internal-only). Matches `AGENTS.md:8` exactly.
- **Static helper coverage is complete.** Shadow overviews exist for all seven Python files in the folder (`_context.py`, `extension.py`, `field_meta.py`, `hints.py`, `plans.py`, `walker.py`, and the just-run `__init__.py`). The helper ran cleanly on `__init__.py` with two imports and no symbols, no ORM markers, no repeated literals, no TODOs — confirming the re-export contract has no hidden surface.

### Summary

The `optimizer/` folder reads as a well-decomposed subsystem: a single ContextVar-lifecycle entry point (`extension.py`), a single walker (`walker.py`) that consumes the plan dataclass + mutators from `plans.py`, a typed public-API hint surface (`hints.py`), a cached Django-descriptor snapshot dataclass (`field_meta.py`), and one underscore-prefixed shared-state module (`_context.py`) that owns the read/write contract for `info.context`. After the 0.0.6 review cycle's per-file passes, every cross-file collaboration is funnelled through documented helpers; every brittle Django-private surface has one wrapper; the cross-file literal-DRY check is clean; the import direction is a strict DAG with no cycles; the `optimizer/__init__.py` re-export contract matches `AGENTS.md` exactly. No High or Medium findings at folder scope. Four Low findings: the parallel walker collapse (defer until a third walker lands), the `RelationPlanCtx` dataclass evaluation (defer until a planner gains an 11th argument or a third file needs one), the `_context.py` underscore convention (keep as a sample of one — earned by the file's role, not retroactive), and the `field_meta.py` absolute-vs-relative import inconsistency (cosmetic, defer until the file is otherwise touched). The folder is in good shape closing the per-file phase of the 0.0.6 review.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/optimizer/field_meta.py:25-30` — converted absolute first-party imports (`from django_strawberry_framework.exceptions import OptimizerError` and `from django_strawberry_framework.utils.relations import (...)`) to relative imports (`from ..exceptions import OptimizerError` and `from ..utils.relations import (...)`) to match the folder convention used by `extension.py`, `hints.py`, and `walker.py`. Behaviour-preserving — the relative imports resolve to the same symbols.

### Tests added or updated

- None. The existing `field_meta` test surface already exercises the imports; no behavior change.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged)
- `uv run ruff check --fix .` — pass (all checks passed)

### Notes for Worker 3

- L1 (parallel AST walker collapse), L2 (`RelationPlanCtx` dataclass), and L3 (`_context.py` underscore convention) are all **deferred** per the explicit dispositions Worker 1 recorded in the Low section above (L1 "defer until a third walker is introduced anywhere in the package", L2 "defer until a planner gains an 11th argument or a third file outside `walker.py` needs to construct one of these planner calls", L3 "keep as a sample of one"). No in-cycle source change for those three.
- Behavior of `field_meta.py` is unchanged (relative imports resolve to the same symbols `OptimizerError`, `RelationKind`, `is_many_side_relation_kind`, `relation_kind`).
- No shadow file was used for the fix; the edit was a six-line import-style harmonization confirmed by inspection of the three sibling modules' relative-import style.

---

## Verification (Worker 3)

### Logic verification outcome

- High: None — accepted.
- Medium: None — accepted.
- L1 (parallel AST walker collapse): deferred per artifact — accepted. The artifact's trigger condition ("if a third walker is introduced anywhere in the package") is the right gate; introducing a visitor today would add indirection without removing meaningful surface.
- L2 (`RelationPlanCtx` dataclass): deferred per artifact — accepted. All four call sites are inside `walker.py`; the planners' positional argument lists ARE the surface. Trigger condition ("a planner gains an 11th argument or a third file outside `walker.py` needs to construct one") is recorded.
- L3 (`_context.py` underscore convention): kept as sample of one per artifact — accepted. The convention is earned by the file's actual cross-subpackage-but-never-consumer-facing role, not retroactively applied for uniformity.
- L4 (`field_meta.py` absolute → relative imports): applied — accepted. Worker 2's diff converts `from django_strawberry_framework.exceptions import OptimizerError` and `from django_strawberry_framework.utils.relations import (...)` to `from ..exceptions import OptimizerError` and `from ..utils.relations import (...)`, matching the relative-import convention used by sibling modules (`extension.py:43-58`, `walker.py:12-15`, `hints.py:33`). The folder-cycle delta on `field_meta.py` is exactly the import block; the other deltas visible in `git diff HEAD` (drop `@runtime_checkable`, delegate `relation_kind`/`is_many_side` to canonical helpers in `utils/relations.py`) were landed and verified in the prior per-file cycle for `rev-optimizer__field_meta.md` and are out of scope here. `uv run pytest tests/optimizer/test_field_meta.py -x` ran clean (16 passed in 0.63s) — collection succeeded, confirming the relative imports resolve correctly.

### DRY findings disposition

Folder-level DRY is clean post-cycle. Brittle Django-private access surface is fully funneled through single-purpose helpers in `plans.py` (`_lookup_path`, `_consumer_prefetch_lookups`, `_consumer_only_fields`, `_flatten_select_related`). No cross-file literal duplication — every repeated string literal in the shadow overviews is intra-file and already pinned by per-file artifacts. Sentinel discipline is consistent (the two-pattern split between `OptimizerHint.SKIP` and `_MISSING = object()` is correctly parallel-by-design). Error handling is consistent — only `ConfigurationError` and `OptimizerError` are raised across the folder; no sibling raises stdlib exceptions or defines a parallel hierarchy. The `logger` lives in exactly one source location at the top-level package and is re-exported via `optimizer/__init__.py:21`. Cardinality classification is funneled through `utils/relations.py:39-70` and consumed by both `walker.py` and `field_meta.py`. Accepted.

### Temp test verification

- Temp test files used: None.
- Disposition: N/A.

### Verification outcome

cycle accepted; verified

---

## Comment/docstring pass

No folder-level comment edits; per-file artifacts handled all docstring updates in their respective comment passes. The folder-pass `## What looks solid` "Folder comment surface tells one coherent story across files" bullet already documents the cross-file coherence after the per-file comment passes landed.

---

## Changelog disposition

- **Warranted?** Not warranted.
- **Reason:** The cycle's one source change is a relative-import refactor in `field_meta.py:25-30` — internal-only, no consumer-visible change, no behavior change (relative imports resolve to the same symbols). Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan's silence on a changelog edit for this folder pass, no `CHANGELOG.md` edit is appropriate.
- **What was done:** No `CHANGELOG.md` edit.
- **Validation:** `uv run ruff format .` — pass; `uv run ruff check --fix .` — pass.

---

## Iteration log

- _pending_
