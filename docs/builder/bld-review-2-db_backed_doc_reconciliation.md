# Build: Review round 2 — R2 DB-backed doc reconciliation + stale test-comment provenance

Spec reference: `docs/SPECS/spec-021-apps-0_0_7.md` (`final-accepted` by R1 this cycle; **closed to this cohort** — R2 must not edit it or its `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` companion)
Plan reference: `docs/builder/build-021-apps-0_0_7.md` `## Verified findings` (F5, F6, F8; **F9 does not hold** — see `### F9 is not this cohort's work` below)
Status: final-accepted

## Plan (Worker 1)

R2 of a **review round** (`BUILD.md` `## Review rounds`), running the ordinary Worker 1 -> 2 -> 3 -> 1 chain. Three findings, three sites, two of which are rows in `examples/fakeshop/db.sqlite3` rather than lines in the rendered markdown a naive reading of the findings names.

**Ownership partition for this cohort** (`build-021-apps-0_0_7.md` `## Declarations`, as amended when `tests/test_apps.py` was folded in). R2 owns exactly:

- `examples/fakeshop/db.sqlite3`
- `docs/GLOSSARY.md` (rendered output only — the source of the change is the DB)
- `KANBAN.md` (same)
- `KANBAN.html` (same, **data block only**)
- `tests/test_apps.py` (one comment, nothing else)
- `docs/builder/bld-review-2-db_backed_doc_reconciliation.md` (this file)

**R1's files are closed.** `docs/SPECS/spec-021-apps-0_0_7.md` and `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` are `final-accepted`; this cohort does not edit them. Neither does it touch `django_strawberry_framework/**`, `CHANGELOG.md`, `docs/builder/build-021-apps-0_0_7.md`, or `docs/builder/bld-review-1-*.md`.

**Baseline-dirty, out of scope, never edit and never revert** (`AGENTS.md` rule 34): `docs/builder/build-020-list_field-0_0_7.md` (staged deleted), `docs/builder/DONE/build-020-list_field-0_0_7.md` (untracked), `docs/builder/bld-003-final.md`, plus the concurrent-session paths listed under `### Baseline at plan time` below.

**Plan declarations, as the build plan states them:**

- **Hot-path declaration — none.** No cohort in this cycle touches executable package code; R2's only `.py` edit is a comment inside one test function.
- **Floor-verification scope — none.** No Django / Strawberry / channels integration seam is touched.
- **Boundary count — zero** (`worker-1.md` `### Boundary count is a split trigger`). This cohort adds no guard, cap, rejection path, or validation branch. **The split question is therefore answered no:** three findings, three sites, one shared procedure (the DB-edit-then-regenerate loop), and splitting F5 from F6 would run that loop twice against the same DB while a concurrent writer is active.

### Baseline at plan time

Measured at this plan's write time, not copied:

- `git status --short` -> 23 paths. **None of R2's five owned paths is dirty**: `examples/fakeshop/db.sqlite3`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, and `tests/test_apps.py` all read clean. Every dirty path is a concurrent session's: 7 package modules and 5 test modules under a refactor, three `docs/SPECS/` files, one further `docs/` file, the two `build-020` paths, and the untracked `appx/` rationales, `build-021`/`build-022` plans, and two `bld-review-1-*` artifacts.
- `uv run python examples/fakeshop/manage.py check` -> `System check identified no issues (0 silenced).`
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have glossary links.`, **exit 0**. **The known pre-existing failure shape described in the dispatch is NOT present at this baseline.** If Worker 2 sees it fail on an unrelated earlier card, record it and do not chase it — and do **not** run the plain `import_spec_terms` sync, because this cohort adds no glossary term and needs no sync.
- Rows to be mutated, confirmed present with the stated identity: `GlossaryTerm` pk **448** (`anchor='django-appconfig'`, `title='Django `AppConfig`'`, status `Shipped`); `CardItem` pk **750** (card pk 43 = `Card.objects.get(number=21)`, status `done`; section is the FK row `key='note'` / `label='Note'`, pk 13; `is_complete=True`; card 21 has exactly three `CardItem` rows, the other two under `Verified in upstream` and both correct).

### DRY analysis

**Helper inventory checked.** Refreshed for the **whole package** at this plan's write time (`worker-1.md` `### Package-wide helper inventory before helper planning`, the AST command run verbatim from the repo root into `docs/shadow/helper-inventory.md`, 1,926 lines). Shapes searched: `ready`, `patch`, `apply`, `glossary`, `kanban`. The relevant hits are `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`, the three `_*_patches.py::apply` / `::_patch_is_installed` pairs, and `django_strawberry_framework/conf.py::upstream_patches_enabled` — all **read** by this pass as the source of truth for the glossary prose, none called, extended, or modified. **No new helper is proposed and none is needed:** this cohort writes no package logic, no test logic, and no script. The condition that would change the answer is a cohort that needed to *derive* the applier list programmatically rather than describe it; that is not this cohort.

- **Existing patterns reused.** The DB-edit-then-regenerate procedure is the repo's standing one (`BUILD.md:139-141`, reproduced in full under `### The DB procedure Worker 2 follows` so Worker 2 needs no other file). The three renderers already exist — `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`, `scripts/build_glossary_md.py` — and Worker 2 invokes them, never re-implements or extends them. The glossary body's prose reuses the shipped source's own vocabulary (`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`'s docstring and the three `_*_patches.py` module docstrings), so a later reader comparing entry against source sees one wording, not two.
- **New helpers justified.** None.
- **Duplication risk avoided.** Two risks, both prevented by a decision in this plan rather than left to Worker 2:
  1. **Re-copying the patch inventory.** `apps.py::…ready`'s docstring states explicitly that each patch module's own docstring is the single source of truth for *which* upstream bugs it hardens, and that the dispatcher repeats none of it; `spec-021`'s Decision 4 declines the copy for the same reason. The glossary body pinned below names the three appliers and their order and **stops there** — it does not enumerate the bugs. A third copy of that inventory would be a third thing to keep true.
  2. **Two prose descriptions of one contract.** `docs/GLOSSARY.md` `## Django AppConfig` and `KANBAN.md` card `DONE-021-0.0.7`'s `#### Note` both describe `ready()`, and a naive fix writes the same paragraph twice. They are deliberately given **different subjects**: the glossary describes the package's **current** state (three appliers, the gate, idempotence), the card note describes **what card 021 itself shipped** and how the `0.0.7` release came to carry a `ready()` body. Neither restates the other.

### The release facts this cohort's wording rests on

Re-derived at this plan's write time, not taken from the dispatch:

| fact | command | result |
|---|---|---|
| the `0.0.7` release tag carries a `ready()` body | `git show 0.0.7:django_strawberry_framework/apps.py \| grep -c 'def ready'` | `1` |
| card 021's own `apps.py` had no `ready()` | `git show 300e2811^:django_strawberry_framework/apps.py` | two class attributes, two docstrings, **no `ready`** |
| the body arrived with sibling card `DONE-024-0.0.7` | `git log --oneline -- django_strawberry_framework/apps.py` | `300e2811` "Ship Django Trac #37064 fix as package-level AppConfig.ready() patch", single Django applier |
| the other two appliers came four releases later | `git show 0.0.10:django_strawberry_framework/apps.py` then `git show 0.0.11:…` | `0.0.10` still imports `_django_patches` alone and calls a bare `apply()` — **one** applier; `0.0.11` carries the three aliased imports and `apply_django()` / `apply_strawberry()` / `apply_cross_web()` — **three**. Baseline `0.0.7`; `git tag \| sort -V` and `grep '^## \[' CHANGELOG.md` put `0.0.8`, `0.0.9`, `0.0.10`, `0.0.11` between them, so `0.0.11` is the fourth release after `0.0.7`. |
| the dispatch test came later still | `git show 0.0.13:tests/test_apps.py \| grep -c test_ready_dispatches_all_three_patch_appliers_and_refires_safely` | `0` — the test is absent from the last tag, so it ships at `0.0.14` (`CHANGELOG.md` `## [0.0.14] - 2026-07-20`, no tag cut), not at `0.0.13` |

So: "no `ready()` body in 0.0.7" is **false as a statement about the release** and **true as a statement about this card's own diff**. That distinction is the whole content of F6's replacement wording, and it is why F9 does not hold.

### F9 is not this cohort's work — resolved, not a defect

`CHANGELOG.md`'s `[0.0.7]` `### Added` entry says the `ready()` body "imports `django_strawberry_framework._django_patches` and calls `apply()`". Read against the table above that is **correct as history**: at the `0.0.7` tag exactly one applier shipped. "Correcting" it to three would falsify the changelog, and `AGENTS.md` rule 21 (#"No CHANGELOG.md updates unless told") forbids the edit independently. R1's final-verification catalog carries it as deferred item 1; **it is not deferred work — it is resolved, not a defect.** Worker 2 must not edit `CHANGELOG.md`; Worker 3 must not file it; the final gate must record it under `### Deferred work catalog` as **resolved-not-a-defect**, not as an open item.

### Implementation steps

Line numbers below are pin-at-write-time navigational hints; verify against the current file before editing. The two DB steps are the substance — the rendered-doc diffs are their **output**, never their source.

1. **Re-confirm the two rows before mutating either.** `uv run python examples/fakeshop/manage.py shell` and read `GlossaryTerm.objects.get(pk=448)` (`anchor`, `title`, `status`, `body`) and `CardItem.objects.get(pk=750)` (`card_id`, `section.key`, `is_complete`, `text`). If either identity or either current text differs from `### Baseline at plan time`, a concurrent session has moved it: **record it in the build report and apply your write on top**; do not reset, do not `git checkout`, do not revert churn you did not cause.

2. **F5 — rewrite `GlossaryTerm` pk 448's `body`** to the text pinned in `### Pinned replacement text` below, verbatim, via the ORM: read the object, assign `term.body = …`, call `term.save()`. **Never `.update()` on a queryset and never raw SQL** — both skip the `post_save` that creates the `UUIDModel` side-row every build script's in-process `/graphql/` query (`uuid { id }`) requires.

3. **F6 — rewrite `CardItem` pk 750's `text`** to the text pinned below, same ORM discipline. Leave `is_complete=True`, leave `section`, leave `order`, and leave card 21's other two `CardItem` rows (both `Verified in upstream`) untouched.

4. **Regenerate all three rendered docs from the repo root**, in this order:

   ```shell
   uv run python scripts/build_kanban_md.py
   uv run python scripts/build_kanban_html.py
   uv run python scripts/build_glossary_md.py
   ```

   **`KANBAN.html`'s Vue shell is hand-edited and the script owns only its data block.** Do not touch the shell.

5. **F8 — replace the provenance comment in `tests/test_apps.py`.** The site is `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes #"no ready() body in"` — the comment block immediately above the `forbidden = {` literal (currently `tests/test_apps.py:36-42`). Replace the whole seven-line block with the six-line text pinned below. **Comment text only:** no assertion, no test body, no test name, no import, no package source. Keep the existing 4-space indent; ASCII-only.

6. **Verify** per `### The DB procedure Worker 2 follows`. Verification is **not** "`git diff` is clean" — this cohort legitimately diverges all four owned generated paths from `HEAD`.

7. **Ruff, scoped to the one file this cohort touches:** `uv run ruff format tests/test_apps.py` then `uv run ruff check --fix tests/test_apps.py`. **Never `.`** — a repo-wide write-mode run would sweep the 12 package/test modules a concurrent session has dirty.

8. **Tick the three `### Dispatched findings checklist` boxes** whose fix actually landed in this diff, set `Status: built`, and write the build report.

### Pinned replacement text

Worker 2 does not compose contract prose. All three texts below are final; copy them verbatim.

#### F5 — `GlossaryTerm` pk 448, `body` (whole column, both paragraphs)

The `**See also:**` line is part of the `body` column and is **unchanged** — see `### Implementation discretion items` for why it is not widened.

```text
`django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`. The `ready()` body does exactly one thing: at Django app-load time it dispatches the package's three defensive upstream-patch appliers, in dependency order — `_django_patches.apply()`, which installs the [Django Trac #37064 hardening](#django-trac-37064-hardening), then `_strawberry_patches.apply()`, then `_cross_web_patches.apply()`. One patch module per third-party dependency the package has to patch; each module's own docstring is the single source of truth for which upstream bugs it hardens, and neither `ready()` nor this entry repeats that inventory. The three imports are function-local, so importing `django_strawberry_framework.apps` outside Django pulls in no patch module. Every applier self-gates on the `APPLY_UPSTREAM_PATCHES` setting (default on), so the gate lives inside each `apply()` rather than in `ready()`, and a consumer who sets `DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}` gets none of them. Each `apply()` is idempotent and self-healing, so a repeated `ready()` — some Django test runners fire it more than once — is safe. `ready()` registers no Django system checks, connects no signals, imports no consumer `DjangoType` module, and does not call [`finalize_django_types`](#finalize_django_types); the consumer owns that synchronization point. Consumers list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's implicit single-AppConfig discovery resolves the explicit class.

**See also:** [Django Trac #37064 hardening](#django-trac-37064-hardening) · [Schema export management command](#schema-export-management-command).
```

Every `(#anchor)` in that text was checked against the live DB at this plan's write time and resolves to exactly one `GlossaryTerm.anchor`: `django-trac-37064-hardening`, `finalize_django_types`, `schema-export-management-command`. The `·` separator and the em dashes match the file's existing convention (`docs/GLOSSARY.md` is generated; link shape there follows the renderer, and this column is rendered verbatim).

#### F6 — `CardItem` pk 750, `text` (one line; the kanban renderer stores and renders one bullet per row)

```text
tiny `AppConfig` (two class attributes, no `ready()` body in this card's own diff) + tests; the `ready()` body that ships in `0.0.7` arrived with sibling card `DONE-024-0.0.7`, dispatching the single Django patch applier, and the Strawberry and `cross_web` appliers followed at `0.0.10`.
```

#### F8 — `tests/test_apps.py`, the comment above `forbidden = {`

```python
    # ``ready`` is deliberately absent from this set: it is required on
    # this class, not forbidden. The package ships a ``ready()`` body
    # that dispatches the three upstream patch modules' ``apply()``
    # calls, and the ``ready`` tests below pin it positively. See
    # ``django_strawberry_framework/apps.py`` ``ready()`` docstring and
    # the three ``_*_patches`` module docstrings.
```

