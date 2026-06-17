# Review: `django_strawberry_framework/utils/querysets.py`

Status: verified

## DRY analysis

- None — this module IS the 0.0.9 DRY consolidation point (`docs/feedback.md` Major 1) for the query-source + visibility contract; re-consolidating a consolidation point is net-negative. Its seven symbols already collapse what list field / connection field / optimizer middleware / Relay node defaults / cascade-permissions / filter related-visibility derive previously spelled separately. The `_RELAY_ASYNC_RECOURSE` module constant (`querysets.py::_RELAY_ASYNC_RECOURSE`) is the single default for the new `async_recourse` parameter; the two non-default recourse strings live with their callers (`permissions.py::apply_cascade_permissions #"apply_cascade_permissions walks target hooks"`) by design — they are surface-specific human guidance, not a dispatch key, and coupling them would force unrelated wordings to co-evolve. `post_process_queryset_result_*` correctly compose `normalize_query_source` + `apply_type_visibility_*` rather than re-implementing the branch.

## High:

None.

## Medium:

None.

## Low:

### `async_recourse` is appended only on the coroutine-reject branch — untested through the cascade caller's custom wording

`apply_cascade_permissions` (`permissions.py:267-277`) passes a bespoke `async_recourse` string, but the only direct unit test of the sync reject path (`tests/utils/test_querysets.py::test_apply_type_visibility_sync_rejects_async_hook_loudly`) matches on the fixed prefix `"returned a coroutine in a sync"` and exercises only the default recourse. The custom-recourse substitution is covered indirectly (the cascade async-edge behavior is pinned in `tests/test_permissions.py`), so this is not a coverage gap that the 100% gate would expose. Forward-looking only. Defer until a third distinct `async_recourse` caller lands; at that point pin each surface's recourse-string substitution with a focused `match=` assertion so a copy-paste error in one caller's guidance cannot pass silently.

### `Any` typing on `info` / `result` deliberately untyped

`info: Any` and `result: Any` across `apply_type_visibility_*` / `post_process_queryset_result_*` mirror the sibling-util convention (`connections.py`, `permissions.py`): plan-time `info` is not always a `strawberry.Info`, and the consumer-resolver return is genuinely heterogeneous (QuerySet / Manager / list / generator). Correct as-is. Defer until a typed resolver-context boundary lands package-wide; tighten all four signatures together then so the contract stays uniform.

## What looks solid

### DRY recap

- **Existing patterns reused.** Composes its own primitives rather than duplicating them: `post_process_queryset_result_sync` (`querysets.py:162-165`) and `_async` (`querysets.py:174-177`) call `normalize_query_source` (`querysets.py:88-90`) then the matching `apply_type_visibility_*`; the connection (`connection.py:830`, `:867`, `:892`), optimizer extension (`extension.py:787`), optimizer walker (`walker.py:243`), Relay node defaults (`types/relay.py:818,839,879,904`), cascade-permissions (`permissions.py:267`), and filter related-derive (`filters/sets.py:995,1014`) all route through this one module. `SyncMisuseError` is single-sited here and re-exported (not redefined) from `types/relay.py:41` and `permissions.py:58`.
- **New helpers considered.** A maybe-await wrapper that hides the sync/async coloring behind one entry point was correctly rejected (module docstring `querysets.py:84-86`): each caller keeps its colored step explicit so an `await` is never silently dropped. No new helper at this granularity.
- **Duplication risk in the current file.** The two `result = type_cls.get_queryset(queryset, info)` lines (`querysets.py:124`, `:147`) are NOT a fold candidate — the sync branch must `iscoroutine`→close→raise and the async branch must `isawaitable`→await; the shared first line is the contract surface, the divergent tails are the whole point. Module-overview reports zero repeated string literals.

### Other positives

