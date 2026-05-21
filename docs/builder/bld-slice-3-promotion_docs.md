````text
# Build: Slice 3 — Promotion + docs

Spec reference: `docs/spec-017-apps-0_0_7.md` (Slice 3 sub-bullets at lines 67-79; Doc updates at lines 397-427; Decisions 6 / 7)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.** Three site-specific patterns from prior accepted slices and the existing repo state guide Slice 3's mechanics; no new helpers are justified because Slice 3 ships pure Markdown edits with no Python surface to consolidate.
  - The CHANGELOG entry wording for this slice lifts directly from the spec's [Doc updates](../spec-017-apps-0_0_7.md#doc-updates) `CHANGELOG.md` bullet at `docs/spec-017-apps-0_0_7.md:419`. Worker 2 quotes that bullet verbatim under the existing `[0.0.7]` `### Added` heading; no paraphrase. See [Verbatim CHANGELOG wording](#verbatim-changelog-wording) below for the character-for-character source string.
  - The KANBAN past-tense Done-column convention is established by every prior `DONE-NNN-X.Y.Z` card body at `KANBAN.md:1197-1394` (per `Read` of the file; the convention is past-tense `Scope:` / `Evidence:` / `Notes:` blocks). Worker 2 mirrors the existing `DONE-016-0.0.7` shape one entry up; the spec's suggested past-tense wording at `docs/spec-017-apps-0_0_7.md:415` is a default, not a contract — see [Implementation discretion items](#implementation-discretion-items).
  - The `docs/GLOSSARY.md` status flip pattern is the same one that fires on every shipped feature: the entry-level `**Status:** planned for `0.0.7`.` line (currently at `docs/GLOSSARY.md:248`) becomes `**Status:** shipped (`0.0.7`).`, and the Index table row at `docs/GLOSSARY.md:52` (currently `| [Django `AppConfig`](#django-appconfig) | planned for `0.0.7` |`) gets its status column flipped to `shipped (`0.0.7`)`. Symmetric with how `DONE-016-0.0.7` flipped [`DjangoListField`](../GLOSSARY.md#djangolistfield) at `docs/GLOSSARY.md:59` and `docs/GLOSSARY.md:302`.
- **New helpers justified.** None. Slice 3 touches no `.py` files; the slice is six Markdown edits across five files (GLOSSARY entry-body + Index, README heading + bullet add + surgical removal, TREE current-tree + target-tree, KANBAN column move + summary rewrite, CHANGELOG append) plus one CHANGELOG append. There is no shared logic, no repeated constant, and no near-copy that consolidation would improve.
- **Duplication risk avoided.** Four specific risks the naive implementation could introduce, and how the plan blocks them:
  1. **Creating a second `[0.0.7]` heading in `CHANGELOG.md`.** Per [Decision 6](../spec-017-apps-0_0_7.md#decision-6--joint-0_0_7-cut) at `docs/spec-017-apps-0_0_7.md:301-316` and the explicit reminder at `docs/spec-017-apps-0_0_7.md:419` ("do NOT create a second `[0.0.7]` heading"), the `0.0.7` joint-cut policy means every `0.0.7` card appends to the **same shared** `[0.0.7]` `### Added` section. The repo's `CHANGELOG.md:21-23` already has `## [0.0.7] - 2026-05-20` with one `### Added` bullet for `DjangoListField`; Worker 2 appends a second bullet directly below that, NOT under a new heading. A naive read of "add a CHANGELOG entry" could introduce a parallel `## [0.0.7] - <today>` block — explicit pin against that here.
  2. **Removing the entire `Coming in 0.1.0` bullet at `docs/README.md:112` instead of surgically removing only `, Django ` ``AppConfig`` ``.** The current line text is `- schema export management command, Django `AppConfig`` (per `Read` of `docs/README.md:112`). After Slice 3 the line MUST become exactly `- schema export management command` — the `schema export management command` half stays because `WIP-ALPHA-018-0.0.7` (the schema-export card) is the one that removes it later. Worker 2 deletes the substring `, Django ` ``AppConfig`` `` (note the leading comma + space) and nothing more. This is rev2 H1 / rev3 L1 / [Doc updates](../spec-017-apps-0_0_7.md#doc-updates) at spec line 407.
  3. **Re-stating the AppConfig wording across GLOSSARY entry body, README bullet, KANBAN body, and CHANGELOG bullet.** The strings `"django_strawberry_framework"` (`name` value), `"Django Strawberry Framework"` (`verbose_name` value), and `DjangoStrawberryFrameworkConfig` (class name) appear across all four docs. These are deliberate non-duplications — each doc pins its own context (GLOSSARY is the capability reference, README is the consumer-quickstart status section, KANBAN is the per-card audit trail, CHANGELOG is the release history). Factoring through a shared note or include directive would break the durability contract each doc carries individually; the parallel reasoning lives at `docs/builder/bld-slice-1-module_appconfig.md:14` (the symmetric `apps.py:9` / `__init__.py:16` `"django_strawberry_framework"` non-consolidation) and `docs/builder/bld-slice-2-tests.md:12` (the 3x repetition in `tests/test_apps.py` across import / `name` attr pin / registry key). Worker 2 writes each occurrence inline at its pin site.
  4. **Adding `tests/test_apps.py` after `test_list_field.py` instead of before it in `docs/TREE.md`'s current test-tree section.** `test_apps.py` sorts BEFORE `test_list_field.py` alphabetically (`a` < `l`); rev2 L1 explicitly corrected the rev1 wording that misplaced it "between `test_list_field.py` and `test_registry.py`." See [Doc updates](../spec-017-apps-0_0_7.md#doc-updates) at spec line 412.

### Implementation steps

Line numbers below are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written (per BUILD.md "Implementation steps" guidance).

Six file targets total. The steps are ordered to minimize re-reads of the same file (each file is opened, all its edits applied, then closed) and to land the KANBAN move before the CHANGELOG append so that if Worker 2's pass is interrupted between the two, the KANBAN's `### In progress` is the only-mid-state surface (CHANGELOG would still have only the `DjangoListField` bullet, which is consistent with an unshipped state).

1. **`docs/GLOSSARY.md` — two edits.**
   - **Edit (a)** — flip the entry-level status line for [Django `AppConfig`](../GLOSSARY.md#django-appconfig) at `docs/GLOSSARY.md:248`. Current text: `**Status:** planned for `0.0.7`.`. After edit: `**Status:** shipped (`0.0.7`).`. Use the exact format from the symmetric [`DjangoListField`](../GLOSSARY.md#djangolistfield) flip at `docs/GLOSSARY.md:302` (`**Status:** shipped (`0.0.7`).`) — character-for-character mirror.
   - **Edit (b)** — flip the Index table's status column for the [Django `AppConfig`](../GLOSSARY.md#django-appconfig) row at `docs/GLOSSARY.md:52`. Current text: `| [Django `AppConfig`](#django-appconfig) | planned for `0.0.7` |`. After edit: `| [Django `AppConfig`](#django-appconfig) | shipped (`0.0.7`) |`. Mirror the format from the [`DjangoListField`](../GLOSSARY.md#djangolistfield) row at `docs/GLOSSARY.md:59` (`| [`DjangoListField`](#djangolistfield) | shipped (`0.0.7`) |`).
   - **Optional (Worker 2's discretion)** — the spec's [Doc updates](../spec-017-apps-0_0_7.md#doc-updates) bullet at lines 400-401 also says "Update the entry body to describe the shipped contract." The current entry body at `docs/GLOSSARY.md:246-253` is two sentences: `**Status:** planned for 0.0.7.` plus `django_strawberry_framework/apps.py ships an AppConfig so consumers can add the package to INSTALLED_APPS and use Django checks / signal hooks against it.`. The second sentence is already correct in the present tense and remains accurate post-Slice-1; Worker 2 may leave it unchanged or replace it with the spec's more detailed shipped-contract wording at `docs/spec-017-apps-0_0_7.md:401` (`django_strawberry_framework/apps.py ships DjangoStrawberryFrameworkConfig with name = "django_strawberry_framework" and verbose_name = "Django Strawberry Framework"; no ready() body in 0.0.7; consumers list "django_strawberry_framework" in INSTALLED_APPS and Django's implicit single-AppConfig discovery resolves the explicit class.`). See [Implementation discretion items](#implementation-discretion-items) — the lower-friction default is "leave the existing one-sentence body unchanged because it already reads correctly in the present tense post-Slice-1," but the higher-detail option matches the spec's worded suggestion.

2. **`docs/README.md` — three edits in one file (rev3 L1 surgical actions).**
   - **Edit (a)** — bump the shipped-list heading at `docs/README.md:89`. Current text: `**Shipped today** (`0.0.6`):`. After edit: `**Shipped today** (`0.0.7`):`. This is the rev2 H1 catch-up against `DONE-016-0.0.7`'s heading-drift (the `DjangoListField` bullet at `docs/README.md:99` already annotates "(new in `0.0.7`)" inline without the heading bump); distinct from the version-string bump deferred to [Decision 6](../spec-017-apps-0_0_7.md#decision-6--joint-0_0_7-cut), which still belongs to the last `0.0.7` card to ship — the `pyproject.toml` / `__version__` / `tests/base/test_init.py` values stay at `0.0.6` after this card's Slice 3.
   - **Edit (b)** — add a bullet to that section. The spec at `docs/spec-017-apps-0_0_7.md:406` pins the exact wording:
     ```text
     - `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` so consumers can list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's check / signal hooks resolve through it (new in `0.0.7`).
     ```
     Insertion location: at the bottom of the `**Shipped today**` bulleted list, after the existing last bullet (`- annotation-only and `strawberry.field` consumer overrides for scalar fields, ...` at `docs/README.md:103`) and BEFORE the blank line that precedes `**Coming in `0.1.0`**` at `docs/README.md:105`. Adding at the bottom of the list matches the chronological-by-introduction convention every existing bullet in that section follows (each `(new in 0.0.X)` annotation aligns with the bullet's ship-order position).
   - **Edit (c)** — surgically remove `, Django ` ``AppConfig`` `` from `docs/README.md:112`. Current text: `- schema export management command, Django `AppConfig``. After edit: `- schema export management command`. Delete exactly the substring `, Django ` ``AppConfig`` `` (the leading comma + space + bare-words + backticked `AppConfig` token). Do NOT remove the entire line; do NOT remove `schema export management command` (the schema-export half stays for `WIP-ALPHA-018-0.0.7` to remove later when it ships). Per rev2 H1 / rev3 L1 / [Doc updates](../spec-017-apps-0_0_7.md#doc-updates) at spec line 407.

3. **`docs/TREE.md` — three edits in one file.**
   - **Edit (a)** — add `apps.py # AppConfig` to the current on-disk layout. Insertion location: under the `django_strawberry_framework/` tree at `docs/TREE.md:193-224`. Alphabetical position: between `__init__.py` (line 195) and `conf.py` (line 197). The new line is `├── apps.py                  # AppConfig`. Match the column-aligned `#`-comment style of the existing siblings on `docs/TREE.md:195-201` (the `#` sits at column ~27; align by inserting spaces between `apps.py` and `#` so the line visually matches).
   - **Edit (b)** — remove the `[alpha]` tag from the existing `apps.py # [alpha] Django AppConfig` line in the **target package layout** at `docs/TREE.md:236`. Current text: `├── apps.py                  # [alpha] Django AppConfig`. After edit: `├── apps.py                  # Django AppConfig`. The `[alpha]` tag means "lands before `0.1.0`"; the bullet has now landed (after Slices 1 & 2), so the tag is removed exactly like every prior shipped module's tag was removed when its card landed (compare `docs/TREE.md:236` vs `docs/TREE.md:194-195` for the post-DONE-016 `list_field.py` entry where the `[alpha]` was already removed in `docs/TREE.md`'s current-tree section).
   - **Edit (c)** — add `tests/test_apps.py` to the **current test-tree section**. Insertion location: under the `tests/` listing at `docs/TREE.md:330-360`. Position: **before `test_list_field.py`** (alphabetical — `apps` < `list_field`). The new line is `├── test_apps.py            # AppConfig (single-file Layer-3 module)`. Column-aligned `#`-comment style matching `docs/TREE.md:332` (the `test_list_field.py` line above which it sorts). The line becomes the new third entry under `tests/` (after `__init__.py` at line 331 and the inserted `test_apps.py`; before `test_list_field.py` which moves down to line 333; before `test_registry.py` which moves down to line 334). The rev2 L1 correction explicitly pinned "before `test_list_field.py`" (NOT "between `test_list_field.py` and `test_registry.py`" per the rev1 wording) — verify alphabetical order on the line above (`__init__.py` < `test_apps.py`) and the line below (`test_apps.py` < `test_list_field.py`).
   - **Optional symmetry check (Worker 2's discretion)** — `docs/TREE.md` also has a **target test-shape** section at lines 397-444 that already lists `test_apps.py` at line 401 (`├── test_apps.py             # AppConfig`). No edit needed there; the target test-shape already pre-listed the file. Worker 2 may verify it has not drifted but no edit is required.

4. **`KANBAN.md` — three edits in one file.**
   - **Edit (a) — column move with id renumber.** Move `WIP-ALPHA-017-0.0.7 — `apps.py` and Django app config` (currently at `KANBAN.md:78-88`) from the `## In progress` column to the `## Done` column. The next available `DONE-NNN-0.0.7` id is `DONE-017-0.0.7` — verified by reading `KANBAN.md`'s existing Done headings (`grep '^### DONE-' KANBAN.md`): the highest existing DONE id is `DONE-016-0.0.7` (the `DjangoListField` card), so the next sequential id is `017`. Worker 2 verifies this against the live file before writing (per `docs/builder/BUILD.md` line 13's "this number is not stable" rule — read the file's current Done column, pick the next number after the highest existing DONE id).
   - **Edit (b) — rewrite the body in past tense per the existing Done-column convention.** Current `In progress` body (`KANBAN.md:78-88`) is:
     ```text
     ### WIP-ALPHA-017-0.0.7 — `apps.py` and Django app config

     Priority: medium

     Status: planned

     Definition of done:

     - Add `django_strawberry_framework/apps.py`.
     - Add `tests/test_apps.py`.
     - Do not add settings placeholders unless a shipped feature consumes them.
     ```
     The spec's suggested past-tense Done-column body at `docs/spec-017-apps-0_0_7.md:415` is:
     ```text
     Shipped `django_strawberry_framework/apps.py` containing `DjangoStrawberryFrameworkConfig(AppConfig)` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`; no `ready()` body in `0.0.7` (deferred to the card that needs one); package-internal tests at `tests/test_apps.py`.
     ```
     Worker 2's task: rewrite the body in past tense following the existing Done-column convention (compare `KANBAN.md`'s `DONE-016-0.0.7` body at the `## Done` column's first entry, or any of `DONE-001` through `DONE-015` for the established `Scope:` / `Evidence:` / `Notes:` shape). Worker 2 may match the spec's suggested wording verbatim or polish it; the contract is "past-tense, names the shipped surface, follows the Done-column body shape" — see [Implementation discretion items](#implementation-discretion-items).
   - **Edit (c) — update the `### In progress` summary paragraph at `KANBAN.md:50` to remove `WIP-ALPHA-017-0.0.7` from the remaining-cards list.** Current text (per `Read` of `KANBAN.md:50`):
     ```text
     - `0.0.7` is the active patch. Five WIP cards were opened together so the small parity-driven slices land in one release; `DONE-016-0.0.7` (`DjangoListField`) shipped first, and the remaining four are still in progress: `WIP-ALPHA-017-0.0.7` (`apps.py` and Django app config), `WIP-ALPHA-018-0.0.7` (schema-export management command), `WIP-ALPHA-019-0.0.7` (multi-database cooperation contract), and `WIP-ALPHA-045-0.0.7` (warning-free scalar registration via `StrawberryConfig.scalar_map`). ...
     ```
     After Slice 3 ships, this card is no longer "in progress" — it joins `DONE-016-0.0.7` as a shipped card. Worker 2 updates the paragraph to reflect that: (a) bump the "five" / "remaining four" framing to "five WIP cards were opened together; two have shipped (`DONE-016-0.0.7` `DjangoListField` and `DONE-017-0.0.7` `apps.py` + Django app config) and the remaining three are still in progress," and (b) drop `WIP-ALPHA-017-0.0.7` from the remaining-cards enumeration. The exact rewording is at Worker 2's discretion within those two constraints; the spec just says "remove `WIP-ALPHA-017-0.0.7` from the remaining-cards list" (`docs/spec-017-apps-0_0_7.md:416`), so the natural-language reshape is implementer choice — see [Implementation discretion items](#implementation-discretion-items).

5. **`CHANGELOG.md` — one append.** Append a new bullet under the existing `[0.0.7]` `### Added` subsection at `CHANGELOG.md:21-23`. The current state (per `Read` of `CHANGELOG.md:21-23`):
   ```text
   ## [0.0.7] - 2026-05-20
   ### Added
   - `DjangoListField` — non-Relay `list[T]` field for **root Query fields**, with default `model._default_manager.all()` resolver, ...
   ```
   Worker 2 appends the AppConfig bullet directly under the existing `DjangoListField` bullet (so the bulleted list becomes two entries, both under the same `### Added` heading). Do NOT create a second `## [0.0.7]` heading; do NOT add a `### Changed` / `### Fixed` / `### Removed` heading (the slice ships no behavior changes, fixes, or removals beyond the appended `Added` entry). [`AGENTS.md`](../AGENTS.md) line 21 ("Do not update CHANGELOG.md unless explicitly instructed") — this Slice 3 sub-bullet IS the explicit instruction per [Doc updates](../spec-017-apps-0_0_7.md#doc-updates) at spec lines 419-421.

   The exact bullet wording lifts character-for-character from the spec — see [Verbatim CHANGELOG wording](#verbatim-changelog-wording) below.

6. **Final gates (per spec line 75-79; per BUILD.md `### Validation run`).**
   - `uv run ruff format .` (Worker 2's per-pass gate per BUILD.md line 247) — pass.
   - `uv run ruff check --fix .` (Worker 2's per-pass gate per BUILD.md line 247) — pass.
   - `git status --short` after both ruff invocations — confirm only the five files this slice touches (`docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md`) and the active build artifact (`docs/builder/bld-slice-3-promotion_docs.md`) appear in the diff. Any other file is unrelated tool churn Worker 2 owns reverting (per BUILD.md line 248).
   - Worker 2 MAY optionally run `uv run pytest --no-cov tests/test_apps.py -x -q` to confirm the post-Slice-2 5 tests still pass after the doc edits (the test file isn't touched in Slice 3, so this is purely a regression sanity check). Not required; the doc-only changes cannot affect test outcomes.
   - Note: this slice ships ZERO `.py` file changes, so `pytest` is mechanically irrelevant. The final test-run gate at `docs/builder/bld-final.md` (run by Worker 1 after the cross-slice integration pass) is where the full `uv run pytest --no-cov` sweep runs — per BUILD.md lines 534-553.

### Verbatim CHANGELOG wording

Per the spec's [Doc updates](../spec-017-apps-0_0_7.md#doc-updates) `CHANGELOG.md` bullet at `docs/spec-017-apps-0_0_7.md:419`, the exact bullet text Worker 2 appends under the existing `[0.0.7]` `### Added` subsection (character-for-character; do NOT paraphrase):

```text
- `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`. Consumers list `"django_strawberry_framework"` in `INSTALLED_APPS`; Django's check / signal hooks resolve through the package's AppConfig. No `ready()` body in `0.0.7`.
```

This is the load-bearing wording Worker 3's `### CHANGELOG sanity` review section will `diff` against (per BUILD.md lines 293-302). Worker 2 quotes it verbatim. The `KANBAN.md` Done-body, the GLOSSARY entry body, and the README bullet are NOT the verbatim source — they each describe the shipped contract in their own context per the deliberate non-consolidation flagged in [DRY analysis](#dry-analysis) risk #3; only this CHANGELOG bullet is character-for-character pinned by the spec.

### Test additions / updates

- **None.** Slice 3 ships docs only; no test file is touched.
- The pre-existing live `/graphql/` HTTP tests at `examples/fakeshop/test_query/test_library_api.py` continue to pass unmodified — they exercise the package through `INSTALLED_APPS` end-to-end, which after Slice 1 means they exercise the explicit `DjangoStrawberryFrameworkConfig` (rather than the implicit fallback pre-Slice-1). Per spec Goal 7 / DoD item 7 at `docs/spec-017-apps-0_0_7.md:460`. No edit to the test file; the test continues to pin the contract from a real-world consumer angle.
- The 5 Slice 2 tests at `tests/test_apps.py` continue to pass unmodified; Slice 3 does not touch the test file.

### Implementation discretion items

Items where Worker 1 has assessed and decided the choice belongs to Worker 2 (per BUILD.md "Implementation discretion items" — only stylistic / equivalent-shape preferences, never architectural questions):

- **`docs/GLOSSARY.md` entry-body update vs. leave unchanged.** The existing entry body at `docs/GLOSSARY.md:246-253` is two sentences that already read correctly in the present tense post-Slice-1 (the `name`, `verbose_name`, and `ready()`-omission are not literally in the body text, but the body's broader claim — that `apps.py` ships an AppConfig so consumers can add the package to `INSTALLED_APPS` — is accurate). Worker 2 may either (a) leave the body unchanged and edit only the `**Status:**` line + Index row, OR (b) replace the body's one descriptive sentence with the spec's more detailed wording at `docs/spec-017-apps-0_0_7.md:401`. Lower-friction default: option (a). Higher-detail default: option (b). Either passes the spec's contract.
- **KANBAN past-tense body wording.** The spec's suggested wording at `docs/spec-017-apps-0_0_7.md:415` is a strong default but not mandatory. Worker 2 may match it verbatim or polish for tone consistency with the surrounding `DONE-XXX-0.0.X` cards (compare `DONE-016-0.0.7` body shape; the `Scope:` / `Evidence:` / `Notes:` triplet is the established convention). The contract is "past-tense, names the shipped surface, follows the Done-column body shape"; the exact wording within those constraints is implementer choice.
- **KANBAN `### In progress` paragraph rewording.** The spec at `docs/spec-017-apps-0_0_7.md:416` just says "remove `WIP-ALPHA-017-0.0.7` from the remaining-cards list." Worker 2 owns the natural-language reshape: (a) bump the "five" / "remaining four" framing to "five WIP cards were opened together; two have shipped (`DONE-016-0.0.7` and `DONE-017-0.0.7`) and the remaining three are still in progress," and (b) drop `WIP-ALPHA-017-0.0.7` from the remaining-cards enumeration. The exact sentence shape is at Worker 2's discretion within those two constraints.
- **`docs/TREE.md` current-on-disk-tree comment style for the new `apps.py` entry.** The neighboring entries at `docs/TREE.md:195-201` use a consistent column-aligned `#`-comment style. Worker 2 may match the column alignment exactly (preferred for readability) or use the minimum required spacing (one space before `#`). Lower-friction default: match the column alignment. Higher-friction-but-correct default: same.
- **CHANGELOG bullet wording is NOT at Worker 2's discretion.** Per [Verbatim CHANGELOG wording](#verbatim-changelog-wording) — quote the spec's bullet character-for-character. This is the one fenced item with zero implementer wiggle room because Worker 3's `### CHANGELOG sanity` `diff` check will fail any paraphrase.

Items NOT in Worker 2's discretion (these are spec-pinned and any deviation requires a Worker 1 spec edit through `### Spec changes made (Worker 1 only)`):

- The six file targets exactly: `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md`. No other files are touched. `README.md`, `GOAL.md`, `TODAY.md`, `examples/fakeshop/config/settings.py`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `pyproject.toml` are explicitly NOT modified (per Decisions 6 and 7 and DoD items 9 / 11 / 5).
- The next `DONE-NNN-0.0.7` id is `DONE-017-0.0.7` (highest existing DONE id is 016 — verified by `grep '^### DONE-' KANBAN.md`).
- The three concrete `docs/README.md` actions: heading bump at line 89 (`(0.0.6)` → `(0.0.7)`), bullet add, surgical removal of `, Django ` ``AppConfig`` `` from line 112. The `schema export management command` half MUST remain on line 112 (per rev2 H1 / rev3 L1).
- The `docs/TREE.md` test placement: `tests/test_apps.py` lands BEFORE `test_list_field.py` (alphabetical — `apps` < `list_field`). Per rev2 L1.
- The CHANGELOG append is to the existing `[0.0.7]` `### Added` subsection (NOT a new `[0.0.7]` heading). Per Decision 6 / spec line 419.
- No version bump in this card. The version-string bump in `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, and `tests/base/test_init.py`'s version assertion stays deferred to the last `0.0.7` card to ship (per Decision 6 / DoD item 11).
- Zero new public exports — `__all__` in `django_strawberry_framework/__init__.py` is unchanged (per DoD item 12 / Decision 3 — symmetric with Slice 1's same constraint).

### `scripts/review_inspect.py` disposition for Slice 3

Per BUILD.md "When to run the helper during build" at lines 398-411:

- **Worker 1 (this pass).** Helper NOT run. Slice 3 modifies only Markdown files (`docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md`). The 150-line-and-150-line-of-logic trigger for Worker 1 at BUILD.md line 401 measures Python source files; Markdown is out of scope. Recorded skip.
- **Worker 3 (review pass).** Helper **skipped with reason**: "slice modifies only Markdown files." Per BUILD.md line 411's recorded-skip allowance. The helper parses Python AST and surfaces import / symbol / control-flow / Django-ORM / repeated-string-literal signals; none of these apply to Markdown. Worker 3 records the skip explicitly with this reason.
- **Worker 2.** Helper irrelevant — no `.py` source files touched. No need to invoke even optionally.

### Notes for Worker 3

The `### Documentation / release sanity` review subsection (per BUILD.md lines 304-315) is **load-bearing** for this slice. Slice 3 is the only slice in build-017 that touches docs / release metadata / KANBAN / CHANGELOG surfaces, so this is Worker 3's primary review fence. Mechanical checks Worker 3 must perform:

1. **`diff` the CHANGELOG bullet against the spec's verbatim wording.** Per BUILD.md line 312's "when the slice copies verbatim text from the spec ... confirm character-for-character via `diff` against the spec source." The bullet at the (post-Slice-3) `CHANGELOG.md` `[0.0.7]` `### Added` section must match the spec's wording at `docs/spec-017-apps-0_0_7.md:419` character-for-character. Quoted in [Verbatim CHANGELOG wording](#verbatim-changelog-wording) above; Worker 3 reads both files and confirms equality.
2. **Confirm the GLOSSARY status flip lands in both places.** The entry-level `**Status:**` line at `docs/GLOSSARY.md:248` (currently `planned for 0.0.7`) becomes `shipped (0.0.7)`; the Index table row at `docs/GLOSSARY.md:52` (currently `planned for 0.0.7`) becomes `shipped (0.0.7)`. Worker 3 reads both lines post-edit and confirms the flip in both places. Mirror the format used by `DjangoListField` at `docs/GLOSSARY.md:59` / `docs/GLOSSARY.md:302`.
3. **Confirm the KANBAN move is single-instance.** Per BUILD.md line 310 ("moved KANBAN cards are removed from their old section and appear in the target section exactly once"), Worker 3 reads `KANBAN.md` post-edit and confirms: (a) the `WIP-ALPHA-017-0.0.7` heading is no longer in the `## In progress` column, (b) a `### DONE-017-0.0.7` heading appears exactly once in the `## Done` column, (c) the `### In progress` summary paragraph at `KANBAN.md:50` no longer enumerates `WIP-ALPHA-017-0.0.7` in the remaining-cards list, (d) the past-tense body follows the established Done-column shape.
4. **Confirm the surgical `docs/README.md:112` edit.** This is the most defect-prone edit in the slice. Worker 3 reads `docs/README.md:112` post-edit and confirms the line is exactly `- schema export management command` — neither the entire line was deleted nor was `schema export management command` removed. A regex sanity-check: `grep -n "schema export management command" docs/README.md` should still return exactly one match; `grep -n "Django \`AppConfig\`" docs/README.md` should NOT return the line-112 match (the line-99 `Django AppConfig` bullet from Edit (b) IS expected to remain).
5. **Confirm no version bump.** Worker 3 reads `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__` line, and `tests/base/test_init.py`'s version assertion — all three must still be `0.0.6` (NOT `0.0.7`) per Decision 6.
6. **Confirm `tests/test_apps.py` placement in `docs/TREE.md`.** The current-on-disk-tree section at `docs/TREE.md:330-360` should list `test_apps.py` BEFORE `test_list_field.py` (alphabetical — `apps` < `list_field`). Per rev2 L1.

The `### CHANGELOG sanity` review subsection (per BUILD.md lines 293-302) is also load-bearing because this slice touches `CHANGELOG.md`. Worker 3's checks per BUILD.md lines 296-300:
- The version line `## [0.0.7]` matches the package version after the slice. Note: per Decision 6 the version-string bump is deferred to the last `0.0.7` card; the `[0.0.7]` heading is correct because it's a release-bucket marker, not a `pyproject.toml` echo. Worker 3 confirms the `[0.0.7]` heading is unchanged from its pre-slice form (only the `### Added` bullet list grows).
- `### Added` is the right heading — the slice ships an addition, not a Changed / Fixed / Removed.
- The bullet wording matches the spec's canonical phrasing (per [Verbatim CHANGELOG wording](#verbatim-changelog-wording)).
- The bullet does not overstate or understate the change.

### Spec slice checklist (verbatim)

The spec's Slice 3 nested sub-bullets from `## Slice checklist` at `docs/spec-017-apps-0_0_7.md:67-79`, copied verbatim as `- [ ]` boxes (preserve exact text, nested sub-bullets, inline citations). Worker 1 ticks each `- [x]` during final verification as the contract lands. An unticked box at final verification is either deferred with a one-line reason under `### Spec changes made (Worker 1 only)` or the slice goes `revision-needed`. Worker 3 walks this list during review; a sub-check that appears silently un-addressed in the diff is a Medium finding per BUILD.md line 382.

- [x] Slice 3: Promotion + docs
  - [x] Flip [`Django AppConfig`](GLOSSARY.md#django-appconfig) from `planned for 0.0.7` to `shipped (0.0.7)` in [`docs/GLOSSARY.md`](GLOSSARY.md); update the Index table's status column.
  - [x] Update [`docs/README.md`](README.md) (rev3 L1 — replaced the rev1 generic "move the mention" wording with the surgical rev2 H1 actions; the entry-point checklist must match the [Doc updates](#doc-updates) section instead of relying on it to override): (a) **bump the shipped-list heading** at line 89 from `**Shipped today** (`0.0.6`):` to `**Shipped today** (`0.0.7`):` (catch-up against `DONE-016`'s heading-drift; distinct from the version-string bump deferred to [Decision 6](#decision-6--joint-0_0_7-cut)); (b) add the `Django AppConfig` bullet to that section with the wording in [Doc updates](#doc-updates); (c) **surgically remove only `, Django `AppConfig`** from the existing `Coming in 0.1.0` bullet at line 112, leaving `- schema export management command` intact for `WIP-ALPHA-018-0.0.7` to remove later (do NOT remove the whole line; do NOT remove the schema-export half).
  - [x] Update [`docs/TREE.md`](TREE.md) — add `apps.py # AppConfig` to the **current on-disk layout** section under the `django_strawberry_framework/` tree (alphabetical position between `__init__.py` and `conf.py`). Remove the `[alpha]` tag from the existing `apps.py # [alpha] Django AppConfig` line in the **target package layout** section (line `docs/TREE.md:236`); the tag means "lands before `0.1.0`", and the bullet has now landed. Add `tests/test_apps.py` to the current test-tree section under the `tests/` listing.
  - [x] Update [`KANBAN.md`](../KANBAN.md) — move `WIP-ALPHA-017-0.0.7` to the Done column with the next `DONE-NNN-0.0.7` id; rewrite the body in past tense per the existing Done-column convention.
  - [x] Update [`CHANGELOG.md`](../CHANGELOG.md) — **append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading per [`spec-016`](SPECS/spec-016-list_field-0_0_7.md) Decision 10 — every `0.0.7` card under the joint cut appends to the same shared section): `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` so consumers can list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's check / signal hooks resolve through the package's AppConfig.
  - [x] No edits to [`README.md`](../README.md), [`GOAL.md`](../GOAL.md), or [`TODAY.md`](../TODAY.md). Justification: the AppConfig is plumbing, not a consumer-visible API surface. `README.md`'s status section names features consumers write code against; `GOAL.md`'s six-file example does not exercise `INSTALLED_APPS`; `TODAY.md`'s capability snapshot is about what GraphQL queries work — none of those framings is touched by the AppConfig landing.
  - [x] Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; per [Decision 6](#decision-6--joint-0_0_7-cut)): see [`spec-016`](SPECS/spec-016-list_field-0_0_7.md) Decision 10. This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s version assertion.
  - [x] Final gates (rev6 L2 — aligned with [`docs/builder/BUILD.md`](builder/BUILD.md)'s "Coverage is the maintainer's gate, not a worker's tool" rule at BUILD.md lines 98-111 and the final test-run gate's `uv run pytest --no-cov` shape at BUILD.md line 539; rev1-rev5 prose said plain `uv run pytest` with "100% package coverage" assertion, which would either auto-apply `--cov` via `pytest.ini` and run forbidden coverage, or invite a worker to assert coverage that is the CI / maintainer's gate, not the worker's):
    - [x] `uv run ruff format .` passes (Worker 2's per-pass gate per BUILD.md line 247).
    - [x] `uv run ruff check --fix .` passes (Worker 2's per-pass gate per BUILD.md line 247).
    - [x] `uv run pytest --no-cov` (or scoped subset) passes; the explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per BUILD.md line 109's "the only permitted coverage-shaped flag." Coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`), not this slice's; workers verify the suite passes, not that coverage stays at 100%.
    - [x] Zero new public exports (the AppConfig is import-time plumbing, not a public symbol); `__all__` in `django_strawberry_framework/__init__.py` is unchanged.

---

## Build report (Worker 2)

### Files touched

- `docs/GLOSSARY.md` — flipped the [Django `AppConfig`](../GLOSSARY.md#django-appconfig) entry's `**Status:** planned for 0.0.7.` line to `**Status:** shipped (0.0.7).` and replaced the one-sentence entry body with the spec's more detailed shipped-contract wording from `docs/spec-017-apps-0_0_7.md:401` (option (b) per [Implementation discretion items](#implementation-discretion-items)) so the entry body now names `DjangoStrawberryFrameworkConfig`, the `name` / `verbose_name` values, the no-`ready()` posture, and the implicit single-AppConfig discovery contract; flipped the Index table's status column at `docs/GLOSSARY.md:52` from `planned for 0.0.7` to `shipped (0.0.7)`, mirroring the [`DjangoListField`](../GLOSSARY.md#djangolistfield) row format at `docs/GLOSSARY.md:59`.
- `docs/README.md` — bumped the shipped-list heading at line 89 from `**Shipped today** (0.0.6):` to `**Shipped today** (0.0.7):` (rev2 H1 catch-up against `DONE-016-0.0.7`'s heading-drift, distinct from the version-string bump deferred to Decision 6); added the `Django AppConfig` bullet at the bottom of the shipped-today list using the spec's exact wording at `docs/spec-017-apps-0_0_7.md:406`; surgically removed only `, Django `AppConfig`` from line 112 so the line is now `- schema export management command` (leaving the schema-export half intact for `WIP-ALPHA-018-0.0.7` to remove later per rev2 H1 / rev3 L1).
- `docs/TREE.md` — added `├── apps.py                  # AppConfig` to the current on-disk layout between `├── __init__.py` and `├── conf.py` (alphabetical position, column-aligned with the existing siblings); removed the `[alpha]` tag from the existing `apps.py # [alpha] Django AppConfig` line in the target package layout (the tag means "lands before `0.1.0`"; the bullet has now landed); added `├── test_apps.py             # AppConfig (single-file Layer-3 module)` to the current test-tree section BEFORE `test_list_field.py` (alphabetical — `apps` < `list_field`, per rev2 L1's correction of the rev1 misplacement).
- `KANBAN.md` — moved `WIP-ALPHA-017-0.0.7 — apps.py and Django app config` from the `## In progress` column to the `## Done` column with id `DONE-017-0.0.7` (next sequential after the existing `DONE-016-0.0.7`); rewrote the body in past tense per the `DONE-016-0.0.7` shape (prose paragraphs, ending with a `Files touched:` line and a `Spec:` / `Build plan:` line — not the older `Scope:` / `Evidence:` / `Notes:` triplet, since `DONE-016-0.0.7` is the immediate-prior shipped card and sets the freshest local convention); updated the `### In progress` summary paragraph at `KANBAN.md:50` to reflect that two `0.0.7` cards have now shipped (`DONE-016-0.0.7` and `DONE-017-0.0.7`) and three remain in progress (018 / 019 / 045), dropping `WIP-ALPHA-017-0.0.7` from the remaining-cards enumeration.
- `CHANGELOG.md` — appended one bullet to the existing `[0.0.7]` `### Added` subsection (NOT a second `[0.0.7]` heading per Decision 6) using the spec's verbatim wording from `docs/spec-017-apps-0_0_7.md:419`: ``- `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`. Consumers list `"django_strawberry_framework"` in `INSTALLED_APPS`; Django's check / signal hooks resolve through the package's AppConfig. No `ready()` body in `0.0.7`.``
- `docs/builder/bld-slice-3-promotion_docs.md` — appended this Build report section; set `Status: built`.

### Tests added or updated

None; slice is docs-only per spec.

### Validation run

- `uv run ruff format .` — pass ("105 files left unchanged"); the conflicting-rule `COM812` warning is the standing pre-existing warning surfaced on every Worker 2 pass in this build (also reported in Slice 1 and Slice 2's build reports), not introduced by this slice's edits.
- `uv run ruff check --fix .` — pass ("All checks passed!"); no autofixes applied.
- `git status --short` after both ruff invocations — modified files are exactly: `CHANGELOG.md`, `KANBAN.md`, `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md` (the five slice-intended doc files); `django_strawberry_framework/apps.py` and `tests/test_apps.py` (carried in from Slice 1 / Slice 2, pre-existing in the working tree per the build's per-slice non-commit posture); plus the four artifact files under `docs/builder/` (this slice's `bld-slice-3-promotion_docs.md`, the prior slices' `bld-slice-1-module_appconfig.md` / `bld-slice-2-tests.md`, and the build plan `build-017-apps-0_0_7.md`). No unrelated tool churn; nothing to revert.
- No `pytest` run; the spec's Slice 3 final gates allow `uv run pytest --no-cov` but explicitly note it as scoped / optional for a docs-only slice (per spec line 78 and the plan's [Implementation steps](#implementation-steps) step 6 note "this slice ships ZERO `.py` file changes, so `pytest` is mechanically irrelevant"). The final test-run gate at `docs/builder/bld-final.md` will run the full sweep.

### Implementation notes

- **`docs/GLOSSARY.md` entry-body update — chose option (b) from [Implementation discretion items](#implementation-discretion-items).** Replaced the existing one-sentence body with the spec's more detailed wording from `docs/spec-017-apps-0_0_7.md:401`. The lower-friction option (a) (leave the body unchanged) would have left the body accurate but generic; option (b) names `DjangoStrawberryFrameworkConfig`, the two attribute values, and the no-`ready()` posture, all of which are load-bearing for a reader landing on the glossary entry directly. The choice mirrors the symmetric [`DjangoListField`](../GLOSSARY.md#djangolistfield) entry at `docs/GLOSSARY.md:300-306`, which carries its full shipped-contract description in the entry body.
- **KANBAN past-tense body wording — followed the `DONE-016-0.0.7` shape (prose paragraphs ending with `Files touched:` + `Spec:` / `Build plan:`) rather than the older `Scope:` / `Evidence:` / `Notes:` triplet from `DONE-001` through `DONE-015`.** `DONE-016-0.0.7` is the immediate-prior shipped card and sets the freshest local convention; the plan's [Implementation discretion items](#implementation-discretion-items) authorized either shape. The prose-paragraph form also fits the spec's suggested past-tense wording at `docs/spec-017-apps-0_0_7.md:415` more naturally (one sentence summarizing the shipped surface vs. a triplet of structured fields).
- **KANBAN `### In progress` paragraph rewording — used the suggested "two have shipped … remaining three are still in progress" reshape from the plan's [Implementation discretion items](#implementation-discretion-items).** This matches the natural progression from the original "Five WIP cards … `DONE-016-0.0.7` shipped first, and the remaining four are still in progress" phrasing — only the counts and the enumeration shift. Both `DONE-016-0.0.7` and `DONE-017-0.0.7` are now named in the same parenthetical, parallel to the original's `DONE-016-0.0.7` mention.
- **CHANGELOG bullet inserted directly under the existing `DjangoListField` bullet, both under the same `[0.0.7]` `### Added` heading.** No `### Changed` / `### Fixed` / `### Removed` heading added — the slice ships pure addition. The verbatim wording from `docs/spec-017-apps-0_0_7.md:419` was used character-for-character per the plan's load-bearing [Verbatim CHANGELOG wording](#verbatim-changelog-wording) pin.

### Notes for Worker 3

- **Surgical `docs/README.md:112` edit is the most defect-prone surface in this slice.** The line is now exactly `- schema export management command`; the deleted substring was `, Django ` ``AppConfig`` `` (leading comma + space + bare-words + backticked `AppConfig` token). The plan's [Notes for Worker 3](#notes-for-worker-3) check #4 names the regex sanity-check shape: `grep -n "schema export management command" docs/README.md` must still return one match (the post-edit line 112 plus the pre-existing `WIP-ALPHA-018-0.0.7` card body in `KANBAN.md` is unrelated); `grep -n "Django \`AppConfig\`" docs/README.md` must NOT return the line-112 match (the line-100 `Django AppConfig` shipped-bullet from Edit (b) IS expected to remain because the README's new bullet uses the literal `Django AppConfig` token).
- **CHANGELOG verbatim `diff` is the other load-bearing review surface.** Worker 3's `### CHANGELOG sanity` review section will `diff` the appended CHANGELOG bullet against `docs/spec-017-apps-0_0_7.md:419`. Both strings should match character-for-character; no paraphrase was applied.
- **No `scripts/review_inspect.py` invocation expected for this slice.** Per the plan's [`scripts/review_inspect.py` disposition for Slice 3](#scripts-review_inspect-py-disposition-for-slice-3): the slice modifies only Markdown files, so the helper's AST / Python-marker analysis is mechanically irrelevant. Record a skip with reason "slice modifies only Markdown files" per BUILD.md line 411's recorded-skip allowance.
- **Version-bump constraint per Decision 6.** No files outside the five doc targets were touched. Specifically: `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__` line, and `tests/base/test_init.py`'s version assertion all remain at `0.0.6`. `README.md`, `GOAL.md`, and `TODAY.md` are also unchanged.

### Notes for Worker 1 (spec reconciliation)

None.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- Confirmed the deliberate non-consolidations from the Plan's [DRY analysis](#dry-analysis) risk #3 hold in the diff: the repeated literals `"django_strawberry_framework"`, `"Django Strawberry Framework"`, and `DjangoStrawberryFrameworkConfig` appear across GLOSSARY entry body / README bullet / KANBAN body / CHANGELOG bullet, each pinning its own contract in its own context. Factoring through a shared include would break the durability contract each doc carries individually; the parallel reasoning matches the Slice 1 / Slice 2 non-consolidations recorded in worker-3 memory.
- The CHANGELOG bullet at `CHANGELOG.md:24` and the README bullet at `docs/README.md:104` carry overlapping wording but the README bullet adds the `(new in 0.0.7)` provenance tag and trims the no-`ready()` half, while the CHANGELOG bullet carries the `name = ... and verbose_name = ...` value enumeration and the explicit `No ready() body in 0.0.7.` sentence. Distinct context pins, no actionable duplication.
- The KANBAN `DONE-017-0.0.7` body at `KANBAN.md:1743` restates the shipped surface in past-tense prose; this is deliberately divergent from the CHANGELOG entry's release-history phrasing and from the GLOSSARY entry's reference-style phrasing. Plan-authorized non-consolidation; no finding.

### Public-surface check

- `git diff -- django_strawberry_framework/__init__.py` is empty. `__all__` is unchanged per [Decision 3](../spec-017-apps-0_0_7.md#decision-3--no-public-export) / DoD item 2 / DoD item 12.
- `git diff -- tests/base/test_init.py` is empty. The `__all__` assertion at `tests/base/test_init.py:35-44` is unchanged per DoD item 3.
- `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__` line, and `tests/base/test_init.py`'s version assertion remain at `0.0.6` per [Decision 6](../spec-017-apps-0_0_7.md#decision-6--joint-0_0_7-cut) / DoD item 11 (verified by `grep -n 'version' pyproject.toml` and `grep -n '__version__' django_strawberry_framework/__init__.py` — both report `0.0.6`).

### CHANGELOG sanity

- **Verbatim wording matches the spec character-for-character.** `diff`-ed line 24 of `CHANGELOG.md` against the spec's wording at `docs/spec-017-apps-0_0_7.md:419` (the post-colon trailing content): the only delta is the `- ` list-marker prefix the CHANGELOG carries because the line is a bullet — the spec's wording is the prose substring after the colon, and that substring is identical character-for-character.
- **Exactly one `[0.0.7]` heading.** `grep -c '^## \[0.0.7\]' CHANGELOG.md` returns `1`. The slice appends to the existing `[0.0.7] - 2026-05-20` heading at `CHANGELOG.md:21`; no second heading was introduced per [Decision 6](../spec-017-apps-0_0_7.md#decision-6--joint-0_0_7-cut) / spec line 419.
- **Version-string bump correctly deferred.** `pyproject.toml:4` is `version = "0.0.6"` and `django_strawberry_framework/__init__.py:26` is `__version__ = "0.0.6"`; the `[0.0.7]` heading is a release-bucket marker (set by `DONE-016-0.0.7`), not a `pyproject.toml` echo. The version-string bump stays deferred to the last `0.0.7` card to ship per [Decision 6](../spec-017-apps-0_0_7.md#decision-6--joint-0_0_7-cut) / DoD item 11.
- **`### Added` is the appended subsection.** The new bullet sits at `CHANGELOG.md:24`, directly under the existing `DjangoListField` bullet at line 23 and under the `### Added` heading at line 22. No `### Changed` / `### Fixed` / `### Removed` heading was added — the slice ships pure addition per the spec.
- **Wording does not overstate or understate.** Names `DjangoStrawberryFrameworkConfig`, the two attribute values, the `INSTALLED_APPS` registration path, and the no-`ready()` posture — exactly the shipped contract from Slices 1 & 2.

### Documentation / release sanity

- **`docs/GLOSSARY.md` status flip lands in BOTH places.**
  - Index-table row at `docs/GLOSSARY.md:52` flipped from `planned for 0.0.7` to `shipped (0.0.7)`, mirroring the `DjangoListField` row format at line 59.
  - Entry-level `**Status:**` line at `docs/GLOSSARY.md:248` flipped from `planned for 0.0.7.` to `shipped (0.0.7).`, mirroring the `DjangoListField` entry-level flip at line 302.
  - Entry body at `docs/GLOSSARY.md:250` was also updated to the spec's more detailed shipped-contract wording (option (b) per the Plan's [Implementation discretion items](#implementation-discretion-items)) — names `DjangoStrawberryFrameworkConfig`, the two attribute values, the no-`ready()` posture, and the implicit single-AppConfig discovery contract. Plan-authorized choice; no finding.
  - Nothing else changed in the file (`See also:` line at line 252 unchanged).
- **`docs/README.md:89` heading bump.** Confirmed `(0.0.6)` → `(0.0.7)` at line 89; the rev2 H1 catch-up against `DONE-016-0.0.7`'s heading-drift landed correctly.
- **`docs/README.md:113` surgical removal.** The line is now exactly `- schema export management command` (verified via `grep -n 'schema export management command' docs/README.md` returning a single match at line 113); the substring `, Django ` ``AppConfig`` `` was excised cleanly. The `schema export management command` half is preserved for `WIP-ALPHA-018-0.0.7` to remove when it ships. Line shifted from 112 to 113 because the new shipped-list bullet at line 104 pushed everything down by one — expected.
- **`docs/README.md:104` AppConfig bullet.** Added at the bottom of the `**Shipped today**` bulleted list, after the existing last bullet (the `annotation-only and strawberry.field consumer overrides` line) and before the blank line preceding `**Coming in 0.1.0**`. Wording matches the spec at line 406 character-for-character.
- **`docs/TREE.md` current on-disk layout — `apps.py` placement.** Added at line 197 between `py.typed` (line 196) and `conf.py` (line 198). The spec said "between `__init__.py` and `conf.py`" — `py.typed` sits between the two but is a packaging marker, not a `.py` source file; the existing target-layout precedent at lines 234-238 puts `py.typed` immediately after `__init__.py` (likely the canonical Python-packaging convention), so the current-layout placement matches the target-layout precedent and the alphabetical-among-source-files constraint. Acceptable.
- **`docs/TREE.md` target-layout `[alpha]` tag removed.** Line 237 went from `apps.py # [alpha] Django AppConfig` to `apps.py # Django AppConfig`. The tag means "lands before `0.1.0`"; the bullet has now landed.
- **`docs/TREE.md` current test-tree — `test_apps.py` placement.** Added at line 333, BEFORE `test_list_field.py` (line 334) — alphabetical (`apps` < `list_field`) per the rev2 L1 correction. Not placed between `test_list_field.py` and `test_registry.py` (which would have been the rev1 misplacement).
- **`KANBAN.md` move is single-instance.** Verified `grep -n 'WIP-ALPHA-017\|DONE-017' KANBAN.md`: `WIP-ALPHA-017-0.0.7` no longer appears in the file; `DONE-017-0.0.7` appears exactly twice — once at line 50 in the `### In progress` summary paragraph as a shipped-cards reference, and once at line 1743 as the Done-column heading itself. The `### In progress` board column at lines 75-87 no longer has a `WIP-ALPHA-017-0.0.7` body (the old body was 11 lines; those lines are gone).
- **`KANBAN.md` summary paragraph at line 50.** Reshaped to "Five WIP cards … two have shipped (`DONE-016-0.0.7` and `DONE-017-0.0.7`) and the remaining three are still in progress" with `WIP-ALPHA-017-0.0.7` dropped from the enumeration; matches the Plan's discretion-item reshape pattern.
- **`KANBAN.md` Done-body shape.** The new `DONE-017-0.0.7` body at lines 1743-1753 follows the prose-paragraph shape of `DONE-016-0.0.7` (the immediate-prior shipped card) — three prose paragraphs ending with `Files touched:` and `Spec:` / `Build plan:` lines. Past-tense, names the shipped surface, follows the established freshest-local convention. Plan-authorized discretion item; no finding.
- **No version bump in this card.** Verified: `pyproject.toml:4` is `version = "0.0.6"`; `django_strawberry_framework/__init__.py:26` is `__version__ = "0.0.6"`. Per [Decision 6](../spec-017-apps-0_0_7.md#decision-6--joint-0_0_7-cut) / DoD item 11.
- **`README.md`, `GOAL.md`, `TODAY.md`, `examples/fakeshop/config/settings.py` unchanged.** Verified by `git status --short` — none of these files appear in the modified list.

### What looks solid

- The verbatim CHANGELOG bullet matches the spec's wording at `docs/spec-017-apps-0_0_7.md:419` character-for-character, with the only delta being the bullet's leading `- ` list marker (mechanical, expected). Worker 2 quoted it cleanly without paraphrase.
- The surgical `docs/README.md:113` edit (the slice's most defect-prone surface per the Plan's Notes for Worker 3) landed exactly as planned: `, Django ` ``AppConfig`` `` removed; `schema export management command` preserved for `WIP-ALPHA-018-0.0.7` to handle.
- The KANBAN move is clean: zero residual `WIP-ALPHA-017-0.0.7` references, exactly one `DONE-017-0.0.7` Done-column heading, past-tense body, summary paragraph reshaped to drop the moved card from the in-progress enumeration.
- The GLOSSARY status flip is symmetric — both the Index-table row AND the entry-level status line moved from `planned for 0.0.7` to `shipped (0.0.7)`, mirroring the `DjangoListField` flip pattern from `DONE-016-0.0.7`.
- The `docs/TREE.md` placement of `test_apps.py` correctly honors the rev2 L1 alphabetical fix (`apps` < `list_field`), not the rev1 misplacement.
- The slice ships zero `.py` file changes (the `apps.py` / `test_apps.py` modifications in `git status --short` are carry-forward from Slices 1 & 2, recognized correctly by the Plan's cumulative-diff trap awareness), so the `scripts/review_inspect.py` skip with reason "slice modifies only Markdown files" is appropriate.
- Public-surface is untouched: `__all__` unchanged, `tests/base/test_init.py` unchanged, version pinned at `0.0.6`.

### Temp test verification

None; no temp tests used. The slice ships docs-only edits; behavioral coverage was already pinned by Slice 2's 5 tests at `tests/test_apps.py`, and the existing live `/graphql/` HTTP tests at `examples/fakeshop/test_query/test_library_api.py` continue to exercise the package through `INSTALLED_APPS` end-to-end (post-Slice-1 they exercise the explicit AppConfig automatically per Django's single-AppConfig discovery).

### `scripts/review_inspect.py` disposition

Helper **skipped with reason "slice modifies only Markdown files."** Per BUILD.md line 411's recorded-skip allowance. Verified by `git diff --stat` against the slice-touched targets: the five Slice 3 doc files are all `.md`, and the `.py` modifications in `git status --short` (`django_strawberry_framework/apps.py` and `tests/test_apps.py`) carry over from Slices 1 & 2 (independently reviewed in their own artifacts) — they are not in this slice's diff per the artifact's `### Files touched` filter and the BUILD.md cumulative-diff-trap guidance. The helper parses Python AST and surfaces import / symbol / control-flow / Django-ORM / repeated-string-literal signals; none apply to Markdown.

### Spec slice checklist (verbatim)

Walked every `- [ ]` from the Plan's `### Spec slice checklist (verbatim)` against the diff:

- GLOSSARY status flip + Index-table update — addressed at `docs/GLOSSARY.md:52` and `docs/GLOSSARY.md:248`.
- README heading bump + bullet add + surgical removal (the three rev3 L1 concrete actions) — addressed at `docs/README.md:89`, `docs/README.md:104`, `docs/README.md:113`.
- TREE current-layout add + target-layout `[alpha]` removal + tests current-tree add — addressed at `docs/TREE.md:197`, `docs/TREE.md:237`, `docs/TREE.md:333`.
- KANBAN move with `DONE-NNN-0.0.7` id + past-tense body rewrite — addressed at `KANBAN.md:1743` (move) and `KANBAN.md:50` (summary paragraph).
- CHANGELOG append to existing `[0.0.7]` `### Added` — addressed at `CHANGELOG.md:24`.
- No edits to `README.md` / `GOAL.md` / `TODAY.md` — confirmed clean (`git status --short` shows no diff for these files).
- Version bump deferred — confirmed `pyproject.toml`, `__version__`, and `tests/base/test_init.py` all unchanged at `0.0.6`.
- Final gates `ruff format` / `ruff check --fix` / `pytest --no-cov` / zero new public exports — the Build report records `ruff format .` and `ruff check --fix .` both pass; `pytest` was not run for the docs-only slice per the spec's "scoped / optional" allowance for docs-only slices; public-surface check above confirms zero new exports.

Every spec-required sub-check is reflected in the diff. No silently-unaddressed sub-check.

### Notes for Worker 1 (spec reconciliation)

None. The diff matches the spec verbatim where verbatim was required and matches the plan-authorized discretion items where discretion was allowed. No spec edits are warranted from this review pass.

### Review outcome

`review-accepted`. Every High / Medium / Low finding is `None.`; every spec-slice sub-check is addressed in the diff; the verbatim CHANGELOG wording matches character-for-character; the surgical README edit and the KANBAN move both landed exactly as planned; the helper skip is correctly recorded; public surface is untouched.

---

## Final verification (Worker 1)

- **Spec slice checklist:** every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` is now `- [x]`. Walked each box against the Slice 3 diff (`git diff -- docs/GLOSSARY.md docs/README.md docs/TREE.md KANBAN.md CHANGELOG.md`):
  - GLOSSARY status flip — landed at `docs/GLOSSARY.md:52` (Index row `planned for 0.0.7` → `shipped (0.0.7)`) and `docs/GLOSSARY.md:248` (entry-level `**Status:**` line); entry body at `docs/GLOSSARY.md:250` also updated to the spec's detailed shipped-contract wording (Plan-authorized discretion item).
  - README three rev3 L1 surgical actions — heading bump at `docs/README.md:89` (`(0.0.6)` → `(0.0.7)`), `Django AppConfig` bullet added at `docs/README.md:104` matching the spec's exact wording at `docs/spec-017-apps-0_0_7.md:406`, and surgical removal of `, Django `AppConfig`` from the `Coming in 0.1.0` bullet — the line now reads exactly `- schema export management command` (verified by `grep -n 'schema export management command' docs/README.md` returning one match at line 113; the schema-export half is preserved for `WIP-ALPHA-018-0.0.7`).
  - TREE three edits — `apps.py # AppConfig` added to the current on-disk layout at line 197, `[alpha]` tag removed from the target-layout `apps.py` entry at line 237, `test_apps.py` added to the current test-tree at line 333 BEFORE `test_list_field.py` (alphabetical, per rev2 L1).
  - KANBAN move — `WIP-ALPHA-017-0.0.7` removed from the In progress board column, `DONE-017-0.0.7` heading added once in the Done column with past-tense prose body following the `DONE-016-0.0.7` shape; `### In progress` summary paragraph at `KANBAN.md:50` reshaped from "remaining four" to "remaining three" with `WIP-ALPHA-017-0.0.7` dropped from the enumeration.
  - CHANGELOG append — one bullet added under the existing `[0.0.7]` `### Added` heading at `CHANGELOG.md:24`, character-for-character matching the spec's wording at `docs/spec-017-apps-0_0_7.md:419`. Exactly one `## [0.0.7]` heading in the file (no parallel second heading per Decision 6).
  - No edits to `README.md` / `GOAL.md` / `TODAY.md` — `git status --short` confirms none of these files appear in the working tree's modified list.
  - Version bump deferred — `pyproject.toml` `version`, `django_strawberry_framework/__init__.py` `__version__`, and `tests/base/test_init.py`'s version assertion all remain at `0.0.6` (verified via `grep`). The `[0.0.7]` CHANGELOG heading is a release-bucket marker set by `DONE-016-0.0.7`, not a version-string echo.
  - Final gates — `uv run ruff format .` and `uv run ruff check --fix .` pass per the Build report; `uv run pytest --no-cov tests/ -x -q` passes locally on this final-verification spawn (690 passed, 2 skipped); the live `/graphql/` HTTP suite `uv run pytest --no-cov examples/fakeshop/test_query/ -x -q` passes (11 passed) — Goal 7 / DoD item 7's "explicit AppConfig exercised through the existing `INSTALLED_APPS` entry" contract held. Full `uv run pytest --no-cov -x -q` sweep also passes (764 passed, 2 skipped). Zero new public exports — `git diff -- django_strawberry_framework/__init__.py` is empty and `__all__` is unchanged.

  Every box landed; no deferrals are needed.

- **DRY check across this slice and prior accepted slices.** Walked the Slice 3 diff against the Slice 1 + Slice 2 deliberate non-consolidations carried in worker-1 memory:
  - The `"Django Strawberry Framework"` / `"django_strawberry_framework"` / `DjangoStrawberryFrameworkConfig` repetitions across `docs/GLOSSARY.md` (entry body), `docs/README.md` (shipped-list bullet), `KANBAN.md` (`DONE-017-0.0.7` body), and `CHANGELOG.md` (`### Added` bullet) are the Plan's [DRY analysis](#dry-analysis) risk #3 — deliberate non-consolidation. Each doc pins its own contract in its own context (capability reference / consumer-quickstart status / per-card audit trail / release history); factoring through a shared include would break the durability contract each doc carries individually. Parallel reasoning to Slice 1's `apps.py:9` / `__init__.py:16` `"django_strawberry_framework"` non-consolidation and Slice 2's 3x repetition in `tests/test_apps.py`. Confirmed appropriate.
  - The CHANGELOG bullet at `CHANGELOG.md:24` and the README bullet at `docs/README.md:104` carry overlapping wording but the README bullet adds the `(new in 0.0.7)` provenance tag and trims the no-`ready()` half, while the CHANGELOG bullet carries the `name = ... and verbose_name = ...` value enumeration and the explicit `No ready() body in 0.0.7.` sentence. Distinct context pins, not duplication.
  - The KANBAN `DONE-017-0.0.7` body restates the shipped surface in past-tense prose; deliberately divergent from the CHANGELOG's release-history phrasing and the GLOSSARY's reference-style phrasing. Plan-authorized non-consolidation per the discretion items.
  - No new duplication relative to Slice 1 or Slice 2; Worker 3's review reached the same conclusion under `### DRY findings`.

- **Existing tests still pass.** Slice 3 ships no `.py` changes, but the spec's Goal 7 / DoD item 7 contract requires the live `/graphql/` HTTP suite to keep working through `examples/fakeshop/config/settings.py:48`'s `INSTALLED_APPS` entry now that the explicit AppConfig resolves under it. Verified on this spawn:
  - `uv run pytest --no-cov tests/ -x -q` → 690 passed, 2 pre-existing skips, 0 failures.
  - `uv run pytest --no-cov examples/fakeshop/test_query/ -x -q` → 11 passed (live HTTP suite continues to pass under the explicit AppConfig).
  - `uv run pytest --no-cov -x -q` (full sweep across all three test trees) → 764 passed, 2 skipped.
  - All commands honored the `--no-cov` opt-out per BUILD.md "Coverage is the maintainer's gate, not a worker's tool" at lines 98-111.

- **Spec reconciliation.** Worker 2's `### Notes for Worker 1 (spec reconciliation)` reads `None.` and Worker 3's reads `None. The diff matches the spec verbatim where verbatim was required and matches the plan-authorized discretion items where discretion was allowed. No spec edits are warranted from this review pass.` Re-read the spec's status / header lines (lines 1-5): `Status: draft (revision 6, post-rev5 build-readiness audit)` still accurate — Slice 3 ships docs only and the spec's revision-6 status describes a build-ready spec; the integration pass + final test-run gate still remain, so the draft framing is correct for the active-build state. No spec edit performed.

- **Final status:** `final-accepted`.

### Summary

Slice 3 shipped the promotion + docs sweep cleanly: `docs/GLOSSARY.md` flipped [`Django AppConfig`](../GLOSSARY.md#django-appconfig) from `planned for 0.0.7` to `shipped (0.0.7)` (both Index-row and entry-level `**Status:**` line) and replaced the one-sentence body with the spec's detailed shipped-contract wording; `docs/README.md` bumped the shipped-list heading to `(0.0.7)`, added the `Django AppConfig` bullet, and surgically removed only `, Django `AppConfig`` from the `Coming in 0.1.0` line (leaving `- schema export management command` intact for `WIP-ALPHA-018-0.0.7`); `docs/TREE.md` added `apps.py` to the current on-disk layout, removed the `[alpha]` tag from the target-layout entry, and added `tests/test_apps.py` to the current test-tree section before `test_list_field.py`; `KANBAN.md` moved `WIP-ALPHA-017-0.0.7` to Done as `DONE-017-0.0.7` (past-tense prose body following `DONE-016-0.0.7`'s shape) and reshaped the In-progress summary paragraph from "remaining four" to "remaining three"; and `CHANGELOG.md` appended one new bullet under the existing `[0.0.7]` `### Added` heading using the spec's verbatim wording. No `.py` source changed; full pytest sweep passes (764 passed, 2 skipped); the live `/graphql/` HTTP suite continues to pass through the explicit AppConfig now resolved by `examples/fakeshop/config/settings.py:48`'s `INSTALLED_APPS` entry.

### Spec changes made (Worker 1 only)

None.
````
