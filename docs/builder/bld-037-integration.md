# Build: cross-slice integration pass (`spec-037` residual-reconciliation cycle)

Spec reference: `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` (whole file) and its rationale companion `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` (whole file)
Status: final-accepted

Worker 1 only (`docs/builder/BUILD.md` `## Cross-slice integration pass`). One combined Plan + Final-verification block; Worker 1 sets `Status:` itself. `git stash` / `git checkout` / `git restore` / `git worktree` were **not used at any point**; every `HEAD` read went through `git show HEAD:<path>` into a scratch path outside the repository. No `--cov*` flag was passed to any run. `ruff` was never invoked against `.`.

Hot-path declaration: **none** (copied from the plan as written).
Floor-verification scope: **none** for this pass. Slice 1's re-declared scope was owned and run by its Worker 2 build pass; the final gate is its backstop.

Raw `path:NN` references are used below under `AGENTS.md` rule 27's per-cycle-artifact carve-out. Spec line numbers are **post-edit** (this pass's own edits shifted three of them).

---

## Plan (Worker 1)

### What this cycle was, and what that makes the standard checks

A residual-reconciliation cycle over a spec shipped at `0.0.11`, not a feature build. Its whole output is one new rationale companion (Slice 0), **one** changed `.py` file (`tests/types/test_base.py`, +57 lines, three test functions — the cycle's entire source diff, landed in Slice 1), and a reconciled spec + appended companion (Slice 2). Several of the pass's standard checks are therefore near-vacuous. Each is answered in writing below rather than skipped: a check recorded as "n/a, here is why" is a decided answer where silence is not.

### Required reading, discharged

Every prior `docs/builder/bld-037-*.md` artifact was read **in full, in slice order**, before anything below was written — no "as needed" (`BUILD.md` step 1): `bld-037-slice-0-rationale_extraction.md` (278 lines), `bld-037-slice-1-code_conformance.md` (846 lines), `bld-037-slice-2-spec_reconciliation.md` (399 lines). Plus `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`, `docs/builder/build-037-upload_file_image_mapping-0_0_11.md`, the active spec and its companion, and `docs/builder/worker-memory/worker-1.md` (read first). No other worker's memory file was opened.

### Implementation steps

1. Answer the six numbered preconditions, each with a measurement or a recorded reason.
2. Re-derive the two populations Slice 2 recorded as under-counted, and spot-check others chosen here.
3. Cross-check the spec against the companion, and both against `HEAD` source.
4. Edit only what a genuine contradiction or under-closed population requires; record every edit.
5. Re-run the doc gates and the anchor / link-definition / chronology / duplicate sweeps after editing.

### Test additions / updates

None. This pass writes no `.py` file and no test. One focused existing run is recorded below for pass/fail only.

### Implementation discretion items

None. Every judgement — which count claims are card-scoped and stay, which read as surface claims and are rewritten, whether a duplicated bullet is a defect or a deliberate restatement — was decided here and is recorded below.

### Dispatched findings checklist

This pass dispatches nothing to a builder: no source work was found. The build plan's own checklist row is the closure target.

- [x] Cross-slice integration pass -> `docs/builder/bld-037-integration.md`

---

## Final verification (Worker 1)

### Summary

The three slices tell one coherent story, with three exceptions this pass found and fixed. The staged-anchor sweep is clean and independently re-derived over a printed population of 440 tracked source/test/example/script files plus the one untracked file in those trees. The two populations Slice 2 recorded as under-counted are closed: zero false `path`-as-default-subfield claims and zero surviving falsified-deferral sites remain in the finished spec. Spot-checks of four further findings all hold. The spec's rewritten SUPERSEDED clauses match `HEAD` source field-for-field. **Three defects were found and fixed: a false version on a `**Post-ship:**` bullet, a verbatim-duplicated bullet in the companion, and a self-contradiction Slice 2's own edit created inside Decision 3.** No source work is owed.

### The six numbered preconditions

**Step 1 — read every prior artifact in slice order, in full.** Done; enumerated under `### Required reading, discharged`. All three carry `Status: final-accepted`.

**Step 2 — confirm the static inspection helper ran, or was explicitly skipped with a recorded reason, for every Python file with review-worthy logic the build touched.**

The build touched exactly one `.py` file, `tests/types/test_base.py`, a test file **outside** the package, +57 lines. Measured here rather than inherited:

```shell
git diff HEAD --stat -- tests/types/test_base.py
git diff HEAD --name-only -- 'django_strawberry_framework/**/*.py'
```

```text
 tests/types/test_base.py | 57 +++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 57 insertions(+)
```

(The 55 package `.py` paths that `git diff HEAD --name-only` also lists are the build plan's baseline-dirty concurrent-session population, not this build's; `types/converters.py` and `types/base.py` — the two files the cycle read hardest — are byte-identical to `HEAD` right now, `git show HEAD:<path>` + `cmp` → exit 0 for both.)

**The skip record exists and its disposition is restated here.** Worker 3 recorded it under `bld-037-slice-1-code_conformance.md` `### Static inspection helper: decision recorded either way` — **not run, deliberately**, walking `BUILD.md` `### When to run the helper during build` clause by clause: no new `.py` file; `tests/types/` is not `django_strawberry_framework/types/`; zero new logic lines inside the package; and the outside-package clause needs 50+ new *logic* lines where this diff's executable statements number 18 (the remaining 39 lines are docstrings, comments and blanks). The skip is correct on every clause and is **confirmed, not merely noted**. Worker 1's own planning obligation was separately discharged: `bld-037-slice-1` `### DRY analysis` records a package-wide helper inventory refreshed to 2,006 lines and grepped for the file/override shapes, and pre-flight step 2 ran `scripts/review_inspect.py` against `types/converters.py` (`docs/shadow/django_strawberry_framework__types__converters.overview.md`, present on disk).

**Steps 3 and 4 — compare the `Repeated string literals` and `Imports` sections across every shadow overview.**

**Not applicable, and here is what makes it so.** These two steps look for a literal or an import shared by two or more files *this build produced or changed*. The cycle produced **no new package module and no cross-module code**: its entire source surface is three test functions in one pre-existing test file, and no package `.py` file changed at all. The comparison set is therefore of size one at most — `docs/shadow/` holds 46 entries, all of them either the pre-flight run on `types/converters.py` or the `035` / `036` cycles' output the plan deliberately did not clear — and a cross-file DRY candidate cannot exist in a one-file diff by construction.

**What that makes the cross-slice DRY scan:** it collapses onto the one question a one-file diff can still answer badly — *does the new code duplicate a shape that already exists in that file or its neighbours?* — and that question was asked and answered mechanically rather than waived. See `### DRY check across the slices`.

**Step 5 — walk every accepted slice artifact's `What looks solid` and `DRY findings` for deferred follow-up that should land here.** Live; done properly. See `### Step 5: deferred follow-up walked`.

**Step 6 — sweep the whole tree for staged anchors naming this build's spec OR card.** Live and mandatory; independently re-derived. See `### Step 6: staged-anchor sweep, re-derived`.

### Step 6: staged-anchor sweep, re-derived

Slice 1 reported a clean sweep over 440 files. That is a **claim**, and Slice 2 has edited the spec since, so it is re-derived here from scratch. The population is printed first, because a zero must be distinguishable from an unrun sweep. zsh does **not** word-split `$FILES`, so arrays are used throughout.

```shell
srcfiles=("${(@f)$(git ls-files 'django_strawberry_framework/**' 'tests/**' 'examples/**' 'scripts/**')}")
print -r -- "source/test/example/script tracked files scanned: ${#srcfiles[@]}"
untr=("${(@f)$(git ls-files --others --exclude-standard 'django_strawberry_framework/**' 'tests/**' 'examples/**' 'scripts/**')}")
print -r -- "untracked in those trees: ${#untr[@]}"; print -l -- $untr
grep -rEo 'TODO\(spec-037|TODO-(ALPHA|BETA|STABLE)-037' django_strawberry_framework tests examples scripts | wc -l
```

```text
source/test/example/script tracked files scanned: 440
untracked in those trees: 1
django_strawberry_framework/utils/canonical.py
0
```

**The instrument carries a negative control, run in the same shell against the same population**, because a sweep that cannot hit is indistinguishable from one that found nothing:

```shell
grep -rEo 'TODO-(ALPHA|BETA|STABLE)-[0-9]{3}' django_strawberry_framework tests examples scripts | wc -l
grep -rEo 'TODO\(spec-[0-9]{3}' django_strawberry_framework tests examples scripts | sort | uniq -c
```

```text
30
   1 django_strawberry_framework/filters/sets.py:TODO(spec-060
   3 django_strawberry_framework/list_field.py:TODO(spec-050
   1 django_strawberry_framework/optimizer/extension.py:TODO(spec-050
   1 django_strawberry_framework/orders/sets.py:TODO(spec-050
   3 django_strawberry_framework/resource_policy.py:TODO(spec-050
   6 django_strawberry_framework/utils/querysets.py:TODO(spec-050
   1 examples/fakeshop/test_query/README.md:TODO(spec-050
   1 examples/fakeshop/test_query/test_library_api.py:TODO(spec-035
   1 examples/fakeshop/test_query/test_library_api.py:TODO(spec-050
   1 examples/fakeshop/test_query/test_list_field_api.py:TODO(spec-050
   1 examples/fakeshop/test_query/test_list_field_async_api.py:TODO(spec-050
   1 examples/fakeshop/test_query/test_multi_db.py:TODO(spec-050
   1 examples/fakeshop/test_query/test_resource_policy_api.py:TODO(spec-050
   1 tests/orders/test_sets.py:TODO(spec-050
   1 tests/test_list_field.py:TODO(spec-050
   1 tests/test_resource_policy.py:TODO(spec-050
```

Both anchor grammars are demonstrably live in this tree and hit 30 / 22 times for other cards. **They hit `037` zero times in shipped source, tests, comments or scripts.**

Repo-wide (excluding `.git/`) the two grammars occur **18** times, every one inside a `.md`. Excluding `KANBAN.md` (2) and `KANBAN.html` (2) per step 6's own carve-out — where `TODO-<MILESTONE>-<NNN>` legitimately names board cards — and `BACKLOG.md` (0), the remaining 14 are: `bld-037-slice-1` (5), the `037` rationale companion (4), the `037` spec (3), `bld-037-slice-2` (2), `BUILD.md`'s own example (1), `spec-036`'s rationale (1). The spec's three, read individually:

```text
459:  #"Upload staged seam (TODO-ALPHA-037-0.0.11)"   -- the deliberate ## Current state observation Slice 2 left in place
1430: discharging the pre-placed `TODO(spec-037 Slice 4)`  -- ## Doc updates, describing a discharged seam
1437: `TODO-ALPHA-037-0.0.11` moved to Done as `DONE-037-0.0.11`  -- the card's own pre-DONE id
```

All three are prose *about* a discharged anchor, none is a staged anchor. Note the spec's count fell from Slice 1's reported 7 to 3 — Slice 2's N12 edits re-homed three dead `#"Upload staged seam"` citations onto `mutations/inputs.py::model_column_write_annotation` and dropped a fourth. That symbol exists in both the `HEAD` blob (`inputs.py:557`) and the working copy (`:546`), checked because `mutations/inputs.py` is baseline-dirty. **No finding; nothing to route.**

### Step 5: deferred follow-up walked

Slices 0 and 2 are procedural-closure slices and carry no Worker 3 `What looks solid` / `DRY findings` sections; their equivalent surfaces (`### Notes for Worker 1`, `### DRY check`, `### Routed to the maintainer`) were walked in their place.

- **Slice 1, `### DRY findings` (Worker 3), four bullets.** (a) *No new factory was introduced* — re-verified here, not accepted: `grep -c '^def _make_'` is **6** against the `HEAD` blob and **6** in the working copy, and the diff's only added top-level `def`s are the three `test_` functions. (b) *Parametrizing tests 1 and 2 was considered and rejected*, with the file's own precedent as the reason — **not re-fought**, per the recorded rejection. (c) *The existence challenge was asked and answered*. (d) *The four-line fixture comment carries no process provenance* — re-verified below. **Nothing deferred.**
- **Slice 1, `### What looks solid`, six bullets.** All are confirmations of what landed (pin reaches the contract's own spelling; controls are real and failable in both directions; `is` vs `==` spellings; failability record complete; floor run reproducible; style gates pass). **Nothing deferred.**
- **Slice 1's one Low** (the third test's annotation assertion overlapping `::test_filesystem_path_fields_absent_leaves_every_column_pathless`) was **ruled on at that slice's own final verification**: path (b), keep as-is, with one clause of the finding refuted at source. It is closed, not deferred, and is explicitly marked do-not-re-raise. This pass does not re-open it.
- **Slice 1's escalation** (four rows failing the full package sweep, all in the concurrent session's baseline-dirty surface, proven independent of this diff by a deselect run) is a **maintainer** item, repeated below so the final gate does not read it as this build's failure.
- **Slice 2's `### Routed to the maintainer`, three items** — carried forward verbatim below. All three are fence items, not defects in `spec-037`.

