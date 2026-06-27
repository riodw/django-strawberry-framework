# Spec: DRF serializer mutations — `SerializerMutation` on the DRF-shaped `class Meta` surface, reusing the frozen `FieldError` envelope and the `DjangoMutation` foundation, with `djangorestframework` as a soft dependency

Planned for `0.0.13` (card [`TODO-ALPHA-039-0.0.13`][kanban]). This card adds the
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

The flavor reuses, **byte-identical**, the contracts [`spec-036`][spec-036] **froze
for exactly this** and [`spec-038`][spec-038] proved reusable: the shared
[`errors: list[FieldError]`][glossary-fielderror-envelope] envelope (populated here
from `serializer.errors`), the generated `<Name>Payload` wrapper with its uniform
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
card [`TODO-ALPHA-040-0.0.13`][kanban] (which reuses the same envelope and
`DjangoMutation` base). So the `pyproject.toml` / `__version__` /
[`tests/base/test_init.py::test_version`][test-base-init] bump from `0.0.12` to
`0.0.13` is owned by the **joint `0.0.13` cut**, not by this card — the same posture
[`spec-036`][spec-036] Decision 13 took for the joint `0.0.11` cut it shared with
[`spec-037`][spec-037]. No slice in this card bumps the version.

Status: **IN PROGRESS** — authored for [`TODO-ALPHA-039-0.0.13`][kanban] via the
[`docs/SPECS/NEXT.md`][next] flow; no slice built yet. The card's hard dependency is
satisfied: [`DONE-036-0.0.11`][kanban] (the mutation foundation this card subclasses)
has shipped, and [`DONE-038-0.0.12`][kanban] (which generalized the field factory and
proved the flavor-on-the-base pattern) has shipped too. **Four slices** (the resolver
pipeline and the products live surface are **one** slice, so the resolver's
consumer-reachable behavior is earned live in the same commit it lands — the
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
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)
/
[Decision 9](#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path)
/
[Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation)),
and Slice 4 (**docs + the soft-dep wiring + card wrap, no version bump**; the per-card
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
[`docs/GLOSSARY.md`][glossary] carries [`SerializerMutation`][glossary-serializermutation]
as `planned for 0.0.13`; Slice 4 promotes it to `shipped (0.0.13)`.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`TODO-ALPHA-039-0.0.13`][kanban]
  card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-06-26). Pinned: the
  canonical structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the card-scope
  boundary that ships the serializer flavor and reuses the frozen `036` contracts +
  the `038`-generalized factory, parking auth for the sibling `0.0.13` card
  ([Decision 2](#decision-2--card-scope-boundary-the-serializer-flavor-ships-auth-stays-out-the-frozen-036-contracts-and-the-038-factory-are-reused-unchanged));
  the **`class Meta`-not-`MutationOptions`** surface
  ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions));
  the `rest_framework/` subpackage layout
  ([Decision 4](#decision-4--module-and-test-locations-rest_framework-subpackage-mirroring-forms));
  the one-base public surface reusing the `038`-generalized factory
  ([Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused));
  the base-class strategy — `SerializerMutation` rides the
  [`DjangoMutation`][glossary-djangomutation] base via the [`_resolve_model`][spec-036]
  seam, `ModelSerializer`-driven
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven));
  the serializer-derived input mapping with a fail-loud converter
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  the `serializer.errors` → [`FieldError`][glossary-fielderror-envelope] pipeline with
  DRF-native `partial=True` update
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload));
  the optimizer composition reusing the `036` re-fetch path
  ([Decision 9](#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path));
  the operation set (`create` / `update`, no serializer `delete`)
  ([Decision 10](#decision-10--operations-create--update-no-serializer-delete));
  permission reuse
  ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelserializer));
  the **soft `djangorestframework` dependency + the 100%-coverage strategy** (DRF out
  of runtime deps, added to the dev group, the absent path covered by simulated
  absence)
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy));
  the products live serializer surface
  ([Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation));
  and **the joint `0.0.13` cut owning the version bump**
  ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)). Four
  card-body tensions are carried into
  [Risks and open questions](#risks-and-open-questions) rather than silently
  reconciled (the card's `Meta.model_operations` vs the package's per-operation
  `Meta.operation`; the card's `Meta.lookup_field` vs the package's `id:`-decode
  locate; the card's "dual-purposed for inputs **and outputs**" converter vs the
  `036`-frozen uniform `node` / `result` slot; and a model-less plain `Serializer`
  flavor), each with a preferred reading.
- **Revision 2** — applied a code-review pass (all findings verified against the
  package source first). Foundational (shape-setting)
  fixes: (1) the resolver pipeline is reordered to **locate → authorize → decode** so
  write authorization runs **before** any relation decode — the package security
  invariant the `038` form pipeline pins
  ([`forms/resolvers.py`][forms-resolvers] #"Authorize BEFORE decoding relations"),
  closing a relation-visibility-probe-by-id regression
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload));
  (2) schema-time field discovery goes through an overridable
  `get_serializer_for_schema()` hook (not a bare no-arg `serializer_class()`), with
  request-dependent schema shape rejected loudly
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  (3) renamed serializer fields (`source`) are designed — supported `source` scope, a
  GraphQL-name-from-field-name rule, backing-column resolution via `source`, and the
  declared name preserved in the now-`(serializer_field_name, source, kind)` reverse map
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  (4) a **dedicated recursive `serializer.errors` flattener** with a dotted path
  convention (`items.0.name`, `NON_FIELD_ERRORS_KEY` → `"__all__"` at every level)
  replaces the implicit reuse of the one-level `036` mapper
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)).
  Plus: the serializer-input ledger clears in the
  [`finalize_django_types`][glossary-finalize_django_types] **pre-bind reset block**
  (not only `TypeRegistry.clear()`) for retry-idempotence
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven));
  the soft-DRF root export is pinned to a root `__getattr__` + a shared `require_drf()`
  with the exact behavior of all four import forms and a cache-eviction rule for the
  absent-path test
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy));
  `uv.lock` is reconciled as **updated** (the DRF dev-group add) while the package
  version stays `0.0.12`
  ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)); and the
  smaller gaps — `optional_fields = "__all__"` rejected as a bare string,
  `permission_classes` kept explicitly in the serializer allowed-key set, and the
  runtime serializer `context` resolved via the shared `request_from_info` helper
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)
  / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)).
