# DRY review: `django_strawberry_framework/registry.py`

Status: verified

## System trace

`TypeRegistry` (process-global singleton `registry`) owns four bodies of state plus two
lifecycle mechanisms:

1. **Type/model maps** - `_types` (model -> [types], registration order), `_models`
   (type -> model, one-to-one), `_primaries` (model -> declared primary),
   `_definitions` (type -> `DjangoTypeDefinition`). Written once per class by
   `DjangoType.__init_subclass__` (`types/base.py`) through
   `register_with_definition`, whose snapshot-conditional rollback shares
   `_detach_type_from_model` with `unregister`. Read side: `get` (primary-first,
   lone-type fallback, `None` when multi-and-unprimary), `primary_for` (strict),
   `types_for`, `iter_types`, `model_for_type` (optimizer reverse lookup),
   `models_with_multiple_types` (the once-per-build tuple both Phase-1 and Phase-2.5
   audits consume), `definition_for_graphql_name` (the GlobalID type-name decode half,
   inverting `types/relay.py::encode_typename`'s ``type`` strategy over Relay-Node
   definitions only).
2. **Pending relations** - `add_pending_relation` / `iter_pending_relations` /
   `discard_pending` (identity-keyed). Produced by `_build_annotations`, drained by
   Phase 1 of `types/finalizer.py::finalize_django_types`.
3. **Choice enums** - `_enums` keyed `(model, field_name)`; the cache behind
   `types/converters.py::convert_choices_to_enum`.
4. **Finalized flag + GlobalID setting snapshot** - `is_finalized` / `mark_finalized`;
   `_globalid_setting_snapshot` with the `GLOBALID_SETTING_UNSET` sentinel, computed
   once per build by the finalizer and reset by `clear()`.

Lifecycle mechanisms: `_check_mutable` (post-finalize mutation guard; `clear()` is the
only bypassing mutator), type teardowns (`register_type_teardown`, LIFO, retry-on-failure,
run by both `clear()` and `unregister`), and subsystem teardown registration
(`register_subsystem_clear` / `iter_subsystem_clears`, with the `before_bind` phase filter
the finalizer's pre-bind sweep replays). The per-type co-clear helper `_clear_if_importable`
(cycle-safe best-effort import via `utils/imports.py::import_attr_if_importable`) serves
`unregister`'s connection-cache eviction; registry-wide co-clears are owner-registered
callbacks instead.

Consumers traced: `types/base.py`, `types/finalizer.py` (all phases + the shared
`_bind_set_owner_common` skeleton), `types/definition.py::DjangoTypeDefinition.related_target_for`,
`types/resolvers.py`, `types/relay.py::decode_global_id`, `optimizer/walker.py`,
`optimizer/extension.py`, `utils/querysets.py` (visibility scoping), `permissions.py`,
`filters/sets.py` (owner binding + target resolution), `auth/mutations.py`
(`_resolve_user_type` three-state split), `mutations/sets.py::make_declaration_registry`
(post-finalize reject reads `registry.is_finalized()`), `testing/relay.py`,
`management/commands/inspect_django_type.py`. Every sibling lifecycle ledger in the
package (input namespaces via `utils/inputs.py::make_input_namespace` /
`make_set_input_namespace`, shape-build caches via `make_shape_build_cache`, declaration
registries via `make_declaration_registry`, `connection._connection_type_cache`,
`relay._node_fields_declared`) announces its teardown through
`register_subsystem_clear` rather than re-implementing a registry-wide clear - the
mechanics are already consolidated; `TypeRegistry` is the sole type-flavor lifecycle
owner.

Lockstep surfaces: a new registry map must move `__init__` + `clear()` together;
a new subsystem cache registers one callback at its own import; a change to the finalized
flag semantics moves `TypeRegistry._check_mutable`, `DjangoType.__init_subclass__`'s guard,
and `make_declaration_registry.register`'s reject (all readers of one fact, not owners of
parallel facts).

## Verification

All five probing axes discharged:

1. **Cross-flavor policy mirroring** - searched: `grep -rn "register_subsystem_clear("`,
   `make_declaration_registry|make_shape_build_cache`, `_materialized_names`,
   `GeneratedInputArgumentsFactory` across all flavors (types, filters, orders,
   mutations, forms, auth, rest_framework). Every flavor's lifecycle ledger already
   routes teardown through this file's `register_subsystem_clear` and shares mechanics
   via `utils/inputs.py` / `mutations/sets.py` factories; no flavor re-implements
   registry-wide clearing. One mirrored *contract* found and rejected (below). Real
   duplication found in a consumer instead: two filters-side sites composing
   `primary_for(...) or get(...)` (Opportunity 1).
