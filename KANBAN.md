# django-strawberry-framework Kanban

Last refreshed: 2026-06-24

This board summarizes what is shipped, what has recently landed, and what remains to finish based on the current code, tests, docs, and release-readiness notes. It is intentionally written as a project-management view: each card has a status, priority, scope, and a practical definition of done.

Editing this board: `KANBAN.md` is a rendered artifact, not a source. The source of truth is the `kanban` Django app under [`examples/fakeshop/apps/kanban/`][kanban-app] — `BoardDoc` rows hold the prose sections (this preamble, the snapshot, the column intros, the footers), `Card` rows hold each card's identity / status / priority / dependencies, and `CardItem` / `CardReference` / `ParityClaim` rows hold the per-card bulleted body, blocking-or-related links between cards, and the parity claims against upstream packages. To change anything on the board, edit the relevant row(s) in the SQLite database at `examples/fakeshop/db.sqlite3` (Django admin or `manage.py shell`), then run `uv run python scripts/build_kanban_md.py` and `uv run python scripts/build_kanban_html.py` to regenerate `KANBAN.md` and `KANBAN.html`. Direct edits to `KANBAN.md` are overwritten on the next rebuild.

## Card ID format

Every card uses the form `<STATUS>[-<MILESTONE>]-NNN-X.Y.Z`:

- `<STATUS>` — the card workflow state: `BACKLOG` (unscheduled investigation / strategic-differentiation candidate), `TODO` (committed to a milestone, not yet active), `WIP` (actively being worked), or `DONE` (shipped). Updated when the card moves between workflow states. Blocking is not part of the workflow status; blocked cards render a derived `blocked` badge from unfinished `blocked_by` references and stay in their normal planning column.
- `<MILESTONE>` *(optional)* — the development phase the card lives in while it's still pre-shipping: `ALPHA` (pre-`0.1.0`), `BETA` (post-`0.1.0` / pre-`1.0.0`), or `STABLE` (post-`1.0.0`). Used on `BACKLOG`, `TODO`, and `WIP` cards. The two release cards themselves are tagged with the phase they usher in: `TODO-BETA-045-0.1.0` is the alpha → beta cut-over and `TODO-STABLE-060-1.0.0` is the beta → stable cut-over. **Dropped when the card ships** — `DONE` cards use the bare `DONE-NNN-X.Y.Z` form (no milestone segment). The card's version tag (`X.Y.Z`) already encodes which phase the shipment belongs to, and the bare form keeps the shipped-card cluster compact and uniform across the package's history.
- `NNN` — a 3-digit sequence number indicating the order the card was completed (`DONE` cards) or is being tracked (everything else; scheduled cards are ordered by planned ship version, and backlog cards sort after the scheduled board). **Unlike status, milestone, and version, this number is not stable** — it is recomputed whenever a card's position in the shipping sequence changes (reordered, new card inserted between two existing cards, version-tag bumped). Use the card title, not the NNN, when referencing a card from long-lived documents.
- `X.Y.Z` — the package version the card shipped in (`DONE` cards), is planned to ship in (scheduled cards), or is provisionally bucketed under (`BACKLOG` cards). Alpha cards span `0.0.6` through `0.0.14` leading up to `0.1.0`; Beta cards span `0.1.1` through `0.1.6` leading up to `1.0.0`. The `0.1.0` and `1.0.0` tags are reserved for the two release cards themselves. Backlog cards may use post-`1.0.0` buckets as ordering placeholders; they stay unscheduled until promoted to `TODO`.

For install, local development, testing, and the canonical documentation map, start from [`README.md`][readme].

## Relative size

A five-point T-shirt estimate of build effort — a planning estimate, not a commitment — anchored to the shipped Filtering subsystem (`DONE-027-0.0.8`) as XL:

- **XS** - trivial / mechanical; ≲½ day; one small module or a bookkeeping edit; no spec.
- **S** - small; ~1 day; one module + tests; light or no spec.
- **M** - moderate; a few days; multi-file, a real spec, a handful of design decisions.
- **L** - large subsystem; ~a week; new subpackage, full spec, broad integration.
- **XL** - very large subsystem at `DONE-027-0.0.8` scale.

## Snapshot

### Shipped foundation

- Layer 1 shared infrastructure is in place: `conf.py`, `exceptions.py`, `registry.py`, `utils/relations.py`, `utils/strings.py`, `utils/typing.py`, `py.typed`.
- The package builds directly on `strawberry-graphql` and does not depend on `strawberry-graphql-django`; that dependency boundary is intentional so this package controls its DRF-shaped API surface end-to-end.
- `DjangoType` is usable today for model-backed Strawberry types:
  - Meta validation for `model`, `fields`, `exclude`, `name`, `description`, `optimizer_hints`, and `interfaces`.
  - Deferred Meta keys are rejected loudly: `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`.
  - Scalar conversion, relation conversion, choice-enum generation, generated relation resolvers, and `get_queryset` sentinel detection are implemented.
- `DjangoOptimizerExtension` is usable today:
  - O1 through O6 are implemented: relation resolvers, root-gated planning, nested prefetch chains, `only()` projection, and `get_queryset`-aware `Prefetch` downgrade.
  - B1 through B8 are implemented: AST plan cache, FK-id elision, strictness mode, optimizer hints, context plan stashing, schema audit, precomputed field metadata, and queryset diffing.
  - Recent cache-key review findings are implemented in source: fragment-spread directives are collected and multi-operation documents hash the selected operation AST.
