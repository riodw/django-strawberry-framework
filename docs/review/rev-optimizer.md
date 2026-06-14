# Review: `django_strawberry_framework/optimizer/`

Status: verified

Folder pass over the optimizer subpackage: 7 reviewed `.py` siblings plus the
subpackage `__init__.py`. Supersedes the stale 0.0.7-era on-disk
`rev-optimizer.md` (which carried `Status: verified`, referenced
`review-0_0_7.md`, treated the folder as a flat single-module `optimizer.py`,
and cited symbols that no longer exist — e.g. `_walk_directives`
`extension.py:92-128` was unified into `_walk_cache_relevant_vars` by the 0.0.9
DRY pass; the FIFO-eviction `extension.py:650-658` cite no longer matches; the
artifact contains none of the 0.0.9 surface — confirmed by grep: zero hits for
`anonymous` / `inline fragment` / `convert_selections` / `type_condition` /
`selections.py`). Active plan box `review-0_0_9.md:98` was unchecked, so this
replaces it wholesale per the recurring stale-artifact pattern. All 7 sibling
file artifacts are `Status: verified` (`_context`, `extension`, `field_meta`,
`hints`, `plans`, `selections`, `walker`).

This folder pass owns one OPEN High forwarded from the walker file artifact
(`rev-optimizer__walker.md`) — the anonymous-inline-fragment crash. It is
re-confirmed live below with the exact source location, the root-cause fix, and
the test expectation, as the input Worker 2 will implement.

## DRY analysis

- **None act-now at folder scope.** Every cross-file consolidation the 7 file
  artifacts surfaced is correctly deferred-with-trigger or already-landed; none
  fires at 0.0.9. The selection-traversal substrate (`optimizer/selections.py`)
  is the 0.0.9 consolidation home that removed the reverse `extension <- walker`
  dependency, and both `extension.py` (`extension.py:66-73`) and `walker.py`
  (`walker.py:35-59`) reach it through underscore aliases — the right factoring,
  not duplication. Carried (all deferred, owned by a future DRY cycle, NOT this
  folder pass):
  - **Fold the three fragment-recursing converted-selection walks onto one
    `_iter_field_descendants` primitive** (`selections.py::included_field_selections`,
    `::named_children`, `::direct_child_selected._check`). Trigger and shape are
    in `rev-optimizer__selections.md` DRY bullet 1; the Medium that motivated it
    was fixed inline (the `should_include` gate) precisely because the fold is
    deferred. Re-triage when a 4th converted-selection walk lands.
  - **Lift the `edges { node }` double-loop into `selections.py`** parameterized
    on a `prefix_fanout` callable — twinned across
    `walker.py::_connection_node_selections` and
    `extension.py::_connection_node_child_selections`. Defer until a 3rd
    `edges { node }` unwrap consumer (`rev-optimizer__selections.md` DRY bullet 2;
    `rev-optimizer__extension.md` deferred bullets).
  - **`_walk_cache_relevant_vars` / `_walk_reachable_fragment_definitions`
    shared visitor** and **`_strawberry_schema_of(obj, *, default)`** — both
    `extension.py`-local, deferred-until-third (`rev-optimizer__extension.md`).
  - **`append_*_unique` indexed-vs-membership dispatch** and
    **`_lookup_paths_from_parts` second construction-time consumer** — both
    `plans.py`-local, deferred-with-trigger (`rev-optimizer__plans.md`).
  - **`hint_kind` classifier** and **`freeze_sentinel` idiom** — `hints.py`,
    deferred-until-second-consumer (`rev-optimizer__hints.md`).
  - **Reverse-O2O nullable predicate vs `relation_kind`** and
    **`_has_composite_pk` defensive `_meta` read** — `field_meta.py`-local,
    deferred (`rev-optimizer__field_meta.md`).

## High:

### Anonymous inline fragment under an optimized field crashes the resolver (`'NoneType' object has no attribute 'name'`)

A valid GraphQL query placing an **anonymous inline fragment** (`... { ... }` —
an inline fragment with NO `on TypeName` type condition) under any optimized
`DjangoType` field crashes the field resolver with
`AttributeError: 'NoneType' object has no attribute 'name'`, surfaced to the
consumer as a `GraphQLError` on the field. It reproduces with NO directive and
NO `totalCount` in the fragment — the bare anonymous-inline-fragment shape is
sufficient. A crash on a spec-valid query against the package's headline
optimizer surface is a **High** ("errors that crash normal consumer usage",
REVIEW.md severity definitions).

This is forwarded from `rev-optimizer__walker.md` (re-confirmed there as LATENT
in `walker.py`'s own `sel.name` reads, but a LIVE crash on the optimizer's
selection-conversion entry). The walker file cycle correctly routed the fix here
because it is cross-file: the edit lands on `extension.py` and `selections.py`,
neither of which is in the walker's per-file scope.

**Root cause (verified at source + reproduced live this pass).**
`optimizer/extension.py::DjangoOptimizerExtension.apply_to`
(`extension.py #"convert_selections(info, info.field_nodes)"`, src line 783)
calls Strawberry's `strawberry.types.nodes.convert_selections`, which dispatches
an anonymous `InlineFragmentNode` to `InlineFragment.from_node` and unguardedly
reads `type_condition=node.type_condition.name.value`
(`.venv/.../strawberry/types/nodes.py:126`). For an anonymous inline fragment
`node.type_condition is None`, so `.name` raises. The package never sees the
converted selection — the converter crashes inside the package's own call.
`apply_to` is the shared entry for BOTH:

- the connection path:
  `connection.py::_finalize_queryset` -> `apply_connection_optimization`
  (`extension.py:1102`) -> `apply_to`, and
- the middleware list path:
  `DjangoOptimizerExtension.resolve` -> `_optimize` (`extension.py:741`) ->
  `apply_to`.

so the bug is NOT connection-specific.

**Live repro (this pass, in-process `schema.execute_sync` against fakeshop,
`seed_data(3)`):** matches the walker artifact's account; the full traceback
terminates at `strawberry/types/nodes.py:126` via the `apply_to` ->
`convert_selections` frame in both paths.

- `{ allItems { edges { node { ... { name } } } } }` (anon inline at node level,
  connection field) -> **CRASH**, path `['allItems']`, via
  `apply_connection_optimization` (`extension.py:1102`) -> `apply_to`
  (`extension.py:783`).
- `{ allItems { ... { edges { node { name } } } } }` (anon inline directly under
  the connection field) -> **CRASH**, path `['allItems']`, same frame.
- `{ allGlossaryTerms { ... { title } } }` (anon inline under a plain LIST
  field) -> **CRASH**, path `['allGlossaryTerms']`, via `resolve` -> `_optimize`
  (`extension.py:741`) -> `apply_to` (`extension.py:783`) — confirms the bug
  spans the middleware list path too.
- `{ allItems { edges { node { ... on ItemType { name } } } } }` (TYPED inline
  `... on ItemType`) -> **NO error** (the typed form carries a `type_condition`
  AST node, so `from_node` reads `.name.value` successfully).
- `{ allItems { edges { node { id name } } } }` (baseline, no fragment) ->
  **NO error**.

So the crash is specific to **anonymous (type-condition-less) inline
fragments**; typed inline fragments and named fragment spreads are unaffected.

```django_strawberry_framework/optimizer/extension.py:781:783
        from strawberry.types.nodes import convert_selections

        selections = convert_selections(info, info.field_nodes)
        # ^ convert_selections -> InlineFragment.from_node reads
        #   `node.type_condition.name.value`; anonymous `... { f }` has
        #   type_condition=None -> AttributeError.
```

