# Build: Slice 4 — Doc updates + card wrap (no version bump)

Spec reference: `docs/spec-039-serializer_mutations-0_0_13.md` (Slice-checklist lines 1028-1051;
`## Doc updates` lines 3304-3349; Decision 12 lines 2475+; Decision 14 lines 2654-2689; DoD
items 7 & 8 lines 3642-3684; Key-glossary-reference note lines 427-437)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused (file:line).**
  - The `rest_framework/` TREE.md summary lines mirror the **`forms/` subsystem block** verbatim
    in shape — `docs/TREE.md:211-216` (package tree) and `docs/TREE.md:369` / `:511` (test tree).
    `rest_framework/` is the structural twin of `forms/` (spec Predecessors: "`rest_framework/`
    mirrors `forms/` module-for-module"), so the per-file one-liners reuse the `forms/` phrasing
    with `serializer_class` in place of `form_class`, `serializer.errors` in place of `form.errors`.
  - The GLOSSARY `SerializerMutation` **body** mirrors the **`DjangoModelFormMutation` entry body**
    (`docs/GLOSSARY.md`, `## DjangoModelFormMutation`) — the twin already shipped: "subclasses
    `DjangoMutation`, overriding `_resolve_model`… input is form-derived… `form.errors` populate
    the shared `FieldError` envelope… bound at `finalize_django_types` phase 2.5… Exported from
    the package root." The serializer body reuses that sentence skeleton (serializer-derived input,
    `serializer.errors`, the soft DRF dep, the lazy root `__getattr__` export).
  - The DB-backed move reuses the **shipped `import_spec_terms` management command**
    (`examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py`) — `_sync_card_links`
    + `_sync_spec_mentions` for the sync, `--check` (`_assert_plan_matches_db`) for the gate. No
    hand-written link wiring.
  - The three regenerators are the shipped `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`,
    `scripts/build_glossary_md.py` — DB → markdown/html renderers, run from repo root. No new script.
- **New helpers justified.** None. Slice 4 adds **no Python logic** — it edits hand-authored doc
  source (`docs/TREE.md`, `TODAY.md`, `GOAL.md`), edits the glossary/kanban DB via the Django ORM,
  and runs the three existing regenerators. Static-helper (`scripts/review_inspect.py`) is **skipped**
  with reason: doc/DB-wrap slice, no Python logic added.
- **Duplication risk avoided.** The naive risk is **hand-editing the rendered `docs/GLOSSARY.md` /
  `KANBAN.md` / `KANBAN.html`** — these are GENERATED from `examples/fakeshop/db.sqlite3`; a hand-edit
  is silently reverted by the next regenerate (and a raw SQL INSERT skips the `post_save` UUIDModel
  side-row the render needs). The plan eliminates that by editing the DB via the Django ORM
  (`manage.py shell`, `.save()` / `import_spec_terms`) and regenerating. A second risk is duplicating
  the `forms/` glossary body verbatim including its `shipped (0.0.12)` status — avoided by setting the
  serializer term's `status_text` to the **"implemented on main"** phrasing (F8), not copying the twin's
  shipped status.

### Implementation steps

The slice splits into (A) hand-authored doc-source edits, and (B) the DB-backed move + regenerate.
The **F8 split** is explicit throughout: implemented-on-main docs land now; release-status docs defer
to the joint `0.0.13` cut (shared with card 040) and are **out of scope** for this slice.

#### F8 split — what lands now vs. what defers (do NOT touch the defer column)

| Surface | Lands NOW (Slice 4) | DEFERS to joint `0.0.13` cut |
|---|---|---|
| `docs/TREE.md` | fill `rest_framework/` + `tests/rest_framework/` summary lines | — |
| `TODAY.md` | note serializer mutation as an **implemented** capability | — |
| `GOAL.md` | crit-6 example → `SerializerMutation` base + `operation = "create"` | — |
| `docs/GLOSSARY.md` body (via DB) | implemented contract + surface-key reconcile; `status_text` = **"implemented on main, releasing in 0.0.13"**; Public-exports + Index + Mutations row | the `shipped (0.0.13)` status flip (status FK + status_text) |
| `docs/README.md` / `README.md` | — | "Coming next" → "Shipped today"; README **Status** → `0.0.13` |
| `CHANGELOG.md` | — (Slice 4 MUST NOT touch) | release bullets, only on explicit maintainer prompt |
| `pyproject.toml` / `__version__` / `test_version` / `uv.lock` pkg version | — (stays `0.0.12`, Decision 14) | version bump |
| `KANBAN.md` / `KANBAN.html` (via DB) | card `039` → Done, re-render | — |

#### A. Hand-authored doc-source edits (edit the files directly; reference-style markdown links per AGENTS.md / START.md)

1. **`docs/TREE.md` — fill the `rest_framework/` package summary** at `docs/TREE.md` #"rest_framework/    # planned by TODO-ALPHA-039-0.0.13"
   (currently two collapsed `planned by` placeholder lines: the package-tree line ~310 and the
   test-tree line ~537). Replace the collapsed `rest_framework/    # planned by TODO-ALPHA-039-0.0.13 - …`
   placeholder with the expanded sub-tree mirroring `forms/` (`docs/TREE.md:211-216`), one line per
   on-disk module. On-disk reality (verified):
   - `rest_framework/__init__.py` — soft-DRF guard + the lazy `SerializerMutation` re-export surface.
   - `rest_framework/serializer_converter.py` — `convert_serializer_field` registry (DRF serializer
     field → Strawberry input annotation + required-ness; reuses the read-side scalar / choice-enum /
     `Upload` converters), dual-purposed inputs/outputs (`is_input` flag).
   - `rest_framework/inputs.py` — serializer-derived `@strawberry.input` generation
     (`<SerializerClass>Input` / `<SerializerClass>PartialInput`) from the serializer's fields.
   - `rest_framework/resolvers.py` — the serializer mutation pipeline (`is_valid()` →
     `serializer.errors` → `FieldError` envelope → `save()`, sync + async).
   - `rest_framework/sets.py` — `SerializerMutation` base + `Meta` validation; rides `DjangoMutation`
     via `_resolve_model` returning `Meta.serializer_class.Meta.model`.
   And the test-tree line ~537 expands to mirror `tests/forms/` (`docs/TREE.md:369`): one line per
   on-disk test module — `test_converter.py`, `test_inputs.py`, `test_resolvers.py`, `test_sets.py`,
   `test_soft_dependency.py`. Keep the exact box-drawing / comment-column convention of the surrounding
   tree. **Drop the `planned by TODO-ALPHA-039-0.0.13` annotation** (the subsystem is now implemented;
   the `planned by` form is for not-yet-shipped subtrees — discharge per AGENTS.md "shipped behavior
   folds into `docs/TREE.md`").
   - **Discretion (Worker 2):** the exact per-line wording is at Worker 2's discretion provided it
     mirrors the `forms/` block's depth and the comment column aligns; pin `serializer_class` /
     `serializer.errors` over the form spellings.

2. **`TODAY.md` — note the serializer mutation as an implemented capability.** Two edit sites,
   mirroring the existing `0.0.12` form-mutation prose:
   - The capability bullet block (`TODAY.md` #"Form-based mutation write surface" — the `0.0.12`
     bullet at line ~20): add a sibling bullet for the serializer flavor as **implemented on main**
     (a `SerializerMutation` over an `ItemSerializer` `ModelSerializer`, the `ModelSerializer` flavor
     reusing the same `FieldError` envelope populated from `serializer.errors`), worded as an
     implemented-on-main capability — NOT "shipped in 0.0.13" (the package version is still `0.0.12`;
     F8 + Decision 14). Match the live products surface Slice 3 landed (the exact mutation field
     name(s) and serializer class are at Worker 2's discretion — confirm against
     `examples/fakeshop/apps/products/schema.py` / `serializers.py` as Slice 3 left them).
   - The "Mutations on products today" section (`TODAY.md` #"Mutations on products today", the
     `0.0.12` form paragraph at line ~357): add the serializer-flavor paragraph in the same register,
     and update the "As of `0.0.12` it exercises…" lead-in (`TODAY.md:11`) only if its enumeration
     of flavors needs the serializer flavor added — phrase as "on main" not "as of 0.0.13".
   - **Constraint:** no `0.0.13` "shipped"/"released" wording anywhere in `TODAY.md`; the package
     version line is `0.0.12`. "implemented on main" / "lands on main" register only.

3. **`GOAL.md` — correct the crit-6 `CreateCategoryFromSerializer` example** at
   `GOAL.md` #"Coming in 0.0.13 — the DRF-serializer flavor on the same base:" (the fenced block at
   lines ~490-494). Two corrections, per spec DoD item 7 (lines 3654-3665) + Decision 6 + Decision 10:
   - Base class `DjangoMutation` → **`SerializerMutation`**:
     `class CreateCategoryFromSerializer(SerializerMutation):`
   - Add the **mandatory explicit** `operation = "create"` inside `class Meta` (Decision 10: not
     inferred), so the declaration validates under the shipped package:
     ```python
     class CreateCategoryFromSerializer(SerializerMutation):
         class Meta:
             serializer_class = CategorySerializer
             operation = "create"
     ```
   - **Discretion (Worker 2), spec-licensed but optional (DoD item 7 lines 3661-3664):** the edit
     *may* assert the inline generated input shape for the depicted `CategorySerializer(fields=("id",
     "name"))` — `CategorySerializerInput { name: String! }` (read-only `id` dropped) — so the
     declaration and its generated schema visibly agree. Recommended to add it (it discharges the
     "visibly agree" intent), as a short comment or adjacent line; the exact placement/format is
     Worker 2's discretion. Also update the surrounding prose (`GOAL.md:458` / crit-6 narrative at
     `GOAL.md:511`) ONLY where it still implies the serializer flavor "lands later" / "still lands
     later" and that is now inaccurate on main — keep the public **release** version framing (`0.0.13`)
     since GOAL.md is a roadmap doc, but the example must depict the shipped surface. Do NOT flip GOAL's
     "0.0.13" roadmap labels to "shipped"; the example-correctness fix is the in-scope change (it is
     "wrong the moment the code lands", Decision 14 line 2670-2671).

