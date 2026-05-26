# Review: `django_strawberry_framework/optimizer/extension.py`

Status: verified

## DRY analysis

- Defer until a third call site lands: extract `_resolve_origin_for_type_name(strawberry_schema, type_name) -> tuple[type, type] | None` to share the `get_type_by_name(name) -> definition -> origin -> model` resolution chain between `_collect_schema_reachable_types._walk_gql_type` (`django_strawberry_framework/optimizer/extension.py:342-358`) and `_resolve_model_from_return_type` (`django_strawberry_framework/optimizer/extension.py:412-443`). Only two call sites today; both currently re-implement the same five-step probe (`get_type_by_name` → check `None` → read `origin` → check `None` → reverse-lookup model). Defer-with-trigger: act when a third site needs the same origin+model resolution from a graphql-core type name.
- Defer until a third AST walker lands: extract `_walk_selection_tree(node, fragments, visited, *, on_node)` generic visitor that takes a per-node callback (directive sweep OR fragment-def collection), collapsing `_walk_directives` (`django_strawberry_framework/optimizer/extension.py:92-128`) and `_walk_reachable_fragment_definitions` (`django_strawberry_framework/optimizer/extension.py:199-227`). Today both walks already share `_child_selections` and `_unvisited_fragment_definition`, and the per-walk bodies are short enough that a callable indirection would obscure the divergence. Defer-with-trigger: act when a third walker (e.g. one that emits `RequiredSelection` markers or computes a fingerprint other than the directive set or fragment set) lands in any optimizer module.

## High:

None.

## Medium:

None — every Medium from the 0.0.6 cycle has been addressed in shipped code (M1 multi-type warning now names `type_cls.__name__` per the test at `tests/optimizer/test_extension.py:3219-3266`; M2 empty-plan-with-strictness invariant is now pinned by the parametrized `test_strictness_with_empty_plan_does_not_raise_or_warn` at `tests/optimizer/test_extension.py:1352-1394`; M3 cache-counter drift now disclosed in `cache_info` docstring at `django_strawberry_framework/optimizer/extension.py:503-513`).

## Low:

### `docs/GLOSSARY.md:462` "FK-id elisions are stashed on `info.context.dst_optimizer_plan`" omits the standalone `dst_optimizer_fk_id_elisions` set

`_publish_plan_to_context` stashes the elision contract on **two** independent context keys at `django_strawberry_framework/optimizer/extension.py:671-672`:

```django_strawberry_framework/optimizer/extension.py:671:672
_stash_on_context(info.context, DST_OPTIMIZER_PLAN, plan)
_stash_on_context(info.context, DST_OPTIMIZER_FK_ID_ELISIONS, set(plan.fk_id_elisions))
```

- `info.context.dst_optimizer_plan` carries the plan instance, whose `plan.fk_id_elisions` attribute is a `tuple[str, ...]` (per `django_strawberry_framework/optimizer/plans.py:68-69,118`).
- `info.context.dst_optimizer_fk_id_elisions` is a separate `set[str]` populated from the same tuple but exposed for direct lookup at resolver time (consumed by `django_strawberry_framework/types/resolvers.py:36,63`).

`docs/GLOSSARY.md:462` reads `"FK-id elisions are stashed on info.context.dst_optimizer_plan for introspection."` — technically true (the plan is stashed there and carries `fk_id_elisions`), but it never names the standalone `dst_optimizer_fk_id_elisions` set that is the actual fast-path introspection surface for resolver-time checks and is the surface the test suite explicitly pins at `tests/optimizer/test_extension.py:325-326,369-371,1430` via `ctx.dst_optimizer_fk_id_elisions == {...}`. Both surfaces are public introspection contracts; the GLOSSARY should mention both so consumers reading the spec do not assume the plan attribute is the only entry point.

Recommended change (GLOSSARY-side; no source edit needed): rewrite `docs/GLOSSARY.md:462` to something like `"FK-id elisions are stashed on info.context.dst_optimizer_plan.fk_id_elisions (tuple, as part of the plan) and info.context.dst_optimizer_fk_id_elisions (standalone set, for resolver-time membership checks)."`

