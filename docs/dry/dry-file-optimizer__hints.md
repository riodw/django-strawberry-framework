# DRY review: `django_strawberry_framework/optimizer/hints.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/hints.py` is the canonical declaration and validation surface for per-field query optimization overrides in the framework ([spec-002][spec-002], [spec-003][spec-003], [spec-004][spec-004], [spec-023][spec-023], [spec-030][spec-030], [spec-033][spec-033], [spec-051][spec-051]). It defines the [`OptimizerHint`][optimizer-hints] frozen dataclass, class-level sentinels, factory classmethods, construction-time invariant validators, and fail-closed skip predicates used to customize AST selection walks, SQL join planning, Relay nested-connection strategies, and schema auditing.

It owns the following architectural responsibilities:

1. **Typed Optimization Directive (`OptimizerHint`):**
   - [`OptimizerHint`][optimizer-hints] (`django_strawberry_framework/optimizer/hints.py::OptimizerHint`): Frozen, immutable dataclass encapsulating per-relation optimization instructions configured in `DjangoType.Meta.optimizer_hints`:
     - `force_select`: Boolean flag forcing SQL `select_related` join optimization regardless of cardinality (restricted to forward and reverse single relations).
     - `force_prefetch`: Boolean flag forcing Django `prefetch_related` batch-query optimization regardless of relation cardinality.
     - `prefetch_obj`: Explicit `django.db.models.Prefetch` instance providing consumer-customized child querysets, filters, or annotations. Acts as a terminal leaf in optimizer traversal (nested fields are not recursed) and marks the resulting plan uncacheable.
     - `skip`: Boolean flag excluding the relation from optimizer AST planning and schema audit warnings entirely.
     - `nested_strategy`: Relay nested-connection fetch strategy override (e.g. `"windowed"`, `"lateral"`, `"auto"`, or a [`NestedConnectionStrategy`][optimizer-nested-fetch] instance) validated at construction time via [`resolve_strategy`][optimizer-nested-fetch].
   - [`OptimizerHint.SKIP`][optimizer-hints] (`django_strawberry_framework/optimizer/hints.py::OptimizerHint.SKIP`): Singleton-like frozen ClassVar sentinel (`OptimizerHint(skip=True)`) providing a standard opt-out handle.

2. **Factory Classmethods:**
   - [`OptimizerHint.select_related`][optimizer-hints] (`django_strawberry_framework/optimizer/hints.py::OptimizerHint.select_related`): Classmethod returning `cls(force_select=True)`.
   - [`OptimizerHint.prefetch_related`][optimizer-hints] (`django_strawberry_framework/optimizer/hints.py::OptimizerHint.prefetch_related`): Classmethod returning `cls(force_prefetch=True)`.
   - [`OptimizerHint.prefetch`][optimizer-hints] (`django_strawberry_framework/optimizer/hints.py::OptimizerHint.prefetch`): Classmethod validating and attaching a `django.db.models.Prefetch` instance via `cls(prefetch_obj=_require_prefetch(obj))`.
   - [`OptimizerHint.strategy`][optimizer-hints] (`django_strawberry_framework/optimizer/hints.py::OptimizerHint.strategy`): Classmethod validating and configuring a nested connection fetch strategy via `cls(nested_strategy=_require_strategy(name))`.

3. **Construction-Time Validation & Invariant Enforcement:**
   - [`_require_prefetch`][optimizer-hints] (`django_strawberry_framework/optimizer/hints.py::_require_prefetch`): Single authoritative validator verifying that an object is a concrete `django.db.models.Prefetch` instance, raising typed [`ConfigurationError`][exceptions] on invalid types or `None` to prevent silent no-op degradation.
   - [`_require_strategy`][optimizer-hints] (`django_strawberry_framework/optimizer/hints.py::_require_strategy`): Single authoritative validator verifying strategy selection names and instances via [`resolve_strategy`][optimizer-nested-fetch], raising typed [`ConfigurationError`][exceptions] on typos or `None`.
   - [`OptimizerHint.__post_init__`][optimizer-hints] (`django_strawberry_framework/optimizer/hints.py::OptimizerHint.__post_init__`): Construction-time validator enforcing flag types (`bool`) and strict mutual exclusion rules:
     - `skip` cannot combine with `force_select`, `force_prefetch`, or `prefetch_obj`.
     - `force_select` and `force_prefetch` cannot both be `True`.
     - `prefetch_obj` cannot combine with `force_select` or `force_prefetch`.
     - `nested_strategy` cannot combine with `skip`, `prefetch_obj`, or `force_select` (`force_prefetch` is redundant-but-allowed).
     - Validates `prefetch_obj` through [`_require_prefetch`][optimizer-hints] and `nested_strategy` through [`_require_strategy`][optimizer-hints].

