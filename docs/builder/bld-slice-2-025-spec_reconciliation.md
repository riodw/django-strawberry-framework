# Build: Slice 2 — Spec reconciliation (D1-D13)

Spec reference: `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` (whole file)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Reuse.** No code pattern is in play: this slice writes Markdown only. The reuse that matters is *shape* reuse — the reconciliation form the recently reconciled siblings use (`docs/SPECS/spec-023-multi_db-0_0_7.md`, `spec-042`, `spec-043`, `spec-044`): a `python3.14` venv citation path, a declared-floor rather than resolved-version phrasing of a version constraint, and a Decision heading that names the posture rather than a moment. Each is applied here rather than invented.
- **Duplication risk this slice creates.** Two: (a) a fact stated in both the spec and the rationale drifts apart later, and (b) an enumeration in the spec duplicates an enumeration in code or tests. The plan avoids (a) by keeping every *change record* in the rationale and every *contract* in the spec, with no chronology in the spec; and (b) by **deleting** enumerations rather than refreshing them wherever the enumeration's owner is elsewhere — the `__all__` tuple (owner: `tests/base/test_init.py::test_public_api_surface_is_pinned`), the ten converter test sites (owner: the live-coverage rule), the `tests/test_scalars.py` item total (owner: nothing — a shared file has no single owner, so the count is not a contract).
- **New helper justified.** None. No `.py` file is touched, so no `ruff` run.

### Implementation steps

1. Rename Decision 8's heading to state the joint-cut posture, sweeping the moved slug through all 7 in-page uses in the spec and both occurrences in the rationale in the same pass.
2. Rewrite Decision 8's body; the rewrite drops the `](#step-3--read-the-kanban)` break and the inline `](../../CHANGELOG.md)` link with it.
3. Work D1-D13 in catalog order, then discharge the two deferred anchor defects, the 5 dead link definitions, and every `python3.10` citation.
4. Audit every `#"..."` substring anchor against its target file (`grep -F`) — the D12 sweep only covers paths, not substrings.
5. Update each rationale `### D<n>` entry to name the edit that discharged it; correct the provenance table's justification-bullet count; re-point the rationale's own inherited `python3.10` citations.
6. Gates: `check_spec_glossary`, `check_trailing_commas --check`, `git diff --check`, the anchor / reference / link-convention sweeps on both files, and a chronology sweep on the spec.
7. Read the whole spec end to end and confirm it reads as a contract that was right from the start.

### Test additions / updates

None. This slice touches no `.py` file and no test. The spec's *statements about* tests changed; the tests did not.

### Implementation discretion items

None delegated — Worker 1 is the sole writing role in this cycle, so there is no second party to delegate to.

### Spec slice checklist (verbatim)

This slice is a reconciliation pass, not a spec slice: the spec's own `## Slice checklist` describes the original card's five build slices, none of which this pass implements. The checklist this pass is audited against is the divergence catalog in `docs/builder/build-025-scalar_map_helper-0_0_7.md` `### Verified post-ship divergences handed to Worker 1`, plus the two anchor defects Slice 1 deferred.

- [x] D1 — the card shipped inside the `0.0.7` cut, not under `[Unreleased]`
- [x] D2 — `scalars.py` declares a module `__all__`
- [x] D3 — the `Upload` forward-compatibility mechanism
- [x] D4 — `_parse_bigint` / `_serialize_bigint` "unchanged from `0.0.6`"
- [x] D5 — the specified fail-open shape, and the new `ValueError`
- [x] D6 — the `repr` fallback is a helper, and it is tested
- [x] D7 — the test counts
- [x] D8 — the live-test rejection reversed by `DONE-026-0.0.7`
- [x] D9 — the fakeshop constructor and the optimizer factory shape
- [x] D10 — the enumerated `__all__` tuple
- [x] D11 — the dead re-tag hypothetical
- [x] D12 — `python3.10` citations and the stale Strawberry floor
- [x] D13 — the doc-side claims about files the card chose not to edit
- [x] Deferred anchor defect 1 — `](#step-3--read-the-kanban)`
- [x] Deferred anchor defect 2 — `[spec-023-decision-9]` pre-rename slug
- [x] The spec's 5 dead link definitions
- [x] The spec's 10 unresolved in-page anchors (1 fixed, 9 recorded as correct-as-written — see `### Anchors that remain unresolved, and why`)

