# Build: Review round 1, cohort A — residue repair (spec + rationale companion)

Spec reference: `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` (Decision 5 at 983-1002; `## Test plan` at 1129-1133; `## Out of scope` at 1450-1468) and its rationale companion `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` (Decision 5's `### Changes this Decision underwent` at 491-519; Decision 9's at 662-696)
Status: final-accepted

**Review round, cohort A** (`docs/builder/BUILD.md` `## Review rounds`; the ownership partition is in `docs/builder/build-037-upload_file_image_mapping-0_0_11.md` `## Review round 1 — residue repair`). Worker 1 alone under the maintainer's standing carve-out that a spec-only change needs no builder, so this is one combined Plan + Final-verification block and Worker 1 sets `Status:` itself. Cohort B owns `examples/fakeshop/apps/products/schema.py` and `examples/fakeshop/test_query/test_products_api.py`; no file appears in both cohorts.

Hot-path declaration: **none** (copied from the plan as written). No runtime code is touched.
Floor-verification scope: **none**. This cohort writes no `.py` file, so it declares no scope and re-declares nothing.

Raw `path:NN` references are used below under `AGENTS.md` rule 27's per-cycle-artifact carve-out. Spec and companion line numbers are **post-edit** unless the row says pre-edit.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately not run, recorded rather than silently skipped: this cohort proposes no helper, no constant, no validation branch and no test helper, and touches no `.py` file at all. The `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning` obligation is scoped to "before proposing any new helper-like logic"; there is none to propose.
- **Existing patterns reused.** R2's explanation is written on the companion's own `**Post-ship:**` shape, read from two existing exemplars first (Decision 4's two bullets at 442-461 pre-edit, Decision 8's at 613-626 pre-edit): a bolded `**Post-ship:**` lead, the false claim quoted, the measurement that falsifies it, whether a contract moved, what the sentence now says, and — where one exists — the second site a single-site fix would have left standing. No new shape invented.
- **New helpers justified.** None. One new link definition, `[init]`, added to the companion because the R2 bullet cites `__init__.py` and the companion had no definition for it; the spec already had one.
- **Duplication risk avoided.** The one duplication a round like this can introduce is **restating in the spec the explanation that belongs in the companion** — the corpus's recurring failure mode and the exact thing `docs/builder/BUILD.md` line 94 forbids. The plan prevents it by writing the corrected contract into the spec as a bare present-tense sentence and putting every word of narrative in the companion; the chronology sweep in `### 5. Chronology sweep over the finished spec` is the mechanical control, and it is clean.

### Implementation steps

1. Verify the two card-id ground-truth headings in `KANBAN.md` and card 066's lifecycle state, so the renumber is proven a renumber and not a lifecycle flip.
2. Re-derive both findings' populations at source with three instruments each, plus a whitespace-flattened pass, and print every count **before** editing so a post-edit zero has a non-zero to be measured against.
3. Prove the `[kanban]` claim: all five R1 sites carry the id as visible link text over one generic definition, so no link definition, heading, or in-page anchor moves.
4. Re-verify all three R2 measurements at source before touching Decision 5.
5. Edit: renumber all five R1 sites; rewrite Decision 5's sentence to the corrected contract with no chronology; append the R2 `**Post-ship:**` bullet to the companion.
6. Re-run every instrument, the two gates, the anchor / link-definition scan, and the chronology sweep; prove the non-edit of everything else by reverse-application.

Line numbers in this artifact are pin-at-write-time. Every anchor was pinned by content at edit time, never by the line number the dispatch supplied — the dispatch's five R1 line numbers happened to be exact, which is recorded as a measurement below, not assumed.

### Test additions / updates

None. This cohort adds no code and no test. `pytest` was not run in any form (`AGENTS.md`: no `pytest` after edits unless asked; and no `.py` changed). No `--cov*` flag was passed to anything.

### Implementation discretion items

None. Every judgement in this pass — each R1 site's tense and referent, whether the verbatim-reproduction collision is inside R1's subject, the exact wording of the corrected Decision-5 sentence, and where the R2 narrative lands — was decided here and is recorded below.

### Dispatched findings checklist

`docs/builder/BUILD.md` `### Dispatched findings checklist`, in the `### Spec slice checklist (verbatim)` position. One box per finding dispatched to cohort A. Worker 1 wrote them and, this cohort having no Worker 2, ticks and audits them itself.

- [x] **R1 — `TODO-BETA-062-0.1.5` names the wrong card. 5 sites.** "The 2026-08-29 board inserts moved the fakeshop-activation card to `TODO-BETA-066-0.1.5` (`KANBAN.md` heading `### [TODO-BETA-066-0.1.5 - Fakeshop GraphQL schema activation]`); `TODO-BETA-062-0.1.3` is now the Aggregation subsystem. Wrong in subject, number and version at once. Sites: spec 1132, 1461; companion 652, 670, 695. A renumber, never a lifecycle flip." Sites re-pinned by content at edit time; card 066's `- Status: To Do` re-read at `KANBAN.md:1433`.
- [x] **R2 — Decision 5 claims a package-root export that does not exist. 1 site.** "Spec 991-992 says `scalars.py` \"(and the package root, `__init__.py`)\" re-export `Upload` \"(and `UploadDefinition`)\". `grep -c 'UploadDefinition' django_strawberry_framework/__init__.py` -> 0. `scalars.py` does export both. Slice 1 graded D-5 BUILT-CONFORMANT citing `scalars.py` only and never tested the `__init__.py` half." Symbol-qualified anchors: `django_strawberry_framework/scalars.py` #"from strawberry.file_uploads.scalars import Upload, UploadDefinition"; `django_strawberry_framework/__init__.py` #"from .scalars import BigInt, Upload, strawberry_config".

