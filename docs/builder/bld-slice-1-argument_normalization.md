# Build: Slice 1 — argument normalization and typed runtime rejection

Spec reference: [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050] (lines 67-82)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Refreshed the shallow AST inventory across the entire package (`django_strawberry_framework/`) into `docs/shadow/helper-inventory.md` before planning. Grepped the inventory for argument normalization, validation, bounding, and error-handling shapes: `parse`, `decode`, `validate`, `reject`, `limit`, `bound`, `offset`, `order_by`, and `signature`. Relevant existing candidates identified:
  - `django_strawberry_framework/exceptions.py::describe_value` (lines 160-207)
  - `django_strawberry_framework/resource_policy.py::ResourceLimitExceeded` (lines 99-150)
  - `django_strawberry_framework/resource_policy.py::_raw_list_bound` (lines 512-522)
  - `django_strawberry_framework/resource_policy.py::effective_bound` (lines 650-665)
  - `django_strawberry_framework/resource_policy.py::bounded_rows` / `bounded_rows_async` (lines 524-638)
  - `django_strawberry_framework/utils/typing.py::schema_config_from_info` (lines 63-80)

- **Existing patterns reused.**
  - [`django_strawberry_framework/exceptions.py::describe_value`][exceptions]: reused for rendering the safe string representation of non-integer values in `ListArgumentError` when a direct Python call bypasses GraphQL scalar coercion.
  - [`django_strawberry_framework/resource_policy.py::ResourceLimitExceeded`][resource-policy]: reused as the architectural precedent for a dual-base `class ListArgumentError(GraphQLError, DjangoStrawberryFrameworkError)` with an explicit `__reduce__` tuple `(cls, args, self.__dict__)` ensuring clean pickle round-tripping without relying on `GraphQLError` slots. (Note: `ListArgumentError` carries no `# noqa: N818` suppression because its name ends in `Error`; adding an unused suppression would fail under `RUF100`).
  - [`django_strawberry_framework/resource_policy.py::_raw_list_bound`][resource-policy]: retained as the sole deadline check and effective returned-row ceiling lookup for raw lists, preserving cooperative execution deadline checks.
  - [`django_strawberry_framework/resource_policy.py::effective_bound`][resource-policy]: reused for limit ceiling calculation without reimplementing `min(policy, field)`.
  - [`django_strawberry_framework/resource_policy.py::bounded_rows`][resource-policy] and [`bounded_rows_async`][resource-policy]: extended with `offset` and `requested_limit` keyword parameters, preserving backward-compatible 3-positional argument calls (`result, info, declared=None`).
  - [`django_strawberry_framework/utils/typing.py::schema_config_from_info`][typing-utils]: reused to retrieve `StrawberryConfig` and access `config.name_converter.from_argument(...)`.

- **New helpers justified.**
  - `_resolve_argument_wire_name(info: Any, parameter_name: str) -> str`: package-private helper in `django_strawberry_framework/list_field.py`. Single responsibility: look up the active GraphQL wire name for an internal parameter name (`"offset"`, `"limit"`, or `"order_by"`) via `info.get_argument_definition(parameter_name)` and `schema_config_from_info(info).name_converter.from_argument(arg_def)`, falling back to standard default names `{"offset": "offset", "limit": "limit", "order_by": "orderBy"}[parameter_name]` for direct calls without a schema/info. Called only inside `ListArgumentError.__init__` on failure paths, guaranteeing zero runtime name-conversion overhead on valid requests.
  - `_ListArguments`: slotted, immutable record in `django_strawberry_framework/list_field.py`. Single responsibility: encapsulate normalized coordinates and state flags (`offset: int | None`, `limit: int | None`, `effective_ceiling: int`, `order_by: Any`, `order_by_supplied: bool`, `any_argument_supplied: bool`).
  - `_normalize_list_arguments(...)`: package-private function in `django_strawberry_framework/list_field.py`. Single responsibility: validate raw resolver arguments, check bool/type invariants, enforce negative and ceiling bounds with deterministic offset-before-limit precedence, and produce a `_ListArguments` instance.
  - `_synthesized_list_signature(target_type: type)`: package-private helper in `django_strawberry_framework/list_field.py`. Single responsibility: build `inspect.Signature` and annotation dictionary with reserved positional-or-keyword `root = None`, keyword-only `info: Info`, keyword-only `offset: int | None = None`, keyword-only `limit: int | None = None`, and conditional keyword-only `order_by: list[order_input_type(orderset_class)] | None = None` when `orderset_class` is present on `target_type`, without installing a return annotation (`inspect.Signature.empty`).
  - `_close_async_iterator(iterator: Any, *, primary_error: BaseException | None = None)`: package-private async helper in `django_strawberry_framework/resource_policy.py`. Single responsibility: safely invoke `iterator.aclose()`, attaching any cleanup failure to `primary_error.__notes__` when a primary exception exists, or raising the cleanup failure directly when iteration succeeded cleanly.

- **Duplication risk avoided.**
  - *No second `min(policy, field)` cap helper:* avoid reimplementing cap arithmetic in `list_field.py`; rely on `effective_bound` from `resource_policy.py`.
  - *No circular import with `connection.py`:* avoid importing `connection._synthesized_signature`. Because `connection.py` imports `_validate_relay_djangotype_target` from `list_field.py`, importing across would create a module import cycle.
  - *No second pagination/slicing seam:* avoid adding list-field-specific window slicing in `list_field.py`. Extend the existing `bounded_rows` and `bounded_rows_async` in `resource_policy.py`.
  - *No eager wire name resolution:* avoid calling `NameConverter.from_argument` on valid requests. Wire name resolution is strictly error-lazy.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against current source before editing.

