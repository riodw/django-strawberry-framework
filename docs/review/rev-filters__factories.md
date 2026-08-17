# Review: `django_strawberry_framework/filters/factories.py`

Status: verified

## Understanding

`FilterArgumentsFactory` owns the filter family's Layer-5 BFS hook. It subclasses
`utils/inputs.py::GeneratedInputArgumentsFactory`, supplies the filter-specific
operator bag (`and_` / `or_` / `not_`), and keeps the filter-family input-class and
collision registries. The shared factory performs FIFO breadth-first traversal over
`FilterSet.related_filters`, handles cycles and diamond deduplication, rejects
duplicate generated input names, and builds idempotently. The generated classes are
not module globals until `types/finalizer.py::_bind_sidecar_sets` reaches its
materialization subpass; `filters/inputs.py::materialize_input_class` pins them into
the module namespace required by Strawberry lazy references.

Layer 6 is the deferred `get_filterset_class` surface. `filters/factories.py` keeps
the family cache and filter-field alias while `utils/inputs.py` owns normalization,
hashing, and dynamic `type(...)` construction. `connection.py::_pipeline_sync` and
`connection.py::_pipeline_async` consume only the already-resolved
`DjangoTypeDefinition.filterset_class`; no production caller invokes
`get_filterset_class`. The order twin uses the same shared BFS and dynamic-factory
mechanics with a disjoint cache, collision registry, and no filter operator bag.

Finalizer binding first binds every owner, expands every wired set, validates helper
orphans, then builds and materializes every reachable input class. The registered
`filters/inputs.py::clear_filter_input_namespace` callback clears Layer-5 ledgers,
factory caches, field provenance, and per-set owner state through
`utils/inputs.py::clear_generated_input_namespace`. The Layer-6 cache intentionally
has no clear callback: its keys include model identity, so a rebuilt model cannot
hit a class built for the previous model object; retained old entries are memory
retention only while the surface has no production consumer.

The filter and order factories are not re-exported from `filters/__init__.py` or
the package root. Live fakeshop schemas use explicit `Meta.filterset_class`
declarations; their `/graphql/` tests exercise Layer 5, lazy references, finalizer
binding, and materialization end to end.

## Verification

- Read the target, `utils/inputs.py`, `filters/inputs.py`, `filters/sets.py`,
  `orders/factories.py`, `orders/inputs.py`, `types/finalizer.py`, `registry.py`,
  `connection.py`, public subpackage exports, fakeshop filter declarations, and
  live query tests.
- Before edits, `uv run pytest --no-cov tests/filters/test_factories.py
  tests/orders/test_factories.py tests/utils/test_inputs.py` passed (85 tests).
- Before edits, `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py
  -k 'filter'` passed (30 live HTTP tests).
- A direct pre-fix Django probe showed that
  `exclude=["name", "id"]` and `exclude={"id", "name"}` produced distinct
  `CategoryAutoFilter` classes. Building both through
  `FilterArgumentsFactory` then raised the duplicate
  `CategoryAutoFilterInputType` collision, despite equivalent django-filter
  semantics.
- The same probe showed `get_filterset_class(None, model=object, ...)` leaked a
  raw `AttributeError` from django-filter instead of the package's
  `ConfigurationError` boundary.
- After edits, direct runtime probes confirmed equivalent exclusions reuse one
  dynamic class and one BFS input class, while a non-Django model raises
  `ConfigurationError`.
- After edits, `python -m py_compile` passed for the shared utility, both factories,
  and both factory test modules. `git diff --check` passed. Repository-required
  `uv run ruff format .` and `uv run ruff check --fix .` both passed. No pytest was
  run after edits, per repository instruction.

## Improvements

### High

None.

### Medium

#### Equivalent `Meta.exclude` declarations split the dynamic cache

- **Observation:** `normalize_set_meta_for_factory` canonicalized unordered
  `fields` shapes but preserved the order of list/tuple values in the extra
  `exclude` Meta option.
- **Evidence:** The pre-fix probe produced two distinct `CategoryAutoFilter`
  classes for a list and an equivalent set with reversed iteration order. The
  shared Layer-5 collision registry then rejected the second generated input
  class because both classes claimed `CategoryAutoFilterInputType`.
- **Impact:** The Layer-6 cache failed its purpose of collapsing equivalent
  declarations. Once the deferred auto-generation consumer is used, two
  connection fields with equivalent exclusions can prevent schema input
  construction rather than sharing one class.
- **Recommendation:** Canonicalize `exclude` list, tuple, set, and frozenset
  declarations to one `repr`-sorted list in the shared normalization owner,
  preserving the family-specific caches while preventing duplicate generated
  names in both filter and order factories.
- **Proof:** Implemented in `utils/inputs.py::normalize_set_meta_for_factory`;
  permanent coverage is in
  `tests/filters/test_factories.py::test_dynamic_filterset_cache_collapses_exclude_order`
  and `tests/orders/test_factories.py::test_get_orderset_class_collapses_exclude_order`.