---

## Build report (Worker 2)

Not applicable: no code change was needed, so Worker 2 was never dispatched (`docs/builder/build-025-scalar_map_helper-0_0_7.md` `## Cycle shape`). Worker 1 performed the Markdown edits directly, and the report of what landed is `### Spec changes made (Worker 1 only)` below.

---

## Review (Worker 3)

Not applicable for the same reason — there is no builder diff for a reviewer to check against a plan. Every check a review pass would own was performed in `## Final verification (Worker 1)`, against source rather than against this pass's own prose.

---

## Final verification (Worker 1)

Read-only HEAD comparisons used `git show HEAD:<path>` into a scratch path **outside** the repository. No `git stash`, `checkout`, `restore`, or `worktree` at any point — three concurrent cycles (`spec-024`, `spec-026`, plus the maintainer) are live on this tree.

### 1. Gates

| Gate | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` | `OK: 17 terms - all have glossary entries and at least one spec link.` exit **0** — the count DoD 9a pins, **unchanged** by this pass, so no DoD edit is owed |
| `uv run python scripts/check_trailing_commas.py --check` on the spec and the rationale | exit **0** |
| `git diff --check` on the spec | exit **0**, no output |
| trailing whitespace / tabs, both files (the rationale is untracked, so `git diff --check` cannot see it) | **0** lines matching `\t` or ` $` in either file |
| `pytest` | not run; no `.py` file in the slice, and no `--cov*` flag was used anywhere in this pass |
| `ruff` | not run; no `.py` file touched |

### 2. Anchors, references, and the link convention

Instrument: a sweep that strips fenced blocks and inline code spans before matching (a `#anchor` inside a code span is prose about an anchor, not an anchor — the trap that made Slice 1's first sweep over-report by 5).

| Check | Spec | Rationale |
|---|---|---|
| `<!-- LINK DEFINITIONS -->` delimiters | 1 | 1 |
| 10 canonical group headers, canonical order | yes | yes |
| alphabetical by ref id within every group | yes | yes (re-sorted after the four additions; sorting whole *lines* instead of ids puts `[next-step-8]` before `[next]`, which is wrong — the convention sorts by id) |
| `used-not-defined` | `[]` | `[]` |
| `defined-not-used` | `[]` | `[]` |
| link-definition targets: file exists, `#fragment` resolves against the target's real headings | **0 failures** (was 5) | **0 failures** |
| inline cross-file links (convention forbids) | **0** (was 2) | **0** (was 1) |
| unresolved in-page anchors | **9**, all correct as written — below | **0** |

The 5 previously dead spec definitions, each repaired rather than deleted:

- `[config]`, `[scalar]` — `python3.10` → `python3.14` (D12).
- `[spec-023-decision-9]` — `#decision-9--joint-0_0_7-cut` → `#decision-9--joint-007-cut`. Verified against the sibling's real heading, `### Decision 9 — Joint \`0.0.7\` cut`: a dotted version slugs to `007`, never `0_0_7`.
- `[today-what-to-put-in-examplesfakeshopconfigschemapy-today]`, `[today-whats-in-examplesfakeshopappsproductsschemapy-today]` — `TODAY.md`'s headings have been shortened to `## What to put in \`config/schema.py\` today` and `## What's in \`products/schema.py\` today`. Both defs were re-pointed at the real slugs, **both ref ids renamed to match**, and the **visible link text** updated at all 5 use sites — a def-only fix would have left the spec printing a path that no longer exists.

