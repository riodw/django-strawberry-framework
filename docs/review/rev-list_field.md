# Review: `django_strawberry_framework/list_field.py`

Status: verified

## DRY analysis

- None — the file's two post-process indirections (`_post_process_consumer_sync`/`_async`, list_field.py:42-47) are thin named entry points over the already single-sited contract in `utils/querysets.py::post_process_queryset_result_sync`/`_async` (list_field.py:42-47 delegate verbatim to querysets.py:153-177); the two validators (`_validate_djangotype_target`/`_validate_relay_djangotype_target`, list_field.py:50-122) are the canonical shared guards consumed cross-module by `relay.py:236` and `connection.py:1236`, so the consolidation already happened (0.0.9 DRY pass, `docs/feedback.md` Major 1 + Major 4). Nothing left to hoist.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The default-resolver body (list_field.py:163-171) reuses `initial_queryset` + `apply_type_visibility_sync`/`_async` from `utils/querysets.py:58,100,134`; the consumer-resolver wrappers reuse `post_process_queryset_result_sync`/`_async` (utils/querysets.py:153,168); the async predicate is the shared `is_async_callable` (utils/typing.py:20); the Relay-shape check delegates to `types/base.py::_is_relay_shaped` (types/base.py:446). No local re-implementation of any of these.
- **New helpers considered.** Inlining `_post_process_consumer_sync`/`_async` (list_field.py:42-47) into the `_wrap` bodies was considered — rejected: they are the deliberately-named module-scope entry points (rev6 H2/H3) that keep the consumer-wrapper call sites readable and the `utils/querysets` contract single-sited; collapsing them would re-spread the contract into the factory body.
- **Duplication risk in the current file.** The `_validate_djangotype_target` / `_validate_relay_djangotype_target` pair (list_field.py:50-122) is intentional sibling design, not a near-copy: the relay variant delegates the four base checks to the base variant (list_field.py:119) and only adds the fifth Relay-shape guard. The `2x DjangoListField` literal (the `field=` arg at list_field.py:150 and the `noqa` comment at 125) is a self-naming constant, not a hoistable duplicate.

### Other positives

- **Prior-cycle Low is resolved upstream.** The 0.0.10 cycle's single Low — the `DjangoListField` GLOSSARY entry describing async detection as `inspect.iscoroutinefunction`-based, omitting the `functools.partial` unwrapping — is now fixed in `docs/GLOSSARY.md:364`, which reads "detected at construction time via the partial-aware `is_async_callable` predicate (checked on the resolver, on its `__call__`... and through a one-hop `functools.partial`)". This is exactly the replacement clause the prior artifact supplied. No GLOSSARY drift remains; nothing to forward this cycle.
- **Async-detection asymmetry is correct and documented.** The default resolver uses runtime `in_async_context()` per-call (list_field.py:165) so one factory output serves both `execute_sync` and `await execute`, while the consumer-wrapper branch commits per-construction via `is_async_callable` (list_field.py:176) because Strawberry freezes sync-vs-async at schema build. The divergence is justified inline (list_field.py:151-160).
- **Default-resolver async branch returns the coroutine directly.** `_default` returns `apply_type_visibility_async(...)` without an inner `async def` wrapper (list_field.py:170), correctly relying on Strawberry's `AwaitableOrValue` dispatch — avoids a redundant coroutine layer. Matches the maintainer's standing async-sqlite/unawaited-coroutine discipline.
- **Await-before-post-process is correct.** The async `_wrap` awaits the consumer coroutine BEFORE passing the value to `_post_process_consumer_async` (list_field.py:183-186), so `normalize_query_source`'s `isinstance(..., QuerySet)` test sees the awaited value, not the coroutine. The sync `_wrap` mirrors this without await.
- **Validator ordering invariant is load-bearing and documented.** `_validate_djangotype_target` checks isclass → issubclass → own-class-registration → callable-resolver in order (list_field.py:80-96), and the docstring (list_field.py:62-74) correctly explains why the third check uses `definition.origin is target_type` rather than `hasattr` (MRO inheritance would wrongly accept a `Meta`-less subclass). Verified against `types/base.py::DjangoType.__init_subclass__` setting `__django_strawberry_definition__` only for concrete own-`Meta` subclasses.
- **Outer-list nullability is consumer-annotation-driven, not factory-driven.** The factory returns a bare `strawberry.field(resolver=...)` (list_field.py:199-204) with no return annotation on the wrappers that would override the consumer's class-attribute annotation; `list[T]` → `[T!]!` and `list[T] | None` → `[T!]` is picked up from the consumer's annotation as documented (GLOSSARY.md:364). The factory must not stamp an outer type.
- **Cross-module reuse confirmed.** `_validate_relay_djangotype_target` is imported and called at `connection.py:59,1236` and `relay.py:64,236` (the latter via the thin `_validate_node_target` wrapper); `_validate_djangotype_target` backs the relay variant. The `field=` self-naming arg keeps each factory's `ConfigurationError` messages naming itself. No drift between the docstring's claimed consumers and the actual call sites.
- **Cycle diff against baseline is empty** — `git diff fab9d0c4984f334d554a9d133a12b0d453571db0 -- django_strawberry_framework/list_field.py` and `git diff HEAD -- …` are both empty; the file is unchanged this cycle. All findings are verification of standing behavior.

### Summary

