# Build: Final test-run gate — spec-021 residual-completion cycle

Spec reference: `docs/SPECS/spec-021-apps-0_0_7.md` (65,342 bytes at this gate's read)
Rationale reference: `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` (85,169 bytes at this gate's read)
Plan reference: `docs/builder/build-021-apps-0_0_7.md` `## Verified findings` and `## Pre-flight record`
Prior artifacts: `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md` (`final-accepted`), `docs/builder/bld-review-2-db_backed_doc_reconciliation.md` (`final-accepted`), `docs/builder/bld-integration.md` (`final-accepted`)
Status: final-accepted

## Why this artifact has no Worker 2 or Worker 3 section

`docs/builder/ARTIFACT.md`'s template carries `## Build report (Worker 2)`, `## Review (Worker 3)` and their subsections because the ordinary unit of work is a slice with a builder and a reviewer. **The final test-run gate has neither.** `docs/builder/BUILD.md` `## Final test-run gate` and `docs/builder/worker-1.md` `## Final test-run gate` both describe it as a Worker 1 pass end to end: Worker 1 runs the commands, records each result, writes the deferred-work catalog, and sets `Status:`. Nothing in it is dispatched, so there is no diff for a builder to produce and no diff for a reviewer to accept. The gate's own outputs are recorded under `## Gate report (Worker 1)` instead, and `docs/builder/bld-003-final.md` in this repo is the worked precedent for that shape.

The gate's isolation guarantee is unchanged: this is a fresh Worker 1 invocation with no memory of the three passes it audits. The artifacts and the working-tree diff are the record.

## Plan (Worker 1)

### DRY analysis

Not applicable in the code sense, and recorded rather than omitted — this is the fifth recording of the same reason in this cycle. **No cohort wrote package `.py`.** The plan's ownership partition assigns `django_strawberry_framework/**` to no cohort; the only `.py` byte either cohort moved is one comment block in `tests/test_apps.py`. Re-verified here rather than taken on report: `git diff HEAD --stat -- tests/test_apps.py` is `1 file changed, 6 insertions(+), 7 deletions(-)`, and every `django_strawberry_framework/` path in the diff belongs to a concurrent session (below). There is no helper, constant, literal or import this cycle authored to duplicate.

The cross-surface DRY work — the spec/rationale move-vs-copy scan at 0.80 and 0.75, and the four-surface subject separation — was performed and recorded by `bld-integration.md`. The gate does not repeat it; it confirms the artifact carrying it is `final-accepted` and that neither file has moved since (both byte counts above match the figures `bld-integration.md` published, and the rationale's four self-reported figures still reproduce — see `### Cross-artifact read`).

### Implementation steps

1. Read the Worker 1 column of `BUILD.md` `## Required reading per worker` in full, plus `worker-1.md`'s final-test-run-gate duties and my own memory file.
2. Run every command in `BUILD.md` `## Final test-run gate`, in that order, from the repo root, recording the exact command and its real exit status.
3. Grade every failure against this cycle's own file set before calling it this cycle's failure.
4. Record the floor-verification declaration and its reason; build no floor venv.
5. Confirm read-only that `docs/GLOSSARY.md` and `KANBAN.md` still carry R2's landed lines and that `GlossaryTerm` pk 448 / `CardItem` pk 750 hold their intended text. Run no generator.
6. Re-derive every population in the deferred-work catalog at the moment of writing it, and prefer a corpus rule to a bare digit wherever the corpus is under concurrent edit.

### Test additions / updates

None, and none is owed. This pass writes exactly one file, `docs/builder/bld-final.md`, and no `.py` anywhere. The suite is executed as the gate's first command, not extended.

### Implementation discretion items

- Whether a gate failure is this cycle's or a baseline exception — decided per failure by whether the failing path is in this cycle's file set, with the evidence recorded either way.
- Whether the catalog carries a digit or a corpus rule — decided per item by whether the corpus is under concurrent edit.

### Dispatched findings checklist

The gate has no dispatched findings. The boxes below are `BUILD.md` `## Final test-run gate`'s own commands plus the two obligations `worker-1.md` adds.

- [x] `uv run pytest --no-cov` — run, **one failure**, graded a baseline exception with evidence.
- [x] `uv run python examples/fakeshop/manage.py check` — pass.
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — pass, no migration reported.
- [x] `uv run ruff format --check .` — pass, read-only, no `--fix` in any form.
- [x] `uv run ruff check .` — pass, read-only.
- [x] `git diff --check` — pass.
- [x] Floor verification — scope `none`, declaration and reason recorded; no floor venv built.
- [x] Generated-doc integrity, read-only, no generator run.
- [x] `### Deferred work catalog`, every population re-derived at write time.

---

## Gate report (Worker 1)

### Gate commands, in `BUILD.md` order

Every command run from the repo root in the shared `.venv`. **No `--cov*` flag in any form, anywhere in this pass.** No `git stash`, `checkout`, `restore`, `merge-base --is-ancestor`, commit or branch.

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **`1 failed, 6177 passed, 40 skipped` in 173.33s, exit `1`.** Baseline exception — see below. |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS.** `System check identified no issues (0 silenced).`, exit `0`. |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS.** `No changes detected`, exit `0`. No migration reported, which is what the plan predicts: this cycle wrote two DB *rows* through the ORM and no model change. |
| 4 | `uv run ruff format --check .` | **PASS.** `424 files already formatted`, exit `0`. (Emits the standing `COM812`-with-formatter warning, which is configuration, not a finding.) |
| 5 | `uv run ruff check .` | **PASS.** `All checks passed!`, exit `0`. |
| 6 | `git diff --check` | **PASS.** No output, exit `0`. Also run in its staged form, `git diff --cached --check` — no output, exit `0` — because the tree carries a staged deletion `git diff --check` alone does not see. |

**Exit codes were captured directly, not inferred from a pipeline.** My first sweep piped `pytest` through `tail`, which reports `tail`'s status; the run was repeated without the pipe to read `pytest`'s own exit code. A pipeline's exit status is not the command's — recording it as one is the same class of instrument error this cycle kept producing.

The `check_spec_glossary` gate the dispatch owes separately: `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-021-apps-0_0_7.md` -> `OK: 12 terms - all have glossary entries and at least one spec link.`, **exit `0`**. Matches the plan's pre-flight step 6 reading. `uv run python scripts/check_trailing_commas.py --check` over both spec files -> exit `0`.

### The one `pytest` failure is a baseline exception, with its evidence

```
FAILED tests/utils/test_write_values.py::test_form_and_serializer_decode_walks_share_field_handlers
E   AttributeError: module 'django_strawberry_framework.mutations.resolvers' has no attribute 'decode_field_handlers'
tests/utils/test_write_values.py:407
```

Graded against this cycle's file set before being graded at all. **Neither the failing test file nor the module it asserts against is in this cycle's file set**, which is `docs/SPECS/spec-021-apps-0_0_7.md`, `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, `tests/test_apps.py` and the five `docs/builder/` files.

Four commands establish it, and the first is decisive:

| probe | result |
|---|---|
| `git show HEAD:tests/utils/test_write_values.py \| grep -c 'mutation_resolvers.decode_field_handlers'` | **0** — the failing assertion does not exist at `HEAD` |
| `grep -c 'mutation_resolvers.decode_field_handlers' tests/utils/test_write_values.py` | **1** — it exists only in the working tree |
| `git show HEAD:django_strawberry_framework/mutations/resolvers.py \| grep -c 'decode_field_handlers'` / same on the working copy | **0** / **0** — the symbol is absent from that module at `HEAD` *and* now |
| `git status --short -- tests/utils/test_write_values.py django_strawberry_framework/mutations/resolvers.py` | both `M`, both in the concurrent session's 7-module + 5-test-module refactor |

So a concurrent session's **uncommitted** work added an assertion naming a symbol its own in-flight module does not yet export. The failure is reproducible (it appeared identically on both full runs, 70.32s and 173.33s, with the same single test), it is not order-dependent, and it is not this cycle's: `uv run pytest tests/test_apps.py --no-cov` -> **8 passed** in 1.42s.

**Not fixed, not reverted, not tidied** (`AGENTS.md` rule 34). Recorded so the maintainer sees it, and so the next cycle does not inherit it as a mystery.

The plan's preamble records the concurrent-session baseline in `### Baseline-dirty, out-of-scope` and `### Concurrent-writable tracked binary / generated files` but names no `pytest`-level exception, because at plan time this refactor had not yet reached a state that fails. That is drift in the baseline, not a gap in the plan: the dispatch's rule — grade by whether the failing file is in this cycle's diff — is what decides it, and it decides cleanly.

### Steps 4-6 are repo-wide and passed anyway

Worth stating because the dispatch anticipates the opposite: the concurrent session's 12 dirty `.py` files are ruff-clean and format-clean as they stand, so no baseline exception was needed for steps 4, 5 or 6. Had one been needed, the read-only form is what makes it recordable — a repo-wide `ruff --fix` would have swept another session's WIP into this cycle's diff, which is precisely why those steps are read-only.

### Floor verification

**Scope `none`, as declared.** `docs/builder/build-021-apps-0_0_7.md` `## Declarations` reads: "**Floor-verification scope** — none. No cohort touches a Django / Strawberry / channels integration seam (`BUILD.md` `### When it is required`)."

The declaration holds at the gate, re-derived rather than accepted: no cohort wrote package source at all this cycle, so none of the seams `BUILD.md` `### When it is required` enumerates — request/response handling, view or ASGI plumbing, upload or body parsing, the session/auth surface, queryset or expression compilation, schema and type construction against Strawberry internals, consumer or middleware wiring — was touched. The cycle's product is two Markdown files, two SQLite rows, three regenerated docs and one comment block.

**No floor venv was built, and none was owed.** `BUILD.md` `## Floor verification` states the floor as "Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**", and that section is quoted here rather than restated from memory, since it is the single canonical statement of those numbers. The same section's other standing rule applies to the green sweep above: the shared `.venv` is **not** the floor, so command 1's result is a top-of-range reading and licenses no floor claim. `worker-1.md`'s backstop obligation — confirm a declared scope was actually run — is vacuous here and is recorded as vacuous rather than silently skipped.

### Generated-doc integrity (read-only)

**No generator was run.** That is a write this pass does not own; `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html` and `examples/fakeshop/db.sqlite3` carry R2's landed output alongside a concurrent cohort's. Verified by reading the two rows through the ORM and the rendered files off disk.

| surface | probe | result |
|---|---|---|
| `GlossaryTerm` pk 448 | `anchor` / `status_text` / `len(body)` | `django-appconfig` / `` shipped (`0.0.7`) `` / **1758** |
| | `body.count('dependency order')` / `body.count('in this order')` / `body.count('three defensive')` | **0** / **1** / **1** |
| | `body.count('_strawberry_patches')` / `body.count('_cross_web_patches')` / `body.count('function-local')` | **1** / **1** / **1** |
| `CardItem` pk 750 | `card_id` / `section.key` / `is_complete` / `len(text)` | **43** / `note` / `True` / **287** |
| | `text.count('0.0.11')` / `text.count('0.0.10')` / `text.count("this card's own diff")` | **1** / **0** / **1** |
| `docs/GLOSSARY.md` | `## Django `AppConfig`` heading | present at line **526**; the entry renders pk 448's body, `in this order` **1**, `_cross_web_patches` **1**, `three defensive` **1**, `dependency order` **0** |
| `KANBAN.md` | the `DONE-021-0.0.7` `#### Note` bullet | present at line **4053**, carrying the `0.0.11` wording once |
| `KANBAN.html` | `grep -c 'appliers followed at'` | **1** |
| `tests/test_apps.py` | `grep -c 'spec-017'` / `grep -c 'spec-021'` / `grep -c '^def test_'` | **0** / **0** / **8** |

**Every line R2 landed is still present, and no regenerate is owed.** The failure mode this check exists to catch is a concurrent regenerate silently reverting a hand-edit; all readings above were taken after the concurrent session's `GlossaryTerm` pk 504 rewrite, and nothing was reverted. **Nothing routes back to R2.**

### Cross-artifact read

All three prior artifacts read in full, in order, before this gate ran, and re-checked at close:

- `bld-review-1-rationale_and_spec_reconciliation.md` — `Status: final-accepted` (header line 6, closing line 1185).
- `bld-review-2-db_backed_doc_reconciliation.md` — `Status: final-accepted` (header line 5, closing line 798). Line 798 is the file's last line; the section R2's final verification removed is gone and R1's own copy is intact, which the integration pass proved and I did not re-prove.
- `bld-integration.md` — `Status: final-accepted` (line 7).

The rationale's four self-reported byte figures, which R1 and the integration pass each had to re-converge after their own edits, **still reproduce at the gate**: `wc -c` gives spec **65,342** and rationale **85,169**, and the rationale's own text carries `65,342` once, `85,169` once, `32,176` twice (by the design that paragraph states) and `52,993` once. Nothing this pass did moved them, because this pass edited neither file.

**Spec status-line re-verification** (owed by every Worker 1 spawn, `worker-1.md` `## Spec status-line re-verification`): `docs/SPECS/spec-021-apps-0_0_7.md` line 4 reads `` Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-021-0.0.7`. `` — correct for a shipped, archived card, and the resolution of the plan's F3.

### Staged-anchor sweep — re-measured at the gate

- `grep -rEn 'TODO\(spec-021|TODO-(ALPHA|BETA|STABLE)-021' .` (`.git` and `.venv` excluded) -> **0 hits**.
- `grep -rEn 'TODO\(spec-017|TODO-(ALPHA|BETA|STABLE)-017' .` (this card's **pre-renumber** number) -> **3 hits, all in one file, none an anchor**: `docs/builder/DONE/build-017-deferred_scalars-0_0_6.md` lines 54, 76 and 139. That file is the completed build plan of `spec-017-deferred_scalars-0_0_6.md`, an unrelated `0.0.6` card, and all three hits are the two patterns **quoted as patterns inside prose** — lines 54 and 139 are that cycle's own record that *its* sweep returned zero. It is also a concurrent session's untracked file under `AGENTS.md` rule 34.

**No anchor in shipped source, tests or comments names this build's spec or card under either number.** Same result as the integration pass, re-derived not copied.

### Working tree at the gate's close

`git status --short | wc -l` -> **32** before this artifact was written, **33** after, since the file stating the count is itself a path. Both readings are stated because a status count that omits the file stating it is the self-referential defect this cycle's memory names.

- **Mine, and the only file this pass wrote:** `?? docs/builder/bld-final.md`.
- **This cycle's, landed and audited by prior passes:** `docs/SPECS/spec-021-apps-0_0_7.md`, `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, `tests/test_apps.py`, `docs/builder/build-021-apps-0_0_7.md`, `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md`, `docs/builder/bld-review-2-db_backed_doc_reconciliation.md`, `docs/builder/bld-integration.md`.
- **Concurrent-session work — recorded, never edited, never reverted, never staged** (`AGENTS.md` rule 34): 7 package modules under a refactor (`auth/mutations.py`, `mutations/inputs.py`, `mutations/resolvers.py`, `mutations/sets.py`, `rest_framework/resolvers.py`, `utils/inputs.py`, `utils/write_values.py`) and 5 test modules (`tests/auth/test_mutations.py`, `tests/mutations/test_inputs.py`, `tests/mutations/test_resolvers.py`, `tests/mutations/test_sets.py`, `tests/utils/test_write_values.py`); `docs/SPECS/spec-022-export_schema-0_0_7.md`, `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`, `docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`, `docs/feedback.md`; `docs/builder/build-020-list_field-0_0_7.md` (staged deleted) with `docs/builder/DONE/build-020-list_field-0_0_7.md` (untracked); and the parallel `spec-022` cycle's `build-022-export_schema-0_0_7.md`, `bld-review-1-spec_022_reconciliation.md`, `bld-review-2-spec_022_glossary_body.md`.

**Drift from the plan's declared baseline, re-derived rather than copied:** `docs/builder/bld-003-final.md` is **not** dirty at this gate (`git status --short -- docs/builder/bld-003-final.md` is empty), so the plan's `### Baseline-dirty, out-of-scope` third entry no longer describes the tree. The integration pass reported the same drift; I re-measured rather than inheriting it.

### Deferred work catalog

The next spec author's reading list. Drawn from the two cohort artifacts' `### Notes for Worker 1` / `What looks solid` / `### Deferred work catalog` sections and `bld-integration.md`'s consolidated list. **`bld-integration.md`'s list was not copied — every population below was re-derived by me at this artifact's write time**, with the corpus named, the instrument stated, and a re-run instruction on the drift-sensitive ones. Where my reading disagrees with a published one, both are shown and the digit is not carried forward.

1. **`[spec-NNN]` ref-id residue: definition lines whose ref-id number and target basename disagree.** Source: `bld-review-1-…md` `### Deferred work catalog` item 2, consolidated at `bld-integration.md` item 1. Licensing clause: none needed — the carrier files are outside every cohort's writable set. The residue is **definitions**, never token hits: `spec-016-fieldmeta_consolidation-0_0_6.md` and `spec-017-deferred_scalars-0_0_6.md` are real current filenames, so a raw token grep massively overstates it.

   **Corpus rule, not a digit.** Over every `*.md` under `docs/SPECS/` (including `appx/`) plus `KANBAN.md`, take each line matching `^\[spec-(\d{3})\]:\s*(\S+)` whose target basename matches `spec-(\d{3})-`; the definition disagrees when the two three-digit numbers differ.

   Two readings taken now, both stated because they answer different questions:
   - **Whole class** (any `spec-NNN` ref-id): **252** definitions, **224** agree, **28** disagree — `spec-023` 6, `spec-025` 8, `spec-027` 9, `spec-054` 1, `KANBAN.md` 4.
   - **The 016/017 class the cycle tracked** (ref-id restricted to `spec-016` or `spec-017`): **12** definitions, **5** agree, **7** disagree — `spec-023` 2, `spec-025` 2, `spec-027` 2, `KANBAN.md` 1.

   `bld-integration.md` published `24 definitions / 16 agree / 8 disagree — spec-023 3, spec-025 2, spec-027 2, KANBAN.md 1`. **That figure does not reproduce under either rule above**; the per-file decomposition matches mine except `spec-023` (3 vs 2), and the totals match neither. The corpus is under concurrent edit and the extractors differ, which is exactly why the rule and not the digit is what carries forward. **Re-run the rule; do not copy any of these numbers.**

   **One instance the 016/017 framing hides**, surfaced by the wider rule and new to this catalog: `docs/SPECS/spec-054-fieldset-0_1_1.md:948` reads `[spec-054]: spec-055-search_fields-0_1_2.md` — the same defect, a different pair, outside the renumber window the cycle was looking at. The class is broader than its name.

2. **`spec-022` asserted the claim R1 retired, about this very spec.** Source: `bld-review-1-…md` `### Deferred work catalog` item 3; `bld-integration.md` item 2. Licensing clause: none — `spec-022` is outside every cohort's writable set in either state. **HIGHLY DRIFT-SENSITIVE, re-derived now:** `grep -c 'ready()' docs/SPECS/spec-022-export_schema-0_0_7.md` -> **0** in the working tree, and `git show 51eb47ba:docs/SPECS/spec-022-export_schema-0_0_7.md | grep -c 'ready()'` -> **4** at the last committed state. The concurrent `spec-022` rationale-extraction round removed all four and **that work is uncommitted**. **Drop this item if that session's work commits; re-open it if the work is reverted.** Corpus: one file, under active concurrent rewrite.

3. **Non-shipped `Status:` lines on shipped cards** — the plan's F3 defect class on specs this cycle does not own. Source: `bld-review-1-…md` `### Deferred work catalog` item 4; `bld-integration.md` item 3. **Re-derived now by reading each file's `Status:` line, not by sweeping**, because the pattern is not uniform:
   - `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` — "Only the final test-run gate remains (workflow gate, not a slice)." on a shipped card. **The only open instance.** The file is clean, so this is `HEAD`'s state and is not drift-sensitive.
   - `docs/SPECS/spec-022-export_schema-0_0_7.md` — now reads shipped-and-archived, under the concurrent session's **uncommitted** work. Drift-sensitive; re-check.
   - `docs/SPECS/spec-023-multi_db-0_0_7.md` — already correct.

4. **The `AGENTS.md` paraphrase-citation convention across `docs/SPECS/`.** Source: `bld-review-1-…md` `### Escalation resolved — the `AGENTS.md` citation class`, resolved there as a repo-wide spec-authoring call, carried at `bld-integration.md` item 4. **Publish the corpus rule; never copy a digit.**

   Rule: a `` `AGENTS.md` #"substring" `` citation *resolves* when the substring occurs verbatim in `AGENTS.md`. Two readings taken now, over every `*.md` under `docs/SPECS/`:
   - strict form (backticked `` `AGENTS.md` `` immediately followed by `#"…"`): **3** files, **9** occurrences, **3** distinct substrings, **1** resolving.
   - loose form (`AGENTS.md` with or without backticks, whitespace tolerated before `#`): **4** files (`spec-020` 1, `spec-021` 1, `spec-023` 7, `spec-025` 11), **20** occurrences, **7** distinct substrings, **1** resolving.

   Six readings now exist inside one week and no two agree: R1 pass 2 `25 / 101 / 22 / 0`, its Worker 3 `23 / 109 / 15 / 2`, R1 pass 3 `27 / 111 / 16 / 3`, its Worker 3 `28 / 119 / 16 / 2`, R1's final verification `28 / 122 / 16 / 2`, and mine above. The instruments differ in what they treat as a citation and the corpus moves under concurrent edit while it is counted.

   **The load-bearing finding is qualitative and must be carried: the class is not uniformly broken.** At least one distinct substring — `Test through real usage` — occurs in `AGENTS.md` verbatim, so **"not one of them resolves" must not be restated.** The prior claim of *two* verbatim resolvers does not reproduce under either of my rules; the safe floor is one, and the retraction it supports is unaffected. If a future catalog wants a number, it re-runs its own rule and timestamps the reading.

5. **No glossary term covers the Strawberry or `cross_web` upstream patches.** Source: `bld-review-2-…md` `### Deferred work catalog — R2's` item 1 and its `### Implementation discretion items`, endorsed by both R2 review passes; `bld-integration.md` item 5. Licensing clause: none — no dispatched finding asks for the term, and `spec-021` `## Doc updates` scopes the glossary work to the `Django AppConfig` entry. **Candidate, not built**: a new term needs an index row, a category membership and a `check_spec_glossary` story.

   **Corpus rule, because a concurrent session is writing this DB:** the term is missing for as long as no `GlossaryTerm.body` outside pk 448 names `_strawberry_patches` or `_cross_web_patches`. Reading taken now through the ORM: across **142** `GlossaryTerm` rows the only body naming either module is pk **448** itself, and **0** anchors contain `patch`. Re-run that probe at write time.

   The `**See also:**` line was deliberately not widened, and a future author should not "fix" it: `#utf-8-wire-contract` and `#request-body-cap` each state in their own bodies that they are *not* upstream-bug patches, so pointing at them would create a cross-reference the target contradicts.

6. **Repo-wide instrument note: "version in `pyproject.toml` at the work commit" is not "shipping release".** Source: `bld-review-2-…md` `### Notes for Worker 1` item 3 (endorsed twice) and its final verification item 2; `bld-integration.md` item 6. The bump lands at the cut, so `git show <commit>:pyproject.toml` reports the **previous** release. Read releases off **tag content** (`git show <tag>:<path>`) or the `CHANGELOG.md` date.

   **`git merge-base --is-ancestor` is not the substitute.** Concurrent sessions rewrite this branch, and it answers `NO` for `c7cb5f5c` against tags whose content plainly contains the change. It was not used anywhere in this pass.

   The class produced **five** wrong or unsupported readings in this cycle, enumerated rather than counted from a description: the plan's `### F9` `c7cb5f5c` row (fixed by Worker 0), the card note's `0.0.10` (fixed by R2 pass 2), R2's release-facts evidence cell and its dispatch-test row's `0.0.13` (both fixed by R2's final verification), and the spec's KANBAN Done-body prescription attributing the three-applier `ready()` to this card (fixed by the integration pass). **Nothing is open**; the note carries the instrument rule, not the digits.

7. **`CHANGELOG.md`'s `[0.0.7]` one-applier entry — RESOLVED-NOT-A-DEFECT, not deferred.** Source: `docs/builder/build-021-apps-0_0_7.md` `### F9 — DOES NOT HOLD`, `bld-review-2-…md` `### F9 is not this cohort's work`, `bld-integration.md` item 7. R1's own catalog carried it as an open item; R2 re-graded it, the integration pass confirmed the re-grade, and **I confirm it a third time on my own instruments, off tag content**: the `0.0.7` tag carries `ready()` with only the Django applier, so an entry naming one applier is accurate *as history* and "correcting" it to three would falsify the changelog. The Strawberry and `cross_web` appliers arrive at `0.0.11` and the dispatch test at `0.0.14`. `AGENTS.md` #"No CHANGELOG.md updates unless told" forbids the edit independently, and `git diff HEAD --stat -- CHANGELOG.md` is empty, so the file is untouched by this cycle. **Recorded here so the next author does not re-open it.**

   A **separable, still-open** defect in the same file is the pre-renumber card labelling. Re-derived now: `grep -oE '01[0-9]-[a-z_0-9]+-0\.0\.[0-9]+' CHANGELOG.md` -> **13 occurrences across 8 distinct labels** (`012-…` 1, `013-…` 1, `014-…` 2, `015-…` 1, `016-…` 1, `017-appspy_and_django_app_config-0.0.7` 1, `018-…` 5, `019-…` 1), of which this card's is one. Corpus: `CHANGELOG.md`, clean at `HEAD`, **not** drift-sensitive. **Do not conflate that figure with the differently-sized one a `KANBAN.md` note records for a different population in a different file.**

8. **Decision 6's four-card bundle vs `KANBAN.md`'s seven `0.0.7` cards — NO ACTION, closed.** Source: `bld-review-1-…md` `### Deferred work catalog` item 6; `bld-integration.md` item 8. The Decision states the WIP set at authoring time excluding the already-shipped `DONE-020-0.0.7`; `DONE-024` and `DONE-026` joined the release afterwards. Its subject is the version-bump policy, which no later card joining the release affects, and rewriting the bundle would make the Decision assert something it never decided. Endorsed four times across R1 and once at integration; recorded so it is not re-opened a sixth time.

**Post-gate execution note (2026-08-18, maintainer-directed, after `final-accepted`).** The maintainer instructed Worker 0 to execute three catalog items directly in spec files, leaving DB-backed and `CHANGELOG.md` surfaces untouched. (i) Item 1's spec-file half is done: every `[spec-NNN]` definition under `docs/SPECS/` (`appx/` included) whose ref-id number disagreed with its target basename was renamed together with all its uses and derived suffixed labels (`spec-023-multi_db-0_0_7.md`, `spec-025-scalar_map_helper-0_0_7.md`, `spec-027-filters-0_0_8.md`, `spec-054-fieldset-0_1_1.md`); `spec-032-full_relay-0_0_9.md`'s `[spec-011]` was repointed to `spec-015` (its prose names `Meta.interfaces` rejection). `appx/spec-005-django_type_contract-0_0_3-rationale.md`'s `[spec-011]` was verified CORRECT and left — its prose really does mean the placeholder-cleanup spec, so the catalog's "two files define it wrongly" claim held for only one of the two. The 4 `KANBAN.md` definitions remain (DB-generated, out of the authorized surface). (ii) Item 3's open instance is closed: `spec-025`'s `Status:` line now reads shipped, on `spec-023`'s wording precedent. (iii) Item 4's class is repaired repo-wide: every non-resolving `AGENTS.md` `#"…"` anchor under `docs/SPECS/` (~124 occurrences across 27 files — far larger than any of the six prior readings, whose instruments all missed the reference-link and em-dash citation spellings) was retargeted to verbatim current `AGENTS.md` text, stale parenthetical requotes included; postcondition re-run to zero non-resolving occurrences. Item 5 (glossary term) and the `CHANGELOG.md` label residue stay deferred — DB and `CHANGELOG.md` surfaces were not authorized.

**Explicitly NOT in this catalog, and why:**

- **F8** — `tests/test_apps.py`'s `spec-017` provenance comment. It is R2's **work item**, it landed, and its tick is audited in R2's final verification, re-confirmed at integration and re-confirmed here (`grep -c 'spec-017' tests/test_apps.py` -> **0**). Both cohorts' catalogs say the same; do not double-count it.
- **The "in dependency order" gloss.** Escalated by R2's Worker 3, resolved by R2's final verification at all three sites, re-verified at integration and re-verified here at every surface (`docs/GLOSSARY.md` **0**, `KANBAN.md` **0**, `KANBAN.html` **0**, `tests/test_apps.py` **0**, `GlossaryTerm` pk 448 body **0**).
- **The misfiled R1 build-report section in R2's artifact.** Removed by R2's final verification after a subset proof; re-verified at integration.
- **The integration pass's own two findings** — the KANBAN Done-body and `CHANGELOG.md` prescriptions in the spec's `## Doc updates`. Fixed there, not deferred.
- **The `pytest` failure in `tests/utils/test_write_values.py`.** It belongs to a concurrent session's uncommitted refactor, not to this cycle, and it is recorded above as a baseline exception rather than as deferred work this build owes.

### Every figure in this artifact, with the command that produced it

Stated because this cycle's standing defect is a claim that reads as measured and was not. Each figure above was measured at write time and re-measured after the artifact's last edit.

| figure | command |
|---|---|
| `1 failed, 6177 passed, 40 skipped`, exit `1` | `uv run pytest --no-cov -q`, exit code read directly, not through a pipe |
| `8 passed` for this cycle's only `.py` | `uv run pytest tests/test_apps.py --no-cov -q` |
| `424 files already formatted` | `uv run ruff format --check .` |
| `12 terms`, exit 0 | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-021-apps-0_0_7.md` |
| spec 65,342 / rationale 85,169 bytes | `wc -c` on both files |
| pk 448 body 1758, pk 750 text 287, 142 `GlossaryTerm` rows | ORM reads under `DJANGO_SETTINGS_MODULE=config.settings` |
| `docs/GLOSSARY.md` heading line 526, `KANBAN.md` note line 4053 | `grep -n` |
| 8 test functions, 0 `spec-017`, 0 `spec-021` in `tests/test_apps.py` | `grep -c` |
| 252 / 224 / 28 and 12 / 5 / 7 ref-id definitions | the `^\[spec-(\d{3})\]:` rule stated in catalog item 1 |
| 3 / 9 / 3 / 1 and 4 / 20 / 7 / 1 `AGENTS.md` citations | the two rules stated in catalog item 4 |
| 13 occurrences / 8 distinct `CHANGELOG.md` labels | `grep -oE '01[0-9]-[a-z_0-9]+-0\.0\.[0-9]+' CHANGELOG.md \| sort \| uniq -c` |
| 0 / 3 staged-anchor hits | the two `grep -rEn` sweeps in `### Staged-anchor sweep` |
| 32 -> 33 paths | `git status --short \| wc -l`, before and after this artifact |

---

## Final verification (Worker 1)

### Summary

**The gate passed.** Five of the six commands are clean: `manage.py check`, `makemigrations --check --dry-run`, `ruff format --check .`, `ruff check .` and `git diff --check` (in both its unstaged and staged forms) all exit 0, and `check_spec_glossary` reports `OK: 12 terms`, exit 0. `uv run pytest --no-cov` reports `1 failed, 6177 passed, 40 skipped` and exits 1; the single failure is `tests/utils/test_write_values.py::test_form_and_serializer_decode_walks_share_field_handlers`, whose failing assertion **does not exist at `HEAD`** and whose file and target module are both dirty under a concurrent session's uncommitted refactor. Neither path is in this cycle's file set. It is a baseline exception, recorded with its evidence, not fixed and not reverted (`AGENTS.md` rule 34). This cycle's only `.py` diff — one comment block in `tests/test_apps.py` — runs 8 passed on its own.

Floor verification was declared `none` and correctly owed nothing: no cohort wrote package source at all, so no Django / Strawberry / channels seam was touched. No floor venv was built. The green sweep in the shared `.venv` is a top-of-range reading and licenses no floor claim.

The generated-doc check, run read-only and without invoking a generator, confirms every line R2 landed: `GlossaryTerm` pk 448 and `CardItem` pk 750 hold their intended text, and `docs/GLOSSARY.md`, `KANBAN.md` and `KANBAN.html` still render it after a concurrent cohort's mid-cycle regenerate. **No regenerate is owed and nothing routes back to R2.**

The deferred-work catalog carries eight items plus five explicit non-items. It was re-derived rather than copied, and doing so mattered: the ref-id residue figure `bld-integration.md` published reproduces under neither of my two rules, so the item now publishes the corpus rule and two readings instead of a digit, and the wider rule surfaced one instance of the same defect class (`spec-054` -> `spec-055`) that the 016/017 framing had hidden. The `AGENTS.md` citation item likewise publishes rules and readings; six sweeps now disagree, and the only claim that survives all of them is the qualitative one.

### Spec changes made (Worker 1 only)

**None.** No gate command failed in a way whose fix is a spec edit, and no gate check surfaced a false claim in either spec file. `docs/SPECS/spec-021-apps-0_0_7.md` and `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` are byte-identical to the state `bld-integration.md` closed on — `wc -c` gives 65,342 and 85,169, matching that artifact's header figures, and the rationale's four self-reported figures still reproduce inside it. This pass wrote exactly one file, `docs/builder/bld-final.md`.

### Final status

`final-accepted`.

Every command in `BUILD.md` `## Final test-run gate` was run from the repo root and its real result recorded, with the one failure graded against this cycle's file set before being graded at all. The floor-verification declaration of `none` holds at the gate and is recorded as vacuous rather than skipped. The DB-backed doc obligation is discharged read-only, with no generator run and nothing routed back. The staged-anchor sweep returns zero anchors for this build's card under either of its numbers. The deferred-work catalog is re-derived, corpus-ruled where the corpus moves, and carries the one item — F9 — that must be read as resolved-not-a-defect rather than as open.

The gate closes the cycle. Worker 0 marks the final checkbox; the maintainer's review is the next touch point.

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