#### Dynamic factories leaked a raw error for a non-Django model

- **Observation:** Missing `model` already raised a package
  `ConfigurationError`, but a supplied non-model object reached
  `model.__name__` / django-filter and leaked `AttributeError`.
- **Evidence:** `get_filterset_class(None, model=object, ...)` raised
  `AttributeError: type object 'object' has no attribute '_meta'`.
- **Impact:** Invalid dynamic Meta input failed at an implementation detail
  instead of the factory boundary, making a future connection-field
  configuration error opaque and inconsistent with the missing-model case.
- **Recommendation:** Validate that dynamic `model` is a Django model class
  before constructing the synthetic set class, using the shared owner so filter
  and order helpers report the same contract.
- **Proof:** Implemented in `utils/inputs.py::create_dynamic_set_class`;
  permanent coverage is in
  `tests/filters/test_factories.py::test_get_filterset_class_rejects_non_model_when_dynamic`
  and `tests/orders/test_factories.py::test_get_orderset_class_rejects_non_model_when_dynamic`.

### Low

None. The Layer-6 no-clear lifecycle is intentional and safe for current usage:
`registry.clear()` resets every Layer-5 binding/cache ledger, model identity remains
part of dynamic keys, and no live consumer exists yet. Adding a clear hook solely to
discard unconsumed old model classes would be lifecycle polish rather than a
correctness fix.

## Summary

The target's Layer-5 family hook is correctly single-sited against the shared BFS;
its collision, cycle, lazy-reference, finalizer, metaclass, export, and live GraphQL
contracts are covered. Two Layer-6 boundary defects were fixed at their shared
owners: semantically equivalent exclusions now share a generated class, and invalid
dynamic models fail with an actionable package error. The target file itself needed
no direct edit; the root-cause changes belong in the shared normalization and
dynamic-class construction helpers used by both set families.

## Implementation (Worker 1)

- Changed source:
  - `django_strawberry_framework/utils/inputs.py::normalize_set_meta_for_factory`
  - `django_strawberry_framework/utils/inputs.py::create_dynamic_set_class`
- Changed tests:
  - `tests/filters/test_factories.py::test_dynamic_filterset_cache_collapses_exclude_order`
  - `tests/filters/test_factories.py::test_get_filterset_class_rejects_non_model_when_dynamic`
  - `tests/orders/test_factories.py::test_get_orderset_class_collapses_exclude_order`
  - `tests/orders/test_factories.py::test_get_orderset_class_rejects_non_model_when_dynamic`
- `django_strawberry_framework/filters/factories.py` has no Worker-1 source delta
  against dispatch baseline `025893b513d80ed5a7c57f5cb208bde54fc1cbab`; its
  shared-helper call sites remain unchanged.
- No changelog update is warranted for this deferred, currently unconsumed
  factory hardening.
- No plan checkbox was changed; Worker 2 owns that lifecycle step.
- Blockers: none.

## Iterations

Worker 2's independent focused run found one regression in
`tests/utils/test_inputs.py::test_make_dynamic_set_getter_collapses_equivalent_meta_and_passthroughs_explicit`:
the shared utility test supplied a plain local `_Model`, while
`utils/inputs.py::create_dynamic_set_class` now correctly requires a real Django
model for both filter and order dynamic factories. The production guard remains
the root-cause fix for invalid dynamic Meta; the permanent test now uses the
fakeshop `apps.products.models.Category` model and keeps its cache identity,
generated-name, and explicit-class passthrough assertions. The review status
remains `fix-implemented`; Worker 2 should re-run independent verification.

## Independent verification (Worker 2)

Status: verified.

- Compared the scoped changes against dispatch baseline
  `025893b513d80ed5a7c57f5cb208bde54fc1cbab`: `filters/factories.py` and
  `orders/factories.py` have no source delta; both continue to route through
  the shared `utils/inputs.py` dynamic getter, with disjoint family caches and
  collision registries.
- Independently inspected the revised utility test and re-ran
  `uv run pytest --no-cov tests/filters/test_factories.py
  tests/orders/test_factories.py tests/utils/test_inputs.py`: 89 passed.
- A direct Django probe verified all four required `exclude` shapes (list,
  tuple, set, and frozenset) collapse to one dynamic class and one BFS input
  class in each family, while `model=object` raises the typed
  `ConfigurationError` diagnostic for both getters.
- `uv run pytest --no-cov tests/filters/test_finalizer.py
  tests/orders/test_finalizer.py` passed (50 tests), covering owner binding,
  expansion, orphan validation, materialization, and registry-cleared rebuild
  lifecycle.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py
  -k filter` passed (30 live HTTP tests), covering the production filter
  pipeline, lazy input references, permissions, and connection composition.
- Audited callers and exports: the dynamic getters remain build-and-test-only;
  live connections consume explicit `Meta.filterset_class` / `Meta.orderset_class`
  sidecars. Generated-name collision, cycle/diamond deduplication, explicit
  passthrough, and family-cache isolation remain covered by the factory tests.

No revision-needed findings remain.