4. **Fail-Closed Skip Dispatch Helper:**
   - [`hint_is_skip`][optimizer-hints] (`django_strawberry_framework/optimizer/hints.py::hint_is_skip`): Centralized predicate function determining whether a hint object represents a skip directive (`hint is OptimizerHint.SKIP or getattr(hint, "skip", False)`). Defensively handles `None`, foreign objects, or unexpected shapes to guarantee fail-closed execution during AST walks and schema auditing.

Connected behavior examined:
- [`django_strawberry_framework/types/base.py`][types-base]: Ingests `Meta.optimizer_hints` during `DjangoType` subclassing (`_meta_optimizer_hints`), validates hint field names against model relations and hint values via `_validate_optimizer_hints`, attaching normalized hints to [`DjangoTypeDefinition.optimizer_hints`][types-definition].
- [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]: Resolves hints via `_resolve_optimizer_hints` and applies directives in `_apply_hint`, rebasing custom prefetches via `_prefetch_hint_for_path`, checking `select_related` cardinality constraints, and setting `plan.cacheable = False` for consumer-provided prefetches.
- [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner]: Inspects hints via `_select_nested_strategy` and [`hint_is_skip`][optimizer-hints] during nested Relay connection planning.
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]: Uses [`hint_is_skip`][optimizer-hints] during `check_schema` to bypass unregistered target type warnings for skipped relations.
- [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch]: Defines [`StrategySelection`][optimizer-nested-fetch] and [`resolve_strategy`][optimizer-nested-fetch] consumed at runtime by `OptimizerHint.strategy`.
- [`django_strawberry_framework/__init__.py`][package-init]: Re-exports [`OptimizerHint`][optimizer-hints] at top level.
- [`tests/optimizer/test_hints.py`][test-optimizer-hints]: Dedicated unit test suite verifying `SKIP` sentinel, factory methods, frozen immutability, equality, mutual exclusion rejection, hostile type safety, and runtime annotation resolution.
- [`tests/optimizer/test_walker.py`][test-optimizer-walker], [`tests/optimizer/test_extension.py`][test-optimizer-extension], [`tests/types/test_base.py`][test-types-base]: Integration tests verifying hint execution, cache invalidation, typo rejection, and schema auditing.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/hints.py --include-constants`):
- Parsed 1 target file, 261 lines.
- Inventory of symbols (9 definitions covered):
  - 1 class definition: [`OptimizerHint`][optimizer-hints].
  - 5 class methods/constructors: [`OptimizerHint.__post_init__`][optimizer-hints], [`OptimizerHint.strategy`][optimizer-hints], [`OptimizerHint.select_related`][optimizer-hints], [`OptimizerHint.prefetch_related`][optimizer-hints], [`OptimizerHint.prefetch`][optimizer-hints].
  - 3 module-level functions: [`_require_prefetch`][optimizer-hints], [`_require_strategy`][optimizer-hints], [`hint_is_skip`][optimizer-hints].
  - 1 class-level ClassVar sentinel: [`OptimizerHint.SKIP`][optimizer-hints].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   [`OptimizerHint`][optimizer-hints] is the sole canonical mechanism for optimization overrides across all GraphQL schema layers (queries, relations, Relay connections, and field resolvers). It adheres strictly to the repository law "DRF first, strawberry second: Meta classes, not stacked decorators":
   - Overrides are declared exclusively in `DjangoType.Meta.optimizer_hints` as a mapping of field names to [`OptimizerHint`][optimizer-hints] instances.
   - Validation in [`django_strawberry_framework/types/base.py`][types-base] (`_meta_optimizer_hints`, `_validate_optimizer_hints`) mirrors the shape and unknown-field error formatting of sibling Meta policies (`Meta.fields`, `Meta.exclude`, `Meta.filters`, `Meta.orders`, `Meta.forms`) using shared helper `_format_unknown_fields_error`.
   - No duplicate or alternative decorator-based hint mechanisms exist.

2. **Sync and async twins:**
   Zero duplication. [`OptimizerHint`][optimizer-hints] is a pure, deterministic, frozen value object. Both synchronous and asynchronous GraphQL execution pipelines (and AST selection walks in `optimizer/walker.py` and `optimizer/nested_planner.py`) consume the exact same `OptimizerHint` instances from `DjangoTypeDefinition.optimizer_hints` without separate async data structures or branched logic.

3. **Derived rather than repeated knowledge:**
   - [`_require_prefetch`][optimizer-hints] and [`_require_strategy`][optimizer-hints] serve as single authoritative owners for invariant validation shared between factory methods (`prefetch`, `strategy`) and direct dataclass constructors (`prefetch_obj=...`, `nested_strategy=...`).
   - [`hint_is_skip`][optimizer-hints] centralizes the skip-predicate check across [`optimizer/walker.py`][optimizer-walker], [`optimizer/nested_planner.py`][optimizer-nested-planner], and [`optimizer/extension.py`][optimizer-extension], eliminating duplicate `getattr` / `is` checks.
   - Strict mutual exclusion validation in [`OptimizerHint.__post_init__`][optimizer-hints] ensures the walker's dispatch sequence in `optimizer/walker.py::_apply_hint` is pure execution without needing duplicate collision arbitration logic.

4. **Inverse and round-trip pairs:**
   - Frozen dataclass semantics ensure full structural equality (`__eq__`) and hashability: `OptimizerHint(skip=True) == OptimizerHint.SKIP`, `OptimizerHint(force_select=True) == OptimizerHint.select_related()`, `OptimizerHint(force_prefetch=True) == OptimizerHint.prefetch_related()`.
   - Multi-database cooperation round-trips: `OptimizerHint.prefetch(Prefetch(queryset=...))` preserves custom querysets and `.using(alias)` routing through optimizer planning to execution without metadata distortion.

5. **Contracts restated in another medium:**
   The `OptimizerHint` architecture and optimization override contracts are codified across:
   - Code: [`django_strawberry_framework/optimizer/hints.py`][optimizer-hints], [`django_strawberry_framework/types/base.py`][types-base], [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker], [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner], [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension], [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch];
   - Specifications: [`docs/SPECS/spec-002-optimizer-0_0_2.md`][spec-002] (O4), [`docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`][spec-003], [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004] (B4, B6), [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023], [`docs/SPECS/spec-030-connection_field-0_0_9.md`][spec-030], [`docs/SPECS/spec-033-connection_optimizer-0_0_9.md`][spec-033], [`docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`][spec-051];
   - Test suites: [`tests/optimizer/test_hints.py`][test-optimizer-hints] (347 lines covering sentinels, factories, frozen immutability, equality, invalid state rejection, hostile type safety, and runtime type introspection), [`tests/optimizer/test_walker.py`][test-optimizer-walker], [`tests/optimizer/test_extension.py`][test-optimizer-extension], [`tests/types/test_base.py`][test-types-base];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new optimizer hint directive, e.g. `batch_size: int | None`):** Add a per-field batching size limit to optimization planning.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/hints.py`][optimizer-hints] (adding the dataclass attribute, validating it in [`OptimizerHint.__post_init__`][optimizer-hints], and adding a factory classmethod if desired).
  - *Site count:* 1.
