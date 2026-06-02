# Review: `django_strawberry_framework/management/commands/export_schema.py`

Status: verified

## DRY analysis

- None — the module is a 55-line `BaseCommand` with one positional + one optional flag and three exclusive branches (stdout / empty-rejection / file-write). Each `CommandError` raise carries a bespoke message (import failure, type guard, empty-`--path` guard, OSError wrap) and a bespoke `from e` chain; folding the two `except → CommandError(str(e)) from e` arms (`export_schema.py:38-39` and `export_schema.py:53-54`) through a shared helper would obscure that they catch deliberately different exception families across deliberately different call sites (`import_module_symbol` vs `Path.write_text`), and the schema-symbol resolve has to precede `print_schema` before the file write is even attempted. No third callsite exists or is in scope through `0.0.7`; revisit only if a sibling management command (or a `--watch` follow-up — deferred to a future card per the GLOSSARY "no `--watch` / `--indent` / JSON mode / settings-backed defaults in `0.0.7`" line) lands a third `import-then-validate-then-emit` triplet.

## High:

None.

## Medium:

### GLOSSARY entry for the Schema export management command lags the four `0.0.7` polish/fix entries

`docs/GLOSSARY.md:1007-1013` says the command "ships `Command(BaseCommand)` with positional `schema` (dotted path, default symbol name `"schema"`) and optional `--path`; SDL output via `strawberry.printer.print_schema`; `CommandError` for unimportable dotted path, non-`strawberry.Schema` resolved symbol, and missing positional argument; no `--watch` / `--indent` / JSON mode / settings-backed defaults in `0.0.7`." That description is the **`Added` entry** language verbatim from `CHANGELOG.md:34`, but four `0.0.7` polish/fix entries that shipped after the Added line are not reflected in the GLOSSARY entry:

- `CHANGELOG.md:41` (`Changed`) — `--path <file>` now emits `Wrote schema to <file>` to `self.stdout` via `self.style.SUCCESS` after a successful write (pinned at `export_schema.py:55`).
- `CHANGELOG.md:42` (`Changed`) — positional `schema` is a single scalar (no `nargs=1` magic-number indexing).
- `CHANGELOG.md:43` (`Changed`) — `--path` requires a value (bare `--path` raises `CommandError` at argparse time; pinned at `export_schema.py:19-23` + `tests/management/test_export_schema.py:76-79`).
- `CHANGELOG.md:61` (`Fixed`) — `--path <file>` wraps `OSError` (missing parent dir, permission denied, target-is-a-directory) in `CommandError` (pinned at `export_schema.py:51-54` + `tests/management/test_export_schema.py:64-73`).

Beyond those four, the GLOSSARY entry also omits the **explicit empty-`--path` guard** (`export_schema.py:49-50` raises `CommandError("--path requires a non-empty value")`; pinned at `tests/management/test_export_schema.py:82-85`). That guard is consumer-visible — empty-string `--path` is the obvious typo class the guard exists to catch — and the GLOSSARY summary is the only place outside the changelog where a consumer reads "what does `--path` do".

Why Medium not Low: this is a documented public-contract symbol (the GLOSSARY entry is the published consumer contract per the worker-1.md "GLOSSARY drift quick-check" rule), and the drift covers five real consumer-facing behaviours, three of which produce or wrap `CommandError` shapes that consumers can catch and key against. Same calibration as the per-file rule: "Stale prose on a documented public-contract symbol → Medium."

Recommended replacement prose for `docs/GLOSSARY.md:1011` (preserve verbatim for Worker 2 lift; keep the surrounding `**Status:**` line and `**See also:**` cross-ref intact):

```
`django_strawberry_framework/management/commands/export_schema.py` ships `Command(BaseCommand)` with positional `schema` (dotted path, default symbol name `"schema"`) and optional `--path`; SDL output via `strawberry.printer.print_schema`. `--path` omitted writes SDL to `self.stdout`; `--path <file>` writes UTF-8 SDL to the named path and reports `Wrote schema to <file>` via `self.style.SUCCESS`. `CommandError` for unimportable dotted path, non-`strawberry.Schema` resolved symbol, missing positional argument, bare `--path` with no value, empty-string `--path`, and file-write `OSError` (missing parent directory, permission denied, target is a directory). No `--watch` / `--indent` / JSON mode / settings-backed defaults in `0.0.7`.
```

