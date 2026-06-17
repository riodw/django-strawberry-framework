# Review: `django_strawberry_framework/testing/_wrap.py`

Status: verified

## DRY analysis

- None — the module is a single ~9-line public helper (`safe_wrap_connection_method`) plus a long docstring; the one shared predicate it needs (`_is_database_failure`) is already single-sourced in `_django_patches.py:129` and imported here (`_wrap.py:27`), which is exactly the "both halves share the same private `_DatabaseFailure` predicate" contract the module docstring promises (`_wrap.py:16-19`). There is no second call site or near-copy to fold.

## High:

None.

## Medium:

None.

## Low:

### `current = getattr(connection, method_name)` raises `AttributeError` on an unknown method name rather than a wrap-helper-shaped error

`safe_wrap_connection_method` validates `wrapper` callability up front with a targeted `TypeError` (`_wrap.py:139-142`) precisely so a consumer typo surfaces at the wrap site with a clear message. The parallel typo — a misspelled `method_name` (e.g. `"curser"`) — falls through `getattr(connection, method_name)` (`_wrap.py:143`) and raises a bare `AttributeError` from `getattr`, not a helper-branded message. This is correct today (the `getattr` does fail loudly at the wrap site, not at a delayed `connection.<method>()` call, so the core "surface at wrap time" goal the `wrapper` guard documents is still met), and adding a second validation branch for symmetry would cost a branch + a test for a marginal message-quality gain.

Defer until a consumer-facing report shows the bare `AttributeError` is confusing in practice, OR until a second optional "create the attribute if absent" mode is requested (at which point the implicit "method must already exist" precondition becomes a real branch worth a dedicated message). Until then the current single-guard shape is the right surface area for a test helper.

## What looks solid

### DRY recap

- **Existing patterns reused.** The wrap/unwrap defense-in-depth is built on one shared predicate: `_is_database_failure` is defined once in `_django_patches.py:129` and imported by both the unwrap-time backstop (`_django_patches.py:173`) and this wrap-time helper (`_wrap.py:27,144`). No local re-implementation of the `_DatabaseFailure is not None and isinstance(...)` test — the helper degrades (returns "install") rather than crashes when Django moves the private symbol, and that degradation lives in the shared predicate, not duplicated here.
- **New helpers considered.** None warranted — the file is a single public function; there is nothing to extract.
- **Duplication risk in the current file.** None. Zero repeated string literals (shadow overview confirms), one `getattr`/one `setattr`, no parallel branches.

### Other positives

- **Correct lifecycle ordering.** The callability guard (`_wrap.py:139-142`) runs *before* any `getattr`/`setattr`, so a non-callable wrapper raises without mutating connection state — pinned by `tests/testing/test_wrap.py::test_safe_wrap_connection_method_raises_on_non_callable_wrapper`, which asserts `connection.cursor is original_cursor` after the raise.
- **Decline-before-clobber semantics are the whole point and are exact.** `_is_database_failure(current)` short-circuits to `return False` (`_wrap.py:144-145`) and leaves the connection method untouched, mirroring `django-debug-toolbar`'s `wrap_cursor` isinstance check named in the docstring. Pinned by `test_safe_wrap_connection_method_declines_when_database_failure_in_place` (asserts the wrapper was NOT replaced).
- **Private-symbol drift is graceful, not fatal.** When Django's `_DatabaseFailure` is unavailable, `_is_database_failure` returns `False`, so the helper installs the wrapper instead of crashing the public `testing` import — pinned by `test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing`.
- **Method-name generality is pinned.** `test_safe_wrap_connection_method_works_on_arbitrary_method_names` exercises `chunked_cursor`, guarding against the helper drifting toward a cursor-specific shape.
- **End-to-end composition is tested.** `test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth` wires the wrap-time decline together with the unwrap-time patched `_remove_databases_failures` and proves the two halves restore the original cleanly.
- **Typing is honest.** `wrapper: Callable[..., Any]` (`_wrap.py:33`) is enforced at runtime by the explicit callability guard rather than left as an unchecked annotation; `BaseDatabaseWrapper` is the correct narrow type for `connection`. The `-> bool` return is exactly the documented install/decline signal.
- **Docstrings match behavior.** Module and function docstrings describe the install/decline/`False` semantics, the `TypeError` raise, and the restoration-is-the-consumer's-responsibility contract — all consistent with the implementation. GLOSSARY entry (`docs/GLOSSARY.md:1124-1143`) is accurate: "shipped (0.0.7)", returns `False` on decline / `True` + install otherwise, pairs with the Trac #37064 hardening. No drift.

### Summary

`_wrap.py` is a clean, well-documented single-function consumer-facing test helper. It is unchanged since baseline `14910230` (empty `git log 14910230..HEAD` and empty `git diff HEAD`); the change context's "wrapt-based wrapping" note does not apply — the module uses plain `getattr`/`setattr` and the shared `_is_database_failure` predicate, not `wrapt`. Logic is correct and edge cases (non-callable wrapper, `_DatabaseFailure` present, private-symbol absent, arbitrary method name, full wrap+unwrap composition) are each pinned by a dedicated test in `tests/testing/test_wrap.py`. No High or Medium. One forward-looking Low (unbranded `AttributeError` on a misspelled `method_name`) recorded with an explicit trigger. GLOSSARY is accurate. No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, 270 files left unchanged (pre-existing COM812-vs-formatter advisory notice only).
- `uv run ruff check --fix .` — pass, "All checks passed!".

