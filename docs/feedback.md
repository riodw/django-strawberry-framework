# Round-5 review — testing-shift implementation (4 commits)

> Round-4 foundation review (N-1 through N-6) and round-5-pre testing-shift spec review (Q-1 through Q-7) are no longer in this file; their resolution is recorded inline below.

Reviewed commits, oldest → newest:

- **`b0e710f`** — *Finished spec-foundation.md*: applied the round-4 `IN-PROGRESS-002` polish.
- **`1251e07`** — *Refactor tests a bit;*: built the `library` example app and the first HTTP tests.
- **`870d981`** — *restructure example project*: flattened `examples/fakeshop/fakeshop/*` → `examples/fakeshop/*`.
- **`efa31fc`** — *Complete spec-testing_shift.md;*: deleted the cardinality fixture, removed it from `INSTALLED_APPS`, repointed package tests at `library.models`.

Test suite: **395 passed, 1 skipped, 0 failed** under `uv run pytest --no-cov -q` (up from 326). The slice did meaningfully more than the spec text asked for.

## What got addressed from prior rounds

### Round-4 foundation polish (`IN-PROGRESS-002`)

All five items landed in `b0e710f`:

- **N-1 (CHANGELOG `[0.0.4]` entry)** — addressed via `CHANGELOG.md +18 lines`.
- **N-2 (cardinality fixture `INSTALLED_APPS` deviation)** — fully resolved by `efa31fc` deleting `tests/fixtures/` and removing the `INSTALLED_APPS` line. The `BACKLOG-010` Kanban card is now genuinely closed, not just notionally closed.
- **N-4 (multi-pending phase-1 atomicity test)** — addressed via `tests/test_registry.py +49 lines`.
- **N-5 (`PendingRelation` hashability comment)** — addressed in `django_strawberry_framework/types/relations.py`.
- **N-6 (skip-reason clarity)** — addressed in `tests/types/test_base.py`.

### Round-5-pre testing-shift spec questions

- **Q-1 (app name and placement)** — settled. The app is `library` at `examples/fakeshop/library/`. Models: `Branch`, `Shelf`, `Genre`, `Book`, `Patron`, `MembershipCard`, `Loan`. Domain is internally coherent and avoids overlap with the products catalog.
- **Q-2 (where `finalize_django_types()` is called)** — settled. `examples/fakeshop/schema.py:24` calls it between `Query` composition and `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`. Matches `docs/spec-foundation.md:62-63` and the README quick-start.
- **Q-5 (query-count assertion shape)** — settled. `test_library_optimizer_selects_book_shelf_in_http_query` uses `CaptureQueriesContext(connection)` and asserts both `len(captured) == 1` and SQL substrings (`"JOIN"`, `"library_book"`, `"library_shelf"`). Exactly the recommended pattern.
- **Q-6 (model rename to avoid `User` collision)** — settled. None of the library models collide with `django.contrib.auth.User`.
- **Q-7 (test data + pytest style + `Client()`)** — settled. `_seed_library_graph` uses inline `Model.objects.create(...)`, tests are pytest-django functional with `@pytest.mark.django_db`, default `Client()`.

Open from the spec review:

- **Q-3 (filter the migration list to drop tests that cannot move to HTTP)** — the spec text was not edited. Practically, the user implemented the additive HTTP coverage and left the package-level tests intact. Defensible but the spec is now describing intent that was only partially executed; see `M-11` below.
- **Q-4 (rewrite override tests for HTTP)** — not done. The Strawberry-internal coupling at `_strawberry_field` was retained, with a docstring added (`tests/types/test_definition_order.py:22-27`) saying the coupling is intentional ("if Strawberry changes this field shape, these tests should fail loudly"). That is a defensible posture; see `M-17` below.

## What this round got right

