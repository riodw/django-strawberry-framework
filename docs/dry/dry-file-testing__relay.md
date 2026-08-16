# DRY review: `django_strawberry_framework/testing/relay.py`

Status: verified

## System trace

`testing/relay.py` owns the **consumer-facing Relay GlobalID test helpers**
(~97 lines): mint (`global_id_for`) and public decode access
(`decode_global_id` re-export). Audience is consumer *test suites*; the
submodule path (not `testing/__init__`) is the public contract so
`import django_strawberry_framework.testing` stays free of `types`-package
cost.

Ownership map (present-day source):

| Concern | Owner |
| --- | --- |
| Strategy → type-name slot (`model` / `type` / `type+model` / callable) | `types/relay.py::encode_typename` |
| Live `resolve_typename` install + `effective_globalid_strategy` stamp | `types/relay.py::install_globalid_typename_resolver` |
| Decode resolve-then-enforce (`ConfigurationError`) | `types/relay.py::decode_global_id` |
| String-strategy vocabulary | `types/base.py::STRING_GLOBALID_STRATEGIES` |
| Relay-Node gate message fragments | `types/base.py::_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL` |
| Consumer mint with finalized / Node / string-strategy gates | **this file** `global_id_for` |
| Public test-suite decode name | **this file** re-exports `types.relay.decode_global_id` (identity, not a wrapper) |
| Root `node(id:)` GraphQLError translation | `relay.py::_decode_or_graphql_error` |
| Typed model-coercing decode | `relay.py::decode_model_global_id` |
| Filter wire decode + type-name accept set | `filters/base.py::_decode_and_validate_global_id` |

Connected surfaces examined (evidence only; `types/relay.py` not absorbed):

- `types/relay.py` — still-open sibling. Owns encode/decode production path;
  this file calls `encode_typename` and re-exports `decode_global_id`.
- `types/base.py` — strategy frozenset + gate prose already shared; this file
  only composes them into the mint helper's raise text.
- `testing/__init__.py` — documents deliberate non-re-export of these helpers.
- Callers of `global_id_for`: `tests/testing/test_relay.py` (contract),
  `tests/forms/test_resolvers.py`, `tests/rest_framework/test_resolvers.py`,
  `tests/filters/test_sets.py` (strategy-aware relation ids).
- Package encode/decode unit suite: `tests/types/test_relay_interfaces.py`
  (imports `decode_global_id` / `encode_typename` from `types.relay`, local
  `_encoded_id` / `_emitted_type_name_slot` for encoder coverage).
- Live `/graphql/` suites: hand-roll `str(relay.GlobalID(type_name=…))` with
  model labels or string slots (`test_products_api._global_id`, library /
  kanban / error-policy / client suites).

Item-scoped baseline
`git diff 77d5cc38c62e14f87d7ba1d15e3d71f67edfa921 --
django_strawberry_framework/testing/relay.py` is empty (and no other paths
were edited).

## Verification

Searches / checks on present source:

- `global_id_for` / `decode_global_id` / `encode_typename` / `STRING_GLOBALID_*`
  / `relay.GlobalID(` / `to_base64(` across package, tests, examples.
- Mint ownership: production string-slot computation is only
  `encode_typename`; `global_id_for` is the sole consumer helper that gates
  finalized + Relay-Node + `STRING_GLOBALID_STRATEGIES` then delegates.
  Pin in `tests/testing/test_relay.py`: helper output equals live
  `row { id }` for `model` / `type` / `type+model`;
  `testing.relay.decode_global_id is types.relay.decode_global_id`.
- Decode ownership: one implementation in `types/relay.py`. Root
  `relay.py` and filters wrap it (or parallel wire parse) for field-error /
  accept-set contracts — different change axes; not this file's job and
  not absorbable without taking the open `types/relay.py` item.
- Example / suite `_global_id(type_name, pk)` helpers take an already-chosen
  type-name **string**, not a `DjangoType`. They mint wrong-type, empty-id,
  and model-label literals for live HTTP pins. That is not
  `global_id_for(type_cls, id)`'s contract.
- `_encoded_id` / `_emitted_type_name_slot` in `test_relay_interfaces.py`
  exercise `types.relay` encode (including callable via live
  `resolve_typename`). Routing those through `testing.relay` would couple
  encoder unit tests to the consumer helper they are not validating.

Scratch pytest: none (inspection + identity pin + call-graph sufficient).

## Opportunities

None — mint gates live only here; slot encoding and decode dispatch already
live in `types/relay.py`; vocabulary / gate prose already shared from
`types/base.py`; re-export is identity by design; remaining hand-mint sites
are intentional test literals or a thinner `(type_name, pk)` shape.

### Strongest rejected candidates

