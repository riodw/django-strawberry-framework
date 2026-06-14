# Review: `django_strawberry_framework/utils/querysets.py`

Status: verified

The neutral query-source + `DjangoType.get_queryset` visibility substrate, single-sited
in the 0.0.9 DRY pass (`docs/feedback.md` Major 1). Seven symbols: `SyncMisuseError`,
`initial_queryset`, `normalize_query_source`, `apply_type_visibility_sync` / `_async`,
`post_process_queryset_result_sync` / `_async`. Cycle-safe leaf (depends only on `django`
+ `..exceptions`); consumed by `list_field.py`, `connection.py`, `types/relay.py`,
`optimizer/walker.py`, `optimizer/extension.py`, `filters/sets.py`. Static helper:
0 control-flow hotspots, 8 ORM marker lines, 4 calls of interest, 0 repeated literals.

## DRY analysis

- **None — this IS the DRY target.** The module is the canonical home the 0.0.9 pass
  extracted *to*; every resolver surface (`list_field.py:42-47,164-171`,
  `connection.py:830,867,892,999`, `types/relay.py:818,839,879,904`,
  `optimizer/walker.py:211-213`, `optimizer/extension.py:731`, `filters/sets.py:986,1005`)
  now reaches one implementation of Manager-coercion + is-queryset + colored visibility
  routing. The sync/async twins (`apply_type_visibility_sync`/`_async`,
  `post_process_queryset_result_sync`/`_async`) are the intentional color-split twin
  pattern that recurs package-wide (per worker-1 memory: awaitable-unwrap makes 2-site
  collapse net-negative); merging them behind a maybe-await abstraction would re-hide the
  exact routing the module docstring says must stay explicit per surface. No further
  consolidation candidate.

## High:

None.

## Medium:

### GLOSSARY `#syncmisuseerror` raise-site list narrowed to Relay node defaults only

`docs/GLOSSARY.md:1276` (the canonical `## SyncMisuseError` entry) and the
Relay-integration bullet at `docs/GLOSSARY.md:1063` both attribute the raise to
"`resolve_node` / `resolve_nodes` on the sync branch when `cls.get_queryset` returns a
coroutine." After the 0.0.9 DRY extraction the raise actually originates in
`utils/querysets.py::apply_type_visibility_sync` and is reached from **every** sync
visibility surface, not just the Relay node refetch defaults:

- `types/relay.py::_resolve_node_default` / `_resolve_nodes_default` (the documented pair),
- `optimizer/walker.py::_build_child_queryset` (sync prefetch-child visibility — a nested
  async-only related `get_queryset` surfaces `SyncMisuseError` at plan time, not a leaked
  coroutine into `OptimizationPlan.apply`),
- `connection.py::_pipeline_sync` (the synthesized relation-connection / sync connection
  pipeline — partially acknowledged at `GLOSSARY:836`),
