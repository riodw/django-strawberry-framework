# Package build plan: optimizer_nested_prefetch_chains / 0.0.2 (003)

Spec source: `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` (**already archived** — the spec, its `-terms.csv`, the `SpecDoc.path` row, and every inbound cross-reference already sit at their post-archive locations; item R3 verifies rather than performs the move)
Target release: `0.0.2` (**shipped long ago** — card `DONE-003-0.0.2`, `target_version.number` `0.0.2`; the package is at `0.0.14` in `pyproject.toml`)
Date created: 2026-08-07
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging. A fact told twice across the spec and its rationale sibling goes stale in one of them — the rationale carries the deliberation, the spec carries the contract, and neither restates the other.
Ownership partition: none; sequential residual items.
Hot-path declaration: none. No residual item changes package source, so no item runs per request, per resolver, per row, per connection, or per outbound message.
Floor-verification scope: none. No residual item touches a Django / Strawberry / channels integration seam — the cycle edits the spec, its rationale sibling, one sibling-spec sentence, and (only if the audit finds drift) DB-rendered docs.
Pre-flight: passed on 2026-08-07 with **two** recorded deviations (below); baseline: clean (`git status --short` empty); cleanup: memory seeded, shadow/temp-tests already empty; prior cycles' `build-*.md` deliberately preserved — see Deviation 1.

## This is a residual-completion cycle, not a fresh build

The single slice spec-003 declares (O4) was built and released at `0.0.2`, twelve minor versions ago. What remains is the deliverable set the shipped cycle never produced, plus the reconciliation that fifty-odd later specs made necessary. The maintainer scoped it in three sequential items: the missing `-rationale.md`, the spec-versus-HEAD reconciliation, then the documentation and archive audit.

The immediate precedent is the **spec-002 residual cycle**, committed at `d613887c` / `a76da376` on 2026-08-07 (`docs/builder/build-002-optimizer-0_0_2.md`), itself modelled on the spec-001 cycle at `cfd1f873`. This plan follows spec-002's structure deliberately: the two cycles are the same shape, and spec-002 is spec-003's own parent document — spec-002 `## Purpose` already assigns the detailed O4 record to this spec.

### Already-shipped spec slice — verified delivered at HEAD (no build cycle dispatched)

Not a checkbox: Worker 0 may only tick a box after a Worker 1 final verification, and this slice predates the plan by twelve releases. It is evidence, pre-verified by Worker 0 at pre-flight so no worker re-derives it.

O4 shipped in commit `4b7d7703` ("feat: enhance optimizer with nested prefetch and resolver key support"). The **behaviour** the spec designed is entirely present; what has diverged is its **symbol names, signatures, file placements, and every present-tense sentence about the pre-implementation codebase**. The spec's own `## Definition of done` walks 8 bullets, and all 8 are delivered — 6 exactly as written, 2 delivered differently (see `### Verified spec-versus-HEAD drift` rows D19–D20).

### Residual scope (this cycle's actual work)

- **R1 — spec rationale extraction.** `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` does not exist. `docs/builder/BUILD.md` `## Spec rationale extraction` makes the move the first substantive action of a build and pre-flight step 7 gates dispatch on it; the shipped cycle predates the rule. Worker 1 is the only role that may perform it. Spec-003 is a **34,030-byte / 447-line** spec — five times spec-002's size — and its deliberative layer is unusually concentrated: **seven fenced pseudo-code blocks** proposing an implementation that landed under different names, plus a `## Documentation updates when O4 ships` section and an `## Anchor and lint notes` section that are wholly discharged. See `### What R1 inherits that spec-002 did not` for the shape-specific guidance.
- **R2 — reconcile the spec with what landed and what later specs corrected.** The maintainer's framing: *make sure the spec matches what actually exists, make sure the code is correct, and where later updates corrected what landed, the spec reflects that; the explanation of each change goes in the rationale, never in the spec.* Twenty-two verified drift items are tabled below. Worker 1 is the only role that may edit the spec.
- **R3 — finish the documentation and audit the archive.** Verify the durable docs (`docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`) describe the O4 surface as shipped; discharge the **one** residual obligation from the spec's own `## Documentation updates when O4 ships` (the spec-004 rider, `### The one authorized sibling-spec edit`); and verify the already-performed archive is complete in all three cross-reference directions, in the kanban DB, and in the terms-CSV importability chain.

**"Make sure the code is correct" is a read-only audit obligation, not a licence to change source.** Worker 0's pre-dispatch audit (`### The read-only correctness audit — findings`) found **no defect** in the shipped O4 paths and four recorded observations. If R2 or R3 finds a genuine correctness defect in shipped optimizer code, it is recorded as a finding and escalated to the maintainer — it does not become a source edit inside a documentation cycle. `AGENTS.md` rule 5 (root-cause fix, never defer) governs what the *fix* must look like when the maintainer authorizes one; it does not authorize a docs cycle to silently become a code cycle.

## Pre-flight outcome (7 steps, `docs/builder/worker-0.md` `## Pre-flight procedure`)

