# Build: Cross-slice integration pass

Spec reference: [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050] and
[`docs/spec-050-list_field_arguments-0_0_15-rationale.md`][spec-050-rationale]
Build plan: [`docs/builder/build-050-list_field_arguments-0_0_15.md`][build-050]
Status: integration-accepted

## Artifact shape: one Worker 1 pass

`## Build report (Worker 2)` and `## Review (Worker 3)` are **not applicable** here.
[`docs/builder/BUILD.md`][build-md] `## Cross-slice integration pass` assigns the pass to
Worker 1 alone and gives it one output, `bld-integration.md`. A builder is dispatched only
if cross-slice DRY, architectural, or divergence findings require code consolidation. This
pass verified all five accepted slices, confirmed end-to-end coherence across package,
test, and documentation tiers, and found zero cross-slice regressions or unresolved
defects.

**Hot-path declaration: none.** This pass introduces no runtime code. Across the card, the
hot-path budgets established in Slices 1-3 were verified: 0 runtime `NameConverter` calls
on valid requests, post-apply seal benchmark measured 22.07 µs/iter (target <= 100 µs), and
sub-microsecond `_AsyncQuerySetRows` adapter unwrap/rewrap overhead in the optimizer
extension.

**Floor-verification scope: none for this pass.** Floor verification across the multi-version
matrix (Python 3.10-3.14, Django 5.2-6.1, strawberry-graphql 0.316.0-0.324.0) was verified
in Slices 1-3 and is owned repo-wide by the final gate and CI. The local verification
environment runs Python 3.14.2, Django 6.1, and strawberry-graphql 0.324.0.

---

## The six mandatory preconditions

### Precondition 1 — read every prior slice artifact in slice order

All five slice artifacts for Card 050 were read in slice order and in full:

| Artifact | Lines | Bytes | Status read |
| :--- | :--- | :--- | :--- |
| [`bld-slice-1-argument_normalization.md`][bld-slice-1] | 630 | 59,270 | `final-accepted` |
| [`bld-slice-2-orderby_pipeline.md`][bld-slice-2] | 1098 | 102,245 | `final-accepted` |
| [`bld-slice-3-sql_and_unit_contracts.md`][bld-slice-3] | 1025 | 96,356 | `final-accepted` |
| [`bld-slice-4-live_acceptance.md`][bld-slice-4] | 645 | 53,177 | `final-accepted` |
| [`bld-slice-5-documentation_fold_in.md`][bld-slice-5] | 460 | 36,277 | `final-accepted` |

All five artifacts reached `final-accepted` before the start of this pass. Zero open
revision loops remain.

### Precondition 2 — confirm static inspection helper ran for touched files

Static inspection was performed across all seven Python files modified during Card 050 via
`scripts/review_inspect.py` into `docs/shadow/`:
- [`django_strawberry_framework/list_field.py`][list-field] ->
  `docs/shadow/django_strawberry_framework__list_field.overview.md` (199 lines)
- [`django_strawberry_framework/resource_policy.py`][resource-policy] ->
  `docs/shadow/django_strawberry_framework__resource_policy.overview.md` (171 lines)
- [`django_strawberry_framework/orders/sets.py`][orders-sets] ->
  `docs/shadow/django_strawberry_framework__orders__sets.overview.md` (160 lines)
- [`django_strawberry_framework/utils/querysets.py`][querysets] ->
  `docs/shadow/django_strawberry_framework__utils__querysets.overview.md` (525 lines)
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension] ->
  `docs/shadow/django_strawberry_framework__optimizer__extension.overview.md` (290 lines)
- [`django_strawberry_framework/_strawberry_patches.py`][strawberry-patches] ->
  `docs/shadow/django_strawberry_framework___strawberry_patches.overview.md` (215 lines)
- [`django_strawberry_framework/__init__.py`][pkg-init] ->
  `docs/shadow/django_strawberry_framework____init__.overview.md` (129 lines)

All shadow stripped source files and static overviews are fresh and up to date. Zero files
were skipped.

### Precondition 3 — compare repeated string literals across shadow overviews