What that replacement deliberately does **not** carry, each dropped for a stated reason:

- **No spec number.** `spec-017` is this card's pre-renumber id and now names an unrelated `0.0.6` spec; `spec-021` would be correct but the sentence it appeared in is going away regardless, and the surrounding `forbidden` dict already cites its Decisions bare ("Decision 2", "Decision 5", "Decision 8"). A bare Decision pointer is the file's existing convention; introducing a spec-qualified one in a comment this pass is deleting narrative from would be new scope.
- **No supersession narrative.** `AGENTS.md` rule 27 and this repo's standing rule: a comment states the **invariant**, never how the change came to be. "The spec's stance is deliberately superseded by …" is process provenance and goes.
- **No test names.** The dispatch forbids naming them, and a name is a rename away from being wrong; "the `ready` tests below" is stable.
- **No count.** "the three appliers" is a fact of the shipped source; "the three tests below" would be a count that a fourth test falsifies.

### Test additions / updates

**No test is added, removed, renamed, or re-asserted.** The only `.py` change in this cohort is a comment, and `tests/test_apps.py`'s eight test functions and their assertions are untouched — `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`'s `forbidden` mapping keeps exactly its three keys (`label`, `default_auto_field`, `default`), which is the set `spec-021` Decision 4 pins.

Confirmation runs (pass/fail only; **no `--cov*` flag ever**, `--no-cov` is the only permitted coverage-shaped flag):

- `uv run pytest tests/test_apps.py --no-cov` — expected **8 passed**. Run it after the comment edit; a comment cannot change behavior, so a non-8 result means something else moved and is a stop-and-report.
- `uv run python examples/fakeshop/manage.py check` — expected `System check identified no issues (0 silenced).`
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` — expected `OK: 49 done cards have glossary links.` See the baseline note about the known pre-existing shape.

No temp/scratch test is appropriate here; there is nothing to prove that reading the rendered output does not prove.

### The DB procedure Worker 2 follows

`BUILD.md` `### Generated docs are DB-backed: edit the DB, then regenerate` is canonical and is reproduced here because Worker 2 cannot read `worker-0.md`, where the full procedure lives.

- `KANBAN.md`, `KANBAN.html` and `docs/GLOSSARY.md` are **rendered** from `examples/fakeshop/db.sqlite3`. A hand-edit of the rendered markdown is silently reverted by the next regenerate, and a raw SQL write skips the `post_save` side-row the renderers need.
- Run **every** DB edit through the **Django ORM** via `uv run python examples/fakeshop/manage.py shell`, using `.save()` / `.objects.update_or_create()`. **Never raw SQL. Never `.update()` on a queryset** — it fires no `post_save`. Each build script runs an in-process `/graphql/` query requesting `uuid { id }`, so the `UUIDModel` side-row the `post_save` creates is load-bearing.
- Regenerate all three from the repo root: `uv run python scripts/build_kanban_md.py`, `uv run python scripts/build_kanban_html.py`, `uv run python scripts/build_glossary_md.py`.
- **`KANBAN.html`'s Vue shell is hand-edited; only its data block regenerates.** The script owns the data block. Do not touch the shell.
- **Verification cannot be "`git diff` is clean"** — this cohort legitimately diverges all three rendered docs from `HEAD`. Verify instead by:
  - **two-consecutive-regenerate byte stability**: hash each rendered file (`shasum -a 256 KANBAN.md KANBAN.html docs/GLOSSARY.md`), run all three scripts again, hash again, compare. Record both hash sets in the build report.
  - **reading the rendered result** — the `## Django AppConfig` entry in `docs/GLOSSARY.md`, the `#### Note` bullet under `DONE-021-0.0.7` in `KANBAN.md` (around `KANBAN.md:4051-4053`), and the corresponding card object in `KANBAN.html`'s data block.
  - **row confirmation**: `uv run python examples/fakeshop/manage.py shell -c "..."` re-reading pk 448's `body` and pk 750's `text` and asserting each equals the pinned string.
  - `uv run python examples/fakeshop/manage.py check`.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` should report OK for all done cards. **If it fails at baseline on an unrelated earlier card**, that is a known pre-existing shape (a done card whose `GlossarySpecMention` rows still point at a pre-archive `docs/` path): record it, do not chase it, and **do not run the plain `import_spec_terms` sync** — this cohort adds no glossary term and does not need it.
- **The maintainer runs parallel sessions writing this same DB.** Never reset it, never `git checkout` it, never revert churn you did not cause. If the DB or a rendered doc changes without your edit, that is concurrent work: record it and apply your writes **on top**, handing the mixed diff to the maintainer (`BUILD.md` `### Tracked binary / generated files`). **A same-size binary diff is not proof of a no-op** — git does not line-diff binaries.

### Failability proofs

This cohort introduces **no new boundary** — no guard, cap, gate, or rejection path. Worker 2 writes, verbatim:

`None; this pass introduced no new boundary.`

Keep the heading either way. `### Hot-path budget` gets `Not applicable; plan declares no hot path.` and `### Floor verification` gets `Not applicable; plan declares floor-verification scope none.`

### Implementation discretion items

Items assessed and decided to be Worker 2's:

- **The order of the two DB writes** (F5's `GlossaryTerm` before F6's `CardItem`, or the reverse). Independent rows in independent apps; either order regenerates identically.
- **Whether both writes go in one `manage.py shell` invocation or two.** Either is fine as long as each mutation is a `.save()`.
- **Whether the row-confirmation read is a separate `shell -c` or the tail of the writing session** — provided a confirmation read runs *after* the last regenerate, not before.

Decided by this plan and **not** Worker 2's discretion:

- **The three replacement texts.** Pinned verbatim above.
- **Whether the glossary body names `APPLY_UPSTREAM_PATCHES`. It does, and this is a factual addition, not scope creep.** Every applier self-gates on that setting — it is a property of the shipped `ready()` the entry is describing, and F5 is precisely that the entry under-describes the shipped `ready()`. Two sibling entries already name the setting (`## DjangoGraphQLView` and `## UTF-8 wire contract`), and both do so only to say they do **not** ride it; the AppConfig entry is the one place that says what does. Scope creep would be documenting the setting's per-dependency mapping form or its resolution order — the body does not, and no `APPLY_UPSTREAM_PATCHES` glossary entry is created.
- **Whether the see-also line widens. It does not.** The entry currently points at `#django-trac-37064-hardening` and `#schema-export-management-command`; both resolve. Since the body now names three appliers, the natural candidate is an entry covering the Strawberry / `cross_web` dispatch — **and none exists** (that absence is part of what F5 records). The nearest entries, `#utf-8-wire-contract` and `#request-body-cap`, are explicitly **not** the upstream patches: each says so in its own body ("This is permanent policy on the view, not one of the upstream-bug patches"). Pointing at them would create a cross-reference the target contradicts. The `#django-trac-37064-hardening` target still carries the one applier the reader can follow. **Creating a new glossary term for the Strawberry / `cross_web` patches is out of this cohort's scope** — it is a new term, needs an index row, a category membership, and a `check_spec_glossary` story, and no finding dispatched here asks for one. Recorded under `### Notes for Worker 1 (spec reconciliation)` as a candidate, not built.
- **That `CHANGELOG.md` is not edited.** See `### F9 is not this cohort's work`.

### Dispatched findings checklist

One box per finding dispatched to R2, quoted as `docs/builder/build-021-apps-0_0_7.md` `## Verified findings` states it. Boxes stay `- [ ]` at planning; **Worker 2 ticks only a box whose fix actually landed in its diff**, and states any deferral in the build report rather than ticking. Worker 3 walks the list; a fresh Worker 1 audits every tick at final verification.

- [x] **F5 — HOLDS. `docs/GLOSSARY.md` `## Django AppConfig` under-describes the shipped `ready()`.** "The entry says the `ready()` body 'imports `django_strawberry_framework._django_patches` and calls `apply()`' — one of the **three** appliers `ready()` actually dispatches. No other glossary entry covers the Strawberry / `cross_web` dispatch. **DB-backed** (`GlossaryTerm.body`); fix is an ORM edit + regenerate, never a hand-edit." Sites: `GlossaryTerm` pk 448 (`anchor='django-appconfig'`) in `examples/fakeshop/db.sqlite3`, rendered at `docs/GLOSSARY.md` `## Django AppConfig`; source of truth read against `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` and the three `django_strawberry_framework/_*_patches.py` module docstrings.
- [x] **F6 — HOLDS. `KANBAN.md` card `DONE-021-0.0.7` `#### Note` is false for the shipped `0.0.7`.** "Reads 'tiny `AppConfig` (two class attributes, no `ready()` body in 0.0.7) + tests'. The `ready()` body shipped **in `0.0.7`** (F1's provenance), and `CHANGELOG.md`'s own `[0.0.7]` entry for this card already says so. **DB-backed** (`CardItem.text`)." Site: `CardItem` pk 750 (card pk 43, section `note`) in `examples/fakeshop/db.sqlite3`, rendered at `KANBAN.md` under the `DONE-021-0.0.7` Done-column card's `#### Note` heading and in `KANBAN.html`'s data block.
- [x] **F8 — HOLDS. `tests/test_apps.py` carries a stale, renumbered, self-narrating provenance comment.** "`tests/test_apps.py #"no ready() body in"` reads `# modules' ``apply()`` calls. The spec-017 "no ready() body in 0.0.7" stance is deliberately superseded by …`. Three defects in one comment: **wrong spec** (`spec-017` is this card's pre-renumber number; post-renumber it names an unrelated `0.0.6` spec — this card is `spec-021`); **falsified referent** (after R1 the spec carries no "no `ready()` body" stance at all); **process provenance in code** (`AGENTS.md`: a comment states the invariant, never how the change came to be). Comment text only — no assertion, no test body, no package source." Site: `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes #"no ready() body in"`.

**Not a box, and not a deferral:** F9. `docs/builder/build-021-apps-0_0_7.md` `### F9 — DOES NOT HOLD` and this plan's `### F9 is not this cohort's work` both record it as **resolved-not-a-defect**. No builder is dispatched at it.

### Notes for Worker 1 (spec reconciliation)

Written at plan time for the fresh Worker 1 who performs final verification:

- **A glossary term for the Strawberry / `cross_web` upstream patches does not exist.** F5 records the absence; this cohort describes the dispatch inside the AppConfig entry rather than creating the term, because a new term carries an index row, a category membership, and a `check_spec_glossary` story that no dispatched finding asks for. Candidate for the deferred-work catalog, not for this round.
- **R1's deferred-work catalog item 1 (`CHANGELOG.md`'s one-applier entry) must be re-graded to resolved-not-a-defect** in `bld-final.md`, on the release facts in `### The release facts this cohort's wording rests on`. It is neither open work nor a deferral.
- **R1's catalog explicitly excludes F8** ("It is R2's work item, not a deferral — do not double-count it"). Once this cohort's F8 box is ticked and audited, nothing about that comment belongs in the final catalog either.


---
## Build report (Worker 2)

Lands F5, F6 and F8 exactly as `### Pinned replacement text` states them. The two DB texts were **extracted programmatically from this artifact's own fenced blocks** rather than retyped, so "verbatim" is a byte fact and not a proofreading claim (see `### Implementation notes`). All three boxes in `### Dispatched findings checklist` are ticked; nothing is deferred.

**Concurrent-session intrusion into this artifact, recorded and not reverted.** Between this pass's first read of this file (224 lines, `Status: planned`) and its build-report append, a concurrent session appended a `## Build report (Worker 1, pass 2 - apply-changes)` section **belonging to R1** into this R2 artifact - its own `### Files touched` names `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md` as "this entry", and every finding it closes (High 1, Medium 2-5, Low 1-2) is R1's rationale/spec work, not R2's. Per `AGENTS.md` rule 34 and this plan's `### The DB procedure Worker 2 follows`, it was **left exactly as written**: not edited, not moved, not reverted. This pass's `Status: built` line and its three `- [x]` ticks survived the intrusion (re-verified after it appeared) and this report is appended below it. Flagged for Worker 3 and Worker 1 below - the misfiled section is R1's to relocate, not R2's.

### Files touched

Grounded in `git status --short` run after both ruff invocations. Five paths changed by this pass; every one is in R2's ownership list:

- `examples/fakeshop/db.sqlite3` - two rows rewritten through the Django ORM with `.save()` (never `.update()`, never raw SQL): `GlossaryTerm` pk 448 `body` (F5) and `CardItem` pk 750 `text` (F6). No other row touched; `is_complete`, `section` (FK pk 13, `key='note'`), `order` and `card_id` all re-read unchanged after the write.
- `docs/GLOSSARY.md` - regenerated output of the pk-448 write. One changed line (`## Django AppConfig`'s body paragraph); the `**See also:**` line is byte-identical to `HEAD`.
- `KANBAN.md` - regenerated output of the pk-750 write. One changed line, the `#### Note` bullet under `DONE-021-0.0.7` (`KANBAN.md:4053`).
- `KANBAN.html` - regenerated **data block only**; one changed line. The hand-maintained Vue shell was not touched by this pass and is not touched by the script.
- `tests/test_apps.py` - the seven-line provenance comment above `forbidden = {` inside `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` replaced by the pinned six-line block (F8). Comment text only: no assertion, no test body, no test name, no import, no package source. The file's eight test functions and the three `forbidden` keys are unchanged.
- `docs/builder/bld-review-2-db_backed_doc_reconciliation.md` - this report, the three checklist ticks, `Status: built`.

Every other dirty path in `git status --short` was dirty at plan time and is a concurrent session's: 7 package modules and 5 test modules under refactor, `docs/SPECS/spec-021`/`spec-022`/`spec-051`, one further `docs/` file, the two `build-020` paths, and the untracked `appx/` rationales, `build-021`/`build-022` plans and three `bld-review-1-*` artifacts. None was edited and none was reverted.

### Tests added or updated

None. No test is added, removed, renamed, or re-asserted - the only `.py` change in this cohort is a comment, as `### Test additions / updates` requires.

### Validation run

- `uv run ruff format tests/test_apps.py` - **pass**, `1 file left unchanged`. Scoped to the one file; never `.`.
- `uv run ruff check --fix tests/test_apps.py` - **pass**, `All checks passed!`.
- ASCII-only check on the edited `.py`: count of bytes `> 127` in `tests/test_apps.py` -> **0**.
- `uv run python scripts/check_trailing_commas.py --check tests/test_apps.py docs/builder/bld-review-2-db_backed_doc_reconciliation.md KANBAN.md docs/GLOSSARY.md` -> **exit 0** (the pre-commit hook `ruff` does not cover).
- `git status --short` after both ruff invocations - five paths newly modified against the plan's baseline: `KANBAN.html`, `KANBAN.md`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3`, `tests/test_apps.py`. All five are in this cohort's writable list and all five appear in `### Files touched`. **Nothing unexpected; nothing reverted.**
- `uv run pytest tests/test_apps.py --no-cov` - **8 passed**, the expected count. No `--cov*` flag in any form.
- `uv run python examples/fakeshop/manage.py check` - `System check identified no issues (0 silenced).`
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` - `OK: 49 done cards have glossary links.`, **exit 0**, matching the plan's baseline. The known pre-existing failure shape did not appear; the plain `import_spec_terms` sync was **not** run.

**Two-consecutive-regenerate byte stability** (`scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`, `scripts/build_glossary_md.py`, in that order, from the repo root, run twice):

| file | hash after regenerate 1 | hash after regenerate 2 |
|---|---|---|
| `KANBAN.md` | `e45bedcb7505d4604c6e4c992859408bff2bf43640df9621f76bf7033bcb769f` | identical |
| `KANBAN.html` | `337c9e5315d035309393140f22adfc2148489ca2885460471ae853ecb2fb3c80` | identical |
| `docs/GLOSSARY.md` | `1f0b4655c8284fd85b768ae336b997f40d4df0b5abf696eb26339384930d2379` | identical |

All three pairs match; the renders are fixed points of the current DB.

**Row confirmation, read back through the ORM after the last regenerate:** `GlossaryTerm.objects.get(pk=448).body` equals the pinned F5 string (1,764 chars) -> `True`; `CardItem.objects.get(pk=750).text` equals the pinned F6 string (287 chars) -> `True`.

**Rendered result read, not inferred:** `docs/GLOSSARY.md` `## Django AppConfig` carries the three appliers in dependency order, the function-local-import sentence, the `APPLY_UPSTREAM_PATCHES` gate, idempotence, and the four negatives, with the see-also line unchanged; `KANBAN.md`'s `DONE-021-0.0.7` `#### Note` carries the "this card's own diff" / `DONE-024-0.0.7` / `0.0.10` wording; `KANBAN.html`'s data block carries the same bullet exactly once. `git diff --stat` shows one changed line in each of the three rendered files - no collateral render drift from the concurrent writer.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **The two pinned texts were extracted from this artifact's own fenced `text` blocks by regex, not retyped into the shell.** Why this shape: a hand-transcribed copy of a 1,764-character paragraph is a proofreading claim, and this one contains three characters a keyboard silently substitutes - two em dashes and the middle-dot see-also separator. Reading the contract file itself makes "verbatim" mechanical. A first draft of the write script was hand-typed and did in fact carry a hyphen for an em dash and curly apostrophes; it was discarded before it ran, and that discovery is why the extraction shape was chosen.
- **Both writes went in one `manage.py shell` invocation, `GlossaryTerm` first.** Discretion the plan granted. One invocation, one DB open, shorter window against the concurrent writer; the order is immaterial since the rows are independent.
- **The row-confirmation read is both the tail of the writing session AND a fresh read after the last regenerate.** The plan permits either; both were run because a regenerate opens the DB, and only a read taken after the final regenerate proves what the rendered files were rendered from.
- **The F8 replacement keeps the existing 4-space indent and the file's double-backtick code convention**, and is ASCII-only. It states the invariant (`ready` is required on this class, not forbidden; the `ready` tests below pin it positively) and carries no spec number, no supersession narrative, no test name and no count - each dropped for the reason `### Pinned replacement text` records.
- **`CHANGELOG.md` was not opened for edit.** F9 is resolved-not-a-defect per `### F9 is not this cohort's work`.

### Notes for Worker 3

- **Read the intrusion note at the top of this report first.** The `## Build report (Worker 1, pass 2 - apply-changes)` section physically sitting between this artifact's plan and this report is **not this cohort's work** and does not describe this diff. Review R2 against `### Dispatched findings checklist`'s three boxes and the five files in `### Files touched`; everything that section discusses (rationale bytes, spec citations, `spec-022`) belongs to R1's artifact.
- **The verification that matters is not `git diff`.** All four generated paths legitimately diverge from `HEAD`. The hash table above, the ORM read-back, and the three rendered spot-checks are the evidence; re-run them rather than looking for a clean diff.
- **`git diff -- django_strawberry_framework/__init__.py` is empty** - no package source anywhere in this cohort, so the public-surface check is trivially satisfied.
- The DB binary diff reads `Bin 5050368 -> 5050368 bytes`. Same size is not a no-op - compare the two rows through the ORM, as recorded above.
- No shadow file and no `scripts/review_inspect.py` run was used by this pass.

### Notes for Worker 1 (spec reconciliation)

1. **No spec amendment is required by this pass.** The three landed texts describe `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` as R1 already reconciled it in `docs/SPECS/spec-021-apps-0_0_7.md` `### Decision 4 - ready() applies the upstream patches`; nothing implemented here diverged from the plan, so there is no drift to reconcile.
2. **A glossary term for the Strawberry / `cross_web` upstream patches still does not exist.** The plan's note stands as written: this cohort described the dispatch inside the `## Django AppConfig` entry rather than creating a term, because a new term carries an index row, a category membership and a `check_spec_glossary` story no dispatched finding asks for. **Candidate for `bld-final.md`'s deferred-work catalog**, not built here. The `**See also:**` line was deliberately not widened for the same reason - `#utf-8-wire-contract` and `#request-body-cap` each state in their own bodies that they are *not* upstream-bug patches, so pointing at them would create a cross-reference the target contradicts.
3. **R1's deferred-catalog item 1 (`CHANGELOG.md`'s one-applier `[0.0.7]` entry) must be re-graded to resolved-not-a-defect.** Carried forward from the plan; `CHANGELOG.md` was not touched by this pass.
4. **F8 must not appear in the final deferred catalog.** It landed in this diff and its box is ticked; R1's catalog already excludes it as "R2's work item, not a deferral".
5. **A concurrent session misfiled R1's pass-2 build report into this R2 artifact** (see the intrusion note above). It is R1's content in R2's file: `docs/builder/bld-review-2-db_backed_doc_reconciliation.md` now contains a `## Build report (Worker 1, pass 2 - apply-changes)` whose `### Files touched` names `bld-review-1-rationale_and_spec_reconciliation.md` as "this entry". **Worker 2 left it untouched** (`AGENTS.md` rule 34 - never revert churn you did not cause), and it is flagged here because relocating another cohort's build report is a custodian action, not a builder's. Whoever reconciles it should first check whether the same text also exists in R1's own artifact, since a "move" that is really a duplicate deletes the only copy.

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

---

## Review (Worker 3)

Reviewed the three dispatched findings (F5, F6, F8) against the working-tree diff, the DB read through the ORM, `django_strawberry_framework/apps.py` and the three `_*_patches.py` modules at `HEAD`, and the release history. Every mechanical claim in the build report reproduced on my own instruments. One factual claim in F6's landed text does not.

### High:

#### F6's replacement note dates the Strawberry / `cross_web` appliers to the wrong release

`CardItem` pk 750's new `text` — now rendered at `KANBAN.md:4053` and inside `KANBAN.html`'s data block — ends:

```KANBAN.md:4053
... and the Strawberry and `cross_web` appliers followed at `0.0.10`.
```

They did not ship in `0.0.10`. They first shipped in **`0.0.11`**. Three independent instruments agree:

1. **Release content.** `git show 0.0.10:django_strawberry_framework/apps.py` -> `ready()` imports `_django_patches` and calls a single `apply()`; there is no `apply_strawberry` / `apply_cross_web` line anywhere in the file (`git show 0.0.10:pyproject.toml` -> `version = "0.0.10"`, so the tag is the release it names). `git show 0.0.11:django_strawberry_framework/apps.py` -> all three imports and all three calls (`version = "0.0.11"`).
2. **Dates.** The `0.0.10` release commit is `fdab1766` "Release 0.0.10", **2026-06-16**; `CHANGELOG.md`'s heading is `## [0.0.10] - 2026-06-16`. `c7cb5f5c` "Patch upstream non-UTF-8 request-body 500 in Strawberry and cross_web" is **2026-06-18** — two days *after* `0.0.10` shipped — and falls inside the `## [0.0.11] - 2026-06-19` window. `git merge-base --is-ancestor c7cb5f5c aec1bd4e` -> yes, where `aec1bd4e` (2026-06-19) is the commit that first sets `version = "0.0.11"`.
3. **The plan's own bump convention, applied consistently.** `### The release facts this cohort's wording rests on` reads the release off `git show <commit>:pyproject.toml`. That instrument reports the *previously released* version, which the build plan itself annotates one row earlier — `300e2811` | `0.0.6` "(pre-bump; the `0.0.7` cut followed)" — and then does not apply to the `c7cb5f5c` row. `c7cb5f5c` at `0.0.10` is the same shape: the cut that followed was `0.0.11`.

Why it matters: this is the defect class F6 exists to remove, reintroduced in a new spelling inside the sentence written to remove it. The old text made a false release claim about `0.0.7`; the new text corrects that one and lands a false release claim about `0.0.10`, in a standing doc, phrased with the same confidence. It also now contradicts the shipped artifact a reader can check in one command.

Recommended change: rewrite `CardItem` pk 750's `text` through the ORM with `0.0.10` -> `0.0.11`, i.e. `... and the Strawberry and \`cross_web\` appliers followed at \`0.0.11\`.`, then re-run all three generators and re-confirm two-consecutive-regenerate byte stability. Nothing else in the sentence needs to move: the `0.0.7` half and the `DONE-024-0.0.7` attribution both re-derived clean (below).

Test expectation: none — no behavior changes. The pinning artifact is the regenerated `KANBAN.md` / `KANBAN.html` pair plus the ORM read-back.

Note for whoever applies it: the same wrong figure is stated in `docs/builder/build-021-apps-0_0_7.md` `### F9 — DOES NOT HOLD` ("The Strawberry and `cross_web` appliers arrived four releases later", table row `c7cb5f5c` -> `version = "0.0.10"`) and in this artifact's `### The release facts this cohort's wording rests on`. Neither is writable by this cohort. Correcting only the DB row leaves two plan-side copies of the false fact available for re-copy; routed under `### Notes for Worker 1` below. **`CHANGELOG.md` is unaffected** — F9 still does not hold, and nothing here reopens it.

### Medium:

None.

### Low:

#### The glossary body calls the dispatch order "dependency order"; the source does not, and the layering runs the other way

`GlossaryTerm` pk 448's new body (`docs/GLOSSARY.md:530`) reads "dispatches the package's three defensive upstream-patch appliers, **in dependency order** — `_django_patches.apply()` ... then `_strawberry_patches.apply()`, then `_cross_web_patches.apply()`". The call order is correct (`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`). The gloss is not supported by anything in the source: `ready()`'s docstring names the three modules without asserting an ordering constraint, and `tests/test_apps.py::test_ready_dispatches_all_three_patch_appliers_and_refires_safely` asserts that all three are installed, never the sequence. The three appliers patch disjoint targets (`SimpleTestCase._remove_databases_failures`, `BaseView` / `SyncBaseHTTPView` / `AsyncBaseHTTPView`, `DjangoHTTPRequestAdapter.body`), so no order is forced. Worse, `django_strawberry_framework/_cross_web_patches.py`'s own module docstring states `cross_web` "is the HTTP request/response abstraction Strawberry's Django view is built on" — so a literal dependency order would put `cross_web` *before* `strawberry`, the reverse of what ships.

Recommended change: drop the two words (`... appliers — \`_django_patches.apply()\`, which installs ...`) or replace with "in this order". Left as a Low because the enumeration itself is right and no reader is misrouted to wrong behavior; fold it into the same ORM write as the High if that write happens.

### DRY findings

None. The cohort adds no helper, no constant, no branch and no module; the plan's `### DRY analysis` decision to give the glossary entry and the card note **different subjects** (current package state vs. what card 021 itself shipped) holds in the landed text — I read both against each other and neither restates the other. The one prose overlap with `apps.py::…ready`'s docstring is deliberate and correctly scoped: both name the three appliers and the gate, and neither copies the per-module bug inventory, which stays single-sited in the three module docstrings. No existence challenge to raise — nothing was introduced to exist.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** (0 lines). `__all__` and the re-export list are unchanged. No package source is touched anywhere in this cohort; the only `.py` byte that moved is a comment in `tests/test_apps.py`.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. Confirmed mechanically: `git diff HEAD -- CHANGELOG.md` is empty. F9 is not filed and is not reopened.

### Documentation / release sanity

Applicable and load-bearing. Every bullet of `ARTIFACT.md` `### Documentation / release sanity`, walked:

- **Verbatim drop-ins confirmed character-for-character via `diff`, against the ORM-read value and not only the rendered file.** Pinned blocks extracted from this artifact by line range into a scratch path outside the repo; DB values written out through `manage.py shell`; `diff` on each pair:
  - F5 — `GlossaryTerm.objects.get(pk=448).body` vs `### Pinned replacement text` F5 block -> **identical** (1,764 chars, matching the build report).
  - F6 — `CardItem.objects.get(pk=750).text` vs the F6 block -> **identical** (287 chars).
  - F8 — `tests/test_apps.py:37-42` vs the F8 block -> **identical**. The em dashes, the curly apostrophe and the `·` see-also separator all survive; no hyphen/ASCII substitution anywhere. The extract-by-regex shape the build report describes is corroborated by the result, not merely asserted.
  - No fenced-code drop-in with a matching inner/outer backtick count is involved.
