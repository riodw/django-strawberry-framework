# Review: `django_strawberry_framework/list_field.py`

Status: verified

## DRY analysis

- **Sync/async post-processor pair `_post_process_consumer_sync` / `_post_process_consumer_async` (`django_strawberry_framework/list_field.py:31-44`).** Both functions are structurally identical — `Manager → .all()` coercion, then `isinstance(QuerySet)` dispatch into the matching `_apply_get_queryset_{sync,async}` helper, else pass-through. The only differences are the `await` keyword and the helper-color suffix. Python's sync-vs-async function coloring makes a single shared body non-trivial (you cannot meaningfully parameterize over `await`), so the duplication is intentional sibling design. **Defer until a third consumer-return color (e.g. an iterator-coercion path) lands or a generalized `_coerce_and_apply(target_type, result, info, apply_fn, is_async)` shape becomes warranted by a second consumer of these helpers outside `list_field.py`.** Trigger to grep: a second module importing `_post_process_consumer_sync` / `_post_process_consumer_async`, OR a third coercion case (beyond `Manager` and `QuerySet`) landing inside either body.
- **Four-guard validation block in `DjangoListField` (`django_strawberry_framework/list_field.py:98-121`).** Four `ConfigurationError`-raising guards with a shared `"DjangoListField "` message prefix; three of four interpolate `target_type.__name__`. A `_validate_target(target_type)` helper would localize the guard sequence, but each guard's message text is meaningfully distinct (the third guard's three-sentence remediation message is the most useful diagnostic in the file) and the comment block at `django_strawberry_framework/list_field.py:91-97` calls out that the guard ORDER is load-bearing (each guard assumes the previous passed). Splitting into a helper would hide the ordering contract behind an opaque call. **Defer until a second `DjangoType`-target factory lands (e.g. when `DjangoConnectionField` or `DjangoNodeField` adopts the same four-guard preamble); then extract `_validate_djangotype_target(target_type, *, factory_name)` and reuse across the factories.** Trigger to grep: a second call site for `isinstance(target_type, type)` + `issubclass(target_type, DjangoType)` + `definition.origin is target_type` in the same sequence anywhere under `django_strawberry_framework/`.

## High:

None.

## Medium:

None.

## Low:

### Stale spec citation on Decision 5 guard comment

The Decision-5 validation block at `django_strawberry_framework/list_field.py:91-92` cites `spec-016`:

```django_strawberry_framework/list_field.py:91-93
    # Decision 5 validation guards
    # (spec-016 #"DjangoListField requires a DjangoType class"): four
    # constructor-site checks that fail at the line that wrote ``DjangoListField(...)`` rather
```

A `grep -l` across `docs/SPECS/*.md` and `docs/*.md` for the string `"DjangoListField requires a DjangoType class"` returns only `docs/SPECS/spec-020-list_field-0_0_7.md` — `spec-016` (`docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`) does not carry the cited substring. The citation should be `spec-020 #"DjangoListField requires a DjangoType class"`. Comment-pass fix.

### Stale spec docstring path

The module docstring at `django_strawberry_framework/list_field.py:3` cites `docs/spec-020-list_field-0_0_7.md` and the `DjangoListField` docstring at `django_strawberry_framework/list_field.py:88` cites the same path:

```django_strawberry_framework/list_field.py:1-5
"""``DjangoListField`` — non-Relay ``list[T]`` field for root Query fields.

Spec: ``docs/spec-020-list_field-0_0_7.md``.
Target release: ``0.0.7``.
"""
```

`ls docs/spec*.md` shows only `docs/spec-028-orders-0_0_8.md` lives at the active-spec slot; the list_field spec was archived to `docs/SPECS/spec-020-list_field-0_0_7.md` per the AGENTS.md docstring-archival convention ("completed design docs stay at their working location at docs/spec-NNN-…md until a NEW spec is being authored, at which point the docs/SPECS/NEXT.md Step 8 batched archive pass run by the new spec's author moves every prior spec from docs/ to docs/SPECS/"). The active path is now `docs/SPECS/spec-020-list_field-0_0_7.md`. Update both citations (module docstring and `DjangoListField` docstring) in the same comment-pass edit. Comment-pass fix.

### Stale `docs/feedback.md` citation

