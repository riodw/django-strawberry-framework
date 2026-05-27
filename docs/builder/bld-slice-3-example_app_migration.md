# Build: Slice 3 — Example-app migration

Spec reference: `docs/spec-020-scalar_map_helper-0_0_7.md` (lines 49–51 for slice sub-checks; lines 402–417 for Decision 9; DoD items 7 and 8 at lines 646–647)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - `examples/fakeshop/config/schema.py #"strawberry.Schema(query=Query"` (current lines 26–29) is the file's sole `strawberry.Schema(...)` construction site. The migration widens the existing call in place; no new helper, no new module, no new symbol introduced.
  - `examples/fakeshop/config/schema.py #"from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types"` (current line 16) is the file's existing one-line import block from `django_strawberry_framework`. The migration widens this single line to add `strawberry_config`; no new import statement is added.
  - The `strawberry_config` symbol itself ships from `django_strawberry_framework/scalars.py` (final-accepted in Slice 1) and is re-exported from `django_strawberry_framework/__init__.py` (final-accepted in Slice 1); the per-call factory shape is exercised by 15 new tests in `tests/test_scalars.py` and the 10 migrated converter-table sites in `tests/types/test_converters.py` (final-accepted in Slice 2). Slice 3 reuses the symbol verbatim — no public-surface change.
- **New helpers justified.**
  - None. The slice is a two-edit migration (one import widen, one constructor-call widen) on a single file. No helper or shared utility is introduced or warranted; the file is the sole project-level schema-construction site and there is no parallel call site to consolidate against.
- **Duplication risk avoided.**
  - The naive implementation could touch the per-app schemas at `examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/apps/products/schema.py` (the "audit-only" targets) under the assumption that they also need migration. Decision 9 (spec lines 402–417) and DoD item 8 (spec line 647) explicitly forbid this — both per-app files declare only `@strawberry.type class Query` with `@strawberry.field` resolvers and do NOT construct `strawberry.Schema(...)`. Verified pre-plan: `grep -rn "strawberry.Schema(" examples/fakeshop/` returns exactly three sites — `config/schema.py:26` (the slice's target), `test_query/test_multi_db.py:142` (a test-local schema construction outside Slice 3 scope), and `test_query/README.md:13` (a docs reference, not source). The per-app schemas contain only `@strawberry.field` / `@strawberry.type` decorator usage (verified via `grep -n "strawberry\." examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/apps/products/schema.py`); neither carries a `strawberry.Schema(` call.
  - The naive implementation could change the import statement style — e.g., split the existing single-line `from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types` into two lines, or reorder symbols by something other than alphabetical. Slice 3 preserves the existing single-line shape and adds `strawberry_config` alphabetically (after `finalize_django_types`) so ruff format's import sorter does not rewrap the block. Worker 2's discretion on the exact in-line ordering — see `### Implementation discretion items` below.
  - The naive implementation could touch the `examples/fakeshop/test_query/test_multi_db.py` test-local `strawberry.Schema(...)` site at line 142 because it constructs a schema. That site is **out of scope** for Slice 3 — Decision 9 names exactly one site (`examples/fakeshop/config/schema.py`). The test-local schema in `test_multi_db.py` is a per-test fixture, not the project schema. Worker 2 does not edit it.
  - The naive implementation could update `examples/fakeshop/test_query/README.md` line 13 (which describes the project schema's construction shape in prose). Slice 3 does NOT modify that file — Slice 4 owns all docs updates (per the spec's slice boundary at lines 52–58); the `test_query/README.md` mention is not in Slice 4's scope either (only `docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, `TODAY.md`, and the terms CSV are named). The `test_query/README.md` line will remain unchanged through the build; if it drifts post-cut, that is a future-card concern.
- **Static inspection helper.** Skipped at planning time. Per `docs/builder/BUILD.md` "When to run the helper during build", Worker 1 must run the helper when the plan adds logic to any existing `.py` file with at least 150 source lines OR any file under `django_strawberry_framework/optimizer/` or `django_strawberry_framework/types/`. For Slice 3:
  - `examples/fakeshop/config/schema.py` is 29 source lines (verified via `wc -l`), well below the 150-line threshold; it is not under `optimizer/` or `types/`. Skip reason: file is 29 source lines, below the 150-line threshold; not under `optimizer/` or `types/`.
  - The two audit-only files (`examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/apps/products/schema.py`) are NOT modified by the slice, so the "adds logic to" trigger does not fire. Skip reason: audit-only; no logic added.
  - Worker 3 may run the helper at review time per its own threshold rules; Worker 1's planning-pass skip does not bind Worker 3.

### Implementation steps

Line numbers are pin-at-write-time navigational hints against the current source. Verify against the file before editing — another worker's pass may have shifted the file since this plan was written.

1. **`examples/fakeshop/config/schema.py` — widen the import line.**
   - At `examples/fakeshop/config/schema.py #"from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types"` (current line 16), widen the existing one-line `from django_strawberry_framework import ...` to add `strawberry_config`. The post-edit shape, in alphabetical order to match the file's existing convention (`DjangoOptimizerExtension`, `finalize_django_types` are already sorted by Python's ASCII case-sensitive default — uppercase then lowercase), is:
     ```python
     from django_strawberry_framework import (
         DjangoOptimizerExtension,
         finalize_django_types,
         strawberry_config,
     )
     ```
   - The line will exceed 110 characters if kept as a single line (`from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types, strawberry_config` = 105 characters — under the 110-char limit, but tight). Worker 2 has discretion to keep the import on one line OR split across multiple lines per the project's existing import-block convention — see `### Implementation discretion items` item 2 below.
   - ASCII-sort note: `D` = 68, `f` = 102, `s` = 115; the post-edit ordering `DjangoOptimizerExtension`, `finalize_django_types`, `strawberry_config` is alphabetical under Python's default `sorted()` and matches the `__all__` ordering pinned at `django_strawberry_framework/__init__.py` (verified by Slice 1's final tuple at spec line 448, where `"strawberry_config"` sorts last in the lowercase block).

