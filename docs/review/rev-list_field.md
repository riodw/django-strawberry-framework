# Review: `django_strawberry_framework/list_field.py`

Status: verified

## DRY analysis

- **Default-branch async dispatch shape is shared verbatim with the Relay node defaults; do NOT extract.** `list_field.py::DjangoListField._default` (lines 161-169) and `types/relay.py::_resolve_node_default` (relay.py:815-820) both run the `if in_async_context(): return <async helper>(...)` / else `apply_type_visibility_sync(...)` shape. The shared *primitives* (`initial_queryset`, `apply_type_visibility_sync/_async`) already live single-sited in `utils/querysets.py`; what remains per-site is the 3-line runtime-context fork plus each caller's distinct tail (list returns the qs as-is; relay adds an id filter + `.get()/.first()`). Wrapping the fork itself would re-hide the per-surface tail behind a maybe-await abstraction — the exact anti-pattern `utils/querysets.py` (lines 13-17, 83-86) deliberately rejected. Keep as-is; no trigger.
- None beyond the above — the four validator guards, the Manager→QuerySet coercion, and the visibility hooks are already extracted to `_validate_djangotype_target` / `utils/querysets.py` and reused by `connection.py` + `relay.py` (the 0.0.9 DRY pass landed cleanly).

## High:

None.

## Medium:

None.

## Low:

### Comment names `inspect.iscoroutinefunction` where the code calls `is_async_callable`

The async-detection comment in the `DjangoListField` body states the consumer-wrapper branch "commits per-construction via `inspect.iscoroutinefunction(user_resolver)`", but the branch actually calls `is_async_callable(user_resolver)`:

```django_strawberry_framework/list_field.py:155:158
            # and ``await schema.execute``. The consumer-wrapper branch below commits
            # per-construction via ``inspect.iscoroutinefunction(user_resolver)``
            # because Strawberry inspects the resolver signature once at schema
            # construction and freezes the sync-vs-async handling.
```

```django_strawberry_framework/list_field.py:173:174
        user_resolver = resolver
        if is_async_callable(user_resolver):
```

`is_async_callable` (`utils/typing.py::is_async_callable`) is deliberately a *superset* of bare `inspect.iscoroutinefunction`: it also inspects `__call__` (callable-instance resolvers with `async def __call__`) and unwraps `functools.partial`. Those exact cases are pinned by tests `tests/test_list_field.py::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied` (line 531), `::test_djangolistfield_partial_wrapped_async_resolver_gets_get_queryset_applied` (line 580), and `::test_djangolistfield_partial_wrapped_async_callable_object_resolver_gets_get_queryset_applied` (line 636) — all of which bare `inspect.iscoroutinefunction(user_resolver)` would fail to route. The comment therefore names a detection mechanism that contradicts both the code and its own tests. The GLOSSARY entry already describes the real behavior correctly ("checked on the resolver itself AND on its `__call__`"); only this source comment is stale. No behavior impact — comment-pass fix only.

Recommended change: replace the comment's `` ``inspect.iscoroutinefunction(user_resolver)`` `` with `` ``is_async_callable(user_resolver)`` `` (optionally noting it is the `__call__`/partial-aware predicate), so the comment matches line 174 and the module's actual contract.

### `_validate_relay_djangotype_target` placement is a project-pass responsibility question, not a local defect

