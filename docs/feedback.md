# Review feedback — spec-015 consumer scalar overrides

Scope: reviewed revision 4 of `docs/spec-015-consumer_overrides_scalar-0_0_6.md` against the current `DjangoType`, Relay, and converter behavior.

## Findings

### M1. Fail-soft `NodeID` detection leaves a broad escape hatch for invalid `id` annotations

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:60`, `:428-439`, `:469-471`.

Revision 4 correctly pins the Relay collision guard to class-creation time and switches to `typing.get_type_hints(..., include_extras=True)` for stringified `relay.NodeID[...]`. The remaining issue is the fail-soft rule: on `NameError` / `AttributeError`, `_id_annotation_is_relay_node_id()` returns `True`.

That accepts any unresolved string annotation on `id`, including non-NodeID shapes such as `id: "SomeMissingType"`. The spec then no longer guarantees that non-`NodeID` `id` annotations are caught at `__init_subclass__`; those cases fall back to Strawberry/schema-construction errors, which is the failure surface this guard was introduced to avoid.

Narrow the fail-soft path. For example: inspect the raw `cls.__annotations__["id"]` string first and only fail-soft accept unresolved strings that syntactically look like a `NodeID[...]` reference (`"relay.NodeID["`, `"NodeID["`, or whatever imports the spec wants to support). For other unresolved strings, raise the package `ConfigurationError`.

Add a reject test for an unresolved non-NodeID string, e.g. `id: "MissingType"`, so this contract stays pinned.

### L1. Decision-7 anchors still say `rev3 narrowed`

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:40`, `:60`, `:347`, `:522`, `:547`.

The Decision 7 title/link target still uses `h1-fix-rev3-narrowed`, even though revision 4 substantially changed the contract: class-creation-only detection, stringified `NodeID` support, and assigned-`id` rejection. This is a stale anchor/name issue, but it will make the spec harder to follow during implementation and closeout.

Rename the Decision 7 heading and all internal links to a rev4-neutral anchor such as `decision-7--relay-id-override-collision`.

### L2. The "100% coverage across test_definition_order.py" note conflicts with optional converter placement

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:155`, `:530`, `:563`.

The KANBAN body still says coverage is across `tests/types/test_definition_order.py`, but revision 4 explicitly allows the nested-`ArrayField` bypass test to live in `tests/types/test_converters.py`. The definition-of-done also says "three converter-bypass in `tests/types/test_definition_order.py`" before noting the `ArrayField` exception.

Adjust the wording to "across the override-contract host and converter tests as applicable" or name both files consistently.

## Notes

The prior blockers are otherwise addressed: the guard is now keyed to GraphQL `id`, direct and stringified `relay.NodeID[...]` are explicitly accepted, assigned `id` rejection is intentional and tested, and the converter-bypass contract is clear.
