# Review: `django_strawberry_framework/permissions.py`

Status: verified

## Understanding

`apply_cascade_permissions` walks the owning `DjangoType` model's single-column concrete forward
foreign-key / one-to-one edges, resolves each target model's registered primary type, invokes the
target visibility hook against a database-pinned default-manager queryset, and intersects the
target's visible target-column subquery into the caller queryset. Nullable edges retain rows with a
`NULL` relation; unregistered target models are skipped. `fields=None` walks every supported edge,
`fields=[]` is the explicit zero-edge scope, and malformed or unsupported scopes fail closed.

The walk carries immutable `ContextVar` state for the root alias, active type tuple, and edge path.
Cycle re-entry raises a path-rich `ConfigurationError`; nested hooks compose transitively; each
token resets in `finally`, including the async wrapper's single `sync_to_async` worker boundary.
Target hook results use the shared sealed visibility boundary, which validates model/table/alias
state, rejects async hooks in the sync walk with `SyncMisuseError`, and re-projects accepted results
onto the edge's actual target column. The helper is consumed by the fakeshop products `DjangoType`
hooks, whose live HTTP paths exercise row visibility before connection pagination, filters, orders,
optimizer planning, and mutation lookup visibility.

The assigned baseline had no `permissions.py` diff. The review traced `permissions.py` together with
the shared queryset visibility boundary, registry, optimizer/list/connection callers, mutation
lookup paths, filter/order permission composition, request/user context handling, and the fakeshop
live GraphQL permission tests.

## Verification

- Existing focused baseline: `uv run pytest --no-cov tests/test_permissions.py
  tests/utils/test_permissions.py` — 94 passed, 1 skipped.
- The disposable probe in `docs/review/temp-tests/permissions/test_root_filter_override.py`
  reproduced a root-queryset bypass: a `QuerySet` subclass whose `.filter()` returned an
  unfiltered base caused a parent pointing at a hidden target to survive the cascade.
- The root helper previously checked `QuerySet` shape and then dispatched the consumer-owned
  `.filter()` directly. The outer hook-result seal could not detect that the required cascade
  predicate had never entered the query state.
- The fakeshop paths were traced and exercised over real `/graphql/` HTTP:
  `test_cascade_anonymous_sees_no_entries_under_private_categories`,
  `test_cascade_view_item_user_respects_category_visibility`,
  `test_cascade_view_entry_user_nested_selection_drops_hidden_targets`,
  `test_cascade_query_count_fixed`, and
  `test_cascade_composes_with_filter_and_order_live` — 5 passed.
- After the fix: `uv run pytest --no-cov tests/test_permissions.py tests/utils/test_permissions.py`
  — 95 passed, 1 skipped.
- `uv run ruff format .` and `uv run ruff check --fix .` — passed.

## Improvements

### High

- **Root cascade predicates could be erased by a consumer queryset override.**
  - **Observation:** `apply_cascade_permissions` accepted a root queryset after structural checks but
    composed each edge with `queryset.filter(condition)`. A subclass or instance-shadowed method
    could return an unfiltered queryset, so the required visibility predicate never reached the
    query state.
  - **Evidence:** The disposable probe used a `FilterEraser(models.QuerySet)` whose `filter()` always
    returned `_CtParent.objects.all()`. Before the implementation change, both visible and hidden
    parents were returned despite the target hook excluding the hidden target.
  - **Impact:** A consumer-defined queryset shape inside its own visibility hook could silently
    bypass cascade visibility while still producing a queryset accepted by the outer shared seal.
    This undermined the fail-closed contract specifically at the root composition boundary.
  - **Recommendation:** Seal the root input through the shared
    `utils/querysets.py::_prepared_visibility_source` boundary before validating fields or
    dispatching cascade `.filter()` calls. The boundary reconstructs a framework-owned plain
    queryset, preserves the effective alias, and rejects untrusted query state before the cascade
    adds predicates.
  - **Proof:** `tests/test_permissions.py::test_root_queryset_filter_override_is_neutralized_by_sealing`
    uses the hostile queryset and confirms the hidden-target parent is removed. The focused package
    suite and live fakeshop suite pass after the change.

