# Rationale: spec-022 — `export_schema` management command (why each Decision holds, rejected alternatives)

Deliberative companion to [`spec-022-export_schema-0_0_7.md`][spec-022]. The spec is the contract; this file holds the reasons behind each of its ten Decisions and the alternatives each one rejected.

## Entries keyed to the spec

Every entry names the spec decision or section it belongs to by heading and anchor.

### [Decision 1 — Module location & no public export][spec-022-d1]

Django's `manage.py` walks `<app>.management.commands.*` for every `<app>` in `INSTALLED_APPS`, so both `management` and `management.commands` must be importable packages — the `__init__.py` files are not optional. On the public-export half: Django's discovery resolves the command through its dotted module path, so consumers never write `from django_strawberry_framework.management.commands.export_schema import Command`; adding a name to `__all__` for something nobody imports is noise-only API widening; and the posture is symmetric with [`spec-021`][spec-021]'s [Decision 3][spec-021-decision-3--no-public-export] and with strawberry-django, which does not re-export its `Command` either.

**Alternatives rejected:**

- **`django_strawberry_framework/commands.py`, a flat module.** Django's discovery walks `management/commands/`, not arbitrary module names. A flat `commands.py` would never be found.
- **`django_strawberry_framework/cli.py`, a Click-based standalone CLI.** `manage.py` is the canonical entry point for Django commands; a parallel CLI doubles the surface and forces consumers to learn a second convention.
- **Re-export `Command` from `__init__.py` for testing convenience.** Tests resolve the class through `call_command` per [Decision 8][spec-022-d8]; the re-export would invite exactly the testing pattern that Decision forbids.

### [Decision 2 — `Command` class shape][spec-022-d2]

Two attributes and one method is the entire surface strawberry-django ships behaviorally, and the card's job is parity. Every attribute the command adds is one the test plan has to pin.

The annotation on `*args` is documentation-quality rather than gate-forced: `ANN002` / `ANN003` / `ANN401` / `D107` / `D417` are globally ignored at `pyproject.toml #"ANN002"`. `**options: Any` matches django-stubs' `BaseCommand.handle` so the argparse-populated `options["schema"]` can be passed on as a `str`.

**Deliberately NOT declared.** No `requires_system_checks` override — the default `("__all__",)` runs Django's system checks before `handle()`, which is fine. No `requires_migrations_checks` override — the command does not touch the database, so the default `False` is correct. No `stealth_options` — every option the command takes is documented.

**Alternatives rejected:**

- **`help = "Export the graphql schema"`, lowercase and upstream-verbatim.** The repo's prose Title-Cases `GraphQL`, and the divergence is one line.
- **A named `--schema` flag instead of the positional argument.** strawberry-django's shape is positional, migrants expect positional, and argparse's error message for a missing positional argument is clearer than for a missing named one.
- **The upstream's `nargs=1` on `schema` and `nargs="?"` on `--path`.** The consumer-visible invocation is identical either way (`manage.py export_schema config.schema`); `nargs=1`'s always-a-list semantics buy nothing but an index, and `nargs="?"` lets a bare `--path` parse as `None` and silently write to stdout.
- **The upstream's `--path` help text `"Optional path to export"`.** It hides that the write replaces an existing file; the shipped text states the destructive overwrite at `manage.py export_schema --help`.

### [Decision 3 — Symbol resolution through the shared `_imports` command helper][spec-022-d3]

Reusing the upstream importer keeps the command body trivial; Strawberry already documents the `module.path:symbol_name` shape and migrants know it. The `default_symbol_name="schema"` fallback matches the conventional layout where `config/schema.py` exposes a top-level `schema = strawberry.Schema(...)`.

The translation lives in `_imports.py` because a second command, `inspect_django_type`, needs the identical `ImportError` / `AttributeError` → `CommandError` translation; one helper keeps the two commands' failure reporting from diverging. The pre-import selector validation exists to replace an unrelated downstream exception with an attributable message: without it `""` reaches `import_module_symbol` as a `ValueError` and `.config.schema` as a `TypeError`, neither of which the narrow catch translates or explains.

**Alternatives rejected:**

- **Hand-roll dotted-path resolution with `importlib.import_module` + `getattr`.** The upstream importer already handles `module.path:symbol_name`, and rewriting it would force the test plan to re-pin the edge cases the upstream's own tests cover. The selector validation in `_imports.py` checks the selector's *shape* only; resolution itself is delegated unchanged.
- **Use `django.utils.module_loading.import_string`.** Django's helper does not understand the `module.path:symbol_name` shape, so using it would diverge from strawberry-django's contract. `_imports.py` offers `import_string_or_command_error` alongside for `inspect_django_type`'s dotted object path — the two coexist because they resolve different input languages.
- **Call `finalize_django_types()` defensively in `handle()` before resolving.** It would either be a no-op (the consumer's module chain already ran it) or would finalize an empty registry (if the consumer's schema module is the first thing to import the `DjangoType` modules). Neither shape is useful.

