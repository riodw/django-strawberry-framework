# Build: Final test-run gate — spec-004 residual-completion cycle

Spec reference: `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` (whole file; the cycle's reconciled contract)
Companion: `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` (the cycle's new deliberative layer)
Build plan: `docs/builder/build-004-optimizer_beyond-0_0_3.md`
Status: final-accepted

**Shape note.** This is `docs/builder/BUILD.md` `## Final test-run gate`, the cycle's last pass, and it has no Worker 2 or Worker 3 phase: `worker-1.md` `## Final test-run gate` gives the whole gate to Worker 1. The `## Build report (Worker 2)` and `## Review (Worker 3)` sections of `docs/builder/ARTIFACT.md` are therefore not applicable, and the gate record lives under `## Gate report (Worker 1)` below, carrying each command's real result. The cycle produces no `bld-integration.md`; the build plan's `## Artifact list` records why (no item landed source, so there is no cross-slice DRY scan to run), and the integration pass's two live obligations were folded in — the staged-anchor sweep into R3, the cross-artifact read into this gate.

**Read this first if you have read none of the three item artifacts.** `### Cycle summary — what the three items delivered` states what shipped and what moved; `### Deferred work catalog` is the deliverable the maintainer asked for by name and is the next spec author's reading list.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, and for the cycle's standing reason rather than a skip: `worker-1.md` `### Package-wide helper inventory before helper planning` gates *proposing helper-like logic*, and this pass proposes none. It also could not be current-by-reuse or stale-by-neglect either way — `git diff -- django_strawberry_framework/ tests/ | wc -l` returns **0**, so nothing under the package has moved for the whole cycle. No inventory was refreshed and none was needed.
- **Existing patterns reused.** The gate's command list is `BUILD.md` `## Final test-run gate` verbatim, in its declared order; the `### Deferred work catalog` shape is that same section's, including its no-deferrals literal. The artifact's overall shape is the immediately-preceding residual cycle's gate, `docs/builder/bld-003-final.md`, read in full before anything here was written.
- **New helpers justified.** None; this pass writes two Markdown files and no code.
- **Duplication risk avoided.** Two live risks, both realised in this cycle and both handled by construction below. **First**, a catalog assembled from the *most recent* artifact rather than from all three drops every item only an earlier artifact carries — and this cycle has **two** such items, not one: the eleventh (R1's precision note against the durable rationale, which R2 never opened) and the twelfth (R1's Worker 3 scaffolding-overlap DRY finding, which neither R2 nor R3 carries). **Second**, an item cited at two different line numbers double-counts if the catalog dedupes by citation instead of by item; the eleventh is exactly that — R1 cites B8's per-slice pointer at spec `:151` against the pre-R2 216-line spec, R3 and this gate cite it at `:171`. The catalog below is therefore keyed by **item**, names every carrying artifact section per bullet, and states the line-number divergence inside the bullet that owns it.

### Implementation steps

1. Read the required standing docs, the active spec, the active rationale, the build plan, and all three closed `bld-004-*` artifacts (`BUILD.md` `## Cross-slice integration pass` step 1 — no "as needed").
2. Re-derive `HEAD` and the working-tree state rather than trusting the plan's recorded hash, and prove no concurrent commit swept this cycle with `git log -1 -- <spec>`, never `git status` alone.
3. Run every gate command in `BUILD.md` `## Final test-run gate` order and record each one's real result.
4. Record the floor-verification disposition for the plan's declared scope, written out rather than omitted.
5. Author the `### Deferred work catalog` by walking all three artifacts' `### Notes for Worker 1 (spec reconciliation)`, `### What looks solid`, `### DRY findings`, and final-verification sections, keying by item.
6. Confirm the three build-plan corrections R3 routed to Worker 0 now read correctly.
7. Set `Status:` and append a memory entry.

### Test additions / updates

None. This pass lands no source and no test; the gate itself is the verification, and its full-sweep command is recorded below.

### Implementation discretion items

None reserved. The gate has no downstream worker, so nothing is delegable.

### Dispatched findings checklist

Spec-004 has no `## Slice checklist` and this is not a review round, so per `worker-1.md` planning step 8 the boxes below are the gate's own obligations, drawn from `BUILD.md` `## Final test-run gate`, `worker-1.md` `## Final test-run gate`, and the build plan's `**Baseline exception for the final test-run gate**`. Worker 1 both performs and ticks; there is no later pass to audit them, so **each box cites the evidence in this artifact that discharges it**.

- [x] `uv run pytest --no-cov` run, full sweep across all three test trees, no `--cov*` flag in any other form, result recorded — `### Gate commands, in BUILD.md order` row 1; line coverage neither inspected nor asserted.
- [x] `uv run python examples/fakeshop/manage.py check` run and recorded — row 2.
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` run and recorded — row 3.
- [x] `uv run ruff format --check .` run read-only, never `--fix`, and recorded — row 4, with the standing `COM812` advisory explained in the notes beneath the table.
- [x] `uv run ruff check .` run read-only, never `--fix`, and recorded — row 5.
- [x] `git diff --check` run and recorded — row 6.
- [x] Floor verification: the plan's declared scope is `none`, so `No floor-verification scope declared.` is **written out** rather than the section silently omitted — `### Floor verification`.
- [x] `### Deferred work catalog` authored from **all three** closed artifacts, keyed by item, with every carrying artifact section named per bullet — `### Deferred work catalog`.
- [x] The two items that live only in an *earlier* artifact are carried: item 11 (R1's final verification) and item 12 (R1's Worker 3 `### DRY findings`) — catalog items 11 and 12, each with the grep proving R2 and R3 do not carry it.
- [x] The one item cited at two line numbers is carried **once**, at its re-derived current line — catalog item 11, spec `:171` not `:151`.
- [x] Deferrals are distinguished from settled judgements — `### Settled judgements, deliberately NOT in the catalog`, covering R2's five recorded-not-filed residues (four decisions, one deferral) and R1's closed handoff rows.
- [x] The baseline exception is applied to what a result *blocks*, never to whether it is recorded — `### Working tree, re-derived` and the gate table; every result below is the command's real one and every command passed, so the exception is inert on the facts.
- [x] The three build-plan corrections R3 routed to Worker 0 confirmed against the plan on disk, with the one that is still imprecise named — `### The three build-plan corrections, confirmed`.
- [x] Every stated count is command-produced and the command is quoted beside it — `### Every count in this artifact, with the command that produced it`.
- [x] `HEAD` re-derived rather than quoted from the plan, and `git log -1 -- <spec>` confirmed still `20a9752f` — `### Working tree, re-derived`.
- [x] No package source or test file written; no `git stash` / `checkout` / `restore` / `worktree`; no commit; no branch created or switched; the three deleted `bld-003-*.md` files not restored — `### Spec changes made (Worker 1 only)`.

---

## Gate report (Worker 1)

### Working tree, re-derived

`HEAD` is re-derived rather than taken from the build plan, which itself warns that any pass quoting a hash from it must re-derive (`HEAD` moved four times during this cycle: `20a9752f` → `c62e990a` → `346d6731` → `ff03c137`).

```text
git rev-parse HEAD                                                  -> ff03c1372365edcad488ff4671389d88ae145276
git log -1 --format='%h %s' -- docs/SPECS/spec-004-…-0_0_3.md       -> 20a9752f docs(spec-003): reconcile the O4 spec with HEAD and extract its rationale
```

Unmoved from R3's close on both readings. **The second is the load-bearing one**: the newest commit reaching the spec is still the *spec-003* cycle's one-clause B4 rider, so nothing of this cycle has been swept into a concurrent session's commit. Checked with `git log`, never with `git status` alone.

`git status --porcelain | wc -l` -> **16**, byte-for-byte the sixteen R3 recorded, unchanged from the start of this pass until this artifact itself was written — after which it is **17**, the seventeenth being `?? docs/builder/bld-004-final.md`. Both readings were taken; the sixteen are:

```text
 M docs/GLOSSARY.md                                        R3, regenerated from the DB (F1 + F2)
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md           R1 + R2
 M docs/SPECS/spec-005-django_type_contract-0_0_3.md       concurrent card-005 cycle
 D docs/builder/bld-003-r1-rationale_move.md               NOT this cycle's — see the plan's `### Fifth change`
 D docs/builder/bld-003-r2-spec_reconciliation.md          NOT this cycle's
 D docs/builder/bld-003-r3-doc_completion_archive.md       NOT this cycle's
 M examples/fakeshop/db.sqlite3                            R3, two `glossary_glossaryterm` rows
?? docs/SPECS/appx/spec-004-…-rationale.md                 R1 + R2
?? docs/SPECS/appx/spec-005-…-rationale.md                 concurrent card-005 cycle
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/bld-004-r2-spec_reconciliation.md
?? docs/builder/bld-004-r3-doc_completion_archive.md
?? docs/builder/bld-005-r1-rationale_move.md               concurrent card-005 cycle
?? docs/builder/bld-005-r2-spec_reconciliation.md          concurrent card-005 cycle
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
?? docs/builder/build-005-django_type_contract-0_0_3.md    concurrent card-005 cycle
```

**Eight are this cycle's, five are the concurrent card-005 cycle's, three are the `bld-003-*` deletions no pass here caused.** `docs/builder/bld-003-final.md` is on disk, does not appear in `git status`, and `git diff --stat` on it is empty — byte-identical to `HEAD`, restored by something outside this cycle. It was read in full for this gate's shape and **was not restored, moved, or edited by this pass**; the other three deletions persist and remain the maintainer's call, because restoring them means the `git checkout` `AGENTS.md` rule 34 forbids while concurrent sessions are writing this tree.

**No concurrent churn arose during this pass**, so nothing further is recorded under `AGENTS.md` rule 34 and nothing was reverted. The build plan's `**Baseline exception for the final test-run gate**` is therefore **inert on the facts** — every gate command passed, so no result is attributable to a file this cycle never wrote. The exception governs what a result *blocks*, never whether it is recorded honestly, and every result below is the command's real one.

**The cycle landed no package source and no test:**

```text
git diff -- django_strawberry_framework/ tests/ | wc -l   ->  0
git status --porcelain | grep -c '\.py$'                  ->  0
```

That is the claim that would make a `pytest` failure un-attributable to this cycle. No failure occurred, so the escalation path the dispatch reserved was not needed.

### Gate commands, in `BUILD.md` order

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `5635 passed, 40 skipped in 63.67s (0:01:03)`, exit 0 |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).` exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 |
| 4 | `uv run ruff format --check .` | **PASS** — `418 files already formatted`, exit 0 |
| 5 | `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0 |
| 6 | `git diff --check` | **PASS** — no output, exit 0 |

Notes on the run, none of them a qualification of a result:

- **Command 1 took no coverage-shaped flag but `--no-cov`.** `pytest.ini`'s `addopts` auto-applies `--cov`, so `--no-cov` is required and is the only permitted form (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). **Line coverage was neither inspected nor asserted**; the only requirement is that the suite passes, and it does. The run is the full sweep across all three test trees — package `tests/`, per-app `examples/fakeshop/apps/<app>/tests/`, and live `examples/fakeshop/test_query/` — which is what makes it the backstop for the order-dependent schema-registry class a focused run structurally cannot see.
- **Command 4 emitted one ruff warning**, `COM812 may cause conflicts when used with the formatter`. It is a configuration advisory printed on every invocation in this repo, not a formatting failure; the command exited 0 with `418 files already formatted`. Exit codes for commands 4 and 5 were re-captured on an unpiped re-run so a pipeline's exit status could not be mistaken for the tool's: **both 0**.
- **Commands 4-6 are read-only.** No `--fix` was passed in any form, and no file was rewritten by the gate. The gate's only writes are this artifact and `docs/builder/worker-memory/worker-1.md`.
- **Commands 1, 4, 5, and 6 read the whole tree**, including the concurrent card-005 cycle's five dirty paths. All four passed, so the plan's baseline exception never had to be applied.

### Floor verification

**No floor-verification scope declared.**

Written out rather than omitted, per `worker-1.md` `## Final test-run gate` — an unrun floor claim and an undeclared one look identical in an artifact that just skips the heading. The build plan's preamble declares `Floor-verification scope: none. No residual item touches a Django / Strawberry / channels integration seam`, and that is correct on the mechanical evidence above rather than accepted from the declaration: the cycle's whole diff is two `glossary_glossaryterm` rows and their rendered doc, the spec, a new rationale companion, and the artifacts, and `git diff -- django_strawberry_framework/ tests/` is 0 lines. `BUILD.md` `### When it is required` scopes the obligation to request/response handling, view or ASGI plumbing, upload or body parsing, the session/auth surface, queryset or expression compilation, schema and type construction against Strawberry internals, and consumer or middleware wiring; the cycle touches none of them. **No floor venv was built and the shared `.venv` was not mutated.** There is no unrun floor claim to close the gate on.

### Hot-path budget

Not applicable; the plan declares `Hot-path declaration: none`. Confirmed rather than accepted: no code runs per request, per resolver, per row, per connection, or per outbound message, because **no code changed** (`git diff -- django_strawberry_framework/ tests/` -> 0 lines).

### Failability proofs

None; the cycle introduced no boundary, guard, gate, or rejection path. Confirmed mechanically by the same command rather than accepted from the plan's declaration or an item's build report, per `worker-1.md` `### Failability and fail-open checks`. The companion confirmation is equally mechanical: **no fail-open shape landed**, vacuously — a fail-open shape is an expression in executable code and the diff contains none. One nuance worth recording, because R3's diff *describes* one: the `docs/GLOSSARY.md` `## OptimizerHint` correction names `OptimizerHint.__post_init__`'s flag-combination rejections in prose. Describing a boundary that shipped eleven releases ago is not introducing one, and no proof is owed for it.

### Cross-artifact read

All three closed artifacts read, as `BUILD.md` `## Cross-slice integration pass` step 1 requires with no "as needed" — `bld-004-r1-rationale_move.md` (5,766 lines), `bld-004-r2-spec_reconciliation.md` (4,108), `bld-004-r3-doc_completion_archive.md` (1,003). All three are `final-accepted`; all three of the build plan's item checkboxes are `- [x]`; the fourth box is this gate's and Worker 0 marks it.

Two traps `bld-003-final.md` flagged for a gate of this shape, both confirmed present again here and both handled in the catalog by construction rather than in prose:

- **An item carried only by an earlier artifact is lost to a walk of the latest one.** This cycle has **two**, where spec-003's had one. Item 11 (R1's final-verification precision note against the durable rationale) was handed to R2 *conditionally* — "R2 can tighten it in one clause if it opens that paragraph" — and R2 never opened that paragraph, so its 18-item handoff has no row for it and R3 could not inherit it. R3's own final verification found it and said so. Item 12 (R1's Worker 3 `### DRY findings` scaffolding-overlap bullet) was never handed forward at all: `grep -c 'hoist'` over `bld-004-r2` and `bld-004-r3` returns **0** and **0**.
- **One item at two line numbers double-counts if the catalog dedupes by citation.** Item 11 again: R1 cites B8's per-slice pointer at spec `:151` (measured against the 216-line post-R1 spec), R3 cites `:171` (against the 236-line post-R2 spec). One item, two line numbers, the shift caused by R2's own insertions. It is carried **once**, at the current line, re-derived at this gate.