- **Version strings, statuses and card IDs.** `DONE-024-0.0.7` exists and is this feature's card (`KANBAN.md:62`, `KANBAN.md:123` — "Django Trac #37064 hardening + `safe_wrap_connection_method`"), and `300e2811` is its commit. The `0.0.7` half of the note re-derived clean: `git tag --contains 300e2811` includes `0.0.7`; `git show 0.0.7:django_strawberry_framework/apps.py` carries `def ready` with the single Django applier; `git show 0.0.7:pyproject.toml` -> `version = "0.0.7"`. The "no `ready()` body in this card's own diff" half also re-derived clean: card 021's shipping commit is `dfa035b4`, whose `apps.py` is exactly the two class attributes and two docstrings with no `ready` (its parent `b972cd84` is the pseudo-only stub). The `0.0.10` string is the High above. `GlossaryTerm` pk 448's `status_text` is unchanged at `shipped (\`0.0.7\`)`, correct for the AppConfig itself.
- **KANBAN card movement.** None — no card moved section; `DONE-021-0.0.7` stays in Done, appears once, and only its `#### Note` bullet changed.
- **Links introduced or moved.** Three in-page `(#anchor)` targets in the new glossary body, all re-derived against `docs/GLOSSARY.md`'s own headings by slugging every `##`-level heading: `#django-trac-37064-hardening` (`docs/GLOSSARY.md:2004`), `#finalize_django_types` (`:904`), `#schema-export-management-command` (`:1813`) — all three resolve to exactly one heading. The `**See also:**` line is byte-identical to `HEAD`; I read the plan's recorded reason for not widening it (`### Implementation discretion items`) and independently confirmed its premise: `#utf-8-wire-contract` and `#request-body-cap` each state in their own bodies that they are package policy and **not** upstream-bug patches (`docs/GLOSSARY.md:628`), so pointing at them would create a cross-reference the target contradicts. Not re-raised.
- **No archival in this slice.**
- **No obsolete "coming soon" / "planned" / old-version wording** remains in the two rewritten bodies or in the replaced comment.
- **Staging language in feeding docstrings.** The three rendered docs here are DB-fed rather than docstring-fed, but the glossary body is *derived from* `apps.py` and the three `_*_patches.py` docstrings, so I swept those four modules for `TODO(`, `Slice N`, `planned`, `Coming` -> **zero hits**. No staging language could leak into the entry, and no docstring fix is owed alongside this regenerate. (`docs/TREE.md`, the genuinely docstring-fed doc, is untouched by this cohort and needs no regenerate: no module docstring changed.)

Additional verification this subsection is the right home for:

- **Regenerate is stable and hand-edit-free.** I re-ran `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`, `scripts/build_glossary_md.py` from the repo root myself and re-hashed. All three files are **byte-identical before and after**, and the hashes match the build report's table exactly: `KANBAN.md` `e45bedcb…9f`, `KANBAN.html` `337c9e53…80`, `docs/GLOSSARY.md` `1f0b4655…79`. A hand-edit riding along would have been reverted by that run; none was. The DB is byte-identical (full `.dump` comparison) before and after my regenerate, so the render is a pure read.
- **Only the intended lines diverge from `HEAD`.** `git diff --stat` over the three rendered files -> `1 insertion(+), 1 deletion(-)` each, i.e. one changed line per file, exactly as claimed. `docs/GLOSSARY.md:530` (the body paragraph; the see-also line at `:532` untouched), `KANBAN.md:4053` (the `#### Note` bullet), `KANBAN.html:97` (the `window.KANBAN_DATA` line).
- **`KANBAN.html`'s hand-maintained Vue shell is untouched.** `diff` of the two files with line 97 deleted from each -> **identical**. Parsing both data blocks as JSON and differencing them normalized shows exactly two changed keys on one card item: `text` and `updatedDate`. Nothing else in the payload moved.

### What looks solid

- **The DB edits are real, ORM-made, complete, and free of collateral.** A full logical `.dump` of `HEAD`'s `db.sqlite3` (recovered read-only outside the repo) against the working-tree DB differs in **exactly two lines**: the `kanban_carditem` row 750 and the `glossary_glossaryterm` row 448. Nothing else in the file changed — including no concurrent-session churn.
- **Surrounding columns intact.** `CardItem` pk 750: `card_id=43`, `section_id=13` (`key='note'`), `order=0`, `is_complete=1` — all identical to `HEAD`; only `text` and `updated_date` moved. `GlossaryTerm` pk 448: `title`, `title_sort`, `anchor`, `status_text`, `entry_order=14`, `index_order=10`, `status_id=13` — all identical; only `body` and `updated_date` moved.
- **Card 21's other two `CardItem` rows are untouched.** Rows 749 and 969 (both `section_id=5`) are byte-identical to `HEAD` including their `updated_date`s.
- **The `UUIDModel` side-rows are intact for both mutated rows.** `kanban_uuidmodel` carries the same three ids for card 43's items as at `HEAD`, unchanged in every column — consistent with a `.save()` through a `post_save` that finds an existing side-row, and inconsistent with a raw-SQL or `.update()` write that would have left a mismatch. (`GlossaryTerm` has no side-row table; the `kanban_uuidmodel` constraint enumerates kanban models only.)
- **F8 states an invariant, not a history.** The diff against `HEAD` is exactly the seven-line comment block replaced by the pinned six-line block and nothing else. The replacement carries **no** spec number (pre-renumber or otherwise), **no** line numbers, **no** supersession narrative, and no test names; "the `ready` tests below pin it positively" is a stable statement of the file's own structure. It states what is true of the class (`ready` is required, not forbidden), which is the invariant form `AGENTS.md` requires. The file is **ASCII-only** (0 bytes > 127). The 8 test functions, the 3 `forbidden` keys (`label`, `default_auto_field`, `default`) and every assertion are byte-identical to `HEAD` — proven by the diff carrying no other hunk.
- **The glossary body is true against the code, not just against the plan.** Read `apps.py::DjangoStrawberryFrameworkConfig.ready`, the three `_*_patches.py` module docstrings and `conf.py::upstream_patches_enabled` at `HEAD` and checked each clause: three appliers dispatched in the stated sequence (`apply_django()`, `apply_strawberry()`, `apply_cross_web()`); all three imports function-local inside `ready()`; each `apply()` opens with its own `if not upstream_patches_enabled(<name>): return`, so the gate is inside `apply()` and `ready()` carries none; `upstream_patches_enabled` defaults to `True` and a global `False` returns `False` for every dependency, so "gets none of them" is exact; each `apply()` documents and implements idempotent, self-healing re-entry via `_patch_is_installed()`; `ready()` registers no system check, connects no signal, imports no consumer module and does not call `finalize_django_types`. The one clause the source does not support is the "dependency order" gloss (Low above).
- **The finding classes do not survive elsewhere.** Swept the DB and every standing doc for the "no `ready()` body" claim and for one-applier descriptions of `ready()`: `CardItem` 750 is the only DB row and `KANBAN.md:4053` the only rendered line; no other `GlossaryTerm` body carries the claim. `CHANGELOG.md`'s `[0.0.7]` entry is the F9 case and is correctly left alone.
- **Confirmation runs reproduce.** `uv run pytest tests/test_apps.py --no-cov` -> **8 passed** (no `--cov*` flag in any form). `uv run python examples/fakeshop/manage.py check` -> `System check identified no issues (0 silenced).`
- **The concurrent-intrusion handling was right.** Worker 2 left the misfiled R1 section in place rather than deleting what might have been the only copy; that is the correct call under `AGENTS.md` rule 34 and is not a defect. See the routing note below.

### Failability proofs re-run

**Empty re-run set, and legal.** The diff introduces **no** boundary, guard, gate, or rejection path — two DB text columns, three regenerated files, one comment block. The mandatory floor is therefore vacuous, and the build report's `None; this pass introduced no new boundary.` is accurate. No source mutation was made by this review; the source carve-out was not exercised. `### Hot-path budget` and `### Floor verification` correctly read not-applicable against the plan's declarations (hot-path none, floor-verification scope none, boundary count zero), all three of which I re-read in `docs/builder/build-021-apps-0_0_7.md` `## Declarations`.

### Temp test verification

No temp test was created; nothing in this cohort is provable by a test that reading the rendered output and the ORM read-back does not prove. `docs/builder/temp-tests/r2/` is empty and no file was left behind. No `scripts/review_inspect.py` run and no shadow file were used: `BUILD.md` `### When to run the helper` scopes it to source logic, and this cohort adds none — recorded as a deliberate skip, matching the plan's pre-flight step 2.

### Dispatched findings checklist audit

- **F5 — ticked, fix landed.** `GlossaryTerm` pk 448's `body` rewritten verbatim through the ORM and rendered. Closed on content, with one Low on two words of it.
- **F6 — ticked, fix landed but is factually wrong in one clause.** The site was rewritten verbatim as pinned; the pinned text itself carries the wrong release. The box is honestly ticked against the plan; the defect is upstream of Worker 2, in the pinned prose. This is the High.
- **F8 — ticked, fix landed and is clean.** No deferral is recorded and none was needed; every box has a matching fix in the diff.

### Notes for Worker 1 (spec reconciliation)

1. **Routing the misfiled R1 section — confirmed a duplicate, safe to remove, and it is yours.** `## Build report (Worker 1, pass 2 — apply-changes)` sits at `docs/builder/bld-review-2-db_backed_doc_reconciliation.md:207`, inside R2's artifact, while R1's own artifact carries the same section at `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md:479`. I differenced the two copies rather than taking the duplication on report: they are 99.2% identical and the difference runs **one way only** — R1's copy has one extra paragraph (the "artifact's two header reference lines carried pass 1's byte figures" note) that R2's copy lacks. R2's copy is a strict subset, so removing it loses nothing. **Remove it at final verification; do not treat it as a Worker 2 defect** — leaving it was the correct call with the information Worker 2 had.
2. **The `0.0.10` -> `0.0.11` correction must also reach the plan, or it will be re-copied.** The High above is a DB fix, but the same wrong release is stated twice in files this cohort cannot write: `docs/builder/build-021-apps-0_0_7.md` `### F9 — DOES NOT HOLD` (the `c7cb5f5c` table row and "arrived four releases later") and this artifact's `### The release facts this cohort's wording rests on`. Both are the same instrument error — reading the shipping release off `pyproject.toml` at the work commit, which reports the *previous* release, exactly as the plan's own `300e2811` | `0.0.6` "(pre-bump)" annotation says. **F9's conclusion is unaffected**: `0.0.7` genuinely carries a one-applier `ready()`, so `CHANGELOG.md` remains correct as history and stays closed.
3. **Escalated (contract-level, maintainer's call): whether the `0.0.10`/`0.0.11` instrument should be fixed repo-wide.** Resolution paths: (a) correct the two plan-side statements in place at final verification and move on; (b) additionally record in `bld-final.md`'s `### Deferred work catalog` that "version at commit" is not "shipping release" in this repo — the bump lands at the end of a cut — so future cycles reach for `git tag --contains` or the `CHANGELOG.md` date instead. I recommend (b): this is the second release-attribution error this cycle has produced from the same instrument, and the first one is the finding this cohort exists to fix.
4. **Deferred-work catalog items carried forward from this cohort, unchanged:** a glossary term for the Strawberry / `cross_web` upstream patches still does not exist (the plan's and build report's reasoning for describing the dispatch inside the AppConfig entry instead is sound and I do not re-raise it); R1 catalog item 1 re-grades to **resolved-not-a-defect**; **F8 must not appear** in the catalog — it landed here and its box is audited.
5. **No spec amendment is required by this cohort.** The landed texts describe `apps.py::DjangoStrawberryFrameworkConfig.ready` as R1 already reconciled it; the High is a release-history error inside a card note, not a divergence from the spec's contract.

### Review outcome

`revision-needed` — one High, one Low, both closable by a single ORM rewrite of `CardItem` pk 750 (and, if taken, `GlossaryTerm` pk 448) followed by a regenerate and a re-run of the byte-stability check. Everything else in this cohort verified clean on independent instruments.

---

## Build report (Worker 2, pass 2)

Closes both findings Worker 3 set `revision-needed` on: the High (`0.0.10` -> `0.0.11` in `CardItem` pk 750) and the Low (the unsupported "in dependency order" gloss in `GlossaryTerm` pk 448). Both are prose corrections inside text this cohort's own plan pinned, so the correction is in the DB rows, not in the mechanical execution — which Worker 3 verified byte-perfect and which this pass did not re-do. No prior artifact entry was edited. `CHANGELOG.md` is untouched; F9 stays closed.

Both edits were made as **targeted `str.replace` on the value read back through the ORM**, not by retyping the paragraph — the same reason pass 1 extracted the pinned blocks by regex. Replacing in place makes it a byte fact that every em dash, curly apostrophe and the `·` see-also separator already in the column survived; each replacement asserted `count(old) == 1` before writing.

### Files touched

Grounded in `git status --short` run after the regenerate. Four paths changed by this pass, all four already in R2's ownership list and all four already divergent from `HEAD` from pass 1:

- `examples/fakeshop/db.sqlite3` — two rows rewritten through the Django ORM with `.save()` (never `.update()`, never raw SQL): `CardItem` pk 750 `text` (High) and `GlossaryTerm` pk 448 `body` (Low).
- `KANBAN.md` — regenerated. One changed line vs. pass 1 (`KANBAN.md:4053`).
- `KANBAN.html` — regenerated, data block only; the hand-maintained Vue shell untouched.
- `docs/GLOSSARY.md` — regenerated. One changed line vs. pass 1 (`docs/GLOSSARY.md:530`).

`tests/test_apps.py` was **not** touched: Worker 3 verified F8 landed clean, no defect was found in it, and therefore no ruff invocation was owed or made this pass.

`git status --short` after the regenerate lists **exactly the same path set as at pass start** — no path entered or left the working tree because of this pass. Everything in it outside the four above is the baseline-dirty concurrent-session work named in `### Baseline at plan time` (7 package modules, 6 test modules, 3 specs, `docs/feedback.md`, the staged-deleted `build-020-*`, and the untracked builder artifacts): left untouched and unreverted per `AGENTS.md` rule 34.

