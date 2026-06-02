# Review: `django_strawberry_framework/testing/_wrap.py`

Status: verified

## DRY analysis

- Defer until a second consumer-facing helper in `django_strawberry_framework/testing/` exposes the `_DatabaseFailure` predicate. Today, `_wrap.py:27` imports `_is_database_failure` from `_django_patches.py` directly (which itself is the canonical predicate per `_django_patches.py::_is_database_failure` at lines 129-131); the symmetry of "wrap site uses `_is_database_failure(current)`" (`_wrap.py:146`) and "unwrap site uses `_is_database_failure(method)`" (`_django_patches.py:173`) is the entire DRY consolidation point and is already correctly single-sourced. Trigger: if a future `testing/` helper grows a third `_is_database_failure` call site (e.g., a `safe_unwrap_connection_method` companion, or a `GraphQLTestCase` fixture), evaluate whether a `testing/_database_failure.py` module hosting the predicate (with `_django_patches.py` re-importing it) cleans up the cross-folder import direction — today the import-from-`_django_patches.py` direction is correct because `_django_patches.py` ships first (autoloaded at `AppConfig.ready`).

## High:

None.

## Medium:

None.

## Low:

### Docstring example `class _MyTest(TransactionTestCase):` references `TransactionTestCase` without showing the import

The runnable `.. code-block:: python` snippet at `_wrap.py:88-110` opens with `class _MyTest(TransactionTestCase):` (`_wrap.py:94`) but the surrounding example only imports `connections` and `safe_wrap_connection_method` (`_wrap.py:90-91`). A consumer copy-pasting the block verbatim hits `NameError: name 'TransactionTestCase' is not defined` at the class statement. Same calibration applies to the implicit `self.assertEqual` / Django TestCase machinery the example doesn't show.

Why it matters: this helper is consumer-facing (`from django_strawberry_framework.testing import safe_wrap_connection_method` per `testing/__init__.py:30`), and the docstring is the published consumer contract — the example block is part of that contract. Same severity as the `list_field.py` / `scalars.py` citation-hygiene Lows: the surrounding prose is correct, only the executable example is incomplete.

Recommended change: add `from django.test import TransactionTestCase` to the example's import block (alongside the existing `from django.db import connections` and `from django_strawberry_framework.testing import safe_wrap_connection_method` lines).

```django_strawberry_framework/testing/_wrap.py:88:110
    .. code-block:: python

        from django.db import connections
        from django_strawberry_framework.testing import safe_wrap_connection_method


        class _MyTest(TransactionTestCase):
            def setUp(self):
                super().setUp()
                self._connection = connections["default"]
                self._original_cursor = self._connection.cursor

                def my_wrapped_cursor(*args, **kwargs):
                    return self._original_cursor(*args, **kwargs)

                self._wrapped = safe_wrap_connection_method(
                    self._connection, "cursor", my_wrapped_cursor,
                )
```

### `CHANGELOG.md:33` references the stale `django_strawberry_framework.test` import path (now `django_strawberry_framework.testing`) — forwarded to project pass

The `CHANGELOG.md` `### Added` entry for `safe_wrap_connection_method` at `CHANGELOG.md:33` reads "Public export from `django_strawberry_framework.test`", but the maintainer-named rename moved the subpackage from `test/` to `testing/` (per the dispatch). The current public import path is `django_strawberry_framework.testing` (`testing/__init__.py:30`, `_wrap.py:91` example, `tests/testing/test_wrap.py:19`). The GLOSSARY entries (`docs/GLOSSARY.md:957`, `:961`) and the source docstrings (`testing/__init__.py:26`, `_wrap.py:91`) all show the corrected `testing` path; only the CHANGELOG `Added` line lags.

Why it matters: CHANGELOG is consumer-facing release notes; a stale import path on a `### Added` line is the first place a consumer reads to confirm the export. Same Low severity as the `spec-016 → spec-020` drift (`list_field.py`) and `TODO-ALPHA-028 → TODO-ALPHA-035` drift (`scalars.py`) — citation hygiene, not logic.

Worker 1 cannot modify `CHANGELOG.md` per `worker-1.md` scope. Forwarded to the project pass (`rev-django_strawberry_framework.md`) for the cross-folder rename sweep — `CHANGELOG.md:33` plus any other surfaces grep finds for the old `django_strawberry_framework.test` path. Recommended replacement: rewrite the parenthetical to "Public export from [`django_strawberry_framework.testing`][test-init]" and update the `[test-init]` link def to `django_strawberry_framework/testing/__init__.py` if it still resolves to the old `test/__init__.py` path.