2. **`examples/fakeshop/config/schema.py` — widen the `strawberry.Schema(...)` constructor call.**
   - At `examples/fakeshop/config/schema.py #"strawberry.Schema(query=Query"` (current lines 26–29), rewrite the constructor call to add `config=strawberry_config()` between the `query=Query,` argument and the `extensions=[DjangoOptimizerExtension()],` argument. The current shape is:
     ```python
     schema = strawberry.Schema(
         query=Query,
         extensions=[DjangoOptimizerExtension()],
     )
     ```
   - The post-edit shape, per spec line 50 and DoD item 7 (spec line 646):
     ```python
     schema = strawberry.Schema(
         query=Query,
         config=strawberry_config(),
         extensions=[DjangoOptimizerExtension()],
     )
     ```
   - The kwarg order (`query=`, then `config=`, then `extensions=`) is pinned by the spec's pinned shape at spec line 50 and the showcase pattern at spec lines 143–149. The order is also consistent with the upstream `strawberry.Schema(...)` constructor signature where `config` is documented as a keyword argument independent of `extensions`. Worker 2 follows the spec-pinned argument order verbatim.
   - Trailing comma on `config=strawberry_config(),` preserved per `AGENTS.md` line 17 (COM812 — trailing comma on multi-arg calls expands the layout and locks it in).

3. **Audit-only verification: per-app schemas remain untouched.**
   - Worker 2 confirms (via `git status --short` after the two edits above) that `examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/apps/products/schema.py` do NOT appear in the modified-files list. Per DoD item 8 (spec line 647), both files are NOT modified — they declare only `@strawberry.type class Query` with `@strawberry.field` resolvers and contain no `strawberry.Schema(...)` construction.
   - If either file appears as `M` in `git status --short` after Step 2, Worker 2 reverts (`git checkout -- examples/fakeshop/apps/library/schema.py` or the products variant) before setting `Status: built`. The diff for Slice 3 should contain edits to exactly one source file: `examples/fakeshop/config/schema.py`.

4. **Formatting sweep.** After the edits, Worker 2 runs `uv run ruff format .` and `uv run ruff check --fix .` per `AGENTS.md` line 15 / `START.md` line 26. The 110-line line length applies; ruff format may rewrap the import line into a multi-line form if Worker 2 chooses to keep it on one line and it exceeds 110 characters (see discretion item 2 below). Whatever shape ruff format settles on is acceptable; the contract is the symbol set and the constructor-call shape, not the source layout.

### Test additions / updates

