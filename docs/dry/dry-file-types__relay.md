# DRY review: `django_strawberry_framework/types/relay.py`

Status: verified

## System trace

`types/relay.py` is the Relay foundation for collected `DjangoType` classes.
It owns lifecycle-phased injection and the GlobalID encode/decode contract;
callers schedule or consume it, they do not reimplement it.

| Phase / seam | What this module owns | Who calls / reads |
| --- | --- | --- |
| Class creation | `install_is_type_of` (`__dict__` membership; optional `_NODE_TYPE_HINT_ATTR`) | `types/base.py::DjangoType.__init_subclass__` |
| Annotation / Meta | (not here) `relay.Node in interfaces` / `_is_relay_shaped` | `types/base.py` — pre-injection shape |
| Phase 2.5 | `apply_interfaces`, `_check_composite_pk_for_relay_node`, `install_relay_node_resolvers`, `install_globalid_typename_resolver` | `types/finalizer.py` after `_validated_globalid_setting` snapshot |
| Post-injection predicate | `implements_relay_node` (`issubclass(..., relay.Node)`) | finalizer, registry name lookup, filters/forms/mutations/DRF bind surfaces |
| Encode | `encode_typename` + strategy frozensets / install closure | installed `resolve_typename`; `testing/relay.py::global_id_for` |
| Decode | `decode_global_id` (resolve-then-enforce → `ConfigurationError`) | package `relay.py` (wire + typed mutation decode); testing re-export |
| Payload-shape sets | `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` + thin predicates | finalizer model-label audit; `filters/base.py` accepted-name set |
| Node defaults | four `resolve_*` via `_RELAY_RESOLVER_DEFAULTS` + sync/async materialization | installed on Relay types; definition custom-id check identity-tests `_resolve_id_default` |
| SyncMisuseError | re-export alias only | true owner `utils/querysets.py`; public path via `types` / package `__init__` |

Vocabulary vs payload partition (intentional split with `types/base.py`):

- `STRING_GLOBALID_STRATEGIES` / `DEFAULT_GLOBALID_STRATEGY` / `_validate_globalid_strategy` live in `base.py` (Meta + setting validation).
- This module resolves precedence (`_resolve_globalid_strategy`), installs the encode closure, enforces decode shape, and publishes the payload-shape frozensets consumed by encode, decode, audit, and filters.

