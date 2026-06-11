# Review - spec-032 implementation in `django_strawberry_framework/`

Scope: package implementation in `django_strawberry_framework/` for
`docs/spec-032-full_relay-0_0_9.md`, reviewed against the committed `HEAD`
implementation. I did not run pytest. I did run four focused `uv run python -c`
probes to verify the lifecycle and async edge cases below.

## Findings

### P1 - Partial-finalize recovery reattaches suppressed list fields for `"connection"` relations

`django_strawberry_framework/types/finalizer.py::_synthesize_relation_connections`
removes the original relation annotation and resolver for
`Meta.relation_shapes = {"items": "connection"}` after attaching
`items_connection`. That is correct on the first pass. The recovery path is not:
if a later Phase 2.5 step fails after synthesis, a retry re-enters
`finalize_django_types()`, runs
`django_strawberry_framework/types/resolvers.py::_attach_relation_resolvers` again,
and reattaches the original `items` Strawberry field. Then synthesis sees the
existing `items_connection` marker and `continue`s before re-removing `items`.

I reproduced this with a post-synthesis orphan `filter_input_type` failure:
after the first failure, `items` was absent and `items_connection` was attached;
after wiring the orphan and retrying, schema construction failed with
`CategoryType fields cannot be resolved. Unexpected type 'typing.Any'` because
the retry reattached an unannotated `items` resolver. This is exactly the
partial-finalize recovery contract the marker is meant to preserve, but it only
works for the default `"both"` shape covered by
`tests/test_relay_connection.py::test_synthesis_skips_already_attached_on_refinalize`.

Preferred fix: make Phase 2 skip relation resolvers that are explicitly
connection-only, e.g. pass
`consumer_assigned_relation_fields | explicit_connection_only_relation_names` into
`_attach_relation_resolvers`, and keep a defensive removal in the marker path for
`shape == "connection"`. Add a retry test for `relation_shapes={"items":
"connection"}` that fails after synthesis and asserts the final SDL has
`itemsConnection` and no `items` field.

### P1 - `DjangoNodesField` async branch breaks synchronous consumer `resolve_nodes` overrides

`django_strawberry_framework/relay.py::DjangoNodesField` unconditionally awaits
each `resolved_type.resolve_nodes(...)` call inside its async gathering coroutine.
That is true for the framework default, because
`django_strawberry_framework/types/relay.py::_resolve_nodes_default` returns a
coroutine when `in_async_context()` is true. It is not true for a valid consumer
override that is synchronous and returns a list.

I reproduced this with a Relay-shaped `DjangoType` declaring a synchronous
`@classmethod resolve_nodes`; `await schema.execute(...)` failed with
`TypeError: 'list' object can't be awaited` from
`django_strawberry_framework/relay.py::DjangoNodesField`. The single-node field
does not have this problem because it passes `resolve_node`'s
awaitable-or-value return through to Strawberry's executor.

Fix: treat `resolve_nodes` as `AwaitableOrValue` in the batch gatherer. Call it,
then await only if `inspect.isawaitable(result)` or use Strawberry's
`await_maybe` helper. Add an async `DjangoNodesField` test with a synchronous
consumer `resolve_nodes` override.

### P2 - `global_id_for` mints ids for strategy-stamped but unfinalized types

`django_strawberry_framework/testing/relay.py::global_id_for` checks
`definition.finalized` only when `definition.effective_globalid_strategy is None`.
But `django_strawberry_framework/types/relay.py::install_globalid_typename_resolver`
stamps `effective_globalid_strategy` before Phase 3 marks the definition
finalized. A Phase 3 failure leaves `definition.finalized == False` with a
non-`None` strategy, and `global_id_for` then returns an id despite its documented
"finalized Relay-Node-shaped type" contract.

I reproduced this by patching `strawberry.type` to raise during Phase 3. After
the failed finalization, the definition had `finalized=False` and
`effective_globalid_strategy="model"`, and `global_id_for(CategoryNode, 1)`
returned a model-label GlobalID instead of the finalize-first
`ConfigurationError`.

Fix: check `if not definition.finalized` before reading or trusting
`effective_globalid_strategy`. Add a partial-finalize failure test for a
Relay-shaped type where the strategy stamp exists but Phase 3 did not complete.

### P3 - Unhashable `Meta.relation_shapes` values leak `TypeError`

`django_strawberry_framework/types/base.py::_validate_relation_shapes` validates a
shape with `if shape not in RELATION_SHAPE_VALUES`. For hashable invalid values
this raises the intended `ConfigurationError`; for an unhashable invalid value
such as `{"items": ["both"]}`, Python raises `TypeError: cannot use 'list' as a
set element` before the package can produce its configured diagnostic.

I verified that exact `TypeError` with a small type-declaration probe. The spec
and the existing validation matrix promise a `ConfigurationError` for values
outside `{"list", "connection", "both"}`.

Fix: validate `isinstance(shape, str)` before set membership, or compare through
a tuple/list membership that cannot raise for unhashable inputs. Add a matrix row
for an unhashable bad value.

## Notes

The major root-field contracts from the prior review are implemented correctly:
raw `strawberry.ID` arguments let malformed ids reach package decode,
`GLOBALID_INVALID` conversion is scoped to decode, and uncoercible pk literals
become nulls rather than ORM errors. The always-concrete connection type change
also matches the intended guard against Strawberry dropping the package
`resolve_connection` override.