---

## Final verification (Worker 1)

### Summary

Both findings are closed. R1's five sites now read `TODO-BETA-066-0.1.5`; the wrong id has **0** occurrences in either owned file under all three instruments and the replacement has **5**, matching the dispatch's expectation exactly. R2's Decision-5 sentence states the corrected contract directly — both modules re-export `Upload`, `UploadDefinition` stops at `scalars.py` — with no amendment block, no retraction, no hedge and no chronology; the explanation is a new `**Post-ship:**` bullet under Decision 5's `### Changes this Decision underwent` in the companion. `check_spec_glossary.py` and `check_citations.py` both exit 0. **One further defect was found and fixed inside R1's own subject** (the companion's "reproduced verbatim below" claim, which R1's fifth edit falsified) and **one measured item is routed to the maintainer** (48 occurrences of the same wrong card id across 13 out-of-fence surfaces, the kanban DB included). No `.py` file, no test, and no out-of-scope doc was touched.

### Ground truth, read before either edit

```shell
grep -n '^### \[' KANBAN.md | grep -E '06[0-9]'
sed -n '1157p;1430p' KANBAN.md
awk 'NR>=1430 && NR<=1450' KANBAN.md | grep -n 'Status'
grep -c '^### \[TODO-BETA-062-0\.1\.5' KANBAN.md
```

```text
1157: ### [TODO-BETA-062-0.1.3 - Aggregation subsystem](KANBAN.html#aggregation_subsystem)
1430: ### [TODO-BETA-066-0.1.5 - Fakeshop GraphQL schema activation](KANBAN.html#fakeshop_graphql_schema_activation)
4:- Status: To Do            (i.e. KANBAN.md:1433, inside card 066)
0                            (the id TODO-BETA-062-0.1.5 heads no card at all)
```

Three facts, each load-bearing and each measured rather than accepted from the dispatch:

- The fakeshop-activation card is `TODO-BETA-066-0.1.5`. **Subject, number and version all move** — `062` is now a `0.1.3` card with an unrelated subject, so the stale spelling is not merely a wrong number, it silently redirects a reader to the aggregation card.
- Card 066 is `Status: To Do`, so `DONE-066-…` would be false. **This is a renumber, not a lifecycle flip**, and the rewrite keeps the `TODO-BETA-` prefix.
- `TODO-BETA-062-0.1.5` heads **no** card heading in `KANBAN.md`. The stale id is a dead reference in visible prose even though the generic `[kanban]` link it sits over still resolves.

### R1 — population, before and after, three instruments plus a flattened pass

Occurrences were counted, never matching lines (`grep -o … | wc -l`), and the whole-file text was also whitespace-flattened with newlines included so a citation wrapped across two lines could not hide. **Every count was printed before the first edit**, so each post-edit zero is measured against a non-zero the same instrument produced.

| Instrument | Spec before | Companion before | Spec after | Companion after |
| --- | --- | --- | --- | --- |
| `TODO-BETA-062-0.1.5` (full id) | **2** | **3** | **0** | **0** |
| `TODO-BETA-062` (version-less) | **2** | **3** | **0** | **0** |
| `062` (bare) | **2** | **3** | **0** | **0** |
| `TODO-BETA-066-0.1.5` (replacement) | 0 | 0 | **2** | **3** |
| `TODO-BETA-066` (version-less) | 0 | 0 | **2** | **3** |
| `066` (bare) | 0 | 0 | **2** | **3** |

**Totals across both files: 5 before, 0 after; 0 replacement before, 5 after.** Exactly the dispatch's expectation, and the second half is the control that makes the first half mean something — a zero produced by *deleting* the subject would read as a zero in **both** blocks.

The flattened pass agreed with the line-oriented one at every cell (spec 2 / companion 3 before, spec 2 / companion 3 of the replacement after), and four wrap-hazard spellings (`TODO- BETA`, `BETA- 062`, `062- 0.1.5`, and the flattened full id) all returned 0 both before and after — so no wrapped citation was hiding from the line-oriented instrument, and no population member went unseen.

**The bare-`062` instrument is the one that could have found a site the other two cannot** (a version-less or differently-prefixed spelling). It returned the same 2 / 3 as the full id in both files, so the population is closed: in these two files the id occurs in exactly one spelling.

### R1 — the five sites, each graded by tense and referent before editing

