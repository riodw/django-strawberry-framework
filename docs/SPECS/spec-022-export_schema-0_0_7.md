# Spec: `export_schema` management command

Target release: `0.0.7`.
Status: shipped in `0.0.7` (2026-05-27) and archived under `docs/SPECS/`; card `DONE-022-0.0.7`. This document states the command's contract as it stands at `HEAD`.
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`Schema export management command`][glossary-schema-export-management-command], [`Django AppConfig`][glossary-django-appconfig], [`DjangoType`][glossary-djangotype], [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], [`finalize_django_types`][glossary-finalize-django-types]); [`KANBAN.md`][kanban] card `DONE-022-0.0.7`; shipped predecessor [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021] (the [`Django AppConfig`][glossary-django-appconfig] it landed is the entry point Django's `INSTALLED_APPS`-driven management-command discovery resolves through for this package); joint-cut policy spec [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] (Decision 10 — joint `0.0.7` cut, reused in [Decision 9](#decision-9--joint-007-cut) here).
Deliberation: why each Decision is shaped as it is, and the alternatives it rejected, live in its companion [`docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`][rationale].

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`Schema export management command`][glossary-schema-export-management-command] — the shipped surface this spec pins.
- [`Django AppConfig`][glossary-django-appconfig] — the entry point Django's `INSTALLED_APPS`-driven command discovery resolves through; see [Decision 1](#decision-1--module-location--no-public-export).
- [`DjangoType`][glossary-djangotype] — the consumer-facing type the exported SDL describes; not imported by the command but the reason the command exists.
- [`finalize_django_types`][glossary-finalize-django-types] — the consumer-owned synchronization point that must have run before the consumer's `schema = strawberry.Schema(...)` is constructed. The command does NOT call it (see [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — present on the consumer's `strawberry.Schema(...)` but not exercised at export time; SDL is the static type system, not a runtime execution.
- [`ConfigurationError`][glossary-configurationerror] — not raised by anything in this card; `CommandError` (Django) is the exclusive error class for export-time failures per [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface).

Project conventions to follow:

- [`AGENTS.md`][agents] — [`AGENTS.md`][agents] #"Test placement:" (package tests live under `tests/`, project-level non-HTTP fakeshop tests under `examples/fakeshop/tests/`, which is not a package; package-test subdirectories like `tests/optimizer/` and `tests/types/` carry `__init__.py`); [`AGENTS.md`][agents] #"any line reachable via a real GraphQL query against fakeshop"; [`AGENTS.md`][agents] #"No pytest after edits"; [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands". **Note:** [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" prohibits [`CHANGELOG.md`][changelog] edits without explicit permission; [Slice 3](#implementation-plan) grants that permission for this card's `[0.0.7]` `### Added` entry.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target.
- [`KANBAN.md`][kanban] — card-ID format; column movement at Slice 3.
- [`START.md`][start] — [`START.md`][start] #"project/config only (urls, settings guard, schema export)" names `examples/fakeshop/tests/` as the home for the schema-export command's tests.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Three slices total.

