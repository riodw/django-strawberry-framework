# Package build plan: stale_placeholder_cleanup / 0.0.4 (011) — residual-completion cycle

Spec source: `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` (already archived; card `DONE-011-0.0.4`)
Rationale companion: `docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md` — **does not exist**; creating it is this cycle's first obligation.
Terms companion: `docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-terms.csv` (exists, 2 rows, one row per anchor, `check_spec_glossary` green).
Target release: `0.0.4` (shipped; this cycle bumps no version and lands no feature).
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential items. R1 and R2 both write the spec file, so they could not run concurrently even if the rest were disjoint.
Hot-path declaration: none. Both items write Markdown only; no package source and no test is in any item's writable set.
Floor-verification scope: **none.** No item touches a Django / Strawberry / channels integration seam — no item touches executable code at all.
Pre-flight: passed on 2026-08-15 with two recorded deviations (steps 3 and 5, below); baseline: **dirty with concurrent sessions' work — 95 paths, none of them this cycle's**; cleanup: **nothing deleted or cleared** (deviation, below); memory files namespaced per cycle.

## Why this cycle exists

Card `DONE-011-0.0.4` shipped at `0.0.4`, so the code is not in question as *new* work. Three obligations, in the maintainer's framing:

1. **Nothing was skipped in the code.** Everything spec-011 promised must be present at `HEAD`, and anything promised and never delivered is a defect this cycle fixes.
2. **Later work that changed the shipped shape is legitimate — but the spec must say so.** Where a later card corrected, superseded, or completed something spec-011 owns, the spec is rewritten to state the **current** contract directly. It never narrates the change (`docs/builder/BUILD.md` `## Spec rationale extraction`).
3. **The explanation goes in the rationale, not the spec.** What changed, why, which card caused it, and what the spec may no longer claim — all of it lands in the rationale companion, keyed to the spec section it belongs to.

Spec-011 is a **card-snapshot stub**: 1,797 bytes, no Decisions, no slice checklist, no rationale companion at all. So obligation 3 here is a creation, not a completion, and obligation 2 is mostly a matter of dispositioning claims that a raw Kanban render dumped into the file.

## Worker-0 verification pass (performed before any dispatch)

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`. Every finding below was read against `HEAD` (`054de9dd`) before this plan was written; each cites its symbol-qualified path (`AGENTS.md` rule 27) or its commit. A finding is dispatched only if it holds.

### What the card actually did — recovered from history, because the stub does not say

The stub's `## Scope` says "replaced stale M2M and forward-reference skips with definition-order tests" and names no skip. The work landed in `118f71a1` (`Complete spec-foundation.md - Slices 7-12 (v0.0.4)`), alongside spec-010's slices. Exactly **three** skipped placeholders were retired there, and exactly **one** was deliberately kept:

| Retired placeholder | Its skip reason at `118f71a1~1` |
|---|---|
| `tests/optimizer/test_extension.py::test_optimizer_applies_prefetch_related_for_m2m` | `"Slice 4+: M2M relation — fakeshop has no M2M field; deferred."` (an empty `pass` body) |
| `tests/types/test_base.py::test_relation_m2m_returns_list` | `"Slice 3+: M2M relation — fakeshop has no M2M field; deferred."` (an empty `pass` body) |
| `tests/types/test_base.py::test_forward_reference_resolves_when_target_defined_later` | `"Slice 3+: forward-reference / definition-order independence. The current implementation requires targets to be registered first; lazy_ref is pending."` |

| Kept placeholder | Why, and what closed it |
|---|---|
| `tests/types/test_base.py::test_consumer_annotation_overrides_synthesized` | Kept because its subject is scalar-override semantics, not definition order — the stub's second `## Scope` bullet. Retired at `0.0.6` by `a357c68c` (card `DONE-019-0.0.6`), which replaced it with `tests/types/test_definition_order.py::test_annotation_only_scalar_field_override_wins_over_synthesized` and six siblings. |

The same commit also deleted the two staged anchors that named the pending work — a `.. todo:: spec-foundation 0.0.4` module-docstring block and a `# TODO(spec-foundation 0.0.4): DELETE this skipped placeholder` comment. `grep -rn "spec-foundation"` over the tree returns **zero** hits outside `docs/builder/DONE/`, so no anchor from this card survives.

### V1-V5: nothing was skipped in the code — verified, not assumed