All five carry the id as **visible link text** over the one generic `[kanban]` definition, which was verified before and re-verified after (`### 4. Every `[kanban]` use still resolves`). **No link definition, heading, or in-page anchor moved**, and the anchor and link-definition scan below proves it rather than asserting it.

| # | Site (pre-edit) | Section and shape | Tense / referent | Disposition |
| --- | --- | --- | --- | --- |
| 1 | spec:1132 | `## Test plan`, Decision-9 two-tier paragraph: "The broader products/fakeshop activation **remains** [id]; it is not a precondition for the file/image surface's own live coverage." | present tense, live referent — where work still stands | **renumbered** |
| 2 | spec:1461 | `## Out of scope`, bullet: "**The broader products/fakeshop activation** — [id]." | present-tense tracked-elsewhere pointer, live referent | **renumbered** |
| 3 | companion:652 | Decision 9 `### Changes this Decision underwent`, `- **Revision 1**` log bullet: "…and the deferral of a live fakeshop upload surface to [id]." | historical *frame*, but the id names the live card the deferral pointed at — not a quotation of a document | **renumbered** |
| 4 | companion:670 | Decision 9, `- **Post-ship, the direct-contract rewrite.**` bullet: "What it replaced: \"No fakeshop model…\", \"live `/graphql/` tests are added **only** if…\", and the deferral of a live upload surface to [id]…" | the two neighbours are quoted verbatim in quotation marks; **this third item is unquoted paraphrase** naming the live card | **renumbered** |
| 5 | companion:695 | Decision 9, inside the `> **Superseded (post-ship, 2026-06-20 round-4 review).**` blockquote: "The broader products/fakeshop activation **stays** [id]." | present tense, live referent — *inside* a block the companion frames as a verbatim reproduction | **renumbered**, and the framing sentence corrected (see `### The one further defect found`) |

**The dispatch's exception was tested against site 5 and does not fire.** The exception withholds a renumber where the id is "a verbatim quotation of text that still reads `062` elsewhere in the tree". Site 5 *is* a verbatim quotation — proven, not assumed:

```shell
git show HEAD:docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md > <scratch>/spec-037-HEAD.md
awk 'NR>=1247 && NR<=1263' <scratch>/spec-037-HEAD.md > <scratch>/head-block.txt
awk 'NR>=681 && NR<=697' <companion> > <scratch>/comp-block.txt
diff <scratch>/head-block.txt <scratch>/comp-block.txt && echo VERBATIM-IDENTICAL
```

```text
VERBATIM-IDENTICAL
```

— but its **source** no longer reads `062` anywhere in the working tree: Slice 0 cut the block out of the spec, and the working-copy spec carries it nowhere. The text survives only in `HEAD`'s blob, which is git history, not the tree. So the exception's condition is unmet, the default rule applies, and the dispatch's own grading of the sentence ("stays [id]" — where work still stands) is what decides it. **Renumbered.** Recorded at this length because the next reader's first instinct is that a verbatim historical block is untouchable, and only the measurement settles it.

**No site was left un-renumbered.** There is no exception to record.

### R2 — all three measurements re-verified at source before the edit

Both `.py` files were confirmed **byte-identical to `HEAD`** first, so they are gradeable against the working copy directly rather than through a blob (`git show HEAD:<path>` into a scratch path outside the repo, then `cmp`):

```text
SAME  django_strawberry_framework/__init__.py
SAME  django_strawberry_framework/scalars.py
```

| Measurement | Command | Result |
| --- | --- | --- |
| the root does not export `UploadDefinition` | `grep -c 'UploadDefinition' django_strawberry_framework/__init__.py` | **0** |
| `scalars.py` imports both | `grep -n 'UploadDefinition' django_strawberry_framework/scalars.py` | `25:from strawberry.file_uploads.scalars import Upload, UploadDefinition` and `40:    "UploadDefinition",` — i.e. in its `__all__`; **2** occurrences |
| the root exports `Upload` but not `UploadDefinition` | `grep -n '\bUpload\b' django_strawberry_framework/__init__.py` | `45:from .scalars import BigInt, Upload, strawberry_config  # noqa: E402` and `155:    "Upload",` — `Upload` in the import and in `__all__`, `UploadDefinition` in neither |

All three confirmed. **The sentence was true of `scalars.py` and false of the package root.**

**S2a read and deliberately not changed.** The `## Slice checklist` Slice-2 sub-check at spec:312 reads "[`scalars.py`][scalars]: re-export `Upload` (and `UploadDefinition`) from `strawberry.file_uploads.scalars` for the public surface" — scoped to `scalars.py` alone, with no mention of the root. Correct as written, untouched, and it is the spec's **internal** evidence that only the Decision-5 sentence was wrong.

**One neighbouring site inspected and left, with its reason.** spec:466-473, in `## Current state`, says "**`Upload` is not re-exported.** … Strawberry already ships `Upload = NewType(\"Upload\", bytes)` + `UploadDefinition` at `strawberry.file_uploads.scalars` **and** registers it in `DEFAULT_SCALAR_REGISTRY` … the package simply does not re-export it". That is a **dated observation of the pre-build repo** (the section opens "A true description of the repo as this spec is authored") and its `UploadDefinition` clause describes what *Strawberry* ships, which is true. It makes no claim about the package root's exports. Not an R2 site; left.

