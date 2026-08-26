# DRY review: `django_strawberry_framework/keyset.py`

Status: verified

## System trace

`keyset.py` owns the value-encoded stable-cursor grammar behind
`Meta.cursor_field`: the opaque AES-SIV codec (`encode_keyset_cursor` /
`decode_keyset_cursor` over `{"o": fingerprint, "v": [values]}`, prefix
`dstcursor`, `SECRET_KEY_FALLBACKS` rotation), the field-authored value
round-trip (`serialize_cursor_value` via `value_to_string` /
`_deserialize_cursor_value` via `to_python` + re-serialization check), the
order-string syntax owner (`split_order_ref` → `validate_cursor_field_references`,
shared by declaration-time `types/base.py::_validate_cursor_field` and
finalization-time `validate_cursor_field_columns` in `types/finalizer.py`),
column resolution (`cursor_columns_for` → `CursorColumn`), the seek structure
(`keyset_seek_greater` → `KeysetSeekPlan` via `build_keyset_seek_plan`), and its
two renderers (`keyset_seek_q` ORM / `keyset_seek_sql` raw SQL, consumed by
`plans.py::apply_window_pagination` and `lateral_fetch.py::build_lateral_sql`;
`lateral_fetch.py::_keyset_seek_quals_match` re-verifies the compiled Q against
the shared plan).

Consumers: `connection.py` (class-cached keyset mode `_keyset_connection_context`
→ `_resolve_keyset_connection` slicer + windowed minting in `_resolve_from_window`),
`optimizer/nested_planner.py` (plan-time window context + per-payload seek decode),
`utils/connections.py::derive_keyset_window_bounds` (the bounds fork shared by both
halves), fakeshop acceptance surface (`apps/library/schema.py::IssueType`,
live tests `examples/fakeshop/test_query/test_keyset_api.py`), package tests
(`tests/test_keyset.py`, `tests/test_keyset_connection.py`, lateral/pg-parity
suites), GLOSSARY prose (optimizer/connection sections). Lockstep partners:
any payload-grammar change moves encode/decode together inside this module;
the cross-strategy byte-parity invariant makes every consumer's columns +
fingerprint one fact.

## Verification

Axis 1 — cross-flavor policy mirroring (searched). Offset vs keyset cursor flavors:
the offset flavor is delegated to upstream (`ListConnection.resolve_edge` /
`SliceMetadata`; `_consume_fallback` calls `super()` — no second offset
implementation in-package). Bounds twins `derive_connection_window_bounds` vs
`derive_keyset_window_bounds` fork deliberately at the cursor vocabulary
(`SliceMetadata` cannot parse a value cursor); their shared cores
(`assert_relay_pagination_bound`, `resolve_relay_max_results`) are already hoisted,
so REJECTED as intentional divergence. Walker adapters
`_connection_window_slice_from_arguments` vs `_keyset_window_slice_from_arguments`
are thin error-posture shells over those shared helpers with different return
shapes ((offset,limit,reverse) vs +seek); merging needs mode flags — REJECTED.

Axis 2 — sync/async twins (searched, ruled clean). No await boundary exists in
the codec or seek builders. `_resolve_keyset_connection` branches sync/async
INSIDE one function over one `_build` body (grep `async def` in keyset consumers);
windowed keyset rows arrive materialized via prefetch. No separated twins found.

Axis 3 — derived rather than repeated knowledge (searched). Grep
`cursor_columns_for | order_fingerprint | __django_strawberry_definition__.*cursor_field`:
the DECLARED vocabulary derivation (dig definition → read `cursor_field` → resolve
columns + fingerprint) was spelled twice in production —
`connection.py::_keyset_connection_context` (wrapped in `_KeysetConnectionState`)
and `nested_planner.py::_keyset_cursor_context` (bare tuple) — plus a third raw
re-dig of `definition.cursor_field` in `plan_connection_relation`'s
`effective_connection_order` call. Became Opportunity 1. The runtime per-order
derivation (`connection.py::_keyset_order_state`) is a DIFFERENT fact (effective
`orderBy:` entries, annotations, per-order fingerprint) — intentionally separate.
An earlier same-cycle artifact rejected these two sites as "thin adapters whose
difference is caching lifetime"; present-day source disproves that reading: neither
site delegated to a shared core — each spelled the full four-step derivation inline,
and the shapes differed (dataclass vs tuple forcing positional `keyset_context[0]`).

Axis 4 — inverse/round-trip pairs (searched, ruled clean). Encode/decode halves are
co-located in this module sharing one prefix constant, one associated-data constant,
one payload grammar; the value round-trip's decode half re-serializes through the
encode half to detect drift (`_deserialize_cursor_value`). Seek renderers share one
structure owner (`KeysetSeekPlan`); only rendering syntax differs (ORM lookups vs
SQL strings) — merging dialects would couple independent media, REJECTED.

Axis 5 — contracts restated in another medium (searched). Module docstring,
GLOSSARY prose, and test expectations restate behavior — documentation and pins,
not parallel implementations. `_RELAY_MAX_RESULTS_DEFAULT` mirrors Strawberry's
documented default with attribution (importing upstream private constants would be
worse) — REJECTED.

