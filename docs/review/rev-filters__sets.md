# Review: `django_strawberry_framework/filters/sets.py`

Status: verified

## Understanding

`filters/sets.py` owns the consumer-facing `FilterSet` declaration and execution boundary. `FilterSetMetaclass` collects `RelatedFilter` declarations, binds owners, and leaves expansion lazy; `FilterSet.get_filters` expands related leaves under a recursion guard and publishes the immutable filter/candidate snapshot used by the row-preserving `EXISTS` applicator. `filter_for_field` / `filter_for_lookup` select scalar, CSV, range, integer-safety, or Relay GlobalID primitives from the owner-aware policy. `FilterSet._normalize_input` converts Strawberry operator bags, lookup names, ranges, enums, GlobalIDs, logical branches, and related branches into django-filter form data.

The apply pipeline is split into `apply_sync` and `apply_async`: each derives active related visibility through the shared sealed queryset boundary, intersects active `RelatedFilter(queryset=...)` constraints before constructing the filterset instance, runs active-input permission gates, validates the form explicitly, and reads `.qs`. The async path pre-derives logical-branch visibility before one thread-sensitive sync boundary; the dispatcher translates only typed sync misuse. `filter_queryset` preserves flat leaves and logical `Q` composition, routing only build-time-proven framework-generated to-many leaves through `correlated_inner_root` / `attach_exists`, while declared, overridden, method, custom, and unaudited leaves retain django-filter’s outer invocation.

The target was traced through `filters/base.py`, `filters/inputs.py`, `filters/factories.py`, `sets_mixins.py`, `utils/input_values.py`, `utils/permissions.py`, `utils/querysets.py`, `utils/relations.py`, `orders/sets.py`, finalizer phase 2.5 owner binding, cascade visibility, connection filter/order pipelines, optimizer predicate consumers, package tests, and live fakeshop filters in products, library, scalars, and kanban. Existing coverage exercises metaclass tombstones/cycles, owner-aware Relay shape, form validation, sync/async visibility, aliases, permission deduplication, logical Q semantics, row-preserving SQL, and live HTTP filter APIs.

## Verification

- Compared the assigned paths with dispatch baseline `87803c5b417f25066a4b99465a50c5d8ec2d928e`; the only Worker 1 source/test deltas are the shared permission utility and its focused/live regressions. Pre-existing changes in `filters/sets.py` and `tests/filters/test_sets.py` were preserved.
- Ran focused pre-edit validation: `uv run pytest --no-cov tests/filters/test_sets.py -k 'normalize_input or apply_sync_filters_against_simple_scalar_input or apply_async_nested_related_gate_fires_once_and_still_denies or declared_filter or direct_m2m_relation_override or malformed_logical or relation_visibility or filter_for_lookup'` — 23 passed.
- Reproduced the composite-path permission gap with `_fire_flat_relation_path_gates`: an overlapping `target_version` declaration won over `target_version__milestone`, so the flat `target_version__milestone__key` path fired no target gate.
- After the fix, the disposable probe and the new permanent regression function both produced `Card.milestone` then `Milestone.key`.
- `uv run ruff format .` completed successfully. The repo-wide `uv run ruff check --fix .` still reports an unrelated pre-existing `B904` at `django_strawberry_framework/utils/relations.py::classify_path` (the concurrent dirty file was not changed). Scoped lint for all Worker 1 paths passed.
- `uv run python -m py_compile django_strawberry_framework/filters/sets.py django_strawberry_framework/utils/permissions.py tests/utils/test_permissions.py examples/fakeshop/test_query/test_kanban_api.py` passed. `git diff --check` passed for the scoped paths. Per repository instruction, pytest was not run after edits.

## Improvements

### High

#### Flat composite relation paths could bypass target permission gates