- 0.0.4 foundation slice has shipped (card `DONE-010-0.0.4`):
  - `DjangoTypeDefinition` is the canonical per-type metadata object stashed at `cls.__django_strawberry_definition__`, with forward-reserved slots (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`) ready for Layer 3 to populate.
  - `finalize_django_types()` resolves pending relations, attaches generated relation resolvers, and runs `strawberry.type(cls, ...)` for every collected type. Re-exported from `django_strawberry_framework` and `django_strawberry_framework.types`.
  - Pending-relation registry (`PendingRelation`, `add_pending_relation`, `iter_pending_relations`, `discard_pending`, `is_finalized`, `mark_finalized`, extended `clear`) supports definition-order-independent FK / reverse FK / forward + reverse OneToOne / forward + reverse M2M / multi-cycle graphs.
  - Manual relation override contract (`consumer_annotated_relation_fields` vs `consumer_assigned_relation_fields`): annotation-only overrides keep the generated relation resolver; `strawberry.field(resolver=...)` / `@strawberry.field` overrides suppress it.
  - Fail-loud unresolved-target finalization error names source model, source field, and target model.
  - OneToOne / M2M cardinality coverage now uses the real `library` example app; the old `tests.fixtures.apps.TestsCardinalityConfig` fixture app has been removed.
- 0.0.5 shipped after this foundation slice and is recorded separately as `DONE-015-0.0.5`.
- 0.0.6 shipped as the patch closing the foundation phase: `DONE-016-0.0.6` (`FieldMeta` consolidation), `DONE-017-0.0.6` (deferred scalar conversions), `DONE-018-0.0.6` (multiple `DjangoType`s per model with `Meta.primary`), and `DONE-019-0.0.6` (consumer override semantics for scalar fields).
- Test suite structure has caught up with the package shape:
  - `tests/optimizer/` covers `extension.py`, `walker.py`, `plans.py`, `hints.py`, `field_meta.py`, and `definition_order.py`.
  - `tests/types/` covers `base.py`, `converters.py`, `resolvers.py`, `definition_order.py`, and `definition_order_schema.py`.
  - `tests/test_registry.py` covers idempotency / phase-1 atomicity / phase-2/3 partial-mutation / pending-set cleanup / class-mutation residue.
  - `tests/utils/` covers utility modules.
  - The full suite runs through `uv run pytest`, including package tests, example-project tests, and live `/graphql/` HTTP tests, with 100% package coverage.

### In progress

- `0.0.7` shipped 2026-05-27 with seven cards: `DONE-020-0.0.7` (`DjangoListField`), `DONE-021-0.0.7` (`apps.py` and Django app config), `DONE-022-0.0.7` (schema-export management command), `DONE-023-0.0.7` (multi-database cooperation contract), `DONE-024-0.0.7` (Django Trac #37064 hardening + `safe_wrap_connection_method` consumer helper), `DONE-025-0.0.7` (warning-free scalar registration via `StrawberryConfig.scalar_map`), and `DONE-026-0.0.7` (scalar conversion end-to-end coverage in the fakeshop example with the new `apps.scalars` app plus a `BigIntegerField` on `apps.library.Patron`). Full card detail lives under the `## Done` board column below. Tag: `0.0.7` at commit `72f6cd9`.
- `0.0.8` shipped both planned read-side subsystems: the Filtering subsystem as `DONE-027-0.0.8` and the Ordering subsystem as `DONE-028-0.0.8`.
- `0.0.12` is the active patch. `DONE-029-0.0.9` (`DjangoType` consumer-DX cleanup) has shipped; the Relay connection cohort is complete — `DONE-030-0.0.9` (`DjangoConnectionField`, the central read-side primitive), `DONE-031-0.0.9` (Django-model-based GlobalID encoding), and `DONE-032-0.0.9` (the full Relay story) have shipped; `DONE-033-0.0.9` (connection-aware optimizer planning) has shipped, closing out the cohort. The version bump from `0.0.8` is owned by the joint `0.0.9` cut, not any single card, per Decision 11 of `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`. Blocked future cards stay in their normal planning columns with derived `blocked` badges, outside the active in-progress column.
- Strategic differentiation roadmap (post-`0.0.6`) captured in [`BACKLOG.md`][backlog]: items neither `graphene-django` nor `strawberry-graphql-django` ship cleanly that should land on the roadmap once parity items are shipped.

### Still not implemented

- Layer 3 public subsystems are still planned only:
  - `aggregates/`
  - `fieldset.py`
  - `permissions.py`
  - `utils/queryset.py`
- Layer 3 still needs the rest of the goal-level contract: declarative aggregation and permission rules configured through `Meta`, composing with the shipped filtering and ordering, and introspectable from one type definition.
- Several DjangoType contract gaps remain:
  - stable choice-enum naming override, because the first `DjangoType` to read a choice field currently wins the enum name
- Optimizer follow-up ideas remain outside the shipped B1-B8 surface:
  - model-property / cached-property optimization hints
- Test/example hygiene items surfaced by the foundation slice review have moved into the testing-shift docs and backlog: package-level override tests intentionally pin Strawberry internals while HTTP tests pin the consumer-visible override contract ([`BACKLOG.md`][backlog] item 38).
- The library GraphQL schema is real and wired into the project schema; the product-catalog Layer 3 aspirational schema block remains commented until those subsystems ship.

## Progress to 1.0.0

**63.3% complete** toward `1.0.0` - 38 of 60 cards done (65.6% size-weighted). Past the 50% mark. Backlog excluded; size-weighted by relative size (XS=1 .. XL=5).

| Milestone | Cards done | Size-weighted |
| --- | --- | --- |
| Alpha (pre-0.1.0) | 38/44 (86.4%) | 86.8% |
| Beta (pre-1.0.0) | 0/15 (0.0%) | 0.0% |
| Stable (post-1.0.0) | 0/1 (0.0%) | 0.0% |

To complete the Alpha (pre-0.1.0) milestone: **86.4%**.

## Board columns

## WIP / DONE spec map

| Card | Spec file |
| --- | --- |
| `DONE-038-0.0.12` - Form-based mutations (Django Forms / ModelForms) | [spec-038-form_mutations-0_0_12.md](docs/SPECS/spec-038-form_mutations-0_0_12.md) |
| `DONE-037-0.0.11` - Upload scalar and file / image field mapping | [spec-037-upload_file_image_mapping-0_0_11.md](docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md) |
| `DONE-036-0.0.11` - Mutations + auto-generated Input types | [spec-036-mutations-0_0_11.md](docs/SPECS/spec-036-mutations-0_0_11.md) |
| `DONE-035-0.0.10` - Optimizer robustness hardening (upstream-comparison guards) | [spec-035-optimizer_hardening-0_0_10.md](docs/SPECS/spec-035-optimizer_hardening-0_0_10.md) |
| `DONE-034-0.0.10` - Permissions subsystem | [spec-034-permissions-0_0_10.md](docs/SPECS/spec-034-permissions-0_0_10.md) |
| `DONE-033-0.0.9` - Connection-aware optimizer planning | [spec-033-connection_optimizer-0_0_9.md](docs/SPECS/spec-033-connection_optimizer-0_0_9.md) |
| `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation) | [spec-032-full_relay-0_0_9.md](docs/SPECS/spec-032-full_relay-0_0_9.md) |
| `DONE-031-0.0.9` - Django-model-based GlobalID encoding | [spec-031-globalid_encoding-0_0_9.md](docs/SPECS/spec-031-globalid_encoding-0_0_9.md) |
| `DONE-030-0.0.9` - `DjangoConnectionField` | [spec-030-connection_field-0_0_9.md](docs/SPECS/spec-030-connection_field-0_0_9.md) |
| `DONE-029-0.0.9` - `DjangoType` consumer-DX cleanup pass | [spec-029-consumer_dx_cleanup-0_0_9.md](docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md) |
| `DONE-028-0.0.8` - Ordering subsystem | [spec-028-orders-0_0_8.md](docs/SPECS/spec-028-orders-0_0_8.md) |
| `DONE-027-0.0.8` - Filtering subsystem | [spec-027-filters-0_0_8.md](docs/SPECS/spec-027-filters-0_0_8.md) |
| `DONE-026-0.0.7` - Scalar conversion end-to-end coverage in the fakeshop example | [spec-026-scalar_conversion_fakeshop-0_0_7.md](docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md) |
| `DONE-025-0.0.7` - Warning-free scalar registration via `StrawberryConfig.scalar_map` | [spec-025-scalar_map_helper-0_0_7.md](docs/SPECS/spec-025-scalar_map_helper-0_0_7.md) |
| `DONE-024-0.0.7` - Django Trac #37064 hardening + `safe_wrap_connection_method` | [spec-024-django_trac_37064_hardening-0_0_7.md](docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md) |
| `DONE-023-0.0.7` - Multi-database cooperation contract | [spec-023-multi_db-0_0_7.md](docs/SPECS/spec-023-multi_db-0_0_7.md) |
| `DONE-022-0.0.7` - Schema export management command | [spec-022-export_schema-0_0_7.md](docs/SPECS/spec-022-export_schema-0_0_7.md) |
| `DONE-021-0.0.7` - `apps.py` and Django app config | [spec-021-apps-0_0_7.md](docs/SPECS/spec-021-apps-0_0_7.md) |
| `DONE-020-0.0.7` - `DjangoListField` (non-Relay list) | [spec-020-list_field-0_0_7.md](docs/SPECS/spec-020-list_field-0_0_7.md) |
| `DONE-019-0.0.6` - Consumer override semantics (scalar fields) | [spec-019-consumer_overrides_scalar-0_0_6.md](docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md) |
| `DONE-018-0.0.6` - Multiple DjangoTypes per model with `Meta.primary` | [spec-018-meta_primary-0_0_6.md](docs/SPECS/spec-018-meta_primary-0_0_6.md) |
| `DONE-017-0.0.6` - Deferred scalar conversions | [spec-017-deferred_scalars-0_0_6.md](docs/SPECS/spec-017-deferred_scalars-0_0_6.md) |
| `DONE-016-0.0.6` - `FieldMeta` single-source-of-truth consolidation and mirror retirement | [spec-016-fieldmeta_consolidation-0_0_6.md](docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md) |
| `DONE-015-0.0.5` - 0.0.5 Relay interfaces and Node foundation | [spec-015-relay_interfaces-0_0_5.md](docs/SPECS/spec-015-relay_interfaces-0_0_5.md) |
| `DONE-014-0.0.4` - Move test fixture out of example settings | [spec-014-testing_shift-0_0_4.md](docs/SPECS/spec-014-testing_shift-0_0_4.md) |
| `DONE-013-0.0.4` - Real M2M coverage | [spec-013-real_m2m_coverage-0_0_4.md](docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md) |
| `DONE-012-0.0.4` - 0.0.4 version and release alignment | [spec-012-version_release_alignment-0_0_4.md](docs/SPECS/spec-012-version_release_alignment-0_0_4.md) |
| `DONE-011-0.0.4` - Stale placeholder cleanup | [spec-011-stale_placeholder_cleanup-0_0_4.md](docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md) |
| `DONE-010-0.0.4` - 0.0.4 foundation slice (definition-order independence) | [spec-010-foundation-0_0_4.md](docs/SPECS/spec-010-foundation-0_0_4.md) |
| `DONE-009-0.0.4` - Rich schema architecture | [spec-009-rich_schema_architecture-0_0_4.md](docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md) |
| `DONE-008-0.0.4` - Definition-order independence design | [spec-008-definition_order_independence-0_0_4.md](docs/SPECS/spec-008-definition_order_independence-0_0_4.md) |
| `DONE-007-0.0.4` - 0.0.4 onboarding docs and spec consolidation | [spec-007-onboarding_docs_spec_consolidation-0_0_4.md](docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md) |
| `DONE-006-0.0.3` - Documentation/status positioning for shipped Layer 2 | [spec-006-public_surface-0_0_3.md](docs/SPECS/spec-006-public_surface-0_0_3.md) |
| `DONE-005-0.0.3` - DjangoType contract and boundary | [spec-005-django_type_contract-0_0_3.md](docs/SPECS/spec-005-django_type_contract-0_0_3.md) |
| `DONE-004-0.0.3` - Optimizer beyond slices B1-B8 | [spec-004-optimizer_beyond-0_0_3.md](docs/SPECS/spec-004-optimizer_beyond-0_0_3.md) |
| `DONE-003-0.0.2` - Optimizer O4 nested prefetch chains | [spec-003-optimizer_nested_prefetch_chains-0_0_2.md](docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md) |
| `DONE-002-0.0.2` - Optimizer O1-O6 foundation | [spec-002-optimizer-0_0_2.md](docs/SPECS/spec-002-optimizer-0_0_2.md) |
| `DONE-001-0.0.1` - DjangoType core foundation | [spec-001-django_types-0_0_1.md](docs/SPECS/spec-001-django_types-0_0_1.md) |

## In progress

Cards actively being implemented — WIP is kept small (typically one or two) so work finishes before new work starts.

## To Do - Alpha (0.1.0)

Cards required to reach feature parity with both upstreams (`⚛️ graphene-django` and `🍓 strawberry-graphql-django`). Each card targets its own `0.0.x` patch within the road to **0.1.0**. The final card in this column is the `0.1.0` release itself (cleanup, verification, alpha → beta cut-over). Cards in NNN order = planned ship order; dependency and parallelism notes live on each card.

<a id="drf_serializer_mutations_serializermutation"></a>
### [TODO-ALPHA-039-0.0.13 - DRF serializer mutations (`SerializerMutation`)](KANBAN.html#drf_serializer_mutations_serializermutation)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Severity: Major
- Status: Planned
- Relative size: L
- Labels: `mutations`, `public-api`, `serializers`

#### Predicted files

- `django_strawberry_framework/rest_framework/` (planned)
- `tests/rest_framework/` (planned)

#### Planning note

needs spec

#### Dependencies

- `DONE-036-0.0.11` - Mutations + auto-generated Input types

#### Definition of done

- [ ] Add `docs/spec-serializer_mutations.md`.
- [ ] Implement `django_strawberry_framework/rest_framework/` exposing `SerializerMutation` (final name pinned during implementation) on the DRF-style Meta surface: `Meta.serializer_class`, `Meta.lookup_field`, `Meta.model_operations`, `Meta.optional_fields`.
- [ ] Serializer-field → Strawberry input mapping lives in `rest_framework/serializer_converter.py`, dual-purposed for inputs and outputs (mirroring graphene's `is_input=True` flag).
- [ ] `rest_framework` is a soft dependency: package import must succeed without DRF installed; the helper raises `ImportError` with an install hint when actually called.
- [ ] Validation errors surface through the shared `errors: list[FieldError]` envelope from `DONE-036-0.0.11`, populated from `serializer.errors`.
- [ ] Tests under `tests/rest_framework/`.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` exercising a `ModelSerializer` mutation.

#### Files likely touched

- `django_strawberry_framework/rest_framework/` (new)
- `tests/rest_framework/` (new)
- `examples/fakeshop/apps/products/schema.py`

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/mutation.py` — `SerializerMutationOptions` carrying `lookup_field`, `model_class`, `model_operations=["create", "update"]`, `serializer_class`, `optional_fields`; `SerializerMutation` class; `fields_for_serializer(serializer, only_fields, exclude_fields, is_input=False, convert_choices_to_enum=True, lookup_field=None, optional_fields=())` helper.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/serializer_converter.py` — DRF-field → GraphQL-type registry; same module covers input and output via `is_input` flag.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/types.py` — shared `ErrorType` envelope.

#### Why it matters

- `graphene-django` ships `SerializerMutation`, which builds a mutation from a DRF `Serializer` / `ModelSerializer`. This is the highest-leverage write-side feature for DRF migrants — they already have serializers defined and want to reuse them in GraphQL.
- [`GOAL.md`][goal] explicitly names DRF as a target migration source ("keep the public API familiar to Django, DRF, and django-filter users"). Shipping `SerializerMutation` is on-mission, not just a parity item.

#### Dependencies

- `DONE-036-0.0.11` — general mutation infrastructure (including the shared `errors` envelope).

#### Other

- graphene-django ships `SerializerMutation`; the highest-leverage write-side feature for DRF migrants.
- no on-board predecessor.
- new `rest_framework/` subpackage (serializer converter dual-purposed for inputs + outputs, plus `SerializerMutation`); soft DRF dependency. Reuses 036's infra + error envelope. Spec + tests + live HTTP.

#### Card references

- Dependency: `DONE-036-0.0.11` — general mutation infrastructure (including the shared `errors` envelope). -> `DONE-036-0.0.11` - Mutations + auto-generated Input types
- Related: Validation errors surface through the shared `errors: list[FieldError]` envelope from `DONE-036-0.0.11`, populated from `serializer.errors`. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="auth_mutations_login_logout_register"></a>
### [TODO-ALPHA-040-0.0.13 - Auth mutations (login / logout / register)](KANBAN.html#auth_mutations_login_logout_register)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Planned
- Relative size: M
- Labels: `auth`, `mutations`, `public-api`

#### Planning note

planned

#### Definition of done

- [ ] Implement `django_strawberry_framework/auth/` with `login_mutation`, `logout_mutation`, `register_mutation`, and a `current_user` query helper, each composable with the existing permissions surface.
- [ ] Mirrored tests under `tests/auth/`.
- [ ] Documented as opt-in: consumers must import explicitly; auth mutations are not injected into every schema.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/auth/` — `mutations.py` (login / logout / register), `queries.py` (`current_user`), `utils.py`.

#### Why it matters

- `strawberry-graphql-django` ships a small auth-mutations module so consumers don't have to hand-wire the most common Django auth flows. Natural follow-on once general mutations land.

#### Other

- strawberry-graphql-django ships a small auth-mutations module.
- depends on `DONE-036-0.0.11`.
- new `auth/` module (`login` / `logout` / `register` + `current_user` query helper) composing with permissions; builds on 036's mutation infra. Mirrored tests; opt-in import.

#### Card references

- Related: depends on `DONE-036-0.0.11`. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="channels_asgi_router_migration_aid"></a>
### [TODO-ALPHA-041-0.0.14 - Channels ASGI router (migration aid)](KANBAN.html#channels_asgi_router_migration_aid)

- Priority: Low
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Low
- Status: Planned
- Relative size: S
- Labels: `asgi`, `channels`, `django-integration`

#### Predicted files

- `django_strawberry_framework/routers.py` (planned)

#### Planning note

planned

#### Definition of done

- [ ] Implement `django_strawberry_framework/routers.py` exposing `DjangoGraphQLProtocolRouter` (final name pinned during implementation).
- [ ] `channels` is a soft dependency: top-level package import must not fail if `channels` is not installed. The helper wraps `channels` imports lazily and raises `ImportError` with an install hint when it is actually called.
- [ ] Tests under `tests/test_routers.py` exercise both the channels-present and channels-absent paths.
- [ ] Migration guide (`TODO-BETA-056-0.1.6`) gains a one-row entry in its "symbol equivalents" table mapping `AuthGraphQLProtocolTypeRouter` → `DjangoGraphQLProtocolRouter`, so the symbol rename is documented in one canonical location.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/routers.py` — `AuthGraphQLProtocolTypeRouter` wrapping `ProtocolTypeRouter`, `URLRouter`, `AllowedHostsOriginValidator`, `AuthMiddlewareStack`, plus `GraphQLHTTPConsumer` / `GraphQLWSConsumer`.

#### Architectural posture

- The router helper must use a **distinctly-ours symbol name** (working name: `DjangoGraphQLProtocolRouter`) so the module is unambiguously ours and does not impersonate the upstream API. This respects the [`GOAL.md`][goal] non-goal "a thin wrapper around `strawberry-graphql-django`".
- Migration ergonomics are preserved by the upstream-equivalent mapping in the migration guide (`TODO-BETA-056-0.1.6`), not by copying the symbol name. A migrant changes one import line: `from strawberry_django.routers import AuthGraphQLProtocolTypeRouter` → `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`.

#### Why it matters

- `strawberry-graphql-django` ships a small `routers.py` that builds a `ProtocolTypeRouter` over `GraphQLHTTPConsumer` and `GraphQLWSConsumer` for consumers using Channels. The module is ~30 lines but is the single import that makes ASGI / WebSocket migration painless.
- Shipping a functionally-equivalent helper lets strawberry-graphql-django migrants update one import line in their ASGI entrypoint. This card exists primarily to reduce migration friction, not to expand the API surface.

#### Other

- small slice; explicit migration aid.
- strawberry-graphql-django ships a Channels `ProtocolTypeRouter` helper; graphene-django ships none.
- small `routers.py` (~30 lines) with a soft `channels` dependency; tests for both channels-present and channels-absent paths. Pure migration-aid card.

#### Card references

- Related: Migration guide (`TODO-BETA-056-0.1.6`) gains a one-row entry in its "symbol equivalents" table mapping `AuthGraphQLProtocolTypeRouter` → `DjangoGraphQLProtocolRouter`, so the symbol rename is documented in one canonical location. -> `TODO-BETA-056-0.1.6` - Migration and adoption guides
- Related: Migration ergonomics are preserved by the upstream-equivalent mapping in the migration guide (`TODO-BETA-056-0.1.6`), not by copying the symbol name. A migrant changes one import line: `from strawberry_django.routers import AuthGraphQLProtocolTypeRouter` → `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`. -> `TODO-BETA-056-0.1.6` - Migration and adoption guides

<a id="debug_toolbar_middleware"></a>
### [TODO-ALPHA-042-0.0.14 - Debug-toolbar middleware](KANBAN.html#debug_toolbar_middleware)

- Priority: Low
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Low
- Status: Planned
- Relative size: M
- Labels: `debugging`, `django-integration`, `middleware`

#### Predicted files

- `django_strawberry_framework/middleware/debug_toolbar.py` (planned)

#### Planning note

planned

#### Definition of done

- [ ] Implement `django_strawberry_framework/middleware/debug_toolbar.py` exposing a `DebugToolbarMiddleware` that **subclasses** `debug_toolbar.middleware.DebugToolbarMiddleware` and overrides `process_view` + `_postprocess` for the two injection paths above.
- [ ] Ship the matching template asset at `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`; the middleware renders it via `render_to_string(...)` into HTML responses for the GraphiQL view.
- [ ] Introspection-query skip behavior preserved (no payload injection when `operationName == "IntrospectionQuery"`).
- [ ] `debug_toolbar` is a soft dependency: top-level package import must succeed without `django-debug-toolbar` installed; the middleware module raises `ImportError` with an install hint when actually imported.
- [ ] In-process test against a fakeshop request that emits SQL, covering both the GraphiQL HTML path and the JSON operation path.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/middlewares/debug_toolbar.py` — `DebugToolbarMiddleware` (subclasses upstream `debug_toolbar.middleware.DebugToolbarMiddleware`); module-level `_get_payload` helper; `_HTML_TYPES` constant for content-type sniffing.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html` — HTML snippet rendered into the GraphiQL response; ships as a template asset alongside the Python module.

#### Architectural posture

- **Not a from-scratch middleware**: strawberry-django **subclasses** `debug_toolbar.middleware.DebugToolbarMiddleware` and overrides `process_view` (to tag GraphiQL requests) and `_postprocess` (to inject the toolbar payload into the response). Our equivalent follows the same subclass-and-override shape; we do not re-implement the panel-rendering logic that `django-debug-toolbar` already owns.
- **GraphiQL-view detection**: strawberry-django tags `request._is_graphiql = bool(view and issubclass(view, BaseView))` where `BaseView` is `strawberry.django.views.BaseView`. Our equivalent uses the same `issubclass` check against whichever view class the package settles on (working name `DjangoGraphQLView`; pinned during implementation).
- **Two output paths, not one**:
- **HTML response** (the GraphiQL page itself): the middleware appends a rendered toolbar template to the response body and refreshes `Content-Length`.
- **JSON response** (a `/graphql/` operation result): the middleware parses the body, injects a `debugToolbar` key carrying per-panel `title` / `subtitle` metadata plus the toolbar's `requestId`, and re-encodes via `DjangoJSONEncoder`.
- **Introspection-query skip**: payload injection is suppressed when `operationName == "IntrospectionQuery"` so IDEs (Apollo Sandbox, etc.) that poll introspection on every keystroke don't flood their request history. Carry this behavior over.

#### Why it matters

- `strawberry-graphql-django` ships a `middlewares/debug_toolbar.py` so `django-debug-toolbar`'s SQL panel captures queries triggered by GraphQL resolvers. Without it, developers can't see the SQL hit by their queries during a `/graphql/` request.
- `graphene-django` ships **no** equivalent; this card is strawberry-graphql-django parity only.

#### Other

- developer experience.
- strawberry-graphql-django ships a debug-toolbar middleware; graphene-django ships none.
- subclass django-debug-toolbar's middleware with two injection paths (GraphiQL HTML + `/graphql/` JSON), a template asset, introspection-skip behavior, and a soft dependency. Single module + tests.

<a id="test_client_helper"></a>
### [TODO-ALPHA-043-0.0.14 - Test client helper](KANBAN.html#test_client_helper)

- Priority: Low
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Low
- Status: Planned
- Relative size: M
- Labels: `graphql-api`, `test-client`, `tests`, `uploads`

#### Predicted files

- `django_strawberry_framework/testing/client.py` (planned)

#### Planning note

planned

#### Dependencies

- `DONE-037-0.0.11` - Upload scalar and file / image field mapping

#### Definition of done

- [ ] Implement `django_strawberry_framework/testing/client.py` exposing `TestClient` / `AsyncTestClient` (per the inheritance shape pinned above) plus a `GraphQLTestMixin` and two concrete `(Mixin, TestCase)` / `(Mixin, TransactionTestCase)` combinations for the unittest crowd.
- [ ] Mixin carries `assertResponseNoErrors` / `assertResponseHasErrors` helpers (or the equivalent named for the chosen `.query()` return type).
- [ ] Project-wide endpoint settings key (working name `GRAPHQL_TESTING_ENDPOINT`, final name pinned during implementation) under `DJANGO_STRAWBERRY_FRAMEWORK`, with constructor / per-call override.
- [ ] Multipart file-upload support on `request()` so consumers can drive `Upload`-scalar mutations from the same helper once `DONE-037-0.0.11` ships.
- [ ] Live HTTP tests under `examples/fakeshop/test_query/` switch to the helper.
- [ ] Tests under `tests/testing/test_client.py`.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/test/client.py` — `TestClient` (subclasses Strawberry's `strawberry.test.BaseGraphQLTestClient`), `AsyncTestClient` (subclasses `TestClient`, takes an `AsyncClient`, overrides `.query()` and `.login()`). The `.query()` / `.mutate()` API surface lives on the upstream `BaseGraphQLTestClient`; strawberry-django adds Django-specific `request()`, `login()`, and the async `query()` override. `request()` switches to `format="multipart"` when `files=` is provided.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/utils/testing.py` — module-level `graphql_query` function; `GraphQLTestMixin` (the reusable mixin carrying `.query(...)`, `assertResponseNoErrors`, `assertResponseHasErrors`); `GraphQLTestCase` (`(GraphQLTestMixin, TestCase)`); `GraphQLTransactionTestCase` (`(GraphQLTestMixin, TransactionTestCase)`).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/settings.py #"TESTING_ENDPOINT"` — graphene reads `TESTING_ENDPOINT` (default `/graphql`) from its own settings dict so the testing helper has a project-wide override knob.

#### Architectural posture

- **Mixin-first shape** (graphene-django convention): the reusable piece is `GraphQLTestMixin`; the concrete `GraphQLTestCase` / `GraphQLTransactionTestCase` are two-line `(Mixin, TestCase)` / `(Mixin, TransactionTestCase)` combinations so consumers with their own custom TestCase base can compose the mixin in directly. Our equivalent follows the same mixin-first shape rather than only shipping the concrete subclasses.
- **`.query()` return type — decide before writing the spec**: strawberry-django returns a typed `Response` dataclass (`data` / `errors` / `extensions`); graphene-django's `GraphQLTestMixin.query` returns a raw Django `HttpResponse` paired with `assertResponseNoErrors` / `assertResponseHasErrors` helpers that parse the body. The two flavors are not interchangeable — pick one and pin it (the typed-dataclass shape is the more DRF-shaped choice and composes better with future typed-error work).
- **Async**: strawberry-django's `AsyncTestClient` subclasses `TestClient` (not `BaseGraphQLTestClient` directly), takes a `django.test.client.AsyncClient`, and only overrides `.query()` + `.login()`. The sync `request()` is reused via `cast("Awaitable", ...)`. Our equivalent ports the same inheritance shape (or picks a flatter alternative explicitly in the spec).
- **Endpoint resolution**: project-wide default reads from `DJANGO_STRAWBERRY_FRAMEWORK["GRAPHQL_TESTING_ENDPOINT"]` (mirrors graphene's `TESTING_ENDPOINT` knob; final settings-key name pinned during implementation), with a per-instance / per-call override identical to strawberry-django's `path` constructor argument and graphene-django's `graphql_url` per-call argument.
- **File-upload coupling**: strawberry-django's `request()` switches to `format="multipart"` when `files=` is provided. Our helper must do the same so live HTTP tests for `DONE-037-0.0.11` (Upload scalar) can exercise multipart uploads through the helper rather than dropping back to raw `client.post(...)` calls.
- **Strawberry base-class reuse — decide before writing the spec**: subclass `strawberry.test.BaseGraphQLTestClient` (less code, couples our `.query()` / `.mutate()` shape to upstream Strawberry's choices) vs. roll our own base (more code, full control over the public surface). The strawberry-django decision was to subclass; the package's DRF-first stance argues for considering the from-scratch alternative.

#### Why it matters

- `strawberry-graphql-django` ships `strawberry_django.test.client.TestClient`, a thin wrapper around `django.test.Client` that posts GraphQL requests with the right content type, parses the response, and exposes `.query(...)` / `.mutate(...)`.
- `graphene-django` ships `graphene_django.utils.testing` with `GraphQLTestMixin` / `GraphQLTestCase` / `GraphQLTransactionTestCase` / `graphql_query` helpers covering the same need.
- The fakeshop live tests already do this by hand; centralizing the pattern is a small win for consumers and keeps our HTTP tests crisp.

#### Dependencies

- `DONE-037-0.0.11` (Upload scalar) — the file-upload helper path lights up once Upload-scalar inputs exist; the helper itself ships without it but gains a tested path here.

#### Other

- developer experience.
- both upstreams ship a GraphQL test client / mixin.
- `test/client.py` (sync + async `TestClient`, a `GraphQLTestMixin`, two `(Mixin, TestCase)` combos), endpoint setting, multipart-upload support; several design decisions to pin; switch the fakeshop tests over.

#### Card references

- Dependency: `DONE-037-0.0.11` (Upload scalar) — the file-upload helper path lights up once Upload-scalar inputs exist; the helper itself ships without it but gains a tested path here. -> `DONE-037-0.0.11` - Upload scalar and file / image field mapping
- Related: Multipart file-upload support on `request()` so consumers can drive `Upload`-scalar mutations from the same helper once `DONE-037-0.0.11` ships. -> `DONE-037-0.0.11` - Upload scalar and file / image field mapping
- Related: **File-upload coupling**: strawberry-django's `request()` switches to `format="multipart"` when `files=` is provided. Our helper must do the same so live HTTP tests for `DONE-037-0.0.11` (Upload scalar) can exercise multipart uploads through the helper rather than dropping back to raw `client.post(...)` calls. -> `DONE-037-0.0.11` - Upload scalar and file / image field mapping

<a id="response_extensions_debug_middleware"></a>
### [TODO-ALPHA-044-0.0.14 - Response-extensions debug middleware](KANBAN.html#response_extensions_debug_middleware)

- Priority: Low
- Parity: ⚛️ graphene-django (Required)
- Severity: Low
- Status: Planned
- Relative size: M
- Labels: `debugging`, `graphql-api`, `middleware`

#### Predicted files

- `django_strawberry_framework/extensions/debug.py` (planned)
- `tests/extensions/` (planned)

#### Planning note

planned

#### Definition of done

- [ ] Implement `django_strawberry_framework/extensions/debug.py` as a Strawberry `SchemaExtension` that captures SQL and exceptions for the in-flight operation and attaches them to the response `extensions` map (key: `debug`).
- [ ] Pin the **exposure mechanism** (response-`extensions` map vs. schema-level `_debug` field) and the **fidelity choice** (cursor-wrap port vs. `connection.queries`) in the spec; default both to the simpler choice (response-`extensions` map + `connection.queries`) unless the spec authoring round chooses otherwise.
- [ ] Output shape mirrors graphene's `DjangoDebugSQL` / `DjangoDebugException` field names where the chosen fidelity supports them; document any shape narrowing (e.g., omitted Postgres-specific fields) explicitly.
- [ ] Off by default; opt-in via the extensions list passed to `strawberry.Schema(...)`.
- [ ] Tests under `tests/extensions/test_debug.py` against a fakeshop request that emits SQL.
- [ ] Documented as the response-side counterpart to `TODO-ALPHA-042-0.0.14`.

#### Files likely touched

- `django_strawberry_framework/extensions/` (new)
- `tests/extensions/` (new)

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/__init__.py` — exports `DjangoDebugMiddleware`, `DjangoDebug`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/middleware.py` — `DjangoDebugContext` (lifecycle around cursor wrapping, exception capture, accumulated debug object), `DjangoDebugMiddleware` (Graphene `resolve` middleware — see Architectural posture; wraps each field resolution and returns the accumulated debug object when the field's return type matches `DjangoDebug`).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/types.py` — `class DjangoDebug(ObjectType)` with `sql: List(DjangoDebugSQL)` and `exceptions: List(DjangoDebugException)`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/sql/types.py` — `DjangoDebugSQL` shape: `vendor`, `alias`, `sql`, `duration`, `raw_sql`, `params`, `start_time`, `stop_time`, `is_slow`, `is_select`, plus Postgres-specific `trans_id`, `trans_status`, `iso_level`, `encoding`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/exception/types.py` — `DjangoDebugException` shape: `exc_type`, `message`, `stack`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/sql/tracking.py` — thread-local cursor wrapping (`wrap_cursor`, `unwrap_cursor`, `NormalCursorWrapper`, `ExceptionCursorWrapper`, `ThreadLocalState`).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/exception/formating.py` — `wrap_exception` (serializes `exc_type`, `message`, `stack`).

#### Architectural posture

- **"Middleware" is overloaded here**: graphene-django's `DjangoDebugMiddleware` is a **Graphene field-resolver middleware** (a callable invoked around each `resolve(root, info, **args)`), not a Django request/response middleware. The card title says "middleware" because that's what the graphene side calls the same idea; our Strawberry-native shape is a `SchemaExtension` (operation-scoped), not a Django middleware. The file name `middleware.py` is preserved on the graphene side for parity with their naming; ours lives under `extensions/`.
- **Exposure mechanism — pick one before writing the spec**:
- graphene-django: **schema-level**. Consumers add a `_debug: DjangoDebug` field to their query and selectively pull `{ _debug { sql { duration } } }`. Pay-for-what-you-select.
- Card's proposed Strawberry-native shape: **response-extensions-level**. Always emit the whole map under `extensions["debug"]` when the extension is enabled, or skip it entirely.
- Both end up "in the GraphQL response," but the graphene shape gives consumers per-query selectivity at the cost of needing a schema field. The Strawberry-extension shape is simpler to wire and skips schema surface entirely.
- **Fidelity tradeoff — pick one before writing the spec**:
- **Port graphene's cursor wrapping** (`sql/tracking.py`): wraps `connection.cursor` per-thread so the wrapper sees `start_time` before `execute()` and computes precise `duration`, captures Postgres-specific `iso_level` / `encoding`, surfaces `is_slow` / `is_select` flags. Higher fidelity; requires thread-local state management and `enable_instrumentation` / `disable_instrumentation` lifecycle hooks tied to the extension's operation begin / end.
- **Use `django.db.connection.queries`**: the SchemaExtension reads `connection.queries` at operation end and emits a smaller shape. Lower fidelity (relies on Django's existing logging — no Postgres-specific data, less precise timing). Trivially threadsafe; no cursor wrapping to manage.
- **Thread-local state** (if porting the cursor wrap): `sql/tracking.py::ThreadLocalState` plus `enable_instrumentation` / `disable_instrumentation` are the lifecycle hooks. The SchemaExtension's `on_operation` (or equivalent) wraps `wrap_cursor` for the request and `unwrap_cursor` on teardown. Exception capture wires through the corresponding execution hooks similarly.

#### Why it matters

- `graphene-django` ships a debug subsystem that exposes the executed SQL queries and raised exceptions for each GraphQL request via a `DjangoDebug` object. This is different from `TODO-ALPHA-042-0.0.14` (django-debug-toolbar SQL panel UI): graphene's mechanism is **inside the GraphQL response**, so frontend clients and Apollo DevTools can read it without the toolbar. Both mechanisms are useful and not mutually exclusive.
- A Strawberry-native equivalent is a small `SchemaExtension` that captures SQL (through `django.db.connection.queries` or via a port of graphene's cursor-wrap mechanism — see Architectural posture) and exceptions and attaches the result to the response's `extensions` map.
- `strawberry-graphql-django` ships **no** equivalent (no file references `connection.queries` and no `*debug*` module exists outside the toolbar middleware tracked by `TODO-ALPHA-042-0.0.14`); this card is graphene-django parity only.

#### Other

- developer experience.
- graphene-django ships an in-response `DjangoDebug` SQL/exception subsystem; strawberry-graphql-django ships none.
- distinct from `TODO-ALPHA-042-0.0.14` (Django debug toolbar).
- a Strawberry `SchemaExtension` that captures SQL + exceptions into `extensions['debug']`; one design choice between porting graphene's cursor-wrap and reading `connection.queries`. Single extension module + tests.

#### Card references

- Related: Documented as the response-side counterpart to `TODO-ALPHA-042-0.0.14`. -> `TODO-ALPHA-042-0.0.14` - Debug-toolbar middleware
- Related: `graphene-django` ships a debug subsystem that exposes the executed SQL queries and raised exceptions for each GraphQL request via a `DjangoDebug` object. This is different from `TODO-ALPHA-042-0.0.14` (django-debug-toolbar SQL panel UI): graphene's mechanism is **inside the GraphQL response**, so frontend clients and Apollo DevTools can read it without the toolbar. Both mechanisms are useful and not mutually exclusive. -> `TODO-ALPHA-042-0.0.14` - Debug-toolbar middleware
- Related: `strawberry-graphql-django` ships **no** equivalent (no file references `connection.queries` and no `*debug*` module exists outside the toolbar middleware tracked by `TODO-ALPHA-042-0.0.14`); this card is graphene-django parity only. -> `TODO-ALPHA-042-0.0.14` - Debug-toolbar middleware
- Related: distinct from `TODO-ALPHA-042-0.0.14` (Django debug toolbar). -> `TODO-ALPHA-042-0.0.14` - Debug-toolbar middleware

## To Do - Beta (1.0.0)

Cards that complete the django-graphene-filters Layer-3 richness on top of parity (`fields_class`, `aggregate_class`, `search_fields`, plus pre-stable cleanup). Each card targets its own `0.1.x` patch within the road to **1.0.0**. The final card in this column is the `1.0.0` release itself (API freeze, cleanup, verification, beta → stable cut-over). Cards in NNN order = planned ship order.

<a id="beta_release_cleanup_verification_alpha_beta"></a>
### [TODO-BETA-045-0.1.0 - Beta release (cleanup, verification, alpha → beta)](KANBAN.html#beta_release_cleanup_verification_alpha_beta)

- Priority: High
- Severity: Major
- Status: Planned
- Relative size: M
- Labels: `cleanup`, `release`, `tests`

#### Predicted files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`tests/base/test_init.py`](tests/base/test_init.py)

#### Planning note

planned

#### Definition of done

- [ ] Every other Alpha card (`ALPHA-013-0.0.6` through `ALPHA-044-0.0.14` plus `ALPHA-024-0.0.9`) is in `DONE`.
- [ ] Full test pass under each supported `(Python, Django, Strawberry)` combination.
- [ ] Coverage stays at 100% for the package source tree.
- [ ] Version bumped to `0.1.0` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock`.
- [ ] `CHANGELOG.md` `[Unreleased]` block promoted to `## [0.1.0] - YYYY-MM-DD` with a one-paragraph release summary plus the cumulative Added / Changed / Fixed / Removed sections covering `0.0.6` through `0.0.14`.
- [ ] `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, and `docs/TREE.md` cross-checked against the actual shipped surface; "shipped" / "planned" status markers updated.
- [ ] Audit pass against the parity findings: every ⚛️ and 🍓 card from the two upstream audits is either `DONE` or explicitly deferred with a recorded reason.
- [ ] Tag the release in git and publish to PyPI.

#### Files likely touched

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`

#### Why it matters

- This card is the formal cut-over from alpha (`0.0.x`) to beta (`0.1.0`). When every other Alpha card is in `DONE`, this card is the only thing left between the current state and the beta release. It exists to make the milestone explicit and to give the cleanup / verification work a place to live.
- Without a dedicated release card, the alpha → beta transition becomes an unstructured handful of doc tweaks and version bumps spread across the last few patches. Tracking it explicitly forces the parity audit and the full test pass to happen on a single named slice.

#### Other

- release card.
- release / verification card — gates the alpha → beta cut; not an upstream-parity feature.
- release-blocking.
- final card in the Alpha queue; gates the alpha → beta milestone.
- release / verification card, no new subsystem: full `(Python, Django, Strawberry)` matrix pass, 100% coverage, version bump to `0.1.0`, CHANGELOG promotion, doc status cross-check, parity audit, tag + publish.

<a id="fieldset"></a>
### [TODO-BETA-046-0.1.1 - `FieldSet`](KANBAN.html#fieldset)

- Priority: High
- Severity: Medium
- Status: Needs spec
- Relative size: M
- Labels: `fieldsets`, `layer-3`, `public-api`

#### Predicted files

- `django_strawberry_framework/fieldset/` (planned)

#### Planning note

Strawberry port of graphene-django's `AdvancedFieldSet` — the declarative field-level behavior layer that the cookbook drives via `Meta.fields_class`. The cookbook shape: a consumer-authored `class GalaxyFieldSet(FieldSet)` carries `resolve_<field>(self, root, info)` overrides for custom resolution, `check_<field>_permission(self, info)` denial gates that raise before resolve runs, and class-level annotations like `display_name: str | None = strawberry.field(description="...")` for computed fields the Django model does not have. Pointed at by `Meta.fields_class = GalaxyFieldSet` on the owning `DjangoType`. This is the smallest Layer-3 surface by file count but the most novel by semantic surface area — the resolver-override contract, the redaction-vs-denial split, and the computed-field annotation discipline all live here.

#### Dependencies

- `DONE-030-0.0.9` - `DjangoConnectionField`

#### Scope

- Cookbook anchor: the `fields.py` example in `GOAL.md` and the `recipes/fields.py` in the django-graphene-filters cookbook are the canonical shapes. Tiered date visibility (staff → full datetime, perm-holder → day precision, authenticated → month precision, anonymous → year precision) plus redaction-vs-denial (`resolve_is_private` returns `False` for non-staff = redaction; `check_updated_date_permission` raises for anonymous = denial) plus computed-field annotations (`display_name: str | None = strawberry.field(...)` with `resolve_display_name`) are the three patterns the FieldSet contract must support cleanly.
- Class shape: `class FooFieldSet(FieldSet)` with `class Meta: model = Foo`. The body holds three flavors of declarations: `resolve_<field>(self, root, info)` (custom resolver, overrides the auto-generated one for `<field>`), `check_<field>_permission(self, info)` (denial gate; raises `GraphQLError` or returns silently — runs before `resolve_<field>` for this request), and class-level annotated attributes (computed fields the model does not have; paired with a `resolve_<field>` method).
- Wiring: `DjangoType.Meta.fields_class = FooFieldSet` binds the fieldset at finalizer phase 2.5 (the same seam `filterset_class` / `orderset_class` use). At type-creation time the framework wires each `resolve_<field>` / `check_<field>_permission` into the owning `DjangoType`'s resolver chain so consumers do not have to subclass the type or hand-attach decorators.
- Composes with `DjangoType.Meta.fields`: declaring `Meta.fields = ("id", "name", ...)` on the owning type stays the source of truth for which model fields surface; `FieldSet` only customizes resolution / permission for fields already in `Meta.fields` AND declares any computed fields via class-level annotations.
- Optimizer cooperation: a `resolve_<field>` that touches ORM data (e.g. tiered date redaction reads `root.created_date`) must NOT defeat the optimizer's `only_fields` projection. The fieldset declares which model columns its resolvers depend on via `Meta.depends_on = {"resolve_created_date": ("created_date",), ...}` (or auto-introspection if reliably available); the optimizer adds those columns to the `only()` projection so the resolver does not trigger a deferred-field fetch.
- Composability with `apply_cascade_permissions` (`DONE-034-0.0.10`): a `check_<field>_permission` gate that raises does NOT short-circuit cascade visibility; the cascade narrows the queryset first, then field-level gates run on whatever survives. A field denial does not leak existence — null fields and denials look identical to the client.

#### Definition of done

- [ ] Add `docs/spec-fieldset.md` covering the `resolve_<field>` override contract, the `check_<field>_permission` denial-vs-redaction guidance, the computed-field annotation discipline (`display_name: str | None = strawberry.field(...)`), and the optimizer `depends_on` contract.
- [ ] Implement `django_strawberry_framework/fieldset/` (package, mirroring the `filters/` shape) with `base.py` (FieldSet class + metaclass), `factories.py` (resolver-binding factory), and a per-fieldset finalizer hook in `types/finalizer.py` phase 2.5.
- [ ] `FieldSet` accepts `class Meta: model = Foo` only; field declarations are method-based (`resolve_<field>`, `check_<field>_permission`) plus class-level computed-field annotations. No `Meta.fields` on the FieldSet itself — the owning `DjangoType.Meta.fields` is the single source of truth for the model-field surface.
- [ ] Optimizer `Meta.depends_on` contract: when a `resolve_<field>` reads model columns the owning type's `Meta.fields` does not surface, the FieldSet declares them via `Meta.depends_on`; the optimizer adds those columns to the `only_fields` projection.
- [ ] Promote `Meta.fields_class` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the resolver-binding pipeline applies end-to-end (per `TODO-BETA-050-0.1.3`).
- [ ] Tests under `tests/fieldset/` mirror the source one-to-one. Live HTTP coverage under `examples/fakeshop/test_query/` exercises tiered visibility (staff vs perm-holder vs authenticated vs anonymous), redaction (non-staff sees `is_private = False`), denial (anonymous raises on `updated_date`), and a computed field (`display_name` resolves only for authenticated users).
- [ ] Composability tests: `FieldSet` + `FilterSet` (a field with a `check_<field>_permission` gate is still filterable by an authorized user); `FieldSet` + `OrderSet` (same for ordering); `FieldSet` + `apply_cascade_permissions` (cascade narrows first, then field gates run — no existence leak).

#### Foundation-slice seam

- `DjangoTypeDefinition.fields_class` is the forward-reserved slot the collection phase will populate.
- `Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (see also [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` custom Strawberry field class that field-level permissions will likely require).
- Phase-2.5 finalizer wiring follows the shipped `_bind_filtersets` / `_bind_ordersets` pattern. New helper `_bind_fieldsets` (or the equivalent dispatched form when `TODO-BETA-050-0.1.3` lands) binds each `Meta.fields_class` to its owning `DjangoTypeDefinition` so resolvers and gates are wired before schema construction.
- Per-field resolver attachment: the existing `_attach_relation_resolvers` already accepts a `skip_field_names` set so consumer-authored fields are not clobbered; FieldSet-bound `resolve_<field>` extends that skip-set so the FieldSet's resolver wins over the auto-generated scalar resolver.
- Custom Strawberry field class — graphene's `AdvancedFieldSet` works with a custom field type that carries the `check_<field>_permission` gate at resolve time. Strawberry's `strawberry.field(...)` already supports a `permission_classes` argument; the spec must decide between mapping `check_<field>_permission` onto that machinery or carrying a parallel gate. See [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` direction.
- Slot realized in `DONE-034-0.0.10`: `DjangoTypeDefinition.fields_class` is now declared as an inert `type | None = None` sidecar (spec-034 Decision 2 — the structural mirror of the shipped `filterset_class` / `orderset_class` slots). It has no populator yet and stays `None`; `Meta.fields_class` remains in `DEFERRED_META_KEYS` (still rejected at validation). This card's `_bind_fieldsets` is what populates the slot and promotes the key end-to-end.

#### Architectural posture

- Non-goal — node-level sentinel redaction. The upstream `django_graphene_filters/object_type.py::AdvancedDjangoObjectType.get_node` / `_make_sentinel` (`is_redacted=True`) masks a hidden non-null FK target in place instead of dropping the row. The package deliberately did **not** adopt this tier (spec-034 Decision 6 chose row-exclusion), and `FieldSet` does **not** revive it. The redaction taxonomy is two-tier: relation/row visibility = queryset narrowing (`apply_cascade_permissions`, which is why the fakeshop `view_<model>` hooks cascade rather than keep a row with a sentinel FK), field visibility = `FieldSet` (redact value / deny). There is no third node-sentinel tier — `FieldSet` redaction runs only on fields of rows that already survived the cascade; it never masks a relation target to keep an otherwise-hidden row visible. It is now tracked as an explicit, opt-in tier — `TODO-BETA-051-0.1.4` (`Meta.redaction_mode`) — for consumers who explicitly want strict django-graphene-filters node-sentinel parity; it stays opt-in (not the default) because it conflicts with the row-narrowing model.

#### Why it matters

- `FieldSet` is the smallest Layer 3 surface and can define field-selection semantics used by `DjangoConnectionField`.
- It bridges the existing `DjangoType.Meta.fields` behavior and future connection/query APIs.
- Field-level visibility is the only cookbook surface where redaction (return a safe value) and denial (raise an error) need to be distinct. Filter / order / cascade all use queryset narrowing — they remove rows. FieldSet is the one place where a row stays visible but a field is either redacted or guarded behind an error. Without it, the cookbook's `is_private` and `description` patterns are not portable.
- Computed fields (annotations like `display_name: str | None = strawberry.field(...)` paired with `resolve_display_name`) are the cookbook's escape hatch for fields the Django model does not have. The framework currently has no declarative way to add them without subclassing `DjangoType`; the FieldSet is the home for that contract.

#### Dependencies

- `DjangoConnectionField` (`DONE-030-0.0.9`) - `FieldSet` composes on top of the shipped connection-field surface.

#### Other

- the smallest Layer-3 subsystem: `fieldset.py` + `docs/spec-fieldset.md` + tests; defines field-selection semantics the connection field consumes. Meta-driven.

#### Card references

- Dependency: `DjangoConnectionField` (`DONE-030-0.0.9`) - `FieldSet` composes on top of the shipped connection-field surface. -> `DONE-030-0.0.9` - `DjangoConnectionField`
- Related: `DONE-034-0.0.10` - Permissions subsystem
- Related: `TODO-BETA-050-0.1.3` - Layer 3 Meta key promotion
- Related: `TODO-BETA-051-0.1.4` - Opt-in node-sentinel redaction tier (`Meta.redaction_mode`)

<a id="metasearch_fields_support"></a>
### [TODO-BETA-047-0.1.2 - `Meta.search_fields` support](KANBAN.html#metasearch_fields_support)

- Priority: High
- Severity: Medium
- Status: Planned
- Relative size: M
- Labels: `connections`, `filters`, `public-api`, `search`

#### Predicted files

- [`django_strawberry_framework/filters/`](django_strawberry_framework/filters/)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- `tests/filters/test_search_fields.py` (planned)

#### Planning note

Strawberry analogue of graphene-django's `Meta.search_fields`. The cookbook shape is a tuple of model-field paths including relation-traversal entries: `search_fields = ("name", "description", "object_type__name", "object_type__description")`. The framework adds a single `search: String` argument to `DjangoConnectionField` consumers; when supplied, the framework fans the input across every declared path as an OR'd `icontains` filter and joins the resulting Q-object into the queryset. Relation paths use Django's standard double-underscore lookup syntax; the framework relies on Django's existing relation traversal rather than a custom resolver. Planned; gated on `DONE-027-0.0.8` (Filtering) and `DONE-030-0.0.9` (`DjangoConnectionField`).

#### Dependencies

- `DONE-027-0.0.8` - Filtering subsystem
- `DONE-030-0.0.9` - `DjangoConnectionField`

#### Scope

- Cookbook anchor: the `recipes/schema.py` example shipped with django-graphene-filters declares `search_fields = ("name", "description", "object_type__name", "object_type__description")` — flat field names AND relation-traversal paths in the same tuple. The framework must accept both shapes identically; relation traversal is built on Django's standard `<rel>__<field>` lookup syntax.
- Argument shape: a single `search: String` argument on the connection field. Empty/null/whitespace-only input is a no-op (queryset passes through unchanged). Non-empty input produces a single Q-object that OR's `<path>__icontains=<input>` across every declared path.
- Composition with `filterset_class`: `search` and `filter` compose by intersection — the resulting queryset matches every declared filter AND the search OR-clause. The argument-factory machinery is shared between `filterset_class` and `search_fields`, so adding `search` does not duplicate the factory infrastructure.
- Composition with `get_queryset`: search runs against the post-visibility queryset (visibility narrows first), so a user cannot search for hidden rows by guessing field values.

#### Definition of done

- [ ] Add `docs/spec-search_fields.md`.
- [ ] Search-fields argument generation lives in `django_strawberry_framework/filters/` and reuses the same DRF-style Meta surface and argument-factory machinery as `filterset_class`.
- [ ] Single `search: String` argument surfaces on `DjangoConnectionField` consumers and produces an OR'd `icontains` queryset filter across every declared field path.
- [ ] Promote `Meta.search_fields` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the pipeline applies it end-to-end (per `TODO-BETA-050-0.1.3`).
- [ ] Tests under `tests/filters/test_search_fields.py` covering single-field, relation-path, and combined-with-filterset cases.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` exercising a search across at least one relation path.

#### Files likely touched

- `django_strawberry_framework/filters/` (search support)
- `django_strawberry_framework/types/base.py` (Meta validation; promote key)
- `tests/filters/test_search_fields.py` (new)
- `examples/fakeshop/apps/products/schema.py` (activation)

#### Why it matters

- `Meta.search_fields` is one of the five django-graphene-filters Layer-3 Meta keys explicitly listed in [`GOAL.md`][goal] alongside `filterset_class`, `orderset_class`, `aggregate_class`, and `fields_class`. Without it the package cannot claim full DGF parity at 1.0.0.
- Currently `search_fields` is in `DEFERRED_META_KEYS` and rejected at validation time. `TODO-BETA-053-0.1.5` (Fakeshop schema activation) explicitly carries a note to "move or defer `search_fields` before uncommenting" because of this gap.

#### Dependencies

- `DONE-027-0.0.8` (Filtering subsystem) — the argument factory is shared.
- `DONE-030-0.0.9` (`DjangoConnectionField`) — the `search: String` argument surfaces on connection fields.

#### Other

- a single `search: String` argument fanning out as an OR'd `icontains` across declared field paths; reuses `DONE-027-0.0.8`'s argument-factory machinery. Spec + tests + live HTTP + Meta-key promotion.
- `django-graphene-filters` exposes `Meta.search_fields = ("name", "description", "category__name")` — a tuple of model-field paths. The connection field gains a single `search: String` argument that fans out across the listed fields as an OR'd `icontains` filter, traversing relations through Django's standard ORM lookup syntax.

#### Card references

- Dependency: planned; gated on `DONE-027-0.0.8` (Filtering) and `DONE-030-0.0.9` (DjangoConnectionField) -> `DONE-027-0.0.8` - Filtering subsystem
- Dependency: `DONE-027-0.0.8` (Filtering subsystem) — the argument factory is shared. -> `DONE-027-0.0.8` - Filtering subsystem
- Related: Promote `Meta.search_fields` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the pipeline applies it end-to-end (per `TODO-BETA-050-0.1.3`). -> `TODO-BETA-050-0.1.3` - Layer 3 Meta key promotion
- Dependency: planned; gated on `DONE-027-0.0.8` (Filtering) and `DONE-030-0.0.9` (DjangoConnectionField) -> `DONE-030-0.0.9` - `DjangoConnectionField`
- Dependency: `DONE-030-0.0.9` (`DjangoConnectionField`) — the `search: String` argument surfaces on connection fields. -> `DONE-030-0.0.9` - `DjangoConnectionField`
- Related: Currently `search_fields` is in `DEFERRED_META_KEYS` and rejected at validation time. `TODO-BETA-053-0.1.5` (Fakeshop schema activation) explicitly carries a note to "move or defer `search_fields` before uncommenting" because of this gap. -> `TODO-BETA-053-0.1.5` - Fakeshop GraphQL schema activation
- Related: a single `search: String` argument fanning out as an OR'd `icontains` across declared field paths; reuses `DONE-027-0.0.8`'s argument-factory machinery. Spec + tests + live HTTP + Meta-key promotion. -> `DONE-027-0.0.8` - Filtering subsystem

<a id="postgres_full_text_search_filter_primitives"></a>
### [TODO-BETA-048-0.1.2 - Postgres full-text search filter primitives](KANBAN.html#postgres_full_text_search_filter_primitives)

- Priority: Medium
- Severity: Medium
- Status: Planned
- Relative size: M
- Labels: `filters`, `public-api`, `search`

#### Predicted files

- [`django_strawberry_framework/filters/base.py`](django_strawberry_framework/filters/base.py)
- [`django_strawberry_framework/filters/inputs.py`](django_strawberry_framework/filters/inputs.py)
- [`examples/fakeshop/test_query/`](examples/fakeshop/test_query/)
- `tests/filters/test_pg_full_text.py` (planned)

#### Planning note

Strawberry analogue of django-graphene-filters' Postgres full-text search family. The cookbook ships `AnnotatedFilter` (base) plus `SearchQueryFilter`, `SearchRankFilter`, and `TrigramFilter` in `django_graphene_filters/filters.py`, with matching `SearchQueryFilterInputType` / `SearchRankFilterInputType` / `TrigramFilterInputType` input shapes in `django_graphene_filters/input_types.py`. These add Postgres-only `searchQuery` / `searchRank` / `trigram` filter inputs to FilterSets on Postgres-backed models, layered on `django.contrib.postgres.search`. Distinct from `Meta.search_fields` (basic OR'd `icontains`); this is the ranked / weighted / similarity full-text surface. Planned; gated on `TODO-BETA-047-0.1.2` (basic search lands first) and shares `DONE-027-0.0.8`'s filter-argument-factory machinery.

#### Dependencies

- `DONE-027-0.0.8` - Filtering subsystem
- `TODO-BETA-047-0.1.2` - `Meta.search_fields` support

#### Scope

- Cookbook anchor: `django_graphene_filters/filters.py` ships `AnnotatedFilter` -> `SearchQueryFilter` / `SearchRankFilter` / `TrigramFilter`; `django_graphene_filters/input_types.py` ships the paired `SearchQueryFilterInputType` / `SearchRankFilterInputType` / `TrigramFilterInputType`. Port the four filter classes plus their input shapes onto the Strawberry side.
- `AnnotatedFilter` base: annotate the queryset with a computed column (`SearchVector` / `SearchRank` / `TrigramSimilarity`) under a generated alias, then filter on that alias. The Strawberry-side annotation derives at materialization via the existing `convert_filter_to_input_annotation` path rather than a Graphene `input_type` constructor arg.
- `SearchQueryFilter`: `SearchVector` + `SearchQuery` full-text match with configurable search config, vector weights, and `search_type` (plain / phrase / raw / websearch).
- `SearchRankFilter`: `SearchRank` weighting with `weights` / `cover_density` / `normalization` options.
- `TrigramFilter`: `pg_trgm` `TrigramSimilarity` / `TrigramWordSimilarity` with a `kind` selector and a similarity threshold.
- Postgres-only: degrade with a clear `ConfigurationError` (or skip the filter) on non-Postgres backends; never emit a malformed query on SQLite.
- Prefix-shortcut operators (parity watch-item, carried over from `docs/feedback.md`): `django_graphene_filters` also exposes single-character search shortcut operators (e.g. `^ = @ $`) over the full-text surface. This card describes the `SearchQuery` / `SearchRank` / `Trigram` filter classes but not the shortcut syntax — the spec must decide whether the shortcut operators are part of the ported surface or are intentionally left out.

#### Definition of done

- [ ] Add `docs/spec-pg_full_text_search.md`.
- [ ] `AnnotatedFilter` + `SearchQueryFilter` / `SearchRankFilter` / `TrigramFilter` ship in `django_strawberry_framework/filters/` and reuse the shared DRF-style Meta surface + argument-factory machinery from `DONE-027-0.0.8`.
- [ ] Paired input types (`SearchQueryFilterInputType` / `SearchRankFilterInputType` / `TrigramFilterInputType`) generate with stable class-derived names.
- [ ] Backend guard: a clear typed error on non-Postgres backends rather than a malformed query.
- [ ] Tests under `tests/filters/test_pg_full_text.py` covering each filter, the weight/config options, and the non-Postgres guard.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` against a Postgres-backed model (gated on a Postgres test backend; skipped under the default SQLite run).

#### Files likely touched

- `django_strawberry_framework/filters/base.py` (new filter classes)
- `django_strawberry_framework/filters/inputs.py` (new input types)
- `tests/filters/test_pg_full_text.py` (new)
- `examples/fakeshop/test_query/` (Postgres-gated HTTP coverage)

#### Why it matters

- The Postgres full-text family is part of django-graphene-filters' shipped filter surface; recreating it is in scope for cookbook parity (`GOAL.md` "Working reference").
- `Meta.search_fields` (`TODO-BETA-047-0.1.2`) only covers OR'd `icontains`; ranked / weighted / similarity search is a distinct capability the cookbook ships and basic search does not.

#### Dependencies

- `TODO-BETA-047-0.1.2` (`Meta.search_fields`) -- basic search lands first; this is the advanced full-text surface.
- `DONE-027-0.0.8` (Filtering subsystem) -- the filter-argument-factory machinery is shared.

#### Other

- Postgres-only filter family (`SearchQuery` / `SearchRank` / `Trigram`) layered on `django.contrib.postgres.search`; cookbook port of `django_graphene_filters` `filters.py` + `input_types.py`. Spec + tests + Postgres-gated HTTP coverage.
- The only cookbook filter-surface gap found in the 0.0.7 DRY-cycle kwarg-parity audit; every other `django_graphene_filters` filter primitive is already shipped in `DONE-027-0.0.8`.

#### Card references

- Dependency: `TODO-BETA-047-0.1.2` (`Meta.search_fields`) -- basic search lands first; this is the advanced full-text surface. -> `TODO-BETA-047-0.1.2` - `Meta.search_fields` support
- Dependency: Strawberry analogue of django-graphene-filters' Postgres full-text search family. The cookbook ships `AnnotatedFilter` (base) plus `SearchQueryFilter`, `SearchRankFilter`, and `TrigramFilter` in `django_graphene_filters/filters.py`, with matching `SearchQueryFilterInputType` / `SearchRankFilterInputType` / `TrigramFilterInputType` input shapes in `django_graphene_filters/input_types.py`. These add Postgres-only `searchQuery` / `searchRank` / `trigram` filter inputs to FilterSets on Postgres-backed models, layered on `django.contrib.postgres.search`. Distinct from `Meta.search_fields` (basic OR'd `icontains`); this is the ranked / weighted / similarity full-text surface. Planned; gated on `TODO-BETA-047-0.1.2` (basic search lands first) and shares `DONE-027-0.0.8`'s filter-argument-factory machinery. -> `TODO-BETA-047-0.1.2` - `Meta.search_fields` support
- Related: `Meta.search_fields` (`TODO-BETA-047-0.1.2`) only covers OR'd `icontains`; ranked / weighted / similarity search is a distinct capability the cookbook ships and basic search does not. -> `TODO-BETA-047-0.1.2` - `Meta.search_fields` support
- Dependency: `DONE-027-0.0.8` (Filtering subsystem) -- the filter-argument-factory machinery is shared. -> `DONE-027-0.0.8` - Filtering subsystem
- Dependency: Strawberry analogue of django-graphene-filters' Postgres full-text search family. The cookbook ships `AnnotatedFilter` (base) plus `SearchQueryFilter`, `SearchRankFilter`, and `TrigramFilter` in `django_graphene_filters/filters.py`, with matching `SearchQueryFilterInputType` / `SearchRankFilterInputType` / `TrigramFilterInputType` input shapes in `django_graphene_filters/input_types.py`. These add Postgres-only `searchQuery` / `searchRank` / `trigram` filter inputs to FilterSets on Postgres-backed models, layered on `django.contrib.postgres.search`. Distinct from `Meta.search_fields` (basic OR'd `icontains`); this is the ranked / weighted / similarity full-text surface. Planned; gated on `TODO-BETA-047-0.1.2` (basic search lands first) and shares `DONE-027-0.0.8`'s filter-argument-factory machinery. -> `DONE-027-0.0.8` - Filtering subsystem
- Related: The only cookbook filter-surface gap found in the 0.0.7 DRY-cycle kwarg-parity audit; every other `django_graphene_filters` filter primitive is already shipped in `DONE-027-0.0.8`. -> `DONE-027-0.0.8` - Filtering subsystem

<a id="aggregation_subsystem"></a>
### [TODO-BETA-049-0.1.3 - Aggregation subsystem](KANBAN.html#aggregation_subsystem)

- Priority: Medium-high
- Severity: Major
- Status: Planned
- Relative size: L
- Labels: `aggregations`, `filters`, `layer-3`, `public-api`

#### Predicted files

- `django_strawberry_framework/aggregates/` (planned)

#### Planning note

Strawberry port of graphene-django's `AdvancedAggregateSet` — declarative per-type aggregation via `Meta.aggregate_class`. Mirrors the shipped Filtering / in-flight Ordering architecture (six-layer lazy-resolution pipeline; finalizer phase-2.5 binding; per-module input-class namespace) but emits `strawberry.type` output types (not input) and adds a sync/async `compute` / `acompute` split. The cookbook shape: `AggregateSet` subclasses declare `Meta.fields = {"name": ["count", "min", "max", "mode", "uniques"], ...}`, per-stat `check_<field>_<statname>_permission` gates, custom-stat `compute_<field>_<statname>` methods registered via `Meta.custom_stats = {...}`, `RelatedAggregate` for cross-relation traversal, and a `get_child_queryset` cascade hook for related aggregates.

#### Scope

- `Sum`, `Count`, `Avg`, `Min`, `Max`, `GroupBy`
- `AggregateSet`
- GraphQL argument/result factories
- `Meta.aggregate_class` promotion
- Cookbook anchor: graphene-django's `recipes/aggregates.py` declares `class ObjectTypeAggregate(AggregateSet)` with `Meta.fields = {"name": ["count", "min", "max", "mode", "uniques"], "description": ["count", "min", "max"]}` and `Meta.custom_stats = {"type_breakdown": str}` paired with a `compute_body_type_type_breakdown(self, queryset) -> str` method. The Strawberry port carries this shape verbatim with `OrderSet` → `AggregateSet` substitution and the `compute` / `acompute` sync/async split.
- Built-in stat surface: `count`, `min`, `max`, `mode`, `uniques`, plus the Django aggregate primitives `Sum`, `Count`, `Avg`, `Min`, `Max`, `GroupBy`. The cookbook ships every one as a per-field option on `Meta.fields`; this card pins the same surface.
- `RelatedAggregate("TargetAggregate", field_name="...")` for relation-traversed aggregates (e.g. `celestial_bodies = RelatedAggregate("CelestialBodyAggregate", field_name="galaxy")` on a `GalaxyAggregate`). Accepts a class reference, an absolute import path, or an unqualified name for circular references — the same lazy-resolution contract `RelatedFilter` and `RelatedOrder` ship.
- `Meta.custom_stats = {"<statname>": <return_type>}` declares consumer-defined stats; the framework expects a paired `compute_<field>_<statname>(self, queryset)` method that returns a value matching the declared type. Cookbook example: `Meta.custom_stats = {"type_breakdown": str}` paired with `compute_body_type_type_breakdown(self, queryset) -> str` returning a comma-separated `KEY=count` breakdown.
- Per-stat permission: `check_<field>_<statname>_permission(self, request)` gates a specific (field, stat) pair (cookbook example: `check_name_uniques_permission` raises for non-staff so non-staff cannot see the unique-name distribution while still seeing `count` / `min` / `max`). Mirrors the per-field permission gate in `FilterSet` / `OrderSet` but keyed on the (field, stat) tuple, not just the field.
- `get_child_queryset(self, rel_name, rel_agg)` cascade hook on `AggregateSet` lets a parent aggregate enforce a cascade rule on its children (cookbook example: a shared `_private_aware_child_qs` that filters out `is_private=True` rows when traversing through a `RelatedAggregate`). Composes with `apply_cascade_permissions` (`DONE-034-0.0.10`).
- Sync / async `compute(self, info, queryset) -> <Output>` and `async def acompute(self, info, queryset) -> <Output>` — same dual-shape contract `FilterSet.apply_sync` / `apply_async` ships. Selection-set-aware: only the aggregate output fields the GraphQL query actually selects are computed; the optimizer plan-cache infrastructure drives the selected-fields detection so a 20-stat aggregate output type does not eagerly compute all 20 when the consumer asked for 3.
- Output-type emission: each `AggregateSet` emits a `@strawberry.type`-decorated output class named `<AggregateSet>OutputType` (e.g. `ObjectTypeAggregateOutputType`) materialized in a per-module `aggregates.outputs` namespace — disjoint from `filters.inputs` / `orders.inputs`, mirroring the per-module namespace pattern.
- Config knobs (parity watch-item, carried over from `docs/feedback.md`): DGF's aggregate subsystem ships tunable safety limits and an async opt-in as settings — `AGGREGATE_MAX_VALUES`, `AGGREGATE_MAX_UNIQUES`, and `ASYNC_AGGREGATES` (`django_graphene_filters/conf.py`). This card captures the `compute` / `acompute` split and the stat surface but not these config knobs; the spec must confirm they are in scope when `spec-aggregates` is authored, or consciously drop them.

#### Definition of done

- [ ] Add `docs/spec-aggregates.md`.
- [ ] Add `django_strawberry_framework/aggregates/`.
- [ ] Add mirrored `tests/aggregates/`.
- [ ] Promote `Meta.aggregate_class` only when aggregation is applied end-to-end.
- [ ] Decide result type naming and grouping semantics.
- [ ] Validate generated queryset aggregation paths.
- [ ] Keep aggregation declarations composable with filters, ordering, and connection field behavior.
- [ ] Add `docs/spec-aggregates.md` covering: `AggregateSet` / `RelatedAggregate` class shape; the `count`/`min`/`max`/`mode`/`uniques` built-in stat surface; `Meta.custom_stats` + `compute_<field>_<statname>` contract; per-stat `check_<field>_<statname>_permission` gating; `get_child_queryset` cascade hook; sync/async `compute` / `acompute` split; selection-set-aware computation; output-type emission and the `aggregates.outputs` namespace.
- [ ] Live HTTP coverage in `examples/fakeshop/test_query/` exercises a real cookbook-shaped aggregate: a parent type with `RelatedAggregate` traversal, a custom stat, a per-stat permission gate, and a selection-set test confirming only the selected stats are computed.
- [ ] Composability with the shipped sidecars: filter narrows first → order is a no-op for aggregate output → aggregate computes against the filtered + cascade-permissioned queryset. Pinned by a single test that exercises all three at once.

#### Foundation-slice seam

- `DjangoTypeDefinition.aggregate_class` is the populated slot.
- The cookbook reference (`AdvancedAggregateSet.compute` / `acompute`) splits sync and async paths; this lines up with the existing async-resolver support in the optimizer.
- Selection-set-aware aggregate computation will reuse the optimizer plan-cache infrastructure, since the aggregate output type's selected fields drive which annotations are computed.

#### Architectural posture

- Concurrency / scatter-gather seam (design guidance carried over from `docs/feedback.md`; net-new value, **not** a DGF-parity item). The package has zero query concurrency today, partly deliberate — `relay.py::DjangoNodesField` chooses sequential awaits over `asyncio.gather`, citing Django async-ORM connection safety. Parallelism only pays for genuinely independent queries on separate connections, never naive fan-out over one shared connection/cursor. Hard constraints any gather seam must respect: (1) each thread worker opens a thread-local connection it must close (`close_old_connections`), so the sync pool is small and bounded (≈2–3), NOT `max_workers=NUM_CORES` — except the independent-DB shard case, where core-scaling is correct; (2) the `chunk_size = ceil(count / NUM_CORES)` PK-range partition is a win ONLY when the reduction runs in Python (mode / uniques / percentile / `Counter`), never for a SQL-native aggregate (`Count`/`Sum`/`Min`/`Max`/`Avg`), which adds round-trips and loses index efficiency; (3) the example project runs on SQLite (serializes), so any speedup must be benchmarked on Postgres/MySQL — the 100%-coverage suite cannot prove it under the default runner.
- Where it pays to invest — the `AggregateSet` gather seam (this card). Independent stats that cannot fold into one `.aggregate()` (mode / uniques / percentile / the `Counter`-based custom `compute_*` stats above) are each their own scan, and the PK-range partition applies to their Python reduction; DB-native stats MUST stay single-query (let SQL do it). `acompute` already implies the async seam — build the gather seam (a sync bounded-pool plus the async `acompute` path) into this card from the start rather than retrofitting it. Design it once here: it is reused by the BACKLOG `matrix_dimensions_and_measures` (item 32 — per-measure fan-out + chunked-partition reduction over the heaviest 10M-row / percentile / pivot surface; design its executor with a parallel reduce from the start) and `sharding_aware_optimizer` (item 41 — multi-shard compose over independent DBs / connections: zero GIL contention, no shared-connection hazard, per-shard count/sum/min/max compose; the one place `max_workers=NUM_CORES` is literally correct) cards.
- Async-path constraint. Every async path today wraps its sync body in `sync_to_async(..., thread_sensitive=True)` — `FilterSet.apply_async`, `OrderSet.apply_async`, `aapply_cascade_permissions`, `resolve_mutation_async` — which serializes them onto one asgiref worker. That is a deliberate connection / consumer-hook safety choice, not a bug, but it is the constraint the async `acompute` gather must design around: the gather must run genuinely independent units on their own connections and never re-enter the shared sensitive thread.
- Adjacent optimizer seams investigated (non-aggregation, recorded here so they are not lost — both marginal / deferred): (a) root-connection `totalCount ∥ page slice` — when `Meta.connection` opts into `totalCount`, the count runs serially after the slice via `count()` / `acount()` on the same filtered queryset (`connection.py::_attach_count_sync` / `_attach_count_async`); the two are independent and package-owned, but it is the smallest standalone win and marginal unless the count rivals the page cost, on a parallelizing backend only. (b) parallel independent top-level `prefetch_related` — plain to-many list / M2M siblings still issue N serial `WHERE parent_id IN (...)` scans inside Django's `prefetch_related_objects`; `OptimizationPlan.apply` returns a lazy queryset and Strawberry/Django owns materialization, so parallelizing means the package takes over materialization in the resolvers it controls (per the root-cause rule — NOT monkeypatching `prefetch_related_objects`). High risk; defer behind a Postgres benchmark.
- Ruled out, on the record: the single root list query (`list_field.py`, nothing to split); `resolve_nodes` (`relay.py`, already one `pk__in` per type — optimal within one DB, don't parallelize the single-DB case); `FilterSet` / `OrderSet` `apply_*` (queryset builders, no fan-out); the `0.0.11` mutations (single-row, single-transaction); `finalize_django_types()` (CPU/GIL-bound and contractually single-threaded); and DB-native aggregates. Do not retrofit concurrency onto shipped code without a Postgres benchmark.

#### Other

- full subsystem, parallel to Ordering: reuses `DONE-027-0.0.8`'s six-layer architecture but emits `strawberry.type` output types (not input) and adds the sync/async `compute` / `acompute` split. New `aggregates/` subpackage + `docs/spec-aggregates.md` + tests.

#### Card references

- Related: full subsystem, parallel to Ordering: reuses `DONE-027-0.0.8`'s six-layer architecture but emits `strawberry.type` output types (not input) and adds the sync/async `compute` / `acompute` split. New `aggregates/` subpackage + `docs/spec-aggregates.md` + tests. -> `DONE-027-0.0.8` - Filtering subsystem
- Related: `DONE-034-0.0.10` - Permissions subsystem

<a id="layer_3_meta_key_promotion"></a>
### [TODO-BETA-050-0.1.3 - Layer 3 Meta key promotion](KANBAN.html#layer_3_meta_key_promotion)

- Priority: Low
- Severity: Low
- Status: Planned
- Relative size: XS
- Labels: `cleanup`, `layer-3`, `public-api`

#### Other

- each Layer 3 subsystem implementation
- `filterset_class`
- `orderset_class`
- `aggregate_class`
- `fields_class`
- `search_fields`
- Do not move a key from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` until the pipeline applies it end-to-end.
- mechanical bookkeeping: move keys from `DEFERRED_META_KEYS` → `ALLOWED_META_KEYS` as each subsystem lands end-to-end. The real work lives in the subsystem cards, not here.

<a id="opt_in_node_sentinel_redaction_tier_metaredaction_mode"></a>
### [TODO-BETA-051-0.1.4 - Opt-in node-sentinel redaction tier (`Meta.redaction_mode`)](KANBAN.html#opt_in_node_sentinel_redaction_tier_metaredaction_mode)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required)
- Severity: Medium
- Status: Needs spec
- Relative size: L
- Labels: `layer-3`, `permissions`, `public-api`, `security`

#### Predicted files

- `django_strawberry_framework/permissions/` (planned)
- [`django_strawberry_framework/types/`](django_strawberry_framework/types/)

#### Planning note

Strawberry port of graphene-django's node-level sentinel redaction — the third redaction tier the package deferred in spec-034 Decision 6 (row-exclusion) and re-confirmed as a `FieldSet` Non-goal (`TODO-BETA-046`). Upstream `django_graphene_filters/object_type.py::AdvancedDjangoObjectType` exposes it as public SDL: `is_redacted = graphene.Boolean(...)` (`:137`), `resolve_is_redacted` (`:151`), `_make_sentinel` (`:200`), and a `get_node` (`:251`) that returns a `pk=0` sentinel in place of a hidden row so a non-null FK to a hidden target still resolves. This card recreates that surface behind an explicit per-`DjangoType` opt-in so a django-graphene-filters consumer relying on `isRedacted` / sentinel masking can port verbatim, without disturbing the default row-narrowing model.

#### Dependencies

- `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)
- `DONE-034-0.0.10` - Permissions subsystem

#### Scope

- Opt-in switch: introduce `Meta.redaction_mode` on `DjangoType` with `"exclude"` (default — the shipped row-narrowing behavior, unchanged) and `"sentinel"` (this tier). The two are mutually exclusive per type; the spec decides whether they may be mixed across a relation chain. The `"exclude"` default leaves every existing schema byte-for-byte unaffected.
- Sentinel chain: in `"sentinel"` mode, a parent row that references a hidden non-null target yields a `pk=0` sentinel object (a `_make_sentinel` analog) instead of excluding the parent row, so the non-null FK still resolves — matching upstream's existence-preserving semantics.
- SDL surface: expose `isRedacted: Boolean` on types in `"sentinel"` mode, resolving `True` for sentinel instances and `False` otherwise (the upstream `resolve_is_redacted` contract).
- Node resolution: override the Relay `get_node` seam (shipped in `DONE-032-0.0.9`) so resolving a hidden id yields the sentinel in `"sentinel"` mode rather than `None`.
- Reconcile with the cascade: in `"sentinel"` mode the masked relation targets must surface as sentinels rather than being narrowed out by `apply_cascade_permissions` (`DONE-034-0.0.10`). The spec resolves the tension — likely: the cascade narrows top-level rows as it does today, and sentinels appear only for non-null relation targets of rows that already survived the cascade. This is the core design decision.
- Existence-leak posture: state the trade-off explicitly — sentinel masking re-introduces the existence signal that row-exclusion (spec-034 Decision 6) was chosen to avoid. The opt-in default keeps the safe behavior; choosing `"sentinel"` is a conscious consumer acceptance of the leak in exchange for django-graphene-filters parity.

#### Definition of done

- [ ] Add `docs/spec-node-sentinel.md` covering the `Meta.redaction_mode` switch, sentinel-chain semantics, the `isRedacted` SDL contract, the `get_node` override, and reconciliation with `apply_cascade_permissions`; state the existence-leak trade-off and why the tier is opt-in.
- [ ] Implement the sentinel-row factory and node-resolution hook (extending the `permissions/` surface) plus the `isRedacted` field and `Meta.redaction_mode` wiring on `DjangoType`.
- [ ] `Meta.redaction_mode` defaults to `"exclude"`; all existing schemas and tests stay unchanged under the default. The `"sentinel"` machinery is wired only when the mode is set.
- [ ] Tests mirror the source one-to-one; live HTTP coverage exercises a hidden non-null FK target resolving to a `pk=0` sentinel with `isRedacted = true`, a normal row reading `isRedacted = false`, and `get_node` on a hidden id returning the sentinel in `"sentinel"` mode vs `null` in `"exclude"` mode.
- [ ] Composability tests: `"sentinel"` mode + `apply_cascade_permissions` — the top-level cascade still narrows rows; sentinels appear only for relation targets of surviving rows (no row resurrection, no double counting).
- [x] Amend the `FieldSet` (`TODO-BETA-046`) Architectural-posture note so its node-sentinel "Non-goal" cross-references this card as the realized opt-in tier.

#### Verified in upstream

- ⚛️ `graphene_django` — `django_graphene_filters/object_type.py::AdvancedDjangoObjectType` exposes node-sentinel redaction as public SDL: `is_redacted = graphene.Boolean(...)` (`:137`), `resolve_is_redacted` (`:151`), `_make_sentinel` (`:200`), and a `get_node` (`:251`) that returns a `pk=0` sentinel in place of a hidden non-null FK target. This card ports that surface behind an opt-in.

#### Architectural posture

- This card is the explicit, opt-in reversal of spec-034 Decision 6. The default stays row-exclusion — the existence-leak-free model; this tier exists only so the one public django-graphene-filters behavior with no analog (`isRedacted` / sentinel FK masking) is portable for consumers who explicitly choose it. It does not become the default and does not weaken the cascade for `"exclude"` schemas.

#### Why it matters

- Closes the single remaining django-graphene-filters public-surface gap recorded in `docs/feedback.md` (finding P2): node-sentinel redaction was the only public upstream behavior with no equivalent and no card. This converts a buried non-goal into a tracked, opt-in parity feature.
- Lets a graphene-django consumer relying on `isRedacted` / sentinel FK masking migrate verbatim instead of re-architecting around row-exclusion.

#### Dependencies

- `DONE-034-0.0.10` (Permissions subsystem) — extends the `apply_cascade_permissions` / `get_queryset` cascade; this tier reconciles sentinels with cascade narrowing.
- `DONE-032-0.0.9` (Full Relay story) — overrides the shipped `get_node` node-resolution seam.

#### Card references

- Dependency: `DONE-034-0.0.10` (Permissions subsystem) — extends the `apply_cascade_permissions` / `get_queryset` cascade; this tier reconciles sentinels with cascade narrowing. -> `DONE-034-0.0.10` - Permissions subsystem
- Dependency: `DONE-032-0.0.9` (Full Relay story) — overrides the shipped `get_node` node-resolution seam. -> `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)
- Related: Amends the `FieldSet` node-sentinel Non-goal note (`TODO-BETA-046`) — this card is the realized opt-in tier that note defers to. -> `TODO-BETA-046-0.1.1` - `FieldSet`

<a id="stable_choice_enum_naming_override"></a>
### [TODO-BETA-052-0.1.4 - Stable choice enum naming override](KANBAN.html#stable_choice_enum_naming_override)

- Priority: Low-medium
- Severity: Medium
- Status: Planned
- Relative size: S
- Labels: `choice-enums`, `public-api`, `schema`, `stable-api`

#### Predicted files

- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`tests/types/test_converters.py`](tests/types/test_converters.py)

#### Planning note

planned

#### Definition of done

- [ ] New or amended spec documents the override key and ambiguity behavior.
- [ ] `_validate_meta` accepts the key only when the pipeline applies it end-to-end.
- [ ] `convert_choices_to_enum()` uses the explicit name when provided.
- [ ] Tests cover explicit naming, cache reuse, duplicate/conflicting names, and default first-reader behavior.

#### Files likely touched

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/registry.py`
- `tests/types/test_converters.py`

#### Other

- bounded override surface (`Meta.choice_enum_names`) preserving `(model, field)` enum reuse; touches `base.py` / `converters.py` / `registry.py` + tests.
- Choice fields generate Strawberry enums and cache them by `(model, field_name)`.
- The first `DjangoType` to read a choice column wins the generated enum's GraphQL name.
- This is deterministic for a fixed import order but still makes schema naming dependent on which type imports first.
- Add a stable override surface such as `Meta.choice_enum_names = {"status": "ItemStatusEnum"}`.
- Decide whether this belongs in the consumer-overrides spec or a small choice-enum follow-up spec.
- Preserve enum reuse by `(model, field_name)` while making the published schema name explicit when consumers need it.

<a id="fakeshop_graphql_schema_activation"></a>
### [TODO-BETA-053-0.1.5 - Fakeshop GraphQL schema activation](KANBAN.html#fakeshop_graphql_schema_activation)

- Priority: Medium
- Severity: Medium
- Status: Planned
- Relative size: S
- Labels: `example-app`, `graphql-api`, `relay`, `schema`

#### Planning note

blocked on `DONE-032-0.0.9` (Relay decisions) and `TODO-BETA-050-0.1.3` (Layer 3 Meta key promotion).

#### Dependencies

- `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)
- `TODO-BETA-050-0.1.3` - Layer 3 Meta key promotion

#### Definition of done

- [ ] Uncomment only the portions whose dependencies have shipped.
- [ ] Keep unshipped subsystem lines commented until their specs land.
- [ ] Move or defer `search_fields` before uncommenting because it is currently a rejected Meta key.
- [ ] Add in-process schema tests under `examples/fakeshop/tests/`.
- [ ] Add live `/graphql/` tests under `examples/fakeshop/test_query/` only when testing the HTTP endpoint.

#### Other

- example-wiring card: uncomment the product-catalog schema portions whose dependencies have shipped; in-process + live HTTP tests. Gated on the Layer-3 subsystems, not heavy itself.
- `examples/fakeshop/apps/products/schema.py` exposes a placeholder `hello` field for the product catalog.
- The aspirational schema block depends on `DjangoConnectionField`, Relay interfaces, filters, orders, aggregates, fieldsets, and permissions.

#### Card references

- Blocked by: blocked on `DONE-032-0.0.9` (Relay decisions) and `TODO-BETA-050-0.1.3` (Layer 3 Meta key promotion). -> `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)
- Blocked by: blocked on `DONE-032-0.0.9` (Relay decisions) and `TODO-BETA-050-0.1.3` (Layer 3 Meta key promotion). -> `TODO-BETA-050-0.1.3` - Layer 3 Meta key promotion

<a id="product_catalog_layer_3_http_graphql_tests"></a>
### [TODO-BETA-054-0.1.5 - Product-catalog Layer 3 HTTP GraphQL tests](KANBAN.html#product_catalog_layer_3_http_graphql_tests)

- Priority: Medium
- Severity: Medium
- Status: Planned
- Relative size: S
- Labels: `example-app`, `graphql-api`, `layer-3`, `tests`

#### Other

- activating the product-catalog fakeshop GraphQL schema
- connection/query fields and other Layer 3 public surfaces
- The library app already has live `/graphql/` acceptance tests under `examples/fakeshop/test_query/`.
- Future product-catalog HTTP tests should use the same placement and schema-reload pattern.
- In-process `schema.execute_sync` tests still go under `examples/fakeshop/tests/`.
- bounded test suite: live `/graphql/` acceptance tests for the activated product-catalog schema, reusing the library app's placement + schema-reload pattern.

<a id="mutation_transactions_and_idempotency"></a>
### [TODO-BETA-055-0.1.6 - Mutation transactions and idempotency](KANBAN.html#mutation_transactions_and_idempotency)

- Priority: High
- Severity: Major
- Status: Needs spec
- Relative size: S
- Labels: `mutations`, `performance`, `security`

#### Predicted files

- [`django_strawberry_framework/mutations/`](django_strawberry_framework/mutations/)
- [`examples/fakeshop/test_query/`](examples/fakeshop/test_query/)
- [`tests/mutations/`](tests/mutations/)

#### Planning note

Promoted from BACKLOG.md item 23 as a Beta differentiator after the core mutation surface exists and before migration/adoption docs lock the pre-1.0 story.

#### Dependencies

- `DONE-036-0.0.11` - Mutations + auto-generated Input types

#### Scope

- Add mutation-level `Meta.atomic = True` so generated create/update/delete mutation resolvers can run inside `transaction.atomic()` without every consumer hand-wrapping the resolver.
- Add `Meta.idempotency_key = "request_id"` and `Meta.idempotency_ttl = 86400` support backed by `django.core.cache`, returning the first successful response for duplicate keys inside the TTL.
- Cache only successful atomic-mode responses; validation, permission, and database failures roll back and skip the idempotency write so client retries naturally re-execute.
- Keep the surface DRF-shaped and mutation-local: declaration lives on each `DjangoMutation.Meta`, with safe defaults and no global setting required.

#### Definition of done

- [ ] New or amended mutation spec documents the atomic/idempotency Meta keys, cache-key shape, TTL behavior, retry semantics, and failure rollback rules.
- [ ] Implementation wraps the real generated mutation execution path in `transaction.atomic()` when enabled and leaves non-atomic mutations behavior-compatible.
- [ ] Idempotency cache entries are scoped by mutation class, key value, authenticated principal or anonymous scope, and operation arguments so unrelated calls do not collide.
- [ ] Tests cover successful replay, validation failure retry, exception rollback, TTL expiration, cache backend errors failing loudly, and sync/async mutation paths where supported.
- [ ] Live `/graphql/` coverage exercises a real fakeshop mutation twice with the same idempotency key and proves the second response does not double-write.
- [ ] Remove the `xfail(strict=True)` marker on `test_update_does_not_commit_when_response_completion_fails` in `examples/fakeshop/test_query/test_mutation_atomicity.py` once this card lands: that committed regression pins that a mutation whose GraphQL response completion fails after the write has committed - e.g. a corrupt related non-nullable field hydrates to `None` and trips 'Cannot return null for non-nullable field' - must roll back rather than commit a partial change. It `xfail`s today because the resolver's `transaction.atomic()` ends when the resolver returns, before graphql-core completes the payload; this card's fix (extending the transaction boundary to span response completion) makes it XPASS, and `strict=True` then turns the suite red until the marker is removed.

#### Foundation-slice seam

- `DONE-036-0.0.11` owns the base `DjangoMutation` class, generated input types, and shared `errors: list[FieldError]` envelope; this card layers safety semantics onto that lifecycle instead of inventing a separate mutation primitive.
- DRF serializer and Form-based mutation cards inherit the same atomic/idempotency implementation through the shared mutation base once their adapters land.

#### Files likely touched

- `django_strawberry_framework/mutations/` or the mutation package introduced by `DONE-036-0.0.11`.
- `tests/mutations/` plus live fakeshop GraphQL mutation tests.
- `docs/GLOSSARY.md` and the mutation spec when the feature ships.

#### Why it matters

- Stripe-style idempotency is production table stakes for payment, order, and inventory writes, but Django GraphQL packages leave it to each app.
- Combining `transaction.atomic()` with keyed response replay makes generated mutations safe by default for retries, client timeouts, and duplicate submissions.

#### Dependencies

- Builds on the core DjangoMutation lifecycle and generated input envelope from TODO-ALPHA-036.

#### Other

- Original backlog score: Realistic 10/10, Impact 8/10, Difficulty 3/10; bang-for-buck score 26.67.
- Neither graphene-django nor strawberry-graphql-django ships mutation idempotency; this is a differentiator rather than an upstream-parity card.

#### Card references

- Dependency: Builds on the core DjangoMutation lifecycle and generated input envelope from TODO-ALPHA-036. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="migration_and_adoption_guides"></a>
### [TODO-BETA-056-0.1.6 - Migration and adoption guides](KANBAN.html#migration_and_adoption_guides)

- Priority: Medium
- Severity: Medium
- Status: Planned
- Relative size: M
- Labels: `docs`, `guides`, `public-api`

#### Planning note

planned

#### Definition of done

- [ ] New docs are added for the two major migration paths.
- [ ] README and `GLOSSARY.md` link to the migration docs.
- [ ] Guides distinguish shipped migration steps from planned Layer 3 migration targets.

#### Files likely touched

- future migration docs under `docs/`
- `docs/README.md`
- `docs/GLOSSARY.md`

#### Other

- docs-only but substantial: two full migration guides (graphene-django → and strawberry-graphql-django →) plus DRF / django-filter mapping notes, with README / GLOSSARY links. No code.
- The package is intentionally shaped for teams coming from `django-filter`, DRF, `graphene-django`, and `strawberry-graphql-django`.
- The feature docs explain the positioning, but there are no dedicated migration guides yet.
- Add ability to set dsf settings to cap the number of schema hookups per model and error if it is more
- Add a `graphene-django` migration guide covering `DjangoObjectType` to `DjangoType`, enum/field conversion differences, query optimizations, and Relay caveats.
- Add a `strawberry-graphql-django` migration guide covering decorator-to-`Meta` translation, optimizer differences, `get_queryset`, and optimizer hints.
- Add concise notes for DRF / django-filter users mapping serializers/filtersets/orders into the planned Layer 3 surfaces.

<a id="adversarial_non_live_test_suite_try_to_break_it_not_just_cover_lines"></a>
### [TODO-BETA-057-0.1.7 - Adversarial non-live test suite (try to break it, not just cover lines)](KANBAN.html#adversarial_non_live_test_suite_try_to_break_it_not_just_cover_lines)

- Priority: Medium-high
- Severity: Medium
- Status: Planned
- Relative size: M
- Labels: `adversarial-testing`, `hardening`, `tests`

#### Predicted files

- [`examples/fakeshop/test_query/README.md`](examples/fakeshop/test_query/README.md)
- [`tests/`](tests/)

#### Planning note

planned

#### Definition of done

- [ ] A dedicated adversarial suite under `tests/` exercises the categories above; every hostile input fails LOUDLY with a typed error rather than crashing.
- [ ] Root `tests/` holds only genuinely-unreachable-from-live cases plus the new adversarial ones; any remaining live-reachable duplicates are pruned (per `examples/fakeshop/test_query/README.md`).
- [ ] Coverage stays at 100% without relying on the pruned duplicates.

#### Files likely touched

- new adversarial test modules under `tests/`
- `examples/fakeshop/test_query/README.md` (cross-reference the adversarial-vs-unreachable split)

#### Why it matters

- `fail_under = 100` proves every LINE executes, not that the code is CORRECT under abuse. The failures that matter — deeply nested logic trees, malformed / wrong-`type_name` GlobalIDs, cyclic `RelatedFilter` graphs, conflicting multi-owner reuse, UNSET/None permutations, oversized `Meta.fields = "__all__"` expansions, unicode / null-byte / oversized values — are exactly the ones a happy-path live query never exercises.

#### Other

- An in-process `tests/` (NON-`/graphql/`) hardening pass whose goal is to BREAK the framework, not to earn line coverage. Live-reachable coverage already lives in `examples/fakeshop/test_query/` per its README rule; the root `tests/` tree is reserved for cases a live query cannot reach — fill it with hostile / pathological inputs rather than coverage duplicates.
- Root `tests/` historically mixed genuinely-unreachable-from-live cases with some that merely duplicated coverage already earned by the live `test_query/` suites (a first prune of redundant filter unit tests landed alongside `DONE-027-0.0.8`).
- There is no deliberate "try to break it" suite; adversarial inputs are covered only incidentally.
- Property-based / fuzz-style tests (e.g. Hypothesis) for the filter input normalizer, GlobalID decode/validate, and `Meta.fields = "__all__"` expansion.
- Pathological structure: logic-tree nesting past `_MAX_LOGIC_DEPTH`, cyclic / self-referential `RelatedFilter` graphs, conflicting multi-owner reuse, proxy / MTI model mixing.
- Hostile wire values: bad-base64 / wrong-`type_name` GlobalIDs, oversized `in` lists, unicode / emoji / null bytes, `strawberry.UNSET` / `None` across every operator-bag slot.
- Scale / resource: very large `"__all__"` field sets and many-relation BFS; assert every failure surfaces as `ConfigurationError` / `GraphQLError` (never a bare traceback) and finalize stays bounded.
- Extend the same philosophy to the future order / aggregate / fieldset subsystems as they land.

#### Card references

- Related: Root `tests/` historically mixed genuinely-unreachable-from-live cases with some that merely duplicated coverage already earned by the live `test_query/` suites (a first prune of redundant filter unit tests landed alongside `DONE-027-0.0.8`). -> `DONE-027-0.0.8` - Filtering subsystem

<a id="optimizer_explain_mode"></a>
### [TODO-BETA-058-0.1.7 - Optimizer explain mode](KANBAN.html#optimizer_explain_mode)

- Priority: High
- Severity: Medium
- Status: Needs spec
- Relative size: S
- Labels: `debugging`, `developer-tools`, `graphql-api`, `optimizer`, `performance`, `query-planning`

#### Predicted files

- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`examples/fakeshop/test_query/`](examples/fakeshop/test_query/)
- [`tests/optimizer/`](tests/optimizer/)

#### Planning note

Promoted from BACKLOG.md item 7 as a pre-1.0 differentiator: expose the optimizer plan already stashed on the GraphQL context as an opt-in response-extension payload so consumers can see exactly what the Django ORM optimizer planned for a request.

#### Scope

- Add an opt-in Strawberry response extension for optimizer explain output, exposed through the GraphQL response `extensions` map under a stable package-owned key.
- Serialize the existing `info.context.dst_optimizer_plan` data into a JSON-safe payload instead of re-planning the query.
- Include the ORM planning facts developers need to debug performance: `select_related`, `prefetch_related` / `Prefetch` chains, `only()` projection, optimizer hints, FK-id elisions, and strictness decisions where available.
- Provide a request-level activation surface such as a header or context flag; keep explain output off by default.
- Guarantee explain mode is observational only: enabling it must not change SQL planning, resolver behavior, GraphQL data shape, or query results.

#### Definition of done

- [ ] A new or amended spec documents the response-extension key, toggle surface, payload shape, privacy boundaries, and compatibility contract.
- [ ] Implementation reuses the existing optimizer plan metadata and does not duplicate the optimizer walker.
- [ ] Tests cover disabled-by-default behavior, enabled response-extension output, JSON-serializable payload shape, and no regression in normal query results.
- [ ] Live `/graphql/` coverage exercises a real fakeshop query and verifies the response carries normal `data` plus the explain extension only when requested.
- [ ] Documentation surfaces the feature as planned or shipped in `docs/GLOSSARY.md`, `docs/README.md`, and `KANBAN.md` as appropriate for the shipping slice.

#### Foundation-slice seam

- `DjangoOptimizerExtension` already stores the computed plan on `info.context.dst_optimizer_plan`; this card promotes that internal diagnostic seam into a documented consumer-facing debug payload.
- Pairs naturally with the backlog's query-time optimizer disable idea, but does not depend on it.

#### Files likely touched

- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/plans.py` or a new small explain serializer module if the payload needs normalization
- `tests/optimizer/`
- `examples/fakeshop/test_query/`
- `docs/GLOSSARY.md` and related standing docs when the feature ships

#### Why it matters

- This is GraphiQL-grade visibility for the Django ORM half of GraphQL requests. Consumers can answer `what did the optimizer do for this query?` without reading SQL logs or reverse-engineering the planner.
- Neither graphene-django nor strawberry-graphql-django ships this. It reinforces the package's optimizer-first mission at a low implementation cost.

#### Other

- Original backlog score: Realistic 10/10, Impact 8/10, Difficulty 2/10; bang-for-buck score 40.0.

<a id="configurable_filterlogic_key_namespace_filter_keyand_keyor_keynot_key"></a>
### [TODO-BETA-059-0.1.7 - Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`)](KANBAN.html#configurable_filterlogic_key_namespace_filter_keyand_keyor_keynot_key)

- Priority: Low
- Parity: ⚛️ graphene-django (Required)
- Severity: Low
- Status: Needs spec
- Relative size: M
- Labels: `config`, `filters`, `public-api`

#### Predicted files

- [`django_strawberry_framework/conf.py`](django_strawberry_framework/conf.py)
- [`django_strawberry_framework/filters/inputs.py`](django_strawberry_framework/filters/inputs.py)
- [`django_strawberry_framework/filters/sets.py`](django_strawberry_framework/filters/sets.py)
- [`django_strawberry_framework/utils/connections.py`](django_strawberry_framework/utils/connections.py)

#### Planning note

Recreate django-graphene-filters' configurable filter-tree key namespace — `DJANGO_GRAPHENE_FILTERS` `FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY` (`django_graphene_filters/conf.py:13-16`, defaults `filter`/`and`/`or`/`not`) — the one DGF config surface with no analogue (`docs/feedback.md` finding P3). The package currently hardcodes the GraphQL names (`_LOGIC_KEYS` at `filters/inputs.py:131`, `CONNECTION_FILTER_KWARG` at `utils/connections.py:41`); this card makes them settings-driven while keeping the defaults and the default SDL byte-for-byte unchanged.

#### Dependencies

- `DONE-027-0.0.8` - Filtering subsystem
- `DONE-030-0.0.9` - `DjangoConnectionField`

#### Scope

- Settings surface: extend the `DJANGO_STRAWBERRY_FRAMEWORK` namespace (`conf.py`) with `FILTER_KEY` (default `"filter"`), `AND_KEY` (`"and"`), `OR_KEY` (`"or"`), and `NOT_KEY` (`"not"`), mirroring DGF's `DJANGO_GRAPHENE_FILTERS` keys and defaults, read through the existing `Settings` accessor so a host project renames them without touching package code.
- Logic-key rework: `_LOGIC_KEYS` (`filters/inputs.py:131`) and its import-time derivatives in `filters/sets.py` (`_LOGIC_PYTHON_ATTRS`, `_LOGIC_WIRE_BY_PYTHON_ATTR`, the `:1084` loop) are frozen module constants computed at import. Make the GraphQL wire names settings-derived and resolve the import-ordering tension — likely lazy resolution at schema-build time rather than at module import — so settings declared in the host `settings.py` are honored.
- Filter argument: the connection `filter` argument name (`CONNECTION_FILTER_KWARG = "filter"`, `utils/connections.py:41`) becomes `FILTER_KEY`-driven; the connection field signature, the resolver kwarg lookup, and any `kwargs.get("filter")` sites follow.
- Python-attr vs wire-name split: keep the Python-side attribute names (`and_`/`or_`/`not_`) stable — they are language-mandated keyword escapes, not parity surface. Only the GraphQL wire names are configurable; the spec pins which layer the rename applies to.
- Default parity: with no settings set, the generated SDL is byte-for-byte unchanged (`filter`/`and`/`or`/`not`), and the `conf.py` malformed/partial-mapping coercion contract still falls back to these defaults.

#### Definition of done

- [ ] Add a spec (or amend the filtering spec) covering the four settings keys and DGF-matching defaults, the import-time → schema-build-time resolution change, the Python-attr/wire-name split, and the default-unchanged guarantee.
- [ ] `conf.py` exposes `FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY` with DGF-matching defaults via the existing `Settings` accessor.
- [ ] `_LOGIC_KEYS` / its derived structures and `CONNECTION_FILTER_KWARG` resolve from settings at schema-build time (not import time); the spec documents the exact resolution point.
- [ ] Default (no settings) generated SDL is unchanged and existing filter tests pass untouched.
- [ ] Tests mirror upstream one-to-one: a host setting renames the operator keys and the `filter` argument in generated SDL and they filter correctly end-to-end (package + live HTTP); a malformed/partial settings dict falls back to defaults per the `conf.py` coercion contract.

#### Verified in upstream

- ⚛️ `graphene_django` — `django_graphene_filters/conf.py:13-16` defines `FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY` (defaults `filter`/`and`/`or`/`not`) under the `DJANGO_GRAPHENE_FILTERS` settings dict, letting the schema author rename the filter-tree operator keys. This package hardcodes them (`filters/inputs.py:131` `_LOGIC_KEYS`, `utils/connections.py:41` `CONNECTION_FILTER_KWARG`); this card ports the rename capability behind the same kind of settings dict.

#### Architectural posture

- This recreates DGF's one filtering config surface with no analogue (`docs/feedback.md` finding P3). The fixed wire names were a deliberate simplification; this card makes them configurable behind settings while keeping the defaults — and the byte-for-byte default SDL — unchanged. The cost is moving `_LOGIC_KEYS` off the import-time fast path to a settings-resolved value; the spec pins the resolution point so import ordering stays correct. It does not change the default schema and only the GraphQL wire names are configurable — the Python attribute names stay fixed.

#### Why it matters

- Closes the last django-graphene-filters config-surface gap recorded in `docs/feedback.md` (finding P3): `DJANGO_GRAPHENE_FILTERS` `FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY` had no analogue and no card.
- Lets a django-graphene-filters consumer who renamed their filter-tree keys (e.g. to avoid clashing with an existing `filter`/`and`/`or`/`not` model field) migrate without a breaking schema rename.

#### Dependencies

- `DONE-027-0.0.8` (Filtering subsystem) — owns `_LOGIC_KEYS` and the filter-tree input-type generation whose wire names this card makes configurable.
- `DONE-030-0.0.9` (`DjangoConnectionField`) — owns the `filter` argument (`CONNECTION_FILTER_KWARG`) that `FILTER_KEY` renames.

#### Card references

- Dependency: `DONE-027-0.0.8` (Filtering subsystem) — owns `_LOGIC_KEYS` and the filter-tree input-type generation whose wire names this card makes configurable. -> `DONE-027-0.0.8` - Filtering subsystem
- Dependency: `DONE-030-0.0.9` (`DjangoConnectionField`) — owns the `filter` argument (`CONNECTION_FILTER_KWARG`) that `FILTER_KEY` renames. -> `DONE-030-0.0.9` - `DjangoConnectionField`

<a id="stable_release_api_freeze_cleanup_verification_beta_stable"></a>
### [TODO-STABLE-060-1.0.0 - Stable release (API freeze, cleanup, verification, beta → stable)](KANBAN.html#stable_release_api_freeze_cleanup_verification_beta_stable)

- Priority: Critical
- Severity: Major
- Status: Planned
- Relative size: L
- Labels: `cleanup`, `release`, `stable-api`, `tests`

#### Predicted files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`tests/base/test_init.py`](tests/base/test_init.py)

#### Planning note

planned; this is the final card in the Beta queue and gates the beta → stable milestone

#### Definition of done

- [ ] Every other Beta card (`TODO-BETA-046-0.1.1` through `TODO-BETA-056-0.1.6` plus `TODO-BETA-050-0.1.3` and `TODO-BETA-054-0.1.5`) is in `DONE`.
- [ ] API surface audit: top-level `__all__` confirmed stable; every public symbol documented; no `# experimental` markers in shipped code; no `_private` symbols accidentally referenced from docs.
- [ ] SemVer policy committed in CHANGELOG header: every release after `1.0.0` follows MAJOR / MINOR / PATCH rules strictly; pre-`0.1.0` deprecation shims removed entirely.
- [ ] Full async + sync coverage matrix validated; no `sync_to_async` workarounds remain on any resolver path.
- [ ] Security review: input-validation surfaces (mutations, filters, GlobalID decoding) audited for injection / authorization gaps.
- [ ] Version bumped to `1.0.0` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock`.
- [ ] `CHANGELOG.md` `[Unreleased]` block promoted to `## [1.0.0] - YYYY-MM-DD`. Release summary mentions the parity story (graphene-django + strawberry-graphql-django), the django-graphene-filters depth, and the SemVer policy switch.
- [ ] Final pass through `BACKLOG.md` to mark differentiators that landed and refresh the post-1.0 roadmap.
- [ ] Tag, publish to PyPI, write the 1.0 announcement.

#### Files likely touched

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`
- `BACKLOG.md`

#### Why it matters

- `1.0.0` is the API freeze. After this card lands, every public symbol — `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `finalize_django_types`, `DjangoConnectionField`, `DjangoListField`, mutation classes, filter / order / aggregate / fieldset surfaces, and the Meta key vocabulary — is bound by strict SemVer. Breaking changes from this point forward require a major bump.
- The release card is where we audit, finalize, and commit to that contract. Without a dedicated card, "1.0 is stable" becomes a soft promise spread across N patches; making it a single card means the audit happens before the version tag goes out.

#### Other

- the heaviest release card: API freeze + `__all__` audit, a security review of every input surface (mutations / filters / GlobalID decoding), full async + sync matrix, version bump to `1.0.0`, CHANGELOG, backlog refresh, tag + publish + announcement.

#### Card references

- Related: Every other Beta card (`TODO-BETA-046-0.1.1` through `TODO-BETA-056-0.1.6` plus `TODO-BETA-050-0.1.3` and `TODO-BETA-054-0.1.5`) is in `DONE`. -> `TODO-BETA-046-0.1.1` - `FieldSet`
- Related: Every other Beta card (`TODO-BETA-046-0.1.1` through `TODO-BETA-056-0.1.6` plus `TODO-BETA-050-0.1.3` and `TODO-BETA-054-0.1.5`) is in `DONE`. -> `TODO-BETA-056-0.1.6` - Migration and adoption guides
- Related: Every other Beta card (`TODO-BETA-046-0.1.1` through `TODO-BETA-056-0.1.6` plus `TODO-BETA-050-0.1.3` and `TODO-BETA-054-0.1.5`) is in `DONE`. -> `TODO-BETA-050-0.1.3` - Layer 3 Meta key promotion
- Related: Every other Beta card (`TODO-BETA-046-0.1.1` through `TODO-BETA-056-0.1.6` plus `TODO-BETA-050-0.1.3` and `TODO-BETA-054-0.1.5`) is in `DONE`. -> `TODO-BETA-054-0.1.5` - Product-catalog Layer 3 HTTP GraphQL tests

## Done

Shipped cards, newest first. Each retains its spec link, parity claims, and completion evidence; the WIP / DONE spec map indexes card to spec file.

<a id="form_based_mutations_django_forms_modelforms"></a>
### [DONE-038-0.0.12 - Form-based mutations (Django Forms / ModelForms)](KANBAN.html#form_based_mutations_django_forms_modelforms)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Severity: Major
- Status: In progress
- Relative size: L
- Labels: `forms`, `mutations`, `public-api`
- Spec: [spec-038-form_mutations-0_0_12.md](docs/SPECS/spec-038-form_mutations-0_0_12.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoFormMutation`](docs/GLOSSARY.md#djangoformmutation) | shipped (`0.0.12`) |
| [`DjangoModelFormMutation`](docs/GLOSSARY.md#djangomodelformmutation) | shipped (`0.0.12`) |
| [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) | shipped (`0.0.11`) |
| [`DjangoMutationField`](docs/GLOSSARY.md#djangomutationfield) | shipped (`0.0.11`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [`FieldError` envelope](docs/GLOSSARY.md#fielderror-envelope) | shipped (`0.0.11`) |
| [Input type generation](docs/GLOSSARY.md#input-type-generation) | shipped (`0.0.11`) |
| [`DjangoModelPermission`](docs/GLOSSARY.md#djangomodelpermission) | shipped (`0.0.11`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) | shipped |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Choice enum generation](docs/GLOSSARY.md#choice-enum-generation) | shipped (`0.0.1`) |
| [`Upload` scalar](docs/GLOSSARY.md#upload-scalar) | shipped (`0.0.11`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) | shipped (`0.0.5`) |
| [`SerializerMutation`](docs/GLOSSARY.md#serializermutation) | planned for `0.0.13` |
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | planned for `0.0.13` |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | planned for `0.0.14` |

#### Package files

- `django_strawberry_framework/forms/` (historical)
- `tests/forms/` (historical)

#### Planning note

needs spec

#### Dependencies

- `DONE-036-0.0.11` - Mutations + auto-generated Input types

#### Definition of done

- [x] Add `docs/SPECS/spec-038-form_mutations-0_0_12.md`.
- [x] Implement `django_strawberry_framework/forms/` on the DRF-style Meta surface (`Meta.form_class`, `Meta.return_field_name`, etc.) rather than graphene's `MutationOptions` pattern.
- [x] Form-field → Strawberry input mapping lives in `forms/converter.py` and reuses the scalar conversion registry where field types overlap.
- [x] Validation errors surface through the shared `errors: list[FieldError]` envelope defined in `DONE-036-0.0.11`, populated from `form.errors`.
- [x] Tests under `tests/forms/`.
- [x] Live HTTP coverage under `examples/fakeshop/test_query/` exercising both a plain `Form` mutation and a `ModelForm` mutation.

#### Files likely touched

- `django_strawberry_framework/forms/` (new)
- `tests/forms/` (new)
- `examples/fakeshop/apps/products/schema.py`

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/mutation.py` — `BaseDjangoFormMutation`, `DjangoFormMutationOptions`, `DjangoFormMutation`, `DjangoModelDjangoFormMutationOptions`, `DjangoModelFormMutation`, plus `fields_for_form(form, only_fields, exclude_fields)` helper.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/converter.py` — `convert_form_field` registry mapping Django form fields → GraphQL types.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/types.py` — `ErrorType` envelope shape.

#### Why it matters

- `graphene-django` ships `DjangoFormMutation` and `DjangoModelFormMutation`: mutation classes that consume a Django `Form` / `ModelForm` and translate field validation + `cleaned_data` into a GraphQL mutation surface. Many graphene-django consumers rely on this as their write-side abstraction because it reuses validation they already have.
- Without an equivalent, graphene-django migrants must rewrite every form-backed mutation against the lower-level mutation surface from `DONE-036-0.0.11`.

#### Dependencies

- `DONE-036-0.0.11` — general mutation infrastructure (input-type generation, mutation-field plumbing) is the foundation form mutations attach to.

#### Other

- graphene-django ships `DjangoFormMutation` / `DjangoModelFormMutation`.
- no on-board predecessor.
- new `forms/` subpackage (form-field converter + `Form`/`ModelForm` mutation classes) on the DRF-style Meta surface; reuses 036's mutation infra + shared error envelope. Spec + tests + live HTTP.

#### Card references

- Dependency: `DONE-036-0.0.11` — general mutation infrastructure (input-type generation, mutation-field plumbing) is the foundation form mutations attach to. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types
- Related: Validation errors surface through the shared `errors: list[FieldError]` envelope defined in `DONE-036-0.0.11`, populated from `form.errors`. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types
- Related: Without an equivalent, graphene-django migrants must rewrite every form-backed mutation against the lower-level mutation surface from `DONE-036-0.0.11`. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="upload_scalar_and_file_image_field_mapping"></a>
### [DONE-037-0.0.11 - Upload scalar and file / image field mapping](KANBAN.html#upload_scalar_and_file_image_field_mapping)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Shipped
- Relative size: M
- Labels: `converters`, `mutations`, `scalars`, `uploads`
- Spec: [spec-037-upload_file_image_mapping-0_0_11.md](docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Specialized scalar conversions](docs/GLOSSARY.md#specialized-scalar-conversions) | shipped (`0.0.6`) |
| [`DjangoFileType`](docs/GLOSSARY.md#djangofiletype) | shipped (`0.0.11`) |
| [`DjangoImageType`](docs/GLOSSARY.md#djangoimagetype) | shipped (`0.0.11`) |
| [`Upload` scalar](docs/GLOSSARY.md#upload-scalar) | shipped (`0.0.11`) |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |
| [`BigInt` scalar](docs/GLOSSARY.md#bigint-scalar) | shipped (`0.0.6`) |
| [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) | shipped (`0.0.11`) |
| [`DjangoMutationField`](docs/GLOSSARY.md#djangomutationfield) | shipped (`0.0.11`) |
| [Input type generation](docs/GLOSSARY.md#input-type-generation) | shipped (`0.0.11`) |
| [`FieldError` envelope](docs/GLOSSARY.md#fielderror-envelope) | shipped (`0.0.11`) |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) | shipped |
| [`Meta.nullable_overrides`](docs/GLOSSARY.md#metanullable_overrides) | shipped (`0.0.9`) |
| [`Meta.required_overrides`](docs/GLOSSARY.md#metarequired_overrides) | shipped (`0.0.9`) |
| [Scalar field override semantics](docs/GLOSSARY.md#scalar-field-override-semantics) | shipped (`0.0.6`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | planned for `0.0.14` |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |

#### Package files

- [`django_strawberry_framework/mutations/`](django_strawberry_framework/mutations/)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`tests/types/test_converters.py`](tests/types/test_converters.py)

#### Planning note

planned

#### Definition of done

- [x] Scalar conversion in `types/converters.py` returns `DjangoFileType` / `DjangoImageType` (or local equivalents) for `FileField` / `ImageField`.
- [x] Mutation input-type generation (`DONE-036-0.0.11`) maps the same fields to Strawberry's `Upload` scalar.
- [x] Synthetic-model tests cover both read and write paths.
- [x] `docs/GLOSSARY.md` documents the conversion table change.

#### Files likely touched

- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/mutations/` (input mapping)
- `tests/types/test_converters.py`

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py` — output mappings `files.FileField: DjangoFileType`, `files.ImageField: DjangoImageType`; input mappings `files.FileField: Upload`, `files.ImageField: Upload`.

#### Why it matters

- `strawberry-graphql-django` maps `FileField` / `ImageField` to `Upload` on the input side and to `DjangoFileType` / `DjangoImageType` (with `name` / `path` / `size` / `url`) on the output side. Without it, every consumer that touches user uploads has to hand-roll the mapping.

#### Other

- strawberry-graphql-django maps `FileField` / `ImageField` to `Upload` (input) and file/image output types.
- pairs with `DONE-036-0.0.11` for the write side.
- bounded converter-table addition: `FileField` / `ImageField` → file/image output types on read, `Upload` on the input side. Touches `converters.py` + mutation input mapping + tests. Pairs with `DONE-036-0.0.11`.

#### Card references

- Related: Mutation input-type generation (`DONE-036-0.0.11`) maps the same fields to Strawberry's `Upload` scalar. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types
- Related: pairs with `DONE-036-0.0.11` for the write side. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="mutations_auto_generated_input_types"></a>
### [DONE-036-0.0.11 - Mutations + auto-generated Input types](KANBAN.html#mutations_auto_generated_input_types)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: XL
- Labels: `graphql-api`, `mutations`, `permissions`, `public-api`
- Spec: [spec-036-mutations-0_0_11.md](docs/SPECS/spec-036-mutations-0_0_11.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) | shipped (`0.0.11`) |
| [Input type generation](docs/GLOSSARY.md#input-type-generation) | shipped (`0.0.11`) |
| [`FieldError` envelope](docs/GLOSSARY.md#fielderror-envelope) | shipped (`0.0.11`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) | shipped |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [Queryset diffing](docs/GLOSSARY.md#queryset-diffing) | shipped (`0.0.3`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter) | shipped (`0.0.8`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) | shipped (`0.0.5`) |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Choice enum generation](docs/GLOSSARY.md#choice-enum-generation) | shipped (`0.0.1`) |
| [Specialized scalar conversions](docs/GLOSSARY.md#specialized-scalar-conversions) | shipped (`0.0.6`) |
| [`auto`-typed annotations](docs/GLOSSARY.md#auto-typed-annotations) | shipped (`0.0.9`) |
| [`Upload` scalar](docs/GLOSSARY.md#upload-scalar) | shipped (`0.0.11`) |
| [`DjangoFileType`](docs/GLOSSARY.md#djangofiletype) | shipped (`0.0.11`) |
| [`DjangoImageType`](docs/GLOSSARY.md#djangoimagetype) | shipped (`0.0.11`) |
| [`DjangoFormMutation`](docs/GLOSSARY.md#djangoformmutation) | shipped (`0.0.12`) |
| [`DjangoModelFormMutation`](docs/GLOSSARY.md#djangomodelformmutation) | shipped (`0.0.12`) |
| [`SerializerMutation`](docs/GLOSSARY.md#serializermutation) | planned for `0.0.13` |
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | planned for `0.0.13` |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |

#### Package files

- [`django_strawberry_framework/mutations/`](django_strawberry_framework/mutations/)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`tests/mutations/`](tests/mutations/)

#### Planning note

needs spec

#### Dependencies

- `DONE-018-0.0.6` - Multiple DjangoTypes per model with `Meta.primary`
- `DONE-034-0.0.10` - Permissions subsystem

#### Definition of done

- [x] Add `docs/spec-mutations.md`.
- [x] Implement `django_strawberry_framework/mutations/` (sets, fields, resolvers, input-type generation) on the DRF-style Meta surface (`Meta.input_class`, `Meta.partial_input_class`, etc.).
- [x] Auto-generated input types respect the relation-override contract pinned in `DONE-010-0.0.4`.
- [x] Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `DONE-038-0.0.12`, `TODO-ALPHA-039-0.0.13`, and `TODO-ALPHA-040-0.0.13`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings).
- [x] Tests under `tests/mutations/`.
- [x] Live HTTP coverage under `examples/fakeshop/test_query/` exercising the products write surface.

#### Files likely touched

- `django_strawberry_framework/mutations/` (new)
- `django_strawberry_framework/types/base.py`
- `tests/mutations/` (new)
- `examples/fakeshop/apps/products/schema.py`

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/mutations/` — `mutations.py` (create/update/delete classes), `fields.py` (`DjangoMutationField`), `resolvers.py` (sync/async write resolvers), `types.py` (input-type generation).

#### Why it matters

- Mutations are the single largest unscoped gap against `strawberry-graphql-django`. Consumers migrating from strawberry-graphql-django will notice the missing write side immediately.
- `strawberry-django` exposes `create`, `update`, `delete`, custom mutations, and auto-generated `Input` / `PartialInput` types per model. These compose with permissions and the optimizer.

#### Dependencies

- `DONE-018-0.0.6` (`Meta.primary`) — explicit primary type drives mutation target resolution.
- `DONE-034-0.0.10` (permissions) — write mutations need to compose with `apply_cascade_permissions`.

#### Other

- mutations are the single largest unscoped gap vs strawberry-graphql-django (create / update / delete + auto-generated Input / PartialInput types).
- no on-board predecessor.
- `DONE-027-0.0.8`-scale. The single largest unscoped gap versus strawberry-graphql-django. New `mutations/` subpackage (sets / fields / resolvers / input-type generation) + spec + tests + live HTTP, plus the shared `errors: list[FieldError]` envelope reused by 038 / 039 / 040.

#### Card references

- Dependency: `DONE-018-0.0.6` (`Meta.primary`) — explicit primary type drives mutation target resolution. -> `DONE-018-0.0.6` - Multiple DjangoTypes per model with `Meta.primary`
- Related: Auto-generated input types respect the relation-override contract pinned in `DONE-010-0.0.4`. -> `DONE-010-0.0.4` - 0.0.4 foundation slice (definition-order independence)
- Dependency: `DONE-034-0.0.10` (permissions) — write mutations need to compose with `apply_cascade_permissions`. -> `DONE-034-0.0.10` - Permissions subsystem
- Related: Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `DONE-038-0.0.12`, `TODO-ALPHA-039-0.0.13`, and `TODO-ALPHA-040-0.0.13`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings). -> `DONE-038-0.0.12` - Form-based mutations (Django Forms / ModelForms)
- Related: Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `DONE-038-0.0.12`, `TODO-ALPHA-039-0.0.13`, and `TODO-ALPHA-040-0.0.13`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings). -> `TODO-ALPHA-039-0.0.13` - DRF serializer mutations (`SerializerMutation`)
- Related: Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `DONE-038-0.0.12`, `TODO-ALPHA-039-0.0.13`, and `TODO-ALPHA-040-0.0.13`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings). -> `TODO-ALPHA-040-0.0.13` - Auth mutations (login / logout / register)
- Related: `DONE-027-0.0.8`-scale. The single largest unscoped gap versus strawberry-graphql-django. New `mutations/` subpackage (sets / fields / resolvers / input-type generation) + spec + tests + live HTTP, plus the shared `errors: list[FieldError]` envelope reused by 038 / 039 / 040. -> `DONE-027-0.0.8` - Filtering subsystem

<a id="optimizer_robustness_hardening_upstream_comparison_guards"></a>
### [DONE-035-0.0.10 - Optimizer robustness hardening (upstream-comparison guards)](KANBAN.html#optimizer_robustness_hardening_upstream_comparison_guards)

- Priority: Medium-high
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Shipped
- Relative size: M
- Labels: `hardening`, `optimizer`, `performance`, `query-planning`
- Spec: [spec-035-optimizer_hardening-0_0_10.md](docs/SPECS/spec-035-optimizer_hardening-0_0_10.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [Queryset diffing](docs/GLOSSARY.md#queryset-diffing) | shipped (`0.0.3`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [Schema audit](docs/GLOSSARY.md#schema-audit) | shipped (`0.0.3`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.relation_shapes`](docs/GLOSSARY.md#metarelation_shapes) | shipped (`0.0.9`) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) | shipped (`0.0.3`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) | shipped (`0.0.11`) |
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | planned for `0.0.13` |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |

#### Package files

- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)
- [`tests/optimizer/test_extension.py`](tests/optimizer/test_extension.py)
- [`tests/optimizer/test_walker.py`](tests/optimizer/test_walker.py)
- [`tests/types/test_resolvers.py`](tests/types/test_resolvers.py)

#### Planning note

Source: 2026-06-11 comparative audit of `django_strawberry_framework/optimizer/` against `~/projects/strawberry-django-main/strawberry_django/optimizer.py` (1,823 lines, 36 capabilities inventoried). Three robustness gaps were verified absent in our source by direct inspection (grep + read, not inferred): no evaluated-queryset guard (zero `_result_cache` references package-wide), no operation-type gating of `.only()` (zero `OperationType` references), and no fragment `type_condition` narrowing (`type_condition` is only used as a fragment *marker* at `walker.py:845` and cloned at `extension.py:346`, never matched). Each guard exists upstream with a known mechanism and file:line anchor. The two big *performance* findings from the same audit — windowed nested-prefetch pagination and `totalCount` window-annotation reuse — are already owned by `Connection-aware optimizer planning` (WIP) and are explicitly NOT in this card. Ships in 0.0.10 because guard G2 must land before the 0.0.11 mutations cohort makes mutation root resolvers returning querysets a mainstream consumer path.

#### Dependencies

- `DONE-033-0.0.9` - Connection-aware optimizer planning

#### Scope

- G1 - evaluated-queryset guard. Today `DjangoOptimizerExtension._optimize` applies the plan to any root queryset; if the consumer's root resolver already evaluated it (a `len(qs)` guard, a `bool(qs)` branch, slicing for a log line), our `.only()` / `.select_related()` clone silently re-executes the SQL - a doubled query invisible to the consumer. Upstream guards this twice: the resolve hook only optimizes when `ret._result_cache is None` (`strawberry_django/optimizer.py:1781`) and `optimize()` re-checks `is_optimized(qs) or qs._result_cache is not None` (`optimizer.py:1628`). Implement: in `extension.py::_optimize`, AFTER the manager-to-`.all()` coercion at `extension.py:714` (a manager coercion always yields a fresh unevaluated queryset, so the guard must not fire before it) and BEFORE `diff_plan_for_queryset`, return the result unchanged when `getattr(queryset, "_result_cache", None) is not None`. Read defensively with `getattr` per the package posture pinned in `field_meta.py::_target_pk_name`.
- G1 non-goals: do NOT port upstream's `is_optimized()` flag, `CONFIG_KEY` queryset config, or the `QuerySet._clone` monkeypatch (`strawberry_django/queryset.py:50-62`) - those exist upstream because their optimizer can run at nested resolvers; our O3 root gate (`info.path.prev is None`, spec-002) already guarantees single application, so execution-state (`_result_cache`) is the only missing check.
- G2 - operation-type gating of `.only()`. We project `only_fields` onto mutation/subscription root querysets identically to queries; upstream disables `only` for non-QUERY operations (`enable_only and info.operation.operation == OperationType.QUERY`, `strawberry_django/optimizer.py:1784`, re-checked at `:1817`). Risk: a mutation resolver returning a queryset gets a selection-set-shaped `.only()`; post-mutation consumer code touching any unprojected field triggers one deferred-field refetch query per access, and `Model.save()` on a deferred instance writes only loaded fields (Django's documented deferred-save semantics) - a surprising interaction with signal handlers and downstream writes. Implement: suppress `only_fields` (keep `select_related` / `prefetch_related`) when `info.operation.operation is not OperationType.QUERY`, at plan-build time in the walker entry point.
- G2 cache-safety argument (spec-004 B1 grounding): gating at plan-build time is safe with ZERO cache-key change because the plan-cache key's first component is the printed operation AST (`_print_operation_with_reachable_fragments`, `extension.py:920-982`), and `print_ast(operation)` includes the `query` / `mutation` / `subscription` keyword - a query document and a mutation document can never collide on one cache entry.
- G2 FK-id-elision-under-non-`QUERY`-ops decision - **RESOLVED** (spec Decision 5): elision stays enabled, with a resolver-time loaded-check. With the optimizer's `only` suppressed the full source row loads, so the FK `attname` column the elision stub reads is normally present; but a consumer-returned `.only(...)` can still defer it, so `types/resolvers.py::_build_fk_id_stub` verifies the column is loaded and falls back **loudly** (strictness-visible) when it is not - never a silent per-row lazy load. Pinned by tests in `tests/types/test_resolvers.py`.
- **[DEFERRED - G3 ships no runtime code in spec-035; moved to the abstract-return optimizer entry card (BACKLOG `polymorphic_interface_connections`); see spec-035 Decision 6/7, Revision 3-4.]** G3 - fragment type-condition narrowing. The walker treats `type_condition` purely as a fragment marker (`walker.py:845` is `hasattr(selection, "type_condition")`); `_included_field_selections` (`walker.py:733`) inlines every fragment body unconditionally. Two verified failure modes on interface/union queries: (a) fields from sibling concrete types miss the current `field_map` and fall through the unknown-name guard (`walker.py:203` `if django_field is None:` -> `continue`) - those branches are silently UNPLANNED, so every sibling-type relation selection is an N+1 the plan can never cover (B3 strictness fires at runtime, which is detection, not prevention); (b) a same-named relation existing on two members gets planned for the wrong branch - a spurious `select_related` join / over-projection (over-fetch, never wrong data).
- **[DEFERRED - G3 ships no runtime code in spec-035; moved to the abstract-return optimizer entry card (BACKLOG `polymorphic_interface_connections`); see spec-035 Decision 6/7, Revision 3-4.]** G3 implementation (bounded, registry-only): when a fragment carries a non-None `type_condition`, inline its body only when the condition's type name matches the current planning type - the `type_cls` returned by `_resolve_field_map` (`walker.py:197`): its own GraphQL name, a name in its `Meta.interfaces`, or the registered primary type name for the model; otherwise skip the fragment subtree. Resolve names through the registry/definition only - NO graphql-core schema lookups in the walk, preserving the B7 invariant (zero per-request Django/schema introspection). Upstream's heavier alternative for contrast: per-model concrete-type resolution via `get_possible_concrete_types` (`strawberry_django/utils/inspect.py:206-245`) with a per-concrete-type `ResolveInfo` re-walk (`optimizer.py:1492-1517`) - explicitly out of scope; we narrow, we do not multi-plan.
- **[DEFERRED - G3 ships no runtime code in spec-035; moved to the abstract-return optimizer entry card (BACKLOG `polymorphic_interface_connections`); see spec-035 Decision 6/7, Revision 3-4.]** G3 cache-safety argument: narrowing is a pure function of (document, target_model, origin) - all three are already plan-cache key components (`extension.py:920-982`), so narrowed plans cache correctly with no key change.

#### Definition of done

- [x] Spec file added under `docs/` (numbered to the card at implementation time, suffix `optimizer_hardening-0_0_10`; it stays at the live working path until the next spec author's batched archive sweep relocates it to `docs/SPECS/`), recording all three guard mechanisms, the G2 elision decision, and the deferred-findings table from the 2026-06-11 audit with upstream file:line anchors.
- [x] G1: early-return lands in `extension.py::_optimize`; test pins the pass-through - root resolver evaluates the queryset (`len(qs)`) then returns it; assert exactly one SQL query total and that the returned object is the SAME queryset instance (not a re-executing clone). A second test pins that the manager-coercion path (`Model.objects`) still optimizes (the guard must sit after `extension.py:714`).
- [x] G2: a mutation operation whose root resolver returns a queryset produces a plan with empty `only_fields` while `select_related` / `prefetch_related` survive; a textually-identical selection set under a `query` operation still projects `only_fields`; both plans coexist in the cache (distinct printed-AST keys). Subscription operations covered by the same gate.
- [x] G2: the FK-id elision under non-QUERY ops decision is pinned by a dedicated test matching whatever the spec records.
- [ ] **[DEFERRED to the abstract-return optimizer entry card — BACKLOG `polymorphic_interface_connections`; see spec-035 Decision 6/7 / Revision 3]** G3: union and interface fragment tests - sibling-type fragment bodies are excluded from the plan (no spurious `select_related` / `only` entries); matching-type and interface-implementor fragments still plan; the same-named-relation-on-two-members shape is a dedicated regression test; B3 strictness keys remain branch-sensitive after narrowing (no regression in `tests/optimizer/` strictness coverage).
- [ ] **[DEFERRED to the abstract-return optimizer entry card — BACKLOG `polymorphic_interface_connections`; see spec-035 Decision 6/7 / Revision 3]** Strictness `warn` no longer fires for relation selections inside correctly-narrowed sibling fragments that the resolver never executes (the old silent-N+1 signature is gone from that path).
- [x] No B1-B8 regressions: full suite green at the 100% coverage gate; the plan-cache hit path gains zero allocations (memoized id-resolver check stays ~40ns, cache-hit promotion unchanged); `ruff format` + `ruff check` clean.
- [x] Optimizer docs (`docs/` optimizer page or README optimizer section) gain a short 'what the optimizer will not touch' note covering evaluated querysets and non-query operations.

#### Files likely touched

- `django_strawberry_framework/optimizer/extension.py` - G1 `_result_cache` early return in `_optimize`; G2 operation-type read threaded to plan build.
- `django_strawberry_framework/optimizer/walker.py` - G2 `only_fields` suppression at `plan_optimizations` entry; G3 `type_condition` matching in `_included_field_selections` (and the extension-side fragment clone helpers `_named_children` / `_node_children_with_runtime_prefix` if connection extraction needs the same narrowing). **[As shipped: the G2 `enable_only` gate landed in `walker.py` threaded through every projection writer; G3 `type_condition` matching is DEFERRED (no code). The Decision 5 FK-id-elision loaded-check landed in `django_strawberry_framework/types/resolvers.py`, with tests in `tests/types/test_resolvers.py`.]**
- `django_strawberry_framework/optimizer/plans.py` - only if the G2 gate lands at apply-time instead of build-time (spec decides; build-time preferred for cacheability).
- `tests/optimizer/test_extension.py`, `tests/optimizer/test_walker.py` - mirrored guard tests.
- `docs/spec-035-optimizer_hardening-0_0_10.md` - new (lives at the live working path; the `docs/SPECS/` archive move is the next spec author's batched sweep, never per-card).

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py:1781` - the resolve hook optimizes only when `isinstance(ret, QuerySet) and ret._result_cache is None`; `optimizer.py:1628` re-guards inside `optimize()` with `is_optimized(qs) or qs._result_cache is not None`; `queryset.py:50-62` monkeypatches `QuerySet._clone` to carry the optimized flag across clones. The execution-state half of this contract (G1) is the part we are missing; the flag half is redundant under our O3 root gate.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py:1784` and `:1817` - `enable_only` is ANDed with `info.operation.operation == OperationType.QUERY`, so `.only()` is never applied to mutation/subscription querysets while select/prefetch optimization stays on - exactly the G2 split this card adopts.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py:1492-1517` + `utils/inspect.py:206-245` (`get_possible_concrete_types`) - upstream resolves the concrete types a model can render as and re-walks hints per concrete type under a synthesized `ResolveInfo`; G3 adopts the narrowing outcome through the registry instead of the schema, without the per-type re-walk.

#### Why it matters

- G2 is sequencing-critical: the 0.0.11 mutations cohort (`Mutations + auto-generated Input types` onward) makes mutation root resolvers returning querysets a mainstream path; shipping mutations on top of an ungated `.only()` bakes deferred-refetch storms and deferred-`save()` surprises into the first write-side release.
- G3 (**DEFERRED** - no runtime code in spec-035) targets the only known silent-N+1 class left in the walker: every interface/union sibling-type branch is unplanned, and B3 strictness only detects it at runtime in dev - the plan itself can never cover it. The narrowing that would close it is carried forward to the abstract-return optimizer entry card (motivation, not behavior shipped here).
- G1 protects consumer-evaluated querysets from invisible double execution - the exact 'respect what the consumer already did' posture spec-004 B8 pinned for optimization state, extended to execution state.
- All three are robustness parity items against `strawberry_django` (each verified at a specific upstream line) while preserving the four advantages the 2026-06-11 audit confirmed we hold over upstream: the global LRU plan cache (B1), FK-id elision (B2), strictness N+1 detection (B3), and class-creation-time `FieldMeta` precomputation (B7).

#### Dependencies

- **[DEFERRED - G3 ships no runtime code in spec-035; moved to the abstract-return optimizer entry card (BACKLOG `polymorphic_interface_connections`); see spec-035 Decision 6/7, Revision 3-4.]** G3 rewrites fragment inlining in the same `walker.py` selection-normalization seam (`_included_field_selections` / `_named_children`) that connection-aware planning extends; land after it to avoid concurrent walker churn, and so G3's union/interface tests can cover connection-wrapped fragments too.

#### Other

- Deferred audit finding (owned elsewhere): windowed nested-prefetch pagination (`strawberry_django/pagination.py:209-282`, `RowNumber` window partitioned by the relation FK) and `totalCount` reuse from the `_strawberry_total_count` window annotation (`relay/list_connection.py`) are the nested-connection performance findings - both already scoped under `Connection-aware optimizer planning`.
- Deferred audit finding (not scheduled): annotation hints - upstream supports `field(annotate=...)` including callables receiving `Info` (`strawberry_django/optimizer.py:492-511`, placeholder-label mechanism at `:206-210` / `:786-798`); we have no annotate path, so computed DB fields cannot be auto-planned. Adjacent to the BACKLOG model-property / cached-property optimization-hints item; promote together if scheduled.
- Deferred audit finding (deliberate non-adoption, record as a spec non-goal): prefetch MERGING - upstream's `PrefetchInspector.merge` (`strawberry_django/utils/inspect.py:324-387`) unions `only` sets and merges conflicting `Prefetch` querysets, using an `_optimizer_sentinel` marker (`optimizer.py:352-355`) to permit unsafe merges of its own prefetches. Our consumer-wins drop in `diff_plan_for_queryset` (spec-004 B8) is a permission-boundary safety stance, not an oversight; revisit only behind a strict no-custom-filter merge precondition.
- Deferred audit findings (out of scope, record as spec non-goals): GenericForeignKey prefetch (`strawberry_django/optimizer.py:1081-1087`), django-polymorphic / InheritanceManager `select_subclasses` cooperation (`optimizer.py:1251-1252`, `:1643-1664`), and a `DjangoOptimizerExtension.disabled()` contextvar escape hatch (`optimizer.py:1796-1803`).
- Audit method note: both inventories were produced from source on 2026-06-11 (36 upstream capabilities; full subsystem map of ours); every gap claimed here was re-verified by direct grep/read of our package before this card was written - no claim rests on the inventory alone.

#### Card references

- Dependency: G3 rewrites fragment inlining in the same `walker.py` selection-normalization seam (`_included_field_selections` / `_named_children`) that connection-aware planning extends; land after it to avoid concurrent walker churn, and so G3's union/interface tests can cover connection-wrapped fragments too. -> `DONE-033-0.0.9` - Connection-aware optimizer planning
- Related: G2 (`.only()` gating by operation type) must land before the 0.0.11 mutations cohort makes mutation root querysets a mainstream consumer path. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types
- Related: G1 extends spec-004 B8's consumer-state reconciliation from optimization state to execution state; G2's cache-safety argument rests on the spec-004 B1 printed-AST cache key. -> `DONE-004-0.0.3` - Optimizer beyond slices B1-B8
- Related: G1's minimal shape (no clone monkeypatch, no optimized flag) is justified by the O3 root gate; G3 lives in the O2 walker's selection-normalization seam. -> `DONE-002-0.0.2` - Optimizer O1-O6 foundation

<a id="permissions_subsystem"></a>
### [DONE-034-0.0.10 - Permissions subsystem](KANBAN.html#permissions_subsystem)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `optimizer`, `permissions`, `public-api`, `security`
- Spec: [spec-034-permissions-0_0_10.md](docs/SPECS/spec-034-permissions-0_0_10.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [`Meta.fields_class`](docs/GLOSSARY.md#metafields_class) | planned for `0.1.1` |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter) | shipped (`0.0.8`) |
| [`RelatedOrder`](docs/GLOSSARY.md#relatedorder) | shipped (`0.0.8`) |
| [`Meta.filterset_class`](docs/GLOSSARY.md#metafilterset_class) | shipped (`0.0.8`) |
| [`Meta.orderset_class`](docs/GLOSSARY.md#metaorderset_class) | shipped (`0.0.8`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [Queryset diffing](docs/GLOSSARY.md#queryset-diffing) | shipped (`0.0.3`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) | shipped (`0.0.3`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoConnection`](docs/GLOSSARY.md#djangoconnection) | shipped (`0.0.9`) |
| [`Meta.connection`](docs/GLOSSARY.md#metaconnection) | shipped (`0.0.9`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [`DjangoNodesField`](docs/GLOSSARY.md#djangonodesfield) | shipped (`0.0.9`) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [`Meta.relation_shapes`](docs/GLOSSARY.md#metarelation_shapes) | shipped (`0.0.9`) |
| [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) | shipped (`0.0.5`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) | shipped (`0.0.11`) |
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | planned for `0.0.13` |
| [`AggregateSet`](docs/GLOSSARY.md#aggregateset) | planned for `0.1.3` |
| [`get_child_queryset`](docs/GLOSSARY.md#get_child_queryset) | planned for `0.1.3` |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |

#### Package files

- [`django_strawberry_framework/permissions.py`](django_strawberry_framework/permissions.py)
- [`django_strawberry_framework/utils/permissions.py`](django_strawberry_framework/utils/permissions.py)
- [`examples/fakeshop/test_query/test_products_api.py`](examples/fakeshop/test_query/test_products_api.py)
- [`tests/optimizer/test_extension.py`](tests/optimizer/test_extension.py)
- [`tests/test_connection.py`](tests/test_connection.py)
- [`tests/test_list_field.py`](tests/test_list_field.py)
- [`tests/test_permissions.py`](tests/test_permissions.py)
- [`tests/test_relay_node_field.py`](tests/test_relay_node_field.py)

#### Planning note

Strawberry port of graphene-django's `apply_cascade_permissions(cls, queryset, info)` from `django_graphene_filters.permissions`. The cookbook line `return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)` is the canonical consumer surface — a single composable helper that walks the model graph at call time, runs each owner type's `get_queryset(qs, info)` against the related queryset, and returns a queryset that respects per-type row-level visibility across every traversed FK / OneToOne edge. Integrates with the optimizer's `Prefetch` downgrade so cascaded relations stay N+1-safe; per-field permission hooks via the reserved `Meta.fields_class` slot are deferred to the later FieldSet work (`TODO-BETA-046-0.1.1`), not shipped in this card.

#### Dependencies

- `DONE-030-0.0.9` - `DjangoConnectionField`

#### Scope

- `apply_cascade_permissions`
- reserved `Meta.fields_class` slot for per-field permission hooks; the per-field read-gate itself ships with the later FieldSet work (`TODO-BETA-046-0.1.1`), not in this card
- Optimizer cooperation: cascaded relations downgrade to `Prefetch(queryset=...)` so visibility filters survive the join (carries the existing `get_queryset` → `Prefetch` downgrade contract across the cascade walk).
- composable permission rules that remain visible from the owning type/query surface
- Public callable surface: `apply_cascade_permissions(cls, queryset, info, fields=None)` returns a queryset; optional `fields=` argument scopes the cascade to specific FK names. Both sync and async variants ship; async variant uses `sync_to_async` around the cascade walker to stay event-loop-safe.
- Walks the model graph via `registry.iter_definitions()` (shipped 0.0.4) — for each FK / OneToOne whose target type has a `get_queryset`, build a subquery from that type's visibility and intersect into the caller's queryset.
- Cycle detection via a `ContextVar` "seen" set so self-referential or mutually-referential type graphs do not recurse infinitely; cycle break returns the partially-narrowed queryset without raising.
- Single-column FK / O2O scope only: relations without a single-column `column` attribute (composite FKs, generic relations) are skipped explicitly. M2M and reverse-FK visibility are out of scope for this card and tracked as deferred follow-ups.
- Nullable FK rows preserved — a `NULL` FK does not reference a hidden target so the parent row is not dropped from the result.
- Multi-DB / sharding safety: the per-edge target visibility subquery is pinned to the caller's database alias via `.using(qs._db)` so shard-aware querysets do not accidentally cross databases.

#### Definition of done

- [x] Add `docs/spec-034-permissions-0_0_10.md`.
- [x] Implement `django_strawberry_framework/permissions.py` or a `permissions/` package if the surface grows.
- [x] Add `tests/test_permissions.py`.
- [x] Define the `Meta` surface for per-field permissions and promote keys only when applied end-to-end.
- [x] Use real fakeshop permission users through `services.create_users(1)` in example tests where the system-under-test is the example project.
- [x] Check all permission-related ORM paths for N+1 behavior.
- [x] `apply_cascade_permissions` exported from the public surface (`from django_strawberry_framework import apply_cascade_permissions`). Both sync and async-aware variants ship together.
- [x] The four upstream invariants are each pinned by a dedicated test: ContextVar cycle guard; single-column FK/O2O scope; multi-DB pinning to the caller's alias; nullable-FK rows preserved.
- [x] Reconcile open question: how the existing per-field FILTER-denial gate (`check_<field>_permission` on `FilterSet` / `OrderSet`) composes with the new cascade visibility. Decision recorded in `docs/spec-permissions.md` before the implementation pass starts; tests pin both shapes.
- [x] Cascade composes with `DjangoConnectionField` (`DONE-030-0.0.9`): a connection field whose wrapped type's `get_queryset` calls `apply_cascade_permissions` produces a Relay connection where every edge's nested relations respect the same cascade rule.
- [x] Live HTTP coverage in `examples/fakeshop/test_query/` exercises real fakeshop permission users (via `services.create_users(1)`) across a 2-deep FK cascade. Real users, not mocked `info.context.user`.

#### Foundation-slice seam

- `apply_cascade_permissions(cls, queryset, info)` walks the model graph at call time; `registry.iter_definitions()` (shipped in 0.0.4) is the public iterator that walk uses to find each owner type's `get_queryset`.
- `_attach_relation_resolvers` already accepts a `skip_field_names` set so consumer-authored fields are not clobbered; field-level permission hooks (`fields_class`) extend the same skip-set semantics.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py::DjangoObjectType.get_queryset` is graphene_django's per-type visibility hook, applied to related fields by `converter.py`'s `CustomField.wrap_resolve` (which routes FK/O2O resolution through `_type.get_queryset` unless `bypass_get_queryset` is set) — the same per-type visibility contract this card's `apply_cascade_permissions` automates by walking FK/O2O edges into each target type's `get_queryset`, so the graphene_django parity is required.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/utils/utils.py::bypass_get_queryset` is graphene_django's explicit per-resolver escape hatch from that visibility hook, confirming graphene_django scopes permission filtering per-relation rather than cascading it; this card's cascade walk is the required-parity superset that propagates the same `get_queryset` visibility across the model graph.

#### Dependencies

- `DjangoType.get_queryset`
- optimizer `Prefetch` downgrade
- future `DjangoConnectionField`

#### Other

- for the fakeshop example and real usage.
- django-graphene-filters ships rich cascade + per-field permissions; strawberry-graphql-django's per-field story is weaker (🍓 parity-adjacent).
- permissions/visibility is security-relevant and blocks the fakeshop real-usage story.
- full subsystem: `apply_cascade_permissions`, per-field `Meta` permission hooks, and optimizer `Prefetch`-downgrade integration. New `permissions.py` (or package) + `docs/spec-permissions.md` + tests.
- Open question — hidden-FK semantics: when a parent row references a hidden target, choose between excluding the parent row, nulling the FK field, or returning a sentinel. The upstream uses sentinels; the Strawberry side has to pick before the cascade lands. Pinned in `docs/spec-permissions.md`.
- Open question — cascade performance: subquery-per-FK (one extra round-trip per FK in the cascade) vs a single annotated pass (one query that joins every cascaded relation). The upstream is subquery-per-FK; benchmark both before committing.
- Open question — M2M / reverse-relation visibility: the upstream cascade explicitly skips M2M and reverse FK. Decide whether to extend coverage here or defer to a sibling card; if deferring, name the follow-up card in the spec.
- Open question — `check_permissions` API surface: does the existing per-field filter-denial `check_<field>_permission(self, request)` survive in its current form, get renamed to disambiguate from the new field-level read gate (`FieldSet.check_<field>_permission(info)` per `TODO-BETA-046-0.1.1`), or get deprecated in favor of a unified shape? Spec must answer before implementation.

#### Card references

- Dependency: future `DjangoConnectionField` -> `DONE-030-0.0.9` - `DjangoConnectionField`
- Related: `TODO-BETA-046-0.1.1` - `FieldSet`

<a id="connection_aware_optimizer_planning"></a>
### [DONE-033-0.0.9 - Connection-aware optimizer planning](KANBAN.html#connection_aware_optimizer_planning)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Planned
- Relative size: M
- Labels: `connections`, `optimizer`, `query-planning`, `relay`
- Spec: [spec-033-connection_optimizer-0_0_9.md](docs/SPECS/spec-033-connection_optimizer-0_0_9.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoConnection`](docs/GLOSSARY.md#djangoconnection) | shipped (`0.0.9`) |
| [`Meta.relation_shapes`](docs/GLOSSARY.md#metarelation_shapes) | shipped (`0.0.9`) |
| [`Meta.connection`](docs/GLOSSARY.md#metaconnection) | shipped (`0.0.9`) |
| [`Meta.filterset_class`](docs/GLOSSARY.md#metafilterset_class) | shipped (`0.0.8`) |
| [`Meta.orderset_class`](docs/GLOSSARY.md#metaorderset_class) | shipped (`0.0.8`) |
| [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) | shipped (`0.0.3`) |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.search_fields`](docs/GLOSSARY.md#metasearch_fields) | planned for `0.1.2` |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [`DjangoNodesField`](docs/GLOSSARY.md#djangonodesfield) | shipped (`0.0.9`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |
| [Queryset diffing](docs/GLOSSARY.md#queryset-diffing) | shipped (`0.0.3`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`filter_input_type`](docs/GLOSSARY.md#filter_input_type) | shipped (`0.0.8`) |
| [`order_input_type`](docs/GLOSSARY.md#order_input_type) | shipped (`0.0.8`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) | shipped (`0.0.5`) |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [Schema audit](docs/GLOSSARY.md#schema-audit) | shipped (`0.0.3`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |

#### Package files

- [`django_strawberry_framework/connection.py`](django_strawberry_framework/connection.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`tests/optimizer/`](tests/optimizer/)

#### Planning note

planned

#### Definition of done

- [x] New spec at `docs/spec-033-connection_optimizer-0_0_9.md` (the canonical structured filename).
- [x] Walker recognizes connection edge/node shapes without reaching into `DjangoConnectionField` internals.
- [x] Tests cover the cookbook-equivalent nested-connection shape against fakeshop or the cardinality fixture.
- [x] No regression on the existing B1-B8 plan-cache and queryset-diff coverage.

#### Files likely touched

- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/optimizer/extension.py`
- future `django_strawberry_framework/connection.py`
- mirrored optimizer tests

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py::_optimize_prefetch_queryset` detects a `StrawberryDjangoConnectionExtension` on a nested field, computes a `SliceMetadata.from_arguments(first, last, before, after, max_results)`, and pushes the cursor slice into the prefetch via `apply_window_pagination` (a `RowNumber` `Window` partitioned by the related field) so each parent's connection is paginated inside one query — the connection-aware planning this card designs, making the strawberry_django parity required.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/list_connection.py::DjangoListConnection.resolve_connection` cooperates with that planner by reading `node._strawberry_total_count` / a `models.Window` annotation for `totalCount` instead of issuing a second `count()` — the per-connection total-count planning this card folds in; graphene_django ships no native connection-aware optimizer, so the claim is correctly strawberry_django-only and required.

#### Other

- gated on `DONE-030-0.0.9` / Relay decisions.
- strawberry-graphql-django plans connection selections natively; graphene-django has only rudimentary connection-aware optimization (⚛️ parity-adjacent).
- bounded optimizer extension: teach the selection-walker to recognize Relay `edges { node }` and plan paginated selections. No new subpackage; touches `walker.py` / `plans.py` / `extension.py` + mirrored tests.
- The optimizer's plan cache, `select_related` / `prefetch_related` planning, FK-id elision, and queryset diffing are all proven for direct selection trees and nested non-Relay relation paths.
- Relay-style nested connection selections (`{ allObjects { edges { node { values { edges { node { value } } } } } } }`, mirroring the cookbook recipes shape) have not been exercised against the optimizer.
- The cookbook reference `AdvancedDjangoFilterConnectionField` does its own argument and queryset construction; the Strawberry equivalent will need the optimizer to recognize Relay edge/node wrappers in its selection walk.
- Selection-tree walker awareness of Relay `edges { node { ... } }` pattern.
- Connection-pagination-aware queryset planning (`Prefetch` downgrade for `connection { edges { node } }`, `total_count` aggregate cooperation, slice-aware projections).
- Plan-cache key hygiene for paginated selections (skip pagination args that do not affect selection shape, hash the ones that do).
- Strictness-mode interaction with connection paths so unplanned nested connection access still surfaces as N+1.
- Unblocked the fakeshop products connections-only conversion (the fakeshop-activation card). The products live optimizer tests (`examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_*` — root-node merge, nested reverse-FK prefetch depth-2, nested forward-FK `select_related` depth-2) rely on root-list optimization. A `0.0.9` `DjangoConnectionField` derived an empty plan before this card (the flat walker was connection-unaware), so the products list->connection replacement landed together with this card rather than ahead of it, keeping the `test_products_optimizer_*` SQL-shape coverage honest.

#### Card references

- Related: gated on `DONE-030-0.0.9` / Relay decisions. -> `DONE-030-0.0.9` - `DjangoConnectionField`

<a id="full_relay_story_node_connection_root_validation"></a>
### [DONE-032-0.0.9 - Full Relay story (Node + Connection + Root + validation)](KANBAN.html#full_relay_story_node_connection_root_validation)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Planned
- Relative size: XL
- Labels: `connections`, `graphql-api`, `permissions`, `public-api`, `relay`
- Spec: [spec-032-full_relay-0_0_9.md](docs/SPECS/spec-032-full_relay-0_0_9.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [`DjangoNodesField`](docs/GLOSSARY.md#djangonodesfield) | shipped (`0.0.9`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoConnection`](docs/GLOSSARY.md#djangoconnection) | shipped (`0.0.9`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.connection`](docs/GLOSSARY.md#metaconnection) | shipped (`0.0.9`) |
| [`Meta.relation_shapes`](docs/GLOSSARY.md#metarelation_shapes) | shipped (`0.0.9`) |
| [`Meta.globalid_strategy`](docs/GLOSSARY.md#metaglobalid_strategy) | shipped (`0.0.9`) |
| [RELAY_GLOBALID_STRATEGY](docs/GLOSSARY.md#relay_globalid_strategy) | shipped (`0.0.9`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`Meta.name`](docs/GLOSSARY.md#metaname) | shipped |
| [`Meta.filterset_class`](docs/GLOSSARY.md#metafilterset_class) | shipped (`0.0.8`) |
| [`Meta.orderset_class`](docs/GLOSSARY.md#metaorderset_class) | shipped (`0.0.8`) |
| [`Meta.search_fields`](docs/GLOSSARY.md#metasearch_fields) | planned for `0.1.2` |
| [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) | shipped (`0.0.3`) |
| [`Meta.fields_class`](docs/GLOSSARY.md#metafields_class) | planned for `0.1.1` |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`filter_input_type`](docs/GLOSSARY.md#filter_input_type) | shipped (`0.0.8`) |
| [`order_input_type`](docs/GLOSSARY.md#order_input_type) | shipped (`0.0.8`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) | shipped (`0.0.5`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | planned for `0.0.14` |
| [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) | planned for `0.0.14` |
| [`safe_wrap_connection_method`](docs/GLOSSARY.md#safe_wrap_connection_method) | shipped (`0.0.7`) |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/connection.py`](django_strawberry_framework/connection.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/relay.py`](django_strawberry_framework/relay.py)
- [`django_strawberry_framework/testing/__init__.py`](django_strawberry_framework/testing/__init__.py)
- [`django_strawberry_framework/testing/relay.py`](django_strawberry_framework/testing/relay.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)

#### Planning note

blocked on `DONE-030-0.0.9` (`DjangoConnectionField`). When the connection field lands, this card unblocks and ships in the same release. The post-`1.0.0` "Relay magic" differentiators (type-rename GlobalID migrations, polymorphic connections, stable cursors, refetchable containers, permission-aware cursor decoding) live separately in [`BACKLOG.md`][backlog] item 39 — they extend this story rather than block it.

#### Dependencies

- `DONE-030-0.0.9` - `DjangoConnectionField`

#### Definition of done

- [x] New spec: `docs/spec-032-full_relay-0_0_9.md` covering all eight goals above with worked examples and decision rationale.
- [x] `DjangoNodeField` and `DjangoNodesField` exported from the package public surface; both wired through the registry's GlobalID decode path and the per-type `get_queryset`.
- [x] Reverse-FK and M2M relations on `relay.Node`-implementing types expose their Connection counterparts; `Meta.relation_shapes` opt-out documented.
- [x] Cursor pagination math passes the package's hand-authored Relay-spec conformance suite (the `first`/`after`/`last`/`before`/`pageInfo` edge cases), against both a root connection and a synthesized relation connection.
- [x] `Meta.connection = {"total_count": True}` adds a `totalCount` field that runs `qs.count()` on the unpaginated post-filter queryset.
- [x] Filter / order arguments accepted on Connection fields when the corresponding `*_class` is declared on the type.
- [x] Permission-aware Node lookup: `node(id:)` returns `null` for hidden rows; no existence leak via error timing.
- [x] Six schema-validation diagnostics from Goal 6 raise `ConfigurationError` with the documented messages.
- [x] `django_strawberry_framework.testing.relay` module exposes `global_id_for(type_cls, id)` and `decode_global_id(gid)`.
- [x] The fakeshop `library` HTTP test suite gains Relay-shaped queries (refetch, paginated connection, cursor round-trip, `totalCount`). Fakeshop `products` activation lights up the full Relay surface as part of `TODO-BETA-053-0.1.5`.
- [x] 100% coverage across the new code paths; tests pin both happy paths and every validation failure.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py::DjangoObjectType.get_node` implements the Relay `Node` interface by running `cls.get_queryset(model.objects, info).get(pk=id)`, so graphene_django's full Relay story routes single-object id lookups through the type's visibility hook — the same Node + global-id + permission-aware root surface this card assembles, hence required parity.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py::resolve_model_nodes` (and `resolve_model_node`) resolve `relay.GlobalID` values to model instances while running the type's `get_queryset` (via `run_type_get_queryset`), and `DjangoListConnection.resolve_connection` provides the connection half — together the Node + Connection + validated-root Relay story this card mirrors, so the strawberry_django parity is required.

#### Other

- eight-goal umbrella for the complete Relay surface (Root `node`/`nodes` fields, relation-as-Connection upgrade, cursor contracts, permission integration, schema-validation diagnostics, test helpers, fakeshop activation). New `relay.py` + `test/relay.py` + finalizer changes + spec. Cursor mechanics overlap with 024; this card is the connective tissue tying it all together.
- ~~`Meta.interfaces` design~~ — `Meta.interfaces` accepted end-to-end for any Strawberry interface; `(relay.Node,)` activates the Node foundation.
- ~~`GlobalID` mapping decision~~ — Strawberry-supplied `id: GlobalID!` from the Relay interface replaces the synthesized `id: int!`; Django primary key remains projected as a connector column for the optimizer (Decision 2 of [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-011]).
- ~~Default `resolve_*` injection~~ — `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes` defaults injected when `relay.Node` is in `Meta.interfaces`; consumer overrides preserved via Strawberry's `__func__` identity test.
- ~~`is_type_of` injection~~ — Unconditional on every `DjangoType`; consumer-declared `is_type_of` preserved.
- ~~`CompositePrimaryKey` rejection~~ — Django 5.2+ composite-pk models raise `ConfigurationError` at finalization with the documented escape hatch (`id: relay.NodeID[...]` annotation).
- `node(id: GlobalID!): Node` — single-object refetch. Decodes the GlobalID, dispatches to the type's `resolve_node`, returns the resolved object. Returns `null` if the GlobalID decodes to a type/ID the requesting user can't see (respects `get_queryset`).
- `nodes(ids: [GlobalID!]!): [Node]!` — batch refetch. Decodes each GlobalID, dispatches per-type to `resolve_nodes` (batched), returns results in input order. Missing IDs become `null` entries (preserves positional correspondence).
- **Implicit upgrade** (default): every `DjangoType` whose `Meta.interfaces` includes `relay.Node` automatically exposes its reverse-FK and M2M relations as Connections in addition to the existing `list[T]` shape. Field names follow a stable convention (`itemsConnection: ItemConnection` alongside `items: list[Item]`).
- **Explicit-only**: consumers who want only Connections (or only lists) on a relation declare `Meta.relation_shapes = {"items": "connection"}` (or `"list"`, or `"both"` — `"both"` is the default for Relay types).
- **Cursor format**: opaque base64-encoded payload by default (`b64("offset:N")`). Documented as opaque — clients must not parse it. `Meta.cursor_field` for stable column-based cursors is **out of scope** for this card; lives in BETTER item 39 sub-feature 3.
- **Required arguments**: `first: Int`, `after: String`, `last: Int`, `before: String`. Backward pagination (`last`/`before`) is required by the Relay spec.
- **`pageInfo`**: emits the four standard fields (`hasNextPage`, `hasPreviousPage`, `startCursor`, `endCursor`) with correct semantics — including the spec-mandated *"the connection MUST resolve `hasNextPage` correctly even when the consumer didn't request it"* invariant.
- **Edge cases**: `first: 0` returns empty edges + `pageInfo`. `first: N` with N > remaining rows returns the actual remainder. `after` cursor for a row that no longer exists falls through to the next existing row (no error). Both `first` and `last` in the same query is rejected with a typed error.
- **`totalCount`**: an opt-in field on every Connection (`Meta.connection = {"total_count": True}`). When selected, runs `qs.count()` on the *unpaginated* queryset (post-filter, pre-slice). Documented as the canonical Relay-compatible total-count surface.
- `filter: <Type>FilterInput` — generated from `Meta.filterset_class` (composes with `DONE-027-0.0.8`)
- `orderBy: [<Type>OrderInput!]` — generated from `Meta.orderset_class` (composes with `DONE-028-0.0.8`)
- `search: String` — generated from `Meta.search_fields` (composes with `TODO-BETA-047-0.1.2` — note: search is `1.0.0` scope, ships after `0.1.0`; until then, search arg is absent)
- decode the GlobalID server-side (never trust the client's claim of which type the ID belongs to)
- dispatch to the resolved type's `resolve_node` (which honors `cls.get_queryset(qs, info)`)
- return `null` for rows the user can't see (not an error — the Relay spec requires `null`, not an exception)
- never reveal *existence* of hidden rows through error timing or status codes
- `relay.GlobalID`, `relay.NodeID[...]`, `relay.Connection`, `relay.ListConnection`, `relay.Edge`, `relay.PageInfo` in `Meta.interfaces` → rejected with a message naming the helper and explaining it's a scalar / annotation / field-type rather than an interface.
- Non-Strawberry-interface classes in `Meta.interfaces` → rejected at validation with the offending class name.
- `Meta.connection = {...}` declared on a type that doesn't include `relay.Node` in `Meta.interfaces` → rejected with a message suggesting either remove the `connection` key or add `relay.Node` to interfaces.
- A `DjangoNodeField()` query field on a schema with **no** `DjangoType`s declaring `relay.Node` → rejected at finalization with *"node lookup configured but no Node types registered."*
- `node(id:)` and `nodes(ids:)` resolve real product / category / item / entry GlobalIDs
- Reverse-FK and M2M relations on those types expose their Connection counterparts
- Live HTTP tests under `examples/fakeshop/test_query/` exercise the full Relay query shape (refetch, paginated connection, cursor round-trip, `totalCount`)
- Type-rename GlobalID migrations (Django-migrations-style history that lets old-format IDs decode alongside new)
- Polymorphic connections (`Connection[Interface]` with auto-dispatched concrete types per edge)
- `Meta.cursor_field` for stable cursors keyed on a deterministic column
- Auto-upgrade reverse FK / M2M to Connection based on a row-count threshold
- Refetchable container schema metadata for `useRefetchableFragment`
- Permission-aware cursor decoding (cursor decode re-runs `get_queryset` so privileged cursors don't leak)
- `DONE-030-0.0.9` (`DjangoConnectionField`) — **hard dependency**; this card unblocks when 026 lands.
- `DONE-027-0.0.8` (Filtering subsystem) — soft dependency for the filter argument on Connections.
- `DONE-028-0.0.8` (Ordering subsystem) — soft dependency for the orderBy argument on Connections.
- `DONE-033-0.0.9` (Connection-aware optimizer planning) — ships in parallel; the Node entry points and the relation-as-Connection upgrade both rely on the walker recognizing `edges { node { ... } }`.
- `DONE-034-0.0.10` (Permissions subsystem) — soft dependency; the Node entry points respect `get_queryset` immediately and integrate with declared permissions when 029 lands.
- `django_strawberry_framework/connection.py` — main implementation (shipped as part of `DONE-030-0.0.9`)
- `django_strawberry_framework/relay.py` (new) — `DjangoNodeField`, `DjangoNodesField`, GlobalID decode dispatch
- `django_strawberry_framework/types/base.py` — `Meta.connection` / `Meta.relation_shapes` validation
- `django_strawberry_framework/types/finalizer.py` — auto-upgrade reverse-FK / M2M to Connection
- `django_strawberry_framework/testing/relay.py` (new) — test helpers
- `tests/test_relay_node_field.py`, `tests/test_relay_connection.py` (new)
- `examples/fakeshop/test_query/test_library_api.py` — Relay-shape HTTP tests
- `examples/fakeshop/apps/products/schema.py` — Relay surface activation (lit up at fakeshop activation time)
- `docs/spec-032-full_relay-0_0_9.md` (new)
- `docs/GLOSSARY.md` — Relay surface description
- Relay node refetch from Apollo / Relay Compiler clients (the *"Relay just works"* end state for `1.0.0`)
- Fakeshop product-catalog Relay activation (Goal 8)
- Per-type `useFragment` / `useRefetchableFragment` patterns (mechanics; the schema-side `@refetchable` directive support lives in BETTER item 39 sub-feature 5)
- Every BETTER item 39 sub-feature builds on this card's mechanics
- Fakeshop products-app activation (`examples/fakeshop/apps/products/schema.py`): replace the four `Query` list resolvers (`all_categories` / `all_items` / `all_properties` / `all_entries`) with `DjangoConnectionField`s for the 1-to-1 `django-graphene-filters` cookbook mirror (connections-only — the cookbook Query is `all_object_types = AdvancedDjangoFilterConnectionField(ObjectTypeNode)` with no list resolvers). The four `*Type` classes are already Relay-Node-shaped with `filterset_class` / `orderset_class` wired, so only the root-field shape changes; `relay.node()` / root `Node.Field` refetch is the separate root-Node goal of this card. Deferred from the `DONE-030-0.0.9` (`DjangoConnectionField`) cycle and gated on `DONE-033-0.0.9` (connection-aware optimizer): a `0.0.9` `DjangoConnectionField` derives an empty optimizer plan, so a connections-only products conversion must land with 033 to avoid regressing the `test_products_optimizer_*` SQL-shape coverage.

#### Card references

- Blocked by: blocked on `DONE-030-0.0.9` (`DjangoConnectionField`). When the connection field lands, this card unblocks and ships in the same release. The post-`1.0.0` "Relay magic" differentiators (type-rename GlobalID migrations, polymorphic connections, stable cursors, refetchable containers, permission-aware cursor decoding) live separately in [`BACKLOG.md`][backlog] item 39 — they extend this story rather than block it. -> `DONE-030-0.0.9` - `DjangoConnectionField`
- Related: `filter: <Type>FilterInput` — generated from `Meta.filterset_class` (composes with `DONE-027-0.0.8`) -> `DONE-027-0.0.8` - Filtering subsystem
- Related: `orderBy: [<Type>OrderInput!]` — generated from `Meta.orderset_class` (composes with `DONE-028-0.0.8`) -> `DONE-028-0.0.8` - Ordering subsystem
- Related: `search: String` — generated from `Meta.search_fields` (composes with `TODO-BETA-047-0.1.2` — note: search is `1.0.0` scope, ships after `0.1.0`; until then, search arg is absent) -> `TODO-BETA-047-0.1.2` - `Meta.search_fields` support
- Related: `DONE-030-0.0.9` (`DjangoConnectionField`) — **hard dependency**; this card unblocks when 026 lands. -> `DONE-030-0.0.9` - `DjangoConnectionField`
- Related: `DONE-027-0.0.8` (Filtering subsystem) — soft dependency for the filter argument on Connections. -> `DONE-027-0.0.8` - Filtering subsystem
- Related: `DONE-028-0.0.8` (Ordering subsystem) — soft dependency for the orderBy argument on Connections. -> `DONE-028-0.0.8` - Ordering subsystem
- Related: `DONE-033-0.0.9` (Connection-aware optimizer planning) — ships in parallel; the Node entry points and the relation-as-Connection upgrade both rely on the walker recognizing `edges { node { ... } }`. -> `DONE-033-0.0.9` - Connection-aware optimizer planning
- Related: `DONE-034-0.0.10` (Permissions subsystem) — soft dependency; the Node entry points respect `get_queryset` immediately and integrate with declared permissions when 029 lands. -> `DONE-034-0.0.10` - Permissions subsystem
- Related: The fakeshop `library` HTTP test suite gains Relay-shaped queries (refetch, paginated connection, cursor round-trip, `totalCount`). Fakeshop `products` activation lights up the full Relay surface as part of `TODO-BETA-053-0.1.5`. -> `TODO-BETA-053-0.1.5` - Fakeshop GraphQL schema activation
- Related: `django_strawberry_framework/connection.py` — main implementation (shipped as part of `DONE-030-0.0.9`) -> `DONE-030-0.0.9` - `DjangoConnectionField`

<a id="django_model_based_globalid_encoding"></a>
### [DONE-031-0.0.9 - Django-model-based GlobalID encoding](KANBAN.html#django_model_based_globalid_encoding)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Parity-adjacent)
- Severity: Major
- Status: Needs spec
- Relative size: M
- Labels: `config`, `public-api`, `registry`, `relay`, `stable-api`, `types`, `versioning`
- Spec: [spec-031-globalid_encoding-0_0_9.md](docs/SPECS/spec-031-globalid_encoding-0_0_9.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.name`](docs/GLOSSARY.md#metaname) | shipped |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`Meta.connection`](docs/GLOSSARY.md#metaconnection) | shipped (`0.0.9`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) | shipped (`0.0.5`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoConnection`](docs/GLOSSARY.md#djangoconnection) | shipped (`0.0.9`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [`Meta.fields_class`](docs/GLOSSARY.md#metafields_class) | planned for `0.1.1` |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter) | shipped (`0.0.8`) |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [`BigInt` scalar](docs/GLOSSARY.md#bigint-scalar) | shipped (`0.0.6`) |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [Schema introspection management command](docs/GLOSSARY.md#schema-introspection-management-command) | shipped (`0.0.9`) |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |
| [`Meta.globalid_strategy`](docs/GLOSSARY.md#metaglobalid_strategy) | shipped (`0.0.9`) |
| [RELAY_GLOBALID_STRATEGY](docs/GLOSSARY.md#relay_globalid_strategy) | shipped (`0.0.9`) |

#### Package files

- [`django_strawberry_framework/filters/base.py`](django_strawberry_framework/filters/base.py)
- [`django_strawberry_framework/filters/inputs.py`](django_strawberry_framework/filters/inputs.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)
- [`django_strawberry_framework/types/relay.py`](django_strawberry_framework/types/relay.py)
- [`django_strawberry_framework/utils/typing.py`](django_strawberry_framework/utils/typing.py)

#### Planning note

Promoted from BACKLOG.md item 40 and slotted after `DjangoConnectionField` but before the Full Relay story. This is the Relay identity-format decision: Django model identity should be the durable GlobalID anchor before root Node/refetch behavior and client-cache-facing Relay semantics harden.

#### Scope

- Switch the default Relay GlobalID payload for `DjangoType` rows from GraphQL type name + id to Django model label + id, e.g. `products.item:42`.
- Add a per-type `Meta.globalid_strategy` override and a schema-wide `DJANGO_STRAWBERRY_FRAMEWORK["RELAY_GLOBALID_STRATEGY"]` setting, with precedence `Meta` override, then setting, then package default.
- Support the planned strategies: `model` as the new default, `type` as an opt-in legacy/standard Relay convention, `type+model` as a transitional decoder/encoder mode, and callable strategies for fully custom encodings.
- Route decoded model-label IDs through Django's app registry and the framework registry so multiple `DjangoType`s for one model resolve through the primary type unless the consumer explicitly opts into type-scoped IDs.
- Document the edge cases: proxy models, multi-table inheritance, slug/custom `resolve_id_attr` values, composite-primary-key rejection, and rare Django model/app rename aliases.

#### Definition of done

- [x] A new or amended Relay spec records the GlobalID format decision before Full Relay root Node/refetch behavior ships.
- [x] Encoder and decoder tests cover `model`, `type`, `type+model`, and callable strategies.
- [x] Settings and `Meta.globalid_strategy` validation reject unknown strategy names loudly with `ConfigurationError`.
- [x] Multiple-`DjangoType` per model behavior is pinned: model-based IDs route through the primary type; type-scoped IDs remain available when consumers need disjoint auth/cache scopes.
- [x] Relay helper tests prove old type-name IDs can be accepted in transitional mode while new emitted IDs use the model-label strategy.
- [x] Standing docs describe the default, the opt-out path, and the pre-1.0 compatibility implications.

#### Foundation-slice seam

- Builds on the shipped Relay Node foundation (`Meta.interfaces = (relay.Node,)`, default `resolve_*` methods, and synthesized-id suppression).
- Must land before the Full Relay story mints durable root `node(id:)` and connection/refetch IDs into the public surface.
- The registry already knows the model-to-`DjangoType` mapping; this card changes what the encoded Relay ID points at, not how consumers declare Relay support.

#### Files likely touched

- `django_strawberry_framework/types/relay.py` or the local Relay helper module that owns encode/decode behavior
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/conf.py`
- `django_strawberry_framework/registry.py`
- `tests/types/test_relay_interfaces.py` and related Relay tests
- `docs/GLOSSARY.md`, `docs/README.md`, and the active Relay spec when the feature ships

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene/relay/node.py::Node.to_global_id` — graphene-django Relay nodes encode the GlobalID as base64 `<GraphQL type name>:<id>` (type-name-anchored). Tagged **parity-adjacent, not required**: the type-anchored convention itself already shipped at parity in `DONE-015-0.0.5` (the Relay-supplied `id: GlobalID!`). 031 preserves that exact convention as the opt-in `type` strategy and makes a Django-model-anchored payload (`app_label.model:id`, e.g. `products.item:42`) the new default — extending the upstream GlobalID surface with a Django-idiomatic encoding neither upstream offers.
- `strawberry.relay.GlobalID` (consumed by strawberry-graphql-django; `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py` wires the Relay node types) encodes `to_base64(type_name, node_id)` — also type-name-anchored. Same parity-adjacent relationship: the standard convention stays available as the `type` strategy, while the model-anchored default plus the `Meta.globalid_strategy` override and the `RELAY_GLOBALID_STRATEGY` setting are the beyond-parity differentiator. Tagged `adjacent` (not `required`) for both upstreams so the Alpha cut stays parity-honest — GlobalID parity proper was met in `DONE-015-0.0.5`.

#### Why it matters

- The standard Relay convention bakes the GraphQL type name into durable object identity. In Django apps the model is the durable thing; the GraphQL type is a refactor-friendly facade.
- Getting this right before `1.0.0` lets consumers rename GraphQL types without invalidating every cached GlobalID. Waiting until after Full Relay ships turns the same decision into migration work.

#### Other

- Original backlog score: Realistic 9/10, Impact 8/10, Difficulty 3/10; bang-for-buck score 24.0.
- Legitimate legacy mode remains available: projects that intentionally scope identity by GraphQL type can opt into the `type` strategy per type or project-wide.

#### Card references

- Related: This card should land before Full Relay because root `node(id:)`, `nodes(ids:)`, and refetch helpers make GlobalID encoding a public durability contract. -> `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)
- Related: `DjangoConnectionField` can land before this card because connection pagination does not require changing the Relay GlobalID payload. -> `DONE-030-0.0.9` - `DjangoConnectionField`
- Related: `DONE-015-0.0.5` - 0.0.5 Relay interfaces and Node foundation

<a id="djangoconnectionfield"></a>
### [DONE-030-0.0.9 - `DjangoConnectionField`](KANBAN.html#djangoconnectionfield)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Planned
- Relative size: L
- Labels: `connections`, `filters`, `optimizer`, `ordering`, `public-api`, `relay`
- Spec: [spec-030-connection_field-0_0_9.md](docs/SPECS/spec-030-connection_field-0_0_9.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoConnection`](docs/GLOSSARY.md#djangoconnection) | shipped (`0.0.9`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.connection`](docs/GLOSSARY.md#metaconnection) | shipped (`0.0.9`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`filter_input_type`](docs/GLOSSARY.md#filter_input_type) | shipped (`0.0.8`) |
| [`Meta.filterset_class`](docs/GLOSSARY.md#metafilterset_class) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`order_input_type`](docs/GLOSSARY.md#order_input_type) | shipped (`0.0.8`) |
| [`Meta.orderset_class`](docs/GLOSSARY.md#metaorderset_class) | shipped (`0.0.8`) |
| [`Ordering`](docs/GLOSSARY.md#ordering) | shipped (`0.0.8`) |
| [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter) | shipped (`0.0.8`) |
| [`RelatedOrder`](docs/GLOSSARY.md#relatedorder) | shipped (`0.0.8`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [Queryset diffing](docs/GLOSSARY.md#queryset-diffing) | shipped (`0.0.3`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) | shipped (`0.0.5`) |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) | shipped |
| [`Meta.name`](docs/GLOSSARY.md#metaname) | shipped |
| [`Meta.description`](docs/GLOSSARY.md#metadescription) | shipped |
| [`Meta.nullable_overrides`](docs/GLOSSARY.md#metanullable_overrides) | shipped (`0.0.9`) |
| [`Meta.required_overrides`](docs/GLOSSARY.md#metarequired_overrides) | shipped (`0.0.9`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [`Meta.search_fields`](docs/GLOSSARY.md#metasearch_fields) | planned for `0.1.2` |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [`Meta.fields_class`](docs/GLOSSARY.md#metafields_class) | planned for `0.1.1` |
| [`AggregateSet`](docs/GLOSSARY.md#aggregateset) | planned for `0.1.3` |
| [`Meta.aggregate_class`](docs/GLOSSARY.md#metaaggregate_class) | planned for `0.1.3` |
| [`RelatedAggregate`](docs/GLOSSARY.md#relatedaggregate) | planned for `0.1.3` |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) | shipped (`0.0.3`) |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/connection.py`](django_strawberry_framework/connection.py)
- [`django_strawberry_framework/list_field.py`](django_strawberry_framework/list_field.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/orders/inputs.py`](django_strawberry_framework/orders/inputs.py)
- [`django_strawberry_framework/orders/sets.py`](django_strawberry_framework/orders/sets.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)

#### Planning note

Strawberry analogue of graphene-django's `AdvancedDjangoFilterConnectionField`. Wires the shipped Layer-3 sidecars into a Relay-shaped connection: accepts `filter:` from `Meta.filterset_class` (`DONE-027-0.0.8`), `orderBy:` from `Meta.orderset_class` (`DONE-028-0.0.8`), plus `first`/`after`/`last`/`before` cursor pagination and opt-in `totalCount`. The `search:` arg activates when `TODO-BETA-047-0.1.2` lands; `FieldSet` selection composition is layered in by `TODO-BETA-046-0.1.1`. Central read-side primitive — every Layer-3 argument composes through this field.

#### Dependencies

- `DONE-027-0.0.8` - Filtering subsystem
- `DONE-028-0.0.8` - Ordering subsystem
- `DONE-029-0.0.9` - `DjangoType` consumer-DX cleanup pass

#### Scope

- Relay-style connection field
- composition of filtering, ordering, aggregation, field selection, and optimizer behavior
- Cookbook anchor: Strawberry analogue of graphene-django's `AdvancedDjangoFilterConnectionField`. Each `DjangoConnectionField(SomeType)` exposes the type's declared sidecars as connection arguments plus the standard Relay pagination args. The graphene cookbook line `all_object_types = AdvancedDjangoFilterConnectionField(ObjectTypeNode)` becomes `all_object_types: DjangoConnection[ObjectTypeNode] = DjangoConnectionField(ObjectTypeNode)` on the Strawberry side; the per-type `Meta.filterset_class` / `Meta.orderset_class` declarations drive argument generation identically.
- `filter: <Type>FilterInput` — auto-derived from `Meta.filterset_class` (`DONE-027-0.0.8`); absent when the type declares no filterset. Active-input gating and `check_*_permission` propagation carry over from the filter subsystem unchanged.
- `orderBy: [<Type>OrderInput!]` — auto-derived from `Meta.orderset_class` (`DONE-028-0.0.8`); absent when the type declares no orderset. List-shaped per the order spec's Decision 5.
- `first` / `after` / `last` / `before` — Relay cursor args; forward AND backward pagination per the Relay spec. Mutually-exclusive guard (`first` + `last` in one query) rejected as a typed error.
- `totalCount` — opt-in via `Meta.connection = {"total_count": True}`; runs `qs.count()` on the unpaginated post-filter queryset so paginated UIs can show "N of M" without a second round-trip.
- Composition order on the resolved queryset: `get_queryset(qs, info)` first (visibility), then `filter` (active-input gates), then `orderBy` (per-field gates), then cursor slice. The pre-pagination shape is what the optimizer plans against; the cursor slice runs last so totals stay correct.

#### Definition of done

- [x] Add `docs/spec-030-connection_field-0_0_9.md`.
- [x] Implement `django_strawberry_framework/connection.py`.
- [x] Add `tests/test_connection.py`.
- [x] Decide whether full Relay support belongs here or a separate `relay/` subpackage.
- [x] Promote `DjangoConnectionField` only when end-to-end schema usage is tested.
- [x] When the wrapped type declares `Meta.filterset_class`, the connection field exposes `filter: <Type>FilterInput` and routes input values through the filterset's `apply_sync` / `apply_async` pair.
- [x] When the wrapped type declares `Meta.orderset_class`, the connection field exposes `orderBy: [<Type>OrderInput!]` and routes through the orderset's `apply_sync` / `apply_async` pair.
- [x] Connection field composes with `cls.get_queryset(queryset, info)` — visibility scoping runs before any filter / order / cursor work.
- [x] Optimizer cooperation: the connection-aware planner (`DONE-033-0.0.9`) layers on without retrofit; this card ships against the existing flat-selection walker and the connection-aware walker takes over when 032 lands.
- [x] Live HTTP coverage in `examples/fakeshop/test_query/` exercises a real round-trip with filter + orderBy + cursor + totalCount on a Relay-Node-shaped type.

#### Foundation-slice seam

- `finalize_django_types()` is the single architectural entry point that `DjangoConnectionField(DjangoType)` (and `DjangoNodeField`) will auto-trigger as their wrapper.
- An auto-trigger wrapper must respect the single-threaded-setup window: either be constrained to schema-construction time, or acquire a real lock around the finalizer.
- Connection-aware optimizer planning is its own follow-up slice (`DONE-033-0.0.9`); the foundation slice did not exercise nested connection prefetch shapes.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/fields.py::DjangoConnectionField.connection_resolver` is graphene_django's Relay connection field: it reads `first`/`last`/`before`/`after`, enforces the `first`-or-`last` guard, runs the type's `get_queryset` for visibility, then slices via `resolve_connection` — the exact composition (`get_queryset` -> filter -> order -> cursor slice) this card's `DjangoConnectionField` ships, so the graphene_django parity is required.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/field.py::StrawberryDjangoConnectionExtension.resolve` resolves a Django queryset and hands it to `connection_type.resolve_connection(nodes, info, before=, after=, first=, last=, max_results=)`, layering the relay pagination args on top of the field's auto-derived filter/order arguments — the Strawberry-side analogue of graphene's filter-connection field this card targets, making the strawberry_django parity required.

#### Dependencies

- `FilterSet` (`DONE-027-0.0.8`)
- `OrderSet` (`DONE-028-0.0.8`)
- Relay/interface decisions
- `FieldSet` — **deferred to `TODO-BETA-046-0.1.1`** (post-Alpha); field-selection composition is layered on after the connection field ships, not a 0.0.9 blocker.
- `DjangoType` consumer-DX cleanup pass (`DONE-029-0.0.9`) - schema-construction examples are current before `DjangoConnectionField` becomes the new consumer pattern.

#### Other

- Filtering and Ordering ship before this card lands, so `DjangoConnectionField` consumes the existing filter and order argument factories on day one. `FieldSet` selection composition is layered in by `TODO-BETA-046-0.1.1`; the `search:` arg activates when `TODO-BETA-047-0.1.2` lands.
- both upstreams ship Relay-shaped connection fields.
- the central read-side primitive — the Relay surface and all Layer-3 arguments compose through it.
- central Relay-shaped connection field plus cursor-pagination math; the integration point that filters / orders / aggregation / field-selection / optimizer all compose through. New `connection.py` + `docs/spec-030-connection_field-0_0_9.md` + tests.

#### Card references

- Dependency: `FilterSet` (`DONE-027-0.0.8`) -> `DONE-027-0.0.8` - Filtering subsystem
- Related: Connection-aware optimizer planning is its own follow-up slice (`DONE-033-0.0.9`); the foundation slice did not exercise nested connection prefetch shapes. -> `DONE-033-0.0.9` - Connection-aware optimizer planning
- Dependency: `OrderSet` (`DONE-028-0.0.8`) -> `DONE-028-0.0.8` - Ordering subsystem
- Related: once filters/orders are stable. FieldSet integration is deferred to `TODO-BETA-046-0.1.1` — `DjangoConnectionField` ships against the Layer-2 surface in 0.0.9 and gains field-selection composition when FieldSet lands. -> `TODO-BETA-046-0.1.1` - `FieldSet`
- Dependency: `DjangoType` consumer-DX cleanup pass (`DONE-029-0.0.9`) - schema-construction examples are current before `DjangoConnectionField` becomes the new consumer pattern. -> `DONE-029-0.0.9` - `DjangoType` consumer-DX cleanup pass
- Related: `TODO-BETA-047-0.1.2` - `Meta.search_fields` support

<a id="djangotype_consumer_dx_cleanup_pass"></a>
### [DONE-029-0.0.9 - `DjangoType` consumer-DX cleanup pass](KANBAN.html#djangotype_consumer_dx_cleanup_pass)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Planned
- Relative size: M
- Labels: `cleanup`, `developer-tools`, `public-api`, `types`
- Spec: [spec-029-consumer_dx_cleanup-0_0_9.md](docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) | shipped |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Choice enum generation](docs/GLOSSARY.md#choice-enum-generation) | shipped (`0.0.1`) |
| [Specialized scalar conversions](docs/GLOSSARY.md#specialized-scalar-conversions) | shipped (`0.0.6`) |
| [Scalar field override semantics](docs/GLOSSARY.md#scalar-field-override-semantics) | shipped (`0.0.6`) |
| [`Meta.choice_enum_names`](docs/GLOSSARY.md#metachoice_enum_names) | planned for `0.1.4` |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [Schema export management command](docs/GLOSSARY.md#schema-export-management-command) | shipped (`0.0.7`) |
| [Schema introspection management command](docs/GLOSSARY.md#schema-introspection-management-command) | shipped (`0.0.9`) |
| [Django `AppConfig`](docs/GLOSSARY.md#django-appconfig) | shipped (`0.0.7`) |
| [`Meta.filterset_class`](docs/GLOSSARY.md#metafilterset_class) | shipped (`0.0.8`) |
| [`Meta.orderset_class`](docs/GLOSSARY.md#metaorderset_class) | shipped (`0.0.8`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [`Meta.fields_class`](docs/GLOSSARY.md#metafields_class) | planned for `0.1.1` |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [`Meta.search_fields`](docs/GLOSSARY.md#metasearch_fields) | planned for `0.1.2` |
| [`AggregateSet`](docs/GLOSSARY.md#aggregateset) | planned for `0.1.3` |
| [`Meta.aggregate_class`](docs/GLOSSARY.md#metaaggregate_class) | planned for `0.1.3` |
| [`BigInt` scalar](docs/GLOSSARY.md#bigint-scalar) | shipped (`0.0.6`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) | shipped (`0.0.3`) |
| [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter) | shipped (`0.0.8`) |
| [`RelatedOrder`](docs/GLOSSARY.md#relatedorder) | shipped (`0.0.8`) |
| [`RelatedAggregate`](docs/GLOSSARY.md#relatedaggregate) | planned for `0.1.3` |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [`Meta.nullable_overrides`](docs/GLOSSARY.md#metanullable_overrides) | shipped (`0.0.9`) |
| [`Meta.required_overrides`](docs/GLOSSARY.md#metarequired_overrides) | shipped (`0.0.9`) |

#### Package files

- [`django_strawberry_framework/management/commands/inspect_django_type.py`](django_strawberry_framework/management/commands/inspect_django_type.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)

#### Planning note

planned; three independent slices that ship in any order. Card body counts as complete when all three slices land; if the schedule forces Slice 3 to defer, the slice carves off as its own follow-up card without disrupting Slices 1 + 2.

#### Scope

- **Slice 1** — Strawberry `extensions=[instance]` factory-callable migration. Mechanical sweep of every `strawberry.Schema(query=…, extensions=[DjangoOptimizerExtension()])` site, replacing the deprecated instance form with `extensions=[DjangoOptimizerExtension]` (class) or `extensions=[lambda: DjangoOptimizerExtension()]` (factory callable). Strawberry deprecated the instance form upstream; future releases will remove it. Affects `tests/optimizer/test_relay_id_projection.py`, `tests/test_list_field.py`, `tests/types/test_generic_foreign_key.py`, `examples/fakeshop/config/schema.py`, plus the schema-construction snippet in `docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, and `TODAY.md`. ~30 min mechanical. No spec.
- **Slice 2** — `manage.py inspect_django_type <TypeName>` diagnostic command. New Django management command at `django_strawberry_framework/management/commands/inspect_django_type.py` walking a `DjangoType.__django_strawberry_definition__` and printing per-field: Django field name → Django field type → resolved GraphQL scalar/type → nullability → which `SCALAR_MAP` row (or relation converter) fired. Mirrors Django's `inspectdb` conceptually but scoped to the framework's type-definition surface. Tests via `examples/fakeshop/tests/test_commands.py::call_command("inspect_django_type", "PatronType", ...)`. Sub-1-day. Light spec or none.
- **Slice 3** — `Meta.nullable_overrides` GraphQL-layer nullability override. New public `Meta` key (and possibly a companion `Meta.required_overrides`) letting consumers decouple the GraphQL type's nullability from the underlying Django column without an `AlterField` migration or a custom resolver. Implemented inside `django_strawberry_framework/types/base.py` and `django_strawberry_framework/types/converters.py`'s scalar-resolution path. Tests in `tests/types/test_converters.py` (override + collision cases) plus a live HTTP test on the library or scalars app demonstrating the override flipping the GraphQL type's nullability without touching the model column. **Requires spec**: `docs/spec-029-consumer_dx_cleanup-0_0_9.md` — open design decisions include dict-of-name vs tuple-set per direction, interaction with `Meta.exclude`, error behavior when both override sets name the same field, choice-field interaction, and FK / reverse-FK interaction.

#### Definition of done

- [x] **Slice 1**: every `extensions=[DjangoOptimizerExtension()]` instance form replaced with the factory-callable equivalent in tests, examples, and consumer-facing docs. `uv run pytest` shows zero `DeprecationWarning` about Strawberry extension instances. CHANGELOG entry under `[Unreleased]` `### Changed`.
- [x] **Slice 2**: `django_strawberry_framework/management/commands/inspect_django_type.py` ships with module + class docstring, `add_arguments` taking a positional `type_dotted_path`, and `handle` printing the resolved field table. Tests via `examples/fakeshop/tests/test_commands.py` using `call_command`. `docs/GLOSSARY.md` adds an entry; `docs/TREE.md` lists the new module under `management/commands/`. CHANGELOG entry under `[Unreleased]` `### Added`.
- [x] **Slice 3**: `docs/spec-029-consumer_dx_cleanup-0_0_9.md` written and reviewed; `Meta.nullable_overrides` (and `Meta.required_overrides` if the spec confirms it) implemented; tests cover override-applies, override-rejects-unknown-field, override-collides-with-other-direction error, and override-on-choice-field. `docs/GLOSSARY.md` adds an entry; live HTTP test in `examples/fakeshop/test_query/` demonstrates the override flipping nullability for a real model field. CHANGELOG entry under `[Unreleased]` `### Added`.

#### Foundation-slice seam

- Slice 1 has no foundation interaction; it's a sweep across already-shipped surfaces.
- Slice 2 reads `DjangoTypeDefinition` populated by `finalize_django_types()`; the command is a strict consumer of the existing introspection surface.
- Slice 3 plugs into `DjangoType._build_annotations` (the converter loop in `django_strawberry_framework/types/base.py`) and the scalar-resolution path in `django_strawberry_framework/types/converters.py`. No finalizer changes — overrides apply at type-construction time, before finalization.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py::DjangoObjectType.__init_subclass_with_meta__` is graphene_django's consumer type-declaration surface, deriving GraphQL field nullability from the Django column (`required = not (field.blank or field.null)` in `converter.py`) and policing `Meta` keys like `fields`/`exclude`/`filterset_class` — the same `DjangoType`/`Meta` DX this card's cleanup pass refines (including the `Meta.nullable_overrides` decoupling), so the graphene_django parity is required.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py::is_optional` decides a `DjangoType` field's nullability straight from `model_field.null`/`blank`, with no consumer hook to override it independent of the column — the gap this card's `Meta.nullable_overrides` (Slice 3) closes against the strawberry_django type-definition surface, making the strawberry_django parity required.

#### Other

- three independent slices: Slice 1 `extensions=` factory-form sweep (XS, ~30 min, no spec), Slice 2 `inspect_django_type` command (S, sub-1-day), Slice 3 `Meta.nullable_overrides` (M, needs spec, deferrable to `0.0.9`). Smallest of the three `0.0.8` cards.
- **Slice 1**: defensive — both upstreams already use the factory-callable form in their consumer docs. Strawberry's removal runway is multiple releases, but landing the migration in 0.0.8 keeps the package's surface aligned with the upstream recommendation.
- **Slice 2**: differentiating — neither `graphene-django` nor `strawberry-graphql-django` ships an equivalent `manage.py inspect_*` diagnostic for their type definitions. Consumers currently introspect by hand against the GraphQL schema after construction. This command moves that diagnostic to the type-definition layer, before schema construction.
- **Slice 3**: ⚛️&🍓 required — `strawberry_django.field(required=True/False)` allows per-field GraphQL nullability override against the Django column's native nullability. `graphene_django` allows the same via `DjangoObjectType.Meta.fields` plus per-field overrides on the type class. This card surfaces the same capability through a single `Meta`-key dict that the rest of the package's `Meta`-shaped API already prefers.

<a id="ordering_subsystem"></a>
### [DONE-028-0.0.8 - Ordering subsystem](KANBAN.html#ordering_subsystem)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `filters`, `graphql-api`, `layer-3`, `ordering`, `public-api`
- Spec: [spec-028-orders-0_0_8.md](docs/SPECS/spec-028-orders-0_0_8.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`Ordering`](docs/GLOSSARY.md#ordering) | shipped (`0.0.8`) |
| [`order_input_type`](docs/GLOSSARY.md#order_input_type) | shipped (`0.0.8`) |
| [`RelatedOrder`](docs/GLOSSARY.md#relatedorder) | shipped (`0.0.8`) |
| [`Meta.orderset_class`](docs/GLOSSARY.md#metaorderset_class) | shipped (`0.0.8`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) | shipped (`0.0.3`) |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [Queryset diffing](docs/GLOSSARY.md#queryset-diffing) | shipped (`0.0.3`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Choice enum generation](docs/GLOSSARY.md#choice-enum-generation) | shipped (`0.0.1`) |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter) | shipped (`0.0.8`) |
| [`filter_input_type`](docs/GLOSSARY.md#filter_input_type) | shipped (`0.0.8`) |
| [`Meta.filterset_class`](docs/GLOSSARY.md#metafilterset_class) | shipped (`0.0.8`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [`DjangoConnection`](docs/GLOSSARY.md#djangoconnection) | shipped (`0.0.9`) |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [Schema export management command](docs/GLOSSARY.md#schema-export-management-command) | shipped (`0.0.7`) |
| [`AggregateSet`](docs/GLOSSARY.md#aggregateset) | planned for `0.1.3` |
| [`RelatedAggregate`](docs/GLOSSARY.md#relatedaggregate) | planned for `0.1.3` |
| [`Meta.aggregate_class`](docs/GLOSSARY.md#metaaggregate_class) | planned for `0.1.3` |
| [`get_child_queryset`](docs/GLOSSARY.md#get_child_queryset) | planned for `0.1.3` |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [`Meta.fields_class`](docs/GLOSSARY.md#metafields_class) | planned for `0.1.1` |
| [`Meta.search_fields`](docs/GLOSSARY.md#metasearch_fields) | planned for `0.1.2` |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/orders/__init__.py`](django_strawberry_framework/orders/__init__.py)
- [`django_strawberry_framework/orders/base.py`](django_strawberry_framework/orders/base.py)
- [`django_strawberry_framework/orders/factories.py`](django_strawberry_framework/orders/factories.py)
- [`django_strawberry_framework/orders/inputs.py`](django_strawberry_framework/orders/inputs.py)
- [`django_strawberry_framework/orders/sets.py`](django_strawberry_framework/orders/sets.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)

#### Planning note

shipped

#### Definition of done

- [x] Add `docs/spec-028-orders-0_0_8.md`.
- [x] Add `django_strawberry_framework/orders/`.
- [x] Add mirrored `tests/orders/`.
- [x] Promote `Meta.orderset_class` only when ordering is applied end-to-end.
- [x] Support simple fields and relation paths.
- [x] Define interaction with filters and connection field.
- [x] Keep ordering declarations introspectable from the owning type/query surface.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField.resolve_queryset` special-cases the `order_by` filter argument (`to_snake_case(v)` before passing it into the filterset), so graphene_django exposes ordering through django-filter's `OrderingFilter` as a first-class connection argument — the directly-comparable ordering surface this card ships, hence required parity.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/ordering.py::apply` walks an `order` type via `process_order` and emits `queryset.order_by(*args)`, where each field resolves through `Ordering.resolve` (the `ASC`/`DESC` plus `NULLS_FIRST`/`NULLS_LAST` enum) into a Django `OrderBy` — the same per-field, list-shaped ordering input this card's `orderBy` argument provides, so the strawberry_django parity is required.

#### Other

- Shipped the ordering subsystem in `0.0.8`. [`OrderSet`][glossary-orderset], [`RelatedOrder`][glossary-relatedorder], and [`Meta.orderset_class`][glossary-metaorderset_class] (promoted out of `DEFERRED_META_KEYS`) land at [`django_strawberry_framework/orders/`][orders] across five files (`base.py`, `sets.py`, `factories.py`, `inputs.py`, `__init__.py`); `tests/orders/` mirrors the layout. Five-layer lazy-resolution pipeline borrowed from `django-graphene-filters` with the same Strawberry-adapted Layer 5 the Filtering subsystem just shipped (`Annotated[\"TypeName\", strawberry.lazy(\"django_strawberry_framework.orders.inputs\")]` over module globals); the shared `LazyRelatedClassMixin` is reused from the neutral `sets_mixins` module via sibling import (per H1 of `docs/feedback.md` rev3 — `sets_mixins.py` carries both `LazyRelatedClassMixin` and `ClassBasedTypeNameMixin` for the set family). Layer 6 (dynamic OrderSet generation) deferred to `0.0.9` alongside `DjangoConnectionField` per Decision 12 of `docs/spec-028-orders-0_0_8.md`. The public `Ordering` enum borrowed verbatim from `strawberry-django` (six members: ASC / DESC / ASC_NULLS_FIRST / ASC_NULLS_LAST / DESC_NULLS_FIRST / DESC_NULLS_LAST) — NULLS positioning honored via Django `F(value).asc/desc(nulls_first=...)` expressions. The list-shaped `orderBy: [<T>OrderInputType!]` argument's element order IS the tie-breaker mechanism. The **resolver-facing API is the classmethod pair `OrderSet.apply_sync(input_value, queryset, info)` and `OrderSet.apply_async(input_value, queryset, info)`** (sync resolvers call the former; async resolvers await the latter), mirroring the shipped filter subsystem's shape. The apply pipeline runs `check_permissions` with **active-input-only scope** (per-field `check_<field>_permission` gates fire only when the consumer's input names the field); extracts the request from `info.context.request` (with an `isinstance(info.context, HttpRequest)` fallback); applies `queryset.order_by(*OrderBy_expressions)` after visibility scoping (`<OwnerType>.get_queryset`) and after optional filter narrowing (`<TypeName>Filter.apply_*`). The new `order_input_type(BranchOrder)` helper produces the resolver-annotation shape; the finalizer enforces orphan validation by raising `ConfigurationError` for any OrderSet referenced via `order_input_type` but never wired via `Meta.orderset_class` (tracked via `_helper_referenced_ordersets`). `registry.clear()` co-clears the order input namespace via `clear_order_input_namespace()` AND clears `_helper_referenced_ordersets` — alongside the already-shipped filter clears. Per-package input-class namespace is separate from the model-to-`DjangoType` registry AND from the filter-input namespace (`Meta.primary` design preserved). `Meta.orderset_class` promotion runs through finalizer phase 2.5 via `_bind_ordersets()` with four ordered subpasses mirroring the filter side's discipline; the phase binds `_owner_definition`, calls `get_fields()` only after all owners are bound, materializes each generated input class as a module global of `django_strawberry_framework.orders.inputs` before `strawberry.Schema(...)` runs. [`examples/fakeshop/apps/library/`][fakeshop-library] grows `orders.py` (carrying `BranchOrder` / `ShelfOrder` / `BookOrder` / `LoanOrder` / `PatronOrder`) and `orders_genre.py` (carrying `GenreOrder` — cross-module fixture for the Layer-2 absolute-import-path test) wired through `Meta.orderset_class`; root resolvers accept `order_by:` via `order_input_type(<Name>Order)` annotations and call `<OwnerType>.get_queryset(...)` then optionally `<TypeName>Filter.apply_*` then `OrderSet.apply_*`. [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] grows exactly 14 live HTTP tests covering scalar ASC / scalar DESC_NULLS_LAST on `Book.subtitle` (per B3 of rev3) / forward-FK / reverse-FK with denormalized-multiplicity-pinned / M2M absolute-import-path RelatedOrder / flat-shorthand path (`shelf__code` → `shelfCode`) / filter + order composition / optimizer cooperation / root `get_queryset` honoring / split-pair active-input-only scalar `check_<field>_permission` (denies-for-active + quiet-for-inactive) / active-branch relation-level permission gate (`check_shelves_permission` per H3 of rev3) / multi-field priority via list-element ordering / empty-list no-op / null-direction no-op. Spec: `docs/spec-028-orders-0_0_8.md`. After this card moves to Done, `0.0.9` follow-up cards can start; no version files change here unless the maintainer explicitly gives the version-bump command.

#### Card references

- Related: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField #"order_by"` — connection field accepts an `order_by` argument that composes through `django_filters.OrderingFilter` declared on the FilterSet. Graphene has no separate ordering primitive; ⚛️ parity is met by the filter subsystem (`DONE-027-0.0.8`) rather than this card. -> `DONE-027-0.0.8` - Filtering subsystem
- Related: second-largest `0.0.8` card. A leaner mirror of `DONE-027-0.0.8`: five of the six lazy-resolution layers carry over, no operator-bag/lookup surface, 🍓-only parity. New `orders/` subpackage + `docs/spec-028-orders-0_0_8.md` + mirrored tests. Layer 6 (dynamic OrderSet generation) has no cookbook counterpart — the one genuinely fresh design decision. -> `DONE-027-0.0.8` - Filtering subsystem

<a id="filtering_subsystem"></a>
### [DONE-027-0.0.8 - Filtering subsystem](KANBAN.html#filtering_subsystem)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: XL
- Labels: `example-app`, `filters`, `graphql-api`, `public-api`
- Spec: [spec-027-filters-0_0_8.md](docs/SPECS/spec-027-filters-0_0_8.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter) | shipped (`0.0.8`) |
| [`Meta.filterset_class`](docs/GLOSSARY.md#metafilterset_class) | shipped (`0.0.8`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) | shipped (`0.0.3`) |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [Queryset diffing](docs/GLOSSARY.md#queryset-diffing) | shipped (`0.0.3`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Choice enum generation](docs/GLOSSARY.md#choice-enum-generation) | shipped (`0.0.1`) |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Specialized scalar conversions](docs/GLOSSARY.md#specialized-scalar-conversions) | shipped (`0.0.6`) |
| [`BigInt` scalar](docs/GLOSSARY.md#bigint-scalar) | shipped (`0.0.6`) |
| [Input type generation](docs/GLOSSARY.md#input-type-generation) | shipped (`0.0.11`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`AggregateSet`](docs/GLOSSARY.md#aggregateset) | planned for `0.1.3` |
| [`get_child_queryset`](docs/GLOSSARY.md#get_child_queryset) | planned for `0.1.3` |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`Meta.search_fields`](docs/GLOSSARY.md#metasearch_fields) | planned for `0.1.2` |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [Schema export management command](docs/GLOSSARY.md#schema-export-management-command) | shipped (`0.0.7`) |
| [`DjangoConnection`](docs/GLOSSARY.md#djangoconnection) | shipped (`0.0.9`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [`Meta.fields_class`](docs/GLOSSARY.md#metafields_class) | planned for `0.1.1` |
| [`Meta.aggregate_class`](docs/GLOSSARY.md#metaaggregate_class) | planned for `0.1.3` |
| [`Meta.orderset_class`](docs/GLOSSARY.md#metaorderset_class) | shipped (`0.0.8`) |
| [`RelatedAggregate`](docs/GLOSSARY.md#relatedaggregate) | planned for `0.1.3` |
| [`RelatedOrder`](docs/GLOSSARY.md#relatedorder) | shipped (`0.0.8`) |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [`filter_input_type`](docs/GLOSSARY.md#filter_input_type) | shipped (`0.0.8`) |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/conf.py`](django_strawberry_framework/conf.py)
- [`django_strawberry_framework/exceptions.py`](django_strawberry_framework/exceptions.py)
- [`django_strawberry_framework/filters/__init__.py`](django_strawberry_framework/filters/__init__.py)
- [`django_strawberry_framework/filters/base.py`](django_strawberry_framework/filters/base.py)
- [`django_strawberry_framework/filters/factories.py`](django_strawberry_framework/filters/factories.py)
- [`django_strawberry_framework/filters/inputs.py`](django_strawberry_framework/filters/inputs.py)
- [`django_strawberry_framework/filters/sets.py`](django_strawberry_framework/filters/sets.py)
- [`django_strawberry_framework/list_field.py`](django_strawberry_framework/list_field.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/scalars.py`](django_strawberry_framework/scalars.py)
- [`django_strawberry_framework/sets_mixins.py`](django_strawberry_framework/sets_mixins.py)
- [`django_strawberry_framework/types/__init__.py`](django_strawberry_framework/types/__init__.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)
- [`django_strawberry_framework/types/relay.py`](django_strawberry_framework/types/relay.py)

#### Planning note

shipped

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField.resolve_queryset` instantiates the type's `Meta.filterset_class` with the GraphQL args as `data`, calls `filterset.is_valid()`, and returns `filterset.qs` (raising `ValidationError` from `filterset.form.errors` otherwise) — this is the same filterset-driven, validation-gated queryset narrowing this card ships, so the graphene_django parity is required.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/filters.py::apply` runs `process_filters(...)` over a strawberry filter type and applies the resulting `Q` via `queryset.filter(q)`, with `StrawberryDjangoFieldFilters.arguments` auto-deriving the `filters:` argument from the type definition — the consumer-facing filter-input surface this card mirrors, making the strawberry_django parity required.

#### Other

- both upstreams ship a FilterSet / filter surface; `django-graphene-filters` is the cookbook source.
- the milestone anchor: six-layer lazy-resolution filtering pipeline, `FilterSet` / `RelatedFilter` / `Meta.filterset_class`, parity-floor filter primitives, finalizer phase-2.5 wiring, 14 live HTTP tests.

<a id="scalar_conversion_end_to_end_coverage_in_the_fakeshop_example"></a>
### [DONE-026-0.0.7 - Scalar conversion end-to-end coverage in the fakeshop example](KANBAN.html#scalar_conversion_end_to_end_coverage_in_the_fakeshop_example)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Low
- Status: Shipped
- Relative size: M
- Labels: `example-app`, `graphql-api`, `scalars`, `tests`
- Spec: [spec-026-scalar_conversion_fakeshop-0_0_7.md](docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`BigInt` scalar](docs/GLOSSARY.md#bigint-scalar) | shipped (`0.0.6`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |

#### Planning note

shipped

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py` converts the full Django field set to GraphQL scalars via singledispatch: `convert_big_int_field` (`BigIntegerField → graphene.BigInt`), `convert_field_to_uuid` (`UUIDField`), `convert_json_field_to_string` (`JSONField`), `convert_datetime_to_string`/`convert_date_to_string`, `convert_field_to_decimal`. This card moves the framework's equivalent numeric/date/JSON/UUID converter rows to live `/graphql/` HTTP coverage in both nullable and non-null shapes (incl. a real `BigIntegerField` on `Patron`), a direct match against graphene-django's scalar-conversion feature, justifying the graphene_django required claim.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py::field_type_map` maps the same set (`BigIntegerField → int`, `DateField → datetime.date`, `DateTimeField → datetime.datetime`, `DecimalField → decimal.Decimal`, `UUIDField → uuid.UUID`, `JSONField → strawberry.scalars.JSON`); this card's `ScalarSpecimen`/`NullableScalarSpecimen` example app plus eight live HTTP tests exercise the framework's equivalent conversion end-to-end in both shapes, a direct match justifying the strawberry_django required claim. (Both claims pre-exist and are kept; the card is example/test coverage but the behavior under test is genuine scalar-conversion parity, not pure housekeeping.)

#### Other

- both upstreams ship scalar conversion for the full numeric / date / JSON / UUID set; this card moves those converter rows to live `/graphql/` HTTP coverage in both nullable and non-null shapes.
- new `apps.scalars` example app (paired non-null / nullable models, self-FK + cross-model `SET_NULL` FK) + eight live HTTP tests + a real-domain `BigIntegerField` on `Patron`.
- `ScalarSpecimen` — every scalar field non-null, exposed via `ScalarSpecimenType`. Adds an intra-model self-FK `parent` (`related_name="children"`) so the example exercises self-referential FK planning under the optimizer.
- `NullableScalarSpecimen` — every scalar field nullable (`null=True, blank=True`), exposed via `NullableScalarSpecimenType`. Adds a cross-model FK `partner: ForeignKey(ScalarSpecimen, on_delete=SET_NULL, related_name="nullable_partners")` — the only `SET_NULL` ondelete in the example tree, and the only cross-model FK in the scalars app.
- The pairing is deliberate (not a single model with paired fields). It exercises **upstream code paths no other example app reaches**: Django's two-`CreateModel` initial migration path, the registry / `finalize_django_types()` resolving sibling `DjangoType` classes in one app, Strawberry type registration across sibling types in one schema build, the optimizer planning across two managed models in one query, and `SET_NULL` ondelete behavior.
- `apps.scalars.schema` composes two root resolvers (`all_scalar_specimens`, `all_nullable_scalar_specimens`) into the project root `Query` at [`examples/fakeshop/config/schema.py`][example-schema]; `ScalarsConfig` lands in `INSTALLED_APPS` at [`examples/fakeshop/config/settings.py`][settings].
- Full non-null wire-format sweep covering every field on `ScalarSpecimen`
- Signed-negative `BigInt` round-trip
- `BigInt`-at-zero edge case
- Schema introspection asserting `BigInt` converter resolves correctly in both shapes (`NON_NULL` on `ScalarSpecimenType`; bare `SCALAR` on `NullableScalarSpecimenType`)
- All-NULL nullable wire format covering every nullable converter branch
- Cross-model `partner` FK linkage round-trip
- Reverse-FK `nullablePartners` exposure
- Self-FK `parent` / `children` traversal

<a id="warning_free_scalar_registration_via_strawberryconfigscalar_map"></a>
### [DONE-025-0.0.7 - Warning-free scalar registration via `StrawberryConfig.scalar_map`](KANBAN.html#warning_free_scalar_registration_via_strawberryconfigscalar_map)

- Priority: Medium
- Severity: Medium
- Status: Shipped
- Relative size: S
- Labels: `config`, `internal`, `public-api`, `scalar-map`, `scalars`
- Spec: [spec-025-scalar_map_helper-0_0_7.md](docs/SPECS/spec-025-scalar_map_helper-0_0_7.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`BigInt` scalar](docs/GLOSSARY.md#bigint-scalar) | shipped (`0.0.6`) |
| [Specialized scalar conversions](docs/GLOSSARY.md#specialized-scalar-conversions) | shipped (`0.0.6`) |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |
| [`Upload` scalar](docs/GLOSSARY.md#upload-scalar) | shipped (`0.0.11`) |
| [`DjangoFileType`](docs/GLOSSARY.md#djangofiletype) | shipped (`0.0.11`) |
| [`DjangoImageType`](docs/GLOSSARY.md#djangoimagetype) | shipped (`0.0.11`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`AggregateSet`](docs/GLOSSARY.md#aggregateset) | planned for `0.1.3` |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/scalars.py`](django_strawberry_framework/scalars.py)

#### Planning note

shipped

#### Other

- package-specific scalar-registration plumbing (`StrawberryConfig.scalar_map` via `strawberry_config()`); not an upstream-parity primitive.
- `strawberry_config()` factory registering `BigInt` via `scalar_map` and removing the deprecation-suppression block; a documented breaking change in alpha.

<a id="django_trac_37064_hardening_safe_wrap_connection_method"></a>
### [DONE-024-0.0.7 - Django Trac #37064 hardening + `safe_wrap_connection_method`](KANBAN.html#django_trac_37064_hardening_safe_wrap_connection_method)

- Priority: Low
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `django-integration`, `hardening`, `internal`
- Spec: [spec-024-django_trac_37064_hardening-0_0_7.md](docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`safe_wrap_connection_method`](docs/GLOSSARY.md#safe_wrap_connection_method) | shipped (`0.0.7`) |
| [Django Trac #37064 hardening](docs/GLOSSARY.md#django-trac-37064-hardening) | shipped (`0.0.7`) |

#### Package files

- [`django_strawberry_framework/_django_patches.py`](django_strawberry_framework/_django_patches.py)
- [`django_strawberry_framework/apps.py`](django_strawberry_framework/apps.py)
- `django_strawberry_framework/test/__init__.py` (historical)
- `django_strawberry_framework/test/_wrap.py` (historical)

#### Planning note

shipped

#### Other

- defensive hardening unique to this package; neither upstream ships a Django Trac #37064 patch.
- two-half defense for Trac #37064: a package-level unwrap patch (auto-applied at app-load) plus the cooperative `safe_wrap_connection_method` helper + tests.

<a id="multi_database_cooperation_contract"></a>
### [DONE-023-0.0.7 - Multi-database cooperation contract](KANBAN.html#multi_database_cooperation_contract)

- Priority: Low
- Parity: 🍓 strawberry-graphql-django (Parity-adjacent)
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `multi-db`, `optimizer`, `tests`
- Spec: [spec-023-multi_db-0_0_7.md](docs/SPECS/spec-023-multi_db-0_0_7.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |
| [Queryset diffing](docs/GLOSSARY.md#queryset-diffing) | shipped (`0.0.3`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [Django `AppConfig`](docs/GLOSSARY.md#django-appconfig) | shipped (`0.0.7`) |
| [Schema export management command](docs/GLOSSARY.md#schema-export-management-command) | shipped (`0.0.7`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [`AggregateSet`](docs/GLOSSARY.md#aggregateset) | planned for `0.1.3` |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) | shipped (`0.0.3`) |

#### Planning note

shipped

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py` builds N+1-avoidance plans out of `django.db.models.Prefetch` objects (imported at line 18; `prefetch_related: list[PrefetchType]`) but specifies no multi-database cooperation contract (a grep of the module for `.using(`, `_db`, `router`, `db_for_read` returns nothing). This card pins that exact seam for the framework's `Prefetch`-based optimizer — `OptimizerHint.prefetch(Prefetch(queryset=...using('shard_b')))` round-tripping with `_db` intact through plan construction (`tests/optimizer/test_multi_db.py`) — so it is adjacent: it underpins/extends the same prefetch-plan subsystem strawberry-graphql-django owns, adding a multi-DB guarantee the upstream leaves unspecified.
- graphene-django has no comparable prefetch-plan optimizer and likewise no multi-DB handling (grep of `graphene_django/*.py` for `.using(`/`_db`/`router`/`db_for_read` returns nothing), so no graphene_django claim is honest here; the contract this card pins (`.using()` preservation, router-aware FK-id stubs, `Prefetch._db` round-trip) is purely a function of the framework's optimizer, which is the strawberry-graphql-django-comparable subsystem.

#### Other

- multi-DB is a Django capability neither upstream specifies a contract around (⚛️&🍓 parity-adjacent); pinning ours smooths the migrant story.
- pin the multi-DB cooperation contract (router-aware FK-id stubs, `.using()` preservation, `Prefetch` `_db` round-trip) + tests; zero production-code change.

<a id="schema_export_management_command"></a>
### [DONE-022-0.0.7 - Schema export management command](KANBAN.html#schema_export_management_command)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `management-command`, `public-api`, `schema`
- Spec: [spec-022-export_schema-0_0_7.md](docs/SPECS/spec-022-export_schema-0_0_7.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Schema export management command](docs/GLOSSARY.md#schema-export-management-command) | shipped (`0.0.7`) |
| [Django `AppConfig`](docs/GLOSSARY.md#django-appconfig) | shipped (`0.0.7`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [`DjangoGraphQLProtocolRouter`](docs/GLOSSARY.md#djangographqlprotocolrouter) | planned for `0.0.14` |
| [Debug-toolbar middleware](docs/GLOSSARY.md#debug-toolbar-middleware) | planned for `0.0.14` |
| [Response-extensions debug middleware](docs/GLOSSARY.md#response-extensions-debug-middleware) | planned for `0.0.14` |
| [`TestClient`](docs/GLOSSARY.md#testclient) | planned for `0.0.14` |
| [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) | planned for `0.0.14` |

#### Package files

- [`django_strawberry_framework/management/__init__.py`](django_strawberry_framework/management/__init__.py)
- [`django_strawberry_framework/management/commands/__init__.py`](django_strawberry_framework/management/commands/__init__.py)
- [`django_strawberry_framework/management/commands/export_schema.py`](django_strawberry_framework/management/commands/export_schema.py)
- [`django_strawberry_framework/scalars.py`](django_strawberry_framework/scalars.py)

#### Planning note

shipped

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/management/commands/export_schema.py::Command` is the `manage.py export_schema` command: positional `schema` arg, optional `--path`, `import_module_symbol` resolution, `isinstance(..., strawberry.Schema)` guard, SDL via `print_schema`, and `CommandError` paths. This card ships the same-named command with the identical positional `schema` / `--path` / `print_schema` / `CommandError` contract, a direct feature match justifying the strawberry_django required claim.
- graphene-django's nearest analog `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/management/commands/graphql_schema.py::Command` is a deliberately different `graphql_schema` command (`--schema`/`--out`/`--indent`/`--watch`, JSON-or-`.graphql` output via `schema.introspect()`), which the card explicitly flags as parity-adjacent and not borrowed; correctly excluded from the claim set.

#### Other

- strawberry-graphql-django ships `manage.py export_schema`; graphene-django's different `graphql_schema` command is parity-adjacent (deliberately not borrowed).
- one management command (positional `schema`, `--path`, SDL via `print_schema`, `CommandError` paths) + tests.

<a id="appspy_and_django_app_config"></a>
### [DONE-021-0.0.7 - `apps.py` and Django app config](KANBAN.html#appspy_and_django_app_config)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Low
- Status: Shipped
- Relative size: XS
- Labels: `django-app`, `packaging`
- Spec: [spec-021-apps-0_0_7.md](docs/SPECS/spec-021-apps-0_0_7.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Django `AppConfig`](docs/GLOSSARY.md#django-appconfig) | shipped (`0.0.7`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [Schema export management command](docs/GLOSSARY.md#schema-export-management-command) | shipped (`0.0.7`) |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [`DjangoGraphQLProtocolRouter`](docs/GLOSSARY.md#djangographqlprotocolrouter) | planned for `0.0.14` |
| [Debug-toolbar middleware](docs/GLOSSARY.md#debug-toolbar-middleware) | planned for `0.0.14` |
| [Response-extensions debug middleware](docs/GLOSSARY.md#response-extensions-debug-middleware) | planned for `0.0.14` |
| [`TestClient`](docs/GLOSSARY.md#testclient) | planned for `0.0.14` |
| [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) | planned for `0.0.14` |

#### Package files

- [`django_strawberry_framework/apps.py`](django_strawberry_framework/apps.py)

#### Planning note

shipped

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/apps.py::StrawberryDjangoConfig` is a minimal `AppConfig` (just `name` and `verbose_name`) enabling `INSTALLED_APPS`-driven discovery; this card ships the equivalent `DjangoStrawberryFrameworkConfig` `AppConfig`, a direct feature match that justifies the strawberry_django required claim.

#### Other

- both upstreams ship an `apps.py` `AppConfig` for `INSTALLED_APPS`-driven discovery.
- tiny `AppConfig` (two class attributes, no `ready()` body in 0.0.7) + tests.

<a id="djangolistfield_non_relay_list"></a>
### [DONE-020-0.0.7 - `DjangoListField` (non-Relay list)](KANBAN.html#djangolistfield_non_relay_list)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Severity: Medium
- Status: Shipped
- Relative size: M
- Labels: `graphql-api`, `list-field`, `optimizer`, `public-api`
- Spec: [spec-020-list_field-0_0_7.md](docs/SPECS/spec-020-list_field-0_0_7.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [`BigInt` scalar](docs/GLOSSARY.md#bigint-scalar) | shipped (`0.0.6`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [`DjangoConnection`](docs/GLOSSARY.md#djangoconnection) | shipped (`0.0.9`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [Queryset diffing](docs/GLOSSARY.md#queryset-diffing) | shipped (`0.0.3`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/apps.py`](django_strawberry_framework/apps.py)
- [`django_strawberry_framework/list_field.py`](django_strawberry_framework/list_field.py)

#### Planning note

shipped

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/fields.py::DjangoListField` is graphene-django's non-Relay list primitive: it wraps the underlying type in `List(NonNull(...))`, exposes `get_manager()`/`get_queryset` cooperation, and coerces `Manager`/`QuerySet` results in `list_resolver`. This card ships the same-named `DjangoListField` factory (`Manager → QuerySet` coercion, sync/async `get_queryset`, outer-list nullability) for the Strawberry stack; required because it is a direct feature match against a primitive strawberry-graphql-django does not provide.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py::field_type_map` maps only relation kinds (`ManyToManyField`, `ManyToOneRel`) to `list[DjangoModelType]` and offers no standalone consumer-facing list field; this confirms the card's premise that strawberry-graphql-django has no non-Relay list-field primitive, so the single `graphene_django` required claim is the honest sole match.

#### Other

- graphene-django ships `DjangoListField`; strawberry-graphql-django has no non-Relay list-field primitive.
- `DjangoListField` factory: default + consumer resolver, `Manager → QuerySet` coercion, sync/async `get_queryset`, outer-list nullability, root-gated optimizer cooperation.

<a id="consumer_override_semantics_scalar_fields"></a>
### [DONE-019-0.0.6 - Consumer override semantics (scalar fields)](KANBAN.html#consumer_override_semantics_scalar_fields)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Shipped
- Relative size: L
- Labels: `public-api`, `relay`, `scalars`, `types`
- Spec: [spec-019-consumer_overrides_scalar-0_0_6.md](docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`BigInt` scalar](docs/GLOSSARY.md#bigint-scalar) | shipped (`0.0.6`) |
| [Choice enum generation](docs/GLOSSARY.md#choice-enum-generation) | shipped (`0.0.1`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) | shipped |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Scalar field override semantics](docs/GLOSSARY.md#scalar-field-override-semantics) | shipped (`0.0.6`) |
| [Specialized scalar conversions](docs/GLOSSARY.md#specialized-scalar-conversions) | shipped (`0.0.6`) |

#### Package files

- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)

#### Planning note

shipped

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::_process_type` only injects `strawberry.auto` for model fields lacking a consumer annotation (`for f in model_fields: if existing_annotations.get(f.name): continue`), so a consumer-authored scalar annotation is authoritative and is never overwritten by the synthesized field — exactly this card's consumer-annotation-overrides-synthesized contract — making the claim `required`; the adjacent `MAP_AUTO_ID_AS_GLOBAL_ID` guard that drops `id` from `model_fields` to avoid clobbering the relay `GlobalID` also mirrors this card's `relay.Node` `id`-collision handling.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py::DjangoObjectType.__init_subclass_with_meta__` yanks consumer-declared class-attribute fields via `yank_fields_from_attrs` alongside the auto-`construct_fields` model conversion, so a field a consumer declares on the type takes precedence over the auto-generated scalar — graphene_django supports the same consumer-authored scalar-override-on-a-model-type feature, so the claim is `required`.

#### Other

- both upstreams support consumer-authored scalar field overrides on model-backed types.
- annotation/assigned scalar-override contract (four-corner matrix), `relay.Node` `id`-collision rejection, cross-type choice-enum cache semantics.
- `DjangoType.__init_subclass__` collected `consumer_annotated_scalar_fields`
- `DjangoTypeDefinition` gained `consumer_annotated_scalar_fields: frozenset[str]`.
- The previously-skipped `test_consumer_annotation_overrides_synthesized`
- End-to-end test pinned the override surviving `strawberry.type(...)`
- **Consumer annotation overrides are authoritative.** `_build_annotations`'s
- **`relay.Node` `id` collision rejected at type-creation time.** A consumer
- No new public API. No `Meta.field_overrides = {...}`-style key. Opt-out
- 100% coverage was reached across `tests/types/test_definition_order.py`
- The four `consumer_*_fields` sets on `DjangoTypeDefinition`
- Resolver / metadata overrides for scalars stay on the assigned
- Type-annotation overrides are the consumer's responsibility for runtime

<a id="multiple_djangotypes_per_model_with_metaprimary"></a>
### [DONE-018-0.0.6 - Multiple DjangoTypes per model with `Meta.primary`](KANBAN.html#multiple_djangotypes_per_model_with_metaprimary)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Parity-adjacent)
- Severity: Medium
- Status: Shipped
- Relative size: L
- Labels: `optimizer`, `public-api`, `registry`, `types`
- Spec: [spec-018-meta_primary-0_0_6.md](docs/SPECS/spec-018-meta_primary-0_0_6.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Choice enum generation](docs/GLOSSARY.md#choice-enum-generation) | shipped (`0.0.1`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.name`](docs/GLOSSARY.md#metaname) | shipped |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [Schema audit](docs/GLOSSARY.md#schema-audit) | shipped (`0.0.3`) |

#### Package files

- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)

#### Planning note

shipped

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::_process_type` gives every Django type its own `is_type_of` closure returning `isinstance(obj, (cls, model))` (with a `get_strawberry_type_cast` short-circuit) and keeps no model-to-type registry at all, so multiple types can back the same model and disambiguation rides on `is_type_of`/`strawberry.cast` rather than an explicit primary flag; this card's registry storing many types per model with an explicit `Meta.primary` selection plus a finalize-time ambiguity audit extends and formalizes that implicit upstream behavior, making the link `adjacent`. graphene_django has no equivalent — `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/registry.py::Registry.register` stores exactly one type per model (`self._registry[cls._meta.model] = cls`), so no claim is made there.

#### Other

- 🍓 parity-adjacent (strawberry-graphql-django has an implicit primary-type concept via `is_type_of`; graphene-django ships no equivalent) — not required on either side.
- registry stores multiple types per model, `Meta.primary` flag, ambiguity audit at finalize, relation-deferral, optimizer origin-type threading.
- Registry stores multiple types per model (`_types: dict[Model, list[Type]]`).
- New `Meta.primary: bool` flag (default `False`); validated in `_validate_meta`.
- `registry.register(..., *, primary: bool = False) -> bool` and
- New registry surface: `primary_for(model)`, `types_for(model)`,
- `registry.get(model)` returns the primary if declared, else the single
- `finalize_django_types()` runs `audit_primary_ambiguity()` first: any
- Two primary types for the same model: rejected at registration time
- Relation conversion in `types/base.py` defers all **auto-synthesized**
- Optimizer planning threads the resolved origin Strawberry type from
- Schema audit (`optimizer/extension.py`) iterates every reachable
- `model_for_type` continues to work for any registered type so
- `DjangoTypeDefinition` gains `primary: bool = False`.
- 100% coverage across `tests/test_registry.py`, `tests/types/test_base.py`,
- Single-type-no-primary stays backward compatible: `registry.get(model)`
- `Meta.primary` is a per-class declaration, not a registry-level
- Already-shipped consumer relation overrides (direct annotation

<a id="deferred_scalar_conversions"></a>
### [DONE-017-0.0.6 - Deferred scalar conversions](KANBAN.html#deferred_scalar_conversions)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Shipped
- Relative size: M
- Labels: `converters`, `public-api`, `scalars`
- Spec: [spec-017-deferred_scalars-0_0_6.md](docs/SPECS/spec-017-deferred_scalars-0_0_6.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`BigInt` scalar](docs/GLOSSARY.md#bigint-scalar) | shipped (`0.0.6`) |
| [Choice enum generation](docs/GLOSSARY.md#choice-enum-generation) | shipped (`0.0.1`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) | shipped (`0.0.11`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) | shipped |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Scalar field override semantics](docs/GLOSSARY.md#scalar-field-override-semantics) | shipped (`0.0.6`) |
| [Specialized scalar conversions](docs/GLOSSARY.md#specialized-scalar-conversions) | shipped (`0.0.6`) |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |
| [`Upload` scalar](docs/GLOSSARY.md#upload-scalar) | shipped (`0.0.11`) |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/scalars.py`](django_strawberry_framework/scalars.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)

#### Planning note

shipped

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py::convert_big_int_field` maps `models.BigIntegerField` to graphene's `BigInt` scalar (defined at `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene/types/scalars.py::BigInt`), and the same module maps `models.JSONField`/`HStoreField` to `JSONString` and `ArrayField` to `List` — graphene_django ships a direct `BigIntegerField -> BigInt`-scalar conversion plus JSON/Array/HStore handlers matching this card, so the claim is `required`.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py::field_type_map` maps `json.JSONField` to `strawberry.scalars.JSON` and resolves `ArrayField` to a nested `list[...]` via `_resolve_array_field_type`, giving strawberry_django direct equivalents for this card's `JSONField -> strawberry.scalars.JSON` and `ArrayField` conversions; the same map routes `BigIntegerField`/`PositiveBigIntegerField` to plain `int` (no dedicated big-int scalar), so the JSON/Array conversion parity is the `required` anchor on this side.

#### Other

- both upstreams ship scalar conversion for `BigIntegerField` / `JSONField` / `HStoreField` / `ArrayField`, etc.
- `BigInt` scalar + strict parser/serializer, `JSONField` / `ArrayField` / `HStoreField` conversion, `SCALAR_MAP` value-type widening.
- Public `BigInt` scalar (`django_strawberry_framework/scalars.py`, `NewType`-based) with the Strawberry class-direct-to-`scalar()` `DeprecationWarning` suppressed at the definition site so consumers see no warning at import time.
- Strict `BigInt` parser via regex `^(0|-?[1-9][0-9]*)$` — rejects `bool`, `float`, empty / whitespace-padded strings, non-decimal strings, underscores, plus signs, leading zeroes, `-0`, and Unicode digits.
- Strict `BigInt` serializer — rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`.
- `BigIntegerField → BigInt` and `PositiveBigIntegerField → BigInt` in `SCALAR_MAP`. `BigAutoField` preserved as `int` (no override recourse at the time of DONE-013; annotation-override recourse now available via `DONE-019-0.0.6`).
- `JSONField → strawberry.scalars.JSON` in `SCALAR_MAP`.
- `ArrayField` and `HStoreField` mapped via sentinel-guarded branches in `convert_scalar`. `HStoreField` not added to `SCALAR_MAP`.
- `ArrayField` rejects nested arrays and outer `choices` with `ConfigurationError`.
- `SCALAR_MAP`'s declared value type widened from `dict[type[models.Field], type]` to `dict[type[models.Field], Any]`.
- `BigInt` added to `django_strawberry_framework.__all__`; `tests/base/test_init.py`'s pinned `__all__` and `__version__` assertions updated.
- Atomic version-bump quintet: `pyproject.toml`, `__init__.py`, `tests/base/test_init.py`, `docs/GLOSSARY.md` package-version line, `uv.lock`.
- 100% coverage via `tests/test_scalars.py` (new flat file) and `tests/types/test_converters.py` (extended). Includes a `test_package_import_does_not_emit_strawberry_deprecation_warning` guard so future regressions to the suppression are explicit.
- Docs: `docs/GLOSSARY.md`, `docs/README.md`, `README.md`, `docs/TREE.md`, `TODAY.md`, `CHANGELOG.md`.
- The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` is suppressed at the definition site (tight `warnings.catch_warnings()` filter). The package import surface is therefore clean. Migration to a `StrawberryConfig.scalar_map`-based design is roadmapped as `DONE-025-0.0.7` — that path is a real public-API change (consumers using `BigInt` directly will merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`), not an internal-only refactor.

#### Card references

- Related: `BigAutoField` preserved as `int` before scalar override recourse shipped in `DONE-019-0.0.6`. -> `DONE-019-0.0.6` - Consumer override semantics (scalar fields)
- Related: The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` is suppressed at the definition site (tight `warnings.catch_warnings()` filter). The package import surface is therefore clean. Migration to a `StrawberryConfig.scalar_map`-based design is roadmapped as `DONE-025-0.0.7` — that path is a real public-API change (consumers using `BigInt` directly will merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`), not an internal-only refactor. -> `DONE-025-0.0.7` - Warning-free scalar registration via `StrawberryConfig.scalar_map`

<a id="fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement"></a>
### [DONE-016-0.0.6 - `FieldMeta` single-source-of-truth consolidation and mirror retirement](KANBAN.html#fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Parity-adjacent)
- Severity: Medium
- Status: Shipped
- Relative size: M
- Labels: `cleanup`, `field-meta`, `metadata`, `optimizer`, `types`
- Spec: [spec-016-fieldmeta_consolidation-0_0_6.md](docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |

#### Package files

- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/field_meta.py`](django_strawberry_framework/optimizer/field_meta.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)

#### Planning note

shipped

#### Scope

- **SSoT consolidation.** Three reader sites now read `FieldMeta` from the canonical source on `DjangoTypeDefinition.field_map`:
- `django_strawberry_framework/types/base.py:_record_pending_relation`
- `django_strawberry_framework/types/converters.py:resolved_relation_annotation`
- `django_strawberry_framework/types/resolvers.py:_make_relation_resolver`
- **Mirror retirement.** `DjangoType.__init_subclass__` no longer writes the legacy class-attribute mirrors. The optimizer reads from `registry.get_definition(type_cls)` directly at all four former reader sites:
- `optimizer/walker.py:_resolve_field_map`
- `optimizer/walker.py:_walk_selections` (hints read)
- `optimizer/extension.py:_collect_schema_reachable_types`
- `optimizer/extension.py:check_schema`
- All `TODO(spec-fieldmeta-*)` source anchors removed.
- 100% package coverage maintained; no consumer-visible API change.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py::_get_model_hints` sources per-type optimization metadata from a single canonical place — `getattr(get_django_definition(object_definition.origin), 'store', None)` (and per-field `getattr(field, 'store', None)`), where `get_django_definition` (`/Users/riordenweber/projects/strawberry-django-main/strawberry_django/utils/typing.py::get_django_definition`) returns the one `__strawberry_django_definition__` on the type rather than any parallel copy; this card's retirement of the legacy class-attribute mirrors so the optimizer reads `FieldMeta` only from `DjangoTypeDefinition.field_map` via `registry.get_definition(...)` aligns the framework's metadata-sourcing posture with strawberry_django's single-definition design, but it is an internal SSoT refactor with no consumer-visible surface, so the link is `adjacent`, not `required`.

#### Why it matters

- Three reader sites were re-deriving relation shape via `relation_kind(field)` + raw `getattr(field, ...)` instead of reading the `FieldMeta` already on `DjangoTypeDefinition.field_map` — duplicating logic and creating drift surface for any future relation-flag addition.
- `DjangoType.__init_subclass__` was writing legacy class-attribute mirrors (`cls._optimizer_field_map`, `cls._optimizer_hints`) that survived `registry.clear()`, then four optimizer sites read those mirrors instead of the canonical `DjangoTypeDefinition`. Two parallel sources of field metadata with no enforced consistency.

#### Other

- internal metadata-architecture refactor; no consumer-visible API change.
- consolidate field metadata onto `DjangoTypeDefinition` (single source of truth) and retire legacy class-attribute mirrors across ~7 reader sites.
- Commit `de35a62` (`refactor(types,optimizer): consolidate metadata onto DjangoTypeDefinition`).
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/extension.py`
- `CHANGELOG.md` (under `[Unreleased] → Changed`)
- Originally tracked as `BACKLOG.md` item 35 ("`FieldMeta` single-source-of-truth consolidation and mirror retirement"). Promoted to a DONE card and removed from `BACKLOG.md` when the work shipped — per `BACKLOG.md`'s "graduate into a `KANBAN.md` card when scheduled" workflow. This is the first `BACKLOG.md` item to graduate; the precedent for shipped items: strike-through with SHIPPED status is fine while the item awaits a release; once a release is imminent, move the item to a `KANBAN.md` `DONE` card and delete it from `BACKLOG.md` so the strategic-differentiation file doesn't keep pointing at completed architecture debt.
- The consolidation eliminates ~7 sites of duplicated relation-shape logic and removes legacy class-attribute residue that previously survived `registry.clear()`. Single source of truth for field metadata reduces drift surface whenever Django adds a new relation flag or changes a descriptor attribute.
- Internal refactor only; no `Meta` key changes, no public surface changes, no consumer-visible behavior changes. Existing tests pass without modification.

<a id="005_relay_interfaces_and_node_foundation"></a>
### [DONE-015-0.0.5 - 0.0.5 Relay interfaces and Node foundation](KANBAN.html#005_relay_interfaces_and_node_foundation)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `public-api`, `relay`, `types`
- Spec: [spec-015-relay_interfaces-0_0_5.md](docs/SPECS/spec-015-relay_interfaces-0_0_5.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [Choice enum generation](docs/GLOSSARY.md#choice-enum-generation) | shipped (`0.0.1`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) | shipped (`0.0.3`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/conf.py`](django_strawberry_framework/conf.py)
- [`django_strawberry_framework/optimizer/_context.py`](django_strawberry_framework/optimizer/_context.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/field_meta.py`](django_strawberry_framework/optimizer/field_meta.py)
- [`django_strawberry_framework/optimizer/hints.py`](django_strawberry_framework/optimizer/hints.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/__init__.py`](django_strawberry_framework/types/__init__.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)
- [`django_strawberry_framework/types/relations.py`](django_strawberry_framework/types/relations.py)
- [`django_strawberry_framework/types/relay.py`](django_strawberry_framework/types/relay.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)
- [`django_strawberry_framework/utils/__init__.py`](django_strawberry_framework/utils/__init__.py)
- [`django_strawberry_framework/utils/relations.py`](django_strawberry_framework/utils/relations.py)
- [`django_strawberry_framework/utils/typing.py`](django_strawberry_framework/utils/typing.py)

#### Planning note

shipped

#### Scope

- `Meta.interfaces` accepted end-to-end for any Strawberry interface.
- Four Relay node resolver defaults injected when `relay.Node` is declared (canonical order: `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes`); consumer-declared overrides are preserved via Strawberry's `__func__` identity test.
- Automatic synthesized `id: int!` suppression when `relay.Node` is in `Meta.interfaces`; the Relay-supplied `id: GlobalID!` is used instead.
- `is_type_of` injection is unconditional for every `DjangoType` (Relay-declared or not); consumer-declared `is_type_of` is preserved.
- Models whose primary key is a Django 5.2+ `CompositePrimaryKey` raise `ConfigurationError` at finalization; declare an explicit `id: relay.NodeID[...]` annotation or remove `relay.Node` from `Meta.interfaces` to remediate.
- Both sync and async paths for `_resolve_node_default` / `_resolve_nodes_default`; async `get_queryset` hooks are awaited on the async branch and rejected with `ConfigurationError` on the sync branch.
- `Meta.interfaces` promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`.
- Package version bumped to `0.0.5` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock`.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::_process_type` injects the four relay defaults (`resolve_id`, `resolve_id_attr`, `resolve_node`, `resolve_nodes`) when `issubclass(cls, relay.Node)` and preserves a consumer-declared resolver via the `existing_resolver.__func__ is getattr(relay.Node, attr).__func__` identity test, and unconditionally installs `is_type_of` unless already in `cls.__dict__` — strawberry_django ships exactly this Node-wiring contract, so the card's `relay.Node`-default injection plus `__func__`-preserving override and unconditional `is_type_of` is `required` against it.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py::DjangoObjectType` accepts a `Meta.interfaces` tuple, auto-enables a Relay `Connection` when any interface `issubclass(interface, Node)`, and provides `get_node`/`get_queryset`/`resolve_id`/`is_type_of` for Node-backed model types (with the global `id` resolved as a `GlobalID` via `graphene.relay.node.AbstractNode`) — graphene_django offers the same end-to-end `Meta.interfaces`-with-Node feature this card matches, so the claim is `required`.

#### Other

- both upstreams ship Relay Node interfaces; this shipped our 🍓-shaped Relay Node integration.
- Relay Node foundation: `Meta.interfaces`, four `resolve_*` defaults, `id: GlobalID!` suppression, `is_type_of` injection, composite-PK rejection, sync + async node resolution.
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/relay.py`
- `django_strawberry_framework/types/finalizer.py`
- `tests/types/test_relay_interfaces.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_relay_id_projection.py`
- `tests/test_registry.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `examples/fakeshop/apps/library/schema.py` (`GenreType` declares `Meta.interfaces = (relay.Node,)`)
- `CHANGELOG.md`
- `docs/GLOSSARY.md`
- `docs/README.md`
- `TODAY.md`
- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- Borrowed patterns from `strawberry-django` (spec "Borrowing posture", Decision 3). The override discriminator triad stays distinct across the three injection sites: `__dict__` membership for `is_type_of`, tuple membership for id suppression, `__func__` identity for the four `resolve_*` defaults.
- `Meta.interfaces` is the first `0.0.4`-reserved `DjangoTypeDefinition` slot that ships end-to-end through finalizer phase 2.5; subsequent Layer 3 subsystems plug into the same architectural seam.

<a id="move_test_fixture_out_of_example_settings"></a>
### [DONE-014-0.0.4 - Move test fixture out of example settings](KANBAN.html#move_test_fixture_out_of_example_settings)

- Priority: Low
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `cleanup`, `example-app`, `internal`, `tests`
- Spec: [spec-014-testing_shift-0_0_4.md](docs/SPECS/spec-014-testing_shift-0_0_4.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Choice enum generation](docs/GLOSSARY.md#choice-enum-generation) | shipped (`0.0.1`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |

#### Planning note

shipped

#### Scope

- Removed `tests.fixtures.apps.TestsCardinalityConfig` from the example project.
- Removed the old unmanaged cardinality fixture files under `tests/fixtures/`.
- Package tests that need OneToOne / M2M / cardinality coverage now use real models from `examples/fakeshop/apps/library/`.

#### Other

- test hygiene.
- remove the `tests.fixtures.apps` fixture app + unmanaged cardinality fixtures; switch package tests to real `library` models.
- `examples/fakeshop/config/settings.py`
- `examples/fakeshop/apps/library/models.py`
- `docs/SPECS/spec-014-testing_shift-0_0_4.md`
- `AGENTS.md`
- `docs/TREE.md`

<a id="real_m2m_coverage"></a>
### [DONE-013-0.0.4 - Real M2M coverage](KANBAN.html#real_m2m_coverage)

- Priority: Medium
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `example-app`, `internal`, `m2m`, `tests`
- Spec: [spec-013-real_m2m_coverage-0_0_4.md](docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |

#### Package files

- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)

#### Planning note

shipped

#### Scope

- Replaced test-only M2M/cardinality fixtures with real managed models in the `library` example app.
- Added package-level and HTTP-level coverage for M2M traversal and optimizer planning.

#### Other

- test hygiene.
- replace test-only M2M / cardinality fixtures with real `library` models; add package + HTTP coverage.
- `examples/fakeshop/apps/library/models.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `tests/types/test_definition_order.py`
- `tests/optimizer/test_definition_order.py`

<a id="004_version_and_release_alignment"></a>
### [DONE-012-0.0.4 - 0.0.4 version and release alignment](KANBAN.html#004_version_and_release_alignment)

- Priority: Low
- Severity: Low
- Status: Shipped
- Relative size: XS
- Labels: `internal`, `release`, `versioning`
- Spec: [spec-012-version_release_alignment-0_0_4.md](docs/SPECS/spec-012-version_release_alignment-0_0_4.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |

#### Planning note

shipped

#### Scope

- Package metadata, runtime version, lockfile, tests, and changelog now agree on `0.0.4`.
- The changelog entry is condensed for the alpha release and covers the actual commit range through 2026-05-08.

#### Other

- release housekeeping (version alignment).
- align package metadata / runtime version / lockfile / tests / changelog on `0.0.4`.
- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`

<a id="stale_placeholder_cleanup"></a>
### [DONE-011-0.0.4 - Stale placeholder cleanup](KANBAN.html#stale_placeholder_cleanup)

- Priority: Low
- Severity: Low
- Status: Shipped
- Relative size: XS
- Labels: `cleanup`, `docs`, `internal`, `tests`
- Spec: [spec-011-stale_placeholder_cleanup-0_0_4.md](docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [Scalar field override semantics](docs/GLOSSARY.md#scalar-field-override-semantics) | shipped (`0.0.6`) |

#### Planning note

shipped

#### Scope

- Replaced stale M2M and forward-reference skips with definition-order tests.
- Kept the remaining scalar override skip documented as a separate scalar-field concern under `DONE-019-0.0.6`.

#### Other

- internal test/doc cleanup.
- replace stale M2M / forward-reference skips with definition-order tests.
- `tests/types/test_definition_order.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_definition_order.py`
- `DONE-019-0.0.6`

#### Card references

- Related: Kept the remaining scalar override skip documented as a separate scalar-field concern under `DONE-019-0.0.6`. -> `DONE-019-0.0.6` - Consumer override semantics (scalar fields)

<a id="004_foundation_slice_definition_order_independence"></a>
### [DONE-010-0.0.4 - 0.0.4 foundation slice (definition-order independence)](KANBAN.html#004_foundation_slice_definition_order_independence)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Parity-adjacent)
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `finalizer`, `registry`, `relations`, `types`
- Spec: [spec-010-foundation-0_0_4.md](docs/SPECS/spec-010-foundation-0_0_4.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Choice enum generation](docs/GLOSSARY.md#choice-enum-generation) | shipped (`0.0.1`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [Schema audit](docs/GLOSSARY.md#schema-audit) | shipped (`0.0.3`) |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/field_meta.py`](django_strawberry_framework/optimizer/field_meta.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/__init__.py`](django_strawberry_framework/types/__init__.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)
- [`django_strawberry_framework/types/relations.py`](django_strawberry_framework/types/relations.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)

#### Planning note

shipped

#### Scope

- `DjangoTypeDefinition` dataclass with forward-reserved slots for every Layer 3 subsystem.
- `PendingRelation` and pending-relation registry API (`add_pending_relation`, `iter_pending_relations`, `discard_pending`, `is_finalized`, `mark_finalized`, extended `clear`).
- `finalize_django_types()` three-phase finalizer (resolve pending → attach resolvers → `strawberry.type(cls)`), with phase-1 failure-atomicity and named-source-model error format.
- Manual relation override contract: split `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields` so annotation-only overrides keep the generated resolver while assigned-field / decorator overrides suppress it. Class-attribute shadowing of relation fields raises `ConfigurationError`.
- `PendingRelationAnnotation` sentinel with metaclass `__repr__` that surfaces a useful `TypeError` body if `strawberry.Schema(...)` is constructed before finalization.
- MRO-aware `_detect_custom_get_queryset` so abstract bases without `Meta` still flip the `has_custom_get_queryset` sentinel for downstream concrete subclasses.
- Real cardinality coverage through the `library` example app (`Patron`, `MembershipCard`, `Genre`, `Book`, `Shelf`, `Branch`, `Loan`) instead of test-only fixture models.
- Dedicated test files: `tests/types/test_definition_order.py`, `tests/types/test_definition_order_schema.py`, `tests/optimizer/test_definition_order.py`, plus `tests/test_registry.py` extensions for idempotency / phase-1 atomicity / phase-2/3 partial-mutation contract / pending-set cleanup / class-mutation residue.
- Documentation sweep: `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, `TODAY.md`, and `CHANGELOG.md`.
- Version bump to `0.0.4` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `uv.lock`.
- Deletion of `TypeRegistry.lazy_ref`; unsupported and unresolved relations now fail with explicit `ConfigurationError` messages at annotation-building or finalization time.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py::convert_onetoone_field_to_djangomodel` (and the sibling FK / M2M converters) wrap related-type resolution in `graphene.Dynamic(dynamic_type)` callables that look up `registry.get_type_for_model(model)` only when the schema is built, giving graphene definition-order independence for relations; this slice ships the equivalent capability through `finalize_django_types()`'s three-phase finalizer that resolves a `PendingRelation` registry against registered `DjangoType`s before `strawberry.type(cls)` runs, so the claim is adjacent because it matches the observable behavior via an explicit collected-types finalize gate rather than graphene's per-field deferred callables.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::_process_type` achieves cross-type relation resolution by forcing relation annotations to `strawberry.auto` and clearing `StrawberryAnnotation.__resolve_cache__` so Strawberry re-evaluates forward references after all types are decorated, with no first-class pending-relation registry; this card's `PendingRelation` / `add_pending_relation` / `finalize_django_types()` foundation delivers the same definition-order-independent relation resolution but as an explicit registry-plus-finalizer mechanism with a `PendingRelationAnnotation` sentinel that errors if `strawberry.Schema(...)` is built early, so the claim is adjacent because the framework underpins and diverges from strawberry_django's implicit lazy-annotation approach rather than matching its public API at parity.

#### Other

- internal Layer-2 foundation (`DjangoTypeDefinition`, finalizer, pending-relation resolution) — enables the parity subsystems rather than being one itself.
- definition-order-independent finalizer, pending-relation registry, manual-override contract, real cardinality coverage — the seam every Layer-3 subsystem plugs into.
- `django_strawberry_framework/types/definition.py`
- `django_strawberry_framework/types/relations.py`
- `django_strawberry_framework/types/finalizer.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/registry.py`
- `tests/types/test_definition_order.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_definition_order.py`
- `tests/test_registry.py`
- `examples/fakeshop/apps/library/models.py`
- `examples/fakeshop/apps/library/schema.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `CHANGELOG.md`
- `docs/SPECS/spec-010-foundation-0_0_4.md`
- `docs/feedback.md`
- The forward-reserved slots on `DjangoTypeDefinition` are the architectural seam where the cookbook-shaped Layer 3 subsystems plug in (each subsystem moves its `Meta` key out of `DEFERRED_META_KEYS`, populates the matching slot in collection, and consumes it during finalization or in `DjangoConnectionField`).
- The pending-resolution pattern (record at class creation, resolve at finalization, fail loud on missing target with named source model / field / target) generalizes directly to lazy related class references for `RelatedFilter`, `RelatedOrder`, and `RelatedAggregate`.
- The previous foundation-slice in-progress cards have been retired; this card is their successor in Done.

<a id="rich_schema_architecture"></a>
### [DONE-009-0.0.4 - Rich schema architecture](KANBAN.html#rich_schema_architecture)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Parity-adjacent)
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `layer-3`, `public-api`, `relations`, `types`
- Spec: [spec-009-rich_schema_architecture-0_0_4.md](docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`AggregateSet`](docs/GLOSSARY.md#aggregateset) | planned for `0.1.3` |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [`DjangoConnection`](docs/GLOSSARY.md#djangoconnection) | shipped (`0.0.9`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [Input type generation](docs/GLOSSARY.md#input-type-generation) | shipped (`0.0.11`) |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`Ordering`](docs/GLOSSARY.md#ordering) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`RelatedAggregate`](docs/GLOSSARY.md#relatedaggregate) | planned for `0.1.3` |
| [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter) | shipped (`0.0.8`) |
| [`RelatedOrder`](docs/GLOSSARY.md#relatedorder) | shipped (`0.0.8`) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [Schema audit](docs/GLOSSARY.md#schema-audit) | shipped (`0.0.3`) |

#### Planning note

shipped

#### Scope

- Lay out the long-term architecture for filters, orders, aggregates, connections, permissions, and fieldsets.
- Compare Graphene, django-graphene-filters, and strawberry-graphql-django patterns against this package's DRF-shaped API.
- Define how the 0.0.4 foundation slice becomes the base for later Layer 3 subsystems.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::type` is the public `@strawberry_django.type(model)` entrypoint that generates a Strawberry type from a Django model and (via `_process_type`) wires relations, filters, ordering, and pagination as decorator kwargs; this card lays out the package's long-term Layer-3 architecture (filters, orders, aggregates, connections, permissions, fieldsets) over a DRF-shaped API and explicitly compares strawberry_django patterns, so it is adjacent because the planned architecture extends and reshapes that upstream surface rather than matching one of its features at parity.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py::convert_field_to_list_or_connection` shows graphene's relation-to-connection/list dispatch keyed off `_type._meta.connection` / `filter_fields` / `filterset_class` on the related `DjangoObjectType`; this card's scope explicitly contrasts Graphene/django-graphene-filters patterns when defining how the foundation slice becomes the base for later connection/filter subsystems, so the claim is adjacent because the package's DRF-shaped layered architecture differs from graphene's Meta-flag dispatch rather than reaching parity with a single graphene feature.

#### Other

- Architecture design record paired with the narrower 0.0.4 foundation implementation spec.

<a id="definition_order_independence_design"></a>
### [DONE-008-0.0.4 - Definition-order independence design](KANBAN.html#definition_order_independence_design)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Parity-adjacent)
- Severity: Major
- Status: Shipped
- Relative size: M
- Labels: `finalizer`, `registry`, `relations`, `types`
- Spec: [spec-008-definition_order_independence-0_0_4.md](docs/SPECS/spec-008-definition_order_independence-0_0_4.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [Schema audit](docs/GLOSSARY.md#schema-audit) | shipped (`0.0.3`) |

#### Planning note

shipped

#### Scope

- Frame the class-definition-time relation-resolution problem.
- Compare options for preserving concrete related `DjangoType`s without import-order coupling.
- Set the failure-mode requirements that the 0.0.4 foundation slice implements.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py::convert_field_to_djangomodel` converts every Django relation field into a `graphene.Dynamic(dynamic_type)` whose `dynamic_type` defers `registry.get_type_for_model(model)` to schema-build time (`graphene/types/dynamic.py::Dynamic.get_type`), so a related `DjangoObjectType` need not exist when the owning type is defined; this card frames the same class-definition-time relation-resolution problem but proposes an explicit pending-relation/finalizer design rather than per-field lazy callables, so the claim is adjacent (it underpins and differs from graphene's surface, not a parity match of a public feature).
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::_process_type` resolves relation annotations per class at decoration time by resetting `StrawberryAnnotation.__resolve_cache__` and forcing relation fields back to `strawberry.auto` so Strawberry re-evaluates forward references later, with no global collected-types finalize gate; this card compares that import-order-coupling-avoidance approach against the package's planned design, so it is adjacent because the framework's proposed deferred-finalize architecture extends and differs from strawberry_django's lazy-annotation mechanism rather than matching it at parity.

#### Other

- Problem-space design record for definition-order independence.

<a id="004_onboarding_docs_and_spec_consolidation"></a>
### [DONE-007-0.0.4 - 0.0.4 onboarding docs and spec consolidation](KANBAN.html#004_onboarding_docs_and_spec_consolidation)

- Priority: Medium
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `docs`, `internal`, `release`
- Spec: [spec-007-onboarding_docs_spec_consolidation-0_0_4.md](docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |

#### Planning note

shipped

#### Scope

- Root `README.md` is the canonical documentation map and operational entry point.
- `docs/README.md` is code-first: quickstart, three-minute path, optimizer behavior, and status.
- `docs/GLOSSARY.md` is the capability catalog with value-led optimizer language and comparison table.
- `docs/TREE.md` is the detailed layout/test-tree reference.
- `CHANGELOG.md` is condensed and no longer relies on design-doc pointers for release context.
- Completed design-doc content is folded into durable docs, while remaining specs preserve design history and follow-up work.

#### Other

- internal docs cleanup / spec consolidation — no upstream-parity surface.
- onboarding-doc consolidation across README / docs / CHANGELOG; completed spec content folded into durable docs.
- `README.md`
- `docs/README.md`
- `docs/GLOSSARY.md`
- `docs/TREE.md`
- `CHANGELOG.md`
- Future in-flight design docs use the `docs/spec-<NNN>-<topic>-<0_0_X>.md` convention (NNN matches the KANBAN card number; see `docs/builder/BUILD.md` "Spec filename pattern"), then get folded into durable docs when shipped.

<a id="documentationstatus_positioning_for_shipped_layer_2"></a>
### [DONE-006-0.0.3 - Documentation/status positioning for shipped Layer 2](KANBAN.html#documentationstatus_positioning_for_shipped_layer_2)

- Priority: Medium
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `docs`, `internal`
- Spec: [spec-006-public_surface-0_0_3.md](docs/SPECS/spec-006-public_surface-0_0_3.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [Queryset diffing](docs/GLOSSARY.md#queryset-diffing) | shipped (`0.0.3`) |
| [Schema audit](docs/GLOSSARY.md#schema-audit) | shipped (`0.0.3`) |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/optimizer/field_meta.py`](django_strawberry_framework/optimizer/field_meta.py)
- [`django_strawberry_framework/optimizer/hints.py`](django_strawberry_framework/optimizer/hints.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)

#### Planning note

shipped

#### Scope

- `docs/README.md` gives a quickstart, package positioning, optimizer value, and status.
- `docs/GLOSSARY.md` describes shipped, planned, deferred, and alpha-constrained capabilities.
- `docs/TREE.md` preserves detailed package/test tree responsibilities.

#### Other

- internal docs / status-positioning card — no upstream-parity surface.
- docs pass: `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md` quickstart + status positioning.
- `docs/README.md`
- `docs/GLOSSARY.md`
- `docs/TREE.md`
- User-facing docs avoid internal slice shorthand; maintainer docs can still use it where useful.

<a id="djangotype_contract_and_boundary"></a>
### [DONE-005-0.0.3 - DjangoType contract and boundary](KANBAN.html#djangotype_contract_and_boundary)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent)
- Severity: Major
- Status: Shipped
- Relative size: M
- Labels: `docs`, `public-api`, `registry`, `types`
- Spec: [spec-005-django_type_contract-0_0_3.md](docs/SPECS/spec-005-django_type_contract-0_0_3.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) | shipped |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |

#### Package files

- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)

#### Planning note

shipped

#### Scope

- Document the alpha one-model-one-type registry constraint.
- Reject unsupported or deferred `Meta` keys instead of accepting unwired surface area.
- Remove consumer override promises that the implementation cannot honor yet.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/registry.py::Registry.register` stores one type per model (`self._registry[cls._meta.model] = cls`, last-write-wins, with the multiple-types assertion left commented out) and `types.py::validate_fields` only `warnings.warn`s when `Meta.fields`/`exclude` name unknown fields -- this card tightens both: it documents the same one-model-one-type registry constraint as a hard alpha boundary and raises (rather than warns) on unsupported/deferred `Meta` keys, so it is adjacent to graphene's looser model-to-type registry and field-validation surface, narrowing rather than matching it.

#### Other

- Contract companion to the 0.0.3 public-surface documentation pass.

<a id="optimizer_beyond_slices_b1_b8"></a>
### [DONE-004-0.0.3 - Optimizer beyond slices B1-B8](KANBAN.html#optimizer_beyond_slices_b1_b8)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `optimizer`, `performance`, `query-planning`, `schema-audit`
- Spec: [spec-004-optimizer_beyond-0_0_3.md](docs/SPECS/spec-004-optimizer_beyond-0_0_3.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) | shipped |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) | shipped (`0.0.3`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [Queryset diffing](docs/GLOSSARY.md#queryset-diffing) | shipped (`0.0.3`) |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/field_meta.py`](django_strawberry_framework/optimizer/field_meta.py)
- [`django_strawberry_framework/optimizer/hints.py`](django_strawberry_framework/optimizer/hints.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)

#### Planning note

shipped

#### Scope

- B1: plan cache keyed by selected operation AST, directive variables, model, and root runtime path
- B2: forward-FK-id elision
- B3: strictness mode (`off`, `warn`, `raise`)
- B4: `Meta.optimizer_hints` with `OptimizerHint`
- B5: plan introspection via context
- B6: schema-build-time audit
- B7: precomputed optimizer field metadata
- B8: queryset diffing against consumer-applied `select_related`, `prefetch_related`, and `Prefetch`

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py::optimize` is strawberry-django's optimization entry point: it short-circuits when `is_optimized(qs)` (a per-queryset already-optimized flag set via `get_queryset_config(qs).optimized`) and otherwise applies the accumulated `OptimizerStore` to the queryset -- the same production-grade extension surface this card extends, where B1's AST-keyed plan cache and B8's `diff_plan_for_queryset` per-path reconciliation against consumer `select_related`/`prefetch_related`/`Prefetch` go beyond strawberry-django's single boolean guard, so the existing required claim covers the shared apply-optimizations-once core that these beyond-slices features build on.

#### Other

- continuation of DONE-002's optimizer lineage (⚛️ parity-adjacent).
- eight optimizer sub-features B1–B8: AST plan cache, FK-id elision, strictness modes, `OptimizerHint`, context plan introspection, schema audit, precomputed field metadata, queryset diffing.
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/hints.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/plans.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_hints.py`
- `tests/optimizer/test_field_meta.py`
- `tests/optimizer/test_plans.py`
- B8 went beyond the initial simple exact-match diff and now handles subtree-aware prefetch reconciliation.
- Fragment-spread directive and multi-operation cache-key bugs have been fixed in source; the old `alpha-review-feedback.md` entries are now historical.

<a id="optimizer_o4_nested_prefetch_chains"></a>
### [DONE-003-0.0.2 - Optimizer O4 nested prefetch chains](KANBAN.html#optimizer_o4_nested_prefetch_chains)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: M
- Labels: `optimizer`, `performance`, `query-planning`, `relations`
- Spec: [spec-003-optimizer_nested_prefetch_chains-0_0_2.md](docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) | shipped (`0.0.3`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint) | shipped (`0.0.3`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [Queryset diffing](docs/GLOSSARY.md#queryset-diffing) | shipped (`0.0.3`) |
| [Schema audit](docs/GLOSSARY.md#schema-audit) | shipped (`0.0.3`) |

#### Package files

- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/field_meta.py`](django_strawberry_framework/optimizer/field_meta.py)
- [`django_strawberry_framework/optimizer/hints.py`](django_strawberry_framework/optimizer/hints.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)

#### Planning note

shipped

#### Scope

- Plan depth > 1 relation selections from the root optimizer pass.
- Emit nested `Prefetch` objects for many-side branches that need shaped child querysets.
- Recurse through single-valued relation chains with `select_related` and `only()` fields intact.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py::_get_hints_from_django_relation` builds a depth>1 nested plan by recursing through `_get_model_hints(..., level=level + 1)`, rebasing the child `OptimizerStore`'s `only`/`select_related` under the relation path, and emitting `Prefetch(path, queryset=field_qs)` for many-side branches -- the identical behavior this card ships in `optimizer/walker.py` (`_build_prefetch_child_queryset` recurses one level deeper and `_plan_prefetch_relation` emits `Prefetch(full_path, queryset=child_queryset)`, while `_plan_select_relation` recurses through single-valued chains preserving `select_related` + `only()`), so O4 nested-prefetch-chain planning is required parity with strawberry-django's nested relation hinting.

#### Other

- Design record for the O4 slice split out from the broader optimizer foundation.

<a id="optimizer_o1_o6_foundation"></a>
### [DONE-002-0.0.2 - Optimizer O1-O6 foundation](KANBAN.html#optimizer_o1_o6_foundation)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `optimizer`, `performance`, `query-planning`, `relations`
- Spec: [spec-002-optimizer-0_0_2.md](docs/SPECS/spec-002-optimizer-0_0_2.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/optimizer/__init__.py`](django_strawberry_framework/optimizer/__init__.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/types/__init__.py`](django_strawberry_framework/types/__init__.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)
- [`django_strawberry_framework/utils/__init__.py`](django_strawberry_framework/utils/__init__.py)
- [`django_strawberry_framework/utils/strings.py`](django_strawberry_framework/utils/strings.py)
- [`django_strawberry_framework/utils/typing.py`](django_strawberry_framework/utils/typing.py)

#### Planning note

shipped

#### Scope

- generated relation resolvers
- selection-tree walker
- root-gated optimizer extension
- nested `Prefetch` chains
- same-query `select_related` recursion
- `only()` projection
- custom `get_queryset` downgrade to `Prefetch`

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py::DjangoOptimizerExtension` is strawberry-django's N+1 solver: a `SchemaExtension` whose `resolve` walks the selection tree, builds an `OptimizerStore` (lists of `only`/`select_related`/`prefetch_related`), and applies it to the root queryset, with `_get_prefetch_queryset` running the target type's `get_queryset` inside generated `Prefetch` objects -- the same root-gated extension, selection-tree walker, `select_related`/`only()` projection, nested `Prefetch` chains, and custom-`get_queryset`-downgrade-to-`Prefetch` behavior this card's O1-O6 foundation ships, so it is required parity with strawberry-django's optimizer extension.

#### Other

- strawberry-graphql-django ships a heavy optimizer extension; graphene-django has only `select_related_field` (⚛️ parity-adjacent).
- heavy optimizer extension: relation resolvers, selection-tree walker, root-gated planning, nested `Prefetch` chains, `only()` projection, `get_queryset` downgrade.
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/plans.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_walker.py`
- `tests/optimizer/test_plans.py`
- Shipped behavior is consolidated into `docs/GLOSSARY.md`; source/tests are the truth for optimizer behavior.

<a id="djangotype_core_foundation"></a>
### [DONE-001-0.0.1 - DjangoType core foundation](KANBAN.html#djangotype_core_foundation)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `public-api`, `registry`, `relations`, `scalars`, `types`
- Spec: [spec-001-django_types-0_0_1.md](docs/SPECS/spec-001-django_types-0_0_1.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`AggregateSet`](docs/GLOSSARY.md#aggregateset) | planned for `0.1.3` |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [`BigInt` scalar](docs/GLOSSARY.md#bigint-scalar) | shipped (`0.0.6`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`Meta.choice_enum_names`](docs/GLOSSARY.md#metachoice_enum_names) | planned for `0.1.4` |
| [`Meta.description`](docs/GLOSSARY.md#metadescription) | shipped |
| [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) | shipped |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.name`](docs/GLOSSARY.md#metaname) | shipped |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/conf.py`](django_strawberry_framework/conf.py)
- `django_strawberry_framework/converters.py` (historical)
- [`django_strawberry_framework/exceptions.py`](django_strawberry_framework/exceptions.py)
- `django_strawberry_framework/optimizer.py` (historical)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- `django_strawberry_framework/types.py` (historical)

#### Planning note

shipped

#### Scope

- `DjangoType` base class
- Meta validation
- scalar conversion
- relation conversion
- choice enums
- type registry
- relation resolvers
- `get_queryset` hook and `has_custom_get_queryset`

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py::DjangoObjectType` is graphene's model-backed type: a nested `Meta` declares `model`/`fields`/`exclude`, `construct_fields` selects model fields, `convert_choice_field_to_enum` (`converter.py`) turns Django `choices` into GraphQL enums, `Registry.register` (`registry.py`) maps model to type, and a classmethod `get_queryset(queryset, info)` scopes visibility -- the exact surface `DjangoType` ships (base class, Meta validation, scalar/relation conversion, choice enums, registry, `get_queryset` hook), so this is required parity with graphene's canonical type-generation feature.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::_process_type` is strawberry-django's adapter behind `@strawberry_django.type`: it reads `model`/`fields`/`exclude`, marks model fields `strawberry.auto`, and records a `StrawberryDjangoDefinition` in the registry, while `queryset.py::run_type_get_queryset` invokes the type's `get_queryset(qs, info)` -- the same model-to-Strawberry-type contract and same `get_queryset` visibility hook `DjangoType` implements, so this is required parity with strawberry-django's core type surface.

#### Other

- `DjangoObjectType` (graphene-django) / `@strawberry_django.type` (strawberry-graphql-django) are the namesake primitive.
- core foundational subsystem: `DjangoType` base, Meta validation, scalar/relation conversion, choice enums, type registry, relation resolvers, `get_queryset` hook.
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `tests/types/test_base.py`
- `tests/types/test_converters.py`
- `tests/types/test_resolvers.py`
- The public shape is intentionally narrow and explicit.
- Deferred Meta keys are rejected, not silently accepted.
- Definition-order independence is now covered by `DONE-010-0.0.4`.

#### Card references

- Related: Definition-order independence is now covered by `DONE-010-0.0.4`. -> `DONE-010-0.0.4` - 0.0.4 foundation slice (definition-order independence)

## Release readiness checklist

Before a release:

- `pyproject.toml` and `django_strawberry_framework/__init__.py` versions match.
- README status matches actual top-level exports.
- `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, and any active design docs agree on shipped/planned state.
- No stale skipped tests refer to already-shipped slices.
- New source modules have mirrored tests in the correct tree.
- `uv run ruff format .` passes.
- `uv run ruff check --fix .` passes.
- `uv run pytest` passes with 100% package coverage when explicitly run for release validation.

## Notes for Kanban maintenance

- Treat this file as a living operational board, not a spec.
- When a card moves to Done, update the evidence and remove stale blocker language.
- When a future spec creates a new subsystem, add it here as a card with a definition of done.
- Keep `CHANGELOG.md` out of routine updates unless explicitly requested.
- Strategic differentiation candidates (features neither `graphene-django` nor `strawberry-graphql-django` ship cleanly) live in [`BACKLOG.md`][backlog] or the Backlog board section. When a backlog item is scheduled, promote it to a `TODO[-MILESTONE]-NNN-X.Y.Z` card here and cross-reference back.

## Decision: FilterSet subclassing unsupported

FilterSet / FilterArgumentsFactory subclassing is unsupported (decided 2026-05-30).

FilterArgumentsFactory raises TypeError on subclassing: its class-level input_object_types / _type_filterset_registry caches are shared mutable dicts a subclass would inherit rather than isolate, silently cross-contaminating builds.

Rationale: supporting subclassing would turn a currently-discouraged pattern into a real API commitment and pull in cache / lifecycle fixes (H-filters-3, M-filters-4, M-filters-5) that do not buy much without a concrete consumer need. Revisit if a real consumer need arises.

Ref: spec-021 pre-merge review M-filters-3 / H-filters-3.

## Decision: Alpha cards must claim upstream parity

Every Alpha (`0.0.x`) card that ships a consumer-facing capability MUST carry at least one upstream parity link — a `ParityClaim` against `graphene_django` (⚛️) and/or `strawberry_django` (🍓), at `required` or `adjacent` level — AND at least one justification bullet in the card's `Verified in upstream` section grounding that link in a specific upstream `path::symbol` (decided 2026-06-09).

Rationale: Alpha is the road to `0.1.0` feature parity, so an Alpha *feature* card with no parity link is either mis-scoped (it belongs in Beta as a beyond-parity differentiator) or simply untracked. Requiring the link plus a grounded justification keeps the Alpha cut honestly parity-bearing and makes each card's placement auditable against the upstreams.

Exemption: pure-internal housekeeping cards — documentation, release / version alignment, cleanup, test-only coverage, and Django-core defensive hardening — have no upstream feature to match and are labeled `internal`; the rule does not apply to them. A parity link must NEVER be fabricated to satisfy the rule: if no honest upstream analog exists, the card is `internal` (or belongs in Beta), not parity-tagged.

Enforcement: `scripts/check_alpha_parity.py` fails if any non-`internal` Alpha card lacks a parity link or a `Verified in upstream` justification.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: BACKLOG.md
[goal]: GOAL.md
[readme]: README.md

<!-- docs/ -->
[docs-readme]: docs/README.md
[glossary-bigint-scalar]: docs/GLOSSARY.md#bigint-scalar
[glossary-django-trac-37064-hardening]: docs/GLOSSARY.md#django-trac-37064-hardening
[glossary-filterset]: docs/GLOSSARY.md#filterset
[glossary-metafilterset_class]: docs/GLOSSARY.md#metafilterset_class
[glossary-multi-database-cooperation]: docs/GLOSSARY.md#multi-database-cooperation
[glossary-optimizerhint]: docs/GLOSSARY.md#optimizerhint
[glossary-relatedfilter]: docs/GLOSSARY.md#relatedfilter
[glossary-safe-wrap-connection-method]: docs/GLOSSARY.md#safe_wrap_connection_method
[glossary-strawberry-config]: docs/GLOSSARY.md#strawberry_config
[spec-021]: docs/SPECS/spec-027-filters-0_0_8.md

<!-- docs/SPECS/ -->
[spec-011]: docs/SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-016]: docs/SPECS/spec-020-list_field-0_0_7.md
[spec-019]: docs/SPECS/spec-023-multi_db-0_0_7.md

<!-- docs/builder/ -->
[build-020-scalar-map-helper-0-0-7]: docs/builder/build-020-scalar_map_helper-0_0_7.md

<!-- django_strawberry_framework/ -->
[apps]: django_strawberry_framework/apps.py
[converters]: django_strawberry_framework/types/converters.py
[django-patches]: django_strawberry_framework/_django_patches.py
[filters]: django_strawberry_framework/filters/
[plans]: django_strawberry_framework/optimizer/plans.py
[resolvers]: django_strawberry_framework/types/resolvers.py
[test-init]: django_strawberry_framework/testing/__init__.py
[wrap]: django_strawberry_framework/testing/_wrap.py

<!-- tests/ -->
[test-converters]: tests/types/test_converters.py
[test-multi-db]: tests/optimizer/test_multi_db.py
[test-resolvers]: tests/types/test_resolvers.py

<!-- examples/ -->
[db-shard-b.sqlite3]: examples/fakeshop/db_shard_b.sqlite3
[example-schema]: examples/fakeshop/config/schema.py
[fakeshop-library]: examples/fakeshop/apps/library/
[kanban-app]: examples/fakeshop/apps/kanban/
[fakeshop-test-multi-db]: examples/fakeshop/test_query/test_multi_db.py
[settings]: examples/fakeshop/config/settings.py
[test-library-api]: examples/fakeshop/test_query/test_library_api.py
[test-scalars-api]: examples/fakeshop/test_query/test_scalars_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