### Cycle summary — what the three items delivered

Spec-004 shipped at `0.0.3`, eleven minor versions before this cycle. All eight of its slices (B1-B8) were built and released then; what this cycle produced is the deliverable set the shipped cycle never made, plus the reconciliation fifty-odd later specs made necessary. **No package source, test, or example code was written, and the full sweep confirms it.**

- **R1 — spec rationale extraction.** Created `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`, the companion `BUILD.md` `## Spec rationale extraction` makes the first substantive action of every build and which the released cycle predated. Eleven entries, one per spec section cut from, each keyed to a resolving spec anchor and each closing with the alternatives rejected, the changes the decision has undergone with the spec that caused each, and the claims the decision may no longer make. Eight fenced implementation proposals, eight slice-opening argument paragraphs, the whole `## Priority and ordering` section, and a dated extension-lifecycle spike `spec-029` retired all left the spec; **five rules that lived only inside cut text were restated in the spec**, because a builder never reads the companion. Seven Worker 3 review rounds; the last found nothing.
- **R2 — spec-versus-HEAD reconciliation.** Every claim the package falsifies restated as the contract that actually holds, or handed to the spec that now owns it, with the explanation of each change landing in the rationale and never in the spec. Worker 0's 28-row drift table was the verified floor, not the worklist: R2's own sweep added **eight** further false claims the table did not carry. Four Worker 3 review rounds.
- **R3 — documentation completion and archive audit.** The durable docs audited **against source rather than against the spec**, which is what found the one defect three prior passes could not: `docs/GLOSSARY.md` called `check_schema` a *classmethod*, a word that survived from spec-004's original pseudo-code through eleven releases, three residual cycles, and R2's own correction of the same claim one document over. Corrected at its DB source and rendered, together with a second false-at-HEAD statement (the `OptimizerHint` entry presented four factories as the whole consumer API while five ship). The archive re-derived clean in all three cross-reference directions, the kanban chain re-derived clean, and the staged-anchor sweep discharged. Worker 3 filed zero findings at every severity.