**Recommended ROOT-CAUSE fix (no bare try/except).** The defect is that the
package routes selection conversion through Strawberry's `convert_selections`,
whose `InlineFragment.from_node` cannot represent the anonymous
(`type_condition=None`) shape. `optimizer/selections.py` already owns the
package's fragment-aware traversal substrate and already duck-types fragments on
`hasattr(selection, "type_condition")` (`selections.py::is_fragment`,
`selections.py:142` — verified this pass), so a `type_condition=None` shell
satisfies that predicate and flows correctly through `included_field_selections`
/ `named_children` / `with_runtime_prefix` (all of which read `.selections`,
never `type_condition.name`). Fix:

1. Add an `ast_to_converted_selections(info, field_nodes)` adapter to
   `optimizer/selections.py` (the existing single home for both AST and
   converted-selection traversal) that mirrors Strawberry's `convert_selections`
   but builds the inline-fragment shell with
   `type_condition = node.type_condition.name.value if node.type_condition is not None else None`,
   reusing the existing fragment-aware substrate.
2. Rewire `extension.py::apply_to` (`extension.py:783`) to call that adapter
   instead of `strawberry.types.nodes.convert_selections`.

This keeps directive/fragment policy single-sourced in `selections.py` (the
`docs/feedback.md` Major 2 consolidation contract) and removes the package's
dependency on a Strawberry internal that mishandles a valid query shape. Do NOT
wrap the `convert_selections` call in try/except — that would swallow the whole
selection tree and silently disable optimization for any query containing an
anonymous inline fragment, and AGENTS.md forbids try/except as a workaround for
an abstraction-level bug. (Upstream `strawberry-django` sidesteps this entirely
by walking the raw graphql-core AST `field_nodes` via `graphql.collect_fields`
rather than `convert_selections` — `~/projects/strawberry-django-main/strawberry_django/utils/gql_compat.py`
+ `optimizer.py:726`.) While implementing, confirm `included_field_selections`
keeps inlining the now-non-crashing anonymous-fragment shells (it will —
`is_fragment` already matches `type_condition=None`).

