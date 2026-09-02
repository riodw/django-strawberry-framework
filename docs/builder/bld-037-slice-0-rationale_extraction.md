# Build: Slice 0 — the rationale move (spec-037 deliberative-layer extraction)

Spec reference: `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` (whole file; lines 98-140, 812-828, 840-856, 952-987, 1042-1074, 1096-1117, 1166-1184, 1196-1214, 1227-1231, 1247-1263, 1300-1309, 1329-1342, 1572-1660 at the pre-move numbering)
Status: final-accepted

**Procedural-closure slice** (`docs/builder/BUILD.md` `### Procedural-closure slices`): Worker 1 only, no Worker 2 build, no Worker 3 review, because it lands **no source diff**. This is one combined Plan + Final-verification block, and Worker 1 sets `Status:` itself. It is pre-flight step 7 of the `037` residual-reconciliation cycle, left open in `docs/builder/build-037-upload_file_image_mapping-0_0_11.md` `## Pre-flight record`.

Hot-path declaration: **none** (copied from the plan as written). No runtime code is touched.
Floor-verification scope: **none** (copied from the plan as written). No Django / Strawberry integration seam is touched.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately not run: this slice adds no helper, no constant, no validation branch and no test helper, and touches no `.py` file at all. The `### Package-wide helper inventory before helper planning` obligation is scoped to "before proposing any new helper-like logic"; there is none to propose. Recorded rather than silently skipped.
- **Existing patterns reused.** `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md` is the immediately-preceding execution of this exact move, on this card's own `0.0.11` sibling. Its structure was copied wholesale: framing header, `## Provenance of this record` with a measured byte census by route, `## Revision history`, one `## Decision N — <full heading text>` per spec Decision each carrying `Spec: [<heading>][anchor].` + `### Justification (moved from the spec)` + `### Alternatives considered (and rejected)` + `### Changes this Decision underwent`, then `## Risks and open questions` and a closing `## Non-Decision deliberation`. Its `<!-- LINK DEFINITIONS -->` footer was the scaffold, re-relativized (both files live in `docs/SPECS/appx/`, so the depths are identical).
- **New helpers justified.** None.
- **Duplication risk avoided.** The one duplication this move can introduce is text that lands in the companion **without leaving** the spec — a copy rather than a move. The plan prevents it by extracting each block into a scratch file by line range and then proving the move in **both** directions afterwards: every chunk ABSENT from the post-move spec, and every chunk PRESENT byte-verbatim in the companion. See `### Move proof (both directions)`.

### Implementation steps

1. Verify the spec is byte-identical to `HEAD` before the first edit, read-only, into a scratch path outside the repo.
2. Census the deliberative layer with three grammars; re-derive Worker 0's counts rather than accepting them.
3. Read every block end-to-end before cutting it, to find a non-deliberative tail inside a `Justification:` / `Alternatives` span.
4. Extract each block by line range into `<scratch>/moved/*.txt`.
5. Rewrite the spec: cut each block, leave a one-line pointer per Decision, keep the `## Risks and open questions` heading with a pointer, and add the `rationale-*` link definitions.
6. Assemble the companion from the extracted bytes plus this pass's own framing.
7. Verify: move proof both directions, `check_spec_glossary.py`, in-page anchor resolution in both files, link-definition integrity, `check_trailing_commas.py --check`.
8. Record every spec-vs-`HEAD` divergence noticed while reading, for the reconciliation slice.

Line numbers in this artifact are pin-at-write-time. Pre-move numbers are stated against the `HEAD` blob; post-move numbers against the file as this slice left it.

### Test additions / updates

None. This slice adds no code and no test. `pytest` was not run in any form (`AGENTS.md`: no `pytest` after edits unless asked; and no `.py` changed).

### Implementation discretion items

None. Every judgement in this pass — which sentences are implementation-relevant, which blocks carry a non-deliberative tail, whether to re-point the spec's surviving `#risks-and-open-questions` anchors — was decided here and is recorded below.

### Spec slice checklist (verbatim)