### Tests added or updated

None. No behavior changed; two DB text columns and their rendered output moved. Worker 3's `### Documentation / release sanity` already records that `tests/test_apps.py`'s 8 functions and 3 `forbidden` keys are byte-identical to `HEAD`, and this pass did not open the file.

### Validation run

**The two corrections, re-derived on this pass's own instruments before writing them.**

The release figure, read off **tag content**, per `docs/builder/build-021-apps-0_0_7.md` `### F9` ("Read releases off the TAGS, never off `pyproject.toml` at the work commit"):

| command | result |
|---|---|
| `git show 0.0.7:django_strawberry_framework/apps.py` | `def ready` present; `from …_django_patches import apply` + a bare `apply()`. **One** applier. |
| `git show 0.0.10:django_strawberry_framework/apps.py \| grep -n apply` | 2 hits: `from …_django_patches import apply`, `apply()`. No `apply_strawberry`, no `apply_cross_web`. **One** applier. |
| `git show 0.0.11:django_strawberry_framework/apps.py \| grep -n apply` | the three function-local imports aliased `apply_cross_web` / `apply_django` / `apply_strawberry`, then `apply_django()`, `apply_strawberry()`, `apply_cross_web()`. **Three** appliers. |

So the Strawberry and `cross_web` appliers first ship at `0.0.11`, not `0.0.10`. `git merge-base --is-ancestor` was **not** used, per the plan's explicit warning that it answers `NO` against both tags on this rewritten branch.

The ordering gloss, read off the source the entry describes:

- `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` — the docstring names the three modules ("Three patch modules, one per third-party dependency") and the gate, and asserts **no** ordering constraint at all. The call sequence `apply_django()` / `apply_strawberry()` / `apply_cross_web()` is a fact of the body with no stated reason.
- `_django_patches.py` module docstring — Django test-runner bug; no ordering claim.
- `_strawberry_patches.py` module docstring — "Companion to `_django_patches`"; no ordering claim.
- `_cross_web_patches.py` module docstring — "`cross_web` is the HTTP request/response abstraction Strawberry's Django view is built on". A literal dependency order would therefore run `cross_web` **before** `strawberry`, the reverse of the shipped sequence.

Both halves of Worker 3's Low reproduce: unsupported, and backwards. The fix states the order as a fact and claims no reason for it — **no replacement rationale was invented**, per the dispatch.

**The two ORM writes, read back after the last regenerate:**

- `GlossaryTerm` pk 448 — `"dependency order"` occurrences: **0**; `"appliers, in this order —"` occurrences: **1**. `body` length 1758 (was 1764; `dependency` -> `this` is exactly -6). Em dashes still **3**, `·` still **1**. `anchor='django-appconfig'`, `status_text='shipped (\`0.0.7\`)'` unchanged.
- `CardItem` pk 750 — `"0.0.10"` occurrences: **0**; `"0.0.11"` occurrences: **1**. `text` length **287**, unchanged (`0.0.10` and `0.0.11` are the same width). `card_id=43`, `section_id=13`, `is_complete=True`, `order=0` — all unchanged.

**Two-consecutive-regenerate byte stability**, all three scripts run from the repo root in the plan's order:

| file | pass-1 hash (this pass's start) | after regenerate #1 | after regenerate #2 |
|---|---|---|---|
| `KANBAN.md` | `e45bedcb…b769f` | `7cd5e705…7d24d` | `7cd5e705…7d24d` |
| `KANBAN.html` | `337c9e53…2fb3c80` | `6a4f1dcf…05cf26d` | `6a4f1dcf…05cf26d` |
| `docs/GLOSSARY.md` | `1f0b4655…30d2379` | `caddf7d1…3a87c6211b` | `caddf7d1…3a87c6211b` |

Identical across the two consecutive regenerates: the render is a pure read of the DB and no hand-edit is riding along. The pass-1 column matches the hashes Worker 3 recorded, confirming this pass started from the tree Worker 3 reviewed.

**Diff scope.** `git diff --stat -- KANBAN.md KANBAN.html docs/GLOSSARY.md` -> `3 files changed, 3 insertions(+), 3 deletions(-)` — exactly one changed line per file against `HEAD`, i.e. this pass moved the same single line pass 1 moved rather than adding a second divergence.

**Rendered result read, not assumed:**

- `docs/GLOSSARY.md:530` — "…dispatches the package's three defensive upstream-patch appliers, in this order — `_django_patches.apply()`, which installs the [Django Trac #37064 hardening](#django-trac-37064-hardening), then `_strawberry_patches.apply()`, then `_cross_web_patches.apply()`." The three in-page anchors, the `**See also:**` line and the rest of the paragraph are untouched.
- `KANBAN.md:4053` — "…and the Strawberry and `cross_web` appliers followed at `0.0.11`."
- `KANBAN.html` — the one changed line is the `window.KANBAN_DATA` data line; `grep -c` for the corrected sentence -> 1.

**Confirmation runs** (no `--cov*` flag in any form):

- `uv run pytest tests/test_apps.py --no-cov` -> **8 passed**.
- `uv run python examples/fakeshop/manage.py check` -> `System check identified no issues (0 silenced).`
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have glossary links.`, exit **0** — matches the recorded baseline. The plain sync was not run.

**Ruff:** not invoked. No `.py` file was touched this pass, so neither `ruff format` nor `ruff check --fix` was owed; a repo-wide run is forbidden by the plan and would have swept the concurrent session's 13 dirty modules.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Targeted in-place replacement over re-pinning the paragraph.** Worker 3's High and Low each name one wrong span inside a text that is otherwise verified byte-perfect against the plan's pinned block. Rewriting the whole column would have re-exposed the exact hazard pass 1's regex extraction existed to close (a silently substituted em dash or curly apostrophe), and would have made "did anything else move?" a proofreading question again. Reading the value through the ORM, asserting the old span occurs exactly once, and writing back the replacement makes the untouched remainder a byte fact. The `count(old) == 1` assertion is the part that matters: it fails loudly if a concurrent session moved the row under this pass.
- **"in this order", not a deletion and not a new rationale.** Worker 3 offered both shapes. Keeping the two-word connector preserves what the sentence is doing — the following clause enumerates three appliers in sequence, and dropping the connector entirely leaves the em-dash list reading as an unordered set, which under-describes a body that does have a fixed call sequence. "in this order" asserts the sequence and asserts nothing about why, which is what the source supports. No substitute reason was invented; the dispatch's "an unsupported claim swapped for another unsupported claim is the same defect" was the binding constraint.
- **The gloss is not re-stated anywhere else.** Swept the DB for the phrase before writing: `"dependency order"` now occurs in **0** `GlossaryTerm` bodies and **0** `CardItem` texts, so the Low is closed at its only site rather than at one of several.
- **F8 deliberately not reopened.** Worker 3 verified the landed comment is clean, ASCII-only and invariant-shaped; the dispatch scopes `tests/test_apps.py` to "only if you find an actual defect". None was found and the file was not opened, which is why no ruff run appears above.
- **The misfiled `## Build report (Worker 1, pass 2 — apply-changes)` section was again left exactly as written**, per the dispatch routing it to Worker 1's final verification. Not removed, not edited, not moved. Verified after this pass's append that it, this artifact's `Status:` line and all three `### Dispatched findings checklist` ticks are intact.

### Notes for Worker 3

- The re-review surface is small: two DB columns and the three regenerated lines. Everything else in this cohort is unchanged from the tree you reviewed, and the pass-1 hash column above lets you confirm that in one command before you start.
- Both fixes are verifiable without trusting this report: `git show 0.0.10:django_strawberry_framework/apps.py` vs `git show 0.0.11:…` for the release, and `apps.py::DjangoStrawberryFrameworkConfig.ready` plus the three `_*_patches.py` module docstrings for the ordering gloss. Do not reach for `git merge-base --is-ancestor` — it answers `NO` against both tags here.
- No box in `### Dispatched findings checklist` changed state this pass. All three were already ticked and their fixes are still in the diff; F6's tick is now honest on content as well as on execution, which is what Worker 3's audit noted it was not.
- No temp test was created or needed; nothing here is provable by a test that the ORM read-back and the rendered output do not prove.

### Notes for Worker 1 (spec reconciliation)

**No spec amendment is required by this pass**, and none was withheld. Both corrections are release history and an unsupported gloss inside two DB-backed doc bodies; neither is a divergence from `spec-021`'s contract, which R1 already reconciled and which this cohort does not edit. Worker 3's item 5 reached the same conclusion for pass 1 and this pass adds nothing to it.

Carried forward for the final gate, restated because they are the deferred-work catalog's inputs and this artifact is where they live:

1. **The plan-side `0.0.10` statements are now corrected upstream — verify, do not re-correct.** `docs/builder/build-021-apps-0_0_7.md` `### F9` has been re-derived by Worker 0 and now reads `0.0.11` in both the table row and the prose, with the instrument rule stated ("Read releases off the TAGS, never off `pyproject.toml` at the work commit"). Worker 3's item 2 is therefore already discharged on the plan side. **This artifact's own `### The release facts this cohort's wording rests on` still states `version = "0.0.10"` for `c7cb5f5c`** — that row is *not wrong as written* (it reports what `pyproject.toml` says at that commit, which is what its command asks) but its surrounding sentence, "the other two appliers came four releases later", **is** wrong, and this cohort's plan section is not writable by Worker 2. Correct or annotate it at final verification.
2. **Worker 3's item 3 (repo-wide instrument note) is endorsed, and this pass is a third data point.** "Version at commit" is not "shipping release" in this repo — the bump lands at the cut. Recording that in `bld-final.md`'s `### Deferred work catalog` is cheap and this cycle has now produced the same class of error three times from the same instrument.
3. **Unchanged from pass 1 and from Worker 3's item 4:** no glossary term exists for the Strawberry / `cross_web` upstream patches (candidate, not built — the AppConfig entry describes the dispatch instead); R1 catalog item 1 (`CHANGELOG.md`'s one-applier `[0.0.7]` entry) re-grades to **resolved-not-a-defect**; **F8 must not appear** in the catalog.
4. **Artifact hygiene, yours:** the duplicate `## Build report (Worker 1, pass 2 — apply-changes)` section still sits inside this R2 artifact. Worker 3 differenced it against R1's own copy and confirmed R2's is a strict subset, so removing it loses nothing. Left in place by both Worker 2 passes deliberately.

### Dispatched findings checklist

No box changed state this pass; all three (F5, F6, F8) were ticked in pass 1 and every one still has its fix in the diff. F6's landed text now carries the correct release, so its tick is true on content as well as on execution. Nothing is deferred.

---

## Review (Worker 3, pass 2)

Closure check, not a fresh review. Both pass-1 findings re-derived on my own instruments and both are closed exactly as reported. The mechanical envelope pass 1 verified is undisturbed: I re-ran it rather than assuming it. The one new item is the pass-1 Low's **defect class surviving outside this cohort's writable set** — in the spec R1 wrote this cycle — which R2 cannot fix and which is escalated rather than held against it.

### High:

None.

### Medium:

#### Escalated — the "in dependency order" gloss the Low removed from the DB is still asserted three times in this cycle's own R1 files

The Low is closed at the site it was filed against and at every site in the DB. It is **not** closed as a defect class. Corpus and instrument, stated so this is re-derivable: `grep -c 'dependency order'` over each file, plus `git show HEAD:<path>` for the pre-existing question.

| site | count | at `HEAD` |
|---|---|---|
| `examples/fakeshop/db.sqlite3` (whole `.dump`, every table, every column) | **0** | 1 (the row this cohort fixed) |
| `docs/SPECS/spec-021-apps-0_0_7.md` `## Slice checklist` Slice 1 sub-bullet and `### Decision 4 - ready() applies the upstream patches` | **2** | **0** |
| `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` reconciliation table row 4 | **1** | 0 (file did not exist) |

`git show HEAD:docs/SPECS/spec-021-apps-0_0_7.md | grep -c 'dependency order'` -> **0**; the working tree -> **2**. The gloss is **not pre-existing**: R1 introduced it into the spec this cycle, in the same window R2 was removing it from the DB. Both spec sites assert it flat, with no supporting reason anywhere in Decision 4 — I read the whole Decision, and it justifies the *dispatch*, the gate, idempotence and the four negatives, and says nothing about ordering.

Both halves of the original Low reproduce against the spec text exactly as they reproduced against the glossary body: `apps.py::DjangoStrawberryFrameworkConfig.ready`'s docstring names the three modules with no ordering claim, `tests/test_apps.py::test_ready_dispatches_all_three_patch_appliers_and_refires_safely` asserts installation and not sequence, the three appliers patch disjoint targets, and `django_strawberry_framework/_cross_web_patches.py`'s own module docstring says `cross_web` "is the HTTP request/response abstraction Strawberry's Django view is built on" — so a literal dependency order runs `cross_web` **before** `strawberry`, the reverse of both the shipped sequence and the spec's own parenthetical `(django, strawberry, cross_web)`.

