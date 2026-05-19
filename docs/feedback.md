# Review feedback — spec-015 consumer scalar overrides

Scope: reviewed revision 3 of `docs/spec-015-consumer_overrides_scalar-0_0_6.md` against the current Relay, scalar-conversion, and override behavior.

## Findings

### H1. Relay guard timing/detection is still internally inconsistent

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:52`, `:353-403`, `:479-480`; current string-annotation behavior is accepted by Strawberry at finalization/schema-build time.

The spec now says the bad `id: int` case raises at `DjangoType.__init_subclass__` time, and the reject test explicitly asserts class-creation failure. But Decision 7 still leaves Worker 1 free to implement `relay.NodeID[...]` detection with a Phase 2.5 `cls.resolve_id_attr()` probe. That option cannot satisfy the stated class-creation contract or the proposed reject test because the guard would run during `finalize_django_types()`, not during class definition.

The recommended `typing.get_args(...)` option also needs one more constraint: it only works for already-evaluated `relay.NodeID[int]` annotations. The current package/Strawberry path accepts string annotations such as `id: "relay.NodeID[int]"` and future-annotations style declarations; a raw `get_args` check at `__init_subclass__` would treat those as non-`NodeID` and falsely reject the supported escape hatch.

Please make the contract singular:

- either require a class-creation-time helper that resolves/evaluates `id` annotations robustly enough to accept `relay.NodeID[...]` in direct and string/future-annotation forms, with tests for both;
- or move the guard, tests, and CHANGELOG wording to finalize-time if reusing Strawberry's `resolve_id_attr()` probe is preferred.

### M1. Assigned `id` fields are always rejected even when they match `Node.id`

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:52`, `:123-135`, `:353-383`.

Revision 3 still rejects any `id` assignment that is a `StrawberryField`. That includes valid Strawberry shapes such as:

`@strawberry.field def id(self) -> relay.GlobalID: ...`

That field matches the Relay interface's `id: ID!` and currently builds a valid schema. If the intent is to ban all assigned `id` overrides and require `relay.NodeID[...]` / resolver hooks instead, the spec should call that out as an intentional restriction and add a regression test for the rejection. If the goal is only to prevent interface type mismatch, the guard should inspect assigned-field type enough to allow `relay.GlobalID` / `ID`-compatible assignments.

### M2. The pseudocode misses `id` annotations whose value is `None`

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:363-367`.

`has_id_annotation = id_annotation is not None` fails to detect `id: None`, because `cls.__annotations__["id"]` is `None`. That is still a consumer-authored `id` annotation and should follow the Relay collision guard. Use key presence (`"id" in cls.__annotations__` or `"id" in consumer_annotations`) rather than value non-`None`.

### L1. Slice 1 test count is still off

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:441`, `:462`, `:491`.

The spec says Slice 1 has nine tests, but the listed groups are 4 core override tests + 3 converter-bypass tests + 3 Relay tests = 10 tests. Update the count, or identify which listed test is not intended to be new.

### L2. The nested `ArrayField` recipe should require matching field/annotation names

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:61`.

The recipe says to build a nested `_FakeArrayField(...)` instance and use a consumer `tags: list[list[int]]` annotation. Make explicit that the model field is named `tags` too. If the model field is named `arr` like the existing converter tests, the annotation must be `arr: list[list[int]]`; otherwise the converter bypass will not fire and the test will exercise the rejection path instead.

## Notes

The previous broad-Relay-guard issue is otherwise addressed: rev3 now correctly keys the collision check to the GraphQL field name `id`, preserves non-`id` scalar overrides on Relay-node-shaped types, and keeps the converter-bypass contract explicit.