1. **Define `ListArgumentError` in [`django_strawberry_framework/list_field.py`][list-field] (lines 175-237):**
   - Declare `class ListArgumentError(GraphQLError, DjangoStrawberryFrameworkError):`.
   - Do NOT add `# noqa: N818`.
   - Implement `__init__(self, field: str, argument: str, reason: str, value: Any = None, ceiling: int | None = None)`.
   - Store instance attributes `field`, `argument`, `reason`, `value`, `ceiling`.
   - Assemble human-readable GraphQL error message describing the field, argument, rejected value (using `describe_value(value)` for non-integers), and accepted contract.
   - Assemble `extensions`: `{"code": "LIST_ARGUMENT_INVALID", "argument": argument, "reason": reason}`, conditionally including `"value": value` when present and `"ceiling": ceiling` for `"over_ceiling"`.
   - Implement `__reduce__(self) -> tuple[object, ...]`: return `(self.__class__, (self.field, self.argument, self.reason, self.value, self.ceiling), self.__dict__)`.

2. **Implement `_resolve_argument_wire_name` in [`django_strawberry_framework/list_field.py`][list-field]:**
   - Accepts `(info: Any, parameter_name: str) -> str`.
   - Checks if `info` has `get_argument_definition`. If available, retrieves `arg_def = info.get_argument_definition(parameter_name)`.
   - If `arg_def` is found, obtains `config = schema_config_from_info(info)` and invokes `config.name_converter.from_argument(arg_def)`.
   - Falls back to `{"offset": "offset", "limit": "limit", "order_by": "orderBy"}.get(parameter_name, parameter_name)`.

3. **Define `_ListArguments` and `_normalize_list_arguments` in [`django_strawberry_framework/list_field.py`][list-field]:**
   - Define slotted `_ListArguments` record with fields: `offset: int | None`, `limit: int | None`, `effective_ceiling: int`, `order_by: Any`, `order_by_supplied: bool`, `any_argument_supplied: bool`.
   - In `_normalize_list_arguments(field_name: str, info: Info, max_rows: int | None, trusted_max_rows: bool, offset: Any, limit: Any, order_by: Any = strawberry.UNSET)`:
     - Normalization of omission: treat `strawberry.UNSET` and `None` as omitted (`None`). `0` and `[]` are treated as supplied.
     - Determine `any_argument_supplied = (offset is not None or limit is not None or (order_by is not strawberry.UNSET and order_by is not None))`.
     - Determine `order_by_supplied = (order_by is not strawberry.UNSET and order_by is not None)`.
     - Calculate `policy = policy_from_info(info)`.
     - Calculate `offset_ceiling = policy.max_list_rows`.
     - Calculate `effective_ceiling = effective_bound(policy.max_list_rows, max_rows, trusted=trusted_max_rows)`.
     - Validate `offset` FIRST:
       - If `offset is not None`:
         - If `isinstance(offset, bool)` or `not isinstance(offset, int)`: raise `ListArgumentError(field_name, _resolve_argument_wire_name(info, "offset"), reason="non_integer", value=describe_value(offset))`.
         - If `offset < 0`: raise `ListArgumentError(field_name, _resolve_argument_wire_name(info, "offset"), reason="negative", value=offset)`.
         - If `offset > offset_ceiling`: raise `ListArgumentError(field_name, _resolve_argument_wire_name(info, "offset"), reason="over_ceiling", value=offset, ceiling=offset_ceiling)`.
     - Validate `limit` SECOND:
       - If `limit is not None`:
         - If `isinstance(limit, bool)` or `not isinstance(limit, int)`: raise `ListArgumentError(field_name, _resolve_argument_wire_name(info, "limit"), reason="non_integer", value=describe_value(limit))`.
         - If `limit < 0`: raise `ListArgumentError(field_name, _resolve_argument_wire_name(info, "limit"), reason="negative", value=limit)`.
         - If `limit > effective_ceiling`: raise `ListArgumentError(field_name, _resolve_argument_wire_name(info, "limit"), reason="over_ceiling", value=limit, ceiling=effective_ceiling)`.
     - Return `_ListArguments(offset=offset, limit=limit, effective_ceiling=effective_ceiling, order_by=order_by, order_by_supplied=order_by_supplied, any_argument_supplied=any_argument_supplied)`.

4. **Implement `_synthesized_list_signature` in [`django_strawberry_framework/list_field.py`][list-field]:**
   - Inspect `definition = getattr(target_type, "__django_strawberry_definition__", None)`.
   - Build parameter list:
     - `inspect.Parameter("root", inspect.Parameter.POSITIONAL_OR_KEYWORD, default=None)`
     - `inspect.Parameter("info", inspect.Parameter.KEYWORD_ONLY, annotation=Info)`
     - `inspect.Parameter("offset", inspect.Parameter.KEYWORD_ONLY, default=None, annotation=int | None)`
     - `inspect.Parameter("limit", inspect.Parameter.KEYWORD_ONLY, default=None, annotation=int | None)`
     - If `definition is not None and definition.orderset_class is not None`:
       - Locally import `from .orders import order_input_type`.
       - Add `inspect.Parameter("order_by", inspect.Parameter.KEYWORD_ONLY, default=None, annotation=list[order_input_type(definition.orderset_class)] | None)`.
   - Set signature return annotation to `inspect.Signature.empty`.
   - Build annotations map omitting `"return"`.
   - Return `(sig, annotations)`.

5. **Update resolver wrappers and signature assignment in [`django_strawberry_framework/list_field.py`][list-field] (lines 348-436):**
   - Update `_default`, async `_wrap`, and sync `_wrap` to accept `*args, offset: Any = None, limit: Any = None, order_by: Any = strawberry.UNSET, **kwargs`.
   - Extract `root` and `info` from arguments (`root = args[0] if args else kwargs.get("root")`, `info = args[1] if len(args) > 1 else kwargs["info"]`).
   - Call `args_record = _normalize_list_arguments("DjangoListField", info, max_rows, trusted_max_rows, offset=offset, limit=limit, order_by=order_by)`.
   - Pass `offset=args_record.offset` and `requested_limit=args_record.limit` to `bounded_rows` and `bounded_rows_async`.
   - Note: For Slice 1, preserve existing resolver execution and post-processing; full `orderBy` application lands in Slice 2.
   - Assign `wrapped.__signature__, wrapped.__annotations__ = _synthesized_list_signature(target_type)` before passing to `strawberry.field(...)`.

