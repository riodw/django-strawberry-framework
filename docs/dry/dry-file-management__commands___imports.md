# DRY review: `django_strawberry_framework/management/commands/_imports.py`

Status: verified

## System trace

The target owns CLI-facing import resolution for the two framework
`manage.py` commands: bad operator paths become `CommandError` with the
underlying failure preserved as `__cause__`, while non-import failures
(`ValueError` from a consumer module body, etc.) propagate unchanged.

Symbols:

- `import_or_command_error` — zero-arg-callable wrapper; catches only
  `(ImportError, AttributeError)` and re-raises `CommandError(str(e)) from e`.
- `_validate_absolute_module_path` — rejects empty / relative module paths
  before the underlying importer can raise `ValueError` / `TypeError`
  (outside the narrow catch).
- `import_module_symbol_or_command_error` — Strawberry `module[:symbol]`
  selectors via `strawberry.utils.importer.import_module_symbol`.
- `import_string_or_command_error` — Django dotted object paths via
  `django.utils.module_loading.import_string`, plus a bare-name guard
  (`rpartition` with no `.`).

Callers (production):

- `export_schema.py::Command.handle` —
  `import_module_symbol_or_command_error(..., default_symbol_name="schema")`.
- `inspect_django_type.py::Command.handle` — same selector helper for
  `--schema`.
- `inspect_django_type.py::Command._resolve_type` —
  `import_string_or_command_error` when the positional `type` contains `.`.

Proof / placement:

- Package unit coverage: `tests/management/test_imports.py` (wrapper
  contract, path guards, non-masking of `ValueError`).
- Command-level CLI contracts:
  `tests/management/test_export_schema.py`,
  `tests/management/test_inspect_django_type.py`,
  `examples/fakeshop/tests/test_export_schema.py`,
  `examples/fakeshop/tests/test_inspect_django_type.py`
  (not `test_query/` — these are management commands).

Baseline
`git diff 1bdb978391e09131c5eeae2286d552810030c306 -- …/_imports.py`
is empty; no concurrent edits touch this file.

## Verification

Searches:

- Package-wide `(ImportError, AttributeError)` → `CommandError` rewrap:
  only this module's `import_or_command_error` body.
- `raise CommandError(str(` in package source: this helper plus
  `export_schema.py::Command.handle` (`OSError` on `Path.write_text` —
  distinct exception family and operation).
- `import_string(` / `import_module_symbol(` in package source: wrappers
  here; `sets_mixins.py::LazyRelatedClassMixin.resolve_lazy_class` uses
  bare `import_string` with `ImportError` retry / propagate (schema-time
  lazy class resolution, not CLI).
- `utils/imports.py` family (`import_attr_if_importable`, `loaded_attr`,
  `import_attr`, `require_optional_module`): soft-dep / loaded-only /
  strict / install-hint contracts — none raise `CommandError`.

Executable probe (exception contracts of the underlying importers):

```text
import_module_symbol(":schema", …)     → ValueError: Empty module name
import_module_symbol(".rel:schema", …) → TypeError: package required…
import_module_symbol("sys:nope", …)    → AttributeError (needs catch)
import_string("schema")                → ImportError (bare path)
import_string("sys.nope")              → ImportError (Django wraps attr miss)
```

That is why absolute-path pre-validation exists (map empty/relative to
`CommandError`) and why the catch tuple includes `AttributeError`
(Strawberry missing-symbol path).

Rejected / deferred candidates:

1. **Merge into `utils/imports.py`.** Disproved: that module owns optional-
   dependency and internal deferred-import policy (`None` / propagate
   `ImportError` / install-hint `ImportError`). This module owns
   operator-facing `CommandError` translation for `manage.py`. Same
   verb (“import”) but different audience, failure mode, and change axis.
   A shared helper would need mode flags and couple soft-dep installs to
   CLI UX.
2. **Generalize `import_or_command_error` to catch caller-supplied
   exception tuples (absorb `export_schema` `OSError` rewrap).**
   Disproved: file-write failures and import failures are independent
   domains; parameterizing the exception tuple is a mode flag that
   obscures ownership. The `OSError` site belongs inline next to
   `write_text` (export_schema file review / folder pass).
3. **Share path validation or `import_string` wrapping with
   `sets_mixins.resolve_lazy_class`.** Disproved: filter/order lazy
   resolution intentionally lets `ImportError` propagate (and retries
   with a module prefix). CLI helpers must never silently fall back to
   registry lookup or relative resolution — different contract.
4. **Hoist helpers into `management/commands/__init__.py` or
   `management/__init__.py`.** Disproved: those markers are Django
   discovery packages with no re-export API; pulling command-import
   policy into package markers would invent a Python import surface the
   commands deliberately avoid. Deferred only as “not this file’s job.”
5. **Inline the wrappers back into the two commands.** Disproved: both
   commands already share selector resolution; `inspect_django_type`
   also needs dotted-path resolution. Removing the owner would
   reintroduce the byte-identical rewrap at multiple sites.

## Opportunities

None — the import→`CommandError` policy is already single-sited here;
callers use the typed wrappers; `utils/imports.py` and the export_schema
`OSError` rewrap are intentionally separate contracts. Item-scoped source
diff vs `ITEM_BASELINE` is empty.

## Judgment

Zero-edit. `_imports.py` is the correct narrow owner for management-
command import error translation. Strongest false friends are
`utils/imports.py` (soft-dep family) and the `OSError`→`CommandError`
tail in `export_schema` (I/O, not import). Ready for Worker 2.

## Independent verification (Worker 2)

Scoped diff vs `ITEM_BASELINE`
`1bdb978391e09131c5eeae2286d552810030c306` for
`django_strawberry_framework/management/commands/_imports.py` is empty.

Re-traced ownership: CLI import→`CommandError` translation for the two
`manage.py` commands. Production callers are only
`export_schema.py::Command.handle` and
`inspect_django_type.py::Command.handle` /
`_resolve_type`. Package-wide
`(ImportError, AttributeError)` → `CommandError` rewrap lives solely in
`import_or_command_error`. Absolute-path pre-validation is single-sited
in `_validate_absolute_module_path`.

Challenged rejected candidates (all held):

1. **Merge into `utils/imports.py`.** That module returns `None`,
   propagates `ImportError`, or raises install-hint `ImportError`. This
   module raises operator-facing `CommandError`. Same verb, different
   audience / failure mode / change axis; a merge needs mode flags.
2. **Generalize catch to absorb `export_schema` `OSError`.** Confirmed
   `CommandError(str(e)) from e` at `write_text` is file I/O, not
   import. Parameterizing the exception tuple would blur ownership.
3. **Share wrapping with `sets_mixins.LazyRelatedClassMixin.resolve_lazy_class`.**
   Confirmed bare `import_string` with `ImportError` retry via
   `bound_class.__module__` prefix — schema-time lazy resolution that
   must not become CLI `CommandError` or absolute-only policy.
4. **Hoist into `management/` / `commands/` `__init__.py`.** Both remain
   discovery package markers with no re-export API.
5. **Inline wrappers back into the two commands.** Would re-duplicate
   the shared selector path and the dotted-path path.

Executable probe of underlying importers matched the artifact
(`ValueError` / `TypeError` for empty/relative selectors;
`AttributeError` for Strawberry missing symbol; Django `import_string`
wraps attr miss as `ImportError`). Pre-validation + `AttributeError` in
the catch tuple remain justified.

Missed consolidation search: no second CLI import-rewrap site, no
parallel absolute-path guard, no stale bypass of the typed wrappers.
Zero-edit stands.
