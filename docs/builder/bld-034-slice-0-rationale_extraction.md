# Build: Slice 0 — spec-034 rationale extraction (pre-flight step 7)

Spec reference: `docs/SPECS/spec-034-permissions-0_0_10.md` (whole file; the move touched lines 11-20, 201-209, 222-231, 238-240, 246-256, 268-275, 281-289, 314-319, 325-327, 333-335, 343-348, 362-368, 379-381, 387-389, 418, 488-489, 513-524, 634-666 in pre-move numbering)
Status: final-accepted

**Procedural-closure pass** per `docs/builder/BUILD.md` `### Procedural-closure slices`: a Worker-1-owned custodial move that lands no source, so `## Build report (Worker 2)` and `## Review (Worker 3)` are not applicable and `## Plan (Worker 1)` and `## Final verification (Worker 1)` are carried as one combined block. This is pre-flight step 7 of the `034` residual-reconciliation cycle; it **gates creation of `docs/builder/build-034-permissions-0_0_10.md`**, which therefore did not exist while this pass ran and is cited by path only.

---

## Plan + Final verification (Worker 1)

### What this pass did

MOVED the deliberative layer out of `docs/SPECS/spec-034-permissions-0_0_10.md` into a new tracked companion at `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`, matching the immediately-preceding execution of the same move (`docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md`) in file shape, `## Provenance of this record` measurement discipline, per-Decision section structure, `## Revision history` handling, `## Risks and open questions` body move, and `## Non-Decision deliberation` catch-all.

**No reconciliation against `HEAD` source was performed and none is claimed.** Suspicions noticed while reading are recorded below, unverified.

### Size, before and after

| | bytes | lines (`wc -l`) |
|---|---|---|
| `spec-034-permissions-0_0_10.md` before | 145,643 | 674 |
| `spec-034-permissions-0_0_10.md` after | 112,241 | 607 |
| spec delta | **-33,402** | -67 |
| `spec-034-permissions-0_0_10-rationale.md` (new) | 69,448 | 396 |

A line-level diff of the pre-move copy against the post-move file removes **41,234** bytes and inserts **7,832**, netting the -33,402 above. Re-derive with:

```shell
git show HEAD:docs/SPECS/spec-034-permissions-0_0_10.md | wc -c -l
wc -c -l docs/SPECS/spec-034-permissions-0_0_10.md docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md
```

### Per-route accounting

Verbatim text carried out, measured on the pre-move spec. These figures count the text of the moved lines and **not** the newline terminating each line, nor the blank separator lines inside each region — which is why they sum to less than the diff-level 41,234.

| Route | What | Count | Bytes | Disposition |
|---|---|---|---|---|
| R1 | `Revision history (kept inline so the spec is self-contained):` preamble | 1 line | 61 | **DELETED** — the move falsifies the claim |
| R1 | `Revision N` entries | 8 | 13,038 | MOVED (byte-for-byte except 6 re-pointed anchors) |
| R2 | `Justification:` blocks | 13 (23 bullets/paragraphs) | 8,610 | MOVED, minus 4 held-back passages |
| R2 | `Alternatives considered (and rejected):` blocks | 13 (29 alternatives) | 7,737 | MOVED |
| R3 | `## Risks and open questions` body (preamble + items) | 1 + 10 | 8,340 | MOVED (heading + pointer stay) |
| R4 | chronology framing in surviving contract prose | 4 sites | 57 | **DELETED** |
| | **route text total** | | **37,843** | |

Label shapes: of the 26 labels, **11 stood on their own line** (5 `Justification:`, 6 `Alternatives considered (and rejected):`) and **15 were inline prefixes** stripped from the paragraph they introduced (8 and 7 respectively). All 26 were stripped in the companion and replaced by the `### Justification (moved from the spec)` / `### Alternatives considered (and rejected)` headings, per the `spec-033` precedent (0 residual labels in either file). The route byte figures above measure what left the spec and therefore still include those 26 labels.

The 3,391-byte gap between the route text (37,843) and the diff-level removal (41,234) is: the newline terminating each of the 101 removed lines; the blank separator lines inside each region; the 3 link definitions the move left unreferenced (143 bytes, listed below); and four partially-rewritten lines that a line-level diff counts whole while only part of each actually left (spec lines 73, 303, 418, 488-489 pre-move).

Bytes put back into the spec, measured line-by-line with terminators: the header pointer **373**, 13 `Rationale companion --` pointer lines **1,535**, the Risks pointer **403**, the held-back passages re-seated as body prose across 5 lines **2,102**, and 15 new link definitions **2,187** — **6,600** of genuinely new content. The balance of the diff-level 7,832 is blank separators plus the rewritten form of the seven lines the move changed only in part (the four chronology sites, the two split `Justification:` paragraphs, and the re-linked `Meta.fields` bullet, whose own delta is +155), which a line-level diff counts whole on both sides.