**Substring citations audited separately, and this is where the D12 catalog was incomplete.** D12 names paths; a `#"..."` substring anchor can rot without the path changing. Every one of the spec's `#"..."` anchors was `grep -F`-checked against its target file: **18 distinct anchors resolve**, and **3 did not**, across **8 uses**:

- `#"Migration to a"` (4 uses) — the `CHANGELOG.md` line it cites is the one this card **removes**, so the anchor is dead by construction. Rewritten to cite `[`CHANGELOG.md`][changelog]` plainly; the quoted sentence is already in the text.
- `#"strawberry.Schema(query=Query"` against `GOAL.md` (3 uses) and `examples/fakeshop/config/schema.py` (1 use) — both files now break that call across lines, so the substring exists in neither. All 4 anchors dropped; the surrounding claims were rewritten under D9 anyway.

### 3. Anchors that remain unresolved, and why

All 9 are inside **quoted `docs/GLOSSARY.md` entry text** — the Slice 4 checklist bullet and the `## Doc updates` pinned bodies: `#bigint-scalar` ×2, `#upload-scalar` ×2, `#specialized-scalar-conversions` ×2, `#strawberry_config` ×2, `#djangotype` ×1, `#djangooptimizerextension` ×1 (that last one added by this pass, syncing the quoted body to the live entry).

They cannot be "fixed" without breaking what they are for: they resolve in `docs/GLOSSARY.md`, which is where the quoted text lands, and the spec's obligation is to quote that text accurately. Rewriting them as reference links into the spec would make the pinned bodies differ from the file they pin, which is the defect the pin exists to prevent. Recorded rather than left silent.

The one genuine break among the original ten, `](#step-3--read-the-kanban)`, is gone: it pointed at a step of an authoring flow the spec never contained, and the Decision 8 rewrite dropped the sentence that carried it.

### 4. Chronology sweep on the spec

Occurrences, `grep -o … | wc -l`: `Revision 1` **0**, `as of revision` **0**, `as of review` **0**, `Amendment` **0**, `Retraction` **0**, `review round` **0**, `Superseded` / `superseded` **0**, `archaeology` **0**, `Unreleased` **0**, `2026-05-23` **0**, `0.0.8` **0**, `DONE-NNN` **0**, `python3.10` **0**, `0.262.0` **0**, `37+` **0**, `22+` **0**.

Three phrase families survive and are correct:

- `no longer` / `pre-migration` / `post-migration` (11 occurrences) describe the `0.0.6` → `0.0.7` **registration break** — the card's subject matter. A migration card that cannot say what changed for consumers is not a contract.
- The `Rationale companion —` pointer lines name what is in the companion, including the words `retracted` and `Revision history`. `worker-1.md` `### Performing the rationale move` rule 1 requires those pointers.
- `## Current state` is the problem statement's baseline. It was given an explicit one-line framing — "the `0.0.6` surface … Every bullet below is a statement about that starting surface, not about the shipped result" — because an unframed section titled "Current state" in a shipped spec reads as a claim about `HEAD`, and three of its bullets would then be false. Deleting the section instead would strand the Slice checklist, whose items name the things it enumerates.

### 5. Every claim I asserted was measured or read against source

No figure or fact below was inherited from the build plan or the rationale without re-derivation.