Single-edit-site counts. Posited change A: "the declared cursor vocabulary gains a
component (or the definition attribute relocates)" — before: 2 production sites
(connection.py + nested_planner.py); after consolidation: 1
(`keyset.resolve_declared_cursor_state`). Posited change B: "seek direction
semantics flip" — 1 site (`keyset_seek_greater`), already single-sited. Posited
change C: "payload grammar gains a field" — 1 module (encode/decode co-located).
Scratch probe `docs/dry/temp-tests/keyset/probe_declared_state.py` proved post-fix
equivalence: class-cached connection state ≡ plan-time resolver state; a cursor
minted under one decodes under the other; caching and negative-result semantics
preserved.

## Opportunities

1. **Repeated responsibility:** resolving a DjangoType's DECLARED `Meta.cursor_field`
   into its canonical `(columns, fingerprint)` vocabulary — the fact every cursor
   mint and decode over the type must agree on (cross-strategy byte-parity).
   **Sites:** `connection.py::_keyset_connection_context` (+ its private
   `_KeysetConnectionState` dataclass) and
   `nested_planner.py::_keyset_cursor_context`; downstream, nested_planner re-dug
   `target_type.__django_strawberry_definition__.cursor_field` for
   `effective_connection_order` and indexed `keyset_context[0]`. Compat alias in
   `walker.py`.
   **Evidence:** posited change A above forced 2 sites before, 1 after; the sites'
   outputs must stay identical for a plan-time-decoded seek to accept a
   resolve-time-minted cursor, so they are one contract, not similar code.
   **Owner:** `keyset.py` — it already owns `CursorColumn`, column resolution, and
   the fingerprint; both consumers already import from it (no cycle).
   **Consolidation:** new `DeclaredCursorState` + `resolve_declared_cursor_state()`
   in keyset.py; `_keyset_connection_context` keeps only its class-cache policy and
   delegates the derivation; `_keyset_cursor_context` deleted (walker alias removed),
   planner reads attributes and passes `keyset_context.cursor_field` directly to
   `effective_connection_order`.
   **Proof:** `tests/test_keyset_connection.py` — new positive/negative pins on
   `resolve_declared_cursor_state` (carrying forward the former walker-helper
   behaviors), existing caching pins unchanged; scratch probe recorded above.
   **Risks / non-goals:** caching stays connection-side only (planner derivation
   remains per-call, as shipped); the runtime `orderBy:` derivation
   (`_keyset_order_state`) must NOT merge with the declared path — different inputs
   and failure posture; payload grammar, bounds twins, and seek dialects remain
   separate (rejected above).

## Judgment

The module itself is the strongest-shaped file reviewed this cycle: every grammar
half (codec, value round-trip, order syntax, seek structure) is co-located with its
inverse, and its documented forks (bounds, dialects, runtime-vs-declared order) are
genuine policy differences backed by single-sited shared cores. One real
duplication existed ACROSS its consumers — the declared-vocabulary derivation — and
now lives once at the root owner. Deferred: `uv run pytest` (not authorized for this
item); ruff format/check and the trailing-comma check pass.

## Implementation (Worker 1)

Tracked edits (diff scoped against cycle baseline `ee34ca39caa5b640f876498c469fe88d24bbd1ce`):

- `django_strawberry_framework/keyset.py`: add `DeclaredCursorState` +
  `resolve_declared_cursor_state()` (single derivation of the declared vocabulary).
- `django_strawberry_framework/connection.py`: delete `_KeysetConnectionState`;
  `_keyset_connection_context` delegates to the shared resolver and keeps only the
  class-cache policy; annotations updated to `DeclaredCursorState`; imports adjusted
  (`cursor_columns_for` dropped; `CursorColumn` retained for the runtime
  `_keyset_order_state` path).
- `django_strawberry_framework/optimizer/nested_planner.py`: delete
  `_keyset_cursor_context`; `plan_connection_relation` uses
  `resolve_declared_cursor_state`; attribute access replaces tuple unpacking and the
  raw definition re-dig.
- `django_strawberry_framework/optimizer/walker.py`: drop the dead
  `_keyset_cursor_context` compat alias.
- `tests/test_keyset_connection.py`: orphan-import sweep; former
  `test_walker_keyset_cursor_context_none_without_cursor_field` carried forward as
  `test_resolve_declared_cursor_state_none_without_cursor_field`; new positive pin
  `test_resolve_declared_cursor_state_resolves_the_declared_vocabulary`; slice-arms
  test reads the shared resolver.

Orphan-import sweep covered all three test trees and examples (no remaining
references to `_keyset_cursor_context` / `_KeysetConnectionState` outside
regenerable `docs/shadow/` snapshots). `uv run ruff format .` and
`uv run ruff check --fix .` run clean; trailing-comma checker passes. Scratch probe
under `docs/dry/temp-tests/keyset/` (untracked) verified behavior end-to-end; its
two example-DB rows were inserted and then deleted (db.sqlite3 was already dirty
from concurrent work before this task and was left otherwise untouched). Pytest run
deferred per AGENTS.md.

## Independent verification (Worker 2)