### Chronology census — three grammars, and what each found

| Grammar | Command | Found |
|---|---|---|
| G1 | `grep -on 'Revision [0-9]'` | **17** |
| G2 | `grep -oin 'evision'` | **20** |
| G3 | `superseded\|earlier revision\|this revision\|review round\|pre-build review\|post-build review\|fix-verification\|feedback2\|incoming review` | **13** |

**G1 missed three sites G2 caught**, and the miss is structural, not incidental: `Revision history` (the block preamble, no digit), `Revision-5` (hyphen, inside Revision 6's prose), and `this revision` (inside Revision 4's prose). G3 found nothing outside the revision block except one false positive — `soon-to-be-superseded` in Decision 2's rejected alternatives, which moved with its bullet anyway. **G2's 20 is the true population**; G1 alone would have under-counted the block and, had any of its three blind spots sat in contract prose rather than inside the moving block, would have left a chronology tag behind.

Of the 20: 16 sit inside the `Revision history` block (moved or deleted wholesale) and **4 are chronology framing embedded in surviving contract prose**, all `Revision 8`:

- pre-move L73, `## Slice checklist` Slice 4 activation sub-bullet — ` — see Revision 8` removed (17 bytes).
- pre-move L303, Decision 6's Consumer-recipe divergence block — `, Revision 8` removed (12 bytes).
- pre-move L488, Test plan Slice 4 `test_cascade_view_item_user_respects_category_visibility` — ` (Revision 8)` removed (14 bytes).
- pre-move L489, Test plan Slice 4 `test_cascade_view_entry_user_nested_selection_drops_hidden_targets` — ` (Revision 8)` removed (14 bytes).

Post-move residual: G1 = 0, G3 = 0, G2 = 1 — the phrase "eight-revision review history" in the header pointer this pass wrote, matching the `033` spec's own "five-revision review history" wording.

### Held back in the spec under the implementation-relevant carve-out

Four passages, one bullet each with the reason:

- **Decision 8's first justification sentence** (why `queryset.db` and not `_db`: `_db` is `None` for a routed queryset, so `.using(None)` would let the target subquery route independently and compose a cross-database `__in`). This is the rule an implementer needs, not an alternative that lost. Held.
- **Decision 8's third and fourth justification sentences** (the Multi-database-cooperation axis-2 contract and its per-handed-queryset scope). Normative. Held. Only the middle sentence — upstream-fidelity plus the card-premise correction — moved, so Decision 8's justification in the companion is a single sentence, and the companion carries a note saying so and pointing the rejected alternative's "— above" back at the held sentence.
- **Decision 9's three closing justification sentences** (the per-call `fields=` validation is redundant-but-bounded, and the per-`(model, fields)` memo would absorb it). Read as deliberation it looks removable; it is a known-cost note that stops a later pass deleting a security re-validation as dead work. Held.
- **Decision 6's `No existence leak` and `The layers stay independent` justification bullets**, and its whole **Consumer-recipe divergence (cookbook `view_<model>`)** block. The two bullets state guarantees the contract makes (the first is restated in `## Error shapes` and the Definition of done), not arguments against nulling or sentinels — those two bullets did move. The divergence block is cited by the parity table as a contract statement and carries the implementation-relevant fact that forces the shape (`django_strawberry_framework/types/resolvers.py::_make_relation_resolver` reads a forward FK by bare accessor with no `DoesNotExist` / sentinel fallback, which is *why* every non-staff branch must cascade). Under "when unclear, it stays", it stayed whole.

Two carve-outs named in the pass instructions **needed no action**, because the rule in each case is stated in the Decision's own body, which never moved:

- Decision 9's reason a bare string must be rejected before per-name validation (a string iterates as characters and would emit a misleading `'i' is not a cascadable field`) is in the Decision body and in `## Error shapes`.
- Decision 5 step 1's reason the predicate tests the `column` *value* rather than `hasattr` (M2M / `GenericRelation` expose `column = None` under Django 6.0) is in step 1 of the Decision body. Only the justification's *restatement* of it — a note about porting fidelity — moved.

### Deleted rather than moved

