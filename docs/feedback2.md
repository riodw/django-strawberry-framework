# Review of HEAD Commit 678b1306

Verdict: this is a real DRY pass, but it is not finished. I would not revert
the commit - it does consolidate several duplicated optimizer contracts in the
right direction - but I would not call it done until the child-queryset planning
seam is fixed. The main weakness is not that code was added; it is that some of
the new code centralizes contracts without moving the abstraction boundary far
enough.

The size concern is valid. The full commit is `1348 insertions / 652 deletions`
for a net `+696`. A large part of that is not implementation: `[docs/feedback.md][feedback-md]`
alone adds `420` lines. Excluding that review artifact, the commit is roughly
`+276` lines. The package code is the growth center at `+595 / -321`, net
`+274`; tests, scripts, and fakeshop helpers are nearly flat overall. So the
DRY pass did remove test/script duplication, but the optimizer package grew to
encode shared contracts that were previously implicit or duplicated.

## What Improved

The best part of the commit is that several correctness-sensitive decisions now
have one owner:

- `[plans.py][plans-py]::window_range_plan` is a strong consolidation. The ORM
  window renderer and the lateral SQL renderer now share the same bound,
  marker-row, `sys.maxsize`, and count-requirement decisions. This is the kind
  of DRY that prevents real pagination drift.
- `[nested_fetch.py][nested-fetch-py]::attach_windowed_prefetch` removes the
  duplicated "apply window pagination, wrap in `Prefetch`, attach to plan" body
  between the windowed and lateral strategies. That is a clean strategy seam.
- `[join_taxonomy.py][join-taxonomy-py]::classify_relation_join` is a useful
  shared vocabulary for partition expressions, connector columns, and lateral
  join fields. The old shape required every consumer to rediscover relation
  topology.
- `[plans.py][plans-py]::deferred_loading_of` is the right idea: the private
  `query.deferred_loading` contract should be read in one place.
- `[selections.py][selections-py]::connection_total_count_selected` and
  `[selections.py][selections-py]::connection_has_next_page_selected` correctly
  make plan-time count annotation and resolve-time count consumption use the
  same selection walk.
- `[connection.py][connection-py]::_set_total_count` and
  `[connection.py][connection-py]::_empty_page_connection` remove repeated
  connection-object construction and count-attribute writes without changing the
  observable Relay behavior.
- `[filters/base.py][filters-base-py]::_apply_lookup_predicate` is a good small
  extraction. It keeps the "whole list as one `__in` predicate" fix from
  splitting again between `ArrayFilter` and `GlobalIDMultipleChoiceFilter`.
- `[examples/fakeshop/strategy_schemas.py][strategy-schemas-py]`,
  `[examples/fakeshop/graphql_client.py][graphql-client-py]`, and
  `[tests/optimizer/conftest.py][tests-optimizer-conftest-py]` are good test
  harness consolidation starts.

I also rechecked the prior `.only()` plus optimizer `select_related()` crash
class with a direct compile probe. The current ordering in
`[extension.py][extension-py]::DjangoOptimizerExtension.optimize_queryset`
prunes unsupported `select_related` paths before publishing strictness metadata
and before applying the plan. A probe with `Item.objects.only("name")` and a
planned `select_related("category")` now prunes to an empty select plan and
compiles.

## Findings

### P1. Child queryset construction is still at the wrong abstraction boundary

Where: `[walker.py][walker-py]::_plan_connection_relation`,
`[walker.py][walker-py]::_build_prefetch_child_queryset`,
`[walker.py][walker-py]::_build_child_queryset`, and
`[nested_fetch.py][nested-fetch-py]::unwindowable_child_queryset_reason`.

The commit adds the right classifier, but the walker uses it too narrowly and
too early:

```python
if (
    has_custom_get_queryset
    and unwindowable_child_queryset_reason(
        _build_child_queryset(django_field, target_type, info, True),
    )
    is not None
):
    return

child_queryset = _build_prefetch_child_queryset(...)
```

That means a custom target `get_queryset` is called once for the safety probe
and then called again inside `_build_prefetch_child_queryset`. This violates the
DRY goal in the most important place: the visibility hook is the source of the
child queryset contract, and the commit now asks it for the same thing twice.

Why this matters:

- A custom `get_queryset` can be non-trivial. Calling it twice can double
  permission work, query construction work, request-context reads, or accidental
  side effects.
