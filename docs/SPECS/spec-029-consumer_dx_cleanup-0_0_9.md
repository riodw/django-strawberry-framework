# Spec: `DjangoType` consumer-DX cleanup pass (`extensions=` singleton-factory, `inspect_django_type`, `Meta.nullable_overrides` / `Meta.required_overrides`)

Status: **SHIPPED (`0.0.9`)** — card [`DONE-029-0.0.9`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.9]` heading. Three independent slices: Slice 1 (the per-construction-site singleton-factory form `extensions=[lambda: <instance>]` for [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], and the standing gate that rejects the two cold-cache forms, per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)), Slice 2 (the `inspect_django_type` diagnostic command), and Slice 3 (the `Meta.nullable_overrides` / `Meta.required_overrides` GraphQL-layer nullability override). The [Slice checklist](#slice-checklist) stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention).

Owner: package maintainer.

Predecessors: [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] (its Decision 10 maintainer-commanded-version-bump posture is the precedent [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut) extends to a joint cut); [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] (the filter subsystem whose [`django_strawberry_framework/types/base.py::_validate_filterset_class`][base] holds the "shape gates run once in `_validate_meta`" invariant Slice 3's two keys also hold to — without a per-key `_validate_*` helper: they shape-check inside `_validate_meta` through the shared [`_normalize_sequence_spec`][base], and their *target* validation runs later, from `__init_subclass__`, per [Decision 8](#decision-8--override-validation-and-collision-behavior)); [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] (the [Schema export management command][glossary-schema-export-management-command] whose [`Command`][export-schema-cmd] shape `inspect_django_type` mirrors); [`docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019] (the [Scalar field override semantics][glossary-scalar-field-override-semantics] Slice 3 composes with — a consumer-authored annotation already controls a field's nullability and is never silently re-overridden); [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-015] (the Relay-Node pk-suppression branch in [`_build_annotations`][base] that Slice 3's scalar path runs alongside); [`docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md`][spec-037] (the read-output entry point [`convert_field_output`][converters] and the `DjangoFileType` / `DjangoImageType` output objects the Slice 3 tri-state reaches). [`docs/GLOSSARY.md`][glossary] carries an entry for each of the three public symbols this spec owns — [`Meta.nullable_overrides`][glossary-metanullable_overrides], [`Meta.required_overrides`][glossary-metarequired_overrides], and the [Schema introspection management command][glossary-schema-introspection-management-command] — and the companion [`docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv`][spec-029-terms] anchors all three.

