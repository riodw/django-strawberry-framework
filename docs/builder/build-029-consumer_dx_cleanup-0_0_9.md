# Package build plan: consumer_dx_cleanup / 0.0.9 (029)

Spec source: `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` (already archived; the spec did NOT move for this cycle)
Companion CSV: `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv` (exists, 44 terms, `check_spec_glossary` green)
Companion rationale: `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` (**does not exist — Slice 1 creates it**)
Target release: `0.0.9` (shipped; `pyproject.toml` is at `0.0.14`, no version file is touched by this cycle)
Date created: 2026-08-24
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

## Cycle type: residual / reconciliation cycle

`DONE-029-0.0.9` shipped its three functional slices long ago. This cycle does NOT re-build the card. Its contract is:

1. **Author the missing `-rationale.md` companion** (the one durable artifact the original cycle never produced).
2. **Prove nothing in the code was skipped, dropped, or forgotten** against the spec's `## Slice checklist`, `## Test plan`, and `## Definition of done`.
3. **Root-cause-fix any live regression against a spec-029 contract** that later cards introduced (`AGENTS.md` L4/L5 — a real regression in committed code is fixed, never deferred).
4. **Reconcile the spec with what actually exists at HEAD**, including every correction and optimization later cards made. The spec is rewritten to read as a clean current contract; **the explanation of what changed and why goes in the rationale file, never in the spec** (`BUILD.md` `## Spec rationale extraction`).

**Fence (maintainer-set, non-negotiable):** this cycle edits **spec files and `.py` files only**. No closeout / agentflow edits. No `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `CHANGELOG.md` / `db.sqlite3` edits — anything found there is routed to `### Deferred work catalog` in `bld-final-029.md`, not fixed. **Every file this cycle creates carries `029` in its name.**

## Pre-flight

Pre-flight: passed on 2026-08-24 with two recorded exceptions (below); baseline: **clean** (`git status --short` empty); cleanup: `docs/shadow/` cleared, `docs/builder/worker-memory/` created + four files seeded empty, `docs/builder/temp-tests/` already empty.