6. **Extend `bounded_rows` and `bounded_rows_async` in [`django_strawberry_framework/resource_policy.py`][resource-policy] (lines 524-638):**
   - Update signatures to include `*, offset: int | None = None, requested_limit: int | None = None, trusted: bool = False`.
   - Calculate `start = offset if offset is not None else 0`.
   - Calculate `window = requested_limit if requested_limit is not None else effective_cap`.
   - Calculate `stop = start + window`.
   - When `window == 0`: return `result[start:start]` if sliceable, else `[]` without consuming iterators.
   - Slicing fallback: `list(islice(result, start, stop))`.
   - In `bounded_rows_async`: if `not is_async_only_iterable(result)`, delegate to `bounded_rows(result, info, declared, offset=offset, requested_limit=requested_limit, trusted=trusted)`.
   - For async-only iterable: consume and discard `start` items, collect up to `window` items, and safely close via `_close_async_iterator`.

7. **Implement `_close_async_iterator` in [`django_strawberry_framework/resource_policy.py`][resource-policy]:**
   - Safely calls `aclose()` on async iterator if present.
   - If iteration failed with `primary_error`, catches cleanup exception and appends to `primary_error.__notes__`.
   - If iteration succeeded, propagates cleanup exception directly.

8. **Export `ListArgumentError` from package root in [`django_strawberry_framework/__init__.py`][package-init]:**
   - Import `ListArgumentError` from `.list_field` (line 26).
   - Add `"ListArgumentError"` to `__all__` alphabetically between `"FieldError"` and `"OptimizerHint"`.

9. **Update public surface pinning tests in [`tests/base/test_init.py`][test-base-init]:**
   - Update `test_public_api_surface_is_pinned` `__all__` tuple and comments (lines 66-97).
   - Update `test_star_import_preserves_namespace_hygiene`.
   - Update `test_reexported_types_resolve_to_canonical_subpackage_definitions` to assert identity between `from django_strawberry_framework import ListArgumentError` and `from django_strawberry_framework.list_field import ListArgumentError as ListListArgumentError`.

### Test additions / updates

- **Package unit tests in [`tests/test_list_field.py`][test-list-field]:**
  - *Signature synthesis test:* Build schema with and without `Meta.orderset_class`. Assert callable signature has keyword-only `info`, `offset: int | None`, `limit: int | None`, and conditional `order_by`. Assert `wrapped` has no return annotation (`inspect.Signature.empty`).
  - *Subpackage isolation test:* Assert importing `django_strawberry_framework` does not import `django_strawberry_framework.orders`.
  - *Runtime argument normalization & rejection test:* Call field resolver / normalizer directly with:
    - Boolean `offset=True`, `limit=False` -> rejected with `reason="non_integer"` and `describe_value`.
    - Non-integer string/float `offset="10"`, `limit=3.5` -> rejected with `reason="non_integer"` and `describe_value`.
    - Negative values `offset=-1`, `limit=-5` -> rejected with `reason="negative"`.
    - Over ceiling values: `offset > ResourcePolicy.max_list_rows`, `limit > effective_ceiling` -> rejected with `reason="over_ceiling"`, verifying `ceiling` in `extensions`.
    - Offset-before-limit precedence: both `offset` and `limit` invalid -> `offset` error raised first.
  - *Error serialization & pickle test:* Verify `ListArgumentError` reconstructs cleanly via `pickle.loads(pickle.dumps(err))`, maintaining `field`, `argument`, `reason`, `value`, `ceiling`, `args`, and `extensions`.
  - *Error-lazy wire name resolution test:* Instrument custom `NameConverter.from_argument`. Assert 0 calls across a batch of valid requests, and exactly 1 call when `ListArgumentError` is instantiated. Test schema with `auto_camel_case=False` producing `order_by`.
  - *Record field independence test:* Pin that `any_argument_supplied`, `offset=0` producing omission window, and `order_by_supplied` act independently.

- **Resource policy bounding tests in [`tests/test_resource_policy.py`][test-resource-policy]:**
  - Verify `bounded_rows` and `bounded_rows_async` with combinations of `offset` and `requested_limit` on sequences, non-subscriptable iterables, and async generators.
  - Verify `requested_limit=0` returns empty sequence without advancing unsliceable iterables.
  - Verify async generator cleanup with note attachment on failure.

### Implementation discretion items

- Whether `_ListArguments` is implemented using `@dataclass(slots=True, frozen=True)` or a plain class with explicit `__slots__`.
- Exact private helper name for async iterator cleanup in `resource_policy.py` (`_close_async_iterator` vs `_safe_aclose`).
- Phrasing and punctuation of the message string in `ListArgumentError` (so long as field, argument, rejected value, and accepted contract are clearly stated).

### Spec slice checklist (verbatim)

- [x] [`django_strawberry_framework/list_field.py`][list-field] synthesizes `offset: Int` and
      `limit: Int` on every `DjangoListField`; both are nullable and optional.
- [x] A package-owned [`ListArgumentError`][glossary-listargumenterror] rejects negative
      and over-ceiling runtime values with stable `extensions`; GraphQL's standard `Int` coercion owns wire type
      rejection before the resolver.
- [x] That class is exported from
      [`django_strawberry_framework/__init__.py`][package-init], and
      [`tests/base/test_init.py`][test-base-init]'s pinned `__all__` tuple, star-import row,
      and export-identity row are updated with it; the version literal and its own assertion
      stay with card 053.
- [x] Argument wire names are resolved only while building an error, never on a successful
      request.
- [x] The offset ceiling is `ResourcePolicy.max_list_rows`; no setting key is added.
- [x] Error payloads derive argument names from the active Strawberry schema rather than
      assuming the default camel-case converter.

### Boundary count and slice split analysis

