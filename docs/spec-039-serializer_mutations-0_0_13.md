# Spec: DRF serializer mutations — `SerializerMutation` on the DRF-shaped `class Meta` surface, reusing the frozen `FieldError` envelope and the `DjangoMutation` foundation, with `djangorestframework` as a soft dependency

Implemented on main; release deferred to the joint `0.0.13` cut (card
[`DONE-039-0.0.13`][kanban]). This card adds the
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

Status: **IMPLEMENTED ON MAIN** — all five slices (Slice 0 + Slices 1-4) are
final-accepted and on main; the implemented-on-main docs + the card wrap landed in
Slice 4 ([`DONE-039-0.0.13`][kanban]). **Release deferred to the joint `0.0.13` cut**
shared with [`WIP-ALPHA-040-0.0.13`][kanban], which still owns the version bump
(`0.0.12` → `0.0.13`) and the public release-status flip (the GLOSSARY `shipped (0.0.13)`
status, the `README.md` / [`docs/README.md`][docs-readme] "Shipped today" move, the
`CHANGELOG.md` bullets) — **F8** / [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut).
The card was authored for `TODO-ALPHA-039-0.0.13` via the
[`docs/SPECS/NEXT.md`][next] flow. The card's hard dependency was
satisfied: [`DONE-036-0.0.11`][kanban] (the mutation foundation this card subclasses)
has shipped, and [`DONE-038-0.0.12`][kanban] (which generalized the field factory and
proved the flavor-on-the-base pattern) has shipped too. **A pre-Slice-1 dependency gate
(Slice 0 — the `djangorestframework` dev-dep + `uv.lock` regen + the verified DRF floor,
F11) plus four implementation/doc slices** (the resolver pipeline and the products
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
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)
/
[Decision 9](#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path)
/
[Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation)),
and Slice 4 (**docs + card wrap, no version bump** — the soft-dep wiring is **not** here;
it landed in the Slice 0 gate, **F11**; the per-card
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
as `planned for 0.0.13`; Slice 4 updates its **body** to the implemented contract
(status **"implemented on main, releasing in 0.0.13"**), and the `shipped (0.0.13)` flip
defers to the joint cut (**F8**, [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).

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
- **Revision 7** — applied a DRY / cross-flavor reuse pass (every reuse claim verified
  against the source first — the relation-decode fork, `_VALID_FORM_OPERATIONS`, the
  shape-cache "twin of" comment, the sync-pipeline orchestration copies, the two
  hand-maintained ledger-clear lists, the `build_input` seam cluster, the field-spec /
  namespace / typo-guard duplications, and the absence of any `register_subsystem_clear`
  seam were all confirmed; corrections folded in: the form bases normalize via
  `forms/sets.py::_resolve_effective_form_field_names` not `_normalize_field_sequence`, no
  `field_error(...)` ctor exists yet, `_form_kwargs_overridden` is the helper to
  generalize). Added a **[Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations)**
  section: the confirmed reuses locked as import obligations, **seven third-copy-fork
  promotions** to single-site now (**P1.1** relation-decode core → `_visible_related_object`
  in `utils/querysets.py`; **P1.2** `NON_DELETE_WRITE_OPERATIONS`; **P1.3** shape-build cache
  plumbing; **P1.4** fail-loud converter dispatch skeleton → `utils/converters.py`; **P1.5**
  the sync write-pipeline orchestration — a **security** ordering, the highest-value
  promotion; **P1.6** a `register_subsystem_clear` seam collapsing the two hand-edited clear
  lists; **P1.7** the `build_input` build/stash/name cluster), **seven single-siting items**
  (**P2.1**–**P2.7**: unified field-spec, the one-ledger namespace trio, `_pascalize_token`,
  the leaf-error sentinel/ctor, the `_validate_meta` sub-validators, `_hook_overridden`, the
  `reject_unknown_meta_keys` typo-guard), the **P3** pin-as-import list + a deliberately
  NOT-applicable list, and a per-`rest_framework/`-module **import manifest** (the DoD-checkable
  DRY contract). Each promotion is pinned into its Decision
  ([4](#decision-4--module-and-test-locations-rest_framework-subpackage-mirroring-forms) /
  [6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven) /
  [7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) /
  [8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload) /
  [10](#decision-10--operations-create--update-no-serializer-delete)) and its Slice DoD
  line, and the [Implementation plan](#implementation-plan) (the per-slice file lists +
  the "no regression" item) is reconciled to show the promotions touch `mutations/` /
  `utils/` / `forms/` / `types/finalizer.py` / `registry.py` **net-near-zero**
  (extract-and-re-point), behavior-preservingly (the `036` / `038` suites stay green).
- **Revision 8** — applied a deep-architecture review (11 findings, each verified against
  the source + the new `TODO(spec-039 Slice N)` anchors before editing). **Contract-precision
  fixes:** **(F1)** `SerializerMutation` is **removed from `__all__`** while DRF is soft — a
  star import consults `__all__` and would trip the `__getattr__` DRF guard, breaking
  `from … import *` for DRF-absent consumers (verified: the root has eager `__all__` + no
  lazy precedent); it stays a **named** lazy export, with a star-import soft-dep test added
  ([Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused) /
  [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
  **(F2)** save-time `ValidationError` is **split by class** — DRF's `.detail` → the
  recursive flattener, Django's `error_dict` / `messages` → the flat `036`
  `validation_error_to_field_errors` (verified: the `036` mapper reads Django's shape, not
  `.detail`), two separate tests
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)).
  **(F3)** the generated relation input carries **one** strategy-dependent annotation
  (Relay → `GlobalID`, else raw-pk scalar; verified via products'
  malformed-`GlobalID`-is-top-level-coercion test); "accepts both" is the shared decode
  *helper*'s contract, package-tested by direct call (Decisions 7/8). **(F4)** serializer-only
  relation fields are **supported via `field.queryset.model`** (else rejected) — the
  previously-undefined write-only-`PrimaryKeyRelatedField` case (Decision 7). **(F5)** the
  error flattener keys `FieldError.field` to the **GraphQL input name** via the reverse map
  (serializer name only when no input field exists), with a live renamed-field test
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)).
  **(F6)** `run_write_pipeline_sync` is **scoped to model-backed create/update only** (delete +
  plain form excluded) with a precise `decode_step` / `write_step` callback contract and a
  byte-equivalence requirement on the existing model/form suites
  ([P1.5](#cross-flavor-reuse-and-dry-obligations)). **(F7)** `get_serializer_kwargs`
  precedence pinned — framework-owned `partial=True` (`ConfigurationError` on `partial=False`),
  merged request `context`. **(F8)** Slice 4 splits **implemented-on-main** docs from
  **release** ("shipped (0.0.13)" / README "Shipped today" / changelog) docs, the latter
  deferred to the joint cut ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
  **(F9)** the live request-context proof is an explicit `validate()`, not a `HiddenField`
  (subtle under `partial=True`). **(F10)** `register_subsystem_clear` uses static
  `(module_path, attr)` rows (no DRF import at registration), with the import-time invariant
  stated. **(F11)** the DRF dev-dependency wiring + floor probe moves to a **pre-Slice-1
  gate (Slice 0)**, since Slice 1–3 tests import DRF. Plus the config assessment: serializer
  relation decode consumes the recorded `effective_globalid_strategy`, never
  `conf.settings` / `_resolve_globalid_strategy` on the query path.
- **Revision 9** — applied an architecture-pass review (3 H + 5 M findings + missing edge
  cases, each verified against the source before editing). **(H1)** normalized the Slice 0 /
  Slice 4 wording across the Status block, Goals item 8, and Decision 14 (the soft-dep wiring
  + `uv.lock` regen are owned by the **Slice 0 gate**, Slice 4 is docs + card-wrap only) —
  the stale "Four slices" / "soft-dep wiring in Slice 4" prose contradicted the gate.
  **(H2)** rewrote the **Write-time `ValidationError`** edge case (and the DoD Slice 3 item)
  to **split by exception class** to match Decision 8 step 6 — it previously sent a Django
  `ValidationError` (no `.detail`) down the DRF `.detail` flattener. **(H3)** made
  `context["request"]` **strictly framework-owned** — the framework sets it unconditionally
  from `request_from_info(...)`, an override supplying a *different* `request` is a
  `ConfigurationError` (actor cannot drift from the permission seam); the prior "escape
  hatch" wording is removed
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)
  step 4). **(M1)** the Slice 3 + DoD relation-id summaries now state the **one
  strategy-dependent generated shape** (shared decoder accepts both only for package-only
  branches) and include the **serializer-only `field.queryset.model`** target source.
  **(M2)** added a **Nullability and defaults** paragraph to Decision 7 (`allow_null` →
  annotation nullability; `required` + DRF `default` → omission; omitted-vs-explicit-`None`
  preserved; `allow_blank` not encoded) with tests. **(M3)** a serializer relation target
  with **no registered primary `DjangoType`** is a class-creation `ConfigurationError`, not
  a default-manager fallback — stricter than the promoted `_visible_related_object` helper,
  whose form behavior stays byte-unchanged (Decision 7). **(M4)** `register_subsystem_clear`
  is now a **mandatory Slice 2 requirement** (static `(module_path, attr)` string rows
  resolved via `_clear_if_importable`), not a budget-dependent fallback — the two-hand-edit
  option is removed. **(M5)** the current-state prose now names the cross-module DRY blast
  radius (`utils/` / `mutations/` / `forms/` / `registry.py` / `types/finalizer.py`).
  **Missing edge cases:** the request-actor-cannot-be-swapped case (H3), two serializer
  fields colliding on one generated GraphQL input name (the serializer analog of
  `forms/inputs.py::_guard_input_attr_collisions`), and two **writable** fields sharing one
  `source` (rejected as a double-write) were pinned. Plus a **Slice 0 floor acceptance
  artifact** (probe script / explicit `uv` commands; the floor recorded in `pyproject.toml`
  + the `require_drf()` hint + Risks) and a **Slice 3 grep-guard** that the serializer
  resolver reads neither `conf.settings` nor `_resolve_globalid_strategy` on the query path.
- **Revision 10** — Slice 4 final-verification reconciliation (Worker 1, build-039). All
  five slices (Slice 0 + Slices 1-4) are final-accepted and on main; the implemented-on-main
  docs (TREE / TODAY / GOAL crit-6 / the GLOSSARY body marked **"implemented on main,
  releasing in 0.0.13"** with the `status` FK kept `planned`) and the card wrap
  ([`DONE-039-0.0.13`][kanban] → Done, all 7 DoD items ticked) landed in Slice 4 (F8 /
  [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)). Reconciled
  the stale header to reality: the body line 3 "Planned for `0.0.13`" and the Status block
  "**IN PROGRESS** … no slice built yet" now read **IMPLEMENTED ON MAIN; release deferred
  to the joint `0.0.13` cut** shared with [`WIP-ALPHA-040-0.0.13`][kanban], which still owns
  the version bump and the public release-status flip (GLOSSARY `shipped (0.0.13)`,
  `README.md` / `docs/README.md` "Shipped today", `CHANGELOG.md` bullets). No version bump,
  no `CHANGELOG.md` / `README.md` Status / `docs/README.md` edit (joint-cut deferrals, F8 —
  confirmed absent from the build diff).

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
  on main, releasing in 0.0.13"**, the `shipped (0.0.13)` flip deferred to the joint cut —
  **F8**) and reconciles the surface keys this spec pins (`Meta.operation` over
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
- [Relation handling][glossary-relation-handling] /
  [Relay Node integration][glossary-relay-node-integration] /
  [`DjangoNodeField`][glossary-djangonodefield] — the relation-decode substrate. The
  serializer relation decoder type- and visibility-checks each `PrimaryKeyRelatedField` /
  `ManyRelatedField` id — a `GlobalID` **or** a raw pk — against the relation's target
  model, reusing the same server-side [`DjangoNodeField`][glossary-djangonodefield] decode
  the `id:` `update` locate rides, across the FK / OneToOne / M2M shapes
  [Relation handling][glossary-relation-handling] spans
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)).
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
  [`tests/rest_framework/`][test-rest-framework]. The new **consumer-facing** subpackage is
  `rest_framework/`, but the card deliberately **promotes shared internals** to avoid third
  copies (M5), so it also edits `utils/converters.py` (new),
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

- [ ] Slice 0 (pre-Slice-1 dependency gate, **F11**): verify + pin the DRF floor **before**
  any converter code, since Slice 1–3 tests import DRF.
  - [ ] **Verify the floor:** confirm a `djangorestframework` release that imports and runs
    **warning-free** across the [`django.yml`][django-workflow] CI matrix (Python
    3.10 → 3.14 × Django 5.2 → 6.0 / `latest`) under [`pytest.ini`][pytest-ini]'s
    `filterwarnings = error` (DRF's Django support lags Django, so a 6.0 / `latest`-clean
    release must be confirmed to exist), and record the **exact pinned floor**
    ([Risks](#risks-and-open-questions)).
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
    `require_drf()` guard's **install hint**, and a one-line note in
    [Risks](#risks-and-open-questions). If no compatible release exists, the card **blocks at
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
    a serializer-only `ChoiceField` is upgraded to a generated enum at the build site (rev6 #6),
    `IntegerField` →
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
  - [ ] **DRY / reuse** ([Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations)):
    `convert_serializer_field` rides the shared fail-loud dispatch **skeleton** promoted to
    `utils/converters.py` (supplying only its precheck table + scalar registry — the
    no-silent-`String`-catch-all contract single-sited with
    [`forms/converter.py`][forms-converter], **P1.4**); the reverse-map field spec is the
    unified `InputFieldSpec` sited in [`utils/inputs.py`][utils-inputs] (the `038`
    `FormInputFieldSpec` analog + the `source` axis, with the conversion result a shared
    shape too — **P2.1**); the input namespace is the promoted `make_input_namespace(...)`
    **one-ledger** trio (the form/mutation clear shape, NOT the heavier
    `clear_generated_input_namespace` — **P2.2**); the `SerializerInputShape` cache + clear is
    the promoted `make_shape_build_cache()` plumbing (**P1.3**); and the divergent-shape
    suffix reuses `mutations/inputs.py::_pascalize_token` (**P2.3**). A grep guard that
    `rest_framework/serializer_converter.py` + `rest_framework/inputs.py` **import** these
    and do not redefine them is the DoD check.
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

    **The clear is wired through the mandatory `register_subsystem_clear` seam (P1.6, F10,
    M4 — NOT two hand-edits).** Rather than hand-add the serializer's clear to **both** sites
    above (a permanent two-list synchronization hazard — and adding the serializer would make
    it a *third* subsystem relying on manually-mirrored clears, exactly the debt this card
    removes), Slice 2 promotes a `register_subsystem_clear(module_path, attr)` seam feeding
    **one canonical list** that **both** the finalizer pre-bind reset and `TypeRegistry.clear()`
    iterate via `_clear_if_importable`. **This is a Slice 2 requirement, not a
    budget-dependent option.** The list holds **static `(module_path, attr)` STRING rows
    only** — it does **not** import the target module at registration time (the serializer row
    is the literal `("…rest_framework.inputs", "clear_serializer_input_namespace")`, resolved
    lazily by `_clear_if_importable`, which already tolerates an absent module). Two
    consequences follow, both load-bearing:
    - **The soft-dep asymmetry vanishes.** Because every entry routes through
      `_clear_if_importable` **by construction**, the special-case the direct mutation / form
      clears would otherwise need for the DRF-behind-soft-import serializer ledger
      (`finalize_django_types` runs on **every** build, including DRF-absent ones, where a
      direct `from ..rest_framework.inputs import …` would raise `ImportError` and break
      schema construction for everyone without DRF) collapses to a **one-line registration**.
      It is also semantically exact: DRF absent ⇒ no
      [`SerializerMutation`][glossary-serializermutation] declared ⇒ the serializer ledger is
      empty ⇒ a skipped clear is a correct no-op.
    - **The import-timing edge is a non-issue (F10).** Storing **strings**, not imported
      callables, means registration never forces a DRF import; the backstop invariant is **a
      subsystem that has created clearable state has, by definition, been imported and
      registered its clear** (stale serializer ledger state implies `rest_framework.inputs`
      was imported in a prior failed bind), so a registered-but-not-yet-imported gap cannot
      leave dirty state.

    A **retry-idempotence test** (materialize serializer input, fail a later type, rerun
    finalization, assert the serializer ledger was cleared) locks it.

    **No new bind entry point** (no `bind_serializer_mutations()`) — that is the dividend
    of the `ModelSerializer`-rides-`DjangoMutation` choice
    ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).
  - [ ] [`__init__.py`][init]: export `SerializerMutation` (one net-new public symbol)
    via a **root-level `__getattr__`** (PEP 562) — `SerializerMutation` is resolvable by
    **name** (`from django_strawberry_framework import SerializerMutation`) through the
    shared `require_drf()` guard (DRF absent → `ImportError` with the install hint), but is
    **NOT added to `__all__`** while DRF is soft, so `from django_strawberry_framework
    import *` stays DRF-free and never trips the guard (**F1** — a star import consults
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
    new `_VALID_SERIALIZER_OPERATIONS`, **P1.2**), and the promoted
    `reject_unknown_meta_keys(name, meta, allowed)` typo-guard called with
    `_ALLOWED_SERIALIZER_META_KEYS`, then returns a `_ValidatedMutationMeta` (**P2.5** /
    **P2.7**); the field-sequence call is
    `utils/inputs.py::normalize_field_name_sequence(..., flavor="SerializerMutation")`
    **directly** — no third re-binding wrapper alongside the model
    (`_normalize_field_sequence`) / form (`normalize_form_field_sequence`) ones (**P2.7** —
    the required keyword-only `flavor` arg exists for exactly this); the `build_input` /
    `input_type_name` cluster rides the promoted `build_and_stash_input` core
    (materialize-then-stash, NOT a byte-parallel `_build_and_stash_serializer_input`,
    **P1.7**) — but its per-shape dedupe is keyed on the `SerializerInputShape` DESCRIPTOR,
    which is only knowable AFTER the build, so it does NOT route through
    `cached_build_input` (whose pre-build key lookup the form flavor can use but the
    serializer cannot without building the shape twice); the
    `get_serializer_kwargs` waiver reuses the generalized
    `_hook_overridden(cls, base, name)` (**P2.6**); and the input-ledger clear registers
    through `register_subsystem_clear` (**P1.6**, the finalizer item above). The serializer's
    only genuinely-new `_validate_meta` logic is the `serializer_class`
    is-a-`ModelSerializer` (+ resolvable `Meta.model`) check and `optional_fields`
    normalization.
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
    model-attr-keyed `036` `_decode_relation_id_set`). **The generated input field exposes
    exactly ONE strategy-dependent shape** (Decision 7): a `GlobalID` when the target primary
    [`DjangoType`][glossary-djangotype] is Relay-shaped, else the target's raw-pk scalar — so
    a live request can only deliver the one shape the annotation admits; the **shared decode
    helper** accepts both a `GlobalID` and a raw pk only because it is reused and package
    tests drive the raw-pk / non-Relay branch by direct call (M1). Each id the decoder sees
    is type-checked against the relation's **target model** — resolved from the backing FK
    via the serializer field's `source`, **or, for a serializer-only relation, from the DRF
    field's `queryset.model`** (Decision 7) —
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
    and an **observable request-context path** — an explicit `validate()` /
    `validate_<field>()` that reads `self.context["request"].user`, proving the injected
    `context={"request": …}` lands. **The live proof must be a `validate()` branch, not a
    `HiddenField(default=CurrentUserDefault())`** (**F9**): DRF hidden-field defaults are
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
  - [ ] **DRY / reuse** ([Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations)):
    the sync pipeline rides the promoted `run_write_pipeline_sync(...)` skeleton **scoped to
    model-backed create/update only** (delete + model-less plain form excluded, **F6**) —
    the serializer supplies only `decode_step` + `write_step` callbacks (construct /
    `is_valid()` / `save()`), and the `transaction.atomic()` boundary + the
    **authorize-before-decode security ordering** is single-sited across the three
    model-backed flavors, not hand-copied a third time, with the existing model / model-form
    suites staying byte-equivalent (**P1.5**); the relation decoder re-keys over the promoted `_visible_related_object`
    in [`utils/querysets.py`][utils-querysets] rather than forking a third object-returning
    decoder (**P1.1**); and `serializer_errors_to_field_errors` (recursive, legitimately new)
    imports the shared `mutations/inputs.py::NON_FIELD_ERROR_KEY` sentinel — and ideally a
    promoted `field_error(path, messages)` leaf ctor both flatteners call — so the DRF
    `non_field_errors` → `"__all__"` mapping cannot drift from the flat `036` mapper
    (**P2.4**). The promotions themselves edit `mutations/resolvers.py` / `utils/querysets.py`
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
  **Soft-dep wiring is NOT here — it landed in the pre-Slice-1 gate (Slice 0, F11), since
  Slice 1–3 tests import DRF.** Release-status wording is **split from implementation
  docs** (**F8**):
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
   the joint cut. `uv.lock` **is** updated in the **Slice 0 dependency gate** (regenerated
   for the `[dependency-groups].dev` DRF add, **before** Slice 1 imports DRF in tests —
   **F11**, not Slice 4), but its `django-strawberry-framework` package `version` entry
   stays `0.0.12` — the lockfile's dependency graph changes, the package version does not
   ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).

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
- **Serializer-derived output types.** The mutation **output** is the primary
  [`DjangoType`][glossary-djangotype] in the frozen `node` / `result` slot — **not** a
  serializer-derived output type (the card's "dual-purposed for inputs and outputs" wording is
  reconciled to the frozen slot, [Risks](#risks-and-open-questions)). Nested writable
  serializers (`ParsedObject`-style nested create / connect) were originally the `036`
  nested-write non-goal; they now ship as the EXPLICIT opt-in `Meta.nested_fields` (rev6 #17 —
  the serializer owns the nested write, the framework never auto-saves the relation).
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

**Shared-helper homes (the DRY promotions land outside `rest_framework/`).** The
[Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations) section
single-sites the helpers the form flavor already forked from the model flavor, so the
serializer flavor imports rather than re-implements: the **fail-loud converter dispatch
skeleton** (**P1.4**) lands in a new `utils/converters.py`; the **relation-decode core**
(`_visible_related_object`, **P1.1**) is promoted into [`utils/querysets.py`][utils-querysets];
the **shape-build cache** (**P1.3**), **build/stash core** (**P1.7**), **non-delete ops
constant** (**P1.2**), and the **`reject_unknown_meta_keys`** typo-guard (**P2.7**) land in
[`mutations/sets.py`][mutations-sets] (or a sibling `mutations/bind_helpers.py`); the
**sync write-pipeline skeleton** (**P1.5**) in [`mutations/resolvers.py`][mutations-resolvers];
the unified **input-namespace trio / field-spec** (**P2.1** / **P2.2**) in
[`utils/inputs.py`][utils-inputs]; and the **`register_subsystem_clear`** seam (**P1.6**)
spans [`types/finalizer.py`][types-finalizer] + [`registry.py`][registry]. These promotions
edit `mutations/` / `utils/` (and `forms/` re-points to the shared site), so the
"near-zero edit to `mutations/`" estimate elsewhere is the *no-DRY-promotion* floor; the
promotions are the cheap-now single-siting this card chooses to pay.

### Decision 5 — Public surface: `SerializerMutation` exported from the root, the `038`-generalized factory reused

One net-new public symbol, re-exported from [`__init__.py`][init] as a **lazy export via
the root `__getattr__`** — and, while DRF is a soft dependency, **deliberately NOT added
to `__all__`** (so `from … import *` stays DRF-free for consumers who never write a
serializer mutation; the named `from django_strawberry_framework import SerializerMutation`
still resolves through `__getattr__`, [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy), F1):

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

**Cross-flavor reuse ([DRY obligations](#cross-flavor-reuse-and-dry-obligations)).**
Because this base is "the **exact** override set `DjangoModelFormMutation` uses," its
`_validate_meta` and `build_input` overrides are on track to be a third byte-parallel
copy of the form cluster. The spec instead requires the serializer to ride shared sites:
`_validate_meta` reuses `mutations/sets.py::_validate_permission_classes`, the shared
field-sequence normalize, the shared non-delete ops set, and returns a
`_ValidatedMutationMeta` (**P2.5**); the `declared - allowed` typo-guard is the promoted
`reject_unknown_meta_keys(name, meta, allowed)` called with the serializer's own
`_ALLOWED_SERIALIZER_META_KEYS`, and the field-sequence call is
`normalize_field_name_sequence(..., flavor="SerializerMutation")` **directly** — no third
re-binding wrapper alongside the model (`_normalize_field_sequence`) / form
(`normalize_form_field_sequence`) ones (**P2.7**); the build/stash/name seam rides the
promoted `build_and_stash_input` core rather than spelling
`_build_and_stash_serializer_input` (**P1.7**), but its descriptor-keyed per-shape dedupe —
the `SerializerInputShape` is only knowable AFTER the build — is an inline lookup-or-store,
NOT `cached_build_input` (whose pre-build key lookup would force building the shape twice);
and the
input-namespace clear **registers through the mandatory `register_subsystem_clear` seam**
(**M4**, not a budget-dependent fallback) instead of being hand-added to both the finalizer
pre-bind reset and `registry.clear()` — which, because every entry routes through
`_clear_if_importable`, **collapses the import-guarded-clear asymmetry** the Slice-2
checklist would otherwise spell out by hand (**P1.6**). The serializer's only genuinely-new `_validate_meta` logic is then the
`serializer_class` is-a-`ModelSerializer` (+ resolvable `Meta.model`) check and the
`Meta.optional_fields` normalization.

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

- `CharField` (and `EmailField` / `SlugField` / `URLField` / `RegexField` / `IPAddressField`
  via MRO) → `str`. A serializer-only `ChoiceField` → a **GENERATED enum** at the build site
  (rev6 #6): the converter's *base* mapping is `str`, upgraded to the enum by
  `resolve_serializer_field` where `type_name` is known (the same finalize-at-the-build-site
  pattern relations / files use). Over a `ModelSerializer` `choices` column an auto-generated
  field reuses the read-side column [enum][glossary-choice-enum-generation]; a
  CONSUMER-DECLARED `ChoiceField` — even `source`-mapped to a plain (non-choice) column —
  emits the serializer-only enum too (rev6 rev2 P2: declared choices are a schema-affecting
  override, never collapsed back to `String`). `FilePathField` stays `str` (dynamic filesystem
  choices, not a stable enum).
- `IntegerField` → `int`, `FloatField` → `float`, `DecimalField` → `Decimal`,
  `BooleanField` → `bool`, `UUIDField` → `uuid.UUID`.
- `DateField` / `DateTimeField` / `TimeField` → Python-native; `DurationField` → `str` (a
  deliberate wire scalar, rev6 #7).
- `DictField` / `HStoreField` → `strawberry.scalars.JSON`; `ModelField` → its wrapped Django
  column's scalar (rev6 #7).
- `JSONField` → `strawberry.scalars.JSON`; `ListField` → `list[<scalar child>]` — the
  `child` is converted **recursively through the same scalar registry**
  (`ListField(child=IntegerField())` → `list[int]`); a `ListField` whose `child` is a
  **relation field or a (nested) serializer** is **out of scope** →
  [`ConfigurationError`][glossary-configurationerror] naming the field (a relation list is
  expressed via `ManyRelatedField` / `PrimaryKeyRelatedField(many=True)`, and a nested
  serializer is the `036` nested-write non-goal — a `ListField` must not become a
  back-door to either). A serializer-only `MultipleChoiceField` → `list[<generated enum>]`
  (rev6 #6; base `list[str]`, upgraded at the build site like `ChoiceField`).
- `PrimaryKeyRelatedField` → the target's id (`relation_single`), `many=True` /
  `ManyRelatedField` → `list[<id>]` (`relation_multi`); the generated field carries
  **exactly one** id annotation, **strategy-dependent on the target** — the target primary
  [`DjangoType`][glossary-djangotype]'s `GlobalID` when it is Relay-Node-shaped, else the
  target's **raw-pk scalar** — decided at the build site (a live request can only submit
  the one shape that annotation admits; "accepts both `GlobalID` and raw pk" is the shared
  decode *helper*'s contract, not a single generated field's, [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload) step 3 / F3).
- `FileField` / `ImageField` → [`Upload`][glossary-upload-scalar] (`file`).
- A nested `ModelSerializer` / `ListSerializer` field → **fail-loud by default**, surfaced
  as a `ConfigurationError` — UNLESS the mutation EXPLICITLY opts it in via
  `Meta.nested_fields = {"<field>": NestedSerializerConfig(...)}` (rev6 #17), which builds the
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

**Serializer-only relation fields — supported via `field.queryset.model` (F4).** A real
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
`ManyRelatedField.child_relation` precedent.)

**A relation target with no registered primary `DjangoType` is a build-time
`ConfigurationError` (M3).** Whether the target model comes from the backing FK (via
`source`) or from `field.queryset.model`, the package's relation-decode promise is
**visibility-scoped**: every related id is resolved through the target's primary
[`DjangoType`][glossary-djangotype]'s [`get_queryset`][glossary-get_queryset-visibility-hook].
A target model with **no registered primary `DjangoType`** cannot honor that promise — so a
serializer relation field whose target lacks one is a **class-creation**
[`ConfigurationError`][glossary-configurationerror] **naming the serializer field and the
target model**, not a silent runtime fallback to `Model._default_manager` (which would write
a hidden / unseeable row, overstating the visibility guarantee). This is **stricter than the
promoted [`forms/resolvers.py`][forms-resolvers] `_visible_related_object` helper**
(**P1.1**), which keeps a no-primary-type **default-manager fallback** for the form flavor's
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

**Nullability and defaults (M2) — `allow_null` and `required` are two different axes.**
GraphQL input nullability and DRF requiredness are **orthogonal**, so the converter pins
them separately:

- **Annotation nullability follows `field.allow_null`.** A field with `allow_null=True`
  gets a nullable GraphQL annotation (`T | None` / `Optional[T]`); `allow_null=False` keeps
  the bare annotation. This is independent of requiredness — DRF's
  `required=True, allow_null=True` means *"the client must send the key, but may send
  `null`,"* which a plain GraphQL input cannot express as **both** required and nullable.
  The package resolves it by making the annotation **nullable** (so `null` is accepted) and
  enforcing the *must-provide* half at the DRF layer: **omission must still reach DRF as
  "missing"** so `serializer.is_valid()` raises the field-`required` error itself, rather
  than the converter forcing a non-null GraphQL field that would reject a legitimate `null`.
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

**Cross-flavor reuse ([DRY obligations](#cross-flavor-reuse-and-dry-obligations)).** The
converter + input generator is where the form flavor forked the most from the model
flavor, so the serializer is on track to be the third copy of each. The spec pins the
reuse: the fail-loud dispatch is the shared `(field, isinstance_prechecks,
scalar_registry, fallthrough_error_factory) → conversion` **skeleton** in a new
`utils/converters.py` — `convert_serializer_field` supplies only its precheck table +
scalar registry, so the **GOAL-mandated no-silent-`String`-catch-all contract is
single-sited** across `forms/converter.py` and the serializer converter (**P1.4**); the
reverse-map field spec is the unified `InputFieldSpec` (the `038` `FormInputFieldSpec`
analog plus the `source` axis) sited in [`utils/inputs.py`][utils-inputs], not a third
ad-hoc dataclass (**P2.1**); the `SerializerInputShape` descriptor identity is
legitimately new, but its **cache + clear plumbing** is the promoted
`make_shape_build_cache()` (**P1.3**) and its **stash procedure** the promoted
`build_and_stash_input` (**P1.7**) — though, because the descriptor cache key is only
knowable after the build, the per-shape dedupe stays an inline lookup-or-store rather than
`cached_build_input` (whose pre-build key lookup would force building the shape twice); the
input namespace is the
promoted `make_input_namespace(...)` **one-ledger** trio — the form / mutation clear
shape, **not** the heavier `clear_generated_input_namespace` (**P2.2**); the
divergent-shape suffix reuses `mutations/inputs.py::_pascalize_token` (**P2.3**); and the
`get_serializer_kwargs` create-required **waiver** reuses the generalized
`_hook_overridden(cls, base, name)` rather than re-deriving the `cls.<name> is base.<name>`
test (**P2.6**).

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
   `038` form decoder (`_visible_related_object`) already enforce — and reduced to the
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
4. **Construct** the serializer via the overridable
   `get_serializer_kwargs(info, *, data, instance=None)` hook (the graphene
   `get_serializer_kwargs` parity seam). **The hook + framework precedence is pinned
   exactly** (it is the update contract, not a soft default):
   - **Default hook return shape:** `{"data": provided_data}` on `create`;
     `{"data": provided_data, "instance": <row>}` on `update`; plus
     `"context": {"request": request_from_info(info, family_label="SerializerMutation")}`
     in both — the package's shared request-extraction helper
     ([`utils/permissions.py`][utils-permissions] `request_from_info`, which resolves both
     `info.context.request` and a bare `HttpRequest` `info.context`, the same helper the
     permission seam uses) — so the serializer's own request-aware validators resolve.
   - **The hook does not own the whole kwargs dict — the framework merges over it.** A
     consumer override may add or replace kwargs (e.g. extra `context` keys, an extra
     constructor kwarg), but the framework applies two **non-overridable** rules after the
     hook returns: (i) **`partial`** is framework-owned — the resolver injects
     `partial=True` for `update` (and never sets it for `create`); a hook that returns
     `partial=False` (or `partial=True` on a create) is a
     [`ConfigurationError`][glossary-configurationerror] (`partial` is the update
     contract, not a knob); and (ii) **`context["request"]` is strictly framework-owned —
     the actor cannot drift from the permission seam (H3).** The framework **merges** the
     override's `context` dict (its other keys win) and then sets
     `context["request"] = request_from_info(info, family_label="SerializerMutation")`
     **unconditionally** — the **same** request object the inherited `check_permission` /
     `permission_classes` seam already authorized against. There is **no escape hatch** for a
     *different* request: if the override supplies a `context["request"]` that **is not** the
     framework's `request_from_info(...)` object, that is a
     [`ConfigurationError`][glossary-configurationerror] (a serializer that validated against
     a different actor than the write-auth seam authorized would let permission and
     validation disagree about user / tenant — a silent authorization-consistency bug);
     supplying the **same** object is tolerated (idempotent). Consumer-specific context
     belongs under **other** keys, never `request`. A hook that omits `data` is filled with
     `provided_data`. This makes "override adds a kwarg," "override cannot disable partial,"
     and "override cannot swap the request actor out from under the permission check" all
     well-defined.
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
   `save_or_field_errors(_do_save)` call and routes by **exception class** — they are
   **not** one branch:
   - **DRF `ValidationError`** (`rest_framework.exceptions.ValidationError` /
     `serializers.ValidationError`): route its `.detail` through the **recursive**
     `serializer_errors_to_field_errors` flattener (the same nested structure
     `serializer.errors` produces).
   - **Django `ValidationError`** (`django.core.exceptions.ValidationError`): route through
     the flat `036` [`mutations/resolvers.py`][mutations-resolvers]`::validation_error_to_field_errors`,
     which already reads Django's `error_dict` / `messages` shape (verified — it does **not**
     read `.detail`); pushing a Django error through the DRF `.detail` path would
     `AttributeError` or silently lose structure.
   - **`IntegrityError`** (a concurrent-uniqueness race / residual db constraint): the `036`
     `save_or_field_errors` mapper.

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
envelope key is a serializer name. Nested sub-paths below the root segment (a `ListField`
index, a `JSONField` key) keep DRF's structure — they have no separate input identity. The
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

**Cross-flavor reuse ([DRY obligations](#cross-flavor-reuse-and-dry-obligations)).** This
pipeline carries the package's load-bearing **security ordering** (authorize → decode), so
its DRY promotions matter most. The whole **sync orchestration** — the
`transaction.atomic()` boundary, the create-vs-update branch, the `coerce_lookup_id →
locate_instance → not_found_error → authorize_or_raise` preamble, and the
`refetch_optimized → build_payload` tail — rides the promoted
`run_write_pipeline_sync(...)` skeleton, **scoped to the model-backed create/update
flavors only** (model `DjangoMutation` create/update, `DjangoModelFormMutation`, and this
serializer flavor) — **not** a universal write skeleton. `delete` (no `data`, no relation
decode, snapshot-before-delete payload) and the **model-less plain form** (no instance, no
primary type, no optimizer re-fetch) are **excluded**; folding them in would make the
skeleton a leaky generic framework instead of a small create/update helper. The callback
contract is precise: the skeleton owns atomicity, locate, the not-found payload,
**authorization before `decode_step`**, the optimizer re-fetch, and payload construction;
each flavor supplies only `decode_step(ctx) -> decoded data | list[FieldError]` and
`write_step(ctx, decoded) -> saved instance | list[FieldError]` (the serializer's
`write_step` is construct / `is_valid()` / `save()`). The **authorize-before-decode
invariant is single-sited** across the three model-backed flavors rather than hand-copied
a third time, and the existing model + model-form behavior must stay **byte-equivalent
under their current tests** before serializer code lands (**P1.5**, **F6**). The relation
decoder re-keys over the
promoted `_visible_related_object` (in [`utils/querysets.py`][utils-querysets]) instead of
forking a third object-returning, field-keyed decoder (**P1.1**). And the recursive
`serializer_errors_to_field_errors` flattener — legitimately new — imports the shared
`mutations/inputs.py::NON_FIELD_ERROR_KEY` sentinel (and, ideally, a promoted
`field_error(path, messages)` leaf ctor both flatteners call), so the DRF
`non_field_errors` → `"__all__"` convention cannot drift between the flat `036` mapper and
this recursive one (**P2.4**, step 5).

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

**Cross-flavor reuse ([DRY obligations](#cross-flavor-reuse-and-dry-obligations)).** The
`{create, update}` set the serializer `_validate_meta` checks against is **byte-identical**
to `forms/sets.py::_VALID_FORM_OPERATIONS` (both being "a validating write flavor that does
not delete"), and `mutations/sets.py::_VALID_OPERATIONS` is the `{create, update, delete}`
superset. The serializer must **not** define a `_VALID_SERIALIZER_OPERATIONS`: a single
`NON_DELETE_WRITE_OPERATIONS` constant is promoted (to [`mutations/sets.py`][mutations-sets])
and **both** the form and serializer `_validate_meta` overrides import it, so the rule and
the "no serializer/form delete" message single-site (**P1.2**).

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
| `from django_strawberry_framework import *` | **Always succeeds and omits `SerializerMutation`** — the name is **not** in `__all__` while DRF is soft, so a star import never resolves it through `__getattr__` and never trips the DRF guard. A DRF-absent consumer who does `import *` today keeps working unchanged (no breaking regression). |

One shared **`require_drf()`** helper (in `rest_framework/__init__.py`) owns the single
install-hint message and is the one place every `rest_framework/` module and the root
`__getattr__` route the guard through (no duplicated try/except message strings) — the
[`types/converters.py`][types-converters] soft-import precedent (`_resolve_array_field`
/ `_resolve_hstore_field`, which return `None` on `ImportError`) generalized to a
*raising* guard with an actionable message.

**`SerializerMutation` is a public lazy export but is NOT added to `__all__` while DRF is
a soft dependency (F1).** Star import (`from … import *`) consults `__all__` and accesses
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
re-break the soft-dep contract.) This reverses the earlier draft's "stays in `__all__`"
choice, which assumed a `0.0.14` `channels` / `debug_toolbar` hard-dep posture that does
not hold while DRF is soft.

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
   **pre-Slice-1 dependency gate (Slice 0), not Slice 4** (**F11**) — because the Slice 1–3
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
   imports DRF in tests. This is the pre-Slice-1 floor check in
   [Risks](#risks-and-open-questions), not an implementation-time discovery.
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
[`spec-037`][spec-037]. **Release-status wording is split from implementation docs
(F8):** Slice 4 updates **implemented-on-main** docs ([`docs/TREE.md`][tree],
[`TODAY.md`][today], and the [`docs/GLOSSARY.md`][glossary] body to the implemented
contract) but the **public "shipped (0.0.13)" status, the README "Shipped today" prose,
and the release changelog defer to the joint cut** — otherwise the repo would advertise a
released `0.0.13` feature while `[project].version` / `__version__` / `test_version` still
report `0.0.12`. The version line and the version files stay at `0.0.12` until the joint
cut. (The [`GOAL.md`][goal] crit-6 example correction lands in this card regardless — the
current example is wrong the moment the code lands.)

**`uv.lock` is NOT a version file — it is updated in this card, deliberately.** The
repository commits a `uv.lock` (verified, `git`-tracked), and the **pre-Slice-1 dependency
gate (Slice 0, F11)** adds `djangorestframework` to `[dependency-groups].dev`
([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
Changing a dev dependency **without** regenerating the lockfile leaves the declared and
locked environments out of sync, so the clean cut is to **edit `pyproject.toml` and
regenerate `uv.lock` together** in that gate (`uv lock` after the dev-group add) — before
Slice 1 imports DRF in tests. The distinction the version policy must keep is: the **DRF
dependency entries** in `uv.lock` *do* change here; the **package's own version** —
`[project].version` *and* the `[[package]] name = "django-strawberry-framework"` `version`
entry inside `uv.lock` — stays `0.0.12` until the joint cut. (An earlier draft lumped
`uv.lock` with the version files, which contradicted the dev-group add; this reconciliation
resolves it.)

Justification: per [`docs/SPECS/NEXT.md`][next] Step 3 / Step 6, when multiple cards
target one patch version the bump belongs to the joint cut, not any individual card's
spec. `039` and `040` both target `0.0.13`.

Alternatives considered (and rejected):

- **Bump to `0.0.13` in this card's Slice 4.** Rejected: `040` also ships into
  `0.0.13`; a per-card bump races the joint cut and would have to be reconciled when
  the sibling lands.

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
[`forms/resolvers.py`][forms-resolvers]'s `_visible_related_object` exists because the
`036` `_relation_visibility_error` *"does not return"* the object, and
[`registry.py`][registry]'s clear block documents a *"same two-block shape"* mirrored per
flavor. Each is a chance to **promote to a shared site now**, while the second consumer
([`forms/`][forms-sets]) and the third ([`rest_framework/`][rf-sets]) are both in view —
the cheapest moment to single-site. The promotion targets below are the spec's binding
implementation obligations; each is pinned into its Decision and its Slice DoD line, and
the per-module import manifest at the end is the DoD-checkable "DRY contract."

Reuse claims here were verified against the source first; corrections to the originating
review are folded in (the form bases normalize their field sequence through
`forms/sets.py::_resolve_effective_form_field_names`, **not** `_normalize_field_sequence`,
so the serializer follows the *model* flavor's `_normalize_field_sequence` precedent for
that piece (**P2.5** / **P2.7**); no `field_error(...)` constructor exists yet — `FieldError`
is a `@strawberry.type` built directly, so **P2.4** is a *promotion proposal*, with the
already-shared `mutations/inputs.py::NON_FIELD_ERROR_KEY` sentinel the hard reuse;
`forms/sets.py::_form_kwargs_overridden` already exists as the helper **P2.6** generalizes;
and no `register_subsystem_clear` seam exists today — both clear lists in **P1.6** are
hand-maintained, confirmed).

### Confirmed reuse — lock as import obligations

These the spec already states in prose. A prose "reuses the `036` helper" does not stop an
implementer quietly re-spelling it, so each becomes a Slice DoD line of the form
**"imported from `<module>`, not re-implemented"** (ideally backed by a one-line import /
identity guard that the symbol is imported and not redefined under `rest_framework/`):

- **By call from [`mutations/resolvers.py`][mutations-resolvers]** (Decision 8):
  `locate_instance`, `coerce_lookup_id`, `authorize_or_raise`, `refetch_optimized`,
  `build_payload`, `not_found_error`, `save_or_field_errors`, `payload_cls_for`,
  `run_pipeline_async`, `_coerce_relation_pk_or_none`, `raw_choice_value`.
- **By call from [`utils/`][utils-permissions]:**
  `utils/permissions.py::request_from_info(info, family_label="SerializerMutation")`
  (already accepts a family label — no edit), `utils/inputs.py::build_strawberry_input_class`
  + `materialize_generated_input_class`.
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

### Promotions to single-site now (P1 — third-copy forks)

| # | Duplicated today (`mutations/` ↔ `forms/`) | Promote to | Serializer obligation | Pin |
| --- | --- | --- | --- | --- |
| **P1.1** | The relation-decode core: `mutations/resolvers.py::_decode_relation_id_set` (+ `_relation_membership_error` / `_relation_visibility_error` / `_raw_pk_relation_error` / `_relation_existence_error`) returns *errors*; [`forms/resolvers.py`][forms-resolvers] rolled its own object-returning, field-keyed `_visible_related_object` / `_decode_form_relation_single` / `_decode_form_relation_multi` because the `036` helper *"does not return"* the object | `_visible_related_object(related_model, pk, info) -> obj \| None` to [`utils/querysets.py`][utils-querysets] (beside `visibility_scoped_related_queryset`, whose composition it already uses); better, the whole one-id *decode-or-coerce → visible-object → no-leak `FieldError`* shape into a shared core taking a small per-flavor descriptor | Re-key the serializer relation decoder over the promoted `_visible_related_object`; do **not** re-implement the visibility / membership check (third copy avoided). The serializer is **stricter on the no-primary-type case (M3)** — it guards at class creation (a relation target with no registered primary `DjangoType` is a `ConfigurationError`), so it never reaches the helper's default-manager fallback; that fallback stays the **form flavor's** behavior, **byte-unchanged** (the stricter path is a class-creation guard, not a change to the shared helper) | [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) + [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload) + Slice 3 resolver checklist |
| **P1.2** | `forms/sets.py::_VALID_FORM_OPERATIONS = {"create", "update"}` is byte-identical to the serializer need; `mutations/sets.py::_VALID_OPERATIONS` is the `{create, update, delete}` superset | A single `NON_DELETE_WRITE_OPERATIONS` constant (to [`mutations/sets.py`][mutations-sets]) both the form and serializer `_validate_meta` import | Import `NON_DELETE_WRITE_OPERATIONS`; do **not** define a `_VALID_SERIALIZER_OPERATIONS`; the "no serializer/form delete" message single-sites too | [Decision 10](#decision-10--operations-create--update-no-serializer-delete) + Slice 2 `_validate_meta` |
| **P1.3** | The per-declaration shape-build cache: `mutations/sets.py::_shape_build_cache` and `forms/sets.py::_form_shape_build_cache` (commented *"twin of"*) + `clear_form_shape_build_cache` | A `make_shape_build_cache()` helper returning the module-level dict + a registered `clear()` wired into the finalizer's pre-bind reset | The `SerializerInputShape` descriptor identity stays legitimately new; only the cache **+ clear plumbing** is shared — do not hand-mirror a third dict + clear | [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) + Slice 2 finalizer-reset checklist |
| **P1.4** | The fail-loud converter dispatch skeleton: [`forms/converter.py`][forms-converter]'s `convert_form_field` (isinstance pre-checks → `type(field).__mro__` walk over `_SCALAR_FORM_FIELDS` → exact-base-`Field` case → raising `ConfigurationError` fallthrough) imports **nothing** from `utils/` — a free-standing skeleton | A shared dispatch skeleton — `(field, isinstance_prechecks, scalar_registry, fallthrough_error_factory) → conversion` — to a new `utils/converters.py`; the unified conversion / field-spec dataclass (**P2.1**) rides with it | `convert_serializer_field` supplies only its precheck table + scalar registry; the **GOAL-mandated fail-loud contract** (no silent `String` catch-all) is single-sited and cannot drift between the two converters | [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) (converter) + [Decision 4](#decision-4--module-and-test-locations-rest_framework-subpackage-mirroring-forms) (skeleton home) + Slice 1 |
| **P1.5** | The **sync write-pipeline orchestration**: `mutations/resolvers.py::_run_pipeline_sync` → `_run_create` / `_run_update` (one `transaction.atomic()`; tail partly factored as `_validate_save_assign_refetch_payload`) is re-spelled by `forms/resolvers.py::_run_modelform_pipeline_sync` (model-backed) — each re-writing the atomic block + the `coerce_lookup_id → locate_instance → not_found_error` preamble + the **authorize-before-decode** ordering | `run_write_pipeline_sync(...)` to [`mutations/resolvers.py`][mutations-resolvers], **scoped to model-backed create/update only** — owning atomicity, the create-vs-update branch, the locate→authorize preamble, **authorization before `decode_step`**, and the `refetch_optimized → build_payload` tail; extend `_validate_save_assign_refetch_payload` into the full preamble+tail. **Exclude `delete`** (no data / no decode / snapshot payload) **and the model-less plain form** (no instance / no primary type / no re-fetch) — not a universal skeleton (**F6**) | The serializer supplies only `decode_step(ctx) -> decoded \| list[FieldError]` and `write_step(ctx, decoded) -> saved \| list[FieldError]` (construct / `is_valid()` / `save()`); it does **not** re-spell the atomic block or the **authorize-before-decode security ordering** — the audit's single highest-value promotion (a security invariant, not just a shape). The existing model + model-form behavior must stay **byte-equivalent under their current tests** before serializer code lands | [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload) + Slice 3 resolver checklist |
| **P1.6** | Two hand-maintained ledger-clear lists with no registration seam: the [`finalize_django_types`][types-finalizer] pre-bind reset (direct, unconditional `clear_mutation_input_namespace()` + `clear_form_input_namespace()` before `bind_mutations()`) **and** `registry.py::TypeRegistry.clear()`'s `_clear_if_importable` co-clear rows (incl. the form shape cache; the block's own comment notes a *"same two-block shape"* mirrored per flavor) | A `register_subsystem_clear(module_path, attr)` seam feeding **one** canonical list that **both** the finalizer pre-bind reset and `registry.clear()` iterate via `_clear_if_importable` (import-guarded by construction) | The serializer's `clear_serializer_input_namespace` is registered as a **static `(module_path, attr)` row** (resolved lazily by `_clear_if_importable` — no DRF import at registration, so the import-timing edge is a non-issue, **F10**) instead of being hand-added to both lists — and because every entry routes through `_clear_if_importable`, the soft-dep import-guarded **asymmetry vanishes**, collapsing the spec's whole Decision-6 / Slice-2 "import-guarded clear" caveat to a one-line registration. Invariant: a subsystem with clearable state has by definition been imported + registered | [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven) + Slice 2 finalizer-reset checklist |
| **P1.7** | The `build_input` build/stash/name seam **implementation cluster**: the model does it inline (`DjangoMutation.build_input` → `_materialize_input_for`; `input_type_name`); [`forms/sets.py`][forms-sets] grew a private mirror — `_cached_build_form_input` (per-shape dedupe + the load-bearing **guard-before-cache-lookup** ordering), `_build_and_stash_form_input` (materialize-then-stash `_input_field_specs`), `_form_input_type_name_for`, `_modelform_operation_kind` | `cached_build_input(shape_key, *, guard, build_fn) -> (input_cls, field_specs)` (owns the per-pass lookup + the **guard-before-lookup** ordering) + `build_and_stash_input(cls, *, build, materialize)` to [`mutations/sets.py`][mutations-sets] (or a new `mutations/bind_helpers.py`) | The serializer supplies only its generator, materialize fn, and shape descriptor, and rides `build_and_stash_input` (materialize-then-stash) — NOT a byte-parallel `_build_and_stash_serializer_input`. It does **not** ride `cached_build_input`: that helper looks its key up BEFORE building, but the serializer's key is the `SerializerInputShape` descriptor, only knowable AFTER the build, so forcing it through the helper would build the shape twice (the waste P1.7 names). The descriptor-keyed dedupe therefore stays an inline lookup-or-store keyed on the post-build descriptor, while the per-declaration guard-before-dedupe ordering is preserved directly. (Layering: **P1.3** is the cache *dict*, **P2.1** the spec *shape*, **P1.7** the build *procedure* — promoting the stash core + the shape/cache plumbing is what stops `rest_framework/sets.py` being a line-for-line `forms/sets.py`) | [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven) / [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) + Slice 2 `sets.py` checklist |

### Single-siting that prevents drift (P2)

- **P2.1 — unify the field-spec / conversion types.** `utils/inputs.py::GeneratedInputFieldSpec`
  (`@dataclass`), `forms/converter.py::FormInputFieldSpec` (`@dataclass`) +
  `FormFieldConversion` (a `__slots__` class, **not** a dataclass), and the planned
  serializer reverse-map are the same idea with flavor-specific extra axes (the serializer's
  is "the `038` `FormInputFieldSpec` analog **plus the `source` axis**"). Define **one**
  generic `InputFieldSpec` in [`utils/inputs.py`][utils-inputs] (shared core +
  optional `source`), or subclass `FormInputFieldSpec`; at minimum **site the serializer
  spec in `utils/inputs.py`** so all three live in one module. Unify the conversion result
  (`annotation` + `kind` + `required`) into one shared shape too. ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth).)
- **P2.2 — the input-namespace clear is a third one-ledger lifecycle.** The four-part
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
- **P2.3 — reuse `_pascalize_token`.** The descriptor-derived names for narrowed / divergent
  shapes reuse the injective single-token encoder `mutations/inputs.py::_pascalize_token`
  (which `forms/inputs.py::form_input_type_name` already imports), not a third suffix
  encoder; the canonical `<Serializer>Input` / `<Serializer>PartialInput` names need no
  helper. ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth).)
- **P2.4 — share the error-flattener leaf primitive.** `serializer_errors_to_field_errors`
  is legitimately new (recursive — the flat `036`
  `mutations/resolvers.py::validation_error_to_field_errors` cannot walk DRF's nested tree).
  But its **base case** — construct a `FieldError(field=<path>, messages=[...])` and map
  DRF's `non_field_errors` bucket to the package's `"__all__"` sentinel — is the convention
  the `036` mapper already encodes (`NON_FIELD_ERRORS` → `mutations/inputs.py::NON_FIELD_ERROR_KEY`).
  The hard reuse is **importing that shared `NON_FIELD_ERROR_KEY`** (no re-spelling
  `"__all__"`); the optional promotion is a small `field_error(path, messages)` leaf ctor
  (no such ctor exists yet — `FieldError` is built directly) that **both** the flat and
  recursive flatteners call so the sentinel convention cannot drift.
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload) step 5.)
- **P2.5 — `_validate_meta` reuses the base sub-validators.** Call
  `mutations/sets.py::_validate_permission_classes`, the non-delete ops check against the
  shared **P1.2** set, and the field-sequence normalize, then return a
  `_ValidatedMutationMeta` — do not re-spell the typo-guard / mutual-exclusion logic. The
  serializer follows the **model** flavor's `mutations/sets.py::_normalize_field_sequence`
  precedent for field-sequence normalization (the form bases route theirs through the
  Slice-1 `forms/sets.py::_resolve_effective_form_field_names` machinery instead). The
  serializer's only genuinely-new validation is `serializer_class`
  is-a-`ModelSerializer` (+ resolvable `Meta.model`) and `Meta.optional_fields`
  normalization. ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven) / Slice 2.)
- **P2.6 — share the override-detection helper.** The `get_serializer_kwargs` default
  body and the override-detection that waives the create-required guard parallel
  `forms/sets.py::_default_get_form_kwargs` + the existing `_form_kwargs_overridden`. The
  serializer flavor ships **only** the finer `get_serializer_kwargs` hook — it has **no**
  coarse `get_serializer` constructor hook (unlike the form flavor's `get_form`): its
  H3 invariants (`partial` and the authorized-actor `context["request"]`) are
  framework-owned in `_merged_serializer_kwargs` and cannot be entrusted to a
  consumer-overridable constructor (a `get_serializer()` override could subvert them),
  so the default body sets **neither** `partial` **nor** `context`
  (spec-039 Medium-7 — the dead-hook removal). The **override-detection** is generic:
  **generalize the existing `_form_kwargs_overridden` into a shared
  `_hook_overridden(cls, base, name)`** identity check the serializer's
  `get_serializer_kwargs` waiver reuses rather than re-deriving `cls.<name> is
  base.<name>`. ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) guard-waiver / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload).)
- **P2.7 — promote the `Meta` typo-guard, do not add a third normalize wrapper.** Every
  `_validate_meta` computes `unknown = sorted(declared - _ALLOWED_<FLAVOR>_META_KEYS)` and
  raises (`mutations/sets.py::_ALLOWED_MUTATION_META_KEYS`, and both form bases). Promote
  `reject_unknown_meta_keys(name, meta, allowed)` to [`mutations/sets.py`][mutations-sets],
  called by every `_validate_meta` with its own frozenset (the serializer's
  `_ALLOWED_SERIALIZER_META_KEYS` **adds** `serializer_class` / `optional_fields`, **drops**
  `model` / `input_class` / `partial_input_class`). And the serializer calls
  `utils/inputs.py::normalize_field_name_sequence(..., flavor="SerializerMutation")`
  **directly** (the required keyword-only `flavor` arg exists for exactly this) rather than
  add a third thin re-binding wrapper alongside `mutations/sets.py::_normalize_field_sequence`
  and `forms/inputs.py::normalize_form_field_sequence`. ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven) / Slice 2; companion to P2.5.)

### Small reuses to pin; deliberately not applicable (P3)

Pin as named import obligations (Slice DoD lines): `utils/inputs.py::graphql_camel_name`
(the `categoryId` alias naming — do not hand-roll camel-casing);
`utils/inputs.py::normalize_field_name_sequence(flavor="SerializerMutation")`;
`utils/permissions.py::request_from_info(family_label="SerializerMutation")`;
`utils/relations.py::{relation_kind, is_forward_many_to_many, is_many_side_relation_kind}`
(for the **backing** model-relation read the converter does via `source`, not re-derived
from DRF's `many` / `source` flags); the
`utils/querysets.py::{model_for, initial_queryset, apply_type_visibility_sync,
apply_type_visibility_async, visibility_scoped_related_queryset, reject_async_in_sync_context}`
locate + relation-visibility + async-guard substrate (a re-spell here is a data-leak risk,
not just a DRY nit); and the read-side
[`types/converters.py`][types-converters]`::{convert_scalar, scalar_for_field, convert_choices_to_enum}`
keyed on the backing `models.Field` via `source` (Decision 7).

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
- **`utils/strings.py`** (`snake_case` / `pascal_case`) — the GraphQL↔Django input-name
  boundary is `graphql_camel_name`; `snake_case` is an optimizer-walk helper, not a
  serializer-input reuse (do not conflate it with `graphql_camel_name`).

### Import manifest — the DRY contract per `rest_framework/` module

The DoD-checkable summary. Each module's allowed imports; anything outside this list that
duplicates a listed symbol's logic is a finding:

| `rest_framework/` module | Imports (do **not** re-implement) |
| --- | --- |
| [`serializer_converter.py`][rf-converter] | the shared dispatch skeleton (**P1.4**), the unified conversion / field-spec dataclass (**P2.1**), `utils/inputs.py::graphql_camel_name`, `utils/relations.py::{relation_kind, is_forward_many_to_many, is_many_side_relation_kind}`, the [`Upload`][glossary-upload-scalar] scalar, the read-side `types/converters.py::{convert_scalar, scalar_for_field, convert_choices_to_enum}`, `exceptions.ConfigurationError` |
| [`inputs.py`][rf-inputs] | `utils/inputs.py::{build_strawberry_input_class, materialize_generated_input_class, normalize_field_name_sequence, graphql_camel_name}`, the shared input-namespace trio (**P2.2**), the shared shape-build cache (**P1.3**), the shared build/stash core (**P1.7**), `mutations/inputs.py::{_pascalize_token, build_payload_type, payload_object_slot, relation_input_annotation}` |
| [`sets.py`][rf-sets] | `mutations/sets.py::{DjangoMutation, _validate_permission_classes, _normalize_field_sequence, _ValidatedMutationMeta, register_mutation}`, the shared non-delete ops constant (**P1.2**), `reject_unknown_meta_keys` (**P2.7**), `mutations/inputs.py::{CREATE, PARTIAL}`, the `_hook_overridden` helper (**P2.6**) |
| [`resolvers.py`][rf-resolvers] | `mutations/resolvers.py::{locate_instance, coerce_lookup_id, authorize_or_raise, refetch_optimized, build_payload, not_found_error, save_or_field_errors, payload_cls_for, run_pipeline_async, _coerce_relation_pk_or_none, raw_choice_value}`, the promoted `_visible_related_object` (**P1.1**), the promoted sync-pipeline skeleton (**P1.5**), `utils/querysets.py::{visibility_scoped_related_queryset, apply_type_visibility_async}`, `utils/permissions.py::request_from_info`, the shared leaf-error sentinel / ctor (**P2.4**) |
| [`__init__.py`][rf-init] | `require_drf()` guard only (Decision 12) |

**Cross-module (not `rest_framework/`):** **P1.6** touches [`types/finalizer.py`][types-finalizer]
(the pre-bind reset block) and [`registry.py`][registry] (the `TypeRegistry.clear()`
co-clear block) — `clear_serializer_input_namespace` **must** register through the
**mandatory** `register_subsystem_clear` seam (**M4**) rather than be hand-added to both
lists.

## Implementation plan

A **pre-Slice-1 dependency gate** plus four slices. Slices 1–2 are package-internal and
staged; **Slice 3 lands the resolver pipeline AND the products live serializer surface in
one commit** (so reachable resolver lines are earned live, not by package tests — the
[`test_query/README.md`][test-query-readme] #"Coverage rule."); Slice 4 is doc +
card-wrap only — **the DRF dev-dependency wiring moves to the gate, not Slice 4** (**F11**:
Slices 1–3 tests import DRF, so the dev-dep + verified floor must exist *before* Slice 1
code lands). Line deltas are planning estimates.

| Slice | Files touched | New / changed tests | Approx. delta |
| --- | --- | --- | --- |
| **0 — pre-Slice-1 dependency gate** (**F11**) | [`pyproject.toml`][pyproject] (`djangorestframework` → `[dependency-groups].dev`, NOT `[project].dependencies`) + `uv.lock` (`uv lock`), [`pytest.ini`][pytest-ini] (a **targeted DRF-origin `ignore::` line** only if the verified floor still emits a deprecation under the CI matrix). **No package-version edit** (stays `0.0.12`, [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)) | the gate is a **precondition**, not a test deliverable: confirm a DRF release imports + runs warning-free across the [`django.yml`][django-workflow] matrix (Python 3.10→3.14 × Django 5.2→6.0/`latest`) under `-W error`, and record the exact pinned floor before converter code | `+5 / 0` (manifest + lock) |
| 1 — serializer-field converter + reverse map + the two serializer-derived inputs | [`rest_framework/serializer_converter.py`][rf-converter] (new; `convert_serializer_field` fail-loud MRO dispatch + the `input_attr → (serializer_field_name, source, kind)` reverse map, renamed-field `source` resolution + id-like-suffix rule), [`rest_framework/inputs.py`][rf-inputs] (new; `<Serializer>Input` + `<Serializer>PartialInput` from the `get_serializer_for_schema()` field set, `SerializerInputShape` descriptor identity, `guard_create_required_serializer_fields`, `read_only` / `optional_fields` handling, narrowing fail-loud), [`rest_framework/__init__.py`][rf-init] (new; DRF soft-import guard), **+ the DRY promotions** ([DRY obligations](#cross-flavor-reuse-and-dry-obligations)): `utils/converters.py` (new; shared dispatch skeleton, **P1.4**) + [`utils/inputs.py`][utils-inputs] (`InputFieldSpec` / `make_input_namespace` / `make_shape_build_cache`, **P2.1** / **P2.2** / **P1.3**) with [`forms/converter.py`][forms-converter] + [`forms/inputs.py`][forms-inputs] re-pointed | [`tests/rest_framework/test_converter.py`][test-rest-framework] + [`tests/rest_framework/test_inputs.py`][test-rest-framework] (~40 — every serializer-field class, id mapping, `Upload`, the reverse-map + `kind` flag, renamed-`source` + id-like-suffix + dotted-`source` raise, custom-field raise, schema-hook (kwargs-serializer reject + override), `read_only` dropped, `optional_fields` (+ `"__all__"` reject), descriptor identity (optional_fields / hook-vary → distinct names), create-required-guard (+ waiver, per-declaration), collision/dedupe, `Meta.fields`/`exclude` fail-loud + empty-set) | `+500 / 0` |
| 2 — the base class + `Meta` validation + the bind + the export guard | [`rest_framework/sets.py`][rf-sets] (new; `SerializerMutation` subclassing `DjangoMutation`, the `_validate_meta` / `_resolve_model` / `build_input` / `input_type_name` / `input_module_path` / `resolve_*` overrides), [`rest_framework/inputs.py`][rf-inputs] (`clear_serializer_input_namespace()`), the serializer input ledger is cleared from **both** the [`types/finalizer.py`][types-finalizer] pre-bind reset block (retry-idempotence — no new bind, rides `bind_mutations()`) and [`registry.py`][registry]'s `TypeRegistry.clear()`, but **via the mandatory `register_subsystem_clear` seam (P1.6, M4), not two hand-edits** — one canonical list of static `(module_path, attr)` string rows that both sites iterate through `_clear_if_importable` (so DRF is never imported while absent, and the soft-dep asymmetry / import-timing edge both vanish, **F10**); [`__init__.py`][init] (guarded `SerializerMutation` export via root `__getattr__`), **+ the DRY promotions** ([DRY obligations](#cross-flavor-reuse-and-dry-obligations)): [`mutations/sets.py`][mutations-sets] (`NON_DELETE_WRITE_OPERATIONS` / `reject_unknown_meta_keys` / `cached_build_input` + `build_and_stash_input` / generalized `_hook_overridden` — **P1.2** / **P2.7** / **P1.7** / **P2.6**) with [`forms/sets.py`][forms-sets] re-pointed | [`tests/rest_framework/test_sets.py`][test-rest-framework] (~18 — `Meta` matrix incl. `delete`-rejected + plain-`Serializer`-rejected + no-model + `permission_classes` kept, both bind, retry-idempotence, no-primary error, model-flavor seam defaults unchanged) | `+340 / -10` |
| 3 — resolver pipeline **+ products live surface (one commit)** | [`rest_framework/resolvers.py`][rf-resolvers] (new; visibility-on-every-branch relation decoder + `partial=True` update + value-preserving save + sync/async pipeline reusing the `036`/`038` promoted helpers), [`examples/fakeshop/apps/products/serializers.py`][products-serializers] (new; `ItemSerializer` + the `Upload`/`Item.attachment` + request-context branches), [`products/schema.py`][products-schema] (serializer mutations), `config/settings.py` (`rest_framework` in `INSTALLED_APPS` if needed), [`mutations/resolvers.py`][mutations-resolvers] + [`utils/querysets.py`][utils-querysets] + [`forms/resolvers.py`][forms-resolvers] (the **P1.1** / **P1.5** promotions — `run_write_pipeline_sync` skeleton + `_visible_related_object` promoted, `forms/` re-pointed; [DRY obligations](#cross-flavor-reuse-and-dry-obligations)) | **Primary: [`test_products_api.py`][test-products-api]** (~16 live `/graphql/` — create/update, field + `"__all__"` envelopes, `categoryId` reverse-map write, partial-update + unique-together, hidden update row, write-auth, hidden-relation `FieldError`, authorize-before-decode, multipart `Upload`, request-context, G2 query shape). **Internals-only: [`tests/rest_framework/test_resolvers.py`][test-rest-framework]** (~13 — recursive-flattener shapes, raw-pk/non-Relay + many-relation decode, call-once save, write-time `IntegrityError` + save-time `ValidationError`, sync/async + `SyncMisuseError`, hermetic kwargs seams) + [`tests/mutations/test_fields.py`][test-mutations] factory-generalization verification | `+560 / 0` |
| 4 — docs + card wrap (no version bump; dep wiring already done in the gate) | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`README.md`][readme], [`GOAL.md`][goal], [`TODAY.md`][today], [`docs/TREE.md`][tree], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban] — **implemented-on-main docs land now; the public "shipped (0.0.13)" / "Shipped today" / release-changelog wording defers to the joint cut** (**F8**) | 0 (doc only) | `+110 / -40` |

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
- **Serializer-only RELATION fields (F4).** A write-only `PrimaryKeyRelatedField` (or
  `many=True`) whose `queryset` is **not** a model column — consumed by a custom
  `create()` / `update()` — is both serializer-only and a relation. Its relation **target
  comes from `field.queryset.model`** (driving the id annotation and the decode-time
  visibility check), and the declared serializer field name is preserved in
  `provided_data`. A relation field with **neither** a resolvable backing column **nor** a
  concrete `queryset.model` is a class-creation
  [`ConfigurationError`][glossary-configurationerror]
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- **Relation target with no registered primary `DjangoType` (M3).** A serializer relation
  field whose target model (from the backing FK or `field.queryset.model`) has **no
  registered primary [`DjangoType`][glossary-djangotype]** is a **class-creation**
  [`ConfigurationError`][glossary-configurationerror] naming the serializer field and the
  target model — **not** a silent runtime fallback to the model's default manager (which
  would write a hidden / unseeable row, breaking the visibility-scoped decode promise). This
  is stricter than the promoted `_visible_related_object` helper's form fallback (which stays
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
- **`get_serializer_kwargs` cannot swap the request actor (H3).** A
  `get_serializer_kwargs(...)` override may add or replace constructor kwargs and merge its
  own `context` keys, but it **cannot change the request actor**: the framework sets
  `context["request"] = request_from_info(info, …)` after merging — the **same** object the
  inherited write-auth seam already authorized — so the serializer's request-aware
  validators see the same user / tenant the permission check saw. An override that supplies a
  **different** `context["request"]` is a [`ConfigurationError`][glossary-configurationerror]
  (it would let permission and validation disagree about the actor); the same object is
  tolerated. Consumer context belongs under other keys
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)
  step 4).
- **`read_only` / `HiddenField` fields.** Dropped from the input (graphene's
  `fields_for_serializer` `is_input` rule); a `HiddenField(default=CurrentUserDefault())`
  resolves at runtime from the injected `context={"request": …}`, never as client
  input. **`HiddenField` defaults are subtle under `partial=True`** (a hidden default may
  not fire on a partial update the way it does on create), so the **live request-context
  proof is an explicit `validate()` branch, not a `HiddenField`** ([Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation), F9);
  `HiddenField` is exercised only for the input-drop rule (and optionally a create-only
  behavior).
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
- **A nested writable serializer field NOT opted in.** A `ModelSerializer` field that is
  itself a serializer (`ListSerializer` / nested `ModelSerializer`) fails loud by default —
  the converter raises [`ConfigurationError`][glossary-configurationerror] naming the field
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth))
  — UNLESS it is EXPLICITLY opted in via `Meta.nested_fields` (rev6 #17), which builds the
  nested input recursively (the serializer owning the nested write via `create()` / `update()`).
- **Write-time `IntegrityError`.** A valid `serializer.save()` that loses a
  concurrent-uniqueness race returns the null-object + `FieldError` envelope via the
  reused `036` `save_or_field_errors` mapper — never a top-level `GraphQLError`.
- **Write-time `ValidationError` — DRF and Django shapes take DIFFERENT paths (F2/H2).** A
  `serializer.save()` whose custom `create()` / `update()` raises a validation error returns
  the null-object + `FieldError` envelope, **not** a top-level `GraphQLError` — but the two
  `ValidationError` classes are **routed by exception class**, exactly the split
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)
  step 6 pins, **never one branch**: a **DRF**
  `rest_framework.exceptions.ValidationError` (== `serializers.ValidationError`) routes its
  `.detail` (the same nested shape as `serializer.errors`) through the **recursive**
  `serializer_errors_to_field_errors` flattener; a **Django**
  `django.core.exceptions.ValidationError` (from a model `full_clean()` inside `save()`)
  has **no `.detail`** and routes through the flat `036`
  [`mutations/resolvers.py`][mutations-resolvers]`::validation_error_to_field_errors`, which
  reads Django's `error_dict` / `messages` shape (verified — it does **not** read `.detail`;
  pushing a Django error down the `.detail` path would `AttributeError` or lose structure).
  Both terminate in the same envelope, the non-field bucket mapping to `"__all__"` either
  way; an `IntegrityError` stays the `036` `save_or_field_errors` branch.
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
- **Two serializer fields sharing one writable `source` (M-edge).** Two distinct declared
  field names with the **same** one-segment `source` both write the same model attribute. If
  **both are input (writable) fields**, the package rejects it at class creation with a
  [`ConfigurationError`][glossary-configurationerror] naming the two fields and the shared
  `source` — two writable inputs feeding one model attr is a double-write hazard, and the
  package will not silently pick a winner. A `read_only` field sharing a `source` with a
  writable one is **fine** (read-only fields are dropped from the input, Decision 7), so the
  common DRF read/write-split pattern is unaffected.
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
  the `serializer.errors` envelope — a `validate_<field>` error is keyed to the **GraphQL
  input name** (not the serializer field name), the `UniqueTogetherValidator` /
  `validate()` error keyed to `"__all__"`; **a renamed-field error path (F5)** — a
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
    field raises; a **serializer-only relation** resolves its target from
    `field.queryset.model`, while a relation with no backing column **and** no concrete
    `queryset.model` raises [`ConfigurationError`][glossary-configurationerror] (F4); a
    relation whose **target model has no registered primary `DjangoType`** raises a
    class-creation [`ConfigurationError`][glossary-configurationerror] naming the field and
    target model (M3) rather than falling back to the default manager.
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
    `ConfigurationError`; **nullability and defaults (M2)** — `allow_null=True` yields a
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
    **save-time validation — DRF and Django are SEPARATE branches (F2):** a serializer
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
    `serializer.instance`); **`get_serializer_kwargs` precedence (F7/H3)** — an override that
    **adds a kwarg while preserving the request context** constructs correctly; an override
    that returns `partial=False` (or `partial=True` on create) raises
    [`ConfigurationError`][glossary-configurationerror]; an override `context` dict is
    **merged** (its non-`request` keys win, the framework-owned `request` is always set from
    `request_from_info(...)`); an override supplying a **different** `context["request"]`
    object raises [`ConfigurationError`][glossary-configurationerror] (the actor cannot drift
    from the permission seam, H3) while the **same** object is tolerated; plus the
    bare-`HttpRequest` `info.context` fallback of `request_from_info`; **the recorded
    GlobalID strategy is consumed, not the live setting (config assessment)** — monkeypatch
    `types/relay.py::_resolve_globalid_strategy` to fail **after** finalization and assert a
    serializer relation mutation still resolves through the recorded
    `effective_globalid_strategy` (only if new serializer code touches GlobalID decode
    directly); **sync + async** (one `sync_to_async(thread_sensitive=True)`) and the
    [`SyncMisuseError`][glossary-syncmisuseerror] async-`get_queryset`-from-sync path.
  - **The DRF-absent import guard** ([`tests/rest_framework/test_soft_dependency.py`][test-rest-framework]
    or in `test_sets.py`): with DRF's import simulated-absent (monkeypatched
    `builtins.__import__`, **module caches for both `rest_framework*` and
    `django_strawberry_framework.rest_framework*` evicted first, and the root
    `django_strawberry_framework.SerializerMutation` attribute deleted**, so neither a
    stale submodule import nor a bound root symbol can mask the path), all three raising
    entry points — the root `__getattr__("SerializerMutation")`, an `…rest_framework`
    import, and an `…rest_framework.sets` import — raise `ImportError` with the install
    hint, while `import django_strawberry_framework` still succeeds. **Star-import stays
    DRF-free (F1):** `from django_strawberry_framework import *` under simulated DRF-absence
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

Each slice owns its doc edits. [`AGENTS.md`][agents] #"Do not update CHANGELOG.md
unless explicitly instructed" requires `CHANGELOG.md` edits to be explicitly
instructed — and a standing design doc cannot itself grant that permission. This spec
only *describes* the release-note work; the **Slice 4 maintainer prompt must explicitly
include the `CHANGELOG.md` edit** for it to be authorized.

- **Pre-Slice-1 gate (Slice 0) — soft-dep wiring** ([`pyproject.toml`][pyproject] +
  `uv.lock` + [`pytest.ini`][pytest-ini], **F11**): add `djangorestframework` to
  `[dependency-groups].dev` (NOT `[project].dependencies`), pinning the **verified** floor
  matching the guard's install hint, regenerate `uv.lock` so the lockfile matches, and add
  any targeted DRF-origin `ignore::` line — **before Slice 1 imports DRF in tests** (not
  Slice 4). **No package-version edits** (the `[project].version` / `__version__` /
  `test_version` and the `uv.lock` package-version entry stay `0.0.12`; only the DRF
  dependency entries change)
  ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
- **Release vs implementation docs are split (F8).** Because this card does **not** bump
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
  **this is a pre-Slice-1 dependency gate (Slice 0), not a Slice 4 surprise (F11)** —
  because Slice 1–3 tests import DRF, the dev-dep add + `uv.lock` regen + any `ignore::`
  line and the verified floor must all land in the gate *before* converter code. In that
  gate, verify a `djangorestframework` release exists that imports and runs **warning-free
  on (Python 3.14, Django 6.0 / `latest`)** as well as the floor (`Python>=3.10`,
  `Django>=5.2`); record the **exact** floor pinned in the dev group (and matched in the
  guard's install hint), plus **any DRF-origin `ignore::` line** that release still needs —
  [`pytest.ini`][pytest-ini]'s own comment already sanctions a targeted `ignore::` for
  "warnings originating in third-party packages we cannot fix" (never a blanket ignore).
  Secondary (API-availability) constraint: bump the floor if a needed serializer API (e.g.
  `api_settings.NON_FIELD_ERRORS_KEY`) is only present in a later release. The probe runs
  against the actually-installed DRF in the gate; the matrix-warning check is the one that
  gates the floor, and if no compatible release exists the card blocks at the gate rather
  than mid-Slice-1.
  **Recorded floor (Slice 0, verified): `djangorestframework>=3.17.0`** — the first release
  adding Django 6.0 + Python 3.14 support (released 2026-03-18; resolves to 3.17.1), proven to
  import warning-free under `-W error` across all 9 [`django.yml`][django-workflow] matrix
  cells (Python 3.10→3.14 × Django 5.2→6.0 / `latest`) with **no** `ignore::` line needed.
  This is place 3 of the three-places-that-must-agree; the `[dependency-groups].dev` pin in
  [`pyproject.toml`][pyproject] is place 1 (landed) and the `require_drf()` install hint
  (Slice 2) is place 2 and must name this same floor.
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
- **Serializer-derived output types** — the frozen `node` / `result` slot supersedes a
  serializer output
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
  (Nested writable serializers were originally a non-goal; they now ship as the EXPLICIT
  opt-in `Meta.nested_fields` — rev6 #17.)
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
   `clear_serializer_input_namespace()` cleared from **both** the
   [`finalize_django_types`][glossary-finalize_django_types] pre-bind reset block (the
   retry-idempotence fix) **and** `TypeRegistry.clear()`, **wired through the mandatory
   `register_subsystem_clear` seam (M4)**: one canonical list of static `(module_path,
   attr)` string rows both sites iterate via `_clear_if_importable`, so DRF is never
   imported while absent (a skipped clear on a DRF-absent build is a correct no-op) and
   the serializer is **not** a third hand-maintained clear list (**F10/P1.6**);
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
   scalar; the shared decoder helper accepts both only for reused / package-only branches,
   M1), each id type-checked against the target model (resolved from the backing FK via the
   serializer field's `source`, **or `field.queryset.model` for a serializer-only
   relation**), resolved to the **visible** object through the related
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
   re-fetch); a **save-time `ValidationError` is routed to the envelope by exception class
   (F2/H2)** — a DRF `serializers.ValidationError`'s `.detail` through the recursive
   `serializer_errors_to_field_errors`, a Django `django.core.exceptions.ValidationError`
   through the flat `036` `validation_error_to_field_errors` (`error_dict` / `messages`, not
   `.detail`), an `IntegrityError` through `save_or_field_errors` — never a top-level
   `GraphQLError`; the payload object is re-fetched through the `036` optimizer path (G2:
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

**Pre-Slice-1 gate (Slice 0) — soft-dep wiring (F11); Slice 4 — docs + card wrap (no version bump)**

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
   release-status wording defers to the joint cut (F8):** the GLOSSARY `shipped (0.0.13)`
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
   [`TODO-ALPHA-040-0.0.13`][kanban] owns the bump). The one net-new public symbol
   (`SerializerMutation`) is a **named lazy export** resolved via the root `__getattr__`
   under the DRF soft-import guard, and is **NOT in `__all__`** while DRF is soft (so
   `from … import *` stays DRF-free, F1).

## Round-6 improvements (better-than-graphene-django)

A review pass (`docs/feedback.md`, rev6) proposed 16 improvements that make the serializer
lane stricter, safer, and more diagnosable than graphene-django's DRF integration, plus one
follow-on (#17 — opt-in nested serializer inputs). They are all in-scope for `0.0.13` (not
backlog). Each keeps the existing wins (fail-loud unmapped fields, visibility-checked
relations, authorize-before-decode, framework-owned `context["request"]` / `partial`, recursive
error flattening, transaction boundary, descriptor-based input identity, DRF-soft-dep root).
This section records the design of each.

### rev6 #11 — Public serializer-field converter registry

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

### rev6 #7 — Expanded DRF scalar capability matrix (no catch-all)

Each mapping is an EXPLICIT registry entry, never a base-`Field` catch-all: `DictField` /
`HStoreField` → `strawberry.scalars.JSON` (`HStoreField` via the MRO walk under `DictField`);
`IPAddressField` / `FilePathField` → `str`; `DurationField` → `str` (a DELIBERATE scalar —
DRF renders a duration as an ISO-8601-ish string on the wire and parses it back at
validation, not an accidental fallthrough); `ModelField` routes through its wrapped
`model_field` via the read-side `scalar_for_field` (a `ModelField` over an unsupported column,
or with no wrapped field, fails loud). Each has a package converter test; the live matrix is
earned by `createShelfViaMetadataSerializer` (`DictField` → `JSON`).

### rev6 #6 — Generated enums for serializer-only `ChoiceField`

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

**Declared choices survive on a model-backed scalar too (rev2 P2).** A CONSUMER-DECLARED
`ChoiceField` / `MultipleChoiceField` — even one `source`-mapped to a plain (non-choice) model
column — emits the SAME generated serializer-only enum (via the shared `_serializer_choice_annotation`),
rather than collapsing back to the column's `String` scalar. The declared choices are part of the
public mutation contract, so they are never silently lost. Package-regression-tested with
`ChoiceField(source="name", choices=...)` over a non-choice column.

### rev6 #8 — Model-backed serializer type-override conflict policy

An AUTO-generated `ModelSerializer` field routes through the read-side `convert_scalar`
(enum/read-write symmetry). A CONSUMER-DECLARED serializer field (in the serializer's
`_declared_fields`) is an explicit contract: if its base GraphQL scalar DISAGREES with the
backing model column's scalar (e.g. `count = IntegerField(source="a_char_col")` — int vs str)
the framework FAILS LOUD naming the field, its `source`, and both scalars, rather than
silently picking the model column (the graphene-django trap). A benign rename
(`display_name = CharField(source="name")` — str vs str) agrees and resolves to the model
scalar; a `choices` column keeps the enum symmetry (the check is skipped there); a
consumer-declared `ChoiceField` is handled by rev2 P2 (it emits the serializer-only enum,
above) BEFORE this scalar-disagreement check. This is a class-creation / bind-time raise (an
invalid configuration), so it is package-tested, not live.

### rev6 #9 — Thread DRF field metadata into the SDL

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

### rev6 #5 — Aggregate schema-time diagnostics

`_walk_serializer_fields` now COLLECTS every per-field conversion error (unsupported field,
non-PK relation, missing relation-primary, dotted / `source="*"`, the rev6 #8 type-override
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

### rev6 #1 — Runtime schema/runtime serializer agreement guard

`rest_framework/resolvers.py::_assert_schema_runtime_agreement(mutation_cls, serializer)` runs
in `_serializer_write_step` AFTER the runtime serializer is constructed and BEFORE
`is_valid()`. It proves the schema-time field map (which drove the generated GraphQL input +
the bind-stashed `_input_field_specs`) still agrees with the runtime `serializer.fields`: for
every schema-time spec the runtime serializer must contain `spec.target_name`, have it WRITABLE
(not `read_only`), bind the same `source`, keep a relation as `PrimaryKeyRelatedField` /
`ManyRelatedField(PrimaryKeyRelatedField)` over the same `related_model`, and keep a file /
scalar kind compatible (a scalar that became a relation or file, or vice versa, is a mismatch).
Any divergence is a framework `ConfigurationError` at the boundary, NOT a silent
DRF-ignores-the-unknown-key ambiguity — the schema hook becomes a VERIFIED contract rather than
a trust point. A runtime serializer with EXTRA fields the schema omits is fine (never provided).

Consequence: a schema-only field the runtime serializer does not declare (the old
decode-then-drop pattern) is now forbidden, so the fakeshop nullability fixtures were
redesigned — `NoteShelfSerializer(note_allow_null=...)` declares `note` as a REAL write-only
runtime field (popped in `create()`), and each mutation's `get_serializer_kwargs` constructs it
with the same `note_allow_null` its schema hook used, so schema and runtime agree while the two
still differ only in `note`'s emitted nullability. Happy path is live-covered (every serializer
mutation now passes the guard); the raise cases are package-tested.

### rev6 #16 — Golden SDL coverage for representative serializer inputs

A narrow golden-SDL snapshot (NOT a whole-schema dump) pins the serializer input lane against
cross-field drift: one library schema-hook mutation (`ShelfMetadataSerializerInput` +
`CreateShelfViaMetadataSerializerPayload` + the shared `FieldError`) and one products serializer
mutation (`ItemSerializerInput` + `CreateItemViaSerializerPayload`). Introspecting the ONE
aggregate `/graphql/` schema, the tests assert generated input names, field names, nullability,
descriptions (rev6 #9), the serializer-only enum (#6), the JSON / registry-mapped scalars
(#7 / #11), the file (`Upload`) + Relay-`GlobalID` (`ID!`) / raw-pk relation id scalars, the
payload object slot (`node` for Relay `Item`, `result` for non-Relay `Shelf`), and the additive
`codes` / `path` on `FieldError` (#4 / #13). Especially valuable now that enums, descriptions,
error metadata, and custom converters are in play.

### rev6 #15 — Schema-shape debug/introspection registry

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

### rev6 #14 — Optional row locking for update mutations (`Meta.select_for_update`)

A new serializer `Meta.select_for_update = True` (validated as a bool, stored on the snapshot's
`select_for_update` slot) opts the UPDATE locate into a `SELECT ... FOR UPDATE` row lock. The
shared `locate_instance(target_type, node_id, info, *, select_for_update=False)` wraps the
visible queryset in `.select_for_update()` when asked — so the lock is acquired AFTER visibility
filtering and INSIDE the pipeline's existing `transaction.atomic()` boundary;
`run_write_pipeline_sync` passes `meta.select_for_update` (default `False` for the model / form
flavors). On a backend without `FOR UPDATE` support (e.g. sqlite) Django silently skips the
clause, so it is safe to declare regardless of backend (no framework-side backend check needed).
Live-tested (`updateBookViaSerializerWithLock` updates a Relay-Node `Book` cleanly with the lock
enabled); package-tested (Meta validation; `locate_instance` applies `.select_for_update()` only
when asked).

### rev6 #12 — `get_serializer_save_kwargs` (a save-time hook, separate from constructor kwargs)

`SerializerMutation.get_serializer_save_kwargs(info, data, instance=None) -> dict` is the
DRF-native customization point for request-derived data DRF expects at `serializer.save(**kwargs)`
(`owner=request.user`), distinct from `get_serializer_kwargs` (construction / context). The
resolver calls it INSIDE the value-preserving `save()` closure - `saved =
serializer.save(**save_kwargs)` - so the transaction boundary, `ValidationError` /
`IntegrityError` mapping, and optimizer re-fetch are all preserved (unlike graphene-django's
`perform_mutate`, which bypasses framework-owned behavior). `_assert_save_kwargs_no_shadow`
rejects a save kwarg whose name matches a serializer INPUT field (it would silently override the
client's value; save kwargs are for server-side data not in the input). Default `{}`. Live-tested
(`createShelfWithSaveKwargs` stamps a server-side `topic` at save); package-tested (shadow raises,
non-shadow allowed).

### rev6 #3 — Visibility-scoped + query-efficient relation validation

Two moves keep the security win (authorize-before-decode + visibility-checked ids) while cutting
the query cost. (a) A batched `utils/querysets.py::visible_related_objects(related_model, pks,
info)` confirms a MULTI relation's whole set in ONE visibility-scoped `pk__in` query instead of
one per id: the serializer multi decoder now type-checks + coerces every id first (the extracted
`_type_check_relation_id`, no DB), then batch-confirms visibility, preserving the uniform
no-existence-leak relation error (a hidden / missing member is the same field-keyed error). (b)
`_scope_relation_querysets_to_visibility` COMPOSES each runtime relation field's `queryset`
(`PrimaryKeyRelatedField`) / `child_relation.queryset` (`ManyRelatedField`) WITH the
visibility-scoped queryset before `is_valid()` — `original.filter(pk__in=<visibility queryset>)`,
an ADDITIONAL constraint (a `pk__in` subquery, still one lookup), never a REPLACEMENT (**rev2
P1**: the earlier reassignment erased a serializer author's own
`PrimaryKeyRelatedField(queryset=...)` restriction and could admit a visible-but-disallowed row).
So DRF's own re-validation honors BOTH the author's queryset AND visibility, and can never
re-fetch a row the decode hid. Package-tested with `assertNumQueries`-style
`CaptureQueriesContext` (the batched multi decode is exactly ONE query), a hidden-member
rejection, and a visible-but-author-disallowed single + many relation (the compose preserves the
author's filter); live-tested by `createShelfViaAltBranchesSerializer` (a raw-pk M2M writes
visible branches, a hidden branch is a `altBranches` relation error over `/graphql/`).

### rev6 #2 — Explicit injection contract (`Meta.injected_fields`)

The old rule "overriding `get_serializer_kwargs` waives the create-required guard entirely" was
too broad — it waived required-field coverage even when the override did not supply the dropped
fields. `Meta.injected_fields = (...)` is the auditable, per-field replacement (a new serializer
`Meta` key, normalized like `optional_fields`, stored on the snapshot): the create-required
guard SUBTRACTS only the declared injected fields (a dropped required field NOT declared injected
STILL raises). Each injected name is validated at CLASS creation against the schema-time field
map (a typo fails loud), and its schema-time spec is stashed (`_injected_field_specs`). At
runtime `_assert_injected_fields_supplied` proves RUNTIME ACCEPTANCE, not mere presence (**rev2
P1**): each injected field must pass the SAME present / writable / source / kind / relation-model
agreement check an input field gets (so the runtime serializer cannot silently drop or ignore it)
AND have reached the serializer's `initial_data` — either failure is a clear `ConfigurationError`.
The old blanket waiver survives ONLY as an explicitly-named unsafe legacy escape hatch
(`legacy_waiver` in `build_input`): it fully skips the guard, but ONLY when `injected_fields` is
NOT declared — declaring `injected_fields` opts into the precise mechanism. Live-tested
(`createShelfWithInjectedTopic` narrows away a required `topic` and injects it); package-tested
(subtract / still-raise / class-validation / runtime agreement + presence).

### rev6 #10 — Fingerprint `get_serializer_for_schema()` for determinism

The spec requires the schema hook to return a STABLE, request-independent field shape, but the
hook runs at class validation AND again at the phase-2.5 bind — a nondeterministic hook could
validate one shape and bind another. `inputs.py::serializer_schema_fingerprint(field_map)`
computes a digest of EVERY SDL-affecting axis (**rev2 P2**): ordered field names, classes,
sources, read/write flags, `required`, `allow_null`, relation target models, PLUS the description
inputs (`help_text` + the constraint summary), the enumerable choice MEMBERS, and the converter
discriminants (`ModelField` wrapped field / `ListField` child) — so a hook that changes a
description, enum members, or converter behavior without changing the coarse identity still trips
the guard. `_validate_meta` captures it on `_ValidatedMutationMeta.schema_fingerprint` at class
validation; both `build_input` AND `input_type_name` read the hook through the ONE guarded path
`_checked_schema_field_map` (**rev2 P2**: the type-name derivation no longer reads an unguarded
field map behind the fingerprint's back), raising `ConfigurationError` on drift. This turns the
spec's stable-shape promise into an enforced contract (graphene-django has no equivalent — no
schema/runtime hook split). Package-tested (drift raises at bind AND via `input_type_name`; the
fingerprint is sensitive to choices / help_text / converter extras; a stable hook binds cleanly).

### rev6 #4 — Preserve DRF `ErrorDetail.code` in the error envelope

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

### rev6 #13 — Structured error `path` in addition to the dotted `field`

`FieldError` also gains an additive, default-empty `path: [String!]` — the dotted `field`
string split into SEGMENTS, derived inside `field_error` so it cannot drift from `field`.
`items.0.name` → `["items", "0", "name"]`. Documented ROOT rule: a model-wide / non-field
error is `field="__all__"` with an EMPTY `path` (`[]`) — whether it arrives as an empty path
(the Django mapper) or as the bare `"__all__"` sentinel (the DRF flattener's top-level
non-field bucket), so the two flavors agree; a NESTED non-field error keeps the sentinel as
its final segment (`["items", "0", "__all__"]`). Additive (a client selecting only `field` /
`messages` is unaffected); pairs with rev6 #4. Live- and package-tested.

### rev6 #17 — Explicit opt-in nested serializer input support

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
  fields do (review P1), so the runtime schema/runtime agreement guard's source comparison matches
  instead of failing every invocation; a dotted source / `source="*"` fails loud in
  `_resolve_nested_field` (the model-column-path fail-loud source policy).
- **Recursively fingerprinted, scoped to the writable set, gated on the opt-in tree.**
  `serializer_schema_fingerprint` folds an OPTED-IN nested serializer's own field map into the
  determinism fingerprint (bounded by an on-path cycle guard), so a nondeterministic hook that
  changes a nested shape is caught at the phase-2.5 bind. The fingerprint runs over the EFFECTIVE
  (writable + narrowed) field set — the SAME set the input build uses — and drops `read_only` /
  `HiddenField` at every level (review P1), so a read-only or narrowed-away nested serializer (e.g.
  a context-sensitive nested OUTPUT serializer whose `.fields` cannot materialize no-arg) is NEVER
  descended into and cannot break class creation; a residual reachable nested-`.fields` failure is
  wrapped as `ConfigurationError`. The recursion is ALSO gated on the `Meta.nested_fields` opt-in
  tree (review follow-on P2), threaded into the fingerprint at BOTH class validation and bind: an
  UNOPTED nested field records a shallow marker (class name + many-ness) WITHOUT reading its
  `.fields` — nesting is opt-in only, so it produces no nested input and its child shape cannot
  affect the SDL, and the field walk raises the canonical `_reject_nested_serializer` opt-in error.
  Descending into an unopted, context-sensitive nested child would otherwise surface a misleading
  "opted in via Meta.nested_fields..." materialization error at class validation, shadowing the
  canonical opt-in error.
- **Depth / cycle guarded.** Recursion is bounded by the finite, immutable `NestedSerializerConfig`
  tree; a serializer class that reappears on the recursion path is a fail-loud cycle, and a
  path beyond `_NESTED_MAX_DEPTH` is a fail-loud depth cap.
- **The framework NEVER auto-saves the nested relation.** `Meta.nested_fields` REQUIRES the
  serializer to override `create()` (create op) / `update()` (update op) — checked at class
  creation, because DRF's default `ModelSerializer.create/update` `assert`s on writable nested
  data (a raw `AssertionError` that would escape the envelope). The framework decodes + validates
  the nested data (visibility-checking each nested relation, recursively, and scoping the runtime
  nested serializer's relation querysets) and hands it to the serializer's OWN `create()` /
  `update()`, which owns the write, inside the pipeline transaction.
- **Errors route through the structured `path` / `codes` envelope, re-keyed at every depth.** A
  nested DRF validation error flattens through the recursive `serializer_errors_to_field_errors`,
  which now RE-KEYS each path segment to its GraphQL name as it descends (review P2 — not only the
  root), driven by a recursive reverse map built from `InputFieldSpec.nested_specs`: a nested child
  field / alias / relation suffix reports its SDL name (`shelves.0.altBranches`, not
  `shelves.0.alt_branches`), while numeric indexes and the `__all__` non-field sentinel are
  preserved. A nested framework decode error (a hidden relation id) is keyed to the same FULL
  nested path with the `invalid` code and rolls the write back (H6). The runtime schema/runtime
  agreement guard (#1) recurses into the nested serializer too.

The nested input dedupes on its `SerializerInputShape` descriptor (folded into the parent
descriptor identity + the per-shape build cache, so two nested shapes never collide on one name)
and materializes through the same ledger. Earned live by `createBranchWithNestedShelves` (a
`Branch` with a nested `shelves` list carrying a raw-pk `altBranches` M2M) — the happy nested
write, the hidden-nested-relation structured-path error + rollback, and the nested DRF
validation-error flattening; the fail-loud / guard / config-validation / source-axis / recursive
re-keying / opt-in-gated-fingerprint branches are package-tested.

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
[glossary-bigint-scalar]: GLOSSARY.md#bigint-scalar
[glossary-choice-enum-generation]: GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-cross-subsystem-invariants]: GLOSSARY.md#cross-subsystem-invariants
[glossary-definition-order-independence]: GLOSSARY.md#definition-order-independence
[glossary-djangoformmutation]: GLOSSARY.md#djangoformmutation
[glossary-djangomodelformmutation]: GLOSSARY.md#djangomodelformmutation
[glossary-djangomodelpermission]: GLOSSARY.md#djangomodelpermission
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: GLOSSARY.md#djangomutationfield
[glossary-djangonodefield]: GLOSSARY.md#djangonodefield
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
[glossary-metaglobalid_strategy]: GLOSSARY.md#metaglobalid_strategy
[glossary-metamodel]: GLOSSARY.md#metamodel
[glossary-metaprimary]: GLOSSARY.md#metaprimary
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: GLOSSARY.md#per-field-permission-hooks
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-relay_globalid_strategy]: GLOSSARY.md#relay_globalid_strategy
[glossary-scalar-field-conversion]: GLOSSARY.md#scalar-field-conversion
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-specialized-scalar-conversions]: GLOSSARY.md#specialized-scalar-conversions
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
[types-definition]: ../django_strawberry_framework/types/definition.py
[types-relay]: ../django_strawberry_framework/types/relay.py
[types-finalizer]: ../django_strawberry_framework/types/finalizer.py
[utils-inputs]: ../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../django_strawberry_framework/utils/querysets.py

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
