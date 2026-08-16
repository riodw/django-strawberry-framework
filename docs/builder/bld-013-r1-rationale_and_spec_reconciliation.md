# Build: R1 — Rationale companion and spec reconciliation (013 / real_m2m_coverage / 0.0.4)

Spec reference: `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md` (whole file; 59 lines before, 77 after)
Status: final-accepted

This is a **review-round-shaped** item of a residual-completion cycle, dispatched to Worker 1 alone
(`docs/builder/build-013-real_m2m_coverage-0_0_4.md` `## Dispatch record`). It writes no code, so
`docs/builder/BUILD.md` `### Isolation is non-waivable` does not bind it and this pass performs both
the work and its own final verification.

Writable set as dispatched, and nothing else was touched:

- `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md` (created)
- `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md` (reconciled)
- `docs/builder/bld-013-r1-rationale_and_spec_reconciliation.md` (this file)
- `docs/builder/worker-memory/spec-013-worker-1.md`

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately skipped: the package-wide AST
  inventory in `worker-1.md` `### Package-wide helper inventory before helper planning` exists to
  prevent duplicated *code* shapes before a builder writes them. This item's writable set is three
  Markdown files, it plans no helper, constant, validation branch, or test helper, and no pass of this
  cycle touches `django_strawberry_framework/`. Running the inventory would produce ~1,600 lines
  bearing on nothing in the diff.
- **Existing patterns reused.** The document shape is taken wholesale from the two closed residual
  cycles rather than invented: `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md`
  supplies the `## How to read this file` / `## Provenance of this record` / `## What the card
  actually did` / `## Entries keyed to the spec` / `## Reconciliation record` skeleton and the
  two-bullet `## Card snapshot` replacement; `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md`
  supplies the "name every test by `path::QualifiedName`" scope shape and the closing
  out-of-scope-fencing sentence. The stub-preamble argument is **cited, not restated**, from
  `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` `### The preamble —
  the stub's own justification, and an instruction that cannot be followed`, exactly as both prior
  cycles cite it.
- **New helpers justified.** None. No executable artifact of any kind.
- **Duplication risk avoided.** Two. (a) Re-arguing the stub preamble in a fourth file — avoided by
  the spec-007 cross-reference. (b) Restating the `library` model set in the spec, which would
  duplicate `examples/fakeshop/apps/library/models.py` and rot as that file grows — avoided by naming
  only the six edges this card owns and fencing the rest out in one sentence.

### Implementation steps

1. Re-derive V1-V8 at `HEAD` (`973d00b2`) from commits and blobs, never from the plan's table.
2. Recover the card's three commits, the retired fixture module, and the six-edge mapping.
3. Trace every later `library/models.py` addition and the app's own relocation to its commit.
4. Verify the `be9130e3` removal-and-replacement claim in both directions.
5. Create the rationale companion; write the spec's dispositioned text into it as *Moved*.
6. Reconcile the spec: header re-verification, pointer sentence, `## Card snapshot` reduction,
   `## Scope` rewrite, `## Planning note` and `## Other` removed, link scaffold rebuilt.
7. Verify the move: `check_spec_glossary`, anchors, inbound `spec-013` grep, disk-check every def,
   byte counts before/after.

Line numbers are pin-at-write-time navigational hints.

### Test additions / updates

None, and none is possible: this item's writable set contains no test file, and
`docs/builder/build-013-real_m2m_coverage-0_0_4.md` records that the cycle found no code defect and
dispatched no builder. No `pytest` invocation was run by this pass.

### Implementation discretion items

None. Every disposition in the diff is argued in the rationale companion with its rejected
alternatives; nothing was left to a later pass's taste.

### Dispatched findings checklist

One box per finding as `docs/builder/build-013-real_m2m_coverage-0_0_4.md` `### R1 findings` states
it. F8 is quoted as stated but was **recorded, not dispatched** by the plan; it is carried here
un-ticked with its deferral reason so the audit is complete.

- [x] **F1** — "No rationale companion exists. `docs/builder/BUILD.md` `## Spec rationale extraction`
  makes it the first substantive action of a build; specs 001-012 all have one."
- [x] **F2** — "The preamble paragraph ('This file is intentionally lightweight… Before implementation
  work starts from this file, expand it into the full builder-format spec') is deliberation about the
  file, and its instruction is **counterfactual** at `HEAD`: implementation shipped ten minor versions
  ago and no expansion preceded it."
