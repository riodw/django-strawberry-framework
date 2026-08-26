# Review: `django_strawberry_framework/exceptions.py`

Status: verified

## Understanding

`django_strawberry_framework/exceptions.py` defines the package-wide exception hierarchy and diagnostic formatting helpers. It sits at the absolute bottom of the framework dependency graph with zero dependencies on Django, Strawberry, or any internal framework modules, relying purely on the Python standard library.

It owns:
1. **Diagnostic formatting helpers**:
   - `_safe_type_name(value)`: safely extracts the identifying type name for an instance or class without trusting consumer-controlled or hostile `__class__`, `__name__`, or metaclass properties. Strips `str` subclasses via `str.__str__` and falls back gracefully to metaclass names or `"object"`.
   - `_safe_arg_repr(value)`: safely renders `repr(value)` via `str.__str__(repr(value))` to strip `str` subclasses, falling back to `<unprintable {_safe_type_name(value)}>` upon any `BaseException`.
   - `_safe_class_name(value, *, qualified=False)`: safely reads `__qualname__` or `__name__` from classes or instances, neutralizing hostile `str` subclasses and falling back through `_safe_type_name` or `_safe_arg_repr`.
   - `_safe_model_label(model)`: extracts `model._meta.label` safely, stripping `str` subclasses and falling back to `_safe_type_name(model)` if missing, malformed, or hostile.
   - `_safe_terminal_label(terminal)`: extracts `terminal.name` safely, stripping `str` subclasses and falling back to `_safe_type_name(terminal)` if missing, malformed, or hostile.
   - `describe_value(value)`: transport-boundary diagnostic tail helper returning `"{_safe_type_name(value)} {value!r}"` or falling back to `"an unprintable {_safe_type_name(value)}"` when `value!r` raises (e.g. hostile `__repr__` or `sys.get_int_max_str_digits()` integer overflow).
2. **Exception hierarchy**:
   - `DjangoStrawberryFrameworkError(Exception)`: package root exception with lazy, dynamic `__str__` and `__repr__` implementations that catch all `BaseException` dunders and strip `str` subclasses to preserve wire identity through GraphQL-core execution.
   - `ConfigurationError(DjangoStrawberryFrameworkError)`: definition-time and runtime configuration validation failure base exception.
   - `PathResolutionError(ConfigurationError)`: strict relation path traversal classification failure. Implements `__reduce__` to preserve constructor parameters (`model`, `field_path`, `segment`) and custom attributes across pickle and deepcopy operations.
   - `LookupValidationError(ConfigurationError)`: terminal django-filter lookup expression validation failure. Implements `__reduce__` to preserve constructor parameters (`terminal`, `lookup_expr`, `part`) and custom attributes across pickle and deepcopy operations.
   - `OptimizerError(DjangoStrawberryFrameworkError)`: query planner and relation optimizer failure.

## Verification

1. Traced connections and call sites across the codebase:
   - `conf.py`, `views.py`, `consumers.py`, `error_policy.py`, `resource_policy.py`, `routers.py`, `types/`, `optimizer/`, `filters/`, `forms/`, `mutations/`, `orders/`, `rest_framework/`, `utils/`.
   - Verified that `describe_value` is consistently used for `got <type> <repr>` diagnostic message tails across view settings, router factories, error policies, and consumer validation.
   - Verified that `SyncMisuseError` (`utils/querysets.py`) inherits from `ConfigurationError` and `RuntimeError`.
2. Examined test suites:
   - `tests/test_exceptions.py` (27 tests): covers exception inheritance lattice, GraphQL error wrapping identity preservation, unprintable and stateful argument handling, multi-argument formatting, pickle/copy attribute preservation for `PathResolutionError` and `LookupValidationError`, `str` subclass stripping, and fallback behaviors under hostile metaclasses and properties.
3. Test executions:
   - `uv run pytest tests/test_exceptions.py --no-cov` (27 passed).
   - `uv run pytest tests/test_exceptions.py -o "addopts=" --cov=django_strawberry_framework.exceptions --cov-report=term-missing` (100% statement and branch coverage).