- **Implementation went past the spec.** The `library` app fully covers all five cardinalities the spec required: forward FK (`Shelf.branch`, `Book.shelf`, `Loan.book`, `Loan.patron`), reverse FK (`Branch.shelves`, `Shelf.books`, `Book.loans`, `Patron.loans`), forward OneToOne (`MembershipCard.patron`), reverse OneToOne (`Patron.card`), forward M2M (`Book.genres`), reverse M2M (`Genre.books`). Plus a multi-hop graph (`Branch → Shelf → Book → Loan → Patron`) for nested-traversal coverage.
- **Awkward declaration order is real**, not just claimed. `library/schema.py:9-62` declares `LoanType` first, `BookType` second, `ShelfType` third, `MembershipCardType` fourth, `GenreType` fifth, `BranchType` sixth, `PatronType` last. Forward refs (`LoanType.book → Book`, `MembershipCardType.patron → Patron`) and reverse refs (`PatronType.card → MembershipCard`) cross declaration order in both directions.
- **Schema finalization seam is correct.** `examples/fakeshop/schema.py:13-29` imports both apps' `Query` types, composes them, then calls `finalize_django_types()` once before `strawberry.Schema(...)`. Single point, single thread, before request handling — exactly the contract from `docs/spec-foundation.md`.
- **Project flattening is mechanical and self-consistent.** `pytest.ini` was updated (`DJANGO_SETTINGS_MODULE = settings`, `pythonpath = examples/fakeshop`), `manage.py` and `wsgi.py` use `os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")`, `urls.py` does `from schema import schema`, and all package tests under `tests/` were updated to import from `library.models` and `products.models`. No drift.
- **Cardinality fixture removal is total.** `tests/fixtures/cardinality_models.py`, `apps.py`, `models.py`, `__init__.py` are gone. The `INSTALLED_APPS` line in the example settings is gone. Every package test that used to import from `tests.fixtures.cardinality_models` now imports from `library.models`. The layering concern from `BACKLOG-010` is fully resolved.
- **HTTP test pattern is reusable.** `_seed_library_graph()`, `_post_graphql()`, and `_assert_graphql_data()` helpers in `test_library_api.py` are the right shape for follow-up tests. Future contributors can copy the file shape.

## New observations (M-1 through M-18)

### M-1. The example-project flattening is a substantive layout decision worth a TREE.md / AGENTS.md note

Before: `examples/fakeshop/fakeshop/products/...` (Django-conventional project + apps shape). After: `examples/fakeshop/products/...`, with project-level `settings.py`, `schema.py`, `urls.py`, `wsgi.py`, `manage.py` at `examples/fakeshop/`. This works because `pytest.ini` sets `pythonpath = examples/fakeshop` and the modules are imported as bare names (`schema`, `urls`, `settings`).

Trade-off: the example no longer looks like a copy-paste-able real Django project starting point. A consumer who copies `settings.py`/`urls.py` into their own project and tries to run will get `ModuleNotFoundError` because their project's package name is not on `sys.path`. AGENTS.md does mention "the flattened example Django project" but does not explain the trade-off. One paragraph in `docs/TREE.md` (under the "current on-disk layout" section) explaining "this layout is a test-tree convenience; production Django projects should keep the conventional project-package + apps layout" would protect future contributors and downstream copy-paste users.

### M-2. The `_reload_project_schema_for_acceptance_tests` autouse fixture is doing heavy lifting that needs an inline comment

`examples/fakeshop/test_query/test_library_api.py:16-35` does four things per HTTP test:

1. `registry.clear()`
2. `importlib.reload(library.schema)` (or import if not yet imported)
3. `importlib.reload(schema)` (the project schema)
4. `importlib.reload(urls)` + `clear_url_caches()` if `urls` was imported

This is the *only* path that makes the package tests' `_isolate_registry` autouse fixture (`registry.clear(); yield; registry.clear()`) coexist with the example app's import-time `finalize_django_types()` call inside one pytest process. Without this fixture, after a package test runs and clears the registry, the cached `library.schema` and `schema` modules still hold references to "unregistered" `DjangoType` classes; the next HTTP request would either silently fail or hit undefined behavior.

Concerns to document inline (right above the fixture):

- The reload is mandatory — removing it makes the test order-dependent.
- `library.models` is **not** reloaded; only `library.schema`. The Django model classes stay the same; the `DjangoType` subclasses are recreated. This works because the registry was cleared first.
- **Hidden invariant**: tests anywhere in the suite must NOT module-level-import `DjangoType` classes from `library.schema` (e.g., `from library.schema import BookType`). Such an import would capture the *old* class, which the reload then replaces; the test holds a stale reference. None of today's tests do this, but the constraint is invisible without a comment.

A 5-line comment above the fixture documenting these points would prevent a future contributor from removing the reload "because it's slow" and breaking suite isolation.

### M-3. The "awkward declaration order" claim in `library/schema.py` is true today, but unpinned

Six of the seven `DjangoType` declarations in `library/schema.py` cross declaration order in either the forward or reverse direction. That is exactly what the spec called for. But: nothing in the test suite *asserts* the order is awkward. A future contributor reordering the classes alphabetically (or by module-of-use) silently removes the test's value — the schema would still build, the HTTP tests would still pass, but the declaration-order coverage that justifies the awkward order would be gone.

Two cheap pins:

1. A one-line comment at the top of `library/schema.py`: `# Order is intentionally awkward to exercise pending-relation resolution; do not reorder.`
2. A regression test in `examples/fakeshop/tests/test_schema.py` that asserts at least one `DjangoType` in `library.schema` has its target type declared *after* it (e.g., `LoanType` is at index 0 but its `book` target type `BookType` is at index 1).

### M-4. The OneToOne null branch is exercised correctly

`test_library_patron_card_and_genre_reverse_paths_over_http` seeds two patrons (Ada with a card, Grace without) and asserts:

```json path=null start=null
"Ada": {"card": {"barcode": "CARD-1", ...}, ...},
"Grace": {"card": null, "loans": [], ...}
```

This is the cleanest possible HTTP test for reverse-OneToOne nullability. Solid.

### M-5. The optimizer SQL-shape test is the right shape but is undercovered

`test_library_optimizer_selects_book_shelf_in_http_query` covers the simplest case: forward FK `select_related`. It does not cover:

- reverse FK `prefetch_related` (would be 2 queries with `IN (...)`)
- M2M `prefetch_related` (2 queries through the through-table)
- nested `Prefetch` chains (3+ queries with named through tables)
- consumer-shaped queryset cooperation (B8 in the optimizer surface)
- `OptimizerHint` routing

These were items 5–6 in the testing-shift spec's "high-value migrations" list. The current single test is a good template; the missing cases should land as follow-up HTTP tests.

### M-6. `_seed_library_graph` is the right pattern but is over-eager for the optimizer test

The helper seeds the full graph (Branch + Shelf + Genre + Book + Patron + MembershipCard + second Patron + Loan). The optimizer test queries only `allLibraryBooks`, which needs just `Branch + Shelf + Book`. The extra seeded rows (Genre, Patron, MembershipCard, Loan, second Patron) are no-ops for that test's assertions, but they do touch the database. Today the cost is invisible; as more tests land, separate small seed helpers (`_seed_book_with_shelf()`, `_seed_patron_without_card()`, etc.) will keep each test's setup cost minimal and its intent legible.

### M-7. AGENTS.md's "First step of every test: seed via services" rule needs a library carve-out

AGENTS.md:18 says: "Tests touching the catalog or auth start by calling them. Do not hand-roll Category, Item, Property, Entry, or User instances test by test." The library tests do hand-roll Patron/Book/etc. via inline `Model.objects.create(...)`. This is the right choice (no Faker variance for query-count assertions), but it conflicts with the AGENTS.md rule as written. Add one sentence: "Library acceptance tests use inline `Model.objects.create(...)`; products tests continue to use `services.seed_data(...)`. The library app intentionally has no `services.py` because deterministic seed shapes matter more than convenience for the acceptance suite."

### M-8. `library/apps.py` uses `name = "library"` (no dotted path)

This works because `pythonpath = examples/fakeshop`. Same observation as M-1: it is unusual. Production Django apps use `name = "myproject.library"`. A one-line comment in `library/apps.py` ("`name = 'library'` relies on the flattened example-project layout; in a real project use the dotted path") would prevent confusion when this is copied as a starting point.

### M-9. `examples/fakeshop/test_query/README.md` is now stale

The README still says "This directory is currently empty; live API tests will land here as the schema gains real types and resolvers." `test_library_api.py` is in that directory now. Update the README to:

- Note that `test_library_api.py` is the first live API test and what cardinalities / patterns it exercises.
- Explain that the project schema (`examples/fakeshop/schema.py`) calls `finalize_django_types()` and constructs `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`.
- Document the per-test `_reload_project_schema_for_acceptance_tests` autouse fixture pattern so future tests adopt it.
- Cross-reference `tests/` for declaration-order-internal coverage and `examples/fakeshop/tests/` for in-process schema execution.

### M-10. `tests/fixtures/__pycache__` was orphaned by the fixture deletion

`efa31fc` deleted `tests/fixtures/apps.py`, `cardinality_models.py`, `models.py`, `__init__.py` but the `__pycache__/` directory remained. Harmless but cluttered. A `rm -rf tests/fixtures/__pycache__ && rmdir tests/fixtures` cleans it up. Worth folding into a `.gitignore` sweep if not already there.

### M-11. `docs/spec-testing_shift.md` was not updated to match the implemented state

The spec text is identical to the version reviewed in round-5-pre. After implementation:

