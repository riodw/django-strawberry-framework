# Package build plan: public_surface / 0.0.3 (006)

Spec source: `docs/SPECS/spec-006-public_surface-0_0_3.md` (**already archived** — the spec, its `-terms.csv`, the `SpecDoc.path` row, and both `KANBAN.md` references already sit at their post-archive locations; item R3 verifies rather than performs the move)
Target release: `0.0.3` (**shipped long ago** — card `DONE-006-0.0.3`, `target_version.number` `0.0.3`; the package is at `0.0.14` in `pyproject.toml`)
Date created: 2026-08-14
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging. A fact told twice across the spec and its rationale sibling goes stale in one of them — the rationale carries the deliberation, the spec carries the contract, and neither restates the other. This cycle additionally operates under `## The single-ownership law` below, which extends the same rule ACROSS specs.
Ownership partition: none; sequential residual items. (Declared explicitly rather than omitted, per `worker-0.md` `### Ownership partition`, so an interrupted item's output stays attributable against a tree a concurrent session is also writing.)
Hot-path declaration: none. No residual item changes package source, so no item runs per request, per resolver, per row, per connection, or per outbound message.
Floor-verification scope: none. No residual item touches a Django / Strawberry / channels integration seam — the cycle edits two archived specs, one archived rationale, one new rationale sibling, and the kanban/glossary DB.
Pre-flight: passed on 2026-08-14 with **three** recorded deviations (below); baseline: three dirty entries, all a concurrent card-wrap's — see `## Baseline-dirty out-of-scope files`; cleanup: **nothing deleted** (Deviations 1 and 3), every path this plan creates verified absent.

## This is a residual-completion cycle, not a fresh build

Spec-006 is a **discipline spec**: it has no `## Slice checklist`, no `## Doc updates`, and no implementation plan. Its deliverable was a set of *rules* — what licenses a name into `django_strawberry_framework/__init__.py`, how the docs describe what is and is not usable, and the status vocabulary both sit on — and those rules shipped at `0.0.3`, eleven minor versions ago. What remains is the deliverable set the shipped cycle never produced, plus the reconciliation that fifty-odd later specs made necessary.

The immediate precedent is the **spec-005 residual cycle** (`docs/builder/build-005-django_type_contract-0_0_3.md`), itself modelled on spec-004, spec-003 (`20a9752f`), spec-002 (`d613887c` / `a76da376`), and spec-001 (`cfd1f873`). This plan follows the same three-item shape and the same collision-avoidance discipline: **every path this cycle creates is `bld-006-` / `build-006-` prefixed**, and nothing belonging to another cycle is deleted, reverted, or re-seeded.

**What makes this spec different from its four predecessors.** Spec-005 was falsified in its *subject*. Spec-006 is falsified in its *instruments*: the rules themselves still read as sound engineering, but three of the four surfaces they operate on do not exist in the shape the spec names.

- The gate's documentation condition points at a `docs/README.md` section — `## Current surface` — that **never existed and does not exist**. The same non-existent section is the target of the spec's own `### docs/README.md structure` topic and of an obligation in `## Non-goals`.
- The seven-marker status vocabulary the spec declares closed and single-sourced shrank in practice to **three** live markers, and to **two** rows in the DB that renders `docs/GLOSSARY.md`.
- The re-export gate is stated as a **biconditional** ("re-exports a name iff all four are true"), and HEAD has six shipped, tested, documented, stable public families that are deliberately **not** root-exported because the import path *is* the opt-in boundary.

Only two topics are true at HEAD exactly as written: the subpackage-to-top-level promotion path (verified subsystem by subsystem below) and the internal-helpers-never-promoted rule.

### Residual scope (this cycle's actual work)

- **R1 — spec rationale extraction.** `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` does not exist. `docs/builder/BUILD.md` `## Spec rationale extraction` makes the move the first substantive action of a build and pre-flight step 7 gates dispatch on it; the shipped cycle predates the rule. Worker 1 is the only role that may perform it. See `### What R1 inherits`.
- **R2 — reconcile the spec with what landed, and perform the coordinated cross-spec retirement.** The maintainer's framing: *make sure the spec matches what actually exists, make sure the code is correct, and where later updates corrected what landed, the spec reflects that; the explanation of each change goes in the rationale, never in the spec.* Nineteen verified drift rows are tabled below. R2 additionally performs the maintainer-decided retirement of `spec-002`'s `## Visibility status` **across every inbound reference in one change** (`### The coordinated retirement — every inbound site`). Worker 1 is the only role that may edit a spec.
- **R3 — finish the documentation and audit the archive.** The DB-backed glossary completion the maintainer authorized (`### Maintainer decision 2`), the card-052 prose discharge the retirement produces, the durable-doc audit, the three-direction cross-reference sweep, and the `TODO(spec-006` / `TODO-<MILESTONE>-006` staged-anchor sweep.

**"Make sure the code is correct" is a read-only audit obligation, not a licence to change source.** Worker 0's pre-dispatch audit (`### The read-only correctness audit — findings`) found **no defect**: all 37 `__all__` entries resolve, are effective, and are tested, and no internal helper has leaked into the public surface. **No source file is writable in this cycle.** If R2 or R3 finds a genuine correctness defect in shipped source, it is recorded as a finding and escalated to the maintainer.

## The single-ownership law

Maintainer instruction, given during this cycle's pre-dispatch escalation and binding on every item:

> each "thing"/feature should only exist concretely in a single spec, other specs can reference them (this should be rare as each spec should be able to stand on it's own) but the claim on ownership should exist in ONLY ONE spec

and, on the mechanics:

> since we did not fix every inbound reference in the same change last time, do that now

Consequences for this cycle, declared before dispatch so no pass improvises them:

1. **A concrete claim restated in two specs is a defect**, and the duplicate is retired rather than kept in sync. Provenance decides which copy is the duplicate: a copy that exists *because the other spec asked for one* is the duplicate.
2. **Retiring or retitling a section fixes every inbound reference in the same change** — by title AND by `#anchor`, in sibling specs, in archived rationale companions, and in the DB-backed board prose. The read-only-sibling default that four prior residual cycles ran under **yields to this instruction** for the sites named in `### The coordinated retirement — every inbound site`, and only for those.
3. **Sibling specs stay read-only everywhere else.** The licence is scoped to the named retirement, not to spec-006's whole reference graph. A pass that finds another cross-spec duplicate records it for the maintainer and does not widen.

## Maintainer decisions (escalated and decided before dispatch)

`docs/builder/BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch` requires the rejected alternatives be recorded with the reason each lost, so the next reader's first instinct does not re-open a settled question.

### Maintainer decision 1 — retire `spec-002`'s `## Visibility status`, fixing every inbound site in this change

**Decided: retire.** `docs/SPECS/spec-002-optimizer-0_0_2.md:57-58` carries two sentences — "O1 through O6 have shipped. The optimizer is public via `DjangoOptimizerExtension`, exported from `django_strawberry_framework.__init__`." Both facts exist elsewhere: the O1-O6 roster in spec-002's own `## Shipped slices` (six `###` subsections) and `## Implementation checklist` (six boxes), and the re-export decision in spec-006's `#### Decision for 0.0.3`, which is a strict superset — rule application, both import forms, and the resulting `__all__`.

The section exists **because spec-006 asked for a copy**: spec-006:136 reads "amended into `spec-002-optimizer-0_0_2.md` \"Visibility status\" so the optimizer spec carries the local context for its own re-export trajectory." Under `## The single-ownership law` clause 1 that provenance makes spec-002's copy the duplicate, and spec-006 stops requesting it.

Rejected alternatives:

- **Leave it and record the deferral again** (the four prior cycles' posture, and the standing board instruction at `KANBAN.md:319`). Lost: it is the posture that kept a two-sentence duplicate alive across five cycles, and the maintainer named it directly — "we did not fix every inbound reference in the same change last time, do that now."
- **Retire spec-006's `#### Decision for 0.0.3` instead and let spec-002 own the optimizer's export placement.** Lost on subject: spec-006 owns the `__all__` roster and the rule that admits names to it; the `0.0.3` decision is that rule's worked application, and the fenced `__all__` tuple is spec-006's own contract. Moving it would leave spec-006 stating a rule with no instance and put a package-surface roster inside a subsystem spec.
- **Retitle rather than delete** (the `spec-001` `## Current state` → `## Prior art` precedent spec-002's own rationale weighs at `:305`). Lost: a retitle preserves the duplication the retirement exists to remove; the heading is not the defect, the second copy is.

**One nuance R2 must not lose.** Spec-002's residual cycle deliberately *merged* the `__init__` export path into this section — `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:83-85` and `:272-275` record it as "the one precision `## Visibility status` lacked." Deleting the heading without a decision on that sentence would silently discard a fact a prior cycle deliberately consolidated. Worker 1 decides its disposition and records the reasoning in **spec-006's** rationale plus an appended entry in **spec-002's** rationale (which is append-only per `worker-1.md` rule 4). Worker 0's non-binding lean, recorded so the alternative is on the table rather than to constrain the custodian: spec-006 owns the roster, so spec-002 needs no restatement at all; if the custodian judges spec-002 cannot stand alone without naming its own public entry point, one sentence stated as contract (never as status) inside `## Shipped slices` is the smaller residue.

### Maintainer decision 2 — fix the `docs/GLOSSARY.md` `## Public exports` bullets now

**Decided: fix in this cycle**, via the glossary ORM plus a regenerate (R3), not deferred to card 052.

Measured at HEAD: the section carries **34** bullets against **37** `__all__` entries. Absent as bullets: `DjangoSchema`, `DjangoMutationExecutionContext`, `DEFAULT_ERROR_POLICY`, `DEFAULT_RESOURCE_POLICY` (the last two *are* named inline inside the `ErrorPolicy` / `ResourcePolicy` bullets, so they are documented; the first two are not documented in the glossary at all). `SerializerMutation` carries a bullet while deliberately absent from `__all__` — correct, and the bullet says why.

Rejected alternative: **defer to card `TODO-ALPHA-052-0.1.0`**, whose scope already carries the gap (`KANBAN.md:314`). Lost: this spec's own gate makes "documented" a condition of being root-exported, so an undocumented `__all__` entry is a live violation of the contract this cycle is reconciling — the one gap a public-surface cycle cannot hand to a later card.

**CORRECTION, appended by Worker 0 at the close of R2's review (2026-08-14).** The measurement above is right about the roster and **wrong about the section**, and R2 inherited the error from this plan before Worker 3 caught it. Read to the next `##` heading, `docs/GLOSSARY.md` `## Public exports` contains **four** bullet groups, not one: the 34-bullet re-exported roster **plus** per-subpackage lists for `extensions` (`DjangoDebugExtension`), `testing` (8 bullets), and `auth` (the four factories). So the section already documents **three of the six** deliberately-not-root-exported families D6 names — which makes "34 bullets" a description of the roster group alone, never of the section. Two consequences:

- **R2's Medium is real and its cause is this plan.** Any spec sentence that tests condition 3 against `## Public exports` as a root-export-only list, or that contrasts a boundary family with it, is false for `extensions` / `testing` / `auth`. R2's apply-changes pass owns the clause.
- **The three families the section omits — `views`, `routers`, `middleware.debug_toolbar` — are NOT in scope here.** Each has its own glossary entry; only the group listing is absent. Adding those groups is a glossary-completeness call of the same family as the `DjangoSchema`-entry question, so it goes to card 052's list, not to R3.

**Scope boundary, and it is narrow.** R3 adds the missing Public-exports bullets for the four `__all__` names measured above, plus the fifth site R2's review escalated (`__version__`, bulleted but unlinked), and nothing else.

**WIDENED by one `CardItem`, authorized by Worker 0 at R3's planning close (2026-08-14).** R3's plan found that this cycle's own glossary write falsifies a **third** card-052 item — `CardItem` pk **1240** (`KANBAN.md:314`), which asserts that `DjangoSchema` and `DjangoMutationExecutionContext` "are absent from the Public exports list even though both are in `__all__`". Once R3's bullets land that sentence is false. Authorized, because `## The single-ownership law` clause 2 — *fix every inbound reference in the same change* — is a maintainer instruction that does not exempt references this cycle's **own** output falsifies, and leaving it would reproduce, inside one cycle, exactly the standoff Maintainer decision 1 exists to end. Scope: **one sentence** in pk 1240, the clause the bullets falsify; the rest of that item (the `DjangoSchema`-entry question, which stays card 052's) survives verbatim, and `is_complete` is ticked on none of the three items. Whether `DjangoSchema` earns a **full glossary entry** with its own anchor stays card 052's decision — it is an editorial call about entry granularity, not a contract violation. A bullet may therefore point at an existing anchor (the `SerializerMutation` and `RESOURCE_LIMIT_ERROR_CODE` bullets already establish the many-bullets-to-one-anchor shape).

## Pre-flight outcome (7 steps, `docs/builder/worker-0.md` `## Pre-flight procedure`)

1. **Working-tree baseline is explicit.** `git status --short` → three entries, all a concurrent card-wrap's. See `## Baseline-dirty out-of-scope files`. HEAD is `947f7494`.
2. **`scripts/review_inspect.py` runs.** `uv run python scripts/review_inspect.py django_strawberry_framework/__init__.py --output-dir docs/shadow --stdout` emitted its overview (20 imports, 1 symbol, 0 control-flow hotspots, **0** TODO comments, 10 repeated string literals). Working, and run against the module this spec governs.
3. **Build artifacts are reset — DEVIATION 1, see below.** Verified instead that every path this plan creates is absent: no `docs/builder/build-006*`, no `docs/builder/bld-006*`, no `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md`.
4. **`.gitignore` lists the untracked scratch paths.** `docs/shadow/` (line 174), `docs/builder/worker-memory/` (188), `docs/builder/temp-tests/` (192). Present.
5. **Scratch directories are cleared — DEVIATION 3, see below.** `docs/shadow/` and `docs/builder/temp-tests/` are empty. `docs/builder/worker-memory/` holds the spec-005 cycle's four namespaced files (durable record of a closed cycle) plus four empty un-namespaced files; **nothing was deleted**.
6. **Spec-doc consistency check.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` Exit 0. Baseline for the constraint in `### The 7-anchor constraint`.
7. **Spec rationale is extracted.** **Not done — it is item R1 of this cycle.** Ordinarily this gates dispatch. Here it cannot, because R1 *is* the dispatch: the work whose spawns the gate protects was built and released before this plan existed, so there is no builder left to protect. R1 runs first regardless, so every later spawn in this cycle reads the smaller spec exactly as the rule intends.

Two further baselines recorded at pre-flight, both green, both re-checked by any pass that writes:

- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-006-public_surface-0_0_3.md` → exit 0 (link-definition scaffold and the 10 canonical group headers intact).
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' docs/SPECS/spec-006-public_surface-0_0_3.md` → **no match**. `AGENTS.md` rule 27 compliance is a property to preserve, not one to establish.

Spec size before R1: **10,934 bytes / 178 lines**, with **6** fence lines (three fenced blocks: two import examples and the `__all__` tuple). Worker 1 reports the after-count in the R1 artifact.

### Deviation 1 — other cycles' `build-*.md` and `bld-*.md` artifacts are PRESERVED

Pre-flight step 3 deletes old `build-*.md` / `bld-*.md`. They are **not** deleted here:

- Every `build-*.md` and `bld-*.md` under `docs/builder/` is **committed** (the working tree carries no dirty or untracked builder file), so each is the record of a closed cycle. `BUILD.md` `### Cohorting, naming, and closure` ("Pre-flight for a round") already establishes that when a cycle's input is already-built work, the prior artifacts are the record of that work and must survive. Every residual item here operates on already-built, already-released work.
- `docs/builder/bld-003-final.md` and `docs/builder/bld-005-*.md` are load-bearing **inputs** to this cycle: both carry deferred-work entries this plan cites.
- **Collision is avoided by naming, not by deletion.** Every artifact this plan creates is `bld-006-`-prefixed and the plan is `build-006-`-prefixed; none of those paths exists.

### Deviation 2 — the `built` state is skipped where the deliverable is Worker-1-exclusive

`docs/builder/ARTIFACT.md` `## Status field ownership` gives `built` to Worker 2, and `worker-0.md` `## Per-slice dispatch` maps `planned` → Worker 2. Items **R1 and R2** have no Worker 2 role that could set it:

- **R1** — `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move, and states outright that **Worker 2 never reads the rationale file** — "that is the point of the move." Dispatching a builder at it would hand the file to the one worker the mechanism exists to keep away from it.
- **R2** — `BUILD.md` `## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the **only** role that may mutate a spec. R2's entire deliverable is spec edits, across four files.

So for R1 and R2 the chain is **Worker 1 (plan + perform, `planned`) → Worker 3 (audit, `review-accepted` | `revision-needed`) → Worker 1 (final verification, `final-accepted`)**, and Worker 0 reads `planned` on those artifacts as "dispatch Worker 3", not Worker 2.

**Corollary, carried forward from the prior residual cycles:** `worker-0.md` `## Per-slice dispatch` step 4 routes a Worker-3 `revision-needed` to Worker 2 for the apply-changes pass. On R1 and R2 that route does not exist — the same two rules that remove Worker 2 from the perform pass remove it from the fix. **The apply-changes pass for R1 and R2 is Worker 1's, and it sets `planned` again**, returning the artifact to the `planned` → Worker 3 mapping above.

The Worker 3 audit is **not** skippable alongside the Worker 2 build. A rewrite performed by the author is reviewed by an agent with no memory of why a sentence was cut — the only vantage point from which an over-cut looks like an over-cut. **R3 runs the full unmodified chain** (Worker 1 plans, Worker 2 performs the ORM edits and regenerates, Worker 3 reviews, Worker 1 final-verifies), because Maintainer decision 2 gives it real DB work.

### Deviation 3 — worker memory is NAMESPACED, not re-seeded

Pre-flight step 5 re-seeds the four `docs/builder/worker-memory/worker-<N>.md` files empty. The four un-namespaced files are already empty, and the spec-005 cycle's four namespaced files are the durable record of a closed cycle that a future closeout may still read. Nothing is deleted; this cycle uses its own namespace, **`docs/builder/worker-memory/spec-006-worker-<N>.md`**, seeded empty by Worker 0 at plan creation.

The rule's intent — a private notebook per worker, persisting across one build, invisible to every other worker — is preserved exactly. Every dispatch prompt names the namespaced path, carries the standing "do not read the other workers' memory files" instruction, and additionally forbids reading the `spec-005-*` and un-namespaced files.

## Baseline-dirty out-of-scope files

Workers neither edit nor revert these, and never `git checkout` them (`AGENTS.md` rule 34). Attribution is positive, not inferred: this cycle's writable set is listed in `## Build-wide context flags`.

- `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3` (`M`) — a **concurrent card-wrap**, live as this plan is written. All three are generated-or-DB surfaces this cycle's R3 must also write, which makes them the one genuine collision risk in the cycle; `## Concurrent-writable tracked binary / generated files` governs how R3 proceeds.

### First growth, recorded at the close of R1 (2026-08-14) — A CONCURRENT spec-007 CYCLE IS LIVE

Reported by Worker 1 during R1, appended by Worker 0. **Nothing was reverted, and no worker may revert any of it.** `HEAD` has not moved (`947f7494`). Newly baseline-dirty and out of scope:

- `docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md` (`??`) — a **concurrent spec-007 residual cycle's build plan**, created mid-pass in another session.

**This matters to R2 and R3 more than an ordinary growth event.** `spec-007` is the named owner of drift rows **D3, D5, D8, and D17** — every undischargeable `docs/README.md` obligation spec-006 carries. Consequences, binding on both remaining items:

- **No write collision exists and none may be created.** This cycle never writes `docs/README.md`, `docs/SPECS/spec-007-…md`, or that cycle's artifacts; that cycle has no licence over spec-006, spec-002, or their rationales. Every path in `## Build-wide context flags`' writable set stays this cycle's alone.
- **A read collision does exist.** R2's D3/D5/D8/D17 rows assert what `docs/README.md` does and does not contain, and the concurrent cycle may change exactly that while R2 writes. **R2 re-derives every `docs/README.md` claim against the file at the moment it writes the sentence** — never against this plan's reading — and states in its artifact when it measured.
- **Direction of correction still runs toward spec-006.** If R2 finds spec-007 (or its cycle's in-flight edits) made stale by an R2 edit, it records the item for the maintainer and does **not** edit it. `## The single-ownership law` clause 3 holds: the retirement licence covers `spec-002` and its rationale only.
- **This cycle's own R1 output was not swept in.** `git log --oneline -1 -- docs/SPECS/spec-006-public_surface-0_0_3.md` still returns `ff65666d`, which predates this cycle, and both R1 files are present and dirty/untracked as expected. That is the check that discharges the standing hazard — never `git status` alone.

**R1's measured spec size, for the record `## Pre-flight outcome` promised:** 10,934 → **11,019 bytes** (+85), 178 → **177 lines**. The spec grew because its entire deliberative layer was 360 bytes while rule 1's mandatory per-decision pointers cost 445; Worker 1 declined to drop a required pointer to make the delta negative and recorded the arithmetic. Rationale companion: 15,449 bytes / 228 lines.

### Second growth, recorded at the close of R1's apply-changes pass (2026-08-14) — FIVE COMMITTED `docs/review/rev-*.md` FILES ARE DELETED

Reported by Worker 1, **verified by Worker 0** with `git status --short docs/review/`, appended by Worker 0. `HEAD` has not moved (`947f7494`). **Nothing was reverted, and no worker in this cycle may revert any of it.**

- `docs/review/rev-_cross_web_patches.md`, `rev-_django_patches.md`, `rev-_strawberry_patches.md`, `rev-apps.md`, `rev-conf.md` (`D`, unstaged) — five **committed** review artifacts deleted by another session.
- `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` (`M`), `docs/SPECS/appx/spec-007-…-rationale.md` (`??`), `docs/builder/bld-007-r1-rationale_move.md` (`??`) — the concurrent spec-007 cycle, now past its own R1. Same read-collision handling as `### First growth`.

**This one needs the maintainer, and it is not this cycle's to fix.** `AGENTS.md` rule 22 names `docs/review/`'s `rev-*.md` as committed source of truth and prescribes `git checkout HEAD -- docs/review/` as the restore — but rule 34 forbids reverting concurrent work without explicit authorization, and a `git checkout` against a tree three sessions are writing is the exact command both rules and `BUILD.md` `## Claims are proven mechanically` ban. The content is safe at `947f7494`. **Worker 0 escalates it to the maintainer; no worker touches `docs/review/`.** This is the same shape the spec-005 cycle carried for four deleted `bld-003-*` artifacts, which is precedent for escalating rather than for acting.

### Third growth, recorded at the close of R2's perform pass (2026-08-14) — ANOTHER SESSION IS EDITING SOURCE AND TESTS

Reported by Worker 1, verified by Worker 0 with `git status --short`, appended by Worker 0. `HEAD` has not moved (`947f7494`). **Nothing was reverted.**

- `django_strawberry_framework/_boundary_ordering.py`, `django_strawberry_framework/middleware/request_body.py`, `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py` (`M`) and `docs/review/rev-_boundary_ordering.md`, `docs/review/review-0_0_14.md` (`??`) — a concurrent session working the request-body / boundary-ordering transport surface.

**Nothing in this cycle may touch any of it**, and the collision risk is one-directional: this cycle is source-read-only, so it cannot write these files, while their session can move the source under a claim this cycle's read-only audit made. The audit's findings that could be affected are narrow and re-derivable — the 37-entry `__all__` roster and the export pin in `tests/base/test_init.py`, neither of which is in that session's diff. **R3 and the final gate re-derive the roster rather than trusting `### The read-only correctness audit — findings`.** The `pytest` / `ruff` / `git diff --check` baseline exception in `## Baseline-dirty out-of-scope files` now covers four source and test files as well, which makes it load-bearing rather than formal: a red final gate attributable to that session's in-flight work is reported, not fixed here, and never blocks `final-accepted`.

**Expect this list to grow.** The spec-004 and spec-005 cycles recorded six growth events between them, including concurrent sessions committing mid-cycle. `HEAD` may move during this cycle; **any pass quoting a commit hash from this plan re-derives it rather than trusting it**, and proves its own work was not swept into someone else's commit with `git log --stat` over this cycle's paths — never `git status` alone (`AGENTS.md` #"Staged `git mv` gets swept by a concurrent commit" is the standing hazard). If the list grows, workers **report it and never revert it**, and Worker 0 appends it here rather than a worker editing the plan.

**Baseline exception for the final test-run gate**, recorded here because `BUILD.md` `## Final test-run gate` requires it in the plan's preamble to be honoured: `uv run pytest --no-cov`, `uv run ruff format --check .`, `uv run ruff check .`, and `git diff --check` all read the whole tree, so they will see the concurrent card-wrap's churn. A failure attributable to a file this cycle never wrote does **not** block `final-accepted` and does **not** route back through a residual item's loop; it is reported to the maintainer. The gate still reports each command's real result — the exception governs what a result *blocks*, never whether it is recorded honestly.

### Fourth through ninth growth events, appended at cycle close by Worker 0 (2026-08-14)

Events 4-7 were reported by R2, R3, and the final gate in their artifacts ("Worker 0 to append to the plan"); event 8 is the gate's own measurement; event 9 is Worker 0's, taken at this append. **Nothing was reverted at any event, and `HEAD` is re-derived unmoved at `947f7494` as of event 9.** All are out of scope; the standing dispositions (report, never revert, never `git checkout`) are unchanged.

- **Fourth growth** (close of R2's perform pass, `bld-006-r2` `### Concurrent work — reported, not touched`): `docs/builder/bld-007-r2-spec_reconciliation.md` (`??`) — the concurrent spec-007 residual cycle reached its own R2. That cycle owns `docs/README.md`, which R2 re-measured at its own reading time and found clean.
- **Fifth growth** (mid-R3, `bld-006-r3` `### Validation run` step 1): `docs/builder/bld-007-r3-doc_completion_archive.md` (`??`) — the spec-007 cycle at its own R3. Same pass also recorded a **correction to this plan's dispatch premise**: `docs/GLOSSARY.md` was NOT baseline-dirty, so `git diff` was available as an independent verification for that one path and was taken.
- **Sixth growth** (close of R3, `bld-006-r3` `#### Addendum … a FIFTH growth event` — its local numbering counts from its own step 1): `django_strawberry_framework/_cross_web_patches.py` (`M`) — the transport / boundary-ordering session extending its working set to a fifth source file, consistent with `docs/review/rev-_cross_web_patches.md` being among the deleted review artifacts.
- **Seventh growth** (R3 `### Hand-off to the final gate`): `docs/review/rev-_cross_web_patches.md` moved `D` → `M` — a deleted committed review artifact re-appearing modified. The gate's baseline exception was restated there to cover six other-session source/test/review files.
- **Eighth growth** (the final gate, `bld-006-final.md`): `docs/builder/bld-007-r2-…` and `bld-007-r3-…` both present untracked (spec-007 at its R3), `docs/review/rev-_boundary_ordering.md` and `docs/review/review-0_0_14.md` untracked, `rev-_cross_web_patches.md` still `M`. HEAD `947f7494`.
- **Ninth growth** (Worker 0, at this append — POST-gate, so the gate's green results predate it): a **concurrent spec-008 residual cycle is now live** (`docs/SPECS/spec-008-definition_order_independence-0_0_4.md` `M`, `appx/spec-008-…-rationale.md` `??`, `docs/builder/build-008-…md` + `bld-008-r1/r2-*.md` `??`); the spec-007 cycle has reached its final gate (`bld-007-final.md` `??`); further sibling-spec churn (`spec-001` `M`, `spec-010` `M`); the transport session's set grew again (`django_strawberry_framework/_request_body.py` `M`, `docs/review/rev-_request_body.md` `??`); and the `docs/review/` deletions changed shape — `rev-_django_patches.md` and `rev-_strawberry_patches.md` are now `M` where `### Second growth` records them `D`, while `rev-apps.md` and `rev-conf.md` remain `D`. This cycle's own paths remain dirty/untracked and uncommitted, verified with `git log -1 --stat` over them (newest touching commit `ff65666d`, pre-cycle) — never `git status` alone. The maintainer escalation on `docs/review/` stands, with the file list updated as above.

## Concurrent-writable tracked binary / generated files

Churn in these is not proof a worker caused it (`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`). Unlike the four prior residual cycles, **all three are already dirty at this pre-flight and R3 must legitimately write two of them**, so "`git diff` is clean" is available as a verification for none of them.

- `examples/fakeshop/db.sqlite3` — **R3 writes it** (glossary bullets per Maintainer decision 2; card-052 `CardItem` prose per `### The coordinated retirement`). Compare `iterdump()` semantics, never file bytes. Apply writes **on top** of the concurrent state without reverting.
- `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html` — generated; regenerated by R3 after its DB writes. Never hand-edited (`AGENTS.md` #"GLOSSARY.md is DB-generated"; `START.md` "Rendered docs — fix the source, not the file").
- Verify by **two-consecutive-regenerate byte-stability** plus spot-checks of the rendered result, and by a **baseline regenerate-to-temp diff taken BEFORE any DB edit** — that baseline is what separates the concurrent writer's pending state from this cycle's own output. Re-run `import_spec_terms --check` **after** the writes rather than trusting a pre-flight reading. Hand the mixed diff to the maintainer to reconcile at commit.

## Build-wide context flags

- **Writable set, exhaustively.** `docs/SPECS/spec-006-public_surface-0_0_3.md` (R2); `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` (R1, new); `docs/SPECS/spec-002-optimizer-0_0_2.md` and `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` (**R2 only, and only for the retirement sites named in `### The coordinated retirement — every inbound site`**); `examples/fakeshop/db.sqlite3` + the three generated docs (R3); the four `bld-006-*` artifacts; this plan (Worker 0 only); the four namespaced memory files.
- **No source or test file is writable.** Package source, `tests/`, and `examples/` code are read-only throughout, docstrings included. The audit found no defect; a defect found later is escalated, never edited.
- **`0.0.3` shipped and the version quintet is at `0.0.14`.** No item touches `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, the GLOSSARY package-version line, or `uv.lock`. In particular: this cycle **reconciles the spec to `__all__`, never `__all__` to the spec.**
- **`CHANGELOG.md` is closed.** `AGENTS.md` rule 21 governs: no item edits it.
- **Sibling specs are read-only except for the one declared retirement.** `## The single-ownership law` clause 3 is the boundary.
- **The spec is already archived.** `BUILD.md` `### Spec stays at its working location` requires a move be plan-declared; there is none. `docs/SPECS/spec-006-public_surface-0_0_3.md` and `docs/SPECS/appx/spec-006-…-terms.csv` are already at their archived paths, `SpecDoc.path` already reads the archived path, and both `KANBAN.md` references already point there. **R1's new rationale file is therefore written directly to `docs/SPECS/appx/`** — the archived-companion location `AGENTS.md` rule 26 names — never to `docs/` first and moved after. At `docs/SPECS/appx/` depth its link definitions need `../../GLOSSARY.md` for a `docs/` target and `../spec-NNN-….md` for a `docs/SPECS/` sibling; `docs/SPECS/appx/spec-005-…-rationale.md` shows the shape.
- **Only the maintainer commits.** No worker commits, and none creates or switches a branch.

## Worker-0-verified facts, passed into dispatch so no worker re-derives them

Read-only queries and greps, run 2026-08-14 at HEAD `947f7494`.

- `Card.objects.get(number=6)` → `card_id` `DONE-006-0.0.3`, `status.key` `done`, `target_version.number` `0.0.3`, title `Documentation/status positioning for shipped Layer 2`. The card is **already Done**; no status flip is in scope, and the 2026-07-30 renumber left 006 untouched (it rotated 045-068 only).
- `SpecDoc` for card 6 → name `spec-006-public_surface-0_0_3`, **`path` already `docs/SPECS/spec-006-public_surface-0_0_3.md`**. No repoint needed. (`SpecDoc.path` is the writable column; `SpecDoc.url` is a read-only `@property` deriving from it — assigning `url=` raises.)
- `card.glossary_links.count()` → **7**, exactly matching the 7 rows of `docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv`: `djangooptimizerextension`, `djangotype`, `filterset`, `metaprimary`, `optimizerhint`, `queryset-diffing`, `schema-audit`. One row per anchor, so the CSV is importable (`worker-0.md` `### DONE-card invariants` — a green `check_spec_glossary` alone does not prove this).
- **Staged-anchor sweep:** `grep -rEn 'TODO\(spec-006|TODO-(ALPHA|BETA|STABLE)-006' .` → **zero hits** outside `KANBAN*`. `BUILD.md` `## Cross-slice integration pass` step 6 is already discharged at baseline; R3 re-runs it as its backstop.
- **Every reference TO spec-006 (all `.md`, excluding this plan):** `KANBAN.md:141` and `:4824` (generated, already the archived path, never hand-edited) and `KANBAN.html`; `KANBAN.md:319` and `:322` (card-052 prose — **R3 writes these via `CardItem.text`**, see the retirement table); `docs/SPECS/spec-005-django_type_contract-0_0_3.md:89`; `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:300` and `:517`; and four prior-cycle build plans (`build-001:166`, `build-002:156`/`:198`, `build-005:128`/`:231`/`:260`/`:261`, `bld-005-*`), which are historical artifacts of closed cycles and are **not** edited.
- **Exactly one inbound reference from another spec exists, and it is not a rule citation.** `spec-005:89` names spec-006 as the companion covering "the package-level public-surface and documentation-discipline rules that this contract feeds into", and records that spec-006 cites spec-005's `### Accepted vs deferred Meta keys` **by title**. That by-title dependency runs spec-006 → spec-005 and is R2's to preserve or to fix on both sides in one change (D13, and `### The 7-anchor constraint`'s sibling hazard).

### The 7-anchor constraint

`docs/SPECS/appx/spec-006-…-terms.csv` carries 7 anchors and `check_spec_glossary.py` passes because each has at least one reference-style link in the spec body. Both R1 (which moves text out) and R2 (which rewrites text) can silently drop the last remaining link for an anchor. The failure is not cosmetic: `import_spec_terms` is what card 6's glossary-link set is rebuilt from, so a dropped anchor breaks the card-wrap chain.

**Measured, not read** — every carrier counted as a reference-style `[text][ref-id]` use, code spans excluded (a code span carries no anchor; miscounting them is the error Worker 0 made on the spec-005 cycle and had corrected at R1):

| Anchor | Carrier (sole, in every case) | Risk |
|---|---|---|
| `glossary-djangotype` | `spec:13`, inside `## Current state`'s 5-name surface list | **High** — D1 rewrites the list wholesale |
| `glossary-djangooptimizerextension` | `spec:14`, same list | **High** — same rewrite |
| `glossary-optimizerhint` | `spec:15`, same list | **High** — same rewrite |
| `glossary-schema-audit` | `spec:53`, inside `#### Decision for 0.0.3` | Medium — the decision survives; its `B1-B8` vocabulary may not |
| `glossary-queryset-diffing` | `spec:53`, same sentence | Medium — same sentence |
| `glossary-filterset` | `spec:117`, inside the falsified "`FilterSet` will provide…" signaling example | **High** — D11 rewrites the example |
| `glossary-metaprimary` | `spec:123`, inside `### When to amend this spec`'s future-spec list | **High** — D12 rewrites the list |

**All seven anchors are single points of failure, and all seven sit in prose the drift table marks for rewrite.** This is stricter than spec-005's profile, where six of seven were single-carrier and four sat in falsified prose. **Every pass that writes the spec re-runs `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md` and quotes the result in its artifact.** A rewrite that would drop an anchor re-sites the link into the surviving contract prose **in the same edit** — never by re-adding narration the pass just removed, and never by editing the CSV.

### What R1 inherits

Spec-006 is the smallest spec of the five residual cycles (10,934 bytes against spec-005's 13,346 and spec-004's 33,928). Its deliberative layer is small but unusually load-bearing, because the document's *subject* is a set of rules and its deliberation is the argument for those rules.

- **The one clearly-deliberative passage is `### docs/README.md structure`'s third paragraph** — "There is no third section. The reviewer suggested `Current` / `Planned` / `Not implemented yet`, but the third section duplicates the second once the markers are in place. The sharper fix is the markers themselves, not more sectioning." That is a rejected alternative with its reason, verbatim: rationale material by definition.
- **The `## Problem statement`'s second paragraph** ("The fix is not more documentation. It is stricter documentation discipline.") is the document's thesis. `worker-1.md` rule: when it is unclear whether a sentence is deliberation or instruction, **it stays**.
- **`## Open questions` reads "None blocking 0.0.3"** — a sentence whose entire meaning is a release-gating judgement made in April 2026. Pure deliberation, and the same shape spec-005's cycle retired.
- **The `## References` alpha-review bullet** names recommendations #1/#2/#7/#8 of a document not present in the repository. Spec-005's cycle hit the identical bullet (its D19) and **removed** it; that precedent is available to R2 and is not binding on it.
- **The rationale must be keyed to spec sections.** `BUILD.md` `## Spec rationale extraction` requires each entry name the spec decision it serves by heading and anchor, and carry: the alternatives rejected and why each lost; every change the decision has undergone with the round or later spec that caused it; and any claim the decision once made and may no longer make. The drift table below is R2's input, but **its "why" column is R1/R2's output** — that is precisely the maintainer's instruction that *explanations of the changes go in the rationale, not the spec*.
- **The single most valuable thing this rationale can record** is why the rules survived while their instruments did not: a documentation-discipline spec whose own documentation obligations were never dischargeable, whose closed vocabulary shrank to three markers by disuse, and whose central gate had to stop being a biconditional the moment a shipped surface wanted its import path to *be* its opt-in. That analysis exists nowhere in the repository.
- **Do not duplicate the siblings.** `docs/SPECS/appx/spec-005-…-rationale.md` narrates the `Meta`-key contract and `appx/spec-002-…-rationale.md` narrates the optimizer's own section retirements. R1 reads both to avoid restating, not to borrow from.

### Verified spec-versus-HEAD drift — R2's input, verified by Worker 0 against source

Read at HEAD (`947f7494`) on 2026-08-14 with the symbol-qualified paths given. Each row is a claim the spec makes that HEAD complicates or falsifies. **A prescribed correction is not included: how the spec should read is Worker 1's call, and the alternatives it rejects belong in the rationale file.** Worker 1 re-verifies each row rather than trusting this table, which is Worker 0's verified floor and not an exhaustive sweep.

| # | Spec claim | HEAD reality | Owner of the move |
|---|---|---|---|
| D1 | `## Current state`: "0.0.3 public surface (per `__init__.py`)" — a 5-item list (`DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `auto`, `__version__`) | **37** entries in `__all__`, verified by import: every one resolves via `hasattr`. Plus two categories the spec has no room for — `logger`, consumer-facing and deliberately *not* in `__all__` (`__init__.py` #"Consumer-facing: the name is the key"), and **7 lazy DRF names** resolved by PEP 562 `__getattr__` and deliberately absent from `__all__` so `import *` stays DRF-free (`SerializerMutation`, `register_serializer_field_converter`, `SerializerFieldConversion`, `describe_serializer_input`, `NestedSerializerConfig`, `SerializerHookContext`, `UploadMetadata`). **Sole carrier of `djangotype`, `djangooptimizerextension`, `optimizerhint`** | every card that shipped a public symbol; spec-039 Decision 12 for the lazy category |
| D2 | the fenced `__all__` tuple for `0.0.3`, five entries | Falsified as present tense. HEAD's tuple is pinned **verbatim** by `tests/base/test_init.py::test_public_api_surface_is_pinned`, which is the executable single source and carries its own per-card provenance comment | the pin itself |
| D3 | `## Current state`: "Current README structure (`docs/README.md`): Goal, vs comparisons, full target architecture (subsystems, folder layout, tests-mirror), design-doc list, status" | **None of those headings exist in `docs/README.md`**, which now runs Installation → Quick start → What just happened? → Today and coming next → the per-subsystem contract sections → Testing → Running the example. Positioning and status moved to the root `README.md` (`## Why this package exists`, `## Status`) and the doc map to its `## Project documentation` | spec-007 (the onboarding/docs consolidation) |
| D4 | `## Current state`: "The remaining mismatch risk is Layer 3: the README's target layout includes subpackages that do not exist on disk yet (`filters/`, `orders/`, `aggregates/`, `management/`, plus `apps.py`, `fieldset.py`, `permissions.py`, `connection.py`)" | Six of the eight **exist**: `filters/`, `orders/`, `management/`, `apps.py`, `permissions.py`, `connection.py`. `aggregates/` is still planned (`docs/TREE.md` target layout, "planned by TODO-BETA-057-0.1.3"); `fieldset.py` never landed as a module — it is planned as the **package** `fieldset/` (TODO-BETA-054-0.1.1). The target layout has also grown three entries the spec cannot have known (`graph/`, `permissions/` as a package migration, `utils/predicates.py`, `extensions/graph.py`) | spec-021/027/028/034 + the beta-line cards |
| D5 | `### Top-level re-export rule` condition 3: "The contract is documented — the symbol appears in `docs/README.md` \"Current surface\" with a status marker of `shipped`" | **The section has never existed.** The documented locus that emerged is `docs/GLOSSARY.md` `## Public exports` (34 bullets, each linking a per-feature entry carrying `**Status:**`) — which is a *better* fit for the condition than the section named, since the marker is per-entry and DB-enforced. Measured gap: 4 `__all__` names carry no bullet, and `SerializerMutation` carries one while deliberately outside `__all__`. **Maintainer decision 2 closes the bullet gap in R3**; the condition's wording is R2's | spec-007 (the section never landed); the glossary became the locus |
| D6 | `### Top-level re-export rule` opener: "re-exports a name **iff** all four are true" | **Falsified as a biconditional.** Six shipped, tested, documented, stable families are deliberately NOT root-exported because the import path *is* the opt-in boundary: `views` (spec-046 #"never a package-root export"), `routers` (spec-041, which explicitly **rejected** the lazy-root-export shape), `extensions.DjangoDebugExtension` (`__init__.py` #"Do not import or root-export DjangoDebugExtension here"), `middleware.debug_toolbar`, `testing` (spec-043 #"The family stays under"), and `auth` (spec-040 Decision 3). A seventh category is conditional: the DRF names are root-*reachable* but out of `__all__` while the dependency is soft. The four conditions are **necessary**, never sufficient | spec-039/040/041/043/046 |
| D7 | same section: "Names that fail any of these stay reachable via their dotted submodule path … so power users and tests can still get them" | Still true, and now understates the case: for the D6 families the dotted path is the **contract**, not a consolation for having failed a gate | spec-040/043/046 |
| D8 | `### docs/README.md structure`: two sections (`## Current surface` / `## Planned surface`), a marker on every entry, "no entry without a marker", and the folder tree split in two with per-entry markers | **Never implemented.** `docs/README.md` carries `## Today and coming next` — a shipped-capability list stamped with one version (`**Shipped today** (0.0.14)`) plus a per-release roadmap — and points at `docs/GLOSSARY.md` for per-feature status. The two-tree half **did** land, in `docs/TREE.md` rather than the README, and its target tree marks each not-yet-existing entry `planned by TODO-BETA-NNN-0.1.X` — card-anchored provenance, not a vocabulary marker | spec-007; `docs/TREE.md`'s renderer |
| D9 | `### Status-marker vocabulary`: seven markers, used in `docs/README.md`, `docs/TREE.md`, and any spec doc, "No synonyms, no improvisation" | **Three live.** Occurrence counts across `docs/README.md` / `docs/TREE.md` / `docs/GLOSSARY.md` / `TODAY.md`: `experimental` **0/0/0/0**, `aspirational` **0/0/0/0**, `in flight` **0/0/1/0**. `shipped`, `planned`, and `deferred` are live; `partial`'s hits are the word in other senses, not a status marker. The glossary's DB-enforced vocabulary is **exactly two rows** — `GlossaryStatus` keys `shipped` and `planned`. The live vocabulary also gained a precision the spec's flat markers lack: a **version stamp** (`**Status:** shipped (0.0.5)`, `planned for 0.1.3`) | disuse; the glossary DB is the de-facto authority |
| D10 | `### Alpha signaling rules`: the `partial` example — "`DjangoOptimizerExtension`'s per-resolver dispatch is shipped; the `on_executing_start` hook required for end-to-end effectiveness is in flight" | Describes a state that ended at `0.0.3` — the hook shipped, which is what this spec's own `#### Decision for 0.0.3` records. The neighbouring `shipped`-tense example is fine: `convert_choices_to_enum` **exists** at `types/converters.py` and is exercised by three test modules, so unlike spec-005's D22 this citation resolves | the card itself |
| D11 | same section: "\"[`FilterSet`][…] will provide…\", \"`permissions.py` is reserved for…\"" as the future-tense exemplars | Both shipped: `FilterSet` at `0.0.8` (spec-027), `permissions.py` at `0.0.10` (spec-034, whose Decision 4 records the package-root export). **Sole carrier of `filterset`** | spec-027, spec-034 |
| D12 | `### When to amend this spec`: "Every future subsystem spec (filters, orders, aggregates, permissions, connection field, relay interfaces, [`Meta.primary`][…], consumer overrides)" | **Seven of eight shipped** — relay interfaces `0.0.5`, `Meta.primary` + consumer overrides `0.0.6`, filters + orders `0.0.8`, connection field `0.0.9`, permissions `0.0.10`. Only aggregates remains, carded at `0.1.3`. **Sole carrier of `metaprimary`** | spec-015/018/019/027/028/030/034 |
| D13 | same section: future specs "Reference this spec for the rules", and "If a future change introduces a marker that isn't in this spec … the marker is added here in the same change. The vocabulary is single-sourced" | **Never once happened, in either direction.** No later spec cites spec-006 at all — the only inbound spec reference is `spec-005:89`, a companion bullet. Every feature spec decided its own export placement independently and locally (spec-027 Decision 2, spec-034 Decision 4, spec-037 Decision 5, spec-041's rejected-alternative block, spec-043, spec-046), and no marker addition was ever folded back. This is the direct cause of D5, D8, and D9 — and therefore of this cycle, exactly as spec-005's D18 was of its own | the card itself; this is the cycle's root cause |
| D14 | `## Coordination with other specs` bullet 3 + `## References` bullet 3: the optimizer-visibility decision "is amended into `spec-002-optimizer-0_0_2.md` \"Visibility status\" so the optimizer spec carries the local context" | **Maintainer decision 1**: the requested copy is retired and both bullets go with it. Every inbound site is fixed in the same change — `### The coordinated retirement — every inbound site` | this cycle, by maintainer decision |
| D15 | `## References` bullet 1: "The original alpha review — recommendations #1 (silent acceptance), #2 (README aspirational), #7 (docs gap), #8 (alpha guarantees); this spec is the durable record of those findings" | Names a document **not present anywhere in the repository**; the bullet's own second clause ("this spec is the durable record") makes the reference self-describing rather than resolvable. Spec-005's identical bullet was removed by its cycle | the alpha review; spec-005's cycle set the precedent |
| D16 | `## Open questions`: "None blocking 0.0.3" | A release-gating judgement made in April 2026 about a release eleven versions back | the card itself |
| D17 | `## Non-goals`: "that lives in `docs/README.md` \"Package architecture\" and the per-subsystem spec docs" | No `## Package architecture` section exists in `docs/README.md`; the layout lives in `docs/TREE.md` (two trees). Second undischargeable README obligation in the same spec, the same shape spec-005 carried at its D6/D21 | spec-007 |
| D18 | `### When a subsystem is top-level vs subpackage-only`: a subsystem "starts as a subpackage with an `__init__.py` that re-exports its consumer-facing names internally … The subpackage `__init__.py` keeps its own re-exports too, so both import paths continue working" | **Verified true at HEAD, subsystem by subsystem.** `types/`, `optimizer/`, `filters/`, `orders/`, `mutations/`, `forms/`, `auth/`, `extensions/`, `testing/`, and `utils/` each declare `__all__` and re-export their consumer-facing names, and the promoted ones kept theirs (`types/__init__.py` #"__all__ = (\"DjangoType\", \"SyncMisuseError\", \"finalize_django_types\")" beside the root's own re-export). One of two topics needing no correction | nothing; the rule held |
| D19 | same section: "Internal helpers — factories, walkers, individual `Filter` / `Order` / aggregate primitives, converters — never get top-level re-exports" | **Verified true.** No factory, walker, converter, or set-primitive appears in `__all__`; the closest calls are deliberate and documented (`FieldError` is the public envelope, `OptimizerHint` the public wrapper). The second topic needing no correction | nothing; the rule held |

**The scope trap specific to this spec.** Spec-006's subject is a rule, and the pull is toward turning it into a current-state inventory of the 37-name surface — a list that has changed at least eleven times and changes again at `0.1.0`. That would recreate D13 as a maintenance obligation rather than retire it. `tests/base/test_init.py::test_public_api_surface_is_pinned` is the executable single source for the roster and `docs/GLOSSARY.md` `## Public exports` is the documented one; the spec's durable contribution is the **rule** (what licenses a name into the surface, what the docs owe a consumer about it, why an unmarked claim is a bug), not the roster.

### The read-only correctness audit — findings

"MAKE SURE NOTHING WAS SKIPPED IN THE CODE" has a literal reading here, because spec-006's rules are auditable properties of the source and the docs: **every name in `__all__` must be effective end-to-end, tested, documented, and stable, and no internal helper may be in there.** Audited name by name. **No defect found.**

- **Rule 1 (effective end-to-end) — passes for all 37.** `[n for n in p.__all__ if not hasattr(p, n)]` → `[]` under the fakeshop settings, and each spot-checked symbol resolves to a real definition in its owning module (`SyncMisuseError` → `utils.querysets`, `DjangoMutationExecutionContext` → `schema`, `DjangoFilePathType` → `types.converters`, `DEFAULT_ERROR_POLICY` → an `ErrorPolicy` instance). No stub, no placeholder. The 7 lazy DRF names also resolve through the `__getattr__` guard.
- **Rule 2 (tested) — passes.** `tests/base/test_init.py::test_public_api_surface_is_pinned` pins the whole tuple verbatim, `::test_file_upload_exports_resolve_to_their_source_definitions` pins re-export *identity* (not merely membership), and every spot-checked name carries independent coverage (`SyncMisuseError` 15 test files, `DjangoFilePathType` 3 + 2 example files, `RESOURCE_LIMIT_ERROR_CODE` 1 + 2).
- **Rule 3 (documented) — one measured gap, and Maintainer decision 2 closes it in R3.** 33 of 37 names appear in `docs/README.md`; all but `DjangoMutationExecutionContext` appear somewhere in `docs/GLOSSARY.md`; the `## Public exports` bullet list is 4 short. No name is undocumented in *both* surfaces except `DjangoMutationExecutionContext`, which `docs/README.md` covers in prose under `### DjangoSchema is required for generated mutations`.
- **Rule 4 (stable naming) — no evidence of churn.** Every `__all__` entry traces to a card that shipped it, per the provenance comment in the export pin.
- **Rule 19 (no internal helpers) — clean.** Nothing factory-, walker-, or converter-shaped is exported.

Two observations recorded so R2 does not mistake either for drift to "fix":

1. **`logger` being public-but-not-in-`__all__` is deliberate**, and the source says so. It is a *category* the spec's binary gate cannot express, not a violation of it.
2. **`SerializerMutation` having a glossary bullet while absent from `__all__` is deliberate**, and the bullet says why. Same category as (1), from the opposite direction.

### The coordinated retirement — every inbound site

Maintainer decision 1, executed as **one change** across every site. `## The single-ownership law` clause 2 is the authority; the sites were established by `grep -rn 'Visibility status\|visibility-status' --include='*.md' .` and are re-swept by the pass that writes them.

| # | Site | What it says now | Disposition | Item |
|---|---|---|---|---|
| 1 | `docs/SPECS/spec-002-optimizer-0_0_2.md:57-58` | the `## Visibility status` heading + two sentences | the retirement itself; the merged `__init__`-export precision needs an explicit disposition (Maintainer decision 1's nuance) | R2 |
| 2 | `docs/SPECS/spec-006-public_surface-0_0_3.md:136` | `## Coordination` bullet 3, which is what *requested* the copy | the back-pointer goes; spec-002 remains named as the implementation spec | R2 |
| 3 | `docs/SPECS/spec-006-public_surface-0_0_3.md:147` | `## References` bullet 3, "carries the local visibility-status amendment that this spec governs" | goes with the amendment it names | R2 |
| 4 | `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:261` | "Spec: [Shipped slices][spec-002-shipped] and [Visibility status][spec-002-visibility], which together absorbed everything it carried" | the second link re-points or drops; the sentence must still name what absorbed the removed `## Current state` | R2 |
| 5 | `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:298-305` | "*Not rejected, and not this cycle's to change — `## Visibility status`.* … do not rename a heading another file cites; fix it in the citing file instead, in the cycle that owns that file" | **falsified by the retirement** and the most important site in the table: it is the record of the deferral this cycle discharges. Appended-to, not deleted (the file is append-only per `worker-1.md` rule 4) so the deferral and its discharge both stand | R2 |
| 6 | `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:515` | `[spec-002-visibility]: ../spec-002-optimizer-0_0_2.md#visibility-status` — the only `#anchor` citation of spec-002 anywhere | re-point or remove; a dangling def is a `check_trailing_commas` scaffold failure and a broken link | R2 |
| 7 | `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:60`, `:83-85`, `:269`, `:274` | four narrative mentions inside entries about the *removed* `## Current state` | these are **history about a prior removal**, correct as written; re-check rather than rewrite, and do not sweep them into the retirement | R2 (verify only) |
| 8 | `KANBAN.md:319` (card `TODO-ALPHA-052-0.1.0` Scope) | the standing deferral: "`## Visibility status` stays because two live pointers would break with it … Retire the heading in the cycle that owns `spec-006`, not this one, and re-point the companion there" | **discharged** — rewrite the `CardItem.text` via the ORM to record the retirement, then regenerate. Never hand-edit `KANBAN.md` | R3 |
| 9 | `KANBAN.md:322` (same card) | "Do not sweep up `spec-006-public_surface-0_0_3.md:136` and `:147` in the same pass: both name `## Visibility status`, and both are live and correct" | **falsified by the retirement** — the two sites are no longer live. Same ORM-then-regenerate route | R3 |
| 10 | `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md:328` | a **verbatim quotation** of spec-003's own discharged "when O4 ships" instruction, which happens to contain the words "visibility status" | **not a reference** — a quotation of a historical instruction. Leave untouched; recorded here so no pass "fixes" it | none |
| 11 | `docs/builder/build-002-…:149`/`:155`/`:156`/`:179`/`:198`, `build-003-…:192`, `bld-003-final.md:197` | prior cycles' verification tables naming the section and the retitle constraint | historical artifacts of closed cycles; **never edited** (`AGENTS.md` rule 22's spirit, and they are the record the retirement is auditable against) | none |

**A twelfth site is conditional and R2 owns the call.** `spec-005:89` records that spec-006 cites spec-005's `### Accepted vs deferred Meta keys` **by title**. If R2's reconciliation changes or drops that citation (it sits at `spec:108`, inside the `deferred` marker definition D9 touches), then `spec-005:89` is falsified and must be fixed in the same change — the identical failure shape this table exists to prevent, running in the other direction. If the citation survives, `spec-005:89` needs nothing. **Either way the pass records which it was.**

### Corrections to Worker 0's own instruments, appended at cycle close (Worker 0, 2026-08-14)

The plan is Worker 0's file and these are Worker 0's defects, adopted from `bld-006-r3` `### Notes for Worker 1 (spec reconciliation)` items 1-4 (each of which supplies its replacement text verbatim) and from the final gate's `### Deferred work catalog`. **In every case the implemented behavior was correct; what was wrong was the evidence formula or the measurement I dispatched.** The prior sections above are not edited — this section is the correction, per the cycle's own convention that a record is corrected by appending, never by rewriting a section a pass already relied on. The defective formulas lived in the R3 dispatch text, which is quoted in full in `bld-006-r3`; a future dispatch reusing that text applies the four replacements below.

1. **The D2 evidence formula was unsatisfiable from the moment R2 ran.** "`git diff -- docs/SPECS/spec-006-public_surface-0_0_3.md` is empty" can never hold in a cycle whose own R2 legitimately rewrites that file uncommitted (`52 62` at the time). What the box actually needs is "the spec is byte-unchanged **by R3**", and the correct evidence is the mtime comparison Worker 2 substituted (spec `12:00:04` predating R3's first regenerate `12:50:04`), later superseded by Worker 1's own R3 edit being declared in `### Spec changes made`. **Rule extracted: an evidence formula must be satisfiable at the tree state the pass will actually see, not at the plan's baseline.**
2. **The row-8 replacement text I prescribed quotes the discharge heading with an ASCII hyphen** where `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:503` carries an em dash, so the quoted string greps to 0. My own ASCII house-style instruction caused it, and my declaring the bullet texts non-discretionary is why Worker 2 correctly wrote the defect as specified instead of fixing it. R3's replacement — quote only the distinctive stem `` `## The discharged deferral` `` — is adopted; the live fix is `CardItem` pk 1260's, target order: maintainer at commit, else card `TODO-ALPHA-052-0.1.0` (the exact `str.replace` is in `bld-006-final.md` `## The maintainer's commit brief`).
3. **The step-10 marker counts were wrong for `KANBAN.md`.** I dispatched `experimental` / `aspirational` as 0/0/0/0/0 across five durable docs; the true shape is 0/0/0/0 plus **1 each in `KANBAN.md`** (`:80` prose about a commented-out example schema block; `:1376` a card checklist item naming `# experimental` as a thing to sweep for) — both prose, neither a marker, no correction owed. The drift table's D9 row above is **not** wrong: its scope was four docs (`docs/README.md` / `docs/TREE.md` / `docs/GLOSSARY.md` / `TODAY.md`); the defect was my widening the doc set in step 10 without re-measuring.
4. **`CardItem.order` values and rendered ordinals are not the same thing**, and my step-8 spot-check conflated them: `order` 1 / 8 / 11 render as the **1st, 6th and 9th** `#### Scope` bullets because the sequence is sparse — so the check as I worded it fails against a correct render. Future formula: name both ("at their unchanged `order` values 1 / 8 / 11, rendering as the 1st / 6th / 9th bullets").

**The class, so it isn't lost with the scratchpads: "right substance, loose citation."** Six instances this cycle — the four above plus R1's box-1 and box-8 citation defects — and R2's final verification recorded four more scratchpad-only record corrections of the same shape (a `GlossaryDocument` model name where the row is `apps.kanban.models.BoardDoc` with `namespace='glossary'`; an n=6 shingle residue of 23 not 26; a survivor tally counting matching lines (2) not occurrences (6); two immaterial line ranges). None affected a durable file. The countermeasure the cycle converged on and this plan now states for its successors: **every checklist box cites evidence that is mechanically re-derivable at audit time, and an auditor re-derives the citation, not just the substance.**

**A method rule worth a durable home beyond this plan — the duplicate-check tokenizer.** R1's first spec-versus-rationale duplication measurement failed **open**, reporting 0 overlap where 3 restated passages existed, because a whitespace tokenizer leaves punctuation and Markdown emphasis attached to tokens and shifts window positions without changing the words. The rule: **a phrase-shaped duplicate check tokenizes on word characters (`[A-Za-z0-9_]+`), case-folds, and windows over the token stream** (8-word shingles served here). Routed per R1 to `worker-1.md` `### Performing the rationale move` for Worker 0 or the maintainer to add; recorded here so the rule survives even if that edit is declined — this plan is the committed record the next residual cycle's Worker 0 reads. Companion non-finding, so the number is not re-derived as a scare: 8-word shingle overlap between this cycle's rationale and its siblings measured 180 non-scaffold against a **247** control for the 006/005 pair — house-template vocabulary, *less* coupled than the control; R2 was instructed not to treat it as a finding and the same holds for any later reader.

## Artifact list

- `docs/builder/bld-006-r1-rationale_move.md`
- `docs/builder/bld-006-r2-spec_reconciliation.md`
- `docs/builder/bld-006-r3-doc_completion_archive.md`
- `docs/builder/bld-006-final.md`

No `bld-integration.md`-equivalent: a cross-slice integration pass exists to find duplication across slices that landed source, and this cycle lands none. Its live obligations are folded in — the staged-anchor sweep (`BUILD.md` `## Cross-slice integration pass` step 6) runs in R3, and the cross-artifact read runs in the final gate.

## Checklist

- [x] R1: Spec rationale extraction into `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` (Worker 1 performs the move; Worker 3 audits it; Worker 1 final-verifies) -> `docs/builder/bld-006-r1-rationale_move.md`
- [x] R2: Reconcile the spec with HEAD — every claim the package falsifies is restated as the contract that actually holds, or handed to the spec that now owns it — **and perform the coordinated retirement across every inbound site** (Maintainer decision 1); the explanation of each change lands in the rationale, never in the spec -> `docs/builder/bld-006-r2-spec_reconciliation.md`
- [x] R3: Finish the documentation and audit the archive — the `## Public exports` bullet completion (Maintainer decision 2), the card-052 prose discharge, the durable-doc audit, the three-direction cross-reference sweep, `SpecDoc.path` / terms-CSV verification, and the `TODO(spec-006` / `TODO-<MILESTONE>-006` staged-anchor sweep -> `docs/builder/bld-006-r3-doc_completion_archive.md`
- [x] Final test-run gate -> `docs/builder/bld-006-final.md`

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