- [x] **F3** — "`## Planning note` carries the single word `shipped` — a raw Kanban `planning_note`
  column render, not contract."
- [x] **F4** — "`## Other` is an undifferentiated dump of six heterogeneous Kanban rows — a 'why it
  matters' note, a restated scope bullet, and four `#### Files likely touched` paths — under a heading
  that names none of them."
- [x] **F5** — "`## Card snapshot` restates board fields (labels, priority, relative size) that belong
  to the Kanban database and are rendered into `KANBAN.md`."
- [x] **F6** — "`## Scope` names **nothing**: not the fixtures it retired, not the models that replaced
  them, not one test. The spec cannot be checked against the tree without recovering three commits
  from history."
- [x] **F7** — "`## Other`'s four file paths are a board **prediction** field
  (`#### Files likely touched`), not a record of the card's diff, and one is wrong for the card's own
  era… The list also omits every file the card actually deleted."
- [ ] **F8** — "The `[backlog]` link definition is unused (one occurrence in the file — the definition
  itself)." **Deferred, by the plan's own disposition** (`worker-0.md` `## Closing out a kanban card`:
  never partial-fix a pattern spanning surfaces). `KANBAN.md` catalogues 71 unused link definitions
  across 23 files, `[backlog]` in eight archived specs including this one, retired in one sweep by
  `TODO-ALPHA-052-0.1.0`. The definition is deliberately left in place and the decision is recorded in
  the rationale's entry titled "The [backlog] link definition — recorded, not fixed".

---

## Build report (Worker 1, acting for this item)

### Files touched

- `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md` — **created**, 0 -> 37,372 bytes /
  532 lines (`wc -c -l`). The durable deliberative companion: provenance of the move, the recovered card history,
  the V1-V8 re-derivation, eight entries keyed to spec headings and anchors, and the
  `## Reconciliation record` closing section.
- `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md` — **reconciled**, 1,669 -> 5,533 bytes,
  59 -> 77 lines.
- `docs/builder/bld-013-r1-rationale_and_spec_reconciliation.md` — this artifact.
- `docs/builder/worker-memory/spec-013-worker-1.md` — memory entry appended.

Nothing else. `git status --porcelain` after the pass shows **129** paths against **125** measured at
the start of this pass; the delta is this item's three (the memory file is `.gitignore`d and does not
appear), plus one further concurrent-session change that arrived mid-pass — the baseline moves, as the
plan's `## Baseline-dirty out-of-scope files` warns, and re-deriving it rather than quoting the plan's
124 is why the discrepancy is visible. Not one baseline-dirty path was edited, reverted, staged,
stashed, or `git checkout`ed.

