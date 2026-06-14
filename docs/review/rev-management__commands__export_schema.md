# Review: `django_strawberry_framework/management/commands/export_schema.py`

Status: verified

## DRY analysis

- Defer-with-trigger — the two `except → CommandError(str(e)) from e` arms (`export_schema.py:39` and `export_schema.py:54`) catch deliberately disjoint exception families (`ImportError | AttributeError` from `import_module_symbol` vs. `OSError` from `Path.write_text`) at call sites separated by the type guard and the `print_schema` render, so folding them through a shared `_raise_command_error_from(e)` helper would obscure the linear staged shape ("resolve symbol → guard type → render SDL → emit"). The sibling `inspect_django_type.py` now also raises `CommandError(str(e)) from e` off its own `import_module_symbol` arm (`inspect_django_type.py:106`) — but that is a third *instance* of the same one-line idiom, not a third call site of a shared body; the idiom is Django's documented `CommandError` convention, not extractable logic. Revisit only if a cross-command helper module for management commands lands and the `import_module_symbol → CommandError` resolve-with-wrap pattern (shared verbatim across `export_schema.py:34-40` and `inspect_django_type.py:103-106`) becomes a 3rd+ consumer of a single resolver helper — at that point extract `_resolve_schema_symbol(selector)` once, since both commands resolve the same `default_symbol_name="schema"` shape.

## High:

None.

## Medium:

None.

## Low:

### `handle(self, *args, **options)` ignores `*args` — the "second command" defer trigger has now fired but resolves to "keep the canonical shape"

`export_schema.py:25` declares `def handle(self, *args: object, **options: object) -> None:` and never reads `args`; the positional `schema` is a single scalar read as `options["schema"]` (`export_schema.py:36`). The prior-cycle (0.0.7) artifact recorded this as a defer-with-trigger Low: "revisit when a **second** management command lands ... and either commits to `*args` or drops it."

That trigger has now fired — `inspect_django_type.py` (the 0.0.9-era sibling) exists in the same package. Re-triaging at the trigger: the sibling uses the **identical** signature `def handle(self, *args: object, **options: object) -> None:` (`inspect_django_type.py:99`) and also never reads `args` (it reads `options["type"]` / `options["schema"]`). So the package has de-facto standardized on Django's documented `BaseCommand.handle(self, *args, **options)` override shape across both commands. There is no inconsistency to resolve and no act-now edit: matching the Django-documented hook signature is the correct convention, and dropping `*args` to `def handle(self, **options: object) -> None:` would diverge from the framework's published override pattern for a purely cosmetic gain. Recorded as resolved-by-consistency; no source edit.

Defer-with-new-trigger: revisit only if a future management command in this package *does* declare a positional `nargs` collector that needs `*args`, or if the package adopts an explicit lint/style rule banning the unused `*args` on `BaseCommand.handle` overrides. Until either, the canonical Django shape stands.

## What looks solid

### DRY recap

- **Existing patterns reused.** `import_module_symbol(default_symbol_name="schema")` reuses Strawberry's first-party importer (`export_schema.py:35-38`) rather than re-implementing a dotted-path splitter; `strawberry.printer.print_schema` reuses Strawberry's SDL serializer (`export_schema.py:45`); `self.style.SUCCESS(...)` reuses Django's terminal-styling pipeline (`export_schema.py:56`) instead of bare `print(...)`. Both `CommandError` raises carry `from e` (`export_schema.py:40`, `:55`) preserving the original traceback per Django's documented convention. The sibling `inspect_django_type.py` reuses the same `import_module_symbol(..., default_symbol_name="schema")` resolve shape, so the cross-command convention is coherent (GLOSSARY:1183 documents the deliberate mirroring).
- **New helpers considered.** The two `except → CommandError(str(e)) from e` arms (`export_schema.py:34-40` and `:52-55`) were considered for folding through a shared helper and rejected — disjoint exception families across call sites separated by the type guard and `print_schema`. The `--path is None / not path / else` ladder (`export_schema.py:46-56`) was considered for a single `_emit(schema_output, path)` helper and rejected — the three branches share no common epilogue, and the `if not path: raise` guard cannot fold into a single test against `path is None` without losing the empty-string-vs-None distinction the suite pins (`tests/management/test_export_schema.py:76-85`).
- **Duplication risk in the current file.** None — the three `CommandError(...)` messages are distinct and deliberately non-shared (`"...must be an instance of strawberry.Schema"` at `:43`; `"--path requires a non-empty value"` at `:51`; the two `str(e)` shapes at `:40`/`:55`). Shadow overview reports `Repeated string literals: 0`.

