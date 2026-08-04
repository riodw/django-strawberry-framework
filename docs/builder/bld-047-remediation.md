# bld-047 remediation — deferred / decision catalog

Scratchpad for the card-047 resource-policy remediation cycle (raw `path:NN` refs allowed
here). Everything below is something deliberately NOT done, or a decision worth stating once
so the next reader does not re-litigate it.

## Deliberately not done

1. **No WebSocket pre-parse scan and no package-owned subscription error envelope.**
   Verified against the installed Strawberry: `schema.py::_subscribe` enters
   `extensions_runner.operation()` and `executing()`, so both the text scan and the walk DO
   run for a subscription — the gap is in RENDERING, not enforcement. `execute` wraps its
   operation block in `try / except Exception -> PreExecutionError`, so HTTP and WS
   queries/mutations get an `errors` entry; `_subscribe` has no such wrapper, and
   `subscriptions/protocols/graphql_transport_ws/handlers.py::BaseGraphQLTransportWSHandler.run_operation`
   catches the escaping exception, logs it, and sends `complete`. Fixing that means owning an
   error envelope for a transport whose lifecycle is upstream's. Out of scope; the prose in
   `resource_policy.py` (`RESOURCE_LIMIT_ERROR_CODE`), the extension module docstring, and
   spec Decision 11 now state the boundary instead of claiming parity.

2. **No transport-level upload charging.** Django's upload handlers have already streamed a
   multipart body by the time coerced values exist. Charging earlier means a package-owned
   upload handler / streaming body reader, which is a transport card. Spec Goal 2 is narrowed
   to "post-materialization, before any resolver, serializer, validator or storage backend
   touches the files".

3. **No package-configured bound on numeric literal size.** CPython's
   `sys.get_int_max_str_digits` (4,300) raises during JSON parsing or graphql-core's literal
   coercion, so the request is refused — but as a malformed-input failure, not a typed
   resource rejection. Adding one would mean a pre-coercion scan of the raw variables JSON,
   which duplicates the body cap's layer. Documented in `_charge_leaf` and in the spec's edge
   cases rather than promised.

4. **`utils/connections.py` gets no `check_deadline` call.** Audited every function in it
   (`connection_sidecar_inputs_from_kwargs`, `window_range_plan`, `split_window_rows`,
   `derive_connection_window_bounds`, `resolve_relay_max_results`, `derive_keyset_window_bounds`,
   and the assert helpers): all pure window arithmetic, no database access.
   `resolve_relay_max_results` is also called at PLAN time, where a deadline check would fire
   outside a resolve and against a plan-time `info`, so it is explicitly the wrong seam.

5. **`forms/resolvers.py::_run_plain_form_pipeline_sync` gets no deadline check.** The
   model-less plain-form flavor has no locate, no relation decode and no model write — no
   database seam to guard. The three model-backed flavors all enter
   `run_write_pipeline_sync`, which has one.

6. **`_charge_container`'s per-reference charging is not memoized at all.** A diamond-shaped
   value (one container referenced from many places) is charged once per reference, which is
   the corrected contract. The cost is bounded by `max_input_nodes`, since every reference
   pops a stack entry and charges a node before it descends — a value engineered to blow the
   walk up runs out of node budget first. No separate work bound was added for it.

7. **Spec checkboxes, `KANBAN`, `GLOSSARY` and the glossary DB untouched**, per the task
   scope. The new `max_value_depth` bound therefore has no glossary entry yet; the
   `ResourcePolicy` glossary body enumerates bounds and will need the fold-in when the card's
   docs slice is revisited.

## Decisions worth stating once

- **Two mechanisms, not one.** The deleted `_seen: set[int]` was doing cycle-guard duty and
  charge-once duty at the same time. They have different lifetime requirements (ancestor-scoped
  + owning vs request-scoped) and only one of them is a contract, which is why one object could
  not correctly be both. The replacement is a path tuple for termination and no cache at all
  for charging.
- **`max_value_depth` default is `20`**, matching `max_depth` — the two bound the same idea on
  the two sides of the text/variable divide, and a value nested deeper than a document may be
  is not a shape any legitimate client sends.
- **The deadline rejection reports `limit = ceil(configured seconds)` and
  `charged = limit + 1`.** This reuses the "exceeded a budget that integers cannot express"
  spelling already used for an unmeasurable upload, rather than putting a monotonic clock
  reading on the wire. The one branch where `configured is None` (a hand-written
  `dst_resource_deadline` key with no policy behind it) reports `limit = 0` and the word
  `unknown`, and still rejects — fail-closed.
- **`_is_connection_type` requires `node` AND `cursor` on the edge type.** Strawberry's
  `ListConnection` edge carries both; requiring both is what keeps the collection-cost
  exemption from being claimable by shape accident.
- **Live-tier deadline rows use `execution_deadline_seconds = 0.000_001`** rather than a sleep,
  so the deadline has always passed by resolve time and the rows are deterministic.
