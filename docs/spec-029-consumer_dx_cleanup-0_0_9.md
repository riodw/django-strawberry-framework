# Spec: `DjangoType` consumer-DX cleanup pass (`extensions=` singleton-factory, `inspect_django_type`, `Meta.nullable_overrides` / `Meta.required_overrides`)

Planned for `0.0.9` (card [`WIP-ALPHA-029-0.0.9`][kanban]). **This spec is an open build plan, not a shipped record.** The Status line below, the [Slice checklist](#slice-checklist) (unticked), and the [Definition of done](#definition-of-done) describe work that has not yet started; the [Current state](#current-state) section is a true description of the repo as of this writing. **Version boundary** (see [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)): this card shares the `0.0.9` patch line with three sibling WIP cards ([`WIP-ALPHA-030-0.0.9`][kanban], [`WIP-ALPHA-031-0.0.9`][kanban], [`WIP-ALPHA-032-0.0.9`][kanban]); the `pyproject.toml` / [`__version__`][package-init] / [`tests/base/test_init.py::test_version`][test-base-init] bump to `0.0.9` is owned by the **joint cut**, not by this card. This card's slices land within the `0.0.9` line and never bump the version themselves.

Status: planned — not yet implemented. Three independent slices that ship in any order (per the [`KANBAN.md`][kanban] card body's Planning note): Slice 1 (migrate the deprecated-instance, named-instance, and bare-class `extensions=` entries to the per-construction-site singleton-factory form `extensions=[lambda: <instance>]` — function-local singletons in tests, module-level only for one-schema-per-module examples — per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)), Slice 2 (the `inspect_django_type` diagnostic command), and Slice 3 (the `Meta.nullable_overrides` / `Meta.required_overrides` GraphQL-layer nullability override). The card body counts as complete when all three slices land; if the schedule forces Slice 3 to defer, the slice carves off as its own follow-up card without disrupting Slices 1 + 2 (see [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)).

Owner: package maintainer.

Predecessors: [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] (the most-recently-shipped spec — the canonical voice / depth / section-layout reference for this document; its [Decision 10][spec-028] maintainer-commanded-version-bump posture is the precedent [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut) extends to a joint-cut boundary); [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] (the filter subsystem whose `_validate_filterset_class` validator at [`django_strawberry_framework/types/base.py::_validate_filterset_class`][base] is the structural template for Slice 3's `Meta`-key validation); [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] (the [Schema export management command][glossary-schema-export-management-command] whose [`Command`][export-schema-cmd] shape Slice 2's `inspect_django_type` command mirrors); [`docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019] (the [Scalar field override semantics][glossary-scalar-field-override-semantics] this card's Slice 3 must compose with — a consumer-authored annotation already controls a field's nullability and must not be silently re-overridden); [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-015] (the Relay-Node pk-suppression branch in [`_build_annotations`][base] that Slice 3's scalar-resolution path threads alongside). [`docs/GLOSSARY.md`][glossary] has **no entry yet** for `Meta.nullable_overrides`, `Meta.required_overrides`, or the `inspect_django_type` command; their entries are created during implementation (per [Doc updates](#doc-updates)) and are flagged in [Risks and open questions](#risks-and-open-questions) as the missing-glossary-heading caveat.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Pinned the canonical spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)) over the card body's stale `docs/spec-021-nullable_overrides-0_0_8.md` reference; the single-spec-covers-all-three-slices scope ([Decision 2](#decision-2--one-spec-covers-all-three-slices)); the `extensions=` instance→factory-callable migration shape ([Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form), reshaped in Revision 2); the `inspect_django_type` command shape and argument-resolution contract ([Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)); the two-key tuple-set override form over a dict-of-name shape ([Decision 5](#decision-5--two-key-tuple-set-override-form)); the net-new `ALLOWED_META_KEYS` landing (NOT a `DEFERRED_META_KEYS` promotion) ([Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)); the tri-state `force_nullable` seam threaded through [`convert_scalar`][converters] ([Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)); the validation and collision behavior — `Meta.exclude` interaction, both-sets collision, consumer-authored interaction ([Decision 8](#decision-8--override-validation-and-collision-behavior)); the choice-field interaction ([Decision 9](#decision-9--choice-field-interaction)); the scalar-only scope with relation-field overrides rejected and deferred ([Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)); the joint-`0.0.9`-cut version-bump boundary ([Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)); and the slice-independence / Slice-3 carve-off contingency ([Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)). Conflicts called out in [Risks and open questions](#risks-and-open-questions): the card body's stale `spec-021-nullable_overrides-0_0_8` filename, its `## [0.0.8]` CHANGELOG-heading references, and its `examples/fakeshop/tests/test_commands.py` test path (no such file exists; the on-disk convention is one file per command).
- **Revision 2** — feedback pass over rev1 captured in [`docs/feedback.md`][feedback]. Four P1 (foundational) + four P2 + one P3 findings applied; the P1s reshaped Slices 1–3 materially.
  - **P1 (beyond the feedback) — Slice 1 plan-cache conflict.** Source-reading surfaced that [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]'s [Plan cache][glossary-plan-cache] is instance-bound ([`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004] + the `# instance!` docstring), so the card's instance→class/factory migration would regress the async cache. [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) rewritten: keep the instance form, document why, defer the migration until the cache is relocated; Problem statement, Current state, Goals, Borrowing posture, User-facing API, Slice checklist, Implementation plan, Test plan, Edge cases, DoD, Risks, and Out of scope all updated.
  - **P1 — inspect read source.** [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) now reads the resolved annotation from `origin.__annotations__` (authoritative — reflects overrides + consumer authorship + resolved relations) and uses `selected_fields` / `field_map` only for Django-side metadata + converter classification; re-running `convert_scalar` for nullability is explicitly rejected. Reconciled with [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar) / [Non-goals](#non-goals).
  - **P1 — finalized-state semantics.** `__django_strawberry_definition__` is assigned at registration (before finalize); finalization is the `DjangoTypeDefinition.finalized` flag. [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) now has two distinct error branches (`definition is None` vs `not definition.finalized`); Edge cases + Test plan + DoD updated.
  - **P1 — Slice 3 validation flow.** [Decision 8](#decision-8--override-validation-and-collision-behavior) split into three stages (`_validate_meta` shape/normalize/collision → `__init_subclass__` target-validation → `_build_annotations` apply); the rev1 single-helper-from-`_validate_meta` signature was not implementable (`_validate_meta` runs before field selection / consumer-authored computation / Relay suppression).
  - **P2 — dotted-path resolution.** Pinned Django's `import_string` (not Strawberry's `import_module_symbol`, which uses the `module:symbol` selector form) per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution).
  - **P2 — bare-name ambiguity.** First-class `CommandError` on a non-unique `__name__` via `registry.iter_types()`; package-internal coverage added.
  - **P2 — live-HTTP host.** Pinned a dedicated acceptance-only secondary `DjangoType` on `library.Book` (`Meta.primary = False`, `BookType` marked primary), avoiding mutation of the `scalars` app's baseline assertions; the [`Meta.primary`][glossary-metaprimary] interaction is part of the plan.
  - **P2 — CSV honesty.** [DoD](#definition-of-done) item 1 now states the companion CSV is intentionally incomplete on the three net-new symbols until their glossary headings land.
  - **P3 — inspect example field.** The illustrative output + happy-path test switched from the non-existent `PatronType.membership_status` to real `BookType` fields (`title` / `subtitle` / `circulation_status` / `shelf` / `genres` / `loans`).
- **Revision 3** — second feedback pass (review of rev2) captured in [`docs/feedback.md`][feedback], verified against the **locked Strawberry `0.316.0`** and source. The conclusions held; the *mechanism* under Decision 3 and three downstream claims were corrected.
  - **P1.1 — stale extension-lifecycle model.** The `_sync_extensions` / `_async_extensions` split (from spec-004's 2026-04-30 spike) no longer exists in 0.316.0; `Schema.get_extensions` runs `[ext if isinstance(ext, SchemaExtension) else ext()]` **per request** in both modes. [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) re-derived against 0.316.0 and pinned to the locked version; Problem statement, Current state, Goals, Borrowing posture, Risks, and the Key-glossary-references bullets all updated.
  - **P1.2 — the instance form DOES warn.** 0.316.0 emits a `DeprecationWarning` at `Schema.__init__` for any instance ("will be removed"); rev2's "no `DeprecationWarning` to chase" claim was false. Corrected in the Slice 1 test plan + DoD item 4 (a no-warning assertion now pins its removal).
  - **P1.3 — the singleton-factory resolves the conflict.** `_optimizer = DjangoOptimizerExtension(); extensions=[lambda: _optimizer]` preserves the instance-bound [Plan cache][glossary-plan-cache] (same singleton per request) AND emits no warning (the entry is a callable). [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) now **adopts** it — Slice 1 flips from rev2's "keep the instance form" to "migrate to the singleton-factory"; plan-cache relocation is no longer a prerequisite (a non-blocking [Out of scope](#out-of-scope-explicitly-tracked-elsewhere) note). User-facing API, Slice checklist, Implementation plan, Doc updates, and Edge cases updated.
  - **P2.1 — Relay-suppressed pk.** [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)'s `origin.__annotations__` read would `KeyError` on the suppressed pk; added the interface-sourced `GlobalID!` special-case + a `test_inspect_relay_node_pk_row` test.
  - **P2.2 — `BookType` is not Relay-shaped.** The illustrative `id → GlobalID!` row was wrong; fixed to `id → Int!`, added the `GenreType` Relay-pk note, and pinned the non-Relay-pk assertion in `test_inspect_by_registered_name`.
  - **P2.3 — cold CLI invocation.** As specified the command never finalized the registry; added the `--schema <dotted_path>` import (mirroring `export_schema`) + `test_inspect_with_schema_option`, and made the unfinalized `CommandError` name `--schema`.
  - **P2.4 — schema-wide assertions.** Added a verification step to the Slice 3 test plan; verified (grep) that `test_query/` carries no full-SDL-snapshot or type-count assertion, so the new acceptance type disturbs nothing.
  - **P3.1 — wording.** Softened "NEXT.md forbids creating glossary entries" to "NEXT.md Step 7 defers glossary anchoring."
- **Revision 4** — third feedback pass (review of rev3) captured in [`docs/feedback.md`][feedback]. The rev3 verdict confirmed every rev2 fix correct; this pass fixes the one new correctness problem the singleton-factory pivot introduced, plus two stale cross-references.
  - **P1 (new) — per-site granularity, not per-file.** Rev3's "one module-level `_optimizer` per file" would break [`tests/optimizer/test_extension.py`][test-extension]'s cache tests (a shared instance pollutes per-test `cache_info()` counters → order-dependent failures) and cannot carry per-site `strictness=` ([`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection] mixes `strictness="raise"` and the default in one module). [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form), the Slice 1 checklist, and DoD item 2 now say **per construction site** — function-local `lambda: ext` where a test holds the instance, module-level only where there is one schema per module. The migration target was widened to the **named** `extensions=[ext]` form too (which also trips the deprecation warning), so DoD item 4's "warning is gone" is achievable.
  - **P2 — stale Out-of-scope cross-ref.** The Out-of-scope `DjangoConnectionField` bullet still said "present the instance form too"; rewritten to the singleton-factory, mirroring the Key-glossary-references bullet.
  - **P3 — polish.** Retitled the Slice 1 User-facing-API heading to "(the singleton-factory form)"; corrected the Non-goals "only documents" lead-in to "migrates (form only)"; added the [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme] snippet to the migration list; noted `warnings.simplefilter("always")` for the no-warning assertion.
- **Revision 5** — fourth feedback pass (review of rev4 against the released [`django_graphene_filters`][upstream-cookbook] parity baseline) captured in [`docs/feedback.md`][feedback]. The verdict confirmed the project is on track to rebuild the old package's feature set; this pass tightened five spots so later parity cards copy the correct pattern.
  - **P1 — Status paragraph.** The top Status line still said Slice 1 "keep[s] the `extensions=` instance form … migration deferred" — the opposite of the rev3/rev4 design. Rewritten to the per-construction-site singleton-factory migration.
  - **P2 — `GOAL.md` lacks the optimizer.** The north-star astronomy schema passes no `extensions=` at all, silently omitting a foundation feature the Strawberry port adds over the old package. Added `GOAL.md` to the Slice 1 doc sweep (add `DjangoOptimizerExtension` via the singleton-factory) across Current state, the Slice 1 checklist, Doc updates, and DoD item 3.
  - **P2 — "`Meta`-key dict" wording.** Two sites (Problem statement, Borrowing posture) called the override surface a dict; corrected to "two `Meta` tuple-set keys" (the decided shape per [Decision 5](#decision-5--two-key-tuple-set-override-form)).
  - **P2 — parity checkpoint.** Added a *Reference-package parity checkpoint* table to the Borrowing posture mapping each [`django_graphene_filters`][upstream-cookbook] exported surface (`AdvancedDjangoObjectType`, `AdvancedFilterSet` / `RelatedFilter`, `AdvancedOrderSet` / `RelatedOrder`, `AdvancedDjangoFilterConnectionField`, `AdvancedFieldSet`, `AdvancedAggregateSet` / `RelatedAggregate`, `apply_cascade_permissions`, the search filters) to its current package status, so the "on track" claim is auditable from inside the spec.
  - **P3 — title.** Added `Meta.required_overrides` to the title parenthetical (it was under-named) and updated the Slice-1 topic to "`extensions=` singleton-factory."
- **Revision 6** — fifth feedback pass (review of rev5, source-verified against the locked Strawberry and the released [`django_graphene_filters`][upstream-cookbook] parity baseline) captured in [`docs/feedback.md`][feedback]. Verdict: core design sound; this pass corrected the executable details before implementation.
  - **P1 — `--schema` loader.** The `--schema` option must use Strawberry's `import_module_symbol(…, default_symbol_name="schema")` (like [`export_schema.py`][export-schema-cmd]), NOT `import_string` — `import_string("config.schema")` reads a `schema` *attribute* off the empty `config` package and fails. [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) now pins `import_module_symbol` for `--schema` (both `config.schema` and `config.schema:schema` forms), keeps `import_string` for the dotted *type* argument only, and dispatches on the dot (a dotted import failure raises `CommandError` with the original error rather than masking it behind a registry miss). The Slice 2 test plan exercises both selector forms.
  - **P1 — order-dependent bare-name tests.** Bare-name `call_command("inspect_django_type", "BookType")` only works after `config.schema` is imported + finalized. The Slice 2 test plan now runs bare-name tests under a registry-clear + reload fixture (mirroring the fakeshop reload pattern) and keeps a separate cold-path `--schema` test; bare-name is documented as a post-schema-import convenience.
  - **P2 — Slice 1 migration count + audit + `GOAL.md`.** Corrected the stale "~24" estimate: an `rg 'extensions=\['` audit finds **48** schema-construction entries across the 5 package test files (incl. two `_CaptureExt(DjangoOptimizerExtension)` subclass instances a `DjangoOptimizerExtension()`-literal grep misses). Current state, Decision 3, the Slice 1 checklist + code-sites item, the implementation-plan table (now including `GOAL.md`), and DoD item 2 updated to audit *every* `extensions=[...]` entry.
  - **P2 — `required_overrides` data safety.** Fakeshop seeds `Book(subtitle=None)`, so the SDL-only test could pass while a `subtitle` query violates the `String!` contract. The acceptance resolver now returns `Book.objects.exclude(subtitle__isnull=True)`, a live data-query test asserts no `errors`, and a new Edge case documents that `required_overrides` changes the GraphQL contract, not the column or runtime values.
  - **P3 — raw line numbers.** Replaced the Current-state section's raw `(line N)` source references with counts + substring / symbol references, per the standing-doc reference convention.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoType`][glossary-djangotype] — the model-backed Strawberry type all three slices touch. Slice 2 introspects its [`DjangoTypeDefinition`][definition]; Slice 3 adds two new `Meta` keys to its surface; Slice 1 migrates its `extensions=` construction snippet to the singleton-factory form.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the schema extension whose `extensions=[DjangoOptimizerExtension()]` construction Slice 1 migrates to the module-level-singleton factory `extensions=[lambda: _optimizer]`, which preserves its instance-bound [Plan cache][glossary-plan-cache] and drops Strawberry 0.316.0's instance-form `DeprecationWarning`, per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form).
- [Plan cache][glossary-plan-cache] — the optimizer's per-request plan cache; **instance-bound** (`self._plan_cache`), which is why Slice 1 uses a singleton-factory (one shared `_optimizer`) rather than the bare class or a constructing factory ([Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)).
- [Strictness mode][glossary-strictness-mode] — the optimizer's `strictness` constructor argument; under [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) a `strictness=` site declares the module-level singleton `_optimizer = DjangoOptimizerExtension(strictness=...)` and passes `extensions=[lambda: _optimizer]`.
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

- [`DjangoConnectionField`][glossary-djangoconnectionfield] — the central read-side primitive being built by the sibling [`WIP-ALPHA-030-0.0.9`][kanban] card. The card body lists it as a dependency of Slice 1; under [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) Slice 1 migrates the `extensions=` instance form to the singleton-factory, so the connection field's new schema-construction surfaces should present the same singleton-factory form.
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

- [ ] Slice 1: migrate `extensions=` construction sites to the singleton-factory form (per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form))
  - [ ] Rewrite **every** instance-form `extensions=` entry — anonymous `[DjangoOptimizerExtension()]`, **named** (`ext = DjangoOptimizerExtension(); extensions=[ext]`), and the bare class `[DjangoOptimizerExtension]` — to a factory over a singleton **scoped to that construction site**: `extensions=[lambda: <instance>]`. This preserves the instance-bound [Plan cache][glossary-plan-cache] (same instance per request under 0.316.0's `get_extensions`) AND drops the `Schema.__init__` instance-form `DeprecationWarning`. Do NOT use the bare class or a constructing-`lambda` `lambda: DjangoOptimizerExtension()` (re-instantiated per request → cold cache, both modes, and a cache-hit-test failure).
  - [ ] Code sites — **per construction site, not per file** (per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)); audit the whole set with `rg 'extensions=\[' <files>` (≈48 entries across the 5 package test files), wrapping **every** entry — anonymous, named `ext`, `strictness=`, bare class, and the two `_CaptureExt()` **subclass** instances in [`tests/optimizer/test_extension.py`][test-extension] (a `DjangoOptimizerExtension()`-literal grep misses these): in [`tests/optimizer/test_extension.py`][test-extension] (41) the cache tests keep their **function-local** `ext` and wrap it `extensions=[lambda: ext]` (a shared module-level instance would pollute per-test `cache_info()` counters); [`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection] (3) keeps each site's instance including the `strictness="raise"` one (one module-level instance cannot carry two strictness values); same per-site wrap for [`tests/optimizer/test_field_meta.py`][test-field-meta] (1) / [`tests/test_list_field.py`][test-list-field] (2) / [`tests/types/test_generic_foreign_key.py`][test-generic-fk] (1) / [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db] (1). The example schema [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] (currently the bare class — a cold-cache regression under 0.316.0) and [`TODAY.md`][today] (class form) have one schema per module, so a module-level `_optimizer` is right there.
  - [ ] Consumer-doc snippets: rewrite the `extensions=[DjangoOptimizerExtension()]` schema-construction snippets in [`docs/README.md`][docs-readme] and [`docs/GLOSSARY.md`][glossary] to the module-level-singleton factory form (one schema per snippet), with a one-line "module-level singleton wrapped in a factory — preserves the instance-bound [Plan cache][glossary-plan-cache], no deprecation warning" note. Migrate the [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme] prose snippet too (prose, not test-breaking, but kept consistent).
  - [ ] Bring the [`GOAL.md`][goal] astronomy schema into the sweep: it currently constructs `strawberry.Schema(query=Query, config=strawberry_config())` with **no** `extensions=` at all, so the north-star recipe omits a foundation feature this Strawberry port adds over the old Graphene package — Slice 1 adds `DjangoOptimizerExtension` via the singleton-factory (`_optimizer = DjangoOptimizerExtension(); … extensions=[lambda: _optimizer]`) so the feature-complete example shows the optimized boundary the [`DjangoConnectionField`][glossary-djangoconnectionfield] / Relay cards inherit by default.
  - [ ] [`CHANGELOG.md`][changelog]: append a `### Changed` bullet under `[Unreleased]` recording the migration to the singleton-factory `extensions=` form (preserves the plan cache, removes Strawberry's instance-form `DeprecationWarning`). No version-heading promotion (per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).
- [ ] Slice 2: `inspect_django_type` diagnostic command
  - [ ] Ship [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] with module + class docstring, `add_arguments` registering a positional `type` argument, and `handle` printing the resolved per-field table per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution). The command resolves its argument as a dotted import path first, then falls back to a registry-name lookup; reads `target.__django_strawberry_definition__` (the [`DjangoTypeDefinition`][definition] populated by [`finalize_django_types`][glossary-finalize_django_types]); and prints, per selected field: Django field name → Django field type → resolved GraphQL scalar / type → nullability → which converter row fired ([`SCALAR_MAP`][converters] entry name, choice-enum, or relation converter).
  - [ ] `CommandError` for: an unresolvable argument (neither an importable dotted path nor a uniquely-registered type name); an **ambiguous bare name** (≥2 registered types share the `__name__` — list candidates); a resolved symbol that is not a [`DjangoType`][glossary-djangotype] subclass; a `DjangoType` with **no `__django_strawberry_definition__`** (abstract / no-`Meta` base); and a `DjangoType` whose **`definition.finalized is False`** (`finalize_django_types()` has not run) — the last two are distinct branches per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution). Mirrors the [`export_schema.py`][export-schema-cmd] `CommandError` discipline.
  - [ ] Example happy-path coverage: [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (new). Bare-name `call_command("inspect_django_type", "BookType")` assertions run under a **registry-clear + reload fixture** (clear the registry, reload `apps.library.schema` + `config.schema`) so they are order-independent; a separate **cold-path** test (no fixture, cleared registry) uses `call_command("inspect_django_type", "BookType", "--schema", "config.schema")` to prove `--schema` finalizes on its own, and exercises both the `config.schema` and `config.schema:schema` selector forms. Assert the printed table names every selected field with its resolved scalar and nullability (including the `circulation_status` choice row). (The card body names `examples/fakeshop/tests/test_commands.py`; no such file exists — see [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) and [Risks and open questions](#risks-and-open-questions). The new file mirrors the one-file-per-command convention at [`examples/fakeshop/tests/test_export_schema.py`][fakeshop-tests-export].)
  - [ ] Package-internal failure-mode coverage: [`tests/management/test_inspect_django_type.py`][test-management-inspect] (new) for the `CommandError` paths not reachable from a live registered type (bad dotted path, non-`DjangoType` symbol, unfinalized type), mirroring [`tests/management/test_export_schema.py`][test-management-export].
  - [ ] [`docs/GLOSSARY.md`][glossary] adds a `## Schema introspection management command` (or `## inspect_django_type`) entry; [`docs/TREE.md`][tree] lists `inspect_django_type.py` under `management/commands/`. [`CHANGELOG.md`][changelog]: `### Added` bullet under `[Unreleased]`.
- [ ] Slice 3: `Meta.nullable_overrides` / `Meta.required_overrides`
  - [ ] [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] grows `"nullable_overrides"` and `"required_overrides"` (net-new public keys — NOT a `DEFERRED_META_KEYS` promotion, per [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)). Validation splits across the three-stage flow per [Decision 8](#decision-8--override-validation-and-collision-behavior): [`_validate_meta`][base] shape-checks the two tuples, normalizes them onto `_ValidatedMeta`, and raises the both-sets collision; a `_validate_nullability_override_targets(...)` helper runs in [`__init_subclass__`][base] **after** `_select_fields` + `consumer_authored_fields` + the Relay-shape check to reject unknown / excluded / consumer-authored / relation / Relay-pk targets.
  - [ ] [`django_strawberry_framework/types/converters.py::convert_scalar`][converters] grows a keyword-only `force_nullable: bool | None = None` tri-state per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar): `None` honors `field.null` (unchanged default); `True` emits `T | None` regardless; `False` emits `T` (non-null) regardless. The widening decision is computed once from `effective_null = field.null if force_nullable is None else force_nullable` and applied uniformly across the `ArrayField` / `HStoreField` / choice / scalar branches.
  - [ ] [`_build_annotations`][base]'s scalar branch ([`base.py`][base] #"annotations[field.name] = convert_scalar(field, cls.__name__)") computes `force_nullable` for each field from the two override sets (`True` if in `nullable_overrides`, `False` if in `required_overrides`, `None` otherwise) and passes it to `convert_scalar`.
  - [ ] Validation per [Decision 8](#decision-8--override-validation-and-collision-behavior): a name in either set must (a) exist on the model, (b) be in the selected field set (not excluded via [`Meta.exclude`][glossary-metaexclude]), (c) NOT be consumer-authored (an annotation / `strawberry.field` override already controls nullability per [Scalar field override semantics][glossary-scalar-field-override-semantics]), (d) NOT be a relation field (scalar-only scope per [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)), and (e) NOT be the Relay-Node-suppressed pk. A field named in **both** sets raises [`ConfigurationError`][glossary-configurationerror] at the shape-check stage (contradictory). Every failure raises [`ConfigurationError`][glossary-configurationerror] at type-creation time naming the offending field.
  - [ ] Package coverage: [`tests/types/test_converters.py`][test-converters] (the `force_nullable` tri-state across scalar / nullable / choice / Array / HStore shapes) + [`tests/types/test_base.py`][test-types-base] (the validation + collision cases: unknown field, excluded field, consumer-authored field, relation field, both-sets collision, override-applies).
  - [ ] Live HTTP coverage: add a **dedicated acceptance-only secondary `DjangoType`** over the [`library`][fakeshop-library-models] `Book` model in [`apps/library/schema.py`][fakeshop-library-schema] (e.g. `NullabilityOverrideBookType`, `Meta.primary = False`) declaring `nullable_overrides = ("title",)` (non-null → nullable) and `required_overrides = ("subtitle",)` (nullable → non-null), and mark the existing `BookType` `Meta.primary = True` to satisfy the [`Meta.primary`][glossary-metaprimary] one-primary rule. **`required_overrides` declares `subtitle` as `String!`, but fakeshop seeds `Book` rows with `subtitle=None`** (e.g. in [`test_library_api.py`][fakeshop-test-library]), so the dedicated root resolver MUST return only rows satisfying the declared invariant — `Book.objects.exclude(subtitle__isnull=True)` — or a `subtitle` query hits a Strawberry non-null violation (the override changes the GraphQL contract, NOT the column or the data). Two live tests in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]: (a) introspect the acceptance type's SDL and assert `title` flipped `String!` → `String` and `subtitle` flipped `String` → `String!` while the `Book` columns are unchanged; (b) a **data query** against the dedicated root field requesting `title` + `subtitle` over the non-null-subtitle rows, asserting `errors` is absent (proves the exposed API is queryable, per the fakeshop live-query rule). The existing `BookType` and the [`scalars`][fakeshop-scalars-models] app's types / assertions are untouched.
  - [ ] [`docs/GLOSSARY.md`][glossary] adds `## Meta.nullable_overrides` and `## Meta.required_overrides` entries; [`CHANGELOG.md`][changelog]: `### Added` bullet under `[Unreleased]`.
- [ ] Card-completion wrap (lands when all three slices ship; NOT a code slice)
  - [ ] [`KANBAN.md`][kanban]: move [`WIP-ALPHA-029-0.0.9`][kanban] to the Done column with the next available `DONE-NNN-0.0.9` id; add / confirm the card body's `Spec:` reference points at [`docs/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (this document).
  - [ ] **No version-file edits in this card.** Leave `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` to the joint `0.0.9` cut per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut).
  - [ ] If the schedule forces Slice 3 to defer, carve it off as its own follow-up card (`docs/spec-029b-nullable_overrides-0_0_9.md` or a renumbered successor) without disrupting Slices 1 + 2 per [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency).

## Problem statement

`django-strawberry-framework`'s `0.0.8` surface ships [`DjangoType`][glossary-djangotype], the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], the filtering and ordering subsystems, and the [Schema export management command][glossary-schema-export-management-command]. The `0.0.9` cohort is dominated by the [`DjangoConnectionField`][glossary-djangoconnectionfield] / full-Relay work (cards [`WIP-ALPHA-030-0.0.9`][kanban] / [`WIP-ALPHA-031-0.0.9`][kanban] / [`WIP-ALPHA-032-0.0.9`][kanban]). This card is the smallest of the four `0.0.9` cards: a three-slice **developer-experience cleanup pass** that closes three independent, small gaps before the larger connection-field surfaces land.

Each slice closes a distinct gap:

1. **Slice 1 — the `extensions=` instance form is deprecated upstream, and the package's plan cache is instance-bound.** Strawberry (locked at `0.316.0`) deprecated `extensions=[SomeExtension()]` (the instance form) and emits a `DeprecationWarning` for it; the card wants the migration to the class / factory form. But [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]'s [Plan cache][glossary-plan-cache] lives on the instance, and under 0.316.0 the bare class / constructing-`lambda` are re-instantiated per request (cold cache, both sync and async). The form that satisfies both constraints is a **module-level-singleton factory** — `_optimizer = DjangoOptimizerExtension(); extensions=[lambda: _optimizer]` — which keeps one shared instance (cache preserved) AND silences the deprecation warning (the tuple holds a callable, not an instance). [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) adopts it: Slice 1 migrates the instance-form sites to the singleton-factory, with no plan-cache relocation needed. This is the defensive slice — the card's migration, done in the one form that doesn't regress the cache.
2. **Slice 2 — there is no type-definition diagnostic.** Neither [`graphene-django`][graphene-django] nor [`strawberry-graphql-django`][strawberry-django] ships an equivalent `manage.py inspect_*` diagnostic for its type definitions. Consumers debugging "why did this field resolve to that GraphQL type?" currently introspect by hand against the constructed GraphQL schema, *after* schema construction. A `manage.py inspect_django_type <TypeName>` command moves that diagnostic to the type-definition layer — it walks a [`DjangoTypeDefinition`][definition] and prints, per field, the Django field → resolved scalar → nullability → which converter fired. This is the differentiating slice (capability neither upstream has).
3. **Slice 3 — GraphQL nullability is welded to the Django column.** Today a field's GraphQL nullability is exactly `field.null`: a non-null column renders as `T!`, a nullable column as `T`. Consumers routinely need to decouple the two — render a non-null column as nullable in GraphQL (a field that is `NOT NULL` in the DB but legitimately absent from a partial response), or render a nullable column as required in GraphQL (a column that is `null=True` for legacy-migration reasons but always populated in practice). [`strawberry_django.field(required=True/False)`][strawberry-django] allows exactly this per-field override against the Django column's native nullability; [`graphene-django`][graphene-django] allows the same via per-field overrides on the `DjangoObjectType`. The only escape hatches the package offers today are an `AlterField` migration (changes the database) or a consumer-authored annotation override (forces the consumer to hand-write the scalar annotation and lose the converter's choice-enum / [`BigInt`][glossary-bigint-scalar] / array resolution). This slice surfaces the same capability through two `Meta` tuple-set keys (`Meta.nullable_overrides` / `Meta.required_overrides`), consistent with the rest of the package's `Meta`-shaped API. This is the ⚛️&🍓-required slice and the one carrying the open design questions; it is the design core of this spec.

The three slices share no implementation surface — Slice 1 is a mechanical sweep over already-shipped code, Slice 2 is a strict reader of the existing introspection surface, and Slice 3 plugs into the scalar-resolution path at type-construction time. They ship in any order; the card completes when all three land (or Slice 3 carves off per [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)).

## Current state

A true description of the repo as of this writing (the plan is written against it):

- [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] = `{"description", "exclude", "fields", "filterset_class", "interfaces", "model", "name", "optimizer_hints", "orderset_class", "primary"}`; [`DEFERRED_META_KEYS`][base] = `{"aggregate_class", "fields_class", "search_fields"}`. Neither `nullable_overrides` nor `required_overrides` exists in either set; declaring either today raises [`ConfigurationError`][glossary-configurationerror] via the unknown-key typo guard at [`_validate_meta`][base].
- [`django_strawberry_framework/types/base.py`][base] ships `_validate_filterset_class` and `_validate_orderset_class` — both use a local in-function import to dodge the `types → {filters,orders} → types` module-load cycle and raise [`ConfigurationError`][glossary-configurationerror] for a non-subclass value. They are the structural template for Slice 3's new `_validate_nullability_overrides` helper.
- [`_build_annotations`][base]'s scalar branch calls `convert_scalar(field, cls.__name__)` for every selected, non-relation, non-consumer-authored, non-pk-suppressed field. Consumer-authored fields (`field.name in consumer_authored_fields`) and the Relay-Node-suppressed pk `continue` past `convert_scalar` entirely.
- [`django_strawberry_framework/types/converters.py::convert_scalar`][converters] takes `(field, type_name)`; its final widening step is `if field.null: py_type = py_type | None`. The `ArrayField` and `HStoreField` branches return early but each widens on `field.null` independently. There is no nullability-override parameter today.
- [`DjangoTypeDefinition`][definition] (on `cls.__django_strawberry_definition__` after [`__init_subclass__`][base]) carries `selected_fields: tuple[models.Field, ...]`, `field_map: dict[str, FieldMeta]`, the four `consumer_*_fields` frozensets, `filterset_class` / `orderset_class` slots, and `finalized: bool`. [`FieldMeta`][field-meta] carries `name`, `is_relation`, the cardinality flags, `nullable`, `related_model`, `attname`, and the FK target columns — the read surface Slice 2's command prints from. There is no `nullable_overrides` / `required_overrides` slot yet (Slice 3 does NOT need one — the override resolves to an annotation at construction time; it does not need to persist on the definition).
- [`django_strawberry_framework/management/commands/export_schema.py`][export-schema-cmd] is the only shipped management command; it is the structural model for Slice 2's `inspect_django_type` command (`add_arguments` with a positional, `handle`, `CommandError` for the failure modes). Its dotted-path resolution uses Strawberry's `import_module_symbol` (the `module:symbol` selector form, with a default symbol name) — Slice 2 instead uses Django's `import_string` for fully-dotted `a.b.c.Symbol` paths per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution). There is **no** `inspect_django_type.py` on disk.
- Instance-form `extensions=[...]` schema-construction sites exist across the package and docs — **more than the card's affected-files list names**. A current audit (`rg -c 'extensions=\[' <file>`) finds **48 actual schema-construction entries across the five package test files**: [`tests/optimizer/test_extension.py`][test-extension] (41, after subtracting one prose/docstring example — *including two `_CaptureExt(DjangoOptimizerExtension)` subclass instances*, at [`test_extension.py`][test-extension] #"extensions=[_CaptureExt()]", that a `DjangoOptimizerExtension()`-literal grep would miss), [`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection] (3, one with `strictness="raise"`), [`tests/optimizer/test_field_meta.py`][test-field-meta] (1), [`tests/test_list_field.py`][test-list-field] (2), [`tests/types/test_generic_foreign_key.py`][test-generic-fk] (1); plus [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db] (1), [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] (1, bare class), [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme] (prose), and the consumer-doc snippets in [`docs/README.md`][docs-readme] / [`docs/GLOSSARY.md`][glossary]. [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] and [`TODAY.md`][today] use the bare class form; [`GOAL.md`][goal]'s astronomy `strawberry.Schema(...)` carries **no `extensions=` argument at all** — the north-star recipe silently omits the optimizer, which Slice 1 corrects (the feature-complete example should show the optimized boundary the connection-field cards inherit). **The migration audit must target every `strawberry.Schema(..., extensions=[...])` entry** — anonymous `DjangoOptimizerExtension()`, named `ext`, `strictness=` variants, the bare class, AND subclass instances like `_CaptureExt()` — not just `DjangoOptimizerExtension()` literals; a naive `grep -rn "DjangoOptimizerExtension()" .` both **misses** subclass instances AND **matches** legitimate direct calls (`ext = DjangoOptimizerExtension()`, `DjangoOptimizerExtension().plan_relation(...)`) plus CHANGELOG / archived-spec prose, so it is **not** a valid migration gate.
- The `DjangoOptimizerExtension` [Plan cache][glossary-plan-cache] is **instance-bound** (`self._plan_cache`). Under the locked Strawberry `0.316.0`, `Schema.get_extensions` runs `ext if isinstance(ext, SchemaExtension) else ext()` **per request** (both sync and async): a passed-in instance is reused (cache preserved) but `Schema.__init__` emits a `DeprecationWarning`; a bare class or constructing-`lambda` is re-instantiated per request (cold cache); a `lambda` closing over a module-level singleton reuses one instance (cache preserved) and emits no warning. [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) adopts the singleton-factory. The old `_sync_extensions` / `_async_extensions` model from spec-004 (2026-04-30) no longer exists in 0.316.0 — claims are pinned to the locked version.
- [`docs/GLOSSARY.md`][glossary] has no heading for `Meta.nullable_overrides`, `Meta.required_overrides`, or the inspect command; the three new glossary entries are authored during implementation (per [Doc updates](#doc-updates)) and flagged in [Risks and open questions](#risks-and-open-questions).
- The [`library`][fakeshop-library-models] `Book` model carries both a non-null scalar (`title = TextField()`) and a nullable scalar (`subtitle = TextField(blank=True, null=True)`) plus a choice field (`circulation_status`), making it the host for Slice 3's live-HTTP nullability flip (both directions on one model) and the `inspect_django_type` choice-row example. The existing `BookType` in [`apps/library/schema.py`][fakeshop-library-schema] is the only `DjangoType` on `Book` today; Slice 3 adds a **dedicated acceptance-only secondary type** rather than mutating `BookType` or the [`scalars`][fakeshop-scalars-models] app's `ScalarSpecimenType` / `NullableScalarSpecimenType` (whose live tests pin baseline non-null / nullable / all-null wire-format behavior that must not change). The [`Meta.primary`][glossary-metaprimary] multi-type rule applies (exactly one primary must be declared); the plan marks `BookType` primary and the acceptance type `Meta.primary = False` — see [Test plan](#test-plan).

## Goals

1. Migrate `DjangoOptimizerExtension`'s instance-form construction sites to the module-level-singleton factory `extensions=[lambda: _optimizer]`, which preserves the instance-bound [Plan cache][glossary-plan-cache] AND drops Strawberry 0.316.0's instance-form `DeprecationWarning`; reject the bare class / constructing-`lambda` (cold cache per request). No plan-cache relocation required (Slice 1, per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)).
2. Ship a `manage.py inspect_django_type <Type>` diagnostic command that walks a [`DjangoTypeDefinition`][definition] and prints the per-field resolution table, with `CommandError` for every failure mode, mirroring the shipped [Schema export management command][glossary-schema-export-management-command] (Slice 2).
3. Ship `Meta.nullable_overrides` and `Meta.required_overrides` as net-new public `Meta` keys that decouple a scalar field's GraphQL nullability from its Django column without an `AlterField` migration or a consumer-authored annotation, validated at type-creation time, composing cleanly with [`Meta.exclude`][glossary-metaexclude], [Choice enum generation][glossary-choice-enum-generation], and [Scalar field override semantics][glossary-scalar-field-override-semantics] (Slice 3).
4. Earn package coverage through live fakeshop HTTP flows (Slice 3's nullability flip on a dedicated acceptance-only `DjangoType` over the [`library`][fakeshop-library-models] `Book` model — which carries both a non-null and a nullable scalar column) and in-process `call_command` tests (Slice 2), per [`docs/TREE.md`][tree]'s coverage-priority rule; the package coverage gate (`fail_under = 100`) is reached because those tests exercise the package end-to-end.
5. Keep package version state command-gated and owned by the joint `0.0.9` cut: no slice in this card edits `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], `uv.lock`, or promotes a CHANGELOG release heading (see [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Non-goals

- **Relation-field nullability override.** Forward-FK / OneToOne nullability override (`TargetType | None` ↔ `TargetType`) and reverse-FK / M2M list nullability override (`[T!]` ↔ `[T!]!`) are out of scope for `0.0.9`; Slice 3's overrides are scalar-column-only and reject a relation override-target with [`ConfigurationError`][glossary-configurationerror] (see [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)). The list-vs-element nullability ambiguity on the many-side is its own design space.
- **`DjangoListField` / `DjangoConnectionField` argument injection.** Slice 1 migrates the construction snippet (form only); it does not add filter / order / nullability arguments to any field. Those compose in the connection-field cohort.
- **A `--watch` / `--json` / SDL-diff mode on the inspect command.** Slice 2 ships a single human-readable table to stdout, matching the `0.0.7` `export_schema` posture (no `--watch` / `--indent` / JSON mode). Machine-readable output is a follow-up if demand surfaces.
- **Persisting overrides on `DjangoTypeDefinition`.** Slice 3 resolves the override to a final annotation written to `cls.__annotations__` at type-construction time; it does not add a `nullable_overrides` slot to [`DjangoTypeDefinition`][definition]. Nothing needs one — the resolved annotation on `origin.__annotations__` IS the authoritative persisted record, and that is exactly what the Slice 2 [`inspect_django_type`](#decision-4--inspect_django_type-command-shape-and-argument-resolution) command reads for post-override nullability (per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) / [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)).
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
| `AdvancedDjangoFilterConnectionField` | [`DjangoConnectionField`][glossary-djangoconnectionfield] / full Relay / [connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] | planned (`0.0.9` — [`WIP-ALPHA-030/031/032-0.0.9`][kanban]) |
| `AdvancedFieldSet` | [`FieldSet`][glossary-fieldset] | planned (`0.1.1`) |
| `AdvancedAggregateSet` / `RelatedAggregate` | [`AggregateSet`][glossary-aggregateset] / `RelatedAggregate` | planned (`0.1.3`) |
| `apply_cascade_permissions` | [`apply_cascade_permissions`][glossary-apply_cascade_permissions] (permissions subsystem) | planned (`0.0.10`) |
| `SearchQueryFilter` / `SearchRankFilter` / `TrigramFilter` + `Meta.search_fields` | Postgres search filters + [`Meta.search_fields`][glossary-metasearch_fields] | planned (`0.1.2`) |

This card touches the *foundation* under that map — the `extensions=` construction boundary the connection-field surfaces inherit (Slice 1), the type-definition introspection layer (Slice 2), and the `Meta`-key surface the override keys extend (Slice 3) — not the parity surfaces themselves.

### Slice 1 — borrow the upstream factory-callable form via a singleton to preserve the plan cache

[`strawberry-graphql-django`][strawberry-django] and the broader Strawberry ecosystem use `extensions=[SchemaExtension]` (class) or `extensions=[lambda: SchemaExtension(...)]` (factory callable); the instance form is deprecated (Strawberry 0.316.0 warns on it). The package's extension is **not** stateless — it carries a per-instance [Plan cache][glossary-plan-cache] — so a bare class or a *constructing* factory would reset the cache every request under 0.316.0. The package therefore borrows the factory-callable shape with a twist: a factory that closes over a **module-level singleton** (`_optimizer = DjangoOptimizerExtension(); extensions=[lambda: _optimizer]`), which is the upstream-recommended callable form yet keeps one shared instance (cache preserved) and emits no deprecation warning. See [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form).

### Slice 2 — `inspect_django_type` is conceptually like Django's `inspectdb`, scoped to the framework

Django's `manage.py inspectdb` introspects a database and prints model definitions; `inspect_django_type` is the framework analogue scoped to the type-definition surface — it introspects a finalized [`DjangoTypeDefinition`][definition] and prints the resolved GraphQL field table. Neither [`graphene-django`][graphene-django] (which ships `manage.py graphql_schema`, an SDL export) nor [`strawberry-graphql-django`][strawberry-django] (which ships `export_schema`, mirrored by this package's [Schema export management command][glossary-schema-export-management-command]) ships a type-definition introspection command. The structural model to borrow is the package's own [`export_schema.py`][export-schema-cmd] `Command` shape (`add_arguments` / `handle` / `CommandError`), not an upstream command.

### Slice 3 — borrow the *capability* of `strawberry_django.field(required=...)`, not its surface

[`strawberry_django.field(required=True/False)`][strawberry-django] lets a consumer override a single field's GraphQL nullability against the Django column's native nullability; [`graphene-django`][graphene-django] allows the same via per-field overrides declared on the `DjangoObjectType` class body. Both are **field-level decorator / assignment surfaces**. The package's [`START.md`][start] "Meta classes everywhere on consumer surfaces" rule forbids that shape for consumer-facing declarations — so the package borrows the *capability* (decouple GraphQL nullability from the column) and re-expresses it as two `Meta` tuple-set keys (`Meta.nullable_overrides` / `Meta.required_overrides`, each a tuple/list of field names — NOT a dict; see [Decision 5](#decision-5--two-key-tuple-set-override-form)), consistent with [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]. What is **not** borrowed: the per-field `field(required=...)` call site (that is the strawberry-django decorator shape the package exists to replace), and the implicit "the annotation declares the override" coupling (the package keeps the converter authoritative and layers the override on top — see [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)).

## User-facing API

### Slice 1 — `extensions=` construction (the singleton-factory form)

```python
import strawberry
from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types, strawberry_config

finalize_django_types()

# Recommended (Strawberry 0.316.0): a module-level SINGLETON wrapped in a factory.
# `get_extensions` runs the callable per request and gets the same `_optimizer`
# back, so the instance-bound plan cache is preserved (both sync and async); and
# because the `extensions` entry is a callable (not an instance), Schema.__init__
# does NOT emit the instance-form DeprecationWarning.
_optimizer = DjangoOptimizerExtension()  # one instance, one plan cache; pass strictness= here
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)

# Correct but DEPRECATED (Schema.__init__ warns "...will be removed..."):
#   extensions=[DjangoOptimizerExtension()]          # instance — cache preserved, but warns
# WRONG under 0.316.0 (re-instantiated per request → cold plan cache, both modes):
#   extensions=[DjangoOptimizerExtension]            # bare class
#   extensions=[lambda: DjangoOptimizerExtension()]  # constructing factory
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
  id                   BigAutoField         Int!                             no         SCALAR_MAP[BigAutoField]
  title                TextField            String!                          no         SCALAR_MAP[TextField]
  subtitle             TextField            String                           yes        SCALAR_MAP[TextField]
  circulation_status   CharField(choices)   BookTypeCirculationStatusEnum!   no         choice enum
  shelf                ForeignKey           ShelfType!                       no         relation: forward FK
  genres               ManyToManyField      [GenreType!]!                    no (list)  relation: M2M
  loans                reverse ForeignKey   [LoanType!]!                     no (list)  relation: reverse FK
```

`BookType` is **not** Relay-shaped (its `Meta` declares no `interfaces`), so its `id` renders as a plain `Int!` read from `origin.__annotations__`, not `GlobalID!`. A Relay-Node type — e.g. `GenreType` (`Meta.interfaces = (relay.Node,)`) — instead shows `id → GlobalID! → relay.Node id`, sourced from the interface (the pk is suppressed from `cls.__annotations__`) per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)'s suppressed-pk contract.

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

### Decision 3 — Slice 1 adopts the singleton-factory `extensions=` form

**The card frames Slice 1 as an instance→class/`lambda`-factory migration. Done naively it regresses [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]'s [Plan cache][glossary-plan-cache], which lives on the instance (`self._plan_cache`) — but the locked Strawberry offers a migration form that preserves the cache AND drops the deprecation warning, so the card's migration is doable, just not in the form the card names.**

**Mechanism, pinned to the locked version.** The package locks `strawberry-graphql == 0.316.0` (`pyproject.toml` pins `>=0.262.0`; `uv.lock` resolves `0.316.0`). The `_sync_extensions` / `_async_extensions` split that [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004]'s spike (2026-04-30) described **no longer exists** in 0.316.0 — it was refactored into one per-request accessor, `Schema.get_extensions` in `strawberry/schema/schema.py` (strawberry-graphql 0.316.0), whose body is `[ext if isinstance(ext, SchemaExtension) else ext() for ext in self.extensions]`. Both `execute()` and `execute_sync()` call it **per request**. Against 0.316.0, therefore:

- A passed-in **instance** is returned unchanged every request (the `isinstance` passthrough) — **one shared instance, plan cache preserved**, in both sync and async — BUT `Schema.__init__` emits a live `DeprecationWarning` ("Passing an extension instance to `extensions=[...]` is deprecated and will be removed in a future release. Pass the class itself, or a factory callable …").
- A **bare class** or a **constructing `lambda`** (`lambda: DjangoOptimizerExtension()`) is re-instantiated **every request, in both modes** — a cold `self._plan_cache` per request, **zero hit rate**. (spec-004's "sync is cached via `@cached_property`" reasoning is false for 0.316.0.)
- A **`lambda` that closes over a module-level singleton** — `_optimizer = DjangoOptimizerExtension(); extensions=[lambda: _optimizer]` — **resolves the conflict**: `get_extensions` runs `ext()` and gets the *same* `_optimizer` back every request (plan cache preserved, both modes), and the `extensions` tuple holds a *callable*, not a `SchemaExtension` instance, so the `any(isinstance(ext, SchemaExtension))` deprecation check in `Schema.__init__` is `False` — **no `DeprecationWarning`**. Its caching and concurrency semantics are **identical** to the bare instance (one shared instance across all requests; per-request optimizer state already lives on `ContextVar`s set in `on_execute`, not on `self`, per [`optimizer/extension.py`][optimizer-extension]), so wrapping the singleton in a factory changes nothing observable except silencing the warning.

**Decision for `0.0.9`: migrate every instance-form `extensions=[<instance>]` entry to a factory over a singleton scoped to that construction site — `extensions=[lambda: <instance>]`.** It is the modernize-without-regression form — preserves the instance-bound plan cache AND removes the (live, "will be removed") deprecation warning, with **no plan-cache relocation required**. The migration targets **every** instance entry: anonymous `[DjangoOptimizerExtension()]`, the **named** form `ext = DjangoOptimizerExtension(); extensions=[ext]` (which also trips the 0.316.0 deprecation warning), AND the bare class `[DjangoOptimizerExtension]` (a cold-cache regression under 0.316.0). **Granularity is per construction site, not per file:**

- **Consumer docs + the example [`config/schema.py`][fakeshop-config-schema]** have one schema per module, so a module-level `_optimizer = DjangoOptimizerExtension(...)` (with `strictness=` as needed) wrapped as `extensions=[lambda: _optimizer]` is right.
- **The package test modules build many schemas**, several holding a *function-local* `ext` whose `cache_info()` / `_plan_cache` a test asserts on — e.g. [`tests/optimizer/test_extension.py`][test-extension]'s `test_cache_hit_on_repeated_query` does `ext = DjangoOptimizerExtension(); … assert ext.cache_info().misses == 1`. Each such site keeps its **function-local** instance and wraps it `extensions=[lambda: ext]`. A single module-level instance shared across that file's ~41 schema-building entries would **pollute the per-test cache counters** (order-dependent failures) and could not carry per-site `strictness=` ([`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection] mixes `strictness="raise"` and the default in one module). The constructing-`lambda` `lambda: DjangoOptimizerExtension()` is rejected here too: it rebuilds per execute, so the cache-hit test's second `execute_sync` would miss.

So Slice 1 wraps **each existing instance** as `extensions=[lambda: <that site's instance>]` — function-local where a test holds the reference, module-level only where there is genuinely one schema per module. The bare instance stays correct but deprecated; the bare class / constructing-`lambda` are rejected (cold cache per request).

**The existing class-form drift is a regression today.** [`config/schema.py`][fakeshop-config-schema] and [`TODAY.md`][today] currently use the bare class form `extensions=[DjangoOptimizerExtension]` — under 0.316.0 that yields a cold plan cache on **every** request (sync included), so it is a silent regression, not "harmless in sync" as an earlier draft claimed. Slice 1 fixes both to the singleton-factory form.

Justification:

- Under 0.316.0 the singleton-factory is strictly better than the bare instance (identical caching / concurrency, no deprecation warning) and strictly better than the bare class / constructing-`lambda` (which get a cold cache every request). It is the one form that both modernizes off the deprecated instance AND preserves the optimization the card never intended to touch.
- No plan-cache relocation is needed — the singleton-factory shares one instance per process, exactly as the bare instance does.
- Pinning the mechanism to `0.316.0` (rather than spec-004's stale `_sync` / `_async` model) keeps the argument honest against the version the repo actually runs; the conclusion holds for any version with the `get_extensions` passthrough + instance-deprecation behavior.

Alternatives considered (and rejected):

- **Keep the bare instance and document why (the rev2 decision).** Rejected: correct on caching, but it leaves a live `DeprecationWarning` ("will be removed") on every schema built the documented way — and a singleton-factory form exists that keeps the caching AND silences the warning, so keeping the deprecated form is no longer the honest move.
- **Migrate to the bare class or constructing `lambda: DjangoOptimizerExtension()`.** Rejected: a cold `self._plan_cache` every request, in both modes, under 0.316.0 — regresses the optimization.
- **Relocate the plan cache off the instance to enable the bare class.** Rejected as unnecessary: the singleton-factory preserves the instance-bound cache with no optimizer change. Cache relocation is a separate, larger optimizer concern ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)) but is NOT a prerequisite for this migration.
- **Suppress the warning with `warnings.filterwarnings("ignore", …)` and keep the instance.** Rejected: hides a real upstream signal the project otherwise guards against (`tests/test_scalars.py` runs a subprocess under `-W error::DeprecationWarning`); the singleton-factory removes the warning at the source instead.

### Decision 4 — `inspect_django_type` command shape and argument resolution

The command ships at [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] as `Command(BaseCommand)`, mirroring [`export_schema.py`][export-schema-cmd]: `add_arguments` registers one positional argument (`type`) plus an optional `--schema <dotted_path>` (see *Reaching a finalized registry* below); `handle` imports the schema (when given), resolves the type, reads `target.__django_strawberry_definition__`, and prints the per-field table; `CommandError` wraps every failure.

**Argument resolution — dotted object path vs bare registered name, dispatched on the dot (not a catch-all fallback).** If the positional `type` argument **contains a dot**, it is a fully-dotted object path resolved via **`django.utils.module_loading.import_string`** (which splits on the last dot — `apps.library.schema.BookType` → module `apps.library.schema`, attribute `BookType`); an `ImportError` / `AttributeError` here raises `CommandError` carrying the **original** failure — it is **NOT** swallowed and retried as a registry lookup, because catching every import error would mask a real import-time bug inside a consumer module. If the argument has **no dot**, it is a bare type name resolved against the registry (next paragraph). This dot-dispatch reconciles the card body's two conflicting signals (the `add_arguments` note says "positional `type_dotted_path`"; the worked test example passes a bare `"BookType"`). `import_string` here resolves a fully-dotted *attribute* path; it is a different loader from the `--schema` option (see *Reaching a finalized registry*), which uses Strawberry's `import_module_symbol` exactly as [`export_schema.py`][export-schema-cmd] does.

**Bare-name lookup requires a unique `__name__` match, and is a post-schema-import convenience.** The registry can hold multiple `DjangoType` classes with the same `__name__` from different modules ([`Meta.primary`][glossary-metaprimary] multi-type, or two apps each declaring a `BookType`). The no-dot branch iterates `registry.iter_types()` and collects every registered type whose `__name__` equals the argument: **exactly one** match resolves; **zero** → `CommandError`; **two or more** → `CommandError` listing the candidates by `module.qualname` and their models, asking the consumer to pass a dotted path. The command MUST NOT return the first match by registry-iteration order — that would make the result import-order-dependent. **Bare-name resolution only works once the registry is already populated and finalized in-process** (the in-process tests via their reload fixture, or a shell where the project schema has been imported); it is explicitly a convenience for an already-loaded schema, **not** a cold-CLI path — a bare name in a cold process has an empty registry → "unresolvable". A cold CLI invocation passes `--schema` (next paragraph). The ambiguity branch has package-internal coverage (see the [Test plan](#test-plan)).

**Output contract — the resolved annotation is read from `origin.__annotations__`, not re-derived.** The authoritative resolved GraphQL annotation for a finalized type lives on `definition.origin.__annotations__` (`origin` is the `DjangoType` class). [`__init_subclass__`][base] writes the synthesized + consumer annotations there (`cls.__annotations__ = {**synthesized, **consumer_annotations}`), and [`finalize_django_types`][glossary-finalize_django_types] rewrites each pending relation annotation onto `source_type.__annotations__` via `resolved_relation_annotation`. So `origin.__annotations__[field]` is the single source of truth for the rendered GraphQL type AND its nullability — and it **already reflects** Slice 3's `nullable_overrides` / `required_overrides` (the override is baked into the synthesized annotation at construction time per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)) **and** consumer-authored annotations (which bypass `convert_scalar` entirely). The command therefore reads, per selected field: the resolved GraphQL type + nullability from `origin.__annotations__`; the Django field name + Django field type (`type(field).__name__`) + column-native `nullable` from `definition.selected_fields` / `definition.field_map` ([`FieldMeta`][field-meta]); and the converter classification by re-running the [`SCALAR_MAP`][converters] MRO lookup **to NAME which row fired** (matched `SCALAR_MAP` entry, choice-enum, Relay-supplied `GlobalID`, or relation converter) — **not** to determine nullability. **Re-running `convert_scalar(field, type_name)` to get nullability would be wrong** — it reproduces the column-native `field.null` widening and would miss a `nullable_overrides` / `required_overrides` flip and any consumer-authored annotation; the resolved-annotation read is what makes the table honest about what the schema actually shows. The exact column layout is an implementation detail; the contract is "every selected field, with its *resolved* GraphQL type and nullability, in selection order." **The Relay-suppressed pk is the one selected field NOT in `origin.__annotations__`:** on a Relay-Node-shaped type the pk `continue`s past `convert_scalar` (the interface supplies `id: GlobalID!`), so it is absent from `cls.__annotations__` (confirmed at [`base.py`][base] #"suppress_pk_annotation"). The command must special-case it — when `field.name` is the suppressed pk, report the interface-supplied `GlobalID!` and a "relay.Node id" converter rather than indexing `origin.__annotations__[pk_name]` (which would `KeyError`). A non-Relay type's pk is **not** suppressed and renders as its plain scalar (e.g. `BigAutoField` → `Int!`), read from `origin.__annotations__` like any other scalar.

**Reaching a finalized registry (cold CLI invocation).** A bare `manage.py inspect_django_type BookType` in a cold process registers nothing (no module imported `BookType`) → unresolvable; and even the dotted *type* form imports only the target's own module, which registers that one type but leaves the registry **unfinalized** (`finalize_django_types()` needs *every* relation target registered, so importing one module is not enough). So the command takes an optional **`--schema <selector>`** (e.g. `config.schema`) that it imports **first** — importing the project schema registers all `DjangoType`s and runs the module's `finalize_django_types()` — before resolving the target type. **The `--schema` loader uses Strawberry's `import_module_symbol(options["schema"], default_symbol_name="schema")`, exactly as [`export_schema.py`][export-schema-cmd] does — NOT `import_string`.** This is load-bearing: `import_string("config.schema")` tries to import a module named `config` and read a `schema` **attribute** off it, which **fails** for this project because `examples/fakeshop/config/__init__.py` is empty (`ImportError: Module "config" does not define a "schema" attribute`); `import_module_symbol` instead imports the **module** `config.schema` and (via `default_symbol_name`) reads its `schema` symbol, so both `config.schema` and `config.schema:schema` resolve — the same two selector forms [`export_schema.py`][export-schema-cmd] accepts (verified by [`examples/fakeshop/tests/test_export_schema.py`][fakeshop-tests-export]). Without `--schema`, the command works only when the registry is already populated + finalized in-process; the unfinalized-`CommandError` names `--schema` as the fix. (Whether `--schema` defaults from a settings key is deferred — the package adds settings keys only when a feature needs them, per [`AGENTS.md`][agents]; for `0.0.9` it is an explicit argument.)

**Finalized-state contract (two distinct branches).** `cls.__django_strawberry_definition__` is assigned in [`__init_subclass__`][base] at registration time — **before** [`finalize_django_types`][glossary-finalize_django_types] runs — so its presence does NOT mean the type is finalized. Finalization is the `DjangoTypeDefinition.finalized` flag (flipped in finalizer Phase 3 after `strawberry.type(...)`). The command requires a finalized type because `origin.__annotations__` only carries resolved relation annotations post-finalize. The two states are distinct error branches: a resolved class with **no `__django_strawberry_definition__`** (an abstract / intermediate base `DjangoType` with no `Meta`, which never registers) and a definition with **`finalized is False`** (a concrete but not-yet-finalized type).

**`CommandError` failure modes:** (1) unresolvable argument (neither a dotted path that imports nor a uniquely-registered type name); (2) an ambiguous bare name (two or more registered types share the `__name__` — lists candidates); (3) a resolved symbol that is not a [`DjangoType`][glossary-djangotype] subclass; (4) a `DjangoType` with no `__django_strawberry_definition__` (abstract / no-`Meta` base — "not a registered DjangoType"); (5) a `DjangoType` whose `definition.finalized is False` ("`finalize_django_types()` has not run — pass `--schema <your project schema dotted path>` so all types register and finalize"). Branches (4) and (5) are separate messages.

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
| 1 — `extensions=` singleton-factory migration | [`docs/README.md`][docs-readme], [`docs/GLOSSARY.md`][glossary], [`GOAL.md`][goal], [`examples/fakeshop/config/schema.py`][fakeshop-config-schema], [`TODAY.md`][today], **48 schema-construction entries across 5 package test files** ([`tests/optimizer/test_extension.py`][test-extension] 41 incl. two `_CaptureExt()` + 4 others — audit `rg 'extensions=\['`), [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db], [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme], [`CHANGELOG.md`][changelog] | 1 (a no-`DeprecationWarning` assertion); existing optimizer suite is the behavior-preserving regression guard | `+70 / -55` |
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
- **`required_overrides` changes the GraphQL contract, not the data.** Declaring `required_overrides = ("x",)` renders `x` as `T!` but does NOT alter the Django column (`null=True` stays) or sanitize runtime values: a resolver that returns a row with `x is None` hits a Strawberry non-null violation at query time. The consumer must guarantee the invariant at the resolver boundary (e.g. `.exclude(x__isnull=True)`), exactly as for any non-null GraphQL field backed by nullable storage — the Slice-3 acceptance resolver demonstrates this with `Book.objects.exclude(subtitle__isnull=True)`. (Symmetrically, `nullable_overrides` is always safe — widening a column to `T | None` never violates a non-null contract.)
- **`inspect_django_type` against a type whose override flipped a column.** The command reads the resolved annotation from `origin.__annotations__` (per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)), so its reported nullability reflects the post-override result — NOT the column-native `field.null` that a re-run of `convert_scalar` would reproduce.
- **`inspect_django_type` against an abstract / intermediate base `DjangoType` with no `Meta`.** Such a class never registers and has no `__django_strawberry_definition__`; the command raises `CommandError` ("not a registered DjangoType") — a **distinct branch** from the concrete-but-unfinalized case (`definition.finalized is False` → "`finalize_django_types()` has not run"), per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution).
- **The singleton-factory under the fakeshop schema-reload fixture.** Each reload re-evaluates the module-level `_optimizer = DjangoOptimizerExtension()` and `extensions=[lambda: _optimizer]`, constructing a fresh singleton (and a fresh empty plan cache) per reload — the same lifecycle the prior instance form had; no captured state leaks across reloads. *Within* a reload, `get_extensions` returns the same `_optimizer` on every request, so the cache works (per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)).

## Test plan

Tests live across the package-internal `tests/` tree and the two `examples/fakeshop/` trees, per [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Coverage that can be earned by a real GraphQL query or a real `call_command` is earned there first.

### Slice 1 — singleton-factory migration

The migration is behavior-preserving: the singleton-factory `extensions=[lambda: _optimizer]` shares one instance per process, exactly as the prior instance form did, so the existing optimizer suite ([`tests/optimizer/test_extension.py`][test-extension] etc.) is the regression guard — it still exercises the [Plan cache][glossary-plan-cache] via the shared `_optimizer` and must continue to pass after the rewrite. The slice's one new assertion corrects the rev2 "no `DeprecationWarning`" error (P1.2): under Strawberry 0.316.0 the **instance** form emits a `DeprecationWarning` at `Schema.__init__`, and the singleton-factory removes it — so a focused test constructs one migrated schema under `warnings.catch_warnings(record=True)` (with `warnings.simplefilter("always")` inside the context, so a previously-emitted `DeprecationWarning` that Python would otherwise dedupe cannot produce a false green) and asserts no `DeprecationWarning` mentioning an extension instance is emitted (mirroring the deprecation-hygiene guard already in `tests/test_scalars.py`, which runs a subprocess under `-W error::DeprecationWarning`).

### Slice 2 — `inspect_django_type`

- [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] (new) — in-process `call_command`. **Bare-name resolution needs a finalized registry, which is order-dependent unless forced** (a test could pass after another test imported `config.schema` and fail when run alone), so the bare-name tests use an explicit fixture — mirroring [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]'s reload pattern (per [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme]) — that **clears the global registry and reloads `apps.library.schema` + `config.schema`** (and the URLconf if needed) before each bare-name `call_command`, so running a test alone behaves identically to running it after a sibling:
  - `test_inspect_by_registered_name` (under the reload fixture) — `call_command("inspect_django_type", "BookType")`; capture stdout; assert every selected `BookType` field appears with its resolved scalar and nullability — including the **non-Relay** pk `id` → `Int!` (BookType declares no `interfaces`, so the pk is a plain scalar, NOT `GlobalID!`) — plus `title` → `String!`, `subtitle` → `String`, `circulation_status` → choice enum, `genres` → list relation.
  - `test_inspect_by_dotted_path` (under the reload fixture) — `call_command("inspect_django_type", "apps.library.schema.BookType")`; same assertions; pins the dotted `import_string` branch (the module import registers `BookType`; the fixture's `config.schema` reload supplies finalization).
  - `test_inspect_with_schema_option` (**cold path — NO reload fixture**) — starting from a `registry.clear()`ed registry, `call_command("inspect_django_type", "BookType", "--schema", "config.schema")` resolves and prints the table, proving `--schema` performs registration + finalization on its own. A sibling assertion uses the explicit `--schema config.schema:schema` selector form too (both forms `import_module_symbol` accepts, per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) *Reaching a finalized registry*). This is the contract that makes the command usable from a real shell; the bare-name tests above are the post-schema-import convenience path.
  - `test_inspect_choice_field_row` — assert the `circulation_status` row reports the generated `BookTypeCirculationStatusEnum` and "choice enum" as the converter.
  - `test_inspect_relation_field_rows` — assert `shelf` reports `ShelfType!` (forward FK), `genres` reports `[GenreType!]!` (M2M), and `loans` reports `[LoanType!]!` (reverse FK).
  - `test_inspect_relay_node_pk_row` — `call_command("inspect_django_type", "GenreType")` (a genuinely Relay-Node-shaped type); assert the `id` row reports `GlobalID!` and a "relay.Node id" converter, sourced from the interface (the suppressed pk is absent from `origin.__annotations__`) — pins [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)'s suppressed-pk contract and guards the `KeyError` the naive `origin.__annotations__[pk_name]` read would raise.
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
  - `test_nullability_override_acceptance_api_is_queryable` — seed at least one `Book` with a non-null `subtitle`, then query the dedicated root field for `{ title subtitle }` and assert the response has **no `errors`** (the resolver's `Book.objects.exclude(subtitle__isnull=True)` keeps the `subtitle = String!` invariant true at the boundary). Without this, the SDL test alone could pass while the API is broken — a `subtitle` query over a `subtitle=None` row would surface a non-null violation because the GraphQL type says `String!` while Django returns `None`. This is the fakeshop live-query rule applied to `required_overrides`.
- **Schema-wide-assertion check before declaring the suite undisturbed (P2.4).** A new reachable type + root field changes the total registered-type count and the full SDL, so confirm no existing `test_query/` test snapshots the whole SDL or asserts a registered-type count. **Verified for the current suite:** a `grep` of `examples/fakeshop/test_query/` finds no full-SDL-snapshot or type-list/count assertion, so adding `NullabilityOverrideBookType` + its root field disturbs no existing assertion (the `BookType` nullability baseline at `test_library_api.py` is per-field, not a snapshot). Re-run the check at implementation time in case a schema-snapshot test has since been added.

## Doc updates

Each slice owns its own doc edits (the slices ship independently). The CHANGELOG-edit permission for each slice comes from its doc-update step per the explicit-instruction rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed".

- **Slice 1**
  - [`docs/README.md`][docs-readme] / [`docs/GLOSSARY.md`][glossary]: rewrite the `extensions=[DjangoOptimizerExtension()]` snippets to the module-level-singleton factory (`_optimizer = DjangoOptimizerExtension(); extensions=[lambda: _optimizer]`) with a one-line "preserves the instance-bound [Plan cache][glossary-plan-cache], no deprecation warning" note, per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form).
  - [`GOAL.md`][goal]: the astronomy `strawberry.Schema(...)` gains `DjangoOptimizerExtension` via the singleton-factory (it currently passes **no** `extensions=`), so the north-star feature-complete recipe shows the optimized boundary rather than silently disabling it.
  - [`CHANGELOG.md`][changelog]: `### Changed` bullet under `[Unreleased]` — "Migrated `extensions=[DjangoOptimizerExtension()]` to the module-level-singleton factory form (`extensions=[lambda: _optimizer]`): preserves the instance-bound plan cache and removes Strawberry 0.316.0's instance-form `DeprecationWarning`."
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

- **GLOSSARY has no entry yet for the three new symbols.** `Meta.nullable_overrides`, `Meta.required_overrides`, and the `inspect_django_type` command have no [`docs/GLOSSARY.md`][glossary] heading at spec-authoring time ([`docs/SPECS/NEXT.md`][next] Step 7 *defers* glossary anchoring to the companion CSV until the heading ships — it does not forbid authoring an entry; the entries simply land with the implementation, not the spec). Preferred answer: the three entries are authored during implementation (Slice 2 and Slice 3's doc-update steps) and are therefore **omitted from the companion [`docs/spec-029-consumer_dx_cleanup-0_0_9-terms.csv`][spec-029-terms]** so [`scripts/check_spec_glossary.py`][check-spec-glossary] stays green (the checker requires every CSV term to resolve to a real glossary heading). Fallback: if the maintainer wants the glossary entries to exist before implementation, a separate doc-only change adds the three `planned for 0.0.9` headings, after which the CSV can carry the three rows and the checker still passes.
- **Card body names a stale spec filename.** The card's Slice 3 "Requires spec" line names `docs/spec-021-nullable_overrides-0_0_8.md` (wrong NNN, wrong version). Preferred answer per [Decision 1](#decision-1--spec-filename-and-canonical-naming): this spec is `docs/spec-029-consumer_dx_cleanup-0_0_9.md`; the card-body reference is rewritten to the canonical name in the [`docs/SPECS/NEXT.md`][next] Step-8 archive sweep / card-completion wrap. Fallback: none — the structured-filename convention is unambiguous.
- **Card body names a stale CHANGELOG heading.** The card's per-slice Definition-of-done text says CHANGELOG entries go under `## [0.0.8]`. Preferred answer per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut): `0.0.8` is shipped; new work accumulates under `[Unreleased]` and is promoted at the joint `0.0.9` cut. Fallback: if the maintainer has already opened a `## [0.0.9]` heading by implementation time, append there instead of `[Unreleased]`.
- **Card body names a non-existent test file.** The card says Slice 2's test lives at `examples/fakeshop/tests/test_commands.py`; no such file exists (the only `test_commands.py` is per-app at `apps/products/tests/`). Preferred answer per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution): the test lands at [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect], mirroring the one-file-per-command convention of [`examples/fakeshop/tests/test_export_schema.py`][fakeshop-tests-export]. Fallback: if the maintainer prefers a single `test_commands.py` aggregating all example-project command tests, the inspect tests move there and `test_export_schema.py` is folded in too — but the per-command split is the existing pattern.
- **`inspect_django_type` argument resolution conflict.** The card body says positional `type_dotted_path` but its test passes a bare `"BookType"`. Preferred answer per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution): two-step resolution — Django's `import_string` for fully-dotted paths first, then a registry lookup that requires a **unique** `__name__` match (an ambiguous bare name raises `CommandError` listing candidates). The earlier "same mechanism as `export_schema` (`import_module_symbol`)" framing was wrong — `import_module_symbol` uses the `module:symbol` selector form and does not resolve a fully-dotted object path. Fallback: if the bare-name convenience proves error-prone, drop it and require the dotted path.
- **Relation-field nullability override deferred.** Preferred answer per [Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred): scalar-only for `0.0.9`; relation override-targets raise. Fallback: if relation override demand surfaces, the natural first extension is forward single-valued FK / OneToOne override (thread `force_nullable` into `resolved_relation_annotation`), with the many-side list-vs-element nullability ambiguity ([Relation handling][glossary-relation-handling]) staying out until its own design lands.
- **Dict-of-name vs tuple-set form.** Preferred answer per [Decision 5](#decision-5--two-key-tuple-set-override-form): two-key tuple-set. Fallback: a single `Meta.nullability = {"field": bool}` dict could be added later as sugar normalized to the two sets if consumers find two keys verbose; the tuple-set form stays the primary shape.
- **Consumer-authored-field override rejection false-positive.** Preferred answer per [Decision 8](#decision-8--override-validation-and-collision-behavior): naming a consumer-authored field in an override set raises (the annotation already controls nullability). Fallback: if a real pattern surfaces where a consumer wants the override to apply *on top of* a partial annotation override, the rule relaxes to "annotation wins, override is a documented no-op for that field" — but fail-loud is the default until that demand is concrete.
- **The Strawberry extension lifecycle is version-dependent; the spec pins claims to the locked `0.316.0`.** Preferred answer per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form): the module-level-singleton factory preserves the instance-bound [Plan cache][glossary-plan-cache] and emits no `DeprecationWarning` under 0.316.0's per-request `get_extensions`. The package's `>=0.262.0` floor is open-ended, so the *mechanism* (not the conclusion) can drift across the supported range — spec-004's `_sync` / `_async` model was accurate at its 2026-04-30 spike and is already stale. Fallback: if a supported Strawberry version stops calling the factory per request, re-derive Decision 3 against that version; the singleton-factory's "one shared instance, no instance-deprecation warning" property holds for any version with 0.316.0's `isinstance`-passthrough + instance-deprecation behavior.
- **`config/schema.py` / `TODAY.md` class-form drift is a live cold-cache regression, not harmless.** Preferred answer: Slice 1 migrates both to the singleton-factory — under 0.316.0 the bare class re-instantiates per request (cold plan cache, sync included), so it is a real (if silent) regression today. Fallback: none — the migration restores caching and removes no functionality.

## Out of scope (explicitly tracked elsewhere)

- **Relation-field nullability override** — deferred (no card yet); the forward single-valued case is the natural follow-up, the many-side list-vs-element case is its own design ([Decision 10](#decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred)).
- **`DjangoConnectionField`** ([`DjangoConnectionField`][glossary-djangoconnectionfield]) — [`WIP-ALPHA-030-0.0.9`][kanban]. Slice 1 migrates the `extensions=` instance form to the singleton-factory, so this card's new schema-construction surfaces should present the same singleton-factory form; the connection field itself is out of scope.
- **Full Relay story** ([`WIP-ALPHA-031-0.0.9`][kanban]) and **connection-aware optimizer planning** ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning], [`WIP-ALPHA-032-0.0.9`][kanban]) — the rest of the `0.0.9` cohort; the joint cut that owns the version bump (per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).
- **`Meta.fields_class`** ([`FieldSet`][glossary-fieldset], [`Meta.fields_class`][glossary-metafields_class]) — `0.1.1`. Field-level resolver / redaction sidecar; orthogonal to nullability override (resolve-time gate vs construction-time annotation rewrite).
- **`Meta.search_fields`** ([`Meta.search_fields`][glossary-metasearch_fields]) — `0.1.2`.
- **`AggregateSet`** ([`AggregateSet`][glossary-aggregateset], [`Meta.aggregate_class`][glossary-metaaggregate_class]) — `0.1.3`.
- **Permissions cascade** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions]) — `0.0.10`.
- **Relocating the `DjangoOptimizerExtension` plan cache off the instance** — **NOT** needed for this card: the singleton-factory ([Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)) preserves the instance-bound cache without it. It remains a possible future optimizer refactor (e.g. if a Strawberry version stops honoring the factory-per-request contract), but it is out of scope here and is not a prerequisite for Slice 1.
- **A `--json` / `--watch` mode on `inspect_django_type`** — not planned; the command ships a single human-readable table, matching the `0.0.7` `export_schema` posture.
- **Persisting overrides on `DjangoTypeDefinition`** — not needed; the override resolves to a final annotation on `cls.__annotations__` at construction time, which is the authoritative record the inspect command reads ([Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar) / [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)).
- **Version bump** — owned by the joint `0.0.9` cut ([Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

## Definition of done

The completion contract the card is built against. Items are grouped by slice; the card completes when all three functional slices' items are satisfied (or Slice 3 carves off per [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)).

**Spec + companion CSV**

1. [`docs/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/spec-029-consumer_dx_cleanup-0_0_9-terms.csv`][spec-029-terms] anchoring every project-specific term that **has** a [`docs/GLOSSARY.md`][glossary] heading; [`uv run python scripts/check_spec_glossary.py --spec docs/spec-029-consumer_dx_cleanup-0_0_9.md`][check-spec-glossary] reports `OK: <N> terms`. The three net-new symbols (`Meta.nullable_overrides`, `Meta.required_overrides`, `inspect_django_type`) have **no glossary heading yet** and are therefore intentionally NOT in the CSV — they are added to the glossary AND the CSV during the Slice 2 / Slice 3 doc-update steps (per [Risks and open questions](#risks-and-open-questions)). The companion CSV is honestly incomplete on the card's new public surfaces until then.

**Slice 1 — `extensions=` singleton-factory migration**

2. Every instance-form `extensions=[<instance>]` entry — anonymous, **named** (`ext = …; extensions=[ext]`), `strictness=` variants, the bare class, AND **subclass instances** (the two `_CaptureExt()` in [`tests/optimizer/test_extension.py`][test-extension]) — across the package test schemas (≈48 entries; audit `rg 'extensions=\['`), the example `config/schema.py`, and the consumer docs is migrated to a singleton-factory `extensions=[lambda: <instance>]` per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) — **function-local** where a test asserts on the instance's `cache_info()`, module-level where there is one schema per module — preserving the instance-bound [Plan cache][glossary-plan-cache].
3. The consumer-doc snippets in [`docs/README.md`][docs-readme] and [`docs/GLOSSARY.md`][glossary] show the singleton-factory form with the one-line rationale; [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] and [`TODAY.md`][today] (previously the bare class — a cold-cache regression under 0.316.0) are migrated too; and [`GOAL.md`][goal]'s astronomy schema — previously with no `extensions=` at all — gains `DjangoOptimizerExtension` via the singleton-factory so the north-star recipe shows the optimized boundary.
4. The instance-form `DeprecationWarning` Strawberry 0.316.0 emits at `Schema.__init__` is **gone** after the migration (the `extensions` entries are callables, not instances), pinned by a focused no-warning assertion. [`CHANGELOG.md`][changelog] `[Unreleased]` carries the `### Changed` bullet.

**Slice 2 — `inspect_django_type`**

5. [`django_strawberry_framework/management/commands/inspect_django_type.py`][inspect-cmd] ships with module + class docstring, `add_arguments` registering a positional `type` argument, and `handle` resolving it (`import_string` dotted path, then a unique-`__name__` registry lookup), reading the **resolved annotation from `origin.__annotations__`** for the GraphQL type + nullability and `definition.selected_fields` / `field_map` for Django-side metadata + converter classification, and printing the per-field resolution table per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution).
6. `CommandError` is raised for: an unresolvable argument; an **ambiguous bare name** (≥2 registered types share the `__name__`); a non-`DjangoType` resolved symbol; a `DjangoType` with **no `__django_strawberry_definition__`** (abstract / no-`Meta` base); and a `DjangoType` whose **`definition.finalized is False`** — the last two are distinct branches per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution).
7. [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect] covers happy paths via `call_command` — bare-name tests under a registry-clear + reload fixture (order-independent), plus a cold-path `--schema config.schema` test (and the `config.schema:schema` selector form) proving `--schema` finalizes on its own — and [`tests/management/test_inspect_django_type.py`][test-management-inspect] covers the failure modes, per the [Test plan](#test-plan).
8. [`docs/GLOSSARY.md`][glossary] adds the command entry; [`docs/TREE.md`][tree] lists the new module + mirrored test; [`CHANGELOG.md`][changelog] `[Unreleased]` carries the `### Added` bullet.

**Slice 3 — `Meta.nullable_overrides` / `Meta.required_overrides`**

9. [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] contains `"nullable_overrides"` and `"required_overrides"`; neither is in [`DEFERRED_META_KEYS`][base] (net-new keys per [Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)).
10. [`django_strawberry_framework/types/converters.py::convert_scalar`][converters] accepts the keyword-only `force_nullable: bool | None = None` tri-state per [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar); the widening decision is computed once from `effective_null` and applied uniformly across the `ArrayField` / `HStoreField` / choice / scalar branches; the `None` default reproduces today's behavior.
11. The override validation is staged per [Decision 8](#decision-8--override-validation-and-collision-behavior): [`_validate_meta`][base] shape-checks + normalizes the two tuples onto `_ValidatedMeta` and raises the both-sets collision; a `_validate_nullability_override_targets(...)` helper runs in [`__init_subclass__`][base] (after `_select_fields` + `consumer_authored_fields` + the Relay-shape check) and raises [`ConfigurationError`][glossary-configurationerror] for unknown / excluded / consumer-authored / relation / Relay-pk targets; [`_build_annotations`][base] receives the normalized override frozensets and passes `force_nullable` per field to `convert_scalar`.
12. [`tests/types/test_converters.py`][test-converters] (tri-state across scalar / nullable / choice / Array / HStore) and [`tests/types/test_base.py`][test-types-base] (validation + collision + override-applies + `ALLOWED_META_KEYS` membership) cover the slice per the [Test plan](#test-plan).
13. A dedicated acceptance-only `NullabilityOverrideBookType` secondary type on `library.Book` (`Meta.primary = False`; `BookType` marked `Meta.primary = True`) is added to [`apps/library/schema.py`][fakeshop-library-schema] with a dedicated root resolver that returns `Book.objects.exclude(subtitle__isnull=True)` (so the `subtitle = String!` invariant holds at the boundary). Two live HTTP tests in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]: an **SDL** test asserting `title` flips `String!` → `String` and `subtitle` flips `String` → `String!` while the `Book` columns are unchanged, and a **data-query** test requesting `{ title subtitle }` over non-null-subtitle rows asserting no `errors`. The existing `BookType` and the `scalars` app's types / assertions are untouched.
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
[upstream-cookbook]: https://github.com/riodw/django-graphene-filters
