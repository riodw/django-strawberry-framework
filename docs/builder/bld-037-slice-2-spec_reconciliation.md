# Build: Slice 2 — spec reconciliation (`spec-037` rewritten to the shipped contract)

Spec reference: `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` (whole file) and its rationale companion `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` (whole file)
Status: final-accepted

**Procedural-closure slice** (`docs/builder/BUILD.md` `### Procedural-closure slices`): Worker 1 only, no Worker 2 build, no Worker 3 review, because it lands **no source diff**. One combined Plan + Final-verification block, and Worker 1 sets `Status:` itself. It is the payload of the `037` residual-reconciliation cycle (`docs/builder/build-037-upload_file_image_mapping-0_0_11.md` `## Cycle shape`).

Hot-path declaration: **none** (copied from the plan as written). No runtime code is touched.
Floor-verification scope: **none**. Slice 1's re-declared scope was discharged in its own build pass; this slice writes no `.py` file, so it re-declares nothing.

Raw `path:NN` references are used below under `AGENTS.md` rule 27's per-cycle-artifact carve-out. Spec line numbers are **pre-edit** unless marked otherwise — the edits shift them, and an anchor quoting the exact phrase a fix rewrites dies on the fix.

---

## Plan (Worker 1)

### The governing rule this slice is built on

`docs/builder/BUILD.md` `## Spec rationale extraction`: **"The spec stays the heart, and it never narrates its own history."** Every divergence Slice 1 graded `SUPERSEDED` is fixed by **rewriting the decision to state the corrected contract directly** — no amendment block, no retraction paragraph, no `(superseded)` marker, no dated parenthetical, no "as of `spec-048`" hedge. What changed, when, why, and what it replaced lands in the rationale companion as a `**Post-ship:**` bullet under the owning Decision, or under `## Non-Decision deliberation` when it belongs to no single Decision. The maintainer stated the split directly: *"Explanation of the changes DO NOT go in the spec file, they go in the rationale file."*

### Input: the graded population

Slice 1 graded all 57 spec items: **42 BUILT-CONFORMANT · 0 DROPPED · 0 DEVIATED · 15 SUPERSEDED.** Nothing the spec planned was skipped, and the one item that owed code (`Meta.required_overrides` end-to-end) shipped in Slice 1. **Every remaining divergence is spec-side, and that is this slice.** 26 recorded findings: D1-D8 (build plan `## Worker-0 verification pass`), N1-N7 (`bld-037-slice-0`), N8-N18 (`bld-037-slice-1`).

### Method: establish the population before editing it

**The partial claim fix is this corpus's dominant reconciliation defect** — fixing the sites a finding names and missing the rest of its population. So every finding below was re-measured at source before it was edited, and the measurement is recorded beside the edit. Counting rules applied throughout (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`): search the **shortest distinctive token**, count **occurrences** not matching lines, and hand-enumerate any population whose members share no token. zsh does not word-split, so every sweep prints its population size and no sweep iterates a bare `$VAR`.

**That method paid for itself three times.** Two recorded findings under-counted their own population, and both under-counts were invisible to the instrument that produced them:

- **N8 / D1 named 17 lines / 18 occurrences of a code-span `` `path` ``. The true population is 20 sites.** Three carry the token with no code span, so `grep '`path`'` cannot see them: `path: String` on spec:651 and spec:658, inside the two SDL example fences — the most concrete falsehood in the file, since a reader copies that SDL — and `` `path: str | None` `` on spec:238 in the Slice-1 checklist.
- **N2 named four sites of the falsified live-coverage deferral. The true population is five.** The fifth is `## Test plan`'s preamble, spec:1226-1229, "with no live fakeshop surface". It shares no token with the other four and was found only by re-reading the section rather than trusting the list.
- **D8's `docs/spec-037-…` path rot** was widened from one site to three by N4 before this pass, and re-measurement confirmed exactly three — a case where the inherited count was right.

### What is NOT edited, decided rather than skipped

- **`__version__` is `0.0.15`, four patch releases past this card's `0.0.11` target.** Decision 10 and Definition-of-done item 7 describe a cut that **happened**. A shipped-version statement about the release this card closed is correct as it stands and is never refreshed to the current version. Recorded as a `**Post-ship:**` bullet under Decision 10 precisely because the sentence reads stale at a glance and invites exactly that edit.
- **Decision 7's "three net-new root-exported symbols" (N11 / D2)** is the same class. Five file/image symbols are root-exported at `HEAD`, but "three net-new" is a statement about what *this card* added, and a card-scoped completion claim stays true however many a later card adds. The heading keeps its count — which also spares its in-page anchor, used by the companion's `[spec-037-d7]` definition and by spec:1470. What *was* rewritten is the `## User-facing API` sentence that read as a claim about the surface rather than about the card.
- **Decision 8's heading and opening sentence** are card-scoped in the same way and were kept; the standing enumeration underneath was rewritten.
- **Decision 2 (N16)** needs no edit at all, and saying so explicitly is cheaper than a future pass re-deriving it. Recorded as a measured no-change bullet in the companion — an unexamined Decision and a verified-still-true one read identically otherwise.

