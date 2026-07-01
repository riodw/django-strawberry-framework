**Findings**

- [P1] The schema fingerprint now descends into read-only or narrowed-away nested serializers, so
  serializers that should remain valid for mutations can fail at class creation. The input builder
  drops `read_only` fields and also respects `Meta.fields` narrowing, but
  [`django_strawberry_framework/rest_framework/inputs.py::serializer_schema_fingerprint`][rf-inputs]
  calls the nested fingerprint path over the raw schema field map before that effective input set
  is considered. I reproduced this with `child = ContextChild(read_only=True)` and a mutation
  declaring `Meta.fields = ("name",)`: class definition raises the child serializer's raw
  `RuntimeError("child fields should not be read")`, even though `child` is not part of the
  mutation input. This is a regression risk for common DRF serializers that expose read-only
  nested output fields or context-sensitive nested read serializers. The fingerprint should be
  scoped to the same writable/effective field set used to generate the input, or at minimum skip
  nested recursion for fields that cannot participate in the generated input; any nested
  fingerprint exception should also be wrapped as `ConfigurationError` if it is still reachable.

- [P1] Opted-in nested serializer fields with DRF `source=...` build a schema and then fail the
  runtime agreement guard. [`django_strawberry_framework/rest_framework/inputs.py::_resolve_nested_field`][rf-inputs]
  hard-codes `InputFieldSpec.source=None` for nested specs, while
  [`django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement`][rf-resolvers]
  compares `spec.source or target` against the runtime field's bound source. A field like
  `renamed = ChildSerializer(source="actual")` produces `spec.source is None`, then every mutation
  invocation raises `ConfigurationError` before `is_valid()`: runtime source `"actual"` disagrees
  with schema source `"renamed"`. Nested fields should record the same normalized source axis as
  scalar/relation serializer fields. If dotted source or `source="*"` is intentionally unsupported
  for nested writes, reject it during `_resolve_nested_field` with the existing fail-loud source
  policy rather than accepting a schema that cannot execute.

- [P2] Nested DRF validation errors are not recursively re-keyed to GraphQL field names. The new
  decode path already reports nested relation decode errors as GraphQL paths such as
  `shelves.0.altBranches`, but
  [`django_strawberry_framework/rest_framework/resolvers.py::serializer_errors_to_field_errors`][rf-resolvers]
  still documents and implements root-only re-keying through `_rekey_root`. I reproduced
  `{"shelves": [{"alt_branches": [ErrorDetail("Bad pk", code="invalid")]}]}` flattening to
  `shelves.0.alt_branches` with path `["shelves", "0", "alt_branches"]`, even though the SDL field
  is `altBranches`. This leaks serializer names for nested child fields, aliases, and relation
  suffixes, and makes DRF validation errors inconsistent with framework decode errors. Replace the
  flat reverse map with a recursive path mapper derived from `InputFieldSpec.nested_specs`, while
  preserving numeric indexes and `__all__` non-field segments.

**Verification**

- `uv run pytest` passed: 2750 passed, 4 skipped, 4 xfailed, 100% coverage.
- Targeted repros confirmed all three findings above against `HEAD` (`fc24b925`).

**Suggested Tests**

- A mutation whose serializer has a read-only nested serializer with a child `get_fields()` that
  raises if read, and whose mutation narrows that field away.
- A live or resolver-level nested write using `renamed = ChildSerializer(source="actual")` for both
  single and `many=True` nested fields.
- A nested DRF validation error on a child field whose GraphQL name differs from its serializer
  name, for example `alt_branches -> altBranches` or `shelf_code -> shelfCode`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[rf-inputs]: ../django_strawberry_framework/rest_framework/inputs.py
[rf-resolvers]: ../django_strawberry_framework/rest_framework/resolvers.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
