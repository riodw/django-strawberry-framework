# Review: `django_strawberry_framework/utils/strings.py`

Status: verified

## Understanding

`django_strawberry_framework/utils/strings.py` provides pure, cycle-free case conversion, name mapping, and ORM lookup flattening across the GraphQL/Django boundary:

1. **Subclass Normalization & Type Safety (`_plain_text`)**:
   - Accepts any string or string subclass and normalizes it to a primitive `str` via `str.__str__(value)` descriptor extraction, shielding downstream string methods and cache hashing from hostile or untrusted subclass method overrides.
   - Rejects non-string inputs with typed `ConfigurationError(f"String helper input must be a string; got {_safe_type_name(value)}.")`.

2. **Reversible Case Mapping (`snake_case`, `graphql_camel_name`)**:
   - `snake_case`: Memoized (`@functools.lru_cache(maxsize=2048)`) char-by-char converter reversing camel/Pascal GraphQL field names to Django `snake_case` attributes. Preserves acronym runs (e.g. `HTTPServer` -> `http_server`), handles digit token boundaries (e.g. `field2Value` -> `field2_value`), and recognizes the adjacent single-letter escape sequence `__x` (e.g. `aA__xA` -> `a_a_a`).
   - `graphql_camel_name`: Lowercases head and camelCases remainder, injecting `__x` between adjacent uppercase tokens to maintain injectivity with `snake_case`.

3. **Schema Type Construction (`pascal_case`, `pascal_case_or_raise`)**:
   - `pascal_case`: Constructs `PascalCase` type and enum stems from Django `snake_case` attributes while preserving digit-leading underscore boundaries (`field_2` -> `Field_2` vs `field2` -> `Field2`) to prevent operator-bag/range-type schema collisions.
   - `pascal_case_or_raise`: Single-sites the no-word-token emptiness guard (`""`, `"_"`, `"__"`) shared by `ClassBasedTypeNameMixin` and `filters/inputs.py`, accepting a caller-specific error factory `make_error: Callable[[str], Exception]`.

4. **Lookup Path Flattening (`flatten_lookup_path`)**:
   - Central owner of the `LOOKUP_SEP` (`"__"`) to single underscore (`"_"`) replacement loop, ensuring generated GraphQL filter/order attribute names, permission method mangles, and aggregate aliases never leak unescaped Django lookup separators.

## Verification

1. **Caller Tracing & Behavioral Invariance**:
   - Traced callers across `filters/inputs.py`, `forms/inputs.py`, `mutations/inputs.py`, `orders/inputs.py`, `orders/sets.py`, `rest_framework/inputs.py`, `rest_framework/serializer_converter.py`, `sets_mixins.py`, `types/base.py`, `types/converters.py`, `types/finalizer.py`, and `optimizer/walker.py`.
   - Verified that all callers rely on `_plain_text` protection, `snake_case` LRU memoization, and `pascal_case_or_raise` validation.
2. **Scratch Probing**:
   - Executed scratch test `docs/review/temp-tests/strings/test_scratch.py` probing numeric segmentation, leading underscore combinations, and hostile string subclasses.
   - Executed scratch test `docs/review/temp-tests/strings/test_scratch_underscores.py` validating underscore-escape invertibility (`_legacy_id`, `_Foo`, `__Foo`).
   - Executed scratch test `docs/review/temp-tests/strings/test_scratch_wraps.py` verifying `functools.wraps` assignment parameters for `snake_case`.
3. **Existing and Expanded Test Suite**:
   - Evaluated `tests/utils/test_strings.py` (41 test cases) covering acronym runs, digit segments, invertibility round-trips, empty inputs, hostile string subclasses, LRU cache introspection, and typed configuration errors.
   - Ran `uv run pytest tests/utils/test_strings.py --no-cov` (41 passed in 1.54s).

## Improvements

### High

None.

### Medium

None.

### Low

1. **`snake_case` wrapper masqueraded as `_snake_case_cached` and module lacked explicit `__all__`**
   - **Observation:** `@functools.wraps(_snake_case_cached)` overwrote `snake_case.__name__` and `snake_case.__qualname__` with `_snake_case_cached`, causing introspection, test runners (e.g. `pytest` parameterized test IDs), and debugging tools to report the private cached function name instead of the public `snake_case` symbol. Additionally, the module lacked an explicit `__all__` declaration.
   - **Evidence:** `pytest.mark.parametrize` over string helpers emitted `test_string_helpers_reject_non_string_inputs[_snake_case_cached]`; `snake_case.__name__` evaluated to `"_snake_case_cached"`.
   - **Impact:** Misleading function introspection and debugger representations for a core public utility function.
   - **Recommendation:** Provide explicit `assigned=("__module__", "__doc__", "__annotations__")` to `functools.wraps` so `snake_case` retains its public `__name__` and `__qualname__` while still wrapping `_snake_case_cached`, and export the public symbols via `__all__`.
   - **Proof:** `assert snake_case.__name__ == "snake_case"` and `assert snake_case.__qualname__ == "snake_case"` pass in `tests/utils/test_strings.py::test_snake_case_preserves_lru_cache_controls`.

