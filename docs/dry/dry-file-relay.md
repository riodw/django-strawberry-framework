# DRY review: `django_strawberry_framework/relay.py`

Status: verified

## System trace

The root Relay refetch surface. `DjangoNodeField` / `DjangoNodesField` are factory functions returning
`strawberry.field(resolver=...)` values that Strawberry's class-body walk picks up (spec-032 Decisions
3/4/5/11). Rules owned here:

- **Decode boundary** (`_decode_or_graphql_error`): every `ConfigurationError` from
  `types/relay.py::decode_global_id` becomes `GraphQLError("Invalid GlobalID: ...",
  extensions={"code": "GLOBALID_INVALID"})`; scope wraps the decode call ONLY so a dispatch-time
  `SyncMisuseError` (a `ConfigurationError` subclass) surfaces as itself.
- **Id-slot coercion** (`_coerce_pk_or_none`, now over `_node_id_slot`): the decoded `node_id`
  coerces through the concrete field behind `resolved_type.resolve_id_attr()` — not
  `model._meta.pk` unconditionally (the consumer `relay.NodeID[...]` escape hatch) — via the shared
  `utils/querysets.py::coerce_field_value_or_none`; uncoercible → `null` / positional hole, no query.
- **Typed-form check** (`_check_typed_match`): identity on the decoded type; code-less `GraphQLError`.
- **Write-side typed-id primitive** (`GlobalIDDecode` / `DecodeResult` / `_resolve_real_pk` /
  `decode_model_global_id`): the single source of the mutation typed-id contract — consumed by
  `mutations/resolvers.py` (`coerce_lookup_id`, `_decode_relation_id_set`), `forms/resolvers.py`,
  `utils/write_values.py::type_check_relation_id`, `rest_framework/resolvers.py`.
- **Batch mechanics**: per-type grouping, positional holes (`_interleave`), override-shape guard
  (`_check_nodes_result`), decode-routing stamp (`_stamp_node_type`, honored by
  `types/relay.py::install_is_type_of` via `_NODE_TYPE_HINT_ATTR`), sequential-await gather coroutine.
- **Lifecycle**: `_node_fields_declared` ledger appended by both factories, co-cleared via
  `register_subsystem_clear`, read by `types/finalizer.py` for the no-Node-types build check.

Consumers/examined edges: `list_field.py::_validate_relay_djangotype_target` (shared target guards,
also used by `connection.py::DjangoConnectionField`); `connection.py` sibling surface (own pipeline;
shares only the validator, `check_deadline`, `registry` teardown pattern, and queryset primitives);
permissions cascade reaches node resolution inside the `resolve_node(s)` defaults'
`apply_type_visibility_*` (`utils/querysets.py`), not in this module; live usage in
`examples/fakeshop/apps/library/schema.py` (`node` / `nodes` / typed `genre`) covered by
`examples/fakeshop/test_query/test_library_api.py` via `testing/relay.py::global_id_for`;
package-side pins in `tests/test_relay_node_field.py` (query counts, error shapes, synthetic
strategies) and `tests/test_relay_connection.py` (relation-connection synthesis — different concern).
Lockstep sets: the decode error vocabulary spans this module + `types/relay.py` +
`filters/base.py` + docs/tests; the id-slot rule spanned the two relay.py functions until this fix;
the stamp mechanism spans `_stamp_node_type` + `_NODE_TYPE_HINT_ATTR` + `install_is_type_of`.

## Verification

All five axes discharged on the present-day tree (baseline `ec0c512d4c5fd901dd65cd48c956f6ab6ca18848`;
diffs scoped to it):

1. **Cross-flavor policy mirroring** — searched `GLOBALID_INVALID`,
   `decode_model_global_id|GlobalIDDecode`, and `_validate_relay_djangotype_target` across the
   package. Found `filters/base.py::_decode_and_validate_global_id`: its own parse-and-wrap,
   empty-id reject, and pk coercion alongside the node-field path. Disproved as one rule: the
   filter validates against a STATICALLY-known target (mismatch is code-less; uncoercible pk is a
   coded error, not `null`; coerces `_meta.pk` only; must issue no query), while the node field
   dispatches dynamically through the registry keyed on the DECODED candidate (nullable-by-contract;
   coerces the `resolve_id_attr` slot). Merging would flip pinned wire behavior (an unresolvable
   type_name / strategy-forbidden shape becomes `GLOBALID_INVALID` instead of the code-less
   mismatch; empty-id precedence reorders). What is genuinely shared is already single-sited:
   strategy memberships (`filters/base.py` imports `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES`),
   coercion mechanics (`coerce_field_value_or_none`), and write-flavor typed-id decode
   (`decode_model_global_id` imported by all four write flavors — verified by import grep).