**Test expectation (High requires it).** Pin with a LIVE fakeshop `/graphql`
query (preferred per AGENTS.md "Test through real usage and prefer the example
project"):

- Add to `examples/fakeshop/test_query/test_products_api.py`: a
  `django.test.Client` POST of `{ allItems { edges { node { ... { name } } } } }`
  asserting `response.json()` has NO `errors` key and returns the seeded item
  names — the anonymous-inline-fragment-under-a-connection-field case.
- Sibling regression guard in the same file: the typed form
  `... on ItemType { name }` still resolves cleanly (the typed path must stay
  working).
- A list-path anonymous-inline-fragment query in `test_glossary_api.py`, e.g.
  `{ allGlossaryTerms { ... { title } } }`, asserting no `errors` — the bug
  spans the middleware list path, so both paths need a live pin.

If the new adapter has a branch a live query cannot reach, fall back to a
package-internal pin in `tests/optimizer/test_selections.py` exercising the
adapter directly on a synthesized anonymous-`InlineFragmentNode`
(`type_condition=None`); but the live queries above ARE reachable here, so they
MUST be earned that way per AGENTS.md test placement.

## Medium:

None. (The `selections.py` `direct_child_selected` `@skip`/`@include` Medium was
fixed in the `selections.py` file cycle — the `should_include` gate landed at
`selections.py::direct_child_selected #"if not should_include(selection)"` with a
live + package-internal pin. Not re-promoted: it is closed, not open, and was a
single-walk omission, not a cross-file folder concern.)

## Low:

### Substrate-consumer consistency: the `totalCount`-detection seam shares the same crashing converter, so the High's fix must be verified to cover `info.selected_fields` too

The folder-focus task asks whether the shared `selections.py` substrate is
consumed consistently by its three advertised consumers — the cache-key AST walk
in `extension.py`, the plan walk in `walker.py`, and the `totalCount` detection
in `connection.py`. It is: each reaches the substrate through the documented
adapter (`extension.py`'s AST trio; `walker.py`'s converted-selection family;
`connection.py::_total_count_requested` -> `direct_child_selected`,
`connection.py:388-391`), and the `is_fragment` discriminator is single-sourced
so the three cannot drift. One consistency note worth recording for Worker 2:
`connection.py::_total_count_requested` reads `info.selected_fields`
(`connection.py:390`), and Strawberry's `Info.selected_fields` property is itself
`convert_selections(info, info.field_nodes)` — the SAME crashing converter. On
the connection path `apply_to` crashes first (during `_finalize_queryset`, before
`_total_count_requested` is reached), so the High's `extension.py` rewire is the
load-bearing fix; but `info.selected_fields` is Strawberry-owned and the package
cannot route it through the new adapter. Worker 2 should, after the
`extension.py` fix, add (or confirm) a live pin that a connection query carrying
an anonymous inline fragment AND `total_count=True` still resolves — i.e. the
fast path that reads `_total_count_requested` does not re-trip the same crash on
`info.selected_fields`. If it does, that is a SECOND fix site (route the
`totalCount` detection off the package's own converted selections rather than
`info.selected_fields`), not a regression of the first. Forward-looking
consistency check, gated on the High's implementation; not an independent defect.

### Fail-loud guard / Strawberry-version assertion on the `prime_selected_fields` internals coupling (forward-looking; maintainer-escalation)

`prime_selected_fields` (`selections.py`) couples to two Strawberry internals —
`Info._raw_info` and `Info.selected_fields` being a `functools.cached_property`
backed by the `info.__dict__["selected_fields"]` slot. Verified live (Worker 3's
recorded reservation): if Strawberry renames `_raw_info` (or stops dict-slot
caching), `prime_selected_fields` SILENTLY no-ops and the connection-path crash
returns — it degrades to the original bug rather than failing loudly. Add a
fail-loud guard / Strawberry-version assertion on the coupling. DEFERRED; trigger:
maintainer opts for explicit fail-loud over the live-test regression net, OR on a
Strawberry major-version bump. Today (pinned Strawberry version) the four live
anonymous-inline-fragment tests are the regression net that would catch such a
rename, so this is forward-looking maintainability, not a shipped defect. No
source edit this cycle.

### GLOSSARY stash keys partially undocumented (forwarded from `rev-optimizer___context.md`; defer triggers unfired)

`docs/GLOSSARY.md:1265` ("Planned resolver keys and lookup paths are stashed on
`info.context` for introspection during strictness incidents") never names the
three keys a consumer would read — `dst_optimizer_planned`,
`dst_optimizer_lookup_paths`, `dst_optimizer_strictness` (the constants at
`_context.py #"DST_OPTIMIZER_PLANNED ="` ff.); `dst_optimizer_plan` /
`dst_optimizer_fk_id_elisions` are named once at `docs/GLOSSARY.md:541`. This is
forward-looking, not act-now: both defer triggers from the `_context.py` cycle
remain unfired (the module is still underscore-prefixed `_context`; both
consumers — `extension.py:51-62`, `types/resolvers.py` — still import the helpers
under `_get_context_value` / `_stash_on_context` aliases, internal-only; still
exactly five `dst_optimizer_*` keys). The natural GLOSSARY home is the
Strictness-mode / `DjangoOptimizerExtension` entry that does the stashing, not
the underscore-prefixed `_context` module (which has no consumer-facing GLOSSARY
surface). No source edit; routed here only so it is not re-discovered as
untriaged. Re-triage when the module de-underscores (helpers go public) OR a
sixth `dst_optimizer_*` key lands.

## What looks solid

### DRY recap

- **Existing patterns reused.** `optimizer/selections.py` is the 0.0.9
  consolidation home for selection traversal: the AST adapter trio
  (`ast_child_selections` / `resolve_unvisited_fragment` /
  `directive_variable_names`) for `extension.py`'s cache-key walk, and the
  converted-selection family (`is_fragment` / `should_include` /
  `included_field_selections` / `named_children` / `with_runtime_prefix` /
  `node_children_with_runtime_prefix` / `direct_child_selected` /
  `response_key[s]`) for `walker.py`'s plan walk and `connection.py`'s
  `totalCount` detection. The reverse `extension <- walker` edge was removed; both
  modules now source from `selections.py` via underscore aliases
  (`extension.py:66-73`, `walker.py:35-59`) so existing bodies/tests resolve
  unchanged. The `_dst_*` window-annotation-name constants (`plans.py`) are
  imported by both `walker.py` and `connection.py` rather than re-spelled. The
  `_context.py` stash-key constants are the single home for the five
  `dst_optimizer_*` literals, imported by name by `extension.py` and
  `types/resolvers.py`. Window-math helpers (`ends_in_unique_column` /
  `deterministic_order` / `apply_window_pagination` /
  `window_partition_for_prefetch`) live once in `plans.py` and are imported by
  `connection.py` and `walker.py`, holding the cursor-parity invariant by
  construction.
- **New helpers considered.** Every cross-file collapse candidate was evaluated
  and correctly deferred (see `## DRY analysis`) — none fires at 0.0.9. The
  `_iter_field_descendants` fold is the natural vehicle for the now-closed
  `selections.py` directive Medium and is correctly deferred to a future DRY
  cycle rather than done speculatively. (The prior stale folder artifact's
  act-now `FieldMeta._from_field_shape` cross-folder bullet is ALREADY LANDED —
  `_from_field_shape` is the live shared builder consumed by `from_django_field`
  and `types/resolvers.py::_field_meta_for_resolver` per the verified
  `rev-optimizer__field_meta.md`; not re-raised.)
- **Duplication risk across the folder.** The static helper's per-file repeated
  literals are all within-file reflective attribute names read via `getattr`
  (`selections` 7x + `directives` 4x in `selections.py`; `_strawberry_schema` 2x
  in `extension.py`; `prefetch_to` / `queryset` 2x in `plans.py`; `arguments` /
  `prefetch` / `related_model` / `_optimizer_runtime_prefixes` in `walker.py`) —
  none is a shared dispatch-key literal re-spelled across two+ files. `selections`
  appears in both `selections.py` and `walker.py`, but as the graphql/converted
  AST attribute name both duck-type, not a constant candidate;
  `_optimizer_runtime_prefixes` is the agreed converted-selection marker name,
  written once in `selections.py::with_runtime_prefix` and read in `walker.py` —
  the marker contract, intentional, not duplication.

### Other positives

- **Import direction is strictly one-way (acyclic DAG), confirmed at source.**
  Leaves `_context.py` and `selections.py` import nothing first-party/intra-folder
  (stdlib + graphql-core only). `field_meta.py` / `hints.py` / `plans.py` depend
  only on `..exceptions` and `..utils`. `walker.py` -> `hints` / `plans` /
  `selections` / `..` (no edge to `extension`). `extension.py` -> `_context` /
  `hints` / `plans` / `selections` / `walker` (top of the DAG). `__init__.py` ->
  `extension`. No back-edges; `connection.py` (root) consumes
  `extension.apply_connection_optimization` + `selections.direct_child_selected`
  downward. The documented within-walker import-cycle deferrals
  (`from ..types.definition import origin_has_custom_id_resolver` at call time;
  `_relay_max_results_from_info` reading `schema._strawberry_schema.config`
  without importing the extension helper) are real and correct.
- **`optimizer/__init__.py` export correctness.** `__all__ = ("DjangoOptimizerExtension", "logger")`
  re-exports exactly the consumer-facing extension plus the canonical `logger`
  handle (re-exported from the top-level package so the
  `"django_strawberry_framework"` literal lives in one place). Both are
  load-bearing: production siblings `extension.py` / `walker.py` consume `logger`
  via `from . import logger`, and the pass-through tests pin the re-export
  contract. `OptimizationPlan` / `plan_optimizations` are deliberately NOT
  re-exported (internal, reached via dotted module paths) — the docstring states
  this accurately. Correct subpackage facade.
- **`OptimizerError` raise-site consistency.** Two raise sites, both typed and
  caller-locating: `field_meta.py:156` (input lacking `name`/`is_relation`, the
  guard that converts a would-be late walker `AttributeError` into a typed
  call-site failure) and `plans.py:567`/`575` (`window_partition_for_prefetch`
  non-windowable kinds). The `plans.py` raises are caught fail-soft by
  `walker.py::_plan_connection_relation` (`walker.py:1237 except OptimizerError`)
  to fall back per-parent — the documented contract. `ConfigurationError` raises
  (`hints.py` four conflict shapes; `walker.py` hint-rebase / lookup mismatch)
  are construction/build-time misconfiguration, the correct distinct type. Error
  vocabulary is consistent across the folder; no drift. (Note: the anonymous
  inline fragment crash is precisely a case where the package routes through a
  Strawberry internal instead of its own typed-error substrate — the High's fix
  brings that path back under the package's own fragment-aware handling.)
- **No import-time side effects across the folder.** No module runs ORM or
  registry work at import; the extension installs no global state at import time;
  the optimizer is opt-in (`apply_connection_optimization` returns the queryset
  unoptimized when no extension is active). Confirmed via the shadow overviews
  (zero import-time executable markers beyond constant/dataclass definitions).
- **Comment consistency.** The two version-pinned future labels flagged across
  the folder (`extension.py`'s `0.1.2` `search:` comment; the recurring
  version-pinned-docstring rot class) are the only comment-tier maintainability
  snags, both forward-looking and trigger-gated in their file artifacts; no
  folder-level comment inconsistency. GLOSSARY entries for the folder's
  public-contract surfaces (`#djangooptimizerextension`, `#plan-cache`,
  `#schema-audit`, "Connection-aware optimizer planning", `#optimizerhint`) were
  each verified accurate against live source in their file cycles — no drift; the
  only open GLOSSARY item is the forward-looking `_context` stash-key Low above.

### Summary

Folder pass over the 8 optimizer modules (7 reviewed siblings + the subpackage
`__init__.py`), all 7 file artifacts `verified`. The subpackage is a clean,
strictly one-way DAG: `selections.py` and `_context.py` are the leaf substrates;
`field_meta` / `hints` / `plans` sit above; `walker` consumes them; `extension`
sits at the top and re-exports through `__init__.py`. The 0.0.9 `selections.py`
consolidation genuinely removed the reverse `extension <- walker` dependency and
is consumed consistently by its three advertised consumers (the cache-key AST
walk, the plan walk, and the `totalCount` detection), with `is_fragment` as the
single shared fragment-vs-field discriminator. `OptimizerError` /
`ConfigurationError` raise-site vocabulary is consistent, `__init__.py` exports
exactly the consumer-facing surface, and no cross-file repeated-literal or
back-edge concerns exist. This pass carries ONE open High forwarded from the
walker artifact and re-confirmed live this pass: an anonymous inline fragment
(`... { ... }`, `type_condition=None`) under any optimized field crashes the
resolver with `'NoneType' object has no attribute 'name'` because
`extension.py::apply_to` (`extension.py:783`) routes `info.field_nodes` through
Strawberry's `convert_selections`, whose `InlineFragment.from_node` dereferences
`type_condition.name` on the `None` condition; it spans both the connection and
the middleware list paths, and typed inline fragments / named spreads / the
baseline are all safe. The root-cause fix is a fragment-aware
`ast_to_converted_selections` adapter in `selections.py` (reusing the existing
`is_fragment` duck-typing) plus rewiring the `extension.py:783` call to it — no
try/except — with live fakeshop pins on both paths plus a typed-fragment
regression guard. Two forward-looking Lows (the `info.selected_fields`
`totalCount`-seam consistency check gated on the High's fix; the `_context`
GLOSSARY stash-key documentation). `Status: under-review` — there is a High to
fix, so Worker 2 implements before this folder pass can verify.

---

## Fix report (Worker 2)

### Live re-confirmation (pre-fix, in-process `schema.execute_sync` against fakeshop, `seed_data(3)` + 3 genres)

Matches the artifact: anonymous inline fragment crashes with
`AttributeError: 'NoneType' object has no attribute 'name'` on BOTH paths;
typed inline + baseline OK.

- `{ allItems { edges { node { ... { name } } } } }` (connection, node-level) -> CRASH
- `{ allItems { ... { edges { node { name } } } } }` (connection, direct) -> CRASH
- `{ allGlossaryTerms { ... { title } } }` (plain list / middleware) -> CRASH
- `{ allLibraryGenresConnection { totalCount ... { edges { node { name } } } } }` -> CRASH
- `{ allItems { edges { node { ... on ItemType { name } } } } }` (typed) -> OK
- `{ allItems { edges { node { id name } } } }` (baseline) -> OK

**The `apply_to` rewire alone did NOT fix the connection path** — a refreshed
live trace after rewiring `extension.py` showed the connection-path crash now
terminates in Strawberry's OWN `relay/utils.py::should_resolve_list_connection_edges`
(`relay/utils.py:88`) reading `info.selected_fields`, reached via
`connection.py::DjangoConnection.resolve_connection #"super().resolve_connection"`
-> Strawberry `ListConnection.resolve_connection` (`relay/types.py:899`). This
crash fires DURING `_next` (the field resolver), BEFORE the middleware's
`_optimize`/`apply_to` runs — so on the connection path the artifact's
"`apply_to` crashes first" ordering is inverted at this Strawberry version
(0.316.0): `info.selected_fields` is the load-bearing first site. The Low's
flagged "SECOND fix site" is therefore the FIRST one on the connection path and
was implemented (see below). The plain-list path's first/only site IS `apply_to`
(no `ListConnection`), fixed by the rewire.

### Files touched

- `django_strawberry_framework/optimizer/selections.py` — (1) added
  `ast_to_converted_selections(info, field_nodes)`: the package-owned
  anonymous-safe mirror of Strawberry's `convert_selections`. Reimplements the
  WHOLE recursion (an anonymous inline fragment can sit at any depth, and
  Strawberry's `SelectedField.from_node` recurses back into the crashing
  converter) using Strawberry's own `SelectedField`/`FragmentSpread`/`InlineFragment`
  dataclasses so the list is drop-in for both the package's duck-typed substrate
  (`is_fragment`) AND Strawberry's `isinstance`-based consumers; the only
  deviation is `type_condition = node.type_condition.name.value if node.type_condition is not None else None`.
  (2) added `prime_selected_fields(info)`: seeds the `Info.selected_fields`
  `cached_property` slot (`info.__dict__["selected_fields"]`) with that safe
  conversion, idempotent + no-op when already populated or no field nodes —
  routes every later read (the package's `_total_count_requested` AND
  Strawberry's `should_resolve_list_connection_edges`) through the safe list.
- `django_strawberry_framework/optimizer/extension.py` — rewired
  `apply_to` (`#"ast_to_converted_selections(info, info.field_nodes)"`) from
  `strawberry.types.nodes.convert_selections` to the new adapter; added
  `ast_to_converted_selections` to the `.selections` import; replaced the
  Strawberry-internal comment with the anonymous-fragment rationale.
- `django_strawberry_framework/connection.py` — call `prime_selected_fields(info)`
  in `_resolve_connection_fast_path` immediately AFTER `_guard_first_and_last`
  (so a `first`+`last` error still short-circuits before `info` is touched —
  `test_first_and_last_guard_on_generated_subclass` passes a minimal info; the
  helper's `getattr` guards make it a no-op there) and BEFORE the `want_count`
  lambda / `super().resolve_connection`. Shared head of BOTH the bare and the
  `totalCount` variants, so one prime covers both. Added `prime_selected_fields`
  to the `.optimizer.selections` import.

### Audit verdict — every other `convert_selections` / `info.selected_fields` site

- `connection.py::_total_count_requested` (`connection.py:390`, `info.selected_fields`):
  **REACHABLE second site, FIXED** — the prime in `_resolve_connection_fast_path`
  runs before the `want_count=lambda: _total_count_requested(info)` evaluation, so
  the read returns the safe list. Live-confirmed: `totalCount` + anonymous fragment
  resolves with `totalCount == 3`.
- Strawberry `should_resolve_list_connection_edges` -> `info.selected_fields`
  (Strawberry-owned, reached via `super().resolve_connection`): **REACHABLE, FIXED**
  by the same prime (it is the first crash on the connection path). Cannot route
  Strawberry's internal off `info.selected_fields`, so priming the cache is the
  root-cause fix that does NOT reimplement Strawberry's slicing engine and uses NO
  try/except.
- `definition.selected_fields` in `types/finalizer.py` (413/468/627),
  `types/resolvers.py:306`, `management/commands/inspect_django_type.py:167`:
  **NOT the crashing converter** — these read `DjangoTypeDefinition.selected_fields`
  (a package list attribute), not Strawberry's `Info.selected_fields` property.
  No anonymous-fragment exposure. No edit.
- `extension.py` cache-key AST walk (`_build_cache_key` etc.): walks raw
  graphql-core AST via the `ast_child_selections` adapter family, never
  `convert_selections`. No edit.

### Tests added (live fakeshop `/graphql` per AGENTS.md; each fails pre-fix, passes post-fix)

- `examples/fakeshop/test_query/test_library_api.py::test_anonymous_inline_fragment_under_connection_field_resolves`
  — anonymous inline fragment under `allLibraryGenresConnection`, both node-level
  (`edges { node { ... { name } } }`) and direct-under-field (`... { edges ... }`);
  asserts no `errors` + seeded names. Pins the connection High.
- `…::test_anonymous_inline_fragment_with_total_count_resolves` — `totalCount` +
  anonymous inline fragment; asserts no `errors`, `totalCount == 3`, edges resolve.
  Pins the reachable `_total_count_requested` / `should_resolve_list_connection_edges`
  second site.
- `…::test_typed_inline_fragment_under_connection_field_still_resolves` — typed
  `... on GenreType { name }` regression guard (passes pre+post; guards the typed
  path the adapter must keep working).
- `examples/fakeshop/test_query/test_glossary_api.py::test_anonymous_inline_fragment_under_list_field_resolves`
  — anonymous inline fragment under the plain `allGlossaryTerms` list field
  (middleware list path); asserts no `errors` + seeded titles. Pins the list path.

All four query shapes re-run live POST-fix over the HTTP test client
(`setup_test_environment` for `testserver` ALLOWED_HOSTS) — all return no
`errors` with the asserted data (`totalCount == 3` on the totalCount case).

### Validation run

- `uv run ruff format .` — pass (reformatted `test_library_api.py` only — new test bodies)
- `uv run ruff check --fix .` — pass (All checks passed)
- Focused live validation: pre-fix crash repro + post-fix resolution on all four
  shapes + typed/baseline, via both `schema.execute_sync` and the HTTP test client.
- pytest NOT run (AGENTS.md / role file).
- `uv.lock` — untouched (`git status` clean).

### Notes for Worker 3

- No shadow file used (read live source + the installed Strawberry 0.316.0
  `relay/utils.py` / `relay/types.py` / `types/info.py` / `types/nodes.py` to
  trace the real crash frame).
- The artifact's "`apply_to` crashes first on the connection path" premise is
  inverted at Strawberry 0.316.0 (the `info.selected_fields` read in
  `should_resolve_list_connection_edges` fires first, during `_next`). Not a
  false-premise REJECTION — the artifact's recommended `apply_to` rewire is still
  necessary (it is the list-path fix and the connection-path optimizer-pass fix),
  and the artifact explicitly anticipated the `info.selected_fields` second site
  in the Low and told me to fix it if reachable. I implemented BOTH; the prime is
  the load-bearing connection-path fix.
- `prime_selected_fields` writes `info.__dict__["selected_fields"]` — this IS the
  `functools.cached_property` storage slot Strawberry uses, so it is the supported
  priming mechanism, not a private-API hack; idempotent and guarded so a legitimate
  earlier read is never overwritten.
- The two forward-looking Lows are preserved untouched (the `info.selected_fields`
  consistency-check Low is now CLOSED by this cycle's prime — recorded here, not
  edited out, per append-only).

---

## Verification (Worker 3)

### Logic verification outcome — LOGIC PASS (interim)

**Crash fixed on ALL paths (pre/post repro via baseline worktree + live tests).**
Created a detached worktree at baseline `0872a20`, copied the working-tree test
files in, and ran the four High pins against PRE-FIX source:
`test_anonymous_inline_fragment_under_connection_field_resolves`,
`…_with_total_count_resolves`, and the glossary list-path
`test_anonymous_inline_fragment_under_list_field_resolves` all **FAIL pre-fix**
with the exact documented `AttributeError: 'NoneType' object has no attribute
'name'` (traceback terminates at `strawberry/types/nodes.py:126`
`InlineFragment.from_node`); the typed-fragment regression guard
`test_typed_inline_fragment_under_connection_field_still_resolves` **passes
pre-fix** (correct — it is a regression guard, not a crash repro). All four
**pass POST-fix** (working tree). So the crash is fixed under (a) a connection
field — anonymous fragment at node level AND directly under the field, (b) a
plain list field (`allGlossaryTerms`, middleware path), and (c) with
`totalCount`; the typed `... on T {}` form still resolves.

**FAITHFUL-MIRROR property — VERIFIED (diff probe).**
`docs/review/temp-tests/optimizer_high/probe.py` (Part 2) and `probe_args.py`
diff `ast_to_converted_selections` against Strawberry's `convert_selections`
field-by-field across 8 non-anonymous query shapes (plain nested + alias +
arguments; typed inline fragment; named fragment spread; field `@include`
directive with variable; multi-field + `pageInfo`; nested object/list
`filter:`/`orderBy:` arguments exercising `convert_value`'s list/object
recursion; mixed named + typed fragments; literal+variable directive args). All
shapes are **identical** under both a normalized-tuple compare AND
`dataclasses.asdict` deep-equality (incl. nested argument/directive values).
The adapter also returns Strawberry's OWN `SelectedField`/`FragmentSpread`/
`InlineFragment` dataclass instances (`isinstance` check passes), so Strawberry's
`isinstance`-based consumer `should_resolve_list_connection_edges` works on the
list. The ONLY divergence is the intended `type_condition=None` on the anonymous
inline branch. Priming the cached-property slot therefore does not change
`info.selected_fields` for any normal query — no risk to slicing / pagination /
totalCount / other consumers.

**PRIMING COMPLETENESS — VERIFIED.** The only read of Strawberry's converting
`Info.selected_fields` property in the package is
`connection.py::_total_count_requested` (`connection.py:390`); grep confirms the
`finalizer.py` / `resolvers.py` / `inspect_django_type.py` `selected_fields`
hits all read `DjangoTypeDefinition.selected_fields` (a package list attribute,
NOT the crashing converter). On the connection resolve path,
`DjangoConnection.resolve_connection` (and the `totalCount` variant's
`resolve_connection`) call `_resolve_connection_fast_path` — which runs
`prime_selected_fields(info)` immediately after the guard — as the FIRST step,
strictly before (i) the `want_count` lambda evaluation of
`_total_count_requested` (evaluated inside `_resolve_connection_fast_path` AFTER
the prime) and (ii) `super().resolve_connection` → Strawberry's
`ListConnection.resolve_connection` → `should_resolve_list_connection_edges`
read. The `apply_to` optimizer-pass crash (which on this query shape fires via
`_finalize_queryset` → `apply_connection_optimization` → `apply_to` BEFORE
`resolve_connection`, confirmed in the pre-fix trace) is covered by the
`ast_to_converted_selections` rewire in `apply_to` itself, not the prime — so the
two fixes are complementary and there is no reachable path that reads
`info.selected_fields` before priming, nor a path where the optimizer pass reads
the crashing converter after the rewire. `prime_selected_fields` is idempotent
(no-op when the slot is already populated — verified it does not overwrite a
legitimate prior read), no-ops on empty `field_nodes`, and is `getattr`-guarded
against a missing `_raw_info` (verified live). Priming targets the genuine
`functools.cached_property` storage slot `info.__dict__["selected_fields"]`
(confirmed `Info.selected_fields` is a `cached_property` and computes
`convert_selections(self._raw_info, self._raw_info.field_nodes)` — the adapter is
fed the same `_raw_info`, faithful).

**ABSTRACTION judgment — chosen approach is the RIGHT root-cause fix, not a
workaround.** Routing the package's OWN conversion through its OWN
`selections.py` substrate (the `docs/feedback.md` Major 2 consolidation home) is
the contained, correct fix at the package's abstraction boundary: it removes the
dependency on a Strawberry internal that mishandles a spec-valid query, uses NO
try/except (per AGENTS.md), and adds a typed adapter the existing fragment-aware
helpers already flow through. I considered the alternative of a global Strawberry
monkeypatch via the `_django_patches` mechanism and reject it as the wrong tool
here: (1) `_django_patches` is explicitly scoped to upstream **Django** bugs
(named, AppConfig-applied, Trac-tracked), not Strawberry; (2) patching
`InlineFragment.from_node` / the `InlineFragment.type_condition: str` contract to
admit `None` would mutate a third-party dataclass's typed contract that
Strawberry's own `isinstance`-based consumers depend on — strictly more invasive
and fragile than seeding a per-instance cached value the faithful-mirror proof
shows is byte-identical to what Strawberry would compute. Priming is a legitimate,
contained, correct fix for the one site the package cannot route
(`info.selected_fields`, read by Strawberry's own code).

**RESERVATION (recorded concern, NOT a logic-pass blocker — surface to
maintainer).** Priming a third-party `cached_property` couples the fix to two
Strawberry internals staying stable: `Info.selected_fields` remaining a
`cached_property` keyed under `info.__dict__["selected_fields"]`, and the raw
info remaining `Info._raw_info`. Verified live
(`docs/review/temp-tests/optimizer_high/probe_fragility.py`): if Strawberry
renames `_raw_info`, `prime_selected_fields` SILENTLY no-ops
(`getattr(info, "_raw_info", None)` → `None` → no seeding) and the connection-path
crash would silently RETURN — it degrades to the original bug rather than failing
loudly. Today (Strawberry 0.316.0, pinned) it is correct and the four live tests
pin it, so a Strawberry bump that broke the internal would be caught by the
suite. This is forward-looking maintainability fragility of the same class as the
folder's existing version-pinned-comment-rot Low — flagging it for the maintainer
(the prime has no version-pin assertion / fail-loud guard on the Strawberry
internals it depends on). Not a defect in the shipped behavior.

**Tests fail-pre / pass-post, placement, not over-fit.** Confirmed above (3 crash
pins FAIL pre / PASS post; typed guard passes both). Placement is AGENTS.md-correct:
live `/graphql` HTTP tests in `examples/fakeshop/test_query/` —
`test_library_api.py` for the connection path (`allLibraryGenresConnection` is the
root `DjangoConnectionField(GenreType)`, co-located with the existing connection
live-coverage block and `_seed_genres` inline `Model.objects.create` per the
library-app convention) and `test_glossary_api.py` for the list path. A defensible
improvement over the artifact's suggested `test_products_api.py` (co-locates with
the connection fixtures). Tests assert no-`errors` + correct seeded data (+ COUNT
counts on the totalCount case); not over-fit. High has tests → no-test-rationale
gate satisfied.

### DRY findings disposition
No DRY item fires at folder scope (artifact `## DRY analysis`: all
deferred-with-trigger or already-landed). The fix did not introduce a new
duplication: `ast_to_converted_selections` is a deliberate, single-home adapter in
`selections.py` mirroring `convert_selections` (the one place the package can fix
the anonymous shape); `prime_selected_fields` is its companion seeding helper.
Both live in the documented consolidation home, consumed by `extension.py`
(`apply_to`) and `connection.py` (`_resolve_connection_fast_path`) via the
established underscore-aliased / named imports. The `_iter_field_descendants`
fold and `edges { node }` lift remain correctly deferred.

### Temp test verification
- `docs/review/temp-tests/optimizer_high/probe.py` — pre-fix crash repro (stock
  `convert_selections`), adapter no-crash, faithful-mirror field-by-field diff
  (5 shapes), prime slot/idempotency/guards, relay-util acceptance of primed list.
- `docs/review/temp-tests/optimizer_high/probe_args.py` — deep `dataclasses.asdict`
  faithful-mirror with nested object/list arguments + mixed fragments + directive
  variable values (3 shapes).
- `docs/review/temp-tests/optimizer_high/probe_fragility.py` — confirms the
  `_raw_info`-rename silent-no-op degradation (the recorded reservation).
- Baseline worktree (`/tmp/dsf-baseline` @ `0872a20`, removed after use) ran the
  four permanent live pins against pre-fix source: 3 FAIL with the documented
  AttributeError, typed guard passes.
- Disposition: all temp/probe artifacts are throwaway (Worker 0 deletes
  `docs/review/temp-tests/` at closeout); the SHIPPED behavior is already pinned by
  the four permanent live tests — no temp test is the sole proof. No new
  Medium/High behavior bug surfaced; the priming-fragility reservation is recorded
  prose, not a promotion-required finding.

### Two forward-looking Lows preserved
Both Lows are intact in the artifact body: the `info.selected_fields`
`totalCount`-seam consistency Low (now CLOSED by this cycle's prime — Worker 2
recorded the closure in `## Notes for Worker 3` per append-only, not edited out)
and the `_context` GLOSSARY stash-key documentation Low (no source edit, routed
forward; defer triggers still unfired). Neither was actioned as a source change
this cycle, correctly.

### Verification outcome
`logic accepted; awaiting comment pass` — sets top-level `Status: logic-accepted`.
Checkbox NOT marked (interim). Comment/docstring pass and changelog disposition
remain for subsequent sub-passes.

---

## Comment/docstring pass

Docstring-only, ZERO executable change. The logic pass already wrote substantial
docstrings on both new helpers and complete inline comments at the two call sites
(`extension.py::apply_to`, `connection.py::_resolve_connection_fast_path`); this
pass closes the specific gaps the dispatch named, lifting Worker 3's
faithful-mirror / priming-completeness findings and the Strawberry-internals
coupling reservation into the source docstrings.

### Files touched

- `django_strawberry_framework/optimizer/selections.py::ast_to_converted_selections`
  — appended a FAITHFUL-MIRROR paragraph to the docstring: byte-identical output
  to `convert_selections` for every non-anonymous shape (verified field-by-field,
  incl. nested argument/directive values), differing only in the
  `type_condition=None` anonymous branch; WHY that identity is load-bearing (the
  list is primed into `info.selected_fields`, so any divergence corrupts
  `info.selected_fields` for normal queries when a connection primes it); and the
  instruction to keep it a mirror (mirror upstream changes rather than diverge).
  The pre-existing docstring already covered the anonymous-safe-mirror purpose and
  the `InlineFragment.from_node` `type_condition=None` crash; not re-stated.
- `django_strawberry_framework/optimizer/selections.py::prime_selected_fields`
  — added two paragraphs: (1) must run BEFORE any `info.selected_fields` read on
  the connection path (cached property computes once on first read; names the
  `_resolve_connection_fast_path` call ordering after the guard, ahead of
  `_total_count_requested` and `super().resolve_connection`); (2) a `NOTE` that it
  COUPLES to Strawberry internals (`Info._raw_info` + the `selected_fields`
  cached-property dict-slot) and will SILENTLY no-op (degrading to the original
  crash) if Strawberry renames them, with the live `test_anonymous_inline_fragment_*`
  tests named as the regression net on a Strawberry version bump.

No edit to `extension.py` / `connection.py` this pass: the logic-pass inline
comments at both call sites already document the anonymous-fragment rationale, the
prime-before-read ordering, and the guard-short-circuits-first ordering at the
correct altitude. Re-reviewed; nothing stale or missing.

### Per-finding dispositions

- High (anonymous-inline-fragment crash): logic accepted by Worker 3. Comment pass
  — both helper docstrings completed per dispatch (faithful-mirror identity +
  must-stay-a-mirror on `ast_to_converted_selections`; run-before-read + internals
  coupling + silent-no-op + live-test regression-net on `prime_selected_fields`).
- Low (Strawberry-internals coupling / fail-loud guard): RECORDED as a new
  forward-looking Low in the `## Low:` section, not fixed (maintainer-escalation
  item; trigger = maintainer-opts-fail-loud OR Strawberry major bump).
- Low (`info.selected_fields` `totalCount`-seam consistency): closed by the logic
  pass's prime; no comment action.
- Low (`_context` GLOSSARY stash keys): forward-looking, defer triggers unfired; no
  comment action.

No GLOSSARY edit: the artifact identified no GLOSSARY drift for the new helpers
(both are internal underscore-free module functions with no consumer-facing
GLOSSARY entry); the only open GLOSSARY item is the forward-looking `_context`
stash-key Low.

### Validation run

- `uv run ruff format .` — pass (no changes; 265 files unchanged)
- `uv run ruff check --fix .` — pass (All checks passed)
- pytest NOT run (AGENTS.md / role file).
- `uv.lock` — untouched (clean).

### Notes for Worker 3

- No shadow file used.
- ZERO logic / executable change this pass — both edits are insertions inside
  existing `"""..."""` docstring blocks of `ast_to_converted_selections` and
  `prime_selected_fields`. The `selections.py` diff-vs-baseline is logic-pass +
  comment-pass combined (the two functions did not exist at baseline `0872a20`);
  the comment-pass delta is the two prose blocks added inside those docstrings.
- The new forward-looking Low (fail-loud guard on the `prime_selected_fields`
  coupling) is the maintainer-escalation item; it codifies Worker 3's recorded
  RESERVATION from the logic-verification section. No source edit for it.

---

## Changelog disposition

### State

`Warranted but deferred to maintainer`.

### Reason

The fixed crash escaped a RELEASED contract. The anonymous-inline-fragment crash
(`'NoneType' object has no attribute 'name'`) is reachable on the plain
list-field / optimizer-middleware path, and that path shipped in **0.0.7** and
**0.0.8**:

- `DjangoListField` shipped in **0.0.7** (CHANGELOG `## [0.0.7] - 2026-05-27`
  Added entry; `list_field.py` present at the 0.0.7 bump commit `5f0ffa5b`).
- The crashing call `convert_selections(info, info.field_nodes)` in
  `DjangoOptimizerExtension._optimize` was introduced **2026-04-30** (commit
  `32b7e033`, "Refactor DjangoOptimizerExtension to implement O3 optimizations"),
  BEFORE the 0.0.7 release, and was present unguarded in the released middleware
  list path of BOTH 0.0.7 (`resolve` -> `_optimize` -> `convert_selections`,
  extension.py:531/563/605 at `5f0ffa5b`) and 0.0.8 (extension.py:528/560/602 at
  the 0.0.8 bump commit `171a9bc1`).
- No anonymous-fragment / `type_condition=None` guard existed in either released
  extension (`grep -c type_condition` = 0 at both `5f0ffa5b` and `171a9bc1`), and
  the anonymous-safe adapter home `optimizer/selections.py` is **new in 0.0.9**
  (ABSENT at both 0.0.7 and 0.0.8).

So a real consumer running 0.0.7 or 0.0.8 who issued a spec-valid
anonymous-inline-fragment query (`{ allGlossaryTerms { ... { title } } }`)
against any `DjangoListField` / optimizer-covered list resolver would have hit
the crash. The new-in-0.0.9 `DjangoConnectionField` connection path is the
SECOND affected surface, but the list-path reachability in a shipped release is
what makes this a Fixed entry for a shipped-contract crash, not an
internal-to-new-feature correctness fold.

This is the warranted-but-deferred case (REVIEW.md / worker-2.md "Changelog
dicta": a behavioural fix at a public API surface where the package is pre-alpha
and the maintainer owns CHANGELOG cadence): the dispatch did NOT authorise a
`CHANGELOG.md` edit, AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly
instructed") forbids it, and a per-file / folder-pass cycle is never the
authorising scope. Distinct from the same-release internal-correctness folds
(inspect_django_type High, selections.py `should_include` Medium), which were
`Not warranted` because their surfaces were new-in-0.0.9 and never escaped a
released contract; this crash's list path predates 0.0.9.

### What was done

No `CHANGELOG.md` edit (maintainer not authorised this cycle). Maintainer-ready
Fixed-entry text preserved verbatim below for lift at release time, under the
0.0.9 `### Fixed` section.

#### Suggested CHANGELOG entry (0.0.9 `### Fixed`)

```
- **Anonymous inline fragments under an optimized field no longer crash the resolver.** A spec-valid query placing an anonymous inline fragment (`... { ... }`, with no `on TypeName` type condition) under any optimizer-covered field — a [`DjangoListField`][glossary-djangolistfield] or other list resolver on the middleware path, or the new [`DjangoConnectionField`][glossary-djangoconnectionfield] connection path — previously failed with `AttributeError: 'NoneType' object has no attribute 'name'` (surfaced to the consumer as a `GraphQLError` on the field), because the optimizer routed selection conversion through Strawberry's `convert_selections`, whose inline-fragment builder dereferences `type_condition.name` on the `None` condition of an anonymous fragment. Corrects `0.0.7`/`0.0.8` behavior on the list path (the optimizer middleware shipped this crash for any `DjangoListField` query carrying an anonymous inline fragment) and covers the new connection path in the same fix. Typed inline fragments (`... on T { ... }`), named fragment spreads, and fragment-free selections were unaffected and stay working.
```

### Validation run

- `uv run ruff format .` — pass / no-changes
- `uv run ruff check --fix .` — pass / no-changes

---

## Iteration log

## Verification (Worker 3, comment pass)

### No logic changed since logic-accept — CONFIRMED
The comment-pass delta is docstring-text-only. AST-dumped the executable bodies
of both new helpers (docstring stripped via `ast`) and confirmed them
byte-equivalent to the logic-accepted skeleton:

- `ast_to_converted_selections` — full `_convert` recursion over
  `InlineFragmentNode` / `FragmentSpreadNode` / else, the sole deviation
  `type_condition = condition.name.value if condition is not None else None` on
  the anonymous inline branch, building Strawberry's own
  `SelectedField`/`FragmentSpread`/`InlineFragment`, returning
  `_convert(field_nodes)`.
- `prime_selected_fields` — `getattr(info, "_raw_info", None)` →
  `getattr(raw_info, "field_nodes", None)` → `not field_nodes or
  "selected_fields" in info.__dict__` no-op/idempotency guard →
  `info.__dict__["selected_fields"] = ast_to_converted_selections(raw_info,
  field_nodes)`.

No executable line added, removed, or reordered relative to logic-accept — only
prose inside the two `"""..."""` blocks. Logic unchanged → not `revision-needed`.

### Docstring accuracy — VERIFIED
- `ast_to_converted_selections`: docstring states the FAITHFUL-MIRROR property
  (byte-identical to `convert_selections` for every non-anonymous shape, verified
  field-by-field incl. nested argument/directive values; only the anonymous
  branch deviates with `type_condition=None`) AND why it is load-bearing — the
  list is primed into `info.selected_fields`, so any divergence corrupts
  `info.selected_fields` for normal queries when a connection primes it. Includes
  the must-stay-a-mirror instruction. Non-restating, accurate against source,
  symbol-qualified per AGENTS.md #27.
- `prime_selected_fields`: docstring states the run-before-read ordering (the
  `cached_property` computes once on first read; names the
  `_resolve_connection_fast_path` call site after the `first`+`last` guard, ahead
  of `_total_count_requested` and `super().resolve_connection`) AND the
  Strawberry-internals coupling / silent-no-op caveat (couples to `Info._raw_info`
  and the `info.__dict__["selected_fields"]` cached-property slot; a future
  `_raw_info` rename makes the prime SILENTLY no-op so the crash returns rather
  than failing loud), with the live `test_anonymous_inline_fragment_*` fakeshop
  tests named as the regression net on a Strawberry version bump. Accurate,
  non-restating, local idiom.

No raw `path:NN` line refs in either docstring (grep clean) — refs are
symbol-qualified `module::Symbol` / `Class.method`, AGENTS.md #27-compliant. No
`extension.py` / `connection.py` source comment touched this pass (logic-pass
inline comments already document the rationale at the right altitude;
re-confirmed nothing stale).

### Fail-loud-guard forward-looking Low — RECORDED with trigger
The new forward-looking Low is in `## Low:` ("Fail-loud guard / Strawberry-version
assertion on the `prime_selected_fields` internals coupling") with its trigger:
maintainer opts for explicit fail-loud over the live-test regression net, OR a
Strawberry major-version bump. No source edit (maintainer-escalation item),
correct. Codifies the logic-pass RESERVATION.

### Validation
- `uv run ruff format --check django_strawberry_framework/optimizer/selections.py`
  — clean (already formatted; COM812 standing notice).
- `uv run ruff check django_strawberry_framework/optimizer/selections.py` — All
  checks passed.
- `git diff -- CHANGELOG.md` — empty (changelog pass pending, consistent with the
  parenthetical).
- pytest NOT run (comment pass; no test introduced this pass).

### Verification outcome
`comments accepted; awaiting changelog disposition` — sets top-level
`Status: comments-accepted`. Checkbox NOT marked (interim). Changelog disposition
remains for the terminal sub-pass.

## Verification (Worker 3, terminal pass)

### High fixed at root cause across ALL paths — RE-AFFIRMED (focused pre/post repro)
Created a detached baseline worktree at `0872a20`, copied the working-tree test
files in (source stays pre-fix; confirmed baseline `selections.py` has NO
`ast_to_converted_selections` / `prime_selected_fields` and `extension.py` still
calls `convert_selections`). Ran the four High pins:

- PRE-FIX: the three anonymous-fragment pins
  (`test_anonymous_inline_fragment_under_connection_field_resolves`,
  `…_with_total_count_resolves`,
  `test_anonymous_inline_fragment_under_list_field_resolves`) all **FAIL** with the
  exact documented `AttributeError: 'NoneType' object has no attribute 'name'`,
  traceback terminating at `strawberry/types/nodes.py:126`
  `InlineFragment.from_node`; the typed-fragment regression guard
  `test_typed_inline_fragment_under_connection_field_still_resolves` **passes**
  pre-fix (correct — it is a regression guard, not a crash repro).
- POST-FIX (working tree): all four **PASS** (`4 passed`).

So the crash is fixed at root cause across: connection node-level
(`edges { node { ... { name } } }`), connection direct-under-field
(`... { edges … }`), `totalCount` + anonymous fragment (count still fires,
`== 3`), and the plain-list / middleware path (`allGlossaryTerms { ... { title } }`);
the typed `... on T {}` form stays working. Both repro dirs under
`docs/review/temp-tests/optimizer_high_terminal/` (gitignored, throwaway); the
shipped behavior is pinned by the four permanent live tests.

### Faithful-mirror + priming-completeness — RE-AFFIRMED against the final diff
Diffed the 3 source files vs baseline: the executable surface is exactly the
logic-accepted shape — `ast_to_converted_selections` (full `_convert` recursion,
sole deviation `type_condition = condition.name.value if condition is not None
else None`, building Strawberry's own `SelectedField`/`FragmentSpread`/
`InlineFragment`), `prime_selected_fields`
(`getattr _raw_info` → `getattr field_nodes` → `not field_nodes or
"selected_fields" in info.__dict__` no-op/idempotency guard → write), the
`apply_to` rewire to the adapter, and the `prime_selected_fields(info)` call in
`_resolve_connection_fast_path`. The comment pass altered NO logic (it added only
docstring prose, already confirmed via AST-dump in the comment-pass entry above),
and the final diff carries no further executable change — so the logic-accept
faithful-mirror conclusion (byte-identical to `convert_selections` for every
non-anonymous shape; only the anonymous branch deviates) and priming-completeness
conclusion both still hold.

Priming-completeness re-confirmed at source on the FINAL diff: call order in
`connection.py::_resolve_connection_fast_path` is `_guard_first_and_last` (:433)
→ `prime_selected_fields(info)` (:441) → `resolved_want_count = want_count()`
(:442) → `super().resolve_connection` (later); BOTH `resolve_connection` variants
(:469 bare, :592 `totalCount`) route through `_resolve_connection_fast_path`, so
the prime strictly precedes the package's `_total_count_requested` read AND
Strawberry's `should_resolve_list_connection_edges`. Grep re-confirms the ONLY
package read of Strawberry's converting `Info.selected_fields` is
`connection.py:390`; `types/resolvers.py:306` reads
`DjangoTypeDefinition.selected_fields` (a package list, not the converter). The
`apply_to` optimizer-pass crash (fires earlier via `_finalize_queryset` on the
list path) is covered by the `ast_to_converted_selections` rewire; the two fixes
are complementary, no reachable path reads the crashing converter after the fix.

### Changelog disposition — JUSTIFIED by git evidence; CHANGELOG untouched
`git diff -- CHANGELOG.md` and `git diff 0872a20 -- CHANGELOG.md` both EMPTY —
`CHANGELOG.md` untouched, consistent with `Warranted but deferred to maintainer`.
The "escaped a released contract" framing is honest and git-confirmed: at the
0.0.7 bump commit `5f0ffa5b` AND the 0.0.8 bump commit `171a9bc1`,
`optimizer/extension.py` carried `convert_selections` (4 hits each) with ZERO
`type_condition` guard, and `list_field.py` was present at 0.0.7 while
`optimizer/selections.py` (the anonymous-safe adapter home) was ABSENT at both —
so a 0.0.7/0.0.8 consumer issuing a spec-valid anonymous-inline-fragment query
against any `DjangoListField` / optimizer-covered list resolver would have hit the
crash on the released middleware list path. This is a genuine consumer-visible
fix, correctly distinguished from the same-release internal folds that were "Not
warranted." The maintainer-ready Fixed-entry text is present verbatim under
`#### Suggested CHANGELOG entry (0.0.9 ### Fixed)` and is accurate: anonymous
inline fragments under optimizer-covered list/connection fields no longer crash;
corrects 0.0.7/0.0.8 list-path behavior; typed inline fragments, named spreads,
and fragment-free selections unaffected and stay working.

### Tests fail-pre/pass-post, AGENTS placement, not over-fit
Confirmed above (3 crash pins FAIL pre / PASS post; typed guard passes both).
Placement is AGENTS.md-correct: live `/graphql` HTTP tests in
`examples/fakeshop/test_query/` — `test_library_api.py` (connection path,
`allLibraryGenresConnection`, co-located with the connection live-coverage block
and `_seed_genres` inline `Model.objects.create` per the library-app convention)
and `test_glossary_api.py` (list path). Tests assert no-`errors` + correct seeded
data (+ COUNT count on the totalCount case); not over-fit. High has tests →
no-test-rationale gate satisfied.

### Forward-looking Lows preserved
All three are intact: the fail-loud-guard Low ("Fail-loud guard / Strawberry-
version assertion on the `prime_selected_fields` internals coupling") in `## Low:`
with its trigger (maintainer opts fail-loud OR Strawberry major bump); the
`info.selected_fields` `totalCount`-seam consistency Low (closed by this cycle's
prime, recorded not deleted); and the `_context` GLOSSARY stash-key Low
(forward-looking, defer triggers unfired). None required a source edit this cycle.

### Cycle diff scope + sibling attribution
Cycle diff (vs `0872a20`) is exactly the 3 source files
(`optimizer/selections.py` +166, `optimizer/extension.py` +20/-13,
`connection.py` +10/-2) + 2 tests (`test_library_api.py` +208,
`test_glossary_api.py` +27). The folder pass authored zero source edits; its diff
IS the forwarded High fix (plus the closed `selections.py` file-cycle Medium
hunks — `with_runtime_prefix` docstring, `direct_child_selected` `should_include`
gate — bundled because both cycles touch the same new-this-cycle file; attribute
to `rev-optimizer__selections.md`, verified, [x] at review-0_0_9.md:96). Wider
owned-scope dirty paths (`conf.py`, `exceptions.py`, `filters/factories.py`,
`filters/sets.py`, `list_field.py`, `management/commands/inspect_django_type.py`,
`optimizer/walker.py`, `docs/GLOSSARY.md`, `tests/optimizer/test_selections.py`,
`tests/management/test_inspect_django_type.py`) all attribute to CLOSED sibling
cycles (each `Status: verified`, `[x]` at review-0_0_9.md:70/72/73/80/82/87/96/97);
`feedback2.md`/`feedback3.md` deletes = AGENTS.md #33 concurrent-maintainer work.

### Validation
- Focused repro: 3 crash pins FAIL pre-fix (documented AttributeError at
  `nodes.py:126`), typed guard passes pre; all 4 PASS post-fix.
- `uv run ruff format --check` on the 3 source files — already formatted (COM812
  standing notice). `uv run ruff check` on the 3 source + 2 test files — All
  checks passed.
- `git diff -- CHANGELOG.md` — empty. Full pytest suite NOT run (terminal-pass
  dispatch forbids it; focused repro per dispatch allowance).

### Temp test verification
- `docs/review/temp-tests/optimizer_high_terminal/` (dir created; the focused
  pre/post repro ran the four permanent live pins via a baseline worktree at
  `/tmp/dsf-baseline-w3-terminal`, removed after use).
- Disposition: throwaway (Worker 0 deletes `docs/review/temp-tests/` at closeout);
  shipped behavior is pinned by the four permanent live tests. No new finding.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
optimizer/ folder-pass checklist box at `review-0_0_9.md:98`.
