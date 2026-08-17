# spec-014-testing_shift-0_0_4.md — IRL API test shift
## Status
Shipped at `0.0.4` under card `DONE-014-0.0.4`. This document states the current contract of the test-placement shift. The design record it was authored from, the alternatives that record weighed, and every claim this spec may no longer make live in [`spec-014-testing_shift-0_0_4-rationale.md`][spec-014-rationale].
## Problem statement
Consumer-visible GraphQL behavior is provable two ways: through package-local tests under `tests/` that build ad hoc schemas, synthetic models, or a test-only fixture app, or through a real Django app answering real `/graphql/` requests. The first buys precision at the cost of realism, and definition-order and relation-cardinality coverage is exactly where that cost bites — an unmanaged fixture model has no table, so its relation edges can be asserted only as annotation shape and never resolved through a query.
The contract of this shift is therefore a split, not a replacement: package tests keep the internals, and public GraphQL behavior is proven by live example-project API tests under `examples/fakeshop/test_query/`.
## Shipped outcome
The example project carries a real `library` app at `examples/fakeshop/apps/library/`. This spec contributes seven of its models — `Branch`, `Shelf`, `Genre`, `Book`, `Patron`, `MembershipCard`, and `Loan` — covering forward FK, reverse FK, forward OneToOne, reverse OneToOne, forward M2M, reverse M2M, a choice field, and a nullable scalar field. Every other class and field in that module belongs to a later card and is outside this spec's scope.
The fakeshop project uses a standard explicit-package layout: orchestration lives in `examples/fakeshop/config/`, and domain apps live in `examples/fakeshop/apps/`. This spec establishes `apps.products` and `apps.library` there; the further app packages beside them are later cards' and are outside this spec's scope. `pytest.ini` keeps `examples/fakeshop` on `pythonpath` and does not add `examples/fakeshop/apps` directly; its `DJANGO_SETTINGS_MODULE` names `config.test_settings`, a pytest-only layer over the shipped `config.settings`.
The project schema in `examples/fakeshop/config/schema.py` imports each app's `Query`, composes the top-level `Query`, and calls [`finalize_django_types`][glossary-finalize-django-types]`()` exactly once after all example [`DjangoType`][glossary-djangotype]s are imported and before the schema object is constructed. The served schema carries exactly one [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] instance. The concrete constructor call carries further contracts owned by later specs — the mutation and write surface, the schema-config factory, and the callable-extension form that preserves the optimizer's instance-bound plan cache — and stating those is theirs, not this spec's.
The test-only cardinality fixture app is gone. `tests.fixtures.apps.TestsCardinalityConfig` is not in `INSTALLED_APPS`, and the `tests/fixtures/` files do not exist.
## Live HTTP coverage
`examples/fakeshop/test_query/test_library_api.py` is the live `/graphql/` acceptance suite. It uses `django.test.Client.post(...)` and asserts HTTP status, JSON response data, and SQL/query-count shape where relevant.
The coverage this spec ships spans nested traversal through `Branch → Shelf → Book → Loan → Patron`, nullable reverse OneToOne (`Patron.card`), reverse M2M (`Genre.books`), a forward FK (`Book.shelf`) planned as `select_related` and executed as a visibility-scoped `Prefetch` because `ShelfType` declares a `get_queryset` hook — two queries, the first over `library_book` and the second over `library_shelf` — reverse FK and M2M `prefetch_related`, [choice enum][glossary-choice-enum-generation] wire values and schema introspection, nullable scalar wire values, consumer-shaped queryset cooperation, [`OptimizerHint`][glossary-optimizerhint]`.prefetch_related()`, `OptimizerHint.SKIP`, and a consumer-authored relation override observed through response data.
Schema-registry isolation is load-bearing for the live tier. Package tests clear the global registry for their own isolation, so the live suite must rebuild project schema state rather than trust a cached module. The rebuild is single-sited in `examples/fakeshop/schema_reload.py`: `reload_all_project_schemas()` clears the registry, re-imports or reloads every contributing app schema module in a dependency-safe order, then reloads `config.schema` and `config.urls` and clears Django's URL caches. `examples/fakeshop/test_query/conftest.py` drives it through the module-scoped autouse `_reload_project_schema_for_acceptance_tests` fixture, paired with a function-scoped guard that rebuilds only the schema and URLconf shell per test, fingerprints app registrations by object identity across that rebuild, and restores the full registry if a test mutated them.
## Package-level tests that intentionally remain
Registry lifecycle, finalizer atomicity, invalid Meta configuration, enum sanitization failures, unresolved targets, optimizer cache-key construction, low-level walker behavior, and helper utilities remain under `tests/`.
Manual relation override coverage is layered. Package tests may intentionally inspect Strawberry internals to pin resolver-attachment details and fail early if Strawberry changes those shapes. HTTP tests pin the consumer-visible contract by proving an overridden relation field returns the resolver-shaped data over the wire.
Package tests use real example-project models from `apps.products.models` and `apps.library.models` rather than a test-only cardinality fixture app. That coupling is intentional: those example model surfaces are part of the framework test substrate.
## Settled decisions
The app name and placement are settled: `apps.library` under the example project's `apps/` package.
The schema finalization seam is settled: one project-level `finalize_django_types()` call in `examples/fakeshop/config/schema.py`.
`examples/fakeshop/apps/library/schema.py` declares its [`DjangoType`][glossary-djangotype]s in a deliberately non-dependency order — `LoanType` ahead of `BookType` and `PatronType`, `ShelfType` ahead of `BranchType`, `MembershipCardType` ahead of `PatronType` — so the example schema proves definition-order-independent finalization at real app-import time. That order is a contract on the module, not an accident: tidying it into dependency order retires the coverage without failing a test.
HTTP query-count assertions count Django database queries through `CaptureQueriesContext(connection)` and assert broad SQL shape rather than fragile full SQL strings.
Plan introspection through `ctx.dst_optimizer_plan` remains package-level; it is not surfaced through HTTP JSON responses.
## Remaining follow-ups
The live layer covers the first acceptance surface and several high-value optimizer paths. Further optimizer extension cases in `tests/optimizer/test_extension.py` are migratable to live HTTP tests wherever the behavior is consumer-visible:
- [Strictness mode][glossary-strictness-mode] coverage is package-level: no live-tier test asserts planned-key state. The condition for moving it is a consumer-visible response surface that exposes that state without reaching into internals; the opt-in `DjangoDebugExtension` is such a surface, so the migration is available to a future slice rather than blocked on one.
- Queryset-cooperation diffing is partially covered by `test_library_consumer_prefetched_queryset_cooperates_with_optimizer_over_http`. Custom `Prefetch(...)` objects carrying shaped querysets stay package-level until a live API flow needs them; no live-tier test constructs one.
Layer-3 features are outside this spec's scope, each owned by its own spec or, where none is authored yet, by its own card: filters, orders, permissions, Relay nodes, and [`DjangoConnectionField`][glossary-djangoconnectionfield] on the alpha line, fieldsets and aggregates on the `0.1.x` beta line.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode

<!-- docs/SPECS/ -->
[spec-014-rationale]: appx/spec-014-testing_shift-0_0_4-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