1. **Move `global_id_for` into `types/relay.py` (or absorb encode/decode here).**
   Disproved: production encode/decode and consumer-test mint/gates have
   different audiences and import-cost budgets. Spec-032 Decision 10 and the
   testing `__init__` export gate keep helpers under `testing/`. Absorbing
   `types/relay.py` would steal the still-open sibling item.

2. **Replace example `_global_id(type_name, pk)` / `label_lower` mints with
   `global_id_for`.** Disproved: different inputs (string slot vs DjangoType)
   and different jobs (pin model-label / wrong-type / empty-id wire vs
   strategy-aware emission). Unifying would need mode flags or force every
   live suite to import GraphQL types. Leave any suite-hygiene sweep to the
   testing-folder / project pass.

3. **Replace `test_relay_interfaces._encoded_id` with `global_id_for`.**
   Disproved: that suite owns encoder/decoder unit coverage for
   `types.relay` (including callable). Using the testing helper would make
   the encoder tests depend on the consumer facade that itself depends on
   `encode_typename` — circular proof, not one shared rule.

4. **Share decode with `filters/_decode_and_validate_global_id` or
   `relay.decode_model_global_id` via this module.** Disproved: those own
   filter accept-sets and model/pk coercion + GraphQLError mapping. Decode
   shape policy belongs with `types/relay.py` (open item), not the testing
   re-export.

5. **Re-export from `testing/__init__.py`.** Already rejected on the
   `__init__` item (import-cost + DoD submodule path); this file's docstring
   matches that split.

## Judgment

Zero-edit. `testing/relay.py` is already a thin true owner: gate-and-mint
for consumer suites, identity re-export of production decode, all slot
encoding delegated to `encode_typename`. No consolidation warranted at this
owner.

## Implementation (Worker 1)

No production or test edits. Item-scoped diff remains empty:

```text
git diff 77d5cc38c62e14f87d7ba1d15e3d71f67edfa921 -- \
  django_strawberry_framework/testing/relay.py docs/dry/dry-file-testing__relay.md
```

(only the new artifact appears as an untracked add; target `.py` unchanged).

Deferred pytest: none required (no behavior change). Permanent tests already
cover the helper contract in `tests/testing/test_relay.py`.

Changelog: no (zero-edit).

Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced present-day `testing/relay.py` (~97 lines), `types/relay.py::encode_typename` /
`decode_global_id`, `testing/__init__.py` export gate, root `relay.py` decode wrappers,
`filters/base.py::_decode_and_validate_global_id`, example/suite hand-mints, and
`tests/testing/test_relay.py` / `tests/types/test_relay_interfaces.py` helpers.

**Scoped diff:**
`git diff 77d5cc38c62e14f87d7ba1d15e3d71f67edfa921 -- django_strawberry_framework/testing/relay.py`
is empty (97 lines unchanged).

**Zero-edit claim confirmed:**

- `global_id_for` is the sole consumer mint that gates finalized / Relay-Node /
  `STRING_GLOBALID_STRATEGIES`, then delegates the slot to `encode_typename` and wraps
  `relay.GlobalID`. Gate prose already shared from `types/base.py`.
- `decode_global_id` is an identity re-export: `uv run` import check
  `testing.relay.decode_global_id is types.relay.decode_global_id` → `True`; pinned in
  `tests/testing/test_relay.py`.

**Rejected candidates challenged (all stand):**

1. **Move mint into `types/relay.py`.** Production encode/decode vs consumer-test gates
   differ in audience and import budget; `testing/__init__` documents deliberate
   non-re-export; absorbing encode/decode would steal the still-open `types/relay.py`
   plan item.
2. **Replace example `_global_id(type_name, pk)` / label_lower mints.** Confirmed
   different inputs (`str` slot vs `DjangoType`) and jobs (wrong-type / empty-id /
   model-label wire pins). Unifying would need mode flags or force GraphQL-type imports
   into live HTTP suites.
3. **Route `_encoded_id` through `global_id_for`.** Encoder unit helpers exercise live
   `resolve_typename` (including callable); `global_id_for` raises on callable/custom —
   circular proof if encoder tests depended on the consumer facade.
4. **Share filter/root decode wrappers via this module.**
   `_decode_or_graphql_error` / `decode_model_global_id` /
   `_decode_and_validate_global_id` add GraphQLError mapping, model/pk coercion, or
   filter accept-sets — different change axes owned elsewhere.
5. **Re-export from `testing/__init__`.** `__all__` omits both names; docstring states
   submodule path + import-cost rationale (already closed on the `__init__` item).

**Independent missed-consolidation search:** no other production site gates-and-mints
strategy-aware ids for a `DjangoType`; remaining `relay.GlobalID(type_name=…)` call
sites are intentional string-slot literals or thinner suite helpers. No consolidation
warranted at this owner.

Outcome: **verified**. Plan checkbox marked `[x]`.

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