- **New boundaries enumerated (9 total):**
  1. Offset boolean rejection (`isinstance(offset, bool)`) -> `ListArgumentError(..., reason="non_integer")`.
  2. Offset non-integer type guard (`not isinstance(offset, int)`) -> `ListArgumentError(..., reason="non_integer")`.
  3. Offset negative check (`offset < 0`) -> `ListArgumentError(..., reason="negative")`.
  4. Offset ceiling check (`offset > policy.max_list_rows`) -> `ListArgumentError(..., reason="over_ceiling")`.
  5. Limit boolean rejection (`isinstance(limit, bool)`) -> `ListArgumentError(..., reason="non_integer")`.
  6. Limit non-integer type guard (`not isinstance(limit, int)`) -> `ListArgumentError(..., reason="non_integer")`.
  7. Limit negative check (`limit < 0`) -> `ListArgumentError(..., reason="negative")`.
  8. Limit ceiling check (`limit > effective_ceiling`) -> `ListArgumentError(..., reason="over_ceiling")`.
  9. Precedence gate: deterministic offset-before-limit evaluation.
- **Split question answered:** Although 9 boundaries exist, they are all direct, cohesive validation rules for the two scalar pagination coordinates (`offset` and `limit`) executed in a single pre-resolver normalization pass. Splitting them would fragment the normalization record and signature synthesis across multiple incomplete slices. No slice split is warranted.

### Hot-path budget declaration

- **Hot-path budget:** 0 `NameConverter.from_argument` calls across valid queries (lazy error-only resolution) and <= 50 µs median wall-clock overhead per resolver call for argument normalization on valid requests; measured via unit mock converter call counts and `timeit` across 1,000 iterations.

### Floor verification scope

- **Floor verification scope:** Re-run signature synthesis and resolver validation unit tests under Python 3.10, Django 4.2, and Strawberry 0.230.0. Owned by the final test-run gate per the build plan.

## Build report (Worker 2)

### Summary

Implemented Slice 1 of Card 050 (`DjangoListField` argument surface) covering pagination scalar argument synthesis (`offset: Int` and `limit: Int`), typed runtime argument validation and normalization via package-owned [`ListArgumentError`][glossary-listargumenterror], dynamic schema-driven argument wire name resolution for error payloads, ceiling lookup and propagation through `ResourcePolicy.bounded_rows` and `bounded_rows_async`, and isolated slotted normalization storage (`_ListArguments`). Added comprehensive test suites pinning all 9 boundaries and verified zero converter calls on the valid hot path with sub-microsecond normalization overhead.

### Files touched

- [`django_strawberry_framework/list_field.py`][list-field]:
  - Defined `ListArgumentError(GraphQLError, DjangoStrawberryFrameworkError)` with `reason`, `argument`, `value`, and optional `ceiling` attributes, stable GraphQL `extensions`, and explicit `__reduce__` tuple ensuring reliable pickle round-tripping.
  - Implemented `_resolve_argument_wire_name(info, arg_name)` retrieving `StrawberryConfig.name_converter.from_argument(...)` lazily via `schema_config_from_info`, falling back to `arg_name` when info or schema config is absent.
  - Defined `_ListArguments` slotted struct (`offset`, `limit`, `order_by`, `order_by_supplied`, `any_argument_supplied`) to isolate pagination coordinates without dictionary overhead.
  - Implemented `_normalize_list_arguments(...)` enforcing 9 validation boundaries (type guard, negative, ceiling, precedence) on `offset` and `limit`.
  - Extended `_synthesized_list_signature` to inject nullable optional `offset: int | None = None` and `limit: int | None = None` parameters.
  - Updated `_wrap` (sync and async resolver wrappers) to normalize pagination coordinates before resolver invocation.
- [`django_strawberry_framework/resource_policy.py`][resource-policy]:
  - Extended `bounded_rows` and `bounded_rows_async` signatures to accept `offset: int | None = None` and `requested_limit: int | None = None`, applying offset slicing and effective bound limits while preserving backward-compatible positional calling.
- [`django_strawberry_framework/__init__.py`][package-init]:
  - Exported `ListArgumentError` in `__all__`.
- [`tests/base/test_init.py`][test-base-init]:
  - Added `ListArgumentError` to pinned `__all__` tuple, star-import verification, and export identity tests.
- [`tests/test_resource_policy.py`][test-resource-policy]:
  - Added test cases verifying `bounded_rows` and `bounded_rows_async` behavior with `offset` and `requested_limit`.
- [`tests/test_list_field.py`][test-list-field]:
  - Added unit and boundary tests covering `ListArgumentError` attributes/extensions/repr/pickling, lazy wire name resolution, zero converter calls on valid requests, signature synthesis, package root isolation, combined boundary coverage in `test_normalize_list_arguments_all_boundaries`, and dedicated parametrized suites for each of the 9 boundaries (`test_normalize_list_arguments_boundary_1_offset_boolean_rejected` through `test_normalize_list_arguments_boundary_9_precedence_offset_before_limit`).
- `docs/builder/temp-tests/slice-1/proofs.json`:
  - Mechanized failability proof manifest defining anchors, mutations, and scopes for all 9 boundaries.
- `docs/builder/bld-slice-1-argument_normalization.md`:
  - Updated status, checklist ticks, and appended this build report.
- `docs/builder/worker-memory/worker-2.md`:
  - Appended pass memory entry.

### Tests added or updated

- `tests/base/test_init.py`:
  - `tests/base/test_init.py::test_all_export_identities` (updated with `ListArgumentError`)
  - `tests/base/test_init.py::test_star_import_matches_all` (updated with `ListArgumentError`)
  - `tests/base/test_init.py::test_package_all_matches_pinned_tuple` (updated with `ListArgumentError`)
- `tests/test_resource_policy.py`:
  - `tests/test_resource_policy.py::test_bounded_rows_with_offset_and_requested_limit`
  - `tests/test_resource_policy.py::test_bounded_rows_async_with_offset_and_requested_limit`