- **Sync/async parity is correct, not merely symmetric.** Sync (`apply_type_visibility_sync`) detects with `inspect.iscoroutine` and rejects (closing the coroutine first to suppress `RuntimeWarning: coroutine was never awaited`, enforced by the repo's `filterwarnings = error` config — pinned by `tests/utils/test_querysets.py::test_apply_type_visibility_sync_rejects_async_hook_loudly`); async (`apply_type_visibility_async`) detects with `inspect.isawaitable` and awaits, passing a sync return through. The broader predicate on the async side is correct: a sync hook returns a non-awaitable QuerySet that must pass through untouched, while an async hook returns a coroutine that must be awaited. No behavioral gap between the two paths beyond the intended sync-reject-vs-async-await difference.
- **No wrong/leaked data.** `apply_type_visibility_*` never mutates the input queryset in place — `get_queryset` returns a (typically narrowed) queryset and the result is what propagates; an unevaluated base queryset is the contract, so no `_result_cache` / evaluated-queryset reuse hazard exists in this module. There is no aliasing or db-pinning logic here by design: db pinning is each caller's concern (the cascade caller pins explicitly via `field.related_model._default_manager.using(queryset.db).all()` at `permissions.py:266`), keeping this module neutral. `normalize_query_source` returns the source object identity-unchanged for the QuerySet and non-queryset paths (pinned by `test_normalize_query_source_passes_queryset_through` / `_passes_non_queryset_through`), so no caller's source is silently swapped.
- **`SyncMisuseError` exception design.** Multiple-inherits `ConfigurationError` AND `RuntimeError` so `FilterSet.apply`'s `RuntimeError` rethrow path and the package's `ConfigurationError` convention both catch it; documented in the class docstring and the GLOSSARY (`docs/GLOSSARY.md:1299-1305`). Subclass relationship asserted in `tests/utils/test_querysets.py:110-111`.
- **`async_recourse` default is an immutable module constant.** `_RELAY_ASYNC_RECOURSE` is a `str`, so the mutable-default-argument anti-pattern does not apply; the default keeps the Relay node-defaults wording while letting the cascade caller (`permissions.py`) supply its accurate "no async-native walk; make the hook sync or scope `fields=`" guidance.
- **Cycle-safe by construction.** Imports only `inspect`, `typing.Any`, `django.db.models`, and `..exceptions` — no first-party package imports, so `types/relay.py` (loaded at module top via `types/base.py`) imports from here without closing a load cycle. Confirmed against the shadow Imports section (5 imports, one local).
- **Test discipline.** `tests/utils/test_querysets.py` pins all seven symbols directly — Manager coercion, QuerySet passthrough, non-queryset passthrough, sync-runs / sync-rejects-async / async-awaits / async-passes-sync, and both `post_process` branches — with deep through-schema coverage deferred to the surface suites it names.

### Summary

`utils/querysets.py` is the single-sited query-source + `DjangoType.get_queryset` visibility contract and reads as a clean consolidation point: tight, dependency-minimal, cycle-safe, with exemplary direct unit coverage. The only change since baseline `14910230` is the `async_recourse` parameterization (commit `ff7c56c2`) — an immutable-string default with caller-specific override, which is correct and net-positive (the cascade caller now gets accurate recourse guidance instead of misleading Relay-node wording). This-cycle `git diff HEAD` is empty. Sync/async parity is sound, no in-place mutation or db/alias hazard exists in this neutral module, and the visibility routing that a data-leak bug would have to corrupt is correct on both colors. No High or Medium findings; two forward-looking Lows. No-source-edit cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format --check django_strawberry_framework/utils/querysets.py` — `1 file already formatted` (the COM812 warning is the standing repo-wide config notice, not a finding).
- `uv run ruff check django_strawberry_framework/utils/querysets.py` — `All checks passed!`

### Notes for Worker 3
- Shape #5 no-source-edit cycle: `git diff HEAD -- django_strawberry_framework/utils/querysets.py` is empty; the only since-baseline change (commit `ff7c56c2`, `async_recourse` parameterization) is already in HEAD and reviewed correct.
- No GLOSSARY-only fix in scope. GLOSSARY references `SyncMisuseError` (`docs/GLOSSARY.md:35,134,154,192,1090,1299-1305`) and `apply_type_visibility_sync` (`:192,1090,1305`) — all prose is accurate against current source (sync closes-and-raises; async twin wraps the sync walk via `sync_to_async`; routing single-sited in `utils/querysets.py`). No drift.
- Two forward-looking Lows, both trigger-gated; neither requires a source edit now.
  - Low 1 (`async_recourse` custom-wording untested directly): defer until a third distinct `async_recourse` caller lands.
  - Low 2 (`Any` typing on `info`/`result`): defer until a typed resolver-context boundary lands package-wide.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

Docstrings reviewed against current source and found accurate: the module docstring correctly states the consolidation rationale and cycle-safety; `apply_type_visibility_sync`'s docstring correctly documents the new `async_recourse` parameter and its default-vs-cascade wording (added in `ff7c56c2`); `apply_type_visibility_async` correctly documents the await contract and the earlier-implementation bug it fixed. No stale comments, no obsolete TODOs (shadow reports zero TODO anchors), no docstring promising behavior the code does not provide. No edits.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no-source-edit cycle (zero edits to any tracked file). Per AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_10.md`) carrying no changelog directive for this item.