Severity Low because the source code is correct, the test pins are correct, and this is doc text not consumer-facing source. Forward to `rev-django_strawberry_framework.md` (project pass) since the fix is to `docs/GLOSSARY.md`, not to `django_strawberry_framework/optimizer/extension.py`, and the project pass is the canonical site for cross-package doc-vs-code drift findings.

### `_root_child_selections` accepts `list[Any]` but only reads `.selections` on each entry; a stricter type hint would surface the implicit `SelectedField` shape

`django_strawberry_framework/optimizer/extension.py:254-272` declares `_root_child_selections(selections: list[Any]) -> list[Any]` and unconditionally calls `selection.selections` on every entry. The actual input is `list[strawberry.types.nodes.SelectedField]` (returned by `convert_selections` at the single call site, `extension.py:605-606`), so the lazy `Any` typing hides the `SelectedField`-shape assumption that drives every other call in the helper. The function is private (underscore prefix) and the call site is one-shot, so the existing shape works; the cost is that future refactors do not have a typed contract to lean on when reasoning about what `_root_child_selections` accepts.

Defer-with-trigger: act when a second caller of `_root_child_selections` lands or when `strawberry.types.nodes.SelectedField` becomes a public Strawberry typing export. Until then the helper's docstring already encodes the contract (`extension.py:255-268`).

```django_strawberry_framework/optimizer/extension.py:254:272
def _root_child_selections(selections: list[Any]) -> list[Any]:
    """Flatten children from every converted root field node.
    ...
    """
    children: list[Any] = []
    for selection in selections:
        children.extend(selection.selections)
    return children
```

### `_walk_gql_type`'s interface-implementation descent uses `hasattr(gql_schema, "get_implementations")` as a version guard but never logs the fallback

`django_strawberry_framework/optimizer/extension.py:378-386` carries a graphql-core-version-portability guard:

```django_strawberry_framework/optimizer/extension.py:378:386
if isinstance(gql_type, GraphQLInterfaceType) and hasattr(
    gql_schema,
    "get_implementations",
):
    impls = gql_schema.get_implementations(gql_type)
    impl_objects = getattr(impls, "objects", None)
    if impl_objects is not None:
        for impl_type in impl_objects:
            _walk_gql_type(impl_type)
```

If a future graphql-core release renames or removes `get_implementations`, the audit silently degrades to "interface-only descent" — interface implementations would not participate in the schema audit, and `check_schema` would silently miss missing-target warnings under that future graphql-core. The `hasattr` guard is correct (graphql-core 3.x stability is not guaranteed across majors), but the silent-fallback path has no observability and no test pin.

Two trigger-gated options:

1. Add a debug-level log when the `hasattr` guard returns `False` so operators can spot the degraded-audit state under a new graphql-core: `logger.debug("Optimizer schema audit: graphql-core %s lacks get_implementations; interface descent skipped.", ...)`.
2. Or: pin the version contract with a unit test that asserts the audit's interface descent works against the currently-pinned graphql-core, so any future bump that loses `get_implementations` fails the test instead of silently degrading.

Defer-with-trigger: act when the project upgrades to graphql-core 4.x (or any major) and the changelog mentions interface-API churn. Today the `tests/optimizer/test_extension.py:1979-2029` test pins the happy path, but does not pin the fallback observability.

Severity Low because the failure mode is "silently-missing audit warning" — the optimizer itself still runs correctly, the silent-skip is bounded to `check_schema`, and graphql-core 3.x has been stable on this API for years.

## What looks solid

### DRY recap