`_is_async_callable`'s docstring at `django_strawberry_framework/list_field.py:65` cites `docs/feedback.md High #2`:

```django_strawberry_framework/list_field.py:62-65
      Without this branch an async-callable-object resolver would land in the
      sync wrapper, its coroutine return would bypass
      ``_post_process_consumer_sync``, and the awaited QuerySet would silently
      skip ``target_type.get_queryset(...)`` (``docs/feedback.md`` High #2).
```

`docs/feedback.md` currently carries spec-028-orders feedback (verified via `head -3 docs/feedback.md`); the historical High #2 content the docstring points readers at no longer lives at that path. The reasoning the docstring captures is still correct — only the citation is dangling. Options at comment-pass time: (a) drop the parenthetical, leaving the standalone reasoning; (b) re-cite to an archived feedback artifact under `docs/SPECS/` if one exists; or (c) re-anchor to the test at `tests/test_list_field.py::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied`, which encodes the same High #2 contract in a way the cycle's grep can verify. Comment-pass fix.

### GLOSSARY narrows `DjangoListField` async-detection mechanism

`docs/GLOSSARY.md` `## ``DjangoListField`` entry at `docs/GLOSSARY.md:315` says:

> Async consumer resolvers are detected at construction time via `inspect.iscoroutinefunction` and routed through an `async def` wrapper that awaits the coroutine before applying the isinstance check.

The actual check at `django_strawberry_framework/list_field.py:72-75` is `_is_async_callable`, which calls `inspect.iscoroutinefunction(fn)` **OR** `inspect.iscoroutinefunction(fn.__call__)`. The second branch is the High #2 fix that catches callable-instance resolvers whose `__call__` is `async def`. The current GLOSSARY phrasing implies only the first branch exists; a consumer reading it would not know they can pass a class instance whose `__call__` is `async def`. Suggested verbatim replacement for the relevant clause:

> Async consumer resolvers are detected at construction time via `inspect.iscoroutinefunction` (checked on the resolver itself AND on its `__call__` so callable-instance resolvers with `async def __call__` are also covered) and routed through an `async def` wrapper that awaits the coroutine before applying the isinstance check.

This is a documented-public-contract widening, not a behavior change. Treat as Low rather than Medium because the surface still exists and is correct on the first branch — the GLOSSARY just understates coverage. Comment-pass fix (GLOSSARY-only — route through shape #4 per worker-1.md, not shape #5).

## What looks solid

### DRY recap

- **Existing patterns reused.** The module already delegates the four-step queryset assembly to `django_strawberry_framework/types/relay.py::_initial_queryset` (model lookup + `_default_manager.all()`) and `_apply_get_queryset_{sync,async}` (sync/async hook invocation including coroutine-rejection in the sync branch) at `django_strawberry_framework/list_field.py:133, 139-140` and `django_strawberry_framework/list_field.py:35, 43`, so the Decision-3 four-step shape lives in exactly one place across the package. The `noqa: N802` comment at `django_strawberry_framework/list_field.py:78` documents the load-bearing PascalCase choice (graphene-django parity).
- **New helpers considered.** A `_validate_target(target_type)` extraction was considered for the four guards and rejected today because the guard message text is meaningfully distinct per guard and the comment-block at `django_strawberry_framework/list_field.py:91-97` calls out that the guard ORDER is load-bearing — a helper-based abstraction would hide that ordering contract. Trigger-deferred under DRY analysis.
- **Duplication risk in the current file.** `_post_process_consumer_sync` / `_post_process_consumer_async` (`django_strawberry_framework/list_field.py:31-44`) are intentional sync/async sibling design — Python's function-coloring rules make collapsing them require a non-trivial higher-order shape. Trigger-deferred under DRY analysis. The two inner `_wrap` functions at `django_strawberry_framework/list_field.py:147-156` (async) and `django_strawberry_framework/list_field.py:159-164` (sync) are the same sibling pattern; the same trigger condition would consolidate them too.

### Other positives

- **Async-detection asymmetry is documented at the decision point.** The comment block at `django_strawberry_framework/list_field.py:122-129` explains exactly why `_default` uses runtime `in_async_context()` per-call while the consumer-resolver branch commits per-construction via `inspect.iscoroutinefunction(user_resolver)` — Strawberry inspects the resolver signature once at schema construction. This is the kind of "documented intentional asymmetry, NOT a harmonization candidate" annotation that survives a DRY cycle review.
- **`_is_async_callable` docstring carries its empirical justification.** `django_strawberry_framework/list_field.py:48-71` explains the two branches and explicitly addresses what would seem like dead code (the manual `partial.func` unwrap is dead on Python 3.10+ because `inspect.iscoroutinefunction` unwraps `functools.partial.func` natively since 3.8). The docstring names the contract pin test `tests/test_list_field.py::test_djangolistfield_partial_wrapped_async_resolver_gets_get_queryset_applied` as the empirical verification — this is exactly the audit shape AGENTS.md calls for.
- **Guard order is load-bearing and documented.** The validation block at `django_strawberry_framework/list_field.py:91-119` orders the four checks (`isclass` → `issubclass(DjangoType)` → `definition.origin is target_type` → `callable(resolver)`) so each downstream check can assume the previous passed; the comment block at `django_strawberry_framework/list_field.py:106-112` explains the own-class invariant (`__django_strawberry_definition__` is inherited via MRO so `hasattr` would silently accept a subclass that omits its own `Meta`) — the strict invariant catches the subclass-without-own-Meta case (rev6 High #1).
- **Default-resolver path avoids the consumer post-processor for a reason.** The module-scope comment at `django_strawberry_framework/list_field.py:25-28` explains that the default-resolver path bypasses `_post_process_consumer_{sync,async}` because `qs` is already a `QuerySet` from `Manager.all()` — no Manager-to-QuerySet coercion or isinstance branching is needed. Removing the dead-looking helpers would over-collapse the consumer-resolver branch.
- **`rev6 H1` no-redundant-coroutine optimization is documented inline.** `django_strawberry_framework/list_field.py:135-138` notes that `_default` returns the coroutine from `_apply_get_queryset_async` directly rather than wrapping it in an inner `async def` (Strawberry's `AwaitableOrValue` dispatch awaits it). The "an inner `async def` wrapper would add a redundant coroutine layer with no semantic gain" line is exactly the kind of explanation a future reviewer needs to NOT add a defensive wrapper.
- **Test coverage is end-to-end.** `tests/test_list_field.py` ships 22 tests covering validation guards (5), default-resolver sync/async branches (3), sync consumer-resolver paths (2), async consumer-resolver paths (4), root-position optimizer cooperation, FK-id elision, outer-nullability annotation pair, and `Meta.primary` interaction (2). The live-HTTP arm for `Manager → QuerySet` coercion lives in `examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http` per the live-HTTP-first rule at `examples/fakeshop/test_query/README.md`. The `_isolate_global_registry` autouse fixture mirrors the registry-isolation pattern in `tests/test_registry.py`.
- **Static helper sanity check.** `docs/shadow/django_strawberry_framework__list_field.overview.md` reports 1 control-flow hotspot (the `DjangoListField` body at 96 lines / 8 branch nodes); 0 repeated string literals; 0 TODO comments; 12 calls of interest (4 `isinstance`, 3 `getattr`, 2+2 helper applications, 1 `issubclass`). Each reflective-access call (`getattr` on `__call__`, `getattr` on `__django_strawberry_definition__`, `getattr` on `origin`) has its rationale captured in the surrounding comment block.

### Summary

`list_field.py` is a tight 173-line factory module with one control-flow hotspot (`DjangoListField` at 96 lines / 8 branches) that earns its size through a load-bearing four-guard validation preamble and a documented sync/async-asymmetry dispatch. Every Django/ORM marker, every reflective `getattr`, and every "this looks like dead code" branch has a comment block explaining why it stays. No High or Medium findings. Four Lows are all comment-pass items: a stale `spec-016` citation that should be `spec-020`, a stale `docs/spec-020-...md` path that should be `docs/SPECS/spec-020-...md` (two sites), a dangling `docs/feedback.md High #2` citation now that feedback.md has been repurposed for spec-028-orders, and a GLOSSARY entry that narrows the async-detection contract by omitting the `__call__`-branch coverage. The DRY analysis defers two real consolidation candidates — the sync/async post-processor pair and the four-guard validation block — with explicit grep-able trigger conditions for the next DRY cycle.

