# Build: Slice 1 — Rationale extraction (spec-023 multi_db)

Spec reference: `docs/SPECS/spec-023-multi_db-0_0_7.md` (whole file; the deliberative layer was concentrated in lines 8-51 and in the nine `### Decision` blocks at 231-465, pre-cut numbering)
Status: final-accepted

This slice is Worker-1-exclusive by `docs/builder/BUILD.md`'s own rules — only Worker 1 may mutate the spec, and Worker 2 may never read the rationale file — so the Plan, the work, and the final-verification block were all written in one pass. No Worker 2 or Worker 3 dispatch.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately skipped: this slice writes Markdown only and adds no logic to `django_strawberry_framework/`. The build plan declares `Hot-path declaration: none` and `Floor-verification scope: none`, and states "No production code is planned." Running the package-wide AST inventory would produce ~1,600 lines that no step of this slice can consume. Recorded as an explicit skip with reason, per `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning`.
- **Existing patterns reused.** `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md` (a concurrent cycle's file, read-only) is the shape reference: title line naming the spec, a `## Provenance of this record` block carrying measured populations and byte counts, a moved/stayed/deleted ledger, per-decision entries keyed by heading and anchor, and a closing `## Verified against the shipped code`. This file follows that shape. It was read and never edited.
- **New helpers justified.** None (no code). Two throwaway scripts were written to the session scratchpad (`cut.py`, `repl.py`, `gen.py`) so every excision and substitution could assert its own occurrence count; they are not repo artifacts.
- **Duplication risk avoided.** The move's characteristic duplication is text that ends up in *both* files. Prevented mechanically: `cut.py` captured the sixteen excised blocks to JSON and deleted them from the spec in the same run, and `gen.py` composed the rationale from that JSON. No block was retyped, so no block can survive in two places.

### Implementation steps

1. Cut the five-revision `Revision history` block (lines 8-52) out of the spec.
2. Cut sixteen `Justification:` / `Alternatives considered (and rejected):` blocks — every one except `### Decision 6`'s justification.
3. Strip every `revN Xn` attribution from the thirteen non-Decision sections, rewriting the sentence to state the narrow claim directly wherever the attribution was carrying it.
4. Rewrite the `Status:` line so it stops advertising an inline revision history and names the rationale companion instead.
5. Add a one-line `Rationale companion —` pointer to each of the nine Decisions.
6. Compose `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` from the captured blocks plus a per-Decision change record.
7. Verify: `check_spec_glossary.py` exits 0, every ref-id resolves in both files, every def path exists on disk, every in-page anchor resolves, and `grep -cE 'rev[0-9]'` against the spec returns 0.

### Test additions / updates

None. This slice adds no test and modifies no test file. The mechanical checks in step 7 stand in for tests and are recorded under `## Final verification` below.

### Implementation discretion items

None delegated — this pass performed the work itself. Two judgement calls it made rather than deferred are recorded under `### Judgement calls` below.

### Spec slice checklist (verbatim)

The spec's `## Slice checklist` has no sub-bullets for this work: its three slices are the original card's build (package tests / live tests / docs), all of which shipped. This cycle's units come from the build plan's own `## Checklist`, so the box below is that plan's Slice 1 line, quoted.

- [x] Slice 1: Rationale extraction — MOVE the deliberative layer out of `docs/SPECS/spec-023-multi_db-0_0_7.md` into `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` -> `docs/builder/bld-slice-1-023-rationale_extraction.md`

---

## Final verification (Worker 1)

### Summary

The deliberative layer of `spec-023` moved to `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`. The spec no longer narrates its own history: after the pass, `grep -cE 'rev[0-9]' docs/SPECS/spec-023-multi_db-0_0_7.md` returns **0** (it returned 202 before, of which 130 were `revN Xn` attribution parentheticals). Nine Decisions each keep a one-line pointer into the rationale; the rationale keys every entry to a Decision by heading and anchor and carries, per Decision, the alternatives rejected, every change it underwent with the round that caused it, and the claims it may no longer make.

**Measured byte counts (`wc -c`, at this working tree):**

| File | Before | After |
|---|---|---|
| `docs/SPECS/spec-023-multi_db-0_0_7.md` | 163,336 | 110,831 |
| `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` | 0 (did not exist) | 84,471 |

The spec's change is **-52,505 bytes**. The **Before** figure is the on-disk size when this pass opened the file, not the size at `HEAD` — see `### Baseline hazard` below. Both figures were produced by writing the sentence with fixed-width placeholders, running `wc -c`, and substituting; the rationale's own figure is a converged fixed point (the substitution changes the file's length, so the script iterated until the stated number equalled the measured one).

This file is larger than the byte delta implies would fit, for two reasons stated in its own provenance block: the per-Decision `### Changes this Decision underwent` records and the whole `## Claims the spec may no longer make` section are **new material** this pass produced (the original cycle never wrote a change record), and five passages were **deleted rather than moved** under `docs/builder/worker-1.md` rule 2.

### Populations measured before the cut

| Population | Measured | Instrument |
|---|---|---|
| `Revision history` entries | 5 | `grep -cE '^\- \*\*Revision [0-9]+\*\*'` |
| numbered findings inside them | 37 | `grep -c '^  [0-9]*\. \*\*'` |
| `Justification:` blocks at line start | 9 | `grep -c '^Justification:'` |
| `Justification`-prefixed clauses anywhere | 11 | `grep -oE 'Justification[a-z ]*:' \| wc -l` |
| `Alternatives considered` lists | 7 | `grep -oE 'Alternatives considered' \| wc -l` |
| `revN Xn` attributions | 130 | `grep -oE '[Rr]ev[0-9]+(-post)? [A-Z][0-9]+' \| wc -l` |
| bare `rev[0-9]` tokens | 202 | `grep -oE 'rev[0-9]' \| wc -l` |

The 9-vs-11 gap is the `spec-022` lesson repeating: two `Justification:` clauses sit mid-bullet where `^Justification:` cannot see them (the Slice-3 "No edits to README / GOAL / TODAY" bullet and the Doc-updates "No edits to `docs/TREE.md`" bullet). Both are one-clause scope statements — the reason a doc is *not* edited — so both **stayed**. The count is recorded so the next reader does not mistake 9 for the population.

### Mechanical verification

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-023-multi_db-0_0_7.md` -> `OK: 18 terms - all have glossary entries and at least one spec link.` exit 0. Same as the pre-flight reading; no term lost its only spec link. The three joint-cut glossary terms (`DjangoListField`, `Django AppConfig`, `Schema export management command`) were at risk because one of their three link sites was inside Decision 9's justification; they survive in `## Current state` and in the `## Doc updates` CHANGELOG entry.
- `uv run python scripts/check_trailing_commas.py --check` on both files -> exit 0 (link-def scaffold intact; all ten canonical group headers present and in order in the new file, `docs/SPECS/appx/` targets filed under `<!-- docs/SPECS/ -->` per the closed-list rule).
- Ref-id resolution, both files: `used-not-defined: []`, `defined-not-used: []` (code spans and fenced blocks stripped before scanning).
- Every one of the rationale's 64 link definitions was disk-exists-checked, and every `#fragment` into the spec was checked against the spec's actual heading slugs. Zero failures.
- In-page anchors, both files: all resolve, with one pre-existing exception recorded below.
- `grep -cE 'rev[0-9]'` on the spec -> `0`. `grep -n 'Worker 1\|Worker 2\|Worker 3'` on the spec -> no hits (three "Worker 2 has to …" phrasings in the `## Test plan` pins were made role-neutral).
- No `pytest` run and no `--cov*` flag anywhere in this pass. No commit, no branch, no `git stash` / `checkout` / `restore`.

### Judgement calls

1. **`## Risks and open questions` stays in the spec.** `spec-022`'s rationale moved its Risks section wholesale, so the precedent pointed the other way. Two things overrode it: the section's bullets are "preferred answer for `0.0.7` + fallback if implementation proves it wrong", which is forward-looking contingency rather than chronology; and the build plan's D2 / D12 dispatch Slice 2 to reconcile specific Risks bullets, which presumes they are still in the spec. Only the `revN Xn` attributions inside the section were cut. Under `docs/builder/worker-1.md`'s "when it is unclear, it stays", this is the conservative outcome.
2. **`### Decision 6`'s whole `Justification:` block stays in the spec.** Its three bullets are the mechanism that makes `pytest.skip(..., allow_module_level=True)` correct and `pytest.mark.skipif` wrong — `config.settings` decides `DATABASES` at module-import time, so a mark evaluated after import cannot stop the model imports running against a single-DB dict. This is exactly the implementation-relevant carve-out the role file calls "the one place this move can itself cause a defect". The same reasoning kept Decision 6's two pinned-import annotations (`importlib` / `sys` are used by the copied reload fixture; `DjangoType` / `finalize_django_types` must NOT be re-added or ruff flags `F401` and the no-`# noqa` rule blocks the fix).

### Deleted, not moved

Five passages whose only reason to exist was to correct an earlier revision, per `docs/builder/worker-1.md` rule 2. Each is catalogued in the rationale's `## Provenance of this record` so a reader can still see it existed.

1. Edge cases: the `D103`-vs-`D102` clarifier (documented a claim that no longer appears anywhere).
2. Edge cases: "Rev1's wording … referred to an API that does not exist; rev3's wording … mis-positioned the third argument."
3. Slice checklist: "mirroring [`spec-021`] rev4 informational item 2 and [`spec-022`] rev2 M1" — a citation into two sibling specs' revision numbering, which their own rationale moves have retired.
4. The rev5 X1 / X2 / X3 letter-correction narratives in Decision 3, Edge cases, and Risks.
5. Four link definitions orphaned by the move (`[spec-018]`, `[spec-019]`, `[spec-021]`, `[next-step-8--archive-prior-specs-and-update-cross-references]`); their targets are cited from the rationale instead.

### Baseline hazard (concurrent session)

`docs/SPECS/spec-023-multi_db-0_0_7.md` was **already dirty at pass start and changed mid-read**. `git show HEAD:…| wc -c` reports 163,533; the on-disk size was 163,449 at my first measurement and 163,336 at my second, with `stat` showing a write at 19:46:27 — a concurrent session rewriting nine stale reference ids (`spec-016`->`spec-020`, `spec-017`->`spec-021`, `spec-018`->`spec-022`, `spec-019`->`spec-023`, plus companions) and four `AGENTS.md` quote substrings. That work was left untouched per `AGENTS.md` rule 34; every cut and replacement in this pass was applied to the post-19:46 content and each asserted its own occurrence count, so a mid-flight change would have failed the assertion rather than silently mis-cutting. **The "Before" byte count in every table above is the post-19:46 on-disk size, not the `HEAD` size.** A reader diffing against `HEAD` will see that session's 43-line change mixed into this slice's diff; it is not this slice's.

The same session also committed several files during the pass (`docs/GLOSSARY.md`, `tests/test_apps.py`, `docs/SPECS/spec-021-apps-0_0_7.md` all went clean) and deleted three of its own `bld-*.md` artifacts. Nothing in this cycle's writable set was affected.

### Handed to Slice 2 (do not treat as discharged)

- **All thirteen drifted claims D1-D13 remain open**, except D13, which this slice discharged. Nothing was pre-corrected while moving text.
- **D1's moved half needs no spec edit but its surviving half does.** Decision 2's grep-population justification moved to the rationale, where it carries an explicit time-scope warning naming the three `utils/` call sites and ten `.using(` modules that postdate it. The identical claim in `## Current state` bullet 1 is still live in the spec and is Slice 2's.
- **D5's "six lines" claim likewise moved** (it sat in Decision 2's third rejected alternative) and carries its own time-scope warning in the rationale. The `## Edge cases and constraints` null-FK bullet's "only runs when `related_id is not None`" is still live in the spec.
- **A pre-existing broken in-page anchor.** `#decision-9--joint-0_0_7-cut` is used twice in the spec (the `Predecessors:` line and Decision 9's own cross-reference) but the heading `### Decision 9 — Joint \`0.0.7\` cut` slugs to `decision-9--joint-007-cut` — a dotted version renders as `007`, not `0_0_7`. This predates the move and was left alone; the rationale's own def uses the correct spelling. Slice 2 should fix both spec occurrences.
- **The letter drift is worse than D12 states.** D12 names one surviving `(g)` in `## Risks and open questions`. There is also a straight disagreement between `## Edge cases and constraints` (calls the consumer-`Prefetch` test **(f)**), `### Decision 3` axis 3 and `## Risks` (call it **(g)**), and the `## Definition of done` item 2 (calls it **(f)**). Every letter was left untouched by this pass. Recorded in the rationale under `## Claims the spec may no longer make` item 4.
- **`docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv` still carries two `rev2 H2` / `rev2 H6` attributions in its `notes` column.** The CSV was outside this pass's writable set. If Slice 2 does not own it, it needs a home.
- **The rationale file is append-only from here.** Slice 2's reconciliation record appends to it in the same custodian pass that edits the spec.

### Spec changes made (Worker 1 only)

Every edit below is Slice 1 (the rationale move). Line references are pre-cut numbering.

| Spec section | Change | Reason |
|---|---|---|
| `Status:` line (4) | Dropped "the revision history below is preserved for archaeology"; now names the rationale companion | The history it advertised is what the move removed |
| Header block (8-52) | Deleted the whole five-revision `Revision history` block | Moved to the rationale; a spec never narrates its own history |
| `## Key glossary references` (59, 61) | Removed two rev-annotations; kept the narrow claim and the `_check_n1` verification | Attribution is deliberation; the claim and the source ref are contract |
| `## Slice checklist` (78-89) | Removed seven rev-annotations; restated the strictness-test placement rule and the `per-file-ignores` fact directly | The rules were only stated inside correction stories |
| `## Problem statement` (107) | Removed one rev-annotation | Chronology |
| `## Current state` (120) | Removed one rev-annotation | Chronology |
| `## Goals` (132-134) | Removed five rev-annotations | Chronology; every narrow claim is stated in the surrounding prose |
| `## User-facing API` (199, 215) | Removed two rev-annotations; kept the three-case implicit-router contract | Chronology |
| `### Decision 1` (235-245, 246) | Cut justification + two rejected alternatives; de-annotated the lifecycle note; added pointer | Rationale move |
| `### Decision 2` (257-268) | Cut justification + three rejected alternatives; added pointer | Rationale move (the moved text carries a time-scope warning in the rationale) |
| `### Decision 3` (271-288) | Cut justification; removed six rev-annotations across the four axes; kept every mechanism and every "verified against" clause; added pointer | Rationale move |
| `### Decision 4` (294-304) | Cut justification + two rejected alternatives; added pointer | Rationale move |
| `### Decision 5` (307, 312-318, 324-329) | Cut justification + three rejected alternatives; de-annotated the opening; kept the `Mock target` block; added pointer | Rationale move |
| `### Decision 6` (340-419) | Cut six rejected alternatives; removed eight rev-annotations from the pinned shapes; **kept the justification and both import annotations**; added pointer | Implementation-relevant carve-out |
| `### Decision 7` (425-436) | Cut justification + two rejected alternatives; added pointer | Rationale move |
| `### Decision 8` (441-447) | Cut justification; kept the breadcrumb sentence; added pointer | Rationale move |
| `### Decision 9` (454-466) | Cut justification + two rejected alternatives; kept the version-bump exclusion sentence; added pointer | Rationale move |
| `## Implementation plan` (473-477) | Removed the per-revision annotation runs from both table rows and the line-delta revision note | Chronology inside a planning table |
| `## Edge cases and constraints` (484-494) | Removed six rev-annotations; deleted two falsified-claim clarifiers; kept every mechanism | Rationale move + rule 2 deletions |
| `## Test plan` (498-552) | Removed thirteen rev-annotations; made three implementer pins role-neutral; kept the `FieldError` mechanism behind the widened isolation query | Chronology; the mechanism is instruction |
| `## Doc updates` (564) | Removed one rev-annotation | Chronology |
| `## Risks and open questions` (594-597) | Removed four rev-annotations; **section otherwise untouched** | Judgement call 1 |
| `## Out of scope` (602) | Removed two rev-annotations | Chronology |
| `## Definition of done` (615-622) | Removed eight rev-annotations | Chronology |
| Link definitions | Added `[spec-023-rationale]` and `[rationale-d1]`…`[rationale-d9]`; removed four defs orphaned by the move | Keeps the spec's half of the two-file keying resolvable |
