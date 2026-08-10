# Build: Final test-run gate — spec-005 residual-completion cycle

Spec reference: `docs/SPECS/spec-005-django_type_contract-0_0_3.md` (whole file; the cycle's reconciled contract)
Companion: `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` (the cycle's new deliberative layer)
Build plan: `docs/builder/build-005-django_type_contract-0_0_3.md`
Status: revision-needed

## THE CYCLE IS CLOSING EARLY. IT DID NOT DELIVER THE PLAN END TO END.

**Read this paragraph before anything else in this file.** This is not the gate `docs/builder/BUILD.md` `## Final test-run gate` describes. That gate runs after every item is `final-accepted` and the integration pass is clean. Here the maintainer has committed the cycle's work at `bca1ccf1` and asked for this artifact **now**, specifically for its `### Deferred work catalog`. The cycle's real state:

| Item | Plan checkbox | Artifact `Status:` | Reality |
|---|---|---|---|
| **R1** — spec rationale extraction | `- [x]` | `final-accepted` | **Complete.** Delivered in full. |
| **R2** — spec-versus-HEAD reconciliation | `- [ ]` | **`revision-needed`** | **PAUSED with two findings open** (M6, L12). Three review rounds ran; the deliverables are done and were confirmed byte-unchanged across two consecutive passes, but the item never reached `final-accepted`. |
| **R3** — documentation completion and archive audit | `- [ ]` | **artifact never created** | **NEVER DISPATCHED.** Its entire scope is undone, **including the one authorized source change of the cycle.** |
| Final test-run gate | `- [ ]` | this file | Run early, at the maintainer's request. |

Two consequences a later reader must not lose:

- **`Status: revision-needed`, not `final-accepted`.** `docs/builder/ARTIFACT.md` gives `revision-needed` to Worker 1 when final verification rejects, and this gate cannot honestly certify a cycle with one item open and one item never run. Every gate command below passed — **the status reflects the undelivered cycle, not a failing command.**
- **The plan's remaining three checkboxes stay `- [ ]`.** `BUILD.md` gives the tick to Worker 0 and only after Worker 1 accepts. Nothing here licenses ticking R2, R3, or this gate's box.

`### Deferred work catalog` is the deliverable the maintainer asked for by name and is written to be usable by someone with no memory of this cycle: every entry states what the item is, where it came from, and what it would take to close, without requiring another file to be opened. `### Settled judgements, deliberately NOT in the catalog` is its companion, so a future reader does not reopen a decided question.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, and for the cycle's standing reason rather than a skip: `worker-1.md` `### Package-wide helper inventory before helper planning` gates *proposing helper-like logic*, and this pass proposes none. It could not be stale-by-neglect either — `git diff -- django_strawberry_framework/ tests/ | wc -l` returns **0**, so nothing under the package has moved for the whole cycle. No inventory was refreshed and none was needed.
- **Existing patterns reused.** The gate's command list is `BUILD.md` `## Final test-run gate` verbatim, in its declared order; the `### Deferred work catalog` shape is that same section's. The artifact's overall shape is the sibling residual cycle's gate, `docs/builder/bld-004-final.md`, read in full before anything here was written — **its structure only. No content was copied; spec-004 is a different spec and its twelve catalog items are not this cycle's.**
- **New helpers justified.** None; this pass writes two Markdown files and no code.
- **Duplication risk avoided.** Two live risks. **First**, a catalog assembled from the most recent artifact drops every item only an earlier one carries. This cycle's R2 is a three-round artifact whose own pass-3 block supersedes figures in its pass-1 and pass-2 blocks, so "the latest section" is not the latest truth for any figure — the catalog below is keyed by **item** and names the carrying artifact block per bullet, block by block rather than by section name alone. **Second**, and specific to this cycle: **R3 does not exist, so nothing carries R3's obligations forward.** They are itemized from the plan's `### Residual scope` and `### THE ONE SOURCE EDIT THIS CYCLE AUTHORIZES` rather than from an artifact, because there is no artifact to walk.

### Implementation steps

1. Read the required standing docs, the active spec, the active rationale, the build plan in full (drift table, both Worker-0 corrections, both new rows, the `### The 7-anchor constraint` CORRECTION, the read-only audit, the source-edit authorization with its widening note and L11 correction, and both baseline-growth records), and both closed `bld-005-*` artifacts end to end (`BUILD.md` `## Cross-slice integration pass` step 1 — no "as needed").
2. Re-derive `HEAD` and the working-tree state rather than trusting the plan or either artifact; confirm the cycle's five files landed at `bca1ccf1` and that no source, test, or `examples/` file rode with them.
3. Run every gate command in `BUILD.md` `## Final test-run gate` order and record each one's real result.
4. Own the staged-anchor sweep that R3 was to run, and publish its decomposition.
5. Record the floor-verification and hot-path dispositions written out rather than omitted.
6. Author the `### Deferred work catalog`, including R3's whole unrun scope.
7. Set `Status:` truthfully and append a memory entry.

### Test additions / updates

None. This pass lands no source and no test; the gate itself is the verification.

### Implementation discretion items

None reserved. The gate has no downstream worker, so nothing is delegable.

### Dispatched findings checklist

Spec-005 has no `## Slice checklist` and this is not a review round, so per `worker-1.md` planning step 8 the boxes below are the gate's own obligations, drawn from `BUILD.md` `## Final test-run gate`, `worker-1.md` `## Final test-run gate`, the plan's `**Baseline exception for the final test-run gate**`, and the early-closure duty this dispatch adds. Worker 1 both performs and ticks; there is no later pass to audit them, so **each box cites the evidence in this artifact that discharges it**.

- [x] The early closure is stated in the opening, and the artifact cannot be read as a clean close — the pre-`---` block above, and `Status: revision-needed`.
- [x] `uv run pytest --no-cov` run, full sweep across all three test trees, no `--cov*` flag in any other form, result recorded — `### Gate commands, in BUILD.md order` row 1; line coverage neither inspected nor asserted.
- [x] `uv run python examples/fakeshop/manage.py check` run and recorded — row 2.
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` run and recorded — row 3.
- [x] `uv run ruff format --check .` run read-only, never `--fix`, and recorded — row 4, with the standing `COM812` advisory explained beneath the table.
- [x] `uv run ruff check .` run read-only, never `--fix`, and recorded — row 5.
- [x] `git diff --check` run and recorded — row 6.
- [x] Floor verification: the plan's declared scope is `none`, so `No floor-verification scope declared.` is **written out** rather than the section silently omitted — `### Floor verification`.
- [x] Hot-path declaration `none` recorded — `### Hot-path budget`.
- [x] Failability proofs: none owed, confirmed mechanically rather than accepted from the plan — `### Failability proofs`.
- [x] **The staged-anchor sweep this cycle folded into the unrun R3 is owned here, re-measured rather than inherited from Worker 0's pre-flight, and its decomposition published** — `### Staged-anchor sweep — owned by this gate, R3 having never run`.
- [x] `### Deferred work catalog` authored from both closed artifacts **and from R3's undone scope**, keyed by item, naming the carrying block per bullet.
- [x] R2's two open findings carried with what each says and why neither touches the spec or the rationale — catalog items 1 and 2.
- [x] R3's unrun scope itemized rather than named as a lump — catalog items 3.1 through 3.5.
- [x] The two authorized-but-unmade docstring corrections carried with their exact measured content, the call-site table reproduced — catalog items 4 and 5.
- [x] Both artifacts' hand-off sections walked, R1's twelve and R2's three sets — catalog items 6 through 11.
- [x] The staged-deleted `bld-003-*.md` files re-measured rather than inherited: **three, not four** — catalog item 12.
- [x] Observed-but-not-fixed items carried — catalog items 13 and 14.
- [x] Settled judgements separated from deferrals — `### Settled judgements, deliberately NOT in the catalog`.
- [x] Spec status-line re-verification performed, and `check_spec_glossary.py` / `check_trailing_commas.py --check` re-run and quoted on the spec, the rationale, and this artifact — `### Spec status-line re-verification` and `### Verification commands run at this gate`.
- [x] Every count stated with the command that produced it, re-derived rather than copied from an artifact — `### Every count in this artifact, with the command that produced it`.
- [x] The cycle's five files confirmed committed at `bca1ccf1`, and no source, test, or `examples/` file touched by any item — `### Working tree, re-derived`.
- [x] The baseline exception applied to what a result *blocks*, never to whether it is recorded — every result below is the command's real one.
- [x] No package source or test file written; no `git stash` / `checkout` / `restore` / `worktree`; no commit; no branch created or switched; the three deleted `bld-003-*.md` files not restored; neither closed artifact, the spec, the rationale, nor Worker 0's plan opened for writing — `### Spec changes made (Worker 1 only)`.

---

## Gate report (Worker 1)

### Working tree, re-derived

`HEAD` is re-derived rather than taken from any artifact, all of which warn that it moves (it moved from `346d6731` to `ff03c137` mid-cycle, and again to `bca1ccf1` at the maintainer's commit):

```text
git rev-parse HEAD                                          -> bca1ccf180489918da0a522d5a711af013b482c7
git log -1 --format='%h %s' -- docs/SPECS/spec-005-…-0_0_3.md
  -> bca1ccf1 docs(spec-005): reconcile the DjangoType contract with HEAD and extract its rationale
```

**The cycle's five files are committed, and the commit is exactly five files, all under `docs/`:**

```text
git show --stat bca1ccf1
  docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md   713 ++++
  docs/SPECS/spec-005-django_type_contract-0_0_3.md                  122 +-
  docs/builder/bld-005-r1-rationale_move.md                          731 ++++
  docs/builder/bld-005-r2-spec_reconciliation.md                    1298 ++++
  docs/builder/build-005-django_type_contract-0_0_3.md               304 ++++
  5 files changed, 3091 insertions(+), 77 deletions(-)
```

**No source, no test, and no `examples/` file was touched by any item of this cycle** — checked three ways rather than asserted:

```text
git diff -- django_strawberry_framework/ tests/         | wc -l   ->  0
git status --porcelain | grep -c '\.py$'                          ->  0
git show --stat bca1ccf1 -- django_strawberry_framework/ tests/ examples/  ->  (no files)
```

That is the claim that would make a `pytest` failure un-attributable to this cycle. No failure occurred, so the escalation path the dispatch reserved was not needed.

`git status --porcelain | wc -l` -> **12** before this artifact was written, **13** after (the thirteenth being `?? docs/builder/bld-005-final.md`). Both readings were taken. **Every one of the twelve belongs to the concurrent spec-004 cycle or to the `bld-003-*` deletions; none is this cycle's:**

```text
 M docs/GLOSSARY.md                                     concurrent spec-004 cycle (its R3 regenerate)
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md        concurrent spec-004 cycle
 D docs/builder/bld-003-r1-rationale_move.md            NOT this cycle's — catalog item 12
 D docs/builder/bld-003-r2-spec_reconciliation.md       NOT this cycle's
 D docs/builder/bld-003-r3-doc_completion_archive.md    NOT this cycle's
 M examples/fakeshop/db.sqlite3                         concurrent writer; same-size churn, see below
?? docs/SPECS/appx/spec-004-…-rationale.md              concurrent spec-004 cycle
?? docs/builder/bld-004-final.md                        concurrent spec-004 cycle
?? docs/builder/bld-004-r1-rationale_move.md            concurrent spec-004 cycle
?? docs/builder/bld-004-r2-spec_reconciliation.md       concurrent spec-004 cycle
?? docs/builder/bld-004-r3-doc_completion_archive.md    concurrent spec-004 cycle
?? docs/builder/build-004-optimizer_beyond-0_0_3.md     concurrent spec-004 cycle
```

Three notes on that list, each a fact a later reader would otherwise have to re-derive:

- **`examples/fakeshop/db.sqlite3` is `Bin 5050368 -> 5050368 bytes, 0 insertions, 0 deletions`.** `BUILD.md` `### Tracked binary / generated files` is explicit that a same-size binary diff is **not** proof of a no-op, and this gate does not claim one. It was already dirty when this pass began, this cycle wrote no DB row, and the only DB-touching command in the whole cycle is the read-only `import_spec_terms --check`. **It was not reverted and must not be** (`AGENTS.md` rule 34) — a concurrent session is writing it.
- **`docs/GLOSSARY.md` is dirty and is the concurrent cycle's**, not this one's. The plan's `## Concurrent-writable tracked binary / generated files` expected it clean; that premise is stale, and it is R3's re-verification duty that never ran (catalog item 3.1).
- **`docs/builder/bld-004-final.md` has appeared since the plan was written** — the concurrent cycle closed while this one paused. It was read for this artifact's shape and was not edited, moved, or restored.

**No concurrent churn arose during this pass.** The plan's `**Baseline exception for the final test-run gate**` is therefore **inert on the facts** — every gate command passed, so no result is attributable to a file this cycle never wrote. The exception governs what a result *blocks*, never whether it is recorded honestly, and every result below is the command's real one.

### Gate commands, in `BUILD.md` order

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `5635 passed, 40 skipped in 64.60s (0:01:04)`, exit 0 |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).` exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 |
| 4 | `uv run ruff format --check .` | **PASS** — `418 files already formatted`, exit 0 |
| 5 | `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0 |
| 6 | `git diff --check` | **PASS** — no output, exit 0 |

**All six pass. That does not make the cycle green** — the six commands measure the tree, and this cycle's undelivered work is an unrun item and an open finding, neither of which any command in this list can see. The `Status:` line, not this table, is the gate's verdict.

Notes on the run, none of them a qualification of a result:

- **Command 1 took no coverage-shaped flag but `--no-cov`.** `pytest.ini`'s `addopts` auto-applies `--cov`, so `--no-cov` is required and is the only permitted form (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). **Line coverage was neither inspected nor asserted.** The run is the full parallel sweep across all three test trees — package `tests/`, per-app `examples/fakeshop/apps/<app>/tests/`, and live `examples/fakeshop/test_query/` — which is what makes it the backstop for the order-dependent schema-registry class a focused run structurally cannot see.
- **Command 4 emitted one ruff warning**, `COM812 may cause conflicts when used with the formatter`. It is a configuration advisory printed on every invocation in this repo, not a formatting failure; the command exited 0 with `418 files already formatted`. Exit codes for 4 and 5 were captured directly from the tools, not from a pipeline.
- **Commands 4-6 are read-only.** No `--fix` was passed in any form, and no file was rewritten by the gate. The gate's only writes are this artifact and `docs/builder/worker-memory/spec-005-worker-1.md`.
- **Commands 1, 4, 5, and 6 read the whole tree**, including the concurrent cycle's seven dirty paths and the dirty DB. All four passed, so the plan's baseline exception never had to be applied.

### Floor verification

**No floor-verification scope declared.**

Written out rather than omitted, per `worker-1.md` `## Final test-run gate` — an unrun floor claim and an undeclared one look identical in an artifact that just skips the heading. The plan's preamble declares `Floor-verification scope: none. No residual item touches a Django / Strawberry / channels integration seam`, and that is correct on the mechanical evidence rather than accepted from the declaration: the cycle's whole diff is one spec, one new rationale companion, and three per-cycle artifacts, and `git diff -- django_strawberry_framework/ tests/` is 0 lines. `BUILD.md` `### When it is required` scopes the obligation to request/response handling, view or ASGI plumbing, upload or body parsing, the session/auth surface, queryset or expression compilation, schema and type construction against Strawberry internals, and consumer or middleware wiring; the cycle touches none. **No floor venv was built and the shared `.venv` was not mutated.** There is no unrun floor claim to close the gate on.

One forward-looking note, because R3 never ran: **if the two authorized docstring corrections (catalog items 4 and 5) are made later, they still owe no floor run** — they are prose inside docstrings, assert no version-dependent behavior, and no test reads them.

### Hot-path budget

**Not applicable; the plan declares `Hot-path declaration: none`.** Confirmed rather than accepted: no code runs per request, per resolver, per row, per connection, or per outbound message, because **no code changed** (`git diff -- django_strawberry_framework/ tests/` -> 0 lines).

### Failability proofs

**None owed; the cycle introduced no boundary, guard, gate, or rejection path.** Confirmed mechanically by the same command rather than accepted from the plan's declaration or an item's report, per `worker-1.md` `### Failability and fail-open checks`. The companion confirmation is equally mechanical: **no fail-open shape landed**, vacuously — a fail-open shape is an expression in executable code and the diff contains none.

One nuance worth recording, because the reconciled spec *describes* boundaries: `spec:36` states the two `Meta.primary` ambiguity rejections and `spec:52` the `_select_fields` unknown-name raise. Describing boundaries that shipped eleven releases ago is not introducing them, and no proof is owed for either.

### Staged-anchor sweep — owned by this gate, R3 having never run

`BUILD.md` `## Cross-slice integration pass` step 6 is normally the integration pass's. This cycle declared no integration artifact (the plan's `## Artifact list` records why) and folded the sweep into R3 — **which was never dispatched — so this gate owns it.** Re-measured here rather than inherited from Worker 0's pre-flight reading of "zero hits anywhere", which predates every artifact this cycle wrote.

**The mechanical test first**, because it closes the classification question by construction rather than by judgement — a staged anchor is a source-site marker (`AGENTS.md` rule 26), so zero outside `docs/builder/` means every surviving hit is by construction a per-cycle scratchpad hit:

```text
grep -rEn 'TODO\(spec-005|TODO-(ALPHA|BETA|STABLE)-005' . --exclude-dir=docs/builder  ->  no match (exit 1)
grep -rEn 'TODO\(spec-005|TODO-(ALPHA|BETA|STABLE)-005' . | wc -l                     ->  2
```

Whole-tree decomposition, published rather than reduced to a bare number (a raw count here reads as a failure signal and is not one):

```text
docs/builder/build-005-django_type_contract-0_0_3.md   2   (:31, :281)
```

**2 matching lines in exactly one `.md` file, both the grep pattern itself quoted in prose describing the sweep R3 was to run** — `:31` is the plan's `### Residual scope` R3 bullet and `:281` is the plan's R3 checklist row. Zero in the spec, zero in the rationale, zero in either closed artifact, zero in any source, test, or example file, zero in `docs/GLOSSARY.md`, and zero in `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` (verified directly, so step 6's board-card exclusion never had to be applied). **Zero staged anchors survive in shipped material, and the sweep is discharged.** This artifact does not appear in the sweep because it writes the anchor only in the *regex* form and never the literal one; fencing is not what keeps a file out, since `grep` does not know about fences.

Worker 0's pre-flight reading of "zero hits anywhere, spec included" is therefore **superseded but not contradicted**: it was taken before the plan existed, and the plan is now the only carrier.

### Cross-artifact read

Both closed artifacts read in full, as `BUILD.md` `## Cross-slice integration pass` step 1 requires with no "as needed" — `bld-005-r1-rationale_move.md` (**731** lines, `final-accepted`) and `bld-005-r2-spec_reconciliation.md` (**1,298** lines, `revision-needed`). There is no third artifact: `docs/builder/bld-005-r3-doc_completion_archive.md` **does not exist on disk**, which is the mechanical form of "R3 was never dispatched".

The trap `bld-004-final.md` flagged for a gate of this shape — an item carried only by an earlier artifact is lost to a walk of the latest one — takes a **different form here and is handled by construction**. R2 is a single artifact carrying three review rounds whose later blocks *supersede figures inside its own earlier blocks* (six such supersessions, listed at its `### Corrections to this artifact's pass-1 and pass-2 records`, plus a seventh L12 charges as unmarked). So the hazard is intra-artifact, not inter-artifact: reading R2's pass-1 drift table without its pass-3 corrections block yields six stale figures. Every figure this catalog states was re-derived at this gate rather than lifted from any block.

### Cycle summary — what R1 and R2 delivered, and what R3 did not

Spec-005 shipped at `0.0.3`, eleven minor versions before this cycle. Its boundary — which `Meta` knobs are applied, which are rejected, which hard constraints are temporary — shipped then and holds. What this cycle produced is the deliverable set the shipped cycle never made, plus the reconciliation that fifty-odd later specs made necessary. **No package source, test, or example code was written, and the full sweep confirms it.**

- **R1 — spec rationale extraction. `final-accepted`.** Created `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`, the companion `BUILD.md` `## Spec rationale extraction` makes the first substantive action of every build and which the released cycle predated. Two `**Future direction.**` prediction blocks, one "real friction" derivation paragraph, one first-registered-wins rejection, and the whole of `## Open questions` were **moved** — three entries plus a cross-cutting standing note, each keyed to its spec section by heading and a resolving anchor, each carrying the alternatives rejected, the later spec that caused each change, and the claims the section may no longer make. Spec `154 -> 132` lines, `13,346 -> 11,002` bytes (**-17.6%**). Two Worker 3 review rounds; three findings (one Medium, two Low), all closed. **Its durable contribution beyond the file is methodological**: a span-sampled move check cannot detect a sentence nobody made into a span, and the line-granularity check driven off `git diff -U0` that replaced it found the one cut sentence two earlier verifications had missed.
- **R2 — spec-versus-HEAD reconciliation. `revision-needed`, PAUSED.** Every claim the package falsifies restated as the contract that actually holds or handed to the spec that now owns it, with the explanation of each change landing in the rationale and never in the spec. `## Current state` was **removed whole** rather than refreshed — a status section inside a contract document is the shape the maintainer's framing forbids — and its one durable claim (the `get_queryset` sentinel) was restated and corrected on four points into `## Coordination …`, where the optimizer half already lived. Both `Meta`-key rosters were **removed, not refreshed**. Three topics were retitled; the never-followed "a future spec must update this contract spec" instruction was retired and replaced by an obligation on the code. Worker 0's 20-row drift table was the verified floor, not the worklist: R2's own sweep added **two** further rows (D21, an undischarged `docs/README.md` obligation D6 caught only half of; D22, a citation of `convert_relation`, a symbol that no longer exists) and corrected one plan test-name citation (D12). **Three** Worker 3 review rounds, **16 findings** — 6 Medium, 10 Low — of which **14 are closed** and **two remain open** (M6, L12), both against R2's own record of how a figure was measured.
- **R3 — documentation completion and archive audit. NEVER DISPATCHED.** Nothing of its scope was performed. Catalog items 3.1-3.5 and 4-5 are that scope.

**The spec's before and after**, every figure re-derived at this gate:

| Figure | Pre-cycle (`git show ff03c137:<spec>`) | Now (at `bca1ccf1`) | Delta |
|---|---|---|---|
| spec lines | 154 | **122** | -32 |
| spec bytes | 13,346 | **13,373** | **+27 (+0.2%)** |
| `git diff --numstat ff03c137 HEAD -- <spec>` | — | **45 insertions / 77 deletions** | — |
| fenced code blocks | 0 | **0** | unchanged |

**The byte count ends 27 above where it started while the line count fell by 32, and that is the cycle's shape rather than an anomaly.** R1 removed 2,344 bytes of deliberation (154 -> 132 lines, 13,346 -> 11,002); R2 then spent most of them back on **contract** — four durable failure classes where four dated gaps stood, three `**Contract.**` blocks, a corrected sentinel description, and one boundary clause — ending at 122 lines / 13,373 bytes. A reconciliation that only shrinks a spec is deleting contract; both directions are reported so the net delta cannot be read as scope creep. **Spec-005 is the only one of the four residual cycles to date whose spec ends larger than it started**, because it is a *contract* spec whose deliberative layer was two predictions rather than eight per-slice arguments.

Alongside it: the rationale companion at **713 lines / 51,373 bytes**, in two layers (R1's move record and R2's ten-entry reconciliation record). **`docs/GLOSSARY.md` was not written by this cycle** — its dirty state is the concurrent spec-004 cycle's.

### Deferred work catalog

Authored from both closed artifacts' `### Notes for Worker 1 (spec reconciliation)`, `### What looks solid`, `### DRY findings`, review, and final-verification blocks — **and from R3's undone scope, which no artifact carries because no artifact exists.** Keyed by item; every carrying block is named per bullet; every open item was re-derived live at this gate and the command is quoted in the item.

**Fourteen items.** Items 1-2 are R2's open findings, 3 is R3's entire unrun scope in five parts, 4-5 are the one authorized source change of the cycle, 6-11 come from the two artifacts' hand-off sections, 12 is a maintainer decision this cycle inherited, and 13-14 are observed-but-not-fixed.

---

#### 1. R2 finding **M6** (Medium, OPEN) — a false demonstration under a standing lesson the cycle intends to carry out

*Carried by:* `bld-005-r2-spec_reconciliation.md` `## Review (Worker 3, pass 3)` `#### M6`, citing `:989`, `:994`, and `:1077` (pass-3 hand-off 4). *Licensing clause:* none — it is an open finding, not a licensed deferral. R2's `Status:` is `revision-needed` and the item was never re-dispatched.

**What it says.** R2's L9 correction is right — the oldest `ALLOWED_META_KEYS` definition is **six** keys including `interfaces`, at commit `084b4643` at the pre-rename path `django_strawberry_framework/types.py`, not the five-key set. But the sub-claim R2 built under it measures false. R2 pass 3 wrote at `:994`: *"Drop the fallback and the same replay yields **12** definitions and a five-key oldest. So '13 distinct definitions, oldest = five keys' … is two numbers from two different populations in one sentence."* Worker 3 re-derived: the stdout-only replay (the two pre-rename blobs unreadable) yields **13** definitions and **also** a six-key oldest, because the first two post-rename revisions — `70c7bff2` and `2893ccb8` — carry the same six-key set at the modern path, so the two unreadable blobs contribute no distinct definition of their own. The five-key set is the *third* state under either replay, never the oldest.

**Three sentences fall together**: "12 definitions", "a five-key oldest", and the two-populations diagnosis — plus pass-3 hand-off 4's causal clause, *"It is what turned 13 definitions into a five-key oldest here."* The real cause of pass 2's five-key figure is not identified by the record, and "12" has the shape of an inference (13 − 1) rather than a measurement, which is the exact class this item charged five times.

**Why it is Medium.** Hand-off 4 promotes the `--follow` rename trap as *"the more dangerous of the two [standing lessons]"* and hand-off 3 instructs that a lesson carried anywhere durable carries its measurement with it. This is the M4 situation one pass later with the polarity reversed: there the pass **refused** a softening and replaced a false anecdote with a real measurement, and was right to. The same standard retires a false instance under a true rule.

**What closing it takes** (Worker 3's recommendation, and no durable file is affected): keep the rule and the two legs that hold — `git show <commit>:<new/path>` on a pre-rename revision exits **128** writing only to stderr, so a replay loop reading stdout drops the oldest revisions silently; and *resolve each blob at the path the file had at that commit*. Retract the three sentences and the causal clause and substitute the measurement above, which is a **stronger** illustration: the stdout-only replay loses two revisions and **its summary numbers do not move at all**, which is a sharper picture of a silent failure than a number that visibly changes. If the cause of pass 2's five-key figure is wanted in the record, **say it is unestablished rather than attributing it.**

**Why it touches neither the spec nor the rationale.** M6 lives entirely inside `bld-005-r2-spec_reconciliation.md`'s own record of how it measured. Both durable files were confirmed byte-unchanged across R2 passes 2 and 3 and are unchanged at this gate: **spec `122 lines / 13,373 bytes`, rationale `713 / 51,373`** (`wc -l -c`, re-measured here). Worker 3's pass-3 note 1 is explicit: *"Neither durable file needs an edit and neither should be opened."*

#### 2. R2 finding **L12** (Low, OPEN) — a sixth stale figure survives under a hand-off that says the sweep is complete

*Carried by:* `bld-005-r2-spec_reconciliation.md` `## Review (Worker 3, pass 3)` `#### L12`, citing `:267`. *Licensing clause:* none — an open finding.

**What it says.** `bld-005-r2-spec_reconciliation.md:267`, the `### Spec changes made (Worker 1 only)` row for `spec:56`, still reads (verified verbatim at this gate):

> `| spec:56 | New paragraph: the error shape is owned by `_format_unknown_fields_error` and inherited by five further keys | the section claimed the contract for two keys; the package honours it for six | D16 |`

That is the mixed-unit form finding L4 charged and the pass corrected **in the rationale** — `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md:516` now reads *"the package honours that claim for **seven**. The unit is keys: the raise sites carry six distinct `attr` labels rather than seven"* (verified). The artifact's copy sits in the per-line change table the final gate walks, **one row above `:270`, which the same pass did mark.**

**Why it is worth a line rather than a shrug**: R2's pass-3 hand-off 5 asserts *"No unmarked figure of the corrected class remains in this artifact."* A completeness claim is what stops the next reader looking.

**What closing it takes**: a sixth bullet under `### Corrections to this artifact's pass-1 and pass-2 records` in the same form as the five already there, and re-wording hand-off 5 from five rows to six. The corrected-class population is exactly six rows: `:117`, `:121`, `:124`, `:135`, `:267`, `:270`. **No durable file is affected**; the row's own left-hand cell ("inherited by **five further keys**") lets a reader derive seven in place.

#### 3. R3's entire unrun scope — itemized

*Carried by:* nowhere. `docs/builder/bld-005-r3-doc_completion_archive.md` does not exist. The scope is reconstructed from the plan's `### Residual scope` R3 bullet (`build-005-…:31`), its checklist row (`:281`), and its `## Worker-0-verified facts`. *Licensing clause:* none — this is undone work, not a licensed deferral.

**3.1 — The durable-doc audit against the shipped contract.** Verify `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, and `KANBAN.md` describe the contract that actually shipped. Three facts R2 established as inputs, all re-usable and all recorded in its hand-offs (pass 1 item 9, pass 2 item 6, pass 3): `docs/README.md` **has no `## Current surface` section and no reference to spec-005 anywhere** (`grep -n 'Current surface' docs/README.md` -> no match; `grep -n spec-005 docs/README.md` -> no match) — which is what makes drift rows D6 and D21 *undischargeable obligations* rather than corrections owed; `docs/GLOSSARY.md`'s `Meta.interfaces` (`shipped (0.0.5)`) and `Meta.primary` (`shipped (0.0.6)`) entries are already correct and the `Meta.primary` entry already carries the **full four-case ambiguity table with both error strings**, which is why the reconciled spec points there rather than restating it; and the three still-deferred keys are labeled by **release** (`Meta.fields_class` `planned for 0.1.1`, `Meta.search_fields` `0.1.2`, `Meta.aggregate_class` `0.1.3`), never by spec, which is the fact `spec:22` now depends on. **The plan's expectation that `docs/GLOSSARY.md` would be clean is stale**: it is dirty right now with the concurrent spec-004 cycle's regenerate, so whoever runs this audit must compare `iterdump()` semantics rather than file bytes and verify by two-consecutive-regenerate byte-stability, per the plan's own `### First growth` revision.

**3.2 — The three-direction cross-reference sweep of the already-performed archive.** The plan's `### Every reference TO spec-005` table is R3's **verification** list, not a rewrite list, and the plan says outright R3 re-runs the sweep rather than trusting it. The three directions: references **to** spec-005 (`KANBAN.md:142` / `:4782` plus `KANBAN.html`, generated and never hand-edited; `spec-006:108` / `:135` / `:146`; prior cycles' build plans); references **from** spec-005 (its 8 link definitions, all disk-checked green at this gate by `check_trailing_commas` and by R2's own 27-target sweep); and the new direction the table cannot show — **the rationale's own outbound links at `docs/SPECS/appx/` depth**, needing `../../GLOSSARY.md` for a `docs/` target and `../spec-NNN-….md` for a `docs/SPECS/` sibling. R2 measured all 27 definitions resolving across both files; nobody has re-measured them since the commit.

**3.3 — The `SpecDoc.path` verification chain.** `worker-0.md` `### DONE-card invariants`. Worker 0's pre-flight recorded `SpecDoc` for card 5 with `path` **already** `docs/SPECS/spec-005-django_type_contract-0_0_3.md`, and card 5 as `DONE-005-0.0.3` / `status.key` `done` / `target_version.number` `0.0.3` with 5 `CardItem`s and no `Definition of done` section. R3 was to verify rather than perform. **Note the DB has been written by a concurrent session since that reading**, so the verification must be re-run, not inherited. (`SpecDoc.path` is the writable column; `SpecDoc.url` is a read-only `@property` and assigning `url=` raises.)

**3.4 — The terms-CSV importability chain.** `card.glossary_links.count()` must equal the 7 rows of `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-terms.csv` — `configurationerror`, `djangotype`, `metaexclude`, `metafields`, `metainterfaces`, `metamodel`, `metaprimary`, one row per anchor so the CSV is importable. **A green `check_spec_glossary` alone does not prove this**, which is why it is a separate obligation. The CSV was never opened by any pass of this cycle (verified: it is clean in `git status`), and this gate re-ran `check_spec_glossary.py` green — but the **DB-side** count has not been re-derived since the concurrent write.

**3.5 — `import_spec_terms --check`.** Run at this gate: `OK: 49 done cards have glossary links.` exit 0, **read-only `--check` form only; the writing sync form was never invoked.** That discharges the command but not R3's obligation, which is the whole chain of 3.3 + 3.4 behind it.

**3.6 — The staged-anchor sweep. DISCHARGED HERE, not deferred.** Listed so a reader of the plan's R3 row does not carry it forward. See `### Staged-anchor sweep — owned by this gate, R3 having never run`: 2 hits, both the plan quoting its own grep pattern, zero outside `docs/builder/`.

#### 4. The **`exceptions.py::ConfigurationError`** docstring correction — authorized, never made

*Carried by:* `bld-005-r2-spec_reconciliation.md` `### Notes for Worker 1 (spec reconciliation)` items 1 and 2 (ESCALATED), routed by Worker 0 into the plan's `### THE ONE SOURCE EDIT THIS CYCLE AUTHORIZES`. *Licensing clause:* the plan's `## Build-wide context flags` — *"R3 may edit a docstring only if its audit finds a factually-false one, and that routes through Worker 2"* — plus the explicit authorization, which requires the **full unmodified worker chain** (Worker 1 plans, **Worker 2 makes the edit**, Worker 3 reviews, Worker 1 final-verifies), not procedural closure. **R3 was never dispatched, so this is the one source change the cycle authorized and did not make.**

**Verified still unmade at this gate** — `django_strawberry_framework/exceptions.py` is byte-identical to HEAD and clean in `git status`. The docstring reads, verbatim:

```text
    Covers type-creation / finalization Meta validation, settings reads,
    registry collisions, filter/order/mutation set wiring, and other
    configuration-time failures. Examples:

        - Missing ``Meta.model``.
        - ``fields`` and ``exclude`` declared together.
        - A deferred-surface key (``aggregate_class``, ``fields_class``,
          ``search_fields``) declared before the spec that owns it has
          shipped.
        - Two ``DjangoType`` subclasses registering against the same model.
        - A non-mapping ``DJANGO_STRAWBERRY_FRAMEWORK`` settings value.
```

**Two defects, one file, one edit:**

- **The fourth example has been false since `0.0.6`.** Registering two `DjangoType` subclasses against one model is the *supported* multi-type pattern — `registry.py::TypeRegistry.register` **appends** to the model's list. What actually raises is narrower and lives at two different points: a **duplicate primary** (`#"is already the primary type"`) or a **flipped primary flag on re-register** (`#"primary flag cannot be flipped on re-register"`) at `register`, and **multiple types with no declared primary** at `types/finalizer.py::_audit_primary_ambiguity`, which is *finalization*-time, not registration-time. The line does not merely overstate — **it tells a consumer that the sanctioned pattern is an error.**
- **The deferred-key example says "spec" where the runtime message says "feature".** Commit `83c25963` (2026-05-05, "Finish consolidation of specs and doc files") deliberately moved the runtime message from "The **spec** that owns them has not shipped" to "The **feature** that owns them has not shipped", which is what `types/base.py::_validate_meta` raises today. The key list is correct; the word is the one drift row D11 records as a deliberate consumer-facing correction, and this docstring is **the last in-source survivor of the retired vocabulary**.

**This is a documentation defect in source, not a correctness defect** — no behavior is wrong and no test asserts the docstring. `AGENTS.md` rule 16 applies after the edit (`ruff format` / `ruff check --fix`). No test is owed and `fail_under = 100` is unaffected. **Scope is one file and these two examples**; the plan's constraint is explicit that Worker 2 does not widen it into a sweep of every docstring in the package.

#### 5. The **`types/base.py::_format_unknown_fields_error`** docstring correction — authorized, never made

*Carried by:* `bld-005-r2-spec_reconciliation.md` `#### L5` (Worker 3, pass 1, RECORDED not fixed) and `### Notes for Worker 1` pass-1 item 4; Worker 0 then **WIDENED** the plan's `### THE ONE SOURCE EDIT THIS CYCLE AUTHORIZES` to a second file, correcting its own first figure at finding L11; the definitive specification is R2 pass 3's `### Hand-off 1, restated exactly`, which **supersedes** pass 2's `:711` wording. *Licensing clause:* same as item 4. **Same unmade status, same reason.**

**Verified still unmade at this gate** — `django_strawberry_framework/types/base.py` is byte-identical to HEAD and clean in `git status`. The docstring reads, verbatim:

```text
    """Return the standard "unknown fields ... Available: ..." error message.

    Used by every validator that points at a typo in ``Meta.fields``,
    ``Meta.exclude``, or ``Meta.optimizer_hints``.  Centralizing the
    format keeps the consumer-visible error shape consistent across
    typo-guard sites.
```

**The defect:** it names three `Meta` keys as its complete caller set. The measured reach is **five direct call sites in three functions, carrying six distinct `attr` labels over seven `Meta` keys.** It under-states its own reach on **the one error shape spec-005 pins as public contract** — which is precisely the sentence R2 widened on the spec side at `spec:56`.

**The call-site table, re-derived at this gate by parsing the module's AST rather than copied from the artifact** (it reproduces R2's hand-off 1 row for row):

| call site | enclosing function | `attr` label passed |
|---|---|---|
| `django_strawberry_framework/types/base.py:1270` | `::_validate_optimizer_hints` | `"optimizer_hints"` (`:1272`) |
| `:1280` | `::_validate_optimizer_hints` | `"optimizer_hints"` (`:1282`) |
| `:1324` | `::_selected_meta_targets` | `attr=attr` (`:1326`) — forwarded, not a literal |
| `:1612` | `::_select_fields` | `"fields"` (`:1614`) |
| `:1624` | `::_select_fields` | `"exclude"` (`:1626`) |

**Six distinct `attr` labels covering seven `Meta` keys:** `exclude`, `fields`, `filesystem_path_fields`, `nullable_overrides/required_overrides` (one label, two keys), `optimizer_hints`, `relation_shapes`.

**Three of the six labels arrive indirectly**, through the single forwarding call at `:1324`, each supplied by its own validator — re-derived here: `nullable_overrides/required_overrides` from `::_validate_nullability_override_targets` (call `:1393`, `attr` `:1396`), `filesystem_path_fields` from `::_validate_filesystem_path_targets` (`:1468` / `:1471`), `relation_shapes` from `::_validate_relation_shape_targets` (`:1533` / `:1536`). **Exactly one of the five direct call sites is inside `_selected_meta_targets`** — the retracted phrasing *"five direct call sites, three of them via `_selected_meta_targets`"* (finding L10) attached the three to the wrong noun, and the plan's earlier "eight distinct `attr` values" (finding L11) counted `attr=` **occurrences**, not distinct labels.

**Write the docstring from the enumeration, not from the counts.** That is R2's own instruction and it is the process fix applied to the sentence: every defect this item found was a numeral standing in for a population. **Nothing in the spec or the rationale is falsified by making this correction** — neither file quotes or characterizes either docstring, and `spec:56` becomes *more* true once the docstring stops naming three keys.

#### 6. R1's twelve hand-offs — eleven discharged by R2, one class standing

*Carried by:* `bld-005-r1-rationale_move.md` `### Notes for Worker 1 (spec reconciliation)` (move pass, items 1-8), the same section in `## Move report (Worker 1, pass 2)` (items 9-11), and `## Final verification (Worker 1)` `### Hand-off list audit` (the twelfth). *Licensing clause:* R2's `### Dispatched findings checklist` box at `:70` records all twelve acted on; Worker 3 confirmed.

**Eleven are closed** and are listed here only so a reader of R1's hand-off section does not reopen them: the `metaprimary` sole-carrier re-siting (discharged in the strongest available form — the anchor was placed into `### One model, many types, one primary` in the **same `Write`** that removed `## Current state`, so the file was never on disk uncarried); the four other single-carrier anchors in falsified prose; D15's discharge; D3/D4/D8's spec-side residue; `## Non-goals` treated as load-bearing; D18 decided with R1's recorded argument available; the `spec-006` by-title heading preserved; both `**Decision for 0.0.3.**` blocks rewritten as one coherent edit each; hand-off 10's Provenance note (see item 7); and hand-off 11's line-granularity method (see item 9).

**The twelfth stands, and it is a standing instruction rather than an unfinished task.** R1's final verification established the population exhaustively — by extracting every double-quoted span of 25+ characters from the rationale (20 spans) and testing each against the spec body — and extended hand-off 9 from the singular to its full class of **two**:

> **The rationale quotes or condenses two claims that were standing in the spec, both deliberately, and no future pass may sync either away when the spec's copies change.** (a) The `@strawberry.type`-rewrites-`cls.__annotations__` override diagnosis, *condensed* in the `### Consumer override semantics` entry — the spec's copies (`## Problem statement` item 2 and the topic's first paragraph, drift row D5) have since been corrected by R2, so the rationale's is now the only copy. (b) `## Coordination …`'s *"must update this contract spec accordingly"*, quoted **verbatim** in the `## Open questions` entry — the spec's copy (D18) has since been retired by R2, so again the rationale's is the only copy. In both cases the rationale's copy is **the record of a claim the spec may no longer make**, which is what `BUILD.md` `## Spec rationale extraction` requires the file to carry. Deleting or rewriting either to match the corrected spec would delete the record.

**Why the two members had to be found by two different methods** is the durable half: a condensation appears in no verbatim scan at all, so neither method alone establishes the class. R2 confirmed both survive untouched.

#### 7. The rationale's layer-1 present-tense sentences — deliberately not corrected, and the decision is deferred

*Carried by:* `bld-005-r2-spec_reconciliation.md` `#### L3` (Worker 3, pass 1), its pass-2 disposition, `### The two edits that removed rather than restated` (Worker 3, pass 2), and pass-2 hand-off 4. *Licensing clause:* `worker-1.md` rule 4 — the rationale file is **append-only during the build**, and layer 1 is R1's record of what that pass did, not a description of the current spec.

**What is deferred.** Four sentences in the rationale's R1 layer make present-tense claims about spec content that R2 has since falsified. The population was **established** rather than sampled — layer 1 was read for present-tense claims about what the spec currently says, and there are exactly four: `## Provenance of this record`'s "deliberately left in the spec" list (`:59-72`); the `## Problem statement` item-1-is-untouched note (`:102-103`) — which is the load-bearing one, since it is the stated justification for moving the competitive argument while leaving the problem-statement sentence, and R2 then removed that sentence; "The promise sentence is still in the spec" (`:222`); and "That sentence is still in the spec and is item R2's to decide on" (`:249`).

**None was edited.** All four are disclosed in one `## How to read this file` clause, which is navigation rather than record, and which covers the class at once instead of annotating each. Worker 3 endorsed this as *"the better remedy of the two available"*.

**What remains open, in R2 pass-2 hand-off 4's own words:** *"If a later pass wants them corrected, that is a decision about whether the rationale's first layer is a record or a description, and it should be taken deliberately rather than as tidy-up."* **That is the deferral: the decision, not the edit.** A related instance is already decided the other way and is in the settled-judgements section below — `## Standing note`, which R2 *did* edit because it is an analytical coda rather than a record of a move.

#### 8. The corrected `git log -S` standing rule — has no durable home

*Carried by:* `bld-005-r2-spec_reconciliation.md` `### M4 re-derived` (the corrected block, quoted in full there) and pass-3 hand-off 3. *Licensing clause:* none; the rule was derived inside a per-cycle scratchpad that closes with its cycle (`START.md` "Temp artifact conventions"), and nothing in this cycle's writable set is durable enough to hold a repo-wide methodology rule.

**The rule, in its corrected form:** `git log -S<identifier>` is a search for changes in **how often a name is written**, not for changes in the value it names. A key added to or removed from a `frozenset` literal moves no occurrence count, so `-S` sees such a commit only when something *else* in the same commit also moves the count — a docstring, a comment, another reference. Whether that happens is incidental to the question being asked. **To establish what values a constant has ever held, replay the definition over every revision of the file** — `git log --follow` for the revision list, `git show <commit>:<path>` per revision, parse the assignment. `-S` remains a sound way to *locate* the files that ever contained an identifier, because a file that ever held it took its count from zero at some commit.

**Its evidence, which must travel with it** (the rule's whole claim is that the hazard is invisible when it bites, so a rule asserted without a demonstrated instance is the thing it warns against): on `DEFERRED_META_KEYS` the hazard did **not** bite — `-S` returns 11 commits carrying all four distinct definitions and the exact six-key union, because every membership change happened to ride with a docstring edit naming the constant. On the **sibling constant in the same file** it does bite: `-S'ALLOWED_META_KEYS'` returns **14** commits but recovers only **9 of 13** definitions and **15 of 17** keys — `cursor_field` and `filesystem_path_fields` never appear in any blob it returns, because the six commits that added them (`dae186a1`, `8cac3495`, `7d892d6f`, `d418e649`, `51421e54`, `567cc6d0`) moved no occurrence count. Anyone asking "did `filesystem_path_fields` ever sit in `ALLOWED_META_KEYS`?" off that list gets the wrong answer from a command that returned 14 commits and looked exhaustive.

**How it got here is itself the lesson**, and it is why this entry exists rather than the rule simply being carried: R2 pass 2 asserted the rule from how the tool *should* behave, with a false anecdote under it; Worker 3 re-derived and charged it (M4); R2 pass 3 **refused** the recommended softening to "a hazard that did not bite here", went and found a real instance, and replaced the evidence rather than retreating. A methodological claim needs the same mechanical proof as a count.

#### 9. The `--follow` rename trap, and the line-granularity move check — two methods with no durable home

*Carried by:* `bld-005-r2-spec_reconciliation.md` `### L9 re-derived` and pass-3 hand-off 4 (the rename trap); `bld-005-r1-rationale_move.md` `## Final verification (Worker 1)` and R1's hand-off 11 (the move check). *Licensing clause:* same as item 8 — both live only in per-cycle scratchpads.

- **The rename trap.** `git show <commit>:<new/path>` on a pre-rename revision exits **128** writing only to stderr, so a replay loop that reads stdout drops the oldest revisions **and reports a clean number**. Resolve each blob at the path the file had at that commit. Two of the 77 revisions `git log --follow` lists for `types/base.py` (`77b8fe7f`, `084b4643`) predate the `types.py` split and do not resolve at the modern path. **Its demonstration in this artifact is what M6 charges (catalog item 1)** — the rule holds; the instance under it does not, and the corrected instance is the sharper one.
- **The line-granularity move check.** Drive a move-verification off `git diff -U0` line by line, never off spans chosen by the worker that made the edits — *"a span-sampled move check cannot detect a sentence nobody made into a span."* R1's "17 hand-chosen spans, 17/17 pass" missed a cut sentence that the diff-driven walk found immediately; R2's own walk of its 45 removed lines exposed three record gaps (a dropped implementation history, a dropped "alpha-stage" qualifier, a promoted sentence) that no span either pass would have chosen could have covered. Its companion: **the cut-not-copy shingle count is tokenizer-dependent and means nothing unquoted** — the same two files measured 0, 3, or 4 non-scaffold overlaps at n=8 depending only on whether a comma and a `#` are tokens.

#### 10. The rationale's `## Provenance of this record` is now partly a statement about R1, not about the spec

*Carried by:* `bld-005-r1-rationale_move.md` hand-off 10; `bld-005-r2-spec_reconciliation.md` `### Implementation notes` and pass-1 hand-off 6. *Licensing clause:* R1's hand-off 10 anticipated the shape and says it needs no edit; R2 agreed and left it; `## How to read this file`'s two-layer bullet tells a reader how to take it.

The "deliberately left in the spec" list names four passages, three of which R2 has since rewritten or removed, and the entry refers to *"the `### Consumer override semantics` `**Decision for 0.0.3.**`"* — a label R2 replaced with `**Contract.**`. **Flagged so a later pass does not read it as drift and "fix" it.** It is the same class as item 7 and shares its open decision.

One reading clarification R1's final verification recorded, worth carrying so two consistent lists are not mistaken for a contradiction: the move report's `### What moved, what stayed, what was deleted` names **four carve-out keeps**, and the rationale's `## Provenance of this record` names **four deliberately-left passages** — a *different* set. Both are correct under their own criterion: the rationale's list enumerates passages *that read like deliberation*, while `## Problem statement` and the promotion rule are normative contract. A reader who takes the two lists as one will conclude a passage went unexamined.

#### 11. Two drift rows R2's own sweep added, both now discharged in the spec — recorded so their origin is legible

*Carried by:* `bld-005-r2-spec_reconciliation.md` `### Drift-row disposition` rows **D21** and **D22**, and pass-1 hand-off 4; Worker 0 appended both to the plan's table. *Licensing clause:* the plan says outright its 20-row table is *"Worker 0's verified floor, and R2 owns the full sweep"*. **Both are closed in the spec** — listed because the *general* residue they leave is open.

- **D21** — `### One-model-one-type`'s `**Decision for 0.0.3.**` carried a **second** `docs/README.md` "Current surface" documentation obligation, the same shape as D6, which caught only the consumer-override half of the same obligation. **Neither obligation was ever dischargeable**: that section does not exist in `docs/README.md`. Not restated in the spec; its durable half survives as `## Goal`'s third bullet.
- **D22** — the same section cited **`convert_relation`** as the consumer of the one-type-per-model reverse lookup. **The symbol no longer exists anywhere in the package**; the only occurrence in the tree is a stale comment inside `tests/types/test_base.py`. A dangling symbol citation in a spec is **invisible to `check_spec_glossary`**, which validates glossary anchors, not source symbols. Removed; the surviving reverse-lookup sentence names `model_for_type`, which does exist.

**The open residue is the class, not either row: nothing in this repository checks a spec's source-symbol citations.** D22 was found by a human-driven sweep and would have survived any automated gate this cycle ran. The stale comment in `tests/types/test_base.py` is also still there, and no pass of this cycle could edit a test file.

#### 12. Three staged-deleted `docs/builder/bld-003-*.md` files — the maintainer's decision, still open

*Carried by:* the plan's `## Baseline-dirty out-of-scope files` (which records **four**, the count at plan time) and every pass of both artifacts as an unchanged baseline item. *Licensing clause:* `AGENTS.md` rule 34 — restoring them means `git checkout -- <path>`, which is banned while concurrent sessions write this tree. **No worker in this cycle may restore them.**

**Re-measured at this gate rather than inherited, and the count has changed:**

```text
git status --short -- docs/builder/ | grep '^ D' | wc -l   ->  3
ls docs/builder/bld-003-*                                  ->  docs/builder/bld-003-final.md
git diff --stat -- docs/builder/bld-003-final.md           ->  (empty, exit 0)
```

**Three remain deleted, not four:** `bld-003-r1-rationale_move.md`, `bld-003-r2-spec_reconciliation.md`, `bld-003-r3-doc_completion_archive.md`. **`bld-003-final.md` has reappeared** — it is on disk, does not appear in `git status`, and is byte-identical to `HEAD`, restored by something outside both cycles. It was read for this gate's shape and **was not restored, moved, or edited by this pass.**

**Not this cycle's doing**, unrestorable by any worker, and awaiting the maintainer. Their content is safe in git history.

#### 13. R2's `### Eight duplications caught by measurement` heading counts eight over a table of nine rows

*Carried by:* `bld-005-r2-spec_reconciliation.md` `## Review (Worker 3, pass 3)` `### Notes for Worker 1` item 5 — **recorded rather than filed, deliberately.** *Licensing clause:* Worker 3's own reasoning — *"the first draft it counts no longer exists, so whether the heading or the table is wrong is not decidable from this artifact"*, and unlike the six corrected figures no later pass has contradicted it.

**Re-measured at this gate:** the table under that heading carries **9 data rows** (`| Overlap | Fix |` header, separator, then nine), one of which is annotated `(×2 shingles)` — so "eight places" is reconcilable with nine rows only if the annotated row is one place, which the record does not say.

**Carried here for exactly the reason Worker 3 flagged it:** so a final-gate reader does not mistake it for a seventh instance of the corrected mixed-unit class, **and so nobody "fixes" it by inventing a ninth place or deleting a row.** No durable file is affected.

#### 14. Two plan defects both closed by Worker 0 — recorded closed so a reader of the artifacts does not reopen them

*Carried by:* `bld-005-r2-spec_reconciliation.md` pass-1 hand-off 3 and `#### L11` (Worker 3, pass 2). Both were routed to Worker 0, who owns the plan, and both landed.

- **Drift row D12's test citation.** The plan cited `tests/types/test_base.py::test_relation_shapes_is_shipped_not_deferred`; no such test exists. The real name is `::test_meta_relation_shapes_in_allowed_meta_keys`, whose docstring names `::test_interfaces_is_shipped_not_deferred` as the mirror it follows — very likely how the wrong name was constructed. **Corrected in the plan** at its `**Corrections and additions, appended by Worker 0 at the close of R2**` block. D12's substance is unaffected and the spec cites the correct name.
- **The source-edit widening note's `attr` count (L11).** The plan first read *"five call sites passing eight distinct `attr` values"*; **eight is the count of `attr=` occurrences in `types/base.py`**, not of distinct labels — two carry the same `"optimizer_hints"` literal and one is the forwarding `attr=attr`, which is not a value at all. **Corrected in the plan** to *"five direct call sites carrying six distinct `attr` labels"* with the six enumerated, and R2 pass 3 verified plan and hand-off agree member for member. Re-derived independently at this gate (catalog item 5's table): **they do.** Nothing further is owed to Worker 0.

---

### Settled judgements, deliberately NOT in the catalog

`BUILD.md` scopes the catalog to what was **deferred**. Several things in this cycle read like deferrals in prose and are decisions. Listing them is what stops a future pass reopening them or a reader treating the catalog as incomplete.

- **The `Meta.primary` detection-point correction is settled (D3).** Spec-005 predicted `Meta.primary: bool = False` with four rules and was **substantially vindicated** — right name, right rule, right rejection of first-registered-wins — and **wrong in exactly one detail: the detection point.** It predicted that "two or more types and none claims primary" would raise at **registration**; what shipped detects ambiguity-by-omission at `finalize_django_types()`, in `types/finalizer.py::_audit_primary_ambiguity`, while duplicate-primary and flipped-flag still raise at `registry.register`. **The reason is the spec's own**: registration cannot know whether a later sibling will claim primary, so a registration-time raise would make the outcome **import-order-dependent** — the exact property the spec demanded be kept out of the API contract. `docs/SPECS/spec-018-meta_primary-0_0_6.md` Decision 5 is the authoritative catalog and spec-005 deliberately does not restate it. **Decided — do not "correct" the spec back toward the prediction, and do not re-file the difference as drift.**
- **The anti-inventory decision is settled: the spec deliberately carries no `ALLOWED_META_KEYS` roster.** The pull on a *contract* spec is to refresh the key list; refusing it **is** the DRY decision. `types/base.py::ALLOWED_META_KEYS` is the executable single source and `docs/GLOSSARY.md` publishes each key's status — the spec names both and lists neither, on purpose: a roster restated in a spec is a copy of an executable frozenset, and this one has gone stale **eleven times** (5 allowed / 6 deferred at `0.0.3` versus 17 / 3 at HEAD) with three more moves already carded on the Beta line at `0.1.1`, `0.1.2`, and `0.1.3`. The rejected alternative worth naming, because it is the tempting one: *keep the instruction and add a check to enforce it* — wrong, because whatever such a check verified would be that this document's copy of the key set matches the real one, **which is the roster problem with tooling attached.** **Decided — do not "helpfully" add the list back.**
- **The removal of the three-library competitive sentence is settled.** `## Problem statement` item 1's DRF / `graphene-django` / `strawberry-graphql-django` sentence was removed. This is **not** a re-fight of the spec-004 cycle's maintainer decision on competitive positioning — that decision preserves *a problem statement's statement of the competitor gap where the comparison is the document's subject*, and what the removed sentence asserted was a **gap**: those three libraries allow several types per model and this package did not. `registry.py::TypeRegistry.register` appends, so the package allows it too. **There is no gap left to preserve, and a sentence stating a closed gap is a false claim, not positioning** — `worker-1.md` rule 2 territory. The competitive argument itself is not lost: R1 moved the "real friction" paragraph, which names the same three libraries, into the rationale. Worker 3 charged the reasoning directly and it held. **Decided — do not re-litigate.**
- **Dropping `model_for_type` from the failure-class clause, rather than restating it, is settled (M1).** Finding M1 charged that `## Problem statement` failure class 1 hung the ambiguity hazard on the **type-to-model** direction, which is one-to-one by construction and structurally cannot exhibit it. The finding offered two remedies: drop `model_for_type` from the sentence, **or** state it as the direction that is *not* at risk. R2 dropped it, and Worker 3 endorsed the choice on its merits: `spec:32` already carries the one-to-one statement in contract prose and `spec:34` enumerates the model-to-type direction, so restating the safe direction inside a failure class would have put **a third copy of one fact in one document** — the shape this whole item exists to remove. The class was retitled `**Ambiguous model-to-type resolution.**` **Decided — not an under-fix; do not reopen `### One model, many types, one primary`.**
- **Removing `## Current state` whole, rather than refreshing it, is settled.** The pass's largest single call. A `## Current state` section is a status report **by construction**, and a status report inside a contract document is precisely the shape the maintainer's framing forbids — a reader has to date it before they can use it. Refreshing it would have been the smaller diff and would have guaranteed a third reconciliation cycle. Its one durable claim (the `get_queryset` sentinel) was restated **and corrected on four points** into `## Coordination …`, where the optimizer half already lived, so the fact now has one home instead of two.
- **Retiring the never-followed "a future spec must update this contract spec" instruction is settled (D18).** Twelve keys added and three promoted across at least eleven specs; **none ever touched spec-005**, which is the direct cause of drift rows D9, D10, and D13 and therefore of this whole cycle. The instruction is replaced by an obligation **on the code**, which is checkable against source. The plan's own D18 row assigns the call to Worker 1, so this was decided rather than escalated.
- **`registry.get()` returning `None` for the ambiguous multi-type case is correct as designed.** Its docstring says callers "cannot distinguish this from 'no type registered' without checking `types_for(model)`". The raise belongs to the finalizer audit, which sees the whole registry at once. Worker 0's read-only correctness audit recorded it explicitly so R2 would not mistake it for drift; it is a rationale fact, not a spec sentence, and not a defect.
- **The read-only correctness audit found no defect, and that finding is settled.** All **17** `ALLOWED_META_KEYS` entries are applied end-to-end (13 thread through to `types/definition.py::DjangoTypeDefinition`; `exclude` is consumed by `_select_fields`; `nullable_overrides`, `required_overrides`, and `filesystem_path_fields` by `_build_annotations` after their own validators). All **3** `DEFERRED_META_KEYS` entries are genuinely unshipped, each carded on the Beta line, each rejected before any other shape gate, parametrized by `tests/types/test_base.py::test_meta_rejects_each_deferred_key`. **The original `Meta.interfaces` mistake this spec exists to prevent — a key validated but never applied — is not repeated anywhere.** One adjacent shape checked because it looks like a violation and is not: `DjangoTypeDefinition.fields_class` exists as a field but is documented as forward-reserved and is never populated, which is the *reverse* of the failure the promotion rule forbids.
- **The `spec-006` inbound title dependency is intact and needs no follow-up.** `docs/SPECS/spec-006-public_surface-0_0_3.md:108` cites spec-005's `### Accepted vs deferred Meta keys` **by title**. R2 dropped only the `(shipped in 0.0.3)` parenthetical, which sits outside the quoted substring. Verified from the sibling, which this cycle never opened for writing. **No inbound break to defer.**
- **R2's re-key of two layer-1 rationale entries after retitling their spec sections is settled.** `worker-1.md` rule 3 ("every in-page anchor still resolves") and rule 4 (append-only) are in direct conflict after a retitle; R2 updated the two link-definition targets and added a one-sentence parenthetical naming each old title, rewriting **no** recorded content. Worker 3 declined the charge R2 invited: *a key is not a record, and a dangling anchor is the larger defect.*
- **Editing `## Standing note` was right, and is distinguished from item 7 on purpose.** It is R1-written but is an **analytical coda** rather than a record of what a pass moved, and the clause corrected was a measurable factual premise that measures false — the two `**Future direction.**` blocks are **245 words versus 112**, not "the same length", and the block that fared worse is also the shorter. Leaving a false premise standing under a "record" defence would have been worse than the edit.
- **No contract-level finding was surfaced by any pass of this cycle**, and each pass checked before deciding not to escalate. Every finding was a defect against an existing contract, against a measurement, or against a record. **Nothing turns on which contract the package should offer, so there is no maintainer decision pending on this cycle other than the `bld-003-*` restoration (catalog item 12) and the dispatch of R3.**

### Spec status-line re-verification (owed by every Worker 1 spawn)

Read `docs/SPECS/spec-005-django_type_contract-0_0_3.md` lines 1-5 at their current content. The spec carries **no `Status:` / owner / target-release / predecessor header block** — `:1` is the title, `:3` the companion-pointer paragraph, `:5` `## Problem statement`. Spec-005 predates that header convention. Established at R1, confirmed through R2, and still true.

Nothing in those lines is a status line this build has falsified: `:3` describes the move accurately and its `[spec-005-rationale]` target resolves on disk. **The falsified status content — `## Current state`'s "0.0.3 shipped (in flight)" framing — no longer exists**, R2 having removed the section whole. Both `(shipped in 0.0.3)` suffixes, the `(alpha constraint)` qualifier, and the `(deferred to a future spec)` qualifier are also gone; **the spec now carries no version stamp at all.** `grep -Ei 'as of|previously|in flight|shipped in|amend|retract'` over the spec returns only `:3`'s companion pointer, which `worker-1.md` rule 1 requires.

**No edit was needed and none was made**, so `### Spec changes made (Worker 1 only)` below reads `None.`

### Verification commands run at this gate, each result quoted

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` -> **`OK: 7 terms - all have glossary entries and at least one spec link.`** exit 0. **Character-identical to the plan's pre-flight step-6 baseline** — which is the property both R1 and R2 could have silently broken, since the plan's own CORRECTION establishes that **six of the seven anchors are single points of failure** and four of those sat in falsified prose before R2. After R2 no anchor sits in falsified prose, because none survives.
- `uv run python scripts/check_trailing_commas.py --check` on the spec, the rationale, and this artifact -> **exit 0**, all three; re-run after the last edit to this file.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> **`OK: 49 done cards have glossary links.`** exit 0. **Read-only `--check` form only; the writing sync form was never invoked at this gate.**
- `git rev-parse HEAD` -> `bca1ccf180489918da0a522d5a711af013b482c7`, re-derived rather than quoted from any artifact.
- `git log -1 --format='%h %s' -- docs/SPECS/spec-005-django_type_contract-0_0_3.md` -> `bca1ccf1 docs(spec-005): reconcile the DjangoType contract with HEAD and extract its rationale` — this cycle's own commit, so the work landed rather than being swept into a concurrent session's commit. Checked with `git log` and `git show --stat`, never with `git status` alone.
- No `git stash` / `checkout` / `restore` / `worktree` at any point. No branch created or switched. Nothing committed. No `--cov*` flag in any command in any form other than `--no-cov`.

### Every count in this artifact, with the command that produced it

`BUILD.md` `## Claims are proven mechanically` — and this cycle spent **three review rounds** on mis-measured numbers, with the recurring trap being a figure lifted from something adjacent (a source comment's clause count, a remembered section shape, a token-occurrence count) rather than derived from its population. **Every figure below was measured as it was written, and none was copied from an artifact.**

| Figure | Command | Result |
|---|---|---|
| suite result | `uv run pytest --no-cov` | `5635 passed, 40 skipped in 64.60s` |
| files ruff-formatted | `uv run ruff format --check .` | `418 files already formatted` |
| working-tree paths | `git status --porcelain \| wc -l` | 12 before this artifact was written, 13 after |
| cycle commit contents | `git show --stat bca1ccf1` | 5 files, 3,091 insertions / 77 deletions, all under `docs/` |
| package/test diff | `git diff -- django_strawberry_framework/ tests/ \| wc -l` | 0 |
| dirty `.py` paths | `git status --porcelain \| grep -c '\.py$'` | 0 |
| `examples/` diff | `git diff --stat -- examples/` | `db.sqlite3 \| Bin 5050368 -> 5050368 bytes` (concurrent writer) |
| deleted `bld-003-*` | `git status --short -- docs/builder/ \| grep '^ D' \| wc -l` | **3** (not the plan's 4) |
| `bld-003-final.md` | `git diff --stat -- docs/builder/bld-003-final.md` | empty, exit 0 — on disk, byte-identical to HEAD |
| spec now | `wc -l -c docs/SPECS/spec-005-…md` | 122 lines / 13,373 bytes |
| spec pre-cycle | `git show ff03c137:docs/SPECS/spec-005-…md \| wc -l -c` | 154 lines / 13,346 bytes |
| spec diff | `git diff --numstat ff03c137 HEAD -- docs/SPECS/spec-005-…md` | `45  77` |
| rationale | `wc -l -c docs/SPECS/appx/spec-005-…-rationale.md` | 713 lines / 51,373 bytes |
| closed artifacts read | `wc -l docs/builder/bld-005-r{1,2}-*.md` | 731 / 1,298 |
| R3 artifact | `ls docs/builder/bld-005-r3-*` | does not exist |
| R2 findings | `grep -cE '^#### (M\|L)[0-9]+ ' docs/builder/bld-005-r2-…md` | **16** — 6 Medium (M1-M6), 10 Low (L1-L6, L9-L12); 14 closed, 2 open |
| R2 review rounds | `grep -cE '^## Review \(Worker 3' docs/builder/bld-005-r2-…md` | 3 |
| R1 findings / rounds | `grep -nE '^#### ' / '^## Review \(Worker 3' docs/builder/bld-005-r1-…md` | 3 findings (1 Medium, 2 Low), 2 rounds, all closed |
| staged anchors, whole tree | `grep -rEn 'TODO\(spec-005\|TODO-(ALPHA\|BETA\|STABLE)-005' . \| wc -l` | **2** |
| staged anchors, shipped material | same, `--exclude-dir=docs/builder` | **no match (exit 1)** |
| staged anchors, board files | same, over `KANBAN.md KANBAN.html BACKLOG.md` | **no match (exit 1)** |
| `_format_unknown_fields_error` call sites | AST walk of `types/base.py` for the call expression and its enclosing function | **5** sites in **3** functions; **6** distinct `attr` labels; **7** `Meta` keys |
| `_selected_meta_targets` label sources | same AST walk over its callers | 3 (`:1393`, `:1468`, `:1533`) |
| duplication-table rows | `sed -n '/^### Eight duplications/,/^### Validation run/p' \| grep -n '^\|'` | header + separator + **9 data rows** (catalog item 13) |
| terms-CSV anchors | `cat docs/SPECS/appx/spec-005-…-terms.csv` | 7 rows, one per anchor |
| plan checklist state | `grep -n '^- \[' docs/builder/build-005-…md` | R1 `[x]`; R2, R3, final gate all `[ ]` |

### DRY check across the cycle

**No new duplication, and this is a measured negative rather than a skipped section.** The cycle's whole diff contains no executable logic (`git diff -- django_strawberry_framework/ tests/` -> 0 lines), so there is no helper, repeated literal, key, tuple shape, or parallel data flow to consolidate, and no new abstraction for the **existence challenge** to interrogate.

On the documentation axis the two delivered items partition cleanly and neither restates the other's output: R1 wrote the rationale's layer 1, R2 wrote the spec and the rationale's layer 2. The spec-versus-rationale split measures **0 non-scaffold 8-word overlap under both named tokenizers** — a figure R1 could reach under only one — with the n=6 survivors being section headings the keying rule *requires* the rationale to reproduce plus "the rejection of first-registered-wins", which two rules jointly require. That figure was re-derived by Worker 3 in two separate rounds and is not re-measured here: **both durable files are byte-identical to the state it was last derived against** (122 / 13,373 and 713 / 51,373, re-measured at this gate), and re-running a measurement over unchanged bytes records a number rather than verifying one.

Two live documentation-duplication risks the cycle named, both correctly handled:

- **The anti-inventory trap** — refusing to refresh `ALLOWED_META_KEYS` into the spec. Settled above; verified here by `grep` returning neither roster in the spec.
- **Over-absorbing the owning siblings** — `spec-010` / `spec-011` / `spec-015` / `spec-018` / `spec-019` / `spec-027` / `spec-028`. Every reference is a pointer plus a spec-005-specific requirement; no rule of theirs is restated, and none was edited. The four-case `Meta.primary` ambiguity table with its error strings stays in `docs/GLOSSARY.md`, where it already lived.

`scripts/review_inspect.py` was correctly skipped by every pass with a recorded reason: `BUILD.md` `### When to run the helper during build` triggers on a new `.py` file, a touched `optimizer/` or `types/` file, or 30+/50+ new logic lines, and the cycle touches no `.py` file at all. **Note for whoever dispatches R3**: the two authorized docstring corrections touch `types/base.py`, which **is** under `types/`, so R3's Worker 3 owes the helper run its trigger requires.

---

## Final verification (Worker 1)

- **Gate commands:** all six run in `BUILD.md` order, all six pass, each result recorded above with its real output. **The green table does not certify the cycle** — see the opening.
- **Concurrent churn:** none arose during this pass. All twelve baseline entries belong to the concurrent spec-004 cycle or to the `bld-003-*` deletions; all reported, none reverted, none restored, nothing `git checkout`-ed.
- **Floor verification:** `No floor-verification scope declared.` — the plan's declaration, confirmed against the diff rather than accepted. No floor venv built; the shared `.venv` not mutated.
- **Hot-path budget:** `none`, confirmed mechanically.
- **Failability proofs:** none owed, confirmed mechanically; no fail-open shape landed, vacuously.
- **Staged-anchor sweep:** owned by this gate because R3 never ran; re-measured, decomposed, **zero anchors in shipped material.**
- **Deferred work catalog:** **fourteen items**, authored from both closed artifacts and from R3's undone scope. The three that deserve a first read are **items 4 and 5**, the two authorized-but-unmade docstring corrections, which are the only source change this cycle sanctioned and are fully specified here so no re-derivation is needed; and **item 3**, R3's entire unrun scope, which nothing else in the repository records.
- **Checklist:** every box in the Plan's `### Dispatched findings checklist` is `- [x]` and each is discharged by named evidence in this artifact. No deferral reason is owed **for this gate's own boxes** — the cycle's deferrals are the catalog.
- **DRY:** no new duplication across the cycle; measured, not asserted.
- **Spec reconciliation:** none owed. This pass opened neither the spec nor the rationale for editing.
- **Item status audit:** R1 `final-accepted` and correctly ticked in the plan. **R2 `revision-needed` with M6 and L12 open — correctly left `- [ ]`.** **R3 never dispatched — correctly left `- [ ]`.** This gate is the fourth box and it is **not** ticked, because `final-accepted` is what licenses a tick and this artifact is `revision-needed`.

### Summary

The spec-005 residual-completion cycle **closes early and incomplete, at the maintainer's request, with its work committed at `bca1ccf1`.** Two of its three items delivered: **R1** created the missing `-rationale.md` companion (713 lines / 51,373 bytes across two layers) and **R2** reconciled the spec against HEAD — removing `## Current state` whole, removing both `Meta`-key rosters rather than refreshing them, retiring an instruction eleven-plus specs had never followed, retitling three topics, and adding two drift rows Worker 0's verified floor had missed. The spec went from **154 lines / 13,346 bytes** to **122 / 13,373**: fewer lines and *more* bytes, because R1 removed 2,344 bytes of deliberation and R2 spent most of them back on contract. All seven glossary anchors survive at exactly 1 use + 1 definition, and after R2 none sits in falsified prose because none survives.

**What did not happen is the point of this artifact.** R2 stands at `revision-needed` with two findings open — **M6**, a false demonstration under a `--follow` rename-trap lesson the cycle intends to outlive it, and **L12**, a sixth stale figure surviving under a hand-off that claims the sweep is complete. Both are against R2's own record of how a figure was measured; **neither touches the spec or the rationale**, which were confirmed byte-unchanged across two consecutive review passes and are unchanged at this gate. **R3 was never dispatched at all**, so the durable-doc audit, the three-direction cross-reference sweep, the `SpecDoc.path` and terms-CSV verification chain, and — most consequentially — **the two authorized corrections to factually-false docstrings in shipped source** are all undone. Those two docstrings are reproduced verbatim in the catalog with the full measured call-site table beside them, so whoever makes them re-derives nothing.

All six gate commands pass: `5635 passed, 40 skipped`, Django's system and migration checks clean, and the read-only lint/format/whitespace gate clean across 418 files. `check_spec_glossary`, `check_trailing_commas`, and `import_spec_terms --check` all exit 0. Zero staged anchors survive in shipped material — the sweep R3 was to own, run here instead. **No source, test, or `examples/` file was touched by any item**, proven three ways rather than asserted.

`Status: revision-needed`. **Worker 0 does not mark the plan's final checkbox.** What the maintainer decides next — dispatch R3, close R2's two findings, accept the cycle as-is with the catalog as the record, or restore the three `bld-003-*.md` files — is a maintainer decision, and the catalog is written to make each of them cheap.

### Spec changes made (Worker 1 only)

**None.** This pass edited no spec, no rationale, no terms CSV, no `CHANGELOG.md`, no `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `docs/TREE.md` / `docs/README.md` / `examples/fakeshop/db.sqlite3`, no source, no test, no sibling spec, neither closed `bld-005-*` artifact, and not Worker 0's build plan. The three deleted `bld-003-*.md` files were not restored, and `docs/builder/bld-003-final.md` and `docs/builder/bld-004-final.md` were read but not moved or edited. Its only writes are `docs/builder/bld-005-final.md` and `docs/builder/worker-memory/spec-005-worker-1.md`. Nothing was committed and no branch was created or switched.

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
