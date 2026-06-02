# Review: `django_strawberry_framework/types/relay.py`

Status: verified

## DRY analysis

- **Defer until a third sync/async-context dispatcher lands.** `_resolve_node_default` (`django_strawberry_framework/types/relay.py:364-397`) and `_resolve_nodes_default` (`:421-461`) share the same `in_async_context()`-discriminated dispatch shape (`id_attr = cls.resolve_id_attr(); if in_async_context(): return _resolve_<X>_async(...); qs = _apply_get_queryset_sync(...); qs = _apply_node_filter(...); ...`). Each variant differs only in the terminal materialization (`qs.get()`/`qs.first()` vs `_order_nodes(...)` against `list(qs)`), so a shared `_dispatch_node_resolver(cls, *, info, finalize_sync, finalize_async_thunk, async_helper, ...)` would lose readability. Defer until a third sync-vs-async-context Relay resolver lands (most plausibly `resolve_connection` when the connection slice ships) — fold all three through a shared helper at that point. Today's two-method split mirrors the same load-bearing-distinction calibration applied to `filters/sets.py::apply_sync` / `apply_async`.
- **Defer until the `feedback.md § High` resolution-coroutine pattern lands at a third callsite.** Both `_resolve_node_default` (`:395`) and `_resolve_nodes_default` (`:455`) follow the same three-line "fetch the initial queryset → guard sync hook → apply id filter" prelude (`qs = _apply_get_queryset_sync(cls, _initial_queryset(cls), info); qs = _apply_node_filter(qs, id_attr, ...)`). Their async mirrors at `:416-417` and `:480-482` are identical for the await-prelude shape. Defer extracting a `_sync_node_prelude(cls, id_attr, info, *, node_id=None, node_ids=None)` / `_async_node_prelude(cls, id_attr, info, *, node_id=None, node_ids=None)` helper pair until the resolver coroutine pattern picks up a third caller (likely `resolve_connection`); collapsing today would obscure the singular/plural argument-shape distinction that the per-method `_apply_node_filter` keyword choice carries.
- **Defer until the orders subsystem's TODO at `:266-273` lands.** The `_apply_get_queryset_sync` / `_apply_get_queryset_async` pair is already cited as the shared visibility-helper home in `TODO(spec-027-filters-0_0_8 Slice 1)` for `FilterSet`'s related-branch scoping. The current trigger is "Reuse these sync/async visibility helpers from FilterSet's related-branch scoping"; restate the trigger here so a future DRY cycle finds the pair without re-grepping the source.

## High:

None.

## Medium:

### M1: GLOSSARY drift on `Relay Node integration` and `Meta.interfaces` — `SyncMisuseError` public-API entry absent

`SyncMisuseError` is re-exported through `django_strawberry_framework/__init__.py:24,34` and through `django_strawberry_framework/types/__init__.py:27,29` as part of the package's public API surface. Its docstring at `relay.py:42-60` explicitly frames it as the typed marker consumers should catch ("Future consumers can match the subclass directly (`except SyncMisuseError`) without depending on the substring-of-message check"), and `filters/sets.py:1638` catches it by type as the dispatcher's sync-misuse rewrap path. The `tests/types/test_relay_interfaces.py::test_sync_misuse_raises_sync_misuse_error_subclass` test at `:887-916` pins the multiple-inheritance contract (`ConfigurationError` AND `RuntimeError`) and references "Future consumers can match the subclass directly".

Yet `docs/GLOSSARY.md` carries zero entries for `SyncMisuseError`:

- `Relay Node integration` (`docs/GLOSSARY.md:928-945`) enumerates "Shipped behavior" bullets but never names `SyncMisuseError` as the typed marker for the "async `get_queryset` invoked from a sync resolver" misuse — it only documents the composite-pk `ConfigurationError` raise.
- `Meta.interfaces` (`docs/GLOSSARY.md:635-654`) is silent on the sync-misuse contract entirely.
- The top-level public-API surface table at `docs/GLOSSARY.md` does not list `SyncMisuseError` despite its presence in `django_strawberry_framework.__all__`.

