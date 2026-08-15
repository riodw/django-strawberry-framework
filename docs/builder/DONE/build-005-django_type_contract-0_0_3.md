# Package build plan: django_type_contract / 0.0.3 (005)

Spec source: `docs/SPECS/spec-005-django_type_contract-0_0_3.md` (**already archived** — the spec, its `-terms.csv`, the `SpecDoc.path` row, and both `KANBAN.md` references already sit at their post-archive locations; item R3 verifies rather than performs the move)
Target release: `0.0.3` (**shipped long ago** — card `DONE-005-0.0.3`, `target_version.number` `0.0.3`; the package is at `0.0.14` in `pyproject.toml`)
Date created: 2026-08-08
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging. A fact told twice across the spec and its rationale sibling goes stale in one of them — the rationale carries the deliberation, the spec carries the contract, and neither restates the other.
Ownership partition: none; sequential residual items. (Declared explicitly rather than omitted, per `worker-0.md` `### Ownership partition`, so an interrupted item's output stays attributable against a tree a concurrent cycle is also writing.)
Hot-path declaration: none. No residual item changes package source, so no item runs per request, per resolver, per row, per connection, or per outbound message.
Floor-verification scope: none. No residual item touches a Django / Strawberry / channels integration seam — the cycle edits the spec, its new rationale sibling, and (only if the audit finds drift) DB-rendered docs.
Pre-flight: passed on 2026-08-08 with **four** recorded deviations (below); baseline: nine dirty entries, **all** of them the concurrently-running spec-004 cycle's or its fallout — see `## Baseline-dirty out-of-scope files`; cleanup: **nothing cleared** (Deviations 1, 3, 4), every path this plan creates verified absent.

## This is a residual-completion cycle, not a fresh build

Spec-005 is a **contract spec**: it has no `## Slice checklist`, no `## Doc updates`, and no implementation plan. Its deliverable was a *boundary* — which `Meta` knobs are applied, which are rejected, which hard constraints are temporary — and that boundary shipped at `0.0.3`, eleven minor versions ago. What remains is the deliverable set the shipped cycle never produced, plus the reconciliation that fifty-odd later specs made necessary.

The immediate precedent is the **spec-004 residual cycle** (`docs/builder/build-004-optimizer_beyond-0_0_3.md`), which is **still in flight in a concurrent session** as this plan is written — its R1 box is `- [x]`, its R2 artifact exists, its R3 artifact does not. That cycle is itself modelled on spec-003 (`20a9752f`), spec-002 (`d613887c` / `a76da376`), and spec-001 (`cfd1f873`). This plan follows the same three-item shape and, critically, the same collision-avoidance discipline: **every path this cycle creates is `bld-005-` / `build-005-` prefixed**, and nothing belonging to another cycle is deleted, reverted, or re-seeded.

**What makes this spec different from its three predecessors.** Spec-004 was falsified in its *details* — symbol names, tuple arity, a dated spike. Spec-005 is falsified in its *subject*. Three of its four `## Topics` describe constraints that no longer exist:

- the one-model-one-type registry constraint was **lifted** at `0.0.6` by `Meta.primary` (spec-018);
- consumer override semantics were **shipped** at `0.0.6` (spec-019) — and the *diagnosis* spec-005 gives for why they were broken was falsified before that, at `0.0.4`;
- the accepted/deferred `Meta`-key partition it enumerates has moved from 5 allowed / 6 deferred to **17 allowed / 3 deferred**.

Only the fourth topic — invalid `Meta.fields` / `Meta.exclude` names — is true at HEAD exactly as written. So the reconciliation here is not a sweep for stale symbols; it is a document whose four load-bearing sections have to be re-decided one at a time.

### Residual scope (this cycle's actual work)

- **R1 — spec rationale extraction.** `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` does not exist. `docs/builder/BUILD.md` `## Spec rationale extraction` makes the move the first substantive action of a build and pre-flight step 7 gates dispatch on it; the shipped cycle predates the rule. Worker 1 is the only role that may perform it. See `### What R1 inherits`.
- **R2 — reconcile the spec with what landed and what later specs corrected.** The maintainer's framing: *make sure the spec matches what actually exists, make sure the code is correct, and where later updates corrected what landed, the spec reflects that; the explanation of each change goes in the rationale, never in the spec.* Twenty verified drift rows are tabled below. Worker 1 is the only role that may edit the spec.
- **R3 — finish the documentation and audit the archive.** Verify the durable docs (`docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`) describe the shipped contract; verify the already-performed archive is complete in all three cross-reference directions, in the kanban DB, and in the terms-CSV importability chain; and run the `TODO(spec-005` / `TODO-<MILESTONE>-005` staged-anchor sweep.

**"Make sure the code is correct" is a read-only audit obligation, not a licence to change source.** Worker 0's pre-dispatch audit (`### The read-only correctness audit — findings`) found **no defect** in the shipped contract paths, and specifically confirmed that the original `Meta.interfaces` mistake this spec exists to prevent — a key validated but never applied — is **not** repeated by any of the seventeen keys now in `ALLOWED_META_KEYS`. The one claim that looked like a code defect (`D11`) resolved on inspection into a **later deliberate correction to the code that the spec never absorbed**, which makes it R2's work and not a builder's. If R2 or R3 finds a genuine correctness defect in shipped source, it is recorded as a finding and escalated to the maintainer — it does not become a source edit inside a documentation cycle.

## Pre-flight outcome (7 steps, `docs/builder/worker-0.md` `## Pre-flight procedure`)

1. **Working-tree baseline is explicit.** `git status --short` → nine entries, every one attributable to the concurrent spec-004 cycle or to the `scripts/clean_up.py` incident that cycle already recorded. See `## Baseline-dirty out-of-scope files`. HEAD is `346d6731`.
2. **`scripts/review_inspect.py` runs.** `uv run python scripts/review_inspect.py django_strawberry_framework/types/base.py --output-dir docs/shadow --stdout` emitted its overview (24 imports, 31 symbols, 16 control-flow hotspots, **0** TODO comments, 15 repeated string literals). Working, and run against the module this cycle actually reads.
3. **Build artifacts are reset — DEVIATION 1, see below.** Verified instead that every path this plan creates is absent: no `docs/builder/build-005*`, no `docs/builder/bld-005*`, no `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`.
4. **`.gitignore` lists the untracked scratch paths.** `docs/shadow/` (line 174), `docs/builder/worker-memory/` (188), `docs/builder/temp-tests/` (192). Present.
5. **Scratch directories are cleared — DEVIATIONS 3 and 4, see below.** `docs/builder/temp-tests/` is empty. `docs/shadow/` and `docs/builder/worker-memory/` were **not** touched: both hold the concurrent cycle's live state.
6. **Spec-doc consistency check.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` Exit 0. Baseline for the constraint in `### The 7-anchor constraint`.
7. **Spec rationale is extracted.** **Not done — it is item R1 of this cycle.** Ordinarily this gates dispatch. Here it cannot, because R1 *is* the dispatch: the work whose spawns the gate protects was built and released before this plan existed, so there is no builder left to protect. R1 runs first regardless, so every later spawn in this cycle reads the smaller spec exactly as the rule intends.

Two further baselines recorded at pre-flight, both green, both re-checked by any pass that writes:

- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-005-django_type_contract-0_0_3.md` → exit 0 (link-definition scaffold and the 10 canonical group headers intact).
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' docs/SPECS/spec-005-django_type_contract-0_0_3.md` → **no match**. The spec carries no raw `path:NN` reference today; `AGENTS.md` rule 27 compliance is a property to preserve, not one to establish. Every cross-file link is already reference-style with all 10 group headers present and every definition resolving on disk.

Spec size before R1: **13,346 bytes / 154 lines**, **zero** fenced code blocks (`grep -c '^```'` → 0). Worker 1 reports the after-count in the R1 artifact. The absence of pseudo-code is the structural difference from spec-004, whose eight fenced blocks were the hardest part of its move: spec-005's deliberative layer is **prose argument and predicted design**, not proposed implementation.

### Deviation 1 — a CONCURRENT cycle's `build-*.md` and `bld-*.md` artifacts are PRESERVED

Pre-flight step 3 deletes old `build-*.md` / `bld-*.md`. They are **not** deleted here, and the reason is stronger than the spec-004 cycle's:

- `docs/builder/build-004-optimizer_beyond-0_0_3.md`, `bld-004-r1-rationale_move.md`, and `bld-004-r2-spec_reconciliation.md` belong to a cycle that is **running right now in another session** — its R2 checkbox is still `- [ ]` and its R3 artifact has not been created. Deleting them would destroy an active cycle's contract mid-flight, not merely a closed cycle's record.
- The seven older `build-*.md` plans are **committed** records of closed cycles, and `BUILD.md` `### Cohorting, naming, and closure` ("Pre-flight for a round") already establishes that when a cycle's input is already-built work, the prior artifacts are the record of that work and must survive. Every residual item here operates on already-built, already-released work.
- **Collision is avoided by naming, not by deletion.** Every artifact this plan creates is `bld-005-`-prefixed and the plan is `build-005-`-prefixed; none of those paths exists.

### Deviation 2 — the `built` state is skipped where the deliverable is Worker-1-exclusive

`docs/builder/ARTIFACT.md` `## Status field ownership` gives `built` to Worker 2, and `worker-0.md` `## Per-slice dispatch` maps `planned` → Worker 2. Items **R1 and R2** have no Worker 2 role that could set it:

- **R1** — `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move, and states outright that **Worker 2 never reads the rationale file** — "that is the point of the move." Dispatching a builder at it would hand the file to the one worker the mechanism exists to keep away from it.
- **R2** — `BUILD.md` `## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the **only** role that may mutate the spec. R2's entire deliverable is spec edits.

So for R1 and R2 the chain is **Worker 1 (plan + perform, `planned`) → Worker 3 (audit, `review-accepted` | `revision-needed`) → Worker 1 (final verification, `final-accepted`)**, and Worker 0 reads `planned` on those artifacts as "dispatch Worker 3", not Worker 2. Declared here, before dispatch, so no pass improvises the mapping.

**Corollary, carried forward from the two prior residual cycles:** `worker-0.md` `## Per-slice dispatch` step 4 routes a Worker-3 `revision-needed` to Worker 2 for the apply-changes pass. On R1 and R2 that route does not exist — the same two rules that remove Worker 2 from the perform pass remove it from the fix. **The apply-changes pass for R1 and R2 is Worker 1's, and it sets `planned` again**, returning the artifact to the `planned` → Worker 3 mapping above. The loop is otherwise unchanged and repeats until Worker 3 has no unresolved finding.

The Worker 3 audit is **not** skippable alongside the Worker 2 build. `BUILD.md` names Worker 3 as a reader of the rationale file during review and as the pass that checks the finished implementation against it. A rewrite performed by the author is reviewed by an agent with no memory of why a sentence was cut — the only vantage point from which an over-cut looks like an over-cut. **R3 may have real Worker 2 work** (durable-doc edits and, if drift is found, DB edits) and runs the full unmodified chain when it does; if its audit finds nothing to change, it closes as a procedural-closure item through Worker 1 alone (`BUILD.md` `### Procedural-closure slices`).

### Deviation 3 — `docs/shadow/` was not emptied

Pre-flight step 5 clears it. It was not: it holds the concurrent spec-004 cycle's optimizer overviews, plus this cycle's step-2 `types/base.py` smoke.

This is safe and changes nothing operationally. `docs/shadow/` is gitignored, regenerable, and — per `AGENTS.md` rule 23 — **each generator clears its own folder before writing**, so a stale overview cannot be read as fresh output by any pass that runs the helper. Both workers that may run `review_inspect.py` in this cycle regenerate what they read. A pass that wants a file it did not generate itself regenerates it rather than trusting the folder's mtime.

### Deviation 4 — worker memory is NAMESPACED, not re-seeded

Pre-flight step 5 re-seeds the four `docs/builder/worker-memory/worker-<N>.md` files empty. Doing so here would **destroy the concurrent spec-004 cycle's live memory** — `worker-1.md` (4,580 bytes) and `worker-3.md` (3,956 bytes) were both written today, `worker-3.md` at 09:19, minutes before this pre-flight ran.

So this cycle uses its own namespace: **`docs/builder/worker-memory/spec-005-worker-<N>.md`**, seeded empty by Worker 0 at plan creation. The rule's intent — a private notebook per worker that persists across a single build and is invisible to every other worker — is preserved exactly; what changes is only that two concurrent builds no longer collide in one file, which the rule never contemplated and which would have broken isolation in **both** directions. Every dispatch prompt in this cycle names the namespaced path and the standing "do not read the other workers' memory files" instruction; it additionally forbids reading the un-namespaced `worker-<N>.md` files, which belong to the other cycle.

## Baseline-dirty out-of-scope files

Workers neither edit nor revert these, and never `git checkout` them (`AGENTS.md` rule 34). Attribution is positive, not inferred: this cycle's writable set is the archived spec-005 file, its new rationale sibling, the four `bld-005-*` artifacts, this plan, and the four namespaced memory files — **no entry below is in any of them.**

- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` (`M`) — the concurrent cycle's R2 output, mid-flight.
- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` (`??`) — the concurrent cycle's R1 deliverable.
- `docs/builder/bld-004-r1-rationale_move.md`, `docs/builder/bld-004-r2-spec_reconciliation.md`, `docs/builder/build-004-optimizer_beyond-0_0_3.md` (`??`) — the concurrent cycle's artifacts and plan.
- `docs/builder/bld-003-final.md`, `bld-003-r1-rationale_move.md`, `bld-003-r2-spec_reconciliation.md`, `bld-003-r3-doc_completion_archive.md` (`D`) — four committed artifacts deleted by something outside both cycles. The spec-004 plan records the attribution in full at its `### Fifth change` and flags it as **maintainer action needed**; restoring them means `git checkout -- <path>`, which `AGENTS.md` rule 34 bans while concurrent sessions write this tree. **No worker in this cycle restores them.** Their content is safe at `20a9752f`.

**Expect this list to grow.** The spec-004 cycle recorded four separate growth events across two days, including a concurrent session committing mid-cycle. `HEAD` may move during this cycle; **any pass quoting a commit hash from this plan re-derives it rather than trusting it**, and proves its own work was not swept into someone else's commit with `git log --stat` over this cycle's paths — never `git status` alone (`AGENTS.md` #"Staged `git mv` gets swept by a concurrent commit" is the standing hazard). If the list grows, workers **report it and never revert it**, and Worker 0 appends it here rather than a worker editing the plan.

### First growth, recorded at the close of R1's review (2026-08-08)

It grew twice during R1's review pass, exactly as predicted. Reported by Worker 3, appended by Worker 0. **Nothing was reverted, and no worker may revert any of it.** `HEAD` has not moved (`346d6731`). Newly baseline-dirty, all out of scope:

- `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3` — a concurrent card-wrap.
- `docs/SPECS/spec-063-structural_templates-0_1_6.md` and `docs/SPECS/spec-063-structural_templates-0_1_6-terms.csv` (`??`) — a new live spec and its terms sibling from the concurrent `NEXT.md` authoring flow. (The CSV surfaced one pass later and is appended here rather than given its own growth section.)
- `BACKLOG.md`, `multi-root-schedule-graph-reproduction.md`.
- `docs/SPECS/spec-041-channels_router-0_0_14.md`, `spec-042-debug_toolbar-0_0_14.md`, `spec-043-test_client-0_0_14.md`, `spec-052-beta_release-0_1_0.md`, `spec-053-graph_substrate-0_1_1.md` — sibling specs touched by the same concurrent flow.

**This revises the premise `## Concurrent-writable tracked binary / generated files` was written on.** "All four are clean at this pre-flight, so a diff is presently attributable" is **no longer true** for `KANBAN.md`, `KANBAN.html`, or `examples/fakeshop/db.sqlite3`; only `docs/GLOSSARY.md` is still clean. **R3 must re-verify DB / KANBAN / GLOSSARY state itself** — comparing `iterdump()` semantics rather than file bytes, and verifying by two-consecutive-regenerate byte-stability rather than by "`git diff` is clean" — and hand any mixed diff to the maintainer.

**This cycle's own work was not swept in.** Worker 3 re-checked both R1 output files byte-identical at close of pass, and `git log --stat -- docs/SPECS/spec-005-django_type_contract-0_0_3.md` shows the newest commit reaching the spec is still `ff65666d` ("docs: normalize review citations to their durable records"), which predates this cycle. That is the check that discharges the standing hazard — never `git status` alone.

**Second change — the growth above was COMMITTED, and `HEAD` moved (2026-08-08, close of R1's re-review).** `HEAD` is now `ff03c137`; the concurrent session committed the entire `### First growth` set (`BACKLOG.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, `multi-root-schedule-graph-reproduction.md`, sibling specs 041 / 042 / 043 / 052 / 053, and both `spec-063` files). **Those paths are now clean, so the list above is partly historical** — a later pass reading it should not expect them dirty. Worker 3 verified this cycle's work was **not** swept into that commit (`git diff --name-status 346d6731 HEAD` lists none of it; spec-005's newest commit is still `ff65666d`) and that spec-005 is byte-identical at both commits, so every measurement recorded in the R1 artifact remains valid. The four `docs/builder/bld-003-*.md` deletions are **still** staged-deleted and still need the maintainer's decision.

**Baseline exception for the final test-run gate**, recorded here because `BUILD.md` `## Final test-run gate` requires it in the plan's preamble to be honoured: `uv run pytest --no-cov`, `uv run ruff format --check .`, `uv run ruff check .`, and `git diff --check` all read the whole tree, so they will see the concurrent cycle's churn. A failure attributable to a file this cycle never wrote does **not** block `final-accepted` and does **not** route back through a residual item's loop; it is reported to the maintainer. The gate still reports each command's real result — the exception governs what a result *blocks*, never whether it is recorded honestly.

## Concurrent-writable tracked binary / generated files

Churn in these is not proof a worker caused it (`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`). All four are **clean at this pre-flight**, so a diff is presently attributable — a premise to re-check at every pass, not to inherit, given that the spec-004 cycle watched all four go dirty and back over two days.

- `examples/fakeshop/db.sqlite3` — **no residual item is expected to write it**: card 5 is already Done, its `SpecDoc.path` already points at the archived location, and its 7 glossary links already match the terms CSV exactly (verified below). A write happens only if R3's audit finds real drift. Compare `iterdump()` semantics, never file bytes.
- `KANBAN.md`, `KANBAN.html` — generated; regenerated only if R3 writes the DB. Never hand-edited.
- `docs/GLOSSARY.md` — DB-rendered; **no residual item is expected to change it.** A diff here is drift to investigate, not build output.

If R3 does write the DB, it applies its writes **on top** of any concurrent state without reverting, verifies by two-consecutive-regenerate byte-stability plus spot-checks rather than by "`git diff` is clean", and hands the mixed diff to the maintainer to reconcile at commit. It also re-runs `import_spec_terms --check` **after** any concurrent DB write rather than trusting the pre-flight baseline reading.

## Build-wide context flags

- **`0.0.3` shipped and the version quintet is at `0.0.14`.** No residual item touches `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, the GLOSSARY package-version line, or `uv.lock`.
- **No source or test file changes in this cycle.** Package source, `tests/`, and `examples/` code are read-only throughout. R3 may edit a docstring only if its audit finds a factually-false one, and that routes through Worker 2.
- **`CHANGELOG.md` is closed.** `AGENTS.md` rule 21 governs: no residual item edits it.
- **Sibling specs are read-only, with NO declared exception.** Spec-005 declares no cross-spec documentation obligation of its own. The successor specs that own this spec's three superseded topics — **spec-011, spec-015, spec-018, spec-019, spec-027, spec-028** — are all **correct as written**, and the direction of correction runs *toward* spec-005, never away from it. A pass that finds a sibling made stale by an R2 edit records it as a deferred item; it does not edit it. The one live inbound dependency is `docs/SPECS/spec-006-public_surface-0_0_3.md`, which cites spec-005 by section title (`"Accepted vs deferred Meta keys"`) — **R2 must not retitle that heading without recording the inbound break**; see `### Every reference TO spec-005`.
- **The spec is already archived.** `BUILD.md` `### Spec stays at its working location` requires a move be plan-declared as a Worker-1-owned final-verification step. There is no move: `docs/SPECS/spec-005-django_type_contract-0_0_3.md` and `docs/SPECS/appx/spec-005-…-terms.csv` are already at their archived paths, `SpecDoc.path` already reads the archived path, and both `KANBAN.md` references already point there. **R1's new rationale file is therefore written directly to `docs/SPECS/appx/`** — the archived-companion location `AGENTS.md` rule 26 names — never to `docs/` first and moved after.
- **Only the maintainer commits.** No worker commits, and none creates or switches a branch.

## Worker-0-verified facts, passed into dispatch so no worker re-derives them

`worker-0.md` `## Closing out a kanban card` requires the live DB references be verified before a card/glossary edit is planned, because plan and spec text can carry stale ones. Read-only queries, run 2026-08-08:

- `Card.objects.get(number=5)` → `card_id` `DONE-005-0.0.3`, `status.key` `done`, `target_version.number` `0.0.3`, title `DjangoType contract and boundary`. The card is **already Done**; no status flip is in scope, and the 2026-07-30 card renumber left 005 untouched (it rotated 045-068 only).
- `SpecDoc` for card 5 → name `spec-005-django_type_contract-0_0_3`, **`path` already `docs/SPECS/spec-005-django_type_contract-0_0_3.md`**. No repoint needed. (`SpecDoc.path` is the writable column; `SpecDoc.url` is a read-only `@property` deriving from it — assigning `url=` raises.)
- `card.glossary_links.count()` → **7**, exactly matching the 7 rows in `docs/SPECS/appx/spec-005-…-terms.csv`: `configurationerror`, `djangotype`, `metaexclude`, `metafields`, `metainterfaces`, `metamodel`, `metaprimary`. One row per anchor, so the CSV is importable (`worker-0.md` `### DONE-card invariants` — a green `check_spec_glossary` alone does not prove this).
- Card 5 carries **5 `CardItem`s** across three sections (`Scope` ×3, `Verified in upstream` ×1, `Note` ×1) and **no `Definition of done` section**. Every `Scope` and `Note` row is `is_complete = True`; the single unticked row is `Verified in upstream`, matching cards 2, 3, and 4 — board convention, not drift. **No card-body edit is in scope** unless R3 finds a factually-false sentence.
- **The card body is BEHIND the spec, not ahead of it** — the inverse of card 4. Its three `Scope` rows still read "Document the alpha one-model-one-type registry constraint", "Reject unsupported or deferred `Meta` keys…", and "Remove consumer override promises that the implementation cannot honor yet." All three describe the `0.0.3` decision accurately **as history**, and two of the three name constraints later cards lifted. A Done card's `Scope` is a record of what that card did, so this is **not** drift to fix — but it means R2 gets no help from the board here, unlike spec-004's R2.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` — the spec-004 cycle recorded `OK: 49 done cards have glossary links.` at its pre-flight; R3 re-runs it rather than trusting that reading, since a concurrent DB write has landed since.
- All seven anchors resolve in `docs/GLOSSARY.md`, and the two that matter most to the drift table already carry the **post-promotion** status: `Meta.interfaces` → `shipped (0.0.5)`, `Meta.primary` → `shipped (0.0.6)`. **The glossary is already correct**; R3 verifies rather than edits.
- **Staged-anchor sweep:** `grep -rEn 'TODO\(spec-005|TODO-(ALPHA|BETA|STABLE)-005' .` → **zero hits anywhere**, spec included. `BUILD.md` `## Cross-slice integration pass` step 6 is therefore already discharged at baseline; R3 re-runs it as its backstop.

### The 7-anchor constraint

`docs/SPECS/appx/spec-005-…-terms.csv` carries 7 anchors, and `check_spec_glossary.py` passes today because each has at least one link in the spec body. Both R1 (which moves text out of the spec) and R2 (which rewrites text) can silently drop the last remaining link for an anchor. The failure is not cosmetic: `import_spec_terms` is what a DONE card's glossary-link set is rebuilt from, so a dropped anchor breaks the card-wrap chain for card 5.

This spec's anchor profile is **less fragile than spec-004's** — no anchor sits inside a fenced block, and two anchors have multiple carriers — but three sit inside sentences the drift table marks as falsified:

| Anchor | Carrier(s) | Risk |
|---|---|---|
| `metaprimary` | `## Current state` final paragraph + `### One-model-one-type` **Future direction** | **Highest.** Both carriers are D2/D3 material — the whole "future direction" framing for a mechanism that shipped at `0.0.6` |
| `metainterfaces` | `## Problem statement` item 4 | Sole carrier, inside the D13 sentence ("`Meta.interfaces` was in `ALLOWED_META_KEYS` … but never applied") |
| `metafields`, `metaexclude` | `## Problem statement` item 3 **and** `### Invalid …` heading | Two carriers each, and the `### Invalid` topic is the one section D16 confirms is fully accurate — low risk |
| `configurationerror` | `## Problem statement` item 1 + `### Invalid …` body | Two carriers; item 1 is D2 material, the body survives |
| `djangotype` | `## Problem statement` item 1 | Sole carrier, inside D2's falsified sentence |
| `metamodel` | `### Invalid …` body | Sole carrier; the section survives intact |

**CORRECTION, appended by Worker 0 at the close of R1 (2026-08-08).** Worker 1 measured the carriers rather than reading them and found **the table above wrong in three rows**: Worker 0 counted plain code spans (`` `Meta.fields` ``) as links. A code span carries no anchor. The measured position, which supersedes the three rows and is **stricter** in the one place that matters:

- **`metaprimary` has ONE carrier, not two** — `## Current state`'s final paragraph, which R1 left in place because it is a falsified *contract* statement and therefore R2's. So the highest-risk anchor in the file is a single point of failure sitting **entirely inside R2's write set**. R2 re-sites that link **in the same edit** that rewrites the paragraph, never after.
- **`configurationerror` has one carrier, not two** — `## Problem statement` item 1, which is D2 material.
- **`metafields` / `metaexclude` have one carrier each, not two** — the `### Invalid …` heading is a heading, not a link.

Every anchor stood at exactly 1 use + 1 definition after R1, and `check_spec_glossary` returned `OK: 7 terms`. With one carrier apiece, **six of the seven anchors are now single points of failure**, four of them in falsified prose. The re-run-and-quote obligation below is not a formality on this spec.

**Every pass that writes the spec re-runs `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` and quotes the result in its artifact.** A rewrite that drops an anchor keeps the anchor's link by re-siting it in the surviving contract prose — never by re-adding narration the item just removed, and never by editing the CSV.

### What R1 inherits

Spec-005 is the smallest spec of the four residual cycles (13,346 bytes against spec-004's 33,928) and carries **no pseudo-code at all**. Its deliberative layer is concentrated and unusually easy to name, which makes the mover's risk the opposite of spec-004's: not "how do I separate design intent from a falsified fence", but "how much of a four-section document survives when three sections are about constraints that no longer exist".

- **Two `**Future direction.**` blocks** — one under `### One-model-one-type`, one under `### Consumer override semantics` — are the bulk of the deliberation. Each predicts a mechanism, lists open sub-questions, and (in the override case) enumerates three candidate approaches. **Both mechanisms have since shipped**, and the rationale file is exactly where a superseded prediction belongs: `worker-1.md` rule 2 says delete rather than move prose the current decisions have falsified, but *the fact that a prediction was made and how it fared* is precisely what a rationale records. Spec-005's `Meta.primary` prediction was **substantially vindicated** (right name, right rule, right rejection of first-registered-wins) and **wrong in one detail** (detection point); its consumer-override prediction was **wrong three ways out of three** (none of the enumerated approaches shipped). That asymmetry is the single most valuable thing this rationale can record, and it exists nowhere else in the repository.
- **The `### One-model-one-type` "real friction" paragraph** argues from DRF, `graphene-django`, and `strawberry-graphql-django` precedent. Per the maintainer decision recorded on the spec-004 cycle (`### Maintainer decision — the surviving competitive positioning`), the governing reading is: per-topic competitive argument moves to the rationale; a **problem statement's** statement of the competitor gap stays when the comparison is the document's subject. Spec-005's `## Problem statement` item 1 names all three libraries and *is* the reason the constraint was flagged — that decision's scope covers it, and R1 should read it before cutting.
- **The `## Open questions` section reads "None blocking 0.0.3"** — a sentence whose entire meaning is a release-gating judgement made in April 2026. Pure deliberation.
- **The rationale must be keyed to spec sections.** `BUILD.md` `## Spec rationale extraction` requires each entry name the spec decision it serves by heading and anchor, and carry: the alternatives rejected and why each lost; every change the decision has undergone with the round or later spec that caused it; and any claim the decision once made and may no longer make. The drift table below is R2's input, but **its "why" column is R1/R2's output** — that is precisely the maintainer's instruction that *explanations of the changes go in the rationale, not the spec*.
- **Do not duplicate the siblings.** `docs/SPECS/appx/spec-001-…-rationale.md` already narrates the type-system foundation. R1 reads it to avoid restating, not to borrow from. It must also not restate spec-018's or spec-019's own reasoning — those specs are the owners; the rationale records only what *spec-005 predicted* and how it compares.

### Verified spec-versus-HEAD drift — R2's input, verified by Worker 0 against source

Read at HEAD (`346d6731`) on 2026-08-08 with the symbol-qualified paths given. Each row is a claim the spec makes that HEAD complicates or falsifies. **A prescribed correction is not included: how the spec should read is Worker 1's call, and the alternatives it rejects belong in the rationale file.** Worker 1 re-verifies each row rather than trusting this table.

| # | Spec claim | HEAD reality | Owner of the move |
|---|---|---|---|
| D1 | Whole-document framing: `## Current state` heads a list "0.0.3 shipped (in flight)"; `## Open questions` reads "None blocking 0.0.3" | All of it shipped at `0.0.3`, eleven minor versions ago; card `DONE-005-0.0.3`. The document is written as though a release is pending | the card itself |
| D2 | `## Problem statement` item 1 + `### One-model-one-type (alpha constraint)`: "`TypeRegistry.register` raises `ConfigurationError` on collision, forcing one `DjangoType` per Django model" | **Falsified.** `registry.py::TypeRegistry.register` appends to a per-model list; multiple types per model are supported since `0.0.6`. `register` now raises only for a **duplicate primary** (`#"is already the primary type"`) or a **flipped primary flag on re-register** (`#"primary flag cannot be flipped on re-register"`). **Sole carrier of `djangotype`, joint carrier of `configurationerror`** | spec-018 |
| D3 | `### One-model-one-type` **Future direction**: predicts `Meta.primary: bool = False` with four rules, incl. "Two or more types and none claims primary -> **registration** raises (ambiguous primary by omission)" | **Shipped, and the prediction held on every point but one — the detection point.** Duplicate-primary raises at `registry.register`; ambiguity-by-omission is detected at `finalize_django_types()` by `types/finalizer.py::_audit_primary_ambiguity`, not at registration. The reason is the spec's own: registration cannot know whether a later sibling will claim primary, so a registration-time raise would make the outcome **import-order-dependent** — the exact property the spec demanded be kept out of the API contract. `docs/SPECS/spec-018-meta_primary-0_0_6.md` Decision 5 is the authoritative catalog. **Joint carrier of `metaprimary`** | spec-018 Decision 5 |
| D4 | `### One-model-one-type` **Future direction**: three sub-questions the future spec "will need to address" — migration path, per-type relation routing, optimizer impact | **All three answered.** Migration: implicit relaxation, no new setting — a single type still registers with no `Meta.primary` (spec-018 Decision 5, row 1). Relation routing: `_build_annotations` **always defers**, the eager-bind shortcut was removed, and binding happens at finalization against the primary (Decision 6). Optimizer: Decision 9, origin-type propagation. None is open | spec-018 |
| D5 | `## Problem statement` item 2 + `### Consumer override semantics`: "`@strawberry.type` rewrites `cls.__annotations__` after the merge so the override doesn't actually hold" | **The diagnosis is falsified, and it was falsified before the feature shipped.** `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` `## Problem statement` records that the skip reason "describes a pre-foundation-slice state": after `DONE-010-0.0.4` the merge at `types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"` already put the consumer last. What was actually missing was the field name's membership in `consumer_authored_fields`, so the synthesized annotation was still computed and the consumer won only by dict-merge order — brittle, but not the stated mechanism | spec-010 (falsified the diagnosis), spec-019 (fixed the real gap) |
| D6 | `### Consumer override semantics` **Decision for 0.0.3**, second half: "The `docs/README.md` 'Current surface' section will explicitly call out consumer overrides as currently *not guaranteed*" | **Doubly stale.** `docs/README.md` has no `## Current surface` section at all (it carries `## Today and coming next` plus a shipped-capability list), and what that list says is the opposite and correct: "annotation-only and `strawberry.field` consumer overrides for scalar fields, symmetric with the shipped relation-override contract". The *first* half of the same Decision — remove the override claim from the `__init_subclass__` docstring — **was delivered and still holds**: the docstring is now the single line "Collect model/type metadata without finalizing the Strawberry type." | doc restructure (`spec-007` consolidation); the promise itself, spec-019 |
| D7 | `### Consumer override semantics` + `## References`: "The skipped `test_consumer_annotation_overrides_synthesized` test in `tests/types/test_base.py` pins the failure mode" / "The skipped test stays as a contract pin and unskips when the real mechanism ships" | **The test does not exist.** `grep -rn` over `tests/`, `examples/`, and `django_strawberry_framework/` returns nothing. spec-019 Decision 5 weighed unskip-and-keep against delete and chose **delete**, on the grounds that a one-line smoke test sitting alone in `test_base.py` would drift from the canonical host. The four-corner override matrix lives in `tests/types/test_definition_order.py` | spec-019 Decision 5 |
| D8 | `### Consumer override semantics` **Future direction**: three candidate approaches — (1) reach into Strawberry's internals, (2) route through Strawberry's field-customization API, (3) an explicit `Meta.field_overrides = {...}` key | **None of the three shipped.** The mechanism is a fourth: extend the existing `consumer_annotated_relation_fields` collection with a parallel `consumer_annotated_scalar_fields` set and union it into `consumer_authored_fields`, so `_build_annotations` short-circuits the field entirely (spec-019 Decisions 1-4). No Strawberry internals were touched, and `KANBAN.md` card `DONE-019-0.0.6` states outright "No new public API. No `Meta.field_overrides = {...}`-style key." | spec-019 |
| D9 | `### Accepted vs deferred Meta keys`: "`ALLOWED_META_KEYS` … Today: `model`, `fields`, `exclude`, `name`, `description`" | **Five, now seventeen** at `types/base.py #"ALLOWED_META_KEYS: frozenset[str] = frozenset("`. Added: `connection`, `cursor_field`, `filesystem_path_fields`, `filterset_class`, `globalid_strategy`, `interfaces`, `nullable_overrides`, `optimizer_hints`, `orderset_class`, `primary`, `relation_shapes`, `required_overrides` | spec-011/015/018/027/028/029/030/031/032/048 + the keyset-cursor card |
| D10 | same section: "`DEFERRED_META_KEYS` … Today: `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`" | **Six, now three**: `aggregate_class`, `fields_class`, `search_fields`. Three were promoted — `interfaces` (`0.0.5`), `filterset_class` and `orderset_class` (`0.0.8`). The three that remain are exactly the three the Beta line still owes: `fields_class` → `0.1.1`, `search_fields` → `0.1.2`, `aggregate_class` → `0.1.3`. **Sole carrier of `metainterfaces` sits in the D13 sentence, not here** | spec-015, spec-027, spec-028 |
| D11 | same section: a deferred key is "rejected with a `ConfigurationError` whose message names them **and points at the spec that will own them**" | **The shipped message names no spec — and the divergence is a later deliberate correction, not a defect.** At `0.0.2` (`70c7bff2`, 2026-04-30) it read "The **spec** that owns them has not shipped"; commit `83c25963` (2026-05-05, "Finish consolidation of specs and doc files") changed it to "The **feature** that owns them has not shipped", which is what `types/base.py::_validate_meta` raises today. Neither form ever named a *specific* spec, so the spec's promise was over-stated from the start and has since been deliberately moved further away from spec-vocabulary. **This is R2's row, not a builder's** | `83c25963` (doc/spec consolidation) |
| D12 | same section: the promotion rule — a key moves to `ALLOWED_META_KEYS` only when the validator accepts it **and** the pipeline applies it end-to-end | **Intact and honoured** (see the audit below: all 17 allowed keys are applied). What HEAD adds is a **third category the spec does not have**: `types/base.py #"are net-new ALLOWED keys, NOT DEFERRED_META_KEYS promotions"` records that six of the twelve added keys were never deferred at all, because each one's feature shipped in the same card that added the key — "never reserved-but-nonfunctional". `tests/types/test_base.py::test_interfaces_is_shipped_not_deferred` and `::test_relation_shapes_is_shipped_not_deferred` pin the distinction | spec-032 Decision 7 (which named the pattern), and the source comment |
| D13 | `## Problem statement` item 4 + `## Current state`: "`Meta.interfaces` was in `ALLOWED_META_KEYS` (validation passed) but never applied" / "0.0.3 shipped: `Meta.interfaces` moved to `DEFERRED_META_KEYS`" | True as history, falsified as present tense. `interfaces` is in `ALLOWED_META_KEYS` **again** and is now fully applied — validated by `types/base.py::_validate_interfaces` (spec-011 Decision 4) and injected into `cls.__bases__` at finalizer Phase 2.5 by `apply_interfaces`. **Sole carrier of `metainterfaces`** | spec-011 (validation), spec-015 (the feature) |
| D14 | `## Current state`: "`_is_default_get_queryset` sentinel flip in `__init_subclass__` and the implemented `has_custom_get_queryset` body" | **Still true, and extended.** The sentinel is now stamped **before** the `meta is None` early return so an abstract base overriding `get_queryset` without declaring `Meta` still flips it; detection moved to `types/base.py::_detect_custom_get_queryset` (an MRO walk terminating at `DjangoType`); and the authoritative value lives on `types/definition.py::DjangoTypeDefinition.has_custom_get_queryset`, with the classvar as the pre-definition fallback. `types/finalizer.py #"if previous.has_custom_get_queryset or new.has_custom_get_queryset"` is a second consumer the spec does not mention. Under-description, not drift to "fix" | the card itself + spec-018 (the finalizer consumer) |
| D15 | `### One-model-one-type`: "The package's own test suite already works around it manually: `tests/types/test_resolvers.py`, `tests/types/test_converters.py`, and the new `test_has_custom_get_queryset_inherits_through_intermediate_base` all call `registry.clear()` … between defining sibling types over the same model" | All three sites still call `registry.clear()` (15 / 2 / 6 occurrences in `test_converters.py` / `test_resolvers.py` / `test_base.py`) and `tests/types/test_base.py::test_has_custom_get_queryset_inherits_through_intermediate_base` still exists — but **the stated reason is falsified**: since `0.0.6` sibling types over one model need no clear. The surviving calls are test isolation against a module-scoped registry, not a collision workaround | spec-018 |
| D16 | `### Invalid `Meta.fields` / `Meta.exclude` (shipped in 0.0.3)`: the validation, the error shape (model + unknowns + available), and three named tests | **The only topic entirely true at HEAD.** `types/base.py::_select_fields` raises on unknown names in both the `fields` and `exclude` arms, and all three named tests exist at `tests/types/test_base.py::test_meta_fields_unknown_name_raises`, `::test_meta_fields_unknown_name_includes_model_and_available`, `::test_meta_exclude_unknown_name_raises`. What changed is **scope**: the message is now built by the shared `types/base.py::_format_unknown_fields_error` and the same shape is reused by every later typo-guard — `optimizer_hints`, `nullable_overrides` / `required_overrides`, `filesystem_path_fields`, `relation_shapes`. The spec's "part of the public contract" claim is carried by more validators than the two it names. **Sole carrier of `metamodel`; joint carrier of `metafields` / `metaexclude` / `configurationerror`** | later specs widened it; the rule itself is unchanged |
| D17 | `## Non-goals`: "the **future** `Meta.primary` mechanism itself, or the **future** consumer-overrides mechanism itself" | Both shipped at `0.0.6`. The non-goal is still correct in substance — this spec does not cover either mechanism — but "future" is false, and a reader cannot tell from this sentence that the follow-ups exist | the card itself |
| D18 | `## Coordination …`: "When a future spec … adds a new Meta key or changes an existing one, that spec **must update this contract spec** accordingly" | **Never once happened.** Twelve keys were added and three promoted across at least eleven specs, and none of them touched spec-005 — which is the direct cause of D9, D10, and D13, and therefore of this cycle. Whether the spec should keep issuing an instruction that has never been followed, or restate the contract so the authoritative key list lives at its single source (`ALLOWED_META_KEYS`) with the spec pointing there, is Worker 1's call | the card itself; this is the cycle's own root cause |
| D19 | `## References` bullets: the "original alpha review"; "`tests/types/test_base.py` — pins … the override-merge skipped placeholder" | The skipped placeholder is deleted (D7), so that clause names a test that does not exist. The "original alpha review" names a document not present anywhere in the repository — the spec itself claims to be "the durable record of those findings", which makes the reference self-describing rather than resolvable. The `spec-001` / `spec-002` / `spec-006` bullets all carry correct `docs/SPECS/` paths | D7's owner; the alpha review, the card itself |
| D20 | `## Goal`: "Every knob accepted by `Meta` is either applied today **or rejected with a clear error pointing at the spec that will own it**" | First half **verified true at HEAD** (see the audit — all 17 allowed keys applied end-to-end, the original `Meta.interfaces` mistake not repeated). Second half is D11: the rejection is clear and names the keys, but points at no spec, deliberately since `83c25963` | first half: holds; second half: D11 |

**Corrections and additions, appended by Worker 0 at the close of R2 (2026-08-08).** Worker 1 swept beyond the table, as row-set framing licenses, and returned three corrections. All three were re-verified against source by Worker 0 before being written here.

- **D12's test citation is wrong.** `tests/types/test_relation_shapes_is_shipped_not_deferred` does not exist; the real name is `tests/types/test_base.py::test_meta_relation_shapes_in_allowed_meta_keys`. `::test_interfaces_is_shipped_not_deferred` is correct as cited. D12's substance — that HEAD carries a net-new-vs-promoted distinction the spec lacks — is unaffected.
- **D21 (new).** `### One-model-one-type`'s **Decision** carried a second `docs/README.md` "Current surface" documentation obligation, the same shape as D6 — which caught only the consumer-override half. Neither obligation was ever dischargeable: that section does not exist in `docs/README.md`.
- **D22 (new).** The same section cited `convert_relation` as the consumer of the one-type-per-model reverse lookup. **The symbol no longer exists anywhere in the package** — `grep -rn convert_relation django_strawberry_framework/ tests/` returns a single hit, and it is a comment inside `tests/types/test_base.py`. A dangling symbol citation in the spec, invisible to `check_spec_glossary` (which validates glossary anchors, not source symbols).

Two things this table deliberately does **not** say. First, that every row must change the spec: some rows are the spec being *superseded* rather than *wrong*, and spec-018 / spec-019 / spec-015 / spec-027 / spec-028 already own the surfaces that superseded it — Worker 1 decides per row whether the contract is restated, pointed elsewhere, or dropped to the rationale. Second, that the list is exhaustive; it is Worker 0's verified floor, and R2 owns the full sweep.

**The scope trap specific to this spec.** Spec-005 is a *contract* spec, so the pull is toward turning it into a current-state inventory of `ALLOWED_META_KEYS` — a list that has changed eleven times and will change again at `0.1.1`, `0.1.2`, and `0.1.3`. That would recreate D18 as a maintenance obligation rather than retire it. `docs/GLOSSARY.md` already carries a per-key status table, and `types/base.py`'s `ALLOWED_META_KEYS` is the executable single source; the spec's durable contribution is the **rule** (what licenses a key to be accepted, what a rejection owes the consumer, why silent acceptance is a bug), not the roster.

### The read-only correctness audit — findings

The maintainer's instruction "MAKE SURE NOTHING WAS SKIPPED IN THE CODE" has an unusually literal reading for this spec, because spec-005's central rule *is* an auditable property of the source: **a key in `ALLOWED_META_KEYS` must be applied end-to-end, not merely validated.** That audit was run key by key. **No defect found.**

- **All seventeen `ALLOWED_META_KEYS` entries are applied.** Thirteen thread through to `types/definition.py::DjangoTypeDefinition` (`connection`, `cursor_field`, `description`, `fields`, `filterset_class`, `globalid_strategy`, `interfaces`, `model`, `name`, `optimizer_hints`, `orderset_class`, `primary`, `relation_shapes`). The remaining four are applied without a definition field, by design: `exclude` is consumed by `types/base.py::_select_fields`; `nullable_overrides`, `required_overrides`, and `filesystem_path_fields` are consumed by `_build_annotations` (passed at `types/base.py #"filesystem_path_fields=validated.filesystem_path_fields"`) after their own target validators run. **The original `Meta.interfaces` mistake — the defect this spec exists to prevent — is not repeated anywhere.**
- **All three `DEFERRED_META_KEYS` entries are genuinely unshipped**, each carded on the Beta line, and each rejected by `_validate_meta` before any other shape gate touches it. `tests/types/test_base.py::test_meta_rejects_each_deferred_key` is parametrized over the set, so the rejection cannot silently lapse when the set changes.
- **`_select_fields` raises in both arms**, and the shared `_format_unknown_fields_error` keeps the message shape identical across every typo-guard that has since adopted it. The spec's "public contract" claim about the error shape is stronger at HEAD than when it was written.
- **The `get_queryset` sentinel is correct and hardened** past the spec's description (D14), with the stamping-order invariant pinned by a named test rather than left to convention.

Two observations recorded so R2 does not mistake either for drift to "fix":

1. **The deferred-key message's "feature" wording is deliberate, not decayed** (D11). Commit `83c25963` moved the package's consumer-facing vocabulary away from naming internal spec documents — a consumer reading a `ConfigurationError` has no access to `docs/SPECS/`. The spec's promise is what is stale.
2. **`registry.get()` returns `None` for the ambiguous multi-type case** rather than raising there, and its docstring says callers "cannot distinguish this from 'no type registered' without checking `types_for(model)`". That is intentional: the raise belongs to the finalizer audit, which sees the whole registry at once (D3). Correct as designed; a rationale entry, not a spec sentence.

One item for the deferred-work catalog rather than for R2: `docs/SPECS/spec-006-public_surface-0_0_3.md` line 108 cites spec-005's "Accepted vs deferred Meta keys" section **by title**, so an R2 retitle silently breaks an inbound reference in a sibling this cycle may not edit. *(Discharged at R2: the title string spec-006 quotes was preserved — only the parenthetical `(shipped in 0.0.3)`, outside the quoted substring, was dropped. No inbound break.)*

### THE ONE SOURCE EDIT THIS CYCLE AUTHORIZES — verified by Worker 0, routed to R3

R2 escalated a **factually-false docstring in shipped source** rather than editing it, correctly: `BUILD.md` `### Worker 0 verifies every finding against source before dispatching` requires Worker 0 to confirm the condition holds at HEAD before any builder is dispatched at it. Verified 2026-08-08, and it holds:

`django_strawberry_framework/exceptions.py::ConfigurationError` #"Two ``DjangoType`` subclasses registering against the same model." lists that as an **example of a ConfigurationError**. It has been false since `0.0.6`: registering two `DjangoType` subclasses against one model is the *supported* multi-type pattern, and `registry.py::TypeRegistry.register` appends rather than raising. What actually raises is narrower and lives at two different points — a **duplicate primary** or a **flipped primary flag on re-register** at `register`, and **multiple types with no declared primary** at `types/finalizer.py::_audit_primary_ambiguity`, which is finalization-time, not registration-time. So the line does not merely overstate; it tells a consumer that the sanctioned pattern is an error.

The same docstring's deferred-key example reads "before the **spec** that owns it has shipped", the vocabulary commit `83c25963` deliberately moved the runtime message away from (D11). Same file, same edit, and aligning it removes the last in-source survivor of the wording the spec's own D11 row is being reconciled against.

**This is a documentation defect in source, not a correctness defect** — no behavior is wrong, and no test asserts the docstring. It is nonetheless exactly the case the plan's `## Build-wide context flags` reserved ("R3 may edit a docstring only if its audit finds a factually-false one, and that routes through Worker 2"), so:

- **R3 runs the full unmodified worker chain**, not the procedural-closure shape — Worker 1 plans, **Worker 2 makes the edit**, Worker 3 reviews, Worker 1 final-verifies.
- **Scope is one file and one docstring.** Worker 2 does not widen it into a sweep of every docstring in the package; anything else it notices is recorded, not fixed.
- `AGENTS.md` rule 16 applies (`ruff format` / `ruff check --fix` after the edit). No test is owed — the change is prose inside a docstring, and `fail_under = 100` is unaffected.

**WIDENED to a second docstring at the close of R2's review (2026-08-08).** Worker 3 found a further source-doc defect in passing, in a **different file** from the one scoped above, and correctly recorded rather than edited it. Worker 0 verified it before widening:

`django_strawberry_framework/types/base.py::_format_unknown_fields_error` #"Used by every validator that points at a typo in" names three `Meta` keys — `fields`, `exclude`, `optimizer_hints` — as its complete caller set. It has **five direct call sites carrying six distinct `attr` labels** (corrected by Worker 0 at the close of R2's re-review, finding L11: the figure first written here was "eight distinct `attr` values", which is the count of `attr=` **occurrences** in the file, not of distinct labels — the exact defect class this item spent two review rounds on, committed in the plan that named it. Measured: `exclude`, `fields`, `filesystem_path_fields`, `nullable_overrides/required_overrides`, `optimizer_hints`, `relation_shapes`). Three families are unnamed by the docstring: `nullable_overrides/required_overrides` (`types/base.py #"attr=\"nullable_overrides/required_overrides\""`), `filesystem_path_fields` (#"attr=\"filesystem_path_fields\""), and `relation_shapes` (#"attr=\"relation_shapes\""), the last reaching the helper through the generic `attr=attr` forwarding in `_selected_meta_targets`. The docstring under-states its own reach, and it does so on the **one error shape spec-005 pins as public contract** — which is precisely the sentence R2 reconciled to say the shape is now carried by more validators than the two the spec named.

**Both docstrings, and nothing else.** The authorization is now two files (`django_strawberry_framework/exceptions.py`, `django_strawberry_framework/types/base.py`), two docstrings, and no third. Worker 2 does not sweep for further examples; anything else it notices is recorded in its build report as a finding for the maintainer. The deliberate narrowness is the point — a documentation cycle that starts correcting source prose by inference is how a docs cycle silently becomes a code cycle.

### Every reference TO spec-005 (verified by grep, 2026-08-08)

The archive already landed, so this table is R3's **verification** list, not a rewrite list. R3 re-runs the sweep rather than trusting it.

| Location | Current text | Status |
|---|---|---|
| `KANBAN.md:142`, `:4782` (+ hits in `KANBAN.html`) | `docs/SPECS/spec-005-django_type_contract-0_0_3.md` | **Generated** — already correct; never hand-edit |
| `docs/SPECS/spec-006-public_surface-0_0_3.md:108` | "(or accepted-and-rejected per `spec-005-…` "Accepted vs deferred Meta keys")" | Read-only sibling; **correct, and it is a title-level dependency** — see the audit's deferred item |
| `docs/SPECS/spec-006-public_surface-0_0_3.md:135`, `:146` | "defines the contract boundary for `DjangoType` itself"; companion-spec reference | Read-only sibling; correct as written |
| `docs/builder/build-001-…:165`, `build-002-…:116`, `:197`, `build-004-…:249` | prior cycles' verification tables citing spec-005 line numbers and the `__init_subclass__` sentinel | Historical artifacts; `build-002`'s `:27` row already confirms the sentinel claim is accurate, which is D14's independent corroboration |

No hit in `CHANGELOG.md`, `README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `START.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`, or any package source or test file.

**The direction this table cannot show** is the one inside the new file: R1's rationale lands at `docs/SPECS/appx/`, two levels below `docs/`, so its link definitions need `../../GLOSSARY.md` for a `docs/` target and `../spec-NNN-….md` for a `docs/SPECS/` sibling. The archived siblings (`docs/SPECS/appx/spec-001-…-rationale.md`) show the shape.

## Artifact list

- `docs/builder/bld-005-r1-rationale_move.md`
- `docs/builder/bld-005-r2-spec_reconciliation.md`
- `docs/builder/bld-005-r3-doc_completion_archive.md`
- `docs/builder/bld-005-final.md`

No `bld-integration.md`-equivalent: a cross-slice integration pass exists to find duplication across slices that landed source, and this cycle lands none. Its live obligations are folded in — the staged-anchor sweep (`BUILD.md` `## Cross-slice integration pass` step 6) runs in R3, and the cross-artifact read runs in the final gate.

## Checklist

- [x] R1: Spec rationale extraction into `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` (Worker 1 performs the move; Worker 3 audits it; Worker 1 final-verifies) -> `docs/builder/bld-005-r1-rationale_move.md`
- [ ] R2: Reconcile the spec with HEAD — every claim the package falsifies is restated as the contract that actually holds, or handed to the spec that now owns it; the explanation of each change lands in the rationale, never in the spec -> `docs/builder/bld-005-r2-spec_reconciliation.md`
- [ ] R3: Finish the documentation and audit the archive — durable-doc audit of the shipped contract, the three-direction cross-reference sweep, `SpecDoc.path` / terms-CSV verification, and the `TODO(spec-005` / `TODO-<MILESTONE>-005` staged-anchor sweep -> `docs/builder/bld-005-r3-doc_completion_archive.md`
- [ ] Final test-run gate -> `docs/builder/bld-005-final.md`

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