Examined the `Repeated string literals` sections across all shadow overview files:
- `django_strawberry_framework/list_field.py`: `DjangoListField` (10x), `Invalid argument` (6x),
  `order_by` (5x), `__django_strawberry_definition__` (3x), `non_integer` (3x), `negative` (3x),
  `over_ceiling` (3x), `order_required` (3x), `queryset_required` (2x).
- `django_strawberry_framework/resource_policy.py`: `execution_deadline_seconds` (3x),
  `ResourcePolicy.` (2x).
- `django_strawberry_framework/orders/sets.py`: `OrderSet` (6x), `related_orders` (4x),
  `for model` (2x).
- `django_strawberry_framework/utils/querysets.py`: `__dict__` (17x), `prefetch_through` (6x),
  `apply_type_visibility for` (6x), `alias_map` (3x), `combined_queries` (3x), `unevaluated` (3x),
  `combined` (3x).
- `django_strawberry_framework/optimizer/extension.py`: 0 repeated string literals.
- `django_strawberry_framework/__init__.py`: DRF-lazy attribute mapping names and submodules (2x).

Cross-file literal comparison confirms no unaddressed duplicated string constants exist.
Domain error reason codes (`offset_negative`, `offset_ceiling`, `limit_negative`, `limit_ceiling`,
`order_required`, `queryset_required`) are single-sited in `list_field.py` and validated across
the test tiers. Sealing policies (`_LIST_ARGUMENT_VISIBILITY_POLICY`, `_ORDERSET_RESULT_POLICY`)
are single-sited in `utils/querysets.py`.

### Precondition 4 — compare imports across shadow overviews for dependency direction

Analyzed the `Imports` sections across all shadow overviews to confirm strict one-way
architectural dependency direction:
- `django_strawberry_framework/list_field.py`: imports from `conf`, `exceptions`,
  `resource_policy`, `types`, `utils.directives`, `utils.querysets`, and `utils.typing`. It
  imports lazily from `.orders` (`order_input_type`) inside `_synthesized_list_signature` at
  field construction time, preventing a module-level import cycle.
- `django_strawberry_framework/resource_policy.py`: imports from `conf`, `exceptions`,
  `utils.context`, `utils.errors`, `utils.policies`, and `utils.querysets`
  (`is_async_only_iterable`). Does not import `list_field.py`.
- `django_strawberry_framework/orders/sets.py`: imports from `exceptions`, `sets_mixins`,
  `utils.input_values`, `utils.inputs`, `utils.querysets`, `utils.relations`, `utils.strings`,
  `.base`, `.inputs`, and `types.definition`. Does not import `list_field.py`.
- `django_strawberry_framework/optimizer/extension.py`: imports from `registry`, `utils.querysets`
  (`normalize_query_source`, `unwrap_async_queryset_adapter`, `wrap_async_queryset_adapter`), and
  `utils.typing`. Does not import `list_field.py`.
- `django_strawberry_framework/utils/querysets.py`: provides core queryset lifecycle, sealing,
  and adapter utilities (`_AsyncQuerySetRows`, `_validate_post_orderset_result`). Does not
  import `list_field.py`.
- `django_strawberry_framework/__init__.py`: top-level root export entry point; imports
  `DjangoListField` and `ListArgumentError` from `.list_field`.

Dependency direction is strictly acyclic and one-way: foundational utilities -> resource
policy / order sets -> list field -> root package.

### Precondition 5 — walk accepted slice artifacts' "What looks solid" and "DRY findings"

Reviewed `What looks solid` and `DRY findings` across all five slice reviews:
- **Slice 1**: Verified single-sited error class `ListArgumentError`, pickle `__reduce__`
  roundtrip, and integer coercion guards. Zero deferred items.
- **Slice 2**: Pass 1 identified 14 weakly pinned boundaries; Pass 2 re-pinned all 14 (failing
  >= 2 rows), extracted `_orderset_class_for_target` and `_build_non_queryset_rejection_error`
  to eliminate duplication, and enforced `_AsyncQuerySetRows` protocol. Zero deferred items.
- **Slice 3**: Verified SQL contract parity, elimination of all 18 `DJANGO_ALLOW_ASYNC_UNSAFE`
  overrides in `tests/test_list_field.py`, and 25 pinned failability boundaries (9 floor re-runs
  verified by Worker 3). Zero deferred items.
