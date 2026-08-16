# Build: Item R1 — rationale companion and spec reconciliation

Spec reference: `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` (whole file, 60 lines at `054de9dd`)
Plan reference: `docs/builder/build-011-stale_placeholder_cleanup-0_0_4.md` `## Worker-0 verification pass` (F1-F8)
Status: final-accepted

This is a **combined plan + build + final-verification pass performed by Worker 1 alone**, authorized
by the plan's `## Dispatch record`: an item that changes only the spec and its rationale companion is
Worker 1's, and both files are Worker 1-owned by `docs/builder/BUILD.md` `## Spec reconciliation` in
any case. No Worker 2 or Worker 3 pass is dispatched for this item because it writes no source and no
test — `### Isolation is non-waivable` binds a pass that writes code, and this pass writes none.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable in the code sense: this item adds no Python and no
  test, so `### Package-wide helper inventory before helper planning` has no candidate surface. The
  documentary equivalent was run instead — the closest precedent,
  `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` (also a
  card-snapshot stub, also `0.0.4`), was read end to end before either file was written, together
  with its reconciled spec body.
- **Existing patterns reused.** The rationale file's shape is spec-007's: a `## How to read this
  file` preamble, `## Provenance of this record`, `## Entries keyed to the spec` with one entry per
  spec heading and an anchored `Spec:` / `Bears on` line, and a `## Reconciliation record` appended
  below it. The reconciled spec body reuses spec-007's `## Card snapshot` two-bullet shape verbatim
  in structure (card identity + a sentence handing the board fields back to the Kanban DB) and its
  one-line rationale-pointer sentence.
- **Duplication risk avoided.** Two arguments are already owned by spec-007's rationale and are
  **cross-referenced, never retold**: the three-way stub-shape choice (expand / delete /
  keep-and-reconcile) behind the boilerplate preamble, and the board-wide migration that retired the
  `Other` card section. `BUILD.md`'s no-padding instruction and the single-ownership rule point the
  same way — a second telling of a settled argument is a copy that goes stale.
- **New shared shape justified.** None. Nothing here is extractable; two Markdown files are the
  whole deliverable.

### Implementation steps

1. Recover the card's real history from git and verify every fact independently of the plan's
   verification table (`git show 118f71a1~1:<path>`, `git show a357c68c --stat`, `git log -S`).
2. Create `docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md` on spec-007's
   shape, carrying the extraction record and the reconciliation record.
3. Rewrite `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` so every sentence states the
   current contract, with all ten canonical link-definition group headers preserved.
4. Verify: `check_spec_glossary.py` exits 0, the scaffold check passes, every rewritten path is
   disk-checked from the writing file's own directory.

### Test additions / updates

None, and none is possible: this item lands no code. The code contract was verified by the plan's
`### V1-V5` and independently re-derived by this pass (below) as read-only evidence for spec claims.

### Implementation discretion items

- Whether the three surviving coverage files are cited as reference-style links or bare code spans.
  Decided at write time: links (they exist and the `<!-- tests/ -->` group was empty), while the
  three **retired** placeholders stay bare `path::QualifiedName` symbol paths, since a link would
  promise a symbol the file no longer contains.

### Dispatched findings checklist

- [x] **F1** — no rationale companion exists; `docs/builder/BUILD.md` `## Spec rationale extraction`
      makes it the first substantive action of a build.
- [x] **F2** — the preamble paragraph is deliberation about the file and its instruction is
      counterfactual at `HEAD`.
- [x] **F3** — `## Planning note` carries the single word `shipped`, a raw Kanban column render.
- [x] **F4** — `## Other` is an undifferentiated dump of heterogeneous Kanban rows under a heading
      that names none of them.
- [x] **F5** — `## Card snapshot` restates board fields that belong to the Kanban DB.
- [x] **F6** — `## Scope` bullet 2 claims a kept scalar-override skip that no longer exists.
- [x] **F7** — `## Scope` bullet 1 names no skip, so the spec cannot be checked against the tree.
- [ ] **F8** — the unused `[backlog]` link definition. **Deliberately not fixed**; see
      `### Spec changes made (Worker 1 only)` and the deferred-work note below.

---

## Final verification (Worker 1)

### Evidence re-derived at this working tree