## Low:

### Idiosyncratic `CHANGELOG-23` citation in `handle()` docstring is a rotted line-number reference

`export_schema.py:30` reads `per the CHANGELOG-23 "requires a value when the flag is given" contract`. The `CHANGELOG-23` token does not match any repo-wide convention — a grep across `django_strawberry_framework/` returns this single hit. The actual entry the docstring quotes lives at `CHANGELOG.md:43` today (the `--path` `nargs="?"` removal `Changed` entry); the `23` was presumably the changelog's line number at authoring time. Any `[Unreleased]` `### Added` entry that lands ahead of the `0.0.7` section will push the cited entry down by N lines and re-rot the reference.

Recommended fix at comment-pass time: replace the rotted line-number citation with a stable anchor. Two acceptable shapes:

- Quote the entry by its `CHANGELOG.md` heading + the verbatim entry-prefix substring the docstring already uses (the actual citation convention used elsewhere in the package per `AGENTS.md` rule 27): `per the CHANGELOG.md "[0.0.7] Changed — manage.py export_schema --path now requires a value when the flag is given" contract`.
- Or drop the cross-reference entirely and rely on the test name `test_export_schema_raises_command_error_when_path_flag_is_empty_string` (`tests/management/test_export_schema.py:82-85`) plus the guard at `export_schema.py:49-50` as the on-disk audit trail. The contract is small enough that the docstring's three-clause prose ("`--path` omitted prints SDL to stdout; `--path ""` ... raises `CommandError`; `--path <file>` writes UTF-8 SDL to the named path") already documents itself without the cross-file pointer.

Severity is Low (citation hygiene, comment-pass) per the worker-1 calibration carried forward from `list_field.py` / `scalars.py` / `sets_mixins.py` — the policy text the citation supports is still correct against the actual `CHANGELOG.md` entry today; only the pointer rotted. Not Medium because the behavior under the citation is correctly implemented and tested.

### `handle(self, *args, **options)` signature accepts but ignores `*args`

`export_schema.py:25` declares `def handle(self, *args: object, **options: object) -> None:` and the body never reads `args`. Django's `BaseCommand.handle` is the standard hook signature, so `*args, **options` is the canonical shape — but `*args` is only meaningful for commands declaring positional `nargs` collectors, which this command does not (the positional `schema` is a single scalar per `CHANGELOG.md:42`'s post-ship polish). The current shape is harmless and matches Django's documented `BaseCommand` override pattern, so this is a Low only — not a finding to act on today, but worth noting if the package ever standardizes management-command signatures across a sibling card.

Defer-with-trigger: revisit when a **second** management command lands in `django_strawberry_framework/management/commands/` and either commits to `*args` (collecting nargs positionals) or drops it. At that point pick one convention (likely `def handle(self, **options: object) -> None:` since neither command today reads `args`) and apply it package-wide. Until then, the canonical Django-documented shape wins.

## What looks solid

### DRY recap

- **Existing patterns reused.** `import_module_symbol(default_symbol_name="schema")` reuses Strawberry's first-party importer (`export_schema.py:34-37`) rather than re-implementing a dotted-path splitter; `strawberry.printer.print_schema` reuses Strawberry's SDL serializer rather than re-walking the schema (`export_schema.py:44`); `self.style.SUCCESS(...)` reuses Django's terminal-styling pipeline (`export_schema.py:55`) instead of `print(...)`. The `from e` chain on both `CommandError` raises (`export_schema.py:39` and `export_schema.py:54`) preserves the original traceback per Django's documented `CommandError` convention.
- **New helpers considered.** The two `except → CommandError(str(e)) from e` arms (`export_schema.py:33-39` and `export_schema.py:51-54`) were considered for folding through a shared `_raise_command_error_from(e)` helper and rejected — the exception families (`ImportError | AttributeError` vs. `OSError`) are deliberately disjoint and the call sites are deliberately separated by the type guard and the `print_schema` evaluation. Folding through a shared helper would obscure the staged shape ("resolve symbol → guard type → render SDL → emit") that the body intentionally makes linear. The `--path is None / not path / else` ladder (`export_schema.py:45-55`) was considered for collapsing through a single `_emit(schema_output, path)` helper and rejected — the three branches share no common epilogue, and the `if not path: raise` guard cannot fold into a single boolean against `path is None` without losing the explicit empty-string-vs-None distinction the test suite pins (`tests/management/test_export_schema.py:76-85`).
- **Duplication risk in the current file.** None — the file's three `CommandError(...)` constructors carry three distinct, deliberately non-shared messages (`"The schema must be an instance of strawberry.Schema"` at `export_schema.py:42`; `"--path requires a non-empty value"` at `export_schema.py:50`; the `str(e)` shapes at `export_schema.py:39` and `export_schema.py:54`). No repeated literal across the file (shadow `Repeated string literals: 0`).