### Grading `## Current state` clause by clause (N6, the explicitly borderline case)

`BUILD.md` `### `## Current state`: observations stand, predictions do not` licenses a dated **observation** of the pre-build repo to stand while a falsified **prediction** is rewritten, and one bullet can carry both. N6 flagged the last bullet as borderline: a dated observation carrying a **reproducible command whose output has changed**.

Graded, four clauses:

| Clause (spec:480-485) | Kind | Disposition |
| --- | --- | --- |
| "**No example app uses a file/image column.**" | dated observation | **stands** |
| "`grep -rln \"FileField\|ImageField\" examples/` returns nothing" | dated observation carrying a command | **stands, command included** |
| "so the read-side break invalidates no in-repo schema" | inference from the observation, about the pre-build repo | **stands** |
| "and the card's 'synthetic-model tests' scoping is **sufficient** for coverage" | **prediction about this build's outcome** | **rewritten** |

The reasoning on the command: the section opens "A true description of the repo as this spec is authored", which dates every clause under it. A reader who re-runs the grep today measures a different repo — they are not catching an error, they are observing the change the card made. Deleting the command would delete the evidence for a claim that is still true of its own moment. The fourth clause is different in kind: nothing dates a claim about the outcome, and **the build itself falsified it** by adding `MediaSpecimen` and live `/graphql/` tests. It now points at Decision 9, which carries the settled placement.

Every other `## Current state` bullet was read and is observation throughout — the `str` read mapping, the refusing write generator, the un-re-exported `Upload`, the `0.0.10` version line, the shipped `mutations/` subpackage. **None was touched.** That includes the one surviving `#"Upload staged seam (TODO-ALPHA-037-0.0.11)"` citation (spec:449), which names a substring with zero occurrences at `HEAD` but describes the pre-build repo where the seam genuinely existed.

### N7: the ten two-hop `[Risks]` uses — a deliberate call

Slice 0's move left ten `[Risks](#risks-and-open-questions)` uses in contract prose resolving in **two hops**: they land on a spec heading that now contains only a pointer to the companion. Slice 0 left them and flagged the call for this slice.

**Decision: re-point all ten at `[rationale-risks]`.** Every one of the ten sentences promises the reader *deliberation* — a settled test dependency, a fallback, an item deferred — and that deliberation is in the companion, so destination and promise now agree in one hop. The alternative considered and rejected: leave them, which keeps ten contract sentences untouched but makes the indirection permanent and lands every reader who follows one at a stub. Two of the ten were being rewritten for N5 anyway, so "leave them" was never a clean no-op either. Re-pointing is uniform — no per-site judgement a later pass must re-derive — and it converts an inline in-page anchor into a reference-style cross-file link, which is what `START.md`'s convention requires for a cross-file target. The spec keeps its `## Risks and open questions` heading and pointer paragraph; it simply has no inbound in-page anchors any more.

### Implementation steps

1. Verify spec and companion are byte-identical to their post-Slice-1 state, read-only, before the first edit.
2. Re-measure every finding's population at source; record found / edited / left per finding.
3. Grade clause by clause where a bullet carries both an observation and a prediction.
4. Edit the spec: state the corrected contract directly, never the chronology.
5. Append `**Post-ship:**` bullets to the companion under each owning Decision; route Decision-less findings to `## Non-Decision deliberation`.
6. Verify: `check_spec_glossary.py`, `check_trailing_commas.py --check`, anchors, link definitions, a chronology sweep over the finished spec, byte/line counts.

### Test additions / updates

None. This slice adds no code and no test. `pytest` was not run in any form (`AGENTS.md`: no `pytest` after edits unless asked; and no `.py` changed).

### Implementation discretion items

None. Every judgement in this pass — which clauses are observations, which are predictions, whether to re-point the `[Risks]` anchors, whether a card-scoped count is stale — was decided here and is recorded above or in the disposition table below.

### Spec slice checklist (verbatim)

Not applicable. This slice has no `## Slice checklist` sub-bullets in `spec-037`: it discharges the `BUILD.md` `## Spec reconciliation` obligation the shipped spec never received, not a spec contract. The build plan's own checklist row is the closure target:

- [x] Slice 2: spec reconciliation — rewrite every stale contract statement to the shipped shape, and record what changed and why as `**Post-ship:**` bullets in the rationale companion -> `docs/builder/bld-037-slice-2-spec_reconciliation.md`