### Verification run — V1-V8 re-derived, not accepted

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` binds this pass
to re-derive the plan's table. `HEAD` = `973d00b2c4cae3d3474dcd819b1c9a012d18bfe1`. Three needed
files are dirty with a concurrent session's work (`examples/fakeshop/test_query/test_library_api.py`,
`tests/types/test_definition_order.py`, `docs/GLOSSARY.md`), so each was read via
`git show HEAD:<path> > <scratch outside the repo>` — never from the working tree, and never via
`git stash` / `git checkout` / `git restore` / `git worktree`.

| # | Verdict | Command / symbol it came from |
|---|---|---|
| V1 | holds | `examples/fakeshop/apps/library/models.py` exists with `migrations/`; `examples/fakeshop/config/settings.py` #"apps.library.apps.LibraryConfig" |
| V2 | holds, with a corrected count | `git ls-tree -r HEAD --name-only \| grep -c "tests/fixtures/"` -> **0**; `grep -rn "tests_cardinality\|cardinality_models"` (excluding `.git`, `.venv`, `db.sqlite3`) -> **5** hits, all documentary (2 in `spec-011-…-rationale.md`, 3 in this cycle's plan). The plan's "zero hits outside `docs/builder/DONE/`" is wrong as a population statement; its finding is unaffected |
| V3 | holds | six-edge mapping re-read from `git show 73004d74:examples/fakeshop/library/models.py` and `git show HEAD:examples/fakeshop/apps/library/models.py` |
| V4 | holds, and covers more than the plan credits | `tests/types/test_definition_order.py::test_many_to_many_forward_and_reverse_relations_resolve` also asserts `BookType.__annotations__["shelf"] is ShelfType` (the forward-FK half); `::test_one_to_one_forward_and_reverse_relations_resolve` carries the O2O pair |
| V5 | holds | `tests/optimizer/test_definition_order.py::test_plan_relation_decisions_match_cardinality_after_finalization` body read at `HEAD`: `("prefetch","default")` for `Book.genres` / `Genre.books`, `("select","default")` for both O2O halves |
| V6 | holds | `^def test_` lists of `git show 67b07f79:<path>` and `git show HEAD:<path>` diffed; all eight names present |
| V7 | holds | `grep -c "library_book_genres"` on the `HEAD` blob -> **6** occurrences, three inside card-013 tests |
| V8 | holds, relocated | `examples/fakeshop/apps/library/tests/test_schema.py` carries both; created by `31642c9c` (2026-05-29) "tests: relocate example app tests into per-app folders" |

**The one later change that matters, verified in both directions.**
`tests/types/test_definition_order_schema.py::test_m2m_schema_shape_builds_with_real_library_models`
exists at `be9130e3~1` (four test functions) and not at `be9130e3` (one). The same commit adds
`examples/fakeshop/test_query/test_library_api.py::test_book_genres_m2m_renders_as_list_shape_live`
(`git show be9130e3 -- <path> | grep "^+def test_book_genres_m2m"` -> hit at diff line 291), whose
docstring names the retired test and which asserts the same `[GenreType!]!` shape by unwrapping
`NON_NULL -> LIST -> NON_NULL -> OBJECT GenreType` from live introspection. `be9130e3`'s own body
states the same-or-stronger rule this satisfies.

**Two plan figures corrected by measurement**, recorded in the rationale rather than silently fixed:

- library model count at `HEAD` is **11** (`grep -c "^class "`), not the plan's 12.
- the app relocation `examples/fakeshop/library/` -> `examples/fakeshop/apps/library/` happened at
  `a7ca9cc2` on **2026-05-07 17:58**, four hours after the card's last commit and the day before the
  `0.0.4` cut — not at a distinctly "later" split. F7's path claim is therefore true of the card's
  three commits and false of the release, and the rationale states it that way.

### Verification of the move (`worker-1.md` `### Performing the rationale move` rule 3)

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md`
  -> `OK: 1 terms - all have glossary entries and at least one spec link.` (exit 0). The term string
  `M2M traversal` is preserved verbatim so the one-row terms CSV still matches its `term` column, and
  the `[glossary-relation-handling]` ref-id and def are unchanged. The CSV was not edited.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` -> exit 0. Run in
  `--check` mode only, so neither file was auto-rewritten.
- **Ref-id audit, both files**, with code spans stripped before matching: zero undefined uses in
  either; the spec's only unused def is `[backlog]` (F8, deliberate); the rationale has no unused
  defs. **Every one of the 9 spec defs and 19 rationale defs was resolved against the filesystem and
  exists.**
- **In-page anchors.** The rationale's two spec-targeting anchors — `#card-snapshot` and `#scope` —
  both resolve to surviving `##` headings in the reconciled spec. No anchor points at a removed
  heading: the two entries keying to `## Planning note` and `## Other` say so in their first line and
  anchor the surviving section their subject bears on, following spec-012's rationale exactly.
- **No surviving cross-reference points into moved text without naming the rationale file.** The
  spec's header block carries the pointer sentence and `[spec-013-rationale]`; nothing else in the
  repository referenced the moved paragraphs.
- **Byte count:** spec **1,669 -> 5,533 bytes**, **59 -> 77 lines** (`wc -c -l`; before-figure from
  `git show HEAD:<path>`).

### Inbound `spec-013` references — swept, and what must not be fixed here

`grep -rn "spec-013"` across the tree (excluding `.git`, `.venv`, `__pycache__`, and the binary
`db.sqlite3`):

- `KANBAN.md:134`, `KANBAN.md:4501` — the card's `SpecDoc` link to this file. Path unchanged; still
  correct.
- `KANBAN.md:340` — the unused-link-definition catalogue naming `spec-013`. Still correct: `[backlog]`
  is deliberately kept.