### Other positives

- **Defensive layering on `--path`.** Three distinct guards for three distinct typo classes: argparse rejects bare `--path` at parse time (no `nargs="?"`); the body guard at `export_schema.py:49-50` rejects empty-string `--path`; the `OSError` wrap at `export_schema.py:51-54` rejects unwritable paths. Each maps to its own `CommandError` shape and its own pinned test.
- **Test discipline (split across two trees).** Package-internal failure-mode pins live in `tests/management/test_export_schema.py` (seven tests covering the unimportable-module, missing-attribute, non-`Schema`-symbol, missing-positional, missing-parent-dir, bare-`--path`, and empty-string-`--path` arms; module-synthesis via `monkeypatch.setitem(sys.modules, "test_module", module)` so pytest teardown clears `sys.modules` per the rev3 L4 cleanup contract called out in the test header docstring). Success-path coverage lives at `examples/fakeshop/tests/test_export_schema.py:8-28` (live `call_command("export_schema", "config.schema:schema", stdout=out)` against the real fakeshop schema for the stdout branch, and `--path <tmp_path>` against the real schema for the file-write branch including the `Wrote schema to <file>` success-message assertion). The split honors the `AGENTS.md` real-usage rule: each branch reachable through `call_command` is earned via the fakeshop example, not mocked.
- **Single-source SDL.** `schema_output = print_schema(schema_symbol)` (`export_schema.py:44`) is computed once before the branch ladder, so the stdout and file-write branches emit byte-identical SDL. If `--path` ever grew a `--check` mode (`BACKLOG`-shaped follow-up) the comparison would be trivial because the source-of-truth string already exists pre-branch.
- **Symbol resolution failure-mode envelope.** `except (ImportError, AttributeError)` at `export_schema.py:38` matches `strawberry.utils.importer.import_module_symbol`'s actual raise surface (the helper raises `ImportError` for unimportable modules and `AttributeError` for missing attributes); the test pins at `tests/management/test_export_schema.py:42-50` exercise both arms.

### Summary

