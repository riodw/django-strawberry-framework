# Review feedback — spec-015 consumer scalar overrides

Scope: reviewed the updated `docs/spec-015-consumer_overrides_scalar-0_0_6.md` against the current `DjangoType` collection/finalization path, Relay tests, and scalar converter behavior.

## Findings

### H1. The proposed Relay guard rejects the advertised `relay.NodeID[...]` escape hatch

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:45`, `:338-357`, `:365`, `:414`; existing `relay.NodeID` coverage in `tests/types/test_relay_interfaces.py:240` and `:994`.

Revision 2 correctly moves the bad `id: int` case to an early package-owned `ConfigurationError`, but the specified predicate is too broad:

`pk_name in consumer_annotated_scalar_fields or pk_name in consumer_assigned_scalar_fields`

For the common `id` primary key, `id: relay.NodeID[int]` is also an annotation on the scalar pk field, so it lands in `consumer_annotated_scalar_fields` and would be rejected by the new guard. That directly contradicts the error message and Decision 7, which tell consumers to use `relay.NodeID[...]` as the supported escape hatch. Current behavior accepts this shape: `id: relay.NodeID[int]` finalizes and builds a schema with `id: ID!`.

The guard also rejects custom-named primary keys that do not collide with `Node.id`. A model with `code = models.CharField(primary_key=True)` and a consumer override `code: str` can coexist with the Relay interface because the GraphQL fields are `id: ID!` and `code: String!`; there is no interface field collision.

Suggested contract:

- reject only consumer-authored fields whose GraphQL/Python name is `id` on a Relay-node-shaped type, unless the annotation is a valid `relay.NodeID[...]`;
- keep `id: relay.NodeID[...]` accepted, with an explicit regression test;
- keep non-`id` primary-key overrides accepted unless there is a separate reason to ban them, and document that separately if so.

### M1. The unsupported-field override test suggests `bytes`, which Strawberry cannot schema-build

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:52`.

The test proposal says to use `myfield: bytes` "or similar" for an unsupported Django field override. Strawberry rejects `bytes` as an unexpected type during schema construction, so that example can create a false failure unrelated to the converter-bypass contract.

Use a Strawberry-supported scalar annotation such as `str` or `int` for this test. That keeps the assertion focused on "Django converter was bypassed" rather than "consumer picked a GraphQL-unsupported Python type."

### M2. The nested `ArrayField` bypass test needs an explicit fake-sentinel setup

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:54`; existing pattern in `tests/types/test_converters.py:1021`.

The spec asks for an `ArrayField(base_field=ArrayField(...))` override test in `tests/types/test_definition_order.py`, but the current converter tests exercise this path by monkeypatching `django_strawberry_framework.types.converters._ARRAY_FIELD_CLS` to a local `_FakeArrayField`. Without that instruction, the new test can become environment-dependent on whether real `django.contrib.postgres.fields.ArrayField` imports cleanly.

Add the fixture/monkeypatch requirement to the spec, or place this one test in `tests/types/test_converters.py` beside the existing fake `ArrayField` tests.

### L1. Several revision-2 cross-references and counts are stale

References:

- `docs/spec-015-consumer_overrides_scalar-0_0_6.md:4` still says revision 1.
- `docs/spec-015-consumer_overrides_scalar-0_0_6.md:24`, `:31`, and `:33` refer to Slice 6, but the checklist has Slice 5 as docs/KANBAN/CHANGELOG.
- `docs/spec-015-consumer_overrides_scalar-0_0_6.md:27` says the card adds no new error sites, but Revision 2 adds a `ConfigurationError` site for Relay collision.
- `docs/spec-015-consumer_overrides_scalar-0_0_6.md:403` still says Slice 1 has 4 tests and `+30/-1`, while the updated plan has 8 tests plus a new guard.
- `docs/spec-015-consumer_overrides_scalar-0_0_6.md:409` still estimates `~80` total added lines despite the expanded test and guard scope.

These are not design blockers, but they will mislead Worker 1 during planning and closeout.

## Notes

The revision fixed the previous converter-bypass ambiguity well: Decision 7a now explicitly says scalar annotation overrides bypass `convert_scalar` validation and side effects, and the docs/CHANGELOG tasks reflect that behavior.
