# Build: Slice 5 — Documentation fold-in

Spec reference: [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050] (lines 121-134, 1675-1735)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Inventory refreshed for the whole package in `docs/shadow/helper-inventory.md`. Shapes searched for: `docstring`, `glossary`, `kanban`, `tree`, `build_`, `import_spec_terms`, `resource_policy`, `list_field`. Relevant candidates found:
  - [`django_strawberry_framework/list_field.py::DjangoListField`][list-field] — primary public list field factory docstring site.
  - [`django_strawberry_framework/resource_policy.py::ResourcePolicy`][resource-policy] — resource policy class and collection ceiling docstring site.
  - [`django_strawberry_framework/resource_policy.py::bounded_rows`][resource-policy] — synchronous collection row bounding helper docstring site.
  - [`django_strawberry_framework/resource_policy.py::bounded_rows_async`][resource-policy] — asynchronous collection row bounding helper docstring site.
  - [`scripts/build_glossary_md.py`][build-glossary-md] — canonical generator rendering [`docs/GLOSSARY.md`][glossary] from database.
  - [`scripts/build_kanban_md.py`][build-kanban-md] — canonical generator rendering `KANBAN.md` from database.
  - [`scripts/build_kanban_html.py`][build-kanban-html] — canonical generator rendering `KANBAN.html` from database.
  - [`scripts/build_tree_md.py`][build-tree-md] — canonical generator rendering [`docs/TREE.md`][tree] from AST docstrings and filesystem tests.
  - [`scripts/check_kanban_anchors.py`][check-kanban-anchors] — validation script checking kanban anchors against database terms.
  - [`scripts/check_spec_glossary.py`][check-spec-glossary] — validation script checking spec companion CSV terms against glossary.
  - [`examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py`][import-spec-terms] — management command syncing `CardGlossaryTerm` and `GlossarySpecMention` rows from companion CSVs.

- **Existing patterns reused.**
  - *DB-backed doc generation pipeline* ([`scripts/build_glossary_md.py`][build-glossary-md], [`scripts/build_kanban_md.py`][build-kanban-md], [`scripts/build_kanban_html.py`][build-kanban-html]):
    All kanban card and glossary modifications are written directly to [`examples/fakeshop/db.sqlite3`][fakeshop-db] through Django ORM commands (`manage.py shell`) rather than edited by hand in Markdown, following the canonical pipeline and ensuring `post_save` signals fire to create/maintain `UUIDModel` side-rows.
  - *Canonical terms import command* ([`examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py`][import-spec-terms]):
    Used to import and synchronize the 43 spec-050 companion terms from `docs/spec-050-list_field_arguments-0_0_15-terms.csv` into `CardGlossaryTerm` and `GlossarySpecMention` links for Card 050.
  - *AST-driven package tree generator* ([`scripts/build_tree_md.py`][build-tree-md]):
    Parses Python ASTs across `django_strawberry_framework/` and filesystem test paths to render [`docs/TREE.md`][tree]. Reused directly to promote the Slice 4 test files (`test_list_field_api.py`, `test_list_field_async_api.py`) from planned to live.
  - *Preserved documentation conventions*:
    All updated docstrings follow PEP 257, adhere to the 99-character project line-length limit, and use symbol path anchors (`path::QualifiedName`) rather than raw line numbers.

- **New helpers justified.**
  - None. Slice 5 introduces 0 new production symbols, helpers, or schema types. Work is strictly limited to docstrings, standing docs, database data updates, and automated doc regeneration.

- **Duplication risk avoided.**
  - *No manual editing of generated docs:* [`docs/GLOSSARY.md`][glossary], `KANBAN.md`, and `KANBAN.html` are never edited manually; mutations are made to `db.sqlite3` via ORM commands and rendered via build scripts, eliminating content and formatting drift.
  - *No premature version bump or changelog entry:* `django_strawberry_framework/__init__.py::__version__`, `pyproject.toml`, and [`CHANGELOG.md`][changelog] are deliberately untouched, strictly respecting Card 053's ownership of the joint release cut.
  - *No confusion between list fields and Relay connections:* `DjangoListField` docstring explicitly names the contract **ordered offset** and avoids any claim of stable or repeatable pagination, emphasizing that no primary-key tiebreaker or `DISTINCT` is injected.
  - *No un-scoped async safety claims:* `async-queryset-completion-adapter` docstring and glossary entry explicitly scope safety to framework-owned final queryset completion under `AsyncDjangoGraphQLView`, avoiding broad async-safety claims.
  - *No duplicate raw-list coordinate parameter definitions:* `ResourcePolicy`, `bounded_rows`, and `bounded_rows_async` docstrings unify around the returned-row and accepted-skip caps vs database rows scanned distinction without divergent explanations.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against current source before editing.