- **The `Revision history (kept inline so the spec is self-contained):` preamble line** (61 bytes). Its claim is falsified by the move itself: the history is no longer inline. Rule 2 — a false sentence belongs in neither file.
- **Four chronology tags** (57 bytes total), listed above. A normative sentence must not carry a chronology a reader could try to apply; each removal is recorded under the owning Decision's `### Changes this Decision underwent` in the companion, or under `## Non-Decision deliberation`.
- **Three link definitions the move left unreferenced** (143 bytes): `[next]: NEXT.md`, `[permissions]: ../../django_strawberry_framework/permissions.py`, `[kanban-models]: ../../examples/fakeshop/apps/kanban/models.py`. Each was used only from text that moved; all three are re-defined in the companion where their uses now live.

### Not byte-verbatim in one respect

Text carrying the in-page anchors `#edge-cases-and-constraints`, `#error-shapes`, `#slice-checklist`, and `#non-goals` names spec sections the companion does not have. Those **7 uses across 4 anchors** are re-pointed at the spec through reference-style links (`[spec-034-edge-cases]`, `[spec-034-error-shapes]`, `[spec-034-slice-checklist]`, `[spec-034-non-goals]`) rather than left to dangle: 6 of them in `Revision 3` / `Revision 4` / `Revision 5` / `Revision 7`, 1 in the Risks item on pre-existing glossary / tooling drift. `#decision-N--…` anchors were left alone — the companion carries headings with exactly those slugs — and `#risks-and-open-questions` likewise resolves locally there.

### Verification commands and their real output

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-034-permissions-0_0_10.md
OK: 42 terms - all have glossary entries and at least one spec link.
# exit 0   (pre-move run of the same command also reported: OK: 42 terms)
```

The `42` is unchanged, which is the required outcome — but it did not hold on the first attempt, and that is the finding of this pass:

```shell
# first post-move run, before the repair:
Spec terms missing a link to GLOSSARY.md:
  - Meta.fields (anchor: metafields) - add at least one link to anchor `metafields` ...
# exit 1
```

**The spec's only link to `#metafields` lived inside Decision 5's rejected alternatives**, so the move carried it out and the term lost its last spec link. The term count never changed; the *link* did. Repaired in the spec, not in the CSV (which this pass may not touch), by linking `Meta.fields` at the `## Edge cases and constraints` bullet that already names it — the same bullet whose parenthetical pointed at Decision 5's alternatives and therefore needed re-pointing at the companion anyway.

```shell
$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-034-permissions-0_0_10.md docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md
# exit 0, no output   (markdown link-def scaffold on both files)

$ uv run python scripts/check_citations.py --check
OK: 857 citations resolve (738 in 431 .py files, 119 in KANBAN.md).
# exit 0
```

