# Build: R1 — rationale companion and spec reconciliation (spec-014)

Spec reference: `docs/SPECS/spec-014-testing_shift-0_0_4.md` (whole file, 27 lines at entry / 39 at exit)
Status: final-accepted

This is a **Worker-1-only item** on a residual-completion cycle: it writes Markdown only, touches no
package source and no test, and is dispatched with no Worker 2 and no Worker 3 pass
(`docs/builder/build-014-testing_shift-0_0_4.md` `## Dispatch record`). Per that dispatch, this
artifact carries a **combined Plan + Final-verification block** rather than the four-pass shape.

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** Not applicable in the code sense — this item writes no Python and
proposes no helper — but the equivalent was performed on the documentary side, which is where this
item's duplication risk lives. The three sibling residual cycles' rationale companions
(`docs/SPECS/appx/spec-011-…-rationale.md`, `…spec-012-…`, `…spec-013-…`) were read for shape, and
the shapes searched for were: the stub-preamble argument, the out-of-scope fence for a file later
cards kept extending, and the provenance ledger. Findings:

- **Existing patterns reused.** `spec-013`'s rationale supplies two reusable shapes, and both are
  cited rather than re-argued: (a) the `git log -S<symbol> --follow` traced table that fences off a
  later-grown module, reused for both the `apps/library/models.py` growth and the `apps/` app-package
  growth; (b) the `## Provenance of this record` ledger distinguishing *moved* / *added in exchange*
  / *deleted outright*.
- **New shape justified.** One, and only one: `## The recovered design record`. No sibling rationale
  has it, because no sibling had a design record to recover. Its single responsibility is to hold the
  ten sections `67b07f79` deleted, each under its original heading, each stating the current section
  it bears on. It is a section rather than a separate file because
  [`BUILD.md`][build] `## Spec rationale extraction` names exactly one companion per spec.
- **Duplication risk avoided.** The obvious near-copy is re-arguing the archived-stub preamble
  disposition that `spec-007`'s rationale settled and `spec-011` / `spec-012` / `spec-013` each
  cross-referenced. It does not arise here: spec-014 is not a stub and carries no such preamble. The
  second risk is restating `AGENTS.md` rule 7's test-placement tiers inside the spec, which would
  create a second drifting source; the reconciliation explicitly declines to, and the recovered
  `## Test placement rules` entry says why.

### Implementation steps

1. Re-derive V1-V10 against `HEAD` rather than accepting the plan's verification pass
   (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`). Files dirty with
   concurrent work are read via `git show HEAD:<path>` into a scratch path outside the repo.
2. Recover `git show 73004d74:docs/spec-testing_shift.md` and decide the `path:NN` handling before
   any of it is transcribed.
3. Create `docs/SPECS/appx/spec-014-testing_shift-0_0_4-rationale.md` on the sibling companions'
   shape, with `## The recovered design record` as the added section.
4. Rewrite each drifted spec claim present-tense; no amendment block, no chronology.
5. Disk-check every link definition from each source file's own directory; re-run
   `check_spec_glossary.py`.

Line numbers in this artifact are pin-at-write-time navigational hints.

### Test additions / updates

None. No test file is in this item's writable set, and no test run is needed: the item lands
Markdown only. The two mechanical gates that do apply are `scripts/check_spec_glossary.py` and the
`source-layout` markdown-scaffold check; both are recorded under `### Validation run`.

### Implementation discretion items

- The rationale file's internal section ordering (recovered record before the per-section entries,
  or after). Decided at write time: **before**, because the entries reference it.
- Blockquote versus fenced-block for each recovered section. Decided per section by whether it
  contains a `path:NN` reference; the rule and its justification are written into the file.

### Dispatched findings checklist

This cycle is a review round in shape (no spec `## Slice checklist` exists), so the checklist is the
plan's F1-F10, quoted as the plan states them, plus the V-row obligation.

- [x] **V1-V10 re-derived rather than accepted**, with any figure that does not reproduce recorded.
- [x] **F1** No rationale companion exists, and this spec had a real deliberative layer to lose.
- [x] **F2** `## Status` claims "The original spec remains here as the design record" — false.
- [x] **F3** Spec says `pytest.ini` sets `DJANGO_SETTINGS_MODULE = config.settings`; at `HEAD` it is
  `config.test_settings`.