- **`KANBAN.md:341` — now stale.** It lists `spec-013` among "four archived stubs still carry the
  boilerplate … preamble". This pass removes that preamble, so the correct figure becomes **three**.
  **Not fixed here, and it must not be:** `KANBAN.md` renders from `examples/fakeshop/db.sqlite3`,
  which is dirty with a concurrent session's uncommitted work, so the fix is an ORM edit plus a
  regenerate that would publish rows that have not landed (`START.md` `## Concurrent sessions`; the
  plan's F12 disposition and the cycle's "no database write, no generator" rule). Routed to the
  deferred-work catalog.
- **`docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md:28` and `:256` — now
  stale** in the same way (the same four-stub list, and the eight-spec `[backlog]` list which remains
  correct). A prior cycle's committed rationale is outside this item's writable set. Routed to the
  deferred-work catalog with `KANBAN.md:341`.
- `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md:348` — the `[backlog]`
  eight-spec list. Still correct.
- `docs/builder/DONE/build-001-django_types-0_0_1.md:151` — "M2M coverage shipped | spec-013". Still
  correct, and this pass strengthens it.
- **False positives, recorded so a later sweep does not mistake them for inbound references to card
  13:** `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` (3 body uses + 1 def) uses the ref-id
  `[spec-013]` for a link that resolves to `spec-017-deferred_scalars-0_0_6.md`; and
  `docs/SPECS/spec-018-…md:175` / `spec-019-…md:133` name a "`spec-013-deferred_scalars`" from before
  the board renumber. None names this card; none is broken by this rewrite; none is fixable without
  opening a cross-surface renumber cluster.
- Prior cycles' `docs/builder/DONE/build-0**.md` and `docs/builder/build-013-…md` hits are cycle
  records, out of scope by the dispatch.

### Failability proofs

None; this pass introduced no new boundary. Its writable set is three Markdown files and it added no
guard, gate, or rejection path.

### Hot-path budget

Not applicable; plan declares no hot path (`docs/builder/build-013-real_m2m_coverage-0_0_4.md`
preamble: "Hot-path declaration: none").

### Floor verification

Not applicable; plan declares floor-verification scope none — no item of this cycle touches
executable code.

### Implementation notes

- **The six-edge mapping is stated in the spec as `cardinality -> library edge`, not as
  `retired edge -> library edge`.** The retired left-hand column is history and belongs in the
  rationale, where it is; the cardinality is the durable axis and is what a reader checks the models
  against. The rationale carries the full three-column form.
- **The spec names eleven test functions and no line numbers.** `AGENTS.md` rule 27 forbids `path:NN`
  in a spec, and `path::QualifiedName` fails loudly on rename where a count or a bare filename fails
  silently — which is the property that let this pass detect the `be9130e3` relocation at all.
- **The closing out-of-scope sentence is in the spec, not only in the rationale.** A reader opening
  `models.py` finds eleven models where the spec names six edges; without the fence the honest reading
  is that the spec is stale. It mirrors spec-011's scalar-override-semantics fence.
- **`## Card snapshot` keeps the card-identity bullet rather than being deleted outright**, because
  this spec exists to be that card's `SpecDoc` target and the rationale's entries resolve to its
  anchor. Precedent: spec-011 and spec-012, unchanged.

### Notes for Worker 3

No Worker 3 pass is dispatched for this item (`## Dispatch record`: "Worker 1 only"). The
verification a reviewer would run is above, with the command for each row.

### Notes for Worker 1 (spec reconciliation)

Two items R2 and the final gate must carry forward, both already routed above:

- The stale four-stub preamble count in `KANBAN.md:341` and
  `docs/SPECS/appx/spec-011-…-rationale.md:28`. Blocked on a dirty `db.sqlite3`; the next sweep should
  measure **three**.
- F8's `[backlog]` cluster, unchanged and still owned by `TODO-ALPHA-052-0.1.0`.

---

## Final verification (Worker 1)

- **Dispatched findings checklist:** F1-F7 `- [x]`, each confirmed against the diff below. F8 `- [ ]`
  with its deferral reason recorded in the checklist entry and under
  `### Spec changes made (Worker 1 only)`. No box is ticked without a matching edit, and no landed fix
  is left un-ticked.
- **Every planned step implemented.** Steps 1-7 all ran; none was rejected.
- **DRY check against prior accepted work:** the rationale reuses spec-012's section skeleton and
  cites spec-007's preamble argument instead of re-arguing it — the specific duplication the two prior
  cycles' custodians called out. No new duplication introduced; the spec deliberately does not
  duplicate `library/models.py`'s model list.