- `## Current state` line 8 says "the current fakeshop schema is still a placeholder in `examples/fakeshop/fakeshop/products/schema.py`" — both the path and the placeholder state are wrong now (the schema is real and lives at `examples/fakeshop/schema.py`).
- `## Current state` line 9 references "`tests.fixtures.apps.TestsCardinalityConfig` being registered from `examples/fakeshop/fakeshop/settings.py`" — both the fixture path and the settings path are gone.
- `## Risks` line 59 ("the schema needs to call `finalize_django_types()` exactly once after importing all example `DjangoType`s. This may require tightening registry isolation in tests so package tests and example schema imports do not fight over global state") — this risk is *resolved* by the `_reload_project_schema_for_acceptance_tests` fixture; the spec should record that resolution.
- Migration list line:numbers will have drifted with the model-name changes (e.g., `tests/types/test_definition_order.py:77` is still the OneToOne test but the symbols are now `MembershipCardType` / `PatronType`, not `ProfileType` / `UserType`).

Either:
1. Mark the spec as "implemented" and freeze it (with a one-paragraph "Outcome" addendum), then archive it under `docs/`, OR
2. Edit the spec in place to describe the new state (if it is going to keep being a contributor reference).

The first option is consistent with the docs-process pattern AGENTS.md describes ("Completed design docs are archived after shipped behavior is folded into docs/FEATURES.md, docs/TREE.md, and KANBAN.md").

### M-12. Package-level definition-order tests are now coupled to the example project's models

`tests/types/test_definition_order.py:5` imports `from library.models import Book, Genre, MembershipCard, Patron, Shelf` and `from products.models import Category, Entry, Item, Property`. So the package tests now depend on whichever models live in the example project. This is the correct trade-off (one fewer fixture to maintain, real Django models are the highest-fidelity test substrate), but the implication is undocumented:

- If `library/` is renamed or restructured, `tests/types/test_definition_order.py` must be updated.
- If a `library` model is renamed (e.g., `MembershipCard` → `Card`), the package test breaks.
- If the `library` app is deleted, the OneToOne / M2M coverage in `tests/` disappears with it.

This is a real coupling. AGENTS.md should record it: "Package tests under `tests/` use models from the example project (`products.models` and `library.models`); changes to those models may require updates to package tests. Treat the example apps' model surfaces as part of the test contract, not just example code."

### M-13. The choice-field path is exercised incidentally; promote it to deliberate

`Book.circulation_status` is a `CharField(choices=CirculationStatus.choices)`. `BookType.Meta.fields` includes `circulation_status`. `test_library_branch_shelf_book_loan_graph_over_http` asserts `"circulationStatus": "checked_out"` in the response. So the choice-field-to-Strawberry-enum conversion path *is* covered by the HTTP layer, but as a side effect of the broader graph test.

Worth a deliberate test that:

- Posts an introspection query (`{ __type(name: "BookType") { fields { name type { name kind ofType { name } } } } }`) and asserts `BookCirculationStatusEnum` (or whatever the generated name is) appears.
- Posts a query that filters or returns the enum value and asserts the wire format.

This belongs under `test_library_api.py` and closes the spec's "choice enum schema shape can move later" item.

### M-14. The nullable-scalar path is exercised incidentally; same treatment

`Book.subtitle` is `TextField(blank=True, null=True)`. The HTTP test asserts `"subtitle": None`. ✅ Covered. Same recommendation: promote to a deliberate test or at least mention in the test docstring that this is the nullable-scalar coverage path.

### M-15. Consumer-shaped queryset cooperation is not yet covered in `test_query/`

All `Query.all_library_*` resolvers in `library/schema.py` return `models.X.objects.order_by("id")` — plain queryset, no `select_related`/`prefetch_related`. The optimizer's queryset-diffing behavior (B8 in `DONE-003`) is therefore not exercised by HTTP tests. The spec called this out as a high-value migration. To unblock it: add at least one resolver to `library/schema.py` that returns a pre-shaped queryset (e.g., `def all_library_prefetched_books(self) -> list[BookType]: return Book.objects.select_related("shelf").prefetch_related("genres")`), then add an HTTP test that compares the SQL count against the unshaped path.

### M-16. `OptimizerHint` is not yet exercised in `test_query/`

None of the library `Meta` declarations carry `optimizer_hints`. The spec called for at least one HTTP test that covers `OptimizerHint.SKIP` and `OptimizerHint.prefetch_related()`. Adding a hint to one library type (e.g., `Book.Meta.optimizer_hints = {"loans": OptimizerHint.prefetch_related()}`) plus a paired HTTP test would close this.

### M-17. The override tests stayed package-level; the spec should explicitly endorse that

`tests/types/test_definition_order.py:174,201` were not migrated to HTTP. Instead, the `_strawberry_field` helper got a docstring (`:22-27`) that says: "Tests intentionally inspect Strawberry internals such as `base_resolver.wrapped_func` to pin resolver attachment; if Strawberry changes this field shape, these tests should fail loudly."