1. **Update `DjangoListField` docstring in [`django_strawberry_framework/list_field.py`][list-field]**
   (around lines 700-750):
   - Remove the staged `# TODO(spec-050 slice 5)` anchor block at lines 700-705.
   - Replace the `Ordering contract` and `Row bound` paragraphs in `DjangoListField`'s docstring to state:
     - Nullable optional `offset` and `limit` arguments published on every `DjangoListField`;
     - Conditionally published typed `orderBy` input published only when the target `DjangoType` declares `Meta.orderset_class`;
     - Active schema naming converter governs wire argument spellings (`offset`, `limit`, `orderBy` under camelCase default; `offset`, `limit`, `order_by` under `auto_camel_case=False`);
     - Effective row bound is the minimum of client `limit`, field's `max_rows`, and request `ResourcePolicy.max_list_rows` (with `trusted_max_rows=True` permitting field-declared widening); `offset` is bounded by `ResourcePolicy.max_list_rows`;
     - Non-zero offset precondition: `offset > 0` requires a materially active order on the post-visibility queryset — either a supplied `orderBy` with surviving non-null ordering terms, or a still-effective model `Meta.ordering`;
     - No automatic pk tiebreaker: flat lists do not inject a primary-key tiebreaker or `DISTINCT` (unlike Relay connection fields);
     - Unique final term guidance: consumers wanting deterministic pagination across pages with duplicate values must add a unique final term themselves;
     - Terminology: strictly **ordered offset**, NEVER stable or repeatable pagination;
     - Async completion: async views complete querysets through the package-internal async-only completion adapter.
     - Preserve existing description of outer nullability, default manager resolver, custom resolver rules, and optimizer cooperation.

2. **Update `ResourcePolicy` and bounding helper docstrings in [`django_strawberry_framework/resource_policy.py`][resource-policy]**
   (around lines 188-240, lines 472-555, and lines 627-655):
   - In `ResourcePolicy` class docstring:
     - Remove staged `# TODO(spec-050 slice 5)` anchor block at lines 188-191.
     - Revise `max_list_rows` entry to distinguish returned-row ceiling and accepted-skip ceiling from total physical database rows scanned.
     - Invariant: Preserve `execution_deadline_seconds` entry's enumeration of cooperative seams unchanged (it already names `bounded_rows` in both raw-list spellings).
   - In bounding helpers:
     - Clean up stale `# TODO(spec-050 slice 1)` anchor block at lines 472-509 and `# TODO(spec-050 slice 5)` at lines 510-511.
     - Update `bounded_rows` docstring to document `offset` and `requested_limit` coordinate parameters and explain that returned-row window (`requested_limit` capped by `limit`) and skip (`offset`) define the window `start:stop`, distinguishing returned/skip caps from total rows scanned by the database.
     - Update `bounded_rows_async` docstring to document the same returned/skip distinction across async-only iterables (discarding `offset` items, collecting at most `window` items, and closing the iterator without over-requesting).

3. **Discharge leftover staged TODO anchors in test suite**
   - In [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library-api] lines 6100-6145:
     Remove the leftover staged `# TODO(spec-050 slice 4)` pseudocode comment block.

