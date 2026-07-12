# Pre-BETA review: optimizer/

Scope: the GraphQL query optimizer -- selection walking (`walker.py`), query
plans (`plans.py`), select/prefetch/annotation assembly, the nested-connection
window machinery (`nested_fetch.py`, `lateral_fetch.py`, `join_taxonomy.py`),
the schema-extension entry point (`extension.py`), and the supporting
`selections.py` / `field_meta.py` / `hints.py` / `_context.py`.

Method: logic-only read of `docs/shadow/current/*optimizer*` plus the diffs
since `0.0.13` (`walker`, `lateral_fetch`, `plans`, `nested_fetch`,
`selections`, `join_taxonomy`, `extension` all changed substantially this
cycle -- the per-response-key window batching and the keyset seek integration).
Read-only; no tests run. The per-key window design (idea #2) and the keyset
seek plumbing are intentional; bugs *within* them are in scope.

Bottom line: this is the most intricate subsystem in the package and it
absorbed the most change this cycle. No P0 found, but the DB-vendor strategy
selection has a real multi-database gap worth confirming before BETA.

## P0 -- correctness suspicions

None confirmed. See the P1 strategy-selection item -- it is the closest to a
correctness bug and would become a P0 if the fallback proves to fetch unbounded.

## P1 -- fix before BETA

### `nested_fetch.py::resolve_strategy` / `_strategy_for_vendor` -- "auto" resolves against the DEFAULT db alias, not the routed one
Confidence: medium. `resolve_strategy("auto")` picks the nested-connection
strategy from `connections[DEFAULT_DB_ALIAS].vendor` -- it chooses the lateral
strategy when the *default* database is PostgreSQL and the windowed strategy
otherwise. But a `DjangoType` can be routed (via a database router or an
explicit `.using(...)`) to a different backend than the default. If the default
alias is PostgreSQL but a type's rows actually live on a non-PostgreSQL alias,
the lateral strategy is selected for a queryset that will execute elsewhere.
`lateral_fetch.py::_fetch_lateral_rows` does guard at fetch time
(`if connection.vendor != "postgresql": return None`) and falls through to
`super()._fetch_all()` -- so the question that decides P1-vs-P0 is whether that
fallback yields a *correctly windowed* page or an *unbounded* child fetch. The
lateral queryset's row limiting lives in the custom SQL; if the fallback runs
the plain queryset without the window, a nested connection on a mis-routed type
returns all children instead of the requested page.
Verify: route a type to a non-PostgreSQL alias while `default` is PostgreSQL,
request a nested connection page, and confirm the fallback both limits rows and
computes `hasNextPage` correctly (not "all children, no window").

## P2 -- polish / hardening

### `nested_fetch.py::_builtin_strategies` -- lazy mutation of a module-global dict
Confidence: low. `_STRATEGIES` is a module-level dict mutated on first access to
insert the lateral strategy (imported lazily to avoid an import cycle).
Concurrent first-touch from two threads is idempotent (same object inserted), so
this is benign today, but a module-global mutable registry is the kind of state
that grows teeth later (e.g. if a consumer registers a custom strategy). Prefer
building the registry once at import behind the cycle-break, or guarding the
lazy insert, so the "mutable global" pattern does not spread.

### `walker.py` divergent per-key windows -- log when a key is dropped to the fallback
Confidence: low. When aliased sibling connection fields carry conflicting
pagination arguments, `_response_key_arguments_conflict` / the malformed-key
path route those keys to the per-parent resolver instead of a shared window.
That is correct, but silent: a schema that accidentally triggers the fallback
loses the batched-window optimization with no signal. A debug-level log naming
the dropped response key would make the N+1-regression visible during
development without changing behavior.

## API & consistency notes

- The keyset nested path deliberately ignores a child `orderBy:` and always
  windows under the declared `cursor_field`
  (`walker.py::_plan_connection_relation` sets `effective = ...cursor_field`),
  so nested keyset cursors are byte-identical to root cursors by construction.
  This is the right call; just make sure it is documented that nested keyset
  connections do not honor a per-field `orderBy:` (they fall back if one is
  supplied via the sidecar).
- `deterministic_order` is the single source for both plan-time window ordering
  and resolve-time ordering, which is what keeps window row numbers from
  drifting from fallback cursors. Preserve that single-source invariant -- any
  future ordering tweak must go through it, not around it.

## Verified sound (do not re-flag)

- `walker.py::_extend_only_projection` -- correctly handles both `defer` and
  `only` loading states: it re-defers `names - attnames` in defer mode and adds
  the missing cursor attnames in only mode, and is a no-op on the default
  (load-all) queryset. It does not accidentally widen or narrow the projection.
- Per-key `to_attr` naming -- `_relation_connection_to_attr_for_key` keys the
  prefetch attribute by response key so aliased sibling connections do not
  clobber each other's fetched rows; the resolver reads the per-key attr first
  and falls back to the shared attr.
- `_normalized_alias_payload` -- normalizes pagination ints before comparing
  aliased-argument payloads, so `first: 10` vs `first: 10` do not falsely read
  as divergent due to type/spelling.
- `nested_fetch.py::NestedConnectionRequest.__post_init__` and
  `lateral_fetch.py::LateralWindowSpec.__post_init__` both assert the
  window-fetch mode invariant (`assert_window_fetch_mode_for`) at construction,
  so an incoherent `with_total_count` + `next_page_probe` combination fails loud
  at plan time.
- `nested_fetch.py::active_strategy` uses a `ContextVar`, so a per-request
  strategy override does not leak across requests or async tasks.
- `lateral_fetch.py::_deduplicate_parent_ids` preserves order via `dict.fromkeys`
  and drops `None`, with a `TypeError` fallback for unhashable ids.

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
