# Build: Final test-run gate

Spec reference: `docs/spec-032-full_relay-0_0_9.md` (all seven slices + the cross-slice integration pass final-accepted; this pass per BUILD.md "Final test-run gate")
Status: final-accepted

## Final test-run gate (Worker 1)

Performed 2026-06-11, fresh spawn. All standing docs (AGENTS.md, START.md, BUILD.md "Final test-run gate" + "Coverage is the maintainer's gate, not a worker's tool", worker-1.md), the active spec, the build plan, `bld-integration.md` (final-accepted, with its carried-forward DEFER list), and all seven `bld-slice-*.md` artifacts read in full for the deferred-work catalog walk. Worker memory (`worker-1.md`) read for the carry-forward watchpoints.

Coverage discipline: NO `--cov*` flag passed anywhere in this pass. `pytest` ran with the explicit `--no-cov` to opt out of `pytest.ini`'s auto-applied `--cov`. Line coverage was neither inspected nor asserted — that is the maintainer's / CI's `fail_under = 100` gate.

### Spec status-line re-verification (worker-1.md per-spawn rule)

Spec line 5 read at spawn start: "Status: in build — all seven slices implemented … build complete pending the cross-slice integration pass and the final test-run gate." The cross-slice integration pass is now closed (`bld-integration.md` → `final-accepted`) and this final gate has run clean, so that wording was stale. Edited — see `### Spec changes made (Worker 1 only)` below.

### Gate command results

| # | Command | Result |
| --- | --- | --- |
| 1 | `uv run pytest --no-cov` (full sweep, all three test trees) | **PASS** — 1629 passed, 3 skipped, 0 failed (74.29s) |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — System check identified no issues (0 silenced) |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — "No changes detected" (exit 0) |
| 4 | `uv run ruff format --check .` | **PASS** — 241 files already formatted (exit 0) |
| 5 | `uv run ruff check .` | **PASS** — "All checks passed!" (exit 0) |
| 6 | `git diff --check` | **PASS** — clean, no whitespace errors / conflict markers (exit 0) |

Notes on the runs:

- **The known one-off flake did NOT recur.** `tests/types/test_definition_order_schema.py::test_relay_declared_type_emits_node_interface_and_global_id` (the Slice-3 Low / integration watchpoint) passed in the full `--no-cov` sweep AND in an isolated focused re-run (`uv run pytest ... -k test_relay_declared_type_emits_node_interface_and_global_id tests/types/test_definition_order_schema.py --no-cov` → 1 passed). No bisection needed — written off as the recorded transient; the gate passes on this test.
- **The 3 skips are expected, not failures.** They are the `FAKESHOP_SHARDED`-gated tests that do not run under the default pytest invocation (AGENTS.md: "Sharded-specific tests live behind `FAKESHOP_SHARDED` and do not run under the default pytest invocation"). Not a gate concern.
- **The `ruff format --check` `COM812` line** is the standard repo formatter warning documented in AGENTS.md (COM812 only auto-adds to already-multi-line constructs; `scripts/check_trailing_commas.py` owns trailing-comma layout). It is a warning, not a failure — the command reported "241 files already formatted" and exited 0.
- **`git diff --check` baseline.** The build plan's preamble recorded a clean baseline except the documented pre-flight artifact deletions; the working tree now carries the whole seven-slice build plus the integration consolidation. `git diff --check` (whitespace/conflict-marker only) is clean across all of it.

All six gate commands pass. No failing behavior to route back through an owning slice; no re-loop required.

### Deferred work catalog

Seeded by `bld-integration.md`'s carried-forward DEFER list (its `### Deferred-work list carried to bld-final.md's deferred-work catalog`, lines 227-237) and cross-checked by walking every per-slice artifact's `### Notes for Worker 1 (spec reconciliation)`, `### What looks solid`, and DRY-findings sections plus the integration `### Accepted deferrals and closed rulings`. The three Slice-7 out-of-scope escalations (card-033 stale citation, board-preamble cohort prose, CHANGELOG `[spec-orders]` link rot) were **resolved in-cycle** by the integration consolidation pass (FIX-NOW items 5/6/7, Worker 3 review-accepted, Worker 1 re-verified) and are therefore NOT open deferrals — they are recorded here as closed for the next author's traceability. Every remaining open item is either an accepted DRY deferral or pre-existing drift. The integration pass carried a DEFER list, so the catalog is enumerated (not the empty-build sentinel).

