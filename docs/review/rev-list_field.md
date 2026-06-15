# Review: `django_strawberry_framework/list_field.py`

Status: verified

## DRY analysis

- None — the file's two near-identical post-process indirections (`_post_process_consumer_sync`/`_async`, list_field.py:42-47) are thin named entry points over the already-DRY single-sited contract in `utils/querysets.py::post_process_queryset_result_sync`/`_async`; the two validators (`_validate_djangotype_target`/`_validate_relay_djangotype_target`, list_field.py:50-122) are the canonical shared guards consumed cross-module by `relay.py:166` and `connection.py:1206`, so the consolidation already happened (0.0.9 DRY pass, `docs/feedback.md` Major 1 + Major 4). Nothing left to hoist.

## High:

None.

## Medium:

None.

## Low:

### GLOSSARY omits `is_async_callable`'s partial-unwrapping in the `DjangoListField` entry

`docs/GLOSSARY.md:355` (the `DjangoListField` entry) describes async-resolver detection as "via `inspect.iscoroutinefunction` (checked on the resolver itself AND on its `__call__`...)". The source actually routes through `utils/typing.py::is_async_callable` (list_field.py:176), which is a strict superset of that prose: besides the resolver and its `__call__`, it also unwraps a one-hop `functools.partial` (`utils/typing.py::is_async_callable` #"value.func if isinstance(value, functools.partial)"). The GLOSSARY text is not wrong about what it lists — it is incomplete: a `functools.partial(async_callable)` resolver IS detected, but the prose would lead a reader to think it is not. This is descriptive prose on a public-contract symbol; the missing clause is the partial case. Non-blocking — defer to a GLOSSARY-accuracy pass, OR fold into the next edit that touches the `DjangoListField` entry. Suggested replacement clause: "...detected at construction time via the partial-aware `is_async_callable` predicate (checked on the resolver, its `__call__`, and through a one-hop `functools.partial`)...". Not promoted to Medium because the connection-field and relay node entries share the same predicate and the same prose pattern, so this is a package-wide GLOSSARY-phrasing item, not a `list_field.py` defect — forwarded for the project pass `docs/review/rev-django_strawberry_framework.md` to decide whether to sweep all three entries together.

## What looks solid

### DRY recap

- **Existing patterns reused.** The default-resolver body (list_field.py:163-171) reuses `initial_queryset` + `apply_type_visibility_sync`/`_async` from `utils/querysets.py:58-138`; the consumer-resolver wrappers reuse `post_process_queryset_result_sync`/`_async` (utils/querysets.py:141-165); the async predicate is the shared `is_async_callable` (utils/typing.py:20); the Relay-shape check delegates to `types/base.py::_is_relay_shaped` (types/base.py:446). No local re-implementation of any of these.
- **New helpers considered.** Inlining `_post_process_consumer_sync`/`_async` (list_field.py:42-47) into the `_wrap` bodies was considered — rejected: they are the deliberately-named module-scope entry points (rev6 H2/H3) that keep the consumer-wrapper call sites readable and the `utils/querysets` contract single-sited; collapsing them would re-spread the contract into the factory body.
- **Duplication risk in the current file.** The `_validate_djangotype_target` / `_validate_relay_djangotype_target` pair (list_field.py:50-122) is intentional sibling design, not a near-copy: the relay variant delegates the four base checks to the base variant (list_field.py:119) and only adds the fifth Relay-shape guard. The `2x DjangoListField` literal (the `field=` arg at list_field.py:150 and the `noqa` comment at 125) is a self-naming constant, not a hoistable duplicate.

### Other positives

- **Async-detection asymmetry is correct and documented.** The default resolver uses runtime `in_async_context()` per-call (list_field.py:165) so one factory output serves both `execute_sync` and `await execute`, while the consumer-wrapper branch commits per-construction via `is_async_callable` (list_field.py:176) because Strawberry freezes sync-vs-async at schema build. The divergence is justified inline (list_field.py:151-160) and matches `connection.py:1005` / `types/relay.py:816,877`.
- **Default-resolver async branch returns the coroutine directly.** `_default` returns `apply_type_visibility_async(...)` without an inner `async def` wrapper (list_field.py:170), correctly relying on Strawberry's `AwaitableOrValue` dispatch — avoids a redundant coroutine layer. Matches the maintainer's standing async-sqlite/unawaited-coroutine discipline.
- **Await-before-post-process is correct.** The async `_wrap` awaits the consumer coroutine BEFORE passing the value to `_post_process_consumer_async` (list_field.py:183-186), so `normalize_query_source`'s `isinstance(..., QuerySet)` test (utils/querysets.py:88-90) sees the awaited value, not the coroutine. The sync `_wrap` mirrors this without await.
- **Validator ordering invariant is load-bearing and documented.** `_validate_djangotype_target` checks isclass → issubclass → own-class-registration → callable-resolver in order (list_field.py:80-96), and the docstring (list_field.py:62-74) correctly explains why the third check uses `definition.origin is target_type` rather than `hasattr` (MRO inheritance would wrongly accept a `Meta`-less subclass). The strict identity guard is the right call — verified against `types/base.py::DjangoType.__init_subclass__` setting `__django_strawberry_definition__` only for concrete own-`Meta` subclasses.
- **Outer-list nullability is consumer-annotation-driven, not factory-driven.** The factory returns a bare `strawberry.field(resolver=...)` (list_field.py:199-204) with no return annotation on the wrappers that would override the consumer's class-attribute annotation; `list[T]` → `[T!]!` and `list[T] | None` → `[T!]` is picked up from the consumer's annotation as documented (GLOSSARY.md:355). Correct — the factory must not stamp an outer type.
- **Cross-module reuse confirmed.** `_validate_relay_djangotype_target` is consumed by `connection.py:1206` and `relay.py:166` (the latter via the thin `_validate_node_target` wrapper, relay.py:157-167); `_validate_djangotype_target` backs the relay variant. The `field=` self-naming arg keeps each factory's `ConfigurationError` messages naming itself. No drift between the docstring's claimed consumers and the actual call sites.
- **Cycle diff against baseline is empty** — the file is unchanged this cycle; all findings are verification of standing behavior.

### Summary

`list_field.py` is a mature, heavily-reviewed factory module (rev4-rev6 history visible in the inline anchors). The default/consumer/sync/async dispatch matrix is correct, the validator ordering invariant is sound and well-documented, outer-nullability is correctly left to the consumer annotation, and every shared helper is reused rather than re-implemented — the 0.0.9 DRY pass already extracted the contract into `utils/querysets.py` and `utils/typing.py`, and the two validators are the canonical cross-module guards. No logic, ORM, async, or typing defects found. The single Low is a GLOSSARY-prose incompleteness (the `DjangoListField` entry describes the async-detection predicate as `inspect.iscoroutinefunction`-based, omitting the `functools.partial` unwrapping that `is_async_callable` actually performs) and is forwarded to the project pass because the same prose pattern recurs across the connection and relay node entries. Logic is correct; no Worker 2 source fix needed for this cycle — collapsed to no-source-edit (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 267 files left unchanged.
- `uv run ruff check --fix .` — All checks passed.

### Notes for Worker 3
- No High / no Medium. Single Low (GLOSSARY async-detection prose incompleteness on the `DjangoListField` entry, GLOSSARY.md:355) is forwarded to the project pass `docs/review/rev-django_strawberry_framework.md` because the same `inspect.iscoroutinefunction`-vs-`is_async_callable` prose pattern recurs across the connection and relay node entries — it is a package-wide GLOSSARY-phrasing sweep, not a `list_field.py`-local defect, so no GLOSSARY edit is in scope for THIS cycle.
- No GLOSSARY-only fix in scope (the forwarded Low is intentionally NOT edited here — it routes through the project pass).
- Cycle diff against `f4b9cbf80496421062350c6d84df7e6df0fe4641` for this file is empty; file unchanged.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source, test, or doc edits were made (no-source-edit cycle); AGENTS.md forbids CHANGELOG updates unless explicitly instructed, and the active plan `docs/review/review-0_0_10.md` is silent on any changelog requirement for review cycles.

---

## Verification (Worker 3)

Shadow-file dicta acknowledged: the shadow strips comments and replaces string literals with `...`, so its line numbers are not canonical; original source line numbers and the artifact's references are treated as authoritative. The shadow was used only to confirm control flow (symbol inventory: 8 symbols, 2 branch hotspots — matches the source).

### Logic verification outcome

No-source-edit cycle (shape #5). High 0 / Medium 0 / Low 1. The single Low (GLOSSARY async-detection prose incompleteness on the `DjangoListField` entry) is genuinely forward-looking and correctly deferred — independently re-derived below, it does NOT mask a present-tense High/Medium:

- **Low premise verified accurate, not a source defect.** `docs/GLOSSARY.md:355` (the `DjangoListField` entry) describes async detection "via `inspect.iscoroutinefunction` (checked on the resolver itself AND on its `__call__` so callable-instance resolvers with `async def __call__` are also covered)" — verbatim, with NO `functools.partial` clause. The source actually routes through `utils/typing.py::is_async_callable` (list_field.py:176), whose body unwraps a one-hop partial (`utils/typing.py::is_async_callable` #"value.func if isinstance(value, functools.partial)", confirmed at the `target = value.func if isinstance(value, functools.partial) else value` line) and whose docstring explicitly enumerates both the `__call__` and the `functools.partial` superset cases. So the GLOSSARY prose is incomplete (a `partial(async_callable)` resolver IS detected but the prose implies otherwise) — a descriptive-prose gap on a public-contract symbol, NOT a behavioral defect. The source comment (list_field.py:156-158) already names the predicate as the "`__call__`/`functools.partial`-aware superset of `inspect.iscoroutinefunction`", so only the standing GLOSSARY text lags. Correctly Low and correctly NOT a source edit.
- **Forward correctly recorded for the project-pass author.** The Low is forwarded to `docs/review/rev-django_strawberry_framework.md` because the same `inspect.iscoroutinefunction`-vs-`is_async_callable` prose pattern recurs across the connection-field and relay-node GLOSSARY entries — a package-wide GLOSSARY-phrasing sweep, not a `list_field.py`-local fix. Recorded in the artifact's Low section and `## Notes for Worker 3`; the project-pass author can collect it from there. No GLOSSARY edit in scope this cycle (the disqualifying GLOSSARY-only fix is correctly absent).
- **Async/sync dispatch sanity-checked independently.** Default resolver uses runtime `in_async_context()` per-call (list_field.py:165) returning the `apply_type_visibility_async` coroutine directly (list_field.py:170, relying on Strawberry AwaitableOrValue); consumer-wrapper branch commits per-construction via `is_async_callable` (list_field.py:176) and awaits the consumer coroutine BEFORE post-processing (list_field.py:183-186). The asymmetry is justified inline (list_field.py:151-160). Correct.
- **Outer-nullability annotation pickup sanity-checked independently.** The factory returns a bare `strawberry.field(resolver=wrapped, ...)` (list_field.py:199-204) with no return annotation on `_default`/`_wrap` that would override the consumer's class-attribute annotation. GLOSSARY:355 documents `list[T]` → `[T!]!` and `list[T] | None` → `[T!]` as consumer-annotation-driven. The factory does not stamp an outer type — correct.
- **Cross-module validator reuse confirmed.** `_validate_relay_djangotype_target` is imported and called at `connection.py:59,1206` and `relay.py:63,166`; `_validate_djangotype_target` backs the relay variant (list_field.py:119) and is called directly at list_field.py:150; `_is_relay_shaped` exists at `types/base.py:446`. The two validators are the canonical cross-module guards as claimed.

### DRY findings disposition

DRY=None and accepted. Re-confirmed: post-process indirections (`_post_process_consumer_sync`/`_async`, list_field.py:42-47) are thin named entry points over the single-sited `utils/querysets.py::post_process_queryset_result_sync`/`_async` contract (0.0.9 DRY pass); the two validators are the canonical shared guards consumed cross-module (verified above). Nothing left to hoist.

### Temp test verification

- No temp tests created — no-source-edit cycle; all claims verified by source re-read + grep against canonical paths. No new behavior shipped that would require a permanent test.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `list_field.py` checklist box at `docs/review/review-0_0_10.md`.

Shape #5 gates all met: empty `git diff --stat` over owned paths (`django_strawberry_framework/`, `tests/`, `docs/GLOSSARY.md`, `CHANGELOG.md`) vs baseline `f4b9cbf80496421062350c6d84df7e6df0fe4641`; both Worker 2 sections open with "Filled by Worker 1 per no-source-edit cycle pattern."; the single Low carries its verbatim trigger phrasing and is forwarded (no disqualifying GLOSSARY-only fix); changelog Not-warranted cites BOTH AGENTS.md and the active plan's silence; ruff `format --check` ("1 file already formatted") and `check` ("All checks passed!") both pass.
