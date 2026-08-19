# Spec: `export_schema` management command

Target release: `0.0.7`.
Status: shipped in `0.0.7` (2026-05-27) and archived under `docs/SPECS/`; card `DONE-022-0.0.7`. This document states the command's contract as it stands at `HEAD`.
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`Schema export management command`][glossary-schema-export-management-command], [`Django AppConfig`][glossary-django-appconfig], [`DjangoType`][glossary-djangotype], [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], [`finalize_django_types`][glossary-finalize-django-types]); [`KANBAN.md`][kanban] card `DONE-022-0.0.7`; shipped predecessor [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021] (the [`Django AppConfig`][glossary-django-appconfig] it landed is the entry point Django's `INSTALLED_APPS`-driven management-command discovery resolves through for this package); joint-cut policy spec [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] (Decision 10 — joint `0.0.7` cut, reused in [Decision 9](#decision-9--joint-007-cut) here).
Deliberation: the alternatives each Decision rejected, the five review revisions that shaped it, the seven risks it once tracked, and every claim it may no longer make live in its companion [`docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`][rationale]. This spec carries no chronology.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`Schema export management command`][glossary-schema-export-management-command] — the shipped surface this spec pins.
- [`Django AppConfig`][glossary-django-appconfig] — the entry point Django's `INSTALLED_APPS`-driven command discovery resolves through; see [Decision 1](#decision-1--module-location--no-public-export).
- [`DjangoType`][glossary-djangotype] — the consumer-facing type the exported SDL describes; not imported by the command but the reason the command exists.
- [`finalize_django_types`][glossary-finalize-django-types] — the consumer-owned synchronization point that must have run before the consumer's `schema = strawberry.Schema(...)` is constructed. The command does NOT call it (see [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — present on the consumer's `strawberry.Schema(...)` but not exercised at export time; SDL is the static type system, not a runtime execution.
- [`ConfigurationError`][glossary-configurationerror] — not raised by anything in this card; `CommandError` (Django) is the exclusive error class for export-time failures per [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface).

Project conventions to follow:

- [`AGENTS.md`][agents] — [`AGENTS.md`][agents] #"Test placement:" (package tests live under `tests/`, example-project non-HTTP tests under `examples/fakeshop/tests/`, no `__init__.py` under the two `examples/fakeshop/` test trees but package-test subdirectories like `tests/optimizer/` and `tests/types/` carry `__init__.py`); [`AGENTS.md`][agents] #"any line reachable via a real GraphQL query against fakeshop"; [`AGENTS.md`][agents] #"No pytest after edits"; [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands". **Note:** [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" prohibits [`CHANGELOG.md`][changelog] edits without explicit permission; [Slice 3](#implementation-plan) grants that permission for this card's `[0.0.7]` `### Added` append.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target.
- [`KANBAN.md`][kanban] — card-ID format; column movement at Slice 3.
- [`docs/TREE.md`][tree] — package layout; tests mirror source one-to-one. [`docs/TREE.md`][tree] #"`examples/fakeshop/tests/` — **Example-project tests, no HTTP `/graphql/`**" confirms `examples/fakeshop/tests/` is the canonical home for "management commands via `call_command`."

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Three slices total.