### The rewritten Decision 5 sentence, verbatim as it now stands

spec:991-994:

```text
[`scalars.py`][scalars] therefore only **re-exports** `Upload` and its
`UploadDefinition` from `strawberry.file_uploads.scalars` for the public surface,
and the package root ([`__init__.py`][init]) re-exports `Upload` alone; the
package adds **no** `_PACKAGE_SCALAR_MAP` entry for it.
```

It discharges every constraint the dispatch set, each checked rather than assumed:

- **States the corrected contract directly.** Present tense, no amendment block, no retraction paragraph, no "as of round 1", no chronology, no dated parenthetical. `docs/builder/BUILD.md` line 94: the spec reads as a clean current contract, as though it had been right from the start.
- **Preserves the deliberate `BigInt` contrast.** The clause "the package adds **no** `_PACKAGE_SCALAR_MAP` entry for it" is kept **as the sentence's final clause**, which is what the next paragraph's "This is the deliberate contrast with [`BigInt`][glossary-bigint-scalar]" refers back to. Moving or dropping it would have stranded that paragraph's opening pronoun — checked by re-reading spec:996-1001 against the new sentence.
- **Preserves the `_PACKAGE_SCALAR_MAP` clause itself**, unweakened.
- **Both link definitions still used.** `[scalars]` and `[init]` are both retained in the sentence, so neither definition lost its last use in the spec (`unused=[]` below).

### The new `**Post-ship:**` bullet, verbatim as it now stands

Appended to the companion's Decision 5 `### Changes this Decision underwent` at 505-518, after the existing `- **Post-ship: no change to the Decision.**` bullet — the companion is append-only during a round (`docs/builder/worker-1.md` `### Performing the rationale move` rule 4), so the prior bullet was not rewritten. Two existing `**Post-ship:**` bullets were read first for shape (Decision 4's and Decision 8's) and the shape is matched, its closing "second site / internal evidence" move included.

```text
- **Post-ship:** the Decision's re-export sentence claimed [`scalars.py`][scalars]
  **and the package root** re-export `Upload` *and* `UploadDefinition`. True of
  `scalars.py`, false of the root: `scalars.py:25` is
  `from strawberry.file_uploads.scalars import Upload, UploadDefinition` and lists both
  in its `__all__`, while [`__init__.py`][init] imports and exports `Upload` alone —
  `grep -c 'UploadDefinition' django_strawberry_framework/__init__.py` is **0** at
  `HEAD`, against **2** for `scalars.py`. No contract moved: the root never carried
  `UploadDefinition`, so this was a false description of the shipped surface rather
  than a later card's deliberate change, and the sentence now states the split — both
  modules re-export `Upload`, `UploadDefinition` stops at `scalars.py`. The spec's own
  `## Slice checklist` Slice-2 sub-check had scoped the `UploadDefinition` re-export to
  `scalars.py` correctly all along, which is the internal evidence that only the
  Decision-5 sentence was wrong, and is why the bullet above graded both halves
  conformant while citing `scalars.py` alone.
```

It records what the spec used to claim, that the claim was false **only** of the root, how that was measured (both greps with both results), and — the part that keeps the two bullets from reading as a contradiction — that **no contract moved**, so the prior bullet's "no change to the Decision" stays true of the contract while this one records the false description of it.

**R1 gets no rationale bullet.** A card renumber is not a contract change, and none was manufactured. The companion's `**Post-ship:**` count therefore rises by exactly one.

### The one further defect found, and why fixing it is inside R1's subject

**R1's fifth edit falsified a neighbouring sentence in the same file.** The companion frames the superseded blockquote, four bullets above it, as a verbatim reproduction; renumbering a card id inside the block makes that framing false, and the byte-comparison above is exactly the instrument that would catch it. This is not scope-widening — it is the direct consequence of an edit R1 ordered, at the site R1 named, in a file this cohort owns.

Fixed at companion:671-674 (pre-edit 657-659), one clause:

```text
  (the spec "never narrates its own history"). The block is reproduced below,
  verbatim but for the fakeshop-activation card id, which carries its current
  spelling; its `below` and `follows` references point at the Decision-9 body it used
  to precede in the spec, not at anything in this file.