Why this is escalated and not `revision-needed`: `docs/SPECS/spec-021-apps-0_0_7.md` is `final-accepted` and **explicitly closed to this cohort** (this artifact's `## Plan (Worker 1)`, "R1's files are closed"), as is its rationale companion. No writable file of R2's carries the gloss. Holding R2 open would ask Worker 2 to edit a file the plan forbids it to open.

Resolution paths for Worker 1, who owns the spec:

- (a) Strike the two words at all three sites — `docs/SPECS/spec-021-apps-0_0_7.md` line 37 and line 228, `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` line 198 — matching the wording R2 landed in the DB: **"in this order"**, which asserts the sequence and claims no reason for it. This keeps the spec and the rendered glossary saying one thing.
- (b) Keep "dependency order" and add the dependency argument to Decision 4 that would make it true. I do not recommend this: the argument does not exist, and the one layering statement in the source runs the other way.

Test expectation: none; no behavior changes, and no test asserts an ordering today.

### Low:

#### The gloss sweep is DB-scoped and its heading is repo-scoped

`## Build report (Worker 2, pass 2)` `### Implementation notes` heads a bullet **"The gloss is not re-stated anywhere else."** The bullet's own body names its corpus honestly — "Swept the **DB** for the phrase" — and its two figures (0 `GlossaryTerm` bodies, 0 `CardItem` texts) both reproduce on my dump. The heading over-reaches that corpus, and at repo scope it is false: three live sites, tabled above. This is the cycle's standing defect in its usual shape — the sentence written after the instrument ran, claiming the instrument's scope was wider than it was.

Confined to the per-cycle artifact, which closes with this cycle; the standing docs R2 owns are all correct. Recommended change: none in this artifact (prior entries are immutable). The correction is this section, and the Medium above is where the substance lands.

#### Pass 2 reports the artifact's "four releases later" sentence as wrong; it is right

Routed item 1 asks me to check `### The release facts this cohort's wording rests on`, whose row reads:

```docs/builder/bld-review-2-db_backed_doc_reconciliation.md:58
| the other two appliers came four releases later | `git show c7cb5f5c:pyproject.toml | grep -m1 '^version'` | `version = "0.0.10"` |
```

`## Build report (Worker 2, pass 2)` `### Notes for Worker 1` item 1 says the row's result cell "is *not wrong as written*" but that "its surrounding sentence, 'the other two appliers came four releases later', **is** wrong". **The sentence is right.** Derivation, from the release list rather than from either version string:

- Shipping release of the two appliers: **`0.0.11`**, from tag content (below, under `### Documentation / release sanity`).
- Baseline the row's "later" is measured from: `0.0.7`, which the two rows immediately above it establish as the release carrying the `ready()` body.
- Releases after `0.0.7`: `git tag | sort -V` -> `0.0.7, 0.0.8, 0.0.9, 0.0.10, 0.0.11, 0.0.13`; `grep '^## \[' CHANGELOG.md` -> `[0.0.8] [0.0.9] [0.0.10] [0.0.11]` between them, with no untagged release in the gap (`0.0.12` is dated after `0.0.11`). `0.0.11` is therefore **exactly four releases after `0.0.7`**.

So: **right about the interval, right about the count, and mis-flagged.** What is defective in that row is narrower and different from what pass 2 named — the claim is true but the evidence cell **cannot establish it**. `git show c7cb5f5c:pyproject.toml` reports the *previous* release, and counting four from that answer (`0.0.6` -> `0.0.10`) is how the row's own wrong release arose in the first place. A true claim resting on the instrument this cycle exists to retire will read as corroborated by it on the next re-copy.

Recommended change for Worker 1, who owns this file at final verification: leave the sentence, replace the row's command and result with the tag-content instrument the plan now mandates (`git show 0.0.10:.../apps.py` -> one applier; `git show 0.0.11:.../apps.py` -> three), so the row's claim and its evidence agree. Do **not** "correct" the sentence to a smaller number.

### DRY findings

None, and nothing changed here from pass 1. The pass added no helper, constant, branch or module — two targeted `str.replace` writes through the ORM and three regenerates. The plan's different-subjects decision (glossary = the package's current state; card note = what card 021 itself shipped) still holds in the landed text: I read both against each other after the edits and neither restates the other. The one prose overlap with `apps.py::…ready`'s docstring stays correctly scoped — both name the three appliers and the gate, neither copies the per-module bug inventory. No existence challenge: nothing was introduced to exist.

The Medium above is adjacent to a DRY concern and is deliberately not filed as one: the spec and the glossary entry describing `ready()` in their own words is the plan's intended shape, not duplication. The defect is that one of the two copies is now saying something the other retracted.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty (0 lines)**. `git diff HEAD -- django_strawberry_framework/__init__.py` -> also empty, so no concurrent staging is masking it. `__all__` and the re-export list are unchanged. No package source is touched by this cohort at all; the only `.py` byte that has moved in either pass is the `tests/test_apps.py` comment from pass 1.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. Confirmed mechanically: `git diff HEAD -- CHANGELOG.md` -> **0 lines**. F9 stays closed and is not reopened. I read `CHANGELOG.md`'s `[0.0.7]` entry only as a release-date source for the Low above; it was not opened for edit.

### Documentation / release sanity

Applicable. Every bullet of `ARTIFACT.md` `### Documentation / release sanity`, walked against pass 2's diff.

- **Verbatim drop-ins, confirmed character-for-character.** Both corrections are targeted substitutions inside text pass 1 landed byte-perfect, so the right instrument is a character-level opcode diff of the ORM value against this artifact's own pinned block, not a re-read. I extracted the pinned F5 block (lines 104-106) and F6 line (line 113) from this file, read both columns out through `manage.py shell`, and ran `difflib.SequenceMatcher.get_opcodes`:
  - **F5** — the *only* non-equal opcode across 1,764 -> 1,758 characters is `replace 'dependency' -> 'this'`. Every other byte of the pinned body is untouched: the three anchors, the function-local-import sentence, the `APPLY_UPSTREAM_PATCHES` gate clause, the idempotence clause, the four negatives, and the `**See also:**` line.
  - **F6** — the *only* non-equal opcode across 287 -> 287 characters is `replace '0`.' -> '1`.'`. Length stability is therefore not what I am reading it off; the opcode set is. The note's other claims survived the edit intact: "this card's own diff", "ships in `0.0.7`", "sibling card `DONE-024-0.0.7`", "the single Django patch applier".
  - **F8** — untouched this pass. `git diff HEAD -- tests/test_apps.py` is the pass-1 comment hunk and nothing else: one `@@` hunk, 7 lines out / 6 lines in, all comment. The 8 test functions, the 3 `forbidden` keys and every assertion are unchanged.
- **Non-ASCII survival, measured on the columns.** `GlossaryTerm` pk 448 body: em dashes **3**, `·` **1**, and those are the *only* two non-ASCII code points present. `CardItem` pk 750 text: **zero** non-ASCII characters. No hyphen-for-em-dash substitution anywhere, which the opcode diffs above prove exhaustively rather than by spot-check. One precision note on pass 2's prose, not a finding: `## Build report (Worker 2, pass 2)`'s opening says the write made it "a byte fact that every em dash, **curly apostrophe** and the `·` … already in the column survived" — there are no curly apostrophes in either column (both use ASCII `'`, as in "card's"), so that member of the list is vacuous. The two figures the pass actually *measured* (`Em dashes still 3`, `· still 1`) both reproduce exactly.
- **Version strings, statuses and card IDs. The release re-derived from tag content**, per the plan's instrument rule, and **not** with `git merge-base --is-ancestor`:

  | command | result |
  |---|---|
  | `git show 0.0.7:django_strawberry_framework/apps.py` | `def ready` present; `from …_django_patches import apply` then a bare `apply()`. **One** applier. |
  | `git show 0.0.10:django_strawberry_framework/apps.py` | identical shape — `_django_patches` import + bare `apply()`. No `apply_strawberry`, no `apply_cross_web`. **One** applier. |
  | `git show 0.0.11:django_strawberry_framework/apps.py` | three aliased function-local imports, then `apply_django()`, `apply_strawberry()`, `apply_cross_web()`. **Three** appliers. |
  | `git show 0.0.7\|0.0.10\|0.0.11:pyproject.toml` | `version = "0.0.7"` / `"0.0.10"` / `"0.0.11"` — each tag names its own release, so tag content is a sound instrument here. |

  The two appliers first ship at **`0.0.11`**, and `CardItem` pk 750 now says `0.0.11`. `GlossaryTerm` pk 448's `status_text` is unchanged at ``shipped (`0.0.7`)``, still correct for the AppConfig itself. `DONE-024-0.0.7` and the `0.0.7` half of the note were re-derived clean in pass 1 and are byte-unchanged by this pass.
- **The stated order matches the source as actually written.** `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` calls `apply_django()`, `apply_strawberry()`, `apply_cross_web()` in that sequence; the rendered body reads "in this order — `_django_patches.apply()` … then `_strawberry_patches.apply()`, then `_cross_web_patches.apply()`". Match. **No substitute rationale was invented:** "in this order" asserts the sequence and nothing about why, which is the whole of what the source supports. The dispatch's constraint — an unsupported claim swapped for another unsupported claim is the same defect — is met.
- **KANBAN card movement.** None. `DONE-021-0.0.7` stays in Done, appears once, and only its `#### Note` bullet differs from `HEAD`.
- **Links introduced or moved.** None by this pass. The three in-page anchors in the glossary body and the `**See also:**` line are inside the byte-identical remainder proved by the F5 opcode diff; all three resolved in pass 1 and no heading moved (`docs/GLOSSARY.md` differs from `HEAD` by one line).
- **No archival in this slice.**
- **No obsolete "coming soon" / "planned" / old-version wording** in either rewritten body. The one old-version string that existed — `0.0.10` — is what this pass removed.
- **Staging language in feeding docstrings.** Unchanged from pass 1 and re-swept: `apps.py` and the three `_*_patches.py` modules carry no `TODO(`, `Slice N`, `planned` or `Coming`. `docs/TREE.md` is untouched and needs no regenerate; no module docstring changed in either pass.

### What looks solid

