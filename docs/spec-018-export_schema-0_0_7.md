# Spec: `export_schema` management command

Target release: `0.0.7`.
Status: draft (revision 1).
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`](GLOSSARY.md) (entries [`Schema export management command`](GLOSSARY.md#schema-export-management-command), [`Django AppConfig`](GLOSSARY.md#django-appconfig), [`DjangoType`](GLOSSARY.md#djangotype), [`DjangoOptimizerExtension`](GLOSSARY.md#djangooptimizerextension), [`finalize_django_types`](GLOSSARY.md#finalize_django_types)); [`KANBAN.md`](../KANBAN.md) card `WIP-ALPHA-018-0.0.7`; shipped predecessor [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) (the [`Django AppConfig`](GLOSSARY.md#django-appconfig) it landed is what makes Django's `INSTALLED_APPS`-driven management-command discovery resolve through this package); joint-cut policy spec [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) (Decision 10 — joint `0.0.7` cut, reused verbatim in [Decision 9](#decision-9--joint-0_0_7-cut) here).

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Pins module location (`django_strawberry_framework/management/commands/export_schema.py` with empty `__init__.py` markers at `management/` and `management/commands/`), command class shape (`Command(BaseCommand)` with `help = "Export the GraphQL schema"`, positional `schema` dotted path, optional `--path`), symbol resolution via `strawberry.utils.importer.import_module_symbol(..., default_symbol_name="schema")`, SDL output via `strawberry.printer.print_schema`, `CommandError` for three failure modes (unimportable dotted path; resolved symbol is not a `strawberry.Schema`; missing positional argument), test placement at `tests/management/test_export_schema.py` with a sibling `tests/management/__init__.py` (mirrors the `tests/optimizer/` / `tests/types/` convention per [`docs/TREE.md`](TREE.md) line 457; the [`AGENTS.md`](../AGENTS.md) line 6 "do not add `__init__.py`" rule applies only to the two `examples/fakeshop/` test trees), live fakeshop coverage placed in `examples/fakeshop/tests/test_commands.py` (extends the existing file via `call_command`, NOT in `examples/fakeshop/test_query/` because the command is not an HTTP-shaped surface), tests use `django.core.management.call_command` exclusively (NOT direct `Command().handle(...)` calls — pinned in [Decision 8](#decision-8--tests-go-through-call_command-not-direct-handle)), the deliberate omissions of JSON output / `--watch` / `--indent` / settings-backed defaults / a `dump_schema` alias / `default_auto_field` (every one rejected with reason), the joint-`0.0.7` cut policy (this card does NOT bump `pyproject.toml`, `__version__`, or `tests/base/test_init.py`'s pinned version unless it ships last), zero new public exports (the command is import-time plumbing, not a `__all__` entry), and the doc-updates list across [`docs/GLOSSARY.md`](GLOSSARY.md), [`docs/README.md`](README.md), [`docs/TREE.md`](TREE.md), [`KANBAN.md`](../KANBAN.md), and [`CHANGELOG.md`](../CHANGELOG.md) (no [`README.md`](../README.md), [`GOAL.md`](../GOAL.md), or [`TODAY.md`](../TODAY.md) edits — the command is not a consumer name-surface change and the fakeshop schema is unchanged).

## Key glossary references

Skim these [`docs/GLOSSARY.md`](GLOSSARY.md) entries first — they anchor the vocabulary used throughout the spec:

- [`Schema export management command`](GLOSSARY.md#schema-export-management-command) — the entry this card flips from `planned for 0.0.7` to `shipped (0.0.7)` in [Slice 3](#implementation-plan).
- [`Django AppConfig`](GLOSSARY.md#django-appconfig) — the predecessor that makes Django's `INSTALLED_APPS`-driven management-command discovery resolve through this package; see [Decision 1](#decision-1--module-location--no-public-export) for why this card's `management/` tree composes cleanly on top of `0.0.7`'s explicit `DjangoStrawberryFrameworkConfig`.
- [`DjangoType`](GLOSSARY.md#djangotype) — the consumer-facing type the exported SDL describes; not directly imported by the command but the reason the command exists.
- [`finalize_django_types`](GLOSSARY.md#finalize_django_types) — the consumer-owned synchronization point that must have run before the consumer's `schema = strawberry.Schema(...)` is constructed; the command resolves the consumer's symbol after the consumer's import-time wiring has executed, so this card does NOT call [`finalize_django_types`](GLOSSARY.md#finalize_django_types) itself (see [Decision 3](#decision-3--symbol-resolution-via-strawberryutilsimporterimport_module_symbol)).
- [`DjangoOptimizerExtension`](GLOSSARY.md#djangooptimizerextension) — present on the consumer's `strawberry.Schema(...)` but not exercised at export time; the SDL output is the static type system, not a runtime execution.
- [`ConfigurationError`](GLOSSARY.md#configurationerror) — not raised by anything in this card; `CommandError` (Django) is the exclusive error class for export-time failures per [Decision 5](#decision-5--commanderror-for-three-failure-modes).

Project conventions to follow:

- [`AGENTS.md`](../AGENTS.md) — line 6 (test placement; package tests live under `tests/`, example-project non-HTTP tests under `examples/fakeshop/tests/`, no `__init__.py` under the two `examples/fakeshop/` test trees but package-test subdirectories like `tests/optimizer/` and `tests/types/` carry `__init__.py`); line 9 ("any coverage line achievable via a real GraphQL query against fakeshop in `examples/fakeshop/test_query/` MUST be earned that way; fall back to `examples/fakeshop/tests/` … or `tests/` only when the line is genuinely unreachable from a real-world query"); line 14 ("Do not run pytest after edits"); line 20 ("Add settings keys only when the feature that needs them lands; do not preemptively populate"). **Note:** line 21 prohibits [`CHANGELOG.md`](../CHANGELOG.md) edits without explicit permission; [Slice 3](#implementation-plan) grants that permission for this card's `[0.0.7]` `### Added` append.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — 100% coverage target.
- [`KANBAN.md`](../KANBAN.md) — card-ID format; column movement at Slice 3.
- [`docs/TREE.md`](TREE.md) — package layout; tests mirror source one-to-one. The `management/` subtree already appears in the target layout at line 309 with the `[alpha]` tag, and [`docs/TREE.md`](TREE.md) line 461 confirms `examples/fakeshop/tests/` is the canonical home for "management commands via `call_command`."

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Three slices total.