#### B. DB-backed move (`wip → done`) + glossary body edit + regenerate

**CRITICAL:** `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html` are GENERATED from
`examples/fakeshop/db.sqlite3`. Edit the **DB via the Django ORM**, then regenerate. NEVER hand-edit
the rendered markdown/html (next regenerate reverts it). Always use the ORM (`manage.py shell`,
`.save()` / `import_spec_terms`), never raw SQL (a raw INSERT skips the `post_save` UUIDModel side-row
the render needs).

**Pre-verified live-DB facts (Worker 0 verified; Worker 2 re-confirms but does not re-derive):**
- Card #39 status = `wip` (milestone `alpha`), renders `WIP-ALPHA-039-0.0.13`. Move is **`wip → done`**
  → renders `DONE-039-0.0.13` (done cards drop the milestone prefix; `build_kanban_md.card_column_key`
  returns `"done"` for `status=done`). (Spec text says "TODO-ALPHA-039"; a concurrent maintainer moved
  it to `wip`. **The DB is ground truth — the move is `wip → done`.**)
- A `SpecDoc` row ALREADY EXISTS for card 39 (name `spec-039-serializer_mutations-0_0_13`, url
  `https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-039-serializer_mutations-0_0_13.md`).
  **KEEP / update in place — do NOT `.create()`** (name is unique → a create collides).
- `CardGlossaryTerm` count for card 39 = **0**. DONE-card invariant requires ≥1 → **bootstrap ≥1**
  before `card.save()` to done.
- All 38 anchors in `docs/spec-039-serializer_mutations-0_0_13-terms.csv` already EXIST as
  `GlossaryTerm` rows (incl. `serializermutation`) → `import_spec_terms`' precondition (every CSV anchor
  exists) is met; **no net-new glossary-term seeding**.
- `GlossaryStatus` has only `shipped` / `planned` keys. `GlossaryTerm.status_text` is a free-text field
  and **is what the renderer prints** (`build_glossary_md.render_term` / `render_index` read
  `term['statusText']`, NOT the status FK). So set `serializermutation.status_text = "implemented on
  main, releasing in \`0.0.13\`"` while **keeping the `status` FK = `planned`** (the `shipped` FK flip +
  the `shipped (0.0.13)` status_text defer to the joint cut). Current: `status` FK `planned`,
  `status_text = "planned for \`0.0.13\`"`, body references the rejected graphene keys
  `Meta.lookup_field` / `Meta.model_operations`.
- `serializermutation` is **ALREADY** in the `mutations` category (`GlossaryCategoryMembership`,
  category key `mutations`, `order=4`) and **ALREADY** in the Index (`index_order=67`, `entry_order=71`,
  non-null → renders today). So the **membership-add + the unique-`(category, order)` collision-rebalance
  dance is NOT needed** — both the Mutations browse row and the Index already carry the term. (Worker 2
  re-confirms membership + index_order before assuming the no-op.)
- **"Public exports" is NOT a `GlossaryCategory`** — it is the hand-authored `BoardDoc` row
  (`namespace=glossary`, `key=public-exports`) whose `body` lists re-exported symbols. The body does
  NOT currently mention `SerializerMutation`. So "add to Public exports" = **edit the
  `public-exports` BoardDoc `body`** (via ORM `.save()`) to add a `SerializerMutation` bullet, then
  regenerate. See step B3 for the `__all__` nuance.

Steps (ORM via `examples/fakeshop/manage.py shell`; regenerate from repo root):

