# DRY review: `django_strawberry_framework/optimizer/nested_fetch.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/nested_fetch.py` is the architectural seam and registry for pluggable nested Relay connection prefetch strategies ([spec-002][spec-002], [spec-004][spec-004], [spec-010][spec-010], [spec-016][spec-016], [spec-023][spec-023], [spec-025][spec-025], [spec-028][spec-028], [spec-033][spec-033], [spec-035][spec-035], [spec-051][spec-051], [spec-063][spec-063]). It implements the Prisma-inspired `JoinSelectBuilder` design pattern: one stable query planner interface with swappable execution backends behind it.

While the private planner ([`optimizer/nested_planner.py::plan_connection_relation`][optimizer-nested-planner]) owns strategy-independent tasks (recognition, Decision-6 fallback shapes, divergent-alias per-response-key resolution, child queryset construction, deterministic ordering, and slice window calculation), it delegates the physical fetching mechanism to the active [`NestedConnectionStrategy`][optimizer-nested-fetch] via an isolated candidate [`OptimizationPlan`][optimizer-plans]. The candidate plan is merged only if the strategy's `plan()` method returns `True`; refusal or exceptions leave the selection unplanned without corrupting planner state.

It owns the following architectural responsibilities:

1. **Strategy-Independent Safety Classifier:**
   - [`unwindowable_child_queryset_reason`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::unwindowable_child_queryset_reason`): Central safety gate that inspects a child `QuerySet` and returns a stable classification string (`"sliced"`, `"select_for_update"`, `"combined"`, `"distinct"`, `"values"`) or `None` if windowable. Used by [`nested_planner.py`][optimizer-nested-planner] before constructing requests and reused as the first line of defense by fetch-time query recognizers ([`lateral_fetch._recognize_lateral_fetch`][optimizer-lateral-fetch], [`single_parent_fetch._fetch_single_parent_rows`][optimizer-single-parent-fetch]).

2. **Recognized QuerySet Skeleton:**
   - [`RecognizedFetchQuerySet`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::RecognizedFetchQuerySet`): Shared abstract `QuerySet` subclass for querysets carrying a recognized strategy-specific fast path.
   - [`RecognizedFetchQuerySet._clone`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::RecognizedFetchQuerySet._clone`): Preserves the strategy spec attribute named by `_dst_spec_attr` and the captured `_dst_window_signature` across Django internal queryset cloning operations (`.using()`, `.filter()`, `_add_hints`).
   - [`RecognizedFetchQuerySet.rebind`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::RecognizedFetchQuerySet.rebind`): Factory method that rebinds a plain windowed `QuerySet` as a recognized subclass, stores the strategy spec, and captures the planned window qualification signature via [`window_predicate_signature`][optimizer-lateral-fetch] before Django's prefetch machinery appends parent `__in` filters.
   - [`RecognizedFetchQuerySet._fetch_recognized_rows`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::RecognizedFetchQuerySet._fetch_recognized_rows`): Abstract hook method for subclasses to return strategy-specific row instances or `None` on unrecognized query shapes.
   - [`RecognizedFetchQuerySet._fetch_all`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::RecognizedFetchQuerySet._fetch_all`): Coordinates execution by attempting `_fetch_recognized_rows()`, populating `_result_cache` on recognition, and delegating to `super()._fetch_all()` to ensure nested `prefetch_related` passes and windowed fallbacks run reliably.

3. **Plannable Nested Connection Request:**
   - [`NestedConnectionRequest`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::NestedConnectionRequest`): Immutable frozen dataclass encapsulating all planner facts for one nested connection (`django_field`, `relation_field_name`, `prefix`, `child_queryset`, `join`, `order_by`, `offset`, `limit`, `reverse`, `with_total_count`, `to_attr`, `lookup`, `next_page_probe`, `keyset_seek`).
   - [`NestedConnectionRequest.__post_init__`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::NestedConnectionRequest.__post_init__`): Calls [`assert_window_fetch_mode_for`][utils-connections] to strictly enforce mutual exclusion between `next_page_probe` and `with_total_count` at the strategy boundary.