### Docstring "Restoration semantics" heading uses RST `---` underline but the rest of the docstring is bare paragraph prose — minor RST-rendering inconsistency

`_wrap.py:81-83` introduces a `Restoration semantics` heading with RST-style `---` underline (`_wrap.py:82`), but the rest of the 105-line docstring uses bare paragraph prose with `*` italics / `**` bolds (`_wrap.py:67-71`) and Google-style `Args:` / `Returns:` / `Raises:` sections (`_wrap.py:118-140`). Sphinx will render the `Restoration semantics` block as an H2 heading while the rest of the docstring renders as flowing prose — a tonal mismatch within a single docstring.

Why it matters: same severity as the `filters/base.py` backtick-convention drift Low — pick one convention per docstring; the mixed render is the smell. Today the docstring is read via `help(safe_wrap_connection_method)` more than via Sphinx, so the render mismatch is latent.

Recommended change: replace the `---` underline at `_wrap.py:82` with bare paragraph emphasis (`**Restoration semantics.**`) or move the entire section's prose under a Google-style `Notes:` block to match the existing `Args:` / `Returns:` / `Raises:` shape. Defer until the package's first Sphinx-published docs build surfaces the inconsistency.

## What looks solid

### DRY recap

- **Existing patterns reused.** The `_is_database_failure` predicate (`_django_patches.py:129-131`) is the single source of truth for the `isinstance(method, _DatabaseFailure)` check; both the wrap-site (`_wrap.py:146`) and the unwrap-site (`_django_patches.py:173`) consume it. The two-halves-of-defense-in-depth framing (wrap-time `_wrap.py` + unwrap-time `_django_patches.py`) is documented identically in both modules' docstrings and the GLOSSARY's `safe_wrap_connection_method` (`docs/GLOSSARY.md:949-968`) and `Django Trac #37064 hardening` (`docs/GLOSSARY.md:1115-1125`) entries cross-reference each other correctly.
- **New helpers considered.** A `_DatabaseFailure`-predicate-hosting `testing/_database_failure.py` module was evaluated and deferred — see `## DRY analysis` for the trigger condition. The current import direction (`_wrap.py` consumes from `_django_patches.py`) is correct because `_django_patches.py` ships first at `AppConfig.ready` time.
- **Duplication risk in the current file.** None — the file is 149 lines with a single public function (`safe_wrap_connection_method`), one runtime guard (`callable(wrapper)`), one predicate call (`_is_database_failure(current)`), and one mutation (`setattr(connection, method_name, wrapper)`). Zero repeated literals per shadow overview at `docs/shadow/django_strawberry_framework__testing___wrap.overview.md:17`.

### Other positives

- **Test coverage.** Six tests at `tests/testing/test_wrap.py` pin every branch: happy-path install (`:28-43`), declines-when-`_DatabaseFailure` (`:46-66`), private-symbol-missing graceful path (`:69-89`), arbitrary method name (`:92-112`), end-to-end composition with the unwrap-time patch (`:115-161`), and the `TypeError` early-validate guard (`:164-187`). The composition test (`:115-161`) is the load-bearing pin — it proves the two halves of the defense-in-depth actually compose and that the `safe_wrap_connection_method`-declines / `_remove_databases_failures`-unwraps sequence restores the sentinel original cleanly.
- **TypeError-at-wrap-site early validation.** The `if not callable(wrapper): raise TypeError(...)` guard at `_wrap.py:141-144` surfaces a non-callable typo at the wrap site rather than as a delayed `TypeError` deep inside Django's ORM at the next `connection.<method>()` call — the docstring's `Raises:` section (`_wrap.py:134-139`) makes the failure-mode promise consumer-facing and `tests/testing/test_wrap.py:164-187` pins it. Same defensive shape as the `_django_patches.py::apply` symbol-missing branch.
- **No mutation before validation.** The two-step "validate wrapper is callable → check current `_DatabaseFailure` state → setattr" sequence at `_wrap.py:141-149` is the correct atomic ordering: the `TypeError` raise (line 142) and the `_is_database_failure` early-return (line 146-147) both happen before the `setattr` mutation (line 148). `tests/testing/test_wrap.py:185` pins the "connection method untouched on TypeError" property.
- **GLOSSARY drift quick-check is clean.** Both `safe_wrap_connection_method` (`docs/GLOSSARY.md:949-968`) and `Django Trac #37064 hardening` (`docs/GLOSSARY.md:1115-1125`) entries are aligned with the source: cooperative wrap-time check, `False` return on `_DatabaseFailure` already in place, `True` return otherwise, mirror to `django-debug-toolbar`'s `wrap_cursor`, defense-in-depth framing, status `shipped (0.0.7)`. The `### Cross-cutting infrastructure` index (`docs/GLOSSARY.md:38`) and the testing category index (`docs/GLOSSARY.md:140`) both link to the entry correctly. No in-cycle GLOSSARY edit warranted.
- **Subpackage rename audit-trail.** The `testing/__init__.py:25-27` "subpackage exists now so consumers have a stable import path" framing is the load-bearing audit trail for the `test/` → `testing/` rename — the docstring deliberately commits the package to a stable consumer-facing path even though only one utility ships today. The `_wrap.py:91` example, `tests/testing/test_wrap.py:19` import, and GLOSSARY snippet (`docs/GLOSSARY.md:957`, `:961`) all use the corrected `testing` path consistently.