Not applicable. This slice has no `## Slice checklist` sub-bullets in `spec-037`: it discharges a `docs/builder/BUILD.md` process obligation the shipped spec predates, not a spec contract. The build plan's own checklist row is the closure target:

- [x] Slice 0: extract the deliberative layer into `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` (pre-flight step 7; Worker 1 procedural pass, no source diff) -> `docs/builder/bld-037-slice-0-rationale_extraction.md`

---

## Final verification (Worker 1)

### Summary

The spec's deliberative layer moved to `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md`: one revision-history block, 9 `Justification:` blocks, 9 `Alternatives considered (and rejected):` blocks carrying 29 rejected alternatives, Decision 9's post-ship `> **Superseded**` narrative, and the whole `## Risks and open questions` body. **22,016 bytes cut, 3,578 bytes of pointers and link definitions added back.** Ten one-line per-Decision pointers and one Risks pointer keep the deliberation visible from the contract. Every verification command below was run and its real output is quoted. No `.py` file, no test, and no out-of-scope doc was touched.

### Baseline: the spec was byte-identical to `HEAD` before the first edit

`git stash` / `git checkout` / `git restore` / `git worktree` were not used at any point (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`; the tree carries a concurrent session's work).

```
$ git show HEAD:docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md > <scratch>/spec-037-HEAD.md
$ diff <scratch>/spec-037-HEAD.md docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md && echo "IDENTICAL-TO-HEAD"
IDENTICAL-TO-HEAD
$ wc -c -l docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
    1863  116067 docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
$ git status --short docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
(no output — clean)
```

`HEAD` at the start of the pass: `5e642547`.

### Byte / line census, before and after, by route

**Before: 116,067 bytes, 1,863 lines. After: 97,629 bytes, 1,567 lines.** Delta `-18,438` bytes, `-296` lines = **22,016 bytes cut** minus **3,578 bytes added back** as pointers and link definitions.

| Route | Pre-move lines | Lines | Bytes | Disposition |
| --- | --- | --- | --- | --- |
| `Revision history (kept inline so the spec is self-contained):` block | 98-139 | 42 | 2,756 | 2,693 moved verbatim (the one `Revision 1` entry); the 62-byte preamble line + its 1-byte blank **deleted, not moved** |
| 9 `Justification:` blocks | 812-820, 840-845, 952-956, 1042-1048, 1096-1102, 1166-1168, 1196-1205, 1227-1230, 1329-1331 | 51 | 3,621 | moved verbatim; labels became `###` headings |
| 9 `Alternatives considered (and rejected):` blocks | 822-828, 847-856, 958-987, 1050-1074, 1104-1117, 1170-1184, 1207-1214, 1300-1309, 1333-1342 | 129 | 8,114 | moved verbatim; labels became `###` headings |
| Decision 9's `> **Superseded (post-ship, 2026-06-20 round-4 review).**` block | 1247-1262 | 16 | 1,245 | moved verbatim as a blockquote under Decision 9's `### Changes this Decision underwent` |
| `## Risks and open questions` body (preamble + 10 items) | 1572-1660 | 89 | 6,280 | moved verbatim; the spec keeps the heading + a pointer |
| **Total cut** | | **327** | **22,016** | |

Per-block byte figures, measured (`sum(len(line.encode()))` over each range): revision 2,756; D1 justification 471 / alternatives 366; D2 455 / 632; D3 339 / 2,042; D4 493 / 1,651; D5 502 / 935; D6 196 / 916; D7 687 / 510; D8 256 / — ; D9 — / 528 plus the 1,245-byte superseded block; D10 222 / 534; risks body 6,280. Justification subtotal 3,621; alternatives subtotal 8,114.

Composition of what moved: **2 justification bullets + 8 justification paragraphs**, and **29 rejected alternatives** (D1 2, D2 2, D3 6, D4 5, D5 3, D6 4, D7 2, D9 2, D10 3).

### Census method, and why one grammar is not enough

Every count above was measured as it was written. Occurrences were counted, never matching lines.

```
$ grep -on 'Justification' <spec> | wc -l
       9
$ grep -on 'Alternatives considered' <spec> | wc -l
       9
```

Both land on 9 distinct lines: 812, 840, 952, 1042, 1096, 1166, 1196, 1227, 1329 and 822, 847, 958, 1050, 1104, 1170, 1207, 1300, 1333. **This confirms Worker 0's line list exactly**, including its suspicion about the pairing: the block boundaries prove **Decision 8 has a `Justification:` and no `Alternatives` block** (the next `Alternatives` line, 1300, falls past Decision 9's heading at 1245) and **Decision 9 has an `Alternatives` block and no `Justification:`**. Both gaps are recorded with an explicit `None.` under the missing heading in the companion, so a later reader cannot mistake a genuine absence for a dropped chunk.

