# Package build plan: onboarding_docs_spec_consolidation / 0.0.4 (007)

Spec source: `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` (**already archived** — the spec, its `-terms.csv`, the `SpecDoc.path` row, and both `KANBAN.md` references already sit at their post-archive locations; item R3 verifies rather than performs the move)
Target release: `0.0.4` (**shipped long ago** — card `DONE-007-0.0.4`, `target_version.number` `0.0.4`, released 2026-05-08 at `231911a8`; the package is at `0.0.14` in `pyproject.toml`)
Date created: 2026-08-14
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging. A fact told twice across the spec and its rationale sibling goes stale in one of them — the rationale carries the deliberation, the spec carries the contract, and neither restates the other. This cycle additionally inherits `## The single-ownership law`, which extends the same rule ACROSS specs and standing docs.
Ownership partition: none; sequential residual items. (Declared explicitly rather than omitted, per `worker-0.md` `### Ownership partition`, so an interrupted item's output stays attributable against a tree two concurrent sessions are also writing.)
Hot-path declaration: none. No residual item changes package source, so no item runs per request, per resolver, per row, per connection, or per outbound message.
Floor-verification scope: none. No residual item touches a Django / Strawberry / channels integration seam — the cycle edits one archived spec and creates one rationale sibling.
Pre-flight: passed on 2026-08-14 with **four** recorded deviations (below); baseline: four dirty entries, all belonging to the **concurrently running spec-006 cycle** or the card-wrap it is performing — see `## Baseline-dirty out-of-scope files`; cleanup: **nothing deleted** (Deviations 1, 3, 4), every path this plan creates verified absent.

## This is a residual-completion cycle, not a fresh build

Spec-007 is a **card-snapshot stub**, and among the smallest specs in the repository: **2,282 bytes / 65 lines** measured at `947f7494` before R1's move, against spec-006's 10,934 and spec-005's 13,373. (Fifth smallest of the 56 tracked `docs/SPECS/spec-*.md`, behind the 011 / 012 / 013 / 024 stubs — see the seventh correction under `### Verified spec-versus-HEAD drift`, which is where this plan's original false superlative is recorded.) It has no `## Slice checklist`, no `## Doc updates`, no Decisions, no implementation plan, and — uniquely among the six residual cycles so far — **almost no deliberative layer to move**. Its `## Scope` and `## Other` sections are a verbatim render of card 7's `CardItem` rows.

Its deliverable shipped at `0.0.4` on 2026-05-08 (`231911a8`), and the file itself was **created afterwards**, at `81e4704d` ("docs: archive prior specs to `docs/SPECS/` and renumber per Step 8 pass"), to give the DONE card a durable `SpecDoc` FK target. Only three commits have ever touched it: `81e4704d` (creation), `e1f9ed26` (glossary CSV backfill), `1592bb90` (the kanban `Status` consolidation). It has never been reconciled against anything.

The immediate precedent is the **spec-006 residual cycle** (`docs/builder/build-006-public_surface-0_0_3.md`), which is **running right now in a concurrent session** — its plan was created today and it seeded its worker memory at 10:25, minutes before this pre-flight. That cycle is itself modelled on spec-005, spec-004, spec-003 (`20a9752f`), spec-002 (`d613887c` / `a76da376`), and spec-001 (`cfd1f873`). This plan follows the same three-item shape and the same collision-avoidance discipline: **every path this cycle creates is `bld-007-` / `build-007-` prefixed**, and nothing belonging to another cycle is deleted, reverted, or re-seeded.

**What makes this spec different from its five predecessors.** Spec-005 was falsified in its *subject*; spec-006 in its *instruments*. Spec-007 is falsified in its **referents**: every sentence describes the *state of a documentation file*, and documentation state is the fastest-moving thing in this repository. Five of the six `## Scope` claims were true on the day they were written and are now wrong, incomplete, or naming a file that has since been renamed, regenerated from a database, or emptied of the thing the claim points at.

- The capability catalog it names — `docs/GLOSSARY.md` — **did not exist under that name at ship time**. At `231911a8` the file was `docs/FEATURES.md`; the rename landed twelve days later at `40c1855f`. The "comparison table" the same sentence names *did* exist then (`## Quick comparison`, a four-column `| Concern | graphene-django | strawberry-graphql-django | this package |`) and **does not exist at HEAD**. And the file is now rendered from the fakeshop glossary app's database rather than hand-authored.
- The root `README.md` was the "operational entry point" at `231911a8` because it carried Installation, Development Setup, Running, Testing, Build, and Publish. **All six moved to `CONTRIBUTING.md` and `docs/README.md`.**
- `docs/README.md`'s "three-minute path" names no section that exists anywhere in the repository; the phrase survives in exactly two places, this spec and the card body it was rendered from.
- The `CHANGELOG.md` claim — "no longer relies on design-doc pointers for release context" — was **falsified four minor versions later** by the `0.0.8` entry, which cites two spec files for exactly that purpose.

The one claim entirely true at HEAD is `docs/TREE.md`'s role, and even that has gained a provenance the spec cannot know: it is script-generated.

### Residual scope (this cycle's actual work)

- **R1 — spec rationale extraction.** `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` does not exist. `docs/builder/BUILD.md` `## Spec rationale extraction` makes the move the first substantive action of a build and pre-flight step 7 gates dispatch on it; the shipped cycle predates the rule by three months. Worker 1 is the only role that may perform it. See `### What R1 inherits` — the honest reading of "move" on a 2.3KB stub is the unusual part of this cycle, and it is decided in advance below rather than left to the mover.
- **R2 — reconcile the spec with what landed and what later changes corrected.** The maintainer's framing: *make sure the spec matches what actually exists, make sure the code is correct, and where later updates corrected what landed, the spec reflects that; the explanation of each change goes in the rationale, never in the spec.* Fourteen verified drift rows are tabled below. Worker 1 is the only role that may edit the spec.
- **R3 — finish the documentation and audit the archive.** Verify the durable docs describe the doc set the shipped card actually produced; verify the already-performed archive is complete in all three cross-reference directions, in the kanban DB, and in the terms-CSV importability chain; and run the `TODO(spec-007` / `TODO-<MILESTONE>-007` staged-anchor sweep.

**"Make sure the code is correct" is a read-only audit obligation, and for this card it has an unusually narrow reading.** Spec-007 shipped **no source code at all** — no package module, no test, no example app. `git show 231911a8` and the card's `Files likely touched` rows agree: five Markdown files and nothing else. So the audit obligation resolves to the documentation-integrity audit recorded at `### The read-only correctness audit — findings`, which found **no defect in package source** and **two falsified statements in standing documentation**, one of which this cycle may not fix (`CHANGELOG.md`, `AGENTS.md` rule 21). **No source file, test file, or example file is writable in this cycle.** If any pass finds a genuine correctness defect in shipped source, it is recorded as a finding and escalated to the maintainer — it does not become a source edit inside a documentation cycle.

## The single-ownership law