- **Posited change 2 (Adding a new valid strategy alias or validation for nested connection strategy):** Add a new connection strategy backend (e.g. `"subquery"`).
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch] (`resolve_strategy`). Target `hints.py` delegates to [`_require_strategy`][optimizer-hints] which calls `resolve_strategy`, requiring 0 changes in `hints.py`.
  - *Site count:* 1 (0 in target).
- **Posited change 3 (Modifying the skip-check predicate behavior):** Extend `hint_is_skip` to support custom user-defined skip sentinels.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/hints.py`][optimizer-hints] (updating [`hint_is_skip`][optimizer-hints]).
  - *Site count:* 1.
- **Posited change 4 (Refining error messages for invalid `Prefetch` values):** Clarify the error message raised when non-`Prefetch` instances are passed to `prefetch()`.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/hints.py`][optimizer-hints] (updating [`_require_prefetch`][optimizer-hints]).
  - *Site count:* 1.
- **Posited change 5 (Enforcing additional mutual exclusion constraints in `OptimizerHint`):** Disallow combining `force_prefetch` with `nested_strategy`.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/hints.py`][optimizer-hints] (updating mutual exclusion checks in [`OptimizerHint.__post_init__`][optimizer-hints]).
  - *Site count:* 1.

### Rejected candidates

1. **Replacing the typed dataclass with an Enum:**
   - Disproved per [spec-004][spec-004]. An Enum cannot carry parameters such as specific `django.db.models.Prefetch` instances or strategy selections (`prefetch_obj`, `nested_strategy`).
2. **Supporting resolver-level stacked decorators (e.g. `@optimizer_hint`):**
   - Disproved per repository laws ("DRF first, strawberry second: Meta classes, not stacked decorators"). Meta-level declarations enable class-construction-time schema validation and prevent runtime decorator overhead.
3. **Deferring hint collision arbitration to query execution time in the walker:**
   - Disproved per [spec-004][spec-004]. Construction-time validation in [`OptimizerHint.__post_init__`][optimizer-hints] surfaces invalid or conflicting directives at schema build time rather than failing late or silently swallowing intent during GraphQL query execution.
4. **Making `OptimizerHint` a mutable dataclass:**
   - Disproved. Frozen immutability guarantees thread and asyncio task safety, prevents cross-request configuration pollution, and ensures stable plan caching.

## Opportunities

None — `django_strawberry_framework/optimizer/hints.py` is a clean, focused, 261-line module. It acts as the single authoritative source of truth for optimization directives, encapsulates construction-time invariants, centralizes skip dispatch, and exhibits zero duplication.

## Judgment

Zero-edit review. `optimizer/hints.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/hints.py --review docs/dry/dry-file-optimizer__hints.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independently audited `django_strawberry_framework/optimizer/hints.py` and reviewed Worker 1's analysis against the system architecture, test suite, and DRY principles.

