# Review: `django_strawberry_framework/relay.py`

Status: verified

## Understanding

`relay.py` owns the public root `DjangoNodeField` and `DjangoNodesField` factories. Each resolver
decodes the raw `ID` argument through `types/relay.py::decode_global_id`, validates the typed target
when present, coerces the decoded `NodeID` against the same field used by node lookup, and dispatches
to the decoded type's `resolve_node` / `resolve_nodes` with `required=False`. The single-node field
returns `None` for hidden, missing, or uncoercible rows; the batch field groups by decoded type,
preserves input order and duplicates, and inserts positional `None` holes. Decode failures are
converted to `GraphQLError` with `GLOBALID_INVALID`; decode happens before ORM access, so malformed
payloads cannot probe row existence.

`types/relay.py` owns encoding/decoding strategy semantics, the resolver defaults, visibility
queryset application, composite-primary-key gating, and the `is_type_of` hint used to disambiguate
two Relay types over one model. `registry.py` supplies primary/model and GraphQL-name routing;
`types/finalizer.py` stamps strategies and installs the defaults before Strawberry schema
construction. `connection.py` consumes the same finalized Relay types and resolver defaults for
cursor edges, nested relation connections, and optimizer windows. The fakeshop library schema
exposes bare `node` / `nodes` plus typed `genre`; live tests exercise model-label round trips,
wrong-type errors, malformed IDs, hidden rows, mixed-type batches, duplicates, and empty batches.

## Verification

- The assigned scoped baseline is byte-identical for the target:
  `git --no-pager diff f133ada4bb8a781d7da35d7a6be77281c3205e55 -- django_strawberry_framework/relay.py`.
- Before editing, focused package tests passed:
  `uv run pytest tests/test_relay_node_field.py tests/testing/test_relay.py --no-cov -q` — 53 passed.
- Focused Relay resolver lifecycle tests passed before editing:
  `uv run pytest tests/types/test_relay_interfaces.py -k 'resolve_node or resolve_nodes or async_get_queryset or composite_pk or relay_chain' --no-cov -q` — 28 passed.
- Focused connection/cursor integration tests passed before editing:
  `uv run pytest tests/test_relay_connection.py -k 'cursor or visibility or pagination or total_count' --no-cov -q` — 11 passed.
- Live fakeshop refetch tests passed before editing:
  `uv run pytest examples/fakeshop/test_query/test_library_api.py -k 'node_refetch_genre or typed_node_field_live or typed_node_field_mismatch_live or node_malformed_id_live or node_uncoercible_pk_live or nodes_batch_mixed_types_order_and_null or nodes_duplicates_and_empty_live or node_hidden_row_null_live' --no-cov -q` — 8 passed.
- Disposable reproduction in `docs/review/temp-tests/relay/test_hint_persistence.py` first failed with
  `Expected value of type 'PrimaryNode' but got: <Category instance>` when one ORM instance was
  reused by a secondary `node(id:)` result and a later concrete primary field. A control query using
  the concrete field alone passed, proving the failure came from the persisted routing hint rather
  than the fixture or schema declaration.

## Improvements

### High

None.

### Medium

- **Relay type-routing hints leaked through reused ORM instances.**
  - **Observation:** `relay.py::_stamp_node_type` attached `_NODE_TYPE_HINT_ATTR` directly to the
    fetched Django model instance. The hint is required to route a bare abstract `node` result
    when multiple Relay `DjangoType`s share one model, but it remained on the object after field
    completion.
  - **Evidence:** The disposable schema registered `PrimaryNode` and `SecondaryNode` over
    `Category`. `SecondaryNode.resolve_node` returned one shared `Category` instance; the query
    then returned that same instance from a concrete `PrimaryNode` field. Before the fix, the
    first field stamped `SecondaryNode`, and Strawberry's `PrimaryNode.is_type_of` rejected the
    reused object. The concrete field succeeds when queried alone. The existing multi-type
    node/nodes tests did not reuse an object across field boundaries.
  - **Impact:** A consumer resolver or cache that reuses a model instance could receive a
    type-resolution error, or could get a stale concrete type if the reused object flowed through
    another abstract field. This makes node refetch behavior depend on prior resolver execution and
    leaks framework routing state into consumer-owned ORM objects.
  - **Recommendation:** Keep the hint scoped to the result object owned by the refetch field. When
    the result is a model instance, shallow-copy it before attaching the hint; preserve the existing
    best-effort behavior for non-model/custom objects that cannot be copied or stamped. The
    ownership fix belongs at `relay.py::_stamp_node_type`, where the hint is introduced.
  - **Proof:** `tests/test_relay_node_field.py::test_node_type_hint_does_not_poison_reused_model_instance`
    executes the real Strawberry schema with the reproduced shared-instance sequence and asserts
    both the secondary `__typename` and the later primary field. The test fails against the
    pre-fix direct mutation and passes after copying.

