# Review: `django_strawberry_framework/testing/_wrap.py`

Status: verified

Supersedes the on-disk `0.0.7`-era artifact (`Status: verified`); the active plan box (`review-0_0_9.md:106`) was unchecked. The prior artifact's second Low (CHANGELOG `django_strawberry_framework.test` path drift) is **already resolved in live source** and is NOT re-raised — see `### DRY recap` / Summary.

## DRY analysis

- **Defer — `_is_database_failure` single-sourcing is already correct.** The wrap site reads the shared predicate via `_wrap.py::safe_wrap_connection_method #"if _is_database_failure(current)"` (source line 144), importing it from `_django_patches.py::_is_database_failure` (source 129-131), which the unwrap site also calls (`_django_patches.py::_patched_remove_databases_failures #"if _is_database_failure(method)"`, source 173). The predicate is the entire shared contract between the wrap-time and unwrap-time halves and is single-sourced today; the import direction (`testing/_wrap.py` -> `_django_patches.py`) is correct because the patch module autoloads at `AppConfig.ready` and ships first. Defer until a third `_is_database_failure` call site lands in `testing/` (e.g. a `safe_unwrap_connection_method` companion or a `GraphQLTestCase` fixture); at that point evaluate hoisting the predicate into a neutral `testing/_database_failure.py` with `_django_patches.py` re-importing it. Trigger: a second `testing/`-package consumer of `_is_database_failure`.

## High:

None.

## Medium:

None.

## Low:

### Docstring example block omits the `TransactionTestCase` import it relies on

The runnable `.. code-block:: python` example (source 85-114) opens with `class _MyTest(TransactionTestCase):` (source 92) but its import block imports only `connections` and `safe_wrap_connection_method` (source 87-89). A consumer copy-pasting the block verbatim hits `NameError: name 'TransactionTestCase' is not defined` at the class statement. This helper is consumer-facing (`from django_strawberry_framework.testing import safe_wrap_connection_method`, `testing/__init__.py #"from django_strawberry_framework.testing._wrap import"`), so the docstring example is part of the published contract.

Why it matters: same citation/example-hygiene tier as prior `list_field.py` / `scalars.py` example Lows — the surrounding prose is correct; only the runnable snippet is incomplete. A consumer's first interaction with the helper is most likely this paste-and-run block.

Recommended change: add `from django.test import TransactionTestCase` to the example's import block, alongside the existing `from django.db import connections` and `from django_strawberry_framework.testing import safe_wrap_connection_method` lines. Keep `super().setUp()` / `super().tearDown()` as-is (they're shown).

```django_strawberry_framework/testing/_wrap.py:85:103
    .. code-block:: python

        from django.db import connections
        from django.test import TransactionTestCase
        from django_strawberry_framework.testing import safe_wrap_connection_method


        class _MyTest(TransactionTestCase):
            def setUp(self):
                super().setUp()
                self._connection = connections["default"]
                self._original_cursor = self._connection.cursor
```

### `getattr(connection, method_name)` can raise an undocumented `AttributeError`; the `Raises:` block only lists `TypeError`