4. **Strategy Protocol & Public Selection:**
   - [`NestedConnectionStrategy`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::NestedConnectionStrategy`): `Protocol` defining the strategy interface (`name: str`, `plan(request, plan) -> bool`).
   - [`NestedConnectionStrategy.plan`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::NestedConnectionStrategy.plan`): Attaches fetch directives to the isolated plan; returning `True` marks the request planned.
   - `StrategySelection` (`django_strawberry_framework/optimizer/nested_fetch.py::StrategySelection`): Unified public type alias `str | NestedConnectionStrategy` used across [`DjangoOptimizerExtension`][optimizer-extension], [`OptimizerHint`][optimizer-hints], and the planner.

5. **Prefetch Attachment Correctness Floor:**
   - [`attach_windowed_prefetch`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::attach_windowed_prefetch`): Canonical implementation of the spec-033 windowed prefetch floor. Calls [`apply_window_pagination`][optimizer-plans] with all request parameters, applies an optional `wrap` callback (e.g. for `LateralQuerySet` or `SingleParentWindowQuerySet` rebinding), appends a unique `Prefetch` to `plan.prefetch_related`, and returns `True`.

6. **Strategy Implementations & Singletons:**
   - [`WindowedPrefetchStrategy`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::WindowedPrefetchStrategy`): Default nested prefetch strategy (`name = "windowed"`).
   - [`WindowedPrefetchStrategy.plan`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::WindowedPrefetchStrategy.plan`): Inspects the request for single-parent eligibility via [`single_parent_spec`][optimizer-single-parent-fetch]; wraps with [`SingleParentWindowQuerySet.rebind`][optimizer-single-parent-fetch] when eligible, or attaches standard windowed prefetch.
   - [`WINDOWED_STRATEGY`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::WINDOWED_STRATEGY`): Stateless singleton instance of `WindowedPrefetchStrategy`.
   - [`AutoNestedConnectionStrategy`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::AutoNestedConnectionStrategy`): Automatic multi-backend strategy (`name = "auto"`).
   - [`AutoNestedConnectionStrategy.plan`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::AutoNestedConnectionStrategy.plan`): Delegates planning to [`LATERAL_STRATEGY`][optimizer-lateral-fetch], producing a lateral-capable windowed queryset whose fetch-time database alias selects PostgreSQL lateral SQL on Postgres while non-Postgres databases execute the windowed ORM body.
   - [`AUTO_STRATEGY`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::AUTO_STRATEGY`): Stateless singleton instance of `AutoNestedConnectionStrategy`.

7. **Strategy Registry & Execution Context:**
   - [`_builtin_strategies`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::_builtin_strategies`): `@cache`-memoized function lazily constructing the immutable `MappingProxyType({"windowed": WINDOWED_STRATEGY, "lateral": LATERAL_STRATEGY})` to break import cycles cleanly.
   - [`resolve_strategy`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::resolve_strategy`): Authoritative validator and resolver converting strategy names, `"auto"`, `None` (falling back to [`nested_connection_strategy_setting`][conf]), or custom strategy instances into validated `NestedConnectionStrategy` instances, failing loudly on typos with typed [`ConfigurationError`][exceptions].
   - `_active_strategy` (`django_strawberry_framework/optimizer/nested_fetch.py::_active_strategy`): `ContextVar` carrying the active execution's strategy, set during [`DjangoOptimizerExtension.on_execute`][optimizer-extension].
   - [`active_strategy`][optimizer-nested-fetch] (`django_strawberry_framework/optimizer/nested_fetch.py::active_strategy`): Retrieves the current execution's active strategy, defaulting to `WINDOWED_STRATEGY` for direct callers and test suites.

Connected behavior examined:
- [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner]: Builds [`NestedConnectionRequest`][optimizer-nested-fetch] and resolves strategy via [`resolve_strategy`][optimizer-nested-fetch] / [`active_strategy`][optimizer-nested-fetch], checking [`unwindowable_child_queryset_reason`][optimizer-nested-fetch] before planning.
- [`django_strawberry_framework/optimizer/lateral_fetch.py`][optimizer-lateral-fetch]: Subclasses [`RecognizedFetchQuerySet`][optimizer-nested-fetch] as `LateralQuerySet`, implements [`NestedConnectionStrategy`][optimizer-nested-fetch] via `LateralPrefetchStrategy`, and reuses [`unwindowable_child_queryset_reason`][optimizer-nested-fetch].
- [`django_strawberry_framework/optimizer/single_parent_fetch.py`][optimizer-single-parent-fetch]: Subclasses [`RecognizedFetchQuerySet`][optimizer-nested-fetch] as `SingleParentWindowQuerySet`, consumed by [`WindowedPrefetchStrategy.plan`][optimizer-nested-fetch].
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]: Resolves configured strategy via [`resolve_strategy`][optimizer-nested-fetch] and publishes it to `_active_strategy` in `on_execute()`.
- [`django_strawberry_framework/optimizer/hints.py`][optimizer-hints]: Validates per-field strategy overrides via [`resolve_strategy`][optimizer-nested-fetch] and exposes `StrategySelection`.
- [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans]: Provides [`apply_window_pagination`][optimizer-plans] and [`append_prefetch_unique`][optimizer-plans] called by [`attach_windowed_prefetch`][optimizer-nested-fetch].
- [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy]: Supplies join classifications stored on `NestedConnectionRequest.join`.
- [`django_strawberry_framework/conf.py`][conf]: Supplies [`nested_connection_strategy_setting`][conf] read by `resolve_strategy(None)`.
- [`django_strawberry_framework/utils/connections.py`][utils-connections]: Supplies [`assert_window_fetch_mode_for`][utils-connections] called by `NestedConnectionRequest.__post_init__`.
- [`tests/optimizer/test_nested_fetch.py`][test-optimizer-nested-fetch]: 14 unit tests covering strategy resolution, registry caching, contextvars, error formatting, and safety matrix.
- [`tests/test_lateral_pg_parity.py`][test-lateral-pg-parity]: Live PostgreSQL integration suite validating parity across strategy selections.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/nested_fetch.py --include-constants`):
- Parsed 1 target file, 447 lines.
- Inventory of symbols (20 definitions):
  - 2 constants: [`WINDOWED_STRATEGY`][optimizer-nested-fetch], [`AUTO_STRATEGY`][optimizer-nested-fetch].
  - 5 classes: [`RecognizedFetchQuerySet`][optimizer-nested-fetch], [`NestedConnectionRequest`][optimizer-nested-fetch], [`NestedConnectionStrategy`][optimizer-nested-fetch], [`WindowedPrefetchStrategy`][optimizer-nested-fetch], [`AutoNestedConnectionStrategy`][optimizer-nested-fetch].
  - 8 methods: [`RecognizedFetchQuerySet._clone`][optimizer-nested-fetch], [`RecognizedFetchQuerySet.rebind`][optimizer-nested-fetch], [`RecognizedFetchQuerySet._fetch_recognized_rows`][optimizer-nested-fetch], [`RecognizedFetchQuerySet._fetch_all`][optimizer-nested-fetch], [`NestedConnectionRequest.__post_init__`][optimizer-nested-fetch], [`NestedConnectionStrategy.plan`][optimizer-nested-fetch], [`WindowedPrefetchStrategy.plan`][optimizer-nested-fetch], [`AutoNestedConnectionStrategy.plan`][optimizer-nested-fetch].
  - 5 functions: [`unwindowable_child_queryset_reason`][optimizer-nested-fetch], [`attach_windowed_prefetch`][optimizer-nested-fetch], [`_builtin_strategies`][optimizer-nested-fetch], [`resolve_strategy`][optimizer-nested-fetch], [`active_strategy`][optimizer-nested-fetch].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `django_strawberry_framework/optimizer/nested_fetch.py` provides the unified seam and protocol definition ([`NestedConnectionStrategy`][optimizer-nested-fetch], `StrategySelection = str | NestedConnectionStrategy`) consumed identically across schema hints ([`OptimizerHint.strategy`][optimizer-hints]), extension configuration ([`DjangoOptimizerExtension`][optimizer-extension]), and query planning ([`nested_planner.py`][optimizer-nested-planner]). It establishes [`attach_windowed_prefetch`][optimizer-nested-fetch] as the single correctness floor and prefetch attachment mechanism shared between `WindowedPrefetchStrategy` and `LateralPrefetchStrategy`. It provides [`RecognizedFetchQuerySet`][optimizer-nested-fetch] as the shared base class for querysets with recognized execution paths (`LateralQuerySet` and `SingleParentWindowQuerySet`), centralizing `_clone`, `rebind`, and `_fetch_all` lifecycle mechanics. It centralizes [`unwindowable_child_queryset_reason`][optimizer-nested-fetch] for strategy-independent safety validation across planner and runtime fetch recognizers. Zero cross-flavor duplication.

