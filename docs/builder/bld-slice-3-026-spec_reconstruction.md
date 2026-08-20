# Build: Slice 3 — Spec reconstruction

Spec reference: `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` (whole file; the stub is 3,668 bytes at the start of this pass)
Status: final-accepted

Combined pass. The maintainer authorized Worker 1 alone on this slice: no `.py` file changes, so there is no Worker 2 build and no Worker 3 review. `## Plan (Worker 1)` is written first, the work is done against it, and `## Final verification (Worker 1)` closes it.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable in the package sense and stated rather than skipped: this slice writes no Python and proposes no helper, constant, validator, or fixture. The package-wide AST inventory (`worker-1.md` `### Package-wide helper inventory before helper planning`) exists to prevent duplicated *code* shapes; there is no code in this diff to duplicate. Shapes searched for anyway, in the two Markdown files this slice writes: an existing section shape to reuse rather than invent, and an existing measurement to cite rather than restate.
- **Existing patterns reused.** The spec's section order and per-section shape come from `docs/SPECS/spec-021-apps-0_0_7.md` (the closest structural peer: same `0.0.7` cut, same builder era, `## Key glossary references` / `## Card snapshot`-adjacent header block / `## Problem statement` / `## Goals` / `## Non-goals` / `## Slice checklist` / `## Architectural decisions` / `## Test plan` / `## Doc updates` / `## Definition of done`). `## Card snapshot`'s two-bullet trimmed form and the "the app carries more than this card's surface; those belong to the cards that added them" paragraph both come from `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md`, which is the nearest peer *in kind* — an example-app coverage card whose app grew afterwards.
- **New helpers justified.** None. No new file beyond this artifact.
- **Duplication risk avoided.** Two, both mechanical:
  1. **Spec-vs-rationale duplication.** The move rule forbids a fact living in both files. Prevented by keeping every measurement's *derivation* in the rationale and every measurement's *result* in the spec only where the result is contract. The spec states ten non-trivial converter rows; the rationale states how the population was counted and what the earlier claim quantified over.
  2. **Restating a Slice 2 `.py` passage in the spec.** Slice 2 landed the corrected `SET_NULL` prose in `apps/scalars/models.py` and the live test. The spec must not carry a second copy of that sentence; it states the `SET_NULL` behavior as contract and names the live test that pins it, which is what the `.py` sites also do — the shared shape is `AGENTS.md`'s symbol-path citation convention, reused rather than reinvented.

### Implementation steps

