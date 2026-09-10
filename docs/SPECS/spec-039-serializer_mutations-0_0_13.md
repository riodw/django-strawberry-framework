# Spec: DRF serializer mutations — `SerializerMutation` on the DRF-shaped `class Meta` surface, reusing the shared `FieldError` envelope and the `DjangoMutation` foundation, with `djangorestframework` as a soft dependency

Shipped in `0.0.13` (card [`DONE-039-0.0.13`][kanban]). This card adds the
**serializer-validated** write flavor on top of the model-driven mutation
foundation [`DONE-036-0.0.11`][kanban] ([`spec-036`][spec-036]) and the form-validated
flavor [`DONE-038-0.0.12`][kanban] ([`spec-038`][spec-038]) already shipped: one new
base — [`SerializerMutation`][glossary-serializermutation] — declared through a
nested `class Meta` (`Meta.serializer_class`, the DRF / graphene-django shape, **not**
graphene's `MutationOptions` / `__init_subclass_with_meta__` / `ClientIDMutation`
pattern). It is a Required [`graphene-django`][upstream-serializer-mutation] parity
item (the card's own ⚛️ Required tag): graphene-django ships `SerializerMutation` as
the dominant write-side abstraction for the DRF migrant who already encodes write
validation in a `ModelSerializer`, and without an equivalent every DRF + django-filter
migrant must re-declare that validation against the lower-level
[`DjangoMutation`][glossary-djangomutation] surface or the form flavor. It is the
single highest-leverage write-side feature for the [`GOAL.md`][goal] DRF-migration
audience — `GOAL.md` names DRF a first-class migration source and its
success-criterion 6 spells the serializer flavor verbatim
(`class CreateCategoryFromSerializer(DjangoMutation): class Meta: serializer_class =
CategorySerializer`).

The flavor reuses the contracts [`spec-036`][spec-036] **froze for exactly this**
and [`spec-038`][spec-038] proved reusable: the shared
[`errors: list[FieldError]`][glossary-fielderror-envelope] envelope (populated here
from `serializer.errors`; the envelope is **additive, not frozen** — this card extends
it with the default-empty `codes` / `path` members every write flavor gains together,
[Decision 2](#decision-2--card-scope-boundary-the-serializer-flavor-ships-auth-stays-out-the-frozen-036-contracts-and-the-038-factory-are-reused-unchanged)),
the generated `<Name>Payload` wrapper with its uniform
`node` / `result` object slot, the [`DjangoMutationField`][glossary-djangomutationfield]
exposure factory (which [`spec-038`][spec-038] **already generalized** along its three
model-hardwired axes "for exactly the `0.0.13` serializer flavor" — see
[Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused)),
the write-authorization seam ([`DjangoModelPermission`][glossary-djangomodelpermission]
/ `Meta.permission_classes` / `check_permission`), and the overridable
[`_resolve_model`][spec-036] / `_validate_meta` / `build_input` / `input_type_name` /
`input_module_path` / `resolve_sync` / `resolve_async` seams ([`spec-036`][spec-036]
Decision 5, [`spec-038`][spec-038] Decision 6) that let the serializer flavor supply
its model from `serializer_class.Meta.model` and its input from a serializer-field
converter **without** re-opening the base. The only genuinely new machinery is a
`rest_framework/serializer_converter.py` DRF-field → Strawberry-input mapping and a
serializer pipeline (`is_valid()` → `serializer.errors` → `serializer.save()`) that
swaps the model-construct + `full_clean()` heart of the [`spec-036`][spec-036]
resolver — and the **soft `djangorestframework` dependency** that makes the package
import without DRF installed
([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).

**Version boundary** (see
[Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)): unlike
[`spec-038`][spec-038] (the lone `0.0.12` card, which owned its own bump), `039`
**shares the `0.0.13` patch line** with the sibling [Auth mutations][glossary-auth-mutations]
card [`DONE-040-0.0.13`][kanban] (which reuses the same envelope and
`DjangoMutation` base). So the `pyproject.toml` / `__version__` /
[`tests/base/test_init.py::test_version`][test-base-init] bump from `0.0.12` to
`0.0.13` is owned by the **joint `0.0.13` cut**, not by this card — the same posture
[`spec-036`][spec-036] Decision 13 took for the joint `0.0.11` cut it shared with
[`spec-037`][spec-037]. No slice in this card bumps the version.

Status: **SHIPPED (`0.0.13`)** — card [`DONE-039-0.0.13`][kanban], released
under the [`CHANGELOG.md`][changelog] `## [0.0.13]` heading; all five slices
(Slice 0 + Slices 1-4) final-accepted, the docs + card wrap landed in Slice 4. The
`0.0.13` version bump and the public release-status flip (the GLOSSARY
`shipped (0.0.13)` status, the `README.md` / [`docs/README.md`][docs-readme] "Shipped
today" move, the `CHANGELOG.md` bullets) belong to the joint cut shared with
[`DONE-040-0.0.13`][kanban], not to this card (see
[Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)). The
[Slice checklist](#slice-checklist) below stays unticked because the `Status:` line
is the completion source of truth (the shipped-spec convention). The card was
authored via the [`docs/SPECS/NEXT.md`][next] flow. The card's hard dependency was
satisfied: [`DONE-036-0.0.11`][kanban] (the mutation foundation this card subclasses)
has shipped, and [`DONE-038-0.0.12`][kanban] (which generalized the field factory and
proved the flavor-on-the-base pattern) has shipped too. **A pre-Slice-1 dependency gate
(Slice 0 — the `djangorestframework` dev-dep + `uv.lock` regen + the verified DRF floor)
plus four implementation/doc slices** (the resolver pipeline and the products
live surface are **one** slice, so the resolver's consumer-reachable behavior is earned
live in the same commit it lands — the
[`examples/fakeshop/test_query/README.md`][test-query-readme] #"Coverage rule." /
[`docs/TREE.md`][tree] #"Coverage priority." live-first mandate): Slice 1
(**DRF-field → Strawberry input mapping** — `rest_framework/serializer_converter.py`
+ the serializer-derived input generator;
[Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)),
Slice 2 (**the `SerializerMutation` base + `Meta` validation + the phase-2.5 bind** —
`rest_framework/sets.py`;
[Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused)
/
[Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)),
Slice 3 (**the serializer resolver pipeline + the products live serializer surface,
earned live** — `rest_framework/resolvers.py` lands together with the products
`ModelSerializer` mutation and its live `/graphql/` tests, which are the **primary**
coverage harness; the package-internal `tests/rest_framework/test_resolvers.py` holds
only genuinely-unreachable internals;
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
/
[Decision 9](#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path)
/
[Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation)),
and Slice 4 (**docs + card wrap, no version bump** — the soft-dep wiring is **not** here;
it landed in the Slice 0 gate; the per-card
[`CHANGELOG.md`][changelog] edit must be named explicitly in the Slice 4 maintainer
prompt — this spec describes the edit but cannot grant the permission
[`AGENTS.md`][agents] reserves for an explicit instruction).

Owner: package maintainer.

Predecessors: [`spec-038-form_mutations-0_0_12.md`][spec-038] (the most-recently-shipped
spec and the canonical voice / depth / section-layout reference; it is the **structural
twin** of this card — a soft-ish-dependency write flavor subclassing the `036` base
through the seams, with its own field converter, its own input generator, its own
resolver pipeline, and reusing [`DjangoMutationField`][glossary-djangomutationfield] —
so `rest_framework/` mirrors `forms/` module-for-module);
[`spec-036-mutations-0_0_11.md`][spec-036] (the foundation this card extends — it
**froze** the [`FieldError` envelope][glossary-fielderror-envelope], the
`<Name>Payload` uniform slot, the [`DjangoMutationField`][glossary-djangomutationfield]
factory, the [`DjangoModelPermission`][glossary-djangomodelpermission] write-auth seam,
and the [`_resolve_model`][spec-036] hook **explicitly for the form / serializer flavor
cards**, [Decision 2](#decision-2--card-scope-boundary-the-serializer-flavor-ships-auth-stays-out-the-frozen-036-contracts-and-the-038-factory-are-reused-unchanged));
[`spec-037-upload_file_image_mapping-0_0_11.md`][spec-037] (the precedent for a
**soft dependency met at the test tier** — `pillow` is an `ImageField` soft dep added
to the dev group so the suite covers it, exactly the posture
[Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)
takes for `djangorestframework`; its [`Upload`][glossary-upload-scalar] scalar is the
input type a serializer `FileField` / `ImageField` maps to);
[`spec-034-permissions-0_0_10.md`][spec-034] (the [`get_queryset`][glossary-get_queryset-visibility-hook]
visibility hook the `update` locate composes with);
[`spec-027-filters-0_0_8.md`][spec-027] / [`spec-028-orders-0_0_8.md`][spec-028]
(the set-family subpackage layout / phase-2.5 binding / materialize-before-`Schema`
discipline `mutations/` and `forms/` mirrored and `rest_framework/` mirrors again).
[`docs/GLOSSARY.md`][glossary] entered this card with
[`SerializerMutation`][glossary-serializermutation] at `planned for 0.0.13`; Slice 4
updates its **body** to the implemented contract (status
**"implemented on main, releasing in 0.0.13"**), and the `shipped (0.0.13)` flip defers to
the joint cut ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).

This spec's deliberative layer — the ten-revision authoring history that produced the
contract, every Decision's justification, every alternative each Decision rejected, and
the risk / open-question deliberation that settled the card's design questions — lives in
the rationale companion
[`docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`][spec-039-rationale].

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [`SerializerMutation`][glossary-serializermutation] — the subject. The glossary
  already pins its planned contract: a base consuming a DRF `Serializer` /
  `ModelSerializer` via `Meta.serializer_class` (`Meta.lookup_field`,
  `Meta.model_operations`, `Meta.optional_fields`), an input-type factory deriving the
  Strawberry input from the serializer's fields, a soft `rest_framework` dependency,
  and validation through the shared [`FieldError` envelope][glossary-fielderror-envelope].
  Slice 4 updates the entry's **body** to the implemented contract (status **"implemented
  on main, releasing in 0.0.13"**, the `shipped (0.0.13)` flip deferred to the joint
  cut) and reconciles the surface keys this spec pins (`Meta.operation` over
  `model_operations`, the `id:`-decode locate over `lookup_field` —
  [Risks](#risks-and-open-questions)).
- [`DjangoMutation`][glossary-djangomutation] /
  [Input type generation][glossary-input-type-generation] /
  [`DjangoMutationField`][glossary-djangomutationfield] — the shipped
  [`spec-036`][spec-036] foundation, generalized by [`spec-038`][spec-038]. The
  serializer flavor reuses the [`DjangoMutationField`][glossary-djangomutationfield]
  exposure factory **unchanged** (the `038` generalization already accepts any
  member of the mutation family via a duck-typed `_has_mutation_protocol` check), the
  generated-payload lifecycle, and the [`DjangoMutation`][glossary-djangomutation]
  base outright; the input *generation*, by contrast, is **serializer-derived here**
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- [`DjangoFormMutation`][glossary-djangoformmutation] /
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] — the `0.0.12` form
  flavor this card is the structural twin of. `SerializerMutation` mirrors
  `DjangoModelFormMutation` almost exactly: both subclass
  [`DjangoMutation`][glossary-djangomutation] via [`_resolve_model`][spec-036], both
  return the post-save object in the uniform `node` / `result` slot, both derive their
  input from the validation object (the form's / serializer's fields) rather than the
  model columns, both compose `create` / `update` only (no `delete`). The lessons
  `038` learned — the relation-id visibility decode, the `IntegrityError` envelope
  mapper, the soft-construction hook — port directly
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven) /
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)).
- [`FieldError` envelope][glossary-fielderror-envelope] — the shared error contract
  [`spec-036`][spec-036] **defined for this card**, and which this card extends
  additively with `codes` / `path`. A serializer mutation
  maps `serializer.errors` (a `field → [messages]` dict, with DRF's
  `non_field_errors` / `api_settings.NON_FIELD_ERRORS_KEY` bucket) onto that one shared
  envelope, keying serializer-level errors to the same `"__all__"`
  sentinel `036` pinned
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)).
- [`DjangoModelPermission`][glossary-djangomodelpermission] — the default
  write-authorization class the `ModelSerializer` flavor inherits unchanged (the
  serializer's model resolves the `add` / `change` perm through the
  [`_resolve_model`][spec-036] override)
  ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelserializer)).
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] /
  [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — the visibility
  seam the `update` locate composes with: a `SerializerMutation` `update` binds the
  serializer to a row located through the target type's
  [`get_queryset`][glossary-get_queryset-visibility-hook], so a hidden row is
  not-found, never an existence leak — the same contract `036` / `038` `update` use
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] /
  [`only()` projection][glossary-only-projection] — the post-save re-fetch
  cooperation. The payload's object is re-fetched and optimizer-planned for the
  response selection through the **same** `036` re-fetch path, so the
  [`spec-035`][spec-035] **G2** mutation gate (keep `select_related` /
  `prefetch_related`, suppress `.only(...)`) comes for free
  ([Decision 9](#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path)).
- [`Meta.primary`][glossary-metaprimary] / [`Meta.model`][glossary-metamodel] /
  [`DjangoType`][glossary-djangotype] — the return-payload type resolves the
  serializer model's **primary** [`DjangoType`][glossary-djangotype] through the
  registry primary lookup, exactly as `036` / `038` do
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).
- [Scalar field conversion][glossary-scalar-field-conversion] /
  [Choice enum generation][glossary-choice-enum-generation] /
  [`Upload` scalar][glossary-upload-scalar] — the converters the serializer-field
  mapping reuses where a serializer field's type overlaps a Django column type (so a
  serializer-derived input field resolves to the same scalar / enum / `Upload` the
  read side and the `036` model-driven input use)
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- [`ConfigurationError`][glossary-configurationerror] /
  [`SyncMisuseError`][glossary-syncmisuseerror] — the validation / misuse exceptions
  this card raises: `ConfigurationError` at serializer-mutation-class creation
  (missing `Meta.serializer_class`, a non-`Serializer` value, a `ModelSerializer`
  with no resolvable model, an unsupported serializer field), and `SyncMisuseError`
  when a sync serializer pipeline meets an `async def` target
  [`get_queryset`][glossary-get_queryset-visibility-hook] (the standing discipline
  `036` / `038` already route through).
- [Auth mutations][glossary-auth-mutations] — the sibling `0.0.13` card
  ([`DONE-040-0.0.13`][kanban]) that shares the joint cut and reuses the same
  envelope; named here to fix the out-of-scope boundary and the joint-version-bump
  ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] /
  [`FieldSet`][glossary-fieldset] / [Per-field permission hooks][glossary-per-field-permission-hooks]
  — the `1.0.0` invariant this card must not violate (a `DjangoType` `Meta` key is
  promoted only when its subsystem applies it end-to-end). A serializer mutation adds
  **no** `DjangoType` `Meta` key, so [`DEFERRED_META_KEYS`][types-base] is untouched
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).
- [Relation handling][glossary-relation-handling] /
  [Relay Node integration][glossary-relay-node-integration] /
  [`DjangoNodeField`][glossary-djangonodefield] — the relation-decode substrate. The
  serializer relation decoder type- and visibility-checks each `PrimaryKeyRelatedField` /
  `ManyRelatedField` id — a `GlobalID` **or** a raw pk — against the relation's target
  model, reusing the same server-side [`DjangoNodeField`][glossary-djangonodefield] decode
  the `id:` `update` locate rides, across the FK / OneToOne / M2M shapes
  [Relation handling][glossary-relation-handling] spans
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)).
- [RELAY_GLOBALID_STRATEGY][glossary-relay_globalid_strategy] /
  [`Meta.globalid_strategy`][glossary-metaglobalid_strategy] — the registry-wide / per-type
  strategy fixing whether a relation id is a Relay `GlobalID` or a raw pk, so the decoder
  accepts **both** forms against the target's primary [`DjangoType`][glossary-djangotype]
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- [Scalar field conversion][glossary-scalar-field-conversion] /
  [Specialized scalar conversions][glossary-specialized-scalar-conversions] /
  [`BigInt` scalar][glossary-bigint-scalar] — the read-side scalar registries the
  serializer-field converter reuses where a serializer field overlaps a model column
  (`DecimalField` → `Decimal`, `UUIDField` → `uuid.UUID`, a `BigIntegerField`-backed
  field → [`BigInt`][glossary-bigint-scalar]) rather than re-deriving the scalar
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- [Definition-order independence][glossary-definition-order-independence] — the
  finalize-time, materialize-before-`Schema` discipline the serializer-input bind rides:
  `SerializerMutation` registers at class creation and its inputs materialize during
  `bind_mutations()` at [`finalize_django_types`][glossary-finalize_django_types]
  phase 2.5 ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package-internal serializer-converter
  / base / resolver mechanics under [`tests/rest_framework/`][test-rest-framework]
  mirroring source; live consumer behavior over `/graphql/` when a realistic request
  reaches it —
  [Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation));
  the settings-keys-only-when-needed rule (this card adds no settings key); the
  no-pytest-after-edits rule; the CHANGELOG-edit-permission rule at
  [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" —
  Slice 4's release-note edit must be named in its maintainer prompt.
- [`START.md`][start] — "Meta classes everywhere on consumer surfaces. If you find
  yourself writing stacked Strawberry decorators on a consumer-facing class, stop."
  This is the decisive rule for
  [Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions); also
  the "behaviorally we copy `strawberry-graphql-django`'s good ideas, surface-wise we
  copy `django-graphene-filters`" rule (the serializer mutation is a graphene-django /
  DRF surface borrow, on a Strawberry engine) and the reference-style markdown link
  convention.
- [`CONTRIBUTING.md`][contributing] — the 100% coverage target (`fail_under = 100`);
  every converter branch, the `is_valid()` / `serializer.errors` paths, the `save()`
  path, **and the DRF-absent import guard** earn coverage in
  [`tests/rest_framework/`][test-rest-framework] plus the live products suite — which
  is exactly why DRF must be a dev-group dependency
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
- [`docs/TREE.md`][tree] — the target layout reserves
  `django_strawberry_framework/rest_framework/` (planned by this card) and
  [`tests/rest_framework/`][test-rest-framework]. The new **consumer-facing** subpackage is
  `rest_framework/`, but the card deliberately **promotes shared internals** to avoid third
  copies, so it also edits `utils/converters.py` (new),
  [`utils/inputs.py`][utils-inputs], [`utils/querysets.py`][utils-querysets],
  [`mutations/sets.py`][mutations-sets], [`mutations/resolvers.py`][mutations-resolvers],
  [`forms/`][forms-sets] (re-pointed to the shared sites), [`registry.py`][registry], and
  [`types/finalizer.py`][types-finalizer] — plus the products-example wiring and the Slice 0
  soft-dep edit. The [Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations)
  section is the binding list of those cross-module edits.
