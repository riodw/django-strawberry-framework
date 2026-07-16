# DRY review: folder `management/`

Status: verified

## System trace

`management/` is the Django discovery root for this package's `manage.py`
commands. The parent marker (`management/__init__.py`) exists so
`INSTALLED_APPS` → `DjangoStrawberryFrameworkConfig` can resolve
`management/commands/`; it owns no runtime policy. All behavior lives under
`commands/`:

- `_imports.py` — CLI path resolution and `ImportError`/`AttributeError` →
  `CommandError` translation (Strawberry `module[:symbol]` selectors and
  Django dotted object paths), plus absolute-path guards.
- `export_schema.py` — resolve a schema selector, require
  `strawberry.Schema`, emit SDL to stdout or `--path`.
- `inspect_django_type.py` — optional `--schema` import for register/finalize
  + naming config, resolve a `DjangoType` (dotted path or bare registry
  name), print the per-field resolution table by reading finalized
  introspection surfaces (not re-deriving types).

Connected behavior examined: both command `handle` paths; package
`utils/imports.py` (soft/strict/optional import family); `apps.py` (discovery
only, no command policy); `registry` / `types.base` / `types.converters` /
`scalars` as inspect's read-only dependencies; `tests/management/` and
`examples/fakeshop/tests/test_{export_schema,inspect_django_type}.py`;
glossary entries for both commands; strawberry_django's upstream
`export_schema` (inline `import_module_symbol` + `isinstance` Schema, no
shared helper — our `_imports` is the local owner for the CLI error
contract).

Baseline item-scoped `git diff a501aae2… -- django_strawberry_framework/management/`
shows only concurrent in-flight work on `inspect_django_type.py`
(`_is_relay_shaped` adoption). Left untouched.

## Verification

- Re-read the full `management/` tree as one component (parent + `commands/`).
- Searched package-wide for `import_module_symbol`, `import_string`,
  `CommandError(str(`, `isinstance(..., Schema)`, `default_symbol_name`, and
  `class Command(BaseCommand)` — only the two package commands plus
  `_imports` own the CLI import/error contract; example-app commands are
  consumer tooling with distinct domains.
- Compared `utils/imports.py` vs `_imports.py`: same verb ("import") but
  opposite failure contracts (best-effort/`None`/install-hint vs always
  `CommandError` for operators). Merging would force mode flags.
- Compared post-import schema contracts: `export_schema` must have a
  `Schema` for `print_schema`; `inspect` uses the import for registration
  side effects and optional `.config` (falls back to default
  `NameConverter` / scalar map). They share selector syntax, not
  post-import validation.
- Confirmed Django skips `_`-prefixed modules under `commands/`
  (`_imports` is correctly private plumbing, not a discoverable command).
- No scratch test needed: ownership and contracts are visible from source
  and existing `tests/management/test_imports.py` coverage of the shared
  owner.

## Opportunities

None — the only cross-command responsibility in this tree (CLI selector /
dotted-path import → `CommandError`) already has a single owner in
`commands/_imports.py`. The parent marker adds no parallel policy. Remaining
similarities fail the same-responsibility / same-change-axis test (see
rejected candidates in Judgment).

## Judgment

Zero-edit. `management/` is a thin Django layout shell over an already
consolidated `commands/` component. Folder-level re-read does not surface a
second owner, a split lifecycle, or competing helper layers that the
commands integration did not already settle.

Strongest rejected / deferred candidates:

1. **Merge `utils/imports.py` with `management/commands/_imports.py`.**
   Soft/strict/optional package imports vs operator-facing `CommandError`
   translation. Different callers, different failure surfaces; a shared
   helper would need mode flags. Keep both.

2. **Bake `default_symbol_name="schema"` into a schema-only import wrapper
   (optionally with `isinstance(..., Schema)`).** Both call sites already
   go through `import_module_symbol_or_command_error`. An alias only renames
   the call; adding a Schema check would wrongly couple inspect's
   side-effect import to export's `print_schema` precondition. Reject.

3. **Require `isinstance(..., Schema)` on inspect `--schema`.** Improves
   typo DX slightly but changes a deliberate post-import contract
   (glossary/spec: import for finalize + naming config, not SDL export).
   Not the same responsibility as export's Schema guard. Reject.

