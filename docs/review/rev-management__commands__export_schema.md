# Review: `django_strawberry_framework/management/commands/export_schema.py`

Status: verified

## DRY analysis

- None — the only repeated shape this file once carried (the `except (ImportError, AttributeError): raise CommandError(str(e)) from e` import-rewrap tail) is already consolidated into `management/commands/_imports.py::import_or_command_error`, consumed at `export_schema.py::Command.handle #"import_or_command_error("`. The remaining `except OSError: raise CommandError(str(e)) from e` site (`export_schema.py::Command.handle #"write_text"`) catches a distinct exception family against a distinct operation (file write, not symbol import) and is intentionally inlined — folding it into the import helper would hide the per-branch exception tuple. The sibling command `inspect_django_type.py` is the cross-file comparison point (folder pass `rev-management__commands.md`), not a local hoist.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `Command.handle` delegates import-failure handling to the canonical `import_or_command_error` helper (`management/commands/_imports.py::import_or_command_error`), passing the Strawberry `import_module_symbol(..., default_symbol_name="schema")` call as a zero-arg lambda so the importer/args stay visible at the call site while the `(ImportError, AttributeError) → CommandError` error shape is shared with `inspect_django_type`. SDL emission reuses Strawberry's own `print_schema`; `CommandError`/`BaseCommand`/`CommandParser` are Django's canonical management-command surface — no local re-implementations.
- **New helpers considered.** A shared "resolve-then-validate" wrapper spanning both commands was evaluated and rejected: `export_schema` validates `isinstance(..., Schema)` while `inspect_django_type` validates a `DjangoType` subclass with finalized-definition checks — divergent post-import contracts that a shared wrapper would obscure. Folding the `OSError` write-rewrap into `import_or_command_error` was likewise rejected (different caught family, different operation).
- **Duplication risk in the current file.** None — single command class, a 7-line `add_arguments`, and a linear `handle` with a three-way `--path` dispatch. Shadow overview reports 0 repeated string literals.

### Other positives

- **Correct `BaseCommand.handle` signature and argument reads.** `handle(self, *args, **options)` matches Django's contract; `schema` is a required positional read via direct `options["schema"]` index (always populated by argparse) while the optional `--path` is read via `options.get("path")`, returning `None` when omitted — the exact sentinel the `if path is None` stdout branch keys on.
- **Correctly-ordered three-way `--path` dispatch.** `None` (omitted → stdout) is tested first, so a falsy-but-not-None `""` can only reach the `if not path:` guard → `CommandError("--path requires a non-empty value")`; truthy → UTF-8 write with explicit `encoding="utf-8"` and a `self.style.SUCCESS` confirmation. A bare `--path` with no following token is rejected by argparse at parse time (no `nargs="?"`), distinct from the runtime empty-string guard.
- **Exhaustive, correctly-scoped exception wrapping.** Import failures (`ModuleNotFoundError`/`ImportError` for a bad module, `AttributeError` for a bad symbol) are rewrapped via the shared helper; file-write failures are narrowed to `OSError` and rewrapped with `from e`, preserving the cause while giving the consumer a clean `CommandError` instead of a traceback. The `isinstance(schema_symbol, Schema)` guard rejects a resolved-but-wrong symbol before printing.
- **Accurate docstring.** The `handle` docstring describes the three branches and quotes the code's real error message (`"--path requires a non-empty value"`) and correctly attributes the `[0.0.7] Changed` "--path now requires a value when the flag is given" contract to the parse-time bare-`--path` rejection (not the runtime empty-string branch). This matches the current source verbatim; no TODOs (shadow: 0 TODO comments).

### Summary

`export_schema.py` is a small, logically clean management command: resolve a dotted-path Strawberry `Schema` symbol via the shared `import_or_command_error` helper, validate it is a real `Schema`, then print SDL to stdout or write UTF-8 to `--path` with explicit empty-string and `OSError` handling. The diff is empty versus both the per-cycle baseline (`756ec82e`) and HEAD; no High/Medium/Low findings surfaced; the prior import-rewrap duplication is already consolidated into `_imports.py`; and `docs/GLOSSARY.md:1226` matches the implementation (positional `schema` + `--path` three-branch contract + all six `CommandError` cases) with no drift. Genuine no-source-edit cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 289 files left unchanged.
- `uv run ruff check --fix .` — pass; all checks passed.

