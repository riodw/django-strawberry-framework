# DRY review: folder `django_strawberry_framework/management/commands/`

Status: verified

## System trace

`management/commands/` is the Django `manage.py` command package for this
framework. Folder shape:

- `__init__.py` — package docstring only (command discovery is Django's
  `management/commands/` layout).
- `_imports.py` — shared CLI import policy: `ImportError` / `AttributeError` →
  `CommandError`, absolute-module-path guards, and the two importer flavors
  (Strawberry `module[:symbol]` vs Django dotted object path).
- `export_schema.py` — resolve a schema selector, require
  `strawberry.Schema`, emit SDL to stdout or `--path`.
- `inspect_django_type.py` — optional `--schema` import for register/finalize
  side effects + schema naming config; resolve a `DjangoType` by dotted path or
  bare registry name; print the per-field resolution table.

Connected behavior re-traced for this folder pass (not inherited as proven):
both commands' `handle` / `_resolve_type` paths; `_imports` helpers and
`tests/management/test_imports.py`; package + fakeshop command suites
(`tests/management/test_export_schema.py`,
`tests/management/test_inspect_django_type.py`,
`examples/fakeshop/tests/test_export_schema.py`,
`examples/fakeshop/tests/test_inspect_django_type.py`); parent
`management/__init__.py` (docstring-only namespace). Grepped the package for
`import_module_symbol_or_command_error`, `import_string_or_command_error`,
`import_or_command_error`, `default_symbol_name="schema"`, and
`raise CommandError(str(e))` sites.

Folder-level axes: duplicated import/`CommandError` policy across the two
commands, competing schema-load helpers, inconsistent public CLI flavors, and
lifecycle work (resolve → validate → act) repeated at several phases.

## Verification

- Item-scoped baseline `a00567f0089b7872f0f15fae2af4bea7142bf536`: working tree
  matched baseline for `django_strawberry_framework/management/commands/` at
  pass start (empty item-scoped diff). Concurrent dirty paths outside this item
  left untouched. Plan checkbox not edited.
- Re-read all four command-package sources end-to-end. Confirmed production
  consumers of `_imports` are only the two commands (three call sites: export
  schema positional, inspect `--schema`, inspect dotted type).
- Compared contracts: export requires a live `Schema` instance for
  `print_schema`; inspect treats the selector as an import-for-side-effect plus
  optional `config` / `name_converter` / `scalar_map` getattr chain and must
  still work when the operator's goal is registry finalization, not SDL export.
- No production edit warranted; no focused pytest (zero-edit). No full pytest.
  Item-scoped diff remains empty aside from this artifact.

## Opportunities

None — the only folder-visible responsibility that once crossed command files
(import failure → `CommandError`, plus absolute-path validation for both
selector flavors) already has a single owner in
`management/commands/_imports.py`. Both commands call that owner; no second
rewrap implementation remains in either command body. Remaining parallels are
distinct CLI contracts or intentional test fixtures, not a second encoding of
one rule.

### Rejected / deferred (re-proved)

1. **Bake `default_symbol_name="schema"` into a schema-only
   `import_schema_symbol_or_command_error`.** Both production call sites pass
   that kwarg, and `_validate_absolute_module_path` already labels failures
   `"schema selector"`. Re-proved: the shared rule (selector parse, absolute-path
   guard, `ImportError`/`AttributeError` → `CommandError`, Strawberry
   `import_module_symbol`) already lives in
   `_imports.import_module_symbol_or_command_error`. The kwarg is call-site
   documentation of the CLI default symbol, not a second implementation. A
   one-line alias would hide that default without moving any ownership boundary.
   Rejected.

2. **Shared post-import `Schema` resolve helper used by both commands.**
   `export_schema` must `isinstance(..., Schema)` before `print_schema`.
   `inspect_django_type` must not: `--schema` exists to register/finalize and
   supply naming config via `getattr`, and a non-`Schema` import that still
   runs registration must not be rejected by an export-shaped guard. Distinct
   post-import contracts. Rejected.

3. **Fold `OSError` → `CommandError` (export `--path` write) into
   `import_or_command_error`.** Same `raise CommandError(str(e)) from e` shape,
   different exception family and operation (filesystem write vs symbol import).
   Folding would force a mode flag or broadened catch that obscures the import
   contract pinned by `tests/management/test_imports.py`. Rejected.