---

## Final verification (Worker 1)

### Summary

`spec-037` now reads as a clean current contract. Every `SUPERSEDED` clause Slice 1 graded is stated in its shipped form with no chronology anywhere in the file, and the narrative for each change lives in the rationale companion under the Decision that owns it. **26 findings disposed: 21 produced spec edits, 5 were graded no-edit with the reasoning recorded.** The spec grew **97,629 → 104,914 bytes** (1,567 → 1,666 lines); the companion grew **47,663 → 61,482 bytes** (799 → 977 lines). The chronology sweep over the finished spec returns **2 occurrences, both cleared**. No `.py` file, no test, and no out-of-scope doc was touched.

### Baseline: both files byte-identical to their post-Slice-1 state before the first edit

`git stash` / `git checkout` / `git restore` / `git worktree` were **not used at any point** (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`; the tree carries a concurrent session's work).

```shell
git rev-parse HEAD
git show HEAD:docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md > <scratch>/head/spec-037.md
diff <scratch>/head/spec-037.md docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
md5 docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
wc -c -l docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
```

```text
5e6425478152897b7d2c63b11bc6c224ef9e0ab8
DIFFERS-FROM-HEAD  docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
NOT-IN-HEAD        docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
MD5 (…spec-037-upload_file_image_mapping-0_0_11.md)           = 51662b10dd4aa6c74800fa61a697c33e
MD5 (…spec-037-upload_file_image_mapping-0_0_11-rationale.md) = 69e34ddc33b364ee31f55d34b39534ee
    1567   97629 docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
     799   47663 docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
```

**The `HEAD` comparison is the wrong instrument here and says so.** The spec differs from `HEAD` because Slice 0's move is uncommitted, and the companion does not exist at `HEAD` because Slice 0 created it. The claim that matters is *byte-identical to the post-Slice-1 state*, and it is proven against the two md5 digests **Slice 1's own final verification recorded** (`bld-037-slice-1-code_conformance.md` `### Spec changes made (Worker 1 only)`): `51662b10…` and `69e34ddc…`. Both match exactly. The line/byte counts independently match Slice 0's post-move census (1,567 lines / 97,629 bytes). Slice 1 edited neither file, and this pass confirms it.

### Per-finding disposition table

**Legend.** *Found* = occurrences or sites the re-measurement established. *Edited* / *Left* sum to *Found*. "Companion" names where the explanation landed.

#### Worker-0 findings (build plan `## Worker-0 verification pass`)

| # | Finding | Found | Edited | Left (and why) | Companion |
| --- | --- | --- | --- | --- | --- |
| D1 | `path` no longer a default `DjangoFileType` subfield (`spec-048`) | **20 sites** (17 code-span lines / 18 occurrences as recorded, **+3 the instrument could not see**) | 13 | 7 — spec:294, :764, :847, :1245 state that `FieldFile.path` raises or that the per-subfield guard isolates a failing `path`, true on the type that publishes it (4 of these gained an explicit opt-in qualifier rather than a rewrite); spec:400 is `## Problem statement` prose about what the old `str` mapping discarded; spec:567's parenthetical describes **upstream's** four-field type and is accurate (its Status cell was qualified instead); spec:911's `path: str` names upstream's non-null shape | D3 `**Post-ship:**` |
| D2 | Two more root exports than Decision 7's "three net-new" | 3 count sites (`three net-new` ×2, `Three net-new` ×1) | 1 | 2 — the Decision-7 heading and DoD item 7 are **card-scoped completion claims**, true of what this card added, and the heading's anchor is load-bearing | D7 `**Post-ship:**` |
| D3 | `convert_field_output` grew a fourth parameter | 2 signature spellings (spec:244, :827) of 8 total `convert_field_output` occurrences | 2 | 0 | D3 `**Post-ship:**` |
| D4 | `Meta` gained `filesystem_path_fields`, which Decision 8 said it would not | 2 (Decision 8 body; `## Edge cases` final bullet — the second site is N10) | 2 | 0 | D8 `**Post-ship:**` |
| D5 | Decision 9 carried a `> **Superseded**` block | 1 | 0 | 1 — **already discharged by Slice 0**, which moved the block to the companion. Its consequence is N1 | D9 (Slice 0's bullet) |
| D6 | `## Out of scope` still defers the live fakeshop upload surface | 1 of N2's 5-site population | 1 | 0 | D9 `**Post-ship:**` |
| D7 | Deliberative layer never extracted | whole file | 0 | — **discharged by Slice 0** | — |
| D8 | Path + placeholder rot in the Definition of done | `docs/spec-037` ×3, `DONE-NNN` ×2 | 5 | 0 | D1 `**Post-ship:**` |

#### Slice 0 findings (`bld-037-slice-0-rationale_extraction.md`)

| # | Finding | Found | Edited | Left (and why) | Companion |
| --- | --- | --- | --- | --- | --- |
| **N1** | Decision 9's body states a superseded contract with **no marker at all** | 1 Decision body (3 false statements) | 1 — full direct-contract rewrite | 0 | D9 `**Post-ship:**` (the rewrite bullet) |
| **N2** | The same falsified deferral has four sites | **5** (`TODO-BETA-062` ×2 + 3 prose sites sharing no token; **the 5th, `## Test plan`'s preamble, is not in the recorded list**) | 5 | 0 | D9 `**Post-ship:**` |
| N3 | `DONE-NNN-0.0.11` is a two-site placeholder | 2 | 2 | 0 | D1 `**Post-ship:**` |
| N4 | Pre-archive `docs/spec-037-…` path has three sites | 3 | 3 | 0 | D1 `**Post-ship:**` |
| N5 | Two hedges point at a Pillow fallback that was not taken | 2 (`stand-in` ×2, on spec:1127 and :1251) | 2 | 0 | Non-Decision (`TestClient`/hedge entry) + D4 context |
| N6 | `## Current state`'s executable grep claim | 1 bullet, **4 clauses** | 1 clause | 3 clauses — dated observations, licensed by the section header | Non-Decision (`## Current state` entry) |
| N7 | Ten surviving `[Risks]` uses now resolve two-hop | 10 body uses (11 occurrences − 1 link definition) | 10 | 0 | Non-Decision (`[Risks]` entry) |

#### Slice 1 findings (`bld-037-slice-1-code_conformance.md`)

| # | Finding | Found | Edited | Left (and why) | Companion |
| --- | --- | --- | --- | --- | --- |
| N8 | `path` rot in three classes | see **D1** — same population, re-measured to 20 | 13 | 7 | D3 `**Post-ship:**` |
| N9 | Three-param `convert_field_output` at two sites | 2 | 2 | 0 | D3 `**Post-ship:**` |
| N10 | `ALLOWED_META_KEYS` "byte-unchanged" is a **second** D4 site | 1 | 1 | 0 | D8 `**Post-ship:**` |
| N11 | Decision 7's count is true of the card, false of the surface | 1 heading + 1 body sentence | 1 (the `## User-facing API` sentence) | 1 — heading kept; anchor preserved and re-verified | D7 `**Post-ship:**` |
| N12 | Slice-2 sub-check asks for a staged anchor the code correctly lacks | 1 sub-check + 3 dead `#"Upload staged seam"` citations (4 total, 1 in `## Current state`) | 4 (sub-check rewritten to *remove*; 3 citations re-homed on `mutations/inputs.py::model_column_write_annotation`) | 1 — spec:449, a dated `## Current state` observation | D5 + D6 `**Post-ship:**` |
| **N13** | `## Test plan`'s converter bullet mis-homes the `Meta.*_overrides` requirement — **and that mis-homing is why the gap survived** | 1 bullet | 1 — split into a converter-seam bullet and a new `tests/types/test_base.py` bullet | 0 | Non-Decision (highest-value entry) |
| N14 | Same bullet spells the filter-input pin as a `FilterSet` test | 2 spellings (`## Test plan` vs the Slice-1 sub-check) | 1 — `## Test plan` reconciled to the delegation spelling; the `FilterSet` form was **not** restored | 1 — the sub-check's narrowed form is correct as written | Non-Decision |
| N15 | `TestClient` in a falsified future tense | **7** `TestClient` occurrences + 1 `TODO-ALPHA-043` card id | 5 (+ the card id) | 2 — spec:380 and :1458 describe the *wording* Slice 4 put into `README.md`, where scoping the claim to the scalar is still exactly right | Non-Decision |
| N16 | Decision 2 needs **no** edit — say so | whole Decision | 0 | 1 — verified still true clause by clause | D2 `**Post-ship:**` (measured no-change) |
| N17 | Cite the redundant-declaration witness | 1 `## Edge cases` bullet | 1 — merged the two override directions into one bullet carrying all three node ids | 0 | D4 `**Post-ship:**` |
| N18 | Write N13's replacement with the three node ids | 1 | 1 — node ids cited by name, not re-described | 0 | Non-Decision |

**Totals: 26 findings. 21 produced spec edits; 5 were graded no-edit (D5 and D7 discharged by Slice 0, N16 verified still true, plus the card-scoped counts of D2/N11 and Decision 10 held).** Sites left standing with a recorded reason: 24.

### Spec changes made (Worker 1 only)

All line numbers are **pre-edit**. Every row's trigger is Slice 2 (this slice); the *Finding* column names the slice that surfaced it.

| Spec location (pre-edit) | Change | Reason | Finding |
| --- | --- | --- | --- |
| :9-10 opener | `name` / `path` / `size` / `url` → `name` / `size` / `url` | `path` is not a default subfield | D1 |
| :15 opener | `#"Upload staged seam (…)"` → `mutations/inputs.py::model_column_write_annotation` | rule-27 anchor resolving to nothing at `HEAD` | N12 |
| :116-124 Key glossary refs | subfield list corrected; opt-in siblings named; `[Risks]` re-pointed | D1 contract + N7 | D1, N7 |
| :182-185 Key glossary refs | `TestClient` future tense → settled ownership split | the helper shipped | N15 |
| :236-252 Slice 1 sub-check | `path: str | None` dropped; opt-in siblings named; 4-param signature | the third `path` site no grep saw, plus D3 | D1, D3/N9 |
| :292-295 Slice 1 sub-check | per-subfield isolation qualified to an opted-in column | removes a trap for a reader | D1 |
| :302-308 Slice 2 sub-check | "fix the anchor to `TODO-ALPHA-037`" → "remove it" | the sub-check as written would create a `BUILD.md` step-6 finding | N12 |
| :309-310 Slice 2 sub-check | dead seam anchor dropped | rule-27 rot | N12 |
| :331 Slice 2 sub-check | `[Risks]` re-pointed | two-hop | N7 |
| :480-485 `## Current state` | clause 4 (a prediction) rewritten; three clauses and the command left | `BUILD.md` observations/predictions rule | N6 |
| :478-479 `## Current state` | `[Risks]` re-pointed | two-hop | N7 |
| :489-495 Goal 1 | subfield list corrected; `filesystem_path_fields` named | D1 contract | D1 |
| :529-532 `## Non-goals` | live-coverage deferral → what actually ships | falsified deferral | N2 |
| :539-542 `## Non-goals` | `url` / `path` / `size` → `url` / `size` (and the opted-in `path`) | D1 contract | D1 |
| :524-528 `## Non-goals` | `TestClient` "future card" → settled split | the helper shipped | N15 |
| :567 parity table | package column and Status cell qualified; upstream parenthetical **kept** | upstream's four fields are accurately described; ours are not field-for-field | D1 |
| :575-580 borrowing posture | "adopted field-for-field" → two named divergences | D1 contract | D1 |
| :613-616 `## User-facing API` | "No new `Meta` key" → the current key set incl. `filesystem_path_fields` | standing surface claim, now false | D4/N10, N11 |
| :642-663 SDL fences | `path: String` removed from both types; opt-in paragraph added | **the site the code-span sweep could not see**, and the one a reader copies | D1 |
| :666-682 nullability para | subfield list corrected | D1 contract | D1 |
| :773 Decision 1 | pre-archive path → `docs/SPECS/` + `docs/SPECS/appx/` companions | path rot | D8/N4 |
| :797-804 Decision 3 | default subfields corrected; opt-in siblings and the second map documented | D1 contract | D1 |
| :827 Decision 3 | 4-param signature + what `expose_filesystem_path` carries | D3 | D3/N9 |
| :909-911 Decision 4 | subfield-nullability bullet corrected | D1 contract | D1 |
| :925 Decision 4 | `{ path }` selection example qualified | D1 contract | D1 |
| :939 Decision 4 | `[Risks]` re-pointed | two-hop | N7 |
| :970 Decision 6 | dead seam anchor → live symbol | rule-27 rot | N12 |
| :1003 Decision 6 | `[Risks]` re-pointed | two-hop | N7 |
| :1030-1039 Decision 8 | standing `Meta`-key enumeration rewritten; heading + opener kept | D4 standing claim; heading is card-scoped | D4/N10 |
| :1057-1097 **Decision 9** | **full direct-contract rewrite** to the shipped two-tier split; fixture paragraph re-scoped; pointer line de-chronologised | the body stated a retracted contract with no marker | **N1**, N2 |
| :1127 impl. plan | Pillow hedge dropped; `FilterSet` → delegation-path spelling | the fallback was not taken | N5, N14 |
| :1155-1160 `## Edge cases` | override bullet merged, both directions stated, **three node ids cited**; `path` bullet qualified | the shipped witness now exists | **N17**, D1 |
| :1173, :1185, :1210 `## Edge cases` | `[Risks]` re-pointed; Pillow dependency stated as shipped | two-hop; hedge | N7, N5 |
| :1211-1214 `## Edge cases` | multipart "until the `0.0.14` helper lands" → settled split | the helper shipped | N15 |
| :1220-1222 `## Edge cases` | "`ALLOWED_META_KEYS` byte-unchanged" → card-scoped + names the key those sets carry | flatly false at `HEAD` | **N10** |
| :1226-1229 `## Test plan` | "with no live fakeshop surface" → the two-tier split | **the 5th N2 site, not in the recorded list** | N2 |
| :1231-1238 `## Test plan` | **converter bullet split**; `Meta.*_overrides` re-homed on `tests/types/test_base.py` with three node ids; delegation spelling | **the mis-homing that let the gap survive** | **N13**, N14, N18 |
| :1239-1253 `## Test plan` | `path` qualified; Pillow hedge dropped | D1, N5 | D1, N5 |
| :1279-1281 `## Test plan` | "Live HTTP tests. None required unless…" → what ships | falsified deferral | N2 |
| :1341-1344 `## Doc updates` | `DONE-NNN-0.0.11` → `DONE-037-0.0.11` | placeholder | N3 |
| :1357-1359 `## Out of scope` | `TODO-ALPHA-043-0.0.14` → `DONE-043-0.0.14`; tense settled | card id now `DONE` | N15 |
| :1366-1369 `## Out of scope` | live-surface deferral → the products/fakeshop activation only | falsified deferral | D6/N2 |
| :1384-1388 DoD item 1 | archived paths; rationale companion added; correct invocation | path rot | D8/N4 |
| :1393 DoD item 2 | `path` clause corrected | false completion claim | D1 |
| :1463 DoD item 6 | `DONE-NNN-0.0.11` → `DONE-037-0.0.11` | placeholder | N3 |
| :1458 DoD item 6 | `TestClient` tense settled | the helper shipped | N15 |

**Spec status-line re-verification (this spawn).** `worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. Read spec:1-40 before the first edit: the title, the "Shipped in `0.0.11` (card `DONE-037-0.0.11`)" opener, `Status: **SHIPPED (`0.0.11`)**`, `Owner:`, and `Predecessors:`. The header carries no "not yet shipped" / "remains to be" claim this build falsified, and every predecessor spec it names exists on disk. **No status-line edit was owed.** Its one stale element — the dead `#"Upload staged seam"` citation at spec:15 — is contract-body prose, was routed to this slice by both prior spawns, and is fixed above.

### Companion changes (append-only, `**Post-ship:**` convention)

`docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md`, whose own header documents this append convention.

| Section | Added |
| --- | --- |
| Header, "How later passes append to this file" | one sentence: a Decision *verified still true* earns a bullet too, since an unexamined Decision and a measured no-change read identically otherwise |
| Decision 1 `### Changes this Decision underwent` | `**Post-ship:**` — the `NEXT.md` Step 8 archive move, and the three sites that went on naming the pre-archive path (one of them a `check_spec_glossary.py` invocation that would fail as written) |
| Decision 2 | `**Post-ship:**` — **measured no-change**, with the `Upload`-mention resolution that proves the scope boundary still holds |
| Decision 3 | `**Post-ship:**` — `spec-048` commit `567cc6d0`, why the path was moved behind an opt-in, what it replaced, the fourth parameter, and **the three sites the code-span instrument could not see** |
| Decision 4 | two `**Post-ship:**` — the subfield-nullability narrowing; and the `required_overrides` test gap this cycle closed, with the three node ids |
| Decision 5 | `**Post-ship:**` — no contract change; the anchor was *removed* rather than re-pointed, which is `BUILD.md` step 6's required outcome |
| Decision 6 | `**Post-ship:**` — no contract change; only the dead seam citations moved, and why the `## Current state` one stayed |
| Decision 7 | `**Post-ship:**` — two further exports; **why the count was not changed** |
| Decision 8 | `**Post-ship:**` — `Meta` half false as a standing claim, setting half still true; and **the second site a Decision-only fix would have missed** |
| Decision 9 | `**Post-ship:**` ×2 + 1 — the direct-contract rewrite, what it replaced, and **the five-site population** where the finding named four |
| Decision 10 | `**Post-ship:**` — **deliberately not updated**, and why the sentence invites the wrong edit |
| `## Non-Decision deliberation` | rewrote the `## Current state` entry into the clause-by-clause grade; added the `[Risks]` re-pointing call with its rejected alternative; the N13 mis-homing entry; the N14 spelling reconciliation; the N15 `TestClient` sweep with its two deliberate leaves; and the maintainer routing below |

### Verification, with real output

**1. `check_spec_glossary.py` exits 0.**

```shell
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
```

```text
OK: 20 terms - all have glossary entries and at least one spec link.
EXIT=0
```

Same 20 terms as the pre-flight and post-Slice-0 baselines. Two terms were at risk in this pass and were checked: `FilterSet` lost its `## Test plan` link to the N14 spelling change but keeps links at spec:812 and :1196; `TestClient` was rewritten at five of seven sites and keeps two.

**2. Markdown-layout gate on both edited files.**

```shell
uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
```

```text
EXIT=0
```

Both files carry all 10 canonical group headers in order under a single `<!-- LINK DEFINITIONS -->` delimiter, verified programmatically:

```text
comment markers (spec):      ['LINK DEFINITIONS', 'Root', 'docs/', 'docs/SPECS/', 'docs/builder/', 'django_strawberry_framework/', 'tests/', 'examples/', 'scripts/', '.venv/', 'External']
comment markers (companion): ['LINK DEFINITIONS', 'Root', 'docs/', 'docs/SPECS/', 'docs/builder/', 'django_strawberry_framework/', 'tests/', 'examples/', 'scripts/', '.venv/', 'External']
```

Paths were **re-relativized, not copied across**: the spec sits in `docs/SPECS/` (`../GLOSSARY.md`, `../../AGENTS.md`), the companion in `docs/SPECS/appx/` (`../../GLOSSARY.md`, `../../../AGENTS.md`), and `docs/SPECS/appx/` shares its parent's `<!-- docs/SPECS/ -->` group per `START.md`.

**3. Anchors, reference ids, and definition targets — both files.**

Fenced code blocks are stripped before the scan, so an SDL example cannot forge an anchor.

```text
docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
  anchors: 80 uses / 13 distinct, unresolved=[]
  linkdefs: 73 defs / 73 used, dangling=[], unused=[], missing_on_disk=[]
docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
  anchors: 36 uses / 14 distinct, unresolved=[]
  linkdefs: 35 defs / 35 used, dangling=[], unused=[], missing_on_disk=[]
```

Every in-page anchor resolves, every reference id has a definition, every definition is used, and every non-URL definition target exists on disk. The spec's anchor count fell from 88 to 80 exactly because the ten `[Risks]` in-page uses became reference-style cross-file links while two new in-page `Decision 9` references were added.

**Heading-rename hazard, checked before acting (N11).** Decision 7's heading carries the disputed count, so renaming it would break `#decision-7--public-surface-three-net-new-root-exported-symbols` — used by spec:1470 and by the companion's `[spec-037-d7]` definition. The heading was kept for the independent reason that its claim is card-scoped and true; the anchor check confirms nothing moved.

**4. Population sweep per finding.** The disposition table above is the sweep. Its supporting residual measurements, each run against the **finished** spec:

```text
must be 0:
  DONE-NNN                                              -> 0
  docs/spec-037                                         -> 0
  TODO-ALPHA-043                                        -> 0
  convert_field_output(field, type_name, *, force_nullable=None)  -> 0
  "byte-unchanged;"                                     -> 0
  "^  path: String$" (SDL fences)                       -> 0
  "no live fakeshop surface"                            -> 0

deliberate residuals, each confirmed in place:
  "Upload staged seam"                                  -> 1  (spec:459, section ## Current state)
  "#risks-and-open-questions"                           -> 1  (the [rationale-risks] link DEFINITION target)

new vocabulary now present (was 0 for the first four before this pass):
  DjangoFilePathType      -> 8
  DjangoImagePathType     -> 7
  filesystem_path_fields  -> 12
  expose_filesystem_path  -> 3
  MediaSpecimen           -> 5
  test_meta_required_overrides_forces_non_null_file_output -> 2
```

Occurrences of a code-span `` `path` `` went **17 lines / 18 occurrences → 22 lines / 25 occurrences**. Stated rather than buried: the corrected text names the opt-in explicitly wherever it removes a false default-subfield claim, so the token's frequency rises while its falsehood count goes to zero. A sweep that read the raw count as a regression indicator would draw the wrong conclusion, which is why the population was graded line by line and never `sed`-ed.

**5. Chronology sweep over the finished spec.** Fourteen forbidden shapes, matched case-insensitively against **whitespace-flattened** text with newlines included, so a phrase wrapped across two lines cannot hide:

```text
docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
  total chronology-word occurrences: 2 | previously=2
    L178:  previously-`NotImplementedError`-raising write input over a file column now
    L1357: previously-`NotImplementedError` path now succeeds.
```

Both were opened and read. Each describes what the **shipped code path** used to do — the write input this card converted from fail-loud to `Upload` — not what the spec used to say. That is contract, not spec self-narration, and it is implementation-relevant at L1357, where it names what the mutation-resolver test proves. **Zero chronology sites survive in contract prose.** `superseded`, `post-ship`, `no longer`, `has since`, `formerly`, `used to`, `replaced by`, `review round`, `as of`, `retract`, `amendment`, `earlier draft` and `originally` are all **0**.

Slice 0's equivalent sweep found 3 survivors including one `post-ship` inside its own Decision-9 pointer line; that line was rewritten here, so the count improved rather than merely holding.

The same sweep over the companion returns **45 occurrences**, and that is the design: the chronology is exactly what the companion is for.

**6. Byte and line counts, before and after.**

| File | Before (post-Slice-1) | After | Delta |
| --- | --- | --- | --- |
| `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` | 1,567 lines / **97,629 bytes** | 1,666 lines / **104,914 bytes** | +99 lines / **+7,285 bytes** |
| `docs/SPECS/appx/…-rationale.md` | 799 lines / **47,663 bytes** | 977 lines / **61,482 bytes** | +178 lines / **+13,819 bytes** |

The companion grew roughly twice as much as the spec, which is the split working as intended: the corrections are terse contract statements, the explanations are not.

**7. Not run, and why.** `uv run ruff format .` / `ruff check --fix .` — no `.py` file was touched, and running them across `.` would write into ~55 package files a concurrent session has dirty. `pytest` — forbidden after edits without an explicit request, and this slice has no code to exercise.

### Routed to the maintainer (out of this cycle's reach)

The maintainer fenced this cycle to **spec files and package `.py` source**. Three items surfaced that the fence puts out of reach. None is a defect in `spec-037`; each is recorded rather than acted on, and the first two are also in the companion's `## Non-Decision deliberation`.

1. **`docs/GLOSSARY.md` is the published home of contracts this pass corrected in the spec.** Its `DjangoFileType` / `DjangoImageType` entries and its `Meta.required_overrides` entry carry the same file/image contract; Slice 1 confirmed the entries exist at `shipped (0.0.11)` but nobody checked whether they still describe the post-`spec-048` default-subfield shape. Worth a look when the fence lifts.
2. **`DjangoFilePathType` / `DjangoImagePathType` are root-exported symbols** (`__init__.py:49-52`, `:132-136`) whose `docs/GLOSSARY.md` and `docs/TREE.md` presence this cycle could neither verify nor fix. They are `spec-048`'s to own; flagged because this pass introduced them into `spec-037`'s vocabulary, where they previously had **zero** occurrences.
3. **Four rows fail the full package sweep**, escalated in Slice 1 and unchanged here: `tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`, `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`, and two rows in `tests/test_sets_mixins.py`. All sit in the concurrent session's baseline-dirty surface, all were proven independent of this build's diff, and **only the maintainer can run a clean `HEAD` tree** to confirm they are pre-existing. Repeated so the final gate's sweep is not read as this build's failure.

### DRY check across this slice and prior accepted slices

No new duplication. This slice adds no helper, no constant and no code; against Slice 0 (which moved spec text) and Slice 1 (which added three tests) there is no shared shape to collide with. The one duplication risk a reconciliation carries is **restating in the spec the explanation that belongs in the companion** — the corpus's recurring failure mode, and the exact thing the maintainer's instruction forbids. The chronology sweep above is the mechanical control against it, and it is clean.

The second risk is a correction that lands in one place and not its siblings. The disposition table's found/edited/left arithmetic is the control against that, and it caught two under-counted populations before either could become a partial fix.

### Failability proofs

`None; this pass introduced no new boundary.` This slice lands no runtime code, so there is no guard, gate or rejection path to prove failable. The proof obligations it *does* carry are the population sweeps and the chronology sweep, run and quoted above. **Each carries its own negative control**, which is what makes a zero mean something:

- the residual sweep's `must be 0` block is paired with a `new vocabulary now present` block, so a zero that came from deleting the subject rather than fixing it would show as a zero in **both**;
- the chronology sweep is paired with the same sweep over the companion (45 occurrences), so a zero produced by a broken command would show as a zero there too;
- the anchor and link-definition scan reports `dangling` and `unused` in both directions, so a definition that lost its last use cannot pass as clean.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Not applicable; this slice writes no .py file and declares floor-verification scope none.` Slice 1's re-declared scope was owned and run by its Worker 2 build pass (`/tmp/dsf-floor-037` — Python 3.10.19 / django 5.2.16 / strawberry-graphql 0.316.0, `6 passed`) and confirmed at its final verification. The final gate is the backstop for that record, not a second owner.

### Final status

`final-accepted`. This pass owns the transition (`BUILD.md` `### Procedural-closure slices`; no Worker 2 build and no Worker 3 review ran, and none was owed). The `037` cycle's payload is discharged: `spec-037` states the shipped contract directly with zero chronology, the rationale companion carries every explanation keyed to the Decision it belongs to, and the cross-slice integration pass is unblocked.

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
