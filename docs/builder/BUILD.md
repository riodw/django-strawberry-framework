# Package build workflow

This document defines the reusable process for **building a feature from a spec doc** under `docs/spec-<NNN>-<topic>-<0_0_X>.md`. It does not track a specific build run; that lives in a per-spec plan file under `docs/builder/`.

The spec is the input contract delivered to Worker 0, not something Worker 0 invents: Worker 0 turns its slice checklist into a build plan. Worker 1 is the only worker authorized to mutate the spec, and only to reconcile pitfalls or conflicts implementation reveals.

## Spec and build-plan filename pattern

Spec files live at `docs/spec-<NNN>-<topic>-<0_0_X>.md`; build plans at `docs/builder/build-<NNN>-<topic>-<0_0_X>.md` — same segments, different directory and prefix. `<NNN>` is the 3-digit zero-padded KANBAN card number (`017` from `DONE-017-0.0.6`), `<topic>` a lowercase underscore-separated slug (`deferred_scalars`), `<0_0_X>` the target release version with dots as underscores (`0_0_6`).

NNN is the build's anchor identity: spec and build plan share it, every artifact references it, KANBAN cards link to it. DONE cards use the bare `DONE-<NNN>-<X.X.X>` form; TODO/BLOCKED cards keep the milestone prefix (`TODO-ALPHA-<NNN>`, `BLOCKED-ALPHA-<NNN>`, …) until they ship.

Example: spec `docs/spec-017-deferred_scalars-0_0_6.md` pairs with build plan `docs/builder/build-017-deferred_scalars-0_0_6.md`. Specs predating this pattern may lack the NNN/version segments; new ones use it. A spec has two tracked siblings sharing its stem: `…-terms.csv` (glossary terms) and `…-rationale.md` (the deliberative layer moved out at pre-flight — see `## Spec rationale extraction`).

!!IMPORTANT!!
Begin by reading `README.md`, `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `GOAL.md`, and the active spec file at `docs/spec-<NNN>-<topic>-<0_0_X>.md`.

!!IMPORTANT — DRY FIRST!!
Every plan, every implementation, every review pass answers one question first: **is this the maximally DRY shape that stays readable?** Duplicated logic, parallel data flows, near-copies between modules, and repeated string/key/tuple literals are all build-time defects. Worker 1 plans for DRY before code is written, Worker 3 enforces it before code is accepted, Worker 1 re-checks it across slices at the integration pass — and Worker 3's **existence challenge**, whether the abstraction should exist at all, is in scope, since the largest DRY win in this repo's history was a deletion, not a consolidation.

Standing workflow files under `docs/builder/` are tracked: `BUILD.md`, `ARTIFACT.md`, `worker-*.md`. Per-build plans and artifacts (`build-*.md`, `bld-*.md`) are tracked only for the active cycle and start from a clean slate; pre-flight deletes old ones. Untracked scratch paths: `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/`.

`AGENTS.md` and `START.md` still apply during build runs. Only the maintainer commits. Workers never commit, even if asked.

Standing worker instructions live beside this overview:

- [Worker 0: project manager](worker-0.md)
- [Worker 1: architect, planner, spec custodian, final QA](worker-1.md)
- [Worker 2: builder / implementer](worker-2.md)
- [Worker 3: code reviewer and DRY enforcer](worker-3.md)

## Required reading per worker

Every worker reads the standing project docs and its own role file before acting. This matrix is the single source of truth; role files reference it instead of re-listing.

| Document | W0 | W1 | W2 | W3 |
|---|---|---|---|---|
| `AGENTS.md` | yes | yes | yes | yes |
| `START.md` | yes | yes | yes | yes |
| `docs/builder/BUILD.md` | yes | yes | yes | yes |
| `docs/builder/ARTIFACT.md` | yes (reads `Status:` to drive dispatch) | yes | yes | yes |
| own role file `docs/builder/worker-<N>.md` | yes | yes | yes | yes |
| `GOAL.md` | yes | yes | — | — |
| `docs/GLOSSARY.md` | yes | yes | — | — |
| `CHANGELOG.md` | — | yes | — | — |
| `docs/TREE.md` | — | — | yes | — |
| `docs/README.md` | — | — | — | yes |
| `examples/fakeshop/test_query/README.md` | — | — | — | yes |
| active `docs/spec-<NNN>-<topic>-<0_0_X>.md` | yes | yes | yes | yes |
| active `docs/spec-<NNN>-<topic>-<0_0_X>-rationale.md` | — | yes (owns) | **never** | yes |
| active `docs/builder/build-<NNN>-<topic>-<0_0_X>.md` | yes (owns) | yes | yes | yes |
| current `docs/builder/bld-*.md` artifact | yes (read-only) | yes (owns plan + final sections) | yes (writes build reports) | yes (writes review section) |
| own `docs/builder/worker-memory/worker-N.md` | yes | yes | yes | yes |
| relevant source / tests | — | yes (read-only) | yes (writes) | yes (read-only) |
| Worker 2's diff | — | — | — | yes |

Workers never read another worker's memory file during the cycle. Adding a new standing doc is a one-line change to this table.

### Where a mechanism belongs: this document, pointed at from the role files

`BUILD.md` is the **canonical home** for every mechanism two or more roles touch. Each role file carries a pointer to the heading here plus only its own role-specific delta: what that worker performs, captures, or audits — never the mechanism, its rationale, its numbers, or an enumeration of what the canonical section covers (a pointer that lists the contents is a copy that goes stale like any other). Conversely, a role-specific procedure no other role performs belongs in that role's file and not here.

Not a style preference: three of these mechanisms drifted between documents within an hour of being written. A role file is not re-read when a mechanism changes, so a copy there goes stale silently — and a stale copy is worse than none, because a dispatcher pastes it into a spawn prompt as fact.

## The corpus ratchet: every edit names the bytes it retires

**This corpus may not grow net.** It applies to **every authorized edit** of `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, and the four `docs/builder/worker-*.md` role files — a closeout retrospective, a mid-build correction, a maintainer-approved clarification, anything. It is not scoped to retrospectives; scoping it that way is the loophole that grew this corpus 69% in a single pass.

- **Name the bytes retired.** Every addition names the paragraph, bullet, or section it replaces, subsumes, or makes redundant, and states the **before-and-after byte count** for each file touched, summed across all six files. The total must not rise.
- **Bytes, not lines, are the gate.** Dense prose is how a document grows without adding lines: a bullet re-worded into three clauses adds cost and no line. Line counts cannot see that; `wc -c` can.
- **If nothing can be retired, the lesson does not land here.** Carry it to the maintainer as a proposal with the trade-off stated.
- **The cheapest retirement is usually a duplicate** — the same lesson narrated here and again in two role files. Collapse it to one canonical telling plus pointers (`### Where a mechanism belongs: this document, pointed at from the role files`) and the addition pays for itself.
- The reason is not tidiness. This corpus is re-read in full on every subagent spawn, so its length is a per-spawn cost paid by every worker in every future build. A document that grows without bound gets skimmed, and **a skimmed rule is worse than no rule, because it looks like evidence that the question was examined.**

## Pre-flight checks

Pre-flight **gates plan creation**: Worker 0 runs it before creating `docs/builder/build-<NNN>-<topic>-<0_0_X>.md` and records the outcome in the plan's preamble. Its seven steps are Worker-0-only procedure and live in `worker-0.md` `## Pre-flight procedure`. No slice is dispatched until step 7, Worker 1's spec-rationale extraction, is done and verified, because every spawn after it reads the smaller spec (`## Spec rationale extraction`).

### Tracked binary / generated files: churn and concurrent-writer handling