- **Existing patterns reused.** This file is a strong DRY citizen across the optimizer subpackage:
  - Context stash dispatched through `_context.stash_on_context` at `django_strawberry_framework/optimizer/_context.py:90-141`, imported as `_stash_on_context` (`django_strawberry_framework/optimizer/extension.py:54-56`); the underscore-prefixed name is re-exported on `__all__` at `extension.py:68` per the per-test backward-compat contract documented at `extension.py:63-67`.
  - Five sentinel keys (`DST_OPTIMIZER_PLAN`, `DST_OPTIMIZER_FK_ID_ELISIONS`, `DST_OPTIMIZER_PLANNED`, `DST_OPTIMIZER_LOOKUP_PATHS`, `DST_OPTIMIZER_STRICTNESS`) imported from `_context.py:34-38` rather than re-declared.
  - Plan construction delegated to `walker.plan_optimizations` (`django_strawberry_framework/optimizer/walker.py:28-58`) at `extension.py:647`; per-relation strategy delegated to module-level `walker.plan_relation` with the `DjangoOptimizerExtension.plan_relation` instance method at `extension.py:791-808` declared as the override seam for subclasses.
  - Plan reconciliation routed through `plans.diff_plan_for_queryset` (`django_strawberry_framework/optimizer/plans.py:330-410`) at `extension.py:618`; lookup-path extraction via `plans.lookup_paths` (`plans.py:472-476`) at `extension.py:679`; runtime path tuple via `plans.runtime_path_from_info` (`plans.py:152-162`) at `extension.py:789`.
  - Skip-hint check via `hints.hint_is_skip` (`django_strawberry_framework/optimizer/hints.py:129`) at `extension.py:719` — no open-coded `OptimizerHint.SKIP` identity check.
  - Registry interactions through the documented public surface (`registry.model_for_type`, `registry.get`, `registry.get_definition`, `registry.iter_types`) at `extension.py:357,440,707,710,721`.
  - `unwrap_graphql_type` from `utils/typing.py` reused at `extension.py:344,427` rather than re-implementing the `GraphQLNonNull`/`GraphQLList` peel.
  - The two AST walkers (`_walk_directives` at `extension.py:92-128` and `_walk_reachable_fragment_definitions` at `extension.py:199-227`) share `_child_selections` (`extension.py:131-145`) and `_unvisited_fragment_definition` (`extension.py:148-175`), which is the right factoring for the visited-fragments cycle guard.
  - The `_strawberry_schema_from_schema` / `_strawberry_schema_from_info` pair at `extension.py:301-318` centralises the brittle Strawberry-private `_strawberry_schema` attribute contract — the only repeated string literal in the file (per shadow Quick scan: `2x _strawberry_schema`), correctly factored into a deliberate two-entry-point shape.
- **New helpers considered.** Both DRY-analysis bullets above are explicitly deferred with trigger conditions; no act-now helper extraction is justified at the current two-call-site shape.
- **Duplication risk in the current file.** The two parallel AST walkers (`_walk_directives`, `_walk_reachable_fragment_definitions`) are the only structural near-copy and are already factored down through `_child_selections`/`_unvisited_fragment_definition`. The two `_strawberry_schema_*` helpers are deliberately parallel (object-input vs `info`-input) and correctly extracted into one pair. No bare `"dst_optimizer_*"` string literals — every sentinel key reaches through the imported constant.

### Other positives