**Nothing from step 5 needed to land in this pass as source or spec work**, other than the three defects this pass found on its own.

### Cross-document coherence: does the spec still contradict itself?

**Re-derivation 1 — the `path` population (D1 / N8), which Slice 2 re-measured from 17 lines / 18 occurrences to 20 sites.**

The pre-edit state is not reconstructible read-only — Slice 0's move is uncommitted, so no blob holds it — so the population was re-derived from **both ends**: the `HEAD` blob (pre-Slice-0) and the finished file.

```text
HEAD blob (pre-Slice-0):  23 code-span `path` occurrences on 22 lines;
                          2 `path: String` lines inside SDL fences (688, 695);
                          1 `path: str | None` (275);  DjangoFilePathType 0; filesystem_path_fields 0
finished spec:            25 code-span `path` occurrences on 22 lines;
                          0 `path: String` inside an SDL fence;  DjangoFilePathType 8;
                          DjangoImagePathType 7; filesystem_path_fields 12; expose_filesystem_path 3
```

The `HEAD` blob independently confirms the three sites the code-span instrument could not see, at exactly the shape Slice 2 named. It also explains the 23 → 18 drop Slice 1 measured: five of the `HEAD` occurrences sat inside blocks Slice 0 moved to the companion.

**All 25 surviving occurrences were graded line by line** (spec:121, 246, 304, 410, 505, 555, 581, 594, 633, 697, 787, 825, 830, 885, 948, 1116, 1120, 1222, 1331, 1336, 1373, 1490 — 22 lines, three carrying two). Every one either (a) states that `path` is **not** a default subfield, (b) names the opt-in explicitly (`Meta.filesystem_path_fields`, `DjangoFilePathType` / `DjangoImagePathType`), (c) describes **upstream's** four-field type, which is accurate, or (d) describes `FieldFile.path` raising, which is true on whichever type publishes it. **Zero false default-subfield claims survive.** The SDL fences now emit `name` / `size` / `url` and `name` / `size` / `url` / `width` / `height`, with the `path` opt-in described in prose beneath — matching `types/converters.py::DjangoFileType` and `::DjangoImageType` field-for-field.