- [`GOAL.md`][goal] — success-criterion 6 ("Write mutations declaratively from
  `ModelForm`, `ModelSerializer`, or auto-generated `Input` types — one shared
  `errors: list[FieldError]` envelope across every flavor"); this card ships criterion
  6's `ModelSerializer` flavor — the last of the three named flavors to land — closing
  the write-side parity story.

## Slice checklist

Each top-level item maps to one commit / PR. **A pre-Slice-1 dependency gate (Slice 0)
plus four slices: serializer-field converter + input generation (Slice 1), the base
class (Slice 2), the resolver pipeline **+ the products live serializer surface, landed
together** (Slice 3), and docs + card wrap (Slice 4).** Slices 1–2 are package-internal
and staged (each builds on the prior); **Slice 3 lands the resolver and its live consumer
surface in one commit** — required by the [`examples/fakeshop/test_query/README.md`][test-query-readme]
#"Coverage rule." live-first mandate, so the resolver's reachable lines are earned by a
real `/graphql/` request (not a package test) at the commit they appear; Slice 4 is
doc + card-wrap only (no version bump — [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).

- [ ] Slice 0 (pre-Slice-1 dependency gate): verify + pin the DRF floor **before**
  any converter code, since Slice 1–3 tests import DRF.
  - [ ] **Verify the floor:** confirm a `djangorestframework` release that imports and runs
    **warning-free** across the [`django.yml`][django-workflow] CI matrix (Python
    3.10 → 3.14 × Django 5.2 → 6.0 / `latest`) under [`pytest.ini`][pytest-ini]'s
    `filterwarnings = error` (DRF's Django support lags Django, so a 6.0 / `latest`-clean
    release must be confirmed to exist), and record the **exact pinned floor**
    ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
  - [ ] **The floor check is an explicit acceptance artifact, not a normal pytest
    assertion** (the suite cannot prove a *matrix-wide* warning-free import from inside one
    interpreter). The artifact is one of: (a) a short probe script
    (`scripts/check_drf_floor.py`) that imports `rest_framework` under `-W error` and asserts
    the installed version `>=` the recorded floor, runnable on each matrix node; **or** (b) a
    documented sequence of explicit `uv` commands (e.g.
    `uv run --python 3.14 --with 'django>=6.0' python -W error -c "import rest_framework"`
    across the Python × Django cells) recorded in the Slice 0 PR description. The **chosen
    floor is recorded in three places that must agree**: the `[dependency-groups].dev`
    `djangorestframework>=<floor>` pin in [`pyproject.toml`][pyproject], the
    `require_drf()` guard's **install hint**, and the recorded floor in
    [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy).
    If no compatible release exists, the card **blocks at
    the gate**, not mid-Slice-1.
  - [ ] **Wire the dev dependency:** add `djangorestframework` to
    `[dependency-groups].dev` (NOT `[project].dependencies` — it stays a soft runtime dep)
    in [`pyproject.toml`][pyproject], regenerate `uv.lock` (`uv lock`), and add any
    **targeted DRF-origin `ignore::` line** to [`pytest.ini`][pytest-ini] the verified
    release still needs — all **before** Slice 1. **No package-version edits** (stays
    `0.0.12`, [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
- [ ] Slice 1: DRF-field → Strawberry input mapping + the serializer-derived input
  generator (per
  [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)
  / [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy))
  - [ ] [`rest_framework/serializer_converter.py`][rf-converter]: a
    `convert_serializer_field(field)` registry (the graphene-django
    [`convert_serializer_field`][upstream-serializer-converter] parity shape)
    returning the Strawberry annotation + required-ness for each supported DRF
    serializer-field class (`CharField` → `str`, `ChoiceField` → `str` *base* —
    a serializer-only `ChoiceField` is upgraded to a generated enum at the build site,
    `IntegerField` → `int`, `BooleanField` → `bool`, `FloatField` → `float`, `DecimalField` →
    `Decimal`, `DateField` / `DateTimeField` / `TimeField` → Python-native,
    `UUIDField` → `uuid.UUID`, `JSONField` → `strawberry.scalars.JSON`, `ListField` →
    `list[<scalar child>]` (scalar `child` only — a relation / nested-serializer `child`
    raises [`ConfigurationError`][glossary-configurationerror]),
    `PrimaryKeyRelatedField` → the target's id,
    `PrimaryKeyRelatedField(many=True)` / `ManyRelatedField` → `list[<id>]`,
    `FileField` / `ImageField` → [`Upload`][glossary-upload-scalar]). **Fail-loud
    dispatch (mirroring [`forms/converter.py`][forms-converter]):** the registry is an
    MRO-walk over individually-registered classes with a **raising fallthrough** —
    **NOT** `functools.singledispatch` with the graphene-django
    `serializers.Field → String` catch-all, which would shadow the raise so every
    custom field silently became `String`; an unmapped `serializers.Field` subclass
    raises [`ConfigurationError`][glossary-configurationerror] naming the field and
    class. Where a serializer field maps to a Django column type the read side already
    converts (a `ModelSerializer` field over a `choices` column), reuse the
    [Scalar field conversion][glossary-scalar-field-conversion] /
    [Choice enum generation][glossary-choice-enum-generation] registry at the build
    site — keyed on the **backing `models.Field` resolved via the serializer field's
    `source`**, not its declared name — rather than re-deriving the scalar. Record, per
    generated input field, a `utils/inputs.py::InputFieldSpec` reverse-map entry
    (`input_attr` / `graphql_name` / `target_name` / `kind` / `source` / `related_model` /
    `nested_specs` / `annotation_repr` / `required`; `kind ∈ {scalar, relation_single,
    relation_multi, file, nested_single, nested_multi}`) the resolver
    needs to build a payload keyed by the declared serializer field name —
    `categoryId` → `category`, a renamed `category_pk` (`source="category"`) → input
    `categoryPk` decoded back to `category_pk` (the `038` `FormInputFieldSpec` analog
    **plus the `source` axis**,
    [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)
    **Renamed fields**: omitted / one-segment `source` supported, dotted `source` /
    `source="*"` rejected for a model-column-converting field). The whole module is
    behind the DRF soft-import guard
    ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
  - [ ] [`rest_framework/inputs.py`][rf-inputs]: build **two** `@strawberry.input`
    classes from the **serializer's schema-time field set** — discovered via the
    overridable `get_serializer_for_schema()` classmethod (default: no-arg
    `serializer_class()`, read `.fields`; a serializer requiring constructor context
    overrides it to return a stable, request-independent field shape; a serializer whose
    field set varies per request is rejected loudly —
    [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)) —
    narrowed by [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude], with `read_only` / `HiddenField`
    fields dropped from the input and `Meta.optional_fields` forced optional —
    graphene's `fields_for_serializer(is_input=True)` parity) — `<Serializer>Input`
    (create; each field's requiredness from `field.required` minus the
    `optional_fields` override) and `<Serializer>PartialInput` (update; every field
    optional) — under a **`SerializerInputShape` descriptor identity** (NOT the
    name-only `036` / `038` key): the backing serializer, the operation kind, the ordered
    emitted field specs, the post-widening annotations, the emitted descriptions, the
    required state, the normalized `optional_fields` set and the type name, so two same-name-set
    inputs that differ in requiredness (`optional_fields`) or hook-returned field specs
    get **distinct** deterministic names, never silent reuse
    ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
    Canonical `<Serializer>Input` / `<Serializer>PartialInput` for the default full
    shape, descriptor-derived names for any divergent shape, identical descriptors
    dedupe, two distinct descriptors on one generated name → finalize-time
    [`ConfigurationError`][glossary-configurationerror]. **Run the create-required
    narrowing guard (`guard_create_required_serializer_fields`) PER declaration, BEFORE
    the descriptor cache lookup** — raise if `Meta.fields` / `Meta.exclude` drops a
    writeable (`read_only` / `HiddenField` exempt) `field.required`-with-no-default
    serializer field. `Meta.injected_fields` is the only field-level subtraction:
    each name must be writable on the same schema-time basis as input generation,
    narrowed out of the client input, and supplied by `get_serializer_injected_data`.
    Reuse [`utils/inputs.py`][utils-inputs]'s `build_strawberry_input_class`
    + `materialize_generated_input_class` core (the latter's ledger gives the collision
    raise for free) and materialize as module globals of the `rest_framework` input
    namespace for the [`strawberry.lazy`][glossary-djangomutationfield] forward-ref.
    Normalize + fail-loud `Meta.fields` / `Meta.exclude` against the serializer's
    field set (bare string, duplicates, unknown names, empty effective set →
    `ConfigurationError`, through the one shared
    `utils/inputs.py::normalize_field_name_sequence(..., flavor="SerializerMutation")`
    every flavor calls).
  - [ ] Package coverage: [`tests/rest_framework/test_converter.py`][test-rest-framework]
    — each supported serializer-field class → its annotation + required-ness; the
    `PrimaryKeyRelatedField` / `ManyRelatedField` id mapping (Relay-`GlobalID` vs raw
    pk by the target's primary [`DjangoType`][glossary-djangotype]); the serializer
    `FileField` → [`Upload`][glossary-upload-scalar] mapping; **renamed fields** — a
    `source="category"` relation and a `source="name"` scalar derive the GraphQL name
    from the **declared** field name, resolve the backing `models.Field` via `source`,
    and preserve the declared name in the reverse map; **the id-like suffix rule** —
    `category` → `categoryId`, `category_id` → `categoryId`, `category_pk` →
    `categoryPk` (no doubled `…IdId` / `…PkId`); a **dotted `source`** / `source="*"` on
    a model-column-converting field raises
    [`ConfigurationError`][glossary-configurationerror]; the unknown serializer-field
    [`ConfigurationError`][glossary-configurationerror]. And
    [`tests/rest_framework/test_inputs.py`][test-rest-framework] — the serializer-derived
    input shape (fields from the schema-time set, required-ness from `field.required`,
    `read_only` dropped, `Meta.fields` / `Meta.exclude` narrowing,
    `Meta.optional_fields` force-optional, `optional_fields = "__all__"` bare-string
    rejected), materialized as a module global; **the schema-time hook** — a serializer
    whose `__init__` requires kwargs **and** one whose `get_fields()` reads `self.context`
    (so it raises at **`.fields` access**, not at construction — proving the guard wraps
    `.fields`, not `serializer_class()`) are both rejected loudly under the default no-arg
    discovery, and an override of `get_serializer_for_schema()` supplying a stable field
    map generates the input; **`SerializerInputShape` descriptor identity** — two create
    mutations over the **same** serializer + effective fields but **different**
    `Meta.optional_fields` get distinct deterministic names (not silent reuse), and two
    schema hooks returning same-named fields with **different annotations / `source` /
    relation kind** likewise diverge (or raise `ConfigurationError` on a name collision),
    identical descriptors dedupe; **the create-required narrowing guard** — excluding a
    required scalar, a required serializer-only field, or a required relation raises
    [`ConfigurationError`][glossary-configurationerror], while `read_only` /
    `HiddenField` fields are outside the writable basis. The guard runs **per
    declaration**; one declaration's `Meta.injected_fields` never suppresses a later
    declaration's guard on the same cached shape.
  - [ ] **DRY / reuse** ([Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations)):
    `convert_serializer_field` rides the shared fail-loud dispatch **skeleton** promoted to
    `utils/converters.py` (supplying only its precheck table + scalar registry — the
    no-silent-`String`-catch-all contract single-sited with
    [`forms/converter.py`][forms-converter]); the reverse-map field spec is the
    unified `InputFieldSpec` sited in [`utils/inputs.py`][utils-inputs] (the `038`
    `FormInputFieldSpec` analog + the `source` axis, with the conversion result a shared
    shape too); the input namespace is the promoted `make_input_namespace(...)`
    **one-ledger** trio (the form/mutation clear shape, NOT the heavier
    `clear_generated_input_namespace`); the `SerializerInputShape` cache + clear is
    the promoted `make_shape_build_cache()` plumbing; and the divergent-shape
    suffix reuses `utils/inputs.py::pascalize_token`.

    **The DoD check is an object-identity ratchet, not a grep**
    ([`tests/rest_framework/test_dry_import_ratchet.py`][test-dry-ratchet]), parametrized
    one node id per row over a manifest of `(consumer module, symbol, owning module)`
    triples; the factory-produced one-ledger closures cannot be object-identical across
    flavors, so their cross-flavor twins are held by `__code__` identity in a second
    manifest. The population is stated explicitly rather than left to a pronoun: the
    four dispatch-skeleton symbols (`convert_with_mro`, `make_kind_converter`,
    `make_scalar_converter`, `finish_field_conversion`), **both** shared conversion shapes
    (`InputFieldSpec` and the conversion base `FieldConversionBase`), the
    one-ledger namespace trio, the shape-build cache pair (`make_shape_build_cache`,
    `get_or_store_shape_build`), the suffix helper (`pascalize_token`), the four
    input-kind constants (`SCALAR` / `FILE` / `RELATION_SINGLE` / `RELATION_MULTI`),
    `build_strawberry_input_class`, `normalize_field_name_sequence`, and
    `graphql_camel_name` in both consumer modules. One ceiling is stated rather than
    implied: the input-kind constants are interned `str`, so their rows catch a deletion
    and a value drift but not a same-valued re-spelling.
- [ ] Slice 2: the `SerializerMutation` base + `Meta` validation + the phase-2.5 bind
  (per
  [Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused)
  /
  [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven))
  - [ ] [`rest_framework/sets.py`][rf-sets]: `SerializerMutation` (subclasses
    [`DjangoMutation`][glossary-djangomutation], overriding [`_resolve_model`][spec-036]
    → `Meta.serializer_class.Meta.model`, plus the `_validate_meta` / `build_input` /
    `input_type_name` / `input_module_path` / `resolve_sync` / `resolve_async` seams —
    the **exact** override set [`DjangoModelFormMutation`][glossary-djangomodelformmutation]
    uses in [`forms/sets.py`][forms-sets]). The serializer-flavor `_validate_meta`
    override: `Meta.serializer_class` is required and must be a DRF
    `serializers.Serializer` subclass; for the `ModelSerializer`-driven contract it
    must be a `serializers.ModelSerializer` with a resolvable `Meta.model`
    (a non-`ModelSerializer` or a `ModelSerializer` with no `Meta.model` raises a
    targeted [`ConfigurationError`][glossary-configurationerror]). The check runs
    **before** `_resolve_model` (so a missing / wrong-type `serializer_class` is a
    clean `ConfigurationError`, never a raw `AttributeError`). **`operation` is
    `create` / `update` only** (a `"delete"` serializer mutation is **rejected** —
    DRF serializers do not delete, [Decision 10](#decision-10--operations-create--update-no-serializer-delete)),
    and its shape-identity operation component is that value. The serializer
    allowed-key set is the shared `mutations/sets.py::MODEL_BACKED_WRITE_META_KEYS`
    (`fields` / `exclude` / `permission_classes` / `operation` / `select_for_update` — the
    `036` write-auth seam inherited unchanged,
    [Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelserializer))
    **plus** `serializer_class` / `optional_fields` / `injected_fields` /
    `nested_fields`; it **drops** the model flavor's `model` / `input_class` /
    `partial_input_class`; `Meta.fields` / `Meta.exclude` are mutually exclusive. The
    whole module is behind the DRF soft-import guard
    ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
  - [ ] No change to [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS`: a
    serializer-mutation `Meta` is its own validation namespace
    ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).
  - [ ] [`types/finalizer.py`][types-finalizer] / [`registry.py`][registry]: because
    `SerializerMutation` subclasses [`DjangoMutation`][glossary-djangomutation] it
    **rides the existing `bind_mutations()`** (the same way
    [`DjangoModelFormMutation`][glossary-djangomodelformmutation] does — finalizer
    comment "the ModelForm flavor rides bind_mutations yet writes the FORM ledger");
    its `build_input` override materializes into a `rest_framework` input namespace, so
    it needs a `clear_serializer_input_namespace()` ledger-clear ([`rest_framework/inputs.py`][rf-inputs],
    the [`forms/inputs.py`][forms-inputs] `clear_form_input_namespace` precedent) run from
    **two clear sites** — the [`forms/inputs.py`][forms-inputs] / [`mutations/inputs.py`][mutations-inputs]
    co-clear precedent **in full**:
    1. **The `finalize_django_types` pre-bind reset block.**
       [`finalize_django_types`][glossary-finalize_django_types] clears the
       `mutations.inputs` **and** `forms.inputs` ledgers **once, immediately before**
       the bind sequence (`clear_mutation_input_namespace()` /
       `clear_form_input_namespace()` → `bind_mutations()`) so a finalize that **fails
       on a later type is retry-idempotent** — the ledgers persist across passes, so no
       single pass can soundly clear them itself. The serializer input ledger has the
       **identical** retry-idempotence problem (it materializes during `bind_mutations()`
       yet survives a later-type failure), so `clear_serializer_input_namespace()` joins
       that same pre-bind reset, not a per-pass clear.
    2. **`TypeRegistry.clear()`** — a full registry reset must wipe serializer inputs too,
       alongside the existing mutation / form co-clears.

    **The clear is wired through the mandatory `register_subsystem_clear` seam — NOT two
    hand-edits.** Rather than hand-add the serializer's clear to **both** sites
    above (a permanent two-list synchronization hazard — and adding the serializer would make
    it a *third* subsystem relying on manually-mirrored clears, exactly the debt this card
    removes), Slice 2 promotes a
    `register_subsystem_clear(clear, *, owner, before_bind=False)` seam feeding **one
    canonical registry** that **both** the finalizer pre-bind reset and `TypeRegistry.clear()`
    iterate. **This is a Slice 2 requirement, not a budget-dependent option.** A row is a
    **zero-argument callable plus a stable `owner` string**, registered by the module that
    owns the state — the serializer registers
    `clear_serializer_input_namespace` with `before_bind=True` from
    [`rest_framework/inputs.py`][rf-inputs]'s own module body. A **string reference is
    rejected** (`TypeError`), and `owner` is a logical identity rather than an import path,
    so factory-generated callbacks register without colliding and an `importlib.reload`
    replaces the old function object instead of accumulating duplicates. `before_bind`
    selects the subset the finalizer also runs before rebuilding generated types; every
    registered callback runs for the test-only full `TypeRegistry.clear()` lifecycle. Two
    consequences follow, both load-bearing:
    - **The soft-dep asymmetry vanishes.** Laziness comes from the **registration site**:
      only an imported owner can register, and `rest_framework/inputs.py` is imported only
      when DRF is present, so a DRF-absent build registers nothing and clears nothing. The
      special-case the direct mutation / form clears would otherwise need for the
      DRF-behind-soft-import serializer ledger (`finalize_django_types` runs on **every**
      build, including DRF-absent ones, where a direct
      `from ..rest_framework.inputs import …` would raise `ImportError` and break schema
      construction for everyone without DRF) collapses to a **one-line registration**. It is
      also semantically exact: DRF absent ⇒ no
      [`SerializerMutation`][glossary-serializermutation] declared ⇒ the serializer ledger is
      empty ⇒ no clear is owed.
    - **The import-timing edge is a non-issue.** The backstop invariant is **a
      subsystem that has created clearable state has, by definition, been imported and
      registered its clear** (stale serializer ledger state implies `rest_framework.inputs`
      was imported in a prior failed bind), so a registered-but-not-yet-imported gap cannot
      leave dirty state. Requiring the callable at registration is what makes a rename fail
      loudly at the owner's own import instead of silently leaving state uncleared.

    A **retry-idempotence test** (materialize serializer input, fail a later type, rerun
    finalization, assert the serializer ledger was cleared) locks it.

    **No new bind entry point** (no `bind_serializer_mutations()`) — that is the dividend
    of the `ModelSerializer`-rides-`DjangoMutation` choice
    ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).
  - [ ] [`__init__.py`][init]: export the serializer flavor's public surface via a
    **root-level `__getattr__`** (PEP 562) — every name in `_DRF_SOFT_EXPORTS` is
    resolvable by **name** (`from django_strawberry_framework import SerializerMutation`)
    through the
    shared `require_drf()` guard (DRF absent → `ImportError` with the install hint), but is
    **NOT added to `__all__`** while DRF is soft, so `from django_strawberry_framework
    import *` stays DRF-free and never trips the guard (a star import consults
    `__all__` and would otherwise break for DRF-absent consumers). `import
    django_strawberry_framework` succeeds without DRF (the root never eagerly imports
    `rest_framework/`). This is the one root edit; the eager-import + explicit-`__all__`
    style of the existing root is otherwise preserved
    ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
  - [ ] Package coverage: [`tests/rest_framework/test_sets.py`][test-rest-framework] —
    the `Meta` validation matrix (missing / wrong-type `serializer_class`, a plain
    `Serializer` with no model rejected, `ModelSerializer`-with-no-model,
    `operation = "delete"` rejected, `serializer_class` accepted as a known key,
    `fields` + `exclude` both set, unknown key), registration, finalizer binding (the
    `bind_mutations()` path), the no-registered-primary-type error, and — proving the
    base is unregressed — the model-flavor seam defaults unchanged.
  - [ ] **DRY / reuse** ([Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations)):
    `_validate_meta` reuses `mutations/sets.py::_validate_permission_classes`, the shared
    non-delete ops set (a promoted `NON_DELETE_WRITE_OPERATIONS` both flavors import — NOT a
    new `_VALID_SERIALIZER_OPERATIONS`), and the promoted
    `reject_unknown_meta_keys(name, meta, allowed)` typo-guard called with
    `_ALLOWED_SERIALIZER_META_KEYS`, then returns a `_ValidatedMutationMeta`; the
    field-sequence call is
    `utils/inputs.py::normalize_field_name_sequence(..., flavor="SerializerMutation")`
    **directly** — the one entry point all three flavors call, with no per-flavor
    re-binding wrapper anywhere (the required keyword-only `flavor` arg exists
    for exactly this); the `build_input` /
    `input_type_name` cluster rides the promoted `build_and_stash_input` core
    (materialize-then-stash, NOT a byte-parallel `_build_and_stash_serializer_input`)
    — but its per-shape dedupe is keyed on the `SerializerInputShape` DESCRIPTOR,
    which is only knowable AFTER the build, so it does NOT route through
    `cached_build_input` (whose pre-build key lookup the form flavor can use but the
    serializer cannot without building the shape twice); required-field injection is
    explicit through `Meta.injected_fields` + `get_serializer_injected_data`, never inferred
    from constructor-hook overrides; and the input-ledger clear registers
    through `register_subsystem_clear` (the finalizer item above).

    The serializer's genuinely-new `_validate_meta` logic is the `serializer_class`
    is-a-`ModelSerializer` (+ resolvable `Meta.model`) check, `optional_fields` normalization,
    `Meta.injected_fields` (normalize, then guard against the writable basis and against a name
    still present in the generated input), `Meta.select_for_update` through the shared
    `validate_select_for_update`, `Meta.nested_fields` including the
    `create()` / `update()`-override requirement, validation of the
    `get_serializer_for_schema()` field map, capture of the schema fingerprint, and
    the recursive writable-`source` ownership walk.
- [ ] Slice 3: the serializer resolver pipeline **+ the products live serializer
  surface, landed in one commit** (per
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
  /
  [Decision 9](#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path)
  /
  [Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation)).
  **The resolver code and its consumer surface ship together** so every
  consumer-reachable resolver line is earned by a real `/graphql/` request the moment it
  lands — the [`examples/fakeshop/test_query/README.md`][test-query-readme]
  #"Coverage rule." live-first mandate; splitting them would force package tests to cover
  reachable lines at the resolver commit, the inverse of the rule.
  - [ ] [`rest_framework/resolvers.py`][rf-resolvers]: the sync + async pipeline, in
    the **locate → authorize → decode → construct → validate → write → re-fetch** order
    (`036` / `038` security invariant — authorize **before** any relation decode) —
    (`update`) **locate** the row through the target type's
    [`get_queryset`][glossary-get_queryset-visibility-hook] (not-found → a `FieldError`
    on `id`, no existence leak; `create` has no locate); **authorize** via the inherited
    `check_permission` / `Meta.permission_classes` against the **raw** input payload
    (`create`: `instance=None`; `update`: the located instance) — denial → top-level
    `GraphQLError`, run **before** decode so an unauthorized caller cannot probe
    relation visibility by id; **decode** the `data:` input via the reverse map into a
    serializer-field-keyed `provided_data`, using a **dedicated serializer relation
    decoder** that mirrors the `038` form decoder (serializer-field-keyed, NOT the
    model-attr-keyed `036` `_decode_relation_id_set`). **The generated input field exposes
    exactly ONE strategy-dependent shape** (Decision 7): a `GlobalID` when the target primary
    [`DjangoType`][glossary-djangotype] is Relay-shaped, else the target's raw-pk scalar — so
    a live request can only deliver the one shape the annotation admits; the **shared decode
    helper** accepts both a `GlobalID` and a raw pk only because it is reused and package
    tests drive the raw-pk / non-Relay branch by direct call. Each id the decoder sees
    is type-checked against the relation's **target model** — resolved from the backing FK
    via the serializer field's `source`, **or, for a serializer-only relation, from the DRF
    field's `queryset.model`** (Decision 7) —
    resolved to the **visible** object through the related primary
    `DjangoType.get_queryset` — the same per-branch raw-pk visibility check both
    `036`'s model-path decoder (`_decode_relation_id_set` → `_raw_pk_relation_error`)
    and the `038` form decoder (now the shared `visible_related_object`) already enforce — and reduced
    to the pk DRF expects for a `PrimaryKeyRelatedField` before landing under the
    serializer field name; a hidden target → field-keyed `FieldError`; a serializer `FileField` /
    `ImageField` value (an [`Upload`][glossary-upload-scalar]) is routed into the
    serializer's `data` like any other value (DRF serializers read files from `data`,
    unlike Django forms which split `files=`); **construct** the serializer with
    **framework-built `data`** (decoded client input + the exact-match
    `Meta.injected_fields` values from
    `get_serializer_injected_data(self, info, *, data, hook_context)`), the
    **constructor-only** `get_serializer_kwargs(self, info, *, data, hook_context)` hook
    merged in for non-reserved kwargs only, and `data` / `instance` / `partial` /
    `context["request"]` / `context["write_alias"]` framework-owned — `partial=True` on
    `update` (DRF's native partial-update, no full-payload reconstruction, the divergence
    from `038`'s form reconstruction) and
    `context["request"] = request_from_info(info, family_label="SerializerMutation")`
    (the package's shared request-extraction helper,
    [`utils/permissions.py`][utils-permissions]) set unconditionally after the merge, so
    the serializer's own validators / `HiddenField(default=CurrentUserDefault())` resolve
    against the same actor the permission seam authorized; hooks receive a frozen
    `SerializerHookContext` plus an immutable data view, never the live located instance
    ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
    step 4);
    **validate** via `serializer.is_valid()` — a failure maps the nested
    `serializer.errors` onto the [`FieldError` envelope][glossary-fielderror-envelope]
    via a **dedicated recursive flattener** (`serializer_errors_to_field_errors`, dotted
    path `items.0.name`, DRF's `non_field_errors` / `NON_FIELD_ERRORS_KEY` bucket → the
    `"__all__"` sentinel `036` froze at every level — NOT the one-level `036`
    `validation_error_to_field_errors`) and returns a null-object payload; **write** via
    `serializer.save()`, **wrapped by the shared `utils/errors.py::integrity_error_field_errors`
    `IntegrityError` → envelope mapper** in a **value-preserving closure** (the wrapper discards its
    callable's return, so the resolver captures `saved = serializer.save()` via
    `nonlocal` — called exactly once); **re-fetch** the saved object by `saved.pk`
    + optimizer-plan; **return** the `<Name>Payload` (`node` / `result`). The whole
    pipeline runs inside one `transaction.atomic()`, and the async path runs the sync
    body in one `sync_to_async(thread_sensitive=True)` call — the same boundary
    `036` / `038` set.
  - [ ] [`mutations/fields.py`][mutations-fields]: **no change** —
    [`DjangoMutationField`][glossary-djangomutationfield] was already generalized by
    [`spec-038`][spec-038] Slice 3 along its three model-hardwired axes (target check
    via the duck-typed `_has_mutation_protocol`, `_resolve` dispatch via
    `mutation_cls.resolve_sync` / `resolve_async`, the `data:` lazy-ref via
    `mutation_cls.input_type_name` + `input_module_path`), explicitly "for the
    `0.0.13` serializer flavor". Slice 3 **verifies** the generalization holds for
    `SerializerMutation` (a `tests/mutations/test_fields.py` extension); no field-factory
    edit is needed ([Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused)).
  - [ ] **Products live serializer surface (same commit).**
    [`examples/fakeshop/apps/products/serializers.py`][products-serializers] (new): an
    `ItemSerializer` (`serializers.ModelSerializer` over `Item`, with a
    `validate_<field>` and a cross-field `validate()`) and a second serializer mutation
    (or fields on `ItemSerializer`) exposing the two **shipped runtime branches** that
    are real `/graphql/` behavior, not future-`TestClient` work: the
    [`Item.attachment`][products-models] `FileField` as an [`Upload`][glossary-upload-scalar]
    input (a real multipart create — the [`test_uploads_api.py`][test-uploads-api]
    `MediaSpecimen` multipart precedent proves `django.test.Client` drives this today),
    and an **observable request-context path** — an explicit `validate()` /
    `validate_<field>()` that reads `self.context["request"].user`, proving the injected
    `context={"request": …}` lands. **The live proof must be a `validate()` branch, not a
    `HiddenField(default=CurrentUserDefault())`**: DRF hidden-field defaults are
    subtle under `partial=True` (a hidden field's default behavior differs between full and
    partial validation), so they are not a stable way to prove update-time request context.
    `HiddenField` stays covered only as an input-generation / drop rule (and, if desired, a
    create-only behavior), never as the request-context proof.
    [`products/schema.py`][products-schema] gains the `SerializerMutation`(s)
    (create + update); `config/schema.py` already wires `mutation=Mutation`
    ([`spec-036`][spec-036] Slice 4). The example settings add `"rest_framework"` to
    `INSTALLED_APPS` only if a serializer needs the app registry (most flat
    `ModelSerializer`s do not). DRF being a dev-group dependency
    ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy))
    keeps it present in the test context (the [`spec-037`][spec-037] `pillow` /
    `MediaSpecimen` precedent).
  - [ ] **Live coverage is the primary harness** ([`test_products_api.py`][test-products-api],
    seeded via `seed_data` / `create_users`): **every consumer-reachable resolver branch
    is earned here over real `/graphql/`** — create / update happy paths;
    field-level (`validate_<field>`) and `"__all__"` (cross-field `validate()` /
    `unique_item_per_category`) `serializer.errors` envelopes; `categoryId` reverse-map
    validate-and-write through the serializer's `category` `PrimaryKeyRelatedField`;
    **partial-update preservation** (`name`-only update preserves `category` /
    `description` via `partial=True`) and the unique-together fire on a one-field change;
    the **visibility-scoped `update`** (hidden row → not-found); **write authorization**
    (anonymous / missing-perm denied, permitted succeeds); **a hidden-`Category`
    `GlobalID` → field-keyed `FieldError`** (relation visibility) and
    **authorize-before-decode** (an unpermitted caller submitting that hidden id gets the
    auth denial, not the relation error); the **multipart `Upload` → `Item.attachment`**
    write; the **request-context** `validate()` path; and the **G2 optimizer re-fetch
    query shape**, which splits across the two tiers because its halves are reachable
    differently: the **behavioral** half is earned live at
    [`test_products_api.py`][test-products-api]`::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`
    (the response keeps the relation, at a bounded absolute query count), while the
    **plan-object** half — that the optimizer's stash carries `select_related` /
    `prefetch_related` and suppresses `.only(...)` — is package-internal at
    [`tests/rest_framework/test_resolvers.py`][test-rest-framework]`::test_serializer_refetch_keeps_select_related_suppresses_only`,
    because the stash is introspection state no `/graphql/` response carries.
  - [ ] **Package-internal, genuinely-unreachable internals only**
    ([`tests/rest_framework/test_resolvers.py`][test-rest-framework]): the residue a live
    fakeshop query **cannot** drive — the **recursive flattener** shapes no products
    serializer emits (deeply nested `ListField` / dict child errors, `<path>.__all__`
    normalization); **raw-pk / non-Relay** relation decoding and **many-relation**
    decoding (products' `Category` is Relay-`GlobalID` and single, so these need a
    synthetic non-Relay / many fixture); the **call-once save capture** (a save spy);
    the **sync + async** boundary (`sync_to_async(thread_sensitive=True)`) and the
    [`SyncMisuseError`][glossary-syncmisuseerror] async-hook-from-sync path; and hermetic
    `get_serializer_kwargs` / constructor seams not observable over HTTP. **No
    create/update happy path, envelope, reverse-map, partial-update, visibility, or
    write-auth test is duplicated here** — those are owned by the live suite above
    (the [`examples/fakeshop/test_query/README.md`][test-query-readme] #"Coverage rule.").
  - [ ] **DRY / reuse** ([Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations)):
    the sync pipeline rides the promoted `run_write_pipeline_sync(...)` skeleton — the ONE
    write orchestration every flavor rides (model create / update / delete, `ModelForm`,
    serializer, and the model-less plain form) — supplying only its `decode_step` +
    `write_step` callbacks (construct / `is_valid()` / `save()`), so the
    `transaction.atomic()` boundary and the **authorize-before-decode security ordering**
    are single-sited rather than hand-copied a third time, with the existing model /
    model-form suites staying byte-equivalent; the relation decoder re-keys over the
    promoted `visible_related_object` in [`utils/querysets.py`][utils-querysets] rather
    than forking a third object-returning decoder; and
    `serializer_errors_to_field_errors` (recursive, legitimately new)
    imports the shared `mutations/inputs.py::NON_FIELD_ERROR_KEY` sentinel — and ideally a
    promoted `field_error(path, messages)` leaf ctor both flatteners call — so the DRF
    `non_field_errors` → `"__all__"` mapping cannot drift from the flat `036` mapper.
    The promotions themselves edit `mutations/resolvers.py` / `utils/querysets.py`
    (with `forms/resolvers.py` re-pointed to the shared sites); the `036` leaf helpers stay
    reused-by-call.
  - [ ] **Config-assessment grep-guard (query-path strategy).** A relation `GlobalID` is
    decoded against the target type's **recorded** `effective_globalid_strategy`
    ([`types/relay.py`][types-relay] / [`types/definition.py`][types-definition], resolved
    once at finalization). A Slice 3 DoD check **greps [`rest_framework/resolvers.py`][rf-resolvers]
    for `conf.settings` and `_resolve_globalid_strategy`** and asserts **neither appears** on
    the query path (no per-request setting re-read / re-validation), backed by the
    post-finalization monkeypatch test in the [Test plan](#test-plan) (fail
    `_resolve_globalid_strategy`, assert serializer relation decode still resolves from
    recorded state).
- [ ] Slice 4: doc updates + card wrap (per
  [Doc updates](#doc-updates) /
  [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)
  / [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
  **Soft-dep wiring is NOT here — it landed in the pre-Slice-1 gate (Slice 0), since
  Slice 1–3 tests import DRF.** Release-status wording is **split from implementation
  docs**:
  - [ ] **Implemented-on-main docs (land now):** [`docs/TREE.md`][tree] (fill the
    `rest_framework/` / [`tests/rest_framework/`][test-rest-framework] summary lines),
    [`TODAY.md`][today] (note the serializer mutation as an implemented capability),
    [`docs/GLOSSARY.md`][glossary] (update the
    [`SerializerMutation`][glossary-serializermutation] **body** to the implemented
    contract + add it to **Public exports** + the **Index** + the **Mutations**
    browse-by-category row; reconcile the surface keys — `Meta.operation` over
    `model_operations`, the `id:`-decode locate over `lookup_field`; mark status
    **"implemented on main, releasing in 0.0.13"**, **not** `shipped (0.0.13)` yet),
    [`GOAL.md`][goal] (criterion 6's crit-6 example corrected to the shipped surface —
    `SerializerMutation` base + `operation = "create"`).
  - [ ] **Joint-cut docs (deferred to the `0.0.13` release):** flip the GLOSSARY status to
    `shipped (0.0.13)`; [`docs/README.md`][docs-readme] / [`README.md`][readme] move the
    flavor from "Coming next (`0.0.13`)" to "Shipped today" (README **Status** line →
    `0.0.13`); [`CHANGELOG.md`][changelog] release bullets — all at the joint cut, only
    when its maintainer prompt explicitly requests the `CHANGELOG.md` edit.
  - [ ] **Card wrap:** [`KANBAN.md`][kanban] (card → Done via the kanban DB + re-render).

## Problem statement

The package shipped its **write side** in [`DONE-036-0.0.11`][kanban] (the model-driven
[`DjangoMutation`][glossary-djangomutation] base, auto-generated
[`Input` / `PartialInput`][glossary-input-type-generation] types, the shared
[`FieldError` envelope][glossary-fielderror-envelope]) and its **form-validated**
flavor in [`DONE-038-0.0.12`][kanban]
([`DjangoModelFormMutation`][glossary-djangomodelformmutation] /
[`DjangoFormMutation`][glossary-djangoformmutation]). Two of the three write flavors
[`GOAL.md`][goal] success-criterion 6 names — `Input`-driven and `ModelForm` — are
live. The third, `ModelSerializer`, is not.

A large class of the package's target audience already encodes its write validation in
a DRF `ModelSerializer`: it is the canonical "Coming from DRF + django-filter?"
migrant [`README.md`][readme] courts. graphene-django serves them with
[`SerializerMutation`][upstream-serializer-mutation]: the mutation runs
`serializer.is_valid()`, surfaces `serializer.errors` to the client, and
`serializer.save()`s the object — reusing the consumer's existing serializer,
including its `validate_<field>` / `validate()` validation, its `extra_kwargs`, and
its declared (non-model) fields. Without an equivalent in this package, a DRF migrant
must:

- rewrite each serializer's field-level and cross-field validation against the
  model's `full_clean()` (losing the `validate_<field>` / `validate()` logic the
  serializer already carries), and
- re-declare the input shape against the model's editable columns rather than the
  serializer's declared fields (a serializer may declare fields that are *not* model
  columns, or omit / rename / make-read-only columns the write surface must honor).

This is a Required `graphene-django` parity item (the card's own ⚛️ Required tag),
foundational by the [`START.md`][start] "do both libraries provide it?" test:
graphene-django ships `SerializerMutation` as a first-class write surface, and
[`GOAL.md`][goal] names `ModelSerializer` explicitly as a target write flavor. The
work is **small in new machinery** precisely because [`spec-036`][spec-036] froze the
reusable contracts and [`spec-038`][spec-038] already proved the flavor-on-the-base
pattern (and generalized the field factory): the only genuinely new parts are the
serializer-field → input mapping, the `is_valid()` → `serializer.errors` →
`save()` pipeline that replaces the model-construct + `full_clean()` heart, and the
**soft `djangorestframework` dependency** discipline — DRF is not a runtime dependency
and must not become one, yet the suite gates 100% coverage and the card mandates a
live `ModelSerializer` test.

This soft-dep posture is also the **deliberate crit-7 exception**. Crit 7's slogan is
"migrate … without bringing the source package along," and for `graphene-django` /
`strawberry-graphql-django` migrants that holds literally — the GraphQL runtime is
dropped. The DRF migrant is the **one** case that *keeps* its source package:
`djangorestframework` stays because the consumer's `ModelSerializer` is the **reused
validation engine** ([`GOAL.md`][goal]'s `CategorySerializer` carries a "no changes"
annotation), not a GraphQL runtime to shed — "GraphQL becomes another transport for the
same business logic." That is precisely why DRF is a *soft* dependency the package guards
rather than a runtime it replaces, and the framing keeps the crit-7 migration story
coherent rather than looking like a contradiction.

## Current state

A true description of the repo as this spec is authored:

- **The mutation foundation and the form flavor are shipped.** [`mutations/sets.py`][mutations-sets]
  ships [`DjangoMutation`][glossary-djangomutation] with the overridable
  [`_resolve_model(meta)`][spec-036] classmethod and the `_validate_meta` /
  `build_input` / `input_type_name` / `input_module_path` / `resolve_sync` /
  `resolve_async` seams (each model-defaulted), whose docstrings name the `0.0.13`
  serializer flavor as the intended override
  (`_resolve_model`: "the 0.0.13 serializer flavor (`Meta.serializer_class.Meta.model`)
  … supply the model WITHOUT a literal `Meta.model`"). [`forms/sets.py`][forms-sets]
  ships [`DjangoModelFormMutation`][glossary-djangomodelformmutation] as the proof the
  override set works: it subclasses [`DjangoMutation`][glossary-djangomutation],
  overrides exactly those seams, derives its input from the form's fields
  ([`forms/converter.py`][forms-converter] / [`forms/inputs.py`][forms-inputs]), runs
  the form pipeline ([`forms/resolvers.py`][forms-resolvers]), and rides
  `bind_mutations()`. `SerializerMutation` is the same shape with `serializer_class`
  in place of `form_class`.
- **The field factory is already generalized.** [`mutations/fields.py`][mutations-fields]'s
  [`DjangoMutationField`][glossary-djangomutationfield] was generalized by
  [`spec-038`][spec-038] Slice 3 along all three model-hardwired axes — the target
  check (`_has_mutation_protocol` duck-typing, not `issubclass(DjangoMutation)`), the
  `_resolve` dispatch (`mutation_cls.resolve_sync` / `resolve_async`), and the `data:`
  lazy-ref (`mutation_cls.input_type_name` + `input_module_path`) — "for exactly the
  `0.0.13` serializer flavor". This card needs **no** field-factory edit; it verifies
  the generalization holds.
- **No `rest_framework/` module exists.** [`docs/TREE.md`][tree]'s *target* layout
  reserves `django_strawberry_framework/rest_framework/` and
  [`tests/rest_framework/`][test-rest-framework] (both "planned by
  `TODO-ALPHA-039-0.0.13`"); neither is on disk. The package root
  [`__init__.py`][init] exports the `036` / `038` mutation symbols but no
  `SerializerMutation`.
- **`djangorestframework` is not installed and not a dependency.** Neither
  [`pyproject.toml`][pyproject] `[project].dependencies` (Django, strawberry-graphql,
  django-filter, wrapt) nor `[dependency-groups].dev` (faker, pillow, pytest, …)
  carries DRF. `uv run python -c "import rest_framework"` raises `ModuleNotFoundError`.
  This card adds DRF to the **dev group only**
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
- **The version line reads `0.0.12`.** [`spec-038`][spec-038] Slice 5 bumped
  [`__init__.py`][init], [`pyproject.toml`][pyproject], and
  [`tests/base/test_init.py::test_version`][test-base-init] to `0.0.12`; this card
  does **not** move them — the joint `0.0.13` cut shared with [`DONE-040-0.0.13`][kanban]
  owns the bump ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
- **`0.0.13` has two cards.** `039` (this card) and `040` ([Auth mutations][glossary-auth-mutations])
  both target `0.0.13`; there is a joint cut to defer the version bump to. (The
  [`KANBAN.md`][kanban] `## In progress` column is empty as this spec is authored;
  `039` is the lowest-NNN card in the active To-Do / Alpha column and is the
  next-up spec target — recorded in [Risks and open questions][rationale-risks].)
- **The products write surface is live.** [`spec-036`][spec-036] /
  [`spec-038`][spec-038] Slice 4 added a products `Mutation` with model-driven and
  form-driven `DjangoMutationField`s and wired `mutation=Mutation` in
  `config/schema.py`; products has **no** `serializers.py` yet. The `Item` model
  carries the `unique_item_per_category` `UniqueConstraint` — a `ModelSerializer` over
  `Item` surfaces that as a DRF `UniqueTogetherValidator` / `validate()` error, the
  live `"__all__"`-sentinel coverage
  ([Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation)).

## Goals

1. **Ship `SerializerMutation` on the `class Meta` surface.** Declared as a class with
   a nested `Meta` (`serializer_class` + `operation` + optional `fields` / `exclude` /
   `optional_fields`), not a graphene `MutationOptions` /
   `__init_subclass_with_meta__` / `ClientIDMutation` flow
   ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions) /
   [Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused)).
2. **Derive the input from the serializer's declared fields.** A
   `rest_framework/serializer_converter.py` DRF-field → Strawberry-annotation
   registry, reusing the read-side scalar / enum / [`Upload`][glossary-upload-scalar]
   converters where the field types overlap, so the input shape is the serializer's
   contract — including fields a model does not have, and honoring `read_only` /
   `Meta.optional_fields`
   ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
3. **Reuse the shared `FieldError` envelope.** Map `serializer.errors` (and DRF's
   `non_field_errors` bucket) onto the one
   [`FieldError`][glossary-fielderror-envelope] envelope `036` defined — extended
   **additively** here with the default-empty `codes` and `path` members,
   which every write flavor gains together because the envelope and its leaf constructor
   are shared
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)).
4. **Run the write through the serializer.** `serializer.is_valid()` →
   `serializer.save()`, sync and async, inside the one-`transaction.atomic()` boundary
   `036` / `038` set; the payload's object is re-fetched and optimizer-planned for the
   response selection
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
   / [Decision 9](#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path)).
5. **Compose with the shipped permission + visibility seams.** The flavor inherits
   [`DjangoModelPermission`][glossary-djangomodelpermission] write-auth and the
   visibility-scoped `update` locate unchanged
   ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelserializer)).
6. **Keep DRF a soft dependency.** The package imports without DRF; DRF is a dev-group
   dependency so the suite covers `rest_framework/` and hits 100%, and the DRF-absent
   import guard is itself covered by simulated absence
   ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
7. **Ship the products live serializer surface** (folded into Slice 3).
8. **Keep package version state owned by the joint `0.0.13` cut.** No slice edits
   `pyproject.toml`'s `[project].version`, `__version__`, or
   [`tests/base/test_init.py::test_version`][test-base-init] — the card leaves all three at
   `0.0.12` and the joint cut moves them. `uv.lock` **is** updated in the **Slice 0 dependency gate** (regenerated
   for the `[dependency-groups].dev` DRF add, **before** Slice 1 imports DRF in tests,
   not Slice 4), but its `django-strawberry-framework` package `version` entry
   stays `0.0.12` — the lockfile's dependency graph changes, the package version does not
   ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).

## Non-goals

- **Auth mutations.** [Auth mutations][glossary-auth-mutations] (`login` / `logout` /
  `register` + `current_user`, `0.0.13`, [`DONE-040-0.0.13`][kanban]) are
  separately carded; they share the joint cut and reuse the same envelope but ship
  independently ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Changing the `036` model-driven generator or the `038` form generator.** Their
  behavior is reused **unchanged**, and no edit to [`mutations/fields.py`][mutations-fields]
  is needed. [`FieldError`][glossary-fielderror-envelope] is **additive, not frozen**: this
  card extends it with the default-empty `codes` and `path` members, which
  is why [`mutations/inputs.py`][mutations-inputs] is re-opened — the shared envelope and
  its shared leaf constructor are the one home both flatteners use, so all three write
  flavors gain the members together. A member may be added; none may be removed or
  retyped, and a client selecting only `field` / `messages` is unaffected
  ([Decision 2](#decision-2--card-scope-boundary-the-serializer-flavor-ships-auth-stays-out-the-frozen-036-contracts-and-the-038-factory-are-reused-unchanged)).
- **A model-less plain `Serializer` flavor.** `0.0.13` ships the
  `ModelSerializer`-driven contract (a resolvable model, the uniform `node` / `result`
  slot); a plain model-less `serializers.Serializer` is deferred
  ([Risks and open questions][rationale-risks]; the [`DjangoFormMutation`][glossary-djangoformmutation]
  model-less sibling is the fallback shape if demanded).
- **Serializer-derived output types.** The mutation **output** is the primary
  [`DjangoType`][glossary-djangotype] in the frozen `node` / `result` slot — **not** a
  serializer-derived output type (the card's "dual-purposed for inputs and outputs" wording is
  reconciled to the frozen slot, [Risks and open questions][rationale-risks]). Nested writable
  serializers (`ParsedObject`-style nested create / connect) were originally the `036`
  nested-write non-goal; they now ship as the EXPLICIT opt-in `Meta.nested_fields` (the
  serializer owns the nested write, the framework never auto-saves the relation).
- **Serializer `delete`.** DRF serializers do not delete; a `delete` write stays the
  model-driven [`DjangoMutation`][glossary-djangomutation] (`Meta.operation =
  "delete"`) the consumer already has
  ([Decision 10](#decision-10--operations-create--update-no-serializer-delete)).
- **graphene's `Meta.model_operations` runtime dispatch and `Meta.lookup_field`
  non-pk locate.** Not adopted verbatim; the package's per-operation `Meta.operation`
  and `id:`-decode locate supersede them
  ([Decision 10](#decision-10--operations-create--update-no-serializer-delete) /
  [Risks and open questions][rationale-risks]).
- **A new `DjangoType` `Meta` key or settings key**
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it? → foundational" test,
serializer mutations are **Required `graphene-django` parity** (the card's own ⚛️
Required tag; `strawberry-graphql-django` ships no serializer-mutation flavor). The
borrowing splits along the package's standing line — *surface-wise* copy
`graphene-django` / DRF (the `class Meta` + `ModelSerializer` shape every DRF
developer already knows), *behaviorally* keep the Strawberry engine and the package's
own optimizer-composed, permission-scoped, async-capable pipeline. The *capabilities*
of graphene-django's `SerializerMutation` (run the serializer's validation, surface
`serializer.errors`, `serializer.save()` the object) are adopted at the **outcome**
level; the graphene `MutationOptions` / `ClientIDMutation` / `__init_subclass_with_meta__`
mechanism is **explicitly rejected** — it is the decorator-adjacent metaclass-options
surface the package replaces with a nested `class Meta`.

### Reference-package parity checkpoint

[`GOAL.md`][goal] elevates the `django-graphene-filters` `recipes` cookbook as the
working reference and names "Cookbook parity" a success measure — but that cookbook (and
the entire `django-graphene-filters` repo) is **query / filter-only: it has no mutation
surface of any kind**. The cookbook is therefore the parity yardstick for the *read-side*
sidecars (filters / orders / aggregates / fieldsets / search) and is **orthogonal to this
card**. Reference parity for serializer mutations is measured against **graphene-django's
`rest_framework` subpackage** (the rows below) — there is no cookbook mutation port to
match, so "why doesn't the cookbook port show this?" has a one-line answer: it never had
one.

| Upstream | `django-strawberry-framework` | Status |
| --- | --- | --- |
| [`graphene_django.rest_framework.mutation.SerializerMutation`][upstream-serializer-mutation] (`ClientIDMutation`, `SerializerMutationOptions`) | [`SerializerMutation`][glossary-serializermutation] base subclassing [`DjangoMutation`][glossary-djangomutation] + nested `Meta.serializer_class` ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions) / [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)) | this card — borrow the capability, reject the `MutationOptions` surface |
| [`fields_for_serializer` + `convert_serializer_field`][upstream-serializer-converter] (DRF field → GraphQL type, `is_input` flag) | [`rest_framework/serializer_converter.py`][rf-converter] `convert_serializer_field` MRO-walk registry, reusing the read-side [scalar][glossary-scalar-field-conversion] / [choice-enum][glossary-choice-enum-generation] / [`Upload`][glossary-upload-scalar] converters where overlapping ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)) | this card — required parity, fail-loud (no `Field → String` catch-all) |
| graphene `convert_serializer_field` `serializers.Field → String` catch-all | a **raising** fallthrough — an unmapped field raises [`ConfigurationError`][glossary-configurationerror] ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)) | deliberate divergence — matches [`forms/converter.py`][forms-converter]'s fail-loud discipline |
| [`ErrorType.from_errors(serializer.errors)`][upstream-serializer-mutation] on the payload | `serializer.errors` → the shared [`FieldError` envelope][glossary-fielderror-envelope], `non_field_errors` → the `"__all__"` sentinel ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)) | this card — the one `036` envelope, additively carrying `codes` / `path` |
| graphene `SerializerMutation` output fields built from the serializer (`is_input=False`) | the primary [`DjangoType`][glossary-djangotype] in the uniform `node` / `result` slot — **not** a serializer-derived output type ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)) | deliberate non-adoption (card-body "dual-purpose" tension, [Risks and open questions][rationale-risks]) |
| graphene `Meta.model_operations = ["create", "update"]` (runtime-dispatched per mutation) | per-operation `Meta.operation ∈ {"create", "update"}` (one mutation per op, the package convention) ([Decision 10](#decision-10--operations-create--update-no-serializer-delete)) | deliberate non-adoption (card-body tension, [Risks and open questions][rationale-risks]) |
| graphene `Meta.lookup_field` (non-pk update locate) + `get_object_or_404` | the `id:` `GlobalID` server-side decode → target `get_queryset` locate ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)) | deliberate non-adoption (card-body tension, [Risks and open questions][rationale-risks]) |
| graphene `Meta.optional_fields` (force specific fields optional) | `Meta.optional_fields` adopted as a force-optional override on the serializer-derived input ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)) | this card — adopted (clean semantics) |
| graphene relation visibility (none — serializer's own queryset only) | every relation id (Relay + raw pk) visibility-checked through the related primary `get_queryset` before the serializer ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)) | package security invariant beyond graphene parity (mirrors the per-branch visibility check `036`'s model path and `038`'s form path already enforce, raw pk included) |
| graphene [`get_serializer_kwargs(cls, root, info, **input)`][upstream-serializer-mutation] (classmethod constructor-kwarg seam) | a **constructor-only** `get_serializer_kwargs(self, info, *, data, hook_context)` hook for NON-RESERVED kwargs; the framework owns `data` / `instance` / `partial` / `context["request"]` / `context["write_alias"]` ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)) | this card — **name-borrowed** seam, not signature-compatible (the graphene signature differs, and the reserved kwargs are framework-owned here; an existing graphene override can't carry over verbatim — a crit-7 "Meta mental model carries over" wrinkle, not a drop-in) |
| graphene optional `rest_framework` dependency | DRF a **soft runtime dependency** (out of `[project].dependencies`, in the dev group, guarded import) ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)) | this card — required parity |
| graphene `MutationOptions` / `ClientIDMutation` / `__init_subclass_with_meta__` / `clientMutationId` | rejected for a nested `class Meta` base ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions)) | deliberately not borrowed |