This is a defensible posture — it pins the contract in two layers (one Strawberry-internal, one user-visible), which catches resolver-attachment bugs earlier than HTTP tests would. But it conflicts with the spec's stated intent ("Manual relation override behavior should be proven by response data rather than Strawberry-internal resolver inspection"). Pick one and align the spec:

- **Option A (recommended)**: keep the package-level coupled tests as intentional pins; add a complementary HTTP test in `test_library_api.py` that asserts a consumer-overridden relation field returns the consumer's data shape over the wire. Coverage is layered, not replaced. Update the spec text to reflect "package-level tests pin internal contract; HTTP tests pin consumer contract."
- **Option B**: rewrite the package-level tests against the response-data observation pattern, then delete `_strawberry_field`. Clean but loses the early-warning value.

`BACKLOG-011` (durable override-test pattern) in KANBAN now blocks on this decision; the card should be updated to reflect Option A or Option B.

### M-18. Coverage gate exclusion: contributors will misread it

AGENTS.md:15 says "[tool.coverage.run] source = ['django_strawberry_framework']. The example app is example code, not shipping code; bugs in it don't affect the published package, so it is intentionally outside the coverage gate." Correct. But: a contributor reading only that line might assume "HTTP tests don't help coverage." They actually do — they cover **package code** (the Strawberry view path, the optimizer, the resolvers, the registry) by exercising it through Django + Strawberry. Only the **library app code** (its `models.py`, `schema.py`, `apps.py`) is uncovered, and that's intentional.

One sentence in AGENTS.md: "HTTP tests under `examples/fakeshop/test_query/` cover the *package* via real Django + Strawberry execution; the example apps' own files (`library/`, `products/`) are intentionally outside the coverage gate."

## Recommended priority order for follow-up

1. **M-9** — update `test_query/README.md` to reflect the live test (5 minutes).
2. **M-11** — decide whether to archive `spec-testing_shift.md` or update its `## Current state` and `## Risks` sections (10 minutes).
3. **M-2** — add the inline comment block above `_reload_project_schema_for_acceptance_tests` (10 minutes).
4. **M-3** — add the "do not reorder" comment in `library/schema.py` and the regression-pin test (15 minutes).
5. **M-7, M-12, M-18** — three small AGENTS.md edits (15 minutes total).
6. **M-17** — pick Option A or Option B for override-test policy; update `BACKLOG-011` (10 minutes for the decision; Option A adds one HTTP test, Option B deletes a helper).
7. **M-13, M-14** — promote choice-field and nullable-scalar coverage to deliberate HTTP tests (20 minutes each).
8. **M-15, M-16** — add consumer-shaped queryset and `OptimizerHint` HTTP coverage (45 minutes each).
9. **M-1, M-8** — flattening trade-off comments (10 minutes total).
10. **M-10** — clean up `tests/fixtures/__pycache__` and the empty `tests/fixtures/` directory (1 minute).

Items 1–6 are documentation and low-cost test additions; items 7–8 grow the HTTP test surface to match the original spec migration list.

## Things that did not come up in the prior reviews

- The `urls.py` admin landing page (`examples/fakeshop/urls.py:11-40`) still points at `/admin/products/item/?...` query-param triggers. These survived the flattening because the admin URL routing is per-app, not per-project-package. ✅ Coincidentally correct; worth noting in commit messages or docs that the flattening preserved the admin trigger paths.
- `examples/fakeshop/tests/test_schema.py` still tests the project-level `Query` and `ProductsQuery` schemas via `schema.execute_sync` (`{ hello }`). The project schema now also includes `LibraryQuery`, but the test does not exercise any library types. Worth one tiny addition: assert the project schema's `__type` introspection includes `BookType` (or any library type). It catches "library failed to wire into the project schema" without requiring a full HTTP round-trip.
- The pytest run also surfaces a warning from `test_seed_shards_command_runs_when_shard_alias_present` overriding `DATABASES`. Pre-existing, unrelated to this shift, but a passing-with-warnings status is sometimes hard to spot. Worth a quick `@override_settings(DATABASES=...)` rewrite on that test if it bothers anybody.

## Closing note

This is the largest single round of progress so far. The foundation slice is functionally complete and shipped. The acceptance-test layer exists and its first HTTP tests are landed. The cardinality fixture is gone. The example project layout is consistent. The remaining work is widening the HTTP coverage surface (M-5, M-13, M-14, M-15, M-16) and tightening contributor-facing documentation (M-1, M-2, M-3, M-7, M-9, M-11, M-12, M-17, M-18). None of it is architecturally hard.
