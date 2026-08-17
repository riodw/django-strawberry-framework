# Build: R1 — rationale extraction and spec reconciliation (spec-015)

Spec reference: `docs/SPECS/spec-015-relay_interfaces-0_0_5.md` (whole file)
Status: final-accepted

Procedural-closure shape per `docs/builder/BUILD.md` `### Procedural-closure slices`: this item was
dispatched to Worker 1 alone — no Worker 2 build, no Worker 3 review — because the plan's
verification pass found no code defect and no code item to build, and both writable content files
(the spec and its rationale companion) are Worker-1-owned by `docs/builder/BUILD.md`
`## Spec reconciliation`. This artifact therefore carries a combined Plan + Final-verification block.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately not run: this item writes Markdown
  only, adds no package source, and proposes no helper, shared constant, validation branch, or test
  helper. `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning` gates
  *helper planning*; there is none here, and running the AST inventory over
  `django_strawberry_framework/` would have produced ~1,600 lines of index for a pass that cannot
  write a helper. The package source was read anyway — read-only, from `HEAD` — but as the subject of
  the spec's claims, not as a reuse surface.
- **Existing patterns reused.** The rationale companion's shape is taken from the two shipped
  precedents in this series, `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md` and
  `docs/SPECS/appx/spec-014-testing_shift-0_0_4-rationale.md` (both read-only, neither edited):
  preamble → `## How to read this file` → `## Provenance of this record` → `## What the card actually
  did` → `## Entries keyed to the spec` → `## Reconciliation record`. Same section names, same
  *Moved* / *Deleted, not moved* / *Claim the spec no longer makes* italic markers, same
  ten-group link-definition scaffold resolved from `docs/SPECS/appx/`.
- **New helpers justified.** None.
- **Duplication risk avoided.** One shape: a rationale that restates the spec's normative content
  alongside its deliberation would make two sources of truth for the same contract, which is exactly
  the failure `## Spec rationale extraction` exists to prevent. The move is a cut — every *Moved*
  block is quoted in the rationale and absent from the spec, verified by grepping the moved
  substrings back against the spec (see `### Move verification` below).

### Implementation steps

1. Create `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md` on the precedent shape;
   perform the MOVE (cut, not copy) of the deliberative layer.
2. Reconcile the spec against `HEAD` for F1-F12, rewriting each falsified claim to state the current
   contract with no chronology, no amendment block, no retraction paragraph.
3. Verify the move mechanically: `check_spec_glossary.py` exit 0, every link def resolves on disk,
   every in-page and cross-file anchor resolves, no moved substring survives in the spec.
4. Record byte counts before and after for Worker 0.

### Test additions / updates

None. This item writes no code and no test; `docs/builder/BUILD.md` `## Coverage is the maintainer's
gate` and the plan's own declarations put no test in the writable set.

### Implementation discretion items

- Whether `## Current state` is rewritten to `HEAD` or left as a `0.0.4` baseline. **Decided, not
  delegated:** the three bullets that were false at `HEAD` are rewritten; the bullets that describe a
  durable fact are kept. A "current state" section that is not current is the same defect F3 names at
  sentence scale.
- Whether the five-commit `## Implementation plan` framing survives. **Decided:** it stays. It is how
  the work was actually sequenced, and `e6907fa8` / `e836d72e` are the commits it names.

### Dispatched findings checklist

- [x] **F1** — no rationale companion exists; perform the `## Spec rationale extraction` MOVE.
- [x] **F2** — the `Status:` line's three-deleted-drafts / `READY-004` clause and the Slice-5
  `Cleanup` box ("Delete `docs/spec-relay_interfaces-3.md`") cannot both be current; both removed.
- [x] **F3** — `## Current state` says `interfaces` is in `DEFERRED_META_KEYS` and then contradicts
  itself parenthetically; the patched-over sentence is replaced, not annotated.
- [x] **F4** — Decision 3's `super(cls, cls).resolve_id_attr()` sketch is deleted (it is an infinite
  recursion at `HEAD`) and replaced by the shipped stamp-then-direct-scan default.
