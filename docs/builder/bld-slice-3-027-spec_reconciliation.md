# Build: Slice 3 — Spec reconciliation

Spec reference: `docs/SPECS/spec-027-filters-0_0_8.md` (whole file; this slice touched the header block, `## Key glossary references`, `## Slice checklist`, `## Current state`, `## Borrowing posture`, `## User-facing API`, Decisions 1 / 2 / 3 / 6 / 8 / 9 / 10 / 12, `## Implementation plan`, `## Edge cases and constraints`, `## Test plan`, `## Doc updates`, `## Risks and open questions`, `## Definition of done`, and the link-definitions block)
Status: final-accepted

## Plan (Worker 1)

### Worker-1-only artifact shape

This artifact carries a combined `## Plan (Worker 1)` and `## Final verification (Worker 1)` block with no Worker 2 build report and no Worker 3 review. The authorizing clauses:

- [`BUILD.md`][build] `## Required reading per worker` marks the active `-rationale.md` **never** for Worker 2 and `yes (owns)` for Worker 1, and `## Spec reconciliation` states that **only** Worker 1 may mutate the spec. Both files this slice writes are Worker-1-exclusive surfaces.
- [`BUILD.md`][build] `### Procedural-closure slices` is the precedent for the shape: "a single Worker 1 pass that sets `Status: final-accepted` directly — no Worker 2 build, no Worker 3 review. The artifact carries one combined Plan + Final-verification block citing the spec clause that authorizes the closure."
- The build plan [`build-027-filters-0_0_8.md`][build-027] declares it in the preamble: "Ownership partition: none; sequential slices. Slices 1 and 3 are Worker 1's alone; Slice 2 is the only slice with a Worker 2 / Worker 3 cycle."

This slice changes no code, so there is nothing for a builder to build or a reviewer to review against a diff.

### Spec status-line re-verification (Worker 1, every spawn)