```

Residual sweep: `"reproduced verbatim below"` → **0** in both files. The correction is chronology, and it is in the **companion**, which is where chronology belongs; the spec's chronology count is unchanged at 2 (below).

### Routed to the maintainer, with the measurement

**The same wrong card id has 48 occurrences across 13 surfaces this cohort's fence puts out of reach**, and `TODO-BETA-062-0.1.5` heads no card in `KANBAN.md` at all, so every one is a dead reference. Measured after this cohort's edits, occurrences not lines, tracked files via `git grep -ln` and untracked via `git ls-files --others --exclude-standard`, with `grep -ao` so the kanban DB is not skipped as binary:

| Surface | Occurrences |
| --- | --- |
| `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md` | 11 |
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | 6 |
| `docs/SPECS/spec-032-full_relay-0_0_9.md` | 5 |
| `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | 4 |
| `KANBAN.html` | 3 |
| `KANBAN.md` | 3 |
| `TODAY.md` | 3 |
| `docs/SPECS/spec-041-channels_router-0_0_14.md` | 3 |
| `examples/fakeshop/db.sqlite3` (the kanban DB) | 3 |
| `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` | 2 |
| `docs/SPECS/spec-030-connection_field-0_0_9.md` | 2 |
| `docs/builder/DONE/build-034-permissions-0_0_10.md` | 2 |
| `docs/SPECS/spec-044-debug_extension-0_0_14.md` | 1 |
| **Total** | **48** |

`KANBAN.md:610` records why: a 2026-08-07 sweep deliberately re-pointed 32 occurrences of the *then*-dead `TODO-BETA-053-0.1.5` onto `TODO-BETA-062-0.1.5`, and the 2026-08-29 inserts moved that card again. **The population is therefore recurring and cumulative, and it now includes `KANBAN.md` and the kanban DB themselves** — which the maintainer's fence, `AGENTS.md`'s DB-generated-doc rule (edit the DB, re-render) and `START.md`'s don't-regenerate-mid-flight rule all put outside a worker's reach here. Not edited, not reverted; routed with the count so the next sweep starts from a measurement instead of a grep vocabulary.

Two smaller notes on the same population, for the same reader:

- This cycle's own per-cycle artifacts carry 13 more (`bld-037-review-1-residue_repair_source.md` 10, `build-037-…md` 2, `bld-037-slice-0-…md` 1). Those are `bld-*` / build-plan scratchpads that close with the cycle (`START.md` `## Temp artifact conventions`) and correctly quote the finding's own wording; **no finding**, listed so a repo-wide sweep can subtract them.
- `TODO-ALPHA-056-0.0.17`'s ledger row on this population is low for the reason the build plan already records — its instrument is `docs/SPECS/spec-03[4-9]*.md` and never scans `docs/SPECS/appx/`. This measurement shows the same blindness costs it far more than the companion's 3: **10 of the 48 sit in `docs/SPECS/appx/`**, and 3 sit in the board surfaces its glob cannot reach either.

### Verification after the edits, with real output

**1. `check_spec_glossary.py` — the gate the dispatch names.**

```shell
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
```

```text
OK: 20 terms - all have glossary entries and at least one spec link.
EXIT=0
```

Same **20 terms** as the pre-flight, post-Slice-0, post-Slice-2 and integration-pass baselines, and the same exit 0 the dispatch recorded as the pre-round state. The term at risk in this pass was `strawberry_config`: Decision 5's rewritten sentence keeps its `[glossary-strawberry-config]` link two lines above, untouched, and the sentence itself introduced and removed no glossary link.

**2. `check_citations.py` — the gate the dispatch names.**

```shell
uv run python scripts/check_citations.py
```

```text
OK: 941 citations resolve (781 in 435 .py files, 160 in KANBAN.md).
EXIT=0
```

**3. Markdown layout / link-def scaffold gate**, scoped to the two owned files — never `.` (which would write into files a concurrent session has dirty):

```shell
uv run python scripts/check_trailing_commas.py --check <spec> <companion>
```

```text
EXIT=0
```

Both files keep all 10 canonical group headers in order under a single `<!-- LINK DEFINITIONS -->` delimiter. The companion's new `[init]` definition was placed in the `<!-- django_strawberry_framework/ -->` group, alphabetically between `[conf]` and `[mutations-inputs]`, with the path re-relativized for `docs/SPECS/appx/` (`../../../django_strawberry_framework/__init__.py`) rather than copied from the spec's `../../` depth.

**4. Anchors, reference ids, definition targets — and every `[kanban]` use.** Fenced code blocks are stripped before the scan, so an SDL example cannot forge an anchor. Heading slugs are computed by replacing each space with one hyphen (not by collapsing runs), because a collapsing slugger reports the ten `#decision-N--…` double-hyphen anchors as unresolved and would have read as a real finding — **the instrument was corrected against the prior passes' recorded `unresolved=[]` before its output was believed.**

```text
docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
  anchors: 80 uses / 13 distinct, unresolved=[]
  linkdefs: 73 defs / 73 used, dangling=[], unused=[], missing_on_disk=[]
  [kanban] uses in body: 15;  [kanban] -> ../../KANBAN.md
docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
  anchors: 36 uses / 14 distinct, unresolved=[]
  linkdefs: 36 defs / 36 used, dangling=[], unused=[], missing_on_disk=[]
  [kanban] uses in body: 6;   [kanban] -> ../../../KANBAN.md
```