### Medium

None.

### Low

None.

## Summary

The cascade implementation's edge classification, unsupported-relation preflight, scope validation,
primary-type resolution, nullable semantics, target-column normalization, cycle handling,
database pinning, sync/async behavior, and GraphQL-visible filter/order/mutation composition are
covered and behave as documented. One high-severity root composition gap was confirmed and fixed by
sealing the helper's input before any consumer-overridable queryset method is dispatched.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/permissions.py::apply_cascade_permissions` to route its
  root queryset through `_prepared_visibility_source(..., require_model_rows=True)` before field
  validation and per-edge predicate composition. This reuses the package's canonical sealed
  execution-queryset boundary and keeps alias handling consistent with framework-owned visibility
  calls.
- Added `tests/test_permissions.py::test_root_queryset_filter_override_is_neutralized_by_sealing`
  to pin the exploit shape and the expected hidden-row exclusion.
- Scratch verification: the pre-fix disposable test returned `["keeps", "leaks"]`; after the fix
  it returns only `["keeps"]`, so the old exploit assertion fails as expected.
- Focused verification: `uv run pytest --no-cov tests/test_permissions.py
  tests/utils/test_permissions.py` — 95 passed, 1 skipped; live fakeshop cascade/filter/order
  selection — 5 passed.
- Formatter/linter: `uv run ruff format .` and `uv run ruff check --fix .` — passed.
- Rejected findings: no additional changes were justified for request/user/session decoding,
  GraphQL error propagation, cycle/alias isolation, nullable edges, filter/order gates, mutation
  lookup visibility, or async traversal; those contracts are owned by their connected modules and
  are covered by the inspected focused and live tests.
- Changelog: no entry requested; this is an alpha security-boundary hardening correction.

## Independent verification (Worker 2)

- Scoped baseline check: `git --no-pager diff 40e9ed64f02dc76364ae29993bca2af15fa40f9 -- django_strawberry_framework/permissions.py tests/test_permissions.py docs/review/rev-permissions.md` contains only the expected `_prepared_visibility_source(..., require_model_rows=True)` root seal, its import, and the permanent hostile-root regression test. No unrelated dirty files were changed.
- Re-traced the root and edge flow through `permissions.py`, `utils/querysets.py`, the registry, optimizer/connection/list/node callers, mutation lookup visibility, filter/order composition, and products live schema. The root is sealed before structural/fields validation and before any consumer-overridable `.filter()` dispatch; target hooks are sealed and normalized through the same shared boundary, then projected to the edge target column.
- Independent historical probe: `uv run pytest --no-cov docs/review/temp-tests/permissions/test_root_filter_override_history.py` — 1 passed. The disposable probe manually performs the pre-fix direct root `.filter()` composition and observes both `keeps` and hidden `leaks`, then observes the current sealed helper returning only `keeps`.
- Permanent-test failure proof: `uv run pytest --no-cov docs/review/temp-tests/permissions/test_root_filter_override_no_seal.py` — 1 passed. Monkeypatching the root seal to identity makes the permanent assertion (`[\"keeps\"]`) fail because the hostile `.filter()` returns both rows.
- Shared-boundary override checks: the focused source/result subclass, instance-shadow, query-chain-shadow, name-agnostic shadow, and async parity tests in `tests/utils/test_querysets.py` — 7 passed. The full focused permission suites `uv run pytest --no-cov tests/test_permissions.py tests/utils/test_permissions.py` — 95 passed, 1 skipped (the sharded-only alias test).
- Live GraphQL callers: the five cited products HTTP tests — 5 passed, including cascade visibility, nested target selection, fixed query count, filter/order composition, and permission gates.
- Boundary review covered malformed and scoped `fields=`, recursive and MTI parent-link traversal, GFK/composite preflight and backing-FK behavior, nullable predicates, primary-type/identity-hook resolution, alias pinning, sync misuse and async worker isolation, optimizer downgrade behavior, connection/list/node/mutation visibility, and the rejected findings recorded by Worker 1. No revision-needed finding remains.

Conclusion: item 14 is independently verified; no production or permanent-test changes were required from Worker 2.
