# Review: `django_strawberry_framework/management/commands/` (folder pass)

Status: verified

Folder pass over `django_strawberry_framework/management/commands/`. In-scope `.py`: `_imports.py`, `export_schema.py`, `inspect_django_type.py` (all `verified` this cycle); the folder `__init__.py` is a single module docstring (shadow overview: 0 symbols, 0 imports, 0 literals). Whole-folder `git diff` is empty against both the per-cycle baseline `5d3bf1dde1b614ce3b8f49c24628e83ac1793ef6` and HEAD, so this is a genuine no-source-edit folder pass (shape #5). The prior-cycle artifact recorded the act-now hoist of the import-rewrap tail into `_imports.py`; that DRY resolution has since landed in HEAD, so this cycle confirms no NEW duplication remains.

## DRY analysis

- None — the management-commands namespace is already at its DRY shape. The one cross-command duplication this folder ever carried (the byte-identical import-failure rewrap tail `except (ImportError, AttributeError) as e: raise CommandError(str(e)) from e`) was resolved into `management/commands/_imports.py::import_or_command_error` and is now consumed from all three former call sites (`export_schema.py::Command.handle #"import_or_command_error("`, `inspect_django_type.py::Command.handle #"import_or_command_error("`, `inspect_django_type.py::Command._resolve_type #"import_string(arg)"`). Grep confirms the rewrap tail survives only inside `_imports.py` itself (the `try/except` body plus its docstring quote) — no NEW duplication remains across the two commands. The importer-as-zero-arg-callable design keeps each site's importer (`import_module_symbol` vs `import_string`) and arguments visible while sharing one error contract; no further folder-level consolidation candidate exists. Two cross-family candidates touching these commands' error handling were considered and rejected as folder-scope: the post-import validation diverges per command (`isinstance(..., Schema)` vs `DjangoType`-subclass + finalized-definition checks), and `export_schema`'s `except OSError → CommandError` write-rewrap is a distinct exception family against a distinct operation — folding either into the import helper would hide the per-branch contract.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The import-failure rewrap is single-sourced in `management/commands/_imports.py::import_or_command_error` and consumed by both commands (three call sites, two importers, one contract) — this folder's headline DRY resolution. Beyond the shared helper each command leans on canonical surfaces rather than re-implementing: `export_schema` reuses Strawberry's `print_schema` and Django's `BaseCommand`/`CommandError`/`CommandParser`; `inspect_django_type` reuses the canonical MRO walk `types/converters.py::_field_output_type_for` (the same site `convert_field_output` uses) for file/image converter naming, plus `registry.iter_types`/`model_for_type`, `SCALAR_MAP`, `BigInt`, `DjangoType`, and `utils/strings.snake_case`.
- **New helpers considered.** A shared "resolve-then-validate" wrapper spanning both commands — rejected: divergent post-import validation contracts (`Schema` instance vs `DjangoType` subclass with finalized-definition checks) that a shared wrapper would obscure. Generalizing `import_or_command_error`'s caught-exception tuple into a parameter — rejected: all three call sites want exactly `(ImportError, AttributeError)` and `str(e)`, so a parameter would be dead surface. Folding the `OSError` write-rewrap into the import helper — rejected: different exception family, different operation.
- **Duplication risk in the current folder.** No cross-sibling repeated literal. `_imports.py` and `export_schema.py` report zero repeated literals; `inspect_django_type.py`'s within-file repeats (`__name__` ×2, `relation:` ×2, `no (list)` ×2) are intentional family self-naming dispositioned in its per-file artifact and recur in no sibling, so there is no folder-level literal to hoist. The two commands' module/class docstrings and `handle` signatures are parallel by Django convention, not copy-paste drift.

### Other positives

- **One-way, acyclic import direction.** `_imports.py` imports only stdlib (`collections.abc`, `typing`) and `django.core.management.base.CommandError` — zero first-party / zero sibling imports, so it is a true leaf. Both commands import `_imports` at module top; neither command imports the other (the `inspect_django_type` docstring mention of `export_schema` is prose, not an import). `export_schema`'s first-party surface is only the helper; `inspect_django_type`'s first-party imports (`registry`, `scalars`, `types.base`, `types.converters`, `utils.strings`) all point inward to shared package modules, never sideways to a sibling or outward to a consumer. No circular-import risk and no import-time side effects in the folder.
- **Consistent naming and error-handling shape.** Both commands subclass `BaseCommand` with the same `add_arguments(self, parser: CommandParser) -> None` / `handle(self, *args, **options) -> None` shape, read the required positional via direct `options[...]` index (always argparse-populated) and the optional flag via `options.get(...)`, and surface every consumer-facing failure as `CommandError` with a concrete, recovery-oriented message rather than a raw traceback (bad import path, wrong symbol type, ambiguous/unknown bare name, unfinalized/abstract definition, empty `--path`, file-write `OSError`, unresolved forward-ref). The shared helper guarantees the import-failure message shape is identical across both commands.
- **`__init__.py` export shape is correct.** The folder `__init__.py` is a single module docstring with no symbols and no `__all__` — appropriate for a Django `management/commands/` package, where command discovery is by module filename (`export_schema`, `inspect_django_type`), not by package re-export. An `__all__` or eager import here would be dead weight (and an eager import would pull `inspect_django_type`'s first-party imports at package-import time for no benefit). The private `_imports.py` helper is deliberately leading-underscore with no `__all__`, so Django does not mistake it for a command module.
- **Comment consistency.** Both commands carry accurate module/class/method docstrings keyed to the real error messages; `inspect_django_type`'s inline `_scalar_row` comment block correctly explains the file/image converter naming via `_field_output_type_for` (not `SCALAR_MAP`). No stale TODO anchors in any file (every sibling overview reports 0 TODO comments).

### Summary

The `management/commands/` folder is in a clean, fully-DRY state with no cross-file findings. The only duplication the namespace ever carried — the import-failure rewrap tail across the two commands — is already consolidated into the leaf helper `_imports.py::import_or_command_error`, consumed from all three former sites with no straggler left (grep-confirmed: the tail survives only inside `_imports.py`). Imports are strictly one-way and acyclic (`_imports` is a stdlib/Django-only leaf; both commands depend on it, neither on the other; `inspect_django_type`'s first-party imports all point inward), there are no cross-sibling repeated literals, the two commands share a consistent Django `BaseCommand` shape and `CommandError`-everywhere error contract, and the package `__init__.py` correctly carries no exports. All three in-scope siblings are `verified` this cycle and the whole-folder diff is empty versus both the cycle baseline `5d3bf1dd` and HEAD, so this is a genuine no-source-edit folder pass. No High / Medium / Low findings; nothing forwarded to the project pass.

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
- Folder pass, shape #5 (no-source-edit). Whole-folder `git diff 5d3bf1dde1b614ce3b8f49c24628e83ac1793ef6 -- django_strawberry_framework/management/commands/` is empty AND `git diff HEAD -- …` is empty (both 0 lines, re-confirmed after the two ruff runs). All three in-scope siblings (`_imports.py`, `export_schema.py`, `inspect_django_type.py`) are `Status: verified` this cycle.
- All severities `None.`; no behaviour-changing finding; nothing forwarded to the project pass (`rev-django_strawberry_framework.md`).
- DRY single `None —` bullet: the import-rewrap consolidation into `_imports.py::import_or_command_error` is the namespace's already-landed DRY resolution, not a pending candidate. Grep-confirmed the rewrap tail `except (ImportError, AttributeError)` survives only inside `_imports.py` (the function body line 32 + the docstring quote line 6) — no NEW duplication after the resolution. The prior-cycle artifact at this path recorded the original act-now hoist; that work is in HEAD now and this cycle is overwriting it cleanly as a fresh shape #5 (carried calibration: overwrite a stale prior-cycle W2/W3 record cleanly, do not retain old blocks).
- Cross-file checks performed: (1) import direction one-way/acyclic — `_imports.py` imports zero siblings (stdlib + `django.core.management.base.CommandError` only); both commands import `_imports`; neither command imports the other (the `inspect_django_type` `export_schema` mention is docstring prose). (2) Cross-sibling repeated literals — none span two files; `_imports`/`export_schema` report none, `inspect_django_type`'s 3 within-file repeats are intentional and file-scoped. (3) `__init__.py` export shape — single module docstring, no `__all__`, correct for a Django command package.
- No GLOSSARY-only fix in scope. GLOSSARY documents the two commands (`export_schema` ~line 1226, `inspect_django_type` ~line 1234) but correctly carries no folder-level or `_imports` entry; the sibling per-file passes confirmed no drift, and no folder-pass drift surfaced.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits — across all four files the docstrings/comments are accurate and consistent: `_imports.py` documents the three-site duplication it resolves and the cause-chaining contract; both command `handle` docstrings describe their branches and quote real error messages; `inspect_django_type.py`'s `_scalar_row` inline block correctly ties file/image converter naming to `_field_output_type_for`. No stale TODOs (every sibling overview: 0 TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — zero edits this cycle (folder-pass review only; whole-folder diff empty vs both baseline and HEAD). Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` (silent on CHANGELOG for this folder-pass item), no entry is produced.

---

## Verification (Worker 3)

### Logic verification outcome
All High / Medium / Low are `None.` and genuine, not lazy. The folder's only headline claim is the already-landed DRY resolution; I re-derived it independently rather than trusting the prose:

- **Rewrap-tail straggler grep (load-bearing).** `grep -rn "except (ImportError, AttributeError)" django_strawberry_framework/management/` returns ONLY `_imports.py` (line 32 body + line 6 docstring quote). The byte-identical catch-and-rewrap tail survives at no call site → the extraction into `_imports.py::import_or_command_error` is complete with no straggler, so the single DRY-`None` ("this is the already-resolved consolidation, no NEW duplication") is correct, not a missed forward.
- **Three sites, two importers, one contract.** `grep -rn import_or_command_error` confirms `export_schema.py:38` (`import_module_symbol`), `inspect_django_type.py:107` (`import_module_symbol`, value discarded — import-for-side-effect) and `:129` (`import_string`, returned). All pass zero-arg callables matching the helper's `Callable[[], T] -> T`; the helper preserves `__cause__` via `from e` and surfaces `str(e)`. The rejected generalize-the-caught-tuple candidate is sound: all three sites want exactly `(ImportError, AttributeError)` + `str(e)`.
- **Import direction one-way / acyclic.** `_imports.py` imports only `collections.abc.Callable`, `typing.TypeVar`, and `django.core.management.base.CommandError` — a true stdlib/Django leaf, zero siblings. Both commands import `_imports` at module top; neither imports the other (the `inspect_django_type` `export_schema` reference is docstring prose, confirmed by grep on the import block). `inspect_django_type`'s first-party imports (`registry`, `scalars`, `types.base`, `types.converters`, `utils.strings`) all point inward to shared package modules — no sideways sibling edge, no cycle.
- **`__init__.py` correctly empty.** `cat` confirms a single module docstring, no symbols, no `__all__` — correct for a Django command package (discovery is by module filename), and `_imports.py`'s leading underscore keeps Django from treating the helper as a command module.
- **No cross-sibling repeated literal.** The within-file repeats in `inspect_django_type.py` are file-scoped and dispositioned in its per-file artifact; nothing spans two siblings worth folding. The two commands' parallel `BaseCommand` shape / `handle` signatures are Django convention, not copy-paste drift.

### DRY findings disposition
Single DRY bullet is the justified `None —`: the namespace is already at its DRY shape, the import-rewrap is single-sourced in `_imports.py`, and the two rejected cross-family candidates (shared resolve-then-validate wrapper; folding the `OSError` write-rewrap into the import helper) are correctly rejected — divergent post-import validation contracts and a distinct exception family/operation. Nothing forwarded to the project pass.

### Temp test verification
- None used — no-source-edit folder pass; the verification is grep + read against live source, no behavior to pin.
- Disposition: n/a.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the management/commands/ folder-pass checkbox in `docs/review/review-0_0_11.md`.

Shape #5 gates all pass: whole-folder `git diff` empty vs both baseline `5d3bf1dd` and HEAD; folder absent from the baseline owned-paths `--stat` (the only dirty paths are `optimizer/field_meta.py`, `optimizer/walker.py`, `utils/relations.py` — non-target sibling / AGENTS.md #33 concurrent work, informational only since the target diff is clean); each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.`; all severities `None.` with no GLOSSARY-only fix; Changelog `Not warranted` cites BOTH AGENTS.md #21 and the active plan's silence; `uv run ruff format --check` (4 files already formatted) and `uv run ruff check` both pass.
