# spec-014-testing_shift-0_0_4.md — IRL API test shift
## Status
Implemented for the 0.0.4 testing-shift slice. The original spec remains here as the design record, but this document now describes the shipped state and the remaining follow-up surface.
## Problem statement
The foundation and optimizer tests proved a lot of consumer-visible behavior through package-local tests under `tests/`, but several tests used ad hoc schemas, synthetic models, or a test-only fixture app. That gave useful precision while making definition-order and relation-cardinality coverage feel less like real framework usage.
The desired shift was to keep low-level package tests for internals while moving public GraphQL behavior into live example-project API tests under `examples/fakeshop/test_query/`.
## Implemented outcome
The example project now has a real `library` app at `examples/fakeshop/apps/library/`. Its models are `Branch`, `Shelf`, `Genre`, `Book`, `Patron`, `MembershipCard`, and `Loan`, covering forward FK, reverse FK, forward OneToOne, reverse OneToOne, forward M2M, reverse M2M, a choice field, and a nullable scalar field.
The fakeshop project now uses a standard explicit-package layout: orchestration lives in `examples/fakeshop/config/`, and domain apps live in `examples/fakeshop/apps/` as `apps.products` and `apps.library`. `pytest.ini` sets `DJANGO_SETTINGS_MODULE = config.settings` and keeps `examples/fakeshop` on `pythonpath`; it does not add `examples/fakeshop/apps` directly.
The project schema in `examples/fakeshop/config/schema.py` imports each app's `Query`, composes the top-level `Query`, calls `finalize_django_types()` once after all example `DjangoType`s are imported, then constructs `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`.
The test-only cardinality fixture app is gone. `tests.fixtures.apps.TestsCardinalityConfig` is no longer in `INSTALLED_APPS`, and the old `tests/fixtures/` files were removed.
## Live HTTP coverage
`examples/fakeshop/test_query/test_library_api.py` is the live `/graphql/` acceptance suite. It uses `django.test.Client.post(...)` and asserts HTTP status, JSON response data, and SQL/query-count shape where relevant.
The suite covers nested traversal through `Branch → Shelf → Book → Loan → Patron`, nullable reverse OneToOne (`Patron.card`), reverse M2M (`Genre.books`), forward FK `select_related`, reverse FK and M2M `prefetch_related`, choice enum wire values and schema introspection, nullable scalar wire values, consumer-shaped queryset cooperation, `OptimizerHint.prefetch_related()`, `OptimizerHint.SKIP`, and a consumer-authored relation override observed through response data.
The autouse `_reload_project_schema_for_acceptance_tests` fixture is load-bearing. Package tests clear the global registry for isolation; the HTTP suite therefore clears the registry, reloads `apps.library.schema`, reloads `config.schema`, reloads `config.urls`, and clears URL caches so cached schema modules never hold stale `DjangoType` classes.
## Package-level tests that intentionally remain
Registry lifecycle, finalizer atomicity, invalid Meta configuration, enum sanitization failures, unresolved targets, optimizer cache-key construction, low-level walker behavior, and helper utilities remain under `tests/`.
Manual relation override coverage is layered. Package tests may intentionally inspect Strawberry internals to pin resolver-attachment details and fail early if Strawberry changes those shapes. HTTP tests pin the consumer-visible contract by proving an overridden relation field returns the resolver-shaped data over the wire.
Package tests now use real example-project models from `apps.products.models` and `apps.library.models` instead of a test-only cardinality fixture app. That coupling is intentional: those example model surfaces are part of the framework test substrate.
## Resolved risks and decisions
The app name and placement are settled: `apps.library` under the example project's `apps/` package.
The schema finalization seam is settled: one project-level `finalize_django_types()` call in `examples/fakeshop/config/schema.py`.
HTTP query-count assertions count Django database queries through `CaptureQueriesContext(connection)` and assert broad SQL shape rather than fragile full SQL strings.
Plan introspection through `ctx.dst_optimizer_plan` remains package-level; it is not surfaced through HTTP JSON responses.
## Remaining follow-ups
The current HTTP layer covers the first acceptance surface and several high-value optimizer paths. Future slices can still migrate more optimizer extension cases from `tests/optimizer/test_extension.py` into live HTTP tests where the behavior is consumer-visible:
- Strictness mode currently remains package-level. Move it to HTTP only if a debug header, test-only extension, or other consumer-visible response surface exposes the planned-key state without relying on internals.
- Queryset-cooperation diffing is partially covered by `test_library_consumer_prefetched_queryset_cooperates_with_optimizer_over_http`; custom `Prefetch(...)` objects with shaped querysets remain package-level until a live API flow needs them.
Layer 3 features such as filters, orders, aggregates, fieldsets, permissions, Relay nodes, and `DjangoConnectionField` remain non-goals for this slice and should land under their own specs.

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