2. **Sync and async twins:**
   Zero duplication. Plan-time strategy resolution and prefetch configuration are purely synchronous, side-effect-free object and query manipulations. Execution-time query evaluation via [`RecognizedFetchQuerySet._fetch_all`][optimizer-nested-fetch] integrates directly into Django's prefetch machinery, supporting both synchronous evaluation and asynchronous query execution without duplicated async execution methods.

3. **Derived rather than repeated knowledge:**
   - Fetch mode validation in [`NestedConnectionRequest.__post_init__`][optimizer-nested-fetch] delegates directly to [`assert_window_fetch_mode_for`][utils-connections], which dynamically resolves the window range plan.
   - [`unwindowable_child_queryset_reason`][optimizer-nested-fetch] derives safety classifications dynamically from AST and query flags (`query.is_sliced`, `query.select_for_update`, `query.combinator`, `query.distinct`, and `_iterable_class`).
   - [`_builtin_strategies`][optimizer-nested-fetch] derives the strategy mapping lazily and caches the immutable result with `@cache`.
   - [`resolve_strategy`][optimizer-nested-fetch] resolves string names against `_builtin_strategies()` or [`nested_connection_strategy_setting`][conf] without duplicating registry lookup logic.
   - [`AutoNestedConnectionStrategy`][optimizer-nested-fetch] derives its multi-backend behavior by delegating to [`LATERAL_STRATEGY`][optimizer-lateral-fetch], allowing Postgres to execute lateral SQL while non-Postgres databases execute the windowed ORM body via `LateralQuerySet`.
   No derived fact is hardcoded or duplicated.