- **Carry-forward delta vs `0.0.6`.** This file changed substantially between the prior cycle's review (Worker 3 verified the cycle at `f83bb71`) and the current snapshot: M1 added the type-name disambiguation in the audit warning template (`extension.py:705-729`) plus the secondary-only audit walk that surfaces missing-target warnings even when the relation is only present on a secondary type; M2 added the empty-plan-with-strictness behavioral pin (`tests/optimizer/test_extension.py:1352-1394`); M3 expanded the `cache_info` docstring to disclose counter drift (`extension.py:503-513`); L1 flipped `check_schema` from `@classmethod` to `@staticmethod` (`extension.py:682-683`); L2 trimmed the `CacheInfo` docstring to drop the `functools.lru_cache` analogy (`extension.py:275-280`); L4 added interface-implementation descent in `_walk_gql_type` (`extension.py:371-386`) plus a behavioral pin (`tests/optimizer/test_extension.py:1979-2029`); L5 added the explicit `Manager` coercion at `extension.py:582-583` plus a query-count pin at `tests/optimizer/test_extension.py:121-167`. Every prior-cycle finding has a corresponding test and corresponding source-code change.
- **Root-gating correctness.** `resolve` (`extension.py:531-561`) checks `info.path.prev is not None` BEFORE checking awaitability. Non-root resolvers short-circuit without coroutine-handling overhead; root resolvers go through the sync/async branching at `extension.py:555-561`. The shape matches strawberry-django's pattern; the test at `tests/optimizer/test_extension.py:635-658` pins the non-root passthrough.
- **`on_execute` ContextVar lifecycle.** The pair-set at `extension.py:523-524` and the pair-reset at `extension.py:528-529` use `try/finally`, so even if `yield` raises, both `_optimizer_active` and `_printed_ast_cache` reset to their prior values. The per-execution AST cache (`_printed_ast_cache`) installed at `extension.py:524` is dict-typed and bounded to the current execution; the test at `tests/optimizer/test_extension.py:774-783` pins the active-flag lifecycle.
- **`_build_cache_key` shape.** The five-component cache key `(doc_key, relevant_vars, target_model, runtime_path, origin)` at `extension.py:789` is documented in detail at `extension.py:738-761`. Each component is necessary:
  - `doc_key` covers operation body shape AND reachable fragment bodies (`_print_operation_with_reachable_fragments` at `extension.py:230-251`); two operations with identical bodies but different fragment bodies no longer share a cached plan (pinned by `tests/optimizer/test_extension.py:861-905`).
  - `relevant_vars` filters to only `@skip`/`@include` directive variables so filter args do not split the cache (pinned by `tests/optimizer/test_extension.py:1032-1062`).
  - `target_model` separates root fields returning different models in the same operation.
  - `runtime_path` separates root fields returning the same model (pinned by `tests/optimizer/test_extension.py:908-996`).
  - `origin` separates primary vs secondary return types for the same model (pinned by `tests/optimizer/test_extension.py:3081-3127`).
- **Multi-operation document safety.** Storing the printed AST string (not its hash) at `extension.py:773-779` eliminates the 64-bit hash-collision risk between two distinct document shapes; pinned by `tests/optimizer/test_extension.py:973-996,1066-1099`.
- **Plan-cache request-scope-uncacheability.** The walker marks `plan.cacheable = False` whenever a request-dependent `Prefetch` is generated (e.g. nested `get_queryset`-downgraded relations); the extension respects this at `extension.py:648-658` so dynamic plans bypass the cache entirely. The pin at `tests/optimizer/test_extension.py:1768-1808` confirms a request-dependent nested prefetch is rebuilt every request and never inflates the cache.
- **Plan-cache FIFO eviction.** The "drop oldest quarter at once" policy at `extension.py:648-656` amortises eviction across ~64 subsequent inserts; the no-LRU-promotion choice (documented at `extension.py:651-653`) means hot plans age out naturally. The pin at `tests/optimizer/test_extension.py:1000-1028` confirms FIFO order under a forced eviction.
- **B6 schema audit's H3 multi-type dedupe.** The `(model, field_name)` dedupe at `extension.py:705-722` correctly collapses two-warning-per-multi-type-model artifacts while still naming the source type in the warning string (pinned by `tests/optimizer/test_extension.py:3219-3266`). Secondary-only audit walk works because every reachable type is iterated, not just primaries (pinned by `tests/optimizer/test_extension.py:3129-3171`).
- **B8 cooperation with `get_queryset` downgrade.** `_optimize` (`extension.py:563-619`) goes through `diff_plan_for_queryset` BEFORE applying the plan, so when the walker has downgraded a forward FK to a `Prefetch`-with-queryset for a target with custom `get_queryset`, the diff still strips the consumer's matching plain-string entry rather than colliding. Pinned by the test cluster at `tests/optimizer/test_extension.py:2802-3033`.
- **`_publish_plan_to_context` write order.** The stash sequence (plan first at `extension.py:671`, then FK-id elision set at `:672`, then strictness sentinels at `:673-680`) is consistent with the resolver-side read order in `types/resolvers.py:63-...` — the resolver reads `dst_optimizer_fk_id_elisions` first for the fast-path elision check, then falls back to the planned-set membership check.
- **Static helper coverage.** All seven control-flow hotspots flagged by the shadow Quick scan have direct test coverage in `tests/optimizer/test_extension.py`:
  - `_walk_directives` — `test_walk_directives_*` cluster at lines 1153-1203.
  - `_collect_schema_reachable_types` — `test_check_schema_descends_*` cluster at lines 1934-2029.
  - `_walk_gql_type` (nested) — same cluster (union + interface descent both covered).
  - `_optimize` — every effective branch covered by the O3/O4/O5/B2/B4/B8 test clusters.
  - `_get_or_build_plan` — `test_cache_*` cluster at lines 791-1099.
  - `check_schema` — `test_check_schema_*` cluster at lines 1877-2108 + `tests/optimizer/test_extension.py:3129-3266`.
  - `_build_cache_key` — `test_cache_key_*` and `test_build_cache_key_*` tests at lines 949-1118.