| Claim | Instrument | Result |
|---|---|---|
| Decision 8 slug uses in the spec | `grep -o <slug> \| wc -l` | **7** (Slice 1's corrected figure; the memory note's earlier "6" was wrong) |
| Decision 8 slug uses in the rationale | same | **2** (one in-page anchor at the Revision-1 entry + the `[spec-025-d8]` def). Distinct population from the "5 `spec-025-d8` occurrences" the carry-forward names — that counts the **ref-id token**, not the slug; both figures are true of different things |
| `python3.10` in the spec | same | **14** before, **0** after |
| `python3.10` in the rationale, in moved text | same | **6** before, **0** after (2 descriptive mentions remain, in D12's own heading and Slice 1's verification record) |
| CHANGELOG heading the bullets live under | `grep -n '^## \['` + line numbers of the three bullets | bullets at 174 / 182 / 190-ish sit between `## [0.0.7] - 2026-05-27` (166) and `## [0.0.6]` (208) — **inside the `0.0.7` cut**, as D1 states |
| `__version__` at HEAD | `pyproject.toml`, `django_strawberry_framework/__init__.py` | **0.0.14**, not `0.0.7` — Decision 8's second, uncatalogued falsehood |
| `__init__.py` `__all__` size | parsed the tuple | **37** names, `strawberry_config` **last**. The plan says "30+" and the rationale says 37; 37 is right |
| `scalars.py` `__all__` | read the module | `["BigInt", "Upload", "UploadDefinition", "strawberry_config"]` — which is why the spec states the *contribution* rather than enumerating |
| `strawberry_config` body at HEAD | read `django_strawberry_framework/scalars.py` | explicit `if extra_scalar_map is None:`, `try` / `except BaseException` → `ValueError("… must be materializable; …") from exc`, `_safe_scalar_map_key_label` in the collision message, and that helper's own `try` / `isinstance(name, str)` guards. The spec's pinned block now matches this |
| `tests/test_scalars.py` items | `grep -c '^def test_'` | **53**; the four factory-boundary tests the spec now names all exist (lines 356, 397, 431, and the two `Upload` pins at 583 / 609) |
| `tests/types/test_converters.py` BigInt section | read the section + `grep -c 'config=strawberry_config()'` | **4** migrated sites remain, plus the deliberately-unmigrated `test_big_auto_field_still_maps_to_int`; the file's own banner comment records the six promoted to live coverage. Six of the spec's ten named sites exist nowhere |
| fakeshop `BigIntegerField` columns | `grep -rn 'BigIntegerField' examples/fakeshop/apps/*/models.py` | `apps/scalars/models.py` (`signed_big`, `unsigned_big`, plus a nullable pair) and `apps/library/models.py` (`lifetime_fines_cents`) — so the Risks item that said fakeshop has none is now the opposite claim, and true |
| live scalars suite size | `grep -c 'def test_'` on `examples/fakeshop/test_query/test_scalars_api.py` | **29** |
| declared floors | `pyproject.toml` | `strawberry-graphql>=0.316.0`, `Django>=5.2.16`, `requires-python >=3.10,<4.0` |
| on-disk venv | `ls -d .venv/lib/*/site-packages` | `python3.14` only |
| justification bullets at HEAD | per-block count over `git show HEAD:` | `[3, 8, 3, 4, 4, 3, 5, 4, 4]` = **38**; the rationale carries **37** under its nine `### Justification` headings, so 37 moved and 1 was retained |
| spec bytes | `wc -c` | **135,777** at HEAD → **114,760** now |
| rationale bytes | `wc -c` | **92,007** (Slice 1 left it at 76,554) |

### 6. The count Slice 1 corrected once and still got wrong

Slice 1's final-verification pass corrected the justification-bullet population from 37 to 38 **in its own artifact** and did not carry the correction into the rationale's `## Provenance of this record` table, which still read `37 (36 moved, 1 retained)`. Re-derived here from `git show HEAD:` as `[3, 8, 3, 4, 4, 3, 5, 4, 4]` = 38, cross-checked against the rationale's own 37 present bullets, and fixed in the table with the per-block derivation recorded beside it. The rationale's closing "two inherited figures were wrong" bullet now says three and names this one.

This is the same lesson a third time in one cycle and it is worth stating precisely: **a correction lands where the corrector was looking.** Slice 1's pass was auditing an artifact, so it fixed the artifact; the durable record kept the wrong number, and the durable record is the one a future reader trusts.