1. **Working-tree baseline is explicit.** `git status --short` → **empty**. Clean at HEAD `99696bac`.
2. **`scripts/review_inspect.py` runs.** `uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow --stdout` emitted its overview (23 imports, 39 symbols, 9 control-flow hotspots, 2 TODO comments, 7 repeated string literals). Working. Note the **2 TODO comments are `TODO(spec-035)`**, not this spec's — see D15.
3. **Build artifacts are reset — DEVIATION 1, see below.** Verified instead that every path this plan creates is absent: no `docs/builder/build-003*`, no `docs/builder/bld-003*`, no `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md`.
4. **`.gitignore` lists the untracked scratch paths.** `docs/shadow/` (line 174), `docs/builder/worker-memory/` (188), `docs/builder/temp-tests/` (192). Present.
5. **Scratch directories are cleared.** `docs/builder/worker-memory/` and `docs/builder/temp-tests/` were already empty (the prior cycle's closeout cleared them); `docs/shadow/` holds only the step-2 smoke output. Four memory files re-seeded empty.
6. **Spec-doc consistency check.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` → `OK: 8 terms - all have glossary entries and at least one spec link.` Exit 0. Baseline for the constraint in `### The 8-anchor constraint` below.
7. **Spec rationale is extracted.** **Not done — it is item R1 of this cycle.** Ordinarily this gates dispatch. Here it cannot, because R1 *is* the dispatch: the slice whose spawns the gate protects was built and released before this plan existed, so there is no builder left to protect. R1 runs first regardless, so every later spawn in this cycle reads the smaller spec exactly as the rule intends.

Two further baselines recorded at pre-flight, both green, both re-checked by any pass that writes:

- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` → exit 0 (link-definition scaffold and the 10 canonical group headers intact).
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` → no match. The spec carries **no** raw `path:NN` reference today; `AGENTS.md` rule 27 compliance is a property to preserve, not one to establish. It also carries **no** inline `](path)` link — every cross-file link is already reference-style with all 8 definitions resolving on disk (verified by walking each definition target).

### Deviation 1 — the prior cycles' `build-*.md` plans are PRESERVED

Pre-flight step 3 deletes old `build-*.md` / `bld-*.md`. The `bld-*.md` artifacts are already gone (commit `99696bac`, "chore(builder): clear the closed cycles' build artifacts"), so only the six surviving `build-*.md` plans are at issue, and they are **not** deleted:

- `build-001-django_types-0_0_1.md`, `build-002-optimizer-0_0_2.md`, `build-044`, `build-045`, `build-046`, `build-048` are **committed** records of closed cycles. `build-002-optimizer-0_0_2.md` in particular is the precedent this plan cites throughout and the source of several verified facts below; deleting it would destroy the record of work now under review.
- The reasoning is `BUILD.md`'s own, under `### Cohorting, naming, and closure` ("Pre-flight for a round"): when the input to a cycle is already-built work, the prior artifacts are the record of that work and must survive. Every residual item here operates on already-built, already-released work.
- **Collision is avoided by naming, not by deletion.** Every artifact this plan creates is `bld-003-`-prefixed and the plan is `build-003-`-prefixed; none of those paths exists. The maintainer's dispatch instruction required exactly this ("use file naming to not conflict with existing concurrent bld work").

### Deviation 2 — the `built` state is skipped where the deliverable is Worker-1-exclusive

`docs/builder/ARTIFACT.md` `## Status field ownership` gives `built` to Worker 2, and `worker-0.md` `## Per-slice dispatch` maps `planned` → Worker 2. Items **R1 and R2** have no Worker 2 role that could set it:

- **R1** — `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move, and states outright that **Worker 2 never reads the rationale file** — "that is the point of the move." Dispatching a builder at it would hand the file to the one worker the mechanism exists to keep away from it.
- **R2** — `BUILD.md` `## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the **only** role that may mutate the spec. R2's entire deliverable is spec edits.

So for R1 and R2 the chain is **Worker 1 (plan + perform, `planned`) → Worker 3 (audit, `review-accepted` | `revision-needed`) → Worker 1 (final verification, `final-accepted`)**, and Worker 0 reads `planned` on those artifacts as "dispatch Worker 3", not Worker 2. Declared here, before dispatch, so no pass improvises the mapping.

**Corollary, recorded when R1's first review returned `revision-needed` (2026-08-07):** `worker-0.md` `## Per-slice dispatch` step 4 routes a Worker-3 `revision-needed` to Worker 2 for the apply-changes pass. On R1 and R2 that route does not exist — the same two rules that remove Worker 2 from the perform pass remove it from the fix. **The apply-changes pass for R1 and R2 is Worker 1's, and it sets `planned` again**, returning the artifact to the `planned` → Worker 3 mapping above. The loop is otherwise unchanged and repeats until Worker 3 has no unresolved finding.

The Worker 3 audit is **not** skippable alongside the Worker 2 build. `BUILD.md` names Worker 3 as a reader of the rationale file during review and as the pass that checks the finished implementation against it. A rewrite performed by the author is reviewed by an agent with no memory of why a sentence was cut — the only vantage point from which an over-cut looks like an over-cut. **R3 has real Worker 2 work** (durable-doc edits and, if drift is found, DB edits) and runs the full unmodified chain; its one sibling-spec sentence is reserved to Worker 1 (`### The one authorized sibling-spec edit`).

## Baseline-dirty out-of-scope files

Workers neither edit nor revert these, and never `git checkout` them (`AGENTS.md` rule 34).

`git status --short` was **empty** at pre-flight. It stopped being empty **during R1's re-review pass** — a concurrent session opened a cycle on the release-notes surface. Recorded here rather than in a later pass's artifact, because the change is Worker 0's to attribute:

- `CHANGELOG.md`
- `GOAL.md`
- `README.md`
- `TODAY.md`

Attribution is positive rather than inferred: this cycle's writable list contains none of these four paths, and every pass so far has been confined to the spec, its new rationale sibling, the `bld-003-*` artifacts, and worker memory. **None of these files is one any residual item writes**, so all four stay out of scope for the whole cycle. `CHANGELOG.md` in particular was already closed to this cycle by `AGENTS.md` rule 21 (`## Build-wide context flags`), so its dirtiness changes nothing about what may be edited — only about what a later `git status` means.

**Second growth, recorded at the close of R1 (2026-08-07).** The same concurrent session widened into the `TODO-BETA-053-0.1.5` → `TODO-BETA-060-0.1.5` card-id renumber that `KANBAN.md`'s card `TODO-ALPHA-052-0.1.0` scope describes ("32 occurrences across 10 files … One owner, one sweep, or not at all"). The out-of-scope list is now:

- `CHANGELOG.md`, `GOAL.md`, `README.md`, `TODAY.md`, `docs/README.md`
- `docs/SPECS/spec-030-connection_field-0_0_9.md`, `spec-032-full_relay-0_0_9.md`, `spec-033-connection_optimizer-0_0_9.md`, `spec-037-upload_file_image_mapping-0_0_11.md`, `spec-041-channels_router-0_0_14.md`, `spec-042-debug_toolbar-0_0_14.md`, `spec-044-debug_extension-0_0_14.md`
- `examples/fakeshop/apps/products/schema.py`, `examples/fakeshop/test_query/test_products_api.py`
- `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html` — the DB write and its regenerates

**Third change, recorded at the close of R2 (2026-08-07): the concurrent session COMMITTED.** `1f4b3265` ("docs: refresh the standing docs against the shipped `0.0.14` surface") is now `HEAD`, and every one of the fourteen paths listed above is clean again. Worker 0 verified this cycle's work was **not** swept into it (`git log --stat` over the three cycle paths shows `1f4b3265` touching none of them; the newest commit reaching `spec-003` is still `e1f9ed26`) — the standing hazard is real and this is the check that discharges it, never `git status` alone. Two **new** out-of-scope dirty paths replaced them:

- `docs/SPECS/NEXT.md`
- `docs/builder/BUILD.md` — an uncommitted edit moving the floor policy to Django `5.2.16`

The `BUILD.md` edit is the notable one: it is a standing workflow doc every later spawn in this cycle reads, so those spawns read the **edited** version. That is correct and desired — `BUILD.md` `## Floor verification` is the single canonical statement of the floor, and a worker must take it from there rather than from a number restated elsewhere. It changes nothing operationally here, because this cycle's floor-verification scope is `none`.

**Fourth change, recorded at the close of R2's first review (2026-08-07): both new paths committed too.** `HEAD` is now `4d1c512a` ("docs(workflow): correct the drifted identifiers in the build and spec flows"), and **the baseline-dirty list is empty again** — the only dirty paths are this cycle's four. Worker 0 re-verified across both commits that nothing of this cycle's was swept: `git log --stat` over the cycle paths shows neither `1f4b3265` nor `4d1c512a` touching one, and the spec diff is still exactly 78 insertions / 285 deletions. `HEAD` has now moved twice mid-cycle; any pass quoting a commit hash from this plan re-derives it rather than trusting it.

**This binds R3 specifically.** R3's archive audit sweeps `docs/SPECS/` and the kanban DB, so it will meet this churn head-on. Two consequences: a `docs/SPECS/spec-0NN` diff R3 finds is **presumptively the renumber sweep's**, to be attributed by content (a `TODO-BETA-053` → `060` token change) before it is treated as drift; and `examples/fakeshop/test_query/test_products_api.py` is one of the two files carrying the O4 live tests this plan's `### Test-plan coverage` table cites, so R3 reads it at its **current** content and never reverts it. `docs/SPECS/spec-003-…` is the one file in that directory dirty from **this** cycle; Worker 3 confirmed at R1's close that its diff is unchanged at 18 insertions / 224 deletions and carries no `TODO-<MILESTONE>-<NNN>` token, so the two edits do not overlap.

**Baseline exception for the final test-run gate**, recorded here because `BUILD.md` `## Final test-run gate` requires it in the plan's preamble to be honoured: `uv run pytest --no-cov`, `uv run ruff format --check .`, `uv run ruff check .`, and `git diff --check` all read the whole tree, so they will see this churn. A failure attributable to a file this cycle never wrote does **not** block `final-accepted` and does **not** route back through a residual item's loop; it is reported to the maintainer. The gate still reports each command's real result — the exception governs what a result *blocks*, never whether it is recorded honestly.

If the list grows again mid-cycle, workers **report it and never revert it**, and Worker 0 appends it here rather than a worker editing the plan.

## Concurrent-writable tracked binary / generated files

Churn in these is not proof a worker caused it (`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`). All four were clean at pre-flight; **three of the four stopped being clean during R1** — read `## Baseline-dirty out-of-scope files` above before treating any diff here as this cycle's. The "a diff here IS attributable" premise this section carried at pre-flight is **withdrawn** for those three:

- `examples/fakeshop/db.sqlite3` — **dirty from the concurrent renumber sweep as of R1's close.** **No residual item is expected to write it**: card 3 is already Done, its `SpecDoc.path` already points at the archived location, and its 8 glossary links already match the terms CSV exactly (verified below). A write happens only if R3's audit finds real drift. Compare `iterdump()` semantics, never file bytes.
- `KANBAN.md`, `KANBAN.html` — **dirty from that same session's regenerate.** Regenerated again only if R3 writes the DB.
- `docs/GLOSSARY.md` — DB-rendered; **still clean**, and **no residual item is expected to change it.** A diff here remains drift to investigate, not build output.

If R3 does write the DB, it applies its writes **on top** of the concurrent state without reverting, verifies by two-consecutive-regenerate byte-stability plus spot-checks rather than by "`git diff` is clean", and hands the mixed diff to the maintainer to reconcile at commit (`BUILD.md` `### Tracked binary / generated files`). It also re-runs `import_spec_terms --check` **after** the concurrent DB write rather than trusting the pre-flight baseline reading.

## Build-wide context flags

- **`0.0.2` shipped and the version quintet is at `0.0.14`.** No residual item touches `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, the GLOSSARY package-version line, or `uv.lock`.
- **No source or test file changes in this cycle.** Package source, `tests/`, and `examples/` code are read-only throughout. R3 may edit a docstring only if its audit finds a factually-false one, and that routes through Worker 2.
- **`CHANGELOG.md` is closed.** `AGENTS.md` rule 21 governs: no residual item edits it. Verified at pre-flight: `CHANGELOG.md` contains no `spec-003` reference at all. The `[0.0.2]`-versus-`[0.0.3]` optimizer dating tension is **explicitly card `TODO-ALPHA-052-0.1.0`'s** ("This card owns the CHANGELOG promotion, so the decision belongs on it", `KANBAN.md` scope); this cycle records it and does not touch it.
- **Sibling specs are read-only, with exactly one declared exception** (`### The one authorized sibling-spec edit`). `spec-002` and `spec-004` are the two spec-003 references; `spec-002` was reconciled by its own cycle yesterday and needs nothing. A pass that finds another sibling made stale by an R2 edit records it as a deferred item — it does not edit it.
- **The spec is already archived.** `BUILD.md` `### Spec stays at its working location` requires a move be plan-declared as a Worker-1-owned final-verification step. There is no move: `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` and `docs/SPECS/appx/spec-003-…-terms.csv` are already at their archived paths, `SpecDoc.path` already reads the archived path, and both `KANBAN.md` references already point there. **R1's new rationale file is therefore written directly to `docs/SPECS/appx/`** — the archived-companion location `AGENTS.md` rule 26 names — never to `docs/` first and moved after.
- **Only the maintainer commits.** No worker commits, and none creates or switches a branch.

## Worker-0-verified facts, passed into dispatch so no worker re-derives them

`worker-0.md` `## Closing out a kanban card` requires the live DB references be verified before a card/glossary edit is planned, because plan and spec text can carry stale ones. Read-only queries, run 2026-08-07:

- `Card.objects.get(number=3)` → `card_id` `DONE-003-0.0.2`, `status.key` `done`, `target_version.number` `0.0.2`, title `Optimizer O4 nested prefetch chains`. The card is **already Done**; no status flip is in scope, and the 2026-07-30 card renumber left 003 untouched (it rotated 045-068 only).
- `SpecDoc` for card 3 → name `spec-003-optimizer_nested_prefetch_chains-0_0_2`, **`path` already `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`**. No repoint needed. (`SpecDoc.path` is the writable column; `SpecDoc.url` is a read-only `@property` deriving from it — assigning `url=` raises.)
- `card.glossary_links.count()` → **8**, exactly matching the 8 rows in `docs/SPECS/appx/spec-003-…-terms.csv`: `djangotype`, `fk-id-elision`, `metaoptimizer_hints`, `only-projection`, `optimizerhint`, `plan-cache`, `queryset-diffing`, `schema-audit`. One row per anchor, so the CSV is importable (`worker-0.md` `### DONE-card invariants` — a green `check_spec_glossary` alone does not prove this).
- Card 3 carries **5 `CardItem`s** across three sections (`Scope` ×3, `Verified in upstream` ×1, `Note` ×1) and **no `Definition of done` section**. The single unticked item is the `Verified in upstream` row; card 2's equivalent row is likewise unticked, so this is the board's convention, not drift. **No card-body edit is in scope** unless R3 finds a factually-false sentence.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` Exit 0. **This is the baseline both R2 and R3 must not break.**
- Spec byte count before R1: **34,030 bytes / 447 lines**. Worker 1 reports the after-count in the R1 artifact.
- **Staged-anchor sweep:** `grep -rEn 'TODO\(spec-003|TODO-(ALPHA|BETA|STABLE)-003' .` → **three hits, all inside spec-003 itself** (its own `## Current state` pseudo-code fence, its `## Documentation updates` instruction, and `## Anchor and lint notes`). **Zero anchors in any source or test file.** `BUILD.md` `## Cross-slice integration pass` step 6 is therefore already discharged at baseline for source; R3 re-runs it as its backstop, and R2 owns the three in-spec survivors.

### The 8-anchor constraint — the trap in this cycle

`docs/SPECS/appx/spec-003-…-terms.csv` carries 8 anchors, and `check_spec_glossary.py` passes today because each has at least one link in the spec body. Both R1 (which moves text out of the spec) and R2 (which rewrites text) can silently drop the last remaining link for an anchor. The failure is not cosmetic: `import_spec_terms` is what a DONE card's glossary-link set is rebuilt from, so a dropped anchor breaks the card-wrap chain for card 3.

Spec-003 is **less fragile than spec-002 was** (which had three anchors each carried by a single link), but four of its anchors sit in exactly the sections R1 and R2 will rewrite hardest:

| Anchor | Where its link(s) live today | Risk |
|---|---|---|
| `queryset-diffing` | `## End-goal context` ("Future B8 queryset diffing"), `### B8 queryset diffing` | Both sections are drift targets (B8 has since **shipped**, D16) |
| `schema-audit` | `## End-goal context` (B6 list) | Single carrier, in a section R2 rewrites |
| `plan-cache` | `## End-goal context`, `## Current state` (`cacheable` bullet) | `## Current state` is being rewritten wholesale |
| `metaoptimizer_hints` | `## End-goal context` (B4 bullet) | Single carrier |
| `fk-id-elision` | `## End-goal context` (B2 bullet) | Single carrier |
| `only-projection` | `### Prefetch-boundary recursion` | Inside a fenced-pseudo-code section R2 replaces |
| `optimizerhint` | `### Hints are leaf operations` | Section survives but is rewritten |
| `djangotype` | `## Lookup paths vs resolver sentinel keys` | Section survives |

**Every pass that writes the spec re-runs `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` and quotes the result in its artifact.** A rewrite that drops an anchor keeps the anchor's link by re-siting it in the surviving contract prose — never by re-adding narration the item just removed, and never by editing the CSV.

### What R1 inherits that spec-002 did not

Spec-002's rationale move was a judgement call over thin, interleaved deliberation. Spec-003's is the opposite problem, and the shape is worth naming before Worker 1 opens the file, because the wrong instinct here is obvious and wrong in both directions:

- **Seven fenced pseudo-code blocks** — `## Current state` (the quoted "current depth-1 behaviour" fence), `### Same-query recursion`, `### Prefetch-boundary recursion` ×2, `### Lookup-path flattening`, `### Resolver sentinel keys` ×2 — propose or quote an implementation. (Corrected 2026-08-07 from "five", which this bullet's own parenthetical already contradicted: `grep -c '^```'` over `git show HEAD:<spec>` returns 14 markers, i.e. 7 fences. Worker 1 and Worker 3 measured it independently and agree; `BUILD.md` `## Claims are proven mechanically` — a count asserted in the same breath as the lesson it illustrates is routinely wrong, and this one was.) **Proposed code that landed under a different name is not deliberation and it is not contract** — it is a falsified present-tense claim. `worker-1.md` `### Performing the rationale move` rule 2 governs: *delete — do not move — prose the current decisions have falsified.* But the **design intent** each block encodes (why the child plan resets `prefix=""`, why the connector column must be injected after the walk, why `prefetch(obj)` is a leaf) is implementation-relevant rationale that **stays in the spec** under the load-bearing carve-out. Separating the two inside one fence is the whole job.
- **`## Documentation updates when O4 ships`** and **`## Anchor and lint notes`** are wholly discharged (D14, D15, D21). Discharged instructions are neither contract nor deliberation; they are history. Their *outcome* is a fact the spec may state once; the instruction itself goes or dies.
- **`## Implementation insertion points (O4)`** is 63 lines of pre-implementation line-number-adjacent guidance ("Line numbers below refer to the current O4 starting point and are approximate"). It is the single largest block of falsified present-tense prose in the file.
- The rationale file must carry, per `BUILD.md` `## Spec rationale extraction`, **an entry keyed to each spec section it serves**, naming: the alternatives rejected and why each lost; every change the decision has undergone with the round or later spec that caused it; and any claim the decision once made and may no longer make. The drift table below is R2's input, but **its "why" column is R1/R2's output** — that is precisely the maintainer's instruction that *explanations of the changes go in the rationale, not the spec*.

### The one authorized sibling-spec edit

Spec-003's `## Documentation updates when O4 ships` declares four obligations against other files. Three are fully discharged (D14). The fourth has **one residual sentence**:

> `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` `## B4 …` **`Depends on.`** — "The `.prefetch(Prefetch(...))` hint composes naturally with O4 (nested chains) and O6 (downgrade rule) **once those land**."

Both landed at `0.0.2`. This is spec-003's *own* declared documentation obligation ("remove … the `not yet implemented` rider on the B-slices that depend on nested resolver-key sentinels"), and the maintainer's mandate for this cycle is that the documentation be finished. **It is therefore in scope, and it is Worker 1's** — spec custody, performed during R3, recorded under `### Spec changes made (Worker 1 only)` with the spec-003 clause that licenses it. Worker 2 never edits a spec. The edit is one clause; nothing else in spec-004 is in scope, and no other sibling spec is opened.

### Verified spec-versus-HEAD drift — R2's input, verified by Worker 0 against source

Read at HEAD on 2026-08-07 with the symbol-qualified paths given. Each row is a claim the spec makes that HEAD complicates or falsifies. **A prescribed correction is not included: how the spec should read is Worker 1's call, and the alternatives it rejects belong in the rationale file.** Worker 1 re-verifies each row rather than trusting this table.

Four rows were independently spot-checked by Worker 0 against source after the sweep (D1, D2, D11, D14-ii) and all four confirmed.

| # | Spec claim | HEAD reality | Owner of the move |
|---|---|---|---|
| D1 | `## Current state` / `## Problem statement` / `## Definition of done` / insertion points: `_collect_scalar_only_fields` "walks scalar children only and silently drops any nested relation" | **Zero occurrences in `django_strawberry_framework/`.** Deleted exactly as the spec predicted. The replacement is the recursive call at `optimizer/walker.py::_plan_select_relation #"_walk_selections("` | O4 itself; already flagged at `KANBAN.md:240` and `:317` |
| D2 | `## Current state`: `plan_optimizations(selected_fields, model, info=None)` | `optimizer/walker.py::plan_optimizations` → `(selected_fields, model, info=None, *, runtime_prefixes=None, source_type=None)`; it passes no `prefix`, derives `enable_only` once, and returns `plan.finalize()` | `source_type` spec-018; `runtime_prefixes` spec-033; `enable_only`/`finalize()` spec-035 Decision 4. Correct wording already published at `docs/SPECS/spec-002-optimizer-0_0_2.md` |
| D3 | `## Current state`: "the final relation-dispatch block still has O4 TODO anchors instead of recursing into `sel.selections`", with a fenced quote of that block | The dispatch is `optimizer/walker.py::_walk_selections #"_dispatch_single_relation("`; no `TODO(spec-003…)` anchor exists in any source file | O4 itself |
| D4 | `## Current state`: `fk_id_elisions` is "currently relation paths … **O4 must migrate this bag**" | `optimizer/plans.py::OptimizationPlan.fk_id_elisions` — "Resolver keys elided because the source row already carries the target id." The migration the spec demands is **delivered** | O4 itself |
| D5 | `## Current state`: `OptimizationPlan` holds five things (`select_related`, `prefetch_related`, `only_fields`, `fk_id_elisions`, `cacheable`) | **Eleven** dataclass fields. The six the spec does not name: `planned_resolver_keys` (B3 strictness sentinel), `select_path_resolver_keys` / `prefetch_path_resolver_keys` (which resolver keys each path satisfies, so a B8 drop de-plans its subtree), and the three `finalized_*` frozensets precomputed by `finalize()`. Plus three `ClassVar` merge partitions enforced at import by `optimizer/plans.py::OptimizationPlan._assert_merge_field_inventory` | `planned_resolver_keys` is O4's own; the path maps and `finalized_*` are spec-033 / spec-035 |
| D6 | Spec is silent on plan immutability | `optimizer/plans.py::OptimizationPlan.finalize` swaps directive lists to tuples and computes three frozensets, so post-handoff mutation raises `AttributeError`; `::_assert_under_construction` rejects a merge onto a finalized plan | spec-035 (plan-cache poisoning guard) |
| D7 | `### Same-query recursion`: the proposed `else: # relation_kind == "select"` **inline block inside `_walk_selections`** | Landed with the same semantics but **extracted**: `optimizer/walker.py::_plan_select_relation`, reached via `::_dispatch_single_relation`. `_append_unique` is the public `optimizer/plans.py::append_unique`; the FK-column append moved to `walker.py::_record_relation_access` and is now `enable_only`-gated; `plan.select_related.append` is `append_unique` | O4 + spec-035 Decision 4 |
| D8 | `### Prefetch-boundary recursion`: `_build_child_queryset(field, target_type, info)` calls `target_type.get_queryset(qs, info)` | `optimizer/walker.py::_build_child_queryset(field, target_type, info, has_custom_qs)` routes through `utils/querysets.py::apply_type_visibility_sync(..., allow_sliced=True)` — the sealed-execution visibility boundary — never a direct hook call | spec-045 (Decision 5 degrade-to-unplanned is named in the docstring) |
| D9 | `### Prefetch-boundary recursion`: `_ensure_connector_only_fields(plan, parent_field)` carries the three connector rules in its body | `optimizer/walker.py::_ensure_connector_only_fields(plan, parent_field, *, enable_only=True)` keeps the name and the `if not plan.only_fields: return` guard, but the rules moved to `optimizer/join_taxonomy.py::_parent_join_column` via `optimizer/nested_planner.py::_connector_only_field`. All three rules survive **and the reverse-FK arm gained `reverse_one_to_one`** | spec-033 / the join-taxonomy extraction; `reverse_one_to_one` per `CHANGELOG.md:247` |
| D10 | `### Prefetch-boundary recursion`: proposed inline `if relation_kind == "prefetch":` block | Extracted to `optimizer/walker.py::_plan_prefetch_relation` + `::_build_prefetch_child_queryset` + `::_build_prefetch_child_queryset_from_base`. `plan_relation` was refactored exactly as the spec asked — `optimizer/walker.py::plan_relation` returns `tuple[str, str]` and constructs nothing | O4 itself |
| D11 | `### Prefetch-boundary recursion`: `Prefetch(full_path, queryset=child_qs)` — the lookup segment is the **field name** | The lookup segment is the **instance accessor**: `optimizer/walker.py::_plan_prefetch_relation #"lookup_path = f\"{prefix}{instance_accessor(django_field)}\""`. **This is a bug fix, not a refactor** — a reverse relation with no `related_name` has field name `book` but accessor `book_set`, and the spec's shape raised `AttributeError: invalid parameter to prefetch_related()`. Landed `2d3f5fad` (2026-06-12) | post-O4 fix; the same rule is documented in `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` |
| D12 | Spec is silent on nested Relay connections | A nested `<field>Connection` selection does **not** reach `_plan_prefetch_relation`: `optimizer/walker.py::_walk_selections #"if resolved is not None and resolved[0] == \"connection\":"` routes to `optimizer/nested_planner.py::plan_connection_relation` with pluggable windowed / lateral strategies | spec-033; already recorded in `docs/SPECS/spec-002-optimizer-0_0_2.md` |
| D13 | `### Resolver sentinel keys`: `_resolver_key` belongs in `walker.py`; `_runtime_path_from_info` and `_is_fk_id_elided` belong in `types/resolvers.py` | Both key helpers landed **public in `plans.py`** — `optimizer/plans.py::resolver_key` and `::runtime_path_from_info` (delegating to `::runtime_path_from_path`, bounded by `_MAX_PATH_DEPTH = 1024`). `walker.py` and `types/resolvers.py` both import them, so there is one implementation rather than two mirrored ones. **`_is_fk_id_elided` and `_get_relation_field_name` do not exist at all**; the elision check is inlined at `types/resolvers.py::_make_relation_resolver.forward_resolver #"if elisions and key in elisions:"` so one `info.path` walk is shared with `_check_n1`. **The proposed key format `Type.field@a.b.c` is correct verbatim, `None`-parent fallback included** — keep it | O4's own shipping commit `4b7d7703` |
| D14 | `## Documentation updates when O4 ships` — four bullets | (i) **discharged, and the instruction is itself false**: spec-002 has no `## Current state` section any more; it carries `## Shipped slices` → `### O4 — Nested prefetch chains`, `## Visibility status` #"O1 through O6 have shipped.", and `## Implementation checklist` #"- [x] O4". (ii) **discharged but for one rider** — see `### The one authorized sibling-spec edit`. (iii) **fully discharged** — zero `TODO(spec-003` anchors in source or tests. (iv) **discharged**; both symbols it names (`_get_relation_field_name`, `_is_fk_id_elided`) do not exist, and `grep -rn "\bO4\b" django_strawberry_framework/` returns **zero hits package-wide** | the spec-002 residual cycle (i); O4 itself (iii, iv) |
| D15 | `## Anchor and lint notes`: "The O4 pseudocode anchors have already been staged in the relevant source and test files … `ruff check .` may report `ERA001` until O4 is implemented. Leave those findings in place" | **False in its entirety.** No `TODO(spec-003…)` anchor survives; no `ERA001` finding is being tolerated for O4. The two TODO comments `review_inspect.py` reports in `walker.py` are `TODO(spec-035)` | O4 itself |
| D16 | `### B8 queryset diffing` and `## End-goal context`: B8 is "future" work that "will normalize" lookup paths | **B8 shipped**: `optimizer/plans.py::diff_plan_for_queryset` + `::prune_unsupportable_select_related`, wired at `optimizer/extension.py #"# B8 pre-publish prune"`. The insertion-point instruction "leave the pseudo-code anchor intact" is dead | spec-004 B8 |
| D17 | `### Lookup-path flattening`: proposed `lookup_paths(plan)` body reads `inner._prefetch_related_lookups` directly | `optimizer/plans.py::lookup_paths` short-circuits on `plan.finalized_lookup_paths`, else delegates to `::_lookup_paths_from_parts`; `::_prefetch_lookup_paths` keeps the exact proposed name and `(entries, prefix="")` signature, recurses to arbitrary depth, and adds a `prefetch_to is None` skip plus routing through `::_consumer_prefetch_lookups` (the single reader of that Django-private contract). Position matches the insertion-point instruction ("End of file"), not the design-section one ("next to `OptimizationPlan`") | O4 + spec-035 |
| D18 | `### Resolver sentinel keys`: a single `runtime_path` tuple per selection | `optimizer/walker.py::_resolver_identities_for` computes a **cartesian product** of `_optimizer_runtime_prefixes` × response keys, returning a tuple of identities. Alias preservation on merged nodes landed as the spec's first option: `optimizer/walker.py::_merge_aliased_selections #"_optimizer_response_keys"` | spec-033 (alias / connection runtime-prefix fan-out) |
| D19 | `## Definition of done` bullet 8: "with TODO-anchored pseudo-code findings left untouched" | Moot — no such findings remain (D15) | O4 itself |
| D20 | `## Desired behavior`: `{ allEntries { item { category { name } } } }` is "1 query total" | Still true of the **package** (`tests/optimizer/test_walker.py::test_plan_emits_nested_select_related_chain_depth_2` pins `select_related == ("item","item__category")` and the exact three `only_fields`). The **live fakeshop** equivalent `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http` now pins **3** queries, because fakeshop's `ItemType`/`CategoryType` gained a cascade `get_queryset` that O6-downgrades each forward FK to a `Prefetch` | spec-034 (the example project's cascade, not the package) |
| D21 | `## Implementation insertion points (O4)` — 63 lines of pre-implementation guidance, opening "Line numbers below refer to the current O4 starting point and are approximate" | Every instruction is discharged. Most landed at the named site; the exceptions are the two relocations (D7/D10 extracted into named helpers, D13 into `plans.py`), the dead B8 anchor (D16), and the two `types/resolvers.py` symbols that never existed (D13) | O4 itself |
| D22 | `## Missing .py files`: "None. Every O4 change lands in an existing module: `walker.py`, `plans.py`, `extension.py`, `resolvers.py`, `hints.py`" | True of the O4 change itself, and **false as a present-tense map of the surface**: the O4 surface now also spans `optimizer/nested_planner.py`, `optimizer/selections.py`, `optimizer/join_taxonomy.py`, and `optimizer/nested_fetch.py`, none of which existed when the spec was written | spec-033 and the later DRY extractions |