- **Anchor counts are byte-for-byte the integration pass's** (80 / 13 and 36 / 14, both `unresolved=[]`), which proves no heading, no in-page anchor and no reference id moved — the claim the dispatch asked to be verified before *and* after.
- **`[kanban]` resolves from both files.** Every use has a definition (`dangling=[]`), and both definitions were path-resolved on disk rather than eyeballed: `docs/SPECS/` + `../../KANBAN.md` → `KANBAN.md`, exists; `docs/SPECS/appx/` + `../../../KANBAN.md` → `KANBAN.md`, exists. All 21 uses across the two files still land on a real file.
- **The companion's definition count is the only movement: 35 → 36**, the one `[init]` this pass added, and `used=36` / `unused=[]` proves it is used rather than orphaned.
- **Cross-file anchors resolve in both directions**, checked because the R2 edit sits inside a Decision that both files cross-reference: the companion's 10 `[spec-037-d*]` definitions all resolve to a real spec heading, and the spec's 11 `[rationale-*]` definitions all resolve to a real companion heading — `unresolved=[]` both ways.

**5. Chronology sweep over the finished spec.** Fifteen forbidden shapes — the dispatch's six (`as of`, `round `, `previously`, `used to`, `no longer`, `superseded`) plus nine more (`post-ship`, `has since`, `formerly`, `replaced by`, `retract`, `amendment`, `review round`, `originally`, `earlier draft`) — matched case-insensitively against **whitespace-flattened** text with newlines included, so a phrase wrapped across two lines cannot hide.

```text
docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md -> total 2 | previously=2
  L178:  previously-`NotImplementedError`-raising write input over a file column now
  L1357: previously-`NotImplementedError` path now succeeds.
```

**Verdict on the two hits: both cleared, neither is this round's.** Each describes what the **shipped code path** used to do — the write input this card converted from fail-loud to `Upload` — not what the spec used to say. That is contract, not spec self-narration, and it is the identical two-line result Slice 2 and the integration pass each recorded and cleared. **`as of` = 0, `round ` = 0, `used to` = 0, `no longer` = 0, `superseded` = 0, `post-ship` = 0**, and the nine others are 0 too. **This round's own two spec edits introduced no chronology**; the count is unchanged from the integration pass.

**Negative control for that zero**, in the same instrument against the companion, because a zero from a broken command is indistinguishable from a zero from clean prose:

```text
docs/SPECS/appx/…-rationale.md -> total 47
  post-ship=23, superseded=6, retract=4, used to=3, previously=2, no longer=1,
  has since=1, formerly=1, replaced by=1, amendment=1, review round=1,
  originally=1, earlier draft=1, round =1
```

Fourteen of the fifteen shapes are live in the instrument. The spec's zeros are measurements, not artefacts. (The companion's total rose from the integration pass's 63-shape-vocabulary 47 on a 15-shape vocabulary; the difference is vocabulary width, not drift, and the chronology is what the companion is **for**.)

**6. R2 residual sweep, paired both ways.** A `must be 0` block alone cannot tell a fix from a deletion, so the replacement vocabulary is swept beside it:

```text
must be 0:
  "(and the package root, [`__init__.py`][init]) therefore"   -> 0 (spec), 0 (companion)
  "only **re-export** `Upload` (and `UploadDefinition`)"      -> 0 (spec), 0 (companion)
  "reproduced verbatim below"                                 -> 0 (spec), 0 (companion)

must be > 0:
  "the package root ([`__init__.py`][init]) re-exports `Upload` alone" -> 1 (spec)
  "`UploadDefinition` stops at `scalars.py`"                          -> 1 (companion)
```

The corrected contract is present in the spec and its explanation is present in the companion — and in the **opposite** file each is 0, which is the split `docs/builder/BUILD.md` line 94 demands, measured rather than asserted.

**7. Non-edit of everything else, proved by reverse-application rather than by `git status`.** The companion is untracked and the spec's `git diff HEAD` still carries Slices 0 and 2 plus the integration pass, so neither a diff nor `git status` can isolate this round. Instead this pass's five edits were reverse-applied in memory and the result's size compared against the integration pass's recorded post-edit figures:

```text
spec      reverse-applied: 1666 lines / 104947 bytes  (record 1666 / 104947) -> MATCHES RECORD
companion reverse-applied:  971 lines /  61019 bytes  (record  971 /  61019) -> MATCHES RECORD
```

Both match to the byte. **Nothing else in either file changed — not by this pass, and not by a concurrent writer while this pass ran.** Each reverse-application also asserted its target appeared exactly once before substituting, so a silent multi-site replace could not have passed.

**8. Byte and line counts, before and after.**

| File | Before (integration-pass record) | After | Delta |
| --- | --- | --- | --- |
| `docs/SPECS/spec-037-…md` | 1,666 lines / 104,947 bytes | 1,666 lines / **104,976 bytes** | 0 lines / **+29 bytes** |
| `docs/SPECS/appx/…-rationale.md` | 971 lines / 61,019 bytes | 987 lines / **62,268 bytes** | +16 lines / **+1,249 bytes** |

The spec's `+29` is the Decision-5 rewrite alone; the five renumbers are byte-neutral (`062` and `066` are the same width). The companion's `+16` lines decompose exactly: 14 for the new `**Post-ship:**` bullet, 1 for the framing sentence's extra wrapped line, 1 for the `[init]` definition. **The companion grew forty-three times what the spec did**, which is the split working as intended: the correction is a terse contract sentence, the explanation is not.

