# Build: Slice 3 — the decode seam (`decode_global_id` resolve-then-enforce + `definition_for_graphql_name` + symmetry + transitional `type+model`)

Spec reference: `docs/spec-031-globalid_encoding-0_0_9.md` (lines 96-100)
Status: final-accepted

## Plan (Worker 1)

This slice ships the **decode** half of the GlobalID-encoding feature, the
forward-looking piece root `node(id:)` / `nodes(ids:)` (sibling card
`WIP-ALPHA-032-0.0.9`) will consume. No shipped `0.0.9` path calls it yet (filtering
uses only the `node_id` slot; native Strawberry `resolve_type` is unreached without a
root node field — spec Current state / Risks). It is validated directly by Slice-3
package tests.

Slices 1 and 2 already shipped (verified against `bld-slice-1-...md` and
`bld-slice-2-...md` final-verification, and against current source). Already present
and **reused, not re-created**:

- `DjangoTypeDefinition.effective_globalid_strategy: str | None = None`
  (`definition.py:132`) — the finalization-recorded classification (`"model"` /
  `"type"` / `"type+model"` / `"callable"` / `"custom"`, or `None` = not a
  framework-decodable Relay-Node type). **Decode reads THIS field**, not
  `_resolve_globalid_strategy` (spec Revision 5 cleanup / Decision 8 / 10).
- `DjangoTypeDefinition.origin` (`definition.py:102`, the `DjangoType` class) and
  `DjangoTypeDefinition.graphql_type_name` property (`definition.py:147-157`,
  `self.name` or `self.origin.__name__`).
- `types/relay.py::MODEL_LABEL_STRATEGIES = frozenset({"model", "type+model"})`
  (relay.py:380) + `_emits_model_label` / `_accepts_model_label_decode` predicates
  (relay.py:383-403) — the single source of truth for the model-label-shape
  membership. **Decode Step-2's model-label acceptance reuses
  `_accepts_model_label_decode`.**
- `registry.get(model)` (registry.py:190-209, primary / lone-type honoring
  `Meta.primary`), `registry.iter_definitions()` (registry.py:333-335),
  `registry.get_definition(type_cls)` (registry.py:315-317).
- `types/relay.py::implements_relay_node(type_cls)` (relay.py:63-73,
  `issubclass(type_cls, relay.Node)`) — the Relay-Node predicate the
  `definition_for_graphql_name` Relay-only scan needs.
- `from ..exceptions import ConfigurationError` (relay.py:35, registry.py:26) — the
  one uniform decode-failure type.

Slice 3 adds exactly two source pieces (spec lines 96-98, Decision 8) plus the carry-
forward DRY consolidation:

1. `registry.py::definition_for_graphql_name(name)` — the type-name decode entry point
   (replaces the TODO at registry.py:319-331).
2. `types/relay.py::decode_global_id(gid)` — the resolve-then-enforce dispatch
   (replaces the TODO at relay.py:541-546, which already pseudo-codes
   `return candidate.origin, gid.node_id`).
3. `types/relay.py::TYPE_NAME_STRATEGIES` — the **planned DRY consolidation** (carry-
   forward from the Slice-2 review + final verification): the "which strategies accept
   a type-name payload" membership, currently a bare tuple `("type", "type+model")` at
   `filters/base.py:245`. Slice 3's decode Step-2 needs the SAME notion, so it lands as
   a sibling named constant at the `types/relay.py` source of truth (next to
   `MODEL_LABEL_STRATEGIES`), and the filter's bare tuple is refactored to consume it.
   Tight scope: one constant + one predicate, two consumers (filter + decoder).

### DRY analysis

**Existing patterns reused (cite file:line — pin-at-write-time hints).**

- **Decode reads the recorded `effective_globalid_strategy`, never re-resolves.** The
  durable contract is the finalization-stamped `definition.effective_globalid_strategy`
  field (`definition.py:132`, recorded by `install_globalid_typename_resolver` at
  relay.py:517). Decode Step-2 reads it directly — it does NOT call
  `_resolve_globalid_strategy` again (which re-runs the precedence + setting read and
  cannot tell a preserved consumer override (`custom`) from the framework closure). This
  is the spec's explicit DRY rule (spec line 35 Revision-2 note + Revision-5 cleanup,
  Decision 8 Step 2). Carried in worker-1 memory.
- **`MODEL_LABEL_STRATEGIES` predicates** (`relay.py:380-403`). Step-2's model-label
  acceptance is exactly `_accepts_model_label_decode(effective_strategy)` (relay.py:393)
  — `model` / `type+model` accept a model-label payload. Reused, not re-typed. (Slice 2
  already reserved this for the decoder; Worker 3 + Worker 1 confirmed it is the same
  frozenset object across module boundaries.)
- **`registry.get(model)`** (registry.py:190-209) is the primary-routing resolver the
  model-label branch reuses verbatim — it returns the declared primary
  (`_primaries[model]`, honoring `Meta.primary`), or the lone registered type, or
  `None`. This is the same resolver relation targets use
  (`DjangoTypeDefinition.related_target_for` → `registry.get`), so a decoded ID and a
  traversed relation land on the same type (spec Decision 8 justification).
- **`registry.iter_definitions()`** (registry.py:333-335) is the scan source for
  `definition_for_graphql_name`, mirroring the TODO pseudocode at registry.py:328 (note:
  the TODO pseudo-scans `self._definitions.items()` — `iter_definitions()` is the public
  spelling of that, which the spec sub-bullet names; use the public iterator, not the
  private dict). `registry.get_definition(type_cls)` (registry.py:315-317) reads the
  candidate definition once Step 1 resolves a `type_cls` via `registry.get`.
