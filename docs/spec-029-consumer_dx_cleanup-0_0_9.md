# Spec: `DjangoType` consumer-DX cleanup pass (`extensions=` migration, `inspect_django_type`, `Meta.nullable_overrides`)

Planned for `0.0.9` (card [`WIP-ALPHA-029-0.0.9`][kanban]). **This spec is an open build plan, not a shipped record.** The Status line below, the [Slice checklist](#slice-checklist) (unticked), and the [Definition of done](#definition-of-done) describe work that has not yet started; the [Current state](#current-state) section is a true description of the repo as of this writing. **Version boundary** (see [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)): this card shares the `0.0.9` patch line with three sibling WIP cards ([`WIP-ALPHA-030-0.0.9`][kanban], [`WIP-ALPHA-031-0.0.9`][kanban], [`WIP-ALPHA-032-0.0.9`][kanban]); the `pyproject.toml` / [`__version__`][package-init] / [`tests/base/test_init.py::test_version`][test-base-init] bump to `0.0.9` is owned by the **joint cut**, not by this card. This card's slices land within the `0.0.9` line and never bump the version themselves.

Status: planned — not yet implemented. Three independent slices that ship in any order (per the [`KANBAN.md`][kanban] card body's Planning note): Slice 1 (the `extensions=` factory-callable migration), Slice 2 (the `inspect_django_type` diagnostic command), and Slice 3 (the `Meta.nullable_overrides` / `Meta.required_overrides` GraphQL-layer nullability override). The card body counts as complete when all three slices land; if the schedule forces Slice 3 to defer, the slice carves off as its own follow-up card without disrupting Slices 1 + 2 (see [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)).

Owner: package maintainer.

Predecessors: [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] (the most-recently-shipped spec — the canonical voice / depth / section-layout reference for this document; its [Decision 10][spec-028] maintainer-commanded-version-bump posture is the precedent [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut) extends to a joint-cut boundary); [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] (the filter subsystem whose `_validate_filterset_class` validator at [`django_strawberry_framework/types/base.py::_validate_filterset_class`][base] is the structural template for Slice 3's `Meta`-key validation); [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] (the [Schema export management command][glossary-schema-export-management-command] whose [`Command`][export-schema-cmd] shape Slice 2's `inspect_django_type` command mirrors); [`docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019] (the [Scalar field override semantics][glossary-scalar-field-override-semantics] this card's Slice 3 must compose with — a consumer-authored annotation already controls a field's nullability and must not be silently re-overridden); [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-015] (the Relay-Node pk-suppression branch in [`_build_annotations`][base] that Slice 3's scalar-resolution path threads alongside). [`docs/GLOSSARY.md`][glossary] has **no entry yet** for `Meta.nullable_overrides`, `Meta.required_overrides`, or the `inspect_django_type` command; their entries are created during implementation (per [Doc updates](#doc-updates)) and are flagged in [Risks and open questions](#risks-and-open-questions) as the missing-glossary-heading caveat.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Pinned the canonical spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)) over the card body's stale `docs/spec-021-nullable_overrides-0_0_8.md` reference; the single-spec-covers-all-three-slices scope ([Decision 2](#decision-2--one-spec-covers-all-three-slices)); the `extensions=` instance→factory-callable migration shape ([Decision 3](#decision-3--instancefactory-callable-migration-shape)); the `inspect_django_type` command shape and argument-resolution contract ([Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)); the two-key tuple-set override form over a dict-of-name shape ([Decision 5](#decision-5--two-key-tuple-set-override-form)); the net-new `ALLOWED_META_KEYS` landing (NOT a `DEFERRED_META_KEYS` promotion) ([Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)); the tri-state `force_nullable` seam threaded through [`convert_scalar`][converters] ([Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)); the validation and collision behavior — `Meta.exclude` interaction, both-sets collision, consumer-authored interaction ([Decision 8](#decision-8--override-validation-and-collision-behavior)); the choice-field interaction ([Decision 9](#decision-9--choice-field-interaction)); the scalar-only scope with relation-field overrides rejected and deferred ([Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)); the joint-`0.0.9`-cut version-bump boundary ([Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)); and the slice-independence / Slice-3 carve-off contingency ([Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)). Conflicts called out in [Risks and open questions](#risks-and-open-questions): the card body's stale `spec-021-nullable_overrides-0_0_8` filename, its `## [0.0.8]` CHANGELOG-heading references, and its `examples/fakeshop/tests/test_commands.py` test path (no such file exists; the on-disk convention is one file per command).

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoType`][glossary-djangotype] — the model-backed Strawberry type all three slices touch. Slice 2 introspects its [`DjangoTypeDefinition`][definition]; Slice 3 adds two new `Meta` keys to its surface; Slice 1 migrates the `extensions=` snippet consumers copy when wiring it.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the schema extension whose instance-form construction (`extensions=[DjangoOptimizerExtension()]`) Slice 1 migrates to the factory-callable form Strawberry now recommends.
- [Strictness mode][glossary-strictness-mode] — the optimizer's `strictness` constructor argument; the reason Slice 1 needs the `lambda:` factory-callable form (not the bare class) for any construction site that passes constructor arguments.
- [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] — the existing field-selection keys whose tuple-of-names shape Slice 3's two new override keys mirror, and whose `_select_fields` filtering determines which fields an override may legally name.
- [Scalar field conversion][glossary-scalar-field-conversion] — the [`convert_scalar`][converters] path Slice 3 threads a nullability override into; the `if field.null: py_type = py_type | None` widening step is exactly what the override decouples from the Django column.
- [Choice enum generation][glossary-choice-enum-generation] — choice-backed columns resolve to a generated enum before null widening; [Decision 9](#decision-9--choice-field-interaction) confirms the override applies to `EnumType | None` the same way it applies to `str | None`.
- [Specialized scalar conversions][glossary-specialized-scalar-conversions] — the `ArrayField` / `HStoreField` early-return branches in `convert_scalar` plus the shared scalar path that [`BigInt`][glossary-bigint-scalar] (a `SCALAR_MAP` entry) flows through, each widening on `field.null`; [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar) makes the override apply at every one of those widening sites.
- [Scalar field override semantics][glossary-scalar-field-override-semantics] — the four-corner consumer-override matrix from `DONE-019-0.0.6`; a consumer-authored annotation or `strawberry.field(...)` assignment bypasses `convert_scalar` entirely, so [Decision 8](#decision-8--override-validation-and-collision-behavior) rejects naming a consumer-authored field in either override set.
- [`Meta.choice_enum_names`][glossary-metachoice_enum_names] — a sibling future `Meta` key referenced when reasoning about choice-field overrides; not implemented here.
- [`ConfigurationError`][glossary-configurationerror] — raised at type-creation time for every Slice 3 validation failure (unknown / excluded / consumer-authored / relation override-target, both-sets collision) and by Slice 2's command for a bad type path.
- [Relation handling][glossary-relation-handling] — the FK / OneToOne / M2M / reverse-relation cardinality mapping; [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred) scopes Slice 3's overrides to scalar columns and rejects relation-field override targets for `0.0.9`.
- [`finalize_django_types`][glossary-finalize_django_types] — the finalizer; Slice 3 needs **no** finalizer change (overrides apply at type-construction time in [`__init_subclass__`][base], before finalization) and Slice 2 is a strict reader of the post-finalize [`DjangoTypeDefinition`][definition].
- [Definition-order independence][glossary-definition-order-independence] — the invariant that keeps Slice 3 entirely inside type-construction; the override resolves a column's GraphQL nullability with zero dependency on relation-target import order.
- [Schema export management command][glossary-schema-export-management-command] — the shipped `manage.py export_schema` command at [`export_schema.py`][export-schema-cmd] whose `add_arguments` / `handle` / `CommandError` shape Slice 2's `inspect_django_type` command mirrors.
- [Django `AppConfig`][glossary-django-appconfig] — `DjangoStrawberryFrameworkConfig`; the management-command discovery path Slice 2's new command resolves through when consumers list `"django_strawberry_framework"` in `INSTALLED_APPS`.
- [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] — the two shipped sidecar keys whose `_validate_*_class` validators ([`base.py`][base]) are the structural template for Slice 3's `Meta`-key validation (a new `_validate_*` helper called from `_validate_meta`).
- [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] — the shipped Layer-3 subsystems; cited because Slice 3 does NOT follow their deferred-key promotion gate (its keys are net-new public `Meta` keys, not promotions — see [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)).
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — the deferred-`Meta`-key promotion rule lives here; [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion) explains why the rule does NOT apply to this card's net-new keys.

Dependency and forward-composition surfaces a reader will hit:

- [`DjangoConnectionField`][glossary-djangoconnectionfield] — the central read-side primitive being built by the sibling [`WIP-ALPHA-030-0.0.9`][kanban] card. The card body lists it as a dependency of Slice 1: the `extensions=` factory-callable migration should land before the connection field's new schema-construction surfaces ship, so consumers copy from a current pattern rather than a deprecated one.
- [`DjangoListField`][glossary-djangolistfield] — the shipped non-Relay list factory; cited because its [`get_queryset`][glossary-get_queryset-visibility-hook]-applying wrapper is one of the schema surfaces Slice 2's `inspect_django_type` introspection complements (it reports the resolved field table, not the resolver wiring).
- [`Meta.fields_class`][glossary-metafields_class] / [`FieldSet`][glossary-fieldset] — `0.1.1`; the field-level resolver / redaction sidecar. Orthogonal to Slice 3 (nullability override is a type-construction-time annotation rewrite; `FieldSet` is a resolve-time gate).
- [`Meta.search_fields`][glossary-metasearch_fields] (`0.1.2`) / [`Meta.aggregate_class`][glossary-metaaggregate_class] (`0.1.3`) — future Layer-3 sidecars, listed only as out-of-scope pointers.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package tests under `tests/` mirroring source; example-project non-HTTP tests under `examples/fakeshop/tests/`; live HTTP tests under `examples/fakeshop/test_query/`); the live-HTTP-priority coverage rule; the no-pytest-after-edits rule; the settings-keys rule; the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — each slice's doc-update step grants the explicit per-slice permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical (Slice 3's nullability flip) and through in-process `call_command` tests where the surface is a management command (Slice 2).
- [`docs/TREE.md`][tree] — tests mirror source one-to-one; Slice 2 adds [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] alongside the shipped `export_schema.py`.
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, all defs at the bottom under the 10 canonical group headers).

## Slice checklist

Each top-level item maps to one commit / PR. **Three independent functional slices plus a card-completion wrap** — the three functional slices ship in any order per the [`KANBAN.md`][kanban] Planning note. Boxes are unticked because the work has not started.

- [ ] Slice 1: `extensions=` factory-callable migration sweep
  - [ ] Replace every `strawberry.Schema(query=…, extensions=[DjangoOptimizerExtension()])` instance-form site with `extensions=[DjangoOptimizerExtension]` (bare class) per [Decision 3](#decision-3--instancefactory-callable-migration-shape). Any site that passes constructor arguments (e.g. `DjangoOptimizerExtension(strictness="raise")`) becomes `extensions=[lambda: DjangoOptimizerExtension(strictness="raise")]` (factory callable) instead — the bare class cannot carry constructor arguments.
  - [ ] Code sites: [`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection] (lines 51, 157), [`tests/test_list_field.py`][test-list-field] (lines 753, 886), [`tests/types/test_generic_foreign_key.py`][test-generic-fk] (line 102). [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] **already uses the class form** ([`config/schema.py`][fakeshop-config-schema] #"extensions=[DjangoOptimizerExtension]") — confirm, do not edit (the card's affected-files list is partly already-migrated; see [Decision 3](#decision-3--instancefactory-callable-migration-shape)).
  - [ ] Consumer-doc snippets: [`docs/README.md`][docs-readme] (the Quick start + Schema setup boundary snippets) and [`docs/GLOSSARY.md`][glossary] (the [`BigInt`][glossary-bigint-scalar] / [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] / [`finalize_django_types`][glossary-finalize_django_types] schema-construction snippets). [`GOAL.md`][goal] and [`TODAY.md`][today] carry **no** instance-form `extensions=` snippet today (TODAY already uses the class form; GOAL's astronomy `strawberry.Schema(...)` has no `extensions=` argument) — confirm, do not edit. The prose mention of `DjangoOptimizerExtension()` at [`docs/README.md`][docs-readme] #"walks the selected GraphQL fields once" describes the extension's behavior, not a construction site, and is rephrased only if it reads as a recommended construction form.
  - [ ] Repo-wide grep `grep -rn "DjangoOptimizerExtension()" .` confirms zero remaining instance-form construction sites (excluding prose and this spec's own quoted examples) before the slice closes.
  - [ ] [`CHANGELOG.md`][changelog]: append a `### Changed` bullet under `[Unreleased]` noting the migration to the factory-callable `extensions=` form. No version-heading promotion (per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).
- [ ] Slice 2: `inspect_django_type` diagnostic command
  - [ ] Ship [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] with module + class docstring, `add_arguments` registering a positional `type` argument, and `handle` printing the resolved per-field table per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution). The command resolves its argument as a dotted import path first, then falls back to a registry-name lookup; reads `target.__django_strawberry_definition__` (the [`DjangoTypeDefinition`][definition] populated by [`finalize_django_types`][glossary-finalize_django_types]); and prints, per selected field: Django field name → Django field type → resolved GraphQL scalar / type → nullability → which converter row fired ([`SCALAR_MAP`][converters] entry name, choice-enum, or relation converter).
  - [ ] `CommandError` for: an unresolvable type argument (neither a dotted path nor a registered type name), a resolved symbol that is not a [`DjangoType`][glossary-djangotype] subclass, and a `DjangoType` that has not been finalized (no `__django_strawberry_definition__`). Mirrors the [`export_schema.py`][export-schema-cmd] `CommandError` discipline.
  - [ ] Example happy-path coverage: [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (new) via `call_command("inspect_django_type", "PatronType")` against a real fakeshop [`DjangoType`][glossary-djangotype], asserting the printed table names every selected field with its resolved scalar and nullability. (The card body names `examples/fakeshop/tests/test_commands.py`; no such file exists — see the conflict note in [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) and [Risks and open questions](#risks-and-open-questions). The new file mirrors the existing one-file-per-command convention at [`examples/fakeshop/tests/test_export_schema.py`][fakeshop-tests-export].)
  - [ ] Package-internal failure-mode coverage: [`tests/management/test_inspect_django_type.py`][test-management-inspect] (new) for the `CommandError` paths not reachable from a live registered type (bad dotted path, non-`DjangoType` symbol, unfinalized type), mirroring [`tests/management/test_export_schema.py`][test-management-export].
  - [ ] [`docs/GLOSSARY.md`][glossary] adds a `## Schema introspection management command` (or `## inspect_django_type`) entry; [`docs/TREE.md`][tree] lists `inspect_django_type.py` under `management/commands/`. [`CHANGELOG.md`][changelog]: `### Added` bullet under `[Unreleased]`.
- [ ] Slice 3: `Meta.nullable_overrides` / `Meta.required_overrides`
  - [ ] [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] grows `"nullable_overrides"` and `"required_overrides"` (net-new public keys — NOT a `DEFERRED_META_KEYS` promotion, per [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)). A new `_validate_nullability_overrides(meta, selected_names, consumer_authored)` helper in [`base.py`][base] validates both sets and is called from [`_validate_meta`][base] / `__init_subclass__`'s field-selection pass.
  - [ ] [`django_strawberry_framework/types/converters.py::convert_scalar`][converters] grows a keyword-only `force_nullable: bool | None = None` tri-state per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar): `None` honors `field.null` (unchanged default); `True` emits `T | None` regardless; `False` emits `T` (non-null) regardless. The widening decision is computed once from `effective_null = field.null if force_nullable is None else force_nullable` and applied uniformly across the `ArrayField` / `HStoreField` / choice / scalar branches.
  - [ ] [`_build_annotations`][base]'s scalar branch ([`base.py`][base] #"annotations[field.name] = convert_scalar(field, cls.__name__)") computes `force_nullable` for each field from the two override sets (`True` if in `nullable_overrides`, `False` if in `required_overrides`, `None` otherwise) and passes it to `convert_scalar`.
  - [ ] Validation per [Decision 8](#decision-8--override-validation-and-collision-behavior): every name in both sets must (a) exist on the model, (b) be in the selected field set (not excluded via [`Meta.exclude`][glossary-metaexclude]), (c) NOT be consumer-authored (an annotation / `strawberry.field` override already controls nullability per [Scalar field override semantics][glossary-scalar-field-override-semantics]), and (d) NOT be a relation field (scalar-only scope per [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)). A field named in **both** sets raises [`ConfigurationError`][glossary-configurationerror] (contradictory). Every failure raises [`ConfigurationError`][glossary-configurationerror] at type-creation time naming the offending field.
  - [ ] Package coverage: [`tests/types/test_converters.py`][test-converters] (the `force_nullable` tri-state across scalar / nullable / choice / Array / HStore shapes) + [`tests/types/test_base.py`][test-types-base] (the validation + collision cases: unknown field, excluded field, consumer-authored field, relation field, both-sets collision, override-applies).
  - [ ] Live HTTP coverage: a test in [`examples/fakeshop/test_query/`][fakeshop-test-library] (the [`scalars`][fakeshop-scalars-models] or [`library`][fakeshop-library-models] app) demonstrating the override flipping a real model field's GraphQL nullability — a non-null column rendered nullable (`T!` → `T`) via `nullable_overrides`, and a nullable column rendered non-null (`T` → `T!`) via `required_overrides` — verified by introspecting the SDL field type, without touching the model column.
  - [ ] [`docs/GLOSSARY.md`][glossary] adds `## Meta.nullable_overrides` and `## Meta.required_overrides` entries; [`CHANGELOG.md`][changelog]: `### Added` bullet under `[Unreleased]`.
- [ ] Card-completion wrap (lands when all three slices ship; NOT a code slice)
  - [ ] [`KANBAN.md`][kanban]: move [`WIP-ALPHA-029-0.0.9`][kanban] to the Done column with the next available `DONE-NNN-0.0.9` id; add / confirm the card body's `Spec:` reference points at [`docs/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (this document).
  - [ ] **No version-file edits in this card.** Leave `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` to the joint `0.0.9` cut per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut).
  - [ ] If the schedule forces Slice 3 to defer, carve it off as its own follow-up card (`docs/spec-029b-nullable_overrides-0_0_9.md` or a renumbered successor) without disrupting Slices 1 + 2 per [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency).

## Problem statement

`django-strawberry-framework`'s `0.0.8` surface ships [`DjangoType`][glossary-djangotype], the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], the filtering and ordering subsystems, and the [Schema export management command][glossary-schema-export-management-command]. The `0.0.9` cohort is dominated by the [`DjangoConnectionField`][glossary-djangoconnectionfield] / full-Relay work (cards [`WIP-ALPHA-030-0.0.9`][kanban] / [`WIP-ALPHA-031-0.0.9`][kanban] / [`WIP-ALPHA-032-0.0.9`][kanban]). This card is the smallest of the four `0.0.9` cards: a three-slice **developer-experience cleanup pass** that closes three independent, small gaps before the larger connection-field surfaces land.

Each slice closes a distinct gap:

1. **Slice 1 — the `extensions=` instance form is deprecated upstream.** Strawberry deprecated `extensions=[SomeExtension()]` (the instance form) in favor of `extensions=[SomeExtension]` (the class) or `extensions=[lambda: SomeExtension(...)]` (the factory callable). Both upstream peers already use the factory-callable form in their consumer docs. The package's tests and consumer-facing docs still carry the instance form in several places. Strawberry's removal runway is multiple releases, but landing the migration in `0.0.9` — **before** the connection-field cards ship new schema-construction surfaces — means consumers copy from a current pattern, not a deprecated one. This is the defensive slice (no behavior change; alignment only).
2. **Slice 2 — there is no type-definition diagnostic.** Neither [`graphene-django`][graphene-django] nor [`strawberry-graphql-django`][strawberry-django] ships an equivalent `manage.py inspect_*` diagnostic for its type definitions. Consumers debugging "why did this field resolve to that GraphQL type?" currently introspect by hand against the constructed GraphQL schema, *after* schema construction. A `manage.py inspect_django_type <TypeName>` command moves that diagnostic to the type-definition layer — it walks a [`DjangoTypeDefinition`][definition] and prints, per field, the Django field → resolved scalar → nullability → which converter fired. This is the differentiating slice (capability neither upstream has).
3. **Slice 3 — GraphQL nullability is welded to the Django column.** Today a field's GraphQL nullability is exactly `field.null`: a non-null column renders as `T!`, a nullable column as `T`. Consumers routinely need to decouple the two — render a non-null column as nullable in GraphQL (a field that is `NOT NULL` in the DB but legitimately absent from a partial response), or render a nullable column as required in GraphQL (a column that is `null=True` for legacy-migration reasons but always populated in practice). [`strawberry_django.field(required=True/False)`][strawberry-django] allows exactly this per-field override against the Django column's native nullability; [`graphene-django`][graphene-django] allows the same via per-field overrides on the `DjangoObjectType`. The only escape hatches the package offers today are an `AlterField` migration (changes the database) or a consumer-authored annotation override (forces the consumer to hand-write the scalar annotation and lose the converter's choice-enum / [`BigInt`][glossary-bigint-scalar] / array resolution). This slice surfaces the same capability through a `Meta`-key dict, consistent with the rest of the package's `Meta`-shaped API. This is the ⚛️&🍓-required slice and the one carrying the open design questions; it is the design core of this spec.

The three slices share no implementation surface — Slice 1 is a mechanical sweep over already-shipped code, Slice 2 is a strict reader of the existing introspection surface, and Slice 3 plugs into the scalar-resolution path at type-construction time. They ship in any order; the card completes when all three land (or Slice 3 carves off per [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)).

## Current state

A true description of the repo as of this writing (the plan is written against it):

- [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] = `{"description", "exclude", "fields", "filterset_class", "interfaces", "model", "name", "optimizer_hints", "orderset_class", "primary"}`; [`DEFERRED_META_KEYS`][base] = `{"aggregate_class", "fields_class", "search_fields"}`. Neither `nullable_overrides` nor `required_overrides` exists in either set; declaring either today raises [`ConfigurationError`][glossary-configurationerror] via the unknown-key typo guard at [`_validate_meta`][base].
- [`django_strawberry_framework/types/base.py`][base] ships `_validate_filterset_class` and `_validate_orderset_class` — both use a local in-function import to dodge the `types → {filters,orders} → types` module-load cycle and raise [`ConfigurationError`][glossary-configurationerror] for a non-subclass value. They are the structural template for Slice 3's new `_validate_nullability_overrides` helper.
- [`_build_annotations`][base]'s scalar branch calls `convert_scalar(field, cls.__name__)` for every selected, non-relation, non-consumer-authored, non-pk-suppressed field. Consumer-authored fields (`field.name in consumer_authored_fields`) and the Relay-Node-suppressed pk `continue` past `convert_scalar` entirely.
- [`django_strawberry_framework/types/converters.py::convert_scalar`][converters] takes `(field, type_name)`; its final widening step is `if field.null: py_type = py_type | None`. The `ArrayField` and `HStoreField` branches return early but each widens on `field.null` independently. There is no nullability-override parameter today.
- [`DjangoTypeDefinition`][definition] (on `cls.__django_strawberry_definition__` after [`__init_subclass__`][base]) carries `selected_fields: tuple[models.Field, ...]`, `field_map: dict[str, FieldMeta]`, the four `consumer_*_fields` frozensets, `filterset_class` / `orderset_class` slots, and `finalized: bool`. [`FieldMeta`][field-meta] carries `name`, `is_relation`, the cardinality flags, `nullable`, `related_model`, `attname`, and the FK target columns — the read surface Slice 2's command prints from. There is no `nullable_overrides` / `required_overrides` slot yet (Slice 3 does NOT need one — the override resolves to an annotation at construction time; it does not need to persist on the definition).
- [`django_strawberry_framework/management/commands/export_schema.py`][export-schema-cmd] is the only shipped management command; it is the structural model for Slice 2's `inspect_django_type` command (`add_arguments` with a positional, `handle` resolving a dotted path via `import_module_symbol`, `CommandError` for the failure modes). There is **no** `inspect_django_type.py` on disk.
- Instance-form `extensions=[DjangoOptimizerExtension()]` sites exist at: [`tests/test_list_field.py`][test-list-field] (lines 753, 886), [`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection] (lines 51, 157), [`tests/types/test_generic_foreign_key.py`][test-generic-fk] (line 102), and the consumer-doc snippets in [`docs/README.md`][docs-readme] (lines 48, 141, 147) and [`docs/GLOSSARY.md`][glossary] (lines 184, 354, 491, 1074). [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] (line 36) and [`TODAY.md`][today] (line 101) **already use** the class form; [`GOAL.md`][goal]'s astronomy `strawberry.Schema(...)` carries no `extensions=` argument. The card's affected-files list names `config/schema.py`, `GOAL.md`, and `TODAY.md`, but those are already migrated or carry no instance form — see [Decision 3](#decision-3--instancefactory-callable-migration-shape).
- [`docs/GLOSSARY.md`][glossary] has no heading for `Meta.nullable_overrides`, `Meta.required_overrides`, or the inspect command; the three new glossary entries are authored during implementation (per [Doc updates](#doc-updates)) and flagged in [Risks and open questions](#risks-and-open-questions).
- The fakeshop [`scalars`][fakeshop-scalars-models] app (paired `ScalarSpecimen` / `NullableScalarSpecimen`, every scalar in non-null and nullable shapes) is the natural live-HTTP host for Slice 3's nullability-flip test — it already pins every converter row in both shapes, so a flipped-nullability assertion sits beside the existing baseline.

## Goals

1. Migrate every `extensions=[DjangoOptimizerExtension()]` instance-form site (tests + consumer docs) to the factory-callable form Strawberry recommends, with zero behavior change and zero remaining instance-form construction site repo-wide (Slice 1).
2. Ship a `manage.py inspect_django_type <Type>` diagnostic command that walks a [`DjangoTypeDefinition`][definition] and prints the per-field resolution table, with `CommandError` for every failure mode, mirroring the shipped [Schema export management command][glossary-schema-export-management-command] (Slice 2).
3. Ship `Meta.nullable_overrides` and `Meta.required_overrides` as net-new public `Meta` keys that decouple a scalar field's GraphQL nullability from its Django column without an `AlterField` migration or a consumer-authored annotation, validated at type-creation time, composing cleanly with [`Meta.exclude`][glossary-metaexclude], [Choice enum generation][glossary-choice-enum-generation], and [Scalar field override semantics][glossary-scalar-field-override-semantics] (Slice 3).
4. Earn package coverage through live fakeshop HTTP flows (Slice 3's nullability flip on the [`scalars`][fakeshop-scalars-models] app) and in-process `call_command` tests (Slice 2), per [`docs/TREE.md`][tree]'s coverage-priority rule; the package coverage gate (`fail_under = 100`) is reached because those tests exercise the package end-to-end.
5. Keep package version state command-gated and owned by the joint `0.0.9` cut: no slice in this card edits `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], `uv.lock`, or promotes a CHANGELOG release heading (see [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Non-goals

- **Relation-field nullability override.** Forward-FK / OneToOne nullability override (`TargetType | None` ↔ `TargetType`) and reverse-FK / M2M list nullability override (`[T!]` ↔ `[T!]!`) are out of scope for `0.0.9`; Slice 3's overrides are scalar-column-only and reject a relation override-target with [`ConfigurationError`][glossary-configurationerror] (see [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)). The list-vs-element nullability ambiguity on the many-side is its own design space.
- **`DjangoListField` / `DjangoConnectionField` argument injection.** Slice 1 migrates the construction snippet; it does not add filter / order / nullability arguments to any field. Those compose in the connection-field cohort.
- **A `--watch` / `--json` / SDL-diff mode on the inspect command.** Slice 2 ships a single human-readable table to stdout, matching the `0.0.7` `export_schema` posture (no `--watch` / `--indent` / JSON mode). Machine-readable output is a follow-up if demand surfaces.
- **Persisting overrides on `DjangoTypeDefinition`.** Slice 3 resolves the override to a final annotation at type-construction time; it does not add a `nullable_overrides` slot to [`DjangoTypeDefinition`][definition] (nothing downstream reads it — the annotation is already authoritative once `convert_scalar` returns).
- **A finalizer change for Slice 3.** Overrides apply in [`__init_subclass__`][base] before [`finalize_django_types`][glossary-finalize_django_types] runs; the finalizer is untouched. This is the [Definition-order independence][glossary-definition-order-independence] property: a column's nullability resolves with zero dependency on relation-target import order.
- **A version bump.** Owned by the joint `0.0.9` cut (see [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Borrowing posture

This card is a DX cleanup, not a new subsystem port. There is no cookbook pipeline to borrow. The relevant precedent is per-slice:

### Slice 1 — both upstreams already use the factory-callable form

[`strawberry-graphql-django`][strawberry-django] and the broader Strawberry ecosystem use `extensions=[SchemaExtension]` (class) or `extensions=[lambda: SchemaExtension(...)]` (factory callable) in their consumer documentation; the instance form `extensions=[SchemaExtension()]` is the deprecated shape Strawberry will eventually remove. Borrow the recommended form verbatim. Nothing about the package's own extension behavior changes — Strawberry instantiates the class (or calls the factory) per-request internally, exactly as it does with a pre-built instance today.

### Slice 2 — `inspect_django_type` is conceptually like Django's `inspectdb`, scoped to the framework

Django's `manage.py inspectdb` introspects a database and prints model definitions; `inspect_django_type` is the framework analogue scoped to the type-definition surface — it introspects a finalized [`DjangoTypeDefinition`][definition] and prints the resolved GraphQL field table. Neither [`graphene-django`][graphene-django] (which ships `manage.py graphql_schema`, an SDL export) nor [`strawberry-graphql-django`][strawberry-django] (which ships `export_schema`, mirrored by this package's [Schema export management command][glossary-schema-export-management-command]) ships a type-definition introspection command. The structural model to borrow is the package's own [`export_schema.py`][export-schema-cmd] `Command` shape (`add_arguments` / `handle` / `CommandError`), not an upstream command.

### Slice 3 — borrow the *capability* of `strawberry_django.field(required=...)`, not its surface

[`strawberry_django.field(required=True/False)`][strawberry-django] lets a consumer override a single field's GraphQL nullability against the Django column's native nullability; [`graphene-django`][graphene-django] allows the same via per-field overrides declared on the `DjangoObjectType` class body. Both are **field-level decorator / assignment surfaces**. The package's [`START.md`][start] "Meta classes everywhere on consumer surfaces" rule forbids that shape for consumer-facing declarations — so the package borrows the *capability* (decouple GraphQL nullability from the column) and re-expresses it as a `Meta`-key dict (`Meta.nullable_overrides` / `Meta.required_overrides`), consistent with [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]. What is **not** borrowed: the per-field `field(required=...)` call site (that is the strawberry-django decorator shape the package exists to replace), and the implicit "the annotation declares the override" coupling (the package keeps the converter authoritative and layers the override on top — see [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)).

## User-facing API

### Slice 1 — `extensions=` construction (consumer-facing migration)

```python
import strawberry
from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types, strawberry_config

finalize_django_types()

# Before (deprecated instance form):
schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])

# After (factory-callable form — bare class; Strawberry instantiates it):
schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension])

# After, when constructor arguments are needed (e.g. strictness):
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[lambda: DjangoOptimizerExtension(strictness="raise")],
)
```

### Slice 2 — `manage.py inspect_django_type <Type>`

```shell
# By registered type name (resolved against the type registry):
uv run python examples/fakeshop/manage.py inspect_django_type PatronType

# By dotted import path (resolved first, before the registry fallback):
uv run python examples/fakeshop/manage.py inspect_django_type apps.library.schema.PatronType
```

Illustrative output (exact column layout is an implementation detail; the contract is "every selected field, with its resolved scalar and nullability"):

```text
PatronType  (model: apps.library.models.Patron)
  field                  django field type        graphql type        nullable   converter
  ---------------------  -----------------------  ------------------  ---------  --------------------
  id                     BigAutoField             GlobalID!           no         relay.Node id
  name                   TextField                String!             no         SCALAR_MAP[TextField]
  lifetime_fines_cents   BigIntegerField          BigInt!             no         SCALAR_MAP[BigIntegerField]
  membership_status      CharField(choices)       PatronMembership…!  no         choice enum
  loans                  reverse ForeignKey       [LoanType!]!        no (list)  relation: reverse FK
```

### Slice 3 — `Meta.nullable_overrides` / `Meta.required_overrides`

```python
from django_strawberry_framework import DjangoType

from . import models


class ScalarSpecimenType(DjangoType):
    class Meta:
        model = models.ScalarSpecimen
        fields = "__all__"
        # `text_value` is NOT NULL in the database but the GraphQL surface
        # should allow it to be absent (e.g. a partial-projection response):
        nullable_overrides = ("text_value",)
        # `note` is `null=True` in the database for legacy reasons but is
        # always populated in practice, so the GraphQL surface marks it required:
        required_overrides = ("note",)
```

- `Meta.nullable_overrides` — a tuple / list of scalar field names whose GraphQL type is forced nullable (`T` → `T | None`, rendered `T` instead of `T!`) regardless of the Django column's `null` flag.
- `Meta.required_overrides` — a tuple / list of scalar field names whose GraphQL type is forced non-null (`T | None` → `T`, rendered `T!` instead of `T`) regardless of the column's `null` flag.

Both keys mirror the [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] tuple-of-names shape. The two sets must be disjoint; naming a field in both raises [`ConfigurationError`][glossary-configurationerror].

#### Error shapes (Slice 3)

- A name in `nullable_overrides` / `required_overrides` that is not a field on the model: [`ConfigurationError`][glossary-configurationerror] at type-creation time naming the field, the model, and the override key.
- A name that is excluded via [`Meta.exclude`][glossary-metaexclude] (or otherwise not in the selected field set): [`ConfigurationError`][glossary-configurationerror] — the override targets a field that will not appear in the GraphQL type.
- A name that is a consumer-authored field (annotation or `strawberry.field` assignment): [`ConfigurationError`][glossary-configurationerror] — the consumer's annotation already controls nullability per [Scalar field override semantics][glossary-scalar-field-override-semantics]; the override would be silently ignored, so the package fails loud.
- A name that is a relation field (FK / OneToOne / M2M / reverse): [`ConfigurationError`][glossary-configurationerror] directing the consumer to the scalar-only scope (relation override deferred per [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)).
- The same field named in both sets: [`ConfigurationError`][glossary-configurationerror] (contradictory — a field cannot be both forced-nullable and forced-required).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-029-consumer_dx_cleanup-0_0_9.md`** (this document), NOT `docs/spec-021-nullable_overrides-0_0_8.md` as the [`KANBAN.md`][kanban] card body's Slice 3 "Requires spec" line names it.

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `WIP-ALPHA-029-0.0.9`, so `<NNN>` is `029` and `<0_0_X>` is `0_0_9`.
- The card body's `docs/spec-021-nullable_overrides-0_0_8.md` reference is doubly stale: `021` is a different card's NNN ([`DONE-021-0.0.7`][kanban], the apps card) and `0_0_8` predates the card's `0.0.9` retag. Per [`docs/SPECS/NEXT.md`][next], a card-body reference that conflicts with the structured-filename convention is rewritten to the canonical name in the same archive sweep (see [Risks and open questions](#risks-and-open-questions)).
- The topic slug is `consumer_dx_cleanup` — it names the card's subject (the consumer-DX cleanup pass) rather than any single slice. The whole card is three slices; a slug naming only Slice 3 (`nullable_overrides`) would mis-scope the spec.

Alternatives considered (and rejected):

- **Honor the card body verbatim with `docs/spec-021-nullable_overrides-0_0_8.md`.** Rejected: wrong NNN, wrong version, and an unnumbered-against-its-card spec that breaks the structured-filename convention.
- **Topic slug `nullable_overrides`** (matching Slice 3, the spec's design core). Rejected: the spec covers all three slices per [Decision 2](#decision-2--one-spec-covers-all-three-slices); naming the file after one slice would imply the other two are out of scope. If Slice 3 carves off into its own follow-up card per [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency), THAT follow-up spec takes the `nullable_overrides` slug.

### Decision 2 — One spec covers all three slices

This single spec covers Slice 1, Slice 2, and Slice 3. The [`KANBAN.md`][kanban] card body says only Slice 3 "Requires spec" (Slice 1 is "No spec", Slice 2 is "Light spec or none"), but the [`docs/SPECS/NEXT.md`][next] flow authors one spec per WIP card, and the card is the whole cleanup pass.

Justification:

- The three slices belong to one card with one Definition of done; splitting the spec would orphan Slices 1 + 2 from any design record.
- Slices 1 + 2 are low-design (a mechanical sweep and a strict introspection reader); their spec coverage is correspondingly light. The architectural depth concentrates on Slice 3, which carries the open design questions the card body raises (dict-of-name vs tuple-set, `Meta.exclude` interaction, both-sets collision, choice-field interaction, FK / reverse-FK interaction).
- The slices ship independently (per the card's Planning note), so each slice's section is self-contained — a reader implementing only Slice 2 reads [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) and the Slice-2 checklist / DoD items without needing the Slice-3 design.

Alternatives considered (and rejected):

- **A spec for Slice 3 only, with Slices 1 + 2 left specless per the card body.** Rejected: the [`docs/SPECS/NEXT.md`][next] flow targets the card, not a slice; and the KANBAN spec-map would then carry a card whose spec covers only a third of its scope.

### Decision 3 — instance→factory-callable migration shape

Slice 1 replaces `extensions=[DjangoOptimizerExtension()]` (instance) with `extensions=[DjangoOptimizerExtension]` (bare class) at every construction site that passes no constructor arguments, and with `extensions=[lambda: DjangoOptimizerExtension(...)]` (factory callable) at any site that passes constructor arguments (e.g. `strictness=`, per [Strictness mode][glossary-strictness-mode]).

Justification:

- The bare class is the smallest migration and the form both upstreams' docs use for the no-argument case; Strawberry instantiates it internally.
- The bare class **cannot** carry constructor arguments, so a site needing `strictness=` (or any future constructor argument) must use the `lambda:` factory callable. Distinguishing the two cases is the whole subtlety of the slice.
- The sweep is repo-wide, not limited to the card's named files: a `grep -rn "DjangoOptimizerExtension()" .` gate confirms zero remaining instance-form construction sites before the slice closes. The card's named files ([`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection], [`tests/test_list_field.py`][test-list-field], [`tests/types/test_generic_foreign_key.py`][test-generic-fk], the doc snippets) are the known sites; the grep catches any the card missed.
- **The card's affected-files list is partly already-migrated.** [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] already uses `extensions=[DjangoOptimizerExtension]` (class form), [`TODAY.md`][today] already uses the class form, and [`GOAL.md`][goal]'s astronomy schema carries no `extensions=` argument. Slice 1 confirms these are current and edits only the sites that still carry the instance form ([`docs/README.md`][docs-readme], [`docs/GLOSSARY.md`][glossary], and the three test files). This is a conflict between the card body and the repo state, resolved toward the repo (see [Risks and open questions](#risks-and-open-questions)).

Alternatives considered (and rejected):

- **Use the `lambda:` factory callable uniformly (even for the no-argument case).** Rejected: the bare class is simpler and the recommended form for the no-argument case; reserving the lambda for argument-bearing sites keeps the diff minimal and the intent legible.
- **Leave the docs on the instance form and migrate only the tests.** Rejected: the consumer-facing docs are precisely where a consumer copies the deprecated pattern from; the card lists them explicitly and the slice's value is removing the deprecated pattern from consumer-visible surfaces before the connection-field cards add new ones.

### Decision 4 — `inspect_django_type` command shape and argument resolution

The command ships at [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] as `Command(BaseCommand)`, mirroring [`export_schema.py`][export-schema-cmd]: `add_arguments` registers one positional argument (`type`); `handle` resolves it, reads `target.__django_strawberry_definition__`, and prints the per-field table; `CommandError` wraps every failure.

**Argument resolution is two-step (dotted path, then registry name).** The positional argument is resolved as a dotted import path first (via Strawberry's `import_module_symbol` / Django's `import_string`, the same mechanism [`export_schema.py`][export-schema-cmd] uses); on `ImportError`, it falls back to a registered-type-name lookup against the package's type registry (matching a `DjangoType` subclass by `__name__`). This reconciles the card body's two internally-conflicting signals: the `add_arguments` note says "positional `type_dotted_path`" (implying a dotted path) while the worked test example is `call_command("inspect_django_type", "PatronType", ...)` (a bare name). The two-step resolution honors both — a bare registered name resolves via the fallback, a dotted path via the primary lookup. This mirrors the two-step lazy resolution shipped for [`RelatedFilter`][glossary-relatedfilter] / [`RelatedOrder`][glossary-relatedorder] (absolute path first, then a module/registry fallback).

**Output contract.** Per selected field on the [`DjangoTypeDefinition`][definition], print: the Django field name, the Django field type (`type(field).__name__`), the resolved GraphQL scalar / type, the GraphQL nullability, and which converter row fired — the matched [`SCALAR_MAP`][converters] entry, a choice-enum, the Relay-supplied `GlobalID` (for a Relay-Node pk), or the relation converter (for a relation field). The command reads `definition.selected_fields` and `definition.field_map` (the [`FieldMeta`][field-meta] map: `nullable`, `is_relation`, `relation_kind`); for scalar fields it re-runs the same [`SCALAR_MAP`][converters] lookup `convert_scalar` uses so the reported scalar matches the schema exactly. The exact column layout is an implementation detail; the contract is "every selected field, with its resolved scalar and nullability, in selection order."

**`CommandError` failure modes:** unresolvable argument (neither a dotted path nor a registered type name), a resolved symbol that is not a [`DjangoType`][glossary-djangotype] subclass, and a [`DjangoType`][glossary-djangotype] with no `__django_strawberry_definition__` (not yet finalized — the command requires [`finalize_django_types`][glossary-finalize_django_types] to have run, which the example project's schema import triggers).

**Test placement.** Happy-path coverage lands at [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (in-process `call_command` against a real finalized fakeshop [`DjangoType`][glossary-djangotype]), mirroring the existing one-file-per-command convention at [`examples/fakeshop/tests/test_export_schema.py`][fakeshop-tests-export]. Failure-mode coverage lands at [`tests/management/test_inspect_django_type.py`][test-management-inspect], mirroring [`tests/management/test_export_schema.py`][test-management-export]. **The card body names `examples/fakeshop/tests/test_commands.py`; no such file exists** — the only `test_commands.py` on disk is per-app at `examples/fakeshop/apps/products/tests/test_commands.py`, and the example-project management-command convention is one file per command. The conflict is resolved toward the existing convention (see [Risks and open questions](#risks-and-open-questions)).

Justification:

- Reusing the [`export_schema.py`][export-schema-cmd] `Command` shape means a maintainer sees one shape across both commands; the `CommandError` discipline (wrap import / type / value failures) is already established.
- Reading `__django_strawberry_definition__` / [`FieldMeta`][field-meta] makes the command a strict consumer of the existing introspection surface — no new public API, no foundation change.
- The two-step argument resolution is the minimal reconciliation of the card body's conflicting positional-name-vs-test-example signals; it adds no surface a consumer must learn (a name or a path both work).

Alternatives considered (and rejected):

- **Dotted-path-only resolution (honor the `add_arguments` note literally).** Rejected: the card's worked test passes a bare `"PatronType"`, which a dotted-path-only command would reject; the two-step resolution honors both signals.
- **Registry-name-only resolution (honor the test example literally).** Rejected: a dotted path is the unambiguous form when two apps register a `PatronType`; dropping it would force disambiguation the consumer cannot express.
- **Build the table from the constructed `strawberry.Schema` introspection instead of `DjangoTypeDefinition`.** Rejected: the card's stated value is moving the diagnostic to the *type-definition* layer, before schema construction; reading the definition keeps the command usable even when schema construction itself fails.

### Decision 5 — Two-key tuple-set override form

Slice 3 ships **two keys, each a tuple / list of field names** — `Meta.nullable_overrides = ("a", "b")` and `Meta.required_overrides = ("c",)` — NOT a single dict-of-name-to-bool (`Meta.nullability = {"a": True, "c": False}`).

Justification:

- The two-key tuple-set form mirrors [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] (both tuple-of-names, both expressing a per-field set membership), so it reads as native to the package's `Meta`-shaped API.
- A dict-of-name-to-bool duplicates the direction the two-key split already encodes and invites the ambiguous `{"field": False}` shape: does `False` mean "force required" or "no override"? The two-key form has no such ambiguity — membership in `nullable_overrides` means "force nullable," membership in `required_overrides` means "force required," absence from both means "honor the column."
- The two directions are genuinely distinct operations (widen `T` → `T | None` vs narrow `T | None` → `T`), so a per-direction set names each operation explicitly.

Alternatives considered (and rejected):

- **A single `Meta.nullability = {"field": bool}` dict.** Rejected for the `{"field": False}` ambiguity above; could be added later as sugar normalized internally to the two sets if consumers ask, but the two-key form is the primary shape.
- **A single `Meta.nullable_overrides = {"field": bool}` dict (one key, dict value).** Rejected: same ambiguity, and it diverges from the tuple-of-names shape of every other field-selection `Meta` key.

### Decision 6 — Net-new `ALLOWED_META_KEYS` entries, not a `DEFERRED_META_KEYS` promotion

`nullable_overrides` and `required_overrides` land **directly** in [`ALLOWED_META_KEYS`][base]. They are NOT promoted out of [`DEFERRED_META_KEYS`][base] the way [`Meta.orderset_class`][glossary-metaorderset_class] and [`Meta.filterset_class`][glossary-metafilterset_class] were.

Justification:

- The deferred-key promotion gate (per [Cross-subsystem invariants][glossary-cross-subsystem-invariants]) exists because [`Meta.orderset_class`][glossary-metaorderset_class] / [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.aggregate_class`][glossary-metaaggregate_class] / [`Meta.fields_class`][glossary-metafields_class] / [`Meta.search_fields`][glossary-metasearch_fields] were **named in the `Meta` surface before their subsystems shipped** — the deferred set holds keys that are reserved-but-not-yet-functional, and the gate promotes one only when its subsystem applies it end-to-end.
- `nullable_overrides` / `required_overrides` were never reserved; they are net-new keys whose feature ships in the same card that adds them. There is no "declared against an earlier version raised `ConfigurationError`" history to honor. So they go straight into `ALLOWED_META_KEYS`; the deferred-set machinery is not involved.
- This is a real difference from the orders / filters precedent worth pinning so a future maintainer does not look for a promotion gate that was never needed.

Alternatives considered (and rejected):

- **Add them to `DEFERRED_META_KEYS` first, then promote in the same commit.** Rejected: pointless churn — the deferred set models "reserved but not functional," which is never true for these keys.

### Decision 7 — Tri-state `force_nullable` threaded through `convert_scalar`

The override is implemented by threading a keyword-only tri-state `force_nullable: bool | None = None` through [`convert_scalar`][converters], NOT by rewriting the returned annotation at the [`_build_annotations`][base] call site.

The tri-state:

- `None` (default) — honor `field.null`. Identical to today's behavior; every existing call site is unaffected.
- `True` — emit `T | None` regardless of `field.null` (force nullable).
- `False` — emit `T` (strip nullability) regardless of `field.null` (force required).

[`convert_scalar`][converters] computes `effective_null = field.null if force_nullable is None else force_nullable` once and applies it in all three widening branches: the `ArrayField` branch (`list[inner] | None`), the `HStoreField` branch (`JSON | None`), and the shared scalar / choice path (`py_type | None`). [`_build_annotations`][base]'s scalar branch computes `force_nullable` per field from the two override sets and passes it.

Justification:

- The card explicitly says the implementation touches both [`types/base.py`][base] AND [`types/converters.py`][converters]'s scalar-resolution path. The tri-state threaded through `convert_scalar` is the cleanest expression of that: the converter stays the single source of truth for "what annotation does this column produce," and the override is one extra input to it.
- Rewriting the returned annotation at the call site would require unwrapping an arbitrary `T | None` Union to strip nullability (`required_overrides` on a nullable column), which is fragile — it must detect the Union, find `NoneType`, and rebuild the non-None member, with special cases for `list[T] | None` and `EnumType | None`. The tri-state computes the widening *before* it happens, so there is nothing to unwrap.
- The override applies uniformly to every branch because the widening decision is computed from one `effective_null` value — choice enums, arrays, hstore, and plain scalars all honor it without per-branch override logic ([Decision 9](#decision-9--choice-field-interaction) confirms the choice case).

Alternatives considered (and rejected):

- **Rewrite the annotation at the `_build_annotations` call site (`ann | None` to widen; unwrap-Optional to narrow).** Rejected: the narrow direction (`required_overrides`) requires robustly unwrapping `T | None`, `list[T] | None`, and `EnumType | None` — fragile and duplicates knowledge `convert_scalar` already has.
- **A separate `convert_scalar_with_override(...)` wrapper.** Rejected: a second entry point that must stay in sync with `convert_scalar`'s branch logic; the keyword-only parameter keeps one function authoritative.

### Decision 8 — Override validation and collision behavior

A new `_validate_nullability_overrides(meta, selected_names, consumer_authored_fields, model)` helper in [`base.py`][base] (called from the field-selection pass in [`__init_subclass__`][base] / [`_validate_meta`][base]) validates both override sets and raises [`ConfigurationError`][glossary-configurationerror] for any of:

1. **Unknown field** — a name not on `model._meta` fields. (Mirrors the [`Meta.optimizer_hints`][glossary-metaoptimizer_hints] unknown-field guard.)
2. **Excluded field** — a name not in `selected_names` (excluded via [`Meta.exclude`][glossary-metaexclude] or otherwise unselected). The override targets a field that will not appear in the GraphQL type, so it is a configuration error, not a silent no-op.
3. **Consumer-authored field** — a name in `consumer_authored_fields`. A consumer-authored annotation or `strawberry.field` assignment already controls the field's nullability (it `continue`s past `convert_scalar` entirely per [Scalar field override semantics][glossary-scalar-field-override-semantics]), so the override would be silently ignored; the package fails loud instead.
4. **Relation field** — a name resolving to a relation field (scalar-only scope per [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)).
5. **Both-sets collision** — a name in `nullable_overrides ∩ required_overrides`. Contradictory; raises naming the field and both keys.

Justification:

- Fail-loud at type-creation time is the package's established posture ([`ConfigurationError`][glossary-configurationerror] for unknown `Meta` keys, invalid hints, mis-typed override targets). A silently-ignored override is the worst failure mode — the consumer believes nullability flipped and it did not.
- Validating against `selected_names` (not just model existence) catches the [`Meta.exclude`][glossary-metaexclude] interaction the card raises as an open question: an excluded field cannot be overridden because it is not in the type.
- Rejecting consumer-authored fields resolves the interaction with [Scalar field override semantics][glossary-scalar-field-override-semantics]: the two mechanisms both control nullability, and the consumer must pick one. The annotation override is strictly more powerful (it controls the whole annotation, not just nullability), so the validator points the consumer there.

Alternatives considered (and rejected):

- **Silently no-op an override on an excluded / consumer-authored field.** Rejected: silent no-op hides a real configuration mistake; the package fails loud everywhere else.
- **Let the consumer-authored annotation win and skip the override silently.** Rejected: same silent-no-op objection; the consumer cannot tell which mechanism took effect.
- **Allow a field in both sets, with one direction winning.** Rejected: there is no non-arbitrary winner for a contradictory declaration; raising is the honest response.

### Decision 9 — Choice-field interaction

A choice-backed column resolves to a generated enum (`EnumType`, or `EnumType | None` when nullable) per [Choice enum generation][glossary-choice-enum-generation]. The override applies to the enum exactly as it applies to a plain scalar, because the widening step in [`convert_scalar`][converters] runs **after** choice substitution (the documented order: "choices replaces `py_type` *before* null widening"). So `force_nullable=True` on a choice field yields `EnumType | None`; `force_nullable=False` yields `EnumType`. No choice-specific override logic is needed.

Justification:

- [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)'s single `effective_null` computation sits at the post-choice-substitution widening point, so the choice case is covered for free.
- This resolves the card's "choice-field interaction" open question: the override flips the enum's nullability, not its members; the stored-DB-value member naming ([Choice enum generation][glossary-choice-enum-generation]) is untouched.

Alternatives considered (and rejected):

- **Reject overrides on choice fields.** Rejected: there is no reason a choice field's GraphQL nullability should be less overridable than a plain scalar's; the widening point already handles it uniformly.

### Decision 10 — Scalar-only scope; relation-field overrides rejected and deferred

For `0.0.9`, `Meta.nullable_overrides` / `Meta.required_overrides` apply to **scalar (non-relation) columns only**. A name resolving to a relation field (forward FK / OneToOne, M2M, reverse FK / OneToOne / M2M) is rejected at type-creation time with [`ConfigurationError`][glossary-configurationerror].

Justification:

- The scalar-resolution path ([`convert_scalar`][converters]) is the only path Slice 3 threads `force_nullable` through; relation fields take the `field.is_relation` branch in [`_build_annotations`][base] → `PendingRelation` / `resolved_relation_annotation`, an entirely separate annotation path the override does not touch.
- Relation nullability override is a genuinely harder design: a forward single-valued relation (`TargetType | None` ↔ `TargetType`) would thread an override into `resolved_relation_annotation`, but a many-side relation ([Relation handling][glossary-relation-handling] reverse-FK / M2M) renders as `list[TargetType]` (`[T!]!`) where "make it nullable" is ambiguous — does it mean the list is nullable (`[T!]`) or the element (`[T]!`)? Resolving that ambiguity is its own card.
- Scoping to scalars keeps Slice 3 bounded and ships the common case (a `NOT NULL` text column the consumer wants optional in GraphQL) without inventing the many-side list-vs-element semantics.

Alternatives considered (and rejected):

- **Include forward single-valued FK / OneToOne overrides in `0.0.9`** (thread `force_nullable` into `resolved_relation_annotation`, reject only many-side overrides). Viable; rejected for `0.0.9` to keep the slice bounded and the validation rule simple ("relation = rejected"). This is the natural first extension if relation override demand surfaces — see the fallback in [Risks and open questions](#risks-and-open-questions).
- **Silently ignore relation override-targets.** Rejected: silent no-op (see [Decision 8](#decision-8--override-validation-and-collision-behavior)).

### Decision 11 — Version bumps are owned by the joint `0.0.9` cut

**Decision: this card ships within `0.0.9` and does not edit package version fields.** The card shares the `0.0.9` patch line with three sibling WIP cards — [`WIP-ALPHA-030-0.0.9`][kanban] ([`DjangoConnectionField`][glossary-djangoconnectionfield]), [`WIP-ALPHA-031-0.0.9`][kanban] (the full Relay story), and [`WIP-ALPHA-032-0.0.9`][kanban] ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]). When multiple cards target one patch, the version bump belongs to the **joint cut**, not to any individual card's spec.

No slice in this card edits `pyproject.toml`, [`django_strawberry_framework/__init__.py::__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock`, and no slice promotes a [`CHANGELOG.md`][changelog] release heading. Each slice appends its bullets to the `[Unreleased]` block (Slice 1 a `### Changed` migration note; Slices 2 and 3 a `### Added` feature note); release-heading promotion (`[Unreleased]` → `## [0.0.9] - <date>`) happens once, at the joint `0.0.9` cut, under the maintainer's explicit version-bump command — exactly the maintainer-commanded posture pinned in [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] Decision 10, here extended to a shared-patch joint cut.

**CHANGELOG heading.** Slice bullets go under `[Unreleased]`, NOT under `## [0.0.8]` as the card body's per-slice Definition-of-done text says. `0.0.8` already shipped; new `0.0.9`-line work accumulates under `[Unreleased]` until the joint cut promotes it. The card body's `## [0.0.8]` references are stale (carried over from the card's pre-retag `0.0.8` history) — see [Risks and open questions](#risks-and-open-questions).

Justification:

- A feature card mutating shared release state would race the three sibling cards for "who owns the `0.0.9` bump"; centralizing the bump in the joint cut removes the race.
- Keeping version edits command-gated prevents an implementer from touching `pyproject.toml` / `__version__` / the pinned version test while implementing a DX slice.

Alternatives considered (and rejected):

- **Bump to `0.0.9` in this card (it is the lowest-NNN `0.0.9` card).** Rejected: lowest-NNN is not "owns the release"; whichever card lands last, or an explicit maintainer cut, owns the bump. Encoding "lowest NNN bumps" is an implicit-bump rule the package's [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] Decision 10 already rejected.
- **Append CHANGELOG bullets under `## [0.0.8]` per the card body.** Rejected: `0.0.8` is shipped; appending to a shipped heading would mis-attribute `0.0.9` work.

### Decision 12 — Slice independence and the Slice-3 carve-off contingency

The three functional slices are independent and ship in any order, per the [`KANBAN.md`][kanban] Planning note. Slice 1 has no foundation interaction (a sweep over shipped surfaces); Slice 2 is a strict reader of the existing [`DjangoTypeDefinition`][definition]; Slice 3 plugs into [`_build_annotations`][base] / [`convert_scalar`][converters] at type-construction time with no finalizer change. None depends on another.

The card completes when all three slices land. **If the schedule forces Slice 3 to defer** (it is the design-heavy `M`-sized slice), it carves off as its own follow-up card — `docs/spec-029b-nullable_overrides-0_0_9.md` or a renumbered successor — without disrupting Slices 1 + 2, which ship and close the bulk of the card. This is the card body's explicit contingency, pinned here so the carve-off is a planned move, not an ad-hoc one.

Justification:

- The card body states the slices "ship in any order" and that Slice 3 "carves off as its own follow-up card" if deferred; this Decision records that as the operating contract.
- Independence means each slice's PR is reviewable in isolation; a reviewer of the Slice 2 command does not need the Slice 3 override design loaded.

Alternatives considered (and rejected):

- **Enforce a strict slice order (1 → 2 → 3).** Rejected: there is no dependency to enforce; an artificial order would block Slice 2 behind Slice 1 for no reason.

## Implementation plan

The card ships as **three independent functional slices plus a card-completion wrap**. Each functional slice is one PR; the slices may land in any order (per [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)). Line deltas are estimates.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — `extensions=` migration sweep | [`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection], [`tests/test_list_field.py`][test-list-field], [`tests/types/test_generic_foreign_key.py`][test-generic-fk], [`docs/README.md`][docs-readme], [`docs/GLOSSARY.md`][glossary], [`CHANGELOG.md`][changelog] | 0 (behavior-preserving; the existing tests still pass against the migrated construction form) | `+25 / -20` |
| 2 — `inspect_django_type` command | [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] (new), [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (new), [`tests/management/test_inspect_django_type.py`][test-management-inspect] (new), [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`CHANGELOG.md`][changelog] | ~8 (resolve-by-name happy path; resolve-by-dotted-path happy path; per-field table names every selected field with scalar + nullability; choice-field row; relation-field row; `CommandError` for bad path; `CommandError` for non-`DjangoType`; `CommandError` for unfinalized type) | `+220 / -0` |
| 3 — `Meta.nullable_overrides` / `Meta.required_overrides` | [`django_strawberry_framework/types/base.py`][base] (`ALLOWED_META_KEYS` + `_validate_nullability_overrides` + `_build_annotations` `force_nullable` computation), [`django_strawberry_framework/types/converters.py`][converters] (`convert_scalar` `force_nullable` tri-state), [`tests/types/test_converters.py`][test-converters], [`tests/types/test_base.py`][test-types-base], a live HTTP test under [`examples/fakeshop/test_query/`][fakeshop-test-library], [`docs/GLOSSARY.md`][glossary], [`CHANGELOG.md`][changelog] | ~14 (tri-state across scalar / nullable-column / choice / Array / HStore; override-applies for both directions; unknown-field reject; excluded-field reject; consumer-authored-field reject; relation-field reject; both-sets collision reject; live HTTP `T!`→`T` flip; live HTTP `T`→`T!` flip) | `+260 / -10` |
| wrap — KANBAN move (when all three land) | [`KANBAN.md`][kanban] | 0 | `+15 / -5` |

Total expected delta: ~520 lines across three functional slices plus the wrap. No version-file edits (per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Edge cases and constraints

- **A field in `nullable_overrides` that is already nullable** (`field.null is True`). The override is a no-op for the annotation (`force_nullable=True` produces `T | None`, which a nullable column already produced) but is NOT a configuration error — it is a legitimate (if redundant) declaration. Pinned as a passing case, not a raise.
- **A field in `required_overrides` that is already non-null** (`field.null is False`). Symmetric no-op; `force_nullable=False` produces `T`, which a non-null column already produced. Passing case, not a raise.
- **An override on a choice field** — applies to the generated enum (`EnumType | None` ↔ `EnumType`) per [Decision 9](#decision-9--choice-field-interaction). The enum members are unchanged.
- **An override on an `ArrayField`** — `force_nullable=True` produces `list[inner] | None`; `force_nullable=False` produces `list[inner]`. The *inner* element nullability follows `base_field.null` and is NOT affected by the outer override (the override controls only the outer field's nullability). Pinned by a `tests/types/test_converters.py` case.
- **An override on an `HStoreField`** — `JSON | None` ↔ `JSON`, same as the scalar branch.
- **An override on the Relay-Node-suppressed pk** — the pk `continue`s past `convert_scalar` (the Relay interface supplies `id: GlobalID!`), so naming `id` in an override set on a Relay-Node-shaped type targets a field that produces no scalar annotation. Treated as a consumer-authored / suppressed field → [`ConfigurationError`][glossary-configurationerror] per [Decision 8](#decision-8--override-validation-and-collision-behavior) (the pk's nullability is the Relay interface's contract, not the column's).
- **An override naming a field absent from `Meta.fields`** (the type lists a subset and the override names a field not in it). Rejected per [Decision 8](#decision-8--override-validation-and-collision-behavior) rule 2 — the field is not in the selected set.
- **`Meta.nullable_overrides` and `Meta.required_overrides` declared as a non-sequence** (e.g. a bare string `"name"`, which is an iterable of characters). Rejected with [`ConfigurationError`][glossary-configurationerror], mirroring the [`Meta.exclude`][glossary-metaexclude] "must be a non-string sequence of field names" guard at [`base.py`][base] #"Meta.exclude must be a non-string sequence".
- **A secondary [`Meta.primary`][glossary-metaprimary]`= False` `DjangoType` with overrides.** The override applies to the secondary type's annotation exactly as it does to the primary's; the two types may flip nullability on the same column differently (each produces its own annotation). No interaction with the registry's primary resolution.
- **`inspect_django_type` against a type whose override flipped a column.** The command's reported nullability reflects the *resolved* annotation (post-override), so the table is honest about what the GraphQL surface shows — it reads the final annotation, not `field.null`.
- **`inspect_django_type` against an abstract / intermediate base `DjangoType` with no `Meta`.** Such a class does not register and has no `__django_strawberry_definition__`; the command raises `CommandError` ("not a finalized DjangoType") per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution).
- **Slice 1's `lambda:` factory in a module that reloads** (the fakeshop schema-reload test fixture). A `lambda: DjangoOptimizerExtension(...)` is re-evaluated on each reload exactly as the instance form was re-constructed; no captured state leaks across reloads. (No fakeshop site needs the lambda form today — `config/schema.py` uses the bare class — but the contract holds if a future site adds `strictness=`.)

## Test plan

Tests live across the package-internal `tests/` tree and the two `examples/fakeshop/` trees, per [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Coverage that can be earned by a real GraphQL query or a real `call_command` is earned there first.

### Slice 1 — migration sweep (no new tests)

The existing tests at [`tests/test_list_field.py`][test-list-field], [`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection], and [`tests/types/test_generic_foreign_key.py`][test-generic-fk] continue to pass against the migrated `extensions=[DjangoOptimizerExtension]` construction form — that is the regression guard. The slice adds no new test; its correctness is "the suite still passes and `grep -rn 'DjangoOptimizerExtension()' .` finds zero construction sites." If the suite surfaces a `DeprecationWarning` about Strawberry extension instances before the sweep and zero after, that delta is the slice's proof.

### Slice 2 — `inspect_django_type`

- [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (new) — in-process `call_command` against real finalized fakeshop types:
  - `test_inspect_by_registered_name` — `call_command("inspect_django_type", "PatronType")`; capture stdout; assert every selected field of `PatronType` appears with its resolved scalar and nullability (e.g. `lifetime_fines_cents` → `BigInt`, non-null; `loans` → list relation).
  - `test_inspect_by_dotted_path` — `call_command("inspect_django_type", "apps.library.schema.PatronType")`; same assertions; pins the dotted-path resolution branch.
  - `test_inspect_choice_field_row` — against a choice-bearing fakeshop type; assert the choice column reports the generated enum and "choice enum" as the converter.
  - `test_inspect_relation_field_row` — assert a relation field reports its `list[TargetType]` / `TargetType` shape and "relation" as the converter.
- [`tests/management/test_inspect_django_type.py`][test-management-inspect] (new) — failure modes unreachable from a live registered type:
  - `test_bad_dotted_path_raises_command_error` — an unimportable / unknown argument raises `CommandError`.
  - `test_non_djangotype_symbol_raises_command_error` — a dotted path resolving to a non-`DjangoType` symbol raises `CommandError`.
  - `test_unfinalized_type_raises_command_error` — a `DjangoType` with no `__django_strawberry_definition__` raises `CommandError`.

### Slice 3 — `Meta.nullable_overrides` / `Meta.required_overrides`

- [`tests/types/test_converters.py`][test-converters] (extend) — `convert_scalar` `force_nullable` tri-state:
  - `test_convert_scalar_force_nullable_true_widens_non_null_column` — a non-null `TextField` with `force_nullable=True` returns `str | None`.
  - `test_convert_scalar_force_nullable_false_narrows_nullable_column` — a nullable `TextField` with `force_nullable=False` returns `str`.
  - `test_convert_scalar_force_nullable_none_honors_field_null` — the default `None` reproduces today's `field.null`-driven behavior (regression guard).
  - `test_convert_scalar_force_nullable_on_choice_field` — a choice field with `force_nullable=True` returns `EnumType | None`; with `False`, `EnumType`.
  - `test_convert_scalar_force_nullable_on_array_field` — `list[inner] | None` ↔ `list[inner]`; inner element nullability unchanged.
  - `test_convert_scalar_force_nullable_on_hstore_field` — `JSON | None` ↔ `JSON`.
- [`tests/types/test_base.py`][test-types-base] (extend) — validation + collision + override-applies:
  - `test_nullable_overrides_in_allowed_meta_keys` — `"nullable_overrides"` and `"required_overrides"` are in [`ALLOWED_META_KEYS`][base] and NOT in [`DEFERRED_META_KEYS`][base] (pins [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)).
  - `test_nullable_override_flips_annotation` — a `DjangoType` with `nullable_overrides = ("text_value",)` on a non-null column produces a `str | None` annotation; `required_overrides = ("note",)` on a nullable column produces `str`.
  - `test_override_unknown_field_raises` — a name not on the model raises [`ConfigurationError`][glossary-configurationerror].
  - `test_override_excluded_field_raises` — a name excluded via [`Meta.exclude`][glossary-metaexclude] raises.
  - `test_override_consumer_authored_field_raises` — a name with a consumer annotation / `strawberry.field` assignment raises.
  - `test_override_relation_field_raises` — a relation field name raises (scalar-only scope, [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)).
  - `test_override_both_sets_collision_raises` — a name in both sets raises.
  - `test_override_redundant_is_no_op` — `nullable_overrides` on an already-nullable column (and `required_overrides` on an already-non-null column) is accepted (the redundant-but-legal edge case).
- Live HTTP coverage — a test under [`examples/fakeshop/test_query/`][fakeshop-test-library] (the [`scalars`][fakeshop-scalars-models] app is the natural host; `test_scalars_api.py` already pins every converter row in both shapes):
  - `test_nullable_override_flips_sdl_nullability` — a fakeshop [`DjangoType`][glossary-djangotype] declares `nullable_overrides` on a non-null column and `required_overrides` on a nullable column; introspect the schema SDL (or the wire-format `__type` introspection query) and assert the GraphQL field types flipped (`T!` → `T` and `T` → `T!`) while the underlying model column is unchanged. This is the end-to-end proof the override decouples GraphQL nullability from the database column without an `AlterField`.

## Doc updates

Each slice owns its own doc edits (the slices ship independently). The CHANGELOG-edit permission for each slice comes from its doc-update step per the explicit-instruction rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed".

- **Slice 1**
  - [`docs/README.md`][docs-readme] / [`docs/GLOSSARY.md`][glossary]: rewrite the `extensions=[DjangoOptimizerExtension()]` schema-construction snippets to the factory-callable form per [Decision 3](#decision-3--instancefactory-callable-migration-shape). [`GOAL.md`][goal] / [`TODAY.md`][today]: confirm-no-edit (already class-form / no `extensions=` snippet).
  - [`CHANGELOG.md`][changelog]: `### Changed` bullet under `[Unreleased]` — "Migrated `extensions=[DjangoOptimizerExtension()]` to the factory-callable form (`extensions=[DjangoOptimizerExtension]`, or `extensions=[lambda: DjangoOptimizerExtension(...)]` for argument-bearing sites) across tests and consumer docs; aligns with Strawberry's recommended extension-construction form."
- **Slice 2**
  - [`docs/GLOSSARY.md`][glossary]: add an entry (e.g. `## Schema introspection management command` or `## inspect_django_type`) describing the command, its argument resolution, output contract, and `CommandError` failure modes; add it to the [Index][glossary-index] table and the "Integration / tooling" [Browse by category][glossary] row, alongside the [Schema export management command][glossary-schema-export-management-command].
  - [`docs/TREE.md`][tree]: list `inspect_django_type.py` under `management/commands/` in the current-on-disk layout; list the mirrored `tests/management/test_inspect_django_type.py`.
  - [`CHANGELOG.md`][changelog]: `### Added` bullet under `[Unreleased]`.
- **Slice 3**
  - [`docs/GLOSSARY.md`][glossary]: add `## Meta.nullable_overrides` and `## Meta.required_overrides` entries (status `shipped (0.0.9)` once shipped) describing the two-key tuple-set form, the scalar-only scope, the validation rules, the choice/array/hstore behavior, and the cross-references to [Scalar field conversion][glossary-scalar-field-conversion] / [Scalar field override semantics][glossary-scalar-field-override-semantics]; add both to the [Index][glossary-index] table and the "Type generation" / "Field conversion" [Browse by category][glossary] rows.
  - [`README.md`][readme] / [`TODAY.md`][today]: optionally note the new nullability-override capability where the shipped-`Meta`-key surface is enumerated (include only if the surface is reflected there; the existing lists are capability-focused, so a one-line addition is in-scope).
  - [`CHANGELOG.md`][changelog]: `### Added` bullet under `[Unreleased]`.
- **Card-completion wrap**
  - [`KANBAN.md`][kanban]: move [`WIP-ALPHA-029-0.0.9`][kanban] to Done with the next `DONE-NNN-0.0.9` id; add / confirm the card body's spec reference points at [`docs/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029]; rewrite the card body's stale Slice-3 `docs/spec-021-nullable_overrides-0_0_8.md` reference and `## [0.0.8]` CHANGELOG references (the latter only as part of the card-body cleanup, NOT as a CHANGELOG edit). No version-file edits (per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Risks and open questions

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **GLOSSARY has no entry yet for the three new symbols.** `Meta.nullable_overrides`, `Meta.required_overrides`, and the `inspect_django_type` command have no [`docs/GLOSSARY.md`][glossary] heading at spec-authoring time (the [`docs/SPECS/NEXT.md`][next] flow forbids creating glossary entries). Preferred answer: the three entries are authored during implementation (Slice 2 and Slice 3's doc-update steps) and are therefore **omitted from the companion [`docs/spec-029-consumer_dx_cleanup-0_0_9-terms.csv`][spec-029-terms]** so [`scripts/check_spec_glossary.py`][check-spec-glossary] stays green (the checker requires every CSV term to resolve to a real glossary heading). Fallback: if the maintainer wants the glossary entries to exist before implementation, a separate doc-only change adds the three `planned for 0.0.9` headings, after which the CSV can carry the three rows and the checker still passes.
- **Card body names a stale spec filename.** The card's Slice 3 "Requires spec" line names `docs/spec-021-nullable_overrides-0_0_8.md` (wrong NNN, wrong version). Preferred answer per [Decision 1](#decision-1--spec-filename-and-canonical-naming): this spec is `docs/spec-029-consumer_dx_cleanup-0_0_9.md`; the card-body reference is rewritten to the canonical name in the [`docs/SPECS/NEXT.md`][next] Step-8 archive sweep / card-completion wrap. Fallback: none — the structured-filename convention is unambiguous.
- **Card body names a stale CHANGELOG heading.** The card's per-slice Definition-of-done text says CHANGELOG entries go under `## [0.0.8]`. Preferred answer per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut): `0.0.8` is shipped; new work accumulates under `[Unreleased]` and is promoted at the joint `0.0.9` cut. Fallback: if the maintainer has already opened a `## [0.0.9]` heading by implementation time, append there instead of `[Unreleased]`.
- **Card body names a non-existent test file.** The card says Slice 2's test lives at `examples/fakeshop/tests/test_commands.py`; no such file exists (the only `test_commands.py` is per-app at `apps/products/tests/`). Preferred answer per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution): the test lands at [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect], mirroring the one-file-per-command convention of [`examples/fakeshop/tests/test_export_schema.py`][fakeshop-tests-export]. Fallback: if the maintainer prefers a single `test_commands.py` aggregating all example-project command tests, the inspect tests move there and `test_export_schema.py` is folded in too — but the per-command split is the existing pattern.
- **`inspect_django_type` argument resolution conflict.** The card body says positional `type_dotted_path` but its test passes a bare `"PatronType"`. Preferred answer per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution): two-step resolution (dotted path first, registry-name fallback) honors both. Fallback: if a registered-type-name collision across two apps proves confusing, require the dotted path and document the bare name as a convenience that errors on ambiguity.
- **Relation-field nullability override deferred.** Preferred answer per [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred): scalar-only for `0.0.9`; relation override-targets raise. Fallback: if relation override demand surfaces, the natural first extension is forward single-valued FK / OneToOne override (thread `force_nullable` into `resolved_relation_annotation`), with the many-side list-vs-element nullability ambiguity ([Relation handling][glossary-relation-handling]) staying out until its own design lands.
- **Dict-of-name vs tuple-set form.** Preferred answer per [Decision 5](#decision-5--two-key-tuple-set-override-form): two-key tuple-set. Fallback: a single `Meta.nullability = {"field": bool}` dict could be added later as sugar normalized to the two sets if consumers find two keys verbose; the tuple-set form stays the primary shape.
- **Consumer-authored-field override rejection false-positive.** Preferred answer per [Decision 8](#decision-8--override-validation-and-collision-behavior): naming a consumer-authored field in an override set raises (the annotation already controls nullability). Fallback: if a real pattern surfaces where a consumer wants the override to apply *on top of* a partial annotation override, the rule relaxes to "annotation wins, override is a documented no-op for that field" — but fail-loud is the default until that demand is concrete.
- **Slice 1 repo-wide sweep completeness.** Preferred answer per [Decision 3](#decision-3--instancefactory-callable-migration-shape): the `grep -rn "DjangoOptimizerExtension()" .` gate catches any instance-form site the card's named-files list missed. Fallback: if a site legitimately needs the instance form (none is known), it is documented inline with the reason; the gate is advisory, not absolute, for such a case.

## Out of scope (explicitly tracked elsewhere)

- **Relation-field nullability override** — deferred (no card yet); the forward single-valued case is the natural follow-up, the many-side list-vs-element case is its own design ([Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)).
- **`DjangoConnectionField`** ([`DjangoConnectionField`][glossary-djangoconnectionfield]) — [`WIP-ALPHA-030-0.0.9`][kanban]. Slice 1 migrates the construction snippet so this card's new schema-construction surfaces start on the current form; the connection field itself is out of scope.
- **Full Relay story** ([`WIP-ALPHA-031-0.0.9`][kanban]) and **connection-aware optimizer planning** ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning], [`WIP-ALPHA-032-0.0.9`][kanban]) — the rest of the `0.0.9` cohort; the joint cut that owns the version bump (per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).
- **`Meta.fields_class`** ([`FieldSet`][glossary-fieldset], [`Meta.fields_class`][glossary-metafields_class]) — `0.1.1`. Field-level resolver / redaction sidecar; orthogonal to nullability override (resolve-time gate vs construction-time annotation rewrite).
- **`Meta.search_fields`** ([`Meta.search_fields`][glossary-metasearch_fields]) — `0.1.2`.
- **`AggregateSet`** ([`AggregateSet`][glossary-aggregateset], [`Meta.aggregate_class`][glossary-metaaggregate_class]) — `0.1.3`.
- **Permissions cascade** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions]) — `0.0.10`.
- **A `--json` / `--watch` mode on `inspect_django_type`** — not planned; the command ships a single human-readable table, matching the `0.0.7` `export_schema` posture.
- **Persisting overrides on `DjangoTypeDefinition`** — not needed; the override resolves to a final annotation at construction time ([Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)).
- **Version bump** — owned by the joint `0.0.9` cut ([Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Definition of done

The completion contract the card is built against. Items are grouped by slice; the card completes when all three functional slices' items are satisfied (or Slice 3 carves off per [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)).

**Spec + companion CSV**

1. [`docs/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/spec-029-consumer_dx_cleanup-0_0_9-terms.csv`][spec-029-terms] anchoring every project-specific term the spec references to its [`docs/GLOSSARY.md`][glossary] heading; [`uv run python scripts/check_spec_glossary.py --spec docs/spec-029-consumer_dx_cleanup-0_0_9.md`][check-spec-glossary] reports `OK: <N> terms`.

**Slice 1 — `extensions=` migration**

2. Every `extensions=[DjangoOptimizerExtension()]` instance-form construction site is migrated to the factory-callable form per [Decision 3](#decision-3--instancefactory-callable-migration-shape) — bare class for no-argument sites, `lambda:` factory for argument-bearing sites. `grep -rn "DjangoOptimizerExtension()" .` finds zero construction sites (prose and this spec's quoted examples excluded).
3. The consumer-doc snippets in [`docs/README.md`][docs-readme] and [`docs/GLOSSARY.md`][glossary] use the factory-callable form; [`examples/fakeshop/config/schema.py`][fakeshop-config-schema], [`GOAL.md`][goal], and [`TODAY.md`][today] are confirmed already-current (no edit).
4. `uv run pytest` (CI gate) shows zero `DeprecationWarning` about Strawberry extension instances. [`CHANGELOG.md`][changelog] `[Unreleased]` carries the `### Changed` bullet.

**Slice 2 — `inspect_django_type`**

5. [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] ships with module + class docstring, `add_arguments` registering a positional `type` argument, and `handle` resolving it (dotted path then registry name), reading `__django_strawberry_definition__`, and printing the per-field resolution table per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution).
6. `CommandError` is raised for: an unresolvable argument, a non-`DjangoType` resolved symbol, and an unfinalized `DjangoType`.
7. [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (happy paths via `call_command`) and [`tests/management/test_inspect_django_type.py`][test-management-inspect] (failure modes) cover the command per the [Test plan](#test-plan).
8. [`docs/GLOSSARY.md`][glossary] adds the command entry; [`docs/TREE.md`][tree] lists the new module + mirrored test; [`CHANGELOG.md`][changelog] `[Unreleased]` carries the `### Added` bullet.

**Slice 3 — `Meta.nullable_overrides` / `Meta.required_overrides`**

9. [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] contains `"nullable_overrides"` and `"required_overrides"`; neither is in [`DEFERRED_META_KEYS`][base] (net-new keys per [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)).
10. [`django_strawberry_framework/types/converters.py::convert_scalar`][converters] accepts the keyword-only `force_nullable: bool | None = None` tri-state per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar); the widening decision is computed once from `effective_null` and applied uniformly across the `ArrayField` / `HStoreField` / choice / scalar branches; the `None` default reproduces today's behavior.
11. [`_build_annotations`][base]'s scalar branch computes `force_nullable` per field from the two override sets and passes it to `convert_scalar`; a new `_validate_nullability_overrides` helper validates both sets and raises [`ConfigurationError`][glossary-configurationerror] for unknown / excluded / consumer-authored / relation override-targets and for a both-sets collision per [Decision 8](#decision-8--override-validation-and-collision-behavior).
12. [`tests/types/test_converters.py`][test-converters] (tri-state across scalar / nullable / choice / Array / HStore) and [`tests/types/test_base.py`][test-types-base] (validation + collision + override-applies + `ALLOWED_META_KEYS` membership) cover the slice per the [Test plan](#test-plan).
13. A live HTTP test under [`examples/fakeshop/test_query/`][fakeshop-test-library] demonstrates the override flipping a real model field's GraphQL nullability in both directions (`T!` → `T` and `T` → `T!`) without touching the model column.
14. [`docs/GLOSSARY.md`][glossary] adds the `Meta.nullable_overrides` / `Meta.required_overrides` entries; [`CHANGELOG.md`][changelog] `[Unreleased]` carries the `### Added` bullet.

**Card-completion wrap**

15. [`KANBAN.md`][kanban] records the card as `DONE-NNN-0.0.9` (moved from [`WIP-ALPHA-029-0.0.9`][kanban]) with the card body's spec reference pointing at [`docs/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029].
16. **No version bump lands in this card** per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut): `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` are unchanged; no [`CHANGELOG.md`][changelog] release heading is promoted (the joint `0.0.9` cut owns that).
17. Package coverage stays at 100% (`fail_under = 100`). Routine per-slice work does not run pytest locally — that is owned by CI per the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"Do not run pytest after edits".
18. Worker-local validation: `uv run ruff format .` and `uv run ruff check --fix .` pass. The worker does not run pytest as part of routine slice work.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[package-init]: ../django_strawberry_framework/__init__.py
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-aggregateset]: GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-bigint-scalar]: GLOSSARY.md#bigint-scalar
[glossary-choice-enum-generation]: GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: GLOSSARY.md#connection-aware-optimizer-planning
[glossary-cross-subsystem-invariants]: GLOSSARY.md#cross-subsystem-invariants
[glossary-definition-order-independence]: GLOSSARY.md#definition-order-independence
[glossary-django-appconfig]: GLOSSARY.md#django-appconfig
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-index]: GLOSSARY.md#index
[glossary-metaaggregate_class]: GLOSSARY.md#metaaggregate_class
[glossary-metachoice_enum_names]: GLOSSARY.md#metachoice_enum_names
[glossary-metaexclude]: GLOSSARY.md#metaexclude
[glossary-metafields]: GLOSSARY.md#metafields
[glossary-metafields_class]: GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: GLOSSARY.md#metafilterset_class
[glossary-metaoptimizer_hints]: GLOSSARY.md#metaoptimizer_hints
[glossary-metaorderset_class]: GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: GLOSSARY.md#metaprimary
[glossary-metasearch_fields]: GLOSSARY.md#metasearch_fields
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-relatedfilter]: GLOSSARY.md#relatedfilter
[glossary-relatedorder]: GLOSSARY.md#relatedorder
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-scalar-field-conversion]: GLOSSARY.md#scalar-field-conversion
[glossary-scalar-field-override-semantics]: GLOSSARY.md#scalar-field-override-semantics
[glossary-schema-export-management-command]: GLOSSARY.md#schema-export-management-command
[glossary-specialized-scalar-conversions]: GLOSSARY.md#specialized-scalar-conversions
[glossary-strictness-mode]: GLOSSARY.md#strictness-mode
[spec-029]: spec-029-consumer_dx_cleanup-0_0_9.md
[spec-029-terms]: spec-029-consumer_dx_cleanup-0_0_9-terms.csv
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-015]: SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-019]: SPECS/spec-019-consumer_overrides_scalar-0_0_6.md
[spec-022]: SPECS/spec-022-export_schema-0_0_7.md
[spec-027]: SPECS/spec-027-filters-0_0_8.md
[spec-028]: SPECS/spec-028-orders-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../django_strawberry_framework/types/base.py
[converters]: ../django_strawberry_framework/types/converters.py
[definition]: ../django_strawberry_framework/types/definition.py
[export-schema-cmd]: ../django_strawberry_framework/management/commands/export_schema.py
[field-meta]: ../django_strawberry_framework/optimizer/field_meta.py
[inspect-cmd]: ../django_strawberry_framework/management/commands/inspect_django_type.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-converters]: ../tests/types/test_converters.py
[test-generic-fk]: ../tests/types/test_generic_foreign_key.py
[test-list-field]: ../tests/test_list_field.py
[test-management-export]: ../tests/management/test_export_schema.py
[test-management-inspect]: ../tests/management/test_inspect_django_type.py
[test-relay-id-projection]: ../tests/optimizer/test_relay_id_projection.py
[test-types-base]: ../tests/types/test_base.py

<!-- examples/ -->
[fakeshop-config-schema]: ../examples/fakeshop/config/schema.py
[fakeshop-library-models]: ../examples/fakeshop/apps/library/models.py
[fakeshop-scalars-models]: ../examples/fakeshop/apps/scalars/models.py
[fakeshop-test-library]: ../examples/fakeshop/test_query/test_library_api.py
[fakeshop-tests-export]: ../examples/fakeshop/tests/test_export_schema.py
[fakeshop-tests-inspect]: ../examples/fakeshop/tests/test_inspect_django_type.py

<!-- scripts/ -->
[check-spec-glossary]: ../scripts/check_spec_glossary.py

<!-- .venv/ -->

<!-- External -->
[graphene-django]: https://github.com/graphql-python/graphene-django
[strawberry-django]: https://github.com/strawberry-graphql/strawberry-django