### From `graphene-django` / DRF — borrow the user-facing shape

- **`Serializer` / `ModelSerializer` consumption.** The mutation runs the consumer's
  existing serializer — `serializer_class(data=…, context={"request": …})` (create) /
  `serializer_class(instance=<row>, data=…, partial=True, context=…)` (update),
  `serializer.is_valid()`, `serializer.save()`. The serializer's `validate_<field>` /
  `validate()` validation, `extra_kwargs`, and declared (non-model) fields are honored
  for free.
- **`serializer.errors` → field-keyed envelope.** graphene-django's
  `ErrorType.from_errors(serializer.errors)` is the parity shape; here it maps onto the
  one shared [`FieldError`][glossary-fielderror-envelope] `036` defined.

### From `strawberry-graphql-django` — borrow the runtime composition

- **Optimizer-composed return + permission scoping.** The payload's object rides the
  same `036` optimizer re-fetch + visibility-scoped `update` locate the model-driven
  and form mutations use — Strawberry-native, async-capable. (strawberry-django ships
  no serializer flavor, so there is no surface to borrow — only the runtime posture.)

### Explicitly do not borrow

- **graphene's `MutationOptions` / `__init_subclass_with_meta__` / `ClientIDMutation`
  / `clientMutationId`.** Rejected: the metaclass-options + relay-mutation surface the
  package's nested `class Meta` replaces
  ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions)).
- **The `serializers.Field → String` converter catch-all.** Rejected for a fail-loud
  raising fallthrough ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- **A second `errors` envelope shape.** Rejected: the card mandates one shared
  envelope across flavors; the `036` [`FieldError`][glossary-fielderror-envelope] is
  reused rather than forked (extended additively, never duplicated).

## User-facing API

One new base class, no new field factory, no new `DjangoType` `Meta` key. A consumer
wraps a `ModelSerializer` they already have:

```python
import strawberry
from rest_framework import serializers

from django_strawberry_framework import (
    DjangoMutationField,
    SerializerMutation,
)

from . import models


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Item
        fields = ("name", "description", "category", "is_private")

    def validate_name(self, value):
        if value.lower() == "forbidden":
            raise serializers.ValidationError("That name is reserved.")
        return value


class CreateItemViaSerializer(SerializerMutation):
    class Meta:
        serializer_class = ItemSerializer        # model resolves via serializer_class.Meta.model
        operation = "create"


class UpdateItemViaSerializer(SerializerMutation):
    class Meta:
        serializer_class = ItemSerializer
        operation = "update"


@strawberry.type
class Mutation:
    # Exposed through the shipped (038-generalized) DjangoMutationField — no
    # class-attribute annotation; the <Name>Payload is materialized at finalization.
    create_item_via_serializer = DjangoMutationField(CreateItemViaSerializer)
    update_item_via_serializer = DjangoMutationField(UpdateItemViaSerializer)
```

generates:

```graphql
type Mutation {
  createItemViaSerializer(data: ItemSerializerInput!): CreateItemViaSerializerPayload!
  updateItemViaSerializer(id: ID!, data: ItemSerializerPartialInput!): UpdateItemViaSerializerPayload!
}

input ItemSerializerInput {
  name: String!
  description: String
  categoryId: GlobalID!
  isPrivate: Boolean
}

type CreateItemViaSerializerPayload {
  node: ItemType
  errors: [FieldError!]!
}
```

The input fields are the **serializer's** declared fields (`ItemSerializer.Meta.fields`,
with `read_only` fields dropped and `Meta.optional_fields` forced optional), not the
model's editable columns — `description` is optional because the serializer field
`required` is `False` (graphene-django parity). The relation input keeps the
cross-flavor `categoryId` GraphQL name, but the resolver decodes it to the **serializer
field** `category` (`{"category": pk}`) so the bound `ModelSerializer` validates it
through its `PrimaryKeyRelatedField` natively — not via a raw model `setattr`
([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)
reverse map). On success the payload's `node` is the saved object re-fetched and
optimizer-planned for the response selection; on a `serializer.is_valid()` failure
`node` is `null` and `errors` carries one [`FieldError`][glossary-fielderror-envelope]
per offending field, with DRF's `non_field_errors` (cross-field `validate()`,
`UniqueTogetherValidator`) bucket keyed to the `"__all__"` sentinel.

**`update` is a true partial update via DRF `partial=True`.** `updateItemViaSerializer`
takes `ItemSerializerPartialInput` (all-optional); the resolver locates the row through
`ItemType.get_queryset(...)` (a row the caller cannot see is a not-found `FieldError`
on `id`, never an existence leak), then constructs
`ItemSerializer(instance=<row>, data=provided, partial=True, context={"request": …})`.
DRF's `partial=True` is the native partial-update mechanism — no full-payload
reconstruction (the `038` form flavor needed reconstruction because a bound Django form
re-validates the whole field set; a DRF serializer with `partial=True` validates only
the provided fields). So changing only `name` preserves `category` / `description` /
`isPrivate`, while a `UniqueTogetherValidator` still validates against the unchanged
`category` (DRF backfills the unchanged member from `serializer.instance` on a partial
update — a DRF behavior pinned to the verified floor, [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)). Write authorization is the inherited
[`DjangoModelPermission`][glossary-djangomodelpermission] default (the `add` /
`change` model perm).

### Error shapes

- A `Meta` with no `serializer_class`; a `serializer_class` that is not a
  `serializers.Serializer` subclass, or (for the `ModelSerializer`-driven contract) is
  a non-`ModelSerializer` / a `ModelSerializer` whose `Meta.model` is unresolvable; a
  bare-string / duplicate-name / unknown-name `Meta.fields` / `Meta.exclude` /
  `Meta.optional_fields` (validated against the serializer's field set); a
  `Meta.operation = "delete"`; or an empty effective field set — each raises
  [`ConfigurationError`][glossary-configurationerror] at mutation-class creation /
  finalization, naming the offending key.
- A `serializer.is_valid()` failure populates the
  [`FieldError` envelope][glossary-fielderror-envelope] (a null-object payload),
  **not** a top-level `GraphQLError`. A serializer field error keys to the serializer
  field name; a `validate()` / `non_field_errors` error keys to the `"__all__"`
  sentinel. A `ValidationError` raised at **`serializer.save()`** time (a custom
  `create()` / `update()`, or a model-level `full_clean()`) maps the **same** way —
  its `.detail` runs through the same recursive flattener into the envelope, never a
  top-level error ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
  step 6).
- A write the caller is not authorized to perform
  ([`DjangoModelPermission`][glossary-djangomodelpermission] / `check_permission`
  denial) raises a top-level `GraphQLError`, **not** a `FieldError` entry — the same
  split [`spec-036`][spec-036] Decision 15 set.
- A relation id for a row the caller cannot see (a hidden `Category` `GlobalID` /
  raw pk) is a field-keyed `FieldError`, never a serializer
  `does_not_exist` / existence leak.
- A sync serializer mutation whose target type has an `async def`
  [`get_queryset`][glossary-get_queryset-visibility-hook] raises
  [`SyncMisuseError`][glossary-syncmisuseerror] (coroutine closed first), the standing
  discipline.
- Importing [`SerializerMutation`][glossary-serializermutation] without
  `djangorestframework` installed raises `ImportError` with an install hint
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec stem is the structured `spec-039-serializer_mutations-0_0_13` the
[`docs/SPECS/NEXT.md`][next] Step 6 convention pins: the card's `039`, the
`serializer_mutations` topic slug, and the `0_0_13` target patch. A spec is authored at the
`docs/` top level and a later card's Step 8 archive sweep moves it, so this document lives
at **`docs/SPECS/spec-039-serializer_mutations-0_0_13.md`**, with its
`-terms.csv` and `-rationale.md` companions under **`docs/SPECS/appx/`**.

Rationale companion — this Decision's justification and its two rejected alternatives:
[Decision 1][rationale-d1].

### Decision 2 — Card-scope boundary: the serializer flavor ships; auth stays out; the frozen `036` contracts and the `038` factory are reused unchanged

This card ships the **serializer-validated** write flavor end-to-end: the
[`SerializerMutation`][glossary-serializermutation] base, the serializer-field → input
mapping, the `is_valid()` → `serializer.errors` → `save()` pipeline, and the products
live serializer surface. It explicitly does **not** ship the adjacent flavor, owned by
the sibling joint-cut card:

- **Auth mutations** ([Auth mutations][glossary-auth-mutations]) —
  [`DONE-040-0.0.13`][kanban].

And it **reuses the contracts [`spec-036`][spec-036] defined for exactly this and
[`spec-038`][spec-038] proved reusable**: the
[`FieldError` envelope][glossary-fielderror-envelope] (additively extended, above), the
`<Name>Payload` wrapper
(uniform `node` / `result` slot), the [`DjangoMutationField`][glossary-djangomutationfield]
factory (already generalized by `038` — **no edit needed**), the
[`DjangoModelPermission`][glossary-djangomodelpermission] / `Meta.permission_classes`
/ `check_permission` write-auth seam, and the [`_resolve_model`][spec-036] /
`_validate_meta` / `build_input` / `input_type_name` / `input_module_path` /
`resolve_*` seam set. The serializer input generator is a separate module, so neither the
`036` nor the `038` generator is re-opened. [`FieldError`][glossary-fielderror-envelope] is
the one deliberate exception, and it is **additive**: this card adds the default-empty
`codes` and `path` members to the shared envelope in
[`mutations/inputs.py`][mutations-inputs], so every write flavor gains them at once and a
client selecting only `field` / `messages` sees no change. Additive means a member may be
added; none may be removed or retyped.

Rationale companion — this Decision's justification and its two rejected alternatives:
[Decision 2][rationale-d2].

### Decision 3 — `class Meta` surface, not graphene's `MutationOptions`

A serializer mutation is a **base class with a nested `class Meta`**
(`serializer_class` + `operation` + optional `fields` / `exclude` / `optional_fields`),
declared exactly like every other consumer surface in the package
([`DjangoType`][glossary-djangotype] / [`FilterSet`][glossary-filterset] /
[`OrderSet`][glossary-orderset], and the [`DjangoMutation`][glossary-djangomutation] /
[`DjangoModelFormMutation`][glossary-djangomodelformmutation] write bases). It is **not**
graphene's `SerializerMutationOptions` / `__init_subclass_with_meta__(serializer_class=…,
model_class=…, lookup_field=…)` keyword-options flow, and **not** a `ClientIDMutation`
lineage.

Rationale companion — this Decision's justification and its two rejected alternatives:
[Decision 3][rationale-d3].

### Decision 4 — Module and test locations: `rest_framework/` subpackage mirroring `forms/`

- **Source:** `django_strawberry_framework/rest_framework/` — the subpackage
  [`docs/TREE.md`][tree]'s target layout reserves, split in the spirit of the
  [`forms/`][forms-sets] subpackage (its structural twin): `serializer_converter.py`
  (the DRF-field → annotation registry, the card DoD's named module), `inputs.py`
  (the serializer-derived input + the namespace materialization), `sets.py`
  (`SerializerMutation` + `Meta` validation + the seam overrides), `resolvers.py`
  (the serializer pipeline), `__init__.py` (the `require_drf()` guard,
  [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)),
  and [`hook_context.py`][rf-hook-context] (the frozen `SerializerHookContext` /
  `UploadMetadata` surface every consumer hook receives). It reuses [`mutations/`][mutations-fields]'s
  [`DjangoMutationField`][glossary-djangomutationfield] and
  [`FieldError`][glossary-fielderror-envelope] rather than re-declaring them.
- **Tests:** new [`tests/rest_framework/`][test-rest-framework] mirroring the source
  modules (`test_converter.py` / `test_inputs.py` / `test_sets.py` / `test_resolvers.py`);
  live coverage extends [`test_products_api.py`][test-products-api].

Rationale companion — this Decision's justification and its three rejected alternatives:
[Decision 4][rationale-d4].

**Shared-helper homes (the DRY promotions land outside `rest_framework/`).** The
[Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations) section
single-sites the helpers the form flavor already forked from the model flavor, so the
serializer flavor imports rather than re-implements: the **fail-loud converter dispatch
skeleton** lands in a new `utils/converters.py`; the **relation-decode core**
(`visible_related_object`, with its batched sibling `visible_related_objects`)
lives in [`utils/querysets.py`][utils-querysets] beside the shared decode primitives in
`utils/write_values.py`; the **shape-build cache**, the **build/stash core**,
and the **`reject_unknown_meta_keys`** typo-guard land in
[`mutations/sets.py`][mutations-sets]; the **non-delete ops constant** and its
single-sited reject message land in a net-new `mutations/operations.py`
(`NON_DELETE_WRITE_OPERATIONS` / `NON_DELETE_OPERATION_INPUT_KIND` /
`non_delete_operation_error`), reached from both flavors through
`mutations/sets.py::require_non_delete_operation`; the **sync write-pipeline skeleton**
lives in [`mutations/resolvers.py`][mutations-resolvers]; the unified
**input-namespace trio / field-spec** and the shared conversion base
`FieldConversionBase` in [`utils/inputs.py`][utils-inputs]; the shared **leaf-error
constructors** in `utils/errors.py`; and the **`register_subsystem_clear`** seam
spans [`types/finalizer.py`][types-finalizer] + [`registry.py`][registry]. These promotions
edit `mutations/` / `utils/` (and `forms/` re-points to the shared site), so the
"near-zero edit to `mutations/`" estimate elsewhere is the *no-DRY-promotion* floor; the
promotions are the cheap-now single-siting this card chooses to pay.

### Decision 5 — Public surface: `SerializerMutation` exported from the root, the `038`-generalized factory reused

The flavor's public surface is **seven names, every one a lazy export via the root
`__getattr__`** under the shared `require_drf()` guard, and — while DRF is a soft
dependency — every one **deliberately NOT added to `__all__`** (so `from … import *`
stays DRF-free for consumers who never write a serializer mutation; the named
`from django_strawberry_framework import SerializerMutation` still resolves through
`__getattr__`, [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
[`__init__.py`][init]'s `_DRF_SOFT_EXPORTS` map is the single enumeration:

- `SerializerMutation` — the `ModelSerializer` mutation base.
- `register_serializer_field_converter` and `SerializerFieldConversion` — the public
  converter registry and its conversion result.
- `describe_serializer_input` — the schema-shape debug helper.
- `NestedSerializerConfig` — the opt-in nested-input declaration.
- `SerializerHookContext` and `UploadMetadata` — the frozen hook surface every consumer
  hook receives ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
  step 4).

`SerializerMutation` is the only one of the seven a consumer must name to declare a
mutation; the other six are the surfaces those improvements and the hook contract expose.

No net-new field factory or error type: the flavor is exposed through the **existing**
[`DjangoMutationField`][glossary-djangomutationfield] and returns the one shared
[`FieldError`][glossary-fielderror-envelope] envelope (additively extended, above). Critically — unlike
[`spec-038`][spec-038], which had to **generalize** the factory along its three
model-hardwired axes — this card needs **no** factory edit, because `038` already did
that generalization "for exactly the `0.0.13` serializer flavor":

1. **Target check.** [`mutations/fields.py`][mutations-fields]'s
   `_validate_mutation_target` already accepts any member of the mutation family via
   the duck-typed `_has_mutation_protocol` (`_mutation_meta` attribute + callable
   `resolve_sync` / `resolve_async` + callable `input_type_name` + an
   `input_module_path`), not `issubclass(DjangoMutation)`. `SerializerMutation`, a
   `DjangoMutation` subclass, passes trivially.
2. **Resolver dispatch.** `DjangoMutationField._resolve` already calls
   `mutation_cls.resolve_sync` / `resolve_async`, so a serializer flavor routes to
   [`rest_framework/resolvers.py`][rf-resolvers] through its
   `resolve_sync` / `resolve_async` overrides.
3. **The `data:` input-ref.** `_synthesized_mutation_signature` already consults
   `mutation_cls.input_type_name(meta)` + `mutation_cls.input_module_path`, so the
   serializer-derived input (in the `rest_framework` input namespace under a
   serializer-derived name, e.g. `ItemSerializerInput`) resolves through the overrides.

The work this card owes the factory is a **verification test**, not an edit
([`tests/mutations/test_fields.py`][test-mutations] extends to prove the generalization
holds for `SerializerMutation`). This is the dividend the `038` forward-intent bought.

Rationale companion — this Decision's justification and its two rejected alternatives:
[Decision 5][rationale-d5].

### Decision 6 — Base-class strategy: `SerializerMutation` rides the `DjangoMutation` base, `ModelSerializer`-driven

[`SerializerMutation`][glossary-serializermutation] **subclasses**
[`DjangoMutation`][glossary-djangomutation] — exactly as
[`DjangoModelFormMutation`][glossary-djangomodelformmutation] does — overriding
[`_resolve_model`][spec-036] to return `Meta.serializer_class.Meta.model`, and so
reuses the base value: the primary [`DjangoType`][glossary-djangotype] payload in the
uniform `node` / `result` slot, the [`DjangoModelPermission`][glossary-djangomodelpermission]
default (authorized for free through the model override), the visibility-scoped
`update` locate, and the optimizer re-fetch (the G2 gate keeps `select_related` /
`prefetch_related` but suppresses `.only(...)`). Its input is serializer-derived rather
than model-column derived, and `Meta.operation` is restricted to `"create"` /
`"update"` (no serializer `delete`,
[Decision 10](#decision-10--operations-create--update-no-serializer-delete)).

Because it is a `DjangoMutation` subclass it registers in the existing mutation
declaration registry and **rides the existing `bind_mutations()`** at
[`finalize_django_types`][glossary-finalize_django_types] phase 2.5 — the same way
[`DjangoModelFormMutation`][glossary-djangomodelformmutation] does (no new
`bind_serializer_mutations()` entry point, the dividend of the
`ModelSerializer`-rides-`DjangoMutation` choice); its `build_input` override
materializes the input into a `rest_framework` input namespace. The flavor adds **no**
`DjangoType` `Meta` key, so [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS`
are untouched.

The contract is **`ModelSerializer`-driven**: `Meta.serializer_class` must be a DRF
`serializers.ModelSerializer` with a resolvable `Meta.model`. A plain model-less
`serializers.Serializer` is **out of scope for `0.0.13`** — `DjangoMutation`'s base
`_validate_meta` requires a resolvable model (it raises when `_resolve_model` returns
`None`), and a model-less serializer has no object slot to return; the
[`DjangoFormMutation`][glossary-djangoformmutation] model-less sibling
(`{ ok, errors }`, its own metaclass + bind) is the fallback shape if a plain
`Serializer` flavor is demanded ([Risks and open questions][rationale-risks]).

Rationale companion — this Decision's justification and its three rejected alternatives:
[Decision 6][rationale-d6].

**Cross-flavor reuse ([DRY obligations](#cross-flavor-reuse-and-dry-obligations)).**
Because this base is "the **exact** override set `DjangoModelFormMutation` uses," its
`_validate_meta` and `build_input` overrides are on track to be a third byte-parallel
copy of the form cluster. The spec instead requires the serializer to ride shared sites:
`_validate_meta` reuses `mutations/sets.py::_validate_permission_classes`, the shared
field-sequence normalize, the shared non-delete ops set, and returns a
`_ValidatedMutationMeta`; the `declared - allowed` typo-guard is the promoted
`reject_unknown_meta_keys(name, meta, allowed)` called with the serializer's own
`_ALLOWED_SERIALIZER_META_KEYS`, and the field-sequence call is
`normalize_field_name_sequence(..., flavor="SerializerMutation")` **directly** — the one
entry point all three flavors call, with no per-flavor re-binding wrapper; the
build/stash/name seam rides the promoted `build_and_stash_input` core rather than spelling
`_build_and_stash_serializer_input`, but its descriptor-keyed per-shape dedupe —
the `SerializerInputShape` is only knowable AFTER the build — is an inline lookup-or-store,
NOT `cached_build_input` (whose pre-build key lookup would force building the shape twice);
and the
input-namespace clear **registers through the mandatory `register_subsystem_clear` seam**
(not a budget-dependent fallback) — a zero-argument callable plus a stable `owner`
string, registered `before_bind=True` from the module that owns the ledger — instead of
being hand-added to both the finalizer pre-bind reset and `registry.clear()`. Because only
an imported owner can register, that **collapses the import-guarded-clear asymmetry** the
Slice-2 checklist would otherwise spell out by hand.

The serializer's genuinely-new `_validate_meta` logic is the `serializer_class`
is-a-`ModelSerializer` (+ resolvable `Meta.model`) check, `optional_fields` normalization,
`Meta.injected_fields` (normalize, then guard against the writable basis and against a name
still present in the generated input), `Meta.select_for_update` through the shared
`validate_select_for_update`, `Meta.nested_fields` including the
`create()` / `update()`-override requirement, validation of the
`get_serializer_for_schema()` field map, capture of the schema fingerprint, and
the recursive writable-`source` ownership walk.

### Decision 7 — Serializer-field → Strawberry input mapping: the serializer is the input source of truth

[`rest_framework/serializer_converter.py`][rf-converter] maps each DRF serializer
field to its Strawberry input annotation + required-ness, and
[`rest_framework/inputs.py`][rf-inputs] builds two `@strawberry.input` classes from the
serializer's **schema-time field set** — the graphene-django
`fields_for_serializer(is_input=True)` parity shape.

**Field discovery goes through an overridable schema-time hook, not a bare
`serializer_class()`.** The input is generated at finalization — *before any request
exists* — so the default `get_serializer_for_schema()` classmethod instantiates the
serializer with **no arguments** (`serializer_class()`) and materializes its **`.fields`**.
**The loud-rejection guard wraps the `.fields` materialization, not the constructor
call** — because DRF builds `.fields` **lazily**: `serializer_class()` with no args does
**not** raise, and a context-requiring serializer (a custom `get_fields()` that reads
`self.context`, or a field whose binding needs request / tenant state) fails only at
**first `.fields` access**, not at construction. Guarding `serializer_class()` alone
would never trigger for the serializers it is meant to catch; the guard must surround the
`.fields` read (and the per-field spec extraction it drives). Many valid DRF serializers
cannot have their schema-time `.fields` materialized no-arg for this reason. For those,
`get_serializer_for_schema()` is the **explicit contract** — a consumer overrides it to
return a serializer instance (or field map) whose field **shape is stable and
request-independent** (it is called once, at bind time, with no request). A serializer
whose field set genuinely varies per request has **no single GraphQL input shape** and is
**rejected loudly** (a [`ConfigurationError`][glossary-configurationerror] if
**materializing `.fields` raises** and the hook is not overridden) — the schema cannot
encode a request-dependent input. This
is the deliberate split the `038` form flavor relies on (class-level form metadata,
never a request-shaped object at schema time); the **runtime**
`get_serializer_kwargs(...)` hook
([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload))
is a **distinct** seam — it shapes the *runtime* serializer (`data` / `instance` /
`context`) and cannot substitute for schema-time discovery, because finalization
precedes the first request.

**The converter is fail-loud (the [`forms/converter.py`][forms-converter] discipline,
diverging from graphene).** Dispatch is a `type(field).__mro__` walk over an
individually-registered registry with a **raising fallthrough** — **not**
`functools.singledispatch` with the graphene-django `serializers.Field → String`
catch-all (which would shadow the raise so every custom serializer field silently
became `String`, losing the `ImproperlyConfigured` parity). An ordered `isinstance`
precheck table runs first, then the scalar registry MRO walk, then a raising default. The
precheck order is itself contract: `(BaseSerializer, ListSerializer)` → `ManyRelatedField`
→ `RelatedField` → `FileField` → `ListField` → `MultipleChoiceField`. Two consequences a
DRF migrant must know. **The nested-serializer reject runs first**, so a nested serializer
over a reverse-relation column is named as a nested field rather than misrouted as a
relation-id or list input. And **the single-relation precheck matches the broad
`serializers.RelatedField`, then rejects any non-`PrimaryKeyRelatedField`**: a
`SlugRelatedField`, a `HyperlinkedRelatedField`, or a custom writable `RelatedField` is a
[`ConfigurationError`][glossary-configurationerror] naming the field, because the package
types every relation input as an id that decodes to a primary key. Matching the narrow
`PrimaryKeyRelatedField` instead would drop those fields through to the scalar walk and
give them a wire shape the decoder cannot honor. **This fail-loud posture — and the explicit relation / file rows in particular —
is mandated by [`GOAL.md`][goal]'s non-goal**, not merely the package's house style:
[`GOAL.md`][goal] forbids "a system that silently weakens rich relations into generic
placeholders," yet graphene-django's own `convert_serializer_field` has **no** relation
registration, so related fields fall through its `serializers.Field → String` catch-all
and degrade to bare strings. Typing `PrimaryKeyRelatedField` / `ManyRelatedField` to a
target id (and raising on the unmapped) makes the package **strictly more faithful to
GOAL than the upstream it borrows from** — the divergence is required, not optional. The
mapping (graphene's `convert_serializer_field` table is the scalar-row reference, but
graphene degrades relation / file fields to `String` via its base-`Field` catch-all —
the relation / file rows below are package extensions graphene lacks, not parity):

- `CharField` (and `EmailField` / `SlugField` / `URLField` / `RegexField` / `IPAddressField`
  via MRO) → `str`. A serializer-only `ChoiceField` → a **GENERATED enum** at the build site:
  the converter's *base* mapping is `str`, upgraded to the enum by
  `resolve_serializer_field` where `type_name` is known (the same finalize-at-the-build-site
  pattern relations / files use). Over a `ModelSerializer` `choices` column an auto-generated
  field reuses the read-side column [enum][glossary-choice-enum-generation]; a
  CONSUMER-DECLARED `ChoiceField` — even `source`-mapped to a plain (non-choice) column —
  emits the serializer-only enum too (declared choices are a schema-affecting
  override, never collapsed back to `String`). `FilePathField` stays `str` (dynamic filesystem
  choices, not a stable enum).
- `IntegerField` → `int`, `FloatField` → `float`, `DecimalField` → `Decimal`,
  `BooleanField` → `bool`, `UUIDField` → `uuid.UUID`.
- `DateField` / `DateTimeField` / `TimeField` → Python-native; `DurationField` → `str` (a
  deliberate wire scalar).
- `DictField` / `HStoreField` → `strawberry.scalars.JSON`; `ModelField` → its wrapped Django
  column's scalar.
- `JSONField` → `strawberry.scalars.JSON`; `ListField` → `list[<scalar child>]` — the
  `child` is converted **recursively through the same scalar registry**
  (`ListField(child=IntegerField())` → `list[int]`); a `ListField` whose `child` is a
  **relation field or a (nested) serializer** is **out of scope** →
  [`ConfigurationError`][glossary-configurationerror] naming the field (a relation list is
  expressed via `ManyRelatedField` / `PrimaryKeyRelatedField(many=True)`, and a nested
  serializer is the `036` nested-write non-goal — a `ListField` must not become a
  back-door to either). A serializer-only `MultipleChoiceField` → `list[<generated enum>]`
  (base `list[str]`, upgraded at the build site like `ChoiceField`).
- `PrimaryKeyRelatedField` → the target's id (`relation_single`), `many=True` /
  `ManyRelatedField` → `list[<id>]` (`relation_multi`); the generated field carries
  **exactly one** id annotation, **strategy-dependent on the target** — the target primary
  [`DjangoType`][glossary-djangotype]'s `GlobalID` when it is Relay-Node-shaped, else the
  target's **raw-pk scalar** — decided at the build site (a live request can only submit
  the one shape that annotation admits; "accepts both `GlobalID` and raw pk" is the shared
  decode *helper*'s contract, not a single generated field's,
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
  step 3).
- `FileField` / `ImageField` → [`Upload`][glossary-upload-scalar] (`file`).
- A nested `ModelSerializer` / `ListSerializer` field → **fail-loud by default**, surfaced
  as a `ConfigurationError` — UNLESS the mutation EXPLICITLY opts it in via
  `Meta.nested_fields = {"<field>": NestedSerializerConfig(...)}`, which builds the
  nested input recursively and hands the decoded nested data to the serializer's own
  `create()` / `update()` (the framework never auto-saves the relation). Nesting is opt-in only:
  an un-named nested field still fails loud.

**Where a serializer field overlaps a model column, reuse the read-side converters.**
A `ModelSerializer` field backed by a `choices` column resolves to the SAME generated
enum the read [`DjangoType`][glossary-djangotype] synthesizes (the symmetric wire
contract), via the read-side [scalar][glossary-scalar-field-conversion] /
[choice-enum][glossary-choice-enum-generation] registry keyed on the **backing**
`models.Field` — resolved from the serializer field's `source` (**Renamed fields**
below), not its declared name — exactly the [`forms/inputs.py`][forms-inputs]
discipline. The two key spaces (`serializers.Field` in the converter, `models.Field` on
the read side) stay strictly separate.

**The generated input must describe the same shape the runtime serializer validates, so a
model-backed relation's cardinality must agree with its backing column.** A serializer
relation field whose `many=` shape contradicts the column it is mapped over — a
`PrimaryKeyRelatedField(many=True, source="category")` across a forward FK, or a single
`PrimaryKeyRelatedField` across a reverse one-to-one that cannot hold a list — is a
[`ConfigurationError`][glossary-configurationerror]
([`rest_framework/serializer_converter.py`][rf-converter]`::_reject_relation_cardinality_mismatch`). Where the two agree,
the emitted `kind` is re-derived from the **serializer** field's cardinality rather than
from the column classifier alone, so a `many=True` field over a reverse FK or a
`GenericRelation` emits a list-of-ids input, which is what DRF will validate.

