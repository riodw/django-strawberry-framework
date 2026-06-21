# Review: `django_strawberry_framework/testing/_wrap.py`

Status: verified

## DRY analysis

- None — the module is a single 18-line public helper (`safe_wrap_connection_method`) plus a long docstring; the one shared predicate it needs (`_is_database_failure`) is already single-sourced in `_django_patches.py::_is_database_failure` (`_django_patches.py:134`) and imported here (`_wrap.py #"from django_strawberry_framework._django_patches import _is_database_failure"`), which is exactly the "both halves share the same private `_DatabaseFailure` predicate" contract the module docstring promises (`_wrap.py:16-19`). The unwrap-time twin (`_django_patches.py::_patched_remove_databases_failures #"if _is_database_failure(method)"`, `_django_patches.py:178`) routes through the same predicate. There is no second call site or near-copy to fold.

## High:

None.

## Medium:

None.

## Low:

### `current = getattr(connection, method_name)` raises a bare `AttributeError` on an unknown method name rather than a wrap-helper-shaped error

`safe_wrap_connection_method` validates `wrapper` callability up front with a targeted `TypeError` (`_wrap.py:139-142`) precisely so a consumer typo surfaces at the wrap site with a clear, helper-branded message. The parallel typo — a misspelled `method_name` (e.g. `"curser"`) — falls through `getattr(connection, method_name)` (`_wrap.py:143`) and raises a bare `AttributeError` from `getattr`, not a helper-branded message. This is correct today: the `getattr` still fails loudly AT the wrap site (not at a delayed `connection.<method>()` call), so the core "surface at wrap time" goal the `wrapper` guard documents is met; adding a second validation branch for symmetry would cost a branch plus a test for a marginal message-quality gain.

Defer until a consumer-facing report shows the bare `AttributeError` is confusing in practice, OR until a second optional "create the attribute if absent" mode is requested (at which point the implicit "method must already exist" precondition becomes a real branch worth a dedicated message). Until then the current single-guard shape is the right surface area for a test helper.

## What looks solid

### DRY recap

- **Existing patterns reused.** The wrap/unwrap defense-in-depth is built on one shared predicate: `_is_database_failure` is defined once (`_django_patches.py:134`) and consumed by both the unwrap-time backstop (`_django_patches.py:178`) and this wrap-time helper (`_wrap.py:27,144`). No local re-implementation of the `_DatabaseFailure is not None and isinstance(...)` test — the graceful "install rather than crash" degradation when Django moves the private symbol lives inside the shared predicate, not duplicated here, so the two halves cannot drift on what counts as Django's wrapper.
- **New helpers considered.** None warranted — the file is a single public function with one decision (decline vs. install) and one guard (`callable`); nothing to extract.
- **Duplication risk in the current file.** None. The static overview reports 0 repeated string literals and 0 TODO comments; the lone f-string (`_wrap.py #"received a non-callable wrapper"`) is a unique diagnostic. One `getattr`, one `setattr`, no parallel branches.

### Other positives