**Slice 3 ships zero new tests.** Per spec Decision 7 (spec lines 363–381) and Decision 9 (spec lines 402–417), the migration is exercised transitively:

- Every `examples/fakeshop/test_query/test_*.py` test that imports the project schema (via the standard `django.test.Client` posts to `/graphql/`) executes `examples/fakeshop/config/schema.py` at import time. Post-Slice-3, that import calls `strawberry_config()` and constructs the `StrawberryConfig` carrying the `_PACKAGE_SCALAR_MAP` (which currently contains only `BigInt`). A registration-path regression in `strawberry_config()` would cause the project schema to fail to construct, and every live HTTP test would fail to set up its `django.test.Client` GraphQL endpoint. Transitive coverage per Decision 7's "matching `docs/SPECS/spec-019-multi_db-0_0_7.md` Decision 6's transitive-coverage posture" rule (spec line 373).
- The two in-process integration tests Slice 2 added in `tests/test_scalars.py` (`test_bigint_serializes_int_via_strawberry_config_schema`, `test_bigint_parses_decimal_string_via_strawberry_config_schema`) pin the schema-execution round trip through `strawberry_config()` at the `tests/` tier. Slice 3 does not duplicate them at the `examples/fakeshop/test_query/` tier because the fakeshop models do not use `BigIntegerField` / `PositiveBigIntegerField` today (verified via `grep -rn "BigInt" examples/fakeshop/` — no matches per spec line 51's pre-existing check). Adding a fakeshop model column just to exercise `BigInt` through the new helper is gold-plating; Decision 9's alternatives-rejected list (spec lines 413–415) explicitly rejects this.

Per `docs/builder/BUILD.md` "Coverage is the maintainer's gate, not a worker's tool", no `pytest --cov*` invocation appears in this slice. If Worker 2 chooses to run a focused test invocation (e.g., to confirm the post-migration project schema still imports), the invocation MUST include `--no-cov` to opt out of `pytest.ini`'s auto-applied `--cov`. The plan does not require a test run for Slice 3; `uv run ruff format .` and `uv run ruff check --fix .` are the only required commands.

### Implementation discretion items

These are choices Worker 1 has assessed and decided are at Worker 2's discretion. None are architectural questions; each has two (or more) equally valid shapes and the spec does not pin one over the other.

1. **Position of `config=strawberry_config()` between `query=Query,` and `extensions=[DjangoOptimizerExtension()],`.** Pinned by the spec at line 50 and the showcase pattern at spec lines 143–149; no discretion. Worker 2 places the kwarg in the order `query=`, then `config=`, then `extensions=`.

2. **Single-line vs multi-line shape of the widened `from django_strawberry_framework import ...` line.** The post-widen single-line form is `from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types, strawberry_config` — 105 characters, under the 110-char limit but tight. The project's existing import-block convention elsewhere in `examples/fakeshop/` favors single-line imports when they fit (verified at `examples/fakeshop/config/schema.py` current line 16 and `examples/fakeshop/apps/library/schema.py`). Worker 2 may either (a) keep the import on a single line (matches the file's current single-line shape) OR (b) split across three indented lines inside parentheses (matches the project's broader multi-line import convention seen in `django_strawberry_framework/__init__.py`). Recommendation: keep on a single line since 105 < 110 and the file's existing import is already single-line; let ruff format rewrap if the formatter prefers otherwise. Either shape is acceptable and the contract is the symbol set, not the layout.

3. **Whether to add a comment near the `strawberry.Schema(...)` call referencing `docs/GLOSSARY.md#strawberry_config` (the future anchor that lands in Slice 4).** Optional. A short comment ("# `config=strawberry_config()` registers package-defined scalars (today: `BigInt`).") would help a future fakeshop reader understand the kwarg's purpose. Recommendation: omit the comment for Slice 3 — the symbol's purpose is self-documenting against the import line, and a forward link to a GLOSSARY anchor that doesn't exist yet (Slice 4 creates it) would be a dangling reference. The example project's schema file is a thin showcase, not a tutorial; cluttering it with explanatory comments would distract from the migration pattern the spec is demonstrating.

### Spec slice checklist (verbatim)

The following sub-checklist is copied verbatim from `docs/spec-020-scalar_map_helper-0_0_7.md` lines 49–51. Worker 1 ticks each `- [x]` during final verification as the contract lands.

- [x] Slice 3: Example-app migration
  - [x] [`examples/fakeshop/config/schema.py`](../examples/fakeshop/config/schema.py): rewrite the `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` call (the file's sole `strawberry.Schema(` invocation, anchored at [`examples/fakeshop/config/schema.py #"strawberry.Schema(query=Query"`](../examples/fakeshop/config/schema.py)) to `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`. Add `strawberry_config` to the existing `from django_strawberry_framework import ...` line. No other change.
  - [x] [`examples/fakeshop/apps/library/schema.py`](../examples/fakeshop/apps/library/schema.py) and [`examples/fakeshop/apps/products/schema.py`](../examples/fakeshop/apps/products/schema.py): audit only — no edits expected. The example app schemas reference `BigInt` indirectly via the Django field-to-scalar converter table at [`django_strawberry_framework/types/converters.py #"BigInt,"`](../django_strawberry_framework/types/converters.py); they do not import the symbol directly today (verified via `grep -n "BigInt" examples/fakeshop/`, which currently returns no matches per the Step-5 grep). If a future card uses `BigInt` directly in a fakeshop schema (e.g., explicit `id: BigInt` annotations), no consumer code changes are needed because the symbol's import path is unchanged.

---

## Build report (Worker 2)

### Files touched

- `examples/fakeshop/config/schema.py` — two edits per the Plan:
  1. Widened the existing `from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types` line (line 16) to add `strawberry_config` as the third symbol. Post-edit line is 106 characters — under the 110-char line-length limit (verified via `awk 'NR==16 {print length($0)}'`), so kept on a single line per discretion item 2's recommendation; ruff format did not rewrap it.
  2. Inserted `config=strawberry_config(),` between `query=Query,` and `extensions=[DjangoOptimizerExtension()],` in the sole `strawberry.Schema(...)` constructor call (lines 26–30 post-edit). Trailing comma preserved per `AGENTS.md` line 17 (COM812).

### Tests added or updated

- None. Per the Plan's `### Test additions / updates` section: Slice 3 ships zero new tests. Transitive coverage comes from (a) every `examples/fakeshop/test_query/test_*.py` test that imports the project schema at module-import time, which now exercises `strawberry_config()` through the `StrawberryConfig` carrying the `_PACKAGE_SCALAR_MAP`, and (b) the two in-process integration tests Slice 2 added in `tests/test_scalars.py` (`test_bigint_serializes_int_via_strawberry_config_schema`, `test_bigint_parses_decimal_string_via_strawberry_config_schema`). The fakeshop models do not use `BigIntegerField` / `PositiveBigIntegerField` (verified pre-plan), so duplicating the integration tests at the live-HTTP tier would require gold-plating a new model column — explicitly rejected by Decision 9.

### Validation run

- `uv run ruff format .` — pass. `118 files left unchanged` (the existing `COM812 may cause conflicts when used with the formatter` warning is standing-config noise from the repo's pre-existing ruff configuration and not introduced by this slice).
- `uv run ruff check --fix .` — pass. `All checks passed!`
- `git status --short` after both ruff invocations:
  ```
   M django_strawberry_framework/__init__.py
   M django_strawberry_framework/scalars.py
   M docs/spec-020-scalar_map_helper-0_0_7.md
   M examples/fakeshop/config/schema.py
   M tests/base/test_init.py
   M tests/test_scalars.py
   M tests/types/test_converters.py
  ?? docs/builder/bld-slice-1-helper_module_and_bigint_redefinition.md
  ?? docs/builder/bld-slice-2-tests.md
  ?? docs/builder/bld-slice-3-example_app_migration.md
  ?? docs/builder/build-020-scalar_map_helper-0_0_7.md
  ```
  Classification:
  - `examples/fakeshop/config/schema.py` — **slice-intended** (the sole source edit; appears in `### Files touched`).
  - All other `M` entries (`django_strawberry_framework/__init__.py`, `django_strawberry_framework/scalars.py`, `docs/spec-020-scalar_map_helper-0_0_7.md`, `tests/base/test_init.py`, `tests/test_scalars.py`, `tests/types/test_converters.py`) — **pre-existing dirty state from Slices 1 and 2**, both `final-accepted` per the build plan's checklist. Not introduced by Slice 3; not unrelated tool churn. Left in place per `AGENTS.md` line 32 (do not auto-revert pre-existing dirty state).
  - The `??` entries are the in-flight build artifacts and the build plan itself; tracked once the maintainer commits. Not source churn.
  - Audit-only files `examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/apps/products/schema.py` are NOT in the modified list, confirming DoD item 8 (spec line 647).
- Focused test commands: none run. Per `AGENTS.md` line 14 (do not run pytest after edits) and the Plan's explicit "no pytest required for Slice 3" note. The maintainer's full pipeline gates pytest at the final test-run gate.

### Implementation notes

- **Single-line import shape kept.** Per discretion item 2 (Plan): the widened line is 106 characters (under 110), and the file's existing convention is single-line imports; ruff format did not rewrap it. The alternative multi-line parenthesized shape would have been equally valid; chose the recommendation in the discretion item.
- **No explanatory comment added near `strawberry.Schema(...)`.** Per discretion item 3 (Plan): chose to omit the optional comment forward-referencing `docs/GLOSSARY.md#strawberry_config` because (a) Slice 4 has not yet shipped the GLOSSARY anchor, so the link would dangle, and (b) the example schema is intentionally a thin showcase, not a tutorial.

### Notes for Worker 3

- No shadow-file usage. Static inspection helper was not run for Slice 3:
  - `examples/fakeshop/config/schema.py` is 30 source lines (post-edit, verified via `wc -l`); well below the 50-line "added logic" or 150-line "existing file" thresholds for non-package files. Not under `django_strawberry_framework/optimizer/` or `types/`.
  - The two audit-only files were not modified, so the "adds logic to" trigger does not fire on them either.
- The diff is two lines. Worker 3 may verify the contract via `git diff examples/fakeshop/config/schema.py` directly; no unusual control flow, no new helper, no new symbol.
- The pre-existing modified files in `git status --short` are the Slice 1 and Slice 2 outputs (both `final-accepted` per `docs/builder/build-020-scalar_map_helper-0_0_7.md`); they are not in Slice 3's diff scope.

### Notes for Worker 1 (spec reconciliation)

- None. The slice landed exactly as planned: the spec's pinned shape at line 50 (`strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`) matches the post-edit constructor call verbatim, and the import widen at line 50 matches the file's existing single-line convention. No spec gap, no spec conflict, no unstated assumption surfaced during implementation.

---

## Review (Worker 3)

### Slice 3 diff scope

Filtered out of review per the cumulative-diff trap rule: pre-existing dirty state from final-accepted Slices 1 and 2 (`django_strawberry_framework/__init__.py`, `django_strawberry_framework/scalars.py`, `docs/spec-020-scalar_map_helper-0_0_7.md`, `tests/base/test_init.py`, `tests/test_scalars.py`, `tests/types/test_converters.py`) and the in-flight build artifacts under `docs/builder/`. The single source-file diff under Slice 3 review is `examples/fakeshop/config/schema.py` (verified via `git diff -- examples/fakeshop/config/schema.py`):

```examples/fakeshop/config/schema.py:16,26-30
- from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types
+ from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types, strawberry_config

  schema = strawberry.Schema(
      query=Query,
+     config=strawberry_config(),
      extensions=[DjangoOptimizerExtension()],
  )
```

The audit-only files (`examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/apps/products/schema.py`) produced empty diffs — confirmed via `git diff -- examples/fakeshop/apps/library/schema.py examples/fakeshop/apps/products/schema.py`. DoD item 8 satisfied.

### Static inspection helper

Skipped. Slice 3 adds <5 lines outside `django_strawberry_framework/`; below all `BUILD.md` thresholds (no new `.py` file, no `optimizer/` or `types/` touch, no 30+ line addition under the package, no 50+ line addition outside the package).

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- None. The migration reuses the existing import line (widened in place) and the existing sole `strawberry.Schema(...)` invocation (widened in place). No new helper, no parallel data flow, no repeated literal introduced. The Plan's DRY analysis section explicitly enumerated the three near-miss over-migration paths (touching per-app schemas, splitting the import line, editing the test-local schema in `test_multi_db.py`); the diff matches none of them.

### Public-surface check

Confirmed via `git diff -- django_strawberry_framework/__init__.py` that the only change to `__init__.py` is Slice 1's previously-accepted widening (`from .scalars import BigInt, strawberry_config` and `"strawberry_config"` appended to `__all__`). Slice 3 does NOT touch `django_strawberry_framework/__init__.py`; the public-export contract is unchanged by this slice.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### Spec slice checklist walk

- [x] Slice 3 sub-check 1: `examples/fakeshop/config/schema.py` rewritten. Post-edit content at lines 16 and 26–30 matches the spec's pinned shape (`strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`) verbatim. `strawberry_config` added to the existing single-line `from django_strawberry_framework import ...` line. No other change.
- [x] Slice 3 sub-check 2: audit-only verification of `examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/apps/products/schema.py`. Both files produced empty `git diff` output; neither is in the modified-files list. Per DoD item 8 and Decision 9, no edits expected and none occurred.

### Kwarg ordering check

Confirmed `query=`, `config=`, `extensions=` is the post-migration canonical shape per spec Decision 9 (line 404) and the showcase pattern at spec lines 143–149. The post-edit constructor call places `config=strawberry_config(),` on its own line between `query=Query,` and `extensions=[DjangoOptimizerExtension()],`, with trailing commas preserved on every kwarg per `AGENTS.md` COM812.

### Single-line import shape

Verified via `awk 'NR==16 {print length($0)}'` that the widened import line is 106 characters — under the 110-char limit (`AGENTS.md` line 16). The single-line shape matches the file's pre-edit convention and Plan discretion item 2's recommendation. Ruff format did not rewrap it per the build report's validation run.

### What looks solid

- The diff is the minimum possible expression of the slice contract: exactly two lines changed in exactly one file, both lines pinned verbatim against spec line 50 and the Decision 9 shape.
- Audit-only DoD item 8 is structurally enforced by the diff being empty for both per-app schema files, rather than requiring a separate audit comment in the source.
- The kwarg ordering anticipates Slice 4's doc examples (`docs/README.md` Quick start, `GOAL.md` astronomy showcase, `TODAY.md` schema block) which will reference this exact constructor shape — no drift risk between source and forthcoming docs.
- The Plan's DRY analysis pre-flagged three over-migration traps (per-app schemas, import-line split, `test_multi_db.py` test-local schema); the diff avoided all three.

### Temp test verification

- No temp test files used. The slice's two-line diff is small enough to verify by reading; transitive coverage is owned by the live HTTP suite under `examples/fakeshop/test_query/` (imports the project schema at module-import time, exercising `strawberry_config()` during `StrawberryConfig` construction) plus the two Slice 2 integration tests (`test_bigint_serializes_int_via_strawberry_config_schema`, `test_bigint_parses_decimal_string_via_strawberry_config_schema`). Disposition: not applicable; no temp tests created.

### Notes for Worker 1 (spec reconciliation)

- None. The diff matches the spec's pinned shape verbatim; no spec edit warranted. Decision 9's "one place only" scope held — the diff touches exactly `examples/fakeshop/config/schema.py` and nothing else.

### Review outcome

`review-accepted` — every spec sub-check is addressed by the diff, no High/Medium/Low/DRY findings, public-surface unchanged, CHANGELOG and documentation surfaces untouched (as the slice contract requires), and the kwarg ordering matches the canonical post-migration shape that Slice 4 will reference in doc examples.

---

## Final verification (Worker 1)

- **Spec slice checklist:** every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` is now `- [x]`. Both sub-bullets landed verbatim against the spec:
  - Sub-check 1 (the `examples/fakeshop/config/schema.py` rewrite): verified via `git diff -- examples/fakeshop/config/schema.py`. The post-edit constructor call is `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])` and the import line widened in place from `from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types` to `from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types, strawberry_config`. The diff is exactly two changed lines in exactly one source file. Matches the spec's pinned shape at spec line 50 character-for-character (modulo the spec's prose-paragraph layout vs the source's per-kwarg-line layout — the spec pins the API call, not the source layout).
  - Sub-check 2 (audit-only on the per-app schemas): verified via `git diff -- examples/fakeshop/apps/library/schema.py examples/fakeshop/apps/products/schema.py` (empty output — neither file is in the modified set). DoD item 8 (spec line 647) satisfied.
- **DRY check across this and prior slices:** Slice 3's two-line edit is mechanical and does not introduce new logic; the only DRY-relevant question is whether the `config=strawberry_config()` invocation pattern is duplicated across other `Schema(...)` construction sites in this build. Examined: the Slice 2 converter-table migration in `tests/types/test_converters.py` widened 10 `strawberry.Schema(query=Query)` sites to `strawberry.Schema(query=Query, config=strawberry_config())`; the Slice 2 integration tests in `tests/test_scalars.py` use the same pattern; Slice 3 widens the single fakeshop project schema to the same shape; Slice 4 will widen the doc examples (`docs/README.md`, `GOAL.md`, `TODAY.md`) to the same shape. **Disposition: the repeated `config=strawberry_config()` pattern IS the post-migration consumer contract, not a DRY violation.** It is the canonical demonstration of the helper this card ships — the spec's central premise (Decision 5, "hard break in alpha") is precisely that consumers add this one-liner at every `strawberry.Schema(...)` construction site. Consolidating it behind a wrapper would defeat the explicit design rejection of `dst.Schema(...)` in [Decision 2](#decision-2--helper-api-shape-and-module-location) ("Wrapping `strawberry.Schema(...)` shadows the upstream symbol and hides composition"). No new duplication, no new helper warranted.
- **Existing tests still pass:** ran `uv run pytest --no-cov examples/fakeshop/tests/ examples/fakeshop/test_query/`. Exit code: 0. Result: **75 passed, 1 skipped, 2 warnings in 23.46s**. The 1 skipped item is a pre-existing PostgreSQL-only fixture; the 2 warnings are pre-existing `DATABASES`-override warnings from `examples/fakeshop/tests/test_commands.py` (sharded-mode tests). Every test in both fakeshop test trees imports the project schema at module-import time, which now exercises `strawberry_config()` during `StrawberryConfig` construction — the all-passing result confirms the schema construction is intact post-migration.
- **Spec reconciliation:** no spec edit warranted from Slice 3's diff content. Worker 2 and Worker 3 both surfaced no notes for spec reconciliation. The status-line refresh (spec line 4: "Slices 1–2 shipped" → "Slices 1–3 shipped (helper module + `BigInt` redefinition; tests; example-app migration); Slices 4–5 remain.") is the per-spawn status-line re-verification described in `docs/builder/worker-1.md` "Spec status-line re-verification (every Worker 1 spawn)"; recorded under `### Spec changes made (Worker 1 only)` below.
- **Final status:** `final-accepted`.

### Summary

Slice 3 shipped a two-line migration on `examples/fakeshop/config/schema.py`: widened the existing `from django_strawberry_framework import ...` line to add `strawberry_config`, and inserted `config=strawberry_config(),` between `query=Query,` and `extensions=[DjangoOptimizerExtension()],` in the file's sole `strawberry.Schema(...)` constructor call. The two per-app schemas (`apps/library/schema.py`, `apps/products/schema.py`) were verified audit-only — both produced empty diffs, as expected (they carry only `@strawberry.type`/`@strawberry.field` decorator usage and no `strawberry.Schema(...)` construction). Zero new tests added; transitive coverage is owned by every `examples/fakeshop/test_query/test_*.py` test (each imports the project schema at module-import time and now exercises `strawberry_config()` through `StrawberryConfig` construction) plus the two in-process integration tests Slice 2 added in `tests/test_scalars.py`. Focused-test run on the fakeshop trees: 75 passed, 1 skipped, exit 0. The slice's diff is the minimum-possible expression of the spec contract; the migration is now in place for Slice 4 (docs) to mirror across `docs/README.md`, `GOAL.md`, `TODAY.md`, and `docs/GLOSSARY.md`.

### Spec changes made (Worker 1 only)

- `docs/spec-020-scalar_map_helper-0_0_7.md` line 4 — refreshed the in-flight status line from "Slices 1–2 shipped (helper module + `BigInt` redefinition; tests); Slices 3–5 remain." to "Slices 1–3 shipped (helper module + `BigInt` redefinition; tests; example-app migration); Slices 4–5 remain." Slice that triggered the edit: Slice 3 (this slice). Reason: the per-spawn spec status-line re-verification required by `docs/builder/worker-1.md` "Spec status-line re-verification (every Worker 1 spawn)" — stale status lines compound across slices if not refreshed at each Worker 1 spawn, so the spec now reflects Slice 3's final-accepted state.