| # | Claim to verify | At `HEAD` | Evidence |
|---|---|---|---|
| V1 | the three placeholders are gone | gone | none of the three symbols exists anywhere in the tree; `grep -rE "pytest\.mark\.(skip\|xfail)"` over `tests/types/` and `tests/optimizer/` returns **zero** matches |
| V2 | M2M (forward + reverse) is covered by a definition-order test | covered | `tests/types/test_definition_order.py::test_many_to_many_forward_and_reverse_relations_resolve` |
| V3 | forward references / definition-order independence are covered | covered | `tests/types/test_definition_order.py::test_reverse_fk_resolves_when_parent_declared_before_child`, `::test_same_module_string_forward_reference_annotation_survives_finalization`, `::test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class` |
| V4 | the retired **optimizer** M2M placeholder's intent (M2M plans a prefetch) is discharged, not merely deleted | discharged | `tests/optimizer/test_definition_order.py::test_plan_relation_decisions_match_cardinality_after_finalization` asserts `plan_relation(Book.genres, GenreType) == ("prefetch", "default")` and the reverse `Genre.books` likewise, against the **real** managed `library` models card `DONE-013-0.0.4` later introduced |
| V5 | the deliberately-kept scalar-override skip was closed and not forgotten | closed at `0.0.6` | `a357c68c`; the replacement tests are listed above |

**No code defect was found. No source or test file is in any item's writable set, so no Worker 2 pass is dispatched** — which is the disposition the maintainer's dispatch instruction anticipated.

### R1 findings — the spec's own text

Each is a stub-shaped defect or a claim later work falsified. None is a code defect.

| # | Finding | Evidence |
|---|---|---|
| F1 | No rationale companion exists. `docs/builder/BUILD.md` `## Spec rationale extraction` makes it the first substantive action of a build; specs 001-010 all have one. | `ls docs/SPECS/appx/spec-011-*` returns only the terms CSV |
| F2 | The preamble paragraph ("This file is intentionally lightweight… Before implementation work starts from this file, expand it into the full builder-format spec") is deliberation about the file, and its instruction is **counterfactual** at `HEAD`: implementation shipped ten minor versions ago and no expansion preceded it. | spec-011 line 7 |
| F3 | `## Planning note` carries the single word `shipped` — a raw Kanban `planning_note` column render, not contract. | spec-011 lines 18-20 |
| F4 | `## Other` is an undifferentiated dump of four heterogeneous Kanban rows — a "why it matters" note, a restated scope bullet, three file paths, and a bare card id — under a heading that names none of them. | spec-011 lines 27-34 |
| F5 | `## Card snapshot` restates board fields (labels, priority, relative size) that belong to the Kanban DB and are rendered into `KANBAN.md`. Spec-007's reconciled shape draws this line explicitly. | spec-011 lines 9-16 vs. `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` `## Card snapshot` |
| F6 | `## Scope` bullet 2 — "**Kept** the remaining scalar override skip documented as a separate scalar-field concern under `DONE-019-0.0.6`" — is written in a tense that no longer holds: the skip was retired at `0.0.6`, so the spec claims a placeholder still stands. | V5 above |
| F7 | `## Scope` bullet 1 names no skip, so the spec cannot be checked against the tree without recovering `118f71a1` from history. The retired set is finite (three) and nameable. | the history table above |
| F8 | The `[backlog]` link definition is unused (one occurrence in the file — the definition itself). | `grep -c "\[backlog\]"` -> 1 |

**F8 is recorded, not dispatched.** Fifteen archived stubs carry the same unused definition; `worker-0.md` `## Closing out a kanban card` forbids partial-fixing a pattern that spans surfaces. It goes to the deferred-work catalog.

### R2 findings — documentation completion and archive audit

| # | Finding | Evidence |
|---|---|---|
| F9 | The spec is already at `docs/SPECS/` and every link definition resolves at that depth (`../../KANBAN.md`, `../GLOSSARY.md#…`), and the file is already reference-style with all ten canonical group headers. The archive move itself is therefore **done**; what R2 owes is the audit and the new companion's own link hygiene. | verified by path check; `uv run python scripts/check_spec_glossary.py --spec …` -> `OK: 2 terms` |
| F10 | The two glossary anchors the card links resolve and carry the right shipped versions: `#definition-order-independence` (`0.0.4`), `#scalar-field-override-semantics` (`0.0.6`). `KANBAN.md`'s `DONE-011-0.0.4` card renders both. | `docs/GLOSSARY.md` lines 113 / 208; `KANBAN.md` `### [DONE-011-0.0.4 …]` |
| F11 | **A `[spec-011]` ref-id cluster points at two different files across the repository.** `docs/SPECS/spec-020-…`, `spec-027-…`, and `KANBAN.md` define `[spec-011]: …spec-015-relay_interfaces-0_0_5.md` and their prose says "spec-011 Decision 9" meaning what is now spec-015 — pre-renumber vocabulary. `docs/SPECS/spec-032-full_relay-0_0_9.md` defines `[spec-011]: spec-011-stale_placeholder_cleanup-0_0_4.md` and attributes Relay-interface rejection to it, which this card never touched. | the five files named |