`list_field.py` is a mature, heavily-reviewed factory module (rev4-rev6 history visible in the inline anchors) and is unchanged since the 0.0.10 cycle. The default/consumer/sync/async dispatch matrix is correct, the validator ordering invariant is sound and well-documented, outer-nullability is correctly left to the consumer annotation, and every shared helper is reused rather than re-implemented — the 0.0.9 DRY pass already extracted the contract into `utils/querysets.py` and `utils/typing.py`, and the two validators are the canonical cross-module guards consumed by `connection.py` and `relay.py`. The 0.0.10 cycle's single Low (GLOSSARY async-detection prose incompleteness) has since been fixed at GLOSSARY.md:364, so no findings carry forward. No logic, ORM, async, or typing defects found. Collapsed to no-source-edit (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 289 files left unchanged.
- `uv run ruff check --fix .` — All checks passed!

### Notes for Worker 3
- No High / no Medium / no Low. The 0.0.10 cycle's single Low (GLOSSARY async-detection prose on the `DjangoListField` entry) is now resolved at `docs/GLOSSARY.md:364`, which reads the partial-aware `is_async_callable` clause the prior artifact recommended — nothing forwarded, nothing to fix.
- No GLOSSARY-only fix in scope — GLOSSARY:364 is current (verified by grep against the source comment at list_field.py:156-158 and `utils/typing.py::is_async_callable`).
- Cycle diff against baseline `fab9d0c4984f334d554a9d133a12b0d453571db0` for this file is empty; file unchanged vs both baseline and HEAD.
- Concurrent-maintainer dirty files (`inspect_django_type.py` + test, `types/base.py`) ignored per AGENTS.md #33 — out of scope for this target.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source, test, or doc edits were made (no-source-edit cycle); AGENTS.md #21 forbids CHANGELOG updates unless explicitly instructed, and the active plan `docs/review/review-0_0_11.md` is silent on any changelog requirement for review cycles.

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium / Low findings to address — all three are `None.` and the determinations are genuine, not lazy. Independently re-read the source:
- Validator ordering invariant (`_validate_djangotype_target`, list_field.py:80-96): isclass → issubclass → own-class registration → callable-resolver, each check assuming the prior passed. The third check uses `definition is None or getattr(definition, "origin", None) is not target_type` — the strict own-class invariant the docstring claims, not `hasattr` (an inherited `__django_strawberry_definition__` would wrongly accept a `Meta`-less subclass). Correct.
- `_validate_relay_djangotype_target` (list_field.py:119-122) delegates the four base checks then adds the Relay-shape fifth via `_is_relay_shaped` — sibling design, not a near-copy.
- Async-detection asymmetry: default `_default` uses runtime `in_async_context()` per-call (list_field.py:165) so one factory output serves both `execute_sync` and `await execute`; consumer-wrapper branch commits per-construction via `is_async_callable(user_resolver)` (list_field.py:176) because Strawberry freezes sync/async at schema build. Divergence justified inline (list_field.py:151-160).
- Async `_wrap` awaits the consumer coroutine BEFORE passing to `_post_process_consumer_async` (list_field.py:183-186) so the isinstance-QuerySet test sees the awaited value; sync `_wrap` mirrors without await. Correct.
- Default async branch returns `apply_type_visibility_async(...)` directly (list_field.py:170), relying on Strawberry's `AwaitableOrValue` dispatch — no redundant coroutine layer.
No masked defect forcing a source edit; `None.` severities are genuine.

### DRY findings disposition
DRY analysis is the justified single `None` — the two post-process indirections delegate verbatim to `utils/querysets.py`, the two validators are the canonical cross-module guards consumed by `connection.py` and `relay.py` (0.0.9 DRY pass already hoisted the contract). Nothing left to extract; nothing to carry forward.

### Shape #5 / #4 gate
Confirmed genuine #5, not a missed #4:
- Zero-edit proof two ways: `git diff fab9d0c4984f334d554a9d133a12b0d453571db0 -- django_strawberry_framework/list_field.py` empty AND `git diff HEAD -- …` empty; target absent from the owned-paths stat (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`).
- Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern."
- GLOSSARY `DjangoListField` entry (GLOSSARY.md:364) verified accurate against live source: reads the partial-aware `is_async_callable` clause ("detected at construction time via the partial-aware `is_async_callable` predicate (checked on the resolver, on its `__call__`... and through a one-hop `functools.partial`)"), which matches `utils/typing.py::is_async_callable` (partial `.func` hop + `__call__` iscoroutinefunction check). The prior 0.0.10 Low (async-detection prose incompleteness) is resolved upstream; no GLOSSARY-only fix owed, nothing forwarded.
- The only GLOSSARY working-tree hunk vs HEAD is at line 305 (relation-cardinality validation) — concurrent-maintainer #33 work, outside list_field territory.
- Dirty working-tree paths (`inspect_django_type.py` + its test, `types/base.py`, GLOSSARY:305) attribute to concurrent-maintainer #33 work per AGENTS.md #33; not a rejection trigger.

### Changelog disposition
"Not warranted" — `git diff -- CHANGELOG.md` empty; cites BOTH AGENTS.md #21 and the active plan's silence. Internal-only framing is honest (zero edits, no public-API change). Accepted.

### Temp test verification
None — no temp tests needed; zero-edit cycle verified by diff + independent source read.

### Validation run
- `uv run ruff format --check django_strawberry_framework/list_field.py` — 1 file already formatted.
- `uv run ruff check django_strawberry_framework/list_field.py` — All checks passed!

### Verification outcome
cycle accepted; verified — sets top-level `Status: verified` AND marks the `list_field.py` checklist box.