Two things this table deliberately does **not** say. First, that every row must change the spec: some rows are the spec being *superseded* rather than *wrong*, and the spec-004 / spec-033 / spec-035 family already owns much of the optimizer's later surface — Worker 1 decides per row whether the contract is restated, pointed elsewhere, or dropped to the rationale. Second, that the list is exhaustive; it is Worker 0's verified floor, and R2 owns the full sweep.

**The scope trap specific to this spec.** Spec-003 is a *child* spec whose parent (spec-002) explicitly delegates the O4 record to it, and whose own subject matter was later extended by spec-033 (nested connections), spec-035 (hardening, immutability, `enable_only`), spec-045 (visibility boundary), and spec-018 (`source_type`). Reconciling it must not turn it into a summary of all four. Rows D8, D9, D12, D18, and D22 are exactly where the pull toward over-absorbing is strongest: the correct move for each is a pointer to the owning spec, not a transplanted paragraph.

### Test-plan coverage — nothing was skipped

The maintainer's instruction "MAKE SURE NOTHING WAS SKIPPED IN THE CODE" was discharged by a per-test existence check against the spec's `## Test plan`. Recorded here so no pass re-derives it, and so R2 knows which sentences it may safely leave alone.

| Spec test-plan item | At HEAD |
|---|---|
| `test_plan_emits_nested_prefetch_chain_depth_2` | `tests/optimizer/test_walker.py` — **exact name** |
| `test_plan_emits_nested_select_related_chain_depth_2` | `tests/optimizer/test_walker.py` — **exact name**; pins the spec's exact three `only_fields` |
| `test_plan_combines_prefetch_boundary_with_inner_select_related` | `tests/optimizer/test_walker.py` — **exact name** |
| `test_plan_propagates_uncacheable_nested_custom_get_queryset` | `tests/optimizer/test_walker.py` — **exact name** |
| `test_plan_honors_optimizer_hints_at_nested_depth` | `tests/optimizer/test_walker.py` — **exact name** |
| `test_plan_honors_prefetch_obj_hint_does_not_walk_inner_selections` | `tests/optimizer/test_walker.py` — **exact name** |
| `test_plan_records_nested_fk_id_elision_with_resolver_key` | `tests/optimizer/test_walker.py` — **exact name**; asserts `("category@items.category",)` |
| fragment / alias / directive variants | `tests/optimizer/test_walker.py::test_plan_nested_prefetch_respects_fragment_alias_and_directive_shapes` and `::test_plan_merges_fragment_branches_before_prefetch_queryset_creation` |
| `test_optimizer_prefetches_nested_reverse_fk_depth_2` (3 queries) | **Promoted to the live tier**: `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http`, pinning exactly 3 queries over real `/graphql/` HTTP (`AGENTS.md` rule 10 / the live-first rule) |
| `test_optimizer_selects_nested_forward_fk_depth_2` (1 query) | **Promoted to the live tier** as `::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http`; see D20 for why its count is 3 |
| `test_optimizer_strictness_accepts_nested_planned_relation` | `tests/optimizer/test_extension.py` — **exact name** |
| `test_optimizer_nested_fk_id_elision_does_not_leak_to_sibling_branch` | Covered on two axes under other names: `examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_fk_id_elision_does_not_leak_to_sibling_root_in_http_query` (sibling **root**) and `tests/types/test_resolvers.py::test_b2_forward_fk_id_elision_does_not_leak_across_parent_types` (parent type). **The sibling-*nested*-branch axis under one parent type is untested** — see the correctness-audit observations below |
| `test_optimizer_nested_prefetch_with_custom_get_queryset_marks_uncacheable` | `tests/optimizer/test_extension.py` — **exact name** |
| "Use the real fakeshop service seeders (`services.seed_data(n)`)" | Both extension tests open with `services.seed_data(1)` |
| the three `tests/types/test_resolvers.py` items | All three present, incl. `::test_b2_forward_fk_id_elision_does_not_leak_across_parent_types` and `::test_runtime_path_from_info_strips_list_indexes_and_keeps_aliases`; plus `::test_b2_forward_fk_id_elision_ignores_bare_field_name_key`, which pins that the depth-1 leak the spec identified is closed |
| `TestLookupPaths` "after the existing `TestOptimizationPlanIsEmpty` class" | `tests/optimizer/test_plans.py::TestLookupPaths` — **exact class name, exact position**, six methods |