The Relay-shaped validator `_validate_relay_djangotype_target` lives in the *non-Relay* `list_field.py` and is imported by both `connection.py:59` and `relay.py:63` (neither used by `list_field` itself). Co-locating it with its base `_validate_djangotype_target` is defensible (the base genuinely belongs here and the relay variant delegates to it), but "the relay validator imported out of the list-field module" is a cross-file ownership smell better judged at the folder/project pass with the connection/relay artifacts in view. Forward-looking: defer to `docs/review/rev-django_strawberry_framework.md` (project pass), which can decide whether both validators should migrate to a shared field-guards module once the third consumer (card 032's `DjangoNodeField`) lands as the docstring at lines 58-59 anticipates. No action in this cycle.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_default` (lines 161-169) reuses `initial_queryset` + `apply_type_visibility_sync/_async` from `utils/querysets.py:58-138`; the consumer-wrapper helpers `_post_process_consumer_sync/_async` (lines 42-47) are thin named entry points over `post_process_queryset_result_sync/_async` (`utils/querysets.py:141-165`); `is_async_callable` (line 174) is the shared `utils/typing.py` predicate also used by `connection.py:997` and `types/base.py:360`. The 0.0.9 DRY pass single-sited the Manager→QuerySet coercion and the visibility-hook routing exactly as the module headers claim.
- **New helpers considered.** Extracting the `_default` runtime-context fork into a shared helper was evaluated and rejected (see DRY analysis bullet 1): it would re-hide each caller's distinct tail behind a maybe-await abstraction that `utils/querysets.py` intentionally avoids.
- **Duplication risk in the current file.** The repeated literal `"DjangoListField"` (factory name at the line-125 `def` + the `field="DjangoListField"` guard arg at line 150) is intentional — the `field=` parameter exists precisely so each factory interpolates its own public name into `ConfigurationError` messages; collapsing it to a constant would couple the message text to the symbol name and defeat the per-factory wording seam (`_validate_djangotype_target` docstring, lines 60-63).

### Other positives

- **Async/sync split is correct and test-pinned.** The default branch uses runtime `in_async_context()` (per-call dispatch, so one factory output serves both `execute_sync` and `await execute` — pinned by `test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution`, line 251), while the consumer branch commits per-construction via `is_async_callable` (Strawberry freezes resolver sync/async handling at schema-build). The asymmetry is intentional and documented; it mirrors `connection.py` (default `def` lazy-queryset vs `is_async_callable` consumer branch) and the `relay.py` node defaults.
- **rev6 H1 micro-optimization is sound.** The async default arm returns the `apply_type_visibility_async(...)` coroutine directly rather than wrapping it in a redundant `async def` (lines 164-168); Strawberry's `AwaitableOrValue` dispatch awaits it. No extra coroutine layer.
- **rev4 H2 await-ordering is correct.** The async `_wrap` awaits the consumer coroutine *before* handing the value to `_post_process_consumer_async` (lines 181-185), so the `normalize_query_source` isinstance check in `utils/querysets.py:150,162` sees the awaited value, not the coroutine. Pinned by the async-consumer-resolver tests (lines 439-523).
- **Validator ordering is load-bearing and documented.** The own-class registration check (`definition.origin is target_type`, line 89) correctly rejects an MRO-inherited definition that bare `hasattr` would accept — the docstring (lines 66-74) explains the data-isolation rationale precisely.
- **Outer-nullability is correctly delegated to the consumer annotation.** The factory returns `strawberry.field(...)` with no return-type assertion (lines 197-202); `list[T]` → `[T!]!` vs `list[T] | None` → `[T!]` is driven entirely by the class-attribute annotation. Pinned by `examples/fakeshop/test_query/test_library_api.py:622` (the `list[BranchType] | None` nullable-outer case).
- **Metadata pass-through is complete.** `description`, `deprecation_reason`, `directives` forward verbatim into the inner `strawberry.field(...)` (lines 199-201).
- **Optimizer cooperation needs nothing here.** The default resolver returns a lazy queryset; root-position optimization rides the existing `info.path.prev is None` gate in `DjangoOptimizerExtension` — no list-field-specific optimizer wiring, consistent with the GLOSSARY's "rides the existing root-gated hook" claim. `optimizer/walker.py:213` independently reuses `apply_type_visibility_sync` for nested targets.

### GLOSSARY drift quick-check

`#djangolistfield` (`docs/GLOSSARY.md:333-337` plus the index rows at lines 29, 69, 152) is accurate and current. It correctly describes: factory-not-class, outer-nullability from the consumer annotation, the `_default_manager.all()` + `get_queryset` default body in both sync/async (sync rejects an async hook with `ConfigurationError`), the Manager/QuerySet coercion on consumer returns, **construction-time async detection via `inspect.iscoroutinefunction` checked on the resolver AND its `__call__`** (this is the behavior the *source comment* at line 156 gets wrong — the GLOSSARY is right), Python-list pass-through, optimizer root-gating, and metadata pass-through. No replacement text needed.

### Summary

`list_field.py` is in strong shape after the 0.0.9 DRY pass: the Manager→QuerySet coercion, visibility-hook routing, and validator guards are all single-sited and reused by `connection.py`/`relay.py`, and the sync/async dispatch split (runtime `in_async_context` for the default, construction-time `is_async_callable` for consumers) is correct and thoroughly test-pinned. No High or Medium findings. The only actionable defect is a single stale comment (line 156) that names `inspect.iscoroutinefunction` where the code calls the superset predicate `is_async_callable` — a comment that actively contradicts three of the module's own tests. One forward-looking Low defers the `_validate_relay_djangotype_target` placement question to the project pass. Because the comment correction is a real source edit, this routes through a standard cycle (not no-source-edit shape #5).

---

## Fix report (Worker 2)

Consolidated single-spawn (per worker-2 role file): the only in-cycle edit is a single
trivially-localised comment correction with no logic change, so logic + comment + changelog
collapse into one pass. Low 2 is forward-looking (deferred to the project pass) and requires no
edit. Logic+comment+changelog filled together; `Status: fix-implemented` set once.

### Files touched
- `django_strawberry_framework/list_field.py:155-158` — comment correction only (Low 1). No logic
  edit; the comment now names the predicate the code actually calls.

### Tests added or updated
- None. Pure comment correction, zero executable lines changed. The three tests the artifact cites
  (`tests/test_list_field.py::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied`,
  `::test_djangolistfield_partial_wrapped_async_resolver_gets_get_queryset_applied`,
  `::test_djangolistfield_partial_wrapped_async_callable_object_resolver_gets_get_queryset_applied`)
  already pin the `is_async_callable` superset behavior; no new pinning is warranted for a comment.

### Validation run
- `uv run ruff format .` — pass / no-changes (265 files left unchanged).
- `uv run ruff check --fix .` — pass / All checks passed (standing COM812-vs-formatter config
  warning only; not an error).

### Notes for Worker 3
- Shadow file used: `docs/shadow/django_strawberry_framework__list_field.overview.md` (overview
  only; line numbers there are non-canonical — source line numbers cited throughout).
- Predicate confirmed in source before editing: `list_field.py:174` calls
  `is_async_callable(user_resolver)` (import at `list_field.py:27` from `.utils.typing`). The stale
  comment was at `list_field.py:156`.
- Low 2 (`_validate_relay_djangotype_target` placement) left forward-looking: no edit, deferred to
  `docs/review/rev-django_strawberry_framework.md` (project pass) exactly as Worker 1's prose
  directs.
- No false-premise rejections; the artifact premise matched source verbatim.
- `git diff` vs baseline `0872a20` for this file: +4/-2. `uv.lock` untouched. Other dirty files in
  `git status` are concurrent maintainer/other-worker work, out of scope (AGENTS.md #33).

---

## Verification (Worker 3)

### Logic verification outcome
- High / Medium: none in artifact; none introduced. Confirmed.
- Low 1 (stale comment): ADDRESSED. Source calls `is_async_callable(user_resolver)` —
  grep-confirmed at `list_field.py:176` (the call) and `:156` (the corrected comment), imported at
  `:27` from `.utils.typing`. (Artifact prose cited line 174; actual call is line 176 — immaterial
  drift, line numbers are non-canonical scratchpad refs and the predicate is unambiguously present.)
  `is_async_callable` is defined at `utils/typing.py:20` and its docstring documents exactly the
  `__call__`-and-`functools.partial`-aware superset behaviour the corrected comment now names — so
  the comment no longer contradicts the code or the three pinning tests. Diff is **comment-only**
  (+4/-2): every changed line sits inside the comment block at lines 155-160; no executable, no logic
  line touched.
- Low 2 (`_validate_relay_djangotype_target` placement): correctly LEFT forward-looking, no edit.
  Artifact preserves the deferral and forwards it to the project pass
  (`docs/review/rev-django_strawberry_framework.md`); recorded here and confirmed.

### DRY findings disposition
DRY analysis carried no trigger (the `_default` runtime-context fork is intentionally not extracted;
the shared primitives already live single-sited in `utils/querysets.py`). Nothing to action.

### Temp test verification
- None used. The fix is a pure comment correction with zero executable change; the three cited tests
  (`tests/test_list_field.py::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied`
  and the two `partial_wrapped_*` variants) already pin the `is_async_callable` superset behaviour.
  No temp test warranted; pytest not run (AGENTS.md / role: no executable change introduced).

### Validation
- `git diff 0872a20 -- list_field.py`: +4/-2, comment-only (verified line-by-line).
- `uv run ruff format --check django_strawberry_framework/list_field.py`: "1 file already formatted".
- `uv run ruff check django_strawberry_framework/list_field.py`: "All checks passed!" (standing
  COM812-vs-formatter warning only).
- `git diff -- CHANGELOG.md`: empty. `git diff --stat 0872a20 -- CHANGELOG.md docs/GLOSSARY.md`:
  empty. Changelog `Not warranted` cites both AGENTS.md #21 and the active plan's silence — correct,
  and the internal-only framing matches the comment-only diff scope.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `list_field.py`
checklist box in `docs/review/review-0_0_9.md`.

---

## Comment/docstring pass

(Consolidated into the single spawn above — performed in the same pass as Low 1 is comment-only.)

### Files touched
- `django_strawberry_framework/list_field.py:155-158` — replaced the comment's backticked
  `` ``inspect.iscoroutinefunction(user_resolver)`` `` with `` ``is_async_callable(user_resolver)`` ``
  and annotated it as the `` ``__call__``/``functools.partial``-aware `` superset of
  `inspect.iscoroutinefunction`, so the comment matches the predicate the code calls at line 174.

  Old:
  > The consumer-wrapper branch below commits per-construction via
  > `` ``inspect.iscoroutinefunction(user_resolver)`` `` because Strawberry inspects the resolver
  > signature once at schema construction and freezes the sync-vs-async handling.

  New:
  > The consumer-wrapper branch below commits per-construction via
  > `` ``is_async_callable(user_resolver)`` `` (the `` ``__call__``/``functools.partial``-aware ``
  > superset of `` ``inspect.iscoroutinefunction`` ``) because Strawberry inspects the resolver
  > signature once at schema construction and freezes the sync-vs-async handling.

### Per-finding dispositions
- Low 1: fixed — comment now names `is_async_callable`, matching `list_field.py:174` and the module
  contract; the optional `__call__`/`functools.partial` note suggested by the artifact was included.
- Low 2: left forward-looking, no edit — deferred to the project pass
  (`docs/review/rev-django_strawberry_framework.md`) per Worker 1's deferral.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3
GLOSSARY (`#djangolistfield`) already described the real behavior; no GLOSSARY edit needed (the
artifact's quick-check confirms this). Only the source comment was stale.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
The cycle's only edit is a source-comment correction with zero behaviour change and no
consumer-visible surface change. Per `AGENTS.md` #21 ("Do not update CHANGELOG.md unless explicitly
instructed") AND the active review plan's silence on changelog authorization for this per-file cycle
(per-file cycles are never the authorising scope — any CHANGELOG drift forwards to the project pass
`docs/review/rev-django_strawberry_framework.md`), no changelog entry is warranted.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Iteration log
