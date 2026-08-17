# Review: `django_strawberry_framework/filters/`

Status: verified

## Understanding

The filters folder is one lifecycle: `FilterSetMetaclass` collects and binds `RelatedFilter` declarations; `FilterSet.get_filters` expands the graph and freezes row-preserving candidate metadata; `FilterArgumentsFactory` builds the reachable Strawberry input graph; finalizer phase 2.5 binds owners, audits related targets and GlobalID strategies, then materializes lazy input classes. `FilterSet.apply_sync` / `apply_async` derive related visibility, apply explicit related querysets, fire active-input permission gates, validate django-filter forms, and feed the resulting queryset to connection and list consumers.

The integrated trace covered the sibling `orders/` lifecycle and permission facade, `sets_mixins.py`, shared input/value/permission/queryset/relation utilities, finalizer phase 2.5, connection signature and pipeline consumers, synthesized relation connections, fakeshop filter declarations, and live HTTP APIs. Existing behavior includes owner-aware Relay filter selection, non-pk `to_field` GlobalID qualification, row-preserving `EXISTS` routing for generated to-many leaves, sync/async visibility boundaries, logical branch composition, and module-global input materialization.

## Verification

- Read the complete filters package and connected order, utility, finalizer, connection/list, fakeshop, and test surfaces; challenged prior per-file dispositions instead of treating them as conclusive.
- Pre-edit focused suites passed: `uv run pytest --no-cov tests/filters tests/orders tests/utils/test_permissions.py tests/utils/test_input_values.py` — 704 passed.
- Pre-edit live GraphQL filter suites passed: `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py examples/fakeshop/test_query/test_scalars_filter_api.py examples/fakeshop/test_query/test_kanban_api.py` — 241 passed.
- A direct Django probe reproduced the integrated defect: a consumer `Meta.filter_overrides` entry returning `CharFilter(distinct=False)` for `loans__note__icontains` was changed to `distinct=True` by `FilterSet.filter_for_field` before its ownership check.
- A second direct probe reproduced the same ownership failure for a Relay own-PK `BigAutoField` override, which was replaced by `GlobalIDFilter`; a method-level `filter_for_lookup` override showed the same replacement.
- After the fix, direct probes report `distinct=False`, `origin=\"override_generated\"`, and `framework_added_distinct=False` for the to-many policy override, plus the consumer `CharFilter` and a non-routable `generation_capable=False` provenance row for the method override.
- Post-edit validation passed: `uv run ruff format .`, `uv run ruff check --fix .`, `uv run python -m py_compile django_strawberry_framework/filters/sets.py tests/filters/test_sets.py`, and `git diff --check` for the scoped paths. Per repository instruction, pytest was not run after edits.

## Improvements

### High

None.

### Medium

#### Consumer filter overrides were mutated by framework conversion policy

- **Observation:** `FilterSet.filter_for_field` resolved `default_origin` only after applying framework policy. A consumer-owned to-many filter selected through `Meta.filter_overrides` therefore received framework `distinct=True` even when its declaration explicitly requested `distinct=False`; consumer-owned Relay own-PK filters were likewise replaced with `GlobalIDFilter` instead of retaining their declared class, including when the consumer overrode `filter_for_lookup`.
- **Evidence:** A real `Book` filter over the reverse `loans__note` path with `filter_overrides={TextField: {"filter_class": CharFilter, "extra": lambda field: {"distinct": False}}}` produced `distinct=True` and provenance `framework_added_distinct=True` before the change. A `Category` Relay-node filter over its `BigAutoField` primary key with a governing `CharFilter` override, and a sibling overriding `filter_for_lookup`, both produced `GlobalIDFilter` / `package_replacement`. All were correctly identified as `override_generated`, so they must retain their consumer-defined behavior.
- **Impact:** The override contract was not fail-closed: duplicate parent rows that a consumer intentionally preserved were collapsed, downstream connection/list counts and pagination could change, and an own-PK input could be advertised and decoded as a GlobalID despite the consumer selecting another wire shape.
- **Recommendation:** Resolve the generation ownership verdict before applying either framework conversion. Apply the package's many-side distinctness and Relay GlobalID replacement only to `framework_default` leaves; keep consumer filters and their provenance unchanged.
- **Proof:** `tests/filters/test_sets.py::test_filter_override_distinct_is_preserved_on_to_many_path`, `tests/filters/test_sets.py::test_filter_override_own_relay_pk_is_preserved`, and `tests/filters/test_sets.py::test_filter_for_lookup_override_own_relay_pk_is_preserved` assert the resolved classes, origins, and provenance bits. The production owners are `django_strawberry_framework/filters/sets.py::FilterSet.filter_for_field` and `django_strawberry_framework/filters/sets.py::FilterSet.filter_for_lookup`.

### Low

None.

## Implementation (Worker 1)

- Updated `django_strawberry_framework/filters/sets.py::FilterSet.filter_for_field` and `FilterSet.filter_for_lookup` to determine ownership before applying framework-added distinctness or Relay GlobalID conversion, preserving consumer-owned filter instances byte-for-byte. Method-overridden generation seams skip framework mutation/conversion but retain a frozen non-routable provenance row; `__init__`-only overrides and shallow-copied untouched defaults retain their existing conversion behavior while remaining non-routable.
- Added `tests/filters/test_sets.py::test_filter_override_distinct_is_preserved_on_to_many_path`, `tests/filters/test_sets.py::test_filter_override_extra_only_does_not_add_distinct_on_to_many_path`, `tests/filters/test_sets.py::test_filter_override_own_relay_pk_is_preserved`, and `tests/filters/test_sets.py::test_filter_for_lookup_override_own_relay_pk_is_preserved`.
- No change was needed in `orders/`, shared permissions, finalizer phase 2.5, connection/list consumers, or fakeshop declarations: they consume the corrected frozen provenance and retain their existing contracts.
- Investigated async nested-visibility prewalking and explicit related-queryset alias composition; no additional correctness defect was proved, so no speculative cross-folder edits were made.
- No changelog update is warranted for this internal customization-boundary hardening.
- The requested dispatch stash object `5dc71b60fc2067ef44205ca2262ccb69cc5187805` is not reachable in this checkout, so an exact Git baseline diff could not be computed. Current dirty and untracked work was preserved; scoped ownership was established from the existing per-file artifacts, current-source trace, and the touched-path diff.