**The spec's before and after**, every figure re-derived at this gate:

| Figure | HEAD (`git show HEAD:<spec>`) | Now | Delta |
|---|---|---|---|
| spec lines | 359 | **236** | -123 |
| spec bytes | 33,928 | **36,223** | **+2,295** |
| `git diff --numstat` | — | **73 insertions / 196 deletions** | — |
| fenced code blocks | 16 markers (8 fences) | **0** | -8 fences |

**The byte count rose while the line count fell, and that is the cycle's shape rather than an anomaly.** R1 removed 7,492 bytes of deliberation (359 -> 216 lines, 33,928 -> 26,436 bytes); R2 then added roughly 9,800 bytes of *contract* (216 -> 236 lines, 26,436 -> 36,223). A reconciliation that only shrinks a spec is deleting contract; both directions are reported so the net delta cannot be read as a defect.

Alongside it: the rationale companion at **1,309 lines / 94,318 bytes**, and **two** `docs/GLOSSARY.md` corrections rendered from the DB (`git diff --numstat -- docs/GLOSSARY.md` -> `8  6`, two hunks — F1's one-line `Classmethod` -> `Static method` fix, and F2's fifth `Supported modes:` bullet plus its re-wrapped `Validation:` paragraph).

### Deferred work catalog

Authored from all three closed artifacts' `### Notes for Worker 1 (spec reconciliation)`, `### What looks solid`, `### DRY findings`, and final-verification sections — **not** from the most recent catalog, which would have dropped items 11 and 12. **Keyed by item; every carrying artifact section is named per bullet.** Every open item was re-derived live at this gate; the command is quoted in the item.

