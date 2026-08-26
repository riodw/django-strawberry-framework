# Review: `django_strawberry_framework/mutations/fields.py`

Status: verified

## Understanding

`django_strawberry_framework/mutations/fields.py` implements `DjangoMutationField`, the write-side root field factory that exposes mutation classes (`DjangoMutation`, `DjangoModelFormMutation`, `DjangoFormMutation`, `SerializerMutation`) on Strawberry root mutation types (`@strawberry.type class Mutation`).

Key responsibilities and contracts traced:
1. **Dynamic forward-referencing without class annotations:** Unlike read-side field factories (`DjangoConnectionField`, `DjangoNodeField`), write-side mutation payloads (`<Name>Payload`) are dynamically materialized during phase 2.5 of `finalize_django_types()`, which occurs after `@strawberry.type class Mutation` annotations evaluate. The field is assigned without a type annotation (`create_item = DjangoMutationField(CreateItem)`), and `_synthesized_mutation_signature` injects an `inspect.Signature` and `__annotations__` mapping with a `strawberry.lazy` forward reference (`_lazy_ref`) to `<Name>Payload` in `mutations.inputs`.
2. **Shared signature building:** `build_lazy_field_signature` builds resolver signatures injecting `root` (positional/keyword default `None`), `info: Info` (keyword-only), operation-specific parameters (`id: strawberry.ID`, `data: strawberry.lazy(...)`), and the return forward-ref. This helper is shared with auth fixed-field factories (`auth/mutations.py`).
3. **Runtime async context dispatch:** The synthesized `_resolve` resolver dynamically routes calls via `strawberry.utils.inspect.in_async_context()` to `mutation_cls.resolve_async` or `mutation_cls.resolve_sync`, enabling a single field declaration to serve both synchronous and asynchronous schema execution.
4. **Target validation & lifecycle guard:** `_validate_mutation_target` verifies duck-typed mutation protocol conformity via `_has_mutation_protocol` (`_mutation_meta`, callable `resolve_sync`, `resolve_async`, `input_type_name`, and non-`None` `input_module_path`), ensures the class owns its own `_mutation_meta` (rejecting abstract bases and un-redeclared subclasses), and asserts membership in the active declaration ledger (`iter_mutations()` or `iter_form_mutations()`).
5. **Mutation atomicity marker:** Stamps `MUTATION_CLASS_MARKER` (`_django_mutation_cls`) on the resolver function for `schema.py::DjangoMutationExecutionContext` to locate the target mutation class and manage transaction boundaries.
6. **Metadata passthrough:** Accepts `description`, `deprecation_reason`, and `directives` keyword arguments and passes them directly to `strawberry.field`.

## Verification

1. **Existing Test Suite:** Examined 13 test cases in `tests/mutations/test_fields.py`, covering argument signature synthesis across operations (`create`, `update`, `delete`), lazy payload resolution post-bind, sync and async resolver dispatch, and construction-time validation of hostile, non-class, abstract base, inherited, and un-registered targets across all mutation flavors (`DjangoMutation`, `DjangoModelFormMutation`, `DjangoFormMutation`, `SerializerMutation`).
2. **Scratch Experiments:** Created `docs/review/temp-tests/mutations__fields/test_scratch_fields.py` testing target protocol variations and metadata propagation (`description`, `deprecation_reason`).
3. **Coverage Check:** Verified 100% statement coverage (62/62 statements) on `django_strawberry_framework/mutations/fields.py`.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/mutations/fields.py` is a clean, well-factored field factory with comprehensive target validation, robust signature synthesis, and reliable async context dispatch. A permanent test was added to `tests/mutations/test_fields.py` to explicitly pin `description` and `deprecation_reason` metadata passthrough.

## Implementation (Worker 1)

- **Changed Files:**
  - `tests/mutations/test_fields.py`: Added permanent test `test_mutation_field_metadata_passthrough` to pin `description` and `deprecation_reason` passthrough to Strawberry field definitions.
- **Permanent Tests:**
  - `tests/mutations/test_fields.py::test_mutation_field_metadata_passthrough`: Confirms that `DjangoMutationField(..., description=..., deprecation_reason=...)` correctly propagates schema-level field metadata to the generated GraphQL type definition.
- **Scratch / Focused Verification:**
  - Ran `pytest docs/review/temp-tests/mutations__fields/test_scratch_fields.py` (2 passed).
  - Ran `pytest tests/mutations/test_fields.py` (14 passed).
- **Formatter and Linter Results:**
  - `uv run ruff format .` reformatted `tests/mutations/test_fields.py`.
  - `uv run ruff check --fix .` passed cleanly with 0 errors.
- **Evidence for Rejected Findings:**
  - No findings were rejected; the module operates in strict accordance with the architecture specifications.
- **Changelog Entry:**
  - None — zero functional change to production code; test coverage enhancement only.

## Independent verification (Worker 2)

- **Target Verification:**
  - Verified `git diff 12779c99 -- django_strawberry_framework/mutations/fields.py` is empty (zero production diff against baseline `HEAD`).
- **Behavior & Contract Trace:**
  - Re-traced `build_lazy_field_signature` argument parameter construction (`root`, `info: Info`, keyword-only arguments) and return annotation mapping, confirming parity and shared usage across `mutations/fields.py` and `auth/mutations.py`.
  - Re-traced `_synthesized_mutation_signature` parameter dispatch across `create`, `update`, `delete`, and `form` operations (`operation_takes_id`, `operation_takes_data`), verifying dynamic lazy forward references (`_lazy_ref`) pointing to `<Name>Payload` in `mutations.inputs` and `data:` input type references across models, forms, and serializers.
  - Re-traced `_validate_mutation_target` protocol check (`_has_mutation_protocol`), concrete `Meta` ownership check, and lifecycle registration verification against `iter_mutations()` / `iter_form_mutations()`.
  - Re-traced `in_async_context()` runtime dispatch in `_resolve` and the `MUTATION_CLASS_MARKER` stamping (`_django_mutation_cls`) used by `schema.py::DjangoMutationExecutionContext` to open completion-spanning transactions.
- **Test Executions:**
  - Ran focused test suite: `pytest tests/mutations/test_fields.py --no-cov` (14 passed).
  - Ran scratch tests: `pytest docs/review/temp-tests/mutations__fields/test_scratch_fields.py --no-cov` (2 passed).
  - Ran integration write transaction / auth mutation tests: `pytest tests/mutations/test_write_transaction.py tests/auth/test_mutations.py --no-cov` (156 passed).
- **Disposition of Findings:**
  - No defects or regressions found. All contracts and behaviors operate as designed.
- **Conclusion:**
  - Production code is verified and requires zero changes. Test suite has been strengthened with explicit metadata passthrough validation.