| Step | Outcome |
|---|---|
| 1. Working-tree baseline explicit | `git status --short` → empty. Clean baseline. |
| 2. `scripts/review_inspect.py` runs | Smoke ran against `django_strawberry_framework/types/converters.py --output-dir docs/shadow --stdout`; emitted a valid overview. |
| 3. Build artifacts reset | No `build-*.md` and no `bld-slice-*` / `bld-integration-*` / `bld-final-*` from a prior cycle exist (the maintainer's `867cea2c "Delete old artifacts;"` cleared them). **Exception recorded — see below.** Every path this plan creates verified absent. |
| 4. `.gitignore` lists scratch paths | `docs/shadow/` (line 174), `docs/builder/worker-memory/` (188), `docs/builder/temp-tests/` (192) all present. |
| 5. Scratch directories cleared | Done. |
| 6. Spec-doc consistency check | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` → `OK: 44 terms - all have glossary entries and at least one spec link.` |
| 7. Spec rationale extracted | **NOT DONE — this is Slice 1 of this cycle.** No slice after Slice 1 is dispatched until it is done and verified. |

**Pre-flight exception 1 — `docs/builder/bld-003-final.md` is left in place.** It is a tracked leftover of the `spec-003` cycle (`20a9752f`) that **survived** the maintainer's deliberate `867cea2c "Delete old artifacts;"` commit. Deleting a tracked file the maintainer just chose to keep is not Worker 0's call, and it cannot collide with any `-029` path this plan creates. Left untouched; flagged to the maintainer.

**Pre-flight exception 2 — `docs/shadow/current/` was cleared along with the rest of `docs/shadow/`.** That subtree is owned by `scripts/review_historical_package_snapshot_at_commit.py` (`AGENTS.md` rule 23) and is regenerable and gitignored; pre-flight step 5 requires the path be emptied.

## Baseline-dirty out-of-scope files

**None** — the working tree was clean at pre-flight. Any file that turns up modified mid-cycle without a worker's edit is a **concurrent session's work**: never revert it, never "tidy" it (`AGENTS.md` rule 34, `START.md` "Concurrent sessions"). Diff against `git show HEAD:<path>` into a scratch path **outside** the repo; never `git stash` / `git checkout` / `git restore` / `git worktree`.

Tracked binary / generated files a concurrent writer can rewrite mid-cycle (`BUILD.md` `### Tracked binary / generated files`): `examples/fakeshop/db.sqlite3`, `examples/fakeshop/db_shard_b.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`. **This cycle writes none of them.** Churn there is a concurrent writer's and is out of scope.

## Build-wide context flags

- **Version-bump owner:** not this card. `pyproject.toml`, `django_strawberry_framework/__init__.py::__version__`, `tests/base/test_init.py::test_version`, and `uv.lock` are **never** touched (spec Decision 11 / DoD 16). The package is at `0.0.14`; `0.0.9` is history.
- **CHANGELOG:** `AGENTS.md` rule 21 plus the maintainer fence keep `CHANGELOG.md` closed to this cycle. Its `0.0.9` bullets already landed; nothing there is edited.
- **Coverage:** never run `pytest` with any `--cov*` flag. `--no-cov` is the only permitted coverage-shaped flag (`pytest.ini` `addopts` auto-applies `--cov`).
- **Derivation-baseline drift is expected and is the point.** The spec's mechanism claims are pinned to strawberry-graphql `0.316.0`. The shared `.venv` at HEAD resolves **strawberry-graphql 0.323.2 / Django 6.1 / Python 3.14** (read with `uv pip list` on 2026-08-24, not from memory). Worker 0 re-derived the load-bearing mechanism at HEAD before writing this plan: `Schema.get_extensions` in 0.323.2 is still `[ext if isinstance(ext, SchemaExtension) else ext() for ext in self.extensions]`, run per request. **Decision 3's mechanism therefore holds unchanged at HEAD** — a bare class and a constructing `lambda` still re-instantiate per request (cold plan cache); a `lambda` closing over a singleton still reuses one instance. This is what makes Slice 2 below a genuine regression repair and not a stale-contract relaxation.
- **A spec-029 claim is a claim, not a measurement.** Every count, census, and "zero hits" assertion in the spec was true when written and several are false at HEAD. Workers re-derive; they never restate a spec number as fact. Enumerate populations, never assert their size (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`).

## Ownership partition

Slices 1-3 ran **sequentially**: Slice 2's code repair changes what Slice 3's spec reconciliation may claim (DoD item 4's forbidden-form gate), so those two are ordered, not parallel.

**One concurrent pairing is licensed, declared here before dispatch (2026-08-25):** Slice 3's remaining review/verification passes and Slice 4's full cycle may run **concurrently**, because their write sets are provably disjoint — Slice 3 writes only `docs/SPECS/**` and its own artifact; Slice 4 writes only `django_strawberry_framework/types/base.py` and its own artifact. No file is owned by both. The two touch the same *subject* (the override-validation helpers) but not the same bytes: Slice 3 corrects the spec's description of them, Slice 4 corrects the source docstrings that describe them. That is a genuine coupling of meaning, so **Slice 4's planning dispatch carries Slice 3's corrected wording as context**, and the integration pass re-checks the pair for agreement rather than assuming it.

Full mapping, for attribution if a pass is interrupted:

| Slice | Files it may write |
|---|---|
| 1 — rationale extraction | `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`, `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` (new), `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` (**added by the mid-flight re-partition below**), `docs/builder/bld-slice-1-029-rationale_extraction.md` |
| 2 — forbidden-form repair | `tests/test_relay_connection.py`, `tests/forms/test_resolvers.py`, `tests/types/test_resolvers.py`, `tests/mutations/test_write_transaction.py`, `tests/mutations/test_resolvers.py`, `examples/fakeshop/test_query/test_products_visibility_api.py`, `tests/optimizer/test_extension.py` (**added by re-partition #2**), `examples/fakeshop/strategy_schemas.py` (**added by re-partition #2**), `tests/test_ci_governance.py` (the governance pin — approved as maintainer decision D1), `docs/builder/bld-slice-2-029-extensions_forbidden_form_repair.md` |
| 3 — spec reconciliation | `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`, `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`, `docs/builder/bld-slice-3-029-spec_reconciliation.md` |
| 4 — docstring-rot repair | `django_strawberry_framework/types/base.py` (**docstrings only**), `docs/builder/bld-slice-4-029-docstring_rot_repair.md` |
| integration | `docs/builder/bld-integration-029.md` (+ spec / rationale if the pass finds a cross-slice defect) |
| final | `docs/builder/bld-final-029.md` |

## Mid-flight ownership re-partition (Worker 0, 2026-08-25)

`BUILD.md` `### Parallel cohorts under a declared ownership partition`: "If a collision surfaces mid-flight (a cohort needs to write a file it does not own), Worker 0 stops that cohort, folds the file into the owning cohort's scope or re-partitions, and records the correction in the plan."

**`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` is folded into Slice 1's ownership.** Slice 1's move relocated the string `P1.1 — stale extension-lifecycle model` — it existed only inside spec-029's revision history and now exists only inside the new `029` companion — so the `spec-004` companion's prose citation of it is broken. Worker 1 deferred it as out of fence; Worker 3 challenged that and is right on both halves:

- **It is inside the maintainer's fence.** The fence is *spec files and `.py` files only*; a `-rationale.md` is a spec-family file. The only thing that put it out of reach was this plan's own ownership table, which Worker 0 owns and is hereby correcting.
- **It belongs to the moving slice, not to a later pass.** The standing lesson from the sibling `spec-027` cycle is exactly this: *budget the post-move `#"substring"` sweep into the moving slice.* There, deferring it grew the repair cohort three times, because each pass swept only the vocabulary of the finding it was handed. Deferring one known-broken citation to an integration pass repeats that mistake with the evidence already in hand.
- **No gate can find it later.** `check_citations.py` resolves `path::Symbol` only and puts `docs/` out of scope, and this is a *prose* citation, so no link check sees it either. Unfixed now, it is invisible forever.

## Mid-flight ownership re-partition #2 (Worker 0, 2026-08-25) — B1's population was under-measured

Slice 2's planning pass re-derived finding B1 and found Worker 0's population **wrong: 25 sites in 8 files, not 12 in 6.** Worker 0 re-verified before accepting, and the correction stands.

**How the miss happened, because the shape recurs.** Worker 0 swept using DoD item 4's own vocabulary — the literal `lambda: DjangoOptimizerExtension()` — so every **keyword-carrying** variant fell outside the pattern: 13 sites spelled `lambda: DjangoOptimizerExtension(strictness=…)` or `(nested_connection_strategy=…)`. This is the standing lesson landing on the dispatcher: **a finding's grep vocabulary is not its population.** The spec's normative sentence states the rule by *form* — "Do NOT use the bare class or a constructing-`lambda`" — and the parenthetical example is one spelling of it, so the wider population was always in scope and the narrow grep simply could not see it. Worker 1's AST classifier (controlled at 18/18 on 9 must-flag and 9 must-not-flag snippets before its reading was believed) is the instrument of record; the raw greps in section B below are superseded and retained only to show what was missed.

**Two files are added to Slice 2's writable-file list**, both `.py` and therefore inside the maintainer's fence:

- `tests/optimizer/test_extension.py` — 7 constructing lambdas
- `examples/fakeshop/strategy_schemas.py` — 1 constructing lambda, plus a docstring the repair falsifies

The ownership table above is corrected accordingly. **Floor-verification scope grows with it**: the eight edited files, plus `tests/test_ci_governance.py`, plus the two readers of `examples/fakeshop/strategy_schemas.py::build_strategy_schema`.

**One scope boundary Worker 1 confirmed from source, which keeps the expansion from over-reaching:** only `DjangoOptimizerExtension` is in scope. `DjangoDebugExtension`'s own docstring *requires* the bare class and forbids a pre-built instance, and `DjangoErrorPolicyExtension`'s says bare class and factory behave identically. A sweep that flags every bare-class `extensions=` entry would break the first of those.

## Slice 4 added mid-cycle (Worker 0, 2026-08-25) — docstring rot in `types/base.py`

Slice 3's reconciliation pass surfaced two `.py` docstring defects while reading the shipped override-validation code, and correctly did **not** fix them (outside its writable surface). It routed them to the deferred catalog. **Worker 0 overrides that routing and opens Slice 4 instead**, for the same reason the `spec-004` citation was pulled back in at Slice 1: they are inside the maintainer's fence (`.py` files), they are cheap, and the cycle's stated contract is to *make sure the code is correct*.

Worker 0 confirmed both against source before opening the slice — they are measurements, not reports:

1. **`types/base.py::_selected_meta_targets` names 2 of its 3 callers.** Its docstring says "The first half shared by `_validate_nullability_override_targets` and …", naming one sibling; the function has **three** call sites (`_validate_nullability_override_targets`, `_validate_filesystem_path_targets`, `_validate_relation_shape_targets`). A docstring that enumerates callers and misses one tells the next reader a seam has fewer consumers than it does — which is precisely the reasoning that makes someone change it unsafely.
2. **`types/base.py::_validate_nullability_override_targets`'s stated check order contradicts its own loop.** The docstring says `unknown -> excluded -> (consumer-authored / relation / Relay-pk)`; the loop body runs consumer-authored → **Relay-pk** → **relation**. The parenthetical grouping softens it, but the order it lists is not the order it runs — and this same ordering discrepancy is one Slice 3 had to correct in the *spec* (divergence C4), so leaving the source copy wrong would reconcile the spec to code whose own comment still disagrees with it.

Neither is a behavior defect: no rejection rule is missing and no order change is proposed. **The fix is the comment, never the code** — reordering a live loop to match a wrong comment would be the tail wagging the dog, and `AGENTS.md` L5 (root-cause fix, no shortcuts) cuts the other way here.

**Scope discipline:** this is a two-docstring repair. It is not a licence to re-audit `types/base.py`, and any further defect found there is recorded, not fixed.

**Ownership:** `django_strawberry_framework/types/base.py` plus `docs/builder/bld-slice-4-029-docstring_rot_repair.md`. Added to the ownership table above. Sequential, after Slice 3 (which is still amending the spec text that describes this same helper).

**Obligations:** hot-path `none` (comment-only; no executable line changes). Floor verification `none` — no framework-surface behavior changes, and a docstring cannot diverge across versions. **Failability proofs `none`**: `BUILD.md` `### What needs a proof, and what does not` exempts comment and doc edits explicitly, and a proof obligation manufactured for a comment is the kind of ritual that makes the real ones unaffordable. The verification that matters is the opposite one — proving the executable bytes are **unchanged**, per `## Claims are proven mechanically, never accepted on prose` ("relocated, promoted, or carried over unchanged"): an AST or executable-token comparison against HEAD with comments and docstrings stripped, which must come back identical.

## Cross-slice conflict created by Slice 4, routed to the integration pass (Worker 0, 2026-08-25)

Slice 4's planning pass surfaced a conflict it correctly refused to fix: **once Slice 4 lands, it falsifies a parenthetical in `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` `## Decision 8`**, which says the two docstring defects are "outside this cycle's editable surface and is routed to the final gate's deferred catalog". All three clauses become untrue: they are inside the fence, they were edited by this cycle, and they are not deferred.

That file belongs to Slice 3, and Slice 4 may not write it. **The integration pass owns the correction** (Worker 1 owns both spec files there), and it is the right owner regardless of which slice closes first — Slice 3's own final verification may run before Slice 4's fix lands, in which case the parenthetical is still true when Slice 3 closes and only becomes false afterwards. That ordering is exactly why this is recorded here rather than left to whichever pass happens to notice.

**CORRECTION (Worker 0, after Slice 3's final verification): the population is ONE sentence, not two passages, and it is false NOW.** Slice 3's final verification enumerated it on three disjoint vocabularies: both clauses live in the **same trailing parenthetical at companion `:245`**, and nothing else in either file asserts it — no passage asserts the `_selected_meta_targets` defect at all, because companion `:244` already names the third caller. Worker 0's "at least two passages" framing below was itself the parallel-site error in miniature: two passes each described the same sentence from a different angle and each read the other's description as a second site. **Slice 4's bytes are already on disk**, so `:245` is false *now* rather than "once Slice 4 lands"; the integration pass still owns the fix, gated only on Slice 4's acceptance. The enumerate-don't-sweep instruction below stands — it is what produced this correction.

**The original two-site framing, kept because it is the evidence for the correction above:** companion `:245` says `_validate_nullability_override_targets`'s docstring "still lists the three per-name rules in the rev1 order" and routes it to the deferred catalog — the exact docstring Slice 4 is repairing. So Slice 4 falsifies **two** companion passages, not one.

That is the parallel-site skip again, and it is the fifth instance in this cycle. **The integration pass must therefore enumerate the population rather than fix the two sites named here** — every companion or spec passage asserting that a docstring defect is unfixed, out of fence, or deferred. Two independent passes each found one site and neither found the other's; a third pass keyed on either of their vocabularies would find only what it already knew.

**No gate catches this class** — it is prose, and `check_citations.py` is `path::Symbol`-only with `docs/` out of scope. Integration must check it by reading, not by running something.

**Related, for `bld-final-029.md`:** the deferred-work catalog must record these two docstring defects as **closed by Slice 4**, not as deferred items. A catalog entry that defers work the cycle actually did is the same false-description defect this cycle exists to repair.

## Hot-path declaration

**Slice 2 — declared hot-path-adjacent, number required.** Its whole subject is the optimizer's per-request plan-cache lifecycle. The change is confined to test-file schema construction (no production line changes), so the metric is not wall-clock: **Worker 2 records, for at least one migrated site per form, the `DjangoOptimizerExtension.cache_info()` reading before and after the migration across two executions of the same query on one schema** — the direct observation that the bare class / constructing `lambda` yields `misses=2, hits=0` (a fresh instance per request) and the singleton-factory yields `misses=1, hits=1`. That number IS the proof the repair is a repair. Slices 1, 3, integration, and final: `none` (documentation and artifacts only).

## Floor-verification scope

- **Slice 2 — required. Owning pass: Worker 2's build pass.** It touches a Strawberry integration seam (`Schema(extensions=...)` construction and the per-request `get_extensions` contract). Focused scope at the floor: the six test files it edits. Floor per `BUILD.md` `## Floor verification`: **Django 5.2.16, Python 3.10, strawberry-graphql 0.316.0**, built in a scratch venv **outside** the repo (`uv venv /tmp/dsf-floor-029 --python 3.10`; install with an explicit `--python`; never mutate the shared `.venv`). Record the resolved `uv pip list --python /tmp/dsf-floor-029/bin/python` output and each focused command's pass/fail. The floor is the version the spec's own Decision 3 was derived against, so it is the version that must confirm the repair.
- Slices 1, 3, integration: `none` (no framework surface).
- Final gate: confirms Slice 2's floor run happened and was recorded; it does not own it.

## Concurrent-session activity observed mid-cycle (out of scope, never reverted)

The tree was clean at pre-flight. During Slice 1 a concurrent session produced: `docs/review/review-0_0_14.md` (modified), `docs/review/rev-django_strawberry_framework.md`, `docs/review/rev-final.md`, `docs/review/rev-management.md`, `docs/review/rev-mutations__operations.md`, and `tests/mutations/test_operations.py` (all new). None is owned by any cohort of this plan and none collides with Slice 2's file list. Per `AGENTS.md` rule 34 they are neither edited nor reverted, and `docs/review/` is committed source of truth that must never be bulk-deleted (`AGENTS.md` rule 22). Recorded here so a later pass does not mistake them for this cycle's output. Their presence means **`git status` is not a reading of this cycle's diff** — attribute by the per-slice ownership table above.

## Maintainer decisions (escalated before dispatch, answered 2026-08-24)

Both were contract choices rather than defects, so `BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch` applies. The rejected alternatives are recorded because the next reader's first instinct will be one of them.

**D1 — Slice 2 ships the repair AND a standing governance pin (Option A).** The 12 sites are migrated to the singleton-factory form, and one assertion is added to `tests/test_ci_governance.py` asserting no active `.py` constructs a schema with `extensions=[DjangoOptimizerExtension]` or `extensions=[lambda: DjangoOptimizerExtension()]`. `tests/test_ci_governance.py` is hereby added to Slice 2's writable-file list.

- *Rejected — repair the 12 sites only.* Lost because the root cause is not the 12 sites: it is that a one-shot build-time grep left nothing standing behind the rule, and four later cards reintroduced the forms across five patch releases with nothing noticing. A rule with no gate rots, so a sites-only repair schedules the same regression again.
- *Rejected — put the gate in `scripts/` wired to pre-commit instead.* Lost on placement, not on merit: `tests/test_ci_governance.py` already exists as this repo's home for standing repo-wide pins, and a second enforcement mechanism for one rule is the duplication the DRY-first rule exists to prevent.
- *Rejected — relax the spec and declare the forbidden forms acceptable in tests.* Lost because the mechanism that makes them forbidden is **unchanged at HEAD** (re-verified against strawberry-graphql 0.323.2's `Schema.get_extensions`), so relaxing would mean writing down a reason that is false.

**D2 — Slice 3 restates Decision 10 as the current contract (divergence C1).** Decision 10, `## Non-goals`, `## Edge cases and constraints`, and the Slice-3 checklist / DoD are rewritten to the shipped scope: the overrides apply to **non-relation model fields — scalar columns and file/image output objects** — with relation targets still rejected. The spec reads as a clean current contract with no chronology; **the widening, the card that caused it, and the claim Decision 10 may no longer make are recorded in the rationale companion.**

- *Rejected — leave Decision 10 as a snapshot of what 0.0.9 shipped.* Lost against `BUILD.md` `## Spec rationale extraction`: "the spec reads as a clean current contract … a reader must never reconstruct what is currently true by applying a chronology to it." A spec that describes a scope narrower than the code enforces is a false contract, whatever its vintage.
- *Rejected — restate but name the widening card inline in the spec.* Lost for the same reason at smaller scale: an inline "later widened by card N" clause is a chronology fragment, and the rationale companion is exactly where that pointer belongs.

## Contract-level escalation to the maintainer (answered — see "Maintainer decisions" above)

`BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch` — one item is a contract choice, not a defect, and Slice 2 is dispatched **without** it. It is dispatched as a *question*, and Worker 2 must not implement it unless the maintainer answers yes.

**Should the forbidden-form gate be mechanically enforced?** Spec-029 DoD item 4 made the gate a one-shot grep run at build time. With no standing gate, four later cards reintroduced the forbidden forms at 12 sites and nothing noticed for five patch releases. The root cause of the regression is not the 12 sites; it is that **a rule with no gate rots**. The repo already carries `tests/test_ci_governance.py` as the home for exactly this kind of standing repo-wide pin.

- **Option A (recommended): add one governance assertion** to `tests/test_ci_governance.py` — no active `.py` file constructs a schema with `extensions=[DjangoOptimizerExtension]` or `extensions=[lambda: DjangoOptimizerExtension()]`. Cost: one test. Benefit: the gate stops depending on a human remembering a five-year-old spec.
- **Option B: repair the 12 sites only**, and record in the rationale that the gate is unenforced and will rot again.
- **Rejected alternative — relax the spec instead** (declare the forbidden forms acceptable in tests). Rejected because the mechanism that made them forbidden is *unchanged at HEAD* (re-verified above against strawberry 0.323.2), so relaxing would be writing down a false reason.

## Dispatch-shape deviation for the two Worker-1-owned slices (recorded, not improvised)

Slices 1 and 3 change **only the spec and its rationale companion**, and `BUILD.md` `## Spec reconciliation` makes Worker 1 the *only* worker permitted to mutate either file. There is therefore no Worker 2 pass to dispatch: a builder has nothing it is allowed to write. The load-bearing property — **the agent that produced the work is not the agent that approves it** (`BUILD.md` `### Isolation is non-waivable`) — is preserved by keeping Worker 3 in the loop. So those two slices run:

**Worker 1 (plan + perform, sets `planned`) → Worker 3 (independent review, sets `review-accepted` / `revision-needed`) → Worker 1 (final verification, sets `final-accepted`).** A `revision-needed` from Worker 3 routes back to **Worker 1**, never Worker 2 — the spec-custody rule, not the structural-drift pause.

The one departure from `## Per-slice dispatch` step 2 is that Worker 3, not Worker 2, is dispatched off `planned` for these two slices. Recorded here so a reader does not mistake it for a dropped pass. **Slice 2 runs the ordinary full cycle** (Worker 1 → Worker 2 → Worker 3 → Worker 1), because it changes `.py` source.

## Artifact list

- `docs/builder/bld-slice-1-029-rationale_extraction.md`
- `docs/builder/bld-slice-2-029-extensions_forbidden_form_repair.md`
- `docs/builder/bld-slice-3-029-spec_reconciliation.md`
- `docs/builder/bld-integration-029.md`
- `docs/builder/bld-final-029.md`

## Worker-0 pre-dispatch verification (findings handed to the cycle)

`BUILD.md` `### Worker 0 verifies every finding against source before dispatching`. Every row below was read against HEAD source on 2026-08-24 and carries its symbol-qualified path. **Each is a hypothesis for the owning worker to re-derive, never an instruction** — three of Worker 0's own findings in the sibling `028` cycle were over-broad, and applying one verbatim would have deleted a true sentence.

### A. Nothing in the code was skipped — verified before dispatch

Every contracted surface of all three slices exists at HEAD:

| Contract | Verified at |
|---|---|
| Slice 3 `Meta` keys | `django_strawberry_framework/types/base.py::ALLOWED_META_KEYS` carries `nullable_overrides` + `required_overrides`; `DEFERRED_META_KEYS` carries neither |
| Slice 3 tri-state | `django_strawberry_framework/types/converters.py::convert_scalar` takes `force_nullable: bool | None = None` and computes one `effective_null` |
| Slice 3 stage-1 shape + collision | `types/base.py::_validate_meta` normalizes both keys onto `_ValidatedMeta` and raises the both-sets collision |
| Slice 3 stage-2 targets | `types/base.py::_validate_nullability_override_targets` — all five rejection rules present (unknown / excluded / consumer-authored / relation / Relay-suppressed pk) |
| Slice 3 stage-3 apply | `types/base.py::_build_annotations` receives both frozensets and threads `force_nullable` per field |
| Slice 3 acceptance type | `examples/fakeshop/apps/library/schema.py::NullabilityOverrideBookType` (`primary = False`, `nullable_overrides = ("title",)`, `required_overrides = ("subtitle",)`); `BookType` marked `primary = True`; root resolver `all_library_nullability_override_books` |
| Slice 3 live tests | `examples/fakeshop/test_query/test_library_api.py::test_nullability_override_flips_sdl_nullability` + `::test_nullability_override_acceptance_api_is_queryable` |
| Slice 3 package tests | all six `force_nullable` cases in `tests/types/test_converters.py`; all eight validation cases in `tests/types/test_base.py` |
| Slice 2 command | `django_strawberry_framework/management/commands/inspect_django_type.py` (31KB) with `Command` / `add_arguments` / `handle` |
| Slice 2 tests | every test the spec's Test plan names exists in `examples/fakeshop/tests/test_inspect_django_type.py` and `tests/management/test_inspect_django_type.py`, including the cross-slice `test_inspect_reads_resolved_annotation_not_field_null` and `test_inspect_relay_node_pk_row` |
| Slice 1 doc + example migration | `GOAL.md`, `TODAY.md`, `examples/fakeshop/config/schema.py`, `examples/fakeshop/test_query/README.md`, `docs/README.md`, `docs/GLOSSARY.md` all carry the `_optimizer = DjangoOptimizerExtension()` + `extensions=[lambda: _optimizer]` singleton-factory form |
| Slice 1 no-warning pin | `tests/optimizer/test_extension.py` #"if issubclass(w.category, DeprecationWarning)" |
| Doc obligations | `docs/GLOSSARY.md` carries `## Meta.nullable_overrides`, `## Meta.required_overrides`, `## Schema introspection management command`; `docs/TREE.md` lists the module and both mirrored tests |

**So: no code gap.** The surface has *grown* since ship, not shrunk. The one thing that regressed is B1.

### B. Live regression against a spec-029 contract (Slice 2 owns)

**B1 — DoD item 4's forbidden-form gate is violated at HEAD by 12 live sites in 6 files.** Spec Decision 3 forbids the bare class and the constructing `lambda` because both re-instantiate per request and give the instance-bound plan cache a zero hit rate; DoD item 4 requires a zero-hit grep across active source. Enumerated (not counted — re-derive, do not trust this list's length):

```
tests/test_relay_connection.py:1497   extensions = [lambda: DjangoOptimizerExtension()] if optimizer else []
tests/test_relay_connection.py:1696   extensions = [lambda: DjangoOptimizerExtension()] if optimizer else []
tests/test_relay_connection.py:1830   extensions=[lambda: DjangoOptimizerExtension()],
tests/test_relay_connection.py:2170   extensions=[lambda: DjangoOptimizerExtension()],
tests/test_relay_connection.py:2274   extensions=[lambda: DjangoOptimizerExtension()],
tests/forms/test_resolvers.py:123     extensions=[DjangoOptimizerExtension],
tests/types/test_resolvers.py:169     extensions=[DjangoOptimizerExtension],
tests/mutations/test_write_transaction.py:180  extensions=[DjangoOptimizerExtension],
tests/mutations/test_resolvers.py:107          extensions=[DjangoOptimizerExtension],
tests/mutations/test_resolvers.py:970          extensions=[DjangoOptimizerExtension],
examples/fakeshop/test_query/test_products_visibility_api.py:160  strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension]),
examples/fakeshop/test_query/test_products_visibility_api.py:192  strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension]),
```

Mechanism re-verified at HEAD (above). **`DjangoDebugExtension` / `DjangoErrorPolicyExtension` / consumer extension classes passed bare are NOT violations** — those are stateless-per-operation by contract (spec-044 requires a fresh instance per operation), and only `DjangoOptimizerExtension` carries the shared cache. A sweep whose vocabulary is `extensions=[` alone will over-report; scope it to the optimizer.

**Do not repair by weakening a test.** Where a site holds no reference, a module- or function-local singleton wrapped in a `lambda` is the shape (spec Decision 3's per-construction-site granularity: function-local where a test asserts on the instance, module-level only where one schema serves the module). The conditional sites (`… if optimizer else []`) need the singleton constructed only on the optimizer branch — a module-level singleton would construct one for the no-optimizer parametrization too, which is a behavior change; prefer function-local.

### C. Spec-vs-HEAD divergences (Slice 3 owns; each is a claim to re-derive, then correct)

Every one of these is the spec asserting something that was true at authoring and is false or incomplete at HEAD. The **explanation** of each goes in the rationale file; the spec gets the corrected contract stated directly, with no chronology and no amendment block.

1. **Scope widened past "scalar-only".** Decision 10, Non-goals, Edge cases, and the Slice-3 checklist all say the overrides apply to *scalar columns only*. At HEAD the shipped error text is `types/base.py` #"(scalar columns and file/image output objects)" and `converters.py::convert_field_output` accepts `force_nullable`, so `required_overrides` opts a `FileField` / `ImageField` read object into a non-null `DjangoFileType!` — a capability `docs/README.md` already documents. Later work (the file/image output card) widened the scope. The `is_relation` rejection is unchanged.
2. **The apply call site is no longer `convert_scalar`.** Decision 7, DoD item 11, and the Slice-3 checklist say `_build_annotations`'s scalar branch calls `convert_scalar(...)`. At HEAD it calls `types/converters.py::convert_field_output`, which routes file/image columns to the structured output object and delegates every other column to `convert_scalar`, threading `force_nullable` through both.
3. **Three `#"substring"` citations are broken** — they resolve to **zero** occurrences at HEAD (re-derive each with `grep -cF`, and mind the wrap hazard: a citation split across two lines is invisible to a single-line grep):
   - `[base] #"Meta.exclude must be a non-string sequence"` — the shape check is now the shared `types/base.py::_normalize_sequence_spec`.
   - `[base] #"annotations[field.name] = convert_scalar(field, cls.__name__)"` — superseded by divergence 2.
   - `[test-extension] #"extensions=[_CaptureExt()]"` — the `_CaptureExt` sites were migrated by Slice 1 itself, so the spec's own Current-state citation was retired by its own build. (`[base] #"suppress_pk_annotation"` and both `[agents]` citations still resolve.)
4. **Helper names.** Current state (`#### Current state`, the `_validate_filterset_class` bullet) still calls the planned helper `_validate_nullability_overrides`; the shipped name — which Decision 8 and DoD 11 already use — is `_validate_nullability_override_targets`. Its signature is keyword-only and takes `relay_shaped: bool`, not a `relay_pk_name`. Its unknown/excluded split is delegated to the shared `types/base.py::_selected_meta_targets` + `_format_unknown_fields_error`, shared with `Meta.filesystem_path_fields` and `Meta.relation_shapes` — a DRY consolidation that arrived after ship and that the spec's "structural template is `_validate_filterset_class`" framing no longer describes. The shipped check order is unknown → excluded → consumer-authored → Relay-pk → relation; Decision 8 lists relation before Relay-pk.
5. **DoD item 1's CSV claim is now false.** It states the three net-new symbols are "intentionally NOT in the CSV … honestly incomplete". At HEAD `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv` carries `Meta.nullable_overrides`, `Meta.required_overrides`, and `Schema introspection management command`, and `check_spec_glossary` reports `OK: 44 terms`. The deferral the item describes was discharged.
6. **DoD item 4's forbidden-form claim** must be reconciled against whatever Slice 2 actually lands (and against the maintainer's answer on the governance pin).
7. **Slice 2's shipped surface is materially larger than Decision 4 describes.** Not a defect — later cards extended it — but the spec under-describes what exists. At minimum: `Meta.name` / SDL-name resolution (`test_inspect_by_meta_name`, `test_bare_name_resolves_meta_name_and_title_uses_graphql_name`, the `Meta.name`-vs-Python-name ambiguity branch); file-output converter rows; multi-member union rendering; connection-only relation shapes; unresolved-forward-ref rejection; custom scalar / named-union scalar naming. Re-derive the list from the two test modules; do not copy this one.
8. **Both loaders now route through the shared `_imports.py` helpers.** Decision 4 pins `django.utils.module_loading.import_string` for the dotted type argument and Strawberry's `import_module_symbol` for `--schema`. At HEAD `inspect_django_type.py` calls `_imports.py::import_string_or_command_error` and `_imports.py::import_module_symbol_or_command_error`, which add a shared absolute-module-path rejection (`_imports.py::_validate_absolute_module_path`) neither loader had at ship. The dispatch-by-shape contract itself is intact.
9. **Current-state census figures are stale.** `tests/optimizer/test_extension.py` now holds far more `extensions=[` entries than the spec's 41, and the "48 entries across five package test files" total is history. `## Current state` is explicitly framed as "the repo as of this spec's authoring, before the build", so these may legitimately stand as-is — but a *completion* claim (DoD, Slice checklist) that repeats a stale number may not. Worker 1 decides per site; whichever way it goes, say why in the rationale.

### D. Outside the fence — route to the deferred catalog, do not fix

- `KANBAN.md`'s `DONE-029` card body still names the **rejected** migration targets (`extensions=[DjangoOptimizerExtension]` class / `lambda: DjangoOptimizerExtension()` factory) as Slice 1's goal, and still names the non-existent `examples/fakeshop/tests/test_commands.py` as Slice 2's test home. Both were resolved *against* the card by Decisions 3 and 4. DB-backed (`KANBAN.md` is rendered from `examples/fakeshop/db.sqlite3`); out of fence.
- `KANBAN.md:366` already carries an open, unrelated item against `docs/GLOSSARY.md`'s `## Schema introspection management command` entry (it owes three selector rejections, not two), filed by the `spec-022` residual cycle. Note it in the catalog so this cycle is not read as having missed it; do not duplicate the filing.

## Checklist

- [x] Slice 1: Rationale extraction — create `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` by MOVING the spec's deliberative layer -> `docs/builder/bld-slice-1-029-rationale_extraction.md`
- [x] Slice 2: Forbidden-form regression repair — migrate the 25 live sites (12 was Worker 0's under-measured figure; see re-partition #2) to the singleton-factory form -> `docs/builder/bld-slice-2-029-extensions_forbidden_form_repair.md`
- [x] Slice 3: Spec reconciliation with HEAD — every divergence in section C, corrected in the spec, explained in the rationale -> `docs/builder/bld-slice-3-029-spec_reconciliation.md`
- [x] Slice 4: Docstring-rot repair in `types/base.py` — two confirmed false docstring claims about live behavior -> `docs/builder/bld-slice-4-029-docstring_rot_repair.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration-029.md`
- [x] Final test-run gate -> `docs/builder/bld-final-029.md`
