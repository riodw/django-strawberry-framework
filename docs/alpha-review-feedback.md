# Review Feedback: B6 Audit Diff

## Scope reviewed

- `django_strawberry_framework/optimizer/extension.py`
- `tests/optimizer/test_extension.py`
- `docs/spec-optimizer_beyond.md`

This feedback only covers the current diff.

## Findings

### 1. `_collect_schema_reachable_types()` audits the schema type map, not true root-reachable types

Priority: P1

The new B6 helper walks `schema._schema.type_map` and treats every `GraphQLObjectType` with a `DjangoType` origin as reachable. That is broader than the contract in `spec-optimizer_beyond.md`, which says the audit should walk only types reachable from the schema's root types. In GraphQL/Strawberry, the schema type map can include extra object types that are present in the schema registry but not actually reachable from `query` / `mutation` / `subscription` roots. Auditing the whole type map will therefore produce false positives for orphan or helper types the consumer intentionally passed into the schema but does not expose.

Recommended fix:

- either do a real traversal from the root operation types, or explicitly narrow the shipped contract to “all object types in the schema type map”
- add a test with an extra `DjangoType` included in the schema but not referenced from any root field, and assert B6 ignores it

Relevant code:

- `django_strawberry_framework/optimizer/extension.py:138-164`
- `docs/spec-optimizer_beyond.md:179-181`

### 2. B6 is marked shipped, but the implementation still covers only the unregistered-target subset of the audit contract

Priority: P1

`docs/spec-optimizer_beyond.md` now marks B6 complete, and the implementation does ship a useful `check_schema(schema)` pass. But the current code only warns when an exposed relation's `related_model` has no registered `DjangoType`. The B6 contract in the same spec is broader: it says the audit should also surface relations hidden behind custom resolvers that bypass the optimizer, and the test surface still names a `check_optimizer` management command. None of that shipped in this diff. Marking B6 complete at this point makes the spec overstate the audit's current guarantees.

Recommended fix:

- either narrow the B6 prose/test surface to “unregistered-target audit” and leave the broader custom-resolver / command work for a follow-up slice, or
- keep B6 unchecked until those remaining behaviors actually land

Relevant code/spec:

- `django_strawberry_framework/optimizer/extension.py:362-396`
- `tests/optimizer/test_extension.py:848-951`
- `docs/spec-optimizer_beyond.md:177-209`
- `docs/spec-optimizer_beyond.md:320-323`

## Overall assessment

This is a good incremental B6 pass, but it is not the full B6 described in the spec yet. The core issue is boundary accuracy: the audit currently answers “which exposed relations point at unregistered target types,” while the spec now says it answers the broader “which relations have no optimization story” question.