Maintainer instruction, given during the concurrent spec-006 cycle's pre-dispatch escalation and recorded in that cycle's plan. It is a standing contract-level decision about how specs relate to each other, not a spec-006-local one, so it binds every item here:

> each "thing"/feature should only exist concretely in a single spec, other specs can reference them (this should be rare as each spec should be able to stand on it's own) but the claim on ownership should exist in ONLY ONE spec

and, on the mechanics:

> since we did not fix every inbound reference in the same change last time, do that now

Consequences for this cycle, declared before dispatch so no pass improvises them:

1. **A concrete claim restated in two places is a defect**, and the duplicate is retired rather than kept in sync. Provenance decides which copy is the duplicate. This bites once here, at drift row **D11**: the spec's closing bullet restates the spec-filename and fold-in convention, whose owners are `AGENTS.md` rule 26 and `docs/builder/BUILD.md` `## Spec and build-plan filename pattern`. Spec-007 is the **borrower**, and its copy has already gone stale in two ways while the owners moved on. It points, or it says only the part it actually decided.
2. **This cycle retires and retitles nothing outside its own spec.** Spec-007 has **no inbound reference from any sibling spec** (`### Every reference TO spec-007` — verified by grep), so clause 2 of the law has nothing to bite on. That absence is itself a fact R2 may rely on: no rewrite here can break an inbound spec reference.
3. **Sibling specs, `AGENTS.md`, `START.md`, `BUILD.md`, and `CHANGELOG.md` stay read-only.** A pass that finds a defect in one records it for the maintainer and does not widen. `CHANGELOG.md` is doubly closed: `AGENTS.md` rule 21.

## Pre-flight outcome (7 steps, `docs/builder/worker-0.md` `## Pre-flight procedure`)

1. **Working-tree baseline is explicit.** `git status --short` → four entries, every one attributable to the concurrent spec-006 cycle or to the card-wrap it is performing. See `## Baseline-dirty out-of-scope files`. HEAD is `947f7494`.
2. **`scripts/review_inspect.py` runs.** `uv run python scripts/review_inspect.py django_strawberry_framework/conf.py --output-dir docs/shadow --stdout` emitted its overview (5 imports, 16 symbols, 2 control-flow hotspots, **0** TODO comments, 0 repeated string literals). Exit 0. Run against a small module deliberately: this cycle reads no package source, so the invocation is a tool smoke test and nothing more.
3. **Build artifacts are reset — DEVIATION 1, see below.** Verified instead that every path this plan creates is absent: no `docs/builder/build-007*`, no `docs/builder/bld-007*`, no `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`.
4. **`.gitignore` lists the untracked scratch paths.** `docs/shadow/` (line 174), `docs/builder/worker-memory/` (188), `docs/builder/temp-tests/` (192). Present.
5. **Scratch directories are cleared — DEVIATIONS 3 and 4, see below.** `docs/builder/temp-tests/` is empty. `docs/shadow/` and `docs/builder/worker-memory/` were **not** cleared: both hold the concurrent cycle's live state.
6. **Spec-doc consistency check.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` → `OK: 1 terms - all have glossary entries and at least one spec link.` Exit 0. Baseline for the constraint in `### The 1-anchor constraint`.
7. **Spec rationale is extracted.** **Not done — it is item R1 of this cycle.** Ordinarily this gates dispatch. Here it cannot, because R1 *is* the dispatch: the work whose spawns the gate protects was built and released before this plan existed, so there is no builder left to protect. R1 runs first regardless, so every later spawn in this cycle reads the reconciled spec exactly as the rule intends.

Two further baselines recorded at pre-flight, both green, both re-checked by any pass that writes:

- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` → exit 0 (link-definition scaffold and the 10 canonical group headers intact).
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` → **no match**. The spec carries no raw `path:NN` reference today; `AGENTS.md` rule 27 compliance is a property to preserve, not one to establish.

Spec size before R1: **2,282 bytes / 65 lines**, **zero** fenced code blocks. Worker 1 reports the after-count in the R1 artifact.

### Deviation 1 — a CONCURRENT cycle's `build-*.md` and `bld-*.md` artifacts are PRESERVED

Pre-flight step 3 deletes old `build-*.md` / `bld-*.md`. They are **not** deleted here:

- `docs/builder/build-006-public_surface-0_0_3.md` belongs to a cycle **running right now in another session** — it is untracked, was written today, and its worker memory was seeded at 10:25. Deleting it would destroy an active cycle's contract mid-flight.
- The eight older `build-*.md` plans and the `bld-003-*` / `bld-005-*` artifacts are **committed** records of closed cycles, and `BUILD.md` `### Cohorting, naming, and closure` ("Pre-flight for a round") already establishes that when a cycle's input is already-built work, the prior artifacts are the record of that work and must survive. Every residual item here operates on already-built, already-released work.
- **Collision is avoided by naming, not by deletion.** Every artifact this plan creates is `bld-007-`-prefixed and the plan is `build-007-`-prefixed; none of those paths exists.

### Deviation 2 — the `built` state is skipped where the deliverable is Worker-1-exclusive

`docs/builder/ARTIFACT.md` `## Status field ownership` gives `built` to Worker 2, and `worker-0.md` `## Per-slice dispatch` maps `planned` → Worker 2. Items **R1 and R2** have no Worker 2 role that could set it:

- **R1** — `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move, and states outright that **Worker 2 never reads the rationale file** — "that is the point of the move." Dispatching a builder at it would hand the file to the one worker the mechanism exists to keep away from it.
- **R2** — `BUILD.md` `## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the **only** role that may mutate the spec. R2's entire deliverable is spec edits.

So for R1 and R2 the chain is **Worker 1 (plan + perform, `planned`) → Worker 3 (audit, `review-accepted` | `revision-needed`) → Worker 1 (final verification, `final-accepted`)**, and Worker 0 reads `planned` on those artifacts as "dispatch Worker 3", not Worker 2. Declared here, before dispatch, so no pass improvises the mapping.

**Corollary, carried forward from the three prior residual cycles:** `worker-0.md` `## Per-slice dispatch` step 4 routes a Worker-3 `revision-needed` to Worker 2 for the apply-changes pass. On R1 and R2 that route does not exist — the same two rules that remove Worker 2 from the perform pass remove it from the fix. **The apply-changes pass for R1 and R2 is Worker 1's, and it sets `planned` again**, returning the artifact to the `planned` → Worker 3 mapping above. The loop is otherwise unchanged and repeats until Worker 3 has no unresolved finding.

The Worker 3 audit is **not** skippable alongside the Worker 2 build. `BUILD.md` names Worker 3 as a reader of the rationale file during review and as the pass that checks the finished work against it. A rewrite performed by the author is reviewed by an agent with no memory of why a sentence was cut — the only vantage point from which an over-cut looks like an over-cut. **R3 is expected to be a procedural-closure item** (`BUILD.md` `### Procedural-closure slices`): the audit below found nothing in this cycle's writable set for a builder to change, and the two documentation defects it did find are both outside it. If R3's own audit finds writable drift, it runs the full unmodified chain instead, and Worker 1 says which shape it took in the artifact.

### Deviation 3 — `docs/shadow/` was not emptied

Pre-flight step 5 clears it. It was not: it holds the concurrent spec-006 cycle's overviews plus this cycle's step-2 `conf.py` smoke.

This is safe and changes nothing operationally. `docs/shadow/` is gitignored, regenerable, and — per `AGENTS.md` rule 23 — **each generator clears its own folder before writing**, so a stale overview cannot be read as fresh output by any pass that runs the helper. A pass that wants a file it did not generate itself regenerates it rather than trusting the folder's mtime.

### Deviation 4 — worker memory is NAMESPACED, not re-seeded

Pre-flight step 5 re-seeds the four `docs/builder/worker-memory/worker-<N>.md` files empty. Doing so here would collide with the concurrent spec-006 cycle, which seeded `spec-006-worker-<N>.md` at 10:25 today, and would also touch the un-namespaced `worker-<N>.md` files this cycle does not own.

So this cycle uses its own namespace: **`docs/builder/worker-memory/spec-007-worker-<N>.md`**, seeded empty by Worker 0 at plan creation (verified present and zero-length). The rule's intent — a private notebook per worker that persists across a single build and is invisible to every other worker — is preserved exactly; what changes is only that three concurrent builds no longer collide in one file, which the rule never contemplated and which would have broken isolation in **every** direction. Every dispatch prompt in this cycle names the namespaced path and the standing "do not read the other workers' memory files" instruction; it additionally forbids reading the un-namespaced `worker-<N>.md` files and the `spec-005-*` / `spec-006-*` namespaces, which belong to other cycles.

## Baseline-dirty out-of-scope files

Workers neither edit nor revert these, and never `git checkout` them (`AGENTS.md` rule 34). Attribution is positive, not inferred: this cycle's writable set is the archived spec-007 file, its new rationale sibling, the four `bld-007-*` artifacts, this plan, and the four namespaced memory files — **no entry below is in any of them.**

- `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3` (`M`) — a concurrent card-wrap. The spec-006 cycle's plan declares a **DB-backed glossary completion** as authorized work, so these three are expected to keep moving throughout this cycle and a diff in them is that cycle's output, not this one's.
- `docs/builder/build-006-public_surface-0_0_3.md` (`??`) — the concurrent cycle's plan, mid-flight.

### First growth, recorded at the close of R1 (2026-08-14)

Reported by Worker 1, appended by Worker 0. **Nothing was reverted, and no worker may revert any of it.** `HEAD` has not moved (`947f7494`). Newly baseline-dirty, all out of scope:

- `docs/SPECS/spec-006-public_surface-0_0_3.md` (`M`), `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` (`??`), `docs/builder/bld-006-r1-rationale_move.md` (`??`) — the concurrent spec-006 cycle finished its own R1 mid-pass. Exactly the predicted growth.
- **`docs/review/rev-_cross_web_patches.md`, `rev-_django_patches.md`, `rev-_strawberry_patches.md`, `rev-apps.md`, `rev-conf.md` (` D`, unstaged deletions) — ESCALATED TO THE MAINTAINER, UNRESOLVED.** All five are tracked at `HEAD` and absent from disk; `REVIEW.md`, the five `review-0_0_*.md`, and `worker-*.md` are untouched. **Neither this cycle nor (per its plan's writable set) the spec-006 cycle touched `docs/review/`.** `AGENTS.md` rule 22 names `rev-*.md` committed source of truth and prescribes `git checkout HEAD -- docs/review/` to restore — which is **banned in this cycle** (the `git checkout` ban in `BUILD.md` `## Claims are proven mechanically`, and rule 34's no-auto-revert). Either a closing REVIEW cycle's authorized cleanup or a rule-22 violation by a third session; only the maintainer can tell, and only the maintainer can restore safely. **No worker in this cycle restores or reverts it**, and no pass treats the absence as its own output.

**This cycle's own work was not swept in.** Worker 1 verified `HEAD` unchanged at `947f7494` across the pass.

### Second growth, recorded at the close of R1's review (2026-08-14)

Reported by Worker 3, appended by Worker 0. Not reverted; `HEAD` still `947f7494`.

- `docs/review/review-0_0_14.md` (`??`) — a new untracked review document appeared during the review pass. Outside this cycle's writable set. It is **weak circumstantial evidence** that the five `rev-*.md` deletions above are a closing REVIEW cycle's authorized cleanup rather than a rule-22 violation, since both would then be one third session's work — but Worker 3 correctly drew no binding inference and neither does this plan. **The escalation stays open and the maintainer's call stands.**

### Third growth, recorded at the close of R1's re-review (2026-08-14)

Reported by Worker 3, appended by Worker 0. Not reverted; `HEAD` still `947f7494`.

- `django_strawberry_framework/_boundary_ordering.py`, `django_strawberry_framework/middleware/request_body.py`, `examples/fakeshop/test_query/test_transport_api.py`, `tests/test_views.py` (`M`) — **a third concurrent session is editing package source**, on the request-body boundary / transport surface. All four are declared read-only for this cycle and are unreachable from any Markdown pass in it, so attribution is unambiguous. **No worker in this cycle edits or reverts them**, and no pass treats their churn as its own output or as drift to fix. Their presence does raise the stakes on this cycle's final gate: a `pytest` or `ruff` failure in the transport surface is that session's in-flight work, and the plan's `## Baseline-dirty out-of-scope files` gate exception governs — reported, never blocking.

### Fourth growth, recorded at the close of R1's second apply-changes pass (2026-08-14)

Reported by Worker 1, appended by Worker 0. Not reverted; `HEAD` still `947f7494`. Twenty-four entries now.

- `docs/SPECS/spec-002-optimizer-0_0_2.md` (`M`), `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` (`M`) — Worker 1 read these as "a sibling spec-002 residual cycle is now running concurrently". **Worker 0 verified and that inference is wrong, in a way worth recording:** `git diff docs/SPECS/spec-002-optimizer-0_0_2.md` is `3 deletions(-)`, and the deleted heading is `## Visibility status`. That is precisely the **coordinated retirement `docs/builder/build-006-public_surface-0_0_3.md` declares as its `### Maintainer decision 1`**, fixing every inbound site in one change under the single-ownership law. So it is the already-known spec-006 cycle reaching R2, not a fifth session. Still out of scope, still never touched — but a pass should not carry "a new cycle appeared" forward as fact.
- `docs/review/rev-_boundary_ordering.md` (`??`) — a new `rev-*.md` whose slug matches one of the four concurrently-edited source files. Further circumstantial evidence that the five deleted `rev-*.md` are a REVIEW cycle regenerating its own artifacts rather than a rule-22 violation. **The escalation stays open and unresolved; this is evidence, not a finding, and no worker acts on it.**

### Fifth growth, recorded at the close of R1's final verification (2026-08-14)

- `docs/builder/bld-006-r2-spec_reconciliation.md` (`??`) — the concurrent spec-006 cycle reaching its own R2, which corroborates Worker 0's reading of the spec-002 edit above. Twenty-five entries now. Not touched, not reverted. The five deleted `docs/review/rev-*.md` remain **escalated and unresolved**.

### Sixth growth, recorded at the close of R3's audit (2026-08-14)

Reported by Worker 1, appended by Worker 0. Not reverted; `HEAD` still `947f7494`. Twenty-nine entries now.

- `docs/builder/bld-006-r3-doc_completion_archive.md` (`??`) — the concurrent spec-006 cycle at its own R3.
- **`docs/GLOSSARY.md` (`M`) — the last of the four concurrent-writable generated files has now gone dirty.** This is the spec-006 cycle's authorized DB-backed glossary completion, which its plan declares and which `## Concurrent-writable tracked binary / generated files` predicted. It moved this spec's `DjangoOptimizerExtension` anchor **mid-audit**, so any pass citing that entry by line number is citing a moving target: cite the heading symbol-qualified instead (`AGENTS.md` rule 27 already requires this; here it is load-bearing rather than stylistic). Both glossary-chain checks were re-run after the churn and held. **No pass in this cycle writes the DB or any generated doc**, and the plan's "attribution by diff is unavailable" premise now covers all four files rather than three.

### Eighth growth, recorded at the close of R3's final verification (2026-08-14)

Thirty-one entries. Two records, one of them a correction to this plan:

- `docs/builder/bld-006-final.md` (`??`, mtime 13:34) — the concurrent spec-006 cycle reaching its own final gate. Both residual cycles are now at the same stage, and their outputs were verified disjoint at R3.
- **Correction to the third growth section above: the transport session's source set is FIVE files, not four.** `django_strawberry_framework/_cross_web_patches.py` (mtime 12:57) joined it and was missed at the reading that recorded the section. Still out of scope, still never touched — but the population as first written was stale, and a baseline-dirty list that under-counts is exactly what makes a later pass mis-attribute a file to itself.

### Seventh growth, recorded at the close of R3's apply-changes pass (2026-08-14)

Thirty entries. Not a new file: **`docs/review/rev-_cross_web_patches.md` now reads ` M` (modified) rather than ` D` (deleted)** — it is back on disk with different content. So the escalated `docs/review/` set is currently **four deletions plus one modification**, not the five deletions the first growth section recorded, and the plan's earlier description of it is historical from here.

This is the strongest evidence yet that the deletions are a REVIEW cycle regenerating its own `rev-*.md` artifacts rather than a rule-22 violation — a file coming *back* is not what a stray `rm` looks like. **It remains evidence, not a conclusion, and the escalation stays open**: only the maintainer can confirm the intent, and no worker in this cycle touches, restores, or reverts any file under `docs/review/`.

**Expect this list to grow further.** The spec-005 cycle recorded four separate growth events across two days, including a concurrent session committing mid-cycle. `HEAD` may move during this cycle; **any pass quoting a commit hash from this plan re-derives it rather than trusting it**, and proves its own work was not swept into someone else's commit with `git log --stat` over this cycle's paths — never `git status` alone (`AGENTS.md` #"Staged `git mv` gets swept by a concurrent commit" is the standing hazard). If the list grows, workers **report it and never revert it**, and Worker 0 appends it here rather than a worker editing the plan.

**Baseline exception for the final test-run gate**, recorded here because `BUILD.md` `## Final test-run gate` requires it in the plan's preamble to be honoured: `uv run pytest --no-cov`, `uv run ruff format --check .`, `uv run ruff check .`, and `git diff --check` all read the whole tree, so they will see the concurrent cycle's churn. A failure attributable to a file this cycle never wrote does **not** block `final-accepted` and does **not** route back through a residual item's loop; it is reported to the maintainer. The gate still reports each command's real result — the exception governs what a result *blocks*, never whether it is recorded honestly.

## Concurrent-writable tracked binary / generated files

Churn in these is not proof a worker caused it (`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`). Three of the four are **already dirty** at this pre-flight from the concurrent card-wrap, so **attribution by diff is not available to this cycle** and no pass may treat a diff in them as its own output or as drift to fix.

- `examples/fakeshop/db.sqlite3` — **no residual item is expected to write it.** Card 7 is already Done, its `SpecDoc.path` already points at the archived location, its single glossary link already matches the terms CSV exactly, and `import_spec_terms --check` is green (verified below). Compare `iterdump()` semantics, never file bytes.
- `KANBAN.md`, `KANBAN.html` — generated; this cycle writes neither the DB nor the rendered files. Never hand-edited.
- `docs/GLOSSARY.md` — DB-rendered and **clean** at this pre-flight; no residual item is expected to change it. A diff here is either the concurrent cycle's authorized glossary completion or drift to investigate — never this cycle's output.

If any pass concludes a DB write is genuinely required, it **stops and escalates to Worker 0** rather than writing: a second session is mid-wrap on the same DB, and the two-consecutive-regenerate verification `worker-0.md` step 8 requires cannot distinguish this cycle's write from theirs while theirs is in flight.

## Build-wide context flags

- **`0.0.4` shipped on 2026-05-08 and the version quintet is at `0.0.14`.** No residual item touches `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, the GLOSSARY package-version line, or `uv.lock`.
- **No source or test file changes in this cycle.** Package source, `tests/`, and `examples/` code are read-only throughout, with **no docstring carve-out**: spec-007 shipped no source, so there is no source prose it owns.
- **`CHANGELOG.md` is closed.** `AGENTS.md` rule 21 governs, and drift row **D9** is a falsified claim *about* `CHANGELOG.md` that this cycle therefore reconciles **in the spec**, never by editing the changelog.
- **`README.md`, `docs/README.md`, `docs/TREE.md`, `AGENTS.md`, `START.md`, and `docs/builder/BUILD.md` are read-only.** The audit found them correct as written; where the spec disagrees with them, the spec is what moves.
- **The spec is already archived.** `BUILD.md` `### Spec stays at its working location` requires a move be plan-declared as a Worker-1-owned final-verification step. There is no move: `docs/SPECS/spec-007-…md` and `docs/SPECS/appx/spec-007-…-terms.csv` are already at their archived paths, `SpecDoc.path` already reads the archived path, and both `KANBAN.md` references already point there. **R1's new rationale file is therefore written directly to `docs/SPECS/appx/`** — the archived-companion location `AGENTS.md` rule 26 names — never to `docs/` first and moved after.
- **Only the maintainer commits.** No worker commits, and none creates or switches a branch.

## Worker-0-verified facts, passed into dispatch so no worker re-derives them

`worker-0.md` `## Closing out a kanban card` requires the live DB references be verified before a card/glossary edit is planned, because plan and spec text can carry stale ones. Read-only ORM queries, run 2026-08-14:

- `Card.objects.get(number=7)` → `card_id` `DONE-007-0.0.4`, `status.key` `done`, `target_version.number` `0.0.4` (alpha), `priority` `Medium`, `relative_size` `S`, title `0.0.4 onboarding docs and spec consolidation`. The card is **already Done**; no status flip is in scope, and the 2026-07-30 card renumber left 007 untouched (it rotated 045-068 only).
- `card.labels` → **three** keys: `docs`, `release`, **`internal`**. The spec's `## Card snapshot` lists two. See drift row **D3**.
- `card.planning_note` → **`''` (empty)**. The spec's `## Planning note` section carries the value `shipped`. See drift row **D4**.
- `SpecDoc` for card 7 → name `spec-007-onboarding_docs_spec_consolidation-0_0_4`, **`path` already `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md`**. No repoint needed. (`SpecDoc.path` is the writable column; `SpecDoc.url` is a read-only `@property` deriving from it — assigning `url=` raises.)
- `card.glossary_links` → **exactly one**: `djangooptimizerextension`, matching the single row in `docs/SPECS/appx/spec-007-…-terms.csv` (`optimizer behavior,djangooptimizerextension,Backfilled for DONE-card glossary linkage from the shipped spec body.`). One row per anchor, so the CSV is importable (`worker-0.md` `### DONE-card invariants` — a green `check_spec_glossary` alone does not prove this).
- Card 7 carries **fourteen `CardItem`s** across five sections: `Scope` ×6, `Files likely touched` ×5, `Why it matters` ×1, `Note` ×2. **Every row is `is_complete = True`**, and there is **no `Definition of done` section**. **No card-body edit is in scope** — a Done card's `Scope` is a record of what that card did, and every row is an accurate record of the `0.0.4` state even where the *present tense* it is written in no longer holds.
- **The spec's `## Scope` is a verbatim render of the six `Scope` rows, and its `## Other` is a lossy merge of the other eight** (`Why it matters` ×1, `Files likely touched` ×5, `Note` ×2 — flattened into one undifferentiated bullet list under a heading the card does not have). See drift row **D13**.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` Green at baseline. R3 re-runs it rather than trusting this reading, since the concurrent cycle is writing the DB.
- The one anchor resolves: `docs/GLOSSARY.md #"## \`DjangoOptimizerExtension\`"` exists.
- **Staged-anchor sweep:** `grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' .` → **zero hits anywhere**, spec included. `BUILD.md` `## Cross-slice integration pass` step 6 is therefore already discharged at baseline; R3 re-runs it as its backstop.

### The 1-anchor constraint

This is the **most fragile anchor profile of any residual cycle so far**, and it is a single point of failure by construction. `docs/SPECS/appx/spec-007-…-terms.csv` carries exactly **one** anchor, `djangooptimizerextension`, and its **sole carrier in the spec body is `## Scope` bullet 2** — the reference-style link `[optimizer behavior][glossary-djangooptimizerextension]` inside the sentence "`docs/README.md` is code-first: quickstart, three-minute path, [optimizer behavior][glossary-djangooptimizerextension], and status."

That sentence is drift row **D6** — one of the two most heavily falsified sentences in the file. So the one link the DONE-card glossary chain depends on sits **inside the prose R2 is most likely to rewrite**, with no second carrier anywhere and no margin at all: dropping it takes `check_spec_glossary` from `OK: 1 terms` to a failure, and breaks the `import_spec_terms` chain for card 7.

**R2 re-sites that link in the same edit that rewrites the sentence, never after.** The link is preserved by re-siting it into the surviving contract prose — never by re-adding narration the item just removed, never by editing the CSV, and never by leaving a hollow bullet behind purely to host it. **Every pass that writes the spec re-runs `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` and quotes the result in its artifact.**

### What R1 inherits

Spec-007 is **among the repository's smallest specs** — fifth of 56, behind the 011 / 012 / 013 / 024 stubs, and corrected from a false superlative this plan originally wrote here (seventh correction below) — and the first residual cycle whose spec may contain **no deliberative layer at all**. That inverts the mover's usual risk. On spec-004 the hard question was how to separate design intent from a falsified fence; here it is whether there is anything to move, and the failure mode is not over-cutting — it is **inventing deliberation that never happened** to justify the file's existence.

Decided in advance, so the mover does not have to improvise the judgement:

- **The move is expected to be small, and may be nearly empty.** The honest candidates are two: the preamble paragraph beginning "This file is intentionally lightweight" (a *process* justification for the stub's existence and an instruction to expand it, neither of which is a contract), and the `## Planning note` section whose entire content is the word `shipped` (a snapshot of a DB field that is now empty, from a model that no longer exists). A move that carries only those two is a **correct** move, not a thin one, and Worker 1 says so plainly rather than padding it.
- **A rationale file is still owed, and it is not owed the *move* — it is owed the RECORD.** `BUILD.md` `## Spec rationale extraction` requires each entry name the spec decision it serves by heading and anchor, and carry: the alternatives rejected and why each lost; every change the decision has undergone, with the round or later change that caused it; and any claim the decision once made and may no longer make. For this spec that third clause is the deliverable: **fourteen claims the spec makes and can no longer make**, each with the commit or later card that falsified it. That is precisely the maintainer's instruction that *explanations of the changes go in the rationale, not the spec*, and it is the only place in the repository where the `0.0.4` documentation-set history is recorded at all.
- **Do not fabricate rejected alternatives.** Where a drift row's history genuinely records a choice between options — the `FEATURES.md` → `GLOSSARY.md` rename, the hand-authored → DB-generated provenance change, the decision to keep the stub rather than expand it — the rationale records the alternatives and why each lost. Where the history records only a change with no visible deliberation, the entry says the change happened and names the commit, and **does not invent a debate**. An imagined alternative is worse than a missing one: it reads as evidence a question was examined.
- **The stub's own existence is the most valuable rationale entry available.** Why a 2.3KB card snapshot is the right shape for this card — as against the "expand it into the full builder-format spec" instruction the file itself carries, as against deleting it, as against back-writing a full spec for work that shipped three months earlier — is a live question every future reader of this file will ask, and it is answered nowhere. Note the precedent: **specs 011 (1,797 bytes), 012 (1,651), and 013 (1,669) are the same shape**, so the stub is a pattern, not an oversight.
- **Do not duplicate the siblings.** `docs/SPECS/appx/spec-001-…-rationale.md` through `spec-005-…-rationale.md` already exist, and a sixth is being authored concurrently for spec-006. R1 reads the closest one for shape, not for content. It must also not restate the reasoning of the cards that *caused* this spec's drift — those cards own their own decisions; this rationale records only what spec-007 claimed and how it fared.

### Verified spec-versus-HEAD drift — R2's input, verified by Worker 0

Read at HEAD (`947f7494`) on 2026-08-14, against source, the kanban DB, and `git show` at the `0.0.4` release commit `231911a8`. Each row is a claim the spec makes that HEAD complicates or falsifies. **A prescribed correction is not included: how the spec should read is Worker 1's call, and the alternatives it rejects belong in the rationale file.** Worker 1 re-verifies each row rather than trusting this table.

| # | Spec claim | HEAD reality | Owner of the move |
|---|---|---|---|
| D1 | Preamble: "This file is intentionally lightweight… **Before implementation work starts from this file**, expand it into the full builder-format spec described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`." | **Falsified twice over.** The work shipped at `0.0.4` on 2026-05-08 (`231911a8`); this file was created *afterwards* at `81e4704d`, as a back-fill so the DONE card had a `SpecDoc` FK target. There is no implementation work left to start, and the instruction to expand was never followed — nor should it be: specs 011 / 012 / 013 are the same deliberate stub shape. The sentence instructs a future reader to do something that is both impossible and unwanted | the card itself; the stub pattern |
| D2 | `Status:` line: "shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact" | **Accurate, and verified as the actual mechanism.** `examples/fakeshop/apps/kanban/signals.py` refuses to save a card with `status.key == "done"` unless it has both a linked `SpecDoc` and ≥1 `CardGlossaryTerm`. The stub is the `SpecDoc` target and the backfilled CSV row is the glossary link. This row is here so R2 does not "fix" a correct sentence | holds |
| D3 | `## Card snapshot`: "Labels: `docs`, `release`" | **Three labels in the DB**, not two: `docs`, `release`, **`internal`**. A snapshot section is only worth its accuracy | the DB |
| D4 | `## Planning note` section, whose entire content is the word "shipped" | **The field is empty** (`card.planning_note == ''`), and the model behind it is gone: `1592bb90` ("refactor(kanban): consolidate the card queue onto Status; drop PlanningState") retired the planning-state dimension. A section rendering a retired field's stale value | `1592bb90` |
| D5 | `## Scope` 1: "Root `README.md` is the canonical documentation map **and operational entry point**." | **First half true, second half falsified.** `README.md` still carries the `## Project documentation` map (eight rows, every link resolving). But at `231911a8` it also carried Installation, Development Setup, Running, Seeding, Test users, Sharded mode, Testing, Formatting, Updating Version, Build, Publish — **all of which moved out**, to `CONTRIBUTING.md` (dev setup / format / test / build / publish) and `docs/README.md` (install / quick start / running / seeding). The root README is now positioning + map + status | the `CONTRIBUTING.md` split |
| D6 | `## Scope` 2: "`docs/README.md` is code-first: quickstart, **three-minute path**, [optimizer behavior], and status." | **Two of four hold; one names nothing; the framing is now wrong.** Quickstart ✓ (`## Quick start`), status ✓ (`## Today and coming next`), optimizer behavior ✓ (`## Nested connection indexing`). "Three-minute path" names **no section anywhere in the repository** — the phrase's only two occurrences are this spec and `KANBAN.md:4794`, the card row it was rendered from. And "code-first" describes a 117KB / 1,003-line document whose bulk is now the production security profile, the transport boundary, the write-contract reference, and the session-auth deployment boundary (spec-046 / 047 / 048 all landed their consumer documentation here). **Sole carrier of the one glossary anchor** — see `### The 1-anchor constraint` | spec-046 / 047 / 048 doc landings |
| D7 | `## Scope` 3, first half: "`docs/GLOSSARY.md` is the capability catalog…" | **The file did not exist under that name when the card shipped.** At `231911a8` the capability catalog was `docs/FEATURES.md` (`## Feature status`, `## Current package surface`, `## Quick comparison`, … `## Deferred and future work`); the rename to `docs/GLOSSARY.md` landed twelve days later at `40c1855f` ("housekeeping: rename files"). The spec — written at `81e4704d`, after the rename — silently substitutes the new name into a claim about the old file, so the sentence cannot be checked against the state it describes | `40c1855f` |
| D8 | `## Scope` 3, second half: "…with value-led optimizer language **and comparison table**." | **The comparison table is gone.** At `231911a8` `docs/FEATURES.md` carried `## Quick comparison`, a four-column `\| Concern \| graphene-django \| strawberry-graphql-django \| this package \|`. HEAD's `docs/GLOSSARY.md` has no such table — its tables are the `## Index` (Entry \| Status) and `## Browse by category`. Separately, the file's **provenance changed**: it is now rendered from the fakeshop glossary app's DB by `scripts/build_glossary_md.py` and is not hand-editable source, so the sentence describes editorial choices a generator now owns. Upstream comparison survives elsewhere — the per-entry `⚛️` / `🍓` parity vocabulary and `README.md`'s "Why it's fast" — but not as the table this claims | the rename + the DB-generation conversion |
| D9 | `## Scope` 5: "`CHANGELOG.md` is condensed and **no longer relies on design-doc pointers for release context**." | **Falsified four minor versions later, and measurably.** `CHANGELOG.md #"The documentation surface was synchronized for the 0.0.8 cycle"` cites `[spec-027-filters-0_0_8.md][spec-filters]` and `[spec-028-orders-0_0_8.md][spec-orders]` **for exactly that purpose**, with the two link definitions live in the bottom block. "Condensed" is also no longer descriptive: 100,289 bytes / 437 lines. **`AGENTS.md` rule 21 closes `CHANGELOG.md` to this cycle**, so the reconciliation happens in the spec and the changelog's own state is a maintainer follow-up, not a fix | the `0.0.8` changelog entry |
| D10 | `## Scope` 6: "Completed design-doc content is folded into durable docs, while remaining specs preserve design history and follow-up work." | **True in substance, and now under-described by a whole convention layer.** The fold-in target set is pinned (`AGENTS.md` rule 26: `docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, in the completing spec's Slice 5), and "remaining specs preserve design history" has become an explicit two-file split — the spec carries the contract, a `-rationale.md` sibling carries the deliberation (`BUILD.md` `## Spec rationale extraction`). **This cycle is itself an instance of the mechanism the sentence predates** | `AGENTS.md` rule 26; `BUILD.md` |
| D11 | `## Other` final bullet: "Future in-flight design docs use the `docs/spec-<NNN>-<topic>-<0_0_X>.md` convention (NNN matches the KANBAN card number; see `docs/builder/BUILD.md` **"Spec filename pattern"**), then get folded into durable docs when shipped." | **A borrowed claim, stale in two ways.** (a) The cited heading does not exist: `BUILD.md`'s heading is `## Spec and build-plan filename pattern` — a dangling title citation, invisible to `check_spec_glossary`, which validates glossary anchors and not section titles. (b) The lifecycle now has a second half the bullet stops short of: a completed spec is **archived** to `docs/SPECS/` with its `-terms.csv` / `-rationale.md` companions to `docs/SPECS/appx/`, by the *next* spec's author at `docs/SPECS/NEXT.md` Step 8 — never at the completing spec's own merge. The owners are `AGENTS.md` rule 26 and `BUILD.md`; under `## The single-ownership law` clause 1 spec-007 is the borrower | `AGENTS.md` rule 26; `NEXT.md` Step 8 |
| D12 | `## Other` bullets 1-2 + `## Scope`: the whole document is written in the **present tense** about a documentation state as of 2026-05-08 | Every `## Scope` row is an accurate record of what card 7 *did*, and five of six are false as statements about *now* (D5-D10). A reader cannot tell from the file which tense it means. The card body has the same property and is **left alone** — a Done card's `Scope` is a record — but the spec is a contract a reader is invited to trust as current | the card itself |
| D13 | Document structure: `## Card snapshot` / `## Planning note` / `## Scope` / `## Other` | The spec claims to "preserve the card scope from the Kanban database", and its `## Other` heading **flattens four distinct card sections into one undifferentiated list**: `Why it matters` ×1, `Files likely touched` ×5, `Note` ×2. A reader cannot recover which bullet was which, and the five `Files likely touched` rows read as scope commitments rather than as the file list they are | the stub renderer |
| D14 | `## Scope` 4: "`docs/TREE.md` is the detailed layout/test-tree reference." | **The only claim entirely true at HEAD**, and the one with a provenance the spec cannot know: `docs/TREE.md` is now **script-generated** by `scripts/build_tree_md.py` from module docstrings plus the kanban DB's predicted-path rows, so a missing module docstring fails the render and hand edits are clobbered. Its role is unchanged; who writes it is not | the TREE generator |

**Corrections to this table, appended by Worker 0 at the close of R1 (2026-08-14).** Worker 1 re-verified every row against source, the DB, and `git show` rather than trusting the table, as its dispatch required, and returned five corrections. Each was re-verified by Worker 0 before being written here. The table above stands except as follows:

- **`231911a8` is the version cut, not the card's work.** It touched **two** files (`CHANGELOG.md`, `KANBAN.md`). The card's actual documentation work is `4b8dce07` / `83c25963` / `3a4d40b7`. Every row citing `231911a8` for the *shipped doc state* should read those three; the `git show 231911a8:docs/…` readings in D5 / D7 / D8 remain valid as **state at the release commit**, which is what they were used for.
- **D4's mechanism is wrong, and the row is weaker than stated.** `1592bb90` **retained** `Card.planning_note`; what it did was clear the value `"shipped"` → `""` in that same commit. No model was dropped behind the section. The drift is a stale rendered value, not a retired field.
- **D13's mechanism and attribution are wrong, and the corrected finding is stronger.** At `81e4704d` card 7 had exactly two sections, `Scope` and `Other`, so the spec's structure flattened nothing — it was faithful when written. The four-way taxonomy (`Why it matters` / `Files likely touched` / `Note`) arrived 2026-07-20 (`0c08204f` / `ac7cc6a4` / `4f68d3f2`, kanban migration 0016). The correct finding: **the spec's `## Other` heading names a card section that no longer exists in the DB** — `grep -c '^#### Other$' KANBAN.md` → 0.
- **"three-minute" has three surfaces, not two:** the spec, `KANBAN.md`, and the `KANBAN.html` payload. D6's substance is unaffected; the count was wrong.
- **The stub population is seven specs, not three:** 007, 011, 012, 013, 016, 024, 026. This strengthens `### What R1 inherits`' precedent argument — the stub is a well-established pattern, not a three-off.

**An eighth correction, to D6, found by Worker 3 at R3's review (2026-08-14) and verified before being written here — the most substantive of the eight.** D6 says "three-minute path" names no section anywhere in the repository. That is true **at HEAD** and false as history: `docs/README.md` carried a literal `## Three-minute path` heading with a five-step body, **added at `83c25963` and deleted at `3a4d40b7` — both card 7's own documentation commits, both 2026-05-05**, before the `0.0.4` release. So the card wrote the section, named it in its own scope, and removed it again the same day; the scope bullet outlived the thing it described by **twenty-seven days** — `3a4d40b7` (2026-05-05) to `81e4704d` (2026-06-01), the spec path's first appearance in history, already carrying the bullet. (The interval was first written here as "three months", unmeasured, and corrected by Worker 1 at R3's apply-changes pass — this cycle's own defect class reaching the correction that documents the defect class. Recorded rather than quietly fixed, for that reason.) D6's *conclusion* stands unchanged (the phrase names nothing at HEAD, and the reconciliation that deleted it was right), but the row's implied history — that the phrase was always aspirational — is wrong, and the true history is a **fifth distinct falsification mechanism**, sharper than the four the rationale already records. Verified by `git show 83c25963:docs/README.md`, `git show 3a4d40b7 -- docs/README.md`, and `git merge-base --is-ancestor 83c25963 HEAD`.

**A sixth correction, this one to Worker 0's own D8 row, found by Worker 3 at R1's review (2026-08-14) and re-verified before being written here.** D8 says HEAD's `docs/GLOSSARY.md` "tables are the `## Index` (Entry \| Status) and `## Browse by category`". There is **one** table: `## Index`. `## Browse by category` is a bulleted list of category groupings, not a table. D8's conclusion — that the four-column `## Quick comparison` table is gone — is unaffected and independently verified (`grep` for it across HEAD returns nothing). Recorded here so the error is not propagated a second time; R1's rationale inherited it unchecked and R3 caught it there too.

**A seventh correction, to this plan's own `### What R1 inherits`, routed by Worker 1 at R1's second apply-changes pass and verified before being written here.** That section opens "Spec-007 is the **smallest spec in the repository**". It is **fifth smallest** of the 56 tracked `docs/SPECS/spec-*.md`, behind spec-024 (1,618 bytes), spec-012 (1,651), spec-013 (1,669), and spec-011 (1,797). Worker 0 wrote the false superlative, R1 propagated it into the durable rationale unchecked, and R1's own later `### The preamble` entry contradicted it 77 lines further down — the same propagation shape as the D8 error. **The section's argument is unaffected and stands**: what it needs is that spec-007 is a card-snapshot stub among the repository's smallest, which is true and is now how both files put it. **Both plan sites are now corrected in place** (this section's opener and the `## This is a residual-completion cycle` preamble), each pointing back here — a false claim left standing in the plan is a trap for the R2 and R3 passes that read it as input, and the propagation stays on the record in this correction rather than in the sentence that caused it.

**Two further observations from R1's final verification, recorded rather than actioned.** Neither is a correction and neither blocks anything. (a) The sixth and seventh corrections were originally written out of order in this section; reordered. (b) This plan carries raw `path:NN` references, and `AGENTS.md` rule 27 exempts per-cycle `docs/builder/bld-*.md` scratchpads but does **not** name `build-*.md` plans. Six committed plans do the same, so it is a standing-doc question for the maintainer — whether the exemption's list should name the plan file alongside the artifacts — not a defect of this cycle.

Two things this table deliberately does **not** say. First, that every row must change the spec: some rows are the spec being *superseded* rather than *wrong* (D10, D14), and D2 is the spec being *right* — Worker 1 decides per row whether the contract is restated, pointed elsewhere, or dropped to the rationale. Second, that the list is exhaustive; it is Worker 0's verified floor, and R2 owns the full sweep.

**The scope trap specific to this spec.** Spec-007's subject is *the state of five documentation files*, and every one of them moves. The pull is therefore toward rewriting the spec as a current inventory of what `README.md` / `docs/README.md` / `docs/GLOSSARY.md` / `docs/TREE.md` / `CHANGELOG.md` contain today — which would guarantee this same cycle has to run again at `0.1.0`, and would make the spec a fifth copy of a map whose owner is `README.md`'s `## Project documentation` section. The durable contribution of a shipped docs-consolidation card is the **division of responsibility it established** — which document answers which question, and why the answers are not duplicated — not the table of contents each document had on the day it shipped.

### The read-only correctness audit — findings

The maintainer's instruction "MAKE SURE NOTHING WAS SKIPPED IN THE CODE" has an unusually narrow reading for this card, because **spec-007 shipped no code**. `git show --stat 231911a8` and the card's own `Files likely touched` rows agree on five Markdown files. So the audit ran against what the card actually shipped — the documentation set — plus the package-source sweep needed to prove the card left no residue there. **No defect found in package source.**

- **No source, test, or example file references anything this card owns.** `grep -rn 'three-minute' django_strawberry_framework/ tests/ examples/` → zero hits; the `TODO(spec-007` / `TODO-<MILESTONE>-007` sweep is empty tree-wide. Nothing was staged and left unshipped.
- **The documentation map is intact and every link resolves.** `README.md`'s `## Project documentation` lists eight documents; all eight exist, and the reference-style definitions resolve on disk. The four documents `## Scope` names all exist and all still hold the *role* the card assigned them — what has moved is the *content* of two (D5, D8) and the *provenance* of two (D8, D14).
- **Two falsified statements in standing documentation, both outside this cycle's writable set.** (1) `CHANGELOG.md` relies on design-doc pointers for `0.0.8` release context (D9), which the card's own scope says it would not — closed to this cycle by `AGENTS.md` rule 21. (2) `KANBAN.md:4794`'s card row carries the "three-minute path" phrase that names no section (D6) — generated from a Done card's `CardItem`, where it is a correct historical record, so **not** drift to fix. Both are recorded for the maintainer in the deferred-work catalog; neither becomes an edit here.
- **The `0.0.4` changelog entry names a wider doc set than the spec does.** `CHANGELOG.md #"User-facing docs were consolidated into code-first onboarding"` names five categories — "code-first onboarding, a current feature catalog, architecture notes, testing guidance, and review/inspection documentation" — against the spec's four files plus `CHANGELOG.md`. At `231911a8` the docs tree was `docs/FEATURES.md`, `docs/README.md`, `docs/TREE.md`, `docs/feedback.md`, and `docs/review/`. So "architecture notes" and "testing guidance" were sections inside those files rather than files of their own, and `docs/review/` is the review/inspection documentation. Consistent, not contradictory — recorded so no pass reads the changelog entry as evidence of a missing deliverable.

One observation recorded so R2 does not mistake it for drift to "fix": **the card body is a faithful record and stays untouched.** Every one of card 7's fourteen `CardItem` rows is `is_complete = True` and every one accurately describes what the card did in May 2026. The spec's problem is that it presents the same sentences as a *current* contract. The fix is therefore entirely inside the spec file, and the divergence it creates from the card body is correct and intended — a Done card records history, a spec states the contract that holds.

### Every reference TO spec-007 (verified by grep, 2026-08-14)

The archive already landed, so this table is R3's **verification** list, not a rewrite list. R3 re-runs the sweep rather than trusting it.

| Location | Current text | Status |
|---|---|---|
| `KANBAN.md:140`, `:4783` (+ the corresponding `KANBAN.html` payload) | `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` | **Generated** — already correct; never hand-edit |
| `examples/fakeshop/db.sqlite3` (`SpecDoc.path`) | `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` | Already the archived path; no repoint |
| `docs/SPECS/appx/spec-007-…-terms.csv` | one row, `optimizer behavior,djangooptimizerextension` | Importable (one row per anchor); anchor resolves in `docs/GLOSSARY.md` |

**A fourth surface for D11's dangling citation, found by Worker 1 at R1 and verified by Worker 0:** `CONTRIBUTING.md #"Spec filename pattern"` carries the same citation of a `BUILD.md` heading that no longer exists. `CONTRIBUTING.md` is **outside this cycle's writable set** (it is not in the plan's writable list and spec-007 does not own it), so this is a maintainer follow-up recorded in R3's deferred-work catalog, not an edit. It does mean D11's fix in the spec cannot be described as retiring the last stale copy.

**No sibling spec references spec-007 at all** — no hit in any `docs/SPECS/*.md`, nor in `CHANGELOG.md`, `README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `START.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`, `BACKLOG.md`, or any package source or test file. This is the first residual cycle with a **zero inbound-reference graph**, which is why `## The single-ownership law` clause 2 has nothing to bite on here: no rewrite in R2 can break an inbound reference, and R3's three-direction sweep is correspondingly short.

**The direction this table cannot show** is the one inside the new file: R1's rationale lands at `docs/SPECS/appx/`, two levels below `docs/`, so its link definitions need `../../GLOSSARY.md` for a `docs/` target, `../../../README.md` for a root target, and `../spec-NNN-….md` for a `docs/SPECS/` sibling. The archived siblings (`docs/SPECS/appx/spec-005-…-rationale.md`) show the shape. One trap is live here: a same-named file one level up **masks** depth rot (`../README.md` from `appx/` resolves to `docs/README.md`, not the root `README.md`), and this spec's subject is precisely a set of same-named files at two depths. Disk-exists-check every rewritten path, and check *which* `README.md` each one lands on.

## Artifact list

- `docs/builder/bld-007-r1-rationale_move.md`
- `docs/builder/bld-007-r2-spec_reconciliation.md`
- `docs/builder/bld-007-r3-doc_completion_archive.md`
- `docs/builder/bld-007-final.md`

No `bld-integration.md`-equivalent: a cross-slice integration pass exists to find duplication across slices that landed source, and this cycle lands none. Its live obligations are folded in — the staged-anchor sweep (`BUILD.md` `## Cross-slice integration pass` step 6) runs in R3, and the cross-artifact read runs in the final gate.

## Checklist

- [x] R1: Spec rationale extraction into `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` (Worker 1 performs the move and authors the record; Worker 3 audits it; Worker 1 final-verifies) -> `docs/builder/bld-007-r1-rationale_move.md`
- [x] R2: Reconcile the spec with HEAD — every claim the repository falsifies is restated as the contract that actually holds, or handed to the document that now owns it; the explanation of each change lands in the rationale, never in the spec -> `docs/builder/bld-007-r2-spec_reconciliation.md`
- [x] R3: Finish the documentation and audit the archive — durable-doc audit of the shipped doc set, the three-direction cross-reference sweep, `SpecDoc.path` / terms-CSV verification, and the `TODO(spec-007` / `TODO-<MILESTONE>-007` staged-anchor sweep -> `docs/builder/bld-007-r3-doc_completion_archive.md`
- [x] Final test-run gate -> `docs/builder/bld-007-final.md`

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