### Notes for Worker 3
- No-source-edit (shape #5): `git diff 756ec82e1fc9dc14f821cf2a18e99d8595e29982 -- <target>` and `git diff HEAD -- <target>` both empty.
- All severities `None.`; no behaviour-changing finding.
- DRY: single `None —` bullet; the import-rewrap consolidation already landed in `_imports.py::import_or_command_error` (prior cycle), not a pending candidate.
- The prior-cycle Low (docstring mis-attributing the empty-string `--path` branch to the wrong CHANGELOG contract) is RESOLVED in current source — the `handle` docstring now quotes `"--path requires a non-empty value"` and ties the `[0.0.7]` contract to the parse-time bare-flag rejection. Not re-flagged.
- No GLOSSARY-only fix in scope — `docs/GLOSSARY.md:1226` matches the implementation (positional `schema` + `--path` three-branch contract + all six `CommandError` cases); no drift.

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits: the module/class/method docstrings accurately describe behavior. The `handle` docstring's three-branch summary, the verbatim `"--path requires a non-empty value"` message, and the bare-`--path`/`[0.0.7] Changed` attribution all match current source; no stale TODOs (shadow: 0 TODO comments).

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — zero source edits this cycle (internal-only review, nothing shipped). Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_11.md`), which carries no changelog directive for this per-file item.

---

## Verification (Worker 3)

### Logic verification outcome
All High / Medium / Low are `None.` — independently confirmed genuine, not lazy:
- **Positional dotted-path resolution.** `handle` reads the required positional via `options["schema"]` (always populated by argparse) and resolves through `import_or_command_error(lambda: import_module_symbol(..., default_symbol_name="schema"))`. The `(ImportError, AttributeError) → CommandError` rewrap lives ONLY in `_imports.py::import_or_command_error`; `grep -rn "except (ImportError, AttributeError)" django_strawberry_framework/management/` returns only `_imports.py` (line 32 + docstring quote line 6) — no straggler tail in `export_schema.py`. Both failure families pinned: `test_export_schema_raises_command_error_for_unimportable_module` (ImportError → "No module named") and `test_export_schema_raises_command_error_for_missing_attribute_on_module` (AttributeError → symbol name).
- **Three-way `--path` dispatch / empty-string + OSError.** Source order at `handle #"path = options.get"` is correct: `path is None` → stdout `return`; falsy-but-not-None `""` → `CommandError("--path requires a non-empty value")`; truthy → `pathlib.Path(path).write_text(..., encoding="utf-8")` inside `try/except OSError as e: raise CommandError(str(e)) from e` then `self.style.SUCCESS` confirmation. The `--path`-no-value parse-time rejection is pinned package-side (`test_export_schema_raises_command_error_when_path_flag_has_no_value`); the runtime empty-string and directory-write `OSError` branches are correctly relocated to the fakeshop project suite (`examples/fakeshop/tests/test_export_schema.py`) per the noted comment in `tests/management/test_export_schema.py`, where they run against the real `config.schema` — consistent with AGENTS.md "test through real usage." Non-Schema guard pinned by `test_export_schema_raises_command_error_for_non_schema_symbol`.
- **`import_or_command_error` consumption.** Single zero-arg-lambda call site matching the `Callable[[], T] -> T` contract; importer + args stay visible at the call site. Correct.
- **`handle()` docstring accuracy.** The three-branch summary, the verbatim `"--path requires a non-empty value"` message, and the bare-`--path`/`[0.0.7] Changed` parse-time attribution all match current source line-for-line. No stale TODOs.
- **GLOSSARY accuracy (genuine #5, not missed #4).** `docs/GLOSSARY.md:1226` describes positional `schema` (default symbol `"schema"`), optional `--path`, the three-branch dispatch, and all six `CommandError` cases (unimportable path, non-Schema symbol, missing positional, bare `--path`, empty-string `--path`, file-write `OSError`) — matches live source verbatim. No drift, no owed GLOSSARY fix.

### DRY findings disposition
Single `None —` bullet, correctly justified: the import-rewrap tail is already consolidated into `_imports.py::import_or_command_error` (prior cycle, landed in `_imports.py`); the remaining `except OSError` write-rewrap is intentionally inlined (distinct exception family, distinct operation). No forward owed; the cross-file `inspect_django_type` comparison is the folder pass's concern, not a local hoist.

### Temp test verification
- None — no temp tests needed; the zero-edit proof and live grep were sufficient.
- Disposition: n/a.

### Shape #5 gate checklist
1. `git diff 756ec82e... -- export_schema.py` empty; `git diff HEAD -- export_schema.py` empty; `git diff --stat 756ec82e... -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty (no owned-path dirt this run, no #33 inspect_django_type churn).
2. Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern." — confirmed.
3. Every Low `None.`; no GLOSSARY-only fix smuggled in.
4. Changelog `Not warranted` cites BOTH AGENTS.md #21 AND the active plan's silence — both present; `git diff -- CHANGELOG.md` empty.
5. `uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (all checks passed) on the target.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box in `docs/review/review-0_0_11.md`.