The module is a tight 55-line `BaseCommand` that runs the right validation ladder (resolve → type-guard → branch on `--path`) and surfaces every consumer-input error class as `CommandError` with `from e` traceback preservation. Three guards on `--path` (argparse-layer for bare flag, body-layer for empty string, `OSError` wrap for unwritable target) plus three guards on `schema` (`ImportError`, `AttributeError`, type) make the consumer-facing failure surface explicit and individually pinned. The only real finding is GLOSSARY drift on `Schema export management command` — five `0.0.7` polish/fix behaviours are missing from the documented contract entry (Medium, GLOSSARY-only fix; routes through shape #4 per `worker-1.md`'s "GLOSSARY-only fixes do NOT qualify [for shape #5]"). One comment-pass Low (`CHANGELOG-23` rotted line-number citation in the `handle()` docstring); one defer-with-trigger Low (`*args` collapse waits for a second management command). No High and no behaviour-changing Medium, so the cycle is single-shape-#4 territory (Worker 2 writes the GLOSSARY swap-in and the docstring citation swap-in together, runs ruff, fills `Fix report` + `Comment/docstring pass` + `Changelog disposition` together; Worker 3 verifies once).

---

## Fix report (Worker 2)

Consolidated single-spawn pass (shape #4): Medium is GLOSSARY-only prose lift, Low (a) is a comment/citation fix in the `handle()` docstring, Low (b) is defer-with-trigger per the artifact's own phrasing — qualifies for consolidation per `worker-2.md` "consolidated single-spawn" gate.

### Files touched
- `docs/GLOSSARY.md:1011` — replaced the `Schema export management command` entry body verbatim with the artifact's "Recommended replacement prose" block. The new prose enumerates the five missing `0.0.7` polish/fix behaviours: (1) `--path <file>` SUCCESS report `Wrote schema to <file>`; (2) bare-`--path` rejection at argparse time; (3) empty-string-`--path` rejection at the body guard; (4) file-write `OSError` wrapped in `CommandError`; (5) `--path` omitted → `self.stdout`. Surrounding `**Status:**` line and `**See also:**` cross-ref kept intact per the artifact.
- `django_strawberry_framework/management/commands/export_schema.py:30` — replaced the rotted `CHANGELOG-23` token in the `handle()` docstring with the stable-anchor citation form recommended in the artifact (option (a)): `per the CHANGELOG.md [0.0.7] Changed "manage.py export_schema --path now requires a value when the flag is given" contract`. Verbatim substring confirmed present on disk at `CHANGELOG.md:43`.

### Tests added or updated
None. No behaviour change; both edits are documentation-only (GLOSSARY entry + docstring comment). No test in either tree pins the GLOSSARY prose or the docstring text (grep returned no matches for the old citation token or the replacement substring outside the file itself).

### Validation run
- `uv run ruff format .` — pass (211 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).
- `uv.lock` — unchanged.

### Notes for Worker 3
- Verified the five behaviours named in the replacement prose are still accurate post-0.0.7 polish by reading `export_schema.py` + `tests/management/test_export_schema.py`: stdout branch at `export_schema.py:46-48`, SUCCESS report at `export_schema.py:55`, empty-string guard at `export_schema.py:49-50`, `OSError` wrap at `export_schema.py:51-54`, type/import guards at `export_schema.py:33-42`. All five pinned in `tests/management/test_export_schema.py` (seven tests cover the failure modes).
- Verified the new docstring citation anchor by grepping `CHANGELOG.md` for the substring `now requires a value when the flag is given` → exact hit at `CHANGELOG.md:43`. The anchor is now substring-based per `AGENTS.md` rule 27, so it survives line-number drift.
- Low (b) (`*args` collapse on `handle()` signature) deferred per the artifact's explicit trigger: "revisit when a **second** management command lands in `django_strawberry_framework/management/commands/` and either commits to `*args` or drops it." No source edit this cycle. Trigger condition: second management command added.
- No shadow file used during fix implementation (edits localised to two single-line docstring/prose swaps).
- No findings rejected.

---

## Comment/docstring pass

Consolidated into the logic pass above (shape #4 single-spawn). The Low (a) citation swap lives in the `Files touched` block of `## Fix report (Worker 2)`; no separate comment pass.

### Files touched
- `django_strawberry_framework/management/commands/export_schema.py:30` — see Fix report above.

### Per-finding dispositions
- Medium 1 (GLOSSARY drift): applied verbatim per the artifact's recommended replacement prose.
- Low 1 (`CHANGELOG-23` rotted citation): applied per the artifact's option (a) (substring-anchored CHANGELOG citation).
- Low 2 (`*args` collapse): deferred-with-trigger per the artifact's own phrasing; no source edit.

### Validation run
- `uv run ruff format .` — pass (run once at end of consolidated pass).
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3
Per-finding dispositions above cover the full set; consolidated-pass shape means the validation run is shared with the logic pass.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Cycle edits are documentation-only: the GLOSSARY prose lift aligns the published consumer-contract entry with shipped `0.0.7` behaviour that already has four explicit `CHANGELOG.md` entries (lines 41, 42, 43, 61) plus the in-source empty-string guard at `export_schema.py:49-50` — no new behaviour is introduced, no public surface changes, the GLOSSARY-prose edit is internal documentation hygiene against the changelog and source that already shipped. The docstring citation swap is a stable-anchor citation hygiene fix against an already-correct CHANGELOG entry. Per the worker-2.md "Not warranted" gate, both halves required: (1) `AGENTS.md` rule 21 — "Do not update CHANGELOG.md unless explicitly instructed"; (2) the active plan does not authorize a CHANGELOG edit for this cycle item (the artifact records no changelog authorization and the dispatch prompt explicitly states "Changelog disposition: `Not warranted` (internal documentation hygiene; the GLOSSARY edit aligns prose with shipped behavior without changing behavior) citing AGENTS.md + active plan silence").

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass (shared with logic/comment pass).
- `uv run ruff check --fix .` — pass.

---

## Verification (Worker 3)

Terminal-verify of Worker 2's consolidated single-spawn (shape #4) pass: one Medium (GLOSSARY drift), one Low (a) (citation hygiene), one Low (b) (defer-with-trigger).

### Logic verification outcome
- **Medium (GLOSSARY drift).** `docs/GLOSSARY.md:1011` replaced verbatim with the artifact's "Recommended replacement prose" (lines 31 of the artifact). Diff confirms the surrounding `**Status:** shipped (`0.0.7`).` line at GLOSSARY:1009 and the `**See also:** [Django `AppConfig`](#django-appconfig).` line at GLOSSARY:1013 are untouched; only the body sentence at :1011 changed. New prose enumerates all five `0.0.7` polish/fix behaviours called out in the Medium: (1) stdout branch on `--path` omitted, (2) `Wrote schema to <file>` SUCCESS report on file-write success, (3) bare-`--path` argparse-time rejection, (4) empty-string-`--path` body-guard rejection, (5) `OSError` wrap on file-write. Spot-confirmed against source: stdout at `export_schema.py:47-49`, SUCCESS report at `:56`, empty-string guard at `:50-51`, `OSError` wrap at `:52-55`, type/import guards at `:34-43`.
- **Low (a) (rotted `CHANGELOG-23` citation).** `export_schema.py:30-31` replaced with substring-anchored citation per the artifact's option (a). The artifact's recommended phrasing was `per the CHANGELOG.md "[0.0.7] Changed — manage.py export_schema --path now requires a value when the flag is given" contract`; Worker 2 rendered it for RST docstring formatting as `per the ` `` `CHANGELOG.md` `` ` ` `` `[0.0.7] Changed` `` ` "manage.py export_schema --path now requires a value when the flag is given" contract` (em-dash dropped, two code spans backticked). The load-bearing substring "now requires a value when the flag is given" grep-confirms verbatim at `CHANGELOG.md:43` (the post-ship-polish bullet for the `nargs="?"` removal), so the citation is stable against future `[Unreleased]` insertions ahead of `0.0.7` per `AGENTS.md` rule 27. Old `CHANGELOG-23` token absent post-edit.
- **Low (b) (`*args` collapse on `handle` signature).** Deferred per the artifact's explicit defer-with-trigger phrasing: "revisit when a **second** management command lands in `django_strawberry_framework/management/commands/` and either commits to `*args` (collecting nargs positionals) or drops it." No source edit this cycle; trigger condition recorded.

### DRY findings disposition
None. The artifact's DRY analysis is `None — …` with explicit justification (the two `except → CommandError(str(e)) from e` arms catch disjoint exception families across separated call sites; the `--path` branch ladder has no common epilogue). Nothing to carry forward.

### Temp test verification
- Temp test files used: none. Validation collapsed to grep + Read since both edits are documentation-only and no behaviour changed.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified`.

**Gate-by-gate:**
1. GLOSSARY edit verbatim against the artifact's recommended prose; surrounding `**Status:**` / `**See also:**` preserved (`git diff -- docs/GLOSSARY.md` shows one-line body swap at :1011).
2. Source comment citation fix applied; substring anchor "now requires a value when the flag is given" matches CHANGELOG.md:43 verbatim.
3. Changelog `Not warranted` cites both AGENTS.md rule 21 ("Do not update CHANGELOG.md unless explicitly instructed") and active-plan silence on changelog authorization for this cycle item.
4. `git diff -- CHANGELOG.md` empty (zero-line diff).
5. Ruff outcomes: `uv run ruff format --check` on `export_schema.py` reports "1 file already formatted" (the GLOSSARY.md "preview mode" warning is harmless and applies only to experimental markdown formatting); `uv run ruff check` on `export_schema.py` reports "All checks passed!".

Out-of-scope dirty paths at dispatch (TODAY.md, docs/TREE.md, docs/review/rev-filters.md, examples/fakeshop/README.md, examples/fakeshop/apps/glossary/migrations/0001_initial.py, examples/fakeshop/db.sqlite3, scripts/import_glossary_md.py) are presumptively concurrent maintainer work per `AGENTS.md` rule 33 and ignored.

---

## Iteration log