---

## Fix report (Worker 2)

Consolidated single-spawn pass per worker-2.md guidance — all four Lows are comment/docstring/GLOSSARY edits, no logic change.

### Files touched

- `django_strawberry_framework/list_field.py:3` — module docstring spec path `docs/spec-020-...` → `docs/SPECS/spec-020-...` (Low 2 site #1).
- `django_strawberry_framework/list_field.py:62-65` — `_is_async_callable` docstring; replaced the dangling `docs/feedback.md High #2` parenthetical with a citation to the contract-pin test `tests/test_list_field.py::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied` (Low 3, artifact-suggested option (c)).
- `django_strawberry_framework/list_field.py:86-89` — `DjangoListField` docstring spec path `docs/spec-020-...` → `docs/SPECS/spec-020-...` (Low 2 site #2).
- `django_strawberry_framework/list_field.py:92` — Decision-5 guard comment citation `spec-016` → `spec-020` (Low 1).
- `docs/GLOSSARY.md:315` — `DjangoListField` entry; widened the async-detection clause to mention the `__call__` branch (Low 4; verbatim artifact-suggested replacement).

### Tests added or updated

None. All four edits are documentation/comment text with no logic change; existing tests already pin the underlying behavior (e.g. `tests/test_list_field.py::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied` for the `__call__`-branch coverage now described in the GLOSSARY).

### Validation run

- `uv run ruff format .` — pass / no-changes (183 files left unchanged).
- `uv run ruff check --fix .` — pass / all checks passed.
- `git status --short uv.lock` — clean.

### Notes for Worker 3

- Verified spec path on disk: `docs/SPECS/spec-020-list_field-0_0_7.md` exists; `docs/spec-020-...md` does not. Only `docs/spec-028-orders-0_0_8.md` lives at the active-spec slot (consistent with the artifact's `ls docs/spec*.md` finding).
- Spot-checked tests for assertions against changed comment/docstring strings — none. The matches `grep`-found in `tests/test_list_field.py` are themselves docstring text, not assertions on `list_field.py`'s strings.
- Out-of-artifact-scope sibling drift noted but not edited: `tests/test_list_field.py:3` carries the old `docs/spec-020-list_field-0_0_7.md` path and `tests/test_list_field.py:578` carries the `docs/feedback.md High #2` citation. The artifact's Low #2 and Low #3 scope both name only `list_field.py` sites; touching the test file would expand cycle scope. Worth a separate sweep next cycle if the cohort wants to chase test-file citation drift, but rejecting it from this cycle is the right call under "no unrelated cleanup".
- No shadow file was used during fix implementation (no logic changes; the static-helper overview Worker 1 cited is sufficient context for the four comment-pass edits).

---

## Verification (Worker 3)

### Logic verification outcome

Consolidated single-spawn pass (comment/docstring/GLOSSARY only — no logic change). All four Lows verified addressed in source:

- **Low 1 (stale `spec-016` → `spec-020`).** `list_field.py:93` now reads `(spec-020 #"DjangoListField requires a DjangoType class")`. `grep` confirms the cited substring lives only in `docs/SPECS/spec-020-list_field-0_0_7.md`.
- **Low 2 (stale `docs/spec-020-…` → `docs/SPECS/spec-020-…`, two sites).** `list_field.py:3` (module docstring) and `list_field.py:89` (factory docstring) both updated. Spec path confirmed on disk: `docs/SPECS/spec-020-list_field-0_0_7.md` exists (150133 bytes); `docs/spec-020-…md` does not — only `docs/spec-028-orders-0_0_8.md` lives at the active-spec slot.
- **Low 3 (dangling `docs/feedback.md High #2`).** `list_field.py:62-66` re-anchors to `tests/test_list_field.py::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied` (artifact-suggested option (c)). Test name grep-confirmed at `tests/test_list_field.py:565`.
- **Low 4 (GLOSSARY async-detection clause widening).** `docs/GLOSSARY.md:315` carries the artifact's verbatim suggested replacement. Cross-verified against source: `list_field.py:73-76` is `inspect.iscoroutinefunction(fn)` OR `inspect.iscoroutinefunction(call)` where `call = getattr(fn, "__call__", None)` — the widened GLOSSARY text matches the actual two-branch implementation.

Diff scope matches the artifact precisely: `django_strawberry_framework/list_field.py` (4 edits at lines 3, 62-66, 89, 93) and `docs/GLOSSARY.md` (1 entry widened at line 315). No test file edits, no other source edits. The other dirty paths in `git status` (`exceptions.py`, `docs/feedback.md`) belong to a different in-flight cycle and are out-of-scope per `AGENTS.md` "Unexpected file modifications" rule.

### DRY findings disposition

Both DRY items are explicit trigger-deferrals: the sync/async post-processor pair waits on a second module importing the helpers OR a third coercion case beyond `Manager`/`QuerySet`; the four-guard validation block waits on a second `DjangoType`-target factory (`DjangoConnectionField` / `DjangoNodeField`) adopting the same preamble. No DRY action this cycle.

### Temp test verification

No temp tests created. The fix is comment/docstring/GLOSSARY-only with zero behavior change; existing permanent tests already pin every underlying contract the edited text describes (e.g. `test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied` for the `__call__`-branch coverage now reflected in both the docstring re-anchor and the GLOSSARY widening).

### Worker 2 notes-for-Worker-3 disposition

Worker 2 flagged out-of-artifact-scope sibling citation drift at `tests/test_list_field.py:3` (stale `docs/spec-020-list_field-0_0_7.md` path) and `tests/test_list_field.py:578` (stale `docs/feedback.md High #2` citation). Spot-confirmed both exist verbatim at the cited lines. Deferring is the correct call for this cycle — the artifact's Low #2 and Low #3 both explicitly scope to `list_field.py` sites, and touching the test file would expand cycle scope in violation of "no unrelated cleanup." The drift is real, Low-grade, and grep-discoverable; it belongs to a future review pass or a dedicated citation-drift sweep, not a re-spawn of this cycle.

### Changelog disposition verification

`git diff -- CHANGELOG.md` is empty (0 lines). Disposition cites both `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this cycle. The "internal-only" framing is honest: all four edits are documentation tightening with no consumer-visible behavior change (the `__call__`-branch coverage the GLOSSARY now mentions shipped in `0.0.7` already and is pinned by an existing test). `Not warranted` is the correct state.

### Validation spot-verification

- `uv run ruff format --check .` — `183 files already formatted`. Matches Worker 2's recorded outcome.
- `uv run ruff check .` — `All checks passed!`. Matches Worker 2's recorded outcome.

### Verification outcome

cycle accepted; verified.

---

## Comment/docstring pass

Folded into the consolidated single-spawn above — see `## Fix report (Worker 2)`.

### Files touched

- `django_strawberry_framework/list_field.py:3, 62-65, 86-89, 92` — see Fix report.
- `docs/GLOSSARY.md:315` — see Fix report.

### Per-finding dispositions

- Low 1 (stale `spec-016` → `spec-020` on Decision-5 guard comment): fixed at `list_field.py:92`.
- Low 2 (stale `docs/spec-020-…` → `docs/SPECS/spec-020-…`, two sites): fixed at `list_field.py:3` (module docstring) and `list_field.py:88` (factory docstring). Verified target path exists on disk.
- Low 3 (dangling `docs/feedback.md High #2` citation): fixed at `list_field.py:62-65` by re-anchoring to the contract-pin test (artifact-suggested option (c)).
- Low 4 (GLOSSARY `DjangoListField` async-detection clause narrows the contract): fixed at `docs/GLOSSARY.md:315` using the artifact's verbatim suggested replacement.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3

See `## Fix report (Worker 2)` notes above; nothing additional for the comment pass.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed"), AND the active plan does not authorize a `CHANGELOG.md` edit for this cycle. The four Lows are documentation tightening: a stale spec-citation correction, two stale-archive-path corrections, a dangling-citation re-anchor to a contract-pin test, and a GLOSSARY clause widening that documents the existing `__call__`-branch coverage (no behavior change — the High #2 fix that added the `__call__` branch shipped in `0.0.7` and is already pinned by `tests/test_list_field.py::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied`). No consumer-facing surface changes; no `CHANGELOG.md` edit warranted.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Iteration log
