# Spec: `DjangoType` consumer-DX cleanup pass (`extensions=` instance form, `inspect_django_type`, `Meta.nullable_overrides`)

Planned for `0.0.9` (card [`WIP-ALPHA-029-0.0.9`][kanban]). **This spec is an open build plan, not a shipped record.** The Status line below, the [Slice checklist](#slice-checklist) (unticked), and the [Definition of done](#definition-of-done) describe work that has not yet started; the [Current state](#current-state) section is a true description of the repo as of this writing. **Version boundary** (see [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)): this card shares the `0.0.9` patch line with three sibling WIP cards ([`WIP-ALPHA-030-0.0.9`][kanban], [`WIP-ALPHA-031-0.0.9`][kanban], [`WIP-ALPHA-032-0.0.9`][kanban]); the `pyproject.toml` / [`__version__`][package-init] / [`tests/base/test_init.py::test_version`][test-base-init] bump to `0.0.9` is owned by the **joint cut**, not by this card. This card's slices land within the `0.0.9` line and never bump the version themselves.

Status: planned — not yet implemented. Three independent slices that ship in any order (per the [`KANBAN.md`][kanban] card body's Planning note): Slice 1 (keep the `extensions=` instance form + document why — the migration the card names is deferred, per [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound)), Slice 2 (the `inspect_django_type` diagnostic command), and Slice 3 (the `Meta.nullable_overrides` / `Meta.required_overrides` GraphQL-layer nullability override). The card body counts as complete when all three slices land; if the schedule forces Slice 3 to defer, the slice carves off as its own follow-up card without disrupting Slices 1 + 2 (see [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)).

Owner: package maintainer.

Predecessors: [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] (the most-recently-shipped spec — the canonical voice / depth / section-layout reference for this document; its [Decision 10][spec-028] maintainer-commanded-version-bump posture is the precedent [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut) extends to a joint-cut boundary); [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] (the filter subsystem whose `_validate_filterset_class` validator at [`django_strawberry_framework/types/base.py::_validate_filterset_class`][base] is the structural template for Slice 3's `Meta`-key validation); [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] (the [Schema export management command][glossary-schema-export-management-command] whose [`Command`][export-schema-cmd] shape Slice 2's `inspect_django_type` command mirrors); [`docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019] (the [Scalar field override semantics][glossary-scalar-field-override-semantics] this card's Slice 3 must compose with — a consumer-authored annotation already controls a field's nullability and must not be silently re-overridden); [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-015] (the Relay-Node pk-suppression branch in [`_build_annotations`][base] that Slice 3's scalar-resolution path threads alongside). [`docs/GLOSSARY.md`][glossary] has **no entry yet** for `Meta.nullable_overrides`, `Meta.required_overrides`, or the `inspect_django_type` command; their entries are created during implementation (per [Doc updates](#doc-updates)) and are flagged in [Risks and open questions](#risks-and-open-questions) as the missing-glossary-heading caveat.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Pinned the canonical spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)) over the card body's stale `docs/spec-021-nullable_overrides-0_0_8.md` reference; the single-spec-covers-all-three-slices scope ([Decision 2](#decision-2--one-spec-covers-all-three-slices)); the `extensions=` instance→factory-callable migration shape ([Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound), reshaped in Revision 2); the `inspect_django_type` command shape and argument-resolution contract ([Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)); the two-key tuple-set override form over a dict-of-name shape ([Decision 5](#decision-5--two-key-tuple-set-override-form)); the net-new `ALLOWED_META_KEYS` landing (NOT a `DEFERRED_META_KEYS` promotion) ([Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)); the tri-state `force_nullable` seam threaded through [`convert_scalar`][converters] ([Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)); the validation and collision behavior — `Meta.exclude` interaction, both-sets collision, consumer-authored interaction ([Decision 8](#decision-8--override-validation-and-collision-behavior)); the choice-field interaction ([Decision 9](#decision-9--choice-field-interaction)); the scalar-only scope with relation-field overrides rejected and deferred ([Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)); the joint-`0.0.9`-cut version-bump boundary ([Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)); and the slice-independence / Slice-3 carve-off contingency ([Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)). Conflicts called out in [Risks and open questions](#risks-and-open-questions): the card body's stale `spec-021-nullable_overrides-0_0_8` filename, its `## [0.0.8]` CHANGELOG-heading references, and its `examples/fakeshop/tests/test_commands.py` test path (no such file exists; the on-disk convention is one file per command).
- **Revision 2** — feedback pass over rev1 captured in [`docs/feedback.md`][feedback]. Four P1 (foundational) + four P2 + one P3 findings applied; the P1s reshaped Slices 1–3 materially.
  - **P1 (beyond the feedback) — Slice 1 plan-cache conflict.** Source-reading surfaced that [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]'s [Plan cache][glossary-plan-cache] is instance-bound ([`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004] + the `# instance!` docstring), so the card's instance→class/factory migration would regress the async cache. [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound) rewritten: keep the instance form, document why, defer the migration until the cache is relocated; Problem statement, Current state, Goals, Borrowing posture, User-facing API, Slice checklist, Implementation plan, Test plan, Edge cases, DoD, Risks, and Out of scope all updated.
  - **P1 — inspect read source.** [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) now reads the resolved annotation from `origin.__annotations__` (authoritative — reflects overrides + consumer authorship + resolved relations) and uses `selected_fields` / `field_map` only for Django-side metadata + converter classification; re-running `convert_scalar` for nullability is explicitly rejected. Reconciled with [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar) / [Non-goals](#non-goals).
  - **P1 — finalized-state semantics.** `__django_strawberry_definition__` is assigned at registration (before finalize); finalization is the `DjangoTypeDefinition.finalized` flag. [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) now has two distinct error branches (`definition is None` vs `not definition.finalized`); Edge cases + Test plan + DoD updated.
  - **P1 — Slice 3 validation flow.** [Decision 8](#decision-8--override-validation-and-collision-behavior) split into three stages (`_validate_meta` shape/normalize/collision → `__init_subclass__` target-validation → `_build_annotations` apply); the rev1 single-helper-from-`_validate_meta` signature was not implementable (`_validate_meta` runs before field selection / consumer-authored computation / Relay suppression).
  - **P2 — dotted-path resolution.** Pinned Django's `import_string` (not Strawberry's `import_module_symbol`, which uses the `module:symbol` selector form) per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution).
  - **P2 — bare-name ambiguity.** First-class `CommandError` on a non-unique `__name__` via `registry.iter_types()`; package-internal coverage added.
  - **P2 — live-HTTP host.** Pinned a dedicated acceptance-only secondary `DjangoType` on `library.Book` (`Meta.primary = False`, `BookType` marked primary), avoiding mutation of the `scalars` app's baseline assertions; the [`Meta.primary`][glossary-metaprimary] interaction is part of the plan.
  - **P2 — CSV honesty.** [DoD](#definition-of-done) item 1 now states the companion CSV is intentionally incomplete on the three net-new symbols until their glossary headings land.
  - **P3 — inspect example field.** The illustrative output + happy-path test switched from the non-existent `PatronType.membership_status` to real `BookType` fields (`title` / `subtitle` / `circulation_status` / `shelf` / `genres` / `loans`).

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoType`][glossary-djangotype] — the model-backed Strawberry type all three slices touch. Slice 2 introspects its [`DjangoTypeDefinition`][definition]; Slice 3 adds two new `Meta` keys to its surface; Slice 1 documents why its `extensions=` construction snippet keeps the instance form.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the schema extension whose instance-form construction (`extensions=[DjangoOptimizerExtension()]`) Slice 1 documents and **preserves**: its [Plan cache][glossary-plan-cache] is instance-bound, so the Strawberry-recommended class / factory form is deferred until the cache is relocated off the instance, per [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound).
- [Plan cache][glossary-plan-cache] — the optimizer's per-request plan cache; **instance-bound** (`self._plan_cache`), which is why Slice 1 keeps `DjangoOptimizerExtension` on the instance form ([Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound)).
- [Strictness mode][glossary-strictness-mode] — the optimizer's `strictness` constructor argument; cited because a `DjangoOptimizerExtension(strictness=...)` site would (under the deferred migration) need a `lambda` factory — which regresses the plan cache too, reinforcing [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound)'s keep-instance call.
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

- [`DjangoConnectionField`][glossary-djangoconnectionfield] — the central read-side primitive being built by the sibling [`WIP-ALPHA-030-0.0.9`][kanban] card. The card body lists it as a dependency of Slice 1; under [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound) Slice 1 **keeps** (does not migrate) the `extensions=` instance form, so the connection field's new schema-construction surfaces should likewise present the instance form — the class / factory migration is deferred until the plan cache is relocated off the extension instance.
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

- [ ] Slice 1: document the intentional `extensions=` instance form (NOT a migration — per [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound))
  - [ ] **Do not migrate** any `extensions=[DjangoOptimizerExtension()]` site to the bare class or `lambda` factory: the [Plan cache][glossary-plan-cache] is instance-bound and `_async_extensions` resets it per request (zero async hit rate). The consumer docs ([`docs/README.md`][docs-readme], [`docs/GLOSSARY.md`][glossary]) and the package test schemas ([`tests/optimizer/test_extension.py`][test-extension], [`tests/optimizer/test_field_meta.py`][test-field-meta], [`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection], [`tests/test_list_field.py`][test-list-field], [`tests/types/test_generic_foreign_key.py`][test-generic-fk], [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db]) already use the instance form and stay on it.
  - [ ] Add a one-line "instance is intentional — the plan cache is instance-bound; see [Plan cache][glossary-plan-cache]" note next to the consumer-facing schema-construction snippets in [`docs/README.md`][docs-readme] and [`docs/GLOSSARY.md`][glossary], mirroring the [`optimizer/extension.py`][optimizer-extension] `# instance!` marker, so the snippet is not later "modernized" into a regression. This is the slice's only content edit.
  - [ ] **Note the inverse drift:** [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] and [`TODAY.md`][today] use the *class* form `extensions=[DjangoOptimizerExtension]`. This is harmless for the sync-only fakeshop live tests (`_sync_extensions` is a `@cached_property`, so the bare class yields one shared instance in sync mode), but it loses async-cache parity. Surface as a maintainer note — aligning them to the instance form is a behavior change to example/doc code, deferred unless the maintainer directs it (see [Risks and open questions](#risks-and-open-questions)).
  - [ ] [`CHANGELOG.md`][changelog]: append a `### Changed` bullet under `[Unreleased]` recording that the instance-form rationale was documented and the upstream-deprecated-form migration deferred pending plan-cache relocation. No version-heading promotion (per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).
- [ ] Slice 2: `inspect_django_type` diagnostic command
  - [ ] Ship [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] with module + class docstring, `add_arguments` registering a positional `type` argument, and `handle` printing the resolved per-field table per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution). The command resolves its argument as a dotted import path first, then falls back to a registry-name lookup; reads `target.__django_strawberry_definition__` (the [`DjangoTypeDefinition`][definition] populated by [`finalize_django_types`][glossary-finalize_django_types]); and prints, per selected field: Django field name → Django field type → resolved GraphQL scalar / type → nullability → which converter row fired ([`SCALAR_MAP`][converters] entry name, choice-enum, or relation converter).
  - [ ] `CommandError` for: an unresolvable argument (neither an importable dotted path nor a uniquely-registered type name); an **ambiguous bare name** (≥2 registered types share the `__name__` — list candidates); a resolved symbol that is not a [`DjangoType`][glossary-djangotype] subclass; a `DjangoType` with **no `__django_strawberry_definition__`** (abstract / no-`Meta` base); and a `DjangoType` whose **`definition.finalized is False`** (`finalize_django_types()` has not run) — the last two are distinct branches per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution). Mirrors the [`export_schema.py`][export-schema-cmd] `CommandError` discipline.
  - [ ] Example happy-path coverage: [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (new) via `call_command("inspect_django_type", "BookType")` against a real finalized fakeshop [`DjangoType`][glossary-djangotype], asserting the printed table names every selected field with its resolved scalar and nullability (including the `circulation_status` choice row). (The card body names `examples/fakeshop/tests/test_commands.py`; no such file exists — see the conflict note in [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) and [Risks and open questions](#risks-and-open-questions). The new file mirrors the existing one-file-per-command convention at [`examples/fakeshop/tests/test_export_schema.py`][fakeshop-tests-export].)
  - [ ] Package-internal failure-mode coverage: [`tests/management/test_inspect_django_type.py`][test-management-inspect] (new) for the `CommandError` paths not reachable from a live registered type (bad dotted path, non-`DjangoType` symbol, unfinalized type), mirroring [`tests/management/test_export_schema.py`][test-management-export].
  - [ ] [`docs/GLOSSARY.md`][glossary] adds a `## Schema introspection management command` (or `## inspect_django_type`) entry; [`docs/TREE.md`][tree] lists `inspect_django_type.py` under `management/commands/`. [`CHANGELOG.md`][changelog]: `### Added` bullet under `[Unreleased]`.
- [ ] Slice 3: `Meta.nullable_overrides` / `Meta.required_overrides`
  - [ ] [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] grows `"nullable_overrides"` and `"required_overrides"` (net-new public keys — NOT a `DEFERRED_META_KEYS` promotion, per [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)). Validation splits across the three-stage flow per [Decision 8](#decision-8--override-validation-and-collision-behavior): [`_validate_meta`][base] shape-checks the two tuples, normalizes them onto `_ValidatedMeta`, and raises the both-sets collision; a `_validate_nullability_override_targets(...)` helper runs in [`__init_subclass__`][base] **after** `_select_fields` + `consumer_authored_fields` + the Relay-shape check to reject unknown / excluded / consumer-authored / relation / Relay-pk targets.
  - [ ] [`django_strawberry_framework/types/converters.py::convert_scalar`][converters] grows a keyword-only `force_nullable: bool | None = None` tri-state per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar): `None` honors `field.null` (unchanged default); `True` emits `T | None` regardless; `False` emits `T` (non-null) regardless. The widening decision is computed once from `effective_null = field.null if force_nullable is None else force_nullable` and applied uniformly across the `ArrayField` / `HStoreField` / choice / scalar branches.
  - [ ] [`_build_annotations`][base]'s scalar branch ([`base.py`][base] #"annotations[field.name] = convert_scalar(field, cls.__name__)") computes `force_nullable` for each field from the two override sets (`True` if in `nullable_overrides`, `False` if in `required_overrides`, `None` otherwise) and passes it to `convert_scalar`.
  - [ ] Validation per [Decision 8](#decision-8--override-validation-and-collision-behavior): a name in either set must (a) exist on the model, (b) be in the selected field set (not excluded via [`Meta.exclude`][glossary-metaexclude]), (c) NOT be consumer-authored (an annotation / `strawberry.field` override already controls nullability per [Scalar field override semantics][glossary-scalar-field-override-semantics]), (d) NOT be a relation field (scalar-only scope per [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)), and (e) NOT be the Relay-Node-suppressed pk. A field named in **both** sets raises [`ConfigurationError`][glossary-configurationerror] at the shape-check stage (contradictory). Every failure raises [`ConfigurationError`][glossary-configurationerror] at type-creation time naming the offending field.
  - [ ] Package coverage: [`tests/types/test_converters.py`][test-converters] (the `force_nullable` tri-state across scalar / nullable / choice / Array / HStore shapes) + [`tests/types/test_base.py`][test-types-base] (the validation + collision cases: unknown field, excluded field, consumer-authored field, relation field, both-sets collision, override-applies).
  - [ ] Live HTTP coverage: add a **dedicated acceptance-only secondary `DjangoType`** over the [`library`][fakeshop-library-models] `Book` model in [`apps/library/schema.py`][fakeshop-library-schema] (e.g. `NullabilityOverrideBookType`, `Meta.primary = False`) declaring `nullable_overrides = ("title",)` (non-null → nullable) and `required_overrides = ("subtitle",)` (nullable → non-null), and mark the existing `BookType` `Meta.primary = True` to satisfy the [`Meta.primary`][glossary-metaprimary] one-primary rule; expose it via a dedicated root resolver. A test in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] introspects the acceptance type's SDL and asserts `title` flipped `String!` → `String` and `subtitle` flipped `String` → `String!` while the `Book` columns are unchanged. The existing `BookType` and the [`scalars`][fakeshop-scalars-models] app's types / assertions are untouched.
  - [ ] [`docs/GLOSSARY.md`][glossary] adds `## Meta.nullable_overrides` and `## Meta.required_overrides` entries; [`CHANGELOG.md`][changelog]: `### Added` bullet under `[Unreleased]`.
- [ ] Card-completion wrap (lands when all three slices ship; NOT a code slice)
  - [ ] [`KANBAN.md`][kanban]: move [`WIP-ALPHA-029-0.0.9`][kanban] to the Done column with the next available `DONE-NNN-0.0.9` id; add / confirm the card body's `Spec:` reference points at [`docs/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (this document).
  - [ ] **No version-file edits in this card.** Leave `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` to the joint `0.0.9` cut per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut).
  - [ ] If the schedule forces Slice 3 to defer, carve it off as its own follow-up card (`docs/spec-029b-nullable_overrides-0_0_9.md` or a renumbered successor) without disrupting Slices 1 + 2 per [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency).

## Problem statement

`django-strawberry-framework`'s `0.0.8` surface ships [`DjangoType`][glossary-djangotype], the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], the filtering and ordering subsystems, and the [Schema export management command][glossary-schema-export-management-command]. The `0.0.9` cohort is dominated by the [`DjangoConnectionField`][glossary-djangoconnectionfield] / full-Relay work (cards [`WIP-ALPHA-030-0.0.9`][kanban] / [`WIP-ALPHA-031-0.0.9`][kanban] / [`WIP-ALPHA-032-0.0.9`][kanban]). This card is the smallest of the four `0.0.9` cards: a three-slice **developer-experience cleanup pass** that closes three independent, small gaps before the larger connection-field surfaces land.

Each slice closes a distinct gap:

1. **Slice 1 — the `extensions=` instance form is deprecated upstream, but the package's plan cache is instance-bound.** Strawberry deprecated `extensions=[SomeExtension()]` (the instance form) in favor of `extensions=[SomeExtension]` (the class) or `extensions=[lambda: SomeExtension(...)]` (the factory callable). The card frames the migration as a mechanical sweep — but [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]'s [Plan cache][glossary-plan-cache] lives on the instance, and the shipped [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004] decision deliberately recommends the **instance** form so the cache survives async requests (Strawberry's `_async_extensions` yields a fresh instance per access, so the bare class *and* the `lambda` factory both reset the cache → zero async hit rate). Migrating would silently regress that shipped optimization. [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound) resolves the conflict: for `0.0.9` the package **keeps the instance form**, and Slice 1 becomes a documentation clarification (document *why* the instance is intentional) rather than a code migration; the bare-class/factory migration is deferred until the plan cache is relocated off the instance. This is the defensive slice, re-scoped to avoid a regression.
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
- [`django_strawberry_framework/management/commands/export_schema.py`][export-schema-cmd] is the only shipped management command; it is the structural model for Slice 2's `inspect_django_type` command (`add_arguments` with a positional, `handle`, `CommandError` for the failure modes). Its dotted-path resolution uses Strawberry's `import_module_symbol` (the `module:symbol` selector form, with a default symbol name) — Slice 2 instead uses Django's `import_string` for fully-dotted `a.b.c.Symbol` paths per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution). There is **no** `inspect_django_type.py` on disk.
- Instance-form `extensions=[DjangoOptimizerExtension()]` schema-construction sites exist across the package and docs — **more than the card's affected-files list names**: [`tests/optimizer/test_extension.py`][test-extension] (≈19 sites), [`tests/optimizer/test_field_meta.py`][test-field-meta] (line 318), [`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection] (lines 51, 157), [`tests/test_list_field.py`][test-list-field] (lines 753, 886), [`tests/types/test_generic_foreign_key.py`][test-generic-fk] (line 102), [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db] (line 145), [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme], and the consumer-doc snippets in [`docs/README.md`][docs-readme] and [`docs/GLOSSARY.md`][glossary]. [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] and [`TODAY.md`][today] already use the class form; [`GOAL.md`][goal]'s astronomy `strawberry.Schema(...)` carries no `extensions=` argument. A naive `grep -rn "DjangoOptimizerExtension()" .` is **not** a valid migration gate — it also matches legitimate direct instantiation in the optimizer unit tests (`ext = DjangoOptimizerExtension()`, `DjangoOptimizerExtension().plan_relation(...)`), CHANGELOG / archived-spec prose, and this spec's own examples.
- The `DjangoOptimizerExtension` [Plan cache][glossary-plan-cache] is **instance-bound** (`self._plan_cache`): [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004] and the class docstring at [`optimizer/extension.py`][optimizer-extension] #"Pass an **instance**" (with a `# instance!` marker) deliberately recommend the instance form so the cache survives async requests. Strawberry's `_async_extensions` is a plain `@property` that yields a fresh instance per async access, so migrating to the bare class or `lambda` factory would reset the cache to a zero hit rate. The Slice-1 migration is therefore a behavioral regression, not a cosmetic alignment — resolved by [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound).
- [`docs/GLOSSARY.md`][glossary] has no heading for `Meta.nullable_overrides`, `Meta.required_overrides`, or the inspect command; the three new glossary entries are authored during implementation (per [Doc updates](#doc-updates)) and flagged in [Risks and open questions](#risks-and-open-questions).
- The [`library`][fakeshop-library-models] `Book` model carries both a non-null scalar (`title = TextField()`) and a nullable scalar (`subtitle = TextField(blank=True, null=True)`) plus a choice field (`circulation_status`), making it the host for Slice 3's live-HTTP nullability flip (both directions on one model) and the `inspect_django_type` choice-row example. The existing `BookType` in [`apps/library/schema.py`][fakeshop-library-schema] is the only `DjangoType` on `Book` today; Slice 3 adds a **dedicated acceptance-only secondary type** rather than mutating `BookType` or the [`scalars`][fakeshop-scalars-models] app's `ScalarSpecimenType` / `NullableScalarSpecimenType` (whose live tests pin baseline non-null / nullable / all-null wire-format behavior that must not change). The [`Meta.primary`][glossary-metaprimary] multi-type rule applies (exactly one primary must be declared); the plan marks `BookType` primary and the acceptance type `Meta.primary = False` — see [Test plan](#test-plan).

## Goals

1. Keep `DjangoOptimizerExtension` on the instance form (the [Plan cache][glossary-plan-cache] is instance-bound per [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004]) and document why the instance is intentional at the consumer-facing snippets, so the upstream-deprecated form is not adopted in a way that regresses async caching; the bare-class / factory migration is deferred until the cache is relocated off the instance (Slice 1, per [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound)).
2. Ship a `manage.py inspect_django_type <Type>` diagnostic command that walks a [`DjangoTypeDefinition`][definition] and prints the per-field resolution table, with `CommandError` for every failure mode, mirroring the shipped [Schema export management command][glossary-schema-export-management-command] (Slice 2).
3. Ship `Meta.nullable_overrides` and `Meta.required_overrides` as net-new public `Meta` keys that decouple a scalar field's GraphQL nullability from its Django column without an `AlterField` migration or a consumer-authored annotation, validated at type-creation time, composing cleanly with [`Meta.exclude`][glossary-metaexclude], [Choice enum generation][glossary-choice-enum-generation], and [Scalar field override semantics][glossary-scalar-field-override-semantics] (Slice 3).
4. Earn package coverage through live fakeshop HTTP flows (Slice 3's nullability flip on a dedicated acceptance-only `DjangoType` over the [`library`][fakeshop-library-models] `Book` model — which carries both a non-null and a nullable scalar column) and in-process `call_command` tests (Slice 2), per [`docs/TREE.md`][tree]'s coverage-priority rule; the package coverage gate (`fail_under = 100`) is reached because those tests exercise the package end-to-end.
5. Keep package version state command-gated and owned by the joint `0.0.9` cut: no slice in this card edits `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], `uv.lock`, or promotes a CHANGELOG release heading (see [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Non-goals

- **Relation-field nullability override.** Forward-FK / OneToOne nullability override (`TargetType | None` ↔ `TargetType`) and reverse-FK / M2M list nullability override (`[T!]` ↔ `[T!]!`) are out of scope for `0.0.9`; Slice 3's overrides are scalar-column-only and reject a relation override-target with [`ConfigurationError`][glossary-configurationerror] (see [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)). The list-vs-element nullability ambiguity on the many-side is its own design space.
- **`DjangoListField` / `DjangoConnectionField` argument injection.** Slice 1 only documents the construction snippet; it does not add filter / order / nullability arguments to any field. Those compose in the connection-field cohort.
- **A `--watch` / `--json` / SDL-diff mode on the inspect command.** Slice 2 ships a single human-readable table to stdout, matching the `0.0.7` `export_schema` posture (no `--watch` / `--indent` / JSON mode). Machine-readable output is a follow-up if demand surfaces.
- **Persisting overrides on `DjangoTypeDefinition`.** Slice 3 resolves the override to a final annotation written to `cls.__annotations__` at type-construction time; it does not add a `nullable_overrides` slot to [`DjangoTypeDefinition`][definition]. Nothing needs one — the resolved annotation on `origin.__annotations__` IS the authoritative persisted record, and that is exactly what the Slice 2 [`inspect_django_type`](#decision-4--inspect_django_type-command-shape-and-argument-resolution) command reads for post-override nullability (per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) / [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)).
- **A finalizer change for Slice 3.** Overrides apply in [`__init_subclass__`][base] before [`finalize_django_types`][glossary-finalize_django_types] runs; the finalizer is untouched. This is the [Definition-order independence][glossary-definition-order-independence] property: a column's nullability resolves with zero dependency on relation-target import order.
- **A version bump.** Owned by the joint `0.0.9` cut (see [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Borrowing posture

This card is a DX cleanup, not a new subsystem port. There is no cookbook pipeline to borrow. The relevant precedent is per-slice:

### Slice 1 — the upstream factory-callable form conflicts with the package's instance-bound plan cache

[`strawberry-graphql-django`][strawberry-django] and the broader Strawberry ecosystem use `extensions=[SchemaExtension]` (class) or `extensions=[lambda: SchemaExtension(...)]` (factory callable) in their consumer documentation; the instance form is the deprecated shape Strawberry will eventually remove. The package **cannot borrow that form for `DjangoOptimizerExtension`**, because — unlike a stateless upstream extension — the package's extension carries a per-instance [Plan cache][glossary-plan-cache] that the shipped [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004] decision keeps on the instance specifically so it survives async requests. Strawberry instantiates the bare class / calls the factory **fresh per async access** (`_async_extensions` is a plain `@property`), so borrowing the upstream form would reset the cache on every async request. The package keeps the instance form and documents the rationale ([Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound)); the upstream form is adoptable only after the cache is relocated off the instance.

### Slice 2 — `inspect_django_type` is conceptually like Django's `inspectdb`, scoped to the framework

Django's `manage.py inspectdb` introspects a database and prints model definitions; `inspect_django_type` is the framework analogue scoped to the type-definition surface — it introspects a finalized [`DjangoTypeDefinition`][definition] and prints the resolved GraphQL field table. Neither [`graphene-django`][graphene-django] (which ships `manage.py graphql_schema`, an SDL export) nor [`strawberry-graphql-django`][strawberry-django] (which ships `export_schema`, mirrored by this package's [Schema export management command][glossary-schema-export-management-command]) ships a type-definition introspection command. The structural model to borrow is the package's own [`export_schema.py`][export-schema-cmd] `Command` shape (`add_arguments` / `handle` / `CommandError`), not an upstream command.

### Slice 3 — borrow the *capability* of `strawberry_django.field(required=...)`, not its surface

[`strawberry_django.field(required=True/False)`][strawberry-django] lets a consumer override a single field's GraphQL nullability against the Django column's native nullability; [`graphene-django`][graphene-django] allows the same via per-field overrides declared on the `DjangoObjectType` class body. Both are **field-level decorator / assignment surfaces**. The package's [`START.md`][start] "Meta classes everywhere on consumer surfaces" rule forbids that shape for consumer-facing declarations — so the package borrows the *capability* (decouple GraphQL nullability from the column) and re-expresses it as a `Meta`-key dict (`Meta.nullable_overrides` / `Meta.required_overrides`), consistent with [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]. What is **not** borrowed: the per-field `field(required=...)` call site (that is the strawberry-django decorator shape the package exists to replace), and the implicit "the annotation declares the override" coupling (the package keeps the converter authoritative and layers the override on top — see [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)).

## User-facing API

### Slice 1 — `extensions=` construction (the instance form is intentional)

```python
import strawberry
from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types, strawberry_config

finalize_django_types()

# Recommended: pass an INSTANCE. The plan cache lives on the instance, and
# Strawberry's async extension accessor (_async_extensions) creates a fresh
# instance per request — so the bare class / lambda-factory forms reset the
# cache to a zero async hit rate.
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[DjangoOptimizerExtension()],  # instance — intentional (async plan cache)
)

# NOT recommended for THIS extension (Strawberry deprecates the instance form
# generally, but for DjangoOptimizerExtension these reset the per-instance plan
# cache in async mode — see Decision 3 and Out of scope):
#   extensions=[DjangoOptimizerExtension]            # bare class
#   extensions=[lambda: DjangoOptimizerExtension()]  # factory callable
```

### Slice 2 — `manage.py inspect_django_type <Type>`

```shell
# By registered type name (must be unique across the registry; tried on ImportError):
uv run python examples/fakeshop/manage.py inspect_django_type BookType

# By fully-dotted object path (resolved first, via Django's import_string):
uv run python examples/fakeshop/manage.py inspect_django_type apps.library.schema.BookType
```

Illustrative output (exact column layout is an implementation detail; the contract is "every selected field, with its *resolved* GraphQL type and nullability read from `origin.__annotations__`"):

```text
BookType  (model: apps.library.models.Book)
  field                django field type    graphql type                     nullable   converter
  -------------------  -------------------  -------------------------------  ---------  --------------------
  id                   BigAutoField         GlobalID!                        no         relay.Node id
  title                TextField            String!                          no         SCALAR_MAP[TextField]
  subtitle             TextField            String                           yes        SCALAR_MAP[TextField]
  circulation_status   CharField(choices)   BookTypeCirculationStatusEnum!   no         choice enum
  shelf                ForeignKey           ShelfType!                       no         relation: forward FK
  genres               ManyToManyField      [GenreType!]!                    no (list)  relation: M2M
  loans                reverse ForeignKey   [LoanType!]!                     no (list)  relation: reverse FK
```

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

### Decision 3 — Slice 1 keeps the instance form (the plan cache is instance-bound)

**The card frames Slice 1 as a mechanical instance→class/`lambda`-factory sweep. That migration is NOT behavior-preserving, because [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]'s [Plan cache][glossary-plan-cache] lives on the instance (`self._plan_cache`).** The shipped decision at [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004] and the class docstring at [`DjangoOptimizerExtension`][optimizer-extension] #"Pass an **instance**" deliberately instruct consumers to pass the **instance** form so the cache survives async requests: Strawberry instantiates `_sync_extensions` once (a `@cached_property` — the bare class is fine in sync mode), but `_async_extensions` is a plain `@property` that yields a **fresh instance per access**. So both `extensions=[DjangoOptimizerExtension]` (bare class) AND `extensions=[lambda: DjangoOptimizerExtension()]` (factory callable) get a new instance with an empty `self._plan_cache` on every async request — **zero async plan-cache hit rate**. Migrating the optimizer extension to either form silently regresses a shipped, spec-004-deliberate optimization; the `lambda` factory does NOT dodge this (Strawberry calls it fresh per async access). The package's own [`optimizer/extension.py`][optimizer-extension] carries a `# instance!` marker on its example for exactly this reason.

This is a genuine conflict between the card's Slice-1 directive and the shipped plan-cache architecture. Per [`docs/SPECS/NEXT.md`][next] the card is preferred and the conflict is surfaced (see [Risks and open questions](#risks-and-open-questions)); this Decision resolves it with a preferred answer for `0.0.9` and a deferred fallback.

**Decision for `0.0.9`: keep the instance form for `DjangoOptimizerExtension`; do NOT migrate it to the bare class or `lambda` factory.** Slice 1 is re-scoped from "migrate every site" to a **documentation clarification**:

- **Keep** every `extensions=[DjangoOptimizerExtension()]` construction site on the instance form — both the consumer-facing docs (a consumer copying a bare-class snippet would lose async caching) and the package's own test / example schemas (the optimizer suite exercises async paths, and `_async_extensions` would defeat the cache).
- **Add a one-line "instance is intentional (async plan cache)" note** at the consumer-facing snippets ([`docs/README.md`][docs-readme], [`docs/GLOSSARY.md`][glossary]) mirroring the class docstring's `# instance!`, so a future maintainer does not "modernize" the snippet into a regression.
- `DjangoOptimizerExtension` is the only `SchemaExtension` the package ships, so there is no other extension to migrate; the slice touches no code, only the two doc snippets.

The bare-class / `lambda`-factory migration is only safe once the plan cache is relocated off the instance (to a schema-scoped or module-level store) — a non-trivial optimizer change with its own concurrency-safety story, **out of scope for this DX card** (see [Out of scope](#out-of-scope-explicitly-tracked-elsewhere)). Strawberry's removal runway for the instance form is multiple releases (per the card), so there is no `0.0.9` urgency.

Justification:

- The instance form is the package's shipped, documented recommendation precisely *because* the plan cache is instance-bound; migrating it regresses async cache hit rate to zero — a real performance regression to a shipped feature, not a cosmetic deprecation cleanup.
- No "modernize without regression" form exists while the cache is instance-bound (the `lambda` factory has the same fresh-per-async-access problem), so the honest move is to keep the instance form and document why.
- The deprecation runway is long; deferring the migration until the cache is relocated is the low-risk path and keeps this DX card bounded.

Alternatives considered (and rejected):

- **Migrate to the bare class / `lambda` factory as the card directs.** Rejected: regresses the async plan cache (spec-004 + the `# instance!` docstring); not behavior-preserving.
- **Migrate everything AND relocate the plan cache off the instance in this card.** Rejected: the cache relocation is a substantial optimizer change with its own concurrency-safety design; it does not belong in a DX-cleanup card. Tracked as a deferred follow-up (see [Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Migrate only the sync-only test schemas, keep docs + async tests on the instance.** Rejected: a split convention (some sites class, some instance) is more confusing than one form; the cache argument applies to every real consumer, so the instance form is the single honest recommendation. The card's `strictness=` sites (which would need the `lambda` form) are doubly disqualified — the `lambda` regresses the cache too.
- **Validate with a `grep -rn "DjangoOptimizerExtension()" .` gate.** Rejected (and moot under this decision): the pattern catches legitimate direct instantiation in the optimizer unit tests (`ext = DjangoOptimizerExtension()`, `DjangoOptimizerExtension().plan_relation(...)`), historical CHANGELOG / archived-spec prose, and this spec's own examples — it cannot distinguish a `strawberry.Schema(..., extensions=[...])` construction site from a direct call, so it is not a valid pass/fail condition.

### Decision 4 — `inspect_django_type` command shape and argument resolution

The command ships at [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] as `Command(BaseCommand)`, mirroring [`export_schema.py`][export-schema-cmd]: `add_arguments` registers one positional argument (`type`); `handle` resolves it, reads `target.__django_strawberry_definition__`, and prints the per-field table; `CommandError` wraps every failure.

**Argument resolution is two-step (dotted path, then registry name).** The positional argument is resolved as a fully-dotted object path first via **`django.utils.module_loading.import_string`** (which splits on the last dot — `apps.library.schema.BookType` → module `apps.library.schema`, attribute `BookType`); on `ImportError` it falls back to a registered-type-name lookup against the package's type registry. **This is NOT the mechanism [`export_schema.py`][export-schema-cmd] uses** — that command resolves via Strawberry's `import_module_symbol`, which accepts the `module:symbol` selector form (or `module` + a default symbol name) and does **not** resolve a fully-dotted `a.b.c.Symbol` path; the earlier draft's "same mechanism as `export_schema`" claim was wrong. The user-facing examples use the dotted `apps.library.schema.BookType` form, so `import_string` (not `import_module_symbol`) is the correct primary resolver. The two-step shape reconciles the card body's two internally-conflicting signals (the `add_arguments` note says "positional `type_dotted_path`"; the worked test example passes a bare `"BookType"`) and mirrors the absolute-path-then-fallback shape of [`RelatedFilter`][glossary-relatedfilter] / [`RelatedOrder`][glossary-relatedorder].

**Bare-name lookup requires a unique `__name__` match.** The registry can hold multiple `DjangoType` classes with the same `__name__` from different modules ([`Meta.primary`][glossary-metaprimary] multi-type, or two apps each declaring a `BookType`). The fallback iterates `registry.iter_types()` and collects every registered type whose `__name__` equals the argument: **exactly one** match resolves; **zero** matches is unresolvable (try-as-dotted-path already failed, so `CommandError`); **two or more** raises `CommandError` listing the candidate classes by `module.qualname` and their models, and asks the consumer to pass a dotted path. The command MUST NOT return the first match by registry-iteration order — that would make the result import-order-dependent. This ambiguity branch has package-internal coverage (see the [Test plan](#test-plan)).

**Output contract — the resolved annotation is read from `origin.__annotations__`, not re-derived.** The authoritative resolved GraphQL annotation for a finalized type lives on `definition.origin.__annotations__` (`origin` is the `DjangoType` class). [`__init_subclass__`][base] writes the synthesized + consumer annotations there (`cls.__annotations__ = {**synthesized, **consumer_annotations}`), and [`finalize_django_types`][glossary-finalize_django_types] rewrites each pending relation annotation onto `source_type.__annotations__` via `resolved_relation_annotation`. So `origin.__annotations__[field]` is the single source of truth for the rendered GraphQL type AND its nullability — and it **already reflects** Slice 3's `nullable_overrides` / `required_overrides` (the override is baked into the synthesized annotation at construction time per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)) **and** consumer-authored annotations (which bypass `convert_scalar` entirely). The command therefore reads, per selected field: the resolved GraphQL type + nullability from `origin.__annotations__`; the Django field name + Django field type (`type(field).__name__`) + column-native `nullable` from `definition.selected_fields` / `definition.field_map` ([`FieldMeta`][field-meta]); and the converter classification by re-running the [`SCALAR_MAP`][converters] MRO lookup **to NAME which row fired** (matched `SCALAR_MAP` entry, choice-enum, Relay-supplied `GlobalID`, or relation converter) — **not** to determine nullability. **Re-running `convert_scalar(field, type_name)` to get nullability would be wrong** — it reproduces the column-native `field.null` widening and would miss a `nullable_overrides` / `required_overrides` flip and any consumer-authored annotation; the resolved-annotation read is what makes the table honest about what the schema actually shows. The exact column layout is an implementation detail; the contract is "every selected field, with its *resolved* GraphQL type and nullability, in selection order."

**Finalized-state contract (two distinct branches).** `cls.__django_strawberry_definition__` is assigned in [`__init_subclass__`][base] at registration time — **before** [`finalize_django_types`][glossary-finalize_django_types] runs — so its presence does NOT mean the type is finalized. Finalization is the `DjangoTypeDefinition.finalized` flag (flipped in finalizer Phase 3 after `strawberry.type(...)`). The command requires a finalized type because `origin.__annotations__` only carries resolved relation annotations post-finalize. The two states are distinct error branches: a resolved class with **no `__django_strawberry_definition__`** (an abstract / intermediate base `DjangoType` with no `Meta`, which never registers) and a definition with **`finalized is False`** (a concrete but not-yet-finalized type).

**`CommandError` failure modes:** (1) unresolvable argument (neither a dotted path that imports nor a uniquely-registered type name); (2) an ambiguous bare name (two or more registered types share the `__name__` — lists candidates); (3) a resolved symbol that is not a [`DjangoType`][glossary-djangotype] subclass; (4) a `DjangoType` with no `__django_strawberry_definition__` (abstract / no-`Meta` base — "not a registered DjangoType"); (5) a `DjangoType` whose `definition.finalized is False` ("`finalize_django_types()` has not run; import the project schema first"). Branches (4) and (5) are separate messages.

**Test placement.** Happy-path coverage lands at [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (in-process `call_command` against a real finalized fakeshop [`DjangoType`][glossary-djangotype]), mirroring the existing one-file-per-command convention at [`examples/fakeshop/tests/test_export_schema.py`][fakeshop-tests-export]. Failure-mode coverage lands at [`tests/management/test_inspect_django_type.py`][test-management-inspect], mirroring [`tests/management/test_export_schema.py`][test-management-export]. **The card body names `examples/fakeshop/tests/test_commands.py`; no such file exists** — the only `test_commands.py` on disk is per-app at `examples/fakeshop/apps/products/tests/test_commands.py`, and the example-project management-command convention is one file per command. The conflict is resolved toward the existing convention (see [Risks and open questions](#risks-and-open-questions)).

Justification:

- Reusing the [`export_schema.py`][export-schema-cmd] `Command` shape means a maintainer sees one shape across both commands; the `CommandError` discipline (wrap import / type / value failures) is already established.
- Reading `__django_strawberry_definition__` / [`FieldMeta`][field-meta] makes the command a strict consumer of the existing introspection surface — no new public API, no foundation change.
- The two-step argument resolution is the minimal reconciliation of the card body's conflicting positional-name-vs-test-example signals; it adds no surface a consumer must learn (a name or a path both work).

Alternatives considered (and rejected):

- **Dotted-path-only resolution (honor the `add_arguments` note literally).** Rejected: the card's worked test passes a bare `"BookType"`, which a dotted-path-only command would reject; the two-step resolution honors both signals.
- **Registry-name-only resolution (honor the test example literally).** Rejected: a dotted path is the unambiguous form when two apps register a `BookType`; dropping it would force disambiguation the consumer cannot express.
- **Resolve a bare name to the first registry match.** Rejected: import-order-dependent output; the unique-`__name__` contract above raises on ambiguity instead.
- **Build the table from the constructed `strawberry.Schema` introspection instead of `origin.__annotations__` + `DjangoTypeDefinition`.** Rejected: the card's stated value is moving the diagnostic to the *type-definition* layer; reading the finalized type's annotations + definition keeps the command usable even when full schema construction fails, and `origin.__annotations__` is already the authoritative resolved-annotation record (no second source needed).

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

[`convert_scalar`][converters] computes `effective_null = field.null if force_nullable is None else force_nullable` once and applies it at each of the three widening sites: the `ArrayField` early-return branch (`list[inner] | None`), the `HStoreField` early-return branch (`JSON | None`), and the shared scalar / choice path's final widening (`py_type | None`). [`_build_annotations`][base]'s scalar branch computes `force_nullable` per field from the two override sets and passes it. The resulting annotation is written to `cls.__annotations__` in [`__init_subclass__`][base] (`cls.__annotations__ = {**synthesized, **consumer_annotations}`), so the override is **persisted on the class annotation itself** — no `DjangoTypeDefinition` slot is needed (see [Non-goals](#non-goals)), and that annotation is the authoritative record the Slice 2 [`inspect_django_type`](#decision-4--inspect_django_type-command-shape-and-argument-resolution) command reads for post-override nullability.

Justification:

- The card explicitly says the implementation touches both [`types/base.py`][base] AND [`types/converters.py`][converters]'s scalar-resolution path. The tri-state threaded through `convert_scalar` is the cleanest expression of that: the converter stays the single source of truth for "what annotation does this column produce," and the override is one extra input to it.
- Rewriting the returned annotation at the call site would require unwrapping an arbitrary `T | None` Union to strip nullability (`required_overrides` on a nullable column), which is fragile — it must detect the Union, find `NoneType`, and rebuild the non-None member, with special cases for `list[T] | None` and `EnumType | None`. The tri-state computes the widening *before* it happens, so there is nothing to unwrap.
- The override applies uniformly to every branch because the widening decision is computed from one `effective_null` value — choice enums, arrays, hstore, and plain scalars all honor it without per-branch override logic ([Decision 9](#decision-9--choice-field-interaction) confirms the choice case).

Alternatives considered (and rejected):

- **Rewrite the annotation at the `_build_annotations` call site (`ann | None` to widen; unwrap-Optional to narrow).** Rejected: the narrow direction (`required_overrides`) requires robustly unwrapping `T | None`, `list[T] | None`, and `EnumType | None` — fragile and duplicates knowledge `convert_scalar` already has.
- **A separate `convert_scalar_with_override(...)` wrapper.** Rejected: a second entry point that must stay in sync with `convert_scalar`'s branch logic; the keyword-only parameter keeps one function authoritative.

### Decision 8 — Override validation and collision behavior

The override validation splits across the existing three-stage type-construction flow. (An earlier draft proposed a single `_validate_nullability_overrides(meta, selected_names, consumer_authored_fields, model)` helper called from `_validate_meta` — that is not implementable: [`_validate_meta`][base] runs *before* `_select_fields`, before `consumer_authored_fields` is computed, and before Relay-pk suppression is known, so `selected_names` / `consumer_authored_fields` do not exist at `_validate_meta` time.)

1. **Shape + normalize (in [`_validate_meta`][base]).** Shape-check that `Meta.nullable_overrides` / `Meta.required_overrides` are non-string sequences (mirroring the [`Meta.exclude`][glossary-metaexclude] guard), normalize each into a `frozenset[str]` on the returned `_ValidatedMeta`, and raise the **both-sets collision** here (a name in `nullable_overrides ∩ required_overrides` is a shape-level contradiction visible from the raw `Meta` alone — no model/field access needed).
2. **Target-validate (in [`__init_subclass__`][base], after `_select_fields` + `consumer_authored_fields` + the Relay-shape check).** Once the selected fields, the `consumer_authored_fields` frozenset, and the Relay-pk suppression state exist, a `_validate_nullability_override_targets(validated, selected_fields, consumer_authored_fields, relay_pk_name)` helper raises [`ConfigurationError`][glossary-configurationerror] for every unknown / excluded / consumer-authored / relation / Relay-suppressed-pk target (rules below).
3. **Apply (in [`_build_annotations`][base]).** The two normalized override frozensets thread into `_build_annotations`, which computes `force_nullable` per field and passes it to [`convert_scalar`][converters] (per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)).

This keeps the package's "shape gates run once in `_validate_meta`" invariant intact and avoids re-reading raw `Meta` attrs in multiple places. The full set of override failure modes (all raising [`ConfigurationError`][glossary-configurationerror] at type-creation time):

1. **Unknown field** — a name not on `model._meta` fields. (Mirrors the [`Meta.optimizer_hints`][glossary-metaoptimizer_hints] unknown-field guard.)
2. **Excluded field** — a name not in `selected_names` (excluded via [`Meta.exclude`][glossary-metaexclude] or otherwise unselected). The override targets a field that will not appear in the GraphQL type, so it is a configuration error, not a silent no-op.
3. **Consumer-authored field** — a name in `consumer_authored_fields`. A consumer-authored annotation or `strawberry.field` assignment already controls the field's nullability (it `continue`s past `convert_scalar` entirely per [Scalar field override semantics][glossary-scalar-field-override-semantics]), so the override would be silently ignored; the package fails loud instead.
4. **Relation field** — a name resolving to a relation field (scalar-only scope per [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)).
5. **Both-sets collision** — a name in `nullable_overrides ∩ required_overrides`. Contradictory; caught in stage 1 (shape-level normalization) above, naming the field and both keys.

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

No slice in this card edits `pyproject.toml`, [`django_strawberry_framework/__init__.py::__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock`, and no slice promotes a [`CHANGELOG.md`][changelog] release heading. Each slice appends its bullets to the `[Unreleased]` block (Slice 1 a `### Changed` note; Slices 2 and 3 a `### Added` feature note); release-heading promotion (`[Unreleased]` → `## [0.0.9] - <date>`) happens once, at the joint `0.0.9` cut, under the maintainer's explicit version-bump command — exactly the maintainer-commanded posture pinned in [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] Decision 10, here extended to a shared-patch joint cut.

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
| 1 — `extensions=` instance-form clarification (no migration) | [`docs/README.md`][docs-readme], [`docs/GLOSSARY.md`][glossary] (add the "instance is intentional" note next to the construction snippets), [`CHANGELOG.md`][changelog] | 0 (no code change; the instance form is kept per [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound)) | `+12 / -2` |
| 2 — `inspect_django_type` command | [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] (new), [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (new), [`tests/management/test_inspect_django_type.py`][test-management-inspect] (new), [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`CHANGELOG.md`][changelog] | ~8 (resolve-by-name happy path; resolve-by-dotted-path happy path; per-field table names every selected field with scalar + nullability; choice-field row; relation-field row; `CommandError` for bad path; `CommandError` for non-`DjangoType`; `CommandError` for unfinalized type) | `+220 / -0` |
| 3 — `Meta.nullable_overrides` / `Meta.required_overrides` | [`django_strawberry_framework/types/base.py`][base] (`ALLOWED_META_KEYS` + `_ValidatedMeta` override slots + `_validate_meta` shape/normalize/collision + `_validate_nullability_override_targets` in `__init_subclass__` + `_build_annotations` `force_nullable` computation), [`django_strawberry_framework/types/converters.py`][converters] (`convert_scalar` `force_nullable` tri-state), [`tests/types/test_converters.py`][test-converters], [`tests/types/test_base.py`][test-types-base], [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] (acceptance-only secondary type + root resolver; `BookType` marked primary), a live HTTP test in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library], [`docs/GLOSSARY.md`][glossary], [`CHANGELOG.md`][changelog] | ~15 (tri-state across scalar / nullable-column / choice / Array / HStore; override-applies both directions; unknown / excluded / consumer-authored / relation / Relay-pk reject; both-sets collision reject; live HTTP `String!`→`String` + `String`→`String!` flip on the Book acceptance type) | `+300 / -10` |
| wrap — KANBAN move (when all three land) | [`KANBAN.md`][kanban] | 0 | `+15 / -5` |

Total expected delta: ~520 lines across three functional slices plus the wrap. No version-file edits (per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Edge cases and constraints

- **A field in `nullable_overrides` that is already nullable** (`field.null is True`). The override is a no-op for the annotation (`force_nullable=True` produces `T | None`, which a nullable column already produced) but is NOT a configuration error — it is a legitimate (if redundant) declaration. Pinned as a passing case, not a raise.
- **A field in `required_overrides` that is already non-null** (`field.null is False`). Symmetric no-op; `force_nullable=False` produces `T`, which a non-null column already produced. Passing case, not a raise.
- **An override on a choice field** — applies to the generated enum (`EnumType | None` ↔ `EnumType`) per [Decision 9](#decision-9--choice-field-interaction). The enum members are unchanged.
- **An override on an `ArrayField`** — `force_nullable=True` produces `list[inner] | None`; `force_nullable=False` produces `list[inner]`. The *inner* element nullability follows `base_field.null` and is NOT affected by the outer override (the override controls only the outer field's nullability). Pinned by a `tests/types/test_converters.py` case.
- **An override on an `HStoreField`** — `JSON | None` ↔ `JSON`, same as the scalar branch.
- **An override on the Relay-Node-suppressed pk** — the pk `continue`s past `convert_scalar` (the Relay interface supplies `id: GlobalID!`), so naming `id` in an override set on a Relay-Node-shaped type targets a field that produces no scalar annotation. Rejected by [Decision 8](#decision-8--override-validation-and-collision-behavior) rule (e) (the Relay-suppressed pk) — the pk's nullability is the Relay interface's contract, not the column's.
- **An override naming a field absent from `Meta.fields`** (the type lists a subset and the override names a field not in it). Rejected per [Decision 8](#decision-8--override-validation-and-collision-behavior) rule 2 — the field is not in the selected set.
- **`Meta.nullable_overrides` and `Meta.required_overrides` declared as a non-sequence** (e.g. a bare string `"name"`, which is an iterable of characters). Rejected with [`ConfigurationError`][glossary-configurationerror], mirroring the [`Meta.exclude`][glossary-metaexclude] "must be a non-string sequence of field names" guard at [`base.py`][base] #"Meta.exclude must be a non-string sequence".
- **A secondary [`Meta.primary`][glossary-metaprimary]`= False` `DjangoType` with overrides** (the Slice 3 acceptance type's shape). The override applies to the secondary type's annotation exactly as it does to the primary's; the two types flip nullability on the same column independently (each produces its own `cls.__annotations__`). The multi-type registry rule applies — exactly one type per model must be primary — so adding the acceptance type on `Book` requires marking `BookType` `Meta.primary = True`. Relation targets still resolve to the primary; the secondary stays reverse-discoverable via `registry.model_for_type(...)`.
- **`inspect_django_type` against a type whose override flipped a column.** The command reads the resolved annotation from `origin.__annotations__` (per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)), so its reported nullability reflects the post-override result — NOT the column-native `field.null` that a re-run of `convert_scalar` would reproduce.
- **`inspect_django_type` against an abstract / intermediate base `DjangoType` with no `Meta`.** Such a class never registers and has no `__django_strawberry_definition__`; the command raises `CommandError` ("not a registered DjangoType") — a **distinct branch** from the concrete-but-unfinalized case (`definition.finalized is False` → "`finalize_django_types()` has not run"), per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution).
- **The kept instance form under the fakeshop schema-reload fixture.** Each reload re-evaluates the module-level `strawberry.Schema(..., extensions=[DjangoOptimizerExtension()])`, constructing a fresh extension instance (and a fresh empty plan cache) per reload — the same lifecycle the instance form has always had; no captured state leaks across reloads. Keeping the instance form (per [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound)) changes nothing here.

## Test plan

Tests live across the package-internal `tests/` tree and the two `examples/fakeshop/` trees, per [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Coverage that can be earned by a real GraphQL query or a real `call_command` is earned there first.

### Slice 1 — instance-form clarification (no new tests)

No code change and no migration (per [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound)), so no new test. The slice's only edits are the "instance is intentional" doc note in [`docs/README.md`][docs-readme] / [`docs/GLOSSARY.md`][glossary] and the CHANGELOG bullet. The existing optimizer suite ([`tests/optimizer/test_extension.py`][test-extension] etc.) continues to exercise the instance form unchanged — that is the standing regression guard that the instance form and its plan cache still work. There is no `DeprecationWarning` to chase: Strawberry accepts a passed-in instance via the `isinstance` passthrough in `get_extensions()` and does not warn on it.

### Slice 2 — `inspect_django_type`

- [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (new) — in-process `call_command` against real finalized fakeshop types:
  - `test_inspect_by_registered_name` — `call_command("inspect_django_type", "BookType")`; capture stdout; assert every selected `BookType` field appears with its resolved scalar and nullability (e.g. `title` → `String!`, `subtitle` → `String`, `circulation_status` → choice enum, `genres` → list relation).
  - `test_inspect_by_dotted_path` — `call_command("inspect_django_type", "apps.library.schema.BookType")`; same assertions; pins the `import_string` dotted-path branch.
  - `test_inspect_choice_field_row` — assert the `circulation_status` row reports the generated `BookTypeCirculationStatusEnum` and "choice enum" as the converter.
  - `test_inspect_relation_field_rows` — assert `shelf` reports `ShelfType!` (forward FK), `genres` reports `[GenreType!]!` (M2M), and `loans` reports `[LoanType!]!` (reverse FK).
  - `test_inspect_reads_resolved_annotation_not_field_null` — against the Slice-3 `NullabilityOverrideBookType` acceptance type: assert the reported nullability for `title` is `String` (post-`nullable_overrides`) and for `subtitle` is `String!` (post-`required_overrides`), proving the command reads `origin.__annotations__` and not a `convert_scalar` re-run. (If Slices 2 and 3 land in separate PRs, this assertion lands with whichever ships second.)
- [`tests/management/test_inspect_django_type.py`][test-management-inspect] (new) — failure modes unreachable from a live registered type:
  - `test_bad_dotted_path_raises_command_error` — an unimportable / unknown argument raises `CommandError`.
  - `test_ambiguous_bare_name_raises_command_error` — two registered `DjangoType`s sharing a `__name__` (registered in the test) make a bare-name lookup raise `CommandError` listing both candidates by `module.qualname`.
  - `test_non_djangotype_symbol_raises_command_error` — a dotted path resolving to a non-`DjangoType` symbol raises `CommandError`.
  - `test_abstract_base_without_definition_raises_command_error` — a `DjangoType` subclass with no `Meta` (no `__django_strawberry_definition__`) raises `CommandError` ("not a registered DjangoType").
  - `test_unfinalized_type_raises_command_error` — a concrete registered `DjangoType` with `definition.finalized is False` (registry not yet finalized) raises `CommandError` ("`finalize_django_types()` has not run") — a distinct branch from the no-definition case.

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
- Live HTTP coverage — a test in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] against the dedicated acceptance-only `NullabilityOverrideBookType` secondary type on `library.Book` (per the [Slice checklist](#slice-checklist) and [Current state](#current-state): `BookType` marked `Meta.primary = True`, the acceptance type `Meta.primary = False`, exposed via a dedicated root resolver — the existing `BookType` and the [`scalars`][fakeshop-scalars-models] app's types / assertions stay untouched):
  - `test_nullability_override_flips_sdl_nullability` — introspect the acceptance type's SDL (a `__type` introspection query over the dedicated root field) and assert `title` renders `String` (flipped from the `NOT NULL` column's native `String!` via `nullable_overrides`) AND `subtitle` renders `String!` (flipped from the `null=True` column's native `String` via `required_overrides`), while `Book._meta.get_field("title").null` / `...("subtitle").null` are unchanged. End-to-end proof that the override decouples GraphQL nullability from the database column without an `AlterField`, and that the `Meta.primary` multi-type wiring resolves both `Book` types cleanly.

## Doc updates

Each slice owns its own doc edits (the slices ship independently). The CHANGELOG-edit permission for each slice comes from its doc-update step per the explicit-instruction rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed".

- **Slice 1**
  - [`docs/README.md`][docs-readme] / [`docs/GLOSSARY.md`][glossary]: **keep** the `extensions=[DjangoOptimizerExtension()]` instance-form snippets and add a one-line "instance is intentional — the plan cache is instance-bound; see [Plan cache][glossary-plan-cache]" note beside each, per [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound). Do NOT rewrite them to the bare class / `lambda` factory.
  - [`CHANGELOG.md`][changelog]: `### Changed` bullet under `[Unreleased]` — "Documented that `extensions=[DjangoOptimizerExtension()]` must stay the instance form (the plan cache is instance-bound; the bare-class / factory-callable forms reset it in async mode); deferred the Strawberry-deprecated-instance-form migration until the plan cache is relocated off the instance."
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
- **`inspect_django_type` argument resolution conflict.** The card body says positional `type_dotted_path` but its test passes a bare `"BookType"`. Preferred answer per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution): two-step resolution — Django's `import_string` for fully-dotted paths first, then a registry lookup that requires a **unique** `__name__` match (an ambiguous bare name raises `CommandError` listing candidates). The earlier "same mechanism as `export_schema` (`import_module_symbol`)" framing was wrong — `import_module_symbol` uses the `module:symbol` selector form and does not resolve a fully-dotted object path. Fallback: if the bare-name convenience proves error-prone, drop it and require the dotted path.
- **Relation-field nullability override deferred.** Preferred answer per [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred): scalar-only for `0.0.9`; relation override-targets raise. Fallback: if relation override demand surfaces, the natural first extension is forward single-valued FK / OneToOne override (thread `force_nullable` into `resolved_relation_annotation`), with the many-side list-vs-element nullability ambiguity ([Relation handling][glossary-relation-handling]) staying out until its own design lands.
- **Dict-of-name vs tuple-set form.** Preferred answer per [Decision 5](#decision-5--two-key-tuple-set-override-form): two-key tuple-set. Fallback: a single `Meta.nullability = {"field": bool}` dict could be added later as sugar normalized to the two sets if consumers find two keys verbose; the tuple-set form stays the primary shape.
- **Consumer-authored-field override rejection false-positive.** Preferred answer per [Decision 8](#decision-8--override-validation-and-collision-behavior): naming a consumer-authored field in an override set raises (the annotation already controls nullability). Fallback: if a real pattern surfaces where a consumer wants the override to apply *on top of* a partial annotation override, the rule relaxes to "annotation wins, override is a documented no-op for that field" — but fail-loud is the default until that demand is concrete.
- **Slice 1's migration conflicts with the instance-bound plan cache (the card's directive is unsafe as written).** Preferred answer per [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound): keep the instance form for `DjangoOptimizerExtension`. The bare-class / `lambda`-factory migration the card directs would reset the per-instance [Plan cache][glossary-plan-cache] in async mode (Strawberry's `_async_extensions` yields a fresh instance per access), regressing a shipped [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004] optimization — the card-vs-shipped-decision conflict surfaced per [`docs/SPECS/NEXT.md`][next]. Fallback: if Strawberry schedules removal of the instance form, the migration must be paired with relocating the plan cache off the instance (a schema-scoped / module-level store) in the same cohort — a dedicated optimizer card, not this DX card.
- **`config/schema.py` and `TODAY.md` already use the class form.** Preferred answer: leave them — the fakeshop live tests run sync (`_sync_extensions` is a `@cached_property`, so the bare class yields one shared instance and the cache works), so the class form is harmless there. Fallback: if the maintainer wants async-cache parity in the example, a follow-up aligns both to the instance form; out of scope for this documentation-clarification slice.

## Out of scope (explicitly tracked elsewhere)

- **Relation-field nullability override** — deferred (no card yet); the forward single-valued case is the natural follow-up, the many-side list-vs-element case is its own design ([Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)).
- **`DjangoConnectionField`** ([`DjangoConnectionField`][glossary-djangoconnectionfield]) — [`WIP-ALPHA-030-0.0.9`][kanban]. Slice 1 keeps and documents the `extensions=` instance form, so this card's new schema-construction surfaces should present the instance form too; the connection field itself is out of scope.
- **Full Relay story** ([`WIP-ALPHA-031-0.0.9`][kanban]) and **connection-aware optimizer planning** ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning], [`WIP-ALPHA-032-0.0.9`][kanban]) — the rest of the `0.0.9` cohort; the joint cut that owns the version bump (per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).
- **`Meta.fields_class`** ([`FieldSet`][glossary-fieldset], [`Meta.fields_class`][glossary-metafields_class]) — `0.1.1`. Field-level resolver / redaction sidecar; orthogonal to nullability override (resolve-time gate vs construction-time annotation rewrite).
- **`Meta.search_fields`** ([`Meta.search_fields`][glossary-metasearch_fields]) — `0.1.2`.
- **`AggregateSet`** ([`AggregateSet`][glossary-aggregateset], [`Meta.aggregate_class`][glossary-metaaggregate_class]) — `0.1.3`.
- **Permissions cascade** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions]) — `0.0.10`.
- **Relocating the `DjangoOptimizerExtension` plan cache off the instance** — the prerequisite for safely adopting the Strawberry-recommended bare-class / factory-callable `extensions=` form (per [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound)); a dedicated optimizer card with its own concurrency-safety design, not this DX card. Until it lands, the instance form stays.
- **A `--json` / `--watch` mode on `inspect_django_type`** — not planned; the command ships a single human-readable table, matching the `0.0.7` `export_schema` posture.
- **Persisting overrides on `DjangoTypeDefinition`** — not needed; the override resolves to a final annotation on `cls.__annotations__` at construction time, which is the authoritative record the inspect command reads ([Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar) / [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)).
- **Version bump** — owned by the joint `0.0.9` cut ([Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Definition of done

The completion contract the card is built against. Items are grouped by slice; the card completes when all three functional slices' items are satisfied (or Slice 3 carves off per [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)).

**Spec + companion CSV**

1. [`docs/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/spec-029-consumer_dx_cleanup-0_0_9-terms.csv`][spec-029-terms] anchoring every project-specific term that **has** a [`docs/GLOSSARY.md`][glossary] heading; [`uv run python scripts/check_spec_glossary.py --spec docs/spec-029-consumer_dx_cleanup-0_0_9.md`][check-spec-glossary] reports `OK: <N> terms`. The three net-new symbols (`Meta.nullable_overrides`, `Meta.required_overrides`, `inspect_django_type`) have **no glossary heading yet** and are therefore intentionally NOT in the CSV — they are added to the glossary AND the CSV during the Slice 2 / Slice 3 doc-update steps (per [Risks and open questions](#risks-and-open-questions)). The companion CSV is honestly incomplete on the card's new public surfaces until then.

**Slice 1 — `extensions=` instance-form clarification**

2. No `extensions=` form is migrated. Every `extensions=[DjangoOptimizerExtension()]` site (tests, examples, consumer docs) stays on the instance form per [Decision 3](#decision-3--slice-1-keeps-the-instance-form-the-plan-cache-is-instance-bound) — the [Plan cache][glossary-plan-cache] is instance-bound and the bare-class / `lambda` forms regress it in async mode.
3. The consumer-doc snippets in [`docs/README.md`][docs-readme] and [`docs/GLOSSARY.md`][glossary] gain a one-line "instance is intentional (async plan cache)" note. The class-form drift in [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] / [`TODAY.md`][today] is surfaced as a maintainer note (harmless for the sync example), not changed here.
4. [`CHANGELOG.md`][changelog] `[Unreleased]` carries the `### Changed` bullet recording the documented rationale + deferred migration. (No `DeprecationWarning` delta to assert — Strawberry does not warn on a passed-in instance.)

**Slice 2 — `inspect_django_type`**

5. [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] ships with module + class docstring, `add_arguments` registering a positional `type` argument, and `handle` resolving it (`import_string` dotted path, then a unique-`__name__` registry lookup), reading the **resolved annotation from `origin.__annotations__`** for the GraphQL type + nullability and `definition.selected_fields` / `field_map` for Django-side metadata + converter classification, and printing the per-field resolution table per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution).
6. `CommandError` is raised for: an unresolvable argument; an **ambiguous bare name** (≥2 registered types share the `__name__`); a non-`DjangoType` resolved symbol; a `DjangoType` with **no `__django_strawberry_definition__`** (abstract / no-`Meta` base); and a `DjangoType` whose **`definition.finalized is False`** — the last two are distinct branches per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution).
7. [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (happy paths via `call_command`) and [`tests/management/test_inspect_django_type.py`][test-management-inspect] (failure modes) cover the command per the [Test plan](#test-plan).
8. [`docs/GLOSSARY.md`][glossary] adds the command entry; [`docs/TREE.md`][tree] lists the new module + mirrored test; [`CHANGELOG.md`][changelog] `[Unreleased]` carries the `### Added` bullet.

**Slice 3 — `Meta.nullable_overrides` / `Meta.required_overrides`**

9. [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] contains `"nullable_overrides"` and `"required_overrides"`; neither is in [`DEFERRED_META_KEYS`][base] (net-new keys per [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)).
10. [`django_strawberry_framework/types/converters.py::convert_scalar`][converters] accepts the keyword-only `force_nullable: bool | None = None` tri-state per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar); the widening decision is computed once from `effective_null` and applied uniformly across the `ArrayField` / `HStoreField` / choice / scalar branches; the `None` default reproduces today's behavior.
11. The override validation is staged per [Decision 8](#decision-8--override-validation-and-collision-behavior): [`_validate_meta`][base] shape-checks + normalizes the two tuples onto `_ValidatedMeta` and raises the both-sets collision; a `_validate_nullability_override_targets(...)` helper runs in [`__init_subclass__`][base] (after `_select_fields` + `consumer_authored_fields` + the Relay-shape check) and raises [`ConfigurationError`][glossary-configurationerror] for unknown / excluded / consumer-authored / relation / Relay-pk targets; [`_build_annotations`][base] receives the normalized override frozensets and passes `force_nullable` per field to `convert_scalar`.
12. [`tests/types/test_converters.py`][test-converters] (tri-state across scalar / nullable / choice / Array / HStore) and [`tests/types/test_base.py`][test-types-base] (validation + collision + override-applies + `ALLOWED_META_KEYS` membership) cover the slice per the [Test plan](#test-plan).
13. A dedicated acceptance-only `NullabilityOverrideBookType` secondary type on `library.Book` (`Meta.primary = False`; `BookType` marked `Meta.primary = True`) is added to [`apps/library/schema.py`][fakeshop-library-schema] with a dedicated root resolver, and a live HTTP test in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] asserts `title` flips `String!` → `String` and `subtitle` flips `String` → `String!` while the `Book` columns are unchanged; the existing `BookType` and the `scalars` app's types / assertions are untouched.
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
[feedback]: feedback.md
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
[glossary-plan-cache]: GLOSSARY.md#plan-cache
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
[spec-004]: SPECS/spec-004-optimizer_beyond-0_0_3.md
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
[optimizer-extension]: ../django_strawberry_framework/optimizer/extension.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-converters]: ../tests/types/test_converters.py
[test-extension]: ../tests/optimizer/test_extension.py
[test-field-meta]: ../tests/optimizer/test_field_meta.py
[test-generic-fk]: ../tests/types/test_generic_foreign_key.py
[test-list-field]: ../tests/test_list_field.py
[test-management-export]: ../tests/management/test_export_schema.py
[test-management-inspect]: ../tests/management/test_inspect_django_type.py
[test-relay-id-projection]: ../tests/optimizer/test_relay_id_projection.py
[test-types-base]: ../tests/types/test_base.py

<!-- examples/ -->
[fakeshop-config-schema]: ../examples/fakeshop/config/schema.py
[fakeshop-library-models]: ../examples/fakeshop/apps/library/models.py
[fakeshop-library-schema]: ../examples/fakeshop/apps/library/schema.py
[fakeshop-scalars-models]: ../examples/fakeshop/apps/scalars/models.py
[fakeshop-test-library]: ../examples/fakeshop/test_query/test_library_api.py
[fakeshop-test-multi-db]: ../examples/fakeshop/test_query/test_multi_db.py
[fakeshop-test-query-readme]: ../examples/fakeshop/test_query/README.md
[fakeshop-tests-export]: ../examples/fakeshop/tests/test_export_schema.py
[fakeshop-tests-inspect]: ../examples/fakeshop/tests/test_inspect_django_type.py

<!-- scripts/ -->
[check-spec-glossary]: ../scripts/check_spec_glossary.py

<!-- .venv/ -->

<!-- External -->
[graphene-django]: https://github.com/graphql-python/graphene-django
[strawberry-django]: https://github.com/strawberry-graphql/strawberry-django
