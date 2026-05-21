# Review: docs/spec-018-export_schema-0_0_7.md

## High

- `Command.add_arguments()` and `Command.handle()` need to be specified with the repo's actual ruff gates, not just the upstream strawberry-django shape. `pyproject.toml` selects both `D` and `ANN`, and there is no `django_strawberry_framework/**` per-file ignore for `D102`, `ANN001`, or `ANN201`. As written, Decision 2 / the Definition of done require only module + class docstrings and show unannotated public methods:
  - `def add_arguments(self, parser):`
  - `def handle(self, *args, **options):`
  That will fail `uv run ruff check --fix .` for the new package module. The spec's Edge cases section also says `D102` is in the per-file ignores for `django_strawberry_framework/**`, but the current config does not contain that ignore. Pin the root-cause implementation shape in the spec: method docstrings for both public methods, `parser` annotated with Django's parser type, and explicit return annotations. The implementation should not rely on a late "verify the ignore list and adjust" note because the ignore list is known now and the final gate is required.

## Medium

- The package-internal test plan is internally inconsistent and currently omits the missing-positional test that the rest of the spec requires. The Slice 2 checklist, Decision 5, Doc updates, and Definition of done all require `CommandError` coverage for the missing positional argument, but `tests/management/test_export_schema.py` is described as "Five tests" and the five listed tests are stdout, `--path`, unimportable path, non-schema symbol, and default-symbol fallback. Add an explicit missing-positional test, and update the counts everywhere. If the intent is also to pin the `AttributeError` half of the import wrapper, split import failures into two tests: one for missing module and one for missing default/explicit symbol.

- The non-schema examples should use a selector that actually resolves to a non-`strawberry.Schema` object. The user-facing error-shape example uses `config.urls`, but fakeshop's `config.urls` imports `schema` from `config.schema`, so `import_module_symbol("config.urls", default_symbol_name="schema")` resolves the real schema and should succeed rather than raising the non-schema `CommandError`. The package test wording has a similar ambiguity: `call_command("export_schema", "test_module.not_a_schema")` imports the module `test_module.not_a_schema` and then reads its default `schema` attribute; it does not read `test_module.not_a_schema` as an attribute on `test_module`. Use an explicit-symbol selector such as `test_module:not_a_schema` / `config.urls:urlpatterns`, or state clearly that the synthesized module is named `test_module.not_a_schema` and contains `schema = 1`.

## Low

- The `docs/TREE.md` update list should also remove `the management command` from the prose in the current on-disk layout section that says every other target-layout module, including the management command, is not on disk yet. The spec already tells the implementer to add the `management/` subtree and remove the target-layout `[alpha]` tag; without this extra prose edit, `docs/TREE.md` can still contradict itself after Slice 3.

## Verified context

- `docs/spec-018-export_schema-0_0_7.md` is tracked and currently clean.
- `strawberry.utils.importer.import_module_symbol` in the local dependency imports the selector as the module name when no `:symbol` suffix is present, then reads `default_symbol_name="schema"`.
- `examples/fakeshop/config/schema.py` exposes the expected top-level `schema = strawberry.Schema(...)`.
- `examples/fakeshop/config/urls.py` imports that schema as a module-level `schema`, so it is not a valid non-schema error example.
- `pyproject.toml` has no package-source per-file ignore for `D102`, `ANN001`, or `ANN201`.