Slice 2's note that the raw token count **rises** while its falsehood count goes to zero is confirmed (18 → 25 occurrences), and is restated here so a later sweep does not read the rise as a regression.

**Re-derivation 2 — the falsified live-coverage deferral (N2), recorded at four sites and re-measured to five.**

```text
finished spec:  TODO-BETA-062 -> 2 (spec:1132, :1461), both re-scoped to the broader
                products/fakeshop activation and both explicitly saying the file/image
                surface's own live coverage is NOT part of it
                "no live fakeshop surface" -> 0 ; "None required unless" -> 0
                MediaSpecimen -> 5 ; test_uploads_api -> 2
```

The five sites were re-read individually in the finished file — Decision 9's body (:1101-1146), `## Out of scope` (:1461-1464), `## Non-goals` bullet 2 (:542), `## Test plan`'s "Live HTTP tests" bullet (:1369-1378), and `## Test plan`'s preamble (:1295-1301, the fifth site that shares no token with the others). **All five now state the shipped two-tier split.** The replacement vocabulary is present (`MediaSpecimen` 5, `test_uploads_api` 2), so the zero is not a zero produced by deleting the subject.

**Spot-checks, chosen here rather than inherited — four, all holding.**

| Finding | Re-measured | Verdict |
| --- | --- | --- |
| **D3 / N9** — the three-parameter `convert_field_output` signature | `grep -n 'convert_field_output(field, type_name'` → 2 sites (spec:252, :862), **both** spelling `(field, type_name, *, force_nullable=None, expose_filesystem_path=False)`; the three-parameter form → **0**. Source: `types/converters.py:500-506` is that exact signature | closed |
| **D4 / N10** — `Meta` gained `filesystem_path_fields`, claimed at two sites | Decision 8's standing enumeration (spec:1070-1099) and `## Edge cases`' final bullet (spec:1286-1292) both now card-scope the claim and **name** `filesystem_path_fields`; `"byte-unchanged;"` → 0. Source: `types/base.py:77` carries the key. The setting half re-verified against the `HEAD` blob of `conf.py`: **9** feature keys, none file/image (only 4 comment-line mentions, in the `MAX_REQUEST_BODY_BYTES` block) | closed, both sites |
| **N7** — ten two-hop `[Risks]` uses | `#risks-and-open-questions` in the spec → **1**, and it is the `[rationale-risks]` link **definition's** target, not an in-page use. Nine `[rationale-risks]` body uses survive (one of them the `## Risks and open questions` pointer paragraph itself); the other two of the original ten went with the Pillow hedges Slice 2 dropped for N5. Slice 2's `Edited 10` is right on its own terms (edited ≠ re-pointed) and its plan text discloses the two rewrites | closed |
| **D8 / N3 / N4** — path and placeholder rot | `DONE-NNN` → 0, `docs/spec-037` → 0, `TODO-ALPHA-043` → 0, `DONE-037-0.0.11` → 4. DoD item 1 (spec:1479-1485) now names `docs/SPECS/`, both `docs/SPECS/appx/` companions, and an invocation that actually runs — re-run here: `OK: 20 terms`, exit 0 | closed |