- [x] **F5** — Decision 9's `ext.optimize(...)` claim is deleted; both Decisions now say the same
  thing, which is that per-node optimizer consultation is not wired.
- [x] **F6** — Decision 2 and Slice 3 restated on both axes: `_is_relay_shaped` (interfaces entry,
  interface subclass, or direct inheritance) and `model._meta.pk.name` rather than the literal `id`.
- [x] **F7** — every resolver signature in `## Internal helper surface`, Decision 3, and the Slice-4
  checklist now matches `HEAD`, with the `TypeError` that forced the keyword-only `info` recorded in
  the rationale.
- [x] **F8** — Decision 3's queryset body sketch replaced by the shared sealed-visibility boundary
  (`initial_queryset` + `apply_type_visibility_sync` / `_async`).
- [x] **F9** — Decision 2, DoD 4, and the composite-pk edge case now state the `relay.NodeID[...]`
  escape hatch the gate honors, and why the gate asks Strawberry's scan directly.
- [x] **F10** — Decision 9 restated: `in_async_context()`, native `aget` / `afirst` / `async for`, no
  `sync_to_async`, no `acount`, plus the `SyncMisuseError` contract the spec never mentioned.
- [x] **F11** — `strawberry-graphql>=0.316.0` stated once (was `>=0.262.0` in two places), with the
  `Django>=5.2.16` floor beside it.
- [x] **F12** — every KANBAN id removed rather than renumbered; the deferrals now state the current
  contract, and the shipped/planned statuses were read from `docs/GLOSSARY.md`, not the board.

Three further falsified claims were found by this pass and fixed under the same obligation; they are
not F-numbered because the plan did not carry them. Each is recorded in the rationale as a claim the
spec may no longer make:

- [x] **W1a** — three `README.md #"For the current capability snapshot"` citations for a
  public-surface stability promise that paragraph does not make (`## Current state`, Decision 1,
  DoD 11). Re-anchored to `README.md #"The public names are stable"`, and the unsupported
  "through `0.1.0`" horizon dropped rather than re-attributed.
- [x] **W1b** — `id: relay.NodeID[str] = strawberry.field(...)`, offered twice as the annotation
  recourse, is refused at `HEAD`: the `0.0.6` Relay id-collision guard raises `ConfigurationError`
  for an assigned `id` on a Relay-shaped type. Replaced with the shipped spelling (annotate the
  target column, subscripted).
- [x] **W1c** — Decision 1 claimed a `types/base.py` block comment "already names this seam"; that
  comment was removed when the pass landed (`grep -c` returns 0 at `HEAD`). Citation deleted.

---

## Final verification (Worker 1)

### Summary

The spec-015 rationale companion now exists and the spec states the contract that holds at `HEAD`.
This is the one cycle in the series that performed a true `docs/builder/BUILD.md`
`## Spec rationale extraction` **MOVE** rather than a reconstruction or a restoration: three whole
sections were cut out of the spec and now exist only in the companion, and not one of the 34
"Justification" passages the spec carried at `HEAD` survives as such — the deliberative ones moved,
and the three implementation-relevant ones were restated in place as plain contract prose.