- [ ] Slice 1: Module + `Command` subclass
  - [ ] New flat package `django_strawberry_framework/management/` with a one-line module docstring `__init__.py` (empty marker).
  - [ ] New flat package `django_strawberry_framework/management/commands/` with a one-line module docstring `__init__.py` (empty marker).
  - [ ] New module `django_strawberry_framework/management/commands/export_schema.py` housing `Command(BaseCommand)` per [Decision 2](#decision-2--command-class-shape) — `help = "Export the GraphQL schema"`, positional `schema` (a single scalar dotted-path value, no `nargs`), optional `--path` (a value is required when the flag is given; no `nargs`), `handle(self, *args: object, **options: object) -> None` that (a) resolves the symbol via `import_module_symbol_or_command_error(options["schema"], default_symbol_name="schema")` per [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper), (b) raises `CommandError` when the resolved symbol is not a `strawberry.Schema` instance per [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface), (c) renders SDL via `strawberry.printer.print_schema(schema_symbol)` per [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema), (d) routes on `path is None` to a newline-suppressed `self.stdout.write(schema_output, ending="")` and returns, (e) rejects an empty or whitespace-only `--path` with `CommandError("--path requires a non-empty value")`, and (f) otherwise writes `pathlib.Path(path).write_text(schema_output, encoding="utf-8", newline="")` inside a `try` / `except (OSError, ValueError)` that re-raises as `CommandError`, then emits `self.style.SUCCESS(f"Wrote schema to {path}")`.
  - [ ] Shared import translation lives in `django_strawberry_framework/management/commands/_imports.py`, not inline in `handle()` (per [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper)). The helper validates the selector's module path before delegating resolution to Strawberry's importer unchanged.
  - [ ] `add_arguments` signed as `def add_arguments(self, parser: CommandParser) -> None:` (`parser: CommandParser` covers `ANN001`; `-> None` covers `ANN201`; `CommandParser` imported from `django.core.management.base`, verified to exist at `.venv/lib/python3.10/site-packages/django/core/management/base.py::CommandParser`).
  - [ ] `--path`'s `help` string is `"Write UTF-8 SDL to this file, overwriting it without prompting"` — the destructive-overwrite contract must be visible at `manage.py export_schema --help`, and the exact string is pinned by a test.
  - [ ] One-line method docstring on `add_arguments` (required by `D102`; pydocstyle convention is google per `pyproject.toml #"convention = \"google\""`). Suggested: `"""Register the positional schema argument and the optional --path flag."""`. Do NOT suppress with `# noqa: D102` — the docstring IS the root-cause fix per [`AGENTS.md`][agents] #"Always give the root-cause fix even when slower".
  - [ ] Method docstring on `handle` (required by `D102`) enumerating the three output branches: newline-suppressed stdout, empty-`--path` rejection, and the destructive UTF-8 file write. Do NOT suppress with `# noqa: D102`.
  - [ ] Do NOT implement a settings-backed default for `schema` (per [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias)).
  - [ ] Do NOT implement `--watch`, `--indent`, `--json`, a `dump_schema` / `print_schema` alias, or a JSON-introspection mode (per [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias)).
  - [ ] Do NOT re-export `Command` from `django_strawberry_framework/__init__.py` (per [Decision 1](#decision-1--module-location--no-public-export)). The class is import-time plumbing Django's command-discovery resolves through `INSTALLED_APPS`; consumers never write `from django_strawberry_framework.management.commands.export_schema import Command`.
  - [ ] One-line module docstring on `export_schema.py` (required by `D100`); one-line class docstring on `Command` (required by `D101`). Module docstring: `"""manage.py export_schema - print or write the GraphQL SDL for a Strawberry schema symbol."""`. Class docstring: `"""Export the GraphQL SDL for a strawberry.Schema symbol."""`. Do NOT suppress with `# noqa: D100` / `# noqa: D101`.
  - [ ] `management/__init__.py` and `management/commands/__init__.py` each carry a one-line module docstring (required by `D100`).
- [ ] Slice 2: Tests
  - [ ] New `tests/management/__init__.py` (empty marker; mirrors the `tests/optimizer/` / `tests/types/` shell per [`docs/TREE.md`][tree] #"Subdirectories carry an `__init__.py` shell to match the existing") plus a one-line module docstring (required by `D100`); the shipped text is `"""Package tests for django-strawberry-framework management commands."""`.
  - [ ] `tests/management/test_export_schema.py` holds the package tier: the selector-error, schema-validation, and CLI-contract surface enumerated in the [Test plan](#test-plan).
  - [ ] `tests/management/test_imports.py` holds the shared helper's own tier — every branch of `_imports.py`, including the two "does not swallow / does not mask" negative contracts.
  - [ ] `examples/fakeshop/tests/test_export_schema.py` holds the live tier: the command driven against the real `config.schema`, including the output branches whose failure modes only arise after a real schema has been imported, finalized, and rendered (per [Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query)). Do NOT add a file under `examples/fakeshop/test_query/`.
  - [ ] Tests exercise the command exclusively through `django.core.management.call_command`, never `Command().handle(...)` (per [Decision 8](#decision-8--tests-go-through-call_command-not-direct-handle)). Parser-shape assertions that read `Command().create_parser(...)` without invoking the command are permitted and are not `handle()` calls.
  - [ ] Package-internal test selectors use the **explicit `:symbol` form** (`test_module:schema`, `test_module:not_a_schema`) so no assertion depends on the `default_symbol_name` fallback by accident; the fallback is pinned deliberately by the live tier's bare `"config.schema"` selectors and at the helper.
- [ ] Slice 3: Promotion + docs
  - [ ] Flip [`Schema export management command`][glossary-schema-export-management-command] from `planned for 0.0.7` to `shipped (0.0.7)` in [`docs/GLOSSARY.md`][glossary]; update the Index table's status column at [`docs/GLOSSARY.md`][glossary] `#"[Schema export management command](#schema-export-management-command)"`; update the entry body to describe the shipped command shape.
  - [ ] Update [`docs/README.md`][readme]: **surgically remove the entire `- schema export management command` bullet** from the [`docs/README.md`][readme] #"**Coming in `0.1.0`**" section (`DONE-021-0.0.7` surgically removed only `, Django `AppConfig`` from that line; this card removes the remaining text in full and deletes the whole bullet). The shipped-list heading at [`docs/README.md`][readme] #"**Shipped today** (`0.0.7`):" already reads `**Shipped today** (`0.0.7`):`; no further heading change here.
  - [ ] Update [`docs/TREE.md`][tree]: (a) add the `management/` subtree to the **current on-disk layout** section under the `django_strawberry_framework/` tree (alphabetical position between `list_field.py` and `optimizer/`), with the `commands/__init__.py` + `commands/export_schema.py` children spelled out; (b) remove the `[alpha]` tag from the existing `management/` block in the **target package layout** section ([`docs/TREE.md`][tree] #"management/              # Django management commands"); (c) **surgically remove `, and the management command` from the current-on-disk-layout prose at [`docs/TREE.md`][tree] #"Every other module shown in the target package layout below"** — after Slice 3 the management command IS on disk, so the fragment self-contradicts; (d) add `tests/management/test_export_schema.py` (with sibling `__init__.py`) to the **current test-tree** section, **before `test_apps.py`** (alphabetical).
  - [ ] Update [`KANBAN.md`][kanban]: move the card to the Done column with the next available `DONE-NNN-0.0.7` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). The past-tense Done body summarizes the shipped scope.
  - [ ] Update [`CHANGELOG.md`][changelog]: **append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading per [Decision 9](#decision-9--joint-007-cut) — every `0.0.7` card under the joint cut appends to the same shared section).
  - [ ] No edits to [`README.md`][readme], [`GOAL.md`][goal], or [`TODAY.md`][today]: the command is `manage.py` plumbing, not a consumer-name surface change, and the fakeshop schema is unchanged by this card.
  - [ ] Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; per [Decision 9](#decision-9--joint-007-cut)): see [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] Decision 10. This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s version assertion.
  - [ ] Zero new public exports — the management command is import-time plumbing discovered through Django's `INSTALLED_APPS` machinery. `__all__` is unchanged.
  - [ ] Final gates:
    - [ ] `uv run ruff format .` passes.
    - [ ] `uv run ruff check --fix .` passes.
    - [ ] `uv run pytest --no-cov` (or scoped subset) passes; the explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov`; coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`), not this slice's.

## Problem statement

`django_strawberry_framework` shipped no `manage.py` surface before this card. The package's [`docs/README.md`][readme] #"**Coming in `0.1.0`**" block advertised a "schema export management command" while the implementation stayed deferred. Consumers who want to emit the GraphQL SDL — for client codegen (`graphql-codegen`, `graphql-cli`), CI schema-diffing, SDL-as-artifact in releases, or human-readable schema review — otherwise hand-roll a script that imports their schema and calls `strawberry.printer.print_schema`. Both reference packages ship the command: `strawberry-django` as `export_schema` (SDL, positional dotted path, optional `--path`), `graphene-django` as `graphql_schema` (JSON-by-default, `--schema` / `--out` / `--indent` / `--watch`, settings-backed defaults).

This card borrows the strawberry-django name and shape and deliberately does not borrow graphene-django's JSON / `--watch` / `--indent` / settings-backed defaults (see [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias) and [Borrowing posture](#borrowing-posture)).

Django's management-command discovery is directory-convention-based — `manage.py` walks `management/commands/` in every installed app — and involves no `AppConfig` method at all. The command therefore composes with the [`Django AppConfig`][glossary-django-appconfig] that [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021] landed without requiring anything of it.

## Current state

- `django_strawberry_framework/management/commands/export_schema.py` ships the command; `django_strawberry_framework/management/__init__.py` and `django_strawberry_framework/management/commands/__init__.py` are one-line-docstring markers. `django_strawberry_framework/management/commands/_imports.py` carries the shared import-translation helpers the command resolves through ([Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper)).
- `examples/fakeshop/config/schema.py` exposes a top-level `schema = DjangoSchema(query=Query, mutation=Mutation, config=strawberry_config(), extensions=[lambda: _optimizer])`; the live tests resolve it through both `"config.schema"` (exercising the `default_symbol_name` fallback) and `"config.schema:schema"`. `DjangoSchema` subclasses `strawberry.Schema` (`django_strawberry_framework/schema.py::DjangoSchema`), so the live tier is also what proves the isinstance guard admits a subclass rather than only the base class.
- `examples/fakeshop/config/schema.py` calls [`finalize_django_types()`][glossary-finalize-django-types] before constructing the schema. By the time the command imports `config.schema`, the finalize call has already run as a side effect of the module's top-level execution; this card does NOT call [`finalize_django_types()`][glossary-finalize-django-types] itself. See [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper).
- `tests/management/` carries `__init__.py`, `test_export_schema.py`, and `test_imports.py`; the live tier is `examples/fakeshop/tests/test_export_schema.py`. Nothing lives under `examples/fakeshop/test_query/` for this command.
- `tests/base/test_init.py` pins the package's `__all__` tuple; the command is not a public export ([Decision 1](#decision-1--module-location--no-public-export)) so that assertion is untouched.
- `pyproject.toml` #"strawberry-graphql>=0.316.0" pins the `strawberry-graphql` floor at `>=0.316.0`. The command constrains it in one direction only — the floor must be high enough that `strawberry.utils.importer.import_module_symbol` and `strawberry.printer.print_schema` exist — and every version in the supported range satisfies that, so raising the floor is never this card's concern. `strawberry.utils.importer.import_module_symbol` (signature `(selector: str, default_symbol_name: str | None = None) -> object`) and `strawberry.printer.print_schema` are both already in the dependency tree; the command adds no new dependency.

## Goals

1. Ship `django_strawberry_framework/management/commands/export_schema.py` containing `Command(BaseCommand)` with the strawberry-django-shaped signature: positional `schema` (a single scalar dotted path; default symbol name `"schema"`), optional `--path` (write UTF-8 SDL to that file, overwriting it without prompting). Absent `--path`, SDL goes to `self.stdout` with Django's default trailing newline suppressed.
2. Ship `django_strawberry_framework/management/__init__.py` and `django_strawberry_framework/management/commands/__init__.py` as one-line-docstring marker modules (required by `D100`; no additional content).
3. Ship the package test tier — `tests/management/__init__.py`, `tests/management/test_export_schema.py`, and `tests/management/test_imports.py` — covering the contracts pinned in the [Test plan](#test-plan): the output branches, the seven `CommandError` shapes the package tier owns, the `--path` help-string contract, and every branch of the shared `_imports.py` helper. The eighth shape, file-write failure, is the live tier's per [Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query).
4. Ship live fakeshop coverage in `examples/fakeshop/tests/test_export_schema.py` that drives the real `config.schema` end to end, asserting the SDL contains a known type from the `library` app (`"type BranchType"` — the `DjangoType` class is `BranchType` at `examples/fakeshop/apps/library/schema.py::BranchType`, and Strawberry emits the GraphQL type name from the class name unchanged).
5. Preserve [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands" by omitting `GRAPHENE.SCHEMA`-style settings-backed defaults.
6. Keep `__all__` unchanged. The command is import-time plumbing; consumers reach it via Django's `manage.py` machinery, not via `from django_strawberry_framework import …`.

## Non-goals

- JSON introspection output (graphene-django's default mode). See [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema).
- `--watch` mode (file-system watcher + Django autoreload). See [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias).
- Settings-backed default schema dotted path (graphene-django's `GRAPHENE.SCHEMA` / `SCHEMA_OUTPUT` / `SCHEMA_INDENT` analogs). See [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias).
- An `--indent` / SDL-formatting option. SDL is whitespace-agnostic; the formatting the consumer wants belongs in downstream tools (`prettier --parser graphql`, `graphql-cli`).
- A `dump_schema` / `print_schema` alias. See [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias).
- Auto-resolving the schema from settings (`SCHEMA = "config.schema"` style). The positional argument is the canonical input and is required.
- Auto-calling [`finalize_django_types()`][glossary-finalize-django-types] before printing. The consumer's `config/schema.py` (or equivalent) owns that call; resolving the schema symbol triggers the consumer's module-level imports, which already invoke it. See [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper).
- A re-export of `Command` from `django_strawberry_framework/__init__.py`. See [Decision 1](#decision-1--module-location--no-public-export).
- A [`Django AppConfig`][glossary-django-appconfig] hook for the command. Django's `manage.py` discovers commands by walking `management/commands/` directories in installed apps; no `AppConfig` method is involved.

## Borrowing posture

The two reference packages take opposite stances on the command's surface. The card borrows the shape from `strawberry-django` and explicitly does not borrow `graphene-django`'s feature creep.

### From `strawberry-django` — borrow the command shape, then harden it

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/management/commands/export_schema.py` (referenced from [`docs/TREE.md`][tree] #"└── export_schema.py").

Verified contents (38 lines):

```python
import pathlib

from django.core.management.base import BaseCommand, CommandError
from strawberry import Schema
from strawberry.printer import print_schema
from strawberry.utils.importer import import_module_symbol


class Command(BaseCommand):
    help = "Export the graphql schema"

    def add_arguments(self, parser):
        parser.add_argument("schema", nargs=1, type=str, help="The schema location")
        parser.add_argument(
            "--path",
            nargs="?",
            type=str,
            help="Optional path to export",
        )

    def handle(self, *args, **options):
        try:
            schema_symbol = import_module_symbol(
                options["schema"][0],
                default_symbol_name="schema",
            )
        except (ImportError, AttributeError) as e:
            raise CommandError(str(e)) from e

        if not isinstance(schema_symbol, Schema):
            raise CommandError("The `schema` must be an instance of strawberry.Schema")

        schema_output = print_schema(schema_symbol)
        path = options.get("path")
        if path:
            pathlib.Path(path).write_text(schema_output, encoding="utf-8")
        else:
            self.stdout.write(schema_output)
```

**Borrowed:** the command name and consumer-visible invocation (`manage.py export_schema <dotted.path> [--path FILE]`); positional `schema` rather than a named flag; SDL via `strawberry.printer.print_schema`; symbol resolution through `strawberry.utils.importer.import_module_symbol` with `default_symbol_name="schema"`; `CommandError` as the sole failure class; the `(ImportError, AttributeError)` narrow catch; the `isinstance(..., strawberry.Schema)` guard and its verbatim message `"The `schema` must be an instance of strawberry.Schema"`; the absence of `--watch`, `--indent`, and JSON.

**Diverged, deliberately.** The consumer-visible invocation is identical; the internals are not:

- **`help` string.** `"Export the GraphQL schema"` — Title Case `GraphQL` for repo prose consistency. Pinned by the test plan.
- **Docstrings and annotations.** The upstream carries none; this module carries the five ruff gates and the `: object` narrows enumerated in [Decision 2](#decision-2--command-class-shape).
- **No `nargs`.** Neither argument declares it. See [Decision 2](#decision-2--command-class-shape).
- **`--path` help string.** Rewritten to state the destructive-overwrite contract, and pinned by a test.
- **Byte-exact output.** The upstream's stdout branch appends Django's default trailing newline and its file write applies platform newline translation, so the two outputs differ. Both are suppressed here. See [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema).
- **A wider, attributable failure surface.** Empty / whitespace-only `--path`, write failures, and two malformed-selector shapes all surface as `CommandError` instead of a raw traceback or a silent fall-through. See [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface).
- **A success message.** `self.style.SUCCESS(f"Wrote schema to {path}")` after a successful write; the upstream exits silently.
- **Shared import translation.** The `try` / `except` wrapper lives in `_imports.py` and is shared with `inspect_django_type`. See [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper).

### From `graphene-django` — explicitly do not borrow

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/management/commands/graphql_schema.py` (referenced from [`docs/TREE.md`][tree] #"│   └── graphql_schema.py").

The upstream is 111 lines and ships a `--schema` named flag, `--out` with `-`-for-stdout and `.graphql` / `.json` extension inference, `--indent`, `--watch` via `django.utils.autoreload`, settings-backed defaults from `graphene_settings.SCHEMA` / `SCHEMA_OUTPUT` / `SCHEMA_INDENT`, and JSON-introspection as the default output mode. None is borrowed; each is settled in [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema), [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias), and [Out of scope](#out-of-scope-explicitly-tracked-elsewhere).

### Explicitly do not borrow

- strawberry-django's broader `extensions/` / `middlewares/` / `test/` modules that surround its `management/`. Those land card-by-card under their own specs (see [Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- A `graphql_schema` command name. Consumers migrating from strawberry-django run their `manage.py export_schema` muscle memory unchanged; aliasing is out per [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias).

## User-facing API

The shipped consumer surface adds one `manage.py` command (`export_schema`) discoverable through Django's `INSTALLED_APPS`-driven command-discovery (the consumer already lists `"django_strawberry_framework"` in `INSTALLED_APPS`). The `Command` class is NOT added to `__all__`.

### Default usage — write SDL to stdout

```bash path=null start=null
# Consumer's project root
uv run python manage.py export_schema config.schema
```

Resolves the dotted path `config.schema` to the consumer's top-level `strawberry.Schema` instance, calls `strawberry.printer.print_schema(schema)`, and writes the SDL to stdout with **no trailing newline appended** — the bytes handed to the stream are exactly `print_schema(schema)`'s, so a shell redirect captures the SDL and nothing else:

```bash path=null start=null
uv run python manage.py export_schema config.schema > schema.graphql
```

Newline suppression governs what the command emits, not what a shell then lands on disk: the redirect target receives the interpreter's own `sys.stdout` translation of those bytes, so on a platform whose native line separator is not LF the redirected file carries that separator. Use `--path` when the file's line endings must be LF everywhere — that branch disables translation at the write (see [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema)).

### Write SDL to a file

```bash path=null start=null
uv run python manage.py export_schema config.schema --path schema.graphql
```

Writes UTF-8 SDL to `schema.graphql` with newline translation disabled, then prints `Wrote schema to schema.graphql`. **The write is unconditionally destructive**: an existing target is replaced without prompting, and a missing parent directory is not created — it is a `CommandError`.

### Explicit `:symbol_name` suffix

When the schema symbol is not named `schema`:

```bash path=null start=null
uv run python manage.py export_schema config.module:my_schema
```

Strawberry's `import_module_symbol` accepts the `module.path:symbol_name` shape directly. The `default_symbol_name="schema"` argument applies only when no `:symbol_name` suffix is present.

### Error shapes

```bash path=null start=null
$ uv run python manage.py export_schema does.not.exist
CommandError: No module named 'does'

$ uv run python manage.py export_schema config.urls:urlpatterns
CommandError: The `schema` must be an instance of strawberry.Schema

$ uv run python manage.py export_schema .config.schema
CommandError: '.config.schema' is not a valid schema selector: relative module paths are not supported.

$ uv run python manage.py export_schema config.schema --path "   "
CommandError: --path requires a non-empty value

$ uv run python manage.py export_schema config.schema --path missing_dir/schema.graphql
CommandError: [Errno 2] No such file or directory: 'missing_dir/schema.graphql'

$ uv run python manage.py export_schema
usage: manage.py export_schema [-h] [--path PATH] ... schema
manage.py export_schema: error: the following arguments are required: schema
```

The non-`Schema` example uses `config.urls:urlpatterns`, the explicit-symbol selector pointing at the URL-configuration list, NOT bare `config.urls`. Verified at `examples/fakeshop/config/urls.py #"from config.schema import schema"` that `config/urls.py` declares `from config.schema import schema`, so resolving `config.urls` under the default symbol name `"schema"` would succeed against the real `strawberry.Schema`. `urlpatterns` is a list (verified at `examples/fakeshop/config/urls.py #"urlpatterns = ["`), so it exercises the isinstance branch.

The final shape is Django's argparse layer doing its job; the test plan asserts it so a future refactor cannot silently drop the requirement.

## Architectural decisions

### Decision 1 — Module location & no public export

**Module location.** The command lives at **`django_strawberry_framework/management/commands/export_schema.py`**, matching the [`docs/TREE.md`][tree] target layout at [`docs/TREE.md`][tree] #"management/              # Django management commands" and Django's `management/commands/` discovery convention.

Two `__init__.py` markers are required — Django's `manage.py` walks `<app>.management.commands.*` for every `<app>` in `INSTALLED_APPS`, so both `management` and `management.commands` must be importable Python packages:

- `django_strawberry_framework/management/__init__.py` — empty marker (one-line module docstring required by `D100`).
- `django_strawberry_framework/management/commands/__init__.py` — empty marker (one-line module docstring required by `D100`).

**Public-export surface.** `django_strawberry_framework/__init__.py` is NOT modified and `__all__` is unchanged. Django's command-discovery resolves the command through its dotted module path; consumers never import `Command`. The posture is symmetric with [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021] [Decision 3][spec-021-decision-3--no-public-export].

Deliberation moved to [the rationale companion][rationale-d1]: three rejected module-location and export alternatives.

### Decision 2 — `Command` class shape

The class declares exactly:

- `help = "Export the GraphQL schema"` — Title Case `GraphQL`; the test plan pins the exact string.
- `add_arguments(self, parser: CommandParser) -> None` registering (a) positional `"schema"` with `type=str, help="The schema location"` and **no `nargs`**, so `options["schema"]` is the scalar dotted path rather than a one-element list; (b) optional `"--path"` with `type=str, help="Write UTF-8 SDL to this file, overwriting it without prompting"` and **no `nargs`**, so argparse rejects a bare `--path` carrying no value.
- `handle(self, *args: object, **options: object) -> None` per [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper), [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema), and [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface).

**Dropping `nargs` is a contract, not a tidy-up.** On the positional argument it removes an index (`options["schema"][0]`) that bought nothing; on `--path` it closes a real hole. Under `nargs="?"` a bare `--path` with no following value parsed successfully and set `options["path"]` to `None` — indistinguishable from omitting the flag entirely, so a user who typed `--path` and forgot the filename silently got stdout. Without `nargs`, argparse raises at parse time.

Method signatures — pinned:

```python path=null start=null
from django.core.management.base import BaseCommand, CommandError, CommandParser
from strawberry import Schema
from strawberry.printer import print_schema

from django_strawberry_framework.management.commands._imports import (
    import_module_symbol_or_command_error,
)


class Command(BaseCommand):
    """Export the GraphQL SDL for a strawberry.Schema symbol."""

    help = "Export the GraphQL schema"

    def add_arguments(self, parser: CommandParser) -> None:
        """Register the positional schema argument and the optional --path flag."""
        parser.add_argument("schema", type=str, help="The schema location")
        parser.add_argument(
            "--path",
            type=str,
            help="Write UTF-8 SDL to this file, overwriting it without prompting",
        )

    def handle(self, *args: object, **options: object) -> None:
        """Resolve the dotted-path schema symbol and emit SDL.

        Docstring enumerates the three output branches; body per Decision 3
        (symbol resolution) / Decision 4 (SDL output) / Decision 5 (errors).
        """
```

Documentation and annotation requirements — every one gate-forced, none stylistic: `D100` (module docstring), `D101` (class docstring), `D102` (a docstring on `add_arguments` and on `handle`), `ANN001` (`parser: CommandParser`, imported from `django.core.management.base`), `ANN201` (`-> None` on both methods). The `: object` narrows on `*args` / `**options` are documentation-quality rather than gate-forced, and they stay. `# noqa: D102 / ANN001 / ANN201` suppressions are forbidden per [`AGENTS.md`][agents] #"Always give the root-cause fix even when slower".

`handle`'s docstring is not a one-liner: it enumerates the three output branches (newline-suppressed stdout, empty-`--path` rejection, destructive UTF-8 file write) plus the argparse-rejected bare `--path`. A reader of the docstring alone must be able to see all four.

Deliberately NOT declared: a `requires_system_checks` override, a `requires_migrations_checks` override, or a `stealth_options` override.

Deliberation moved to [the rationale companion][rationale-d2]: the shape justification, the per-rule provenance of each docstring and annotation, the reasoning behind the three non-declarations, and three rejected alternatives — one of which (`nargs=None`) is what now ships.

### Decision 3 — Symbol resolution through the shared `_imports` command helper

`handle()` resolves the consumer's dotted path through `django_strawberry_framework/management/commands/_imports.py::import_module_symbol_or_command_error`:

```python path=null start=null
schema_symbol = import_module_symbol_or_command_error(
    options["schema"],
    default_symbol_name="schema",
)
```

The helper does three things, in order:

1. **Validates the selector's module path** via `::_validate_absolute_module_path`, before any import is attempted. An empty module path (`""`, `":schema"`) and a relative module path (a leading `.`) each raise their own `CommandError` naming the offending value and the reason. Without this, `importlib` surfaces an unrelated internal error that does not tell the operator what they mistyped.
2. **Delegates resolution, unchanged**, to `strawberry.utils.importer.import_module_symbol(selector, default_symbol_name=...)`. Nothing here re-implements dotted-path parsing.
3. **Translates `ImportError` / `AttributeError` into `CommandError`** via `::import_or_command_error`, preserving the original as `__cause__` and using `str(e)` as the message.

Behavior:

- `"config.schema"` → resolves the `config.schema` module attribute named `schema` (the `default_symbol_name` fallback).
- `"config.module:my_schema"` → resolves the `config.module` module attribute named `my_schema`.
- `"does.not.exist"` → `ImportError` → `CommandError` per [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface).
- `"config.module:does_not_exist"` → `AttributeError` → `CommandError`.
- `""` / `":schema"` / `".config.schema"` → rejected before import, with a selector-specific message.

**The helper is shared, and that is why it exists.** `_imports.py` also serves `inspect_django_type` (card `DONE-029-0.0.9`), whose positional argument is a Django dotted object path rather than a Strawberry selector; `::import_string_or_command_error` is its sibling entry point over `django.utils.module_loading.import_string`. Both share `::import_or_command_error` and `::_validate_absolute_module_path`. Any third command needing the same translation extends this module rather than re-inlining a `try` / `except`.

**No auto-call to [`finalize_django_types()`][glossary-finalize-django-types].** The consumer's `config/schema.py` (or equivalent) calls it before constructing the schema; resolving the dotted path triggers the consumer's module-level imports, which run the finalize call as a side effect. Adding a `finalize_django_types()` call in `handle()` would either be silently redundant (the consumer's module already ran it) or — if the consumer's schema module deferred finalization to a function — would call it too early, before the consumer's imports are complete.

Deliberation moved to [the rationale companion][rationale-d3]: the delegation justification, the second-consumer trigger for the extraction, and three rejected alternatives (hand-rolled resolution, `import_string` for this command, a defensive `finalize_django_types()`).

### Decision 4 — SDL output via `strawberry.printer.print_schema`

`handle()` renders SDL with `print_schema(schema_symbol)` and then routes on three branches:

```python path=null start=null
schema_output = print_schema(schema_symbol)
path = options.get("path")
if path is None:
    # Match ``Path.write_text`` / ``print_schema`` bytes exactly: Django's
    # OutputWrapper defaults ``ending="\n"``, which would diverge stdout
    # from ``--path`` by a trailing newline and break redirect-vs-file diffs.
    self.stdout.write(schema_output, ending="")
    return
if not isinstance(path, str) or not path.strip():
    raise CommandError("--path requires a non-empty value")
try:
    pathlib.Path(path).write_text(schema_output, encoding="utf-8", newline="")
except (OSError, ValueError) as e:
    raise CommandError(str(e)) from e
self.stdout.write(self.style.SUCCESS(f"Wrote schema to {path}"))
```

**The byte-identity contract is the load-bearing part.** Three byte sequences must be equal for any schema: what the command writes to `self.stdout`, what it writes to the `--path` file, and what `print_schema(schema)` returns. Two defaults would break it and both are suppressed explicitly:

- Django's `OutputWrapper.write` defaults `ending="\n"`, so the stdout branch passes `ending=""`. Without it, what the command writes to `self.stdout` differs from what it writes to the `--path` file by exactly one trailing byte, and a consumer diffing the two forms in CI sees a spurious change.
- `pathlib.Path.write_text` defaults to platform newline translation, so the file branch passes `newline=""`. Without it, a platform whose native newline is not LF rewrites every line ending in the SDL.

Neither kwarg is stylistic. A maintainer who deletes either silently breaks a contract the test plan asserts.

**The two suppressions do not reach the same place, and the contract is scoped accordingly.** `newline=""` reaches the bytes on disk: the `--path` file carries the SDL's LF line endings unchanged on every platform. `ending=""` reaches only the string handed to `self.stdout` — `django.core.management.base.OutputWrapper.write` concatenates `ending` and passes the result to the wrapped stream unchanged, so a shell redirect of the stdout form is still subject to the interpreter's own `sys.stdout` newline translation and receives the platform separator wherever that is not LF. The three-way equality above is therefore a statement about the three byte sequences the command *emits*; only the `--path` form is a guarantee about the bytes a file receives on every platform. Doc text quoting this contract states the three emitted byte sequences, never an unqualified cross-platform equivalence between `manage.py export_schema … > out.graphql` and `--path out.graphql`.

**Routing is on `path is None`, not on truthiness.** `--path` omitted and `--path ""` are different inputs and must not collapse: the first means "write to stdout", the second means "the user gave a flag with no usable value". A truthiness test conflates them and sends the second silently to stdout.

**A successful write reports.** `self.style.SUCCESS(f"Wrote schema to {path}")` matches Django's convention for a command that produces a side effect; without it the user gets no in-terminal signal that the write happened.

**`self.stdout.write`, never `print(...)`.** `call_command(..., stdout=captured)` redirects `self.stdout` but does NOT redirect `sys.stdout`, so a `print(...)` form is uncapturable without monkey-patching and the test plan could not assert on it.

**UTF-8 on the file write** matches the upstream and avoids platform-specific locale surprises.

Deliberation moved to [the rationale companion][rationale-d4]: the `print_schema` justification, the commit-by-commit history of how the byte-identity contract accreted, and three rejected alternatives (`--json`, `--indent`, `print(...)`).

### Decision 5 — `CommandError` is the command's only failure surface

**Every way this command can fail reaches the operator as Django's `CommandError`** — never [`ConfigurationError`][glossary-configurationerror], never a custom exception, never a raw traceback. There are eight shapes, grouped by the layer that raises them.

**Pre-`handle()`, from Django's argparse layer (two).** The relevant class is `django.core.management.base.CommandParser`, a subclass of `argparse.ArgumentParser` whose `error()` is overridden:

```python path=null start=null
def error(self, message):
    if self.called_from_command_line:
        super().error(message)        # -> argparse.ArgumentParser.error -> SystemExit(2)
    else:
        raise CommandError("Error: %s" % message)  # <- the call_command path
```

When `call_command(...)` constructs the parser, `called_from_command_line` defaults to `False`, so `CommandParser.error()` raises `CommandError` **directly** — no `SystemExit` is involved anywhere on that path. The `SystemExit(2)` branch is taken only when `manage.py` runs the command from a shell. Verified against `.venv/lib/python3.10/site-packages/django/core/management/base.py::CommandParser`.

1. **Missing positional `schema`.**
2. **`--path` given with no following value.** Reachable only because [Decision 2](#decision-2--command-class-shape) drops `nargs="?"`.

Both are the load-bearing reason [Decision 8](#decision-8--tests-go-through-call_command-not-direct-handle) requires `call_command`: a direct `Command().handle(...)` call skips argparse entirely, so neither contract would be exercised.

**Selector validation, before any import (two)** — raised by `::_validate_absolute_module_path` in `_imports.py` per [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper):

3. **Empty module path** — `""` or `":schema"`. Message: `"<value>" is not a valid schema selector: the module path is empty.`
4. **Relative module path** — a leading `.`. Message: `"<value>" is not a valid schema selector: relative module paths are not supported.`

**Symbol resolution (one):**

5. **Unimportable dotted path** — `import_module_symbol` raises `ImportError` (module not found) or `AttributeError` (module loads, attribute absent). Both are re-raised as `CommandError(str(e)) from e`, so the original stays reachable through `__cause__`.

**Post-resolution (one):**

6. **Resolved symbol is not a `strawberry.Schema` instance** — `isinstance(schema_symbol, strawberry.Schema)` fails. Raises `CommandError("The `schema` must be an instance of strawberry.Schema")`, verbatim from the upstream wording; the backticks around `schema` are deliberate and the test plan pins the string.

**Output (two):**

7. **`--path` empty or whitespace-only** — `not isinstance(path, str) or not path.strip()`. Raises `CommandError("--path requires a non-empty value")`. The `.strip()` is deliberate: `--path "   "` is as unusable as `--path ""`.
8. **File-write failure** — `pathlib.Path(path).write_text(...)` raises `OSError` (missing parent directory, permission denied, target is a directory) or `ValueError` (a path `pathlib` itself rejects, such as an embedded null byte). Both are caught and re-raised as `CommandError(str(e)) from e`.

**The catches stay narrow, and that is a contract of its own.** `(ImportError, AttributeError)` around resolution and `(OSError, ValueError)` around the write are deliberately not `except Exception`: a `KeyError` inside the consumer's `Schema(...)` constructor, or a `ValueError` raised by the consumer's own module body, must propagate as itself rather than be relabelled a command failure. The test plan pins both non-swallowing contracts explicitly.

**Error-message wording — pinned:**

- `CommandError(str(e))` for the resolution and write cases — defers to the underlying message (`"No module named 'does'"`, `"[Errno 2] No such file or directory: …"`). Pinning a prefix would over-constrain the test, since exact wording varies by Python version; tests assert the `CommandError` class and `match=` a stable fragment.
- `CommandError("The `schema` must be an instance of strawberry.Schema")` for the non-`Schema` case — verbatim.
- `CommandError("--path requires a non-empty value")` for the empty-`--path` case — verbatim; pinned by tests in both tiers.

Deliberation moved to [the rationale companion][rationale-d5]: the `CommandError`-over-`ConfigurationError` justification, the commit-by-commit provenance of the five shapes that accreted after ship, and three rejected alternatives.

### Decision 6 — No watch, indent, JSON, settings-backed defaults, or alias

The command does NOT ship:

- `--watch` mode (file-system watcher + Django autoreload, graphene-django's shape). Reasonable post-`1.0.0` differentiator if consumer demand surfaces; deferred.
- `--indent` (graphene-django's JSON-pretty-printing flag). SDL is whitespace-agnostic; the formatting consumers want belongs in downstream tools.
- `--json` / a JSON-introspection mode (graphene-django's default output). SDL is the Strawberry-native serialization. See [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema).
- Settings-backed defaults from `DJANGO_STRAWBERRY_FRAMEWORK` (graphene-django's `GRAPHENE.SCHEMA` / `SCHEMA_OUTPUT` / `SCHEMA_INDENT` analogs). [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands" forbids preemptive settings; consumers wrap the command in a `Makefile` entry.
- A `dump_schema` / `print_schema` alias. One command name, one canonical invocation.

`add_arguments` therefore registers exactly two arguments and no more.

Deliberation moved to [the rationale companion][rationale-d6]: the minimum-surface justification and three rejected alternatives.

### Decision 7 — Test placement: `tests/management/__init__.py` ships

`tests/management/` carries an `__init__.py` shell matching the existing `tests/optimizer/__init__.py` and `tests/types/__init__.py` convention per [`docs/TREE.md`][tree] #"Subdirectories carry an `__init__.py` shell to match the existing", so pytest collects the modules as `tests.management.<module>`.

[`AGENTS.md`][agents] #"NOT a package, no `__init__.py`"'s "do not add `__init__.py`" rule is scoped to the two `examples/fakeshop/` test trees and says so explicitly ("collides on the tests package name once `examples/fakeshop` is on pythonpath"). Package-test subdirectories under `tests/` are not in its scope.

Deliberation moved to [the rationale companion][rationale-d7]: two rejected alternatives (a flat test file; omitting the marker).

### Decision 8 — Tests go through `call_command`, NOT direct `handle()`

Every test that **invokes** the command does so through `django.core.management.call_command(...)`, never by instantiating `Command()` and calling `.handle(...)`.

- `call_command` runs the full argparse layer, so the test catches type-coercion and argument-shape mismatches a direct `handle()` call would silently accept — and, decisively, it is the only way to reach failure shapes 1 and 2 in [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface). Django's `CommandParser.error()` raises `CommandError` directly on the `called_from_command_line=False` branch that `call_command` constructs by default; a direct `handle()` call skips argparse and therefore skips `CommandParser.error()` entirely, leaving both contracts unexercised.
- `call_command` captures `self.stdout` / `self.stderr` cleanly through the `stdout=` / `stderr=` kwargs; a direct `handle()` call requires monkey-patching to capture output.

**One narrow exception, and it is not an invocation.** A test may construct `Command().create_parser(...)` to inspect the parser the command builds — that is how `--path`'s help-string contract is pinned. It never calls `handle()` and never runs the command, so the rule above is intact.

The constraint propagates to the live tier: `examples/fakeshop/tests/test_export_schema.py` uses `call_command` exclusively, matching [`docs/TREE.md`][tree] #"`examples/fakeshop/tests/` — **Example-project tests, no HTTP `/graphql/`**".

Deliberation moved to [the rationale companion][rationale-d8]: two rejected alternatives (a unit/integration split; `pytest.mark.django_db` as a substitute).

### Decision 9 — Joint `0.0.7` cut

`0.0.7` ships under the joint-cut policy from [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] [Decision 10][spec-020-decision-10--joint-007-cut]: every card in the bundle accumulates `### Added` entries under the same `[0.0.7]` heading in [`CHANGELOG.md`][changelog], and the version bump in `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, and `tests/base/test_init.py`'s pinned version assertion is owned by whichever card ships last in the bundle, NOT this card.

[`KANBAN.md`][kanban] #"The last `0.0.7` card to ship owns the version bump from `0.0.6`" carries the same policy at board level. The Slice 3 doc-updates list explicitly excludes the version bump.

Deliberation moved to [the rationale companion][rationale-d9]: the restatement justification and two rejected alternatives.

### Decision 10 — Live coverage belongs in `examples/fakeshop/tests/`, NOT `test_query/`

The live fakeshop coverage lives in `examples/fakeshop/tests/`; it does NOT go under `examples/fakeshop/test_query/`.

- [`examples/fakeshop/test_query/README.md`][test-query-readme] is explicit: "Live GraphQL-API tests … exercise the full Django + Strawberry HTTP stack end-to-end by sending requests to `/graphql/` (typically via `django.test.Client.post(...)`)." The schema-export command is not an HTTP-shaped surface: it does not hit `/graphql/` and does not exercise the request pipeline.
- [`docs/TREE.md`][tree] #"`examples/fakeshop/tests/` — **Example-project tests, no HTTP `/graphql/`**": "`examples/fakeshop/tests/` — Example-project tests, no HTTP `/graphql/`. … management commands via `django.core.management.call_command`."
- [`AGENTS.md`][agents] #"any line reachable via a real GraphQL query against fakeshop"'s coverage-priority rule is satisfied rather than waived: the command's lines are genuinely unreachable from a live `/graphql/` query, so the fall-back tier is the correct one.

**The live tier is not a smoke test.** Where a package-tier test would exercise a branch against a synthesized fixture schema, and the branch's failure mode only arises after a real schema has been imported, finalized, and rendered to SDL, the test belongs here instead — the live form carries strictly stronger contract pressure. The `--path` write-failure branches are the worked example: they are reached only after the real `config.schema` has produced SDL, so they live in `examples/fakeshop/tests/test_export_schema.py` and the package tier deliberately gave them up.

Deliberation moved to [the rationale companion][rationale-d10]: the tier justification's file-specific half, and two rejected alternatives.

## Implementation plan

The card shipped as **three slices** aligned with the [Slice checklist](#slice-checklist). Each slice maps to one commit.

| Slice | Files touched | Tests |
| --- | --- | --- |
| 1 — Module + `Command` subclass | `django_strawberry_framework/management/__init__.py` (new), `django_strawberry_framework/management/commands/__init__.py` (new), `django_strawberry_framework/management/commands/export_schema.py` (new), `django_strawberry_framework/management/commands/_imports.py` (shared helper) | 0 (tests land in Slice 2) |
| 2 — Tests | `tests/management/__init__.py` (new), `tests/management/test_export_schema.py` (new), `tests/management/test_imports.py` (new), `examples/fakeshop/tests/test_export_schema.py` (new) | the three tiers in the [Test plan](#test-plan) |
| 3 — Promotion + docs | `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md` | 0 |

The three slices are authored in order. Slice 2 depends on Slice 1 (the class must exist before tests can `call_command` it); Slice 3 depends on Slice 2 (the [`CHANGELOG.md`][changelog] `### Added` line and [`KANBAN.md`][kanban] Done body must describe a shipped, tested module).

Deliberation moved to [the rationale companion][rationale-implementation-plan]: the per-slice line-delta estimates and their revision-by-revision adjustments.

## Edge cases and constraints

- **Django command-discovery is `INSTALLED_APPS`-driven.** `manage.py` discovers the command as long as `"django_strawberry_framework"` is in `INSTALLED_APPS` (the example project already has this entry at `examples/fakeshop/config/settings.py #"\"django_strawberry_framework\","`). Django walks the `management/commands/` directory by convention; no `AppConfig` method is involved. The [`Django AppConfig`][glossary-django-appconfig] shipped under [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021] is the entry point `INSTALLED_APPS` resolves to, and command discovery asks nothing of it.
- **`finalize_django_types()` runs as a side effect of resolving the schema symbol.** The consumer's `config/schema.py` calls [`finalize_django_types()`][glossary-finalize-django-types] at module level before constructing `strawberry.Schema(...)`. When the importer loads the module, the finalize call runs as part of its top-level execution. The command does NOT call it.
- **Idempotent reads.** The command reads the consumer's schema; it does not write to the database and does not mutate process state outside Strawberry's own caches. Running it twice produces identical output.
- **Schema symbol is resolved at command-invocation time.** Each `call_command("export_schema", "config.schema")` re-imports `config.schema` or hits the import cache. The cached case is correct: the schema is constructed once and stays constant for the process lifetime.
- **The `isinstance` check uses the public `strawberry.Schema` class**, imported as `from strawberry import Schema`. Subclasses pass, which is right — a `MyCustomSchema(strawberry.Schema)` is a valid export target. This is exercised, not hypothetical: the fakeshop schema the live tier drives is a `DjangoSchema`, a subclass, so narrowing the guard to an exact-type check would fail the live tier immediately.
- **`--path` is destructive and does not create directories.** An existing target is replaced without prompting; a missing parent directory is a `CommandError`, not an implicit `mkdir`. The `--path` help string states the first half so `manage.py export_schema --help` is not silent about it.
- **UTF-8, no newline translation.** `write_text(schema_output, encoding="utf-8", newline="")` is the only encoding shape. Both kwargs are load-bearing per [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema).
- **`tmp_path` for file-write tests.** Both tiers use pytest's `tmp_path` fixture so written files are auto-cleaned between runs.
- **`call_command` and `stdout`.** Capture via `stdout=StringIO()` is the documented pattern. Because [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema) suppresses Django's default trailing newline, a captured stdout value equals `print_schema(schema)` exactly — assertions compare for **equality**, not for a substring plus a newline allowance. A test that tolerates a trailing newline is asserting the pre-`0.0.7`-polish behavior and would not detect the contract's loss.
- **A `--path`-writing test that captures stdout must still pass `stdout=`.** The success message goes to `self.stdout`, so a `--path` invocation with no `stdout=` kwarg prints into the test runner's output.
- **No per-file ruff escape for the package.** `[tool.ruff.lint.per-file-ignores]` (see `pyproject.toml #"[tool.ruff.lint.per-file-ignores]"`) covers only `__init__.py` (`F401`), `tests/**/*.py`, `examples/**/*.py`, `scripts/**/*.py` (`PERF`), `**/migrations/*.py`, `**/views.py`, `**/urls.py`, and `**/admin.py`. There is **no** `django_strawberry_framework/**` entry, so the module is subject to all five gates named in [Decision 2](#decision-2--command-class-shape).
- **`pytest-django` setup.** Tests that invoke the command need Django's app registry populated; `pytest-django` handles this via `django.setup()` once per session. The package tier uses a fixture-shaped schema constructed in the test module (not pulled from a `DjangoType` registry), so it needs no `pytest.mark.django_db`. The live tier needs none either — the command only reads the schema.
- **Re-importing a moved schema module.** If a consumer reorganizes `config/schema.py` between two invocations in one process, Python's import cache may hold the stale module. That is a fixture concern, not a command bug, and is not tested.

## Test plan

Tests live across three modules in two trees, matching [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Placement is mandatory per [Decision 7](#decision-7--test-placement-testsmanagement__init__py-ships) and [Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query).

### `tests/management/__init__.py`

Empty marker module with a one-line docstring (`"""Package tests for django-strawberry-framework management commands."""`). Required for pytest to collect tests as `tests.management.<module>` and to satisfy `D100`. No further content.

### `tests/management/test_export_schema.py`

Package tier; system-under-test is `django_strawberry_framework.management.commands.export_schema`. **10 test functions, 12 collected items** (`uv run pytest tests/management/test_export_schema.py --collect-only -q --no-cov`). Selectors use the **explicit `:symbol` form** so no assertion depends on the `default_symbol_name` fallback by accident.

**Fixture-module cleanup contract.** Every test that synthesizes a `test_module` does so via `monkeypatch.setitem(sys.modules, "test_module", module)` where `module = types.ModuleType("test_module")`, with whatever attributes that test needs assigned to it. Pytest's `monkeypatch` teardown removes the entry from `sys.modules` at end of test, so a test that sets `test_module.schema = <Schema>` does not pollute the next test that needs `test_module.not_a_schema = 1` or a `test_module` with no `schema` attribute. Without this the suite is order-dependent: a bare `sys.modules["test_module"] = module` assignment leaves the module cached, the test that runs first wins, and any reordering surfaces flake. Tests that synthesize no fixture module (the unimportable-selector and missing-positional cases) do not need `monkeypatch`.

**One deliberate `pytest.mark.parametrize`.** `::test_export_schema_raises_command_error_for_malformed_selector` fans out over three selector shapes (`""`, `":schema"`, `".config.schema"`) that share one assertion. Parametrizing a set of inputs against one boundary is the right shape; a per-input copy would be three near-identical functions. Elsewhere, one pytest item per test.

Required coverage:

- **Unimportable module** — `call_command("export_schema", "does.not.exist:schema")`, `pytest.raises(CommandError, match="No module named")`. Pins the `ImportError` half of the resolution wrapper.
- **Missing attribute on an importable module** — `call_command("export_schema", "test_module:does_not_exist")`, `match="does_not_exist"`. Pins the `AttributeError` half, so a refactor narrowing the catch to `ImportError` alone fails.
- **Non-`Schema` resolved symbol** — the fixture module carries `not_a_schema = 1`; asserts `match=r"must be an instance of strawberry\.Schema"`. Pins the isinstance branch and the exact wording.
- **Missing positional argument** — `call_command("export_schema")`, `pytest.raises(CommandError)`. Pins the `CommandParser.error()` path of [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface).
- **Bare `--path` with no value** — `call_command("export_schema", "test_module:schema", "--path")`. Pins the argparse rejection that dropping `nargs="?"` bought.
- **Malformed selector** — the three-case parametrize above, matching `"module path is empty"` and `"relative module paths"`.
- **Whitespace-only `--path`** — `--path "   "`, `match="--path requires a non-empty value"`. Pins the `.strip()` widening; empty-string `--path` is pinned in the live tier.
- **`--path` help string** — reads the action off `Command().create_parser("manage.py", "export_schema")` and asserts `help == "Write UTF-8 SDL to this file, overwriting it without prompting"`. This is the one permitted `Command()` construction ([Decision 8](#decision-8--tests-go-through-call_command-not-direct-handle)); it makes the destructive-overwrite disclosure a contract rather than prose.
- **Three-way byte identity** — one test drives the same schema through stdout capture and through `--path`, then asserts both equal `print_schema(schema)`. This single assertion subsumes the two separate happy-path tests it replaced, and is what pins [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema)'s stdout newline suppression: with `ending=""` removed it fails.
- **Newline translation disabled** — monkeypatches `pathlib.Path.write_text` to capture its kwargs and asserts `encoding == "utf-8"` and `newline == ""`. Pinning the kwarg at the call site is the only way to assert it: the effect is invisible on an LF platform.

### `tests/management/test_imports.py`

The shared helper's own tier. **15 test functions, 19 collected items.** Every branch of `_imports.py`, and in particular the two negative contracts that keep the catches narrow:

- `::test_import_or_command_error_does_not_swallow_other_exceptions` — an exception that is neither `ImportError` nor `AttributeError` propagates as itself.
- `::test_import_module_symbol_or_command_error_does_not_mask_module_body_valueerror` — a `ValueError` raised by the *consumer's module body* during import is not relabelled a `CommandError`, even though a `ValueError` raised by `pathlib` during the write is ([Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface) shape 8). The two are different failures and must report differently.
- `::test_import_module_symbol_or_command_error_applies_default_symbol_name` — pins the `default_symbol_name="schema"` fallback at the helper, so a refactor dropping the kwarg fails here as well as in the live tier.

### `examples/fakeshop/tests/test_export_schema.py`

Live tier, driven against the real `config.schema`. **5 tests.** Four of the five use the bare `"config.schema"` selector with no `:schema` suffix, so the `default_symbol_name` fallback is pinned four times over by real usage rather than by one dedicated test.

- **SDL to stdout** — `call_command("export_schema", "config.schema:schema", stdout=out)`; asserts `"type BranchType"` in the captured value. Pins end-to-end resolution of the consumer's real schema — a `DjangoSchema` built through [`finalize_django_types()`][glossary-finalize-django-types] — rather than a synthesized fixture.
- **Destructive overwrite via `--path`** — writes a sentinel string to the target first, then runs the command; asserts the SDL landed, the sentinel is gone, and `Wrote schema to <path>` appears on stdout. One test pins three contracts: the write, the overwrite, and the success message.
- **Missing parent directory** — `pytest.raises(CommandError, match="No such file or directory")`. Pins the `OSError` half of the write-failure catch.
- **Empty-string `--path`** — `--path ""`, `match="--path requires a non-empty value"`.
- **Embedded null byte in `--path`** — `match="embedded null byte"`. Pins the `ValueError` half of the write-failure catch.

The last three live here rather than in the package tier deliberately: each is reached only after the real schema has been imported, finalized, and rendered to SDL, so the live form carries stronger contract pressure than a synthetic `test_module:schema` equivalent ([Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query)). Two of them are [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface) shape 8, which the package tier therefore does not cover at all; the third is the empty-string spelling of shape 7, whose whitespace-only twin is pinned package-side, so shape 7 is covered in both tiers. No `pytest.mark.django_db` is needed — the command performs no database access.

No live `/graphql/` HTTP test is required; the command is not HTTP-shaped.

Deliberation moved to [the rationale companion][rationale-test-plan]: each test's per-revision provenance, and the negative-shape test the card considered and declined to author.

## Doc updates

- [`docs/GLOSSARY.md`][glossary]
  - Flip [`Schema export management command`][glossary-schema-export-management-command] from `planned for 0.0.7` to `shipped (0.0.7)` (Index-table state at [`docs/GLOSSARY.md`][glossary] `#"[Schema export management command](#schema-export-management-command)"`; the entry body lives at [`docs/GLOSSARY.md`][glossary] #"## Schema export management command").
  - Update the entry body to describe the shipped contract: `django_strawberry_framework/management/commands/export_schema.py` ships `Command(BaseCommand)` with positional `schema` (dotted path, default symbol name `"schema"`) and optional `--path`; SDL output via `strawberry.printer.print_schema`, with the stdout write, the `--path` file and `print_schema`'s return value the same bytes; a destructive UTF-8 write with a `Wrote schema to <file>` success message; `CommandError` for every failure shape in [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface); no `--watch` / `--indent` / JSON mode / settings-backed defaults.
  - Update the Index table's status column for the row at [`docs/GLOSSARY.md`][glossary] `#"[Schema export management command](#schema-export-management-command)"`.

- [`docs/README.md`][readme]
  - **Surgically remove the entire `- schema export management command` bullet** in the [`docs/README.md`][readme] #"**Coming in `0.1.0`**" section. `DONE-021-0.0.7` removed only `, Django `AppConfig`` from that line; this card removes the remainder.
  - The shipped-list heading at [`docs/README.md`][readme] #"**Shipped today** (`0.0.7`):" already reads `**Shipped today** (`0.0.7`):`; no further heading change here.
  - Add a bullet to the `Shipped today (0.0.7)` section reading: "`manage.py export_schema` — Django management command that prints or writes the GraphQL SDL for a `strawberry.Schema` symbol (positional dotted path, optional `--path`); migration-parity with `strawberry-django`'s command of the same name. See [`GLOSSARY.md#schema-export-management-command`][glossary-schema-export-management-command]."

- [`docs/TREE.md`][tree]
  - Add the `management/` subtree to the **current on-disk layout** section under the `django_strawberry_framework/` tree ([`docs/TREE.md`][tree] #"## django_strawberry_framework (current on-disk layout)"), between `list_field.py` and `optimizer/` (alphabetical). Spell out the `commands/__init__.py` and `commands/export_schema.py` children.
  - Remove the `[alpha]` tag from the existing `management/ # [alpha] Django management commands` block in the **target package layout** section at [`docs/TREE.md`][tree] #"management/              # Django management commands".
  - **Surgically remove `, and the management command` from the current-on-disk-layout prose at [`docs/TREE.md`][tree] #"Every other module shown in the target package layout below"**. The prose reads "Every other module shown in the target package layout below — query-surface subpackages, the mutation cluster, the auth / forms / DRF integrations, the test client, the Channels router, and the management command — is not on disk yet and will land as the corresponding `KANBAN.md` cards ship." After Slice 3 the management command IS on disk, so the fragment self-contradicts. After the edit the sentence reads: "Every other module shown in the target package layout below — query-surface subpackages, the mutation cluster, the auth / forms / DRF integrations, the test client, and the Channels router — is not on disk yet and will land as the corresponding `KANBAN.md` cards ship." This action is stated here as well as in the [Slice checklist](#slice-checklist) and [Definition of done](#definition-of-done) because this section is the implementer-facing list a worker walks top-down.
  - Add `tests/management/` (with its `__init__.py` and test-module children) to the **current test-tree** section ([`docs/TREE.md`][tree] #"### Current shape (on disk today)"), **before `test_apps.py`** (alphabetical).

- [`KANBAN.md`][kanban]
  - Move the card to the Done column with the next available `DONE-NNN-0.0.7` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). The card's past-tense Done body is its `#### Note`, which summarizes the shipped scope: "one management command (positional `schema`, `--path`, SDL via `print_schema`, `CommandError` paths) + tests."
  - Update the `### In progress` summary paragraph to remove this card from the remaining-cards list once it moves to Done.

- [`CHANGELOG.md`][changelog]
  - **Append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading — the `[0.0.7]` heading at [`CHANGELOG.md`][changelog] #"## [0.0.7] - 2026-05-27" already carries `DONE-020-0.0.7`'s [`DjangoListField`][glossary-djangolistfield] entry and `DONE-021-0.0.7`'s [`Django AppConfig`][glossary-django-appconfig] entry; every `0.0.7` card under the joint cut appends to the same shared section per [Decision 9](#decision-9--joint-007-cut)): "`Schema export management command` — `django_strawberry_framework/management/commands/export_schema.py` ships `Command(BaseCommand)`; `manage.py export_schema config.schema [--path schema.graphql]` writes SDL via `strawberry.printer.print_schema`. Symbol resolution via `strawberry.utils.importer.import_module_symbol(default_symbol_name=\"schema\")`. `CommandError` for unimportable dotted path, non-`strawberry.Schema` resolved symbol, and missing positional argument. No `--watch` / `--indent` / JSON mode / settings-backed defaults in `0.0.7` (each deferred to a follow-up card driven by consumer demand)."
  - The version bump entry is owned by **the last `0.0.7` card to ship** per [Decision 9](#decision-9--joint-007-cut), NOT this slice.
  - [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" — this Slice 3 bullet is the explicit instruction.

- No edits to [`README.md`][readme]: its status section names consumer-facing primitives, and the command is plumbing reachable via `manage.py` rather than via a consumer import.
- No edits to [`GOAL.md`][goal]: its `astronomy` showcase walks model definitions, schema, filters, orders, aggregates, and fieldsets, none of which exercises `manage.py`.
- No edits to [`TODAY.md`][today]: it is a query-shape-and-capability snapshot, and the fakeshop schema is unchanged by this card.

## Out of scope (explicitly tracked elsewhere)

- JSON introspection output (graphene-django's default mode). See [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias); not on the roadmap.
- `--watch` mode (file-system watcher + Django autoreload). See [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias); reasonable post-`1.0.0` differentiator if consumer demand surfaces.
- Settings-backed default schema dotted path (`DJANGO_STRAWBERRY_FRAMEWORK.SCHEMA_PATH` analog). See [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias); [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands" explicitly forbids preemptive settings.
- `--indent` / SDL-formatting option. See [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias); SDL is whitespace-agnostic.
- `dump_schema` / `print_schema` aliases. See [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias).
- [Multi-database cooperation][glossary-multi-database-cooperation] contract: `DONE-023-0.0.7` in [`KANBAN.md`][kanban]. The cooperation is in `types/resolvers.py`, not in `management/`; the two cards are independent.
- Warning-free scalar registration via `StrawberryConfig.scalar_map`: `DONE-025-0.0.7` in [`KANBAN.md`][kanban]. The scalar map is consumer-facing schema-construction shape, not management-command surface.
- Channels ASGI router ([`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]): shipped as `DONE-041-0.0.14`.
- [Debug-toolbar middleware][glossary-debug-toolbar-middleware]: shipped as `DONE-042-0.0.14`.
- [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]: shipped as `DONE-044-0.0.14`.
- Test-client helpers ([`TestClient`][glossary-testclient], [`GraphQLTestCase`][glossary-graphqltestcase]): shipped as `DONE-043-0.0.14`.
- A second `manage.py` command over the same import-translation helper: `inspect_django_type`, shipped as `DONE-029-0.0.9`. It shares `_imports.py` with this command ([Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper)) and is otherwise independent.

## Definition of done

The card is complete when all of the following are true:

1. `django_strawberry_framework/management/__init__.py` exists with a one-line module docstring (no further content); `django_strawberry_framework/management/commands/__init__.py` exists with a one-line module docstring (no further content).
2. `django_strawberry_framework/management/commands/export_schema.py` exists and defines `Command(BaseCommand)` per [Decision 2](#decision-2--command-class-shape) — `help = "Export the GraphQL schema"`, `add_arguments(self, parser: CommandParser) -> None` registering positional `schema` (`type=str, help="The schema location"`, no `nargs`) and optional `--path` (`type=str, help="Write UTF-8 SDL to this file, overwriting it without prompting"`, no `nargs`), and `handle(self, *args: object, **options: object) -> None` per [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper), [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema), and [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface). Module docstring (`D100`), class docstring (`D101`), and docstrings on both methods (`D102`) all present, with `handle`'s enumerating its output branches. `parser: CommandParser` and `-> None` on both methods (`ANN001` / `ANN201`). No `--watch`, `--indent`, `--json`, settings-backed defaults, or alias (per [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias)). No `# noqa` suppressions for any `D` or `ANN` rule.
3. `django_strawberry_framework/management/commands/_imports.py` carries the shared import translation and the pre-import selector validation per [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper); `export_schema.py` contains no inline `try` / `except (ImportError, AttributeError)`.
4. `django_strawberry_framework/__init__.py` is NOT modified (per [Decision 1](#decision-1--module-location--no-public-export)); `__all__` is unchanged; `tests/base/test_init.py`'s `__all__` assertion is unchanged.
5. `tests/management/__init__.py` exists with a one-line module docstring. `tests/management/test_export_schema.py` covers every contract listed for it in the [Test plan](#test-plan), and `tests/management/test_imports.py` covers every branch of the shared helper including the two non-swallowing contracts.
6. `examples/fakeshop/tests/test_export_schema.py` carries the live tier per [Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query), including both file-write-failure cases ([Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface) shape 8, the only shape the package tier gives up) and the empty-string `--path` spelling of shape 7 whose whitespace-only twin stays package-side. No file under `examples/fakeshop/test_query/` is created.
7. Every test that invokes the command uses `django.core.management.call_command(...)` per [Decision 8](#decision-8--tests-go-through-call_command-not-direct-handle); the only `Command()` construction anywhere is the parser-inspection test, which never calls `handle()`.
8. `examples/fakeshop/config/settings.py` is NOT modified (the existing `"django_strawberry_framework"` entry in `INSTALLED_APPS` is sufficient for Django to discover the command).
9. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`) — **verified by CI's gate, not by the worker locally.** The worker's local verification is item 13's `uv run pytest --no-cov` suite-passing check, in line with [`docs/builder/BUILD.md`][build]'s "Coverage is the maintainer's gate, not a worker's tool" rule. If CI reports a coverage regression on the PR, the worker adds the missing test before merge.
10. [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][readme], [`docs/TREE.md`][tree], [`KANBAN.md`][kanban], and [`CHANGELOG.md`][changelog] reflect the shipped state per the [Doc updates](#doc-updates) section. The `- schema export management command` bullet at [`docs/README.md`][readme] #"**Coming in `0.1.0`**" is removed in full; the `[alpha]` tag on the `management/` block at [`docs/TREE.md`][tree] #"management/              # Django management commands" is removed; the `, and the management command` fragment at [`docs/TREE.md`][tree] #"Every other module shown in the target package layout below" is surgically removed. [`README.md`][readme], [`GOAL.md`][goal], and [`TODAY.md`][today] are NOT edited.
11. [`KANBAN.md`][kanban] moves the card to Done with the next `DONE-NNN-0.0.7` id and a past-tense body summarizing the shipped scope.
12. The version bump is NOT in this card per [Decision 9](#decision-9--joint-007-cut); the last `0.0.7` card to ship owns `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion.
13. Zero new public exports — `__all__` is unchanged.
14. `uv run ruff format .` passes; `uv run ruff check --fix .` passes; `uv run pytest --no-cov` passes (the explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov`; workers verify the suite passes, not that coverage stays at 100%).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[today]: ../../TODAY.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-debug-toolbar-middleware]: ../GLOSSARY.md#debug-toolbar-middleware
[glossary-django-appconfig]: ../GLOSSARY.md#django-appconfig
[glossary-djangographqlprotocolrouter]: ../GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-graphqltestcase]: ../GLOSSARY.md#graphqltestcase
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-response-extensions-debug-middleware]: ../GLOSSARY.md#response-extensions-debug-middleware
[glossary-schema-export-management-command]: ../GLOSSARY.md#schema-export-management-command
[glossary-testclient]: ../GLOSSARY.md#testclient
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[rationale]: appx/spec-022-export_schema-0_0_7-rationale.md
[rationale-d1]: appx/spec-022-export_schema-0_0_7-rationale.md#decision-1--module-location--no-public-export
[rationale-d10]: appx/spec-022-export_schema-0_0_7-rationale.md#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query
[rationale-d2]: appx/spec-022-export_schema-0_0_7-rationale.md#decision-2--command-class-shape
[rationale-d3]: appx/spec-022-export_schema-0_0_7-rationale.md#decision-3--symbol-resolution-through-the-shared-_imports-command-helper
[rationale-d4]: appx/spec-022-export_schema-0_0_7-rationale.md#decision-4--sdl-output-via-strawberryprinterprint_schema
[rationale-d5]: appx/spec-022-export_schema-0_0_7-rationale.md#decision-5--commanderror-is-the-commands-only-failure-surface
[rationale-d6]: appx/spec-022-export_schema-0_0_7-rationale.md#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias
[rationale-d7]: appx/spec-022-export_schema-0_0_7-rationale.md#decision-7--test-placement-testsmanagement__init__py-ships
[rationale-d8]: appx/spec-022-export_schema-0_0_7-rationale.md#decision-8--tests-go-through-call_command-not-direct-handle
[rationale-d9]: appx/spec-022-export_schema-0_0_7-rationale.md#decision-9--joint-007-cut
[rationale-implementation-plan]: appx/spec-022-export_schema-0_0_7-rationale.md#the--implementation-plan-section
[rationale-test-plan]: appx/spec-022-export_schema-0_0_7-rationale.md#the--test-plan-section
[spec-020-decision-10--joint-007-cut]: spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-020]: spec-020-list_field-0_0_7.md
[spec-021-decision-3--no-public-export]: spec-021-apps-0_0_7.md#decision-3--no-public-export
[spec-021]: spec-021-apps-0_0_7.md

<!-- docs/builder/ -->
[build]: ../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[test-query-readme]: ../../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