## Summary

`django_strawberry_framework/utils/strings.py` is a well-engineered, thoroughly tested string transformation module with strict injective naming guarantees and defense-in-depth subclass normalization. The wrapper metadata was adjusted to preserve public symbol identity, and an explicit `__all__` tuple was defined.

## Implementation (Worker 1)

- **Changed files:**
  - `django_strawberry_framework/utils/strings.py`: Added explicit `__all__` export tuple and passed `assigned=("__module__", "__doc__", "__annotations__")` to `@functools.wraps` on `snake_case`.
  - `tests/utils/test_strings.py`: Added assertions to `test_snake_case_preserves_lru_cache_controls` verifying `snake_case.__name__ == "snake_case"` and `snake_case.__qualname__ == "snake_case"`.
- **Permanent tests and pinned behavior:**
  - `tests/utils/test_strings.py::test_snake_case_preserves_lru_cache_controls`: Pins that `snake_case.__name__` and `snake_case.__qualname__` are preserved as `"snake_case"` across `functools.wraps` while keeping the LRU cache control interface and `__wrapped__` target.
- **Scratch or focused verification:**
  - `uv run pytest tests/utils/test_strings.py --no-cov` (41 passed in 1.54s).
- **Formatter and linter results:**
  - `uv run ruff format .` (432 files left unchanged).
  - `uv run ruff check --fix .` (All checks passed).
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — internal metadata refinement and `__all__` declaration with zero breaking behavioral changes.

## Independent verification (Worker 2)

1. **Behavioral and contract verification**:
   - Re-traced `_plain_text` descriptor extraction `str.__str__(value)`, validating that arbitrary hostile `str` subclass overrides (custom `__str__`, `__hash__`, `split`, `replace`, `isupper`, `islower`, `isdigit`, `lower`, `upper`, `strip`) are completely neutralized before string processing and cache hashing.
   - Verified that non-string inputs (`None`, `int`, `float`, `list`, `dict`, `set`, `object`) are rejected consistently across all public helpers with `ConfigurationError`.
   - Re-traced `snake_case` char-by-char conversion: acronym runs (`HTTPServer` -> `http_server`, `XMLHTTPRequest` -> `xmlhttp_request`), digit boundaries (`field2Value` -> `field2_value`, `field2` -> `field2`), title-case boundaries (`OAuth2Token` -> `o_auth2_token`), leading/trailing underscores (`_legacyId` -> `_legacy_id`, `trailing_` -> `trailing_`), and the `__x` escape sequence (`aA__xA` -> `a_a_a`).
   - Re-traced `graphql_camel_name` injectivity and roundtripping with `snake_case`, confirming bidirectional invertibility across multi-letter, single-letter, digit, leading/trailing, and double underscore sequences.
   - Re-traced `pascal_case` digit-leading underscore preservation (`field_2` -> `Field_2` vs `field2` -> `Field2`, `field_20_value` -> `Field_20Value`) ensuring schema type and enum name collisions are prevented.
   - Re-traced `pascal_case_or_raise` emptiness validation across empty and underscore-only inputs (`""`, `"_"`, `"__"`), confirming delegation to the provided `make_error` factory.
   - Re-traced `flatten_lookup_path` while-loop replacement of `"__"` -> `"_"` preventing `LOOKUP_SEP` leakage into GraphQL input attribute names and aggregate aliases.
2. **Diff and test inspection**:
   - Confirmed `git diff 12779c99 -- django_strawberry_framework/utils/strings.py` contains only the explicit `__all__` tuple and `assigned` parameter on `functools.wraps`.
   - Confirmed `tests/utils/test_strings.py` pins `snake_case.__name__ == "snake_case"` and `snake_case.__qualname__ == "snake_case"` while preserving the LRU cache control surface (`cache_clear`, `cache_info`, `cache_parameters`, `__wrapped__`).
3. **Execution**:
   - Created comprehensive scratch test `docs/review/temp-tests/strings/test_worker2_verification.py` testing hostile subclass neutralization, non-string input rejection, cache hits/misses, acronym runs, injective roundtripping, digit segment boundaries, error factory raising, and lookup flattening.
   - Ran `uv run pytest docs/review/temp-tests/strings/test_worker2_verification.py tests/utils/test_strings.py --no-cov` (77 passed in 1.61s).
4. **Outcome**:
   - All string conversion contracts and naming invariants verified. No defects or regressions found.