**One self-contradiction found, in Decision 3, created by Slice 2's own edit.** See `### Spec changes made (Worker 1 only)` item 3.

### Cross-document coherence: do the spec and the companion agree?

- **Every spec Decision keeps its pointer.** 10 `Rationale companion — …` lines (spec:800, 813, 923, 980, 1003, 1054, 1067, 1098, 1147, 1169), one per Decision, plus the `## Risks and open questions` pointer. 11 `rationale-*` link definitions, all used, none dangling.
- **Every companion Decision heading matches a spec Decision heading, character for character.** Ten `## Decision N — …` in the companion against ten `### Decision N — …` in the spec; slugged and compared programmatically, `rationale-* defs unresolved in companion: []` and `spec-037-d* defs unresolved in spec: []`. Both directions.
- **No `**Post-ship:**` bullet contradicts the contract the spec now states.** All 13 bullets were read against the spec section each names. Decision 3's `path` / fourth-parameter narrative, Decision 4's subfield-nullability narrowing and test-gap closure, Decision 5's anchor-removal note, Decision 7's five-exports-but-three-net-new distinction, Decision 8's `Meta`-half-false / setting-half-true split, Decision 9's rewrite, and Decision 10's deliberate non-update all match the spec's current text. Two were verified against source rather than read: Decision 8's "nine feature keys, none file/image" (confirmed against the `HEAD` blob of `conf.py`) and Decision 7's "five are exported in total" (`__init__.py:49-52`, `:132-136`, `:155`).
- **Two defects found in the companion**, both fixed — see `### Spec changes made (Worker 1 only)` items 1 and 2.
- **Anchors and link definitions, both files, after this pass's edits:**