Each Decision's justification and the alternatives it rejected live in the rationale companion [`docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`][spec-029-rationale].

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoType`][glossary-djangotype] — the model-backed Strawberry type all three slices touch. Slice 2 introspects its [`DjangoTypeDefinition`][definition]; Slice 3 adds two `Meta` keys to its surface; Slice 1 fixes the `extensions=` form its schemas are built with.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the schema extension constructed as a factory over a module-level singleton, `extensions=[lambda: _optimizer]`, which keeps its instance-bound [Plan cache][glossary-plan-cache] and passes Strawberry a callable rather than the deprecated instance, per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form).
- [Plan cache][glossary-plan-cache] — the optimizer's plan cache; **instance-bound** (`self._plan_cache`), which is why Slice 1 uses a singleton-factory (one shared `_optimizer`) rather than the bare class or a constructing factory ([Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)).
- [Strictness mode][glossary-strictness-mode] — the optimizer's `strictness` constructor argument; a `strictness=` site declares the singleton `_optimizer = DjangoOptimizerExtension(strictness=...)` and passes `extensions=[lambda: _optimizer]`.
- [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] — the field-selection keys whose names-collection shape Slice 3's two override keys mirror, and whose `_select_fields` filtering determines which fields an override may legally name.
- [Scalar field conversion][glossary-scalar-field-conversion] — the [`convert_scalar`][converters] path Slice 3 threads a nullability override into; its `effective_null` widening step is what the override decouples from the Django column. Read-output conversion enters through [`convert_field_output`][converters], which routes file/image columns to their output object and delegates every other column to `convert_scalar`, threading the override through both (per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)).
- [Choice enum generation][glossary-choice-enum-generation] — choice-backed columns resolve to a generated enum before null widening; [Decision 9](#decision-9--choice-field-interaction) applies the override to `EnumType | None` the same way it applies to `str | None`.
- [Specialized scalar conversions][glossary-specialized-scalar-conversions] — the `ArrayField` / `HStoreField` early-return branches in `convert_scalar` plus the shared scalar path that [`BigInt`][glossary-bigint-scalar] (a `SCALAR_MAP` entry) flows through, each widening on `effective_null`; [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar) makes the override apply at every one of those widening sites.
- [Scalar field override semantics][glossary-scalar-field-override-semantics] — the four-corner consumer-override matrix; a consumer-authored annotation or `strawberry.field(...)` assignment bypasses conversion entirely, so [Decision 8](#decision-8--override-validation-and-collision-behavior) rejects naming a consumer-authored field in either override set.
- [`Meta.choice_enum_names`][glossary-metachoice_enum_names] — a planned sibling `Meta` key referenced when reasoning about choice-field overrides; not part of this spec.
- [`ConfigurationError`][glossary-configurationerror] — raised at type-creation time for every Slice 3 validation failure (unknown / excluded / consumer-authored / Relay-pk / relation override-target, both-sets collision).
- [Relation handling][glossary-relation-handling] — the FK / OneToOne / M2M / reverse-relation cardinality mapping; [Decision 10](#decision-10--non-relation-scope-relation-field-overrides-rejected-and-deferred) scopes Slice 3's overrides to non-relation model fields and rejects relation-field override targets.
- [`finalize_django_types`][glossary-finalize_django_types] — the finalizer; Slice 3 needs **no** finalizer change (overrides apply at type-construction time in [`__init_subclass__`][base], before finalization) and Slice 2 is a strict reader of the post-finalize [`DjangoTypeDefinition`][definition].
- [Definition-order independence][glossary-definition-order-independence] — the invariant that keeps Slice 3 entirely inside type-construction; the override resolves a column's GraphQL nullability with zero dependency on relation-target import order.
- [Schema export management command][glossary-schema-export-management-command] — `manage.py export_schema` at [`export_schema.py`][export-schema-cmd], whose `add_arguments` / `handle` / `CommandError` shape Slice 2's command mirrors.
- [Django `AppConfig`][glossary-django-appconfig] — `DjangoStrawberryFrameworkConfig`; the management-command discovery path Slice 2's command resolves through when consumers list `"django_strawberry_framework"` in `INSTALLED_APPS`.
- [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] — the sidecar keys whose `_validate_*_class` validators ([`base.py`][base]) hold the "shape gates run once in `_validate_meta`" invariant Slice 3's two keys also hold to. Slice 3's keys have no per-key `_validate_*` helper — they shape-check inside [`_validate_meta`][base] through the shared [`_normalize_sequence_spec`][base], and their *target* validation runs later, from [`__init_subclass__`][base] via [`_validate_nullability_override_targets`][base] (see [Decision 8](#decision-8--override-validation-and-collision-behavior)).
- [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] — cited because Slice 3 does NOT follow their deferred-key promotion gate (its keys are net-new public `Meta` keys, not promotions — see [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)).
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — the deferred-`Meta`-key promotion rule lives here; [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion) explains why the rule does NOT apply to this spec's net-new keys.

Dependency and forward-composition surfaces a reader will hit:

- [`DjangoConnectionField`][glossary-djangoconnectionfield] — the read-side primitive of the sibling [`DONE-030-0.0.9`][kanban] card; its schema-construction examples use the same singleton-factory `extensions=` form.
- [`DjangoListField`][glossary-djangolistfield] — the non-Relay list factory; its [`get_queryset`][glossary-get_queryset-visibility-hook]-applying wrapper is one of the schema surfaces `inspect_django_type` complements (it reports the resolved field table, not the resolver wiring).
- [`Meta.fields_class`][glossary-metafields_class] / [`FieldSet`][glossary-fieldset] — planned (`0.1.1`); the field-level resolver / redaction sidecar. Orthogonal to Slice 3 (nullability override is a type-construction-time annotation choice; `FieldSet` is a resolve-time gate).
- [`Meta.search_fields`][glossary-metasearch_fields] (`0.1.2`) / [`Meta.aggregate_class`][glossary-metaaggregate_class] (`0.1.3`) — planned Layer-3 sidecars, listed only as out-of-scope pointers.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package tests under `tests/`; project-level example tests under `examples/fakeshop/tests/`; live HTTP tests under `examples/fakeshop/test_query/`), the live-HTTP-priority coverage rule, the settings-keys rule, and the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told".
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical (Slice 3's nullability flip) and through in-process `call_command` tests where the surface is a management command (Slice 2).
- [`docs/TREE.md`][tree] — lists [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] alongside `export_schema.py`.
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, all defs at the bottom under the 10 canonical group headers).

## Slice checklist

Three independent functional slices plus a card-completion wrap. Boxes stay unticked because the `Status:` line is the completion source of truth (the shipped-spec convention).

- [ ] Slice 1: the singleton-factory `extensions=` construction form (per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form))
  - [ ] Every optimizer `extensions=` entry is a factory over a singleton **scoped to its construction site**: `extensions=[lambda: <instance>]`. That preserves the instance-bound [Plan cache][glossary-plan-cache] (Strawberry calls the factory per operation and gets the same instance back) and passes a callable, so Strawberry's instance-form `DeprecationWarning` never fires. The bare class and a constructing lambda `lambda: DjangoOptimizerExtension()` are rejected: each hands every operation a fresh instance, so the cache never hits.
  - [ ] Granularity is **per construction site, not per file** (per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)); `rg 'extensions=\['` finds the sites. Package tests that assert on an instance's `cache_info()` or carry a per-site `strictness=` keep a **function-local** `ext` and wrap it `extensions=[lambda: ext]` — e.g. [`tests/optimizer/test_extension.py`][test-extension] (its `_CaptureExt(DjangoOptimizerExtension)` subclass instances included), [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db], and the cache-hit snippet in [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme]. One-schema-per-module sites use a module-level `_optimizer`: the example schema [`examples/fakeshop/config/schema.py`][fakeshop-config-schema], the consumer snippets in [`docs/README.md`][docs-readme], [`docs/GLOSSARY.md`][glossary], and [`TODAY.md`][today], and the module and class docstrings of [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension].
  - [ ] The [`GOAL.md`][goal] astronomy schema constructs the optimizer through the singleton-factory (`_optimizer = DjangoOptimizerExtension(strictness="raise")`; `extensions=[lambda: _optimizer]`, beside the [`strawberry_config`][glossary-strawberry-config] scalar-map factory), so the north-star recipe shows the optimized boundary the [`DjangoConnectionField`][glossary-djangoconnectionfield] / Relay surfaces inherit.
  - [ ] **Standing forbidden-form gate:** the rule is enforced by **form**, not by a list of spellings, and by a standing test rather than a one-shot sweep. [`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`][test-ci-governance] classifies every `extensions=` sequence entry across active first-party `.py` and fails on either cold-cache form — the **bare class** `extensions=[DjangoOptimizerExtension]` and **any constructing lambda** `extensions=[lambda: DjangoOptimizerExtension(...)]`, keyword-carrying variants (`strictness=`, `nested_connection_strategy=`) included, since those are the same form and a spelling list cannot see them. The **instance** forms (`extensions=[DjangoOptimizerExtension()]`, `extensions=[ext]`, `extensions=[_CaptureExt()]`) are not the pin's job: Strawberry's instance-form `DeprecationWarning` meets `pytest.ini`'s `filterwarnings = error`, so any of them is already fatal at runtime. "Active first-party source" is exactly what the pin's corpus walks — the four [`scripts/check_citations.py`][check-citations] `SOURCE_TREES` plus the tracked `.py` files outside them that `EXTRA_SOURCE_FILES` carries back; the gitignored `docs/*/temp-tests/` scratch is excluded by construction. (The broad `rg 'extensions=\['` audit finds construction *sites*; this gate rejects the forms.)
  - [ ] [`CHANGELOG.md`][changelog] `## [0.0.9]` carries the `### Changed` bullet for the singleton-factory form.
- [ ] Slice 2: `inspect_django_type` diagnostic command
  - [ ] [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] ships with module + class docstring, `add_arguments` registering a positional `type` argument **plus `--schema <selector>`**, and `handle` printing the resolved per-field table per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution). The command **dispatches the `type` argument by shape** (NOT a catch-all fallback): a **dotted** argument resolves via Django's `import_string` and a dotted import failure raises `CommandError` carrying the **original** error — it is NOT swallowed and retried as a registry lookup; a **bare** name resolves via a unique registry match on the authoritative SDL type name (the active schema `NameConverter` applied to the type, honoring both a custom converter's renames and `Meta.name`) **or** the Python class `__name__`, so an operator can paste either surface. `--schema` is loaded via `import_module_symbol(..., default_symbol_name="schema")` (mirroring `export_schema`) to register + finalize all types first **and** to supply the schema's scalar map and name converter. Both loaders route through the shared [`django_strawberry_framework/management/commands/_imports.py`][commands-imports] helpers (`import_string_or_command_error` / `import_module_symbol_or_command_error`), which reject a malformed module path — empty or relative — before any import is attempted, then translate `ImportError` / `AttributeError` to `CommandError` preserving the original message. The command reads `target.__django_strawberry_definition__` (the [`DjangoTypeDefinition`][definition] populated by [`finalize_django_types`][glossary-finalize_django_types]) and prints, per selected field: Django field name → Django field type → resolved GraphQL type → nullability → which converter row fired ([`SCALAR_MAP`][converters] entry name, `convert_field_output` output object, choice enum, relation converter, or `relay.Node id`). **The Relay-suppressed pk** (per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)): on a Relay-shaped type a non-relation pk `continue`s past conversion and is absent from `origin.__annotations__`, so its row is sourced as the interface-supplied `GlobalID!` / "relay.Node id" rather than indexing `origin.__annotations__[pk_name]` (which would `KeyError`); a relation pk is never suppressed and renders as its relation row.
  - [ ] `CommandError` for: a **malformed** dotted path or `--schema` selector (empty or relative module path); an unresolvable argument (neither an importable dotted path nor a uniquely-registered type name); an **ambiguous bare name** (≥2 registered types share a resolution surface — list the candidates as copyable fully-dotted paths with their models); a resolved symbol that is not a [`DjangoType`][glossary-djangotype] subclass; a `DjangoType` with **no `__django_strawberry_definition__`** (abstract / no-`Meta` base); a `DjangoType` whose **`definition.finalized is False`** (`finalize_django_types()` has not run); and a **forward reference `finalize_django_types()` could not resolve** (Strawberry's `UNRESOLVED` sentinel — raise rather than print a bogus type). The no-definition and unfinalized cases are distinct branches per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution). Mirrors the [`export_schema.py`][export-schema-cmd] `CommandError` discipline.
  - [ ] Project-tier coverage: [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect], one file per command as [`examples/fakeshop/tests/test_export_schema.py`][fakeshop-tests-export] is. Bare-name `call_command("inspect_django_type", "BookType")` assertions run under a fixture that clears the registry and rebuilds the full project schema (`schema_reload.reload_all_project_schemas`), so they are order-independent; a separate **cold-path** test evicts the schema modules from `sys.modules` and clears the registry before `call_command("inspect_django_type", "BookType", "--schema", <selector>)`, proving `--schema` finalizes on its own, parametrized over the `config.schema` and `config.schema:schema` selector forms. The module also covers the failure modes the shipped schema can show.
  - [ ] Package coverage: [`tests/management/test_inspect_django_type.py`][test-management-inspect] for the branches that need a throwaway type (ambiguous bare names, the no-definition base, the unfinalized type, an unresolved forward reference, a relation pk on a Relay type, and the naming / rendering helpers), mirroring [`tests/management/test_export_schema.py`][test-management-export].
  - [ ] [`docs/GLOSSARY.md`][glossary] carries the `## Schema introspection management command` entry; [`docs/TREE.md`][tree] lists `inspect_django_type.py` under `management/commands/` and both test modules; [`CHANGELOG.md`][changelog] `## [0.0.9]` carries the `### Added` bullet.
- [ ] Slice 3: `Meta.nullable_overrides` / `Meta.required_overrides`
  - [ ] [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] contains `"nullable_overrides"` and `"required_overrides"` (net-new public keys — NOT a `DEFERRED_META_KEYS` promotion, per [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)). Validation splits across the three-stage flow per [Decision 8](#decision-8--override-validation-and-collision-behavior): [`_validate_meta`][base] shape-checks the two keys, normalizes them onto `_ValidatedMeta`, and raises the both-sets collision; [`_validate_nullability_override_targets`][base] runs in [`__init_subclass__`][base] **after** `_select_fields` + `consumer_authored_fields` + the Relay-shape check to reject unknown / excluded / consumer-authored / Relay-pk / relation targets, in that order.
  - [ ] [`django_strawberry_framework/types/converters.py::convert_scalar`][converters] takes a keyword-only `force_nullable: bool | None = None` tri-state per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar): `None` honors `field.null`; `True` emits `T | None` regardless; `False` emits `T` (non-null) regardless. The widening decision is computed once from `effective_null = field.null if force_nullable is None else force_nullable` and applied uniformly across the `ArrayField` / `HStoreField` / choice / scalar branches.
  - [ ] [`_build_annotations`][base]'s non-relation branch ([`django_strawberry_framework/types/base.py::_build_annotations`][base] #"annotations[field.name] = convert_field_output(") computes `force_nullable` for each field from the two override sets (`True` if in `nullable_overrides`, `False` if in `required_overrides`, `None` otherwise) and passes it to the read-output entry point [`convert_field_output`][converters], which applies it to a file/image output object directly and threads it unchanged into [`convert_scalar`][converters] for every other column.
  - [ ] Validation per [Decision 8](#decision-8--override-validation-and-collision-behavior) derives **two distinct name sets** — `model._meta.get_fields()` names (for "unknown") and the post-`Meta.fields`/`Meta.exclude` selected set (for "excluded") — as **separate error paths**: a name in either override set must (a) exist on the model (else **unknown-field** error), (b) be in the selected set (else **excluded / not-selected** error — kept distinct from (a) so the [`Meta.exclude`][glossary-metaexclude] contract isn't collapsed into "unknown"), (c) NOT be consumer-authored (an annotation / `strawberry.field` override already controls nullability per [Scalar field override semantics][glossary-scalar-field-override-semantics]), (d) NOT be the Relay-Node-suppressed pk, and (e) NOT be a relation field (non-relation scope per [Decision 10](#decision-10--non-relation-scope-relation-field-overrides-rejected-and-deferred)). A field named in **both** override sets raises [`ConfigurationError`][glossary-configurationerror] at the shape-check stage (contradictory). Every failure raises [`ConfigurationError`][glossary-configurationerror] at type-creation time naming the offending field.
  - [ ] Package coverage: [`tests/types/test_converters.py`][test-converters] (the `force_nullable` tri-state across scalar / nullable / choice / Array / HStore shapes, plus `convert_field_output`'s default-nullable file object) + [`tests/types/test_base.py`][test-types-base] (the validation + collision cases: unknown field, excluded field, consumer-authored field, Relay-suppressed pk, relation field, both-sets collision, shape guard, override-applies, and the file/image overrides).
  - [ ] Live HTTP coverage: a **dedicated acceptance-only secondary `DjangoType`** over the [`library`][fakeshop-library-models] `Book` model in [`apps/library/schema.py`][fakeshop-library-schema], `NullabilityOverrideBookType` (`Meta.primary = False`), declares `nullable_overrides = ("title",)` (non-null → nullable) and `required_overrides = ("subtitle",)` (nullable → non-null); `BookType` carries `Meta.primary = True` to satisfy the [`Meta.primary`][glossary-metaprimary] one-primary rule. **`required_overrides` declares `subtitle` as `String!`, but fakeshop seeds `Book` rows with `subtitle=None`**, so the dedicated root field `allLibraryNullabilityOverrideBooks` returns only rows satisfying the declared invariant **with deterministic ordering** — `Book.objects.exclude(subtitle__isnull=True).order_by("id")` — because the override changes the GraphQL contract, NOT the column or the data. Two live tests in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]: (a) introspect the acceptance type's SDL and assert `title` flipped `String!` → `String` and `subtitle` flipped `String` → `String!` while the `Book` columns are unchanged; (b) a **data query** against the dedicated root field requesting `title` + `subtitle` over the non-null-subtitle rows, asserting `errors` is absent. The existing `BookType` and the [`scalars`][fakeshop-scalars-models] app's types / assertions are untouched.
  - [ ] [`docs/GLOSSARY.md`][glossary] carries the `## Meta.nullable_overrides` and `## Meta.required_overrides` entries; [`CHANGELOG.md`][changelog] `## [0.0.9]` carries the `### Added` bullet.
- [ ] Card-completion wrap (NOT a code slice)
  - [ ] [`KANBAN.md`][kanban] records this card as [`DONE-029-0.0.9`][kanban], its `Spec:` reference pointing at [`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (this document).
  - [ ] **No version-file edits in this card.** `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` belong to the joint `0.0.9` cut per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut).

## Problem statement

Three small, independent consumer-DX gaps:

1. **Slice 1 — the `extensions=` instance form is deprecated upstream, and the package's plan cache is instance-bound.** Strawberry deprecates `extensions=[SomeExtension()]` (the instance form) and emits a `DeprecationWarning` for it, recommending a class or a factory callable. But [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]'s [Plan cache][glossary-plan-cache] lives on the instance, and Strawberry instantiates a bare class or calls a constructing `lambda` once per operation (cold cache, both sync and async). The form that satisfies both constraints is a **singleton factory** — `_optimizer = DjangoOptimizerExtension(); extensions=[lambda: _optimizer]` — which keeps one shared instance (cache preserved) AND passes a callable (no deprecation warning). [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) adopts it, with no plan-cache relocation needed.
2. **Slice 2 — a type-definition diagnostic.** Neither [`graphene-django`][graphene-django] nor [`strawberry-graphql-django`][strawberry-django] ships a `manage.py inspect_*` diagnostic for its type definitions; a consumer debugging "why did this field resolve to that GraphQL type?" otherwise introspects the constructed GraphQL schema by hand. `manage.py inspect_django_type <TypeName>` moves that diagnostic to the type-definition layer — it walks a [`DjangoTypeDefinition`][definition] and prints, per field, the Django field → resolved GraphQL type → nullability → which converter fired. This is the differentiating slice (capability neither upstream has).
3. **Slice 3 — GraphQL nullability welded to the Django column.** Without an override, a field's GraphQL nullability is exactly `field.null`: a non-null column renders as `T!`, a nullable column as `T`. Consumers need to decouple the two — render a non-null column as nullable in GraphQL (a field that is `NOT NULL` in the DB but legitimately absent from a partial response), or render a nullable column as required (a column that is `null=True` for legacy-migration reasons but always populated in practice). [`strawberry_django.field(required=True/False)`][strawberry-django] allows exactly this per field; [`graphene-django`][graphene-django] allows the same via per-field overrides on the `DjangoObjectType`. The other escape hatches are an `AlterField` migration (changes the database) or a consumer-authored annotation override (forces the consumer to hand-write the annotation and lose the converter's choice-enum / [`BigInt`][glossary-bigint-scalar] / array resolution). This slice surfaces the capability through two `Meta` tuple-set keys (`Meta.nullable_overrides` / `Meta.required_overrides`), consistent with the rest of the package's `Meta`-shaped API. It is the ⚛️&🍓-required slice and the design core of this spec.

The three slices share no implementation surface — Slice 1 is a construction-form rule over shipped code, Slice 2 is a strict reader of the existing introspection surface, and Slice 3 plugs into the scalar-resolution path at type-construction time.

## Goals

1. Construct `DjangoOptimizerExtension` everywhere as a singleton factory `extensions=[lambda: <instance>]`, which preserves the instance-bound [Plan cache][glossary-plan-cache] AND avoids Strawberry's instance-form `DeprecationWarning`; reject the bare class / constructing-`lambda` (cold cache per operation) with a standing gate (Slice 1, per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)).
2. Ship a `manage.py inspect_django_type <Type>` diagnostic command that walks a [`DjangoTypeDefinition`][definition] and prints the per-field resolution table, with `CommandError` for every failure mode, mirroring the [Schema export management command][glossary-schema-export-management-command] (Slice 2).
3. Ship `Meta.nullable_overrides` and `Meta.required_overrides` as net-new public `Meta` keys that decouple a non-relation field's GraphQL nullability from its Django column without an `AlterField` migration or a consumer-authored annotation, validated at type-creation time, composing with [`Meta.exclude`][glossary-metaexclude], [Choice enum generation][glossary-choice-enum-generation], and [Scalar field override semantics][glossary-scalar-field-override-semantics] (Slice 3).
4. Earn package coverage through live fakeshop HTTP flows (Slice 3's nullability flip on a dedicated acceptance-only `DjangoType` over the [`library`][fakeshop-library-models] `Book` model — which carries both a non-null and a nullable scalar column) and in-process `call_command` tests (Slice 2); the package coverage gate (`fail_under = 100`) is reached because those tests exercise the package end-to-end.
5. Keep package version state owned by the joint `0.0.9` cut: no slice in this card edits `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], `uv.lock`, or promotes a CHANGELOG release heading (see [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Non-goals

- **Relation-field nullability override.** Forward-FK / OneToOne nullability override (`TargetType | None` ↔ `TargetType`) and reverse-FK / M2M list nullability override (`[T!]` ↔ `[T!]!`) are out of scope; Slice 3's overrides apply to non-relation model fields only and reject a relation override-target with [`ConfigurationError`][glossary-configurationerror] (see [Decision 10](#decision-10--non-relation-scope-relation-field-overrides-rejected-and-deferred)). The list-vs-element nullability ambiguity on the many-side is its own design space.
- **`DjangoListField` / `DjangoConnectionField` argument injection.** Slice 1 sets the construction form only; it adds no filter / order / nullability arguments to any field.
- **A `--watch` / `--json` / SDL-diff mode on the inspect command.** Slice 2 prints a single human-readable table to stdout; `export_schema` has no watch or JSON mode either.
- **Persisting overrides on `DjangoTypeDefinition`.** Slice 3 resolves the override to a final annotation written to `cls.__annotations__` at type-construction time; [`DjangoTypeDefinition`][definition] has no `nullable_overrides` slot. Nothing needs one — the resolved annotation on `origin.__annotations__` IS the authoritative persisted record, and that is what the Slice 2 [`inspect_django_type`](#decision-4--inspect_django_type-command-shape-and-argument-resolution) command reads for post-override nullability (per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) / [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)).
- **A finalizer change for Slice 3.** Overrides apply in [`__init_subclass__`][base] before [`finalize_django_types`][glossary-finalize_django_types] runs; the finalizer is untouched. This is the [Definition-order independence][glossary-definition-order-independence] property: a column's nullability resolves with zero dependency on relation-target import order.
- **A version bump.** Owned by the joint `0.0.9` cut (see [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Borrowing posture

This card is a DX cleanup, not a new subsystem port. There is no cookbook pipeline to borrow. The relevant precedent is per-slice:

### Reference-package parity checkpoint

This card is one *enabling* step in the larger effort to rebuild the released [`django_graphene_filters`][upstream-cookbook] feature set on the package's Strawberry foundation (the working reference per [`START.md`][start]). It does not itself port a parity surface — it hardens schema construction (Slice 1), adds a type-metadata inspection command (Slice 2), and expresses GraphQL nullability overrides through `Meta` (Slice 3). For audit, the old package's exported surfaces map to the current package as:

| `django_graphene_filters` (Graphene) | `django-strawberry-framework` (Strawberry) | Status |
| --- | --- | --- |
| `AdvancedDjangoObjectType` | [`DjangoType`][glossary-djangotype] (`class Meta` sidecars) | shipped |
| `AdvancedFilterSet` / `RelatedFilter` | [`FilterSet`][glossary-filterset] / [`RelatedFilter`][glossary-relatedfilter] | shipped (`0.0.8`) |
| `AdvancedOrderSet` / `RelatedOrder` | [`OrderSet`][glossary-orderset] / [`RelatedOrder`][glossary-relatedorder] | shipped (`0.0.8`) |
| `AdvancedDjangoFilterConnectionField` | [`DjangoConnectionField`][glossary-djangoconnectionfield] / full Relay / [connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] | shipped (`0.0.9`) |
| `AdvancedFieldSet` | [`FieldSet`][glossary-fieldset] | planned (`0.1.1`) |
| `AdvancedAggregateSet` / `RelatedAggregate` | [`AggregateSet`][glossary-aggregateset] / [`RelatedAggregate`][glossary-relatedaggregate] | planned (`0.1.3`) |
| `apply_cascade_permissions` | [`apply_cascade_permissions`][glossary-apply_cascade_permissions] (permissions subsystem) | shipped (`0.0.10`) |
| `SearchQueryFilter` / `SearchRankFilter` / `TrigramFilter` + `Meta.search_fields` | Postgres search filters + [`Meta.search_fields`][glossary-metasearch_fields] | planned (`0.1.2`) |

This card touches the *foundation* under that map — the `extensions=` construction boundary the connection-field surfaces inherit (Slice 1), the type-definition introspection layer (Slice 2), and the `Meta`-key surface the override keys extend (Slice 3) — not the parity surfaces themselves.

### Slice 1 — borrow the upstream factory-callable form via a singleton to preserve the plan cache

[`strawberry-graphql-django`][strawberry-django] and the broader Strawberry ecosystem use `extensions=[SchemaExtension]` (class) or `extensions=[lambda: SchemaExtension(...)]` (factory callable); Strawberry warns on the instance form. The package's extension is **not** stateless — it carries an instance-bound [Plan cache][glossary-plan-cache] — so a bare class or a *constructing* factory would reset the cache every operation. The package therefore borrows the factory-callable shape with a twist: a factory that closes over a **singleton** (`_optimizer = DjangoOptimizerExtension(); extensions=[lambda: _optimizer]`), which is the upstream-recommended callable form yet keeps one shared instance (cache preserved) and emits no deprecation warning. See [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form).

### Slice 2 — `inspect_django_type` is conceptually like Django's `inspectdb`, scoped to the framework

Django's `manage.py inspectdb` introspects a database and prints model definitions; `inspect_django_type` is the framework analogue scoped to the type-definition surface — it introspects a finalized [`DjangoTypeDefinition`][definition] and prints the resolved GraphQL field table. Neither [`graphene-django`][graphene-django] (which ships `manage.py graphql_schema`, an SDL export) nor [`strawberry-graphql-django`][strawberry-django] (which ships `export_schema`, mirrored by this package's [Schema export management command][glossary-schema-export-management-command]) ships a type-definition introspection command. The structural model is the package's own [`export_schema.py`][export-schema-cmd] `Command` shape (`add_arguments` / `handle` / `CommandError`), not an upstream command.

### Slice 3 — borrow the *capability* of `strawberry_django.field(required=...)`, not its surface

[`strawberry_django.field(required=True/False)`][strawberry-django] lets a consumer override a single field's GraphQL nullability against the Django column's native nullability; [`graphene-django`][graphene-django] allows the same via per-field overrides declared on the `DjangoObjectType` class body. Both are **field-level decorator / assignment surfaces**. The package's [`START.md`][start] "Meta classes on every consumer surface" rule forbids that shape for consumer-facing declarations — so the package borrows the *capability* (decouple GraphQL nullability from the column) and re-expresses it as two `Meta` tuple-set keys (`Meta.nullable_overrides` / `Meta.required_overrides`, each a collection of field names — NOT a dict; see [Decision 5](#decision-5--two-key-tuple-set-override-form)), consistent with [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]. What is **not** borrowed: the per-field `field(required=...)` call site (the strawberry-django decorator shape the package exists to replace), and the implicit "the annotation declares the override" coupling (the package keeps the converter authoritative and layers the override on top — see [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)).

## User-facing API

### Slice 1 — `extensions=` construction (the singleton-factory form)

```python
from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    finalize_django_types,
    strawberry_config,
)

finalize_django_types()

# Recommended: a module-level SINGLETON wrapped in a factory. Strawberry calls
# the factory per operation and gets the same `_optimizer` back, so the
# instance-bound plan cache is preserved (both sync and async); and because the
# `extensions` entry is a callable (not an instance), Schema.__init__ does NOT
# emit the instance-form DeprecationWarning.
_optimizer = DjangoOptimizerExtension()  # one instance, one plan cache; pass strictness= here
schema = DjangoSchema(
    query=Query,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)

# Correct caching but DEPRECATED (Schema.__init__ warns "...will be removed..."):
#   extensions=[DjangoOptimizerExtension()]          # instance — cache preserved, but warns
# WRONG (fresh instance per operation → cold plan cache, both modes):
#   extensions=[DjangoOptimizerExtension]            # bare class
#   extensions=[lambda: DjangoOptimizerExtension()]  # constructing factory
```

### Slice 2 — `manage.py inspect_django_type <Type>`

```shell
# Cold process: --schema imports the project schema first so every type registers and finalizes:
uv run python examples/fakeshop/manage.py inspect_django_type BookType --schema config.schema

# By fully-dotted object path (resolved via Django's import_string; no registry fallback):
uv run python examples/fakeshop/manage.py inspect_django_type apps.library.schema.BookType --schema config.schema
```

A bare name without `--schema` resolves only when the registry is already populated and finalized in-process (a test fixture, or a shell where the project schema was imported).

Illustrative output (exact column layout is an implementation detail; the contract is "every selected field, with its *resolved* GraphQL type and nullability, in selection order."):

```text
BookType  (model: apps.library.models.Book)
  field                django field type    graphql type                     nullable   converter
  -------------------- -------------------- -------------------------------- ---------- --------------------
  loans                ManyToOneRel         [LoanType!]!                     no (list)  relation: reverse FK
  id                   BigAutoField         GlobalID!                        no         relay.Node id
  title                TextField            String!                          no         SCALAR_MAP[TextField]
  subtitle             TextField            String                           yes        SCALAR_MAP[TextField]
  circulation_status   CharField            BookTypeCirculationStatusEnum!   no         choice enum
  shelf                ForeignKey           ShelfType!                       no         relation: forward FK
  genres               ManyToManyField      [GenreType!]!                    no (list)  relation: M2M
```

Rows come out in `definition.selected_fields` order, and the "django field type" column is `type(field).__name__` verbatim — so a reverse FK reads `ManyToOneRel` and a choice column reads its plain `CharField`, with the choice fact carried by the converter column instead. The title is the type's SDL name (a `Meta.name` or a custom name converter shows there).

`BookType` is Relay-Node-shaped — its [`Meta.interfaces`][glossary-metainterfaces] includes `relay.Node` — so its pk is suppressed from `cls.__annotations__` (the interface supplies `id: GlobalID!`) and its `id` row is sourced from the [Relay Node integration][glossary-relay-node-integration] interface as `GlobalID!` / "relay.Node id" per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)'s suppressed-pk contract. A type that is **not** Relay-shaped keeps its pk in the annotations and renders it as a plain scalar — `ShelfType`'s `BigAutoField` pk reports `Int!` with converter `SCALAR_MAP[BigAutoField]` — read from `origin.__annotations__` like any other non-relation field. A file or image column names the read-output converter that fired (`convert_field_output -> DjangoFileType` / `DjangoImageType`), not its `SCALAR_MAP` row.

### Slice 3 — `Meta.nullable_overrides` / `Meta.required_overrides`

```python
from django_strawberry_framework import DjangoType

from . import models


class NullabilityOverrideBookType(DjangoType):
    """Acceptance-only secondary type on Book (BookType stays the primary)."""

    class Meta:
        model = models.Book
        fields = ("id", "title", "subtitle")
        primary = False  # BookType carries Meta.primary = True
        # `title` is NOT NULL in the database but the GraphQL surface
        # should allow it to be absent (e.g. a partial-projection response):
        nullable_overrides = ("title",)
        # `subtitle` is null=True in the database but is always populated in
        # practice, so the GraphQL surface marks it required:
        required_overrides = ("subtitle",)
```

- [`Meta.nullable_overrides`][glossary-metanullable_overrides] — a non-string sequence or set of non-relation field names whose GraphQL type is forced nullable (`T` → `T | None`, rendered `T` instead of `T!`) regardless of the Django column's `null` flag.
- [`Meta.required_overrides`][glossary-metarequired_overrides] — a non-string sequence or set of non-relation field names whose GraphQL type is forced non-null (`T | None` → `T`, rendered `T!` instead of `T`) regardless of the column's `null` flag. On a file/image column this is also the opt-out from the default-nullable output object: `required_overrides` renders `DjangoFileType!` / `DjangoImageType!` in place of the default `… | None`.

Both keys mirror the [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] name-collection shape. The two sets must be disjoint; naming a field in both raises [`ConfigurationError`][glossary-configurationerror].

#### Error shapes (Slice 3)

- A name in `nullable_overrides` / `required_overrides` that is not a field on the model: [`ConfigurationError`][glossary-configurationerror] at type-creation time naming the field, the model, and the override key.
- A name that is excluded via [`Meta.exclude`][glossary-metaexclude] (or otherwise not in the selected field set): [`ConfigurationError`][glossary-configurationerror] — the override targets a field that will not appear in the GraphQL type.
- A name that is a consumer-authored field (annotation or `strawberry.field` assignment): [`ConfigurationError`][glossary-configurationerror] — the consumer's annotation already controls nullability per [Scalar field override semantics][glossary-scalar-field-override-semantics]; the override would be silently ignored, so the package fails loud.
- A name that is the Relay-Node-suppressed pk on a Relay-shaped type: [`ConfigurationError`][glossary-configurationerror] — the pk's nullability is the `relay.Node` interface's contract (`id: GlobalID!`), not the column's.
- A name that is a relation field (FK / OneToOne / M2M / reverse): [`ConfigurationError`][glossary-configurationerror] directing the consumer to the non-relation scope (relation override deferred per [Decision 10](#decision-10--non-relation-scope-relation-field-overrides-rejected-and-deferred)).
- The same field named in both sets: [`ConfigurationError`][glossary-configurationerror] (contradictory — a field cannot be both forced-nullable and forced-required).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file is **`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`** (this document): `029` is the card's number, `0_0_9` its target patch, and `consumer_dx_cleanup` names the whole three-slice card rather than any one slice.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 1][rationale-d1].

### Decision 2 — One spec covers all three slices

This single spec covers Slice 1, Slice 2, and Slice 3: the [`docs/SPECS/NEXT.md`][next] flow authors one spec per card, and the card is the whole cleanup pass.

Rationale companion — this Decision's justification and its one rejected alternative: [Decision 2][rationale-d2].

### Decision 3 — Slice 1 adopts the singleton-factory `extensions=` form

[`DjangoOptimizerExtension`][glossary-djangooptimizerextension]'s [Plan cache][glossary-plan-cache] lives on the instance (`self._plan_cache`), and Strawberry deprecates passing an instance. The migration form that preserves the cache AND drops the deprecation warning is a factory over a singleton.

**Mechanism.** Strawberry's `Schema.get_extensions` resolves the extension list per operation as `ext if isinstance(ext, SchemaExtension) else ext()`, and both `execute()` and `execute_sync()` call it. Therefore:

- A passed-in **instance** is returned unchanged every operation (the `isinstance` passthrough) — **one shared instance, plan cache preserved**, in both sync and async — BUT `Schema.__init__` emits a `DeprecationWarning` ("Passing an extension instance to `extensions=[...]` is deprecated and will be removed in a future release. Pass the class itself, or a factory callable …").
- A **bare class** or a **constructing `lambda`** (`lambda: DjangoOptimizerExtension()`) is re-instantiated **every operation, in both modes** — a cold `self._plan_cache` per operation, **zero hit rate**.
- A **`lambda` that closes over a singleton** — `_optimizer = DjangoOptimizerExtension(); extensions=[lambda: _optimizer]` — **resolves the conflict**: `get_extensions` runs `ext()` and gets the *same* `_optimizer` back every operation (plan cache preserved, both modes), and the `extensions` list holds a *callable*, not a `SchemaExtension` instance, so `Schema.__init__`'s instance-deprecation check does not fire — **no `DeprecationWarning`**. Sharing the instance is safe because per-operation optimizer state is not stored on `self`: the extension is an operation-bound extension whose per-operation state the package's operation runner binds ([`django_strawberry_framework/extensions/operation_state.py`][operation-state]), and its configuration (`strictness`, the nested-connection strategy) is settled once at construction in [`optimizer/extension.py`][optimizer-extension].

**Decision: every optimizer `extensions=` entry is a factory over a singleton scoped to that construction site — `extensions=[lambda: <instance>]`.** It preserves the instance-bound plan cache AND removes the deprecation warning, with **no plan-cache relocation required**. It covers anonymous instances, the **named** form `ext = DjangoOptimizerExtension(); extensions=[ext]` (which also trips the deprecation warning), subclass instances, and the bare class (a cold-cache regression). **Granularity is per construction site, not per file:**

- **Consumer docs + the example [`config/schema.py`][fakeshop-config-schema]** have one schema per module, so a module-level `_optimizer = DjangoOptimizerExtension(...)` (with `strictness=` as needed) wrapped as `extensions=[lambda: _optimizer]` is right.
- **The package test modules build many schemas**, several holding a *function-local* `ext` whose `cache_info()` a test asserts on (e.g. the [`tests/optimizer/test_extension.py`][test-extension] rows asserting `ext.cache_info().misses`). Each such site keeps its **function-local** instance and wraps it `extensions=[lambda: ext]`. A single module-level instance shared across that file's schemas would **pollute the per-test cache counters** (order-dependent failures) and could not carry per-site `strictness=`. Per-file granularity is not merely coarse, it is unimplementable: [`tests/optimizer/test_extension.py::test_strictness_flags_a_relation_under_an_unplannable_root`][test-extension] builds two schemas **inside one function** from a `strictness="raise"` instance and a `strictness="off"` instance, and asserts opposite outcomes on each — one instance per module could not carry both values, and neither could one instance per function. The constructing-`lambda` is rejected here too: it rebuilds per execute, so a cache-hit assertion's second `execute_sync` would miss.

The bare instance stays correct but deprecated; the bare class / constructing-`lambda` are rejected (cold cache per operation), and the standing pin [`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`][test-ci-governance] keeps both out of active source (see the [Slice checklist](#slice-checklist)).

Rationale companion — this Decision's justification and its four rejected alternatives: [Decision 3][rationale-d3].

### Decision 4 — `inspect_django_type` command shape and argument resolution

The command ships at [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] as `Command(BaseCommand)`, mirroring [`export_schema.py`][export-schema-cmd]: `add_arguments` registers one positional argument (`type`) plus an optional `--schema <selector>` (see *Reaching a finalized registry* below); `handle` imports the schema (when given), resolves the type, reads `target.__django_strawberry_definition__`, and prints the per-field table; `CommandError` wraps every failure.

**Both loaders route through the shared command-import helper.** Neither loader calls its underlying importer directly: both go through [`django_strawberry_framework/management/commands/_imports.py`][commands-imports], shared with [`export_schema.py`][export-schema-cmd]. `import_string_or_command_error` and `import_module_symbol_or_command_error` each **validate the module path before attempting any import** via [`django_strawberry_framework/management/commands/_imports.py::_validate_absolute_module_path`][commands-imports] — an empty module path and a relative one (leading `.`) each raise their own `CommandError` naming the offending value and the reason, instead of letting `importlib` surface an internal error that does not say what the operator mistyped — and then translate `ImportError` / `AttributeError` into `CommandError` with the original message preserved as the `__cause__`. The two loaders stay distinct in *which* importer they wrap; the translation, the pre-validation, and the "does not swallow, does not mask" contract are one shared implementation.

**Argument resolution — dotted object path vs bare registered name, dispatched on the dot (not a catch-all fallback).** If the positional `type` argument **contains a dot**, it is a fully-dotted object path resolved via **`django.utils.module_loading.import_string`** (which splits on the last dot — `apps.library.schema.BookType` → module `apps.library.schema`, attribute `BookType`); an `ImportError` / `AttributeError` here raises `CommandError` carrying the **original** failure — it is **NOT** swallowed and retried as a registry lookup, because catching every import error would mask a real import-time bug inside a consumer module. If the argument has **no dot**, it is a bare type name resolved against the registry (next paragraph). `import_string` here resolves a fully-dotted *attribute* path; it is a different importer from the `--schema` option (see *Reaching a finalized registry*), which uses Strawberry's `import_module_symbol` exactly as [`export_schema.py`][export-schema-cmd] does.

**Bare-name lookup matches two surfaces, requires a unique result, and is a post-schema-import convenience.** A bare name is matched against **both** the type's authoritative SDL name — the active schema's `NameConverter` applied to the type, which honors a custom converter's renames **and** `Meta.name` — and the Python class `__name__`, so an operator can paste either the name they see in the schema or the name they see in the source. The registry can hold multiple `DjangoType` classes colliding on either surface ([`Meta.primary`][glossary-metaprimary] multi-type, two apps each declaring a `BookType`, or one type's `Meta.name` equal to another's class name). The no-dot branch walks `registry.iter_definitions()` — which visits each type once, so a single type matching on both surfaces still appends once — and collects every match: **exactly one** resolves; **zero** → `CommandError` naming `--schema` and the dotted form as the fixes; **two or more** → `CommandError` listing the candidates as copyable fully-dotted `module.qualname` paths with their models, asking the consumer to pass one. The command never returns the first match by registry-iteration order — that would make the result import-order-dependent. **Bare-name resolution only works once the registry is already populated and finalized in-process** (the in-process tests via their reload fixture, or a shell where the project schema has been imported); it is a convenience for an already-loaded schema, **not** a cold-CLI path — a bare name in a cold process has an empty registry → "unresolvable". A cold CLI invocation passes `--schema` (next paragraph).

**Output contract — the resolved type is read from the authoritative post-finalize record, never re-derived.** [`__init_subclass__`][base] writes the synthesized + consumer annotations to `definition.origin.__annotations__` (`origin` is the `DjangoType` class; `cls.__annotations__ = {**synthesized, **consumer_annotations}`), and [`finalize_django_types`][glossary-finalize_django_types] rewrites each pending relation annotation onto `source_type.__annotations__` via `resolved_relation_annotation`. **Which** record is authoritative depends on the field's origin, and the command dispatches most-specific-first:

1. **The Relay-Node-suppressed pk** wins over everything: a non-relation pk on a Relay-shaped type is absent from `origin.__annotations__` by construction, so the row is sourced from the interface as `GlobalID!` / "relay.Node id". The shape test is the same [`_is_relay_shaped`][base] predicate `_build_annotations` used when it suppressed the pk, so a `Meta`-declared `relay.Node`, a `CustomNode(relay.Node)` interface, and direct `class Foo(DjangoType, relay.Node)` inheritance all stay in lockstep with synthesis. A **relation** pk (`OneToOneField(primary_key=True)`, an MTI parent link) is never suppressed — `_build_annotations` routes every relation field through its relation branch before the pk-suppression check — so it keeps its annotation and renders as the relation row the schema actually builds.
2. **A consumer-authored field** (`definition.consumer_authored_fields`) reads its resolved type from the **finalized Strawberry field metadata**, `origin.__strawberry_definition__` — not from `origin.__annotations__`, whose entry for such a field is a `StrawberryAnnotation` object for a `strawberry.field` assignment and an *unresolved forward-ref string* for an annotated relation. The Strawberry definition is authoritative for both override kinds and has resolved its forward references. A forward reference [`finalize_django_types`][glossary-finalize_django_types] could **not** resolve surfaces as Strawberry's `UNRESOLVED` sentinel and raises `CommandError` rather than printing a bogus type.
3. **An auto-synthesized relation** reads its resolved annotation from `origin.__annotations__`, with one exception: a `relation_shapes = {<rel>: "connection"}` relation has had its list annotation *popped* by the Phase-2.5 synthesizer while the Django field stays in `selected_fields`, so its row is rendered from the synthesized `<rel>_connection` sibling's finalized Strawberry field instead of indexing a deleted key.
4. **An auto-synthesized non-relation field** reads its resolved annotation from `origin.__annotations__`, which **already reflects** Slice 3's `nullable_overrides` / `required_overrides` (the override is baked into the synthesized annotation at construction time per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)).

Alongside the resolved type the command reads the Django field name, the Django field type (`type(field).__name__`), and the column-native `nullable` from `definition.selected_fields` / `definition.field_map` ([`FieldMeta`][field-meta]); and it classifies the converter **to NAME which row fired**, never to determine nullability — the read-output converter and its output object for a column [`convert_field_output`][converters] routes through `FIELD_OUTPUT_TYPE_MAP`, "choice enum" for a choice column, otherwise the [`SCALAR_MAP`][converters] entry named by the **matched MRO ancestor** (so a consumer subclass of a supported field reports the ancestor row rather than its own class name), plus the relation-cardinality label and the Relay-supplied `GlobalID`. **Re-running `convert_scalar(field, type_name)` to get nullability would be wrong** — it reproduces the column-native `field.null` widening and would miss a `nullable_overrides` / `required_overrides` flip and any consumer-authored annotation; the resolved-record read is what makes the table honest about what the schema actually shows. The Relay-suppressed pk's absence from `cls.__annotations__` is at [`django_strawberry_framework/types/base.py::_build_annotations`][base] #"if suppress_pk_annotation and field.name == pk_name:": on a Relay-Node-shaped type the non-relation pk `continue`s past conversion because the interface supplies `id: GlobalID!`. A non-Relay type's pk is **not** suppressed and renders as its plain scalar (e.g. `BigAutoField` → `Int!`), read from `origin.__annotations__` like any other non-relation field.

**Reaching a finalized registry (cold CLI invocation).** A bare `manage.py inspect_django_type BookType` in a cold process registers nothing (no module imported `BookType`) → unresolvable; and even the dotted *type* form imports only the target's own module, which registers that one type but leaves the registry **unfinalized** (`finalize_django_types()` needs *every* relation target registered, so importing one module is not enough). So the command takes an optional **`--schema <selector>`** (e.g. `config.schema`) that it imports **first** — importing the project schema registers all `DjangoType`s and runs the module's `finalize_django_types()` — before resolving the target type. The imported schema object is not discarded once it has had that side effect: the command also reads its `config` for the **scalar map** and the **name converter**, so both the bare-name SDL match and the printed type names are the schema's own rather than a default's. Without `--schema` the command falls back to a default `NameConverter` and the package's own scalar names. **The `--schema` loader uses Strawberry's `import_module_symbol(..., default_symbol_name="schema")`, exactly as [`export_schema.py`][export-schema-cmd] does — NOT `import_string`.** This is load-bearing: `import_string("config.schema")` imports the package `config` and reads a `schema` **attribute** off it, which **fails** for this project because `examples/fakeshop/config/__init__.py` defines no such attribute (`ImportError: Module "config" does not define a "schema" attribute/class`); `import_module_symbol` instead imports the **module** `config.schema` and (via `default_symbol_name`) reads its `schema` symbol, so both `config.schema` and `config.schema:schema` resolve — the same two selector forms [`export_schema.py`][export-schema-cmd] accepts (verified by [`examples/fakeshop/tests/test_export_schema.py`][fakeshop-tests-export]). Without `--schema`, the command works only when the registry is already populated + finalized in-process; the unfinalized-`CommandError` names `--schema` as the fix. `--schema` is an explicit argument with no settings-key default (the package adds settings keys only when a feature needs them, per [`AGENTS.md`][agents]). **`--schema` relies on the schema module's import-time side effects** (class registration when the `DjangoType` subclasses are defined + the module's `finalize_django_types()` call); in a real cold CLI process the module is not yet imported, so those run, but an **in-process** test must simulate that (`sys.modules` eviction) because `import_module_symbol` returns a cached module unchanged — see the cold-path test in the [Test plan](#test-plan).

**Finalized-state contract (two distinct branches).** `cls.__django_strawberry_definition__` is assigned in [`__init_subclass__`][base] at registration time — **before** [`finalize_django_types`][glossary-finalize_django_types] runs — so its presence does NOT mean the type is finalized. Finalization is the `DjangoTypeDefinition.finalized` flag, flipped once every type's Phase-3 `strawberry.type(...)` call has returned. The command requires a finalized type because `origin.__annotations__` only carries resolved relation annotations post-finalize. The two states are distinct error branches: a resolved class with **no `__django_strawberry_definition__`** (an abstract / intermediate base `DjangoType` with no `Meta`, which never registers) and a definition with **`finalized is False`** (a concrete but not-yet-finalized type).

**`CommandError` failure modes:** (1) a malformed dotted path or `--schema` selector — an empty module path, or a relative one — rejected by `_validate_absolute_module_path` before any import is attempted; (2) an unresolvable argument (neither a dotted path that imports nor a uniquely-registered type name); (3) an ambiguous bare name (two or more registered types collide on the SDL name or the Python `__name__` — lists the candidates as copyable dotted paths with their models); (4) a resolved symbol that is not a [`DjangoType`][glossary-djangotype] subclass; (5) a `DjangoType` with no `__django_strawberry_definition__` (abstract / no-`Meta` base — "not a registered DjangoType"); (6) a `DjangoType` whose `definition.finalized is False` ("`finalize_django_types()` has not run - pass `--schema <your project schema dotted path>` so all types register and finalize"); (7) a consumer-authored field whose forward reference finalization could not resolve (Strawberry's `UNRESOLVED` sentinel). Branches (5) and (6) are separate messages.

**Test placement.** Coverage reachable through the shipped fakeshop schema lands at [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (in-process `call_command` against real finalized fakeshop [`DjangoType`][glossary-djangotype]s), following the one-file-per-command convention of [`examples/fakeshop/tests/test_export_schema.py`][fakeshop-tests-export]. Branches that need a throwaway type land at [`tests/management/test_inspect_django_type.py`][test-management-inspect], mirroring [`tests/management/test_export_schema.py`][test-management-export].

Rationale companion — this Decision's justification and its four rejected alternatives: [Decision 4][rationale-d4].

### Decision 5 — Two-key tuple-set override form

Slice 3 ships **two keys, each a collection of field names** — `Meta.nullable_overrides = ("a", "b")` and `Meta.required_overrides = ("c",)` — NOT a single dict-of-name-to-bool (`Meta.nullability = {"a": True, "c": False}`).

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 5][rationale-d5].

### Decision 6 — Net-new `ALLOWED_META_KEYS` entries, not a `DEFERRED_META_KEYS` promotion

`nullable_overrides` and `required_overrides` are in [`ALLOWED_META_KEYS`][base] **directly**. They were never in [`DEFERRED_META_KEYS`][base], unlike [`Meta.orderset_class`][glossary-metaorderset_class] and [`Meta.filterset_class`][glossary-metafilterset_class], which were reserved there before their subsystems shipped.

Rationale companion — this Decision's justification and its one rejected alternative: [Decision 6][rationale-d6].

### Decision 7 — Tri-state `force_nullable` threaded through `convert_scalar`

The override is implemented by threading a keyword-only tri-state `force_nullable: bool | None = None` through the converter, NOT by rewriting the returned annotation at the [`_build_annotations`][base] call site. Both converter entry points carry the parameter: [`convert_scalar`][converters], which owns scalar conversion, and the read-output entry point [`convert_field_output`][converters], which `_build_annotations` calls and which either applies the tri-state to a file/image output object or hands it to `convert_scalar` unchanged.

The tri-state:

- `None` (default) — honor `field.null`; every call site that passes nothing gets the column-native behavior.
- `True` — emit `T | None` regardless of `field.null` (force nullable).
- `False` — emit `T` (strip nullability) regardless of `field.null` (force required).

[`convert_scalar`][converters] computes `effective_null = field.null if force_nullable is None else force_nullable` once and applies it at each of the three widening sites: the `ArrayField` early-return branch (`list[inner] | None`), the `HStoreField` early-return branch (`JSON | None`), and the shared scalar / choice path's final widening (`py_type | None`).

[`_build_annotations`][base]'s non-relation branch computes `force_nullable` per field from the two override sets and passes it to the read-output entry point [`convert_field_output`][converters], which owns the same tri-state and dispatches on the column (the file/image routing is [`spec-037`][spec-037]'s contract):

- A `FileField` / `ImageField` resolves through `FIELD_OUTPUT_TYPE_MAP` to the structured `DjangoFileType` / `DjangoImageType` output object, whose **default is nullable** independent of the column's `null` / `blank` — the generated parent resolver returns `None` for an empty `FieldFile`, which is reachable even on a `null=False, blank=False` column. `force_nullable` still wins when set, so `required_overrides` (`force_nullable=False`) is the explicit opt-in to `DjangoFileType!`.
- Every other column delegates to [`convert_scalar`][converters] with `force_nullable` threaded through unchanged.

Keeping the file/image lookup off `convert_scalar` / `scalar_for_field` / [`SCALAR_MAP`][converters] is what stops an output object ever reaching the shared filter-input path; the override seam is the same one either way. The resulting annotation is written to `cls.__annotations__` in [`__init_subclass__`][base] (`cls.__annotations__ = {**synthesized, **consumer_annotations}`), so the override is **persisted on the class annotation itself** — no `DjangoTypeDefinition` slot is needed (see [Non-goals](#non-goals)), and that annotation is the authoritative record the Slice 2 [`inspect_django_type`](#decision-4--inspect_django_type-command-shape-and-argument-resolution) command reads for post-override nullability.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 7][rationale-d7].

### Decision 8 — Override validation and collision behavior

The override validation splits across the three-stage type-construction flow, and it cannot be collapsed into one helper called from [`_validate_meta`][base]: `_validate_meta` runs *before* `_select_fields`, before `consumer_authored_fields` is computed, and before Relay-pk suppression is known, so the selected names and `consumer_authored_fields` do not exist at `_validate_meta` time. The staging is forced by that ordering, not chosen for style.

1. **Shape + normalize (in [`_validate_meta`][base]).** Shape-check both keys through the shared [`_normalize_sequence_spec`][base] — the same normalizer [`Meta.exclude`][glossary-metaexclude] uses, keyed on the declared name so the rejection message names the key the consumer wrote — normalize each into a `frozenset[str]` on the returned `_ValidatedMeta`, and raise the **both-sets collision** here (a name in `nullable_overrides ∩ required_overrides` is a shape-level contradiction visible from the raw `Meta` alone — no model/field access needed).
2. **Target-validate (in [`__init_subclass__`][base], after `_select_fields` + `consumer_authored_fields` + the Relay-shape check).** Once the selected fields, the `consumer_authored_fields` frozenset, and the Relay-pk suppression state exist, [`django_strawberry_framework/types/base.py::_validate_nullability_override_targets`][base] raises [`ConfigurationError`][glossary-configurationerror] for every unknown / excluded / consumer-authored / Relay-suppressed-pk / relation target (rules below). Its parameters are keyword-only — `model`, `selected_fields`, `consumer_authored_fields`, `relay_shaped`, `nullable_overrides`, `required_overrides` — and it takes `relay_shaped: bool` rather than a pre-computed pk name, deriving `model._meta.pk.name` itself only when the type is Relay-shaped.
3. **Apply (in [`_build_annotations`][base]).** The two normalized override frozensets thread into `_build_annotations`, which computes `force_nullable` per field and passes it to [`convert_field_output`][converters], and on to [`convert_scalar`][converters] for every non-file column (per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)).

This keeps the package's "shape gates run once in `_validate_meta`" invariant intact and avoids re-reading raw `Meta` attrs in multiple places. **The target-validate helper derives two distinct name sets and keeps "unknown" and "excluded" as separate error paths** — collapsing them would weaken the [`Meta.exclude`][glossary-metaexclude] contract: the **model field names** from `model._meta.get_fields()` (rule 1 below — *unknown-field* reporting) and the **post-`Meta.fields` / `Meta.exclude` selected set** (rule 2 — *excluded / not-selected* reporting).

**That unknown/excluded half is shared, not per-key.** It lives in [`django_strawberry_framework/types/base.py::_selected_meta_targets`][base], which derives both name sets, routes the unknown path through the shared [`_format_unknown_fields_error`][base] (so the consumer-visible shape matches the [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] / [`Meta.optimizer_hints`][glossary-metaoptimizer_hints] typo guards), raises the caller's family-specific excluded message, and returns the `{name: field}` selected map plus the sorted target names. Every `Meta` key that targets a set of field names on the type validates through it — the two override keys here, `Meta.filesystem_path_fields`, and `Meta.relation_shapes` — and each caller keeps only its own per-name rules. Rules 3-5 below are this helper's per-name remainder, applied in the order listed: they operate on names the first two rules have already confirmed exist and are selected.

The full set of override failure modes (all raising [`ConfigurationError`][glossary-configurationerror] at type-creation time):

1. **Unknown field** — a name not on `model._meta` fields. (Mirrors the [`Meta.optimizer_hints`][glossary-metaoptimizer_hints] unknown-field guard.)
2. **Excluded field** — a name not in the selected set (excluded via [`Meta.exclude`][glossary-metaexclude] or otherwise unselected). The override targets a field that will not appear in the GraphQL type, so it is a configuration error, not a silent no-op.
3. **Consumer-authored field** — a name in `consumer_authored_fields`. A consumer-authored annotation or `strawberry.field` assignment already controls the field's nullability (it `continue`s past conversion entirely per [Scalar field override semantics][glossary-scalar-field-override-semantics]), so the override would be silently ignored; the package fails loud instead.
4. **Relay-Node-suppressed pk** — on a Relay-shaped type, the pk. Its nullability is the `relay.Node` interface's contract (`id: GlobalID!`), not the column's. It is checked **before** the relation rule, so a name that is both (a relation pk, e.g. `OneToOneField(primary_key=True)`, on a Relay type) is reported with the Relay reason.
5. **Relation field** — a name resolving to a relation field (non-relation scope per [Decision 10](#decision-10--non-relation-scope-relation-field-overrides-rejected-and-deferred)).
6. **Both-sets collision** — a name in `nullable_overrides ∩ required_overrides`. Contradictory; caught in stage 1 (shape-level normalization) above, naming the field and both keys.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 8][rationale-d8].

### Decision 9 — Choice-field interaction

A choice-backed column resolves to a generated enum (`EnumType`, or `EnumType | None` when nullable) per [Choice enum generation][glossary-choice-enum-generation]. The override applies to the enum exactly as it applies to a plain scalar, because the widening step in [`convert_scalar`][converters] runs **after** choice substitution. So `force_nullable=True` on a choice field yields `EnumType | None`; `force_nullable=False` yields `EnumType`. No choice-specific override logic is needed.

Rationale companion — this Decision's justification and its one rejected alternative: [Decision 9][rationale-d9].

### Decision 10 — Non-relation scope; relation-field overrides rejected and deferred

`Meta.nullable_overrides` / `Meta.required_overrides` apply to **non-relation model fields**: scalar columns and the file/image output objects. A name resolving to a relation field (forward FK / OneToOne, M2M, reverse FK / OneToOne / M2M) is rejected at type-creation time with [`ConfigurationError`][glossary-configurationerror].

The boundary is the annotation path, not the column's storage class. A non-relation field's annotation is produced by [`convert_field_output`][converters] — the one seam `force_nullable` threads through, whether the column resolves to a scalar or to a `DjangoFileType` / `DjangoImageType` output object. A relation field takes the `field.is_relation` branch in [`_build_annotations`][base] to `PendingRelation` / `resolved_relation_annotation`, a separate path the override does not reach, and the many-side's list-vs-element nullability ambiguity (`[T!]` vs `[T]!`) is a design question in its own right.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 10][rationale-d10].

### Decision 11 — Version bumps are owned by the joint `0.0.9` cut

**Decision: this card ships within `0.0.9` and does not edit package version fields.** The card shares the `0.0.9` patch line with its sibling cards — [`DONE-030-0.0.9`][kanban] ([`DjangoConnectionField`][glossary-djangoconnectionfield]), [`DONE-031-0.0.9`][kanban] (Django-model-based GlobalID encoding), [`DONE-032-0.0.9`][kanban] (the full Relay story), and [`DONE-033-0.0.9`][kanban] ([connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]). When multiple cards target one patch, the version bump belongs to the **joint cut**, not to any individual card's spec.

No slice in this card edits `pyproject.toml`, [`django_strawberry_framework/__init__.py::__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock`, and no slice promotes a [`CHANGELOG.md`][changelog] release heading. Each slice's bullets accumulate under `[Unreleased]` (Slice 1 a `### Changed` note; Slices 2 and 3 a `### Added` feature note) until the joint cut promotes them to `## [0.0.9]` under the maintainer's explicit version-bump command — the maintainer-commanded posture pinned in [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] Decision 10, extended to a shared-patch joint cut.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 11][rationale-d11].

### Decision 12 — Slice independence

The three functional slices are independent and ship in any order. Slice 1 has no foundation interaction (a construction-form rule over shipped surfaces); Slice 2 is a strict reader of the existing [`DjangoTypeDefinition`][definition]; Slice 3 plugs into [`_build_annotations`][base] / [`convert_scalar`][converters] at type-construction time with no finalizer change. None depends on another; the one cross-slice assertion is `test_inspect_reads_resolved_annotation_not_field_null`, a Slice 2 command test over the Slice 3 acceptance type.

Rationale companion — this Decision's justification and its one rejected alternative: [Decision 12][rationale-d12].

## Implementation plan

Where each slice lives:

| Slice | Source | Tests |
| --- | --- | --- |
| 1 — `extensions=` singleton-factory form | every optimizer construction site (`rg 'extensions=\['`); consumer snippets in [`docs/README.md`][docs-readme], [`docs/GLOSSARY.md`][glossary], [`GOAL.md`][goal], [`TODAY.md`][today], [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme]; [`examples/fakeshop/config/schema.py`][fakeshop-config-schema]; the [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension] module + class docstrings | [`tests/optimizer/test_extension.py::test_singleton_factory_extensions_form_emits_no_deprecation_warning`][test-extension]; [`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`][test-ci-governance]; the optimizer suite as the behavior-preserving guard |
| 2 — `inspect_django_type` command | [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd], [`django_strawberry_framework/management/commands/_imports.py`][commands-imports] | [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect], [`tests/management/test_inspect_django_type.py`][test-management-inspect] |
| 3 — `Meta.nullable_overrides` / `Meta.required_overrides` | [`django_strawberry_framework/types/base.py`][base] (`ALLOWED_META_KEYS`, `_ValidatedMeta` override slots, `_validate_meta` shape/normalize/collision, `_validate_nullability_override_targets` in `__init_subclass__`, `_build_annotations` `force_nullable`), [`django_strawberry_framework/types/converters.py`][converters] (`convert_scalar` and `convert_field_output` tri-state); [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] (acceptance type + root resolver; `BookType` primary) | [`tests/types/test_converters.py`][test-converters], [`tests/types/test_base.py`][test-types-base], [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] |

## Edge cases and constraints

- **A field in `nullable_overrides` that is already nullable** (`field.null is True`). The override is a no-op for the annotation (`force_nullable=True` produces `T | None`, which a nullable column already produced) but is NOT a configuration error — it is a legitimate (if redundant) declaration. Pinned as a passing case, not a raise.
- **A field in `required_overrides` that is already non-null** (`field.null is False`). Symmetric no-op; `force_nullable=False` produces `T`, which a non-null column already produced. Passing case, not a raise.
- **An override on a choice field** — applies to the generated enum (`EnumType | None` ↔ `EnumType`) per [Decision 9](#decision-9--choice-field-interaction). The enum members are unchanged.
- **An override on an `ArrayField`** — `force_nullable=True` produces `list[inner] | None`; `force_nullable=False` produces `list[inner]`. The *inner* element nullability follows `base_field.null` and is NOT affected by the outer override (the override controls only the outer field's nullability). Pinned by a `tests/types/test_converters.py` case.
- **An override on an `HStoreField`** — `JSON | None` ↔ `JSON`, same as the scalar branch.
- **An override on a `FileField` / `ImageField`.** The column resolves to the structured `DjangoFileType` / `DjangoImageType` output object, which is **nullable by default** whatever the column's `null` / `blank` says — the generated parent resolver returns `None` for an empty `FieldFile`, and an empty value is reachable even on `null=False, blank=False`. So `nullable_overrides` on such a column is the redundant-but-legal no-op case above, and `required_overrides` is the meaningful direction: it renders `DjangoFileType!` / `DjangoImageType!`, which is the same contract-not-data bargain the `required_overrides` bullet below describes — an empty stored file then trips the non-null violation at query time.
- **An override on the Relay-Node-suppressed pk** — the pk `continue`s past conversion (the Relay interface supplies `id: GlobalID!`), so naming `id` in an override set on a Relay-Node-shaped type targets a field that produces no annotation. Rejected by [Decision 8](#decision-8--override-validation-and-collision-behavior) rule 4 — the pk's nullability is the Relay interface's contract, not the column's.
- **An override naming a field absent from `Meta.fields`** (the type lists a subset and the override names a field not in it). Rejected per [Decision 8](#decision-8--override-validation-and-collision-behavior) rule 2 — the field is not in the selected set.
- **`Meta.nullable_overrides` and `Meta.required_overrides` declared as a non-sequence** (e.g. a bare string `"name"`, which is an iterable of characters). Rejected with [`ConfigurationError`][glossary-configurationerror] by the same normalizer the [`Meta.exclude`][glossary-metaexclude] guard uses, [`django_strawberry_framework/types/base.py::_normalize_sequence_spec`][base], which names the key the consumer actually wrote. It accepts any non-string sequence or set — every key routed through it is a *set* of field names whose declaration order carries no meaning — and refuses a `str`, which would silently read one field name as a sequence of single-character names. A non-`str` **entry** is rejected separately, naming the offending value.
- **A secondary [`Meta.primary`][glossary-metaprimary]`= False` `DjangoType` with overrides** (the Slice 3 acceptance type's shape). The override applies to the secondary type's annotation exactly as it does to the primary's; the two types flip nullability on the same column independently (each produces its own `cls.__annotations__`). The multi-type registry rule applies — exactly one type per model is primary — so the acceptance type on `Book` requires `BookType` to carry `Meta.primary = True`. Relation targets resolve to the primary; the secondary stays reverse-discoverable via `registry.model_for_type(...)`.
- **`required_overrides` changes the GraphQL contract, not the data.** Declaring `required_overrides = ("x",)` renders `x` as `T!` but does NOT alter the Django column (`null=True` stays) or sanitize runtime values: a resolver that returns a row with `x is None` hits a Strawberry non-null violation at query time. The consumer must guarantee the invariant at the resolver boundary (e.g. `.exclude(x__isnull=True)`), exactly as for any non-null GraphQL field backed by nullable storage — the Slice 3 acceptance resolver does this with `Book.objects.exclude(subtitle__isnull=True)`. (Symmetrically, `nullable_overrides` is always safe — widening a column to `T | None` never violates a non-null contract.)
- **`inspect_django_type` against a type whose override flipped a column.** The command reads the resolved annotation from `origin.__annotations__` (per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)), so its reported nullability reflects the post-override result — NOT the column-native `field.null` that a re-run of `convert_scalar` would reproduce.
- **`inspect_django_type` against an abstract / intermediate base `DjangoType` with no `Meta`.** Such a class never registers and has no `__django_strawberry_definition__`; the command raises `CommandError` ("not a registered DjangoType") — a **distinct branch** from the concrete-but-unfinalized case (`definition.finalized is False` → "`finalize_django_types()` has not run"), per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution).
- **`inspect_django_type` against a relation pk on a Relay type** (`OneToOneField(primary_key=True)`, an MTI parent link). The pk is not suppressed, so its row is the relation row, not the interface's `GlobalID!` (per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)).
- **The singleton-factory under the fakeshop schema-reload fixture.** Each reload re-evaluates the module-level `_optimizer = DjangoOptimizerExtension()` and `extensions=[lambda: _optimizer]`, constructing a fresh singleton (and a fresh empty plan cache) per reload; no captured state leaks across reloads. *Within* a reload, `get_extensions` returns the same `_optimizer` on every operation, so the cache works (per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)).

## Test plan

Tests live across the package-internal `tests/` tree and the two `examples/fakeshop/` trees, per [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Coverage that can be earned by a real GraphQL query or a real `call_command` is earned there first.

### Slice 1 — singleton-factory form

The singleton-factory shares one instance per construction site exactly as the instance form does, so the optimizer suite ([`tests/optimizer/test_extension.py`][test-extension] etc.) is the regression guard — it exercises the [Plan cache][glossary-plan-cache] through each site's shared instance. Two rows pin the form itself:

- [`tests/optimizer/test_extension.py::test_singleton_factory_extensions_form_emits_no_deprecation_warning`][test-extension] constructs one singleton-factory schema under `warnings.catch_warnings(record=True)` (with `warnings.simplefilter("always")` inside the context, so a previously-emitted `DeprecationWarning` that Python would otherwise dedupe cannot produce a false green) and asserts no `DeprecationWarning` mentioning an extension instance is emitted.
- [`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`][test-ci-governance] reports zero bare-class or constructing-lambda entries across its corpus (see the [Slice checklist](#slice-checklist)).

### Slice 2 — `inspect_django_type`

- [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] — in-process `call_command` against the shipped fakeshop schema. **Bare-name resolution needs a finalized registry, which is order-dependent unless forced** (a test could pass after another test imported `config.schema` and fail when run alone), so the bare-name tests use a fixture that **clears the global registry and rebuilds the full project schema** through `schema_reload.reload_all_project_schemas` (per [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme]), so running a test alone behaves identically to running it after a sibling:
  - `test_inspect_by_registered_name` — `call_command("inspect_django_type", "BookType")`; assert the pk `id` → `GlobalID!` / "relay.Node id" (`BookType` is Relay-Node-shaped), `title` → `String!` with converter `SCALAR_MAP[TextField]` (the matched MRO ancestor), `subtitle` → `String`, `circulation_status` → choice enum, `genres` → `[GenreType!]!`. Assert `title` and `subtitle` **per row**, not against the whole capture: `String` is a substring of `String!`, so a whole-text assertion cannot fail when the flip is wrong.
  - `test_inspect_by_meta_name` — a bare argument that is a type's **SDL** name rather than its Python `__name__` (`PublicPatronType` declaring `Meta.name = "PublicPatron"`) resolves, and the table is **titled** with that SDL name; the Python class name still resolves to the same title.
  - `test_inspect_by_dotted_path` — `call_command("inspect_django_type", "apps.library.schema.BookType")`; pins the dotted `import_string` branch.
  - `test_inspect_with_schema_option` (**cold path**, parametrized over `config.schema` and `config.schema:schema`) — proves `--schema` performs registration + finalization on its own. **An in-process `registry.clear()` alone is NOT a cold start:** if `config.schema` (or the app schema modules) are already in `sys.modules`, `import_module_symbol` returns the **cached** symbol without re-executing module load, so class registration and `finalize_django_types()` do **not** re-run. The test evicts `config.schema` and every app schema module from `sys.modules` and clears the registry before the in-process `call_command`, so the `--schema` import re-executes registration + finalize, and restores the full project schema on teardown. The **production command only imports `--schema`** — arranging the cold state is the harness's responsibility.
  - `test_inspect_choice_field_row` — the `circulation_status` row reports the generated `BookTypeCirculationStatusEnum` and "choice enum".
  - `test_inspect_relation_field_rows` — per row: `shelf` → `ShelfType!` (forward FK), `genres` → `[GenreType!]!` (M2M), `loans` → `[LoanType!]!` (reverse FK).
  - `test_inspect_consumer_authored_relation_field` / `test_inspect_consumer_authored_scalar_override_matrix` — the consumer-authored read source over live types (`BranchType.shelves`; `OverriddenScalarSpecimenType` across the four-corner override matrix): the row comes from the finalized Strawberry field metadata, so an assigned relation reports its resolved type rather than the `StrawberryAnnotation` `origin.__annotations__` holds for it, and the converter column names the consumer source rather than `SCALAR_MAP`.
  - `test_inspect_bigint_field_rows_use_package_scalar_name` — without `--schema`, a package-defined scalar row prints the name `strawberry_config()` registers, not a hand-copied literal.
  - `test_inspect_relay_node_pk_row` — `call_command("inspect_django_type", "GenreType")`; the `id` row reports `GlobalID!` and "relay.Node id", sourced from the interface — pins [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)'s suppressed-pk contract and guards the `KeyError` the naive `origin.__annotations__[pk_name]` read would raise.
  - `test_inspect_reads_resolved_annotation_not_field_null` — against the Slice 3 `NullabilityOverrideBookType` acceptance type: `title` reports `String` (post-`nullable_overrides`) and `subtitle` reports `String!` (post-`required_overrides`), proving the command reads `origin.__annotations__` and not a `convert_scalar` re-run.
  - `test_inspect_connection_only_relation_shape_renders_row` (bare and dotted) — `PeriodicalType.issues`, whose list annotation the synthesizer popped, renders from the `issues_connection` sibling as `IssueTypeConnection!` with a "(connection-only)" converter.
  - `test_inspect_file_and_image_rows_name_output_converters` — over `MediaSpecimenType` / `MediaSpecimenWithPathType`, the file and image rows name `convert_field_output -> DjangoFileType` / `DjangoImageType`, never `SCALAR_MAP`.
  - Failure modes the shipped schema can show: `test_bad_dotted_path_raises_command_error` (an unimportable argument raises with the original error); `test_malformed_dotted_path_raises_command_error` / `test_malformed_schema_selector_raises_command_error` (an empty or relative module path in the positional argument or `--schema` is rejected by `_validate_absolute_module_path` before any import runs); `test_bad_schema_selector_raises_command_error`; `test_unregistered_bare_name_raises_command_error` (a bare name with no match raises, naming `--schema` and the dotted form as the fixes); `test_non_djangotype_symbol_raises_command_error` (a dotted path resolving to a non-`DjangoType` symbol).
- [`tests/management/test_inspect_django_type.py`][test-management-inspect] — the branches that need a throwaway type:
  - `test_ambiguous_bare_name_lists_copyable_dotted_paths` — two registered `DjangoType`s colliding on a bare-name surface make the lookup raise `CommandError` listing both candidates as copyable `module.qualname` paths with their models.
  - `test_bare_name_meta_name_collision_with_python_name_is_ambiguous` — the collision is across surfaces too: one type's `Meta.name` equal to another type's class `__name__` is ambiguous, not first-match.
  - `test_abstract_base_without_definition_raises_command_error` — a `DjangoType` subclass with no `Meta` (no `__django_strawberry_definition__`) raises "not a registered DjangoType".
  - `test_unfinalized_type_raises_command_error` — a concrete registered `DjangoType` with `definition.finalized is False` raises "`finalize_django_types()` has not run" — a distinct branch from the no-definition case.
  - `test_inspect_unresolved_forward_ref_relation_raises_command_error` — a consumer-authored forward reference finalization could not resolve raises rather than printing Strawberry's `UNRESOLVED` sentinel.
  - `test_inspect_one_to_one_pk_on_relay_type_reports_relation_row` / `test_inspect_mti_parent_link_pk_on_relay_type_reports_relation_row` — a relation pk on a Relay type renders as its relation row, not `GlobalID!`; `test_inspect_direct_relay_node_inheritance_suppresses_pk_row` covers the `class Foo(DjangoType, relay.Node)` shape.
  - Naming and rendering branches with no fakeshop host: the SDL-name resolution and titling group (`test_bare_name_resolves_converter_applied_sdl_name_and_titles_it`, `test_sdl_type_name_ignores_inherited_strawberry_definition`, `test_inspect_uses_sdl_names_for_renamed_relation_and_consumer_enum`, `test_schema_option_uses_schema_naming_configuration`, `test_schema_help_documents_naming_and_cold_process_requirements`); the converter-naming group (`test_matched_scalar_key_names_supported_mro_ancestor`, `test_scalar_name_uses_custom_scalar_definition_name`, `test_scalar_name_uses_named_union_metadata`, `test_scalar_name_falls_back_to_dunder_name_for_definitionless_type`); and `test_render_annotation_renders_multi_member_union`.

### Slice 3 — `Meta.nullable_overrides` / `Meta.required_overrides`

- [`tests/types/test_converters.py`][test-converters] — the `force_nullable` tri-state:
  - `test_convert_scalar_force_nullable_true_widens_non_null_column` — a non-null `TextField` with `force_nullable=True` returns `str | None`.
  - `test_convert_scalar_force_nullable_false_narrows_nullable_column` — a nullable `TextField` with `force_nullable=False` returns `str`.
  - `test_convert_scalar_force_nullable_none_honors_field_null` — the default `None` reproduces the `field.null`-driven behavior.
  - `test_convert_scalar_force_nullable_on_choice_field` — a choice field with `force_nullable=True` returns `EnumType | None`; with `False`, `EnumType`.
  - `test_convert_scalar_force_nullable_on_array_field` — `list[inner] | None` ↔ `list[inner]`; inner element nullability unchanged.
  - `test_convert_scalar_force_nullable_on_hstore_field` — `JSON | None` ↔ `JSON`.
  - `test_convert_field_output_force_nullable_overrides_default` — the file output object's default-nullable annotation yields to an explicit `force_nullable`.
- [`tests/types/test_base.py`][test-types-base] — validation + collision + override-applies:
  - `test_nullable_overrides_in_allowed_meta_keys` — `"nullable_overrides"` and `"required_overrides"` are in [`ALLOWED_META_KEYS`][base] and NOT in [`DEFERRED_META_KEYS`][base] (pins [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)).
  - `test_nullable_override_flips_annotation` — a `DjangoType` with `nullable_overrides = ("text_value",)` on a non-null column produces a `str | None` annotation; `required_overrides = ("note",)` on a nullable column produces `str`.
  - `test_override_flips_choice_field_enum_nullability` — an override flips a choice field's **generated enum** nullability end-to-end through `Meta` (the enum members are untouched in both directions). Pins [Decision 9](#decision-9--choice-field-interaction).
  - `test_override_unknown_field_raises` — a name not on the model raises [`ConfigurationError`][glossary-configurationerror].
  - `test_override_excluded_field_raises` — a name excluded via [`Meta.exclude`][glossary-metaexclude] raises.
  - `test_override_consumer_authored_field_raises` — a name with a consumer annotation / `strawberry.field` assignment raises.
  - `test_override_relation_field_raises` — a relation field name raises (non-relation scope, [Decision 10](#decision-10--non-relation-scope-relation-field-overrides-rejected-and-deferred)).
  - `test_override_relay_suppressed_pk_raises` — the Relay-Node-suppressed pk named on a Relay-shaped type raises.
  - `test_override_both_sets_collision_raises` — a name in both sets raises.
  - `test_override_non_sequence_raises` — a bare string is rejected by the shape guard.
  - `test_override_redundant_is_no_op` — `nullable_overrides` on an already-nullable column (and `required_overrides` on an already-non-null column) is accepted.
  - `test_meta_required_overrides_forces_non_null_file_output` / `test_meta_required_overrides_forces_non_null_image_output` / `test_meta_nullable_overrides_on_a_file_column_is_a_no_op` — the file/image direction of the override (per [Edge cases](#edge-cases-and-constraints)).
- Live HTTP coverage in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] against the acceptance-only `NullabilityOverrideBookType` secondary type on `library.Book` (per the [Slice checklist](#slice-checklist)):
  - `test_nullability_override_flips_sdl_nullability` — a `__type(name: "NullabilityOverrideBookType")` introspection query asserts `title` renders `String` (flipped from the `NOT NULL` column's native `String!` via `nullable_overrides`) AND `subtitle` renders `String!` (flipped from the `null=True` column's native `String` via `required_overrides`), while `Book._meta.get_field("title").null` / `...("subtitle").null` are unchanged.
  - `test_nullability_override_acceptance_api_is_queryable` — creates a `Book` with a non-null `subtitle`, then queries `allLibraryNullabilityOverrideBooks { title subtitle }` and asserts **no `errors`** and exactly that row (the resolver's `exclude(subtitle__isnull=True).order_by("id")` keeps the `subtitle = String!` invariant true at the boundary). Without this, the SDL test alone could pass while the API is broken — a `subtitle=None` row would surface a non-null violation.

## Doc updates

Where each surface is documented:

- **Slice 1** — the singleton-factory snippets in [`docs/README.md`][docs-readme], [`docs/GLOSSARY.md`][glossary], [`GOAL.md`][goal], and [`TODAY.md`][today] (the [`docs/README.md`][docs-readme] one carries the "preserves the instance-bound [Plan cache][glossary-plan-cache], no deprecation warning" rationale); [`CHANGELOG.md`][changelog] `## [0.0.9]` `### Changed`.
- **Slice 2** — the [Schema introspection management command][glossary-schema-introspection-management-command] glossary entry beside the [Schema export management command][glossary-schema-export-management-command]; [`docs/TREE.md`][tree] (`inspect_django_type.py` and both test modules); [`docs/README.md`][docs-readme]; [`CHANGELOG.md`][changelog] `## [0.0.9]` `### Added`.
- **Slice 3** — the [`Meta.nullable_overrides`][glossary-metanullable_overrides] and [`Meta.required_overrides`][glossary-metarequired_overrides] glossary entries (cross-referencing [Scalar field conversion][glossary-scalar-field-conversion] / [Scalar field override semantics][glossary-scalar-field-override-semantics]); [`TODAY.md`][today]'s type-configuration list; [`CHANGELOG.md`][changelog] `## [0.0.9]` `### Added`.

## Risks and open questions

Every question this card opened is answered by a Decision above. One maintenance rule stays here:

- **Decision 3's mechanism is Strawberry's, so a Strawberry change can move it.** The extension-lifecycle claims in [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) are read from Strawberry's `Schema.get_extensions` and `Schema.__init__` in the `uv.lock`-resolved release; `pyproject.toml` declares a `strawberry-graphql` floor, so the *mechanism* can drift across the supported range even where the conclusion holds. A supported version that stops calling the `extensions=` factory per operation, or stops passing an instance through, requires Decision 3 to be re-derived by executing against that version — never read forward from this document, and never inferred from a changelog.

## Out of scope (explicitly tracked elsewhere)

- **Relation-field nullability override** — deferred (no card yet); the forward single-valued case is the natural follow-up, the many-side list-vs-element case is its own design ([Decision 10](#decision-10--non-relation-scope-relation-field-overrides-rejected-and-deferred)).
- **`DjangoConnectionField`** ([`DjangoConnectionField`][glossary-djangoconnectionfield]) — [`DONE-030-0.0.9`][kanban]. Its schema-construction examples use the same singleton-factory form; the connection field itself is out of scope.
- **Full Relay story** ([`DONE-032-0.0.9`][kanban]) and **connection-aware optimizer planning** ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning], [`DONE-033-0.0.9`][kanban]) — the rest of the `0.0.9` cohort, sharing the joint cut that owns the version bump (per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).
- **`Meta.fields_class`** ([`FieldSet`][glossary-fieldset], [`Meta.fields_class`][glossary-metafields_class]) — `0.1.1`. Field-level resolver / redaction sidecar; orthogonal to nullability override (resolve-time gate vs construction-time annotation).
- **`Meta.search_fields`** ([`Meta.search_fields`][glossary-metasearch_fields]) — `0.1.2`.
- **`AggregateSet`** ([`AggregateSet`][glossary-aggregateset], [`Meta.aggregate_class`][glossary-metaaggregate_class]) — `0.1.3`.
- **Permissions cascade** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions]) — `0.0.10`.
- **Relocating the `DjangoOptimizerExtension` plan cache off the instance** — not needed: the singleton-factory ([Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)) preserves the instance-bound cache without it. It remains a possible future optimizer refactor (e.g. if a Strawberry version stops honoring the factory-per-operation contract).
- **A `--json` / `--watch` mode on `inspect_django_type`** — not planned; the command prints a single human-readable table.
- **Persisting overrides on `DjangoTypeDefinition`** — not needed; the override resolves to a final annotation on `cls.__annotations__` at construction time, which is the authoritative record the inspect command reads ([Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar) / [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)).
- **Version bump** — owned by the joint `0.0.9` cut ([Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Definition of done

The completion contract, grouped by slice.

**Spec + companion CSV**

1. [`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv`][spec-029-terms] anchoring every project-specific term that has a [`docs/GLOSSARY.md`][glossary] heading; [`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`][check-spec-glossary] reports `OK: <N> terms`. The card's three public symbols are among them: `Meta.nullable_overrides`, `Meta.required_overrides`, and the [Schema introspection management command][glossary-schema-introspection-management-command] each carry a glossary heading and a CSV row. A term whose heading does not exist cannot be in the CSV without failing the checker, so heading and row land together.

**Slice 1 — `extensions=` singleton-factory form**

2. Every optimizer `extensions=` entry — across the package test schemas, the example `config/schema.py`, and the consumer docs, subclass instances such as the `_CaptureExt()` sites in [`tests/optimizer/test_extension.py`][test-extension] included — is a singleton-factory `extensions=[lambda: <instance>]` per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form): **function-local** where a test asserts on the instance's `cache_info()` or needs a per-site `strictness=`, module-level where there is one schema per module, preserving the instance-bound [Plan cache][glossary-plan-cache]. The population is whatever `rg 'extensions=\['` reports; it is not a fixed count.
3. The consumer-doc snippets in [`docs/README.md`][docs-readme] and [`docs/GLOSSARY.md`][glossary], [`examples/fakeshop/config/schema.py`][fakeshop-config-schema], [`TODAY.md`][today], and [`GOAL.md`][goal]'s astronomy schema show the singleton-factory form, so the north-star recipe shows the optimized boundary.
4. Strawberry's instance-form `DeprecationWarning` does not fire for any of them (the `extensions` entries are callables, not instances), pinned by [`tests/optimizer/test_extension.py::test_singleton_factory_extensions_form_emits_no_deprecation_warning`][test-extension]; and the two cold-cache forms are held out of active first-party source by a **standing test**, not by a one-shot sweep — [`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`][test-ci-governance] classifies every `extensions=` sequence entry by **form** and reports zero violations. Enforcing by form rather than by a list of spellings is the contract: the bare class `extensions=[DjangoOptimizerExtension]` and **any** constructing lambda `extensions=[lambda: DjangoOptimizerExtension(...)]` are both violations however they are spelled, keyword-carrying variants included, and a gate written against a spelling list cannot see the variants. The instance forms need no entry in that gate — Strawberry's `DeprecationWarning` meets `pytest.ini`'s `filterwarnings = error`, so any of them fails the suite where it stands. The gate's corpus is the four [`scripts/check_citations.py`][check-citations] `SOURCE_TREES` plus the tracked `.py` files outside them that the pin's own [`tests/test_ci_governance.py::EXTRA_SOURCE_FILES`][test-ci-governance] carries back, with the gitignored `docs/*/temp-tests/` scratch excluded by construction. [`CHANGELOG.md`][changelog] `## [0.0.9]` carries the `### Changed` bullet.

