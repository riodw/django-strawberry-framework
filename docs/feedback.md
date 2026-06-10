# Review - spec-032 Full Relay build plan

Reviewed `docs/spec-032-full_relay-0_0_9.md` against the current package source,
the shipped `spec-030` / `spec-031` contracts, and the locked Strawberry relay
behavior. The document is mostly internally coherent, but I found three contract
issues worth fixing before implementation starts.

## Findings

### P1 - Stale `after` cursor behavior is false for Strawberry offset cursors

`docs/spec-032-full_relay-0_0_9.md::Decision 9` and the Test plan require
`test_stale_after_cursor_falls_through`, described as: an `after` cursor whose
row was deleted "falls through to the next existing row, no error."

That is not the behavior of the delegated cursor engine this same decision says
we keep. In the locked Strawberry source,
`.venv/lib/python3.14/site-packages/strawberry/relay/utils.py::SliceMetadata.from_arguments`
decodes `after` and sets `start = int(after_parsed) + 1`. The cursor encodes an
offset, not a row identity. If the row at or before that offset disappears
between page requests, the next query starts from the numeric offset in the new
sequence and can skip or duplicate rows. `spec-030` already corrected this exact
claim in its Revision 2 / Edge cases language: offset-cursor queries should not
error, but stability under inserts/deletes is not guaranteed until stable
column-keyed cursors land.

Fix the spec to match `spec-030`: keep a no-error test for stale-looking cursors
if useful, but do not assert "next existing row" or "falls through" semantics.
The conformance suite should pin the guaranteed behavior of opaque offset
cursors, not a keyset-cursor property the implementation deliberately defers.

### P2 - `testing.relay` round-trip test is wrong for secondary model-label emitters

`docs/spec-032-full_relay-0_0_9.md::Decision 10` says
`global_id_for(type_cls, id)` returns the id a finalized type emits. The Edge
cases correctly note that a model-label id for a secondary type decodes through
the model primary, not back to the secondary. But the Slice 5 test plan says
`decode_global_id(global_id_for(T, pk)) == (T, str(pk))` for the decodable
strategies.

Those cannot both be true. For a secondary Relay type using `model` or
`type+model`, `global_id_for(SecondaryType, pk)` should emit the same
`app_label.modelname:<pk>` payload the live type emits, and
`decode_global_id(...)` must resolve that payload via `registry.get(model)` to
the primary type. Expecting `(SecondaryType, pk)` would either fail the test or
pressure the helper into minting an id the type does not actually emit.

Tighten the helper contract/tests: round-trip to `(T, pk)` only for lone/primary
model-label types and for type-name payloads. Add an explicit secondary
model-label case asserting decode returns the primary, or state that
`global_id_for` rejects secondary model-label emitters if that is the intended
public helper boundary.

### P2 - Root-field nullability contract contradicts itself

The Slice 2 checklist and DoD say `DjangoNodeField` / `DjangoNodesField` return
`null` for hidden and missing rows through one shared `resolve_node(s)` path.
`docs/spec-032-full_relay-0_0_9.md::Decision 5` repeats that visibility /
existence failures become `null` for bare and typed forms. But the User-facing
API section also says a non-optional annotation renders `Node!` and "a missing
row then surfaces the model's `DoesNotExist` as a GraphQL error."

That latter sentence only holds if the root resolver inspects the field's final
nullability and calls the shipped `resolve_node(..., required=True)` /
`resolve_nodes(..., required=True)` path. The rest of the spec describes an
always-null-on-missing contract. If the resolver always uses `required=False`,
a non-null annotation would surface as Strawberry's generic non-null violation,
not the model's `DoesNotExist`.

Pick one contract and make the implementation plan/test names match it. The
lower-risk choice is to keep the Relay root fields nullable-by-contract and
delete the `DoesNotExist` promise, because the spec already centers the
no-existence-oracle `null` path. If annotation-sensitive `required=True` is
intentional, add it as source work and cover both singular and batch item
nullability explicitly.

## Checks run

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md`
  -> `OK: 38 terms`.
- Inspected the locked Strawberry relay offset implementation via `uv run
  python`; no pytest run per repo instructions.