Connected surfaces read (siblings not reopened as owners): `types/finalizer.py` (Phase 2.5 schedule + `_emits_model_label` / `_accepts_model_label_decode` audit), `types/base.py` (strategy vocabulary + `install_is_type_of` call), `testing/relay.py` (`encode_typename` + `decode_global_id` re-export), package `relay.py` (`decode_global_id` + `_NODE_TYPE_HINT_ATTR` stamp), `filters/base.py` (strategy-aware filter validate, not resolve), `connection.py` / `list_field.py` / `keyset.py` (Relay-shaped factory gates via `_is_relay_shaped`, not this module's post-MRO predicate), `utils/querysets.py` (`SyncMisuseError`, visibility, `initial_queryset`, `model_for`), `types/definition.py` (`effective_globalid_strategy` stamp target; `_resolve_id_default` identity).

Item-scoped baseline `743b3f2327de3c839bf73df9cb793c34597701c0`:
`git diff 743b3f… -- django_strawberry_framework/types/relay.py` empty at review
start and after this item (proved zero-edit). Artifact path is the only
addition under this item's ownership.

## Verification

Searches: `encode_typename` / `decode_global_id` / `GlobalID.from_id`,
`MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` / `STRING_GLOBALID_STRATEGIES`,
`install_globalid` / `install_relay_node` / `install_is_type_of` /
`apply_interfaces` / `implements_relay_node`, `__func__` override tests,
`_NODE_TYPE_HINT` / `_FRAMEWORK_CLOSURE` / `_RELAY_ID_ATTR`,
`SyncMisuseError as SyncMisuseError`, `_is_relay_shaped`, filter
`_decode_and_validate_global_id`, root `decode_model_global_id`.

Executable body compare (scratch): `_emits_model_label` and
`_accepts_model_label_decode` have identical AST bodies; node sync/async pairs
and override helpers do not.

Strongest rejected candidates:

1. **`decode_global_id` vs `filters/base.py::_decode_and_validate_global_id`** —
   Both parse `GlobalID` / `from_id` and read `effective_globalid_strategy`, but
   contracts diverge: resolve-any-payload → `(type, node_id)` +
   `ConfigurationError` vs validate-against-known-filter-target → `node_id` +
   coded `GraphQLError` (mismatch / `GLOBALID_INVALID` /
   `GLOBALID_UNVALIDATABLE`). Wire node fields wrap the former; filters own the
   latter. Unifying would need mode flags for error surface and lookup axis.
   Rejected.

2. **`decode_global_id` vs package `relay.py::decode_model_global_id`** —
   Typed mutation path already delegates shape decode here, then adds
   expected-model check + pk coercion (`_coerce_pk_or_none` /
   `_resolve_real_pk`). That post-decode WRITE contract is not this module's.
   Rejected.

3. **`STRING_GLOBALID_STRATEGIES` vs `MODEL_LABEL_STRATEGIES` /
   `TYPE_NAME_STRATEGIES`** — Vocabulary (valid string strategies + default) vs
   payload-shape partitions for encode/decode/filter/audit. Overlap on
   `"type+model"` is the partition, not a hoistable duplicate.
   `filters/base.py::FRAMEWORK_GLOBALID_STRATEGIES` already derives from these
   frozensets. Rejected.

4. **`_emits_model_label` ≡ `_accepts_model_label_decode` bodies** — One
   frozenset already single-sources membership; distinct names document encode
   emission vs decode acceptance for the model-label audit / Step-2 gate.
   Collapsing to one predicate would blur the change axis the docs say to split
   if membership ever diverges. Rejected.

5. **`implements_relay_node` vs `types/base.py::_is_relay_shaped`** —
   Post-`apply_interfaces` MRO check vs pre-injection
   `Meta.interfaces` ∪ direct inheritance. Factory construction and Meta gates
   must accept Meta-only Relay before Phase 2.5; finalizer / registry / bind
   surfaces need the resolved MRO. Module docstring already separates them.
   Rejected.

6. **`__func__` override test in `install_relay_node_resolvers` vs
   `_consumer_overrode_resolve_typename`** — Same Node-default identity idea,
   but `resolve_typename` also needs `_FRAMEWORK_CLOSURE_MARKER` so an inherited
   framework closure is not misclassified `custom`. A shared helper would need
   a marker/mode flag. The three discriminators (`__dict__`, `__func__`, marker)
   answer different lifecycle questions. Rejected.

7. **`SyncMisuseError` re-export** — Definition lives in
   `utils/querysets.py`; this module keeps the documented back-compat alias
   that `types/__init__.py` and the package facade still route through.
   Same redundant-`as` pattern as `permissions.py`. Removing the alias without
   migrating the public import surface is an API break, not a DRY win. Rejected.

8. **Node sync/async resolve pairs vs `list_field` / connection visibility** —
   All use `apply_type_visibility_*` + `in_async_context`; node paths add
   `_apply_node_filter` / `_order_nodes` and DoesNotExist semantics. Visibility
   already consolidated in `utils/querysets.py`. Further merge would couple
   list/connection pipelines to Relay id filtering. Rejected.

9. **Encode sites outside this module** — `testing/relay.py::global_id_for`
   calls `encode_typename` (correct consumer). Example/test hand-rolled
   `relay.GlobalID(...)` / `to_base64` are fixtures, not a second encoder.
   Keyset `to_base64` is cursor encoding, orthogonal. Rejected.

10. **Composite-PK / `NodeIDAnnotationError` / stamp / `resolve_id_attr`
    fallback** — Three call sites ask Strawberry's scan for different outcomes
    (escape hatch vs stamp `"pk"` vs live unstamped fallback). Shared scan is
    upstream `relay.Node.resolve_id_attr.__func__`; local branches are not
    one responsibility. Rejected.

## Opportunities

None — this module is already the single owner of Relay interface injection,
node-resolver defaults, GlobalID typename install/encode, and resolve-then-
enforce decode. Cross-file consumers either call these APIs, wrap them for a
different error surface, or own a deliberately earlier/later Relay-shape
predicate. The remaining lookalikes (filter validate, typed mutation decode,
strategy vocabulary in `base.py`, twin model-label predicates) were disproved
as shared-change-axis duplicates.

## Judgment

Proved zero-edit. Boundaries with `types/base.py` (strategy vocabulary +
pre-injection shape), `types/finalizer.py` (orchestration + audit consumers),
`filters/base.py` / package `relay.py` (decode consumers with distinct
contracts), and `utils/querysets.py` (`SyncMisuseError` / visibility owners)
are correct. Ready for Worker 2.

Item-scoped diff statement: relative to
`743b3f2327de3c839bf73df9cb793c34597701c0`, production
`django_strawberry_framework/types/relay.py` is unchanged; this review adds
only `docs/dry/dry-file-types__relay.md`.

## Independent verification (Worker 2)

**Scoped diff.**
`git diff 743b3f2327de3c839bf73df9cb793c34597701c0 -- django_strawberry_framework/types/relay.py`
is empty (982 lines at baseline and HEAD). Zero-edit claim holds for production.

**Re-trace.** Confirmed present-day ownership: Phase 2.5 injection
(`apply_interfaces` / composite-pk / `install_relay_node_resolvers` /
`install_globalid_typename_resolver`), encode (`encode_typename` + payload
frozensets), decode (`decode_global_id`), and class-creation `install_is_type_of`.
Consumers call these APIs; they do not reimplement the contracts.

**Rejected candidates challenged (source evidence):**

1. **Filter decode** — `filters/base.py::_decode_and_validate_global_id`
   returns `node_id` only, validates against a known filter target via
   `_accepted_globalid_type_names`, raises coded `GraphQLError`
   (`GLOBALID_INVALID` / `GLOBALID_UNVALIDATABLE` / type mismatch).
   `decode_global_id` resolve-any-payload → `(type, node_id)` +
   `ConfigurationError`. Shared `from_id` parse is not one change axis;
   unifying needs error-surface / lookup-axis flags. Rejection stands.

2. **`decode_model_global_id`** — `relay.py` already delegates shape decode
   here, then adds expected-model check + `_coerce_pk_or_none` /
   `_resolve_real_pk` for WRITE consumers. Post-decode contract stays in
   package `relay.py`. Rejection stands.

3. **Vocabulary vs payload frozensets** — `STRING_GLOBALID_STRATEGIES` /
   `DEFAULT_GLOBALID_STRATEGY` in `types/base.py` (Meta/setting validation);
   `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` here (encode/decode/
   filter/audit payload shape). `FRAMEWORK_GLOBALID_STRATEGIES` derives from
   the latter. Overlap on `"type+model"` is the partition. Rejection stands.

4. **Twin model-label predicates** — AST bodies identical
   (`return effective_strategy in MODEL_LABEL_STRATEGIES`); frozenset is
   already SSOT. Distinct names match finalizer audit emit vs Step-2
   accept axes; collapsing would blur the documented diverge-if-needed
   split. Rejection stands.

5. **`implements_relay_node` vs `_is_relay_shaped`** — post-injection
   `issubclass(..., relay.Node)` vs pre-injection Meta ∪ direct inheritance
   (`types/base.py`). Factories/`Meta.connection` need the earlier
   predicate; finalizer/registry/bind need MRO. Rejection stands.

6. **`SyncMisuseError` re-export** — defined in `utils/querysets.py`;
   this module + `types/__init__.py` + package facade keep the documented
   back-compat alias (same pattern as `permissions.py`). Not a DRY win.
   Rejection stands.

7. **Testing encode** — `testing/relay.py::global_id_for` calls
   `encode_typename`; `decode_global_id` is a re-export. Correct consumer,
   not a second encoder.

**Missed consolidations searched.** Encode sites outside this module
(filter input re-base64, keyset cursor `to_base64`, example/test
`GlobalID` fixtures) are orthogonal. Shared GlobalID parse between
decode and filter would require an error-factory mode flag — rejected
under DRY.md. No additional consolidation opportunity found.

**Disposition.** Status verified. Plan checkbox marked `[x]`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