### Notes for Worker 3
- Shadow overview used: `docs/shadow/django_strawberry_framework__testing___wrap.overview.md` (+ `.stripped.py`). Shadow line numbers not canonical; artifact cites original source.
- Single Low is forward-looking with an explicit trigger ("Defer until a consumer-facing report shows the bare `AttributeError` is confusing in practice, OR until a second optional 'create the attribute if absent' mode is requested"). No source edit warranted.
- No GLOSSARY-only fix in scope — `docs/GLOSSARY.md:1124-1143` verified accurate against the implementation.
- Empty `git log 14910230..HEAD` and empty `git diff HEAD` for the target; no behavior change anywhere.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits warranted. Module docstring (`_wrap.py:1-20`) and function docstring (`_wrap.py:35-138`) accurately describe install/decline/`False`-return, the `TypeError` wrap-site guard, the restoration-is-consumer-responsibility contract, and the django-debug-toolbar precedent. No stale comments, no obsolete TODOs (shadow confirms zero TODO anchors).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source change in this cycle (empty diff), so there is nothing to record; and per AGENTS.md #21 / START.md, `CHANGELOG.md` is not touched unless explicitly instructed, and the active plan (`docs/review/review-0_0_10.md`) records no changelog requirement for review cycles.

---

## Verification (Worker 3)

Shadow caveat: `docs/shadow/django_strawberry_framework__testing___wrap.overview.md` strips `#` comments and replaces string-literal tokens with `...`; its line numbers are not canonical. Original source line numbers and this artifact's references are treated as canonical; the shadow was used only for control-flow confirmation (1 symbol, 2 branch nodes, 1 `getattr`/1 `setattr`, 0 TODOs, 0 repeated literals — matches the artifact).

### Logic verification outcome

No-source-edit cycle (shape #5); no High/Medium/Low fix to implement. Confirmed the helper's behavior directly against source `_wrap.py:139-147`:
- **Lifecycle ordering** — `callable(wrapper)` guard (`:139-142`) precedes both `getattr` (`:143`) and `setattr` (`:146`), so a non-callable wrapper raises `TypeError` without mutating connection state. Pinned by `test_safe_wrap_connection_method_raises_on_non_callable_wrapper` (asserts `connection.cursor is original_cursor` after the raise, `tests/testing/test_wrap.py:164-187`).
- **Decline-before-clobber** — `_is_database_failure(current)` short-circuits to `return False` (`:144-145`) leaving the method untouched. Pinned by `test_safe_wrap_connection_method_declines_when_database_failure_in_place`.
- **Private-symbol drift** — `_DatabaseFailure is None` path returns `False` so the helper installs rather than crashing the public import. Pinned by `test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing`.
- **Method-name generality** — pinned by `test_safe_wrap_connection_method_works_on_arbitrary_method_names` (`chunked_cursor`).
- **End-to-end composition** — pinned by `test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth`. All six branches pinned in `tests/testing/test_wrap.py`.

The single Low (bare `AttributeError` on a misspelled `method_name` via `getattr(connection, method_name)`, `:143`) is genuinely forward-looking with a falsifiable trigger ("a consumer-facing report shows the bare `AttributeError` is confusing in practice, OR a second optional 'create the attribute if absent' mode is requested"). Confirmed the current single-guard shape is correct today: the `getattr` fails loudly AT the wrap site, satisfying the "surface at wrap time" goal the `wrapper` guard documents; the missing branch would buy only message-quality at the cost of a branch + test. No GLOSSARY-only fix present (disqualifier absent).

### DRY findings disposition

Artifact's DRY None is correct and is the load-bearing claim. Verified by grep: `def _is_database_failure` appears exactly once (`_django_patches.py:129`), and all uses are the single def (`:129`), the unwrap-time backstop (`:173`), and this wrap-time helper's import + call (`_wrap.py:27,144`). No local re-implementation of the `_DatabaseFailure is not None and isinstance(...)` test — the predicate body (`_django_patches.py:131`) is single-sourced and read by both defense-in-depth halves, exactly as the module docstring (`_wrap.py:16-19`) promises. The graceful-degradation-on-symbol-move lives in the shared predicate, not duplicated here. No second call site or near-copy to fold.

### Temp test verification

None used. The six existing tests in `tests/testing/test_wrap.py` cover every branch; no behavior is in doubt and the cycle introduced no edit, so no focused pytest run was warranted (per worker-3.md "do not run pytest preemptively").

### Shape #5 checks

1. `git diff HEAD -- django_strawberry_framework/testing/_wrap.py` empty; `git log 14910230..HEAD -- _wrap.py` empty. File is absent from the cycle-wide diff stat (`git diff --stat 14910230 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) — the absence is the zero-edit proof. The dirty paths in that stat belong to OTHER planned cycle items (filters/orders/optimizer/management/permissions/types/utils + their tests + GLOSSARY/CHANGELOG/version bump), not to this item; this item's own diff is empty.
2. All three Worker 2 sections open with `Filled by Worker 1 per no-source-edit cycle pattern.`
3. The single Low carries verbatim trigger phrasing; no GLOSSARY-only fix.
4. Changelog `Not warranted` cites BOTH AGENTS.md #21 and the active plan's silence; `git diff -- CHANGELOG.md` is empty (no contradiction). Internal-only framing is honest — the helper is consumer-facing API but the cycle made NO change to it, so there is nothing consumer-visible to record.
5. `uv run ruff format --check` → "1 file already formatted" (COM812-vs-formatter advisory only); `uv run ruff check` → "All checks passed!".

GLOSSARY (`docs/GLOSSARY.md:1124-1143`) verified accurate against the implementation: shipped 0.0.7, returns `False` + leaves method untouched on decline / `True` + install otherwise, mirrors debug-toolbar's wrap-time isinstance check, pairs with the Trac #37064 unwrap-time hardening. No drift.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `testing/_wrap.py` checklist box in `docs/review/review-0_0_10.md`.

---

## Iteration log

(none)