Seven O4 walker tests exist **beyond** the plan (depth-3 chains, the three `_ensure_connector_only_fields` rule arms, hint-adaptation and hint-rejection paths).

### The read-only correctness audit — findings

All four contracts the maintainer named were verified present. **No defect found.** Four observations, recorded so R2 does not mistake any of them for drift to "fix":

1. **All four B2 guards survive, in one predicate** — `optimizer/walker.py::_plan_select_relation #"if ("`: FK-points-at-target-pk (via `optimizer/field_meta.py::FieldMeta.from_django_field #"fk_id_elision_eligible=("`, which additionally excludes composite PKs — a hardening beyond the spec), no custom `get_queryset`, no custom id resolver, and target-pk-only selection (`::_selected_scalar_names` returns `None` rather than a set if any child is a relation, so the equality can never accidentally hold).
2. **`cacheable` propagates in exactly one place, deliberately.** `optimizer/walker.py::_absorb_child_plan` → `optimizer/plans.py::OptimizationPlan.merge_metadata_from #"if not other.cacheable:"`, folded into the merge "so a future third site cannot forget it". `_plan_prefetch_relation` also sets the flag *before* building the child, so it survives a degraded child build.
3. **The elision path deliberately does NOT record `select_path_resolver_keys`** — an elision reads a column already on the parent row and adds no query, so a B8 consumer-wins drop must not strip it. Documented at `optimizer/walker.py::_plan_prefetch_relation #"Nested FK-id elisions are deliberately NOT recorded"`, pinned by `tests/optimizer/test_extension.py::test_b8_consumer_wins_prefetch_preserves_nested_fk_id_elision`. **Correct as designed; not drift.**
4. **An unguarded ordering invariant.** `optimizer/walker.py::_record_relation_access` must run *before* the elision check in `_plan_select_relation`, because it appends the FK `attname` the elided resolver later reads (`types/resolvers.py::_build_fk_id_stub`). Reversing them would silently reintroduce an N+1. It is documented in the helper's docstring and there is **no automated guard**. Not a defect; a maintainer-facing note for the deferred-work catalog.