Open deferrals (the next spec author's reading list):

- **Relation-resolver near-copy → `WIP-ALPHA-033-0.0.9`.** Source: `bld-slice-3-relation_shapes.md` Worker-3 review Low + Slice-3 final verification, re-ruled in `bld-integration.md` `### Accepted deferrals` (d). Spec license: Decision 6 pins the standalone-helper shape. `connection.py::_build_relation_connection_resolver` near-copies `_build_connection_resolver`'s sync branch (~10 mechanical lines); consolidating now would route a framework-synthesized resolver through the consumer-resolver branch (semantic mislabel, pointless `_is_async_callable` run) and strand the helper's load-bearing docstring contract (the 033 prefetch-cache seam, the `many_resolver` accessor-identity pin, the strictness-blind posture). 033 wires strictness/planning into the connection pipeline and may genuinely diverge the two builders — re-rule at 033's build.
- **Fifth-guard "Relay-Node-shaped DjangoType" wording, 2 sites → weigh at `WIP-ALPHA-033-0.0.9`.** Source: `bld-slice-2-root_node_fields.md` DRY findings + `bld-integration.md` `### Accepted deferrals` (c). No spec line licenses a change; this is build hygiene. `connection.py:738` (shipped `DONE-030` wording, a connection-field guard) and `relay.py:136` (the named node-field factory + "target") have distinct subjects and the shared parenthesized tail `"(or inherit \`relay.Node\` directly)"` is only 2x (below the 3rd-copy hoist rule). 033 works in `connection.py` next, so any cross-module parameterization is better weighed there.
- **TREE.md target-tree `test_wrap.py` back-fill.** Source: `bld-slice-7-doc_card_wrap.md` final-verification item 3 + `bld-integration.md` `### Accepted deferrals` (TREE.md back-fill). No spec line licenses it; pre-existing drift predating this card (the target `tests/testing/` tree never mirrored the shipped `testing/_wrap.py`). Slice 7 added a minimal target `testing/` entry carrying only `test_relay.py`; the missing `test_wrap.py` mirror is an optional one-liner for the next doc-touching card, not worth a DB-free doc edit this cycle.
- **`tests/types/test_definition_order_schema.py::test_relay_declared_type_emits_node_interface_and_global_id` flake — DISCHARGED at this gate.** Source: `bld-slice-3-relation_shapes.md` Worker-3 review Low, carried as the integration watchpoint. It did NOT recur in the full `--no-cov` sweep or the isolated re-run (see the gate-command notes). Closed as the recorded transient; no further action.

Accepted-closed DRY rulings (recorded for completeness; no future action unless a trigger fires):

- **`.Meta.interfaces entry ` 2x f-string prefix** (`types/base.py`). Source: `bld-slice-1-validation_diagnostics.md` DRY findings + `bld-integration.md` `### Accepted deferrals` (b). Accepted; a constant for a 2x 24-char prefix hurts readability more than it saves. Re-open only if a future gate adds a 3rd `…Meta.interfaces entry…` raise.
- **`global_id_for: ` 4x message prefix** (`testing/relay.py`). Source: `bld-slice-5-testing_relay.md` DRY findings + `bld-integration.md` `### Accepted deferrals` (f). Accepted closed; all four sites are one-function-local, no second module would import a 15-char prefix constant.
- **Opted/bare connection-description asymmetry** (`connection.py` — opted `<TypeName>Connection` classes ship description-less; the bare path preserves the inherited Strawberry description). Source: `bld-slice-4-cursor_conformance.md` plan amendment + Worker-2 notes + `bld-integration.md` `### Accepted deferrals` (g). Watch-only; both are shipped SDL surface and normalizing would churn shipped opted SDL for zero consumer value. Revisit only if a future card deliberately normalizes connection SDL.

Resolved in-cycle by the integration consolidation pass (closed — listed for traceability, NOT open):

- **Gate-tail 3x hoist** `"or inherit \`relay.Node\` directly."` → consolidated into `_RELAY_NODE_GATE_INHERIT_TAIL` (`bld-integration.md` FIX-NOW item 3; byte-identical, Worker 3 verified).
- **Two repeated GraphQL documents** in `tests/test_relay_node_field.py` → hoisted to `_CATEGORY_QUERY` / `_CATEGORIES_QUERY` (FIX-NOW item 4).
- **Stale "staged" docstring** at `tests/test_relay_node_field.py:8-9` (Slice-2/Slice-4 deferred Low) → reworded to past tense (FIX-NOW item 1).
- **7 trailing-comma layout violations** on build-added lines → fixed via `scripts/check_trailing_commas.py` (FIX-NOW item 2).
- **Card-033 stale `WIP-ALPHA-032-0.0.9` citation** (`KANBAN.md`) → ORM-edited to `TODO-BETA-051-0.1.5` and regenerated (FIX-NOW item 5).
- **Board-preamble "four WIP cards" cohort prose** (`KANBAN.md`) → ORM-edited to the three-done-one-WIP shape and regenerated (FIX-NOW item 6).
- **CHANGELOG `[spec-orders]` link rot** → re-relativized to `docs/SPECS/spec-028-orders-0_0_8.md` under the explicit per-card grant (FIX-NOW item 7).

Catalog headline count: **4 open deferrals** (relation-resolver near-copy → 033; fifth-guard wording → 033; TREE.md `test_wrap.py` back-fill; the flake — discharged at this gate). Plus 3 accepted-closed DRY rulings and 7 integration-resolved items recorded for traceability.

### Spec changes made (Worker 1 only)

- `docs/spec-032-full_relay-0_0_9.md` line 5 (status line) — "build complete pending the cross-slice integration pass and the final test-run gate" updated to record that the cross-slice integration pass is closed (`final-accepted`) and the final test-run gate passed clean (full `--no-cov` sweep 1629 passed / 3 skipped, Django checks + lint/format/diff gate all green); the build is complete and uncommitted, pending the maintainer's commit and the joint-`0.0.9`-cut version bump (Decision 13). Triggered by the final-test-run-gate spawn per the worker-1.md per-spawn status-line re-verification rule. This is a status-line currency edit only — no normative contract changed.

`scripts/check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md` re-run after the edit: OK (40 terms — all have glossary entries and ≥1 spec link).

### Final status

`final-accepted`. All six gate commands pass (full `--no-cov` sweep 1629 passed / 3 skipped / 0 failed; `manage.py check` clean; `makemigrations --check --dry-run` no changes; `ruff format --check` 241 files already formatted; `ruff check` all checks passed; `git diff --check` clean). The known transient did not recur and is discharged. No genuine failure, so no owning slice re-loop. The build cycle is closed; Worker 0 marks the final checklist box `- [x]` and hands off to the maintainer (workers never commit).
