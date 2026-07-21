# test_query

Guide to the fakeshop live GraphQL HTTP acceptance-test tier and its isolation contract.

Tests in this directory exercise the full Django + Strawberry HTTP stack end-to-end by sending requests to `/graphql/` — ordinarily through the shared [`../graphql_client.py`][graphql-client] helpers, whose JSON path routes through the package's own `django_strawberry_framework.testing.TestClient` (spec-043) while keeping the raw-`HttpResponse` return contract. Only tests whose subject is the raw request envelope (malformed bodies, content-type negotiation) drop to a bare `django.test.Client.post(...)`. They are slower than the in-process schema tests under [`../tests/`][tests-dir] but verify the entire request pipeline — URL routing, view, schema execution, and JSON response serialization.

**Coverage rule.** Any coverage line in `django_strawberry_framework/` that can be earned by a real-world GraphQL query against the fakeshop schema MUST be earned here. This directory is the *first* place to add a test when adding or changing package code; only fall back to [`../tests/`][tests-dir] (in-process schema execution, services, admin, management commands, URLs) or the package-internal `tests/` tree when the code path is genuinely unreachable from a live `/graphql/` request. Mock only when the real path is impossible (mock behaviour, not the class). The example app is intentionally outside the `fail_under = 100` coverage gate, but the live HTTP tests under this directory are how the package itself reaches 100% — that is the point.

Use the sibling [`../tests/`][tests-dir] directory for tests that exercise schemas (via `schema.execute_sync`), services, models, admin, management commands, or URLs **without** hitting `/graphql/` over HTTP.

`test_library_api.py` is the first live API suite. It covers the `library` acceptance app through real HTTP requests, including FK and reverse-FK traversal, OneToOne nullability, M2M traversal, choice enum serialization, nullable scalar serialization, optimizer SQL shape, optimizer hints, consumer-shaped querysets, a consumer relation override, and the `filter:` / `orderBy:` surfaces.

Sibling live suites now cover the other fakeshop apps and cross-cutting surfaces: `test_products_api.py`, `test_scalars_api.py`, `test_scalars_filter_api.py`, `test_kanban_api.py`, `test_glossary_api.py`, `test_auth_api.py` (the `accounts` auth surface), `test_uploads_api.py` (multipart `Upload`), `test_debug_toolbar_api.py` (the spec-042 `DebugToolbarMiddleware`, now that fakeshop's shipped settings wire the toolbar — it drives the real `/graphql/` request path under a `DEBUG=True` override, since pytest-django forces the suite to `DEBUG=False`), and `test_multi_db.py` — exercising the `FilterSet` / `OrderSet` surfaces (`filter:` / `orderBy:`) wired across every app.

Two more cross-cutting suites round out the tier. `test_client_api.py` is the request-driving half of `testing/client.py`'s coverage: it posts real operations through the spec-043 `TestClient` / `AsyncTestClient` / `GraphQLTestCase` / `GraphQLTransactionTestCase` family (async multipart upload, `login()` brackets, the `GRAPHQL_URL` / per-call endpoint rungs against a real view), while the DB-free mechanics stay in the package tier at `../../../tests/testing/test_client.py`. `test_mutation_atomicity.py` pins the mutation-atomicity response-completion transaction contract (shipped 0.0.14): a generated mutation's transaction now stays open through graphql-core payload serialization, so a completion failure (an unserializable payload) rolls the write back instead of committing behind `data: null`. These began as `xfail(strict=True)` regressions; the 0.0.14 mutation-atomicity work has landed, they XPASSed, and the markers were removed — the assertions now encode the shipped contract.

The project schema lives at `../config/schema.py`. It imports each app's `Query` (from all six apps — `library`, `products`, `scalars`, `kanban`, `glossary`, `accounts`) and the `Mutation`s contributed by `products`, `scalars`, `library`, and `accounts`, composes them into the top-level `Query` and `Mutation`, calls `finalize_django_types()`, then constructs `strawberry.Schema(query=Query, mutation=Mutation, config=strawberry_config(), extensions=[lambda: _optimizer])` over a module-level `_optimizer = DjangoOptimizerExtension()` singleton.

HTTP tests in this directory use a two-level autouse isolation contract. `_reload_project_schema_for_acceptance_tests` rebuilds the **whole** project schema once on every worker assigned tests from a module. Before every test, `_isolate_project_schema_for_acceptance_test` cheaply rebuilds only `config.schema` and `config.urls`, giving the test a fresh Strawberry schema, optimizer instance, and URLconf while reusing the finalized app types. It fingerprints every registry map and contributing app module; if the test changes that state, teardown performs the complete rebuild under ambient settings, including after assertion failure. The reload discipline is single-sited in the shared [`../schema_reload.py`][schema-reload] module. `reload_all_project_schemas()` clears the global registry, reloads **every** app's `apps.<app>.schema` in dependency-safe order (`glossary` before `kanban`, whose `CardGlossaryTermType.term` FKs to `glossary.GlossaryTerm`), then rebuilds the aggregate schema and URLconf. Reloading the full set is required because `config.schema` composes all six apps: an earlier per-app reload left the *other* apps unregistered after a package-test `registry.clear()`, producing order-dependent `LazyType` `KeyError` or `DuplicatedTypeName` failures. Tests that must re-finalize under changed settings request `project_schema_override`; the function guard detects that registration replacement and restores the default schema after the settings context exits.

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
[graphql-client]: ../graphql_client.py
[tests-dir]: ../tests/
[schema-reload]: ../schema_reload.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