Two further observations for the catalog rather than for R2: `optimizer/plans.py::_prefetch_lookup_paths` recurses with no depth cap while its sibling `::runtime_path_from_path` is explicitly bounded (theoretical asymmetry only — the walker cannot construct a cyclic `Prefetch` graph); and the sibling-nested-branch resolver-key axis noted in the test table is untested-but-correct, since the key format does distinguish those branches by runtime path.

### Every reference TO spec-003 (verified by grep, 2026-08-07)

The archive already landed, so this table is R3's **verification** list, not a rewrite list. Every entry already reads correctly; R3 confirms and reports, and only edits if one is wrong.

| Location | Current text | Status |
|---|---|---|
| `KANBAN.md:144`, `:4819` (+ hits in `KANBAN.html`) | `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` | **Generated** — already correct; never hand-edit |
| `KANBAN.md:240`, `:317` | card `TODO-ALPHA-052-0.1.0` scope items naming this spec's stale sites | Generated; the prose is `CardItem.text`. `:317`'s four named sites are all in the drift table (D1, D2, D14-i, D14 parent-spec clause). R3 decides whether a discharged scope item is R3's to retire or card 052's — **default is card 052's** |
| `docs/SPECS/spec-002-optimizer-0_0_2.md` `## Purpose` | "the detailed O4 design and implementation record belongs to `docs/SPECS/spec-003-…`" | Read-only sibling; **correct and load-bearing** — it is the clause that makes this spec the O4 record |
| `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`, `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` (10 occurrences across 10 lines) | the two prior rationales' accounts of the optimizer split | Read-only; **R1 must not duplicate their content** — spec-002's rationale already narrates why O4 was extracted into its own spec |
| `docs/builder/build-002-optimizer-0_0_2.md` (11 occurrences across 10 lines) | the prior cycle's plan | Historical artifact; correct as history |

