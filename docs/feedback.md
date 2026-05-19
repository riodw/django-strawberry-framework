# Review feedback - spec-015 consumer scalar overrides

Scope: reviewed revision 6 of `docs/spec-015-consumer_overrides_scalar-0_0_6.md` against the current `DjangoType` pipeline and Strawberry Relay `NodeID` behavior.

## Findings

### H1. The fail-soft string `NodeID` accept path is not end-to-end accepted

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:72`, `:88`, `:490-538`, `:564-572`, `:664`.

Revision 6 says the fail-soft branch accepts unresolved string annotations that contain `"NodeID["`, and the coverage section says `test_consumer_id_string_relay_nodeid_annotation_on_relay_node_type_is_accepted` can hit that branch by deliberately leaving `relay` unimported at module scope.

That class can pass the new guard, but it is not a valid end-to-end accepted type. Strawberry later resolves Relay annotations from the class module globals. If the module still does not expose `relay` / `NodeID`, schema construction fails with Strawberry's unresolved-field/type-resolution error. In other words, the proposed fail-soft acceptance only suppresses the package `ConfigurationError`; it does not make the annotation resolvable for `finalize_django_types()` / `strawberry.Schema(...)`.

Split the tests/contracts:

- A resolved string-form acceptance test should keep `relay` or `strawberry` available at module scope and assert finalize/schema success.
- A fail-soft branch test may assert class-creation acceptance only, unless the implementation also normalizes `cls.__annotations__["id"]` to a resolved `relay.NodeID[...]` object before Strawberry sees it.

Also tighten the raw-string predicate if it remains: a plain substring check accepts typo shapes like `"NotNodeID[int]"`. Prefer a token-shaped check such as `(^|\.)NodeID\[` or an explicit normalization path.

### M1. The inherited `id: int` edge case expects the wrong downstream behavior

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:37`, `:91`, `:109`, `:185-187`, `:625`, `:651-660`, `:670`.

The spec says an inherited `id: int` annotation on a no-`Meta` base `DjangoType` subclass slips past the guard and then raises Strawberry's `ValueError` at schema construction because `Node.id` collides with `Int!`.

That does not match the current pipeline. A base like:

`class BaseWithId(DjangoType): id: int`

followed by a child `DjangoType` with `Meta.interfaces = (relay.Node,)` does not leave an `id: int` field on the child GraphQL type. `_build_annotations` suppresses the child's pk annotation for Relay, Strawberry supplies `id: ID!`, and `resolve_id_attr()` falls back to `"pk"` because the inherited `id: int` is not a `NodeID` marker. Schema construction succeeds.

Update the inherited-id test and every doc sentence around it. Either drop the test, or invert it to pin the real contract: inherited non-`NodeID` `id` annotations on a no-`Meta` base are ignored by the guard and do not create a schema collision. If the intended behavior is actually to reject inherited non-`NodeID` `id` annotations, the spec needs a different implementation contract that explicitly walks the MRO.

### M2. The sibling-field workaround examples need a resolver

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:34`, `:70-71`, `:109`, `:160-166`, `:413`, `:441-456`, `:677`.

The assigned-`id` rejection message and docs point consumers to a sibling field like:

`display_id: ID = strawberry.field(description="...")`

That attaches metadata, but it does not define a value source. Since `display_id` is not a Django model field, Strawberry's default resolver will look for a `display_id` attribute on the returned model instance and fail at query time unless the consumer also supplies a resolver or property.

Make the workaround explicit as a resolver-backed sibling, for example `@strawberry.field(description="...") def display_id(self) -> strawberry.ID: ...`, or `display_id: strawberry.ID = strawberry.field(resolver=..., description="...")`. The error-message example should not point at a field shape that is likely to build but fail when queried.

### L1. The choice-enum edge-case note still points at the single-type test

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:626`.

The edge-case bullet describes the new two-type enum-cache behavior, but its final sentence says the grouped-choices bypass test pins it. Revision 6 added `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` for that exact scenario. Update the sentence to name the cross-type cache test as the behavior pin.
