# Spec 029 review feedback

## Verdict

The spec is on the right track for the larger goal: recreate the original
`django_graphene_filters` feature set on a DRF-shaped, `Meta`-first Strawberry
foundation instead of inheriting strawberry-graphql-django's decorator-heavy
consumer API.

This card is correctly scoped as a consumer-DX cleanup / foundation card, not
as the whole parity project. It supports the parity path by tightening schema
construction, adding an inspect command, and adding a `Meta`-level nullability
escape hatch. The already-shipped filters and orders map cleanly onto the old
package's `AdvancedFilterSet` / `RelatedFilter` and `AdvancedOrderSet` /
`RelatedOrder`; later cards still need to carry the old package's connection
field, cascade permissions, search filters, fieldsets, and aggregates.

I would not implement the spec unchanged yet. The core design is sound, but the
details below need correction for the spec to be executable and honestly
verified.

## Findings

### P1 - `--schema config.schema` will not work with `import_string`

Slice 2 says the inspect command's `--schema <dotted_path>` import mirrors
`export_schema`, but the proposed loader does not mirror it. The shipped export
command uses `strawberry.utils.importer.import_module_symbol(...,
default_symbol_name="schema")`, which is why both `config.schema:schema` and
`config.schema` work in `examples/fakeshop/tests/test_export_schema.py`.

By contrast, `django.utils.module_loading.import_string("config.schema")`
tries to import module `config` and read an attribute named `schema` from that
package. In this project `examples/fakeshop/config/__init__.py` is empty, so
that call fails with:

```text
ImportError: Module "config" does not define a "schema" attribute/class
```

Impact: the planned `test_inspect_with_schema_option` will fail, and the cold
CLI path still will not finalize the registry from `--schema config.schema`.
There is a second correctness trap here: if the command catches every
`ImportError` from a dotted type path and falls back to registry-name lookup, it
can mask a real import-time bug inside a consumer module.

Required spec change:

- Use `import_module_symbol(options["schema"], default_symbol_name="schema")`
  for the `--schema` option, matching `export_schema`.
- Keep `import_string` for the positional type argument only when resolving a
  fully dotted object path such as `apps.library.schema.BookType`.
- Fall back to registered-name lookup only for bare names, or at least only
  after determining the argument is not a dotted import path. A dotted import
  failure should raise `CommandError` with the original import failure, not be
  hidden behind a registry miss.
- Test both accepted schema selector forms: `config.schema` and
  `config.schema:schema`.

### P1 - The bare-name inspect tests are order-dependent as written

The spec's happy-path example uses:

```python
call_command("inspect_django_type", "BookType")
```

That only works after `config.schema` has imported all app schemas and called
`finalize_django_types()`. The command itself cannot discover `BookType` by
bare name in a cold registry unless `--schema` imports the schema first. The
fakeshop live-test README explicitly warns that schema tests must clear the
registry and reload app schema modules / `config.schema` to avoid stale or
missing `DjangoType` classes.

Impact: `examples/fakeshop/tests/test_inspect_django_type.py` could pass when
run after another test that imported `config.schema`, then fail when run alone.
That is not an acceptable command contract or test plan.

Required spec change:

- Add an explicit fixture for the example command tests that clears the global
  registry and imports/reloads `apps.library.schema`, `config.schema`, and any
  needed URL/schema modules before bare-name assertions.
- Keep a separate cold-path test that starts from a cleared registry and calls
  `call_command("inspect_django_type", "BookType", "--schema",
  "config.schema")`, proving the option performs finalization.
- State that bare-name lookup is intentionally a post-schema-import convenience;
  cold CLI usage should pass `--schema`.

### P2 - Slice 1 undercounts the extension migration and the edit map still omits `GOAL.md`

The spec now has the correct singleton-factory target, but the migration size
is stale. A focused audit with `rg -c "extensions=\\["` reports:

```text
tests/optimizer/test_extension.py: 42
tests/optimizer/test_relay_id_projection.py: 3
tests/optimizer/test_field_meta.py: 1
tests/test_list_field.py: 2
tests/types/test_generic_foreign_key.py: 1
examples/fakeshop/test_query/test_multi_db.py: 1
examples/fakeshop/config/schema.py: 1
```

One `tests/optimizer/test_extension.py` match is a prose/docstring example, but
that still leaves 41 actual schema-construction entries in that file. The five
package test files contain 48 actual schema-construction entries, not the
implementation-plan table's `~24 package test-schema sites`. The two
`_CaptureExt()` entries in `tests/optimizer/test_extension.py` are subclass
instances and must be migrated too; a grep for only `DjangoOptimizerExtension()`
will miss them.

The Slice 1 checklist and DoD correctly mention `GOAL.md`, but the
implementation-plan table's Slice 1 file list still omits it.

Impact: implementers following the table can leave deprecated instance-form
entries behind, causing Strawberry's instance-extension deprecation warning to
survive and the proposed no-warning assertion to fail. They can also miss the
north-star `GOAL.md` schema update even though the checklist requires it.

Required spec change:

- Update the Slice 1 implementation-plan table to include `GOAL.md`.
- Replace the `~19` / `~24` estimates with current counts, or remove the
  fragile counts and specify an audit command.
- Make the audit target all `strawberry.Schema(..., extensions=[...])` entries,
  not only `DjangoOptimizerExtension()` literals. Named `ext` instances,
  strictness variants, bare class entries, and subclass instances such as
  `_CaptureExt()` all need a callable factory wrapper.