- A non-idempotent hook can pass the probe and return a different queryset to
  the actual plan.
- Unsafe states from the related model's default manager are not classified at
  all when `has_custom_get_queryset` is false. A custom default manager can still
  produce `distinct()`, `values()`, `select_for_update()`, a combined queryset,
  or a sliced queryset. The comment says the build composes only `.all()` plus
  optimizer additions, but `_default_manager.all()` is already consumer code.

Root-cause fix: split "build the base child queryset" from "apply the child
optimization plan" and make the base queryset a single value that flows through
the rest of the planner. A good shape would be:

```python
base_queryset = _build_child_queryset(django_field, target_type, info, has_custom_get_queryset)
reason = unwindowable_child_queryset_reason(base_queryset)
if reason is not None:
    return

child_queryset, sub_plan = _build_prefetch_child_queryset_from_base(
    node_sel,
    django_field,
    target_type,
    parent_plan,
    info,
    runtime_paths,
    base_queryset=base_queryset,
    has_custom_get_queryset=has_custom_get_queryset,
    enable_only=enable_only,
)
```

This removes the duplicate hook call and applies the safety classifier to every
base queryset, including default-manager shapes. It also keeps the pre-build
classification before `.only()` can crash on combined/sliced querysets.

### P1. The unsafe-child-queryset contract is declared strategy-independent, but lateral still partly enforces it itself

Where: `[nested_fetch.py][nested-fetch-py]::unwindowable_child_queryset_reason`
and `[lateral_fetch.py][lateral-fetch-py]::_extract_parent_ids`.

The new classifier says `distinct`, `sliced`, `combined`, `values`, and
`select_for_update` are states no fetch strategy can window safely. That is the
right policy. But because the walker only invokes the classifier for custom
target hooks, other querysets can still reach the strategy layer. Lateral then
has fetch-time fallback checks for some of those states, while the windowed path
does not have the same late guard.

That weakens the DRY contract: one module names the strategy-independent safety
rule, but the enforcement still depends on which backend happens to see the
queryset later.

Fix this together with P1 above: classify the single base child queryset
unconditionally in the walker before any strategy request is created. Then keep
the lateral fetch-time checks as defensive drift guards, not as part of the
primary correctness path.

### P2. `deferred_loading_of` does not satisfy its own defensive contract

Where: `[plans.py][plans-py]::deferred_loading_of`.

The docstring says malformed deferred-loading state returns `None`. It only
catches unpacking errors. A malformed but correctly sized tuple still escapes:

```python
deferred_loading = (None, False)
return frozenset(field_set), bool(defer_flag)
```

I verified that a simple test double with `(None, False)` raises:

```text
TypeError: 'NoneType' object is not iterable
```

Production Django querysets will normally have a valid set here, so this is not
a common runtime bug. It is still a bad defensive helper because this commit
advertises it as the one safe reader of a brittle private contract. The fix is
small: wrap the `frozenset(field_set)` conversion in the same `try` block and
return `None` on `TypeError`.

### P2. The new `WindowRangePlan` is probably in the wrong module

Where: `[plans.py][plans-py]::WindowRangePlan` and
`[plans.py][plans-py]::window_range_plan`.

The helper is pure connection-window arithmetic. It is not specific to
`OptimizationPlan`, and it is now shared by the walker, the ORM window renderer,
and lateral SQL. Architecturally it belongs next to
`[utils/connections.py][utils-connections-py]::derive_connection_window_bounds`
and `[utils/connections.py][utils-connections-py]::is_ambiguous_empty_window`.

Leaving it in `plans.py` works today, but it makes unrelated code import the
optimizer plan module for pagination arithmetic. Moving it to
`utils/connections.py` would make the contract more portable and reduce the
chance that future resolver-side code grows another copy instead of importing
from the optimizer package.

### P2. Test helper code is imported directly from `conftest.py`

Where: `[tests/optimizer/conftest.py][tests-optimizer-conftest-py]`,
`[tests/optimizer/test_nested_fetch.py][test-nested-fetch-py]`, and
`[tests/optimizer/test_lateral_fetch.py][test-lateral-fetch-py]`.

The shared `nested_connection_request` builder is useful, but direct imports
from `tests.optimizer.conftest` are a weak pattern. `conftest.py` is pytest
fixture/configuration surface, not a general helper module. It works because
`tests` is importable as a package, but it creates a brittle precedent and can
interact badly with pytest import modes.

