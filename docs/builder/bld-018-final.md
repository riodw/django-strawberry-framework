# Build: Final test-run gate — spec-018 residual closeout cycle

Spec reference: `docs/SPECS/spec-018-meta_primary-0_0_6.md` (whole file)
Rationale companion: `docs/SPECS/appx/spec-018-meta_primary-0_0_6-rationale.md`
Status: final-accepted

Run immediately after the cycle's cross-round integration pass, in the same Worker 0 spawn — the
combined dispatch was recorded in that pass's own preamble. `HEAD`: `de2601e9`.

**Closeout note, 2026-08-18.** The two per-round artifacts this cycle produced —
`bld-review-1-spec018_rationale.md` (R1: rationale extraction, spec reconciliation, code-completeness
audit) and `bld-integration.md` (the cross-round integration pass) — were **deleted at closeout** by
the maintainer's instruction, **before this cycle was committed, so they appear in no commit and are
not recoverable from git history**, leaving `docs/builder/build-018-meta_primary-0_0_6.md` and this
file as the cycle's surviving record. Everything either artifact held that a later reader needs is folded in
here: the integration pass's measured results under `## Integration pass results, folded in` below,
and R1's findings in the deferred-work catalog. **Citations to either filename elsewhere in this file
or in the build plan are historical, naming a pass rather than a readable file** — the same condition
the spec-017 closeout produced, whose broken pointers cost commit `09003dc2` to repair. No sentence
below depends on opening a deleted file.

## What a green gate does and does not prove here

Stated up front because it governs how every row below should be read:

- **This round wrote zero lines of code.** Its writable set is four paths, all markdown; no `.py` file
  was opened for write in any pass. **So a red suite could not have been this round's doing, and a
  green suite proves nothing about this round's diff.** The gate is run because the process requires
  it and because an unattributed failure must never be waved through — not because it can validate a
  documentation change.
- **The tree is not this round's alone.** The build plan's preamble records a dirty baseline, and the
  concurrent session's churn grew across every pass of this round. At gate time `git status --short`
  shows **94 entries**, of which **15 are under `django_strawberry_framework/`** — 14 `.py` modules
  (`exceptions.py`, `filters/inputs.py`, `forms/converter.py`, `mutations/resolvers.py`,
  `optimizer/field_meta.py`, `optimizer/walker.py`, `relay.py`, `testing/relay.py`, `types/base.py`,
  `types/finalizer.py`, `types/resolvers.py`, `utils/converters.py`, `utils/relations.py`,
  `utils/write_values.py`) plus the `debug_toolbar.html` template — and **12 are under `tests/`**.
  **Every one of those 27 is a concurrent session's work.** Not read as work product, not edited, not reverted
  (`AGENTS.md` rule 34).
- **Therefore the gate below describes the working tree, which is mostly someone else's, not this
  round's diff and not `HEAD`.** Attribution rule applied to every command: a failure is this round's
  only if the failing path is in this round's four-path writable set. None was, because there were no
  failures.

## Gate results, command by command

| # | Command | Result | Attribution |
|---|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `6151 passed, 40 skipped in 59.98s`, exit **0** | No failure to attribute |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).`, exit **0** | — |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit **0** | — |
| 4 | `uv run ruff format --check .` | **PASS** — `424 files already formatted`, exit **0** | — |
| 5 | `uv run ruff check .` | **PASS** — `All checks passed!`, exit **0** | — |
| 6 | `git diff --check` | **PASS** — no output, exit **0** | — |

**No `--cov*` flag was passed to any command**, and plain `uv run pytest` — which is a coverage run in
this repository — was never invoked (`docs/builder/BUILD.md` `## Coverage is the maintainer's gate,
not a worker's tool`). No `git stash`, `checkout`, `restore`, or `worktree` at any point in this
round. Neither `ruff` invocation used `--fix`; both are the read-only forms the gate specifies.