**Twelve items. R3's final verification predicted eleven and named ten; the twelfth is this gate's own find, and it is the same class of miss R3 caught — an item carried only by R1.**

1. **The `check_optimizer` management command and custom-resolver detection were named as B6 follow-up work at `0.0.3`, never built, and no card names either.** *Carried by:* `bld-004-r2` `### Row-by-row disposition` row D21, and its `### Notes for Worker 1 (spec reconciliation)` item 2 in every pass's list; `bld-004-r3` `### 5.` row 2, its Plan `### Notes for Worker 1` item 1, and Worker 3's consolidated list item 1. Originally the build plan's drift row D21 and its `### The read-only correctness audit — findings` closing paragraph. *Licensing clause:* none, and that is the point — R2's disposition is *"A promise eleven versions old with no card is not a contract"*, so it was dropped from the spec and recorded in the rationale. *Re-derived here:* `grep -c 'check_optimizer'` over the spec -> **0**; `django_strawberry_framework/management/commands/` ships `export_schema.py` and `inspect_django_type.py` only. `inspect_django_type` (spec-029) answers a different question and is explicitly not a substitute.
2. **The `_record_relation_access`-before-elision ordering invariant has no automated guard.** *Carried by:* the build plan's `### The read-only correctness audit — findings` closing paragraph; `bld-004-r2` `### Notes for Worker 1` item 3 in every pass's list and `### The three claims this pass refused to make` bullet 3; `bld-004-r3` `### 5.` row 3, Plan item 2, Worker 3's consolidated item 2. *Licensing clause:* the build plan's `## Build-wide context flags` — package source, `tests/`, and `examples/` are read-only for the whole cycle, and *"make sure the code is correct" is a read-only audit obligation, not a licence to change source*. *Description:* `optimizer/walker.py::_record_relation_access` must run **before** the elision short-circuit in `::_plan_select_relation`, because it appends the FK `attname` the elided resolver later reads; reversing them silently reintroduces the N+1 the elision exists to remove. *Re-derived here:* defined at `walker.py:826`, called at `:722` / `:786` / `:1004`, with no ordering assertion anywhere. **This is `bld-003-final.md`'s catalog item 1, now in its second consecutive cycle** — protected by docstrings and a spec-level requirement, by no test and no assertion. Whether it earns a guard is the maintainer's call; promoting it was the strongest form available inside a documentation cycle.
3. **`spec-029` calls `strawberry-graphql 0.316.0` "locked", and its `pyproject.toml` figure is wrong — one edit across every site, not two.** *Carried by:* `bld-004-r1` Worker 3 pass-4 `### Notes for Worker 1` item 17 (offered as an R2 touch-up rather than a finding); `bld-004-r2` `### Notes for Worker 1` item 4 in every pass's list; `bld-004-r3` `### 5.` row 4, Plan item 3, Worker 3's consolidated item 3 (which widened it). *Licensing clause:* the build plan's `## Build-wide context flags` — *"Sibling specs are read-only, with NO declared exception."* *Re-derived here:* `pyproject.toml:36` reads `"strawberry-graphql>=0.316.0"` — a declared **floor**, not a lock; `grep -c 'locked'` over `spec-029` -> **8 lines**; `grep -o '0\.316\.0' | wc -l` -> **36 occurrences**. **Whoever fixes it must decide for every site at once** — correcting the `>=0.262.0` figure alone does not close it.
4. **The `spec-003` pair credits plan-immutability enforcement to `spec-035`, which contains none of it — seven sites, enumerated.** *Carried by:* `bld-004-r2` `#### M3` (Worker 3 pass 2), `### M3 — the seven sites, and the sweep the last pass did not run` (apply pass 2), `#### M5` (Worker 3 pass 3), `### M5 — the deferral widened from one site to seven, in the durable file` (apply pass 3), and `### Notes for Worker 1` item 5; `bld-004-r3` `### 5.` row 5, Plan item 4, Worker 3's consolidated item 4. Also the build plan's `**CORRECTION (2026-08-08)**` paragraph under the drift table. *Licensing clause:* both files are read-only in this cycle; the enumeration therefore lives in the **durable** spec-004 rationale (`#"Spec-003 is a read-only sibling in this cycle"`) rather than only in a scratchpad. *Re-derived here:* `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:30`, plus six body citations in its companion (`:253`, `:521`, `:598`, `:604`, `:855`, `:952`) and the `[spec-035]` link definition at `:1050`; only `:521`'s projection-gate item is sound. **Decide for all seven at once.**
5. **Three B7 test names still spell the retired `_optimizer_field_map`.** *Carried by:* the build plan's `### Test-surface coverage` B7 row and drift row D22; `bld-004-r2` `### Notes for Worker 1` item 6; `bld-004-r3` `### 5.` row 6, Plan item 5, Worker 3's consolidated item 5. *Licensing clause:* already carded on `TODO-ALPHA-052-0.1.0` (the live-code sweep), and no test file is writable in this cycle. *Re-derived here:* `tests/optimizer/test_field_meta.py` `:322` `::test_optimizer_field_map_populated`, `:339` `::test_optimizer_field_map_contains_relations`, `:362` `::test_optimizer_field_map_respects_fields_filter`. Naming only — the coverage is real and passing.
6. **The spec's `## Non-goals` says Layer-3 features "have their own specs"; aggregates has none.** *Carried by:* `bld-004-r2` `### The two residues Worker 3 recorded rather than filed — both decided` residue 1, and Worker 3's `### What looks solid` in all four review passes; `bld-004-r3` Plan item 6 and Worker 3's consolidated item 6. *Licensing clause:* R2's refusal to land an unreviewed contract edit on a byte-stable spec at final verification — *"the imprecision costs less than the unreviewed change"*. *Re-derived here:* spec `:181`; filters, orders, and permissions have specs, aggregates has none on disk. **Self-discharging** — whoever authors the aggregates spec makes the sentence true by existing; if that spec is never written, a future spec-004 custodian narrows the clause.
7. **`KANBAN.md` card 4's B1 `Scope` row names four cache-key components; five ship.** *Carried by:* `bld-004-r3` `### 1.` (the `KANBAN.md` audit), Plan `### Notes for Worker 1` item 7, Worker 3's consolidated item 7. *Licensing clause:* `worker-0.md` `## Closing out a kanban card` — a Done card's `Scope` row records **declared scope**, not a live contract. *Re-derived here:* `KANBAN.md:4925` reads *"B1: plan cache keyed by selected operation AST, directive variables, model, and root runtime path"*; the missing fifth is the resolver's `origin` Strawberry type, which arrived with `spec-018`, three releases after this card. **A deliberate refusal, not an oversight**: rewriting board history to match a later spec is not what a card records, and a reader who needs the current key has two correct sources (the reconciled spec and the `Plan cache` glossary entry). Whoever disagrees should note the fix is a `CardItem.text` ORM edit plus a `build_kanban_md.py` / `build_kanban_html.py` regenerate.
8. **`docs/README.md`'s `## Today and coming next` `OptimizerHint` bullet omits `strategy`.** *Carried by:* `bld-004-r3` `### 1.` (the `docs/README.md` audit), Plan item 8, Worker 2's `### Notes for Worker 1` item 2, Worker 3's consolidated item 8. *Licensing clause:* `docs/README.md` is on the R3 dispatch's explicit do-not-touch list, and Worker 0 did not fold it into Worker 2's scope. *Re-derived here:* `docs/README.md:108` reads *"`OptimizerHint` — per-relation overrides (`SKIP`, `select_related`, `prefetch_related`, custom `Prefetch`)"*. Non-blocking: unlike the entry F2 corrected, this bullet asserts no completeness, and the same file documents `strategy` in full at `:177`. After F2 this is the **only** durable-doc surface left where `strategy` is absent from an `OptimizerHint` member list.
9. **`docs/GLOSSARY.md` `## Connection-aware optimizer planning` says the nested fetch strategy is "fixed per instance"; `OptimizerHint.strategy(...)` overrides it per connection field.** *Carried by:* `bld-004-r3` Worker 2's `### Notes for Worker 1` item 1 (found while siting F2's pointer), Worker 3's `### DRY findings` and consolidated item 9, and Worker 1's `### DRY check across R3 and the two closed items`. *Licensing clause:* the entry is not one of card 4's ten anchors and the R3 dispatch scoped Worker 2 to F1 and F2, so it is outside that item's writable set. *Re-derived here:* `docs/GLOSSARY.md:390`. So the extension-wide setting is the **default**, not a fixed value. The fix is a `GlossaryTerm(anchor='connection-aware-optimizer-planning')` ORM edit plus a regenerate. **Same defect class as F1 and F2** — a claim that was true when written and was never re-taken after a later slice extended the surface.
10. **DISCHARGED, not deferred — R3's Plan item 9** (*"if Worker 0 rules F2 outside R3's charter, it defers here"*). *Carried by:* `bld-004-r3` Plan `### Notes for Worker 1` item 9 and Worker 3's consolidated item 10. Worker 0 dispatched F2, it landed, and Worker 3 and Worker 1 both graded it correct. Carried here **closed**, so a reader of R3's Plan does not re-open it.
11. **The rationale's `**The win.**` standing note overstates the per-slice pointer population by one.** *Carried by:* `bld-004-r1` `## Final verification (Worker 1)` #"One precision note on the durable paragraph that carries item 20" — **and by no other pass in this cycle until R3's final verification**, `bld-004-r3` `## Final verification (Worker 1)` `### The ten-item catalog audited as the gate's input — nine live, one discharged, and ONE MISSING`. *Licensing clause:* `worker-1.md`'s refusal to land unreviewed prose into a durable file at a final gate, invoked identically by R1 and by R3; the sentence's operative instruction (*"The asymmetry is deliberate: a harmonizing sweep must not level it back"*) is unaffected, so no reader reaches a wrong action from it. *Re-derived here, at source:* the rationale at `:792`-`:793` reads *"The same characterization was in the spec's own pointer text — the companion-pointer paragraph and the eight per-slice pointers"*; the eight per-slice pointers are at spec `:41`, `:63`, `:81`, `:109`, `:119`, `:139`, `:151`, `:171`, and **B8's (`:171`) opens "The ordering argument that put this slice last"** and carries no such clause — so it was in **seven** of eight. The same paragraph's closing clause (*"`### B5`'s and `### B7`'s pointers now open 'The opening argument' where **the others** still open 'The competitive argument'"*) is imprecise in the same direction: five of the remaining six do (`:41`, `:63`, `:81`, `:109`, `:139`), and B8 does not. **Line-number divergence, handled by item:** R1 cites B8's pointer at `:151` against the 216-line post-R1 spec; the current line is `:171`. One item, one bullet. Fix it in one clause whenever a chartered pass next opens that paragraph. **How it went missing is the durable lesson:** R1 handed it forward *conditionally* — "R2 can tighten it in one clause if it opens that paragraph" — and a conditional hand-off does not enter the next item's numbered handoff, which is built from the previous handoff and never from the artifact behind it.
12. **The rationale-file scaffolding is on its fourth-and-later hand-reproduced instance, measured and priced but never routed.** *Carried by:* `bld-004-r1` `## Review (Worker 3)` `### DRY findings`, first bullet — **and by nothing else in this cycle.** *Licensing clause:* none; the bullet's own disposition is *"**No change recommended** — recorded so the next cycle's reviewer does not re-derive it, and so the maintainer can see the cost if a fourth sibling makes it worth hoisting into `BUILD.md`."* *Description:* the optimizer rationale files reproduce one file form by hand — the H1 suffix, the "Deliberative companion to …" opener, `## How to read this file`, `## Provenance of this record`'s *Moved* / *Cut* / *Deleted* vocabulary, `## Standing notes`, and the link-definition scaffold at `docs/SPECS/appx/` depth. R1 measured the cost: **540** 8-word shingles of overlap against `spec-003`'s rationale and **175** against `spec-002`'s, longest run 89 shingles. Whether it becomes a documented template is a standing-docs question for the maintainer, not a defect in any item. *Re-derived here:* `ls docs/SPECS/appx/*rationale.md | wc -l` -> **10** files, so the "fourth sibling" trigger the bullet names is amply met. **Why this bullet exists:** it is the direct continuation of `bld-003-final.md`'s catalog item 2, which that gate carried precisely because *"R2's catalog dropped it"* — and the same drop recurred here. `grep -c 'hoist'` over `bld-004-r2` -> **0**; over `bld-004-r3` -> **0**.