- **Slice 4**: Pass 1 identified 1 medium finding (`test_multi_db.py` missing the unrouted
  `_hints` mismatch half of spec row 26) and 1 low finding (failability proof formatting). Pass 2
  verified both completely resolved with `test_post_orderset_hints_routing_mismatch_rejected_on_sharded_db`
  and clean formatting. Zero deferred items.
- **Slice 5**: Verified AST docstrings in `list_field.py` and `resource_policy.py`, KANBAN card
  closeout, glossary synchronization (43 terms), and standing doc updates in `docs/README.md`
  and `README.md`. Zero deferred items.

Conclusion: No unresolved review findings, deferred tickets, or unaddressed architectural debts
exist across any of the five slices.

### Precondition 6 — sweep whole tree for staged anchors

Ran comprehensive repository-wide grep checks for staged anchors:
1. `git grep -rn 'TODO(spec-050' .`
2. `git grep -rn 'TODO.*050' .`

Results:
- **0** staged `# TODO(spec-050 ...)` anchors remain in package source
  (`django_strawberry_framework/`), test trees (`tests/`, `examples/`), or standing documentation
  (`docs/README.md`, `README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`).
- Historical discussions in `docs/bug_hunt/` and archived build plans in `docs/builder/DONE/`
  reference card history, which is appropriate.
- Card 050 is closed in `KANBAN.md` with all Definition of Done checkboxes satisfied.

---

## Cross-slice checks

### Helper duplication and existence challenge

- **Helper inventory**: Audited all symbols added or updated across the slices against
  `docs/shadow/helper-inventory.md`:
  - `_resolve_argument_wire_name`: single-sited in `list_field.py`, resolves wire argument
    spellings dynamically through active `NameConverter` only on error.
  - `_normalize_list_arguments`: single-sited in `list_field.py`, parses coordinates and enforces
    deterministic `offset`-before-`limit` error order.
  - `_synthesized_list_signature`: single-sited in `list_field.py`, constructs resolver signature
    and annotations without leaking default values into GraphQL SDL.
  - `_is_random_order_term` & `_is_model_default_ordering_active`: single-sited in `list_field.py`,
    evaluates ordering activity without executing database queries.
  - `_orderset_class_for_target` & `_build_non_queryset_rejection_error`: single-sited in
    `list_field.py`, extracted in Slice 2 to avoid duplicate target inspection and error formatting.
  - `_AsyncQuerySetRows`: single-sited in `utils/querysets.py`, implements `__aiter__` and explicitly
    omits `__iter__` to prevent synchronous iteration escapes under async views.
  - `wrap_async_queryset_adapter` & `unwrap_async_queryset_adapter`: single-sited in
    `utils/querysets.py`, reused cleanly by `DjangoOptimizerExtension` across all exit paths.
  - `_validate_post_orderset_result`: single-sited in `utils/querysets.py`, enforces
    `_ORDERSET_RESULT_POLICY` and verifies `_db` and `_hints` identity between sealed source and
    candidate.
  - `_close_async_iterator`: single-sited in `resource_policy.py`, safely invokes `aclose()` and
    preserves primary exceptions while attaching cleanup diagnostics to `__notes__`.
- **Verdict**: Clean. No helper duplication, redundant abstractions, or orphaned utilities exist.

### Naming consistency

- **Internal parameter names**: `offset`, `limit`, `order_by` consistently used across
  `_normalize_list_arguments`, `_ListArguments`, and resolver wrappers (`_default`, `_wrap`).
- **Wire argument names**: Consistently resolved via `schema_config_from_info(info).name_converter.from_argument(...)`.
  Verified under default camelCase (`offset`, `limit`, `orderBy`) and snake_case (`order_by`).
- **Error classes**: `ListArgumentError` inherits from `(GraphQLError, DjangoStrawberryFrameworkError)`.
- **Error extensions**: Consistently emits `{"code": "LIST_ARGUMENT_INVALID", "argument": "<wire_name>", "reason": "<reason_slug>"}`.
- **Reason slugs**: Consistently used: `offset_negative`, `offset_ceiling`, `limit_negative`,
  `limit_ceiling`, `order_required`, `queryset_required`.

### Error handling and fail-closed guarantees

