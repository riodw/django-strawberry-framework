# test_query

Live GraphQL-API tests for the **fakeshop** example project.

Tests in this directory exercise the full Django + Strawberry HTTP stack end-to-end by sending requests to `/graphql/` (typically via `django.test.Client.post(...)`). They are slower than the in-process schema tests under [`../tests/`][tests-dir] but verify the entire request pipeline — URL routing, view, schema execution, and JSON response serialization.

**Coverage rule.** Any coverage line in `django_strawberry_framework/` that can be earned by a real-world GraphQL query against the fakeshop schema MUST be earned here. This directory is the *first* place to add a test when adding or changing package code; only fall back to [`../tests/`][tests-dir] (in-process schema execution, services, admin, management commands, URLs) or the package-internal `tests/` tree when the code path is genuinely unreachable from a live `/graphql/` request. Mock only when the real path is impossible (mock behaviour, not the class). The example app is intentionally outside the `fail_under = 100` coverage gate, but the live HTTP tests under this directory are how the package itself reaches 100% — that is the point.

Use the sibling [`../tests/`][tests-dir] directory for tests that exercise schemas (via `schema.execute_sync`), services, models, admin, management commands, or URLs **without** hitting `/graphql/` over HTTP.

`test_library_api.py` is the first live API suite. It covers the `library` acceptance app through real HTTP requests, including FK and reverse-FK traversal, OneToOne nullability, M2M traversal, choice enum serialization, nullable scalar serialization, optimizer SQL shape, optimizer hints, consumer-shaped querysets, a consumer relation override, and the `filter:` / `orderBy:` surfaces.

Sibling live suites now cover the other fakeshop apps: `test_products_api.py`, `test_scalars_filter_api.py`, `test_kanban_api.py`, and `test_glossary_api.py` — exercising the `FilterSet` / `OrderSet` surfaces (`filter:` / `orderBy:`) wired across every app.

The project schema lives at `../config/schema.py`. It imports each app's `Query`, composes them into the top-level `Query`, calls `finalize_django_types()`, then constructs `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`.

<!-- TODO(spec-029 Slice 1):
Update this prose to the singleton-factory optimizer form.
Pseudo:
    _optimizer = DjangoOptimizerExtension()
    strawberry.Schema(query=Query, extensions=[lambda: _optimizer])
-->

HTTP tests in this directory should follow the `_reload_project_schema_for_acceptance_tests` fixture pattern from `test_library_api.py`: clear the global registry, reload `apps.<app>.schema` modules, reload `config.schema`, then reload `config.urls` and clear URL caches. Package tests under `../../../tests/` clear the same global registry for isolation; without the reload pattern, cached example-schema modules can hold stale `DjangoType` classes.

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
