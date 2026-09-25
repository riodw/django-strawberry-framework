# REVIEW plan: 0.0.15

Status: partial (utils/strings.py)
Mode: autonomous
Run: 0.0.15 2026-09-24-1
Scope: utils/strings.py

Method: `docs/review/REVIEW.md`. Fresh source review; findings from prior build, review, DRY or
hunt artifacts are not imported.

## Cycle baseline

`git status --short` at generation. Every path below is concurrent work: never edited, reverted,
tidied, or attributed to an item. Worker-0 appends the `CYCLE_BASELINE` stash object once at
start and nothing afterwards; drift goes on `Drift:` lines under the run heading.

```text
?? output/
```

CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 (`git stash create` empty; `git rev-parse HEAD`)
Untracked under django_strawberry_framework/: none

## Bench baseline

Each figure is bound by the package digest and instrument ids in its provenance
header; `CYCLE_BASELINE` is recorded beside it, and each run's workspace run id
(REVIEW.md "Workspace"). `<scratch>` is the absolute session scratchpad, `<phase>`
either `baseline` or `gate`, each its own copy. The nested-fetch row runs in that
copy's own Postgres database (REVIEW.md "Database cells").
Worker-0 fills Baseline at cycle entry, Gate and Delta at the final gate.

Gate: package digest `sha256:ffacb6907783cf474a9cb1c59e2c3aa0582979e08adcef97a54ba7ae42b08dcb` (the item's change), every instrument blob id identical to the baseline's, copy `review/bench/gate` synced after the item closed.
Baseline: package digest `sha256:df761b8225865985fd218f13f3288212bb3e0a5cf4ec546ec28f926d9b9f3130`, `_bench_common.py` blob 253a3953, `CYCLE_BASELINE` 6ac69870, copy `review/bench/baseline` synced 2026-09-25T03:32:07Z; python 3.14.2, django 6.1, strawberry-graphql 0.324.0.

| Command | Baseline | Gate | Delta |
|---|---|---|---|
| `uv run python scripts/workspace.py run review/bench/<phase> -- python scripts/bench_plan_cache.py --json <scratch>/bench/<phase>/plan_cache.json` | `review-20260925T033208-815a5f`; warm/cold us median: glossary scalar 710.8/790.5, nested 4062.6/4371.5, deep 6835.6/7457.0, products scalar 1204.9/1296.2, products nested (non-cacheable) 1840.7/1861.5; instrument `bench_plan_cache.py` blob 1d6203ad | `review-20260925T042312-b835a5`; warm/cold us median: glossary scalar 715.8/781.5, nested 4034.4/4290.3, deep 6920.8/7335.4, products scalar 1221.5/1316.0, products nested 1756.9/1856.0 | warm within spread on every row (+0.7%, -0.7%, +1.2%, +1.4%, -4.6%); no figure moves |
| `uv run python scripts/workspace.py run review/bench/<phase> -- python scripts/bench_optimizer_walk.py --json <scratch>/bench/<phase>/optimizer_walk.json` | `review-20260925T033406-a529d7`; min/median us: glossary scalar 5.25/5.50, nested 75.92/81.33, deep 145.92/154.33, products connection 4.50/4.71; instrument blob de745175 | `review-20260925T042505-43a836`; min/median us: glossary scalar 5.21/5.42, nested 76.12/82.00, deep 141.38/149.33, products connection 4.42/4.58 | medians -1.5%, +0.8%, -3.2%, -2.8%, inside run spread; plan shapes identical |
| `uv run python scripts/workspace.py run review/bench/<phase> --cell pg -- python scripts/bench_nested_fetch.py --json <scratch>/bench/<phase>/nested_fetch.json` | `review-20260925T033421-9c27d5`; pg 16.15, median ms count-free windowed 19.40 / lateral 17.51 / per-parent 68.41; totalCount 18.98 / 19.31 / 99.78; queries 2/2/101 and 2/2/201; instrument blob d7f8c39e | `review-20260925T042517-f3e320`; median ms count-free windowed 19.06 / lateral 17.52 / per-parent 66.93; totalCount 19.02 / 18.41 / 97.77; queries 2/2/101 and 2/2/201 | query counts identical; timings within spread |
| `uv run python scripts/workspace.py run review/bench/<phase> -- python scripts/importtime_report.py --rounds 5 --json <scratch>/bench/<phase>/importtime.json` | `review-20260925T033429-12e0bd`; package cumulative 177.4 ms, self 22.4 ms over 67 modules; instrument blob bfce84b9 | `review-20260925T042524-088936`; package cumulative 175.4 ms, self 22.1 ms over 67 modules | -2.0 ms cumulative, same module count; noise |

## How to work one item

`docs/review/REVIEW.md` is the method; this section only points into it.

- Roles and dispatch order: "Roles", "Cycle per file item".
- Per-axis looks-for list, instrument and record fields: "The three axes", "Severity".
- Evidence and measurement: "Ground rules", "Workspace".
- Dirty paths, item baselines, ledger rows: "Baseline and ownership".
- Artifact shapes and names: "Artifacts".
- Folder and project items: "Integration passes"; the gate: "Final gate and closeout".
- Plan drift before the first dispatch and before the gate:
  `uv run python scripts/review_plan.py reconcile --plan <this plan>`.

## utils/

- [x] utils/strings.py
    - Status: verified
    - Item baseline: 6ac698704402240b954f95072bed4639354ab831 (`git stash create` empty; HEAD); untracked under the package: none; dirty: none
    - Path class: hot - the optimizer walker calls `snake_case` once per selection on every plan build (plan-cache miss, every non-cacheable request); every other helper runs at declaration, finalize or behind an upstream memo
    - Artifacts: rev-utils__strings.md, rev-utils__strings.performance.md, rev-utils__strings.mechanics.md, rev-utils__strings.comments.md
    - Result: 12 findings implemented (1/5/6: M1 High; F1-F4, F9 Medium; L1, F5-F7, F10, F11 Low), 19 rejected with triggers (Performance 5; Mechanics 5 + 2 Comments cross-axis leads; Comments 7 + its looks-for discharges; each record's `## Rejected` / `## Cross-axis`), 1 deferred (F8 Low, `tests/utils/test_strings.py` provenance). Files: the 13 `## Owned changes` rows for this item.
    - Verification: Passed. Performance pass 1 (L1 `_plain_text` delta 0.6 ns <= 2.0 ns, parity ok; no bench figure moves); Mechanics pass 1 (M1 two package-tier nodes, prove pins exactly them, attacks async / connection / SKIP / inspect); Comments pass 2 (F1-F7, F9-F11 landed; prose-only re-pass proven by stripped-AST identity).
    - Cleanup: Removed docs/review/temp-tests/utils__strings; copies released; unrelated work preserved.

## Final gate

- [x] Final gate
    - Status: verified
    - Runs: `uv run python scripts/workspace.py gate review` (default, `FAKESHOP_SHARDED=1` and Postgres suites in a gate copy that keeps a git index, REVIEW.md "Final gate and closeout"), each w/ its own counts; every `## Pending execution` command from every artifact; the `## Bench baseline` commands at `<phase>` `gate`, delta recorded
    - Result: `gate-review-20260925T042258-72d2fd.json`, bound to `git stash create` 49456066d336cbedbedaeab24ab842d1b33752ee. default `review-20260925T041601-4e904e` exit 0, 8854 passed, 40 skipped, package coverage 100.00% (18636 statements); sharded `review-20260925T041812-70749d` exit 0, 8875 passed, 37 skipped; pg `review-20260925T042013-26eea0` exit 0, 2342 passed, 3 skipped. No `## Pending execution` commands (none recorded). Bench gate rows filled; no figure moves.
    - Inventory re-reconciled before the gate: `reconcile` exit 0.

## Out of scope this run

Not examined under `Scope: utils/strings.py`; an unticked box here is not a pending
review of this run. A later run moves an item into its scope under its own `## Run` heading.

- [ ] _boundary_ordering.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-_boundary_ordering.md, rev-_boundary_ordering.performance.md, rev-_boundary_ordering.mechanics.md, rev-_boundary_ordering.comments.md
- [ ] _cross_web_patches.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-_cross_web_patches.md, rev-_cross_web_patches.performance.md, rev-_cross_web_patches.mechanics.md, rev-_cross_web_patches.comments.md
- [ ] _django_patches.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-_django_patches.md, rev-_django_patches.performance.md, rev-_django_patches.mechanics.md, rev-_django_patches.comments.md
- [ ] _graphql_core_patches.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-_graphql_core_patches.md, rev-_graphql_core_patches.performance.md, rev-_graphql_core_patches.mechanics.md, rev-_graphql_core_patches.comments.md
- [ ] _request_body.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-_request_body.md, rev-_request_body.performance.md, rev-_request_body.mechanics.md, rev-_request_body.comments.md
- [ ] _strawberry_patches.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-_strawberry_patches.md, rev-_strawberry_patches.performance.md, rev-_strawberry_patches.mechanics.md, rev-_strawberry_patches.comments.md
- [ ] apps.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-apps.md, rev-apps.performance.md, rev-apps.mechanics.md, rev-apps.comments.md
- [ ] conf.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-conf.md, rev-conf.performance.md, rev-conf.mechanics.md, rev-conf.comments.md
- [ ] connection.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-connection.md, rev-connection.performance.md, rev-connection.mechanics.md, rev-connection.comments.md
- [ ] consumers.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-consumers.md, rev-consumers.performance.md, rev-consumers.mechanics.md, rev-consumers.comments.md
- [ ] error_policy.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-error_policy.md, rev-error_policy.performance.md, rev-error_policy.mechanics.md, rev-error_policy.comments.md
- [ ] exceptions.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-exceptions.md, rev-exceptions.performance.md, rev-exceptions.mechanics.md, rev-exceptions.comments.md
- [ ] keyset.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-keyset.md, rev-keyset.performance.md, rev-keyset.mechanics.md, rev-keyset.comments.md
- [ ] list_field.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-list_field.md, rev-list_field.performance.md, rev-list_field.mechanics.md, rev-list_field.comments.md
- [ ] permissions.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-permissions.md, rev-permissions.performance.md, rev-permissions.mechanics.md, rev-permissions.comments.md
- [ ] registry.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-registry.md, rev-registry.performance.md, rev-registry.mechanics.md, rev-registry.comments.md
- [ ] relay.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-relay.md, rev-relay.performance.md, rev-relay.mechanics.md, rev-relay.comments.md
- [ ] resource_policy.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-resource_policy.md, rev-resource_policy.performance.md, rev-resource_policy.mechanics.md, rev-resource_policy.comments.md
- [ ] routers.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-routers.md, rev-routers.performance.md, rev-routers.mechanics.md, rev-routers.comments.md
- [ ] scalars.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-scalars.md, rev-scalars.performance.md, rev-scalars.mechanics.md, rev-scalars.comments.md
- [ ] schema.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-schema.md, rev-schema.performance.md, rev-schema.mechanics.md, rev-schema.comments.md
- [ ] sets_mixins.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-sets_mixins.md, rev-sets_mixins.performance.md, rev-sets_mixins.mechanics.md, rev-sets_mixins.comments.md
- [ ] views.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-views.md, rev-views.performance.md, rev-views.mechanics.md, rev-views.comments.md
- [ ] auth/mutations.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-auth__mutations.md, rev-auth__mutations.performance.md, rev-auth__mutations.mechanics.md, rev-auth__mutations.comments.md
- [ ] auth/queries.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-auth__queries.md, rev-auth__queries.performance.md, rev-auth__queries.mechanics.md, rev-auth__queries.comments.md
- [ ] auth/sessions.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-auth__sessions.md, rev-auth__sessions.performance.md, rev-auth__sessions.mechanics.md, rev-auth__sessions.comments.md
- [ ] auth/ integration
    - Status: out-of-scope
    - Init files: `auth/__init__.py`
    - Artifacts: rev-auth.md, rev-auth.performance.md, rev-auth.mechanics.md, rev-auth.comments.md
- [ ] extensions/debug.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-extensions__debug.md, rev-extensions__debug.performance.md, rev-extensions__debug.mechanics.md, rev-extensions__debug.comments.md
- [ ] extensions/error_policy.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-extensions__error_policy.md, rev-extensions__error_policy.performance.md, rev-extensions__error_policy.mechanics.md, rev-extensions__error_policy.comments.md
- [ ] extensions/operation_state.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-extensions__operation_state.md, rev-extensions__operation_state.performance.md, rev-extensions__operation_state.mechanics.md, rev-extensions__operation_state.comments.md
- [ ] extensions/resource_policy.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-extensions__resource_policy.md, rev-extensions__resource_policy.performance.md, rev-extensions__resource_policy.mechanics.md, rev-extensions__resource_policy.comments.md
- [ ] extensions/ integration
    - Status: out-of-scope
    - Init files: `extensions/__init__.py`
    - Artifacts: rev-extensions.md, rev-extensions.performance.md, rev-extensions.mechanics.md, rev-extensions.comments.md
- [ ] filters/base.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-filters__base.md, rev-filters__base.performance.md, rev-filters__base.mechanics.md, rev-filters__base.comments.md
- [ ] filters/factories.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-filters__factories.md, rev-filters__factories.performance.md, rev-filters__factories.mechanics.md, rev-filters__factories.comments.md
- [ ] filters/inputs.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-filters__inputs.md, rev-filters__inputs.performance.md, rev-filters__inputs.mechanics.md, rev-filters__inputs.comments.md
- [ ] filters/sets.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-filters__sets.md, rev-filters__sets.performance.md, rev-filters__sets.mechanics.md, rev-filters__sets.comments.md
- [ ] filters/ integration
    - Status: out-of-scope
    - Init files: `filters/__init__.py` (defines `_clear_helper_referenced_filtersets`, `filter_input_type`)
    - Artifacts: rev-filters.md, rev-filters.performance.md, rev-filters.mechanics.md, rev-filters.comments.md
- [ ] forms/converter.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-forms__converter.md, rev-forms__converter.performance.md, rev-forms__converter.mechanics.md, rev-forms__converter.comments.md
- [ ] forms/inputs.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-forms__inputs.md, rev-forms__inputs.performance.md, rev-forms__inputs.mechanics.md, rev-forms__inputs.comments.md
- [ ] forms/resolvers.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-forms__resolvers.md, rev-forms__resolvers.performance.md, rev-forms__resolvers.mechanics.md, rev-forms__resolvers.comments.md
- [ ] forms/sets.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-forms__sets.md, rev-forms__sets.performance.md, rev-forms__sets.mechanics.md, rev-forms__sets.comments.md
- [ ] forms/ integration
    - Status: out-of-scope
    - Init files: `forms/__init__.py`
    - Artifacts: rev-forms.md, rev-forms.performance.md, rev-forms.mechanics.md, rev-forms.comments.md
- [ ] management/commands/_imports.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-management__commands___imports.md, rev-management__commands___imports.performance.md, rev-management__commands___imports.mechanics.md, rev-management__commands___imports.comments.md
- [ ] management/commands/export_schema.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-management__commands__export_schema.md, rev-management__commands__export_schema.performance.md, rev-management__commands__export_schema.mechanics.md, rev-management__commands__export_schema.comments.md
- [ ] management/commands/inspect_django_type.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-management__commands__inspect_django_type.md, rev-management__commands__inspect_django_type.performance.md, rev-management__commands__inspect_django_type.mechanics.md, rev-management__commands__inspect_django_type.comments.md
- [ ] management/commands/ integration
    - Status: out-of-scope
    - Init files: `management/commands/__init__.py`
    - Artifacts: rev-management__commands.md, rev-management__commands.performance.md, rev-management__commands.mechanics.md, rev-management__commands.comments.md
- [ ] management/ integration
    - Status: out-of-scope
    - Init files: `management/__init__.py`
    - Artifacts: rev-management.md, rev-management.performance.md, rev-management.mechanics.md, rev-management.comments.md
- [ ] middleware/debug_toolbar.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-middleware__debug_toolbar.md, rev-middleware__debug_toolbar.performance.md, rev-middleware__debug_toolbar.mechanics.md, rev-middleware__debug_toolbar.comments.md
- [ ] middleware/request_body.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-middleware__request_body.md, rev-middleware__request_body.performance.md, rev-middleware__request_body.mechanics.md, rev-middleware__request_body.comments.md
- [ ] middleware/ integration
    - Status: out-of-scope
    - Init files: `middleware/__init__.py`
    - Artifacts: rev-middleware.md, rev-middleware.performance.md, rev-middleware.mechanics.md, rev-middleware.comments.md
- [ ] mutations/fields.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-mutations__fields.md, rev-mutations__fields.performance.md, rev-mutations__fields.mechanics.md, rev-mutations__fields.comments.md
- [ ] mutations/inputs.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-mutations__inputs.md, rev-mutations__inputs.performance.md, rev-mutations__inputs.mechanics.md, rev-mutations__inputs.comments.md
- [ ] mutations/operations.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-mutations__operations.md, rev-mutations__operations.performance.md, rev-mutations__operations.mechanics.md, rev-mutations__operations.comments.md
- [ ] mutations/permissions.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-mutations__permissions.md, rev-mutations__permissions.performance.md, rev-mutations__permissions.mechanics.md, rev-mutations__permissions.comments.md
- [ ] mutations/resolvers.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-mutations__resolvers.md, rev-mutations__resolvers.performance.md, rev-mutations__resolvers.mechanics.md, rev-mutations__resolvers.comments.md
- [ ] mutations/sets.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-mutations__sets.md, rev-mutations__sets.performance.md, rev-mutations__sets.mechanics.md, rev-mutations__sets.comments.md
- [ ] mutations/ integration
    - Status: out-of-scope
    - Init files: `mutations/__init__.py`
    - Artifacts: rev-mutations.md, rev-mutations.performance.md, rev-mutations.mechanics.md, rev-mutations.comments.md
- [ ] optimizer/_context.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer___context.md, rev-optimizer___context.performance.md, rev-optimizer___context.mechanics.md, rev-optimizer___context.comments.md
- [ ] optimizer/extension.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__extension.md, rev-optimizer__extension.performance.md, rev-optimizer__extension.mechanics.md, rev-optimizer__extension.comments.md
- [ ] optimizer/field_meta.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__field_meta.md, rev-optimizer__field_meta.performance.md, rev-optimizer__field_meta.mechanics.md, rev-optimizer__field_meta.comments.md
- [ ] optimizer/hints.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__hints.md, rev-optimizer__hints.performance.md, rev-optimizer__hints.mechanics.md, rev-optimizer__hints.comments.md
- [ ] optimizer/join_taxonomy.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__join_taxonomy.md, rev-optimizer__join_taxonomy.performance.md, rev-optimizer__join_taxonomy.mechanics.md, rev-optimizer__join_taxonomy.comments.md
- [ ] optimizer/lateral_fetch.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__lateral_fetch.md, rev-optimizer__lateral_fetch.performance.md, rev-optimizer__lateral_fetch.mechanics.md, rev-optimizer__lateral_fetch.comments.md
- [ ] optimizer/nested_fetch.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__nested_fetch.md, rev-optimizer__nested_fetch.performance.md, rev-optimizer__nested_fetch.mechanics.md, rev-optimizer__nested_fetch.comments.md
- [ ] optimizer/nested_planner.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__nested_planner.md, rev-optimizer__nested_planner.performance.md, rev-optimizer__nested_planner.mechanics.md, rev-optimizer__nested_planner.comments.md
- [ ] optimizer/plans.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__plans.md, rev-optimizer__plans.performance.md, rev-optimizer__plans.mechanics.md, rev-optimizer__plans.comments.md
- [ ] optimizer/predicates.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__predicates.md, rev-optimizer__predicates.performance.md, rev-optimizer__predicates.mechanics.md, rev-optimizer__predicates.comments.md
- [ ] optimizer/selections.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__selections.md, rev-optimizer__selections.performance.md, rev-optimizer__selections.mechanics.md, rev-optimizer__selections.comments.md
- [ ] optimizer/single_parent_fetch.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__single_parent_fetch.md, rev-optimizer__single_parent_fetch.performance.md, rev-optimizer__single_parent_fetch.mechanics.md, rev-optimizer__single_parent_fetch.comments.md
- [ ] optimizer/walker.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__walker.md, rev-optimizer__walker.performance.md, rev-optimizer__walker.mechanics.md, rev-optimizer__walker.comments.md
- [ ] optimizer/ integration
    - Status: out-of-scope
    - Init files: `optimizer/__init__.py`
    - Artifacts: rev-optimizer.md, rev-optimizer.performance.md, rev-optimizer.mechanics.md, rev-optimizer.comments.md
- [ ] orders/base.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-orders__base.md, rev-orders__base.performance.md, rev-orders__base.mechanics.md, rev-orders__base.comments.md
- [ ] orders/factories.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-orders__factories.md, rev-orders__factories.performance.md, rev-orders__factories.mechanics.md, rev-orders__factories.comments.md
- [ ] orders/inputs.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-orders__inputs.md, rev-orders__inputs.performance.md, rev-orders__inputs.mechanics.md, rev-orders__inputs.comments.md
- [ ] orders/sets.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-orders__sets.md, rev-orders__sets.performance.md, rev-orders__sets.mechanics.md, rev-orders__sets.comments.md
- [ ] orders/ integration
    - Status: out-of-scope
    - Init files: `orders/__init__.py` (defines `_clear_helper_referenced_ordersets`, `order_input_type`)
    - Artifacts: rev-orders.md, rev-orders.performance.md, rev-orders.mechanics.md, rev-orders.comments.md
- [ ] rest_framework/hook_context.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-rest_framework__hook_context.md, rev-rest_framework__hook_context.performance.md, rev-rest_framework__hook_context.mechanics.md, rev-rest_framework__hook_context.comments.md
- [ ] rest_framework/inputs.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-rest_framework__inputs.md, rev-rest_framework__inputs.performance.md, rev-rest_framework__inputs.mechanics.md, rev-rest_framework__inputs.comments.md
- [ ] rest_framework/resolvers.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-rest_framework__resolvers.md, rev-rest_framework__resolvers.performance.md, rev-rest_framework__resolvers.mechanics.md, rev-rest_framework__resolvers.comments.md
- [ ] rest_framework/serializer_converter.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-rest_framework__serializer_converter.md, rev-rest_framework__serializer_converter.performance.md, rev-rest_framework__serializer_converter.mechanics.md, rev-rest_framework__serializer_converter.comments.md
- [ ] rest_framework/sets.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-rest_framework__sets.md, rev-rest_framework__sets.performance.md, rev-rest_framework__sets.mechanics.md, rev-rest_framework__sets.comments.md
- [ ] rest_framework/ integration
    - Status: out-of-scope
    - Init files: `rest_framework/__init__.py` (defines `require_drf`)
    - Artifacts: rev-rest_framework.md, rev-rest_framework.performance.md, rev-rest_framework.mechanics.md, rev-rest_framework.comments.md
- [ ] testing/_wrap.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-testing___wrap.md, rev-testing___wrap.performance.md, rev-testing___wrap.mechanics.md, rev-testing___wrap.comments.md
- [ ] testing/client.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-testing__client.md, rev-testing__client.performance.md, rev-testing__client.mechanics.md, rev-testing__client.comments.md
- [ ] testing/relay.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-testing__relay.md, rev-testing__relay.performance.md, rev-testing__relay.mechanics.md, rev-testing__relay.comments.md
- [ ] testing/ integration
    - Status: out-of-scope
    - Init files: `testing/__init__.py`
    - Artifacts: rev-testing.md, rev-testing.performance.md, rev-testing.mechanics.md, rev-testing.comments.md
- [ ] types/base.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-types__base.md, rev-types__base.performance.md, rev-types__base.mechanics.md, rev-types__base.comments.md
- [ ] types/converters.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-types__converters.md, rev-types__converters.performance.md, rev-types__converters.mechanics.md, rev-types__converters.comments.md
- [ ] types/definition.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-types__definition.md, rev-types__definition.performance.md, rev-types__definition.mechanics.md, rev-types__definition.comments.md
- [ ] types/finalizer.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-types__finalizer.md, rev-types__finalizer.performance.md, rev-types__finalizer.mechanics.md, rev-types__finalizer.comments.md
- [ ] types/relations.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-types__relations.md, rev-types__relations.performance.md, rev-types__relations.mechanics.md, rev-types__relations.comments.md
- [ ] types/relay.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-types__relay.md, rev-types__relay.performance.md, rev-types__relay.mechanics.md, rev-types__relay.comments.md
- [ ] types/resolvers.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-types__resolvers.md, rev-types__resolvers.performance.md, rev-types__resolvers.mechanics.md, rev-types__resolvers.comments.md
- [ ] types/ integration
    - Status: out-of-scope
    - Init files: `types/__init__.py`
    - Artifacts: rev-types.md, rev-types.performance.md, rev-types.mechanics.md, rev-types.comments.md
- [ ] utils/canonical.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__canonical.md, rev-utils__canonical.performance.md, rev-utils__canonical.mechanics.md, rev-utils__canonical.comments.md
- [ ] utils/connections.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__connections.md, rev-utils__connections.performance.md, rev-utils__connections.mechanics.md, rev-utils__connections.comments.md
- [ ] utils/context.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__context.md, rev-utils__context.performance.md, rev-utils__context.mechanics.md, rev-utils__context.comments.md
- [ ] utils/converters.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__converters.md, rev-utils__converters.performance.md, rev-utils__converters.mechanics.md, rev-utils__converters.comments.md
- [ ] utils/directives.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__directives.md, rev-utils__directives.performance.md, rev-utils__directives.mechanics.md, rev-utils__directives.comments.md
- [ ] utils/errors.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__errors.md, rev-utils__errors.performance.md, rev-utils__errors.mechanics.md, rev-utils__errors.comments.md
- [ ] utils/execution_mode.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__execution_mode.md, rev-utils__execution_mode.performance.md, rev-utils__execution_mode.mechanics.md, rev-utils__execution_mode.comments.md
- [ ] utils/imports.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__imports.md, rev-utils__imports.performance.md, rev-utils__imports.mechanics.md, rev-utils__imports.comments.md
- [ ] utils/input_values.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__input_values.md, rev-utils__input_values.performance.md, rev-utils__input_values.mechanics.md, rev-utils__input_values.comments.md
- [ ] utils/inputs.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__inputs.md, rev-utils__inputs.performance.md, rev-utils__inputs.mechanics.md, rev-utils__inputs.comments.md
- [ ] utils/operation_lease.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__operation_lease.md, rev-utils__operation_lease.performance.md, rev-utils__operation_lease.mechanics.md, rev-utils__operation_lease.comments.md
- [ ] utils/permissions.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__permissions.md, rev-utils__permissions.performance.md, rev-utils__permissions.mechanics.md, rev-utils__permissions.comments.md
- [ ] utils/policies.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__policies.md, rev-utils__policies.performance.md, rev-utils__policies.mechanics.md, rev-utils__policies.comments.md
- [ ] utils/private_state.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__private_state.md, rev-utils__private_state.performance.md, rev-utils__private_state.mechanics.md, rev-utils__private_state.comments.md
- [ ] utils/querysets.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__querysets.md, rev-utils__querysets.performance.md, rev-utils__querysets.mechanics.md, rev-utils__querysets.comments.md
- [ ] utils/relations.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__relations.md, rev-utils__relations.performance.md, rev-utils__relations.mechanics.md, rev-utils__relations.comments.md
- [ ] utils/sessions.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__sessions.md, rev-utils__sessions.performance.md, rev-utils__sessions.mechanics.md, rev-utils__sessions.comments.md
- [ ] utils/typing.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__typing.md, rev-utils__typing.performance.md, rev-utils__typing.mechanics.md, rev-utils__typing.comments.md
- [ ] utils/write_transaction.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__write_transaction.md, rev-utils__write_transaction.performance.md, rev-utils__write_transaction.mechanics.md, rev-utils__write_transaction.comments.md
- [ ] utils/write_values.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-utils__write_values.md, rev-utils__write_values.performance.md, rev-utils__write_values.mechanics.md, rev-utils__write_values.comments.md
- [ ] utils/ integration
    - Status: out-of-scope
    - Init files: `utils/__init__.py`
    - Artifacts: rev-utils.md, rev-utils.performance.md, rev-utils.mechanics.md, rev-utils.comments.md
- [ ] Project integration
    - Status: out-of-scope
    - Covers: package-root modules as one component; public exports; import-time cost vs `## Bench baseline`; end-to-end lifecycle across folders; the package-root `__init__.py` (each folder's `__init__.py` is on its folder item)
    - Init files: `__init__.py` (defines `__getattr__`)
    - Artifacts: rev-project.md, rev-project.performance.md, rev-project.mechanics.md, rev-project.comments.md

## Decisions

Maintainer decisions the run surfaced: ruff rules to enable, trade-offs, contracts nobody could cite.

- utils/strings.py (M1): missing fakeshop fixture, a model with a mixed-case scalar, a mixed-case forward FK and a reverse `related_name`, so `tests/optimizer/test_extension.py::test_mixed_case_model_field_selection_projects_its_real_column` and `::test_mixed_case_relation_selections_plan_through_their_django_names` can move to `examples/fakeshop/test_query/`. An item adds no example model.
- Pre-existing, blocks the gate row's CI parity only: `build_tree_md.py --check` is red at HEAD 6ac69870 because `tests/test_workspace.py` (committed in cd6a74aa) has no `docs/TREE.md` row; not this run's item. Fix = render TREE.md in its own change.
- `scripts/prove_failability.py` counts pytest captured-log `ERROR <logger>` lines as collection/setup errors (run `review-20260925T035307-0da5c6` INVALID COUNT); workaround `--show-capture=no` in the scope. Script defect outside the package, no item owns it.
- utils/strings.py (Performance verifier gap, no in-scope owner): a mixed-case or digit-boundary selection costs 7.5-8.4 us per plan build in `optimizer/walker.py::_resolve_selection_target` (reverse miss rebuilds `_graphql_names_by_python_name` and scans via `_field_by_graphql_name`) vs ~150 ns for a lowercase field (`review-20260925T040111-52f3c0`, `-040057-e51263`). Owner: a Performance pass on `optimizer/walker.py`, outside this run's scope; candidate fixes and reopen trigger in `rev-utils__strings.performance.md` `## Verification (Performance)`.
- utils/strings.py (Mechanics, rejected): generated input field names are pinned camelCase and ignore `auto_camel_case=False`; no contract source says they follow the naming config. Decide whether they should.

## Owned changes

One row per tracked edit or new file a verified item landed. A later item may build on a path
listed here; any other dirty hunk is external.

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/utils/strings.py` | utils/strings.py | Performance, Comments | `_plain_text` (branch order, docstring); module docstring; `_snake_case_cached` docstring; `snake_case` (`functools.wraps` `assigned`, docstring); `pascal_case`, `pascal_case_or_raise`, `graphql_camel_name`, `flatten_lookup_path` docstrings |
| `django_strawberry_framework/types/base.py` | utils/strings.py | Mechanics | `DjangoType.__init_subclass__` (field-map key), `_validate_relation_shape_targets`, `_build_annotations`; `snake_case` import removed |
| `django_strawberry_framework/types/finalizer.py` | utils/strings.py | Mechanics | `_synthesize_relation_connections`, `finalize_django_types`; `snake_case` import removed |
| `django_strawberry_framework/management/commands/inspect_django_type.py` | utils/strings.py | Mechanics | `Command._resolve_row`; `snake_case` import removed |
| `django_strawberry_framework/types/relations.py` | utils/strings.py | Mechanics | `PendingRelation` docstring |
| `django_strawberry_framework/optimizer/walker.py` | utils/strings.py | Mechanics | `_resolve_field_map` docstring |
| `django_strawberry_framework/types/__init__.py` | utils/strings.py | Mechanics | module docstring (dependency paragraph) |
| `django_strawberry_framework/optimizer/field_meta.py` | utils/strings.py | Comments | `FieldMeta` docstring (`name` attribute) |
| `tests/optimizer/test_extension.py` | utils/strings.py | Mechanics | `_unmanaged_tables`, `test_mixed_case_model_field_selection_projects_its_real_column`, `test_mixed_case_relation_selections_plan_through_their_django_names` (new) |
| `tests/optimizer/test_walker.py` | utils/strings.py | Mechanics | `_register_type_definition`, `test_scalar_only_secondary_resolver_uses_secondary_field_map`, `test_optimizer_walker_uses_primary_for_nested_relation_target`; `snake_case` import removed |
| `tests/optimizer/test_multi_db.py` | utils/strings.py | Mechanics, Comments | `_register_type_definition`; `snake_case` import removed; module docstring (AGENTS.md citation) |
| `tests/types/test_relay_interfaces.py` | utils/strings.py | Mechanics | `_field_map_for`; `snake_case` import removed |
| `tests/types/test_finalizer.py` | utils/strings.py | Mechanics | `test_malformed_pending_field_name_is_rejected_before_relation_lookup` docstring |

## Outcomes

Filled by Worker-0 at closeout before any scratch is removed; a scoped run adds "Scope of this run".

### utils/strings.py

- Performance: L1 Low `_plain_text` exact-`str` test first, implemented; `_plain_text` 36.7 -> 29.3 ns vs the reordered reference (delta 8.4 -> 0.6 ns, before `review-20260925T034653-e76c46`, after `review-20260925T035407-988276`, verifier reproduced 9.0 / 0.6 ns); no bench figure moves. 5 rejections w/ triggers (inline `snake_case` fast path, `lru_cache` sizing, cached char loop, cold string building, `flatten_lookup_path` loop).
- Mechanics: M1 High defect fixed at the owner. `DjangoTypeDefinition.field_map` was keyed by `snake_case(f.name)`, so a mixed-case model field (legal Django) crashed every optimized query selecting it (`FieldDoesNotExist`, masked as an internal error; unoptimized path served it). Now keyed by the raw Django name; five readers in `types/base.py`, `types/finalizer.py`, `inspect_django_type.py` stop re-applying `snake_case`; the walker alone still reverses GraphQL selection names. Permanent tests `tests/optimizer/test_extension.py::test_mixed_case_model_field_selection_projects_its_real_column` and `::test_mixed_case_relation_selections_plan_through_their_django_names` (package tier; fixture gap under `## Decisions`); `prove` pins exactly those two; verifier attacks (async, `relation_shapes` connection, `OptimizerHint.SKIP`, `inspect_django_type`) pass and three of them fail on revert. 7 rejections w/ triggers incl. two Comments cross-axis leads.
- Comments: F1-F4 Medium (stale module docstring; `snake_case` contract overclaimed and hidden behind `functools.wraps`; `graphql_camel_name` "Lowercase the head"; `pascal_case` false reasons), F5-F7 Low, all implemented pass 1; verify 1 added F9 Medium (`FieldMeta.name` "snake_case"), F10 Low ("every request" -> "every plan build"), F11 Low (stale `AGENTS.md #"..."` citation in `tests/optimizer/test_multi_db.py`), implemented pass 2 and verified; prose-only re-pass proven by stripped-AST identity. F8 Low (provenance in `tests/utils/test_strings.py`) deferred: no higher finding touches that file. 7 rejections w/ triggers.
- Out-of-item leads, owners named: `utils/__init__.py` "case conversion (``snake_case``, ``pascal_case``)" framing -> `utils/` folder item Comments; past-tense narrative in `tests/optimizer/test_walker.py` docstrings -> an `optimizer/walker.py` item; walker slow path for mixed-case / digit-boundary selections -> `## Decisions`.

### Run

- Bench baseline vs gate: every row within spread, instrument ids identical, query counts identical (table above).
- Decisions owed to Rio: four, under `## Decisions` (mixed-case fakeshop fixture; pre-existing `docs/TREE.md` drift for `tests/test_workspace.py` at HEAD, CI `build_tree_md.py --check` red independent of this run; `prove_failability.py` captured-log miscount; generated inputs vs `auto_camel_case=False`), plus the walker slow-path lead.
- Cells unverified: none. sharded and pg `inapplicable by construction` for every finding (verifiers concurred); both suites ran green in the gate.
- Blocked items: none.
- Net source change vs cycle baseline 6ac69870: package 8 files +105/-92; tests 5 files +162/-14; uncommitted.
- Gate record: `gate-review-20260925T042258-72d2fd.json`, all three suites exit 0, coverage 100%.
- Concurrent work untouched: the cycle baseline held only `output/`; no drift during the run.
- Scope of this run: `utils/strings.py` and the final gate. Every other file, folder and the project item were out of scope and not examined; their boxes stay unticked. The M1 fix edited files outside the target as its root-cause owner (13 ledger rows); those files' own items were not reviewed.
