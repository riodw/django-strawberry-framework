# Package build plan: connection_optimizer / 0.0.9 (033)

Spec source: `docs/spec-033-connection_optimizer-0_0_9.md`
Target release: `0.0.9`
Date created: 2026-06-12
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

Pre-flight: passed on 2026-06-12; baseline: clean (`git status --short` empty); cleanup: no old `build-*.md`/`bld-*.md` artifacts existed, `docs/builder/worker-memory/` + `docs/builder/temp-tests/` + `docs/shadow/` confirmed empty and re-cleared after the `review_inspect.py` smoke run. Checks: `review_inspect.py` runs (smoke on `optimizer/walker.py`); `.gitignore` lists all three scratch paths; `check_spec_glossary.py --spec docs/spec-033-connection_optimizer-0_0_9.md` → `OK: 38 terms`, exit 0.

## Baseline-dirty out-of-scope files

None. Working tree was clean at pre-flight. Any file that appears dirty mid-build without a worker's edit is presumptively the maintainer's concurrent work (per `AGENTS.md`): workers do not edit or revert it.

## Build-wide context flags

- **Version boundary (joint `0.0.9` cut owns the bump — spec Decision 12):** NO slice edits `pyproject.toml`, `__version__`, `tests/base/test_init.py::test_version`, or `uv.lock`; NO `CHANGELOG.md` release heading is promoted. On-disk version stays `0.0.8`; `0.0.9`-tagged surfaces ship under `[Unreleased]`. The version bump is the maintainer's release act, not a slice.
- **Joint-cut mechanism gate (spec lines 5, 54, 422):** Slices 1 and 2 are ONE mechanism split into two reviewable commits — they must land together (one PR, two commits, or Slice 1's planner branch gated off until Slice 2 consumes it) so `main` never carries a planned-but-unconsumed window prefetch. Within this build cycle they are dispatched as two sequential slices, but the maintainer's commit posture keeps them in one cut. Dependencies: Slice 3 and Slice 4 build on 1–2; Slice 5 builds on 2; Slice 6 builds on 2–5; Slice 7 lands last.
- **CHANGELOG-edit permission is Slice-7-only (spec lines 47, 543):** `AGENTS.md` withholds `CHANGELOG.md` edits without explicit instruction. Slice 7's doc-update step is the explicit per-card grant — only the Slice 7 dispatch may touch `CHANGELOG.md`, and only under `[Unreleased]` (no version-heading promotion). Slices 1–6 must NOT edit `CHANGELOG.md`.
- **Slice 7 is DB-backed generated-doc work (spec line 554; `BUILD.md` "Generated docs are DB-backed"; `worker-0.md` "Closing out a kanban card"):** `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` are rendered from `examples/fakeshop/db.sqlite3` via `scripts/build_*_md.py`. The card-move and glossary-flip mean **edit the DB via the Django ORM, then regenerate** — never hand-edit the rendered markdown. This card ships **no net-new glossary symbol**, so no terms-CSV entry is added.
- **No new source module (spec Decision 11):** every edit lands in an existing module with an existing test twin (`walker.py`, `plans.py`, `extension.py`, `connection.py`, `types/definition.py`, `types/finalizer.py`, `types/resolvers.py`); tests extend existing files. No new test file.
- **Staged seams (spec line 436):** any staged-but-not-implemented seam uses an `AGENTS.md`-style `TODO(spec-033 Slice N)` anchor (paired with `NotImplementedError` where a call path must fail loudly), removed in the change that ships that slice.
- **Coverage is the maintainer's gate:** no worker runs `pytest` with `--cov*` flags. Worker-local validation is `uv run ruff format .` + `uv run ruff check --fix .`. The final gate runs `uv run pytest --no-cov` once.

## One-slice-at-a-time rule (short copy)

Build only one slice at a time. Do not start the next slice until the current slice's plan → build → review → final-verification → spec-reconciliation cycle is complete and Worker 1 has set the artifact `final-accepted`. After all seven spec slices are accepted, run the cross-slice integration pass, then the final test-run gate. No maintainer pause between slices on the happy path; escalate genuine blockers immediately.

## DRY-first rule (short copy)

Before any code: is this the maximally DRY shape that stays readable? Duplicated logic, parallel data flows, near-copies between modules, and repeated string/key/tuple literals are build-time defects. Worker 1 plans for DRY; Worker 3 enforces it before accepting; Worker 1 re-checks DRY across slices at the integration pass. (Spec-specific DRY pressure points: the `edges { node }` helper consolidation into the walker so one implementation serves root + nested unwrap — Decision 9; the deterministic-order helper hoisted to `plans.py` so plan-time window order and resolve-time order share one source — the cursor-parity invariant of Decision 4; `_check_n1` parameterized rather than duplicated into `connection.py` — Decision 8.)

## Artifact list

- `docs/builder/bld-slice-1-plan_foundation.md`
- `docs/builder/bld-slice-2-fast_path.md`
- `docs/builder/bld-slice-3-cache_key_hygiene.md`
- `docs/builder/bld-slice-4-strictness_wiring.md`
- `docs/builder/bld-slice-5-library_sql_shape.md`
- `docs/builder/bld-slice-6-products_conversion.md`
- `docs/builder/bld-slice-7-doc_wrap.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: plan-side foundation — selection-helper consolidation, `relation_connections` synthesis metadata, argument-aware alias handling, union context publish, walker recognition, relation-kind-correct windowed-`Prefetch` planning (spec lines 56-64; Decision 3 / Decision 4 / Decision 9) -> `docs/builder/bld-slice-1-plan_foundation.md`
- [x] Slice 2: connection-class fast path — windowed-row wrapper from the synthesized resolver, generated connection class derives edges / cursors / `pageInfo` / `totalCount` from annotations with per-parent fallback for ambiguous empty windows (spec lines 65-69; Decision 5) -> `docs/builder/bld-slice-2-fast_path.md`
- [x] Slice 3: plan-cache key hygiene — nested-connection pagination variables hash into the plan-cache key, root pagination variables stay out (incl. through root-level fragments) (spec lines 70-73; Decision 7) -> `docs/builder/bld-slice-3-cache_key_hygiene.md`
- [x] Slice 4: strictness wiring for connection paths — connection pipeline consults union-published strictness sentinels so an unplanned, unserved nested-connection access surfaces under `"warn"` / `"raise"` without clobbering parent plan context (spec lines 74-77; Decision 8) -> `docs/builder/bld-slice-4-strictness_wiring.md`
- [x] Slice 5: live library nested-connection SQL-shape coverage — the deferred fixed-query-count + nested-`totalCount`-no-per-parent-COUNT + visibility-filtered-window pins for the two-level genres→books connection shape (spec lines 78-80) -> `docs/builder/bld-slice-5-library_sql_shape.md`
- [x] Slice 6: products connections-only conversion — the four products list resolvers become `DjangoConnectionField`s (cookbook mirror); `test_products_optimizer_*` re-pinned through `edges { node }`, denial gates re-pinned on synthesized args, accounting for the `relay_max_results` cap and appended `ORDER BY pk` (spec lines 81-84; Decision 10) -> `docs/builder/bld-slice-6-products_conversion.md`
- [x] Slice 7: doc updates + card-completion wrap — GLOSSARY flip + caveat sweep, `docs/README.md` / `docs/TREE.md` / `TODAY.md` / `README.md` updates, `CHANGELOG.md` `[Unreleased]` bullets (explicit permission grant), KANBAN card → Done via the kanban DB + re-render; no version-file edits (spec lines 85-86; Doc updates; Decision 12) -> `docs/builder/bld-slice-7-doc_wrap.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