- [x] **F4** Spec says the project schema "constructs
  `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`"; at `HEAD` it is
  `DjangoSchema(query=Query, mutation=Mutation, config=strawberry_config(), extensions=[lambda: _optimizer])`.
- [x] **F5** Spec names two domain apps; at `HEAD` there are six.
- [x] **F6** Spec names the `library` app's seven models as though they are its content; the module
  holds 11 classes at `HEAD`. Needs an out-of-scope fence.
- [x] **F7** The spec's description of the autouse `_reload_project_schema_for_acceptance_tests`
  fixture describes a per-test full reload that no longer exists.
- [x] **F8** `## Remaining follow-ups` says seven Layer-3 features "remain non-goals for this slice
  and should land under their own specs"; five have since shipped.
- [x] **F9** The strictness-mode follow-up's stated condition has had its premise change
  (`DjangoDebugExtension` shipped `0.0.14`); the disposition has not.
- [x] **F10** The custom-`Prefetch(...)`-objects deferral still holds and is correct — verify before
  relying on it, do not "fix" a true claim.

---

## Final verification (Worker 1)

### Baseline re-derived

`HEAD` at this pass is `676f10d29e9e331c30155dfd6ba73adca4c83372`, **not** the
`973d00b2c4cae3d3474dcd819b1c9a012d18bfe1` the build plan recorded. Two concurrent-session commits
landed between plan and pass: `fd0c7327` (filter/order dynamic-Meta hashing) and `676f10d2`
(write-flavor Meta gates). `git diff --name-only 973d00b2..HEAD` touches twelve files, all under
`django_strawberry_framework/` and `tests/`, **none of them evidence for any V-row or F-finding**.
`git status --porcelain | wc -l` is still **174**, and
`git status --porcelain docs/SPECS/spec-014-testing_shift-0_0_4.md` is empty — the spec was clean at
`HEAD` before this pass, so this cycle's edit to it is unambiguously attributable.

Files this item needed to read that are baseline-dirty with concurrent work:
`examples/fakeshop/test_query/test_library_api.py` (read via
`git show HEAD:… > <scratch>/test_library_api.head.py`, scratch path outside the repo) and
`docs/GLOSSARY.md` (not read for content; only `check_spec_glossary.py` touches it, read-only).
Nothing dirty was edited, reverted, staged, stashed, or `git checkout`ed.

### V1-V10 re-derivation

All ten rows reproduce; the full evidence table is in the rationale file's
`### Nothing was skipped in the code — re-derived, not accepted`, which is the durable record. **No
code defect exists.** Everything spec-014 promised is present at `HEAD`.

### What Worker 0's plan got wrong

Four figures beside the V-rows do not reproduce as written. None changes a finding; all four would
have propagated.

1. **V3 says "nine relation shapes"; the spec names eight** — forward FK, reverse FK, forward
   OneToOne, reverse OneToOne, forward M2M, reverse M2M, a choice field, a nullable scalar field.
   There is no ninth. All eight verified present against the field declarations.
2. **`## Why this cycle exists` and F1 call the destroyed catalogue a "ten-bullet" candidate
   catalogue; it is eight bullets** carrying 37 candidate refs
   (`awk '/^## High-value/,/^## Tests that should/' | grep -c "^[A-Z]"` -> 8;
   `… | grep -o "tests/[a-z_/]*\.py:[0-9]*" | wc -l` -> 37).
3. **V1's "9 hits, all documentary" is a moving population, not a stable count.** It now returns
   roughly twice that, the additions being two concurrent residual cycles' artifacts written since
   the plan. The finding — zero *live* hits — is unaffected, and the rationale states the live-hit
   count instead of the total so it cannot rot the same way.