### Other positives

- **Defensive layering on `--path`.** Three guards for three distinct typo classes, each mapping to its own `CommandError` shape and its own pinned test: argparse rejects bare `--path` at parse time (no `nargs="?"`, `tests/management/test_export_schema.py:76-79`); the body guard at `export_schema.py:50-51` rejects empty-string `--path` (`tests/...:82-85`); the `OSError` wrap at `:52-55` rejects unwritable paths (`tests/...:64-73`).
- **Symbol-resolution failure envelope.** `except (ImportError, AttributeError)` at `export_schema.py:39` matches `import_module_symbol`'s actual raise surface (`ImportError` for unimportable module, `AttributeError` for missing attribute); both arms pinned at `tests/management/test_export_schema.py:42-50`.
- **Single-source SDL.** `schema_output = print_schema(schema_symbol)` (`export_schema.py:45`) is computed once before the branch ladder, so the stdout and file-write branches emit byte-identical SDL.
- **Test discipline split across two trees per `AGENTS.md`.** Package-internal failure-mode pins in `tests/management/test_export_schema.py` (seven tests, `monkeypatch.setitem(sys.modules, ...)` for teardown-safe module synthesis); success-path stdout + file-write branches earned via live `call_command` against the real fakeshop schema at `examples/fakeshop/tests/test_export_schema.py:8-28`, including the `Wrote schema to <file>` SUCCESS assertion. Each `call_command`-reachable branch is exercised through real usage, not mocked.

### Summary

A tight 56-line `BaseCommand` running the correct validation ladder (resolve dotted-path symbol → type-guard against `strawberry.Schema` → branch on `--path`) and surfacing every consumer-input error class as `CommandError` with `from e` traceback preservation. Three `--path` guards (argparse bare-flag, body empty-string, `OSError` wrap) plus three `schema` guards (`ImportError`, `AttributeError`, type) make the failure surface explicit and individually pinned. **This is a fresh 0.0.9 review superseding a stale 0.0.7 `Status: verified` artifact on disk; all three findings the prior artifact raised are already merged into current source** — verified at source: the GLOSSARY drift Medium is resolved (GLOSSARY:1173 now carries the full five-behaviour prose), the `CHANGELOG-23` rotted-citation Low (a) is resolved (the `handle()` docstring now uses the substring-anchored citation "now requires a value when the flag is given", grep-confirmed at `CHANGELOG.md:110`), and the `*args` Low (b) trigger has fired but re-triages to keep-the-canonical-shape (the sibling `inspect_django_type.py:99` uses the identical signature). No High, no Medium, one forward-looking Low with a new trigger, zero edits to any tracked file — a no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format --check django_strawberry_framework/management/commands/export_schema.py` — "1 file already formatted" (the `COM812`-vs-formatter warning is the standing repo config warning, harmless).
- `uv run ruff check django_strawberry_framework/management/commands/export_schema.py` — "All checks passed!".

### Notes for Worker 3
- Single Low (`handle` `*args`): the prior-cycle defer-trigger ("a second management command lands") has fired (`inspect_django_type.py` exists), but re-triage at the trigger resolves to no edit — the sibling uses the identical `def handle(self, *args: object, **options: object)` signature, so the package is consistently on Django's documented override shape. Recorded with a new trigger (a positional-`nargs`-collecting command, or an explicit anti-`*args` lint rule). No source edit warranted.
- No GLOSSARY-only fix in scope. GLOSSARY:1173 already matches the contract verbatim (the prior cycle's recommended replacement prose is the live text) — re-verified at source, no drift remaining. Do NOT re-raise the prior cycle's GLOSSARY Medium; it is merged.
- The prior cycle's Low (a) (`CHANGELOG-23` token) is merged — source docstring (`export_schema.py:30-32`) uses the substring-anchored citation; old token absent. Do NOT re-raise.
- No shadow file regenerated (plan-time `--all` overview is current; source unchanged since).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits. The `handle()` docstring (`export_schema.py:26-33`) is accurate against current behaviour and uses a stable substring-anchored `CHANGELOG.md` citation per `AGENTS.md` rule 27 (the prior-cycle `CHANGELOG-23` rot is already fixed in source). The class/method docstrings match the implemented contract.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

`Not warranted`. No source/test/GLOSSARY/CHANGELOG edits this cycle. Cited per the "Not warranted" gate: (1) `AGENTS.md` rule 21 — "Do not update CHANGELOG.md unless explicitly instructed"; (2) the active plan records no changelog authorization for this cycle item, and the dispatch prompt forbids touching `CHANGELOG.md`.

---

## Verification (Worker 3)

### Logic verification outcome
Independently re-inspected `export_schema.py` (56 lines) against the artifact's no-source-edit (shape #5) conclusions:
- **One Low (`handle` `*args`):** confirmed `export_schema.py #"def handle(self, *args"` declares `def handle(self, *args: object, **options: object) -> None:` and never reads `args`; the sibling `inspect_django_type.py:99` uses the byte-identical signature (grep-confirmed). The defer-trigger ("second command lands") fired but correctly re-triages to keep the Django-documented `BaseCommand.handle` override shape — no inconsistency to resolve, no act-now edit. New trigger (positional-`nargs` collector / anti-`*args` lint) recorded. Accepted.
- **Prior-cycle findings claimed merged — all confirmed at source:**
  - GLOSSARY:1173 export_schema entry carries the full five-behaviour prose (stdout / bare-`--path` parse-time / empty-string / file-write / OSError families); unchanged from baseline (`git diff` of GLOSSARY shows hunks only at lines 286/991/1001, none at 1173). Merged.
  - `handle()` docstring (`export_schema.py:26-33`) uses the substring-anchored citation "now requires a value when the flag is given", grep-confirmed live at `CHANGELOG.md:110`; old `CHANGELOG-23` token absent. Merged per AGENTS rule 27.
  - `*args` signature present as described. Merged.