Link / anchor audit (script kept in this pass's scratchpad, re-derivable):

```text
===== docs/SPECS/spec-034-permissions-0_0_10.md
  in-page anchors used: 23; unresolved: 0
  ref-ids used: 93; defined: 93          (no undefined, no unused)
  10 canonical headers present and in order: True
===== docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md
  in-page anchors used: 13; unresolved: 0
  ref-ids used: 47; defined: 47          (no undefined, no unused)
  every non-URL def resolves to a file on disk: True
  every cross-file def carrying a #fragment resolves to a real heading: True
  10 canonical headers present and in order: True
```

Line-conservation audit (every non-blank pre-move line either survives in the spec, is reproduced in the companion, or is a recorded deletion):

```text
lines appearing MORE often after than before: 38 -- all of them framing this pass wrote
lines lost from the spec: 74; of those NOT present in the companion: 15
   4 x Revision entries    -- modified by the anchor re-pointing above
   1 x Risks item          -- modified by the anchor re-pointing above
   4 x chronology lines    -- the R4 deletions
   2 x split Justification lines (Decisions 8 and 9)
   1 x Meta.fields bullet  -- re-linked
   3 x pruned link definitions
```

One real defect was caught by this audit and fixed: the first rewrite emitted Decision 6's `**No existence leak**` bullet **twice** (the held-back pair was re-inserted while the original line, sitting outside every replaced region, was also copied through). A byte count alone would not have found it; the duplicate is now gone and the audit is clean.

**Foreign-citation census, run as a postcondition.** A rationale move breaks citations in *other* files and no gate sees it, because the link still resolves. Counting **occurrences** of the token `spec-034` across tracked files: **179 occurrences in 27 files**, 24 of them in the spec itself. `grep` for `spec-034-permissions-0_0_10.md#` across the tree returns **zero deep anchor links**. Six lines pair `spec-034` with a chronology or deliberation word; all six are false positives — two `KANBAN` data / board-note lines, one KANBAN card checklist item citing a Decision (Decisions stayed), and `spec-035` line 291 / `spec-036` line 415, each citing a `spec-034` **Decision** from inside its own `Justification:` block. **No citation anywhere in the tree points into this spec's revision history or its Risks body**, so the move breaks nothing outside the two files it touched.

### Files written

- `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` — created, 69,448 bytes.
- `docs/SPECS/spec-034-permissions-0_0_10.md` — edited, the move only.
- `docs/builder/bld-034-slice-0-rationale_extraction.md` — this artifact.
- `docs/builder/worker-memory/worker-1.md` — appended.

No source or test file was touched, so no `ruff` run was owed and none was made. `pytest` was not run in this pass, with or without `--cov*` flags.

### Baseline-dirty, out of scope, untouched

`BACKLOG.md`, `KANBAN.html`, `KANBAN.md`, `README.md`, `examples/fakeshop/db.sqlite3`, `scripts/_kanban_lib.py`, `scripts/build_kanban_html.py`, `scripts/build_kanban_md.py`, `tests/test_build_kanban_html.py`, plus untracked `0_0_14.md` and `docs/DIVERGENCE.md`. A concurrent session owns these; none was edited or reverted.

---

## Build report (Worker 2)

Not applicable. `docs/builder/BUILD.md` `### Procedural-closure slices`: this pass lands no source and no tests, so there is no build pass to dispatch.

---

## Review (Worker 3)

Not applicable, same reason. There is no diff for Worker 3 to review; the custodial move is verified mechanically in the block above and audited by the cycle's later passes against the companion it created.

---

## Final verification (Worker 1)

- Spec slice checklist: not applicable — this pass predates the build plan and has no spec `## Slice checklist` entry of its own. It is pre-flight step 7.
- DRY check across this slice and prior accepted slices: not applicable — no code.
- Existing tests still pass: not run. `pytest` is out of scope for this pass by instruction, and no executable byte changed.
- Spec reconciliation: performed only to the extent the move required; see `### Spec changes made (Worker 1 only)`.
- Final status: `final-accepted`.

### Summary

`spec-034` gained the `-rationale.md` sibling it shipped without. The spec fell from 145,643 to 112,241 bytes (-23%) and now reads as a clean current contract with no chronology in it; the eight-revision history, 13 justifications, 29 rejected alternatives, and the 10-item Risks deliberation live in the companion, keyed to the Decision each belongs to and structured so a `**Post-ship:**` bullet appends under any Decision without restructuring. Four passages were held back in the spec under the implementation-relevant carve-out and two more needed no action because the rule was already in the Decision body. `check_spec_glossary.py` still reports `OK: 42 terms`.

### Notes for Worker 1 (spec reconciliation)

Recorded from close reading during the move. **None of these was verified against `HEAD` and none was acted on** — they are leads for the conformance cohorts, not findings.

- **`## Current state`'s first bullet may be stale in its last clause.** It reads "**`permissions.py` shipped in Slice 1.** … The four products-schema hooks that call it remain comments (Slice 4's uncomment)." The `Status:` line says all five slices are final-accepted, so the hooks are presumably active. The section is licensed to describe the repo at a moment in time (`BUILD.md` `### `## Current state`: observations stand, predictions do not`), but a sentence in the present tense that the same file's status line falsifies is the stale-sentence shape. **This move deliberately did not touch it** — rewriting it is reconciliation.
- **Card-id rot, three populations.** (a) `TODO-BETA-046-0.1.1` is named as the FieldSet card in Decision 2 (twice), Decision 6, and elsewhere, while `docs/SPECS/spec-055-fieldset-0_1_1.md` exists on disk — the card is plausibly `055` now. (b) `TODO-ALPHA-035-0.0.10` appears in Decision 13 and `## Out of scope` while the spec's own header calls it `DONE-035-0.0.10` — the file contradicts itself. (c) `TODO-ALPHA-034-0.0.10` appears in `## Current state`, the Slice checklist, `## Doc updates`, and the Definition of done for a card the header calls `DONE-034-0.0.10`. Note the `033` cycle's lesson: a bare numeral and a full card id are two populations and a grep for either misses the other.
- **Pre-archive path spelling.** Decision 1 states the spec "lives at **`docs/spec-034-permissions-0_0_10.md`**" and Definition of done item 1 names both that path and the command `uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md`. The file is archived at `docs/SPECS/`. The reference-style link definitions were re-pointed by the archive sweep so nothing resolves wrongly, but the DoD's `--spec` argument is load-bearing: it fails at the stale path. This is the exact third rot class the `033` cycle named.
- **Raw `path:NN` citations in a standing doc.** Decision 12 cites `(walker.py:212-214)`, the Sharded-callers edge case cites `walker.py:212`, and the Slice 1 test plan's multi-DB harness note cites `examples/fakeshop/config/settings.py` line ~116. `AGENTS.md` rule 27 permits raw line numbers only in per-cycle scratch artifacts. Three sites, all in surviving contract prose.
- **`## Error shapes` may be short one case.** Revision 8 records that `_validate_fields` rejects a non-iterable / non-string `fields=` as `ConfigurationError` rather than a raw `TypeError`. `## Error shapes` lists the unknown/non-cascadable case and the bare-string case, but not the non-iterable case. Worth a conformance check against `django_strawberry_framework/permissions.py::_validate_fields`.
- **"the pinned Django 6.0" appears in Decision 5 step 1 and twice in `## Edge cases and constraints`.** The repo has since audited and supported a wider Django range; the phrase may be stale as a present-tense claim even though the `column`-value correction it justifies is still right.
- **Decision 12's ordering claim is worth pinning against `connection.py` at `HEAD`.** It states the connection pipelines call `apply_type_visibility_sync` / `_async` "before `filter:` / `orderBy:` / slicing". `spec-033` reworked the connection path and the `033` companion records later unowned "idea #N" commits that inverted three of that card's contracts on the same seam. Verify, do not assume.
- **Two countable claims to re-derive rather than accept.** The Risks item on live-suite sensitivity says Slice 4 re-pinned "12 across `test_products_api.py` and the in-process `test_schema.py`"; the `## Implementation plan` table estimates per-slice test counts and a "~1,100 lines net-positive" total. A count can be right in every digit and wrong in its subject.
- **Pre-existing link-definition ordering in the spec, not caused by this move and not fixed by it.** Under `<!-- django_strawberry_framework/ -->`, `[types-base]` precedes `[definition]`; under `<!-- docs/ -->`, `[glossary]` precedes `[glossary-aggregateset]`. Both predate this pass (confirmed against the pre-move copy) and `scripts/check_trailing_commas.py --check` accepts both, since its scaffold fixer slots defs per category without re-sorting within one. Cosmetic; flagged only so a later pass does not attribute it to the move.
- **Decision 2 cites `[`types/base.py`][types-base] #"aggregate_class"` as the anchor for `DEFERRED_META_KEYS`.** A `path #"substring"` citation breaks on reflow as well as reword and no gate sees it (`check_citations.py` is `path::Symbol`-only). Worth confirming the substring still exists.