### 7. Rationale coherence

Every `### D<n>` entry now names both the drift and the edits that discharged it, keyed by reference-style anchor into the spec headings it touched. The 4 new ref ids the resolutions needed (`[build-tree]`, `[spec-025-goals]`, `[spec-025-key-glossary]`, `[spec-025-out-of-scope]`) were added and resolve. Slice 1's verification section was retitled `## Verification performed by the rationale move (Slice 1)` and a `## Verification performed by the spec reconciliation (Slice 2)` section appended, so "this pass" is never ambiguous in an append-only file. One inherited inline cross-file link in Decision 8's moved text (`](../../../CHANGELOG.md)`, carrying a `#"## [Unreleased]"` substring anchor for a heading that no longer exists) was converted to the reference-style `[changelog]` with the anchor dropped.

### 8. Scope compliance

`git status --short` confirms this pass wrote exactly its authorized paths: `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`, `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`, this artifact, and `docs/builder/worker-memory/worker-1-025.md`. No `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `CHANGELOG.md` / `docs/TREE.md` / `GOAL.md` / `TODAY.md` / `README.md` edit, no `db.sqlite3` write, no `-terms.csv` edit. `docs/builder/bld-slice-1-025-rationale_authoring.md` was read and not written. Nothing belonging to the concurrent `spec-024` or `spec-026` cycles was touched, and **nothing baseline-dirty was reverted** — the tree has since grown `docs/SPECS/spec-024-*.md`, `spec-026-*.md`, their rationale companions, and several `-024` / `-026` artifacts, all of them another session's and all untouched. No other worker's memory file was read or written. No commit, no branch.

### 9. The end-to-end read

Performed after the checklist, as the deliverable rather than a formality — and it earned its keep: the sweeps were clean while four claims were still false, and only reading found them.

- Slice 1's `__init__.py` bullet and Slice 2's `tests/base/test_init.py` bullet still said `__all__` appends "after `\"finalize_django_types\"`" — the positional claim D10 retires, in two sites the catalog does not list (it names DoD 3, DoD 18 and the Edge case). A third instance sat in the Test plan's "Existing tests" paragraph.
- The Slice 3 audit-only bullet claimed `grep -n "BigInt" examples/fakeshop/` "currently returns no matches". It returns many now — the same fact D8 records from the other side. Rewritten to the structural reason the per-app schemas need no edit (none constructs a schema), which does not decay.
- The `## Current state` `CHANGELOG.md` bullet said "anchored at the `\"Migration to a\"` substring above" after this pass had removed that anchor — an edit creating a dangling back-reference two hundred lines away.
- Decision 1 asserted the spec "lives at `docs/spec-025-scalar_map_helper-0_0_7.md`", contradicting its own next paragraph's rule now that the archive pass has run.

The spec now reads as a contract: what the factory must do, what it must reject, which files change and which do not, and why each rejection path exists. Nowhere does a reader have to apply a date, a card, or a review round to it to find out what is currently true.

### Summary

All thirteen catalogued divergences are discharged in the spec, plus the two anchor defects Slice 1 deferred, all 5 dead link definitions, 8 uses of 3 dead substring anchors the catalog did not cover, and 4 further false claims the end-to-end read found. The spec dropped 21,017 bytes (135,777 → 114,760) — almost all of it enumerations deleted rather than refreshed, which is the durable half of this pass: an enumeration whose owner is elsewhere goes stale again, so the spec now states the rule and names the owner. Every one of the thirteen rationale entries closes with the edit that discharged it, and one wrong count that survived Slice 1's own correction pass was re-derived and fixed in the durable record. Gates green, nothing outstanding, nothing deferred that is not written down below.

### Spec changes made (Worker 1 only)

All edits are to `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` unless noted. Line citations are pre-edit positions in the HEAD file.