- **Validation order**: Strictly deterministic across all execution modes: `offset` evaluated
  before `limit`; coordinate bounds evaluated before order execution; order permissions evaluated
  before offset guard.
- **Ceiling enforcement**: `offset` and `limit` capped at request `ResourcePolicy.max_list_rows`
  (with `trusted_max_rows=True` permitting field-declared widening of `limit`). Over-ceiling
  values reject immediately with HTTP 200 GraphQL error envelopes without executing SQL queries.
- **Seal rejections**: Pre-sliced and combined querysets reject with actionable
  `ConfigurationError` at source and result seals.
- **Multi-database routing**: Mismatches between sealed source and OrderSet candidate for `_db`
  or `_hints` fail closed with `ConfigurationError`.
- **Async iterator cleanup**: Non-queryset and rejected async iterators are cleanly closed via
  `aclose()` without over-requesting items or masking domain errors.

### ORM and QuerySet patterns

- **No pk tiebreaker**: Flat `DjangoListField` fields deliberately omit automatic primary-key
  tiebreakers, adhering strictly to ordered-offset semantics rather than Relay cursor pagination.
- **No DISTINCT injection**: Flat list order queries avoid injecting `SELECT DISTINCT` into SQL,
  even across to-many relation ordering.
- **Zero-limit short-circuit**: `limit: 0` returns empty lists (`[]` or `none()`) with exactly
  0 row-fetching SQL queries executed.
- **Slicing**: Queryset slicing `queryset[offset:offset + limit]` occurs only after visibility
  filtering and OrderSet application.

### Module responsibilities and exports

- **Single responsibility principle**:
  - `list_field.py`: Field factory, argument normalization, error generation, and execution
    pipeline orchestration.
  - `resource_policy.py`: Execution resource limits, deadline checks, and row bounding helpers
    (`bounded_rows`, `bounded_rows_async`).
  - `orders/sets.py`: OrderSet definition, input normalization, active term inspection, and
    apply execution (`apply_sync`, `apply_async`).
  - `utils/querysets.py`: QuerySet sealing, visibility application, post-OrderSet candidate
    validation, and async completion adapter protocol.
  - `optimizer/extension.py`: GraphQL selection tree planning, safely unwrapping and rewrapping
    the async completion adapter.
- **Public exports**: Verified `django_strawberry_framework/__init__.py` re-exports
  `DjangoListField` and `ListArgumentError` in `__all__`. Pinned in `tests/base/test_init.py`.

### Comment and docstring coherence

- All docstrings updated in Slice 5 follow PEP 257 and project conventions (line length 99,
  symbol path references `path::QualifiedName` instead of volatile line numbers).
- Zero banned staging tokens (`TODO`, `planned`, `Slice N`) remain in production code or
  standing documentation.
- Terminology is strictly **ordered offset**, never claiming stable or repeatable pagination.

---

## Test execution

### 1. Non-sharded focused test suite

Command:
```bash
uv run pytest \
  tests/base/test_init.py \
  tests/test_list_field.py \
  tests/test_resource_policy.py \
  tests/orders/test_sets.py \
  tests/utils/test_querysets.py \
  tests/optimizer/test_extension.py \
  examples/fakeshop/test_query/test_list_field_api.py \
  examples/fakeshop/test_query/test_list_field_async_api.py \
  examples/fakeshop/test_query/test_resource_policy_api.py \
  --no-cov
```

Result:
```text
============================= 955 passed in 17.74s =============================
```
Exit code: **0**. Zero test failures, zero warnings, zero regressions.

### 2. Sharded live acceptance test suite

Command:
```bash
FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query/test_multi_db.py --no-cov
```

Result:
```text
============================== 12 passed in 8.03s ==============================
```
Exit code: **0**. Both routing mismatch tests (`test_post_orderset_routing_mismatch_rejected_on_sharded_db`
and `test_post_orderset_hints_routing_mismatch_rejected_on_sharded_db`) passed cleanly under
`FAKESHOP_SHARDED=1`.

---

## Failability and fail-open summary across card

### Failability proof inventory

