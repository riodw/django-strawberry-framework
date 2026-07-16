# DRY review: `django_strawberry_framework/management/commands/export_schema.py`

Status: verified

## System trace

The target owns the `manage.py export_schema` CLI: resolve a Strawberry
`module[:symbol]` selector to a `strawberry.Schema`, render SDL via
`strawberry.printer.print_schema`, then either print those exact bytes to
stdout (`ending=""` so redirect matches `--path` / `print_schema`) or write
UTF-8 to `--path` (destructive, no parent-dir creation) and report success.

Symbols:

- `Command` — Django `BaseCommand` subclass.
- `Command.add_arguments` — positional `schema`; optional `--path`.
- `Command.handle` — import → `isinstance(..., Schema)` → `print_schema` →
  stdout / blank-path reject / file write + `OSError`→`CommandError`.

Dependencies already owned elsewhere:

- Selector import + absolute-path guards:
  `_imports.import_module_symbol_or_command_error` (shared with
  `inspect_django_type` `--schema`).
- SDL rendering: Strawberry `print_schema` (upstream, not reimplemented).

Callers / registration:

- Django discovers the command via
  `django_strawberry_framework.management.commands.export_schema` (app
  `management/commands/` layout). No Python import of `Command` in package
  production code; consumers invoke `manage.py export_schema` /
  `call_command`.

Proof / placement (AGENTS.md tiers):

- Package CLI contracts: `tests/management/test_export_schema.py`
  (selector errors, non-`Schema`, argparse bare `--path`, whitespace
  `--path`, stdout≡`--path`≡`print_schema`).
- Project / real schema: `examples/fakeshop/tests/test_export_schema.py`
  (`config.schema`, overwrite, missing parent dir, empty `--path`).
- Not `test_query/` — management command, not live GraphQL HTTP.

Baseline
`git diff 1815116758443e5b1b09a7664cf5b8b65250306a -- …/export_schema.py`
is empty; no concurrent edits touch this file.

## Verification

Searched package-wide for `print_schema`, `export_schema`,
`import_module_symbol_or_command_error`, `write_text`,
`must be an instance of strawberry.Schema`, `--path requires a non-empty`,
and `Wrote schema to`. Compared contracts against:

- `management/commands/_imports.py` (shared import owner);
- `management/commands/inspect_django_type.py` (sibling `--schema` import);
- `utils/imports.py` (different domain: optional / strict / loaded attrs —
  no CLI `CommandError` translation);
- upstream `strawberry_django/.../export_schema.py` (migration-parity
  ancestor; still inlines import try/except and lacks blank-path /
  `OSError` / stdout-byte / success-message contracts this package added);
- Strawberry CLI `export_schema` (Typer + `load_schema` + `--output`;
  different surface, not a second in-repo owner).

Rejected / deferred candidates:

1. **Extract `resolve_schema_or_command_error` (import + `isinstance Schema`).**
   Only `export_schema` requires a `Schema` instance.
   `inspect_django_type` imports `--schema` for registration / finalize side
   effects and reads `.config`; it must not share a Schema-guarded helper
   (would invent a false shared contract). One-caller helper rejected.

2. **Fold `OSError`→`CommandError` into `_imports.import_or_command_error`.**
   File I/O is not import resolution. Broadening the catch tuple would mix
   domains and invite masking unrelated failures. Leave the write-site
   try/except local. Deferred only if a second CLI write path appears with
   the same contract.

3. **Share `_make_test_module` across `test_export_schema` /
   `test_inspect_django_type`.** Same fixture shape, independent command
   contracts. DRY.md preserves intentional test repetition when behaviors
   stay independently legible; a shared conftest couples unrelated suites.

4. **Align further with strawberry-django / Strawberry CLI bodies.**
   External parity is intentional positioning, not in-repo duplication.
   Upstream still uses `nargs=1` / silent write / no blank-path guard;
   consolidating toward upstream would regress this package's contracts.

5. **Shared `default_symbol_name="schema"` constant.** Two call sites, one
   literal meaning "Strawberry default symbol". A named constant would not
   change ownership or drift risk.

No scratch experiment required — contracts are covered by permanent tests
and the sibling import owner is already single-sited.

## Opportunities

None — import/`CommandError` translation already lives in `_imports`; the
remaining handle body is this command's unique SDL emit and path I/O
lifecycle. Apparent parallels with `inspect_django_type`, upstream
export_schema, and test fixtures fail the shared-contract / change-together
test (see Verification).

## Judgment

Zero-edit. The file is a thin CLI adapter over a shared import helper and
Strawberry's printer. Ready for Worker 2.

## Independent verification (Worker 2)

Scoped diff vs
`1815116758443e5b1b09a7664cf5b8b65250306a` for
`django_strawberry_framework/management/commands/export_schema.py` is empty.
Independently re-traced `Command.handle` → `_imports` → `print_schema` →
stdout / blank-path / `write_text`+`OSError`, plus
`inspect_django_type` `--schema`, `utils/imports.py`, package + fakeshop
export tests, and upstream strawberry-django `export_schema`. Package-wide
search for `print_schema`, `export_schema`,
`import_module_symbol_or_command_error`, `write_text`, Schema-guard /
blank-path / success-message literals, and `ending=""` found no second
in-repo owner of the SDL emit or path I/O lifecycle.

Rejected candidates disposed:

1. **`resolve_schema_or_command_error`** — still only `export_schema` needs
   `isinstance(..., Schema)`. `inspect_django_type` imports for
   registration / finalize and reads `.config`; a Schema-guarded shared
   helper would invent a false contract. Holds.
2. **`OSError`→`CommandError` into `_imports`** — sole CLI write site; I/O
   is not import resolution. Broadening the import catch would mix domains.
   Holds.
3. **Shared `_make_test_module`** — identical shape in
   `test_export_schema` / `test_inspect_django_type`, but suites pin
   independent command contracts; DRY.md allows intentional test
   repetition. Holds.
4. **Upstream / Strawberry CLI body alignment** — external parity only;
   consolidating toward upstream would drop blank-path / `OSError` /
   stdout-byte / success-message contracts. Holds.
5. **`default_symbol_name="schema"` constant** — two call sites, same
   Strawberry default; a named constant would not change ownership or
   drift risk. Holds.

No missed consolidation: import/`CommandError` already single-sited in
`_imports` (verified sibling artifact); remaining handle body is this
command's unique SDL emit and path I/O. Zero-edit stands.
