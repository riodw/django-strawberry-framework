# Spec 036 mutations -- DRY review

Review basis: latest committed delta ending at `bd998093` (`Refactor mutation input handling and
error reporting`). The working tree was clean when reviewed. This pass is scoped to duplication,
shared abstractions, and future drift risk; it is not a full correctness review.

## Verdict

No DRY issue here looks release-blocking by itself. The implementation is still readable and the
new behavior is well covered. The main opportunity is to single-source two concepts that now have
multiple local spellings:

- generated input shape identity / type-name derivation;
- typed GlobalID decode + model check + pk coercion.

The test suite also picked up enough duplicated mutation setup/assertion scaffolding that the next
mutation behavior change will likely require synchronized edits across several tests.

## DRY-1 (Medium) -- input shape identity is recomputed outside the input generator

`django_strawberry_framework/mutations/inputs.py::mutation_input_type_name` documents the input
identity as `(model, operation_kind, frozenset(effective_field_names))`, and
`django_strawberry_framework/mutations/inputs.py::build_mutation_input` computes the selected
fields, the full editable set, and the generated type name from that same shape.

`django_strawberry_framework/mutations/sets.py::_materialize_input_for` now recomputes
`effective_field_names`, builds a parallel `shape_key`, and then calls
`build_mutation_input`, which repeats the editable-field walk. The merged-input path then calls
`build_mutation_input` largely to recover the canonical shape name from `remainder.__name__`.

That is a drift point: if the generator's shape identity changes for relation attrs, file/upload
fields, operation-specific field eligibility, or future serializer/form mutation variants, the bind
cache can silently disagree with the generated name.

Recommendation: add a small shape descriptor helper in `mutations/inputs.py`, for example
`mutation_input_shape(model, operation_kind, fields=None, exclude=None)`, returning the selected
fields, full field names, effective field-name frozenset, generated type name, and cache key. Then
`build_mutation_input`, `_materialize_input_for`, and `_materialize_merged_input` should all consume
that descriptor instead of re-walking and reassembling the shape independently.

## DRY-2 (Medium) -- typed GlobalID decode/model-check/pk-coercion has two mutation implementations

The node field already owns the core decode/coerce mechanics through
`django_strawberry_framework/types/relay.py::decode_global_id` and
`django_strawberry_framework/relay.py::_coerce_pk_or_none`. The mutation resolver correctly reuses
the pk coercer, but it still has separate mutation-local implementations for the rest of the typed
decode contract:

- root update/delete ids: `django_strawberry_framework/mutations/resolvers.py::_coerce_lookup_id`;
- relation ids: `django_strawberry_framework/mutations/resolvers.py::_typecheck_relation_id` and
  `django_strawberry_framework/mutations/resolvers.py::_wrong_type_field_error`;
- relation visibility dispatch: `django_strawberry_framework/mutations/resolvers.py::_decode_single_relation_id`
  and `django_strawberry_framework/mutations/resolvers.py::_decode_relation_id_list`.

The error surfaces differ, so this should not become a node-field `GraphQLError` helper. But the
decode result can still be single-sourced as a structured primitive: decode the value, verify the
resolved model against an expected model, coerce through the resolved type's id field, and return a
success/failure code. The caller can then map the code to `FieldError("id")`, relation
`FieldError`, `None`, or `GraphQLError` as appropriate.

Recommendation: extract a non-GraphQL-raising helper near the Relay decode code or in a neutral
mutation utility, such as `decode_model_global_id(value, expected_model) -> DecodeResult`. Use it
from `_coerce_lookup_id` and `_typecheck_relation_id`. Then collapse the FK and M2M relation paths
onto one list-oriented relation decoder so the "type-check, coerce, maybe visibility-check in one
query" contract has a single implementation.

## DRY-3 (Low/Medium) -- create/update share the same validate-save-assign-refetch tail

`django_strawberry_framework/mutations/resolvers.py::_run_create` and
`django_strawberry_framework/mutations/resolvers.py::_run_update` necessarily differ in
authorization placement, instance construction/location, and partial-update `exclude` calculation.
After that, they both run the same tail:

- `full_clean` into payload;
- `save` into payload;
- M2M assignment;
- optimizer-planned refetch;
- success payload.

This is not a correctness bug, but it means any future change to write finalization, save error
mapping, M2M timing, or post-write refetch has to be patched twice. The recent `IntegrityError`
message change already had to touch both save call sites.

Recommendation: extract an internal helper, for example `_validate_save_assign_refetch_payload`,
that accepts `instance`, `exclude`, `m2m_assignments`, `primary_type`, `info`, `slot`, and
`payload_cls`. Keep the operation-specific prelude in `_run_create` / `_run_update`; single-source
only the shared write-finalization tail.

## DRY-4 (Low) -- tests duplicate mutation schema builders and in-band error assertions

The new consumer-input tests introduced
`tests/mutations/test_resolvers.py::_build_item_schema_with_input_class`, which repeats most of
`tests/mutations/test_resolvers.py::_build_item_schema`: Category/Item primary declaration,
mutation `Meta` assembly, `Mutation` class wiring, finalization, and schema construction. The only
real variation is optional `input_class` / `partial_input_class`.

The same file also repeats the in-band mutation error assertion shape many times:
`res.errors is None`, payload lookup, `node is None`, first/only error field, and sometimes "row
was not written". That repetition is readable in isolation, but it makes envelope changes noisy and
increases the chance that one new regression test asserts the envelope differently from the rest.

Recommendation: extend `_build_item_schema` with optional `input_cls` and `partial_input_cls`
parameters instead of keeping a second builder. Add a tiny assertion helper such as
`assert_mutation_field_error(result, payload_key, field)` for the common in-band error envelope,
while leaving test-specific database side-effect assertions inline.

## Do not over-DRY

I would not collapse mutation `Meta` validation into the existing `DjangoType` / `FilterSet` /
`OrderSet` validators. The current duplication is mostly policy-level similarity, not identical
mechanics, and the separate mutation namespace is part of the public DRF-shaped design. The
worthwhile DRY cuts are the narrower ones above, where the same mutation concept already has
multiple implementations.