4. **Inverse and round-trip pairs:**
   - `_active_strategy` ContextVar management: Setting the active strategy via `_active_strategy.set(strategy)` is paired with `_active_strategy.reset(token)` in [`DjangoOptimizerExtension.on_execute`][optimizer-extension], guaranteeing round-trip restoration of context state.
   - `RecognizedFetchQuerySet.rebind`: Rebinds a plain windowed queryset as a recognized subclass and captures `_dst_window_signature`, with `_clone` preserving spec and signature across all subsequent Django cloning operations.
   - Request construction and attachment: [`NestedConnectionRequest`][optimizer-nested-fetch] packages planner facts into an immutable record, and [`attach_windowed_prefetch`][optimizer-nested-fetch] cleanly unpacks them into [`apply_window_pagination`][optimizer-plans] and `Prefetch(to_attr=...)`.

5. **Contracts restated in another medium:**
   The nested connection strategy seam contracts are codified across:
   - Code: [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch], [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner], [`django_strawberry_framework/optimizer/lateral_fetch.py`][optimizer-lateral-fetch], [`django_strawberry_framework/optimizer/single_parent_fetch.py`][optimizer-single-parent-fetch], [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension], [`django_strawberry_framework/optimizer/hints.py`][optimizer-hints], [`django_strawberry_framework/conf.py`][conf], [`django_strawberry_framework/utils/connections.py`][utils-connections];
   - Specifications: [`docs/SPECS/spec-002-optimizer-0_0_2.md`][spec-002], [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004], [`docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md`][spec-010], [`docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`][spec-016], [`docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`][spec-023], [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`][spec-025], [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028], [`docs/SPECS/spec-033-nested_connection_execution_plan-0_0_9.md`][spec-033], [`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`][spec-035], [`docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`][spec-051], [`docs/SPECS/spec-063-structural_templates-0_1_6.md`][spec-063];
   - Test suites: [`tests/optimizer/test_nested_fetch.py`][test-optimizer-nested-fetch] (14 unit tests covering strategy resolution, registry caching, contextvars, error formatting, and safety matrix), [`tests/optimizer/test_nested_planner.py`][test-optimizer-nested-planner], [`tests/optimizer/test_lateral_fetch.py`][test-optimizer-lateral-fetch], [`tests/optimizer/test_single_parent_fetch.py`][test-optimizer-single-parent-fetch], [`tests/optimizer/test_walker.py`][test-optimizer-walker], [`tests/optimizer/test_extension.py`][test-optimizer-extension], [`tests/optimizer/test_hints.py`][test-optimizer-hints], [`tests/test_lateral_pg_parity.py`][test-lateral-pg-parity];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new built-in strategy backend, e.g. SQLite correlated JSON subquery strategy `"sqlite_correlated"`):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch] (adding `"sqlite_correlated": SQLITE_CORRELATED_STRATEGY` to [`_builtin_strategies`][optimizer-nested-fetch]), plus the new strategy module itself.
  - *Site count:* 1 in target.
- **Posited change 2 (Adding a new unwindowable queryset reason / guard shape, e.g. detecting unwindowable raw SQL queries):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch] ([`unwindowable_child_queryset_reason`][optimizer-nested-fetch]), which automatically protects planner ([`nested_planner.py`][optimizer-nested-planner]) and recognizers ([`lateral_fetch.py`][optimizer-lateral-fetch], [`single_parent_fetch.py`][optimizer-single-parent-fetch]).
  - *Site count:* 1 in target.
- **Posited change 3 (Changing the strategy-selection setting fallback default from `"windowed"` to `"auto"`):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/conf.py`][conf] ([`nested_connection_strategy_setting`][conf]), with [`resolve_strategy(None)`][optimizer-nested-fetch] automatically respecting it.
  - *Site count:* 1 (0 in target).