- **`implements_relay_node(type_cls)`** (relay.py:63-73) is the Relay-only-scan
  predicate `definition_for_graphql_name` applies (`registry.py` imports it in-function
  to dodge the `registry → relay → registry`-adjacent direction — see "Duplication risk
  avoided" import note). It also belt-and-suspenders pairs with Step-2's absent-`None`
  rejection (a non-Relay type's `effective_globalid_strategy` is never stamped).
- **`relay.GlobalID.from_id(value)`** (strawberry `relay/types.py:113`, verified against
  the installed `0.316.0`) is the `str → GlobalID` parser. It wraps `from_base64` and
  re-raises any `ValueError` as `GlobalIDValueError` (`relay/types.py:70`, a subclass of
  `ValueError`). The `str` branch reuses this exactly as `filters/base.py:271` already
  does (`relay.GlobalID.from_id(value)`); catching `ValueError` (the superset spelling)
  suffices. There is **no** `GlobalID.from_base64` classmethod (module-level
  `from_base64` returns a raw tuple) — `from_id` is correct (spec Revision 4 P3
  correction).
- **The `ConfigurationError`-message-builder fail-loud shape.** The spec names the
  `RelatedFilter`-style fail-loud message for an unqualified/unresolvable name. The
  decode errors follow that shape (name the resolution attempt: the offending
  `type_name` / label / strategy). One uniform `ConfigurationError` for every failure
  mode keeps the contract `032`'s arbitrary client input depends on.
- **Test scaffolding.** Both `tests/types/test_relay_interfaces.py` (autouse
  `registry.clear()` fixture at test_relay_interfaces.py:37-42; real fakeshop models
  `apps.products.models.{Category, Item}`; `finalize_django_types()`; the Slice-2
  `_emitted_typename`-style helpers) and `tests/test_registry.py` (autouse
  `_isolate_global_registry` at test_registry.py:34-39; `fresh_registry` fixture;
  `Category`/`Item`/`Property` models; the `register` / `primary` multi-type fixtures at
  test_registry.py:721-802) already carry the fixtures the new tests need. Decode
  round-trips build encoded IDs with `relay.to_base64(type_name, node_id)` (or
  `str(relay.GlobalID(...))`).

**New helpers / constants justified (single responsibility each).**

- `registry.py::definition_for_graphql_name(name) -> DjangoTypeDefinition` — single
  responsibility: invert the `type`-strategy encode (which emits
  `definition.graphql_type_name`) by a unique `graphql_type_name` lookup over
  Relay-Node definitions, raising `ConfigurationError` on miss or ambiguity. It is the
  type-name half of Step 1. Keyed on `graphql_type_name` (NOT `type_cls.__name__`) so a
  `Meta.name`-renamed type round-trips (spec Decision 8 / feedback P1). Relay-Node scan
  only (a non-Node type can never be a `GlobalID` target — spec Revision 4 P1).
- `types/relay.py::decode_global_id(gid: relay.GlobalID | str) -> tuple[type, str]` —
  single responsibility: the input-gate + parse + resolve-then-enforce dispatch,
  returning `(target_type, node_id)` (`target_type` is `candidate.origin`, the
  `DjangoType` class; `node_id` is the parsed `gid.node_id` string). One uniform
  `ConfigurationError` for every failure.
- `types/relay.py::TYPE_NAME_STRATEGIES = frozenset({"type", "type+model"})` + a
  predicate `_accepts_type_name_decode(effective_strategy) -> bool` (sibling of
  `_accepts_model_label_decode`) — single responsibility: the "which strategies accept a
  type-name payload" membership. Reused by BOTH decode Step-2 (type-name branch) AND
  `filters/base.py::_accepted_globalid_type_names` (refactoring its bare tuple at
  filters/base.py:245). This is the planned consolidation; without it the second site
  (the decoder) would make `{"type", "type+model"}` a parallel-literal defect (Worker 3
  Slice-2 DRY note + Worker 1 Slice-2 carry-forward).

**Duplication risk avoided.**

- **The strategy→shape sets are NOT re-typed.** Step-2 enforcement maps shape→strategy
  via the two named predicates: a model-label payload is permitted iff
  `_accepts_model_label_decode(strategy)` (relay.py:393, reused); a type-name payload is
  permitted iff `_accepts_type_name_decode(strategy)` (new, sourced from
  `TYPE_NAME_STRATEGIES`). The decoder never inlines `{"model", "type+model"}` or
  `{"type", "type+model"}` — both memberships are single-sourced in `types/relay.py`.
- **`callable` / `custom` "no decode" falls out of the predicate math, no third
  literal.** Neither predicate includes `callable` or `custom`, so a `callable`/`custom`
  candidate's payload is permitted by neither shape → uniform rejection. No separate
  encode-only set is needed; the absence from both `MODEL_LABEL_STRATEGIES` and
  `TYPE_NAME_STRATEGIES` IS the encode-only contract. (Worker 2 may add a brief comment
  naming this, but must not introduce a `{"callable", "custom"}` literal.)
- **The filter refactor is a pure swap, not a behavior change.**
  `filters/base.py:245` `if strategy in ("type", "type+model"):` becomes
  `if _accepts_type_name_decode(strategy):` (or `if strategy in TYPE_NAME_STRATEGIES:`)
  — same membership, now single-sourced. The `model` branch at filters/base.py:243
  already uses `MODEL_LABEL_STRATEGIES`; this makes the two branches symmetric. No
  filter-behavior change, no new filter test needed beyond confirming the existing
  Slice-2 filter tests (`tests/filters/test_base.py`) still pass (Worker 2 re-runs them;
  the import + tuple swap is behavior-preserving). The shared mapping import direction
  (`filters → types`) is already established and acyclic (Slice 2, filters/base.py:44
  module-top `from ..types.relay import MODEL_LABEL_STRATEGIES`); add
  `TYPE_NAME_STRATEGIES` (and/or the predicate) to that same import.
- **`registry.py` import of `implements_relay_node` is in-function** to avoid coupling
  the registry module top to `types.relay`. `registry.py` already uses in-function
  imports for the same cycle-dodge reason (the `clear()` filter/order/connection imports
  at registry.py:434-479, and the module-top `TYPE_CHECKING`-only `DjangoTypeDefinition`
  import at registry.py:29). `definition_for_graphql_name` is only called at decode time
  (well after module load), so an in-function `from .types.relay import
  implements_relay_node` resolves cheaply. (Worker 2 discretion: if a module-top import
  is proven acyclic under Django setup it is acceptable, but in-function is the safe
  default given `registry.py` is imported very early.)
- **No hand-rolled label parsing / formatting.** The model-label-vs-type-name shape
  discrimination is "does the `type_name` slot contain a dot" (spec Decision 8 Step 1:
  `"app_label.modelname"` contains a dot, a bare GraphQL type name does not). Use the
  dot test directly on the parsed `gid.type_name`; `apps.get_model` is the canonical
  `app_label.model → model` resolver (it accepts the dotted `"app.model"` string or the
  split pair — Worker 2 picks; `apps.get_model("app", "model")` after a single
  `split(".", 1)` is the explicit form). Do NOT re-derive labels with `f"{app}.{model}"`.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against current source
before editing — Slices 1/2 already shifted these files.

1. **`django_strawberry_framework/types/relay.py` — add `TYPE_NAME_STRATEGIES` + its
   predicate.** Immediately after `MODEL_LABEL_STRATEGIES` / `_emits_model_label` /
   `_accepts_model_label_decode` (relay.py:380-403), add
   `TYPE_NAME_STRATEGIES = frozenset({"type", "type+model"})` and
   `_accepts_type_name_decode(effective_strategy: str | None) -> bool`
   (`effective_strategy in TYPE_NAME_STRATEGIES`). Extend the single-source-of-truth
   comment (relay.py:374-379) to name the type-name membership alongside the model-label
   one (both are the payload-shape source of truth the encoder/audit/filter/decoder
   reference). Names at Worker 2 discretion; the requirement is single-sourcing reused by
   the filter AND the decoder.

2. **`django_strawberry_framework/registry.py` — add `definition_for_graphql_name`.**
   Replace the TODO at registry.py:319-331 with the method, placed where the TODO sits
   (immediately before `iter_definitions`, registry.py:333). Signature:
   `def definition_for_graphql_name(self, name: str) -> DjangoTypeDefinition:`. Logic
   (spec line 97, Decision 8 Step 1 type-name branch):
   - In-function `from .types.relay import implements_relay_node` (cycle-dodge — see DRY
     note; Worker 2 may hoist if proven acyclic).
   - Scan `self.iter_definitions()` (or `self._definitions.items()` — the public iterator
     is preferred per the spec sub-bullet's `iter_definitions()` wording); collect every
     `definition` where `implements_relay_node(type_cls)` AND
     `definition.graphql_type_name == name`.
   - **Exactly one match** → return it.
   - **Zero matches** → `raise ConfigurationError(...)` naming the unresolvable
     `graphql_type_name` (the fail-loud shape; the spec says raise on a miss — this is
     the registry-level miss, distinct from `decode_global_id`'s own wrapping).
   - **Two or more matches** → `raise ConfigurationError(...)` naming the ambiguous name
     and the colliding types (spec: raise on ambiguity).
   - Reuse the `_already_registered`-style canonical-phrasing posture only if it reads
     cleanly; the spec does not require sharing that builder, so an inline
     `ConfigurationError(f"...")` matching the registry's existing inline-error style
     (e.g. registry.py:126, 134) is acceptable. Worker 2 discretion on exact wording,
     within "name the attempt" content.
   - Docstring: name it the GlobalID type-name decode entry point, keyed on
     `graphql_type_name` (NOT `type_cls.__name__`) so `Meta.name` round-trips, Relay-Node
     scan only.

3. **`django_strawberry_framework/types/relay.py` — add `decode_global_id`.** Replace the
   decode TODO at relay.py:541-546 with the helper. Add the imports it needs:
   `from django.apps import apps` (NOT yet imported — add to the django-import block near
   relay.py:29-30) for the model-label resolver. `relay`, `ConfigurationError`,
   `MODEL_LABEL_STRATEGIES`/`_accepts_model_label_decode`, the new
   `TYPE_NAME_STRATEGIES`/`_accepts_type_name_decode`, and `implements_relay_node` are
   already module-level. `registry` is reached **in-function** (`from ..registry import
   registry` — `registry.py` imports `types.relay::implements_relay_node` in-function, and
   `relay.py` must not import `registry` at module top; `relay.py` already reaches
   `..conf`/`base` in-function for the same cycle-dodge reason — relay.py:348-358).
   Signature: `def decode_global_id(gid: relay.GlobalID | str) -> tuple[type, str]:`.
   Logic (spec Decision 8, error shapes spec lines 264-267):
   - **Runtime input-type gate (first).**
     `if not isinstance(gid, (relay.GlobalID, str)): raise ConfigurationError(...)` —
     reject `None` / `int` / lazy objects up front (its caller is `032`'s root
     `node(id:)`, fed arbitrary client input), so no `AttributeError` / `TypeError`
     leaks past the uniform-error contract (spec line 264, feedback P2).
   - **Parse.** A `relay.GlobalID` is used directly. A `str` is parsed via
     `relay.GlobalID.from_id(value)` inside a `try/except ValueError` (catching the
     `ValueError` superset covers `GlobalIDValueError`); on `ValueError` →
     `raise ConfigurationError(...) from e` (malformed base64 / non-`type:id` shape — spec
     line 265). NOTE: `from_id` does NOT enforce non-empty slots (verified —
     `to_base64("", "")` parses to empty `type_name`/`node_id`), so the empty-slot checks
     are package-added.
   - **Empty-slot rejection.** After obtaining `type_name = decoded.type_name` /
     `node_id = decoded.node_id`, reject an empty `type_name` OR empty `node_id` as
     `ConfigurationError` (spec line 265, feedback P2; the encoder never emits an empty
     type-name slot, and the package does not support blank-string primary keys).
   - **Step 1 — resolve a candidate type from the type-name slot's shape:**
     - **Model-label slot** (`"." in type_name`): split into `(app_label, model_name)`
       (`type_name.split(".", 1)`); resolve the model via
       `apps.get_model(app_label, model_name)` inside a `try/except LookupError` (an
       unknown app/model → `ConfigurationError` naming the label — spec line 266); then
       `target_type = registry.get(model)` (the primary / lone type, honoring
       `Meta.primary`). If `registry.get(model)` is `None` (no registered Relay-Node type,
       or an ambiguous multi-type-no-primary state) → `ConfigurationError` naming the
       resolution attempt (spec line 266). Resolve the candidate `definition` via
       `registry.get_definition(target_type)`.
     - **GraphQL-type-name slot** (no dot): `definition = registry.definition_for_graphql_name(type_name)`
       (which itself raises `ConfigurationError` on miss/ambiguity — Worker 2 may let that
       propagate, or wrap it; either way the surfaced type is `ConfigurationError`).
       `target_type = definition.origin`.
   - **Step 2 — enforce the candidate's recorded effective strategy permits the payload
     shape** (read `definition.effective_globalid_strategy`):
     - `strategy is None` (absent — a non-Relay-Node `DjangoType`, or a mid-state type
       whose install never stamped it) → `ConfigurationError` naming the candidate as not
       a framework-decodable Relay-Node type (spec line 266, feedback P1; belt-and-
       suspenders with the Relay-only scan in Step 1).
     - **Model-label payload** (this resolution went through the dot branch): permitted
       iff `_accepts_model_label_decode(strategy)` (`model` / `type+model`); else
       `ConfigurationError` (a model-label ID for a `type`-strategy type — spec line 267 /
       406).
     - **Type-name payload** (no-dot branch): permitted iff
       `_accepts_type_name_decode(strategy)` (`type` / `type+model`); else
       `ConfigurationError` (a type-name ID for a `model`-strategy type — spec line 267 /
       405).
     - `callable` / `custom` are in neither membership, so any payload resolving to such a
       candidate is rejected (encode-only in `0.0.9` — spec line 408). This falls out of
       the predicate math; no separate set.
     - **Discretion (Worker 2):** the cleanest structure is to branch on the slot shape
       (dot vs no-dot) computed in Step 1, carry that shape forward, and apply the one
       matching predicate in Step 2. Whether Step 1 returns a `(definition, shape)` pair
       or Step 2 re-tests `"." in type_name` is Worker 2's call, provided the two
       memberships are read via the named predicates and not re-typed.
   - **Return** `(target_type, node_id)` (i.e. `candidate.origin, decoded.node_id` — the
     decode TODO at relay.py:546 already pseudo-codes this).
   - Every failure path raises `ConfigurationError` (one uniform decode-failure type, the
     `RelatedFilter`-style fail-loud message naming the resolution attempt — spec
     Decision 8 / feedback P2).

4. **`django_strawberry_framework/filters/base.py` — refactor the bare tuple to the
   shared constant (the planned DRY consolidation).** At
   `_accepted_globalid_type_names` (filters/base.py:220-247), change
   `if strategy in ("type", "type+model"):` (filters/base.py:245) to read the new shared
   membership — `if _accepts_type_name_decode(strategy):` (or
   `if strategy in TYPE_NAME_STRATEGIES:`). Add `TYPE_NAME_STRATEGIES` and/or
   `_accepts_type_name_decode` to the existing module-top import
   `from ..types.relay import MODEL_LABEL_STRATEGIES` (filters/base.py:44). This is a
   behavior-preserving swap (same `{"type", "type+model"}` membership), so it adds NO new
   filter behavior — but it removes the parallel-literal-set risk the Slice-2 review
   flagged. Worker 2 confirms the existing `tests/filters/test_base.py` Slice-2 strategy-
   aware tests still pass unchanged (no assertion edits expected; if a test imported the
   bare tuple it does not — it tests behavior).

### Test additions / updates

Per spec Test plan "Slice 3" (spec lines 598-610) and DoD item 5 (spec line 677). All
package-internal — decode has no live caller in `0.0.9` (root `node(id:)` is `032`), so
this slice is correctly earned in `tests/types/` + `tests/test_registry.py`, NOT
`examples/fakeshop/test_query/` (the live decode round-trip is `032`'s; Slice 4's live
work is emitted-ID + filter round-trip only). Build encoded inputs with
`relay.to_base64(type_name, node_id)` / `str(relay.GlobalID(type_name, node_id))` — never
a raw `"app.model:pk"` payload.

#### `tests/test_registry.py` (extend) — spec line 100 (the helper)

Reuse the `fresh_registry` fixture (test_registry.py:29-39) + `Category`/`Item`/
`Property` models. Build real Relay-Node `DjangoType`s (interfaces `(relay.Node,)`) and
finalize so `graphql_type_name` + Relay-shape are real, OR register definitions directly
where that reads cleaner (Worker 2 discretion — the helper only reads
`iter_definitions` + `implements_relay_node` + `graphql_type_name`).

- `test_definition_for_graphql_name_returns_match` — a registered Relay-Node type's
  `graphql_type_name` resolves to its `DjangoTypeDefinition`.
- `test_definition_for_graphql_name_honors_meta_name` — a type with `Meta.name = "Item"`
  resolves via `"Item"` (the `graphql_type_name`), NOT its class name (proves keying on
  `graphql_type_name`, not `type_cls.__name__`).
- `test_definition_for_graphql_name_ignores_non_relay_definitions` — a non-Relay-Node
  `DjangoType` with a matching `graphql_type_name` is NOT returned (Relay-only scan); if
  it is the only candidate, the lookup raises (miss).
- `test_definition_for_graphql_name_unknown_raises` — an unregistered name raises
  `ConfigurationError`.
- `test_definition_for_graphql_name_ambiguous_raises` — two Relay-Node definitions
  sharing one `graphql_type_name` raise `ConfigurationError` naming the ambiguity. (If a
  natural duplicate-name arrangement is hard to construct through the public API, Worker 2
  may register two definitions directly on a `fresh_registry` with the same
  `graphql_type_name` — discretion.)

#### `tests/types/test_relay_interfaces.py` (extend) — spec lines 598-610 (the `types/relay.py` mirror)

Add `decode_global_id` (and any new predicate exercised directly) to the
`from ...types.relay import (...)` block (test_relay_interfaces.py:23-33). Reuse the
autouse `registry.clear()` fixture + `apps.products.models.{Category, Item}` + the
Slice-2 finalize/emit helpers. For multi-type / primary fixtures, mirror the
`tests/test_registry.py` `primary=` registration pattern (test_registry.py:721-802) via
two `DjangoType`s over one model with `Meta.primary`.

- `test_decode_model_label_routes_to_primary` —
  `decode_global_id(relay.GlobalID("products.item", "42"))` → `(ItemType, "42")` via
  `apps.get_model` + `registry.get`; a multi-type model routes to the `Meta.primary` type
  (pinned with a multi-`DjangoType` fixture — spec line 99/600).
- `test_decode_type_name_routes_via_graphql_name` — a type-name payload resolves via
  `registry.definition_for_graphql_name(...)`, keyed on `graphql_type_name`.
- `test_decode_type_strategy_honors_meta_name_round_trip` — `ItemType` with
  `Meta.name = "Item"` under the `type` strategy emits `GlobalID("Item", …)` (via the
  installed/default `resolve_typename`) and `decode_global_id` returns `ItemType` (proves
  decode keys on `graphql_type_name`, not `__name__` — feedback P1).
- `test_encode_decode_round_trip_decodable_strategies` — encode→decode symmetry for
  `model` / `type` / `type+model` (build the emitted type-name slot via the installed
  `resolve_typename` or `encode_typename`, base64 it, decode it back to the origin type +
  node_id). `callable` is encode-only — NO decode symmetry (covered only by the Slice-2
  encode test).
- `test_type_plus_model_decodes_both` — a `type+model` type decodes BOTH an old
  type-anchored ID (`GlobalID(graphql_type_name, pk)`) AND a new model-anchored ID
  (`GlobalID(label, pk)`) to the same `(type, pk)` (the transitional accept-old-IDs path —
  the card DoD's explicit requirement, spec line 603).
- `test_decode_model_strategy_rejects_type_name_id` — a type-name payload for a
  `model`-strategy type raises `ConfigurationError` (Step-2, direction 1 — spec line 605).
- `test_decode_type_strategy_rejects_model_label_id` — a model-label payload for a
  `type`-strategy type raises `ConfigurationError` (Step-2, direction 2 — spec line 605).
- `test_decode_callable_strategy_has_no_decode_path` — a payload resolving to a
  `callable`-strategy type raises `ConfigurationError` (encode-only — spec line 606).
- `test_decode_custom_override_type_has_no_decode_path` — a payload resolving to a
  `custom` (consumer `resolve_typename` override) type raises `ConfigurationError`
  (encode-only — spec line 606).
- `test_decode_non_node_graphql_name_raises` / absent-strategy — a
  `to_base64("SomePlainType", "1")` (or model label) whose candidate has
  `effective_globalid_strategy is None` (a non-Relay-Node `DjangoType`, or any unstamped
  candidate) raises `ConfigurationError`, NOT a leaked `KeyError` / `AttributeError` (the
  absent-`None` rejection — spec line 607, 404, feedback P1).
- `test_decode_malformed_base64_raises_configuration_error` — a malformed base64 /
  non-`type:id` string raises `ConfigurationError` (Strawberry's `GlobalIDValueError` /
  `ValueError` caught and re-raised, not leaked — spec line 608).
- `test_decode_non_str_input_raises` — `None` / an `int` / an arbitrary object raises
  `ConfigurationError` (the runtime input-type gate — spec line 609, 264).
- `test_decode_empty_type_name_raises` / `test_decode_empty_node_id_raises` — a
  `to_base64("", "1")` / `to_base64("products.item", "")` raises `ConfigurationError` (the
  empty-payload contract — spec line 609, 265). (These are package-added checks; `from_id`
  does NOT reject empty slots — verified against installed strawberry.)
- `test_decode_unresolvable_label_raises` — an unknown app/model
  (`to_base64("nope.nope", "1")`), an unregistered model, or an ambiguous
  `graphql_type_name` raises `ConfigurationError` naming the attempt (spec line 610).

Filter-refactor regression: Worker 2 re-runs `tests/filters/test_base.py` (the Slice-2
strategy-aware suite) after the bare-tuple→`TYPE_NAME_STRATEGIES` swap to confirm the
behavior-preserving refactor introduces no regression. No new filter test is required
(the membership is unchanged); if Worker 3 wants an explicit single-source assertion, a
one-line `filters.base` `TYPE_NAME_STRATEGIES is relay.TYPE_NAME_STRATEGIES` identity
check (mirroring the Slice-2 `MODEL_LABEL_STRATEGIES` identity check) is a reasonable
addition — discretion.

Temp/scratch tests: none required — every branch is package-internal and directly covers
a Slice-3 contract. Worker 3 should confirm (a) the round-trip tests build encoded
`GlobalID`s (never raw payloads), (b) BOTH Step-2 rejection directions are exercised, and
(c) the absent-`None` and malformed-input paths surface `ConfigurationError` (not a leaked
`KeyError`/`ValueError`/`AttributeError`).

### Implementation discretion items

Assessed and intentionally delegated to Worker 2 (equivalent-shape / naming choices);
none are architectural escape hatches:

- The exact names of `TYPE_NAME_STRATEGIES` / `_accepts_type_name_decode` — any clear
  names; the requirement is ONE source of truth reused by the filter AND the decoder, not
  the literal spelling.
- Whether the filter swap reads `if _accepts_type_name_decode(strategy):` or
  `if strategy in TYPE_NAME_STRATEGIES:` — either; the requirement is consuming the shared
  membership, not re-typing the tuple.
- Whether `decode_global_id` carries the slot shape (dot vs no-dot) forward from Step 1 to
  Step 2, or Step 2 re-tests `"." in type_name` — either, provided the two memberships are
  read via the named predicates and `callable`/`custom`/`None` rejection falls out of the
  predicate math (no `{"callable", "custom"}` literal).
- The model-label resolve spelling: `apps.get_model(app_label, model_name)` after a single
  `type_name.split(".", 1)`, or `apps.get_model(type_name)` (the dotted form Django also
  accepts) — Worker 2 picks; both raise `LookupError` for unknown labels, caught and
  re-raised as `ConfigurationError`.
- Whether `definition_for_graphql_name` imports `implements_relay_node` in-function
  (preferred default, cycle-safe) or module-top (acceptable only if proven acyclic under
  Django setup — `registry.py` is imported very early, so in-function is the safe call).
- Whether `decode_global_id` lets `definition_for_graphql_name`'s `ConfigurationError`
  propagate or wraps it — either, since both surface `ConfigurationError`; propagation is
  simpler and avoids a redundant wrap.
- Whether the registry tests build the lookup fixtures via real finalized `DjangoType`s or
  by registering definitions directly on a `fresh_registry` — Worker 2 picks whichever
  reads cleaner per case (the helper only reads `iter_definitions` + `implements_relay_node`
  + `graphql_type_name`).
- The exact `ConfigurationError` message wording, within the spec's required content (each
  decode failure names the resolution attempt — the offending `type_name` / label /
  strategy / the not-a-Node-type candidate — in the `RelatedFilter`-style fail-loud shape).

No unresolved architectural questions — nothing escalated to the maintainer.

### Spec slice checklist (verbatim)

- [x] [`registry.py`][registry] gains `definition_for_graphql_name(name)` — a unique-`graphql_type_name` lookup over [`iter_definitions()`][registry] returning the matching [`DjangoTypeDefinition`][definition], raising [`ConfigurationError`][glossary-configurationerror] on ambiguity or miss (the type-name decode entry point; keyed on `graphql_type_name`, NOT `type_cls.__name__`, so a [`Meta.name`][glossary-metaname]-renamed type still decodes — [`docs/feedback.md`][feedback] P1).
- [x] [`django_strawberry_framework/types/relay.py`][relay] gains an internal `decode_global_id(gid: relay.GlobalID | str)` (accepts a [`relay.GlobalID`][glossary-relay-node-integration] or its base64 string, NOT a raw payload — [`docs/feedback.md`][feedback] P3) implementing the **resolve-then-enforce** dispatch of [Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type): Step 1 resolves a candidate — a model-label slot via `django.apps.apps.get_model(...)` → [`registry.get(model)`][registry] (primary / lone type), a GraphQL-type-name slot via `registry.definition_for_graphql_name(...)`; Step 2 reads the candidate's **recorded effective strategy** ([Decision 10](#decision-10--resolve_typename-injection-via-the-__func__-identity-test-at-phase-25)) and enforces it permits the payload shape (`model` → model-label only; `type` → type-name only; `type+model` → both; `callable` / `custom` → no decode, encode-only). Malformed base64 / non-`type:id` input (Strawberry's `GlobalIDValueError` / `ValueError`), an unresolvable label, or a strategy-forbidden shape all raise [`ConfigurationError`][glossary-configurationerror] (one uniform decode-failure type, the [`RelatedFilter`][glossary-relation-handling]-style fail-loud message — [`docs/feedback.md`][feedback] P2).
- [x] Encoder/decoder round-trip symmetry tests for the **three decodable strategies** (`model` / `type` / `type+model`; `callable` is encode-only — no decode symmetry); the transitional-mode test proving an old type-anchored ID still decodes while new emitted IDs use the model-label payload (the card DoD's explicit requirement); a [`Meta.name`][glossary-metaname]-renamed `type`-strategy round-trip (`ItemType` with `Meta.name = "Item"` emits `Item:<pk>` and decodes back through the `graphql_type_name` helper); and the **negative** Step-2 cases (a type-name ID rejected by a `model`-strategy type, a model-label ID rejected by a `type`-strategy type, any ID for a `custom`-override type rejected as encode-only); and a malformed-base64 / non-`type:id` input raising [`ConfigurationError`][glossary-configurationerror] (not a leaked `GlobalIDValueError`). The decode helper honors [`Meta.primary`][glossary-metaprimary] (a model-label ID for a multi-type model routes to the primary) — pinned with a multi-`DjangoType` fixture.
- [x] Package coverage: [`tests/types/test_relay_interfaces.py`][test-relay-interfaces] (the one-to-one mirror of [`types/relay.py`][relay] per [`docs/TREE.md`][tree], where the encode / decode lands) covers the `model` / `type` / `type+model` decode paths, the `graphql_type_name` (not `__name__`) lookup, the Step-2 strategy-shape enforcement (both rejection directions plus the `custom` encode-only rejection), the **absent-strategy rejection** (a non-Relay-Node `graphql_type_name` / model-label candidate whose `effective_globalid_strategy` is `None`), the malformed-input `ConfigurationError`, the primary-routing rule, and the unresolvable-label `ConfigurationError`. [`registry.definition_for_graphql_name`][registry] coverage (Relay-only scan + ambiguity) lands in [`tests/test_registry.py`][test-registry].

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/relay.py` — (1) added `TYPE_NAME_STRATEGIES =
  frozenset({"type", "type+model"})` as a sibling of `MODEL_LABEL_STRATEGIES` plus the
  `_accepts_type_name_decode(effective_strategy)` predicate next to
  `_accepts_model_label_decode`; extended the source-of-truth comment to name both
  memberships and to state that `callable`/`custom`'s "no decode" contract IS their
  absence from both sets (no `{"callable","custom"}` literal). (2) Added `from
  django.apps import apps` to the django-import block. (3) Replaced the decode TODO with
  `decode_global_id(gid) -> tuple[type, str]`: the runtime input-type gate, the
  `relay.GlobalID.from_id` parse (catching `ValueError`), empty-slot rejection, the
  Step-1 dot-vs-no-dot candidate resolution (model-label via `apps.get_model` →
  `registry.get`; type-name via `registry.definition_for_graphql_name`), and the Step-2
  shape enforcement reading the recorded `effective_globalid_strategy` through the two
  named predicates. `registry` is reached in-function (cycle-dodge).
- `django_strawberry_framework/registry.py` — replaced the `definition_for_graphql_name`
  TODO with the method: in-function `implements_relay_node` import, a list comprehension
  over `iter_definitions()` filtering on Relay-Node shape AND `graphql_type_name == name`,
  returning the lone match or raising `ConfigurationError` on miss / ambiguity (the
  ambiguity message names the colliding `origin.__name__`s).
- `django_strawberry_framework/filters/base.py` — the planned DRY consolidation: added
  `TYPE_NAME_STRATEGIES` to the existing module-top `from ..types.relay import
  MODEL_LABEL_STRATEGIES` and swapped the bare tuple `if strategy in ("type",
  "type+model"):` at `_accepted_globalid_type_names` to `if strategy in
  TYPE_NAME_STRATEGIES:`. Behavior-preserving (same membership), single-sourced.
- `tests/test_registry.py` — replaced the Slice-3 TODO with five
  `definition_for_graphql_name` tests (returns-match, honors-`Meta.name`,
  ignores-non-Relay, unknown-miss, ambiguous) using real finalized `DjangoType`s on the
  autouse-cleared global registry.
- `tests/types/test_relay_interfaces.py` — added `decode_global_id` to the
  `types.relay` import block; appended the Slice-3 decode test section (19 test
  functions counting parametrizations) plus two local helpers (`_emitted_type_name_slot`,
  `_encoded_id`) reusing the Slice-2 `_emitted_typename` / `_definition_of` /
  `_build_multi_type` scaffolding.

### Tests added or updated

- `tests/test_registry.py::test_definition_for_graphql_name_returns_match` — a registered
  Relay-Node type's `graphql_type_name` resolves to its definition.
- `::test_definition_for_graphql_name_honors_meta_name` — keyed on `graphql_type_name`
  (`Meta.name = "Item"` resolves via `"Item"`; the class name `"ItemNode"` misses).
- `::test_definition_for_graphql_name_ignores_non_relay_definitions` — a non-Relay-Node
  `DjangoType` with a matching name is not returned (Relay-only scan → miss).
- `::test_definition_for_graphql_name_unknown_raises` — an unregistered name raises.
- `::test_definition_for_graphql_name_ambiguous_raises` — two Relay-Node definitions
  (on `Category` / `Item`) sharing `Meta.name = "Dup"` raise naming both colliders.
- `tests/types/test_relay_interfaces.py::test_decode_model_label_routes_to_primary` —
  `GlobalID("products.item", "42")` → `(PrimaryType, "42")` via a `model`-primary +
  `type`-secondary multi-`DjangoType` fixture (primary-routing + `Meta.primary`).
- `::test_decode_type_name_routes_via_graphql_name` — a `type`-strategy type-name payload
  resolves via `definition_for_graphql_name`.
- `::test_decode_type_strategy_honors_meta_name_round_trip` — `ItemType` with `Meta.name
  = "Item"` emits `Item` in the slot and decodes back to `ItemType`.
- `::test_encode_decode_round_trip_decodable_strategies[model|type|type+model]` —
  encode→decode symmetry for the three decodable strategies (parametrized).
- `::test_type_plus_model_decodes_both` — `type+model` decodes BOTH a new model-label ID
  and an old type-anchored ID (the transitional accept-old-IDs path).
- `::test_decode_model_strategy_rejects_type_name_id` /
  `::test_decode_type_strategy_rejects_model_label_id` — both Step-2 rejection directions.
- `::test_decode_callable_strategy_has_no_decode_path` /
  `::test_decode_custom_override_type_has_no_decode_path` — `callable` / `custom`
  encode-only rejection.
- `::test_decode_non_node_graphql_name_raises` — absent-`None` strategy rejection
  (a non-Relay-Node `DjangoType`).
- `::test_decode_malformed_base64_raises_configuration_error` — malformed base64 surfaces
  `ConfigurationError`, not a leaked `GlobalIDValueError`.
- `::test_decode_non_str_input_raises[None|42|object|bytes]` — the runtime input-type gate
  (parametrized).
- `::test_decode_empty_type_name_raises` / `::test_decode_empty_node_id_raises` — the
  package-added empty-slot rejection.
- `::test_decode_unresolvable_label_raises` — unknown app/model label names the attempt.
- `::test_decode_model_label_unregistered_model_raises` — a real model with no registered
  Relay-Node type raises `no registered` (the `registry.get(model) is None` branch).

### Validation run

- `uv run ruff format .` — pass (235 files unchanged; the standing COM812-vs-formatter
  warning is pre-existing config noise, not introduced here).
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- `git status --short` after both ruff invocations — modified files:
  - **Slice-3-intended (my diff):** `django_strawberry_framework/types/relay.py`,
    `django_strawberry_framework/registry.py`,
    `django_strawberry_framework/filters/base.py`, `tests/test_registry.py`,
    `tests/types/test_relay_interfaces.py`.
  - **Cumulative Slice 1 + Slice 2 accepted diff (workers never commit — EXPECTED, NOT
    churn, not reverted):** `django_strawberry_framework/types/base.py`,
    `django_strawberry_framework/types/definition.py`,
    `django_strawberry_framework/types/finalizer.py`,
    `django_strawberry_framework/filters/inputs.py`, `tests/types/test_base.py`,
    `tests/filters/test_base.py`. (The `git diff` of `filters/base.py` /
    `test_relay_interfaces.py` / `registry.py` / `test_registry.py` shows BOTH my Slice-3
    hunks and prior-slice hunks because the working tree is diffed against the committed
    `archive 030` HEAD, which predates Slices 1–2.)
  - **Tracked build-cycle artifacts:** `docs/builder/bld-slice-{1,2,3}-*.md`,
    `docs/builder/build-031-globalid_encoding-0_0_9.md` (untracked/new — the maintainer
    commits with the build).
  - No unrelated tool churn to revert.
- Focused tests (no `--cov*`): `uv run pytest --no-cov tests/types/test_relay_interfaces.py
  tests/filters/test_base.py` → **165 passed**; `uv run pytest --no-cov tests/test_registry.py
  -k definition_for_graphql_name` → **5 passed**. The filter suite passing unchanged
  confirms the bare-tuple→`TYPE_NAME_STRATEGIES` swap is behavior-preserving.
  **One pre-existing failure is NOT mine** — see Notes for Worker 1.

### Implementation notes

- **`decode_global_id` carries the slot shape forward** (`is_model_label = "." in
  type_name`, computed once in Step 1) rather than re-testing `"." in type_name` in Step 2
  — Worker 1 left this to discretion; carrying it is fewer string ops and keeps the
  Step-2 predicate choice (`_accepts_model_label_decode` vs `_accepts_type_name_decode`)
  in one ternary.
- **Model-label resolve uses the split form** `apps.get_model(app_label, model_name)`
  after `type_name.split(".", 1)` (Worker-1 discretion item) — the explicit two-arg form
  reads more clearly than the dotted single-arg form; both raise `LookupError`, caught and
  re-raised as `ConfigurationError`.
- **`definition_for_graphql_name`'s `ConfigurationError` is allowed to propagate** out of
  `decode_global_id` (Worker-1 discretion) — no redundant wrap, since both surface
  `ConfigurationError`; the no-dot branch is a one-liner.
- **Registry tests use real finalized `DjangoType`s on the global registry** (Worker-1
  discretion) rather than hand-constructing `DjangoTypeDefinition` instances — the
  dataclass has ~10 required fields, so real types read far cleaner and exercise the real
  `graphql_type_name` property and Relay shape. The ambiguity fixture uses two types on
  DIFFERENT models (`Category` / `Item`) with the same `Meta.name = "Dup"` to avoid
  tripping the Slice-2 multi-type model-label-routing audit.
- **`_emitted_type_name_slot` test helper** — the `type` strategy installs no closure (it
  keeps Strawberry's default `resolve_typename`, which reads `info.path.typename`), so the
  Slice-2 `_emitted_typename(type_cls)` helper (which passes `info=None`) raises
  `AttributeError` for `type`-strategy types. The new helper returns
  `definition.graphql_type_name` for the `type` strategy and delegates to
  `_emitted_typename` for the closure strategies, so the round-trip tests build the
  emitted slot correctly for all three decodable strategies.

### Notes for Worker 3

- No shadow file was used (the plan did not require one; `decode_global_id` is ~35 logic
  lines added to `relay.py`, and `definition_for_graphql_name` is a small comprehension).
- The decode round-trip tests build encoded `GlobalID`s via `str(relay.GlobalID(slot,
  node_id))` / `relay.GlobalID(slot, node_id)`, never a raw `"app.model:pk"` payload (per
  the plan's Worker-3 checklist item (a)).
- BOTH Step-2 rejection directions are exercised
  (`test_decode_model_strategy_rejects_type_name_id` +
  `test_decode_type_strategy_rejects_model_label_id`), and the absent-`None` /
  malformed-input / non-`str` paths all assert `ConfigurationError` (no leaked
  `KeyError`/`ValueError`/`AttributeError`) — checklist items (b) and (c).
- I did NOT add the optional `filters.base.TYPE_NAME_STRATEGIES is
  relay.TYPE_NAME_STRATEGIES` identity check — the existing Slice-2 filter suite passing
  unchanged already proves the swap is behavior-preserving, and the import is a direct
  re-export (same frozenset object). If Worker 3 wants the explicit single-source
  assertion, it is a one-liner mirroring the Slice-2 `MODEL_LABEL_STRATEGIES` check.

### Notes for Worker 1 (spec reconciliation)

- **Pre-existing Slice-2 test failure, NOT introduced by Slice 3 — needs a Slice-2 fix
  decision.** `tests/test_registry.py::test_audit_runs_once_per_build` fails (`assert 2 ==
  1`) on the current working tree, independent of every file I touched. Root cause: Slice
  2 added a SECOND caller of `registry.models_with_multiple_types()` in
  `types/finalizer.py` — the model-label-routing audit (`finalizer.py:200`) alongside the
  pre-existing `_audit_primary_ambiguity` (`finalizer.py:139`). This Slice-2 test spies on
  `models_with_multiple_types` and asserts exactly ONE call across two `finalize_django_types()`
  calls; with two audit callers per finalize, the correct post-Slice-2 count is **2**, not
  1. I verified it fails in isolation (`uv run pytest --no-cov
  tests/test_registry.py::test_audit_runs_once_per_build` → `assert 2 == 1`) and that my
  Slice-3 diff touches neither `finalizer.py` nor this test. This is structural drift in a
  prior slice surfaced during Slice 3; per worker-2.md I did NOT edit it (out of my slice
  contract, and the fix is a judgment call: bump the test to `== 2`, OR consolidate the two
  audit-loop iterations of `models_with_multiple_types()` into one shared walk). Flagging
  for Worker 1 / the Slice-2 owner to resolve — the final test-run gate will otherwise trip
  on it.

---

## Review (Worker 3)

Reviewed the Slice-3 contribution only, using the cumulative-diff filter (`git diff
-- django_strawberry_framework/ tests/` split by Worker 2's `### Files touched`).
Slice-3-only: the new `registry.py::definition_for_graphql_name` + its tests in
`tests/test_registry.py`. Mixed (Slice-3 additions reviewed only): `types/relay.py`
(`TYPE_NAME_STRATEGIES` + `_accepts_type_name_decode` + `decode_global_id` + the `from
django.apps import apps` import), `tests/types/test_relay_interfaces.py` (the decode
test block at test_relay_interfaces.py:1773-1992), `filters/base.py` (the bare-tuple →
`TYPE_NAME_STRATEGIES` swap at `_accepted_globalid_type_names`). Slice-1/2-only files
(`types/base.py`, `types/definition.py`, `types/finalizer.py`, `filters/inputs.py`,
`tests/types/test_base.py`, `tests/filters/test_base.py`, and the Slice-2 encode test
block at test_relay_interfaces.py:1405-1771) were treated as already-accepted context
and not re-reviewed.

Static inspection helper (REQUIRED — slice touches `types/` and adds logic to
`registry.py`): ran both with `--output-dir docs/shadow`:
- `uv run python scripts/review_inspect.py django_strawberry_framework/types/relay.py --output-dir docs/shadow`
- `uv run python scripts/review_inspect.py django_strawberry_framework/registry.py --output-dir docs/shadow`

Shadow walk findings:
- **Control-flow hotspots.** `decode_global_id` (relay.py:560) is flagged a hotspot
  (114 lines / 15 branch nodes). The 114 "lines" are dominated by the long contract
  docstring; the executable body is ~50 lines and every branch maps 1:1 to a
  spec-mandated failure mode (input gate, parse / `ValueError`, empty-slot, dot-vs-no-dot
  Step 1, `LookupError`, `registry.get` `None`, absent-`None` strategy, the
  shape-permitted enforcement). The branch count is inherent to the resolve-then-enforce
  contract (spec Decision 8, error shapes spec lines 264-267), not accidental complexity
  — Medium-tier attention applied, no finding. `definition_for_graphql_name`
  (registry.py:319) spans 42 lines / 3 branches (exactly-one / zero / two-or-more) —
  clean.
- **Django/ORM markers.** `decode_global_id` uses `apps.get_model(app_label,
  model_name)` (a single in-memory Django app-registry lookup, NOT a query — no N+1) with
  `LookupError` caught and re-raised as `ConfigurationError` (verified). `registry.get` /
  `registry.get_definition` / `definition_for_graphql_name` are all in-memory dict reads
  over `iter_definitions()` — no DB work introduced. `definition.model._meta.label_lower`
  is not re-derived in decode (decode never formats a label; it splits the incoming
  `type_name`). N+1-free.
- **Repeated string literals.** relay.py reports `2x type+model` (the two frozenset
  definitions `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` — the single-source-of-truth
  definitions themselves, not duplication) and `3x decode_global_id:` (the error-message
  function-name prefix, idiomatic). registry.py reports `None`. No duplicated strategy
  literal set — confirmed `{"type", "type+model"}` is now spelled exactly once
  (`TYPE_NAME_STRATEGIES` at relay.py:386) and consumed by both the decoder and the
  filter.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **The Slice-2 carry-forward DRY note is fully resolved.** My Slice-2 review left one
  Low, non-blocking note (carried into worker-3 memory and Worker-1 memory): the
  graphql-name-acceptance membership was a bare tuple `("type", "type+model")` at
  `filters/base.py::_accepted_globalid_type_names`, and Slice 3's decode Step-2 would need
  the same notion. Slice 3 lands exactly the recommended consolidation:
  `TYPE_NAME_STRATEGIES = frozenset({"type", "type+model"})` is defined once at the
  `types/relay.py` source of truth (relay.py:386, sibling of the Slice-2
  `MODEL_LABEL_STRATEGIES`), and is consumed by BOTH `decode_global_id`'s no-dot Step-2
  branch (via `_accepts_type_name_decode`, relay.py) AND
  `filters/base.py::_accepted_globalid_type_names` (filters/base.py:245, `if strategy in
  TYPE_NAME_STRATEGIES:`). The bare tuple is gone. The filter's two membership branches
  (filters/base.py:243 `MODEL_LABEL_STRATEGIES` / filters/base.py:245 `TYPE_NAME_STRATEGIES`)
  are now symmetric and both single-sourced. Confirmed the module-top import
  `from ..types.relay import MODEL_LABEL_STRATEGIES, TYPE_NAME_STRATEGIES` (filters/base.py:46)
  binds the same frozenset objects (re-export, not a copy), preserving the Slice-2
  `is`-identity property. No parallel literal set survives anywhere.
- **`callable` / `custom` "no decode" falls out of predicate math — no third literal.**
  Verified there is no `{"callable", "custom"}` literal anywhere in the Slice-3 diff. A
  `callable`- or `custom`-strategy candidate is in neither `MODEL_LABEL_STRATEGIES` nor
  `TYPE_NAME_STRATEGIES`, so its payload is permitted by neither predicate → uniform
  rejection. The absence-from-both-sets IS the encode-only contract (spec line 408). The
  source-of-truth comment (relay.py:380-384) states this explicitly; the
  `test_decode_callable_strategy_has_no_decode_path` /
  `test_decode_custom_override_type_has_no_decode_path` tests pin it.
- **Decode reuses recorded outputs, not re-implementations.** `decode_global_id` reads
  the recorded `definition.effective_globalid_strategy` (Slice 2's finalization stamp) and
  does NOT re-call `_resolve_globalid_strategy` (which would re-run precedence and could
  not tell a preserved `custom` override from the framework closure) — the spec's explicit
  DRY rule (spec Revision 5, Decision 8 Step 2). Step-1 reuses `apps.get_model` /
  `registry.get` / `registry.get_definition` / `registry.definition_for_graphql_name` /
  `implements_relay_node` rather than re-deriving any of them. No hand-rolled label parse
  (it splits the incoming `type_name`, never re-formats `f"{app}.{model}"`).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty (no `__all__` / re-export
change). Confirmed neither `decode_global_id` nor `definition_for_graphql_name` is added
to `__all__` — both are internal forward-looking helpers `WIP-ALPHA-032-0.0.9` will
consume (spec Decision 8 / Decision 11; spec line 418 "the forward-looking piece … no
shipped `0.0.9` path requires it"). No public-export drift.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Spec-checklist boxes all truly landed.** Walked every `- [x]` in the Plan's `### Spec
  slice checklist (verbatim)`:
  - Box 1 (`definition_for_graphql_name`): scans `iter_definitions()`, filters on
    `implements_relay_node(type_cls)` AND `definition.graphql_type_name == name` (keyed on
    `graphql_type_name`, NOT `__name__`), returns the unique match, raises
    `ConfigurationError` on miss (names the name) and on ambiguity (names both colliders).
    Landed exactly.
  - Box 2 (`decode_global_id`): input gate first → `relay.GlobalID.from_id` parse catching
    `ValueError` → empty-slot rejection → Step-1 dot/no-dot resolution → Step-2 recorded-
    strategy enforcement → uniform `ConfigurationError`. Landed exactly.
  - Box 3 (round-trip + transitional + Meta.name + negatives + malformed): every named test
    present.
  - Box 4 (package coverage placement): decode paths in `test_relay_interfaces.py`,
    `definition_for_graphql_name` in `test_registry.py`. Correct per `docs/TREE.md` mirror.
- **Resolve-then-enforce dispatch matches Decision 8 precisely.** Step 1 resolves the
  candidate from the slot shape (`is_model_label = "." in type_name`, computed once and
  carried forward — Worker-2 discretion, clean), Step 2 reads the recorded
  `effective_globalid_strategy` and applies the one matching predicate. The absent-`None`
  rejection (relay.py, before the predicate test) is belt-and-suspenders with the
  Relay-only scan and pinned by `test_decode_non_node_graphql_name_raises`.
- **Uniform `ConfigurationError` contract verified end-to-end.** Confirmed against
  installed strawberry that `GlobalIDValueError ⊂ ValueError` (so catching `ValueError`
  covers it), that `from_id` does NOT reject empty slots (so the package-added empty-slot
  checks are genuinely necessary, not redundant), and that malformed input raises a
  `ValueError` subclass. Every failure path (`test_decode_non_str_input_raises[None|42|object|bytes]`,
  malformed, empty-`type_name`, empty-`node_id`, unresolvable-label, unregistered-model,
  absent-strategy, both Step-2 rejection directions, callable, custom) asserts
  `ConfigurationError` with no leaked `KeyError`/`ValueError`/`AttributeError`/`TypeError`.
- **Primary-routing pinned with a real multi-type fixture.** `test_decode_model_label_routes_to_primary`
  uses `_build_multi_type(primary_strategy="model", secondary_strategy="type")` (primary
  carries `Meta.primary = True`), so `registry.get(Item)` returns the primary
  deterministically and the model-label-routing invariant is satisfied (primary accepts
  model-label decode). Genuine `Meta.primary` exercise, not a single-type shortcut.
- **Round-trip tests build encoded `GlobalID`s, never raw payloads.** `_encoded_id`
  base64-wraps the emitted slot via `str(relay.GlobalID(slot, node_id))`; the
  `_emitted_type_name_slot` helper correctly returns `graphql_type_name` for the `type`
  strategy (which installs no closure) and delegates to `_emitted_typename` for the closure
  strategies — so the symmetry tests exercise the true emit path for all three decodable
  strategies. Worker-3 checklist items (a)/(b)/(c) from the plan all satisfied.
- **The in-function `registry` / `implements_relay_node` imports** (relay.py decode →
  `from ..registry import registry`; registry.py `definition_for_graphql_name` →
  `from .types.relay import implements_relay_node`) correctly dodge the
  `registry`↔`relay` module-load coupling, matching the established cycle-dodge convention.
  Both are decode-time calls (well after module load), so the local imports resolve
  cheaply. No new module-top cross-folder import was introduced.
- **Filter swap is behavior-preserving.** `tests/filters/test_base.py` (the Slice-2
  strategy-aware suite, 59 tests) passes unchanged after the bare-tuple →
  `TYPE_NAME_STRATEGIES` swap — confirming the consolidation added no filter behavior.

### Temp test verification

- No temp tests created. Every Slice-3 branch is package-internal and directly covered by
  a permanent test in `tests/types/test_relay_interfaces.py` / `tests/test_registry.py`;
  the reading-driven gap walk (spec Decision 8 behaviors vs diff branches vs test
  assertions) found no uncovered branch, so no temp test was needed to prove a suspicion.
- Behavior confirmed directly against the installed strawberry via a one-off interpreter
  check (NOT a temp test file): `GlobalIDValueError ⊂ ValueError`, `from_id` parses empty
  slots without raising, malformed input raises a `ValueError` subclass. This validates the
  package-added empty-slot checks and the `except ValueError` spelling.

### Notes for Worker 1 (spec reconciliation)

- **Confirmed cross-slice regression to route to the integration pass (NOT a Slice-3
  defect):** `tests/test_registry.py::test_audit_runs_once_per_build` fails (`assert 2 ==
  1`). Verified by running the full `tests/test_registry.py` (no `--cov`): `1 failed, 67
  passed`. Root cause is **Slice-2-owned**: Slice 2's model-label-routing audit
  (`finalizer.py::_audit_model_label_routing`, finalizer.py:200) added a SECOND
  `registry.models_with_multiple_types()` caller per finalize, alongside the pre-existing
  `_audit_primary_ambiguity` (finalizer.py:139); this Slice-2 test spies on
  `models_with_multiple_types` and asserts exactly ONE call across two
  `finalize_django_types()` invocations, so the correct post-Slice-2 count is now 2.
  Verified the Slice-3 diff touches NEITHER `finalizer.py` NOR this test (`git diff --
  tests/test_registry.py` shows zero hunks naming `test_audit_runs_once_per_build`; the
  Slice-3 `### Files touched` lists `registry.py` only for the unrelated
  `definition_for_graphql_name` addition). Slice 3's decode/registry-lookup contract is
  independent of the audit-call-count, so this does NOT block Slice-3 acceptance. Routing
  to the integration pass for the Slice-2 owner to resolve (bump the assertion to `== 2`,
  OR consolidate the two audit loops into one shared `models_with_multiple_types()` walk —
  the consolidation is the more DRY shape and would be the recommended root-cause fix per
  `AGENTS.md`). The final test-run gate will otherwise trip on it.
- No spec ambiguity surfaced during this review. Decision 8 / the Slice-3 checklist / the
  Test plan all map cleanly onto the diff; no spec edit is implied by Slice 3.

### Review outcome

`review-accepted`. Every spec-required Slice-3 behavior (`definition_for_graphql_name`
unique-Relay-Node lookup + miss/ambiguity raises; `decode_global_id` input-gate + parse +
empty-slot + resolve-then-enforce + uniform `ConfigurationError`; the
`TYPE_NAME_STRATEGIES` DRY consolidation consumed by both the decoder and the filter) is
reflected in the diff and pinned by a test. No High / Medium / Low findings. The
carried-forward Slice-2 DRY note is resolved exactly as recommended. The flagged
`test_audit_runs_once_per_build` regression is a Slice-2-owned cross-slice issue routed to
the integration pass and is NOT counted as a Slice-3 defect.

---

## Final verification (Worker 1)

Final-verification pass on the cumulative Slice 1+2+3 working tree (workers never commit).
Audited ONLY the Slice-3 contract: Slice-3-only `registry.py::definition_for_graphql_name`
+ `tests/test_registry.py` lookup tests; mixed-file Slice-3 additions in `types/relay.py`
(`TYPE_NAME_STRATEGIES`, `_accepts_type_name_decode`, `decode_global_id`, the
`from django.apps import apps` import), `tests/types/test_relay_interfaces.py` (decode
block), and `filters/base.py` (the bare-tuple → `TYPE_NAME_STRATEGIES` swap). Slice-1/2-only
files were treated as already-accepted context (verified against the Slice-1 / Slice-2
`final-accepted` artifacts) and not re-audited.

### Spec slice checklist audit

Walked every `- [x]` in the Plan's `### Spec slice checklist (verbatim)` against the actual
diff. All four boxes truly landed — no over-tick, no silent un-tick, no remaining `- [ ]`,
no deferral needed:

- **Box 1 — `registry.py::definition_for_graphql_name(name)`** (registry.py:319-360): a
  list comprehension over `iter_definitions()` filtered by `implements_relay_node(type_cls)`
  AND `definition.graphql_type_name == name` (keyed on `graphql_type_name`, NOT `__name__` —
  honors `Meta.name`); returns the unique match; raises `ConfigurationError` on miss
  (names the name) and on ambiguity (names the sorted colliders). `implements_relay_node`
  imported in-function (cycle-dodge). Relay-Node scan only. **Landed exactly.**
- **Box 2 — `decode_global_id(gid: relay.GlobalID | str)`** (relay.py:560-673): runtime
  input-type gate first (relay.py:609); `relay.GlobalID.from_id` parse catching `ValueError`
  (relay.py:616-622); package-added empty-slot rejection (relay.py:628-632); Step-1 dot vs
  no-dot resolution (model-label via `apps.get_model` → `registry.get`; type-name via
  `definition_for_graphql_name`); Step-2 enforcement reading the **recorded**
  `effective_globalid_strategy` (relay.py:655) through `_accepts_model_label_decode` /
  `_accepts_type_name_decode`, with the absent-`None` rejection (relay.py:656-660). One
  uniform `ConfigurationError` for every failure path. `registry` reached in-function.
  **Landed exactly.**
- **Box 3 — round-trip symmetry + transitional `type+model` + `Meta.name` + negatives +
  malformed:** every named test present in `tests/types/test_relay_interfaces.py` (decode
  block), including both Step-2 rejection directions, `callable`/`custom` encode-only
  rejection, absent-`None`, malformed input, primary-routing via a real multi-`DjangoType`
  fixture, and the transitional accept-old-IDs path. Round-trips build encoded `GlobalID`s,
  never raw payloads. **Landed exactly.**
- **Box 4 — package-coverage placement:** decode paths in `tests/types/test_relay_interfaces.py`
  (the `types/relay.py` mirror per `docs/TREE.md`); `definition_for_graphql_name` coverage
  (Relay-only scan + miss + ambiguity) in `tests/test_registry.py`. **Correct placement.**

### DRY check across Slices 1-3

- **`TYPE_NAME_STRATEGIES` is single-sourced at `types/relay.py:386`** and consumed by BOTH
  `decode_global_id` (via `_accepts_type_name_decode`, relay.py:664) AND
  `filters/base.py::_accepted_globalid_type_names` (filters/base.py:245, importing it at
  filters/base.py:44). The Slice-2 bare tuple `("type", "type+model")` is **gone** — grep
  confirms no surviving `("type", "type+model")` / `{"type", "type+model"}` literal outside
  the single `frozenset` definition.
- **`MODEL_LABEL_STRATEGIES` / `_emits_model_label` / `_accepts_model_label_decode` and
  `effective_globalid_strategy` are reused, not re-created.** Decode reads the recorded
  `effective_globalid_strategy` field directly (relay.py:655) — it does NOT re-call
  `_resolve_globalid_strategy` (the spec's explicit DRY rule, Revision 5 / Decision 8 Step 2).
- **No `{"callable", "custom"}` literal anywhere** (grep-confirmed; only the documentation
  comment at relay.py:384 names it to state the contract). `callable`/`custom`/`None`
  rejection falls out of neither-membership predicate math, exactly as planned.
- No parallel literal strategy sets; the two memberships (`MODEL_LABEL_STRATEGIES`,
  `TYPE_NAME_STRATEGIES`) plus the Slice-1 `STRING_GLOBALID_STRATEGIES` (a distinct
  valid-string concept) are each named once.

### Existing tests still pass (focused, Slice-3 scope)

`uv run pytest tests/types/test_relay_interfaces.py tests/test_registry.py tests/filters/test_base.py --no-cov`
→ **1 failed, 232 passed**. The single failure is
`tests/test_registry.py::test_audit_runs_once_per_build` (`assert 2 == 1`) — the **routed
Slice-2 regression** (see below), NOT a Slice-3 failure. Slice 3's own contract tests all
pass: the focused `-k "decode or definition_for_graphql_name"` run → **26 passed** (21 decode
tests in `test_relay_interfaces.py` + 5 `definition_for_graphql_name` tests in
`test_registry.py`). The `tests/filters/test_base.py` Slice-2 strategy-aware suite passes
unchanged, confirming the bare-tuple → `TYPE_NAME_STRATEGIES` swap is behavior-preserving.
(`--no-cov` is required — `pytest.ini` auto-applies `--cov`; this was NOT a coverage run.)

### Disposition of the routed Slice-2 regression (cross-slice reconciliation)

`tests/test_registry.py::test_audit_runs_once_per_build` fails `assert 2 == 1`. This is a
**Slice-2-owned cross-slice consolidation question, NOT a Slice-3 defect** — verified the
Slice-3 diff touches neither `finalizer.py` nor this test. **It does NOT block Slice-3
acceptance** (Slice 3's decode + `definition_for_graphql_name` contract is independent of the
audit call count and is complete + green). Formally ROUTED to the cross-slice integration
pass:

- **(a) Confirmed root cause.** Slice 2 added a SECOND `registry.models_with_multiple_types()`
  caller per finalize: `finalizer.py::_audit_model_label_routing` (finalizer.py:200) walks it
  alongside the pre-existing Phase-1 `finalizer.py::_audit_primary_ambiguity`
  (finalizer.py:139). The test spies on `models_with_multiple_types` and asserts exactly ONE
  call across two `finalize_django_types()` invocations (the second short-circuits on
  `is_finalized()`); with two audit callers per finalize, the post-Slice-2 count is 2.
- **(b) Recommended root-cause fix (per `AGENTS.md` "always recommend the root-cause fix over
  the surface patch").** Assess whether the two audits can share ONE
  `models_with_multiple_types()` walk. They genuinely can — and SHOULD: both
  `_audit_primary_ambiguity` (Phase 1) and `_audit_model_label_routing` (Phase 2.5) iterate
  the SAME `registry.models_with_multiple_types()` set, and for multi-type models Phase 1 has
  already guaranteed a primary exists, which Phase 2.5 relies on. The **preferred** fix is to
  have the two audits share a single materialized `models_with_multiple_types()` walk
  (e.g. compute the multi-type-model list once per finalize and pass/share it to both audit
  helpers, or fold both per-model checks into one loop body), which **preserves the test's
  "once per build" invariant** (`== 1`) — that invariant is correct and worth keeping
  (one finalize = one registry walk). Only if a single shared walk proves genuinely
  infeasible (it is not, here) would the fallback be to update the test's invariant to `== 2`;
  that is the surface patch and should NOT be the chosen path. Note the two audits run in
  different phases (Phase 1 pre-pending-resolution for failure-atomicity, Phase 2.5
  post-strategy-recording), so the consolidation must preserve the phase ordering — share the
  *walk result* / the multi-type-model set across the two phase checks rather than physically
  merging the two raises into one call site.
- **(c) Ownership.** The cross-slice **integration pass** owns implementing this consolidation
  (dispatch Worker 2 + Worker 3 from `bld-integration.md`); the **final test-run gate**
  (`uv run pytest --no-cov` full sweep in `bld-final.md`) is the backstop that will trip on
  the failing test until the consolidation lands. Carried into worker-1 memory as a must-do
  for the integration pass so it cannot be lost.

### Spec reconciliation

No spec edit made. Slice 3 landed exactly as specced (Decision 8 / the Slice-3 checklist /
DoD item 5 all map cleanly onto the diff). Per-spawn status/header re-verification (Worker-1
role rule): the spec `Status:` / header (spec line 3-5) is the **intentional contract record**
(spec line 5: the Slice checklist "stays unticked as the contract record"), NOT a build
tracker — it is correctly left unticked and is not stale relative to the build. `__init__.py`
is unchanged (Decision 11: no public export in `0.0.9`) — confirmed.

### Summary

Slice 3 ships the **decode** half of the GlobalID-encoding feature: `registry.py` gains
`definition_for_graphql_name` (the unique Relay-Node `graphql_type_name` decode entry point,
keyed on the GraphQL name so `Meta.name`-renamed types round-trip), and `types/relay.py` gains
`decode_global_id` (the resolve-then-enforce dispatch: input gate → parse → empty-slot
rejection → Step-1 dot/no-dot candidate resolution → Step-2 recorded-strategy enforcement →
one uniform `ConfigurationError`). The planned Slice-2 carry-forward DRY consolidation landed:
`TYPE_NAME_STRATEGIES` is single-sourced at `types/relay.py` and now consumed by both the
decoder and the strategy-aware filter (the bare tuple is gone). All four verbatim checklist
boxes truly landed; all 26 Slice-3-own tests pass. The one failing test
(`test_audit_runs_once_per_build`) is a Slice-2-owned cross-slice regression, routed to the
integration pass with a recommended root-cause fix (share one `models_with_multiple_types()`
walk across the two audits, preserving the `== 1` invariant). No Slice-3-caused failure, no
DRY violation, no spec gap.

### Spec changes made (Worker 1 only)

None. The spec needed no edit for Slice 3 — the decode contract landed exactly as Decision 8
/ DoD item 5 specify, and the spec `Status:` / Slice-checklist header is the intentional
unticked contract record (spec line 5), not a stale build tracker.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[feedback]: ../feedback.md
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-metaname]: ../GLOSSARY.md#metaname
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-relatedfilter]: ../GLOSSARY.md#relatedfilter
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[definition]: ../../django_strawberry_framework/types/definition.py
[registry]: ../../django_strawberry_framework/registry.py
[relay]: ../../django_strawberry_framework/types/relay.py

<!-- tests/ -->
[test-registry]: ../../tests/test_registry.py
[test-relay-interfaces]: ../../tests/types/test_relay_interfaces.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