No hit in `CHANGELOG.md`, `README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, or `docs/README.md`. The sweep is re-run by R3, not trusted from this table.

**The direction this table cannot show** is the one inside the new file: R1's rationale lands at `docs/SPECS/appx/`, two levels below `docs/`, so its link definitions need `../../GLOSSARY.md` for a `docs/` target and `../spec-NNN-….md` for a `docs/SPECS/` sibling. The archived siblings (`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`) show the shape.

## Artifact list

- `docs/builder/bld-003-r1-rationale_move.md`
- `docs/builder/bld-003-r2-spec_reconciliation.md`
- `docs/builder/bld-003-r3-doc_completion_archive.md`
- `docs/builder/bld-003-final.md`

No `bld-integration.md`-equivalent: a cross-slice integration pass exists to find duplication across slices that landed source, and this cycle lands none. Its live obligations are folded in — the staged-anchor sweep (`BUILD.md` `## Cross-slice integration pass` step 6) runs in R3, and the cross-artifact read runs in the final gate.

## Checklist

- [x] R1: Spec rationale extraction into `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` (Worker 1 performs the move; Worker 3 audits it; Worker 1 final-verifies) -> `docs/builder/bld-003-r1-rationale_move.md`
- [x] R2: Reconcile the spec with HEAD — every claim the package falsifies is restated as the contract that actually holds, or handed to the spec that now owns it; the explanation of each change lands in the rationale, never in the spec -> `docs/builder/bld-003-r2-spec_reconciliation.md`
- [x] R3: Finish the documentation and audit the archive — durable-doc audit of the O4 surface, the one authorized `spec-004` rider edit, the three-direction cross-reference sweep, `SpecDoc.path` / terms-CSV verification, and the `TODO(spec-003` / `TODO-ALPHA-003` staged-anchor sweep -> `docs/builder/bld-003-r3-doc_completion_archive.md`
- [x] Final test-run gate -> `docs/builder/bld-003-final.md`

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
