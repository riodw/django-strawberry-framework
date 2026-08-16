# Build: Final test-run gate — spec-010 residual-completion cycle

Spec reference: `docs/SPECS/spec-010-foundation-0_0_4.md` (whole file; the cycle's reconciled contract)
Rationale companion: `docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md`
Build plan: `docs/builder/build-010-foundation-0_0_4.md`
Status: final-accepted

**Shape note.** This is `docs/builder/BUILD.md` `## Final test-run gate`, the cycle's last pass, and it has **no Worker 2 and no Worker 3 phase**: `docs/builder/worker-1.md` `## Final test-run gate` gives the whole gate to Worker 1. The `## Build report (Worker 2)` and `## Review (Worker 3)` sections of `docs/builder/ARTIFACT.md` are therefore not applicable, and the gate record lives under `## Gate report (Worker 1)` below, carrying each command's **real** result. The cycle produces no `bld-integration.md`; the build plan's `## Artifact list` records why (it lands one test file's worth of source, so there is no cross-slice DRY surface), and the integration pass's two live obligations are folded in here — the read of all four closed artifacts, and the staged-anchor sweep. Same disposition, and the same reason, as the spec-003 cycle.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, and for a structural reason rather than a skip: `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning` gates *proposing helper-like logic*, and this pass proposes none — it writes two Markdown files. The whole cycle's executable diff is two test paths and **zero package source**, measured below, so there is no package surface an inventory could speak to.
- **Existing patterns reused.** The gate's command list is `docs/builder/BUILD.md` `## Final test-run gate` verbatim, in its declared order; the `### Deferred work catalog` shape is that same section's, including its no-deferrals literal; the artifact's single-pass shape and the item-keyed catalog are `docs/builder/bld-003-final.md`'s, which is the worked precedent for exactly this cycle type.
- **New helpers justified.** None; this pass writes two Markdown files and no code.
- **Duplication risk avoided.** One live risk, and it is the precedent cycle's recorded trap: a catalog assembled from the **most recent** artifact rather than from all four both **drops** items carried once (R1's three notes appear in no later artifact; R2's `constants.py` obligation is restated by R2b only to say it does *not* apply to R2b) and **double-counts** an item whose carrier shifted (the failability residue is stated in R2b's build report, its review, *and* its final verification — one item, three sections). The catalog below is therefore keyed by **item**, names every carrying artifact section per bullet, and states the licensing clause where one exists.

### Implementation steps

1. Read the required standing docs, the active spec, the active rationale, the build plan (including `### Baseline exception for the final test-run gate`), and **all four** closed `bld-010-*` artifacts in full, plus `bld-003-final.md` read-only as precedent (`docs/builder/BUILD.md` `## Cross-slice integration pass` step 1 — no "as needed").
2. Re-derive `HEAD` and the working tree; enumerate this cycle's own paths and confirm nothing outside them was written; confirm mechanically that no package source changed.
3. Run every gate command in `docs/builder/BUILD.md` `## Final test-run gate` order and record each one's real result, applying the plan's baseline exception under its three stated limits.
4. Confirm both declared floor-verification records exist with resolved versions and results, and that the shared `.venv` was never mutated — read, never recalled.
5. Run the staged-anchor sweep and publish its decomposition; state the DRY check as a measured result.
6. Author the `### Deferred work catalog` by walking all four artifacts, keyed by item.
7. Re-verify the spec's status lines; set `Status:`; append a memory entry.

### Test additions / updates

None. This pass lands no source and no test; the gate itself is the verification, and its full-sweep command is recorded below.

### Implementation discretion items

None reserved. The gate has no downstream worker, so nothing is delegable.

### Dispatched findings checklist

Spec-010 has no live `## Slice checklist` and this is not a review round, so per `docs/builder/worker-1.md` planning step 8 the boxes below are the gate's own obligations, drawn from `docs/builder/BUILD.md` `## Final test-run gate` and `## Floor verification`, `docs/builder/worker-1.md` `## Final test-run gate`, and the build plan's `### Baseline exception for the final test-run gate`. Worker 1 both performs and ticks; there is no later pass to audit them, so each box cites the evidence in this artifact that discharges it.

- [x] `uv run pytest --no-cov` run, full sweep across all three test trees, **no `--cov*` flag in any form**, real result recorded including its one failing row.
- [x] Every failing row attributed: node id, whether the file is in this cycle's diff, whether it is baseline-dirty, and the read-only `git show HEAD:` evidence.
- [x] `uv run python examples/fakeshop/manage.py check` run and recorded.
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` run and recorded.
- [x] `uv run ruff format --check .` run read-only, never `--fix`, and recorded.
- [x] `uv run ruff check .` run read-only, never `--fix`, and recorded.
- [x] `git diff --check` run and recorded.
- [x] `HEAD` and `git status --porcelain` re-derived rather than quoted from the plan; this cycle's paths enumerated and nothing outside them written.
- [x] **No package source changed** — confirmed mechanically, `types/base.py` clean and `types/finalizer.py` carrying only the concurrent session's unchanged hunk (md5 re-derived).
- [x] No `ACTIVE-MUTATION.json` marker survives anywhere.
- [x] Floor verification confirmed for **both** declared scopes (R2 and R2b), records read with resolved versions and results, and the shared `.venv` read rather than recalled.
- [x] All four closed artifacts read in full — the first folded-in integration obligation.
- [x] Staged-anchor sweep run with its decomposition published, not a bare number — the second folded-in integration obligation.
- [x] DRY check across the cycle stated as a **measured** result rather than a skipped section.
- [x] `### Deferred work catalog` authored from **all four** closed artifacts, keyed by item, with every carrying artifact section named.
- [x] Spec status-line re-verification performed and recorded.
- [x] No package source or test file written; no spec, rationale, `CHANGELOG.md`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, or `db.sqlite3` written; no closed artifact and not Worker 0's build plan edited; no baseline-dirty path touched; no commit, no branch, no `git stash` / `checkout` / `restore` / `worktree`.

---

## Gate report (Worker 1)

### Working tree, re-derived

`HEAD` and the tree are read fresh. The build plan warns that its own numbers were stale within minutes, and every pass of this cycle recorded a different one (47 -> 58 -> 70 -> 77 -> 87 -> 95 -> 107 -> 126 -> 128 -> 141 -> 143).