### [Decision 4 — SDL output via `strawberry.printer.print_schema`][spec-022-d4]

`print_schema` is Strawberry's canonical SDL serializer and handles directives, custom scalars, federation extensions, descriptions, and deprecation reasons; re-implementing it would re-walk the type graph for nothing. SDL is the Strawberry-native serialization, and consumers needing JSON pipe through downstream tools — `strawberry export-schema` takes the same posture. UTF-8 on the file write matches the upstream and avoids locale surprises.

The Decision marks the scope of the two newline suppressions because, read together with nothing marking the change of scope, the `ending=""` and `newline=""` bullets read as one cross-platform guarantee about `… > out.graphql` versus `--path out.graphql`. `ending=""` only removes an appended byte from the string handed to `self.stdout`; the interpreter's own `sys.stdout` translation still applies to whatever a shell redirects. Stating the scope once at the source text is cheaper than correcting each derived doc that over-reads it.

**Alternatives rejected:**

- **A JSON introspection mode behind `--json`.** Modern codegen tools prefer SDL or accept both, and the flag would double the test surface for no current consumer.
- **Pretty-printed SDL behind `--indent`.** SDL is whitespace-agnostic and formatting is a downstream concern (`prettier --parser graphql`).
- **`print(schema_output)` instead of `self.stdout.write`.** `call_command(..., stdout=captured)` redirects `self.stdout` but not `sys.stdout`, so `print(...)` would be uncapturable without monkey-patching.

### [Decision 5 — `CommandError` is the command's only failure surface][spec-022-d5]

`CommandError` is Django's documented escape hatch for "the command cannot proceed and it is the user's fault, not a bug"; `manage.py` prints the message and exits non-zero, which is what CI tooling needs, and both reference packages use it. `ConfigurationError` is reserved for `DjangoType` / `Meta` validation at class-definition and finalize time; using it for runtime command failures would muddy the hierarchy. A custom `ExportSchemaError` would force every test to import it and buy nothing.

**Alternatives rejected:**

- **Catch `Exception` and wrap it.** A broad except masks real bugs — a `KeyError` inside the consumer's `Schema(...)` constructor would surface as a confusing `CommandError`. The write-failure catch is `(OSError, ValueError)` rather than `Exception` for the same reason, and `tests/management/test_imports.py::test_import_or_command_error_does_not_swallow_other_exceptions` and `tests/management/test_imports.py::test_import_module_symbol_or_command_error_does_not_mask_module_body_valueerror` pin the resolution side: a `ValueError` raised by the consumer's *module body* must not be translated, even though a `ValueError` raised by `pathlib` must be.
- **Distinguish "module not found" from "attribute not found" with different messages.** The upstream does not, and `__cause__` carries the distinction for anyone who wants it.
- **Let the isinstance failure fall through to a `TypeError` inside `print_schema`.** The explicit check produces an attributable `CommandError` instead of a deep Strawberry-internal traceback.

### [Decision 6 — No watch, indent, JSON, settings-backed defaults, or alias][spec-022-d6]

Each non-shipped feature is a real pain point in some workflow, but none is repeated friction in the migration story this card serves; the card's job is parity with strawberry-django. Each feature has its own design surface to settle (what does `--watch` do under `runserver`? what JSON shape does `--json` emit?), which is a reason to land it under its own card rather than fold it in here.

**Alternatives rejected:**