- [ ] Slice 1: Module + `Command` subclass
  - [ ] Package `django_strawberry_framework/management/` with a one-line module docstring `__init__.py` (empty marker).
  - [ ] Package `django_strawberry_framework/management/commands/` with a one-line module docstring `__init__.py` (empty marker).
  - [ ] Module `django_strawberry_framework/management/commands/export_schema.py` housing `Command(BaseCommand)` per [Decision 2](#decision-2--command-class-shape) — `help = "Export the GraphQL schema"`, positional `schema` (a single scalar dotted-path value, no `nargs`), optional `--path` (a value is required when the flag is given; no `nargs`), `handle(self, *args: object, **options: Any) -> None` that (a) resolves the symbol via `import_module_symbol_or_command_error(options["schema"], default_symbol_name="schema")` per [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper), (b) raises `CommandError` when the resolved symbol is not a `strawberry.Schema` instance per [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface), (c) renders SDL via `strawberry.printer.print_schema(schema_symbol)` per [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema), (d) routes on `path is None` to a newline-suppressed `self.stdout.write(schema_output, ending="")` and returns, (e) rejects an empty or whitespace-only `--path` with `CommandError("--path requires a non-empty value")`, and (f) otherwise writes `pathlib.Path(path).write_text(schema_output, encoding="utf-8", newline="")` inside a `try` / `except (OSError, ValueError)` that re-raises as `CommandError`, then emits `self.style.SUCCESS(f"Wrote schema to {path}")`.
  - [ ] Shared import translation lives in `django_strawberry_framework/management/commands/_imports.py`, not inline in `handle()` (per [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper)). The helper validates the selector's module path before delegating resolution to Strawberry's importer unchanged.
  - [ ] `add_arguments` signed as `def add_arguments(self, parser: CommandParser) -> None:` (`parser: CommandParser` covers `ANN001`; `-> None` covers `ANN201`; `CommandParser` imported from `django.core.management.base`). Both `add_arguments` and `handle` carry `@override` (from `typing_extensions`), which basedpyright's `reportImplicitOverride` requires.
  - [ ] `--path`'s `help` string is `"Write UTF-8 SDL to this file, overwriting it without prompting"` — the destructive-overwrite contract must be visible at `manage.py export_schema --help`, and the exact string is pinned by a test.
  - [ ] One-line method docstring on `add_arguments` (required by `D102`; pydocstyle convention is google per the `pyproject.toml` `[tool.ruff.lint.pydocstyle]` table): `"""Register the positional schema argument and the optional --path flag."""`. Do NOT suppress with `# noqa: D102` — the docstring IS the root-cause fix per [`AGENTS.md`][agents] #"Always give the root-cause fix even when slower".
  - [ ] Method docstring on `handle` (required by `D102`) enumerating the three output branches: newline-suppressed stdout, empty-`--path` rejection, and the destructive UTF-8 file write. Do NOT suppress with `# noqa: D102`.
  - [ ] Do NOT implement a settings-backed default for `schema` (per [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias)).
  - [ ] Do NOT implement `--watch`, `--indent`, `--json`, a `dump_schema` / `print_schema` alias, or a JSON-introspection mode (per [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias)).
  - [ ] Do NOT re-export `Command` from `django_strawberry_framework/__init__.py` (per [Decision 1](#decision-1--module-location--no-public-export)). The class is import-time plumbing Django's command-discovery resolves through `INSTALLED_APPS`; consumers never write `from django_strawberry_framework.management.commands.export_schema import Command`.
  - [ ] One-line module docstring on `export_schema.py` (required by `D100`); one-line class docstring on `Command` (required by `D101`). Module docstring: `"""manage.py export_schema - print or write the GraphQL SDL for a Strawberry schema symbol."""`. Class docstring: `"""Export the GraphQL SDL for a strawberry.Schema symbol."""`. Do NOT suppress with `# noqa: D100` / `# noqa: D101`.
  - [ ] `management/__init__.py` and `management/commands/__init__.py` each carry a one-line module docstring (required by `D100`).
- [ ] Slice 2: Tests
  - [ ] `tests/management/__init__.py` (empty marker, matching `tests/optimizer/__init__.py` / `tests/types/__init__.py`) with a one-line module docstring (required by `D100`): `"""Package tests for django-strawberry-framework management commands."""`.
  - [ ] `tests/management/test_export_schema.py` holds the package tier: only the contracts with no project-schema shape, enumerated in the [Test plan](#test-plan) — the two argparse rejections, the `--path` help string, and the `newline=""` kwarg pin.
  - [ ] `tests/management/test_imports.py` holds the shared helper's own tier — every branch of `_imports.py`, including the two "does not swallow / does not mask" negative contracts.
  - [ ] `examples/fakeshop/tests/test_export_schema.py` holds the live tier: every other contract, driven against the real `config.schema` — SDL content, three-way byte identity, the selector and non-`Schema` failure shapes, and every `--path` branch (per [Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query)). Do NOT add a file under `examples/fakeshop/test_query/`.
  - [ ] Tests exercise the command exclusively through `django.core.management.call_command`, never `Command().handle(...)` (per [Decision 8](#decision-8--tests-go-through-call_command-not-direct-handle)). Parser-shape assertions that read `Command().create_parser(...)` without invoking the command are permitted and are not `handle()` calls.
  - [ ] Package-tier selectors use the **explicit `:symbol` form** (`test_module:schema`, `config.schema:schema`) so no assertion depends on the `default_symbol_name` fallback by accident; the fallback is pinned deliberately by the live tier's bare `"config.schema"` selectors and at the helper.
- [ ] Slice 3: Promotion + docs
  - [ ] [`docs/GLOSSARY.md`][glossary] carries [`Schema export management command`][glossary-schema-export-management-command] at `shipped (0.0.7)` in both the entry and the Index table, with the entry body describing the shipped command.
  - [ ] [`docs/README.md`][readme] names `manage.py export_schema` beside `manage.py inspect_django_type`.
  - [ ] [`docs/TREE.md`][tree] lists `management/commands/` (`_imports.py`, `export_schema.py`) under the package tree and `tests/management/` under the test tree; both are rendered from module docstrings.
  - [ ] [`KANBAN.md`][kanban] carries the card in the Done column as `DONE-022-0.0.7`, with a past-tense body summarizing the shipped scope.
  - [ ] [`CHANGELOG.md`][changelog]: the entry sits in the shared `[0.0.7]` `### Added` subsection (one `[0.0.7]` heading per [Decision 9](#decision-9--joint-007-cut) — every `0.0.7` card under the joint cut appends to the same section).
  - [ ] No edits to [`README.md`][readme-root], [`GOAL.md`][goal], or [`TODAY.md`][today]: the command is `manage.py` plumbing, not a consumer-name surface change, and the fakeshop schema is unchanged by this card.
  - [ ] Version bump owned by **the last `0.0.7` card to ship**, NOT this card ([Decision 9](#decision-9--joint-007-cut)); this card does not touch `__version__` in `django_strawberry_framework/__init__.py`, the single version source.
  - [ ] Zero new public exports — the management command is import-time plumbing discovered through Django's `INSTALLED_APPS` machinery. `__all__` is unchanged.
  - [ ] Final gates:
    - [ ] `uv run ruff check --fix .` passes.
    - [ ] `uv run ruff format .` passes.
    - [ ] `uv run pytest --no-cov` (or scoped subset) passes; the explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov`; coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`), not this slice's.

## Problem statement

Consumers who want to emit the GraphQL SDL — for client codegen (`graphql-codegen`, `graphql-cli`), CI schema-diffing, SDL-as-artifact in releases, or human-readable schema review — would otherwise hand-roll a script that imports their schema and calls `strawberry.printer.print_schema`. Both reference packages ship the command: `strawberry-django` as `export_schema` (SDL, positional dotted path, optional `--path`), `graphene-django` as `graphql_schema` (JSON-by-default, `--schema` / `--out` / `--indent` / `--watch`, settings-backed defaults).

This card borrows the strawberry-django name and shape and deliberately does not borrow graphene-django's JSON / `--watch` / `--indent` / settings-backed defaults (see [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias) and [Borrowing posture](#borrowing-posture)).

Django's management-command discovery is directory-convention-based — `manage.py` walks `management/commands/` in every installed app — and involves no `AppConfig` method at all. The command therefore composes with the [`Django AppConfig`][glossary-django-appconfig] that [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021] landed without requiring anything of it.

## Current state

- `django_strawberry_framework/management/commands/export_schema.py` ships the command; `django_strawberry_framework/management/__init__.py` and `django_strawberry_framework/management/commands/__init__.py` are one-line-docstring markers. `django_strawberry_framework/management/commands/_imports.py` carries the shared import-translation helpers the command resolves through ([Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper)).
- `examples/fakeshop/config/schema.py` exposes a top-level `schema = DjangoSchema(query=Query, mutation=Mutation, config=strawberry_config(), extensions=[lambda: _optimizer])`; the live tests resolve it through both `"config.schema"` (exercising the `default_symbol_name` fallback) and `"config.schema:schema"`. `DjangoSchema` subclasses `strawberry.Schema` (`django_strawberry_framework/schema.py::DjangoSchema`), so the live tier is also what proves the isinstance guard admits a subclass rather than only the base class.
- `examples/fakeshop/config/schema.py` calls [`finalize_django_types()`][glossary-finalize-django-types] before constructing the schema. By the time the command imports `config.schema`, the finalize call has already run as a side effect of the module's top-level execution; the command does NOT call [`finalize_django_types()`][glossary-finalize-django-types] itself. See [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper).
- `tests/management/` carries `__init__.py`, `test_export_schema.py`, and `test_imports.py` (beside `inspect_django_type`'s own module); the live tier is `examples/fakeshop/tests/test_export_schema.py`. Nothing lives under `examples/fakeshop/test_query/` for this command.
- `tests/base/test_init.py` pins the package's `__all__` tuple; the command is not a public export ([Decision 1](#decision-1--module-location--no-public-export)) so that assertion is untouched.
- `pyproject.toml` pins the `strawberry-graphql` floor. The command constrains it in one direction only — `strawberry.utils.importer.import_module_symbol` and `strawberry.printer.print_schema` must exist — and every version in the supported range satisfies that. `import_module_symbol` (signature `(selector: str, default_symbol_name: str | None = None) -> object`) and `print_schema` are both already in the dependency tree; the command adds no new dependency.

## Goals

1. Ship `django_strawberry_framework/management/commands/export_schema.py` containing `Command(BaseCommand)` with the strawberry-django-shaped signature: positional `schema` (a single scalar dotted path; default symbol name `"schema"`), optional `--path` (write UTF-8 SDL to that file, overwriting it without prompting). Absent `--path`, SDL goes to `self.stdout` with Django's default trailing newline suppressed.
2. Ship `django_strawberry_framework/management/__init__.py` and `django_strawberry_framework/management/commands/__init__.py` as one-line-docstring marker modules (required by `D100`; no additional content).
3. Ship the package test tier — `tests/management/__init__.py`, `tests/management/test_export_schema.py`, and `tests/management/test_imports.py` — covering the contracts pinned in the [Test plan](#test-plan) that have no project-schema shape: the two argparse `CommandError` shapes, the `--path` help-string contract, the `newline=""` kwarg pin, and every branch of the shared `_imports.py` helper.
4. Ship live fakeshop coverage in `examples/fakeshop/tests/test_export_schema.py` that drives the real `config.schema` end to end: the SDL contains a known type from the `library` app (`"type BranchType"` — the `DjangoType` class is `BranchType` at `examples/fakeshop/apps/library/schema.py::BranchType`, and Strawberry emits the GraphQL type name from the class name unchanged), the three-way byte identity holds, and the remaining six `CommandError` shapes of [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface) are raised.
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

Local source path: `~/projects/strawberry-django-main/strawberry_django/management/commands/export_schema.py` (referenced from [`docs/TREE.md`][tree] #"└── export_schema.py").

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

- **`help` string.** `"Export the GraphQL schema"` — Title Case `GraphQL` for repo prose consistency.
- **Docstrings and annotations.** The upstream carries none; this module carries the ones enumerated in [Decision 2](#decision-2--command-class-shape).
- **No `nargs`.** Neither argument declares it. See [Decision 2](#decision-2--command-class-shape).
- **`--path` help string.** Rewritten to state the destructive-overwrite contract, and pinned by a test.
- **Byte-exact output.** The upstream's stdout branch appends Django's default trailing newline and its file write applies platform newline translation, so the two outputs differ. Both are suppressed here. See [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema).
- **A wider, attributable failure surface.** Empty / whitespace-only `--path`, write failures, and two malformed-selector shapes all surface as `CommandError` instead of a raw traceback or a silent fall-through. See [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface).
- **A success message.** `self.style.SUCCESS(f"Wrote schema to {path}")` after a successful write; the upstream exits silently.
- **Shared import translation.** The `try` / `except` wrapper lives in `_imports.py` and is shared with `inspect_django_type`. See [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper).

### From `graphene-django` — explicitly do not borrow

Local source path: `~/projects/django-graphene-filters/.venv/lib/python*/site-packages/graphene_django/management/commands/graphql_schema.py` (referenced from [`docs/TREE.md`][tree] #"│   └── graphql_schema.py").

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

The non-`Schema` example uses `config.urls:urlpatterns`, the explicit-symbol selector pointing at the URL-configuration list, NOT bare `config.urls`. `config/urls.py` declares `from config.schema import schema` (`examples/fakeshop/config/urls.py #"from config.schema import schema"`), so resolving `config.urls` under the default symbol name `"schema"` would succeed against the real `strawberry.Schema`. `urlpatterns` is a list (`examples/fakeshop/config/urls.py #"urlpatterns = ["`), so it exercises the isinstance branch.

The final shape is Django's argparse layer doing its job; the test plan asserts it so a refactor cannot silently drop the requirement.

## Architectural decisions

### Decision 1 — Module location & no public export

**Module location.** The command lives at **`django_strawberry_framework/management/commands/export_schema.py`**, matching Django's `management/commands/` discovery convention.

Two `__init__.py` markers are required — Django's `manage.py` walks `<app>.management.commands.*` for every `<app>` in `INSTALLED_APPS`, so both `management` and `management.commands` must be importable Python packages:

- `django_strawberry_framework/management/__init__.py` — empty marker (one-line module docstring required by `D100`).
- `django_strawberry_framework/management/commands/__init__.py` — empty marker (one-line module docstring required by `D100`).

**Public-export surface.** `django_strawberry_framework/__init__.py` does not export `Command` and `__all__` does not name it. Django's command-discovery resolves the command through its dotted module path; consumers never import `Command`. The posture is symmetric with [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021] [Decision 3][spec-021-decision-3--no-public-export].

Rejected alternatives: [the rationale companion][rationale-d1].

### Decision 2 — `Command` class shape

The class declares exactly:

- `help = "Export the GraphQL schema"` — Title Case `GraphQL`.
- `add_arguments(self, parser: CommandParser) -> None` registering (a) positional `"schema"` with `type=str, help="The schema location"` and **no `nargs`**, so `options["schema"]` is the scalar dotted path rather than a one-element list; (b) optional `"--path"` with `type=str, help="Write UTF-8 SDL to this file, overwriting it without prompting"` and **no `nargs`**, so argparse rejects a bare `--path` carrying no value.
- `handle(self, *args: object, **options: Any) -> None` per [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper), [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema), and [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface).

**Dropping `nargs` is a contract, not a tidy-up.** On the positional argument it removes an index (`options["schema"][0]`) that bought nothing; on `--path` it closes a real hole. Under the upstream's `nargs="?"` a bare `--path` with no following value parses successfully and sets `options["path"]` to `None` — indistinguishable from omitting the flag entirely, so a user who typed `--path` and forgot the filename silently gets stdout. Without `nargs`, argparse raises at parse time.

Method signatures — pinned:

```python path=null start=null
import pathlib
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from strawberry import Schema
from strawberry.printer import print_schema
from typing_extensions import override

from django_strawberry_framework.management.commands._imports import (
    import_module_symbol_or_command_error,
)


class Command(BaseCommand):
    """Export the GraphQL SDL for a strawberry.Schema symbol."""

    help = "Export the GraphQL schema"

    @override
    def add_arguments(self, parser: CommandParser) -> None:
        """Register the positional schema argument and the optional --path flag."""
        parser.add_argument("schema", type=str, help="The schema location")
        parser.add_argument(
            "--path",
            type=str,
            help="Write UTF-8 SDL to this file, overwriting it without prompting",
        )

    @override
    def handle(self, *args: object, **options: Any) -> None:
        """Resolve the dotted-path schema symbol and emit SDL.

        Docstring enumerates the three output branches; body per Decision 3
        (symbol resolution) / Decision 4 (SDL output) / Decision 5 (errors).
        """
```

Documentation and annotation requirements — every one gate-forced, none stylistic: `D100` (module docstring), `D101` (class docstring), `D102` (a docstring on `add_arguments` and on `handle`), `ANN001` (`parser: CommandParser`, imported from `django.core.management.base`), `ANN201` (`-> None` on both methods), and basedpyright's `reportImplicitOverride` (`@override` on both methods). `**options: Any` matches django-stubs' `BaseCommand.handle` and lets the argparse-populated `options["schema"]` flow on as the `str` the helper takes; `*args: object` is a documentation-quality narrow (`ANN002` / `ANN003` / `ANN401` are globally ignored). `# noqa: D102 / ANN001 / ANN201` suppressions are forbidden per [`AGENTS.md`][agents] #"Always give the root-cause fix even when slower".

`handle`'s docstring is not a one-liner: it enumerates the three output branches (newline-suppressed stdout, empty-`--path` rejection, destructive UTF-8 file write) plus the argparse-rejected bare `--path`. A reader of the docstring alone must be able to see all four.

Deliberately NOT declared: a `requires_system_checks` override, a `requires_migrations_checks` override, or a `stealth_options` override.

Why each non-declaration holds, and the rejected alternatives: [the rationale companion][rationale-d2].

### Decision 3 — Symbol resolution through the shared `_imports` command helper

`handle()` resolves the consumer's dotted path through `django_strawberry_framework/management/commands/_imports.py::import_module_symbol_or_command_error`:

```python path=null start=null
schema_symbol = import_module_symbol_or_command_error(
    options["schema"],
    default_symbol_name="schema",
)
```

The helper does three things, in order:

1. **Validates the selector's module path** via `django_strawberry_framework/management/commands/_imports.py::_validate_absolute_module_path`, before any import is attempted. An empty module path (`""`, `":schema"`) and a relative module path (a leading `.`) each raise their own `CommandError` naming the offending value and the reason. Without this, `import_module_symbol` surfaces an unrelated exception (`ValueError` for an empty module name, `TypeError` for a relative import without a package) that the narrow catch would miss and that does not tell the operator what they mistyped.
2. **Delegates resolution, unchanged**, to `strawberry.utils.importer.import_module_symbol(selector, default_symbol_name=...)`. Nothing here re-implements dotted-path parsing.
3. **Translates `ImportError` / `AttributeError` into `CommandError`** via `django_strawberry_framework/management/commands/_imports.py::import_or_command_error`, preserving the original as `__cause__` and using `str(e)` as the message.

Behavior:

- `"config.schema"` → resolves the `config.schema` module attribute named `schema` (the `default_symbol_name` fallback).
- `"config.module:my_schema"` → resolves the `config.module` module attribute named `my_schema`.
- `"does.not.exist"` → `ImportError` → `CommandError` per [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface).
- `"config.module:does_not_exist"` → `AttributeError` → `CommandError`.
- `""` / `":schema"` / `".config.schema"` → rejected before import, with a selector-specific message.

**The helper is shared, and that is why it exists.** `_imports.py` also serves `inspect_django_type` (card `DONE-029-0.0.9`): its `--schema` selector resolves through the same `import_module_symbol_or_command_error`, and its dotted-path positional through the sibling entry point `django_strawberry_framework/management/commands/_imports.py::import_string_or_command_error`, over `django.utils.module_loading.import_string`. Both entry points share `import_or_command_error` and `_validate_absolute_module_path`. Any further command needing the same translation extends this module rather than re-inlining a `try` / `except`.

**No auto-call to [`finalize_django_types()`][glossary-finalize-django-types].** The consumer's `config/schema.py` (or equivalent) calls it before constructing the schema; resolving the dotted path triggers the consumer's module-level imports, which run the finalize call as a side effect. Adding a `finalize_django_types()` call in `handle()` would either be silently redundant (the consumer's module already ran it) or — if the consumer's schema module deferred finalization to a function — would call it too early, before the consumer's imports are complete.

Why resolution is delegated and shared, and three rejected alternatives: [the rationale companion][rationale-d3].

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

Why `print_schema`, and three rejected alternatives (`--json`, `--indent`, `print(...)`): [the rationale companion][rationale-d4].

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

When `call_command(...)` constructs the parser, `called_from_command_line` defaults to `False`, so `CommandParser.error()` raises `CommandError` **directly** — no `SystemExit` is involved anywhere on that path. The `SystemExit(2)` branch is taken only when `manage.py` runs the command from a shell.

1. **Missing positional `schema`.**
2. **`--path` given with no following value.** Reachable only because [Decision 2](#decision-2--command-class-shape) declares no `nargs="?"`.

Both are the load-bearing reason [Decision 8](#decision-8--tests-go-through-call_command-not-direct-handle) requires `call_command`: a direct `Command().handle(...)` call skips argparse entirely, so neither contract would be exercised.

**Selector validation, before any import (two)** — raised by `_validate_absolute_module_path` in `_imports.py` per [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper):

3. **Empty module path** — `""` or `":schema"`. Message: `f"{value!r} is not a valid schema selector: the module path is empty."`
4. **Relative module path** — a leading `.`. Message: `f"{value!r} is not a valid schema selector: relative module paths are not supported."`

**Symbol resolution (one):**

5. **Unimportable dotted path** — `import_module_symbol` raises `ImportError` (module not found) or `AttributeError` (module loads, attribute absent). Both are re-raised as `CommandError(str(e)) from e`, so the original stays reachable through `__cause__`.

**Post-resolution (one):**

6. **Resolved symbol is not a `strawberry.Schema` instance** — `isinstance(schema_symbol, strawberry.Schema)` fails. Raises `CommandError("The `schema` must be an instance of strawberry.Schema")`, verbatim from the upstream wording; the backticks around `schema` are deliberate and the test plan pins the string.

**Output (two):**

7. **`--path` empty or whitespace-only** — `not isinstance(path, str) or not path.strip()`. Raises `CommandError("--path requires a non-empty value")`. The `.strip()` is deliberate: `--path "   "` is as unusable as `--path ""`.
8. **File-write failure** — `pathlib.Path(path).write_text(...)` raises `OSError` (missing parent directory, permission denied, target is a directory) or `ValueError` (a path `pathlib` itself rejects, such as an embedded null byte). Both are caught and re-raised as `CommandError(str(e)) from e`.

**The catches stay narrow, and that is a contract of its own.** `(ImportError, AttributeError)` around resolution and `(OSError, ValueError)` around the write are deliberately not `except Exception`: a `KeyError` inside the consumer's `Schema(...)` constructor, or a `ValueError` raised by the consumer's own module body, must propagate as itself rather than be relabelled a command failure. The test plan pins the resolution-side non-swallowing contracts explicitly.

**Error-message wording — pinned:**

- `CommandError(str(e))` for the resolution and write cases — defers to the underlying message (`"No module named 'does'"`, `"[Errno 2] No such file or directory: …"`). Pinning a prefix would over-constrain the test, since exact wording varies by Python version; tests assert the `CommandError` class and `match=` a stable fragment.
- `CommandError("The `schema` must be an instance of strawberry.Schema")` for the non-`Schema` case — verbatim.
- `CommandError("--path requires a non-empty value")` for the empty-`--path` case — verbatim; pinned by the live tier in both its empty and whitespace-only spellings.

Why `CommandError`, and three rejected alternatives: [the rationale companion][rationale-d5].

### Decision 6 — No watch, indent, JSON, settings-backed defaults, or alias

The command does NOT ship:

- `--watch` mode (file-system watcher + Django autoreload, graphene-django's shape). Reasonable post-`1.0.0` differentiator if consumer demand surfaces; deferred.
- `--indent` (graphene-django's JSON-pretty-printing flag). SDL is whitespace-agnostic; the formatting consumers want belongs in downstream tools.
- `--json` / a JSON-introspection mode (graphene-django's default output). SDL is the Strawberry-native serialization. See [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema).
- Settings-backed defaults from `DJANGO_STRAWBERRY_FRAMEWORK` (graphene-django's `GRAPHENE.SCHEMA` / `SCHEMA_OUTPUT` / `SCHEMA_INDENT` analogs). [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands" forbids preemptive settings; consumers wrap the command in a `Makefile` entry.
- A `dump_schema` / `print_schema` alias. One command name, one canonical invocation.

`add_arguments` therefore registers exactly two arguments and no more.

Rejected alternatives: [the rationale companion][rationale-d6].

### Decision 7 — Test placement: `tests/management/__init__.py` ships

`tests/management/` carries an `__init__.py` shell, as every package-test subdirectory under `tests/` does (`tests/optimizer/__init__.py`, `tests/types/__init__.py`), so pytest collects the modules as `tests.management.<module>`.

[`AGENTS.md`][agents] #"NOT a package, no `__init__.py`" scopes the no-`__init__.py` rule to `examples/fakeshop/tests/`. Package-test subdirectories under `tests/` are not in its scope.

Rejected alternatives: [the rationale companion][rationale-d7].

### Decision 8 — Tests go through `call_command`, NOT direct `handle()`

Every test that **invokes** the command does so through `django.core.management.call_command(...)`, never by instantiating `Command()` and calling `.handle(...)`.

- `call_command` runs the full argparse layer, so the test catches type-coercion and argument-shape mismatches a direct `handle()` call would silently accept — and, decisively, it is the only way to reach failure shapes 1 and 2 in [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface). Django's `CommandParser.error()` raises `CommandError` directly on the `called_from_command_line=False` branch that `call_command` constructs by default; a direct `handle()` call skips argparse and therefore skips `CommandParser.error()` entirely, leaving both contracts unexercised.
- `call_command` captures `self.stdout` / `self.stderr` cleanly through the `stdout=` / `stderr=` kwargs; a direct `handle()` call requires monkey-patching to capture output.

**One narrow exception, and it is not an invocation.** A test may construct `Command().create_parser(...)` to inspect the parser the command builds — that is how `--path`'s help-string contract is pinned. It never calls `handle()` and never runs the command, so the rule above is intact.

The constraint propagates to the live tier: `examples/fakeshop/tests/test_export_schema.py` uses `call_command` exclusively.

Rejected alternatives: [the rationale companion][rationale-d8].

### Decision 9 — Joint `0.0.7` cut

`0.0.7` ships under the joint-cut policy from [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] [Decision 10][spec-020-decision-10--joint-007-cut]: every card in the bundle accumulates `### Added` entries under the same `[0.0.7]` heading in [`CHANGELOG.md`][changelog], and the version bump — the `__version__` literal in `django_strawberry_framework/__init__.py`, the single version source, which `tests/base/test_init.py::test_version` pins — is owned by whichever card ships last in the bundle, NOT this card. The Slice 3 doc-updates list excludes the version bump.

Rejected alternatives: [the rationale companion][rationale-d9].

### Decision 10 — Live coverage belongs in `examples/fakeshop/tests/`, NOT `test_query/`

The live fakeshop coverage lives in `examples/fakeshop/tests/`; it does NOT go under `examples/fakeshop/test_query/`.

- [`examples/fakeshop/test_query/README.md`][test-query-readme] scopes that tree to live GraphQL requests over HTTP to fakeshop's `/graphql/`. The schema-export command is not an HTTP-shaped surface: it does not hit `/graphql/` and does not exercise the request pipeline.
- [`START.md`][start] #"project/config only (urls, settings guard, schema export)" names `examples/fakeshop/tests/` as the home for project/config-level tests, schema export among them.
- [`AGENTS.md`][agents] #"any line reachable via a real GraphQL query against fakeshop"'s coverage-priority rule is satisfied rather than waived: the command's lines are genuinely unreachable from a live `/graphql/` query, so the fall-back tier is the correct one.

**The live tier is not a smoke test.** Where a contract can be driven against the real `config.schema` — imported, finalized, and rendered to SDL — the test belongs here rather than against a synthesized fixture schema; the live form carries strictly stronger contract pressure. The package tier keeps only what has no project-schema shape: the argparse rejections (raised before `handle()` runs), the parser's help string, and the `newline=""` kwarg pin (invisible on an LF platform, so only a call-site capture can assert it).

Rejected alternatives: [the rationale companion][rationale-d10].

## Implementation plan

The card shipped as **three slices** aligned with the [Slice checklist](#slice-checklist). Each slice maps to one commit.

| Slice | Files touched | Tests |
| --- | --- | --- |
| 1 — Module + `Command` subclass | `django_strawberry_framework/management/__init__.py`, `django_strawberry_framework/management/commands/__init__.py`, `django_strawberry_framework/management/commands/export_schema.py`, `django_strawberry_framework/management/commands/_imports.py` (shared helper) | 0 (tests land in Slice 2) |
| 2 — Tests | `tests/management/__init__.py`, `tests/management/test_export_schema.py`, `tests/management/test_imports.py`, `examples/fakeshop/tests/test_export_schema.py` | the three tiers in the [Test plan](#test-plan) |
| 3 — Promotion + docs | `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md` | 0 |

The three slices are authored in order. Slice 2 depends on Slice 1 (the class must exist before tests can `call_command` it); Slice 3 depends on Slice 2 (the [`CHANGELOG.md`][changelog] `### Added` line and [`KANBAN.md`][kanban] Done body must describe a shipped, tested module).

## Edge cases and constraints

- **Django command-discovery is `INSTALLED_APPS`-driven.** `manage.py` discovers the command as long as `"django_strawberry_framework"` is in `INSTALLED_APPS` (the example project carries this entry at `examples/fakeshop/config/settings.py::INSTALLED_APPS`). Django walks the `management/commands/` directory by convention; no `AppConfig` method is involved. The [`Django AppConfig`][glossary-django-appconfig] shipped under [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021] is the entry point `INSTALLED_APPS` resolves to, and command discovery asks nothing of it.
- **`finalize_django_types()` runs as a side effect of resolving the schema symbol.** The consumer's `config/schema.py` calls [`finalize_django_types()`][glossary-finalize-django-types] at module level before constructing `strawberry.Schema(...)`. When the importer loads the module, the finalize call runs as part of its top-level execution. The command does NOT call it.
- **Idempotent reads.** The command reads the consumer's schema; it does not write to the database and does not mutate process state outside Strawberry's own caches. Running it twice produces identical output.
- **Schema symbol is resolved at command-invocation time.** Each `call_command("export_schema", "config.schema")` re-imports `config.schema` or hits the import cache. The cached case is correct: the schema is constructed once and stays constant for the process lifetime.
- **The `isinstance` check uses the public `strawberry.Schema` class**, imported as `from strawberry import Schema`. Subclasses pass, which is right — a `MyCustomSchema(strawberry.Schema)` is a valid export target. This is exercised, not hypothetical: the fakeshop schema the live tier drives is a `DjangoSchema`, a subclass, so narrowing the guard to an exact-type check would fail the live tier immediately.
- **`--path` is destructive and does not create directories.** An existing target is replaced without prompting; a missing parent directory is a `CommandError`, not an implicit `mkdir`. The `--path` help string states the first half so `manage.py export_schema --help` is not silent about it.
- **UTF-8, no newline translation.** `write_text(schema_output, encoding="utf-8", newline="")` is the only encoding shape. Both kwargs are load-bearing per [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema).
- **`tmp_path` for file-write tests.** Live-tier tests that write a real file use pytest's `tmp_path` fixture so written files are auto-cleaned between runs; the package-tier kwarg pin monkeypatches `pathlib.Path.write_text` and writes nothing.
- **`call_command` and `stdout`.** Capture via `stdout=StringIO()` is the documented pattern. Because [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema) suppresses Django's default trailing newline, a captured stdout value equals `print_schema(schema)` exactly — assertions compare for **equality**, not for a substring plus a newline allowance. A test that tolerates a trailing newline would not detect the contract's loss.
- **A `--path`-writing test that captures stdout must still pass `stdout=`.** The success message goes to `self.stdout`, so a `--path` invocation with no `stdout=` kwarg prints into the test runner's output.
- **No per-file ruff escape for the package.** `[tool.ruff.lint.per-file-ignores]` (see `pyproject.toml #"[tool.ruff.lint.per-file-ignores]"`) covers only `__init__.py` (`F401`), `tests/**/*.py`, `examples/**/*.py`, `scripts/**/*.py` (`PERF`), `**/migrations/*.py`, `**/views.py`, `**/urls.py`, and `**/admin.py`. There is **no** `django_strawberry_framework/**` entry, so the module is subject to every gate named in [Decision 2](#decision-2--command-class-shape).
- **`pytest-django` setup.** Tests that invoke the command need Django's app registry populated; `pytest-django` handles this via `django.setup()` once per session. The package tier's kwarg pin uses a fixture-shaped schema constructed in the test module (not pulled from a `DjangoType` registry), so it needs no `pytest.mark.django_db`. The live tier needs none either — the command only reads the schema.
- **Re-importing a moved schema module.** If a consumer reorganizes `config/schema.py` between two invocations in one process, Python's import cache may hold the stale module. That is a fixture concern, not a command bug, and is not tested.

## Test plan

Tests live across three modules in two trees, matching [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Placement is mandatory per [Decision 7](#decision-7--test-placement-testsmanagement__init__py-ships) and [Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query).

### `tests/management/__init__.py`

Empty marker module with a one-line docstring (`"""Package tests for django-strawberry-framework management commands."""`). Required for pytest to collect tests as `tests.management.<module>` and to satisfy `D100`. No further content.

### `tests/management/test_export_schema.py`

Package tier; system-under-test is `django_strawberry_framework.management.commands.export_schema`. It holds only the contracts with no project-schema shape ([Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query)); selectors use the **explicit `:symbol` form**.

- **Missing positional argument** — `::test_export_schema_raises_command_error_for_missing_positional_argument`: `call_command("export_schema")`, `pytest.raises(CommandError)`. Pins the `CommandParser.error()` path of [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface).
- **Bare `--path` with no value** — `::test_export_schema_raises_command_error_when_path_flag_has_no_value`: `call_command("export_schema", "config.schema:schema", "--path")`, `match="expected one argument"`. Pins the argparse rejection that declaring no `nargs="?"` buys.
- **`--path` help string** — `::test_export_schema_path_help_documents_destructive_utf8_write`: reads the action off `Command().create_parser("manage.py", "export_schema")` and asserts `help == "Write UTF-8 SDL to this file, overwriting it without prompting"`. This is the one permitted `Command()` construction ([Decision 8](#decision-8--tests-go-through-call_command-not-direct-handle)); it makes the destructive-overwrite disclosure a contract rather than prose.
- **Newline translation disabled** — `::test_export_schema_file_write_disables_newline_translation`: monkeypatches `pathlib.Path.write_text` to capture its kwargs and asserts `encoding == "utf-8"` and `newline == ""`. Pinning the kwarg at the call site is the only way to assert it: the effect is invisible on an LF platform.

**Fixture-module cleanup contract.** The kwarg-pin test synthesizes `test_module` via `monkeypatch.setitem(sys.modules, "test_module", module)` where `module = types.ModuleType("test_module")`, with a fixture `strawberry.Schema` assigned as `schema`. Pytest's `monkeypatch` teardown removes the entry from `sys.modules` at end of test; a bare `sys.modules["test_module"] = module` assignment would leave the module cached and make any later test synthesizing `test_module` order-dependent.

### `tests/management/test_imports.py`

The shared helper's own tier: every branch of `_imports.py`, and in particular the two negative contracts that keep the catches narrow:

- `::test_import_or_command_error_does_not_swallow_other_exceptions` — an exception that is neither `ImportError` nor `AttributeError` propagates as itself.
- `::test_import_module_symbol_or_command_error_does_not_mask_module_body_valueerror` — a `ValueError` raised by the *consumer's module body* during import is not relabelled a `CommandError`, even though a `ValueError` raised by `pathlib` during the write is ([Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface) shape 8). The two are different failures and must report differently.
- `::test_import_module_symbol_or_command_error_applies_default_symbol_name` — pins the `default_symbol_name="schema"` fallback at the helper, so a refactor dropping the kwarg fails here as well as in the live tier.

### `examples/fakeshop/tests/test_export_schema.py`

Live tier, driven against the real `config.schema`. Most tests use the bare `"config.schema"` selector with no `:schema` suffix, so the `default_symbol_name` fallback is pinned by real usage throughout.

- **SDL to stdout** — `::test_export_schema_writes_fakeshop_sdl_to_stdout_by_default`: `call_command("export_schema", "config.schema:schema", stdout=out)`; asserts `"type BranchType"` in the captured value. Pins end-to-end resolution of the consumer's real schema — a `DjangoSchema` built through [`finalize_django_types()`][glossary-finalize-django-types] — rather than a synthesized fixture.
- **Three-way byte identity** — `::test_export_schema_stdout_matches_print_schema` (parametrized over `"config.schema:schema"` and `"config.schema"`) asserts captured stdout equals `print_schema(schema)`, and `::test_export_schema_path_file_matches_print_schema` asserts the `--path` file's UTF-8 text equals it too. These pin [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema)'s stdout newline suppression: with `ending=""` removed the stdout test fails.
- **Unimportable module** — `::test_export_schema_raises_command_error_for_unimportable_module`: `"does.not.exist:schema"`, `match="No module named"`. Pins the `ImportError` half of the resolution wrapper.
- **Missing attribute on an importable module** — `::test_export_schema_raises_command_error_for_missing_attribute_on_module`: `"config.schema:does_not_exist"`, `match="does_not_exist"`. Pins the `AttributeError` half, so a refactor narrowing the catch to `ImportError` alone fails.
- **Non-`Schema` resolved symbol** — `::test_export_schema_raises_command_error_for_non_schema_symbol`, parametrized over a `DjangoType` class (`apps.library.schema:BookType`), a model class (`apps.products.models:Item`), and a settings value (`config.settings:DEBUG`); asserts `match=r"must be an instance of strawberry\.Schema"`. Pins the isinstance branch and the exact wording.
- **Malformed selector** — `::test_export_schema_raises_command_error_for_malformed_selector`, parametrized over `""`, `":schema"`, `".config.schema"`, matching `"module path is empty"` and `"relative module paths"`.
- **Whitespace-only `--path`** — `::test_export_schema_raises_command_error_when_path_flag_is_whitespace_only`, parametrized over spaces, tab, and newline; `match="--path requires a non-empty value"`. Pins the `.strip()`.
- **Empty-string `--path`** — `::test_export_schema_raises_command_error_when_path_flag_is_empty_string`: `--path ""`, same match.
- **Destructive overwrite via `--path`** — `::test_export_schema_overwrites_existing_path_with_utf8_fakeshop_sdl`: writes a sentinel string to the target first, then runs the command; asserts the SDL landed, the sentinel is gone, and `Wrote schema to <path>` appears on stdout. One test pins three contracts: the write, the overwrite, and the success message.
- **Missing parent directory** — `::test_export_schema_raises_command_error_when_path_directory_missing`: `match="No such file or directory"`. Pins the `OSError` half of the write-failure catch.
- **Embedded null byte in `--path`** — `::test_export_schema_raises_command_error_when_path_contains_embedded_null`: `match="embedded null byte"`. Pins the `ValueError` half of the write-failure catch.

Each `pytest.mark.parametrize` fans one assertion out over inputs that share one boundary; elsewhere, one pytest item per test. No `pytest.mark.django_db` is needed — the command performs no database access.

No live `/graphql/` HTTP test is required; the command is not HTTP-shaped.

Why one negative-shape test is not authored: [the rationale companion][rationale-test-plan].

## Doc updates

- [`docs/GLOSSARY.md`][glossary] (rendered from the glossary DB)
  - [`Schema export management command`][glossary-schema-export-management-command] reads `shipped (0.0.7)` in the entry and in the Index table.
  - The entry body describes the shipped contract: `django_strawberry_framework/management/commands/export_schema.py` ships `Command(BaseCommand)` with positional `schema` (dotted path, default symbol name `"schema"`) and optional `--path`; SDL output via `strawberry.printer.print_schema`, with the stdout write, the `--path` file and `print_schema`'s return value the same bytes; a destructive UTF-8 write with a `Wrote schema to <file>` success message; `CommandError` for every failure shape in [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface); no `--watch` / `--indent` / JSON mode / settings-backed defaults.

- [`docs/README.md`][readme]
  - Names `manage.py export_schema <dotted.path.to.schema>` beside `manage.py inspect_django_type` as the command that prints or writes the SDL.

- [`docs/TREE.md`][tree] (rendered from module docstrings)
  - The package tree lists `management/` → `commands/` with `_imports.py` and `export_schema.py`; the test tree lists `tests/management/` with `test_export_schema.py` and `test_imports.py`, and `examples/fakeshop/tests/` with `test_export_schema.py`.

- [`KANBAN.md`][kanban]
  - The card sits in the Done column as `DONE-022-0.0.7`; its past-tense Done body summarizes the shipped scope.

- [`CHANGELOG.md`][changelog]
  - The `[0.0.7]` `### Added` subsection — one heading shared with every `0.0.7` card under the joint cut per [Decision 9](#decision-9--joint-007-cut), beside `DONE-020-0.0.7`'s [`DjangoListField`][glossary-djangolistfield] entry and `DONE-021-0.0.7`'s [`Django AppConfig`][glossary-django-appconfig] entry — carries this card's `Schema export management command` entry.
  - The version bump is owned by **the last `0.0.7` card to ship** per [Decision 9](#decision-9--joint-007-cut), NOT this slice.
  - [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" — this Slice 3 bullet is the explicit instruction.

- No edits to [`README.md`][readme-root]: its status section names consumer-facing primitives, and the command is plumbing reachable via `manage.py` rather than via a consumer import.
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
2. `django_strawberry_framework/management/commands/export_schema.py` exists and defines `Command(BaseCommand)` per [Decision 2](#decision-2--command-class-shape) — `help = "Export the GraphQL schema"`, `add_arguments(self, parser: CommandParser) -> None` registering positional `schema` (`type=str, help="The schema location"`, no `nargs`) and optional `--path` (`type=str, help="Write UTF-8 SDL to this file, overwriting it without prompting"`, no `nargs`), and `handle(self, *args: object, **options: Any) -> None` per [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper), [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema), and [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface), both methods decorated `@override`. Module docstring (`D100`), class docstring (`D101`), and docstrings on both methods (`D102`) all present, with `handle`'s enumerating its output branches. `parser: CommandParser` and `-> None` on both methods (`ANN001` / `ANN201`). No `--watch`, `--indent`, `--json`, settings-backed defaults, or alias (per [Decision 6](#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias)). No `# noqa` suppressions for any `D` or `ANN` rule.
3. `django_strawberry_framework/management/commands/_imports.py` carries the shared import translation and the pre-import selector validation per [Decision 3](#decision-3--symbol-resolution-through-the-shared-_imports-command-helper); `export_schema.py` contains no inline `try` / `except (ImportError, AttributeError)`.
4. `django_strawberry_framework/__init__.py` does not export `Command` (per [Decision 1](#decision-1--module-location--no-public-export)); `tests/base/test_init.py`'s `__all__` assertion does not name it.
5. `tests/management/__init__.py` exists with a one-line module docstring. `tests/management/test_export_schema.py` covers every contract listed for it in the [Test plan](#test-plan) — the two argparse shapes, the help string, the `newline=""` kwarg pin — and `tests/management/test_imports.py` covers every branch of the shared helper including the two non-swallowing contracts.
6. `examples/fakeshop/tests/test_export_schema.py` carries the live tier per [Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query): SDL content, three-way byte identity, and [Decision 5](#decision-5--commanderror-is-the-commands-only-failure-surface) shapes 3-8 (shape 7 in both its empty and whitespace-only spellings, shape 8 in both its `OSError` and `ValueError` halves). No file under `examples/fakeshop/test_query/` is created.
7. Every test that invokes the command uses `django.core.management.call_command(...)` per [Decision 8](#decision-8--tests-go-through-call_command-not-direct-handle); the only `Command()` construction anywhere is the parser-inspection test, which never calls `handle()`.
8. `examples/fakeshop/config/settings.py` is NOT modified (the existing `"django_strawberry_framework"` entry in `INSTALLED_APPS` is sufficient for Django to discover the command).
9. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`) — **verified by CI's gate, not by the worker locally.** The worker's local verification is item 14's `uv run pytest --no-cov` suite-passing check, in line with [`docs/builder/BUILD.md`][build]'s "Coverage is the maintainer's gate, not a worker's tool" rule. If CI reports a coverage regression on the PR, the worker adds the missing test before merge.
10. [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][readme], [`docs/TREE.md`][tree], [`KANBAN.md`][kanban], and [`CHANGELOG.md`][changelog] reflect the shipped state per the [Doc updates](#doc-updates) section. [`README.md`][readme-root], [`GOAL.md`][goal], and [`TODAY.md`][today] are NOT edited.
11. [`KANBAN.md`][kanban] carries the card in Done as `DONE-022-0.0.7` with a past-tense body summarizing the shipped scope.
12. The version bump is NOT in this card per [Decision 9](#decision-9--joint-007-cut); the last `0.0.7` card to ship owns `__version__` in `django_strawberry_framework/__init__.py`.
13. Zero new public exports — `__all__` is unchanged.
14. `uv run ruff check --fix .` passes; `uv run ruff format .` passes; `uv run pytest --no-cov` passes (the explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov`; workers verify the suite passes, not that coverage stays at 100%).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[readme-root]: ../../README.md
[start]: ../../START.md
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