Lines 1-9 of `docs/SPECS/spec-027-filters-0_0_8.md` were read at the start of this pass. The `Status:` line was still the ~4,000-character build-progress paragraph opening `in progress` — falsified by the card being `DONE-027-0.0.8`. **This slice owns it** (build-plan finding D2), so the re-verification is discharged by the edit itself rather than by a note; see `### Spec changes made (Worker 1 only)` item 1. `Target release` and `Owner` were accurate; `Predecessors` carried one falsified clause (the three glossary entries described as "all currently `planned for 0.0.8`"), corrected in the same pass.

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately skipped, on the same ground as Slice 1: [`BUILD.md`][build] `### Package-wide helper inventory before helper planning` gates *helper planning*, and this slice adds no helper, shared constant, validation branch, coercion utility, or test helper. No `.py` file is in this slice's writable list; the whole diff is `.md`.
- **Existing patterns reused.** Three, all from files already in the archive. The `Status:` line's shape is [`spec-023-multi_db-0_0_7.md`][spec-023]'s and [`spec-020-list_field-0_0_7.md`][spec-020]'s (`shipped (0.0.X)` + "retained at this path as the durable record"). The `## Current state` framing sentence is `spec-020`'s verbatim idiom ("That is the pre-card baseline this spec was authored against"). The rationale's Slice-3 section reuses this file's own established per-Decision keying (`### <Decision heading>` + a `[spec-027-dN]` cross-file link) so every entry is looked-up-able by the heading and anchor [`BUILD.md`][build] `## Spec rationale extraction` requires.
- **New helpers justified.** None in the package. One throwaway scratch script outside the repo (`apply.py` in the session scratchpad) applied each exact-string replacement only when its occurrence count matched an expected count, writing nothing on any mismatch. It caught one wrong count before it could corrupt the file (a replacement asserted at 1 that had 2 sites — Decision 2's `sets.py` bullet and DoD item 4(c.2) carry the same "five named internal helpers" sentence).
- **Duplication risk avoided.** The characteristic failure of a reconciliation slice is a **half-applied** correction: repointing one of N sites that state the same claim, so the spec ends up internally contradictory. Prevented mechanically — every finding was closed by re-running an occurrence count to zero over the whole file, not by fixing the sites the brief happened to name. The counts are in `### Required re-derivations`.

### Implementation steps

1. Read the spec end to end, then re-derive every one of D2-D11 against `HEAD` rather than accepting the build plan's statement of it.
2. Run two population-finding instruments the brief did not name, because the findings' own vocabulary cannot find what the findings do not mention: (a) every `test_[a-z0-9_]+` token in the spec checked against every `def test_…` in the tree; (b) every backticked package-shaped identifier in the spec checked against the concatenated `django_strawberry_framework/` source.
3. Apply the spec edits in count-asserted batches, gates re-run between batches.
4. Sweep for contradictions the slice itself introduced: census claims spelled positively, forward pointers falsified by a later edit, and sections left on the wrong side of a boundary a new sentence draws.
5. Append the Slice-3 record to the rationale, keyed by spec heading and anchor, carrying what each corrected sentence replaced and why.
6. Verify: both gates, the scaffold checker, in-page anchors, cross-file anchors in both directions, link-definition used-vs-defined, and the required zero-counts.

Line numbers are pin-at-write-time navigational hints. This slice renumbered the spec (1,090 -> 1,113 lines), so any line number written before it ran is stale by construction; everything below cites by content.

### Test additions / updates

None. This slice changes no executable statement, so no test can observe it. The gates that stand in for tests are `scripts/check_spec_glossary.py`, `scripts/check_citations.py`, and `scripts/check_trailing_commas.py --check`; all three are recorded under `## Final verification (Worker 1)`, together with four bespoke link/anchor audits the gates do not cover.

### Implementation discretion items

None. This slice had no Worker 2 to delegate to.

### Failability proofs

`None; this pass introduced no new boundary.` — and not on prose: the diff contains no executable statement at all. `git diff --stat -- '*.py'` is empty for this pass, and the two writable files are `.md`.

### Boundary count and the split question

Zero new boundaries. The split question is answered **no**: the slice's unit of work is "the spec states the current contract", and its findings are not separable — D5's symbol rename and D9's subpass reorder both land inside Decision 6/8 prose that D4's alias table also touches, so splitting would guarantee the half-reconciled state this slice exists to remove.

### Hot-path budget

Not applicable; the build plan declares no hot path, and this slice changes no executable statement.

### Floor verification

Not applicable. The build plan's preamble declares `Floor-verification scope: none`. **No slice in this cycle touches a Django / Strawberry / channels integration seam, so no floor venv is owed by any pass in this cycle** — recorded as that literal rather than left blank, per [`worker-1.md`][worker-1] `### Floor verification scope`.

### Spec slice checklist (verbatim)

The spec's own `## Slice checklist` has no entry for this cycle — `027` shipped as `DONE-027-0.0.8` and its six slices are closed. This slice's contract is the build plan's checklist line plus the governing rule in [`BUILD.md`][build] `## Spec rationale extraction`. The boxes below are that contract, audited by this same pass under `## Final verification (Worker 1)`.

- [x] Rewrite `docs/SPECS/spec-027-filters-0_0_8.md` so it reads as the current contract of what shipped.
- [x] No explanation of any change appears in the spec: no amendment block, no retraction paragraph, no "as of review round N" hedge.
- [x] D2 — the `Status:` line becomes a statement of the card's state.
- [x] D3 — `Filter` is described as the plain re-export of `django_filters.Filter` that it is.
- [x] D4 — the spec states where the relocated mechanics live (`utils/inputs.py`, `sets_mixins.py`), as a where-not-what change: every spec-named symbol still resolves.
- [x] D5 — Decision 8 and DoD item 4 state the typed-`SyncMisuseError` mechanism and the real dispatch symbols; no `_apply_get_queryset_*`, no sentinel string, no interpolated rethrow.
- [x] D6 — Decision 9 states the `register_subsystem_clear` registration seam, not the retired cycle-safe local import.
- [x] D7 — Decision 8 no longer claims a live async HTTP test; it names where `apply_async` is covered.
- [x] D8 — every test name the spec states resolves to a test that exists; the mapping was re-derived, not assumed.
- [x] D9 — the two phase-2.5 filter-only audits are named.
- [x] D10 — the flat-field contract states the `HIDE_FLAT_FILTERS` opt-in.
- [x] D11 — the tail-section rot is closed: `_get_fields`, the "32 terms" CSV claim, the pre-archive `docs/spec-027-…` path, `DONE-NNN-0.0.8`, the `WIP-ALPHA-021` / `spec-021` collision, the open joint-cut contingency, the `[fakeshop-test-library-reload]` target, and the surviving `xfail` description.
- [x] Every change's what / why / what-it-replaced is recorded in `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`, keyed to the spec decision it belongs to by heading and anchor.
- [x] No `.py` file edited; no fenced file edited (`KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `CHANGELOG.md`, `docs/TREE.md`, `README.md`, `docs/README.md`, `TODAY.md`, `GOAL.md`, `db.sqlite3`, the `-terms.csv`).
- [x] `check_spec_glossary.py`, `check_citations.py`, and `check_trailing_commas.py --check` all exit 0.
- [x] Every in-page `](#anchor)` resolves; every `[ref-id]` has a def and every def is used.

---

## Final verification (Worker 1)

- Spec slice checklist: every box above is `- [x]`; each is evidenced below.
- DRY check across this slice and Slices 1-2: no new duplication. Slice 2's file set is 19 `.py` files; this slice's is 2 `.md` files. **Disjoint.**
- Existing tests still pass: not run. This slice changes no executable statement and the plan calls for no focused scope; the gates below are what it can falsify.
- Spec reconciliation: performed as the slice itself.
- Final status: `final-accepted`.

### Byte and line counts

Measured with `wc -c -l` at the moment each number was written.

| File | Before this slice | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-027-filters-0_0_8.md` | 243,044 bytes / 1,090 lines | 255,077 bytes / 1,113 lines | +12,033 bytes / +23 lines |
| `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` | 112,631 bytes / 580 lines | 139,535 bytes / 730 lines | +26,904 bytes / +150 lines |

The **Before** column is the state Slice 1 left, not `HEAD`: `git show HEAD:docs/SPECS/spec-027-filters-0_0_8.md | wc -c -l` reports 324,436 / 1,303, because Slices 1 and 2 are uncommitted. The cycle-wide figure for the spec is therefore 324,436 -> 255,077 (-69,359).

**The spec grew, and that is the expected shape of this slice, not a regression.** Slice 1 was a cut; Slice 3 is a correction. Nine of the twelve findings replace a short wrong sentence with a longer right one (a mechanism named instead of asserted, a test list that resolves, a subpass ordering with its reason), and three add contract that was never stated at all (the two phase-2.5 audits, `HIDE_FLAT_FILTERS`, the alias table). The corpus ratchet in [`BUILD.md`][build] `## The corpus ratchet` binds edits to the six workflow documents, none of which this slice touches.

### Required re-derivations

Every one run against the post-edit file, per the brief. Counted as **occurrences**, not matching lines.

| Token | Occurrences | Note |
|---|---|---|
| `xfail` | **1** | The single surviving use is the contract sentence this slice wrote: the Slice-4a bullet stating the test carries **no** `xfail` marker. Was 3. |
| `WIP-ALPHA-021` | **0** | Was 6. |
| `DONE-NNN` | **0** | Was 3. |
| `_get_fields` | **0** | Was 10. |
| `_apply_get_queryset_sync` | **0** | Was 6; `_apply_get_queryset_async` was 2, now 0. |
| `docs/spec-027` (pre-archive path) | **0** | Was 7. |
| raw `L<digits>` spec self-references | **0** | Was 1 (`Decision-10 L5`), measured outside fenced code blocks. |
| `sentinel` | **0** | Was 2. |
| `bld-slice-6` | **0** | Was 1 (the deleted per-cycle artifact named in the `Status:` line). |
| `32 terms` | **0** | Was 1. |
| `_apply_related_queryset_constraints` | **4** | All four deliberate: they name the **cookbook's** `AdvancedFilterSet` method, not the package's helper. Was 11. |

### Verification performed by this pass

| Check | Command / instrument | Result |
|---|---|---|
| Glossary gate | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-027-filters-0_0_8.md` | `OK: 48 terms - all have glossary entries and at least one spec link.` exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 740 citations resolve (665 in 422 .py files, 75 in KANBAN.md).` exit 0 — identical to Slice 2's post-edit figure, so this slice added and removed no `path::Symbol` citation |
| Markdown scaffold (`source-layout` hook's checker) | `uv run python scripts/check_trailing_commas.py --check` on both edited `.md` files | exit 0 |
| Spec in-page anchors | slug-and-resolve over headings + `<a id=...>` anchors, fenced code stripped | 20 refs, **0 dangling** |
| Rationale in-page anchors | same | **0 dangling** |
| Spec -> rationale cross-file anchors | resolve each `#fragment` against the rationale's headings | all resolve |
| Rationale -> spec cross-file anchors | resolve each `#fragment` against the spec's headings | all resolve |
| Link definitions, spec | used-vs-defined diff + on-disk existence of every def target | no undefined, **no unused** (`[relay]` was orphaned by D5's rewrite and dropped), no broken path |
| Link definitions, rationale | same | no undefined, no unused, no broken path |
| Spec-named test functions vs the tree | every `test_[a-z0-9_]+` token in the spec vs every `def test_…` in the tree | 86 names, **0 missing** (12 remaining non-matches are file stems: `test_base`, `test_sets`, …) |
| Spec-named package symbols vs the package | every backticked package-shaped identifier vs concatenated `django_strawberry_framework/` source | 39 unresolved candidates, **all 39 legitimately external** (upstream cookbook names, `graphene_django` names, fakeshop example classes, stdlib warnings, illustrative names) |
| Scope fence | `git status --short -- docs/SPECS docs/builder` | the only files this pass modified are `docs/SPECS/spec-027-filters-0_0_8.md` and `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`; `spec-024*`, `spec-025*`, `spec-026*` churn is the three concurrent sessions', untouched |
| `.py` diff | `git diff --stat -- '*.py'` for this pass | empty |

### Findings this slice added beyond D2-D11

The brief's contract was D2-D11 plus the seven Slice-2 hand-off items. Six further defects surfaced from the two instruments in `### Implementation steps` step 2, and are the same defect classes as D5 (a pinned symbol that was replaced) and D8 (a named test that does not exist). All six were fixed in this pass and recorded in the rationale.

1. **`_apply_related_queryset_constraints` has zero hits tree-wide.** Six spec surfaces named it as the package's helper; the package's is `FilterSet._apply_related_constraints`. The name is the cookbook's, carried in and never reconciled. Four sites genuinely meant the cookbook ancestor and keep it.
2. **`cls.check_permissions(input_value, request)` is not a call that exists.** `check_permissions(self, request, requested_fields=None)` is the public instance method; the apply pipeline calls the classmethod `cls._run_permission_checks(input_value, request)`, inherited from `sets_mixins.py::ActiveInputPermissionMixin`.
3. **The phase-2.5 subpass order flipped.** D9 named the two unstated audits but not this: at `HEAD` orphan validation runs **before** materialization, the reverse of Decision 6's subpass 3/4. It surfaced from reading `_bind_sidecar_sets` (the shared implementation) rather than `_bind_filtersets` (the filter-family wrapper) alone.
4. **D8's population is 14, not 3** — and one of the three the plan named was no longer a spec claim at all. Detail in the rationale's `### `## Test plan`` entry.
5. **The `tests/filters/` mirror-file census was stated three different ways**, none matching the tree.
6. **`_run_permission_checks` and `LazyRelatedClassMixin` are shared-substrate members**, extending D4's list of relocated mechanics from three names to six.

### Contradictions this slice introduced, and caught

Per the standing trap that a reconciliation slice creates contradictions it cannot see itself, three were found by sweeping after the edits rather than during them:

1. **`## Current state` vs the new `Status:` line.** `## Current state`'s first bullet describes `filters/` as a TODO skeleton, which reads as a contradiction beside `Status: shipped`. Resolved by adding `spec-020`'s pre-card-baseline framing sentence, not by editing the bullet — the baseline is what the section is for.
2. **The `Predecessors` line's glossary-status claim.** It says the three glossary entries are "all currently `planned for 0.0.8`". `docs/GLOSSARY.md` carries `**Status:** shipped (`0.0.8`).` for all three plus `filter_input_type`. The `Status:` rewrite made the contradiction visible; both that line and the `## Current state` glossary bullet now carry the Slice-5 pointer that resolves it. `docs/GLOSSARY.md` itself is fenced and was not touched.
3. **A census claim I wrote in the same pass that warns against them.** The D4 alias table's lead-in first read "Six of the names this Decision pins — the six rows of the table below, **and no other name in this Decision**". False: `materialize_input_class`, `clear_filter_input_namespace`, `_materialized_names` and `_field_specs` are also substrate-produced, by `utils/inputs.py::make_set_input_namespace`. Weakened to a claim that can be checked, and the four extra names stated, before the sentence was left standing. This is the fourth consecutive cycle the positively-spelled-census trap has bitten, and the third time on text the cycle had just written.

A fourth was settled rather than introduced: **Slice 6's disposition**. The `Status:` rewrite states it as carried by the sibling card, which falsifies four surfaces that still left it conditional (`## Slice checklist` Slice 6, `## Implementation plan`'s prose and its table row, DoD item 27). All four now state the settled branch and retain the conditional rule beneath it, so a reader can still judge the rule that produced the outcome.

### Failability, fail-open, and floor confirmations

- **Failability record exists and is proved, not asserted.** `None; this pass introduced no new boundary.` is discharged mechanically: `git diff --stat -- '*.py'` is empty for this pass and both writable files are `.md`, so the diff contains no statement, branch, guard, comparison, or raise for the mandatory floor to select.
- **No fail-open shape landed.** Same proof — the diff contains no expression.
- **Floor verification: none owed, and this artifact records the literal rather than leaving it blank.** The build plan declares `Floor-verification scope: none`; no slice in this cycle touches a Django / Strawberry / channels integration seam, because no slice changes an executable statement. **No floor venv is owed by any pass in this cycle**, and the final gate inherits that declaration.
- **Staged-anchor sweep.** `grep -rn 'TODO(spec-027' .` returns nothing outside this cycle's own artifacts. This slice staged none.

### Summary

Slice 3 rewrote `spec-027` so it states the contract of what shipped. Twelve findings closed: the `Status:` build-progress log became a state; `Filter` is described as the deliberate re-export of `django_filters.Filter` that it is; six relocated mechanics are named at their real homes in `utils/inputs.py` and `sets_mixins.py` with every spec-named alias still resolving; Decision 8's retired sentinel-string / `_apply_get_queryset_*` misuse mechanism became the typed `SyncMisuseError` caught off `apply_type_visibility_sync`; Decision 9's cycle-safe local import became the `register_subsystem_clear` registration seam with the three properties that make it the contract; Decision 8's claimed live async test is retired and `apply_async`'s real package-tier coverage named; every one of the spec's 86 test names now resolves to a test that exists; the two phase-2.5 filter-only audits and the orphan-before-materialize subpass order are stated; `HIDE_FLAT_FILTERS` is attached to the flat-field contract; and the tail rot — `_get_fields`, the "32 terms" claim, the pre-archive path, `DONE-NNN`, the `WIP-ALPHA-021` / `spec-021` collision, the open joint-cut contingency, the reload-fixture target, the surviving `xfail` — is closed to zero occurrences each. Six further defects the build plan never named surfaced from two whole-population instruments and were fixed in the same pass. Every change's what / why / what-it-replaced is in the rationale, keyed by spec heading and anchor; nothing explaining a change survives in the spec.

### Spec changes made (Worker 1 only)

Every edit is to `docs/SPECS/spec-027-filters-0_0_8.md` unless stated. Cited by content, not by line number — this slice renumbered the file. Each entry names the finding it discharges and its one-line reason; the full what-it-replaced record is the rationale's `## Slice 3 — spec reconciliation against HEAD`.

1. **`Status:` line** (D2) -> replaced whole. Reason: a ~4,000-character build-progress log that opened `in progress`, tracked Slices 1-3 / 4 / 4a / 5 / 6 as they landed, and cited a deleted per-cycle `bld-*.md` artifact is the chronology-to-reconstruct-truth shape [`BUILD.md`][build] forbids. Now states `shipped (0.0.8)`, the card id, and what is on disk.
2. **`## Current state`** -> gained `spec-020`'s pre-card-baseline framing sentence. Reason: prevents the contradiction edit 1 would otherwise create.
3. **`Predecessors` line and the `## Current state` glossary bullet** -> the `planned for 0.0.8` glossary-status claim corrected, with the Slice-5 flip named. Reason: `docs/GLOSSARY.md` carries `shipped (0.0.8)` for all four entries.
4. **`## Key glossary references`, three bullets** -> dropped the parenthetical `(planned for 0.0.8)` status tags. Reason: same falsified status; the bullets are vocabulary pointers and carry no status obligation.
5. **Decision 2's `base.py` bullet, the Slice-1 checklist (2 bullets), `## Borrowing posture`, DoD item 3** (D3) -> `Filter` described as the plain re-export of `django_filters.Filter` that deliberately shadows the upstream name; `LazyRelatedClassMixin` described as re-exported from `sets_mixins.py`. Reason: `filters/__init__.py`'s own module docstring states the contract the spec described as a port.
6. **Decision 2's `inputs.py` bullet** (D4) -> gained the where-the-mechanics-live table (six alias / inherited members) plus the `make_set_input_namespace` quartet sentence. Reason: `FieldSpec`, `build_input_class`, `_input_type_name_for`, `LazyRelatedClassMixin`, `RelatedFilter`'s owner-bind machinery and `_run_permission_checks` are single-sited in the shared substrate; every name still resolves from `filters/`, so this is where-not-what.
7. **Decision 3's `FieldSpec` code block and lead-in** (D4) -> shows `utils/inputs.py::GeneratedInputFieldSpec` and names the alias. Reason: the block declared a class in a module that does not define it.
8. **Slice-2 checklist's `build_input_class` call site** (D4) -> corrected `strawberry_django_framework.filters.inputs` to `django_strawberry_framework.filters.inputs` and named the substrate function. Reason: the module path was a transposition of the package name and resolves to nothing.
9. **DoD item 6** (D4) -> names the substrate for the three aliases. Reason: same as 6.
10. **Decision 8's opening paragraph, helper bullet, step 3, step 5, the sync/async split's precedent clause, the `apply_sync` bullet, and the dispatcher paragraph; `## User-facing API`'s apply paragraph; Decision 2's `sets.py` bullet; DoD item 4(c.1)** (D5) -> the retired mechanism replaced throughout by `utils/querysets.py::apply_type_visibility_sync` / `::apply_type_visibility_async` and the typed `SyncMisuseError`, with the class-based dispatch and the un-interpolated rethrow stated. Reason: `_apply_get_queryset_sync` / `_apply_get_queryset_async` have zero hits tree-wide and the sentinel-string match is retired.
11. **`## User-facing API`'s request-extraction clause** (D5-adjacent) -> names `FilterSet._request_from_info(info)` instead of inlining one expression. Reason: the behavior is the contract; the spelling is not.
12. **Decision 8 step 5** (new finding 2) -> names `cls._run_permission_checks(input_value, request)` and marks `check_permissions(self, request, requested_fields=None)` as the public instance method. Reason: the call the spec named exists in neither shape.
13. **Decision 8's consumer-pattern paragraph** (D7) -> the claimed live async HTTP test retired; `apply_async`'s package-tier coverage named; the `aget_queryset` hedge removed. Reason: `grep -rn apply_async examples/fakeshop/` returns zero and no `aget_queryset` exists.
14. **Decision 9's import-cycle bullet and code block** (D6) -> replaced by the `register_subsystem_clear` seam with the three properties that make it the contract; Decision 11's clear bullet, the Slice-3 checklist, the `## Implementation plan` Slice-3 row and DoD item 10 reconciled in the same pass. Reason: `registry.py` imports `filters` by no route at all; the local-import shape predates the registration seam.
15. **Decision 6's subpass block** (D9 + new finding 3) -> gained `**Subpass 2.5 — Filter-only audits.**` naming both audits and their order, restated subpass 3 as orphan validation and subpass 4 as materialization, and added the paragraph on why that order is load-bearing. Slice-3 checklist and DoD item 10 reconciled. Reason: `_bind_sidecar_sets` runs bind -> expand -> audits -> orphan -> materialize; the spec had 3 and 4 reversed and named neither audit.
16. **Decision 3's flat-field contract, the `galaxy__name` edge case, and the `## Test plan`** (D10) -> state the `HIDE_FLAT_FILTERS` opt-in, its default, its every-depth scope, and its four tests. Reason: `conf.py::hide_flat_filters_setting` changes the generated input shape and the spec's flat-field contract read as unconditional.
17. **`## Test plan`, eleven passages; Slice-4a's three-test bullet** (D8) -> every named test replaced with one that exists, including the three tree-form tests that moved to the live tier and the `filter_input_type` PEP-563 test that has no replacement. Reason: 14 spec-named test functions returned zero hits.
18. **Decision 12, the `## Test plan` heading paragraph, DoD item 11** (new finding 5) -> one enumerated `tests/filters/` set, consistent across all three. Reason: three different "five files" counts, none matching the tree.
19. **Decision 2's `sets.py` bullet, Decision 3, `## Edge cases`, `## Borrowing posture`, `## Test plan`, DoD item 4(e)** (D11) -> `_get_fields` -> `FilterSet.get_fields`, and the Test plan's `_get_fields("__all__")` call shape corrected to the real no-argument classmethod. Reason: no `_get_fields` exists anywhere in the package.
20. **Seven surfaces naming `_apply_related_queryset_constraints` as the package's helper** (new finding 1) -> `FilterSet._apply_related_constraints`; the four that mean the cookbook ancestor keep the upstream name and now say so. Reason: zero hits tree-wide for the package symbol.
21. **Decision 1, the `## Doc updates` KANBAN quote, the Risks CSV bullet, DoD items 1 and 17** (D11) -> the pre-archive `docs/spec-027-…` path corrected to `docs/SPECS/…` (and the CSV to `docs/SPECS/appx/…`); Decision 1 now states the stem is canonical at either location. Reason: `NEXT.md` Step 8 archived the file.
22. **Risks, the terms-CSV bullet** (D11) -> "32 terms and does NOT include `filter_input_type`" replaced by the timing rule plus the shipped counts. Reason: the CSV carries 48 rows and does include it; the glossary heading exists and the gate is green.
23. **Decision 10 and DoD item 24** (D11) -> the three-WIP-card bundle corrected to filtering + ordering (the consumer-DX card shipped at `0.0.9` as `DONE-029-0.0.9`); the joint-cut contingency resolved to the branch that applies, with the rule retained beneath it. Reason: `0.0.8` shipped and the ordering card is last of the bundle.
24. **Six `WIP-ALPHA-021-0.0.8` sites and DoD item 22's `DONE-NNN-0.0.8`** (D11) -> the card named `DONE-027-0.0.8` throughout. Reason: `021` names the `AppConfig` spec today, so the spec used one number for two things.
25. **The `## Doc updates` KANBAN quote's `Decision-10 L5` clause** (D11) -> names the outcome instead of a spec line. Reason: [`AGENTS.md`][agents] rule 27 forbids raw line refs in a standing doc, and Slice 1's renumbering had already falsified it.
26. **Slice-4a's test bullet** (D11) -> states the test as a plain passing test carrying no `xfail` marker. Reason: no `xfail` marker exists anywhere in `test_library_api.py`.
27. **`[fakeshop-test-library-reload]` definition and the `## Test plan` footnote** (D11) -> both repointed to `examples/fakeshop/test_query/conftest.py::_reload_project_schema_for_acceptance_tests`, together in one edit. Reason: fixing the definition alone would leave the footnote naming a symbol in a file that does not define it.
28. **`## Slice checklist` Slice 6, `## Implementation plan` prose and table row, DoD item 27** -> the Slice-6 disposition settled as carried by `DONE-028-0.0.8` at `tests/orders/test_composition.py`, with the conditional rule retained. Reason: edit 1 states it in the header; leaving four surfaces conditional is the half-reconciled state.
29. **Decision 4's "corrected rule", Decision 4's "no longer sufficient", the Risks section's "corrected idiom"** -> narration phrasing Slice 1 did not reach, restated directly. Reason: `## Spec rationale extraction` — the spec never narrates its own history.
30. **Link-definitions block** -> added `[conf]`, `[querysets]`, `[sets-mixins]`, `[utils-inputs]`, `[test-orders]`, `[test-registry]`; removed `[relay]`, orphaned by edit 10; repointed `[fakeshop-test-library-reload]`. Reason: every def used, every use defined, every path on disk.

**`docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`** gained `## Slice 3 — spec reconciliation against HEAD` (+26,904 bytes): one entry per spec surface above, each naming what the corrected sentence replaced, why the replacement is right, and what caused the drift; a 14-row table mapping every retired test name to what covers its contract; a re-derived-populations table naming the five inherited counts that were wrong and how; and the symbol-sweep instrument that found the six extra defects. A pointer sentence was added at the head of the pre-existing `## Claims the spec may no longer make` naming the two items in it whose populations the Slice-3 measurement corrects — a two-line correction rather than a rewrite, keeping the list readable as the pre-measurement inventory it is.

### Notes for Worker 1 (integration pass and final gate)

**Deferred, with a target. Nothing here is a code defect in shipped behavior.**

1. **`tests/test_registry.py::test_clear_tolerates_unimportable_filter_submodules` carries a docstring describing a mechanism that no longer exists** — "Both `except ImportError` guards in `clear()` are best-effort … cycle-safe local imports". `TypeRegistry.clear()` has no such guards; the test now proves only that poisoning `sys.modules` leaves the registry's own clear undisturbed. Its `_order_` and `_connection_` and `_relay_` siblings at `tests/test_registry.py` are the same shape and want the same read. **Target: the final gate's `### Deferred work catalog`, for a card.** Slice 2 closed this cycle's `.py` work and this slice edits no `.py` file. Re-derive the sibling population before carding — I read four names off a `grep` and did not audit whether all four describe the retired shape.
2. **The PEP-563 (`from __future__ import annotations`) resolver-annotation path for `filter_input_type` has no test.** The spec now says so. The eager path is covered by two package tests plus the six live fakeshop resolver annotations, and the repeat-safety property PEP 563 depends on is covered by `test_filter_input_type_is_idempotent_under_repeated_calls`, so this is a coverage boundary rather than an untested contract. **Target: the final gate's catalog, for a card.**
3. **Slice 2's hand-off items 5, 6 and 7 remain open and are not this slice's.** (5) history-narrating prose in `.py` comments — a real class whose population is instrument-dependent and unaudited (Worker 3 measured ~65 across 15 files, my token sweep 54 across 11, neither audited hit-by-hit; both include legitimate contrast prose). (6) bare `Decision N` references naming no card — 83 raw occurrences, most belonging to **other** cards, so the defect is attribution and cannot be swept by number. (7) five `spec-036` raw line refs in `examples/fakeshop/test_query/test_products_api.py` at lines 2948 / 2984 / 3015 / 3051 / 3098. **Target: the final gate's catalog.** All three are `.py`-surface.
4. **`KANBAN.md`'s carded repo-wide sweep already owns one spec-027 item** — its "lands when `DjangoConnectionField` ships in `0.0.9`" auto-generation sentence in `## Non-goals`, to be scrubbed to match `spec-028` Decision 12's standing-non-goal precedent, gated on the DRY-squeeze card's WP-D answer. **Left untouched deliberately**; it is carded, and acting on it here would pre-empt a decision this cycle does not own. Record it in the catalog as already-carded so a future sweep does not re-derive it as new rot.
5. **`docs/GLOSSARY.md`, `KANBAN.md`, `docs/TREE.md`, `README.md`, `docs/README.md`, `TODAY.md`, `GOAL.md` were not read against the spec's `## Doc updates` obligations.** The maintainer fenced this cycle to spec files and `.py` files, so the spec may describe what those docs carry but this slice could not verify it. **The integration pass should not read the absence of a finding here as a clean bill** — it is an unexamined surface, not an examined-and-green one. The one datum I do have: `docs/GLOSSARY.md` carries `shipped (0.0.8)` for all four filter entries, which is what closed contradiction 2 above.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

[spec-020]: ../SPECS/spec-020-list_field-0_0_7.md
[spec-023]: ../SPECS/spec-023-multi_db-0_0_7.md

<!-- docs/builder/ -->

[build-027]: build-027-filters-0_0_8.md
[build]: BUILD.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