**9. Scope discipline, measured.**

```shell
git status --short -- docs/SPECS/
```

```text
 M docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
?? docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
```

Exactly the two owned files. **Cohort B's two `.py` files were never opened for writing by this pass** and both were already dirty from that concurrent worker (` M examples/fakeshop/apps/products/schema.py`, ` M examples/fakeshop/test_query/test_products_api.py`); by the time this pass measured the tree they carried **0** occurrences of the wrong id, so cohort B's R3 landed independently — recorded as an observation, not as this cohort's work. No closeout-agentflow surface (`KANBAN.md`, `CHANGELOG.md`, `TODAY.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`) was written; `KANBAN.md` was read only. No auto-fixer was run over any file, and `ruff` was not invoked at all — no `.py` file was touched.

**10. Not run, and why.** `uv run ruff format .` / `ruff check --fix .` — no `.py` file was touched by this cohort, and running them across `.` would write into ~55 package files a concurrent session has dirty. `pytest` in any form — forbidden after edits without an explicit request, and this cohort has no code to exercise; no `--cov*` flag was passed to anything, in any pass.

### Dispatched-findings tick audit

`docs/builder/worker-1.md` `## Final verification job` step 3, self-audited because this cohort has no Worker 2. Both boxes were audited against the files, not against this artifact's own prose.

| Box | Contract as dispatched | Landed? | Evidence |
| --- | --- | --- | --- |
| R1 | all 5 sites renumbered to `TODO-BETA-066-0.1.5`; a renumber, not a lifecycle flip | **yes** | spec:1132, :1461; companion:666, :685, :710. Three instruments plus a flattened pass: wrong id 0, replacement 5. `TODO-BETA-` prefix retained at all five; no `DONE-` anywhere near them |
| R1 | no link definition, heading, or in-page anchor moved | **yes** | anchors 80/13 and 36/14, `unresolved=[]` both — byte-for-byte the integration pass's figures; `dangling=[]`, `missing_on_disk=[]`; all 21 `[kanban]` uses resolve |
| R2 | Decision 5's sentence states the corrected contract directly, no amendment block / retraction / hedge / chronology | **yes** | spec:991-994, quoted above; spec chronology sweep total 2, both pre-existing and cleared; `as of`, `round `, `superseded`, `post-ship` all 0 |
| R2 | the `BigInt` contrast and the "no `_PACKAGE_SCALAR_MAP` entry" clause preserved | **yes** | the clause is the sentence's final clause, so spec:996's "This is the deliberate contrast with `BigInt`" still has its referent — re-read against the new sentence |
| R2 | the explanation is a companion `**Post-ship:**` bullet under Decision 5's `### Changes this Decision underwent`, in the existing shape | **yes** | companion:505-518; two exemplars read first; append-only (the prior bullet untouched); records the old claim, that it was false only of the root, and both grep measurements |
| R2 | S2a read and unchanged | **yes** | spec:312, scoped to `scalars.py`, byte-unchanged — and the reverse-application proof shows no edit anywhere but the five sites |