- **Correct lifecycle ordering.** The callability guard (`_wrap.py:139-142`) runs before any `getattr`/`setattr`, so a non-callable wrapper raises `TypeError` without mutating connection state — pinned by `tests/testing/test_wrap.py::test_safe_wrap_connection_method_raises_on_non_callable_wrapper`, which asserts `connection.cursor is original_cursor` after the raise.
- **Decline-before-clobber semantics are the whole point and are exact.** `_is_database_failure(current)` short-circuits to `return False` (`_wrap.py:144-145`) and leaves the connection method untouched, mirroring `django-debug-toolbar`'s `wrap_cursor` isinstance check named in the docstring. Pinned by `test_safe_wrap_connection_method_declines_when_database_failure_in_place`.
- **Private-symbol drift is graceful, not fatal.** When Django's `_DatabaseFailure` is unavailable, `_is_database_failure` returns `False`, so the helper installs the wrapper instead of crashing the public `testing` import — pinned by `test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing`.
- **Method-name generality is pinned.** `test_safe_wrap_connection_method_works_on_arbitrary_method_names` exercises `chunked_cursor`, guarding against the helper drifting toward a cursor-specific shape.
- **End-to-end composition is tested.** `test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth` wires the wrap-time decline together with the unwrap-time patched `_remove_databases_failures` and proves the two halves restore the original cleanly.
- **Typing is honest.** `wrapper: Callable[..., Any]` (`_wrap.py:33`) is enforced at runtime by the explicit callability guard rather than left as an unchecked annotation; `BaseDatabaseWrapper` is the correct narrow type for `connection`; the `-> bool` return is exactly the documented install/decline signal.
- **Restoration contract is scoped, not silently dropped.** The docstring carries a worked `setUp`/`tearDown` example making explicit that the helper handles only the wrap step and the consumer owns restoration, and that the unwrap-time backstop makes omitting it non-fatal — so there is no hidden re-entrancy or idempotent-unwrap expectation buried in the helper.
- **GLOSSARY contract matches source.** `docs/GLOSSARY.md` `## safe_wrap_connection_method` (lines 1149-1168) states the exact contract the source implements — declines and returns `False` (method untouched) when `_DatabaseFailure` is in place, installs and returns `True` otherwise, the wrap-time/unwrap-time defense-in-depth split (shipped `0.0.7`), and the debug-toolbar mirror. No drift on this public-contract symbol.

### Summary

`_wrap.py` is a clean, well-documented single-function consumer-facing test helper: `safe_wrap_connection_method` validates `wrapper` is callable, declines (returns `False`, state untouched) when Django's `_DatabaseFailure` is already installed, and otherwise installs the wrapper (returns `True`). The `_DatabaseFailure` predicate is single-sourced in `_django_patches.py` and shared with the unwrap-time backstop, so the two halves cannot drift; restoration is explicitly delegated to the consumer with a worked example, so no re-entrancy or idempotent-wrapping concern is hidden in the helper. Logic is correct and every branch (non-callable wrapper, `_DatabaseFailure` present, private-symbol absent, arbitrary method name, full wrap+unwrap composition) is pinned by a dedicated test in `tests/testing/test_wrap.py`. Both the per-cycle baseline diff (`62de611a`) and the HEAD diff for this file are empty, GLOSSARY prose is accurate, and both ruff commands report clean. No High or Medium; one forward-looking Low with an explicit trigger. No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `289 files left unchanged` (no changes; the COM812-vs-formatter advisory is pre-existing config noise, not a result of this cycle).
- `uv run ruff check --fix .` — `All checks passed!`