**No failure was recorded, so no baseline exception was invoked.** The plan's preamble records a
dirty-baseline exception and it stayed unused — worth stating, because a recorded exception that goes
unexercised is evidence the gate ran honestly rather than leaned on it.

**The suite was fully interpretable.** No collection error, no half-saved concurrent edit, no
unattributable row: 6,151 tests ran to a clean exit against a tree carrying 27 dirty package and test
files. That is a real result and it is reported as one — but it is a result about the concurrent
session's in-flight work, which happens to be green right now, not a statement about anything this
round produced.

### One check outside the gate's list, re-run here

`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-018-meta_primary-0_0_6.md` ->
`OK: 15 terms - all have glossary entries and at least one spec link.`, exit **0**. Not a gate command,
but it is the one script that can be broken by a rationale move, and it broke mid-pass twice in this
cycle's sibling (spec-017) and once here. Re-run at the gate rather than cited from an earlier pass.

`uv run python scripts/check_trailing_commas.py --check` on this cycle's five written markdown paths
-> exit **0**. Repo-wide the same command exits 1 on exactly two paths, **both outside this cycle's
writable set and both untouched**: a concurrent session's untracked
`examples/fakeshop/test_query/test_products_visibility_api.py` (an over-exploded layout in a file this
round never opened) and an agent memory file under `.claude/`, outside the package entirely. Recorded
and escalated below; not fixed, not reverted.

## Floor verification

**Scope: `none`, as declared in the plan and correctly.** No Django, Strawberry, or channels seam is
touched by this round — no source at all is. **No floor venv was built**, and the shared `.venv` was
not mutated, downgraded, or installed into at any point.

## Deferred work catalog

**No deferred work; the round delivered its dispatch end-to-end.** Every dispatched finding, every
custodian item, Worker 3's seven findings, RR-1, and the final-verification pass's own Decision 1
finding landed inside the round. D-R3-1, escalated non-blocking, was closed by deletion rather than
parked.

Three items are **handed to the maintainer**. None is a deferral of this round's work — each lies
outside the writable set by the dispatch, not by choice. This is the next spec author's reading list.

1. **The live `KANBAN.md` `DONE-018-0.0.6` card body is stale in one place.** It names the
   public `audit_primary_ambiguity()` — private as `_audit_primary_ambiguity` since commit `13d8dac5`,
   2026-05-18. Recorded by the R1 pass under
   `### Notes for Worker 1 (spec reconciliation)` item 1 — that artifact is deleted, so the readable
   source is the companion's `### What this cycle deliberately did not fix`, which carries the same
   finding and its 2026-08-18 correction. **The fix is a DB edit plus a regenerate**, not a
   file edit: `KANBAN.md` renders from `examples/fakeshop/db.sqlite3` via
   `scripts/build_kanban_md.py`, and both the DB and the rendered doc are on this cycle's
   do-not-touch list. The spec's own copy of that body was moved verbatim into the companion,
   deliberately uncorrected — correcting a historical copy would falsify it as a record.

   **Correction, 2026-08-18 — this item said "stale in two places" and the second was not real.**
   It also charged the body with quoting the retired duplicate-primary message
   `"<new> is already declared primary as <existing>"` (reworded by commit `21212a19`). That claim
   was read off the verbatim card-body copy held in the companion, which does carry the message, and
   attributed to the board, which never did: measured against `examples/fakeshop/db.sqlite3`, the
   substring `declared primary` returns **zero `CardItem` rows and zero `CardReference` rows
   board-wide**, and zero occurrences in the rendered `KANBAN.md`. The withdrawn half is recorded
   here rather than deleted because the homing bullet on `TODO-ALPHA-052-0.1.0` cites this item by
   name and tells its author not to hunt for a second edit. Two further facts surfaced in the same
   measurement, both now carried by that bullet: the one real staleness is `CardItem` 723 (`note`,
   order 6), and **10 of this card's 15 `note` items end mid-sentence** (rows 720, 721, 722, 723,
   725, 726, 727, 728, 732, 733) from an import-time truncation predating every residual cycle, so
   row 723 is both stale and clipped. This is the same defect class the round's own reports hit
   three times — a description outliving the source it was derived from — reaching the hand-off
   list itself.