- **Posited change 4 (Updating `RecognizedFetchQuerySet` cloning mechanics to propagate additional cache metadata):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch] ([`RecognizedFetchQuerySet._clone`][optimizer-nested-fetch]), which automatically propagates to `LateralQuerySet` and `SingleParentWindowQuerySet`.
  - *Site count:* 1 in target.
- **Posited change 5 (Adding a new parameter to the correctness floor `attach_windowed_prefetch`):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch] ([`attach_windowed_prefetch`][optimizer-nested-fetch]), inherited by all strategy backends.
  - *Site count:* 1 in target.

### Rejected candidates

1. **Moving strategy resolution into `nested_planner.py` or `hints.py`:**
   - Disproved per [spec-033][spec-033] and [spec-035][spec-035]. Strategy resolution is an extension-level configuration concern shared by the planner, extension constructor, and field-level hints. Housing `resolve_strategy` in `nested_fetch.py` alongside the `NestedConnectionStrategy` protocol keeps the dependency graph acyclic and clean.
2. **Hardcoding strategy instantiation inside `DjangoOptimizerExtension` without a protocol seam:**
   - Disproved. The protocol seam (`NestedConnectionStrategy`) allows pluggable backend implementations (such as Postgres `CROSS JOIN LATERAL`, single-parent optimizations, and consumer-authored strategies) without coupling the extension directly to database-specific engines.