Three grammars for the chronology population, and all three were needed:

```
$ grep -on 'Revision [0-9]' <spec> | wc -l
       1
$ grep -oin 'evision' <spec>
98:evision
100:evision
```

The digit form finds 1 and is blind to the block's own preamble (`Revision history`, no digit). The shortest distinctive token `evision`, case-insensitive, finds **2 occurrences on 2 lines** — the true population, both inside the block. `spec-037` carries **no** `Revision N` cross-reference anywhere else, so the block lifted whole without repointing a single surviving sentence.

The third sweep: 22 chronology words carrying no `revision` token (`superseded`, `post-ship`, `earlier draft`, `prior draft`, `first draft`, `later changed`, `amendment`, `review round`, `formerly`, `no longer`, `has since`, `retract`, `pre-build`, `post-build`, `feedback`, `previously`, `used to`, `replaced by`, `reconciled`, `originally`, `round-4`, `round 4`), matched case-insensitively against **whitespace-flattened** text (newlines included, so a phrase wrapped across two lines cannot hide):

```
HEAD-SPEC total chronology-word occurrences: 6 | superseded=1, post-ship=1, previously=2, reconciled=1, round-4=1
DRAFT     total chronology-word occurrences: 3 | post-ship=1, previously=2
```

The 3 survivors, opened and read rather than counted: `spec:174` and `spec:1267` are `previously-`NotImplementedError`` descriptions of what the shipped code path used to do — contract, not spec self-narration — and `spec:1096` is the word `post-ship` inside this move's own Decision-9 pointer line. **Zero chronology sites survive in contract prose.**

### Move proof (both directions)

The proof that matters is not "the companion contains the text" but "the spec no longer does". Both were run over all 21 extracted chunks, comparing the exact bytes (label stripped where the label became a heading):

```
chunks checked: 21
STILL PRESENT IN SPEC (must be empty): []
MISSING FROM COMPANION (must be empty): []
spec occurrences of 'Justification:': 0
spec occurrences of 'Alternatives considered (and rejected):': 0
spec occurrences of 'Revision history (kept inline': 0
spec occurrences of 'Superseded (post-ship': 0
```

### Verification commands and their real output

**1. `check_spec_glossary.py` exits 0.**

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
OK: 20 terms - all have glossary entries and at least one spec link.
EXIT=0
```

Same 20 terms as the pre-flight baseline. This was the live risk of the move: three of the CSV's terms (`ConfigurationError`, `TestClient`, and — via `[glossary-orderset]` — `OrderSet`, which is not a CSV term) had a link inside moved text. `TestClient` and `ConfigurationError` each keep a surviving link elsewhere in the spec; `glossary-orderset`'s only use was in the moved Risks body, which is why its **link definition** was removed from the spec and carried to the companion.

**2. Every in-page anchor still resolves in whichever file now carries the text.**

```
SPEC(after): 88 anchor uses, 14 distinct, unresolved=[]
SPEC(HEAD):  109 anchor uses, 16 distinct, unresolved=[]
companion:   headings 18, unresolved in-page anchors: []
```

The moved text carries **21 anchor occurrences across 11 distinct anchors** — the ten `#decision-N--…` slugs and `#risks-and-open-questions`. The companion carries headings with exactly those slugs, so **zero anchors needed re-pointing at the spec**. That is a measured result, not an assumption: the `036` execution of this same move had to repair a broken slug with 16 uses and re-point 5 uses across 4 anchors naming spec sections its companion lacked; `spec-037` carried neither defect.