Move the builder to something like `tests/optimizer/builders.py` or
`tests/optimizer/_builders.py`, then import it from there. If a fixture is ever
needed, `conftest.py` can wrap the helper.

### P2. The new `make_django_type` helper is good but under-used

Where: `[examples/fakeshop/strategy_schemas.py][strategy-schemas-py]`,
`[tests/test_relay_connection.py][test-relay-connection-py]`, and
`[tests/test_permissions.py][test-permissions-py]`.

The helper is a good seed, but the commit only converts a small slice of the
dynamic `DjangoType` declarations. The repo still has many local
`type(..., (DjangoType,), {"Meta": ...})` builders, including several in files
this commit touched. Some are special cases and should stay explicit, but many
look mechanically convertible.

If the goal is "DRY as possible," this should become a deliberate test-builder
utility with a clearer home and broader adoption plan. Otherwise it reads as a
third helper style rather than a consolidated one.

Also fix the stale comments introduced by this commit:

- `[tests/test_permissions.py][test-permissions-py]::_make_type` says the
  declaration core is `tests/conftest.py::make_django_type`.
- `[tests/test_relay_connection.py][test-relay-connection-py]` has the same
  wording.

The helper actually lives in `[examples/fakeshop/strategy_schemas.py][strategy-schemas-py]`.

### P2. The GraphQL HTTP helper is too narrow to remove much duplication

Where: `[examples/fakeshop/graphql_client.py][graphql-client-py]` and the live
acceptance tests under `examples/fakeshop/test_query/`.

`post_graphql` is useful, and replacing repeated `Client().post("/graphql/")`
calls is good. But `assert_graphql_data` only covers the exact-data happy path.
The live acceptance suite still has a large amount of repeated:

```python
assert response.status_code == 200
payload = response.json()
assert "errors" not in payload, payload
```

That means the helper added a new abstraction but left most of the DRY payoff
unclaimed. It should grow into a fuller live GraphQL test harness:

- `graphql_payload(query, *, client=None, variables=None)` returning parsed JSON
  after the status-code assert.
- `assert_graphql_success(query, *, client=None, variables=None)` returning the
  `data` payload and failing on GraphQL errors.
- `assert_graphql_data(..., variables=None)` so variable-driven tests do not
  fall back to manual posting.
- `post_graphql_raw(body, *, client=None)` for the raw-body tests currently
  keeping a local helper in `[test_products_api.py][test-products-api-py]`.

That would turn the helper from "one wrapper" into the single live request
contract the acceptance tier actually uses.

### P2. `[docs/feedback.md][feedback-md]` should probably not be part of this implementation commit

The commit title is a code refactor, but it adds a 420-line review artifact.
That accounts for most of the perceived line growth in the full diff. If
`feedback.md` is intentional project documentation for this workstream, keep it.
If it is working feedback, it should not live in the implementation commit.

At minimum, separate the review artifact from the code refactor in commit
history. That makes the DRY implementation easier to audit and keeps future
line-count review from being distorted by non-code text.

### P3. Benchmark bootstrap consolidation is okay, but the SQLite mode still depends on no connection opening during `django.setup()`

Where: `[scripts/_bench_common.py][bench-common-py]::bootstrap_fakeshop_django`
and `[scripts/bench_plan_cache.py][bench-plan-cache-py]`.

The helper preserves the old behavior: call `django.setup()`, then mutate
`settings.DATABASES["default"]["NAME"] = ":memory:"`, then migrate. That works
as long as no import during setup opens the default connection first. It is not
a new regression, but moving it into a shared helper makes the assumption more
important.

If this helper is going to be reused beyond the current benchmark scripts,
consider setting the in-memory database before `django.setup()` in the
`sqlite-memory` branch, or explicitly closing/reconfiguring the connection after
the settings mutation.

## File-by-File Notes