### Summary

`extension.py` reads as a mature subsystem entry point: every prior-cycle Medium and Low has a corresponding source change with a corresponding behavioral test pin, and the carry-forward from `rev-optimizer___context.md` (GLOSSARY drift on the FK-id elision introspection contract at `docs/GLOSSARY.md:462`) lands cleanly as a single Low forwarded to the project-pass artifact (`rev-django_strawberry_framework.md`) because the fix surface is the GLOSSARY text, not the file under review. The two trigger-gated DRY opportunities (`_resolve_origin_for_type_name` consolidation and the generic AST visitor) are both deferred-with-trigger and both have explicit second-call-site / third-walker preconditions stated verbatim. No High, no Medium, three Lows (one forward-looking GLOSSARY drift, two trigger-gated polish items). The five-component cache key, the per-execution AST memo, the FIFO eviction policy, the multi-type audit dedupe, the interface-implementation descent, the Manager-coercion contract, the B8 diff-before-apply ordering, and the per-execution ContextVar lifecycle all hold up under deeper inspection and all have corresponding test pins in `tests/optimizer/test_extension.py`.

---

## Fix report (Worker 2)

Consolidated single-spawn no-op pass. Artifact carries 0 High / 0 Medium / 3 Lows; every Low is either forwarded to a different artifact or explicitly trigger-gated per Worker 1's prose, so no in-cycle source edit is warranted.

### Files touched

- None. Zero source edits, zero test edits, zero docs edits in this cycle. L1 fix surface is `docs/GLOSSARY.md:462`, which Worker 1 explicitly forwarded to `rev-django_strawberry_framework.md` (project pass); editing it here would jump the project-pass boundary.

### Tests added or updated

- None. No behavioural change, no contract change, no new branch — nothing to pin.

### Per-finding dispositions (logic pass)

- Low 1 (`docs/GLOSSARY.md:462` omits the standalone `dst_optimizer_fk_id_elisions` set): forwarded to `rev-django_strawberry_framework.md` per Worker 1's explicit instruction (`"Forward to rev-django_strawberry_framework.md (project pass) since the fix is to docs/GLOSSARY.md, not to django_strawberry_framework/optimizer/extension.py"`). No edit in this cycle.
- Low 2 (`_root_child_selections` `list[Any]` typing): forward-looking defer. Worker 1's verbatim trigger: `"Defer-with-trigger: act when a second caller of _root_child_selections lands or when strawberry.types.nodes.SelectedField becomes a public Strawberry typing export."` Single call site at `extension.py:605-606`; the helper docstring already encodes the contract at `extension.py:255-268`. No edit.
- Low 3 (`_walk_gql_type` `hasattr(gql_schema, "get_implementations")` silent fallback): forward-looking defer. Worker 1's verbatim trigger: `"Defer-with-trigger: act when the project upgrades to graphql-core 4.x (or any major) and the changelog mentions interface-API churn."` Today's happy path is pinned at `tests/optimizer/test_extension.py:1979-2029`; the silent-skip is bounded to `check_schema`'s audit warnings and graphql-core 3.x has been stable on this API for years. No edit.

### Validation run

