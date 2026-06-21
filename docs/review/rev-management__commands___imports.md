# Review: `django_strawberry_framework/management/commands/_imports.py`

Status: verified

## DRY analysis

- None — this file *is* the DRY resolution for the management-commands namespace. It extracts the byte-identical catch-and-rewrap tail (`except (ImportError, AttributeError) as e: raise CommandError(str(e)) from e`) that previously appeared verbatim at three call sites across two commands. The importer-as-zero-arg-callable design (`Callable[[], T]`) lets each call site keep its own importer (`import_module_symbol` vs `import_string`) and arguments visible at the site while sharing one error-handling shape. The single consumer-discard site (`inspect_django_type.py::Command.handle` import-for-side-effect at lines 107-109) is covered by the same helper because the return value is passed through unchanged and simply ignored. No further consolidation candidate exists at this granularity.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The helper consolidates the previously-duplicated rewrap tail now reached from `export_schema.py::Command.handle #"schema_symbol = import_or_command_error"` (line 38) and `inspect_django_type.py::Command.handle #"import_or_command_error("` (line 107) plus `inspect_django_type.py::Command._resolve_type #"import_string(arg)"` (line 129). Three sites, two distinct importers, one error contract.
- **New helpers considered.** None beyond this one — the module is the new helper. A further generalization (e.g. parameterizing the caught exception tuple) was considered and rejected: all three sites want exactly `(ImportError, AttributeError)` and `str(e)`, so widening the surface would add an unused parameter and weaken the single contract the tests pin.
- **Duplication risk in the current file.** None — single function, single `try/except`, no repeated literals (static overview reports 0 repeated string literals).

### Other positives

- **Correct exception scope.** Catches only `(ImportError, AttributeError)` and lets every other exception propagate untouched — pinned by `tests/management/test_imports.py::test_import_or_command_error_does_not_swallow_other_exceptions`. `import_string`/`import_module_symbol` surface a missing module as `ImportError` and a missing attribute on a resolved module as `AttributeError`, so the tuple matches the real failure modes without over-catching.
- **Cause chaining preserved.** `raise CommandError(str(e)) from e` keeps the original exception as `__cause__` (so debuggers/tracebacks retain root cause) while the consumer sees a clean `str(e)` message with no raw traceback — both halves pinned by `test_import_or_command_error_wraps_import_error` and `test_import_or_command_error_wraps_attribute_error`.
- **Generic pass-through typing.** `Callable[[], T] -> T` propagates the importer's return type, and the value is returned unchanged so the discard-for-side-effect site composes correctly. Pinned by `test_import_or_command_error_passes_through_return_value` (identity assertion).
- **Sound shared home.** Living at `management/commands/_imports.py` (leading underscore, no `__all__`) scopes it as a private intra-namespace helper for exactly the two commands that need it; it imports only stdlib (`collections.abc`, `typing`) and `django.core.management.base.CommandError`, so it has no first-party dependency and creates no import-time side effects or circular-import risk. Both commands import it at module top with no ordering hazard.
- **Test discipline.** `tests/management/test_imports.py` pins the helper contract directly (four focused unit tests) while the per-command tests exercise the live importer branches via `call_command`, per the AGENTS.md test-through-real-usage rule — the unit tests cover only what the real-usage path cannot reach cleanly (the discard-site identity and the non-swallow branch).

### Summary

