# Feedback: `docs/spec-019-multi_db-0_0_7.md`

Overall: the spec has the right strategic boundary. Treating multi-database support as a cooperation contract, not a new public API, is the correct posture for `0.0.7`. The strongest parts are the explicit non-goals, the zero-public-export stance, the split between hermetic package tests and fakeshop sharded coverage, and the repeated reminder that first-class sharding-aware planning belongs in `BACKLOG.md` item 41.

The main issue is that a few contract statements overclaim what the current code can prove without production changes. Tighten those before implementation so the tests pin real behavior instead of forcing a bigger feature than the card intends.

## High-priority corrections

### 1. Do not claim implicit router querysets get `_db` set before optimizer planning

The spec says, in the implicit `DATABASE_ROUTERS` usage section, that “the `_db` attribute is set on the queryset before the optimizer's plan application.” That is not generally how Django querysets work. For implicit router use, a queryset can keep `_db is None`; Django consults `queryset.db` / the router at evaluation time.

Recommended rewrite:

- Explicit `.using(alias)` path: the package preserves the queryset's explicit `_db` through `only()`, `select_related()`, and `prefetch_related()`.
- Implicit router path: the package does not force an alias; it leaves `_db` unset and lets Django route evaluation through the registered routers.
- FK-id elision stubs: the package explicitly calls `router.db_for_read(related_model, instance=parent_or_none)` because those stubs are freshly constructed model instances and do not inherit a queryset alias.

This keeps the contract accurate for both `.using()` and router-driven deployments.

### 2. The `get_queryset` / `Prefetch` alias-preservation test is probably over-specified

The planned test `test_get_queryset_downgrade_preserves_using_alias_on_prefetch` asserts that a generated `Prefetch` has `queryset._db == "shard_b"` after planning from a parent `Model.objects.using("shard_b")` queryset.

Current code does not pass the parent queryset into `walker.plan_optimizations(...)`. `_build_child_queryset(...)` starts from:

- `field.related_model._default_manager.all()`
- then optionally `target_type.get_queryset(queryset, info)`

So the generated child queryset will not automatically have the parent queryset's `_db` at plan-construction time. Depending on Django's prefetch internals, actual evaluation may still route correctly via instance hints, but the pinned assertion on `Prefetch.queryset._db` is not supported by the current code.

Pick one of these two directions:

1. Keep “zero production code change” and narrow the contract:
   - The optimizer preserves explicit aliases on the root queryset.
   - Consumer-provided `Prefetch(queryset=SomeModel.objects.using(...))` keeps its own `_db`.
   - Generated child querysets do not promise `_db == parent._db` at plan-construction time; Django router / instance hints own that path at evaluation time.
2. Expand the card into a production-code card:
   - Thread the root queryset alias into generated `Prefetch` child querysets.
   - Then the test asserting `Prefetch.queryset._db == "shard_b"` becomes valid.

For this card, option 1 fits the stated scope better.

### 3. `plan_optimizations(...)` cannot test queryset alias preservation by itself

The spec says to “run a GraphQL selection through `walker.plan_optimizations` against a queryset constructed via `Model.objects.using("shard_b").all()`.” `plan_optimizations(...)` accepts selections and a model; it does not accept a queryset.

Recommended test shape:

- Build a plan with `plan_optimizations(...)`.
- Apply it to `Model.objects.using("shard_b").all()` via `plan.apply(qs)`, then assert the resulting queryset's `_db == "shard_b"`.
- Or test at the `DjangoOptimizerExtension` level by returning a `.using("shard_b")` queryset from a resolver and inspecting the optimized result / executed connection behavior.

This is a test-plan wording fix, not necessarily a source-code issue.

### 4. Split resolver tests from optimizer tests unless intentionally overriding `docs/TREE.md`

The planned `tests/optimizer/test_multi_db.py` includes tests for `_build_fk_id_stub(...)` and `_check_n1(...)`, which live in `django_strawberry_framework/types/resolvers.py`.