- `uv run ruff format .` — pass, 118 files left unchanged (no source edits this cycle).
- `uv run ruff check --fix .` — pass, all checks passed.
- No pytest run per `START.md` standing rule (no source edit, no new test).

### Notes for Worker 3

- No shadow file was consulted during this consolidated spawn (zero source edits to plan against); Worker 1's artifact already cites `docs/shadow/optimizer__extension.overview.md` as the basis for the static-helper coverage section at lines 116-123. Worker 3 may re-use that overview when verifying the no-op stance.
- No false-premise rejections this cycle; all three Lows are explicit Worker 1 defers/forwards, not contested findings. Citations:
  - L1 forward instruction lives at `rev-optimizer__extension.md:36`.
  - L2 trigger lives at `rev-optimizer__extension.md:42`.
  - L3 trigger lives at `rev-optimizer__extension.md:78`.
- Deferred-finding trigger conditions verbatim for future cycle grep-discoverability:
  - L1: when the project pass runs against `docs/GLOSSARY.md` (next cycle target `rev-django_strawberry_framework.md`).
  - L2: when a second caller of `_root_child_selections` lands OR when `strawberry.types.nodes.SelectedField` becomes a public Strawberry typing export.
  - L3: when the project upgrades to graphql-core 4.x (or any major) AND the changelog mentions interface-API churn.

---

## Comment/docstring pass

Per consolidated-single-spawn criterion `"All Lows are explicitly forward-looking per Worker 1's own prose"` from `docs/review/worker-2.md:163`, this cycle qualifies for the collapsed three-sub-pass shape. The logic-pass sub-pass made zero edits, so there is no post-fix contract to redescribe and no stale comment to refresh.

### Files touched

- None.

### Per-finding dispositions

- Low 1: no docstring touch — fix surface is `docs/GLOSSARY.md`, forwarded to the project pass.
- Low 2: no docstring touch — `_root_child_selections` docstring at `extension.py:255-268` already encodes the `SelectedField`-shape contract per Worker 1's own acknowledgement (`"the helper's docstring already encodes the contract"`).
- Low 3: no docstring touch — Worker 1 offered two trigger-gated remediation options (debug log OR version-pin test); both are act-on-trigger, neither is a docstring update for current shape.

### Validation run

- `uv run ruff format .` — pass, 118 files left unchanged.
- `uv run ruff check --fix .` — pass, all checks passed.

### Notes for Worker 3

- No comment/docstring edits this cycle. The five-component cache-key block at `extension.py:738-761`, the `cache_info` docstring at `extension.py:503-513`, and the `_root_child_selections` docstring at `extension.py:255-268` all describe shipped behaviour accurately per Worker 1's What-looks-solid analysis; none warranted polish given the zero-logic-edit posture.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Three-leg argument plus the established 0.0.7 precedent chain for no-source-edit consolidated spawns:

1. `AGENTS.md` line 21: `"Do not update CHANGELOG.md unless explicitly instructed"`.
2. `docs/review/review-0_0_7.md` is silent on changelog authorisation for this cycle, and the dispatch prompt explicitly authorises a `Not warranted` disposition (`"Changelog (Not warranted) in one spawn"`).
3. Precedent chain: this is the twelfth 0.0.7 review cycle (`_django_patches`, `apps`, `conf`, `exceptions`, `list_field`, `registry`, `scalars`, `management__commands__export_schema`, `management__commands`, `management`, `optimizer___context`, now `optimizer__extension`); every prior cycle closed `Not warranted`, including each of the four prior no-source-edit consolidated spawns (`exceptions` skip artifact, the two folder passes `rev-management__commands.md` + `rev-management.md`, and `rev-optimizer___context.md`). On a zero-edit cycle, chain-length itself signals the established 0.0.7 default per the `rev-optimizer___context.md` Worker 2 memory entry (`"on a no-source-edit consolidated spawn the Changelog disposition leans on the precedent chain's depth as the dominant argument"`).

### What was done

No `CHANGELOG.md` edit. Zero source edits, zero test edits, zero docs edits — there is no consumer-visible delta to record for the 0.0.7 release. L1's downstream GLOSSARY edit (when the project pass executes it) will itself be doc-text-only and will not warrant a CHANGELOG entry under the same three-leg argument unless the project pass cycle is explicitly authorised to amend `CHANGELOG.md`.