**B1. Update the `serializermutation` GlossaryTerm body + status_text.**
   - Set `body` to the implemented contract, mirroring the `DjangoModelFormMutation` body skeleton:
     consumes a DRF `Serializer` / `ModelSerializer` via `Meta.serializer_class`; subclasses
     `DjangoMutation`, overriding `_resolve_model` to return `Meta.serializer_class.Meta.model` (so it
     reuses the base value: the primary `DjangoType` payload in the uniform `node` / `result` slot, the
     `DjangoModelPermission` default, the visibility-scoped `update` locate, the optimizer G2 re-fetch);
     input is **serializer-derived** (the `serializer_converter` field map + the serializer-input
     generator); validation runs `serializer.is_valid()` then `serializer.save()`, with
     `serializer.errors` populating the shared `FieldError` envelope (`NON_FIELD_ERRORS`/`"__all__"`);
     bound at `finalize_django_types` phase 2.5; the soft `djangorestframework` dependency (package
     imports without DRF; the helper raises `ImportError` with an install hint naming
     `djangorestframework>=3.17.0` when accessed without DRF); the one net-new public symbol is a
     lazy root `__getattr__` export under the DRF guard, NOT in `__all__` (F1).
   - **Reconcile the surface keys** (recorded as deliberate non-adoptions of graphene's keys):
     `Meta.operation` over graphene's `Meta.model_operations`; the `id:`-decode locate over graphene's
     `Meta.lookup_field`. Drop the stale `Meta.lookup_field` / `Meta.model_operations` /
     `Meta.optional_fields` references the current body carries; phrase the non-adoption explicitly
     (e.g. "uses `Meta.operation` (not graphene's `model_operations`); locates the `update` target by
     decoding the `id:` argument (not a `Meta.lookup_field`)").
   - Set `status_text = "implemented on main, releasing in \`0.0.13\`"` (the exact phrasing the spec
     pins: spec lines 1043 / 3335 / 433-434). **Keep `status` FK = `planned`** (do not flip to
     `shipped`). `.save()` the term.
   - **No `GlossaryCategoryMembership` add and no Index edit needed** (already present per the
     pre-verified facts) — Worker 2 confirms `index_order` is non-null and the `mutations` membership
     exists, then leaves them. (If a re-confirm shows either missing, add the `mutations` membership
     and/or set `index_order`; only THEN does the `(category, order)` collision-rebalance dance apply —
     bump existing members `order += 1000` into a temp band, reassign `0..N-1`. Expected: not needed.)

**B2. Keep the existing `SpecDoc`** — verify `name` + `url` correct (they are). Update in place ONLY if
   wrong. Do NOT `.create()` (unique-name collision).

**B3. Edit the `public-exports` BoardDoc body** (the Public-exports surface). Add a `SerializerMutation`
   bullet to `BoardDoc.objects.get(namespace="glossary", key="public-exports").body`, in the alphabetical
   position among the `Django*` entries, linking `[\`SerializerMutation\`](#serializermutation)`.
   - **`__all__` nuance (F1) — discretion + recommended phrasing:** the doc header reads "Symbols
     re-exported from `django_strawberry_framework`". `SerializerMutation` IS re-exported from the root
     (via the PEP-562 `__getattr__` under the DRF soft guard) but is **NOT in `__all__`** (so
     `from … import *` stays DRF-free). To avoid implying it is an unconditional `__all__` export, the
     bullet should note the soft-DRF lazy nature, e.g.:
     `- [\`SerializerMutation\`](#serializermutation) — DRF \`ModelSerializer\` mutation base subclassing
     \`DjangoMutation\`; a lazy root export under the soft \`djangorestframework\` guard (resolved via
     \`__getattr__\`, not in \`__all__\` while DRF is soft).`
     The exact wording is Worker 2's discretion provided it (a) does not claim membership in `__all__`
     and (b) names the soft-DRF lazy nature. `.save()` the BoardDoc. This is an implemented-on-main
     reality (the symbol IS importable from the root today), so it lands now under F8 — it is not a
     release-status flip.

**B4. Bootstrap ≥1 `CardGlossaryTerm`** for card 39 BEFORE the done-save (DONE-card invariant). Create one
   `CardGlossaryTerm` linking card 39 → the `serializermutation` `GlossaryTerm` (the first CSV anchor),
   via ORM `.create()` / `update_or_create` (NOT raw SQL). `import_spec_terms` (B6) will reconcile/reorder
   the full 38-term set afterward, so the bootstrap `order` value is throwaway.

**B5. Flip status to done:** `card.status = Status.objects.get(key="done"); card.save()`. The ORM
   `.save()` fires the `apps/kanban/signals.py` pre_save validation (asserts linked SpecDoc ✓ +
   ≥1 CardGlossaryTerm ✓ from B4) and the milestone side-effect (`pre_save`: a done card clears its
   milestone prefix per the signal at `signals.py:132`). If the save raises `ValidationError`, the
   bootstrap (B4) or SpecDoc (B2) precondition was not met — fix and retry; do not force.

**B6. Sync glossary links:** `uv run python examples/fakeshop/manage.py import_spec_terms` (NO `--check`)
   from repo root. This (`_sync_card_links`) reconciles card 39's `CardGlossaryTerm` set to all 38 CSV
   anchors (the bootstrap term survives via `update_or_create`, re-ordered) and (`_sync_spec_mentions`)
   syncs the `GlossarySpecMention` rows for the spec_path. Only DONE cards are planned by the command
   (`_plan_done_cards` filters `status__key="done"`), which is why B5 precedes B6.

**B7. Fix card-body DoD CardItems.** Mark every shipped `definition_of_done` `CardItem.is_complete=True`
   for card 39. **All 7 DoD CardItems ship in this build** (verified against the live DB; the deferred
   joint-cut work — version bump / README "Shipped today" / CHANGELOG / GLOSSARY `shipped` flip — is NOT
   represented as a card-body `definition_of_done` CardItem; it lives in the spec's DoD items 7 & 8 and
   the deferred catalog, not on the card). So tick all 7:
   - order 0 "Add `docs/spec-serializer_mutations.md`." — spec exists → `is_complete=True`
   - order 1 "Implement `rest_framework/` exposing `SerializerMutation` …" — Slices 1-3 → `True`
   - order 2 "Serializer-field → input mapping in `serializer_converter.py` …" — Slice 1 → `True`
   - order 3 "`rest_framework` soft dependency … helper raises `ImportError` …" — Slices 0+2 → `True`
   - order 4 "Validation errors surface through `errors: list[FieldError]` from `DONE-036-0.0.11`,
     populated from `serializer.errors`." — Slice 3 → `True`
   - order 5 "Tests under `tests/rest_framework/`." — shipped → `True`
   - order 6 "Live HTTP coverage under `examples/fakeshop/test_query/` …" — Slice 3 → `True`
   Save each. (Only `definition_of_done` items have meaningful `is_complete`; leave other sections'
   `is_complete` as-is.) **No deferred-DoD-item follow-up marker is needed** because no card-body DoD
   item maps to deferred joint-cut work — the deferral is recorded in the spec DoD + the deferred catalog
   (`### Notes for Worker 1` below). **Card-body ref residue:** the `{{card_ref:N}}` placeholders are
   FK-backed and render correctly (`DONE-036-0.0.11` resolves at line 177); the spec wrap names no stale
   card-body refs to fix. No residue work.

**B8. Regenerate all three** from repo root (each runs an in-process `/graphql/` query against the DB):
   - `uv run python scripts/build_kanban_md.py`
   - `uv run python scripts/build_kanban_html.py`
   - `uv run python scripts/build_glossary_md.py`

### Test additions / updates

**None — doc/DB-wrap slice; no Python logic, no pytest tests.** Verification is by regenerate-stability
+ the kanban/glossary consistency commands, NOT pytest:

- **Two-consecutive-regenerate byte-stability** (the gate replacing "`git diff docs/GLOSSARY.md` is
  clean", which is invalid this slice because the GLOSSARY body legitimately diverges from HEAD per F8):
  run each of the three regenerators **twice**; the second run must produce a **byte-identical** file to
  the first (`shasum` / `cmp` the two renders) → the DB renders deterministically and the slice's writes
  are stable. (Do not gate on `git diff` cleanliness for `docs/GLOSSARY.md` / `KANBAN.md` / `KANBAN.html`
  / `db.sqlite3` — they have intentionally diverged.)
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → reports `OK: N done cards have
  glossary links.` (asserts card 39's glossary links AND the spec_path `GlossarySpecMention` rows match
  the 38-anchor CSV exactly).
- `uv run python examples/fakeshop/manage.py check` → passes (model/admin/url config clean).
- **Spot-checks of the rendered result:** `KANBAN.md` shows `DONE-039-0.0.13` in the **Done** column
  (removed from To-Do/WIP, present once) with all 7 DoD bullets ticked `- [x]`; `docs/GLOSSARY.md`'s
  `## SerializerMutation` entry shows `**Status:** implemented on main, releasing in \`0.0.13\`.`, the
  reconciled surface keys (`Meta.operation`, the `id:`-decode locate; no `lookup_field` /
  `model_operations`), the implemented body, and the Public-exports list includes the
  `SerializerMutation` bullet.

Note for Worker 3 (review-time): there are no temp tests; the regenerators and consistency commands are
the verification surface. The semantic DB diff (kanban card move + glossary body) is the slice's intended
output, not tool drift — do NOT `git checkout` `db.sqlite3` / `KANBAN.md` / `KANBAN.html` /
`docs/GLOSSARY.md`.

### Implementation discretion items

- **TREE.md per-line wording** for the `rest_framework/` + `tests/rest_framework/` sub-tree — at Worker 2's
  discretion provided it mirrors the `forms/` block's depth and the comment column aligns; pin the
  `serializer_class` / `serializer.errors` spellings over the form spellings.
- **TODAY.md serializer-flavor field name(s) / serializer class name** — confirm against the products
  live surface Slice 3 landed (`examples/fakeshop/apps/products/schema.py` / `serializers.py`) and use
  the actual names; the exact prose register is Worker 2's discretion within the "implemented on main"
  constraint (no `0.0.13`-shipped wording).
- **GOAL.md inline generated-shape assertion** (`CategorySerializerInput { name: String! }`) — spec-licensed
  but optional (DoD item 7); recommended to include; exact placement/format Worker 2's discretion.
- **Public-exports `SerializerMutation` bullet wording** — Worker 2's discretion provided it does not
  claim `__all__` membership and names the soft-DRF lazy (`__getattr__`) nature (recommended phrasing in
  step B3).
- **Bootstrap `CardGlossaryTerm` order value** (B4) — throwaway; `import_spec_terms` reorders it.

### Spec slice checklist (verbatim)

(Copied verbatim from `docs/spec-039-serializer_mutations-0_0_13.md` lines 1028-1051. Worker 2 ticks
each box as it lands that sub-check; Worker 1 audits at final verification.)

- [x] Slice 4: doc updates + card wrap (per
  [Doc updates](#doc-updates) /
  [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)
  / [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
  **Soft-dep wiring is NOT here — it landed in the pre-Slice-1 gate (Slice 0, F11), since
  Slice 1–3 tests import DRF.** Release-status wording is **split from implementation
  docs** (**F8**):
  - [x] **Implemented-on-main docs (land now):** [`docs/TREE.md`][tree] (fill the
    `rest_framework/` / [`tests/rest_framework/`][test-rest-framework] summary lines),
    [`TODAY.md`][today] (note the serializer mutation as an implemented capability),
    [`docs/GLOSSARY.md`][glossary] (update the
    [`SerializerMutation`][glossary-serializermutation] **body** to the implemented
    contract + add it to **Public exports** + the **Index** + the **Mutations**
    browse-by-category row; reconcile the surface keys — `Meta.operation` over
    `model_operations`, the `id:`-decode locate over `lookup_field`; mark status
    **"implemented on main, releasing in 0.0.13"**, **not** `shipped (0.0.13)` yet),
    [`GOAL.md`][goal] (criterion 6's crit-6 example corrected to the shipped surface —
    `SerializerMutation` base + `operation = "create"`).
  - [ ] **Joint-cut docs (deferred to the `0.0.13` release):** flip the GLOSSARY status to
    `shipped (0.0.13)`; [`docs/README.md`][docs-readme] / [`README.md`][readme] move the
    flavor from "Coming next (`0.0.13`)" to "Shipped today" (README **Status** line →
    `0.0.13`); [`CHANGELOG.md`][changelog] release bullets — all at the joint cut, only
    when its maintainer prompt explicitly requests the `CHANGELOG.md` edit.
  - [x] **Card wrap:** [`KANBAN.md`][kanban] (card → Done via the kanban DB + re-render).

> Worker-2 ticking guidance for the verbatim boxes: the parent "Slice 4" box and the
> **Implemented-on-main docs** + **Card wrap** sub-boxes land in THIS slice (tick when their
> contract lands in the diff). The **Joint-cut docs (deferred)** sub-box is intentionally NOT
> shipped in Slice 4 (F8 / Decision 14) — Worker 2 leaves it `- [ ]`; Worker 1 records its
> deferral under `### Spec changes made (Worker 1 only)` at final verification (target: joint
> `0.0.13` cut shared with card 040; `CHANGELOG.md` only on explicit maintainer prompt). The
> parent box is ticked when the in-scope sub-boxes (implemented-on-main + card wrap) all land.

### Notes for Worker 1 (spec reconciliation)

- **Spec status-header reconciliation (Slice-4-owned; do at final verification).** Spec lines 55-56
  read `Status: **IN PROGRESS** — … no slice built yet.` This is stale — Slices 0-3 are all
  final-accepted and the implementation is on main. Per the per-spawn status-line re-verification rule
  (worker-1.md) and my carry-forward across Slices 1-3 ("stale spec Status header → Slice 4 owns the
  implemented-on-main edit"), **reconcile lines 55-56 in this slice's final-verification pass** to reflect
  reality: implementation slices landed, the implemented-on-main docs + card wrap are done, and the joint
  `0.0.13` cut (with card 040) still owns the version bump + public release-status flip. Phrase the new
  Status as e.g. "IMPLEMENTED ON MAIN (Slices 0-3 landed; docs + card wrap done in Slice 4) — releasing in
  the joint `0.0.13` cut shared with `TODO-ALPHA-040-0.0.13`." Record under `### Spec changes made
  (Worker 1 only)` with the line range + reason. Also re-check the "Planned for `0.0.13`" body line
  (spec line 3) and the inline "no slice built yet" if it recurs. (Worker-1-only spec edit; not a Worker 2
  task.)

- **Deferred joint-cut docs (record under `### Spec changes made (Worker 1 only)` at final verification).**
  The verbatim "Joint-cut docs (deferred)" sub-box stays `- [ ]` — it is licensed deferral (F8 /
  Decision 14, spec lines 1046-1050 / 3338-3345 / 2663-2671). Target: the joint `0.0.13` cut shared with
  `TODO-ALPHA-040-0.0.13`; `CHANGELOG.md` only when the cut's maintainer prompt explicitly requests it
  (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; the spec describes but cannot
  authorize the edit). Surfaces deferred: GLOSSARY `shipped (0.0.13)` status flip (status FK +
  status_text), `docs/README.md` / `README.md` "Coming next" → "Shipped today" (README Status →
  `0.0.13`), `CHANGELOG.md` release bullets.

- **Carry-ins for the integration pass / `bld-final.md` deferred catalog (NOT Slice-4 fixes — do NOT plan
  to fix them here):**
  1. `relation_field_error` / `"Invalid id for relation …"` 3-site near-copy → shared ctor
     (`forms/resolvers.py` `_relation_field_error` + `rest_framework/resolvers.py` `_relation_field_error`
     byte-identical + `mutations/resolvers.py` `_raw_pk_relation_error`, the 036-preexisting third site).
     Spans the 036 model path → integration DRY scan; route to `bld-integration.md` + `bld-final.md`'s
     deferred catalog.
  2. L1 vacuous-tautology assertion at `tests/rest_framework/test_inputs.py:620` (UNSET singleton →
     `X or not X`; contract pinned by the adjacent lines). Slice-1 carry; folds into the integration pass
     (both touch `tests/rest_framework`). Route to the deferred catalog.

- **Generated-doc verification caveat for the integration/final pass.** Because Slice 4 legitimately
  diverges `db.sqlite3` / `docs/GLOSSARY.md` / `KANBAN.md` / `KANBAN.html` from HEAD, the final gate's
  `git diff --check` must treat those four as expected-divergent (page-level binary churn on `db.sqlite3`
  is not proof of a no-op; semantic diff = the card move + glossary body). The two-consecutive-regenerate
  byte-stability check is the per-slice gate; the maintainer reconciles the mixed DB diff at commit.

---

## Build report (Worker 2)

Status: built. No version bump, no source/test `.py` edits (doc + DB-wrap slice).

### Files touched

**Hand-authored doc source (edited directly):**
- `docs/TREE.md` — filled the `rest_framework/` package subtree (in BOTH the current-state tree
  and the target-layout tree) mirroring the `forms/` block depth, one line per on-disk module
  (`__init__.py` / `serializer_converter.py` / `inputs.py` / `resolvers.py` / `sets.py`), pinning
  `serializer_class` / `serializer.errors` over the form spellings; dropped the
  `planned by TODO-ALPHA-039-0.0.13` annotation (subsystem now implemented). Filled
  `tests/rest_framework/` in BOTH the current test tree and the target test shape, one line per
  on-disk test module (`test_converter.py` / `test_inputs.py` / `test_resolvers.py` /
  `test_sets.py` / `test_soft_dependency.py`). No stale `039` ref remains in TREE.md (the line-50
  `rest_framework/` is the graphene-django REFERENCE tree, correctly untouched).
- `TODAY.md` — added a serializer-flavor capability bullet (the `createItemViaSerializer` /
  `updateItemViaSerializer` over `ItemSerializer` surface Slice 3 landed) and a
  `**Serializer-backed mutations (on main, releasing in 0.0.13).**` paragraph in "Mutations on
  products today"; added the `[glossary-serializermutation]` reference-link def. Register is
  "implemented on main / releasing in `0.0.13`" — no `0.0.13`-shipped/released wording; the
  package-version frame stays `0.0.12`.
- `GOAL.md` — corrected the crit-6 `CreateCategoryFromSerializer` example: base
  `DjangoMutation` → `SerializerMutation`, added the mandatory `operation = "create"` in
  `class Meta`, and added the inline generated-input assertion comment
  (`CategorySerializerInput { name: String! }`, read-only `id` dropped). Left the roadmap-version
  prose ("lands in `0.0.13`") as instructed (GOAL.md is a roadmap doc).

**DB-via-ORM edits (`examples/fakeshop/manage.py shell`, `.save()` / `update_or_create`; never raw SQL):**
- `glossary.GlossaryTerm[anchor=serializermutation]` — replaced `body` with the implemented
  contract (the `Meta.serializer_class` surface, serializer-derived input, `serializer.errors` →
  `FieldError` envelope, the soft DRF dep + lazy `__getattr__` not-in-`__all__` symbol, 036 base
  reuse) + the explicit surface-key non-adoptions (`Meta.operation` over `model_operations`;
  `id:`-decode locate over `lookup_field`); set `status_text = "implemented on main, releasing in
  \`0.0.13\`"`; **kept `status` FK = `planned`** (the `shipped` flip defers to the joint cut).
- `kanban.BoardDoc[namespace=glossary, key=public-exports]` — added the `SerializerMutation`
  bullet (alpha position after `OptimizerHint`, before `SyncMisuseError`), noting the soft-DRF
  lazy `__getattr__` / not-in-`__all__` nuance (F1), without claiming `__all__` membership.
- `kanban.Card[number=39]` — bootstrapped 1 `CardGlossaryTerm` (→ `serializermutation`) BEFORE the
  done-save (DONE-card invariant), then `status` FK `wip → done` (`.save()` fired the pre_save
  validation: SpecDoc present ✓ + ≥1 CardGlossaryTerm ✓). SpecDoc kept in place (name + url
  re-verified; no `.create()`). Then `import_spec_terms` reconciled card 39's links to all 38 CSV
  anchors (count 0 → 38, `serializermutation` first at order 0) and synced the spec mentions.
- `kanban.CardItem` ×7 (`section.key=definition_of_done`, card 39) — all set `is_complete=True`;
  render confirms all 7 `- [x]`.

**Regenerated generated files (from repo root):**
- `KANBAN.md`, `KANBAN.html` (`scripts/build_kanban_md.py` / `build_kanban_html.py`)
- `docs/GLOSSARY.md` (`scripts/build_glossary_md.py`)
- `examples/fakeshop/db.sqlite3` — carries the intended card move + glossary/boarddoc body edits.

### Tests added or updated

None; doc / DB-wrap slice (no Python logic, no pytest tests). Verification is by regenerate
byte-stability + the kanban/glossary consistency commands, per the plan.

### Verification command results

- **Two-consecutive-regenerate byte-stability (the per-slice gate):** ran all three regenerators
  twice; pass-1 and pass-2 SHA-256 are byte-identical:
  - `KANBAN.md`     `a16e299f08c0d67635c9fdd76ab05bcfd838fe670e0359b0f52da46dd967dc77`
  - `KANBAN.html`   `4644baf5107e9baf5ba00670d4f955a8822ac24069183dd37ea33a17a8e7584e`
  - `docs/GLOSSARY.md` `ec56a5a964c88e6870c93043ac95391f2260e3f31ad9c172e87c3c7dd2cdde3f`
  (`diff` of the two hash dumps empty → DB renders deterministically.)
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 39 done cards have
  glossary links.`
- `uv run python examples/fakeshop/manage.py check` → `System check identified no issues (0
  silenced).`
- **Spot-checks:** `KANBAN.md` shows `DONE-039-0.0.13` in the Done table + a card-detail section,
  the milestone `alpha` prefix correctly dropped, all 7 DoD bullets `- [x]`, the
  `SerializerMutation` glossary-term status `implemented on main, releasing in 0.0.13`; no
  `WIP-ALPHA-039` / `TODO-ALPHA-039` id remains (the surviving `DONE-039-0.0.13` cross-refs in
  card 036's body / dependency graph are FK-backed `{{card_ref}}` placeholders resolving to the new
  id — expected). `docs/GLOSSARY.md` `## SerializerMutation` entry, the Index row (`implemented on
  main, releasing in 0.0.13`), the Public-exports bullet (soft-DRF lazy, no `__all__` claim), and
  the Mutations browse row all render correctly.

### Validation run

- `uv run ruff format .` → `295 files left unchanged` (no-op, as expected — no `.py` changed by
  this slice; the COM812-vs-formatter warning is pre-existing config noise).
- `uv run ruff check --fix .` → `All checks passed!` (no fixes applied).
- `git status --short` classification:
  - **Slice-4-intended (mine):** `GOAL.md`, `TODAY.md`, `docs/TREE.md` (hand-authored);
    `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3` (DB-edit +
    regenerate). Plus this artifact (report + checklist ticks) and `worker-memory/worker-2.md`.
  - **Concurrent churn I did NOT author (do NOT revert — noted for the maintainer):** all
    `django_strawberry_framework/**/*.py`, `tests/**/*.py`, `examples/fakeshop/apps/products/*.py`,
    `examples/fakeshop/config/settings.py`, `examples/fakeshop/test_query/test_products_api.py`,
    `pyproject.toml`, `uv.lock`, `docs/spec-039-*.md`, `docs/feedback.md`, and the untracked
    `docs/builder/bld-slice-*.md` / `build-039-*.md` / `tests/utils/test_converters.py`. These are
    the prior-accepted Slice 0–3 source/test/spec working-tree state, NOT touched this pass. HEAD
    advanced during the session (session-start `b2d088f2` → now `b9d0732d "Delete 038 bld
    artifacts"`), so a concurrent maintainer process is active; ruff confirmed it changed none of
    them (`295 files left unchanged`). Left untouched per the "do not revert concurrent churn"
    guardrail.
- No `pytest --cov*` (this slice has no pytest tests).

### Implementation notes (design deltas the plan did not pin)

- **`BoardDoc` lives in `apps.kanban.models`, not `apps.glossary.models`** (the plan's B3 / verified
  facts said `apps.glossary.models`). It is a shared prose-section model partitioned by `namespace`;
  the Public-exports doc is `namespace="glossary", key="public-exports"`. Mechanically obvious;
  flagged in Notes for Worker 1.
- **Public-exports bullet placement** — strict alphabetical among capitalized symbols puts
  `SerializerMutation` after `OptimizerHint` and before `SyncMisuseError` (`Se` < `Sy`), not inside
  the `Django*` cluster. Anchored the insert on the `OptimizerHint` line.
- **Glossary body shape** — the renderer prepends `**Status:** <status_text>.`; the `GlossaryTerm.body`
  field holds the prose from the first paragraph through the `**See also:**` line. Modeled the body
  on the `DjangoModelFormMutation` twin skeleton, swapping form→serializer spellings and adding the
  surface-key-non-adoption paragraph + the soft-DRF paragraph.
- **`optional_fields`** is kept in the new body only as a legitimate input-narrowing `Meta` key
  (per `sets.py` `_validate_meta`), NOT as one of the dropped graphene keys — the plan said to drop
  the stale `lookup_field` / `model_operations` graphene-key references, which I did.
- **DoD-item text vs plan paraphrase** — the live CardItem `text` for orders 1–2 reads
  `Implement \`django_strawberry_framework/rest_framework/\` …` / `… lives in
  \`rest_framework/serializer_converter.py\` …` (the plan paraphrased these); ticked all 7 by
  `section.key`, no text edits.

### Notes for Worker 1 (spec reconciliation)

- **Card 39 `planning_state` left as "In progress" (deliberate, matches precedent).** The card's
  free-text `planning_state` FK renders `- Status: In progress` in KANBAN.md. This field is NOT
  named in the plan, the spec slice checklist, or the build steps (the card-wrap contract is the
  `status` FK `wip → done`, which drove column placement + the `DONE-039-0.0.13` id). The
  immediately-preceding **DONE-038-0.0.12 card also carries `planning_state="In progress"`** (a
  final-accepted card wrapped through this same workflow), so leaving it matches precedent rather
  than introducing drift. If the maintainer wants done cards to read `planning_state="Shipped"`,
  that is a separate board-hygiene pass spanning at least cards 38 + 39 (and the `Planned` /
  `Needs spec` done cards 29–33) — out of this slice's contract. Flagging for the joint-cut /
  integration pass.
- **`BoardDoc` model location correction** — the plan's B3 + the verified-facts block say "the
  hand-authored `public-exports` `BoardDoc` body … `BoardDoc.objects.get(namespace=...)`" implying
  `apps.glossary.models`; the model actually lives in `apps.kanban.models` (a shared
  namespace-partitioned prose model). No behavioral change — the `namespace="glossary",
  key="public-exports"` lookup is correct — only the import path. Recording per the small-drift rule.
- **Joint-cut docs (deferred) sub-box stays `- [ ]`** — licensed deferral (F8 / Decision 14). Target:
  the joint `0.0.13` cut shared with `TODO-ALPHA-040-0.0.13`. Surfaces deferred: GLOSSARY `shipped
  (0.0.13)` status flip (status FK + status_text), `docs/README.md` / `README.md` "Coming next" →
  "Shipped today" (README Status → `0.0.13`), `CHANGELOG.md` release bullets (only on explicit
  maintainer prompt). I did NOT touch `CHANGELOG.md`, the `README.md` Status line, or `docs/README.md`
  "Coming next".
- **Spec status-header reconciliation (Slice-4-owned, Worker 1 to do at final verification).** Per
  the plan's Notes-for-Worker-1: spec lines 55-56 read `Status: **IN PROGRESS** — … no slice built
  yet.` — stale; reconcile to the implemented-on-main + docs/card-wrap-done framing, joint `0.0.13`
  cut owning the version bump + release-status flip. (Worker-1-only spec edit; I did not touch the
  spec — the `docs/spec-039-*.md` modification in `git status` is pre-existing concurrent churn.)

### Notes for Worker 3 (review-time)

- No temp tests; the verification surface is the two-regenerate byte-stability + `import_spec_terms
  --check` + `manage.py check` (all green above). No shadow files used.
- The semantic DB diff (card move + glossary body + BoardDoc bullet + DoD ticks) IS the slice's
  intended output — do NOT `git checkout` `db.sqlite3` / `KANBAN.md` / `KANBAN.html` /
  `docs/GLOSSARY.md`. Because GLOSSARY legitimately diverges from HEAD this slice, do NOT gate on
  `git diff docs/GLOSSARY.md` cleanliness — the byte-stability check is the gate.
- The large set of `.py` / `pyproject.toml` / `uv.lock` / spec modifications in `git status` is
  concurrent prior-slice churn I did not author (ruff confirmed it changed nothing); see the
  Validation classification above.

---

## Review (Worker 3)

Status: review-accepted

Scope filter (per `### Files touched`): reviewed ONLY Slice-4's contribution — hand-authored
`GOAL.md` / `TODAY.md` / `docs/TREE.md`; DB-backed `docs/GLOSSARY.md` / `KANBAN.md` / `KANBAN.html`
(semantic content via rendered output + the embedded JSON, not bytes); `examples/fakeshop/db.sqlite3`
(via render). All Slice 0-3 source/test/spec working-tree churn and `docs/feedback.md` treated as
prior-accepted / baseline-dirty and out of scope.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

None for this slice. Slice 4 adds no Python logic; the doc edits reuse the established shapes
(the `forms/` TREE block depth for the `rest_framework/` subtree, the `DjangoModelFormMutation`
GLOSSARY body skeleton swapped form→serializer, the `0.0.12` form-mutation TODAY prose register).
The cross-slice `_relation_field_error` / `relation_field_error` 3-site near-copy and the
`test_inputs.py:620` vacuous-tautology carry-ins are already routed to the integration/final
deferred catalog by Worker 1's plan notes and my Slice-1/3 memory; they are not Slice-4 defects.

### Public-surface check

Slice 4 added NOTHING to `django_strawberry_framework/__init__.py`. The `__getattr__` / `__all__`
diff present there is Slice-2-accepted work (the PEP-562 lazy `SerializerMutation` export under the
DRF soft guard; the prior `TODO(spec-039 Slice 2)` comment was replaced by the actual `__getattr__`
in Slice 2, not this slice). `SerializerMutation` is deliberately NOT in `__all__` (F1) — confirmed
in the diff. No Slice-4 contribution to the public surface.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. `git status` confirms `CHANGELOG.md` is absent
from the diff — the correct F8 / Decision-14 behavior (release bullets defer to the joint `0.0.13`
cut, only on explicit maintainer prompt per AGENTS.md).

### Documentation / release sanity (the centerpiece for this slice)

- **F8 split held (CRITICAL) — PASS.** `docs/GLOSSARY.md` `## \`SerializerMutation\`` entry
  (line 1247) reads `**Status:** implemented on main, releasing in \`0.0.13\`.` — the free-text
  `status_text` the spec pins (spec lines 117 / 1043 / 3335 / 3650), NOT `shipped (0.0.13)`. The
  `status` FK stays **planned** (no `shipped (0.0.13)` string anywhere in `docs/GLOSSARY.md` /
  `KANBAN.md` — grep empty). Surface keys reconciled: body uses `Meta.operation` (explicitly "not
  graphene's `model_operations`") and the `id:`-decode locate (explicitly "not a `Meta.lookup_field`");
  the stale `lookup_field` / `model_operations` references are gone from the GLOSSARY body
  (`optional_fields` retained only as a legitimate input-narrowing `Meta` key, correct). `SerializerMutation`
  appears in Public exports (line 43, soft-DRF lazy framing, NO `__all__` claim), the Index
  (line 142, `implemented on main, releasing in \`0.0.13\``), and the Mutations browse-by-category row
  (line 168). Joint-cut deferrals confirmed ABSENT via `git status`: no `CHANGELOG.md`, no
  `README.md`, no `docs/README.md` in the diff; no `shipped (0.0.13)`; no README Status → `0.0.13`.
- **Version invariant — PASS.** Package version is `0.0.12` in `pyproject.toml:4` and
  `__init__.py:37`. No doc edit advertises a *released* `0.0.13`. The single `0.0.13` mention in the
  deliberately-edited prose (GOAL.md:458 "...lands in `0.0.13`", and the GOAL example comment "Coming
  in 0.0.13") is roadmap framing GOAL.md is licensed to keep (plan step 3); TODAY.md uses
  "implemented on main, releasing in `0.0.13`" / "on main" register only — no shipped/released claim.
- **KANBAN card move — PASS.** Card 39 → Done: the embedded JSON in `KANBAN.html` shows
  `"status":{"key":"done","label":"Done"}`; the `WIP / DONE spec map` table (KANBAN.md:101) and the
  card-detail heading (KANBAN.md:1303) render `DONE-039-0.0.13` (milestone `alpha` prefix correctly
  dropped). No `WIP-ALPHA-039` / `TODO-ALPHA-039` remains in `KANBAN.md` or `KANBAN.html` (grep
  empty); the other 6 `DONE-039-0.0.13` occurrences are FK-backed `{{card_ref}}` cross-refs in card
  036/027 bodies + the dependency graph (expected, matches my KANBAN-residue memory note). All 7 DoD
  items render `- [x]` (KANBAN.md:1371-1377). The `planning_state` rendering `- Status: In progress`
  is the known board-hygiene artifact — verified DONE-038-0.0.12 (a final-accepted card) carries the
  identical `status: Done / planningState: In progress` shape, so it matches precedent and is NOT a
  Slice-4 defect (per the review brief; flagged by Worker 2 for the joint-cut board-hygiene pass).
- **GOAL.md crit-6 — PASS.** `class CreateCategoryFromSerializer(SerializerMutation): class Meta:
  serializer_class = CategorySerializer; operation = "create"` with the inline generated-shape
  assertion `# Generated input drops the read-only \`id\`: CategorySerializerInput { name: String! }`.
  Base flipped from `DjangoMutation` → `SerializerMutation`, mandatory explicit `operation` present.
- **TODAY.md / docs/TREE.md — PASS.** TODAY.md adds the serializer-flavor capability bullet + the
  "Serializer-backed mutations (on main, releasing in `0.0.13`)" paragraph; the named live surface
  (`createItemViaSerializer` / `updateItemViaSerializer` / `ItemSerializer`) all exist in the
  Slice-3 products code (`schema.py::CreateItemViaSerializer` :361, `::UpdateItemViaSerializer` :375,
  `serializers.py::ItemSerializer` :37) — no overclaim. `docs/TREE.md` fills the `rest_framework/` +
  `tests/rest_framework/` lines in BOTH the current-state and target-layout trees, mirroring the
  `forms/` block depth, pinning `serializer_class` / `serializer.errors`; the `planned by
  TODO-ALPHA-039-0.0.13` annotation is dropped. No stale "planned"/"coming soon"/old-version wording
  and no `TODO-ALPHA-039` / `TODO(spec-039` residue in any deliberately-updated file (grep empty).
- **Markdown links — PASS.** The one new cross-file ref-link def `[glossary-serializermutation]:
  docs/GLOSSARY.md#serializermutation` sits under TODAY.md's `<!-- docs/ -->` group (line 388),
  alphabetical between `scalar-field-override-semantics` and `upload-scalar`; inline use is
  `[...][glossary-serializermutation]`. Target file + anchor exist. Convention followed.
- **Verbatim-copy check — N/A.** No text was copied verbatim from the spec into the GLOSSARY entry
  or KANBAN card body. The GLOSSARY body is modeled on the `DjangoModelFormMutation` twin skeleton
  (form→serializer swap) and the status_text matches the spec's pinned phrasing semantically (the
  GLOSSARY render adds backticks around `0.0.13` per its version-rendering convention; the plan
  pinned exactly `"implemented on main, releasing in \`0.0.13\`"`). No verbatim drop-in to diff.
- **Spec slice checklist walk — PASS.** Artifact lines 309-340: parent "Slice 4" `- [x]`,
  "Implemented-on-main docs" `- [x]`, "Card wrap" `- [x]` — all match landed work in the diff. The
  "Joint-cut docs (deferred)" box stays `- [ ]` with its full deferral note inline (joint `0.0.13`
  cut, CHANGELOG only on maintainer prompt) — correct; it is NOT this build's work.

### DB-backed verification

- **Two-consecutive-regenerate byte-stability (the per-slice gate) — PASS.** Ran all three
  regenerators twice from repo root; pass-1 and pass-2 SHA-256 are byte-identical (`diff` of the two
  hash dumps empty). Pass-1 hashes match Worker 2's reported hashes exactly:
  - `docs/GLOSSARY.md` `ec56a5a964c88e6870c93043ac95391f2260e3f31ad9c172e87c3c7dd2cdde3f`
  - `KANBAN.md`        `a16e299f08c0d67635c9fdd76ab05bcfd838fe670e0359b0f52da46dd967dc77`
  - `KANBAN.html`      `4644baf5107e9baf5ba00670d4f955a8822ac24069183dd37ea33a17a8e7584e`
  So the committed render does NOT drift from the DB; the slice's writes regenerate deterministically.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 39 done cards have
  glossary links.` (card 39's links + spec_path mentions match the 38-anchor CSV).
- `uv run python examples/fakeshop/manage.py check` → `System check identified no issues (0 silenced).`

### Static helper

Skipped. Reason: doc / DB-wrap slice — no Python logic added (no new or modified `.py` file in
Slice 4's contribution; the `__init__.py` change is Slice-2-accepted). Per BUILD.md the helper runs
only on `.py` files with review-worthy logic. Nothing to inspect.

### What looks solid

- The F8 split is executed cleanly across all surfaces — the implemented-on-main contract lands
  (TREE, TODAY, GOAL, GLOSSARY body + Public-exports + Index + Mutations row, card → Done) while the
  release-status flip (GLOSSARY `shipped` FK, README Status, docs/README "Shipped today", CHANGELOG)
  is held for the joint cut. The discipline of editing the DB via the ORM and regenerating (never
  hand-editing the rendered markdown) is reflected in the byte-stable re-render.
- The GLOSSARY surface-key non-adoption is phrased as a deliberate design statement ("uses
  `Meta.operation`, not graphene's `model_operations`; ... not a `Meta.lookup_field`"), so a DRF
  migrant reading the entry learns the divergence rather than hitting it.
- TODAY.md's prose names the actual shipped products fields and serializer class, so the capability
  snapshot stays true to the live `/graphql/` surface rather than a planned shape.

### Temp test verification

None used. The verification surface for a doc/DB-wrap slice is the two-regenerate byte-stability +
`import_spec_terms --check` + `manage.py check` (all green above), not pytest. No focused suite run
(optional for a doc slice; the regenerate gate is the real check). No shadow files used.

### Notes for Worker 1 (spec reconciliation)

- Worker 2's two reconciliation carry-forwards are correctly recorded and out-of-scope for this
  review: (1) the spec status-header reconciliation at spec lines 55-56 (`Status: IN PROGRESS — no
  slice built yet`) is Slice-4-owned and is Worker 1's final-verification edit; (2) the deferred
  joint-cut docs sub-box stays `- [ ]` (F8 / Decision 14, joint `0.0.13` cut with card 040). Neither
  is a Slice-4 build defect.
- The `BoardDoc` model-location correction (`apps.kanban.models`, not `apps.glossary.models`) Worker 2
  flagged is a benign small-drift note — the `namespace="glossary", key="public-exports"` lookup is
  correct and the Public-exports bullet renders. No action needed beyond Worker 1's awareness.
- No escalations.

### Review outcome

`review-accepted`. All Documentation/release-sanity checks pass; the F8 split held, the version
invariant holds, the KANBAN card moved to Done exactly once with all 7 DoD items ticked, and the
two-consecutive-regenerate byte-stability gate is green. No High / Medium / Low / DRY findings.

---

## Final verification (Worker 1)

Status: final-accepted

### Spec slice checklist audit (re-audited every `- [x]` against the working-tree diff)

- **Parent "Slice 4" `- [x]` — VERIFIED.** The in-scope sub-boxes (implemented-on-main + card
  wrap) all landed; parent correctly ticked.
- **"Implemented-on-main docs (land now)" `- [x]` — VERIFIED in the diff:**
  - `docs/TREE.md` — the `rest_framework/` + `tests/rest_framework/` summary lines are filled in
    BOTH the current-state tree (lines ~233-238 / ~405-408) and the target-layout tree
    (~316-321 / ~554-557), mirroring the `forms/` depth, pinning `serializer_class` /
    `serializer.errors`. The `planned by TODO-ALPHA-039-0.0.13` annotation is dropped (grep count
    0). The graphene-django REFERENCE tree (~line 50) is correctly untouched.
  - `TODAY.md` — the serializer-flavor capability bullet (line 21) + the "Serializer-backed
    mutations (on main, releasing in `0.0.13`)" paragraph (line 360) name the actual Slice-3 live
    surface (`createItemViaSerializer` / `updateItemViaSerializer` / `ItemSerializer`). No
    `shipped`/`released`-`0.0.13` wording (grep empty); register is "implemented on main /
    releasing in `0.0.13`" only.
  - `docs/GLOSSARY.md` (via DB) — `## SerializerMutation` body reconciled to the implemented
    contract; **`**Status:** implemented on main, releasing in `0.0.13`.`** (line 1247) and the
    Index row (line 142) carry the F8 status_text; the `status` FK stays `planned` (no
    `shipped (0.0.13)` anywhere in GLOSSARY/KANBAN — grep empty). Surface keys reconciled
    (`Meta.operation` not `model_operations`; `id:`-decode locate not `lookup_field`). Public
    exports + Index + Mutations browse row all carry `SerializerMutation`.
  - `GOAL.md` — crit-6 example corrected to `class CreateCategoryFromSerializer(SerializerMutation):`
    with `operation = "create"` in `Meta` + the inline generated-shape comment
    `CategorySerializerInput { name: String! }` (lines 491-495).
- **"Joint-cut docs (deferred to the `0.0.13` release)" stays `- [ ]` — CORRECT (recorded
  deferral).** This is the joint `0.0.13` cut's work shared with `WIP-ALPHA-040-0.0.13` (F8 /
  Decision 14). Confirmed ABSENT from the build diff: no `CHANGELOG.md`, no `README.md`, no
  `docs/README.md` dirty; no `shipped (0.0.13)`; no README Status → `0.0.13`. Deferral reason
  recorded under `### Spec changes made (Worker 1 only)`. Nothing ticked failed to land → no
  un-tick, no `revision-needed`.

### DRY check (doc slice — minimal)

No contradictory wording across GOAL / TODAY / TREE / GLOSSARY. All four describe the serializer
flavor consistently as implemented-on-main, releasing in `0.0.13`, reusing the `FieldError`
envelope and riding the `DjangoMutation` base. No new duplication introduced (Slice 4 adds no
Python logic). The two cross-slice carry-ins (the `relation_field_error` 3-site near-copy; the
`test_inputs.py:620` vacuous tautology) are NOT Slice-4 defects — routed to the integration pass
(see below), unchanged from Worker 3's finding.

### Verification commands (NOT coverage)

- `uv run python examples/fakeshop/manage.py check` → `System check identified no issues (0
  silenced).` PASS.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 39 done cards have
  glossary links.` PASS.
- `uv run pytest examples/fakeshop/apps/kanban/tests --no-cov` → `33 passed` (explicit `--no-cov`;
  the DB card-move broke nothing). PASS.
- Two-consecutive-regenerate byte-stability (re-confirmed): pass-1 == pass-2 SHA-256, matching
  Worker 2's + Worker 3's reported hashes exactly (`KANBAN.md`
  `a16e299f…`, `KANBAN.html` `4644baf5…`, `docs/GLOSSARY.md` `ec56a5a9…`). The committed renders
  match the DB. PASS.
- Version invariant: `pyproject.toml:4` and `__init__.py:37` both `0.0.12` (Decision 14). PASS.

### Spec header reconciliation (the Slice-4-owned spec edit)

Done — see `### Spec changes made (Worker 1 only)`. `check_spec_glossary.py` re-run after the
edits → `OK: 38 terms`, exit 0.

### Carry-ins for the integration pass / `bld-final.md` deferred catalog (NOT fixed here)

1. **`relation_field_error` / `"Invalid id for relation …"` 3-site near-copy → shared ctor.**
   `forms/resolvers.py::_relation_field_error` + `rest_framework/resolvers.py::_relation_field_error`
   byte-identical + `mutations/resolvers.py::_raw_pk_relation_error` (the 036-preexisting third
   site). Spans the 036 model path → route to `bld-integration.md` DRY scan + `bld-final.md`
   deferred catalog.
2. **L1 vacuous-tautology assertion at `tests/rest_framework/test_inputs.py:620`** (UNSET
   singleton → `X or not X`; contract pinned by adjacent lines). Slice-1 carry; both touch
   `tests/rest_framework` → integration pass + deferred catalog.
3. **Board-hygiene observation (out of scope).** Card 39's `planning_state` renders
   "In progress" in KANBAN.md — matches the DONE-038-0.0.12 precedent (also a final-accepted
   card with `planningState: In progress`). NOT a Slice-4 defect (the card-wrap contract is the
   `status` FK `wip → done`, which drove column placement + the `DONE-039-0.0.13` id). Any
   done-card `planning_state` normalization is a separate board-hygiene pass spanning cards
   38 + 39 (and the Planned/Needs-spec done cards) — flag for the joint-cut / integration pass.

### Summary

Slice 4 (the final spec slice) shipped the implemented-on-main documentation + the DB-backed
card wrap, with the release-status flip cleanly deferred to the joint `0.0.13` cut (F8). The F8
split held across every surface: TREE / TODAY / GOAL crit-6 / the GLOSSARY body (status_text
"implemented on main, releasing in `0.0.13`", `status` FK kept `planned`) / Public-exports / Index
/ Mutations row landed now; the GLOSSARY `shipped` flip, README/docs-README "Shipped today", and
CHANGELOG bullets deferred. Card 039 moved to `DONE-039-0.0.13` exactly once (milestone prefix
dropped), all 7 DoD items ticked, with byte-stable regeneration. No version bump (Decision 14);
no CHANGELOG / README Status / docs-README edits crept in. All verification commands pass. No
findings. `Status: final-accepted`.

### Spec changes made (Worker 1 only)

All edits to `docs/spec-039-serializer_mutations-0_0_13.md`; trigger = Slice 4 final verification
(the Slice-4-owned header reconciliation; the spec's status was stale relative to the on-main
implementation). `check_spec_glossary.py --spec …` re-run → `OK: 38 terms`, exit 0.

- **Line 3 (body lead)** — "Planned for `0.0.13` (card `TODO-ALPHA-039-0.0.13`)" → "Implemented on
  main; release deferred to the joint `0.0.13` cut (card `DONE-039-0.0.13`)". Reason: all five
  slices landed on main; the card is Done in the kanban DB. Mirrors the F8 / Decision-14 wording
  ("implemented on main; release deferred to the joint 0.0.13 cut"); does NOT claim "shipped
  0.0.13".
- **Status block (formerly lines 55-56)** — "**IN PROGRESS** — authored … no slice built yet." →
  "**IMPLEMENTED ON MAIN** — all five slices final-accepted and on main; implemented-on-main docs
  + card wrap landed in Slice 4 (`DONE-039-0.0.13`); release deferred to the joint `0.0.13` cut
  shared with `WIP-ALPHA-040-0.0.13`, which owns the version bump + the public release-status flip
  (GLOSSARY `shipped (0.0.13)`, README/docs-README 'Shipped today', CHANGELOG bullets)." Reason:
  the stale "no slice built yet" header is the Slice-4-owned reconciliation carried forward from
  Slices 1-3 (Worker-1-only). Card-id reference within the block updated `TODO-ALPHA-039` →
  `DONE-039` to match the DB.
- **Revision history — new "Revision 10" entry** (appended before `## Key glossary references`).
  Reason: records the Slice-4 final-verification reconciliation (the two header edits above + the
  F8/Decision-14 deferral of the joint-cut release work), per the BUILD.md "update the Revision
  history if appropriate" guidance.

**Deferred (recorded, NOT edited — the verbatim "Joint-cut docs (deferred)" sub-box stays
`- [ ]`):** licensed deferral per F8 / Decision 14 (spec lines ~1046-1050 / ~3338-3345 /
~2663-2671). Target: the joint `0.0.13` cut shared with `WIP-ALPHA-040-0.0.13`; `CHANGELOG.md`
only when the cut's maintainer prompt explicitly requests it (AGENTS.md "Do not update
CHANGELOG.md unless explicitly instructed"). Surfaces deferred: GLOSSARY `shipped (0.0.13)` status
flip (status FK + status_text), `docs/README.md` / `README.md` "Coming next" → "Shipped today"
(README Status → `0.0.13`), `CHANGELOG.md` release bullets. Confirmed none crept into the Slice-4
diff.