2. **Sync and async twins** — read both colors of each resolver. `DjangoNodeField` handles colors
   inline (`in_async_context` → `_await_and_stamp`; sync → `reject_async_in_sync_context`).
   `DjangoNodesField`'s sync loop and `_gather` coroutine share their colorless cores
   (`_check_nodes_result`, `_stamp_node_type`, `_interleave`) and diverge only in the deliberate
   await-vs-reject middle. Posited change "add a required kwarg to the `resolve_nodes` invocation":
   count 2 (one call line per color), adjacency-local within one closure pair with each color
   independently legible — rejected as extraction-without-decision-removal. Connected twins in
   `types/relay.py` (`_resolve_node(s)_default` / `_async`) already share the color-agnostic
   `_apply_node_filter`.
3. **Derived rather than repeated knowledge** — FOUND AND FIXED: the "which concrete column backs
   the Relay id slot" rule (pk special-case → `get_field` → non-concrete fall-through) was spelled
   twice in this module (`_coerce_pk_or_none`, `_resolve_real_pk`), with docstrings explicitly
   acknowledging the mirroring. Also checked `_accepted_globalid_type_names` (derives from the same
   membership constants and name sources as `encode_typename` — one source, no restatement) and
   `_check_typed_match`'s `graphql_type_name` reads (shared definition attribute).