**3. No surviving cross-reference points into moved text without naming the rationale file.**

- Link-definition integrity, post-move: spec **0 dangling uses, 0 unused definitions** (after removing `[glossary-orderset]`); companion **35 definitions, 35 uses, 0 dangling, 0 unused**. Every companion definition's target file exists on disk except `[bld-037-slice-0]`, which is this artifact and now does.
- Ten `Rationale companion — …` pointer lines exist, one per Decision, plus the `## Risks and open questions` pointer: `11` `][rationale-` uses in the spec body.
- **The 10 surviving `[Risks](#risks-and-open-questions)` uses in contract prose were deliberately left as they are** (spec lines 120, 331, 479, 939, 1003, 1127, 1173, 1185, 1210, 1252). They still resolve — the spec keeps the heading — and the heading now carries the one-paragraph pointer naming the companion, so a reader reaches the moved text in two hops instead of one. Re-pointing them would mean editing surviving contract prose, which this pass does not do. Recorded here and in the companion's `## Non-Decision deliberation` so the reconciliation slice can reverse the call if it prefers.

**4. Markdown-layout gate.**

```
$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
EXIT=0
```

The companion's `<!-- LINK DEFINITIONS -->` block carries all 10 canonical group headers in order, present even when empty (`tests/`, `scripts/`, `.venv/` are empty), with paths resolved from `docs/SPECS/appx/` (`../spec-037-…md`, `../../GLOSSARY.md`, `../../../AGENTS.md`, `../../../django_strawberry_framework/…`). `docs/SPECS/appx/` shares its parent's `<!-- docs/SPECS/ -->` group per `START.md`.

**5. Not run, and why.** `uv run ruff format .` / `ruff check --fix .` — no `.py` file was touched by this slice, and running them across `.` would write into 55 package files a concurrent session has dirty. `pytest` — forbidden after edits without an explicit request, and this slice has no code to exercise.

### What was held back under the implementation-relevant carve-out, itemized

Each is the "why" that changes how the thing is built. All stayed exactly where they were, unmoved and unedited.