3. **Making `NestedConnectionRequest` a mutable class or omitting post-init validation:**
   - Disproved. Frozen immutability guarantees thread safety and cache stability. Enforcing mutual exclusion between probe mode and partition count in `__post_init__` guarantees fail-loud detection of invalid planning requests at the boundary.
4. **Extracting `RecognizedFetchQuerySet` to a separate standalone utility module:**
   - Disproved. `RecognizedFetchQuerySet` is the execution backbone for recognized nested fetch strategies. Keeping it in `nested_fetch.py` provides cohesive locality without module proliferation.

## Opportunities

None — `django_strawberry_framework/optimizer/nested_fetch.py` is a concise (447 lines), robust, and fully consolidated module. It acts as the singular source of truth for nested connection strategy protocols, registry resolution, execution contextvars, and query safety classification, exhibiting zero duplicate policy.

## Judgment

Zero-edit review. `optimizer/nested_fetch.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/nested_fetch.py --review docs/dry/dry-file-optimizer__nested_fetch.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Worker 2 independently verified the nested connection fetch strategy seam, protocol definition, query safety classification, queryset lifecycle mechanics, and registry resolution across the codebase:

1. **Safety Gate & QuerySet Execution Lifecycle:**
   - Re-traced [`unwindowable_child_queryset_reason`][optimizer-nested-fetch] across the 5 unsafe child queryset states (`"sliced"`, `"select_for_update"`, `"combined"`, `"distinct"`, `"values"`). Verified that it serves as the single source of truth for both plan-time safety rejection in [`nested_planner.py`][optimizer-nested-planner] and fetch-time fail-closed detection in [`lateral_fetch._recognize_lateral_fetch`][optimizer-lateral-fetch] and [`single_parent_fetch._fetch_single_parent_rows`][optimizer-single-parent-fetch].
   - Validated [`RecognizedFetchQuerySet`][optimizer-nested-fetch] mechanics:
     - `rebind()` cleanly mutates `__class__` on a fresh `_chain()` clone, attaches the strategy spec attribute named by `_dst_spec_attr`, and captures `_dst_window_signature` via [`window_predicate_signature`][optimizer-lateral-fetch] before Django prefetch filters are appended.
     - `_clone()` faithfully propagates `_dst_spec_attr` and `_dst_window_signature` through all internal Django queryset cloning operations (`.using()`, `.filter()`, `_add_hints()`).
     - `_fetch_all()` coordinates execution: recognized rows populate `_result_cache`, while `super()._fetch_all()` guarantees that downstream `prefetch_related` lookups and unwindowable fallbacks execute without regressions.

2. **Nested Connection Request & Seam Architecture:**
   - Verified that [`NestedConnectionRequest`][optimizer-nested-fetch] encapsulates all planning facts into an immutable frozen dataclass, strictly guarding the boundary by calling [`assert_window_fetch_mode_for`][utils-connections] in `__post_init__` to reject contradictory probe and total count configurations.
   - Validated [`attach_windowed_prefetch`][optimizer-nested-fetch] as the universal correctness floor, delegating to [`apply_window_pagination`][optimizer-plans] and [`append_prefetch_unique`][optimizer-plans], with optional `wrap` callback support for strategy rebinding.

3. **Strategy Implementations, Resolution, & Context State:**
   - Verified [`WindowedPrefetchStrategy`][optimizer-nested-fetch] plans standard windowed prefetches and seamlessly delegates single-parent eligible requests to [`SingleParentWindowQuerySet`][optimizer-single-parent-fetch].
   - Verified [`AutoNestedConnectionStrategy`][optimizer-nested-fetch] plans lateral-capable windowed querysets via [`LATERAL_STRATEGY`][optimizer-lateral-fetch], dynamically selecting PostgreSQL lateral SQL at fetch time while executing standard windowed ORM queries on non-Postgres backends.
   - Verified [`_builtin_strategies`][optimizer-nested-fetch] and [`resolve_strategy`][optimizer-nested-fetch]: lazy caching breaks import cycles cleanly, while string names, `"auto"`, setting defaults via [`nested_connection_strategy_setting`][conf], and custom `NestedConnectionStrategy` instances are validated with typed [`ConfigurationError`][exceptions] on invalid inputs.
   - Verified `_active_strategy` ContextVar isolation and default fallback to [`WINDOWED_STRATEGY`][optimizer-nested-fetch] in [`active_strategy`][optimizer-nested-fetch].

4. **Duplication Probing Matrix & Single-Edit Site Test:**
   - All 5 axes of the mandatory probing matrix were independently inspected and confirmed discharged.
   - Single-edit-site counts hold at 1 for all posited changes.

5. **Static Analysis & Test Verification:**
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/nested_fetch.py --review docs/dry/dry-file-optimizer__nested_fetch.md --include-constants`: confirmed 20 target definitions covered with 0 errors.
   - Executed unit test suite `tests/optimizer/test_nested_fetch.py` (16/16 tests passing).
   - Executed related test suites `tests/optimizer/test_lateral_fetch.py`, `tests/optimizer/test_single_parent_fetch.py`, `tests/optimizer/test_walker.py`, and `tests/optimizer/test_nested_index_advisory.py` (383/383 tests passing).