| Spec line(s) | Change | Reason | Divergence |
|---|---|---|---|
| 296 (heading) | `Decision 8 — Version posture: cut already shipped, this card lands under \`[Unreleased]\`` → `… this card ships inside the \`0.0.7\` cut`; slug swept through 7 spec uses and 2 rationale occurrences | the heading named a false posture | D1 |
| 3 | `Target release:` now says the card ships inside the joint cut, entries under `## [0.0.7] - 2026-05-27` | the header's first factual claim was false | D1 |
| 298-300 | Decision 8 body rewritten to the joint-cut contract; the `__version__ = 0.0.7` claim and the `[Unreleased]` promotion both dropped | `__version__` is `0.0.14`; the entries are in the cut | D1 + a further falsehood in the same paragraph |
| 298 | `[Step 3](#step-3--read-the-kanban)` and the inline `](../../CHANGELOG.md)` removed with that sentence | anchor resolved to no heading; inline cross-file link violates `START.md` | deferred anchor defect 1 |
| 23, 55, 56, 476, 479, 490, 494, 501, 548, 549 | every `[Unreleased]` occurrence replaced by the shared `[0.0.7]` section, and the bump reassigned to the cut's last card | the card shipped inside the cut | D1 |
| 407, 410, 48 | GLOSSARY index-row and entry-status pins `shipped ([Unreleased])` → shipped (`0.0.7`) | matches the landed GLOSSARY | D1 |
| 34 | Slice 1 import bullet retitled "Import and module surface"; states the module declares an `__all__` this card adds two names to | the pinned surface omitted `__all__` | D2 |
| 239-241 (block) | pinned block gains the `.exceptions` import and a comment naming the base-descriptor normalization; the `# Parser and serializer unchanged from 0.0.6.` comment removed | the bodies are hardened; the wire format is what is stable | D4 |
| 253-264 (block) | pinned block gains the `is None` branch, the `BaseException` materialization guard, `_safe_scalar_map_key_label`, and three bullets naming which properties are contract | the spec **specified** a fail-open truthiness test | D5, D6 |
| 193-195 | `## Error shapes` gains the materialization `ValueError` with its message and `from exc` chaining | a new error shape was undocumented | D5 |
| 270 | Decision 4 gains the "only rejection class" statement and the `ConfigurationError` contrast | the uniformity is a contract, and the guard is what makes it one | D5 |
| 332 | the `extra_scalar_map={}` edge case split into an outcome-not-truthiness bullet plus a new unmaterializable-mapping bullet | same | D5 |
| 339 | "Collision-error message stability" rewritten around `_safe_scalar_map_key_label` and its three hostile-key cases; "is not separately tested" deleted, both pinning tests named | the fallback is a tested helper now | D6 |
| 15, 87, 65, 96, 505, 514 | five `Upload` surfaces rewritten to the real mechanism (already in `DEFAULT_SCALAR_REGISTRY`, **no** map entry) and Risks item 5 rewritten to the general rule | the prediction was right in outcome, wrong in mechanism | D3 |
| 290, 341, 348, 350, 401, 533 | "fifteen new items" → "contributes fifteen"; `22+15 = 37+` and both `22+` counts deleted; the Test plan names the three later boundary tests | a shared file's total is nobody's contract | D7 |
| 41, 292, 536 | converter-test migration stated as a rule; the ten-site enumeration deleted; live-coverage rule named as the owner of *which* cases live where | six of the ten sites exist nowhere | D8 |
| 507 | Risks "fakeshop does not exercise `BigInt`" inverted to the true claim, with the live tier named | `DONE-026-0.0.7` reversed it | D8 |
| 44, 306, 538, 137-141, 172, 419, 448 | Decision 9 / Slice 3 / DoD 7 narrowed to the two-line `config=` edit; the User-facing API examples and the quoted GLOSSARY bodies moved to `extensions=[lambda: _optimizer]`; DoD 8 widened to every app `schema.py` | the constructor and extension shape are other cards' | D9 |
| 340, 532, 535, 550, 397 | the nine-name `__all__` enumeration and every "after `\"finalize_django_types\"\`" positional claim deleted; the ASCII-sort rule kept and `test_public_api_surface_is_pinned` named as the owner | the enumeration is stale; the rule is not | D10 |
| 501, 502, 54, 469, 547 | every `WIP-ALPHA-020-0.0.8` / `docs/spec-020-…-0_0_8.md` / `DONE-NNN` remnant deleted; the card keeps `DONE-025-0.0.7` and the spec pins the body, not the number | a dead contingency and a placeholder id | D11 |
| 33, 39, 60, 67, 194, 215, 328, 335, 338, 471, 506, 641, 642 | all 14 `python3.10` → `python3.14`, including the two link definitions; the inline `](.venv/…config.py)` converted to `[config]` | dead paths, and one convention violation | D12 |
| 506 | Risks "Strawberry version pin compatibility" rewritten around the declared `>=0.316.0` floor, with the venv reading named as the top of the range | `>=0.262.0` was stale, and a resolved version is not a constraint | D12 |
| 328 | the overload edge case likewise restated against the declared range | same | D12 |
| 51, 464, 545 | TREE claims restated as "no structural edit" + "script-rendered from module docstrings, never hand-edited", citing `scripts/build_tree_md.py` | the rendered line changed and always will | D13 |
| 546 | DoD 14 restated as a statement about this card's scope, with the release-line bullet named as not this card's | root `README.md` is no longer untouched | D13 |
| 47, 452, 542 | `docs/README.md` obligations re-scoped from a named-example list to a rule; the Relay-Node sub-bullet's target loss made harmless | that example no longer constructs a schema | D13 |
| 615 | `[spec-023-decision-9]` → `#decision-9--joint-007-cut` | a dotted version slugs to `007` | deferred anchor defect 2 |
| 567, 568 + 5 use sites | both `TODAY.md` defs re-pointed at the renamed headings, ref ids renamed, visible link text updated | the headings dropped the `examples/fakeshop/` prefix | dead link definitions |
| 81, 83, 194, 298, 457, 543, 588, 593 | 8 uses of 3 dead `#"…"` substring anchors rewritten to cite the file without a substring | `#"Migration to a"` cites a line this card removes; `#"strawberry.Schema(query=Query"` no longer exists in `GOAL.md` or the fakeshop schema | **not in the catalog** — found by auditing every substring anchor |
| 201, 203, 52, 466, 471, 530, 541 | `docs/spec-025-…` and `docs/spec-025-…-terms.csv` prose paths → the archived `docs/SPECS/` and `docs/SPECS/appx/` paths; Decision 1's opener restated so filename-is-canonical, directory-is-not | Decision 1's own rule, applied to Decision 1 | **not in the catalog** |
| 45 | Slice 3 audit-only bullet's "`grep -n \"BigInt\" examples/fakeshop/` currently returns no matches" replaced by the structural reason | the grep returns many matches now | **not in the catalog** — the other half of D8 |
| 69-71 | `## Current state` given a one-line framing as the `0.0.6` baseline | an unframed "Current state" reads as a claim about `HEAD` | **not in the catalog** |
| 52, 466 | the "the CSV completeness callout becomes stale; this slice removes it" clauses deleted | the callout they promise to remove does not exist | **not in the catalog** |
| link definitions | added `[exceptions]`, `[build-tree]`; renamed the two `[today-…]` ids | new citations, and the renamed `TODAY.md` slugs | — |

