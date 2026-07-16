# DRY review: `django_strawberry_framework/extensions/debug.py`

Status: verified

ITEM_BASELINE: `d4cfd513ea60850eb98808b69bd609afceb34ecb`

## System trace

`extensions/debug.py` owns the complete **response-extensions debug** surface:
`DjangoDebugExtension` (Strawberry `SchemaExtension`) plus the module-private capture,
serialize, and assemble helpers that make its wire contract real. Opt-in is the **class**
in `extensions=[..., DjangoDebugExtension]` (one fresh instance per operation; requires
`strawberry-graphql>=0.316.0`). Off by default; never root-exported (subpackage path is the
opt-in signal — already verified under `extensions/__init__.py`).

Owned responsibilities (each already single-sited inside this file):

1. **Overlap-safe `force_debug_cursor` bracketing** —
   `_CursorCaptureCoordinator` / `_CaptureToken` / `_ActiveCapture` / module `_coordinator`.
   Reference-counted, lock-protected, keyed by concrete connection wrapper object (not alias).
   Saves and restores the prior flag; does not attribute rows or open unused aliases.
2. **Query-log slice + graphene-shaped SQL rows** — `_ConnectionSnapshot`,
   `_query_log_entries_since`, `_serialize_sql_row` (`vendor` / `alias` / `sql` / `duration` /
   `isSlow` / `isSelect`; `_SLOW_QUERY_SECONDS = 10`).
3. **Execution-exception rows** — `_terminal_original_error` (bounded
   `GraphQLError.original_error` walk), `_serialize_exception` (graphene
   `excType` / `message` / `stack`), `_collect_exceptions` (skip pure parse/validation;
   preserve result-error order).
4. **Payload assembly + two-phase diagnostic degrade** — `_build_payload` always returns both
   lists; SQL failures keep rows already serialized, exception failures degrade to `[]`; both
   log server-side and never touch `data` / `errors`.
5. **Lifecycle / publish contract** — `on_operation` (pre-yield acquire + snapshot via
   `ExitStack`; post-yield stash only when `execution_context.result` is a graphql-core
   `ExecutionResult`) and idempotent `get_results` (`{"debug": payload}` or `{}`).

Connected surfaces traced (evidence, not co-owners of this wire contract):

- **`middleware/debug_toolbar.py`** — sibling *developer* surface: soft-dep HTTP middleware
  that injects a top-level `debugToolbar` object (panel titles / `requestId`) into tagged
  JSON responses and appends a GraphiQL bridge template. Shares the "debug tooling, not
  production" posture and the product framing as an in-response counterpart, but owns a
  different delivery seam, different payload key/shape, different dependency boundary, and
  no SQL/exception serialization. Folder / project passes may revisit posture docs; this
  file does not own toolbar injection.
- **`optimizer/extension.py`** — the other package `SchemaExtension`. Deliberately opposite
  lifetime: singleton-in-a-factory (plan cache) vs class-form per-operation isolation. Module
  and class docstrings already document the contrast; consumers and live tests
  (`test_debug_extension_api.py`) place `lambda: _optimizer` beside `DjangoDebugExtension`
  to keep both lifetimes visible. No shared capture or payload code.
- **`exceptions.py`** — package exception hierarchy with call-time safe `__str__` /
  `__repr__` so graphql-core `located_error`'s unguarded `str(original_error)` cannot
  destroy typed identity. Interacts with debug only as a *possible* terminal exception type
  that happens to render safely; see Verification.
- **`utils/typing.py::_MAX_TYPE_WRAPPER_DEPTH`** — same numeric ceiling (64) as
  `_MAX_ORIGINAL_ERROR_HOPS`, different domain and failure policy (raise on corrupt type
  chain vs best-effort return last unique candidate). Comment in-target already records the
  deliberate non-import.
- **`extensions/__init__.py`** — eager public re-export only; no behavior.
- **Tests** — `tests/extensions/test_debug.py` (mechanics unreachable over live HTTP:
  serializers, coordinator, masking order, async overlap, degrade) and
  `examples/fakeshop/test_query/test_debug_extension_api.py` plus
  `test_multi_db.py` (live `/graphql/` HTTP via probe URLconf). Wire keys and the 10s slow
  threshold are independently re-spelled in package tests (spec-044 DRY D4) — intentional
  drift detection, not a second production owner.
- **Baseline** — `git diff d4cfd513ea60850eb98808b69bd609afceb34ecb --
  django_strawberry_framework/extensions/debug.py` is empty; working tree matches the
  item baseline for the target.

## Verification

Searches / reads (concepts and names):

- `force_debug_cursor`, `queries_log`, `CaptureQueriesContext`, `isSlow` / `isSelect` /
  `excType`, `_serialize_exception`, `original_error` walks, `_MAX_*DEPTH` / `_MAX_*HOPS`,
  `DjangoDebugExtension`, `SchemaExtension` across `django_strawberry_framework/` and the
  debug test trees.