**No over-tick and no under-tick, and nothing is deferred** — both boxes are ticked with their contract landed in the files, so no deferral reason is owed on a checklist box. (The checkbox literals themselves are deliberately not spelled out in this prose: a box-shaped literal in a sentence is indistinguishable from a real box to the next audit's sweep, in either state.)

### DRY check across this cohort and the prior accepted slices

No new duplication. This cohort adds no helper, no constant and no code; against Slice 0 (which moved spec text), Slice 1 (three tests), Slice 2 and the integration pass there is no shared shape to collide with. The one duplication risk a residue repair carries is restating the companion's explanation inside the spec, and the paired `must be 0` / `must be > 0` sweep in `### 6.` is the mechanical control: each half of the split is present in exactly one file and 0 in the other. The `[init]` definition is a reuse of the spec's existing reference id spelling rather than a new one invented for the companion, so a reader moving between the two files meets one name for one target.

### Failability proofs

`None; this pass introduced no new boundary.` This cohort lands no runtime code, so there is no guard, gate or rejection path to prove failable. The proof obligations it *does* carry are the sweeps above, and **each carries its own negative control**, which is what makes a zero mean something:

- the `062` sweep is paired with a `066` sweep of the replacement vocabulary, so a zero produced by **deleting** the card id would read as a zero in both blocks rather than as a fix;
- every `must be 0` count was printed as a **non-zero before the edit** by the same instrument, so no post-edit zero is an unrun sweep;
- the three instruments (full id / version-less / bare `062`) are paired with a whitespace-flattened pass and four wrap-hazard spellings, so a citation broken across two lines could not hide from a line-oriented grep;
- the chronology sweep is paired with the same fifteen shapes over the companion (47 occurrences, 14 of 15 shapes live), so a zero from a mistyped pattern would show as a zero there too;
- the anchor scan's slugger was **corrected against the prior passes' recorded `unresolved=[]`** before its output was believed — an instrument that reported ten false unresolved anchors would otherwise have read as this round's regression;
- the non-edit claim is proved by reverse-application to the byte, not by `git status`, which cannot see past a concurrently dirty tree.

No fail-open shape landed: the diff is one rewritten sentence, five card-id renumbers, one corrected framing clause, one appended bullet and one link definition — no expression, guard or default that could silently substitute a permissive answer.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Not applicable; this cohort writes no .py file and declares floor-verification scope none.` Slice 1's re-declared scope was owned and run by its Worker 2 build pass (`/tmp/dsf-floor-037` — Python 3.10.19 / django 5.2.16 / strawberry-graphql 0.316.0, `6 passed`) and confirmed at Slice 1's final verification and again at the cycle's final gate. This round adds no framework seam and so no second owner.

### Spec status-line re-verification (this spawn)

`docs/builder/worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. Read spec:1-40 before the first edit. The header states `Shipped in 0.0.11 (card DONE-037-0.0.11)`, `Status: **SHIPPED (0.0.11)**`, `Owner:`, and predecessors `spec-036` / `spec-001`, both of which exist on disk. It carries no "not yet shipped" / "remains to be" claim this round falsified and references no predecessor doc this round deleted; its opener's `mutations/inputs.py::model_column_write_annotation` citation still resolves (`check_citations.py` exit 0 above). **No status-line edit was owed, and none was made** — the reverse-application proof shows the header's bytes untouched.

### Spec changes made (Worker 1 only)

| File and location (post-edit) | Change | Reason | Finding |
| --- | --- | --- | --- |
| `docs/SPECS/spec-037-…md:1132` | `TODO-BETA-062-0.1.5` → `TODO-BETA-066-0.1.5` | the 2026-08-29 board inserts moved the fakeshop-activation card; `062` is now a `0.1.3` card with an unrelated subject | R1 |
| `docs/SPECS/spec-037-…md:1461` | same | same | R1 |
| `docs/SPECS/spec-037-…md:991-994` | Decision 5's re-export sentence rewritten to state the corrected contract: `scalars.py` re-exports `Upload` **and** `UploadDefinition`; the package root re-exports `Upload` alone | the sentence claimed a package-root `UploadDefinition` export that has never existed — `grep -c` in `__init__.py` is 0 | R2 |
| `docs/SPECS/appx/…-rationale.md:666` | `TODO-BETA-062-0.1.5` → `TODO-BETA-066-0.1.5` | as above; the `- **Revision 1**` bullet's frame is historical but the id names the live card | R1 |
| `docs/SPECS/appx/…-rationale.md:685` | same | as above; unquoted paraphrase naming the live card, unlike its two quoted neighbours | R1 |
| `docs/SPECS/appx/…-rationale.md:710` | same | as above; present-tense "stays [id]" inside the reproduced blockquote — the dispatch's verbatim-quotation exception was tested and does not fire | R1 |
| `docs/SPECS/appx/…-rationale.md:671-674` | "The block is reproduced verbatim below" → "reproduced below, verbatim but for the fakeshop-activation card id, which carries its current spelling" | R1's fifth edit falsified this claim; fixing it is inside R1's subject, and the block's verbatim fidelity was byte-proved against `HEAD` before the edit | R1 (consequence) |
| `docs/SPECS/appx/…-rationale.md:505-518` | new `**Post-ship:**` bullet under Decision 5's `### Changes this Decision underwent` | `docs/builder/BUILD.md` `## Spec rationale extraction` — the explanation of what changed belongs here, never in the spec | R2 |
| `docs/SPECS/appx/…-rationale.md` link definitions | `[init]: ../../../django_strawberry_framework/__init__.py` added under `<!-- django_strawberry_framework/ -->`, alphabetically | the new bullet cites `__init__.py` and the companion had no definition for it; `used=36` / `unused=[]` proves it is not orphaned | R2 |

**Sites deliberately not edited, each with its reason:** spec:312 (S2a — correct as written, and the internal evidence that only Decision 5 was wrong); spec:466-473 (`## Current state`'s dated pre-build observation, whose `UploadDefinition` clause describes what Strawberry ships and is true); every other card id in both files (out of R1's subject by the dispatch's own fence); the 48 out-of-fence occurrences of the wrong id (routed above with the measurement); this cycle's own `bld-*` / build-plan artifacts (per-cycle scratchpads correctly quoting the finding's wording). **No R1 site was left un-renumbered, so the dispatch's exception clause records no entry.**

### Final status

`final-accepted`. Both `### Dispatched findings checklist` boxes carry a landed contract, audited against the files rather than against prose. Every instrument was run before and after with a printed non-zero pre-edit reading and a paired replacement-vocabulary control; both gates the dispatch names exit 0; the spec narrates no chronology and every `[kanban]` use still resolves to a definition whose target exists on disk; anchors and link definitions are byte-for-byte the integration pass's, so nothing structural moved; and the non-edit of everything else in both files is proved to the byte by reverse-application. One further defect was found inside R1's own subject and fixed; one measured 48-occurrence population is routed to the maintainer rather than swept.

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
