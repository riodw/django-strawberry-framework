# test_query

Live GraphQL-API tests for the **fakeshop** example project.

Tests in this directory exercise the full Django + Strawberry HTTP stack end-to-end by sending requests to `/graphql/` (typically via `django.test.Client.post(...)`). They are slower than the in-process schema tests under [`../tests/`][tests-dir] but verify the entire request pipeline — URL routing, view, schema execution, and JSON response serialization.

**Coverage rule.** Any coverage line in `django_strawberry_framework/` that can be earned by a real-world GraphQL query against the fakeshop schema MUST be earned here. This directory is the *first* place to add a test when adding or changing package code; only fall back to [`../tests/`][tests-dir] (in-process schema execution, services, admin, management commands, URLs) or the package-internal `tests/` tree when the code path is genuinely unreachable from a live `/graphql/` request. Mock only when the real path is impossible (mock behaviour, not the class). The example app is intentionally outside the `fail_under = 100` coverage gate, but the live HTTP tests under this directory are how the package itself reaches 100% — that is the point.

Use the sibling [`../tests/`][tests-dir] directory for tests that exercise schemas (via `schema.execute_sync`), services, models, admin, management commands, or URLs **without** hitting `/graphql/` over HTTP.

`test_library_api.py` is the first live API suite. It covers the `library` acceptance app through real HTTP requests, including FK and reverse-FK traversal, OneToOne nullability, M2M traversal, choice enum serialization, nullable scalar serialization, optimizer SQL shape, optimizer hints, consumer-shaped querysets, a consumer relation override, and the `filter:` / `orderBy:` surfaces.

Sibling live suites now cover the other fakeshop apps: `test_products_api.py`, `test_scalars_filter_api.py`, `test_kanban_api.py`, and `test_glossary_api.py` — exercising the `FilterSet` / `OrderSet` surfaces (`filter:` / `orderBy:`) wired across every app.

The project schema lives at `../config/schema.py`. It imports each app's `Query` (from all five apps — `library`, `products`, `scalars`, `kanban`, `glossary`) and the `Mutation`s contributed by `products`, `scalars`, and `library`, composes them into the top-level `Query` and `Mutation`, calls `finalize_django_types()`, then constructs `strawberry.Schema(query=Query, mutation=Mutation, config=strawberry_config(), extensions=[lambda: _optimizer])` over a module-level `_optimizer = DjangoOptimizerExtension()` singleton.

HTTP tests in this directory get an autouse `_reload_project_schema_for_acceptance_tests` fixture that rebuilds the **whole** project schema via the shared `reload_all_project_app_schemas` fixture in `conftest.py`: it clears the global registry, reloads **every** app's `apps.<app>.schema` in dependency-safe order (`glossary` before `kanban`, whose `CardGlossaryTermType.term` FKs to `glossary.GlossaryTerm`), then reloads `config.schema` and `config.urls` and clears URL caches. Reloading the full set is required because `config.schema` composes all five apps: an earlier per-app reload (only `apps.<this-app>.schema` + `config.schema`) left the *other* apps unregistered after a package-test `registry.clear()`, so the combined build raised a `LazyType` `KeyError` (e.g. `CategoryFilterInputType`) under collection orders that did not happen to pre-materialize them — a filesystem-order-dependent failure. Package tests under `../../../tests/` clear the same global registry for isolation. A test that must re-finalize under a changed setting (e.g. `override_settings` for a strategy opt-out) requests the `reload_all_project_app_schemas` fixture itself and calls it after applying the setting — there is no module-level reload helper to `import`, so no brittle cross-module import boundary.

Cross-reference:

- `../../../tests/` keeps package-internal coverage such as registry lifecycle, definition-order internals, invalid configuration, and optimizer unit tests.
- `../tests/` keeps example-project tests that execute in process without hitting `/graphql/`.
- This directory is for consumer-visible GraphQL behavior that benefits from the real Django + Strawberry HTTP stack.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[tests-dir]: ../tests/

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