**F11 is recorded, not dispatched.** It spans five surfaces, one of them DB-generated (`KANBAN.md`), and correcting only the one file this cycle owns would leave the cluster *divergently* wrong rather than uniformly wrong — the exact disposition `worker-0.md` prescribes. It goes to the deferred-work catalog as a maintainer / next-spec-author item.

## Baseline-dirty out-of-scope files

`HEAD` at plan time: `054de9dd37a2c4181fb2a91ded57f4823a1b5220`. `git status --porcelain | wc -l` -> **95**, and **not one of them is this cycle's**. Every path belongs to a concurrent maintainer session (`START.md` `## Concurrent sessions`, `AGENTS.md` rule 34). **No worker edits, reverts, stages, or `git checkout`s any of them.** In particular:

- `docs/SPECS/spec-009-…md`, `docs/SPECS/spec-010-…md` and both their `appx/` rationale companions are **modified right now** by two concurrent residual-completion cycles (`docs/builder/build-009-…md`, `docs/builder/build-010-…md`, both untracked). No worker of this cycle opens any of the four for writing, and reads them only as shape precedent, never as authority on a moving claim.
- `tests/types/test_definition_order.py` is modified by the spec-010 cycle (its R2 item is adding a `strawberry.lazy` relation-override test). This cycle **reads** it for verification and never writes it. The V2/V3 evidence above was read at plan time; a pass that needs it re-derives it.
- 22 modified package sources, ~20 modified tests, and the `docs/review/` + `docs/dry/` scratchpads of an in-flight `0.0.14` review cycle. `AGENTS.md` rule 22 forbids touching `docs/review/` regardless.

**The list is moving** — it grew from 47 to 95 paths between this cycle's start and this plan. Any pass that needs the baseline re-derives it rather than quoting this section.

## Pre-flight deviations, recorded

Two steps of `worker-0.md` `## Pre-flight procedure` did not run as written; both deviations protect concurrent sessions.

- **Step 3 (artifact reset).** **Nothing was deleted.** `docs/builder/bld-003-final.md` is the committed record of a closed cycle, and `build-009-…md` / `build-010-…md` / `bld-009-*` / `bld-010-*` are two concurrent sessions' live plans and artifacts. Deleting a prior cycle's record is the one irreversible pre-flight mistake that step names; deleting a live concurrent plan would be worse. What the step protects — that this cycle overwrites no existing path — was verified directly: every path in `## Artifact list` was confirmed absent, as was the rationale companion.
- **Step 5 (scratch directories cleared).** **Nothing was cleared.** `docs/builder/worker-memory/` holds four files a concurrent session wrote minutes ago (`spec-009-worker-1.md`, `worker-1.md`, `worker-2.md`, `worker-0.md`), and `docs/shadow/` is that session's review substrate. Clearing either would destroy live work. This cycle instead uses **namespaced** memory files — `docs/builder/worker-memory/spec-011-worker-0.md` and `…/spec-011-worker-1.md` — following the `spec-009-worker-1.md` precedent the concurrent session set. No worker of this cycle reads or writes any other file in that directory.

Steps 1, 2, 4, 6 ran: the baseline is enumerated above and included per the maintainer's knowing dispatch onto this tree; `scripts/review_inspect.py` smoke-invoked OK; `.gitignore` carries all three scratch paths; `check_spec_glossary --spec docs/SPECS/spec-011-…md` exits 0. Step 7 (rationale extraction) is item R1.

## Artifact list

- `docs/builder/bld-011-r1-rationale_and_spec_reconciliation.md`
- `docs/builder/bld-011-r2-doc_completion_archive_audit.md`
- `docs/builder/bld-011-r3-kanban_card_body.md` (added mid-cycle — see `### R3, added after R2`)
- `docs/builder/bld-011-final.md`