- [ ] Slice 1: Module + `Command` subclass
  - [ ] New flat package `django_strawberry_framework/management/` with a one-line module docstring `__init__.py` (empty marker).
  - [ ] New flat package `django_strawberry_framework/management/commands/` with a one-line module docstring `__init__.py` (empty marker).
  - [ ] New module `django_strawberry_framework/management/commands/export_schema.py` housing `Command(BaseCommand)` per [Decision 2](#decision-2--command-class-shape) — `help = "Export the GraphQL schema"`, positional `schema` (single value, dotted path), optional `--path`, `handle(self, *args, **options)` body that (a) resolves the symbol via `strawberry.utils.importer.import_module_symbol(options["schema"][0], default_symbol_name="schema")` per [Decision 3](#decision-3--symbol-resolution-via-strawberryutilsimporterimport_module_symbol), (b) raises `CommandError` on `ImportError` / `AttributeError` per [Decision 5](#decision-5--commanderror-for-three-failure-modes), (c) raises `CommandError` when the resolved symbol is not a `strawberry.Schema` instance per [Decision 5](#decision-5--commanderror-for-three-failure-modes), (d) writes SDL via `strawberry.printer.print_schema(schema_symbol)` per [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema), (e) routes to `pathlib.Path(path).write_text(..., encoding="utf-8")` when `--path` is set, otherwise to `self.stdout.write(...)`.
  - [ ] Do NOT implement a settings-backed default for `schema` (per [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias)).
  - [ ] Do NOT implement `--watch`, `--indent`, `--json`, a `dump_schema` / `print_schema` alias, or a JSON-introspection mode (per [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias)).
  - [ ] Do NOT re-export `Command` from `django_strawberry_framework/__init__.py` (per [Decision 1](#decision-1--module-location--no-public-export)). The class is import-time plumbing Django's command-discovery resolves through `INSTALLED_APPS`; consumers never write `from django_strawberry_framework.management.commands.export_schema import Command`.
  - [ ] One-line module docstring on `export_schema.py` (required by `D100`); one-line class docstring on `Command` (required by `D101`). Module docstring: `"""manage.py export_schema — print or write the GraphQL SDL for a Strawberry schema symbol."""`. Class docstring: `"""Export the GraphQL SDL for a strawberry.Schema symbol."""` (or equivalent one-liner). Do NOT suppress with `# noqa: D100` / `# noqa: D101` — the docstrings are the root-cause fix per [`AGENTS.md`](../AGENTS.md) line 4. Same posture as [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) rev3 H1 / rev4 L3.
  - [ ] `management/__init__.py` and `management/commands/__init__.py` each carry a one-line module docstring (required by `D100`). Suggested: `"""Django management entry points for django-strawberry-framework."""` and `"""Management command implementations for django-strawberry-framework."""`.
- [ ] Slice 2: Tests
  - [ ] New `tests/management/__init__.py` (empty marker; mirrors the `tests/optimizer/` / `tests/types/` shell per [`docs/TREE.md`](TREE.md) line 457) plus one-line module docstring `"""Package tests for django_strawberry_framework.management.*."""` (required by `D100`).
  - [ ] New `tests/management/test_export_schema.py` covering the four contracts pinned in [Test plan](#test-plan): happy-path stdout output, happy-path `--path` file write, `CommandError` for each of the three failure modes ([Decision 5](#decision-5--commanderror-for-three-failure-modes)), and a positive test that the resolved symbol's default-name fallback (`default_symbol_name="schema"`) works when the consumer omits the trailing `:schema` suffix.
  - [ ] Tests exclusively use `django.core.management.call_command` (NOT `Command().handle(...)`) per [Decision 8](#decision-8--tests-go-through-call_command-not-direct-handle).
  - [ ] Extend `examples/fakeshop/tests/test_commands.py` (existing file under `examples/fakeshop/tests/`; do NOT add `examples/fakeshop/test_query/test_export_schema.py` per [Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query)) with one live test that runs `call_command("export_schema", "config.schema", "--path", str(tmp_path / "schema.graphql"))` against the fakeshop schema and asserts the produced SDL contains a known type from the `library` app (e.g., `"type Branch"`).
- [ ] Slice 3: Promotion + docs
  - [ ] Flip [`Schema export management command`](GLOSSARY.md#schema-export-management-command) from `planned for 0.0.7` to `shipped (0.0.7)` in [`docs/GLOSSARY.md`](GLOSSARY.md); update the Index table's status column at line 104; update the entry body to describe the shipped command shape.
  - [ ] Update [`docs/README.md`](README.md): **surgically remove the entire `- schema export management command` bullet at line 113** from the `Coming in 0.1.0` section (DONE-017-0.0.7 surgically removed only `, Django `AppConfig`` from that line; this card removes the remaining text in full and deletes the whole bullet). The shipped-list heading at line 89 already reads `**Shipped today** (`0.0.7`):` (DONE-017 bumped it); no further heading change here.
  - [ ] Update [`docs/TREE.md`](TREE.md): add the `management/` subtree to the **current on-disk layout** section under the `django_strawberry_framework/` tree (alphabetical position between `list_field.py` and `optimizer/`), with the `commands/__init__.py` + `commands/export_schema.py` children spelled out; remove the `[alpha]` tag from the existing `management/` block in the **target package layout** section at lines 309-313 (the tag means "lands before `0.1.0`", and the bullet has now landed). Add `tests/management/test_export_schema.py` (with sibling `__init__.py`) to the **current test-tree** section; placement is **before `test_apps.py`** (alphabetical — `management/` sorts before `test_apps.py`).
  - [ ] Update [`KANBAN.md`](../KANBAN.md): move `WIP-ALPHA-018-0.0.7` to the Done column with the next available `DONE-NNN-0.0.7` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). The past-tense Done body summarizes the shipped scope.
  - [ ] Update [`CHANGELOG.md`](../CHANGELOG.md): **append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading per [Decision 9](#decision-9--joint-0_0_7-cut) — every `0.0.7` card under the joint cut appends to the same shared section).
  - [ ] No edits to [`README.md`](../README.md), [`GOAL.md`](../GOAL.md), or [`TODAY.md`](../TODAY.md). Justification: the command is `manage.py` plumbing, not a consumer-name surface change; the fakeshop schema is unchanged by this card. Same posture as [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) Slice 3 for the AppConfig.
  - [ ] Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; per [Decision 9](#decision-9--joint-0_0_7-cut)): see [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) Decision 10. This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s version assertion.
  - [ ] Zero new public exports — the management command is import-time plumbing discovered through Django's `INSTALLED_APPS` machinery, not via `from django_strawberry_framework import …`. `__all__` is unchanged.
  - [ ] Final gates (same posture as [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) rev6 L2):
    - [ ] `uv run ruff format .` passes.
    - [ ] `uv run ruff check --fix .` passes.
    - [ ] `uv run pytest --no-cov` (or scoped subset) passes; the explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per the per-pass-gates contract; coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`), not this slice's.

## Problem statement

`django_strawberry_framework` ships no `manage.py` surface today. The package's [`docs/README.md`](README.md) `Coming in 0.1.0` block (line 113) advertises a "schema export management command" but the implementation has been deferred. Consumers who want to emit the GraphQL SDL — for client codegen (`graphql-codegen`, `graphql-cli`), CI schema-diffing, SDL-as-artifact in releases, or human-readable schema review — currently hand-roll a script that imports their schema and calls `strawberry.printer.print_schema`. Both reference packages ship the command:

- `strawberry-django` ships a 38-line [`management/commands/export_schema.py`](GLOSSARY.md#schema-export-management-command) (verified at `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/management/commands/export_schema.py`): positional `schema` dotted path, optional `--path`, SDL output via `strawberry.printer.print_schema`, `CommandError` on `ImportError` / `AttributeError` and on a resolved symbol that is not a `strawberry.Schema` instance.
- `graphene-django` ships a 111-line `graphql_schema.py` (verified at `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/management/commands/graphql_schema.py`): `--schema` / `--out` / `--indent` / `--watch`, settings-backed defaults from `GRAPHENE.SCHEMA` / `SCHEMA_OUTPUT` / `SCHEMA_INDENT`, JSON-by-default with `.graphql` / `.json` extension inference.

The asymmetry is small but real: migrants from `strawberry-django` know the command as `manage.py export_schema`; migrants from `graphene-django` know it as `manage.py graphql_schema`. We borrow the strawberry-django name + shape (SDL output, positional schema dotted path); we deliberately do not borrow the graphene-django JSON / `--watch` / `--indent` / settings-backed defaults (each is a post-`1.0.0` differentiator if consumer demand surfaces — see [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias)).

The shipping bar is intentionally low — the command is `~40` lines of `Command(BaseCommand)` plus its `management/__init__.py` and `management/commands/__init__.py` markers. The discipline the card needs to enforce is **what NOT to put in it**: no settings keys, no introspection-JSON mode, no autoreload watcher, no aliases. Each of those is a future-spec home (or, for the settings-backed defaults, an explicit anti-pattern under [`AGENTS.md`](../AGENTS.md) line 20).

The predecessor [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md)'s [Decision 4](SPECS/spec-017-apps-0_0_7.md#decision-4--no-readyhook-in-0_0_7) deliberately deferred any [`Django AppConfig`](GLOSSARY.md#django-appconfig) `ready()` body. Django's management-command discovery is directory-convention-based (`management/commands/`), **not** AppConfig-method-based — so this card needs no follow-up to 017's AppConfig. The two cards compose cleanly.

## Current state

- `django_strawberry_framework/` ships the modules listed in [`docs/TREE.md`](TREE.md) lines 188-225 (`__init__.py`, `apps.py` — landed under [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md), `conf.py`, `exceptions.py`, `list_field.py`, `registry.py`, `scalars.py`, the `optimizer/`, `types/`, and `utils/` subpackages) and `py.typed`. There is no `management/` subdirectory on disk today; the target layout at [`docs/TREE.md`](TREE.md) line 309 lists `management/ # [alpha] Django management commands` with the `[alpha]` tag meaning "lands before `0.1.0`."
- `examples/fakeshop/config/schema.py` exposes a top-level `schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` symbol; the live-coverage test in Slice 2 resolves through the dotted path `"config.schema"` (Strawberry's `import_module_symbol` falls back to the default symbol name `"schema"` when no `:symbol_name` suffix is given).
- `examples/fakeshop/config/schema.py` calls [`finalize_django_types()`](GLOSSARY.md#finalize_django_types) before constructing the schema. By the time the management command imports `config.schema`, the finalize call has already run as a side effect of the module's top-level execution; this card does NOT need to call [`finalize_django_types()`](GLOSSARY.md#finalize_django_types) itself. See [Decision 3](#decision-3--symbol-resolution-via-strawberryutilsimporterimport_module_symbol).
- `examples/fakeshop/tests/test_commands.py` is the existing example-project test home for management commands invoked via `call_command`. The file currently covers the project-side `seed_data`, `delete_data`, `seed_shards`, `create_users`, and `delete_users` commands. Adding one test for `export_schema` extends it in place; no new file is needed under `examples/fakeshop/tests/`. The README at `examples/fakeshop/test_query/README.md` is explicit that `test_query/` is for live `/graphql/` HTTP tests via `django.test.Client`; an SDL-export command is not an HTTP-shaped surface.
- `tests/optimizer/__init__.py` and `tests/types/__init__.py` exist on disk (verified by listing `tests/`); the package-test-subdirectory convention is well-established. `tests/management/__init__.py` follows the same pattern.
- `tests/base/test_init.py` pins the package's `__all__` tuple; the command is NOT a public export (see [Decision 1](#decision-1--module-location--no-public-export)) so this assertion stays unchanged in `0.0.7`.
- `WIP-ALPHA-018-0.0.7`'s [`KANBAN.md`](../KANBAN.md) card body (lines 77-153 of the current file) carries a pinned "Recommended architectural direction" block that this spec preserves verbatim and expands with rationale. The card body explicitly defers the spec author from re-litigating the command shape; the spec's job is to pin the open questions (test placement, error wording, the `tests/management/__init__.py` question).
- `pyproject.toml` line 30 pins `strawberry-graphql>=0.262.0`. `strawberry.utils.importer.import_module_symbol` (verified at `.venv/lib/python3.10/site-packages/strawberry/utils/importer.py:4`) and `strawberry.printer.print_schema` (verified at `.venv/lib/python3.10/site-packages/strawberry/printer/printer.py`) are both already in the dependency tree; the command adds no new dependency.

## Goals

1. Ship `django_strawberry_framework/management/commands/export_schema.py` containing `Command(BaseCommand)` with the strawberry-django-shaped signature: positional `schema` (single value, dotted path; default symbol name `"schema"` via Strawberry's `import_module_symbol`), optional `--path` (write to file, UTF-8). Absent `--path` writes SDL to `self.stdout`.
2. Ship `django_strawberry_framework/management/__init__.py` and `django_strawberry_framework/management/commands/__init__.py` as one-line-docstring marker modules (required by `D100`; no additional content).
3. Ship `tests/management/__init__.py` (one-line docstring marker) and `tests/management/test_export_schema.py` covering the four contracts pinned in [Test plan](#test-plan).
4. Extend `examples/fakeshop/tests/test_commands.py` with one live test that runs `call_command("export_schema", "config.schema", "--path", str(tmp_path / "schema.graphql"))` and asserts the SDL contains a known type from the `library` app (`"type Branch"`).
5. Preserve [`AGENTS.md`](../AGENTS.md) line 20's "Add settings keys only when the feature that needs them lands" by omitting `GRAPHENE.SCHEMA`-style settings-backed defaults. Future cards add what they need; this card adds the bare command.
6. Keep `__all__` unchanged. The command is import-time plumbing; consumers reach it via Django's `manage.py` machinery, not via `from django_strawberry_framework import …`.

## Non-goals

- JSON introspection output (graphene-django's default mode). See [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema).
- `--watch` mode (file-system watcher + Django autoreload). See [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias).
- Settings-backed default schema dotted path (graphene-django's `GRAPHENE.SCHEMA` / `SCHEMA_OUTPUT` / `SCHEMA_INDENT` analogs). See [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias).
- An `--indent` / SDL-formatting option. SDL is whitespace-agnostic; the formatting the consumer wants belongs in downstream tools (`prettier --parser graphql`, `graphql-cli`).
- A `dump_schema` / `print_schema` alias. See [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias).
- Auto-resolving the schema from settings (`SCHEMA = "config.schema"` style). The positional argument is the canonical input; the test surface treats it as required.
- Auto-calling [`finalize_django_types()`](GLOSSARY.md#finalize_django_types) before printing. The consumer's `config/schema.py` (or equivalent) owns that call; resolving the schema symbol triggers the consumer's module-level imports, which already invoke [`finalize_django_types()`](GLOSSARY.md#finalize_django_types). See [Decision 3](#decision-3--symbol-resolution-via-strawberryutilsimporterimport_module_symbol).
- A re-export of `Command` from `django_strawberry_framework/__init__.py`. See [Decision 1](#decision-1--module-location--no-public-export).
- A second [`Django AppConfig`](GLOSSARY.md#django-appconfig) hook for the command. Django's `manage.py` discovers commands by walking `management/commands/` directories in installed apps — no AppConfig method is involved. See the [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) [Decision 4](SPECS/spec-017-apps-0_0_7.md#decision-4--no-readyhook-in-0_0_7) `ready()`-body deferral, which is preserved here.

## Borrowing posture

The two reference packages take opposite stances on the command's surface. The slice borrows the shape from `strawberry-django` and explicitly does not borrow `graphene-django`'s feature creep.

### From `strawberry-django` — borrow the command shape verbatim

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/management/commands/export_schema.py` (referenced from [`docs/TREE.md`](TREE.md) lines 108-112).

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

- **Positional `schema` + optional `--path` + SDL via `print_schema`.** Same shape adopted here. Justification: this is the minimal Django-correct surface for the command. Strawberry's printer is the canonical SDL serializer for a `strawberry.Schema`; reusing the upstream importer + printer keeps the command body trivial and avoids re-implementing dotted-path resolution.
- **`CommandError` on `ImportError` / `AttributeError`.** Same shape adopted here per [Decision 5](#decision-5--commanderror-for-three-failure-modes). Justification: `CommandError` is Django's documented escape hatch for "the command can't proceed and it's the user's fault, not a bug"; both upstreams use it for the same purpose.
- **`CommandError` on non-`Schema` resolved symbol.** Same shape adopted here. The exact error message is pinned in [Decision 5](#decision-5--commanderror-for-three-failure-modes) — we capitalize differently (`"The "` → `"The "` is unchanged) and adopt the wording verbatim because the test plan pins it for regression safety and the consumer-visible string is not worth diverging on.
- **No `--watch`, no `--indent`, no JSON.** strawberry-django ships none; neither do we. See [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias).
- **Class-level `help` attribute.** Same. Wording: `"Export the GraphQL schema"` (Title Case `GraphQL` for consistency with the repo's prose; the upstream uses lowercase `"Export the graphql schema"`). This is one of two forced cosmetic divergences from the upstream string; the test plan pins both so the choice is durable.
- **Two forced divergences** (same posture as [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) [Borrowing posture](SPECS/spec-017-apps-0_0_7.md#borrowing-posture) "two forced divergences"): this repo's pydocstyle gate (`pyproject.toml [tool.ruff.lint] select = [..., "D", ...]`) enables both `D100` and `D101`; neither is in the ignore list. The upstream `strawberry_django/management/commands/export_schema.py` has neither a module docstring nor a class docstring. We add one of each; see [Decision 2](#decision-2--command-class-shape) and the [Slice checklist](#slice-checklist) Slice 1 sub-bullets.

### From `graphene-django` — explicitly do not borrow

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/management/commands/graphql_schema.py` (referenced from [`docs/TREE.md`](TREE.md) lines 45-50).

The upstream is 111 lines and ships:

- `--schema` named flag (we use the positional shape per strawberry-django).
- `--out` with `-` for stdout and `.graphql` / `.json` extension inference (we use `--path`, no extension inference, and stdout when `--path` is absent — simpler and less surprising).
- `--indent` for JSON-introspection pretty-printing (we ship no JSON mode, so no `--indent`).
- `--watch` via `django.utils.autoreload` (we ship no watcher — see [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias)).
- Settings-backed defaults from `graphene_settings.SCHEMA` / `SCHEMA_OUTPUT` / `SCHEMA_INDENT` (we ship none — see [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias)).
- JSON-introspection as the default output mode (we ship SDL exclusively — see [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema)).

Each non-borrowed element is justified in [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema), [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias), and [Out of scope](#out-of-scope-explicitly-tracked-elsewhere). The headline justification: graphene-django's surface accreted across many years as consumer demand shifted; we ship the minimum useful command in `0.0.7` and let follow-up cards add features when real demand surfaces.

### Explicitly do not borrow

- strawberry-django's broader `extensions/` / `middlewares/` / `test/` modules that surround its `management/`. We ship just the management command in `0.0.7`; the surrounding modules land card-by-card under their own specs (see [Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- A `graphql_schema` command name (graphene-django's name). The whole point of the migration is that consumers can run their `manage.py export_schema` muscle memory from strawberry-django without re-learning a different command. Aliasing is out per [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias).

## User-facing API

The shipped consumer surface in `0.0.7` adds one new `manage.py` command (`export_schema`) discoverable through Django's `INSTALLED_APPS`-driven command-discovery (the consumer already lists `"django_strawberry_framework"` in `INSTALLED_APPS`; once Slice 1 lands, `manage.py export_schema` becomes available). The `Command` class is NOT added to `__all__`; consumers reach the command through `manage.py`, not through the package's import surface.

### Default usage — write SDL to stdout

```bash path=null start=null
# Consumer's project root
uv run python manage.py export_schema config.schema
```

Resolves the dotted path `config.schema` to the consumer's top-level `strawberry.Schema` instance, calls `strawberry.printer.print_schema(schema)`, and writes the SDL to stdout. Pipe to a file with shell redirection if `--path` is undesirable:

```bash path=null start=null
uv run python manage.py export_schema config.schema > schema.graphql
```

### Write SDL to a file

```bash path=null start=null
uv run python manage.py export_schema config.schema --path schema.graphql
```

Writes UTF-8 SDL to `schema.graphql`. The file is overwritten if it exists.

### Explicit `:symbol_name` suffix

When the schema symbol is not named `schema`:

```bash path=null start=null
uv run python manage.py export_schema config.module:my_schema
```

Strawberry's `import_module_symbol` accepts the `module.path:symbol_name` shape directly. The `default_symbol_name="schema"` argument we pass only applies when no `:symbol_name` suffix is present.

### Error shapes

```bash path=null start=null
$ uv run python manage.py export_schema does.not.exist
CommandError: No module named 'does'

$ uv run python manage.py export_schema config.urls
CommandError: The `schema` must be an instance of strawberry.Schema

$ uv run python manage.py export_schema
usage: manage.py export_schema [-h] [--path [PATH]] ... schema
manage.py export_schema: error: the following arguments are required: schema
```

The third shape is Django's argparse layer doing its job; the test plan asserts the shape so a future refactor cannot silently drop the requirement.

## Architectural decisions

### Decision 1 — Module location & no public export

**Module location.** The command lives at **`django_strawberry_framework/management/commands/export_schema.py`** (new module under a new subpackage), matching the [`docs/TREE.md`](TREE.md) target layout at lines 309-313 and Django's `management/commands/` discovery convention.

Two `__init__.py` markers are required:

- `django_strawberry_framework/management/__init__.py` — empty marker (one-line module docstring required by `D100`).
- `django_strawberry_framework/management/commands/__init__.py` — empty marker (one-line module docstring required by `D100`).

Justification:

- Django's `manage.py` walks `<app>.management.commands.*` for every `<app>` in `INSTALLED_APPS`. Both `management` and `management.commands` must be importable Python packages for the walk to find `export_schema.py`. The `__init__.py` files are not optional.
- The [`docs/TREE.md`](TREE.md) target layout already reserves `management/` with the `[alpha]` tag at line 309 — Slice 3 removes the tag once the file lands.
- The [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) [`Django AppConfig`](GLOSSARY.md#django-appconfig) makes `manage.py` resolve the package's commands through the explicit `DjangoStrawberryFrameworkConfig`; the implicit-AppConfig fallback would also work (Django's command-discovery does not depend on an explicit AppConfig), but the explicit class is what `INSTALLED_APPS` resolves to as of `0.0.7`.

**Public-export surface.** `django_strawberry_framework/__init__.py` is NOT modified.

Justification:

- Django's command-discovery resolves the command through its dotted module path; consumers never write `from django_strawberry_framework.management.commands.export_schema import Command`.
- `tests/base/test_init.py` pins `__all__`; adding a name to `__all__` for something consumers never `import` would be noise-only API widening.
- Symmetric with [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) [Decision 3](SPECS/spec-017-apps-0_0_7.md#decision-3--no-public-export) for [`Django AppConfig`](GLOSSARY.md#django-appconfig), and with strawberry-django which does not re-export its `Command` either.

Alternatives considered (and rejected):

- **`django_strawberry_framework/commands.py` flat module.** Rejected: Django's command-discovery walks `management/commands/`, not arbitrary module names; the convention is load-bearing. A flat `commands.py` would never be discovered.
- **`django_strawberry_framework/cli.py` Click-based standalone CLI.** Rejected: the consumer's `manage.py` is the canonical entry point for Django commands; a parallel CLI doubles the surface area without benefit and forces consumers to learn a second convention.
- **Re-export `Command` from `__init__.py` for testing convenience.** Rejected: tests should resolve the class through `call_command` per [Decision 8](#decision-8--tests-go-through-call_command-not-direct-handle), not via direct import; the re-export would invite the wrong testing pattern.

### Decision 2 — `Command` class shape

The class declares exactly:

- `help = "Export the GraphQL schema"` — Title Case `GraphQL` (the upstream uses lowercase `"Export the graphql schema"`; we Title-Case for repo prose consistency; the test plan pins the exact string).
- `add_arguments(self, parser)` adding (a) positional `"schema"` with `nargs=1, type=str, help="The schema location"`, (b) optional `"--path"` with `nargs="?", type=str, help="Optional path to export"`.
- `handle(self, *args, **options)` per [Decision 3](#decision-3--symbol-resolution-via-strawberryutilsimporterimport_module_symbol), [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema), and [Decision 5](#decision-5--commanderror-for-three-failure-modes).

Documentation (gate-forced, not behavioral):

- Module docstring at the top of `export_schema.py` — required by ruff's `D100`. Suggested: `"""manage.py export_schema — print or write the GraphQL SDL for a Strawberry schema symbol."""`.
- Class docstring directly under the class statement — required by ruff's `D101`. Suggested: `"""Export the GraphQL SDL for a strawberry.Schema symbol."""`.

Both docstrings diverge from the upstream's `export_schema.py` (which has neither) because this repo's pydocstyle gate is stricter than the upstream's; both divergences are forced by the gate, not chosen for stylistic reasons. Same posture as [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) [Borrowing posture](SPECS/spec-017-apps-0_0_7.md#borrowing-posture) "two forced divergences."

Deliberately NOT declared:

- A `requires_system_checks` override. The default `("__all__",)` means Django runs system checks before `handle()`; this is fine — the command does not need to bypass checks. Future cards that need a checks-free mode (e.g., schema export before migrations) can override then.
- A `requires_migrations_checks` override. The command does not touch the database; the default `False` is correct.
- A `stealth_options` override. The command takes only documented options; there is nothing stealth to hide.

Justification for shape:

- Two attributes (`help`, two `add_arguments` calls) and one method (`handle`) is the entire surface strawberry-django ships behaviorally; we match the behavioral shape exactly. The two docstrings are additive, forced by this repo's stricter pydocstyle gate.
- Every attribute the spec adds is one the test plan has to pin; every attribute that doesn't ship is one the spec doesn't have to defend.

Alternatives considered (and rejected):

- **`help = "Export the graphql schema"` (lowercase, matching upstream verbatim).** Rejected: the test plan pins the string; the repo's prose consistently Title-Cases `GraphQL`; this divergence is one line and is durable across the test pin.
- **Use named `--schema` instead of positional `schema`.** Rejected: the strawberry-django shape is positional; consumers migrating from strawberry-django expect positional; argparse error messages for missing positional arguments are clearer than for missing named arguments.
- **Default `nargs=None` for `schema` (single value, not a one-element list).** Rejected: the upstream uses `nargs=1` and reads `options["schema"][0]`; we keep that shape so the test can verify the upstream-shape resolution. The argparse semantics of `nargs=1` (always a list) versus `nargs=None` (always the value) are subtly different in test setup; matching the upstream avoids re-litigating the choice.

### Decision 3 — Symbol resolution via `strawberry.utils.importer.import_module_symbol`

`handle()` resolves the consumer's dotted path through Strawberry's documented importer:

```python path=null start=null
schema_symbol = import_module_symbol(
    options["schema"][0],
    default_symbol_name="schema",
)
```

Behavior:

- `"config.schema"` → resolves the `config.schema` module attribute named `schema` (the `default_symbol_name` fallback).
- `"config.module:my_schema"` → resolves the `config.module` module attribute named `my_schema`.
- `"does.not.exist"` → raises `ImportError` → caught and re-raised as `CommandError` per [Decision 5](#decision-5--commanderror-for-three-failure-modes).
- `"config.module:does_not_exist"` → raises `AttributeError` → caught and re-raised as `CommandError`.

Justification:

- Reusing the upstream importer keeps the command body trivial. Strawberry already documents the `module.path:symbol_name` shape; consumers migrating from strawberry-django know it.
- The `default_symbol_name="schema"` fallback matches the conventional Python project layout where `config/schema.py` (or `app/schema.py`) exposes a top-level `schema = strawberry.Schema(...)`. Consumers with non-default naming use the `:symbol_name` suffix.
- No re-invention of dotted-path parsing. A hand-rolled parser would need to handle the same edge cases (empty path, trailing dots, missing module, missing attribute) and would add ~30 lines for no benefit.

**No auto-call to [`finalize_django_types()`](GLOSSARY.md#finalize_django_types).** The consumer's `config/schema.py` (or equivalent) calls [`finalize_django_types()`](GLOSSARY.md#finalize_django_types) before constructing the schema; resolving the dotted path triggers the consumer's module-level imports, which run the finalize call as a side effect. Adding a `finalize_django_types()` call in `handle()` would either be silently redundant (the consumer's module already ran it) or — if the consumer's schema module deferred finalization to a function — would call it too early (before the consumer's imports are complete). The same anti-pattern is pinned in [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) [Decision 4](SPECS/spec-017-apps-0_0_7.md#decision-4--no-readyhook-in-0_0_7) for [`Django AppConfig`](GLOSSARY.md#django-appconfig)`.ready()`; the same logic applies here.

Alternatives considered (and rejected):

- **Hand-roll dotted-path resolution via `importlib.import_module` + `getattr`.** Rejected: strawberry-django's importer handles `module.path:symbol_name` already; rewriting it would force the test plan to pin the same edge cases the upstream's tests already cover.
- **Use `django.utils.module_loading.import_string`.** Rejected: Django's helper does not handle the `module.path:symbol_name` shape; using it would diverge from strawberry-django's contract and force consumers to learn a different syntax.
- **Call `finalize_django_types()` defensively in `handle()` before resolving.** Rejected: `finalize_django_types()` requires the consumer's `DjangoType` modules to be imported first; calling it before resolving the schema symbol would either be a no-op (modules already imported as a side effect of the consumer's `apps/<app>/schema.py` chain) or would finalize an empty registry (if the consumer's schema module is the first time anything imports the `DjangoType` modules). Neither shape is useful.

### Decision 4 — SDL output via `strawberry.printer.print_schema`

`handle()` writes SDL via:

```python path=null start=null
schema_output = print_schema(schema_symbol)
path = options.get("path")
if path:
    pathlib.Path(path).write_text(schema_output, encoding="utf-8")
else:
    self.stdout.write(schema_output)
```

Justification:

- `print_schema` is Strawberry's canonical SDL serializer for a `strawberry.Schema` instance; it handles directives, custom scalars, federation extensions, descriptions, deprecation reasons. Re-implementing SDL serialization would re-walk the Strawberry type graph for no benefit.
- SDL is the Strawberry-native serialization. Consumers needing JSON introspection pipe SDL through downstream tools (`graphql-codegen`, `graphql-cli`, `graphql-inspector`); this is consistent with the broader Strawberry ecosystem's posture (`strawberry export-schema` is SDL-only).
- UTF-8 encoding for the file-write matches the upstream and avoids platform-specific locale surprises.
- `self.stdout.write` (not `print(...)`) is Django's documented way to emit command output so test capture via `call_command(..., stdout=StringIO())` works.

Alternatives considered (and rejected):

- **JSON introspection mode behind a `--json` flag.** Rejected: graphene-django's JSON-by-default surface is the historical artifact of older codegen tools that required JSON introspection. Modern tools (`graphql-codegen`, `graphql-inspector`, IntelliJ's GraphQL plugin) prefer SDL or accept both. Adding JSON would double the test surface for no current consumer benefit.
- **Pretty-print SDL with an `--indent` option.** Rejected: SDL is whitespace-agnostic; consumer-side formatting is a downstream concern (`prettier --parser graphql`).
- **Emit SDL via `print(schema_output)` instead of `self.stdout.write`.** Rejected: Django's `call_command(..., stdout=captured)` redirects `self.stdout` but does NOT redirect `sys.stdout`; the test plan needs `self.stdout.write` to capture cleanly without monkey-patching.

### Decision 5 — `CommandError` for three failure modes

`handle()` raises Django's `CommandError` (NOT [`ConfigurationError`](GLOSSARY.md#configurationerror); NOT a custom exception) in three shapes:

1. **Unimportable dotted path** — `import_module_symbol` raises `ImportError` (module not found, malformed path) or `AttributeError` (module loads but the attribute does not exist). Both are caught and re-raised as `CommandError(str(e)) from e`. The `from e` chain is preserved so the original exception remains accessible via `__cause__`.
2. **Resolved symbol is not a `strawberry.Schema` instance** — `isinstance(schema_symbol, strawberry.Schema)` check fails. Raises `CommandError("The `schema` must be an instance of strawberry.Schema")` (verbatim from the upstream wording; the test plan pins it).
3. **Missing positional argument** — Django's argparse layer catches this before `handle()` runs and emits a usage banner + error to stderr with exit code 2. The test plan asserts the shape via `pytest.raises(CommandError)` — Django wraps argparse's `SystemExit(2)` into a `CommandError` only when invoked via `call_command(...)`; the test pins the wrapped form.

Justification:

- `CommandError` is Django's documented escape hatch for management-command failures; both reference packages use it. `manage.py` prints the error message and exits with non-zero status, which is what `make`/CI tools need.
- [`ConfigurationError`](GLOSSARY.md#configurationerror) is reserved for `DjangoType` / `Meta` validation issues at class-definition / finalize time; using it for runtime command failures would muddy the exception hierarchy.
- A custom `ExportSchemaError` would force every test to import it; reusing Django's class keeps the test surface small.

Error-message wording — pinned exactly:

- `CommandError(str(e))` for the `ImportError` / `AttributeError` case — defers to Python's import-machinery message (e.g., `"No module named 'does'"` or `"module 'config.urls' has no attribute 'schema'"`). Pinning the prefix would over-constrain the test (Python's exact message text varies by version); the test asserts the `CommandError` class and uses `match=` substring matching against a stable fragment.
- `CommandError("The `schema` must be an instance of strawberry.Schema")` for the non-`Schema` case — verbatim from the upstream wording; the backticks around `schema` are deliberate.

Alternatives considered (and rejected):

- **Catch `Exception` and wrap it in `CommandError`.** Rejected: broad-except masks real bugs (a `KeyError` inside the consumer's `Schema(...)` constructor would surface as a confusing `CommandError`). The narrow `(ImportError, AttributeError)` catch matches the upstream and matches the actual failure modes of `import_module_symbol`.
- **Distinguish "module not found" from "attribute not found" with different error messages.** Rejected: the upstream does not distinguish, and the underlying exception (`__cause__`) carries the distinction for consumers who want to read it. Diverging from the upstream without test-plan benefit is gratuitous.
- **Let `isinstance(..., strawberry.Schema)` fall through to a `TypeError` at `print_schema(...)` time.** Rejected: the explicit isinstance check produces a clear, attributable `CommandError` instead of a deep Strawberry-internal stack trace; the upstream agrees.

### Decision 6 — No `--watch` / `--indent` / `--json` / settings-backed defaults / alias

The command does NOT ship:

- `--watch` mode (file-system watcher + Django autoreload, graphene-django's `--watch` shape). Reasonable post-`1.0.0` differentiator if consumer demand surfaces; deferred.
- `--indent` option (graphene-django's JSON-pretty-printing flag). SDL is whitespace-agnostic; the formatting consumers want belongs in downstream tools (`prettier --parser graphql`, `graphql-cli`). Not on the roadmap.
- `--json` option / JSON-introspection mode (graphene-django's default output). SDL is the Strawberry-native serialization; consumers pipe through `graphql-codegen` / `graphql-inspector` for JSON. See [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema).
- Settings-backed defaults from `DJANGO_STRAWBERRY_FRAMEWORK` (graphene-django's `GRAPHENE.SCHEMA` / `SCHEMA_OUTPUT` / `SCHEMA_INDENT` analogs). [`AGENTS.md`](../AGENTS.md) line 20 explicitly forbids preemptive settings. Consumers wrap the command in a shell alias or `Makefile` entry; a follow-up card adds settings keys alongside the consuming behavior if demand surfaces.
- A `dump_schema` / `print_schema` alias for the same command. One command name, one canonical invocation; aliasing fragments documentation and consumer mental models.

Justification:

- Each non-shipped feature is a real consumer pain point in some workflow, but none has surfaced as repeated friction in the migration story this card serves. `0.0.7`'s job is parity with strawberry-django; graphene-django's surface accretions belong in follow-up cards driven by real consumer asks.
- The follow-up path is clean: each non-shipped feature lands as its own card with its own design surface (what does `--watch` do under `runserver`? what JSON shape does `--json` emit?), tested independently. Folding three of them in here would bloat the slice and complicate review.
- Mirrors [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) [Decision 4](SPECS/spec-017-apps-0_0_7.md#decision-4--no-readyhook-in-0_0_7) and [Decision 5](SPECS/spec-017-apps-0_0_7.md#decision-5--no-default_auto_field-and-no-models)'s posture: do the minimum the parity story needs; defend each non-shipped feature with a stated reason; let follow-up cards re-litigate when consumer demand changes.

Alternatives considered (and rejected):

- **Ship `--watch` because graphene-django ships it.** Rejected: `--watch` is meaningful for the JSON-introspection workflow (regenerate `schema.json` whenever a Python file changes); for SDL output, consumers already have `entr` / `watchexec` / `make` and don't need a Django-specific watcher. The watcher's value is also tied to whether the consumer is iterating on the schema in `runserver`; pinning the right ergonomics needs a separate design pass.
- **Ship a settings-backed default for the positional `schema` argument** (`DJANGO_STRAWBERRY_FRAMEWORK = {"SCHEMA_PATH": "config.schema"}`). Rejected per [`AGENTS.md`](../AGENTS.md) line 20; consumers wrap the command in a `Makefile`:

  ```makefile path=null start=null
  export-schema:
  	uv run python manage.py export_schema config.schema --path schema.graphql
  ```

  which is one line and visible at the repo root.
- **Ship `--json` because it's "free" — just `json.dumps(strawberry.tools.create_type(...)...)`.** Rejected: the JSON-introspection shape graphene-django emits is the GraphQL introspection query result, not a `print_schema` round-trip; emitting it correctly requires running the introspection query, which means executing the schema (and any `DjangoOptimizerExtension` extensions, request-context dependencies, etc.). The full design is non-trivial.

### Decision 7 — Test placement: `tests/management/__init__.py` ships

`tests/management/` carries an `__init__.py` shell matching the existing `tests/optimizer/__init__.py` and `tests/types/__init__.py` convention per [`docs/TREE.md`](TREE.md) line 457.

Justification:

- [`AGENTS.md`](../AGENTS.md) line 6's "do not add `__init__.py`" rule applies only to the two `examples/fakeshop/` test trees (`examples/fakeshop/tests/` and `examples/fakeshop/test_query/`) — explicitly: "(collides on the tests package name once `examples/fakeshop` is on pythonpath)." Package-test subdirectories under `tests/` are NOT in scope of that rule.
- [`docs/TREE.md`](TREE.md) line 457: "Subdirectories carry an `__init__.py` shell to match the existing `tests/__init__.py` + `tests/base/__init__.py` convention so pytest collects them as `tests.<subpkg>.<module>`."
- The existing `tests/` directory listing confirms `tests/optimizer/__init__.py` and `tests/types/__init__.py` exist on disk; following the established pattern keeps the test collection model uniform.

Alternatives considered (and rejected):

- **Flat `tests/test_export_schema.py` (no subdirectory).** Rejected: the source lives under a subpackage (`management/commands/`), and the [`docs/TREE.md`](TREE.md) mirror rule pairs source subpackages with test subdirectories. A flat test file would diverge from the established mirror pattern and would force a future second test file (e.g., for a `dump_schema` follow-up) to either re-flat or migrate.
- **Omit `tests/management/__init__.py`** (treating it like the `examples/fakeshop/` rule). Rejected per the AGENTS.md scoping above; the rule does not apply to package-test subdirectories.

### Decision 8 — Tests go through `call_command`, NOT direct `handle()`

Every test in `tests/management/test_export_schema.py` invokes the command through `django.core.management.call_command(...)`, NOT by instantiating `Command()` and calling `.handle(...)` directly.

Justification:

- The card body pins this explicitly: "Tests use `django.core.management.call_command`, NOT direct `handle()` calls — pinned here because direct `handle()` calls bypass Django's argument parsing and let dev errors slip past the test contract."
- `call_command` runs the full argparse layer, so the test catches `nargs=1` / `nargs="?"` / type-coercion mismatches a direct `handle()` call would silently accept.
- `call_command` captures `self.stdout` / `self.stderr` cleanly via the `stdout=`, `stderr=` kwargs; direct `handle()` calls require monkey-patching to capture output.
- `call_command` wraps `SystemExit` from argparse into `CommandError` for the missing-positional-argument case; the test plan asserts the `CommandError` shape, which only the wrapper produces.

The constraint also propagates to the example-project live test in `examples/fakeshop/tests/test_commands.py`: per [`docs/TREE.md`](TREE.md) line 461 the file uses `call_command` exclusively, which matches.

Alternatives considered (and rejected):

- **Allow direct `Command().handle(...)` calls for "unit" tests and `call_command` for "integration" tests.** Rejected: the distinction is illusory for a Django command — `handle()` without argparse is not the production code path, and the unit/integration split here would test code that nobody runs in production.
- **Use `pytest.mark.django_db` instead of `call_command`.** Rejected: the mark only handles database setup; it does not invoke commands. Both can coexist (the live fakeshop test uses both — `django_db` for fixtures, `call_command` for the command invocation).

### Decision 9 — Joint `0.0.7` cut

`0.0.7` ships under the joint-cut policy from [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) [Decision 10](SPECS/spec-016-list_field-0_0_7.md#decision-10--joint-007-cut): the three remaining WIP cards in the bundle — `WIP-ALPHA-018-0.0.7` (this card), `WIP-ALPHA-019-0.0.7` (multi-database cooperation contract), and `WIP-ALPHA-045-0.0.7` (warning-free scalar registration) — accumulate `### Added` entries under the same `[0.0.7]` heading in [`CHANGELOG.md`](../CHANGELOG.md). The version bump in `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__` line, and `tests/base/test_init.py`'s pinned version assertion is owned by whichever card ships last in the bundle, NOT this card.

Justification:

- Restates [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) [Decision 10](SPECS/spec-016-list_field-0_0_7.md#decision-10--joint-007-cut) verbatim so this card's reader does not have to chase the cross-spec reference.
- Per [`KANBAN.md`](../KANBAN.md) line 50: "The last `0.0.7` card to ship owns the version bump from `0.0.6` per Decision 10 of `docs/SPECS/spec-016-list_field-0_0_7.md`." The cross-card policy is already pinned in the [`KANBAN.md`](../KANBAN.md); this Decision pulls it into the spec so Slice 3's checklist can reference it.
- The [`CHANGELOG.md`](../CHANGELOG.md) `[0.0.7]` `### Added` section already carries `DONE-016-0.0.7`'s [`DjangoListField`](GLOSSARY.md#djangolistfield) entry and `DONE-017-0.0.7`'s [`Django AppConfig`](GLOSSARY.md#django-appconfig) entry; this card appends a third bullet for [`Schema export management command`](GLOSSARY.md#schema-export-management-command). Verified at [`CHANGELOG.md`](../CHANGELOG.md) lines 21-24 — the `[0.0.7]` heading and the existing two `### Added` bullets are present today.

The Slice 3 doc-updates list explicitly excludes the version bump.

Alternatives considered (and rejected):

- **This card bumps `0.0.7` because it ships fourth (the schema-export card is conventionally last to merge).** Rejected: ship order is determined by which card a maintainer picks up next, not by card NNN; pinning the bump to a specific card creates a sequencing constraint that has no engineering justification.
- **Add a separate `TODO-ALPHA-XXX-0.0.7 — 0.0.7 release cut` card to [`KANBAN.md`](../KANBAN.md) that owns the bump.** Rejected: out of scope for this spec (the spec's boundary forbids editing [`KANBAN.md`](../KANBAN.md) outside the column move in Slice 3); the "last card to ship" policy is workable as-is.

### Decision 10 — Live coverage belongs in `examples/fakeshop/tests/`, NOT `test_query/`

The live fakeshop coverage extends `examples/fakeshop/tests/test_commands.py` with one new test; it does NOT add a file under `examples/fakeshop/test_query/`.

Justification:

- [`examples/fakeshop/test_query/README.md`](../examples/fakeshop/test_query/README.md) is explicit: "Live GraphQL-API tests … exercise the full Django + Strawberry HTTP stack end-to-end by sending requests to `/graphql/` (typically via `django.test.Client.post(...)`)." The schema-export command is not an HTTP-shaped surface; it does not hit `/graphql/`; it does not exercise the request pipeline.
- [`docs/TREE.md`](TREE.md) line 461: "`examples/fakeshop/tests/` — Example-project tests, no HTTP `/graphql/`. … management commands via `django.core.management.call_command`."
- [`examples/fakeshop/tests/test_commands.py`](../examples/fakeshop/tests/test_commands.py) already covers the example project's other commands (`seed_data`, `delete_data`, `seed_shards`, `create_users`, `delete_users`) via `call_command`. Adding one test for `export_schema` extends the file in place.
- The card body acknowledges this: "Live coverage: a fakeshop test under `examples/fakeshop/test_query/` (or `examples/fakeshop/tests/` if not HTTP-shaped)." This Decision settles the "or" in favor of `examples/fakeshop/tests/` because the command is decidedly not HTTP-shaped.

[`AGENTS.md`](../AGENTS.md) line 9's coverage-priority rule ("Any coverage line achievable via a real GraphQL query against fakeshop in `examples/fakeshop/test_query/` MUST be earned that way; fall back to `examples/fakeshop/tests/` … or `tests/` … only when the line is genuinely unreachable from a real-world query") is satisfied: the command's lines are not reachable from a live `/graphql/` query (the command's job is to print SDL from the consumer's `manage.py`, not to serve a request), so the fall-back to `examples/fakeshop/tests/` is the correct tier.

Alternatives considered (and rejected):

- **Place the live test under `examples/fakeshop/test_query/test_export_schema.py`.** Rejected: violates the [`examples/fakeshop/test_query/README.md`](../examples/fakeshop/test_query/README.md) scope; the file would be the only non-HTTP test in the tree.
- **Skip the example-project live test and rely on `tests/management/test_export_schema.py` for everything.** Rejected: the package-internal test uses a fixture schema, not the consumer's real fakeshop schema; the example-project test is what proves the command works against a real consumer-shape `strawberry.Schema(query=..., extensions=[DjangoOptimizerExtension()])` constructed through `finalize_django_types()`.

## Implementation plan

The slice ships as **three slices** aligned with the [Slice checklist](#slice-checklist). Each slice maps to one commit; squashing all three into a single PR is acceptable given the small surface.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — Module + `Command` subclass | `django_strawberry_framework/management/__init__.py` (new), `django_strawberry_framework/management/commands/__init__.py` (new), `django_strawberry_framework/management/commands/export_schema.py` (new) | 0 (tests land in Slice 2) | `+50 / -0` |
| 2 — Tests | `tests/management/__init__.py` (new), `tests/management/test_export_schema.py` (new), `examples/fakeshop/tests/test_commands.py` (extend) | 6 (5 package-internal — happy stdout, happy `--path`, three `CommandError` shapes, default-symbol-name fallback; +1 fakeshop live) | `+120 / -0` |
| 3 — Promotion + docs | `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md` | 0 | `+35 / -10` |

Total expected delta: ~205 lines across the three slices.

The three slices must be authored in order. Slice 2 depends on Slice 1 (the class must exist before tests can `call_command` it); Slice 3 depends on Slice 2 (the [`CHANGELOG.md`](../CHANGELOG.md) `### Added` line and [`KANBAN.md`](../KANBAN.md) Done body must describe a shipped, tested module, not a half-landed one).

## Edge cases and constraints

- **Django command-discovery is `INSTALLED_APPS`-driven.** Once `django_strawberry_framework/management/commands/export_schema.py` ships, `manage.py` discovers the command as long as `"django_strawberry_framework"` is in `INSTALLED_APPS` (the example project already has this entry at `examples/fakeshop/config/settings.py:48`). No `AppConfig.ready()` hook is involved — Django walks the `management/commands/` directory by convention. The [`Django AppConfig`](GLOSSARY.md#django-appconfig) shipped under [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) is the entry point Django resolves through for the walk, but it has no `ready()` body and does not need one.
- **`finalize_django_types()` runs as a side effect of resolving the schema symbol.** The consumer's `config/schema.py` calls [`finalize_django_types()`](GLOSSARY.md#finalize_django_types) at module-level before constructing `strawberry.Schema(...)`. When `import_module_symbol("config.schema")` loads the module, the finalize call runs as part of the module's top-level execution. The command does NOT need to call [`finalize_django_types()`](GLOSSARY.md#finalize_django_types) itself; the consumer's schema module owns the synchronization point.
- **Idempotent reads.** The command reads the consumer's schema; it does not write to the database; it does not mutate process state outside Strawberry's own caches. Running `manage.py export_schema config.schema` twice produces identical output; running it during `pytest` does not require a fixture teardown.
- **Schema symbol is resolved at command-invocation time.** Each `call_command("export_schema", "config.schema")` re-imports `config.schema` (or hits the import cache if already imported). The test plan can rely on the consumer's module-level wiring having executed; the cached-imports case is correct because the schema is constructed once and stays constant for the process lifetime.
- **`strawberry.Schema` `isinstance` check uses the public `strawberry.Schema` class.** Imported as `from strawberry import Schema` per the upstream's shape. Subclasses of `strawberry.Schema` (none currently shipped by this package) pass the check; this is the right behavior — a `MyCustomSchema(strawberry.Schema)` is still a valid export target.
- **UTF-8 file write.** `pathlib.Path(path).write_text(schema_output, encoding="utf-8")` is the only encoding shape; non-UTF-8 environments (rare on modern Linux/macOS, unusual on Windows) get a deterministic file that downstream tools can read. The test plan does not test non-UTF-8 platforms; a future card adds Windows-encoding handling if real demand surfaces.
- **`tmp_path` for file-write tests.** The fakeshop live test uses pytest's `tmp_path` fixture so the file is auto-cleaned between runs. The package-internal test uses the same shape.
- **`call_command` and `stdout`.** Capture via `stdout=StringIO()` is the documented pattern; the test plan uses it. `self.stdout.write(schema_output)` appends a trailing newline by default; the test plan accounts for the newline in the captured-string assertions (`out.getvalue().endswith("\n")` or substring-match against the SDL body).
- **`pyproject.toml [tool.ruff.lint.per-file-ignores]`.** The per-file-ignores at `pyproject.toml` lines ~100-107 do not exempt `django_strawberry_framework/management/commands/export_schema.py`; the file is subject to the full `D` ruleset. The module + class docstrings cover `D100` / `D101`; `add_arguments` and `handle` are method-level (`D102`) and would normally need docstrings too, but `D102` is in the per-file-ignores for `django_strawberry_framework/**` (verified — if `D102` is NOT in the per-file-ignores, the spec adds one-line docstrings to both methods as a Slice 1 sub-task; the Slice 1 checklist already accommodates this as part of the "do not suppress with `# noqa: D…`" rule). The implementer verifies the actual ignore list at Slice 1 time and adjusts the method-docstring shape accordingly.
- **Coverage of the command body.** The class body has `add_arguments` (two `parser.add_argument` calls) and `handle` (six statements). The Slice 2 tests cover every branch: happy stdout, happy `--path`, `ImportError`, `AttributeError`, non-`Schema` isinstance failure, missing positional argument. Plus the fakeshop live test exercises the full flow end-to-end against a real `strawberry.Schema`. Coverage stays at 100% under `pyproject.toml [tool.coverage.report] fail_under = 100`.
- **`pytest-django` setup.** Tests that invoke the command need Django's app registry populated; `pytest-django` handles this via `django.setup()` once per session. The Slice 2 `tests/management/test_export_schema.py` uses a fixture-shaped schema (constructed in the test module, NOT pulled from a `DjangoType` registry) so it does not need `pytest.mark.django_db` for the unit tests. The fakeshop live test in `examples/fakeshop/tests/test_commands.py` follows the existing file's conventions (no `django_db` is needed because the command only reads the schema; no database access).
- **Re-importing a moved schema module.** If the consumer reorganizes their `config/schema.py` between two `call_command` invocations in the same process, Python's import cache may hold the stale module. This is a pytest fixture concern, not a command bug; the test plan does not test for it. (The fakeshop live test uses `tmp_path` for the output file, not for the schema module, so this is irrelevant.)

## Test plan

Tests live across two trees, matching the rules in [`docs/TREE.md`](TREE.md) and [`AGENTS.md`](../AGENTS.md). Test-tree placement is mandatory per [Decision 7](#decision-7--test-placement-testsmanagement__init__py-ships) and [Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query).

### `tests/management/__init__.py` (new)

Empty marker module with a one-line docstring (`"""Package tests for django_strawberry_framework.management.*."""`). Required for pytest to collect tests as `tests.management.<module>` and to satisfy `D100`. No further content.

### `tests/management/test_export_schema.py` (new)

Package tests; system-under-test is `django_strawberry_framework.management.commands.export_schema`. Five tests:

- `test_export_schema_writes_sdl_to_stdout_by_default` — constructs a small `strawberry.Schema` inline (single `@strawberry.type` Query with one field), exposes it on a synthesized module via `sys.modules["test_module.schema"]`, calls `call_command("export_schema", "test_module.schema", stdout=captured)` and asserts the captured string contains a known SDL fragment (e.g., `"type Query"`). Pins the happy stdout path.
- `test_export_schema_writes_sdl_to_path_when_path_set` — same fixture schema, calls `call_command("export_schema", "test_module.schema", "--path", str(tmp_path / "schema.graphql"))`, asserts the file exists, is UTF-8, and contains the known SDL fragment. Pins the happy `--path` path.
- `test_export_schema_raises_command_error_for_unimportable_dotted_path` — calls `call_command("export_schema", "does.not.exist")` and asserts `pytest.raises(CommandError, match="No module named")` (substring match against Python's stable import-error fragment; the exact wording varies by Python version). Pins the `ImportError`-wrapped `CommandError` branch.
- `test_export_schema_raises_command_error_for_non_schema_symbol` — exposes a non-`Schema` object (a plain `int`) on a synthesized module and calls `call_command("export_schema", "test_module.not_a_schema")`; asserts `pytest.raises(CommandError, match=r"must be an instance of strawberry\.Schema")`. Pins the isinstance-failure branch and the exact wording.
- `test_export_schema_falls_back_to_default_symbol_name_schema` — exposes the fixture schema as the module-level `schema` attribute and calls `call_command("export_schema", "test_module")` (no `:symbol_name` suffix). Asserts the SDL is produced. Pins Strawberry's `default_symbol_name="schema"` fallback so a future refactor that drops the kwarg fails this test.

Negative-shape test (one):

- `test_export_schema_command_does_not_define_forbidden_attributes` — asserts that `Command.__dict__` does NOT contain keys that this spec forbids: nothing currently (every key we ship — `help`, `add_arguments`, `handle` — is legitimate). This test is INTENTIONALLY OMITTED for `0.0.7`: the AppConfig spec's consolidated negative-shape test exists because there are four documented decisions about what NOT to add; here, every Decision is about what TO add or HOW the existing surface behaves. No forbidden-key list exists for the `Command` class. If a future card adds a "do not ship `--watch`" enforcement (e.g., a check that no `--watch` argparse arg is registered), it adds the negative test then. The Slice 2 implementation does not author a placeholder negative test.

No live `/graphql/` HTTP test is required (the command is not HTTP-shaped — see [Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query)).

### `examples/fakeshop/tests/test_commands.py` (extend)

Extend the existing file with one test:

- `test_export_schema_command_against_fakeshop_schema` — calls `call_command("export_schema", "config.schema", "--path", str(tmp_path / "schema.graphql"))` and asserts the produced SDL contains `"type Branch"` (a known type from the `library` app, present in the live schema). Pins end-to-end behavior: the command resolves the consumer's real `strawberry.Schema(query=..., extensions=[DjangoOptimizerExtension()])` constructed through [`finalize_django_types()`](GLOSSARY.md#finalize_django_types), prints SDL, and writes it to a file. Without this test, the command's lines are covered by the unit tests but the integration with the example project is not proven.

The test follows the existing file's conventions (no `pytest.mark.django_db` needed — the command only reads the schema; no database access).

## Doc updates

- [`docs/GLOSSARY.md`](GLOSSARY.md)
  - Flip [`Schema export management command`](GLOSSARY.md#schema-export-management-command) from `planned for 0.0.7` to `shipped (0.0.7)` (current state at line 104 of the Index table; the entry body lives at line 910).
  - Update the entry body to describe the shipped contract: `django_strawberry_framework/management/commands/export_schema.py` ships `Command(BaseCommand)` with positional `schema` (dotted path, default symbol name `"schema"`) and optional `--path`; SDL output via `strawberry.printer.print_schema`; `CommandError` for unimportable dotted path, non-`strawberry.Schema` resolved symbol, and missing positional argument; no `--watch` / `--indent` / JSON mode / settings-backed defaults in `0.0.7`.
  - Update the Index table's status column for the row at line 104.

- [`docs/README.md`](README.md)
  - **Surgically remove the entire `- schema export management command` bullet** at line 113 (the `Coming in 0.1.0` section). DONE-017-0.0.7 removed only `, Django `AppConfig`` from that line; this card removes the remainder.
  - The shipped-list heading at line 89 already reads `**Shipped today** (`0.0.7`):` (DONE-017 bumped it); no further heading change here.
  - Add a bullet to the `Shipped today (0.0.7)` section reading: "`manage.py export_schema` — Django management command that prints or writes the GraphQL SDL for a `strawberry.Schema` symbol (positional dotted path, optional `--path`); migration-parity with `strawberry-django`'s command of the same name. See [`GLOSSARY.md#schema-export-management-command`](GLOSSARY.md#schema-export-management-command)."

- [`docs/TREE.md`](TREE.md)
  - Add the `management/` subtree to the **current on-disk layout** section under the `django_strawberry_framework/` tree (lines 192-224 of the current file). Position: between `list_field.py` and `optimizer/` (alphabetical). Spell out `commands/__init__.py` and `commands/export_schema.py` children.
  - Remove the `[alpha]` tag from the existing `management/ # [alpha] Django management commands` block in the **target package layout** section at lines 309-313 (the tag means "lands before `0.1.0`", and the bullet has now landed).
  - Add `tests/management/` (with `__init__.py` and `test_export_schema.py` children) to the **current test-tree** section (lines 329-360 of the current file). Position: **before `test_apps.py`** (alphabetical — `management/` sorts before `test_apps.py`).

- [`KANBAN.md`](../KANBAN.md)
  - Move `WIP-ALPHA-018-0.0.7` to the Done column with the next available `DONE-NNN-0.0.7` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). The past-tense Done body summarizes the shipped scope: "Shipped `django_strawberry_framework/management/commands/export_schema.py` containing `Command(BaseCommand)` with positional `schema` (dotted path, default symbol name `\"schema\"`) and optional `--path`; SDL output via `strawberry.printer.print_schema`; `CommandError` for unimportable dotted path, non-`strawberry.Schema` resolved symbol, and missing positional argument. Package-internal tests at `tests/management/test_export_schema.py`; live fakeshop coverage in `examples/fakeshop/tests/test_commands.py`."
  - Update the `### In progress` summary paragraph to remove `WIP-ALPHA-018-0.0.7` from the remaining-cards list once this card moves to Done.

- [`CHANGELOG.md`](../CHANGELOG.md)
  - **Append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading — verified at [`CHANGELOG.md`](../CHANGELOG.md) lines 21-24, the `[0.0.7]` heading already carries DONE-016's [`DjangoListField`](GLOSSARY.md#djangolistfield) entry and DONE-017's [`Django AppConfig`](GLOSSARY.md#django-appconfig) entry; every `0.0.7` card under the joint cut appends to the same shared section per [Decision 9](#decision-9--joint-0_0_7-cut)): "`Schema export management command` — `django_strawberry_framework/management/commands/export_schema.py` ships `Command(BaseCommand)`; `manage.py export_schema config.schema [--path schema.graphql]` writes SDL via `strawberry.printer.print_schema`. Symbol resolution via `strawberry.utils.importer.import_module_symbol(default_symbol_name=\"schema\")`. `CommandError` for unimportable dotted path, non-`strawberry.Schema` resolved symbol, and missing positional argument. No `--watch` / `--indent` / JSON mode / settings-backed defaults in `0.0.7` (each deferred to a follow-up card driven by consumer demand)."
  - The version bump entry is owned by **the last `0.0.7` card to ship** per [Decision 9](#decision-9--joint-0_0_7-cut), NOT this slice.
  - [`AGENTS.md`](../AGENTS.md) line 21 ("Do not update CHANGELOG.md unless explicitly instructed") — this Slice 3 bullet is the explicit instruction.

- No edits to [`README.md`](../README.md). Justification: the README's status section names consumer-facing primitives ([`DjangoType`](GLOSSARY.md#djangotype), the optimizer, [`DjangoListField`](GLOSSARY.md#djangolistfield)); the management command is plumbing reachable via `manage.py`, not via a consumer import. If a future maintainer disagrees, the change is one line and can be added later without revising this spec. Same posture as [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) Slice 3.

- No edits to [`GOAL.md`](../GOAL.md). Justification: `GOAL.md`'s `astronomy` showcase walks through model definitions, schema, filters, orders, aggregates, fieldsets — none of which exercises `manage.py`. The command is dev/CI plumbing; it does not appear in any consumer-code example in `GOAL.md`.

- No edits to [`TODAY.md`](../TODAY.md). Justification: `TODAY.md` is a query-shape-and-capability snapshot ("what GraphQL queries work in fakeshop today?"). The command is not a query-shape change; the fakeshop schema is unchanged by this card.

## Risks and open questions

Each item names a preferred answer for `0.0.7` and a fallback if implementation reveals the preferred answer is wrong.

- **Strawberry's `import_module_symbol` signature stability.** Preferred answer: the symbol's signature `(name: str, *, default_symbol_name: str | None = None) -> Any` has been stable since strawberry-graphql 0.x (the upstream's `strawberry_django` has used it unchanged for years). Fallback: if a future `strawberry-graphql` minor release renames or removes the symbol, this card's Slice 1 module pins `from strawberry.utils.importer import import_module_symbol` at the top, so the test suite would catch the breakage at import time and the fix is to update the import path. The `pyproject.toml` dependency floor (`strawberry-graphql>=0.262.0`, line 30) keeps the package on a recent-enough version that the symbol exists.
- **`strawberry.printer.print_schema` output stability.** Preferred answer: Strawberry's `print_schema` output has been stable for years; consumers using the upstream's `export_schema` rely on byte-for-byte stability for SDL-diffing in CI. Fallback: if a future Strawberry release changes the output (whitespace, directive ordering), consumers' CI diffs would break — but that's a strawberry-graphql concern, not ours; the test plan asserts content (substring `"type Branch"`) not byte-for-byte equality.
- **`call_command` and `CommandError` wrapping for missing positional argument.** Preferred answer: `call_command` wraps argparse's `SystemExit(2)` into `CommandError`, and `pytest.raises(CommandError)` catches it. Fallback: if Django's wrapping changes (unlikely; the behavior has been stable since the `call_command` helper was introduced), the test catches the new exception type and re-asserts; no production code changes.
- **Schema module side effects at import time.** Preferred answer: resolving the consumer's dotted path runs the consumer's `config/schema.py` module body, which calls [`finalize_django_types()`](GLOSSARY.md#finalize_django_types) and constructs the `strawberry.Schema(...)`. If the consumer's schema module depends on Django being fully set up (database connections, signal handlers), `pytest-django`'s session-scoped setup handles it. Fallback: if a consumer constructs their schema with side effects that require runtime context (e.g., reading a `request.user`), the command would either fail with a clear `CommandError` (caught by the `(ImportError, AttributeError)` branch via deeply-nested `AttributeError` from `request`) or — more likely — the consumer's `Schema(...)` constructor would not actually depend on per-request context. The risk is theoretical; if it materializes, the fix is to teach `import_module_symbol` to swallow the deeper exception, which is the upstream's job, not ours.
- **No `management/__init__.py.py` typo regression.** Preferred answer: the file names `__init__.py` (Python init marker), not `__init__.py.py` or similar. The test plan's `tests/management/__init__.py` is collected by pytest as the test package; if either init were misnamed, pytest collection would fail before the test body runs. Fallback: ruff's `D` ruleset would flag the missing module docstring on the misnamed file, and `from django_strawberry_framework.management.commands import export_schema` would raise `ImportError`, which Slice 2's first test catches.
- **`docs/TREE.md` `[alpha]` tag drift.** Preferred answer: Slice 3 removes the `[alpha]` tag from the existing `management/` block at [`docs/TREE.md`](TREE.md) line 309 in the same pass that adds the current-on-disk block. Fallback: if a future card adds a second module to `management/` (e.g., a hypothetical `dump_schema` command), it adds the new entry under the existing `management/` block in the current-on-disk section; no second tag-removal pass is needed.
- **Future-card surface accretions (`--watch` / `--indent` / JSON / settings).** Preferred answer: none of the four are scheduled. Fallback: if real consumer demand materializes for any of them (e.g., a `0.0.x` card adds `--watch` driven by an actual user request), that card's spec adds the option, the argparse argument, the test, and the doc update in one slice. The current minimal surface does not preclude future accretion — it leaves the option in the consumer's argparse hands without consuming the namespace.

## Out of scope (explicitly tracked elsewhere)

- JSON introspection output (graphene-django's default mode). See [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias); not on the roadmap.
- `--watch` mode (file-system watcher + Django autoreload). See [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias); reasonable post-`1.0.0` differentiator if consumer demand surfaces.
- Settings-backed default schema dotted path (`DJANGO_STRAWBERRY_FRAMEWORK.SCHEMA_PATH` analog). See [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias); [`AGENTS.md`](../AGENTS.md) line 20 explicitly forbids preemptive settings.
- `--indent` / SDL-formatting option. See [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias); SDL is whitespace-agnostic.
- `dump_schema` / `print_schema` aliases. See [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias).
- [Multi-database cooperation](GLOSSARY.md#multi-database-cooperation) contract: `WIP-ALPHA-019-0.0.7` in [`KANBAN.md`](../KANBAN.md). The cooperation is in `types/resolvers.py`, not in `management/`; the two cards are independent.
- Warning-free scalar registration via `StrawberryConfig.scalar_map`: `WIP-ALPHA-045-0.0.7` in [`KANBAN.md`](../KANBAN.md). The scalar map is consumer-facing schema-construction shape, not management-command surface.
- Channels ASGI router ([`DjangoGraphQLProtocolRouter`](GLOSSARY.md#djangographqlprotocolrouter)): `TODO-ALPHA-029` for `0.0.12`.
- [Debug-toolbar middleware](GLOSSARY.md#debug-toolbar-middleware): `TODO-ALPHA-031` for `0.0.12`.
- [Response-extensions debug middleware](GLOSSARY.md#response-extensions-debug-middleware): `TODO-ALPHA-032` for `0.0.12`.
- Test-client helpers ([`TestClient`](GLOSSARY.md#testclient), [`GraphQLTestCase`](GLOSSARY.md#graphqltestcase)): `TODO-ALPHA-033` for `0.0.12`.

## Definition of done

The card is complete when all of the following are true:

1. `django_strawberry_framework/management/__init__.py` exists with a one-line module docstring (no further content); `django_strawberry_framework/management/commands/__init__.py` exists with a one-line module docstring (no further content).
2. `django_strawberry_framework/management/commands/export_schema.py` exists and defines `Command(BaseCommand)` per [Decision 2](#decision-2--command-class-shape) — `help = "Export the GraphQL schema"`, `add_arguments` registering positional `schema` (`nargs=1, type=str, help="The schema location"`) and optional `--path` (`nargs="?", type=str, help="Optional path to export"`), `handle` per [Decision 3](#decision-3--symbol-resolution-via-strawberryutilsimporterimport_module_symbol), [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema), and [Decision 5](#decision-5--commanderror-for-three-failure-modes). Module docstring (required by `D100`) and class docstring (required by `D101`) present. No `--watch`, no `--indent`, no `--json`, no settings-backed defaults, no alias (per [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias)).
3. `django_strawberry_framework/__init__.py` is NOT modified (per [Decision 1](#decision-1--module-location--no-public-export)). `__all__` is unchanged.
4. `tests/base/test_init.py`'s `__all__` assertion is unchanged (per [Decision 1](#decision-1--module-location--no-public-export)).
5. `tests/management/__init__.py` exists with a one-line module docstring (no further content). `tests/management/test_export_schema.py` exists and contains the 5 tests listed in the [Test plan](#test-plan) — happy stdout, happy `--path`, three `CommandError` shapes (unimportable, non-`Schema`, missing positional), and default-symbol-name fallback. Every test uses `django.core.management.call_command(...)` per [Decision 8](#decision-8--tests-go-through-call_command-not-direct-handle); no direct `Command().handle(...)` calls.
6. `examples/fakeshop/tests/test_commands.py` carries one new test `test_export_schema_command_against_fakeshop_schema` per [Decision 10](#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query). No file under `examples/fakeshop/test_query/` is created.
7. `examples/fakeshop/config/settings.py` is NOT modified (the existing `"django_strawberry_framework"` entry in `INSTALLED_APPS` is sufficient for Django to discover the command).
8. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`).
9. [`docs/GLOSSARY.md`](GLOSSARY.md), [`docs/README.md`](README.md), [`docs/TREE.md`](TREE.md), [`KANBAN.md`](../KANBAN.md), and [`CHANGELOG.md`](../CHANGELOG.md) reflect the shipped state per the [Doc updates](#doc-updates) section. The `- schema export management command` bullet at [`docs/README.md`](README.md) line 113 is removed in full; the `[alpha]` tag on the `management/` block at [`docs/TREE.md`](TREE.md) line 309 is removed. [`README.md`](../README.md), [`GOAL.md`](../GOAL.md), and [`TODAY.md`](../TODAY.md) are NOT edited.
10. [`KANBAN.md`](../KANBAN.md) moves `WIP-ALPHA-018-0.0.7` to Done with the next `DONE-NNN-0.0.7` id and a past-tense body summarizing the shipped scope.
11. The version bump is NOT in this card per [Decision 9](#decision-9--joint-0_0_7-cut); the last `0.0.7` card to ship owns `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion.
12. Zero new public exports — `__all__` is unchanged.
13. `uv run ruff format .` passes; `uv run ruff check --fix .` passes; `uv run pytest --no-cov` passes (explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov`; coverage enforcement is CI's job per `pyproject.toml [tool.coverage.report] fail_under = 100`, not this slice's; workers verify the suite passes, not that coverage stays at 100%).
