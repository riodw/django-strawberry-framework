# Build: Slice 3 — docs + the `0.0.13` version cut + card wrap

Spec reference: `docs/spec-040-auth_mutations-0_0_13.md` (Slice-3 contract: `## Slice checklist` Slice 3, lines 675-707; release mechanics: `## Doc updates` lines 2522-2557, `### Decision 12` lines 2097-2139, `## Definition of done` item 7 lines 2762-2776)
Status: final-accepted

<!-- Worker 1 spec-reconciliation pass (2026-07-02): resolved the Family-2 step-2f
     import_spec_terms blocker CSV-side (deduped the spec-040 terms CSV to unique
     anchors). Remaining work is Worker 2 running the card-wrap completion (2f sync
     → 2g card-body/DoD ticks → Family-3 regenerates → verification). Status stays
     revision-needed to route Worker 0 → Worker 2. See "## Reconciliation (Worker 1)"
     below. -->


## Plan (Worker 1)

Slice 3 ships **no new resolver logic** — it is docs + the `0.0.13` version cut + the DB-backed kanban card wrap, and it completes the joint `0.0.13` cut spec-039 deferred to this card (Decision 12). Slices 1 and 2 are `final-accepted` (their changes are in the uncommitted working tree). This slice has three work families that must run in a specific order:

1. **File edits** (version quintet minus the DB-generated line, README/docs-README/GOAL/TODAY/CHANGELOG prose, the `build_tree_md.py` script edit, the `tests/rest_framework/__init__.py` render-blocker fix).
2. **DB edits via the ORM** (glossary term flips, BoardDoc version line, card-40 wrap, glossary-link bootstrap + `import_spec_terms` sync).
3. **Regenerate the three DB-backed docs** (`KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`) + regenerate `docs/TREE.md`.