```text
docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
  anchors: 80 uses / 13 distinct, unresolved=[]
  linkdefs: 73 defs / 73 used, dangling=[], unused=[], missing_on_disk=[]
docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
  anchors: 36 uses / 14 distinct, unresolved=[]
  linkdefs: 35 defs / 35 used, dangling=[], unused=[], missing_on_disk=[]
```

Fenced code blocks are stripped before the scan, so an SDL example cannot forge an anchor. Unchanged from Slice 2's numbers — this pass's edits touched no heading and no reference id.

### Cross-document coherence: does the spec agree with the code the cycle verified?

Slice 1 graded 57 items and Slice 2 rewrote the 15 SUPERSEDED ones. The three named spot-checks, plus the node-id existence check, all read at source:

- **`DjangoFileType`'s default subfield set.** Source (`types/converters.py:109-172`): `DjangoFileType` defines `name` (`-> str`), `size` (`-> int | None`), `url` (`-> str | None`); `DjangoImageType(DjangoFileType)` adds `width` / `height` (both `int | None`); `path` lives on `_FileSystemPathFields`, mixed into `DjangoFilePathType(DjangoFileType, _FileSystemPathFields)` and `DjangoImagePathType(DjangoImageType, _FileSystemPathFields)` (`:176`, `:204`, `:215`). The spec's SDL fences (spec:660-679), Decision 3's bullets (spec:820-838), Decision 4's nullability paragraph (spec:687-700) and DoD item 2 (spec:1489-1500) all state exactly that. **Match.**
- **`convert_field_output`'s shipped signature.** Source `types/converters.py:500-506`: `(field, type_name, *, force_nullable=None, expose_filesystem_path=False)`. Spec:252 and :862 quote it verbatim. The spec's added sentence that `expose_filesystem_path` "is read only inside the file branch, so it can never silently change a scalar column's annotation" is true at `:552-553`, where the parameter is consumed after the `FIELD_OUTPUT_TYPE_MAP` hit. **Match.**
- **The `## Test plan` clause re-homed on `tests/types/test_base.py` (N13 / N18).** The spec's new `**`Meta`-level override tests**` bullet (spec:1303-1314) cites three node ids. All three exist and their assertions match the sentence:

| Node id | Assertions at source | Sentence it discharges |
| --- | --- | --- |
| `tests/types/test_base.py::test_meta_required_overrides_forces_non_null_file_output` (`test_base.py:2176`) | `__annotations__["attachment"] is DjangoFileType`; control `["preview"] == (DjangoImageType \| None)` | `required_overrides` reaches the file branch through the public `Meta` surface |
| `::test_meta_required_overrides_forces_non_null_image_output` (`:2198`) | `["preview"] is DjangoImageType`; control `["attachment"] == (DjangoFileType \| None)` | the branch is not `FileField`-only |
| `::test_meta_nullable_overrides_on_a_file_column_is_a_no_op` (`:2212`) | `["attachment"] == (DjangoFileType \| None)` | `nullable_overrides` is the redundant direction |