Every fact restated in the spec or the rationale was measured by this pass rather than carried over
from the plan. The disagreements are recorded because a stated count reads as measured
(`BUILD.md` `## Claims are proven mechanically, never accepted on prose`).

| Claim | Command | Result |
|---|---|---|
| three retired placeholders and their verbatim skip reasons | `git show 118f71a1~1:tests/types/test_base.py`, `… :tests/optimizer/test_extension.py` | confirmed, quoted verbatim in the rationale |
| none of the three names survives | `grep -rn <names> tests/ examples/ django_strawberry_framework/` | 0 |
| no skip/xfail under the two directories | `grep -rEn "pytest\.mark\.(skip\|xfail)" tests/types/ tests/optimizer/` | 0 |
| the three replacement files are `118f71a1`'s | `git show 118f71a1~1:<path>` absent, `git show 118f71a1:<path>` present | confirmed for all three |
| the kept placeholder's skip reason was rewritten one commit later | `git show 1d9ca597 -- tests/types/test_base.py` | confirmed; before/after quoted |
| the kept placeholder was retired at `0.0.6` | `git show a357c68c --stat`, `git show a357c68c -- tests/types/test_base.py` | 33 deleted lines from `test_base.py` |
| replacement sibling count | `git show a357c68c -- tests/types/test_definition_order.py \| grep -c "^+def test_"` | **18**, not the plan's "six siblings" |
| the M2M fixtures changed hands twice | `git log -S`, per-commit `git show <c>:tests/optimizer/test_definition_order.py` | `73004d74` added the managed `library` app; `1057ddc2` re-pointed the tests and deleted `tests/fixtures/cardinality_models.py`; `a7ca9cc2` moved the import to `apps.library.models` |
| card 11's `planning_note` is empty | `sqlite3` on a **copy** of `examples/fakeshop/db.sqlite3` in the scratchpad | `11\|Stale placeholder cleanup\|` |
| the fourth label `internal` and its date | `git log -S 'Labels: \`cleanup\`, \`docs\`, \`internal\`, \`tests\`' -- KANBAN.md` | `2baf93b5`, 2026-06-09 |
| files sharing the unused `[backlog]` definition | per-file `grep -c '\[backlog\]'` over `docs/SPECS/*.md` + `appx/*.md`, then repo-wide | **8**, not the plan's "fifteen" |
| spec byte/line counts | `wc -c` / `wc -l`, and `git show 054de9dd:<spec>` | 1,797 / 60 -> 3,440 / 53 |

The database was read from a **copy** in the session scratchpad; `examples/fakeshop/db.sqlite3` was
never opened for writing, and no generated doc (`KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`) was
touched. No file outside this item's writable set was modified: `git status --short` shows exactly
the two written docs plus this artifact (the namespaced memory file is under the gitignored
`docs/builder/worker-memory/`), against a baseline that is otherwise the concurrent sessions' — 111
dirty paths at the end of this pass, up from the 95 the plan enumerated, none of them touched,
reverted, or staged (`AGENTS.md` rule 34).

### Verification commands run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md`
  -> `OK: 2 terms - all have glossary entries and at least one spec link.` (exit 0)
- `uv run python scripts/check_trailing_commas.py --check <the spec> <the rationale>` -> exit 0
  (link-def scaffold, all ten group headers, ASCII rules)
- disk-existence check of every rewritten path, from `docs/SPECS/` for the spec and
  `docs/SPECS/appx/` for the companion -> all 15 targets resolve
- no `pytest` run: this item has no test, and the plan declares floor-verification scope `none` and
  hot-path `none` (Markdown only)

### Summary

The spec-011 stub is now a contract. Its deliberative layer — the boilerplate preamble and the
`## Planning note` section — was **moved** into a new rationale companion, and the falsified or
board-owned prose (`## Card snapshot`'s metadata bullets, the whole `## Other` section, the kept-skip
tense of `## Scope` bullet 2) was **deleted** and recorded there as claims the spec may no longer
make. `## Scope` now names all three retired placeholders by `path::QualifiedName`, pairs each with
the test that pins its subject today, closes with one checkable negative (no skip or `xfail` remains
under `tests/types/` or `tests/optimizer/`), and states the scalar-override division of concerns with
its owning card instead of claiming a placeholder that no longer exists.