1. **Target Definitions & Invariants Coverage:**
   - Ran `export_dry_review.py check --target django_strawberry_framework/optimizer/hints.py --review docs/dry/dry-file-optimizer__hints.md --include-constants` and confirmed 100% target coverage across all 10 symbols: [`OptimizerHint`][optimizer-hints], [`OptimizerHint.__post_init__`][optimizer-hints], [`OptimizerHint.strategy`][optimizer-hints], [`OptimizerHint.select_related`][optimizer-hints], [`OptimizerHint.prefetch_related`][optimizer-hints], [`OptimizerHint.prefetch`][optimizer-hints], [`_require_prefetch`][optimizer-hints], [`_require_strategy`][optimizer-hints], [`hint_is_skip`][optimizer-hints], and [`OptimizerHint.SKIP`][optimizer-hints].
   - Verified that `_require_prefetch` and `_require_strategy` enforce single authoritative validation of types and values before instantiation and in `__post_init__`, completely preventing silent no-op degradation when `None` or invalid shapes are supplied.
   - Re-verified that runtime type annotations on [`OptimizerHint`][optimizer-hints] (including `StrategySelection`) are resolvable without requiring runtime `TYPE_CHECKING` guards, ensuring clean introspection for IDEs and schema tools.

2. **Equivalence & Boundary Audit:**
   - Confirmed clear boundaries between `optimizer/hints.py` (value object declaration & invariant validation) and consumers (`types/base.py` for schema definition binding, `optimizer/walker.py` for AST query optimization, `optimizer/nested_planner.py` for Relay connection strategies, and `optimizer/extension.py` for schema auditing).
   - Confirmed that [`hint_is_skip`][optimizer-hints] centralizes the skip-checking predicate defensively across all consumers with fail-closed behavior, preventing unexpected crashes during schema inspection.
   - Verified that mutual exclusion rules enforced in [`OptimizerHint.__post_init__`][optimizer-hints] prevent priority arbitration ambiguities in the walker dispatch sequence.

3. **Mandatory 5-Axis Matrix Discharge:**
   - Verified all 5 axes are fully discharged with robust, factual rationales. No cross-flavor duplication, no sync/async divergence, derived invariant centralization, exact round-trip value preservation, and complete codification across specs, tests, and documentation.

4. **Single-Edit-Site Verification:**
   - Evaluated posited changes 1 through 5 and confirmed that modifications to hint semantics, skip predicates, invariants, or allowed combinations require exactly 1 site in `hints.py` (or 0 for strategy backends owned by `nested_fetch.py`).

5. **Test Suite Verification:**
   - Executed `tests/optimizer/test_hints.py` (40 unit tests), verifying 100% branch and statement coverage for `django_strawberry_framework/optimizer/hints.py`.

Worker 1's findings verified and approved. Setting `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-002]: ../SPECS/spec-002-optimizer-0_0_2.md
[spec-003]: ../SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md
[spec-004]: ../SPECS/spec-004-optimizer_beyond-0_0_3.md
[spec-023]: ../SPECS/spec-023-multi_db-0_0_7.md
[spec-030]: ../SPECS/spec-030-connection_field-0_0_9.md
[spec-033]: ../SPECS/spec-033-connection_optimizer-0_0_9.md
[spec-051]: ../SPECS/spec-051-boundary_dry_squeeze-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-hints]: ../../django_strawberry_framework/optimizer/hints.py
[optimizer-nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[optimizer-nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[package-init]: ../../django_strawberry_framework/__init__.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-definition]: ../../django_strawberry_framework/types/definition.py

<!-- tests/ -->
[test-optimizer-extension]: ../../tests/optimizer/test_extension.py
[test-optimizer-hints]: ../../tests/optimizer/test_hints.py
[test-optimizer-walker]: ../../tests/optimizer/test_walker.py
[test-types-base]: ../../tests/types/test_base.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