2. **Two `check_trailing_commas` layout violations exist repo-wide and belong to no cycle.**
   `examples/fakeshop/test_query/test_products_visibility_api.py` (untracked, a concurrent session's
   new live-tier test, `should collapse (< threshold, over-exploded)`) and
   `.claude/projects/.../memory/one-spec-owns-each-feature.md` (missing the link-def scaffold, and
   outside the package). Both will block a pre-commit run until someone who owns them fixes them.
3. **No standing-doc edit is owed for this card.** `docs/GLOSSARY.md`, `CHANGELOG.md`,
   `docs/README.md`, and `TODAY.md` were each read against `HEAD` and each reflects this card's
   shipped state — the glossary marks `Meta.primary` `shipped (0.0.6)` and quotes the landed error
   message, and `CHANGELOG.md` documents both the message reword and the `register` / `get` semantics.
   Recorded so the next author does not re-derive it.

## Integration pass results, folded in

The cross-round integration pass returned **no integration findings** and required no consolidation
dispatch: there is no code in this cycle, no documentation duplication across the spec, the companion,
`docs/GLOSSARY.md` or `CHANGELOG.md`, no surviving staged anchor, and no parked follow-up beyond the
hand-offs catalogued above. It made no spec edit.

Its measurements are preserved here because they are the evidence for this cycle's central claim —
that the rationale extraction was a **move**, not a copy:

| Measure | Result |
|---|---|
| Long sentences (>=90 chars) in the spec | 371 |
| Long sentences (>=90 chars) in the companion | 203 |
| **Byte-identical sentences shared by both** | **0** |
| **Near-duplicate runs of >=110 chars (`difflib` longest-match over all 75,313 pairs)** | **0** |

Both files were stripped of fenced code and table rows before splitting, so quoted pseudocode in the
companion's historical records does not inflate the comparison. Two zeros over 75,313 pairs is the
`Moved` / `Kept deliberately` / `Deleted outright` / `Reconciled in place` disposition set holding in
fact rather than in assertion.

Four further mechanical confirmations from the same pass: **32** `path::Symbol` refs in the spec and
**17** in the companion all resolve against a parsed AST; the **5** surviving `#"substring"` citations
each resolve inside the named symbol's own source range, extracted via `ast` rather than by searching
the file; the moved round-label vocabulary (`H[1-3]` / `M[1-2]` / `L[1-5]` / `rev[1-6]` / `revision`)
returns **0** hits under a word-boundary sweep; and **9** pointer links carry each spec site whose
deliberation moved to the companion. Cross-document overlap against `docs/GLOSSARY.md` and
`CHANGELOG.md` peaks at 45 characters and every hit is an identifier or the mandated link scaffold —
no contract sentence and no error message is duplicated.

The one place the pair could have told two stories was the `plan_optimizations` call site, where the
spec carried a precise checklist box against a vague routing-table row. Worker 3 caught it as RR-1 and
both sites now spell the chain identically (`_get_or_build_plan`, reached from `._optimize` via
`.apply_to`). That was the coherence defect the check exists to find, found and closed inside the
round.

## Summary

The gate is six commands and all six pass: `pytest --no-cov` at `6151 passed, 40 skipped`, both Django
consistency checks clean, `ruff format --check` and `ruff check` clean, `git diff --check` clean. The
recorded dirty-baseline exception went unused because nothing failed. Floor-verification scope is
`none` and no floor venv was built.

The honest reading of that green is narrow, and the artifact says so rather than banking it: **this
round wrote no code, so the suite can neither convict nor acquit it.** What the gate genuinely
establishes is that the tree this round is being closed against is in a coherent state, and that
nothing this round did — four markdown files — broke a build it never touched.

`Status: final-accepted`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