All three build the type through `_make_path_optin_type(model, …_overrides=…)` — the contract's own spelling — not through a `convert_field_output(force_nullable=…)` keyword, which is precisely what the rewritten sentence claims. `uv run pytest tests/types/test_base.py --no-cov -q` in this pass → **170 passed in 1.41s**.

- **Decision 9's live tier, checked against the example project** because it is the Decision the cycle rewrote most heavily. `examples/fakeshop/apps/scalars/models.py::MediaSpecimen` exists with a required `FileField` and a required `ImageField`; `examples/fakeshop/test_query/test_uploads_api.py` carries **9** `def test_` rows covering the SDL default-nullable shape, the absent default `path`, the opt-in's absence and presence, populated subfields, the empty-required-file `null`, the `Upload` input SDL, and two real multipart uploads; `examples/fakeshop/config/urls.py:74` sets `multipart_uploads_enabled=True`. Every clause of the rewritten Decision is true at source.

### Comments: one coherent story, no process provenance

The only new code is three tests plus a four-line fixture comment. Read at source (`tests/types/test_base.py:2169-2223`) and swept mechanically over the added lines for `worker`, `round <N>`, `review`, `W2`/`W3`, `slice <N>`, `pass <N>`, `mutation A`, `bld-`:

- The four-line comment states the invariant — that `_make_path_optin_model` / `_make_path_optin_type` are the only fixture pair carrying a file column, an image column and a scalar in one model, which is what a per-column override needs an unnamed sibling for — and says nothing about how the tests came to be there.
- The three docstrings cite `spec-037 Decision 4` as design rationale, which `AGENTS.md` and `ARTIFACT.md` keep (provenance citing a spec) rather than scrub (staging language such as "planned" / "Slice N" / `TODO(`). No `TODO`, no "planned", no "after Slice N".
- The sweep's only hits were the substring `review` inside the fixture column name **`preview`**. **No process provenance landed.**

### DRY check across the slices

- **Cross-file literal / import comparison:** structurally impossible here, for the reason recorded under steps 3 and 4 — a one-file diff with no package module cannot carry a cross-file literal.
- **Within-file duplication, asked mechanically:** added top-level `def _make_` = **0**, total unchanged at **6** (`HEAD` blob vs working copy). No fourth model/type factory appeared. The one genuine overlap in the diff — the third test's annotation assertion — was graded, ruled *keep*, and its reasoning recorded at Slice 1's final verification; this pass does not re-open it.
- **Duplication across documents, which is a reconciliation cycle's real DRY risk:** the spec must not restate the explanation that belongs in the companion. The chronology sweep is the control and it is clean (below). A second control was run here and **caught something**: a verbatim-duplicated bullet inside the companion's own `## Non-Decision deliberation` (fixed, item 2).
- **No duplicated helper, inconsistent naming, repeated ORM/queryset pattern, misplaced responsibility, or export change** exists to find: `git diff -- django_strawberry_framework/__init__.py` is empty and no package file changed.

### Spec changes made (Worker 1 only)

Three edits, each a genuine contradiction or a false statement. All line numbers are **pre-edit**.

| File and location | Change | Reason |
| --- | --- | --- |
| `docs/SPECS/appx/…-rationale.md:379` (Decision 3, `**Post-ship:**`) | `` `spec-048` (Secure output defaults, `0.0.17`, …) `` → `` `0.0.14` `` | **False version, contradicting the corpus's own record.** The spec is `docs/SPECS/spec-048-secure_output_defaults-0_0_14.md`, whose header reads "Targeted at `0.0.14` (card `DONE-048-0.0.14`)", and whose rationale companion records the `0.0.17` targeting as *falsified, then withdrawn*: "`0.0.15`, `0.0.16`, and `0.0.17` were never the version of a released artifact". The `0.0.17` figure propagated from the build plan's `## Worker-0 verification pass` D1 into this bullet. It was the **only** `0.0.17` occurrence in either `037` file; residual sweep after the edit → 0 in both. |
| `docs/SPECS/appx/…-rationale.md:915-920` (`## Non-Decision deliberation`) | deleted a **verbatim duplicate** of the `Justification:` / `Alternatives considered (and rejected):` pairing bullet | The identical six-line bullet stood at :901-906 and again at :915-920, straddling the maintainer-routing bullet Slice 2 appended. Detected by a whole-file duplicate-bullet scan over both documents (spec: 0 duplicates; companion: 1). The first occurrence is kept in place; the maintainer-routing bullet now closes the section. |
| `docs/SPECS/spec-037-…md:818-820` (Decision 3 preamble) | "defines **two** `@strawberry.type` output types and a **new read-output field-type map**" → "defines the file/image `@strawberry.type` output types and the **read-output field-type maps** that select among them" | **Self-contradiction created by Slice 2's own edit.** The preamble's counts were left untouched while the bullet list beneath it was extended to name four output types (`DjangoFileType`, `DjangoImageType`, `DjangoFilePathType`, `DjangoImagePathType`) and a second, output-type-keyed map. At `HEAD` `types/converters.py` carries **5** `@strawberry.type` classes and **2** output maps (`FIELD_OUTPUT_TYPE_MAP:266`, `FILESYSTEM_PATH_OUTPUT_TYPE_MAP:277`). Unlike Decision 7's heading and Decision 2's opener, this sentence is **not** card-scoped — it is present tense about what the module defines, sitting directly above the list that refutes it, which is the one shape a reader cannot resolve. Fixed by dropping the counts rather than by narrating the change: no chronology, no "as of `spec-048`". |