- `tests/test_list_field.py`:
  - `tests/test_list_field.py::test_list_argument_error_properties_extensions_and_repr`
  - `tests/test_list_field.py::test_list_argument_error_pickle_roundtrip`
  - `tests/test_list_field.py::test_resolve_argument_wire_name_fallback_and_custom`
  - `tests/test_list_field.py::test_resolve_argument_wire_name_zero_calls_on_valid_normalization`
  - `tests/test_list_field.py::test_synthesized_list_signature_without_and_with_orderset`
  - `tests/test_list_field.py::test_subpackage_isolation_orders_not_imported_at_package_root`
  - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
  - `tests/test_list_field.py::test_normalize_list_arguments_boundary_1_offset_boolean_rejected`
  - `tests/test_list_field.py::test_normalize_list_arguments_boundary_2_offset_non_integer_rejected`
  - `tests/test_list_field.py::test_normalize_list_arguments_boundary_3_offset_negative_rejected`
  - `tests/test_list_field.py::test_normalize_list_arguments_boundary_4_offset_over_ceiling_rejected`
  - `tests/test_list_field.py::test_normalize_list_arguments_boundary_5_limit_boolean_rejected`
  - `tests/test_list_field.py::test_normalize_list_arguments_boundary_6_limit_non_integer_rejected`
  - `tests/test_list_field.py::test_normalize_list_arguments_boundary_7_limit_negative_rejected`
  - `tests/test_list_field.py::test_normalize_list_arguments_boundary_8_limit_over_ceiling_rejected`
  - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit`

### Validation run

- Command: `uv run pytest tests/base/test_init.py tests/test_resource_policy.py tests/test_list_field.py --no-cov`
- Result: **PASS — `225 passed in 6.13s`**
- Formatting & linting verification:
  - `uv run ruff format django_strawberry_framework/list_field.py django_strawberry_framework/resource_policy.py django_strawberry_framework/__init__.py tests/base/test_init.py tests/test_list_field.py tests/test_resource_policy.py` -> 0 changes
  - `uv run ruff check --fix django_strawberry_framework/list_field.py django_strawberry_framework/resource_policy.py django_strawberry_framework/__init__.py tests/base/test_init.py tests/test_list_field.py tests/test_resource_policy.py` -> 0 violations
  - `uv run python scripts/check_trailing_commas.py` -> 0 violations (`Fixed 0 file(s)`)

### Failability proofs

Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked — the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/list_field.py::_normalize_list_arguments offset boolean rejection` | `django_strawberry_framework/list_field.py` | `if isinstance(norm_offset, bool) or not isinstance(norm_offset, int): raise ListArgumentError( field_name, _resolve_a...` -> `if not isinstance(norm_offset, int): raise ListArgumentError( field_name, _resolve_argument_wire_name(info, "offset")...` - builder's description (unverified prose): isinstance(norm_offset, bool) check removed from offset type guard | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 3cb5e2d0c16ef917... == 3cb5e2d0c16ef917... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/list_field.py::_normalize_list_arguments offset non-integer type guard` | `django_strawberry_framework/list_field.py` | `if isinstance(norm_offset, bool) or not isinstance(norm_offset, int): raise ListArgumentError( field_name, _resolve_a...` -> `if isinstance(norm_offset, bool): raise ListArgumentError( field_name, _resolve_argument_wire_name(info, "offset"), r...` - builder's description (unverified prose): not isinstance(norm_offset, int) check removed from offset type guard | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 3cb5e2d0c16ef917... == 3cb5e2d0c16ef917... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/list_field.py::_normalize_list_arguments offset negative check` | `django_strawberry_framework/list_field.py` | deleted: `if norm_offset < 0: raise ListArgumentError( field_name, _resolve_argument_wire_name(info, "offset"), reason="negativ...` - builder's description (unverified prose): norm_offset < 0 check deleted | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 3cb5e2d0c16ef917... == 3cb5e2d0c16ef917... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/list_field.py::_normalize_list_arguments offset ceiling check` | `django_strawberry_framework/list_field.py` | deleted: `if norm_offset > offset_ceiling: raise ListArgumentError( field_name, _resolve_argument_wire_name(info, "offset"), re...` - builder's description (unverified prose): norm_offset > offset_ceiling check deleted | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 3cb5e2d0c16ef917... == 3cb5e2d0c16ef917... (vs pre-mutation copy) |
| 5 | `django_strawberry_framework/list_field.py::_normalize_list_arguments limit boolean rejection` | `django_strawberry_framework/list_field.py` | `if isinstance(norm_limit, bool) or not isinstance(norm_limit, int): raise ListArgumentError( field_name, _resolve_arg...` -> `if not isinstance(norm_limit, int): raise ListArgumentError( field_name, _resolve_argument_wire_name(info, "limit"), ...` - builder's description (unverified prose): isinstance(norm_limit, bool) check removed from limit type guard | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 3cb5e2d0c16ef917... == 3cb5e2d0c16ef917... (vs pre-mutation copy) |
| 6 | `django_strawberry_framework/list_field.py::_normalize_list_arguments limit non-integer type guard` | `django_strawberry_framework/list_field.py` | `if isinstance(norm_limit, bool) or not isinstance(norm_limit, int): raise ListArgumentError( field_name, _resolve_arg...` -> `if isinstance(norm_limit, bool): raise ListArgumentError( field_name, _resolve_argument_wire_name(info, "limit"), rea...` - builder's description (unverified prose): not isinstance(norm_limit, int) check removed from limit type guard | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 3cb5e2d0c16ef917... == 3cb5e2d0c16ef917... (vs pre-mutation copy) |
| 7 | `django_strawberry_framework/list_field.py::_normalize_list_arguments limit negative check` | `django_strawberry_framework/list_field.py` | deleted: `if norm_limit < 0: raise ListArgumentError( field_name, _resolve_argument_wire_name(info, "limit"), reason="negative"...` - builder's description (unverified prose): norm_limit < 0 check deleted | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 3cb5e2d0c16ef917... == 3cb5e2d0c16ef917... (vs pre-mutation copy) |
| 8 | `django_strawberry_framework/list_field.py::_normalize_list_arguments limit ceiling check` | `django_strawberry_framework/list_field.py` | deleted: `if norm_limit > effective_ceiling: raise ListArgumentError( field_name, _resolve_argument_wire_name(info, "limit"), r...` - builder's description (unverified prose): norm_limit > effective_ceiling check deleted | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 3cb5e2d0c16ef917... == 3cb5e2d0c16ef917... (vs pre-mutation copy) |
| 9 | `django_strawberry_framework/list_field.py::_normalize_list_arguments precedence offset before limit` | `django_strawberry_framework/list_field.py` | `if norm_offset is not None: if isinstance(norm_offset, bool) or not isinstance(norm_offset, int): raise ListArgumentE...` -> `if norm_limit is not None: if isinstance(norm_limit, bool) or not isinstance(norm_limit, int): raise ListArgumentErro...` - builder's description (unverified prose): evaluation order inverted: limit validated before offset | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 3cb5e2d0c16ef917... == 3cb5e2d0c16ef917... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset boolean rejection` — pinned
2. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset non-integer type guard` — pinned
3. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset negative check` — pinned
4. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset ceiling check` — inside Worker 3's mandatory re-run floor (<= 3 rows)
5. `django_strawberry_framework/list_field.py::_normalize_list_arguments limit boolean rejection` — inside Worker 3's mandatory re-run floor (<= 3 rows)
6. `django_strawberry_framework/list_field.py::_normalize_list_arguments limit non-integer type guard` — inside Worker 3's mandatory re-run floor (<= 3 rows)
7. `django_strawberry_framework/list_field.py::_normalize_list_arguments limit negative check` — inside Worker 3's mandatory re-run floor (<= 3 rows)
8. `django_strawberry_framework/list_field.py::_normalize_list_arguments limit ceiling check` — inside Worker 3's mandatory re-run floor (<= 3 rows)
9. `django_strawberry_framework/list_field.py::_normalize_list_arguments precedence offset before limit` — pinned

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset boolean rejection`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `========================= 4 failed, 78 passed in 5.37s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================== 82 passed in 5.45s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_1_offset_boolean_rejected[True]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_1_offset_boolean_rejected[False]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[True--1-non_integer]`
2. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset non-integer type guard`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `========================= 4 failed, 78 passed in 5.41s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================== 82 passed in 5.39s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_2_offset_non_integer_rejected[ten-str 'ten']`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_2_offset_non_integer_rejected[3.14-float 3.14]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[bad-101-non_integer]`
3. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset negative check`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `========================= 5 failed, 77 passed in 5.39s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================== 82 passed in 5.37s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_resolve_argument_wire_name_zero_calls_on_valid_normalization`
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_3_offset_negative_rejected[-1]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_3_offset_negative_rejected[-10]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[-1--2-negative]`
4. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset ceiling check`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `========================= 3 failed, 79 passed in 5.29s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================== 82 passed in 5.32s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_4_offset_over_ceiling_rejected[101]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_4_offset_over_ceiling_rejected[500]`
5. `django_strawberry_framework/list_field.py::_normalize_list_arguments limit boolean rejection`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `========================= 3 failed, 79 passed in 5.28s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================== 82 passed in 5.31s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_5_limit_boolean_rejected[True]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_5_limit_boolean_rejected[False]`
6. `django_strawberry_framework/list_field.py::_normalize_list_arguments limit non-integer type guard`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `========================= 3 failed, 79 passed in 5.27s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================== 82 passed in 5.36s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_6_limit_non_integer_rejected[twenty-str 'twenty']`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_6_limit_non_integer_rejected[3.14-float 3.14]`
7. `django_strawberry_framework/list_field.py::_normalize_list_arguments limit negative check`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `========================= 3 failed, 79 passed in 5.27s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================== 82 passed in 5.37s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_7_limit_negative_rejected[-1]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_7_limit_negative_rejected[-10]`
8. `django_strawberry_framework/list_field.py::_normalize_list_arguments limit ceiling check`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `========================= 3 failed, 79 passed in 5.23s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================== 82 passed in 5.26s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_8_limit_over_ceiling_rejected[50-False-51-50]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_8_limit_over_ceiling_rejected[200-True-201-200]`
9. `django_strawberry_framework/list_field.py::_normalize_list_arguments precedence offset before limit`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `========================= 4 failed, 78 passed in 5.38s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================== 82 passed in 5.60s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[-1--2-negative]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[True--1-non_integer]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[bad-101-non_integer]`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` — the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all — and a 0 from such a run is not a zero-row result: resolve it and re-run.

### Hot-path budget

- **Budget declaration from plan:** 0 `NameConverter.from_argument` calls across valid queries (lazy error-only resolution) and <= 50 µs median wall-clock overhead per resolver call for argument normalization on valid requests.
- **Lazy wire name resolution calls measured:**
  - Valid queries: **0** calls to `NameConverter.from_argument`. Verified via `tests/test_list_field.py::test_resolve_argument_wire_name_zero_calls_on_valid_normalization` tracking mock converter calls across 10 valid normalizations.
  - Invalid queries: Exactly **1** call only when building the `ListArgumentError` payload.
- **Wall-clock overhead measured:**
  - Measurement benchmark: 10 repeats of 1,000 iterations calling `_normalize_list_arguments("items", info, None, False, offset=10, limit=20)`.
  - Result: **0.467 µs** median per-call overhead (Min: 0.446 µs, Max: 0.487 µs).
  - Verdict: **PASS** — measured 0.467 µs is > 100x below the <= 50 µs ceiling.

### Floor verification

Owned by the final gate per the plan's declaration.

### Implementation notes

- **Dual-base `ListArgumentError` with explicit `__reduce__`:** `ListArgumentError` subclasses both `strawberry.exceptions.GraphQLError` and `DjangoStrawberryFrameworkError`. Because `GraphQLError` uses slots and complex internals, standard pickle serialization would fail without a customized `__reduce__` method returning `(cls, args, self.__dict__)`. Verified by `test_list_argument_error_pickle_roundtrip`.
- **Slotted `_ListArguments`:** Implemented with `__slots__` and no `__dict__` overhead to ensure zero-allocation overhead on the hot resolver execution path.
- **Precedence gate:** Validation order enforces `offset` evaluation strictly prior to `limit`. Mutating the evaluation sequence inverts the error order when both coordinates are invalid and fails 4 distinct test node IDs.
- **Subpackage isolation:** Re-verified that importing `django_strawberry_framework` does not eagerly import or leak `orders/` or other subpackages.

### Notes for Worker 3

- **Re-run scope for the independent failability check:** `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py`.
- **Mandatory re-run floor:** Boundaries 4, 5, 6, 7, and 8 have 3 failing rows each and fall inside Worker 3's mandatory re-run floor (<= 3 rows). All 9 boundaries can be verified mechanically using:
  `uv run python scripts/prove_failability.py docs/builder/temp-tests/slice-1/proofs.json`
- **Pristine state:** Pre-mutation copy was byte-compared and SHA-256 matched upon restore.
- **Hot-path budget verification:** Run:
  `uv run pytest tests/test_list_field.py::test_resolve_argument_wire_name_zero_calls_on_valid_normalization --no-cov`
  and the timing benchmark snippet documented in `### Hot-path budget`.

### Notes for Worker 1 (spec reconciliation)

- All 6 checklist items from `docs/spec-050-list_field_arguments-0_0_15.md` (lines 67-82) are fulfilled and ticked.
- No spec gaps or deviations discovered during implementation of Slice 1.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

None.
- Abstraction hygiene: No redundant wrappers or gratuitous layers introduced. Slotted `_ListArguments` avoids object allocation overhead on the resolver execution path.
- Existing helper reuse: Reused `describe_value` from `exceptions.py`, `effective_bound` and `_raw_list_bound` from `resource_policy.py`, and `schema_config_from_info` from `utils/typing.py`.
- Shared logic: Factored `_close_async_iterator` cleanly in `resource_policy.py` to share the `__notes__` error propagation logic between normal early exit (zero window / prefix reached) and iteration error cleanup without duplication.

### Failability audit

- Audited all 9 boundaries recorded by Worker 2. Anchor checks passed cleanly for all 9 boundaries with zero failures and zero collection/setup errors. No boundary is weakly pinned (all >= 3 failing rows).
- **Mandatory re-run floor:** Boundaries with failing rows <= 3 (boundaries 4, 5, 6, 7, and 8) were independently re-run using `scripts/prove_failability.py` with the recorded scope (`tests/test_list_field.py`). Node-id sets and failing row counts matched Worker 2's build report exactly:
  - Boundary 4 (`offset ceiling check`, 3 rows):
    - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
    - `tests/test_list_field.py::test_normalize_list_arguments_boundary_4_offset_over_ceiling_rejected[101]`
    - `tests/test_list_field.py::test_normalize_list_arguments_boundary_4_offset_over_ceiling_rejected[500]`
  - Boundary 5 (`limit boolean rejection`, 3 rows):
    - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
    - `tests/test_list_field.py::test_normalize_list_arguments_boundary_5_limit_boolean_rejected[True]`
    - `tests/test_list_field.py::test_normalize_list_arguments_boundary_5_limit_boolean_rejected[False]`
  - Boundary 6 (`limit non-integer type guard`, 3 rows):
    - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
    - `tests/test_list_field.py::test_normalize_list_arguments_boundary_6_limit_non_integer_rejected[twenty-str 'twenty']`
    - `tests/test_list_field.py::test_normalize_list_arguments_boundary_6_limit_non_integer_rejected[3.14-float 3.14]`
  - Boundary 7 (`limit negative check`, 3 rows):
    - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
    - `tests/test_list_field.py::test_normalize_list_arguments_boundary_7_limit_negative_rejected[-1]`
    - `tests/test_list_field.py::test_normalize_list_arguments_boundary_7_limit_negative_rejected[-10]`
  - Boundary 8 (`limit ceiling check`, 3 rows):
    - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
    - `tests/test_list_field.py::test_normalize_list_arguments_boundary_8_limit_over_ceiling_rejected[50-False-51-50]`
    - `tests/test_list_field.py::test_normalize_list_arguments_boundary_8_limit_over_ceiling_rejected[200-True-201-200]`
- **Boundaries accepted on Worker 2's record:** Boundaries 1, 2, 3, and 9 each carry > 3 failing rows (4, 4, 5, and 4 rows respectively) and were verified by checking anchors and audit inspection.
- **Restore verification:** Byte-comparison (`filecmp.cmp(shallow=False) True`) and SHA-256 match against pre-mutation copy verified for every mutant tested.

### Hot-path budget audit

- **Lazy wire name resolution:** Confirmed that `_resolve_argument_wire_name` makes 0 calls to `NameConverter.from_argument` on valid requests. Tested and verified via `tests/test_list_field.py::test_resolve_argument_wire_name_zero_calls_on_valid_normalization`.
- **Resolver call overhead:** Measured median overhead of 0.475 µs per call across 10 repeats of 1,000 iterations (budget <= 50 µs). Passes with > 100x margin.

### Public-surface check

Authorized by `docs/spec-050-list_field_arguments-0_0_15.md` lines 73-77 and 466-483: `ListArgumentError` added to `django_strawberry_framework/__init__.py` and exported in `__all__`. Pinned `__all__` tuple, star-import row, and export-identity row in `tests/base/test_init.py` updated and verified. No other public exports introduced.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- Precise implementation of `ListArgumentError` inheriting from `GraphQLError` and `DjangoStrawberryFrameworkError` with full pickle roundtrip support (`__reduce__`), stable GraphQL extensions, and proper omission of unused `noqa` comments.
- Subpackage isolation preserved: `django_strawberry_framework.orders` is lazily imported only inside `_synthesized_list_signature` when an orderset is present, preventing eager leakage at the root import.
- Pure argument normalization separating coordinate parsing (`_normalize_list_arguments`) from execution pipelines, with deterministic precedence (`offset` before `limit`).
- Clean bounding and async iterator handling: zero-window limits cleanly return empty results without advancing generators, and early-terminated async iterators have `aclose()` called with non-destructive exception chaining via `__notes__`.

### Temp test verification

- Manifest and temp test proofs: `docs/builder/temp-tests/slice-1/proofs.json`.
- Disposition: Preserved under `docs/builder/temp-tests/slice-1/` as regenerable proof artifacts; permanent test cases are checked into `tests/test_list_field.py` and `tests/test_resource_policy.py`.

### Notes for Worker 1 (spec reconciliation)

None; all 6 checklist items from spec-050 lines 67-82 are implemented faithfully with zero drift or gaps.

### Review outcome

review-accepted

---

## Final verification (Worker 1)

### Summary

Slice 1 shipped the argument normalization and typed runtime rejection surface for
`DjangoListField`:
- Synthesized optional and nullable `offset: Int` and `limit: Int` parameters on `DjangoListField`
  resolver signatures, preserving outer nullability via `inspect.Signature.empty` return
  annotation.
- Implemented [`ListArgumentError`][glossary-listargumenterror] dual-inheriting from
  `GraphQLError` and `DjangoStrawberryFrameworkError` with stable GraphQL extensions and pickle
  roundtrip support via explicit `__reduce__`.
- Exported [`ListArgumentError`][glossary-listargumenterror] from
  [`django_strawberry_framework/__init__.py`][package-init] root and pinned `__all__`, star
  imports, and identity tests in [`tests/base/test_init.py`][test-base-init].
- Implemented lazy GraphQL argument wire name lookup (`_resolve_argument_wire_name`) via active
  Strawberry schema `NameConverter` evaluated strictly on error construction.
- Enforced 9 validation boundaries in `_normalize_list_arguments` with deterministic `offset`-before-`limit`
  precedence and ceiling bounds (`offset` capped at `ResourcePolicy.max_list_rows`, `limit` capped
  at `effective_bound`).
- Extended `bounded_rows` and `bounded_rows_async` in [`django_strawberry_framework/resource_policy.py`][resource-policy]
  to support `offset` and `requested_limit`, including safe early cleanup via
  `_close_async_iterator` without advancing generators on zero window.

### Checklist audit

Every planned item in `### Spec slice checklist (verbatim)` was verified against the diff:
- [x] [`django_strawberry_framework/list_field.py`][list-field] synthesizes `offset: Int` and
      `limit: Int` on every `DjangoListField`; both are nullable and optional. (Verified in
      `_synthesized_list_signature` and
      `tests/test_list_field.py::test_synthesized_list_signature_without_and_with_orderset`).
- [x] A package-owned [`ListArgumentError`][glossary-listargumenterror] rejects negative and
      over-ceiling runtime values with stable `extensions`; GraphQL's standard `Int` coercion owns
      wire type rejection before the resolver. (Verified in
      [`django_strawberry_framework/list_field.py`][list-field] `ListArgumentError` and boundary test
      suites in [`tests/test_list_field.py`][test-list-field]).
- [x] That class is exported from [`django_strawberry_framework/__init__.py`][package-init], and
      [`tests/base/test_init.py`][test-base-init]'s pinned `__all__` tuple, star-import row, and
      export-identity row are updated with it; the version literal and its own assertion stay with
      card 053. (Verified in [`django_strawberry_framework/__init__.py`][package-init] and
      [`tests/base/test_init.py`][test-base-init]).
- [x] Argument wire names are resolved only while building an error, never on a successful request.
      (Verified by error-only invocation in `_normalize_list_arguments` and
      `tests/test_list_field.py::test_resolve_argument_wire_name_zero_calls_on_valid_normalization`
      asserting 0 calls on valid requests).
- [x] The offset ceiling is `ResourcePolicy.max_list_rows`; no setting key is added. (Verified in
      `_normalize_list_arguments` using `policy.max_list_rows`; confirmed no settings modified).
- [x] Error payloads derive argument names from the active Strawberry schema rather than assuming the
      default camel-case converter. (Verified by schema config resolution in
      `_resolve_argument_wire_name` and custom converter tests in
      `tests/test_list_field.py::test_resolve_argument_wire_name_fallback_and_custom`).

### Test run

Focused test suite command:
`uv run pytest tests/base/test_init.py tests/test_resource_policy.py tests/test_list_field.py --no-cov`

Result: **PASS** (`225 passed in 6.45s`, exit code 0).
Ran without `--cov*` flags per [`BUILD.md`][build-md] guidelines; zero test failures or regressions.

### Failability and fail-open confirmation

- **Failability proofs:** All 9 boundaries enumerated in the plan carry complete failability proof
  records in `docs/builder/temp-tests/slice-1/proofs.json`. Independently re-ran all 9 boundaries via
  `uv run python scripts/prove_failability.py docs/builder/temp-tests/slice-1/proofs.json`. All 9
  boundaries failed the exact expected set of test node IDs with zero collection/setup errors, and
  each was verified to cleanly restore via SHA-256 and byte-level comparison
  (`filecmp.cmp(shallow=False)`).
- **Fail-open audit:** Audited the working tree diff across
  [`django_strawberry_framework/list_field.py`][list-field] and
  [`django_strawberry_framework/resource_policy.py`][resource-policy]. Confirmed no fail-open
  shapes landed:
  - Coordinate presence checks explicitly test against `None` and `strawberry.UNSET`, properly
    recognizing `0` and `[]` as supplied coordinates rather than falling through to omission.
  - Type guards explicitly check boolean types (`isinstance(..., bool)`) before integer types
    (`not isinstance(..., int)`) to prevent Python's `bool` subclassing from coercing into valid
    integers.
  - Window calculations in `bounded_rows` and `bounded_rows_async` use explicit identity checks
    (`if offset is None and requested_limit is None`), guard `window == 0` without advancing
    unsliceable iterables, and fallback to `islice` on unsliceable inputs rather than returning
    unbounded sequences.
  - Exception handling in `_close_async_iterator` attaches cleanup errors to
    `primary_error.__notes__` without replacing the primary error on failure paths, and propagates
    cleanup errors directly when iteration succeeded cleanly.

### Spec changes made (Worker 1 only)

None.

### Notes for the build plan

Slice 1 is accepted. The next slice is Slice 2 (`Meta-derived orderBy and list pipeline`). Staged
anchors for Slice 2 (`TODO(spec-050 slice 2)`) remain in
[`django_strawberry_framework/list_field.py`][list-field] and will be discharged when Slice 2 ships.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-listargumenterror]: ../GLOSSARY.md#listargumenterror
[spec-050]: ../spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-md]: BUILD.md

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[list-field]: ../../django_strawberry_framework/list_field.py
[package-init]: ../../django_strawberry_framework/__init__.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[typing-utils]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-list-field]: ../../tests/test_list_field.py
[test-resource-policy]: ../../tests/test_resource_policy.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