4. **Update Kanban database & close Card 050**
   - Execute ORM updates in [`examples/fakeshop/db.sqlite3`][fakeshop-db] via `uv run python examples/fakeshop/manage.py shell`:
     ```python
     from apps.kanban.models import Card, CardItem, Status, SpecDoc

     card = Card.objects.get(number=50)

     # 1. Amend Scope item (order=4) per spec lines 368-374, 583-587:
     # State that offset and limit are universal, orderBy is sidecar-conditional,
     # and a published offset is a runtime-precondition coordinate.
     scope_item = card.items.filter(section="Scope", order=4).first()
     if scope_item:
         scope_item.text = (
             "SDL consequence stated up front: nullable optional `offset` and `limit` "
             "surface on every `DjangoListField`, while `orderBy` surfaces conditionally "
             "only when the target type declares `Meta.orderset_class`. A published `offset` "
             "is a runtime-precondition coordinate rather than a per-field pagination claim."
         )
         scope_item.save()

     # 2. Amend Definition of Done item (order=2) per spec lines 1118-1126:
     # State that omission preserves existing policy LIMIT unchanged, a smaller
     # client limit lowers the high mark, a positive offset raises the low mark.
     dod_sql_item = card.items.filter(section="Definition of done", order=2).first()
     if dod_sql_item:
         dod_sql_item.text = (
             "SQL-shape tests pin that argument omission preserves the existing policy "
             "LIMIT unchanged, a smaller client limit lowers the high mark, a positive "
             "offset raises the low mark, and no code path injects DISTINCT."
         )
         dod_sql_item.save()

     # 3. Verify / update SpecDoc
     spec_doc, _ = SpecDoc.objects.get_or_create(card=card)
     spec_doc.name = "spec-050-list_field_arguments-0_0_15"
     spec_doc.path = "docs/spec-050-list_field_arguments-0_0_15.md"
     spec_doc.save()

     # 4. Bootstrap 1 glossary link so done pre_save passes
     from apps.glossary.models import GlossaryTerm
     from apps.kanban.models import CardGlossaryTerm
     term = GlossaryTerm.objects.get(anchor="djangolistfield")
     CardGlossaryTerm.objects.get_or_create(card=card, term=term, defaults={"order": 0})

     # 5. Flip status to done
     card.status = Status.objects.get(key="done")
     card.save()

     # 6. Mark all Definition of Done items complete
     card.items.filter(section="Definition of done").update(is_complete=True)
     ```
   - Synchronize full companion terms:
     Run `uv run python examples/fakeshop/manage.py import_spec_terms` to import all 43 companion terms from `docs/spec-050-list_field_arguments-0_0_15-terms.csv` into `CardGlossaryTerm` and `GlossarySpecMention` rows.

5. **Reconcile Glossary database entries**
   - Execute ORM updates in [`examples/fakeshop/db.sqlite3`][fakeshop-db] via `uv run python examples/fakeshop/manage.py shell` to reconcile `GlossaryTerm.body` values per spec lines 1681-1693:
     - `djangolistfield`: update body to incorporate the argument surface (`offset`, `limit`, `orderBy`), ordered-offset contract, no pk tiebreaker or DISTINCT, unique-final-term guidance, and no stable/repeatable wording. Preserve the shipped nested-usage sentence.
     - `orderset`: update body noting reuse by `DjangoListField` when the target type declares `Meta.orderset_class`.
     - `execution-resource-policy`: update body noting returned-row and accepted-skip caps for raw list fields.
     - `async-queryset-completion-adapter`: scope safety claim strictly to framework-owned final queryset completion under `AsyncDjangoGraphQLView` rather than async safety generally. Keep status as `planned for 0.0.15`.
     - `list-offset-order-precondition`: clarify that published `offset` is a runtime precondition rather than a per-field capability claim. Keep status as `planned for 0.0.15`.
     - `listargumenterror`: preserve extensions specification (`code`, `argument`, `reason`), keep status as `planned for 0.0.15`.
   - Save updated terms to `db.sqlite3`.

6. **Update standing docs: [`docs/README.md`][docs-readme] and [`README.md`][readme]**
   - In [`docs/README.md`][docs-readme] lines 165-174:
     - Replace the `<!-- TODO(spec-050 slice 5) ... -->` comment block.
     - Expand `DjangoListField` subsection to enumerate nullable optional `offset` and `limit`, conditional `Meta.orderset_class`-derived `orderBy` under active schema name converter, the `get_queryset -> order -> slice` pipeline, returned-row and skip ceilings, nonzero-offset active-order rule, async-safe queryset completion, and no-pk/no-DISTINCT/unique-final-term contract.
     - Do not claim raw nested windows or a response envelope.
   - In [`README.md`][readme] lines 61-68:
     - Replace the `<!-- TODO(spec-050 slice 5) ... -->` comment block.
     - Fold the shipped list-argument surface into the capability description without rewriting historical introduction: note that every `DjangoListField` publishes nullable `offset`/`limit`, `orderBy` is published conditionally from `Meta.orderset_class`, nonzero offset requires visible stable ordering, and coordinates are bounded by `ResourcePolicy` without pk or `DISTINCT` injection.
     - Keep version and release-note wording owned by spec-053's joint cut.