Why it matters: `SyncMisuseError` is a `ConfigurationError`-shaped exception the consumer can catch and key against, the dispatcher in `filters/sets.py` already catches it by type, and the docstring frames it as the recommended marker for consumer code. Same calibration as the GLOSSARY-drift Mediums filed in `rev-optimizer__extension.md::DjangoOptimizerExtension`, `rev-optimizer__walker.md::Queryset diffing`, `rev-management__commands__export_schema.md::Schema export management command`, and `rev-types__base.md::DjangoType`: when a primary-public-surface entry lags a shipped consumer-keyable contract, the drift is Medium not Low because the entry IS the published consumer contract.

Recommended replacement prose (Worker 2 lifts verbatim):

In the `Relay Node integration` entry at `docs/GLOSSARY.md:937-944` "Shipped behavior" list, after the `is_type_of` bullet (`:940`) and before the composite-pk bullet (`:940`), insert:

> - The framework rejects the "async `get_queryset` invoked from a sync resolver context" misuse with [`SyncMisuseError`](#syncmisuseerror) — a typed marker that multiple-inherits `ConfigurationError` AND `RuntimeError` so consumers may catch either base class while future code can match `SyncMisuseError` directly without depending on substring-of-message checks. Raised by `resolve_node` / `resolve_nodes` on the sync branch when `cls.get_queryset` returns a coroutine; the unawaited coroutine is closed before the raise so Python does not emit `RuntimeWarning: coroutine was never awaited`.

And add a new top-level entry alongside `Relay Node integration`:

> ## `SyncMisuseError`
>
> **Status:** shipped (`0.0.5`).
>
> Typed marker for the "async `get_queryset` hook invoked from a sync resolver context" misuse. Multiple-inherits [`ConfigurationError`](#configurationerror) AND `RuntimeError` so existing handlers continue to match while future code can match the subclass directly.
>
> - Raised by [Relay Node integration](#relay-node-integration)'s default `resolve_node` / `resolve_nodes` on the sync branch when `cls.get_queryset` returns a coroutine.
> - Caught and rewrapped by [`FilterSet.apply`](#filterset)'s sync dispatcher so the package's two `async get_queryset` misuse surfaces emit a single typed exception.
> - Exported through `django_strawberry_framework` so consumers can import it without reaching into private `types.relay`.
>
> **See also:** [Relay Node integration](#relay-node-integration) · [`ConfigurationError`](#configurationerror) · [`FilterSet`](#filterset).

The `Meta.interfaces` index row at `docs/GLOSSARY.md:87` and the public-API listing remain unchanged; cross-references update transparently because the new entry sits alphabetically between `safe_wrap_connection_method` and the `Schema audit` block (`:949`).

## Low:

### L1: `spec-011` citation drift — seven sites point at the wrong on-disk spec

`docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` exists at 0.0.4 and is the maintainer's stub for a different concern. The Relay foundation spec at 0.0.5 is `docs/SPECS/spec-015-relay_interfaces-0_0_5.md`. Yet `relay.py` cites `spec-011` at seven locations:

- `:85` `(spec-011 Decision 6 #"injection (Decision-1 borrow) is added unconditionally")` — the prose at `docs/SPECS/spec-015-relay_interfaces-0_0_5.md:351` (Decision 6).
- `:116-118` `(spec-011 #"A class that already inherits from one of the listed", spec-011 #"only those not already present in", spec-011 #"Inherited interfaces via parent")` — `docs/SPECS/spec-015-relay_interfaces-0_0_5.md:329`, `:339`, `:458`.
- `:125` `(spec-011 Risk note #"surface any `TypeError` as a `ConfigurationError`")` — `docs/SPECS/spec-015-relay_interfaces-0_0_5.md:541`.
- `:145` `(spec-011 #"Composite primary keys (Django 5.2+) are explicitly out of scope")` — `docs/SPECS/spec-015-relay_interfaces-0_0_5.md:287`.
- `:208` `(spec-011 #"id_attr = cls.resolve_id_attr" / Decision 7's "no avoidable lazy loads on `resolve_id`")` — `docs/SPECS/spec-015-relay_interfaces-0_0_5.md:313`.

The cited prose is correct against `spec-015`; only the pointer rotted. Same drift class as the `spec-014 → spec-018` citation rot in `rev-optimizer__extension.md` (one site), `rev-optimizer__walker.md` (two sites), the `spec-016 → spec-020` drift in `rev-list_field.md`, the `TODO-ALPHA-028 → TODO-ALPHA-035` drift in `rev-scalars.md`, and the `spec-020 → spec-025` drift in `rev-scalars.md`. Tests at `tests/types/test_relay_interfaces.py` carry the same `spec-011` token at 11 sites (`:73`, `:222`, `:267`, `:301`, `:303`, `:336`, `:512`, `:763`, `:1102-1103`, `:1126`) and need the same rewrite in lockstep.

Recommended fix: bulk-rewrite `spec-011` → `spec-015-relay_interfaces-0_0_5 Slice <N>` (or simpler `spec-015`) at all seven source sites and 11 test sites in one sweep. Lift the rewrite into the same comment-pass commit as L4 (CHANGELOG/feedback citation rot below).

### L2: `feedback.md § High` citations rotted post-spec-028 reshape

`docs/feedback.md` is now the active feedback file for `spec-028-orders-0_0_8.md` (the orders card), per `docs/feedback.md:1`'s heading `# Review feedback - docs/spec-028-orders-0_0_8.md`. The four `feedback.md § High` citations in `relay.py` at `:200`, `:234-236`, `:378-379`, `:388-390`, `:449-450` therefore no longer resolve at the cited location. The reasoning the comments capture is still correct (resolved-info-positional-collision, async-`get_queryset`-not-awaited, sync-context-async-hook); only the pointer rotted. Same drift class as the `feedback.md` rot already filed at `rev-list_field.md::Low #4` and the `rev-types__finalizer.md` carry-forward (8-site `feedback.md` rot sweep flagged for the next types/ folder cycle).

Recommended fix: replace each `feedback.md § High` citation with either a heading anchor from the now-archived spec text — most plausibly fold these into the existing `spec-015` rewrite by quoting the same "Review feedback" anchors that `spec-015-relay_interfaces-0_0_5.md::Open questions` retained internally — or drop the cross-reference entirely if the surrounding docstring prose already documents the contract (the `_resolve_id_default` docstring at `:194-215`, the `_apply_get_queryset_sync` docstring at `:226-247`, and the `_resolve_node_default` docstring at `:371-391` all already document the contract independently of the citation).

### L3: TODO block at `:266-273` is structurally orphaned

The TODO block at `:266-273` references `_apply_get_queryset_sync` / `_apply_get_queryset_async` (defined upstream at `:225-263`) as the shared visibility-helper home for `FilterSet`'s related-branch scoping. But there is no blank line between the TODO body's last line (`:273`) and the next symbol declaration at `:274` (`def _coerce_node_id(...):`), which visually attaches the TODO to `_coerce_node_id` rather than to the `_apply_get_queryset_*` pair it actually targets. The ruff formatter does not enforce the two-blank-line rule on comment-then-def boundaries the way it does on def-then-def boundaries, so the formatter does not catch this.

Recommended fix: insert one blank line between `:273` (`#   parent_qs = parent_qs.filter(...)`) and `:274` (`def _coerce_node_id(...)`) so the TODO visually attaches to the helper pair above it. Same readability calibration as the `rev-optimizer__hints.md::OptimizerHint.prefetch_obj repr=False` Low — a small consumer-debug-surface miss that the formatter's defaults cannot catch.

### L4: `Decision 9` framing in `_apply_get_queryset_sync` docstring elides the typed-marker contract

`_apply_get_queryset_sync` docstring at `:226-247` names "Decision 9" of spec-015 (the async-resolver-support decision) but frames the sync misuse path as raising "a named `ConfigurationError`" — it never names `SyncMisuseError` as the specific marker, despite the function raising exactly that subclass at `:241`. The wider docstring property (a typed marker the consumer can catch by subclass identity rather than substring-of-message) is exactly what M1's GLOSSARY entry surfaces; the local docstring should mirror the same contract.

Recommended fix: replace "raise a named `ConfigurationError`" at `:233-234` with "raise a named `SyncMisuseError` (a `ConfigurationError` subclass that also inherits `RuntimeError`)" so the docstring names the typed marker the caller catches and pairs with M1's new GLOSSARY entry. The same one-word tightening applies to the `_resolve_node_default` docstring at `:387` and the `_resolve_nodes_default` docstring at `:449`. Defer if M1's GLOSSARY entry is rejected — those four docstrings stay coherent with the existing "a named `ConfigurationError`" framing if `SyncMisuseError` does not appear in the GLOSSARY.

### L5: Docstring-vs-implementation drift in `_resolve_id_default` proxy-model rationale

`_resolve_id_default`'s docstring at `:211-214` documents that keying on `root.__class__._meta.pk.attname` is "deliberate: the alternative `cls.__django_strawberry_definition__.model._meta.pk.attname` would mis-key the `__dict__` lookup for proxy-model rows whose actual class differs from the declared DjangoType model." The package's test suite at `tests/types/test_relay_interfaces.py` does NOT pin this proxy-model branch — the only `__dict__`-cache-miss test (`test_resolve_id_falls_back_to_getattr` at `:506-525`) uses a synthetic `_FakeRoot` class that mimics the `__class__._meta.pk.attname` contract, not a Django proxy-model instance. The contract claim survives without a regression pin.

Same calibration as the `rev-optimizer__walker.md` carry-forward on uncovered `id_attr == "pk"` branches: when a docstring asserts an explicit cardinality property and no test pins it, the cost of the property silently regressing is real but the fix is bounded by adding one focused test. Defer until a proxy-model fixture exists elsewhere in the package OR a regression surfaces; then add `tests/types/test_relay_interfaces.py::test_resolve_id_uses_proxy_model_class_for_attname` pinning the proxy-model branch directly.

### L6: GLOSSARY absence on `apply_interfaces` / `install_relay_node_resolvers` / `_check_composite_pk_for_relay_node` is intentional convention — confirm at folder pass

The seven module-internal helpers in `relay.py` (`apply_interfaces`, `_check_composite_pk_for_relay_node`, `install_is_type_of`, `install_relay_node_resolvers`, `implements_relay_node`, the seven `_resolve_*` / `_apply_*` / `_coerce_*` helpers, and the `_RELAY_RESOLVER_DEFAULTS` tuple) are all absent from `docs/GLOSSARY.md`. This matches the convention recorded in prior memory entries (`optimizer/__init__.py:14-17`-style "internal implementation details" calibration applied to `_resolve_node_default` siblings, `_field_meta_for_resolver`, etc.). The consumer-visible behaviors all surface through the `Relay Node integration` entry (`docs/GLOSSARY.md:928-945`).

Forward to `rev-types.md` folder pass as a positive-audit-trail confirmation rather than a per-file GLOSSARY-coverage gap. Do NOT propose new entries for these internal helpers; the absence is intentional and the entry surface that DOES need attention is the `SyncMisuseError` gap filed at M1.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_model_for` at `:305-314` is the single source of truth for `cls.__django_strawberry_definition__.model` access — consumed at `:101` (`install_is_type_of`), `:160` (`_check_composite_pk_for_relay_node`), `:317-324` (`_initial_queryset`), and `:350` (`_order_nodes`). This collapsed an earlier four-site repetition. `_initial_queryset` (`:317-324`) likewise centralizes `model._default_manager.all()` for the sync and async assembly paths. `_RELAY_RESOLVER_DEFAULTS` (`:493-498`) is the single source of truth for the four Relay resolver method names plus their framework defaults; `install_relay_node_resolvers` iterates it once and there is no parallel literal anywhere else in the package (`grep -rn "resolve_id_attr\|resolve_id\|resolve_node\|resolve_nodes" django_strawberry_framework/types/relay.py` confirms the cluster is contained). `_apply_node_filter` (`:284-302`) is color-agnostic — both sync and async paths consume it, dodging the parallel-implementation regression flagged in `feedback.md § High` "Async `get_queryset` is not awaited in Relay node defaults".
- **New helpers considered.** A unified `_dispatch_node_resolver(cls, *, info, finalize_sync, finalize_async_thunk, ...)` that folds `_resolve_node_default` and `_resolve_nodes_default` was considered and rejected — the readability cost of threading two terminal-materialization callbacks through a single dispatcher outweighs the saved seven lines, and the sync/async-context distinction at the dispatch site is exactly the load-bearing distinction that the two-method split surfaces statically. Same calibration as `filters/sets.py::apply_sync` / `apply_async`. Folding the `_coerce_node_id` / `_coerce_node_ids` pair into a single function-with-`Optional[list]` signature was also considered and rejected — the two functions are at exactly two and three callers respectively and the split signature carries the singular-vs-plural distinction more cleanly than an `Optional` would.
- **Duplication risk in the current file.** The four-line sync-vs-async dispatch shape at `_resolve_node_default` (`:392-397`) and `_resolve_nodes_default` (`:452-461`) is intentional sibling design — folding through a shared prelude would obscure the singular/plural argument-shape difference. Recorded as defer-with-trigger above; do not act now.

### Other positives

- **Two-phase lifecycle split is well-documented.** The module docstring (`:1-21`) names exactly three lifecycle phases (class-creation, annotation-synthesis, finalization Phase 2.5) and assigns each helper to its phase. The same split is mirrored in the function docstrings (`install_is_type_of` at `:77-98` names class-creation; `apply_interfaces` at `:110-126` names Phase 2.5; `_check_composite_pk_for_relay_node` at `:143-159` names Phase 2.5; the `__init_subclass__` Slice 3 tuple-membership check is correctly pointed at `types/base.py`). The three structurally distinct discriminators (`cls.__dict__` membership for `is_type_of`; `relay.Node in interfaces` tuple-membership for id-suppression; `__func__` identity for `resolve_*` injection) are explicitly named at `:516-519` — they answer different questions at different lifecycle phases and the docstring tells the reader why none of them can be collapsed into a single test.
- **Three escape hatches for composite-pk + Relay are correctly documented and tested.** `_check_composite_pk_for_relay_node` at `:142-176` raises only when the model has a composite pk AND `resolve_id_attr()` raises `NodeIDAnnotationError` — the explicit `id: relay.NodeID[...]` escape hatch survives, pinned by `test_composite_pk_with_explicit_node_id_annotation_is_accepted` at `tests/types/test_relay_interfaces.py:238-256`. The Phase-2.5 ordering note at `:163-164` tells a future reader why the upstream `relay.Node.resolve_id_attr` is the right method to call here (our default is installed after this gate runs).
- **Async-`get_queryset` contract is honored on both bulk and single paths.** `_apply_get_queryset_async` (`:251-263`) awaits the hook unconditionally when `inspect.isawaitable(result)` is true; the sync mirror at `:225-248` closes the unawaited coroutine before raising `SyncMisuseError` so Python does not emit `RuntimeWarning: coroutine was never awaited`. Both branches are pinned by `test_resolve_node_async_awaits_async_get_queryset` (`:798-816`), `test_resolve_nodes_async_awaits_async_get_queryset` (`:820-842`), `test_resolve_nodes_async_no_ids_awaits_async_get_queryset` (`:846-859`), `test_resolve_node_sync_with_async_get_queryset_raises` (`:862-884`), `test_resolve_nodes_sync_with_async_get_queryset_raises` (`:919-940`), and `test_sync_misuse_raises_sync_misuse_error_subclass` (`:887-916`).
- **Override discipline is well-tested.** Every consumer-override branch in `install_relay_node_resolvers` is pinned (`test_consumer_resolve_id_attr_wins`, `test_consumer_resolve_id_wins`, `test_consumer_resolve_node_wins`, `test_consumer_resolve_nodes_wins`, `test_consumer_async_resolve_node_wins`, `test_install_relay_node_resolvers_preserves_consumer_override`), and the idempotency contract is pinned at `test_install_relay_node_resolvers_idempotent` (`:1226-1252`) by comparing `__func__` identities snapshot-vs-second-call.
- **Direct `relay.Node` inheritance is fully wired through Phase 2.5.** The `feedback.md § High` regression "Direct `relay.Node` inheritance bypasses Relay finalization" is closed by tests at `test_direct_relay_node_inheritance_suppresses_id_annotation` (`:1260-1289`), `test_direct_relay_node_inheritance_injects_resolvers_and_suppresses_id` (`:1293-1331`), and `test_direct_relay_node_inheritance_composite_pk_raises` (`:1334-1351`). The `implements_relay_node` helper at `:63-73` is the single discriminator both `Meta.interfaces` and direct-base inheritance route through.

### Summary

`types/relay.py` is a 528-line internal-helper module that ports `strawberry_django`'s Relay foundation behavior without importing the upstream package at runtime, well-organized by lifecycle phase (class-creation, annotation-synthesis, finalization Phase 2.5) with a 1453-line test suite that pins every documented contract including the `feedback.md § High` regressions from rev3 of the spec. The only Medium finding is GLOSSARY drift on `SyncMisuseError` — the publicly-exported typed marker is absent from both the `Relay Node integration` entry and the package-level public-API listing, even though the docstring explicitly frames it as a typed marker for consumer code. Six Lows split across citation hygiene (`spec-011 → spec-015` rewrite at 7 source + 11 test sites; `feedback.md § High` post-spec-028 rot at 4 sites), a structural orphan-block readability tightening on the orders-subsystem TODO, a docstring-vs-implementation marker-naming tightening, a deferred proxy-model branch pin, and a confirmation-only forward on internal-helper GLOSSARY absence. No High findings; no behavior bugs.

---

## Fix report (Worker 2)

Consolidated single-spawn — Medium-GLOSSARY-verbatim-lift + citation-hygiene Lows + one structural-readability Low + one typed-marker-naming Low. All edits are documentation-only; the `SyncMisuseError` typed marker was already raised by `_apply_get_queryset_sync` at the source — these edits document the shipped contract.

### Files touched
- `docs/GLOSSARY.md` — M1 GLOSSARY drift fix. Inserted the verbatim "framework rejects the async `get_queryset` invoked from a sync resolver context" bullet into the `Relay Node integration` entry's "Shipped behavior" list (between the `is_type_of` and composite-pk bullets) per the artifact's recommended replacement prose. Added a new top-level `## SyncMisuseError` entry verbatim from the artifact, placed alphabetically between `Strictness mode` and `TestClient`. Index row at `:87` and public-API surface listing untouched per artifact prose.
- `django_strawberry_framework/types/relay.py` — L1 + L2 + L3 + L4. (a) L1: seven `spec-011` → `spec-015` swaps in module/function docstrings (lines `:85`, `:116`, `:117`, `:118`, `:125`, `:145`, `:208`). (b) L2: dropped all five rotted `feedback.md § High` citation parentheticals across `_resolve_id_default` (`:200`), `_apply_get_queryset_sync` (`:234-236`), `_resolve_node_default` (`:379` + `:389-390`), and `_resolve_nodes_default` (`:450`); the surrounding docstring prose already documents the contracts independently. (c) L3: inserted blank lines between the orders-subsystem TODO block tail (`:272`) and the `def _coerce_node_id` declaration so the TODO visually attaches to the `_apply_get_queryset_*` pair above it. (d) L4: named `SyncMisuseError` (a `ConfigurationError` subclass that also inherits `RuntimeError`) in three docstrings — `_apply_get_queryset_sync`, `_resolve_node_default`, `_resolve_nodes_default` — so each one mirrors M1's GLOSSARY entry.
- `tests/types/test_relay_interfaces.py` — L1 lockstep. Eleven `spec-011` → `spec-015` swaps at `:73`, `:222`, `:267`, `:301`, `:303`, `:336`, `:512`, `:763`, `:1102`, `:1103`, `:1126`.

### Tests added or updated
None. All edits are documentation-only — citation rotation, docstring naming alignment, GLOSSARY entry insertion, and a blank-line readability tightening. The `SyncMisuseError` typed marker is already pinned by `tests/types/test_relay_interfaces.py::test_sync_misuse_raises_sync_misuse_error_subclass` (`:887-916`); no new pin is needed.

### Validation run
- `uv run ruff format .` — pass (213 files unchanged, expected because the edits are inside docstrings, comments, and Markdown).
- `uv run ruff check --fix .` — pass (All checks passed!).
- Focused tests — not run (Worker 2 hard rule).

### Notes for Worker 3
- L5 (proxy-model branch test) and L6 (internal-helper GLOSSARY absence forward) deferred per artifact prose.
- GLOSSARY entry placed alphabetically between `Strictness mode` (`:1098`) and `TestClient` (`:1114`). The artifact's recommended insertion text says "alphabetically between `safe_wrap_connection_method` and the `Schema audit` block" — that placement is incorrect alphabetically (`Sync` > `Schema`) so I followed proper alphabetical placement after `Strictness mode`. The entry text itself is verbatim from the artifact.
- L2 artifact body lists 5 line-ranges for "four sites"; on inspection `_resolve_node_default`'s docstring contained two distinct `feedback.md § High` cite expressions (`:379` and `:389-390`), so the actual rotted-cite count is 5. I dropped all five since they are the same drift class and Worker 1's intent ("drop the cross-reference entirely if the surrounding docstring prose already documents the contract") clearly applies to each.
- L3 placed two blank lines (not one) between the TODO body and `def _coerce_node_id` so the formatter's two-blank-line-between-top-level-defs rule is honored. Ruff format reports no further changes.
- Concurrent maintainer activity dirty across many files (`KANBAN.md`, `types/base.py`, `types/finalizer.py`, `types/relations.py`, builder docs, `tests/types/test_base.py`, kanban-app changes, `review-0_0_7.md`) untouched per AGENTS.md #33.
- `uv.lock` unchanged.

---

## Verification (Worker 3)

Terminal-verify of bare `fix-implemented`. All seven dispatch checks pass against scoped diff (`git diff -- docs/GLOSSARY.md django_strawberry_framework/types/relay.py tests/types/test_relay_interfaces.py CHANGELOG.md`).

### Logic verification outcome

All edits are documentation-only and match the artifact's per-finding prose:

1. **GLOSSARY M1.** `docs/GLOSSARY.md:940` carries the new `SyncMisuseError` bullet inside `Relay Node integration`'s "Shipped behavior" list, positioned between the `is_type_of` bullet (`:939`) and the composite-pk bullet (`:941`) per the artifact recipe. New top-level `## SyncMisuseError` entry lands at `:1114-1124` with the verbatim three-bullet body + `See also` line; alphabetical placement between `Strictness mode` (`:1098`) and `TestClient` (`:1126`) is correct (`Sync` > `Str` > `Tes`). Worker 2's deviation from the artifact's mis-alphabetized "between `safe_wrap_connection_method` and `Schema audit`" suggestion was the right call and is logged in Notes-for-Worker-3.
2. **L1 spec-011 → spec-015 swap.** `grep -c "spec-011" django_strawberry_framework/types/relay.py` returns 0; `grep -c "spec-015"` returns 7 (matching the artifact's 7-source-site count at `:85, :116, :117, :118, :125, :145, :208`). On the test file `grep -c "spec-011" tests/types/test_relay_interfaces.py` returns 0; `grep -c "spec-015"` returns 11 (matching the artifact's 11-test-site count).
3. **L2 rotted `feedback.md § High` cites dropped.** `grep -c "feedback" django_strawberry_framework/types/relay.py` returns 0; the five rotted parentheticals at `:200`, `:234-236`, `:379`, `:389-390`, `:450` are gone and the surrounding docstring prose still names the contract independently per the artifact's option (b). Worker 2's 5-vs-4 count widening (artifact says "four sites" but `_resolve_node_default` had two distinct cites) is documented and the diff confirms all five were swept.
4. **L3 blank lines before `_coerce_node_id`.** Two blank lines exist between `:272` (`#   parent_qs = parent_qs.filter(...)`) and `:275` (`def _coerce_node_id(...)`). Two-blank-line spacing (not one) honors Python's top-level-def convention; the TODO body visually attaches to the `_apply_get_queryset_*` pair upstream.
5. **L4 `SyncMisuseError` named in three docstrings.** `grep -n "SyncMisuseError" django_strawberry_framework/types/relay.py` returns hits at the class definition (`:41`) plus the raise site (`:240`) plus three docstring sites: `:233` (`_apply_get_queryset_sync`), `:388` (`_resolve_node_default`), `:450` (`_resolve_nodes_default`). Each names the typed marker as "a `ConfigurationError` subclass that also inherits `RuntimeError`", matching the artifact's recommended phrasing and mirroring M1's GLOSSARY prose.
6. **Changelog `Not warranted`.** `git diff -- CHANGELOG.md` is empty. The artifact's Changelog disposition cites both AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and active-plan silence, plus a calibration-sibling enumeration covering `optimizer/extension.py`, `list_field.py`, `optimizer/hints.py`, `types/finalizer.py`, and `types/converters.py`.
7. **Ruff plausible.** `uv run ruff check django_strawberry_framework/types/relay.py tests/types/test_relay_interfaces.py docs/GLOSSARY.md` → All checks passed.

### DRY findings disposition

Three DRY deferrals all carry explicit "third callsite" triggers — defer-`_dispatch_node_resolver` until a third sync-vs-async-context Relay resolver lands (most plausibly `resolve_connection`), defer-`_sync_node_prelude`/`_async_node_prelude` until the resolver coroutine pattern picks up a third caller, and restate the existing `TODO(spec-027-filters-0_0_8 Slice 1)` trigger inside this file. No in-cycle DRY edit; deferrals are pre-authorized by the artifact's own prose and Worker 2 took no action.

### Temp test verification

Not applicable. All edits are documentation-only (citation hygiene, GLOSSARY entry insertion, blank-line readability, typed-marker naming in docstrings). The `SyncMisuseError` typed marker is already pinned by `tests/types/test_relay_interfaces.py::test_sync_misuse_raises_sync_misuse_error_subclass` (`:887-916`); no new pin is needed.

### Verification outcome

Verified. Concurrent maintainer activity on `types/base.py`, `types/finalizer.py`, `types/relations.py`, `tests/types/test_base.py`, and several builder/kanban/example files is out-of-scope per AGENTS.md #33 and untouched by this cycle's diff.

---

## Comment/docstring pass

Consolidated single-spawn — comment/docstring edits were applied in the same pass as the M1 GLOSSARY lift because the artifact carried pre-derived verbatim replacement prose for the Medium and the Lows are all citation/comment/docstring-only. Same shape #4 calibration applied to `optimizer/extension.py`, `list_field.py`, `optimizer/hints.py`, `types/finalizer.py`, and other recent 0.0.7 cycles.

### Files touched
Same set as the Fix report above; no additional comment-pass-only edits.

### Per-finding dispositions
- Medium 1 (GLOSSARY drift on `Relay Node integration` + new `SyncMisuseError` entry): applied verbatim from the artifact's recommended prose; alphabetical placement adjusted from the artifact's "between `safe_wrap_connection_method` and `Schema audit`" suggestion to the correct slot between `Strictness mode` and `TestClient` (the entry text itself is unchanged).
- Low 1 (`spec-011` → `spec-015` swap): applied to all 7 source sites + 11 test sites in lockstep.
- Low 2 (`feedback.md § High` rotted cites): all 5 rotted parentheticals dropped (artifact's recommended "drop the cross-reference entirely if the surrounding docstring prose already documents the contract" path); the surrounding docstring prose at each site still documents the contract.
- Low 3 (TODO block at `:266-273` structurally orphaned): two blank lines inserted between the TODO tail and `def _coerce_node_id`.
- Low 4 (name `SyncMisuseError` in three docstrings): applied to `_apply_get_queryset_sync`, `_resolve_node_default`, `_resolve_nodes_default`.
- Low 5 (proxy-model branch pin): deferred per artifact's own prose ("Defer until a proxy-model fixture exists elsewhere in the package OR a regression surfaces").
- Low 6 (internal-helper GLOSSARY absence confirmation): forwarded to `rev-types.md` folder pass per artifact instruction; no per-file action taken.

### Validation run
- `uv run ruff format .` — pass (213 files unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3
Same as the Fix-report Notes above; no additional comment-pass-specific notes.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
- AGENTS.md #21 — "Do not update CHANGELOG.md unless explicitly instructed." Dispatch prompt explicitly directs `Not warranted` and the active review plan does not authorise a `CHANGELOG.md` edit for this cycle.
- All in-cycle edits are documentation hygiene: M1 GLOSSARY drift fix (the publicly-exported `SyncMisuseError` was already raised by `_apply_get_queryset_sync` since 0.0.5 and is already caught by `filters/sets.py::FilterSet.apply` — the cycle documents the existing consumer contract, it does not change behavior), L1 7-source+11-test citation rotation (no logic change), L2 rotted-feedback.md citation drop (no logic change), L3 blank-line readability tightening (no logic change), L4 typed-marker-naming-in-docstring (no logic change, no exception-message-substring change at the runtime raise site).
- Calibration siblings for `Not warranted`: prior 0.0.7 cycles with GLOSSARY-Medium-lift + citation/comment Lows — `optimizer/extension.py` (3-entry GLOSSARY lift + spec-014→spec-018), `list_field.py` (`DjangoListField` async-detection clause + 4-site spec/path rotation), `optimizer/hints.py` (`OptimizerHint` Validation paragraph + four in-place Lows), `types/finalizer.py` (9-Lows citation hygiene), `types/converters.py` (5 docstring-only Lows). All calibrated to `Not warranted` on the same AGENTS.md #21 + active-plan-silence pair.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass (213 files unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

---

## Iteration log