---

## Verification (Worker 3)

Terminal-verify, shape #5 (no-source-edit), data-isolation-critical visibility util.

### Logic verification outcome

Re-derived every dispatch invariant against LIVE source, not the artifact prose.

- **`apply_type_visibility_sync` applies the hook with no skip/weaken path** (`querysets.py::apply_type_visibility_sync`): one unconditional `result = type_cls.get_queryset(queryset, info)`, then `iscoroutine`→`close()`→`raise SyncMisuseError`, else `return result`. There is no early-return or fall-through that would propagate the *un-narrowed* input — a sync hook's narrowed queryset is the sole non-raise return. The cascade composition surface (`permissions.py::apply_cascade_permissions`, :267) takes `target_qs` from this call and folds it into `Q(**{f"{field.name}__in": target_qs}) | Q(__isnull=True)` (:278-280), so the narrowed set is what gates the parent rows.
- **sync/async parity — same visibility result, intended divergence only.** Sync detects with `inspect.iscoroutine` and rejects; async (`apply_type_visibility_async`) detects with `inspect.isawaitable` and `await`s, passing a sync (non-awaitable) return through untouched. The async predicate is correctly the broader one: a sync hook returns a non-awaitable QuerySet (passes through), an async hook returns a coroutine (awaited). No path where one color enforces and the other bypasses. The cascade async twin (`aapply_cascade_permissions`) wraps the SAME sync walk via `sync_to_async` (Decision 10) — so the async cascade *also* raises `SyncMisuseError` on an async target hook (pinned by `test_aapply_async_target_hook_still_raises`), confirming no async-side enforcement gap.
- **close-before-raise is correct and load-bearing.** The unawaited coroutine is `.close()`d before `raise` to suppress `RuntimeWarning: coroutine was never awaited`, which `pytest.ini filterwarnings = error` would turn into a hard failure. Independently confirmed by a temp test that promoted `RuntimeWarning` to error *locally* (independent of pytest.ini) and still saw a clean `SyncMisuseError` (see Temp test verification).
- **`SyncMisuseError` raised in the right cases:** only on the sync color when the hook returns a coroutine; never on the async color (it awaits instead). Dual-base (`ConfigurationError` + `RuntimeError`) confirmed at `querysets.py:35` and re-derived in the temp suite.
- **No in-place mutation / no `_result_cache` reuse / `normalize_query_source` identity-preserving.** `apply_type_visibility_*` return the hook's output and never mutate the input base — temp test proves the returned narrowed queryset `is not base` and `base.query` carries no `WHERE` after the call. The contract is an unevaluated base queryset, so no evaluated-`_result_cache` reuse hazard exists here. `normalize_query_source` returns the QuerySet / non-queryset source object identity-unchanged (`.all()` only on a `Manager`), pinned by `test_normalize_query_source_passes_queryset_through` / `_passes_non_queryset_through`. No db/alias logic here by design — the cascade caller pins via `field.related_model._default_manager.using(queryset.db).all()` (`permissions.py:266`, content-confirmed at line 266 of current HEAD).
- **Cycle-safe import set confirmed:** only `inspect`, `typing.Any`, `django.db.models`, `..exceptions` — zero first-party package import, so `types/relay.py` re-export closes no load cycle.