Across the five slices of Card 050, a total of **56 failability boundaries** were defined,
mechanically proved via `scripts/prove_failability.py`, and verified:
- **Slice 1 (Argument normalization)**: 9 boundaries proved in
  `docs/builder/temp-tests/slice-1/proofs.json`. Every boundary failed >= 3 test rows (range:
  3 to 17 rows). Zero weakly pinned boundaries.
- **Slice 2 (OrderBy pipeline)**: 22 boundaries proved in
  `docs/builder/temp-tests/slice-2/proofs.json`. Every boundary failed >= 2 test rows (range:
  2 to 7 rows). Zero weakly pinned boundaries.
- **Slice 3 (SQL and unit contracts)**: 25 boundaries proved in
  `docs/builder/temp-tests/slice-3/proofs.json`. Every boundary failed >= 2 test rows (range:
  2 to 76 rows). Zero weakly pinned boundaries. All 9 floor boundaries independently re-run
  by Worker 3 with 100% agreement.
- **Slice 4 (Live acceptance)**: 0 new production boundaries (test-only tier).
- **Slice 5 (Documentation fold-in)**: 0 new production boundaries (doc-only tier).

All 56 boundaries carry durable proof records, verified pre-mutation bit-level file
restorations, and zero collection or setup errors.

### Fail-open audit

The Card 050 implementation contains zero fail-open shapes:
- Type checks use explicit `isinstance(..., bool)` before `isinstance(..., int)`.
- Identity guards explicitly distinguish `None` and `strawberry.UNSET`.
- Sliced and combined querysets fail closed with `ConfigurationError` at source and result seals.
- Mismatched multi-database routing (`_db` and `_hints`) fails closed with `ConfigurationError`.
- `_AsyncQuerySetRows` implements only `__aiter__` and fails closed on synchronous iteration.
- `_close_async_iterator` preserves primary exceptions while attaching cleanup diagnostics to
  `__notes__`.

---

## Spec reconciliation

Zero spec modifications or reconciliations were required during Card 050. All five slices
were planned, implemented, tested, and verified in strict accordance with
[`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050] and its rationale companion
[`docs/spec-050-list_field_arguments-0_0_15-rationale.md`][spec-050-rationale].

---

## Summary

The cross-slice integration pass for Card 050 (`DjangoListField` argument surface: `offset`,
`limit`, and `orderBy`) has been successfully completed:
1. All five slice artifacts were verified in slice order and confirmed at `final-accepted`.
2. Static inspection overviews and stripped Python source files in `docs/shadow/` were
   refreshed and verified across all touched files.
3. Cross-file repeated string literals and import dependency directions were analyzed and
   confirmed clean, acyclic, and strictly one-way.
4. `What looks solid` and `DRY findings` across all slice reviews were verified with zero
   deferred follow-ups.
5. Repository-wide staged anchor sweep confirmed zero live `# TODO(spec-050 ...)` anchors
   remain in source, tests, or standing documentation.
6. Helper existence, naming conventions, fail-closed error handling, ORM patterns, and
   module responsibilities were confirmed coherent and non-duplicative.
7. The full focused test suite (955 tests non-sharded, 12 tests sharded) passed with 100%
   success and zero regressions.
8. Card 050 is fully closed in `KANBAN.md` and `KANBAN.html` with all Definition of Done
   items satisfied.

---

## Final status

`integration-accepted`

<!-- LINK DEFINITIONS -->

<!-- Root -->
[pkg-init]: ../../django_strawberry_framework/__init__.py

<!-- docs/ -->
[spec-050]: ../spec-050-list_field_arguments-0_0_15.md
[spec-050-rationale]: ../spec-050-list_field_arguments-0_0_15-rationale.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-050]: build-050-list_field_arguments-0_0_15.md
[build-md]: BUILD.md
[bld-slice-1]: bld-slice-1-argument_normalization.md
[bld-slice-2]: bld-slice-2-orderby_pipeline.md
[bld-slice-3]: bld-slice-3-sql_and_unit_contracts.md
[bld-slice-4]: bld-slice-4-live_acceptance.md
[bld-slice-5]: bld-slice-5-documentation_fold_in.md

<!-- django_strawberry_framework/ -->
[list-field]: ../../django_strawberry_framework/list_field.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[strawberry-patches]: ../../django_strawberry_framework/_strawberry_patches.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