2. **Sync and async twins** - searched: `async def.*finaliz`, `await.*registry`,
   `await finalize` - zero hits. Ruled otherwise inapplicable on the real surface:
   every mutating method runs at import time from `__init_subclass__` (single-threaded
   module loading); the class docstring forbids request-handler/async-resolver mutation,
   so no await-boundary twin can exist.
3. **Derived rather than repeated knowledge** - searched: `primary_for(` across package +
   tests. Found the one live instance of re-derived precedence: `filters/sets.py`
   spelled `registry.primary_for(x) or registry.get(x)` twice, which equals
   `registry.get(x)` because `get`'s first return state IS the primary. Decisive
   evidence: `tests/types/test_definition_relations.py::test_related_target_for_resolves_to_primary_when_two_types_share_target_model`
   documents the identical chain as ALREADY collapsed at
   `types/definition.py::DjangoTypeDefinition.related_target_for` with exactly this
   safety argument - the two filter sites are the missed leftovers. Fixed (Opportunity 1).
4. **Inverse and round-trip pairs** - searched: `def global_id_for|encode|decode`,
   `register/unregister` call graphs. Three pairs verified consistent:
   `encode_typename` (emits `definition.graphql_type_name`) vs
   `definition_for_graphql_name` (scans the same attribute, Relay-only, unique-match)
   - one grammar, key stored once on the definition; `register`/`unregister` share
   `_detach_type_from_model` and deliberately diverge elsewhere (docstring names the
   disagreement); `iter_pending_relations`/`discard_pending` are colocated drain/refill.
5. **Contracts restated in another medium** - searched `docs/GLOSSARY.md` for
   `finalize_django_types` / primary semantics: prose describes the same behavior
   (e.g. `Meta.primary` entry states `registry.get(model)` returns the primary) with no
   drift against code; error substrings pinned by tests are the documented grep-stability
   contract (`_already_registered`, the `_format_*` sibling formatters), not accidental
   restatement.

**Single-edit-site counts.**

- Posited change: "break or relocate the primary-first rule for resolving a model's
  relation-target DjangoType." Before this review: 3 sites carried it -
  `TypeRegistry.get` + the two `filters/sets.py` chains (every other consumer delegates
  to plain `get`). After Opportunity 1: 1 site (`TypeRegistry.get`).
- Posited change returning **one**: "tighten the multi-type audit threshold from >=2
  registered types." Forces exactly one edit (`models_with_multiple_types`); both audits
  consume the accessor's output, and no other module re-derives the predicate.
- Posited change returning **one**: "add a new build-lifecycle cache to a subsystem."
  Forces one edit at the owning module (`register_subsystem_clear(..., owner=...)`);
  `clear()` needs none - the registration mechanism already achieved single-site
  extension, confirmed by 13 owner-registered rows across 10 modules.

**Scratch experiments**: none warranted - every equivalence above is provable from pure
dict reads with no timing, truthiness (type classes have no `__bool__`), or interleaving
hazard; the strongest claim is additionally pinned end-to-end by new permanent tests.

**Strongest rejected candidates.**