- **Observation:** The shared flat-path permission walker matched only the next single ORM hop. When a `RelatedFilter` declaration used a composite `field_name` such as `target_version__milestone` and a separate shorter `target_version` declaration existed, a generated flat leaf at `target_version__milestone__key` followed the shorter branch and stopped before the declared milestone target.
- **Evidence:** A direct helper probe with overlapping declarations returned no gate calls for the flat path. The live kanban filter surface emits `milestoneKey` from `CardFilter.milestone`, whose ORM path is `target_version__milestone`; the nested `milestone: { key: ... }` path reaches `MilestoneFilter`, so the two spellings were not authorization-equivalent.
- **Impact:** A consumer could bypass `check_key_permission` on the target filterset by selecting the flat spelling, defeating the documented rule that flat and nested relation filters share permission gates.
- **Recommendation:** In `utils/permissions.py::_fire_flat_relation_path_gates`, match declarations by ORM-path prefix and choose the longest matching prefix. Preserve the public declaration name for the parent branch gate, then continue from the resolved target set; retain the existing fail-closed stop when no declaration or target resolves.
- **Proof:** The permanent unit regression `tests/utils/test_permissions.py::test_fire_flat_relation_path_gates_prefers_composite_branch_prefix` asserts the exact gate sequence. The live HTTP regression `examples/fakeshop/test_query/test_kanban_api.py::test_flat_composite_milestone_filter_fires_target_permission_gate` exercises `milestoneKey` against the fakeshop schema with a denied target gate.

### Medium

None.

### Low

None.

## Implementation (Worker 1)

- Updated `django_strawberry_framework/utils/permissions.py::_fire_flat_relation_path_gates` to select the longest matching composite ORM-path declaration, closing the flat-vs-nested permission bypass for both FilterSet and OrderSet configurations.
- Added package-level regression coverage in `tests/utils/test_permissions.py` and live `/graphql/` coverage in `examples/fakeshop/test_query/test_kanban_api.py`.
- No source change was needed in `django_strawberry_framework/filters/sets.py`; its `ActiveInputPermissionMixin` call path now consumes the corrected shared traversal.
- Preserved unrelated concurrent edits, including the pre-existing target-file changes. The review-plan checkbox was not edited.
- No changelog update is warranted for this security hardening.

## Summary

The target’s declaration/expansion lifecycle, owner-aware lookup routing, form and value normalization, sync/async boundaries, related visibility composition, permission recursion, logical Q semantics, row-preserving predicate routing, finalizer binding, connection/optimizer cooperation, and fakeshop APIs are coherent and broadly covered. One high-impact representational permission bypass remained at the shared flat-path traversal boundary; it is fixed at the shared owner with unit and live acceptance coverage.

## Independent verification (Worker 2)

- Re-traced the target against dispatch baseline `87803c5b417f25066a4b99465a50c5d8ec2d928e`: `filters/sets.py` and its package tests contain no Worker 1 delta relative to that baseline; the implementation delta is the shared `utils/permissions.py` traversal plus its package/live regressions. The `FilterSet` and `OrderSet` callers both route active leaf paths through `run_active_input_permission_checks`, with family-specific `related_attr` / `target_attr` configuration preserved.
- Verified `_fire_flat_relation_path_gates` against the composite-shadow case for both family configurations: for `target_version__milestone__key`, matching declarations are collected at each remaining prefix and the longest `field_name` prefix wins, so `Card.milestone` / `Milestone.key` (FilterSet) and `CardOrder.milestone` / `MilestoneOrder.key` (OrderSet) fire instead of descending through the shorter `target_version` branch. Missing declarations stop without guessing a target; an unresolved target fires only the resolved parent branch gate; flat/nested repeats deduplicate by class.
- Verified active-input semantics in both consumers: omitted / `None` / `strawberry.UNSET` fields and related branches do not fire gates; active filter branches recurse and deny; inactive logical arms remain identity; order top-level lists deduplicate repeated branch and child gates, and empty order input remains unchanged.
- Pre-edit executable checks passed: `uv run pytest --no-cov tests/utils/test_permissions.py -k 'fire_flat_relation_path_gates'` (8 passed); focused filter active-input / denial checks (9 + 3 passed); focused order permission / empty-input checks (9 passed); and live kanban checks for nested milestone filtering, denied flat `milestoneKey`, and status ordering (3 passed). `uv run ruff check .` currently passes. The previously reported repo-wide `B904` is outside this item in concurrent `django_strawberry_framework/utils/relations.py::classify_path`; it was not changed or reverted.
- No revision-needed finding remains. Per repository instruction, no pytest was run after this review-doc edit.
