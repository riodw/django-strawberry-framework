# Build: R4 — rationale correction (integration finding I1, the shipped-not-deferred edge memo)

Spec reference: `docs/SPECS/spec-034-permissions-0_0_10.md` — **not edited by this round.**
Rationale companion: `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` (the round's only writable spec-family file)
Build plan: `docs/builder/build-034-permissions-0_0_10.md`
Input: `docs/builder/bld-034-integration.md` `### Finding I1` + `### What Worker 0 must decide` (option (b) taken)
Status: final-accepted

**Pass shape.** This round lands **no source and no test**. Per `docs/builder/BUILD.md` `### Procedural-closure slices` it carries one combined `## Plan (Worker 1)` + `## Final verification (Worker 1)` block; `## Build report (Worker 2)` and `## Review (Worker 3)` are marked not-applicable with that reason.

---

## Plan (Worker 1) + Final verification (Worker 1)

### Spec status-line re-verification (this spawn)

Read `docs/SPECS/spec-034-permissions-0_0_10.md` lines 1-9 end to end — title, the `Shipped in 0.0.10` identity paragraph, `Status:`, `Owner:`, `Predecessors:`, and the rationale-companion pointer paragraph. **Nothing this round does falsifies any of them, and no header edit is owed or made.** The `Status:` line still reads SHIPPED (`0.0.10`) with all five slices final-accepted; the companion pointer paragraph still describes the file this round appends to. The integration pass re-verified the same lines one pass earlier and R2 had already removed the two stale clauses; nothing has moved since.

### Dispatched findings checklist

- [x] **I1 (SUPERSEDED, Low)** — *"the per-model edge memo shipped, and three deliberation sites still call it unshipped."* At `HEAD` `django_strawberry_framework/permissions.py::_edge_plan` is `@lru_cache(maxsize=1024)` over `model._meta.get_fields()`, shared by `fields=` validation, the unsupported-edge preflight and the walk. Three sites in the rationale companion describe that as not shipped: `## Risks and open questions` → **Cascade-call overhead on hot paths** (its per-call cost premise, and its fallback's "deferred per the measure-first discipline"), and `## Decision 5` → `### Alternatives considered (and rejected)` alternative 4 (*"a cache layer with invalidation semantics. Measure first."*). **The spec is clean and is not touched** (`docs/builder/bld-034-integration.md` `### Finding I1`).

### The finding re-derived at source, not read off the integration artifact

`BUILD.md` `## Claims are proven mechanically, never accepted on prose`: the inherited claim was re-measured here before anything was written.

```shell
$ grep -n '_edge_plan' django_strawberry_framework/permissions.py
191:    ``_edge_plan`` built from this predicate, so scope cannot drift.
228:def _edge_plan(model: type[models.Model]) -> _EdgePlan:
250:    return _edge_plan(model).cascadable
304:    plan = _edge_plan(model)
629:    plan = _edge_plan(model)
689:    for field in _edge_plan(model).cascadable:
```

`permissions.py::_edge_plan` is decorated `@lru_cache(maxsize=1024)`; its body loops `model._meta.get_fields()` once and returns an `_EdgePlan(cascadable=..., unsupported=...)`. Its three production readers are `_validate_fields` (`:304`), `apply_cascade_permissions`'s preflight (`:629`) and `_walk` (`:689`). So the `get_fields()` loop runs **once per model**, and what runs per call is set ops over the cached plan.

**Attribution measured, not assumed** — and it is not the commit the integration pass implied:

```shell
$ git log --oneline -S'_edge_plan' -- django_strawberry_framework/permissions.py
c68aecab feat(permissions): harden cascade visibility graph, fail-closed on every SQL boundary

$ git log --oneline -S'lru_cache' -- django_strawberry_framework/permissions.py
bc1a6aaf feat: add caching to _path_traverses_to_many and _cascadable_edges functions for improved performance

$ git merge-base --is-ancestor bc1a6aaf c68aecab && echo ancestor
ancestor
```

`bc1a6aaf` (2026-06-15) is where the memo actually shipped — it put `@lru_cache(maxsize=1024)` on a new `_cascadable_edges(model)` and rewrote `_walk` to iterate it instead of re-scanning `get_fields()`. `c68aecab` (2026-07-16) widened that memo into `_edge_plan` so the unsupported-edge preflight could share the same metadata slice. Naming only `c68aecab` would have been wrong by a month and would have missed the sharpest fact in the record: **`bc1a6aaf` landed the same day as the card's final review revision (Revision 8, 2026-06-15)**, so the fallback was already false when the spec closed, not four releases later.

### Judgement applied per site, and why the three are not one edit

`worker-1.md` `### Performing the rationale move` rule 2 — *delete, do not preserve, prose the current implementation has falsified* — governs, but the three sites are three different kinds of wrong and take three different treatments.

| Site | Kind of wrong | Treatment |
|---|---|---|
| Risks item's cost premise (*"one `get_fields()` loop plus set ops"* per call) | A **cost claim the implementation falsified**. Nothing about it is worth preserving as history: it is simply not what the code costs. | **Corrected in place.** |
| Risks item's fallback (*"deferred per the measure-first discipline"*) | A **fallback described as deferred that in fact shipped**, in a different key. | **Corrected in place**, stating that the edges half shipped, naming `_edge_plan`, and keeping the two clauses that are still true. |
| Decision 5 rejected alternative 4 | A **rejected alternative later adopted.** That it was once rejected, and what changed, is exactly what a rationale file exists to carry. | **Text left byte-identical; a `**Post-ship:**` bullet appended** under `### Changes this Decision underwent`. |

**The precedent was read before the shape was chosen, not after.** Decision 5 already holds one re-adopted alternative in this same position — *"Calling every target's `get_queryset` unconditionally (upstream behavior)"*, rejected on dead-SQL grounds and re-adopted by `c68aecab`. Its rejected-alternative bullet was **not** edited; the record is a `**Post-ship:**` bullet that names the re-adoption, then states the counter-argument the original deliberation never reached (*"the gate is a visibility decision wearing an optimization's clothes"*). This round matches that shape rather than inventing one: name the adoption, then say precisely which premise of the rejection gave way and which still stands.

The same read settled where the Risks correction is *recorded*. Risks-item corrections are already homed under `## Non-Decision deliberation` — the last three bullets there correct the **Live-suite sensitivity** item — and the Risks preamble itself carries a sentence counting them. So a Risks in-place correction owes a bullet there **and** an update to that preamble sentence, which is the half a patch-shaped edit would have left stale.

Nine other `**Post-ship:**` bullets were read for voice before writing (Decisions 3, 5 x3, 7 x2, 8 x2, 9, and the six under `## Non-Decision deliberation`). The house shape is: a bolded lead clause stating what went wrong in the record, the shipped fact with its symbol path and commit, then what the original reasoning still gets right.

### Edits made — four, all in the rationale companion

Recorded in full under `### Spec changes made (Worker 1 only)` below.

### Verification — every command run in this pass, output quoted as produced

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-034-permissions-0_0_10.md
OK: 42 terms - all have glossary entries and at least one spec link.
# exit 0

$ uv run python scripts/check_citations.py --check
OK: 857 citations resolve (738 in 431 .py files, 119 in KANBAN.md).
# exit 0

$ uv run python scripts/check_trailing_commas.py --check
# no output, exit 0   (link-def scaffold + layout gate, whole tree)
```

Anchors and reference definitions, both files, both directions, re-derived with GitHub's actual slug rule (lowercase, punctuation dropped, **each** space one hyphen — an em-dash heading therefore yields `--`, which a whitespace-collapsing slugger gets wrong and which my own first audit in this cycle got wrong):

```text
--- docs/SPECS/spec-034-permissions-0_0_10.md
  refs used: 96 | definitions: 96 | unused: []
  unresolved: 0
--- docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md
  refs used: 51 | definitions: 51 | unused: []
  unresolved: 0
TOTAL unresolved: 0
```

Three link classes were checked, not one: inline in-page `](#anchor)` against the file's own headings; every reference definition carrying a `#fragment` against the target file's headings on disk; and every `[text][ref-id]` use against the definition block, plus the reverse (no orphan definition). **96/96 and 51/51 with zero unused** matches R2's recorded parity exactly, so the two definitions this round newly *uses* (`[permissions]`, `[spec-034-d9]`) were already defined and no definition was orphaned.

The spec's zero-narration baseline, re-measured **after** the edits because the round writes into the file the history lives in and a leak would land in the spec:

```text
Post-ship        0
post-ship        0
Revision         0
as of review     0
later changed    0
amendment        0
```

**The spec was not written to.** `docs/SPECS/spec-034-permissions-0_0_10.md` is 130,222 bytes / 656 lines with an mtime of `2026-08-28 02:43:55`, which is R3's final-verification pass — an hour before this round's first tool call and before the integration pass, which also wrote nothing to it. Its size reconciles: R2 recorded 128,905 / 655 and R3 recorded one Test-plan edit replacing one bullet with two, which is the +1,317 / +1.

Companion: 93,722 bytes / 434 lines before, **97,720 / 436 after** — `+3,998 / +2`. The two new lines are the two appended bullets; the other ~250 bytes are the two in-place corrections and the preamble sentence.

**No `pytest` was run and none is owed.** This round changes no executable byte; the focused runs belong to R3 and the full sweep to the final gate. No `--cov*` flag was used anywhere.

### Final status

`final-accepted`. The one dispatched finding is discharged at all three sites, the spec is untouched and still narration-free, and every gate the plan names re-runs clean at the figures R2 recorded.

### Spec changes made (Worker 1 only)

**No edit to `docs/SPECS/spec-034-permissions-0_0_10.md`.** Four edited locations in `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`, all discharging I1, listed as five rows because rows 2 and 3 are opposite operations inside one contiguous rewrite.

| # | Section | Change | Reason |
|---|---|---|---|
| 1 | `## Risks and open questions`, preamble | *"It moved verbatim and was corrected once afterwards, in the **Live-suite sensitivity** item's resolution paragraph … the last **three** bullets"* → *"has been corrected twice since"*, naming both items, → *"the last **four** bullets"*. | The preamble counts the corrections the body has taken. Edit 2 makes it a second correction and edit 4 a fourth bullet; leaving it would have been a false count generated by this very round. |
| 2 | `## Risks and open questions` → **Cascade-call overhead on hot paths** | Cost premise *"The work is one `get_fields()` loop plus set ops"* → *"The per-call work is set ops over the model's cached edge plan; the `get_fields()` loop that builds that plan runs once per model, not once per call ([`permissions.py::_edge_plan`][permissions])"*. Fallback's *"deferred per the measure-first discipline"* → *"**The edges half shipped**, keyed per model rather than per `(model, fields)`"*, naming `_edge_plan` and what it is shared by. | Rule 2: prose the implementation falsified is corrected, not preserved. Both clauses were false at `HEAD`. |
| 3 | Same item, two clauses **kept and made explicit** rather than deleted | Added: the querysets half *"did not and cannot: hook outcomes are request-scoped"*, and the per-`(model, fields)` keying *"is still the one that would absorb the `fields=` validation's own per-call set diff, and that diff still runs"*. | Load-bearing, and the reason a whole-item deletion would have been the wrong fix. The **spec's** Decision 9 closing paragraph points *into* this fallback (*"would be absorbed for free by the per-`(model, fields)` edge-list memo recorded as the Risks overhead fallback"*) and is still true — the shipped memo is keyed per model and absorbs nothing of the `fields=` diff. Dropping the per-`(model, fields)` phrasing would have semantically dangled that pointer while every link checker still read clean. |
| 4 | `## Decision 5` → `### Changes this Decision underwent`, appended | New bullet led `**Post-ship (`bc1a6aaf`, reshaped by `c68aecab`) — a second recorded rejected alternative was adopted, in the lazy form its objection did not weigh.**` The rejected alternative *"A finalize-time precomputed cascade plan per type"* was adopted in lazy form. States which premise held (**finalize-time** — the plan is built on first use, so no type-construction step knows about it) and which dissolved (**invalidation** — the cached value is model metadata, frozen after app loading; the cap only bounds synthetic test models; eviction is correctness-neutral, all three stated in the helper's own docstring), and what the rejection correctly protected and still protects (`fields=` and hook outcomes are not cached). | Matches the precedent set by this Decision's other re-adopted alternative. The rejected-alternative bullet itself is **byte-identical** — a rejection later adopted is the record, not the error. |
| 5 | `## Non-Decision deliberation`, appended | New `**Post-ship:**` bullet recording edit 2, naming `permissions.py::_edge_plan` and the falsified clauses, stating what the item still gets right, and why it belongs to no single Decision (the memo is Decision 5's alternative arriving; the cost premise is the Risks item's). | Where every prior Risks-item correction is homed — the three bullets correcting **Live-suite sensitivity** sit in exactly this position. |

(Edits 2 and 3 are one contiguous rewrite of one bullet, listed apart because they are opposite operations: 2 removes falsified prose, 3 preserves prose a coarser fix would have removed with it.)

**Why the spec needed no companion edit.** The integration pass's claim was re-derived here rather than accepted: `grep -nE 'get_fields|per call|per-call|memo|cach'` over the spec returns the Decision 5 step-1 scope predicate (`model._meta.get_fields()` as the edge source — still exactly right), Decision 9's *"The check is a set comparison per call"* closing paragraph (still true; `_validate_fields` does the set diff on every call), and plan-cache prose belonging to the optimizer. **The spec asserts a per-call `get_fields()` loop nowhere.** The stale sentences were the deliberative ones, which Slice 0 had already moved out — which is precisely why R1a graded the code CONFORMS and R2 saw nothing to reconcile.

---

## Build report (Worker 2)

Not applicable. `docs/builder/BUILD.md` `### Procedural-closure slices`: this round lands no source and no tests. There is no `### Files touched` beyond this artifact and the rationale companion, no `### Failability proofs` (no boundary introduced), no `### Hot-path budget` (the plan declares none for every pass after R1 and no executable byte changes), and no `### Floor verification` (R3's builder pass owns the cycle's one floor run; the final gate is its backstop). No `ruff` run was owed and none was made — the round touches no `.py` file.

---

## Review (Worker 3)

Not applicable, same reason. `docs/builder/BUILD.md` `### Isolation is non-waivable` binds the builder/reviewer pair over a **source diff**; there is none. What stands in place of a second reader is that every claim above is re-runnable from the quoted commands, and that the finding itself was re-derived at source rather than inherited from the artifact that raised it — which is how the attribution error (`c68aecab` alone, rather than `bc1a6aaf` reshaped by `c68aecab`) was caught.

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