## Summary

The filters package composes coherently with orders, shared traversal/permission/queryset utilities, finalizer phase 2.5, connection/list consumers, and live fakeshop APIs. One integrated customization-boundary defect had three manifestations: consumer-owned to-many overrides were altered before the fail-closed ownership decision, and consumer-owned Relay own-PK overrides were converted through both policy and method override seams. The root fix is implemented at the two filter-generation owners with permanent package coverage; formatting, lint, syntax, and whitespace checks pass.

## Iterations

Worker 2's independent verification found one residual manifestation: an extra-only `Meta.filter_overrides` provider that omitted `distinct` was still receiving framework-added `distinct=True` despite being classified `override_generated`. Worker 1 corrected the ownership predicate in `FilterSet.filter_for_field`, added `test_filter_override_extra_only_does_not_add_distinct_on_to_many_path`, and preserved the existing explicit-distinct, own-PK, method-override, and candidate-routing controls. The artifact is `fix-implemented`; Worker 2 should re-run independent verification.

The integrated `test_c4_untouched_surfaces_attach_no_reserved_alias` assertion was also stale: its extra-only override intentionally preserves duplicate parent occurrences once framework mutation is removed. The test now asserts `[book.pk, book.pk]`, making the consumer multiset contract explicit rather than restoring the old deduplication behavior.

## Independent verification (Worker 2)

- The final ownership fix passes the three added regressions and the broader integrated checks: `uv run pytest --no-cov tests/filters/test_sets.py -k 'filter_override_distinct_is_preserved_on_to_many_path or filter_for_lookup_override_own_relay_pk_is_preserved or filter_override_own_relay_pk_is_preserved'` (3 passed), `uv run pytest --no-cov tests/filters/test_sets.py` (287 passed), `uv run pytest --no-cov tests/filters tests/orders tests/utils/test_permissions.py tests/utils/test_input_values.py` (707 passed), and the three live fakeshop filter APIs (241 passed). Focused re-challenges also passed: GlobalID/dynamic-factory/input/finalizer checks (124 passed), composite permission checks (8 passed), and live kanban permission/order checks (5 passed).
- Direct probes against real fakeshop models confirmed explicit `distinct=False` preservation, own-PK `CharFilter` preservation through both policy and `filter_for_lookup` seams, framework-default to-many `distinct=True`, `framework_default`/`generation_capable=True` provenance, and routable candidate metadata. The GlobalID invalid-PK, dynamic factory, declared-key normalization, and composite permission fixes remain green in the focused suites.
- **Revision needed — consumer-owned extra-only overrides still receive framework distinctness.** A `BookFilter` with `Meta.filter_overrides = {TextField: {"filter_class": CharFilter, "extra": lambda field: {}}}` on `loans__note__icontains` is correctly classified as `origin="override_generated"` and excluded from candidate routing, but the resolved consumer `CharFilter` is mutated to `distinct=True` and stamped `framework_added_distinct=True`. The mutation is at `django_strawberry_framework/filters/sets.py:1584-1596`, where `framework_added_distinct` is computed for any generation-capable to-many leaf lacking a captured `distinct` key and then assigned regardless of `effective_origin`.
- **Impact:** The fail-closed customization boundary is still porous: a consumer-owned `Meta.filter_overrides` filter can have its queryset semantics changed even when the consumer intentionally supplied a custom `extra` provider. This can collapse duplicate parent occurrences and alter list/connection counts or pagination, despite the leaf being correctly marked non-routable.
- **Recommendation:** Compute and apply framework-added to-many distinctness only when `effective_origin == "framework_default"`; consumer-owned `override_generated` instances must retain their live `distinct` value and carry `framework_added_distinct=False`. Add a permanent regression for an extra-only override that omits `distinct`, asserting the class, `distinct=False`, provenance, and absent/non-routable candidate row, while retaining the existing explicit-`distinct=False` and pristine-default controls.
- **Disposition:** `revision-needed`; the folder item remains open and the plan checkbox is intentionally unchanged.

## Iterations

Worker 2 re-ran the final Worker 1 revision after the extra-only ownership fix and the duplicate-preservation assertion update. The four ownership regressions passed (explicit `distinct=False`, extra-only override, own-PK policy override, and `filter_for_lookup` override); the full integrated package suites passed with `708` tests; live fakeshop filter, GlobalID, permission, reverse-relation, and ordering APIs passed with `241` tests; the prior GlobalID/dynamic-factory/input/finalizer checks passed with `124` tests; and the composite permission traversal checks passed with `8` tests.

A direct probe against real fakeshop models confirmed that an extra-only consumer override remains `distinct=False`, `origin="override_generated"`, `framework_added_distinct=False`, and absent from candidate routing; untouched generated to-many defaults still receive `distinct=True`, `framework_default` provenance, and routable metadata; and both own-PK override seams retain `CharFilter` rather than `GlobalIDFilter`. No additional integration defect remains. The filters folder review is verified.