### Notes for Worker 3
- No source, test, GLOSSARY, or CHANGELOG edits were made. Both `git diff 62de611af325b1eabce0a586ffa1d0515bbe2e5f -- django_strawberry_framework/testing/_wrap.py` and `git diff HEAD -- django_strawberry_framework/testing/_wrap.py` are empty.
- Per-Low disposition: the single Low (bare `AttributeError` on a misspelled `method_name` via `getattr(connection, method_name)`, `_wrap.py:143`) is forward-looking with an explicit trigger ("a consumer-facing report shows the bare `AttributeError` is confusing in practice, OR a second optional 'create the attribute if absent' mode is requested"). No source edit warranted.
- No GLOSSARY-only fix in scope — `docs/GLOSSARY.md` lines 1149-1168 already match the source contract verbatim.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits warranted. The module docstring (`_wrap.py:1-20`) and the `safe_wrap_connection_method` docstring (`_wrap.py:35-138`) accurately describe install/decline/`False`-return, the `TypeError` wrap-site guard, the restoration-is-the-consumer's-responsibility contract with worked example, and the `django-debug-toolbar` precedent. No stale references, no obsolete TODOs (overview reports 0 TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source change this cycle (empty diff), so there is nothing to record; and per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_11.md`, silent on changelog entries for review cycles), `CHANGELOG.md` is not touched.

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit cycle (shape #5). Zero-edit proof holds: `git diff 62de611af325b1eabce0a586ffa1d0515bbe2e5f -- django_strawberry_framework/testing/_wrap.py` empty, `git diff HEAD -- django_strawberry_framework/testing/_wrap.py` empty, `git diff --stat 62de611a -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty (owned paths). Target absent from the dirty list; all dirty files are `docs/review/`, `docs/dry/`, `docs/feedback2.md`, and `docs/spec-038-…` — sibling-cycle artifacts and concurrent-maintainer doc work (AGENTS.md #34), none touching the target. Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern."

- **High / Medium: None — confirmed genuine.**
  - *Wrap/install idempotency & connection safety.* Callability guard (`_wrap.py #"if not callable(wrapper)"`) runs before any `getattr`/`setattr`, so a non-callable `wrapper` raises `TypeError` without mutating connection state — pinned by `test_safe_wrap_connection_method_raises_on_non_callable_wrapper` (asserts `connection.cursor is original_cursor` after the raise). Decline path short-circuits `return False` leaving the method untouched — pinned by `test_safe_wrap_connection_method_declines_when_database_failure_in_place` (asserts `connection.cursor is django_wrapper`). Install path `setattr` + `return True` — pinned by `test_safe_wrap_connection_method_installs_wrapper_when_no_database_failure`.
  - *Consumer-owned restoration.* No re-entrancy or idempotent-unwrap expectation buried in the helper — restoration is explicitly delegated to the consumer via the worked `setUp`/`tearDown` example (`_wrap.py` docstring), with the unwrap-time backstop making omission non-fatal. No hidden state.
  - *`_is_database_failure` single-source linkage shared with the unwrap backstop.* Verified independently: `_is_database_failure` is defined once at `_django_patches.py:134-136` (`return _DatabaseFailure is not None and isinstance(method, _DatabaseFailure)`), imported by the wrap helper (`_wrap.py #"from django_strawberry_framework._django_patches import _is_database_failure"`, used `_wrap.py #"if _is_database_failure(current)"`) AND consumed by the unwrap backstop `_patched_remove_databases_failures` (`_django_patches.py:178`). The two halves cannot drift on what counts as Django's wrapper, and the `_DatabaseFailure is not None` guard means a future private-symbol move degrades the helper (installs rather than crashes the public `testing` import) — pinned by `test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing` (patches `_DatabaseFailure` to `None`, asserts install). End-to-end composition pinned by `test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth`.
- **Low (bare `AttributeError` on misspelled `method_name`): genuinely forward-looking.** `getattr(connection, method_name)` (`_wrap.py #"current = getattr(connection, method_name)"`) raises a bare `AttributeError` on a typo. This still fails loudly AT the wrap site (not at a delayed `connection.<method>()` call), so the documented "surface at wrap time" goal is met; the Low carries verbatim two-part trigger phrasing (consumer-facing confusion report OR an "create-the-attribute-if-absent" mode). Forward, not a missed fix. Not a GLOSSARY-only fix.

### DRY findings disposition
DRY-None confirmed. Independently grep-verified: `_is_database_failure` has exactly one definition (`_django_patches.py:134`) and two consumers (the wrap helper and the unwrap backstop at `:178`) — no local re-implementation of the `_DatabaseFailure is not None and isinstance(...)` test, no second call site or near-copy to fold. The module is a single 18-line public function with one decision and one guard; nothing to extract.

### Temp test verification
- None — no behavior suspicion required a temp test; existing suite (`tests/testing/test_wrap.py`, 6 tests) pins every branch (install, decline, symbol-missing, arbitrary method name, wrap+unwrap composition, non-callable guard). No pytest run warranted (no test introduced, all claims confirmable by read+grep).

### Changelog disposition verification
`git diff -- CHANGELOG.md` empty. "Not warranted" cites BOTH AGENTS.md and the active plan's silence. Internal-only framing matches the empty-diff scope. Accepted.

### GLOSSARY (#4-vs-#5 gate)
`docs/GLOSSARY.md ## safe_wrap_connection_method` read against live source: declines-and-returns-`False` (method untouched) when `_DatabaseFailure` in place, installs-and-returns-`True` otherwise, wrap-time/unwrap-time defense-in-depth split (shipped `0.0.7`), debug-toolbar `wrap_cursor` mirror — all accurate. Public symbol correctly carries an entry. No GLOSSARY-only fix exists in scope → genuine #5, not a missed #4.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box at `docs/review/review-0_0_11.md:129`.