Per the existing mirror pattern, those direct unit tests belong in `tests/types/test_resolvers.py`, where FK-id elision resolver coverage already exists. `tests/optimizer/test_multi_db.py` should focus on `OptimizationPlan`, `walker`, `plans.diff_plan_for_queryset(...)`, and extension-level optimizer behavior.

Suggested split:

- `tests/types/test_resolvers.py`
  - FK-id elision stub calls `router.db_for_read`.
  - Router call passes `instance=<parent_row>`.
  - Router call passes `instance=None` when the parent lacks `_state`.
  - Null FK returns `None` and does not call the router.
  - Strictness still raises for objects whose `_state.db` is non-default, if you want a direct `_check_n1` pin.
- `tests/optimizer/test_multi_db.py`
  - `OptimizationPlan.apply(...)` preserves root queryset `_db`.
  - `diff_plan_for_queryset(...)` preserves queryset `_db`.
  - Generated / consumer-provided `Prefetch` behavior under `.using(...)`, with the narrowed contract from item 2.

If the single-file placement is deliberate because the KANBAN card names `tests/optimizer/test_multi_db.py`, state that this is an intentional exception to the mirror rule.

### 5. The null-FK and parent-lacks-`_state` cases are conflated

The checklist says the FK-id elision stub returns `None` for a `None` FK and that “the `instance` arg is forwarded as `None` when the parent row has no `_state` attribute.” These are separate branches.

Current resolver behavior:

- If `related_id is None`, `_build_fk_id_stub(...)` returns `None` before calling `router.db_for_read(...)`.
- If the parent lacks `_state` but has a non-null FK id, the stub is built and `router.db_for_read(..., instance=None)` is called.

Recommended tests:

- `test_fk_id_elision_returns_none_for_null_fk_and_does_not_call_router`
- `test_fk_id_elision_router_call_passes_none_instance_when_parent_lacks_state`

Do not combine them into one assertion.

### 6. Strictness mode does not “track the originating connection”

`_check_n1(...)` is connection-agnostic. It checks:

- whether the resolver key was planned;
- whether the relation is cached / prefetched;
- whether strictness is `off`, `warn`, or `raise`.

It does not inspect `root._state.db`, `queryset._db`, or `router.db_for_read(...)`. That is fine, but the spec should not say strictness “tracks the originating connection.”

Recommended wording:

- “Strictness mode remains active for objects loaded from any database alias.”
- “The package does not re-route strictness checks; Django owns which alias a lazy load would use.”
- “The error class and message are unchanged under non-default aliases.”

The test can set `root._state.db = "shard_b"` to prove the object shape is accepted, but it cannot prove connection routing unless it performs a real lazy load. With strictness set to `raise`, the lazy load is intentionally prevented.

## Fakeshop live-test corrections

### 7. Live `/graphql/` HTTP and inline schema execution are different contracts

The spec requires live `/graphql/` HTTP tests, then later says in-process `_test_schema.execute_sync(...)` is acceptable. Those are not equivalent.

If the requirement is live HTTP, pin one concrete implementation:

- Use `django.test.Client.post("/graphql/", ...)`.
- Provide a temporary URLConf with `urlpatterns = [path("graphql/", GraphQLView.as_view(schema=_test_schema))]`.
- Wrap tests with `override_settings(ROOT_URLCONF=<test_module_urlconf>)`.
- Call `clear_url_caches()` during setup / teardown.

If in-process execution is acceptable, move the tests to `examples/fakeshop/tests/` or clearly mark them as non-HTTP. Given `AGENTS.md`'s live-query rule, live HTTP is the better fit here.

### 8. Multi-db Django tests need explicit database access markers

Any test that writes or reads `shard_b` under `pytest-django` should declare access to that database. Use one of:

- `@pytest.mark.django_db(databases=["default", "shard_b"])`
- `@pytest.mark.django_db(databases="__all__")`

Without this, pytest-django can block access to `shard_b` even when `FAKESHOP_SHARDED=1` has registered the alias.

### 9. Book seeding is not “no relations needed”

