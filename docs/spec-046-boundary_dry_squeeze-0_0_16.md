# Spec: Boundary hardening + system-wide DRY squeeze — enforce the optimizer/core seams inside one distribution, then compress ~1,100–1,300 duplicated lines across four verified axes

Planned for `0.0.16` (card `TODO-ALPHA-046-0.0.16`); **this card is the only
card at `0.0.16` and owns the version bump**
([Decision 11](#decision-11--lone-card-at-0016--slice-5-owns-the-version-cut)).
This card is a **maintainability card**: it ships no new consumer feature
(the one consumer-visible artifact is the packaging-extras advertisement,
[Decision 5](#decision-5--packaging-extras-advertise-the-existing-soft-dependency-seams)).
Its purpose is to make the package materially easier to hold in one head, by
doing two things in sequence:

1. **Boundary hardening ("the not-splitting alternative").** The maintainer
   considered splitting the package (standalone optimizer distribution).
   Investigation rejected the split
   ([Decision 1](#decision-1--no-package-split--the-boundary-becomes-formal-not-physical)):
   the optimizer is bidirectionally fused to the type system, and ecosystem
   precedent (strawberry-django-plus absorbed INTO strawberry-django;
   graphene-django-optimizer stagnant at ~120k downloads/month with no
   maintenance) shows framework-coupled optimizers fail as standalone
   packages. Instead, the architectural instinct is honored **inside one
   distribution**: the optimizer's inward-facing API is promoted to a
   deliberate surface ([Decision 4](#decision-4--promote-the-optimizers-inward-facing-api)),
   the dependency architecture is enforced mechanically by `import-linter`
   contracts in CI ([Decision 3](#decision-3--import-linter-owns-boundary-enforcement)),
   and the existing [soft dependency][glossary-soft-dependency] seams are
   advertised as pip extras.
2. **A system-wide DRY squeeze.** Four parallel audits (the sets family, the
   inputs/converters family, the resolvers family, root+optimizer+utils)
   produced **32 verified consolidation candidates totaling ~1,100–1,300
   source lines**, phased mechanical → structural → contract-level, plus a
   recorded do-not-touch ledger of deliberate duplication so future passes
   do not re-litigate
   ([Decision 8](#decision-8--the-deliberate-duplication-ledger-is-part-of-the-deliverable)).
   The maintainer's standing directive for this card: maximal DRY even at
   small performance cost — and the audits confirmed the whole plan avoids
   the documented hot loops, so the measured cost is expected to be ~zero
   ([Decision 9](#decision-9--phase-sequencing-and-hot-path-exclusions)).

Two deliberate behavior changes ride the squeeze, both maintainer-approved in
advance: the plain-form mutation pipeline gains the transactional
auth-alias isolation every other flavor already has
([Decision 6](#decision-6--close-the-plain-form-alias-guard-gap)), and
`editable_input_fields` inherits the shared field-name normalization
strictness ([Decision 10](#decision-10--editable_input_fields-rides-the-shared-spine-strictness-tightening-accepted)).
Every other consolidation is behavior-preserving by construction, with
test-pinned error strings preserved **byte-identical**
([Decision 7](#decision-7--error-string-byte-preservation-policy)).

Status: **PLANNED — no slice built yet.**
Five slices: Slice 1 (**boundary hardening**: optimizer surface promotion,
`import-linter` contracts wired into CI/pre-commit, packaging extras),
Slice 2 (**mechanical DRY batch** — ~450–550 lines, all
provably-coinciding behavior), Slice 3 (**structural DRY batch** —
~500–600 lines, including the two write-skeleton folds and the filter
dispatch-table unification), Slice 4 (**contract-level DRY** — the
single-window planner unification, the walker dual-contract retirement, the
model relation-decoder re-expression), Slice 5 (**docs fold-in + the
`0.0.16` version cut + card wrap**).

Permission caveat: `AGENTS.md` prohibits `CHANGELOG.md` edits without
explicit permission; this spec's Slice 5 grants that permission for the
`0.0.16` release entry, and no earlier slice touches it.

---

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [`FilterSet`][glossary-filterset], [`OrderSet`][glossary-orderset] — the
  query-side set family whose thin-delegate layer Slice 2 absorbs.
- [`DjangoMutation`][glossary-djangomutation],
  [`DjangoFormMutation`][glossary-djangoformmutation],
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation],
  [`SerializerMutation`][glossary-serializermutation] — the write-side set
  family riding the shared skeleton.
- [`DjangoType`][glossary-djangotype],
  [`finalize_django_types`][glossary-finalize_django_types] — the type
  system whose `DjangoTypeDefinition` is the optimizer's input contract.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension],
  [`OptimizerHint`][glossary-optimizerhint],
  [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning],
  [Plan cache][glossary-plan-cache], [Strictness mode][glossary-strictness-mode],
  [FK-id elision][glossary-fk-id-elision] — the optimizer surfaces the
  boundary work formalizes and the contract-level slice touches.
- [`DjangoConnection`][glossary-djangoconnection] — owner of the connection
  dispatch tails Slice 3 unifies.
- [Soft dependency][glossary-soft-dependency],
  [Hard dependency][glossary-hard-dependency],
  [`require_optional_module`][glossary-require_optional_module] — the
  existing seams the extras advertise.
- [Input type generation][glossary-input-type-generation],
  [Scalar field conversion][glossary-scalar-field-conversion],
  [Choice enum generation][glossary-choice-enum-generation],
  [`filter_input_type`][glossary-filter_input_type],
  [`order_input_type`][glossary-order_input_type],
  [`Upload` scalar][glossary-upload-scalar] — the conversion pipelines the
  inputs axis consolidates around.
- [Per-field permission hooks][glossary-per-field-permission-hooks],
  [`request_from_info`][glossary-request_from_info] — the permission plumbing
  behind the query-side delegate absorption.
- [`FieldError` envelope][glossary-fielderror-envelope] — the error contract
  every resolver consolidation must preserve byte-identically.
- [Multi-database cooperation][glossary-multi-database-cooperation] — the
  alias-guard machinery the plain-form flavor joins.
- [Relation handling][glossary-relation-handling],
  [Relay Node integration][glossary-relay-node-integration],
  [`Ordering`][glossary-ordering] — surfaces cited by individual candidates.
- [`ConfigurationError`][glossary-configurationerror] — the raise type shared
  by the validator/walker helpers being hoisted.
- [Joint version cut][glossary-joint-version-cut],
  [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the
  release and test disciplines Slice 5 and the test plan follow.
- [Cookbook parity][glossary-cookbook-parity] — the constraint that decides
  whether dead query-side delegates may be deleted or must be kept as
  documented surface ([Risks](#risks-and-open-questions)).

## Slice checklist

Each top-level item maps to one commit / PR. **Five slices.** The card is an
XL: four work packages spanning ~30 files, but each candidate is small and
independently verifiable; the weight is breadth, not depth.

- [ ] **Slice 1 — Boundary hardening (WP-A)**
  - [ ] **A0 re-baseline** (before any DRY slice acts): commit `60998b17`
        ("seal get_queryset hook results into framework-owned querysets",
        2026-07-20, +1,677 lines to `utils/querysets.py`) landed AFTER the
        four DRY audits collected their figures. Re-measure the audit totals
        (the ~1,100–1,300 / 32-candidate estimate, the ~47.3k/~19.7k package
        sizes, and Decision 1's ~12k/~25% import-closure figure) against the
        post-`60998b17` tree, and refresh any candidate touching
        `utils/querysets.py` before Slices 2–4 act on it.
  - [ ] **A2 first** (it makes A1's contracts satisfiable): promote the
        optimizer's inward-facing API. `optimizer/__init__.py` re-exports the
        deliberate cross-boundary surface (the `_context` names consumed by
        `types/resolvers.py`; the `extension` symbols consumed by
        `mutations/resolvers.py` and `connection.py`; `plans.resolver_key`
        / `plans.runtime_path_from_info`; the `nested_planner` /
        `selections` symbols `connection.py` consumes; `FieldMeta`;
        `OptimizerHint`) with a docstring naming it the package-internal
        contract. Retarget the three consumer files; no behavior change.
  - [ ] **A1**: add `import-linter` to `[dependency-groups].dev`; configure
        `[tool.importlinter]` contracts (optimizer inward surface; no
        `optimizer._*` imports from outside; soft-dep subpackages are leaves;
        `utils/` independence). Wire into CI and `.pre-commit-config.yaml`.
  - [ ] **A3**: declare `[project.optional-dependencies]` extras — `drf`,
        `channels`, `keyset-encryption`, `debug-toolbar` — mirroring the dev
        group's floors. Runtime guards unchanged. README install section
        updated in the same commit (implemented-contract doc, not a
        release-status doc).
- [ ] **Slice 2 — Mechanical DRY batch (WP-B, ~450–550 lines)**
  - [ ] B1 query-side delegate absorption (`ActiveInputSetMixin` +
        per-family traversal descriptor in `sets_mixins.py`; dead-delegate
        deletion pending the cookbook-parity check in
        [Risks](#risks-and-open-questions)).
  - [ ] B2 write-side sets (`PermissionClassesMixin`, metaclass merge,
        and/or/not flatten).
  - [ ] B3 inputs micro-hoists (`relation_id_scalar`,
        `name_set_input_type_name`, `optional_field_kwargs` fusion).
  - [ ] B4 resolvers micro batch (`coerce_pks`, substituted-row helper,
        `open_write_pipeline`, shared pre_save cross-alias guard, kwargs
        resolver entries).
  - [ ] B5 root/optimizer/types small batch (`strawberry_schema_config`,
        `validate_relay_page_bound`, `keyset_context_for`, `_target_pk_name`
        delegation, keyed `resolve_unvisited_fragment`,
        `_graphql_surface_names`, `_relay_node_gate`, `_validate_set_sidecar`,
        `_attach_generated_resolvers`, relay node-default routing,
        `require_subclass`).
- [ ] **Slice 3 — Structural DRY batch (WP-C, ~500–600 lines)**
  - [ ] C1 `_run_delete` folded onto the write skeleton (`tail_step` seam).
  - [ ] C2 `_run_plain_form_pipeline_sync` folded onto the skeleton —
        **closes the alias-guard gap** ([Decision 6](#decision-6--close-the-plain-form-alias-guard-gap));
        new live-tier coverage for the newly-guarded path.
  - [ ] C3 filter converter/normalizer dispatch table (kills the two-ladder
        drift hazard).
  - [ ] C4 `install_input_namespace()` parked-globals unification.
  - [ ] C5 bind-drain merge (`bind_write_declarations`).
  - [ ] C6 connection dispatch tails → `_consume_fallback`.
  - [ ] C7 `slot_child_selections()` in `optimizer/selections.py`.
  - [ ] C8 `iter_relation_path()` shared `__`-path walker.
  - [ ] C9 iterative budgeted-walk primitive.
  - [ ] C10 column-backed conversion sharing (mutations+forms only).
  - [ ] C11 finalizer family-noun error formatters via `_SidecarBindingSpec`.
  - [ ] C12 underscore alias re-export blocks deleted (test retarget sweep).
  - [ ] C13 `editable_input_fields` onto `resolve_effective_fields`
        ([Decision 10](#decision-10--editable_input_fields-rides-the-shared-spine-strictness-tightening-accepted)).
- [ ] **Slice 4 — Contract-level DRY (WP-D, ~150 lines + doc debt)**
  - [ ] D1 single-window planner scheme through `_divergent_key_windows`.
  - [ ] D2 walker `_resolve_field_map` dual contract retired (FieldMeta
        fallback map).
  - [ ] D3 model relation decoder re-expressed over the shared spine.
- [ ] **Slice 5 — Docs fold-in + `0.0.16` cut + card wrap**
  - [ ] GLOSSARY/TREE/KANBAN fold-in per the completing-spec rules;
        `docs/GLOSSARY.md` status flips for anything this card shipped.
  - [ ] The version quintet: `pyproject.toml` `[project].version`,
        `django_strawberry_framework/__init__.py::__version__`,
        `tests/base/test_init.py`, the GLOSSARY package-version row, the
        root package entry in `uv.lock`.
  - [ ] `CHANGELOG.md` `0.0.16` entry (permission granted by this slice).
  - [ ] Card flip to Done + `KANBAN.md`/`KANBAN.html` regeneration from the
        DB; `import_spec_terms` run.

## Problem statement

The package works — 3,300+ tests green under a `fail_under = 100` gate — but
the maintainer reports alignment fatigue: ~47.3k lines (~19.7k code) across
14 subpackages plus 13 root modules, with several families (sets, inputs,
resolvers) that grew in parallel and re-spell shared shapes. A package split
was considered and rejected on evidence. What remains is the real work the
split instinct was pointing at: the optimizer/core boundary exists only by
convention (private `optimizer._context` is imported from two subsystems;
nothing enforces the seam), and four subsystem axes carry verified
duplication that makes every cross-cutting change cost more than it should.

## Current state

- The optimizer imports `registry`, `keyset`, `exceptions`, `conf`, and six
  `utils` modules; in the other direction `types/resolvers.py` imports the
  private `_context` module, while `mutations/resolvers.py` and
  `connection.py` import optimizer internals through `extension` (and
  `connection.py` also `nested_planner` / `plans` / `selections`). No
  mechanical check guards any of this.
- Soft dependencies (DRF, channels, cryptography, debug-toolbar) are guarded
  at runtime by `require_optional_module` but not advertised as pip extras.
- Prior DRY work already landed the big shared spines: the write pipeline
  skeleton (`mutations/resolvers.py::run_write_pipeline_sync`, spec-039
  P-series), the input-assembly substrate (`utils/inputs.py`), the query-side
  permission core (`utils/permissions.py` + `sets_mixins.py`), and the
  selection-walking home (`optimizer/selections.py`). The 32 candidates in
  this spec are what four fresh audits found still duplicated **after** those
  passes — plus the audits' verified-and-rejected ledger.
- The per-file DRY review cycle (`docs/dry/dry-0_0_13.md`, workflow
  `docs/dry/DRY.md`) is mid-flight and independent: it reviews one file at a
  time; this card is the cross-file strategic pass. Neither blocks the other.
- Card `WIP-ALPHA-044-0.0.14`
  ([`DjangoDebugExtension`][glossary-djangodebugextension]) is mid-flight and owns
  the `0.0.14` joint cut; card `TODO-ALPHA-045-0.0.15`
  ([`docs/spec-045-debug_extraction-0_0_15.md`][spec-045]) then **extracts
  that extension into the standalone `django-strawberry-debug` package**.
  This card is sequenced behind BOTH: by the time its slices run,
  `extensions/debug.py` is gone, `extensions/` is a soft-dependency leaf
  (the `rest_framework/` shape, guarded re-export + `[debug]` extra), and
  the extras pattern of Decision 5 already has its first member
  ([Risks](#risks-and-open-questions)).

## Goals

- The optimizer/core dependency architecture is written down and enforced in
  CI — the split question becomes moot because the boundary is real.
- Consumers can `pip install django-strawberry-framework[drf]` (etc.) and get
  the soft-dependency floor pinned for them.
- ~1,100–1,300 duplicated source lines removed across the four audited axes,
  with every consolidation either provably behavior-preserving or explicitly
  decision-pinned as a behavior change.
- Two invariants strengthened as side effects: the delete and plain-form
  mutation paths inherit all future write-skeleton hardening automatically,
  and the auth-alias guard becomes uniform across all mutation flavors.
- One live drift hazard eliminated (the filter dispatch ladder pair).
- The deliberate-duplication ledger recorded so future DRY passes don't
  re-litigate settled non-candidates.

## Non-goals

- **No package split.** Rejected on evidence; see Decision 1.
- **No new consumer-facing feature.** The extras are packaging metadata over
  existing behavior; no runtime surface changes except the two pinned
  behavior changes (Decisions 6 and 10).
- **No hot-path refactoring.** `_IndexedList.append_unique`,
  `included_field_selections`, `_merge_aliased_selections`, and the
  resolver bodies (`forward_resolver` / `many_resolver`) are out of bounds.
- **No docstring-thinning campaign.** The audits observed that ~51% of the
  package is prose; reducing prose is not this card (consolidations that
  delete duplicated docstrings alongside duplicated code are fine).
- **No test-suite DRY pass.** Intentional repetition in tests stays
  (docs/dry/DRY.md ground rule).

## Borrowing posture

- **`import-linter`** (external tool) supplies the boundary contracts —
  `layers`, `forbidden`, and `independence` contract types cover all four
  seams; no hand-rolled AST walker.
- **DRF / django-filter idioms**: the audits checked whether upstream
  machinery could replace hand-rolled code. Verdicts to carry into
  implementation: `sets_mixins.py::collect_related_declarations` is
  deliberately **stronger** than Django's `DeclarativeFieldsMetaclass`
  (diamond-tombstone reconciliation) — replacing it would regress; the
  permission-classes machinery already matches DRF's
  `APIView.check_permissions` shape; the one genuinely DRF-shaped remaining
  move is the dispatch-table style (`@convert.register`, already in-house as
  `utils/converters.py::convert_with_mro`) that C3/C8 extend to the filter
  ladders.

## User-facing API

The only consumer-visible additions are the extras:

```
pip install django-strawberry-framework[drf]
pip install django-strawberry-framework[channels]
pip install django-strawberry-framework[keyset-encryption]
pip install django-strawberry-framework[debug-toolbar]
```

Each extra pins the same floor the dev group already tests against. Absence
behavior is unchanged: the [`require_optional_module`][glossary-require_optional_module]
guards still raise the same install-hint errors when the module is missing.
Everything else in this card is package-internal.

## Architectural decisions

### Decision 1 — No package split — the boundary becomes formal, not physical

**Decision**: the package stays one distribution. The considered split
(standalone optimizer package, core depending on it) is rejected.

**Evidence**: (a) the optimizer's minimal import closure is ~12k lines (~25%
of the package; re-measure post-`60998b17`, which grew `utils/querysets.py`
by ~1,677 lines — see Slice 1 A0) including `registry`, `keyset`, and — via
`utils/querysets.py` — the mutation write pipeline
(`utils/write_transaction.py`); (b) the optimizer's input contract IS the
type system (`optimizer/walker.py` plans via `registry.get_definition`,
which returns `types/definition.py::DjangoTypeDefinition` objects only
[`finalize_django_types`][glossary-finalize_django_types]-built types
produce), so no external consumer could feed it; (c) reverse coupling is
wide and partly private (`types/resolvers.py` imports `optimizer._context`;
`mutations/resolvers.py` and `connection.py` import `optimizer.extension`,
and `connection.py` also `nested_planner`, `plans`, `selections` internals);
(d) ecosystem precedent
is uniformly against it — strawberry-django's optimizer was absorbed FROM a
separate package (strawberry-django-plus, 2023, ~8x perf gain credited to
unification), graphene-django-optimizer is heavily used but unmaintained,
join-monster is dead, and the one standalone strawberry optimizer attempt
died at 8 stars.

**Alternatives rejected**: 2-way split as proposed (no standalone audience;
private modules become public API; doubled release machinery); split at the
soft-dep seams (`rest_framework` → sibling package — architecturally clean
but buys nothing the extras don't); 3+ way core/types/optimizer split (the
LangChain coordination tale); monorepo-multi-wheel (least-bad mechanics,
still no audience, pip in-place upgrade hazard).

### Decision 2 — Card scope: maintainability only; consumer surface frozen

This card deliberately ships no new feature. Scope is (a) boundary
enforcement, (b) packaging metadata, (c) code compression with two pinned
behavior changes. Anything discovered mid-slice that would grow consumer
surface gets carded separately, not absorbed.

### Decision 3 — `import-linter` owns boundary enforcement

**Decision**: add `import-linter` as a dev-group dependency; declare
contracts in `pyproject.toml` `[tool.importlinter]`; run `lint-imports` in CI
and pre-commit. Maintainer-selected over a repo-local script.

Contracts (initial set):

1. **Optimizer inward surface** (`forbidden`):
   `django_strawberry_framework.optimizer` may not import
   `types`, `mutations`, `forms`, `filters`, `orders`, `rest_framework`,
   `connection`, `auth`, `extensions`, `middleware`, `testing`. (Allowed by
   omission: `registry`, `keyset`, `exceptions`, `conf`, `utils`, the root
   logger.)
2. **Private-module protection** (`forbidden`): no module outside
   `django_strawberry_framework.optimizer` imports
   `django_strawberry_framework.optimizer._context` (generalize to
   `optimizer._*` as further private modules appear). Satisfiable only after
   Decision 4 lands — sequence A2 before A1 inside Slice 1.
3. **Soft-dep leaves** (`forbidden`): core subpackages may not import
   `rest_framework`, `middleware`, `extensions`, or `testing` (matching the
   existing `require_optional_module` discipline; `testing` is a leaf by
   design; `extensions` is a soft-dep leaf by the time this contract is
   authored — card `045`'s extraction reduced it to the guarded
   `django-strawberry-debug` re-export).
4. **`utils` independence** (`forbidden`): `django_strawberry_framework.utils`
   imports no feature subpackage (`exceptions` and stdlib/Django only), with
   exactly two sanctioned function-local deferred imports whitelisted via the
   contract's `ignore_imports` — both exist to break real import cycles, not
   as boundary leaks:
   (i) `utils/querysets.py::related_visibility_queryset` does
   `from ..registry import registry` (deferred because `registry` imports
   `utils` at module load);
   (ii) `utils/write_values.py::type_check_relation_id` does
   `from ..relay import GlobalIDDecode, decode_model_global_id` inside the
   `relay.GlobalID` branch (deferred because `relay` imports `utils.querysets`
   at module level — cycle documented at the call site).
   TYPE_CHECKING-only upward imports (`utils/write_values.py`,
   `utils/errors.py` -> `mutations.inputs`) are covered by the
   type-checking-import exclusion (see Risks).

**Alternative rejected**: `scripts/check_import_boundaries.py` in the
existing repo-tooling style — zero new dependencies but we'd own the import
graph edge cases (TYPE_CHECKING blocks, in-function imports, string
references) that import-linter already handles.

### Decision 4 — Promote the optimizer's inward-facing API

**Decision**: the symbols other subsystems legitimately consume become the
optimizer's declared package-internal contract, re-exported from
`optimizer/__init__.py` with a docstring naming them as such. Verified
consumer inventory to cover: the `_context` names
(`DST_OPTIMIZER_FK_ID_ELISIONS`, `DST_OPTIMIZER_PLANNED`,
`DST_OPTIMIZER_STRICTNESS`, `get_context_value`) used by
`types/resolvers.py`;
`plans.resolver_key` / `plans.runtime_path_from_info`;
`extension.apply_connection_optimization` (used by `mutations/resolvers.py`
and `connection.py`) and `extension.mutation_payload_child_selections`
(used by `mutations/resolvers.py`); the `nested_planner` /
`selections` symbols `connection.py` uses; `field_meta.FieldMeta`;
`hints.OptimizerHint`; the optimizer `logger`. Pure re-export + retarget; no
symbol moves, no behavior change. After this, contract 2 of Decision 3 is
enforceable.

**Alternative rejected**: moving the shared symbols out of the optimizer
into a neutral module — churns every `::QualifiedName` doc reference for no
gain; the re-export achieves the same seam without relocation.

### Decision 5 — Packaging extras advertise the existing soft-dependency seams

**Decision**: `[project.optional-dependencies]` gains `drf`, `channels`,
`keyset-encryption`, `debug-toolbar`, each pinning the floor the dev group
already installs. The block itself already exists by this card: card `045`'s
extraction established it with the `debug` extra
(`django-strawberry-debug`); this card adds the remaining four members to
the same pattern. `[project].dependencies` is untouched; the runtime guards
are untouched; absence tests (the `sys.modules[name] = None` sentinel shape
in `tests/_soft_dependency.py`) are untouched. This is metadata, not
behavior.

### Decision 6 — Close the plain-form alias-guard gap

**Decision** (maintainer-approved): when
`forms/resolvers.py::_run_plain_form_pipeline_sync` folds onto the shared
skeleton (C2), it **gains** `pipeline_alias_guard` + `authorization_phase`
wrapping like every other flavor, rather than parameterizing the guard off.
Plain-form mutations' permission classes now run inside the same
transactional auth-alias isolation
([Multi-database cooperation][glossary-multi-database-cooperation]) as
model / ModelForm / serializer mutations.

**Rationale**: the exemption was an artifact of the fork, not a decision —
no docstring defends it. A uniform invariant is worth the small behavior
change (auth-alias statements in plain-form permission checks become
force-rolled-back, exactly as elsewhere).

**Alternative rejected**: preserving the exemption via a guard flag —
perpetuates a non-uniform security posture and adds a mode flag, the
anti-pattern docs/dry/DRY.md warns about.

### Decision 7 — Error-string byte-preservation policy

Every consolidation that touches a raise site must render the existing
message **byte-identically** — wording differences between families become
parameters (family noun, spec citation tail, accessor name), never averaged
prose. The existing pinned tests are the enforcement mechanism; a
consolidation that requires editing an error-string assertion is wrong until
a Decision here says otherwise (Decisions 6 and 10 are the only two).
This policy is what makes C11 (finalizer formatters), B1/B2, and the C10
error factories safe.

### Decision 8 — The deliberate-duplication ledger is part of the deliverable

The audits verified the following as **intentional, load-bearing
duplication**; they are recorded here as rejected candidates so future
sweeps (and future maintainer-agents) do not re-flag them:

- The ORM-vs-lateral window renderer pair
  (`optimizer/plans.py::apply_window_pagination` ↔
  `optimizer/lateral_fetch.py::build_lateral_sql`) — a byte-mirror contract,
  two SQL dialects of one `WindowRangePlan`; the shared
  `utils/connections.py` layer already IS the consolidation.
- Sync/async color twins (`connection.py::_pipeline_sync` /
  `_pipeline_async` and kin) — the repo convention pins colored steps
  explicit, never maybe-await.
- `derive_connection_window_bounds` vs `derive_keyset_window_bounds` — a
  deliberate vocabulary fork (offset vs cursor).
- The three per-flavor scalar tables (`models.Field` / `forms.Field` /
  `serializers.Field` key spaces) — three key spaces is the architecture.
- Per-flavor required/optional predicates — DRF's orthogonal `allow_null`
  semantics are load-bearing; do not unify predicates.
- The four disjoint `_ALLOWED_*_META_KEYS` frozensets (spec-039 Decision 13's
  named over-DRY trap).
- `rest_framework/sets.py::SerializerMutation.build_input`'s partial reuse of
  `cached_build_input` (documented at `#"P1.7 reuse is partial here"`).
- `keyset.py::split_order_ref` vs `plans.py::order_entry_name_and_direction`
  (loud config error vs soft fallback — documented).
- `filters/sets.py::FilterSet._evaluate_logic_tree`'s three branches (the
  combinators genuinely differ: `&=`, grouped `|=`, `~`).
- The `initial_queryset(target_type)` visibility-seed non-candidate at
  `filters/sets.py::FilterSet` (owner model may be a subclass —
  verified-and-rejected in a prior cycle).
- The `meta.__dict__` vs MRO-`getattr` asymmetry in `_validate_meta`
  (docstring: do not unify).
- `sets_mixins.py::collect_related_declarations`'s bespoke diamond-tombstone
  logic (stronger than upstream; replacement would regress).
- `forms/inputs.py::FormInputFieldSpec` vs the unified `InputFieldSpec`
  (spec-039 Decision 1 minimal-blast-radius choice; form suite pinned
  byte-equivalent).
- The two choice-enum caches (registry `(model, field)`-keyed vs
  `_SERIALIZER_CHOICE_ENUMS` name-keyed) — documented separate key spaces.
- `types/finalizer.py`'s per-field loops (`_build_annotations` /
  `_select_fields` / `_consumer_assigned_fields`) — distinct concerns,
  import-time only; merging trades clarity for nothing.
- `mutations/inputs.py::_audit_mutation_input_surface`'s post-consumer-merge
  re-walk — a different lifecycle point than `build_strawberry_input_class`'s
  own walk, not a duplicate.

### Decision 9 — Phase sequencing and hot-path exclusions

**Decision**: mechanical (Slice 2) → structural (Slice 3) → contract-level
(Slice 4), because Slice 2's per-family traversal descriptor is the
substrate for Slice 3's mixin work, and the skeleton folds (C1/C2) should
land before anyone touches the delete path again. Within Slice 3, C1+C2
land first (C2 carries the behavior change and its new coverage); C4 lands
after B3; C6 is verified against the spec-032 generic-specialization pins
before landing.

**Hot-path audit result**: no candidate touches the documented row-scaled
loops. The only per-request code touched is `_consume_fallback` delegation
(per-connection, non-window path) and plan-time-only code behind the
[Plan cache][glossary-plan-cache]. The maintainer accepted a small
performance cost; the plan's expected measured cost is ~zero, verified by
the Slice 4 bench runs ([Test plan](#test-plan)).

### Decision 10 — `editable_input_fields` rides the shared spine; strictness tightening accepted

**Decision** (maintainer-approved): C13 rebases
`mutations/inputs.py::editable_input_fields` on
`utils/inputs.py::resolve_effective_fields`, which brings
`normalize_field_name_sequence`'s bare-string/duplicate rejection to the
mutation flavor — inputs that previously slipped through now raise
[`ConfigurationError`][glossary-configurationerror] at class creation. This
is a fail-loud improvement, pinned here as an accepted behavior change. The
shared spine gains an `allow_empty` knob because the mutation flavor
legitimately defers its empty-set raise to `build_mutation_input` (a
consumer-`overrides` merge can empty the generated remainder).

### Decision 11 — Lone card at `0.0.16` — Slice 5 owns the version cut

Per the Step 3 scan, this card is the **only** non-Done card at `0.0.16`
(its board neighbors are `0.0.14` — the [joint version
cut][glossary-joint-version-cut] card `044` owns that line — `0.0.15` — the
lone debug-extraction card `045` owns that cut — and the `0.1.x` beta
queue). So this spec mirrors the lone-card shape (spec-038 Decision 14,
spec-044 Decision 12): Slice 5 carries the version quintet
(`pyproject.toml` `[project].version`,
`django_strawberry_framework/__init__.py::__version__`,
`tests/base/test_init.py`, the GLOSSARY package-version row, the root
package entry in `uv.lock`), the release-status doc moves, and the
`CHANGELOG.md` entry. No earlier slice moves any of the quintet.

### Decision 12 — TODO anchors stage the unbuilt slices

Per the repo's staging discipline, staged-but-unbuilt slices carry
`TODO(spec-046 Slice N)` source anchors at the sites they will change,
removed in the change that ships the slice. Caveat: the version-quintet
sites currently carry `TODO(spec-044 Slice 3)` anchors owned by the
in-flight `0.0.14` cut; this card adds its Slice 5 anchors **only after**
spec-044's cut lands and removes them ([Risks](#risks-and-open-questions)).

## Implementation plan

Per-slice delta table (estimates from the four audits; net = lines removed
minus helper lines added):

| Slice | Work package | Candidates | Est. net lines removed | Risk profile |
|---|---|---|---|---|
| 1 | WP-A boundary | A2 → A1 → A3 | ~0 (adds config) | LOW — re-exports + metadata |
| 2 | WP-B mechanical | B1–B5 (16 items) | ~450–550 | LOW — provably-coinciding behavior |
| 3 | WP-C structural | C1–C13 | ~500–600 | MEDIUM — pinned strings, ledger ordering, one behavior change (C2) |
| 4 | WP-D contract | D1–D3 | ~150 + doc debt | MED-HIGH — strictness accounting, test-double pins |
| 5 | Docs + cut | — | — | mechanical breadth |

Slice-2/3/4 candidate details — duplicated blocks, target helpers, per-item
risk, and the divergences that must be threaded as parameters (never
averaged) — are pinned in the audit findings summarized throughout this
spec; the executing agent works from this spec's checklist plus the
referenced symbols. Key parameterize-don't-average obligations, restated:

- C5: the bind-drain docstrings encode load-bearing ledger-reset ordering
  (retry idempotence); cache clears must not move.
- C8/C10: the filter side's `str` catch-all vs the form side's no-catch-all
  raise is a GOAL-level contract — share the MRO walk, never the table, and
  do not import `forms/converter.py` into `filters/`.
- C10: the serializer conversion spine stays separate (spec-039 Decision 1);
  the model-less relation core parameterizes the raw-pk-fallback vs
  require-primary divergence.
- D1: Decision-4/5/8 strictness accounting (malformed keys record
  identities; fallbacks must not), per-shape log reasons, and the `last: 0`
  quirk survive byte-for-byte.
- D3: the raw-pk existence fallback (`_relation_existence_error`,
  default-manager check) and the `_relation_membership_error`
  declared-vs-queried-pks contract survive as threaded parameters.

## Helper-reuse obligations (DRY)

New helpers this card introduces become the canonical owners; the executing
slices must retarget ALL call sites, not just the audited ones (sweep by
symbol before closing each item): `ActiveInputSetMixin` + the traversal
descriptor (`sets_mixins.py`), `PermissionClassesMixin`
(`mutations/permissions.py`), `relation_id_scalar` (`mutations/inputs.py`),
`name_set_input_type_name` (`utils/inputs.py`), `coerce_pks` +
`open_write_pipeline` + the substituted-row helper
(`utils/write_transaction.py` / `mutations/resolvers.py`),
`strawberry_schema_config` (`utils/typing.py`), `validate_relay_page_bound`
(`utils/connections.py`), `keyset_context_for` (`keyset.py`),
`slot_child_selections` (`optimizer/selections.py`), `iter_relation_path`
(`utils/relations.py`), the budgeted-walk primitive (`utils/`),
`install_input_namespace` (`utils/inputs.py`), `bind_write_declarations`
(`mutations/sets.py`), `require_subclass` (`utils/inputs.py` or
`exceptions.py` — executor's choice, documented at the definition).

## Edge cases and constraints

- **Concurrent sessions**: this repo is worked on in parallel; every slice
  must re-verify its target files against HEAD at execution time rather than
  trusting this spec's snapshot (the audits ran against a tree with active
  concurrent edits to `optimizer/walker.py` and others).
- **C6 `super()` binding**: `_consume_fallback` delegation must verify
  `super(DjangoConnection, cls)` reaches `ListConnection` for generated
  subclasses (spec-032 pins; through-schema tests exist).
- **C12 churn**: deleting the walker/extension underscore aliases retargets
  imports across all three test trees — mechanical but wide; do it as its
  own commit.
- **D2 test doubles**: tests pin the raw-field fallback shape
  (`SimpleNamespace` fields) — the FieldMeta-ized fallback map needs those
  doubles updated in the same change, and
  `nested_planner._raw_relation_field`'s re-fetch path re-verified.
- **B1 dead-delegate deletion** is gated on the cookbook-parity check (see
  Risks): if the delegates are documented consumer surface, they are
  absorbed (single implementation, kept methods) instead of deleted.
- **ASCII-only in `.py`**; trailing-comma layout; ruff format+check after
  every edit; symbol-qualified doc references re-swept for every renamed
  symbol.

## Test plan

- **Gate**: the full suite green under `fail_under = 100` at every slice
  boundary (run only at maintainer-invoked gates per `AGENTS.md`). Baseline
  note: the 49-failure + 1-collection-error baseline observed at authoring
  time has since resolved — the suite returned to green (4,371 passed, 100%
  coverage) at the `0.0.14` / `DONE-064` close on 2026-07-20; still reconcile
  the working-tree state with the maintainer before using the suite as this
  card's gate (concurrent sessions remain active).
- **Behavior changes get NEW coverage first** (the
  [live-first coverage mandate][glossary-live-first-coverage-mandate]):
  C2's newly-guarded plain-form path and C13's strictness rejections each
  get live-tier tests in `examples/fakeshop/test_query/` where reachable,
  package-tier otherwise.
- **Deleted delegates** ⇒ their package tests retarget to
  `utils/permissions.py` or are deleted; verify the coverage gate still
  holds (retire package-only stand-ins rule).
- **Error-string preservation**: the existing pinned tests are the proof;
  zero assertion edits outside Decisions 6/10.
- **Boundary**: `lint-imports` green in CI; a grep proves no `optimizer._`
  import survives outside `optimizer/`.
- **Perf sanity** (Slice 4 only): `scripts/bench_optimizer_walk.py` and
  `scripts/bench_nested_fetch.py` before/after; expect noise-level deltas
  (plan-time-only changes).
- **Extras**: an isolated-venv install of each extra (never the shared
  `.venv`) resolves and imports its guarded module.

## Doc updates

- Slice 1: `README.md` install section (extras); `docs/TREE.md` regen if
  module docstrings change.
- Slice 5 (the release-status set): `docs/GLOSSARY.md` (status flips + the
  package-version row via the glossary DB + re-render), `docs/README.md`,
  `docs/TREE.md`, `README.md`, `TODAY.md`, `KANBAN.md`/`KANBAN.html` (DB +
  regen), `CHANGELOG.md` (permission granted by this slice), `GOAL.md` only
  if its maintainability framing warrants it.

## Risks and open questions

- **Sequencing behind spec-044 AND spec-045**: card 044 owns the `0.0.14`
  cut (its TODO anchors sit on the version-quintet sites), and card 045's
  debug extraction ships `0.0.15` next — this card's Slice 1 contract
  wording and Slice 5 cut both assume the post-extraction tree. This card
  must not start Slice 5 (nor place its own quintet anchors) until BOTH
  cuts land. Preferred answer: begin Slices 1–2 only after card 045 wraps
  (they are cheap to hold and the contract wording depends on it); hold
  Slice 5 behind the `0.0.15` release. Fallback: if the queue stalls, the
  maintainer may re-order the cuts explicitly, and contract 3's
  `extensions` wording reverts to the pre-extraction (hard-import leaf)
  shape.
- **Cookbook-parity status of the dead query-side delegates**: several
  `FilterSet`/`OrderSet` permission delegates have zero package-internal
  callers but may be intentional documented surface
  ([Cookbook parity][glossary-cookbook-parity]). Preferred answer: delete
  (they are underscore-prefixed and internal-shaped); fallback: absorb into
  the mixin and keep the methods as thin documented wrappers. Resolve with
  the maintainer at Slice 2 execution.
- **C2 blast radius**: closing the alias-guard gap changes plain-form
  permission-check transaction semantics. Preferred answer: ship with new
  live coverage per Decision 6; fallback (only if a real consumer contract
  surfaces): the parameterized exemption, decision-documented.
- **Estimate confidence**: line-savings totals are audit estimates;
  individual items may shrink on contact with pinned tests. The card's
  success metric is the seam quality and the candidate disposition (done /
  rejected-with-reason), not hitting a lines number.
- **import-linter vs TYPE_CHECKING imports**: `registry.py` imports
  `DjangoTypeDefinition` under `TYPE_CHECKING` from `types/` — contracts
  must be configured to ignore type-checking-only imports (import-linter
  supports this) or the `utils`/optimizer contracts will false-positive.

## Out of scope (explicitly tracked elsewhere)

- The per-file DRY review cycle (`docs/dry/dry-0_0_13.md`) — continues
  independently.
- Any package split or new distribution — rejected, Decision 1.
- Test-tree DRY, docstring-volume reduction, and process/ceremony changes —
  raised in the maintainer conversation, not carded here.
- The beta-release cleanup card (now `TODO-ALPHA-047-0.1.0` after the
  renumbers — it ushers in the beta and closes the Alpha column) — this
  card's squeeze does not absorb its verification scope.
- The `DjangoDebugExtension` extraction — card `045`
  ([`docs/spec-045-debug_extraction-0_0_15.md`][spec-045]), which this card
  depends on.

## Definition of done

- [ ] `lint-imports` runs green in CI and pre-commit with the four contracts
      of Decision 3; no `optimizer._*` import exists outside `optimizer/`.
- [ ] `optimizer/__init__.py` declares the package-internal contract;
      `types/resolvers.py`, `mutations/resolvers.py`, `connection.py` import
      only through it.
- [ ] The four extras install and resolve in isolated venvs.
- [ ] Every Slice 2–4 candidate is either landed or recorded
      rejected-with-reason in this spec; the Decision 8 ledger is preserved.
- [ ] Plain-form mutations run inside `pipeline_alias_guard` +
      `authorization_phase` with live coverage (Decision 6).
- [ ] Full suite green under `fail_under = 100`; zero error-string assertion
      edits outside Decisions 6/10; bench deltas at noise level.
- [ ] Slice 5 shipped: version quintet at `0.0.16`, GLOSSARY flips,
      `CHANGELOG.md` entry, card flipped Done, `KANBAN.md`/`KANBAN.html`
      regenerated from the DB, `import_spec_terms` green.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[kanban]: ../KANBAN.md

<!-- docs/ -->
[glossary]: GLOSSARY.md
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangoformmutation]: GLOSSARY.md#djangoformmutation
[glossary-djangomodelformmutation]: GLOSSARY.md#djangomodelformmutation
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-optimizerhint]: GLOSSARY.md#optimizerhint
[glossary-connection-aware-optimizer-planning]: GLOSSARY.md#connection-aware-optimizer-planning
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-strictness-mode]: GLOSSARY.md#strictness-mode
[glossary-fk-id-elision]: GLOSSARY.md#fk-id-elision
[glossary-djangoconnection]: GLOSSARY.md#djangoconnection
[glossary-soft-dependency]: GLOSSARY.md#soft-dependency
[glossary-hard-dependency]: GLOSSARY.md#hard-dependency
[glossary-require_optional_module]: GLOSSARY.md#require_optional_module
[glossary-input-type-generation]: GLOSSARY.md#input-type-generation
[glossary-scalar-field-conversion]: GLOSSARY.md#scalar-field-conversion
[glossary-choice-enum-generation]: GLOSSARY.md#choice-enum-generation
[glossary-filter_input_type]: GLOSSARY.md#filter_input_type
[glossary-order_input_type]: GLOSSARY.md#order_input_type
[glossary-upload-scalar]: GLOSSARY.md#upload-scalar
[glossary-per-field-permission-hooks]: GLOSSARY.md#per-field-permission-hooks
[glossary-request_from_info]: GLOSSARY.md#request_from_info
[glossary-fielderror-envelope]: GLOSSARY.md#fielderror-envelope
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-ordering]: GLOSSARY.md#ordering
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-cookbook-parity]: GLOSSARY.md#cookbook-parity
[glossary-djangodebugextension]: GLOSSARY.md#djangodebugextension

<!-- docs/SPECS/ -->
[spec-038]: SPECS/spec-038-auth_mutations-0_0_13.md
[spec-045]: spec-045-debug_extraction-0_0_15.md
[spec-039]: SPECS/spec-039-serializer_mutations-0_0_13.md
[spec-043]: SPECS/spec-043-test_client-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[import-linter]: https://import-linter.readthedocs.io/