Independently re-traced from the cycle baseline `ee34ca39caa5b640f876498c469fe88d24bbd1ce`
(`git diff ee34ca3` over the five scoped files) without sourcing Worker 1's reading.

**Equivalence, per input class.** Former connection site built
`_KeysetConnectionState(definition, cursor_field, cursor_columns_for(definition.model,
cursor_field), order_fingerprint(cursor_field))`; former planner site returned the 2-tuple
`(cursor_columns_for(...), order_fingerprint(...))` from the same two getattrs.
`resolve_declared_cursor_state` performs the identical four steps with the identical
`is None` gate, into a frozen dataclass with the same field names/order/types — so:

- *declared field present*: byte-identical `(columns, fingerprint)` from both former sites'
  argument lists; the extra `definition`/`cursor_field` fields are consumed (not dead) by
  `_keyset_order_state`'s declared fast path and `plan_connection_relation`.
- *declared field absent / non-DjangoType / `None` target*: resolver → `None`;
  connection caches the same `False` sentinel and returns `None` (cache policy byte-preserved:
  `_dst_keyset_state` name, sentinel write, `cached or None` read — registry's cache eviction
  unaffected); planner gets `None` → offset window. Old code's `getattr(None, ...)` default
  path is reproduced by the `target_type is not None` guard plus in-resolver getattrs.
- *Meta.ordering variants*: neither the old nor new declared path reads ordering — that is
  the deliberately separate runtime `_keyset_order_state`, untouched, error posture intact.
- *finalized vs pending types*: derivation depends only on definition-attr presence in both
  spellings; post-finalize model drift still surfaces as loud `FieldDoesNotExist` from the
  same `cursor_columns_for` call.
- *byte-parity probe*: `encode_keyset_cursor` embeds `{"o": fingerprint}`; decode rejects
  fingerprint mismatch and arity mismatch against `columns` — one resolver makes mint/decode
  agreement structural. Scratch probe re-read: cross-path mint→decode replay asserted.

Planner downstream conversions check out: `[0]`/`[1]` indexing → `.columns`/`.fingerprint`,
and the raw `__django_strawberry_definition__.cursor_field` re-dig replaced by
`keyset_context.cursor_field` (identical value whenever the context is non-None);
`_divergent_key_windows` has exactly one caller, updated; no tuple-shape stragglers.

**Ownership challenged.** `keyset.py` imports only django/graphql/strawberry +
`.exceptions`/`.utils.imports` — no connection.py↔keyset.py cycle; both consumers already
imported from it pre-change. `utils/connections.py` owns window-bound arithmetic (a different
contract), and the registry owns model→type lifecycle — either would couple an opt-in codec
vocabulary into an unrelated layer. Root owner correct.

**Orphan sweep.** Repo-wide grep for `_keyset_cursor_context` / `_KeysetConnectionState`:
zero `.py` matches across package, examples/, and all three test trees; remaining hits are
historical prose under committed `docs/review/` plus this artifact's own removal record.

**Rejected candidates re-probed.** Bounds twins: the fork is real — `SliceMetadata` cannot
parse a `dstcursor:` payload — and the shared cores (`assert_relay_pagination_bound`,
`resolve_relay_max_results`) are genuinely hoisted and shared by plan, resolve, and root
slicer. Walker adapter shells: differing return shapes and error-classification sets; merge
would need mode flags. Edge-minting twins: the windowed loop mints under the DECLARED
vocabulary while root `_build` mints under the EFFECTIVE per-order vocabulary
(annotations, related-path value sources, distinct `GraphQLError` posture) — the rule
(canonical codec) is already single-sited in `encode_keyset_cursor`; extracting the ~6-line
edge-construction loop would be a token-saving helper, not a rule owner. New probe:
`connection.py::_finalize_queryset` also digs the raw declared tuple for
`effective_connection_order`, but it consumes only the raw ORDER-BY strings, never the
columns/fingerprint — routing it through the vocabulary resolver would eagerly mint an hmac
fingerprint and resolve fields per request on the resolve hot path for no codec need. The
planner's twin re-dig was consolidated only because the full state was already in hand there
at zero cost. Distinct responsibility — correctly left separate.

**Single-edit-site recount.** Own posited change: "the declared attribute relocates on the
definition." Vocabulary-derivation responsibility: 2 production sites before (connection dig,
planner dig) + 1 raw re-dig → exactly 1 after (the resolver); raw-declaration readers
(`types/finalizer.py` gate, `_finalize_queryset`) were plural before the change too and carry
distinct responsibilities, so the recorded count holds within its stated scope. Second
recount: "seek direction flips" — `keyset_seek_greater` remains the single direction rule
behind both dialect renderers and the lateral verifier.

**Matrix discharge confirmed.** Axis 1 searched (offset flavor delegated upstream; bounds/
walker forks re-probed above); axis 2 ruled clean (no await boundary in codec/seek; sync/
async branches inside one `_build` body); axis 3 IS the finding, implemented; axis 4 clean
(decode half re-serializes through the encode half — `_deserialize_cursor_value` verified);
axis 5 pins only. Verdict: **verified**. Pytest run deferred (not authorized).