**Renamed fields (`source`) — supported for the simple cases, fail-loud otherwise.** A
DRF serializer field's GraphQL-facing identity is its **declared field name**, but the
model attribute it reads / writes is its `source` (default: the field name). A consumer
can declare `category_pk = PrimaryKeyRelatedField(source="category", queryset=…)` or
`full_name = CharField(source="name")`, and the card's problem statement explicitly
courts serializers that rename fields. The supported `source` scope for `0.0.13`:

- **Omitted `source`** (the common case, `source == field_name`) and a **simple
  one-segment `source`** (`source="category"`) are supported. The **GraphQL input name
  is derived from the declared serializer field name** by the cross-flavor rule, with an
  **id-like-suffix normalization** so the relation convention does not double-suffix:
  the relation `Id` suffix is appended **only when the declared field name is not
  already id-like** (`*_id` / `*_pk`); an already-id-like name is just
  camel-cased. So a relation field `category` → `categoryId` (suffix appended, the
  package convention that surfaces FK `category` as `categoryId`), `category_id` →
  `categoryId` (already id-like — camel-cased, **no** doubled `…IdId`), and
  `category_pk` → `categoryPk` (already id-like — camel-cased, **no** `…PkId`). This
  matters because DRF migrants routinely name write-only related-id fields `<name>_id`
  already; appending `Id` regardless would emit `categoryIdId`. (A non-relation scalar
  field is camel-cased with no suffix: `full_name` → `fullName`.) The **backing Django
  model field** (for the enum / relation-target resolution above) is looked up by
  **`source`**, not the field name. The reverse map **preserves the declared serializer
  field name** as the `provided_data` key — DRF's `to_internal_value` reads by the
  declared key and maps it to `source` internally, so the resolver must **not**
  pre-apply `source`.
- A **dotted `source`** (`source="user.email"`) or **`source="*"`** is **rejected** for
  any field that resolves its target from a model column (a `ModelSerializer` FK-backed
  relation, or a `choices`-enum overlap): a [`ConfigurationError`][glossary-configurationerror]
  naming the field, since the backing column is not a single resolvable `models.Field`. A
  plain scalar serializer-only field (no model-column conversion) is unaffected — it is a
  scalar input validated by the serializer, keyed by its declared name.

**Serializer-only relation fields — supported via `field.queryset.model`.** A real
DRF pattern sits between "serializer-only fields are scalar inputs" and "relation targets
resolve through `source`": a **write-only `PrimaryKeyRelatedField` (or `many=True`) whose
`queryset` is not a model column** and is consumed by a custom `create()` / `update()`.
That field is *both* serializer-only *and* a relation, so the relation **target model is
resolved from the DRF field's `queryset.model`** (not from a backing FK via `source`), and
that target drives the id annotation (Relay `GlobalID` vs raw-pk scalar, the same
strategy-dependent rule) and the decode-time visibility check through the target's primary
`DjangoType.get_queryset`. The **declared serializer field name is preserved** in
`provided_data` (DRF hands it to the custom `create()` / `update()`). So a relation field
resolves its target from **either** the backing FK (a `ModelSerializer` mapped relation,
via one-segment `source`) **or** `field.queryset.model` (a serializer-only relation); a
relation field with **neither** a resolvable backing column **nor** a concrete
`queryset.model` (e.g. a dotted / `source="*"` relation with no queryset, or a relation
field with `queryset=None` outside a `ModelSerializer` mapping) is a
[`ConfigurationError`][glossary-configurationerror] naming the field — there is no target
to type or visibility-check. (`PrimaryKeyRelatedField.queryset.model` is a standard DRF
attribute; assert it against the installed DRF when Slice 1 lands, the
`ManyRelatedField.child_relation` precedent — verified against the pinned DRF floor.)

**A relation target with no registered primary `DjangoType` is a build-time
`ConfigurationError`.** Whether the target model comes from the backing FK (via
`source`) or from `field.queryset.model`, the package's relation-decode promise is
**visibility-scoped**: every related id is resolved through the target's primary
[`DjangoType`][glossary-djangotype]'s [`get_queryset`][glossary-get_queryset-visibility-hook].
A target model with **no registered primary `DjangoType`** cannot honor that promise — so a
serializer relation field whose target lacks one is a **class-creation**
[`ConfigurationError`][glossary-configurationerror] **naming the serializer field and the
target model**, not a silent runtime fallback to `Model._default_manager` (which would write
a hidden / unseeable row, overstating the visibility guarantee). This is **stricter than the
promoted [`utils/querysets.py`][utils-querysets]`::visible_related_object`
helper**, which keeps a no-primary-type **default-manager fallback** for the form flavor's
existing behavior: the serializer flavor opts into the stricter contract by **guarding at
class creation** (so the no-primary path is provably unreachable at decode time) — leaving
the promoted helper's form behavior **byte-unchanged**. (If a future flavor needs to choose
the strict path at decode time instead, the seam is an explicit
`require_primary_type=True` parameter on the promoted helper, not a behavior change to the
form fallback.)