- Full read of `middleware/debug_toolbar.py`, `optimizer/extension.py` (lifecycle /
  opt-in shape), `exceptions.py` (current call-time safe render — not the retired
  construction-time `_sanitize_exc_arg` name), `utils/typing.py` unwrap ceilings,
  `extensions/__init__.py`, live + package debug suites.

Rejected / deferred candidates (tried to disprove shared ownership):

1. **`_serialize_exception` vs `exceptions.py` safe render (`__str__` / `__repr__`, helpers
   `_safe_type_name` / `_safe_arg_repr`).** Fresh executable probe (not inherited from the
   exceptions.py DRY artifact):
   - `ConfigurationError(Hostile())` where `Hostile.__str__` / `__repr__` raise →
     `str(err) == "<unprintable Hostile>"` and `_serialize_exception(err)` succeeds
     (framework types already render safely before debug sees them).
   - plain `ThirdPartyHostile(Exception)` with raising `__str__` →
     `_serialize_exception` raises; `_build_payload([], ExecutionResult(errors=[GraphQLError(...,
     original_error=tp)]))` logs and returns `exceptions: []`.
   - **Disproved as one responsibility.** `exceptions.py` protects **typed wire identity**
     through graphql-core's unguarded `str(original_error)` with no outer `except` before
     `located_error` replaces the exception. `_serialize_exception` builds a **diagnostic
     row** for an arbitrary `BaseException` and relies on `_build_payload`'s degrade-and-log
     `except Exception`. Unifying would force incompatible recovery policies (fail-safe
     identity vs best-effort empty/partial diagnostics) onto one helper, and would pull
     private hierarchy helpers into a development extension that must accept third-party
     exceptions the hierarchy never sees. Couples domains that must change independently.

2. **`_MAX_ORIGINAL_ERROR_HOPS = 64` vs `utils/typing.py::_MAX_TYPE_WRAPPER_DEPTH = 64`.**
   Same Power-of-Ten budget, different chains (`GraphQLError.original_error` vs
   `of_type` wrappers) and opposite stop policies (return last unique candidate vs raise
   `RuntimeError`). Importing the typing constant would falsely imply a shared invariant
   and a shared failure mode. Rejected; local constant stays.

3. **Consolidate with `middleware/debug_toolbar.py`.** Different seams (`SchemaExtension`
   → `extensions.debug` vs HTTP middleware → `debugToolbar`), different payloads (SQL +
   exception rows vs toolbar panel metadata), different dependency stories (hard strawberry
   vs soft django-debug-toolbar with import-time install/app gates). The module docstring's
   "counterpart" language is product framing, not a claim of shared implementation. This
   file is not the toolbar owner; no consolidate-from-here move is warranted. Deferred only
   as folder/project evidence if a future pass asks whether *posture documentation* should
   cross-link more tightly — not a code merge.

4. **Share `SchemaExtension` lifecycle / opt-in shape with `DjangoOptimizerExtension`.**
   Opposite intentional lifetimes (plan-cache singleton factory vs per-operation class
   instance). Collapsing them would break either the plan cache or per-operation isolation.
   Rejected.

5. **Replace `_CursorCaptureCoordinator` with Django's `CaptureQueriesContext`.**
   Documented divergence: `CaptureQueriesContext.__enter__` eagerly opens every configured
   connection; this coordinator enables the flag without forcing aliases open and adds
   overlap-safe restore. Same underlying Django debug-cursor mechanism, deliberately
   different ownership of connection lifecycle. Rejected.

6. **Extract a shared "diagnostic degrade" helper over the two `_build_payload`
   `try`/`except Exception` blocks.** Same high-level policy (never fail the operation),
   different degrade contracts (keep partial SQL rows via `extend` vs assign `exceptions`
   to `[]` when collection fails). A shared helper would need a mode flag or lose one
   contract. Rejected — parallel structure is the clearest expression of the two-phase
   policy.

7. **Promote the live-test probe URLconf / holder pattern shared with
   `test_multi_db.py`.** Spec-044 DRY D3 already records "deliberately copied — not
   promoted." Test-placement rules prefer independently legible acceptance fixtures over a
   shared harness for two different opt-in schema shapes. Out of scope for this production
   file; not a package DRY opportunity owned here.

8. **Import production wire-key / slow-threshold constants into
   `tests/extensions/test_debug.py`.** Intentionally forbidden (independent literals so a
   rename fails the suite). Preserved repetition.

No permanent production consolidation survived disproof. No scratch file left under
`docs/dry/temp-tests/` (probe was inline and discarded).

## Opportunities

None — every responsibility this file claims already has a single authoritative
implementation here; the strongest near-duplicates (`exceptions.py` render safety,
toolbar middleware, optimizer extension lifetime, typing unwrap ceiling, Django
`CaptureQueriesContext`) were independently disproved as shared contracts. Sibling
`extensions/` folder pass remains open for package-level export/lifetime questions already
narrowed by the `__init__.py` item.

## Judgment

Zero-edit. `debug.py` is a dense but correctly bounded owner: one coordinator, one SQL
serializer, one exception-row path, one payload builder, one SchemaExtension lifecycle.
Apparent overlap with exceptions safe-render and with debug-toolbar is framing or adjacent
tooling, not duplicated policy. Ready for Worker 2.

