# Build: Slice 6 — Sibling-card composition smoke tests

Spec reference: `docs/spec-021-filters-0_0_8.md` (Slice checklist sub-bullet at lines 160-161; cross-references at L60 "DoD item 27", L1176 DoD item 27, and L4 status-line trailing sentence)

Status: final-accepted

## Plan (Worker 1)

### Procedural-closeout justification

This is a **procedural closeout pass**, not a normal plan/build/review/verify cycle. The spec's own Slice-checklist sub-bullet (L161) carries an explicit conditional clause that pre-resolves what happens depending on which sibling card ships first:

> "If `WIP-ALPHA-022-0.0.8` ships first, the test lands as a slice-back-edit to this card's PR; if **this card ships first, the composition test lands in the ordering card's PR and this card's Slice 6 is closed as 'carried by sibling'**."

`KANBAN.md` (L51, L77, L79) confirms `WIP-ALPHA-022-0.0.8` (Ordering subsystem) is still WIP and has NOT shipped. This card (`WIP-ALPHA-021-0.0.8` — Filtering subsystem) ships first via Slices 1, 2, 3, 4, 4a, and 5 — every prior slice landed `final-accepted` per the build plan checklist at `docs/builder/build-021-filters-0_0_8.md`. The conditional clause's "this card ships first" branch fires; Slice 6 closes as **carried by sibling**.

The contract Slice 6 names — a `tests/filters/test_composition.py` smoke test that wires both `Meta.filterset_class` and `Meta.orderset_class` on a single `DjangoType` and asserts both input types resolve through `finalize_django_types()` — is **not violated** by this card's silence. The contract is **fulfilled by the spec's conditional clause itself**: the test is owned by whichever sibling card ships second, and that sibling is `WIP-ALPHA-022-0.0.8`. DoD item 27 (spec L1176) reinforces: "This card's DoD does NOT require Slice 6's test to land here."

The procedural compression — Worker 1 produces both the Plan and the Final-verification sections in a single artifact with `Status: final-accepted` set at the top — is authorized by the spec's explicit closure clause AND by the absence of any code/test surface to build, review, or test. No Worker 2 / Worker 3 dispatch is needed because there is no implementation to write and no diff to review. No `pytest` run is needed because there is no new test surface and the existing filter suite is already exercised by Slices 1-4a.

### Spec slice checklist (verbatim)

- [x] One in-process test under [`tests/filters/test_composition.py`][test-filters-composition] (new) that constructs a `DjangoType` with BOTH `Meta.filterset_class` AND `Meta.orderset_class` set, calls `finalize_django_types()`, and asserts both factories' input types are reachable from the schema. The test is held until [`WIP-ALPHA-022-0.0.8`][kanban] (ordering) ships its `OrderSet` / `Meta.orderset_class` so this card's spec body can name the composition contract without writing the sibling-card test prematurely. If [`WIP-ALPHA-022-0.0.8`][kanban] ships first, the test lands as a slice-back-edit to this card's PR; if this card ships first, the composition test lands in the ordering card's PR and this card's Slice 6 is closed as "carried by sibling".

The box is ticked because the spec's contract for Slice 6 is a conditional — it does NOT require the test to land in THIS card's PR when this card ships first. The "carried by sibling" branch is the spec-authorized closure, and `WIP-ALPHA-022-0.0.8` (still WIP per `KANBAN.md`) inherits the maintainer-side carry-forward obligation to land `tests/filters/test_composition.py` in its own PR.

### Implementation steps

No implementation in this card. Slice 6's composition smoke test will land in `WIP-ALPHA-022-0.0.8`'s PR per spec L161.

### Test additions / updates

None in this card.

### Implementation discretion items

Not applicable.

---

## Final verification (Worker 1)