The fakeshop live tests propose seeding `Book` rows with “minimal fixtures, no relations needed.” `Book` has a non-null FK to `Shelf`, and `Shelf` has a non-null FK to `Branch`.

Each alias used in the live tests needs at least:

- `Branch.objects.using(alias).create(...)`
- `Shelf.objects.using(alias).create(branch=branch, ...)`
- `Book.objects.using(alias).create(shelf=shelf, ...)`

The shard-isolation test should seed a complete branch/shelf/book chain on `default` and a separate chain on `shard_b`.

### 10. The pinned module header includes unnecessary duplicate pytest import / `# noqa`

Decision 6's sample header imports `pytest`, then later imports `pytest as _pytest_for_fixtures  # noqa: F401`. That contradicts the checklist's “No `# noqa` suppressions” rule and is unnecessary.

Keep one `import pytest` before the module-level skip block; fixtures below can use that same name.

## Spec hygiene corrections

### 11. The pydocstyle / annotation wording is inconsistent

The Slice 1 checklist says test docstrings are required by `D100` / `D102` because `tests/**` is not effectively ignored. But `pyproject.toml` has:

- `tests/**/*.py = ["D", "ANN", ...]`
- `examples/**/*.py = ["D", "ANN", ...]`

So docstrings and annotations in tests/examples are convention, not a ruff gate. Also, the missing-docstring code for free test functions would be `D103`, not `D102`.

Recommended rewrite:

- “Add module and test docstrings to match existing style.”
- “Do not add `# noqa` suppressions for docstring or annotation rules; they are unnecessary under the current per-file ignores.”

### 12. The terms CSV should not map `Meta.preferred_database` to the multi-db anchor

`docs/spec-019-multi_db-0_0_7-terms.csv` maps `Meta.preferred_database` to `multi-database-cooperation`. That is misleading: `Meta.preferred_database` is a hypothetical future key and does not have that glossary heading.

Preferred options:

1. Remove `Meta.preferred_database` from the CSV and leave it as plain out-of-scope prose in the spec.
2. Add a real glossary entry for `Meta.preferred_database` if the project wants to reserve that future surface explicitly.

Do not anchor one concept to a different concept just to satisfy the checker.

### 13. The spec filename / archive path should be made explicit once

The active spec lives at `docs/spec-019-multi_db-0_0_7.md`, but several completion/update bullets refer to the archived path `docs/SPECS/spec-019-multi_db-0_0_7.md`.

That can be correct if the workflow is:

1. active WIP spec at `docs/spec-019-multi_db-0_0_7.md`;
2. implementation lands;
3. archive pass moves it to `docs/SPECS/spec-019-multi_db-0_0_7.md`;
4. KANBAN Done entry points at the archived path.

Add one short note near Decision 1 or Slice 3 explaining that distinction. Otherwise future implementers may think the spec is already expected under `docs/SPECS/`.

## Suggested wording changes

- Replace “the stub's `_state.db` matches the parent row's routing context” with “the stub's `_state.db` is whatever `router.db_for_read(...)` returns when given the parent row as the `instance=` hint.”
- Replace “strictness mode tracks the originating connection” with “strictness mode remains active for rows loaded from any alias; Django owns the alias used by any lazy load that strictness permits.”
- Replace “`Prefetch` chains respect routing” with the narrower “consumer-provided `Prefetch(queryset=...)` objects keep their own queryset alias; generated `Prefetch` querysets do not intentionally discard aliases they are given.”
- Replace “the router decides the connection at queryset evaluation time; the `_db` attribute is set on the queryset before optimizer plan application” with “the router decides the connection at evaluation time when `_db` is unset; the optimizer preserves explicit aliases and otherwise leaves routing to Django.”

## Bottom line

The spec is close, but it should be tightened before implementation. The biggest decision is whether this remains a zero-production-code tests/docs card. If yes, narrow the `get_queryset` / generated-`Prefetch` and strictness claims. If no, explicitly promote the card into a production-code change that threads database aliases into generated child querysets.