Verification complete. Setting `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-002]: ../SPECS/spec-002-optimizer-0_0_2.md
[spec-004]: ../SPECS/spec-004-optimizer_beyond-0_0_3.md
[spec-010]: ../SPECS/appx/spec-010-foundation-0_0_4-rationale.md
[spec-016]: ../SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md
[spec-023]: ../SPECS/appx/spec-023-multi_db-0_0_7-rationale.md
[spec-025]: ../SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-033]: ../SPECS/spec-033-nested_connection_execution_plan-0_0_9.md
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-051]: ../SPECS/spec-051-boundary_dry_squeeze-0_0_15.md
[spec-063]: ../SPECS/spec-063-structural_templates-0_1_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[keyset]: ../../django_strawberry_framework/keyset.py
[optimizer-context]: ../../django_strawberry_framework/optimizer/_context.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[optimizer-hints]: ../../django_strawberry_framework/optimizer/hints.py
[optimizer-join-taxonomy]: ../../django_strawberry_framework/optimizer/join_taxonomy.py
[optimizer-lateral-fetch]: ../../django_strawberry_framework/optimizer/lateral_fetch.py
[optimizer-nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[optimizer-nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py
[optimizer-single-parent-fetch]: ../../django_strawberry_framework/optimizer/single_parent_fetch.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[utils-connections]: ../../django_strawberry_framework/utils/connections.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->
[test-lateral-pg-parity]: ../../tests/test_lateral_pg_parity.py
[test-optimizer-extension]: ../../tests/optimizer/test_extension.py
[test-optimizer-hints]: ../../tests/optimizer/test_hints.py
[test-optimizer-join-taxonomy]: ../../tests/optimizer/test_join_taxonomy.py
[test-optimizer-lateral-fetch]: ../../tests/optimizer/test_lateral_fetch.py
[test-optimizer-nested-fetch]: ../../tests/optimizer/test_nested_fetch.py
[test-optimizer-nested-planner]: ../../tests/optimizer/test_nested_planner.py
[test-optimizer-plans]: ../../tests/optimizer/test_plans.py
[test-optimizer-single-parent-fetch]: ../../tests/optimizer/test_single_parent_fetch.py
[test-optimizer-walker]: ../../tests/optimizer/test_walker.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