- Spec: **73,479 → 66,594 bytes** (627 → 595 lines), `wc -c` / `wc -l`.
- Rationale companion (new): **63,860 bytes**, 910 lines.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-015-relay_interfaces-0_0_5.md`
  → `OK: 18 terms - all have glossary entries and at least one spec link.` (exit 0).

### Nothing was skipped in the code — re-verified, not inherited

The plan's V1-V15 were re-derived rather than accepted, from `git show HEAD:<path>` copies taken into
`/private/tmp/claude-501/.../scratchpad/head/` (the tree is dirty with two concurrent sessions;
`git status --porcelain | wc -l` moved 189 → 192 during this pass). **No code defect was found and no
promised behavior is missing.** The three claims worth restating:

- **30 of 33 named tests exist under their own names**, each `grep -c "def <name>("` → 1.
- **The other three were built at `e6907fa8` and later relocated**, proven by diff:
  `git show e6907fa8 | grep '^+def '` carries all three;
  `git show 4f4db722 | grep '^-def test_relay_target_relation_planning_unchanged'` and
  `git show be9130e3 | grep '^-def test_relay_declared_type_emits…'` remove them.
- **The live twins assert what their names claim** — read, not grepped:
  `test_relay_genre_type_emits_node_interface_and_global_id_live` asserts `"Node" in interface_names`
  and `id` as `NON_NULL(ID)`; `test_mixed_relay_and_non_relay_no_interface_bleed_live` asserts `Node`
  on `GenreType`, absent from `ShelfType`, and `ShelfType.id != ID`.

### The adversarial obligation — one plan claim did not survive reading

`docs/builder/build-015-relay_interfaces-0_0_5.md` V12 records, as verified evidence, that "the live
suite pins forward-FK `select_related`". **It does not, at `HEAD`.**
`examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http`
keeps the name and asserts the opposite: its docstring reads "Before spec-034 this query planned a
single `select_related("item__category")` JOIN. With the cascade hooks active, `ItemType` and
`CategoryType` both define a custom `get_queryset`, so the optimizer downgrades each forward FK in
the `item -> category` chain to a windowed `Prefetch`", and the row pins a three-query Prefetch chain
with no JOIN. This is the third consecutive residual cycle whose one real drift is a test that kept
its name while its assertion changed.

Consequences, all discharged in this pass:

- Decision 7's fifth invariant no longer promises a `select_related` shape the tree does not produce.
  It states what holds: a target's Relay declaration does not change how relations to it are planned,
  because the optimizer reads `DjangoTypeDefinition`, and planning follows the same rules as for any
  other target — the `get_queryset` → `Prefetch` downgrade included.
- The Test plan names where the invariant is actually pinned (both live products rows, forward and
  reverse), with no claim about which ORM verb each plans.
- The **residual** is recorded for the final gate's deferred-work catalog, not silently closed: the
  retired `test_relay_target_relation_planning_unchanged` was an A/B row (Relay target under a
  non-Relay root, asserting `"category" in plan.select_related`, recovered with
  `git show 4f4db722^:tests/optimizer/test_relay_id_projection.py`). Its live replacements pin
  planning **across** Relay targets but not planning **unchanged relative to a non-Relay target**.
  Nothing regressed; the comparative assertion is simply no longer pinned, and restoring it is a test
  change this cycle is not authorized to make.

### Move verification

`docs/builder/worker-1.md` `### Performing the rationale move` rule 3.

- **The move is a cut.** Each moved block was grepped back against the spec after the edit, counting
  occurrences rather than matching lines: the spike fence
  (`Item.__bases__ = (Base, relay.Node)`), the borrowing posture's own markers
  (`Explicitly do not borrow`), and the risk register (`Preferred answer`, `Fallback`) —
  **0 in the spec, present in the companion** for each.
  `grep -c "Justification" docs/SPECS/spec-015-relay_interfaces-0_0_5.md` → **0**; the same grep
  against `git show HEAD:` the spec → **34** (8 of them in the borrowing posture).
  Three deliberately-surviving mentions are not move residue and were checked individually:
  `MAP_AUTO_ID_AS_GLOBAL_ID` (1) is Decision 2's own normative sentence, not the borrowing posture's
  bullet; `super(cls, cls)` (1) is Decision 3's explicit prohibition, which replaced the sketch;
  `ext.optimize` (1) is Decision 3 naming the upstream step it deliberately does not wire.
- **Sections cut, with measured sizes:** `## Borrowing posture` (6,210 bytes),
  `## Risks and open questions` (5,568 bytes), `## Pre-implementation spike outcome`, plus the
  per-Decision justification paragraphs and the falsified helper-signature fence.
- **Every Decision keeps a one-line pointer** (rule 1). Decisions 1, 2, 3, 6, 8 and the header block
  each name what moved and where via `[rationale companion][spec-015-rationale]`; Decisions 4, 5, 7,
  9 lost only text that is either restated normatively in place or recorded as a deleted false claim.