**Not edited, decided rather than skipped.** `## Implementation plan`'s closing paragraph (spec:1188-1191) says the `scalars.py` docstring's stale `TODO-ALPHA-035-0.0.11` reference "is corrected in the same slice", where N12 rewrote the Slice-2 sub-check to say **remove**. Inspected and left: removal *is* the correction, the sentence names no replacement anchor, and rewriting it would be a stylistic pass over true prose. Recorded so a later sweep does not re-open it as an N12 residual.

**Spec status-line re-verification (this spawn).** `worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. Read spec:1-40 and the companion's header block. The spec states `Shipped in `0.0.11` (card `DONE-037-0.0.11`)`, `Status: **SHIPPED (`0.0.11`)**`, and predecessors `spec-036` / `spec-001`, all of which exist on disk; it carries no "not yet shipped" / "remains to be" claim this build falsified, and it references no predecessor doc this build deleted. Its opener's `mutations/inputs.py::model_column_write_annotation` citation — Slice 2's N12 replacement for the dead seam substring — resolves at `HEAD`. **No status-line edit owed this spawn.**

### Verification after this pass's edits, with real output

**1. Doc gates.**

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
OK: 20 terms - all have glossary entries and at least one spec link.
EXIT=0
$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-037-…md docs/SPECS/appx/…-rationale.md
EXIT=0
```

Same 20 terms as the pre-flight, post-Slice-0 and post-Slice-2 baselines.

**2. Anchors and link definitions** — quoted under the spec/companion agreement section; unchanged in both files.

**3. Chronology sweep over the finished spec**, 23 forbidden shapes matched case-insensitively against **whitespace-flattened** text with newlines included, so a phrase wrapped across two lines cannot hide:

```text
docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
  total: 2 | previously=2
    L178:  previously-`NotImplementedError`-raising write input over a file column now
    L1357: previously-`NotImplementedError` path now succeeds.
```

Both opened and read: each describes what the **shipped code path** used to do, not what the spec used to say — contract, not spec self-narration. `superseded`, `post-ship`, `no longer`, `has since`, `formerly`, `used to`, `replaced by`, `review round`, `as of`, `retract`, `amendment`, `originally`, `earlier draft`, `prior draft`, `first draft`, `later changed`, `pre-build`, `post-build`, `feedback`, `reconciled`, `round-4`, `round 4` are all **0**. **This pass's own three edits introduced no chronology** — the count is identical to Slice 2's.

**Negative control for that zero:** the same sweep over the companion returns **63** occurrences across 22 of the 23 shapes, so a zero produced by a broken command would show as a zero there too. (Slice 2 reported 45 with a 14-shape vocabulary; the difference is vocabulary width, not drift.)

**4. Duplicate-bullet scan, both files, after the fix.**

```text
spec:      duplicate bullet blocks: 0
companion: duplicates: []
```

**5. Byte and line counts.**

| File | Post-Slice-2 | After this pass | Delta |
| --- | --- | --- | --- |
| `docs/SPECS/spec-037-…md` | 1,666 lines / 104,914 bytes | 1,666 lines / **104,947 bytes** | +33 bytes |
| `docs/SPECS/appx/…-rationale.md` | 977 lines / 61,482 bytes | 971 lines / **61,019 bytes** | −6 lines / −463 bytes |

The companion's delta is the duplicated bullet's six lines; the version fix is byte-neutral.