The rationale's substance is the recovered change record the stub never had: the three skip reasons
verbatim, the one deliberately-kept placeholder and the commit that closed it at `0.0.6`, and the
fact — recoverable only from history — that the replacement definition-order tests were first pinned
against **test-only** fixture models, the same weakness the placeholders had, until `DONE-013-0.0.4`
added the managed `library` models and `DONE-014-0.0.4` re-pointed the tests at them and deleted the
fixture module, both within three hours of the retirement.

### Spec changes made (Worker 1 only)

Spec: `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md`, whole file (60 lines at `054de9dd`,
53 lines now).

- **Preamble paragraph (was line 7)** — moved to the rationale; replaced by the one-line pointer
  sentence naming what moved and where. Reason: F2; deliberation about the file, carrying an
  instruction the release falsified three weeks before the file existed.
- **`## Planning note` (was lines 18-20)** — section removed, moved verbatim to the rationale.
  Reason: F3; a raw Kanban column render whose value is now empty.
- **`## Card snapshot` (was lines 9-16)** — the labels / priority / relative-size bullets deleted;
  the section now identifies the card and hands the remaining board fields back to `KANBAN.md`.
  Reason: F5, and the list was already stale by one label.
- **`## Scope` bullet 1 (was line 24)** — rewritten to name all three retired placeholders and the
  tests that pin their subjects. Reason: F7; the old bullet was true and uncheckable.
- **`## Scope` bullet 2 (was line 25)** — deleted and replaced by a statement of the standing
  division of concerns plus the owning card. Reason: F6; it claimed a kept placeholder retired at
  `0.0.6`. The spec does not say the skip "was later retired" — that would be the self-narration
  `BUILD.md` `## Spec rationale extraction` forbids; the chronology is in the rationale.
- **`## Other` (was lines 27-34)** — heading and all six bullets deleted, each dispositioned in the
  rationale. Reason: F4; the heading names a card section the board no longer has, and five of the
  six bullets are now said better in `## Scope`.
- **Link definitions** — gained `[spec-011-rationale]` under `<!-- docs/SPECS/ -->` and three
  `<!-- tests/ -->` definitions; all ten canonical group headers preserved in order.
- **`[backlog]` kept, deliberately (F8 deferral).** Eight tracked Markdown files carry the identical
  unused definition; partial-fixing a cross-surface pattern leaves it divergently rather than
  uniformly wrong, which `worker-0.md` `## Closing out a kanban card` forbids. Target: the
  deferred-work catalog in `docs/builder/bld-011-final.md`, for a maintainer / next-spec-author
  sweep.

Rationale companion created: `docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md`
(new file). It is tracked and committed alongside the spec, and append-only for the rest of this
cycle.

### Notes for the deferred-work catalog (`bld-011-final.md`)

- **F8 — the unused `[backlog]` link definition.** Eight files at this working tree:
  `docs/SPECS/spec-011`, `spec-012`, `spec-013`, `spec-016`, `spec-024`, `spec-026`, `spec-036`,
  `spec-054`. One sweep or none. **The plan's figure of fifteen does not reproduce**; the measured
  count and its command are in the rationale's "The `[backlog]` link definition" entry.
- **The plan's "six siblings" figure for `a357c68c` does not reproduce either** — the measurement is
  eighteen added `def test_` lines in `tests/types/test_definition_order.py`. Recorded so a later
  pass does not re-copy the plan's number.
- **Five archived stubs still carry the boilerplate preamble** — `spec-012`, `spec-013`, `spec-016`,
  `spec-024`, `spec-026` — each awaiting its own residual cycle. Out of scope here; naming them
  saves the next author a grep.
- **F11 (from the plan, R2's) gained corroboration in passing.** `docs/SPECS/spec-011-…` was created
  at `81e4704d` (2026-06-01), while `docs/spec-011-relay_interfaces-0_0_5.md` existed under that
  number before the renumber (`df13b644`, 2026-05-17) and is now `spec-015-relay_interfaces-0_0_5.md`
  — which is exactly why a bare `spec-011` reference is ambiguous across older documents. Noted for
  R2; not acted on here.
- **No generated-doc edit is owed by this item.** `KANBAN.md`'s `DONE-011-0.0.4` card, its two
  glossary rows, and `docs/GLOSSARY.md`'s two anchors were read and are consistent with the
  reconciled spec. Nothing in this item requires a DB write, so no Worker 2 re-partition is
  requested.

### Final status

`final-accepted`.

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