### Both Lows genuinely forward-looking

- **Low 1** (`async_recourse` custom wording untested via focused `match=`): grep confirms EXACTLY one override caller (`permissions.py:271`); every other site uses the default. The custom-recourse substitution IS covered indirectly by `tests/test_permissions.py::test_sync_helper_raises_syncmisuseerror_on_async_target_hook` (asserts `"fields="`, `"get_queryset sync"`, and `"Relay node defaults" not in message`), so it is not a 100%-gate coverage gap. Trigger ("third distinct `async_recourse` caller lands") unmet — gated on a future caller, no source-site TODO owed.
- **Low 2** (`Any` on `info`/`result`): 4 sites confirmed; mirrors sibling-util convention (`connections.py`, `permissions.py`); plan-time `info` is not always a `strawberry.Info` and the consumer-resolver return is genuinely heterogeneous. Gated on a typed resolver-context boundary landing package-wide. Forward-looking.

### DRY findings disposition

DRY=None accepted — this module IS the 0.0.9 consolidation point. Grep confirms each of the seven symbols is single-sited here and every surface routes through it: `apply_type_visibility_sync` consumed by connection (:867), list_field (:171), filters/sets (:995), permissions (:267), relay (:818/:879), walker (:243), and `post_process_*_sync` (:164); the async twins likewise; `SyncMisuseError` defined once (:35) and re-exported (not redefined) from `types/relay.py:41` and `permissions.py:58`. `_RELAY_ASYNC_RECOURSE` is the single immutable-string default; the cascade's bespoke wording lives with its caller by design. The two `type_cls.get_queryset(...)` lines are not a fold candidate — the divergent `iscoroutine`-reject vs `isawaitable`-await tails are the contract.

### Temp test verification

- Temp file used: `docs/review/temp-tests/utils/test_querysets_w3.py` (gitignored). 5 tests, all passed:
  - close-before-raise with `RuntimeWarning` promoted to error locally (no coroutine leak);
  - custom `async_recourse` substituted verbatim into the message, default Relay wording absent;
  - no in-place mutation (returned narrowed qs `is not base`; `base.query` has no `WHERE`);
  - async awaits an async hook and passes a sync hook through;
  - `SyncMisuseError` dual-base.
- Also ran the cited permanent tests: `tests/utils/test_querysets.py` (12 passed), `test_permissions.py::{test_sync_helper_raises_syncmisuseerror_on_async_target_hook, test_aapply_async_target_hook_still_raises, test_aapply_runs_walk_off_event_loop}` (3 passed). 20 passed total.
- Disposition: deleted (no new behavior bug or edge case found; permanent suite already pins all seven symbols + the cascade async edge).

### Shape #5 + changelog checks

- `git diff HEAD -- django_strawberry_framework/utils/querysets.py` empty. The `querysets.py | 24` line in the cycle-wide stat vs `14910230` is the `ff7c56c2` `async_recourse` parameterization already in HEAD (last-touch `ff7c56c2`, in HEAD `58ca2def`) — NOT a this-cycle edit; the empty `git diff HEAD` is the zero-edit proof.
- Each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.` ✓
- Both Lows carry verbatim forward-looking trigger phrasing; no GLOSSARY-only fix in scope. ✓
- Changelog `Not warranted` cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND active-plan (`review-0_0_10.md`) silence; `git diff HEAD -- CHANGELOG.md` empty. Internal-only framing honest — zero edits this cycle, no public-API surface changed. ✓
- `uv run ruff format --check` → `1 file already formatted` (COM812 notice is the standing repo-wide config warning, not a finding); `uv run ruff check` → `All checks passed!`. ✓

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box at `review-0_0_10.md:125`.

---

## Iteration log

(none)