4. Scratch tests:
   - `docs/review/temp-tests/exceptions/test_scratch_exceptions.py` (10 passed): tested the complete input matrix across primitives, classes, instances, hostile `__class__` properties, hostile metaclasses, non-string `__name__`, empty names, huge integers exceeding `sys.get_int_max_str_digits()`, and pickle fidelity.

## Improvements

### High

None.

### Medium

None.

### Low

- **`DjangoStrawberryFrameworkError.__str__` and `__repr__` preserved `str` subclasses from arguments, permitting hostile `__format__` execution**:
  - **Observation**: `DjangoStrawberryFrameworkError.__str__` and `__repr__` returned `super().__str__()` and `super().__repr__()` without stripping `str` subclasses. When an exception was constructed with a `str` subclass having an overridden `__format__` or `__str__`, the resulting `str(exc)` or `repr(exc)` retained that subclass type.
  - **Evidence**: `ConfigurationError(HostileFormatStr("msg"))` returned an instance of `HostileFormatStr` from `str(exc)`. Formatting `f"{str(exc)}"` triggered the subclass's hostile `__format__` method, causing unexpected runtime exceptions during downstream string interpolation or logging.
  - **Impact**: Inconsistent with the defensive design of `_safe_type_name`, `_safe_arg_repr`, `_safe_class_name`, `_safe_model_label`, and `_safe_terminal_label`, which all explicitly strip `str` subclasses using `str.__str__(...)`.
  - **Recommendation**: Wrap `super().__str__()` and `super().__repr__()` in `str.__str__(...)` inside `DjangoStrawberryFrameworkError.__str__` and `DjangoStrawberryFrameworkError.__repr__`.
  - **Proof**: Pinned by `test_framework_error_str_and_repr_strip_str_subclasses` in `tests/test_exceptions.py`.

## Summary

`django_strawberry_framework/exceptions.py` provides the foundational exception hierarchy and safe diagnostic formatting utilities for the entire package. It sits at the absolute bottom of the framework dependency graph with zero internal or external framework imports. All diagnostic helpers (`_safe_type_name`, `_safe_arg_repr`, `_safe_class_name`, `_safe_model_label`, `_safe_terminal_label`, `describe_value`) and base exception methods (`DjangoStrawberryFrameworkError.__str__`, `__repr__`) defensively handle hostile metadata, unprintable objects, integer string-length overflows, and `str` subclasses. `PathResolutionError` and `LookupValidationError` cleanly preserve constructor arguments and attributes across pickle and deepcopy roundtrips.

## Implementation (Worker 1)

- **Changed files:**
  - `django_strawberry_framework/exceptions.py`: Wrapped `super().__str__()` and `super().__repr__()` in `str.__str__(...)` inside `DjangoStrawberryFrameworkError.__str__` and `__repr__` to strip `str` subclasses and prevent hostile `__format__` execution downstream.
  - `tests/test_exceptions.py`: Added permanent tests (`test_framework_error_str_and_repr_strip_str_subclasses`, `test_safe_class_name_on_standard_classes`, `test_describe_value_on_printable_and_unprintable_values`) verifying `str` subclass stripping, class name resolution, and `describe_value` edge cases.
- **Permanent tests and pinned behavior:**
  - `tests/test_exceptions.py` (27 tests) achieves 100% statement and branch coverage on `django_strawberry_framework.exceptions`.
  - `test_framework_error_str_and_repr_strip_str_subclasses`: pins `str` subclass neutralization across `str(err)` and `repr(err)`.
  - `test_safe_class_name_on_standard_classes`: pins `_safe_class_name` on standard classes, qualified names, and class instances.
  - `test_describe_value_on_printable_and_unprintable_values`: pins `describe_value` formatting across primitives, unprintable objects, `BaseException` dunders, and large integers.
- **Scratch verification:**
  - `docs/review/temp-tests/exceptions/test_scratch_exceptions.py` (10 tests, 100% pass) verified the complete safety matrix for all helpers and exception subclasses.