**Slice 2 — `inspect_django_type`**

5. [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] ships with module + class docstring, `add_arguments` registering a positional `type` argument plus `--schema <selector>`, and `handle` resolving the `type` argument **by shape** (a dotted argument via `import_string`, raising `CommandError` with the original error on import failure — never masked by a registry fallback; a bare name via a unique registry match on the SDL name or the Python `__name__`) with `--schema` loaded via `import_module_symbol(..., default_symbol_name="schema")` and its `config` read for the scalar map and name converter, both loaders routed through the shared [`_imports.py`][commands-imports] helpers that pre-validate the module path and translate import failures, reading the GraphQL type + nullability from the **authoritative post-finalize record for that field's origin** (`origin.__annotations__` for auto-synthesized fields, `origin.__strawberry_definition__` for consumer-authored ones and for a connection-only relation's synthesized sibling, the interface for a Relay-suppressed non-relation pk) and `definition.selected_fields` / `field_map` for Django-side metadata + converter classification, and printing the per-field resolution table per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution).
6. `CommandError` is raised for: a **malformed** dotted path or `--schema` selector (empty or relative module path, rejected before any import); an unresolvable argument; an **ambiguous bare name** (≥2 registered types collide on the SDL name or the Python `__name__`, listed as copyable dotted paths); a non-`DjangoType` resolved symbol; a `DjangoType` with **no `__django_strawberry_definition__`** (abstract / no-`Meta` base); a `DjangoType` whose **`definition.finalized is False`** — those last two are distinct branches per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution); and an **unresolved forward reference** on a consumer-authored field (Strawberry's `UNRESOLVED` sentinel), raised rather than printed.
7. [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] covers the paths reachable through the shipped schema via `call_command` — bare-name tests under a registry-clear + full-project-reload fixture (order-independent), plus a cold-path `--schema` test over both the `config.schema` and `config.schema:schema` selector forms proving `--schema` finalizes on its own — and [`tests/management/test_inspect_django_type.py`][test-management-inspect] covers the branches that need a throwaway type, per the [Test plan](#test-plan).
8. [`docs/GLOSSARY.md`][glossary] carries the command entry; [`docs/TREE.md`][tree] lists the module + both test modules; [`CHANGELOG.md`][changelog] `## [0.0.9]` carries the `### Added` bullet.

**Slice 3 — `Meta.nullable_overrides` / `Meta.required_overrides`**

9. [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] contains `"nullable_overrides"` and `"required_overrides"`; neither is in [`DEFERRED_META_KEYS`][base] (net-new keys per [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)).
10. [`django_strawberry_framework/types/converters.py::convert_scalar`][converters] accepts the keyword-only `force_nullable: bool | None = None` tri-state per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar); the widening decision is computed once from `effective_null` and applied uniformly across the `ArrayField` / `HStoreField` / choice / scalar branches; the `None` default reproduces the column-native behavior. The read-output entry point [`convert_field_output`][converters] carries the same keyword-only tri-state, applying it to a file/image output object's default-nullable annotation and threading it into `convert_scalar` unchanged for every other column.
11. The override validation is staged per [Decision 8](#decision-8--override-validation-and-collision-behavior): [`_validate_meta`][base] shape-checks both keys through the shared [`_normalize_sequence_spec`][base], normalizes them onto `_ValidatedMeta`, and raises the both-sets collision; [`_validate_nullability_override_targets`][base] runs in [`__init_subclass__`][base] (after `_select_fields` + `consumer_authored_fields` + the Relay-shape check), keyword-only and taking `relay_shaped: bool`, and raises [`ConfigurationError`][glossary-configurationerror] for unknown / excluded / consumer-authored / Relay-pk / relation targets in that order — deriving **two distinct sets** (`model._meta.get_fields()` names for *unknown*, the post-`Meta.fields`/`exclude` selected set for *excluded*) as separate error paths so the `Meta.exclude` contract isn't collapsed into "unknown", through the shared [`_selected_meta_targets`][base] + [`_format_unknown_fields_error`][base] every set-of-field-names `Meta` key validates through; [`_build_annotations`][base] receives the normalized override frozensets and passes `force_nullable` per field to [`convert_field_output`][converters].
12. [`tests/types/test_converters.py`][test-converters] (tri-state across scalar / nullable / choice / Array / HStore, plus the file output object) and [`tests/types/test_base.py`][test-types-base] (validation + collision + override-applies + `ALLOWED_META_KEYS` membership + file/image overrides) cover the slice per the [Test plan](#test-plan).
13. A dedicated acceptance-only `NullabilityOverrideBookType` secondary type on `library.Book` (`Meta.primary = False`; `BookType` carries `Meta.primary = True`) lives in [`apps/library/schema.py`][fakeshop-library-schema] with a dedicated root resolver that returns `Book.objects.exclude(subtitle__isnull=True).order_by("id")` (so the `subtitle = String!` invariant holds at the boundary and rows are deterministically ordered). Two live HTTP tests in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]: an **SDL** test asserting `title` flips `String!` → `String` and `subtitle` flips `String` → `String!` while the `Book` columns are unchanged, and a **data-query** test requesting `{ title subtitle }` over non-null-subtitle rows asserting no `errors`. The existing `BookType` and the `scalars` app's types / assertions are untouched.
14. [`docs/GLOSSARY.md`][glossary] carries the `Meta.nullable_overrides` / `Meta.required_overrides` entries; [`CHANGELOG.md`][changelog] `## [0.0.9]` carries the `### Added` bullet.

**Card-completion wrap**

15. [`KANBAN.md`][kanban] records the card as [`DONE-029-0.0.9`][kanban] with the card body's spec reference pointing at [`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029].
16. **No version bump lands in this card** per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut): `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` are untouched by its slices; the joint `0.0.9` cut promotes the CHANGELOG release heading.
17. Package coverage stays at 100% (`fail_under = 100`).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[start]: ../../START.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-aggregateset]: ../GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-cross-subsystem-invariants]: ../GLOSSARY.md#cross-subsystem-invariants
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-django-appconfig]: ../GLOSSARY.md#django-appconfig
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fieldset]: ../GLOSSARY.md#fieldset
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-metaaggregate_class]: ../GLOSSARY.md#metaaggregate_class
[glossary-metachoice_enum_names]: ../GLOSSARY.md#metachoice_enum_names
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metafields_class]: ../GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: ../GLOSSARY.md#metafilterset_class
[glossary-metainterfaces]: ../GLOSSARY.md#metainterfaces
[glossary-metanullable_overrides]: ../GLOSSARY.md#metanullable_overrides
[glossary-metaoptimizer_hints]: ../GLOSSARY.md#metaoptimizer_hints
[glossary-metaorderset_class]: ../GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-metarequired_overrides]: ../GLOSSARY.md#metarequired_overrides
[glossary-metasearch_fields]: ../GLOSSARY.md#metasearch_fields
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-relatedaggregate]: ../GLOSSARY.md#relatedaggregate
[glossary-relatedfilter]: ../GLOSSARY.md#relatedfilter
[glossary-relatedorder]: ../GLOSSARY.md#relatedorder
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[glossary-scalar-field-override-semantics]: ../GLOSSARY.md#scalar-field-override-semantics
[glossary-schema-export-management-command]: ../GLOSSARY.md#schema-export-management-command
[glossary-schema-introspection-management-command]: ../GLOSSARY.md#schema-introspection-management-command
[glossary-specialized-scalar-conversions]: ../GLOSSARY.md#specialized-scalar-conversions
[glossary-strawberry-config]: ../GLOSSARY.md#strawberry_config
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