- *Post-finalize guard spelled twice* (`_check_mutable` vs
  `make_declaration_registry.register`'s "Cannot declare ... after finalization"):
  both READ `registry.is_finalized()` - one fact, two consumers with different subjects
  (registry mutators vs declaration ledger). Consolidating messages would couple
  unrelated flavors; the flag itself has one owner.
- *Two teardown media for the connection cache* (`unregister`'s string-based
  `_clear_if_importable` eviction vs `connection.py`'s registered
  `clear_connection_type_cache`): distinct lifecycles (per-type eviction vs whole-cache
  reset); the parameterized per-type form cannot ride zero-arg
  `register_subsystem_clear`; eager import is impossible because `connection.py` imports
  `registry` (module-load cycle), so the cycle-safe string import owned by
  `utils/imports.py` is the root shape. Rename drift is pinned by
  `test_unregister_evicts_connection_type_cache_entry`.
- *`get` vs `primary_for` vs `types_for` read APIs*: documented distinct return states
  (three-state vs strict-primary vs full list); `auth/mutations.py::_resolve_user_type`
  legitimately combines them to split states `get` intentionally conflates.

## Opportunities

### 1. Collapse the historical `primary_for(x) or get(x)` composition at both FilterSet target-resolution fallbacks

- **Repeated responsibility:** "resolve a model's relation-target DjangoType,
  primary-first" - stated once by `TypeRegistry.get` and re-derived twice by
  composition whose result is identical (`get` returns `_primaries[model]` first;
  type classes are always truthy).
- **Sites:** `django_strawberry_framework/filters/sets.py::FilterSet._resolve_relation_target_type`
  (the unbound-owner fallback) and `django_strawberry_framework/filters/sets.py::FilterSet._target_type_for_related_filter`
  (the unbound-child fallback); docstrings at both sites plus the Decision-4 selector's
  docstring named the old chain.
- **Evidence:** the codebase's own precedent -
  `tests/types/test_definition_relations.py::test_related_target_for_resolves_to_primary_when_two_types_share_target_model`
  records the identical chain as already collapsed at `related_target_for` "NOT the
  historical ... chain", with the same safety argument. Every other registry consumer
  (walker, resolvers, querysets visibility, permissions, finalizer, definition) uses
  plain `get`. Posited change "break primary-first in `get`": pre-fix, the two filter
  chains silently kept old semantics while six-plus other consumers moved - count 3;
  post-fix, count 1.
- **Owner:** `TypeRegistry.get` (`registry.py`) - already the authoritative statement.
- **Consolidation:** replace both chains with `registry.get(...)`; update the three
  docstring references; leave a pointer comment at each collapsed site.
- **Proof:** permanent pins added next to their siblings in `tests/filters/test_sets.py`:
  `test_resolve_relation_target_type_registry_fallback_prefers_declared_primary` and
  `test_target_type_for_related_filter_registry_fallback_prefers_declared_primary`
  (two types on one model, declared primary wins through each fallback), mirroring the
  definition-side twin. Existing live `/graphql` filter coverage exercises the common
  single-type-no-primary shape.
- **Risks / non-goals:** none behavioral - both methods keep their owner-aware branch
  untouched; the registry fallback remains pre-bind/unbound-only. Do not extend the
  collapse to `auth/mutations.py::_resolve_user_type`, whose `get`+`types_for` pair is a
  different, documented three-state discrimination.

None otherwise - the registry's own mechanics (maps, teardown registration, rollback,
decode scan, sentinel) each have exactly one implementation after this fix.

## Judgment

`registry.py` is the system's cleanest consolidation hub, not a duplication source: the
five axes surfaced no parallel registry, no async twin, no inverse-pair drift, and no
restated contract. The one genuine finding lived one hop away in a consumer that had
missed an in-repo consolidation precedent (`related_target_for`), re-deriving `get`'s
precedence by composition at two filter fallbacks; collapsing it makes
"primary-first relation-target resolution" single-sited at `TypeRegistry.get` and brings
the filters family in line with every other consumer. Rejected candidates document why
the remaining look-alikes (dual guard sites, dual teardown media, triple read API) are
deliberately separate.

## Implementation (Worker 1)

Tracked changes (scoped against cycle baseline `564297c`; concurrent dirty files
untouched):

- `django_strawberry_framework/filters/sets.py`: collapsed
  `registry.primary_for(related_model) or registry.get(related_model)` ->
  `registry.get(related_model)` in `_resolve_relation_target_type`, same for
  `_target_type_for_related_filter` (`child_model`), with pointer comments; updated the
  three affected docstrings to name `registry.get`.
- `tests/filters/test_sets.py`: added the two permanent primary-wins pins described in
  Opportunity 1 (placed beside their sibling direct-method tests; no orphan imports -
  all symbols were already imported).

Post-edit hygiene: `uv run ruff format .` (no changes) and `uv run ruff check --fix .`
(all checks passed). Pytest deferred per `AGENTS.md` (not explicitly requested);
equivalence is argued above and pinned by the new tests for the final gate.

## Independent verification (Worker 2)