`safe_wrap_connection_method #"current = getattr(connection, method_name)"` (source 143) reads the named attribute with no default, so a bogus `method_name` (typo, or a method that doesn't exist on the backend) raises `AttributeError` before the wrap. The docstring `Raises:` section (source 131-137) documents only the `TypeError` non-callable-wrapper case.

Why it matters: forward-looking, comment-tier. The current behavior is *correct* — a non-existent method name is a programmer error and failing loud at the wrap site is the right outcome (mirrors the `TypeError` rationale: "surfaces here rather than ... deep inside Django's ORM machinery"). The gap is only that the contract under-documents a second loud-failure mode a consumer can hit. Defer with trigger: when this docstring is next touched for any reason, add an `AttributeError: If method_name is not an attribute of connection.` bullet to the `Raises:` block so both wrap-site loud-failures are documented symmetrically. No logic change.

### `Restoration semantics` uses a `**bold**` lead-in while the surrounding sections use Google-style `Args:`/`Returns:`/`Raises:` headers — minor in-docstring style mix

The `**Restoration semantics.**` paragraph lead-in (source 81) is bold-prefixed prose, while the lower half of the docstring uses Google-style section headers (`Args:`/`Returns:`/`Raises:`, source 116-137) and the upper half uses `*`-bulleted RST-ish lists (source 66-74). The docstring mixes three light conventions.

Why it matters: cosmetic, latent. `help(safe_wrap_connection_method)` renders all three as flowing text, so the mismatch is invisible today; a future Sphinx/napoleon pass would render the Google headers as definition lists but the bold lead-in as inline-bold prose. Forward-looking: if this docstring is ever brought under a Sphinx build, normalize to one convention (Google-style throughout, since the `Args:`/`Returns:`/`Raises:` triad is load-bearing). No action now; trigger = a docs build lands for the `testing` subpackage.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module reuses the canonical `_django_patches.py::_is_database_failure` predicate (source 27 import, source 144 call) — the single shared contract between the wrap-time and unwrap-time halves of the Trac #37064 defense; it does not re-spell the `isinstance(..., _DatabaseFailure)` check or the `_DatabaseFailure is not None` import-resilience guard. Type imports (`Callable`, `Any`, `BaseDatabaseWrapper`) are the conventional stdlib/Django annotations.
- **New helpers considered.** A `testing/_database_failure.py` host module for the predicate was evaluated and deferred (single `testing/` consumer today; the import-from-`_django_patches` direction is correct given the patch module ships first at `AppConfig.ready`).
- **Duplication risk in the current file.** None — one function, zero repeated literals (shadow overview: 0 repeated string literals), no near-copy branches.

### Other positives

- **Guard ordering is correct and mutation-safe.** The `not callable(wrapper)` check (source 139-142) precedes the only `setattr` (source 146), so a non-callable wrapper can never leave the connection in a half-mutated state; the `TypeError` message echoes the offending value (`{wrapper!r}`) and the docstring's `Raises:` block explains the cursor-object-vs-callable footgun it catches. Pinned by `tests/testing/test_wrap.py::test_safe_wrap_connection_method_raises_on_non_callable_wrapper`.
- **Decline path is side-effect-free.** When `_is_database_failure(current)` is true the helper returns `False` with no `setattr` (source 144-145) — Django's wrapper is left untouched, which is the whole cooperative contract. Pinned by `::test_safe_wrap_connection_method_declines_when_database_failure_in_place`.
- **Multi-database safe by construction.** The helper operates only on the `BaseDatabaseWrapper` instance handed to it (`connections[alias]`); no global state, no default-alias assumption — any alias works. Pinned by `::test_safe_wrap_connection_method_works_on_arbitrary_method_names`.
- **Thread/process safety adequate for the documented surface.** The `getattr`-then-`setattr` is a non-atomic read-check-write, but Django `connections` is a thread-local registry and the helper is documented for `setUp`/`tearDown` (single-threaded test phase) with zero process-global mutable state — the TOCTOU window is benign in the intended usage. Not a finding.
- **Restoration semantics correctly delegated.** The helper deliberately does only the wrap step; the docstring's "Restoration semantics" block makes the caller responsible for saving/restoring the original, and the `_django_patches` unwrap-time backstop covers the non-cooperative path. This separation matches the `_django_patches.py` module docstring's two-halves framing and is consistent with the GLOSSARY contract.
- **Symbol-missing resilience inherited.** `_is_database_failure` returns `False` when `_DatabaseFailure` is `None` (Django moved/removed the private symbol), so the helper *installs* the wrapper rather than crashing the public `django_strawberry_framework.testing` import. Pinned by `::test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing`.
- **GLOSSARY accurate, no drift.** The `safe_wrap_connection_method` entry (`docs/GLOSSARY.md:1096-1115`) correctly states the return semantics (`False` = declined/untouched, `True` = installed), the `django-debug-toolbar` mirror precedent, the wrap/unwrap defense-in-depth pairing, and the auto-applied unwrap half. The availability table (`:121`) and Trac #37064 entry (`:1289-1299`) also match live source. No replacement text needed.
- **Prior-artifact CHANGELOG Low resolved.** The superseded artifact flagged `CHANGELOG.md:33` carrying the stale `django_strawberry_framework.test` import path. Live `CHANGELOG.md` now documents the rename explicitly (`CHANGELOG.md:66`, "The old `django_strawberry_framework.test` package path has been renamed") and the `### Added` entry reads "Public export from [`django_strawberry_framework.testing`][test-init]" (`CHANGELOG.md:100`). Already merged — not re-raised.

### Summary

`safe_wrap_connection_method` is a single, tightly-scoped consumer-facing helper: callable-guard, read-current, decline-if-Django-owns-it, else install-and-report. Logic is correct and side-effect-safe (guard before the only mutation; decline path mutates nothing); multi-database and thread/process behavior are sound for the documented `setUp`/`tearDown` surface; restoration is correctly delegated with the `_django_patches` unwrap backstop as the net. The shared `_is_database_failure` predicate is single-sourced (do not flag as drift per the cross-file confirmation). No High, no Medium. Three Lows are all comment/docstring tier — one act-now (the example's missing `TransactionTestCase` import is a real consumer-facing contract gap warranting a source docstring edit), two forward-looking (undocumented `AttributeError` mode; in-docstring style mix). Because the act-now Low recommends a real source edit, this is a standard cycle (`under-review`), not a no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Consolidated single-spawn (act-now Low already satisfied in source; the other two Lows are forward-looking). No source edit required this cycle.

### Files touched

- None. The act-now Low's recommended change is **already present in live source at the baseline SHA** (`0872a20`). `django_strawberry_framework/testing/_wrap.py:88` already reads `from django.test import TransactionTestCase`, inside the docstring example's import block (source 87-89), exactly as the artifact's recommended-change block (artifact lines 30-42) prescribes. `git show 0872a20:.../testing/_wrap.py` confirms the import was present at baseline — the example is already self-contained and a verbatim copy-paste resolves `TransactionTestCase`, `connections`, and `safe_wrap_connection_method`. No `NameError`. The premise of the act-now Low no longer holds; nothing to edit.

### Tests added or updated

- None. No behavior change; the example-block fix was a no-op (already merged). The existing pinning tests cited in the artifact's "What looks solid" (`tests/testing/test_wrap.py::test_safe_wrap_connection_method_raises_on_non_callable_wrapper`, `::test_safe_wrap_connection_method_declines_when_database_failure_in_place`, `::test_safe_wrap_connection_method_works_on_arbitrary_method_names`, `::test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing`) remain valid and untouched.

### Validation run

- `uv run ruff format .` — pass / no-changes (265 files left unchanged)
- `uv run ruff check --fix .` — pass / no-changes (All checks passed)
- No pytest (per AGENTS.md/START.md). `_wrap.py` is byte-identical to baseline.

### Notes for Worker 3

- Shadow file used: `docs/shadow/django_strawberry_framework__testing___wrap.overview.md` (read-only). Its line numbers do not match source; all citations above use original source line numbers.
- **Act-now Low rejected as already-satisfied (not a false premise about correctness, a stale-source premise).** Contradicting evidence: `git show 0872a20fcbecf870b3669742f108364202709e26:django_strawberry_framework/testing/_wrap.py` shows `from django.test import TransactionTestCase` at the example import block (line 88). Worker 3 can re-run that `git show` to confirm the import predates this cycle. The artifact's own recommended-change snippet (artifact lines 30-42) is identical to current source — the fix is in place.
- **Deferred Lows (both forward-looking, no edit):** (1) undocumented `AttributeError` from `getattr(connection, method_name)` with no default — trigger: next time the docstring's `Raises:` block is touched, add an `AttributeError` bullet for symmetry with the existing `TypeError` loud-failure mode. (2) in-docstring style mix (`**bold**` lead-in vs Google-style `Args:`/`Returns:`/`Raises:`) — trigger: a Sphinx/napoleon docs build lands for the `testing` subpackage; normalize to Google-style then.
- DRY `_is_database_failure` single-sourcing: confirmed correct per artifact, NOT re-flagged.

---

## Verification (Worker 3)

### Logic verification outcome

- **Act-now Low rejection verified with falsifiable contradicting evidence (all 3 false-premise gates hold).** W2 rejected Low 1 (example missing `TransactionTestCase` import) as an already-satisfied/stale-source premise, citing `git show 0872a20fcbecf870b3669742f108364202709e26:django_strawberry_framework/testing/_wrap.py`. Independently re-ran that `git show`: line 88 reads `from django.test import TransactionTestCase`, sitting in the example import block (87-89) directly above `class _MyTest(TransactionTestCase):` (92). The example is self-contained — a verbatim copy-paste resolves `connections`, `TransactionTestCase`, and `safe_wrap_connection_method` with no `NameError`. The cited line exists in source, the evidence disproves the artifact's premise, and the import predates this cycle. Rejection accepted.
- **Logic independently sanity-checked (W1 "looks solid" claims hold).** Guard-before-setattr: the `not callable(wrapper)` guard (`_wrap.py:139-142`) precedes the only `setattr` (`:146`) → a non-callable wrapper can never half-mutate the connection. Decline path side-effect-free: `_is_database_failure(current)` true → `return False` (`:144-145`) with no `setattr`, Django's wrapper untouched. Multi-DB safe: operates only on the passed `BaseDatabaseWrapper`, zero global/default-alias state. Cooperative restore: helper does only the wrap step; restoration delegated to the caller, with the `_django_patches` unwrap-time backstop as the net.
- **`_is_database_failure` single-sourcing confirmed, NOT re-flagged.** Defined once at `_django_patches.py::_is_database_failure` (`:129-131`), imported by the wrap site (`_wrap.py:27`/call `:144`) and called by the unwrap site (`_django_patches.py:173`) — one shared predicate, correct import direction (patch module ships first at `AppConfig.ready`). Matches the DRY defer.
- **4 pinning tests grep-match** in `tests/testing/test_wrap.py` (`_raises_on_non_callable_wrapper`:164, `_declines_when_database_failure_in_place`:46, `_works_on_arbitrary_method_names`:92, `_installs_when_database_failure_symbol_missing`:69).

### DRY findings disposition

- `_is_database_failure` single-sourcing: deferred-with-trigger (second `testing/`-package consumer) — confirmed correct, not re-flagged. Other 2 Lows forward-looking with triggers (AttributeError `Raises:` bullet on next docstring touch; style-mix normalize on a Sphinx build).

### Temp test verification

- None created. The decisive evidence was a `git show` at baseline + source reads; no behavior probe required (zero source change).

### Verification outcome

`cycle accepted; verified`. Shape: no-source-edit (cycle diff `git diff --stat 0872a20 -- _wrap.py` empty; `_wrap.py` byte-identical to baseline). The act-now Low's rejection holds on independent re-check of the cited `git show` (import present at baseline line 88). CHANGELOG diff empty, Not-warranted with both citations. Ruff format-check + check pass. Sets top-level `Status: verified` and marks the `testing/_wrap.py` box in `review-0_0_9.md`.

---

## Comment/docstring pass

Folded into the consolidated single-spawn. No comment/docstring edit made this cycle.

### Files touched

- None.

### Per-finding dispositions

- Low 1 (example missing `TransactionTestCase` import): **No edit — already satisfied in source.** `_wrap.py:88` carries `from django.test import TransactionTestCase` at baseline `0872a20`; the example is self-contained and runnable as-is.
- Low 2 (undocumented `AttributeError` in `Raises:`): **Deferred (forward-looking).** Per Worker 1's framing — current loud-fail behavior is correct; add the bullet when the docstring is next touched. No action now.
- Low 3 (in-docstring style mix): **Deferred (forward-looking).** Cosmetic/latent; normalize to Google-style when a Sphinx build lands for `testing`. No action now.

### Validation run

- `uv run ruff format .` — pass / no-changes (265 files left unchanged)
- `uv run ruff check --fix .` — pass / no-changes (All checks passed)

### Notes for Worker 3

The act-now Low was already resolved in live source; the only two remaining findings are explicitly forward-looking. No source or docstring lines changed in this cycle.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Zero source change this cycle (the act-now Low was already merged at baseline; the other two Lows are forward-looking with no edit). Nothing consumer-visible changed. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active review plan's silence on changelog authorization for this per-file cycle (per-file cycles are never the authorising scope and forward any CHANGELOG drift to the project pass), no edit is warranted.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass / no-changes (265 files left unchanged)
- `uv run ruff check --fix .` — pass / no-changes (All checks passed)

---

## Iteration log
