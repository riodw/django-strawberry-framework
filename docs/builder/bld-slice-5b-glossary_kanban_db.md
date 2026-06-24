# Build: Slice 5b — DB-backed GLOSSARY promote/correct + version-line BoardDoc + KANBAN card move + regenerate

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (Slice 5 checklist lines 464-486; `## Doc updates` lines 2086-2128 — GLOSSARY promotion/correction lines 2100-2115, KANBAN card move lines 2125-2128; Decision 14 lines 1835-1862 — the package-version line; Decision 6 lines 1051-1147 incl. the pinned plain-form `ok`+`errors` payload and the model-less-sibling correction; the Key-glossary-refs `DjangoFormMutation` correction note spec lines 145-159). Build-plan flags: `docs/builder/build-038-form_mutations-0_0_12.md` lines 16-25 (generated-docs-are-DB-backed; Slice-5 DB-writes-on-top-of-concurrent-work; DB-concurrency coordination; the byte-stability verification adjustment). The version quintet ex-GLOSSARY-line + plain docs + CHANGELOG are the sibling **`docs/builder/bld-slice-5-docs_version_cut.md`** (Slice 5a).
Status: final-accepted

> **CARVE NOTICE (Worker 1).** This artifact is the **5b** half of the split Slice 5 (the split spec edit is recorded in `bld-slice-5-docs_version_cut.md` `### Spec changes made (Worker 1 only)`). 5b = the DB-backed GLOSSARY promotion/correction + the GLOSSARY package-version `BoardDoc` + the KANBAN card move + the three regenerates (a large generated-doc diff entangled with concurrent-writer kanban state, plus a maintainer-coordination surface). The plain-text half (version quintet ex-GLOSSARY-line, plain docs, CHANGELOG) is Slice 5a in `bld-slice-5-docs_version_cut.md`. 5b runs AFTER 5a is `final-accepted`.

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - The DB-backed card-close + glossary-promote is the **standard worker-0.md "Closing out a kanban card" procedure** (embedded verbatim in the build-plan flags and reproduced in `### Implementation steps` below). It reuses the shipped render scripts (`scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`, `scripts/build_glossary_md.py`) and the shipped `manage.py import_spec_terms` (with `--check`) — no new tooling.
  - The GLOSSARY Index row + the Mutations browse-by-category row are **generated** from `GlossaryTerm.statusText` and `GlossaryCategoryMembership` rows respectively (`scripts/build_glossary_md.py::render_index` / `render_browse`); flipping `status_text` flips the Index row for free. **Verified:** both form symbols ALREADY carry `GlossaryCategoryMembership` rows in the `mutations` category (`djangoformmutation` order 2, `djangomodelformmutation` order 3) — so "add to the Mutations browse-by-category row" is **already satisfied in the DB**; 5b VERIFIES this, it does not re-add (avoid the `(category, order)` unique collision a blind add would risk).
  - The package-version line is the SAME `0.0.11` value 5a bumps elsewhere; here it lives in the `docs/GLOSSARY.md`-rendered `BoardDoc` (namespace=`glossary`, key=`status-legend`), NOT a `build_glossary_md.py` literal. The version edit reuses the version-quintet bump shape (string `0.0.11` → `0.0.12`), only the carrier is a DB row + regenerate rather than a source-file edit.
- **New helpers justified.** None. Slice 5b touches no package logic — it is DB row edits via the ORM + three regenerates. No helper, module, or constant is created.
- **Duplication risk avoided.**
  - **Hand-editing a generated doc.** `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` are DB-rendered; a hand-edit is silently reverted by the next regenerate. 5b edits the DB via the ORM then regenerates — NEVER touches the rendered markdown directly. The GLOSSARY package-version line is a `BoardDoc` body, NOT a script literal (verified: `scripts/build_glossary_md.py` has no version string; the line is rendered from the `namespace='glossary', key='status-legend'` `BoardDoc`, pk≈40).
  - **Raw SQL skips the side-row.** All DB writes go through the Django ORM (`.save()` / `.objects.create(...)`), NEVER raw SQL — kanban/glossary rows need the `post_save` `UUIDModel` side-row the render's `uuid { id }` query reads; a raw insert skips it and the render breaks.
  - **Re-seeding already-present terms.** All 31 terms-CSV anchors already exist as `GlossaryTerm` rows (verified) and both form symbols already have Mutations-category memberships — so the worker-0 procedure's "seed net-new terms" + "add category memberships" steps are **no-ops here**; 5b only PROMOTES + CORRECTS the two existing rows, appends two Public-exports bullets, moves the version-line `BoardDoc`, and moves the card. The plan calls these out as verify-not-create to stop Worker 2 duplicating rows.

### Implementation steps

Line numbers are pin-at-write-time hints; verify against current source before editing (a concurrent writer is touching `db.sqlite3` / `KANBAN.*` — see the concurrency flag).

#### Static-helper skip (record)

`scripts/review_inspect.py` is **SKIPPED for the entire sub-slice**: Slice 5b touches no package `.py` logic — only DB rows + regenerated markdown. No file under `django_strawberry_framework/` gains logic; the BUILD.md run-triggers are not met. NEVER pass `--cov*` anywhere in this slice.

#### 5b — DB-backed GLOSSARY promotion + correction (Doc updates, spec lines 2100-2115; Decision 6)