- **Symbol-resolution failure envelope (live probe):** drove `import_module_symbol` under `uv run python` — bad module raises `ModuleNotFoundError` (subclass of `ImportError`), missing attribute raises `AttributeError`; both land in `except (ImportError, AttributeError)` at `:39`. `issubclass(AttributeError, (ImportError, AttributeError))` True. Envelope claim holds.
- **`--path` three-guard ladder:** `path is None` (omitted → stdout, `:47-49`), `not path` (empty-string → CommandError, `:50-51`), real path (write + OSError wrap, `:52-56`) — the empty-string-vs-None distinction is preserved exactly as the artifact and pinned tests describe. SDL computed once at `:45` before the branch (single-source). All correct.

No High/Medium. No defect requiring a code change found.

### Sibling-cycle attribution (shape #5)
Owned-path cycle diff `git diff <baseline> -- django_strawberry_framework/management/commands/export_schema.py` is EMPTY (confirmed). Broader diff-stat dirty paths all attribute to CLOSED sibling cycles (each `Status: verified` + `[x]` in `review-0_0_9.md`):
- `conf.py` (rev-conf.md, [x] review-0_0_9.md:70), `exceptions.py` (rev-exceptions.md, :72), `list_field.py` (rev-list_field.md, :73), `filters/factories.py` (rev-filters__factories.md, :80), `filters/sets.py` (rev-filters__sets.md, :82).
- `docs/GLOSSARY.md` three hunks: line 286 DjangoConnection → rev-connection.md (sibling); lines 991/1001 RelatedFilter/RelatedOrder → rev-filters.md folder-pass (verified). None touch the export_schema entry.
- `feedback2.md` / `feedback3.md` deletions = AGENTS.md #33 concurrent-maintainer work; untracked `rev-connection.md` / `rev-relay.md` / `rev-management__commands__inspect_django_type.md` / `review-0_0_9.md` are concurrent-cycle artifacts. Left untouched.
The cycle's "Files touched: None" claim holds.

### DRY findings disposition
Single defer-with-trigger DRY item (two `except → CommandError(str(e)) from e` arms catching disjoint families; third instance in `inspect_django_type.py` is the same one-line Django idiom, not a shared body). Correctly carried forward with a concrete re-extraction trigger (a cross-command helper module + 3rd consumer of an `import_module_symbol → CommandError` resolver). Not actionable now; accepted.

### Temp test verification
- Created `docs/review/temp-tests/export_schema/` (gitignored); used an inline `uv run python` probe of `import_module_symbol`'s raise surface rather than a file. No temp test file persisted.
- Disposition: none to promote — existing suite (`tests/management/test_export_schema.py` seven failure pins + `examples/fakeshop/tests/test_export_schema.py` live success branches) already covers every branch per AGENTS test-tree discipline.

### Changelog disposition verification
`Not warranted`. `git diff -- CHANGELOG.md` EMPTY (confirmed). Both citations present: AGENTS.md rule 21 + active-plan silence / dispatch-prompt prohibition. Internal-only framing honest — zero source/test/GLOSSARY/CHANGELOG edits this cycle, no public-API surface changed. Correct state.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `export_schema.py` checklist box in `docs/review/review-0_0_9.md`.

---

## Iteration log
