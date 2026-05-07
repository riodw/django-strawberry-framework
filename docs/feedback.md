# Review: `docs/spec-testing_shift.md`

> Round-4 foundation review feedback (N-1 through N-6) is no longer in this file. Those items have moved to `KANBAN.md` under `IN-PROGRESS-002 — 0.0.4 release polish`. This file is now feedback on the testing-shift spec.

## Verdict

The shift is the right direction and the spec correctly draws the unit/integration line. The migration list is concrete and actionable. Before approving, the spec needs to resolve seven concrete questions (named "Q-1" through "Q-7" below) and tighten the migration list so genuinely package-level tests are not promoted to HTTP. The strategy section needs a per-feature add-then-remove cycle, and the new app's interaction with the existing package-test registry-isolation pattern needs a documented answer.

## What the spec gets right

- Clear problem statement: tests under `tests/types/test_definition_order_schema.py` and the cardinality fixtures **work**, but they prove a public surface through synthetic apparatus rather than the real Django + Strawberry view stack. The shift is well-motivated.
- The non-goals section ("Do not activate unshipped Layer 3 API … Do not require full production readiness") is calibrated correctly: this is an acceptance-coverage shift, not a Layer 3 expansion.
- Test placement rules (`## Test placement rules`) cleanly partition the three trees: HTTP under `examples/fakeshop/test_query/`, in-process schema under `examples/fakeshop/tests/`, package internals under `tests/`. This matches the existing `examples/fakeshop/test_query/README.md` reservation and the `pytest.ini` `testpaths` already covers all three.
- The list of tests that **stay** package-level (`## Tests that should stay package-level`) is the strongest part of the spec. Registry idempotency, configuration error paths, optimizer cache-key construction, and utility tests all belong where they are.
- The risks section flags the cardinality-fixture / app-registry tension, which is the same concern tracked under `KANBAN.md` `BACKLOG-010` (cardinality fixture's `INSTALLED_APPS` line in the example settings).

## Significant concerns

### Q-1. The new app needs a name, a placement, and a one-paragraph rationale before any code lands

The spec says "the name should make clear that it is a framework acceptance app rather than the product-catalog example" but leaves both the name and the placement open. Two viable options:

1. **In-project app**: `examples/fakeshop/fakeshop/framework/` (or `acceptance/`) with `app_label = "framework"`. Cheapest in churn; one new app entry in `INSTALLED_APPS`.
2. **Separate example project**: `examples/framework_proving/`. Keeps the fakeshop products catalog as a clean cookbook reference (per `GOAL.md` "Cookbook parity"). More plumbing (a second `manage.py`, second `settings.py`, second `urls.py`, second `pytest` settings module).

I recommend option 1 with the name `framework`, on the grounds that:
- `GOAL.md` already says fakeshop's products schema should grow into the rich-schema showcase (filters / orders / aggregates / connection fields). Mixing a tiny acceptance app *next to* that showcase is fine; growing a second project is overhead the single-maintainer team does not need yet.
- The existing `pytest.ini` `DJANGO_SETTINGS_MODULE = examples.fakeshop.fakeshop.settings` and `testpaths` already cover this layout. Option 2 doubles every settings/test-paths change.

Whichever option the spec picks, it needs to land in the spec **before** the migration list is touched, because the new app's name appears in every HTTP-test path written under it.

### Q-2. Where exactly does `finalize_django_types()` get called, and what is the contract with package tests?

The spec says (under "Risks") "the schema needs to call `finalize_django_types()` exactly once after importing all example `DjangoType`s." It does not say where the call lives. The right answer per `docs/spec-foundation.md:62-63` is "after every module that defines `DjangoType` classes has been imported, and before `strawberry.Schema(...)` construction." For the proposed app, that is one of:

- **In `examples/fakeshop/fakeshop/schema.py`** between the per-app Query imports and `strawberry.Schema(query=Query)` (the current shape of that file makes this a one-line addition).
- **In the new app's `schema.py`** before the app exposes its `Query`.
- **In an `apps.py:ready()`** hook on the new app.

The `schema.py` placement is the only one consistent with the foundation spec's recommended pattern; the README quick-start at `README.md:80-86` already shows that shape. Pin it in the spec.

This question matters more than it looks because of **package-test interaction**:

- `pytest.ini` sets `DJANGO_SETTINGS_MODULE = examples.fakeshop.fakeshop.settings`. Every test process — including package tests under `tests/` — imports the fakeshop settings. If `fakeshop/schema.py` is imported during test collection, it finalizes the registry once at module import time. The registry is now finalized for the rest of the process.
- The package tests under `tests/` rely on autouse `_isolate_registry` fixtures that call `registry.clear(); yield; registry.clear()` so each test redeclares its types. After this shift, `registry.clear()` resets the `_finalized` flag, but the new acceptance-app's `DjangoType` classes still carry their `__strawberry_definition__` mutations from the import-time finalization. They cannot be re-finalized; new test-local `DjangoType` classes can.
- Practical implication: the `_isolate_registry` pattern keeps working for **package tests that declare their own types in the test function**. It does **not** revive the acceptance app's types. That is fine — the acceptance app's types are only used in HTTP tests, which are the *consumer* of the finalized schema, not declarers of new types.

The spec needs one paragraph documenting this contract explicitly:

> The new app's `DjangoType` subclasses are declared at module import time and finalized once when `examples/fakeshop/fakeshop/schema.py` is imported. Package tests under `tests/` continue to use the autouse `_isolate_registry` fixture; that fixture clears the registry between tests, so package tests can still declare their own short-lived `DjangoType` classes. Package tests **must not** assume the acceptance app's types are present — they are not, after the first `registry.clear()`.

### Q-3. The migration list includes tests that fundamentally cannot move to HTTP

Three categories must be filtered out of the "high-value migrations" section:

#### Q-3a. Declaration-order tests in `tests/types/test_definition_order.py`

The whole point of `test_reverse_fk_resolves_when_parent_declared_before_child` and `test_reverse_fk_resolves_when_child_declared_before_parent` (and the OneToOne / M2M counterparts) is that the test functions **declare `DjangoType` subclasses inside the test body in a controlled order**. An HTTP test cannot do that — the schema has been finalized once, in whatever order the acceptance app declares its types. By the time the request hits `/graphql/`, the order question is already settled.

The migration list cites `tests/types/test_definition_order.py:33`, `:55`, `:77`, `:96`, `:122`, `:174`, `:201`, `:230`. Of those:

- `:33` and `:55` (parent-first vs child-first reverse FK) **must stay package-level**. The HTTP layer can prove that the acceptance app's specific order works, but cannot prove order-independence.
- `:77` (OneToOne forward + reverse) and `:96` (M2M forward + reverse) **can move to HTTP** because the HTTP test only needs to prove the cardinality maps correctly — it does not need to permute declaration order. Keep one or two declaration-order permutation tests for these cardinalities at package level.
- `:122` (multi-cycle) **can move to HTTP** for the same reason; keep the package-level multi-cycle test as a regression pin.
- `:174`, `:201`, `:230` (override cases) — see Q-4 below.

#### Q-3b. Plan-introspection tests in `tests/optimizer/test_extension.py`

A non-trivial fraction of `test_extension.py` asserts on `info.context.dst_optimizer_plan`, `info.context.dst_optimizer_fk_id_elisions`, `info.context.dst_optimizer_planned`, FK-id elision sets, and strictness-mode raise/warn behavior. These have no JSON wire representation. The migration list at `:328`, `:1275`, `:1309`, `:1381`, `:2018`, `:2054` needs to be re-checked one by one — without seeing each test body, my read is that several of these are plan-shape assertions, not response-data assertions.

Recommendation: split the migration list into two columns:

- **Response-data tests** → migrate to HTTP.
- **Plan-shape tests** → stay package-level.

The spec already concedes this in its last bullet under "Risks" ("Plan-introspection assertions through `ctx.dst_optimizer_plan` do not naturally survive HTTP JSON responses"). That concession needs to flow into the migration list itself, not sit at the bottom as an afterthought.

#### Q-3c. Resolver-internal coupling tests

`tests/types/test_resolvers.py` includes tests that assert on `field.base_resolver.wrapped_func.__name__` and similar Strawberry-internal attribute paths. These were already flagged for follow-up in `KANBAN.md` `BACKLOG-011`. Promoting them to HTTP is the right move *only if* the test asserts on response data (which it can do once a real schema executes). Promoting them to HTTP without rewriting the assertion does nothing — the HTTP boundary cannot see resolver internals.

### Q-4. Manual-override tests are HTTP candidates only when they assert on response data

The spec is right that "manual relation override behavior should be proven by response data rather than Strawberry-internal resolver inspection" (`tests/types/test_definition_order.py:174`, `:201`, `:230`). Concrete check before migration:

- `:230` (`test_decorator_relation_field_override_routes_schema_query_through_consumer_resolver`) is **already** a schema-execution test that asserts response data. Easy promotion.
- `:174` (`test_annotation_only_relation_override_keeps_generated_resolver`) and `:201` (`test_assigned_relation_field_override_keeps_consumer_resolver`) currently assert on `base_resolver.wrapped_func.__name__`. Promoting them to HTTP requires **rewriting** the assertion to fire a query and observe whose code ran. Do not just relocate; rewrite. This is the cheapest concrete payoff for the testing shift, and it incidentally addresses `BACKLOG-011`.

### Q-5. Query-count assertion shape needs to be pinned

The spec says "HTTP query-count assertions may include request-stack overhead. The tests should count only database queries and avoid brittle assumptions about non-ORM work." Concrete recommendation:

- Use `django.test.utils.CaptureQueriesContext(connection)` — narrower than `assertNumQueries` because it captures only the queries that ran inside the `with` block.
- Assert on **both** count and SQL shape. Pure count assertions pass when the optimizer regresses from one `select_related` JOIN to two sequential SELECTs (still a count of "2", but a different shape). Couple every count assertion with a substring or regex over `ctx.captured_queries[i]["sql"]` for the JOIN / LEFT OUTER JOIN / WHERE structure.
- Do **not** wrap the entire `client.post(...)` call in a single `CaptureQueriesContext`. Wrap only the GraphQL execution step if you can isolate it; otherwise, accept that auth / session / CSRF middleware queries will be in the count and assert against the **delta** (start with a no-op POST baseline, then subtract).

This belongs in the spec's "Validation expectations" section as a worked example.

### Q-6. The acceptance app's models need migrations and a name-collision check

`tests/fixtures/cardinality_models.py` declares `User`, `Profile`, `Author`, `Tag`, `Book` as `managed = False`. The acceptance app needs **real** managed models so the test database has actual tables for the OneToOne and M2M cases. That implies:

- `examples/fakeshop/fakeshop/framework/models.py` (or wherever Q-1 lands)
- `examples/fakeshop/fakeshop/framework/migrations/0001_initial.py`
- `pytest-django`'s `django_db_setup` fixture runs the migration once per session (already wired in the existing `tests/test_definition_order_schema.py`).

Naming concern: the cardinality fixture's `User` model conflicts with `django.contrib.auth.User` if the acceptance app uses the same name. The fixture currently lives under `app_label = "tests_cardinality"` so there is no collision today, but a contributor renaming an acceptance-app model to `User` would shadow the auth model in admin/error messages. Recommend renaming to `Person` (or `OneToOneOwner`) in the acceptance app to avoid the trap. Pin the rename in the spec.

### Q-7. Test-data seeding and pytest style need explicit choices

The existing fakeshop example tests use `services.seed_data(1)` (Faker-driven). For acceptance tests, deterministic test data is better than Faker variance:

- **Recommended**: each test calls `Model.objects.create(...)` inline at the start of the test body. No fixtures, no factories, no Faker. Two consequences: (a) query-count assertions are stable across reruns; (b) the acceptance app does not need its own `services.py`.
- **Alternative**: a small `factories.py` per relationship shape. More machinery, but reusable.

Pin the choice in the spec.

Pytest style: the existing `examples/fakeshop/tests/test_schema.py` and the new HTTP files should both use **pytest-django functional style** (`@pytest.mark.django_db` plus `client = django.test.Client()` from a fixture) rather than `unittest.TestCase` subclasses. The `pytest-django` plugin is already a dev dependency. Pin this so the first HTTP test is not bikeshed material.

CSRF: `django.test.Client()` defaults to `enforce_csrf_checks=False`, and Strawberry's `GraphQLView` accepts POSTs without CSRF tokens by default in dev. The spec should add one sentence noting that production hardening (CSRF middleware on the GraphQL endpoint) is out of scope and that acceptance tests run with default `Client()`.

## Smaller items

- **Naming**: "IRL" in the title and intro reads casually. Consider "End-to-end HTTP test shift" or "Live API test shift" for a contract document.
- **Headings**: `## Tests that should stay package-level` and `## Test placement rules` are siblings, but conceptually the former is a subset of the latter. Consider nesting.
- **File:line drift**: like `docs/spec-foundation.md:553-554`, this spec's migration list cites in-repo line numbers (`test_extension.py:51`, `:1275`, etc.). Add a one-sentence "line numbers may drift; verify against the symbol name before migrating" caveat at the top of the migration section.
- **Migration grouping**: the optimizer migration list is ~12 line refs in one paragraph. Group by what each test proves (relation traversal vs `only()` projection vs FK-id elision vs queryset cooperation vs strictness mode vs hints), so reviewers can decide which groups are HTTP candidates without opening each line ref.
- **AGENTS.md**: `examples/fakeshop/tests/test_schema.py:3-4` references AGENTS.md as the source of "schema is tested via `schema.execute_sync` … never by calling resolver methods directly". The new HTTP testing rule needs to land in AGENTS.md too, otherwise contributors will keep writing in-process schema tests for HTTP-shaped behavior.
- **`finalize_django_types()` mention in `examples/fakeshop/tests/test_schema.py`**: today's two tests there (`test_products_schema_executes_hello`, `test_project_schema_executes_hello`) build their own `strawberry.Schema(query=ProductsQuery)` and execute it. Once the acceptance app ships a real schema, consider pruning these to a single `test_project_schema_imports_without_error` test, since `hello` becomes redundant against the new HTTP coverage.

## Recommended additions before approval

1. **App name and placement** — a concrete paragraph naming the app, its `app_label`, and where it lives in the tree (Q-1).
2. **Finalization seam contract** — one paragraph fixing where `finalize_django_types()` is called and how that interacts with the package-test `_isolate_registry` autouse fixture (Q-2).
3. **Re-graded migration list** — split high-value migrations into "response-data" (HTTP candidates) and "plan-introspection / declaration-order / resolver-internal" (stay package-level) (Q-3, Q-4).
4. **Query-count assertion shape** — `CaptureQueriesContext` plus SQL-shape assertions, with a worked example (Q-5).
5. **Acceptance-app models** — model list, migration plan, and explicit `User → Person` rename (Q-6).
6. **Test-data shape and pytest style** — inline `Model.objects.create(...)`, pytest-django functional style, default `Client()` (Q-7).
7. **Per-feature add-then-remove migration cycle** — explicit step ordering: add app + migration → run existing suite (no regression) → add HTTP smoke test → migrate one feature category (start with reverse-FK traversal) → only then downgrade or remove the package test. The current "Migration strategy" section gestures at this but doesn't enumerate.
8. **Cross-references** — the testing shift naturally subsumes `BACKLOG-010` (cardinality fixture's `INSTALLED_APPS` line in the example project settings) and partially addresses `BACKLOG-011` (durable override-test pattern). Add a "## Cross-references" section linking to those Kanban cards and to `GOAL.md`'s "Cookbook parity" target so the spec reads as a long-term direction, not a one-time refactor.

## Things the spec correctly leaves out

- It does not propose moving `tests/test_registry.py` to HTTP. Correct — registry idempotency, phase-1 atomicity, phase-3 partial-mutation contract, and pending-set cleanup all need direct registry access.
- It does not propose activating Layer 3 features as part of the shift. Correct — that would conflate two unrelated changes.
- It does not propose deleting `tests/fixtures/cardinality_models.py` immediately. Correct — package tests still use it for in-test-function declaration-order coverage.
- It does not propose moving `tests/utils/` tests. Correct — those are pure unit tests with no Django/Strawberry involvement.

## Closing note

The shift will be a net win for both confidence and contributor onboarding — a cookbook-parity acceptance suite is the right shape for proving the framework end-to-end. The current spec is roughly 70% there. The seven Q-items above are mostly local clarifications, not architecture changes; the spec can close them in one editing pass.
