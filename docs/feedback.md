Spec-039 deeper review on the fakeshop live-test lane
=====================================================

Review scope: current `HEAD` (`c9eeb79e`) after the latest fixes, still judged
against `examples/fakeshop/test_query/README.md`. I reviewed the implementation
diff from `1f7e5d70..HEAD`, the new library serializer mutations, the live
`test_library_api.py` additions, and the remaining package-only tests.

Overall assessment: the implementation bug from the prior review is fixed. A
targeted local probe that previously failed now finalizes successfully with a
descriptor-derived input name:

```text
OK BadDefaultSerNameab03d5Category3330b1Input
```

The new commit also moves part of the acceptance coverage into fakeshop live HTTP
tests, which is the right direction. The deeper issue is that the live coverage is
still not testing the exact consumer-visible failure modes that motivated the
implementation changes. The package tests are doing most of the hard proof.

Findings
--------

### High: live coverage does not exercise the same-serializer hook-shape collision

The core naming fix in this lane is for two `SerializerMutation` declarations over
the same serializer class whose `get_serializer_for_schema()` hooks return the
same field names with different field specs, especially different relation target
models. That is the bug that previously materialized two distinct input classes
under one canonical `<Serializer>Input` name.

The current live fakeshop additions include only one schema-hook serializer
mutation:

- `examples/fakeshop/apps/library/schema.py::CreateShelfViaSchemaHookSerializer`
- `examples/fakeshop/test_query/test_library_api.py::test_create_shelf_via_schema_hook_serializer_executes_over_http`

That proves a hook-backed serializer can execute over HTTP, but it does not prove
the same-serializer/different-hook-shape collision is fixed in the real project
schema. The actual collision case remains package-only:

- `tests/rest_framework/test_sets.py::test_hook_varied_relation_targets_bind_to_distinct_input_names`

Under the README's coverage rule, this is still live-reachable. The fakeshop
schema can declare two live serializer mutations over one serializer class, with
two hook field maps that expose the same `target` field but point it at different
models, then hit both mutations through `/graphql/`. That would exercise the
materialization ledger, descriptor-derived names, and runtime reverse map in the
same stack users run.

Required correction: add a fakeshop live pair that reproduces the collision shape
inside the project schema. The test should assert schema import succeeds, both
mutation fields execute over HTTP, and the two generated input types are distinct
via introspection or by successful variable-typed calls if the names are stable
enough to reference.

### High: unsupported-default-field schema-hook recovery is only package-tested

The implementation now correctly treats failures while constructing the default
full shape as "no canonical default shape" instead of rejecting a valid hook map:

- `django_strawberry_framework/rest_framework/inputs.py::_default_full_shape_identity`

I verified the old failure mode locally with a serializer whose default no-arg
field map contains a writable `SlugRelatedField`, while the schema hook returns a
supported `PrimaryKeyRelatedField` replacement. It now finalizes successfully.

However, the regression is only covered in package tests:

- `tests/rest_framework/test_inputs.py::test_unsupported_default_field_does_not_reject_supported_hook_map`

The new live hook serializer,
`examples/fakeshop/apps/library/serializers.py::TenantShelfSerializer`, covers a
different default failure mode: construction requires a `tenant` kwarg, so default
schema discovery fails before field conversion. It does not cover the deeper case
where default discovery succeeds but default field conversion is unsupported and
the hook supplies a valid schema map.

That path is also live-reachable under the README rule. A fakeshop serializer can
declare an unsupported default field and a mutation hook can replace it with a
supported field map, then a real `/graphql/` mutation can prove the hook map is
used for both schema and runtime.

Required correction: add a live fakeshop serializer mutation for the
unsupported-default-field recovery case, or extend the new live hook serializer so
its default no-arg field map succeeds but contains an unsupported default field
that the hook replaces.

### Medium: serializer relation visibility is still not pinned live

The new live serializer mutations all create shelves with visible branches. The
library app already has live hidden-branch coverage for model and form mutations,
because `BranchType.get_queryset` hides `city="restricted"` from anonymous users:

- `examples/fakeshop/test_query/test_library_api.py::test_create_shelf_via_form_hidden_branch_fk_is_relation_field_error`
- `examples/fakeshop/test_query/test_library_api.py::test_create_shelf_model_mutation_hidden_branch_is_field_error`

The serializer resolver has its own relation decode path:

- `django_strawberry_framework/rest_framework/resolvers.py::_decode_serializer_data`
- `django_strawberry_framework/rest_framework/resolvers.py::_decode_relation_single`

It is consumer-visible and reachable through the newly added
`createShelfViaSerializer` / `createShelfViaSchemaHookSerializer` mutations, but
there is no equivalent live assertion that a hidden raw-pk `branchId` is rejected
with a `FieldError` and no write. Package tests cover pieces of relation decode,
but the README rule says this should be earned through `/graphql/` when possible.

Required correction: add a live serializer mutation test that posts a restricted
branch pk as `branchId` anonymously and asserts the payload has `result: null`,
the error field is `branchId`, and no `Shelf` row is created. Prefer using the
schema-hook mutation too, so the test covers hook-generated input plus serializer
relation visibility in one request.

Resolved items verified
-----------------------

- `_default_full_shape_identity` now catches conversion-time `ConfigurationError`
  while building the default identity, so a valid hook map is not rejected by an
  unsupported default field.
- The new library serializer surface is in the correct app/test tree for live
  HTTP acceptance coverage.
- `CreateShelfViaSchemaHookSerializer` proves a construction-kwarg-requiring
  serializer can execute over `/graphql/` when schema and runtime hooks agree.
- `CreateShelfViaSubclassedSerializer` proves the inherited `_mutation_meta`
  snapshot bug is covered through schema import and a live write.

Validation notes
----------------

I ran one targeted `uv run python` probe for the previously failing unsupported
default-field hook case. I did not run pytest because the repository instructions
say not to run pytest unless explicitly asked.