1. **Decision 3's "Why a separate map, not a `SCALAR_MAP` rewrite" paragraph** (spec:806-820). `SCALAR_MAP` is walked by the read path *and* the filter-input path, so a `SCALAR_MAP[models.FileField]` returning `DjangoFileType` would make a `FilterSet` over a file column emit an **output** object as a GraphQL **input**. A builder who never reads it puts the object types in `SCALAR_MAP`.
2. **Decision 3's thin-wrapper paragraph** (spec:822-837) — why `convert_field_output` is a new read-only helper rather than an expansion of `convert_scalar`.
3. **Decision 3's MRO-ordering paragraph** (spec:839-843) — why `ImageField` must precede `FileField` in the map, `ImageField` being a `FileField` subclass and the walk testing `type(field).__mro__`.
4. **Decision 3's file-resolver paragraph, and in particular its `consumer_authored_fields` skip clause** (spec:845-872, skip clause at 859-872) — why the file pass's skip set is deliberately broader than the relation pass's `consumer_assigned_relation_fields`: skipping only assigned overrides would silently clobber an annotation-only opt-out. Its breaking-wire-format paragraph (spec:874-886) stayed with it.
5. **Decision 4's "The guard must live on the subfields, not the parent resolver" paragraph** (spec:913-927). Strawberry resolves each selected subfield by `getattr` **after** and **outside** the parent resolver, so a parent `try/except` cannot reach the accesses that raise. A builder who never reads it writes the parent-level guard — the defect the Decision's own rejected alternative names.
6. **Decision 4's `SuspiciousFileOperation` paragraph** (spec:929-939) — the exception is deliberately not caught, because a path-traversal / hostile-name condition is a security signal rather than a storage quirk.
7. **Decision 4's default-nullable object-field bullet** (spec:892-908) — the object is nullable independent of `null` / `blank` because Django stores `""` for "no file" and that is reachable on a `null=False, blank=False` column, so a non-null SDL would 500. Its subfield-nullability sibling bullet (spec:909-911) stayed with it.
8. **Decision 6's no-new-resolver-code sentence (spec:980-986), its "Omittable is not nullable" paragraph (spec:988-1003), and its CR-6 lifting paragraph (spec:1005-1012)** — why no dedicated file-assignment branch is added (Django's `FileField` descriptor accepts an `UploadedFile`, so the generic scalar path carries it), the observable error contract for an explicit `null`, and what the build had to remove from `mutations/inputs.py`.
9. **Decision 8's standing architectural line** (spec:1041-1052) — normalization in `conf.py`, key-specific validation in the domain module, and any request-affecting setting resolved and stamped **once at schema build / finalization**. This is the one block whose measured span had to be **narrowed by reading**: a naive cut from the `Justification` label to the next Decision heading takes 17 lines / 1,130 bytes; the actual justification is 4 lines / 256 bytes, and the 12 lines after it are a rule for future work plus the contract statement "this card reads **no** setting, so it adds no settings-read or per-query validation overhead". This is the recurring shape — a deliberative block with a non-deliberative tail — and it was caught by reading the last sentence of every block before cutting it.
10. **Two Risks items could move only because the spec already states their rules elsewhere**, checked before the body was cut: the `Storage-metadata read cost` item's "does **not** cache or batch storage calls" rule is restated in `## Edge cases and constraints` (spec:1170-1173), and the `Image dimension dependency` item's "never a Pillow-conditional `skip`, which would slip uncovered branches past `fail_under = 100`" rule is restated in `## Test plan` (spec:1250-1253). Had either been unique to the Risks body it would have stayed under the rule that an unclear sentence stays.

### What was deleted rather than moved

- **The `Revision history (kept inline so the spec is self-contained):` preamble line and its trailing blank — 63 bytes.** The claim that the history is kept inline is exactly what this move made untrue, so it belongs in neither file (`docs/builder/worker-1.md` rule 2; git preserves it).
- **The spec's `[glossary-orderset]: ../GLOSSARY.md#orderset` link definition.** Its only use was inside the moved Risks body; it is carried in the companion instead. It is not a `-terms.csv` term, so `check_spec_glossary.py` is unaffected (re-run above: 20 terms, exit 0).

