# Rationale companion: spec-029 (`DjangoType` consumer-DX cleanup pass)

Companion to [`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029]. It carries that spec's **deliberative layer**: every Decision's justification and every alternative a Decision rejected and why it lost. The spec carries the contract; this file carries the reasons for it.

Read this when checking the implementation against the reasoning that produced it, or before re-opening a settled question. Worker 2 never reads it (`docs/builder/BUILD.md` `### Who reads it, and when`).

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-029-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] bakes the card's NNN and target patch into the filename. The card is `DONE-029-0.0.9`, so `<NNN>` is `029` and `<0_0_X>` is `0_0_9`.
- The topic slug is `consumer_dx_cleanup` — it names the card's subject (the consumer-DX cleanup pass) rather than any single slice. The whole card is three slices; a slug naming only Slice 3 (`nullable_overrides`) would mis-scope the spec.

### Alternatives considered (and rejected)

- **The card body's `docs/spec-021-nullable_overrides-0_0_8.md`.** Rejected: `021` is a different card's NNN ([`DONE-021-0.0.7`][kanban], the apps card) and `0_0_8` is not the card's patch, so the name breaks the structured-filename convention.
- **Topic slug `nullable_overrides`** (matching Slice 3, the spec's design core). Rejected: the spec covers all three slices per [Decision 2](#decision-2--one-spec-covers-all-three-slices); naming the file after one slice would imply the other two are out of scope.

## Decision 2 — One spec covers all three slices

Spec: [Decision 2 — One spec covers all three slices][spec-029-d2].

### Justification

- The three slices belong to one card with one Definition of done; splitting the spec would orphan Slices 1 + 2 from any design record.
- Slices 1 + 2 are low-design (a construction-form rule and a strict introspection reader); their spec coverage is correspondingly light. The architectural depth concentrates on Slice 3, which carries the card's design questions (dict-of-name vs tuple-set, `Meta.exclude` interaction, both-sets collision, choice-field interaction, FK / reverse-FK interaction).
- The slices are independent, so each slice's section is self-contained — a reader of Slice 2 reads [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) and the Slice 2 checklist / DoD items without needing the Slice 3 design.

### Alternatives considered (and rejected)

- **A spec for Slice 3 only, with Slices 1 + 2 specless.** Rejected: the [`docs/SPECS/NEXT.md`][next] flow targets the card, not a slice; and the board's spec map would then carry a card whose spec covers only a third of its scope.

## Decision 3 — Slice 1 adopts the singleton-factory `extensions=` form

Spec: [Decision 3 — Slice 1 adopts the singleton-factory `extensions=` form][spec-029-d3].

### Justification

- The singleton-factory is strictly better than the bare instance (identical caching, no deprecation warning) and strictly better than the bare class / constructing-`lambda` (which get a cold cache every operation). It is the one form that both moves off the deprecated instance AND preserves the optimization.
- No plan-cache relocation is needed — the singleton-factory shares one instance per construction site, exactly as the bare instance does.
- The mechanism is read from the Strawberry release `uv.lock` resolves, not from an older extension-lifecycle model: an earlier model that split `_sync_extensions` / `_async_extensions` (the one [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004] spiked) does not describe the supported range, where one per-operation `Schema.get_extensions` serves both modes. The conclusion holds for any version with the `get_extensions` instance passthrough + instance-deprecation behavior.
- **Per construction site, not per file or per module.** One shared instance per file would pollute the per-test `cache_info()` counters in [`tests/optimizer/test_extension.py`][test-extension] (order-dependent failures) and could not carry per-site `strictness=`; [`tests/optimizer/test_extension.py::test_strictness_flags_a_relation_under_an_unplannable_root`][test-extension] builds two differently-configured schemas inside one function, which rules out per-function granularity too.
- **A standing gate by form, not a one-shot sweep or a spelling list.** A build-time grep has nothing standing behind it, so the forbidden forms can come back unnoticed; [`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`][test-ci-governance] runs every time. Enumerating spellings under-reports — a sweep for `lambda: DjangoOptimizerExtension()` misses the keyword-carrying variants (`strictness=`, `nested_connection_strategy=`), which are the same form. The instance forms need no entry: Strawberry's instance-form `DeprecationWarning` meets `pytest.ini`'s `filterwarnings = error` and fails the suite on its own.

### Alternatives considered (and rejected)

- **Keep the bare instance and document why.** Rejected: correct on caching, but it leaves a `DeprecationWarning` ("will be removed") on every schema built the documented way — and a singleton-factory form exists that keeps the caching AND silences the warning.
- **The bare class or a constructing `lambda: DjangoOptimizerExtension()`** (the forms the [`KANBAN.md`][kanban] card body names). Rejected: a cold `self._plan_cache` every operation, in both modes — regresses the optimization.
- **Relocate the plan cache off the instance to enable the bare class.** Rejected as unnecessary: the singleton-factory preserves the instance-bound cache with no optimizer change. Cache relocation is a separate, larger optimizer concern ([Out of scope][spec-029-out-of-scope]) and not a prerequisite for this form.
- **Suppress the warning with `warnings.filterwarnings("ignore", …)` and keep the instance.** Rejected: hides a real upstream signal the project otherwise guards against (`tests/test_scalars.py` runs a subprocess under `-W error::DeprecationWarning`); the singleton-factory removes the warning at the source instead.

## Decision 4 — `inspect_django_type` command shape and argument resolution

Spec: [Decision 4 — `inspect_django_type` command shape and argument resolution][spec-029-d4].

### Justification

- Reusing the [`export_schema.py`][export-schema-cmd] `Command` shape means a maintainer sees one shape across both commands; the `CommandError` discipline (wrap import / type / value failures) is shared, and both commands' loaders go through [`django_strawberry_framework/management/commands/_imports.py`][commands-imports], so the pre-import path validation and the import-failure translation are one implementation.
- Reading `__django_strawberry_definition__` / [`FieldMeta`][field-meta] makes the command a strict consumer of the existing introspection surface — no new public API, no foundation change.
- Dispatching on the dot resolves the card body's two signals (a positional `type_dotted_path`, and a worked test passing a bare `"BookType"`) without a catch-all fallback; a name or a path both work, and a dotted import failure is never masked by a registry retry, because catching every import error would hide a real import-time bug inside a consumer module.
- Matching the bare name against both the SDL name and the Python `__name__` lets an operator paste whichever surface they are looking at; requiring a unique match across both surfaces keeps the result independent of import order.
- **The authoritative record differs by field origin, so the read differs too.** `origin.__annotations__` is authoritative for auto-synthesized fields and reflects the Slice 3 overrides — the property [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar) depends on. It is not authoritative for a consumer-authored field (its entry is a `StrawberryAnnotation` for a `strawberry.field` assignment and an unresolved forward-ref string for an annotated relation) nor for a connection-only relation (whose list annotation is deleted), so those rows read the finalized `origin.__strawberry_definition__`. The principle is one rule: read the authoritative post-finalize record for that field's origin, never re-derive by re-running the converter.
- **A relation pk is not the Relay row.** `_build_annotations` routes every relation field through its relation branch before the pk-suppression check, so a relation pk on a Relay type (`OneToOneField(primary_key=True)`, an MTI parent link) keeps its annotation and the schema exposes the relation; reporting `GlobalID!` there would describe a field Strawberry never emits.

### Alternatives considered (and rejected)

- **Dotted-path-only resolution.** Rejected: rejects the bare `"BookType"` an operator naturally types; the dot-dispatch (dotted → `import_string`, bare → registry) honors both forms.
- **Registry-name-only resolution.** Rejected: a dotted path is the unambiguous form when two apps register a `BookType`; dropping it would force disambiguation the consumer cannot express.
- **Resolve a bare name to the first registry match.** Rejected: import-order-dependent output; the unique-match contract raises on ambiguity instead.
- **Build the table from the constructed `strawberry.Schema` introspection instead of the type's annotations + `DjangoTypeDefinition`.** Rejected: the command's value is moving the diagnostic to the *type-definition* layer; reading the finalized type's records keeps the command usable even when full schema construction fails, and those records are already authoritative (no second source needed).

## Decision 5 — Two-key tuple-set override form

Spec: [Decision 5 — Two-key tuple-set override form][spec-029-d5].

### Justification

- The two-key form mirrors [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] (both names collections, both expressing per-field set membership), so it reads as native to the package's `Meta`-shaped API.
- A dict-of-name-to-bool duplicates the direction the two-key split already encodes and invites the ambiguous `{"field": False}` shape: does `False` mean "force required" or "no override"? The two-key form has no such ambiguity — membership in `nullable_overrides` means "force nullable," membership in `required_overrides` means "force required," absence from both means "honor the column."
- The two directions are genuinely distinct operations (widen `T` → `T | None` vs narrow `T | None` → `T`), so a per-direction set names each operation explicitly.

### Alternatives considered (and rejected)

- **A single `Meta.nullability = {"field": bool}` dict.** Rejected for the `{"field": False}` ambiguity above; it could be added later as sugar normalized internally to the two sets if consumers ask, but the two-key form is the primary shape.
- **A single `Meta.nullable_overrides = {"field": bool}` dict (one key, dict value).** Rejected: same ambiguity, and it diverges from the names-collection shape of every other field-selection `Meta` key.

## Decision 6 — Net-new `ALLOWED_META_KEYS` entries, not a `DEFERRED_META_KEYS` promotion

Spec: [Decision 6 — Net-new `ALLOWED_META_KEYS` entries, not a `DEFERRED_META_KEYS` promotion][spec-029-d6].

### Justification

- The deferred-key promotion gate (per [Cross-subsystem invariants][glossary-cross-subsystem-invariants]) exists for keys **named in the `Meta` surface before their subsystems shipped** — [`Meta.orderset_class`][glossary-metaorderset_class] and [`Meta.filterset_class`][glossary-metafilterset_class] were, and [`Meta.aggregate_class`][glossary-metaaggregate_class] / [`Meta.fields_class`][glossary-metafields_class] / [`Meta.search_fields`][glossary-metasearch_fields] still are; the deferred set holds keys that are reserved-but-not-yet-functional, and the gate promotes one only when its subsystem applies it end-to-end.
- `nullable_overrides` / `required_overrides` were never reserved; they are net-new keys whose feature ships in the same card that adds them. So they go straight into `ALLOWED_META_KEYS`; the deferred-set machinery is not involved.
- Pinning the difference stops a future maintainer from looking for a promotion gate that was never needed.

### Alternatives considered (and rejected)

- **Add them to `DEFERRED_META_KEYS` first, then promote in the same commit.** Rejected: pointless churn — the deferred set models "reserved but not functional," which is never true for these keys.

## Decision 7 — Tri-state `force_nullable` threaded through `convert_scalar`

Spec: [Decision 7 — Tri-state `force_nullable` threaded through `convert_scalar`][spec-029-d7].

### Justification

- The tri-state keeps the converter the single source of truth for "what annotation does this column produce," with the override as one extra input to it.
- Rewriting the returned annotation at the call site would require unwrapping an arbitrary `T | None` Union to strip nullability (`required_overrides` on a nullable column), which is fragile — it must detect the Union, find `NoneType`, and rebuild the non-None member, with special cases for `list[T] | None`, `EnumType | None`, and a `DjangoFileType | None` output object. The tri-state computes the widening *before* it happens, so there is nothing to unwrap.
- The override applies uniformly to every branch because the widening decision is computed from one `effective_null` value — choice enums, arrays, hstore, and plain scalars all honor it without per-branch override logic ([Decision 9](#decision-9--choice-field-interaction) confirms the choice case).
- The read-output entry point `convert_field_output` carries the same tri-state rather than reimplementing it, and threads it into `convert_scalar` unchanged, so the seam is still one parameter. Keeping the file/image lookup off `convert_scalar` / `scalar_for_field` / `SCALAR_MAP` means an output object can never reach the shared filter-input path.
- Because the override is baked into the synthesized annotation at construction time, `origin.__annotations__` is the authoritative post-override record, which is why the inspect command reads it instead of re-deriving nullability ([Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)).

### Alternatives considered (and rejected)

- **Rewrite the annotation at the `_build_annotations` call site (`ann | None` to widen; unwrap-Optional to narrow).** Rejected: the narrow direction (`required_overrides`) requires robustly unwrapping `T | None`, `list[T] | None`, `EnumType | None`, and a file/image output object — fragile, and it duplicates knowledge the converter already has.
- **A separate `convert_scalar_with_override(...)` wrapper.** Rejected: a second entry point that must stay in sync with `convert_scalar`'s branch logic; the keyword-only parameter keeps one function authoritative.

## Decision 8 — Override validation and collision behavior

Spec: [Decision 8 — Override validation and collision behavior][spec-029-d8].

### Justification

- Fail-loud at type-creation time is the package's established posture ([`ConfigurationError`][glossary-configurationerror] for unknown `Meta` keys, invalid hints, mis-typed override targets). A silently-ignored override is the worst failure mode — the consumer believes nullability flipped and it did not.
- Validating against the selected set (not just model existence) catches the [`Meta.exclude`][glossary-metaexclude] interaction: an excluded field cannot be overridden because it is not in the type.
- Rejecting consumer-authored fields resolves the interaction with [Scalar field override semantics][glossary-scalar-field-override-semantics]: the two mechanisms both control nullability, and the consumer must pick one. The annotation override is strictly more powerful (it controls the whole annotation, not just nullability), so the validator points the consumer there.
- The helper takes `relay_shaped: bool` rather than a pre-computed pk name and derives `model._meta.pk.name` itself, only when the type is Relay-shaped, so no caller can hand it a pk name computed under a different Relay predicate than the one synthesis used.
- The Relay-pk rule runs before the relation rule so a name that is both — a relation pk such as `OneToOneField(primary_key=True)` on a Relay type — is reported with the Relay reason.
- The unknown/excluded half is shared through `_selected_meta_targets` because every `Meta` key targeting a set of field names needs exactly that derivation; one implementation keeps the consumer-visible unknown-field shape identical to the `Meta.fields` / `Meta.exclude` / `Meta.optimizer_hints` typo guards, and each caller keeps only its per-name remainder.

### Alternatives considered (and rejected)

- **Silently no-op an override on an excluded / consumer-authored field.** Rejected: silent no-op hides a real configuration mistake; the package fails loud everywhere else.
- **Let the consumer-authored annotation win and skip the override silently.** Rejected: same silent-no-op objection; the consumer cannot tell which mechanism took effect.
- **Allow a field in both sets, with one direction winning.** Rejected: there is no non-arbitrary winner for a contradictory declaration; raising is the honest response.

## Decision 9 — Choice-field interaction

Spec: [Decision 9 — Choice-field interaction][spec-029-d9].

### Justification

- [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)'s single `effective_null` computation sits at the post-choice-substitution widening point, so the choice case is covered for free.
- The override flips the enum's nullability, not its members; the stored-DB-value member naming ([Choice enum generation][glossary-choice-enum-generation]) is untouched.

### Alternatives considered (and rejected)

- **Reject overrides on choice fields.** Rejected: there is no reason a choice field's GraphQL nullability should be less overridable than a plain scalar's; the widening point already handles it uniformly.

## Decision 10 — Non-relation scope; relation-field overrides rejected and deferred

Spec: [Decision 10 — Non-relation scope; relation-field overrides rejected and deferred][spec-029-d10].

### Justification

- The non-relation annotation path (`convert_field_output`, and `convert_scalar` behind it) is the only path `force_nullable` threads through; relation fields take the `field.is_relation` branch in [`_build_annotations`][base] → `PendingRelation` / `resolved_relation_annotation`, an entirely separate annotation path the override does not touch. The discriminator is that path, not the column's storage class, which is why a file/image output object is in scope: it is nullable by default (the generated parent resolver returns `None` for an empty `FieldFile`), and `required_overrides` is the opt-in to `DjangoFileType!` that [`docs/README.md`][docs-readme] and the [`Meta.required_overrides`][glossary-metarequired_overrides] entry describe.
- Relation nullability override is a genuinely harder design: a forward single-valued relation (`TargetType | None` ↔ `TargetType`) would thread an override into `resolved_relation_annotation`, but a many-side relation ([Relation handling][glossary-relation-handling] reverse-FK / M2M) renders as `list[TargetType]` (`[T!]!`) where "make it nullable" is ambiguous — does it mean the list is nullable (`[T!]`) or the element (`[T]!`)? Resolving that ambiguity is its own card.
- Scoping to non-relation fields keeps Slice 3 bounded and ships the common case (a `NOT NULL` text column the consumer wants optional in GraphQL) without inventing the many-side list-vs-element semantics.

### Alternatives considered (and rejected)

- **Include forward single-valued FK / OneToOne overrides** (thread `force_nullable` into `resolved_relation_annotation`, reject only many-side overrides). Viable; rejected to keep the slice bounded and the validation rule simple ("relation = rejected"). This is the natural first extension if relation-override demand surfaces.
- **Silently ignore relation override-targets.** Rejected: silent no-op (see [Decision 8](#decision-8--override-validation-and-collision-behavior)).

## Decision 11 — Version bumps are owned by the joint `0.0.9` cut

Spec: [Decision 11 — Version bumps are owned by the joint `0.0.9` cut][spec-029-d11].

### Justification

- A feature card mutating shared release state would race its sibling cards for "who owns the `0.0.9` bump"; centralizing the bump in the joint cut removes the race.
- Keeping version edits command-gated prevents an implementer from touching `pyproject.toml` / `__version__` / the pinned version test while implementing a DX slice.

### Alternatives considered (and rejected)

- **Bump to `0.0.9` in this card (it is the lowest-NNN `0.0.9` card).** Rejected: lowest-NNN is not "owns the release"; whichever card lands last, or an explicit maintainer cut, owns the bump. Encoding "lowest NNN bumps" is an implicit-bump rule [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] Decision 10 already rejected.
- **Append CHANGELOG bullets under `## [0.0.8]`.** Rejected: `0.0.8` was already shipped; appending to a shipped heading would mis-attribute `0.0.9` work.

## Decision 12 — Slice independence

Spec: [Decision 12 — Slice independence][spec-029-d12].

### Justification

- The three slices share no implementation surface, so each slice's change is reviewable in isolation; a reviewer of the Slice 2 command does not need the Slice 3 override design loaded.

### Alternatives considered (and rejected)

- **Enforce a strict slice order (1 → 2 → 3).** Rejected: there is no dependency to enforce; an artificial order would block Slice 2 behind Slice 1 for no reason.

## The Slice 3 acceptance surface

Not a Decision, but its reasons hold:

- The live-HTTP host is a dedicated acceptance-only secondary [`DjangoType`][glossary-djangotype] on `library.Book` (`Meta.primary = False`, with `BookType` primary) rather than a change to `BookType` or the `scalars` app's types, whose live tests pin baseline non-null / nullable / all-null wire-format behavior. The [`Meta.primary`][glossary-metaprimary] interaction is therefore part of the plan.
- Fakeshop seeds `Book(subtitle=None)`, so an SDL-only test could pass while a `subtitle` query violated the declared `String!` contract. The acceptance resolver excludes null-subtitle rows, a data-query test asserts no `errors`, and `.order_by("id")` keeps that assertion independent of response order.

<!-- LINK DEFINITIONS -->
<!-- Root -->
[kanban]: ../../../KANBAN.md

<!-- docs/ -->
[docs-readme]: ../../README.md
[glossary-choice-enum-generation]: ../../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-cross-subsystem-invariants]: ../../GLOSSARY.md#cross-subsystem-invariants
[glossary-djangotype]: ../../GLOSSARY.md#djangotype
[glossary-metaaggregate_class]: ../../GLOSSARY.md#metaaggregate_class
[glossary-metaexclude]: ../../GLOSSARY.md#metaexclude
[glossary-metafields]: ../../GLOSSARY.md#metafields
[glossary-metafields_class]: ../../GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: ../../GLOSSARY.md#metafilterset_class
[glossary-metaorderset_class]: ../../GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: ../../GLOSSARY.md#metaprimary
[glossary-metarequired_overrides]: ../../GLOSSARY.md#metarequired_overrides
[glossary-metasearch_fields]: ../../GLOSSARY.md#metasearch_fields
[glossary-relation-handling]: ../../GLOSSARY.md#relation-handling
[glossary-scalar-field-override-semantics]: ../../GLOSSARY.md#scalar-field-override-semantics

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-004]: ../spec-004-optimizer_beyond-0_0_3.md
[spec-028]: ../spec-028-orders-0_0_8.md
[spec-029-d10]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-10--non-relation-scope-relation-field-overrides-rejected-and-deferred
[spec-029-d11]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-11--version-bumps-are-owned-by-the-joint-009-cut
[spec-029-d12]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-12--slice-independence
[spec-029-d1]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-1--spec-filename-and-canonical-naming
[spec-029-d2]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-2--one-spec-covers-all-three-slices
[spec-029-d3]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-3--slice-1-adopts-the-singleton-factory-extensions-form
[spec-029-d4]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-4--inspect_django_type-command-shape-and-argument-resolution
[spec-029-d5]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-5--two-key-tuple-set-override-form
[spec-029-d6]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion
[spec-029-d7]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-7--tri-state-force_nullable-threaded-through-convert_scalar
[spec-029-d8]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-8--override-validation-and-collision-behavior
[spec-029-d9]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-9--choice-field-interaction
[spec-029-out-of-scope]: ../spec-029-consumer_dx_cleanup-0_0_9.md#out-of-scope-explicitly-tracked-elsewhere
[spec-029]: ../spec-029-consumer_dx_cleanup-0_0_9.md

<!-- docs/builder/ -->
<!-- django_strawberry_framework/ -->
[base]: ../../../django_strawberry_framework/types/base.py
[commands-imports]: ../../../django_strawberry_framework/management/commands/_imports.py
[export-schema-cmd]: ../../../django_strawberry_framework/management/commands/export_schema.py
[field-meta]: ../../../django_strawberry_framework/optimizer/field_meta.py

<!-- tests/ -->
[test-ci-governance]: ../../../tests/test_ci_governance.py
[test-extension]: ../../../tests/optimizer/test_extension.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->
<!-- External -->