### Settled judgements, deliberately NOT in the catalog

`BUILD.md` scopes the catalog to what was **deferred**. Several things in this cycle read like deferrals in prose and are decisions; listing them here is what stops a future pass re-opening them or a reader treating the catalog as incomplete.

**R2's five recorded-not-filed residues — four decisions, one deferral.** R2's `## Final verification (Worker 1)` names five items examined and deliberately not filed across its four reviews. **Four are settled**: `## Current state`'s "effective end-to-end" (HEAD's own wording, unfalsifiable, and rewriting it would be scope R2 did not open); `### B7`'s `**Test surface.**` "Benchmark (optional)" (marked optional, never a delivery claim); the rationale's `## How to read this file` bullet 8 (scoped to the extraction pass by its own first three words, and accurate as history); and the `34`-where-it-is-`35` occurrence figure (a numeral inside a per-cycle scratchpad, correctly routed nowhere — *"putting a scratchpad numeral in the next spec author's reading list would be noise"*). **The fifth, the `## Non-goals` aggregates clause, is a genuine deferral and is carried as catalog item 6.**

Also settled, and named so the catalog's absences are legible:

- **The `## Problem statement` competitive-positioning question is a maintainer decision, already made.** Worker 3 escalated it at R1's pass-2 review and correctly declined to rule; the maintainer decided *keep the spec sentence byte-for-byte, make two recording edits in the rationale*, and the decision plus its three rejected alternatives are recorded in the build plan's `## Maintainer decision — the surviving competitive positioning in `## Problem statement``. R1 implemented it and proved the sentence byte-identical to HEAD by `diff` on the line (584 bytes each side). **Decided — do not re-open.**
- **R1's handoff items 10, 16, 18, and 20 are marked CLOSED / DISCHARGED in the artifact itself**, each stating what replaced it; R1's final verification confirmed all three closures independently.
- **R2's handoff item 13 — two behaviours with no spec owner anywhere, deliberately** (plan-immutability enforcement via `OptimizationPlan.finalize` / `::_assert_under_construction`, and the once-per-row resolver-key threading). Not deferred work: R2 established from `git log -S` that no sibling spec owns either, and stated them in spec-004 without a citation rather than mis-citing one. If a future spec claims either, spec-004's sentences are the ones to update.
- **R1's handoff item 19's cross-sibling comparison** (10 modal labels here against 47 non-modal across the spec-001/002/003 rationales) lives in R1's artifact and its handoff only, and R1 judged that non-blocking with three stated reasons — chiefly that the instruction is **conditional and expired with R2**. Recorded here so its absence from the catalog is a decision rather than a gap.
- **The one-clause deviation from R3's Plan letter** (F2's rejection enumeration gaining `nested_strategy=` set with `skip=True`, `prefetch_obj=`, or `force_select=True`) was raised for Worker 1 to keep or revert, and Worker 1 **kept it**, verified against `optimizer/hints.py::OptimizerHint.__post_init__` operand for operand. Not an open item.