| File | Review |
| --- | --- |
| `[connection.py][connection-py]` | Good DRY work. `_set_total_count`, `_empty_page_connection`, and shared selection predicates reduce real duplication without hiding behavior. |
| `[filters/base.py][filters-base-py]` | Good small extraction. `_apply_lookup_predicate` matches the actual bug class: keep list values whole for `__in`. |
| `[join_taxonomy.py][join-taxonomy-py]` | Useful consolidation. Keep it, but consider adding self-referential M2M coverage because the through-link side swap is easy to regress. |
| `[lateral_fetch.py][lateral-fetch-py]` | Better after `attach_windowed_prefetch` and join descriptor reuse. `_select_columns` should defensively handle `deferred_loading_of(...) is None` if the helper promises unreadable states return `None`. |
| `[nested_fetch.py][nested-fetch-py]` | The new safety classifier is the right abstraction, but the walker must apply it unconditionally to the single built base queryset. |
| `[plans.py][plans-py]` | Strong consolidation for range planning and order parsing. Fix `deferred_loading_of`, and consider moving pure window arithmetic to `utils/connections.py`. |
| `[selections.py][selections-py]` | Good DRY improvement. Count-observability now has one implementation for plan and resolve. |
| `[walker.py][walker-py]` | Main remaining problem. The new helper routing is cleaner, but child queryset construction still happens twice for custom hooks and safety classification is not broad enough. |
| `[utils/connections.py][utils-connections-py]` | `is_ambiguous_empty_window` belongs here and is a good addition. `WindowRangePlan` probably belongs here too. |
| `[examples/fakeshop/graphql_client.py][graphql-client-py]` | Good start, but too narrow for the acceptance suite's repeated success/error envelope checks. |
| `[examples/fakeshop/strategy_schemas.py][strategy-schemas-py]` | Useful shared schema builder. The type-builder half needs a clearer adoption boundary so the repo does not end up with three dynamic-type idioms. |
| `[scripts/_bench_common.py][bench-common-py]` | Useful script DRY. Watch the SQLite setup ordering assumption. |
| `[tests/optimizer/conftest.py][tests-optimizer-conftest-py]` | Helper is useful, but should move out of `conftest.py` if tests import it directly. |

## Bottom Line

This commit is not a fake DRY pass. It does consolidate duplicated contracts
that matter for optimizer correctness. The added code is mostly doing real work.

The commit is also not as DRY as it should be yet. The child-queryset build and
safety gate need a root-cause refactor before this can be considered finished:
build the base child queryset once, classify it once for every relation, and
feed that same queryset into the child plan. After that, clean up the helper
placement/comment drift and either remove `[docs/feedback.md][feedback-md]`
from the implementation commit or separate it into its own commit.

I did not run pytest. I reviewed the `HEAD^..HEAD` diff, read the changed
optimizer and helper files, ran a direct compile probe for the
`.only()`/`select_related()` prune path, and ran a direct malformed
`deferred_loading_of` probe.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[conftest-root]: ../conftest.py

<!-- docs/ -->
[feedback-md]: feedback.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection-py]: ../django_strawberry_framework/connection.py
[extension-py]: ../django_strawberry_framework/optimizer/extension.py
[filters-base-py]: ../django_strawberry_framework/filters/base.py
[join-taxonomy-py]: ../django_strawberry_framework/optimizer/join_taxonomy.py
[lateral-fetch-py]: ../django_strawberry_framework/optimizer/lateral_fetch.py
[nested-fetch-py]: ../django_strawberry_framework/optimizer/nested_fetch.py
[plans-py]: ../django_strawberry_framework/optimizer/plans.py
[selections-py]: ../django_strawberry_framework/optimizer/selections.py
[utils-connections-py]: ../django_strawberry_framework/utils/connections.py
[walker-py]: ../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-lateral-fetch-py]: ../tests/optimizer/test_lateral_fetch.py
[test-lateral-pg-parity-py]: ../tests/test_lateral_pg_parity.py
[test-nested-fetch-py]: ../tests/optimizer/test_nested_fetch.py
[test-permissions-py]: ../tests/test_permissions.py
[test-relay-connection-py]: ../tests/test_relay_connection.py
[tests-conftest-py]: ../tests/conftest.py
[tests-optimizer-conftest-py]: ../tests/optimizer/conftest.py

<!-- examples/ -->
[graphql-client-py]: ../examples/fakeshop/graphql_client.py
[kanban-constants-py]: ../examples/fakeshop/apps/kanban/constants.py
[strategy-schemas-py]: ../examples/fakeshop/strategy_schemas.py
[test-products-api-py]: ../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->
[bench-common-py]: ../scripts/_bench_common.py
[bench-nested-fetch-py]: ../scripts/bench_nested_fetch.py
[bench-plan-cache-py]: ../scripts/bench_plan_cache.py

<!-- .venv/ -->

<!-- External -->