[next]: NEXT.md
[rationale-d10]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md#decision-10--non-relation-scope-relation-field-overrides-rejected-and-deferred
[rationale-d11]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md#decision-11--version-bumps-are-owned-by-the-joint-009-cut
[rationale-d12]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md#decision-12--slice-independence
[rationale-d1]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md#decision-2--one-spec-covers-all-three-slices
[rationale-d3]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md#decision-3--slice-1-adopts-the-singleton-factory-extensions-form
[rationale-d4]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md#decision-4--inspect_django_type-command-shape-and-argument-resolution
[rationale-d5]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md#decision-5--two-key-tuple-set-override-form
[rationale-d6]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion
[rationale-d7]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md#decision-7--tri-state-force_nullable-threaded-through-convert_scalar
[rationale-d8]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md#decision-8--override-validation-and-collision-behavior
[rationale-d9]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md#decision-9--choice-field-interaction
[spec-015]: spec-015-relay_interfaces-0_0_5.md
[spec-019]: spec-019-consumer_overrides_scalar-0_0_6.md
[spec-022]: spec-022-export_schema-0_0_7.md
[spec-027]: spec-027-filters-0_0_8.md
[spec-028]: spec-028-orders-0_0_8.md
[spec-029-rationale]: appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md
[spec-029-terms]: appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv
[spec-029]: spec-029-consumer_dx_cleanup-0_0_9.md
[spec-037]: spec-037-upload_file_image_mapping-0_0_11.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/types/base.py
[commands-imports]: ../../django_strawberry_framework/management/commands/_imports.py
[converters]: ../../django_strawberry_framework/types/converters.py
[definition]: ../../django_strawberry_framework/types/definition.py
[export-schema-cmd]: ../../django_strawberry_framework/management/commands/export_schema.py
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[inspect-cmd]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[operation-state]: ../../django_strawberry_framework/extensions/operation_state.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[package-init]: ../../django_strawberry_framework/__init__.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-ci-governance]: ../../tests/test_ci_governance.py
[test-converters]: ../../tests/types/test_converters.py
[test-extension]: ../../tests/optimizer/test_extension.py
[test-management-export]: ../../tests/management/test_export_schema.py
[test-management-inspect]: ../../tests/management/test_inspect_django_type.py
[test-types-base]: ../../tests/types/test_base.py

<!-- examples/ -->
[fakeshop-config-schema]: ../../examples/fakeshop/config/schema.py
[fakeshop-library-models]: ../../examples/fakeshop/apps/library/models.py
[fakeshop-library-schema]: ../../examples/fakeshop/apps/library/schema.py
[fakeshop-scalars-models]: ../../examples/fakeshop/apps/scalars/models.py
[fakeshop-test-library]: ../../examples/fakeshop/test_query/test_library_api.py
[fakeshop-test-multi-db]: ../../examples/fakeshop/test_query/test_multi_db.py
[fakeshop-test-query-readme]: ../../examples/fakeshop/test_query/README.md
[fakeshop-tests-export]: ../../examples/fakeshop/tests/test_export_schema.py
[fakeshop-tests-inspect]: ../../examples/fakeshop/tests/test_inspect_django_type.py

<!-- scripts/ -->
[check-citations]: ../../scripts/check_citations.py
[check-spec-glossary]: ../../scripts/check_spec_glossary.py

<!-- .venv/ -->

<!-- External -->
[graphene-django]: https://github.com/graphql-python/graphene-django
[strawberry-django]: https://github.com/strawberry-graphql/strawberry-django
[upstream-cookbook]: https://github.com/riodw/django-graphene-filters
