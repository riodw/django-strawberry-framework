# spec-testing_shift.md — IRL API test shift
## Problem statement
The current foundation and optimizer coverage proves a lot of consumer-visible behavior through package-local tests under `tests/`, but several tests build ad hoc schemas, synthetic models, or test-only fixture apps. That gives useful precision, but it also makes the new definition-order and relation-cardinality work feel hacky where the behavior would be better proven through a real Django app and real `/graphql/` HTTP requests.
The desired shift is to keep low-level package tests for internals while moving public GraphQL behavior into live example-project API tests under `examples/fakeshop/test_query/`, matching `examples/fakeshop/test_query/README.md`.
## Current state
`docs/README.md` defines the shipped public surface as `DjangoType`, `finalize_django_types()`, definition-order-independent relation finalization, generated relation resolvers, and `DjangoOptimizerExtension`.
`examples/fakeshop/test_query/README.md` reserves `examples/fakeshop/test_query/` for live GraphQL API tests that hit `/graphql/` through Django’s request stack, usually with `django.test.Client.post(...)`.
The current fakeshop schema is still a placeholder in `examples/fakeshop/fakeshop/products/schema.py`, so the existing tests cannot simply be moved into `examples/fakeshop/test_query/` without first adding a real schema that uses the shipped surface.
The current OneToOne and M2M tests depend on `tests.fixtures.apps.TestsCardinalityConfig` being registered from `examples/fakeshop/fakeshop/settings.py`, which works but mixes test fixture models into the example project. A real example app with its own models and schema would remove that pressure.
## Goals
Move consumer-visible GraphQL behavior to IRL HTTP tests where possible.
Use real Django models, real database tables, real schema import/finalization, the real Strawberry view, and real JSON responses.
Keep fast package-level tests for narrow internals, invalid configuration, registry lifecycle, finalizer failure-atomicity, cache-key construction, and utility helpers.
Reduce reliance on test-only model fixtures being loaded through the example project’s settings.
Make the example project a durable proving ground for the currently shipped API, not only for future Layer 3 features.
## Non-goals
Do not remove all package tests. The unit/integration split should become sharper, not disappear.
Do not force intentionally broken app states through `/graphql/` just to test internal failure paths.
Do not activate unshipped Layer 3 API such as `DjangoConnectionField`, filters, orders, aggregates, fieldsets, permissions, or Relay nodes as part of this shift.
Do not require full production readiness for the example project; the target is realistic framework acceptance coverage.
## Proposed example app
Add a dedicated example app for shipped-surface testing. It can live inside the fakeshop project as a small app whose purpose is to exercise framework behavior through real models and a real schema without polluting the product-catalog example.
The app should include models for these relationship shapes:
A FK and reverse FK pair equivalent to `Category` and `Item`.
A multi-hop FK graph equivalent to `Category`, `Item`, `Property`, and `Entry`.
A OneToOne pair equivalent to `User` and `Profile`.
An M2M graph equivalent to `Author`, `Book`, and `Tag`.
A choice field and nullable field if the scalar/enum schema-shape tests are moved into IRL coverage.
The schema should use only shipped APIs: `DjangoType`, `finalize_django_types()`, `DjangoOptimizerExtension`, normal Strawberry root fields, and root resolvers returning Django QuerySets. Type declarations should intentionally exercise awkward definition orders in at least one module so the schema proves finalization behavior at app import time.
## Test placement rules
Tests under `examples/fakeshop/test_query/` should hit `/graphql/` through `django.test.Client.post(...)` and assert HTTP status, GraphQL response JSON, and query counts where relevant.
Tests under `examples/fakeshop/tests/` should continue to cover in-process schema execution, services, models, admin, commands, URLs, and project wiring that does not need HTTP.
Tests under `tests/` should remain the home for package internals, direct helper tests, invalid Meta behavior, registry lifecycle, finalizer atomicity, optimizer cache-key construction, and tests that need monkeypatching or synthetic failure states.
## High-value migrations to HTTP tests
Definition-order and relation traversal should move first. Candidate source tests include `tests/types/test_definition_order_schema.py:22`, `tests/types/test_definition_order.py:33`, `tests/types/test_definition_order.py:55`, and `tests/types/test_definition_order.py:122`. The HTTP replacement should query nested FK and reverse-FK paths and prove the schema works after real app import/finalization.
OneToOne and M2M should move out of the test fixture app. Candidate source tests include `tests/types/test_definition_order.py:77`, `tests/types/test_definition_order.py:96`, `tests/types/test_definition_order_schema.py:51`, and `tests/optimizer/test_definition_order.py:39`. The HTTP replacement should query both sides of OneToOne and M2M relationships using real tables.
Relation resolver correctness should become API behavior. Candidate source tests include `tests/types/test_resolvers.py:58`, `tests/types/test_resolvers.py:97`, and, if a no-optimizer endpoint or schema variant is useful, `tests/types/test_resolvers.py:398`.
Optimizer query-count behavior is the highest-value HTTP migration after relation traversal. Candidate source tests include `tests/optimizer/test_extension.py:51`, `tests/optimizer/test_extension.py:82`, `tests/optimizer/test_extension.py:118`, `tests/optimizer/test_extension.py:160`, `tests/optimizer/test_extension.py:201`, `tests/optimizer/test_extension.py:247`, `tests/optimizer/test_extension.py:328`, `tests/optimizer/test_extension.py:1275`, `tests/optimizer/test_extension.py:1309`, `tests/optimizer/test_extension.py:1381`, `tests/optimizer/test_extension.py:2018`, and `tests/optimizer/test_extension.py:2054`.
Consumer-shaped queryset behavior should be proven through HTTP once the example schema has root fields that intentionally return pre-shaped querysets. Candidate source tests include `tests/optimizer/test_extension.py:2277`, `tests/optimizer/test_extension.py:2319`, and `tests/optimizer/test_extension.py:2354`.
Optimizer hints can become HTTP tests if the example schema contains a type or root field configured with `OptimizerHint.SKIP` and `OptimizerHint.prefetch_related()`. Candidate source tests include `tests/optimizer/test_extension.py:1678` and `tests/optimizer/test_extension.py:1715`.
Manual relation override behavior should be proven by response data rather than Strawberry-internal resolver inspection. Candidate source tests include `tests/types/test_definition_order.py:174`, `tests/types/test_definition_order.py:201`, `tests/types/test_definition_order.py:230`, and `tests/optimizer/test_definition_order.py:146`.
Choice enum and scalar schema shape can move later if the new app includes appropriate fields. Candidate source tests include `tests/types/test_converters.py:105`, `tests/types/test_converters.py:233`, `tests/types/test_base.py:224`, `tests/types/test_base.py:305`, and `tests/types/test_base.py:317`.
## Tests that should stay package-level
Registry tests in `tests/test_registry.py` should stay under `tests/` because they directly validate registry state, idempotency, clear behavior, phase-1 failure atomicity, phase-3 partial mutation, and retry behavior.
Configuration and error tests should stay under `tests/`, including missing/unknown Meta keys, invalid optimizer hints, unsupported fields, unresolved relation target errors, class-attribute shadowing, enum sanitization collisions, grouped choices, and nullable conversion edge cases.
Optimizer internals should stay under `tests/`, including cache-key construction, directive variable collection, operation-name separation, eviction, `_resolve_model_from_return_type`, `_stash_on_context`, `_optimizer_active`, `plan_relation`, `FieldMeta.from_django_field`, and walker unit tests.
Utility tests under `tests/utils/` should stay as unit tests.
## Migration strategy
Start by adding the real example app and schema without deleting existing package tests. The first HTTP tests should be additive and should cover a narrow end-to-end path: seed data, POST to `/graphql/`, nested relation response, and query count.
Once an HTTP test proves the same public behavior more realistically, downgrade the corresponding package test to a smaller internal assertion or remove the duplicate if it no longer adds unique value.
Move OneToOne and M2M off `tests.fixtures.cardinality_models.py` only after the new example app has real migrations and HTTP coverage for both relationship shapes.
Keep package tests that assert exact annotation objects or registry internals until an equivalent internal contract is intentionally no longer needed.
## Validation expectations
The new HTTP test layer should run with `pytest` and Django’s test database, using `django.test.Client` against `/graphql/`.
Focused validation for each migration should include the new `examples/fakeshop/test_query/` tests plus the package tests most likely to be affected by schema/finalization changes.
Release validation should continue to run the full suite when explicitly requested.
## Risks and open decisions
The new app needs a name and placement. A small app under the fakeshop project is simplest, but the name should make clear that it is a framework acceptance app rather than the product-catalog example.
The schema needs to call `finalize_django_types()` exactly once after importing all example `DjangoType`s. This may require tightening registry isolation in tests so package tests and example schema imports do not fight over global state.
HTTP query-count assertions may include request-stack overhead if authentication, middleware, or GraphQL view behavior changes. The tests should count only database queries and avoid brittle assumptions about non-ORM work.
Plan-introspection assertions through `ctx.dst_optimizer_plan` do not naturally survive HTTP JSON responses. Those should usually remain package-level unless a deliberate debug field or test-only extension is introduced, which is not recommended for the first migration.