### P2 - The `required_overrides=("subtitle",)` acceptance resolver can expose invalid data

The Slice 3 acceptance type sets `required_overrides = ("subtitle",)` on
`library.Book`. That is a valid feature contract if the consumer guarantees the
field is non-null at the GraphQL boundary. The current fakeshop data does not
guarantee that. `examples/fakeshop/test_query/test_library_api.py` already
creates `Book` rows with `subtitle=None`, and many other `Book.objects.create`
calls omit `subtitle`.

The planned test only introspects SDL, so it can pass while the dedicated root
resolver is queryable and broken. If that resolver returns all books and a
client queries `subtitle`, Strawberry must surface a non-null violation because
the GraphQL type says `String!` while Django returns `None`.

Impact: the spec would verify the schema shape but not verify the exposed API
works. That violates the fakeshop live-query rule and gives consumers a bad
example for `required_overrides`.

Required spec change:

- Either make the dedicated acceptance resolver return only rows satisfying the
  declared GraphQL invariant, e.g. `Book.objects.exclude(subtitle__isnull=True)`,
  or choose a nullable field / fixture setup where the invariant is true.
- Add a live HTTP data query against the acceptance root field that requests
  `title` and `subtitle` and asserts no GraphQL errors.
- Document the core rule: `required_overrides` changes the GraphQL contract; it
  does not change the database column or sanitize runtime values.

### P3 - The spec still contains raw numeric source-line references

The current-state section still uses raw numeric line references for several
extension sites. This is a standing design doc, not a per-cycle scratchpad, so
the repo rule from `AGENTS.md` / `START.md` applies: source references should
use symbol-qualified paths or unique substrings, not raw line numbers.

Impact: this does not break implementation, but it does violate the standing-doc
reference convention and will create churn when files move or tests are edited.

Required spec change:

- Replace raw numeric references with forms such as
  `tests/optimizer/test_field_meta.py #"extensions=[DjangoOptimizerExtension()]"`
  or symbol-qualified references where an enclosing function is useful.

## Positive checks

- The singleton-factory decision is technically correct for the installed
  Strawberry. `Schema.get_extensions()` returns existing `SchemaExtension`
  instances as-is and otherwise calls the extension entry. A callable returning
  a module- or function-scoped singleton preserves the existing plan cache while
  avoiding the instance-form deprecation emitted at `Schema.__init__`.
- The spec correctly preserves the DRF-shaped public surface: `DjangoType.Meta`
  keys, `Meta.filterset_class`, `Meta.orderset_class`, and now
  `Meta.nullable_overrides` / `Meta.required_overrides`. It does not drift into
  stacked consumer-facing Strawberry decorators.
- The `inspect_django_type` command's source-of-truth decision is correct: read
  resolved annotations from `origin.__annotations__` after finalization, and use
  `selected_fields` / `field_map` for Django metadata and converter
  classification. Re-running `convert_scalar` would lie about consumer-authored
  annotations and nullability overrides.
- The two distinct inspect error branches are correct: no
  `__django_strawberry_definition__` means an abstract / non-registered
  `DjangoType`; `definition.finalized is False` means the concrete type exists
  but `finalize_django_types()` has not run.
- The Slice 3 validation flow is pointed at the right root cause: add net-new
  `ALLOWED_META_KEYS`, normalize on `_ValidatedMeta`, validate targets after
  field selection and consumer-authored field detection, and reject relations /
  Relay pk / excluded / consumer-authored targets.
- The scalar-only scope is appropriate for this card. Relation nullability
  overrides would touch finalizer relation annotation semantics and should stay
  out of this cleanup slice.

## Feature-parity direction

The package is still aligned with recreating the original
`django_graphene_filters` package, but the parity story should stay explicit:

- `AdvancedDjangoObjectType` maps to `DjangoType` plus `Meta` keys and
  `finalize_django_types()`.
- `AdvancedFilterSet` / `RelatedFilter` are already represented by the shipped
  `FilterSet` / `RelatedFilter` system.
- `AdvancedOrderSet` / `RelatedOrder` are already represented by the shipped
  `OrderSet` / `RelatedOrder` system.
- `AdvancedDjangoFilterConnectionField` maps to the upcoming
  `DjangoConnectionField` / Relay connection work, not to this cleanup card.
- `apply_cascade_permissions`, `AdvancedFieldSet`, `SearchQueryFilter` /
  `SearchRankFilter` / `TrigramFilter`, `AdvancedAggregateSet`, and
  `RelatedAggregate` remain future parity work per the roadmap.

So the answer is yes: the spec is moving in the correct direction. It should be
tightened around the concrete issues above before implementation starts, because
those are not cosmetic; they affect whether the command works, whether tests are
order-independent, whether Slice 1 actually removes the warnings, and whether
the live acceptance API can be queried successfully.

## Verification performed

- Read the project orientation docs the review is grounded in: `AGENTS.md`,
  `START.md`, `docs/README.md`, and `examples/fakeshop/test_query/README.md`.
- Re-read `docs/spec-029-consumer_dx_cleanup-0_0_9.md`.
- Checked the installed Strawberry `Schema.get_extensions()` behavior.
- Checked `django_strawberry_framework/management/commands/export_schema.py` and
  `examples/fakeshop/tests/test_export_schema.py` for the existing schema-loader
  contract.
- Ran a local `import_string("config.schema")` check and confirmed it fails for
  this project shape.
- Audited current `extensions=[...]` construction sites with `rg`.
- Rechecked the old package public exports under
  `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters`.
- No pytest run, per repo instruction.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
