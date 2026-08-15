# Package build plan: visibility_boundary / 0.0.14 (045)

Spec source: `docs/spec-045-visibility_boundary-0_0_14.md`
Target release: `0.0.14` (already cut by the joint release `6a86d21f`; this card owns no version quintet — spec Decision 7)
Build rule: one round at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every round must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential rounds (see `## Ownership partition` below for the per-round file lists).
Hot-path declaration: **R1b only** (added after R1 surfaced a code defect; the original declaration of `none` held only while every round was documentary). The seal runs per visibility-hook resolution, i.e. per resolver per request, and canonical reconstruction was already measured at roughly 1.7x on simple/medium queries and 2.3x on an annotation-heavy shape, so R1b owes a before/after number for the same metric measured both times (`BUILD.md` `## Hot-path budget`). R1, R2, R3, integration, and the final gate: none — no runtime code.
Floor-verification scope: **R1b only** — it changes queryset / expression-graph validation, which is a Django ORM compile-surface seam, so its focused scope (`tests/utils/test_querysets.py` plus the row-survival surfaces `tests/test_connection.py`, `tests/test_relay_node_field.py`, `tests/test_list_field.py`) re-runs in an isolated floor venv, owned by the R1b builder pass and confirmed by the final gate. R1, R2, R3: none — documentation, DB-backed generated docs, and a tracked file move only.
Pre-flight: passed on 2026-07-31; baseline: clean (`git status --short` empty); cleanup: `docs/shadow/`, `docs/builder/temp-tests/`, `docs/builder/worker-memory/` cleared and the four memory files seeded empty; `scripts/review_inspect.py` smoke OK; `.gitignore` lists all three scratch paths; `check_spec_glossary.py --spec docs/spec-045-visibility_boundary-0_0_14.md` exits 0 (9 terms, all anchors resolve).

**Pre-flight step 3 deviation (recorded, deliberate).** Old `build-*.md` / `bld-*.md` artifacts from the `044` and `046` cycles are present and **were not deleted**. They are tracked, committed records of already-shipped work (`bld-044-r1..r3`, `build-046-*`, `bld-slice-*`, `bld-review-*`), and this cycle's artifacts take new `bld-045-*` paths that were verified absent. Deleting a committed prior cycle's record is the one irreversible pre-flight mistake (`worker-0.md` `## Pre-flight procedure` step 3); the review-round carve-out ("the prior cycle's `bld-*.md` artifacts are the record of the work now under review and must survive") is the governing shape here, because this cycle's input is already-built, already-committed work.

## Cycle shape: three closeout rounds, not spec slices

The spec's `## Slice checklist` declares **one** documentation slice, and that slice already shipped: the card is `DONE-045-0.0.14` in the kanban DB, `KANBAN.md` / `KANBAN.html` render it in Done, all five authored glossary terms exist as `## ` headings in `docs/GLOSSARY.md`, and `docs/spec-045-visibility_boundary-0_0_14-terms.csv` is on disk at one row per anchor. The work this cycle owes is the closeout the slice did not carry, so the rounds below are **review rounds** in the `BUILD.md` `## Review rounds` sense (input = already-built work), each driven through the unchanged `Status:` chain:

- **R1 — rationale extraction + spec/code reconciliation.** `docs/spec-045-visibility_boundary-0_0_14-rationale.md` does not exist. It is the deliberative layer of a spec whose deliberation is unusually load-bearing: several adversarial review rounds plus a post-`0.0.14` canonical-reconstruction rearchitecture produced the current contract, and none of that reasoning has a keyed home. (This line originally asserted "nine" rounds. R1's sourcing pass could evidence five rounds plus one root fix, only three of them carrying an index anywhere, and refused the figure — corrected here rather than left as a number a later pass would treat as measured, per `BUILD.md` `## Claims are proven mechanically, never accepted on prose`.) Worker 1 authors it, and in the same pass reconciles the spec against the code that actually landed — **corrections state the current contract directly in the spec; what changed and why goes in the rationale file** (`BUILD.md` `## Spec rationale extraction`).
- **R1b — expression-owned bound-payload retention (CODE round, maintainer-decided).** R1's reconciliation pass found, and Worker 0 and Worker 3 independently verified, that an expression-owned bound payload survives the seal **by reference**: `_expr_graph_defect` proves a `Value` node genuine and then reaches its children through `get_source_expressions()`, which a `Value` answers `[]`, so its `value` slot is never validated; `_reconstructed_value` rebuilds the node but routes that slot to `_normalized_bound_value`, whose `for … else` returns unchanged anything descending from no plain-data base and not an `enum.Enum`. `_direct_rhs_defect` rejects exactly that shape on a `Lookup`'s right-hand side, so the boundary applies its own admitted-bound-value rule inconsistently. Worker 3's probe widened it: a **`list` subclass** bound the same way is also retained, and a post-seal `append` is visible inside the sealed query — so the retention is not limited to opaque scalars, and it is the ownership class `dfa86f90` set out to close generically. **Maintainer decision: fix the root cause**, with two constraints — do **not** duplicate functions another package already provides, and where the limitation genuinely belongs to another package, cap the contract there rather than working around it (unless that package has a bug, which is then named as such). Escalated as contract-level before any builder was dispatched (`BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch`); rejected alternatives are recorded in `docs/builder/bld-045-r1b-bound_payload_retention.md`.
- **R2 — documentation completion.** Verify the standing docs describe what exists: the five glossary bodies against the implemented boundary, the terms CSV's importability, the card body's DoD/prose, and whether `docs/README.md` / `docs/TREE.md` claims about the boundary still hold. Generated docs are DB-backed — edit the DB, regenerate (`BUILD.md` `### Generated docs are DB-backed`).
- **R3 — spec archive.** The spec and its two companions move to `docs/SPECS/` / `docs/SPECS/appx/` with the full three-direction cross-reference sweep and the `SpecDoc.path` repoint + regenerate (`docs/SPECS/NEXT.md` Step 8, run in archive-only mode: there is no new active spec, so Step 8 actions 4 and 6 do not apply).

Archival is licensed by the maintainer's explicit instruction for this cycle and is executed as a Worker 1-owned final-verification step (`BUILD.md` `### Spec stays at its working location`).

## Baseline-dirty out-of-scope files

None; the baseline is clean. `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are **concurrent-writable generated/binary files** (`BUILD.md` `### Tracked binary / generated files`): a maintainer session may rewrite them mid-cycle. Churn in them is not proof of this cycle's output, a same-size binary diff is not proof of a no-op, and none of them is ever blind-`git checkout`ed as tool drift.

## Do-not-touch (every round)

- `CHANGELOG.md` — `AGENTS.md` forbids edits without explicit permission; the `0.0.14` entry already shipped.
- `docs/feedback.md`, `docs/feedback2.md` — maintainer artifacts, never edited, and never named in code, commits, or the DB.
- `pyproject.toml` `[project].version`, `django_strawberry_framework/__init__.py` `__version__`, `tests/base/test_init.py` — spec Decision 7: no version quintet here.
- Every other cycle's artifacts: `docs/builder/bld-044-*`, `docs/builder/bld-slice-*`, `docs/builder/bld-review-*`, `docs/builder/bld-integration.md`, `docs/builder/bld-final.md`, `docs/builder/build-044-*`, `docs/builder/build-046-*`.
- `docs/spec-046-*`, `docs/spec-05*` — other cards' specs; `spec-046` stays live at `docs/` (its own archive belongs to the next spec author's `NEXT.md` Step 3/8 sweep, not to this card).