### The three build-plan corrections, confirmed

R3 routed three corrections to Worker 0 rather than editing the plan, which is Worker 0's file. All three have been applied. Two now read correctly; **one is still imprecise in the same way it was before, and this gate is reporting it rather than fixing it.**

1. **The B-owned glossary entry count — applied to the numeral, NOT to the list.** The plan's `## Worker-0-verified facts` `:158` now reads *"**Corrected at R3: there are SEVEN, not the five this bullet first claimed while naming six**"* — and then names the same **six**: `FK-id elision`, `Meta.optimizer_hints`, `Plan cache`, `Queryset diffing`, `Schema audit`, `Strictness mode`. The seventh, `OptimizerHint`, is still absent, so the bullet again states a count its own enumeration does not reach. Re-derived at this gate against the DB rather than the rendered doc — `GlossaryTerm.objects.filter(status_text__icontains='0.0.3')` -> **exactly 7 rows**, every one `shipped (`0.0.3`)`, the seventh being `optimizerhint`, which is precisely the entry F2 corrected. **Non-blocking**: the conclusion the sentence carries — every B-owned entry is `shipped (0.0.3)`, no status flip owed — is unaffected, and R3's finding was reported accurately. It is Worker 0's file and this gate does not edit it; the remaining fix is one word added to the list.
2. **The staged-anchor baseline — correct.** `:160` now carries *"(Corrected at R3: the sweep now returns 3 hits, all this cycle's own scratchpads quoting the grep pattern back. The original "zero hits anywhere" predated those artifacts.)"* — the honest form, since a filtered "zero" would require silently excluding files. Re-derived below.
3. **The deleted `bld-003-*.md` count — correct where it governs.** `### Fifth change` now opens *"**Re-measured at R3's close: THREE remain deleted, not four.**"* and names `bld-003-final.md` as restored and byte-identical to HEAD. Re-derived: `git status --short -- docs/builder/ | grep '^ D' | wc -l` -> **3**. One residue, recorded and not corrected because the plan is Worker 0's: the paragraph *below* that correction still reads *"`git status --short` shows four `D` entries"* over a four-item list. The leading correction governs the section, so no reader is misled about the current state, but the present tense below is stale.

### Staged-anchor sweep — re-measured at the gate, with its decomposition