### Spec changes made (Worker 1 only)

Every edit below is the move or a consequence of it. Line numbers are pre-move.

1. **Lines 11-20 → one line.** Deleted the `Revision history (kept inline so the spec is self-contained):` preamble (falsified by the move); moved the eight `Revision N` entries to the companion; inserted the header pointer paragraph naming the companion, in the position `spec-033` uses.
2. **Thirteen `Justification:` + `Alternatives considered (and rejected):` regions → one `Rationale companion --` pointer line each** (pre-move lines 201-209, 222-231, 238-240, 246-256, 268-275, 281-289, 314-319, 325-327, 333-335, 343-348, 362-368, 379-381, 387-389). Each pointer names what moved and where, in the `spec-033` form, with the rejected-alternative count spelled out.
3. **Decision 6 (pre-move 281-289) restructured around the carve-out.** The two held-back justification bullets are re-seated as unlabelled body prose above the pointer; the Consumer-recipe divergence block stays below it, minus its `, Revision 8` tag.
4. **Decision 8 (pre-move 325) split three ways.** Sentence 1 and sentences 3-4 stay as body prose; sentence 2 moved.
5. **Decision 9 (pre-move 333) split two ways.** Sentences 1-2 moved; sentences 3-5 stay as body prose.
6. **Lines 513-524 → one line.** The `## Risks and open questions` body moved; the heading stays with a pointer paragraph, exactly as `spec-033` did.
7. **Four chronology tags removed** from surviving contract prose (pre-move lines 73, 303, 488, 489).
8. **Edge-cases `Meta.fields` bullet re-linked** (pre-move line 418): `Meta.fields` now carries its `[glossary-metafields]` reference — the move had taken the spec's only link to that anchor and broken `check_spec_glossary.py` — and the bullet's parenthetical, which pointed at Decision 5's now-moved alternatives, names the companion.
9. **Link definitions:** added `[spec-034-rationale]`, `[rationale-risks]`, and `[rationale-d1]`-`[rationale-d13]` under `<!-- docs/SPECS/ -->`; pruned `[next]`, `[permissions]`, and `[kanban-models]`, which the move left with no use in the spec.

No contract sentence was reworded, no Decision was renumbered, and no claim about shipped behavior was changed.

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