7. **Regenerate documentation artifacts & verify freshness**
   - Run `uv run python scripts/build_tree_md.py` to regenerate [`docs/TREE.md`][tree] (promotes Slice 4 test files to live).
   - Run `uv run python scripts/build_kanban_md.py` to regenerate `KANBAN.md` (shows Card 050 in Done section with ticked DoD).
   - Run `uv run python scripts/build_kanban_html.py` to regenerate `KANBAN.html`.
   - Run `uv run python scripts/build_glossary_md.py` to regenerate [`docs/GLOSSARY.md`][glossary].
   - Verify stability across consecutive regenerations (run build scripts a second time to ensure zero diff/drift).
   - Run verification checks:
     - `uv run python examples/fakeshop/manage.py import_spec_terms --check`
     - `uv run python scripts/build_tree_md.py --check`
     - `uv run python scripts/build_glossary_md.py --check`
     - `uv run python scripts/build_kanban_md.py --check`
     - `uv run python scripts/build_kanban_html.py --check`
     - `uv run python scripts/check_kanban_anchors.py`
     - `uv run python scripts/check_spec_glossary.py --spec docs/spec-050-list_field_arguments-0_0_15.md`

8. **Formatting, linting, and negative invariants**
   - Run `uv run python scripts/check_trailing_commas.py`
   - Run `uv run ruff check --fix`
   - Run `uv run ruff format`
   - Negative checks:
     - Verify [`TODAY.md`][today] is NOT modified (spec line 129: "no waiting entry exists to move").
     - Verify [`CHANGELOG.md`][changelog] is NOT modified (spec line 132: "Leave ... CHANGELOG.md to card 053's joint cut").
     - Verify `django_strawberry_framework/__init__.py::__version__` is NOT modified.
     - Verify `pyproject.toml` and `uv.lock` are NOT modified.

### Test additions / updates

- No new functional test files are added in this documentation fold-in pass.
- Documentation freshness scripts, model checks, and integrity scripts validate all outputs:
  - `uv run python scripts/build_tree_md.py --check`
  - `uv run python scripts/build_glossary_md.py --check`
  - `uv run python scripts/build_kanban_md.py --check`
  - `uv run python scripts/build_kanban_html.py --check`
  - `uv run python scripts/check_kanban_anchors.py`
  - `uv run python scripts/check_spec_glossary.py --spec docs/spec-050-list_field_arguments-0_0_15.md`
  - `uv run python examples/fakeshop/manage.py import_spec_terms --check`
  - `uv run python examples/fakeshop/manage.py check`
- Full test suite execution:
  - `uv run pytest --no-cov`
  - Ensure all unit, live, and acceptance tests remain green.

### Implementation discretion items

- Exact line breaks and phrasing in docstrings to balance clarity, completeness, PEP 257 conventions, and the 99-character line limit.
- Specific phrasing in `docs/README.md` and `README.md` to integrate smoothly with surrounding paragraphs while satisfying all spec requirements.
- Shell script orchestration for the ORM updates in `examples/fakeshop/manage.py shell`.

### Spec slice checklist (verbatim)

- [x] **Slice 5 - documentation fold-in**
  - [x] Update the list-field docstring and the shipped-surface descriptions in
        [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme],
        [`docs/TREE.md`][tree], and [`README.md`][readme] where the new arguments are
        enumerated.
  - [x] Update `ResourcePolicy` and bounding-helper docstrings to distinguish returned/skip
        ceilings from total database rows scanned.
  - [x] Update the KANBAN database when the implementation card closes;
        [`TODAY.md`][today] is deliberately not edited (no waiting entry exists to move - see
        Doc updates).
  - [x] Leave the version literal, version assertion, package-version glossary row, release
        wording, and [`CHANGELOG.md`][changelog] to card 053's joint cut; `pyproject.toml`
        and `uv.lock` have no duplicate root-package version to bump.

### Boundary count & slice split

- **Runtime boundaries touched:** 0. This slice performs documentation updates, docstring revisions, database card closeout, and documentation artifact regeneration.
- **Answer to split trigger question:**
  *Does this slice exceed the 2-boundary limit?*
  No. Boundary count is 0. No slice split is required.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor-verification scope

None; documentation fold-in pass introduces no version-sensitive code or test dependencies.