### Low

None.

## Summary

Relay ID decoding, strategy-aware primary/secondary routing, typed mismatch handling, visibility
nullability, malformed-ID errors, composite-primary-key restrictions, sync/async dispatch, batch
ordering, duplicate handling, cursor integration, resource-policy deadline hooks, and registry
finalization coupling matched their documented contracts. One medium state-isolation defect was
confirmed in the concrete-type hint bridge and fixed at its ownership boundary; no additional
source change was justified.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/relay.py::_stamp_node_type` to shallow-copy model-backed
  results before attaching `_NODE_TYPE_HINT_ATTR`. Non-model returns retain the prior best-effort
  stamp/fallback behavior; copy failures leave the original untouched rather than mutating a
  consumer-owned object.
- Added
  `tests/test_relay_node_field.py::test_node_type_hint_does_not_poison_reused_model_instance`,
  pinning multi-type abstract routing followed by reuse of the same ORM instance in a concrete
  field.
- Scratch verification:
  `uv run pytest docs/review/temp-tests/relay/test_hint_persistence.py --no-cov -q` — 1 passed
  after the fix; the pre-fix run reproduced the concrete-type error.
- Focused post-edit verification:
  `uv run pytest tests/test_relay_node_field.py tests/testing/test_relay.py --no-cov -q` — 54 passed;
  `uv run pytest tests/types/test_relay_interfaces.py -k 'resolve_node or resolve_nodes or async_get_queryset or composite_pk or relay_chain' --no-cov -q` — 28 passed;
  `uv run pytest tests/test_relay_connection.py -k 'cursor or visibility or pagination or total_count' --no-cov -q` — 11 passed; live fakeshop node subset — 8 passed.
- `uv run ruff format .` and `uv run ruff check --fix .` — passed.
- Rejected findings: no additional issue was reproduced in malformed/invalid IDs, hidden-vs-missing
  null behavior, wrong-type routing, strategy/primary audits, custom `NodeID` coercion, composite
  primary-key gates, sync/async resolver dispatch, registry clearing/finalization, or
  offset/keyset connection paths. Existing focused and live tests cover those boundaries.
- Changelog: no entry requested; this is a bounded alpha state-isolation correction.

## Independent verification (Worker 2)

- Confirmed the assigned baseline diff is limited to the reported `_stamp_node_type` ownership fix
  in `django_strawberry_framework/relay.py`: model-backed resolver results are shallow-copied
  before `_NODE_TYPE_HINT_ATTR` is attached; `None` and non-model best-effort returns retain their
  prior behavior. No source or permanent test edits were made by this verification.
- Re-traced the complete route: `DjangoNodeField` / `DjangoNodesField` decode and validate before
  ORM access, coerce against the finalized Relay type's resolution field, dispatch consumer
  `resolve_node` / `resolve_nodes`, and stamp sync or awaited results. `types/relay.py` supplies
  strategy-aware GlobalID decode, primary/model routing, visibility-filtered sync/async defaults,
  composite-primary-key gates, and `is_type_of`; finalization snapshots strategies and audits
  model-label routing; registry clearing resets the node-field ledger and strategy snapshot.
  Connection cursor/edge paths consume the same finalized node types and were checked for
  visibility, pagination, and total-count interactions.
- Focused verification passed:
  `uv run pytest tests/test_relay_node_field.py tests/testing/test_relay.py --no-cov -q` (54);
  `uv run pytest tests/types/test_relay_interfaces.py -k 'resolve_node or resolve_nodes or async_get_queryset or composite_pk or relay_chain' --no-cov -q` (28);
  `uv run pytest tests/test_relay_connection.py -k 'cursor or visibility or pagination or total_count' --no-cov -q` (11);
  live fakeshop node subset in `examples/fakeshop/test_query/test_library_api.py` (8);
  `uv run pytest docs/review/temp-tests/relay/test_hint_persistence.py --no-cov -q` (1).
- Independently forced the pre-fix behavior in disposable
  `docs/review/temp-tests/relay/test_hint_without_copy.py` by making `copy.copy` return the
  original object; the permanent reused-instance regression then produced the expected stale
  `PrimaryNode` type-resolution failure. The fixed path passed the same scenario and left the
  original ORM row unstamped. `test_hint_copy_state.py` additionally confirmed the copied
  `Category` retains class, primary key, database state, and original field dictionary.
- Rechecked malformed and composite/invalid IDs, primary/secondary strategy routing, typed mismatch
  errors, hidden-vs-missing null equivalence, batch ordering/duplicates/empty inputs, sync/async
  overrides, registry/finalizer coupling, and offset/keyset connection behavior through the
  focused and live suites. No residual finding or unrelated target change was found.