- **Revision 3** — applied a second code-review pass (again verified against the package
  source first; the form `guard_create_required_fields` /
  `_cached_build_form_input` per-declaration precedent and the
  `save_or_field_errors` return-discard were confirmed in code). Foundational
  (shape-setting) fixes: (1) serializer input identity is now a **`SerializerInputShape`
  descriptor** (the emitted field specs + normalized `optional_fields`), not the
  name-only `(class, op, names)` key — two same-named shapes that differ in requiredness
  or in `get_serializer_for_schema()`-returned field specs get distinct deterministic
  names or a `ConfigurationError`, never silent cache reuse
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  (2) a **create-required narrowing guard** (`guard_create_required_serializer_fields`,
  the form `guard_create_required_fields` analog) fails at bind, per declaration, before
  the descriptor cache lookup, when `Meta.fields` / `Meta.exclude` drops a writeable
  required-no-default field (waived by a `get_serializer_kwargs` override)
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
  Plus: an **id-like-suffix rule** so a relation field already named `*_id` / `*_pk` is
  not double-suffixed (`category` → `categoryId`, `category_id` → `categoryId`,
  `category_pk` → `categoryPk`)
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  a **value-preserving save** — the resolver captures `serializer.save()`'s returned
  object in the `save_or_field_errors` closure (called once) and re-fetches by its pk,
  rather than re-deriving from a return the wrapper discards
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload));
  and the root `__getattr__` is pinned to **not memoize** `SerializerMutation`, with the
  absent-DRF test also evicting the root attribute
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
- **Revision 4** — applied a third code-review pass (test-placement, verified against
  [`examples/fakeshop/test_query/README.md`][test-query-readme] #"Coverage rule.",
  [`docs/TREE.md`][tree] #"Coverage priority.", the existing
  [`test_uploads_api.py`][test-uploads-api] live-multipart precedent, and the
  [`Item.attachment`][products-models] `FileField`). **Foundational restructuring:** the
  five-slice plan collapses to **four** — the serializer resolver pipeline and the
  products live serializer surface now land in **one** slice (Slice 3), so every
  consumer-reachable resolver line is earned by a real `/graphql/` request *at the commit
  it appears* (a separate live slice would leave reachable lines package-covered at the
  resolver commit, the inverse of the live-first rule)
  ([Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation)).
  [`test_products_api.py`][test-products-api] becomes the **primary** harness for every
  reachable branch (happy paths, envelopes, reverse-map, partial-update, visibility,
  write-auth, authorize-before-decode, **the multipart `Upload` write**, **the
  request-context `validate()` path**, and the G2 query shape — the last two are shipped
  `0.0.13` runtime branches, so they move from package tests to live), and
  [`tests/rest_framework/test_resolvers.py`][test-rest-framework] is narrowed to the
  residue a live query cannot drive (recursive-flattener shapes, raw-pk/non-Relay +
  many-relation decode, call-once save, `IntegrityError`, sync/async + `SyncMisuseError`,
  hermetic kwargs seams). The [Test plan](#test-plan) now states the **explicit
  package-test boundary** so the new `tests/rest_framework/` tree cannot accrete
  resolver-acceptance coverage. The old Slice 5 (docs + soft-dep + card wrap) is now
  Slice 4 throughout.
- **Revision 5** — applied a fourth code-review pass (every claim verified against the
  package source first: the finalizer's **direct, unconditional** mutation / form clears
  ([`types/finalizer.py`][types-finalizer] #"clear_mutation_input_namespace"),
  `TypeRegistry.clear()`'s `_clear_if_importable` asymmetry, the
  [`django.yml`][django-workflow] CI matrix × [`pytest.ini`][pytest-ini]
  `filterwarnings = error`, `fail_under = 100`, and DRF's lazy `.fields` were all
  confirmed). **Foundational (shape-setting) fixes:** (1) the pre-bind
  `clear_serializer_input_namespace()` is pinned **import-guarded** (`try/except
  ImportError` / `_clear_if_importable`) — `rest_framework/inputs.py` is behind the DRF
  soft-import guard while the mutation / form clears are direct unconditional imports, and
  [`finalize_django_types`][glossary-finalize_django_types] runs on **every** DRF-absent
  schema build, so a literal mirror would `ImportError` and break schema construction for
  every DRF-absent consumer
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven),
  Slice 2 checklist); (2) the **DRF version floor** open question becomes a concrete
  **pre-Slice-1 check gated by the CI matrix under `-W error`** — the dev-group DRF must
  import / run warning-free on (Python 3.14, Django 6.0 / `latest`); DRF's Django support
  lags Django releases, so a compatible release must be confirmed before pinning and a
  targeted DRF-origin `ignore::` line budgeted — the binding constraint, not
  `NON_FIELD_ERRORS_KEY` availability
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)
  / [Risks](#risks-and-open-questions)). Plus: a **save-time `ValidationError`** (from a
  custom `create()` / `update()` / model `full_clean()`) is routed through the recursive
  flattener into the envelope — split by exception type from `IntegrityError`, never a
  top-level `GraphQLError`
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)
  step 6); the `get_serializer_for_schema()` loud-rejection guard wraps **`.fields`
  materialization**, not `serializer_class()` (DRF builds `.fields` lazily, so a
  context-requiring serializer fails at `.fields` access, not construction)
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  the carried `is_input` parameter is pinned **accepted-and-ignored with no `if not
  is_input:` branch**, so it adds no uncovered line under `fail_under = 100`
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  the partial-update unique-together fire is flagged a **DRF behavior** (DRF backfills the
  unchanged member from `serializer.instance`) tied to the verified floor; the mutation's
  `Meta.fields` (input surface) vs the serializer's own `Meta.fields` (validation) are
  clarified as **distinct namespaces** and `Meta.optional_fields` noted a no-op on
  `update`; `ListField` is scoped to **scalar children** (a relation / nested-serializer
  child raises); the `rest_framework/` name-collision test cost is named at
  [Decision 4](#decision-4--module-and-test-locations-rest_framework-subpackage-mirroring-forms);
  and the stale "Slice 5" CHANGELOG reference is corrected to Slice 4.
- **Revision 6** — applied a [`GOAL.md`][goal] + working-reference cross-reference pass
  (every claim verified first: [`GOAL.md`][goal]'s crit-6 serializer example really does
  show the `DjangoMutation` base with **no** `operation`, while the model sibling and
  prose carry an explicit `operation = "create"`; and the shipped `DjangoMutation`
  **requires** an explicit `operation` — a missing key is a `ConfigurationError`,
  [`spec-036`][spec-036] — so defaulting it for the serializer flavor would make it the
  only write flavor that infers the op). **Foundational (surface-reconciliation) fixes:**
  the spec's public surface (`SerializerMutation` base + mandatory `operation`) and
  GOAL.md's crit-6 example diverged, and nothing in Slice 4 reconciled them — now (1)
  [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)
  weighs the GOAL-literal "`DjangoMutation` detects `serializer_class`" alternative and
  justifies the `SerializerMutation` base on **by-name `graphene-django` migration
  parity** (crit 7); (2)
  [Decision 10](#decision-10--operations-create--update-no-serializer-delete) pins
  `operation` mandatory (uniform with the family that already requires it) and frames the
  real crit-7 friction (the migrant adds an `operation` key + splits one auto-dispatching
  mutation into two); (3) the **Slice-4 GOAL.md edit now explicitly corrects the crit-6
  example** to the `SerializerMutation` base + `operation = "create"`, asserting the
  read-only-`id`-dropped `CategorySerializerInput { name: String! }` shape; and (4) the
  [Risks](#risks-and-open-questions) `model_operations`-alias fallback is elevated to the
  named near-term crit-7 affordance. Plus: a note that the `django-graphene-filters`
  cookbook is **query/filter-only**, so reference parity for this card is graphene-django's
  `rest_framework`, not the cookbook ([Borrowing posture](#borrowing-posture)); the
  `get_serializer_kwargs` parity row reflagged **name-borrowed, not signature-compatible**
  (a graphene override can't carry over verbatim); the serializer flavor framed as the
  deliberate **crit-7 exception that keeps its source package** (`djangorestframework` is
  the reused validation engine, not a runtime to shed); and the fail-loud converter's
  relation/file mapping pinned as **mandated by [`GOAL.md`][goal]'s "don't silently weaken
  rich relations" non-goal**, not stylistic
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [`SerializerMutation`][glossary-serializermutation] — the subject. The glossary
  already pins its planned contract: a base consuming a DRF `Serializer` /
  `ModelSerializer` via `Meta.serializer_class` (`Meta.lookup_field`,
  `Meta.model_operations`, `Meta.optional_fields`), an input-type factory deriving the
  Strawberry input from the serializer's fields, a soft `rest_framework` dependency,
  and validation through the shared [`FieldError` envelope][glossary-fielderror-envelope].
  Slice 4 promotes the entry from `planned for 0.0.13` to `shipped (0.0.13)` and
  reconciles the surface keys this spec pins (`Meta.operation` over `model_operations`,
  the `id:`-decode locate over `lookup_field` — [Risks](#risks-and-open-questions)).
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
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)).
- [`FieldError` envelope][glossary-fielderror-envelope] — the shared error contract
  [`spec-036`][spec-036] **defined and froze** for this card. A serializer mutation
  maps `serializer.errors` (a `field → [messages]` dict, with DRF's
  `non_field_errors` / `api_settings.NON_FIELD_ERRORS_KEY` bucket) onto the
  byte-identical envelope, keying serializer-level errors to the same `"__all__"`
  sentinel `036` pinned
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)).
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
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)).
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
  ([`TODO-ALPHA-040-0.0.13`][kanban]) that shares the joint cut and reuses the same
  envelope; named here to fix the out-of-scope boundary and the joint-version-bump
  ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] /
  [`FieldSet`][glossary-fieldset] / [Per-field permission hooks][glossary-per-field-permission-hooks]
  — the `1.0.0` invariant this card must not violate (a `DjangoType` `Meta` key is
  promoted only when its subsystem applies it end-to-end). A serializer mutation adds
  **no** `DjangoType` `Meta` key, so [`DEFERRED_META_KEYS`][types-base] is untouched
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package-internal serializer-converter
  / base / resolver mechanics under [`tests/rest_framework/`][test-rest-framework]
  mirroring source; live consumer behavior over `/graphql/` when a realistic request
  reaches it —
  [Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation));
  the settings-keys-only-when-needed rule (this card adds no settings key); the
  no-pytest-after-edits rule; the CHANGELOG-edit-permission rule at
  [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" —
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
  [`tests/rest_framework/`][test-rest-framework]; this card creates those trees and
  adds no module outside them beyond the products-example wiring and the soft-dep edit.
- [`GOAL.md`][goal] — success-criterion 6 ("Write mutations declaratively from
  `ModelForm`, `ModelSerializer`, or auto-generated `Input` types — one shared
  `errors: list[FieldError]` envelope across every flavor"); this card ships criterion
  6's `ModelSerializer` flavor — the last of the three named flavors to land — closing
  the write-side parity story.

## Slice checklist

Each top-level item maps to one commit / PR. **Four slices: serializer-field
converter + input generation (Slice 1), the base class (Slice 2), the resolver pipeline
**+ the products live serializer surface, landed together** (Slice 3), and the docs +
soft-dep wiring + card wrap (Slice 4).** Slices 1–2 are package-internal and staged
(each builds on the prior); **Slice 3 lands the resolver and its live consumer surface
in one commit** — required by the [`examples/fakeshop/test_query/README.md`][test-query-readme]
#"Coverage rule." live-first mandate, so the resolver's reachable lines are earned by a
real `/graphql/` request (not a package test) at the commit they appear; Slice 4 is
doc + soft-dep + card-wrap only (no version bump — [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).

- [ ] Slice 1: DRF-field → Strawberry input mapping + the serializer-derived input
  generator (per
  [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)
  / [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy))
  - [ ] [`rest_framework/serializer_converter.py`][rf-converter]: a
    `convert_serializer_field(field)` registry (the graphene-django
    [`convert_serializer_field`][upstream-serializer-converter] parity shape)
    returning the Strawberry annotation + required-ness for each supported DRF
    serializer-field class (`CharField` / `ChoiceField` → `str`, `IntegerField` →
    `int`, `BooleanField` → `bool`, `FloatField` → `float`, `DecimalField` →
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
    generated input field, the `input_attr → (serializer_field_name, source, kind)`
    reverse map (`kind ∈ {scalar, relation_single, relation_multi, file}`) the resolver
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
    name-only `036` / `038` key): the ordered tuple of each emitted field's
    `(input_attr, GraphQL annotation, required/default, serializer_field_name, source,
    kind)` plus the normalized `optional_fields` set for create, so two same-name-set
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
    serializer field; waived (`guard_required=False`) when the mutation overrides
    `get_serializer_kwargs` to inject the values (the [`forms/inputs.py`][forms-inputs]
    `guard_create_required_fields` + [`forms/sets.py`][forms-sets] per-declaration
    precedent). Reuse [`utils/inputs.py`][utils-inputs]'s `build_strawberry_input_class`
    + `materialize_generated_input_class` core (the latter's ledger gives the collision
    raise for free) and materialize as module globals of the `rest_framework` input
    namespace for the [`strawberry.lazy`][glossary-djangomutationfield] forward-ref.
    Normalize + fail-loud `Meta.fields` / `Meta.exclude` against the serializer's
    field set (bare string, duplicates, unknown names, empty effective set →
    `ConfigurationError`, mirroring `036`'s `_normalize_field_sequence` and `038`'s
    form normalization).
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
    [`ConfigurationError`][glossary-configurationerror], `read_only` / `HiddenField`
    exclusions do **not**, and the `get_serializer_kwargs` waiver
    (`guard_required=False`) suppresses it; the guard runs **per declaration** (a waiving
    mutation materializing a shape first does not suppress it for a later non-waiving
    mutation on the same shape).
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
    allowed-key set **adds** `serializer_class` / `optional_fields`, **keeps**
    `operation` / `fields` / `exclude` / `permission_classes` (the `036` write-auth seam
    is inherited unchanged, [Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelserializer);
    matching the form flavor's [`forms/sets.py`][forms-sets] allowed-key set, which also
    keeps `permission_classes`), and **drops** `model` / `input_class` /
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
    the [`forms/inputs.py`][forms-inputs] `clear_form_input_namespace` precedent) called
    in **two** places — the [`forms/inputs.py`][forms-inputs] / [`mutations/inputs.py`][mutations-inputs]
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
       that same pre-bind block, not a per-pass clear. **The call must be
       import-guarded — it is *not* a literal mirror of the mutation / form clears.**
       [`forms/inputs.py`][forms-inputs] / [`mutations/inputs.py`][mutations-inputs] are
       always importable, so the finalizer calls `clear_mutation_input_namespace()` /
       `clear_form_input_namespace()` **directly and unconditionally**
       ([`types/finalizer.py`][types-finalizer] #"clear_mutation_input_namespace"). But
       `rest_framework/inputs.py` lives **behind the DRF soft-import guard**, and
       [`finalize_django_types`][glossary-finalize_django_types] runs on **every** schema
       build — including for the read / model / form consumers who never install DRF
       (Goal 6: "the package imports without DRF"). A direct `from ..rest_framework.inputs
       import clear_serializer_input_namespace` would raise `ImportError` and **break
       schema construction for everyone without DRF**. So the pre-bind serializer clear
       runs **import-guarded** — a `try/except ImportError`, or the same
       `_clear_if_importable(...)` shape place #2 uses — exactly the asymmetry place #2
       already encodes (a `_clear_if_importable` row, not a direct call). The guard is also
       semantically exact: DRF absent ⇒ no [`SerializerMutation`][glossary-serializermutation]
       can be declared ⇒ the serializer ledger is necessarily empty ⇒ a skipped clear is a
       correct no-op.
    2. **`TypeRegistry.clear()`** — added as a `_clear_if_importable(
       "django_strawberry_framework.rest_framework.inputs",
       "clear_serializer_input_namespace", …)` co-clear row alongside the existing
       mutation / form co-clears, so a full registry reset wipes serializer inputs too.

    **No new bind entry point** (no `bind_serializer_mutations()`) — that is the dividend
    of the `ModelSerializer`-rides-`DjangoMutation` choice
    ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).
  - [ ] [`__init__.py`][init]: export `SerializerMutation` (one net-new public symbol)
    via a **root-level `__getattr__`** (PEP 562) — `SerializerMutation` is added to
    `__all__` but **not** eagerly imported, so `import django_strawberry_framework`
    succeeds without DRF and resolving the name lazily routes through the shared
    `require_drf()` guard (DRF absent → `ImportError` with the install hint). This is the
    one root edit; the eager-import + explicit-`__all__` style of the existing root is
    otherwise preserved
    ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
  - [ ] Package coverage: [`tests/rest_framework/test_sets.py`][test-rest-framework] —
    the `Meta` validation matrix (missing / wrong-type `serializer_class`, a plain
    `Serializer` with no model rejected, `ModelSerializer`-with-no-model,
    `operation = "delete"` rejected, `serializer_class` accepted as a known key,
    `fields` + `exclude` both set, unknown key), registration, finalizer binding (the
    `bind_mutations()` path), the no-registered-primary-type error, and — proving the
    base is unregressed — the model-flavor seam defaults unchanged.
- [ ] Slice 3: the serializer resolver pipeline **+ the products live serializer
  surface, landed in one commit** (per
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)
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
    model-attr-keyed `036` `_decode_relation_id_set`): each relation id — `GlobalID`
    *or* **raw pk** — is type-checked against the relation's target model (resolved from
    the backing FK via the serializer field's `source`,
    [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)),
    resolved to the **visible** object through the related primary
    `DjangoType.get_queryset` — the same per-branch raw-pk visibility check both
    `036`'s model-path decoder (`_decode_relation_id_set` → `_raw_pk_relation_error`)
    and the `038` form decoder (`_visible_related_object`) already enforce — and reduced
    to the pk DRF expects for a `PrimaryKeyRelatedField` before landing under the
    serializer field name; a hidden target → field-keyed `FieldError`; a serializer `FileField` /
    `ImageField` value (an [`Upload`][glossary-upload-scalar]) is routed into the
    serializer's `data` like any other value (DRF serializers read files from `data`,
    unlike Django forms which split `files=`); **construct** the serializer via the
    overridable `get_serializer_kwargs(info, *, data, instance=None)` hook (the graphene
    `get_serializer_kwargs` parity seam) — create:
    `serializer_class(**get_serializer_kwargs(info, data=provided_data))`; **update
    (partial):** `serializer_class(**get_serializer_kwargs(info, data=provided_data,
    instance=<row>))` with **`partial=True`** injected (DRF's native partial-update —
    no full-payload reconstruction needed, the divergence from `038`'s form
    reconstruction); inject `context={"request": request_from_info(info,
    family_label="SerializerMutation")}` (the package's shared request-extraction
    helper, [`utils/permissions.py`][utils-permissions]) so the serializer's own
    validators / `HiddenField(default=CurrentUserDefault())` resolve;
    **validate** via `serializer.is_valid()` — a failure maps the nested
    `serializer.errors` onto the [`FieldError` envelope][glossary-fielderror-envelope]
    via a **dedicated recursive flattener** (`serializer_errors_to_field_errors`, dotted
    path `items.0.name`, DRF's `non_field_errors` / `NON_FIELD_ERRORS_KEY` bucket → the
    `"__all__"` sentinel `036` froze at every level — NOT the one-level `036`
    `validation_error_to_field_errors`) and returns a null-object payload; **write** via
    `serializer.save()`, **wrapped by the `036` `save_or_field_errors` `IntegrityError`
    → envelope mapper** in a **value-preserving closure** (the wrapper discards its
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
    and an **observable request-context path** — a `validate()` (or
    `HiddenField(default=CurrentUserDefault())`) that reads
    `self.context["request"].user`, proving the injected `context={"request": …}` lands.
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
    query shape** (assert the SQL keeps `select_related` / `prefetch_related`, no
    `.only(...)`).
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
- [ ] Slice 4: doc updates + soft-dep wiring + card wrap (per
  [Doc updates](#doc-updates) /
  [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)
  / [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut))
  - [ ] **Soft-dep wiring** ([`pyproject.toml`][pyproject] **+ `uv.lock`**): add
    `djangorestframework` to `[dependency-groups].dev` (NOT `[project].dependencies` —
    it stays a soft runtime dep), pinning a floor that matches the install hint the
    guard prints, and **regenerate `uv.lock`** (`uv lock`) so the committed lockfile
    matches the manifest. **No package-version edits** — the `[project].version` /
    `__version__` / `test_version` stay `0.0.12`, and so does the
    `django-strawberry-framework` `version` entry inside `uv.lock`
    ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
  - [ ] [`docs/GLOSSARY.md`][glossary] (promote
    [`SerializerMutation`][glossary-serializermutation] to `shipped (0.0.13)`; add it
    to **Public exports** + the **Index** status column + the **Mutations**
    browse-by-category row; reconcile the entry's surface keys with what this card
    actually pins — `Meta.operation` over `model_operations`, the `id:`-decode locate
    over `lookup_field`), [`docs/README.md`][docs-readme] / [`README.md`][readme]
    (move the serializer flavor from "Coming next (`0.0.13`)" to "Shipped today" in
    the "Coming from DRF + django-filter?" paragraph; the README **Status** line moves
    to `0.0.13` only at the joint cut, not here), [`GOAL.md`][goal] (criterion 6's
    `ModelSerializer` flavor now ships — all three named flavors shipped),
    [`TODAY.md`][today] (note the serializer mutation as a package capability),
    [`docs/TREE.md`][tree] (fill the planned `rest_framework/` /
    [`tests/rest_framework/`][test-rest-framework] summary lines), [`CHANGELOG.md`][changelog]
    (only if the Slice 4 maintainer prompt explicitly requests it), [`KANBAN.md`][kanban]
    (card → Done via the kanban DB + re-render).

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
  does **not** move them — the joint `0.0.13` cut shared with [`TODO-ALPHA-040-0.0.13`][kanban]
  owns the bump ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
- **`0.0.13` has two cards.** `039` (this card) and `040` ([Auth mutations][glossary-auth-mutations])
  both target `0.0.13`; there is a joint cut to defer the version bump to. (The
  [`KANBAN.md`][kanban] `## In progress` column is empty as this spec is authored;
  `039` is the lowest-NNN card in the active To-Do / Alpha column and is the
  next-up spec target — recorded in [Risks](#risks-and-open-questions).)
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
3. **Reuse the frozen `FieldError` envelope.** Map `serializer.errors` (and DRF's
   `non_field_errors` bucket) onto the byte-identical
   [`FieldError`][glossary-fielderror-envelope] envelope `036` defined
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)).
4. **Run the write through the serializer.** `serializer.is_valid()` →
   `serializer.save()`, sync and async, inside the one-`transaction.atomic()` boundary
   `036` / `038` set; the payload's object is re-fetched and optimizer-planned for the
   response selection
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)
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
   [`tests/base/test_init.py::test_version`][test-base-init] — these stay `0.0.12` until
   the joint cut. `uv.lock` **is** updated in Slice 4 (regenerated for the
   `[dependency-groups].dev` DRF add), but its `django-strawberry-framework` package
   `version` entry stays `0.0.12` — the lockfile's dependency graph changes, the package
   version does not ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).

