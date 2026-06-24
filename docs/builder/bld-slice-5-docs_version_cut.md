# Build: Slice 5a — version quintet (ex-GLOSSARY-line) + plain docs + CHANGELOG

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (Slice 5 checklist lines 464-486; `## Doc updates` lines 2086-2128; Decision 14 lines 1835-1862; Definition-of-done items 7-8 lines 2419-2439). Build-plan flags: `docs/builder/build-038-form_mutations-0_0_12.md` lines 16-25 (version-bump owner = this card; CHANGELOG AUTHORIZED). The DB-backed GLOSSARY promote/correct + GLOSSARY version-line BoardDoc + KANBAN card move + regenerate are carved out to the sibling **`docs/builder/bld-slice-5b-glossary_kanban_db.md`**.
Status: final-accepted

> **CARVE NOTICE (Worker 1).** Slice 5 was split into **5a + 5b** (the split spec edit is recorded under `### Spec changes made (Worker 1 only)` below). This artifact carries the **5a** plan only: the version quintet EXCEPT the DB-backed `docs/GLOSSARY.md` package-version line (`pyproject.toml`, `__version__` in `__init__.py`, `tests/base/test_init.py::test_version`, `uv.lock`) + the plain docs (`docs/README.md`, `README.md`, `GOAL.md`, `TODAY.md`, `docs/TREE.md`) + `CHANGELOG.md` (maintainer-AUTHORIZED). The 5b plan (DB-backed GLOSSARY promotion/correction, the GLOSSARY package-version `BoardDoc`, the KANBAN card move, the three regenerates) lives in `docs/builder/bld-slice-5b-glossary_kanban_db.md`.

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - The version quintet is the **exact same five-site edit** `spec-037` Decision 10 performed for the `0.0.11` cut (spec lines 1844-1851): `pyproject.toml [project].version` (`pyproject.toml` line 4), `__version__` in `django_strawberry_framework/__init__.py` (line 37), `tests/base/test_init.py::test_version` (the `assert __version__ == "0.0.11"` at line 19), the `docs/GLOSSARY.md` package-version line (DB-backed — **carved to 5b**), and `uv.lock` (the package's own `version = "0.0.11"` at line 218, directly under `name = "django-strawberry-framework"` at line 217). No new mechanism — mirror the prior cut. **5a edits four of the five sites; the DB-backed GLOSSARY package-version line is 5b.**
  - The CHANGELOG entry reuses the established `## [0.0.X] - DATE` + `### Added` / `### Changed` shape (the `[0.0.11]` block at `CHANGELOG.md` lines 19-34 is the template); canonical phrasings crib from `docs/README.md` line 123-124 and the spec's Goals/Decision-6 prose.
- **New helpers justified.** None. Slice 5a touches no package logic — it is version strings, prose edits, and a CHANGELOG entry. No helper, module, or constant is created.
- **Duplication risk avoided.**
  - **Version-string drift** (AGENTS.md rule 31: `pyproject.toml` and `__init__.py` MUST match). The plan pins all four 5a sites in one list and the final-verify greps `0.0.11` across them to prove none was missed (the fifth site, the GLOSSARY package-version line, is 5b's responsibility — 5a final-verification defers it with a recorded reason).
  - **Re-flowing prose into stale version tags.** The plain-doc edits are status/version flips; the risk is leaving an old-version "coming soon" string alongside a flipped one. The plan pins each old string and its replacement; Worker 3's documentation-sanity check (BUILD.md lines 322-333) backstops "no obsolete coming soon / planned / old-version wording remains".

### Implementation steps

Line numbers are pin-at-write-time hints; verify against current source before editing.

#### Static-helper skip (record)

`scripts/review_inspect.py` is **SKIPPED for the entire sub-slice**: Slice 5a touches no package `.py` logic — only version strings (`pyproject.toml`, `__init__.py`, `uv.lock`), a test constant (`tests/base/test_init.py`), standing prose docs, and `CHANGELOG.md`. No file under `django_strawberry_framework/` gains logic; the BUILD.md run-triggers (≥150-line file gaining logic; `optimizer/` / `types/` edits; ≥30 new logic lines) are not met. NEVER pass `--cov*` anywhere in this slice.

#### 5a — version quintet (Decision 14)

Bump `0.0.11` → `0.0.12` at the four non-DB sites. Do NOT bump anywhere else; the bump moves ONLY in this slice (build-plan flag).

1. `pyproject.toml` line 4: `version = "0.0.11"` → `version = "0.0.12"`.
2. `django_strawberry_framework/__init__.py` line 37: `__version__ = "0.0.11"` → `__version__ = "0.0.12"`. (MUST match `pyproject.toml`, AGENTS.md rule 31.)
3. `tests/base/test_init.py::test_version` line 19: `assert __version__ == "0.0.11"` → `... == "0.0.12"`. (This is the only TEST edit in the slice — see `### Test additions / updates`.) Also sweep the surrounding comment block (lines ~41-48 narrate the `0.0.11` joint cut owning `test_version`); a one-line note that `038` owns the `0.0.12` cut is allowed but not required — Worker 2 discretion (see discretion items).
4. `uv.lock` line 218: `version = "0.0.11"` (the entry directly under `name = "django-strawberry-framework"` at line 217) → `0.0.12`. Edit ONLY the package's own version stanza; do not touch any dependency version. If `uv` would otherwise rewrite the lock, prefer the minimal in-place string edit (no `uv lock` run — that risks unrelated dependency churn in the diff; if a hash/consistency field forces a `uv lock --offline` refresh, record it in the build report and confirm the diff is confined to the package stanza).
5. The `docs/GLOSSARY.md` package-version line is **DB-backed** — it is NOT edited here; it is part of **5b** (the `BoardDoc` edit + glossary regenerate). 5a does not touch `docs/GLOSSARY.md`.

After 5a version edits: `uv run ruff format .` then `uv run ruff check --fix .` (AGENTS.md rule 15). No pytest.

#### 5a — plain docs (Doc updates, spec lines 2116-2124)

All cross-file links follow the reference-style convention (START.md / AGENTS.md rule 28): inline `[text][ref-id]`, defs in the bottom unified block under the correct path-based group header. Reuse existing ref-ids where present; only add a def if a genuinely new cross-file link is introduced (unlikely — these are status/prose flips, not new links).

6. `README.md`:
   - **Status line** (line 61): `**`0.0.11`, single-maintainer, alpha-quality.**` → `0.0.12`; refresh the "Newest shipped surface" prose so form mutations are named as the newest surface (the `Upload`/`DjangoFileType` text currently leads). Keep it factual: the `ModelForm` + plain-`Form` write flavors on the `class Meta` surface, the form-derived input, `form.errors` → the shared `FieldError` envelope.
   - The line-57 "Mutations ship today" sentence already names `0.0.11` `DjangoMutation` and the `0.0.13` serializer flavor; ADD the `0.0.12` `ModelForm` / `Form` flavor as now-shipped (it currently jumps `0.0.11` → `0.0.13`). Do not overstate: `ModelSerializer` stays `0.0.13`.
7. `docs/README.md`:
   - **"Shipped today (`0.0.11`)"** header (line 97): the spec says move form mutations from "Coming next (`0.0.12`)" to "Shipped today". Bump the "Shipped today" version tag to `0.0.12` and ADD a form-mutations bullet to the shipped list (mirror the `0.0.11` mutation bullet at line 123 in shape: the two bases, `Meta.form_class`, form-derived input via `forms/converter.py`, `form.errors` → `FieldError`, the plain-form `ok`+`errors` payload vs the `ModelForm` `node`/`result` payload, both exported from the root).
   - **"Coming next" block** (lines 126-127): DELETE the `- `0.0.12` — form-based mutations (Django Forms / ModelForms)` line; the block now opens at `0.0.13`. Reword the block header `**Coming next — remaining alpha (`0.0.12` → `0.0.14`):**` → `(`0.0.13` → `0.0.14`)`.
8. `GOAL.md`:
   - Criterion 6 (line 511): the `ModelForm` flavor now ships (`0.0.12`); update the trailing clause "the `ModelForm` (`0.0.12`) and `ModelSerializer` (`0.0.13`) flavors still land later" → the `ModelForm` flavor shipped in `0.0.12`, only `ModelSerializer` (`0.0.13`) remains.
   - Line 458 prose names `0.0.11` `DjangoMutation` + the `0.0.13` serializer flavor; add the `0.0.12` `ModelForm`/`Form` flavor as shipped. `ModelSerializer` stays `0.0.13` (do not move it).
9. `TODAY.md`:
   - Note form mutations as a package capability and that **products now demonstrates a `ModelForm` write surface** (Slice 4 added `products/forms.py` + form `DjangoModelFormMutation`/`DjangoFormMutation` to `products/schema.py`). The natural sites: the `0.0.11` capability list around lines 11-25 (add a "form mutation write surface" bullet, `0.0.12`) and the "Mutations on products today" section around lines 324-354 (note the form-backed mutations alongside the model-driven ones). Keep claims matched to what Slice 4 actually shipped (an `ItemModelForm` + a plain `Form`, a `categoryId`-through-form, a multipart `Upload`, the `{ok,errors}` plain payload).
10. `docs/TREE.md`:
    - **Current on-disk layout** (`## django_strawberry_framework (current on-disk layout)`, line 188; Source `django_strawberry_framework/` line 190): ADD the now-existing `forms/` subtree (on disk: `__init__.py`, `converter.py`, `inputs.py`, `resolvers.py`, `sets.py`) in its alphabetical slot, with the one-line summary the section's style uses. **Do NOT touch the line-39 `forms/`** — that is under `## graphene_django` (the upstream `.venv` tree), unrelated.
    - **Target package layout** (line 250; line 280 `forms/    # planned by TODO-ALPHA-038-0.0.12 - …`): FILL the planned line — drop the `# planned by TODO-ALPHA-038-0.0.12` annotation and list the `forms/` files with summaries (now that it ships, it is no longer "planned"). Per the section's own rule (line 252: "planned entry names the card that introduces it"), a shipped subtree is rendered like the other on-disk entries.
    - **Current test trees** (line 332) + **Target test shape** (line 464, line 497 `forms/ # planned by TODO-ALPHA-038-0.0.12`): ADD the now-existing `tests/forms/` subtree to the current trees (on disk: `test_converter.py`, `test_inputs.py`, `test_sets.py`, `test_resolvers.py` — verify the exact filenames against `tests/forms/` at build time) and FILL the planned `tests/forms/` line in the target shape (drop the `# planned by` annotation).

#### 5a — CHANGELOG.md (AUTHORIZED — build-plan flag line 19)

11. Add a new release block. The repo's CHANGELOG carries dated released blocks (`## [0.0.11] - 2026-06-19`, etc.) with NO standing `[Unreleased]` section at present — so add a fresh **`## [0.0.12] - <DATE>`** block at the top of the version list (immediately above `## [0.0.11] - 2026-06-19` at line 19). (The build-plan flag's "`[Unreleased]`→`0.0.12`" wording describes the conceptual move; mechanically this repo cuts a dated block per release — match the shipped `[0.0.11]` shape. If Worker 2 finds an `[Unreleased]` section was added by concurrent work, fold into it instead and note it.)
    - **`### Added`**: the two new bases — `DjangoFormMutation` (plain model-less `Form`, its own metaclass + declaration registry, pinned `ok: Boolean!` + `errors: [FieldError!]!` payload, `perform_mutate` hook) and `DjangoModelFormMutation` (subclasses `DjangoMutation` via the `_resolve_model` seam, returns the post-save object in the uniform `node`/`result` slot) on the `class Meta` (`Meta.form_class` + optional `fields`/`exclude`) surface; the `forms/converter.py` form-field → Strawberry-input mapping reusing the read-side scalar/enum/`Upload` converters; the `form.errors` → frozen `FieldError` envelope mapping (`NON_FIELD_ERRORS` → `"__all__"`); the relation-visibility-on-every-branch form decoder; sync+async; both bases exported from the package root (two net-new public exports added to `__all__`).
    - **`### Changed`**: `django_strawberry_framework.__version__` is now `0.0.12` (mirror the `[0.0.11]` "is now `0.0.11`" line at CHANGELOG line 34). The `036` `DjangoMutationField` factory was generalized along three axes (target-check, `_resolve` dispatch, `data:` lazy-ref) to expose the form flavors — the model-driven path is unchanged (no consumer-visible regression). Note this carefully: it is a no-regression internal generalization, not a breaking change — do not overstate.
    - Heading discipline: use ONLY `### Added` / `### Changed` (the spec authorizes these; no `### Fixed` / `### Removed` — Slice 5 ships no fix/removal). The version line MUST read `0.0.12` to match `pyproject.toml`/`__init__.py` (Worker 3's CHANGELOG sanity check, BUILD.md lines 311-320). Reference-style links for any glossary/file refs in the entry (match the existing CHANGELOG link style — it already uses `[text][ref-id]` with a bottom def block; reuse existing `[glossary-djangomutation]` etc. ref-ids, add `[glossary-djangoformmutation]` / `[glossary-djangomodelformmutation]` defs if they are not already present in the CHANGELOG's def block — verify).
    - **CHANGELOG hedge dropped (authorized).** The spec's Slice-5 sub-bullet conditions the CHANGELOG edit on "only if the Slice 5 maintainer prompt explicitly requests it"; the maintainer **explicitly authorized** the CHANGELOG edit on 2026-06-23 (build-plan flag line 19). That hedge is therefore satisfied — 5a DOES add the `[0.0.12]` entry; it is not optional/contingent for this build.

After all 5a edits: `uv run ruff format .` + `uv run ruff check --fix .`. No pytest.

### Test additions / updates

- `tests/base/test_init.py::test_version` — change the assertion from `assert __version__ == "0.0.11"` to `assert __version__ == "0.0.12"` (step 3). This is the ONLY test edit in the slice. It pins the version quintet's package-facing value; it will pass once `__init__.py` is bumped (step 2) and fail loudly if the bump is missed. The surrounding comment block (lines ~41-48) narrating the `0.0.11` joint cut may get a one-line refresh (discretion).
- No other test is added or changed. Slice 5a ships no package logic; the form-mutation behavior is already pinned by Slices 1-4's `tests/forms/` + `test_products_api.py`. Worker 3 reads the diff against the spec rather than running coverage. No temp/scratch tests are appropriate (no logic under test).

### Implementation discretion items

Assessed and decided to be Worker 2's choice (style / equivalent-shape only; none architectural):

- The exact wording of the `CHANGELOG.md` `### Added` / `### Changed` bullets, within the spec-authorized content + the no-overstate constraint (Worker 3's CHANGELOG sanity check is the backstop).
- The exact one-line summaries for the `forms/` / `tests/forms/` subtrees in `docs/TREE.md` (match the section's house style).
- Whether to add the optional one-line `038-owns-the-0.0.12-cut` note to the `tests/base/test_init.py` comment block (lines ~41-48) — allowed, not required.
- The order of the independent 5a edits among themselves.

### Spec slice checklist (verbatim)

The spec's `## Slice checklist` Slice 5 nested sub-bullets, copied verbatim (preserve text, nesting, inline citations). These two boxes are the **monolithic** Slice-5 sub-bullets; they mix 5a and 5b targets. **5a delivers** its portion of each (annotated below); the **5b portions are deferred to `bld-slice-5b-glossary_kanban_db.md`** (5a final-verification will record a deferral reason for the 5b targets rather than tick the boxes — the monolithic boxes get fully ticked in 5b once the whole contract has landed). Not ticked at planning — Worker 2 ticks each `- [x]` only when that contract lands in its diff; Worker 1 audits at final verification.

**5a delivers:** the version quintet EXCEPT the DB-backed `docs/GLOSSARY.md` package-version line — `pyproject.toml`, `__version__` in `__init__.py`, `tests/base/test_init.py::test_version`, `uv.lock`; the plain docs `docs/README.md`, `README.md`, `GOAL.md`, `TODAY.md`, `docs/TREE.md`; and `CHANGELOG.md` (maintainer-authorized).

**Deferred to 5b** (carved to `bld-slice-5b-glossary_kanban_db.md`): the `docs/GLOSSARY.md` promotion of `DjangoFormMutation` / `DjangoModelFormMutation` to `shipped (0.0.12)` + their Public-exports / Index / Mutations rows + the `DjangoFormMutation` body correction (Decision 6); the `docs/GLOSSARY.md` package-version line move to `0.0.12` (the DB-backed `BoardDoc`); and the `KANBAN.md` card → Done move (`WIP-ALPHA-038-0.0.12` → `DONE-038-0.0.12`). Because each box below mixes 5a and 5b targets, 5a final-verification records it as partially-landed (5a portions ticked, 5b portions deferred with reason); 5b ticks the boxes fully.

- [ ] **Version files to `0.0.12`**
  ([Decision 14](#decision-14--this-card-owns-the-0012-version-bump)):
  [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init],
  [`tests/base/test_init.py::test_version`][test-base-init], the
  [`docs/GLOSSARY.md`][glossary] package-version line, and `uv.lock` if it
  carries the package version.
- [ ] [`docs/GLOSSARY.md`][glossary] (promote
  [`DjangoFormMutation`][glossary-djangoformmutation] /
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] to
  `shipped (0.0.12)`; add both to **Public exports** + the **Index** + the
  **Mutations** browse-by-category row; move the package-version line to `0.0.12`),
  [`docs/README.md`][docs-readme] / [`README.md`][readme] (move form mutations
  from "Coming next (`0.0.12`)" to "Shipped today" and the README **Status** line
  from `0.0.11` to `0.0.12`), [`GOAL.md`][goal] (criterion 6's `ModelForm` flavor
  now ships; the `ModelSerializer` flavor stays `0.0.13`), [`TODAY.md`][today]
  (note form mutations as a package capability — products now demonstrates a
  `ModelForm` write surface), [`docs/TREE.md`][tree] (fill the planned `forms/` /
  [`tests/forms/`][test-forms] summary lines), [`CHANGELOG.md`][changelog] (only
  if the Slice 5 maintainer prompt explicitly requests it), [`KANBAN.md`][kanban]
  (card → Done via the kanban DB + re-render).

> **Worker 2 (5a build pass) — checklist landing note.** Both boxes above are monolithic and mix 5a + 5b targets, so neither is fully landed by 5a; per worker-2.md ("never tick a box for a deferred or not-yet-built sub-check") I leave both `- [ ]` and record the partial landing here for Worker 1's final-verification audit and for 5b to tick fully:
> - **Box 1 (Version files to `0.0.12`):** 5a LANDED `pyproject.toml`, `__version__` in `__init__.py`, `tests/base/test_init.py::test_version`, and `uv.lock` (all `0.0.12`, focused `test_version` passes). DEFERRED to 5b: the `docs/GLOSSARY.md` package-version line (DB-backed `BoardDoc`).
> - **Box 2 (docs / card wrap):** 5a LANDED `docs/README.md`, `README.md`, `GOAL.md`, `TODAY.md`, `docs/TREE.md` (`forms/` + `tests/forms/` summary lines filled), and `CHANGELOG.md` (maintainer-authorized). DEFERRED to 5b: `docs/GLOSSARY.md` (promote both symbols to `shipped (0.0.12)` + Public-exports/Index/Mutations rows + Decision-6 body correction + the package-version line) and `KANBAN.md` (card → Done via the kanban DB + re-render).

---

## Build report (Worker 2)

### Files touched

All ten are slice-intended (the 5a contract); each diff against HEAD is small and confined to my edits. (Note: HEAD still carries `0.0.11` with no `forms/`; Slices 1–4 are uncommitted in the working tree, so a `git diff` against HEAD on `__init__.py` etc. also shows Slices 1–4 churn — my line in `__init__.py` is exactly `__version__`.)

- `pyproject.toml` — `[project].version` `0.0.11` → `0.0.12` (version quintet site 1; AGENTS.md rule 31).
- `django_strawberry_framework/__init__.py` — `__version__` `0.0.11` → `0.0.12` (site 2; verified the only line I changed — the `.forms` import + the two `__all__` entries are Slice 2's, not mine).
- `tests/base/test_init.py` — `test_version` assertion `0.0.11` → `0.0.12` (site 3); plus the discretionary one-line refresh of the `test_public_api_surface_is_pinned` comment block (lines ~43-50) naming spec-038 as the lone `0.0.12` card owning the cut (Decision 14). NO change to the `__all__` assertion itself — see Notes for Worker 1.
- `uv.lock` — the package's own `version = "0.0.11"` → `0.0.12` (site 4; the stanza at `name = "django-strawberry-framework"` / `source = { editable = "." }`). Minimal in-place string edit, no `uv lock` run, no dependency stanza touched.
- `README.md` — **Status** line `0.0.11` → `0.0.12` + "Newest shipped surface" prose re-led with form mutations (the two `Meta.form_class` flavors, form-derived input, `form.errors` → `FieldError`, `node`/`result` vs `ok`/`errors` payloads); the "Mutations ship today" sentence (Is-this-for-you section) now names the `0.0.12` `ModelForm`/`Form` flavor between the `0.0.11` foundation and the `0.0.13` serializer.
- `docs/README.md` — "Shipped today" header `0.0.11` → `0.0.12`; added a form-mutations shipped bullet mirroring the `0.0.11` mutation bullet; deleted the `0.0.12` line from "Coming next" and re-headed that block `(`0.0.13` → `0.0.14`)`. Added the `[glossary-djangoformmutation]` ref-id to the `<!-- docs/ -->` def group (alphabetical).
- `GOAL.md` — criterion 6 now reads the `ModelForm` flavor ships in `0.0.12` (plus the plain-`Form` sibling), only `ModelSerializer` (`0.0.13`) remains; the DRF + django-filter migration prose (line ~458) gains the `0.0.12` form flavor as shipped. `ModelSerializer` left at `0.0.13`.
- `TODAY.md` — added a `0.0.12` form-mutation capability bullet to the products "What it demonstrates" list, noted the form-backed fields in the "Mutations on products today" intro, and added a "Form-backed mutations (`0.0.12`)" paragraph matching the actual Slice-4 surface (`createItemViaForm`/`updateItemViaForm` `ModelForm`, `createItemWithFileViaForm` multipart `Upload`, `createStampedItemViaForm` `get_form_kwargs` user-inject, `submitContact` plain `Form` `{ok,errors}`). Added the `[glossary-djangoformmutation]` ref-id to the `<!-- docs/ -->` def group (alphabetical).
- `docs/TREE.md` — added the `forms/` subtree (`converter.py` / `inputs.py` / `resolvers.py` / `sets.py`) to BOTH the current on-disk layout and the target package layout (dropping the `# planned by TODO-ALPHA-038-0.0.12` annotation in the target); added the `tests/forms/` subtree (`test_converter.py` / `test_inputs.py` / `test_resolvers.py` / `test_sets.py`) to BOTH the current test trees and the target test shape (dropping the planned annotation). Verified exact on-disk filenames before writing.
- `CHANGELOG.md` — new `## [0.0.12] - 2026-06-23` block (above `## [0.0.11]`), spec-authorized `### Added` (the two bases, the `forms/converter.py` mapping, the `form.errors` → `FieldError` pipeline) + `### Changed` (the no-regression `036` `DjangoMutationField`/base generalization; the `__version__` is-now-`0.0.12` line). Only `### Added` / `### Changed` headings (no `### Fixed` / `### Removed`). Version line `0.0.12` matches `pyproject.toml`/`__init__.py`. Added `[glossary-djangoformmutation]` / `[glossary-djangomodelformmutation]` ref-ids to the CHANGELOG `<!-- docs/ -->` def group (alphabetical) — the existing `[glossary-djangomutation]` / `[glossary-fielderror-envelope]` / `[glossary-djangomutationfield]` / `[glossary-djangomodelpermission]` / `[glossary-upload-scalar]` / `[glossary-configurationerror]` ref-ids were already present and reused.

### uv.lock carries the package version — YES, bumped

`uv.lock` line 218 carries `version = "0.0.11"` directly under `name = "django-strawberry-framework"` with `source = { editable = "." }` (the package's own stanza, not a dependency). Bumped to `0.0.12` via a minimal in-place edit. No `uv lock` refresh was needed (no hash/consistency field forced it); the diff is confined to the one version line.

### Tests added or updated

- `tests/base/test_init.py::test_version` — assertion bumped to `0.0.12` (the only test edit in the slice). Focused run `uv run pytest tests/base/test_init.py::test_version --no-cov` → **1 passed**. No other test added/changed; Slice 5a ships no package logic.

### Validation run

- `uv run ruff format .` — pass (`277 files left unchanged`; my edits are `.md`/`.toml`/`.lock` + an already-formatted test comment). The editable install rebuilt at `0.0.12`.
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- `git status --short` — classified below.
- `uv run pytest tests/base/test_init.py::test_version --no-cov` — **1 passed** (the only focused run the plan permits; no `--cov*`).

#### git status classification

**Slice-5a-intended (stay in the diff; in Files touched):** `pyproject.toml`, `django_strawberry_framework/__init__.py` (my line = `__version__` only), `tests/base/test_init.py`, `uv.lock`, `README.md`, `docs/README.md`, `GOAL.md`, `TODAY.md`, `docs/TREE.md`, `CHANGELOG.md`.

**Slices 1–4 (uncommitted, NOT mine — left untouched):** `django_strawberry_framework/mutations/{fields,inputs,permissions,resolvers,sets}.py`, `registry.py`, `relay.py`, `types/finalizer.py`, `examples/fakeshop/apps/products/{models,schema}.py`, `examples/fakeshop/apps/products/forms.py`, `examples/fakeshop/apps/products/migrations/0002_item_attachment.py`, `examples/fakeshop/test_query/test_products_api.py`, `tests/mutations/*`, untracked `django_strawberry_framework/forms/`, `tests/forms/`, and the six untracked `docs/builder/*.md` build artifacts + the deleted 037-cycle `bld-*.md` / `build-037-*.md`.

**Carve-out / out-of-scope (left exactly as found — NOT touched, NOT reverted):** `examples/fakeshop/db.sqlite3` (concurrent-writer + Slice-4 migration; build-plan flag), `KANBAN.md` / `KANBAN.html` (DB-backed, Slice 5b), `scripts/build_kanban_md.py` (concurrent/Slices), `docs/feedback.md` (baseline-dirty out-of-scope), `docs/SPECS/spec-038-*.md` (Worker-1-only; dirty from the carve edit). **`docs/GLOSSARY.md` is NOT in the dirty list** — confirmed I did not touch it (its promotion + version-line move is Slice 5b).

**No tool churn introduced by me.** `ruff format`/`check` left my ten files unchanged beyond my own edits; nothing to revert.

### Implementation notes

- **Static-helper skip** stands as the plan recorded it: no package `.py` logic touched, so `scripts/review_inspect.py` was not run.
- **CHANGELOG release shape** = a dated `## [0.0.12] - 2026-06-23` block (no standing `[Unreleased]` section exists in this repo; mechanically it cuts a dated block per release, matching the `[0.0.11]` template). The build-plan flag's "`[Unreleased]`→`0.0.12`" wording is the conceptual move.
- **`### Changed` framing** for the `036` generalization is deliberately a no-regression internal-generalization statement (not "breaking"), per the plan's no-overstate constraint — the `0.0.11` model-driven mutation behavior is byte-unchanged at the consumer surface (Slices 2/3 default every new seam to today's model behavior).
- **TODAY.md prose was matched to the actual Slice-4 surface**, not the spec's earlier sketch: I read `products/forms.py` + `products/schema.py` and named the real field set (`createItemViaForm` / `updateItemViaForm` / `createItemWithFileViaForm` / `createStampedItemViaForm` / `submitContact`) and the real form classes (`ItemModelForm`, `ContactForm`, `StampedItemModelForm`, `ItemFileModelForm`).
- **New cross-file links** all point at `docs/GLOSSARY.md#djangoformmutation` (and `#djangomodelformmutation` in CHANGELOG) — the in-page anchor is created by Slice 5b's GLOSSARY promotion, exactly as the pre-existing `[glossary-djangomutation]: ...GLOSSARY.md#djangomutation` convention does. The disk-exists check is on the file `docs/GLOSSARY.md` (exists); anchor resolution lands with 5b.

### Notes for Worker 3

- **CHANGELOG sanity (your check):** the entry is at the top of the version list as `## [0.0.12] - 2026-06-23`; version line matches `pyproject.toml`/`__init__.py`/`uv.lock` (all `0.0.12`); headings are exactly `### Added` + `### Changed` (spec-authorized; no `### Fixed`/`### Removed`). The `### Added` content: the two bases (`DjangoModelFormMutation` rides `DjangoMutation` via `_resolve_model`, returns `node`/`result`; plain `DjangoFormMutation` is the model-less sibling with `ok`+`errors` + `perform_mutate`), the `forms/converter.py` form-field → input mapping reusing the read-side converters, and the `form.errors` → frozen `FieldError` envelope pipeline (`NON_FIELD_ERRORS` → `"__all__"`, relation visibility on every branch, partial update, G2 re-fetch, sync+async, two net-new root exports). The `### Changed` content: the no-regression three-axis `DjangoMutationField` + base-seam generalization, and the `__version__` is-now-`0.0.12` line. Nothing overstated — the generalization is explicitly "not a breaking change".
- **Documentation/release sanity (your check):** all version strings I touched read `0.0.12`; no obsolete "coming soon / planned / `0.0.11`" wording remains in the files I deliberately updated (the `docs/README.md` "Coming next" block now opens at `0.0.13`; the `0.0.12` line is deleted). The `forms/` + `tests/forms/` TREE entries match the on-disk filenames I verified. The four new ref-id defs are alphabetically placed in the correct `<!-- docs/ -->` groups.
- **Carve-outs:** I did NOT touch `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `db.sqlite3`, or `docs/feedback.md`. The GLOSSARY promotion + version-line move + KANBAN card move are Slice 5b.

### Build report addendum (Worker 2 — 5a completion)

This continuation finishes 5a's remaining scope: the public-API export-pin update I flagged in `### Notes for Worker 1` above (now resolved here, not routed out).

- **Files touched (this continuation):** `tests/base/test_init.py` — the `test_public_api_surface_is_pinned` expected-`__all__` tuple. Inserted `"DjangoFormMutation"` (alphabetical slot after `"DjangoFileType"`) and `"DjangoModelFormMutation"` (slot after `"DjangoListField"`), mirroring the live `django_strawberry_framework/__init__.py` `__all__` exactly (23 symbols). No other symbol added. `__init__.py` NOT touched (Slice 2's export add is the correct contract; only the test pin lagged).
- **Validation:** `uv run pytest tests/base/test_init.py --no-cov` → **5 passed**, incl. `test_version` AND `test_public_api_surface_is_pinned` both green at the 23-symbol / `0.0.12` surface (no `--cov*`). `uv run ruff format .` → `277 files left unchanged`; `uv run ruff check --fix .` → `All checks passed!`. No tool churn to revert. Carve-outs (`docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, `docs/feedback.md`) left untouched.
- **Completes spec-038 DoD item 8:** the two net-new public symbols are in `__all__` (Slice 2) AND the export pin is now updated accordingly — DoD item 8's export-pin half is delivered. `Status: built` unchanged.

### Notes for Worker 1 (spec reconciliation)

- **[HIGH — final-test-gate blocker, NOT my slice] `tests/base/test_init.py::test_public_api_surface_is_pinned` currently FAILS.** Slice 2 added `DjangoFormMutation` / `DjangoModelFormMutation` to `django_strawberry_framework/__init__.py`'s `__all__`, but the `__all__` assertion inside `test_public_api_surface_is_pinned` was NOT updated to include them — so the test asserts a stale 21-symbol tuple against the live 23-symbol `__all__`. Confirmed by running it: `FAILED ... At index 4 diff: 'DjangoFormMutation' != 'DjangoImageType'; Left contains 2 more items`. The public-surface pin is **Slice 2's contract** (its spec sub-bullet ships "both bases exported from the package root", which this test pins), not Slice 5a's (my only authorized test edit is `test_version`, per the plan + worker-2.md "do not broaden the slice"). I deliberately did NOT touch the assertion. **Route to Slice 2** (or authorize a Slice-5a follow-up) before the final test-run gate, which runs the full suite and will fail here. The fix is to insert `"DjangoFormMutation"` and `"DjangoModelFormMutation"` into the asserted tuple in their alphabetical slots (after `DjangoFileType` and after `DjangoListField` respectively) — but that is a public-surface pin change, so it must be made under the slice that owns the surface.
- **`docs/TREE.md` had a pre-existing `mutations/` gap I left alone (scope).** Both the **current on-disk layout** and the **target package layout** still render `mutations/` as a collapsed `# planned by TODO-ALPHA-036-0.0.11` line even though `mutations/` shipped in `0.0.11` (`DONE-036`). My plan (step 10) scopes me to `forms/` + `tests/forms/` only, so I filled those and did NOT touch `mutations/` / `tests/mutations/`. This looks like a spec-036 Slice-5 doc-update miss. Flagging as a next-author / maintainer follow-up (or a candidate for the integration pass) — not a Slice-5a defect.
- **New GLOSSARY anchors are forward-refs to Slice 5b.** The four ref-ids I added resolve to `docs/GLOSSARY.md#djangoformmutation` / `#djangomodelformmutation`, anchors Slice 5b creates when it promotes both symbols. If 5b's rendered anchor slugs differ from these (the glossary renderer's slugging), 5b must reconcile the four defs I added (in `docs/README.md`, `TODAY.md`, and `CHANGELOG.md` ×2). I matched the existing `[glossary-djangomutation]: ...#djangomutation` slug convention.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- None. Slice 5a touches no package logic — it is version strings, prose flips, a test constant, and the CHANGELOG entry. The version quintet mirrors `spec-037` Decision 10's five-site cut (no new mechanism); the CHANGELOG entry reuses the established `## [0.0.X] - DATE` + `### Added` / `### Changed` shape and the existing CHANGELOG def block; the TREE `forms/` summaries reuse the section's house style. No duplicated logic introduced or entrenched.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows TWO classes of change: (1) the `__version__` `0.0.11` → `0.0.12` line — Slice 5a's only owned `__init__.py` edit (Decision 14); (2) the `.forms` import + the two `__all__` entries (`DjangoFormMutation`, `DjangoModelFormMutation`) — these are **Slice 2's** contract, not 5a's, present only because Slices 1–4 are uncommitted in the working tree. Confirmed 5a authored only the `__version__` line.

The two new `__all__` symbols are **AUTHORIZED** by spec Decision 5 (lines 976–982, "Two net-new public symbols, re-exported from `__init__.py` and added to `__all__`") and DoD item 8 (lines 2437–2439, "The two net-new public symbols … are added to `__all__` and the export pin updated accordingly").

The export-pin half — `tests/base/test_init.py::test_public_api_surface_is_pinned` — now **exactly mirrors** the live 23-symbol `__all__`. Walked both tuples symbol-by-symbol: `__init__.py` lines 40–65 vs `test_init.py` lines 51–76 are identical, both 23 entries, including `DjangoFormMutation` (alphabetical slot after `DjangoFileType`) and `DjangoModelFormMutation` (slot after `DjangoListField`). No missing/extra symbol; ordering correct. `test_public_api_surface_is_pinned` passes (see Temp test verification). The Worker-2-5a-completion addendum's pin fix (resolving the HIGH it had flagged for routing) is correct and is the right home: DoD item 8 explicitly authorizes the export-pin update under this card.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Read the new `[0.0.12]` block end-to-end (CHANGELOG lines 19–28). **Verdict: PASS.**

- **Version line:** `## [0.0.12] - 2026-06-23` matches `pyproject.toml` (`0.0.12`), `__init__.py` `__version__` (`0.0.12`), and the `uv.lock` package stanza (`0.0.12`). All four sites consistent.
- **Headings:** exactly `### Added` + `### Changed` — the two the spec authorizes (Doc updates lines 2122–2124; Slice ships no fix/removal). No unauthorized `### Fixed` / `### Removed`.
- **Wording vs shipped behavior:** accurate, no overstatement. `### Added` correctly states `DjangoModelFormMutation` rides `DjangoMutation` via the `_resolve_model` seam → `node` / `result` slot; the plain `DjangoFormMutation` is the model-less sibling (own metaclass + declaration registry, no object slot, pinned `ok: Boolean!` + `errors: [FieldError!]!`, `perform_mutate` hook). The `forms/converter.py` form-field → input mapping (read-side scalar/enum/`Upload` reuse; `ModelChoiceField` → target id, `FileField`/`ImageField` → `Upload`; unknown ancestor → `ConfigurationError`). The `form.errors` → frozen `FieldError` pipeline with `NON_FIELD_ERRORS` → `"__all__"`, every-branch relation-visibility, partial `update`, G2 re-fetch, sync+async, two net-new root exports. `### Changed` frames the `036` `DjangoMutationField` + base generalization as a **no-regression internal generalization** across the three Decision-5 axes (target-check, `_resolve` dispatch, `data:` lazy-ref) plus the new overridable base seams — explicitly "not a breaking change; no consumer-visible behavior of the `0.0.11` model-driven mutation changes." This matches Decision 5/6 and does not over- or under-state. The `__version__` is-now-`0.0.12` line mirrors the `[0.0.11]` precedent.
- **Verbatim fidelity:** the spec describes (not dictates verbatim) the CHANGELOG content; the plan committed to spec-cribbed phrasings within the no-overstate constraint (Worker-2 discretion item). The wording reads coherently against the actual Slice 1–4 behavior — spot-checked against Decisions 5/6 and the docs/README mutation bullet. No fenced-code drop-in in the entry, so the four-backtick fence rule is N/A.
- **Release shape:** the repo carries no standing `[Unreleased]` section (verified — dated blocks only: `[0.0.12]` above `[0.0.11] - 2026-06-19`). The dated-block cut matches the `[0.0.11]` template; the build-plan flag's "`[Unreleased]` → `0.0.12`" is the conceptual move. Correct.
- **Link defs:** `[glossary-djangoformmutation]` and `[glossary-djangomodelformmutation]` added to the CHANGELOG `<!-- docs/ -->` def group, alphabetically placed (lines 313, 315) between the pre-existing `[glossary-djangofiletype]` / `[glossary-djangoimagetype]` / `[glossary-djangomodelpermission]` defs. They resolve to `docs/GLOSSARY.md#…` (file exists); the in-page anchors are Slice-5b forward-refs, consistent with the existing `[glossary-djangomutation]: …#djangomutation` convention. All other glossary ref-ids used in the entry pre-existed.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Read the changed docs end-to-end. **Verdict: PASS.**

- **Four non-GLOSSARY version sites all read `0.0.12` and are mutually consistent:** `pyproject.toml` line 4, `__init__.py` `__version__` line 37, `tests/base/test_init.py::test_version` line 19, `uv.lock` package stanza (line 218). The `uv.lock` diff is confined to the one package version line (no dependency churn, no hash refresh). The fifth quintet site — the DB-backed `docs/GLOSSARY.md` package-version line — is correctly **deferred to 5b** and untouched here.
- **README Status line** moved `0.0.11` → `0.0.12` (line 66) and the "Newest shipped surface" prose now leads with form mutations (the two `Meta.form_class` flavors, form-derived input, `form.errors` → `FieldError`, `node`/`result` vs `ok`/`errors` payloads), with the old `Upload`/`DjangoFileType` text demoted to the "lands on top of" chain. The "Mutations ship today" sentence (line 57) now reads `0.0.11` foundation → `0.0.12` form flavors → `0.0.13` serializer — correct ordering, `ModelSerializer` left at `0.0.13`.
- **docs/README.md** "Shipped today" header bumped `0.0.11` → `0.0.12` (line 97); a form-mutations shipped bullet added (line 125, mirroring the `0.0.11` mutation bullet's shape); the `0.0.12` line **deleted** from "Coming next" and the block re-headed `(`0.0.13` → `0.0.14`)` — no stale `0.0.12`-coming-soon wording remains; the block now opens at `0.0.13`.
- **GOAL.md** criterion 6 (line 511) now reads the `ModelForm` flavor (`DjangoModelFormMutation` + the plain-`Form` `DjangoFormMutation` sibling) ships in `0.0.12`; **only `ModelSerializer` (`0.0.13`) still lands later** — correctly preserved. The DRF-migration prose (line 458) gains the `0.0.12` form flavor as shipped with `ModelSerializer` held at `0.0.13`.
- **TODAY.md** adds a `0.0.12` form-mutation capability bullet (line 20) and a "Form-backed mutations (`0.0.12`)" paragraph (line 357) that matches the actual Slice-4 surface — `createItemViaForm`/`updateItemViaForm` (`ItemModelForm`), `createItemWithFileViaForm` (multipart `Upload`), `createStampedItemViaForm` (`get_form_kwargs` user-inject), `submitContact` (plain `ContactForm` `{ok,errors}`); the "Mutations on products today" intro (line 89) notes the form-backed fields. Claims are matched to what Slice 4 shipped (verified against the live products surface in prior slice reviews).
- **docs/TREE.md** fills `forms/` in BOTH current on-disk layout (line ~211) and target package layout (line ~286, dropping the `# planned by TODO-ALPHA-038-0.0.12` annotation), and `tests/forms/` in BOTH current test trees (line ~369) and target test shape (line ~511, annotation dropped). **On-disk filenames verified** against the live trees: `forms/` = `converter.py` / `inputs.py` / `resolvers.py` / `sets.py` (✓ match); `tests/forms/` = `test_converter.py` / `test_inputs.py` / `test_resolvers.py` / `test_sets.py` (✓ match). Summaries follow the section house style.
- **Ref-style links:** every introduced/moved link is reference-style; the new `[glossary-djangoformmutation]` def is alphabetically placed in the correct `<!-- docs/ -->` group in docs/README.md (line 275) and TODAY.md (line 389). All defs target `docs/GLOSSARY.md` / `GLOSSARY.md` (file exists); in-page anchors are Slice-5b forward-refs (documented future surface), matching the established convention.
- **docs/GLOSSARY.md is correctly UNCHANGED** by 5a — confirmed absent from `git status --short` (its promotion + package-version-line move are Slice 5b). No carve-out file was touched by the review's focused test run (db.sqlite3 / KANBAN.* unchanged).

### What looks solid

- The version quintet's four 5a sites are mutually consistent at `0.0.12` (AGENTS.md rule 31 satisfied); the `uv.lock` edit is a clean in-place package-stanza bump with zero dependency churn.
- The public-API pin now exactly mirrors the live 23-symbol `__all__` — the Worker-2 5a-completion addendum correctly resolved the pin lag under the card the spec assigns it to (DoD item 8), rather than routing it out.
- The CHANGELOG entry is disciplined: spec-authorized headings only, no overstatement of the `036`-generalization (explicitly no-regression), version line consistent across all four sites.
- The doc flips are complete and stale-wording-free: the `0.0.12`-coming-soon line is deleted, the README Status + "newest surface" prose lead with the shipped flavor, `ModelSerializer` is consistently held at `0.0.13` across README/docs/README/GOAL.
- The TREE `forms/` and `tests/forms/` subtrees match the on-disk filenames exactly in all four render sites.

### Temp test verification

- No temp test authored (no package logic under review). Ran the permitted focused check `uv run pytest tests/base/test_init.py --no-cov` → **5 passed** (incl. `test_version` at `0.0.12` and `test_public_api_surface_is_pinned` at the 23-symbol surface). No `--cov*` flag used. The run dirtied no carve-out files (db.sqlite3 / KANBAN.* untouched).
- **Static-helper skip recorded:** `scripts/review_inspect.py` SKIPPED for the whole sub-slice — Slice 5a touches no package `.py` logic (only version strings, a test constant, prose docs, CHANGELOG). None of the BUILD.md run-triggers (≥150-line file gaining logic; `optimizer/`/`types/` edits; ≥30 new logic lines) are met.

### Notes for Worker 1 (spec reconciliation)

- **Verbatim-checklist audit — both monolithic Slice-5 boxes correctly left `- [ ]`.** Confirmed Worker 2 left both boxes unticked with the partial-landing note (5a portions landed: the four non-GLOSSARY quintet sites + the five plain docs + CHANGELOG; 5b portions deferred: the `docs/GLOSSARY.md` promotion/correction + DB-backed package-version line + `KANBAN.md` card move). The deferred-to-5b portions are NOT 5a omissions — they are intentionally Slice 5b. No 5a checklist gap.
- **CHANGELOG `[Unreleased]` vs dated-block:** the spec's `## Doc updates` says "`[Unreleased]` → `0.0.12` bullets"; the repo carries no `[Unreleased]` section, so Worker 2 cut a dated `## [0.0.12] - 2026-06-23` block matching the `[0.0.11]` template. Mechanically correct; a spec note that this repo cuts dated blocks per release (no standing `[Unreleased]`) would close the wording gap, but it is not a defect.
- **New GLOSSARY anchors are Slice-5b forward-refs.** The four ref-id defs Worker 2 added (docs/README.md, TODAY.md, CHANGELOG ×2) resolve to `docs/GLOSSARY.md#djangoformmutation` / `#djangomodelformmutation`, anchors 5b creates on promotion. If 5b's rendered slugs differ, 5b must reconcile these defs — already flagged by Worker 2; surfacing here so the dependency is on Worker 1's radar.
- **Carried from prior slices (not 5a defects):** Worker 2's note that `docs/TREE.md` still renders `mutations/` as a collapsed `# planned by TODO-ALPHA-036-0.0.11` line despite `mutations/` shipping in `0.0.11` (a likely spec-036 Slice-5 doc miss, out of 5a scope) stands as a maintainer/integration follow-up.

### Review outcome

`review-accepted`. Zero High/Medium/Low findings. The version quintet's four 5a sites are consistent at `0.0.12`; the public-API pin exactly mirrors the live 23-symbol `__all__` (export-pin half of DoD item 8 delivered, authorized by Decision 5); the CHANGELOG entry passes sanity (matching version line, spec-authorized headings, no overstatement); the documentation/release surfaces are consistent and stale-wording-free; `docs/GLOSSARY.md` is correctly untouched. The Notes-for-Worker-1 items are reconciliation flags, not blockers.

---

## Final verification (Worker 1)

**Status decision: `final-accepted`.**

### Summary

Slice 5a cut the `0.0.12` version stamp at its four non-GLOSSARY sites, flipped the plain
standing docs from "form mutations coming next (`0.0.12`)" to shipped, filled the `forms/` /
`tests/forms/` TREE subtrees, added the maintainer-authorized `## [0.0.12]` CHANGELOG block, and
landed the DoD-item-8 export-pin update. Verified against the diff, the artifact, and the spec:

- **Version consistency (DoD item 8 + AGENTS.md rule 31).** The four non-GLOSSARY version sites all
  read `0.0.12` and are mutually consistent: `pyproject.toml` line 4, `__version__` in
  `django_strawberry_framework/__init__.py` line 37, `tests/base/test_init.py::test_version` line 19
  (`assert __version__ == "0.0.12"`), and the `uv.lock` package stanza (line 218, directly under
  `name = "django-strawberry-framework"`). `pyproject.toml` and `__init__.py` match (rule 31). The
  fifth quintet site — the DB-backed `docs/GLOSSARY.md` package-version line — is correctly **deferred
  to 5b** and untouched (`docs/GLOSSARY.md` absent from `git status --short`).
- **5a touched ONLY `__version__` in `__init__.py`.** `git diff HEAD -- __init__.py` shows two
  change-classes: (1) the `__version__` `0.0.11`→`0.0.12` line (5a's only owned `__init__.py` edit),
  and (2) the `.forms` import + the two `__all__` entries (`DjangoFormMutation` /
  `DjangoModelFormMutation`) — **Slice 2's** contract, present only because Slices 1–4 are uncommitted
  in the working tree, authorized by spec Decision 5 / DoD item 8. Confirmed 5a authored only the
  `__version__` line.
- **Export pin mirrors the live 23-symbol `__all__`.** Walked both tuples symbol-by-symbol:
  `__init__.py` `__all__` (lines 39–65) and `tests/base/test_init.py::test_public_api_surface_is_pinned`
  (lines 51–77) are byte-identical, both 23 entries, including `DjangoFormMutation` (alphabetical slot
  after `DjangoFileType`) and `DjangoModelFormMutation` (slot after `DjangoListField`). No missing/extra
  symbol; ordering correct. The Worker-2 5a-completion addendum correctly resolved the pin under the
  card the spec assigns it to (DoD item 8) rather than routing it out.
- **DRY check across the build.** None. Slice 5a touches no package logic — version strings, prose
  flips, a test constant, and the CHANGELOG entry. The version quintet mirrors the `spec-037` Decision-10
  five-site cut (no new mechanism); the CHANGELOG reuses the established `## [0.0.X] - DATE` +
  `### Added` / `### Changed` shape; the TREE `forms/` summaries reuse the section house style. No new
  duplication introduced or entrenched.
- **Existing tests still pass.** `uv run pytest tests/base/ --no-cov` → **25 passed** (the focused 5a
  scope: the version + pin tests), including `test_version` at `0.0.12` and
  `test_public_api_surface_is_pinned` at the 23-symbol surface. No `--cov*` flag used; full suite NOT
  run (final-test-run gate's job).
- **Carve-outs untouched.** `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`
  all confirmed UNCHANGED by 5a (`KANBAN.*` / `db.sqlite3` are dirty from the concurrent kanban writer /
  Slice 4, per the build preamble — NOT 5a diff items; `docs/GLOSSARY.md` is not dirty at all).
- **GLOSSARY / GOAL UNCHANGED-in-5a confirmed:** the spec's `## Glossary` surface is untouched in 5a
  (its promotion is 5b); GOAL.md's edits are the authorized criterion-6 / DRF-prose flips, not the
  north-star contract.

### Spec slice checklist audit (verbatim boxes)

Both monolithic Slice-5 verbatim boxes (`Version files to 0.0.12`; `docs / card wrap`) mix 5a + 5b
targets. **Confirmed Worker 2 correctly left both `- [ ]`** with the partial-landing note: 5a landed the
four non-GLOSSARY version sites, the five plain docs, the `forms/`/`tests/forms/` TREE lines, and the
CHANGELOG; deferred to 5b are the `docs/GLOSSARY.md` promotion/correction + DB-backed package-version
`BoardDoc` + the `KANBAN.md` card move. These boxes are **completed across 5a+5b and will be ticked at
5b final-verification** — they are **deferred-with-reason, NOT silently un-ticked** (so they do NOT block
5a `final-accepted`; per BUILD.md, a deferred box with a recorded reason is allowed). See the
deferral-reason record below.

### Reconciliation of Worker 3's flags

- **(1) Verbatim-checklist:** confirmed correctly left `- [ ]` with the 5b-deferral note (see audit
  above). No action.
- **(2) `[Unreleased]` vs dated block:** the spec's `## Doc updates` (line 2123) said "`[Unreleased]` →
  `0.0.12` bullets"; the repo cuts dated `## [0.0.X] - DATE` blocks (no standing `[Unreleased]`). Made a
  minimal faithful spec note so the spec describes the repo's actual release mechanic (cited below).
- **(3) GLOSSARY ref-id forward-refs:** the four ref-id defs 5a added (`docs/README.md` ×1, `TODAY.md`
  ×1, `CHANGELOG.md` ×2) resolve to `docs/GLOSSARY.md#djangoformmutation` / `#djangomodelformmutation`,
  anchors 5b creates on promotion, matching the established `[glossary-djangomutation]: …#djangomutation`
  slug convention. **Carried to 5b: if 5b's rendered glossary slugs differ from these, 5b must reconcile
  the four defs.** Recorded in worker-1 memory for the 5b planning pass.
- **(4) `docs/TREE.md` stale `mutations/` line:** TREE still renders `mutations/` as
  `# planned by TODO-ALPHA-036-0.0.11` despite `mutations/` shipping in `0.0.11` (`DONE-036`). This is
  **spec-036 doc debt, OUT of spec-038's contract** — Worker 1 only edits the spec, not source TREE here.
  Recorded for the deferred-work catalog (integration/final) / maintainer follow-up; no 5a source edit.

### Spec changes made (Worker 1 only)

- **Deferral record (5a verbatim-checklist).** The two monolithic Slice-5 verbatim boxes in
  `### Spec slice checklist (verbatim)` are intentionally left `- [ ]` in 5a: each mixes 5a + 5b targets,
  5a landed its portion (four non-GLOSSARY version sites, the five plain docs, the TREE subtrees,
  CHANGELOG), and the 5b portions (`docs/GLOSSARY.md` promotion/correction + DB-backed package-version
  line + `KANBAN.md` card move) are carved to `bld-slice-5b-glossary_kanban_db.md`. They are
  **deferred-with-reason to 5b final-verification** (which ticks them fully once the whole contract
  lands), NOT silently un-ticked. No spec `## Slice checklist` box-text change.
- **Spec edit — `## Doc updates` CHANGELOG line (spec-038 lines 2122-2124, now 2122-2127).** Appended a
  parenthetical note that this repo's `CHANGELOG.md` cuts a dated `## [0.0.X] - DATE` block per release
  rather than maintaining a standing `[Unreleased]` section, so the entry is mechanically a fresh dated
  `0.0.12` block matching the `[0.0.11]` template and "`[Unreleased]` → `0.0.12`" names the conceptual
  move. Triggered by Slice 5a (Worker 3 reconciliation flag 2). Reason: keeps the spec faithful to the
  repo's actual release mechanic without changing the Slice-5 contract. `scripts/check_spec_glossary.py
  --spec docs/SPECS/spec-038-form_mutations-0_0_12.md` re-run after the edit → `OK: 31 terms` (exit 0).
- **Status line:** re-verified (spec lines 42-46). It reads "Slices 1–4 built and accepted … only Slice 5
  remains. Slice 5 flips this line to shipped at the `0.0.12` cut." Since 5a does NOT ship the full
  Slice-5 contract (5b carries the GLOSSARY promotion + KANBAN card move), the status line correctly
  stays "IN PROGRESS / only Slice 5 remains" — NO edit needed at 5a (the flip to shipped is 5b's).

---

#### Prior spec-changes record (Slice 5 split + carve)

- **Slice 5 SPLIT into 5a + 5b** (Slice-5 planning pass). Spec `## Slice checklist` Slice 5 (lines 464-486) describes one slice mixing plain text edits (version quintet, plain docs, CHANGELOG) with intricate DB-backed regenerate work (GLOSSARY promotion/correction + KANBAN card move + three regenerates). Per BUILD.md "Slice splitting" (lines 590-592), the two halves have **independent risk profiles and sharply different review tractability**: 5a is a small deterministic text diff Worker 3 reads line-by-line; 5b produces a huge generated-doc diff (`KANBAN.md`/`KANBAN.html`/`docs/GLOSSARY.md` fully re-rendered) entangled with the concurrent-writer's uncommitted kanban edits, plus a maintainer-coordination surface (the concurrency decision). Isolating 5b keeps the plain-doc review clean and contains the concurrency surface to one artifact. **Recorded as a Worker-1 spec edit; control returned to Worker 0 to regenerate the build-plan checklist** (the single Slice 5 box was replaced with `Slice 5a` + `Slice 5b` boxes, in that order). The spec's `## Slice checklist` text itself is left intact (the split is a build-execution decision; the spec's Slice-5 contract is delivered in full across 5a+5b) — if the maintainer prefers the spec's checklist also show the split, Worker 1 will annotate it during 5a/5b final verification. Reason: review quality + concurrency-surface containment.
- **Mechanical carve (this pass).** This artifact was re-scoped from the combined Slice-5 plan to **Slice 5a only**; the 5b plan content was moved verbatim into the new sibling `docs/builder/bld-slice-5b-glossary_kanban_db.md`. No plan content changed in substance — the carve only partitions the already-written plan along the 5a/5b boundary so each sub-slice has its own `Status:` line for dispatch. The combined artifact's full DB-backed procedure, step sequence, and verification adjustment now live in the 5b artifact.