`_imports.py` is a NEW file this 0.0.11 cycle and a textbook DRY resolution: it factors the byte-identical import-failure rewrap tail out of `export_schema` and `inspect_django_type` into one `import_or_command_error(importer)` helper that takes the importer as a zero-arg callable, so each of the three call sites keeps its own importer and arguments visible while sharing a single, well-tested error-handling contract. The exception scope is tight (only `ImportError`/`AttributeError`), cause chaining is preserved, generic typing passes the return through unchanged, and there are no import-time side effects or circular-import risk. The contract is pinned by four focused tests in `tests/management/test_imports.py`; GLOSSARY documents both commands but correctly carries no entry for this internal helper, so there is no doc drift. `git diff` is empty against both the cycle baseline `b8f85723` and HEAD — the file fully landed in HEAD (commit `8d6ca99b`), so this is a genuine no-source-edit cycle. No High/Medium/Low findings.

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
- Zero High/Medium/Low findings; `## DRY analysis` is a single `None —` bullet (this file is itself the DRY resolution of the prior management-commands duplication).
- `git diff b8f85723149ac20d229207a07e4c53645d959639 -- django_strawberry_framework/management/commands/_imports.py` is empty; `git diff HEAD -- …` is empty. File landed in HEAD via commit `8d6ca99b`. No pending edits exist this cycle.
- No GLOSSARY-only fix in scope. GLOSSARY documents `export_schema` (lines 1222-1228) and `inspect_django_type` (lines 1230-1240) but carries no entry for `_imports.py` / `import_or_command_error` — correct, as it is a private intra-namespace helper, not a documented public-contract symbol. Ran the grep-GLOSSARY drift check (the step separating shape #4 from #5): clean.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

Module docstring and function docstring are accurate: the module docstring explains the three-call-site duplication being removed and the importer-as-callable rationale; the function docstring documents the catch scope, the pass-through-of-return, and the `from e` cause preservation. No stale comments, no restating-the-obvious, no obsolete TODOs (static overview reports 0 TODO comments). No comment/docstring edits needed.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source edit was made this cycle (empty diff vs baseline and HEAD), so there is nothing to record. Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` (silent on CHANGELOG for this item), no changelog entry is produced by the review cycle.

---

## Verification (Worker 3)

### Logic verification outcome
All High / Medium / Low are `None.` and confirmed genuine (not lazy):

- **Three call sites, two importers, one contract** — independently grepped: `export_schema.py:38` wraps `import_module_symbol`; `inspect_django_type.py:107` wraps `import_module_symbol` (side-effect-only, return discarded) and `:129` wraps Django's `import_string` and returns it. All three pass a zero-arg `lambda`, matching `import_or_command_error(importer: Callable[[], T]) -> T`. The artifact's three-site / two-importer claim holds verbatim.
- **No residual duplicate of the rewrap tail** — `grep -rn "except (ImportError, AttributeError)" django_strawberry_framework/management/` returns only `_imports.py` itself (line 32 + the docstring quote at line 6). The byte-identical tail was fully extracted; no straggler left at any call site, so the DRY-resolution claim is real.
- **Exception scope / cause chaining** — catches exactly `(ImportError, AttributeError)`, lets all else propagate; `raise CommandError(str(e)) from e` preserves `__cause__`. Pinned by `tests/management/test_imports.py::test_import_or_command_error_wraps_import_error`, `…_wraps_attribute_error` (asserts `__cause__ is original` AND `str` equality), and `…_does_not_swallow_other_exceptions` (ValueError propagates). Pass-through identity pinned by `…_passes_through_return_value` (`is sentinel`). Four focused tests cover exactly what the live `call_command` paths cannot reach cleanly — consistent with AGENTS.md test-through-real-usage.
- **Sound shared home / no import-time side effects** — imports only stdlib (`collections.abc`, `typing`) + `django.core.management.base.CommandError`; leading-underscore module, no `__all__`. Both consumers import it at module top; no first-party dependency, no circular-import risk.

No masked defect forces a source edit — genuine shape #5.

### DRY findings disposition
Single `None —` bullet: this file *is* the DRY resolution of the prior management-commands duplication (the extracted tail), confirmed above (no remaining duplicate in `management/`). No further consolidation candidate at this granularity; nothing forwarded.

### Temp test verification
- None used — zero-edit cycle, no new behavior to prove; the existing four unit tests fully pin the contract.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `_imports.py` checklist box in `docs/review/review-0_0_11.md`.

Shape #5 gate evidence:
1. `git diff b8f85723149ac20d229207a07e4c53645d959639 -- …/_imports.py` empty; `git diff HEAD -- …/_imports.py` empty. `git diff --stat <baseline> -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` fully empty — no owned-path dirt at all this run (no standing #33 inspect_django_type churn present). File landed in HEAD via commit `8d6ca99b`.
2. Each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.`
3. All Lows `None.`; no GLOSSARY-only fix in scope.
4. Changelog `Not warranted` with BOTH citations (AGENTS.md #21 + plan silence); `git diff HEAD -- CHANGELOG.md` and vs baseline both empty.
5. GLOSSARY: independently grepped — entries exist for `export_schema` (1226) and `inspect_django_type` (1234, 1238) but ZERO hits for `_imports` / `import_or_command_error`. Correct: a private intra-namespace helper carries no public-contract entry. Genuine #5, no GLOSSARY drift.