### Validation run

- `uv run ruff format .` — pass, 118 files left unchanged.
- `uv run ruff check --fix .` — pass, all checks passed.

---

## Verification (Worker 3)

### Logic verification outcome

Zero-edit consolidated single-spawn no-op verified. All three Lows are explicit Worker 1-authored defers/forwards (not contested findings):

- **L1** (`docs/GLOSSARY.md:462` omits `dst_optimizer_fk_id_elisions`): forwarded to `rev-django_strawberry_framework.md` (project pass) per Worker 1's verbatim instruction at `rev-optimizer__extension.md:36` (`"Forward to rev-django_strawberry_framework.md (project pass) since the fix is to docs/GLOSSARY.md, not to django_strawberry_framework/optimizer/extension.py, and the project pass is the canonical site for cross-package doc-vs-code drift findings"`). Worker 2's `### Notes for Worker 3` block (artifact line 163) preserves the forward target for future grep-discoverability. The fix surface is `docs/GLOSSARY.md`, not the file under review, so no in-cycle edit is correct.
- **L2** (`_root_child_selections` `list[Any]` typing): forward-looking defer with verbatim two-alternative trigger preserved at artifact line 42 (`"Defer-with-trigger: act when a second caller of _root_child_selections lands or when strawberry.types.nodes.SelectedField becomes a public Strawberry typing export"`). Both arms of the disjunctive trigger appear in Worker 2's restatement at artifact line 146 and in `### Notes for Worker 3` at line 164. Re-read of `extension.py:254-272` confirms the single call site at `extension.py:605-606` and the docstring at `extension.py:255-268` that Worker 1's "the helper's docstring already encodes the contract" claim depends on. No edit warranted.
- **L3** (`_walk_gql_type` `hasattr(gql_schema, "get_implementations")` silent fallback): forward-looking defer with verbatim trigger preserved at artifact line 78 (`"Defer-with-trigger: act when the project upgrades to graphql-core 4.x (or any major) and the changelog mentions interface-API churn"`). Restated verbatim in Worker 2's per-finding disposition at line 147 and in `### Notes for Worker 3` at line 165. Happy path pinned at `tests/optimizer/test_extension.py:1979-2029` (cited in artifact); silent-skip bounded to `check_schema` audit warnings; graphql-core 3.x stability on `get_implementations` is the load-bearing precondition. No edit warranted.

### DRY findings disposition

Two DRY items present, both Worker 1-authored deferrals with explicit trigger conditions preserved verbatim:

- **DRY 1** (`_resolve_origin_for_type_name` consolidation between `_walk_gql_type` and `_resolve_model_from_return_type`): defer until a third call site lands. Two call sites today (`extension.py:342-358`, `extension.py:412-443`); the five-step probe re-implementation is shallow enough that helper extraction at two sites is premature.
- **DRY 2** (`_walk_selection_tree` generic visitor): defer until a third AST walker lands. Two walkers today (`_walk_directives` at `extension.py:92-128`, `_walk_reachable_fragment_definitions` at `extension.py:199-227`) already share `_child_selections` and `_unvisited_fragment_definition`; a callable indirection at the two-walker shape would obscure the divergence.

Both deferrals are appropriate at current scale; no new helpers warranted.

### Temp test verification

- No temp tests created this cycle (zero-edit consolidated no-op; nothing to pin).

### Changelog verification

`git diff -- CHANGELOG.md` is empty, matching `Not warranted` framing. The disposition cites three legs (AGENTS.md line 21, `review-0_0_7.md` silence, twelve-cycle precedent chain) — the two-citation bar is comfortably cleared and the chain-length leg is now the dominant signal at zero-edit consolidated-spawn scale per the `rev-optimizer___context.md` precedent. The "internal-only" framing matches the cycle's actual zero-edit scope: no public-API surface change, no new test, no docstring drift.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box in `docs/review/review-0_0_7.md:107`.