**All DB writes via `uv run python examples/fakeshop/manage.py shell` using the Django ORM (NEVER raw SQL — kanban/glossary rows need the `post_save` `UUIDModel` side-row the render's `uuid { id }` query reads). Regenerate from repo root. Do NOT revert/undo the concurrent writer's `db.sqlite3` kanban edits (build-plan flag line 20).**

**Pre-verified DB state (confirmed during planning — Worker 2 re-confirm before writing, the concurrent writer may have shifted things):**
- All 31 terms-CSV anchors already exist as `GlossaryTerm` rows → the worker-0 "seed net-new terms" step is a **NO-OP**. Do not create term rows.
- `djangoformmutation` + `djangomodelformmutation`: `status.key="planned"`, `status_text="planned for `0.0.12`"`. Both already have `GlossaryCategoryMembership` in the `mutations` category (orders 2, 3) → the "add to Mutations browse-row" step is a **NO-OP / verify-only**. Do not add memberships (would risk the `(category, order)` unique collision).
- `GlossaryStatus` keys available: `shipped`, `planned`.

12. **Promote + correct the two form `GlossaryTerm` rows** (the only term edits):
    - `t = GlossaryTerm.objects.get(anchor="djangoformmutation")`: set `t.status = GlossaryStatus.objects.get(key="shipped")`; set `t.status_text = "shipped (`0.0.12`)"` (match the exact rendered form other shipped entries use — verify against a shipped row, e.g. `DjangoMutation`'s `status_text`); **rewrite `t.body` per Decision 6 (the P2 correction):** the CURRENT body (`docs/GLOSSARY.md` line 342) wrongly calls it a "`DjangoMutation` subclass" returning "the post-save object as the return value". Replace with the model-less-sibling shape: a plain Django `Form` mutation declared via `Meta.form_class`, **its own metaclass (NOT a `DjangoMutation` subclass)**, accepted by the generalized mutation-field family, returning the **pinned `ok: Boolean!` + `errors: [FieldError!]!` payload with NO `DjangoType` object slot**; validation surfaces through the shared `FieldError` envelope (populated from `form.errors`, `NON_FIELD_ERRORS` → `"__all__"`); the `perform_mutate(self, form, info) -> None` side-effect hook (default `form.save()`-if-present else no-op). Keep the See-also links.
    - `t = GlossaryTerm.objects.get(anchor="djangomodelformmutation")`: same status/status_text flip; update `t.body` to the shipped contract — a `ModelForm` mutation via `Meta.form_class` that **subclasses `DjangoMutation`** (overriding `_resolve_model` → `form_class._meta.model`), returns the post-save object in the uniform `node`/`result` slot, reuses the `DjangoModelPermission` default + visibility-scoped `update` locate + optimizer re-fetch (G2), form-derived input, `form.errors` → `FieldError`. This entry's "subclass / post-save object" claim is CORRECT for the ModelForm — keep it, just promote and enrich to the shipped contract.
    - `t.save()` each (fires the `post_save` side-row signal). `title_sort` / `entry_order` / `index_order` are unchanged (the entries already exist in the ordering — do not reslot).
13. **Move the package-version line to `0.0.12`** (DB-backed): `d = BoardDoc.objects.get(namespace="glossary", key="status-legend")` (pk≈40 — match on namespace+key, not pk, the concurrent writer may renumber); edit `d.body` replacing `Current package version: `0.0.11`` → `0.0.12`; `d.save()`. (This is the fifth site of the version quintet — 5a deliberately deferred it here because it is DB-backed.)
14. **Add the two form symbols to Public exports** (DB-backed, NET-NEW — verified absent): `d = BoardDoc.objects.get(namespace="glossary", key="public-exports")`; append two bullets to `d.body` in the export list, alongside the existing `DjangoMutation` / `DjangoMutationField` / `FieldError` / `Upload` bullets (match their exact bullet shape `- [`Name`](#anchor) — short description.`): `DjangoFormMutation` (the plain model-less `Form` mutation base) and `DjangoModelFormMutation` (the `ModelForm` mutation base subclassing `DjangoMutation`). `d.save()`.
    - The **Index** status column and the **Mutations** browse-row are auto-generated (Index from `status_text`; Mutations from the existing memberships) → no separate DB edit; they flip on regenerate.

#### 5b — DB-backed KANBAN card move (`WIP-ALPHA-038-0.0.12` → `DONE-038-0.0.12`; Doc updates spec lines 2125-2128)

**Verified DB state:** Card #38 is currently `status.key="wip"` (the concurrent writer moved TODO→WIP; the spec/dispatch text says `TODO-ALPHA-038` but the live DB is `WIP-ALPHA-038` — the rendered `KANBAN.md` line 144 confirms `WIP-ALPHA-038-0.0.12`). The card already has a `SpecDoc` (name `spec-038-form_mutations-0_0_12`, url `https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-038-form_mutations-0_0_12.md` — the canonical form, matches DONE-036's SpecDoc) and **0 `CardGlossaryTerm`** rows and 18 `CardItem` DoD rows. The rendered DONE id will be `DONE-038-0.0.12` (`_card_identifier` drops the milestone prefix for a done card; number `038`, target_version `0.0.12`).

15. **SpecDoc — verify, do not recreate.** `card = Card.objects.get(number=38)`. A `SpecDoc` already exists with the canonical url; confirm `name`/`url` are correct (the `import_spec_terms` parse + the DONE-card invariant `_validate_done_card_has_spec` need it). No edit needed unless the concurrent writer changed it — if so, UPDATE url/name to the canonical form (do not create a second; `name` is unique).
16. **Bootstrap ≥1 `CardGlossaryTerm`** (REQUIRED — currently 0; the `_validate_done_card_has_glossary_link` invariant blocks the done-save otherwise). Create one linking card #38 to the first terms-CSV anchor (`djangoformmutation`): `CardGlossaryTerm.objects.create(card=card, term=GlossaryTerm.objects.get(anchor="djangoformmutation"))` (verify the exact `CardGlossaryTerm` field names — `term` vs `glossary_term` — against the model before writing; use the ORM so the side-row fires). The full link set is synced by `import_spec_terms` in step 19.
17. **Fix card-body content the spec wrap names** (via `CardItem.text`, ORM):
    - DoD `CardItem` "Add `docs/spec-form_mutations.md`." (rendered `KANBAN.md` line 169) carries a **stale filename** — rewrite the text to the canonical `docs/SPECS/spec-038-form_mutations-0_0_12.md` (mirror how other DONE cards reference their spec).
    - Sweep the card's `CardItem` rows for any `docs/spec-0NN-…` stale ref or `## [0.0.X]` → `[Unreleased]` mismatch the worker-0 procedure names; correct via `CardItem.text`. (Verify each against the live rows; do not invent edits the DB does not carry.)
    - **Mark every SHIPPED `definition_of_done` `CardItem` `is_complete = True`** (verify the field name — `is_complete` per the build-plan/worker-0 procedure). The six DoD bullets (rendered lines 169-174: spec exists; `forms/` on the DRF Meta surface; `forms/converter.py` reuses the scalar registry; `form.errors` → `FieldError` envelope; `tests/forms/`; live HTTP for both `Form` and `ModelForm`) ALL shipped across Slices 1-4 → set each complete. (Note: DoD item 2's parenthetical names `Meta.return_field_name`; the spec's Decision 6 deliberately did NOT adopt it — the bullet is a card-body description, not a falsified contract; tick the item as the surface shipped on the `class Meta` shape. Do not rewrite the card body to remove the `return_field_name` mention unless it reads as a literal unshipped promise — Worker 2 discretion, flag to Worker 1 if ambiguous.)
18. **Flip status:** `card.status = Status.objects.get(key="done"); card.save()` (ORM `.save()` fires the pre_save validation + the DONE-card invariants + sets `milestone_id`; the rendered id auto-becomes `DONE-038-0.0.12`). Do this AFTER steps 15-16 so both invariants (SpecDoc + ≥1 CardGlossaryTerm) are satisfied — a premature flip raises `ValidationError`.
19. **Sync the full glossary-link set:** `uv run python examples/fakeshop/manage.py import_spec_terms` (creates the `CardGlossaryTerm` rows for every anchor in the card's terms-CSV; requires every anchor to already exist as a `GlossaryTerm` — verified true).

#### 5b — regenerate all three docs (from repo root, in order)

20. `uv run python scripts/build_kanban_md.py`
21. `uv run python scripts/build_kanban_html.py`
22. `uv run python scripts/build_glossary_md.py`

#### 5b — verification (ADJUSTED per the maintainer concurrency decision — build-plan flag line 20)

The standard worker-0 "`git diff docs/GLOSSARY.md` clean after regenerate" check is **NOT applicable** (the DB legitimately diverged from HEAD via concurrent kanban work; the regenerated docs reflect BOTH the concurrent edits AND this card's move — the maintainer reconciles at commit). Instead verify:

- (a) **Two-consecutive-regenerate byte-stability.** Run steps 20-22 twice; the second run produces byte-identical `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` to the first (proves MY DB writes regenerate deterministically, independent of the concurrent-writer noise). Capture via `md5`/`sha256` of each file across the two runs, or `git diff --stat` showing no delta between run-1 and run-2 outputs.
- (b) **Rendered `KANBAN.md` shows the card as `DONE-038-0.0.12`** with its DoD bullets ticked (`- [x]`).
- (c) **Both glossary symbols render as `shipped (`0.0.12`)`** in `docs/GLOSSARY.md` (the entry `**Status:**` line, the Index status column, and the package-version line all show `0.0.12`); the `DjangoFormMutation` body shows the model-less-sibling shape (no "DjangoMutation subclass" / "post-save object" claim); both symbols appear under Public exports.
- (d) **`uv run python examples/fakeshop/manage.py import_spec_terms --check`** reports OK, and **`uv run python examples/fakeshop/manage.py check`** passes.

Workers never commit — the regenerated docs + `db.sqlite3` are handed to the maintainer (who reconciles the concurrent-writer state at commit). If (a) surfaces drift between the two regenerate runs that traces to the concurrent writer rewriting `db.sqlite3` mid-pass, that is a **maintainer-coordination point, not a Slice-5b build defect** — record it in the build report and flag to Worker 1 / Worker 0, do not attempt to "fix" the DB.

### Test additions / updates

- None. Slice 5b ships no package logic and edits no test file (the version-quintet test edit `tests/base/test_init.py::test_version` is Slice 5a's; 5b's fifth version site is the DB-backed `BoardDoc`, which is verified via the rendered `docs/GLOSSARY.md`, not a unit test). The form-mutation behavior is already pinned by Slices 1-4's `tests/forms/` + `test_products_api.py`. Worker 3 reads the diff against the spec and walks the rendered docs rather than running coverage. No temp/scratch tests are appropriate (no logic under test); the verification is the byte-stable-regenerate + `import_spec_terms --check` + `manage.py check` sequence above.

### Implementation discretion items

Assessed and decided to be Worker 2's choice (style / equivalent-shape only; none architectural):

- The order of the independent 5b DB writes among steps 12-14 (the term-promote/correct, version-line `BoardDoc`, and Public-exports edits are independent). **NOT discretionary:** the card-move sequencing (steps 15-16 BEFORE step 18; step 19 after the flip) — the DONE-card invariants enforce it.
- The precise `CardGlossaryTerm` field name (`term` vs `glossary_term`) and the `CardItem` completion-flag field name (`is_complete`) — verify against the live models; the choice is mechanical, not a design decision.
- Whether step 17's card-body `return_field_name` parenthetical reads as a literal unshipped promise (rewrite) or a card-body description (leave) — Worker 2 discretion, flag to Worker 1 if ambiguous.
- The exact prose of the corrected `DjangoFormMutation` / enriched `DjangoModelFormMutation` `GlossaryTerm.body` text, within the Decision-6 contract + the no-overstate constraint (Worker 3's documentation-sanity check is the backstop; the model-less-sibling shape vs the `DjangoMutation`-subclass shape is NOT discretionary — it is the Decision-6 correction).

### Spec slice checklist (verbatim)

The spec's `## Slice checklist` Slice 5 nested sub-bullets, copied verbatim (preserve text, nesting, inline citations). These are the same two **monolithic** Slice-5 sub-bullets the 5a artifact carries; 5b ticks them **fully** at its final verification, because by 5b's completion the whole Slice-5 contract (5a's plain-text portion + 5b's DB-backed portion) has landed. Not ticked at planning — Worker 2 ticks each `- [x]` only when that contract lands in its diff; Worker 1 audits at final verification.

**5b delivers:** the `docs/GLOSSARY.md` promotion of `DjangoFormMutation` / `DjangoModelFormMutation` to `shipped (0.0.12)` (+ the Decision-6 `DjangoFormMutation` body correction); their **Public exports** bullets + the auto-flipped **Index** status column + the verify-only **Mutations** browse-by-category row; the `docs/GLOSSARY.md` **package-version line** move to `0.0.12` (the DB-backed `BoardDoc` — the fifth version-quintet site); and the **`KANBAN.md` card → Done** move (`WIP-ALPHA-038-0.0.12` → `DONE-038-0.0.12`) via the kanban DB + the three regenerates. These are the 5b targets. 5b ticks the two monolithic boxes fully at its final verification (5a's version-quintet/plain-docs/CHANGELOG portions already landed by then).

- [x] **Version files to `0.0.12`**
  ([Decision 14](#decision-14--this-card-owns-the-0012-version-bump)):
  [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init],
  [`tests/base/test_init.py::test_version`][test-base-init], the
  [`docs/GLOSSARY.md`][glossary] package-version line, and `uv.lock` if it
  carries the package version.
- [x] [`docs/GLOSSARY.md`][glossary] (promote
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

---

## Build report (Worker 2)

5b ran DB-backed (ORM only, no raw SQL) against the CURRENT `examples/fakeshop/db.sqlite3`
(which already carried the concurrent writer's uncommitted kanban edits), then regenerated
the three docs. Per binding maintainer decisions (1) + (2): writes applied ON TOP OF the
concurrent work, nothing reverted/checked-out; verification uses the byte-stability +
rendered-output checks, not the `git diff GLOSSARY.md clean` check. The two monolithic
Slice-5 verbatim boxes are now FULLY delivered across 5a+5b → both ticked `- [x]`.

### Files touched

Slice-intended (mixed with concurrent-writer state — maintainer reconciles at commit):

- `examples/fakeshop/db.sqlite3` — ORM writes: promoted + corrected the two form
  `GlossaryTerm` rows (steps 12); version-line `BoardDoc` `status-legend` → `0.0.12`
  (step 13); two new `public-exports` `BoardDoc` bullets (step 14); bootstrapped one
  `CardGlossaryTerm` for card #38 (step 16); corrected DoD item o=0 stale filename +
  marked all 6 DoD items `is_complete=True` (step 17); flipped card #38 `status` → `done`
  (step 18); `import_spec_terms` synced card #38 to its 31 terms-CSV anchors (step 19).
- `docs/GLOSSARY.md` — regenerated. My hunks: version line `0.0.11`→`0.0.12`; both form
  symbols' Index status `planned for 0.0.12`→`shipped (0.0.12)`; both `**Status:**` lines
  `shipped (0.0.12)`; corrected `DjangoFormMutation` body (model-less sibling) + enriched
  `DjangoModelFormMutation` body; two new Public-exports bullets. **One concurrent-writer
  hunk also appears** (see Notes for Worker 1) — NOT mine, left intact per decision (1).
- `KANBAN.md` — regenerated. My change: card #38 moved WIP→Done section, id
  `WIP-ALPHA-038-0.0.12`→`DONE-038-0.0.12`, all 6 DoD bullets ticked `- [x]`, stale spec
  filename corrected. The large line count of the diff is the concurrent writer's edits +
  the section move combined.
- `KANBAN.html` — regenerated alongside `KANBAN.md` (same DB).

NOT touched (confirmed via `git status --short`): `docs/feedback.md` (baseline-dirty,
out of scope), `examples/fakeshop/apps/products/migrations/0002_item_attachment.py`
(untracked Slice-4 artifact — `migrate` was NOT run, products.0002 stays un-applied).

### Tests added or updated

- None. Slice 5b ships no package logic and edits no test file (per plan "Test additions /
  updates" — the version-quintet `test_version` edit is Slice 5a's; 5b's fifth version
  site is the DB-backed `BoardDoc`, verified via the rendered `docs/GLOSSARY.md`).

### Validation run

- `uv run ruff format .` / `uv run ruff check --fix .` — **not run** (intentionally
  skipped): 5b edited no `.py` file (DB rows + regenerated markdown only). Confirmed via
  `git status --short`: no package/test `.py` in the slice-intended set.
- `git status --short` after the build — slice-intended dirty: `examples/fakeshop/db.sqlite3`,
  `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`. These NOW carry my 5b writes MIXED with
  the concurrent writer's edits — expected per decision (1); NOT separated or reverted.
  `docs/feedback.md` (baseline-dirty) and the products.0002 migration were left as found.
- `pytest` — not run (the render scripts are in-process `/graphql/` queries = the
  regenerate, not a test). No `--cov*` anywhere.

#### Adjusted verification (a)-(d) — ALL PASS

- **(a) Two-consecutive-regenerate byte-stability — PASS.** Ran steps 20-22 twice;
  SHA-256 of all three files identical across run 1 and run 2 (proves MY DB writes
  regenerate deterministically):
  - `KANBAN.md` `4809a66c…68c4a7` (run1 == run2)
  - `KANBAN.html` `06e82c32…68a32a` (run1 == run2)
  - `docs/GLOSSARY.md` `453b8a95…b0b4ed3b` (run1 == run2)
  `diff` of the two checksum sets is empty.
- **(b) Rendered card → `DONE-038-0.0.12` with DoD ticked — PASS.** `KANBAN.md`: card
  renders `DONE-038-0.0.12` (board table line 100, Done card heading line 1360);
  `WIP-ALPHA-038` count = 0, `### [DONE-038-0.0.12` heading count = 1 (moved exactly once);
  all 6 DoD bullets `- [x]`; DoD item 0 reads `Add docs/SPECS/spec-038-form_mutations-0_0_12.md.`
- **(c) Both glossary symbols `shipped (0.0.12)` + corrected body + public exports — PASS.**
  Version line = `0.0.12`; Index status column shows `shipped (0.0.12)` for both
  (lines 78, 82); both entry `**Status:**` lines = `shipped (0.0.12)`; the
  `DjangoFormMutation` body shows the model-less-sibling shape (explicitly "**not** a
  `DjangoMutation` subclass", own metaclass, no `DjangoType` object slot, pinned `ok` +
  `errors`, `perform_mutate`) — the stale "DjangoMutation subclass" / "post-save object"
  claim is gone; `DjangoModelFormMutation` enriched to the shipped subclass contract; both
  symbols appear under Public exports (lines 30, 33) and the Mutations browse-by-category
  row (line 167 — verify-only, was already present via the existing memberships, no re-add).
- **(d) `import_spec_terms --check` OK + `manage.py check` passes — PASS.**
  `import_spec_terms --check` → `OK: 38 done cards have glossary links.`;
  `manage.py check` → `System check identified no issues (0 silenced).`

### Exact ORM commands run

All via `uv run python examples/fakeshop/manage.py shell -c '…'`, ORM only, each write
block wrapped in `transaction.atomic()`. Condensed:

```python
# Step 12 — promote + correct the two form terms
shipped = GlossaryStatus.objects.get(key="shipped")
tf = GlossaryTerm.objects.get(anchor="djangoformmutation")
tf.status = shipped; tf.status_text = "shipped (`0.0.12`)"; tf.body = FORM_BODY; tf.save()
tm = GlossaryTerm.objects.get(anchor="djangomodelformmutation")
tm.status = shipped; tm.status_text = "shipped (`0.0.12`)"; tm.body = MODELFORM_BODY; tm.save()
# Step 13 — version line
legend = BoardDoc.objects.get(namespace="glossary", key="status-legend")
legend.body = legend.body.replace("Current package version: `0.0.11`",
                                   "Current package version: `0.0.12`"); legend.save()
# Step 14 — two Public-exports bullets (alphabetical in the Django* block)
pe = BoardDoc.objects.get(namespace="glossary", key="public-exports")
pe.body = pe.body.replace(FILE_BULLET, FILE_BULLET + FORM_BULLET + "\n", 1)
pe.body = pe.body.replace(LIST_BULLET, LIST_BULLET + MODELFORM_BULLET + "\n", 1); pe.save()
# Step 15 — SpecDoc verify-only (canonical url/name already correct; no write)
# Step 16 — bootstrap >=1 CardGlossaryTerm BEFORE the done-flip
CardGlossaryTerm.objects.create(card=card,
    term=GlossaryTerm.objects.get(anchor="djangoformmutation"), order=0,
    raw_text="DjangoFormMutation")
# Step 17 — fix stale filename + mark DoD complete
dod0 = card.items.get(section__key="definition_of_done", order=0)
dod0.text = "Add `docs/SPECS/spec-038-form_mutations-0_0_12.md`."; dod0.save()
card.items.filter(section__key="definition_of_done").update(is_complete=True)  # 6 rows
# Step 18 — flip to done (pre_save sets milestone_id + runs both DONE-card invariants)
card.status = Status.objects.get(key="done"); card.save()
```

Then from repo root:
```
uv run python examples/fakeshop/manage.py import_spec_terms          # step 19 (synced 38 done cards; card #38 → 31 links)
uv run python scripts/build_kanban_md.py && … build_kanban_html.py && … build_glossary_md.py   # steps 20-22 (×2 for byte-stability)
```

### Implementation notes

- **Public-exports bullet placement** — inserted `DjangoFormMutation` after the
  `DjangoFileType` bullet and `DjangoModelFormMutation` after the `DjangoListField`
  bullet (anchored the `.replace(..., count=1)` on the full neighboring bullet line so the
  insert is unambiguous). The body's `Django*` run is alphabetical from `BigInt` through
  `DjangoType`, so this keeps both new symbols in alphabetical position within that run.
  Discretionary per plan (order of the independent step-12/13/14 writes / bullet shape).
- **Bootstrap `CardGlossaryTerm` used `order=0`** — the `(card, order)` unique constraint
  is empty for card #38 (0 prior links) so `order=0` is safe; `import_spec_terms`
  immediately re-offsets and reconciles all 31 links in step 19, so the bootstrap row's
  order is transient. The bootstrap exists solely to satisfy
  `_validate_done_card_has_glossary_link` at the step-18 done-flip (which fires before
  step 19 can run, since a done card cannot be saved without ≥1 link).
- **DoD `return_field_name` parenthetical — left as-is (plan discretion item).** DoD item
  o=1 reads "…on the DRF-style Meta surface (`Meta.form_class`, `Meta.return_field_name`,
  etc.)…". Per Decision 6 the package deliberately did NOT adopt `Meta.return_field_name`
  (the `036` uniform `node`/`result` slot is frozen). I read the bullet as a card-body
  *description* of the planned DRF-style surface (note the "etc."), not a literal shipped-
  contract promise, so I ticked it complete without rewriting the text — matching the
  plan's step-17 guidance. Flagged to Worker 1 below in case it prefers a rewrite.
- **Skipped `scripts/review_inspect.py` entirely** — per plan's "Static-helper skip
  (record)": 5b touches no package `.py` logic, so the BUILD.md run-triggers are not met.

### Notes for Worker 3

- The diff is **intentionally mixed** (my 5b writes + the concurrent writer's `db.sqlite3`
  kanban edits) per binding maintainer decision (1); do NOT treat the concurrent hunks as
  5b scope or flag them as drift to revert. The `KANBAN.md` line count (~229 changed) is
  dominated by the concurrent writer + the WIP→Done section relocation.
- **`docs/GLOSSARY.md` carries ONE non-5b hunk**: the `django-appconfig` term body
  (`apps.py` / `ready()` paragraph) regenerated to a shorter `_django_patches`-only form.
  GLOSSARY.md was clean at HEAD before my writes, so this hunk traces to a concurrent-writer
  edit to that `GlossaryTerm.body` row in `db.sqlite3` (confirmed: I never touched the
  `django-appconfig` row — only `djangoformmutation`/`djangomodelformmutation`, the
  `status-legend`/`public-exports` BoardDocs, and card #38). Left intact per decision (1)
  + AGENTS.md rule 34. Every OTHER GLOSSARY.md hunk is a deliberate 5b write.
- No shadow file used. No temp tests (no logic under test).
- Verbatim-checklist ticks: both monolithic Slice-5 boxes flipped `- [x]` (5a+5b complete);
  Worker 1 audits against the combined 5a+5b diff.

### Notes for Worker 1 (spec reconciliation)

- **Concurrent-writer drift in the regenerated docs is a maintainer-coordination point,
  not a 5b defect** (build-plan flag line 20). The `db.sqlite3` carries another process's
  kanban edits AND a `django-appconfig` glossary-body edit; my regenerate faithfully
  reflects BOTH them and my 5b writes. Byte-stability check (a) passed, proving the
  regenerate is deterministic — so the only non-determinism risk would be the concurrent
  writer rewriting `db.sqlite3` mid-pass, which did not occur (run1 == run2). The maintainer
  reconciles the mixed `db.sqlite3` / `KANBAN.*` / `docs/GLOSSARY.md` diff at commit.
- **DoD `Meta.return_field_name` mention (discretionary, flagged per plan step 17):** I
  left the card-body text mentioning `Meta.return_field_name` and ticked the DoD item,
  reading it as a surface-description not an unshipped-promise. Decision 6 (spec lines
  1149-1157) records `return_field_name` as deliberately NOT adopted. If Worker 1 judges
  the card bullet reads as a literal contract, the fix is a `CardItem.text` ORM edit +
  re-render (DB-backed, not a hand-edit) — flagging rather than deciding unilaterally.

---

## Review (Worker 3)

Reviewed the 5b artifact + the working-tree diff against `docs/SPECS/spec-038-form_mutations-0_0_12.md`
(Decision 6, Decision 14, the `## Doc updates` GLOSSARY/KANBAN bullets), the terms-CSV (31 anchors),
and `db.sqlite3` via read-only ORM queries. The mixed-diff carve (Worker 2's 5b writes ON TOP OF the
concurrent writer's uncommitted kanban + `django-appconfig` edits) is honored — I reviewed 5b's writes,
did not audit or revert the concurrent edits, and did not mutate the DB or any generated doc.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

None (DB-row + regenerated-doc work; no package `.py` logic touched). Confirmed Worker 2 reused the
shipped render scripts + `import_spec_terms` (no new tooling), did NOT duplicate the SpecDoc (DB query:
exactly 1 SpecDoc for card 38, canonical name+url), and did NOT blind-add a Mutations membership
(`djangoformmutation` order 2 / `djangomodelformmutation` order 3 are the pre-existing rows — verify-only,
no `(category, order)` collision risk taken).

### Public-surface check

Not applicable — 5b made no `__init__.py` / package change. Confirmed: `git status --short` shows
`django_strawberry_framework/__init__.py` dirty from Slices 2/5a (the two `__all__` adds + `__version__`),
NOT from 5b; 5b's dirty set is `db.sqlite3` / `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` only.

### CHANGELOG sanity

Not applicable — 5b did not touch `CHANGELOG.md` (that was Slice 5a). Noted for cross-consistency only:
the version quintet (`pyproject.toml`, `__init__.py`, `CHANGELOG.md [0.0.12]`, and the GLOSSARY
package-version line) all read `0.0.12`.

### Documentation / release sanity

VERDICT: PASS on all four 5b surfaces.

- **KANBAN card move — PASS.** Card renders `DONE-038-0.0.12` in the board spec-map (line 100) and the
  Done-section card heading (line 1360), exactly once each; `WIP-ALPHA-038` count = 0 (fully removed from
  WIP). The other 4 `DONE-038-0.0.12` hits are cross-references in OTHER cards' bodies (the FieldError-
  envelope card + the related-links block), correctly auto-updated on regenerate. All 6 definition-of-done
  bullets ticked `- [x]` (lines 1421-1426). DoD item 0 stale filename corrected to
  `Add docs/SPECS/spec-038-form_mutations-0_0_12.md.`. SpecDoc points at the canonical spec URL
  (`https://github.com/riodw/.../docs/SPECS/spec-038-form_mutations-0_0_12.md`); DB query confirms exactly
  1 SpecDoc and 31 `CardGlossaryTerm` rows (matches the CSV's 31 anchors). `status.key=done` (DB).
- **GLOSSARY promotion + Decision-6 correction — PASS (load-bearing).** Both symbols render
  `shipped (0.0.12)` in the Index status column (lines 78, 82), the entry `**Status:**` lines (342, 372),
  Public exports (30, 33), and the Mutations browse-by-category row (167). The `DjangoFormMutation` body
  (line 344) now reflects Decision 6: explicitly "**not** a `DjangoMutation` subclass", own lightweight
  metaclass, NO `DjangoType` object slot, pinned `ok: Boolean!` + `errors: [FieldError!]!` payload,
  `perform_mutate(self, form, info) -> None` hook (default `form.save()`-if-present else no-op),
  `NON_FIELD_ERRORS` → `"__all__"`, its own `forms/sets.py` registry + `bind_form_mutations()`. The stale
  "`DjangoMutation` subclass" / "post-save object as the return value" text is GONE (confirmed via
  `git show HEAD:docs/GLOSSARY.md` — HEAD carried both stale claims). `DjangoModelFormMutation` body
  (line 374) correctly RETAINS the subclass/post-save shape (it IS a `DjangoMutation` subclass via
  `_resolve_model` → `form_class._meta.model`), enriched to the shipped contract. Measured against
  Decision 6 spec lines 1051-1147: faithful.
- **Package-version line — PASS.** `docs/GLOSSARY.md` line 20 reads `Current package version: 0.0.12`
  (HEAD was `0.0.11`), consistent with `pyproject.toml` / `__init__.py` / `CHANGELOG.md` (all `0.0.12`).
- **GLOSSARY diff scope — clean.** 6 hunks total: 5 deliberate 5b writes (version line @17, public-exports
  @27, index @73, `DjangoFormMutation` body @337, `DjangoModelFormMutation` body @367) + ONE concurrent-
  writer hunk (@305, the `django-appconfig` `ready()` body regenerated to a shorter `_django_patches`-only
  form). The `django-appconfig` row is plausibly NOT-5b: GLOSSARY was clean at HEAD, Worker 2 only touched
  the two form terms + the two `status-legend`/`public-exports` BoardDocs + card 38, so the appconfig body
  change traces to a concurrent `GlossaryTerm.body` edit in `db.sqlite3`. Confirmed not-5b's, left intact
  per the maintainer carve + rule 34 — not a 5b defect.

DB integrity (read-only): `import_spec_terms --check` → `OK: 38 done cards have glossary links.`;
`manage.py check` → `System check identified no issues (0 silenced).` Independently re-ran the
two-consecutive-regenerate byte-stability check: pre-existing on-disk hashes already matched Worker 2's
reported run, and run-1 == run-2 == Worker-2 for all three files (`KANBAN.md 4809a66c…68c4a7`,
`KANBAN.html 06e82c32…68a32a`, `docs/GLOSSARY.md 453b8a95…b0b4ed3b`) — determinism proven, docs left
byte-identical to Worker 2's state, no concurrent writer landed mid-check. ORM-only confirmed (Worker 2's
command log shows `manage.py shell` ORM blocks in `transaction.atomic()`, no raw SQL). `manage.py migrate`
NOT run.

### What looks solid

- The Decision-6 correction is the precise inversion the spec demanded: the model-less sibling shape now
  lives on `DjangoFormMutation` and the subclass/post-save shape stays on `DjangoModelFormMutation` —
  neither over- nor under-stated against Decision 6 and the pinned-payload contract.
- Card-move hygiene: removed-from-WIP + appears-once-in-Done + SpecDoc/CardGlossaryTerm invariants
  satisfied, with the bootstrap `CardGlossaryTerm` correctly superseded by the `import_spec_terms` 31-link
  sync.
- No `(category, order)` collision: the verify-only Mutations membership discipline held (no blind add).
- Byte-stable regenerate independently reproduced; version quintet fully consistent at `0.0.12`.

### Temp test verification

- No temp tests written or used (5b ships no package logic under test; verification is the byte-stable-
  regenerate + `import_spec_terms --check` + `manage.py check` + read-only DB queries). Nothing to dispose.

### `Meta.return_field_name` DoD-bullet flag — assessed: CLEAN (not a finding)

Worker 2 ticked DoD item 2 ("Implement `forms/` on the DRF-style Meta surface (`Meta.form_class`,
`Meta.return_field_name`, etc.)") reading the `return_field_name` mention as a surface-description.
Concur — clean, fine to tick:
- The bullet text is byte-identical between HEAD (`- [ ]`) and now (`- [x]`); Worker 2 only flipped the
  checkbox, did not author or alter the `return_field_name` text. It is pre-existing card-body planning prose.
- Decision 6 (spec lines 1149-1157) anticipated this EXACT card-body mention and resolved it under the
  `docs/SPECS/NEXT.md` "prefer the card, surface the conflict" rule — recording the deliberate non-adoption
  as a Risks entry rather than mandating a card-body rewrite. The "etc." framing + parenthetical position
  make it a description of the planned DRF-style surface, not a literal shipped-contract promise.
- The box reflects that `forms/` shipped on the `class Meta` surface (it did). No `CardItem.text` edit is
  warranted. Recorded for Worker 1's awareness; not escalated (the spec already governs the resolution).

### Notes for Worker 1 (spec reconciliation)

- **Card-body `Status:` field reads "In progress" (not "Shipped").** The rendered DONE-038 card body shows
  `Status: In progress` (line 1365), whereas the sibling DONE-037 shows `Status: Shipped` (line 1467). This
  is a free-text card-body field independent of the kanban workflow `status.key` (which IS `done` — the card
  correctly lands in Done with the `DONE-` id). It was already `In progress` at HEAD (when the card was WIP),
  so it is NOT a 5b regression, and 5b's plan step 17 named only the stale-filename fix + the DoD completion
  flags — this body field was out of 5b's named scope. Flagging as a possible cosmetic follow-up for the
  maintainer/Worker 1 (a one-line `CardItem`/field DB edit + re-render if desired), NOT a 5b defect or a
  blocker. Not escalated as a finding.
- Concurrent-writer drift (`django-appconfig` GLOSSARY hunk + the kanban-table churn) is the maintainer's
  commit-time reconciliation point per binding decision (1), not a 5b defect — confirmed not-5b's and left
  intact.
- The `return_field_name` flag above is informational; the spec (Decision 6 + Risks) already resolves it.

### Review outcome

`review-accepted` — every documentation/release-sanity surface verified against the spec; zero
High/Medium/Low; the `return_field_name` flag assessed clean; both monolithic Slice-5 verbatim boxes
legitimately `- [x]` (5a portions landed earlier + 5b GLOSSARY/KANBAN portions rendered now = whole
contract delivered, each box's claimed contents confirmed in the rendered docs). Static-helper skip
recorded (no package `.py` logic touched — BUILD.md run-triggers not met). The mixed `db.sqlite3` /
`KANBAN.*` / `docs/GLOSSARY.md` diff is handed to the maintainer for commit-time reconciliation of the
concurrent-writer state.

---

## Final verification (Worker 1)

### Summary

**Final status: `final-accepted`.** Slice 5b is the last in-spec slice; its DB-backed GLOSSARY promotion/correction + version-line + KANBAN card move + three regenerates are correct, faithful to the spec (Decision 6, Decision 14, the `## Doc updates` GLOSSARY/KANBAN bullets), and independently re-confirmed against the rendered docs and read-only ORM/management commands. The mixed `db.sqlite3` / `KANBAN.*` / `docs/GLOSSARY.md` diff (Worker 2's 5b writes ON TOP OF the concurrent writer's edits) was honored per binding maintainer decision (1) — I verified the 5b writes, did NOT audit/revert the concurrent edits (incl. the flagged `django-appconfig` GLOSSARY hunk), and touched none of `db.sqlite3` / `KANBAN.*` / `docs/GLOSSARY.md`.

**Spec slice checklist audit — PASS.** Both monolithic Slice-5 verbatim boxes (artifact lines 96-115) are legitimately `- [x]`; each box's contracted contents actually renders:
- **Box 1 (version quintet).** GLOSSARY package-version line = `0.0.12` (`docs/GLOSSARY.md` line 20). The four non-GLOSSARY sites (`pyproject.toml`, `__init__.py`, `tests/base/test_init.py::test_version`, `uv.lock`) landed + were verified in Slice 5a (sibling artifact, final-accepted); 5b owns only the DB-backed GLOSSARY line, which renders correctly. Box fully delivered across 5a+5b.
- **Box 2 (GLOSSARY + plain docs + CHANGELOG + KANBAN).** GLOSSARY: both symbols promoted to `shipped (0.0.12)` — Index status column (lines 78, 82), entry `**Status:**` lines (342, 372); both added to Public exports (lines 30, 33, alphabetical in the `Django*` run); Index rows + Mutations browse-by-category row (line 167, verify-only — pre-existing memberships, no blind re-add); the Decision-6 `DjangoFormMutation` correction is rendered (line 344 — model-less sibling, explicitly "**not** a `DjangoMutation` subclass", own lightweight metaclass, NO `DjangoType` object slot, pinned `ok: Boolean!` + `errors: [FieldError!]!`, `perform_mutate(self, form, info) -> None`, `NON_FIELD_ERRORS` → `"__all__"`); `DjangoModelFormMutation` (line 374) correctly RETAINS the subclass / post-save-object-in-uniform-slot shape, enriched to the shipped contract. KANBAN: `DONE-038-0.0.12` renders once in Done (board line 100, card heading line 1360), `WIP-ALPHA-038` count = 0 (removed from WIP), all 6 DoD bullets `- [x]` (lines 1421-1426), DoD item 0 stale filename corrected to `docs/SPECS/spec-038-form_mutations-0_0_12.md`. The 5a plain-doc + CHANGELOG portions (README/docs-README Status + "Shipped today", GOAL criterion 6, TODAY, TREE, CHANGELOG `[0.0.12]`) landed in Slice 5a. Box fully delivered across 5a+5b. Neither box was ticked without its contract rendered → no un-tick / revision-needed.

**Load-bearing 5b deliverables — independently confirmed.** Card renders `DONE-038-0.0.12` once in Done + removed from WIP (counts above); both glossary symbols `shipped (0.0.12)`; the `DjangoFormMutation` body matches Decision 6 (model-less sibling, no object slot, `ok`+`errors`, `perform_mutate`, NOT a `DjangoMutation` subclass); `DjangoModelFormMutation` is the `DjangoMutation`-subclass flavor; GLOSSARY version line = `0.0.12`. Read-only management commands: `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 38 done cards have glossary links.`; `uv run python examples/fakeshop/manage.py check` → `System check identified no issues (0 silenced).` `manage.py migrate` and the full pytest suite were NOT run.

**DRY check — none expected, none found.** 5b is DB-row + regenerated-doc work; no package `.py` logic touched (confirmed across Worker 2 + Worker 3). Cross-slice DRY candidates carry to the integration pass (see worker-1 memory); none is a 5b blocker.

**Spec reconciliation.**
- **(a) `return_field_name` DoD bullet — CONFIRMED CLEAN, no edit.** Decision 6 (spec lines 1149-1157) deliberately did NOT adopt `Meta.return_field_name`, recording it under the `docs/SPECS/NEXT.md` "prefer the card, surface the conflict" rule as a Risks-tracked card-body tension rather than mandating a card-body rewrite. The DoD bullet (KANBAN line 1422) is card-body planning prose (note the "etc." framing + parenthetical position); it is byte-identical HEAD→now apart from the checkbox flip. The box reflects that `forms/` shipped on the `class Meta` surface (it did). Worker 3 independently assessed it clean. No `CardItem.text` edit warranted; the spec already governs the resolution.
- **(b) DONE-038 card-body free-text `Status: In progress` field — DEFERRED as cosmetic (recorded in the deferred-work catalog).** The rendered DONE-038 card body shows `Status: In progress` (KANBAN line 1365) vs sibling DONE-037's `Status: Shipped` (line 1467). Verified via `git show HEAD:KANBAN.md`: the field read `In progress` at HEAD (line 149, when the card was WIP) — so it is a pre-existing free-text field, NOT a 5b regression, independent of the workflow `status.key` (which IS `done` — the card correctly lands in Done with the `DONE-` id). It is outside 5b's named step-17 scope (which named only the stale-filename fix + the DoD completion flags). Judgment: deferring is the right call (free-text field, pre-existing, the maintainer reconciles the mixed DB diff at commit anyway; a one-line `CardItem.text` → "Shipped" + re-render is a defensible DONE-card-convention nicety but not warranted for a final-acceptance gate). NOT routing a Worker-2 DB fix; recorded in the deferred-work catalog (worker-1 memory). The artifact stays `final-accepted`.

No spec edit was made (see below). `db.sqlite3` / `KANBAN.*` / `docs/GLOSSARY.md` were not touched.

### Spec changes made (Worker 1 only)

- **None.** The Slice 5 → 5a/5b split spec edit is recorded in the sibling `bld-slice-5-docs_version_cut.md` `### Spec changes made (Worker 1 only)` (not duplicated here); this artifact's 5b plan content is verbatim the 5b half of that combined plan — partition only, no substantive plan change. The final-verification pass required no spec reconciliation edit: the `return_field_name` tension is already governed by Decision 6 + Risks, and the DONE-038 card-body `Status:` field is a deferred cosmetic DB/doc item (not a spec contract). `scripts/check_spec_glossary.py` was therefore not re-run (no spec edit to gate).