- **The two closures are exact, and exactness is the point.** Each is a single opcode against a text pass 1 verified byte-perfect. That is a stronger result than "the new text is correct", because it also rules out the class of collateral a re-pin would have risked — which is precisely the reason the pass gave for choosing `str.replace` over re-pinning, so the recorded mechanism and the measured outcome agree.
- **The DB moved in exactly two rows and nowhere else.** Full logical `.dump` of `HEAD`'s `db.sqlite3` (extracted read-only outside the repo via `git show HEAD:`) against the working-tree DB -> **4 diff lines = 2 changed rows**: `kanban_carditem` 750 and `glossary_glossaryterm` 448, each differing only in its text column and its `updated_date`. Nothing else in the file changed. This subsumes every sibling check as a whole-file result rather than a row-by-row one: card 43's other two `CardItem` rows, every `kanban_uuidmodel` side-row, all sibling columns of both mutated rows, and every other table are byte-identical to `HEAD`. The ORM read-back independently confirms `card_id=43`, `section_id=13` (`key='note'`), `order=0`, `is_complete=True` on pk 750, and `anchor`, `title`, `title_sort`, `status_text`, `entry_order=14`, `index_order=10`, `status_id=13` on pk 448.
- **The regenerate is a pure read, proved on my own run.** I re-ran `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`, `scripts/build_glossary_md.py` from the repo root and re-hashed. All three files **byte-identical before and after**, and the DB `.dump` byte-identical across my regenerate too. The hashes match pass 2's table exactly: `KANBAN.md` `7cd5e7054ee1a3fee0acd858db61c90f392648593d2c51a2a784710da817d24d`, `KANBAN.html` `6a4f1dcfdf8d58bbe6495a6f05fb81c1786d3435797fea25bf769099e05cf26d`, `docs/GLOSSARY.md` `caddf7d1be2912eb3608885ae04e09d1918934fce05cc5ffe720e33a87c6211b`. Nothing was hand-written into a generated doc; a hand-edit would have been reverted by that run.
- **One changed line per rendered file, still.** `git diff HEAD --stat` (`HEAD`-anchored, so a concurrent session's staging cannot read it clean) -> `KANBAN.md 2 +-`, `KANBAN.html 2 +-`, `docs/GLOSSARY.md 2 +-`; `-U0` puts them at `KANBAN.md:4053`, `docs/GLOSSARY.md:530`, `KANBAN.html:97`. Same three lines as pass 1 — this pass moved the lines it already owned rather than adding a second divergence.
- **`KANBAN.html`'s hand-maintained Vue shell is untouched.** `diff` of `git show HEAD:KANBAN.html` against the tree copy with line 97 deleted from each -> **identical**. Parsing both data blocks as JSON and differencing them flattened: **0** keys added, **0** removed, **2** changed — `/cards/20/items/2/text` and `/cards/20/items/2/updatedDate`. Nothing else in a 5MB payload moved.
- **`tests/test_apps.py` and `CHANGELOG.md` are untouched by pass 2.** `tests/test_apps.py` carries only the pass-1 comment hunk and is ASCII-only (0 bytes > 127); `CHANGELOG.md`'s `HEAD` diff is empty. No ruff run was owed and none was made, correctly.
- **Confirmation runs reproduce on my instruments.** `uv run pytest tests/test_apps.py --no-cov` -> **8 passed** (no `--cov*` flag in any form). `uv run python examples/fakeshop/manage.py check` -> `System check identified no issues (0 silenced).` `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have glossary links.`, exit **0**, matching the recorded baseline; the plain sync was not run.
- **The plan-side half of pass-1's routing item 2 is genuinely discharged.** `docs/builder/build-021-apps-0_0_7.md` `### F9` now reads `0.0.11` in both the table row and the prose, states the instrument rule ("Read releases off the TAGS, never off `pyproject.toml` at the work commit"), and carries the `git merge-base --is-ancestor` warning. It no longer contains the phrase "four releases later" at all, so the only surviving copy of that sentence is the artifact row graded as a Low above. `grep -c 'dependency order' docs/builder/build-021-apps-0_0_7.md` -> 0.
- **F9 stays closed and correctly so.** `git show 0.0.7:…/apps.py` carries exactly one applier, so `CHANGELOG.md`'s `[0.0.7]` entry is accurate as history. Nothing in this pass reopens it.

### Failability proofs re-run

**Empty re-run set, and legal.** Pass 2 introduced no boundary, guard, gate, or rejection path — two DB text columns and three regenerated files. The mandatory floor is vacuous and the build report's `None; this pass introduced no new boundary.` is accurate. No source mutation was made by this review; the Worker 3 source carve-out was not exercised. `### Hot-path budget` and `### Floor verification` correctly read not-applicable against the plan's declarations (hot-path **none**, floor-verification scope **none**, boundary count **zero**), all three re-read in `docs/builder/build-021-apps-0_0_7.md` `## Declarations`.

### Temp test verification

No temp test was created and none was needed: everything at issue this pass is provable by the ORM read-back, the character-level opcode diffs, the `.dump` comparison and the regenerate. `docs/builder/temp-tests/r2/` **does not exist** on disk (`ls` -> no such file or directory), so nothing was left behind by either review pass. No `scripts/review_inspect.py` run and no shadow file were used — `BUILD.md` `### When to run the helper` scopes the helper to source logic and this cohort adds none; recorded as a deliberate skip.

### Dispatched findings checklist audit

- **F5 — ticked, fix landed, now clean on content.** `GlossaryTerm` pk 448's `body` is the pinned text with the pass-1 Low's two words replaced by "in this order". Closed at every site inside R2's writable set. The class survives outside it — the Medium.
- **F6 — ticked, fix landed, now clean on content.** `CardItem` pk 750's `text` is the pinned text with the release corrected to `0.0.11`, which I re-derived from tag content independently. The tick was honest on execution in pass 1 and is now honest on content too.
- **F8 — ticked, fix landed, untouched this pass and still clean.** Its diff hunk is byte-unchanged from the one I audited in pass 1.

No box changed state, no box is ticked without a matching fix in the diff, and no box is unaddressed. Nothing is deferred.

### Notes for Worker 1 (spec reconciliation)

Deferred items carried forward for `bld-final.md`'s `### Deferred work catalog`. **Drift-sensitive figures are flagged: re-run them at write time rather than copying them from here** — three of the files below are dirty under concurrent sessions.

1. **Escalated: the "in dependency order" gloss survives in `docs/SPECS/spec-021-apps-0_0_7.md` (2 sites) and `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` (1 site).** Full derivation and the two resolution paths are in `### Medium:` above; (a) — strike to "in this order", matching what R2 landed — is what I recommend. **Yours because the spec is yours:** R2's plan closes both files to this cohort, so no writable file of R2's can carry the fix. **Drift-sensitive:** all three sites are in working-tree files a concurrent session is editing; re-run `grep -c 'dependency order'` on each before writing a count, and re-run `git show HEAD:docs/SPECS/spec-021-apps-0_0_7.md | grep -c 'dependency order'` (**0** as I measured it) before repeating the not-pre-existing claim.
2. **This artifact's `### The release facts this cohort's wording rests on` needs its instrument replaced, not its sentence corrected.** Pass 2 routed the sentence to you as wrong; it is right (`0.0.7` -> `0.0.11` is four releases, derived in `### Low:` above from `git tag` and `CHANGELOG.md`). The row's `version = "0.0.10"` evidence cell is what cannot support it. **Not drift-sensitive** — it is a fixed row in a per-cycle artifact — but it is the last surviving copy of the pre-bump instrument in this cycle's prose, since the plan's `### F9` no longer carries it.
3. **Endorsed and unchanged: record the repo-wide instrument note in the catalog.** "Version at commit" is not "shipping release" here — the bump lands at the cut, so `git show <commit>:pyproject.toml` reports the *previous* release. Reach for tag content or the `CHANGELOG.md` date. This cycle has now produced the class three times from the same instrument, and item 2 is a fourth appearance in a subtler shape: a true claim propped on it. `git merge-base --is-ancestor` is **not** the substitute — it answers `NO` for `c7cb5f5c` against both the `0.0.10` and `0.0.11` tags on this rewritten branch, which I did not use for exactly that reason.
4. **The misfiled `## Build report (Worker 1, pass 2 — apply-changes)` section is still a strict subset and still routed to you.** Re-derived this pass, not carried forward: R2's copy at `docs/builder/bld-review-2-db_backed_doc_reconciliation.md:207` (102 lines) against R1's at `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md:479` (104 lines) — **0** non-blank lines present in R2's copy and absent from R1's, **1** line present only in R1's (the "artifact's two header reference lines carried pass 1's byte figures" note), sequence ratio **0.9921**. Removing R2's copy loses nothing. Both Worker 2 passes correctly left it in place under `AGENTS.md` rule 34; it is a custodian action, not a builder defect. **Drift-sensitive:** both artifacts are untracked working-tree files — re-run the subset check before deleting.
5. **Unchanged from pass 1, carried without re-derivation because nothing in pass 2 touched them:** no glossary term exists for the Strawberry / `cross_web` upstream patches (**candidate, not built** — the AppConfig entry describes the dispatch instead, and the `**See also:**` line was deliberately not widened because `#utf-8-wire-contract` and `#request-body-cap` each state in their own bodies that they are *not* upstream-bug patches); R1 catalog item 1 (`CHANGELOG.md`'s one-applier `[0.0.7]` entry) re-grades to **resolved-not-a-defect**; **F8 must not appear** in the catalog — it landed here and both its ticks are audited.
6. **No spec amendment is required by the diff itself.** The landed texts describe `apps.py::DjangoStrawberryFrameworkConfig.ready` as R1 reconciled it. Item 1 is a defect *in* the spec, not a divergence of the diff from it — the diff is what makes the spec's gloss visible, by retracting it everywhere R2 could reach.

7. **Recorded, not reverted: a concurrent session rewrote a different glossary row while this review was running.** Between my regenerate and my closing `git status`, `docs/GLOSSARY.md` and `examples/fakeshop/db.sqlite3` both changed hash under me. Re-derived rather than assumed: a fresh `.dump` against the one I took an hour earlier differs in **exactly one line** — `glossary_glossaryterm` pk **504** (`Schema export management command`), `updated_date` `2026-08-18 21:46:22`. That is the parallel `bld-review-2-spec_022_glossary_body.md` cohort's row, not R2's. **R2's two rows are unharmed**, re-read after the intrusion: `CardItem` 750 length **287** with `0.0.11` at offset 280; `GlossaryTerm` 448 length **1758**, `"dependency order"` at **0**, `"in this order"` at offset 311. `docs/GLOSSARY.md`'s `HEAD` diffstat is now `6 ++++--` rather than `2 +-` — R2's one line plus the other cohort's two. Nothing was reverted and nothing was reset (`AGENTS.md` rule 34). **Every figure in this review section was measured before that write and holds for R2's rows; the `docs/GLOSSARY.md` hash `caddf7d1…6211b` and the whole-file "one changed line" statement are the two that the intrusion has since superseded** — re-run both at final verification rather than copying them.

### Review outcome

`review-accepted`, with one Medium transparently escalated to Worker 1 under item 1 above.

Both pass-1 findings are closed at every site inside this cohort's writable set, each by a single measured character-level substitution inside otherwise byte-identical pinned text, and the entire mechanical envelope re-verified on my own instruments: two DB rows and only two, byte-stable regenerates matching the recorded hashes, one changed line per rendered file, the Vue shell provably untouched, `tests/test_apps.py` and `CHANGELOG.md` untouched by this pass, and the public surface empty.

The Medium does not rise to `revision-needed` under the dispatch's rule, and the reason is not that it is small — it is that **no standing doc this cohort owns carries a false statement.** The DB, all three rendered docs and `tests/test_apps.py` are correct; the surviving false claim is in `docs/SPECS/spec-021-apps-0_0_7.md`, which this cohort's own plan closes to it. Sending R2 back would send Worker 2 at a file it is forbidden to open. Both Lows are residual imprecisions inside this per-cycle artifact, which closes with the cycle and is not a standing doc; each is corrected here in the record rather than by an edit, since prior entries are immutable.

---

## Final verification (Worker 1)

A fresh Worker 1 invocation with no memory of the passes above. Every figure below was measured by me at this pass's write time against the working tree; none is copied from a prior section, and no prior entry was edited. No `git stash` / `checkout` / `restore`, no `--cov*` flag in any form, no `git merge-base --is-ancestor`, no commit, no branch.

### Summary

R2 delivered three site fixes and nothing else. Two are rows in `examples/fakeshop/db.sqlite3`, read back through the ORM by me: `GlossaryTerm` pk **448** (`anchor='django-appconfig'`, `title='Django `AppConfig`'`, `status_text='shipped (`0.0.7`)'`, body length **1758**) now describes the shipped three-applier dispatch, the function-local imports, the `APPLY_UPSTREAM_PATCHES` gate inside each `apply()`, idempotence and the four negatives — `body.count('dependency order')` -> **0**, `body.count('in this order')` -> **1**; `CardItem` pk **750** (card 43, section `note`, `is_complete=True`, `order=0`, text length **287**) now separates "no `ready()` body in this card's own diff" from the `ready()` body that ships in `0.0.7` with `DONE-024-0.0.7`, and dates the Strawberry / `cross_web` appliers to `0.0.11`. The third is the provenance comment in `tests/test_apps.py`; `git diff HEAD -- tests/test_apps.py` is one hunk, 7 lines out / 6 in, comment only, `grep -c 'spec-017'` -> **0**, non-ASCII bytes **0**.

The rendered docs still carry R2's intended text after the concurrent regenerate that rewrote `GlossaryTerm` pk 504: `docs/GLOSSARY.md:530` carries the "in this order" body, `grep -c 'dependency order' docs/GLOSSARY.md` -> **0**, `KANBAN.md:4053` carries the `0.0.11` note, and `KANBAN.html` carries the same bullet once (`grep -c "appliers followed at"` -> 1). **Nothing R2 landed was reverted by that regenerate.** `git diff HEAD --stat` over the four generated paths reads `KANBAN.html 2 +-`, `KANBAN.md 2 +-`, `docs/GLOSSARY.md 6 ++++--`, `examples/fakeshop/db.sqlite3 Bin 5050368 -> 5050368` — the `docs/GLOSSARY.md` figure is R2's one line plus the other cohort's two, as Worker 3 predicted and as I re-measured rather than copied.

Confirmation runs, mine: `uv run pytest tests/test_apps.py --no-cov` -> **8 passed in 2.60s**. `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-021-apps-0_0_7.md` -> `OK: 12 terms - all have glossary entries and at least one spec link.`, exit **0**. `uv run python scripts/check_trailing_commas.py --check` over the two spec files and this artifact -> exit **0**.

### Spec changes made (Worker 1 only)

Three edits closing the escalated Medium, plus the rationale record it licenses. Population re-derived before acting, counting occurrences and not lines: `grep -o 'dependency order' <file> | wc -l` -> **2** in `docs/SPECS/spec-021-apps-0_0_7.md`, **1** in `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md`; `git show HEAD:docs/SPECS/spec-021-apps-0_0_7.md | grep -c 'dependency order'` -> **0**, so the claim is this cycle's own. I also swept for the claim spelled otherwise — `grep -nE 'depend'` and `grep -nE '\border(ing|ed)?\b'` over both files, read line by line — and every other hit is a different subject (slice sequencing, `INSTALLED_APPS` ordering, consumer import order, "one patch module per third-party dependency"). **Three sites, no fourth.**

- `docs/SPECS/spec-021-apps-0_0_7.md` `## Slice checklist` Slice 1, the `ready()` sub-bullet — "three `apply()` calls in dependency order (`django`, `strawberry`, `cross_web`)" -> "in this order". Reason: the parenthetical already states the sequence; "dependency" asserted a cause the source does not carry.
- `docs/SPECS/spec-021-apps-0_0_7.md` `### Decision 4 — `ready()` applies the upstream patches`, first paragraph — "in dependency order — `…_django_patches.py::apply`, then …" -> "in this order — …". Same reason; the three symbol paths that follow are the sequence.
- `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` `### [Decision 4 — `ready()` applies the upstream patches][spec-021-d4]`, reconciliation-table row 4 — "requiring the three-applier dispatch in dependency order" -> "in the order the shipped `ready()` makes the calls". Reason: the row describes the spec sub-bullet above, so it had to stop asserting what that sub-bullet no longer asserts.
- Same rationale section, a new bullet in **Rejected while reconciling it** recording why the phrase was struck and why no substitute reason was invented, keyed to Decision 4 by heading and anchor. Its evidence: `apps.py::DjangoStrawberryFrameworkConfig.ready` asserts no ordering constraint; `tests/test_apps.py::test_ready_dispatches_all_three_patch_appliers_and_refires_safely` asserts installation, not sequence; the three appliers replace **disjoint** targets, which I verified at source rather than taking on report — `_django_patches` targets `SimpleTestCase._remove_databases_failures`, `_strawberry_patches` assigns `BaseView.parse_json`, `BaseView.parse_query_params`, `SyncBaseHTTPView.parse_multipart` and `AsyncBaseHTTPView.parse_multipart`, `_cross_web_patches` assigns `DjangoHTTPRequestAdapter.body`; and `django_strawberry_framework/_cross_web_patches.py` #"request/response abstraction Strawberry's Django view is built on" puts `cross_web` *under* Strawberry, so a literal dependency order is the reverse of the shipped sequence. The citation substring was chosen to fall inside one source line — the wrapped form `is the HTTP request/response abstraction …` occurs **0** times, the unwrapped form **1**.
- Same section, `**Claims this decision may no longer make:**` gained "that the dispatch sequence is a *dependency order*", so a later author reintroducing the phrase meets a standing refusal.
- `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` link definitions: one new def `[glossary]: ../../GLOSSARY.md` under `<!-- docs/ -->`, alphabetically before `[glossary-djangolistfield]`, disk-exists-checked (`docs/SPECS/appx/../../GLOSSARY.md` resolves, 285,513 bytes). All 10 canonical group headers were already present and ordered; the scaffold check passes.

**The correction is the fact with no reason attached**, matching what R2 landed in the DB: spec and rendered glossary now both read "in this order". No substitute rationale was invented — an unsupported claim swapped for another unsupported claim is the same defect. **The spec narrates no history**; the whole account of how the phrase arrived and why it went lives in the rationale file, which is where chronology belongs.

Post-edit re-derivation, run after the last edit to either file: `grep -o 'dependency order'` -> **0** in the spec, **2** in the rationale — both are my own additions (the rejected-alternative bullet and the may-no-longer-make claim), each of which *names* the rejected phrase rather than asserting it, and there is no other occurrence in either file. `grep -o 'in this order'` -> **2** in the spec, **1** in the rationale. Anchor sweep re-run over both files after the edits (headings slugged from rendered text, code fences stripped, in-page `](#…)` uses plus this-file reference defs): spec 31 headings / 15 in-page anchors / **0** dangling, rationale 27 headings / 6 in-page anchors / **0** dangling. The one apparent dangle (`#django-appconfig`) is inside a `#"…"` citation quoting `docs/GLOSSARY.md`'s own index link, not a link in this file; the target anchor exists in the glossary DB. No heading text changed this pass, so no anchor moved.

Byte counts after the last edit (`wc -c`): `docs/SPECS/spec-021-apps-0_0_7.md` **64,801**, `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` **81,986**.

### Dispatched findings checklist audit

I am not the original ticker. Each box re-checked against the working tree on my own instruments; **all three ticks hold, none is over-ticked, none is left open, and nothing is deferred for a box.**

- **F5 — `- [x]` confirmed.** `GlossaryTerm` pk 448's `body` read through the ORM carries the three-applier dispatch, the three in-page anchors, the gate, idempotence, the four negatives and the unchanged `**See also:**` line; the rendered `docs/GLOSSARY.md:530` carries the identical text after the concurrent regenerate. The entry no longer says one applier.
- **F6 — `- [x]` confirmed.** `CardItem` pk 750's `text` scopes "no `ready()` body" to this card's own diff, states the `0.0.7` body arrived with `DONE-024-0.0.7`, and dates the other two appliers to `0.0.11`, which I re-derived from tag content (below). Rendered at `KANBAN.md:4053` and once in `KANBAN.html`.
- **F8 — `- [x]` confirmed.** The comment above `forbidden = {` is the pinned six-line replacement; no spec number, no supersession narrative, no test names, no count of tests. `spec-017` occurrences in the file: **0**. The three `forbidden` keys and all eight test functions are unchanged, and the suite passes.

No box was un-ticked, none was ticked by me, and no `- [ ]` remains, so no deferral reason is owed under `### Spec changes made (Worker 1 only)`.

### Escalation resolution — the "in dependency order" gloss

**Resolved by fixing, path (a).** Worker 3's derivation reproduces in full on my instruments: the population is exactly three occurrences, all introduced this cycle by R1, none pre-existing at `HEAD`; the source carries no ordering rationale; the only layering statement in the package runs the other way. The three sites are struck to "in this order" and the rationale carries the record. Path (b) — keeping the phrase and supplying a dependency argument — was rejected because no such argument exists in the source and manufacturing one would repeat the defect in a new costume.

What I deliberately did **not** add: a sentence claiming the order is *irrelevant*. The disjoint-target evidence supports it, and `## Edge cases and constraints` already makes the neighbouring point about `INSTALLED_APPS` position, but the dispatch's rule cuts both ways — the spec says what the code does, and nothing more, unless the contract is cited. That evidence lives in the rationale, where it is doing the job of explaining a rejection.

The glossary and the spec now agree word for word on the clause, and both agree with `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`, which calls `apply_django()`, `apply_strawberry()`, `apply_cross_web()` in that sequence.

### Routed item 1 — `### The release facts this cohort's wording rests on`

**Worker 3 is right and Worker 2's flag was wrong; I fixed the evidence cell, not the sentence.** Re-derived from tag content, never from `pyproject.toml` at a work commit and never with `git merge-base --is-ancestor`:

| command | result |
|---|---|
| `git show 0.0.7:django_strawberry_framework/apps.py` | `def ready` present; `_django_patches` import + bare `apply()`. **One** applier. |
| `git show 0.0.10:django_strawberry_framework/apps.py` | same shape. **One** applier. |
| `git show 0.0.11:django_strawberry_framework/apps.py` | three aliased imports, `apply_django()` / `apply_strawberry()` / `apply_cross_web()`. **Three**. |
| `git tag \| sort -V` | `0.0.7 0.0.8 0.0.9 0.0.10 0.0.11 0.0.13` (plus two `backup-*` refs, not releases) |
| `grep '^## \[' CHANGELOG.md` | `[0.0.8] [0.0.9] [0.0.10] [0.0.11]` lie between `[0.0.7]` and the shipping release |

So `0.0.11` is exactly the fourth release after `0.0.7`: **the sentence is right**, and what could not support it was the cell (`git show c7cb5f5c:pyproject.toml` -> `version = "0.0.10"`, the pre-bump reading this cycle exists to retire). The row's command and result now carry the tag-content derivation and the release count, so claim and evidence agree.

**A second row in that table carried the same instrument defect, unflagged by either reviewer, and I fixed it too.** The last row read "the dispatch test came later still | `136c5476` | version `0.0.13`". `git show 0.0.13:tests/test_apps.py | grep -c test_ready_dispatches_all_three_patch_appliers_and_refires_safely` -> **0**: the test is absent from the last tag cut. `136c5476` is dated 2026-07-13, between `[0.0.13] - 2026-07-06` and `[0.0.14] - 2026-07-20`, so the test ships at **`0.0.14`**, not `0.0.13` — exactly the pre-bump misreading, one release off, in the same table. The row now states the tag probe and the `0.0.14` conclusion. Propagation swept after the change: `136c5476` occurs in four other files, and none of them claims `0.0.13` — `docs/builder/build-021-apps-0_0_7.md`'s corrected release table already reads `0.0.14` with `pyproject.toml at the commit reads 0.0.13` as its explicit caveat, and the rationale's chronology row carries a date and no version. The first row's `72f6cd9` (a kanban renumber commit, not a release) was replaced by the `0.0.7` tag itself for the same reason.

### Routed item 2 — the misfiled `## Build report (Worker 1, pass 2 — apply-changes)` section

**Subset relation re-confirmed by me, then removed.** Instrument, before deleting anything: R2's copy at `docs/builder/bld-review-2-db_backed_doc_reconciliation.md:207` extracted to lines 207-308 (**102** lines) and R1's at `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md:479` to lines 479-582 (**104** lines); `comm -23` over the sorted unique line sets -> **0** lines present in R2's copy and absent from R1's; `comm -13` -> **1** line present only in R1's. R2's copy is a strict subset; removing it loses nothing, and R1's own copy is intact (`grep -c '^## Build report (Worker 1, pass 2'` over R1's artifact -> **1**).

Removed lines 206-308 (the section, its trailing separator and the surrounding blank lines), keeping the `---` that already separated the plan from what follows. This artifact went from **798** to **695** lines, `-103`; the next `##` heading after `## Plan (Worker 1)` is now `## Build report (Worker 2)`. A pre-deletion copy was kept outside the repo for the duration of this pass. The four surviving mentions of the section — Worker 2's intrusion note and its `### Notes for Worker 3`, and both Worker 3 passes' routing items — are prior entries and stay exactly as written; they now read as the record of a resolved routing rather than a live one. **Worker 2's decision to leave the section in place was correct under `AGENTS.md` rule 34 and is not a defect**; relocating another cohort's build report is a custodian action.

### Worker 3's Low, filed here

`## Build report (Worker 2, pass 2)` `### Implementation notes` heads a bullet **"The gloss is not re-stated anywhere else."** The bullet's body names its corpus correctly ("Swept the **DB** for the phrase") and both its figures reproduce on my read — 0 `GlossaryTerm` bodies, 0 `CardItem` texts, measured through the ORM across all 142 terms. **The heading claims a repo-wide scope the sweep did not have**, and at repo scope it was false when written: three live sites in the two `spec-021` files, now closed by this pass. Corrected here in the record, not by editing that entry — prior entries are immutable. The heading is true as of this pass, and it was not true as of the pass that wrote it.

### Spec reconciliation

Read `docs/SPECS/spec-021-apps-0_0_7.md` end to end against `django_strawberry_framework/apps.py` and `tests/test_apps.py` at `HEAD`, as a reader with no knowledge of this cycle. It states the shipped contract cleanly and completely: the two class attributes and two docstrings with their ruff rules; the `ready()` override whose body is the three-applier dispatch from function-local imports; the gate inside each `apply()` with the per-dependency mapping form; idempotence and reload behavior; the four things `ready()` does not do; the three-key negative-shape set with `"ready"` called out as required rather than forbidden; the eight tests, named, each with what it distinguishes. Every one of those checks against source: `ready` is in `DjangoStrawberryFrameworkConfig.__dict__`, the three imports are inside the method, the `forbidden` mapping has exactly `label` / `default_auto_field` / `default`, and the suite is 8 tests. `## Definition of done` item 4's "8 tests" and item 9's "`ready()` included" both hold. The glossary entry agrees with the spec on every clause it shares — dispatch, sequence, function-local imports, gate placement, idempotence, the `finalize_django_types` negative, `INSTALLED_APPS` discovery — and now on the wording of the sequence clause itself. **No further spec change is owed by this diff.**

### DRY check

- **Spec Decision 4 vs the glossary entry vs the card note.** Three descriptions of `ready()`, three different subjects by the plan's design: the spec is the contract, the glossary describes the package's current state, the card note describes what card 021's own diff shipped. Read against each other after my edits, none restates another's argument and none contradicts another. The one clause they share verbatim is the sequence, which is the point.
- **Spec vs rationale.** The rationale's Decision 4 section explains and the spec asserts; my new bullet adds the ordering argument in exactly one place, the rationale, and the spec carries none of it. No argument is told twice.
- **The patch inventory is still stated once.** `ready()`'s docstring, Decision 4 and the glossary entry each decline to enumerate which upstream bug each module fixes, each saying the module docstrings own it. Still three declines and zero copies.
- **No claim stated in one place and contradicted in another** across the spec, the rationale and the glossary body — the "dependency order" split was the only one, and it is closed.

### Deferred work catalog — R2's, consolidated and re-derived

R1's catalog is already published at `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md` `### Deferred work catalog — consolidated and re-derived`; `bld-final.md` should point at it rather than restate it. Below is **R2's**, gathered from the `### Notes for Worker 1 (spec reconciliation)` blocks of the plan, both Worker 2 passes and both Worker 3 passes, with every population re-derived by me at this pass's write time.

1. **No glossary term covers the Strawberry or `cross_web` upstream patches.** Source: this artifact's `## Plan (Worker 1)` `### Implementation discretion items` and `### Notes for Worker 1`, endorsed by both Worker 3 passes. Licensing clause: none — no dispatched finding asks for the term; `spec-021` `## Doc updates` scopes the glossary work to the `Django AppConfig` entry. **Candidate, not built**: a new term needs an index row, a category membership and a `check_spec_glossary` story. Re-derived: across **142** `GlossaryTerm` rows, the only body naming `_strawberry_patches` or `_cross_web_patches` is pk **448** itself, and **0** anchors contain `patch`. The `**See also:**` line was deliberately not widened — `#utf-8-wire-contract` and `#request-body-cap` each state in their own bodies that they are *not* upstream-bug patches, so pointing at them would create a cross-reference the target contradicts. **Corpus rule, not a digit** (a concurrent session is writing this DB): the term is missing for as long as no `GlossaryTerm.body` outside pk 448 names those two modules — re-run that probe at write time.
2. **Repo-wide instrument note: "version at `pyproject.toml` at the work commit" is not "shipping release".** Source: Worker 3 pass 2 `### Notes for Worker 1` item 3, endorsed. The bump lands at the cut, so `git show <commit>:pyproject.toml` reports the **previous** release. Use tag content or the `CHANGELOG.md` date. `git merge-base --is-ancestor` is **not** the substitute — concurrent sessions rewrite this branch's history and it answers `NO` for `c7cb5f5c` against tags whose content plainly contains it. The class has now produced **four** wrong or unsupported readings in this cycle: the plan's `### F9` row (fixed by Worker 0), the card note's `0.0.10` (fixed in pass 2), this artifact's release-facts evidence cell, and its dispatch-test row's `0.0.13` — the last two fixed by me above, and the fourth found only because I re-derived a row nobody had flagged. Nothing is open; the note is carried so the next cycle inherits the instrument rule, not the digits.
3. **R1 catalog item 1 — `CHANGELOG.md`'s `[0.0.7]` one-applier entry — re-grades to resolved-not-a-defect.** Source: this artifact's `### F9 is not this cohort's work` and both Worker 3 passes. Re-derived on my instruments: `git show 0.0.7:django_strawberry_framework/apps.py` carries exactly one applier, so the entry is accurate as history; "correcting" it to three would falsify it, and `AGENTS.md` rule 21 forbids the edit independently. `git diff HEAD -- CHANGELOG.md` -> **0** lines. Record it in `bld-final.md` as resolved-not-a-defect, **not** as an open item.
4. **F8 must not appear in the catalog.** Source: the plan's `### Notes for Worker 1` and Worker 3 pass 2 item 5. It is R2's work item, it landed, and both its ticks are audited above.
5. **Closed by this pass, listed so the final gate does not re-open them:** the escalated "in dependency order" gloss (3 sites, all struck); the release-facts evidence cell and the dispatch-test row; the misfiled R1 build-report section (removed, 103 lines); Worker 3's Low on the DB-scoped sweep's repo-scoped heading (corrected in the record above). None is deferred work.
6. **Recorded, not a deferral: the concurrent rewrite of `GlossaryTerm` pk 504.** A parallel cohort's row and its regenerate moved `docs/GLOSSARY.md` and the DB under this review. R2's two rows and all three rendered lines survive it, verified by me above. Nothing was reverted (`AGENTS.md` rule 34). Any `docs/GLOSSARY.md` whole-file hash or "one changed line" figure from the pass-2 review sections is superseded — **re-run, never copy**, since that cohort is still writing.

### `git status --short` at this pass's close

31 paths. Mine, and inside my writable set: `docs/SPECS/spec-021-apps-0_0_7.md`, `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` (untracked), this artifact (untracked). R2's, landed and audited: `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3`, `tests/test_apps.py`. Everything else is concurrent-session work — **recorded, not reverted, not staged**: 7 package modules (`auth/mutations.py`, `mutations/inputs.py`, `mutations/resolvers.py`, `mutations/sets.py`, `rest_framework/resolvers.py`, `utils/inputs.py`, `utils/write_values.py`) and 5 test modules under a refactor; `docs/SPECS/spec-022-export_schema-0_0_7.md`, `docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`, one further `docs/` file; `docs/builder/build-020-list_field-0_0_7.md` (staged deleted) with `docs/builder/DONE/build-020-list_field-0_0_7.md` (untracked); and the untracked `appx/spec-022-…-rationale.md`, `bld-review-1-spec_022_reconciliation.md`, `bld-review-2-spec_022_glossary_body.md`, `build-021-apps-0_0_7.md`, `build-022-export_schema-0_0_7.md`. `docs/builder/bld-003-final.md` is not dirty at this pass's close, contrary to the plan's baseline note — re-derived, not copied. No `.py` file was edited by me, so no ruff run was owed and none was made.

Status: final-accepted.