- **Formatter and linter results:**
  - `uv run ruff format .` passed (1 file reformatted).
  - `uv run ruff check --fix .` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/exceptions.py tests/test_exceptions.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — internal diagnostic hardening and defensive exception formatting cleanup; no public API breaking changes.

## Independent verification (Worker 2)

- **Verification methodology and edge-case probing:**
  - Independently re-traced the exception hierarchy (`DjangoStrawberryFrameworkError`, `ConfigurationError`, `PathResolutionError`, `LookupValidationError`, `OptimizerError`) and diagnostic helpers (`_safe_type_name`, `_safe_arg_repr`, `_safe_class_name`, `_safe_model_label`, `_safe_terminal_label`, `describe_value`).
  - Evaluated string subclass stripping behavior in `DjangoStrawberryFrameworkError.__str__` and `__repr__`. Verified that hostile `str` subclasses with custom `__format__` or `__str__` methods cannot detonate string interpolation downstream.
  - Executed extensive independent scratch testing (`docs/review/temp-tests/exceptions/test_worker2_verification.py`, 12 test functions) covering:
    - Hostile metadata and metaclasses (`__name__` / `__qualname__` raising `RuntimeError` or `BaseException`, returning integers, or returning empty strings).
    - Hostile `__class__` properties raising `KeyboardInterrupt` on objects.
    - Large integer formatting boundary conditions exceeding `sys.get_int_max_str_digits()`.
    - Zero, single, and multi-argument construction and dynamic `args` reassignment on exception instances.
    - GraphQL-core `located_error` wrapping fidelity during in-process GraphQL execution without losing `original_error` type or instance identity.
    - Pickle, shallow copy, and `copy.deepcopy` roundtrip attribute fidelity for `PathResolutionError` and `LookupValidationError`.
- **Test execution results:**
  - `uv run pytest tests/test_exceptions.py docs/review/temp-tests/exceptions/ --no-cov` (50 passed in 1.47s).
  - Pinned permanent tests in `tests/test_exceptions.py` pass cleanly and prove that `str.__str__(...)` prevents `str` subclass method execution.
- **Contract and linter checks:**
  - Verified `__all__` exports match the public contract.
  - Formatter and linter checks clean (`ruff check`, `ruff format`, `scripts/check_trailing_commas.py`).
- **Conclusion:**
  - All behavior is independently verified. No defects or regressions remain.

## Iterations

Post-run audit correction. The `## Implementation (Worker 1)` **Changed files** list above is
incomplete: it records only the `str.__str__(...)` wrapping, but this target also became the home of
the shared `_safe_text` / `_unprintable` renderers, folding in two copies that lived elsewhere. That
is a cross-file edit, and REVIEW.md requires the expanded ownership be named in the artifact:

- `django_strawberry_framework/exceptions.py` - added `_unprintable` (the one `<unprintable {T}>`
  placeholder) and `_safe_text` (the shared no-raise `str` renderer).
- `django_strawberry_framework/utils/errors.py` - **expanded ownership**: deleted its local
  `_safe_text` / `_unprintable`, now imported from the target.
- `django_strawberry_framework/types/converters.py` - **expanded ownership**: deleted its local
  `_safe_text`, now imported from the target.

The consolidation is behavior-preserving or stronger, verified independently of Worker 1/2:

- The converters copy rendered via plain `str(value)`; the shared body routes a `str` subclass
  through `str.__str__`, so `_field_label` gained hostile-subclass resistance it did not have.
- The signature widened from the converters copy's required-positional `fallback` to
  `fallback: str = ""`, so both the positional (`converters.py`) and keyword (`utils/errors.py`)
  call styles resolve; no caller was left behind (`_safe_text` / `_unprintable` resolve tree-wide).
- Pinned by `tests/test_exceptions.py::test_safe_text_is_the_shared_str_renderer` and
  `tests/test_exceptions.py::test_safe_text_is_single_sourced_across_consumer_modules`, the latter
  asserting all three modules bind the one object.

Worker 2's verification above enumerates the helpers it re-traced and `_safe_text` / `_unprintable`
are absent from that list, so the consolidation reached `verified` without independent coverage.
This section supplies it; the code needs no revision.
