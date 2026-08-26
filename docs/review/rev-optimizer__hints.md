# Review: `django_strawberry_framework/optimizer/hints.py`

Status: verified

## Understanding

`django_strawberry_framework/optimizer/hints.py` provides the public, typed configuration abstraction (`OptimizerHint`) and helper predicate (`hint_is_skip`) for declaring per-relation query optimization overrides in `DjangoType.Meta.optimizer_hints`:

1. **Core Data Structure & Immutability (`OptimizerHint`)**:
   - Implemented as a frozen dataclass (`@dataclass(frozen=True)`) with fields:
     - `force_select: bool = False`: Forces `select_related` planning regardless of field cardinality.
     - `force_prefetch: bool = False`: Forces `prefetch_related` planning regardless of field cardinality.
     - `prefetch_obj: Prefetch | None = None`: Carries a custom `django.db.models.Prefetch` instance for leaf prefetching.
     - `skip: bool = False`: Instructs the optimizer to exclude the relation from automated planning.
     - `nested_strategy: StrategySelection | None = None`: Overrides the nested connection fetch strategy (e.g., `"windowed"`, `"lateral"`, `"auto"`, or a `NestedConnectionStrategy` instance).
   - Re-exported from top-level `django_strawberry_framework/__init__.py` for convenient consumer imports.

2. **Sentinel & Factory Classmethods**:
   - `OptimizerHint.SKIP`: Singleton-like sentinel instance declared via `ClassVar` and initialized as `OptimizerHint(skip=True)`.
   - `OptimizerHint.select_related()`: Factory returning `OptimizerHint(force_select=True)`.
   - `OptimizerHint.prefetch_related()`: Factory returning `OptimizerHint(force_prefetch=True)`.
   - `OptimizerHint.prefetch(obj: Prefetch)`: Factory enforcing that `obj` is a `Prefetch` instance before returning `OptimizerHint(prefetch_obj=obj)`.
   - `OptimizerHint.strategy(name: StrategySelection)`: Factory resolving and validating the strategy name or instance before returning `OptimizerHint(nested_strategy=name)`.

3. **Construction-Time Validation (`__post_init__`, `_require_prefetch`, `_require_strategy`)**:
   - Enforces fail-fast validation at schema build time rather than query execution time:
     - Type checks boolean flags (`force_select`, `force_prefetch`, `skip`) to prevent truthy/falsy non-booleans from bypassing logic.
     - Prohibits conflicting directives: `skip` cannot be combined with `force_select`, `force_prefetch`, `prefetch_obj`, or `nested_strategy`.
     - Prohibits simultaneous `force_select` and `force_prefetch`.
     - Prohibits combining `prefetch_obj` with `force_select`, `force_prefetch`, or `nested_strategy`.
     - Disallows combining `nested_strategy` with `skip`, `force_select`, or `prefetch_obj` (allows `force_prefetch` as redundant but harmless).
     - Validates `prefetch_obj` via `_require_prefetch` and `nested_strategy` via `_require_strategy`/`resolve_strategy` (safely handling hostile types without unhandled crashes).

4. **Skip Predicate (`hint_is_skip`)**:
   - Provides a centralized, defensively guarded predicate used by `optimizer/walker.py`, `optimizer/nested_planner.py`, and `optimizer/extension.py` (schema audit).
   - Fast paths for `None` and identity with `OptimizerHint.SKIP`.
   - Safely wraps attribute access in `try...except BaseException` to maintain a fail-closed, "never raises" contract during schema audits.

5. **Runtime Type Hints & Global Namespace Safety**:
   - Imports `StrategySelection` and `resolve_strategy` at module runtime rather than under `TYPE_CHECKING` so `typing.get_type_hints(OptimizerHint)` resolves cleanly in consumer introspection tools, documentation generators, and IDE bridges without `NameError`.

## Verification

1. **Existing Test Suite**: Executed and verified `tests/optimizer/test_hints.py` (40 passed in 2.01s) covering:
   - `TestSkipSentinel`: Sentinel type, flag state, cross-access identity stability, and equality with fresh `OptimizerHint(skip=True)`.
   - `TestSelectRelatedFactory` / `TestPrefetchRelatedFactory` / `TestPrefetchFactory`: Factory flag configurations, isolation of non-targeted flags, and `None` rejection.
   - `TestStrategyFactory`: Storage of strategy names, strategy resolution validation, rejection of invalid names, rejection of conflicting flags, hostile type safety, and runtime typing resolution.
   - `TestFrozenImmutability`: `FrozenInstanceError` / `AttributeError` on attempted attribute mutation.
   - `TestEquality`: Structural equality and inequality semantics across factories and distinct `Prefetch` objects.
   - `TestInvalidStatesRejected`: Rejection of non-boolean flags, conflicting flag combinations, non-`Prefetch` objects, and hostile type names.
   - `TestSkipPredicate`: Fail-closed evaluation of hostile object shapes and invalid inputs.