- **Spec slice checklist:** the single sub-check at spec L161 is ticked `- [x]` above. The spec contract for Slice 6 is a conditional that resolves to "carried by sibling" when this card ships first; the contract is satisfied by this card NOT writing the test and by `WIP-ALPHA-022-0.0.8` inheriting the carry-forward obligation. There is no silently un-ticked box and no implicit deferral — the box's resolution mode is the spec's own pre-pinned branch.
- **DRY check across this slice and prior accepted slices:** N/A. This slice ships no code, no tests, no docs, and no helpers. No new duplication can be introduced by an empty contract.
- **Existing tests still pass:** N/A. No new test surface; the existing filter suite was last exercised at Slice 5's final-verification pass (`uv run pytest tests/filters/ examples/fakeshop/test_query/test_library_api.py --no-cov` = 154 passed, 26 warnings) and at Slice 4's final-verification pass (`uv run pytest examples/fakeshop/test_query/test_library_api.py tests/filters/ tests/types/ --no-cov` = 396 passed, 2 skipped, 1 xfailed; Slice 4a then flipped the xfail to passing). The full-suite test-run gate runs in `bld-final.md` after the integration pass.
- **Spec reconciliation:** the spec needed a minimal status-line edit to record that the carry trigger fired. See `### Spec changes made (Worker 1 only)` below.
- **Final status:** `final-accepted`.

### Spec changes made (Worker 1 only)

- `docs/spec-021-filters-0_0_8.md` L4 (the status header line, two clauses): (a) flipped the bolded trailing clause from `Slice 6 composition smoke tests held until sibling card [WIP-ALPHA-022-0.0.8][kanban] ships` to `Slice 6 composition smoke tests closed as "carried by sibling" per the Slice-checklist conditional clause — this card shipped first, so the composition smoke test lands in [WIP-ALPHA-022-0.0.8][kanban]'s PR`; (b) rewrote the L4 closing sentence from `The cross-card composition smoke tests with [WIP-ALPHA-022-0.0.8][kanban] are still pending per the Slice checklist below.` to `The cross-card composition smoke test with [WIP-ALPHA-022-0.0.8][kanban] is carried by the sibling card per the Slice-checklist conditional clause (docs/builder/bld-slice-6-composition_smoke_test.md records the procedural closure).`. Reason: the prior wording described Slice 6 as pending; the procedural-closeout pass resolved Slice 6 via the spec's own conditional clause, so the status line must record the resolution (which branch of the conditional fired) and forward-reference this artifact as the procedural record. The contract bodies at L161, L60 (rev6 H1's DoD item 27 rationale), and L1176 (DoD item 27) are unchanged — they already document the conditional outcome; the L4 edit is mechanical status-tracking only.

### Summary

Slice 6 closes procedurally as **carried by sibling**, not as a worked slice. The spec's Slice-checklist sub-bullet at L161 names a conditional contract: when `WIP-ALPHA-022-0.0.8` (Ordering subsystem) ships first, the composition smoke test lands here as a back-edit; when this card (`WIP-ALPHA-021-0.0.8` — Filtering subsystem) ships first, the composition smoke test lands in the ordering card's PR and Slice 6 closes here as "carried by sibling". `KANBAN.md` confirms `WIP-ALPHA-022-0.0.8` is still WIP, so the "this card ships first" branch fires and the spec-pinned closure applies. No source code, no tests, and no doc surfaces land in this card for Slice 6. DoD item 27 (spec L1176) explicitly does not require Slice 6's test to land here. The maintainer-side carry-forward — that `tests/filters/test_composition.py` lands in `WIP-ALPHA-022-0.0.8`'s PR when the ordering subsystem ships — is recorded in `docs/builder/worker-memory/worker-1.md` so the next Worker 1 instance dispatched for the ordering card inherits the obligation. A single targeted spec edit at L4 flips the status-header wording from "Slice 6 ... held until ... ships" to "Slice 6 ... closed as 'carried by sibling' ... this card shipped first" and forward-references this artifact; no contract clauses were touched.