Nothing else. No sentence was found that the current Decisions have falsified **and** that this pass could delete without rewriting contract prose — the falsified statements this pass found are structural (Decision 9's body, the `Out of scope` / `Non-goals` / `Test plan` siblings) and are the reconciliation slice's, not a mover's. They are itemized below.

**One moved sentence is false at `HEAD` and moved verbatim anyway.** The `Image dimension dependency + test strategy` Risks item says "the project does **not** currently declare Pillow in runtime or dev dependencies"; `pyproject.toml` declares `pillow>=10.0.0` in the `dev` group at `HEAD` — the item's own *preferred* answer having been taken. The premise is gone while the moved text keeps its wording; the correction is recorded in the companion's `## Provenance of this record` rather than applied inside moved text, which is the treatment the `036` companion gave its one false Risks premise.

### Spec changes made (Worker 1 only)

Old path: `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` (unchanged — the spec stays at its archived location; `docs/builder/BUILD.md` `### Spec stays at its working location`).
New path (created): `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md`, tracked and durable, never touched by a pre-flight artifact reset.

| Pre-move spec lines | Change | Reason |
| --- | --- | --- |
| 98-139 | `Revision history …:` block replaced by a 5-line "This spec's deliberative layer … lives in the rationale companion" paragraph | `BUILD.md` `## Spec rationale extraction`; the preamble's own claim is falsified by the move |
| 812-828 | Decision 1's justification + 2 alternatives replaced by a 2-line pointer | rule 1: every Decision keeps a one-line pointer |
| 840-856 | Decision 2's justification + 2 alternatives replaced by a pointer | same |
| 952-987 | Decision 3's justification + 6 alternatives replaced by a pointer | same |
| 1042-1074 | Decision 4's justification + 5 alternatives replaced by a pointer | same |
| 1096-1117 | Decision 5's justification + 3 alternatives replaced by a pointer | same |
| 1166-1184 | Decision 6's justification + 4 alternatives replaced by a pointer | same |
| 1196-1214 | Decision 7's justification + 2 alternatives replaced by a pointer | same |
| 1227-1231, 1243 | Decision 8's 4-line justification removed; pointer appended **after** the standing architectural paragraph, which stays | same; the carve-out keeps 1232-1243 in the spec |
| 1247-1263 | Decision 9's `> **Superseded (post-ship, …)**` block removed | `BUILD.md` `## Spec rationale extraction`: the spec never narrates its own history |
| 1300-1309 | Decision 9's 2 alternatives replaced by a pointer naming both the alternatives **and** the post-ship supersession | rule 1, widened so the supersession stays visible from the spec without being narrated in it |
| 1329-1342 | Decision 10's justification + 3 alternatives replaced by a pointer | rule 1 |
| 1572-1660 | `## Risks and open questions` body replaced by a 6-line pointer paragraph; the heading stays | the preferred-answer / fallback shape is a build-time instrument, not a contract |
| link definitions | 12 `rationale-*` / `spec-037-rationale` definitions added under `<!-- docs/SPECS/ -->`; `[glossary-orderset]` removed | the pointers need targets; the removed definition's only use moved |

**Spec status-line re-verification (this spawn).** Lines 1-40 (title, shipped-in-`0.0.11` opener, `Status: **SHIPPED (`0.0.11`)**`, `Owner:`, `Predecessors:`) were read and still describe the build's state: the card is `DONE-037-0.0.11`, all four slices were final-accepted, the slice checklist is deliberately unticked with the `Status:` line as truth, and every predecessor spec named exists on disk. **No status-line edit was needed.** Decision 1's claim that the spec "lives at `docs/spec-037-…`" is a body claim, not a status line, and is left for the reconciliation slice (Worker 0's D8).

### Notes for Worker 1 (spec reconciliation)

Worker 0's plan already carries D1-D8 verified at source; they are not re-derived here. **The single most important item is N1 — it is a consequence this pass created and it must not be lost.**

- **N1 (created by this pass; highest priority). Decision 9's surviving body now states a superseded contract with no marker at all.** Removing the `> **Superseded**` block was correct — `BUILD.md` forbids that shape outright — but the block was the only thing signalling that the body under it is retracted. The body now reads, unqualified: "No fakeshop model has a file/image field" (spec:1059-1060), "live `/graphql/` tests are added **only** if implementation naturally exposes a file/image field through an existing fakeshop app" (spec:1068-1069), and "a live fakeshop file-upload surface is deferred to fakeshop activation ([`TODO-BETA-062-0.1.5`][kanban]); the tension is recorded, not silently resolved" (spec:1077-1081). All three are false at `HEAD` — the `scalars` app carries `MediaSpecimen` and `examples/fakeshop/test_query/test_uploads_api.py` exists. **The spec was self-contradictory before this pass and is now uniformly wrong on this point, which is harder to notice.** Slice 2 owes Decision 9 a direct-contract rewrite: state the shipped split (live `/graphql/` tests own the read objects, the SDL shapes and a real multipart upload; the synthetic-model package tests own the storage-backend fault injection and corrupt-dimension edges that a live request cannot reach), with no chronology. The narrative and the verbatim block are already parked in the companion under Decision 9's `### Changes this Decision underwent`, so a `**Post-ship:**` bullet is in place and only needs the spec side.
- **N2. The same falsified deferral has four sites, not the two Worker 0 named.** Worker 0's D5 (Decision 9) and D6 (`## Out of scope`, spec:1366-1368) are two. The other two: `## Non-goals` bullet 2 (spec:529-532), "if a real file/image field is later added to fakeshop, it earns live coverage then", and `## Test plan` (spec:1279-1281), "**Live HTTP tests.** None required unless implementation adds or discovers a genuine fakeshop file/image field; do not add a fake upload domain solely for coverage." Fixing D5/D6 alone is the partial claim fix. Grep handle for the whole population: `TODO-BETA-062` (2 hits at spec:1080, 1367) plus the two prose sites above, which carry no shared token — a token-only sweep under-counts this population by half.
- **N3. `DONE-NNN-0.0.11` is a two-site placeholder, not one.** Worker 0's D8 names DoD item 6; the same literal is also in `## Doc updates` Slice 4 (spec:1342). `grep -n 'DONE-NNN' <spec>` -> 2.
- **N4. The pre-archive `docs/spec-037-…` path has three sites.** Decision 1's body (spec:773), DoD item 1's file claim (spec:1384) and DoD item 1's `check_spec_glossary.py --spec docs/spec-037-…` invocation (spec:1387). Worker 0's D8 covers the DoD; Decision 1's body is the third. The correct invocation is the one this artifact quotes above.
- **N5. Two surviving hedges point at a fallback that was not taken.** `## Implementation plan` row 1 (spec:1127) says Pillow is added to the dev extras "unless the [Risks](#risks-and-open-questions) stand-in fallback is taken", and `## Test plan` (spec:1252) offers "(or the lightweight stand-in of the [Risks](#risks-and-open-questions) fallback)". `pyproject.toml` declares `pillow>=10.0.0` in the `dev` group at `HEAD`, so the preferred answer shipped and both hedges are stale. Both also now point at a heading that carries only a pointer.
- **N6. `## Current state` carries an executable claim whose output has changed.** Spec:480-482: "**No example app uses a file/image column.** `grep -rln "FileField\|ImageField" examples/` returns nothing". It returns hits at `HEAD`. `BUILD.md` `### `## Current state`: observations stand, predictions do not` licenses a dated observation to stand, and the `036` reconciliation used exactly that licence — but it rewrote the clauses that were **not** dated observations. This one is a dated observation carrying a reproducible command, which is a borderline case Slice 2 should grade explicitly rather than skip.
- **N7. The 10 surviving `[Risks](#risks-and-open-questions)` uses are now two-hop.** Listed under verification 3 above with line numbers. They resolve, and the heading they land on names the companion. If Slice 2 prefers them pointed directly at `[rationale-risks]`, that is 10 edits to surviving contract prose and it should be a deliberate call, not a drive-by.
- **Not a finding, do not re-raise.** `__version__` is `0.0.15` while this card targeted `0.0.11`; Decision 10 and DoD item 7 describe a cut that happened and are not stale (the plan's `## Worker-0 verification pass` already settles this).

### DRY check across this slice and prior accepted slices

No prior slice exists in this cycle. Against the corpus: this is the fourth execution of the same move (`034`, `035`, `036`, `037`) and it reuses the `036` companion's structure rather than inventing one, which is the point of the shape being fixed in `BUILD.md` / `worker-1.md`. No new duplication.

### Failability proofs

`None; this pass introduced no new boundary.` This slice lands no runtime code, so there is no guard, gate or rejection path to prove failable. The proof obligations this pass *does* carry are the move proofs and the census, run and quoted above; the move proof's negative direction (**every chunk absent from the post-move spec**) is the control that makes the positive direction meaningful — a copy that never left the spec would pass a presence-only check and fail this one.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Not applicable; plan declares floor-verification scope none.`

### Final status

`final-accepted`. This pass owns the transition (`docs/builder/BUILD.md` `### Procedural-closure slices`; no Worker 2 build and no Worker 3 review ran, and none was owed). Pre-flight step 7 of `docs/builder/build-037-upload_file_image_mapping-0_0_11.md` is discharged and the later slices are unblocked.

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