### Summary

149-line single-function module hosting `safe_wrap_connection_method`, the wrap-time half of the package's Django Trac #37064 defense-in-depth (the unwrap-time half lives in `_django_patches.py`). Zero High / Medium; three Lows all comment/docstring-pass: (a) the `.. code-block:: python` example references `TransactionTestCase` without showing its import — consumers copy-pasting hit `NameError`; (b) `CHANGELOG.md:33`'s `### Added` line still cites the old `django_strawberry_framework.test` import path post-rename to `django_strawberry_framework.testing` — forwarded to project pass since Worker 1 cannot edit CHANGELOG; (c) one RST `---`-underlined heading inside an otherwise bare-paragraph docstring is a minor render-mismatch latent until Sphinx publishes. The `_is_database_failure` predicate single-sourcing across `_wrap.py:146` and `_django_patches.py:173` is the correct DRY shape; the `## DRY analysis` records the defer-with-trigger gate for a future third call site. Test coverage at `tests/testing/test_wrap.py:1-187` is comprehensive — the end-to-end composition test (`:115-161`) is the load-bearing proof that the two halves of defense-in-depth compose. Standard three-spawn cycle: Lows require source edits at comment-pass time. `Status: under-review`.

---

## Fix report (Worker 2)

### Files touched
- `django_strawberry_framework/testing/_wrap.py` — applied both in-cycle Lows in the single `safe_wrap_connection_method` docstring. Low #1: added `from django.test import TransactionTestCase` to the `.. code-block:: python` example's import block (between `from django.db import connections` and `from django_strawberry_framework.testing import safe_wrap_connection_method`) so a verbatim copy-paste no longer hits `NameError: name 'TransactionTestCase' is not defined` at the `class _MyTest(TransactionTestCase):` line. Low #3: collapsed the `Restoration semantics` RST-underlined heading (`---` underline) into a bare-paragraph `**Restoration semantics.**` bold lead-in inline with the prose, matching the rest of the docstring's bare-paragraph + `**bold**`/`*italic*` + Google-style `Args:`/`Returns:`/`Raises:` convention (per the artifact's first recommended alternative). Both edits are docstring-only — no logic change to the public `safe_wrap_connection_method` symbol.