4. **Shared `BaseCommand` / argparse mixin for schema arguments.** Export takes
   a required positional `schema`; inspect takes an optional `--schema` beside a
   positional `type`. Spec-pinned CLI shapes, not one duplicated option layout.
   Rejected.

5. **Hoist package `_make_test_module` across
   `test_export_schema` / `test_inspect_django_type` (and `_make_module` in
   `test_imports`).** Same monkeypatch pattern, independent suites that must
   stay legible when one command's tests change. Intentional test repetition per
   `AGENTS.md`. Rejected.

6. **Parameterize or rename the hardcoded `"schema selector"` label on the
   generic-looking `import_module_symbol_or_command_error`.** Mild API/name
   tension only: every current caller is a schema selector, so the label matches
   behavior. Not a duplicated responsibility across commands. Deferred — only
   revisit if a non-schema `import_module_symbol` management path appears.

## Judgment

Zero-edit. The commands folder is already at its DRY shape: `_imports` owns the
cross-command import/`CommandError` policy; each command owns its distinct
resolve → validate → emit lifecycle. Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced `management/commands/` as one component from source (all four
modules end-to-end), parent `management/__init__.py`, both command `handle` /
`_resolve_type` paths, `_imports` helpers, package + fakeshop command suites,
and `utils/imports.py`. Did not treat Worker 1 findings as proven.

**Scoped diff.** `git diff a00567f0089b7872f0f15fae2af4bea7142bf536 --
django_strawberry_framework/management/commands/` is empty (0 bytes). Working-
tree dirt vs HEAD on `inspect_django_type.py` (`_is_relay_shaped` consume)
matches that baseline and was left untouched — concurrent WIP, not a folder-
item production edit. No new production edits in this pass.

**Ownership re-check.** Grep for `import_module_symbol_or_command_error`,
`import_string_or_command_error`, `import_or_command_error`,
`default_symbol_name="schema"`, `print_schema`, `isinstance(..., Schema)`, and
`raise CommandError(str(e))`: the only cross-command shared rule
(import/`AttributeError` → `CommandError` + absolute-path guards for both
selector flavors) lives solely in `_imports.py`. Production callers are exactly
the three documented sites (export positional, inspect `--schema`, inspect
dotted type). `print_schema` / Schema-instance guard exist only in
`export_schema`. Inspect `CommandError`s are type/registry/finalize/UNRESOLVED
diagnostics. `utils/imports.py` is soft-dep / strict / install-hint — no
`CommandError`. Only two `class Command(BaseCommand)` in the package.

**Challenged rejected candidates (required).**

1. **Schema-only `import_schema_symbol_or_command_error` alias.** Still
   rejected. Both sites already call the shared owner with
   `default_symbol_name="schema"`. An alias would rename the call without
   moving any rule out of `_imports`. Holds.

2. **Shared post-import `Schema` resolve helper.** Still rejected. Export must
   `isinstance(..., Schema)` before `print_schema`. Inspect imports `--schema`
   for register/finalize + optional `config` / `name_converter` / `scalar_map`
   via `getattr` and must accept a non-`Schema` import that still runs
   registration. Distinct post-import contracts. Holds.

3. **Fold `OSError` → `CommandError` into `import_or_command_error`.** Still
   rejected. Sole CLI write site; filesystem vs import exception families;
   broadening the catch would obscure the import contract pinned by
   `tests/management/test_imports.py`. Holds.

4. **Shared `BaseCommand` / argparse mixin for schema arguments.** Still
   rejected. Export required positional `schema` vs inspect optional `--schema`
   beside positional `type` are spec-pinned CLI shapes, not one duplicated
   option layout. Holds.

5. **Hoist `_make_test_module` / `_make_module` across command test suites.**
   Still rejected. Identical monkeypatch shape, independent command contracts;
   intentional test repetition per `AGENTS.md` / DRY.md. Holds.

6. **`"schema selector"` label on generic-looking
   `import_module_symbol_or_command_error`.** Still deferred. Mild API/name
   tension only; every current caller is a schema selector. Not a duplicated
   responsibility across commands. Revisit only if a non-schema
   `import_module_symbol` management path appears.

**Missed consolidations.** None. No second encoding of the cross-command
import/`CommandError` policy; remaining parallels are distinct CLI contracts
or intentional test fixtures. Zero-edit stands.