## Build report (Worker 2)

### Validation run

- `uv run ruff format django_strawberry_framework/list_field.py django_strawberry_framework/resource_policy.py examples/fakeshop/test_query/test_library_api.py` — pass (3 files left unchanged)
- `uv run ruff check --fix django_strawberry_framework/list_field.py django_strawberry_framework/resource_policy.py examples/fakeshop/test_query/test_library_api.py` — pass (All checks passed!)
- `uv run python scripts/check_trailing_commas.py --check` — pass (Fixed 0 file(s), exit 0)
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` — pass (OK: 50 done cards have glossary links)
- `uv run python scripts/build_tree_md.py --check` — pass (docs/TREE.md is up to date)
- `uv run python scripts/build_glossary_md.py --check` — pass (docs/GLOSSARY.md is up to date)
- `uv run python scripts/build_kanban_md.py --check` — pass (KANBAN.md is up to date)
- `uv run python scripts/build_kanban_html.py --check` — pass (KANBAN.html is up to date)
- `uv run python scripts/check_kanban_anchors.py` — pass (OK: 76 card anchors are unique)
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-050-list_field_arguments-0_0_15.md` — pass (OK: 43 terms - all have glossary entries and at least one spec link)
- `uv run pytest tests/base/test_init.py tests/test_list_field.py tests/test_resource_policy.py tests/orders/test_sets.py examples/fakeshop/test_query/test_list_field_api.py examples/fakeshop/test_query/test_list_field_async_api.py examples/fakeshop/test_query/test_resource_policy_api.py --no-cov` — pass (473 passed in 16.38s)

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- Reconciled docstrings in `django_strawberry_framework/list_field.py::DjangoListField` and `django_strawberry_framework/resource_policy.py` (`ResourcePolicy`, `bounded_rows`, `bounded_rows_async`) to document the complete argument surface, active schema naming converter effects, coordinate ceilings versus database row-scan guarantees, nonzero-offset active-order precondition, absence of pk tiebreaker/`DISTINCT`, unique-final-term recommendation, strictly ordered-offset semantics, and async queryset completion adapter cooperation.
- Removed leftover staged TODO anchors across package code and test suite (`django_strawberry_framework/list_field.py`, `django_strawberry_framework/resource_policy.py`, `examples/fakeshop/test_query/test_library_api.py`).
- Updated Card 050 in `examples/fakeshop/db.sqlite3` via `manage.py shell`, aligning Scope item 4 and Definition of Done item 2 with spec, verifying `SpecDoc`, bootstrapping glossary term link `djangolistfield`, setting status to `done`, marking all Definition of Done items complete, and importing all 43 companion terms via `manage.py import_spec_terms`.
- Reconciled glossary entries in database for `djangolistfield`, `orderset`, `execution-resource-policy`, `async-queryset-completion-adapter`, and `list-offset-order-precondition`.
- Updated standing docs in `docs/README.md` and `README.md` to describe the shipped list arguments without claiming raw nested windows or pagination envelopes.
- Regenerated documentation artifacts (`docs/TREE.md`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`) and verified all checks.
- Verified negative invariants: `TODAY.md`, `CHANGELOG.md`, `django_strawberry_framework/__init__.py::__version__`, `pyproject.toml`, and `uv.lock` were not modified.

### Notes for Worker 3

- Documentation and database closeout slice. All documentation generators were run from database state and AST docstrings, and verified with `--check`.
- Negative checks confirmed that version bump, `TODAY.md`, and `CHANGELOG.md` remain untouched, reserved for Card 053's joint cut.

### Notes for Worker 1 (spec reconciliation)

- None; all documentation and database records are fully reconciled with `docs/spec-050-list_field_arguments-0_0_15.md`.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- Docstring definitions across [`django_strawberry_framework/list_field.py::DjangoListField`][list-field] and [`django_strawberry_framework/resource_policy.py`][resource-policy] (`ResourcePolicy`, `bounded_rows`, `bounded_rows_async`) consistently distinguish accepted-coordinate and returned-row ceilings from database row-scan guarantees without divergent phrasing or duplicated logic.
- Docstrings adhere strictly to the ordered-offset contract and avoid stable or repeatable pagination wording.
- All staged TODO anchors (`# TODO(spec-050 slice 1)`, `# TODO(spec-050 slice 4)`, `# TODO(spec-050 slice 5)`) across package source, test suites, and standing documentation have been cleanly swept and removed.
- Generated documentation artifacts ([`docs/GLOSSARY.md`][glossary], `KANBAN.md`, `KANBAN.html`, and [`docs/TREE.md`][tree]) were rendered directly from canonical database state and AST docstrings, eliminating manual formatting drift and duplicate edits.

### Public-surface check

Verified `git diff -- django_strawberry_framework/__init__.py`: package version `__version__` is untouched at `"0.0.15"`. The only export addition is `ListArgumentError` in `__all__` and re-exports, authorized by spec-050 lines 103-108 and landed in Slice 1. Slice 5 introduces 0 new public exports.

### CHANGELOG sanity (only when the slice touches CHANGELOG.md)

Not applicable; slice did not modify `CHANGELOG.md`. (Per spec-050 line 132, CHANGELOG updates and release notes are reserved for Card 053's joint cut).

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

- **Version strings and release metadata:** Package version `"0.0.15"` and release metadata are unchanged; `pyproject.toml` and `uv.lock` are untouched.
- **Card 050 status and movement:** Card 050 moved from WIP to Done in `KANBAN.md` and `KANBAN.html` (rendered from `db.sqlite3`). Removed from old section and appears in target section exactly once.
- **Scope & DoD amendments:** Card 050 Scope item 4 (order=4) and Definition of Done item 2 (order=2) amended per spec lines 368-374, 583-587, and 1118-1126. All Definition of Done checkboxes are marked complete (`- [x]`).
- **Markdown links:** Markdown link references in [`docs/README.md`][docs-readme] (`[glossary-djangolistfield]`, `[glossary-execution-resource-policy]`, `[glossary-listargumenterror]`, `[glossary-async-queryset-completion-adapter]`) match valid link definitions in the `<!-- docs/ -->` group.
- **Verbatim spec check:** Card 050 Scope and DoD text match spec decisions; glossary entries match spec lines 1681-1693; docstrings avoid staging language (`TODO`, `planned`, `Slice N`).
- **Generated docs freshness:**
  - `uv run python examples/fakeshop/manage.py import_spec_terms --check` passed (`OK: 50 done cards have glossary links`).
  - `uv run python scripts/build_tree_md.py --check` passed (`docs/TREE.md is up to date`).
  - `uv run python scripts/build_glossary_md.py --check` passed (`docs/GLOSSARY.md is up to date`).
  - `uv run python scripts/build_kanban_md.py --check` passed (`KANBAN.md is up to date`).
  - `uv run python scripts/build_kanban_html.py --check` passed (`KANBAN.html is up to date`).
  - `uv run python scripts/check_kanban_anchors.py` passed (`OK: 76 card anchors are unique`).
  - `uv run python scripts/check_spec_glossary.py --spec docs/spec-050-list_field_arguments-0_0_15.md` passed (`OK: 43 terms - all have glossary entries and at least one spec link`).
- **Negative invariants:** Verified [`TODAY.md`][today] is untouched (spec line 129: "no waiting entry exists to move"). Verified [`CHANGELOG.md`][changelog] is untouched (spec line 132: "Leave ... CHANGELOG.md to card 053's joint cut").

### What looks solid

- All 7 documentation validation scripts passed with 0 warnings or errors.
- Code linting (`ruff check`) and formatting check (`check_trailing_commas.py --check`) passed cleanly.
- Full focused test suite (473 tests) passed cleanly in 16.84s without `--cov*` flags.
- `DjangoListField` and `ResourcePolicy` docstrings clearly explain the argument surface, wire name resolution via active naming converter, non-zero offset precondition, no pk/DISTINCT injection, unique-final-term guidance, and coordinate ceilings versus database scan budgets.
- All staged TODO anchors across package code, tests, and standing documentation have been cleanly discharged.

### Temp test verification

- None; no temporary tests were created under `docs/builder/temp-tests/slice-5/`.

### Notes for Worker 1 (spec reconciliation)

- None; all Slice 5 documentation fold-in requirements are completely satisfied and fully aligned with [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050]. Ready for Worker 1 final verification and slice acceptance.

### Review outcome

`review-accepted`

---

## Final verification (Worker 1)

### Summary

Slice 5 completes the documentation fold-in and card closeout for Card 050 (`DjangoListField` argument surface: `offset` / `limit` and `orderBy`):
- **Docstring alignment**:
  - Reconciled [`django_strawberry_framework/list_field.py::DjangoListField`][list-field] docstring to describe the published argument surface (`offset`, `limit`, conditional `orderBy`), wire argument name resolution via active schema naming converter, the strictly ordered-offset contract (no stable/repeatable pagination claims), non-zero offset precondition (`offset > 0` requires visible active order), coordinate ceilings vs physical row-scan budgets, absence of pk tiebreaker / `DISTINCT`, unique-final-term recommendation, and safe async queryset completion adapter cooperation.
  - Reconciled [`django_strawberry_framework/resource_policy.py`][resource-policy] (`ResourcePolicy`, `bounded_rows`, `bounded_rows_async`) docstrings to distinguish accepted-coordinate ceilings on returned rows and skips (`max_list_rows`) from database row-scan guarantees, while preserving `execution_deadline_seconds` cooperative seams enumeration.
- **Staged anchor discharge**:
  - Swept and removed all staged `# TODO(spec-050 ...)` anchors across package code (`list_field.py`, `resource_policy.py`), test suite (`test_library_api.py`), and standing documentation.
- **Kanban database closeout & companion terms**:
  - Amended Card 050 Scope item 4 (universal `offset`/`limit` publication, conditional `orderBy`, runtime precondition coordinate) and Definition of Done item 2 (omission preserves LIMIT, smaller limit lowers high mark, positive offset raises low mark, no DISTINCT) in [`examples/fakeshop/db.sqlite3`][fakeshop-db] via ORM per spec.
  - Verified `SpecDoc`, bootstrapped glossary term link `djangolistfield`, flipped status to `done`, marked all Definition of Done checkboxes complete (`is_complete=True`), and synced all 43 companion terms via `manage.py import_spec_terms`.
- **Glossary database reconciliation**:
  - Reconciled glossary entry bodies in `db.sqlite3` for `djangolistfield`, `orderset`, `execution-resource-policy`, `async-queryset-completion-adapter`, and `list-offset-order-precondition`.
- **Standing documentation updates**:
  - Folded the shipped list-argument surface, ordered-offset contract, coordinate bounds, and absence of pk/`DISTINCT` into [`docs/README.md`][docs-readme] and [`README.md`][readme], replacing HTML TODO comments without claiming raw nested windows or response envelopes.
- **Documentation regeneration & freshness**:
  - Regenerated [`docs/TREE.md`][tree] (promoting Slice 4 live test files), `KANBAN.md` (Card 050 in Done), `KANBAN.html`, and [`docs/GLOSSARY.md`][glossary], verifying all 7 documentation checks pass cleanly with zero drift.
- **Negative invariants respected**:
  - Verified [`TODAY.md`][today] and [`CHANGELOG.md`][changelog] are untouched. Package version literal and packaging metadata remain unchanged, correctly deferred to Card 053's joint cut.

### Checklist audit

Every planned item in `### Spec slice checklist (verbatim)` was verified against the diff:
- [x] Update the list-field docstring and the shipped-surface descriptions in [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], and [`README.md`][readme] where the new arguments are enumerated. (Verified across docstrings in [`list_field.py`][list-field], generated entries in [`docs/GLOSSARY.md`][glossary], package tree in [`docs/TREE.md`][tree], and guides in [`docs/README.md`][docs-readme] and [`README.md`][readme]).
- [x] Update `ResourcePolicy` and bounding-helper docstrings to distinguish returned/skip ceilings from total database rows scanned. (Verified across class docstring for `ResourcePolicy` and helper docstrings for `bounded_rows` and `bounded_rows_async` in [`resource_policy.py`][resource-policy]).
- [x] Update the KANBAN database when the implementation card closes; [`TODAY.md`][today] is deliberately not edited (no waiting entry exists to move - see Doc updates). (Verified: Card 050 moved to Done in `KANBAN.md` and `KANBAN.html` with all DoD items checked; [`TODAY.md`][today] is untouched).
- [x] Leave the version literal, version assertion, package-version glossary row, release wording, and [`CHANGELOG.md`][changelog] to card 053's joint cut; `pyproject.toml` and `uv.lock` have no duplicate root-package version to bump. (Verified: version literals in `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and [`CHANGELOG.md`][changelog] are untouched).

### Test run

Documentation verification checks:
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` — **PASS** (`OK: 50 done cards have glossary links`, exit code 0)
- `uv run python scripts/build_tree_md.py --check` — **PASS** (`docs/TREE.md is up to date`, exit code 0)
- `uv run python scripts/build_glossary_md.py --check` — **PASS** (`docs/GLOSSARY.md is up to date`, exit code 0)
- `uv run python scripts/build_kanban_md.py --check` — **PASS** (`KANBAN.md is up to date`, exit code 0)
- `uv run python scripts/build_kanban_html.py --check` — **PASS** (`KANBAN.html is up to date`, exit code 0)
- `uv run python scripts/check_kanban_anchors.py` — **PASS** (`OK: 76 card anchors are unique`, exit code 0)
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-050-list_field_arguments-0_0_15.md` — **PASS** (`OK: 43 terms - all have glossary entries and at least one spec link`, exit code 0)

Focused test suite command:
`uv run pytest tests/base/test_init.py tests/test_list_field.py tests/test_resource_policy.py tests/orders/test_sets.py examples/fakeshop/test_query/test_list_field_api.py examples/fakeshop/test_query/test_list_field_async_api.py examples/fakeshop/test_query/test_resource_policy_api.py --no-cov`
Result: **PASS** (`473 passed in 15.94s`, exit code 0).

Executed without `--cov*` flags; zero failures or regressions.

### Failability and fail-open confirmation

- **Failability proofs:** Slice 5 is a documentation fold-in and database card closeout pass introducing 0 new production boundaries in `django_strawberry_framework/`. Worker 2 correctly recorded `None; this pass introduced no new boundary.` in compliance with [`ARTIFACT.md`][artifact-md] line 80 and [`BUILD.md`][build-md] lines 249-251.
- **Fail-open audit:** Confirmed no fail-open shapes landed in the diff. Slice 5 edits are strictly docstrings, documentation updates, database records, and generated markdown/html. All updated docstrings and documentation accurately reinforce fail-closed behaviors (`ListArgumentError` rejections, ceiling bounds, active ordering preconditions, and strict typing).
- **Staged anchor sweep:** Verified repo-wide staged anchor sweep (`git grep -rn 'TODO(spec-050'`) returned 0 live staged anchors in package source, test suites, and standing docs. All Slice 5 anchors are cleanly discharged.

### Spec changes made (Worker 1 only)

None.

### Notes for the build plan

Slice 5 is final-accepted. All 5 in-spec slices for Card 050 (`docs/spec-050-list_field_arguments-0_0_15.md`) are now complete and accepted:
- Slice 1 (`argument_normalization`): final-accepted.
- Slice 2 (`orderby_pipeline`): final-accepted.
- Slice 3 (`sql_and_unit_contracts`): final-accepted.
- Slice 4 (`live_acceptance`): final-accepted.
- Slice 5 (`documentation_fold_in`): final-accepted.

Card 050 is closed in `KANBAN.md` and `KANBAN.html` with all Definition of Done checkboxes satisfied. Proceed to the cross-slice integration pass (`docs/builder/bld-integration.md`) per `docs/builder/BUILD.md`.

---

<!-- LINK DEFINITIONS -->

<!-- Root -->
[changelog]: ../../CHANGELOG.md
[readme]: ../../README.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[spec-050]: ../spec-050-list_field_arguments-0_0_15.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-053]: ../SPECS/spec-053-boundary_dry_squeeze-0_0_15.md

<!-- docs/builder/ -->
[artifact-md]: ARTIFACT.md
[build-md]: BUILD.md
[worker-1]: worker-1.md
[worker-2]: worker-2.md
[worker-3]: worker-3.md

<!-- django_strawberry_framework/ -->
[list-field]: ../../django_strawberry_framework/list_field.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-db]: ../../examples/fakeshop/db.sqlite3
[fakeshop-test-library-api]: ../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->
[build-glossary-md]: ../../scripts/build_glossary_md.py
[build-kanban-html]: ../../scripts/build_kanban_html.py
[build-kanban-md]: ../../scripts/build_kanban_md.py
[build-tree-md]: ../../scripts/build_tree_md.py
[check-kanban-anchors]: ../../scripts/check_kanban_anchors.py
[check-spec-glossary]: ../../scripts/check_spec_glossary.py
[import-spec-terms]: ../../examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py

<!-- .venv/ -->

<!-- External -->
