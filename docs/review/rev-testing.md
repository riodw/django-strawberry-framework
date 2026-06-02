# Review: `django_strawberry_framework/testing/` (folder pass)

Status: verified

## DRY analysis

- None — the folder hosts a single source sibling (`_wrap.py`, already verified at `rev-testing___wrap.md` with `Status: verified`) plus a docstring-only `__init__.py` (one re-export, no logic). There is no cross-file surface inside the folder against which to extract a shared helper: every cross-file consolidation candidate that touches `_wrap.py` is already enumerated at per-file scope. The single defer-with-trigger gate from the per-file artifact (`rev-testing___wrap.md` `## DRY analysis`) carries forward verbatim: a future *third* `_is_database_failure` call site in `testing/` (beyond today's one consumer at `_wrap.py:27`) would re-open the question of whether a `testing/_database_failure.py` host module would clean up the cross-folder import direction. Today the import-from-`_django_patches.py` direction is correct because `_django_patches.py` autoloads first at `AppConfig.ready` time; the wrap-time/unwrap-time symmetric pair (`_wrap.py:144` consuming `_is_database_failure`; `_django_patches.py:173` consuming the same predicate at the unwrap-time mirror site) is the entire DRY consolidation point and is already single-sourced through one import line.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_is_database_failure` is single-sourced at `django_strawberry_framework/_django_patches.py::_is_database_failure` and consumed at `django_strawberry_framework/testing/_wrap.py:27` (import) → `:144` (call). This is the entire wrap-time/unwrap-time symmetry of the package's Django Trac #37064 defense-in-depth — the wrap-time half lives here, the unwrap-time half lives in `_django_patches.py`. The folder-level audit grep confirms exactly one `_is_database_failure` import surface inside `testing/` (`grep -rn '_is_database_failure' django_strawberry_framework/testing/` returns the line-27 import and the line-144 call only).
- **New helpers considered.** A `testing/_database_failure.py` host module was evaluated at per-file scope and deferred-with-trigger — see `## DRY analysis`. No new folder-level helper candidate emerged at the folder pass: the only sibling is `__init__.py` (one re-export, zero exec-code per the shadow overview at `docs/shadow/django_strawberry_framework__testing____init__.overview.md` — "imports: 1, symbols: 0, control-flow hotspots: 0, calls of interest: 0, repeated string literals: 0"), which is too thin a surface to share a helper with.
- **Duplication risk in the current file.** None — the folder's two `.py` files contain a combined 178 source lines (149 in `_wrap.py` + 33 in `__init__.py`), one public function (`safe_wrap_connection_method`), one re-export, and one explanatory module docstring per file. Folder-pass repeated-literal grep confirms zero cross-file string-literal duplication (both shadow overviews list `repeated string literals: 0`).

### Other positives

- **Folder shape mirrors the `management/commands/` single-sibling-plus-`__init__` pattern.** Per the carry-forward from `rev-management__commands.md`, a single-sibling folder pass has no cross-file surface to grep against — no naming drift, no shared-helper candidate, no import-direction concern, no repeated literals. The right shape is shape #5 (no-source-edit cycle, skip Worker 2) with a `## DRY analysis` that names the per-file artifact's defer-with-trigger gate. This artifact does that. Do NOT speculate a folder-level helper module against a single concrete utility — that's the `START.md` "preemptively populate" anti-pattern.
- **Import-direction audit is clean.** The folder has exactly one cross-folder consumer relationship: `testing/_wrap.py:27` imports `_is_database_failure` from `django_strawberry_framework._django_patches`. The direction is correct because `_django_patches.py` autoloads at `DjangoStrawberryFrameworkConfig.ready` time before any test module can import `testing/`. No sibling reverses this direction (no file under `_django_patches.py`'s graph imports from `testing/`).
- **`__init__.py` is a thin, correctly-scoped re-export.** The file at `django_strawberry_framework/testing/__init__.py` is 33 lines: a 28-line module docstring naming today's single export plus the three forward exports tracked in `docs/GLOSSARY.md` (`TestClient` / `AsyncTestClient` / `GraphQLTestCase` at `planned for 0.0.12` status), one import line, and one `__all__`. The "subpackage exists now so consumers have a stable import path" framing at `:25-27` is the load-bearing audit trail for the `test/` → `testing/` rename — the docstring deliberately commits the package to a stable consumer-facing path even though only one utility ships today. Same calibration as the `management/commands/__init__.py` pure-docstring shape at the single-command stage.
- **Forward-looking GLOSSARY entries exist as the `__init__.py` docstring promises.** Grep against `docs/GLOSSARY.md` confirms entries for `GraphQLTestCase` (`docs/GLOSSARY.md:538-544`, `planned for 0.0.12`), `TestClient` (`docs/GLOSSARY.md:1107-1113`, `planned for 0.0.12`, body explicitly names `AsyncTestClient` as the bundled async sibling), plus the cross-referenced index entry at `docs/GLOSSARY.md:140`. The `## Currently exports` and `## Future exports` sections of `__init__.py:3-24` are honest against the documented contract.
- **GLOSSARY drift quick-check is clean at folder scope.** The per-file artifact `rev-testing___wrap.md` already verified `safe_wrap_connection_method` (`docs/GLOSSARY.md:949-968`) and `Django Trac #37064 hardening` (`docs/GLOSSARY.md:1115-1125` per the per-file artifact; current grep places the heading at `docs/GLOSSARY.md:1115`) as aligned with source behavior post-rename. The folder pass has no additional folder-level GLOSSARY symbol to audit because Django's package-discovery contract is convention-driven, not `__all__`-driven, and the folder's only consumer-visible export is the single `safe_wrap_connection_method` symbol the per-file pass already covered.
- **Both ruff runs clean.** `uv run ruff format --check django_strawberry_framework/testing/` → `2 files already formatted`. `uv run ruff check django_strawberry_framework/testing/` → `All checks passed!`. No formatter or linter drift at folder scope.
- **The per-file Low #2 forward to project pass is correctly out-of-scope here.** The `CHANGELOG.md:33` stale-`django_strawberry_framework.test`-import-path drift recorded by `rev-testing___wrap.md::Low #2` is the project pass's cross-folder rename sweep responsibility (`rev-django_strawberry_framework.md`), not the folder pass's — the folder pass cannot edit `CHANGELOG.md` per `worker-1.md` scope and would double-file the forward if it re-listed the Low here. Restated in the DRY recap only as part of the wrap-time/unwrap-time defense-in-depth audit trail.

### Summary

178-line two-file subpackage (`_wrap.py` 149 lines + `__init__.py` 33 lines) hosting a single public utility, `safe_wrap_connection_method`, the wrap-time half of the package's Django Trac #37064 defense-in-depth (unwrap-time half in `_django_patches.py`). The per-file artifact at `rev-testing___wrap.md` already closed every in-cycle finding (`Status: verified` after a consolidated single-spawn shape #4 cycle that fixed two docstring Lows in the public symbol and forwarded the `CHANGELOG.md:33` stale-path Low to the project pass). The folder pass has zero High / Medium / Low: no cross-file surface against which to file new findings, no naming drift, no shared-helper candidate, no repeated literals (both shadow overviews list `repeated string literals: 0`), no import-direction concern (single `_is_database_failure` import from `_django_patches.py` autoloads first). DRY analysis carries the per-file artifact's single defer-with-trigger bullet verbatim (a future *third* `_is_database_failure` call site in `testing/` re-opens the `testing/_database_failure.py` host-module question; today the wrap-time/unwrap-time symmetric pair is already single-sourced through the line-27 import). Both ruff commands run clean against the folder. Shape #5 (no-source-edit cycle, skip Worker 2): zero edits to any tracked file. `Status: fix-implemented`.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format --check django_strawberry_framework/testing/` — pass (`2 files already formatted`).
- `uv run ruff check django_strawberry_framework/testing/` — pass (`All checks passed!`).

### Notes for Worker 3
- Shape #5 (no-source-edit cycle, skip Worker 2). Single-sibling-plus-`__init__` folder pass with the same structural shape as `rev-management__commands.md`. The per-file artifact `rev-testing___wrap.md` already closed every finding at its own cycle (`Status: verified`); the folder pass adds no new High/Medium/Low and forwards no new Low.
- DRY-bullet trigger: a future *third* `_is_database_failure` call site in `django_strawberry_framework/testing/` (grep-resolvable via `grep -rn '_is_database_failure' django_strawberry_framework/testing/` — today returns exactly the line-27 import and the line-144 call inside `_wrap.py`) re-opens the `testing/_database_failure.py` host-module DRY question. The deferral premise holds at folder scope.
- The per-file artifact's Low #2 (`CHANGELOG.md:33` stale-`django_strawberry_framework.test`-path) is the project pass's responsibility (`rev-django_strawberry_framework.md`), not duplicated here.
- No GLOSSARY-only fix in scope at folder scope — `safe_wrap_connection_method` and `Django Trac #37064 hardening` GLOSSARY entries are already aligned per the per-file artifact's quick-check; the forward-looking entries (`GraphQLTestCase`, `TestClient`, `AsyncTestClient`) are confirmed present at `planned for 0.0.12` status as the `__init__.py` docstring promises.
- No shadow-file regeneration required at folder scope; the per-file shadow at `docs/shadow/django_strawberry_framework__testing___wrap.overview.md` is current from the per-file cycle, and I regenerated `docs/shadow/django_strawberry_framework__testing____init__.overview.md` at folder-pass time to confirm the zero-symbol, zero-exec-code shape (the shadow now records `imports: 1, symbols: 0, control-flow hotspots: 0, calls of interest: 0, repeated string literals: 0`).

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit folder pass on the two-file `testing/` subpackage. Zero High / Medium / Low at folder scope; the artifact's single DRY bullet is a verbatim forward of the per-file `rev-testing___wrap.md::DRY analysis` defer-with-trigger gate (future *third* `_is_database_failure` call site in `testing/` re-opens the `testing/_database_failure.py` host-module question). Verified the deferral premise still holds: `grep -rn '_is_database_failure' django_strawberry_framework/testing/` returns exactly the line-27 import and the line-144 call inside `_wrap.py`, matching the artifact's claim verbatim. Per-file sibling artifact is `Status: verified` on disk with checkbox `[x]` at `review-0_0_7.md:81`.

### DRY findings disposition
Single DRY bullet carried forward verbatim from the per-file artifact; deferral premise re-confirmed at folder scope (one consumer relationship, one import direction, single source of truth in `_django_patches.py::_is_database_failure`). No new folder-level DRY candidate emerged because `__init__.py` is a zero-symbol re-export per the shadow overview at `docs/shadow/django_strawberry_framework__testing____init__.overview.md` (imports: 1, symbols: 0, control-flow hotspots: 0, calls of interest: 0, repeated string literals: 0) — too thin a surface to share a helper with.

### Temp test verification
- No temp tests required — shape #5 no-source-edit cycle with zero High/Medium/Low and no behavioral claims to spot-pin.

### Shape #5 gate confirmations
1. **Diff scope.** `git diff --stat HEAD -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` is NOT empty (19 files / 3360 insertions / 249 deletions), but every hunk attributes to a closed sibling cycle: `testing/_wrap.py` (+4/-6) is the per-file sibling `rev-testing___wrap.md`'s `Status: verified` edit (Low #1 `TransactionTestCase` import added at the `.. code-block:: python` import block + Low #3 `Restoration semantics` `---`-underline collapse to inline `**Restoration semantics.**`), confirmed char-for-char against `git diff HEAD -- django_strawberry_framework/testing/_wrap.py`. Remaining hunks (`optimizer/*.py`, `optimizer/test_walker.py`, `management/commands/export_schema.py`, `docs/GLOSSARY.md`) all attribute to closed sibling cycles per worker-3 memory entries (extension, hints, plans, walker, field_meta, _context, export_schema all `Status: verified` with `[x]`-marked checkboxes); `orders/*` hunks are out-of-scope concurrent maintainer work per AGENTS.md rule 33 (no review artifact yet on `orders/`). The folder pass's own "Files touched: None" claim holds — same dirty-tree-from-verified-sibling attribution pattern recorded at `management/commands/` and `management/` and `optimizer/` folder passes.
2. **Worker 2 sections boilerplate.** All three sections (`## Fix report (Worker 2)`, `## Comment/docstring pass`, `## Changelog disposition`) open with `Filled by Worker 1 per no-source-edit cycle pattern.` verbatim.
3. **No GLOSSARY-only fixes done here.** Zero in-cycle edits at folder scope (`Files touched: None`). The GLOSSARY hunks in the dirty tree attribute to closed sibling cycles, not this folder pass.
4. **Changelog `Not warranted` + both citations.** `git diff -- CHANGELOG.md` shows no hunks attributable to this cycle (the `CHANGELOG.md:33` stale-path Low is the project-pass forward from `rev-testing___wrap.md::Low #2`, explicitly out of scope here). Disposition cites BOTH `AGENTS.md` #21 ("Do not update `CHANGELOG.md` unless explicitly instructed") AND active-plan silence at `docs/review/review-0_0_7.md`.
5. **Ruff plausible.** `uv run ruff format --check django_strawberry_framework/testing/` → `2 files already formatted`; `uv run ruff check django_strawberry_framework/testing/` → `All checks passed!`.

### Verification outcome
cycle accepted; verified

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No source/docstring edits at folder scope. The per-file artifact `rev-testing___wrap.md` already applied the two in-cycle docstring Lows (`TransactionTestCase` import addition and `Restoration semantics` RST-underline normalization) on `_wrap.py` and verified them clean; `__init__.py`'s module docstring at `django_strawberry_framework/testing/__init__.py:1-28` is current against the documented contract (today's single export plus the three planned-for-0.0.12 forward exports cross-referenced in `docs/GLOSSARY.md:538`, `:1107`, `:1111`).

### Validation run
- `uv run ruff format --check django_strawberry_framework/testing/` — pass (`2 files already formatted`).
- `uv run ruff check django_strawberry_framework/testing/` — pass (`All checks passed!`).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

### State
`Not warranted`

### Reason
No-source-edit folder pass over a two-file subpackage whose only source sibling is already `Status: verified` at `rev-testing___wrap.md`. Zero edits to any tracked file (source, tests, GLOSSARY, CHANGELOG, anything). Falls squarely under `worker-2.md`'s "Not warranted" calibration for folder-pass cycles that introduce no behavior change. Cites both halves: (a) `AGENTS.md` #21 ("Do not update `CHANGELOG.md` unless explicitly instructed"), and (b) the active plan (`docs/review/review-0_0_7.md`) is silent on changelog authorization for this cycle. Mirrors the prior `rev-management__commands.md` folder-pass disposition — same shape (single sibling + `__init__.py`), same Not-warranted framing.

### What was done
No `CHANGELOG.md` edit. The per-file artifact's forwarded `CHANGELOG.md:33` stale-path Low remains the project pass's responsibility per `rev-testing___wrap.md::Low #2`.

### Validation run
- `uv run ruff format --check django_strawberry_framework/testing/` — pass (`2 files already formatted`).
- `uv run ruff check django_strawberry_framework/testing/` — pass (`All checks passed!`).

---

## Iteration log

_