## Implementation (Worker 1)

No source changes. Item-scoped diff against
`d4cfd513ea60850eb98808b69bd609afceb34ecb` for
`django_strawberry_framework/extensions/debug.py` is empty (re-checked after writing this
artifact). Only new tracked path for this item is this artifact itself. No new tests
(behavior unchanged; live suite in `examples/fakeshop/test_query/test_debug_extension_api.py`
and package suite in `tests/extensions/test_debug.py` already cover the contracts traced).
`ruff format` / `ruff check --fix` not run — no production or test edits. No changelog.
Plan checkbox left untouched (Worker 2 closes the item). Status `fix-implemented` as a
proved zero-edit handoff.

## Independent verification (Worker 2)

Re-traced `extensions/debug.py` as the sole owner of the response-extensions
`debug` wire contract (coordinator → SQL/exception serializers →
`_build_payload` → `DjangoDebugExtension` lifecycle). Confirmed connected
surfaces only as evidence: `middleware/debug_toolbar.py`,
`optimizer/extension.py`, `exceptions.py` call-time safe render,
`utils/typing.py::_MAX_TYPE_WRAPPER_DEPTH`, `extensions/__init__.py` re-export,
package + live debug test trees.

**Scoped diff empty.** Working-tree blob of
`django_strawberry_framework/extensions/debug.py` matches both
`ITEM_BASELINE` (`d4cfd513…`, hash `f8149cc9…`) and `HEAD`;
`git diff d4cfd513… -- django_strawberry_framework/extensions/debug.py` and
`git diff HEAD -- …/debug.py` are empty. Zero-edit precondition holds.
(Baseline commit is a stash WIP tip, not an ancestor of `HEAD`; blob identity
still proves the target file is unchanged from the recorded baseline.)

**Challenged `_serialize_exception` vs `exceptions.py` safe render.** Fresh
inline probe (not inherited):

- `ConfigurationError(Hostile())` with raising `__str__`/`__repr__` →
  `str(err) == "<unprintable Hostile>"` and `_serialize_exception(err)`
  succeeds (framework types already render safely).
- plain `ThirdPartyHostile(Exception)` with raising `__str__` →
  `_serialize_exception` raises; `_build_payload([], ExecutionResult(errors=[
  GraphQLError(..., original_error=tp)]))` logs and returns `exceptions: []`.

Rejection stands. `exceptions.py` owns **typed wire identity** through
graphql-core's unguarded `str(original_error)` with no outer catch before
`located_error` replaces the exception. `_serialize_exception` owns a
**graphene-shaped diagnostic row** for arbitrary `BaseException` and relies
on `_build_payload`'s degrade-and-log. Same syntactic `str(...)` is not one
responsibility; unifying would force incompatible recovery policies and pull
hierarchy helpers into a third-party exception path.

**Challenged debug-toolbar overlap.** Full read of
`middleware/debug_toolbar.py`: soft-dep HTTP middleware injecting top-level
`debugToolbar` (panel titles / `requestId`) plus GraphiQL bridge template.
No SQL row shape, no exception-row serialization, no `force_debug_cursor`
coordinator, different opt-in seam (`MIDDLEWARE` import vs
`extensions=[DjangoDebugExtension]`). Module docstring "counterpart"
language is product framing only. No consolidate-from-here move; folder /
project may still revisit posture docs.

**Other rejected candidates re-checked and disposed:**

| Candidate | Disposition |
| --- | --- |
| `_MAX_ORIGINAL_ERROR_HOPS` vs `_MAX_TYPE_WRAPPER_DEPTH` | Same numeric ceiling; opposite stop policy (best-effort return vs raise). Local constant stays. |
| Share lifecycle with `DjangoOptimizerExtension` | Opposite intentional lifetimes (per-op class vs plan-cache factory). |
| Replace coordinator with `CaptureQueriesContext` | Documented divergence: no eager alias open; overlap-safe restore. |
| Shared two-phase degrade helper | Partial-SQL `extend` vs exceptions `[]` — mode flag would obscure. |
| Promote live-test probe URLconf | Spec-044 DRY D3; test-placement, not production DRY. |
| Import wire-key / slow-threshold into tests | Intentional drift detection (spec-044 D4). |

**Missed-opportunity search.** Concept/name sweep for `force_debug_cursor`,
`queries_log`, `isSlow`/`isSelect`/`excType`, `_serialize_exception`,
`SchemaExtension`/`on_operation`/`get_results`, `DjangoDebug` across
`django_strawberry_framework/`: graphene wire keys and cursor coordinator
exist only in this file; the other `SchemaExtension` is the optimizer with
no shared capture/payload code; `mutations/resolvers.py` only mentions
`CaptureQueriesContext` in a test-wiring comment. No stale second production
owner, bypass, or duplicate policy found.

**Verdict:** zero-edit confirmed. Status → `verified`. Plan item checked.
No production edits, no commit, no scratch files left.