`BUILD.md` `## Cross-slice integration pass` step 6 was discharged in R3; re-run here as the gate's backstop. **The mechanical test first**, because it closes the classification question by construction rather than by judgement — a staged anchor is a source-site marker (`AGENTS.md` rule 26), so zero outside `docs/builder/` means every surviving hit is by construction a per-cycle scratchpad hit:

```text
grep -rEn 'TODO\(spec-004|TODO-(ALPHA|BETA|STABLE)-004' . --exclude-dir=docs/builder   ->  no match (exit 1)
grep -rEn 'TODO\(spec-004|TODO-(ALPHA|BETA|STABLE)-004' . | wc -l                      ->  3
```

Whole-tree decomposition, published rather than reduced to a bare number (a raw count here reads as a failure signal and is not one):

```text
docs/builder/build-004-optimizer_beyond-0_0_3.md          2   (:29, :345)
docs/builder/bld-004-r2-spec_reconciliation.md            1   (:3889)
```

**3 matching lines across exactly two `.md` files, all three the grep pattern itself quoted in prose describing the sweep.** R3 measured the plan's two hits at `:29` and `:343`; they are now `:29` and `:345`, because Worker 0's three corrections added two lines to the plan after R3 closed — which is the same line-number-drift class the catalog handles by keying on items. Zero in the spec, zero in the rationale, zero in any source, test, or example file, zero in `docs/GLOSSARY.md`, and zero in `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` (so step 6's board-card exclusion never had to be applied). This artifact does not appear in the sweep because it writes the anchor only in the *regex* form and never the literal one — fencing is not what keeps a file out, since `grep` does not know about fences. **Zero staged anchors survive in shipped material.**

Separately, and deliberately **not** swept: `grep -oE '\bB[1-8]\b'` over `optimizer/*.py` plus `types/resolvers.py` returns **21** provenance markers. These are spec-Decision pointers on the KEEP list of `AGENTS.md` rule 27 and the no-process-provenance rule, not staged anchors. Do not remove them.

### Every count in this artifact, with the command that produced it

`BUILD.md` `## Claims are proven mechanically` — and this cycle had counts come out wrong on first write **six** times in R2 alone, with the recurring traps being `grep -c` counting *lines* where the rule prescribes *occurrences*, and a count stated for a worklist rather than for a population. Every figure below was measured as it was written.

| Figure | Command | Result |
|---|---|---|
| suite result | `uv run pytest --no-cov` | `5635 passed, 40 skipped in 63.67s` |
| files ruff-formatted | `uv run ruff format --check .` | `418 files already formatted` |
| working-tree paths | `git status --porcelain \| wc -l` | 16 before this artifact was written, 17 after |
| package/test diff | `git diff -- django_strawberry_framework/ tests/ \| wc -l` | 0 |
| dirty `.py` paths | `git status --porcelain \| grep -c '\.py$'` | 0 |
| deleted `bld-003-*` | `git status --short -- docs/builder/ \| grep '^ D' \| wc -l` | 3 |
| spec now | `wc -l -c docs/SPECS/spec-004-…md` | 236 lines / 36,223 bytes |
| spec at HEAD | `git show HEAD:docs/SPECS/spec-004-…md \| wc -l -c` | 359 lines / 33,928 bytes |
| spec diff | `git diff --numstat -- docs/SPECS/spec-004-…md` | `73  196` |
| rationale | `wc -l -c docs/SPECS/appx/spec-004-…-rationale.md` | 1,309 lines / 94,318 bytes |
| glossary diff | `git diff --numstat -- docs/GLOSSARY.md` | `8  6` |
| B-owned `shipped (0.0.3)` entries | ORM: `GlossaryTerm.objects.filter(status_text__icontains='0.0.3')` | **7** (`fk-id-elision`, `metaoptimizer_hints`, `optimizerhint`, `plan-cache`, `queryset-diffing`, `schema-audit`, `strictness-mode`) |
| staged anchors, whole tree | `grep -rEn 'TODO\(spec-004\|TODO-(ALPHA\|BETA\|STABLE)-004' . \| wc -l` | 3 |
| staged anchors, shipped material | same, `--exclude-dir=docs/builder` | **no match (exit 1)** |
| `B1`-`B8` provenance markers | `grep -oE '\bB[1-8]\b' optimizer/*.py types/resolvers.py \| wc -l` | 21 (KEEP list) |
| spec pointer uses | `grep -c 'spec-004-rationale' docs/SPECS/spec-004-…md` | 11 (8 per-slice + companion + problem-statement + 1 definition) |
| per-slice pointers | `grep -n 'spec-004-rationale' docs/SPECS/spec-004-…md` | `:41 :63 :81 :109 :119 :139 :151 :171` — **8**, of which **7** carried the characterization |
| `spec-029` "locked" | `grep -c 'locked' docs/SPECS/spec-029-…md` | 8 lines |
| `spec-029` `0.316.0` | `grep -o '0\.316\.0' docs/SPECS/spec-029-…md \| wc -l` | 36 occurrences |
| `spec-003` pair `spec-035` sites | `grep -n 'spec-035'` over both files | 1 + 7 (6 body citations + 1 link definition) |
| rationale files under `appx/` | `ls docs/SPECS/appx/*rationale.md \| wc -l` | 10 |
| closed artifacts read | `wc -l docs/builder/bld-004-r{1,2,3}-*.md` | 5,766 / 4,108 / 1,003 |

### DRY check across the cycle

**No new duplication, and this is a measured negative rather than a skipped section.** The cycle's whole diff contains no executable logic (`git diff -- django_strawberry_framework/ tests/` -> 0 lines), so there is no helper, repeated literal, key, tuple shape, or parallel data flow to consolidate, and no new abstraction for the **existence challenge** to interrogate. On the documentation axis the three items partition cleanly and none restates another's output: R1 wrote the rationale, R2 wrote the spec, R3 wrote neither — three items, three disjoint surfaces, confirmed by `git diff --stat -- docs/SPECS/` plus R3's `docs/GLOSSARY.md` + two-DB-row diff.

Two live documentation-duplication risks the cycle named, both correctly handled and both leaving a residue in the catalog rather than in the code:

- **Over-absorbing the later optimizer specs into spec-004.** The build plan's `**The scope trap specific to this spec.**` names spec-033 / spec-035 / spec-029 as the pull; R2's answer is a pointer per behaviour rather than a transplanted paragraph, and it also caught the **mirror** the plan did not name — two places where spec-004 was crediting a sibling for its *own* shipped surface. Neither direction survives.
- **A fourth carrier of the nested-connection strategy contract.** R3's F2 added a pointer, not a copy: it names `OptimizerHint.strategy(...)` and states no backend, no selection rule, no precedence rule, no extension-wide default. The live duplication is in the *second* carrier, `docs/GLOSSARY.md` `## Connection-aware optimizer planning`, which is catalog item 9.

`scripts/review_inspect.py` was correctly skipped by every pass with a recorded reason: `BUILD.md` `### When to run the helper during build` triggers on a new `.py` file, a touched `optimizer/` or `types/` file, or 30+/50+ new logic lines, and the cycle touches no `.py` file at all.

### Spec status-line re-verification (owed by every Worker 1 spawn)

Read `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` lines 1-9 at their current content. The spec carries **no `Status:` / owner / target-release / predecessor header block** — `:1` is the title, `:3` the companion-pointer paragraph, `:5` `## Problem statement`, `:9` the eight-improvements framing sentence. Established at R1, unchanged through R2 and R3, and still true. Nothing in those lines is a status line this build has falsified: `:3` describes the move accurately and its `[spec-004-rationale]` target resolves on disk; `:9` points the recommended build sequence at the rationale rather than at the deleted `## Priority and ordering` section. **No edit was needed and none was made**, so `### Spec changes made (Worker 1 only)` below reads `None.`

### Verification commands run at this gate, each result quoted

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **`OK: 10 terms - all have glossary entries and at least one spec link.`** exit 0. Character-identical to the build plan's pre-flight baseline, which is the property both R1 and R2 could have silently broken by dropping an anchor's sole carrier.
- `uv run python scripts/check_trailing_commas.py --check` on the spec, the rationale, `docs/GLOSSARY.md`, and this artifact -> **exit 0**, all four; re-run after the last edit to this file.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> **`OK: 49 done cards have glossary links.`** exit 0. **Read-only `--check` form only; the writing sync form was never invoked at this gate.**
- `git rev-parse HEAD` -> `ff03c1372365edcad488ff4671389d88ae145276`, re-derived rather than quoted.
- `git log -1 --format='%h %s' -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> `20a9752f docs(spec-003): reconcile the O4 spec with HEAD and extract its rationale` — unchanged, so nothing of this cycle was swept by a concurrent commit.
- No `git stash` / `checkout` / `restore` / `worktree` at any point. No branch created or switched. Nothing committed. No `--cov*` flag in any command in any form other than `--no-cov`.

---

## Final verification (Worker 1)

- **Gate commands:** all six run in `BUILD.md` order, all six pass, each result recorded above with its real output.
- **Concurrent churn:** none arose during this pass; the working tree was the same sixteen entries at the start and at the end, plus this artifact. Five of the sixteen are the concurrent card-005 cycle's and three are `bld-003-*` deletions no pass here caused — all reported, none reverted, none restored.
- **Floor verification:** `No floor-verification scope declared.` — the plan's declaration, confirmed against the diff rather than accepted.
- **Deferred work catalog:** authored from all three closed artifacts; **twelve** bullets. R3's final verification predicted eleven; the twelfth is this gate's own find and is the same class of miss — an item carried only by R1's Worker 3 review and dropped by both later artifacts, the exact trap `bld-003-final.md` warned about, recurring.
- **Checklist:** every box in the Plan's `### Dispatched findings checklist` is `- [x]` and each is discharged by named evidence in this artifact. No deferral reason is owed.
- **DRY:** no new duplication across the cycle; measured, not asserted.
- **Spec reconciliation:** none owed. This pass opened neither the spec nor the rationale for editing.

### Summary

The spec-004 residual-completion cycle closes green. Its three items delivered the missing `-rationale.md` companion (R1, 1,309 lines), the spec-versus-HEAD reconciliation (R2), and the documentation completion plus archive audit (R3) — landing **no package source and no test**, which this gate confirmed mechanically rather than accepted from the plan. All six gate commands pass: the full sweep is `5635 passed, 40 skipped`, Django's system and migration checks are clean, and the read-only lint/format/whitespace gate is clean across 418 files. The spec went from **359 lines / 33,928 bytes** to **236 / 36,223** — fewer lines and *more* bytes, because R1 removed 7,492 bytes of deliberation and R2 then added roughly 9,800 of contract; a reconciliation that only shrinks a spec is deleting contract. Eight fenced implementation proposals are gone and none remains in either file. Two false-at-HEAD statements in `docs/GLOSSARY.md` were corrected at their DB source and rendered. Zero staged anchors survive in shipped material.

The catalog carries **twelve** items to the maintainer, keyed by item and naming every carrying artifact section. Three deserve a first read: **item 2**, the `_record_relation_access` ordering invariant, which is now in its second consecutive cycle with no automated guard and is the only one that names shipped optimizer behaviour; **item 11**, the durable rationale's one-off overstatement, which existed only inside a closed artifact because it was handed forward *conditionally* and a conditional hand-off never enters the next item's numbered list; and **item 12**, which is item 11's shape without even a conditional hand-off — an R1-only DRY measurement that both later artifacts dropped, exactly as `bld-003-final.md` predicted this class would be dropped. Everything else is either outside the cycle's writable set, a source change a documentation cycle cannot make, a deliberate refusal to rewrite board history, or an item that discharges itself when a future spec lands.

`Status: final-accepted`. Worker 0 marks the plan's final checkbox; the maintainer's review and commit are next.

### Spec changes made (Worker 1 only)

None. This pass edited no spec, no rationale, no terms CSV, no `CHANGELOG.md`, no `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `docs/TREE.md` / `docs/README.md` / `examples/fakeshop/db.sqlite3`, no source, no test, no sibling spec, no closed `bld-004-*` artifact, and not Worker 0's build plan. The three deleted `bld-003-*.md` files were not restored and `docs/builder/bld-003-final.md` was read but not moved or edited. Its only writes are `docs/builder/bld-004-final.md` and `docs/builder/worker-memory/worker-1.md`. Nothing was committed and no branch was created or switched.

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