Changes to `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`:

| Change | Reason |
|---|---|
| all 13 `### D<n>` entries gained a closing `**Resolved in the spec (Slice 2).**` paragraph naming the actual edits | `BUILD.md` requires the rationale to carry every change a Decision underwent; an entry that records only the drift leaves the next reader unable to tell whether it was acted on |
| `## Provenance of this record`: justification bullets `37 (36 moved, 1 retained)` → `38 (37 moved, 1 retained)`, with `[3, 8, 3, 4, 4, 3, 5, 4, 4]` recorded as the derivation | wrong at HEAD; Slice 1's own correction landed only in its artifact |
| `## Provenance of this record`: the "Re-relativization" bullet now says the reconciliation slice re-pointed the moved text's venv citations | the bullet said they were deliberately left dead, which stopped being true when D12 was discharged |
| 6 moved-text `.venv/lib/python3.10/` citations → `python3.14` | dead paths in a durable record |
| Decision 8's moved inline `](../../../CHANGELOG.md)` → reference-style `[changelog]`, `#"## [Unreleased]"` anchor dropped | `START.md` requires reference-style; the heading no longer exists |
| header paragraph re-tensed (the reconciliation has run); `## Verification performed by this pass` retitled `… by the rationale move (Slice 1)`; new `## Verification performed by the spec reconciliation (Slice 2)` section | an append-only file cannot have two sections called "this pass" |
| closing bullet: "two inherited figures were wrong" → three, naming the justification-bullet count | it is now three |
| 4 ref ids added (`[build-tree]`, `[spec-025-goals]`, `[spec-025-key-glossary]`, `[spec-025-out-of-scope]`); `docs/SPECS/` group re-sorted by id | the resolutions cite them |