4. **The commit table omits that `a7ca9cc2` also edited the spec.** `git show a7ca9cc2 --
   docs/spec-testing_shift.md` is a real +10/-8 diff. This is the substantive one: the shipped-state
   summary `67b07f79` wrote described the **flat** layout and was stale within four hours, and the
   two `## Remaining follow-ups` bullets (strictness mode, `Prefetch(...)`) that F9 and F10 are about
   were authored at `a7ca9cc2`, not at the overwrite. The plan attributes the whole current body to
   one commit. Corrected in the rationale's commit table.

One plan figure reads as wrong and is not: **V9's "-61/+27 lines"**. Read as line counts it is exact
(`git show 73004d74:… | grep -c ''` -> 61; the same at `67b07f79` -> 27). Read as a `git diff --stat`
it is not (the stat is `25 insertions(+), 59 deletions(-)`; `wc -l` reports 60 for the original
because it has no trailing newline). Both readings are recorded so the next reader does not
"correct" the right number.

### Spec changes made (Worker 1 only)

Whole-file reconciliation of `docs/SPECS/spec-014-testing_shift-0_0_4.md`; 6,282 bytes before,
8,002 after. Per-section changes and the reason for each are in the rationale's
`### Section by section`. The five that change a claim:

| Section | Change | Trigger |
|---|---|---|
| `## Status` | false design-record claim replaced by a present-tense shipped statement + the one-line rationale pointer | F1, F2 |
| `## Implemented outcome` → `## Shipped outcome` | renamed; `config.test_settings` corrected; constructor transcription replaced by the finalize-once + one-`DjangoOptimizerExtension`-instance invariant with the rest assigned to its owning specs; app list and model list fenced to what this card contributes, the model fence covering fields as well as classes | F3, F4, F5, F6 |
| `## Live HTTP coverage` | fixture paragraph rewritten to the `schema_reload.py` single-siting, six-module dependency-safe rebuild, module-scoped autouse fixture, and function-scoped identity-fingerprint guard | F7 |
| `## Resolved risks and decisions` → `## Settled decisions` | renamed (the old heading implies a chronology whose risks were deleted from the document); all four resolutions verbatim | reconciliation |
| `## Remaining follow-ups` | Layer-3 sentence rewritten as a scope fence with no temporal frame; strictness bullet restated with its condition intact and the enabling surface named; `Prefetch(...)` bullet restated present-tense with its verification explicit | F8, F9, F10 |