- **Falsified prose was deleted, not moved** (rule 2), in six places, each recorded in the rationale
  as a claim the spec may no longer make: the `super(cls, cls)` sketch, the helper-signature fence,
  the `is_awaitable` / `sync_to_async` / `acount` sentence, the three `README.md` citations, the
  `id = strawberry.field(...)` spelling, and the `types/base.py` block-comment citation.
- **Glossary anchors survive.** All 19 `[glossary-*]` defs are still used exactly once in the body.
  `#apply_cascade_permissions` was carried only by the moved risk bullet and was re-homed onto the
  `## Non-goals` cascade bullet in the same edit, preserving the `apply_cascade_permissions` term
  string the terms CSV matches. `check_spec_glossary.py` exits 0 with `OK: 18 terms`.
- **Anchors and links resolve.** A script check over both files reports no undefined reference, no
  unused definition, no missing link target on disk, and no dangling in-page anchor; every
  `spec-015-…md#<anchor>` def in the companion resolves to a heading that exists in the reconciled
  spec (one was corrected after the `## Out of scope` heading changed).
- **Layout gate.** `uv run python scripts/check_trailing_commas.py --check` on both files → exit 0
  (the markdown link-def scaffold check, which `ruff` does not cover). `ruff` was not run: neither
  writable file is Python, and a repo-wide invocation would rewrite a concurrent session's work.

### Checklist audit

Every box in `### Dispatched findings checklist` is `- [x]` and each was ticked against the reconciled
text, not against intent. No box is deferred. The three W1 items were found during the pass and
closed in it.

### Working-tree discipline

`HEAD` = `4c9e4e0dd66f64b6eb3e29dcf481a9bfb4ec6eae` throughout. Every source and test reading was
taken read-only via `git show HEAD:<path>` into a scratch path outside the repository; no
`git stash`, `git checkout`, `git restore`, or `git worktree` was used. This pass touched exactly
four paths: the spec, the new rationale companion, this artifact, and
`docs/builder/worker-memory/spec-015-worker-1.md`. `git status --porcelain -- docs/SPECS/` shows
`M docs/SPECS/spec-015-relay_interfaces-0_0_5.md` and
`?? docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md` as this cycle's only entries there;
`spec-014-*` and the `bld-014-*` set belong to the concurrent cycle and were neither edited nor
reverted. Nothing was committed.

### Notes for Worker 1 (spec reconciliation) — carried to R2 and the final gate

Four items for the `### Deferred work catalog`, none of them a code defect:

1. **The A/B relation-planning row** (above). No current test asserts that planning across a
   Relay-declared target matches planning across a non-Relay one.
2. **A stale cross-reference inside a shipped test docstring.**
   `tests/types/test_relay_interfaces.py::test_relay_node_strips_django_id_annotation` closes with
   "End-to-end coverage of the same suppression path lives in
   `tests/types/test_definition_order_schema.py`" — the file whose two Relay extensions `be9130e3`
   retired for the live twins. Accurate that end-to-end coverage exists, wrong about where. Editing
   it is a test-file edit, outside this cycle's writable set.
3. **The `[spec-011]` citation cluster (plan F14)** — eight sites, already homed on
   `TODO-ALPHA-051-0.0.15`, files dirty with a concurrent session. Confirmed still recorded, not
   stolen.
4. **The `public-exports` terms-CSV gap (plan F13)** — R2's item; this pass did not touch the CSV and
   left the anchor's body use in the Slice checklist intact, so R2's population is unchanged.

Two plan corrections for Worker 0, surfaced here because the plan is Worker 0's file:

- **V12's evidence sentence is wrong at `HEAD`** ("the live suite pins forward-FK `select_related`").
  V12's *conclusion* — the test was relocated, not skipped — is correct and independently re-proven
  above; only the characterization of the live replacement is false.
- **The commit table's ordering** lists `be9130e3` (2026-06-13) before `4f4db722` (2026-06-02). Both
  hashes and both descriptions are correct; only the row order implies a false sequence.

### Spec changes made (Worker 1 only)