**Requiredness, `read_only`, `optional_fields`.** A create-input field's requiredness
is the serializer field's `field.required`, minus the `Meta.optional_fields` override
(graphene's `force_optional`); a `read_only=True` field and a `HiddenField` are
**dropped from the input** (graphene's `fields_for_serializer` `is_input` rule — a
read-only / hidden field is server-supplied, not client input). `<Serializer>PartialInput`
is every input field optional.

**Nullability and defaults — `allow_null` and `required` are two different axes.**
GraphQL input nullability and DRF requiredness are **orthogonal**, so the converter pins
them separately:

- **The annotation is nullable when the field is `allow_null=True` OR when it is optional
  in the generated input**, and every nullable field carries a `strawberry.UNSET` default
  so the key is omittable; only a `required=True, allow_null=False` field emits the bare
  non-null annotation with no default. Both halves of that disjunction are load-bearing.
  `allow_null=True` must be nullable so a legitimate `null` is accepted: DRF's
  `required=True, allow_null=True` means *"the client must send the key, but may send
  `null`,"* which a plain GraphQL input cannot express as **both** required and nullable,
  so the package makes the annotation nullable and enforces the *must-provide* half at the
  DRF layer — **omission still reaches DRF as "missing"** and `serializer.is_valid()`
  raises the field-`required` error itself. And an *optional* field must be nullable
  because the bullet below forbids fabricating a GraphQL default: a GraphQL input field
  that is neither nullable nor defaulted **is required**, so a non-null annotation on an
  omittable field would make the input un-satisfiable. Nullability and requiredness are
  therefore separate axes on the DRF side and jointly determine the emitted annotation.
- **Omission / default behavior follows `field.required` + the DRF default.** A
  `required=False` field with a serializer `default` (including `CreateOnlyDefault`) is
  **omittable** — leaving it out lets DRF apply the default; the converter does not
  fabricate a GraphQL default that would shadow DRF's.
- **Omitted vs explicit `None` are distinct and both preserved.** An omitted input key is
  **left absent** from `provided_data` (never injected as `None`), so DRF can tell *missing*
  from *explicit `null`* — the difference between "apply the default / treat as not-provided
  under `partial=True`" and "set the value to `None`." An explicitly-supplied `None` is
  **preserved** as `None` in `provided_data`.
- **`allow_blank` is not a GraphQL concern.** `allow_blank=True` (empty-string acceptance
  for `CharField`-family fields) is a **serializer validation rule**, not a nullability axis;
  it is **not** encoded in the GraphQL annotation and stays enforced by the serializer.

Tests pin all three axes ([Test plan](#test-plan)): `required=True, allow_null=True` (the
annotation is nullable, omission still triggers DRF's required error, explicit `null` is
accepted), `required=False, default=…` (omittable, DRF applies the default), and
`allow_blank=True` (not reflected in the SDL, enforced by the serializer).

**Two `Meta` namespaces — the mutation's vs the serializer's.** A
[`SerializerMutation`][glossary-serializermutation]'s `Meta.fields` / `Meta.exclude`
narrows the **GraphQL input surface** (which serializer fields become input arguments) —
it does **not** restrict the serializer's own `Meta.fields` *validation* set. A DRF
migrant must not expect the mutation key to change what `serializer.is_valid()`
validates: the serializer still validates its full declared field set; the mutation key
only removes client-supplied **inputs** (and the create-required guard below rejects a
narrowing that would drop a field the serializer requires). And `Meta.optional_fields` is
a **no-op on `update`** — `<Serializer>PartialInput` is already all-optional, so a consumer
who sets `optional_fields` on an `update` mutation changes nothing; it is meaningful only
on `create`.

**Output direction — not adopted; the frozen slot supersedes it.** graphene's
`fields_for_serializer(is_input=False)` builds a serializer-derived *output* type; the
package's mutation **output** is the primary [`DjangoType`][glossary-djangotype] in the
frozen `node` / `result` slot ([`spec-036`][spec-036] AR-H5). So the converter is
**input-directed** in `0.0.13` — the card's "dual-purposed for inputs **and outputs**"
wording is reconciled to the frozen slot (the same way `038` superseded
`Meta.return_field_name`), recorded in [Risks and open questions][rationale-risks]. An `is_input`
parameter is carried on `convert_serializer_field`'s **signature** for graphene-parity and
forward use, but it is **accepted-and-ignored — there is no `if not is_input:` branch** in
`0.0.13`: the converter is input-directed and `is_input` never alters control flow, so it
leaves **no uncovered branch** under `fail_under = 100` (a merely-threaded parameter is
free; a dead `is_input=False` branch would gate-fail). A future serializer-derived output
direction adds the branch **and** its coverage together.

**Reverse map.** Record, per generated input field, a `utils/inputs.py::InputFieldSpec`
(the `038` `FormInputFieldSpec` analog, **plus the `source` axis** Django form fields lack
— see **Renamed fields** above) so [`rest_framework/resolvers.py`][rf-resolvers] builds a
payload keyed by the **declared serializer field name** (`categoryId` → `category`; a
renamed `categoryPk` → `category_pk`), which DRF maps to `source` internally. The spec
carries nine axes — `input_attr` / `graphql_name` / `target_name` / `kind` / `source` /
`related_model` / `nested_specs` / `annotation_repr` / `required` — and `kind` has six
members: `scalar`, `relation_single`, `relation_multi`, `file`, plus `nested_single` /
`nested_multi` for an opted-in nested serializer. `nested_specs` is what lets
the resolver's reverse map recurse, so nested error paths and nested decode key by SDL
name at every depth.

**Shape identity is the generated field specs, not the field names** — the divergence
from the `036` / `038` generators. There, `(class, operation, frozenset(names))` is a
sufficient identity because the model column (or the form field class) **fixes** each
field's type and requiredness, so a given name-set deterministically yields one shape.
A serializer breaks that determinism two ways: (1) `Meta.optional_fields` changes a
create input's requiredness **without changing the name set**; and (2) the schema-time
`get_serializer_for_schema()` hook can return the **same field names** with different
field classes, `source`, child type, `choices`, relation kind, or requiredness. Under a
name-only identity, the first declaration would win the shape cache and silently hand a
later mutation the wrong nullability, annotation, or reverse map. So the serializer
identity is a **`SerializerInputShape` descriptor** carrying the backing serializer
class, the operation kind, the ordered emitted field specs, the emitted **annotations**,
the emitted **descriptions**, the required state, the normalized `optional_fields` set,
and the type name. Two axes are easy to under-state and both are load-bearing:
`descriptions` is **independent** (DRF field metadata is threaded into the SDL, so a
description-only hook divergence must not share a generated class), and the annotation
axis is the **post-nullable-widening** repr taken after the optional-field widening — which
is exactly what makes a `required=True, allow_null=False` and a
`required=True, allow_null=True` pair diverge rather than collapse onto one shape. The **same descriptor** drives the per-shape **bind/build cache**, the
**generated-name derivation**, and the **materialization collision check** — one source
of truth.

**Naming + dedupe.** The canonical `<Serializer>Input` / `<Serializer>PartialInput` is
granted only when the shape's per-field identity **equals the identity the default,
no-argument schema discovery produces** (`rest_framework/inputs.py::_default_full_shape_identity`,
consumed by `::build_serializer_input_class`) — not merely when the shape happens to look
full. A `get_serializer_for_schema()` hook returning a differently-shaped "full" field set
therefore takes a descriptor-derived name; granting it the canonical name would let two
distinct descriptors collide there at materialize. Any shape that differs (narrowed by
`Meta.fields` / `Meta.exclude`,
`optional_fields`-modified, or hook-varied) derives a **deterministic name from the
descriptor** (a stable suffix), so two same-name-set-but-different-shape inputs get
**distinct** names rather than silently colliding. Identical descriptors dedupe; two
**distinct** descriptors that would still land on one generated name → a finalize-time
[`ConfigurationError`][glossary-configurationerror] (the reused
`materialize_generated_input_class` ledger raise, now keyed by descriptor). `Meta.fields`
/ `Meta.exclude` / `Meta.optional_fields` are normalized + fail-loud against the
serializer's field set — a **bare string (including `"__all__"`)**, a duplicate, an
unknown name, or an empty effective set raises
[`ConfigurationError`][glossary-configurationerror]. There is **no `"__all__"`
sentinel** for these keys: the package's `"__all__"` is the non-field-error envelope key
alone, never a field selector, so an all-optional create input is expressed by listing
the fields in `optional_fields`, not by `optional_fields = "__all__"` (rejected as a
bare string, with a message pointing at the explicit list).

**Create-required narrowing guard (bind-time, per declaration).** `Meta.fields` /
`Meta.exclude` are validated against the serializer field set, but a *valid* narrowing
can still drop a field `serializer.is_valid()` will require, finalizing a schema that
can never be satisfied (the client has no way to supply the omitted field). The form
flavor already guards this ([`forms/inputs.py`][forms-inputs] `guard_create_required_fields`,
run per declaration by [`forms/sets.py`][forms-sets] `_cached_build_form_input`
#"Run the create-required-narrowing guard PER declaration"); the serializer flavor
gets the DRF-adapted analog, `guard_create_required_serializer_fields`: for a **create**
input, raise [`ConfigurationError`][glossary-configurationerror] naming any **writeable**
serializer field with `field.required` (and no serializer `default`) that the effective
set drops. `read_only` / `HiddenField` fields are never client inputs, so they do **not**
count as dropped-required. The guard runs **per mutation declaration, before the
shape-cache lookup**. `Meta.injected_fields` is the only subtraction and is declaration
state rather than shape identity, so an injecting mutation that materializes a narrowed
shape first cannot suppress the guard for a later non-injecting mutation reusing the
cached shape. Update inputs need no such guard — DRF
`partial=True` makes every field optional, so a dropped field is simply un-validated.

Rationale companion — this Decision's justification and its three rejected alternatives:
[Decision 7][rationale-d7].

**Cross-flavor reuse ([DRY obligations](#cross-flavor-reuse-and-dry-obligations)).** The
converter + input generator is where the form flavor forked the most from the model
flavor, so the serializer is on track to be the third copy of each. The spec pins the
reuse: the fail-loud dispatch is the shared `(field, isinstance_prechecks,
scalar_registry, fallthrough_error_factory) → conversion` **skeleton** in a new
`utils/converters.py` — `convert_serializer_field` supplies only its precheck table +
scalar registry, so the **GOAL-mandated no-silent-`String`-catch-all contract is
single-sited** across `forms/converter.py` and the serializer converter; the
reverse-map field spec is the unified `InputFieldSpec` (the `038` `FormInputFieldSpec`
analog plus the `source` axis) sited in [`utils/inputs.py`][utils-inputs], not a third
ad-hoc dataclass; the `SerializerInputShape` descriptor identity is
legitimately new, but its **cache + clear plumbing** is the promoted
`make_shape_build_cache()` and its **stash procedure** the promoted
`build_and_stash_input` — though, because the descriptor cache key is only
knowable after the build, the per-shape dedupe stays an inline lookup-or-store rather than
`cached_build_input` (whose pre-build key lookup would force building the shape twice); the
input namespace is the
promoted `make_input_namespace(...)` **one-ledger** trio — the form / mutation clear
shape, **not** the heavier `clear_generated_input_namespace`; the
divergent-shape suffix reuses `utils/inputs.py::pascalize_token`.
Required-field injection is declaration-scoped through `Meta.injected_fields`; constructor
hook identity is not part of guard behavior.

### Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `serializer.errors` → `save()` → optimizer re-fetch → payload

[`rest_framework/resolvers.py`][rf-resolvers] runs the sync + async pipeline, reusing
the `036` / `038` promoted helpers (`locate_instance` / `coerce_lookup_id` /
`authorize_or_raise` / `refetch_optimized` / `build_payload` / `not_found_error`) by
call, not re-implementation. The shared decode primitives live in
`utils/write_values.py` (`decode_visible_relation`, `decode_visible_relation_ids`,
`decode_provided_fields`, `decode_field_handlers`, `decoded_into`,
`type_check_relation_id`, `coerce_relation_pk_or_none`, `raw_choice_value`) and the
shared leaf-error constructors in `utils/errors.py` (`field_error`,
`validation_error_to_field_errors`, `integrity_error_field_errors`,
`join_error_path`); the serializer flavor calls both and re-implements neither.

**The transaction boundary is a guarded, phase-separated pipeline, not a bare
`transaction.atomic()`.** Every consumer-reachable phase — the permission hook, decode,
hooks, validation, write, and re-fetch, for all three write flavors and delete — runs
under a pipeline-wide **alias guard**
([`utils/write_transaction.py`][utils-write-transaction]`::pipeline_alias_guard`): an
`execute_wrapper` on every non-pinned configured connection rejects **every** SQL
statement, with deliberately **no read/write classification** (a lexical keyword test is
bypassable — leading SQL comments, PostgreSQL `EXPLAIN ANALYZE UPDATE`, write-capable
functions invoked through `SELECT`) and **before the query executes**, since post-hoc
detection could not roll back an already-escaped cross-alias write. That covers the
signal-less `QuerySet.update()` / `bulk_create` / raw-cursor paths by construction; a
thread-scoped `pre_save` guard gives the `Model.save()` path an earlier, clearer error.
The guard grants exactly **one** narrow, phase-scoped exception: a dedicated
**authorization phase** (`::authorization_phase`) wraps only the single
permission-evaluation call and permits statements on the explicitly identified **auth
aliases** ([`utils/permissions.py`][utils-permissions]`::resolve_auth_aliases` — the
router's read answer for the user model, `auth.Permission` / `Group`, and
`contenttypes`), so a divergent read/write router that keeps auth off the write alias can
still resolve the user + permission set. That boundary is **transactional and
database-enforced, never lexical**: each non-pinned auth alias runs inside a
`transaction.atomic` put in a **backend-enforced read-only mode**
(`::_enforce_read_only_barrier` — PostgreSQL `SET TRANSACTION READ ONLY`, SQLite
`PRAGMA query_only`, the latter read and restored to its prior value on exit so a
pre-existing setting or an enclosing barrier survives — stack-safe) **and**
unconditionally rolled back when the phase ends. Forced rollback alone is **not** a
portable barrier even against ordinary writes (non-transactional tables and
implicitly-committed DDL escape it), so an ordinary write a permission backend attempts
is refused by the database itself and discarded on rollback; a backend that cannot
provide the read-only guarantee **fails closed** — the pipeline raises rather than route
auth there. This is **not** a sandbox against a *hostile* backend: backend read-only mode
still permits side-effecting functions (PostgreSQL `nextval` / `setval` advance a
sequence and are never rolled back; a session-scope advisory lock outlives the
transaction), so the model **trusts permission backends to read only** — the barrier
contains ordinary and accidental writes, not deliberate volatile side effects, and a
deployment that cannot make that assumption must use genuinely capability-restricted
credentials for divergent-router authorization. The exception closes the instant
authorization returns — decode, hooks, and validation cannot reach the auth alias — and
evaluating permissions there fills the per-user cache as a side effect, so no pre-guard
warming step exists. It is gated on the mutation actually declaring permission classes,
so the explicit `permission_classes = []` opt-out grants no auth-alias access and never
resolves the lazy user.

**Phase separation on the pinned connection.** Permission checks, decoding, hooks,
validation, and save-kwargs preparation are **database-read-only**: on the pinned
connection the guard rejects write-shaped SQL outside the flavor's write phase
(`::pipeline_write_phase()`, opened for exactly `serializer.save()` / `Model.save()` +
M2M / `form.save()` / `instance.delete()`). There the conservative comment-stripped
allow-list (`::is_read_only_sql`) is **phase-ordering enforcement, not the atomicity
boundary** — a false negative still executes inside the pinned transaction and rolls back
with it. `serializer.save()` runs inside its own nested-`atomic` **savepoint**, rolled
back *before* a caught DRF / Django `ValidationError` or `IntegrityError` converts into
the [`FieldError`][glossary-fielderror-envelope] envelope, so a custom `save()` that
wrote rows and then raised leaves no partial write. The exceptions are caught **outside**
the atomic block: an `IntegrityError` escaping `save_base`'s savepoint-less inner atomic
flags `needs_rollback`, which only the enclosing atomic's own rollback clears.

The pipeline steps:

1. **Locate** (`update` only): coerce the top-level `id:` `GlobalID` and resolve the
   row through the target type's [`get_queryset`][glossary-get_queryset-visibility-hook]
   (a miss / hidden row → a not-found `FieldError` on `id`, no existence leak). `create`
   has no instance lookup. This is the **only** decode that precedes authorization, and
   it is a `GlobalID` decode of the mutation's *own* `id:` argument — never a relation
   visibility probe. **The pipeline skeleton snapshots the authorized pk and the located
   row's loaded concrete field values immediately after the locate** — before the
   permission hook, the first consumer-controlled code, can touch the mutable located
   instance — and publishes them on the write-pipeline context
   ([`utils/write_transaction.py`][utils-write-transaction]`::WriteAliasContext.authorized_pk`
   / `.target_state`). The snapshot captures each field **by value**, never by reference:
   mutable containers (`JSONField` / `ArrayField`) as iterative structural fingerprints
   and a `FieldFile` by its database-relevant `name` string, so an in-place mutation on
   the same object (`instance.data["x"] = …`, `instance.file.name = …`) is still caught as
   drift. Pk equality everywhere goes through the model pk field's own `to_python`
   canonicalization (`::pks_match`), never a `str()` comparison — a `UUID` pk spells the
   same row several ways, and a forged pk of the wrong shape must read as a mismatch.
   `Meta.select_for_update` governs whether the locate takes a row lock.
2. **Authorize** via the inherited `check_permission` / `Meta.permission_classes`,
   **before any relation decoding** — `create` authorizes the **raw input payload**
   with `instance=None`; `update` authorizes the located instance + the raw payload.
   Denial → top-level `GraphQLError`. **This ordering is a package security invariant,
   not an incidental step:** relation decoding (step 3) issues visibility-scoped
   `get_queryset` queries, so decoding *before* authorization would let an unauthorized
   caller probe related-object visibility by id — observing an auth denial vs a
   relation-specific `FieldError` for a missing / hidden / malformed / wrong-type
   related id (most visible on `create`, which needs no instance lookup at all before
   authorization). The `038` form pipeline pins exactly this
   ([`forms/resolvers.py`][forms-resolvers] #"Authorize runs BEFORE the relation decode":
   *"the decode issues visibility-scoped `get_queryset`
   queries, so running it pre-auth would let an unauthorized caller probe related-object
   visibility by id … Matches the `036` model path's locate → authorize → decode
   order"*); the serializer pipeline obeys the same **locate → authorize → decode**
   order.
3. **Decode** the (now-authorized) `data:` input via the reverse map into a
   serializer-field-keyed `provided_data`, using a **dedicated serializer relation
   decoder** that mirrors the `038` form decoder (serializer-field-keyed, NOT the
   model-attr-keyed `036` `_decode_relation_id_set`). **The generated input field carries
   exactly ONE annotation, strategy-dependent** (Decision 7): a relation whose target
   primary [`DjangoType`][glossary-djangotype] is Relay-shaped exposes a `GlobalID`; a
   non-Relay / raw-pk target exposes the target's raw-pk scalar. So a *live* GraphQL
   request can only ever deliver the **one shape the annotation admits** — a raw integer
   against a `GlobalID`-typed field is a **top-level variable-coercion error before the
   resolver runs** (verified: products' `test_create_item_malformed_category_id_is_top_level_coercion_error`,
   because relation inputs are typed `GlobalID`, not `ID!`). The **shared decode helper**
   accepts **both** a `GlobalID` and a raw pk because it is reused and package tests
   exercise the raw-pk / non-Relay branch by **direct call** (no live HTTP shape exists for
   it unless fakeshop grows a real non-Relay relation field). Each id the decoder does see
   is type-checked against the relation's **target model** — resolved from the backing FK
   via the serializer field's `source`, or, for a serializer-only relation, from the DRF
   field's `queryset.model`
   ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)) —
   resolved to the **visible** object through the related primary
   `DjangoType.get_queryset` — the same per-branch raw-pk visibility check both `036`'s
   model-path decoder (`_decode_relation_id_set` → `_raw_pk_relation_error`) and the
   `038` form decoder (now the shared `visible_related_object`) already enforce — and reduced to the
   **pk** DRF's `PrimaryKeyRelatedField` expects before landing under the **serializer
   field name** (the public `data` key DRF maps to `source` internally,
   [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
   a hidden / wrong-type target → field-keyed
   [`FieldError`][glossary-fielderror-envelope]. **The decode consumes the recorded Relay
   GlobalID strategy, never the live setting:** a `GlobalID` is decoded through the
   existing Relay decode helpers against the target type's recorded
   `effective_globalid_strategy` ([`types/relay.py`][types-relay] /
   [`types/definition.py`][types-definition], resolved once at finalization), and the
   decoder must **not** read `conf.settings.RELAY_GLOBALID_STRATEGY` or call
   `_resolve_globalid_strategy(...)` on the query path — that domain validation belongs to
   finalization, not request handling (no per-request re-read / re-validate). A
   `FileField` / `ImageField` value
   (an [`Upload`][glossary-upload-scalar]) lands in `provided_data` like any other
   value — DRF serializers read files from `data`, the deliberate contrast with the
   `038` form flavor's `data=` / `files=` split (a bound Django form reads files from
   `files=`).
4. **Construct** the serializer. **The framework builds the authoritative `data` itself
   and owns every reserved constructor kwarg**; the overridable
   `get_serializer_kwargs(self, info, *, data, hook_context)` hook is
   **constructor-only** — a seam for *additional* kwargs (an extra `context` key, a
   constructor argument such as `tenant`), never a seam for reshaping the write.
   - **The framework composes `data`** as decoded client input plus the values
     `get_serializer_injected_data(self, info, *, data, hook_context)` supplies for the
     `Meta.injected_fields` declaration; the hook's returned keys must match
     that declaration **exactly** — a missing declared field or an undeclared extra key
     is a [`ConfigurationError`][glossary-configurationerror].
   - **Consumer hooks never receive the live located instance.** Every hook
     (`get_serializer_kwargs`, `get_serializer_injected_data`,
     `get_serializer_save_kwargs`) takes a frozen
     `SerializerHookContext(operation, write_alias, instance_pk)`
     ([`rest_framework/hook_context.py`][rf-hook-context]) plus an **immutable data
     view**: read-only mapping proxies, lists and tuples as tuples, sets as frozensets,
     `bytearray` as `bytes`, and each upload replaced by a frozen `UploadMetadata`
     descriptor, so the stateful authoritative upload objects reach only the serializer's
     own validation. The freeze (`_frozen_hook_view`) is **recursive and iteratively
     built**, so nested in-place mutation is structurally impossible and
     client-controlled JSON nesting depth cannot crash the pipeline with a
     `RecursionError`; a **cyclic** container is a loud `ConfigurationError` rather than an
     unbounded loop; a merely shared (diamond) reference freezes once and stays shared;
     immutable scalar leaves pass by reference; and an opaque, possibly-mutable leaf with
     no immutable rendering **fails closed** rather than being aliased into a value a hook
     could mutate to reach the authoritative data.
   - **Every hook result crosses a typed mapping boundary** (`_hook_mapping`): a
     non-`Mapping` return, a mapping that cannot be materialized, and a mapping carrying
     a non-`str` key are each a `ConfigurationError` naming the hook — never a silent
     coercion.
   - **`data`, `instance`, `partial`, `context["request"]`, and `context["write_alias"]`
     are framework-owned.** The reserved returns are checked by **omission sentinel +
     object identity**, never deep equality: a returned `data` must be omitted or the
     **exact** frozen object the hook received (an explicit `data=None` and a
     rebuilt-equal copy are both refused — a deep `!=` recurses on deep valid payloads,
     and a `pop(..., None)` default conflates explicit `None` with omission), and **any**
     returned `instance` key is rejected outright, since the framework injects the
     authorized row itself and hooks see only its pk via `hook_context.instance_pk`.
     `partial` is the update contract, not a knob: the resolver sets `partial=True` for
     `update` and never for `create`, and a hook returning a `partial` key **at all** —
     whatever its value, on either operation — is a `ConfigurationError`. After merging the hook's other kwargs the framework
     sets `context["request"] = request_from_info(info, family_label="SerializerMutation")`
     and `context["write_alias"]` **unconditionally** — the same request object the
     inherited `check_permission` / `permission_classes` seam already authorized against
     so the serializer's request-aware validators cannot drift from the actor the
     permission check saw. Consumer-specific context belongs under **other** keys.
   - **Post-construct, pre-`is_valid()`, the runtime serializer is proved to agree with
     the schema** (`_assert_schema_runtime_agreement` → `_assert_field_agreement` /
     `_assert_relation_agreement` / `_assert_nested_agreement`), and
     `_assert_runtime_write_source_ownership` re-runs the writable-`source` uniqueness
     rule against the **runtime**, context-dependent `get_fields()` at every nesting
     depth — a serializer whose runtime field set feeds two writable inputs into one model
     attribute is rejected there even though its schema-time field map was clean.
   - **Every top-level and nested relation field's queryset is composed as author
     queryset ∩ target visibility** (`_scope_relation_querysets_to_visibility` /
     `_scope_specs_over_serializer`), pinned to the operation's write alias and
     locked when `Meta.select_for_update` locks; a cross-alias author queryset **fails
     closed**.
5. **Validate** via `serializer.is_valid()` — a failure maps the nested
   `serializer.errors` structure onto the
   [`FieldError` envelope][glossary-fielderror-envelope] via a **dedicated recursive
   serializer-error flattener** (DRF's `non_field_errors` /
   `api_settings.NON_FIELD_ERRORS_KEY` bucket → the `"__all__"` sentinel `036` froze)
   and returns a null-object payload. `serializer.errors` is **not** the flat
   `field → [messages]` dict the `036` `validation_error_to_field_errors` handles — the
   flattener is spelled out below. Two guards bracket the validation:
   - **A relation-intent ledger.** `_instrument_relation_intent` wraps every (top-level
     and nested) relation field's `run_validation()` after the queryset scoping and
     before `is_valid()`, recording the exact resolved objects — one entry per `many=True`
     list item, with custom `pk_field` implementations still supported, since the ledger
     records the relation object DRF finally resolves. `_assert_relation_intent` then
     requires the final `validated_data` to carry them **by identity**: renamed sources,
     injected fields, single relations, lists (length plus pairwise identity, so duplicate
     and explicit-empty-list set semantics pass through), and nested paths alike. A
     validator may reject or pop a relation (popping reverts to omitted semantics); it may
     never substitute or inject one.
   - **Validator queryset pinning.** `_pin_validator_querysets` walks the serializer's
     validators recursively — per instance, on a copy — and pins each one's queryset to
     the operation's write alias, so a `UniqueTogetherValidator` (or any author validator)
     cannot read through a different connection than the write is pinned to.

   The flattener itself is **iterative, cycle-rejecting, and budget-capped** for the same
   reason the hook freeze is: the error structure mirrors client-controlled input nesting,
   so a pathological fan-out ends in one `"__all__"`-keyed `truncated` marker
   (`_ERROR_FLATTEN_NODE_BUDGET`) instead of unbounded work, and a cyclic structure fails
   loud rather than looping.
6. **Write** via `serializer.save()`, **wrapped by the `036` `IntegrityError` → envelope
   mapper** (`utils/errors.py::integrity_error_field_errors` — no top-level error on a
   save-time race); `serializer.save()` runs `create()` / `update()` and handles M2M
   assignment internally (DRF's `ModelSerializer.save()` writes the instance + its
   relations). Five guards bracket the write, in order:
   - **In-memory target drift is rejected immediately before `serializer.save()`**
     (`assert_no_target_drift`, against the step-1 `target_state` snapshot). DRF's
     `update()` saves the whole instance, so a `setattr` by a permission method, hook, or
     validator would otherwise ride into the write unvalidated. A flavor-independent
     backstop separately rejects an update result whose pk drifted from the
     `authorized_pk` snapshot, and a delete whose instance pk drifts during authorization
     fails the same way.
   - **A pre-save M2M membership snapshot** (`_m2m_membership_snapshot`) is taken at
     write-step entry — strictly **after** authorization, so no relation-membership query
     ever runs pre-auth, and before any consumer hook.
   - **A thread-scoped write witness** (`_write_witness`) records the backing model's
     actual writes through `post_save`, **with a pk snapshot taken at the signal**,
     because the model object is mutable and identity alone is forgeable; a `pre_save`
     arm blocks cross-alias writes.
   - **`get_serializer_save_kwargs` runs inside the same value-preserving, error-mapped
     closure as `save()` itself**.
   - **After the save the returned top-level row is attested against the database**
     (`_attest_saved_relations`): every supplied FK / OneToOne column is read back in one
     `values()` query and must hold the validated target's pk (canonical comparison
     through the related pk field), every supplied M2M must equal the validated pk
     **set** (an explicit `[]` clears; duplicates collapse per DRF `.set()` semantics),
     and every omitted partial-update M2M on the write surface must equal its pre-save
     membership snapshot. A custom `create()` / `update()` that ignored or replaced
     validated relations is a loud [`ConfigurationError`][glossary-configurationerror];
     arbitrary same-alias behavior inside custom write code otherwise remains trusted.

   **The save result is validated before the re-fetch** (`_checked_saved_result`):
   correct model; identity with `serializer.instance` (DRF's `save()` bookkeeping — a
   detached saved-looking fabrication fails closed); a non-null pk and not `_state.adding`;
   exactly the pinned alias; on **create**, a witnessed `created=True` write of the
   returned row on the pinned alias **whose snapshotted pk still equals the returned pk**
   (identity alone is forgeable through normal DRF bookkeeping — a custom `create()`
   returning an existing row is still assigned to `self.instance`, and a really-inserted
   object can be re-pointed at a hidden row's pk afterwards, so only the observed INSERT
   plus the pk snapshot proves the row was not laundered through the visibility-free
   re-fetch; signal-less bulk persistence fails closed); and on **update**, the same pk as
   the post-locate `authorized_pk` snapshot (a live `instance.pk` comparison would be
   forgeable, since `instance` and the returned object can be the same mutable object).

   **The wrapper is value-preserving — the saved object is captured, not re-derived.**
   The model and form flavors ride `mutations/resolvers.py::save_or_field_errors`, which
   returns `list[FieldError] | None` and **discards the callable's return value** (it is
   shaped for paths that already hold the instance). The serializer path needs the object
   DRF returns from `serializer.save()` **and** needs the savepoint containment above, so
   it spells the same contract inline over the shared leaf constructor rather than through
   that wrapper — capturing the return in the closure rather than re-deriving it (no
   second `serializer.save()`, no re-fetch from a stale `serializer.instance`):
   ```python
   saved = None
   def _do_save():
       nonlocal saved
       saved = serializer.save(**save_kwargs)   # called exactly once
   ```
   The re-fetch (step 7) then keys off `saved.pk`. (`serializer.instance` *is* `saved`
   after a successful DRF `save()`, but pinning the captured return value keeps the
   contract explicit and the call-once guarantee testable.)
   **A save-time `ValidationError` is routed to the envelope, not raised — but DRF and
   Django `ValidationError`s have DIFFERENT shapes and take different paths.** A custom
   `create()` / `update()` / `save()` can raise either a DRF
   `rest_framework.exceptions.ValidationError` (== `serializers.ValidationError`, carrying
   a `.detail` that is the **same** arbitrarily-nested structure as `serializer.errors`)
   **or** a model-level `django.core.exceptions.ValidationError` (from a `full_clean()`
   inside `save()`, carrying Django's `error_dict` / `messages` shape — **no `.detail`**).
   Left unhandled either would escape as a **top-level `GraphQLError`**, contradicting this
   card's own "validation → [`FieldError`][glossary-fielderror-envelope] envelope, not
   `GraphQLError`" contract ([Error shapes](#error-shapes)). So the resolver wraps the
   save closure and routes by **exception class** — they are
   **not** one branch:
   - **DRF `ValidationError`** (`rest_framework.exceptions.ValidationError` /
     `serializers.ValidationError`): route its `.detail` through the **recursive**
     `serializer_errors_to_field_errors` flattener (the same nested structure
     `serializer.errors` produces).
   - **Django `ValidationError`** (`django.core.exceptions.ValidationError`): route through
     the flat `036` `utils/errors.py::validation_error_to_field_errors`,
     which already reads Django's `error_dict` / `messages` shape (verified — it does **not**
     read `.detail`); pushing a Django error through the DRF `.detail` path would
     `AttributeError` or silently lose structure.
   - **`IntegrityError`** (a concurrent-uniqueness race / residual db constraint): the
     shared `utils/errors.py::integrity_error_field_errors` leaf, the same envelope the
     `036` `save_or_field_errors` wrapper produces.

   The two `ValidationError` classes are caught **separately** (DRF's first, since both
   subclass `Exception` but neither subclasses the other) so a Django error never reaches
   the `.detail` path and a DRF error never reaches the flat mapper. All three stay inside
   the one `transaction.atomic()`; none becomes a top-level error. (The non-field bucket
   maps to `"__all__"` in **both** flatteners via the shared `NON_FIELD_ERROR_KEY`, so the
   envelope key convention is uniform regardless of which path fired.)
7. **Re-fetch** the saved object (by `saved.pk`) + optimizer-plan
   ([Decision 9](#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path)),
   and **return** the `<Name>Payload` (`node` / `result`).

The whole pipeline runs inside one `transaction.atomic()`, and the async path runs the
sync body in one `sync_to_async(thread_sensitive=True)` call — the same boundary
`036` / `038` set. A sync path meeting an `async def`
[`get_queryset`][glossary-get_queryset-visibility-hook] raises
[`SyncMisuseError`][glossary-syncmisuseerror] (coroutine closed first).

**`serializer.errors` is a recursive structure — the flattener pins a deterministic
path encoding.** Unlike a Django form's / model's flat `field → [messages]` errors
(which the `036` `validation_error_to_field_errors` handles by reading a one-level
`ValidationError.error_dict` with a `messages` fallback), DRF's `serializer.errors` is
an **arbitrarily nested** structure: `ErrorDetail` strings, lists, `ReturnDict` /
`ReturnList`, the **indexed child errors** a `ListField` / `MultipleChoiceField` /
`ListSerializer` produces (`{"tags": {0: ["…"], 2: ["…"]}}`), a `JSONField`'s dict
payload, and the `api_settings.NON_FIELD_ERRORS_KEY` bucket — while the shared
[`FieldError`][glossary-fielderror-envelope] is flat (`field: str`,
`messages: list[str]`). This is **not** a nested-writable-serializer concern (those
stay out of scope,
[Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)):
`ListField` / `MultipleChoiceField` / `JSONField` are **supported input field kinds**
that already produce nesting. So [`rest_framework/resolvers.py`][rf-resolvers] owns a
**dedicated recursive flattener** (`serializer_errors_to_field_errors`, **NOT** the
`036` mapper) with a **pinned path convention**: it walks the error tree depth-first,
joining dict keys and list indices with `.` into a dotted path (`items.0.name`,
`tags.2`); it normalizes DRF's `NON_FIELD_ERRORS_KEY` to the package's `"__all__"`
sentinel at **every** level (a top-level `validate()` error → `"__all__"`; a nested
non-field error → `<path>.__all__`); and it emits **one
[`FieldError`][glossary-fielderror-envelope] per leaf path** with all leaf
`ErrorDetail` values coerced to `str`. No nested structure is stringified into a single
message, and **no child error is dropped** — the failure mode an ad-hoc `str(errors)`
would hit. The flattener is the serializer-flavor analog of the model/form
`validation_error_to_field_errors`, but recursive; both terminate in the same shared
envelope.

**Error field names are keyed to the GraphQL input path, not the serializer path.**
`serializer.errors` keys are **serializer field names** (`category`, `name`), but a
client submitted **GraphQL input names** (`categoryId`, `fullName`). The flattener maps
each leaf path's **root segment back through the reverse map** to the GraphQL input name
when that serializer field has a generated input field — so a validation error on
`category` is reported as `FieldError(field="categoryId")` and a renamed `name`
(`source`-renamed `fullName`) as `FieldError(field="fullName")`, **aligning the envelope
with the relation-decode errors of step 3** (which already key by the submitted input
name) and with what the client can act on. The `"__all__"` non-field sentinel is
preserved as-is (it has no input field). **If an error references a serializer field with
no input field in the surface** — a field the serializer still validates but the mutation
did not expose (narrowed out, or read-only-but-still-validated) — the **serializer field
name is kept**, because there is no GraphQL input path to report; this is the one case the
envelope key is a serializer name. **The re-keying runs at every depth, not only the root**
(`_rekey_segment` over the recursive child maps `_build_reverse_map` derives from
`InputFieldSpec.nested_specs`), so a nested child field, alias, or relation suffix reports
its SDL name (`shelves.0.altBranches`, never `shelves.0.alt_branches`); numeric indexes, a
`JSONField`'s own keys, and the `"__all__"` non-field sentinel are preserved as they are.
The
choice is locked by a **live renamed-field error test** ([Test plan](#test-plan)), not only
a plain `name` error, so decode errors, validation errors, and renamed-field errors all
agree on the key space.

**`update` is DRF-native partial, not a reconstruction (the divergence from `038`).**
Where the `038` form flavor reconstructs the full bound payload from the located
instance (a bound Django form re-validates the whole field set), a DRF serializer with
`partial=True` validates **only the provided fields** natively — so `update` passes
`provided_data` directly with `partial=True`, no `model_to_dict` reconstruction. This
is simpler and is the DRF idiom; a `UniqueTogetherValidator` still validates the
provided field against the instance's unchanged members.

Rationale companion — this Decision's justification and its three rejected alternatives:
[Decision 8][rationale-d8].

**Cross-flavor reuse ([DRY obligations](#cross-flavor-reuse-and-dry-obligations)).** This
pipeline carries the package's load-bearing **security ordering** (authorize → decode), so
its DRY promotions matter most. The whole **sync orchestration** — the
`transaction.atomic()` boundary, the create-vs-update branch, the `coerce_lookup_id →
locate_instance → not_found_error → authorize_or_raise` preamble, and the
`refetch_optimized → build_payload` tail — rides the promoted
`run_write_pipeline_sync(...)` skeleton, which is **the one write skeleton every flavor
rides**: model `DjangoMutation` create / update / **delete**, `DjangoModelFormMutation`,
this serializer flavor, and the **model-less plain form**. The callback contract is what
keeps it small rather than generic: the skeleton owns atomicity, locate, the not-found
payload, **authorization before `decode_step`**, the optimizer re-fetch, and payload
construction; each flavor supplies only
`decode_step(instance) -> decoded data | list[FieldError]`,
`write_step(instance, decoded) -> saved instance | list[FieldError]` (the serializer's is
construct / `is_valid()` / `save()`), and — where the default tail does not fit — a
`tail_step(saved)`, which is the delete flavor's snapshot-before-delete payload. A
model-less mutation, having no primary type, takes the `{ ok: true }` tail. Every one of
those variations is a callback, so none of them re-spells the security ordering — the
**authorize-before-decode invariant is single-sited** across every flavor rather than
hand-copied a third time, and the existing model + model-form behavior must stay
**byte-equivalent under their current tests** before serializer code lands. The relation
decoder re-keys over the
promoted `visible_related_object` (in [`utils/querysets.py`][utils-querysets]) instead of
forking a third object-returning, field-keyed decoder. And the recursive
`serializer_errors_to_field_errors` flattener — legitimately new — imports the shared
`mutations/inputs.py::NON_FIELD_ERROR_KEY` sentinel (and, ideally, a promoted
`field_error(path, messages)` leaf ctor both flatteners call), so the DRF
`non_field_errors` → `"__all__"` convention cannot drift between the flat `036` mapper and
this recursive one (step 5).

### Decision 9 — Optimizer composition: the `ModelSerializer` payload re-fetch rides the `spec-036` G2 path

The payload's object is re-fetched by pk and routed through
[`DjangoOptimizerExtension`][glossary-djangooptimizerextension] for the response
selection through the **same** `036` re-fetch path (`refetch_optimized`) the
model-driven and form mutations use. Because the operation is a **mutation**, the
[`spec-035`][spec-035] **G2** gate keeps `select_related` / `prefetch_related` but
suppresses all `.only(...)` column deferral — so the re-fetched instance carries no
selection-shaped deferred-field set. The re-fetch is **by pk, without the visibility
`get_queryset` filter** (the actor just wrote the row — the `036` Medium-1 exception to
[`GOAL.md`][goal] crit-4). This card writes **no** new optimizer code; it reuses the
shipped path.

Rationale companion — this Decision's justification and its one rejected alternative:
[Decision 9][rationale-d9].

### Decision 10 — Operations: `create` / `update`, no serializer `delete`

`Meta.operation` is restricted to `"create"` / `"update"` for
[`SerializerMutation`][glossary-serializermutation]; a `"delete"` is **rejected** at
class creation with a [`ConfigurationError`][glossary-configurationerror]. This matches
graphene-django's `model_operations = ["create", "update"]` default and the `038` form
flavor (a `ModelForm` / serializer validates + writes, it does not delete). A `delete`
write stays the model-driven [`DjangoMutation`][glossary-djangomutation]
(`Meta.operation = "delete"`) the consumer already has.

The package's per-operation `Meta.operation` (one mutation per op) is used rather than
graphene's runtime-dispatched `Meta.model_operations` list (one mutation handling both,
dispatched by whether the lookup field is in the input) — the uniform-with-`DjangoMutation`
convention. graphene's `Meta.model_operations` / `Meta.lookup_field` keys are recorded
as deliberate non-adoptions in [Risks and open questions][rationale-risks].

**`Meta.operation` stays mandatory** (no default), and [`GOAL.md`][goal]'s crit-6
serializer example omits it. This is **not** a divergence to paper over by defaulting:
the shipped model-driven base **already requires** an explicit `operation` —
`DjangoMutation`'s `_validate_meta` rejects a missing key
(`getattr(meta, "operation", None)` must be in `{"create", "update", "delete"}`,
[`spec-036`][spec-036]), and the `038` `DjangoModelFormMutation` follows suit. Defaulting
`operation = "create"` for the serializer flavor alone would make it the **only** write
flavor that infers the operation — breaking the "Meta mental model carries over" (crit 7)
uniformity the spec leans on. So the fix is to make GOAL.md match the package, not the
other way around: **Slice 4 adds `operation = "create"` to GOAL.md's example.** The real
crit-7 friction this leaves for a `graphene-django` serializer-mutation migrant — who
runs one auto-dispatching `model_operations = ["create", "update"]` mutation — is that
they must (i) add an `operation` key and (ii) split that one mutation into two. That
friction, and the `model_operations`-alias affordance that would soften it, are owned by
the [Risks and open questions][rationale-risks] `model_operations` item.

**Cross-flavor reuse ([DRY obligations](#cross-flavor-reuse-and-dry-obligations)).** The
`{create, update}` set the serializer `_validate_meta` checks against is **byte-identical**
to the form flavor's (both being "a validating write flavor that does not delete"), and
`mutations/operations.py::_VALID_OPERATIONS` is the `{create, update, delete}` superset. The
serializer must **not** define a `_VALID_SERIALIZER_OPERATIONS`: one
`NON_DELETE_WRITE_OPERATIONS` constant and one `non_delete_operation_error` message live in
`mutations/operations.py` and reach **both** the form and serializer `_validate_meta`
overrides through `mutations/sets.py::require_non_delete_operation`, so the rule and the
"no serializer/form delete" message single-site.

Rationale companion — this Decision's justification and its two rejected alternatives:
[Decision 10][rationale-d10].

### Decision 11 — Write authorization: reuse the `036` seam (`DjangoModelPermission` for the `ModelSerializer`)

The flavor inherits the [`spec-036`][spec-036] Decision 15 write-authorization seam
unchanged: `Meta.permission_classes` defaults to `[DjangoModelPermission]`, which
resolves the model via the `_resolve_model` override
(`Meta.serializer_class.Meta.model`) and enforces the Django `add` / `change` model
perm (`create` requires `add`, `update` requires `change`). An anonymous or
under-privileged caller is denied with a top-level `GraphQLError` before any write.
Write authorization stays **separate** from [`get_queryset`][glossary-get_queryset-visibility-hook]
visibility (can-view ≠ can-write) and from the serializer's own validation. The
`check_permission(self, info, operation, data, instance=None)` override point is the
escape hatch, exactly as for the model and form flavors.

Rationale companion — this Decision's justification and its one rejected alternative:
[Decision 11][rationale-d11].

### Decision 12 — Soft `djangorestframework` dependency and the 100%-coverage strategy

`djangorestframework` is a **soft runtime dependency**: the package top-level import
must succeed without DRF installed, and importing
[`SerializerMutation`][glossary-serializermutation] (or any `rest_framework/` module)
without DRF raises `ImportError` with an **install hint**. Because the package root
[`__init__.py`][init] uses **eager imports + an explicit `__all__` tuple** (verified;
`SerializerMutation` cannot be a plain new import line — that would make
`import django_strawberry_framework` fail when DRF is absent), the export is **lazy via
a root-level `__getattr__`** (PEP 562). The exact, pinned behavior:

| Import | Behavior |
| --- | --- |
| `import django_strawberry_framework` | **Always succeeds** — DRF absent or present. The root never eagerly imports `rest_framework/`. |
| `from django_strawberry_framework import SerializerMutation` | Triggers the root `__getattr__("SerializerMutation")`, which imports `rest_framework.sets`. DRF present → the class; **DRF absent → `ImportError` with the install hint**. |
| `import django_strawberry_framework.rest_framework` (or any submodule) | The `rest_framework/__init__.py` guard runs `require_drf()` first — DRF absent → `ImportError` with the hint. |
| `from django_strawberry_framework import *` | **Always succeeds and omits `SerializerMutation`** — the name is **not** in `__all__` while DRF is soft, so a star import never resolves it through `__getattr__` and never trips the DRF guard. A DRF-absent consumer who does `import *` today keeps working unchanged (no breaking regression). |

One shared **`require_drf()`** helper (in `rest_framework/__init__.py`) owns the single
install-hint message and is the one place every `rest_framework/` module and the root
`__getattr__` route the guard through (no duplicated try/except message strings) — the
[`types/converters.py`][types-converters] soft-import precedent (`_resolve_array_field`
/ `_resolve_hstore_field`, which return `None` on `ImportError`) generalized to a
*raising* guard with an actionable message.

**`SerializerMutation` is a public lazy export but is NOT added to `__all__` while DRF is
a soft dependency.** Star import (`from … import *`) consults `__all__` and accesses
each listed name — so a name in `__all__` that only resolves through a DRF-guarded
`__getattr__` would make `from django_strawberry_framework import *` **raise `ImportError`
for a DRF-absent consumer who never touches serializers** (verified: Python binds every
`__all__` name via `__getattr__`, and the root has no lazy-`__all__` precedent today — all
current `__all__` names are eagerly bound). That is a breaking regression against the very
soft-dep promise ("a consumer who never writes a serializer mutation never needs DRF"), so
`SerializerMutation` stays **out of `__all__`**: the **named** import
(`from django_strawberry_framework import SerializerMutation`) still works through the root
`__getattr__` — named imports do not consult `__all__` — and `SerializerMutation` is
documented as a public lazy export in the GLOSSARY. (If DRF ever becomes a hard dependency,
it joins `__all__` then; until then, star-import membership is the one thing that would
re-break the soft-dep contract.)

**The root `__getattr__` does not memoize.** It must **not** bind the resolved
`SerializerMutation` into the root module's globals (no
`globals()["SerializerMutation"] = …` caching) — each `from
django_strawberry_framework import SerializerMutation` re-runs `__getattr__`, so the
`require_drf()` guard re-fires on every access. This is both a correctness choice (the
symbol is read at schema-build time and the field factory holds its own reference, so
re-resolution is cheap and there is no hot path to optimize) and a **test-isolation**
choice: a memoized root attribute would be a *third* cache — beyond `rest_framework*`
and `django_strawberry_framework.rest_framework*` — that an earlier DRF-present import
could leave bound, so the absent-path test would pass on the stale root attribute even
with the submodules evicted. The absent-DRF test therefore also **deletes the root
`SerializerMutation` attribute (and/or reloads the root package)** before forcing the
failure (below).

The coverage tension is the spec's load-bearing constraint: the package gates **100%
coverage** (`fail_under = 100`, `source = ["django_strawberry_framework"]`), and the
card mandates package tests **and** a live `ModelSerializer` test — both of which need
DRF *present* to exercise the `rest_framework/` code, while the DRF-absent guard path
needs DRF *absent* to cover its raise. The resolution (the [`spec-037`][spec-037]
`pillow` precedent — `pillow` is the `ImageField` soft dep, kept out of runtime deps
but added to the dev group so the suite covers the image path):

1. **DRF stays out of `[project].dependencies`** — it remains a soft runtime dep. A
   consumer who never writes a serializer mutation never needs DRF.
2. **`djangorestframework` is added to `[dependency-groups].dev`** in the
   **pre-Slice-1 dependency gate (Slice 0), not Slice 4** — because the Slice 1–3
   package tests and the live products surface all import DRF, the dev-dep and its verified
   floor must exist *before* Slice 1 code lands, or Slice 1 is blocked late by dependency
   support rather than design. The test environment then has it; the suite exercises every
   `rest_framework/` branch and the live products serializer surface, meeting
   `fail_under = 100`. **The dev-group floor must clear the CI matrix under `-W error`:**
   [`django.yml`][django-workflow] runs Django 5.2.0 → 6.0.\* → `latest` on Python
   3.10 → 3.14 and [`pytest.ini`][pytest-ini] sets `filterwarnings = error`, so the pinned
   DRF release must **import and run warning-free** on (Python 3.14, Django 6.0 / `latest`)
   — DRF's Django support lags Django releases, so confirm such a release exists before
   pinning, and add any **targeted DRF-origin `ignore::` line** (sanctioned by
   [`pytest.ini`][pytest-ini]'s own third-party comment) **in the same gate**, before code
   imports DRF in tests. This is a pre-Slice-1 floor check, not an implementation-time
   discovery. **The verified floor is `djangorestframework>=3.17.0`** — the first release
   adding Django 6.0 + Python 3.14 support (released 2026-03-18; resolves to 3.17.1),
   proven to import warning-free under `-W error` across all 9
   [`django.yml`][django-workflow] matrix cells (Python 3.10 → 3.14 × Django 5.2 → 6.0 /
   `latest`) with **no** `ignore::` line needed. That floor is one of the **three places
   that must agree**: the `[dependency-groups].dev` `djangorestframework>=<floor>` pin in
   [`pyproject.toml`][pyproject], the `require_drf()` guard's install hint, and this
   Decision.
3. **The DRF-absent import-guard path is covered by simulated absence** — a package test
   forces the `ImportError` branch through the importlib-native **`sys.modules["rest_framework"]
   = None` sentinel** ([`tests/_soft_dependency.py`][test-soft-dependency]`::simulated_absence`,
   the shared helper every soft-dependency suite uses), never by monkeypatching
   `builtins.__import__`: the guards go through `importlib.import_module`, which consults
   `sys.modules` directly and never calls `__import__`, so an `__import__` patch leaves the
   guard unreached and the test passes without exercising anything. The test asserts the
   install-hint message on **all three** raising entry points (the root `__getattr__("SerializerMutation")`, an
   `import …rest_framework`, and an `…rest_framework.sets` import), while
   `import django_strawberry_framework` itself still succeeds — DRF is actually
   installed in the test env, so this is the only way to cover **both** branches at
   100%. The test must **evict the module caches for both `rest_framework*` AND
   `django_strawberry_framework.rest_framework*`** (`sys.modules` pop / `importlib`
   reload) **and delete the root `django_strawberry_framework.SerializerMutation`
   attribute** (or reload the root package) before forcing the failure — otherwise an
   earlier import in the same test process leaves the submodules cached *or* the root
   symbol bound and **masks** the missing-dependency path (it would pass on a stale
   import, defeating the test). The root `__getattr__` not memoizing the class (above)
   means the root attribute only exists if a test bound it, so the eviction is a clean
   reset. The root-import half additionally runs in a **fresh subprocess**, which is
   strictly stronger than an in-process re-import: it can catch a newly-introduced eager
   `rest_framework` import at the package root, which a re-import inside an already-warm
   process cannot.
4. **The example assumes the dev group** (DRF, like `pillow` / `faker`, is a
   dev / test artifact) — the products schema wires the serializer mutation
   unconditionally and the example settings add `"rest_framework"` to `INSTALLED_APPS`
   only if a serializer needs the app registry (most flat `ModelSerializer`s do not).

Rationale companion — this Decision's justification and its three rejected alternatives:
[Decision 12][rationale-d12].

### Decision 13 — Live coverage: products grows a `ModelSerializer` mutation

Products gains a [`serializers.py`][products-serializers] with an `ItemSerializer`
(`serializers.ModelSerializer` over `Item`, with a `validate_<field>` /
`validate()`), and [`products/schema.py`][products-schema] gains a
`SerializerMutation` create + update over `Item`; `config/schema.py` already wires
`mutation=Mutation`. **This surface lands in the SAME slice (Slice 3) as
[`rest_framework/resolvers.py`][rf-resolvers]** — not a later slice — because the
[`examples/fakeshop/test_query/README.md`][test-query-readme] #"Coverage rule." /
[`docs/TREE.md`][tree] #"Coverage priority." mandate is absolute: a
`django_strawberry_framework/` line reachable by a real fakeshop `/graphql/` request
**must** be earned in [`test_products_api.py`][test-products-api], and earned *at the
commit the line appears*. Shipping the resolver in one slice and the live tests in the
next would leave the resolver's reachable lines covered by package tests at the resolver
commit — the exact inversion the rule forbids. So [`test_products_api.py`][test-products-api]
(seeded via `seed_data` / `create_users`) is the **primary** harness and proves, live,
**every consumer-reachable resolver branch**: create / update happy paths; `categoryId`
reverse-map validate-and-write through the serializer's `category`
`PrimaryKeyRelatedField`; partial-update preservation (a `name`-only update preserves
`category` / `description` via `partial=True`, and a `UniqueTogetherValidator` /
`unique_item_per_category` fires on a one-field change — the fire is DRF's
`UniqueTogetherValidator` backfilling the unchanged `category` from `serializer.instance`,
a **DRF behavior, not a package one**, pinned to the verified DRF floor
([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy))); the `serializer.errors`
envelope (`validate_<field>` keyed to its field; a cross-field `validate()` error keyed
to `"__all__"`); write authorization; the visibility-scoped `update`; the
hidden-`Category` relation-visibility `FieldError` and **authorize-before-decode**; the
**multipart `Upload` → [`Item.attachment`][products-models]** write (real
`django.test.Client` multipart, the [`test_uploads_api.py`][test-uploads-api]
precedent); the **request-context** `validate()` path (proving the injected
`context={"request": …}` lands); and the **G2 re-fetch query shape**. The
package-internal [`tests/rest_framework/test_resolvers.py`][test-rest-framework] keeps
**only** the residue a live query cannot drive
([Test plan](#test-plan)).

Rationale companion — this Decision's justification and its three rejected alternatives:
[Decision 13][rationale-d13].

### Decision 14 — Version bumps are owned by the joint `0.0.13` cut

No slice in this card edits the **package-version state**: `[project].version` in
[`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init], or
[`tests/base/test_init.py::test_version`][test-base-init]. This card **shares the
`0.0.13` patch line** with [`DONE-040-0.0.13`][kanban]
([Auth mutations][glossary-auth-mutations]); the version bump from `0.0.12` to `0.0.13`
is owned by the **joint `0.0.13` cut**, not by either individual card — the same posture
[`spec-036`][spec-036] Decision 13 took for the joint `0.0.11` cut it shared with
[`spec-037`][spec-037]. **Release-status wording is split from implementation
docs:** Slice 4 updates **implemented-on-main** docs ([`docs/TREE.md`][tree],
[`TODAY.md`][today], and the [`docs/GLOSSARY.md`][glossary] body to the implemented
contract) but the **public "shipped (0.0.13)" status, the README "Shipped today" prose,
and the release changelog defer to the joint cut** — otherwise the repo would advertise a
released `0.0.13` feature while `[project].version` / `__version__` / `test_version` still
report `0.0.12`. The version line and the version files stay at `0.0.12` until the joint
cut. (The [`GOAL.md`][goal] crit-6 example correction lands in this card regardless — the
current example is wrong the moment the code lands.)

**`uv.lock` is NOT a version file — it is updated in this card, deliberately.** The
repository commits a `uv.lock` (verified, `git`-tracked), and the **pre-Slice-1 dependency
gate (Slice 0)** adds `djangorestframework` to `[dependency-groups].dev`
([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
Changing a dev dependency **without** regenerating the lockfile leaves the declared and
locked environments out of sync, so the clean cut is to **edit `pyproject.toml` and
regenerate `uv.lock` together** in that gate (`uv lock` after the dev-group add) — before
Slice 1 imports DRF in tests. The distinction the version policy must keep is: the **DRF
dependency entries** in `uv.lock` *do* change here; the **package's own version** —
`[project].version` *and* the `[[package]] name = "django-strawberry-framework"` `version`
entry inside `uv.lock` — stays `0.0.12` until the joint cut.

Rationale companion — this Decision's justification and its one rejected alternative:
[Decision 14][rationale-d14].

## Cross-flavor reuse and DRY obligations

The spec is **already reuse-first by design** — it routes the resolver pipeline through
the `036` promoted helpers by call, reuses the `038`-generalized
[`DjangoMutationField`][glossary-djangomutationfield], and builds inputs through
[`utils/inputs.py`][utils-inputs]'s `build_strawberry_input_class` /
`materialize_generated_input_class`. That reuse is good and is not re-litigated here.

The residual DRY risk is narrower and concrete: a **handful of places where
[`forms/`][forms-sets] ALREADY re-implemented a [`mutations/`][mutations-sets] helper
rather than sharing it** — so the serializer flavor is on track to be the **third**
divergent copy. The package's own source carries the receipts: [`forms/sets.py`][forms-sets]
comments its shape cache a *"twin of"* `mutations/sets.py::_shape_build_cache`,
the form flavor's object-returning relation decoder exists because the
`036` `_relation_visibility_error` *"does not return"* the object, and
[`registry.py`][registry]'s clear block documents a *"same two-block shape"* mirrored per
flavor. Each is a chance to **promote to a shared site now**, while the second consumer
([`forms/`][forms-sets]) and the third ([`rest_framework/`][rf-sets]) are both in view —
the cheapest moment to single-site. The promotion targets below are the spec's binding
implementation obligations; each is pinned into its Decision and its Slice DoD line, and
the per-module import manifest at the end is the DoD-checkable "DRY contract."

Reuse claims here were verified against the source first; corrections to the originating
review are folded in (field-sequence normalization has one home,
`utils/inputs.py::normalize_field_name_sequence(..., flavor=…)`, which every flavor calls
directly; the leaf-error constructor
`utils/errors.py::field_error(path, messages, *, codes=None)` is the shared base case both
flatteners call, alongside the `mutations/inputs.py::NON_FIELD_ERROR_KEY` sentinel;
`forms/sets.py::_form_kwargs_overridden` already exists as the helper the narrow
constructor-hook item below generalizes; and no `register_subsystem_clear` seam exists
today — both clear lists the registration-seam promotion replaces are hand-maintained,
confirmed).

### Confirmed reuse — lock as import obligations

These the spec already states in prose. A prose "reuses the `036` helper" does not stop an
implementer quietly re-spelling it, so each becomes a Slice DoD line of the form
**"imported from `<module>`, not re-implemented"** (ideally backed by a one-line import /
identity guard that the symbol is imported and not redefined under `rest_framework/`):

- **By call from [`mutations/resolvers.py`][mutations-resolvers]** (Decision 8):
  `run_write_pipeline_sync` and `make_resolver_entries`. The `036` locate / authorize /
  re-fetch / payload helpers (`locate_instance`, `coerce_lookup_id`, `authorize_or_raise`,
  `refetch_optimized`, `build_payload`, `not_found_error`, `payload_cls_for`,
  `run_pipeline_async`) are reached **through** that skeleton rather than called directly —
  which is the point of the promoted skeleton: the serializer flavor cannot re-order the security
  preamble because it does not own it.
- **By call from [`utils/`][utils-permissions]:**
  `utils/permissions.py::request_from_info(info, family_label="SerializerMutation")`
  (already accepts a family label — no edit); `utils/inputs.py::build_strawberry_input_class`
  (materialization goes through the promoted one-ledger namespace trio, not
  `materialize_generated_input_class` directly); the `utils/write_values.py` decode
  primitives, including `raw_choice_value`, `coerce_relation_pk_or_none`, and
  `type_check_relation_id`; and the `utils/errors.py` leaf constructors.
- **Conceptual contracts reused:** the [`FieldError`][glossary-fielderror-envelope]
  envelope + the `mutations/inputs.py::NON_FIELD_ERROR_KEY` (`"__all__"`) sentinel, the
  `<Name>Payload` `node` / `result` slot (`payload_object_slot` / `build_payload_type`),
  the `_resolve_model` / `_validate_meta` / `build_input` / `input_type_name` /
  `input_module_path` / `resolve_sync` / `resolve_async` seams, `bind_mutations()`, and the
  [`DjangoModelPermission`][glossary-djangomodelpermission] write-auth seam.
- **The `038`-generalized field factory:**
  [`mutations/fields.py`][mutations-fields]'s [`DjangoMutationField`][glossary-djangomutationfield]
  is duck-typed (`_has_mutation_protocol`), so the serializer base passes with **no factory
  edit** (Decision 5).
- **No bespoke declaration registry / factory call.** `mutations/sets.py::make_declaration_registry`
  is a **shared factory** the model path itself instantiates (the model-less plain
  `DjangoFormMutation` instantiates the same factory over a second disjoint store), and a
  `DjangoMutation`-subclass serializer rides `register_mutation` / `bind_mutations()` — so
  there is **no** `register_serializer_mutation` / `bind_serializer_mutations` to add
  (Decision 6). A plain model-less serializer flavor (the only case that would want its own
  store) is out of scope.

### Promotions to single-site now (third-copy forks)

| Promotion | Duplicated today (`mutations/` ↔ `forms/`) | Promote to | Serializer obligation | Pin |
| --- | --- | --- | --- | --- |
| **Relation-decode core** | The model flavor's id-set decoder and its four error helpers in [`mutations/resolvers.py`][mutations-resolvers] return *errors*; [`forms/resolvers.py`][forms-resolvers] rolled its own object-returning, field-keyed one-id decoder plus `_decode_form_relation_single` / `_decode_form_relation_multi` because the `036` helper *"does not return"* the object | `visible_related_object(related_model, pk, info) -> obj \| None` (plus the batched `visible_related_objects(related_model, pks, info)`) to [`utils/querysets.py`][utils-querysets] (beside `visibility_scoped_related_queryset`, whose composition it already uses); better, the whole one-id *decode-or-coerce → visible-object → no-leak `FieldError`* shape into a shared core taking a small per-flavor descriptor | Re-key the serializer relation decoder over the promoted `visible_related_object` / `visible_related_objects`; do **not** re-implement the visibility / membership check (third copy avoided). The serializer is **stricter on the no-primary-type case** — it guards at class creation (a relation target with no registered primary `DjangoType` is a `ConfigurationError`), so it never reaches the helper's default-manager fallback; that fallback stays the **form flavor's** behavior, **byte-unchanged** (the stricter path is a class-creation guard, not a change to the shared helper) | [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) + [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload) + Slice 3 resolver checklist |
| **Non-delete operation set** | The form flavor's private `{"create", "update"}` operation set is byte-identical to the serializer need; `mutations/operations.py::_VALID_OPERATIONS` is the `{create, update, delete}` superset | A single `NON_DELETE_WRITE_OPERATIONS` constant plus its reject message, sited in a net-new `mutations/operations.py` and reached from both flavors through `mutations/sets.py::require_non_delete_operation` | Call the shared `require_non_delete_operation`; do **not** define a `_VALID_SERIALIZER_OPERATIONS`; the "no serializer/form delete" message single-sites too | [Decision 10](#decision-10--operations-create--update-no-serializer-delete) + Slice 2 `_validate_meta` |
| **Shape-build cache** | Per-declaration, twice: `mutations/sets.py::_shape_build_cache` and `forms/sets.py::_form_shape_build_cache` (commented *"twin of"*) + `clear_form_shape_build_cache` | A `make_shape_build_cache()` helper returning the module-level dict + a registered `clear()` wired into the finalizer's pre-bind reset | The `SerializerInputShape` descriptor identity stays legitimately new; only the cache **+ clear plumbing** is shared — do not hand-mirror a third dict + clear | [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) + Slice 2 finalizer-reset checklist |
| **Converter dispatch skeleton** | [`forms/converter.py`][forms-converter]'s `convert_form_field` (isinstance pre-checks → `type(field).__mro__` walk over `_SCALAR_FORM_FIELDS` → exact-base-`Field` case → raising `ConfigurationError` fallthrough) imports **nothing** from `utils/` — a free-standing skeleton | A shared dispatch skeleton — `(field, isinstance_prechecks, scalar_registry, fallthrough_error_factory) → conversion` — to a new `utils/converters.py`; the unified conversion / field-spec dataclass rides with it | `convert_serializer_field` supplies only its precheck table + scalar registry; the **GOAL-mandated fail-loud contract** (no silent `String` catch-all) is single-sited and cannot drift between the two converters | [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) (converter) + [Decision 4](#decision-4--module-and-test-locations-rest_framework-subpackage-mirroring-forms) (skeleton home) + Slice 1 |
| **Sync write-pipeline skeleton** | The **sync write-pipeline orchestration**: `mutations/resolvers.py::_run_pipeline_sync` → `_run_create` / `_run_update` (one `transaction.atomic()`; tail partly factored as `_validate_save_assign_refetch_payload`) is re-spelled by the form flavor's own model-backed sync pipeline in [`forms/resolvers.py`][forms-resolvers] — each re-writing the atomic block + the `coerce_lookup_id → locate_instance → not_found_error` preamble + the **authorize-before-decode** ordering | `run_write_pipeline_sync(...)` to [`mutations/resolvers.py`][mutations-resolvers] — owning atomicity, the create-vs-update branch, the locate→authorize preamble, **authorization before `decode_step`**, and the `refetch_optimized → build_payload` tail, with a `tail_step` seam for delete's snapshot payload and a no-primary-type `{ ok: true }` tail for the model-less plain form, so **every** flavor rides it | The serializer supplies only `decode_step(ctx) -> decoded \| list[FieldError]` and `write_step(ctx, decoded) -> saved \| list[FieldError]` (construct / `is_valid()` / `save()`); it does **not** re-spell the atomic block or the **authorize-before-decode security ordering** — the audit's single highest-value promotion (a security invariant, not just a shape). The existing model + model-form behavior must stay **byte-equivalent under their current tests** before serializer code lands | [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload) + Slice 3 resolver checklist |
| **Subsystem-clear registration seam** | Two hand-maintained ledger-clear lists with no registration seam: the [`finalize_django_types`][types-finalizer] pre-bind reset (direct, unconditional `clear_mutation_input_namespace()` + `clear_form_input_namespace()` before `bind_mutations()`) **and** `registry.py::TypeRegistry.clear()`'s `_clear_if_importable` co-clear rows (incl. the form shape cache; the block's own comment notes a *"same two-block shape"* mirrored per flavor) | A `register_subsystem_clear(clear, *, owner, before_bind=False)` seam feeding **one** canonical registry that **both** the finalizer pre-bind reset and `registry.clear()` iterate | The serializer's `clear_serializer_input_namespace` is registered as a **zero-argument callable with a stable `owner`**, `before_bind=True`, from the module that owns the ledger (a string reference is rejected) instead of being hand-added to both lists — and because only an imported owner can register, the soft-dep import-guarded **asymmetry vanishes**, collapsing the spec's whole Decision-6 / Slice-2 "import-guarded clear" caveat to a one-line registration, while a rename now fails loudly at the owner's own import. Invariant: a subsystem with clearable state has by definition been imported + registered | [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven) + Slice 2 finalizer-reset checklist |
| **Build / stash / name seam** | The `build_input` **implementation cluster**: the model does it inline (`DjangoMutation.build_input` → `_materialize_input_for`; `input_type_name`); [`forms/sets.py`][forms-sets] grew a private mirror — `_cached_build_form_input` (per-shape dedupe + the load-bearing **guard-before-cache-lookup** ordering), `_build_and_stash_form_input` (materialize-then-stash `_input_field_specs`), `_form_input_type_name_for`, `_modelform_operation_kind` | `cached_build_input(shape_key, *, guard, build_fn) -> (input_cls, field_specs)` (owns the per-pass lookup + the **guard-before-lookup** ordering) + `build_and_stash_input(cls, *, build, materialize)` to [`mutations/sets.py`][mutations-sets] (or a new `mutations/bind_helpers.py`) | The serializer supplies only its generator, materialize fn, and shape descriptor, and rides `build_and_stash_input` (materialize-then-stash) — NOT a byte-parallel `_build_and_stash_serializer_input`. It does **not** ride `cached_build_input`: that helper looks its key up BEFORE building, but the serializer's key is the `SerializerInputShape` descriptor, only knowable AFTER the build, so forcing it through the helper would build the shape twice (the waste this promotion exists to avoid). The descriptor-keyed dedupe therefore stays an inline lookup-or-store keyed on the post-build descriptor, while the per-declaration guard-before-dedupe ordering is preserved directly. (Layering: the shape-build cache is the cache *dict*, the unified field spec is the spec *shape*, and this row is the build *procedure* — promoting the stash core + the shape/cache plumbing is what stops `rest_framework/sets.py` being a line-for-line `forms/sets.py`) | [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven) / [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) + Slice 2 `sets.py` checklist |

### Single-siting that prevents drift

- **Unify the field-spec / conversion types.** `utils/inputs.py::GeneratedInputFieldSpec`
  (`@dataclass`), the form flavor's own field-spec dataclass in
  [`forms/converter.py`][forms-converter] + its `FormFieldConversion` (a `__slots__` class,
  **not** a dataclass), and the planned serializer reverse-map are the same idea with flavor-specific extra axes (the serializer's
  is "the `038` `FormInputFieldSpec` analog **plus the `source` axis**"). Define **one**
  generic `InputFieldSpec` in [`utils/inputs.py`][utils-inputs] (shared core +
  optional `source`), or subclass `FormInputFieldSpec`; at minimum **site the serializer
  spec in `utils/inputs.py`** so all three live in one module. Unify the conversion result
  (`annotation` + `kind` + `required`) into one shared shape too. ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth).)
- **The input-namespace clear is a third one-ledger lifecycle.** The four-part
  per-flavor lifecycle (module-path const + `_materialized_names` ledger +
  `materialize_*_input_class` wrapper + `clear_*_input_namespace`) is hand-mirrored across
  [`mutations/inputs.py`][mutations-inputs] and [`forms/inputs.py`][forms-inputs]. Promote
  `make_input_namespace(module_path, family_label) -> (ledger, materialize_fn, clear_fn)` to
  [`utils/inputs.py`][utils-inputs]. **The serializer clear is the one-ledger
  `_materialized_names.clear()` (the form / mutation shape), NOT the heavier
  `utils/inputs.py::clear_generated_input_namespace`** (which also resets factory caches +
  per-subclass binding state the filter / order families have and the
  mutation / form / serializer flavors do not) — state this so an implementer does not reach
  for the wrong helper. ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) / Slice 2.)
- **Reuse the one PascalCase token encoder.** The descriptor-derived names for
  narrowed / divergent shapes reuse the injective single-token encoder
  `utils/inputs.py::pascalize_token` (`mutations/inputs.py::_pascalize_token` survives only
  as a backward-compatible alias to it), not a third suffix encoder; the canonical `<Serializer>Input` / `<Serializer>PartialInput` names need no
  helper. ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth).)
- **Share the error-flattener leaf primitive.** `serializer_errors_to_field_errors`
  is legitimately new (recursive — the flat `036`
  `utils/errors.py::validation_error_to_field_errors` cannot walk DRF's nested tree).
  But its **base case** — construct a `FieldError(field=<path>, messages=[...])` and map
  DRF's `non_field_errors` bucket to the package's `"__all__"` sentinel — is the convention
  the `036` mapper already encodes (`NON_FIELD_ERRORS` → `mutations/inputs.py::NON_FIELD_ERROR_KEY`).
  The hard reuses are the shared `NON_FIELD_ERROR_KEY` (no re-spelling `"__all__"`) and
  the shared leaf constructor `utils/errors.py::field_error(path, messages, *, codes=None)`,
  which **both** the flat and recursive flatteners call so the sentinel convention — and the
  `codes` and `path` derivation — cannot drift. That module is the single home for the
  whole leaf-error substrate: `field_error`,
  `validation_error_to_field_errors`, `integrity_error_field_errors`,
  `relation_field_error`, `null_field_error`, and `join_error_path`.
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload) step 5.)
- **`_validate_meta` reuses the base sub-validators.** Call
  `mutations/sets.py::_validate_permission_classes`, the non-delete ops check against the
  shared non-delete operation set, and the field-sequence normalize, then return a
  `_ValidatedMutationMeta` — do not re-spell the typo-guard / mutual-exclusion logic. All
  three flavors normalize their field sequence through the one
  `utils/inputs.py::normalize_field_name_sequence(..., flavor=…)` entry point; there is no
  per-flavor re-binding wrapper to follow (see the typo-guard item below). The serializer's genuinely-new
  validation is the `serializer_class` is-a-`ModelSerializer` (+ resolvable `Meta.model`)
  check plus the `optional_fields` / `injected_fields` / `select_for_update` /
  `nested_fields` / schema-field-map / fingerprint / writable-`source` work
  [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)
  enumerates. ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven) / Slice 2.)
- **Keep constructor-hook ownership narrow.** The `get_serializer_kwargs` default
  body parallels `forms/sets.py::_default_get_form_kwargs`, but the serializer hook does
  not participate in required-field guard decisions. The
  serializer flavor ships **only** the finer `get_serializer_kwargs` hook — it has **no**
  coarse `get_serializer` constructor hook (unlike the form flavor's `get_form`): its
  framework-owned invariants (`partial` and the authorized-actor `context["request"]`) are
  framework-owned in `_merged_serializer_kwargs` and cannot be entrusted to a
  consumer-overridable constructor (a `get_serializer()` override could subvert them),
  so the default body sets **neither** `partial` **nor** `context`
  the hook is not the place for them. Required-field injection is instead
  explicit through `Meta.injected_fields` + `get_serializer_injected_data`.
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload).)
- **Promote the `Meta` typo-guard, do not add a third normalize wrapper.** Every
  `_validate_meta` computes `unknown = sorted(declared - _ALLOWED_<FLAVOR>_META_KEYS)` and
  raises (`mutations/sets.py::_ALLOWED_MUTATION_META_KEYS`, and both form bases). Promote
  `reject_unknown_meta_keys(name, meta, allowed)` to [`mutations/sets.py`][mutations-sets],
  called by every `_validate_meta` with its own frozenset (the serializer's
  `_ALLOWED_SERIALIZER_META_KEYS` is `MODEL_BACKED_WRITE_META_KEYS` **plus**
  `serializer_class` / `optional_fields` / `injected_fields` / `nested_fields`, and
  **drops** `model` / `input_class` / `partial_input_class`). And the serializer calls
  `utils/inputs.py::normalize_field_name_sequence(..., flavor="SerializerMutation")`
  **directly** (the required keyword-only `flavor` arg exists for exactly this) rather than
  add a per-flavor re-binding wrapper of any kind; there is exactly one normalizer. ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven) / Slice 2; companion to the `_validate_meta` sub-validator item above.)

### Small reuses to pin; deliberately not applicable

Pin as named import obligations (Slice DoD lines): `utils/strings.py::graphql_camel_name`
(the `categoryId` alias naming — do not hand-roll camel-casing) and its sibling
`utils/strings.py::pascal_case`; `utils/inputs.py::normalize_field_name_sequence(flavor="SerializerMutation")`;
`utils/permissions.py::request_from_info(family_label="SerializerMutation")`;
`mutations/inputs.py::{annotate_queryset_relation, model_column_write_annotation,
model_column_write_kind}` (the **backing** model-relation read the converter does via
`source`, not re-derived from DRF's `many` / `source` flags) plus
`utils/relations.py::is_forward_many_to_many` on the resolver's attestation path; the
`utils/querysets.py::{model_for, initial_queryset, apply_type_visibility_sync,
apply_type_visibility_async, visibility_scoped_related_queryset, reject_async_in_sync_context}`
locate + relation-visibility + async-guard substrate (a re-spell here is a data-leak risk,
not just a DRY nit); and the read-side
[`types/converters.py`][types-converters]`::{convert_scalar, scalar_for_field,
build_enum_from_choices}` keyed on the backing `models.Field` via `source` — the enum core
the read side and the serializer converter share (Decision 7).

**Deliberately NOT applicable** — stated so a future reader does not hunt for a phantom
reuse:

- **`utils/connections.py`** (`derive_connection_window_bounds`,
  `CONNECTION_SIDECAR_KWARGS`, …) — read-side pagination windowing. The serializer
  payload's `node` is a single re-fetched object, not a connection.
- **`utils/input_values.py`** (`iter_active_fields`, `SetInputTraversal`, `ActiveField`, …)
  and the active-input permission walkers in [`utils/permissions.py`][utils-permissions]
  (`active_permission_field_paths`, `run_active_input_permission_checks`, …) — the
  FilterSet / OrderSet set-input traversal substrate. The serializer write path has no
  set-input dataclass traversal and no per-field `check_<field>_permission` walk (its
  authorization is the inherited [`DjangoModelPermission`][glossary-djangomodelpermission]
  row gate). `request_from_info` is the **only** member of `utils/permissions.py` the
  serializer flavor consumes.
- **`utils/typing.py`** — `is_async_callable` is unneeded (async dispatch is owned by
  [`DjangoMutationField`][glossary-djangomutationfield]'s `in_async_context()` check, not
  the serializer base); `unwrap_return_type` / `unwrap_graphql_type` apply only to a
  consumer `input_class` override, which is out of scope for `0.0.13`
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).
- **`utils/strings.py::snake_case`** — an optimizer-walk helper, not a serializer-input
  reuse; do not conflate it with `graphql_camel_name`, which lives in the same module and
  **is** the GraphQL↔Django input-name boundary the serializer flavor imports (as does
  `pascal_case`, above).

### Import manifest — the DRY contract per `rest_framework/` module

The DoD-checkable summary, stated at **module** granularity: each `rest_framework/` module
may import from exactly the packages listed for it, and re-implementing anything those
packages own is a finding. Module granularity is deliberate — a per-symbol allow-list goes
stale on every legitimate DRY-driven symbol move *inside* a permitted module, which makes
the manifest a maintenance tax on unrelated cards without catching anything a module list
misses. The per-symbol obligation that genuinely needs a ratchet is the shared substrate
the Slice-1 DRY bullet enumerates, and that one is executable
([`tests/rest_framework/test_dry_import_ratchet.py`][test-dry-ratchet]) rather than prose.

| `rest_framework/` module | May import from | The substrate it must not re-implement |
| --- | --- | --- |
| [`serializer_converter.py`][rf-converter] | `exceptions`, `registry`, `scalars`, `mutations/inputs.py`, `types/converters.py`, `utils/converters.py`, `utils/inputs.py`, `utils/strings.py` | the shared fail-loud dispatch skeleton, the shared conversion base + field spec, the four input-kind constants, the read-side scalar / enum core (`convert_scalar`, `scalar_for_field`, `build_enum_from_choices`), the model-column relation classifiers (`model_column_write_kind`, `model_column_write_annotation`, `annotate_queryset_relation`), the [`Upload`][glossary-upload-scalar] scalar, `graphql_camel_name` / `pascal_case`, the `register_subsystem_clear` seam |
| [`inputs.py`][rf-inputs] | `exceptions`, `registry`, `mutations/inputs.py`, `utils/inputs.py`, `utils/strings.py`, `.serializer_converter` | the input-namespace one-ledger trio, the shape-build cache pair, `build_strawberry_input_class`, `generated_input_type_name`, `guard_dropped_required`, `iter_input_field_collisions`, `optional_input_field`, `resolve_effective_fields`, `normalize_field_name_sequence`, `pascalize_token`, `InputFieldSpec`, `graphql_camel_name`, the `CREATE` / `PARTIAL` kinds, the `register_subsystem_clear` seam |
| [`sets.py`][rf-sets] | `exceptions`, `mutations/inputs.py`, `mutations/sets.py`, `utils/inputs.py`, `.inputs`, `.serializer_converter` | `DjangoMutation`, `_ValidatedMutationMeta`, `_validate_permission_classes`, `reject_unknown_meta_keys`, `MODEL_BACKED_WRITE_META_KEYS`, `NON_DELETE_OPERATION_INPUT_KIND` + `require_non_delete_operation`, `build_and_stash_input`, `construction_kwargs`, `normalize_meta_field_selection`, `require_backing_class` / `require_model_class` / `require_subclass`, `resolve_backed_model_or_raise` / `resolve_meta_model`, `resolver_seams`, `validate_select_for_update`, `normalize_field_name_sequence` |
| [`resolvers.py`][rf-resolvers] | `exceptions`, `mutations/inputs.py`, `mutations/resolvers.py`, `utils/errors.py`, `utils/inputs.py`, `utils/permissions.py`, `utils/querysets.py`, `utils/relations.py`, `utils/write_transaction.py`, `utils/write_values.py`, `.hook_context`, `.inputs`, `.serializer_converter` | the promoted sync-pipeline skeleton `run_write_pipeline_sync` + `make_resolver_entries`, the shared decode primitives in `utils/write_values.py` — `decode_visible_relation`, `decode_visible_relation_ids`, `decode_provided_fields`, `decode_field_handlers`, `decoded_into` — the shared leaf-error constructors in `utils/errors.py`, the `NON_FIELD_ERROR_KEY` sentinel and `FieldError`, the write-transaction substrate (`require_write_pipeline`, `pipeline_write_phase`, `pin_write_queryset`, `base_locked_queryset`, `assert_no_target_drift`, `pks_match`, `make_cross_alias_save_guard`), `related_visibility_queryset`, `request_from_info` |
| [`__init__.py`][rf-init] | `utils/imports.py` | the shared `require_optional_module` core behind `require_drf()` (Decision 12) |
| [`hook_context.py`][rf-hook-context] | nothing | — (two frozen dataclasses, no framework dependency) |

**Cross-module (not `rest_framework/`):** the subsystem-clear registration seam touches
[`types/finalizer.py`][types-finalizer]
(the pre-bind reset block) and [`registry.py`][registry] (the `TypeRegistry.clear()`
co-clear block) — `clear_serializer_input_namespace` **must** register through the
**mandatory** `register_subsystem_clear` seam rather than be hand-added to both
lists.


## Implementation plan

A **pre-Slice-1 dependency gate** plus four slices. Slices 1–2 are package-internal and
staged; **Slice 3 lands the resolver pipeline AND the products live serializer surface in
one commit** (so reachable resolver lines are earned live, not by package tests — the
[`test_query/README.md`][test-query-readme] #"Coverage rule."); Slice 4 is doc +
card-wrap only — **the DRF dev-dependency wiring moves to the gate, not Slice 4**
(Slices 1–3 tests import DRF, so the dev-dep + verified floor must exist *before* Slice 1
code lands). Line deltas are planning estimates.

| Slice | Files touched | New / changed tests | Approx. delta |
| --- | --- | --- | --- |
| **0 — pre-Slice-1 dependency gate** | [`pyproject.toml`][pyproject] (`djangorestframework` → `[dependency-groups].dev`, NOT `[project].dependencies`) + `uv.lock` (`uv lock`), [`pytest.ini`][pytest-ini] (a **targeted DRF-origin `ignore::` line** only if the verified floor still emits a deprecation under the CI matrix). **No package-version edit** (stays `0.0.12`, [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)) | the gate is a **precondition**, not a test deliverable: confirm a DRF release imports + runs warning-free across the [`django.yml`][django-workflow] matrix (Python 3.10→3.14 × Django 5.2→6.0/`latest`) under `-W error`, and record the exact pinned floor before converter code | `+5 / 0` (manifest + lock) |
| 1 — serializer-field converter + reverse map + the two serializer-derived inputs | [`rest_framework/serializer_converter.py`][rf-converter] (new; `convert_serializer_field` fail-loud MRO dispatch + the nine-axis `utils/inputs.py::InputFieldSpec` reverse map, renamed-field `source` resolution + id-like-suffix rule), [`rest_framework/inputs.py`][rf-inputs] (new; `<Serializer>Input` + `<Serializer>PartialInput` from the `get_serializer_for_schema()` field set, `SerializerInputShape` descriptor identity, `guard_create_required_serializer_fields`, `read_only` / `optional_fields` handling, narrowing fail-loud), [`rest_framework/__init__.py`][rf-init] (new; DRF soft-import guard), **+ the DRY promotions** ([DRY obligations](#cross-flavor-reuse-and-dry-obligations)): `utils/converters.py` (new; shared dispatch skeleton) + [`utils/inputs.py`][utils-inputs] (`InputFieldSpec` / `make_input_namespace` / `make_shape_build_cache`) with [`forms/converter.py`][forms-converter] + [`forms/inputs.py`][forms-inputs] re-pointed | [`tests/rest_framework/test_converter.py`][test-rest-framework] + [`tests/rest_framework/test_inputs.py`][test-rest-framework] (~40 — every serializer-field class, id mapping, `Upload`, the reverse-map + `kind` flag, renamed-`source` + id-like-suffix + dotted-`source` raise, custom-field raise, schema-hook (kwargs-serializer reject + override), `read_only` dropped, `optional_fields` (+ `"__all__"` reject), descriptor identity (optional_fields / hook-vary → distinct names), create-required guard (explicit-injection subtraction, per-declaration), collision/dedupe, `Meta.fields`/`exclude` fail-loud + empty-set) | `+500 / 0` |
| 2 — the base class + `Meta` validation + the bind + the export guard | [`rest_framework/sets.py`][rf-sets] (new; `SerializerMutation` subclassing `DjangoMutation`, the `_validate_meta` / `_resolve_model` / `build_input` / `input_type_name` / `input_module_path` / `resolve_*` overrides), [`rest_framework/inputs.py`][rf-inputs] (`clear_serializer_input_namespace()`), the serializer input ledger is cleared from **both** the [`types/finalizer.py`][types-finalizer] pre-bind reset block (retry-idempotence — no new bind, rides `bind_mutations()`) and [`registry.py`][registry]'s `TypeRegistry.clear()`, but **via the mandatory `register_subsystem_clear` seam, not two hand-edits** — one canonical registry of `(zero-argument callable, owner)` rows that both sites iterate (so DRF is never imported while absent, and the soft-dep asymmetry / import-timing edge both vanish); [`__init__.py`][init] (guarded `SerializerMutation` export via root `__getattr__`), **+ the DRY promotions** ([DRY obligations](#cross-flavor-reuse-and-dry-obligations)): [`mutations/sets.py`][mutations-sets] (`NON_DELETE_WRITE_OPERATIONS` / `reject_unknown_meta_keys` / `cached_build_input` + `build_and_stash_input` / generalized `_hook_overridden`) with [`forms/sets.py`][forms-sets] re-pointed | [`tests/rest_framework/test_sets.py`][test-rest-framework] (~18 — `Meta` matrix incl. `delete`-rejected + plain-`Serializer`-rejected + no-model + `permission_classes` kept, both bind, retry-idempotence, no-primary error, model-flavor seam defaults unchanged) | `+340 / -10` |
| 3 — resolver pipeline **+ products live surface (one commit)** | [`rest_framework/resolvers.py`][rf-resolvers] (new; visibility-on-every-branch relation decoder + `partial=True` update + value-preserving save + sync/async pipeline reusing the `036`/`038` promoted helpers), [`examples/fakeshop/apps/products/serializers.py`][products-serializers] (new; `ItemSerializer` + the `Upload`/`Item.attachment` + request-context branches), [`products/schema.py`][products-schema] (serializer mutations), `config/settings.py` (`rest_framework` in `INSTALLED_APPS` if needed), [`mutations/resolvers.py`][mutations-resolvers] + [`utils/querysets.py`][utils-querysets] + [`forms/resolvers.py`][forms-resolvers] (the relation-decode and sync-pipeline promotions — `run_write_pipeline_sync` skeleton + `visible_related_object` promoted, `forms/` re-pointed; [DRY obligations](#cross-flavor-reuse-and-dry-obligations)) | **Primary: [`test_products_api.py`][test-products-api]** (~16 live `/graphql/` — create/update, field + `"__all__"` envelopes, `categoryId` reverse-map write, partial-update + unique-together, hidden update row, write-auth, hidden-relation `FieldError`, authorize-before-decode, multipart `Upload`, request-context, G2 query shape). **Internals-only: [`tests/rest_framework/test_resolvers.py`][test-rest-framework]** (~13 — recursive-flattener shapes, raw-pk/non-Relay + many-relation decode, call-once save, write-time `IntegrityError` + save-time `ValidationError`, sync/async + `SyncMisuseError`, hermetic kwargs seams) + [`tests/mutations/test_fields.py`][test-mutations] factory-generalization verification | `+560 / 0` |
| 4 — docs + card wrap (no version bump; dep wiring already done in the gate) | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`README.md`][readme], [`GOAL.md`][goal], [`TODAY.md`][today], [`docs/TREE.md`][tree], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban] — **implemented-on-main docs land now; the public "shipped (0.0.13)" / "Shipped today" / release-changelog wording defers to the joint cut** | 0 (doc only) | `+110 / -40` |

Total expected delta: ~`+1590 / -50` — an L cut, matching the card's relative size. The
resolver-helper reuse-by-call (the `036` helpers) and the
[`DjangoMutationField`][glossary-djangomutationfield] generalization reused unchanged are
the dividend of the `036` freeze + the `038` generalization. The
[Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations)
**promotions** are the one deliberate, contained exception to "near-zero edit to
`mutations/`": they touch `mutations/` / `utils/` / `forms/` / [`types/finalizer.py`][types-finalizer]
/ [`registry.py`][registry], but are **net-near-zero** — each *extracts* a shared helper,
*re-points* the existing [`forms/`][forms-sets] copy to it, and *deletes* that duplicate
body (the serializer would otherwise have written a third copy), the one genuinely-new
file being `utils/converters.py`. The above per-slice deltas fold these in; treat the
"no DRY promotion" figures as the floor. Staged-but-not-implemented seams follow the
[`AGENTS.md`][agents] design-doc anchor discipline (a source-site
`TODO(spec-039 Slice N)` comment naming this spec, removed in the slice that ships it).

## Edge cases and constraints

- **DRF not installed.** `import django_strawberry_framework` succeeds (the
  `SerializerMutation` export resolves lazily through the root `__getattr__`, never
  eagerly importing `rest_framework/`); `from django_strawberry_framework import
  SerializerMutation` or any `rest_framework/` import raises `ImportError` with an
  install hint via the shared `require_drf()` guard
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
- **Serializer-only fields (no model column).** A serializer field with no model
  column (a `confirm_password`, a write-only validation field) becomes an input field
  via the converter and is validated by the serializer; `serializer.save()` handles
  what reaches the model. This is why the input derives from the serializer, not the
  model.
- **Serializer-only RELATION fields.** A write-only `PrimaryKeyRelatedField` (or
  `many=True`) whose `queryset` is **not** a model column — consumed by a custom
  `create()` / `update()` — is both serializer-only and a relation. Its relation **target
  comes from `field.queryset.model`** (driving the id annotation and the decode-time
  visibility check), and the declared serializer field name is preserved in
  `provided_data`. A relation field with **neither** a resolvable backing column **nor** a
  concrete `queryset.model` is a class-creation
  [`ConfigurationError`][glossary-configurationerror]
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- **Relation target with no registered primary `DjangoType`.** A serializer relation
  field whose target model (from the backing FK or `field.queryset.model`) has **no
  registered primary [`DjangoType`][glossary-djangotype]** is a **class-creation**
  [`ConfigurationError`][glossary-configurationerror] naming the serializer field and the
  target model — **not** a silent runtime fallback to the model's default manager (which
  would write a hidden / unseeable row, breaking the visibility-scoped decode promise). This
  is stricter than the promoted `visible_related_object` helper's form fallback (which stays
  unchanged); the serializer opts in by guarding at class creation
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- **Renamed serializer fields (`source`).** A field declared as
  `category_pk = PrimaryKeyRelatedField(source="category", …)` or
  `full_name = CharField(source="name")` gets its GraphQL input name from the **declared
  field name** under the id-like-suffix rule (`category_pk` → `categoryPk`,
  `full_name` → `fullName`), its backing-column resolution from **`source`**, and its
  `provided_data` key preserved as the **declared name** (DRF maps it to `source`).
  Omitted and one-segment `source` are supported; a dotted `source` or
  `source="*"` on a model-column-converting field is a class-creation
  [`ConfigurationError`][glossary-configurationerror]
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- **Dynamic / kwargs-requiring serializers (schema-time).** The input shape is
  discovered at finalization via `get_serializer_for_schema()` (default: no-arg
  `serializer_class()`, then **`.fields` materialization** — the guarded step, since DRF
  builds `.fields` lazily and a context-requiring serializer fails at `.fields` access,
  not at construction). A serializer whose schema-time `.fields` cannot be materialized
  no-arg — because its `__init__` raises without kwargs, or its `get_fields()` derives the
  field set from request / tenant state — must override the hook to return a **stable,
  request-independent** field shape; one whose field set genuinely varies per request has
  no single GraphQL input and is rejected loudly. The runtime `get_serializer_kwargs(...)`
  hook is a separate seam and does not affect schema shape
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- **`get_serializer_kwargs` cannot swap the request actor.** A
  `get_serializer_kwargs(...)` override may add or replace NON-RESERVED constructor kwargs
  and merge its own `context` keys — `data`, `instance`, `partial`,
  `context["request"]`, and `context["write_alias"]` are framework-owned — and it
  **cannot change the request actor**: the framework sets
  `context["request"] = request_from_info(info, …)` after merging — the **same** object the
  inherited write-auth seam already authorized — so the serializer's request-aware
  validators see the same user / tenant the permission check saw. An override that supplies a
  **different** `context["request"]` is a [`ConfigurationError`][glossary-configurationerror]
  (it would let permission and validation disagree about the actor); the same object is
  tolerated. Consumer context belongs under other keys
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
  step 4).
- **`read_only` / `HiddenField` fields.** Dropped from the input (graphene's
  `fields_for_serializer` `is_input` rule); a `HiddenField(default=CurrentUserDefault())`
  resolves at runtime from the injected `context={"request": …}`, never as client
  input. **`HiddenField` defaults are subtle under `partial=True`** (a hidden default may
  not fire on a partial update the way it does on create), so the **live request-context
  proof is an explicit `validate()` branch, not a `HiddenField`**
  ([Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation));
  `HiddenField` is exercised only for the input-drop rule (and optionally a create-only
  behavior). Dropped from the *input* does not mean invisible to the *guards*: a
  `HiddenField`'s resolved key is a top-level `serializer.validated_data` key, so
  `_assert_save_kwargs_no_shadow` rejects a save kwarg that would shadow it,
  exactly as it does for a renamed `source=` input or a serializer default.
- **Serializer `validate()` / `non_field_errors`.** A cross-field `validate()` error or
  a `UniqueTogetherValidator` error surfaces in `serializer.errors` under DRF's
  `non_field_errors` key (`api_settings.NON_FIELD_ERRORS_KEY`), mapped to the
  `"__all__"` sentinel `036` froze — identical to the form / model flavors.
- **`update` partial preservation via `partial=True`.** A `name`-only update preserves
  the unprovided fields (DRF's `partial=True` validates only provided fields); a hidden
  row is not-found before the serializer runs.
- **File / image serializer fields.** `serializers.FileField` / `ImageField` map to the
  [`Upload`][glossary-upload-scalar] scalar on input, and the value lands in the
  serializer's `data` (DRF reads files from `data`, the contrast with the `038` form
  `files=` split), and is written over a real multipart `/graphql/` request — earned live
  by [`test_products_api.py`][test-products-api]`::test_create_item_via_serializer_multipart_upload_to_attachment`
  against a bare `django.test.Client` multipart post. The ergonomic
  [`TestClient`][glossary-testclient] wrapper is a separate card's convenience, not a
  prerequisite for this behavior.
- **Relation visibility is not delegated to the serializer's queryset, and it is enforced
  twice.** A `PrimaryKeyRelatedField`'s default queryset is `Model.objects.all()` (not
  request-scoped), so the decode type- and visibility-checks the id through the related
  primary `DjangoType.get_queryset` **before** the serializer sees it; a hidden /
  unseeable target is a field-keyed `FieldError`, identical to the model / form path. The
  decode is not the only gate: before `is_valid()` runs, each runtime relation field's own
  queryset is **composed** with the visibility queryset (author ∩ visibility, pinned to the
  write alias and locked when `Meta.select_for_update` locks), so DRF's own
  re-validation lookup is itself the visibility lookup and can never re-fetch a row the
  decode hid.
- **`many=True` related fields are a `ManyRelatedField` wrapper (DRF realization detail).**
  DRF's `PrimaryKeyRelatedField(many=True)` does **not** subclass `ManyRelatedField`;
  `RelatedField.__new__` / `many_init` returns a `ManyRelatedField` that *wraps* the
  single field as `child_relation`. So the converter's `relation_multi` branch matches
  `serializers.ManyRelatedField` (a type disjoint from `PrimaryKeyRelatedField`, so the
  two `isinstance` checks are order-independent for correctness), and the relation
  target / id type is read off `field.child_relation`, **not** `field`.
- **A plain `serializers.Serializer` (no model) on `SerializerMutation`.** Rejected at
  class creation with a [`ConfigurationError`][glossary-configurationerror] (the
  `ModelSerializer`-driven contract requires a resolvable model); the model-less plain
  `Serializer` flavor is out of scope for `0.0.13`
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).
- **A `Meta.operation = "delete"`.** Rejected at class creation
  ([Decision 10](#decision-10--operations-create--update-no-serializer-delete)).
- **A nested writable serializer field NOT opted in.** A `ModelSerializer` field that is
  itself a serializer (`ListSerializer` / nested `ModelSerializer`) fails loud by default —
  the converter raises [`ConfigurationError`][glossary-configurationerror] naming the field
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth))
  — UNLESS it is EXPLICITLY opted in via `Meta.nested_fields`, which builds the
  nested input recursively (the serializer owning the nested write via `create()` / `update()`).
- **Write-time `IntegrityError`.** A valid `serializer.save()` that loses a
  concurrent-uniqueness race returns the null-object + `FieldError` envelope via the
  shared `utils/errors.py::integrity_error_field_errors` leaf — never a top-level
  `GraphQLError`.
- **Write-time `ValidationError` — DRF and Django shapes take DIFFERENT paths.** A
  `serializer.save()` whose custom `create()` / `update()` raises a validation error returns
  the null-object + `FieldError` envelope, **not** a top-level `GraphQLError` — but the two
  `ValidationError` classes are **routed by exception class**, exactly the split
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
  step 6 pins, **never one branch**: a **DRF**
  `rest_framework.exceptions.ValidationError` (== `serializers.ValidationError`) routes its
  `.detail` (the same nested shape as `serializer.errors`) through the **recursive**
  `serializer_errors_to_field_errors` flattener; a **Django**
  `django.core.exceptions.ValidationError` (from a model `full_clean()` inside `save()`)
  has **no `.detail`** and routes through the flat `036`
  `utils/errors.py::validation_error_to_field_errors`, which
  reads Django's `error_dict` / `messages` shape (verified — it does **not** read `.detail`;
  pushing a Django error down the `.detail` path would `AttributeError` or lose structure).
  Both terminate in the same envelope, the non-field bucket mapping to `"__all__"` either
  way; an `IntegrityError` stays the `utils/errors.py::integrity_error_field_errors` branch.
- **Two distinct generated serializer inputs colliding on one GraphQL name.** Two
  **different** serializer classes with the same `__name__` both emit
  `<__name__>Input` and **always** raise a finalize-time
  [`ConfigurationError`][glossary-configurationerror] (the reused
  `materialize_generated_input_class` ledger raise); only repeats of the **same**
  `SerializerInputShape` descriptor dedupe.
- **Two serializer fields colliding on one generated GraphQL input name (M-edge).** Within
  **one** serializer, two declared fields whose generated GraphQL input names collide — a
  relation `category` that suffixes to `categoryId` clashing with a field literally named
  `category_id` that camel-cases to `categoryId` (the id-like-suffix rule, Decision 7), or
  two scalars `foo_bar` + `fooBar` that both camel-case to `fooBar` — raise a
  [`ConfigurationError`][glossary-configurationerror] **before materialization**, naming both
  offending fields. This is the serializer analog of the form collision guard
  [`forms/inputs.py`][forms-inputs]`::_guard_input_attr_collisions` (which guards both the
  input-attr and the camel-cased GraphQL-name clash) and the read-side
  [`types/finalizer.py`][types-finalizer]`::_audit_field_surface`; the serializer reuses that
  guard's shape rather than re-forking it (a silent drop of one field would otherwise let
  `build_strawberry_input_class` collapse the two).
- **Two writable fields sharing one `source` (M-edge).** A writable serializer `source`
  must be **unique across the whole write surface** — generated input fields **and**
  `Meta.injected_fields`. Two distinct declared names with the same one-segment `source`
  both write the same model attribute, and DRF resolves the collision last-write-wins, so
  an injected value could silently replace the client's; the package rejects it at class
  creation with a [`ConfigurationError`][glossary-configurationerror] naming the two fields
  and the shared `source` rather than picking a winner. The rule is enforced **again at
  runtime**, against the instantiated serializer's context-dependent `get_fields()` and at
  every opted-in nesting depth
  (`rest_framework/resolvers.py::_assert_runtime_write_source_ownership`), because
  schema-time discovery cannot see a field set a serializer builds from its context. A
  `read_only` field sharing a `source` with a writable one is **fine** (read-only fields
  are dropped from the input, Decision 7), so the common DRF read/write-split pattern is
  unaffected.
- **Same serializer, same field names, different shape.** Two create mutations over one
  serializer with the **same** effective field names but **different**
  `Meta.optional_fields` (or a `get_serializer_for_schema()` hook that returns the same
  names with different field classes / `source` / requiredness) produce **different**
  `SerializerInputShape` descriptors → **distinct** deterministic input names, never
  silent reuse of the first declaration's shape
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- **Create narrowing drops a required serializer field.** `Meta.fields` / `Meta.exclude`
  that omits a writeable `field.required`-with-no-default field on a **create** mutation
  is a bind-time [`ConfigurationError`][glossary-configurationerror]
  (`guard_create_required_serializer_fields`, run per declaration) — the schema would
  otherwise finalize but never validate. `read_only` / `HiddenField` are outside the
  writable basis; `Meta.injected_fields` is the only field-level subtraction. Update
  (`partial=True`) inputs are unaffected.
- **No `DjangoType` `Meta` key added.** This card touches neither
  [`DEFERRED_META_KEYS`][types-base] nor `ALLOWED_META_KEYS`, and adds no settings key;
  every later addition to `ALLOWED_META_KEYS` belongs to another card and names it.

## Test plan

Test placement obeys the [`examples/fakeshop/test_query/README.md`][test-query-readme]
#"Coverage rule." / [`docs/TREE.md`][tree] #"Coverage priority." **live-first** mandate,
not just the mirror rule: **any `django_strawberry_framework/` line a real fakeshop
`/graphql/` request can reach is earned in [`test_products_api.py`][test-products-api]
first**, and `tests/rest_framework/` carries **only** the residue a live query cannot
drive. Because the resolver lands together with the products surface (Slice 3), there is
**no window** where a reachable resolver line is covered by a package test. The
**package-internal boundary** (`tests/rest_framework/`) is therefore narrow and explicit
— it owns exactly:

- **schema / build-time invalid configurations** (the `Meta` matrix, narrowing
  fail-loud, the create-required guard, descriptor-collision raises) — these never reach
  a resolver;
- **converter field-class matrix rows fakeshop does not expose** (every supported DRF
  field → annotation, the custom-field raise, dotted-`source` raise);
- **registry / finalizer lifecycle** (binding, retry-idempotence, no-primary error);
- **soft-dependency import simulation** (the DRF-absent guard);
- **pure flattening-helper edge cases** (nested `serializer.errors` shapes no products
  serializer emits);
- **runtime branches impossible to drive through the sync `/graphql/` view**
  (raw-pk / non-Relay + many-relation decode with synthetic fixtures, the call-once save
  spy, the `sync_to_async` boundary + `SyncMisuseError`, hermetic constructor seams).

If a planned `tests/rest_framework/test_resolvers.py` case turns out to be drivable by a
real products query, it **moves to the live suite** — that direction only. **DRF is a
dev-group dependency** so the test env has it
([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).

**"Live" means the one aggregate `/graphql/` schema, not one file.**
[`test_products_api.py`][test-products-api] owns the products serializer lane named below,
but the live tier spans every `examples/fakeshop/test_query/` module, and the fixtures the
[improvement items](#improvements-over-graphene-djangos-drf-integration) need — a non-Relay
`Shelf`, a raw-pk M2M, a nested `Branch` → `shelves` write, a schema-hook serializer — live
in the library app, so those rows and both golden-SDL snapshots (the products one included,
since it introspects the same aggregate schema) sit in `test_query/test_library_api.py`. Same tier,
same transport, different app.

- **Live, over `/graphql/`** (Slice 3, [`test_products_api.py`][test-products-api],
  seeded via `seed_data` / `create_users`) — **the primary harness for every reachable
  resolver branch**: `createItemViaSerializer` / `updateItemViaSerializer` happy paths;
  the `serializer.errors` envelope — a `validate_<field>` error is keyed to the **GraphQL
  input name** (not the serializer field name), the `UniqueTogetherValidator` /
  `validate()` error keyed to `"__all__"`; **a renamed-field error path** — a
  `validate_<field>` error on a `source`-renamed field (or the relation field) is returned
  as `FieldError(field="<graphQLInputName>")` (e.g. `categoryId`, not `category`), locking
  the reverse-map error keying against decode errors and plain-`name` errors; **`categoryId`
  validates and writes through the serializer's `category`
  `PrimaryKeyRelatedField`** (proving the reverse map); **partial-update preservation** —
  a `name`-only `updateItemViaSerializer` preserves `description` and `category`, and the
  unique constraint fires when only `name` changes to a value already taken under the
  unchanged `category` (the `partial=True` contract — but note this fire depends on DRF's
  `UniqueTogetherValidator.filter_queryset` **backfilling the unchanged `category` from
  `serializer.instance`** during a partial update, a **DRF behavior, not a package one**,
  so the assertion is tied to the DRF floor verified in
  [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)); a non-colliding partial update;
  write authorization (anonymous denied, a caller missing the model perm denied, a
  permitted caller succeeds); the visibility-scoped `update` (a caller who cannot see a
  private `Item` gets not-found); **relation visibility** — a permitted writer submitting
  a **hidden** `Category` `GlobalID` as `categoryId` gets a field-keyed `FieldError`;
  **authorize-before-decode** — an *un*permitted writer submitting that same hidden
  `categoryId` is denied with a top-level error (the auth failure, not the relation
  `FieldError` — relation visibility is never probed before authorization); **the
  multipart `Upload` write** — a real multipart `/graphql/` request uploads a file to
  [`Item.attachment`][products-models] through the serializer's `Upload` field (the
  [`test_uploads_api.py`][test-uploads-api] transport precedent), proving the
  `Upload`-into-`data` routing; **the request-context path** — a `validate()` that reads
  `self.context["request"].user` observably fires (proving the injected
  `context={"request": …}` reaches the serializer); and **the G2 optimizer re-fetch query
  shape** — asserting the payload re-fetch keeps the relation at a bounded absolute query
  count (`CaptureQueriesContext`). The plan-object half of G2 — `select_related` /
  `prefetch_related` retained and `.only(...)` suppressed on the stashed optimizer plan —
  is package-internal below, because no `/graphql/` response carries the stash.
- **Package-internal** ([`tests/rest_framework/`][test-rest-framework]):
  - `test_converter.py` — each supported serializer-field class → annotation +
    required-ness; `PrimaryKeyRelatedField` / `ManyRelatedField` id mapping
    (Relay-`GlobalID` vs raw pk); `FileField` → [`Upload`][glossary-upload-scalar]; the
    nine-axis `utils/inputs.py::InputFieldSpec` reverse map; **renamed fields**
    — a `source="category"` FK and a `source="name"` scalar derive the GraphQL name from
    the declared field name, resolve the backing column via `source`, and preserve the
    declared name in the reverse map; a **dotted `source`** / `source="*"` on a
    model-column-converting field raises
    [`ConfigurationError`][glossary-configurationerror]; **the fail-loud dispatch — a
    known field maps, but a custom `class CustomField(serializers.Field)` raises
    [`ConfigurationError`][glossary-configurationerror]** (the catch-all-shadowing
    regression test); a `ListField` with a **scalar** child maps to `list[<scalar>]` but a
    `ListField` whose child is a relation / nested serializer raises; a nested serializer
    field raises; a **serializer-only relation** resolves its target from
    `field.queryset.model`, while a relation with no backing column **and** no concrete
    `queryset.model` raises [`ConfigurationError`][glossary-configurationerror]; a
    relation whose **target model has no registered primary `DjangoType`** raises a
    class-creation [`ConfigurationError`][glossary-configurationerror] naming the field and
    target model rather than falling back to the default manager.
  - `test_inputs.py` — the two generated inputs (`<Serializer>Input` with
    `field.required` requiredness for create; `<Serializer>PartialInput` all-optional);
    fields from the **schema-time field set**, `read_only` / `HiddenField` dropped,
    `Meta.fields` / `Meta.exclude` narrowing, `Meta.optional_fields` force-optional, a
    serializer-only (non-model) field included; **the schema-time hook** — a
    kwargs-requiring serializer **and** one whose `get_fields()` reads `self.context`
    (failing at **`.fields` access**, not construction — the guard wraps `.fields`) are
    both rejected under default no-arg discovery, and a `get_serializer_for_schema()`
    override supplying a stable field map generates the input; **`Meta.optional_fields = "__all__"` (bare string) rejected**; **the
    `SerializerInputShape` descriptor identity** — two create mutations over the same
    serializer + effective fields but different `Meta.optional_fields` get **distinct**
    deterministic names (not silent reuse), two schema hooks returning same-named fields
    with different annotations / `source` / relation kind diverge or raise on a name
    collision, identical descriptors dedupe; **the create-required narrowing guard** —
    excluding a required scalar / serializer-only / relation field raises
    [`ConfigurationError`][glossary-configurationerror], `read_only` / `HiddenField`
    exclusions do not, and the guard
    fires **per declaration** (injecting-first does not suppress a later non-injecting
    mutation on the same shape); the distinct-shapes-collide
    [`ConfigurationError`][glossary-configurationerror]; an empty effective field set →
    `ConfigurationError`; **nullability and defaults** — `allow_null=True` yields a
    **nullable** annotation while `required=True, allow_null=True` still leaves the key
    **omittable-as-missing** (omission reaches DRF as missing so `is_valid()` raises the
    required error; explicit `null` is accepted; the converter does not force a non-null
    field), `required=False, default=…` is **omittable** and lets DRF apply the default (no
    fabricated GraphQL default), and `allow_blank=True` is **absent from the generated SDL**
    (a serializer validation rule, not a GraphQL nullability axis); **two declared serializer
    fields colliding on one generated GraphQL input name** (`category` relation → `categoryId`
    clashing with a literal `category_id` → `categoryId`, or `foo_bar` + `fooBar` → `fooBar`)
    raise [`ConfigurationError`][glossary-configurationerror] **before materialization** (the
    serializer analog of [`forms/inputs.py`][forms-inputs]`::_guard_input_attr_collisions`,
    M-edge), two **writable** serializer fields sharing **one** one-segment `source`
    raise [`ConfigurationError`][glossary-configurationerror] (no double-write of one model
    attr, M-edge) while a `read_only` field sharing a `source` with a writable one is
    **accepted** (read-only is dropped from the input).
  - `test_sets.py` — the `Meta` validation matrix (missing `serializer_class`; a
    non-`Serializer`; a plain `Serializer` (no model) rejected; a `ModelSerializer`
    with no `Meta.model`; `operation = "delete"` rejected; `serializer_class` a known
    key; `permission_classes` a known key (inherited write-auth seam); `fields` +
    `exclude` both set; unknown key); registration; phase-2.5 binding via
    `bind_mutations()`; **retry-idempotence** — serializer input materialization
    succeeds, a **later type fails finalization**, the missing type is registered, and a
    second `finalize_django_types()` succeeds with no stale serializer-input attributes
    (proving `clear_serializer_input_namespace()` runs in the pre-bind reset block, not
    a per-pass clear); the no-registered-primary-type error; the model-flavor seam
    defaults unchanged.
  - `test_resolvers.py` — **genuinely-unreachable internals only** (the create/update
    happy paths, `validate_<field>` / flat `validate()` → `"__all__"` envelopes,
    `categoryId` reverse-map, partial-update, visibility-scoped update, write-auth,
    authorize-before-decode, `Upload`, request-context, and G2 query shape are **owned by
    the live suite above** and are **not** repeated here): **the recursive error
    flattener** — a `ListField` / `MultipleChoiceField` **indexed child error** maps to a
    dotted-path `FieldError` (`tags.2`), a nested dict-shaped error maps to its joined
    path, and a nested non-field error normalizes to `<path>.__all__` (no structure
    stringified, no leaf dropped) — shapes no products serializer emits; **non-Relay
    raw-pk and many-relation decode** — a hidden target → field-keyed `FieldError` for a
    **non-Relay raw-pk** primary and for a **many** relation, plus a raw-pk / wrong-model
    id → `FieldError` (synthetic fixtures; products' `Category` is Relay-`GlobalID` and
    single, so these are unreachable live); **write-time `IntegrityError`** → `FieldError`
    envelope (a monkeypatched `save()` race, not deterministically drivable over HTTP);
    **save-time validation — DRF and Django are SEPARATE branches:** a serializer
    whose custom `create()` / `update()` raises a **DRF**
    `serializers.ValidationError` from `save()` routes its `.detail` through the
    **recursive** `serializer_errors_to_field_errors` flattener; a serializer (or model
    `full_clean()`) raising a **Django** `django.core.exceptions.ValidationError` from
    `save()` routes through the **flat `036` `validation_error_to_field_errors`** (its
    `error_dict` / `messages` shape — **not** `.detail`). Both land in the envelope, never a
    top-level error; two distinct synthetic serializers (products' flat `ItemSerializer`
    has no custom `save()`), asserting a Django error never hits the `.detail` path and a
    DRF error never hits the flat mapper; **write-time `IntegrityError`** → `FieldError`
    envelope (a monkeypatched `save()` race) stays the third branch;
    **the value-preserving save** — `serializer.save()` is called **exactly once** (a
    save spy) and the re-fetch uses the returned object (not a second save, not a stale
    `serializer.instance`); **`get_serializer_kwargs` precedence** — an override that
    **adds a kwarg while preserving the request context** constructs correctly; an override
    that returns a `partial` key **at all** — whatever its value, on create or update —
    raises [`ConfigurationError`][glossary-configurationerror] (the framework owns
    partial-update semantics); an override `context` dict is
    **merged** (its non-`request` keys win, the framework-owned `request` is always set from
    `request_from_info(...)`); an override supplying a **different** `context["request"]`
    object raises [`ConfigurationError`][glossary-configurationerror] (the actor cannot drift
    from the permission seam) while the **same** object is tolerated; plus the
    bare-`HttpRequest` `info.context` fallback of `request_from_info`; **the recorded
    GlobalID strategy is consumed, not the live setting (config assessment)** — monkeypatch
    `types/relay.py::_resolve_globalid_strategy` to fail **after** finalization and assert a
    serializer relation mutation still resolves through the recorded
    `effective_globalid_strategy` (only if new serializer code touches GlobalID decode
    directly); **sync + async** (one `sync_to_async(thread_sensitive=True)`) and the
    [`SyncMisuseError`][glossary-syncmisuseerror] async-`get_queryset`-from-sync path.
  - **The DRF-absent import guard** ([`tests/rest_framework/test_soft_dependency.py`][test-rest-framework]):
    with DRF's import simulated-absent through the
    [`tests/_soft_dependency.py`][test-soft-dependency]`::simulated_absence`
    `sys.modules[…] = None` sentinel (**never** a `builtins.__import__` patch — the guards
    use `importlib.import_module`, which such a patch does not intercept, so the block
    would silently pass), **module caches for both `rest_framework*` and
    `django_strawberry_framework.rest_framework*` evicted first, and the root
    `django_strawberry_framework.SerializerMutation` attribute deleted**, so neither a
    stale submodule import nor a bound root symbol can mask the path: all three raising
    entry points — the root `__getattr__("SerializerMutation")`, an `…rest_framework`
    import, and an `…rest_framework.sets` import — raise `ImportError` with the install
    hint, while `import django_strawberry_framework` still succeeds. **Star-import stays
    DRF-free:** `from django_strawberry_framework import *` under simulated DRF-absence
    **succeeds and binds no `SerializerMutation`** (the name is not in `__all__`, so the
    star import never resolves it through `__getattr__` and never trips the guard) — the
    regression test for the soft-dep promise. A **non-memoization** assertion (a successful
    `SerializerMutation` access does not bind the name into the root module globals)
    ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
  - [`tests/mutations/test_fields.py`][test-mutations] (extend) — the
    `038`-generalized [`DjangoMutationField`][glossary-djangomutationfield] target
    check + dispatch + `data:` ref accept a `SerializerMutation` unchanged (the
    verification, not an edit).
- **Cross-cutting — no regression.** The full suite is green at the 100% coverage gate
  (`fail_under = 100`); `ruff format` + `ruff check` are clean; the **observable behavior**
  of the `036` / `038` mutation surfaces and the read side is unchanged. The
  [Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations)
  promotions refactor shared internals (extract a helper, re-point the `forms/` copy, delete
  its duplicate body) **behavior-preservingly** — the existing `036` / `038` mutation and
  form-mutation test suites stay green unchanged, which is the regression check that the
  promotion did not alter the form/model paths.

## Doc updates

Each slice owns its doc edits. [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" requires `CHANGELOG.md` edits to be explicitly
instructed — and a standing design doc cannot itself grant that permission. This spec
only *describes* the release-note work; the **Slice 4 maintainer prompt must explicitly
include the `CHANGELOG.md` edit** for it to be authorized.

- **Pre-Slice-1 gate (Slice 0) — soft-dep wiring** ([`pyproject.toml`][pyproject] +
  `uv.lock` + [`pytest.ini`][pytest-ini]): add `djangorestframework` to
  `[dependency-groups].dev` (NOT `[project].dependencies`), pinning the **verified** floor
  matching the guard's install hint, regenerate `uv.lock` so the lockfile matches, and add
  any targeted DRF-origin `ignore::` line — **before Slice 1 imports DRF in tests** (not
  Slice 4). **No package-version edits** (the `[project].version` / `__version__` /
  `test_version` and the `uv.lock` package-version entry stay `0.0.12`; only the DRF
  dependency entries change)
  ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
- **Release vs implementation docs are split.** Because this card does **not** bump
  the version (the joint `0.0.13` cut owns it,
  [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)), Slice 4 must
  not leave the repo advertising a **released** `0.0.13` feature while the package still
  reports `0.0.12`. So:
  - **Slice 4 — implemented-on-main docs (land now):** [`docs/TREE.md`][tree] fills the
    `rest_framework/` / [`tests/rest_framework/`][test-rest-framework] summary lines;
    [`TODAY.md`][today] notes the serializer mutation as an implemented capability;
    [`docs/GLOSSARY.md`][glossary] updates the [`SerializerMutation`][glossary-serializermutation]
    **body** to the implemented contract (the `Meta.serializer_class` surface, the
    serializer-derived input, the `serializer.errors` → [`FieldError`][glossary-fielderror-envelope]
    mapping, the soft DRF dependency, the `036` reuse) and **reconciles the surface keys** —
    `Meta.operation` over graphene's `model_operations`, the `id:`-decode locate over
    `lookup_field` (both recorded as deliberate non-adoptions) — marking the status
    **"implemented on main, releasing in 0.0.13"** (not `shipped (0.0.13)` yet). The
    [`GOAL.md`][goal] crit-6 example correction lands now (it is wrong the moment the code
    lands).
  - **Joint-cut docs (deferred to the `0.0.13` release):** the GLOSSARY status flips to
    `shipped (0.0.13)`, [`docs/README.md`][docs-readme] / [`README.md`][readme] move the
    serializer flavor from "Coming next (`0.0.13`)" to "Shipped today" (and the README
    **Status** version line moves to `0.0.13`), and [`CHANGELOG.md`][changelog] carries the
    release bullets — all at the joint cut, **only when the cut's maintainer prompt
    explicitly requests the `CHANGELOG.md` edit**. (If the maintainer explicitly wants
    unreleased-main docs to advertise the future version, that is an accepted override
    stated in the Slice 4 prompt; the default is the split.)
- **Slice 4 — card wrap**: [`KANBAN.md`][kanban] moves card `039` to Done as
  [`DONE-039-0.0.13`][kanban], keeping its `SpecDoc` pointing at the
  canonical card spec (a `SpecDoc` DB edit re-rendered via `scripts/build_kanban_md.py`,
  never a hand-edit).

## Risks and open questions

Every question this card opened is answered by a Decision above, and the DRF
version floor those questions gated is recorded in
[Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy). The deliberation that answered them — each question's
preferred answer for the `0.0.13` cut, its fallback if implementation proved the
preferred answer wrong, and the card-citation tensions the cut chose to record rather
than silently reconcile — is recorded in the rationale companion under
[Risks and open questions][rationale-risks].

## Out of scope (explicitly tracked elsewhere)

- **Auth mutations** ([Auth mutations][glossary-auth-mutations]) — `0.0.13`
  ([`DONE-040-0.0.13`][kanban]); shares the joint cut, reuses the same envelope.
- **A model-less plain `Serializer` flavor** — deferred
  ([Risks and open questions][rationale-risks]; the [`DjangoFormMutation`][glossary-djangoformmutation]
  model-less sibling is the fallback shape).
- **Serializer-derived output types** — the frozen `node` / `result` slot supersedes a
  serializer output
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
  (Nested writable serializers were originally a non-goal; they now ship as the EXPLICIT
  opt-in `Meta.nested_fields`.)
- **Serializer `delete`** — not shipped; the model-driven
  [`DjangoMutation`][glossary-djangomutation] (`Meta.operation = "delete"`) covers
  deletion ([Decision 10](#decision-10--operations-create--update-no-serializer-delete)).
- **The ergonomic `TestClient` / `AsyncTestClient` helper** —
  [`TestClient`][glossary-testclient], routed to `DONE-043-0.0.14` and shipped there
  at the `0.0.14` cut. This card ships the serializer `Upload`-field correctness (the
  `Upload` input typing, the value in `data`, and the live multipart write) and hands the
  test-client wrapper to that card.
- **Field-level read gates** ([`FieldSet`][glossary-fieldset] /
  [Per-field permission hooks][glossary-per-field-permission-hooks]) — `0.1.1`,
  composing on top of (not replacing) write authorization.
- **The `0.0.13` version bump** — routed to, and performed by, the joint `0.0.13` cut
  shared with [`DONE-040-0.0.13`][kanban]; no slice of this card touches it
  ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
- **A new `DjangoType` `Meta` key or settings key**
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).

## Definition of done

The completion contract the card is built against. Items map onto the card's own DoD
bullets: item 1 (spec), 2 (the `rest_framework/` subpackage on the DRF Meta surface),
3 (the serializer-field converter dual-purposed via the `is_input` flag), 4 (the soft
DRF dependency), 5 (the `FieldError` envelope from `serializer.errors`), 6 (package
tests), 7 (live HTTP for a `ModelSerializer`) — plus the export / soft-dep wiring the
[`docs/SPECS/NEXT.md`][next] flow adds.

**Spec + companion CSV**

1. `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` (this document) and its companion
   `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-terms.csv` exist;
   `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-039-serializer_mutations-0_0_13.md`
   reports `OK: 38 terms`.

**Slice 1 — serializer-field converter + serializer-derived input**

2. [`rest_framework/serializer_converter.py`][rf-converter] ships
   `convert_serializer_field` (every supported serializer-field class → its Strawberry
   annotation + required-ness, reusing the read-side
   [scalar][glossary-scalar-field-conversion] /
   [choice-enum][glossary-choice-enum-generation] /
   [`Upload`][glossary-upload-scalar] converters where overlapping) with a **fail-loud
   dispatch — no `serializers.Field → String` catch-all**: a known class maps via MRO,
   but a custom `serializers.Field` subclass hits the **raising** default →
   [`ConfigurationError`][glossary-configurationerror]; **and the `input_attr →
   (serializer_field_name, source, kind)` reverse map** (the `source` axis carries
   renamed fields — declared name → GraphQL name via the **id-like-suffix rule**
   (`category`/`category_id` → `categoryId`, `category_pk` → `categoryPk`, no doubled
   suffix), `source` → backing column, declared name preserved as the DRF write-back
   key; dotted `source` / `source="*"` on a model-column-converting field rejected).
   [`rest_framework/inputs.py`][rf-inputs] builds both the serializer-derived
   `<Serializer>Input` (create) and `<Serializer>PartialInput` (update) from the
   **schema-time field set** (the overridable `get_serializer_for_schema()` hook, default
   no-arg `serializer_class()`; a kwargs-requiring / request-shaped serializer rejected
   loudly unless the hook supplies a stable shape) with `read_only` / `HiddenField`
   dropped and `Meta.optional_fields` forced optional, under a **`SerializerInputShape`
   descriptor identity** (the emitted field specs + normalized `optional_fields`, NOT a
   name-only key — so a requiredness / hook difference yields a distinct name, never
   silent reuse), with canonical / descriptor-derived names, dedupe, and a finalize-time
   collision [`ConfigurationError`][glossary-configurationerror]; the **create-required
   narrowing guard** (`guard_create_required_serializer_fields`) runs per declaration
   before the descriptor cache lookup; `Meta.injected_fields` is its only subtraction;
   `Meta.fields` / `Meta.exclude` / `Meta.optional_fields` are normalized + fail-loud (a
   bare string including `"__all__"` rejected); all materialized as module globals
   ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).

**Slice 2 — the base class**

3. [`rest_framework/sets.py`][rf-sets] ships `SerializerMutation` subclassing
   [`DjangoMutation`][glossary-djangomutation] (overriding [`_resolve_model`][spec-036]
   → `Meta.serializer_class.Meta.model` plus the `_validate_meta` / `build_input` /
   `input_type_name` / `input_module_path` / `resolve_*` seams). The serializer-flavor
   `_validate_meta` enforces the matrix (missing `serializer_class`; a non-`Serializer`;
   a plain `Serializer` (no model) rejected; `ModelSerializer`-with-no-model;
   `operation = "delete"` rejected; mutually exclusive / normalized / fail-loud
   `fields` / `exclude` / `optional_fields` (bare-string `"__all__"` rejected); the
   inherited `permission_classes` key kept; unknown key →
   [`ConfigurationError`][glossary-configurationerror]) **and the rest of the shipped
   validator**: `Meta.injected_fields` (normalized, then guarded against the writable
   basis and against a name still present in the generated input),
   `Meta.select_for_update` through the shared `validate_select_for_update`,
   `Meta.nested_fields` including its `create()` / `update()`-override requirement,
   validation of the `get_serializer_for_schema()` field map, capture of the schema
   fingerprint, and the recursive writable-`source` ownership walk
   ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven));
   the model flavor's seam defaults are unchanged;
   [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS` are unchanged; `SerializerMutation` rides `bind_mutations()` (no new bind entry) with
   `clear_serializer_input_namespace()` cleared from **both** the
   [`finalize_django_types`][glossary-finalize_django_types] pre-bind reset block (the
   retry-idempotence fix) **and** `TypeRegistry.clear()`, **wired through the mandatory
   `register_subsystem_clear` seam**: one canonical registry of
   `(zero-argument callable, owner)` rows — registered `before_bind=True` by the module
   that owns the ledger, a string reference rejected — that both sites iterate, so DRF is
   never imported while absent (a DRF-absent build registers nothing and owes no clear) and
   the serializer is **not** a third hand-maintained clear list;
   and `SerializerMutation` exports from [`__init__.py`][init]
   under the DRF soft-import guard
   ([Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused)
   / [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)
   / [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).

**Slice 3 — resolver pipeline + products live serializer surface (one commit)**

4. [`rest_framework/resolvers.py`][rf-resolvers] runs the **locate → authorize → decode
   → `is_valid()` → `save()` → re-fetch → payload** pipeline (sync + async, one
   `transaction.atomic()` / one `sync_to_async(thread_sensitive=True)`) — **authorize
   runs before relation decode** (the `036` / `038` security invariant: decode issues
   visibility-scoped queries, so a pre-auth decode would leak relation visibility by id;
   `create` authorizes the raw payload with `instance=None`, `update` authorizes the
   located instance). Decode then produces a serializer-field-keyed `provided_data` via
   the **dedicated serializer relation decoder**: the **generated input field exposes one
   strategy-dependent shape** (the target's `GlobalID` if Relay-shaped, else its raw-pk
   scalar; the shared decoder helper accepts both only for reused / package-only
   branches), each id type-checked against the target model (resolved from the backing FK via the
   serializer field's `source`, **or `field.queryset.model` for a serializer-only
   relation**), resolved to the **visible** object through the related
   primary `DjangoType.get_queryset` (the same per-branch raw-pk visibility check
   `036`'s model path and `038`'s form path already enforce), and reduced to the pk
   before landing under the serializer field name; a hidden target → field-keyed
   `FieldError`; an [`Upload`][glossary-upload-scalar] value lands in `data`;
   the framework builds `data` itself (decoded client input + the exact-match
   `Meta.injected_fields` values from `get_serializer_injected_data`) and merges the
   **constructor-only** `get_serializer_kwargs(self, info, *, data, hook_context)` hook's
   non-reserved kwargs over the construction, then sets
   `context["request"] = request_from_info(info, …)`, `context["write_alias"]`, and
   `partial=True` on `update` unconditionally; every hook sees a frozen
   `SerializerHookContext` plus an immutable data view, never the live instance.
   `serializer.errors` maps onto the
   [`FieldError` envelope][glossary-fielderror-envelope] via the **dedicated recursive
   flattener** (`serializer_errors_to_field_errors`; dotted path `items.0.name`;
   `non_field_errors` → `"__all__"` at every level; not the one-level `036` mapper); the
   write is wrapped by the shared `utils/errors.py::integrity_error_field_errors` mapper in a
   **value-preserving closure** (`serializer.save()` called once, its returned object captured for the
   re-fetch); a **save-time `ValidationError` is routed to the envelope by exception
   class** — a DRF `serializers.ValidationError`'s `.detail` through the recursive
   `serializer_errors_to_field_errors`, a Django `django.core.exceptions.ValidationError`
   through the flat `036` `validation_error_to_field_errors` (`error_dict` / `messages`, not
   `.detail`), an `IntegrityError` through `integrity_error_field_errors` — never a top-level
   `GraphQLError`; the payload object is re-fetched through the `036` optimizer path (G2:
   `select_related` / `prefetch_related` kept, no [`.only(...)`][glossary-only-projection]),
   pinned across two tiers — the behavioral half live at
   [`test_products_api.py`][test-products-api]`::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`,
   the plan-object half package-internal at
   [`tests/rest_framework/test_resolvers.py`][test-rest-framework]`::test_serializer_refetch_keeps_select_related_suppresses_only`,
   since the optimizer's stash is introspection state no `/graphql/` response carries.
   [`mutations/fields.py`][mutations-fields] is **unchanged** — the `038`-generalized
   [`DjangoMutationField`][glossary-djangomutationfield] exposes the serializer flavor,
   verified by a [`tests/mutations/test_fields.py`][test-mutations] extension
   ([Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused)
   / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
   / [Decision 9](#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path)).

5. **In the same commit**, products exposes the `SerializerMutation`(s) (create + update
   over `Item`) backed by an [`ItemSerializer`][products-serializers], and
   [`test_products_api.py`][test-products-api] (seeded via `seed_data` / `create_users`)
   is the **primary coverage harness** — every consumer-reachable resolver branch is
   earned over real `/graphql/`: create / update happy paths, `categoryId` reverse-map
   validate-and-write through the serializer's `category` field, a **hidden-`Category`
   `GlobalID` → field-keyed `FieldError`** and **authorize-before-decode** (an unpermitted
   caller submitting that hidden id gets the auth denial, not the relation error),
   **partial-update preservation** + unique-together on a one-field change, the
   `serializer.errors` envelope (field-level + `"__all__"`), write authorization, the
   visibility-scoped `update`, the **multipart `Upload` → [`Item.attachment`][products-models]**
   write, the **request-context** `validate()` path, and the behavioral half of the
   **G2 re-fetch query shape** (its plan-object half is package-internal, item 4).
   `tests/rest_framework/test_resolvers.py` holds **only** the genuinely-unreachable
   internals (recursive-flattener shapes, raw-pk/non-Relay + many-relation decode,
   call-once save, `IntegrityError` + save-time `ValidationError`, sync/async +
   `SyncMisuseError`, hermetic kwargs seams) — **no reachable behavior is duplicated
   between the package tier and the live tier**, which spans every
   `examples/fakeshop/test_query/` module and not `test_products_api.py` alone (the
   library app hosts the fixtures those improvement rows need)
   ([Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation),
   the [`test_query/README.md`][test-query-readme] #"Coverage rule.").

**Cross-cutting — no regression**

6. The full suite is green at the 100% coverage gate (`fail_under = 100`) — including
   the **DRF-absent import-guard path covered by simulated absence**; `ruff format` +
   `ruff check` are clean; the `036` / `038` mutation surfaces and the read side are
   unchanged.

**Pre-Slice-1 gate (Slice 0) — soft-dep wiring; Slice 4 — docs + card wrap (no version bump)**

7. **Gate (before Slice 1):** [`pyproject.toml`][pyproject] adds `djangorestframework` to
   `[dependency-groups].dev` (NOT `[project].dependencies`) **and `uv.lock` is regenerated
   to match** (the DRF dependency entries only), with any verified-floor DRF-origin
   `ignore::` line added to [`pytest.ini`][pytest-ini]. **Slice 4 (implemented-on-main):**
   [`docs/GLOSSARY.md`][glossary] updates the
   [`SerializerMutation`][glossary-serializermutation] body to the implemented contract
   (status **"implemented on main, releasing in 0.0.13"**, with Public-exports + Index +
   Mutations-category rows) and reconciles its surface keys (`Meta.operation`, the
   `id:`-decode locate); [`TODAY.md`][today] / [`docs/TREE.md`][tree] reflect the
   implemented flavor — and the [`GOAL.md`][goal] crit-6 "Coming from DRF + `django-filter`"
   example is **corrected to the shipped surface**:
   `class CreateCategoryFromSerializer(SerializerMutation):` (not
   `DjangoMutation`,
   [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven))
   with an explicit `operation = "create"` (mandatory, not inferred,
   [Decision 10](#decision-10--operations-create--update-no-serializer-delete)), so the
   north star stops depicting a declaration that fails validation under the shipped
   package. The edit may assert the generated shape inline for the depicted
   `CategorySerializer(fields=("id", "name"))` — `CategorySerializerInput { name: String! }`
   (the read-only `id` dropped,
   [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)) —
   so GOAL.md's declaration and its generated schema visibly agree. **The public
   release-status wording defers to the joint cut:** the GLOSSARY `shipped (0.0.13)`
   flip, the [`docs/README.md`][docs-readme] / [`README.md`][readme] "Coming next" →
   "Shipped today" move (and README **Status** → `0.0.13`), and the
   [`CHANGELOG.md`][changelog] release bullets land at the `0.0.13` cut — `CHANGELOG.md`
   **only when the cut's maintainer prompt explicitly requests the edit**; [`KANBAN.md`][kanban]
   records the card `DONE-NNN-0.0.13` with the `SpecDoc` reference at the canonical card
   spec (kanban DB + re-render).
8. **No version bump lands in this card**
   ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)):
   `[project].version`, `__version__`, and
   [`tests/base/test_init.py::test_version`][test-base-init] stay `0.0.12`, and so does
   the `django-strawberry-framework` `version` entry inside `uv.lock` — but `uv.lock`
   **is** regenerated for the `[dependency-groups].dev` DRF add (lockfile and manifest
   stay in sync; only the DRF dependency entries change). No [`CHANGELOG.md`][changelog]
   release heading is promoted (the joint `0.0.13` cut shared with
   [`DONE-040-0.0.13`][kanban] owns the bump). Every name in
   [`__init__.py`][init]'s `_DRF_SOFT_EXPORTS` — `SerializerMutation`,
   `register_serializer_field_converter`, `SerializerFieldConversion`,
   `describe_serializer_input`, `NestedSerializerConfig`, `SerializerHookContext`,
   `UploadMetadata` — is a **named lazy export** resolved via the root `__getattr__`
   under the DRF soft-import guard, and **none is in `__all__`** while DRF is soft (so
   `from … import *` stays DRF-free).

## Improvements over graphene-django's DRF integration

Seventeen improvements make the serializer lane stricter, safer, and more
diagnosable than graphene-django's DRF integration, and all seventeen ship in
`0.0.13` (none is backlog). Each keeps the existing wins (fail-loud unmapped fields,
visibility-checked relations, authorize-before-decode, framework-owned
`context["request"]` / `partial`, recursive error flattening, transaction boundary,
descriptor-based input identity, DRF-soft-dep root). The subsections run in capability
order — input and type construction, then schema-time and runtime diagnostics, then the
write-time contracts, then the error envelope, then nested inputs — and each is addressed
by its own title. Each subsection below states the shipped contract; how the set was
arrived at is in the rationale companion under
[Improvements over graphene-django's DRF integration][rationale-improvements].

### Public serializer-field converter registry

The scalar-dispatch table `rest_framework/serializer_converter.py::_SERIALIZER_FIELD_CONVERTERS`
is now a `serializers.Field` class → converter-callable registry (each returns a
`SerializerFieldConversion`), seeded from `_BUILTIN_SCALAR_CONVERTERS`, still walked by the
shared `convert_with_mro` MRO skeleton with NO base-`Field` catch-all.
`register_serializer_field_converter(FieldClass, converter, *, override=False)` is the
sanctioned public extension (resolved by name through the root `__getattr__` under the DRF
guard, like `SerializerMutation`; also exports `SerializerFieldConversion`): a consumer maps
their OWN DRF field without patching the framework, while an unregistered custom field still
hits the raising fallthrough. Mirrors the read-side `SCALAR_MAP` mutable-module-dict hook
(persists for the process, not reset by `registry.clear()`; a re-registration without
`override=True` fails loud).

### Expanded DRF scalar capability matrix (no catch-all)

Each mapping is an EXPLICIT registry entry, never a base-`Field` catch-all: `DictField` /
`HStoreField` → `strawberry.scalars.JSON` (`HStoreField` via the MRO walk under `DictField`);
`IPAddressField` / `FilePathField` → `str`; `DurationField` → `str` (a DELIBERATE scalar —
DRF renders a duration as an ISO-8601-ish string on the wire and parses it back at
validation, not an accidental fallthrough); `ModelField` routes through its wrapped
`model_field` via the read-side `scalar_for_field` (a `ModelField` over an unsupported column,
or with no wrapped field, fails loud). Each has a package converter test; the live matrix is
earned by `createShelfViaMetadataSerializer` (`DictField` → `JSON`).

### Generated enums for serializer-only `ChoiceField`

A model-backed `ChoiceField` keeps the read-side model-choice enum reuse (the symmetric wire
contract). A serializer-ONLY `ChoiceField` / `MultipleChoiceField` is upgraded at the
`resolve_serializer_field` build site to a GENERATED enum (`MultipleChoiceField` →
`list[<enum>]`) via the shared `types/converters.py::build_enum_from_choices` core (the SAME
grouped-form rejection, value-based sanitization, and sanitize-collision guard the model enum
applies), so a serializer-only choice enum cannot drift from a model-choice enum. The enum is
cached by its descriptor-derived name (`<TypeName><Field>Enum`) so two inputs referencing one
serializer-only choice field share one enum object; a name reused with a different member set
fails loud. `FilePathField` (a `ChoiceField` subclass with dynamic filesystem-path choices) is
excluded — it stays `str`. Earned live by `createShelfViaMetadataSerializer` (`priority`).

**Declared choices survive on a model-backed scalar too.** A CONSUMER-DECLARED
`ChoiceField` / `MultipleChoiceField` — even one `source`-mapped to a plain (non-choice) model
column — emits the SAME generated serializer-only enum (via the shared `_serializer_choice_annotation`),
rather than collapsing back to the column's `String` scalar. The declared choices are part of the
public mutation contract, so they are never silently lost. Package-regression-tested with
`ChoiceField(source="name", choices=...)` over a non-choice column.

### Model-backed serializer type-override conflict policy

An AUTO-generated `ModelSerializer` field routes through the read-side `convert_scalar`
(enum/read-write symmetry). A CONSUMER-DECLARED serializer field (in the serializer's
`_declared_fields`) is an explicit contract: if its base GraphQL scalar DISAGREES with the
backing model column's scalar (e.g. `count = IntegerField(source="a_char_col")` — int vs str)
the framework FAILS LOUD naming the field, its `source`, and both scalars, rather than
silently picking the model column (the graphene-django trap). A benign rename
(`display_name = CharField(source="name")` — str vs str) agrees and resolves to the model
scalar; a `choices` column keeps the enum symmetry (the check is skipped there); a
consumer-declared `ChoiceField` is handled by the declared-choices rule (it emits the
serializer-only enum, above) BEFORE this scalar-disagreement check. This is a class-creation / bind-time raise (an
invalid configuration), so it is package-tested, not live.

### Thread DRF field metadata into the SDL

`serializer_converter.py::serializer_field_description(field)` builds a GraphQL input-field
description from a DRF field's metadata — `help_text` heads it, then a coherent constraint
summary (`min_length` / `max_length` / `min_value` / `max_value`, plus `allow_blank` when
permitted and `allow_empty` when forbidden). `_walk_serializer_fields` threads it into each
triple's `description=` (which `build_strawberry_input_class` already supports). This is
documentation / introspection only — DRF still owns runtime validation, and the field's TYPE
is unchanged. The description is a deterministic function of the field, so it never varies
independently of the descriptor identity (identical descriptors share identical descriptions;
no identity axis added). Graphene-django threads only `help_text`; this surfaces the DRF
validation summary too. Earned live by `createShelfViaMetadataSerializer`'s `label` field.

### Aggregate schema-time diagnostics

`_walk_serializer_fields` now COLLECTS every per-field conversion error (unsupported field,
non-PK relation, missing relation-primary, dotted / `source="*"`, the type-override
conflict) instead of raising on the first, folds in the input-attr / GraphQL-name / source
collision messages (the former `_guard_serializer_input_attr_collisions`, refactored to a
message collector `_collect_input_attr_collision_messages`), and raises ONE
`ConfigurationError`. A SINGLE problem is raised verbatim (so the precise per-field wording
and every `pytest.raises(match=...)` substring are preserved); TWO OR MORE are grouped under a
`… has N schema-time problem(s):` header with one bullet each, so a consumer with several bad
fields fixes them all in one pass. The aggregate is still a `ConfigurationError`, so the
canonical-name gate's `_default_full_shape_identity` keeps swallowing it (an unbuildable
default shape simply does not reserve the canonical name). Package-tested (it is a
configuration-time raise).

### Runtime schema/runtime serializer agreement guard

`rest_framework/resolvers.py::_assert_schema_runtime_agreement(mutation_cls, serializer)` runs
in `_serializer_write_step` AFTER the runtime serializer is constructed and BEFORE
`is_valid()`. It walks ONE unified list, `_write_surface_specs(mutation_cls)` — the generated
GraphQL input specs plus the `Meta.injected_fields` specs — so an injected field is proved by
exactly the same present / writable / `source` / kind / relation-model checks an input field
receives, through the same `_assert_field_agreement` body. For every spec the runtime
serializer must contain `spec.target_name`, have it WRITABLE (not `read_only`), bind the same
`source`, keep a relation as `PrimaryKeyRelatedField` /
`ManyRelatedField(PrimaryKeyRelatedField)` over the same `related_model`, and keep a file /
scalar kind compatible (a scalar that became a relation or file, or vice versa, is a
mismatch). It additionally holds two drift arms the coarse checks cannot see: the runtime
field's **requiredness** must match what the schema emitted (given the operation and
`Meta.optional_fields`), and its emitted **annotation `repr`** must match the one the
descriptor recorded. Any divergence is a framework `ConfigurationError` at the boundary, NOT a
silent DRF-ignores-the-unknown-key ambiguity — the schema hook becomes a VERIFIED contract
rather than a trust point. A runtime serializer with EXTRA fields the schema omits is fine
(never provided).

**Reaching the requiredness / annotation arms without a validated `Meta` snapshot is itself a
raise, not a stop.** Those arms need the operation and the normalized `optional_fields`, so the
guard states the requirement as a contract: any object reaching them carries a `_mutation_meta`
snapshot exposing `operation` **and** `optional_fields`. Both incoherent spellings — the
attribute absent, and the attribute present but `None` — raise one `ConfigurationError` naming
the field, so a future flavor reusing a duck-typed snapshot cannot slip past the arms
unnoticed. Returning early there would have been a fail-open: the guard would report agreement
it never checked.

Consequence: a schema-only field the runtime serializer does not declare (the old
decode-then-drop pattern) is now forbidden, so the fakeshop nullability fixtures were
redesigned — `NoteShelfSerializer(note_allow_null=...)` declares `note` as a REAL write-only
runtime field (popped in `create()`), and each mutation's `get_serializer_kwargs` constructs it
with the same `note_allow_null` its schema hook used, so schema and runtime agree while the two
still differ only in `note`'s emitted nullability. Happy path is live-covered (every serializer
mutation now passes the guard); the raise cases are package-tested.

### Golden SDL coverage for representative serializer inputs

A narrow golden-SDL snapshot (NOT a whole-schema dump) pins the serializer input lane against
cross-field drift: one library schema-hook mutation (`ShelfMetadataSerializerInput` +
`CreateShelfViaMetadataSerializerPayload` + the shared `FieldError`) and one products serializer
mutation (`ItemSerializerInput` + `CreateItemViaSerializerPayload`). Introspecting the ONE
aggregate `/graphql/` schema, the tests assert generated input names, field names, nullability,
descriptions, the serializer-only enum, the JSON / registry-mapped scalars, the file
(`Upload`) + Relay-`GlobalID` (`ID!`) / raw-pk relation id scalars, the
payload object slot (`node` for Relay `Item`, `result` for non-Relay `Shelf`), and the additive
`codes` / `path` on `FieldError`. Especially valuable now that enums, descriptions,
error metadata, and custom converters are in play.

### Schema-shape debug/introspection registry

`inputs.py::_SERIALIZER_SHAPE_REGISTRY` maps each generated input class name to its
`SerializerInputShape` (recorded by `build_serializer_input_class`, reset by
`clear_serializer_input_namespace`). `describe_serializer_input(name)` (a public debug helper,
resolved by name through the root `__getattr__`) formats a shape: backing serializer, operation,
per-field (declared name -> GraphQL name, emitted annotation, kind, source, relation target,
requiredness), and whether the CANONICAL name was used or a descriptor-derived one. The
descriptor-derived names are deliberately opaque (hash-bearing), so this makes the package's
stronger descriptor-based identity inspectable - and the materialize-collision
`ConfigurationError` is ENRICHED with the registered shape's description, so a name clash is
diagnosable rather than cryptic. Package-tested (describe reports a shape / `None` for unknown;
the collision message carries the shape).

### Row locking for model-backed write mutations (`Meta.select_for_update`)

`Meta.select_for_update` is a **shared model-backed write key, defaulting to `True`**: every
model-backed flavor — model `DjangoMutation`, `DjangoModelFormMutation`, and
`SerializerMutation` — takes a `SELECT ... FOR UPDATE` row lock on the update / delete locate
unless the mutation opts out with an explicit `select_for_update = False`. Locked writes are
the safe posture, so the key is an **opt-out**, and one shared validator
(`mutations/sets.py::validate_select_for_update`) owns its contract for all three flavors so
it cannot drift; the validated value is stored on the `_ValidatedMutationMeta` snapshot and
`run_write_pipeline_sync` passes it through. `locate_instance(target_type, node_id, info, *,
alias, select_for_update=True)` wraps the visible queryset in `.select_for_update()`, so the
lock is acquired AFTER visibility filtering and INSIDE the pipeline's write transaction, and
every relation-target check under the same write acquires it too. On a backend without
`FOR UPDATE` support (e.g. sqlite) Django silently skips the clause, so the key is safe to
declare regardless of backend and needs no framework-side backend check. Live-tested
(`updateBookViaSerializerWithLock` updates a Relay-Node `Book` cleanly under the lock);
package-tested (`Meta` validation; `locate_instance` applies `.select_for_update()` only when
asked).

### `get_serializer_save_kwargs` (a save-time hook, separate from constructor kwargs)

`SerializerMutation.get_serializer_save_kwargs(self, info, *, data, hook_context) -> dict` is
the DRF-native customization point for request-derived data DRF expects at
`serializer.save(**kwargs)`, distinct from `get_serializer_kwargs` (construction / context).
Like every consumer hook it receives the frozen `SerializerHookContext` plus an immutable data
view, never the live instance. The resolver calls it INSIDE the value-preserving `save()`
closure — `saved = serializer.save(**save_kwargs)` — so the transaction boundary,
`ValidationError` / `IntegrityError` mapping, and optimizer re-fetch are all preserved (unlike
graphene-django's `perform_mutate`, which bypasses framework-owned behavior). Default `{}`.

**Two guards, and together they confine the hook to non-model custom arguments.**
`_assert_save_kwargs_no_shadow` rejects a save kwarg whose name matches a top-level
`serializer.validated_data` key (renamed `source=` inputs, `Meta.injected_fields` injections,
serializer defaults, and `HiddenField`s alike — the comparison is against the actual validated
keys, not the input-spec names, because a collision would silently override the validated
value). `_assert_save_kwargs_not_model_fields` then rejects a save kwarg naming **any** model
field at all, whether or not it was validated: model-field injection goes exclusively through
the audited `Meta.injected_fields` channel, so an `owner=request.user` style save
kwarg is a `ConfigurationError` and its `Meta.injected_fields` equivalent is the supported
spelling. The hook's remaining, intended use is a **custom argument the serializer's own
`create()` / `update()` consumes**: the live fixture stamps a non-model `stamp` kwarg that
`create()` pops and writes into `topic`. Live-tested (`createShelfWithSaveKwargs`, and the
model-field rejection over `/graphql/`); package-tested (shadow raises, model-field raises,
non-shadow allowed).

### Visibility-scoped + query-efficient relation validation

Two moves keep the security win (authorize-before-decode + visibility-checked ids) while cutting
the query cost. (a) A batched `utils/querysets.py::visible_related_objects(related_model, pks,
info)` confirms a MULTI relation's whole set in ONE visibility-scoped `pk__in` query instead of
one per id: the serializer multi decoder now type-checks + coerces every id first (the shared
`utils/write_values.py::type_check_relation_id`, no DB), then batch-confirms visibility, preserving the uniform
no-existence-leak relation error (a hidden / missing member is the same field-keyed error). (b)
`_scope_relation_querysets_to_visibility` COMPOSES each runtime relation field's `queryset`
(`PrimaryKeyRelatedField`) / `child_relation.queryset` (`ManyRelatedField`) WITH the
visibility-scoped queryset before `is_valid()` — `original.filter(pk__in=<visibility queryset>)`,
an ADDITIONAL constraint (a `pk__in` subquery, still one lookup), never a REPLACEMENT
(a reassignment would erase a serializer author's own
`PrimaryKeyRelatedField(queryset=...)` restriction and could admit a visible-but-disallowed row).
So DRF's own re-validation honors BOTH the author's queryset AND visibility, and can never
re-fetch a row the decode hid. Package-tested with `assertNumQueries`-style
`CaptureQueriesContext` (the batched multi decode is exactly ONE query), a hidden-member
rejection, and a visible-but-author-disallowed single + many relation (the compose preserves the
author's filter); live-tested by `createShelfViaAltBranchesSerializer` (a raw-pk M2M writes
visible branches, a hidden branch is a `altBranches` relation error over `/graphql/`).

### Explicit injection contract (`Meta.injected_fields`)

`Meta.injected_fields = (...)` is the auditable, per-field server-data contract (a serializer
`Meta` key, normalized like `optional_fields`, stored on the snapshot): the create-required
guard always runs and subtracts only the declared injected fields, so a dropped required field
not declared injected still raises. Each injected name is validated at class creation against
the same writable schema-time field basis as generated input: typos, `read_only` fields, and
`HiddenField` instances fail loud. The schema-time spec is stashed in
`_injected_field_specs`.

The framework builds serializer `data` itself from decoded client data plus the values supplied
exclusively by `get_serializer_injected_data(self, info, *, data, hook_context)`, whose keys
must exactly match `Meta.injected_fields`. Runtime acceptance rides the ONE unified
`_write_surface_specs` walk through `_assert_schema_runtime_agreement`, so an
injected field receives exactly the same present / writable / `source` / kind / relation-model
checks an input field does — there is no separate injected-field guard to keep in step. Live-tested (`createShelfWithInjectedTopic`
narrows away a required `topic` and injects it); package-tested (subtraction / still-raise /
writable class validation / exact keys / runtime agreement).

### Fingerprint `get_serializer_for_schema()` for determinism

The spec requires the schema hook to return a STABLE, request-independent field shape, but the
hook runs at class validation AND again at the phase-2.5 bind — a nondeterministic hook could
validate one shape and bind another. `inputs.py::serializer_schema_fingerprint(field_map)`
computes a digest of EVERY SDL-affecting axis: ordered field names, classes,
sources, read/write flags, `required`, `allow_null`, relation target models, PLUS the description
inputs (`help_text` + the constraint summary), the enumerable choice MEMBERS, and the converter
discriminants (`ModelField` wrapped field / `ListField` child) — so a hook that changes a
description, enum members, or converter behavior without changing the coarse identity still trips
the guard. `_validate_meta` captures it on `_ValidatedMutationMeta.schema_fingerprint` at class
validation; both `build_input` AND `input_type_name` read the hook through the ONE guarded path
`_checked_schema_field_map` (the type-name derivation never reads an unguarded
field map behind the fingerprint's back), raising `ConfigurationError` on drift. This turns the
spec's stable-shape promise into an enforced contract (graphene-django has no equivalent — no
schema/runtime hook split). Package-tested (drift raises at bind AND via `input_type_name`; the
fingerprint is sensitive to choices / help_text / converter extras; a stable hook binds cleanly).

### Preserve DRF `ErrorDetail.code` in the error envelope

The shared `FieldError` (`mutations/inputs.py`) gains an additive, default-empty
`codes: [String!]` alongside the intact `field` / `messages`. The single leaf ctor
`field_error(path, messages, *, codes=None)` (still the one both flatteners call) populates
it: the DRF flattener passes each leaf `ErrorDetail.code` (`_error_detail_codes`), the Django
flat mapper passes each `ValidationError.code` (via `error.error_list`), and the
framework-generated errors pass a deliberate code (`invalid` for a bad relation id / bad
lookup id / unstorable text, `null` for an explicit null, `not_found` for a locate miss,
`constraint` for the `IntegrityError` fallback). A client branches on `required` / `invalid`
/ `unique` / … without parsing localized text. Uniform across all three write flavors (the
leaf is shared). Live-tested (`createShelfViaMetadataSerializer`: a `max_length` DRF code).

### Structured error `path` in addition to the dotted `field`

`FieldError` also gains an additive, default-empty `path: [String!]` — the dotted `field`
string split into SEGMENTS, derived inside `field_error` so it cannot drift from `field`.
`items.0.name` → `["items", "0", "name"]`. Documented ROOT rule: a model-wide / non-field
error is `field="__all__"` with an EMPTY `path` (`[]`) — whether it arrives as an empty path
(the Django mapper) or as the bare `"__all__"` sentinel (the DRF flattener's top-level
non-field bucket), so the two flavors agree; a NESTED non-field error keeps the sentinel as
its final segment (`["items", "0", "__all__"]`). Additive (a client selecting only `field` /
`messages` is unaffected); pairs with the preserved `ErrorDetail.code` above. Live- and package-tested.

### Explicit opt-in nested serializer input support

graphene-django converts a nested `ModelSerializer` / `ListSerializer` field automatically,
caching the generated input by the serializer's CLASS NAME (silently conflating two shapes of
one class) with little write-contract validation. The package's default is the OPPOSITE (safer
but less capable): a nested serializer field fails loud. This adds the CAPABILITY with the
package's fail-loud architecture — a DRF-first, EXPLICIT, opt-in contract:

- **Opt-in only, descriptor-keyed.** `Meta.nested_fields = {"items": NestedSerializerConfig(...)}`
  names the nested field(s) that build a nested input RECURSIVELY. A nested field NOT named
  still fails loud (`serializer_converter.py::_reject_nested_serializer`, now the FIRST check in
  `resolve_serializer_field` so a nested field over a reverse-relation column can never be
  misrouted as a relation-id input). `NestedSerializerConfig` (a frozen dataclass, exported from
  the root by name under the DRF guard like `SerializerMutation`) carries `fields` / `exclude` /
  `optional_fields` (narrow the nested input via the SAME machinery the top level uses) and a
  recursive `nested_fields` map (the deeper opt-in — each level names its own children). A nested
  field with a DRF `source=` records the same normalized one-segment source axis scalar / relation
  fields do, so the runtime schema/runtime agreement guard's source comparison matches
  instead of failing every invocation; a dotted source / `source="*"` fails loud in
  `_resolve_nested_field` (the model-column-path fail-loud source policy).
- **Recursively fingerprinted, scoped to the writable set, gated on the opt-in tree.**
  `serializer_schema_fingerprint` folds an OPTED-IN nested serializer's own field map into the
  determinism fingerprint (bounded by an on-path cycle guard), so a nondeterministic hook that
  changes a nested shape is caught at the phase-2.5 bind. The fingerprint runs over the EFFECTIVE
  (writable + narrowed) field set — the SAME set the input build uses — and drops `read_only` /
  `HiddenField` at every level, so a read-only or narrowed-away nested serializer (e.g.
  a context-sensitive nested OUTPUT serializer whose `.fields` cannot materialize no-arg) is NEVER
  descended into and cannot break class creation; a residual reachable nested-`.fields` failure is
  wrapped as `ConfigurationError`. The recursion is ALSO gated on the `Meta.nested_fields` opt-in
  tree, threaded into the fingerprint at BOTH class validation and bind: an
  UNOPTED nested field records a shallow marker (class name + many-ness) WITHOUT reading its
  `.fields` — nesting is opt-in only, so it produces no nested input and its child shape cannot
  affect the SDL, and the field walk raises the canonical `_reject_nested_serializer` opt-in error.
  Descending into an unopted, context-sensitive nested child would otherwise surface a misleading
  "opted in via Meta.nested_fields..." materialization error at class validation, shadowing the
  canonical opt-in error.
- **Depth / cycle guarded.** Recursion is bounded by the finite, immutable `NestedSerializerConfig`
  tree; a serializer class that reappears on the recursion path is a fail-loud cycle, and a
  path beyond `_NESTED_MAX_DEPTH` is a fail-loud depth cap.
- **The framework NEVER auto-saves the nested relation.** A NON-EMPTY `Meta.nested_fields`
  REQUIRES the serializer to override `create()` (create op) / `update()` (update op) —
  checked at class creation, because DRF's default `ModelSerializer.create/update` `assert`s
  on writable nested data (a raw `AssertionError` that would escape the envelope). An EMPTY
  declaration (`Meta.nested_fields = {}`) opts nothing in, passes no nested data, and so
  demands no override. The framework decodes + validates
  the nested data (visibility-checking each nested relation, recursively, and scoping the runtime
  nested serializer's relation querysets) and hands it to the serializer's OWN `create()` /
  `update()`, which owns the write, inside the pipeline transaction.
- **Errors route through the structured `path` / `codes` envelope, re-keyed at every depth.** A
  nested DRF validation error flattens through the recursive `serializer_errors_to_field_errors`,
  which RE-KEYS each path segment to its GraphQL name as it descends — not only the
  root — driven by a recursive reverse map built from `InputFieldSpec.nested_specs`: a nested child
  field / alias / relation suffix reports its SDL name (`shelves.0.altBranches`, not
  `shelves.0.alt_branches`), while numeric indexes and the `__all__` non-field sentinel are
  preserved. A nested framework decode error (a hidden relation id) is keyed to the same FULL
  nested path with the `invalid` code and rolls the write back. The runtime schema/runtime
  agreement guard recurses into the nested serializer too.

The nested input dedupes on its `SerializerInputShape` descriptor (folded into the parent
descriptor identity + the per-shape build cache, so two nested shapes never collide on one name)
and materializes through the same ledger. Earned live by `createBranchWithNestedShelves` (a
`Branch` with a nested `shelves` list carrying a raw-pk `altBranches` M2M) — the happy nested
write, the hidden-nested-relation structured-path error + rollback, and the nested DRF
validation-error flattening; the fail-loud / guard / config-validation / source-axis / recursive
re-keying / opt-in-gated-fingerprint branches are package-tested.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[django-workflow]: ../../.github/workflows/django.yml
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[pytest-ini]: ../../pytest.ini
[readme]: ../../README.md
[start]: ../../START.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-apply_cascade_permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-auth-mutations]: ../GLOSSARY.md#auth-mutations
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-cross-subsystem-invariants]: ../GLOSSARY.md#cross-subsystem-invariants
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-djangoformmutation]: ../GLOSSARY.md#djangoformmutation
[glossary-djangomodelformmutation]: ../GLOSSARY.md#djangomodelformmutation
[glossary-djangomodelpermission]: ../GLOSSARY.md#djangomodelpermission
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: ../GLOSSARY.md#djangomutationfield
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: ../GLOSSARY.md#fielderror-envelope
[glossary-fieldset]: ../GLOSSARY.md#fieldset
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-input-type-generation]: ../GLOSSARY.md#input-type-generation
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metaglobalid_strategy]: ../GLOSSARY.md#metaglobalid_strategy
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: ../GLOSSARY.md#per-field-permission-hooks
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-relay_globalid_strategy]: ../GLOSSARY.md#relay_globalid_strategy
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[glossary-serializermutation]: ../GLOSSARY.md#serializermutation
[glossary-specialized-scalar-conversions]: ../GLOSSARY.md#specialized-scalar-conversions
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror
[glossary-testclient]: ../GLOSSARY.md#testclient
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[next]: NEXT.md
[rationale-d10]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-10--operations-create--update-no-serializer-delete
[rationale-d11]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelserializer
[rationale-d12]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy
[rationale-d13]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-13--live-coverage-products-grows-a-modelserializer-mutation
[rationale-d14]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-14--version-bumps-are-owned-by-the-joint-0013-cut
[rationale-d1]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-2--card-scope-boundary-the-serializer-flavor-ships-auth-stays-out-the-frozen-036-contracts-and-the-038-factory-are-reused-unchanged
[rationale-d3]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-3--class-meta-surface-not-graphenes-mutationoptions
[rationale-d4]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-4--module-and-test-locations-rest_framework-subpackage-mirroring-forms
[rationale-d5]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused
[rationale-d6]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven
[rationale-d7]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth
[rationale-d8]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload
[rationale-d9]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path
[rationale-improvements]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#improvements-over-graphene-djangos-drf-integration
[rationale-risks]: appx/spec-039-serializer_mutations-0_0_13-rationale.md#risks-and-open-questions
[spec-027]: spec-027-filters-0_0_8.md
[spec-028]: spec-028-orders-0_0_8.md
[spec-034]: spec-034-permissions-0_0_10.md
[spec-035]: spec-035-optimizer_hardening-0_0_10.md
[spec-036]: spec-036-mutations-0_0_11.md
[spec-037]: spec-037-upload_file_image_mapping-0_0_11.md
[spec-038]: spec-038-form_mutations-0_0_12.md
[spec-039-rationale]: appx/spec-039-serializer_mutations-0_0_13-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[init]: ../../django_strawberry_framework/__init__.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[rf-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[rf-hook-context]: ../../django_strawberry_framework/rest_framework/hook_context.py
[rf-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-write-transaction]: ../../django_strawberry_framework/utils/write_transaction.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-dry-ratchet]: ../../tests/rest_framework/test_dry_import_ratchet.py
[test-mutations]: ../../tests/mutations/
[test-rest-framework]: ../../tests/rest_framework/
[test-soft-dependency]: ../../tests/_soft_dependency.py

<!-- examples/ -->
[products-models]: ../../examples/fakeshop/apps/products/models.py
[products-schema]: ../../examples/fakeshop/apps/products/schema.py
[products-serializers]: ../../examples/fakeshop/apps/products/serializers.py
[test-products-api]: ../../examples/fakeshop/test_query/test_products_api.py
[test-query-readme]: ../../examples/fakeshop/test_query/README.md
[test-uploads-api]: ../../examples/fakeshop/test_query/test_uploads_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-serializer-converter]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/serializer_converter.py
[upstream-serializer-mutation]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/mutation.py