4. **Lift `_imports.py` to `management/_imports.py`.** Pure packaging
   shuffle; Django discovery and the commands folder already treat `_`
   modules as private helpers. No ownership win. Reject.

5. **Generalize `CommandError(str(e)) from e` across import failures and
   `export_schema`'s `OSError` on `--path` writes.** Same syntactic shape,
   different domains (import vs filesystem). Folding IO into `_imports`
   obscures ownership. Reject.

## Independent verification (Worker 2)

Re-traced `management/` as one component from source: parent
`management/__init__.py` (docstring-only marker, no defs/imports),
`commands/__init__.py` (same), `_imports.py`, both command `handle` /
`_resolve_type` paths, `utils/imports.py`, `apps.py` (discovery only),
package + fakeshop command suites, and glossary entries for both commands.
Did not treat Worker 1 findings as proven. Did not concatenate the verified
`commands/` folder artifact.

**Scoped diff.** `git diff a501aae2b076b985c727a1c19481aab7b106eada --
django_strawberry_framework/management/` is empty (0 bytes). Working-tree
dirt vs HEAD on `inspect_django_type.py` (`_is_relay_shaped` consume) matches
that baseline and was left untouched — concurrent WIP, not a folder-item
production edit. No new production edits in this pass.

**Ownership re-check.** Parent marker owns no runtime policy. Grep for
`import_module_symbol_or_command_error`, `import_string_or_command_error`,
`import_or_command_error`, `default_symbol_name="schema"`, `print_schema`,
`isinstance(..., Schema)`, and `raise CommandError(str(e))`: the only
cross-command shared rule (import/`AttributeError` → `CommandError` +
absolute-path guards) lives solely in `commands/_imports.py`. Production
callers are exactly three sites (export positional, inspect `--schema`,
inspect dotted type). Schema-instance guard / `print_schema` exist only in
`export_schema`. Inspect `--schema` uses `getattr` for config /
name_converter / scalar_map with cold-path defaults. `utils/imports.py` is
soft-dep / strict / install-hint — no `CommandError`. Package
`class Command(BaseCommand)` count is two; `_`-prefixed `_imports` is not
Django-discoverable. Marker `__init__` files define no symbols.

**Challenged rejected candidates (required).**

1. **Merge `utils/imports.py` with `commands/_imports.py`.** Still rejected.
   Soft/`None`/install-hint vs always-`CommandError` for operators. Different
   callers and failure surfaces; a shared helper would need mode flags. Holds.

2. **Schema-only import wrapper (optionally with `isinstance(..., Schema)`).**
   Still rejected. Both sites already call the shared owner with
   `default_symbol_name="schema"`. An alias renames without moving ownership;
   baking in Schema-instance validation would couple inspect's side-effect
   import to export's `print_schema` precondition. Holds.

3. **Require `isinstance(..., Schema)` on inspect `--schema`.** Still
   rejected. Glossary/spec: import for finalize + naming config, not SDL
   export. Distinct post-import contract from export's Schema guard. Holds.

4. **Lift `_imports.py` to `management/_imports.py`.** Still rejected. Pure
   packaging shuffle; Django discovery and `_`-prefix privacy already place
   the helper correctly under `commands/`. No ownership win. Holds.

5. **Generalize `CommandError(str(e)) from e` across import and
   `export_schema` `OSError`.** Still rejected. Sole CLI write site;
   filesystem vs import exception families; broadening the catch would
   obscure the import contract pinned by `tests/management/test_imports.py`.
   Holds.

**Folder-level extras challenged.** Collapse/delete either package marker —
Django requires both `management/` and `management/commands/` packages;
neither carries policy. Re-export `Command` / `_imports` from parent —
conflicts with discovery-only role and no-public-Command-export posture.
Hoist test `_make_test_module` / `_make_module` across suites — intentional
test repetition; independent command contracts. Not consolidations.

**Missed consolidations.** None. Folder-level re-read surfaces no second
owner, split lifecycle, or competing helper layer beyond the already-
consolidated `_imports` owner. Zero-edit stands.