**6. Diff attribution.** This pass wrote exactly three files: the two above and this artifact (plus `docs/builder/worker-memory/worker-1.md`). No `.py` file was touched — `types/converters.py` and `types/base.py` are byte-identical to `HEAD` (`git show HEAD:<path>` into a scratch path outside the repo, then `cmp` → exit 0 for both), and `/private/tmp/dsf-failability-037/` holds only `pristine/` while `/private/tmp/dsf-r3-037/` holds only `converters.orig` — **no `ACTIVE-MUTATION.json` anywhere**, so no failability mutation was left live by any pass. The cycle's whole source diff remains `tests/types/test_base.py`, 57 insertions, 0 deletions.

**7. Not run, and why.** `uv run ruff format .` / `ruff check --fix .` — no `.py` file was touched by this pass, and running them across `.` would write into 55 package files a concurrent session has dirty. The full `pytest` sweep — that is the final gate's, not this pass's.

### Consolidation: none dispatched

No DRY or correctness issue needing **source** work was found. The three defects were documentation contradictions inside the two files this pass is licensed to edit, and all three are fixed here. `Status: revision-needed` is therefore not set, and Worker 0 dispatches no Worker 2 / Worker 3 consolidation loop.

### Routed to the maintainer (out of this cycle's reach)

Carried forward unchanged from Slice 1 and Slice 2. The maintainer fenced this cycle to spec files and package `.py` source; none of these is a defect in `spec-037`.

1. **`docs/GLOSSARY.md` is the published home of contracts this cycle corrected in the spec.** Its `DjangoFileType` / `DjangoImageType` entries and its `Meta.required_overrides` entry carry the same file/image contract; nobody has checked whether they still describe the post-`spec-048` default-subfield shape.
2. **`DjangoFilePathType` / `DjangoImagePathType` are root-exported symbols** (`__init__.py:49-52`, `:132-136`) whose `docs/GLOSSARY.md` and `docs/TREE.md` presence this cycle could neither verify nor fix. They are `spec-048`'s to own; flagged because this cycle introduced them into `spec-037`'s vocabulary, where they previously had zero occurrences.
3. **Four rows fail the full package sweep**, escalated in Slice 1 and unchanged: `tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`, `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`, and two rows in `tests/test_sets_mixins.py`. All sit in the concurrent session's baseline-dirty surface; Slice 1 proved them independent of this build's diff with a deselect run (`6188 - 3 = 6185`, identical failing set). **Only the maintainer can run a clean `HEAD` tree** to confirm they are pre-existing. Repeated so the final gate's sweep is not read as this build's failure.
4. **New here:** the build plan's `## Worker-0 verification pass` D1 names `spec-048` as "Secure output defaults (0.0.17, spec-048)". `0.0.17` is wrong — the card shipped at `0.0.14` and the `0.0.17` targeting was withdrawn program-wide. The build plan is not writable by this pass; the value it seeded into the companion is corrected above.

### Failability proofs

`None; this pass introduced no new boundary.` This pass lands no runtime code, so there is no guard, gate or rejection path to prove failable. The proof obligations it *does* carry are the sweeps above, and **each carries its own negative control**, which is what makes a zero mean something:

- the staged-anchor sweep is paired with the same two grammars run against the same population for **other** cards (30 and 22 hits), so a zero produced by a mis-typed pattern would show as a zero there too;
- the `path` and deferral sweeps are paired with a replacement-vocabulary sweep (`DjangoFilePathType` 8, `filesystem_path_fields` 12, `MediaSpecimen` 5), so a zero produced by deleting the subject is distinguishable from one produced by fixing it;
- the chronology sweep is paired with the same sweep over the companion (63 occurrences);
- the duplicate-bullet scan was run over **both** documents, and the spec's 0 is what makes the companion's 1 a finding rather than an instrument artifact.

`BUILD.md`'s Worker-1 delta was also discharged: Slice 1's single failability record was audited field by field at that slice's final verification and **re-run independently by Worker 3** at the recorded scope with an identical node-id set and a byte-proved revert. No fail-open shape landed — the cycle's diff is three test functions and five assertions over an unchanged code path.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Not applicable; this pass writes no .py file.` Slice 1's re-declared scope was owned and run by its Worker 2 build pass (`/tmp/dsf-floor-037` — Python 3.10.19 / django 5.2.16 / strawberry-graphql 0.316.0, `6 passed`) and confirmed at its final verification. The final gate is the backstop for that record, not a second owner.

### Final status

`final-accepted`. All six numbered preconditions are discharged with a measurement or a recorded reason; the staged-anchor sweep is clean against a printed population with a live negative control; both under-counted populations are re-derived and closed; the spec, the companion and `HEAD` source tell one story; and the three contradictions this pass found are fixed inside its own writable surface. No consolidation loop is owed. The final test-run gate is unblocked.

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
