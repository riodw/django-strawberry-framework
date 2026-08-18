# Build: Cross-cohort integration pass — spec-021 residual-completion cycle

Spec reference: `docs/SPECS/spec-021-apps-0_0_7.md` (65,342 bytes at this pass's close)
Rationale reference: `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` (85,169 bytes at this pass's close)
Plan reference: `docs/builder/build-021-apps-0_0_7.md` `## Verified findings`
Cohort artifacts: `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md` (`final-accepted`), `docs/builder/bld-review-2-db_backed_doc_reconciliation.md` (`final-accepted`)
Status: final-accepted

## Plan (Worker 1)

The cross-cohort integration pass of a **review round**, not a fresh build. The card `DONE-021-0.0.7` shipped in `0.0.7`; Worker 0's `## Verified findings` concludes that no code was skipped, dropped or deviated, and neither cohort wrote package source. R1 performed the rationale MOVE and the spec reconciliation; R2 performed the DB-backed doc reconciliation and the one stale test comment.

The integration corpus is therefore **prose across four surfaces that must tell one story** — the spec, the rationale companion, `docs/GLOSSARY.md`'s `## Django AppConfig` entry, and `KANBAN.md`'s `DONE-021-0.0.7` `#### Note` — plus the test comment and the shipped code all four describe.

### DRY analysis

**Helper inventory checked.** Not applicable in the code sense and not refreshed: no cohort in this cycle added or edited a helper, constant, validation branch, coercion utility or test helper, and the only `.py` byte either cohort moved is one comment block. The inventory exists to prevent duplicated *implementation* shapes; there is no implementation in this cycle to duplicate. The condition that would change the answer is a cohort writing package logic, which the plan's ownership partition forbids.

The DRY questions that do apply are cross-surface:

- **Existing patterns reused.** The move-vs-copy instrument is the cross-file long-sentence similarity scan both R1 review passes used, run here at a **lower** threshold (0.80, then 0.75) because the 0.85 threshold this cycle relied on hid a real five-entry duplication that R1's own final verification later found.
- **New shared shape justified.** None. Two cohorts, both closed, no shape to assign.
- **Duplication risk avoided.** Two risks. (1) The spec/rationale MOVE degrading into a copy — measured below, not asserted. (2) Four surfaces describing one `ready()` and drifting apart — the plan's design gives them different subjects (spec = the contract; rationale = how it got there; glossary = the package's current state; card note = what card 021's own diff shipped), and this pass reads all four side by side against source to check that the subjects held.

### Implementation steps

1. Read both cohort artifacts in full and in order, plus the plan's `## Verified findings`, the spec, the rationale, `AGENTS.md`, `START.md`, `BUILD.md`, `ARTIFACT.md`, `worker-1.md`, `GOAL.md`, `docs/GLOSSARY.md`, `CHANGELOG.md`.
2. Read the four prose surfaces side by side against `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` and the three `_*_patches.py` module docstrings at `HEAD`.
3. Sweep all four surfaces for any surviving assertion, implication or dependency on "no `ready()` body", in any spelling.
4. Re-run the move-vs-copy scan at 0.80 or lower.
5. Re-derive every release fact off **tag content**, and check the plan's `### F9` table, R2's release-facts block, the card note, the glossary body and `CHANGELOG.md`'s `[0.0.7]` entry against each other.
6. Run the staged-anchor sweep for both this card's current number and its pre-renumber number.
7. Confirm the generated docs still carry R2's intended lines, read-only, without running a generator.
8. Walk both artifacts' `What looks solid` and `Notes for Worker 1` sections and re-derive every catalog population at write time.

### Test additions / updates

None, and none is owed. This pass writes no `.py`; `tests/test_apps.py` is R2's landed work and was read, not modified. `uv run pytest tests/test_apps.py --no-cov` was run once as confirmation, not as a gate.

### Implementation discretion items

- The section ordering inside this artifact, provided every check `BUILD.md` `## Cross-slice integration pass` names is either performed or recorded as skipped with its reason.
- Whether a cross-surface inconsistency is fixed here or routed back through a cohort — decided per finding by whether the fix is a spec edit (mine) or touches a DB row, package source, or `CHANGELOG.md` (not mine, and `revision-needed`).

### Dispatched findings checklist

An integration pass has no dispatched findings. The boxes below are `BUILD.md` `## Cross-slice integration pass`'s own steps plus the four checks that replace steps 2-4 for a cohort pair that wrote no package `.py`.

- [x] **Step 1 — every prior cohort artifact read in full, in order.** `bld-review-1-rationale_and_spec_reconciliation.md` (1,185 lines, three build passes and three reviews plus final verification) and `bld-review-2-db_backed_doc_reconciliation.md` (798 lines, two build passes and two reviews plus final verification).
- [x] **Steps 2, 3 and 4 — the `scripts/review_inspect.py` shadow-overview comparisons.** **Skipped, with the reason recorded** — see `### Applicability record` below.
- [x] **Step 5 — both artifacts' `What looks solid` / `DRY findings` / `Notes for Worker 1` walked** for deferred follow-up that should land here.
- [x] **Step 6 — staged-anchor sweep**, for `spec-021` / `021` and for the pre-renumber `spec-017` / `017`.
- [x] **Four-surface coherence**, read side by side against source.
- [x] **No surviving claim the code falsifies**, swept by idea as well as by phrase.
- [x] **The MOVE is still a move**, at 0.80 and at 0.75.
- [x] **Release facts agree everywhere**, re-derived off tag content.
- [x] **Generated-doc integrity**, read-only, through the rendered files and the ORM.

---

## Integration pass record

### Applicability record — `BUILD.md` steps 2, 3 and 4 skipped

`BUILD.md` `## Cross-slice integration pass` steps 2-4 require confirming `scripts/review_inspect.py` ran for every Python file with review-worthy logic, then comparing the **Repeated string literals** and **Imports** sections across every shadow overview.

**Not applicable to this cycle, recorded rather than omitted.** `BUILD.md` `### When to run the helper during build` scopes the helper to source logic. No cohort in this cycle added or edited package `.py`: the plan's ownership partition assigns `django_strawberry_framework/**` to no cohort, and the only `.py` file either cohort touched is `tests/test_apps.py`, whose diff is one comment block — one hunk, seven lines out, six lines in, no assertion, no test body, no import. Verified here rather than taken on report: `git diff HEAD -- django_strawberry_framework/` over the paths either cohort owns is empty, and `git diff HEAD -- tests/test_apps.py` is that single comment hunk.

There is consequently no shadow overview to compare, no repeated string literal across cohorts, and no import direction to check — the two cohorts' outputs are Markdown, two SQLite rows and one comment. The plan's pre-flight step 2 recorded the same skip for the same reason, and both cohorts' review passes recorded it again; this is the fourth recording and the first at cross-cohort scope.

**What replaces them** is the four-surface coherence work below. That substitution is not a waiver: a cycle whose entire product is prose has its duplication risk in the prose, and the instruments that find it are the cross-file similarity scan and a side-by-side read against source.

### Four-surface coherence

Read side by side: the spec's Slice 1 `ready()` sub-bullet and `### Decision 4 — ready() applies the upstream patches`; the rationale's Decision 4 entry; `docs/GLOSSARY.md`'s `## Django AppConfig`; `KANBAN.md`'s `DONE-021-0.0.7` `#### Note`. Then each against `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`, the three `_*_patches.py` module docstrings, `django_strawberry_framework/conf.py::upstream_patches_enabled` and `tests/test_apps.py` at `HEAD`.

**Every clause the four surfaces share holds against source.** Checked clause by clause, reading the source first: `ready` is in `DjangoStrawberryFrameworkConfig.__dict__`; the three imports are inside the method body, so importing the module outside Django pulls in no patch module; the call sequence is `apply_django()`, `apply_strawberry()`, `apply_cross_web()`; the dispatcher carries no gate and each `apply()` self-gates on `APPLY_UPSTREAM_PATCHES`; the dispatcher's docstring states that each patch module's docstring is the single source of truth for its inventory and repeats none of it — and neither Decision 4 nor the glossary entry repeats it either, so the inventory is stated once and declined three times.

**The ordering gloss is closed at every site, and closed the same way everywhere.** `grep -o 'dependency order' | wc -l` (occurrences, not lines): spec **0**, rationale **2**, `docs/GLOSSARY.md` **0**, `KANBAN.md` **0**, `KANBAN.html` **0**, `tests/test_apps.py` **0**. The two rationale occurrences are the rejected-alternative bullet under Decision 4 and the `**Claims this decision may no longer make:**` list — both *name* the struck phrase as refused rather than assert it, which is what a rationale file is for. Spec and glossary both read **"in this order"**, word for word, and both agree with the source sequence.

**Two findings, both fixed here.** They are the class this cycle kept producing, one surface over from where each cohort was looking, and neither cohort could have seen them: R1 wrote the prescriptions, R2 landed the text, and no pass compared the two.

#### Finding 1 — the spec's `## Doc updates` KANBAN prescription attributes the three-applier `ready()` to this card

`## Doc updates`' `KANBAN.md` bullet prescribed the Done body as "Shipped `django_strawberry_framework/apps.py` containing `DjangoStrawberryFrameworkConfig(AppConfig)` … **plus a `ready()` body that dispatches the package's three upstream-patch appliers**; package-internal tests at `tests/test_apps.py`."

Both halves of the emphasised clause are false, and each is falsifiable in one command:

- **This card's own diff carries no `ready()` at all.** The commit that first adds the module (`git log --diff-filter=A -- django_strawberry_framework/apps.py`) has `grep -c 'def ready'` -> **0**, and so does `git show 300e2811^:django_strawberry_framework/apps.py`.
- **The three-applier dispatch is not `0.0.7` content.** `git show 0.0.7:django_strawberry_framework/apps.py` -> `def ready` present, `grep -cE 'apply_strawberry|apply_cross_web'` -> **0**. The first tag carrying all three is `0.0.11`.

It also contradicted the same file's `## Out of scope`, which already assigns the Django half to `DONE-024-0.0.7` and the Strawberry and `cross_web` halves to later cards — an intra-file contradiction on top of the cross-surface one.

This is precisely the claim R2's Worker 3 filed as its **High** against the card note and Worker 2 fixed in the DB. R2's landed `CardItem` text reached the correct scoping independently; the spec was the one surface still asserting the unscoped version, and the two disagreed in writing. R1's rewrite of this prescription replaced a false *absence* ("no `ready()` body in `0.0.7` (deferred to the card that needs one)") with an unscoped *presence*, which is the same defect in the other direction.

**Fixed** — the prescription now scopes the absence to this card's own diff and says where the release's `ready()` came from. Recorded under `### Spec changes made (Worker 1 only)`.

#### Finding 2 — the spec's `## Doc updates` CHANGELOG prescription diverges from an entry the cycle resolved must not change

The same section prescribed the `[0.0.7]` `### Added` text ending "…and the `ready()` body applies the package's upstream patches at app-load time." `CHANGELOG.md`'s live entry ends differently: the `ready()` body "imports `django_strawberry_framework._django_patches` and calls `apply()` to install the Django Trac #37064 hardening at app-load time".

The plan's `### F9` and R2's `### F9 is not this cohort's work` both grade the live entry **resolved-not-a-defect**: it describes the `0.0.7` release, which carries one applier, so naming one applier is what makes it accurate, and `AGENTS.md` forbids the edit independently. A spec prescribing a *different* text for that entry is a standing instruction to make the edit the cycle just resolved must not be made — and the prescription is looser than the release ("the package's upstream patches", unqualified), so enacting it would weaken an accurate entry.

For contrast, the `docs/README.md` prescription in the same section matches its target **verbatim** (`docs/README.md` line 112 against the spec's quoted bullet), which is the shape the other prescriptions should have.

**Fixed** — the prescription now states the entry as it shipped and says explicitly that the Strawberry and `cross_web` appliers are not `0.0.7` content.

#### The glossary prescription is correct and was deliberately left alone

`## Doc updates`' `docs/GLOSSARY.md` bullet prescribes an entry body naming "the package's three upstream-patch appliers, all gated by `APPLY_UPSTREAM_PATCHES`" and instructs that the entry "names the dispatch, not the patch inventory". A glossary entry describes the package's **current** state, where the three-applier dispatch is what ships, so no release scoping is owed there. R2's landed body satisfies the instruction including the inventory carve-out. Not a finding; recorded because the neighbouring two bullets were fixed and a reader will ask why this one was not.

### No claim the code falsifies

Swept all four surfaces plus `tests/test_apps.py` and `CHANGELOG.md` for any surviving assertion, implication or dependency on "no `ready()` body", by idea rather than by phrase: `grep -nioE '(no|without|not|never|absent|omit[a-z]*|defines no|adds no|lacks?)[^.]{0,60}ready'`, then read every hit in context.

- **`docs/SPECS/spec-021-apps-0_0_7.md`** — 12 matching lines, **0** surviving claims. Every hit is a correct statement about something else: the `conf.py` bullet's "no `ready()`-side initialization is needed" for the settings singleton; Decision 4's "the gate lives inside each `apply()`, **not** in `ready()`"; Borrowing posture's "strawberry-django implements no `ready()`; this package does"; the Slice 1 and DoD sub-bullets' "and nothing else"; the test-name token `defines_no_extra_appconfig_attributes`; `## Out of scope`'s "a future card would extend `ready()`".
- **`docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md`** — many hits, **0** surviving claims. Every one is a record of the retired claim under a `Was` column, a `Deleted outright` bullet, a revision entry, or the `Claims this decision may no longer make` list. That is the file's job.
- **`docs/GLOSSARY.md`** and **`KANBAN.md`** — **0** hits inside this card's surfaces. The `KANBAN.md` hit at the card note is R2's scoped statement, which is true of this card's diff and says so.
- **`tests/test_apps.py`** — **0** hits of any kind. `grep -c 'spec-017'` -> **0** and `grep -c 'spec-021'` -> **0**; the comment states the invariant ("`ready` is deliberately absent from this set: it is required on this class, not forbidden") and carries no spec number, no supersession narrative and no test names.
- **`CHANGELOG.md`** — **0** hits about `ready()`. Its `[0.0.7]` entry asserts the one applier that release carries, which is accurate rather than a survival.

### The MOVE is still a move

Instrument: fenced blocks stripped, every sentence of 90 characters or more compared pairwise across the two files with `difflib.SequenceMatcher`, run **after** this pass's last edit to either file. Corpus: 270 long sentences in the spec, 342 in the rationale.

- exact duplicate sentences: **0**
- pairs at or above **0.80**: **0**
- pairs at or above **0.75** (a second, lower run, because 0.85 is the threshold that hid a real duplication earlier in this cycle): **0**

The one near-verbatim pair anywhere in the corpus is across a *different* boundary and is not a defect: `docs/GLOSSARY.md`'s entry and spec Decision 4 share "The three imports are function-local, so importing `django_strawberry_framework.apps` outside Django pulls in no patch module" at 0.984 (the spec bolds `function-local`). That is one shared **fact** between a contract and a capability catalog, not a shared argument, and the plan's different-subjects decision explicitly contemplates the two surfaces stating the same facts in their own voices. No consolidation is proposed: a glossary entry that omitted the function-local property would under-describe the shipped `ready()`, which is the finding R2 exists to close.

### Release facts agree everywhere

Every figure below re-derived from **tag content**. `git merge-base --is-ancestor` was not used anywhere in this pass.

| fact | command | result |
|---|---|---|
| `0.0.7` carries a `ready()` body | `git show 0.0.7:django_strawberry_framework/apps.py \| grep -c 'def ready'` | **1** |
| `0.0.7` carries the Django applier alone | same file, `grep -cE 'apply_strawberry\|apply_cross_web'` | **0** |
| `0.0.10` still carries one applier | `git show 0.0.10:… \| grep -cE 'apply_strawberry\|apply_cross_web'` | **0** |
| `0.0.11` is the first tag carrying three | `git show 0.0.11:… \| grep -cE 'apply_strawberry\(\)\|apply_cross_web\(\)'` | **2** (plus `apply_django()`) |
| the dispatch test is absent from the last tag | `git show 0.0.13:tests/test_apps.py \| grep -c test_ready_dispatches_all_three_patch_appliers_and_refires_safely` | **0**, so it ships at `0.0.14` |
| the release list | `git tag \| sort -V` | `0.0.7 0.0.8 0.0.9 0.0.10 0.0.11 0.0.13` plus two `backup-*` refs, which are not releases |

Checked against every surface that states a release:

- **`docs/builder/build-021-apps-0_0_7.md` `### F9`** — table reads `0.0.7` / **`0.0.11`** / `0.0.14`, with `pyproject.toml` at each work commit recorded as the *caveat* rather than the evidence. Agrees.
- **`docs/builder/bld-review-2-db_backed_doc_reconciliation.md` `### The release facts this cohort's wording rests on`** — the appliers row now carries the tag-content derivation and "four releases later"; the dispatch-test row reads `0.0.14` with the `0.0.13` tag probe as its evidence. Agrees, and "four releases later" is arithmetically right (`0.0.8`, `0.0.9`, `0.0.10`, `0.0.11`).
- **`KANBAN.md` card note** — "the Strawberry and `cross_web` appliers followed at `0.0.11`". `grep -c '0.0.10'` in `CardItem` pk 750's text -> **0**. Agrees.
- **`docs/GLOSSARY.md`** — states no release for the appliers; its `**Status:**` is `shipped (0.0.7)`, correct for the AppConfig itself. No conflict.
- **`CHANGELOG.md` `[0.0.7]`** — one applier, the Django Trac #37064 hardening. Accurate as history; unchanged by both cohorts (`git diff HEAD -- CHANGELOG.md` -> 0 lines).
- **The spec** — carried no `0.0.11` claim before this pass and states the corrected release facts only where Finding 1 and Finding 2 required. Version strings in the file: 55 `0.0.7`, 9 `0.0.14`, 2 `0.0.6`, and now the `0.0.7` scoping added by the two fixes. No `0.0.12` anywhere.
- **The rationale** — its Decision 4 chronology table states dates and commits and claims no version for `c7cb5f5c` or `136c5476`, so it cannot disagree; the claims-index row added this pass states `0.0.11` with the tag-content derivation behind it.

### Staged-anchor sweep

`grep -rEn 'TODO\(spec-021|TODO-(ALPHA|BETA|STABLE)-021' .` over the whole tree (`.git` and `.venv` excluded) -> **zero hits**.

`grep -rEn 'TODO\(spec-017|TODO-(ALPHA|BETA|STABLE)-017' .` (this card's **pre-renumber** number) -> **three hits, all in one file and none an anchor**: `docs/builder/DONE/build-017-deferred_scalars-0_0_6.md` lines 54, 76 and 139. Judged by what they name rather than by their number, per the dispatch: that file is the completed build plan of `spec-017-deferred_scalars-0_0_6.md`, a different, unrelated `0.0.6` card, and line 54 is that cycle's own record that *its* sweep returned zero — the two patterns appear there as quoted patterns inside prose, not as staged anchors in source. The file is also a concurrent session's untracked/moved artifact under `AGENTS.md` rule 34.

**No anchor in shipped source, tests or comments names this build's spec or card, under either number.** Nothing to discharge, nothing to route.

`KANBAN.md`, `KANBAN.html` and `BACKLOG.md` were excluded from the judgement as the dispatch requires, where `TODO-<MILESTONE>-<NNN>` legitimately names unshipped board cards. For completeness, the spec itself carries **zero** `TODO-ALPHA` / `WIP-ALPHA` tokens after R1's `## Out of scope` re-derivation.

### Generated-doc integrity (read-only)

No generator was run by this pass — that would be a write this pass does not own, and `docs/GLOSSARY.md` / `KANBAN.md` / `KANBAN.html` / `examples/fakeshop/db.sqlite3` are R2's landed output plus a concurrent cohort's. Verified instead by reading the rendered files and the two rows through the ORM.

- `GlossaryTerm` pk **448** — `anchor='django-appconfig'`, `status_text='shipped (`0.0.7`)'`, `len(body)` **1758**; `body.count('dependency order')` -> **0**, `body.count('in this order')` -> **1**, `body.count('three defensive')` -> **1**.
- `CardItem` pk **750** — `card_id=43`, `section.key='note'`, `is_complete=True`, `len(text)` **287**; `text.count('0.0.11')` -> **1**, `text.count('0.0.10')` -> **0**, `text.count("this card's own diff")` -> **1**.
- `docs/GLOSSARY.md` — the `## Django AppConfig` entry renders the pk-448 body (rendered paragraph 1,609 characters; the remainder of the column is the `**See also:**` line, which the renderer emits verbatim from the same column). `grep -c 'dependency order' docs/GLOSSARY.md` -> **0**.
- `KANBAN.md` — the `DONE-021-0.0.7` `#### Note` bullet carries the `0.0.11` wording, once.
- `KANBAN.html` — `grep -c 'appliers followed at'` -> **1**, and the rendered fragment reads `` appliers followed at `0.0.11`. ``

**A concurrent session regenerated these docs mid-cycle for `GlossaryTerm` pk 504, and nothing R2 landed was reverted by it.** That is the failure mode this check exists to catch — a regenerate is exactly what would silently revert a hand-edit — and all five readings above were taken after that regenerate.

### Cross-cohort DRY

- **No duplicated helper, constant, literal or import across the two cohorts.** Neither wrote package source; there is nothing to consolidate. The `worker-1.md` delta — grep a consolidation candidate's readers before designing a shared shape — has no candidate to apply to.
- **The patch inventory is stated once and declined three times.** `ready()`'s docstring owns "which upstream bugs each module hardens"; Decision 4, the glossary entry and the card note each decline to copy it, each saying so. Three declines, zero copies, verified by reading all four.
- **The four surfaces' subjects held.** Contract / chronology / current state / this card's diff. After the two fixes above, no surface asserts what another retracts.
- **One argument told twice inside the rationale, examined and left.** `## Provenance of this record`'s `Deleted outright` list and the `## Claims the spec may no longer make` table narrate the same five retractions. The table is framed as an index of the retractions above, which is an index-vs-body relationship with one owner rather than duplication. R1's Worker 3 reached the same judgement in its pass-1 and pass-3 `DRY findings`; re-derived here rather than inherited, and I agree. The next editor should know that correcting one of those five means correcting two places.
- **Existence challenge: none raised.** Neither cohort introduced an abstraction, helper, registry or indirection layer.

---

## Final verification (Worker 1)

### Summary

The two cohorts land one coherent story. R1 delivered the rationale MOVE the original `0.0.7` cycle never ran and the Decision 4 reconciliation a sibling card falsified inside its own release; R2 delivered the two DB-backed doc bodies and the stale test comment. Read side by side against source, the spec, the rationale, the glossary entry and the card note now agree with each other and with `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` on every clause they share, and no surface carries a surviving "no `ready()` body" claim in any spelling.

This pass found two cross-cohort inconsistencies, both in the spec's `## Doc updates` prescriptions and both invisible from inside either cohort: R1 wrote a KANBAN Done-body prescription attributing the three-applier `ready()` to this card, which R2's landed board text contradicts and which the `0.0.7` tag falsifies; and a CHANGELOG prescription diverging from an entry this cycle resolved must not be edited. Both fixes are spec edits, neither touches a DB row, package source or `CHANGELOG.md`, and neither requires a cohort loop — so the cycle does not reopen.

The shadow-overview comparisons `BUILD.md` steps 2-4 require are recorded as skipped with their reason: no cohort wrote package `.py`.

### Spec changes made (Worker 1 only)

| # | File and passage | Change | Reason |
|---|---|---|---|
| 1 | `docs/SPECS/spec-021-apps-0_0_7.md` `## Doc updates`, the `KANBAN.md` Done-body prescription | "plus a `ready()` body that dispatches the package's three upstream-patch appliers" -> "and no `ready()` override in this card's own diff", followed by a sentence naming `DONE-024-0.0.7` as the source of the release's `ready()` and the Django applier as the only one `0.0.7` carries, with a pointer to `## Out of scope` | Finding 1. Both halves of the struck clause are false against tag content and against the commit that first adds the module, it contradicted `## Out of scope` in the same file, and it disagreed with the board text R2 landed. |
| 2 | `docs/SPECS/spec-021-apps-0_0_7.md` `## Doc updates`, the `CHANGELOG.md` entry prescription | ", and the `ready()` body applies the package's upstream patches at app-load time." -> the entry as it shipped (the `_django_patches` import, the `apply()` call, the Django Trac #37064 hardening), plus an explicit statement that the Strawberry and `cross_web` appliers are not `0.0.7` content | Finding 2. The prescription diverged from an entry the cycle graded resolved-not-a-defect, and was looser than the release, so enacting it would weaken an accurate entry. |
| 3 | `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` `### `## Doc updates`` | New paragraph recording both corrections, the commands behind them, and why the `docs/GLOSSARY.md` prescription is untouched | The rationale is where chronology lives; the spec states the corrected prescriptions flat and narrates nothing. |
| 4 | Same file, `## Claims the spec may no longer make` | New row: "this card's own diff shipped a `ready()` body dispatching three upstream-patch appliers" | So a later author restoring the clause meets a standing refusal, the same shape the "dependency order" retraction already has. |
| 5 | Same file, `## Left open by this pass` — opener and third bullet | Opener restated (two items open, one closed by the round's own R2 cohort after the section was written); third bullet rewritten to record the two DB-backed bodies as **closed**, with what each now says | The bullet described R2's completed work as open, in a standing doc, because R1 wrote it before R2 ran. |
| 6 | Same bullet, its `CHANGELOG.md` sentence | "`CHANGELOG.md`'s `[0.0.7]` entry has the same understatement (one applier, not three)" -> a statement that the entry is **not** understated, with the release reason and the `AGENTS.md` prohibition | This was a **false claim in a standing doc**, asserting as a defect exactly what the plan's `### F9` and R2's plan both grade resolved-not-a-defect. The sharpest single finding of the pass. |
| 7 | Same file, `## Provenance of this record` byte figures | Re-measured after the last content edit and substituted at equal width: spec **65,342**, rationale **85,169**, shed **32,176** (`97518 - 65342`), surplus **52,993** (`85169 - 32176`) | Edits 3-6 falsified all four. The paragraph reports the size of the file that carries it, so the substitution must be width-neutral or it moves the number it reports. |
| 8 | Same file, `<!-- docs/ -->` link definitions | No new definition needed — `[agents]` already existed and is now used by edit 6's citation | Recorded so the unused/undefined sweep below reads as intentional. |

**Method for edit 7, and its proof.** Every figure measured first, then substituted digit-for-digit at identical width, then the file re-measured to confirm the substitution moved nothing: `len(bytes)` before **85,169**, after **85,169**. Arithmetic re-checked independently: `97518 - 65342 = 32176`; `85169 - 32176 = 52993`. **Twin sweep after the change** — `grep -c '64,813\|80,506\|32,705\|47,801'` over the rationale -> **0**, and a full numeral sweep (`[0-9]{1,3},[0-9]{3}|[0-9]{4,}`) returns only the five byte figures (the shed twice, by the design the paragraph states), the four commit-hash digit runs, the `sed` range `34,513`, the Trac id `37064` and calendar years.

### Validation run

Every command run after this pass's last edit to either file.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-021-apps-0_0_7.md` -> `OK: 12 terms - all have glossary entries and at least one spec link.`, **exit 0**.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-021-apps-0_0_7.md docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` -> **exit 0**.
- `uv run pytest tests/test_apps.py --no-cov` -> **8 passed** in 1.64s. No `--cov*` flag in any form, anywhere in this pass. Confirmation only: this pass touches no `.py`.
- `uv run ruff format .` / `uv run ruff check --fix .` — **not applicable**; no `.py` file was touched, and a repo-wide write-mode run would sweep the concurrent session's dirty modules.
- **In-page anchors, re-swept after the last edit** by slugging every heading's rendered text outside fenced blocks (reference-style headings slug to their label alone; underscores survive slugging). Spec: 31 headings, 15 distinct in-page anchors, **14 resolve**; the 15th is the known false positive `#django-appconfig`, which is text inside the `docs/GLOSSARY.md #"[Django `AppConfig`](#django-appconfig)"` citation and not a link — re-read to confirm. Rationale: 27 headings, 6 distinct anchors, **all resolve**. The one anchor this pass added, `#out-of-scope-explicitly-tracked-elsewhere`, resolves. My first sweep reported three extra spec dangles; the fault was my own slugger stripping underscores, which the GitHub rule keeps — re-run corrected. A broken instrument that indicts the file is the trap this cycle keeps hitting one level out.
- **Reference-link integrity, both files:** zero undefined uses, zero unused definitions, every non-URL definition path disk-exists-checked from its own file's directory, all ten canonical group headers present in the required order, **every group alphabetical**. The rationale's two apparent undefined refs, `0-9` and `a-z0-9-`, remain character classes inside code spans in the re-derivation commands.
- `AGENTS.md` rule 27: `grep -E '[A-Za-z0-9_/.-]+\.(py|md|toml):[0-9]+'` over both standing docs -> **0** in each. Rule 4: neither names the forbidden files.
- **History narration in the spec:** `grep -noiE 'rev[0-9]|revision|superseded|formerly|previously|originally|no longer|used to|Alternatives considered|Revision history|Risks and open questions'` -> hits on **line 8 only**, the required rationale-pointer paragraph. My two spec edits state the current fact flat; both chronologies went to the rationale.
- **The citation this pass added resolves:** `AGENTS.md #"No CHANGELOG.md updates unless told"` -> `grep -c` on `AGENTS.md` returns **1**. Chosen over the paraphrase spellings this cycle recorded as the repo-wide `AGENTS.md` class precisely because it occurs verbatim.
- `git status --short` -> **32 paths**, re-measured after this artifact was written and therefore counting it (the reading taken before the write was 31 — a `git status` count that omits the file stating it is the same self-referential defect as a byte figure taken mid-write). Mine, and in my writable set: `M docs/SPECS/spec-021-apps-0_0_7.md`, `?? docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md`, `?? docs/builder/bld-integration.md`. R2's landed and audited: `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3`, `tests/test_apps.py`. The remaining 24 are concurrent-session work — **recorded, never edited, never reverted, never staged** (`AGENTS.md` rule 34): 7 package modules under a refactor (`auth/mutations.py`, `mutations/inputs.py`, `mutations/resolvers.py`, `mutations/sets.py`, `rest_framework/resolvers.py`, `utils/inputs.py`, `utils/write_values.py`) and their 5 test modules; `docs/SPECS/spec-022-export_schema-0_0_7.md` and `docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`; one further `docs/` path; `docs/builder/build-020-list_field-0_0_7.md` (staged deleted) with `docs/builder/DONE/build-020-list_field-0_0_7.md` (untracked); Worker 0's two plans; the two cohort artifacts; and the concurrent `spec-022` cycle's `appx/spec-022-export_schema-0_0_7-rationale.md`, `bld-review-1-spec_022_reconciliation.md` and `bld-review-2-spec_022_glossary_body.md`. **Drift from the plan's declared baseline, re-derived not copied: `docs/builder/bld-003-final.md` is no longer dirty** and is therefore not among them.
- **Both cohort artifacts re-read at close:** `Status: final-accepted` on each; the misfiled R1 build-report section is gone from R2's artifact (`grep -c '^## Build report (Worker 1, pass 2'` -> **0**) and present exactly once in R1's own (-> **1**), so the removal R2's final verification performed took nothing with it.

### Deferred work catalog — consolidated across both cohorts, re-derived at this pass's write time

The final gate draws its `### Deferred work catalog` from this list. Each item names its **source artifact section** rather than duplicating its prose, and **every population below was re-derived by me now** — a catalog is a claim, and two of this cycle's catalogs were wrong on first statement. Drift-sensitivity is marked per item.

1. **`[spec-016]` / `[spec-017]` ref-id residue in sibling files.** Source: `bld-review-1-…md` `### Deferred work catalog — consolidated and re-derived` item 2 (population corrected twice within R1). The residue is **definition lines whose ref-id number and target basename disagree**, never token hits — a raw token grep over the same files massively overstates it, because `spec-016-fieldmeta_consolidation-0_0_6.md` and `spec-017-deferred_scalars-0_0_6.md` are real current filenames. **HIGHLY DRIFT-SENSITIVE. Re-derived now over the working tree: 24 definitions across `docs/SPECS/`, `docs/SPECS/appx/` and `KANBAN.md`; 16 agree, 8 disagree — `spec-023` 3, `spec-025` 2, `spec-027` 2, `KANBAN.md` 1.** `spec-022`'s seven are gone under a concurrent session's uncommitted work. **Re-run the instrument at write time; do not copy this number.**
2. **`spec-022` asserted the claim R1 retired, about this very spec.** Source: `bld-review-1-…md` `### Deferred work catalog` item 3 and the rationale's `## Left open by this pass`. At `51eb47ba` the file carried four `ready()` passages, three of them false assertions. **HIGHLY DRIFT-SENSITIVE, and re-derived now: `grep -c 'ready()' docs/SPECS/spec-022-export_schema-0_0_7.md` -> 0.** The concurrent `spec-022` rationale-extraction round removed all four, and that work is **uncommitted**. **Drop this item if that session's work commits; re-open it if the work is reverted.**
3. **Non-shipped `Status:` lines on shipped cards.** Source: `bld-review-1-…md` `### Deferred work catalog` item 4. **Re-derived now by reading line 4 of each: `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` still reads "Only the final test-run gate remains" on a shipped card — the only open instance.** `spec-022`'s line 4 now reads shipped-and-archived under the concurrent session's uncommitted work (drift-sensitive, re-check); `spec-023`'s was already correct. The pattern is not uniform, so each file needs its own look rather than a sweep.
4. **The `AGENTS.md` paraphrase-citation convention across `docs/SPECS/`.** Source: `bld-review-1-…md` `### Escalation resolved — the `AGENTS.md` citation class`, resolved there as a spec-authoring call. **Publish the corpus rule, never a digit copied from this cycle.** The readings are enumerated rather than counted, because a count of disagreeing sweeps is the same kind of claim they failed at: R1 pass 2 reported `25 files / 101 occurrences / 22 distinct / zero resolving`; its Worker 3 measured `23 / 109 / 15 / two`; R1 pass 3 reported `27 / 111 / 16 / three`; its Worker 3 measured `28 / 119 / 16 / two`; R1's final verification measured `28 / 122 / 16 / two`. No two agree on occurrences, and the corpus is under concurrent rewrite while it is being counted — the only digit stable across the whole window is the 16 distinct substrings. The stable qualitative finding must be carried: **the class is not uniformly broken — at least two distinct substrings occur in `AGENTS.md` verbatim — so "not one resolves" must not be restated.** A repo-wide decision, not a per-spec fix. If the catalog wants a number, it re-runs the rule and timestamps the reading.
5. **No glossary term covers the Strawberry or `cross_web` upstream patches.** Source: `bld-review-2-…md` `## Plan (Worker 1)` `### Implementation discretion items` and its `### Deferred work catalog — R2's` item 1; endorsed by both R2 review passes. **Candidate, not built** — a new term needs an index row, a category membership and a `check_spec_glossary` story that no dispatched finding asks for. **Re-derived now through the ORM: across 142 `GlossaryTerm` rows, the only body naming `_strawberry_patches` or `_cross_web_patches` is pk 448 itself, and 0 anchors contain `patch`.** Stated as a **corpus rule** because a concurrent session is writing this DB: the term is missing for as long as no `GlossaryTerm.body` outside pk 448 names those two modules — re-run that probe at write time. The `**See also:**` line was deliberately not widened: `#utf-8-wire-contract` and `#request-body-cap` each state in their own bodies that they are *not* upstream-bug patches, so pointing at them would create a cross-reference the target contradicts.
6. **Repo-wide instrument note: "version at `pyproject.toml` at the work commit" is not "shipping release".** Source: `bld-review-2-…md` `### Notes for Worker 1` (Worker 3 pass 2 item 3, endorsed twice, and R2's final verification item 2). The bump lands at the cut, so `git show <commit>:pyproject.toml` reports the **previous** release; read releases off tag content or the `CHANGELOG.md` date. `git merge-base --is-ancestor` is **not** the substitute — concurrent sessions rewrite this branch and it answers `NO` for `c7cb5f5c` against tags whose content plainly contains it. **The class produced five wrong or unsupported readings in this cycle**, enumerated rather than counted from a description: the plan's `### F9` row (fixed by Worker 0), the card note's `0.0.10` (fixed by R2 pass 2), R2's release-facts evidence cell and its dispatch-test row's `0.0.13` (both fixed by R2's final verification), and the KANBAN Done-body prescription's three-applier attribution (Finding 1, fixed here). Nothing is open; the note is carried so the next cycle inherits the instrument rule rather than the digits.
7. **`CHANGELOG.md`'s `[0.0.7]` one-applier entry — RESOLVED-NOT-A-DEFECT, not an open item.** Source: `docs/builder/build-021-apps-0_0_7.md` `### F9 — DOES NOT HOLD` and `bld-review-2-…md` `### F9 is not this cohort's work`. R1's own catalog carried it as open item 1; R2 re-graded it and I confirm the re-grade on my own instruments: `git show 0.0.7:django_strawberry_framework/apps.py` carries exactly one applier, so the entry is accurate as history and "correcting" it to three would falsify it; `AGENTS.md` #"No CHANGELOG.md updates unless told" forbids the edit independently; `git diff HEAD -- CHANGELOG.md` -> 0 lines. **Record it in `bld-final.md` as resolved-not-a-defect.** A separable, still-open defect in the same file is the pre-renumber card labelling — re-derived now: `grep -oE '01[0-9]-[a-z_0-9]+-0\.0\.[0-9]+' CHANGELOG.md` gives 13 occurrences across 8 distinct labels, of which this card's `017-appspy_and_django_app_config-0.0.7` is one. **Do not conflate that with the differently-sized figure a `KANBAN.md` note records for a different population in a different file.**
8. **Decision 6's four-card bundle vs `KANBAN.md`'s seven `0.0.7` cards — NO ACTION, closed.** Source: `bld-review-1-…md` `### Deferred work catalog` item 6. The Decision states the WIP set at authoring time excluding the already-shipped `DONE-020-0.0.7`; `DONE-024` and `DONE-026` joined the release afterwards. Its subject is the version-bump policy, which no later card joining the release affects. Endorsed four times across R1; recorded so it is not re-opened a fifth.

**Explicitly NOT in this catalog:**

- **F8** (`tests/test_apps.py`'s `spec-017` provenance comment). It is R2's **work item**, it landed, and its tick is audited in R2's final verification and re-confirmed here (`grep -c 'spec-017' tests/test_apps.py` -> 0). Both cohorts' catalogs say the same; do not double-count it.
- **The "in dependency order" gloss.** Escalated by R2's Worker 3, resolved by R2's final verification at all three sites, re-verified here at every surface including the DB and both rendered docs.
- **The misfiled R1 build-report section in R2's artifact.** Removed by R2's final verification after a subset proof; re-verified here as gone from R2's artifact and intact in R1's.
- **Findings 1 and 2 of this pass.** Fixed here, not deferred.

### Final status

`final-accepted`.

Both cohorts' artifacts are `final-accepted` and every tick in each was audited by a fresh Worker 1 before this pass. The four prose surfaces tell one story, verified clause by clause against `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` and the three patch-module docstrings rather than against each other's accounts; no surface carries a surviving claim the code falsifies; the MOVE holds as a move at 0.80 and at 0.75; every release fact agrees across the plan, both artifacts, the card note, the glossary body and `CHANGELOG.md`, all re-derived off tag content; the staged-anchor sweep returns zero anchors for this build's card under either of its numbers; and R2's landed lines survive a concurrent cohort's mid-cycle regenerate, verified by reading the rendered files rather than by trusting a row read.

The two findings this pass produced are both spec edits inside my own writable set — a prescription attributing the three-applier `ready()` to a card whose diff carries none, and a prescription diverging from a `CHANGELOG.md` entry the cycle resolved must not change — plus two corrections to the rationale's own record of R2's work, one of which asserted as a defect exactly what the cycle graded resolved-not-a-defect. None of them touches a DB row, package source, `CHANGELOG.md` or either cohort's artifact, so none needs Workers 2 or 3 and the cycle does not reopen.

`BUILD.md` steps 2-4 are recorded as skipped with their reason rather than silently omitted. The consolidated deferred-work catalog above has every population re-derived at this pass's write time, with the drift-sensitive ones marked re-run-do-not-copy.

Next: the final test-run gate, `docs/builder/bld-final.md`.

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