4. **Inverse and round-trip pairs** — encoder (`encode_typename` + installed closure) and decoder
   (`decode_global_id`) are co-located in `types/relay.py` on the shared membership constants;
   `testing/relay.py::global_id_for` mints THROUGH `encode_typename` (its line
   #"payload = encode_typename"), so test-minted ids match live emission by construction; the
   secondary-emitter→primary-decode asymmetry is documented routing, not drift. Posited change
   "change the model-label payload grammar": one module moves. No second grammar exists.
5. **Contracts restated in another medium** — GLOSSARY `DjangoNodeField`/`DjangoNodesField` entries
   and `docs/README.md` restate the wire contracts in prose (the documentation medium — expected and
   kept); tests pin codes/messages (`GLOBALID_INVALID`, `"Invalid GlobalID: "` prefix, mismatch
   fragments) as behavioral pins; CHANGELOG/LIFECYCLE are frozen release records. Nothing
   consolidatable.

Single-edit-site counts: posited "support a NodeID over an FK column / memoize the resolved id-slot
field" forced 2 sites before the fix, 1 after (implemented below). Posited "change how the bare-field
stamp routes `__typename`" came back **1** — `_stamp_node_type` is the sole writer and
`_NODE_TYPE_HINT_ATTR` (imported, not re-declared) the sole wire to the sole reader
(`install_is_type_of`) — independence proved. Posited "reword the malformed-id wire error" counts 3+
production sites (this module, `types/relay.py` message bodies, `filters/base.py`) — real vocabulary
sharing, but the strongest rejected candidate: see axis 1 for why a merge is wrong (different
questions, different error surfaces, different DB posture); the shared parts are already extracted.
No scratch experiments needed: the implemented refactor is statically equivalence-provable and its
branches are pinned by existing tests; pytest remains deferred per AGENTS.md.

## Opportunities

### Implemented — single-site the Relay id-slot resolution (`_node_id_slot`)

- **Repeated responsibility:** "which concrete model field backs this Relay type's GlobalID id
  slot" — `resolve_id_attr()` → `"pk"` maps to `model._meta.pk`, otherwise `model._meta.get_field`,
  non-concrete attr falls through with the raw literal. Stated twice with mirrored
  `FieldDoesNotExist` handling; each docstring cross-referenced the other's fall-through.
- **Sites:** `django_strawberry_framework/relay.py::_coerce_pk_or_none` (READ: needs the field to
  coerce against) and `django_strawberry_framework/relay.py::_resolve_real_pk` (WRITE: needs the
  attr name plus its concreteness before the pk-mapping query).
- **Evidence:** posited change "allow/memoize a new id-slot shape (FK-column NodeID)" or any change
  to the fall-through semantics forced both preambles to move together (count 2); the rule, inputs
  (`resolve_id_attr()`, `_meta`), and outputs coincide.
- **Owner:** this module — the only consumer; `resolve_id_attr()` itself stays owned by
  `types/relay.py`'s stamped default.
- **Consolidation:** new private `_node_id_slot(resolved_type) -> (id_attr, field | None)` states
  the mapping once; `_coerce_pk_or_none` consumes `[1]` (None → raw literal passthrough),
  `_resolve_real_pk` unpacks both (`pk` or None field → value returned unchanged). Behavior
  identical branch-for-branch.
- **Proof:** existing permanent tests cover every helper branch through the public entry points —
  pk default (`test_bare_node_field_resolves_model_label_id`,
  `test_decode_model_global_id_resolves_custom_node_id_to_real_pk`), concrete non-pk NodeID
  (`test_node_custom_node_id_attr_resolves`, `test_decode_model_global_id_resolves_custom_node_id_to_real_pk`,
  `test_node_custom_node_id_attr_uncoercible_returns_null`), non-concrete fall-through
  (`test_coerce_pk_or_none_passes_raw_string_for_non_field_node_id`,
  `test_decode_model_global_id_passes_raw_value_for_non_field_node_id`). No tests deleted; coverage
  gate unaffected. Pytest run deferred (not authorized).
- **Risks / non-goals:** `filters/base.py`'s pk-only coercion and the `types/relay.py` defaults'
  string-keyed filtering are DIFFERENT consumers of `resolve_id_attr()` and deliberately stay out —
  folding them in would couple read coercion, projection, and filter vocabularies that change for
  different reasons.

Other candidates investigated and rejected: filters/node-field decode merge (axis 1 evidence),
batch color-loop extraction (axis 2 count-2-but-legible), factory scaffolding merge (three-line
validate+ledger+`strawberry.field` tail with genuinely divergent resolvers; a mode-flag merge hides
ownership), `testing/relay.py` encode twin (does not exist — it routes through `encode_typename`).

## Judgment

This module is already heavily consolidated at the right boundaries — target validation, coercion
mechanics, strategy memberships, and the write-flavor typed-id decode all route through single
owners, and the encode/decode/test-helper grammar lives in one place. The one genuine restatement was
the id-slot mapping inside this file itself, now single-sited. The remaining cross-flavor similarity
with `filters/base.py` is two different questions wearing the same vocabulary; merging them would
trade pinned wire behavior for fewer lines. One small, behavior-preserving fix implemented; nothing
else warranted.

## Implementation (Worker 1)

- `django_strawberry_framework/relay.py`: added `_node_id_slot`; rewrote `_coerce_pk_or_none` and
  `_resolve_real_pk` onto it; added `from django.db import models` import; docstrings updated to
  name the shared rule instead of describing the mirror. Diff scoped to baseline
  `ec0c512d4c5fd901dd65cd48c956f6ab6ca18848` touches only this file.
- Hygiene: `uv run ruff format .` (no changes), `uv run ruff check --fix .` (all checks passed),
  trailing-comma checker clean, `py_compile` clean.
- Tests: none added/removed (pure consolidation; all branches already permanently covered as listed
  above). `uv run pytest` deferred — not explicitly requested.

## Independent verification (Worker 2)

Independently re-traced against baseline `ec0c512d4c5fd901dd65cd48c956f6ab6ca18848`. Verdict:
**verified**.

- **Scoped diff:** `git diff ec0c512 -- django_strawberry_framework/relay.py` contains exactly the
  described change (+ `from django.db import models`, + `_node_id_slot`, the two caller rewrites,
  docstring updates) and nothing else; `_node_id_slot` appears nowhere else in the tree (grep). The
  other dirty files at review time are concurrent maintainer work, untouched.
- **Equivalence, per input class** (both old bodies read from the diff):
  - *pk slot* (`resolve_id_attr() == "pk"`): READ coerces against `model._meta.pk` before and after
    (same field object reaches `coerce_field_value_or_none`); WRITE returns `coerced_id` unchanged
    with no query before and after. The WRITE side now additionally calls `model_for` on this path
    via the helper — a pure `__django_strawberry_definition__.model` lookup that every caller has
    already evaluated successfully (`decode_model_global_id` guards on it at its model check), so
    no new exception surface.
  - *custom concrete attr*: `get_field` success → identical coercion field (READ) and identical
    `{id_attr: coerced_id}` default-manager lookup incl. the untouched `using`-resolution block
    (WRITE). `model_for` is recomputed inline instead of carried in a local — same pure result.
  - *non-concrete attr* (`FieldDoesNotExist`): READ passes the raw `node_id` literal through in
    both versions; WRITE returns `coerced_id` unchanged with no query in both. Django's
    `get_field` never returns `None` on success (it raises or returns a Field), so the helper's
    `field is None` ⟺ the old caught-branch, exactly.
  - Exception types unchanged: only `FieldDoesNotExist` around `get_field` is caught, in the same
    scope; the swapped evaluation order of `resolve_id_attr()` / `model_for` cannot change which
    exceptions propagate (both unconditional, independent, side-effect-free lookups). No
    `resolved_type=None` class exists — callers always hold a decoded registered type.
  - Raw-literal passthrough preserved at both consumers.
- **Coverage map:** all six proof tests exist in `tests/test_relay_node_field.py` and hit disjoint
  helper branches through public entry points — pk branch: `test_bare_node_field_resolves_model_label_id`
  (:103, live `node(id:)`); `get_field` success: `test_node_custom_node_id_attr_resolves` (:366),
  `test_decode_model_global_id_resolves_custom_node_id_to_real_pk` (:437); uncoercible-on-concrete:
  `test_node_custom_node_id_attr_uncoercible_returns_null` (:403); fall-through→`None`:
  `test_coerce_pk_or_none_passes_raw_string_for_non_field_node_id` (:518),
  `test_decode_model_global_id_passes_raw_value_for_non_field_node_id` (:493). New caller lines:
  `_coerce_pk_or_none`'s `field is None` covered by :518/:493; `_resolve_real_pk`'s pk arm by the
  live `updateItem` HTTP suite (`examples/fakeshop/test_query/test_products_api.py` et al. via
  `coerce_lookup_id`), its `field is None` arm by :493, its query body by :437 plus the no-row case
  :468. Every added line is permanently exercised; `fail_under = 100` unaffected; no tests deleted.
- **Imports:** `models` is referenced by the helper's return annotation (relay.py:123);
  `FieldDoesNotExist` / `model_for` / `coerce_field_value_or_none` all still used. No orphans.
- **Rejected candidates re-probed:** read `filters/base.py::_decode_and_validate_global_id` in
  full (:573-707) — Strawberry-native parse, STATICALLY-resolved target, strategy-aware acceptance,
  coded `GLOBALID_UNVALIDATABLE` backstop, code-less mismatch, empty-id `GLOBALID_INVALID` reject,
  `_meta.pk`-only coercion raising on failure. Different question, different error surfaces,
  different DB posture than the node field's dynamic dispatch + `resolve_id_attr`-slot + nullable
  null; a merge flips pinned wire behavior. Rejection upheld; shared parts already single-sited
  (`MODEL_LABEL_STRATEGIES`/`TYPE_NAME_STRATEGIES` imports, `coerce_field_value_or_none`).
  Axis-4 claim confirmed: `testing/relay.py:109` mints through `encode_typename` — no twin encoder.
- **Matrix:** all five axes re-discharged against the present-day tree (axis 3 = the implemented
  fix; 1/2/4/5 spot-checked in source, not taken from prose).
- **Single-edit-site recount (own posited change):** "memoize the resolved id-slot field per type /
  support an FK-column slot" — post-fix forces exactly one site (`_node_id_slot`; the READ consumer
  reads `[1]`, the WRITE consumer unpacks `(id_attr, field)`); pre-fix it forced both preambles
  (count 2). Recorded count holds.
- Pytest run remains deferred (not authorized).