Rename safety: `grep -rn "spec-014-testing_shift"` across the tree returns only whole-file references
(`KANBAN.md` x3 and this cycle's own artifacts). No inbound in-page anchor pointed at either renamed
heading.

### Rationale companion created

`docs/SPECS/appx/spec-014-testing_shift-0_0_4-rationale.md`, 59,517 bytes (`wc -c`). It carries the sibling companions'
shape plus one section none of them has, `## The recovered design record` — the ten sections
`67b07f79` deleted, restored verbatim from `git show 73004d74:docs/spec-testing_shift.md`, each keyed
to the current spec section it bears on.

**The `path:NN` handling, stated because the prompt required it be deliberate.** `AGENTS.md` rule 27
bans raw `path:NN` in standing docs and this file is one. The recovered
`## High-value migrations to HTTP tests` is 37 such refs across 8 bullets. Three dispositions were
weighed and the reasoning is written into the file's
`### Why the recovered catalogue is fenced rather than quoted inline`: translating each ref to the
symbol-qualified form was rejected (the numbers name 2026-05-07 lines in files rewritten many times
since, so any translation is a guess that would read as measurement, and it destroys the record of
what the author was looking at); summarizing the catalogue was rejected (a summary of a priority
ordering is not a priority ordering); **reproducing it verbatim inside a fenced code block, labelled
as a quotation of a named blob and accompanied by the recovery command, was adopted.** A fenced block
renders verbatim as example content and is explicitly not a live reference
(`START.md` `## Markdown link convention`), so what sits inside it is quotation of a primary source
rather than a reference this document asserts. Rule 27 governs refs a doc makes. The same fencing is
applied to `## Migration strategy`, the one other recovered section naming a path that reads as a
reference; the seven sections carrying no `path:NN` are blockquoted.

**Three findings the recovery produced that no F-row anticipated**, each a live constraint that was
destroyed rather than mere deliberation, and each recorded in the rationale:

- The `## Proposed example app` section's last sentence — "Type declarations should intentionally
  exercise awkward definition orders in at least one module" — is an instruction about how
  `apps/library/schema.py` must be written. A later editor tidying that module into dependency order
  would silently retire finalization coverage, and nothing outside git history said so.
- `## Risks and open decisions` is the premise set for all four of the spec's surviving settled
  decisions. With the risks deleted, each resolution reads as an arbitrary preference — including the
  `CaptureQueriesContext` broad-SQL-shape rule, which is a live constraint on anyone adding an
  assertion to the live suite.
- Risk 4's deferral of plan introspection is explicitly conditioned on a test-only extension being
  "not recommended for the first migration". That is a stronger and more specific statement of F9's
  premise change than the spec's summary carried, and it is the reason the reconciled bullet keeps
  the condition rather than deleting it as met.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-014-testing_shift-0_0_4.md`
  -> `OK: 7 terms - all have glossary entries and at least one spec link.` **Pass**, and unchanged
  from entry. Each of the seven `term`-column strings verified to survive verbatim in the rewritten
  body by per-term `grep -c`: `choice enum`, `DjangoConnectionField`, `DjangoOptimizerExtension`,
  `DjangoType`, `finalize_django_types`, `OptimizerHint`, `Strictness mode` — all ≥ 1.
- `uv run python scripts/check_trailing_commas.py --check <both files>` -> **pass**, no output. Both
  carry the `<!-- LINK DEFINITIONS -->` delimiter and all ten canonical group headers in order.
- Link definitions disk-checked from each source file's own directory, not assumed: 13 paths from
  `docs/SPECS/appx/` (`../../../` root, `../../` docs, `../` docs/SPECS, bare sibling under `appx/`)
  and the one added def from `docs/SPECS/`. All resolve. This is the depth trap a same-named file one
  level up masks, so it was checked by `[ -e ]` per path rather than by reading.
- In-page anchors: the rationale's eight `#…` anchors into the spec were checked against the spec's
  seven `##` headings plus `#status`. All resolve.
- No `pytest` run and no coverage-shaped flag in any pass. No test is in this item's writable set.
- **Floor verification: not applicable.** The plan declares floor-verification scope `none`; this
  item touches no executable code at all.
- **Hot-path budget: not applicable.** The plan declares no hot path; this item writes Markdown only.
- **Failability proofs: none; this pass introduced no new boundary.** It introduced no code.
- `git status --short` after the pass shows exactly three paths this item owns as changed or new:
  `docs/SPECS/spec-014-testing_shift-0_0_4.md`,
  `docs/SPECS/appx/spec-014-testing_shift-0_0_4-rationale.md`, and this artifact — plus
  `docs/builder/worker-memory/spec-014-worker-1.md`, which is gitignored. Nothing else moved by this
  pass.

### Deferred

- **F14 (the duplicate `#### Scope` bullet on the rendered `DONE-014-0.0.4` card).** Not this item's;
  it is R2's, and the plan already catalogues it as blocked on a dirty `examples/fakeshop/db.sqlite3`.
  Restated in the rationale's `### What this cycle deliberately did not fix` so the disposition
  survives the cycle. **This cycle makes no database write and runs no generator.**
- **`docs/builder/DONE/build-008-definition_order_independence-0_0_4.md` cites spec-014 for an object
  it does not own** — almost certainly card-renumber rot. A closed cycle's archived artifact, outside
  this item's writable set. Recorded in the rationale, not fixed; it belongs in the final gate's
  deferred-work catalog.

### Summary

The spec now states the current contract of the test-placement shift in the present tense, with the
four drifted claims corrected and the two over-broad ones fenced to what card `DONE-014-0.0.4`
actually contributed. Its false `## Status` claim is gone. The design record that claim wrongly
promised — ten sections destroyed in place by the card's own sibling commit — is restored in the new
rationale companion, keyed section by section to the spec, alongside the rejected alternatives, the
cause commit for every change, and every claim the spec may no longer make. No code defect was found;
everything spec-014 promised is present at `HEAD`.

Final status: `final-accepted`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build]: BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
