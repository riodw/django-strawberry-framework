# Review feedback — spec-015 consumer scalar overrides

Scope: reviewed `docs/spec-015-consumer_overrides_scalar-0_0_6.md` against the current `DjangoType` collection/finalization path, scalar converter behavior, and the existing tests.

## Findings

### H1. Relay `id` override edge case names the wrong failure phase and exception

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:316`, `django_strawberry_framework/types/base.py:643-657`, `django_strawberry_framework/types/finalizer.py:156-165`.

The spec says a `DjangoType` with `Meta.interfaces = (relay.Node,)` and a consumer `id: int` annotation should "still raise `NodeIDAnnotationError` at finalization." That does not match the current lifecycle. With a consumer-authored `id`, `_build_annotations` hits `if field.name in consumer_authored_fields: continue` before the Relay primary-key suppression branch, so the consumer `id: int` remains on `cls.__annotations__`. Finalization itself succeeds; building `strawberry.Schema(...)` then fails with Strawberry's schema validation error because `Node.id` is `ID!` but the concrete type's `id` field is `Int!`.

The spec should choose and pin the actual intended contract:

- reject plain consumer `id` annotations on Relay-node-shaped types with a package-owned `ConfigurationError` before schema construction; or
- document and test the current downstream schema-build failure, using the actual `ValueError` phase/message rather than `NodeIDAnnotationError` at finalization.

If `relay.NodeID[...]` is the supported consumer escape hatch, the spec should say that explicitly and distinguish it from `id: int`.

### H2. The new short-circuit bypasses scalar converter validations, but the spec only covers enum caching

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:155`, `:184`, `:317`; `django_strawberry_framework/types/converters.py:95-196`; existing converter tests in `tests/types/test_converters.py`.

Adding annotation-only scalar names to `consumer_authored_fields` skips the whole scalar branch before `convert_scalar(...)` runs. That does more than prevent auto-synthesized annotations: it also bypasses every converter-side validation and side effect for that selected field, including unsupported field-type errors, grouped/empty/colliding choice validation, ArrayField/HStoreField rejection paths, null widening, and enum registration.

That may be the right consumer-authoritative contract, but the spec needs to state it directly. Today it only calls out the choice-enum cache behavior. Add a decision and mandatory tests for at least:

- annotation-only override of an otherwise unsupported scalar field, documenting whether this is now allowed;
- annotation-only override of a choice field with an invalid/generated-enum shape, documenting whether converter validation is intentionally bypassed;
- the docs update needed for `docs/FEATURES.md`'s scalar-conversion text, which currently frames unsupported scalar fields as `ConfigurationError` cases with `Meta.exclude` as the recourse.

If those converter validations are still meant to run, the implementation cannot be just the proposed `consumer_authored_fields` short-circuit; it needs a separate "validate converter shape but do not synthesize annotation/register enum" path.

### M1. The end-to-end introspection test query is not enough to assert `Int`

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:44`, `:331`; existing helper pattern at `tests/types/test_converters.py:434`.

The proposed introspection query reads `type { name }`, but `description: int` on the fakeshop `Category.description` field will be non-null in GraphQL, so the immediate `type.name` is `null`; the scalar name lives under `type.ofType.name`. The test should request `kind`, `name`, and nested `ofType` and unwrap to the terminal type, or reuse the existing `_introspect_field_type` helper shape from converter tests.

### L1. The definition-field insertion point is inconsistent

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:37`, `:247-254`; `django_strawberry_framework/types/definition.py:28-31`.

Slice 1 says to add `consumer_annotated_scalar_fields` after the existing `consumer_assigned_scalar_fields`, but Decision 3's sample places it between `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields`. Pick one order and make the checklist, sample, and tests agree. The grouped order in Decision 3 is clearer, but the spec should not leave Worker 1 to infer whether reordering the existing dataclass fields is expected.

## Notes

The core collection design is otherwise sound: collecting `consumer_annotated_scalar_fields` beside `consumer_annotated_relation_fields` and unioning it into `consumer_authored_fields` matches the existing relation path and uses the current `_build_annotations` scalar short-circuit correctly.