- **Ship `--watch` because graphene-django ships it.** `--watch` earns its keep for the JSON-introspection workflow (regenerate `schema.json` on every Python change); for SDL output consumers already have `entr`, `watchexec`, and `make`. Its value is also tied to whether the consumer is iterating under `runserver`, which needs its own design pass.
- **Ship a settings-backed default for the positional argument** (`DJANGO_STRAWBERRY_FRAMEWORK = {"SCHEMA_PATH": "config.schema"}`). Rejected per [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands". The consumer's substitute is a one-line `Makefile` target.
- **Ship `--json` because it is "free".** It is not free. The JSON shape graphene-django emits is the GraphQL introspection *query result*, not a `print_schema` round-trip, so emitting it correctly means executing the schema — with the consumer's `DjangoOptimizerExtension` and any request-context dependencies in play.

### [Decision 7 — Test placement: `tests/management/__init__.py` ships][spec-022-d7]

[`AGENTS.md`][agents]'s no-`__init__.py` rule is scoped to `examples/fakeshop/tests/`; package-test subdirectories under `tests/` are outside it, and `tests/optimizer/__init__.py` and `tests/types/__init__.py` follow the positive convention.

**Alternatives rejected:**

- **A flat `tests/test_export_schema.py` with no subdirectory.** The source lives under a subpackage, test subdirectories mirror source subpackages, and a flat file would force a second command's tests to either re-flatten or migrate. `tests/management/` holds `test_export_schema.py`, `test_imports.py`, and `test_inspect_django_type.py`.
- **Omit `tests/management/__init__.py`, treating it like the `examples/fakeshop/tests/` rule.** Rejected per the scoping above.

### [Decision 8 — Tests go through `call_command`, NOT direct `handle()`][spec-022-d8]

Direct `handle()` calls bypass Django's argument parsing and let dev errors slip past the test contract. `call_command` runs the full argparse layer, so the test catches type-coercion and `nargs` mismatches a direct call would accept silently, and it captures `self.stdout` / `self.stderr` through the `stdout=` / `stderr=` kwargs without monkey-patching.

**Alternatives rejected:**

- **Allow direct `Command().handle(...)` for "unit" tests and `call_command` for "integration" tests.** The distinction is illusory for a Django command. `handle()` without argparse is not the production path, so the unit half would test code nobody runs.
- **Use `pytest.mark.django_db` instead of `call_command`.** The mark handles database setup and does not invoke commands. The two are orthogonal and coexist.

### [Decision 9 — Joint `0.0.7` cut][spec-022-d9]

The Decision restates [`spec-020`][spec-020]'s [Decision 10][spec-020-decision-10--joint-007-cut] so this card's reader does not have to chase a cross-spec reference.

**Alternatives rejected:**

- **This card bumps `0.0.7` because of its position in the bundle.** Ship order is whichever card a maintainer picks up next, not card `NNN`. Pinning the bump to a specific card creates a sequencing constraint with no engineering justification.
- **Add a separate release-cut card to `KANBAN.md` owning the bump.** Out of scope for a spec whose only authorized `KANBAN.md` edit is its own column move, and the "last card to ship" policy works as-is.

### [Decision 10 — Live coverage belongs in `examples/fakeshop/tests/`, NOT `test_query/`][spec-022-d10]

`examples/fakeshop/test_query/` is the live `/graphql/` HTTP tier, and an SDL-export command is not an HTTP-shaped surface. [`AGENTS.md`][agents]'s coverage-priority rule is satisfied rather than waived: the fall-back tier is correct only because the lines are genuinely unreachable from a live query, which they are.

**Alternatives rejected:**

- **Put the live test under `examples/fakeshop/test_query/test_export_schema.py`.** It violates that tree's declared scope and would be the only non-HTTP test in it.
- **Skip the live test and rely on the package tests for everything.** The package tests use a synthesized fixture schema, not the consumer's real one. The live test is what proves the command works against the consumer's real schema — a `DjangoSchema` (a `strawberry.Schema` subclass) built through `finalize_django_types()`, which is also the only place the isinstance guard's subclass tolerance is exercised — and a failure branch reached only after the real schema is imported, finalized, and rendered carries stronger contract pressure than a synthetic `test_module:schema` equivalent. That is why every contract with a project-schema shape lives in the live tier.

### The `## Test plan` section

**No negative-shape test.** The sibling AppConfig spec's consolidated negative-shape test exists because that card has several documented decisions about what *not* to add. Every Decision here is about what to add or how the existing surface behaves, so there is no forbidden-attribute list for `Command` to assert against; [Decision 6][spec-022-d6]'s omissions are pinned by `add_arguments` registering exactly two arguments.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-020-decision-10--joint-007-cut]: ../spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-020]: ../spec-020-list_field-0_0_7.md
[spec-021-decision-3--no-public-export]: ../spec-021-apps-0_0_7.md#decision-3--no-public-export
[spec-021]: ../spec-021-apps-0_0_7.md
[spec-022-d1]: ../spec-022-export_schema-0_0_7.md#decision-1--module-location--no-public-export
[spec-022-d10]: ../spec-022-export_schema-0_0_7.md#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query
[spec-022-d2]: ../spec-022-export_schema-0_0_7.md#decision-2--command-class-shape
[spec-022-d3]: ../spec-022-export_schema-0_0_7.md#decision-3--symbol-resolution-through-the-shared-_imports-command-helper
[spec-022-d4]: ../spec-022-export_schema-0_0_7.md#decision-4--sdl-output-via-strawberryprinterprint_schema
[spec-022-d5]: ../spec-022-export_schema-0_0_7.md#decision-5--commanderror-is-the-commands-only-failure-surface
[spec-022-d6]: ../spec-022-export_schema-0_0_7.md#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias
[spec-022-d7]: ../spec-022-export_schema-0_0_7.md#decision-7--test-placement-testsmanagement__init__py-ships
[spec-022-d8]: ../spec-022-export_schema-0_0_7.md#decision-8--tests-go-through-call_command-not-direct-handle
[spec-022-d9]: ../spec-022-export_schema-0_0_7.md#decision-9--joint-007-cut
[spec-022]: ../spec-022-export_schema-0_0_7.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