All in `docs/SPECS/spec-015-relay_interfaces-0_0_5.md`, triggered by item R1. Line numbers are omitted
per `AGENTS.md` rule 27; each change names its section.

| Section | Change | Reason |
|---|---|---|
| Header block | `Status:` rewritten; `Predecessors:` re-pointed to `DONE-015-0.0.5`; `Rationale companion:` line added | F2; the move needs a pointer (rule 1) |
| `## Slice checklist` | Slice 3 retitled and its two sub-bullets restated; Slice 4 resolver signatures and helper list corrected; optimizer/schema test sub-bullets re-pointed at where the coverage lives; Slice 5 KANBAN bullet re-pointed; `Cleanup` box removed | F2, F6, F7, V11, V12 |
| `## Problem statement` | Framed as the `0.0.4` problem the slice solved; two board-id bullets restated | F12 |
| `## Current state` | Deferred-key, finalizer, and optimizer bullets rewritten to `HEAD`; `get_queryset` bullet re-anchored on the sealed boundary; glossary quotation aligned to the glossary's current wording | F3, F5, F8, W1a |
| `## Pre-implementation spike outcome` | **Section cut** to the rationale | F1 (move) |
| `## Non-goals` | Board ids removed; the cascade bullet now carries the `apply_cascade_permissions` glossary link | F12; anchor preservation |
| `## Borrowing posture` | **Section cut** to the rationale (6,210 bytes) | F1 (move) |
| `## User-facing API` | `resolve_id_attr` / `resolve_id` / `resolve_node` / `resolve_nodes` bullets restated; the `NodeID` override spelling corrected; the `get_queryset` subsection names the shared boundary | F5, F7, F8, W1b |
| Decision 1 | Justification block cut; `TypeError` wrap and the direct-inheritance path stated; block-comment citation deleted | F1 (move), W1c |
| Decision 2 | Rewritten on both suppression axes plus the composite-pk escape hatch and the direct-scan rationale | F6, F9 |
| Decision 3 | `super()` sketch deleted; stamp step, shipped signatures, keyword-only `info`, and the sealed-boundary routing stated; two justifications cut | F4, F7, F8, F1 (move) |
| Decision 4 | Two justifications cut; the six-helper named rejection added | F1 (move); completeness at `HEAD` |
| Decision 5 | No-new-state justification cut; Phase 2.5 gate restated on the resolved MRO; later cards' steps named | F1 (move) |
| Decision 6 | Three justifications cut; the `is_type_of` discriminator named | F1 (move) |
| Decision 7 | Two justifications cut; the relation-traversal invariant restated | F1 (move); the adversarial finding above |
| Decision 8 | Board ids removed; justifications cut | F12, F1 (move) |
| Decision 9 | Detection mechanism, `sync_to_async` / `acount`, and the `ext.optimize` claim deleted; `in_async_context`, native async ORM, and `SyncMisuseError` stated | F5, F10 |
| `## Internal helper surface` | Signature fence replaced with the shipped eight; lower bound corrected to `>=0.316.0` and stated once | F7, F11 |
| `## Implementation plan` | Commit 3 restated as pk-name suppression; commit 4's helper list completed; commit 5's board-id justification replaced; `file:line` phrasing dropped | F6, F7, F12, `AGENTS.md` rule 27 |
| `## Edge cases and constraints` | Composite-pk bullet states the escape hatch | F9 |
| `## Test plan` | Two relocated schema tests re-homed on their live twins; `test_relay_target_relation_planning_unchanged` replaced by the live rows that pin the invariant; four bullet descriptions corrected against the shipped assertions | V11, V12, F10, W1b, and the adversarial finding |
| `## Doc updates` | KANBAN bullets state the shipped card and the sequence advance | F12 |
| `## Out of scope` | Retitled `owned elsewhere`; every board id removed and the section re-pointed at the durable catalog | F12 |
| `## Definition of done` | Items 4, 5, 6, 10, 11 restated | F9, F12, W1a, V11/V12, the adversarial finding |
| Link definitions | `[spec-015-rationale]` added under `<!-- docs/SPECS/ -->` | the move's pointer |

### Final status

`final-accepted`.