```text
git rev-parse HEAD              -> 054de9dd37a2c4181fb2a91ded57f4823a1b5220   (unmoved for the whole cycle)
git status --porcelain | wc -l  -> 146
```

**This cycle's own paths — nine, and every one accounted for:**

```text
git status --porcelain -- <the nine paths>
 M docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md      R1 + R2 + R2b + R3
 M docs/SPECS/spec-010-foundation-0_0_4.md                     R1 + R2 + R3
 M tests/types/test_definition_order.py                        R2 (2 rows) + R2b (1 row)
?? docs/builder/bld-010-r1-spec_reconciliation.md
?? docs/builder/bld-010-r2-lazy_override_coverage.md
?? docs/builder/bld-010-r2b-assigned_override_coverage.md
?? docs/builder/bld-010-r3-doc_completion_archive.md
?? docs/builder/build-010-foundation-0_0_4.md                  Worker 0's plan
?? tests/types/fixtures/lazy_relation_target_module.py         R2, new
```

The tenth is this artifact; the eleventh is `docs/builder/worker-memory/worker-1.md`, which is gitignored scratch. **Nothing outside that set was written by any pass of this cycle.**

The remaining **137** paths are the concurrent maintainer session's `0.0.14` work, plus a second concurrent cycle's. Per `AGENTS.md` rule 34 and `START.md` `## Concurrent sessions`, none was edited, reverted, staged, or `git checkout`-ed.

**New churn since R3's close, reported and positively attributed rather than inferred.** `KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3` are dirty and were not in the plan's baseline list. R3 recorded that its stop-and-escalate condition did not fire and that it made no kanban edit, so attribution needed evidence, and the diff supplies it:

```text
git diff --numstat -- KANBAN.md KANBAN.html examples/fakeshop/db.sqlite3
1  1   KANBAN.html
2  3   KANBAN.md
-  -   examples/fakeshop/db.sqlite3   (binary)
```