- `filters/sets.py` sync related-visibility derive (`apply_type_visibility_sync` at
  `filters/sets.py:986`, caught + rethrown by `FilterSet.apply`'s sync dispatcher).

`SyncMisuseError` is a public-contract symbol (exported from the package root, GLOSSARY
roster line 35 + 132), so an undercount of where it fires is a contract-doc accuracy gap —
Medium per the GLOSSARY drift rule. The single-sourced raise site is the relevant fact;
the entry reads as though the Relay defaults are the only trigger.

Recommended verbatim replacement for the final sentence of `docs/GLOSSARY.md:1063`
(the `Raised by ...` clause):

> Raised by `utils/querysets.py`'s shared `apply_type_visibility_sync` whenever a sync
> resolver surface's `cls.get_queryset` returns a coroutine — the Relay node defaults
> (`resolve_node` / `resolve_nodes`), the connection sync pipeline, the optimizer's sync
> prefetch-child visibility, and the filter related-visibility derive all route through it;
> the unawaited coroutine is closed before the raise so Python does not emit
> `RuntimeWarning: coroutine was never awaited`.

Recommended verbatim replacement for the first sub-bullet under `docs/GLOSSARY.md:1276`
(currently `- Raised by [Relay Node integration]...on the sync branch when ...returns a coroutine.`):

> - Raised by the shared `apply_type_visibility_sync` (the 0.0.9 single-sited visibility
>   routing) on every sync visibility surface — the [Relay Node integration](#relay-node-integration)
>   defaults `resolve_node` / `resolve_nodes`, the [`DjangoConnectionField`](#djangoconnectionfield)
>   sync pipeline, the optimizer's sync prefetch-child build, and the [`FilterSet`](#filterset)
>   related-visibility derive — when `cls.get_queryset` returns a coroutine; the unawaited
>   coroutine is closed before the raise.

## Low:

### Sync path detects only true coroutines, not arbitrary non-coroutine awaitables

`apply_type_visibility_sync` gates on `inspect.iscoroutine(result)` (querysets.py:110)
while the async sibling gates on the broader `inspect.isawaitable(result)`
(querysets.py:136). The asymmetry is correct and deliberate: the sync path must `.close()`
the rejected value to suppress `RuntimeWarning: coroutine was never awaited`, and only
true coroutines expose `.close()` — `isawaitable` would also match `Future`/`Task`/custom
`__await__` objects that have no `.close()`. Because `async def get_queryset` always
returns a true coroutine, the realistic misuse is always caught. The only uncovered case
is a consumer whose sync-declared `get_queryset` returns an *exotic* non-coroutine
awaitable (custom `__await__`); that would slip past the guard and produce a downstream
`AttributeError: '...' object has no attribute 'filter'` instead of the clean
`SyncMisuseError`. This is a vanishingly rare, self-inflicted shape and the docstring
scopes the contract to the `async def` case. Defer until a consumer is observed returning
a non-coroutine awaitable from a sync `get_queryset`; then widen the sync guard to
`isawaitable` + a `getattr(result, "close", None)` close-if-present before the raise.
Recorded-intent Low only — no edit warranted now.

### `initial_queryset` missing-definition contract is an undocumented `AttributeError` shape

`initial_queryset` (querysets.py:58-68) reads
`type_cls.__django_strawberry_definition__.model._default_manager.all()` and the docstring
states a missing definition "surfaces as a raw `AttributeError`." That is the honest
fail-loud contract (callers are constructor-guarded via
`list_field.py::_validate_djangotype_target` / `connection.py` before any field reaches
this, so production never hits it), and is consistent with the package's fail-loud-on-
misuse posture. No defensive guard wanted (would mask a registration bug). Low /
recorded-intent: the docstring already names the contract, so no action.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is itself the canonical extraction target —
  consumers delegate rather than re-spell: `list_field.py` thin-wraps
  `post_process_queryset_result_*` (`_post_process_consumer_sync/_async`,
  list_field.py:42-47); `connection.py::_prepare_pipeline_source` (conn.py:830) and
  `optimizer/extension.py:731` reuse `normalize_query_source`; the four Relay node defaults
  and the connection pipeline reuse `apply_type_visibility_*` + `initial_queryset`. The
  sync/async twin split is the package-wide intentional color-split pattern.
- **New helpers considered.** Collapsing `apply_type_visibility_sync`/`_async` (or the two
  `post_process_*`) into a single maybe-await helper was rejected — the module docstring
  explicitly keeps the colored calls per-surface so a visibility-routing mistake (a
  data-leak class) is never hidden behind a maybe-await abstraction; the async sibling's
  `await` cannot live in a sync caller. Correct to keep four functions.
- **Duplication risk in the current file.** The two `result = type_cls.get_queryset(queryset, info)`
  call lines (querysets.py:109,135) are the irreducible twin heads of the sync/async split,
  not a near-copy to fold; the guard that follows each (`iscoroutine`+`.close()`+raise vs
  `isawaitable`+`await`) is genuinely different per color.

### Other positives

- **Visibility never silently bypassed.** Every queryset-returning sync surface routes
  through `apply_type_visibility_sync`; the only skip is `optimizer/walker.py:212` gated on
  `has_custom_qs`, and skipping the *default identity* `get_queryset` (which returns the
  queryset unchanged) is a correctness-preserving optimization, not a bypass. The default
  `DjangoType.get_queryset` (`types/base.py:653-666`) is the identity hook, so calling it
  unconditionally on the resolver surfaces (relay/list/connection) is harmless.
- **Multi-DB / `.using()` preservation is intact.** `initial_queryset` seeds
  `_default_manager.all()` (default alias), and the visibility hook's return is passed
  through unchanged — a consumer applying `.using(alias)` inside `get_queryset` keeps its
  `_db` because the module never re-seeds or `.all()`-rebases the hook output. This is
  consistent with GLOSSARY `#multi-database-cooperation` (`_db` preservation is owned by
  `OptimizationPlan.apply` for root querysets, not re-decided here). No `.using()` /
  `_db` access in this module — correctly out of scope.
- **`SyncMisuseError` design is sound.** Multiple-inherits `ConfigurationError` AND
  `RuntimeError` so both `except ConfigurationError` (package convention) and
  `except RuntimeError` (post-`FilterSet.apply`-rethrow consumer code) match; the unawaited
  coroutine is `.close()`d before the raise (pinned by
  `tests/utils/test_querysets.py::test_apply_type_visibility_sync_rejects_async_hook_loudly`
  under `filterwarnings = error`). The error message points the consumer at the async
  resolver path or a sync rewrite — actionable, not a bare type.
- **Manager coercion is correct and minimal.** `normalize_query_source` coerces only
  `models.Manager` via `.all()` (fresh unevaluated QuerySet), passes a `QuerySet` through
  by identity (test_normalize_query_source_passes_queryset_through pins `source is qs`), and
  reports `is_queryset=False` for Python lists/generators so each caller keeps its own tail
  (connection's GraphQL non-queryset error, list-field passthrough). Returning the
  `(source, is_queryset)` tuple instead of deciding the tail is the right seam.
- **Test discipline.** `tests/utils/test_querysets.py` pins the neutral mechanics directly
  (manager coercion, identity passthrough, sync-rejects-async-loudly with subclass
  assertions, async-awaits + async-passes-sync-through, post-process manager-coerce + list
  passthrough on both colors); deep through-schema visibility coverage is delegated to the
  surface suites per the file docstring. The async stub `_AsyncType.get_queryset` and sync
  `_SyncType` duck-type a `DjangoType` cleanly.

### Summary

A small, well-factored substrate file that is the canonical home of the visibility-routing
contract — the 0.0.9 DRY pass collapsed five surfaces' Manager-coercion + sync/async
`get_queryset` routing here, and the factoring holds up: visibility is never silently
bypassed, the sync `SyncMisuseError` fail-loud is correctly raised+closed, Manager→QuerySet
coercion is identity-preserving, and `.using()`/`_db` set inside a hook survives because
the hook output is passed through untouched. No High or behavior-changing Medium. One
Medium is a GLOSSARY contract-doc accuracy gap (the `#syncmisuseerror` and Relay-integration
entries still scope the raise to the Relay node defaults, but post-0.0.9 it fires from every
sync visibility surface via the single-sited `apply_type_visibility_sync`) — verbatim
replacement text supplied; routes through shape #4 (a real GLOSSARY edit). Two Lows are
recorded-intent / forward-looking (sync `iscoroutine`-vs-`isawaitable` narrowness for exotic
non-coroutine awaitables; `initial_queryset`'s documented raw-`AttributeError` on a
missing definition).

---

## Fix report (Worker 2)

Consolidated single-spawn (shape #4, GLOSSARY-prose only; no `querysets.py` source change). The sole Medium is a real GLOSSARY edit; both Lows are recorded-intent / forward-looking (no in-cycle edit). No logic-pass / comment-pass interaction — collapsed.

### Premise re-confirmed against source

- `SyncMisuseError` is **single-sited**: the only `raise` is `querysets.py::apply_type_visibility_sync` (querysets.py:112). `grep -rn "raise SyncMisuseError"` over the package returns exactly that one site.
- Actual sync visibility surfaces that call `apply_type_visibility_sync` (and therefore reach the raise), confirmed by grep + enclosing-symbol trace:
  - `types/relay.py::_resolve_node_default` (:818) and `types/relay.py::_resolve_nodes_default` (:879) — the documented Relay node defaults pair.
  - `connection.py::_pipeline_sync` (:867) — the connection sync pipeline.
  - `optimizer/walker.py::_build_child_queryset` (:213) — the optimizer sync prefetch-child build.
  - `filters/sets.py::_derive_related_visibility_querysets_sync` (:986) — the filter related-visibility derive (rethrown by `FilterSet.apply`'s sync dispatcher).
  - (also `list_field.py` default-resolver `:171` direct + consumer-resolver `:43` via `post_process_queryset_result_sync` — a fifth surface; the artifact's four-family enumeration is the intended public-facing list, so the GLOSSARY prose mirrors it without inflating the list with the list-field path.)
- The artifact's verbatim replacement text is **accurate as written** — the four enumerated families match source, the single-sited claim holds, and the `.close()`-before-raise detail matches querysets.py:111-112.

### Files touched

- `docs/GLOSSARY.md` (`## Relay Node integration` shipped-behavior bullet, the `SyncMisuseError` `Raised by …` clause) — replaced the Relay-defaults-only attribution with the single-sited `apply_type_visibility_sync` routing across all four sync surfaces. Verbatim from the artifact's first replacement block.
- `docs/GLOSSARY.md` (`## SyncMisuseError` first sub-bullet) — replaced the `Raised by [Relay Node integration]…` line with the every-sync-surface enumeration (Relay defaults, `DjangoConnectionField` sync pipeline, optimizer prefetch-child, `FilterSet` related-visibility derive). Verbatim from the artifact's second replacement block.

Both sites carried the stale Relay-defaults-only scope; both fixed. No `querysets.py` edit (it is already the canonical single-sited home — the artifact requested no source change).

### Anchor / link hygiene

- Used in-page anchors only: `#relay-node-integration`, `#djangoconnectionfield` (target `## \`DjangoConnectionField\`` at :294), `#filterset` (target `## \`FilterSet\`` at :465). All three anchor targets verified present. No inline cross-file `](path)` link introduced; no `<!-- LINK DEFINITIONS -->` block change.

### Tests added or updated

None. Doc-only change; no behaviour change. The single-sited raise is already pinned by `tests/utils/test_querysets.py::test_apply_type_visibility_sync_rejects_async_hook_loudly` (cited in the artifact's "What looks solid").

### Validation run

- `uv run ruff format .` — pass / no-changes (265 files unchanged).
- `uv run ruff check --fix .` — pass (all checks passed; COM812-vs-formatter warning is the standing config notice, not a finding).
- `git diff --stat <baseline> -- docs/GLOSSARY.md` — `docs/GLOSSARY.md` only (+9/-8; the larger count vs the two-line logical change reflects prior-cycle GLOSSARY edits already stacked above baseline `0872a20`).
- `uv.lock` — clean (untouched).

### Notes for Worker 3

- No shadow file used.
- Both Lows are recorded-intent / forward-looking per Worker 1 (sync `iscoroutine`-vs-`isawaitable` narrowness for exotic non-coroutine awaitables — defer until a consumer is observed; `initial_queryset`'s documented raw-`AttributeError` on a missing definition — docstring already names the contract). No edit warranted; no rejection.
- The list-field surface (`list_field.py`) is a genuine fifth sync route through `apply_type_visibility_sync` but is intentionally not added to the GLOSSARY enumeration — the artifact's verbatim text scopes to the four resolver families and the list-field path is the consumer-resolver post-process, not a distinct "where SyncMisuseError fires" surface a reader needs. Flagging so the omission reads as deliberate, not an undercount.

---

## Verification (Worker 3)

### Logic verification outcome

- **`SyncMisuseError` single-sited — confirmed.** `grep -rn "raise SyncMisuseError"` over the package returns exactly one site: `querysets.py:112` inside `apply_type_visibility_sync`. Class def at `querysets.py:35` (`SyncMisuseError(ConfigurationError, RuntimeError)`).
- **Caller enumeration independently re-greped — accurate.** `grep -rn "apply_type_visibility_sync"` + enclosing-symbol trace confirms the four named families all reach the raise: `types/relay.py:818`/`:879` (Relay node defaults), `connection.py:867` (sync pipeline), `filters/sets.py:986` (related-visibility derive, rethrown by `FilterSet.apply`), `optimizer/walker.py:213` (sync prefetch-child build). All four GLOSSARY enumerations match source.
- **Medium (GLOSSARY raise-site narrowed):** fixed at both sites with the artifact's verbatim text; accurate as written. Both lead with a complete, surface-agnostic framing (`:1063` "whenever a sync resolver surface's `cls.get_queryset` returns a coroutine"; `:1276` "on every sync visibility surface ... when `cls.get_queryset` returns a coroutine") followed by an illustrative four-family enumeration.
- **Both Lows (sync `iscoroutine`-vs-`isawaitable` narrowness; `initial_queryset` documented raw-`AttributeError`):** recorded-intent / forward-looking, no edit warranted; accepted.

### Omitted fifth surface (DjangoListField) — assessed, omission ACCEPTABLE

`list_field.py:171` (`_default` resolver sync branch) genuinely calls `apply_type_visibility_sync`, so a `DjangoListField` whose target declares an `async def get_queryset` *would* surface `SyncMisuseError` from a fifth surface not in the enumeration; `## DjangoListField` is itself a public GLOSSARY entry (:334). I judge the four-families framing acceptable rather than incomplete because **both edited hunks lead with a complete, surface-agnostic contract clause** ("the shared `apply_type_visibility_sync` ... whenever a sync resolver surface's `cls.get_queryset` returns a coroutine") that carries the actual contract; the bullet list reads as illustrative ("the Relay defaults, the connection pipeline, ... all route through it"), not a closed set, and the load-bearing correction this cycle delivers — the *single-sited* attribution to `apply_type_visibility_sync`, replacing the old Relay-only undercount — is accurate. The prose is therefore not falsified by the omission. The list-field surface omission is recorded as prose debt (a future enumeration could name it or add an explicit "including" qualifier), not a contract inaccuracy; not a reopen trigger.

### DRY findings disposition

`None — this IS the DRY target` (the 0.0.9 single-sited extraction home). No carry-forward; the sync/async twin split is the intentional package-wide color-split, correctly kept un-collapsed.

### Temp test verification

None used. Doc-only change; the single-sited raise is already pinned by `tests/utils/test_querysets.py::test_apply_type_visibility_sync_rejects_async_hook_loudly`.

### Diff scope / changelog

- `git diff <baseline> -- django_strawberry_framework/utils/querysets.py` is EMPTY (source byte-unchanged). `git diff -- CHANGELOG.md` EMPTY.
- The two `SyncMisuseError` GLOSSARY hunks (`:1063` Relay-integration bullet, `:1276` `## SyncMisuseError` sub-bullet) are this cycle's and match the artifact verbatim. Remaining `docs/GLOSSARY.md` hunks (testing relay helpers, `DjangoConnection`, `Meta.orderset_class`, `OrderSet`, `RelatedFilter`, `RelatedOrder`, `inspect_django_type`) attribute to closed sibling cycles. "No `querysets.py` source change" holds.
- In-page anchors only (`#djangoconnectionfield`:294, `#filterset`:465, `#relay-node-integration`:1051 — all present); no cross-file `](path)` link introduced.
- Changelog `Not warranted` cites BOTH AGENTS.md #21 and the active plan's silence — correct; framing matches the doc-only, internal scope.
- `uv run ruff format --check` + `ruff check` on querysets.py both pass (COM812 = standing config notice).

### Verification outcome

`cycle accepted; verified`

---

## Comment/docstring pass

Folded into the consolidated single-spawn. The cycle's only edit IS GLOSSARY prose (the contract-doc itself), so there is no separate source-comment/docstring tier to revisit — `querysets.py` was not touched and its docstrings already describe the single-sited contract accurately (module docstring lines 4-11 already name list fields, connection fields, the optimizer middleware, the Relay node defaults, and the filter related-visibility derive as the surfaces; `apply_type_visibility_sync` docstring lines 98-107 already describe the close-then-raise). No source comment/docstring change needed or made.

### Per-finding dispositions

- Medium 1 (GLOSSARY `#syncmisuseerror` raise-site narrowed): fixed at both sites (`:1063` Relay-integration bullet + `:1276` `SyncMisuseError` sub-bullet) with the artifact's verbatim text, accurate as-written.
- Low 1 (sync `iscoroutine` vs `isawaitable` narrowness): recorded-intent, deferred — no edit (trigger: a consumer returning a non-coroutine awaitable from a sync `get_queryset`).
- Low 2 (`initial_queryset` raw-`AttributeError` on missing definition): recorded-intent — docstring already names the contract, no action.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

The cycle's only edit is GLOSSARY contract-doc prose accuracy (correcting where `SyncMisuseError` is documented as firing to match the 0.0.9 single-sited `apply_type_visibility_sync`); zero behaviour change, no public symbol added or removed, no typed-error contract change. Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active review plan's silence on changelog authorization for this cycle — both required, neither alone sufficient. A per-file cycle is never the authorising scope; any genuine CHANGELOG drift forwards to the project pass (none observed here — `SyncMisuseError` itself shipped 0.0.5 and is already in the changelog history; only the GLOSSARY description drifted).

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Iteration log

(none yet)