2. **Scratch Test Suite**: Created and ran `docs/review/temp-tests/optimizer/hints/test_scratch.py` (6 passed in 1.60s) verifying:
   - Direct construction vs factory constructor equivalence.
   - Support for custom `NestedConnectionStrategy` instances in `strategy()` and `nested_strategy=`.
   - Comprehensive matrix of invalid flag combinations and non-boolean arguments raising `ConfigurationError`.
   - Type invariant helper functions `_require_prefetch` and `_require_strategy`.
   - Fail-closed behavior of `hint_is_skip` across `None`, valid hints, scalar values, and hostile throwing descriptors.
   - Full evaluation of `typing.get_type_hints` for `OptimizerHint` and `hint_is_skip`.
3. **Scoped Diff Verification**: Confirmed zero diff against cycle baseline `12779c99` (`git diff 12779c99 -- django_strawberry_framework/optimizer/hints.py`).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/optimizer/hints.py` is a clean, robust, and well-isolated configuration module. It provides a type-safe, immutable interface for declaring relation optimization hints, ensures early construction-time validation of invalid or conflicting states, handles runtime introspection cleanly, and provides fail-closed predicate helpers for downstream optimizer components. No defects or design issues were found.

## Implementation (Worker 1)

None — zero-edit cycle

- **Changed files**: None.
- **Permanent tests**: Existing test coverage in `tests/optimizer/test_hints.py` (40 tests) comprehensively covers sentinel identity, factory classmethods, frozen immutability, invalid state rejection, hostile type safety, and runtime typing introspection.
- **Scratch verification**: `docs/review/temp-tests/optimizer/hints/test_scratch.py` passed (6 tests, 0 failures) probing direct construction, factory semantics, invalid flag combinations, strategy instances, `hint_is_skip` fail-closed safety, and runtime type hints.
- **Formatter and linter**: Zero-edit cycle (no code modifications made).
- **Evidence for rejected findings**: No findings raised or rejected; all investigated code paths behave according to design and specifications.
- **Changelog**: Does not merit a changelog entry (zero-edit cycle).

## Independent verification (Worker 2)

Worker 2 independently verified `django_strawberry_framework/optimizer/hints.py` across all functional requirements and contracts:

1. **Production Zero-Edit Confirmation**: Verified `git diff 12779c99 -- django_strawberry_framework/optimizer/hints.py` is empty against cycle baseline `12779c99`.
2. **Behavioral & Contractual Re-Tracing**:
   - `OptimizerHint` data structure & immutability: Verified frozen dataclass invariants, structural equality, and mutation prohibition (`FrozenInstanceError` / `AttributeError`).
   - Factories & Sentinels: Verified `OptimizerHint.SKIP`, `.select_related()`, `.prefetch_related()`, `.prefetch(obj)`, and `.strategy(name)` factories initialize the expected flags and validate parameters upfront.
   - Validation & Conflict Prevention: Confirmed construction-time strictness in `__post_init__`, `_require_prefetch`, and `_require_strategy`, preventing conflicting flag combinations (`skip` with others, `force_select` with `force_prefetch`, `prefetch_obj` with other flags, `nested_strategy` with `skip`/`force_select`/`prefetch_obj`) and rejecting non-bools/hostile types.
   - Fail-Closed Predicate (`hint_is_skip`): Verified fail-closed evaluation across `None`, valid `OptimizerHint` instances, non-hint values, and hostile property/boolean descriptors.
   - Runtime Introspection: Verified `StrategySelection` and `resolve_strategy` module imports allow `typing.get_type_hints(OptimizerHint)` and `typing.get_type_hints(OptimizerHint.strategy)` to resolve without `NameError`.
3. **Focused & Scratch Test Execution**: Executed `tests/optimizer/test_hints.py` and `docs/review/temp-tests/optimizer/hints/test_scratch.py` (46 passed in 1.69s with `--no-cov`).
4. **Outcome**: All behaviors, contracts, and safety invariants are fully verified. No defects or regressions found. Status marked `verified`.