1. Re-derive every seeded fact (D1-D10 in the build plan, and the locators Slice 2's second final verification addressed to this slice) against HEAD before using it. A build plan's number is a claim.
2. Rewrite `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` into builder format: header block, `## Key glossary references`, `## Card snapshot`, `## Problem statement`, `## Goals`, `## Non-goals`, `## Slice checklist`, `## Architectural decisions`, `## Test plan`, `## Doc updates`, `## Definition of done`, link-definition block. Dissolve `## Other`, `## Planning note`, and the stub preamble.
3. Fix D2 and D3 in **one** edit: the sentence carrying both false clauses is rewritten as contract with no census in either half.
4. Rest the paired-model justification on D4's corrected claim; state the ten non-trivial converter rows and the two-branch mirror as the contract, with the exclusivity measurement left in the rationale.
5. Write a `## Test plan` naming **nine** live tests (D5) plus the library test, and the package tests the card retired.
6. Put the `ArrayField` / `HStoreField` exclusion in `## Non-goals` (D6).
7. Replace the placeholder `Status:` line (D9) and delete `## Planning note` (D10).
8. Add a `## Scope at HEAD`-style paragraph attributing the app's later growth to the cards that added it (D7 / D8) without implying this card shipped it.
9. Resolve the dangling `[example-schema]` / `[settings]` uses by using them inline; drop the unused `[backlog]` definition. Neither silently — both recorded here.
10. Append the reconstruction entries to the rationale companion, keyed by heading and anchor, including a **key-forwarding table** for `D4` / `D5`, whose `#other` anchor this reconstruction retires.
11. Sweep every census claim in the finished spec in **both** polarities.
12. Run `check_spec_glossary.py` and `check_trailing_commas.py --check`; disk-check every link-definition path from `docs/SPECS/`.

Line numbers are pin-at-write-time navigational hints.

### Test additions / updates

None. This slice writes no Python. `AGENTS.md` #"No pytest after edits" applies, and the dispatch explicitly records that no test run is owed. The one live-suite fact the `## Definition of done` asserts — that the card's nine tests are collected by the live module at HEAD — is checked with `--collect-only` (no execution, no `--cov*` flag), which is a mechanical existence check rather than a test run.

### Implementation discretion items

None. There is no second worker to delegate to; every choice in this slice is Worker 1's own.

### Spec slice checklist (verbatim)

`spec-026` has **no `## Slice checklist`** at the start of this pass — its absence is finding `D1` and is the reason this slice exists. As in Slice 1, the boxes below are this slice's obligations decomposed from the build plan's Slice 3 line and the dispatch, so the final-verification audit has something to audit.

- [x] The spec carries `## Slice checklist`, `## Architectural decisions`, `## Test plan`, `## Doc updates`, and `## Definition of done` (D1)
- [x] D2 and D3 fixed in one edit; neither clause survives and no replacement census is introduced
- [x] The paired-model justification rests on D4's corrected claim; the falsified exclusivity framing is absent
- [x] `## Test plan` names nine live tests, `test_scalar_specimen_introspects_json_scalar_in_both_shapes` included (D5)
- [x] The `ArrayField` / `HStoreField` exclusion is in `## Non-goals` (D6)
- [x] The spec states the card's contract without implying it shipped the app's later growth (D7, D8)
- [x] The placeholder `Status:` line is replaced (D9) and `## Planning note` is gone (D10)
- [x] `[example-schema]` and `[settings]` resolve; the unused `[backlog]` definition is disposed of deliberately
- [x] Every `## Definition of done` item is checkable against HEAD, and was checked in this pass
- [x] Both-polarity census sweep run over the finished spec
- [x] The spec narrates no history: no amendment block, no retraction, no "previously", no rev-annotation
- [x] Reconstruction entries appended to the rationale, keyed by heading and anchor, with the `#other` key-forwarding table
- [x] `check_spec_glossary.py` exit 0; `check_trailing_commas.py --check` exit 0; every link-definition path disk-checked

---

## Final verification (Worker 1)

Every number below was measured in this pass against the working tree or against the named commit. Nothing is inherited from the build plan, from Slice 1's or Slice 2's artifacts, or from my own memory file — including numbers those sources and this pass agree on.

### Re-derivation of the seeded findings

| Finding | Instrument run in this pass | Result |
| --- | --- | --- |
| D1 — stub has no auditable contract | `grep -c '^## ' docs/SPECS/spec-026-…md` before the rewrite | 3 (`## Card snapshot`, `## Planning note`, `## Other`) |
| D2 — `SET_NULL` census false | `grep -o 'on_delete=models\.SET_NULL' examples/fakeshop/apps/*/models.py \| wc -l` | **4** — `kanban` 2, `scalars` 2 (occurrences, not lines) |
| D3 — "only cross-model FK in the scalars app" false | `grep -n 'ForeignKey' examples/fakeshop/apps/scalars/models.py` | 3 FKs: `parent` (self, intra-model), `tag` -> `ScalarSpecimenTag`, `partner` -> `ScalarSpecimen`; **two** are cross-model |
| D4 — corrected claim | Django metadata over both models (below) | both declare one column per each of the ten non-trivial `SCALAR_MAP` rows; `NullableScalarSpecimen`'s twelve declared fields are all `null=True` |
| D5 — nine tests, not eight | `git show 2701eb88:…/test_scalars_api.py \| grep -c '^def test_'` | **9**; all nine present at HEAD under the same names |
| D6 — `ArrayField` / `HStoreField` | `grep -rn 'ArrayField\|HStoreField' django_strawberry_framework/types/converters.py` | sentinel-guarded branches in `convert_scalar`, **not** `SCALAR_MAP` rows — the spec's non-goal is worded accordingly |
| D7 — app growth | `grep -c '^def test_' examples/fakeshop/test_query/test_scalars_api.py`; `grep -c 'migrations.CreateModel'` on the initial migration | **29** tests (9 at ship); **5** `CreateModel` + 1 `AddField` (2 at ship) |
| D8 — `Meta.fields` | `apps/scalars/schema.py::ScalarSpecimenType` | card selection intact; `tag` added by a later card |
| D9 / D10 | spec lines 1-5 and `## Planning note` | placeholder `Status:` and the single word `shipped`, both as recorded |

Converter-population measurement, run in this pass:

```python
from django_strawberry_framework.types.converters import SCALAR_MAP
nontrivial = {k: v for k, v in SCALAR_MAP.items() if v not in (int, str)}
# len(SCALAR_MAP) -> 26 ; len(nontrivial) -> 10
```

The ten are `BigIntegerField` and `PositiveBigIntegerField` (both -> `BigInt`), `BooleanField`, `FloatField`, `DecimalField`, `DateField`, `DateTimeField`, `TimeField`, `JSONField`, `UUIDField`. `SCALAR_MAP` is byte-identical between `2701eb88` and HEAD for these ten rows (`git show 2701eb88:django_strawberry_framework/types/converters.py`), so the population the card quantified over has not moved under the claim.

Django metadata over both models, run in this pass under `config.settings`:

| Model | declared (non-`auto_created`) fields | non-trivial rows hit | `null=True` |
| --- | --- | --- | --- |
| `ScalarSpecimen` | 13 (`label`, ten scalars, `parent`, `tag`) | **10 of 10** | only `parent` and `tag` |
| `NullableScalarSpecimen` | 12 (`label`, ten scalars, `partner`) | **10 of 10** | **all 12** |

### Two findings this pass added, both from re-deriving what the build plan asserted

**D11 — the card retired SIX package tests, not three.** `a5c89c98` ("Migrate BigInt/JSON converter tests to live HTTP; isolate synthetic app_labels", 2026-05-27) deleted six test functions from `tests/types/test_converters.py`, each carrying a synthetic `managed = False` owner model that the real pair supersedes:

```
git show a5c89c98 -- tests/types/test_converters.py | grep '^-def test_'
-def test_big_integer_field_maps_to_bigint_in_schema():
-def test_big_integer_field_nullable_in_schema():
-def test_positive_big_integer_field_maps_to_bigint_in_schema():
-def test_json_field_maps_to_json_scalar_in_schema():
-def test_json_field_nullable_in_schema():
-def test_json_field_round_trips_dict_via_schema_execution():
```

All six are absent at HEAD (`grep -c` over `tests/types/test_converters.py` -> 0 for each). `CHANGELOG.md`'s `[0.0.7]` entry for this card names **three** of the six — the BigInt half — and omits the JSON half; the ship test `test_scalar_specimen_introspects_bigint_scalar_for_both_fields`'s own docstring names exactly the three BigInt ones, which is the likely lift path. The reconstructed spec states six.

**D12 — the card's footprint is four commits, not two.** `git log --grep 'DONE-048'` returns eight commits; classified by what each message says about the card rather than by proximity in time:

| Commit | Relation to the card | Evidence in the message |
| --- | --- | --- |
| `2701eb88` | card content | closes `Part of DONE-048-0.0.7.` |
| `cae2d5a3` | card content | closes `Part of DONE-048-0.0.7.` |
| `a5c89c98` | card content — the live-first retirement | "fell out of the DONE-048 converter-coverage audit"; the card's own `CHANGELOG` entry claims the removals |
| `45a8f301` | card content — the standing-docs wrap | "closes the standing-docs hygiene piece of DONE-048-0.0.7" |
| `b148fde7` | **not** card content | "Audit followup batch 2"; a separate migration stream, 29 minutes later, whose 231 added lines in `test_scalars_api.py` are among the twenty tests the app grew past this card |
| `0b91a123`, `5addc067`, `72f6cd9b` | **not** card content | each merely dates itself relative to the card ("after the DONE-048 audit migrations", "post-DONE-048") |

The build plan's `## Pre-dispatch verification` names two ship commits. That is the count of commits using the `Part of` formula, not the count of the card's commits, and it is why the doc obligations (`45a8f301`) and the live-first retirement (`a5c89c98`) were both missing from the plan's contract table. The reconstructed spec's `## Slice checklist` therefore carries three slices, and `## Doc updates` exists at all.

Zero files under `django_strawberry_framework/` are touched by any of the four (`git show --stat --format= --name-only <c> | grep -c '^django_strawberry_framework/'` -> 0, four times), which is what makes the "no package source change / no new public export" definition-of-done items true rather than assumed.

### Spec changes made (Worker 1 only)

The whole file was rewritten, so the list below is by contract rather than by line: each entry names the text as it stood, what replaced it, the reason, and the finding that triggered it.

1. **Header block.** `Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.` -> `Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-026-0.0.7`.` — the old line described the file's provenance, not the card's state, and the sibling `0.0.7` specs all carry the shipped/archived form. Trigger: **D9**.
2. **Stub preamble deleted.** "This file is intentionally lightweight… Before implementation work starts from this file, expand it into the full builder-format spec…" — the precondition it states was made moot by the ship commits, and the file it asks for is the file it now is. Trigger: **D1**.
3. **`## Planning note` deleted.** Its whole body was the word `shipped`, which the `Status:` line already carries. Trigger: **D10**.
4. **`## Other` dissolved** into `## Problem statement`, `## Goals`, `## Non-goals`, `## Slice checklist`, `## Architectural decisions`, `## Test plan`, `## Doc updates`, and `## Definition of done`. The section was a lift of `2701eb88`'s commit-message body under a heading, which is why both of its inherited defects (D4, D5) were invisible to it. Trigger: **D1**.
5. **The two-false-clause sentence, corrected in ONE edit.** As it stood: "Adds a cross-model FK `partner: ForeignKey(ScalarSpecimen, on_delete=SET_NULL, related_name="nullable_partners")` — **the only `SET_NULL` ondelete in the example tree, and the only cross-model FK in the scalars app**." Replaced by Decision 3's statement, which describes the edge's own behavior (`SET_NULL` clears `partner_id` and leaves the source row in place) and names the live test that pins it, with **no quantifier over the example tree and no quantifier over the app**. Both clauses are false at HEAD — 4 `SET_NULL` occurrences, and two cross-model FKs in the app — and a fix landing only one half would leave the reader unable to tell which half is current. Triggers: **D2**, **D3**.
6. **The paired-model justification now rests on the true claim.** The surviving `The pairing is deliberate (not a single model with paired fields)` fragment became Decision 1, whose stated reason is the per-column non-null / nullable mirror over one identical column set — the shape that makes the introspection assertions meaningful. Trigger: **D4**.
7. **`## Test plan` names nine live tests**, `test_scalar_specimen_introspects_json_scalar_in_both_shapes` included, against the stub's eight. Trigger: **D5**.
8. **`ArrayField` / `HStoreField` exclusion added to `## Non-goals`**, worded as "no `SCALAR_MAP` row of their own" because both are sentinel-guarded branches in `convert_scalar` rather than table rows. Trigger: **D6**.
9. **Later growth attributed away from the card.** A closing paragraph in `## Card snapshot`'s style names `ScalarSpecimenTag`, `Base36Field` / `OverrideSpecimen`, `MediaSpecimen`, `filters.py` / `orders.py` / `forms.py`, the mutation surface, and `ScalarSpecimenType.Meta.fields`'s `tag` entry as later cards' work. Modeled on `spec-013`'s closing paragraph. Triggers: **D7**, **D8**.
10. **`## Doc updates` and a third slice added**, covering the standing-docs wrap and the live-first retirement. Trigger: **D12** (and **D11** for the retirement's count).
11. **`## Definition of done` added**, thirteen numbered items, every one checked in this pass (table below). Trigger: **D1**.
12. **Link definitions.** `[example-schema]` and `[settings]` now carry inline uses (in Decision 2 and the `## Slice checklist`) and gained their definitions under `<!-- examples/ -->`, which was an empty group with two dangling uses. `[backlog]` was defined and never used; **dropped**, because this spec has no BACKLOG obligation to point at. Recorded rather than silently resolved, as the dispatch required.

Per-spawn status-line re-verification (`worker-1.md` `## Spec status-line re-verification`): performed as change 1 above rather than separately — the header block was the first thing read and the first thing rewritten.

### The `## Definition of done` audit — every item checked at HEAD in this pass

| # | Item | Instrument | Result |
| --- | --- | --- | --- |
| 1 | `apps/scalars/` exists with `apps.py`, `models.py`, `schema.py`, `migrations/0001_initial.py` | `ls` | all present |
| 2 | `ScalarSpecimen` declares one column per each of the ten non-trivial rows, none nullable | Django metadata | 10 of 10; all eleven scalar columns `null=False` |
| 3 | `NullableScalarSpecimen` mirrors them with `null=True, blank=True` | Django metadata | all twelve declared fields `null=True` |
| 4 | self-FK `parent`, `related_name="children"` | `models.py::ScalarSpecimen` | present, `null=True`, `CASCADE` |
| 5 | cross-model FK `partner`, `SET_NULL`, `related_name="nullable_partners"` | `models.py::NullableScalarSpecimen` | present as specified |
| 6 | both exposed via their `DjangoType`s with every converted column selected | `schema.py` | `ScalarSpecimenType` 15 card-era entries + `tag`; `NullableScalarSpecimenType` 13 |
| 7 | two root fields composed into the project `Query` | `config/schema.py` | `from apps.scalars.schema import Query as ScalarsQuery`; `ScalarsQuery` in the `Query` bases |
| 8 | `ScalarsConfig` in `INSTALLED_APPS` | `config/settings.py` | `"apps.scalars.apps.ScalarsConfig"` present |
| 9 | nine live tests in `test_query/test_scalars_api.py` | `grep '^def test_'` on the file and on `2701eb88` | all nine ship names present at HEAD; `--collect-only -q --no-cov` collects the module |
| 10 | `Patron.lifetime_fines_cents` present, selected, pinned live past `2**53 - 1` | `library/models.py`, `library/schema.py::PatronType`, `test_library_api.py::test_library_patron_bigint_lifetime_fines_over_http` | present; `large_value = 9007199254752336`; asserted as a decimal string |
| 11 | six superseded package tests absent | `grep -c` per name over `tests/types/test_converters.py` | 0 for all six |
| 12 | no package source change, no new public export | `git show --stat --format= --name-only` over all four commits | 0 files under `django_strawberry_framework/` |
| 13 | standing docs carry the card | `CHANGELOG.md` `[0.0.7]` `### Added`; `KANBAN.md` Done card; `docs/TREE.md`; `TODAY.md` | all four carry it (see the deferred catalog for the two that carry it *wrongly*) |

Item 10's migration is a squash artifact and is checked at the right place: `0003_patron_lifetime_fines_cents.py` no longer exists as a file, and the column is in `apps/library/migrations/0001_initial.py` (`grep -n 'lifetime_fines_cents'` -> one hit). Item 13 asserts presence, never accuracy — `KANBAN.md` and `CHANGELOG.md` carry claims this cycle cannot close, catalogued below.

### Both-polarity census sweep over the finished spec

Run over the rewritten spec with **both** vocabularies — `only` / `sole` / `no other` / `the one` **and** `every` / `all` / `each` / `always` — because a positively-spelled universal is invisible to a negative-vocabulary sweep, and that exact blind spot cost Slice 2 a revision loop.

- **35 occurrences, every one read in context** (`grep -ioE` over both vocabularies, counting occurrences rather than matching lines). Four are the idiomatic compounds `PostgreSQL-only`, `read-only`, `non-live`, and `at all`, and one is the peer-standard companion sentence in the header block; none is a census. No hit quantifies over the example tree, over the repository, or over "no other example app". The census the stub carried in both those shapes is gone from the spec in both polarities.
- **Two of the census hits were universals this pass had just written, and the sweep is what caught them.** `Sixteen collapse to plain int or plain str and are exercised transitively by **every model-backed type in the example project**` quantified over a population nobody counted — and is false for the `SlugField` / `URLField` / `GenericIPAddressField` / `FilePathField` rows, which no example model need carry at all. `Before this card those twenty shapes were pinned **only** by package-internal tests` asserted a tree-wide absence. Both were rewritten into local, unquantified statements before this section was finalized. Recorded because the pass writing the fix is a first-class suspect, not an auditor standing outside the file.
- The surviving universals quantify over one of three closed, named populations, each stated in the sentence that uses it: the ten non-trivial `SCALAR_MAP` rows (measured, and the table is in the package), the columns one named model declares (measured via Django metadata), and the nine tests one named module carried at ship (measured against `2701eb88`). Each is falsifiable only by a change to the thing the sentence is about, which is the property Slice 2 established as the standard.
- `## Non-goals`'s "no write surface" claim is scoped to `apps/scalars` by name. Tree-wide it would be false: `apps/products/schema.py::DeleteItem` is the tree's one delete mutation (`git grep -n 'class Delete' -- 'examples/fakeshop/apps/*/schema.py'` -> exactly 1 hit, re-run in this pass).

### History-narration check

`grep -inE 'previously|used to|no longer|formerly|as of |amend|retract|rev-[0-9]|round [0-9]|earlier version'` over the rewritten spec.

**The first run returned three hits, and two of them were mine.** The three `Rationale companion — …` pointer lines the move rule requires had been written chronologically ("the exclusivity justification this decision **no longer** rests on"; "the two census claims this decision **used to** carry"), which is precisely the reader-applies-a-chronology failure the spec is forbidden to contain — written, as these things are, inside the sentences whose job was to keep history out. Both were rewritten to name the rationale entry's *content* rather than the spec's past: "the measurement behind the mirror claim", "the replacement framings weighed and rejected here".

The rerun returns **one** hit, the header block's companion-pointer sentence, and it stays: it is the peer-standard form, character-for-character the shape `docs/SPECS/spec-021-apps-0_0_7.md:8` and `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md:7` both use (`every claim this spec once made and may no longer make`), and it describes what the rationale file *contains* rather than what this file used to say.

### Rationale entries appended

Appended to `docs/SPECS/appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md`, in the shape its own `## Entry shape for entries appended after this pass` fixes, each keyed to a spec heading and anchor:

- `## Key forwarding` — the `#other` anchor `D4` and `D5` key to no longer exists. A table maps each earlier entry to the section and anchor that now carries its decision. Appended rather than edited into `D4` / `D5`, because the rationale is append-only during a build (`worker-1.md` rule 4) — the two earlier entries' arguments are untouched, and the `[spec-026-other]` link definition is left as it stands for the same reason, with this table as the on-disk resolution.
- `D1` — why the reconstruction has the sections it has, and why `## Other` could not survive as a section.
- `D2 / D3` — the two false clauses, the rejected replacement framings (including the two that measure true today and are the same *shape* of claim), and the claims the decision may no longer make.
- `D6` — the `ArrayField` / `HStoreField` scope decision, and why it is worded as "no `SCALAR_MAP` row of their own".
- `D11` — six retired package tests against the `CHANGELOG`'s three, with the lift path.
- `D12` — the four-commit footprint, the classification rule used, and why `b148fde7` is out.

### Plan contract, declarations, and gates

- **Every planned step landed.** Steps 1-12 of `### Implementation steps` are each evidenced above or in the gate results below. Nothing planned was dropped or silently rejected.
- **Ownership partition: none — holds.** One worker, one pass; no second cohort's diff exists.
- **Hot-path declaration: none — re-verified against the landed diff.** The diff is three Markdown files. No `.py` file was opened for writing. `git status --short -- '*.py'` lists **five** modified files, and none is this pass's: `_strawberry_patches.py`, `optimizer/hints.py`, and `tests/optimizer/test_hints.py` are on the build plan's baseline-dirty out-of-scope list, and `examples/fakeshop/apps/scalars/models.py` and `examples/fakeshop/test_query/test_scalars_api.py` carry **Slice 2's landed, uncommitted** edits. All five untouched and unreverted. The tree has also grown concurrent work since the build plan's baseline snapshot (`docs/SPECS/spec-024-…md`, `spec-025-…md` and their rationales are now dirty or untracked); observed, not touched.
- **Floor-verification scope: none — re-verified.** No import, no Django / Strawberry / channels API, no version-sensitive construct in the diff. `docs/builder/BUILD.md` `## Floor verification` remains the single canonical statement of the floor versions; no floor number is restated here.
- **Failability proofs:** `None; this pass introduced no new boundary.` The diff contains no branch, guard, gate, or rejection path — there is nothing to mutate.
- **Fail-open shapes: none possible.** The diff adds no expression.
- **Boundary count: 0**, so the split question is answered without a split.
- **Cross-slice duplication.** Checked against Slice 1 and Slice 2. Slice 1 wrote the rationale frame plus `D4` / `D5`; Slice 2 wrote four prose passages in two `.py` files; this slice wrote the spec body plus six rationale entries. No sentence is shared between the spec and the `.py` sites, and no rationale entry restates one already there — the `#other` forwarding table exists precisely so the reconstruction does not have to restate `D4` / `D5`.
- **Staged-anchor sweep:** `git grep -n 'TODO(spec-026'` -> **0** repo-wide.
- **Gates:** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` -> `OK: 3 terms - all have glossary entries and at least one spec link.`, exit **0**. `uv run python scripts/check_trailing_commas.py --check` scoped to the three files this slice wrote -> exit **0**. Every link-definition path in both Markdown files disk-checked from its own directory -> all resolve.
- **Focused test run: not owed and not run.** This slice writes no Python; `AGENTS.md` #"No pytest after edits" applies and the dispatch records the exemption. The one suite fact the definition of done asserts is checked by `--collect-only` with no `--cov*` flag.

### Spec slice checklist audit

Thirteen boxes, all `- [x]` in the plan above after this pass. Audited against the diff:

| Box | Verdict | Proof run in this pass |
| --- | --- | --- |
| 1 — five missing sections present | tick | `grep -c '^## '` -> **10** headings and `grep -c '^### '` -> 10; all five named sections present |
| 2 — D2/D3 in one edit, no replacement census | tick | `git grep -F 'only cross-model FK in the scalars app' docs/SPECS/` -> 0; `git grep -F 'only `SET_NULL` ondelete in the example tree' docs/SPECS/` -> 0; both-polarity sweep above found no replacement census |
| 3 — D4's corrected claim | tick | `grep -c 'no other example app' docs/SPECS/spec-026-…md` -> 0; Decision 1 states the mirror shape |
| 4 — nine tests | tick | the nine names are each in `## Test plan`; `grep -c 'introspects_json_scalar_in_both_shapes'` -> 1 |
| 5 — non-goal added | tick | `## Non-goals` item 1 |
| 6 — later growth attributed away | tick | the closing paragraph of `## Card snapshot` names six later surfaces and attributes none to this card |
| 7 — `Status:` replaced, `## Planning note` gone | tick | header line 3; `grep -c '^## Planning note'` -> 0 |
| 8 — link definitions | tick | `[example-schema]` and `[settings]` each used inline and defined; `grep -c '^\[backlog\]'` -> 0 |
| 9 — every DoD item checkable and checked | tick | the thirteen-row audit table above |
| 10 — both-polarity sweep | tick | the sweep section above, 21 hits read |
| 11 — no history narration | tick | the narration grep -> 0 hits |
| 12 — rationale entries appended and keyed | tick | six entries, each opening with `**Keys to:**` and a heading anchor. `D4` / `D5` untouched: the append was a programmatic concatenation that never rewrote the prefix, and each entry's heading occurs exactly once (`grep -c` -> 1, twice). The file is untracked, so `git diff` proves nothing here and is not cited. The **link-definition block did change** — nine definitions added and the `<!-- docs/SPECS/ -->` group re-alphabetized — which is link maintenance, not entry revision; `[spec-026-other]` itself was left byte-identical |
| 13 — gates | tick | both scripts exit 0; every link path disk-checked |

No box is over-ticked, none is left `- [ ]`, so no deferral reason is owed under `### Spec changes made (Worker 1 only)`.

### Deferred work, for the final gate's `### Deferred work catalog`

Five items. Each locator was re-run in this pass; a catalog is a claim, not an inheritance — and re-running Slice 2's three-item catalog here turned up a fourth site it had missed.

1. **`KANBAN.md` AND `KANBAN.html` carry the two-false-clause sentence verbatim.** `grep -rln 'only cross-model FK in the scalars app' --exclude-dir=.git .` returns six files: `KANBAN.md`, **`KANBAN.html`**, and four that are this cycle's own record (the rationale companion quoting it as a retired claim, and three `026` builder artifacts). The spec copy is gone. **`KANBAN.html` is a site Slice 2's catalog did not name** — it was found here by dropping the path list from the grep, which is the difference between measuring a population and measuring a guess about one. Both files are DB-rendered (a fix is a fakeshop kanban DB edit plus `scripts/build_kanban_md.py`; `KANBAN.html`'s Vue shell is additionally hand-maintained and only its data block regenerates), both are on the build plan's baseline-dirty do-not-edit list, and both are outside the maintainer's spec-and-`.py` scope fence. **No slice of this cycle closes either.**
2. **`KANBAN.md` and `CHANGELOG.md` carry `D4`'s shape.** `grep -n 'no other example app' KANBAN.md CHANGELOG.md` -> exactly **two** lines, one in each file, and no third site anywhere. Same three fences; the `CHANGELOG` line is additionally a historical ship record.
3. **`CHANGELOG.md`'s entry for this card names three retired package tests where six were retired** (`D11`), and describes the live surface as "eight tests" where nine shipped (`D5`). Same fences. Recorded here because `D11` is new in this pass and appears in no earlier catalog.
4. **`KANBAN.html`'s copy of `D4`'s shape**, alongside item 2's two files, for the same reason and under the same fence.
5. **`docs/TREE.md`'s one-line description of `test_scalars_api.py`** describes the module's HEAD surface ("scalar wire formats, filtering, relations, and optimizer behavior"), which is correct for the module and says nothing false about this card. **Not deferred work** — recorded only so the next reader does not re-open it as a fourth item.

### Summary

Expanded the `015`+ era's last surviving spec stub into a full builder-format spec stating the contract the shipped code delivers: ten top-level sections (3,668 -> 21,324 bytes), three slices, six architectural decisions, a nine-test test plan, and a thirteen-item definition of done every one of which was checked against HEAD in this pass. Both false clauses in the stub's one sentence were corrected in a single edit with no replacement census; the falsified exclusivity justification was replaced by the measured mirror claim; the deliberate PostgreSQL-only exclusion became a non-goal; and the app's later growth is attributed to the cards that added it. Two findings the build plan did not carry were re-derived here and are now contract: the card retired **six** package tests, not three, and its footprint is **four** commits, not two — which is why the spec has a `## Doc updates` section at all.

### Outcome

`final-accepted`. Thirteen checklist boxes, thirteen ticks, each audited against the diff. Ownership-partition, hot-path, and floor-verification declarations all `none` and all re-verified against the landed diff; the failability-proof exemption holds and is recorded rather than blank. Three Markdown files written, no `.py` file opened, no `-terms.csv` edit, no baseline-dirty file touched. Five deferred items catalogued, all fenced, one of them a site no earlier catalog in this cycle had found.

Status: final-accepted

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
