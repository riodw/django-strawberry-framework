**Findings**

- [P2] Unopted writable nested serializer fields are still recursively fingerprinted before the
  opt-in rejection path can run. The previous read-only/narrowed-away regression is fixed, but
  [`django_strawberry_framework/rest_framework/inputs.py::serializer_schema_fingerprint`][rf-inputs]
  still descends into every writable nested serializer in the effective field set, regardless of
  whether that field is declared in `Meta.nested_fields`. For a nested field not opted in, the
  nested child shape cannot affect generated SDL because no nested input is supposed to be built;
  the contract is that
  [`django_strawberry_framework/rest_framework/serializer_converter.py::_reject_nested_serializer`][rf-converter]
  raises the explicit "nested serializer writes are opt-in only" error. I reproduced a serializer
  with `child = RaisingChild()` and no `Meta.nested_fields`; class creation fails earlier from the
  fingerprint with a misleading message saying "A nested serializer opted in via
  Meta.nested_fields..." even though it was not opted in. This is not a successful-write
  regression, but it is a DRF-first diagnostics and architecture issue: unsupported unopted nested
  fields should not require materializing child `.fields`, especially when the child serializer is
  context-sensitive. The fix should make recursive fingerprinting conditional on the same
  `NestedSerializerConfig` tree used by the input builder, or use a shallow fingerprint marker for
  unopted nested fields and let the field walk raise the canonical opt-in error. Add a test where
  an unopted writable nested child raises from `get_fields()` and assert the visible error is the
  opt-in-only nested serializer error, not the nested child materialization error.

**Verified Fixed**

- Nested serializer fields with `source=...` now record the normalized source axis and pass the
  runtime schema/agreement guard.
- Nested DRF validation errors are now recursively re-keyed to GraphQL names, e.g.
  `shelves.0.altBranches` instead of `shelves.0.alt_branches`.
- Read-only or narrowed-away nested serializers are no longer descended into by the effective-set
  fingerprint path.

**Verification**

- `uv run pytest` passed: 2759 passed, 4 skipped, 4 xfailed, 100% coverage.
- Targeted changed-test slice passed all 9 selected tests, but exited nonzero because a slice run
  cannot satisfy the repository-wide 100% coverage gate.
- Direct repros confirmed the three prior issues are fixed and the remaining unopted-nested
  diagnostic issue is still present.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[rf-converter]: ../django_strawberry_framework/rest_framework/serializer_converter.py
[rf-inputs]: ../django_strawberry_framework/rest_framework/inputs.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