### Tests added or updated
- None. Both Lows are docstring polish; no behavior changes. Existing pinning tests at `tests/testing/test_wrap.py` (six tests, lines 28-187 per the artifact's `## What looks solid` enumeration) already pin every branch of the wrap-time logic; nothing in the docstring touch changes the surface they cover.

### Validation run
- `uv run ruff format .` — pass (213 files left unchanged)
- `uv run ruff check --fix .` — pass (All checks passed!)

### Notes for Worker 3
- Consolidated single-spawn shape per dispatch (all three Lows fit the shape: two trivially-localised docstring edits in the same `safe_wrap_connection_method` docstring + one forwarded). Logic + comment + changelog disposition recorded in one pass.
- Low #2 (`CHANGELOG.md:33` stale `django_strawberry_framework.test` import path) **forwarded to project pass** per artifact instruction (Worker 1 cannot modify `CHANGELOG.md` per `worker-1.md` scope; Worker 2 dispatch prompt also explicitly excludes CHANGELOG edits this cycle). Project pass artifact (`rev-django_strawberry_framework.md`) should sweep the cross-folder `test/` → `testing/` rename: at minimum `CHANGELOG.md:33` per the artifact; recommend grep for the full string `django_strawberry_framework.test` (no trailing dot or `ing`) to catch any other lagging surfaces.
- Low #3 convention choice: I picked the **inline `**Restoration semantics.**` bold-paragraph** alternative over the `Notes:` Google-style block because (a) the code-block-with-prose-around-it shape doesn't fit cleanly under a single `Notes:` heading (the prose continues after the code-block with the "package's unwrap-time backstop" paragraph), (b) the inline bold matches the existing `**Wrap time**` / `**Unwrap time**` bullets at `_wrap.py:66-71` so the docstring now has one consistent emphasis convention, and (c) it preserves the prose-flow ordering (semantics paragraph → code-block → consequence paragraph → Args/Returns/Raises) without forcing a section break.
- No shadow file used; the source is 149 lines and reads straight.
- `uv.lock` unchanged. Other repo-dirty paths (`TODAY.md`, multiple `optimizer/*.py`, `orders/*.py`, `docs/GLOSSARY.md`, sibling `rev-*.md` artifacts) are out-of-scope concurrent maintainer/sibling-cycle work per AGENTS.md #33 and were not touched.

---

## Verification (Worker 3)

### Logic verification outcome
Consolidated single-spawn (shape #4) cycle on a 149-line single-public-function testing helper. Two in-cycle Lows applied as docstring-only edits in `safe_wrap_connection_method`:

- **Low #1 (TransactionTestCase import).** Diff adds `from django.test import TransactionTestCase` between the two existing import lines in the `.. code-block:: python` example (`_wrap.py:88`). A consumer copy-pasting the block verbatim no longer hits `NameError: name 'TransactionTestCase' is not defined` at `class _MyTest(TransactionTestCase):` (`_wrap.py:92`). The import was inserted at the position the artifact's recommended replacement names (alongside the existing `from django.db import connections` and `from django_strawberry_framework.testing import safe_wrap_connection_method`).
- **Low #3 (RST convention normalization).** Diff collapses the two-line `Restoration semantics` heading with `---` underline (formerly `_wrap.py:81-82`) into an inline `**Restoration semantics.** This helper handles only the wrap step.` bold lead-in (`_wrap.py:81-83`). The new convention now matches the existing `**Wrap time**` / `**Unwrap time**` inline-bold bullets at `_wrap.py:66-71` and leaves the docstring with one consistent emphasis convention plus the pre-existing Google-style `Args:` / `Returns:` / `Raises:` blocks at `_wrap.py:116-138`. Worker 2's "inline bold over `Notes:` block" rationale (Notes-for-Worker-3) is correct — the `Notes:` form would have forced a section break between the prose and the code-block-with-trailing-paragraph shape.
- **Low #2 (CHANGELOG.md:33 stale path).** Forwarded to project pass (`rev-django_strawberry_framework.md`) per the artifact's own instruction and `worker-1.md` scope. Worker 2 explicitly defers this Low and does not edit `CHANGELOG.md`. `git diff -- CHANGELOG.md` is empty, confirming the forward.

Spot-verified positive claims in `## What looks solid`: `_is_database_failure(current)` predicate consumed at `_wrap.py:144` (Worker 1 cited :146 pre-edit; the docstring net contracted by 2 lines under the Low #3 collapse), `TypeError` early-validate guard at `_wrap.py:139-142` (Worker 1 cited :141-144), `setattr` mutation at `_wrap.py:146` (Worker 1 cited :148). All three sequence-ordering claims hold post-edit modulo the same -2 line shift introduced by the docstring collapse. The `_DatabaseFailure` single-source-of-truth import at `_wrap.py:27` (consuming the canonical predicate from `_django_patches.py::_is_database_failure`) is untouched.

### DRY findings disposition
`## DRY analysis` records a defer-with-trigger gate: a future third `_is_database_failure` call site in `testing/` (e.g., a `safe_unwrap_connection_method` companion or a `GraphQLTestCase` fixture) would re-open the question of whether a `testing/_database_failure.py` host module would clean up the cross-folder import direction. Today the import-from-`_django_patches.py` direction is correct because `_django_patches.py` autoloads first at `AppConfig.ready` time. The trigger is grep-resolvable (`grep -rn "_is_database_failure" django_strawberry_framework/testing/` → exactly one consumer site at `_wrap.py:27`) and the deferral premise holds.

### Temp test verification
None used. The artifact's enumerated existing pinning tests at `tests/testing/test_wrap.py:28-187` (six tests covering happy-path install, `_DatabaseFailure` decline, private-symbol-missing graceful path, arbitrary method name, end-to-end composition with the unwrap-time patch, and the `TypeError` early-validate guard) are sufficient — the docstring-only edits change zero observable behavior at the public surface so no new test is warranted.

### Verification outcome
`cycle accepted; verified`. Top-level `Status:` flipped to `verified`. Checklist box at `docs/review/review-0_0_7.md:81` marked `[x]`.

Changelog disposition (`Not warranted`) verified clean: cites BOTH (a) `AGENTS.md` #21 ("Do not update `CHANGELOG.md` unless explicitly instructed") and (b) active plan silence at `docs/review/review-0_0_7.md` (dispatch prompt itself pre-named the disposition as "`Not warranted` (internal docstring polish) citing AGENTS.md + active plan silence" — matches). `git diff -- CHANGELOG.md` empty. Internal-only framing is honest — the `safe_wrap_connection_method(connection, method_name, wrapper) -> bool` public contract is bit-for-bit identical pre- and post-edit (same parameters, same return type, same `_DatabaseFailure` decline branch, same `TypeError` early-validate guard, same `setattr` mutation).

Ruff outcomes spot-verified on the touched file: `uv run ruff format --check django_strawberry_framework/testing/_wrap.py` → `1 file already formatted`; `uv run ruff check django_strawberry_framework/testing/_wrap.py` → `All checks passed!`.

---

## Comment/docstring pass

Folded into the consolidated single-spawn above (see `## Fix report (Worker 2)`). Per-finding dispositions:

- Low #1 (docstring example missing `TransactionTestCase` import): **applied** — added `from django.test import TransactionTestCase` to the example's import block.
- Low #2 (`CHANGELOG.md:33` stale `django_strawberry_framework.test` path): **forwarded to project pass** — Worker 2 dispatch prompt explicitly defers this Low to the cross-folder rename sweep handled by `rev-django_strawberry_framework.md`.
- Low #3 (mixed RST-underline vs bare-paragraph convention): **applied** — replaced `Restoration semantics\n---------------------` underlined heading with inline `**Restoration semantics.**` bold lead-in to match the docstring's pre-existing bare-paragraph + `**bold**` + Google-style `Args:`/`Returns:`/`Raises:` convention.

### Validation run
- `uv run ruff format .` — pass (213 files left unchanged)
- `uv run ruff check --fix .` — pass

---

## Changelog disposition

### State
`Not warranted`

### Reason
Cycle's edits are docstring-only polish on a single public symbol (`safe_wrap_connection_method`): adding a missing import line inside a `.. code-block:: python` example so verbatim copy-paste runs, and normalizing one RST-underlined sub-heading into the docstring's pre-existing bare-paragraph + inline-bold convention. No behavior change at the public surface; the `safe_wrap_connection_method(connection, method_name, wrapper) -> bool` contract, the `_DatabaseFailure` decline branch, the `TypeError` early-validate guard, and the `setattr` mutation are all bit-for-bit identical pre- and post-edit. Falls squarely under `worker-2.md`'s "Not warranted" calibration — "docstring polish… semantically equivalent simplifications". Cites both halves: (a) `AGENTS.md` #21 ("Do not update `CHANGELOG.md` unless explicitly instructed"), and (b) the active plan (`docs/review/review-0_0_7.md`) is silent on changelog authorization for this cycle (the dispatch prompt itself names changelog as "`Not warranted` (internal docstring polish) citing AGENTS.md + active plan silence" — matches). Comparable severity to prior cycles' `Not warranted` calibrations: `list_field.py` four citation/docstring Lows, `scalars.py` TODO-anchor rotation + symmetry-claim tighten, `optimizer/walker.py` private-helper validator hoist with preserved public contract.

### What was done
No `CHANGELOG.md` edit. Low #2's CHANGELOG.md:33 stale-path drift is forwarded to the project pass (`rev-django_strawberry_framework.md`) per the artifact and the dispatch prompt; that future cross-folder sweep will record its own changelog disposition.

### Validation run
- `uv run ruff format .` — pass (213 files left unchanged)
- `uv run ruff check --fix .` — pass

---

## Iteration log

_