**Further churn appeared mid-pass, and is reported rather than reverted** (`AGENTS.md` rule 34; the build plan's `## Baseline-dirty out-of-scope files` closes with the same instruction). After the six gate commands had run and while this artifact was being written, the tree moved from **146** to **151** paths. Four of the five are the concurrent `0.0.14` review cycle's new untracked scratchpads under `docs/review/` — `rev-routers.md`, `rev-scalars.md`, `rev-schema.md`, `rev-sets_mixins.md` — which `AGENTS.md` rule 22 forbids touching regardless; the fifth is this artifact. **None was edited, reverted, or staged**, and none changes a result above: they are `.md` files, so `pytest` cannot execute them and `ruff format --check` / `ruff check` cannot see them, and `git diff --check` was **re-run after they appeared** and still exits 0. The plan's baseline exception would cover them in any case, but no gate result needs the cover.

`git diff -- KANBAN.md` is **entirely inside the `DONE-011-0.0.4` card body** — its `#### Scope` and `#### Card references` rows, rewritten to the wording `docs/builder/bld-011-r3-kanban_card_body.md` (a *different* cycle's artifact, present untracked in this tree and reading `Status: final-accepted`) declares as its deliverable. The one `grep -c 'spec-010\|DONE-010'` hit inside that diff is the `DONE-010-0.0.4` heading appearing as trailing **context**, not a changed line. `DONE-010-0.0.4`'s own body is byte-unmoved. **Not edited, not reverted, changes no result below** — a `.md`/binary trio that `pytest` cannot execute and `ruff` cannot see, and `git diff --check` was run after it appeared and exits 0.

**The cycle lands no package source**, which is what makes the baseline exception's attribution decidable:

```text
git status --porcelain -- django_strawberry_framework/            -> 38 paths, ALL the concurrent session's, NONE this cycle's
git status --porcelain -- django_strawberry_framework/types/base.py      -> (empty; clean)
git status --porcelain -- django_strawberry_framework/types/finalizer.py -> M   (concurrent session's)
git diff -- django_strawberry_framework/types/finalizer.py | md5         -> 91a39c748dc31b73b86f15752e9ff2d9
find . -name 'ACTIVE-MUTATION.json' -not -path './.git/*' | wc -l        -> 0
```

- **`types/base.py` is clean.** R2's failability proof and Worker 3's independent re-run both mutated it and both proved a byte-identical restore; the file carries no residue of either.
- **`types/finalizer.py`'s diff md5 is `91a39c748dc31b73b86f15752e9ff2d9`, identical to the figure R2b recorded across three passes** — and now a fourth. An unchanged diff md5 proves two things in one number: no worker mutated the file, and the concurrent session has not written to it since. Had it changed, that would have meant the other session wrote again, never that a worker did.
- The boundary R2b's owed proof targets is present and its anchor still unique: exact 12-space anchor -> **1** occurrence, naive token `consumer_assigned_relation_fields` -> **2** (measured by `str.count` over the file text, occurrences not lines).

**The cycle's executable diff, measured:**

```text
git diff --numstat -- tests/types/test_definition_order.py      -> 216  0
git diff -- tests/types/test_definition_order.py | grep -c '^-[^-]' -> 0
git diff --numstat -- docs/SPECS/spec-010-foundation-0_0_4.md   -> 186  118
git diff --numstat -- docs/SPECS/appx/…-rationale.md            -> 614  7
```

216 added lines and **zero deleted** in the one tracked test file, plus one new untracked fixture module. No existing row was re-pinned, weakened, or renamed by either R2 or R2b.

### Gate commands, in `BUILD.md` order

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **FAIL (exit 1)** — `1 failed, 5723 passed, 40 skipped in 98.96s`. The one failing row is attributed below and is covered by the plan's baseline exception. |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).`, exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 |
| 4 | `uv run ruff format --check .` | **PASS** — `419 files already formatted`, exit 0 |
| 5 | `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0 |
| 6 | `git diff --check` | **PASS** — no output, exit 0 |

Notes on the run, none of them a qualification of a result:

- **Command 1 took no coverage-shaped flag but `--no-cov`.** `pytest.ini`'s `addopts` auto-applies `--cov`, so `--no-cov` is required and is the only permitted form (`docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). **Line coverage was neither inspected nor asserted.** The run is the full sweep across all three test trees — package `tests/`, per-app `examples/fakeshop/apps/<app>/tests/`, and live `examples/fakeshop/test_query/` — which is what makes it the backstop for the order-dependent schema-registry class a focused run cannot see. **Every `tests/types/` row is green**, including all four override-shape rows and R2's discriminator.
- **Command 4 emitted one ruff warning**, `COM812 may cause conflicts when used with the formatter`. It is a configuration advisory printed on every invocation in this repo, not a formatting failure; the command exited 0.
- **Commands 4-6 are read-only.** No `--fix` was passed in any form and no file was rewritten by the gate. This pass's only writes are `docs/builder/bld-010-final.md` and `docs/builder/worker-memory/worker-1.md`.

### Command 1's failing row — attributed, not assumed

One failing row. Recorded honestly first, then attributed; the plan's exception governs what a result *blocks*, never whether it is reported.

```text
FAILED tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol
```

| Question | Answer | Evidence |
|---|---|---|
| Is the file in this cycle's diff? | **No.** | The cycle's nine paths are enumerated above; `tests/rest_framework/test_inputs.py` is not among them. The cycle lands **no** package source and exactly two test paths, both under `tests/types/`. |
| Is it baseline-dirty? | **Yes**, and so is the module it exercises. | `git status --porcelain -- tests/rest_framework/test_inputs.py django_strawberry_framework/rest_framework/inputs.py` -> ` M` on both. |
| Does the failing node exist at `HEAD`? | **No.** | `git show HEAD:tests/rest_framework/test_inputs.py` into a scratch path **outside** the repo, then count occurrences of the node name: **0** in the `HEAD` copy against **1** in the working copy. It is a row the concurrent session is currently adding. |

**This is the exception's one known instance, re-measured at the gate rather than inherited from R2's record.** The three limits the plan places on it all hold: it excuses nothing this cycle wrote (a failure in `tests/types/test_definition_order.py`, in `tests/types/fixtures/lazy_relation_target_module.py`, or anywhere under `django_strawberry_framework/` would block the gate outright, and none occurred); the attribution is proven by the read-only `HEAD` comparison rather than assumed; and the result above is the command's real one.

**No new unattributable failing row appeared.** The failing set is exactly the one row R2's Worker 3 sweep found and R2's final verification proved absent at `HEAD` — no set difference in either direction. Per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, a failing test's pre-existing-at-`HEAD` status is **not worker-verifiable at all** on a tree this dirty; the evidence above is what is available, and the row is escalated in the catalog rather than diagnosed further. No fix, no revert, no `git checkout` was attempted.

### Floor verification — both declared scopes confirmed

The canonical floor is read from `docs/builder/BUILD.md` `## Floor verification`, which is its single canonical statement: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**. Never restated from memory.

The plan scoped floor verification to **R2 only**; R2b's planning pass **widened** it to include R2b, on the ground that its row ends in a real `strawberry.Schema(query=Query)` build. Both were owned by their builder passes, and this gate is the backstop confirming it happened — not a second owner. Both records exist and both reproduce, read at the gate rather than accepted from the artifacts:

| Scope | Venv (outside the repo) | Resolved versions, as read | Focused scope | Result |
|---|---|---|---|---|
| R2 | `/tmp/dsf-floor-r2` | `Python 3.10.19`; `django 5.2.16`, `strawberry-graphql 0.316.0`, `pytest 9.1.1` | `tests/types/test_definition_order.py --no-cov` | **45 passed** (recorded by R2's builder, reproduced by R2's Worker 3) |
| R2b | `/tmp/dsf-floor-r2b` | `Python 3.10.19`; `django 5.2.16`, `strawberry-graphql 0.316.0`, `pytest 9.1.1` | `tests/types/test_definition_order.py --no-cov` | **46 passed** (recorded by R2b's builder, reproduced by R2b's Worker 3 at `46 passed in 1.47s`) |

Commands used at this gate: `<venv>/bin/python -V` and `uv pip list --python <venv>/bin/python`. Both venvs are still on disk, both are outside the working tree, and both resolve to the canonical floor exactly.

**The shared `.venv` was never mutated, and this is a reading rather than a recollection** (`docs/builder/BUILD.md` `## Floor verification`: never state its versions from memory or from a number written down):

```text
uv pip list        -> django 6.1, strawberry-graphql 0.323.2
.venv/bin/python -V -> Python 3.14.2
```

Nowhere near the floor points, so no floor install leaked in. Had one leaked, those numbers would read 5.2.16 / 0.316.0 / 3.10.

**R1 and R3 declared `none`, correctly** — both write Markdown only and touch no `.py` file, so `### When it is required`'s seams are untouched. **No planned floor verification went unrun**, so nothing here is grounds for `revision-needed`.

**One scoping limit carried forward** (Worker 3's Low from R2b, upheld by R2b's final verification and repeated here so the record is durable): **R2b's floor run evidences schema-and-type construction only.** It is **not** evidence about Strawberry's annotation-versus-resolver-return-type precedence, because the landed row's class annotation and its resolver's return annotation both name `list[ItemType]`, so the row cannot discriminate which precedence Strawberry applied. The widening stands entirely on its first ground.

### Hot-path budget

Not applicable; the plan declares `Hot-path declaration: none`. Confirmed rather than accepted: the cycle changes no package source at all (`git status --porcelain -- django_strawberry_framework/` lists only the concurrent session's paths), so nothing runs per request, per resolver, per row, per connection, or per outbound message that did not run identically before.

### Failability proofs

Confirmed as `docs/builder/worker-1.md` `### Failability and fail-open checks` requires, not accepted from a build report.

- **The cycle introduces no new boundary**, so `docs/builder/BUILD.md` `### What needs a proof, and what does not` attaches no mandatory obligation to it. Verified mechanically rather than declared: the whole executable diff is `216 insertions(+), 0 deletions(-)` in one test file plus one new fixture module, and no package source is dirty from any pass.
- **R2's proof exists and carries every required field** — boundary `types/base.py::_build_annotations` relation branch, the exact mutation, the scope as run, the pre-mutation state (`45 passed`, 0 pre-existing failures), the failing node ids **listed** (2), collection/setup errors **0**, and a byte-compared revert (`filecmp.cmp(shallow=False)` plus matching sha256). Worker 3 re-ran it at the recorded scope to an **identical node-id set**. 2 rows clears the weakly-pinned threshold.
- **R2b's on-disk proof was aborted and is still owed** — its target is dirty with the concurrent session's work, and the loop's `cp` restore would silently discard it. It is carried in the catalog **named**, with manifest path, exact command, and expected node-id set. The obligation is plan-elected diligence against a **pre-existing** boundary rather than a mandatory gate, which is what makes the deferral honest; both R2b's Worker 3 and its Worker 1 measured the substitute to an identical node-id set under independently written mutations, and closed the substitute's own named gap by proving `_attach_relation_resolvers` has exactly one call site.
- **No fail-open shape landed**, vacuously and stated rather than omitted: a fail-open shape is an expression in executable code, and the cycle's only executable diff is test assertions.
- **No mutation survives.** `types/base.py` is clean; `types/finalizer.py` carries only the concurrent session's comment-only hunk at an unchanged md5; `find . -name 'ACTIVE-MUTATION.json'` returns nothing.

### Cross-artifact read — the first folded-in integration obligation

All four closed artifacts read **in full**, as `docs/builder/BUILD.md` `## Cross-slice integration pass` step 1 requires with no "as needed", plus `docs/builder/bld-003-final.md` read-only as the worked precedent for this cycle type.

```text
grep -H '^Status:' docs/builder/bld-010-*.md
bld-010-r1-spec_reconciliation.md:Status: final-accepted
bld-010-r2-lazy_override_coverage.md:Status: final-accepted
bld-010-r2b-assigned_override_coverage.md:Status: final-accepted
bld-010-r3-doc_completion_archive.md:Status: final-accepted
```

All four `final-accepted`; all four of the plan's item checkboxes are `- [x]`; the fifth box is this gate's and Worker 0 marks it. Every checklist tick in all four was audited by the pass that owned it, and the **one** `- [ ]` box in the cycle — R2b's failability box — carries its one-line deferral reason under that artifact's `### Spec changes made (Worker 1 only)` and is carried below.

The precedent cycle's artifact-walk trap was confirmed live here and is handled by construction in the catalog: keying by item is what stops R1's three notes (carried by no later artifact) being dropped, and what stops the R2b failability residue (stated in a build report, a review, *and* a final verification) being counted three times.

### Staged-anchor sweep — the second folded-in integration obligation

`docs/builder/BUILD.md` `## Cross-slice integration pass` step 6. **The mechanical test first**, because it closes the classification question by construction rather than by judgement — a staged anchor is a **source-site** marker (`AGENTS.md` rule 26), so zero in the source trees means every surviving hit is by construction a `.md` hit and therefore not a staged anchor:

```text
grep -rEn 'TODO\(spec-010|TODO-(ALPHA|BETA|STABLE)-010' django_strawberry_framework/ tests/ examples/ scripts/ | wc -l   ->  0
```

Whole-tree decomposition, published rather than reduced to a bare number (a raw count reads as a failure signal and is not one here):

```text
docs/builder/bld-010-r2b-assigned_override_coverage.md   1
docs/builder/bld-010-r3-doc_completion_archive.md        1
```

**2 matching lines across exactly two `.md` files**, both per-cycle artifacts, and both hits are prose *about* the sweep rather than anchors. Zero in the spec, zero in the rationale, zero in any source or test file, and zero in `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` — so step 6's board-card exclusion never had to be applied. This artifact does not appear in its own scan because it writes the anchor only in the escaped regex form; fencing is not what keeps a file out of the sweep, since `grep` does not know about fences. **Zero staged anchors survive.**

### DRY check across the cycle — a measured result, not a skipped section

**No new duplication.** Stated as a measurement rather than an omission, per the precedent cycle:

- **The cycle's executable diff is two test paths**, `216 insertions(+) / 0 deletions(-)` in `tests/types/test_definition_order.py` plus a 22-line pure-class-definition fixture module. That leaves **nothing to consolidate on the package axis**: no helper, no constant, no repeated literal, no key or tuple shape, no parallel data flow, and no new abstraction for the **existence challenge** to interrogate — which R2's Worker 3 nonetheless raised against the fixture module and recorded as failing, since deleting it would leave `strawberry.lazy` with no importable path to resolve.
- **What it does leave** is one axis worth checking, and both passes decided it in the plan rather than leaving it to a builder: R2's two rows and R2b's one row share a structural template with the two pre-existing override rows, and the shared assertion blocks are the contract asserted at four spellings rather than duplication. R2 bound the fixture's dotted path once as `_LAZY_TARGET_MODULE` while deliberately keeping the two `strawberry.lazy("...")` literals literal (a `strawberry.lazy(CONSTANT)` call is not the consumer shape under test); R2b decided **against** copying R2's `primary=True` discriminator, with the reason recorded, because R2b's vacuity axis is *which function* rather than *which class*. `scripts/review_inspect.py`'s **Repeated string literals** section was re-run at R2b's review and carries no literal R2b introduced.
- **On the documentation axis the four items partition cleanly** and none restates another's output: R1 rewrote falsified contracts in place and moved the deliberation out, R2 corrected the spec's own non-working worked example, R2b made the four-shape coverage sentence true by landing a row rather than by rewriting the sentence, R3 converted the links and audited the archive. The one live documentation-duplication risk R1 named — importing a later spec's contract into spec-010 — was decided against uniformly across all fifteen findings, so spec-010 gained one clause per seam and no second copy of anyone else's contract.
- `scripts/review_inspect.py` was run where `docs/builder/BUILD.md` `### When to run the helper during build` triggers (R2 and R2b both ran it against `tests/types/test_definition_order.py`, past the 50-lines-outside-the-package threshold) and skipped with a recorded reason where it does not (the fixture module, under the pure-class-definition exemption; R1 and R3, which touch no `.py` file).

### Spec status-line re-verification (owed by every Worker 1 spawn)

Read `docs/SPECS/spec-010-foundation-0_0_4.md` lines 1-10 at their **current** content. The spec carries **no `Status:` / owner / target-release / predecessor header block**: its opening is the title (an anchored glossary link), the rationale-companion pointer, then `## Purpose`. The one forward-looking line in that region is the companion pointer's list of what the rationale holds; R1 extended it in this cycle to include the reconciliation record, and R2's and R3's later rationale additions are keyed entries of the classes that pointer already names.

**Nothing in those lines is falsified by this pass**, which edits neither the spec nor the rationale. `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-010-foundation-0_0_4.md` -> `OK: 12 terms - all have glossary entries and at least one spec link.`, exit 0. **No edit was needed and none was made**, so `### Spec changes made (Worker 1 only)` below reads `None.`

### Every count in this artifact, with the command that produced it

`docs/builder/BUILD.md` `## Claims are proven mechanically` — counted as **occurrences** rather than matching lines wherever the two differ, and measured at the moment each number was written. This cycle produced one wrong inferred count already (the F20 claim that the assignment form was covered "alongside" the decorator form, inferred from a test's *name*), which is the whole reason item R2b exists.

| Figure | Command | Result |
|---|---|---|
| suite result | `uv run pytest --no-cov` | `1 failed, 5723 passed, 40 skipped`, exit 1 |
| files ruff-formatted | `uv run ruff format --check .` | `419 files already formatted` |
| working-tree paths | `git status --porcelain \| wc -l` | 146 at the gate commands; **151** after this artifact was written (4 new concurrent `docs/review/` scratchpads + this file) |
| this cycle's paths | `git status --porcelain -- <the nine>` | 9 (+ this artifact = 10 tracked-to-be) |
| dirty package sources, all concurrent | `git status --porcelain -- django_strawberry_framework/ \| wc -l` | 38 |
| `types/base.py` dirty? | `git status --porcelain -- …/types/base.py` | empty (clean) |
| `types/finalizer.py` diff md5 | `git diff -- …/types/finalizer.py \| md5` | `91a39c748dc31b73b86f15752e9ff2d9` (unchanged across 4 passes) |
| test-file diff | `git diff --numstat -- tests/types/test_definition_order.py` | `216  0` |
| test-file deletions | `git diff -- … \| grep -c '^-[^-]'` | 0 |
| spec diff | `git diff --numstat -- docs/SPECS/spec-010-…md` | `186  118` |
| rationale diff | `git diff --numstat -- docs/SPECS/appx/…-rationale.md` | `614  7` |
| KANBAN churn | `git diff --numstat -- KANBAN.md KANBAN.html` | `2 3` / `1 1`, all `DONE-011` card body |
| failing node at `HEAD` | `git show HEAD:tests/rest_framework/test_inputs.py` into a scratch path outside the repo, then `grep -o … \| wc -l` | **0** (working copy: 1) |
| staged anchors, source trees | `grep -rEn 'TODO\(spec-010\|TODO-(ALPHA\|BETA\|STABLE)-010' django_strawberry_framework/ tests/ examples/ scripts/ \| wc -l` | **0** |
| staged anchors, whole tree | same regex over `.` excluding `.git` / `.venv` | 2 lines, 2 `.md` files, both descriptive |
| `ACTIVE-MUTATION.json` markers | `find . -name 'ACTIVE-MUTATION.json' -not -path './.git/*' \| wc -l` | **0** |
| proof anchor uniqueness | `str.count` over `types/finalizer.py` | exact 12-space anchor **1**; naive token **2** |
| override-shape rows | `grep -n '^def test_…' tests/types/test_definition_order.py` | 4 shapes at `:231`, `:258`, `:287`, `:354` + the discriminator at `:428` |
| glossary check | `uv run python scripts/check_spec_glossary.py --spec …` | `OK: 12 terms`, exit 0 |
| floor venv R2 | `uv pip list --python /tmp/dsf-floor-r2/bin/python` | `django 5.2.16`, `strawberry-graphql 0.316.0`, `Python 3.10.19` |
| floor venv R2b | `uv pip list --python /tmp/dsf-floor-r2b/bin/python` | `django 5.2.16`, `strawberry-graphql 0.316.0`, `Python 3.10.19` |
| shared `.venv` | `uv pip list` / `.venv/bin/python -V` | `django 6.1`, `strawberry-graphql 0.323.2`, `Python 3.14.2` |
| `aggregate_class` / `search_fields` provenance | `git log --oneline -S … -- …/types/definition.py` | introduced `27d62919`, removed `f83bb71b` |

### Deferred work catalog

Authored from **all four** closed artifacts' `### Notes for Worker 1 (spec reconciliation)`, `### Maintainer escalations`, `What looks solid`, and review sections — not from the most recent, which would have dropped items 5-7 and 10 and triple-counted item 1. Keyed by **item**, with every carrying artifact section named.

**The two that need the maintainer's hand are items 1 and 2.**

1. **OWED, MAINTAINER-GATED — R2b's on-disk failability proof.** *Source:* `bld-010-r2b-assigned_override_coverage.md` `### Failability proofs` (Worker 2, which named the abort), `### The central judgement: Worker 2 aborted the BUILD.md proof and supplied a substitute` and `### Notes for Worker 1 (spec reconciliation)` (Worker 3), and `### 1. The unticked failability box — disposition decided` plus `### Spec changes made (Worker 1 only)` (Worker 1's deferral reason). **One item, five sections — a catalog deduping by section would count it up to five times.** *Licensing clause:* `docs/builder/BUILD.md` `### What needs a proof, and what does not` scopes the **mandatory** obligation to *new* boundaries; R2b introduces none (216 insertions of test, zero package source), so the proof was plan-elected diligence against a **pre-existing** boundary and **the deferral waives no mandatory gate**. *Description:* the target `django_strawberry_framework/types/finalizer.py` is dirty with the concurrent session's uncommitted comment-only hunk, and the proof loop's restore is a blind `cp` that would silently discard it (`AGENTS.md` rule 34). Reproduced here so it is discharged in one step:

   > **Run** `uv run python scripts/prove_failability.py docs/builder/temp-tests/r2b/proofs.json --output <path>` **once** `git status --porcelain -- django_strawberry_framework/types/finalizer.py` **is empty.** The manifest is on disk, verified unedited at this gate, and needs no change; its scratch root `/tmp/dsf-failability-r2b` is outside the repository, and its anchor (the 12-space-indented `skip_field_names=definition.consumer_assigned_relation_fields,` line with its trailing comma) was re-measured at this gate as matching **exactly once** (the naive token matches twice — do not use it). **Expected result**, from three independent in-process measurements (Worker 2's, Worker 3's, and Worker 1's audit): **2 failing rows, 0 collection/setup errors** —
   > - `tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver`
   > - `tests/types/test_definition_order.py::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver`
   >
   > **A different node-id set is a finding.**

   The substitute's one named gap — that a rebinding cannot prove the recorded anchor is the live call site — was closed by measurement: `_attach_relation_resolvers` occurs 8 times across 4 files but has **exactly one call site**, `types/finalizer.py:793`, whose `skip_field_names=` argument is the anchor line; the other 7 are the definition, an import, docstrings, and a comment. What remains unproved is only that the tool's own machinery (anchor match, `cp`/`cmp` round trip, marker file) runs clean against this manifest — procedural residue, not a gap in the evidence about the code.

2. **`examples/fakeshop/apps/kanban/constants.py` must be regenerated at commit time.** *Source:* `bld-010-r2-lazy_override_coverage.md` `### Implementation steps` (plan), `### Notes for Worker 1 (spec reconciliation)` (Worker 2), `### Documentation / release sanity` (Worker 3, which verified it real), and `### Maintainer escalations` item 3 (Worker 1). *Licensing clause:* none — it is a commit-time mechanic no worker may perform, since `git add` is the maintainer's and workers never stage. *Description:* R2 adds a new **tracked-to-be** file, `tests/types/fixtures/lazy_relation_target_module.py`. `examples/fakeshop/apps/kanban/constants.py` is rendered from `git ls-files` by `scripts/build_kanban_tracked_path_constants.py::tracked_file_paths`, and its `source-layout` / kanban pre-commit hook fails on staleness. Regenerating **now** produces no change, because the file is untracked and therefore invisible to `git ls-files`. So: after `git add tests/types/fixtures/lazy_relation_target_module.py`, run `uv run python scripts/build_kanban_tracked_path_constants.py` **before** committing, or the hook blocks the commit. Confirmed real — the tracked-path list already enumerates `tests/types/fixtures/*.py` (`grep -c "branch_module\|shelf_module" …/constants.py` -> 2). `constants.py` was not hand-edited by any pass and no regenerate was attempted.

3. **ESCALATED — the unrelated suite failure in the concurrent session's dirty area.** *Source:* `bld-010-r2-lazy_override_coverage.md` `### What looks solid` and `### Notes for Worker 1 (spec reconciliation)` (Worker 3, who first hit it in an independent full sweep) and `### Maintainer escalations` item 1 (Worker 1, who gathered the evidence); re-measured at this gate. *Licensing clause:* the build plan's `### Baseline exception for the final test-run gate`, and `docs/builder/BUILD.md` `## Claims are proven mechanically`, under which a failing test's pre-existing-at-`HEAD` status is **not worker-verifiable** on a tree this dirty — recording plus escalating discharges the obligation. *Description:* `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol` fails in the full sweep. Both the test file and `django_strawberry_framework/rest_framework/inputs.py` are baseline-dirty; the node **does not exist at `HEAD`** (`git show HEAD:` into a scratch path outside the repo -> 0 occurrences against 1 in the working copy), so it is a row the concurrent session is currently adding, not a regression this cycle could have caused. R2 reproduced it read-only for convenience: it fails at `assert shape_a == shape_b`, the differing attribute being `serializer_class` — two distinct function-local `ItemSer` classes sharing a qualname, i.e. an in-flight cache-identity assertion. The maintainer is the only party who can run a clean `HEAD` tree. **Not fixed, not reverted, not chased.**

4. **`tests/types/test_definition_order.py::test_filterset_class_resolves_across_module_boundary`'s module eviction is weaker than its comment claims — worth carding.** *Source:* `bld-010-r2-lazy_override_coverage.md` `### Notes for Worker 1 (spec reconciliation)` (Worker 3's Low, routed rather than fixed), `### Temp test verification` (the probe that measured it), the same artifact's `### Notes for Worker 1` (Worker 2's independent side observation), and Worker 1's `### Maintainer escalations` item 3. *Licensing clause:* **pre-existing at `HEAD`**, verified read-only (`git show HEAD:tests/types/test_definition_order.py` into a scratch path outside the repo carries the same `from ... import ...` pair and the same comment), and outside R2's writable set. *Description:* the row pops two fixture modules from `sys.modules` and re-imports them with `from tests.types.fixtures import branch_module, shelf_module`, under a comment asserting the pop makes the next import re-execute the module. Measured: it does not — the parent package's still-set attribute satisfies the import, so the **stale** module object comes back and `sys.modules` is never repopulated. The row passes today only because nothing imports those modules first, making it a latent order dependence of exactly the class invisible below a full parallel run. **The fix is one `importlib.import_module` per module plus a corrected comment** — which is precisely the drift R2's builder was forced into for its own rows, and why the weakness was found at all.

5. **Spec-010's `## Pre-implementation spikes` still says the Phase-0 conclusions were "written into `README.md`".** *Source:* `bld-010-r1-spec_reconciliation.md` `### Notes for Worker 1 (spec reconciliation)` item 2 — **carried by R1 alone**; no later artifact restates it. *Licensing clause:* none; it is a boundary judgement the maintainer may draw elsewhere. *Description:* at `HEAD` the schema-setup boundary, the correct/wrong-order snippet pair, and the import-boundary note all live in `docs/README.md`; the root `README.md` carries only the correct snippet. R1 fixed the two sentences stating a **current** documentation location (`## Strawberry finalization strategy` and phase-10) and deliberately left the spike record alone as a historical account of what a spike concluded and where it was recorded **at the time** — the same correct-as-history class R3 later applied twice. Flagged rather than fixed.

6. **The `### Manual annotation contract for relation fields` heading lost its `(0.0.4)` suffix in R1's pass.** *Source:* `bld-010-r1-spec_reconciliation.md` `### Notes for Worker 1 (spec reconciliation)` item 3 — **R1 alone**; re-confirmed by R3's inbound-anchor table. *Licensing clause:* none; informational. *Description:* no in-page anchor, no reference-style link definition, and no other document targets it, and R3 independently verified all five of spec-008's **anchored** inbound definitions still resolve against the current heading list. Recorded because a heading rename is the one edit class that silently breaks an inbound anchor, and the check is cheap to state and expensive to re-derive.

7. **`::test_annotation_only_relation_override_keeps_generated_resolver` does NOT pin the collection-phase short-circuit — do not cite it as though it does.** *Source:* `bld-010-r2-lazy_override_coverage.md` `### Failability proofs` (Worker 2's unpredicted measurement), confirmed independently in Worker 3's `### Independent failability re-run — measured result`, and routed in Worker 2's `### Notes for Worker 1 (spec reconciliation)`. *Licensing clause:* none; nothing in the spec asserts otherwise, so it is not a spec amendment. *Description:* the plan predicted the pre-existing annotation-only row would co-fail when `types/base.py::_build_annotations`'s consumer-authored short-circuit is deleted. It does not: the synthesized placeholder resolves back to the **same class**, so every assertion in that row still holds, and its `consumer_*` set assertions read state computed in `__init_subclass__` rather than in `_build_annotations`. **Before R2, the relation-branch short-circuit was unpinned for *every* override shape**, not merely untested for the lazy one — a stronger justification for F16 than the plan's own reasoning, and a live trap for a future reader citing that row.

8. **R2b's floor run must not be cited as evidence about Strawberry's annotation-versus-resolver-return-type precedence.** *Source:* `bld-010-r2b-assigned_override_coverage.md` `### Low: The floor-verification widening's second stated ground is not exercised by the landed row` and `### Notes for Worker 1 (spec reconciliation)` (Worker 3), upheld in `### 4. Worker 3's Low finding — the rejection is judged and upheld` (Worker 1). *Licensing clause:* a **recorded rejection** — no change requested and no re-loop; the widening stands entirely on its first ground (the row ends in a real `strawberry.Schema(query=Query)` build). *Description:* the landed row's class annotation is `list[ItemType]` and `category_items`'s return annotation is *also* `list[ItemType]`, so the SDL is identical under either precedence and the row cannot discriminate which Strawberry applied. Discriminating it would require the two to name **different** types — precisely the validation spec-010 explicitly defers — and would pin an upstream rule for no contract gain. Durably recorded in a `*Consequence to carry*` sentence in the rationale's F20 entry, and repeated in this gate's floor section.

9. **`KANBAN.md`'s `DONE-010-0.0.4` reserved-slot list is a near-miss that is correct as history — do not "fix" it.** *Source:* `bld-010-r3-doc_completion_archive.md` `### Notes for Worker 1 (spec reconciliation)` item 1 and `### Maintainer escalations`. *Licensing clause:* `docs/builder/BUILD.md` `### Generated docs are DB-backed`, and `worker-0.md` `## Closing out a kanban card` — `KANBAN.md` renders from `examples/fakeshop/db.sqlite3` and is **never** hand-edited; a change here is a DB edit plus a re-render, i.e. a Worker 0 re-partition. *Description:* the card body says `DjangoTypeDefinition` carries forward-reserved slots `filterset_class`, `orderset_class`, **`aggregate_class`**, `fields_class`, **`search_fields`**, `interfaces`. R1's F7 established that at `HEAD` only `fields_class` is reserved-and-unused, and that `aggregate_class` / `search_fields` are rejected `Meta` keys with **no slot on the dataclass at all**. The card is nonetheless accurate as a record of what `0.0.4` shipped — re-derived at this gate, `git log --oneline -S "aggregate_class" -- django_strawberry_framework/types/definition.py` and the same for `search_fields` both show the pair introduced at `27d62919` (the foundation slice) and removed at `f83bb71b`, i.e. **after** `0.0.4`. **No edit is owed.** Recorded so a future reader does not close it helpfully in passing.

10. **`KANBAN.md:335-336` carries two carded, still-open observations about spec-010, and R3's clean Class-3 result does not close them.** *Source:* `bld-010-r3-doc_completion_archive.md` `### Notes for Worker 1 (spec reconciliation)` item 2. *Licensing clause:* both are owned by a board card, not by this cycle; the second additionally needs the maintainer to authorize a shipped-spec edit before any pass may start. *Description:* (a) spec-010's two inbound citations into spec-009 both resolve to something other than the claim they are cited for, and the underlying cause is that `spec-009 #"### Layer 3: Finalization trigger"` still presents hybrid auto-finalization as the preferred direction after that direction was rejected — so the fix is a **spec-009 residual reconciliation cycle**, not two pointer edits. (b) spec-010 carries the board's largest single `AGENTS.md` rule-27 debt (42 raw `path:NN` occurrences on 30 lines as of 2026-08-14, of which 20 on 15 lines are in-repo and forbidden), and closing it requires retiring `## Note on source line references` in the same change. **R3 verified only that the three `#"…"` citation targets *exist*; it did not and could not adjudicate whether each supports the claim it is cited for**, which is the carded work. This cycle honoured the plan's standing constraint and never opened spec-009 in either direction, since a concurrent session is reconciling it.

11. **Cosmetic, deliberately not acted on: R2's lazy row docstring calls itself "The fourth shape".** *Source:* `bld-010-r2b-assigned_override_coverage.md` `### 2. The spec sentence this sub-item existed to make true`. *Licensing clause:* `docs/builder/ARTIFACT.md` `## Re-pass sections` — R2 is closed and its prior sections are never edited. *Description:* the spec lists that shape **second**, and R2b's own row correctly says "third listed". The ordinal is prose in a docstring rather than a contract, and re-opening a `final-accepted` item to renumber it is not worth a re-loop. **Low-tier cosmetic only.**

12. **Per-cycle scratch awaiting closeout deletion.** *Source:* `bld-010-r2b-assigned_override_coverage.md` `### Temp test verification` and `### 5. Mechanical confirmations`, and `bld-010-r2-lazy_override_coverage.md` `### Temp test verification`. *Licensing clause:* `docs/builder/BUILD.md` — `docs/builder/temp-tests/` is untracked scratch cleared per cycle by `scripts/clean_up.py`; **the deletion belongs to closeout, not to any pass**, and this gate did not perform it. *Description:* `docs/builder/temp-tests/r2/` holds R2's and Worker 3's proof manifests and emitted reports plus three probes; `docs/builder/temp-tests/r2b/` holds `proofs.json` (which item 1 still needs, so **do not delete it before that proof runs**) and `test_sdl_assertion_is_non_distinguishing.py`, whose recorded disposition is deleted-not-promoted — promoting it would ship a permanently-passing row that pins nothing. The out-of-repo scratch (`/tmp/dsf-failability-r2b/`, `/tmp/dsf-w3-r2b/`, `/tmp/dsf-floor-r2`, `/tmp/dsf-floor-r2b`) is outside the tree and needs no repo action.

**Two items the cycle closed rather than deferred**, recorded so a reader does not re-open them: `docs/GLOSSARY.md#definition-order-independence`'s lazy-shape bullet (R1's note 1) is **unspecific rather than wrong** — it elides the annotated type, so it names the marker without committing to a placement — and is DB-generated, so no edit is owed and none was made; and R2's escalation that the four-shape claim was true for only three of four is **closed by R2b's row**, with the four shapes now mapping one-to-one onto four structurally different rows at `:231`, `:258`, `:287`, and `:354` (the row at `:428` is the lazy row's discriminator, not a fifth shape — counting it would be the doubling that check exists to catch).

---

## Final verification (Worker 1)

- **Gate commands:** all six run in `docs/builder/BUILD.md` order. Five pass; command 1 fails on exactly one row, recorded with its real output and attributed by read-only `HEAD` comparison to a file this cycle never wrote.
- **Baseline exception applied, under all three of its limits.** It excuses nothing this cycle wrote — every `tests/types/` row is green, no package source is in the diff, and a failure in either of the cycle's two test paths or anywhere under `django_strawberry_framework/` would have blocked the gate outright. The attribution is proven rather than assumed. And the exception governed only what the result *blocks*: the result itself is reported exactly as the command produced it.
- **Working tree:** re-derived at 146 paths at the gate commands, of which **nine** are this cycle's and 137 are concurrent sessions'; 151 by the end of this pass. New churn (`KANBAN.md` / `KANBAN.html` / `db.sqlite3`) appeared since R3 and is positively attributed to a *different* cycle's `DONE-011-0.0.4` card-body item by reading its diff, and four more `docs/review/` scratchpads appeared while this artifact was being written. All reported, none reverted, and none changes a result.
- **No package source changed.** `types/base.py` clean, `types/finalizer.py` at the unchanged concurrent md5 `91a39c748dc31b73b86f15752e9ff2d9` for a fourth consecutive pass, no `ACTIVE-MUTATION.json` anywhere.
- **Floor verification:** both declared scopes (R2 as planned, R2b as widened) were owned and run by their builder passes; both records exist at `/tmp/dsf-floor-r2` and `/tmp/dsf-floor-r2b`, both resolve to Django 5.2.16 / strawberry-graphql 0.316.0 / Python 3.10.19, and both passed. **No planned floor verification went unrun.** The shared `.venv` was read (Django 6.1 / strawberry-graphql 0.323.2 / Python 3.14.2) and was never mutated.
- **Integration obligations:** all four closed artifacts read in full and all four `final-accepted`; the staged-anchor sweep returns **zero** in every source tree and two descriptive `.md` mentions, decomposition published.
- **DRY:** no new duplication, measured rather than skipped — the executable diff is two test paths with zero package source, so there is nothing to consolidate, and the one live axis (four near-identical override rows) was decided in the plans with reasons on record.
- **Checklist:** every box in the Plan's `### Dispatched findings checklist` is `- [x]`, each discharged by evidence in this artifact. No deferral reason is owed for this pass's own boxes.
- **Deferred work catalog:** twelve items, keyed by item and drawn from all four artifacts. Items 1 and 2 are maintainer actions with exact commands; item 3 is an escalation; the rest are notes, recorded rejections, and do-not-"fix" markers.
- **Spec reconciliation:** none owed. This pass opened neither the spec nor the rationale for writing.

### Summary

The spec-010 residual-completion cycle closes. Its four items delivered the spec-versus-`HEAD` reconciliation of fifteen falsified claims with a keyed rationale entry for each (R1), the `strawberry.lazy` relation-override coverage that also proved the spec's own worked example of that shape had never worked (R2), the `strawberry.field(resolver=...)` relation-assignment row that made "Tests cover all four shapes" true by landing a row rather than by rewriting the sentence (R2b), and the archive audit that closed three broken links plus one masked-rot link a checker could never have flagged (R3) — landing **216 lines of test, one fixture module, and no package source**, which this gate confirmed mechanically rather than accepted from the plan.

**Five of six gate commands pass. Command 1 fails on one row, and the failure is the plan's baseline exception operating exactly as it was written for**: `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol` does not exist at `HEAD`, lives in a file this cycle never wrote, and sits beside the concurrent session's dirty `rest_framework/inputs.py`. Everything the cycle owns is green, at the shared `.venv` and at the floor, and Django's system and migration checks plus the read-only lint / format / whitespace gate are clean across 419 files. Zero staged anchors survive anywhere in the tree.

The catalog carries twelve items. **Item 1 is the one real residue**: R2b's on-disk failability proof is still owed, blocked by a file only the maintainer can clean, and it is carried forward *named* — manifest path, exact command, precondition, and the expected two-node-id set — rather than waived. It waives no mandatory gate, because R2b introduces no new boundary; its evidentiary work is already done three times over in-process. **Item 2 is the one that will block a commit if missed**: regenerate `examples/fakeshop/apps/kanban/constants.py` after staging the new fixture file.

`Status: final-accepted`. Worker 0 marks the plan's final checkbox; the maintainer's review and commit are next.

### Spec changes made (Worker 1 only)

None. This pass edited no spec, no rationale, no terms CSV, no `CHANGELOG.md`, no `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `examples/fakeshop/db.sqlite3`, no source, no test, no closed artifact, and not Worker 0's build plan. Its only writes are `docs/builder/bld-010-final.md` and `docs/builder/worker-memory/worker-1.md`. Nothing was committed, no branch was created or switched, and no `git stash` / `checkout` / `restore` / `worktree` was used at any point.

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