This repo tracks binary and generated files a concurrent maintainer process (or a build's own test/regenerate runs) can rewrite mid-build — `examples/fakeshop/db.sqlite3`, `KANBAN.md` / `KANBAN.html`, `docs/GLOSSARY.md`, any rendered-from-DB doc. `git status` reporting one dirty does **not** by itself mean a worker caused it, and a same-size binary diff (`Bin N -> N bytes, 0 insertions, 0 deletions`) is **not** proof of a no-op — git does not line-diff binaries.

- **At pre-flight,** note in the build plan which tracked binary/generated files are concurrent-writable, so later passes do not mistake their churn for build output.
- **Diff the SEMANTIC content before treating churn as revertible tool-drift.** For a SQLite DB compare the `iterdump()` (schema + rows), not the file bytes; for a generated doc compare against a fresh regenerate. A genuine no-op (page churn from a read-only open) is safe to leave; a semantic change is either the slice's intended output or a concurrent writer's work.
- **Never blind-`git checkout` a tracked binary/generated file as "tool drift."** If the semantic diff shows a concurrent writer's in-progress work, treat it as out-of-scope per `AGENTS.md` rule 34 — record it in the baseline-dirty list and **do not revert it** (reverting clobbers their work, and they may re-apply it, churning the build repeatedly). Revert only when the semantic diff confirms it is the build's own throwaway churn on a slice with no intended change to that file.
- **DB-backed slices that legitimately diverge the DB from HEAD** (a kanban card move, a glossary regenerate) cannot verify via "`git diff <generated doc>` is clean". Verify instead by **two-consecutive-regenerate byte-stability** plus spot-checks of the rendered result. With a concurrent writer active on the same DB, apply the slice's writes **on top** without reverting the concurrent state, and hand the mixed diff to the maintainer to reconcile at commit.

## Spec rationale extraction

**The first substantive action of every build.** Before the build plan is written, Worker 1 MOVES the spec's *deliberative layer* into a companion file, `docs/spec-<NNN>-<topic>-<0_0_X>-rationale.md`. It is a cut-and-paste, not a copy and not a summary: text that lands in the rationale file leaves the spec.

Why: the deliberative layer is the largest thing in a spec and the least useful during implementation. On `spec-046`, `## Architectural decisions` alone was 118,013 bytes — **48% of a 247KB spec** — and specs here run to 342KB. Every worker spawn reads the active spec, so broadcasting the deliberation multiplies its cost by the spawn count, while a builder implementing one rejection path needs none of it. It IS needed later, to check the finished implementation against the reasoning that produced it — hence a move, not a deletion.

**The spec stays the heart, and it never narrates its own history.** When a review round changes a decision, the custodian **rewrites that decision to state the corrected contract directly** — no amendment block, no retraction paragraph, no "as of review round N" hedge. The spec reads as a clean current contract, as though it had been right from the start; a reader must never reconstruct what is currently true by applying a chronology to it. What changed, when, why, and what was rejected live in the rationale file. That is the difference between a contract and a changelog, and the spec is the contract.

Worker 1 is the only role that performs the move, so what moves, what stays, and the mechanics of performing it live in `worker-1.md` `### Performing the rationale move`. One rule is not the mover's but the reader's, and stays here:

**The rationale file is keyed to the spec, so it works as a review instrument rather than an archive.** Every entry names the spec decision it belongs to by heading and anchor, and carries for that decision: the alternatives rejected and why each lost; every change the decision has undergone, with the round that caused it; and any claim the decision once made and may no longer make. Worker 3 checks the finished implementation against these entries and Worker 1 audits them at final verification — an entry naming no decision cannot be looked up, and is worthless however well argued.

### Who reads it, and when

- **Worker 2 never reads it.** That is the point of the move.
- **Worker 3 reads it during review** — it stops a reviewer re-raising a rejected alternative, and it is the reasoning the finished implementation is checked against.
- **Worker 1 reads and owns both files**, as spec custodian and at final verification.
- **Worker 0** carries the correct file into each spawn prompt, and never sends the rationale file to a builder.

## Versioned build plan

Worker 0 is **handed** the active spec at the start of the cycle and derives the plan from it; it never writes the spec. Read the spec, take its topic slug and target release version (dots to underscores — version-bump correctness is the maintainer's responsibility), and create `docs/builder/build-<NNN>-<topic>-<0_0_X>.md`. That file is the canonical checklist for the whole build and is committed alongside the implementation changes.

If the spec is missing, malformed, or its slice checklist cannot be parsed, stop and record the mismatch in the plan before any slice work starts.

## Build scope

The build covers every slice in the spec's "Slice checklist", in declared order. The plan mirrors that checklist, one cycle per slice, plus a cross-slice integration pass and a final test-run gate.

- Build only one slice at a time. **Spec slices** are sequentially dependent by construction — a later slice builds on the surface an earlier one lands. `### Parallel cohorts under a declared ownership partition` is the one licensed exception.
- Do not start the next slice until the current one's plan/build/review/verification/spec-reconciliation cycle is complete.
- After all in-spec slices are built, Worker 1 runs the cross-slice **integration pass** (which may trigger a second-loop refactor through Workers 2 and 3 if DRY opportunities appear).
- The build closes with one final test-run gate, handled by Worker 1.

### Parallel cohorts under a declared ownership partition

Strict serialization is the right default for spec slices and the wrong default for everything else. When work decomposes into cohorts whose **file ownership is provably disjoint** — a review round's findings, an integration-pass consolidation across unrelated modules — serializing them costs wall-clock for no quality gain. A prior cycle ran three builder cohorts concurrently with zero collisions; a fourth waited only because it shared one test file.

What licenses concurrent dispatch is the **ownership partition**: Worker 0's declared mapping of every file the cohorts will write to exactly one cohort.

- Worker 0 declares it **in the build plan, before dispatch** (see `## Required plan structure`). An undeclared partition is not a partition — dispatch sequentially.
- Every file any cohort will write (source, tests, docs, its own artifact) appears in exactly one cohort's list. Files no cohort writes are not listed.
- **Any file owned by two cohorts serializes them.** Cohorts with entirely disjoint production files that both re-pin assertions in one shared test file run in sequence. One shared file is enough; overlap size does not matter.
- Each cohort still runs the full worker cycle (plan → build → review → final verification) on its own artifact. Concurrency changes the dispatch order, never the cycle, and never `### Isolation is non-waivable`.
- Spec slices stay sequential unless the spec proves two slices touch disjoint files **and** neither consumes the other's surface. Ordinarily a later slice consumes an earlier one's surface, so the default holds.
- If a collision surfaces mid-flight (a cohort needs to write a file it does not own), Worker 0 stops that cohort, folds the file into the owning cohort's scope or re-partitions, and records the correction in the plan. A worker never silently writes outside its cohort's ownership.

### Procedural-closure slices

When a slice's spec contract is to ship nothing in this card ("carried by sibling" because a dependent card ships first, or a slice the spec explicitly defers), close it via a single Worker 1 pass that sets `Status: final-accepted` directly — no Worker 2 build, no Worker 3 review. The artifact carries one combined Plan + Final-verification block citing the spec clause that authorizes the closure. Worker 0 dispatches Worker 1 once with explicit procedural-closure framing.

### Generated docs are DB-backed: edit the DB, then regenerate

`KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are **generated** from the kanban/glossary tables in `examples/fakeshop/db.sqlite3` (by `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`, `scripts/build_glossary_md.py`), not hand-authored source. When a spec slice says "edit `KANBAN.md`" or "flip `docs/GLOSSARY.md`", it means **edit the DB via the Django ORM, then regenerate** — never hand-edit the rendered markdown (the next regenerate silently reverts a hand-edit, and a raw SQL insert skips the `post_save` side-row the render needs). Plan and build such a slice accordingly. The full DB-backed procedure (DONE-card invariants, `import_spec_terms`, the terms-CSV anchor rule, byte-clean-regenerate verification) lives in [worker-0.md](worker-0.md) "Closing out a kanban card".

## Review rounds

A **review round** is a cycle whose input is a maintainer adversarial review of **already-built** (possibly already-committed) work — typically delivered as the maintainer's incoming review document — rather than a slice from the spec's `## Slice checklist`. Rounds are normal, not exceptional: one prior build ran **nine**. Each was improvised because this document knew only spec slices, and the artifact template and `Status:` chain fell away as a direct result. They do not fall away: a round runs the same worker cycle, the same artifact contract, and the same final gate as a spec slice.

### The review document is evidence, not contract

- **No worker ever edits the review document** — not to tick findings, not to annotate, not to record disagreement. It is the maintainer's artifact.
- **Decisions live in the spec** (see `## Spec reconciliation`). A finding the round accepts becomes a spec amendment authored by Worker 1; the spec, not the review, is what the next reader must be able to trust.
- Findings tracked as work live in the round's `bld-review-*.md` artifact.

### Worker 0 verifies every finding against source before dispatching

**An incoming review can itself be wrong, and following it verbatim can cause the defect.** One review's own prescribed remediation said to preserve body bytes "in the request shape Django expects", which reads as assigning `request._body` — and doing so **disables Django's `DATA_UPLOAD_MAX_MEMORY_SIZE`**. A live test row flipping 400 → 200 proved it. That review was the source of a regression, not the cure for one.

So before any builder is dispatched, Worker 0 reads the current source behind every finding and records, per finding:

- whether the described condition actually holds at HEAD, citing the symbol-qualified path (`AGENTS.md` "Source references in docs and code comments");
- whether the review's **prescribed remediation** holds. A finding can be real while its prescribed fix is wrong. A prescribed fix is a hypothesis, never an instruction;
- for a finding that does not hold, the evidence that it does not — reported to the maintainer rather than quietly dropped. It still matters: it says the maintainer's model of the code is off somewhere.

### Contract-level findings are escalated as maintainer decisions before dispatch

- a **defect against an existing contract** — the code does not do what the spec, docs, or tests say. Workers fix these.
- a **contract-level finding** — the answer turns on which contract the package *should* offer (whether a consumer seam is supported at all, whether a stricter default is a breaking change, whether an abstraction should exist). **Not a worker's call.**

Worker 0 escalates every contract-level finding to the maintainer as a decision **before** builders are dispatched, and records in the round artifact the decision made and the **rejected alternatives, each with its reason**. The rejected alternatives are load-bearing: the next reader's first instinct will be the alternative, and only the recorded reason stops the round being re-fought.

### Dispatched findings checklist

A round has no `## Slice checklist` to copy from, so its artifact carries a **`### Dispatched findings checklist`** in the `## Plan (Worker 1)` section, in the position and under the tick-and-audit discipline `### Spec slice checklist (verbatim)` holds for a spec slice. This is the canonical name; all four role files use it verbatim.

- **Worker 1 writes it** at plan time: one `- [ ]` box per finding dispatched to this cohort, quoting the finding as the review stated it and citing the symbol-qualified path Worker 0's verification pass recorded (`### Worker 0 verifies every finding against source before dispatching`). Every dispatched finding appears in exactly one cohort's list, mirroring the ownership partition. Boxes stay `- [ ]` at planning.
- **Worker 2 ticks `- [x]`** only a box whose fix actually landed in its diff this pass, and states any deferral in the build report rather than ticking.
- **Worker 3 walks the list** during review. A box the diff does not address with no recorded deferral is a Medium finding; a box ticked with no matching fix is likewise. The round-specific checks in `worker-3.md` "Review-round duties" apply on top.
- **Worker 1 audits every tick at final verification**, exactly as for `### Spec slice checklist (verbatim)`: un-tick and set `revision-needed` for an over-tick, tick a landed box Worker 2 left open, record a one-line deferral reason for anything still `- [ ]`.

A maintainer decision the round escalated is not a checklist box — it becomes a numbered spec Decision authored by Worker 1 (`worker-1.md` "Review-round custody").

### Cohorting, naming, and closure

- **Cohort findings by ownership partition, not by severity.** Group findings by the files their fix and their tests touch, then apply `### Parallel cohorts under a declared ownership partition`. Severity grouping feels natural and is the wrong axis: the tests for several findings of unrelated severity frequently live in one file, and that file's ownership decides whether two groups can run concurrently.
- **Artifact naming:** `## Build artifact naming` gives the path; one artifact per cohort of the round's ownership partition. The `Status:` chain and the [ARTIFACT.md](ARTIFACT.md) template apply **unchanged**, failability-proof and hot-path-budget subsections included.
- **Spec amendments stay custodian-only.** Every builder writes its required-spec-amendment list **into its artifact on disk** under `### Notes for Worker 1 (spec reconciliation)`, not only into its return report to Worker 0. Detail living only in a subagent's report does not reach the next worker: in one round two builders' amendment lists never landed on disk and the custodian had to re-derive all of them. The template already provides the section; the failure was not using it.
- **Closure:** a round closes with a Worker 3 pass over the round's whole diff and the full `## Final test-run gate` (including `## Floor verification` where it applies), then hands to the maintainer. A round that skips the gate is not closed.
- **Pre-flight for a round** runs every step of `worker-0.md` `## Pre-flight procedure` **except** step 3's artifact reset — the prior cycle's `bld-*.md` artifacts are the record of the work now under review and must survive. Verify only that the round's own new `bld-review-*.md` paths do not already exist.

## Coverage is the maintainer's gate, not a worker's tool

Workers do not run `pytest` with coverage flags. `--cov=...`, `--cov-report=...`, `--cov-config=...`, and equivalents are forbidden in every worker pass — planning, build, apply-changes, review, re-review, final verification, integration, and the final gate. `--no-cov` is the only permitted coverage-shaped flag: it opts OUT entirely rather than configuring coverage, and is required because `pytest.ini`'s `addopts` auto-applies `--cov`.

Coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`) and the maintainer's. Missing test branches are caught by comparing the diff against the spec — "Decision 4 says X must be rejected; is there a test that asserts X is rejected?" — not by running coverage. If gap-discovery feels intractable, escalate to the maintainer rather than running coverage.

**Coverage output is also the lower-quality finding, which is why the substitute is not a concession.** "Line 325 is uncovered" never says which spec contract went unasserted; reading the diff against the spec names the contract, and a finding that names the contract is one Worker 2 can close without guessing what the assertion was supposed to prove.

Tests themselves are still in scope: Worker 1 plans which must exist, Worker 2 writes them in the same change as the code, Worker 3 verifies they exercise the right branches by reading the diff against the spec. Focused runs without coverage flags are fine anywhere they confirm pass/fail.

### Query-shape tests must pin the load-bearing property, not observability

A test that asserts only that an optimization is *observable* — an annotation is present, a column was added — does not prove it *happened*. For ORM-shape work the wire result is frequently identical whether the query was optimized or fell back to an N+1, so a wire-only or annotation-only assertion is non-distinguishing. Pin the property directly:

- **Batched/windowed/prefetch vs. N+1:** assert the **query count at two or more parent cardinalities** — equal count means batched; count scaling with cardinality means N+1. An equality-only assertion is vacuous unless paired with an **absolute** expected count (some fallback shapes are also "equal across runs"). Derive the absolute count from a real run; never guess it.
- **Right-path tests:** confirm the query under test actually exercises the intended path. An argument that silently routes a selection to a fallback (e.g. a sidecar `filter:` / `orderBy:` that disables a planned optimization) makes a "fast-path" test pass while pinning the fallback. Keep the test's query minimal so it can only take the path it claims to test.

### Example-project schema changes must sync every schema-module list

A slice that adds a new example-project app — or any new schema module — must register that module in **every** schema-module enumeration across the test trees, not only the shared reload helper. Some harnesses carry their own private hardcoded lists (cold-path `sys.modules` eviction tuples, bare-name reload loops), and one file may hold more than one such seam. An omitted module leaves its types stranded-registered across a `registry.clear()` / reload, producing an **order-dependent** `DuplicatedTypeName` / `LazyType KeyError` at the aggregate schema build. This class is **invisible below the full parallel test run** — it passes in isolation, single-worker, and any one fixed file order. So when a slice adds an app or schema module: grep the whole test tree for private schema-module lists, sync the new module into each (dependency-safe order), and re-verify with the full parallel `uv run pytest --no-cov` — never a focused run. The final gate's full sweep is the backstop; per-slice focused tests are not.

### Test staleness a focused run cannot see

Two further change shapes strand test files the slice never names, and both hide for one reason: the un-re-pinned file is not in the diff, so neither per-pass diff review nor any focused run executes it before the final gate's full sweep.

- **An example-model field/column added, removed, or renamed** breaks every test hard-coding that model's field set — package `tests/` may use real example models as fixtures — through *different* mechanisms: a stale `fields=` / `exclude=` list, an editable-column expectation, a `"__all__"` shorthand that now raises on an unfilterable column type, a dedup/identity assertion. The sweep is the full `uv run pytest tests/ --no-cov`, never a focused run, and every staleness it exposes is fixed in the same pass. The faithful fix restores the test's original intent against the model's **current** field set: never weaken an assertion to force a pass, never change production code to make a stale test green.
- **A wire-shape conversion** — a root or relation field becoming a connection, or any change to the `edges` / `node` / argument envelope a consumer query must use — must be re-pinned in **every** test tree exercising that field, not only the tree the slice text names (`AGENTS.md` defines three: package `tests/`, per-app `examples/fakeshop/apps/<app>/tests/`, live `examples/fakeshop/test_query/`). The check is `grep -rn <converted field name>` across all three.

A regression either shape introduces is the build's to fix **in-loop**: never a separate-session follow-up, never off-loaded to a task-spawning tool. Background hand-off is only for genuinely out-of-build, pre-existing-at-HEAD issues (`## Claims are proven mechanically, never accepted on prose`). A tree left stale is at minimum a Medium finding.

## Failability proofs: prove the test can fail

A passing suite is evidence only if it could have failed. Twice here it could not: once because the harness could not exhibit the failure at all (`### Harness-impossible interleavings`), and once because the defect was an expression rather than a branch, which statement coverage structurally cannot see (the fail-open-shapes section below).

A **failability proof** is the remedy: transiently mutate the production code so the boundary is gone, observe **which** test rows fail, revert, and **prove the revert by byte-comparison**. "I reverted it" in prose is not the proof; the comparison is. The procedure is one loop, run once per boundary:

```shell
grep -c '<anchor line inside the boundary>' <file>  # must print exactly 1, BEFORE the copy
uv run pytest <focused scope> --no-cov             # pre-mutation: green, or record what fails
cp <file> /tmp/dsf-proof-<slug>.orig               # scratch path OUTSIDE the repo
# apply the mutation, then:
uv run pytest <focused scope> --no-cov             # record failing node ids, errors, this scope
cp /tmp/dsf-proof-<slug>.orig <file>               # restore
cmp <file> /tmp/dsf-proof-<slug>.orig              # the proof: exit 0
```

**The anchor check is first because nothing else in the loop can tell that its own reference is already mutated.** If a prior proof, or an agent that died mid-proof, left a mutation live, then `cp` copies the *mutated* file, `cmp` passes, the record reads clean, and the boundary stays gone — precisely the `### Mutations are transient` failure, and invisible from inside the loop. A live prior mutation means the anchor is absent, so the entry aborts having written nothing.

**The scratch path must be outside the repository.** A pristine copy under `docs/builder/temp-tests/` satisfies every other word here while putting a copy of the file under proof inside the tree under proof.

The pre-mutation copy is the reference because **the tree is legitimately dirty** with this build's own work: an empty `git diff -- <file>` is therefore NOT the proof (it cannot be empty, and a boundary this build introduces has no HEAD version anyway), and `git checkout -- <file>` is never the restore — it would discard the slice. For a boundary already present at HEAD, the read-only HEAD reference in `## Claims are proven mechanically, never accepted on prose` is equally valid.

### Mechanized: `scripts/prove_failability.py`

`uv run python scripts/prove_failability.py <manifest.json>` mechanizes the loop above and is the **supported way to perform a proof**: it runs every step in order per entry and refuses the shortcuts — a target outside the repo, a scratch root inside it, a row-hiding scope (`--cov`, `-x`, `--maxfail`), a label whose leading path is not the target, an anchor matching other than exactly once; `--help` carries the complete list, which this sentence deliberately does not chase — never invokes `git`, names a live mutation in `ACTIVE-MUTATION.json`, and emits a `### Failability proofs` block with every measured field filled in — the pre-mutation baseline included, since it runs one by default — leaving by hand only the **why 0** judgement on a zero-row entry, emitted as a `why 0: <fill in — …>` placeholder. **`--help` and its module docstring own the manifest schema and every flag**; this document does not restate them. Manifest home: `docs/builder/temp-tests/<slice>/proofs.json`, cleared per cycle by `scripts/clean_up.py`.

Exit codes: **`0`** every entry proved, none weakly pinned; **`1`** weakly pinned, an entry error (an anchor matching zero or many times included), a collection/setup error (so the count is not a valid count at all), an unusable manifest, or `--output` asked for without a baseline; **`3`** a restore could not be proved — the tree may still hold a mutation, so read the marker the run left behind before anything else; the partial report is still written to `--output`. `scripts/` sits outside the coverage gate, so using it adds no coverage obligation.

The fenced loop stays the fallback: a worker must still know what the tool does.

### What needs a proof, and what does not

Required for every **new boundary, guard, gate, or rejection path** a slice introduces — anything whose job is to say "no", hold an invariant, or fail closed. **Not** required for every changed line: renamed symbols, relocated bodies, added annotations, doc edits, and refactors that move existing behavior need none (their own proof rule is `## Claims are proven mechanically, never accepted on prose`). Keep the obligation scoped to boundaries, or it becomes unaffordable and gets skipped.

### Who performs it

**Worker 2 performs and records the proof; Worker 3 audits every record and independently re-runs a subset.** This division is settled — two agents have already argued each half is redundant. Neither is.

- **Worker 2's obligation is mandatory, not sampled.** Every new boundary the pass introduces carries a proof in the build report's `### Failability proofs` subsection. Not redundant: in the most recent round the builder's own self-proof is what discovered the harness-impossible interleaving below — which the reviewer never saw, precisely because the builder found and closed it first.
- **Worker 3 audits every recorded proof and independently re-runs a subset — not all of them.** `worker-3.md` "Reading is necessary, not sufficient" sets the **mandatory floor** on that subset; above it, Worker 3 re-runs whatever it distrusts. The re-run is not redundant either: it is performed by an agent with **no memory of why the test was written that way**, the only vantage point from which a self-convincing proof looks thin. Subset-not-all is the cost control — proving every boundary twice is what would make this unaffordable.
- **Worker 3's narrow source carve-out stands** (`worker-3.md` "Scope"): record the mutation in the artifact before making it, revert it inside the same pass, prove the revert by byte-comparison. It exists so the independent re-run is possible, and licenses no other source edit.
- A missing, unconvincing, or unreverted proof is `revision-needed`, set by Worker 3.
- Worker 3 may still write a temp test under `docs/builder/temp-tests/<slice>/` to demonstrate that an existing assertion is non-distinguishing.

### Mutations are transient

A mutation is deliberately broken production code sitting in the working tree. An agent that dies mid-proof leaves it there, and the next worker inherits a repo whose boundary is missing on purpose.

- Keep each proof **narrow** — one boundary, one mutation.
- **Revert before moving to the next proof**, not at the end of the pass.
- Never leave a mutation in place across a `Status:` transition, and never hand a mutated tree to Worker 3.

### What gets recorded

Per new boundary, in the build report's `### Failability proofs` subsection:

- the boundary, by symbol-qualified path;
- the **exact mutation applied** — what was deleted, inverted, or weakened. A mutation must remove the boundary, not merely perturb code near it;
- the **failing test node ids, listed**, plus the **focused scope as run**. Not a count: the count is `len()` of the list and therefore auditable rather than asserted. A bare count rots — the tool re-measured seven boundaries at identical scope and **four** disagreed with the reviewer's recorded counts, purely because rows had landed in between, and only a node-id set difference distinguishes "better pinned now" from "different scope" or "someone measured wrong";
- the **collection / setup error count, separately.** Rows that never ran cannot fail, so a mutation that collection-errors a module reports few or **0** failures and grades weakly pinned when it was in fact catastrophic — the direction of the corruption is fail-open. It has happened: "2 failures + 8 collection errors" for a dropped `csrf_exempt` on `as_view`, recorded in ad-hoc prose because no slot existed. **A proof carrying collection or setup errors is not a valid count.** Resolve the errors and re-run, or the boundary's scope was wrong;
- the **pre-mutation state of that same scope** — green, or the node-id set the mutant's is differenced against. In a tree legitimately dirty with several cohorts' work one pre-existing failing row inflates every count and can make a genuinely 0-row boundary read as pinned, which is the exact class the acceptance rule below exists to catch;
- the **revert, proved by byte-comparison** (command and result);
- on any **zero-row** result, a one-line **why 0** naming which case it is: weakly pinned (the acceptance rule below) or a harness-impossible interleaving (`### Harness-impossible interleavings`). Those two sections prescribe opposite responses to the same measurement, so a record that does not name one reads as though they contradict each other.

**A "test row" is one failing test node id under the focused scope** — a parametrized case is one row, not one per file or per assertion. Two thresholds key off the count: the weakly-pinned rule below (0 or 1) and Worker 3's mandatory re-run floor (3 or fewer, `worker-3.md` "Reading is necessary, not sufficient"). A wider scope inflates it and so silently shrinks the reviewer's mandatory subset, hence **Worker 3 re-runs at the scope Worker 2 recorded** and compares node-id sets rather than numbers.

### Acceptance rule: weakly pinned is `revision-needed`

A boundary is **weakly pinned** when removing it makes **0 or 1** test rows fail, counted as `### What gets recorded` defines a row and at the scope recorded there. Weakly pinned is not accepted:

- **0 rows fail** — nothing pins the boundary at all. The suite cannot tell whether it exists.
- **1 row fails** — the boundary rests on one assertion in one row. A single refactor, fixture change, or skip retires it silently.

Worker 3 sets `revision-needed` and names the additional rows required. The fix is more (or better-targeted) rows — never a weaker boundary, and never a recorded exception.

### Harness-impossible interleavings

Sometimes the suite passes with the boundary removed because **the harness cannot exhibit the failure at all** — a **harness-impossible interleaving**. The lock case is exactly this: `channels.testing`'s `base_send` puts onto an unbounded queue and never suspends, so the bad interleaving cannot occur in-process, while a real ASGI socket write does suspend. The lock mutant passed **every** wire-level row in that suite; each one was structurally incapable of failing, however many rows there were. Reading the diff could never have found it; only the mutation did.

A whole finding class can be invisible the same way: `WebsocketCommunicator` synthesizes no `host` header and no `scope["server"]`, so every WebSocket row in this repo had been driving handshakes with zero host information — no existing test could have caught a missing Host-validation boundary.

When a proof shows 0 rows failing and the reason is the harness rather than the tests:

- **Assert the invariant at the production call site**, not at the wire. The lock case was closed by asserting `lock.locked()` where the production code performs the send.
- **A wire-level assertion that still passes with the invariant removed is worthless.** Deleting it loses nothing; keeping it manufactures confidence. Say that in the artifact instead of adding rows to it.
- Record the harness limitation itself in the artifact. It is the reason the next reader should not trust a green run in that area either.
- Reaching for a mock is not the answer: `AGENTS.md` permits mocking only when the real path is impossible, and a call-site invariant assertion *is* the real path.

### Fail-open shapes: what `fail_under = 100` structurally cannot see

`fail_under = 100` measures **statements**. A fail-open **expression** is not a branch, so full statement coverage executes it, reports it green, and never asks what it returned. A prior round shipped

```python
remaining = max(end - position, 0)
```

in a body-size probe. When `end` and `position` were incoherent — an unmeasurable stream — the clamp turned "cannot determine the size" into `0`, which the caller read as "empty, therefore allowed". No byte was read; no bound was enforced. Every statement ran; coverage was 100%. No amount of coverage tooling could ever have seen it.

A **fail-open shape** is a syntactic form that converts "cannot determine" into "permit". Treat each of these as a suspect wherever a slice introduces or touches one:

- a **clamp** — `max(x, 0)`, `min(x, limit)` — on a value that participates in a decision;
- a **`getattr` default** standing in for an attribute whose absence is meaningful (Python 3.10's `SpooledTemporaryFile` has no `seekable` attribute at all);
- an **`or` fallback** (`value = candidate or fallback`) where the left operand can be legitimately falsy;
- a **bare `except`** (or an over-broad `except Exception`) wrapped around a check, which converts "the check blew up" into "the check passed";
- a **truthiness test on a value that can be absent**, where absent and empty mean different things;
- any default reached because the input was *incoherent* rather than *absent*.

The rule: **guard the ANSWER, not one spelling of the incoherent input.** The correct fix for the case above was

```python
remaining = end - position
if remaining <= 0:
    return None
```

so the undeterminable case exits the permit path instead of being coerced into it. Note that the reviewer's own first prescribed guard — `if end < position` — was **also insufficient**: it enumerates one shape of incoherent input and leaves the rest (`end == position` on an unmeasurable stream) flowing into the permit branch. A guard written against an input spelling is a guess; a guard written against the answer is a boundary. This is also why a review's prescribed remediation is a hypothesis and not an instruction (`## Review rounds`).

Because coverage cannot see these, they are found by **reading for the shape**: Worker 1 at plan time (do not plan one), Worker 2 at implementation time, Worker 3 at review time. A fail-open shape on a decision path is at minimum a Medium finding, and High when the decision is a security or data-isolation boundary.

## Hot-path budget

Nothing else in this process measures performance; cost is invisible to every correctness gate. One build added a per-connection serialization point on an outbound hot path — every concurrent operation on a socket now waits behind a session-store read — accepted on correctness grounds with **zero numbers captured**. That may have been the right trade. Nobody knows, because nobody measured.

A different obligation from `### Query-shape tests must pin the load-bearing property, not observability`: those are an **N+1 detector**, answering "is the work batched?" with a query count and a pass/fail. A **hot-path budget** is a *number*, before and after, for a change that adds cost to a path that runs often. A slice can hold a perfectly green query-count assertion and still have added a lock, a per-request cache read, an extra round trip, or a re-parse to every call.

- **Worker 1 declares it at plan time**, in the plan preamble (`## Required plan structure`) and per-slice where slices differ. A hot path runs per request, per resolver, per row, per connection, or per outbound message — as opposed to per process start, per schema build, or per management command.
- **Worker 2 captures a before/after number** for any slice declared hot-path, in the build report's `### Hot-path budget` subsection: what was measured, how (exact command or snippet), before, after, delta. A query count, a wall-clock median over a stated iteration count, or an added-`await` count all qualify; the metric must be stated, reproducible, and the *same* one before and after. A single-shot wall-clock reading is not a number.
- **Worker 3 verifies the number EXISTS** and is reproducible as recorded — not that it is good. A hot-path-declared slice whose build report carries no number is a Medium finding and `revision-needed`.
- **Whether the trade-off is acceptable is the maintainer's call.** No worker accepts or rejects a slice on performance grounds, and none weakens a correctness boundary to buy back a number. The obligation is only that the number exists, sits next to the change that caused it, and reaches the maintainer — so a cost is never accepted **silently**.
- If Worker 1 declares a slice **not** hot-path and Worker 2 or 3 finds otherwise, record it under `### Notes for Worker 1 (spec reconciliation)`; Worker 1 decides at final verification whether the slice re-loops for a measurement.

## Required plan structure

`docs/builder/build-<NNN>-<topic>-<0_0_X>.md` must begin with: spec source path; target release version; date created; pre-flight outcome and working-tree baseline summary; baseline-dirty out-of-scope files (workers neither edit nor revert them); build-wide context flags (e.g. joint-cut path: safe-default vs contingency; version-bump-owner card); a short copy of the one-slice-at-a-time and DRY-first rules; a list of every build artifact that will be created; and these three declarations, each either concrete or explicitly `none`:

- the **ownership partition** — the cohort-to-files mapping that licenses concurrent dispatch, or `none; sequential slices` (`### Parallel cohorts under a declared ownership partition`)
- the **hot-path declaration** — which slices touch a hot path and therefore owe a before/after number (`## Hot-path budget`)
- the **floor-verification scope** — which slices touch a Django / Strawberry / channels integration seam, the focused tests they re-run at the floor, and the pass that owns each run (`## Floor verification`)

Then a slice-level checklist. Every slice and every integration/final pass carries a checkbox (only Worker 0 marks `- [x]`, and only after Worker 1's final verification accepts it), the spec slice it implements, and the exact artifact file to create.

A fictional placeholder rendering of the whole file — preamble, artifact list, checklist — lives in `worker-0.md` `### Template shape`, the only role that writes the plan. Workers 1, 2, and 3 read the actual plan, never its template.

## Build artifact naming

Per-slice, integration, and final artifacts are tracked Markdown files under `docs/builder/` for the active cycle, committed alongside the source changes they describe, then treated as old artifacts at the next build's pre-flight cleanup. All start with `docs/builder/bld-`; `<short_slug>` is always a lowercase underscore-separated summary.

- Spec slice: `bld-slice-<N>-<short_slug>.md`, `N` the 1-indexed spec slice number, slug from the slice title.
- Review round (see `## Review rounds`): `bld-review-<R>-<short_slug>.md`, `R` the 1-indexed round number, slug from the finding cohort. One artifact per cohort of the round's ownership partition.
- Cross-slice integration pass: `docs/builder/bld-integration.md`. Final test-run gate: `docs/builder/bld-final.md`.

The build plan must list every artifact before build work starts.

## Build artifact template

Every `bld-*.md` artifact is copied from the template in **[ARTIFACT.md](ARTIFACT.md)**, which governs the `Status:` line, its per-transition ownership, and every named section Workers 1, 2, and 3 write. It is a separate file because each worker reads all ~13KB of it while needing only its own role's sections. Read it once per spawn; this document does not restate its structure. Every `###` artifact-subsection name cited here is defined there — the two exceptions, defined in this document, are `### Dispatched findings checklist` (under `## Review rounds`) and `### Deferred work catalog` (under `## Final test-run gate`).

## Severity definitions

**High** — confirmed correctness bug; spec contract violation (the build does not deliver what the spec says); API breakage against shipped `0.0.x` surface; DRY violation that will entrench duplicated logic across the package; Django ORM behavior that can return wrong data; security / data-isolation regression; crashes a normal consumer code path.

**Medium** — likely performance regression; N+1 risk or unnecessary database work; redundant implementation that should be consolidated; unclear ownership between modules introduced by the new code; brittle edge-case behavior; missing tests for important branches; repeated literal / key / tuple that should be a named constant; silently-unaddressed spec slice sub-check (a `- [ ]` item in the Plan's `### Spec slice checklist (verbatim)` with no matching implementation in the diff and no recorded deferral).

**Low** — small maintainability issues; naming clarity; minor typing/API polish; localized simplification; comments or docstrings stale or wrong but not load-bearing.

## Claims are proven mechanically, never accepted on prose

Three claim shapes move work or risk out of a build, each cheapest to wave through where it most deserves distrust. All three carry one obligation: the claimant cites its verification, the reader re-derives instead of accepting, and **an unverified claim of any of these shapes is a Medium finding.**

They share a read-only HEAD reference: `git show HEAD:<path>` into a scratch path **outside** the repo, then `diff`; quote the commands and output in the artifact. **`git stash`, `git checkout`, `git restore`, and `git worktree` are never part of verifying a claim** — the maintainer runs concurrent sessions against this same tree, so a stash round-trip races their writes and a `git checkout HEAD` can destroy uncommitted work, theirs or the build's. No verification need waives that ban.

- **Pre-existing at HEAD.** A file's content is verifiable read-only as above. A failing test or runtime behavior is **not worker-verifiable at all** — reproducing it needs the whole tree at HEAD, and this tree is legitimately dirty with the build's work and possibly a concurrent session's. Record the claim plus the evidence you have (failing node ids, traceback, HEAD content obtained read-only, whether the failing test or its code is even in the build's diff), then **escalate to the maintainer**, the only party who can run a clean HEAD tree. Recording plus escalating discharges the obligation; the Medium finding is for a claim asserted with neither.
- **Relocated, promoted, or carried over unchanged** — a body moved into a seam, a private helper renamed public "rename-only", logic called byte-identical. It is what a "no-regression" gate rests on, and "I only moved it" is the cheapest claim in the build. Prove it with an executable-token or character diff against pristine HEAD, comments and whitespace stripped and any renamed receiver normalized, then token-identity confirmed. Applies equally to a helper promotion and a cross-flavor lift, where BOTH call sites must reproduce their originals' messages and behavior byte-for-byte.
- **A stated count** — "5 rows fail", "43 boxes", "the delta is exactly the sum". A number reads as measured and every later pass treats it as measured, so a guess propagates silently, invisible to re-reading. Two failure modes recur: a **long grep phrase samples a claim's vocabulary rather than establishing its population** (the same thing spelled another way, or wrapped across a line, does not match) — so search the shortest distinctive token and count *occurrences*, not matching lines; and a count asserted in the same breath as the lesson it illustrates is routinely wrong — **measure as you write the number.** Prefer any form whose count the reader can re-derive, for the reason `### What gets recorded` gives for listing node ids rather than counting them.

## Static inspection helper: `scripts/review_inspect.py`

The helper parses the target file as text and AST only — it never imports or executes the module — so it is safe to run on files that touch Django settings, the registry, or Strawberry type creation at import time.

### When to run the helper during build

Worker 1 **must run** it during planning when the plan adds logic to any existing `.py` file of 150+ source lines, or to any file under `django_strawberry_framework/optimizer/` or `django_strawberry_framework/types/`.

Worker 3 **must run** it during review when the slice:

- adds a new `.py` file of any size, **unless** that file is a pure-class-definition module (only `class` declarations with docstrings, no logic);
- touches an existing `.py` file under `optimizer/` or `types/`;
- adds 30+ lines of new logic to any file under `django_strawberry_framework/`, or 50+ lines to any file outside it.

Either worker may skip the helper for a file whose artifact disposition will be "no review-worthy logic" (pure re-exports, single-line constants) — the skip is recorded explicitly with a short reason.

Worker 2 **may re-run** it when refreshed output would help implementation, noting shadow-file use in `### Notes for Worker 3`.

### How to run

From the repository root, one file or (with `--all`) every package `.py` recursively:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
uv run python scripts/review_inspect.py --all --output-dir docs/shadow
```

**Every build-cycle invocation must pass `--output-dir docs/shadow`.** The helper does not default to it and `--help` does not say it is required; this process does. For every other flag, run `--help` — it prints each one with its default, so this document does not restate them.

### Reading the overview

The emitted `.overview.md` sections are self-describing; read them rather than a paraphrase here. What this process adds:

- **Django / ORM markers** (executable code only; comment and string-literal mentions ignored) — **walk every entry; each needs either a one-line justification or a finding.**
- **Repeated string literals** (executable literals; docstrings excluded) — the DRY signal, and **essential at the cross-slice integration pass**, which compares this section across every shadow overview to find cross-file literals (see `## Cross-slice integration pass`).
- **Control-flow hotspots** — apply Medium-tier complexity attention to every entry.
- **Imports** — a cross-folder import is usually a structural change worth flagging.

### Output files, and why their line numbers are NOT canonical

Two files land under `docs/shadow/<stable-stem>`, gitignored and read-only — never edit or commit them: `<stem>.overview.md` (the AST overview) and `<stem>.stripped.py` (the source with `#` comments removed and every string-literal token, docstrings included, replaced by `...`).

Stripping shifts the line numbers, so they do not match the original source. Build artifacts, review feedback, and source edits cite the original via the symbol-qualified convention from `AGENTS.md` #"Source references in docs and code comments" — `path::QualifiedName`, `path::QualifiedName #"unique substring"`, or `path #"unique substring"` — never shadow-file or original-file line numbers. Raw `path:NN` refs are allowed only in per-cycle scratchpads (the worker artifacts under `docs/builder/`), where shadow line numbers may sit inline alongside the symbol identifiers for review convenience.

## Subagent dispatch and worker memory

Workers 1, 2, and 3 each run as **separate subagent invocations per cycle item**; Worker 0 stays in the main thread as project manager. The split is what makes the artifact-as-contract model work: the worker that reviews a build has no in-context memory of the worker that wrote it.

### Worker memory

Each worker keeps a private gitignored notebook at `docs/builder/worker-memory/worker-<N>.md` that **persists across slices within a single build** and is invisible to every other worker. Worker 0 creates the directory at plan time and seeds the four files empty after the pre-flight cleanup has deleted any prior-build memory; the next build's pre-flight clears them again.

**What a worker writes.** At the end of each cycle it appends a short entry (3-5 lines) capturing what to carry into the next. Entries are append-only; past ~50 lines the worker consolidates similar entries into one pattern observation **before** adding more. Acknowledging the cap and continuing to append is not consolidation — do the merge first.

**Isolation, both directions.** A worker reads and writes **only** its own memory file. Worker 0 reads all four at closeout for the retrospective — never during the active cycle — and never edits another worker's.

### Spawn-per-cycle dispatch

Worker 0 spawns the workers in this order per slice. Each appends to its own memory file and returns.

1. **Worker 1 (planning pass)** — writes the artifact's plan section, sets `Status: planned`.
2. **Worker 2 (build pass)** — implements the slice, appends a build report, sets `Status: built`.
3. **Worker 3 (review pass)** — reviews, appends the review section, may create temp tests under `docs/builder/temp-tests/<slice>/`, sets `Status: review-accepted` or `revision-needed`.
4. **If `revision-needed`:** Worker 0 re-spawns Worker 2 (apply-changes pass, new build report), then Worker 3 (re-review). Repeat until Worker 3 has no unresolved findings, or every remaining finding is intentionally rejected with a recorded reason.
5. **Worker 1 (final-verification pass)** — runs the slice-local checks, reconciles the spec if needed, appends the final-verification section, sets `Status: final-accepted` or `revision-needed`.
6. **Worker 0** marks the slice's checkbox `- [x]` only if Worker 1 set `final-accepted`, then appends progress to `worker-0.md`.

What every spawn prompt must carry is a mechanical checklist, and it is Worker 0's alone: `worker-0.md` `### Spawn-prompt contents`.

**No cross-worker chatter.** Subagents never message each other. All inter-worker information flows through the artifact and the diff.

### Isolation is non-waivable

Worker 2 and Worker 3 always run as separate subagent invocations — even for trivial slices, even with no High-severity findings. Combining them would let the agent that wrote the code also approve it.

### Recovery from interrupted subagent runs

If a subagent fails mid-run (transient API error, network failure, time-out), the on-disk diff and the artifact's appended sections are the record of how far it got. Worker 0 dispatches a **fresh subagent of the same role** with explicit "pick up where the prior pass left off" context: the partial artifact, the working-tree diff as authoritative, the worker's own memory file, and the original task contract. The new subagent finishes the **same** pass — no "pass N+1" suffix — and sets the appropriate `Status:`. If the diff is unsalvageable, escalate to the maintainer rather than guessing at rollback.

## Cross-slice integration pass

After every slice in the spec is checked complete, Worker 1 runs the integration pass and produces `docs/builder/bld-integration.md`. Before writing it, Worker 1 must:

1. Read every prior `docs/builder/bld-slice-*.md` artifact in slice order. No "as needed" — every artifact is required context for the cross-slice DRY scan.
2. Confirm the static inspection helper ran, or was explicitly skipped with a recorded reason, for every Python file with review-worthy logic the build touched.
3. Compare the **Repeated string literals** sections across every shadow overview. A literal in two or more files is a cross-slice DRY candidate; record it in the integration artifact.
4. Compare the **Imports** sections across every shadow overview to confirm one-way dependency direction and spot any sibling importing from outside the documented boundary.
5. Walk every accepted slice artifact's `What looks solid` and `DRY findings` sections for deferred follow-up that should land in this pass.
6. **Sweep the whole tree for staged anchors naming this build's spec OR card:** `grep -rEn 'TODO\(spec-<NNN>|TODO-(ALPHA|BETA|STABLE)-<NNN>' .` (the card-id form, e.g. `TODO-ALPHA-037-0.0.11`, also stages work). Every such anchor left in shipped source/tests/comments must be discharged by the build's end: the work it names has landed **and** the anchor was removed in the slice that shipped it (replace with non-TODO provenance such as `spec-<NNN>` / `DONE-<NNN>` where historical context helps, otherwise delete). `AGENTS.md`'s "shipped behavior folds into `docs/TREE.md` … and the staged anchor is removed in the same change that ships the slice" is standing authority even when the anchor's file was omitted from the spec's `## Slice checklist` or `## Doc updates` — a checklist that forgets a staged-anchor file does not waive the obligation. (Exclude `KANBAN.md` / `KANBAN.html` / `BACKLOG.md`, where `TODO-<MILESTONE>-<NNN>` legitimately names unshipped board cards.) Record any still-present anchor as a finding and route it to the owning slice (re-loop) before the build closes.

The pass itself checks for: duplicated helpers across slices; inconsistent naming or error handling between slices; repeated ORM/queryset patterns that should be centralized; misplaced responsibilities between modules touched by different slices; missing or too-broad exports; repeated string literals / dictionary keys / tuple shapes across slices; and whether comments now tell one coherent story across the new code.

If DRY opportunities are found, Worker 1 records them in `bld-integration.md` and asks Worker 0 to dispatch Worker 2 for a consolidation pass and Worker 3 for a review pass. Repeat until clean.

## Final test-run gate

After the integration pass is clean, Worker 1 runs the final test-run gate and produces `docs/builder/bld-final.md`.

The gate is intentionally narrow:

- `uv run pytest --no-cov` — full sweep across all three test trees per `AGENTS.md`. Plain `uv run pytest` is a coverage run in this repo and is forbidden by `## Coverage is the maintainer's gate, not a worker's tool`. The only `pytest`-side requirement is that the suite passes; do NOT inspect or assert line coverage.
- Django's own consistency checks against the example project — `uv run python examples/fakeshop/manage.py check` and `… makemigrations --check --dry-run` — which catch model/admin/url-config drift `pytest` does not.
- The lint/format/diff gate, all read-only (never `--fix`): `uv run ruff format --check .`, `uv run ruff check .`, and `git diff --check` (whitespace errors and conflict markers anywhere in the tree). Failures block `final-accepted` unless a pre-flight baseline exception was recorded in the plan's preamble.
- **Floor verification** for every slice in the plan's floor-verification scope: that slice's focused tests, re-run in an isolated floor venv. The shared `.venv` is NOT the floor. See `## Floor verification` for the procedure and what gets recorded — the gate is the backstop confirming it happened, not the owner.

Record each command's pass/fail in `bld-final.md`. On failure, re-loop through whichever slice owns the failing behavior (Worker 1 plans, Worker 0 dispatches Workers 2 and 3, Worker 1 re-runs the gate).

`bld-final.md` must also include a `### Deferred work catalog` subsection — the next spec author's reading list. Walk every per-slice and integration artifact's spec-reconciliation notes and `What looks solid` / `Notes for Worker 1` sections and surface every item explicitly deferred to a future slice, future spec, or maintainer follow-up: one bullet each with the source artifact section, the spec line that licenses the deferral (if any), and a one-line description. If nothing was deferred, write `No deferred work; the build delivered the spec end-to-end.`.

The gate closes the build cycle. Worker 0 then marks the final checkbox `- [x]`.

## Floor verification

Every command in the gate above runs in the shared `.venv`. **The shared `.venv` is not the supported floor** — it tracks the newest supported versions, so a green sweep in it proves only that the build works on a version many consumers are not running. The supported floor is Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**.

**Never state `.venv`'s own versions from memory or from a number written down in a document.** They move on every dependency bump; a floor number does not. When a pass needs to know what the shared environment carries, read it — `uv pip list` — and cite the reading.

**This section is the single canonical statement of the floor versions.** `pyproject.toml` is the **ultimate source for the dependency floor**; the exact version a floor run installs is a **policy choice recorded here**, because a lower bound is a range and a floor run needs one point in it. When the floor moves, `pyproject.toml` and this section change together and nothing else has to — the role files name this section rather than restate the numbers, per `### Where a mechanism belongs: this document, pointed at from the role files`.

**Reading a newer version's source to answer a floor question is not verification.** Neither is reasoning from a changelog or a version classifier. The floor is something you execute. Two concrete costs of conflating the two: reading 6.0.5's source to answer a 5.2.0 capability question nearly shipped an unverified async-capability claim, and Python 3.10's `SpooledTemporaryFile` lacking a `seekable` attribute — it became an `io.IOBase` subclass only in 3.11 — was caught **only** by executing at the floor.

### When it is required

Any slice touching a **Django / Strawberry / channels integration seam** re-runs its **focused** tests at the floor: request/response handling, view or ASGI plumbing, upload or body parsing, the session/auth surface, queryset or expression compilation, schema and type construction against Strawberry internals, consumer or middleware wiring. Not the full sweep — the focused scope for the seam the slice touched.

**Worker 1 declares the scope in the plan preamble and the declaration names the owning pass** — the builder pass for that slice, or Worker 1 itself. The `## Final test-run gate` is the **backstop that confirms it happened**, not a second owner: a planned floor verification no pass ran is grounds for `revision-needed`.

Slices touching none of those seams (docs, KANBAN / glossary regeneration, pure-Python helpers with no framework surface) declare `none` and skip it.

### How to build the floor venv

Build it under a scratch path outside the repo, and install with an explicit `--python`:

```shell
uv venv /tmp/dsf-floor --python 3.10
uv pip install --python /tmp/dsf-floor/bin/python -e . --group dev
uv pip install --python /tmp/dsf-floor/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'
/tmp/dsf-floor/bin/python -m pytest <focused scope> --no-cov
```

- **Never mutate the shared `.venv`.** `uv pip install` ignores `UV_PROJECT_ENVIRONMENT` and installs into `.venv` if you let it; the explicit `--python <path>` is what keeps it out. A mutated `.venv` silently changes the floor for every later pass and every concurrent session in this repo.
- The floor venv lives outside the working tree, so it needs no `.gitignore` entry. Never create it inside the repo.
- **Record the resolved versions** (`uv pip list --python /tmp/dsf-floor/bin/python`) and each focused command's pass/fail in `bld-final.md`. An unrecorded floor run is not verifiable later.
- A floor failure blocks `final-accepted` and routes back through the owning slice loop. The fix is production code that works at the floor — never a raised floor, and never a `pragma: no cover` on the divergent branch (`AGENTS.md` forbids that shortcut explicitly for interpreter-divergent bugs).

## Spec reconciliation

The spec is **input** to the build, not output. But implementation routinely reveals gaps (a Decision depending on something unstated), conflicts between Decisions, and codebase realities the spec did not anticipate.

**Only Worker 1** may mutate `docs/spec-<NNN>-<topic>-<0_0_X>.md`, and records each edit in the active artifact under `### Spec changes made (Worker 1 only)` with cited spec line(s), a one-line reason, and the slice that triggered it. Workers 0, 2, and 3 surface spec issues under `### Notes for Worker 1 (spec reconciliation)` instead; they never edit the spec. If an edit fundamentally changes the contract Worker 2 already implemented against, Worker 1 re-spawns Worker 2 for an adjustment pass before final verification.

### `## Current state`: observations stand, predictions do not

Its vintage framing licenses dated **observations** of the pre-build repo, not **predictions** about the build. A falsified observation stays — the header dates it; a falsified prediction is rewritten, since nothing dates a claim about the outcome. One bullet can carry both, so grade clause by clause. A slice-checklist box or Definition-of-done item gets none: a stale figure there is a false completion claim.

### Slice splitting

Worker 1 may also **split a planned slice into sub-slices** (e.g. `5a` / `5b`) when implementation reveals it cannot land as one coherent diff — the diff is too large for sensible review, the two halves have independent risk profiles, or one half is blocked while the other can ship. The split is a spec edit, recorded like any other. Worker 1 then returns control to Worker 0 to regenerate the plan's checklist and dispatch each sub-slice in sequence. A split costs an extra artifact and an extra full worker cycle, so reserve it for cases where the unsplit slice would harm review quality.

**Estimated new boundary count is a further trigger, independent of diff size.** Boundaries are dense — a rejection path can be three lines — so a unit can be tiny by diff and enormous by boundary. The load is the builder's, not the reviewer's: each new boundary owes a mandatory mutate / run / count-rows / revert / byte-compare loop (`## Failability proofs: prove the test can fail`) on top of the change, its tests, ruff, churn classification, a hot-path number where declared, and a floor venv where scoped. One cohort in a prior build was handed ~20 boundaries, i.e. ~20 such loops in one pass. That overload never surfaces as a refusal; it surfaces as corners cut invisibly — a proof written from memory, a revert asserted in prose, several boundaries folded into one mutation that removes only one.

As with diff size, the obligation is to **answer** the split question in writing, not to split: boundaries that cannot be separated (one guard site, or one contract making them a single decision) are one unit, and saying so while naming what makes them one is a decided answer where silence is not. Roughly five or more estimated boundaries is a useful prompt to write that answer down — prior practice, not a maintainer-set threshold, so never a gate a count of four waives. Decide before dispatch while the count is still an estimate; afterwards the only evidence the unit was too big is thin proofs, and a thin proof is indistinguishable from a boundary that was never pinned.

### Spec stays at its working location

Specs stay at `docs/spec-<NNN>-<topic>-<0_0_X>.md` after the build closes; closing a build does NOT imply archiving the spec. Live follow-up state belongs in the durable docs the spec named (`docs/GLOSSARY.md`, `KANBAN.md`, `CHANGELOG.md`).

Archival or relocation happens only when a spec's own slice checklist declares it. Then Worker 1 calls the move out in the plan as a Worker 1-owned final-verification step; Worker 2 implements the durable docs / KANBAN / changelog / release-file edits the plan names but never moves or edits the active spec; Worker 1 performs the mechanical move during final verification, recording old and new paths under `Spec changes made (Worker 1 only)`.

## Slice handoff (no maintainer pause between slices)

The build runs end-to-end without pausing for maintainer review between slices. After Worker 0 marks a slice `- [x]` (Worker 1's final-verification set the artifact to `final-accepted`), Worker 0 IMMEDIATELY dispatches the next slice's planning pass — or, if every spec slice is complete, the cross-slice integration pass. Worker 1's final-verification IS the per-slice safety net; nothing else runs between slices.

The maintainer's first touch point is after the final gate sets `bld-final.md` to `final-accepted` and Worker 0 marks the final checkbox. Worker 0 then stops driving and hands off; the maintainer reviews the whole build and commits the source changes + every `bld-*.md` artifact + spec edits + the completed plan, at their discretion. The closeout retrospective runs after that commit, not before.

If anything goes wrong mid-cycle (an unresolvable spec ambiguity, an unsalvageable diff, a stop-condition in `worker-0.md`), Worker 0 escalates immediately rather than waiting for the end of the build. The non-pause rule applies to the happy path, not to genuine blockers.

Workers also never amend, force-push, or otherwise rewrite git history.

## Closeout

Closeout is Worker-0-only, and its steps live in `worker-0.md` `## Closeout job`. Two facts belong to the process rather than the role: it runs **after** the maintainer has committed the build and supplied the build-cycle commit range (the diff scan needs the commits to exist, so closeout never runs against an uncommitted tree), and every workflow-doc edit it produces is bound by `## The corpus ratchet: every edit names the bytes it retires` exactly as any other edit is.