**Sequencing rationale (DB card-wrap vs file edits).** The file edits (family 1) are independent of the DB edits and can land first or interleaved — they never read the DB. The DB edits (family 2) MUST precede the regenerate (family 3), and within family 2 the strict order is: (a) reconcile the two glossary-term bodies/status + the BoardDoc version line, (b) verify/update the card-40 SpecDoc, (c) bootstrap one CardGlossaryTerm so the done-save invariant passes, (d) flip card-40 status to `done` via `.save()`, (e) run `import_spec_terms` to sync the full glossary-link set (this also reconciles 039's stale-path mentions), (f) card-body `CardItem` edits + tick shipped DoD items. Then family 3 regenerates. **The glossary regenerate (family 3) reads the DB written in family 2**, so a hand-edit of `docs/GLOSSARY.md` / `KANBAN.md` / `KANBAN.html` would be silently reverted — every "edit GLOSSARY / KANBAN" is an ORM edit + regenerate, never a markdown hand-edit (BUILD.md "Generated docs are DB-backed"). The `build_tree_md.py` script edit (family 1) must precede the TREE regenerate (family 3).

**Two maintainer decisions folded in (authoritative):**
- **CHANGELOG.md: AUTHORIZED.** The maintainer has explicitly granted the `CHANGELOG.md` edit for this slice (satisfying AGENTS.md #"Do not update CHANGELOG.md unless explicitly instructed" and spec Decision 12's "only when explicitly named in the Slice 3 maintainer prompt"). Slice 3 DOES add the `0.0.13` release bullets for BOTH cards (039 serializer flavor + 040 auth). See Implementation step 5.
- **Pre-existing 039 mention re-key: PROCEED with the standard card-wrap.** `import_spec_terms --check` fails at baseline on card 039 (its `GlossarySpecMention` rows are keyed under the archived `docs/SPECS/spec-039-…` path but the DB rows are empty — VERIFIED at plan time: `--check` reports `GlossarySpecMention rows for docs/SPECS/spec-039-serializer_mutations-0_0_13.md do not match … : [] != [38 anchors]`). The maintainer approved running the standard `import_spec_terms` sync (which reconciles ALL done cards, fixing 039 as a side effect), verifying `--check` passes for every done card afterward, and handing the mixed `db.sqlite3` diff to the maintainer. Worker 2 must VERIFY `--check` passes for ALL done cards post-sync and RECORD (not silently absorb, not partial-fix) any done card OTHER than 040 that stays broken.

### DRY analysis

- **Utils inventory checked.** `django_strawberry_framework/utils/` has no uncommitted changes at plan time (`git status --short django_strawberry_framework/utils/` is empty), so the inventory index is current from the Slice-1/2 passes; refreshing it adds nothing. **No relevant utility candidate applies** — Slice 3 introduces **no new package helper, constant, validation branch, coercion utility, or test helper.** It is docs + a one-line `__version__` string edit + a one-line `test_version` assertion + DB/ORM edits + doc regenerates. The DRY spine here is "reuse the generators, never hand-edit their output": `build_kanban_md.py` / `build_kanban_html.py` / `build_glossary_md.py` / `build_tree_md.py` are the single-sited renderers; the ORM is the single-sited edit surface for KANBAN/GLOSSARY content. Editing a rendered `.md` by hand would duplicate (and then lose) state the DB owns.
- **Existing patterns reused.** The version bump mirrors every prior cut-owning spec: `pyproject.toml:4` `[project].version`, `django_strawberry_framework/__init__.py:37` `__version__`, `tests/base/test_init.py:19` `test_version`, `uv.lock:218` (the `name = "django-strawberry-framework"` block). The GLOSSARY version line is DB-generated (see below). The doc-flip prose reuses the sibling cards' existing wording shapes (README "Shipped today" list, docs/README "Shipped today" / "Coming next" split, TODAY "Shipped package capabilities not exercised by products", GOAL fakeshop paragraph). The card-wrap reuses the DB-backed move procedure verbatim (worker-0.md "Closing out a kanban card" / BUILD.md L112-114 / task prompt).
- **New helpers justified.** None. If a temptation arises to write a one-off script to bump the version quintet, reject it — five targeted edits + one BoardDoc ORM edit is lower-risk than a new script.
- **Duplication risk avoided.** (1) The version string appears in FIVE source-side places PLUS the DB BoardDoc; the naive risk is editing four and missing one. The plan enumerates all six precisely (four source files + `uv.lock` + the `kanban.BoardDoc` pk=40 body). (2) The naive risk of hand-editing `docs/GLOSSARY.md` / `KANBAN.md` for the term-status/version/card flips — avoided by the ORM-then-regenerate discipline. (3) The CHANGELOG uses reference-style links with a unified bottom block; the naive risk is inline `](path)` links or a missing ref def — avoided by using existing refs and adding any new ref to the correct alphabetical group.

### Static inspection helper

**Skipped — recorded with reason (agreed).** Slice 3 touches no package `.py` logic beyond the one-line `__version__` string edit in `__init__.py` and the one-line `0.0.13` assertion in `tests/base/test_init.py::test_version`. BUILD.md mandates the helper only when a plan adds ≥30 lines of logic to a package file, adds logic to `optimizer/` or `types/`, or adds a new `.py` file — none apply. The helper parses AST/text and adds no value for a string-literal edit. Skip recorded per BUILD.md L438.

### Implementation steps

Worker 2 owns all source/test/script/DB edits and the regenerates. Line numbers are pin-at-write-time hints — verify against current source before editing.

**Family 1 — file edits (no DB reads; can land first).**

1. **Version quintet, four source-side members `0.0.12` → `0.0.13`:**
   - `pyproject.toml:4` — `version = "0.0.12"` → `"0.0.13"`.
   - `django_strawberry_framework/__init__.py:37` — `__version__ = "0.0.12"` → `"0.0.13"`.
   - `tests/base/test_init.py:19` — `assert __version__ == "0.0.12"` → `"0.0.13"` (this is the ONLY test that changes in Slice 3). The stale explanatory comment at `test_init.py:49-50` ("`0.0.12` card it owns the `0.0.12` cut (Decision 14), so `test_version` is asserted at `0.0.12` above") references the 038 cut and should be updated to name the 040 `0.0.13` cut so the comment does not lie; this is a Worker-2 comment refresh in the same edit (Low-risk, but leaving it stale would be a documentation defect this slice deliberately touches).
   - `uv.lock:218` — the `version = "0.0.12"` inside the `[[package]]` block whose `name = "django-strawberry-framework"` (block header at `uv.lock:217`) → `"0.0.13"`. Edit ONLY that block's version; do not touch other packages' pins.
   - **The fifth quintet member — the `docs/GLOSSARY.md` package-version line — is DB-generated; see Family 2 step 2b. Do NOT hand-edit `docs/GLOSSARY.md:20`.**
   - **`tests/base/test_init.py` `__all__` public-surface assertion needs NO change** (Slices 1/2 added no package-root exports — auth symbols are submodule-only per Decision 3). Named here so it is not missed; leave the `__all__` tuple assertion (`test_init.py:51+`) untouched.

2. **`tests/rest_framework/__init__.py` render-blocker fix (spec-reconciliation item — see Notes for Worker 1).** VERIFIED at plan time: `scripts/build_tree_md.py --check` currently fails with `TreeRenderError: tests/rest_framework/__init__.py is missing a module docstring` — its first line is a `#` comment (`# Package for spec-039 package-internal DRF serializer-mutation tests.`) not a `"""docstring"""`. `build_tree_md.py::python_docstring` (L142-143) raises if a walked module (or folder `__init__.py` read by `folder_description`) lacks a docstring. The TREE regenerate (Family 3) CANNOT pass until this is a real docstring. Convert the `#` comment to a module docstring, e.g. `"""Package-internal DRF serializer-mutation tests (spec-039)."""`. This is a `tests/` file (Worker 2 territory). It is a pre-existing HEAD blocker introduced by the Done 039 work, but AGENTS.md's "shipped behavior folds into `docs/TREE.md`" makes clearing the render blocker this slice's obligation since Slice 3 owns the TREE regenerate. **This is the ONLY `.py` docstring gap that blocks the TREE render** — verified: every other render-walked non-`__init__` `.py` file under the package, `tests/`, `test_query/`, `examples/fakeshop/tests/`, and `examples/fakeshop/apps/products/` carries a module docstring, and the new `auth/` + `tests/auth/` + `accounts/__init__.py` + `test_auth_api.py` files all carry docstrings. `accounts/apps.py` and `accounts/schema.py` lack no-op-relevant docstrings ONLY where walked — the fakeshop project tree walks files for `products` alone (`build_tree_md.py::render_fakeshop_project_tree` `if entry == "products"`), so accounts' non-`__init__` files are NOT walked and their docstring status is irrelevant to the render (`accounts/apps.py` has no module docstring and that is FINE).

3. **`scripts/build_tree_md.py` script edit — add `accounts` to the fakeshop app list.** VERIFIED: `FAKESHOP_APP_NAMES` (`build_tree_md.py:37-43`) is a hardcoded tuple `("glossary", "kanban", "library", "products", "scalars")` that does NOT include `accounts`. Add `"accounts"` in alphabetical position (first). This makes the `accounts` app appear in the fakeshop project tree (as a directory-only row, since only `products` walks its children) AND surfaces its `accounts/__init__.py` docstring paragraph in the "App roles" section (`render_fakeshop_app_details`). This is a **script edit, not a doc hand-edit** — TREE.md is script-rendered; the row lands via the regenerate in Family 3. Without this edit the `accounts` app never appears in TREE.md, failing the Slice-3 checkbox "`docs/TREE.md` gains … the fakeshop `accounts` app".
   - The `auth/` package rows, `tests/auth/` tree, and `test_auth_api.py` row require NO script edit — they render automatically from the filesystem walk (`render_package_tree` / `render_tree(REPO_ROOT / "tests")` / the `test_query/` render) once TREE is regenerated. Their appearance is the "closing the target-layout gap" the Slice-3 checklist names.

4. **README.md + docs/README.md — "Coming next" → "Shipped today" + Status → `0.0.13`.**
   - `README.md:59-61` **Status** section: `**0.0.12**` → `**0.0.13**`, and the "Newest shipped surface:" prose (currently form-based mutations) updates to name the newest-shipped surface for `0.0.13` (the serializer flavor + the auth surface). `README.md:57` "A DRF-serializer flavor via `Meta.serializer_class` follows in `0.0.13`" reads as future — update to shipped (or fold into the Status prose). Keep the edit coherent with what shipped; do not overstate.
   - `docs/README.md:97` "**Shipped today** (`0.0.12`)" → (`0.0.13`); ADD two bullets under "Shipped today" for the serializer flavor (`SerializerMutation` via `Meta.serializer_class`) and the auth surface (`login` / `logout` / `register` / `current_user`, opt-in submodule import). `docs/README.md:127-128` "**Coming next … (`0.0.13` → `0.0.14`)**" — REMOVE the `0.0.13` line (both features now shipped) and keep only the `0.0.14` line. Use the existing "Shipped today" bullet shape; reuse the GLOSSARY link refs already in the docs/README bottom block (add `[glossary-serializermutation]` / `[glossary-auth-mutations]` refs to the `<!-- docs/ -->` group if not present, alphabetical).

5. **CHANGELOG.md — the `0.0.13` release bullets for BOTH cards (AUTHORIZED by maintainer).**
   - Add a new `## [0.0.13] - 2026-07-02` section at the top of the version history — AFTER the `## Versioning` block, BEFORE `## [0.0.12] - 2026-06-23` (CHANGELOG.md:19). There is currently NO `[0.0.13]` or `[Unreleased]` section (verified).
   - Use only the `### Added` / `### Changed` headings the spec authorizes. Canonical content:
     - `### Added`: (a) **DRF serializer-based mutations — `SerializerMutation`** (the 039 flavor: `Meta.serializer_class` over a DRF `Serializer` / `ModelSerializer`, riding `DjangoMutation`, reusing the frozen `FieldError` envelope; soft DRF dependency, lazy root `__getattr__` export never in `__all__`). (b) **Session-auth mutations — `login_mutation` / `logout_mutation` / `register_mutation` + the `current_user` query helper** in an opt-in `django_strawberry_framework/auth/` module (submodule import only, **no** package-root re-export; the AllowAny default as the documented inversion of the family's deny-by-default; the shared `FieldError` envelope; `register` a `DjangoMutation` rider with `validate_password` + `set_password`; session-transport constraints, no Channels).
     - `### Changed`: `django_strawberry_framework.__version__` is now `0.0.13`. (Match the prior versions' one-line `__version__` bullet shape at CHANGELOG.md:28 / :45.)
   - The version line MUST match `pyproject.toml` / `__init__.py` (`0.0.13`) — Worker-3 CHANGELOG-sanity check applies.
   - Reference-style links: reuse existing refs (`[glossary-fielderror-envelope]`, `[glossary-djangomutation]`, `[glossary-djangomutationfield]`, `[glossary-djangomodelpermission]`, `[glossary-configurationerror]`, `[glossary-syncmisuseerror]` all EXIST in the CHANGELOG bottom block). ADD any new ref used (`[glossary-serializermutation]`, `[glossary-auth-mutations]`) to the `<!-- docs/ -->` group alphabetically. Do NOT introduce inline `](path)` links.

6. **GOAL.md — fakeshop auth wording future → shipped.** `GOAL.md:535` — in the Fakeshop paragraph, "auth mutations exercised by the existing test users" is listed among growth-direction items ("into the full Relay-shaped showcase: … auth mutations exercised by the existing test users; …"). Flip that clause from a future/growth item to a shipped statement (the fakeshop `accounts` app now ships it). Keep the neighboring unshipped items (aggregate/fieldset/search sidecars, ModelSerializer already shipping in `0.0.13`, sharded stress) accurate. Also `GOAL.md:490` "# Coming in 0.0.13 — the DRF-serializer flavor" and `GOAL.md:513` "only the `ModelSerializer` (`0.0.13`) flavor still lands later" / `GOAL.md:458` "lands in `0.0.13`" read as future for the serializer flavor — update to shipped-in-`0.0.13` phrasing consistent with the release. Keep to what the spec authorizes; leave unrelated prose alone.

7. **TODAY.md — serializer wording → shipped; auth noted under capabilities-not-exercised.**
   - `TODAY.md:21` and `TODAY.md:360` — "implemented on main (releasing in `0.0.13`)" / "on main, releasing in `0.0.13`" for the serializer surface → shipped `0.0.13` wording (drop "releasing in").
   - Add an auth entry under "## Shipped package capabilities not exercised by products" (`TODAY.md:370`) — a bullet noting the shipped auth surface (`login` / `logout` / `register` / `current_user`) is demonstrated by the fakeshop **`accounts`** app (products stays the canonical vehicle — the file's own scope rule; the accounts app is the live demonstration). Point at `docs/GLOSSARY.md#auth-mutations`. Add the `[glossary-auth-mutations]` ref to TODAY.md's bottom `<!-- docs/ -->` group if not present.

**Family 2 — DB edits via the ORM (run via `uv run python examples/fakeshop/manage.py shell`; MUST precede Family 3).**

PRE-VERIFIED DB state at plan time (Worker 2 re-verifies before editing):
- Card 40: `number=40`, `status.key=wip`, `glossary_links.count()=0`, title "Auth mutations (login / logout / register)".
- A `SpecDoc` for card 40 ALREADY EXISTS: name `spec-040-auth_mutations-0_0_13`, url `https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-040-auth_mutations-0_0_13.md`, linked to card 40's row. → **UPDATE/verify, do NOT `.create()`** (name is unique → a create collides).
- All 30 spec-040 `-terms.csv` distinct anchors already exist as `GlossaryTerm` rows → **NO net-new GlossaryTerm seeding needed.**
- `auth-mutations` `GlossaryTerm`: `status.key=planned`, `status_text="planned for \`0.0.13\`"`. `serializermutation` `GlossaryTerm`: `status.key=planned`, `status_text="implemented on main, releasing in \`0.0.13\`"`.
- The GLOSSARY "Current package version: `0.0.12`" line lives in `kanban.BoardDoc` pk=40 (`namespace='glossary'`, `key='status-legend'`, title "Status legend") — pulled into the glossary render via `allGlossaryDocuments`. This is the DB-backed source of the fifth quintet member.
- `done` `Status` row exists.

2a. **Reconcile the two glossary-term flips (DB status change → regenerate later).**
   - `auth-mutations` `GlossaryTerm`: set `status` to the `shipped (0.0.13)` `GlossaryStatus` (match the exact status row prior shipped terms use — resolve it by `key`, do NOT invent a new status row) and set `status_text` to the shipped form (e.g. `shipped (0.0.13)`). Update `body` to the implemented contract per spec `## Doc updates`: the four factories, the submodule-only import path, the AllowAny default + rationale, the envelope semantics, the no-Channels constraint, and the **`UserType`-selection caution** (the user type's field selection is the authenticated read surface — exclude `password` and privilege columns). Reconciling the body here (not just status) prevents the regenerate from reverting shipped doc content that the build hand-edited elsewhere.
   - `serializermutation` `GlossaryTerm`: set `status` → `shipped (0.0.13)` and `status_text` "implemented on main, releasing in `0.0.13`" → `shipped (0.0.13)`. (The 039-deferred flip.) Update `body` only insofar as the committed `docs/GLOSSARY.md` serializer entry body diverges from the DB — sync so the regenerate does not revert shipped content.
   - Update the GLOSSARY **Index rows** for both terms (the Index status column renders from the term status, so flipping status handles it automatically — verify after regenerate). Add the **submodule-exports note beside the `testing` note** (auth symbols are NOT root exports, Decision 3): this is a body/document edit in whatever glossary document carries the exports note — locate the note (likely a `BoardDoc` in the `glossary` namespace) and add the auth-submodule sentence via ORM.

2b. **BoardDoc version-line bump (the DB-generated fifth quintet member).** Edit `kanban.BoardDoc` pk=40 (`namespace='glossary'`, `key='status-legend'`) body: `Current package version: \`0.0.12\`` → `\`0.0.13\``. Via ORM `.save()` (a raw SQL update would skip the `post_save` UUID side-row the GraphQL render needs). This lands the GLOSSARY version line at regenerate.

2c. **Card-40 SpecDoc — UPDATE/verify (do NOT create).** Confirm the existing SpecDoc row (name `spec-040-auth_mutations-0_0_13`) is linked to card 40 and its url points at `docs/spec-040-auth_mutations-0_0_13.md` (the spec stays at its working `docs/` location — it is NOT archived to `docs/SPECS/` by this build; archival is the NEXT spec author's Step 8 job). No change expected; verify only.

2d. **Bootstrap ≥1 glossary link.** Create ONE `CardGlossaryTerm` for card 40 pointing at a term in the spec-040 CSV (e.g. the `auth-mutations` anchor) so the done-save invariant (`examples/fakeshop/apps/kanban/signals.py`: a `done` card needs ≥1 `CardGlossaryTerm`) passes. `import_spec_terms` (step 2f) reconciles the full set next.

2e. **Flip status to done.** `card = Card.objects.get(number=40); card.status = Status.objects.get(key="done"); card.save()`. The ORM `.save()` fires the pre_save validation (requires the linked SpecDoc [2c] + ≥1 CardGlossaryTerm [2d]) and sets `milestone_id`; the rendered id auto-becomes `DONE-040-0.0.13`.

2f. **Sync the full glossary-link set + reconcile 039.** `uv run python examples/fakeshop/manage.py import_spec_terms` (NO `--check` — the real sync). This processes EVERY done card, creating `CardGlossaryTerm` + `GlossarySpecMention` rows from each card's `-terms.csv` — this is what reconciles card 039's stale-path mentions as a side effect (maintainer decision #2). **`import_spec_terms` requires every anchor in a card's `-terms.csv` to already exist as a `GlossaryTerm` row** — VERIFIED true for all 30 spec-040 anchors, so no seeding gate blocks it. NOTE: `check_spec_glossary` allows many-terms→one-anchor, but `import_spec_terms` (done cards) requires unique anchors + a `GlossaryTerm` per anchor; the spec-040 CSV has 30 distinct anchors across 128 rows (many term→same-anchor rows), all backed — confirmed importable.

2g. **Card-body content edits (`CardItem.text`) + tick shipped DoD items.** Per the spec wrap: fix any stale spec-filename refs in the card body, `## [0.0.X]` → `[Unreleased]` residue if present, and mark every **shipped** `definition_of_done` `CardItem.is_complete = True`. Keep to what the spec authorizes; leave unrelated prose alone. (Card-id refs in prose are FK-backed `{{card_ref:N}}` placeholders per worker-1 memory — do NOT rewrite those as bare numbers.)

**Family 3 — regenerate (reads the Family-2 DB; run from repo root).**

3a. `uv run python scripts/build_kanban_md.py` — regenerates `KANBAN.md`.
3b. `uv run python scripts/build_kanban_html.py` — regenerates `KANBAN.html`.
3c. `uv run python scripts/build_glossary_md.py` — regenerates `docs/GLOSSARY.md` (picks up the two term flips, the version line, the submodule-exports note).
3d. `uv run python scripts/build_tree_md.py` — regenerates `docs/TREE.md` (picks up `auth/`, `tests/auth/`, `test_auth_api.py` from the filesystem walk + the `accounts` app from the `FAKESHOP_APP_NAMES` script edit). Requires step 2-fix (`tests/rest_framework/__init__.py` docstring) to have landed or it raises `TreeRenderError`.

### Verification (Worker 2 records; Worker 1 re-checks at final verification)

- `uv run python examples/fakeshop/manage.py import_spec_terms --check` reports **OK for ALL done cards** (incl. 039 AND 040). RECORD (do not silently absorb) any done card OTHER than 040 that stays broken post-sync.
- **GLOSSARY / KANBAN regenerate stability via TWO CONSECUTIVE regenerates:** hash `docs/GLOSSARY.md` (and `KANBAN.md`) after a first regenerate, regenerate a second time, hash again — the two hashes must be byte-identical. A plain `git diff` is NOT the test here (the DB has legitimately diverged for the card move; git diff shows cumulative HEAD drift, not second-regenerate stability — BUILD.md L84).
- `KANBAN.md` shows `DONE-040-0.0.13` in the Done section (removed from WIP, appearing in Done exactly once) with its DoD items ticked.
- `docs/TREE.md` shows `auth/` package rows, the `tests/auth/` tree, the fakeshop `accounts` app, and `test_auth_api.py`; `uv run python scripts/build_tree_md.py --check` exits 0 after the regenerate.
- `uv run python examples/fakeshop/manage.py check` passes.
- `uv run ruff format .` + `uv run ruff check --fix .` clean on the touched source/test/script files (the doc `.md` files and the DB are not ruff targets; `build_tree_md.py` and the two edited `.py` test/init files are).

### Test additions / updates

- `tests/base/test_init.py::test_version` — the ONLY test that changes: `assert __version__ == "0.0.13"`. Pin the assertion shape exactly. No new resolver tests (Slice 3 adds no logic).
- `tests/base/test_init.py` `__all__` assertion — UNCHANGED (no new package-root exports; auth is submodule-only). Named so Worker 3 confirms the diff does NOT touch it.
- No new tests under `tests/auth/`, `test_query/`, or elsewhere — Slice 3 ships no new logic.

### Implementation discretion items

- **CHANGELOG bullet wording granularity.** The exact prose of the two `### Added` bullets is at Worker 2's discretion within the canonical content pinned in step 5 (name both cards, the frozen envelope reuse, the AllowAny inversion, the submodule-only import, the soft-DRF/lazy-export note for serializer) — as long as nothing overstates/understates and the version line matches the quintet. Prefer coherence with the `0.0.11`/`0.0.12` bullet voice.
- **Which term the bootstrap `CardGlossaryTerm` (step 2d) points at.** Any anchor in the spec-040 CSV is acceptable; `auth-mutations` is the natural choice. `import_spec_terms` reconciles the full set regardless.
- **The precise phrasing of the shipped `auth-mutations` GLOSSARY body** — Worker 2 writes the implemented contract; it must include the six pinned elements (four factories, submodule-only import, AllowAny default + rationale, envelope semantics, no-Channels constraint, UserType-selection caution) but the sentence structure is at discretion.

### Spec slice checklist (verbatim)

- [x] **Slice 3 — docs + the `0.0.13` version cut + card wrap**
  - [x] The version quintet moves `0.0.12` → `0.0.13`: [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init], [`tests/base/test_init.py::test_version`][test-base-init], the [`docs/GLOSSARY.md`][glossary] package-version line, and the `django-strawberry-framework` `version` entry inside `uv.lock` ([Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)).
  - [x] The `039`-deferred joint-cut release flips land: the GLOSSARY [`SerializerMutation`][glossary-serializermutation] status → `shipped (0.0.13)`; [`docs/README.md`][docs-readme] / [`README.md`][readme] move the serializer flavor **and** the auth surface from "Coming next (`0.0.13`)" to "Shipped today" (README **Status** → `0.0.13`); [`CHANGELOG.md`][changelog] carries the `0.0.13` release bullets for both cards — **only when the maintainer prompt explicitly requests the `CHANGELOG.md` edit**.
  - [x] [Auth mutations][glossary-auth-mutations] GLOSSARY entry flips to `shipped (0.0.13)` with the implemented contract (the four factories, the submodule-only import path, the AllowAny default and its rationale, the envelope semantics); the Index row updates; a submodule-exports note is added beside the `testing` note (auth symbols are **not** root exports, [Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)).
  - [x] [`docs/TREE.md`][tree] gains the `auth/` package rows, the `tests/auth/` tree, the fakeshop `accounts` app, and the live `test_auth_api.py` row (closing the target-layout gap recorded in [Risks](#risks-and-open-questions)); [`TODAY.md`][today] notes the shipped auth surface under its capabilities-not-exercised-by-products section (the `accounts` app owns the live demonstration); [`GOAL.md`][goal]'s fakeshop paragraph flips "auth mutations exercised by the existing test users" from future to shipped.
  - [x] [`KANBAN.md`][kanban] card wrap: `WIP-ALPHA-040-0.0.13` → Done with the next `DONE-040-0.0.13` id and its `SpecDoc` pointing at this spec (kanban DB edit + `scripts/build_kanban_md.py` / `build_kanban_html.py` re-render, never a hand-edit).

---

## Build report (Worker 2)

**PAUSED — structural blocker in Family-2 step 2f (`import_spec_terms`).** The
plan's card-wrap sync cannot run: the spec-040 terms CSV has genuine duplicate
anchors and `import_spec_terms._load_rows` raises on the first one. This is
plan-vs-implementation **structural drift** (the plan asserted the CSV was
"confirmed importable"; it is not — it needs a Worker-1 architectural call on
which of two root-cause fixes to take). Per `worker-2.md` "Structural drift" I did
NOT decide unilaterally: I left the DB in its coherent partial-wrap state (do NOT
revert — the term flips + version-line bump + card done-flip are correct slice
output), did NOT run the Family-3 regenerates (they would emit throwaway output
against a half-wrapped card whose glossary-link set will change once the sync
runs), recorded the blocker below and in `### Notes for Worker 1 (spec
reconciliation)`, and set `Status: revision-needed`. Everything NOT dependent on
`import_spec_terms` landed (Family-1 file edits + Family-2 steps 2a–2e).

### Files touched

**Family 1 — source / test / script file edits (all landed, ruff-clean):**

- `pyproject.toml` — `[project].version` `0.0.12` → `0.0.13` (quintet member 1).
- `django_strawberry_framework/__init__.py` — `__version__` `0.0.12` → `0.0.13`
  (quintet member 2). No `__all__` / re-export change (auth is submodule-only,
  Decision 3).
- `tests/base/test_init.py` — `test_version` assertion `0.0.12` → `0.0.13`
  (quintet member 3); refreshed the stale `test_public_api_surface_is_pinned`
  comment (was describing the spec-038 `0.0.12` cut) to name the spec-040 `0.0.13`
  joint cut and state `__all__` is unchanged. The `__all__` tuple assertion itself
  is UNTOUCHED.
- `uv.lock` — the `version = "0.0.12"` → `"0.0.13"` inside the
  `name = "django-strawberry-framework"` `[[package]]` block only (quintet
  member 4). No other package pin touched.
- `tests/rest_framework/__init__.py` — converted the leading `#` comment to a
  `"""docstring"""` (TREE render-blocker fix; `build_tree_md.py --check` was
  raising `TreeRenderError` on this file at baseline).
- `scripts/build_tree_md.py` — added `"accounts"` to `FAKESHOP_APP_NAMES` (first,
  alphabetical) so the fakeshop `accounts` app renders in TREE.md.
- `README.md` — Status version `0.0.12` → `0.0.13`; rewrote the "Newest shipped
  surface" prose to lead with the `0.0.13` serializer + session-auth surfaces; the
  line-57 "A DRF-serializer flavor … follows in `0.0.13`" future clause updated to
  name both `0.0.13` surfaces as shipping.
- `docs/README.md` — "Shipped today" header `0.0.12` → `0.0.13`; added two
  "Shipped today" bullets (serializer flavor + session-auth surface); removed the
  `0.0.13` line from "Coming next" (now only `0.0.14`); added
  `[glossary-serializermutation]` / `[glossary-auth-mutations]` refs to the
  `<!-- docs/ -->` bottom group (alphabetical).
- `CHANGELOG.md` — **AUTHORIZED by maintainer.** New `## [0.0.13] - 2026-07-02`
  section (after `## Versioning`, before `## [0.0.12]`) with `### Added` bullets for
  BOTH cards (039 `SerializerMutation` + 040 session-auth) and `### Changed`
  `__version__` is now `0.0.13`. Version line matches the quintet. Added
  `[glossary-auth-mutations]` / `[glossary-serializermutation]` refs to the
  `<!-- docs/ -->` bottom group (alphabetical); reused all pre-existing glossary
  refs; no inline `](path)` links introduced.
- `GOAL.md` — the "Coming from DRF + django-filter" serializer clause + the code
  comment + the success-criteria item 6 flipped from future to shipped-in-`0.0.13`;
  the Fakeshop target paragraph moved "auth mutations exercised by the existing
  test users" (and the `ModelSerializer` flavor) out of the growth-direction list
  into a shipped statement naming the `accounts` app.
- `TODAY.md` — the two serializer surfaces dropped "releasing in `0.0.13`" for
  shipped wording; added a "Session-auth mutations (shipped `0.0.13`)" bullet under
  "Shipped package capabilities not exercised by products" pointing at the
  `accounts` app + `test_auth_api.py` and `docs/GLOSSARY.md#auth-mutations`; added
  the `[glossary-auth-mutations]` ref to the bottom group.

**Family 2 — DB edits via the ORM (`examples/fakeshop/db.sqlite3`; steps 2a–2e
landed, 2f BLOCKED, 2g not started):**

- `examples/fakeshop/db.sqlite3` — **slice-intended generated/binary divergence, do
  NOT revert.** Applied via `manage.py shell` (ORM `.save()`, never raw SQL):
  - 2a: `auth-mutations` `GlossaryTerm` → status `shipped`, `status_text`
    `` shipped (`0.0.13`) ``, body rewritten to the implemented contract (the four
    factories + factory idiom, submodule-only import + absent-from-`__all__`,
    AllowAny default + rationale, shared `FieldError` envelope semantics + register
    password-hashing, session-only/no-Channels constraint, and the
    `UserType`-selection caution). `serializermutation` `GlossaryTerm` → status
    `shipped`, `status_text` `` shipped (`0.0.13`) `` (body already byte-matched the
    rendered entry; content is version-agnostic, so status/status_text only).
    Added an "`django_strawberry_framework.auth` submodule" exports section to the
    `glossary`/`public-exports` `BoardDoc` (pk=41), inserted **beside** the
    `testing` note (after the testing list, before the trailing `_Note:_`).
  - 2b: `glossary`/`status-legend` `BoardDoc` (pk=40) body version line
    `` Current package version: `0.0.12`. `` → `` `0.0.13`. `` (the DB-generated
    fifth quintet member).
  - 2c: verified (no create) card-40 `SpecDoc` (`spec-040-auth_mutations-0_0_13`,
    url → `docs/spec-040-auth_mutations-0_0_13.md`) is linked to card 40.
  - 2d: bootstrapped one `CardGlossaryTerm` (card 40 → `auth-mutations`, order 0)
    to satisfy the done-save `>=1 glossary link` invariant.
  - 2e: `card.status = Status(key="done"); card.save()` → card renders
    `DONE-040-0.0.13`, `milestone` segment dropped as expected. `manage.py check`
    passes; DB is coherent (not corrupted).
  - 2f: **BLOCKED** — see the blocker note above and Notes for Worker 1.
  - 2g: **NOT STARTED** — the card-body / DoD `CardItem` ticks assume the wrap
    completed; deferred behind 2f.

**Family 3 — regenerates: NOT RUN** (blocked behind 2f). `KANBAN.md`,
`KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md` are therefore UNCHANGED in the
working tree — regenerating now would produce throwaway output against a
half-wrapped card. The `build_tree_md.py` script edit + the
`tests/rest_framework/__init__.py` docstring fix (the two TREE render blockers) DID
land, so the TREE regenerate is unblocked and ready to run in the re-pass once 2f
is resolved.

### Tests added or updated

- `tests/base/test_init.py::test_version` — assertion flipped to
  `assert __version__ == "0.0.13"` (the ONLY test change in Slice 3). Focused run
  below: 5 passed (incl. `test_version` and `test_public_api_surface_is_pinned`,
  which confirms `__all__` is unchanged).
- No new tests (Slice 3 ships no new logic).

### Validation run

- `uv run ruff format .` — pass (308 files left unchanged; the COM812/formatter
  warning is the standing pre-existing config warning, not from this slice).
- `uv run ruff check --fix .` — pass (All checks passed!).
- `uv run python scripts/check_trailing_commas.py --check scripts/build_tree_md.py
  tests/base/test_init.py tests/rest_framework/__init__.py` — pass (no output). The
  `FAKESHOP_APP_NAMES` tuple went 5 → 6 items and stays correctly one-per-line with
  a trailing comma.
- `uv run pytest tests/base/test_init.py --no-cov -q` — **5 passed** (no `--cov`
  flags).
- `uv run python examples/fakeshop/manage.py check` — pass (0 issues), confirming
  the partial DB wrap did not corrupt anything.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` — **FAILS**
  (`CommandError: Duplicate glossary anchor 'auth-mutations' in …spec-040-…-terms.csv`).
  This is the blocker; it fails during `_plan_done_cards` → `_load_rows` on card 40
  now that card 40 is `done`. At baseline (before the done-flip) `--check` failed
  instead on card 039's stale `docs/SPECS/` mention path (the maintainer-decision-#2
  re-key target) — that 039 failure is expected to be reconciled by the same sync
  once it can run.
- **Two-consecutive-regenerate byte-stability + `DONE-040` in KANBAN Done + TREE
  `--check` = 0 + `makemigrations --check`** — NOT RUN (all downstream of the
  blocked regenerate; deferred to the re-pass).
- `git status --short` classification: my slice-intended files are the 5 doc prose
  files (`CHANGELOG.md`, `GOAL.md`, `README.md`, `TODAY.md`, `docs/README.md`), the
  4 source-side quintet members (`pyproject.toml`,
  `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `uv.lock`),
  the 2 TREE-render fixes (`scripts/build_tree_md.py`,
  `tests/rest_framework/__init__.py`), and the slice-intended
  `examples/fakeshop/db.sqlite3` divergence. NOT my churn (left untouched per the
  task's Hard rules): the Slice-1/2 already-modified auth/mutations source
  (`django_strawberry_framework/auth/{mutations,queries}.py`,
  `mutations/{fields,resolvers}.py`, `registry.py`, `types/finalizer.py`,
  `examples/fakeshop/apps/accounts/schema.py`, `config/{schema,settings}.py`,
  `schema_reload.py`, `test_query/test_auth_api.py`, `tests/auth/*`), the modified
  spec (`docs/spec-040-…md`, Worker 1), the 8 `D` prior-039-cycle artifact
  deletions, and the untracked `build-040-*` plan + 3 `bld-slice-*` artifacts. No
  unrelated tool churn to revert. `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` /
  `docs/TREE.md` are correctly ABSENT from the dirty set (regenerates not run).

### Implementation notes

- **Shipped status is `status.key="shipped"` + version-tagged `status_text`, NOT a
  separate `shipped (0.0.13)` status row.** The `GlossaryStatus` table has exactly
  two rows (`shipped`, `planned`); every version-specific shipped term (e.g.
  `djangoformmutation`) uses `status=shipped` with `status_text` = `` shipped
  (`0.0.12`) ``. I matched that convention exactly (`` shipped (`0.0.13`) ``) rather
  than inventing a status row — the plan's "`shipped (0.0.13)` GlossaryStatus"
  phrasing is the `status_text` label, not a new lookup row. The GLOSSARY Index
  status column renders from term status, so the flip handles the Index row
  automatically (to be verified after the eventual regenerate).
- **Exports note placement.** Inserted the auth-submodule section into the
  `public-exports` `BoardDoc` body between the `testing`-subpackage list and the
  trailing `_Note:_` paragraph (idempotent guard on the
  `django_strawberry_framework.auth` marker), so it reads "beside the testing note"
  as the plan/spec require, using `[…](#auth-mutations)` in-page anchors.
- **`serializermutation` body left unchanged.** Its DB body byte-matches the
  currently-rendered `docs/GLOSSARY.md` entry and is version-agnostic prose, so only
  status/status_text changed (per the plan's "sync body only insofar as it
  diverges" — it does not diverge).
- **DB left in partial-wrap state on purpose.** The card-40 done-flip and term
  flips are correct regardless of which CSV/importer fix Worker 1 picks, so
  reverting them would only force a re-do; per BUILD.md L84 the DB legitimately
  diverges on a card move and is not revertible "tool drift."

### Notes for Worker 3

- Nothing to review yet beyond the Family-1 file diffs — the slice is `revision-needed`
  pending Worker 1's structural decision (see below). If re-dispatched to review
  after the re-pass, the regenerated `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md`
  / `docs/TREE.md` and the completed card-wrap will be part of that later diff.
- Static inspection helper: skipped per the Plan (no package `.py` logic beyond the
  one-line `__version__` string edit; `build_tree_md.py` gained one tuple element).
- No shadow files used.

### Notes for Worker 1 (spec reconciliation)

**STRUCTURAL DRIFT — blocks the card-wrap (Family-2 step 2f). Requires a Worker-1
architectural decision before the slice can complete.**

The plan (Family-2 step 2f + DRY analysis + the task prompt) asserts the spec-040
terms CSV is "confirmed importable" by `import_spec_terms` — "30 distinct anchors
across 128 rows (many term→same-anchor rows), all backed." **It is not importable.**
`import_spec_terms._load_rows`
(`examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py`
#"Duplicate glossary anchor") raises `CommandError` on the FIRST duplicate anchor
within a single card's CSV:

```
CommandError: Duplicate glossary anchor 'auth-mutations' in
  docs/spec-040-auth_mutations-0_0_13-terms.csv
```

Verified facts (proper CSV parse, quoted-comma-safe):

- `docs/spec-040-auth_mutations-0_0_13-terms.csv`: 127 data rows, all with non-empty
  term+anchor, but only **30 distinct anchors** — **12 anchors are duplicated**
  (`auth-mutations`×22, `djangomutation`×26, `djangomodelpermission`×10,
  `finalize_django_types`×12, `input-type-generation`×10, `fielderror-envelope`×9,
  `get_queryset-visibility-hook`×5, `syncmisuseerror`×4, `djangomutationfield`×4,
  `metaprimary`×3, `djangooptimizerextension`×2, `djangoformmutation`×2). The many
  rows map distinct spec SYMBOLS (`login_mutation`, `LoginPayload`,
  `bind_auth_mutations`, …) onto a shared documented anchor.
- **spec-040 is the ONLY terms CSV in the repo with genuine duplicate anchors.**
  Every prior Done card's CSV is one-row-per-anchor (I surveyed all 40; e.g.
  spec-039 = 38 rows/38 anchors; spec-027's apparent "48 of 50" is just two
  blank-term/anchor rows the loader skips, NOT dup anchors). So the standing
  importer has never had to handle this shape, and the spec-040 CSV was authored in
  the many-term→one-anchor grammar that only `scripts/check_spec_glossary.py`
  (`load_terms`, lenient — no uniqueness check; `check_spec_glossary` passed with
  "OK: 127 terms" at pre-flight) accepts.
- The two tools disagree on the terms-CSV grammar. `check_spec_glossary` (spec
  authoring gate) allows many-terms→one-anchor; `import_spec_terms` (done-card
  wrap) requires unique anchors. This is exactly the invariant worker-2 memory
  records — but the spec-040 CSV violates the `import_spec_terms` half.
- The spec itself does NOT pin the terms-CSV anchor grammar or the importer's
  dedup behavior (only references the companion CSV at spec lines 1090, 2662), so
  this is an unstated-assumption spec gap.

Consequence: `import_spec_terms --check` now fails for card 40 (was failing on 039
at baseline), so the standard wrap verification ("`--check` OK for ALL done cards")
is unreachable with the CSV as-authored, and card 40 currently carries only the 1
bootstrap glossary link instead of the intended 30-anchor set.

**Two root-cause fixes (Worker-1's call — do not want to make it unilaterally):**

1. **Make `import_spec_terms._load_rows` aggregate rows per anchor** (dedupe:
   keep the first row's `term_text`/notes/order per distinct anchor, or record all
   `GlossarySpecMention` term_texts but link the card once per distinct anchor).
   This is the AGENTS.md root-cause fix — it makes the done-card importer accept the
   SAME CSV grammar `check_spec_glossary` already accepts, preserves the 127-row
   symbol provenance, and fixes the tool disagreement permanently for any future
   many-term→one-anchor CSV. Costs a small importer change + a package/example test
   (this is the fakeshop importer, outside the 100% package gate). RECOMMENDED.
2. **De-duplicate the spec-040 terms CSV to 30 one-per-anchor rows** (match every
   other card's shape). Smaller diff, but discards the 97 extra symbol→anchor
   provenance rows and leaves the two tools mutually inconsistent for the next
   many-term CSV. This edits a spec companion artifact (Worker-1 territory).

Either way, after the fix the re-pass runs `import_spec_terms` (real sync — also
reconciles card 039's stale `docs/SPECS/spec-039-…` mention path as a side effect,
maintainer decision #2), then Family-2 step 2g (card-body/DoD ticks), then the
Family-3 regenerates + the full verification (two-consecutive-regenerate hashes,
`--check` OK for all done cards, `DONE-040` in KANBAN Done, TREE `--check`=0,
`makemigrations --check`).

**Also recorded (already fixed, informational):** the
`tests/rest_framework/__init__.py` TREE render-blocker (a `#` comment where
`build_tree_md.py` requires a `"""docstring"""`) — a pre-existing HEAD defect from
the Done 039 work — was converted to a real docstring this slice, per the task
prompt's TREE-hazard directive. No other `.py` docstring gap blocks the TREE render
(verified). The `scripts/build_tree_md.py` `FAKESHOP_APP_NAMES` hardcoded-list
hazard (missing `accounts`) was also fixed this slice.

---

## Build report (Worker 2, pass 2)

**BUILT — the card-wrap is complete.** Worker 1's CSV dedup cleared the Family-2
step-2f blocker. This pass ran the real `import_spec_terms` sync, ticked the shipped
DoD items, and regenerated all four DB-backed docs. All verification gates pass.
Every step from the prior partial-wrap forward now landed; nothing deferred.

### Files touched

**Regenerated generated docs (Family 3 — this pass; DB-backed, do NOT hand-edit):**

- `KANBAN.md` — regenerated via `scripts/build_kanban_md.py`. Now shows
  `DONE-040-0.0.13` in the Done section (catalog row + card entry), removed from WIP,
  with all three Definition-of-done items rendered `- [x]`. The `{{card_ref:0}}`
  placeholder resolves to `DONE-036-0.0.11` (FK-backed, correct).
- `KANBAN.html` — regenerated via `scripts/build_kanban_html.py` (mirror of the MD).
- `docs/GLOSSARY.md` — regenerated via `scripts/build_glossary_md.py`. Picks up the
  two term flips (`auth-mutations` + `serializermutation` Index rows and detail
  entries now `shipped (\`0.0.13\`)`), the package-version line at `0.0.13`
  (BoardDoc pk=40), and the auth-submodule exports note (BoardDoc pk=41). Render stats:
  86 terms, 89 category memberships, 1192 spec mentions across 51 specs.
- `docs/TREE.md` — regenerated via `scripts/build_tree_md.py`. Renders `auth/` package
  rows, the `tests/auth/` tree, the fakeshop `accounts` app (via the pass-1
  `FAKESHOP_APP_NAMES += "accounts"` script edit), and the live `test_auth_api.py`
  row. `--check` exits 0 (up to date).

**DB (`examples/fakeshop/db.sqlite3` — slice-intended generated/binary divergence, do
NOT revert):**

- Family-2 step 2f: ran `uv run python examples/fakeshop/manage.py import_spec_terms`
  (real sync, no `--check`) → "Imported glossary terms for 40 done card(s)." Card 40's
  `CardGlossaryTerm` set went from the 1 bootstrap link to the full **30-anchor** set;
  card 039's stale `docs/SPECS/spec-039-…` `GlossarySpecMention` rows were reconciled
  as the maintainer-approved joint-cut side effect (039 mention rows now populated,
  `--check` passes for it).
- Family-2 step 2g: set all **3** card-40 `definition_of_done` `CardItem.is_complete`
  → `True` via ORM `.save()` (matching the sibling done-card convention: DONE-038 =
  6/6, DONE-039 = 7/7 all ticked). No stale spec-filename refs or `## [0.0.X]` residue
  found in the card body; the `{{card_ref:0}}` placeholder is FK-backed and left
  untouched.

**Family-1 file edits (landed in pass 1, re-verified present & intact this pass — NOT
re-touched):** `pyproject.toml`, `django_strawberry_framework/__init__.py`,
`tests/base/test_init.py`, `uv.lock` (quintet members); `scripts/build_tree_md.py` +
`tests/rest_framework/__init__.py` (TREE render fixes); `README.md`, `docs/README.md`,
`CHANGELOG.md`, `GOAL.md`, `TODAY.md` (prose). Spot-verified: `pyproject`/`__init__`
version = `0.0.13`, `test_version` asserts `0.0.13`, `build_tree_md.py`
`FAKESHOP_APP_NAMES` includes `"accounts"`, `tests/rest_framework/__init__.py` leads
with a `"""docstring"""`, CHANGELOG has the `## [0.0.13] - 2026-07-02` section,
README Status = `0.0.13`.

### Tests added or updated

- None this pass. Slice 3 ships no new logic; the only test change
  (`tests/base/test_init.py::test_version` → `0.0.13`) landed in pass 1. No focused
  pytest run was required by the artifact for this pass (the work is ORM sync + doc
  regenerates). Ran no `pytest --cov*`.

### Validation run

- **`import_spec_terms --check` (all done cards):** pre-sync baseline re-verified —
  failed ONLY on card 039's stale `docs/SPECS/spec-039-…` path (`[] != [38 anchors]`),
  exactly the maintainer-approved pre-sync state. **Post-sync: `OK: 40 done cards have
  glossary links.`** — OK for EVERY done card incl. 039 AND 040. No done card stays
  broken; nothing to escalate to Worker 1.
- **Two-consecutive-regenerate byte-stability (sha256, regen → hash → regen → hash):**
  all four byte-identical across the two runs:
  - `KANBAN.md` = `bb6d85f5f9666f6f86b27dd61c093d6e1ab372e41a9a5636cad213609490b180` (both)
  - `KANBAN.html` = `30b6fbd13ad66edd0abadf1360393d078a3ba317239935ca6f760289a749f415` (both)
  - `docs/GLOSSARY.md` = `eb6cda59b1a66e7c53681f35443526c76427b61f9ae5878c789bbf090545980f` (both)
  - `docs/TREE.md` = `7afbb80660d8c8f3d8cb7ed55705591261a1e89d6847406f17c9cf86489e3c6d` (both)
- **KANBAN DONE check:** `DONE-040-0.0.13` appears in the Done section (catalog line +
  entry), zero `WIP-ALPHA-040` / `WIP-040` residue, all 3 DoD items render `- [x]`.
- **GLOSSARY flips:** package-version line = `Current package version: \`0.0.13\``;
  Index rows `[Auth mutations](#auth-mutations) | shipped (\`0.0.13\`)` and
  `[\`SerializerMutation\`](#serializermutation) | shipped (\`0.0.13\`)`.
- **TREE `--check`:** exits 0 (`docs/TREE.md is up to date.`); `auth/` + `tests/auth/`
  + `accounts` + `test_auth_api.py` rows all present.
- **`manage.py check`:** System check identified no issues (0 silenced).
- **`makemigrations --check --dry-run`:** No changes detected (exit 0).
- **`check_spec_glossary --spec docs/spec-040-auth_mutations-0_0_13.md`:** `OK: 30
  terms - all have glossary entries and at least one spec link.`
- **`ruff format .`** — 308 files unchanged (the COM812/formatter warning is the
  standing pre-existing config warning). **`ruff check --fix .`** — All checks passed!
- **`git status --short` classification:** slice-intended = the 4 regenerated docs
  (`KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`) + the
  `examples/fakeshop/db.sqlite3` divergence (this pass) plus the 11 pass-1 Family-1
  source/test/script/prose files (unchanged this pass, re-verified intact). NOT my
  churn (left untouched per Hard rules): Slices-1/2 source
  (`django_strawberry_framework/auth/{mutations,queries}.py`,
  `mutations/{fields,resolvers}.py`, `registry.py`, `types/finalizer.py`,
  `examples/fakeshop/apps/accounts/schema.py`, `config/{schema,settings}.py`,
  `schema_reload.py`, `test_query/test_auth_api.py`, `tests/auth/*`), Worker 1's
  modified spec + deduped terms CSV, the 8 `D` prior-039-cycle deletions, the 4
  untracked build artifacts. No unrelated tool churn to revert.

### Implementation notes

- **DoD tick set = all 3 items.** All three card-40 `definition_of_done` items
  describe shipped behavior (auth module + four factories; mirrored `tests/auth/`;
  opt-in-import documentation), so all three flipped to complete — matching the
  sibling done-card convention (DONE-038 6/6, DONE-039 7/7 all ticked). No DoD item
  describes deferred work.
- **`planning_state="In progress"` left untouched (matches siblings).** The KANBAN
  card-body `Status: In progress` line renders from the `planning_state` field, which
  DONE-038 and DONE-039 also carry as `In progress` (verified). It is a legacy field
  the plan does not name; the kanban-column `status.key='done'` is what places the
  card in the Done section. Not a card-wrap edit target — left as-is for parity.
- **Card-body prose needed no edits.** Grepped the card-40 `CardItem.text` bodies for
  stale spec-filename refs and `## [0.0.X]` residue: none present. The `{{card_ref:0}}`
  placeholder resolves via FK to `DONE-036-0.0.11` at render — correctly not rewritten
  to a bare number (per worker-2 memory).
- **039 reconcile confirmed non-destructive.** Post-sync `import_spec_terms --check`
  reports OK for all 40 done cards; the 039 mention rows are populated
  (both the working `docs/` and archived `docs/SPECS/` spec paths carry mentions), and
  no done card other than 040 stays broken — nothing to hand back to Worker 1.

### Notes for Worker 3

- The reviewable pass-2 diff is: the 4 regenerated generated docs (`KANBAN.md`,
  `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`), the `examples/fakeshop/db.sqlite3`
  divergence (card-40 full 30-anchor glossary-link set + 3 DoD ticks + the all-cards
  039/040 mention reconcile), and the pass-1 Family-1 file edits (unchanged this pass).
  The generated docs are DB-render output — review them against the DB state, not as
  hand-edits (any hand-edit would be reverted by the next regenerate).
- Two-consecutive-regenerate byte-stability is proven (hashes above) — the docs are a
  faithful render of the DB, not stale.
- Static inspection helper: skipped per the Plan (no package `.py` logic this pass;
  the only `.py` script touch, `FAKESHOP_APP_NAMES += "accounts"`, was pass 1). No
  shadow files used.

### Notes for Worker 1 (spec reconciliation)

- **039 re-key outcome: fully reconciled, nothing outstanding.** The prior-pass
  structural blocker (spec-040 terms-CSV duplicate anchors) is resolved by your
  Option-B dedup (30 unique-anchor rows). The real `import_spec_terms` sync ran clean
  across all 40 done cards; `import_spec_terms --check` now reports `OK: 40 done cards
  have glossary links.` — card 039's stale `docs/SPECS/` mention mismatch is
  reconciled as the maintainer-approved joint-cut side effect, and **no done card
  other than 040 stays broken.** There is nothing to escalate or partial-fix.
- No new drift discovered this pass. The dedup is the reconciled state — I did NOT
  re-touch the spec or the terms CSV. The `planning_state="In progress"` render on
  DONE-040 (noted in Implementation notes) is sibling-consistent, not a defect.

### Spec slice checklist (verbatim) — tick audit (this pass)

All five sub-boxes + the slice-level box now `- [x]`; every sub-contract landed across
pass 1 (version quintet source members, the 039-deferred prose flips, the CHANGELOG
`0.0.13` section, the term-flip + version-line + exports-note DB edits, the TREE
script/docstring fixes, the card done-flip) and pass 2 (the full `import_spec_terms`
sync completing the 30-anchor glossary-link set, the DoD ticks, and the four-doc
regenerate that materializes the KANBAN Done row + GLOSSARY flips + TREE rows). No box
ticked for deferred work — nothing is deferred.

---

## Review (Worker 3)

Reviewed the full Slice-3 incremental surface: the four source-side quintet members +
the DB-generated GLOSSARY version line, the doc-flip prose (`README.md`,
`docs/README.md`, `GOAL.md`, `TODAY.md`), the maintainer-authorized `CHANGELOG.md`
`[0.0.13]` section, the two TREE render-fixes (`scripts/build_tree_md.py`,
`tests/rest_framework/__init__.py`), the four regenerated DB-backed docs
(`KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`), the semantic DB
content (via the regenerated docs + read-only ORM/CLI queries), and the deduped
terms CSV. Independently re-ran the byte-stability regenerate, `import_spec_terms
--check`, `manage.py check`, `makemigrations --check`, the focused `test_init.py`
run, and the trailing-comma check. Out-of-scope Slice-1/2 source and the modified
spec / `resolvers.py` `TODO(spec-040 Slice 1)` anchor were not weighed (except where a
Slice-1/2 residue surfaces into a Slice-3-regenerated doc — see M1).

### High:

None.

### Medium:

#### M1 — Stale "planned by spec-040" staging wording renders into the Slice-3-regenerated `docs/TREE.md`

The TREE regenerate (a Slice-3-owned deliverable) sources its per-directory
descriptions from module docstrings. Two now-shipped source `__init__.py` files still
carry pre-ship staging language, and it surfaces verbatim in `docs/TREE.md`:

```docs/TREE.md #"Opt-in session-auth field factories planned by spec-040."
├── auth/    # Opt-in session-auth field factories planned by spec-040.
```
(rendered at `docs/TREE.md` lines 84-context/208 from
`django_strawberry_framework/auth/__init__.py` #"planned by spec-040", whose docstring
also still reads "after Slice 1/2 replace the fail-loud placeholders in
``mutations.py`` and ``queries.py``")

```docs/TREE.md #"Schema-only fakeshop accounts app planned by spec-040."
    ├── accounts/    # Schema-only fakeshop accounts app planned by spec-040.
```
(rendered at `docs/TREE.md` line 657 from
`examples/fakeshop/apps/accounts/__init__.py` #"planned by spec-040")

The `auth/mutations.py` / `auth/queries.py` module docstrings additionally carry
`spec-040 Slice 1` / `Slice 2` staging tags that render into `docs/TREE.md` lines
209-210 (`# ... (spec-040 Slice 1: login / logout)` etc.).

**Why it matters.** The behavior these docstrings describe as "planned"/"after
Slice 1/2 replace the fail-loud placeholders" is now SHIPPED (the `auth/` package is
live, wired into the fakeshop `accounts` app, and exercised by `test_auth_api.py`).
`docs/TREE.md` is a file Slice 3 deliberately updated, and my
`### Documentation / release sanity` mandate is "no obsolete planned/old-version
wording remains in files the slice updated." This is also exactly the staged-language
residue `BUILD.md` cross-slice integration step 6 sweeps for.

**Scope / why this is escalated, not a hard block.** The three source files
(`auth/__init__.py`, `accounts/__init__.py`, `auth/mutations.py`/`queries.py`) are
Slice-1/2 territory — NOT in the Slice-3 `### Files touched` Family list, NOT in the
Slice-3 diff, and the task's out-of-scope list names them final-accepted. Slice 3
CANNOT fix this in-scope: the TREE render is DB/filesystem-sourced and hand-editing the
generated `docs/TREE.md` is forbidden (the next regenerate reverts it), and the fix
lives in out-of-scope source docstrings. Note the sibling `tests/auth/__init__.py`
docstring WAS refreshed this cycle ("planned" → "opt-in ... (spec-040)", `TODO(spec-040
Slice 1-2)` anchor removed), so the fix pattern is established — the two package/example
`__init__.py` files and the two `auth/*.py` module docstrings were simply missed.
Recorded as an `Escalated:` item under `### Notes for Worker 1 (spec reconciliation)`
with the resolution paths; routing to the integration pass / owning slice per BUILD.md
step 6 rather than blocking Slice 3, since the Slice-3 deliverables themselves are
correct and the stale strings are a faithful render of out-of-scope source.

**Recommended change (integration-pass / Slice-1-2 re-loop, not Slice 3):** refresh
`django_strawberry_framework/auth/__init__.py` and
`examples/fakeshop/apps/accounts/__init__.py` module docstrings from "planned by
spec-040" / "after Slice 1/2 replace the fail-loud placeholders" to shipped wording
(mirroring the `tests/auth/__init__.py` refresh); consider whether the `Slice 1`/`Slice
2` staging tags in `auth/mutations.py`/`queries.py` docstrings should become
`spec-040` / `DONE-040-0.0.13` provenance (AGENTS.md "shipped behavior … the staged
anchor is removed in the same change that ships the slice"). Then regenerate
`docs/TREE.md`.

**Test expectation:** none (docstring/doc wording; no behavior change). The TREE
`--check` already exits 0 both before and after such a refresh.

### Low:

None.

### DRY findings

None. Slice 3 introduces no package helper, constant, validation branch, or test
helper — it is a one-line `__version__` string edit, a one-line `test_version`
assertion, a one-item `FAKESHOP_APP_NAMES` tuple addition, a docstring conversion,
doc-prose flips, and DB/ORM edits + doc regenerates. The DRY spine ("reuse the
generators, never hand-edit their output") is honored: all four generated docs are a
verified byte-stable render of the DB (no hand-edits), and the version string is bumped
at each of its six single-sited homes (four source files + `uv.lock` + the `kanban`
`BoardDoc` pk=40) rather than via a one-off bump script. The CHANGELOG reuses existing
reference-style link defs and adds new ones (`[glossary-auth-mutations]`,
`[glossary-serializermutation]`) to the correct `<!-- docs/ -->` group alphabetically;
no inline `](path)` links introduced.

### Public-surface check

**PASS.** `git diff HEAD -- django_strawberry_framework/__init__.py` changes ONLY the
`__version__` string literal (`"0.0.12"` → `"0.0.13"`); no `__all__` / re-export change.
The auth surface is submodule-only (Decision 3) — the `auth` symbols are NOT added to
the package root. `tests/base/test_init.py::test_public_api_surface_is_pinned` asserts
the 26-member `__all__` tuple UNCHANGED (only the neighboring explanatory comment was
refreshed to name the spec-040 `0.0.13` cut and state `__all__` is unchanged); the tuple
assertion body is byte-identical to HEAD. `tests/base/test_init.py` focused run: 5
passed (incl. `test_version` at `0.0.13` and the `__all__` pin). Confirmed
independently: `django_strawberry_framework.__all__` contains no `login`/`logout`/
`register`/`current_user`/`SerializerMutation` entry.

### CHANGELOG sanity

**PASS.** The slice adds a new `## [0.0.13] - 2026-07-02` section (maintainer-authorized
per plan step 5 / Decision 12), placed after `## Versioning`, before `## [0.0.12] -
2026-06-23`.

- **Version line matches the quintet.** `[0.0.13]` matches `pyproject.toml` (`0.0.13`),
  `__init__.py` `__version__` (`0.0.13`), and the `### Changed`
  "`django_strawberry_framework.__version__` is now `0.0.13`" bullet.
- **Headings authorized.** Uses only `### Added` (two bullets, one per card) and `###
  Changed` (the `__version__` bump) — exactly what the plan/spec authorize; no
  unauthorized `### Fixed` / `### Removed`.
- **Wording coherent with what shipped, no over/understatement.** The `SerializerMutation`
  bullet correctly names the `Meta.serializer_class` DRF-flavor, the ride on the shipped
  `DjangoMutation` pipeline, the byte-identical frozen `FieldError` envelope reuse
  (`"__all__"` non-field keying), and the soft-DRF / lazy-root-`__getattr__` / not-in-
  `__all__` behavior. The auth bullet correctly names the four factories + `current_user`,
  the submodule-only import (absent from `__all__`, `import *` stays auth-free), the
  `FieldError` envelope, the `register` `DjangoMutation` rider with `validate_password` +
  `set_password` (plaintext never persisted, sync + async), the AllowAny default as the
  documented inversion of the write family's deny-by-default `DjangoModelPermission`, and
  the session-only / no-Channels-until-`0.0.14` constraint. Both match the shipped
  Slice-1/2 behavior and the GLOSSARY entries.
- **Links resolve.** All five glossary refs used (`[glossary-serializermutation]`,
  `[glossary-auth-mutations]`, `[glossary-fielderror-envelope]`,
  `[glossary-djangomutation]`, `[glossary-djangomodelpermission]`) are defined in the
  CHANGELOG bottom block and point at existing `docs/GLOSSARY.md` anchors (verified:
  `#serializermutation`, `#auth-mutations`, `#fielderror-envelope`, `#djangomutation`,
  `#djangomodelpermission` all present).

### Documentation / release sanity

**PASS with one escalated Medium (M1).**

- **Version strings + statuses + card IDs.** Version quintet all read `0.0.13`: the four
  source-side members (`pyproject.toml`, `__init__.py`, `test_init.py::test_version`,
  `uv.lock` `django-strawberry-framework` block) verified in the diff, and the DB-generated
  fifth member (`docs/GLOSSARY.md` "Current package version: `0.0.13`") rendered from
  `kanban.BoardDoc` pk=40. README **Status** header = `**0.0.13**`; docs/README "Shipped
  today (`0.0.13`)". The GLOSSARY Index rows for both flipped terms read `shipped
  (`0.0.13`)` (`Auth mutations` and `SerializerMutation`), and both detail entries carry
  `**Status:** shipped (`0.0.13`)`. Card ID `DONE-040-0.0.13` used consistently.
- **KANBAN card moved exactly once.** `DONE-040-0.0.13` appears in the Done section
  (catalog line 100 + card entry line 1265); ZERO `WIP-ALPHA-040` / `WIP-040` residue in
  `KANBAN.md` or `KANBAN.html` (grep exit 1). All three `Definition of done` items render
  `- [x]` (matching sibling DONE-038 6/6 / DONE-039 7/7 fully-ticked convention; no DoD
  item describes deferred work).
- **Auth GLOSSARY entry has the full implemented contract.** The `## Auth mutations`
  entry carries all six pinned elements: four factories, submodule-only import (absent
  from `__all__`), AllowAny default + rationale, `FieldError` envelope semantics
  (`"__all__"` for wrong-credentials, `GraphQLError` for permission denial),
  no-Channels/session-only constraint, and the `UserType`-selection caution.
- **Markdown links introduced/moved point at existing targets.** New refs
  `[glossary-auth-mutations]` / `[glossary-serializermutation]` added to docs/README,
  CHANGELOG, and TODAY `<!-- docs/ -->` groups (alphabetical); all resolve to live
  GLOSSARY anchors.
- **Verbatim spec-copied text.** The GLOSSARY / CHANGELOG entry text is DB-rendered /
  plan-canonical and reads coherently against the spec's `## Doc updates`; the version
  line and card IDs match the post-slice package version.
- **Obsolete "coming/planned/old-version" wording in files the slice updated.** README
  (line 57 future clause + Status "Newest shipped surface"), docs/README ("Coming next"
  now only `0.0.14`, the two shipped bullets added), GOAL (three future→shipped flips +
  the fakeshop paragraph), and TODAY (two serializer "releasing in `0.0.13`" clauses
  dropped + the shipped auth bullet under capabilities-not-exercised) are all correctly
  flipped. **One residue in a Slice-3-regenerated doc: `docs/TREE.md` still renders
  "planned by spec-040" (M1)** — but the fix lives in out-of-scope Slice-1/2 source
  docstrings, so it is escalated, not a Slice-3 hand-edit.
- **DB-backed-doc determinism.** Independently re-ran all four regenerates: the second-
  regenerate sha256 of `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md` is
  byte-identical to Worker 2's reported hashes AND to the pre-regenerate state (no-op),
  confirming the docs are a faithful, deterministic render of the DB, not stale hand-edits.
  `import_spec_terms --check` → `OK: 40 done cards have glossary links.` (all done cards
  incl. 039 + 040 reconciled; nothing else broken). `manage.py check` → no issues.
  `makemigrations --check --dry-run` → no changes.

### What looks solid

- **Version quintet consistency.** All six version homes (four source + `uv.lock` +
  DB-rendered GLOSSARY line) read `0.0.13`; `test_version` asserts `0.0.13`; `__all__`
  untouched. Clean, no missed member.
- **Two-consecutive-regenerate byte-stability, independently reproduced.** The generated
  docs are deterministic (hashes match Worker 2's to the byte). The two build passes
  cohere: Worker 1's CSV dedup + Worker 2 pass-2 wrap together produce card 40 with the
  full 30-anchor glossary-link set (not the 1 bootstrap link) and all DoD items ticked.
- **Deduped terms CSV is coherent.** 30 data rows, 30 distinct anchors, zero duplicates;
  12 rows carry `(groups: ...)` provenance in `notes` (the 12 formerly-duplicated umbrella
  anchors), preserving the symbol→anchor intent. `check_spec_glossary` stays green (per
  Worker 1's reconciliation record); `import_spec_terms` now accepts it.
- **039 joint-cut reconcile is non-destructive.** `--check` OK for all 40 done cards; no
  done card other than 040 stays broken.
- **Doc prose is accurate, not overstated.** The "accounts app owns the live
  demonstration" claim is real — `examples/fakeshop/apps/accounts/schema.py` wires
  `login`/`logout`/`register`/`me` over a `UserType` selecting only
  `("id", "username", "email")` (honoring the UserType-selection caution), exercised by
  the extant `test_auth_api.py`. The neighboring unshipped items (aggregate/fieldset/search
  sidecars, image-upload, sharded stress) stay accurately future in GOAL/TODAY.

### Temp test verification

No temp tests created. Slice 3 ships no new logic; the only test change
(`tests/base/test_init.py::test_version` → `0.0.13`, landed pass 1) was verified by a
focused `uv run pytest tests/base/test_init.py --no-cov -q` run (5 passed, no `--cov`
flags). Behavior verification for this slice is regenerate byte-stability + the
`import_spec_terms --check` / `manage.py check` / `makemigrations --check` gates, all
run above.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (M1, Medium): stale "planned by spec-040" staging docstrings render into
  the Slice-3-regenerated `docs/TREE.md`.** `django_strawberry_framework/auth/__init__.py`
  (#"planned by spec-040" + "after Slice 1/2 replace the fail-loud placeholders") and
  `examples/fakeshop/apps/accounts/__init__.py` (#"planned by spec-040") describe
  now-shipped behavior as planned; the `auth/mutations.py`/`queries.py` module docstrings
  carry `Slice 1`/`Slice 2` staging tags. All four are out-of-scope Slice-1/2 source (not
  in the Slice-3 diff), but their text renders into `docs/TREE.md` lines 84/208/209/210/657
  — a doc Slice 3 owns and that my doc-sanity mandate ("no obsolete planned wording in
  files the slice updated") + BUILD.md integration step 6 (staged-language sweep) both
  cover. Slice 3 cannot fix it in-scope (TREE is generated; the fix is in source
  docstrings). **Resolution paths for Worker 1:** (a) route to the cross-slice integration
  pass / a Slice-1-2 re-loop to refresh the two `__init__.py` docstrings (mirroring the
  already-done `tests/auth/__init__.py` refresh) and re-tag the `auth/*.py` `Slice N`
  provenance to `spec-040` / `DONE-040-0.0.13`, then regenerate `docs/TREE.md`; or (b)
  record it in `bld-final.md`'s deferred-work catalog if the maintainer prefers to fold it
  into a follow-up. Accepted Slice 3 with this escalated (the Slice-3 deliverables are
  themselves correct; the stale strings are a faithful render of out-of-scope source), per
  the reviewer's escalate-with-accept path.
- The `resolvers.py:1465` `TODO(spec-040 Slice 1)` anchor is integration-pass-owned per the
  task scope — not re-flagged here, but noted so Worker 1's integration step-6 grep catches
  it alongside M1's staging tags (both name spec-040).

### Review outcome

`review-accepted` (M1 transparently escalated to Worker 1 with resolution paths; no
unresolved High/Medium/Low blocking Slice 3's own deliverables). The version quintet,
CHANGELOG, doc flips, KANBAN card wrap, GLOSSARY flips, deduped terms CSV, and the four
byte-stable regenerated docs are all correct and convention-conforming.

---

## Reconciliation (Worker 1)

Spec-reconciliation pass triggered by Worker 2's `### Notes for Worker 1 (spec
reconciliation)` structural blocker (Family-2 step 2f). This is NOT a final-verification
pass — the slice is not built end-to-end yet (regenerates not run). It resolves the
blocker and routes the remaining wrap back to Worker 2.

### Root-cause diagnosis of the two-tool disagreement

The two tools that read the terms CSV do NOT share a data model, and only one can own
the CSV grammar:

- **`scripts/check_spec_glossary.py`** (spec authoring gate) reads a CSV row as a
  `(term, anchor)` pair where `term` is a *prose phrase to locate in the spec body* and
  `anchor` is *which GLOSSARY H2 that phrase links to*. Its pass/fail is **anchor-keyed
  only** — `check_terms` (`check_spec_glossary.py::check_terms`) checks `anchor in
  glossary_index` and `anchor in spec_anchors`; it never uses `term` for validation.
  `len(terms)` is a cosmetic count in the "OK: N terms" line. Many rows sharing one
  anchor is harmless to it. This is why it accepted the 127-row CSV.
- **`import_spec_terms`** (done-card wrap;
  `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py`) reads a
  CSV row as *one canonical mention*, keyed on `anchor` → `GlossaryTerm.get(anchor=…)`
  → a `GlossarySpecMention` row. Its backing model
  `apps/glossary/models.py::GlossarySpecMention` carries
  `UniqueConstraint(["spec_path", "term"], name="unique_glossary_term_per_spec")` — the
  DB **physically cannot** hold two mention rows for the same `(spec, anchor)`.
  `_assert_plan_matches_db` compares `expected = [row.anchor for row in plan.rows]`
  against a DB list necessarily deduped by that constraint. So `_load_rows`'s
  duplicate-anchor `CommandError` is not incidental strictness — it is the ONLY honest
  guard for a downstream model whose identity IS the anchor. A dup-anchor CSV is
  structurally meaningless to this tool.

The 97 extra rows in spec-040's CSV were a **glossary-authoring device**: they
enumerate spec SYMBOLS (`login_mutation`, `LoginPayload`, `build_payload_type`,
`run_write_pipeline_sync`, …) so the authoring gate can confirm each symbol's prose
mention is anchored, with many symbols legitimately mapping to one umbrella anchor
(all auth factories → `#auth-mutations`; all envelope helpers → `#fielderror-envelope`).
That is a legitimate use of `check_spec_glossary` but an **abuse of the terms CSV as
`import_spec_terms`'s input** — the CSV was doing double duty, and the second consumer's
contract (one row = one canonical mention, unique per anchor) is the one every other
artifact in the repo already honors.

### Empirical verification (read-only; destructive sync NOT run)

- **Dedup keeps `check_spec_glossary` green.** Verified via `check_spec_glossary`'s own
  `load_terms`/`check_terms`: with the full 127-row CSV → `missing_glossary=0,
  missing_links=0`; with a first-row-per-anchor dedup to 30 rows → `missing_glossary=0,
  missing_links=0`; the distinct-anchor set is byte-identical before/after
  (`{a for _,a in full} == {a for _,a in deduped}` is `True`). Every one of the 30
  anchors is present in `docs/GLOSSARY.md` AND linked from the spec body. So the task's
  worst-case ("dedup orphans 97 symbols each needing a row") is **disproven** — the spec
  body links by anchor, not by the 127 phrases, and every anchor survives dedup.
- **No existing test pins the duplicate-anchor raise.**
  `apps/glossary/tests/test_import_spec_terms.py` has three tests; none exercise a
  dup-anchor CSV. But `test_import_spec_terms_reconciles_done_card_csv_to_db` asserts a
  literal 1:1 row→mention mapping with `mention.term_text` = the row's term column,
  confirming the model's one-row-per-anchor intent.
- **Option A cannot actually preserve the 97 rows.** Because the model is anchor-unique,
  aggregating in `_load_rows` still collapses to 30 mentions — it would pick one row's
  `term_text` arbitrarily (or concatenate, changing mention semantics and breaking that
  existing test's assertion shape). Option A trades a clean declarative dedup for a lossy
  runtime dedup that HIDES the collapse and changes how EVERY card's CSV is interpreted.

### Decision — Option B (dedupe the CSV), root-cause per AGENTS.md L4

Chose **Option B: de-duplicate the spec-040 terms CSV to 30 one-per-anchor rows**,
conforming to the repo-wide convention. Rejected Option A (loosen `import_spec_terms`).

Why B is the root-cause fix, not the surface patch:

1. **The 1:1 anchor↔mention shape is the standing contract, enforced in three places:**
   the model constraint (`unique_glossary_term_per_spec`), the importer, and the existing
   importer test. All prior done-card CSVs honor it (037 = 20/20, 038 = 31/31, 039 =
   38/38; spec-040 is the lone outlier). The spec-040 CSV is **mis-authored** against that
   contract — written in the checker's lenient grammar without accounting for the
   importer's stricter, model-enforced one.
2. **Option A is the surface patch**: it makes the symptom vanish by weakening the tool
   that correctly rejected bad input, with **cross-card impact** (re-interprets every
   card's CSV), and still cannot honestly store the extra rows the model forbids.
3. **B makes the two tools agree permanently in the correct direction**: the same 30-row
   CSV passes BOTH tools with identical anchor semantics; `check_spec_glossary` just
   reports "OK: 30 terms". No future many-term CSV is enabled (correct — the model does
   not support it); authors keep the one-row-per-anchor convention the whole repo follows.
4. The symbol→anchor provenance is **not lost**: it lives in the spec body (where each
   symbol is defined and linked) and the umbrella GLOSSARY entries; the surviving 30 rows'
   `notes` column now records each umbrella anchor's grouped symbols
   (`… (groups: login_mutation, logout_mutation, …)`) so the CSV itself retains the
   provenance intent.

### Scope / escalation verdict

**No escalation.** Option B is entirely within Worker-1's spec-custody remit (edit a spec
companion artifact — the terms CSV). It requires **no source/tooling change** and has **no
cross-card impact** (only the spec-040 CSV changed; no other card's CSV, and no shipped
Python, touched). Option A would have changed `import_spec_terms` behavior for every
card's wrap — cross-card tooling behavior exceeding spec-040's authorized scope and
requiring maintainer sign-off — which is a second reason to prefer B. B keeps both tools
green within remit, so per the task's outcome rule the CSV-side fix is preferred.

### `check_spec_glossary` result after the edit

`uv run python scripts/check_spec_glossary.py --spec docs/spec-040-auth_mutations-0_0_13.md`
→ `OK: 30 terms - all have glossary entries and at least one spec link.` (exit 0).

`uv run python examples/fakeshop/manage.py import_spec_terms --check` (read-only) no
longer raises the duplicate-anchor `CommandError` on card 40 — `_load_rows` now parses
the spec-040 CSV cleanly and advances past card 40. `--check` now fails instead on card
039's pre-existing stale-path mention mismatch (`[] != [38 anchors]` under
`docs/SPECS/spec-039-…`), which is the EXPECTED pre-sync baseline the maintainer already
approved reconciling via the standard sync (build plan maintainer decision #2). The
structural blocker is cleared; the real sync (step 2f below) populates both 039 and 040.

### Spec changes made (Worker 1 only)

- `docs/spec-040-auth_mutations-0_0_13-terms.csv` (whole file, 127 data rows → 30):
  de-duplicated to one row per distinct glossary anchor (first-seen row's `term` + `notes`
  kept per anchor; each umbrella anchor's grouped member symbols appended to its `notes`
  as `(groups: …)` to preserve provenance). Triggered by Slice 3 Family-2 step 2f
  (`import_spec_terms._load_rows` raised `CommandError` on the first duplicate anchor).
  Reason: conform to the repo-wide one-row-per-anchor terms-CSV convention that the
  `GlossarySpecMention` unique constraint + `import_spec_terms` enforce, so the done-card
  wrap sync can run; `check_spec_glossary` stays green (anchor-keyed validation, distinct
  anchor set unchanged).
- **Spec body (`docs/spec-040-auth_mutations-0_0_13.md`): NO edit.** The only two spec
  references to the companion CSV are grammar-agnostic — Decision 1 (spec:1089-1093) just
  names the file; Definition-of-done item 1 (spec:2661-2664) asserts `check_spec_glossary`
  reports `OK: <N> terms` with a literal `<N>` placeholder (now satisfied by `30`). The
  spec never pinned the many-term grammar, so the mis-authoring was confined to the CSV.
- **Spec header/status lines re-verified (per-spawn duty):** spec:72 already reads Slice 2
  `final-accepted` from my Slice-2 pass; Slice 3 is still in progress (regenerates not
  run), so no header edit is warranted this pass.

### Notes for Worker 2 (remaining card-wrap completion — the ONLY remaining Slice-3 work)

The blocker is cleared CSV-side. Re-verify the current DB partial-wrap state, then run the
remaining steps IN ORDER (all were planned; only the sync onward is left):

1. **Re-verify partial-wrap state stands** (do NOT revert `examples/fakeshop/db.sqlite3`):
   card 40 is `done` (`DONE-040-0.0.13`) with exactly 1 bootstrap `CardGlossaryTerm`
   (`auth-mutations`); the two term flips (`auth-mutations`, `serializermutation` →
   `shipped` + `shipped (\`0.0.13\`)`), the BoardDoc version-line bump (pk=40 →
   `\`0.0.13\``), and the public-exports auth-submodule note (pk=41) all landed in the
   prior build pass. Family-1 file edits all landed and are ruff-clean.
2. **Family-2 step 2f — run the real `import_spec_terms` sync (NOT `--check`):**
   `uv run python examples/fakeshop/manage.py import_spec_terms`. This now succeeds for
   card 40 (30-anchor CSV) AND reconciles card 039's stale `docs/SPECS/spec-039-…` mention
   path as a side effect (maintainer decision #2). Card 40's `glossary_links` set goes from
   the 1 bootstrap link to the full 30-anchor set.
3. **Family-2 step 2g — card-body / DoD ticks:** fix any stale spec-filename refs / stale
   `## [0.0.X]` → `[Unreleased]` residue in card 40's `CardItem.text`, and set every
   SHIPPED `definition_of_done` `CardItem.is_complete = True` via ORM `.save()`. Do NOT
   rewrite FK-backed `{{card_ref:N}}` placeholders as bare numbers.
4. **Family-3 — regenerate all four docs (reads the Family-2 DB), from repo root:**
   `build_kanban_md.py`, `build_kanban_html.py`, `build_glossary_md.py`,
   `build_tree_md.py` (the two TREE render-blocker fixes — `tests/rest_framework/__init__.py`
   docstring + `scripts/build_tree_md.py` `FAKESHOP_APP_NAMES += "accounts"` — already
   landed, so the TREE render is unblocked).
5. **Verify (record results, do NOT silently absorb):**
   - `import_spec_terms --check` → **OK for ALL done cards** (incl. 039 AND 040). Record
     any done card OTHER than 040 that stays broken post-sync.
   - Two-consecutive-regenerate byte-stability of `docs/GLOSSARY.md` and `KANBAN.md`
     (hash → regenerate again → hash; must be byte-identical). NOT a `git diff` check (the
     DB legitimately diverged for the card move).
   - `KANBAN.md` shows `DONE-040-0.0.13` in Done exactly once (removed from WIP) with DoD
     items ticked.
   - `docs/TREE.md` shows `auth/`, `tests/auth/`, the fakeshop `accounts` app, and
     `test_auth_api.py`; `build_tree_md.py --check` exits 0.
   - `manage.py check` passes; `makemigrations --check --dry-run` clean.
   - `ruff format .` + `ruff check --fix .` clean on touched source/test/script files.
6. Set `Status: built` and hand back to Worker 0 → Worker 3 review.

Do NOT re-touch the spec-040 CSV — the dedup is the reconciled state. Do NOT edit the spec.
The `check_spec_glossary` result and the `import_spec_terms --check` pre-sync state above
are the reconciled baseline you build on.

---

## Final verification (Worker 1)

Final-verification pass for Slice 3, run after Worker 3's `review-accepted` (with M1
escalated to me). Read the full artifact chain (my reconciliation section, both Worker 2
build reports, the Worker 3 review), the build plan, the spec's `## Doc updates` /
Decision 12 / Definition-of-done item 7, and re-verified every contract against the
current working-tree diff. All checks below were re-run independently, not accepted on
prose.

### Spec slice checklist audit (against the working-tree diff)

Walked all five sub-checks + the slice-level box. **Every `- [x]` is truthfully landed —
none over-ticked, none un-ticked, nothing to revise.**

- [x] **Slice-level box.** Slice 3's own deliverables are complete (version cut + release
  flips + card wrap). Confirmed below.
- [x] **Version quintet `0.0.12` → `0.0.13` (all six homes).** Verified in the diff:
  `pyproject.toml:4` (`version = "0.0.13"`), `django_strawberry_framework/__init__.py:37`
  (`__version__ = "0.0.13"`), `tests/base/test_init.py:19` (`test_version` asserts
  `0.0.13`), `uv.lock:218` (the `name = "django-strawberry-framework"` block's version),
  and the DB-generated fifth member `docs/GLOSSARY.md:20` (`Current package version:
  `0.0.13``, rendered from `kanban.BoardDoc` pk=40). `test_version` passes (below).
- [x] **The `039`-deferred joint-cut release flips.** GLOSSARY `SerializerMutation` Index
  row + detail entry both read `shipped (`0.0.13`)` (GLOSSARY:148, :1261); `docs/README.md`
  + `README.md` moved BOTH the serializer flavor and the auth surface from "Coming next"
  to "Shipped today" (docs/README:97 header `0.0.13`, :126-127 the two shipped bullets,
  :129 "Coming next" now only `0.0.14`; README Status → `0.0.13`); `CHANGELOG.md` carries
  the `## [0.0.13] - 2026-07-02` section (maintainer-authorized per the task prompt +
  Decision 12) with `### Added` bullets for both cards + `### Changed` `__version__` bump.
- [x] **Auth-mutations GLOSSARY entry.** Flips to `shipped (`0.0.13`)` (GLOSSARY:74 Index,
  :222 detail) with the implemented contract (the six pinned elements — four factories,
  submodule-only import absent from `__all__`, AllowAny default + rationale, envelope
  semantics, no-Channels constraint, `UserType`-selection caution) and the auth-submodule
  exports note beside the testing note (BoardDoc pk=41). Verified via the byte-stable
  regenerate (below), not a hand-edit.
- [x] **TREE / TODAY / GOAL updates.** `docs/TREE.md` renders the `auth/` package rows, the
  `tests/auth/` tree, the fakeshop `accounts` app (via the `FAKESHOP_APP_NAMES += "accounts"`
  script edit), and the live `test_auth_api.py` row; `TODAY.md` notes the shipped auth
  surface under capabilities-not-exercised-by-products (the `accounts` app owns the live
  demonstration); `GOAL.md` flips the fakeshop auth clause + the serializer clauses from
  future to shipped. **(See M1 below: TREE also renders now-stale staging strings from
  out-of-scope Slice-1/2 source docstrings — a separate finding, does not un-tick this box;
  the target-layout rows the box requires all landed.)**
- [x] **KANBAN card wrap.** `DONE-040-0.0.13` appears in the Done section exactly once
  (catalog line 100 + card entry line 1265), ZERO `WIP-ALPHA-040` / `WIP-040` residue
  (grep = 0 matches), all three Definition-of-done items render `- [x]`, and the card's
  `SpecDoc` points at `docs/spec-040-auth_mutations-0_0_13.md`.

**No box was ticked without matching implementation; no landed contract was left un-ticked;
no box is deferred. The audit is clean.**

### DRY check (this slice + prior accepted slices)

**No new duplication.** Slice 3 introduces no package helper, constant, validation branch,
coercion utility, or test helper — it is a one-line `__version__` string edit, a one-line
`test_version` assertion, a one-item `FAKESHOP_APP_NAMES` tuple addition, a docstring
conversion (`tests/rest_framework/__init__.py`), doc-prose flips, and DB/ORM edits + doc
regenerates. The DRY spine ("reuse the generators, never hand-edit their output") is
honored: all four generated docs are a verified byte-stable render of the DB, and the
version string is bumped at each of its six single-sited homes rather than via a one-off
bump script. The CHANGELOG reuses existing reference-style link defs and adds new ones
alphabetically; no inline `](path)` links. Concur with Worker 3's DRY finding of None.

### Existing tests still pass

`uv run pytest tests/base/test_init.py --no-cov` (NO `--cov*` flag) → **5 passed**
(incl. `test_version` asserting `0.0.13` and `test_public_api_surface_is_pinned` confirming
`__all__` unchanged — auth is submodule-only per Decision 3). Slice 3 adds no new resolver
tests.

### DB-backed verification (re-run independently)

- **Two-consecutive-regenerate byte-stability.** Hashed all four DB-backed docs, regenerated
  all four (`build_kanban_md.py` / `build_kanban_html.py` / `build_glossary_md.py` /
  `build_tree_md.py`), re-hashed: **byte-identical across both runs AND matching Worker 2's
  reported hashes** (`KANBAN.md` `bb6d85f5…`, `KANBAN.html` `30b6fbd1…`, `docs/GLOSSARY.md`
  `eb6cda59…`, `docs/TREE.md` `7afbb806…`). The docs are a faithful, deterministic render
  of the DB — not stale, not hand-edited. My regenerate was a no-op on the working tree (no
  drift introduced).
- **`import_spec_terms --check`** → `OK: 40 done cards have glossary links.` — OK for EVERY
  done card incl. 039 AND 040. No done card other than 040 stays broken; nothing to escalate
  (Worker 2's 039 joint-cut reconcile confirmed non-destructive).

### Carry-forward anchors — confirmed still cleanly deferred

- `django_strawberry_framework/mutations/resolvers.py:1465` `TODO(spec-040 Slice 1)` — the
  ONLY surviving `TODO(spec-040` anchor in the tree (verified: `grep -rEn 'TODO\(spec-040'
  --include='*.py'` returns exactly this one line). Integration-pass owned, spec-recorded
  (Decision 10 P3 "may"), does not block Slice 3.
- The unused `_build_auth_field` / `_bind_auth_mutations` `permission_holder` param
  (`auth/mutations.py:185`, `del permission_holder` at :206 "captured by the resolver
  closures, not read here") — integration-pass consolidation carry-forward, Low/cosmetic,
  out-of-scope for Slice 3.

Both remain cleanly deferred and are re-flagged for the integration pass below alongside M1.

### M1 adjudication (escalated by Worker 3) — DECISION: (a) DEFER to the integration pass

**M1 (Medium):** the Slice-3-regenerated `docs/TREE.md` renders now-stale "planned by
spec-040" / "Slice 1"/"Slice 2" staging strings sourced from out-of-scope Slice-1/2 module
docstrings — describing now-shipped behavior as planned (AGENTS.md L26: "shipped behavior
folds into `docs/TREE.md` … the staged anchor is removed in the same change that ships the
slice"). Verified the source strings and their TREE render:
- `django_strawberry_framework/auth/__init__.py:1` — "planned by spec-040" (→ TREE:208, :297).
- `examples/fakeshop/apps/accounts/__init__.py:1` — "planned by spec-040" (→ TREE:657-context).
- `django_strawberry_framework/auth/mutations.py:1` / `queries.py:1` — `Slice 1` / `Slice 2`
  staging tags (→ TREE:209-210, :298-299).
- **Additionally (broader than the escalation named):** `tests/auth/test_mutations.py` /
  `test_queries.py` docstrings carry "spec-040 Slice 1/2 residue" language (→ TREE:396-397,
  :559), and `examples/fakeshop/test_query/test_auth_api.py` carries the "spec-040 Slice 1/2"
  tag (→ TREE:524). This strengthens the case that M1 is a *tree-wide* staging sweep, not two
  isolated `__init__.py` files.

**Decision: (a) — defer to the integration pass. Slice 3 is `final-accepted`; M1 is recorded
here as an integration-pass carry-forward, NOT a Slice-3 blocker.** Rationale:
1. **Out-of-scope for Slice 3 and unfixable in-scope.** The fix lives in Slice-1/2 source
   docstrings (final-accepted, not in the Slice-3 diff), and `docs/TREE.md` is generated —
   a hand-edit would be reverted by the next regenerate. Slice 3 literally cannot fix it.
2. **Does not affect Slice 3's own deliverables.** The version cut, the 039-deferred release
   flips, the auth-GLOSSARY flip, the TREE target-layout rows, and the DB card wrap are all
   correct and verified above. The stale strings are a faithful render of out-of-scope source.
3. **The integration pass is the designed owner.** BUILD.md "Cross-slice integration pass"
   step 6 mandates a tree-wide `grep -rEn 'TODO\(spec-040|TODO-(ALPHA|BETA|STABLE)-040'`
   staged-anchor sweep + the shipped-behavior fold-in. M1's staging strings and the two prior
   carry-forwards (the `resolvers.py:1465` anchor + the `_build_auth_field` param) all name
   spec-040 and are the natural batch for that single pass.

**CRITICAL CAVEAT (must be honored by the integration pass):** `docs/TREE.md` renders FROM
the module docstrings, so when the integration pass fixes the source docstrings it MUST
re-run `scripts/build_tree_md.py` afterward — the docstring fix + the TREE regenerate must
land together in the same change (else TREE stays stale or `--check` drifts). The refresh
should mirror the already-completed `tests/auth/__init__.py` refresh (its "planned" → "opt-in
(spec-040)" flip + `TODO(spec-040 Slice 1-2)` anchor removal happened this cycle), flipping
"planned by spec-040" / "after Slice 1/2 replace the fail-loud placeholders" to shipped
wording and re-tagging the `Slice N` provenance to `spec-040` / `DONE-040-0.0.13`. The `--check`
already exits 0 both before and after such a refresh (no behavior change).

Rejected (b) `revision-needed`: it would force a heavier Slice-1/2 re-loop now for a
cosmetic doc-wording residue that neither breaks a Slice-3 deliverable nor blocks the build,
when the integration pass (which runs immediately next) is the purpose-built owner.

### Final status

**`final-accepted`.** Slice 3's own deliverables are all complete and verified: the six-home
version cut at `0.0.13`, the `039`-deferred joint-cut release flips (GLOSSARY
`SerializerMutation` + README/docs-README "Shipped today" + README Status + the
maintainer-authorized CHANGELOG `[0.0.13]` bullets), the auth-mutations GLOSSARY flip with the
implemented contract, the TREE/TODAY/GOAL updates, and the `DONE-040-0.0.13` DB card wrap
(30-anchor glossary-link set + 3 DoD ticks). All five checklist sub-boxes + the slice box
truthfully landed; tests pass; the four DB-backed docs are byte-stable renders of the DB;
`import_spec_terms --check` is OK for all 40 done cards. M1 is recorded as an integration-pass
carry-forward (out-of-scope Slice-1/2 docstring residue), joining the two prior carry-forwards.

### Summary

Slice 3 completed the spec-040 auth-mutations build's docs + `0.0.13` version cut + DB-backed
kanban card wrap. It shipped no new resolver logic. The version quintet moved `0.0.12` →
`0.0.13` across all six homes (four source files + `uv.lock` + the DB-rendered GLOSSARY line);
the joint `0.0.13` cut that spec-039 deferred was completed (SerializerMutation + auth surfaces
flipped from "Coming next" to "Shipped today" in README/docs-README, README Status bumped, the
CHANGELOG `[0.0.13]` section added for both cards); the auth-mutations GLOSSARY entry flipped
to `shipped (`0.0.13`)` with the full implemented contract; TREE/TODAY/GOAL were updated for the
shipped auth surface; and card 40 moved to `DONE-040-0.0.13` with its full 30-anchor
glossary-link set and all Definition-of-done items ticked. The prior structural blocker (the
spec-040 terms-CSV duplicate anchors) was resolved by my earlier reconciliation-pass CSV dedup
(Option B); the four DB-backed docs are verified byte-stable renders of the DB.

### Spec changes made (Worker 1 only)

- **`docs/spec-040-auth_mutations-0_0_13.md` header/status line (spec:72).** Edited during
  THIS final-verification pass. The line still read "Slice 3 (docs + version cut) not started."
  — stale now that Slice 3 is built and review-accepted. Per the per-spawn spec-status
  re-verification duty (worker-1.md "Spec status-line re-verification"), flipped it to reflect
  all three slices final-accepted. Reason: stale status headers compound across the cycle and
  mislead downstream readers; Slice 3 is the terminal in-spec slice.
- **`docs/spec-040-auth_mutations-0_0_13-terms.csv` (whole file, 127 data rows → 30).** Made
  earlier in this slice's cycle (my reconciliation pass, recorded under `## Reconciliation
  (Worker 1)` → `### Spec changes made (Worker 1 only)`): de-duplicated to one row per distinct
  glossary anchor to conform to the repo-wide one-row-per-anchor terms-CSV convention that the
  `GlossarySpecMention` unique constraint + `import_spec_terms` enforce, unblocking the
  done-card wrap sync (`check_spec_glossary` stays green — anchor-keyed validation, distinct
  anchor set unchanged). Noted here for completeness; no further CSV edit this pass.
- **No further spec-body edit this pass.** The spec's two references to the companion CSV are
  grammar-agnostic and already satisfied; Decision 12, the `## Doc updates` mechanics, and
  Definition-of-done item 7 all match what landed. M1 is a source-docstring / generated-doc
  residue, not a spec inaccuracy — no spec edit is warranted for it (it is routed to the
  integration pass instead).