**Scoped diff** (`git diff 564297c -- filters/sets.py registry.py tests/filters/test_sets.py`):
exactly the claimed change - `registry.py` untouched; two chain collapses
(`filters/sets.py::FilterSet._resolve_relation_target_type #``return
registry.get(related_model)```, `filters/sets.py::FilterSet._target_type_for_related_filter
#``return registry.get(child_model)```), three docstring updates, pointer comments at both
sites, plus the two pins in `tests/filters/test_sets.py`. Nothing else changed for this item.

**Equivalence re-derived from `TypeRegistry.get` / `primary_for` return-state machinery**
(`registry.py`), per input class - all IDENTICAL:

- *Registered, no definition yet*: neither reader touches `_definitions`; both read only
  `_primaries`/`_types`, which `register_with_definition`'s symmetric rollback keeps consistent
  for either read order. Identical.
- *Multiple primaries per model*: unreachable by construction - `register` raises on
  duplicate-primary and on idempotent flag-flip; `_primaries[model]` is a single dict slot both
  methods read. Identical (vacuously).
- *x not registered*: `get(x)` returns ``None`` via both miss branches; the chain evaluates
  ``None or None`` -> ``None``. Identical.
- *Finalization windows*: neither reader consults `_finalized`; every mutation is import-time
  single-threaded from `__init_subclass__`, over plain dicts keyed by model classes (identity
  hash/eq - no user code runs between the chain's two probes), so no interleaving can split
  them. Stronger: even a falsy-but-not-None stored primary cannot diverge, because `get`
  re-checks `_primaries` with ``is not None`` and returns that same object where the chain's
  second operand would; type classes here carry no metaclass `__bool__`/`__len__`. Identical
  across all reachable states.

**Chain sweep**: zero executable `primary_for(...) or ...get(...)` chains remain anywhere
(package, `tests/`, `examples/fakeshop/`). Remaining textual hits are history-naming docstrings
inside the two new pins and the definition-relations precedent test. Executable `primary_for(`
calls are finalizer audit reads only (`types/finalizer.py`), which report ambiguity rather than
resolve targets; zero `_primaries` reach-ins outside `registry.py`.

**Tests**: both pins exercise the FilterSet fallbacks end-to-end (module autouse
`_isolate_registry` guarantees no phase-2.5 binding, so `_owner_definition is None` at
`filters/sets.py:1173`; `RelatedFilter(ShelfFilter)` takes the documented FilterSet-class
acceptance shape). They fail under any semantic regression of primary-first through these
paths (e.g. registration-order `candidates[0]`, strict-primary-only): ShelfType registers
first, AdminShelfType(primary=True) must win. Honest nuance: literal reintroduction of the
historical chain is undetectable by ANY behavioral test - that is precisely the equivalence
theorem - so the correct proof standard is the precedence-contract pin through each resolution
path, which these provide (matching Worker 1's stated intent).

**Rejected candidates re-probed**: dual post-finalize guards confirmed as one fact/two readers
(`mutations/sets.py::make_declaration_registry.register #"Cannot declare"` vs
`TypeRegistry._check_mutable`); dual connection-cache teardown media confirmed distinct
(per-type string-import pop in `unregister` vs owner-registered
`connection.py::clear_connection_type_cache`; eager import impossible - `connection.py` imports
from `.registry`); triple read API confirmed deliberately separate
(`auth/mutations.py::_resolve_user_primary_or_raise` combines `get`+`types_for` to split the
states `get` conflates).

**Matrix re-discharged**: axis 1 re-searched (`register_subsystem_clear` consumers span types,
filters, orders, mutations, forms, auth, rest_framework, relay, connection - no flavor
re-implements clearing); axis 2 ruled inapplicable against the class docstring's import-time
mutation contract; axes 3-5 re-searched above; GLOSSARY `Meta.primary` prose matches `get`'s
documented first return state.

**Single-edit-site recount**: posited "break or relocate primary-first relation-target
resolution" - post-fix exactly ONE site carries the rule (`TypeRegistry.get`); all 17+
executable `registry.get(...)` call sites delegate without composing; pre-fix count 3 confirmed
by the scoped diff showing exactly the two collapsed chains. Holds.

Two citation imprecisions in the artifact, non-blocking, corrected here: the auth symbol is
`_resolve_user_primary_or_raise` (`_resolve_user_type` never existed at baseline either), and
the teardown-row count was already 17 rows across 14 modules at baseline (now 18/17 with
concurrent work), not 13/10 - the mechanism claim's direction is unchanged and stronger.

Pytest deferred per `AGENTS.md`. Verdict: **verified**.