**No `bld-integration.md`.** `docs/builder/BUILD.md` `## Cross-slice integration pass` scans landed source for cross-slice duplication; this cycle lands no source at all, so there is no cross-slice DRY surface. Both of the pass's live obligations are folded into the final gate and recorded there: the staged-anchor sweep, and the read of every closed artifact. Same disposition, and the same reason, as the spec-003 and spec-010 cycles.

### R3, added after R2

R2 reported — rather than made, correctly — a **generated-doc** defect its audit found: the `DONE-011-0.0.4` card body rendered into `KANBAN.md` / `KANBAN.html` still carries finding F6 live. Its `#### Scope` bullet 2 is the "Kept the remaining scalar override skip…" tense R1 removed from the spec (the skip was retired at `0.0.6`), it re-renders in `#### Card references`, and `#### Scope` additionally carries a duplicate row (bullet 3 restates bullet 1). `KANBAN.md` and `KANBAN.html` are rendered from the kanban tables in `examples/fakeshop/db.sqlite3`, so the fix is an ORM edit plus a regenerate — never a hand-edit — which is a Worker 2 job. `docs/GLOSSARY.md` needs no edit, and R2 verified the terms CSV is importable.

Worker 0 re-partitioned on the disposition this plan's `## Dispatch record` already declared for R2. **Concurrency check performed before dispatch:** `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are all **clean at `HEAD`** and the DB file was last written at 15:57, before this cycle opened — so no concurrent session has an unlanded card edit that a regenerate would publish (`START.md` `## Concurrent sessions`). R3 is the cycle's only item that writes anything outside `docs/`, so it runs the full worker cycle: `### Isolation is non-waivable` binds it and the agent that writes it does not approve it.

## Checklist

- [x] R1: create the rationale companion and reconcile the spec against `HEAD` (F1-F8) -> `docs/builder/bld-011-r1-rationale_and_spec_reconciliation.md`
- [x] R2: documentation completion and archive audit (F9-F11) -> `docs/builder/bld-011-r2-doc_completion_archive_audit.md`
- [x] R3: correct the `DONE-011-0.0.4` card body in the kanban DB and regenerate -> `docs/builder/bld-011-r3-kanban_card_body.md`
- [x] Final test-run gate -> `docs/builder/bld-011-final.md`

## Corrections to this plan, recorded

Two figures in `## Worker-0 verification pass` did not reproduce when R1 and R2 measured them, and both are corrected here rather than left standing (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` — a stated count reads as measured and propagates silently):

- **F8's "fifteen archived stubs"** — the real count of archived specs carrying an unused `[backlog]` definition is **8**, measured by R1 and re-verified by R2. The finding's disposition is unchanged: still a cross-surface pattern, still not partial-fixed here.
- **`a357c68c`'s replacement siblings** — the `### What the card actually did` table said "six siblings"; the commit adds **18** `def test_` lines to `tests/types/test_definition_order.py`. R1 measured it.

R2 also widened F11 materially: the `[spec-011]` ref-id ambiguity is **43 standing occurrences across 13 files**, not the five surfaces this plan named, and it reaches package source (`types/base.py`, `types/resolvers.py`) and tests. Two files link this card while meaning spec-015 — `spec-032-full_relay-0_0_9.md` (named here) and `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` (not named here). Disposition unchanged: measured, catalogued, not partial-fixed.

## Dispatch record

| Item | Passes dispatched | Why |
|---|---|---|
| R1 | Worker 1 only | The maintainer's standing instruction for this cycle: an item that changes only the spec and its rationale is Worker 1's alone, and both files are Worker 1-owned by `docs/builder/BUILD.md` `## Spec reconciliation` in any case. |
| R2 | Worker 1 only unless it turns up a durable-doc or DB edit | Its findings are inside the spec and its companions. If the pass finds a `docs/GLOSSARY.md` or kanban-DB edit is owed, it stops and Worker 0 re-partitions with a Worker 2 pass, because those are generated from `examples/fakeshop/db.sqlite3` and are never hand-edited. |
| Final | Worker 1 only | `worker-1.md` `## Final test-run gate` gives the whole gate to Worker 1. |
| (none) | Worker 2 / Worker 3 | The verification pass found no code defect and no code item to build. `### Isolation is non-waivable` binds a pass that writes code; this cycle writes none. |

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