## Non-goals

- **Auth mutations.** [Auth mutations][glossary-auth-mutations] (`login` / `logout` /
  `register` + `current_user`, `0.0.13`, [`TODO-ALPHA-040-0.0.13`][kanban]) are
  separately carded; they share the joint cut and reuse the same envelope but ship
  independently ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Changing the `036` model-driven generator, the `038` form generator, or the
  `FieldError` envelope.** The frozen contracts are reused **unchanged**; this card
  adds no field to [`FieldError`][glossary-fielderror-envelope], does not re-open
  [`mutations/inputs.py`][mutations-inputs] or [`forms/inputs.py`][forms-inputs], and
  needs no edit to [`mutations/fields.py`][mutations-fields]
  ([Decision 2](#decision-2--card-scope-boundary-the-serializer-flavor-ships-auth-stays-out-the-frozen-036-contracts-and-the-038-factory-are-reused-unchanged)).
- **A model-less plain `Serializer` flavor.** `0.0.13` ships the
  `ModelSerializer`-driven contract (a resolvable model, the uniform `node` / `result`
  slot); a plain model-less `serializers.Serializer` is deferred
  ([Risks](#risks-and-open-questions); the [`DjangoFormMutation`][glossary-djangoformmutation]
  model-less sibling is the fallback shape if demanded).
- **Serializer-derived output types / nested writable serializers.** The mutation
  **output** is the primary [`DjangoType`][glossary-djangotype] in the frozen
  `node` / `result` slot — **not** a serializer-derived output type (the card's
  "dual-purposed for inputs and outputs" wording is reconciled to the frozen slot,
  [Risks](#risks-and-open-questions)); nested writable serializers (`ParsedObject`-style
  nested create / connect) stay the `036` nested-write non-goal
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Serializer `delete`.** DRF serializers do not delete; a `delete` write stays the
  model-driven [`DjangoMutation`][glossary-djangomutation] (`Meta.operation =
  "delete"`) the consumer already has
  ([Decision 10](#decision-10--operations-create--update-no-serializer-delete)).
- **graphene's `Meta.model_operations` runtime dispatch and `Meta.lookup_field`
  non-pk locate.** Not adopted verbatim; the package's per-operation `Meta.operation`
  and `id:`-decode locate supersede them
  ([Decision 10](#decision-10--operations-create--update-no-serializer-delete) /
  [Risks](#risks-and-open-questions)).
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
| [`ErrorType.from_errors(serializer.errors)`][upstream-serializer-mutation] on the payload | `serializer.errors` → the frozen [`FieldError` envelope][glossary-fielderror-envelope], `non_field_errors` → the `"__all__"` sentinel ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)) | this card — reuse the `036`-frozen envelope, byte-identical |
| graphene `SerializerMutation` output fields built from the serializer (`is_input=False`) | the primary [`DjangoType`][glossary-djangotype] in the uniform `node` / `result` slot — **not** a serializer-derived output type ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)) | deliberate non-adoption (card-body "dual-purpose" tension, [Risks](#risks-and-open-questions)) |
| graphene `Meta.model_operations = ["create", "update"]` (runtime-dispatched per mutation) | per-operation `Meta.operation ∈ {"create", "update"}` (one mutation per op, the package convention) ([Decision 10](#decision-10--operations-create--update-no-serializer-delete)) | deliberate non-adoption (card-body tension, [Risks](#risks-and-open-questions)) |
| graphene `Meta.lookup_field` (non-pk update locate) + `get_object_or_404` | the `id:` `GlobalID` server-side decode → target `get_queryset` locate ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)) | deliberate non-adoption (card-body tension, [Risks](#risks-and-open-questions)) |
| graphene `Meta.optional_fields` (force specific fields optional) | `Meta.optional_fields` adopted as a force-optional override on the serializer-derived input ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)) | this card — adopted (clean semantics) |
| graphene relation visibility (none — serializer's own queryset only) | every relation id (Relay + raw pk) visibility-checked through the related primary `get_queryset` before the serializer ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)) | package security invariant beyond graphene parity (mirrors the per-branch visibility check `036`'s model path and `038`'s form path already enforce, raw pk included) |
| graphene [`get_serializer_kwargs(cls, root, info, **input)`][upstream-serializer-mutation] (classmethod constructor-kwarg seam) | `get_serializer_kwargs(info, *, data, instance=None)` hook (defaults the package kwargs + `context={"request": …}` + `partial=True` on update) ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)) | this card — **name-borrowed** seam, not signature-compatible (the graphene signature differs; an existing graphene override can't carry over verbatim — a crit-7 "Meta mental model carries over" wrinkle, not a drop-in) |
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
  `036`-frozen [`FieldError`][glossary-fielderror-envelope].

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
  reused unchanged.

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
update — a DRF behavior pinned to the verified floor, [Risks](#risks-and-open-questions)). Write authorization is the inherited
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
  top-level error ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)
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

The spec file lives at **`docs/spec-039-serializer_mutations-0_0_13.md`** (this
document), at the `docs/` top level per the [`docs/SPECS/NEXT.md`][next] Step 6
convention; the [`docs/SPECS/NEXT.md`][next] Step 8 archive sweep leaves it there
(it is the only / active spec at `docs/` top-level — every prior spec is already
archived under `docs/SPECS/`).

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in
  [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN (`039`) and target patch
  (`0_0_13`) into the filename.
- The topic slug is `serializer_mutations` — short, snake-case, and naming the
  subsystem (the stem of the card DoD's suggested `docs/spec-serializer_mutations.md`).

Alternatives considered (and rejected):

- **The card's own `docs/spec-serializer_mutations.md`.** Rejected: predates the
  structured-filename convention; [`spec-036`][spec-036] / [`spec-038`][spec-038]
  Decision 1 set the precedent of preferring the structured name and recording the
  card's older one (carried in [Risks](#risks-and-open-questions)).
- **Topic slug `serializers` / `drf` / `rest_framework`.** Rejected: `serializers`
  collides conceptually with the DRF `serializers` module name; `drf` / `rest_framework`
  name the dependency, not the subsystem capability (the mutation flavor).

### Decision 2 — Card-scope boundary: the serializer flavor ships; auth stays out; the frozen `036` contracts and the `038` factory are reused unchanged

This card ships the **serializer-validated** write flavor end-to-end: the
[`SerializerMutation`][glossary-serializermutation] base, the serializer-field → input
mapping, the `is_valid()` → `serializer.errors` → `save()` pipeline, and the products
live serializer surface. It explicitly does **not** ship the adjacent flavor, owned by
the sibling joint-cut card:

- **Auth mutations** ([Auth mutations][glossary-auth-mutations]) —
  [`TODO-ALPHA-040-0.0.13`][kanban].

And it **reuses, byte-identical, the contracts [`spec-036`][spec-036] froze for exactly
this and [`spec-038`][spec-038] proved reusable**: the
[`FieldError` envelope][glossary-fielderror-envelope], the `<Name>Payload` wrapper
(uniform `node` / `result` slot), the [`DjangoMutationField`][glossary-djangomutationfield]
factory (already generalized by `038` — **no edit needed**), the
[`DjangoModelPermission`][glossary-djangomodelpermission] / `Meta.permission_classes`
/ `check_permission` write-auth seam, and the [`_resolve_model`][spec-036] /
`_validate_meta` / `build_input` / `input_type_name` / `input_module_path` /
`resolve_*` seam set. This card adds **no** field to
[`FieldError`][glossary-fielderror-envelope] and does not re-open the `036` /
`038` input generators (the serializer generator is a separate module).

Justification: the card is sized **L** and auth is separately carded with its own
`0.0.13` target — pulling it forward would bloat the slice exactly as
[`START.md`][start]'s scope-creep rule warns. The foundation and the form-flavor
precedent already exist; this card's job is the serializer-specific generation +
pipeline on top of them. This is the third and last of the three flavors
[`spec-036`][spec-036] Decision 2 named as the envelope's reusers (`038` form, `039`
serializer, `040` auth).

Alternatives considered (and rejected):

- **Ship auth mutations too** (they also reuse the envelope). Rejected: auth is its
  own `0.0.13` card with a distinct surface (`login` / `logout` / `register` +
  `current_user`, composing with `django.contrib.auth`), not a serializer-flavor
  concern.
- **Extend the `036` `FieldError` with serializer metadata.** Rejected: the card
  mandates the envelope is **reused unchanged**; forking it would break the
  one-contract promise.

### Decision 3 — `class Meta` surface, not graphene's `MutationOptions`

A serializer mutation is a **base class with a nested `class Meta`**
(`serializer_class` + `operation` + optional `fields` / `exclude` / `optional_fields`),
declared exactly like every other consumer surface in the package. It is **not**
graphene's `SerializerMutationOptions` / `__init_subclass_with_meta__(serializer_class=…,
model_class=…, lookup_field=…)` keyword-options flow, and **not** a `ClientIDMutation`
lineage.

Justification: this is the package's defining surface contract, stated verbatim in
[`START.md`][start] ("Meta classes everywhere on consumer surfaces"). The
[`spec-036`][spec-036] [`DjangoMutation`][glossary-djangomutation] base and the
[`spec-038`][spec-038] form bases already established the nested-`Meta` mutation shape;
the serializer flavor is uniform with them (and with [`DjangoType`][glossary-djangotype]
/ [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset]). The
*capabilities* of graphene-django's `SerializerMutation` are borrowed at the outcome
level; the `MutationOptions` / `ClientIDMutation` mechanism is not. [`GOAL.md`][goal]'s
DRF-migration diff spells the surface as
`class CreateCategoryFromSerializer(DjangoMutation): class Meta: serializer_class = …`;
the card ships the **`SerializerMutation` base** instead (for the by-name
`graphene-django` migration carry-over weighed in
[Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)),
and Slice 4 updates that GOAL.md example to the shipped base so the two stop disagreeing
in print.

Alternatives considered (and rejected):

- **graphene's `__init_subclass_with_meta__` keyword options.** Rejected: it is the
  metaclass-options surface the nested `class Meta` replaces; it also fragments the
  declaration shape away from [`DjangoMutation`][glossary-djangomutation].
- **A `@serializer_mutation(serializer_class=…)` decorator.** Rejected: a decorator on
  a consumer class is exactly the shape [`START.md`][start] forbids.

### Decision 4 — Module and test locations: `rest_framework/` subpackage mirroring `forms/`

- **Source:** `django_strawberry_framework/rest_framework/` — the subpackage
  [`docs/TREE.md`][tree]'s target layout reserves, split in the spirit of the
  [`forms/`][forms-sets] subpackage (its structural twin): `serializer_converter.py`
  (the DRF-field → annotation registry, the card DoD's named module), `inputs.py`
  (the serializer-derived input + the namespace materialization), `sets.py`
  (`SerializerMutation` + `Meta` validation + the seam overrides), and `resolvers.py`
  (the serializer pipeline). It reuses [`mutations/`][mutations-fields]'s
  [`DjangoMutationField`][glossary-djangomutationfield] and
  [`FieldError`][glossary-fielderror-envelope] rather than re-declaring them.
- **Tests:** new [`tests/rest_framework/`][test-rest-framework] mirroring the source
  modules (`test_converter.py` / `test_inputs.py` / `test_sets.py` / `test_resolvers.py`);
  live coverage extends [`test_products_api.py`][test-products-api].

Justification: the card predicts `django_strawberry_framework/rest_framework/` and
[`tests/rest_framework/`][test-rest-framework]; the [`forms/`][forms-sets] subpackage
([`spec-038`][spec-038] Decision 4) is the proven shape for a flavor reusing the
mutation base — and `rest_framework/` is its near-exact structural twin (a converter +
an input generator + a metaclass-or-subclass + a resolver pipeline). A separate
subpackage keeps the serializer-specific generation + pipeline cleanly distinct and
behind one DRF soft-import boundary
([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
The directory name `rest_framework/` matches the card prediction and graphene-django's
own `rest_framework/` subpackage. **One cost is worth naming:** because
`django_strawberry_framework.rest_framework` shares its leaf name with DRF's own
top-level `rest_framework` package, the absent-DRF test must evict **both** `rest_framework*`
**and** `django_strawberry_framework.rest_framework*` from `sys.modules` (the two-namespace
eviction dance in
[Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
That test-complexity is a **direct consequence of the name**, accepted here for the card +
graphene-django parity — a future reader seeing the double eviction should know it traces
to this naming choice, not to an accident of the guard.

Alternatives considered (and rejected):

- **Fold the serializer base into [`mutations/`][mutations-sets] or
  [`forms/`][forms-sets].** Rejected: the card predicts a `rest_framework/` subpackage,
  the serializer-field converter is a distinct concern, and the DRF soft-import
  boundary wants its own module wall — one subpackage per flavor keeps each extension
  point separable (the `036` / `038` precedent).
- **A flat `rest_framework.py` module.** Rejected: the surface is a converter + an
  input generator + a base + a resolver pipeline — a subpackage matches it, and the
  card predicts `rest_framework/`.
- **Name it `serializers/` instead of `rest_framework/`.** Rejected: the card predicts
  `rest_framework/`, it matches graphene-django's layout, and it names the dependency
  boundary the soft-import guard wraps.

### Decision 5 — Public surface: `SerializerMutation` exported from the root, the `038`-generalized factory reused

One net-new public symbol, re-exported from [`__init__.py`][init] and added to
`__all__`:

- `SerializerMutation` — the `ModelSerializer` mutation base.

No net-new field factory or error type: the flavor is exposed through the **existing**
[`DjangoMutationField`][glossary-djangomutationfield] and returns the frozen
[`FieldError`][glossary-fielderror-envelope] envelope. Critically — unlike
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

Justification: keeping the public surface at one symbol (the base) — reusing the field
factory + error type rather than a parallel factory — honors the one-shared-contract
promise and lets the `038` generalization pay off exactly as designed. The base + the
seam set are the irreducible new surface.

Alternatives considered (and rejected):

- **A net-new `DjangoSerializerMutationField` factory.** Rejected: the `038`-generalized
  [`DjangoMutationField`][glossary-djangomutationfield] already exposes any
  mutation-family member; a parallel factory would duplicate the dispatch + ref logic
  for no gain (it was the explicit `038` fallback, not needed because the generalization
  shipped).
- **Exporting from a `django_strawberry_framework.rest_framework` namespace only.**
  Rejected: the symbol is used inside schema modules alongside root-exported
  [`DjangoMutation`][glossary-djangomutation] / [`DjangoModelFormMutation`][glossary-djangomodelformmutation],
  so it belongs at the root next to its sibling flavor bases (the `036` / `038`
  precedent) — guarded so the root import survives DRF's absence
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).

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
`Serializer` flavor is demanded ([Risks](#risks-and-open-questions)).

Justification: this is the exact shape [`DjangoModelFormMutation`][glossary-djangomodelformmutation]
proved in `038`, and the [`_resolve_model`][spec-036] seam was frozen in `036`
"for the `0.0.13` serializer flavor (`Meta.serializer_class.Meta.model`)". Riding the
base maximizes reuse (permission, locate, re-fetch, payload, bind all come free) and
keeps the serializer flavor uniform with the form flavor. A **dedicated
[`SerializerMutation`][glossary-serializermutation] base** (rather than teaching
[`DjangoMutation`][glossary-djangomutation] itself to detect `serializer_class` — the
shape [`GOAL.md`][goal]'s crit-6 example literally shows) also buys the strongest
**crit-7 migration ergonomics**: a `graphene-django` serializer-mutation consumer
already writes `class FooMutation(SerializerMutation): ...`, so exporting a
`SerializerMutation` base lets that declaration carry over **by name** — only the import
line changes ([`GOAL.md`][goal] crit 7), strictly better than GOAL's literal
`DjangoMutation` shape. GOAL.md's crit-6 example currently depicts the `DjangoMutation`
base; Slice 4 reconciles it to this shipped base so the north star stops advertising a
declaration that will not dispatch.

Alternatives considered (and rejected):

- **`DjangoMutation` itself detects `Meta.serializer_class`** (no dedicated
  `SerializerMutation` base — the literal shape [`GOAL.md`][goal]'s crit-6 example shows,
  `class CreateCategoryFromSerializer(DjangoMutation): class Meta: serializer_class = …`).
  Rejected: it forfeits the by-name `graphene-django` migration carry-over above (a
  migrant's `class FooMutation(SerializerMutation)` would have to be rewritten to
  `(DjangoMutation)`), and folds serializer-specific `Meta` validation / `build_input`
  branching into the model-driven base's hot path instead of isolating it in a subclass.
  The base is reused **by subclassing**, not by overloading one class with both flavors.
  Slice 4 updates GOAL.md's example to the `SerializerMutation` base.
- **A standalone `SerializerMutation` not subclassing `DjangoMutation`** (its own
  metaclass + registry + bind, the model-less [`DjangoFormMutation`][glossary-djangoformmutation]
  shape). Rejected for the `ModelSerializer`-driven contract: it would re-implement the
  permission / locate / re-fetch / payload the base already provides; the model-less
  sibling shape is reserved for the deferred plain-`Serializer` flavor.
- **Supporting both `ModelSerializer` and plain `Serializer` in `0.0.13`** (graphene's
  single `SerializerMutation` handles both via `model_class=None`). Rejected: it
  doubles the surface (two payload shapes, two bind paths) for a rare case; the
  `ModelSerializer` flavor is the headline and the `038` form card already
  established the two-flavor split lands across cards, not within one.

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
([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload))
is a **distinct** seam — it shapes the *runtime* serializer (`data` / `instance` /
`context`) and cannot substitute for schema-time discovery, because finalization
precedes the first request.

**The converter is fail-loud (the [`forms/converter.py`][forms-converter] discipline,
diverging from graphene).** Dispatch is a `type(field).__mro__` walk over an
individually-registered registry with a **raising fallthrough** — **not**
`functools.singledispatch` with the graphene-django `serializers.Field → String`
catch-all (which would shadow the raise so every custom serializer field silently
became `String`, losing the `ImproperlyConfigured` parity). Relation / file kinds are
matched first by `isinstance` (`PrimaryKeyRelatedField` / `ManyRelatedField`,
`FileField` / `ImageField`), then the scalar registry MRO walk, then a raising
default. **This fail-loud posture — and the explicit relation / file rows in particular —
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

- `CharField` (and `EmailField` / `SlugField` / `URLField` / `RegexField` via MRO) →
  `str`; `ChoiceField` → `str` (model-less default; over a `ModelSerializer` column's
  `choices`, routed through the read-side [enum][glossary-choice-enum-generation] at
  the build site).
- `IntegerField` → `int`, `FloatField` → `float`, `DecimalField` → `Decimal`,
  `BooleanField` → `bool`, `UUIDField` → `uuid.UUID`.
- `DateField` / `DateTimeField` / `TimeField` → Python-native.
- `JSONField` → `strawberry.scalars.JSON`; `ListField` → `list[<scalar child>]` — the
  `child` is converted **recursively through the same scalar registry**
  (`ListField(child=IntegerField())` → `list[int]`); a `ListField` whose `child` is a
  **relation field or a (nested) serializer** is **out of scope** →
  [`ConfigurationError`][glossary-configurationerror] naming the field (a relation list is
  expressed via `ManyRelatedField` / `PrimaryKeyRelatedField(many=True)`, and a nested
  serializer is the `036` nested-write non-goal — a `ListField` must not become a
  back-door to either). `MultipleChoiceField` → `list[str]`.
- `PrimaryKeyRelatedField` → the target's id (`relation_single`), `many=True` /
  `ManyRelatedField` → `list[<id>]` (`relation_multi`); the id type is the target
  primary [`DjangoType`][glossary-djangotype]'s `GlobalID` (Relay-Node) or raw pk,
  resolved at the build site.
- `FileField` / `ImageField` → [`Upload`][glossary-upload-scalar] (`file`).
- A nested `ModelSerializer` / `ListSerializer` field → **out of scope**
  (the `036` nested-write non-goal), surfaced as a `ConfigurationError` (nested writes
  are not supported in `0.0.13`).

**Where a serializer field overlaps a model column, reuse the read-side converters.**
A `ModelSerializer` field backed by a `choices` column resolves to the SAME generated
enum the read [`DjangoType`][glossary-djangotype] synthesizes (the symmetric wire
contract), via the read-side [scalar][glossary-scalar-field-conversion] /
[choice-enum][glossary-choice-enum-generation] registry keyed on the **backing**
`models.Field` — resolved from the serializer field's `source` (**Renamed fields**
below), not its declared name — exactly the [`forms/inputs.py`][forms-inputs]
discipline. The two key spaces (`serializers.Field` in the converter, `models.Field` on
the read side) stay strictly separate.

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
  already id-like** (`*_id` / `*_pk` / `*Id` / `*Pk`); an already-id-like name is just
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
  any field that needs model-column conversion (a relation, or a `choices`-enum
  overlap): a [`ConfigurationError`][glossary-configurationerror] naming the field,
  since the backing column is not a single resolvable `models.Field`. A plain scalar
  serializer-only field (no model-column conversion) is unaffected — it is a scalar
  input validated by the serializer, keyed by its declared name.

**Requiredness, `read_only`, `optional_fields`.** A create-input field's requiredness
is the serializer field's `field.required`, minus the `Meta.optional_fields` override
(graphene's `force_optional`); a `read_only=True` field and a `HiddenField` are
**dropped from the input** (graphene's `fields_for_serializer` `is_input` rule — a
read-only / hidden field is server-supplied, not client input). `<Serializer>PartialInput`
is every input field optional.

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
`Meta.return_field_name`), recorded in [Risks](#risks-and-open-questions). An `is_input`
parameter is carried on `convert_serializer_field`'s **signature** for graphene-parity and
forward use, but it is **accepted-and-ignored — there is no `if not is_input:` branch** in
`0.0.13`: the converter is input-directed and `is_input` never alters control flow, so it
leaves **no uncovered branch** under `fail_under = 100` (a merely-threaded parameter is
free; a dead `is_input=False` branch would gate-fail). A future serializer-derived output
direction adds the branch **and** its coverage together.

**Reverse map.** Record, per generated input field, an
`input_attr → (serializer_field_name, source, kind)` reverse map (the `038`
`FormInputFieldSpec` analog, **plus the `source` axis** Django form fields lack — see
**Renamed fields** above; `kind ∈ {scalar, relation_single, relation_multi, file}`) so
[`rest_framework/resolvers.py`][rf-resolvers] builds a payload keyed by the **declared
serializer field name** (`categoryId` → `category`; a renamed `categoryPk` →
`category_pk`), which DRF maps to `source` internally.

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
identity is a **`SerializerInputShape` descriptor**: the ordered tuple of each emitted
field's `(input_attr, GraphQL annotation, required/default state, serializer_field_name,
source, kind)`, with the normalized `optional_fields` set folded into the create
descriptor. The **same descriptor** drives the per-shape **bind/build cache**, the
**generated-name derivation**, and the **materialization collision check** — one source
of truth.

**Naming + dedupe.** The canonical `<Serializer>Input` / `<Serializer>PartialInput`
names the **default full shape** (all input fields, default requiredness, no
`optional_fields`); any shape that differs (narrowed by `Meta.fields` / `Meta.exclude`,
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
shape-cache lookup** (the cache key is the descriptor, which excludes the waiver flag —
exactly the form discipline), so a waiving mutation that materializes a narrowed shape
first cannot suppress the guard for a later non-waiving mutation reusing the cached
shape. The **waiver** is explicit: a mutation that overrides `get_serializer_kwargs(...)`
to inject the missing values builds with `guard_required=False` (the form
`get_form_kwargs` / `get_form` waiver precedent). Update inputs need no such guard — DRF
`partial=True` makes every field optional, so a dropped field is simply un-validated.

Justification: deriving the input from the serializer's fields is the card's headline
parity item and the only way a serializer's declared / renamed / extra fields reach the
write surface; reusing the read-side converters keeps the symmetric wire contract; the
fail-loud converter matches the package's own [`forms/converter.py`][forms-converter]
posture; the shape-identity + materialize-before-`Schema` discipline is the proven
set-family lifecycle.

Alternatives considered (and rejected):

- **Reuse the `036` model-column generator** (derive the input from `Meta.model`, not
  the serializer). Rejected: a serializer may declare fields a model lacks, rename
  fields, mark columns read-only, or narrow — the input must be the serializer's
  contract, exactly the `038` form-derived precedent.
- **graphene's `singledispatch` + `Field → String` catch-all.** Rejected: the
  catch-all shadows the raise so an unmapped field silently becomes `String`; the
  fail-loud MRO walk is the package's settled discipline.
- **Build a serializer-derived output type** (`is_input=False`). Rejected: the frozen
  uniform `node` / `result` slot is the one cross-flavor output contract; a
  serializer-derived output would fork it.

### Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `serializer.errors` → `save()` → optimizer re-fetch → payload

[`rest_framework/resolvers.py`][rf-resolvers] runs the sync + async pipeline, reusing
the `036` / `038` promoted helpers (`locate_instance` / `coerce_lookup_id` /
`authorize_or_raise` / `refetch_optimized` / `build_payload` / `not_found_error` /
`save_or_field_errors`) by call, not re-implementation:

1. **Locate** (`update` only): coerce the top-level `id:` `GlobalID` and resolve the
   row through the target type's [`get_queryset`][glossary-get_queryset-visibility-hook]
   (a miss / hidden row → a not-found `FieldError` on `id`, no existence leak). `create`
   has no instance lookup. This is the **only** decode that precedes authorization, and
   it is a `GlobalID` decode of the mutation's *own* `id:` argument — never a relation
   visibility probe.
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
   ([`forms/resolvers.py`][forms-resolvers] `_run_modelform_pipeline_sync` #"Authorize
   BEFORE decoding relations": *"the decode issues visibility-scoped `get_queryset`
   queries, so running it pre-auth would let an unauthorized caller probe related-object
   visibility by id … Matches the `036` model path's locate → authorize → decode
   order"*); the serializer pipeline obeys the same **locate → authorize → decode**
   order.
3. **Decode** the (now-authorized) `data:` input via the reverse map into a
   serializer-field-keyed `provided_data`, using a **dedicated serializer relation
   decoder** that mirrors the `038` form decoder (serializer-field-keyed, NOT the
   model-attr-keyed `036` `_decode_relation_id_set`): each relation id — `GlobalID` *or*
   **raw pk** — is type-checked against the relation's target model (resolved from the
   backing FK via the serializer field's `source`,
   [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)),
   resolved to the **visible** object through the related primary
   `DjangoType.get_queryset` — the same per-branch raw-pk visibility check both `036`'s
   model-path decoder (`_decode_relation_id_set` → `_raw_pk_relation_error`) and the
   `038` form decoder (`_visible_related_object`) already enforce — and reduced to the
   **pk** DRF's `PrimaryKeyRelatedField` expects before landing under the **serializer
   field name** (the public `data` key DRF maps to `source` internally,
   [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
   a hidden / wrong-type target → field-keyed
   [`FieldError`][glossary-fielderror-envelope]. A `FileField` / `ImageField` value
   (an [`Upload`][glossary-upload-scalar]) lands in `provided_data` like any other
   value — DRF serializers read files from `data`, the deliberate contrast with the
   `038` form flavor's `data=` / `files=` split (a bound Django form reads files from
   `files=`).
4. **Construct** the serializer via the overridable
   `get_serializer_kwargs(info, *, data, instance=None)` hook (the graphene
   `get_serializer_kwargs` parity seam) — `create`:
   `serializer_class(**get_serializer_kwargs(info, data=provided_data))`; `update`:
   `serializer_class(**get_serializer_kwargs(info, data=provided_data,
   instance=<row>))` with **`partial=True`** injected. The default kwargs inject
   `context={"request": request_from_info(info, family_label="SerializerMutation")}` —
   the package's shared request-extraction helper
   ([`utils/permissions.py`][utils-permissions] `request_from_info`, which resolves both
   `info.context.request` and a bare `HttpRequest` `info.context`, the same helper the
   permission seam uses) — so the serializer's own validators and
   `HiddenField(default=CurrentUserDefault())` resolve.
5. **Validate** via `serializer.is_valid()` — a failure maps the nested
   `serializer.errors` structure onto the
   [`FieldError` envelope][glossary-fielderror-envelope] via a **dedicated recursive
   serializer-error flattener** (DRF's `non_field_errors` /
   `api_settings.NON_FIELD_ERRORS_KEY` bucket → the `"__all__"` sentinel `036` froze)
   and returns a null-object payload. `serializer.errors` is **not** the flat
   `field → [messages]` dict the `036` `validation_error_to_field_errors` handles — the
   flattener is spelled out below.
6. **Write** via `serializer.save()`, **wrapped by the `036` `save_or_field_errors`
   `IntegrityError` → envelope mapper** (no top-level error on a save-time race);
   `serializer.save()` runs `create()` / `update()` and handles M2M assignment
   internally (DRF's `ModelSerializer.save()` writes the instance + its relations).
   **The wrapper is value-preserving — the saved object is captured, not re-derived.**
   The `036` `save_or_field_errors(callable)` returns `list[FieldError] | None` and
   **discards the callable's return value** (it is shaped for the model / form paths,
   which already hold the instance). The serializer path needs the object DRF returns
   from `serializer.save()`, so the resolver captures it in the wrapped closure rather
   than re-deriving it (no second `serializer.save()`, no re-fetch from a stale
   `serializer.instance`):
   ```python
   saved = None
   def _do_save():
       nonlocal saved
       saved = serializer.save()   # called exactly once
   errors = save_or_field_errors(_do_save)
   ```
   The re-fetch (step 7) then keys off `saved.pk`. (`serializer.instance` *is* `saved`
   after a successful DRF `save()`, but pinning the captured return value keeps the
   contract explicit and the call-once guarantee testable.)
   **A save-time `ValidationError` is routed through the flattener, not raised.** DRF
   explicitly supports a custom `create()` / `update()` / `save()` raising
   `serializers.ValidationError` (and a model-level
   `django.core.exceptions.ValidationError` can surface from `save()` too). Left
   unhandled it would escape as a **top-level `GraphQLError`**, contradicting this card's
   own "validation → [`FieldError`][glossary-fielderror-envelope] envelope, not
   `GraphQLError`" contract ([Error shapes](#error-shapes)). So the resolver wraps the
   `save_or_field_errors(_do_save)` call to **also catch a save-time `ValidationError`**
   and route its `.detail` — the **same** nested structure as `serializer.errors` — through
   the **same** `serializer_errors_to_field_errors` flattener, returning the null-object
   envelope. The split is explicit and by exception type: a **`ValidationError`**
   (validation, expected, possibly raised from a custom `create()` / `update()`) → the
   recursive flattener; an **`IntegrityError`** (a concurrent-uniqueness race / residual
   db constraint) → the `036` `save_or_field_errors` mapper. Both stay inside the one
   `transaction.atomic()`; neither becomes a top-level error.
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
payload, and the `api_settings.NON_FIELD_ERRORS_KEY` bucket — while the frozen
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
`validation_error_to_field_errors`, but recursive; both terminate in the same frozen
envelope.

**`update` is DRF-native partial, not a reconstruction (the divergence from `038`).**
Where the `038` form flavor reconstructs the full bound payload from the located
instance (a bound Django form re-validates the whole field set), a DRF serializer with
`partial=True` validates **only the provided fields** natively — so `update` passes
`provided_data` directly with `partial=True`, no `model_to_dict` reconstruction. This
is simpler and is the DRF idiom; a `UniqueTogetherValidator` still validates the
provided field against the instance's unchanged members.

Justification: `serializer.is_valid()` / `serializer.save()` is the DRF-native
validation + write entry; routing `serializer.errors` into the envelope (rather than
raising) is the graphene-django / cross-flavor contract; the relation-visibility decode
is the package security invariant the `036` / `038` mutations enforce; the single
`atomic()` / single `sync_to_async` boundary is the settled async-safety contract.

Alternatives considered (and rejected):

- **Skip `is_valid()` and rely on the model's `full_clean()`.** Rejected: it loses the
  serializer's `validate_<field>` / `validate()` logic — the whole point of the
  flavor.
- **Reconstruct the full payload for `update` (the `038` shape).** Rejected: DRF's
  `partial=True` is the native partial-update mechanism and is cleaner than a
  `model_to_dict` overlay; reconstruction is a form-flavor necessity, not a serializer
  one.
- **Pass relation ids straight to the serializer without the visibility decode.**
  Rejected: a `PrimaryKeyRelatedField`'s default queryset is `Model.objects.all()`
  (not request-scoped), so a hidden target would be writable — the package's
  relation-visibility invariant (the `036` / `038` contract) requires the decode-time
  `get_queryset` check.

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

Justification: the re-fetch path is shipped and the G2 gate exists for exactly this;
reusing it gives the serializer flavor optimizer-composed returns for free, identical
to the form flavor.

Alternatives considered (and rejected):

- **Return `serializer.data` / `serializer.instance` without re-fetching.** Rejected:
  `serializer.instance` after `save()` has no response-selection relations loaded, so a
  relation in the response selection N+1s; the re-fetch is what makes the response
  planable, and `serializer.data` is the serializer's representation, not the
  `DjangoType` the frozen slot returns.

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
as deliberate non-adoptions in [Risks](#risks-and-open-questions).

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
the [Risks](#risks-and-open-questions) `model_operations` item.

Justification: `create` / `update` are the operations a serializer expresses; `delete`
has no serializer step; one-mutation-per-operation is the package's settled shape (the
`036` / `038` precedent).

Alternatives considered (and rejected):

- **Adopt graphene's `model_operations` runtime dispatch.** Rejected: it fragments the
  declaration shape away from [`DjangoMutation`][glossary-djangomutation] /
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] (one mutation per
  operation), and the single-string `Meta.operation` is the more `class Meta`-idiomatic
  selector.
- **Add a serializer `delete`.** Rejected: DRF serializers have no delete pipeline;
  the model-driven `DjangoMutation` `delete` already covers it.

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

Justification: the seam was frozen in `036` and proven reusable in `038`; the
`ModelSerializer`'s model resolves the default perm for free through the
`_resolve_model` override, so the serializer flavor is safe-by-default with no new
permission machinery.

Alternatives considered (and rejected):

- **Use DRF's own `permission_classes` / `DEFAULT_PERMISSION_CLASSES`.** Rejected: the
  package's write-auth is a first-class, `class Meta`-driven contract shared across
  flavors; threading DRF's request-level permissions through a GraphQL mutation would
  fork the contract and couple write-auth to DRF's view machinery (which is absent — a
  serializer is used here without a DRF view).

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
| `from django_strawberry_framework import *` | `SerializerMutation` **is** in `__all__` (so the name is documented / discoverable), but a `*`-import only binds names the module can resolve; with DRF absent, resolving `SerializerMutation` via `__getattr__` raises the same actionable `ImportError` rather than silently dropping it. |

One shared **`require_drf()`** helper (in `rest_framework/__init__.py`) owns the single
install-hint message and is the one place every `rest_framework/` module and the root
`__getattr__` route the guard through (no duplicated try/except message strings) — the
[`types/converters.py`][types-converters] soft-import precedent (`_resolve_array_field`
/ `_resolve_hstore_field`, which return `None` on `ImportError`) generalized to a
*raising* guard with an actionable message. `SerializerMutation` stays in the root
`__all__` (the `0.0.14` `channels` / `debug_toolbar` soft-dep posture).

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
2. **`djangorestframework` is added to `[dependency-groups].dev`** (Slice 4) so the
   test environment has it; the suite exercises every `rest_framework/` branch and the
   live products serializer surface, meeting `fail_under = 100`. **The dev-group floor
   must clear the CI matrix under `-W error`:** [`django.yml`][django-workflow] runs
   Django 5.2.0 → 6.0.\* → `latest` on Python 3.10 → 3.14 and [`pytest.ini`][pytest-ini]
   sets `filterwarnings = error`, so the pinned DRF release must **import and run
   warning-free** on (Python 3.14, Django 6.0 / `latest`) — DRF's Django support lags
   Django releases, so confirm such a release exists before pinning, and budget a
   targeted DRF-origin `ignore::` line (sanctioned by [`pytest.ini`][pytest-ini]'s own
   third-party comment) for any deprecation that release still emits. This is the
   pre-Slice-1 floor check in [Risks](#risks-and-open-questions), not an
   implementation-time discovery.
3. **The DRF-absent import-guard path is covered by simulated absence** — a package
   test forces the `ImportError` branch (monkeypatching `builtins.__import__` so the
   guarded `import rest_framework` fails) and asserts the install-hint message on **all
   three** raising entry points (the root `__getattr__("SerializerMutation")`, an
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
   reset.
4. **The example assumes the dev group** (DRF, like `pillow` / `faker`, is a
   dev / test artifact) — the products schema wires the serializer mutation
   unconditionally and the example settings add `"rest_framework"` to `INSTALLED_APPS`
   only if a serializer needs the app registry (most flat `ModelSerializer`s do not).

Justification: this is the established pattern for a soft dependency under a 100%-coverage
gate — out of runtime deps, in the dev group, the absent path simulated. It mirrors
[`spec-037`][spec-037]'s `pillow` handling exactly, and graphene-django's own optional
`rest_framework` dependency.

Alternatives considered (and rejected):

- **Add DRF to `[project].dependencies`.** Rejected: it forces every consumer to
  install DRF even if they never write a serializer mutation, exactly the soft-dep the
  card mandates against ("package import must succeed without DRF installed").
- **`# pragma: no cover` the whole `rest_framework/` subpackage.** Rejected: it would
  ship untested write-side code; the dev-group dependency lets the suite cover it for
  real, which is the point of the 100% gate.
- **Skip the absent-path test.** Rejected: the guard's raise is a reachable line under
  the 100% gate; simulated absence covers it.

### Decision 13 — Live coverage: products grows a `ModelSerializer` mutation, landed with the resolver

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
([Risks](#risks-and-open-questions))); the `serializer.errors`
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

Justification: the card DoD mandates "live HTTP coverage … exercising a
`ModelSerializer` mutation", and the test-query README makes live the **first** home for
any reachable line — so the resolver and its live surface are one deliverable, not two
slices. Products is the established write-surface example (the `036` / `038` precedent),
already carries the `unique_item_per_category` constraint, the seeded fixtures, and the
[`Item.attachment`][products-models] `FileField` the `Upload` path needs. DRF being a
dev-group dependency
([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy))
keeps it present in the test context.

Alternatives considered (and rejected):

- **Keep the resolver and the products live surface as separate commits** (the prior
  draft split them across two slices). Rejected: it violates the
  [`test_query/README.md`][test-query-readme] #"Coverage rule." — at the resolver
  commit, the resolver's reachable lines would be earned by `tests/rest_framework/`
  package tests, then duplicated by live tests in the next slice. Merging them into
  Slice 3 is the reviewer-pinned fix; the resolver's reachable behavior is earned live,
  once.
- **A dedicated `test_serializer_api.py` against a fresh app.** Rejected: products
  already carries the `unique_item_per_category` constraint and the seeded fixtures;
  extending `test_products_api.py` matches the `036` / `038` precedent (a dedicated
  file remains an acceptable alternative if the products suite grows unwieldy).
- **Reuse the `library` app.** Rejected: products is the canonical write-surface
  example and already hosts the model-driven and form mutations.

### Decision 14 — Version bumps are owned by the joint `0.0.13` cut

No slice in this card edits the **package-version state**: `[project].version` in
[`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init], or
[`tests/base/test_init.py::test_version`][test-base-init]. This card **shares the
`0.0.13` patch line** with [`TODO-ALPHA-040-0.0.13`][kanban]
([Auth mutations][glossary-auth-mutations]); the version bump from `0.0.12` to `0.0.13`
is owned by the **joint `0.0.13` cut**, not by either individual card — the same posture
[`spec-036`][spec-036] Decision 13 took for the joint `0.0.11` cut it shared with
[`spec-037`][spec-037]. (The Slice 4 doc edits do move feature-status text — the
[`docs/GLOSSARY.md`][glossary] `SerializerMutation` entry to `shipped (0.0.13)` — but
the version line and the version files stay at `0.0.12` until the joint cut.)

**`uv.lock` is NOT a version file — it is updated in this card, deliberately.** The
repository commits a `uv.lock` (verified, `git`-tracked), and Slice 4 adds
`djangorestframework` to `[dependency-groups].dev`
([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
Changing a dev dependency **without** regenerating the lockfile leaves the declared and
locked environments out of sync, so the clean cut is to **edit `pyproject.toml` and
regenerate `uv.lock` together** in Slice 4 (`uv lock` after the dev-group add). The
distinction the version policy must keep is: the **DRF dependency entries** in `uv.lock`
*do* change here; the **package's own version** — `[project].version` *and* the
`[[package]] name = "django-strawberry-framework"` `version` entry inside `uv.lock` —
stays `0.0.12` until the joint cut. (An earlier draft lumped `uv.lock` with the version
files, which contradicted the Slice 4 dev-group add; this reconciliation resolves it.)

Justification: per [`docs/SPECS/NEXT.md`][next] Step 3 / Step 6, when multiple cards
target one patch version the bump belongs to the joint cut, not any individual card's
spec. `039` and `040` both target `0.0.13`.

Alternatives considered (and rejected):

- **Bump to `0.0.13` in this card's Slice 4.** Rejected: `040` also ships into
  `0.0.13`; a per-card bump races the joint cut and would have to be reconciled when
  the sibling lands.

## Implementation plan

Four slices. Slices 1–2 are package-internal and staged; **Slice 3 lands the resolver
pipeline AND the products live serializer surface in one commit** (so reachable resolver
lines are earned live, not by package tests — the
[`test_query/README.md`][test-query-readme] #"Coverage rule."); Slice 4 is doc +
soft-dep + card-wrap only. Line deltas are planning estimates.

| Slice | Files touched | New / changed tests | Approx. delta |
| --- | --- | --- | --- |
| 1 — serializer-field converter + reverse map + the two serializer-derived inputs | [`rest_framework/serializer_converter.py`][rf-converter] (new; `convert_serializer_field` fail-loud MRO dispatch + the `input_attr → (serializer_field_name, source, kind)` reverse map, renamed-field `source` resolution + id-like-suffix rule), [`rest_framework/inputs.py`][rf-inputs] (new; `<Serializer>Input` + `<Serializer>PartialInput` from the `get_serializer_for_schema()` field set, `SerializerInputShape` descriptor identity, `guard_create_required_serializer_fields`, `read_only` / `optional_fields` handling, narrowing fail-loud), [`rest_framework/__init__.py`][rf-init] (new; DRF soft-import guard) | [`tests/rest_framework/test_converter.py`][test-rest-framework] + [`tests/rest_framework/test_inputs.py`][test-rest-framework] (~40 — every serializer-field class, id mapping, `Upload`, the reverse-map + `kind` flag, renamed-`source` + id-like-suffix + dotted-`source` raise, custom-field raise, schema-hook (kwargs-serializer reject + override), `read_only` dropped, `optional_fields` (+ `"__all__"` reject), descriptor identity (optional_fields / hook-vary → distinct names), create-required-guard (+ waiver, per-declaration), collision/dedupe, `Meta.fields`/`exclude` fail-loud + empty-set) | `+500 / 0` |
| 2 — the base class + `Meta` validation + the bind + the export guard | [`rest_framework/sets.py`][rf-sets] (new; `SerializerMutation` subclassing `DjangoMutation`, the `_validate_meta` / `_resolve_model` / `build_input` / `input_type_name` / `input_module_path` / `resolve_*` overrides), [`rest_framework/inputs.py`][rf-inputs] (`clear_serializer_input_namespace()`), [`types/finalizer.py`][types-finalizer] (call it **import-guarded** in the pre-bind reset block — `try/except ImportError` / `_clear_if_importable`, NOT a literal mirror of the direct mutation / form clears, since `rest_framework/inputs.py` is behind the DRF soft-import guard and the finalizer runs on every DRF-absent build too — no new bind, rides `bind_mutations()`), [`registry.py`][registry] (one `_clear_if_importable` co-clear row in `TypeRegistry.clear()`), [`__init__.py`][init] (guarded `SerializerMutation` export via root `__getattr__`) | [`tests/rest_framework/test_sets.py`][test-rest-framework] (~18 — `Meta` matrix incl. `delete`-rejected + plain-`Serializer`-rejected + no-model + `permission_classes` kept, both bind, retry-idempotence, no-primary error, model-flavor seam defaults unchanged) | `+340 / -10` |
| 3 — resolver pipeline **+ products live surface (one commit)** | [`rest_framework/resolvers.py`][rf-resolvers] (new; visibility-on-every-branch relation decoder + `partial=True` update + value-preserving save + sync/async pipeline reusing the `036`/`038` promoted helpers), [`examples/fakeshop/apps/products/serializers.py`][products-serializers] (new; `ItemSerializer` + the `Upload`/`Item.attachment` + request-context branches), [`products/schema.py`][products-schema] (serializer mutations), `config/settings.py` (`rest_framework` in `INSTALLED_APPS` if needed), [`mutations/resolvers.py`][mutations-resolvers] (no change) | **Primary: [`test_products_api.py`][test-products-api]** (~16 live `/graphql/` — create/update, field + `"__all__"` envelopes, `categoryId` reverse-map write, partial-update + unique-together, hidden update row, write-auth, hidden-relation `FieldError`, authorize-before-decode, multipart `Upload`, request-context, G2 query shape). **Internals-only: [`tests/rest_framework/test_resolvers.py`][test-rest-framework]** (~13 — recursive-flattener shapes, raw-pk/non-Relay + many-relation decode, call-once save, write-time `IntegrityError` + save-time `ValidationError`, sync/async + `SyncMisuseError`, hermetic kwargs seams) + [`tests/mutations/test_fields.py`][test-mutations] factory-generalization verification | `+560 / 0` |
| 4 — docs + soft-dep wiring + card wrap (no version bump) | [`pyproject.toml`][pyproject] (DRF → dev group) + `uv.lock`, [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`README.md`][readme], [`GOAL.md`][goal], [`TODAY.md`][today], [`docs/TREE.md`][tree], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban] | 0 (doc + dep only) | `+110 / -40` |

Total expected delta: ~`+1590 / -50` — an L cut, matching the card's relative size. The
near-zero edit to `mutations/` (the `036` helpers are reused by call; the
[`DjangoMutationField`][glossary-djangomutationfield] generalization is reused
unchanged) is the dividend of the `036` freeze + the `038` generalization.
Staged-but-not-implemented seams follow the [`AGENTS.md`][agents] design-doc anchor
discipline (a source-site `TODO(spec-039 Slice N)` comment naming this spec, removed in
the slice that ships it).

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
- **`read_only` / `HiddenField` fields.** Dropped from the input (graphene's
  `fields_for_serializer` `is_input` rule); a `HiddenField(default=CurrentUserDefault())`
  resolves at runtime from the injected `context={"request": …}`, never as client
  input.
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
  `files=` split). Full multipart HTTP ergonomics still await the `0.0.14`
  [`TestClient`][glossary-testclient]; the scalar + serializer-field typing ship here.
- **Relation visibility is not delegated to the serializer's queryset.** A
  `PrimaryKeyRelatedField`'s default queryset is `Model.objects.all()` (not
  request-scoped), so the decode type- and visibility-checks the id through the related
  primary `DjangoType.get_queryset` **before** the serializer sees it; a hidden /
  unseeable target is a field-keyed `FieldError`, identical to the model / form path.
- **`many=True` related fields are a `ManyRelatedField` wrapper (DRF realization detail).**
  DRF's `PrimaryKeyRelatedField(many=True)` does **not** subclass `ManyRelatedField`;
  `RelatedField.__new__` / `many_init` returns a `ManyRelatedField` that *wraps* the
  single field as `child_relation`. So the converter's `relation_multi` branch matches
  `serializers.ManyRelatedField` (a type disjoint from `PrimaryKeyRelatedField`, so the
  two `isinstance` checks are order-independent for correctness), and the relation
  target / id type is read off `field.child_relation`, **not** `field`. (Asserted from
  DRF's API; verify against the installed DRF when Slice 1 lands.)
- **A plain `serializers.Serializer` (no model) on `SerializerMutation`.** Rejected at
  class creation with a [`ConfigurationError`][glossary-configurationerror] (the
  `ModelSerializer`-driven contract requires a resolvable model); the model-less plain
  `Serializer` flavor is out of scope for `0.0.13`
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).
- **A `Meta.operation = "delete"`.** Rejected at class creation
  ([Decision 10](#decision-10--operations-create--update-no-serializer-delete)).
- **A nested writable serializer field.** A `ModelSerializer` field that is itself a
  serializer (`ListSerializer` / nested `ModelSerializer`) is out of scope (the `036`
  nested-write non-goal) — the converter raises
  [`ConfigurationError`][glossary-configurationerror] naming the field
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- **Write-time `IntegrityError`.** A valid `serializer.save()` that loses a
  concurrent-uniqueness race returns the null-object + `FieldError` envelope via the
  reused `036` `save_or_field_errors` mapper — never a top-level `GraphQLError`.
- **Write-time `ValidationError`.** A serializer with a custom `create()` / `update()`
  that raises `serializers.ValidationError` (or a model `full_clean()` raising
  `django.core.exceptions.ValidationError`) at `serializer.save()` time returns the
  null-object + `FieldError` envelope via the **recursive flattener** (the error's
  `.detail` is the same nested shape as `serializer.errors`), **not** a top-level
  `GraphQLError` — the split-by-exception-type in
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)
  step 6.
- **Two distinct generated serializer inputs colliding on one GraphQL name.** Two
  **different** serializer classes with the same `__name__` both emit
  `<__name__>Input` and **always** raise a finalize-time
  [`ConfigurationError`][glossary-configurationerror] (the reused
  `materialize_generated_input_class` ledger raise); only repeats of the **same**
  `SerializerInputShape` descriptor dedupe.
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
  otherwise finalize but never validate. `read_only` / `HiddenField` are exempt;
  overriding `get_serializer_kwargs` to inject the values waives the guard. Update
  (`partial=True`) inputs are unaffected.
- **No `DjangoType` `Meta` key added.** [`DEFERRED_META_KEYS`][types-base] /
  `ALLOWED_META_KEYS` are byte-unchanged.

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

- **Live, over `/graphql/`** (Slice 3, [`test_products_api.py`][test-products-api],
  seeded via `seed_data` / `create_users`) — **the primary harness for every reachable
  resolver branch**: `createItemViaSerializer` / `updateItemViaSerializer` happy paths;
  the `serializer.errors` envelope (a `validate_<field>` error keyed to the serializer
  field, the `UniqueTogetherValidator` / `validate()` error keyed to `"__all__"`);
  **`categoryId` validates and writes through the serializer's `category`
  `PrimaryKeyRelatedField`** (proving the reverse map); **partial-update preservation** —
  a `name`-only `updateItemViaSerializer` preserves `description` and `category`, and the
  unique constraint fires when only `name` changes to a value already taken under the
  unchanged `category` (the `partial=True` contract — but note this fire depends on DRF's
  `UniqueTogetherValidator.filter_queryset` **backfilling the unchanged `category` from
  `serializer.instance`** during a partial update, a **DRF behavior, not a package one**,
  so the assertion is tied to the DRF floor verified in
  [Risks](#risks-and-open-questions)); a non-colliding partial update;
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
  shape** — asserting (via `CaptureQueriesContext` / the optimizer's plan) the payload
  re-fetch keeps `select_related` / `prefetch_related` and emits no `.only(...)` column
  deferral.
- **Package-internal** ([`tests/rest_framework/`][test-rest-framework]):
  - `test_converter.py` — each supported serializer-field class → annotation +
    required-ness; `PrimaryKeyRelatedField` / `ManyRelatedField` id mapping
    (Relay-`GlobalID` vs raw pk); `FileField` → [`Upload`][glossary-upload-scalar]; the
    `input_attr → (serializer_field_name, source, kind)` reverse map; **renamed fields**
    — a `source="category"` FK and a `source="name"` scalar derive the GraphQL name from
    the declared field name, resolve the backing column via `source`, and preserve the
    declared name in the reverse map; a **dotted `source`** / `source="*"` on a
    model-column-converting field raises
    [`ConfigurationError`][glossary-configurationerror]; **the fail-loud dispatch — a
    known field maps, but a custom `class CustomField(serializers.Field)` raises
    [`ConfigurationError`][glossary-configurationerror]** (the catch-all-shadowing
    regression test); a `ListField` with a **scalar** child maps to `list[<scalar>]` but a
    `ListField` whose child is a relation / nested serializer raises; a nested serializer
    field raises.
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
    exclusions do not, the `get_serializer_kwargs` waiver suppresses it, and the guard
    fires **per declaration** (waiving-first does not suppress a later non-waiving
    mutation on the same shape); the distinct-shapes-collide
    [`ConfigurationError`][glossary-configurationerror]; an empty effective field set →
    `ConfigurationError`.
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
    **a save-time `ValidationError`** — a serializer whose custom `create()` / `update()`
    raises `serializers.ValidationError` from `save()` routes through the recursive
    flattener into the envelope (the split-by-exception-type; products' flat
    `ItemSerializer` has no custom `save()`, so this needs a synthetic serializer);
    **the value-preserving save** — `serializer.save()` is called **exactly once** (a
    save spy) and the re-fetch uses the returned object (not a second save, not a stale
    `serializer.instance`); the **hermetic `get_serializer_kwargs` override** (injecting a
    non-default `context` / constructor kwargs) and the bare-`HttpRequest` `info.context`
    fallback of `request_from_info`; **sync + async** (one
    `sync_to_async(thread_sensitive=True)`) and the
    [`SyncMisuseError`][glossary-syncmisuseerror] async-`get_queryset`-from-sync path.
  - **The DRF-absent import guard** ([`tests/rest_framework/test_soft_dependency.py`][test-rest-framework]
    or in `test_sets.py`): with DRF's import simulated-absent (monkeypatched
    `builtins.__import__`, **module caches for both `rest_framework*` and
    `django_strawberry_framework.rest_framework*` evicted first, and the root
    `django_strawberry_framework.SerializerMutation` attribute deleted**, so neither a
    stale submodule import nor a bound root symbol can mask the path), all three raising
    entry points — the root `__getattr__("SerializerMutation")`, an `…rest_framework`
    import, and an `…rest_framework.sets` import — raise `ImportError` with the install
    hint, while `import django_strawberry_framework` still succeeds; and a
    **non-memoization** assertion (a successful `SerializerMutation` access does not bind
    the name into the root module globals)
    ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
  - [`tests/mutations/test_fields.py`][test-mutations] (extend) — the
    `038`-generalized [`DjangoMutationField`][glossary-djangomutationfield] target
    check + dispatch + `data:` ref accept a `SerializerMutation` unchanged (the
    verification, not an edit).
- **Cross-cutting — no regression.** The full suite is green at the 100% coverage gate
  (`fail_under = 100`); `ruff format` + `ruff check` are clean; the `036` / `038`
  mutation surfaces and the read side are unchanged.

## Doc updates

Each slice owns its doc edits. [`AGENTS.md`][agents] #"Do not update CHANGELOG.md
unless explicitly instructed" requires `CHANGELOG.md` edits to be explicitly
instructed — and a standing design doc cannot itself grant that permission. This spec
only *describes* the release-note work; the **Slice 4 maintainer prompt must explicitly
include the `CHANGELOG.md` edit** for it to be authorized.

- **Slice 4 — soft-dep wiring** ([`pyproject.toml`][pyproject] + `uv.lock`): add
  `djangorestframework` to `[dependency-groups].dev` (NOT `[project].dependencies`),
  pinning a floor matching the guard's install hint, and regenerate `uv.lock` so the
  lockfile matches. **No package-version edits** (the `[project].version` /
  `__version__` / `test_version` and the `uv.lock` package-version entry stay `0.0.12`;
  only the DRF dependency entries change)
  ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
- **Slice 4 — GLOSSARY** ([`docs/GLOSSARY.md`][glossary]): promote
  [`SerializerMutation`][glossary-serializermutation] from `planned for 0.0.13` to
  `shipped (0.0.13)` (updating the body to the shipped contract — the
  `Meta.serializer_class` surface, the serializer-derived input, the `serializer.errors`
  → [`FieldError`][glossary-fielderror-envelope] mapping, the soft DRF dependency, the
  `036` reuse) and **reconcile the surface keys** to what this card pins:
  `Meta.operation` (the package convention) rather than graphene's `model_operations`,
  the `id:`-decode locate rather than `lookup_field` (both recorded as deliberate
  non-adoptions). Add `SerializerMutation` to **Public exports**, the **Index** (status
  column), and the **Mutations** browse-by-category row.
- **Slice 4 — package docs**: [`docs/README.md`][docs-readme] / [`README.md`][readme]
  move the serializer flavor from "Coming next (`0.0.13`)" to "Shipped today" in the
  "Coming from DRF + django-filter?" paragraph (the README **Status** version line
  moves to `0.0.13` at the joint cut, not here); [`GOAL.md`][goal] — criterion 6's
  `ModelSerializer` flavor now ships (all three named flavors shipped); [`TODAY.md`][today]
  notes the serializer mutation as a package capability; [`docs/TREE.md`][tree] fills
  the planned `rest_framework/` / [`tests/rest_framework/`][test-rest-framework]
  summary lines; [`CHANGELOG.md`][changelog] carries the bullets **only when the Slice
  4 maintainer prompt explicitly requests it**.
- **Slice 4 — card wrap**: [`KANBAN.md`][kanban] moves [`TODO-ALPHA-039-0.0.13`][kanban]
  to Done with the next `DONE-NNN-0.0.13` id, keeping its `SpecDoc` pointing at the
  canonical card spec (a `SpecDoc` DB edit re-rendered via `scripts/build_kanban_md.py`,
  never a hand-edit).

## Risks and open questions

Each item names a preferred answer for the `0.0.13` cut and a fallback if
implementation reveals it is wrong.

- **The `## In progress` KANBAN column is empty as this spec is authored.** The
  [`docs/SPECS/NEXT.md`][next] flow targets "the next-up Work-In-Progress card", but no
  card is in the `wip` status (the column renders empty; `git`-verified against the
  `apps.kanban` DB). Preferred reading: `039` is the **lowest-NNN card in the active
  To-Do / Alpha column** and the natural next-up spec target (the latest `DONE` card is
  `038-0.0.12`; `039` is the next NNN). The card's status was **not** moved to `wip`
  (the [`docs/SPECS/NEXT.md`][next] boundary forbids non-spec DB edits). Fallback: if
  the maintainer intended a different next card, re-author against it — but `039` is the
  unambiguous lowest-NNN active card.
- **Model-less plain `Serializer` flavor — deferred (preferred), not RESOLVED.**
  Preferred answer ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)):
  `0.0.13` ships the `ModelSerializer`-driven contract only (a resolvable model, the
  uniform `node` / `result` slot); a plain model-less `serializers.Serializer` is out of
  scope (it has no object slot and `DjangoMutation`'s base requires a resolvable model).
  Fallback: add a model-less sibling later in the [`DjangoFormMutation`][glossary-djangoformmutation]
  shape (its own metaclass + `{ ok, errors }` payload + `bind_serializer_mutations()`),
  if a consumer needs a serializer-validated non-model write — never weaken the
  `ModelSerializer` contract.
- **Card key `Meta.model_operations` vs the package's `Meta.operation` — the real
  crit-7 friction point.** The card lists `Meta.model_operations` (graphene's
  runtime-dispatched list); the package uses per-operation `Meta.operation`
  ([Decision 10](#decision-10--operations-create--update-no-serializer-delete)).
  Preferred reading: honor `Meta.operation` (uniform with
  [`DjangoMutation`][glossary-djangomutation] / [`DjangoModelFormMutation`][glossary-djangomodelformmutation]
  — both of which already **require** an explicit `operation`, so the serializer flavor
  cannot quietly default it without becoming the odd one out). This is where the
  `graphene-django` serializer-mutation migrant feels crit-7 most: their one
  auto-dispatching `model_operations = ["create", "update"]` mutation must become **two**
  package mutations, each with an `operation` key their old code never had — a
  declaration-shape change, not "only the import line changes." The base-class swap
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven))
  carries over by name; this key does not. The **near-term affordance** (preferred over
  leaving the migrant to hand-split) is to accept `Meta.model_operations` as an alias
  that **expands to the per-operation mutations** under the hood — a contained
  metaclass-time desugaring that keeps the package's one-mutation-per-op internals while
  letting the graphene key migrate verbatim; sequence it right after `0.0.13` if the
  migration friction proves real. Recorded per the [`docs/SPECS/NEXT.md`][next] "prefer
  the card, surface the conflict" rule.
- **Card key `Meta.lookup_field` vs the `id:`-decode locate.** The card lists
  `Meta.lookup_field` (graphene's non-pk update locate via `get_object_or_404`); the
  package locates an `update` row by decoding the `id:` `GlobalID` server-side and
  running it through the target `get_queryset`
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)).
  Preferred reading: keep the `id:`-decode locate (the package's no-existence-leak
  contract, uniform with `036` / `038`); the fallback is a future `Meta.lookup_field`
  for a non-pk locate (a contained resolver change). Recorded, not silently reconciled.
- **Card phrase "dual-purposed for inputs and outputs" vs the frozen `node` / `result`
  slot.** The card DoD names the converter "dual-purposed for inputs and outputs
  (mirroring graphene's `is_input=True` flag)"; the `036`-frozen uniform `node` /
  `result` slot is the package's one cross-flavor output contract
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
  Preferred reading: the converter is **input-directed**; the mutation output is the
  primary [`DjangoType`][glossary-djangotype] in the frozen slot, not a
  serializer-derived output type (the same way `038` superseded `Meta.return_field_name`).
  The `is_input` parameter is carried for graphene parity / forward use but is
  **accepted-and-ignored — no `if not is_input:` branch**, so it adds no uncovered line
  under `fail_under = 100`. Fallback: if a consumer needs a serializer-shaped output, that
  is a separate (post-`1.0.0`) surface, not this card.
- **DRF version floor — a concrete pre-Slice-1 check, gated by the CI matrix under
  `-W error`.** This is the biggest practical risk and the **binding** constraint is
  *not* serializer-API availability — it is that the dev-group DRF must **import and run
  warning-free across the entire CI matrix**. [`pyproject.toml`][pyproject] declares
  `requires-python = ">=3.10,<4.0"` with Django 5.2 / 6.0 classifiers, the
  [`django.yml`][django-workflow] matrix runs **Django 5.2.0 → 5.2.\* → 6.0.\* →
  `latest` on Python 3.10 → 3.14**, and [`pytest.ini`][pytest-ini] sets
  `filterwarnings = error`. So **any** `DeprecationWarning` / `RemovedInDjango*Warning`
  DRF emits under Django 6.0 / `latest` or Python 3.14 becomes a hard
  collection / test failure — exactly the failure mode the `forms.URLField()`
  `assume_scheme` deprecation just produced (a third-party-adjacent deprecation turned
  fatal by `-W error`). DRF's Django-version support also **lags** Django releases, so a
  DRF release that officially supports Django 6.0 / Python 3.14 may not yet exist; if it
  does not, the Django-6.0 / `latest` matrix nodes fail at `uv sync` / import time.
  Preferred answer
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)):
  **before Slice 1**, verify a `djangorestframework` release exists that imports and runs
  **warning-free on (Python 3.14, Django 6.0 / `latest`)** as well as the floor
  (`Python>=3.10`, `Django>=5.2`); record the **exact** floor pinned in the dev group
  (and matched in the guard's install hint), plus **any DRF-origin `ignore::` line** that
  release still needs — [`pytest.ini`][pytest-ini]'s own comment already sanctions a
  targeted `ignore::` for "warnings originating in third-party packages we cannot fix"
  (never a blanket ignore). Secondary (API-availability) constraint: bump the floor if a
  needed serializer API (e.g. `api_settings.NON_FIELD_ERRORS_KEY`) is only present in a
  later release. Settled during implementation against the actually-installed DRF, but the
  matrix-warning check is the one that gates the floor.
- **`serializer.save()` create-vs-update + M2M.** Preferred answer
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)):
  `serializer.save()` runs `create()` (no instance) / `update()` (with instance)
  internally and assigns M2M within that call, all inside the one
  `transaction.atomic()` — no separate M2M step (the DRF idiom). Fallback: an explicit
  `perform_save` hook only if a consumer serializer needs the saved instance before its
  M2M rows — a contained resolver change, not a contract change.
- **`rest_framework` in the example's `INSTALLED_APPS`.** Preferred answer
  ([Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation)):
  add `"rest_framework"` to the fakeshop `INSTALLED_APPS` only if a flat
  `ModelSerializer` needs the app registry (most do not — DRF serializers validate /
  save without the app installed). Fallback: add it unconditionally if a serializer
  feature (browsable-API-only machinery) is reached; settled during implementation.
- **Card-citation note — the spec filename vs the card's
  `docs/spec-serializer_mutations.md`.** The card DoD names
  `docs/spec-serializer_mutations.md`; the structured convention authors at
  `docs/spec-039-serializer_mutations-0_0_13.md`
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)). Recorded, not
  silently reconciled, per the [`docs/SPECS/NEXT.md`][next] boundary rule.

## Out of scope (explicitly tracked elsewhere)

- **Auth mutations** ([Auth mutations][glossary-auth-mutations]) — `0.0.13`
  ([`TODO-ALPHA-040-0.0.13`][kanban]); shares the joint cut, reuses the same envelope.
- **A model-less plain `Serializer` flavor** — deferred
  ([Risks](#risks-and-open-questions); the [`DjangoFormMutation`][glossary-djangoformmutation]
  model-less sibling is the fallback shape).
- **Serializer-derived output types / nested writable serializers** — the frozen
  `node` / `result` slot supersedes a serializer output, and nested writes stay the
  `036` non-goal
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- **Serializer `delete`** — not shipped; the model-driven
  [`DjangoMutation`][glossary-djangomutation] (`Meta.operation = "delete"`) covers
  deletion ([Decision 10](#decision-10--operations-create--update-no-serializer-delete)).
- **The ergonomic `TestClient` / `AsyncTestClient` helper** —
  [`TestClient`][glossary-testclient] (`TODO-ALPHA-043-0.0.14`); the serializer
  `Upload`-field correctness (the `Upload` input typing, the value in `data`) ships
  here, only the multipart test-client wrapper is deferred.
- **Field-level read gates** ([`FieldSet`][glossary-fieldset] /
  [Per-field permission hooks][glossary-per-field-permission-hooks]) — `0.1.1`,
  composing on top of (not replacing) write authorization.
- **The `0.0.13` version bump** — owned by the joint `0.0.13` cut shared with
  [`TODO-ALPHA-040-0.0.13`][kanban]
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

1. `docs/spec-039-serializer_mutations-0_0_13.md` (this document) and its companion
   `spec-039-serializer_mutations-0_0_13-terms.csv` exist;
   `uv run python scripts/check_spec_glossary.py --spec docs/spec-039-serializer_mutations-0_0_13.md`
   reports `OK: <N> terms`.

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
   before the descriptor cache lookup (waived by a `get_serializer_kwargs` override);
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
   [`ConfigurationError`][glossary-configurationerror]); the model flavor's seam
   defaults are unchanged; [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS` are
   unchanged; `SerializerMutation` rides `bind_mutations()` (no new bind entry) with
   `clear_serializer_input_namespace()` called from **both** the
   [`finalize_django_types`][glossary-finalize_django_types] pre-bind reset block (the
   retry-idempotence fix — **import-guarded**, since the finalizer runs on DRF-absent
   builds where the serializer ledger is empty and a skipped clear is a correct no-op,
   unlike the always-importable mutation / form clears) **and**
   `TypeRegistry.clear()`; and `SerializerMutation` exports from [`__init__.py`][init]
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
   the **dedicated serializer relation decoder**: every relation id — `GlobalID` *or*
   **raw pk** — is type-checked (target model resolved from the backing FK via the
   serializer field's `source`), resolved to the **visible** object through the related
   primary `DjangoType.get_queryset` (the same per-branch raw-pk visibility check
   `036`'s model path and `038`'s form path already enforce), and reduced to the pk
   before landing under the serializer field name; a hidden target → field-keyed
   `FieldError`; an [`Upload`][glossary-upload-scalar] value lands in `data`;
   construction goes through the overridable
   `get_serializer_kwargs(info, *, data, instance=None)` hook (injecting
   `context={"request": request_from_info(info, …)}` and `partial=True` on `update`).
   `serializer.errors` maps onto the
   [`FieldError` envelope][glossary-fielderror-envelope] via the **dedicated recursive
   flattener** (`serializer_errors_to_field_errors`; dotted path `items.0.name`;
   `non_field_errors` → `"__all__"` at every level; not the one-level `036` mapper); the
   write is wrapped by the `036` `save_or_field_errors` mapper in a **value-preserving
   closure** (`serializer.save()` called once, its returned object captured for the
   re-fetch); the payload object is re-fetched through the `036` optimizer path (G2:
   `select_related` / `prefetch_related` kept, no [`.only(...)`][glossary-only-projection]).
   [`mutations/fields.py`][mutations-fields] is **unchanged** — the `038`-generalized
   [`DjangoMutationField`][glossary-djangomutationfield] exposes the serializer flavor,
   verified by a [`tests/mutations/test_fields.py`][test-mutations] extension
   ([Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused)
   / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)
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
   write, the **request-context** `validate()` path, and the **G2 re-fetch query shape**.
   `tests/rest_framework/test_resolvers.py` holds **only** the genuinely-unreachable
   internals (recursive-flattener shapes, raw-pk/non-Relay + many-relation decode,
   call-once save, `IntegrityError` + save-time `ValidationError`, sync/async +
   `SyncMisuseError`, hermetic kwargs seams) — **no reachable behavior is duplicated
   across the two trees**
   ([Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation),
   the [`test_query/README.md`][test-query-readme] #"Coverage rule.").

**Cross-cutting — no regression**

6. The full suite is green at the 100% coverage gate (`fail_under = 100`) — including
   the **DRF-absent import-guard path covered by simulated absence**; `ruff format` +
   `ruff check` are clean; the `036` / `038` mutation surfaces and the read side are
   unchanged.

**Slice 4 — docs + soft-dep + card wrap (no version bump)**

7. [`pyproject.toml`][pyproject] adds `djangorestframework` to `[dependency-groups].dev`
   (NOT `[project].dependencies`) **and `uv.lock` is regenerated to match** (the DRF
   dependency entries only); [`docs/GLOSSARY.md`][glossary] promotes
   [`SerializerMutation`][glossary-serializermutation] to `shipped (0.0.13)` (with
   Public-exports + Index + Mutations-category rows) and reconciles its surface keys
   (`Meta.operation`, the `id:`-decode locate); [`docs/README.md`][docs-readme] /
   [`README.md`][readme] move the serializer flavor to "Shipped today"; [`GOAL.md`][goal]
   / [`TODAY.md`][today] / [`docs/TREE.md`][tree] reflect the shipped flavor — and the
   [`GOAL.md`][goal] crit-6 "Coming from DRF + `django-filter`" example is **corrected to
   the shipped surface**: `class CreateCategoryFromSerializer(SerializerMutation):` (not
   `DjangoMutation`,
   [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven))
   with an explicit `operation = "create"` (mandatory, not inferred,
   [Decision 10](#decision-10--operations-create--update-no-serializer-delete)), so the
   north star stops depicting a declaration that fails validation under the shipped
   package. The edit may assert the generated shape inline for the depicted
   `CategorySerializer(fields=("id", "name"))` — `CategorySerializerInput { name: String! }`
   (the read-only `id` dropped,
   [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)) —
   so GOAL.md's declaration and its generated schema visibly agree;
   [`CHANGELOG.md`][changelog] carries the bullets **only when the Slice 4 maintainer
   prompt explicitly requests the edit**; [`KANBAN.md`][kanban] records the card
   `DONE-NNN-0.0.13` with the `SpecDoc` reference at the canonical card spec (kanban DB
   + re-render).
8. **No version bump lands in this card**
   ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)):
   `[project].version`, `__version__`, and
   [`tests/base/test_init.py::test_version`][test-base-init] stay `0.0.12`, and so does
   the `django-strawberry-framework` `version` entry inside `uv.lock` — but `uv.lock`
   **is** regenerated for the `[dependency-groups].dev` DRF add (lockfile and manifest
   stay in sync; only the DRF dependency entries change). No [`CHANGELOG.md`][changelog]
   release heading is promoted (the joint `0.0.13` cut shared with
   [`TODO-ALPHA-040-0.0.13`][kanban] owns the bump). The one net-new public symbol
   (`SerializerMutation`) is added to `__all__` (resolved lazily via the root
   `__getattr__` under the DRF soft-import guard).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[pyproject]: ../pyproject.toml
[pytest-ini]: ../pytest.ini
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- .github/ -->
[django-workflow]: ../.github/workflows/django.yml

<!-- docs/ -->
[docs-readme]: README.md
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-choice-enum-generation]: GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-cross-subsystem-invariants]: GLOSSARY.md#cross-subsystem-invariants
[glossary-djangoformmutation]: GLOSSARY.md#djangoformmutation
[glossary-djangomodelformmutation]: GLOSSARY.md#djangomodelformmutation
[glossary-djangomodelpermission]: GLOSSARY.md#djangomodelpermission
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: GLOSSARY.md#djangomutationfield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: GLOSSARY.md#fielderror-envelope
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-input-type-generation]: GLOSSARY.md#input-type-generation
[glossary-metaexclude]: GLOSSARY.md#metaexclude
[glossary-metafields]: GLOSSARY.md#metafields
[glossary-metamodel]: GLOSSARY.md#metamodel
[glossary-metaprimary]: GLOSSARY.md#metaprimary
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: GLOSSARY.md#per-field-permission-hooks
[glossary-scalar-field-conversion]: GLOSSARY.md#scalar-field-conversion
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-syncmisuseerror]: GLOSSARY.md#syncmisuseerror
[glossary-testclient]: GLOSSARY.md#testclient
[glossary-upload-scalar]: GLOSSARY.md#upload-scalar
[glossary]: GLOSSARY.md
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-027]: SPECS/spec-027-filters-0_0_8.md
[spec-028]: SPECS/spec-028-orders-0_0_8.md
[spec-034]: SPECS/spec-034-permissions-0_0_10.md
[spec-035]: SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-036]: SPECS/spec-036-mutations-0_0_11.md
[spec-037]: SPECS/spec-037-upload_file_image_mapping-0_0_11.md
[spec-038]: SPECS/spec-038-form_mutations-0_0_12.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[forms-converter]: ../django_strawberry_framework/forms/converter.py
[forms-inputs]: ../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../django_strawberry_framework/forms/sets.py
[init]: ../django_strawberry_framework/__init__.py
[mutations-fields]: ../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../django_strawberry_framework/mutations/sets.py
[registry]: ../django_strawberry_framework/registry.py
[rf-converter]: ../django_strawberry_framework/rest_framework/serializer_converter.py
[rf-init]: ../django_strawberry_framework/rest_framework/__init__.py
[rf-inputs]: ../django_strawberry_framework/rest_framework/inputs.py
[rf-resolvers]: ../django_strawberry_framework/rest_framework/resolvers.py
[rf-sets]: ../django_strawberry_framework/rest_framework/sets.py
[types-base]: ../django_strawberry_framework/types/base.py
[types-converters]: ../django_strawberry_framework/types/converters.py
[types-finalizer]: ../django_strawberry_framework/types/finalizer.py
[utils-inputs]: ../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../django_strawberry_framework/utils/permissions.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-mutations]: ../tests/mutations/
[test-rest-framework]: ../tests/rest_framework/

<!-- examples/ -->
[products-models]: ../examples/fakeshop/apps/products/models.py
[products-schema]: ../examples/fakeshop/apps/products/schema.py
[products-serializers]: ../examples/fakeshop/apps/products/serializers.py
[test-products-api]: ../examples/fakeshop/test_query/test_products_api.py
[test-query-readme]: ../examples/fakeshop/test_query/README.md
[test-uploads-api]: ../examples/fakeshop/test_query/test_uploads_api.py

<!-- scripts/ -->

<!-- .venv/ -->
[upstream-serializer-converter]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/serializer_converter.py
[upstream-serializer-mutation]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/mutation.py

<!-- External -->