### Notes for Worker 1 (spec reconciliation)

Deferred-work catalog for the final gate. Nothing here is actionable inside this cycle's scope fence (spec files and `.py` source only).

- **`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`** rows for `DjangoFileType` / `DjangoImageType` cite `TODO-ALPHA-028-0.0.11`, which shipped as `DONE-037-0.0.11`. Carried from Slice 1; still true; the CSV is not a spec file.
- **The `TODO-ALPHA-051-0.0.15` KANBAN bullet** still describes six `[spec-013]` / `[spec-011]` occurrences in this spec. `grep -c` reports **0** for both — the label rot was already repaired, so the KANBAN description is what is stale. Worker 0 verified this as NOT a defect in the spec; the correction belongs to whoever owns that card.
- **The spec's pinned KANBAN Done body does not exist in `KANBAN.md`.** `KANBAN.md` is rendered from the fakeshop kanban DB, and the live `DONE-025-0.0.7` card carries a generated body (priority / status / labels / glossary-terms table / package files / a one-line `#### Note`), not the long past-tense paragraph the spec pins in `## Doc updates`. This is a real divergence and it is **not** in the D1-D13 catalog. It is not fixable from the spec side alone: the fix is either a DB edit plus a regenerate (fenced, and DB-backed per `AGENTS.md`) or a decision that a spec should not pin a verbatim body for a generated file at all. That second reading is the interesting one and belongs to the maintainer, because it applies to every spec in the corpus, not just this one. The spec's own `Definition of done` item 15 was narrowed this pass to pin the **body** rather than the card number, which is as far as the spec side can go.
- **The quoted `CHANGELOG.md` `### Added` body in `## Doc updates` is missing a trailing clause** that the landed bullet carries: `Tracked as [025-warning_free_scalar_registration_via_strawberryconfigscalar_map-0.0.7][card-…] in [\`KANBAN.md\`][kanban].` That clause is appended by the kanban tooling, not authored, so the spec quoting the authored text is defensible — but a reader diffing the two will find it. Left as-is deliberately; recorded so the finding is not rediscovered as a defect.
- **`CHANGELOG.md`'s whole `## [0.0.7]` section labels every card by its pre-renumber number** (the `047-warning_free_scalar_registration_via_strawberryconfigscalar_map-0.0.7` label is this card, 3 occurrences). Already catalogued on `TODO-ALPHA-051-0.0.15` with a measured population; noted here only because this cycle read the section.

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