- **Relocation claims proven, not accepted** (`worker-1.md` `### Verifying relocation / promotion
  claims`): both the `be9130e3` test relocation and the `31642c9c` per-app test move were verified by
  blob comparison at the commit and its parent, quoted above.
- **Existing tests:** none run, and none owed — this item's writable set contains no test and no
  source. No `--cov*` flag was used anywhere in this pass.
- **Staged-anchor sweep** (`worker-1.md` `## Final verification job` step 6):
  `grep -rn 'TODO(spec-013' .` returns exactly one hit, this artifact's own quotation of the command
  on the line above. No staged anchor exists anywhere in the tree; nothing to remove.
- **Final status:** `final-accepted`.

### Summary

Created the spec-013 rationale companion (37,372 bytes) and reconciled the spec from a 1,669-byte
Kanban-render stub into a 5,533-byte checkable contract. The spec now names the retired unmanaged
`tests_cardinality` app and its five models, the six relation cardinalities and the real `library`
edges that carry them, and all eleven test functions that pin them at `HEAD` by
`path::QualifiedName` across the package tier, the live `/graphql/` tier, and the per-app example
tier — and fences the `library` app's later growth out of this card's scope. The boilerplate preamble
and `## Planning note` were moved into the rationale; `## Other` and the board-metadata bullets were
deleted as falsified. Independently re-derived V1-V8: **nothing spec-013 promised is missing at
`HEAD`**, and the one card-013 test that no longer exists where it was written was replaced at
`be9130e3` by a strictly stronger live HTTP twin — recorded in the rationale, stated in the spec as
current location only.

### Spec changes made (Worker 1 only)

Paths and line ranges are of the reconciled file at `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md`
unless the reason names the removed original.

| Spec lines | Change | Reason |
|---|---|---|
| 1-5 | header block re-verified, left unchanged | `worker-1.md` `## Spec status-line re-verification`: title, target release `0.0.4`, `Status: shipped`, and owner are all still accurate at `HEAD`; the ten intervening minor versions falsified none of them. No predecessor reference exists to update. |
| 7 | pointer sentence added, replacing the removed preamble paragraph | F1/F2. Names what moved to the rationale and where, per `worker-1.md` rule 1; the counterfactual "expand it into the full builder-format spec" instruction is gone. |
| 9-12 | `## Card snapshot` reduced to two bullets | F5. Board metadata belongs to the Kanban DB and had already drifted (the spec listed three labels; the card carries four at `HEAD`). Card identity retained because this file is the card's `SpecDoc` target. |
| (removed) `## Planning note` | section deleted; heading + body moved to the rationale | F3. Its one-word body duplicates the `Status:` line one screen above it. |
| 14-46 | `## Scope` rewritten from two unnamed summaries into a named substitution, a six-edge cardinality table, and eleven `path::QualifiedName` test citations across three tiers | F6, and the core of the item. Every claim is now greppable against the tree at `HEAD`. |
| 46 | closing sentence fencing the `library` app's later additions out of scope | F7 and the dilution finding: the app carries 11 models at `HEAD` against the card's 7, including a **second** M2M (`Shelf.alt_branches`). The spec's M2M edge is `Book.genres` / `Genre.books`. |
| (removed) `## Other` | heading and all six bullets deleted | F4/F7. One triage note, one duplicate of `## Scope`, and four board-*prediction* paths that are not the card's diff and omit every file it deleted. Dispositioned bullet-by-bullet in the rationale. |
| 48-77 | link-definitions block rebuilt | All ten canonical group headers present and in order, alphabetical within each group, paths resolved from `docs/SPECS/`. Added `[spec-013-rationale]`, `[library-models]`, `[test-library-api]`, `[test-library-schema]`, `[test-types-definition-order]`, `[test-optimizer-definition-order]`; every def disk-checked. |
| 51 | `[backlog]` kept | **F8 deferral.** Unused (1 occurrence, the def itself), but it is one file of a 71-definition / 23-file pattern owned by `TODO-ALPHA-052-0.1.0`; partial-fixing leaves the surface divergently rather than uniformly wrong (`worker-0.md` `## Closing out a kanban card`). |

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