## Ownership partition

Sequential rounds, so each round owns every file it writes and no two rounds run concurrently.

- **R1** — `docs/spec-045-visibility_boundary-0_0_14-rationale.md` (new), `docs/spec-045-visibility_boundary-0_0_14.md` (Worker 1 only), `docs/builder/bld-045-r1-rationale_reconciliation.md`.
- **R1b** — `django_strawberry_framework/utils/querysets.py`, `tests/utils/test_querysets.py`, `docs/builder/bld-045-r1b-bound_payload_retention.md`, `docs/builder/temp-tests/r1b/**`. The spec stays R1's (custodian-only), so R1b records its required amendment under `### Notes for Worker 1 (spec reconciliation)` rather than editing it.
- **R2** — `examples/fakeshop/db.sqlite3` (glossary/kanban ORM rows), `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html` (all four regenerate-only), `docs/spec-045-visibility_boundary-0_0_14-terms.csv`, `docs/spec-045-visibility_boundary-0_0_14.md` (Worker 1 only), `docs/README.md`, `docs/TREE.md` (only if a claim is wrong), `docs/builder/bld-045-r2-doc_completion.md`.
- **R3** — the moved `docs/SPECS/spec-045-visibility_boundary-0_0_14.md`, `docs/SPECS/appx/spec-045-visibility_boundary-0_0_14-terms.csv`, `docs/SPECS/appx/spec-045-visibility_boundary-0_0_14-rationale.md`, `examples/fakeshop/db.sqlite3` + `KANBAN.md` + `KANBAN.html` (the `SpecDoc.path` repoint and regenerate), any doc carrying a `spec-045` link, `docs/builder/bld-045-r3-spec_archive.md`.

## Artifact list

- `docs/builder/bld-045-r1-rationale_reconciliation.md`
- `docs/builder/bld-045-r1b-bound_payload_retention.md`
- `docs/builder/bld-045-r2-doc_completion.md`
- `docs/builder/bld-045-r3-spec_archive.md`
- `docs/builder/bld-045-integration.md`
- `docs/builder/bld-045-final.md`

## Checklist

- [ ] R1: Rationale extraction + spec/code reconciliation -> `docs/builder/bld-045-r1-rationale_reconciliation.md`
- [ ] R1b: Expression-owned bound-payload retention (code) -> `docs/builder/bld-045-r1b-bound_payload_retention.md`
- [ ] R2: Documentation completion (glossary bodies, terms CSV, card body, standing-doc claims) -> `docs/builder/bld-045-r2-doc_completion.md`
- [ ] R3: Spec archive to `docs/SPECS/` + companions to `docs/SPECS/appx/` + cross-reference sweep -> `docs/builder/bld-045-r3-spec_archive.md`
- [ ] Cross-round integration pass -> `docs/builder/bld-045-integration.md`
- [ ] Final test-run gate -> `docs/builder/bld-045-final.md`

## Worker-0 pre-dispatch verification (`BUILD.md` `### Worker 0 verifies every finding against source before dispatching`)

Recorded per round in that round's artifact preamble by Worker 0's dispatch, and summarized here as each round is dispatched.

- R1b dispatch carried: the retention mechanism read at HEAD by Worker 0 (`::_reconstructed_value` falling through to `::_normalized_bound_value`), independently confirmed by Worker 3's read-only probe under `docs/builder/temp-tests/r1/`, and escalated to the maintainer as a contract choice before dispatch. Decision: fix the root cause under the no-duplication / cap-at-the-other-package constraints.
- R1 dispatch carried: the eight spec Decisions' enforcing-symbol lists verified against `django_strawberry_framework/utils/querysets.py` at HEAD, each symbol confirmed present or reported absent with evidence. See `docs/builder/bld-045-r1-rationale_reconciliation.md` `## Plan (Worker 1)`.
