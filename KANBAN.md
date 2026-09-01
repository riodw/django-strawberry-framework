# django-strawberry-framework Kanban

Last refreshed: 2026-08-31

This board summarizes what is shipped, what has recently landed, and what remains to finish based on the current code, tests, docs, and release-readiness notes. It is intentionally written as a project-management view: each card has a status, priority, scope, and a practical definition of done.

Editing this board: `KANBAN.md` is a rendered artifact, not a source. The source of truth is the `kanban` Django app under [`examples/fakeshop/apps/kanban/`][kanban-app] — `BoardDoc` rows hold the prose sections (this preamble, the snapshot, the column intros, the footers), `Card` rows hold each card's identity / status / priority / dependencies, and `CardItem` / `CardReference` / `ParityClaim` rows hold the per-card bulleted body, blocking-or-related links between cards, and the parity claims against upstream packages. To change anything on the board, edit the relevant row(s) in the SQLite database at `examples/fakeshop/db.sqlite3` (Django admin or `manage.py shell`), then run `uv run python scripts/build_kanban_md.py` and `uv run python scripts/build_kanban_html.py` to regenerate `KANBAN.md` and `KANBAN.html`. Direct edits to `KANBAN.md` are overwritten on the next rebuild.

## Card ID format

Every card uses the form `<STATUS>[-<MILESTONE>]-NNN-X.Y.Z`:

- `<STATUS>` — the card workflow state: `BACKLOG` (unscheduled investigation / strategic-differentiation candidate), `TODO` (committed to a milestone, not yet active), `WIP` (actively being worked), or `DONE` (shipped). Updated when the card moves between workflow states. Blocking is not part of the workflow status; blocked cards render a derived `blocked` badge from unfinished `blocked_by` references and stay in their normal planning column.
- `<MILESTONE>` *(optional)* — the development phase the card lives in while it's still pre-shipping: `ALPHA` (pre-`0.1.0`), `BETA` (post-`0.1.0` / pre-`1.0.0`), or `STABLE` (post-`1.0.0`). Used on `BACKLOG`, `TODO`, and `WIP` cards. The two release cards themselves are tagged with the phase they usher in: `TODO-ALPHA-057-0.1.0` is the alpha → beta cut-over and `TODO-STABLE-073-1.0.0` is the beta → stable cut-over. **Dropped when the card ships** — `DONE` cards use the bare `DONE-NNN-X.Y.Z` form (no milestone segment). The card's version tag (`X.Y.Z`) already encodes which phase the shipment belongs to, and the bare form keeps the shipped-card cluster compact and uniform across the package's history.
- `NNN` — a 3-digit sequence number indicating the order the card was completed (`DONE` cards) or is being tracked (everything else; scheduled cards are ordered by planned ship version, and backlog cards sort after the scheduled board). **Unlike status, milestone, and version, this number is not stable** — it is recomputed whenever a card's position in the shipping sequence changes (reordered, new card inserted between two existing cards, version-tag bumped). Use the card title, not the NNN, when referencing a card from long-lived documents.
- `X.Y.Z` — the package version the card shipped in (`DONE` cards), is planned to ship in (scheduled cards), or is provisionally bucketed under (`BACKLOG` cards). Alpha cards span `0.0.6` through `0.0.15` leading up to `0.1.0`; Beta cards span `0.1.1` through `0.1.8` leading up to `1.0.0`. The `0.1.0` and `1.0.0` tags are reserved for the two release cards themselves. Backlog cards may use post-`1.0.0` buckets as ordering placeholders; they stay unscheduled until promoted to `TODO`.

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
- `0.0.15` is the active patch. `DONE-029-0.0.9` (`DjangoType` consumer-DX cleanup) has shipped; the Relay connection cohort is complete — `DONE-030-0.0.9` (`DjangoConnectionField`, the central read-side primitive), `DONE-031-0.0.9` (Django-model-based GlobalID encoding), and `DONE-032-0.0.9` (the full Relay story) have shipped; `DONE-033-0.0.9` (connection-aware optimizer planning) has shipped, closing out the cohort. The version bump from `0.0.8` is owned by the joint `0.0.9` cut, not any single card, per Decision 11 of `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`. Blocked future cards stay in their normal planning columns with derived `blocked` badges, outside the active in-progress column.
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

**67.1% complete** toward `1.0.0` - 49 of 73 cards done (65.0% size-weighted). Across all non-backlog cards (incl. post-`1.0.0`), 49 of 74 (66.2%, 63.9% size-weighted). Past the 50% mark. Backlog excluded; size-weighted by relative size (XS=1 .. XL=5).

| Milestone | Cards done | Size-weighted |
| --- | --- | --- |
| Alpha (pre-0.1.0) | 49/57 (86.0%) | 84.0% |
| Beta (pre-1.0.0) | 0/15 (0.0%) | 0.0% |
| Stable (post-1.0.0) | 0/2 (0.0%) | 0.0% |

## Board columns

## WIP / DONE spec map

| Card | Spec file |
| --- | --- |
| `WIP-ALPHA-050-0.0.15` - `DjangoListField` argument surface: `offset` / `limit` and `orderBy` | [spec-050-list_field_arguments-0_0_15.md](docs/spec-050-list_field_arguments-0_0_15.md) |
| `DONE-049-0.0.14` - Dependency and CI hardening: refresh Django locks, add audit automation, least-privilege CI | [spec-049-dependency_ci_hardening-0_0_14.md](docs/SPECS/spec-049-dependency_ci_hardening-0_0_14.md) |
| `DONE-048-0.0.14` - Secure output and error defaults: drop file path, fail-closed debug, prod error policy | [spec-048-secure_output_defaults-0_0_14.md](docs/SPECS/spec-048-secure_output_defaults-0_0_14.md) |
| `DONE-047-0.0.14` - Execution resource policy: central budget object + value-cardinality walker | [spec-047-resource_policy-0_0_14.md](docs/SPECS/spec-047-resource_policy-0_0_14.md) |
| `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation | [spec-046-transport_security-0_0_14.md](docs/SPECS/spec-046-transport_security-0_0_14.md) |
| `DONE-045-0.0.14` - Sealed get_queryset visibility-boundary policy artifacts | [spec-045-visibility_boundary-0_0_14.md](docs/SPECS/spec-045-visibility_boundary-0_0_14.md) |
| `DONE-044-0.0.14` - Response-extensions debug middleware | [spec-044-debug_extension-0_0_14.md](docs/SPECS/spec-044-debug_extension-0_0_14.md) |
| `DONE-043-0.0.14` - Test client helper | [spec-043-test_client-0_0_14.md](docs/SPECS/spec-043-test_client-0_0_14.md) |
| `DONE-042-0.0.14` - Debug-toolbar middleware | [spec-042-debug_toolbar-0_0_14.md](docs/SPECS/spec-042-debug_toolbar-0_0_14.md) |
| `DONE-041-0.0.14` - Channels ASGI router (migration aid) | [spec-041-channels_router-0_0_14.md](docs/SPECS/spec-041-channels_router-0_0_14.md) |
| `DONE-040-0.0.13` - Auth mutations (login / logout / register) | [spec-040-auth_mutations-0_0_13.md](docs/SPECS/spec-040-auth_mutations-0_0_13.md) |
| `DONE-039-0.0.13` - DRF serializer mutations (`SerializerMutation`) | [spec-039-serializer_mutations-0_0_13.md](docs/SPECS/spec-039-serializer_mutations-0_0_13.md) |
| `DONE-038-0.0.12` - Form-based mutations (Django Forms / ModelForms) | [spec-038-form_mutations-0_0_12.md](docs/SPECS/spec-038-form_mutations-0_0_12.md) |
| `DONE-037-0.0.11` - Upload scalar and file / image field mapping | [spec-037-upload_file_image_mapping-0_0_11.md](docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md) |
| `DONE-036-0.0.11` - Mutations + auto-generated Input types | [spec-036-mutations-0_0_11.md](docs/SPECS/spec-036-mutations-0_0_11.md) |
| `DONE-035-0.0.10` - Optimizer robustness hardening (upstream-comparison guards) | [spec-035-optimizer_hardening-0_0_10.md](docs/SPECS/spec-035-optimizer_hardening-0_0_10.md) |
| `DONE-034-0.0.10` - Permissions subsystem | [spec-034-permissions-0_0_10.md](docs/SPECS/spec-034-permissions-0_0_10.md) |
| `DONE-033-0.0.9` - Connection-aware optimizer planning | [spec-033-connection_optimizer-0_0_9.md](docs/SPECS/spec-033-connection_optimizer-0_0_9.md) |
| `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation) | [spec-032-full_relay-0_0_9.md](docs/SPECS/spec-032-full_relay-0_0_9.md) |
| `DONE-031-0.0.9` - Django-model-based GlobalID encoding | [spec-031-globalid_encoding-0_0_9.md](docs/SPECS/spec-031-globalid_encoding-0_0_9.md) |
| `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field) | [spec-030-connection_field-0_0_9.md](docs/SPECS/spec-030-connection_field-0_0_9.md) |
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

<a id="djangolistfield_argument_surface_offset_limit_and_orderby"></a>
### [WIP-ALPHA-050-0.0.15 - `DjangoListField` argument surface: `offset` / `limit` and `orderBy`](KANBAN.html#djangolistfield_argument_surface_offset_limit_and_orderby)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Required)
- Status: WIP
- Relative size: M
- Labels: `list-field`, `ordering`, `public-api`
- Spec: [spec-050-list_field_arguments-0_0_15.md](docs/spec-050-list_field_arguments-0_0_15.md)

#### Planning note

Promoted from the 0.1.0 parity register's largest unaccounted finding (offset/limit pagination - both upstreams ship a client-facing offset surface) together with spec-028's orphaned orderBy deferral, taken as one card because both open the same list-field argument-factory seam and would otherwise open it twice. Maintainer decision 2026-08-29: build the minimal shape - bounded offset/limit on `DjangoListField` only, never on connections.

#### Scope

- Bounded `offset` / `limit` arguments on `DjangoListField` only. Connections are a permanent non-goal the spec must pin: grafting offset onto a connection reintroduces the skip-based instability keyset cursors exist to remove, and ⚛'s own `offset: Int`-on-every-connection is the shape being refused.
- Caps and hygiene: the effective row count is the minimum of the client `limit`, the field's `max_rows`, and the request `ResourcePolicy.max_list_rows` (the shipped bound; `trusted_max_rows` semantics unchanged); `offset` is bounded by a policy ceiling rather than unbounded skip; negative, non-integer, or over-ceiling values raise a typed `GraphQLError`, never a silent clamp in the error direction. With neither argument supplied, behavior and SQL are byte-for-byte today's.
- `orderBy` argument on `DjangoListField` through the shipped OrderSet argument machinery (the target type's `orderset_class`, the same binding connections use) - this is spec-028's deferred orderBy-argument integration, orphaned since `0.0.9` and adjudicated onto this card by the doc-debt card's archived-spec deferral sweep. `django_strawberry_framework/list_field.py`'s ordering-contract docstring already promises order "unless the query supplies an `orderBy` argument" - an argument the field could not accept until this card, so the docstring becomes true rather than aspirational.
- Determinism interplay, a spec decision: an `offset` page without an active order (argument or `Meta.ordering`) is database-dependent and unstable across requests. Preferred answer: require an active order whenever `offset` is non-zero (typed error otherwise); the alternative - documenting the instability - must say why upstream's silent instability was kept.
- SDL consequence stated up front: the three arguments surface on every `DjangoListField` (nullable, optional), which is a schema-visible addition for every consumer; the spec records it as such.
- Migration mapping: ⚛'s connection `offset` and 🍓's `pagination=True` / `OffsetPaginationInput` / `OffsetPaginated[T]` / `offset_paginated()` all map onto this surface; the migration-guides card owes the note, including that nested/windowed offset pagination stays served by nested connections here.

#### Definition of done

- [ ] A spec is written for the card covering the argument shapes, the caps table, the typed-error contract, the offset-requires-order decision, and the connections non-goal.
- [ ] `offset` / `limit` / `orderBy` ship on `DjangoListField`; with none supplied, generated SDL for existing consumers is unchanged apart from the three new optional arguments and the emitted SQL is unchanged byte-for-byte.
- [ ] SQL-shape tests pin `LIMIT`/`OFFSET` present exactly when supplied, composed with the policy bound, and no code path injects `DISTINCT`.
- [ ] `orderBy` composes with type visibility (`get_queryset` narrows first) and reuses the OrderSet pipeline end-to-end; the pk tiebreaker question is answered in the spec (lists have no cursors, so the connection tiebreaker is not blindly inherited).
- [ ] Typed `GraphQLError` on negative / non-integer / over-ceiling `offset` or `limit`, live-tested on both values.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` exercises offset paging with an order, the cap interplay, and an orderBy'd list.
- [ ] `django_strawberry_framework/list_field.py`'s ordering-contract docstring is updated to describe the shipped argument.
- [ ] The migration-guides card gains the offset-mapping note (its upstream-settings/surface table).
- [ ] Full suite green under `fail_under = 100`; live-first placement respected. No version quintet or CHANGELOG entry - the `0.0.15` release state is owned by the DRY-squeeze card's joint cut, which lands last on the line.

#### Files likely touched

- `django_strawberry_framework/list_field.py` (argument factory, caps, docstring)
- `django_strawberry_framework/orders/` argument machinery reused at the list-field seam
- `django_strawberry_framework/conf.py` only if the offset ceiling needs its own key (prefer deriving from `max_list_rows`)
- Mirrored `tests/` modules plus live coverage under `examples/fakeshop/test_query/`

#### Verified in upstream

- ⚛ adds `offset: Int` to every connection field (graphene-django connection arguments).
- 🍓 `strawberry_django/pagination.py` ships `OffsetPaginationInput`, the `OffsetPaginated[T]` generic (`pageInfo` / `totalCount` / `results`), `offset_paginated()`, and window-function nested offset pagination.
- spec-028 deferred the `orderBy` argument on `DjangoListField` at `0.0.9`; the deferral had no card until this one.

#### Note

- This card discharges the parity register's offset/limit cut blocker and satisfies the archived-deferral sweep's card-or-drop adjudication for spec-028's orderBy orphan: carded here.
- Renumber consequence: this card was inserted at 050 while In Progress (it ships next), shifting the 22 cards then numbered 050-071 up by one to 051-072; the board DB's text columns were re-swept for full card ids in the same pass. Spec filename stems and tree-wide references remain owed to the standing three-grammar sweep.

#### Card references

- Related: Shares the `0.0.15` line; both are pre-beta parity work, this card lands first. -> `TODO-ALPHA-051-0.0.15` - Upstream parity-gap closure
- Related: Its archived-spec deferral sweep names spec-028's orphaned orderBy integration; adjudicated: carded here. -> `TODO-ALPHA-056-0.0.17` - Alpha documentation-debt discharge
- Related: Owes the offset-mapping migration note: upstream offset surfaces map to this card's `DjangoListField` arguments; nested offset pagination maps to nested connections. -> `TODO-BETA-071-0.1.8` - Migration and adoption guides
- Related: The parity claim's offset/limit cut blocker is closed by this card. -> `TODO-ALPHA-057-0.1.0` - Beta release (cleanup, verification, alpha → beta)

<a id="upstream_parity_gap_closure"></a>
### [TODO-ALPHA-051-0.0.15 - Upstream parity-gap closure](KANBAN.html#upstream_parity_gap_closure)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: To Do
- Relative size: M
- Labels: `mutations`, `public-api`, `scalars`, `types`

#### Planning note

The six code gaps left by the `0.1.0` parity audit after everything homeable was homed onto existing cards. All six are small, test-pinned items against a named upstream surface; none is a new subsystem. They are grouped because they share a charter — close every remaining build-side parity delta before the beta cut — not because they share a seam.

#### Scope

- A `through=` class-creation guard: reject at type creation a `through=`-declared M2M whose through model carries required extra columns (non-null, no default, beyond the two FKs) wherever the relation is writable through generated inputs, with a `ConfigurationError` naming the through model and the offending columns — today `django_strawberry_framework/mutations/resolvers.py::_assign_m2m` is a plain `.set(pks)` and neither `django_strawberry_framework/mutations/inputs.py` nor `django_strawberry_framework/utils/relations.py` guards the declaration, so the failure happens at runtime inside Django's `.set()`, outside the `FieldError` envelope. Fail-loud is package doctrine; this guard is also what makes the `through_defaults` refusal homed on TODO-BETA-071-0.1.8 safe.
- `GeneratedField` support: resolve type and nullability from the field's `output_field` in `django_strawberry_framework/types/converters.py::convert_field_output` (the upstream answer — 🍓 `strawberry_django/fields/types.py` #"GeneratedField" — and a direct fit for our converter table), and exclude the column from generated write inputs since it is database-computed. Today a Django 5.0+ `GeneratedField` reached through `Meta.fields = "__all__"` raises `ConfigurationError "Unsupported Django field type 'GeneratedField'"` at type creation, `Meta.exclude` is the only escape, and nothing documents it — a migrating consumer with any generated column cannot declare the type at all.
- Model `help_text` as the SDL field description: thread the model column's `help_text` into the generated field's GraphQL description. Today no model-column path exists — the only `help_text` handling is on the DRF serializer-input side (`django_strawberry_framework/rest_framework/serializer_converter.py`) and `django_strawberry_framework/types/base.py` synthesizes bare annotations — so a ⚛️ migrant takes a silent whole-schema SDL regression on every documented model. The spec decides always-on (⚛️ threads `str(field.help_text)` unconditionally) versus opt-in (🍓 gates it behind `FIELD_DESCRIPTION_FROM_HELP_TEXT`); an explicit consumer-declared description wins over `help_text` either way.
- `django-choices-field` enum reuse: when a `TextChoicesField` / `IntegerChoicesField` declares a `choices_enum`, reuse the consumer's own enum instead of silently minting a second one from the raw choices (🍓 parity: `strawberry_django/fields/types.py` #"TextChoicesField"). Soft-dependency detection only — no hard dependency on `django-choices-field`; the `(model, field)` enum-reuse cache contract is unchanged. Coordinate with TODO-BETA-065-0.1.4, which owns `convert_choices_to_enum()` naming and that cache on the far side of the beta cut.
- `FieldError` key casing: unify the wire casing of `FieldError.field` across the three flavors — model-flavor validation errors emit raw snake_case (`django_strawberry_framework/utils/errors.py::validation_error_to_field_errors` is an identity pass-through), relation-decode errors emit the camelCased wire name (`::relation_field_error`), and the serializer flavor re-keys recursively (`django_strawberry_framework/rest_framework/resolvers.py::serializer_errors_to_field_errors`) — and pin the chosen casing with live tests including a multi-word snake_case field, which no test covers today (the divergence is invisible to the suite). ⚛️ context: `graphene_django/settings.py` #"CAMELCASE_ERRORS", default on, in the exact `ErrorType` our `FieldError` mirrors.
- Surface upstream relay/pagination argument rejections as typed errors: raise them as `GraphQLError` carrying an audited `extensions.code` instead of letting the secure-output defaults mask them, so a migrant's first contact reads as a policy, not a bug. The fix is exactly the one TODO-ALPHA-057-0.1.0's open question states; landing this discharges that question.

#### Definition of done

- [ ] A `through=` M2M with required extra columns fails at type creation with a `ConfigurationError` naming the through model and columns; an auto-created or fully-defaulted through model is unaffected; live coverage proves the runtime `.set()` path is never reached.
- [ ] A `GeneratedField` reached through `Meta.fields = "__all__"` or an explicit field list converts via its `output_field` type and nullability, is absent from generated write inputs, and is live-probed end-to-end.
- [ ] Model `help_text` appears as the SDL field description per the spec's on-by-default-or-opt-in decision; an explicit description wins; SDL snapshot coverage pins it.
- [ ] A `TextChoicesField` / `IntegerChoicesField` with a declared `choices_enum` publishes the consumer's enum (one enum type, not two); absence of `django-choices-field` changes nothing.
- [ ] `FieldError.field` casing is uniform across model, relation-decode, and serializer flavors; a live test pins a multi-word snake_case field on each flavor.
- [ ] Upstream relay/pagination argument rejections surface as `GraphQLError` with an audited `extensions.code`; TODO-ALPHA-057-0.1.0's masked-rejections open question is closed against this card.
- [ ] TODO-BETA-071-0.1.8's upstream-settings disposition table gains its `CAMELCASE_ERRORS` row stating whatever casing story ships — ⚛️'s key is a toggle (`graphene_django/types.py` camelizes only when true, default on) and no equivalent knob exists here, so the row is owed under any outcome.
- [ ] TODO-ALPHA-053-0.0.15's Slice 5 joint-cut sentence and its GLOSSARY-flip DoD were amended for every card on the line, and the dependency edge sequencing it behind this card was added, at the 2026-08-29 board review; verify both still hold at wrap.
- [ ] Docs fold-in and card wrap: GLOSSARY terms via the DB, TREE regenerated, card flipped Done, KANBAN regenerated, `import_spec_terms` green.
- [ ] Full suite green under `fail_under = 100`; live-first placement respected. No version quintet, GLOSSARY status flip or CHANGELOG entry — all three ride TODO-ALPHA-053-0.0.15's joint `0.0.15` cut, which lands last on this line.

#### Files likely touched

- `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/utils/relations.py`
- `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/rest_framework/resolvers.py`
- `django_strawberry_framework/connection.py` and `django_strawberry_framework/error_policy.py` (argument-rejection surfacing: `connection.py` already raises `GraphQLError` for `first` + `last`, and the masking rule whose untouched branch the rejections must land in lives in `error_policy.py`)
- Mirrored `tests/` modules plus live coverage under `examples/fakeshop/test_query/`

#### Verified in upstream

- 🍓 `strawberry_django/fields/types.py` #"GeneratedField" resolves type and nullability from `output_field`.
- 🍓 `strawberry_django/fields/types.py` #"TextChoicesField" reuses the consumer's `choices_enum`.
- ⚛️ threads `str(field.help_text)` into every converter unconditionally; 🍓 ships the same behind `strawberry_django/settings.py` #"FIELD_DESCRIPTION_FROM_HELP_TEXT".
- ⚛️ `graphene_django/settings.py` #"CAMELCASE_ERRORS" (default on) camelizes `ErrorType` keys in `graphene_django/types.py`.

#### Why it matters

- The beta line is defined as feature parity with both upstreams. These six are the entire remaining build-side delta after the `0.1.0` parity audit homed everything else: two type-creation failures a migrant cannot work around (`through=`, `GeneratedField`), a whole-schema SDL regression (`help_text`), a duplicate-enum surprise, a mixed error wire format no test can see, and rejections that read as bugs. Closing them before `0.1.0` is what makes the parity claim on TODO-ALPHA-057-0.1.0 true rather than asserted.

#### Dependencies

- Nothing blocks this card. The sequencing runs the other way: TODO-ALPHA-053-0.0.15's four-DRY-axes file list covers `mutations/{sets,inputs,resolvers,permissions}.py`, `rest_framework/*`, `utils/*`, `connection.py` and `types/base.py` — every file this card touches except `types/converters.py` — so that card must be sequenced behind this one, exactly as it is already sequenced behind the debug extraction on the same line. That dependency edge and note are owed on that card, not this one.
- This card lands first on the shared `0.0.15` line; the debug extraction and the DRY squeeze follow, and the DRY squeeze still lands last and owns the joint cut.

#### Note

- Renumber consequence, already enacted when this card was written: inserting this card at 050 shifted the 21 cards then numbered 050-070 up by one, to 051-071 (the list-field argument card later inserted at 050 shifted them again). Their spec filename stems, the `spec-NNN` and `TODO-*-NNN-*` references across the tree, the bare prose numerals, and the board DB's own text columns (`CardItem.text`, `CardReference.raw_text`, `Card.planning_note`, `BoardDoc.body`) all rot with them and need the three-grammar sweep.
- This card's spec is not written. It takes `docs/SPECS/spec-051-parity_gaps-0_0_15.md`, a stem the 2026-08-29 renumber sweep freed by moving the DRY-squeeze spec to `spec-053-boundary_dry_squeeze-0_0_15.md`.

#### Card references

- Related: Its masked-rejections open question is discharged by this card. -> `TODO-ALPHA-057-0.1.0` - Beta release (cleanup, verification, alpha → beta)
- Related: Owed the `CAMELCASE_ERRORS` row on its upstream-settings disposition table, and already carries the `through_defaults` refusal this card's `through=` guard is what makes safe. -> `TODO-BETA-071-0.1.8` - Migration and adoption guides
- Related: Shares every file in this card's Files-likely-touched list except `types/converters.py`, so it is sequenced behind this card the same way it is sequenced behind the debug extraction. -> `TODO-ALPHA-053-0.0.15` - Boundary hardening and system-wide DRY squeeze
- Related: Owns `convert_choices_to_enum()` naming and the enum-reuse cache on the far side of the beta cut; this card lands the enum-reuse behaviour that card then names. -> `TODO-BETA-065-0.1.4` - Stable choice enum naming override

<a id="extract_djangodebugextension_into_the_standalone_django_strawberry_debug_package"></a>
### [TODO-ALPHA-052-0.0.15 - Extract DjangoDebugExtension into the standalone django-strawberry-debug package](KANBAN.html#extract_djangodebugextension_into_the_standalone_django_strawberry_debug_package)

- Priority: Medium
- Status: To Do
- Relative size: M
- Labels: `internal`
- Spec: [spec-052-debug_extraction-0_0_15.md](docs/SPECS/spec-052-debug_extraction-0_0_15.md)

#### Dependencies

- `DONE-044-0.0.14` - Response-extensions debug middleware

#### Scope

- Slice 1 - the new package: brand-new standalone repo riodw/django-strawberry-debug; pyproject (deps Django>=5.2 + strawberry-graphql>=0.316.0, NO dependency on django-strawberry-framework), src layout, MIT, README ported from spec-044's user-facing API (posture, wire contract, graphene narrowing table, async boundary); debug.py moved VERBATIM except the single logger swap (logging.getLogger("django_strawberry_debug")); the 1,019-line suite moved onto a self-contained harness; CI matrix green; 0.1.0 published to PyPI.
- Slice 2 - the framework seam: delete extensions/debug.py + tests/extensions/test_debug.py; rewrite extensions/__init__.py as the require_optional_module-guarded PEP 562 lazy re-export; add [project.optional-dependencies] debug = ["django-strawberry-debug>=0.1.0"] (+ dev-group pin); absence test on the None-sentinel shape; ONE live-tier re-export + optimizer-composability proof; the probe scaffold slims to that seam test; fail_under = 100 re-verified.
- Slice 3 - docs fold-in (GLOSSARY via DB, README, TREE regen, dry-file doc retired) and card wrap; the 0.0.15 version-quintet cut and CHANGELOG entry belong to the boundary-hardening/DRY-squeeze card, which shares this patch line and lands last.

#### Definition of done

- [ ] django-strawberry-debug 0.1.0 on PyPI: verbatim-moved debug.py (logger swap only), moved suite green on its own harness, CI matrix green, README carrying posture + wire contract + async boundary.
- [ ] This repo: extensions/debug.py and its package-tier suite deleted; extensions/__init__.py is the guarded lazy re-export; [debug] extra added; absence sentinel test + one live seam/composability test in place; probe scaffold slimmed.
- [ ] pip install django-strawberry-framework[debug] resolves in an isolated venv and `from django_strawberry_framework.extensions import DjangoDebugExtension` works; with the extra absent, import-innocence + the install-hint error hold.
- [ ] Full suite green under fail_under = 100 after the deletion.
- [ ] Docs fold-in, card flipped Done, KANBAN regenerated, import_spec_terms green - no version quintet, GLOSSARY status flip or CHANGELOG entry, all of which ride the boundary-hardening/DRY-squeeze card's joint 0.0.15 cut.

#### Files likely touched

- New repo (riodw/django-strawberry-debug): pyproject.toml, src/django_strawberry_debug/{__init__,debug}.py, tests/, CI workflows, README, CHANGELOG
- This repo: `django_strawberry_framework/extensions/{__init__,debug}.py`, `tests/extensions/test_debug.py`, `tests/_soft_dependency.py`, `examples/fakeshop/test_query/test_debug_extension_api.py`, `pyproject.toml` (extras + dev group), `uv.lock`
- Slice 3 docs: `docs/GLOSSARY.md` (DB + re-render), `README.md`, `docs/README.md`, `docs/TREE.md`, `TODAY.md`, `CHANGELOG.md`, KANBAN regen

#### Architectural posture

- Extraction, not the in-tree leaf: the split test applied to opposite facts. The optimizer split was rejected on bidirectional fusion; this module has zero reverse coupling, one trivial forward import, and a framework-independent audience - the one place extraction sheds weight without cutting a live seam.
- The name django-strawberry-debug is EARNED by generality (maintainer's rule: the generic family name only if it works beyond this framework; the import-surface proof settles it). Zero behavior change: the wire contract, capture mechanics, and developer-only posture move verbatim - the logger swap is the only code delta.
- The strawberry-graphql>=0.316.0 floor STAYS in the framework: per-operation extension isolation is a release-wide engine-lifecycle fix affecting every consumer schema, debug enabled or not. It was never debug-only; it does not travel with the feature.
- The shipped import path survives byte-for-byte via the guarded re-export - the extraction is invisible to any 0.0.14 consumer who installs the extra. No deprecation machinery at 0.0.x.

#### Why it matters

- A dead-weight review of the package found extensions/debug.py (DjangoDebugExtension, card 044's feature) is the one genuinely extractable module: its import surface is stdlib + Django + graphql-core + Strawberry plus exactly one package symbol (the root logger), nothing in the package imports it back, and it works against ANY strawberry-graphql + Django schema - no DjangoType, registry, or optimizer required.
- Carrying it in-tree costs this distribution ~1,900 lines (472 impl + ~1,375 tests) for a feature with no in-package consumer, while a standalone package serves a real audience beyond the framework. The same evidence standard that rejected the optimizer split (bidirectional fusion) endorses this one (zero coupling).
- Sequenced BEFORE the boundary+DRY card deliberately: extraction shrinks that card's surface - extensions/ becomes a soft-dependency leaf (the rest_framework/ shape) before the import-linter contracts are authored, and the extras block gains its first member for the DRY card's four to join.

#### Dependencies

- Sequenced behind DONE-044-0.0.14: the extension must SHIP at 0.0.14 before it is extracted (extracting an unreleased feature would rewrite card 044 mid-flight). The whole card - not just the cut - waits for the 0.0.14 release. Within the card, Slice 2 is gated on Slice 1's published 0.1.0 artifact.

#### Card references

- Dependency: `DONE-044-0.0.14` - Response-extensions debug middleware

<a id="boundary_hardening_and_system_wide_dry_squeeze"></a>
### [TODO-ALPHA-053-0.0.15 - Boundary hardening and system-wide DRY squeeze](KANBAN.html#boundary_hardening_and_system_wide_dry_squeeze)

- Priority: High
- Status: To Do
- Relative size: XL
- Labels: `internal`
- Spec: [spec-053-boundary_dry_squeeze-0_0_15.md](docs/SPECS/spec-053-boundary_dry_squeeze-0_0_15.md)

#### Dependencies

- `DONE-044-0.0.14` - Response-extensions debug middleware
- `WIP-ALPHA-050-0.0.15` - `DjangoListField` argument surface: `offset` / `limit` and `orderBy`
- `TODO-ALPHA-051-0.0.15` - Upstream parity-gap closure
- `TODO-ALPHA-052-0.0.15` - Extract DjangoDebugExtension into the standalone django-strawberry-debug package

#### Scope

- WP-A boundary hardening: promote the optimizer's inward-facing API (kill cross-boundary `_context` imports), enforce the dependency architecture with `import-linter` contracts in CI/pre-commit, declare packaging extras (`drf`, `channels`, `keyset-encryption`, `debug-toolbar`) over the existing soft-dependency seams.
- WP-B mechanical DRY batch (~450-550 lines): query-side delegate absorption into `sets_mixins.py`, write-side `PermissionClassesMixin` + metaclass merge, inputs micro-hoists, resolvers micro batch, root/optimizer/types small batch.
- WP-C structural DRY batch (~500-600 lines): fold `_run_delete` and the plain-form pipeline onto the shared write skeleton, filter converter/normalizer dispatch table, `install_input_namespace()`, bind-drain merge, connection dispatch tails, `slot_child_selections()`, `iter_relation_path()`, budgeted-walk primitive, column-backed conversion sharing (mutations+forms only), finalizer error formatters, underscore alias deletion, `editable_input_fields` onto `resolve_effective_fields`.
- WP-D contract-level DRY (~150 lines + doc debt): single-window planner scheme through `_divergent_key_windows`, walker `_resolve_field_map` dual-contract retirement (FieldMeta fallback), model relation decoder over the shared spine.
- Slice 5: docs fold-in, the joint `0.0.15` version cut (shared with the other three `0.0.15` cards; this card lands last so it owns the quintet), CHANGELOG entry, card wrap.
- Widen `views.py::_canonicalizes_to_utf8` to catch `ValueError` and `UnicodeEncodeError` alongside `LookupError`. Pre-existing, fail-loud and not reachable from the wire, which is why it was left; a codec whose name canonicalizes but whose lookup raises escapes as an unrelated 500.
- A shared "is this one of our views?" recognizer with `middleware/debug_toolbar.py` is now a decidable question: the constraint that forced `middleware/request_body.py` to recognize by marker attribute (it must not import `views.py`) was removed when the ordering marks moved to `_boundary_ordering.py`. `debug_toolbar` recognizes a package view by class through an *upstream* `BaseView` import, so a narrower shared recognition needs no `views.py` import either. Revisit only when a third middleware needs the same recognition, or when two need to agree about one callback - not as a DRY sweep for its own sake.
- `middleware/request_body.py::_package_view_instance`'s docstring still says `process_view` is "a hook whose every other outcome is a controlled response" while the same docstring records that a boundary the recognition *accepted* which raises anything but `HTTPException` leaves the hook uncaught. Scope the absolute to the outcomes the recognition decides. The behaviour must not change: a guard there would sit across the body cap's own errors.
- `_request_body.py`'s Decision 7 paragraph says the seekability probe "reaches for four capabilities"; the code guards six call sites across five `try` blocks - `_declares_seekable`'s `seekable()`, the position `tell()`, `stream.seek(0, SEEK_END)`, `_position_restored`'s restoring `seek`, its verifying `tell()`, and the `end - position` subtraction, with `_position_restored` guarding two in one `try`. Both the decision paragraph and the spec's `## Edge cases` capability bullet repeat the four-item list, so the fix has two sites; four other sites cite that paragraph's bolded opener by substring, which is why it was not corrected in passing.
- `consumers.py::send_revalidated_operation_frame`'s docstring calls the derived adapter a "two-line delegation"; `_RevocationGatedWebSocketAdapter.send_json`'s body is four statements. Pre-measured replacement, to carry verbatim rather than re-derive: "a four-statement delegation - the frame-type test, the plain `super()` delegation for a non-information-bearing frame, its `return`, and the gated call". Owner is the next pass that legitimately opens `consumers.py`, not an opening of that file for its own sake.
- The WebSocket `Host` denial in `consumers.py` logs nothing, while the other two fail-closed paths on that connection now do. Three separate passes recommended the same fix - log all three, no wire change. Supporting evidence already gathered: Django's own `django.security.DisallowedHost` logs every `SuspiciousOperation` at `error` level, read at Django 6.0.5 and NOT confirmed at the declared floor, so confirm at the floor before relying on the parallel.
- `conf.py`'s `MAX_REQUEST_BODY_BYTES` docstring carries the clause "EXCEPT for a multipart request" without saying that the multipart carve-out is POST-scoped. A multipart content type on any other method is counted like any other body, which is the stricter direction and what the other four surfaces of this wording already say. Grep `POST-scoped` over `conf.py` to confirm it is still open.
- `auth/mutations.py` carries repeated literals - `password` seven times, `register` four, `current_user` three. Pre-existing rather than introduced by the transport work, which is why it was never folded into a security pass.
- The DRY `parse_json` note attributes `_validate_upstream_shape` to "the upstream-mounted path". That gate decides whether the patch installs at all, for **every** mount, so pairing it with the genuinely path-scoped `UnicodeDecodeError` translation under one prepositional phrase is loose. It makes no "only mount" claim, so nothing is false - it is imprecise, and it is the shape a stricter reviewer will raise.
- The `_optimizer_field_map` rename left four live-code sites naming a symbol the package no longer defines. It has zero occurrences in `django_strawberry_framework/`; the walker reads `DjangoTypeDefinition.field_map` through `optimizer/walker.py::_resolve_field_map`. The sites: `tests/optimizer/test_field_meta.py:322` `::test_optimizer_field_map_populated`, `:339` `::test_optimizer_field_map_contains_relations`, `:362` `::test_optimizer_field_map_respects_fields_filter`, and the token in `scripts/review_inspect.py:42`. Fold into WP-D's `_resolve_field_map` dual-contract retirement, which already opens both the walker and its tests. The prose survivals in `CHANGELOG.md` / `KANBAN.md` / `spec-010` / `spec-016` are correct as history and are not in the sweep - widening it into a documentation sweep is the error to avoid. A second instance of the same shape is carried by `TODO-ALPHA-057-0.1.0`: `_collect_scalar_only_fields` is likewise absent from the package while `spec-003-optimizer_nested_prefetch_chains-0_0_2.md:27` still names it in the present tense.
- Send a rejected subscription the `RESOURCE_LIMIT_EXCEEDED` envelope on both WebSocket protocols. Enforcement is not the gap: a subscription enters the extension runner's `operation()` and `executing()` exactly as a query does, so the document scan and the value walk both fire and a violating subscription IS refused. Upstream's non-streaming path converts a pre-execution exception into an `errors` entry and its streaming path does not, so the client sees a `complete` close instead of the code. Write the fix against that broad-versus-narrow `except` asymmetry, pin no private upstream symbol, and re-measure the asymmetry across the whole open-ended `strawberry-graphql>=0.316.0` range rather than the installed wheel (spec-047 Decision 13).
- Charge upload bytes before Django's upload handlers stream the body, through a package-owned upload handler or streaming body reader, so the upload bounds stop being post-materialization. Django has already streamed a multipart body by the time coerced values exist, so the seam sits beside the request-body cap rather than inside the value walker - which is why spec-047 narrows its own goal to "before any resolver, serializer, validator or storage backend touches the files" (spec-047 Decision 13).
- Refuse an oversized numeric literal as a typed resource rejection carrying `RESOURCE_LIMIT_EXCEEDED` rather than as the malformed-input failure CPython's `sys.get_int_max_str_digits` raises during JSON parsing or literal coercion. The request is already refused; only the envelope is wrong. A configured bound means a pre-coercion scan of the raw variables JSON, which is the body cap's layer rather than the walker's (spec-047 Decision 13).
- `optimizer/walker.py::_record_relation_access` must run before the FK-id-elision short-circuit in `optimizer/walker.py::_plan_select_relation` - it appends the FK `attname` the elided resolver reads (`types/resolvers.py::_build_fk_id_stub`), so reversing the order silently reintroduces the N+1 the elision exists to remove. The invariant is stated in the helper's docstring and in `spec-003-optimizer_nested_prefetch_chains-0_0_2.md`'s same-query-recursion contract, but no test or assertion pins the order. Add a guard: a call-site assertion or a walker test that fails when the two statements are swapped.
- `optimizer/plans.py::_prefetch_lookup_paths` recurses through nested `Prefetch` queryset lookups with no depth cap, while its sibling `optimizer/plans.py::runtime_path_from_path` is explicitly bounded at `_MAX_PATH_DEPTH` with a documented cyclic-or-corrupt rationale. The walker cannot construct a cyclic `Prefetch` graph, so the asymmetry is theoretical - but the codebase elsewhere treats unbounded traversal as a defect class, so either bound it to match its sibling or record why the asymmetry is deliberate.
- `exceptions.py::ConfigurationError`'s fourth docstring example - "Two `DjangoType` subclasses registering against the same model" - has been false since `0.0.6`: `registry.py::TypeRegistry.register` appends, and the docstring on `register` itself opens "Multiple types may register against the same model". What actually raises is narrower and split across two moments: duplicate-primary (`#"is already the primary type"`) and flipped-primary-on-re-register (`#"primary flag cannot be flipped on re-register"`) at registration, and ambiguity-by-omission at `types/finalizer.py::_audit_primary_ambiguity`, which is finalization-time. The line does not merely overstate - it tells a consumer the sanctioned multi-type pattern is an error. The same docstring's deferred-key example says "before the spec that owns it has shipped" where the runtime message deliberately says "feature" (the `83c25963` vocabulary correction); it is the last in-source survivor of the retired wording. Scope is one file and these two examples - not a license for a package-wide docstring sweep. A documentation defect in source, not a correctness defect: no behavior is wrong, no test asserts the docstring, and `fail_under = 100` is unaffected. Authorized by the spec-005 residual cycle and never made, because the round that owned it was never dispatched.
- `types/base.py::_format_unknown_fields_error`'s docstring names `Meta.fields`, `Meta.exclude`, and `Meta.optimizer_hints` as its complete caller set; the measured reach is five direct call sites in three functions carrying six distinct `attr` labels over seven `Meta` keys. Pre-measured by AST walk, to carry verbatim rather than re-derive: `::_validate_optimizer_hints` x2 (`optimizer_hints`), `::_select_fields` x2 (`fields`, `exclude`), and one forwarding site in `::_selected_meta_targets` (`attr=attr`) supplied by `::_validate_nullability_override_targets` (`nullable_overrides/required_overrides` - one label, two keys), `::_validate_filesystem_path_targets` (`filesystem_path_fields`), and `::_validate_relation_shape_targets` (`relation_shapes`). Write the replacement from the enumeration, not from the counts - every defect in this item's own history was a numeral standing in for a population: "eight distinct `attr` values" counted `attr=` occurrences, and "five call sites, three of them via `_selected_meta_targets`" attached the three to the wrong noun (exactly one of the five is inside it). This is the one error shape spec-005 pins as public contract, which is why the under-statement matters. Same authorization and same never-dispatched status as the `ConfigurationError` docstring item.
- `tests/types/test_base.py:1278` carries a comment naming `convert_relation`, a symbol with zero occurrences in `django_strawberry_framework/` - relation annotations resolve through `types/converters.py::resolved_relation_annotation`. Fold into whichever WP batch legitimately opens `test_base.py`; it is the same shape as the `_optimizer_field_map` item above and takes the same boundary - the present-tense survivals in shipped specs (`spec-009`, `spec-010` and `spec-019` all still name `convert_relation`; `spec-008` did until its 2026-08-14 residual reconciliation removed the last one, and it now greps 0, so do not re-add it on a later sweep) are correct as history and are not in the sweep. The same file carries a second, unrelated stale reference worth fixing in the same opening: `:212`'s test docstring reads "must raise until the spec that owns it ships", the last occurrence anywhere in the tree of the deferred-key vocabulary commit `83c25963` retired in favour of "feature". The package-side half of that correction landed at `65fd201e`, which is what leaves this one exposed - `grep -rn 'spec that owns' django_strawberry_framework/` now returns nothing while this line survives.
- The `[spec-011]` renumber artifact reaches six live-code sites this card's WP batches already open: `django_strawberry_framework/types/base.py` carries five occurrences and `django_strawberry_framework/types/resolvers.py` one, whose quoted substrings resolve to spec-015 Decisions 4, 7, and 9 (`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`, the pre-renumber `spec-011`), plus `tests/types/test_base.py` and `tests/filters/test_sets.py`. Measured 2026-08-15 by the spec-011 residual cycle (`docs/builder/bld-011-final.md` deferred-work catalog). Same shape and same boundary as this card's `_optimizer_field_map` and `convert_relation` items: fold into whichever WP batch legitimately opens the file and retarget the citations to `spec-015` - widening into a documentation sweep is the error to avoid; the documentation half of the cluster is owned by `TODO-ALPHA-057-0.1.0`. **Re-derivation trap, measured 2026-08-17 by the spec-015 residual cycle:** the population is 8 OCCURRENCES across 4 files, but the natural command for it - `git grep -oh '\[spec-011\]' | wc -l` - reports **9**. The extra row is git's `Binary file examples/fakeshop/db.sqlite3 matches` line, and that file's own hits are kanban card text, out of scope for this bullet. Two independent passes hit the same 9 and had to resolve it; count occurrences per file (`types/base.py` 5, `types/resolvers.py` 1, `tests/types/test_base.py` 1, `tests/filters/test_sets.py` 1) rather than trusting the tree-wide total, and do not read 9 as evidence the cluster grew.
- `django_strawberry_framework/types/definition.py::DjangoTypeDefinition`'s `fields_class` docstring reserves the slot for the pre-renumber `TODO-BETA-046-0.1.1`; post-renumber that id names the shipped transport card and the live FieldSet owner is `TODO-BETA-059-0.1.1`. Same shape and same boundary as this card's `_optimizer_field_map` / `convert_relation` / `[spec-011]` items: fold into whichever WP batch legitimately opens `types/definition.py` and retarget the citation - or let the FieldSet card's own wiring slice absorb it if that lands first. Measured by the spec-009 residual cycle (`docs/builder/bld-009-final.md` deferred-work catalog item 6), standing since that cycle's R1/R1b.
- WP-D contract question, both halves answered together: BOTH dynamic-set factories are production-unconsumed - `orders/factories.py::get_orderset_class` / `_dynamic_orderset_cache` and the filter twin `get_filterset_class` have no package consumer; the only importers are `tests/`. Dead code or deliberately symmetric skeleton is a contract-level call, not a worker's, and the answer sequences two other edits: the GLOSSARY `OrderSet` entry's closing clause ("so no dynamic order factory is shipped" - imprecise since `fd0c7327`: a factory IS shipped, it simply has no production consumer) is a Slice 5 glossary-DB edit whose right wording depends on this answer, and `spec-027`'s auto-generation scrub (owned by the beta-release card's repo-wide deferral sweep) should state "no auto-generation ships" flatly if the factories go, or point at the kept skeleton if they stay. Measured by the spec-009 residual cycle (`docs/builder/bld-009-final.md` deferred-work catalog items 14-15).
- `django_strawberry_framework/orders/inputs.py` carries the retired reserved-slot rationale a third and fourth time in one module: `::_build_input_fields #"reserved -- see"` and `::_build_input_fields._leaf_of #"is a future-extension"`. Neither is false today - the first defers to `convert_order_field_to_input_annotation`'s docstring and the second describes a converter affordance that genuinely is unused - but they are the same sentence's third and fourth instances in one file, which is this card's DRY subject. The first two instances were rewritten at `f02dfda7` (the spec-028 DISTINCT ON retirement) and now read "kept for shape-symmetry"; these two were outside that commit's scope and still carry the older wording, so the module now states the same idea two different ways. Fold into whichever WP batch opens `orders/inputs.py`. Measured by the spec-009 residual cycle (`docs/builder/bld-009-final.md` deferred-work catalog item 19), re-verified 2026-08-16.
- Do NOT sweep the six remaining `docs/spec-NNN-...` spellings in `.py` files: all six are decided non-edits, and an undifferentiated sweep breaks a passing test and destroys a deliberate example. `scripts/check_spec_glossary.py`'s 4 are usage examples in a docstring whose own prose then discusses what an archived spec keeps, so the pre-archive form is the point; `examples/fakeshop/test_query/test_glossary_api.py`'s 2 (`spec_path=` and the `specPath: { exact: ... }` assertion) are fixture DATA matching a glossary DB row, not a path claim - rewriting them breaks the test (the DB row itself is stale because `import_spec_terms::_sync_spec_mentions` orphans `GlossarySpecMention` rows at the pre-archive path, which is this card's separate live defect). The edit half of this item is DISCHARGED: the six test-module docstrings that genuinely made a stale path claim - `tests/test_connection.py`, `tests/test_list_field.py`, `tests/test_relay_node_field.py`, `tests/test_relay_connection.py`, `tests/optimizer/test_multi_db.py`, `tests/testing/test_relay.py` - all now read `docs/SPECS/`, three re-relativized by the spec-032 residual cycle and three by its follow-on sweep (2026-08-27, verified: every rewritten target EXISTS at `docs/SPECS/` and is MISSING at `docs/`). Original population measured by the spec-009 residual cycle (`docs/builder/bld-009-final.md` catalog item 22, which recorded only the `test_connection.py` site); enumerated 2026-08-16 as 12 occurrences, 6 edits. The board-DB half of this same defect is likewise discharged: the 13 stale `docs/spec-NNN` paths in kanban card bodies were rewritten in the same 2026-08-27 sweep, leaving only the 4 legitimate in-flight paths (`057`, `058` x2, `060`), which name unwritten specs whose proper working location IS `docs/`.
- `django_strawberry_framework/filters/sets.py::FilterSetMetaclass.__new__ #"meta_class.fields = meta_class.filter_fields"` mutates the **consumer's** `Meta` class in place to alias `filter_fields` onto `fields`, and its `hasattr(meta_class, "fields")` guard sees **inherited** attributes - so a consumer `Meta` that subclasses another `Meta` already carrying `fields` silently skips the alias, and a consumer whose `Meta` is shared across two FilterSets has the first one's aliasing observed by the second. Pre-existing, shipped and tested; recorded as a design question, not a defect claim - the fix direction (copy the Meta or resolve the alias into the new class's attrs rather than writing to the consumer's object) is a contract-level call that belongs with this card's boundary work. Measured by the spec-009 residual cycle (`docs/builder/bld-009-final.md` deferred-work catalog item 23).
- Three stale pointers left in the Relay foundation's own files by the spec-015 residual cycle's rationale move, all in files this card's WP batches already open. Same shape and same boundary as this card's `_optimizer_field_map`, `convert_relation` and `[spec-011]` items: fold into whichever WP batch legitimately opens the file and retarget - do not open these files for the citations' own sake, and do not widen into a documentation sweep. (a) Two sites cite spec-015's Risk note for the `ConfigurationError` wrap - `django_strawberry_framework/types/relay.py::apply_interfaces` (spelled `spec-015 Risk note #"..."`) and the matching wrap row in `tests/types/test_relay_interfaces.py` (spelled `spec-015 #"..."`) - and `## Risks and open questions` no longer lives in the spec: the residual cycle moved it to `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md` and quoted the cited bullet verbatim there, so the citation still resolves inside the spec's own file family and nothing is dangling today. Retarget both at the companion or at Decision 1's own `ConfigurationError`-wrap sentence. The `relay.py` site has since been line-wrapped, so its quoted substring is split across a line break and no longer matches a plain grep - the second way an anchor dies, and the reason this is worth retargeting rather than leaving. (b) `tests/types/test_relay_interfaces.py::test_relay_node_strips_django_id_annotation`'s docstring points at `tests/types/test_definition_order_schema.py` for end-to-end coverage of the same id-suppression path. That file still EXISTS, so no existence check catches it; it carries zero Relay coverage since `be9130e3` retired its Relay extensions (`grep -ciE 'relay|node|global_id'` returns 0), and the end-to-end coverage now lives in `examples/fakeshop/test_query/test_library_api.py`'s two `_live` twins. A reader following the pointer lands on a real file that cannot support the sentence. Measured 2026-08-16 by the spec-015 residual cycle (`docs/builder/bld-015-final.md` deferred-work catalog items 2 and 5), re-derived at that cycle's close.
- No test pins Decision 7's relation-traversal invariant unchanged relative to a NON-Relay target, and this card's `_record_relation_access` ordering guard is the same shape of missing-guard item, so the two belong in one opening of the optimizer test tree. `test_relay_target_relation_planning_unchanged` was that A/B row - a Relay target under a non-Relay root, asserting `"category" in plan.select_related` - built at `e6907fa8` and retired at `4f4db722` in favour of live coverage; confirmed absent from `tests/` and `examples/` on 2026-08-16. Its live replacements pin planning ACROSS Relay targets but not the comparison, and the comparison can no longer be made in the live tier at all: since spec-034's cascade every `products` type declares a `get_queryset`, so all of them take the windowed `Prefetch` downgrade and no non-Relay arm survives to compare against. Nothing regressed and nothing was skipped - the comparative assertion is simply unpinned, and a package-tier row is now the only place it can live. Measured 2026-08-16 by the spec-015 residual cycle (`docs/builder/bld-015-final.md` deferred-work catalog item 4).
- WP-D's `_resolve_field_map` dual-contract retirement must DELETE the contract's documentation rather than re-point it. When the registry-coverage gate lands and the unregistered-model fallback disappears, three sites retire together: the `DUAL CONTRACT` paragraph in `django_strawberry_framework/optimizer/walker.py::_resolve_field_map`, which names its own exit condition (#"registry-coverage gate lands"); that paragraph's cross-reference to `django_strawberry_framework/types/resolvers.py::_field_meta_for_resolver`; and the first of the two bullets under `### Bounded exceptions to the single-source rule` in `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`. Re-pointing any of the three leaves a documented exception standing for a shape that no longer exists, which is worse than the debt it replaces. Two constraints the retiring slice inherits. First, the rejected alternative - have the walker's fallback build a `FieldMeta` so the resolver-side fallbacks can go instead - stays rejected, with its reasons in `docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`; it was raised and answered four separate times in the cycle that measured this, so reopening it needs a new argument rather than a fresh look. Second, the walker's own read rule goes with the fallback: `name` and `is_relation` are the only attributes both shapes carry (`django_strawberry_framework/optimizer/field_meta.py::_DjangoFieldLike`), so the standing rule that any other attribute must be read through a `getattr(..., default)` becomes dead weight the same slice should remove rather than preserve. Measured 2026-08-17 by the spec-016 residual cycle (`docs/builder/bld-016-final.md` deferred-work catalog item 9).
- Three rule-27 source-reference spellings left by the spec-016 consolidation, all in files this card's WP batches already open, none of them a behavior defect. (a) `django_strawberry_framework/optimizer/walker.py::_plan_prefetch_relation` cites `utils.relations.instance_accessor` in dotted form where rule 27 requires `django_strawberry_framework/utils/relations.py::instance_accessor`; the cycle that found it had that very file open and deliberately left it, because `instance_accessor` is not a spec-016 symbol and fixing it there would have been scope creep rather than thoroughness. (b) `django_strawberry_framework/optimizer/field_meta.py::_target_pk_name #"field shapes on the resolver path"` cites `_field_meta_for_resolver` as a bare symbol with no path at all, while the docstring of `::_from_field_shape` earlier in the same module already spells that same symbol correctly as `types/resolvers.py::_field_meta_for_resolver` - so one module states one convention two ways, which is this card's DRY subject rather than a separate citation nit. (c) `tests/test_registry.py::test_finalize_discards_consumer_authored_pending_relation_without_rewriting_annotation` names `_record_pending_relation`, a helper deleted at `f83bb71b` five days after the card shipped; the canonical read is now `django_strawberry_framework/types/base.py::_build_annotations`. Same shape and same boundary as this card's `_optimizer_field_map` and `convert_relation` items: fold into whichever WP batch legitimately opens the file, and do not widen into a documentation sweep - the present-tense survivals in shipped specs and in `CHANGELOG.md` are correct as history. Measured 2026-08-17 by the spec-016 residual cycle (`docs/builder/bld-016-final.md` deferred-work catalog items 1, 5 and 6).
- The bare-basename cross-folder citation shorthand is ACQUITTED as house style, but its ambiguous tail is not, and the population recorded for that tail is wrong in a way a sweep would inherit. Re-measured at HEAD `fa248bdf` on 2026-08-17 across package source, classifying every `basename.py::Symbol` citation by whether the citing file's own directory holds a file of that basename and whether the basename is unique package-wide: **97 same-folder occurrences** (unambiguous by proximity, never the question) and **61 cross-folder occurrences whose basename has exactly one home** (the genuinely acquitted class) both stay exactly as they are. **13 cross-folder occurrences cite a basename with more than one home and are un-acquitted:** `relay.py` x8, which has three homes (root, `types/`, `testing/`), cited from `extensions/resource_policy.py`, `filters/base.py` x2, `mutations/fields.py` x2, `mutations/resolvers.py`, `utils/querysets.py` and `utils/write_values.py`; and `resource_policy.py` x5, which has two (root and `extensions/`), cited from `types/base.py`, `types/resolvers.py` x2, `utils/connections.py` and `utils/context.py`. Every cited symbol has exactly one definition, so all 13 resolve by symbol today - this is a readability and drift defect, not a dangling reference - but it is precisely the ambiguity that made a bare `resolvers.py` citation a defect rather than a shorthand, which is why the tail does not survive the convention's acquittal. **The instrument defect is the part worth carrying:** the cycle that recorded this class reported 12 and enumerated only the double-backtick RST spelling, because that is what its census pattern matched; the two single-backtick occurrences in `filters/base.py` were invisible to it, and having landed 2026-07-13 and 2026-07-15 they were present the whole time - so they are exactly the two a sweeper working from the recorded figure would leave behind. Any pattern for this class must accept the single-backtick spelling as well as the double-backtick one. **Do not treat the total as stable:** the working tree at measurement carried a 14th occurrence in `mutations/resolvers.py` from another session's uncommitted edit, so re-derive against HEAD rather than trusting a number. Measured by the spec-016 residual cycle (`docs/builder/bld-016-final.md` deferred-work catalog item 7), whose recorded '~12 sites, each basename unique package-wide' is corrected here on both the count and the stated ground; that item's other correction stands - `filters/inputs.py`'s `connection_field.py::_get_trimmed_filterset_class` reference is not an instance of the convention at all, since no `connection_field.py` exists anywhere in the repository and the surrounding comment names strawberry-graphql-django's module, not this package's.
- Two vocabulary residues left in `tests/types/test_definition_order.py` by commit `2bcd7f96`, which rewrote `django_strawberry_framework/types/base.py::_id_annotation_is_relay_node_id` two days after the `0.0.6` release: it no longer calls `typing.get_type_hints` at all, reading `cls.__annotations__["id"]` and dispatching on `isinstance(raw, str)` instead, because `get_type_hints` handles nested forward references differently on py3.10 and py3.11+ and left a branch reachable only on the newer interpreter. The observable contract did not change - the same 11 Relay verdicts - so all three affected tests pin current, correct behaviour and only the naming is retired: no correctness defect, no assertion edit owed, and `fail_under = 100` unaffected. Same shape and same boundary as this card's `_optimizer_field_map` and `convert_relation` items: fold into whichever WP batch legitimately opens the file, and do not widen into a documentation sweep - the present-tense survivals in shipped specs are correct as history. (a) **The retired fail-soft vocabulary, four occurrences across three tests.** Two are test NAMES derived from the retired "fail-soft sub-case 1 / 2" wording, `::test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` and `::test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`; one is an inline comment in the second of those, #"the fail-soft annotation walk accepts the"; and one is a docstring on a third test, `::test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` #"raises via the fail-soft regex reject". **This population is not greppable by its own vocabulary** - only the comment and the docstring carry the literal string, so `grep -c 'fail.soft'` reports 2 against a real 4 and a sweep working from that figure stops two short. It is also how the count was first understated as three-across-two, corrected by the same cycle's integration pass before it was homed here. (b) **The `spec015_*` synthetic identifiers, four occurrences**, all test-local strings with no cross-file consumer: `app_label = "test_spec015_unsupported"`, `app_label = "test_spec015_grouped_choices"`, `app_label = "test_spec015_co_resident"`, and `stub_name = f"spec015_unresolved_relay_stub_{uuid.uuid4().hex}"`. The `015` is the pre-2026-07-30-renumber number of `DONE-019-0.0.6`. Renaming these is optional in a way (a) is not - the spec's `## Test strategy` and its Slice 1 unresolved-string entries record the spelling as the landed one rather than as a recipe to re-make, so leaving them is a defensible disposition; decide it rather than sweeping it. Both populations measured 2026-08-18 by the spec-019 residual cycle and re-derived at its final gate, identical at `HEAD` and in the working tree - only the line numbers differ, which is why no `path:NN` citation is given.
- The `orderBy` / pk-tiebreaker precision bundle - **take it whole or not at all**. It lands here rather than on `TODO-ALPHA-057-0.1.0` only because one of its three files is a `.py` docstring, which this card's WP batches can open and a documentation sweep cannot; the archived-spec sites travel with it and must NOT be split off into that card's sweep. Two imprecisions ride one sentence, repeated across three files. (i) The `orderBy` recourse names an argument `DjangoListField` does not itself wire - the factory's whole signature is `target_type`, `resolver`, `description`, `deprecation_reason`, `directives`, `max_rows`, `trusted_max_rows` (re-derived 2026-08-18); order arguments are added to both primitives by the Layer-3 specs, which the spec's own next bullet records two lines down. (ii) The comparative '`DjangoConnectionField` appends a pk tiebreaker' is unqualified where the shipped append is **conditional**: `django_strawberry_framework/connection.py::_finalize_queryset` delegates to `django_strawberry_framework/optimizer/plans.py::deterministic_order`, which appends `model._meta.pk.attname` only when `ends_in_unique_column(effective, model)` is False, and the keyset branch above that call (`cursor_field is not None and not explicit`) returns `qs.order_by(*cursor_field)` without reaching the helper at all, appending nothing. **Population - 3 files, and inside the spec 5 sites, not 1**: `docs/SPECS/spec-020-list_field-0_0_7.md` at `## Non-goals` #"adds no order tiebreaker", at `## User-facing API` #"**No order guarantee.**", and at three consecutive `### Decision 8` bullets (the `DjangoListField` boundary bullet, the `DjangoConnectionField` sibling carrying the unqualified comparative, and the asymmetry-is-deliberate bullet); `django_strawberry_framework/list_field.py::DjangoListField`'s docstring #"Ordering contract:", one passage carrying both halves; and `docs/GLOSSARY.md`'s `DjangoListField` entry (anchor `#djangolistfield`) at #"**Ordering.**", one paragraph carrying both halves, reached by a `GlossaryTerm.body` ORM edit plus `scripts/build_glossary_md.py` - this card's Slice 5 already owns a glossary flip. **Neither sweep token enumerates the population**: `tiebreaker` occurs 5 times in the spec and `orderBy` 3, and the two sets are not the same 5 lines. Deferred by the spec-020 residual cycle 2026-08-18 (`docs/builder/build-020-list_field-0_0_7.md` `## Deferred-work homing` item 3), which declared itself no-source-and-no-test and so could not execute the whole-population fix, while `docs/builder/worker-1.md` `## Spec custody` independently forbade the spec half alone because every statement is true as a conditional. Related but distinct, and the same adjudicator should see both: `TODO-ALPHA-057-0.1.0`'s repo-wide deferral sweep carries `spec-028`'s orphaned `0.0.9` `DjangoListField` orderBy-argument-integration deferral, which has no card anywhere.
- The retired `is_async_callable` characterisation survives on the two surfaces the spec-020 residual cycle could not reach, and they are the SAME two files as this card's `orderBy` / pk-tiebreaker bundle - fold the two items together. `django_strawberry_framework/utils/typing.py::_callable_inspection_target` peels `functools.partial` **and** `staticmethod` in a `while` loop, so the predicate is not a three-shape, one-hop one: it also sees a raw `staticmethod` descriptor and arbitrary nestings of the two (`partial(staticmethod_obj)` and `staticmethod(partial(callable_instance))`, both named in that helper's own docstring), pinned by `tests/test_list_field.py::test_djangolistfield_async_staticmethod_resolver_gets_get_queryset_applied`. The spec's six sites were rewritten by that cycle's Round 1. The two survivors: (i) `docs/GLOSSARY.md`'s `DjangoListField` entry (anchor `#djangolistfield`), its opening paragraph, #"and through a one-hop `functools.partial`" - closed at three shapes, omitting `staticmethod`, and the file's ONLY surviving `one-hop`; (ii) `django_strawberry_framework/list_field.py` #"``__call__``/``functools.partial``-aware superset of", the inline comment that cycle's root-cause note named as the vector which propagated the abbreviation into the spec three times, and which is narrower still - it closes at **two** shapes, not three. **Re-derived 2026-08-18, and the `.py` site is not greppable by either token**: `one-hop` occurrences are spec **0**, rationale **0**, `README.md` **0**, `docs/README.md` **0**, `docs/GLOSSARY.md` **1**, `list_field.py` **0**; `staticmethod` occurrences are spec **11**, rationale **8**, `docs/GLOSSARY.md` **0**, `list_field.py` **0** - so a `one-hop` sweep finds one of the two sites and reports itself complete. Low severity, understatement rather than falsehood - neither site states a wrong count, both name the correct authority, and `is_async_callable`'s own docstring is complete - but correcting the glossary alone would leave the generated consumer catalog disagreeing with the source comment a maintainer reads while editing the very branch it describes, and the spec now guards explicitly against the 'harmonization' that would re-narrow it. Surfaced by that cycle's integration pass as finding I1 and recorded at `docs/builder/build-020-list_field-0_0_7.md` `## Deferred-work homing` item 5; the integration artifact itself was deleted at closeout, so this bullet is the standing record.
- `docs/GLOSSARY.md`'s `SyncMisuseError` entry (anchor `#syncmisuseerror`) carries a raising-surface list that omits `DjangoListField`, which belongs there **twice over**. That entry's first bullet enumerates the surfaces as the Relay Node defaults' `resolve_node` / `resolve_nodes`, the `DjangoConnectionField` sync pipeline, the optimizer's sync prefetch-child build, and the `FilterSet` related-visibility derive, framing all four as 'when `cls.get_queryset` returns a coroutine'. `DjangoListField`'s sync default resolver reaches that same raise through `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`, called in `django_strawberry_framework/list_field.py` beside its `apply_type_visibility_async` twin; and `django_strawberry_framework/utils/querysets.py::reject_async_iterable_in_sync_context`, called from `django_strawberry_framework/list_field.py`, raises the SAME error for a **different** misuse - an async-only iterable met from synchronous execution - which the entry's `get_queryset`-coroutine framing does not describe at all. **The spec-020 residual cycle raised the cost of leaving it** (`docs/builder/build-020-list_field-0_0_7.md` `## Deferred-work homing` item 4): its Round 2 added an `**Async-iterable resolvers.**` paragraph to the `djangolistfield` entry, so that entry now carries **2** of the file's 10 inbound `#syncmisuseerror` links and the newer one sends a reader to an entry covering neither case they arrived from. Deferred there rather than fixed because widening the entry redefines another term's scope and its `Status:` line records `0.0.5` and so belongs to a different card - which is why it lands on this card's Slice 5 glossary flip, sharing one `GlossaryTerm.body` ORM edit and one `scripts/build_glossary_md.py` run with the two glossary halves in the items above. Never hand-edit the rendered file.
- One banned build-phase name survives in shipped package source: `django_strawberry_framework/types/base.py` #"hoist, spec-032 integration pass", the lead comment on `_RELAY_NODE_GATE_INHERIT_TAIL`. The standing rule is that a comment states the invariant and never how the change came to be, and a pass name resolves to nothing for a reader of the published package. **Population re-derived 2026-08-27, and it is exactly one.** A grep for the whole banned vocabulary (`integration pass|final gate|worker N|review round|slice N|residual cycle|reconciliation pass|consolidation pass|DRY pass`, case-insensitive) over `django_strawberry_framework/**/*.py` returns two lines, and the second is `filters/sets.py` #"TODO(spec-060 Slice 1)", a live staged-slice anchor that AGENTS.md L26 REQUIRES to name its doc and slice - do not sweep it, and do not let a wider regex fold it in. Tree-wide the only other `.py` hits are `scripts/bug_hunt.py`, `scripts/prove_failability.py`, `scripts/check_citations.py` and `tests/test_bug_hunt.py`, which are review-domain tools describing their own surfaces and are an explicit keep. Fix: preserve the technical claim (byte-identical at three compose sites) and the `spec-032` pointer, drop the pass name or re-point it at the owning Decision. Fold into whichever WP batch legitimately opens `types/base.py` - this card already opens that file for the `[spec-011]` renumber item and for `_format_unknown_fields_error`.
- **`tests/test_registry.py`'s connection and relay `clear()`-tolerance tests are controls that cannot fail, and their docstrings describe a mechanism the package retired.** `::test_clear_tolerates_unimportable_connection_submodule` and `::test_clear_tolerates_unimportable_relay_module` poison `sys.modules` and assert `registry.clear()` does not raise - but nothing on that path performs an import, so neither test can fail. `TypeRegistry.clear()` runs no import: it drops its own state, then replays already-resolved callables through `registry.py::iter_subsystem_clears`. The two callbacks are `connection.py::clear_connection_type_cache` (body: `_connection_type_cache.clear()`) and `django_strawberry_framework/relay.py::_clear_node_fields_declared` (body: `_node_fields_declared.clear()`), each a single `.clear()` on a module-level container registered at its OWN module's import time. The one import-bearing helper, `registry.py::_clear_if_importable`, has exactly one caller - `TypeRegistry.unregister`, not `clear()` - and `registry.py` #"do not go through this helper" says so in the package's own words. Deleting the poison from either test leaves it passing identically. **The filter and order twins are the same shape but NOT the same case, and they are the repaired precedent to copy**: their poison IS reachable, because `utils/inputs.py::clear_generated_input_namespace` makes two `_safe_import` lookups at clear time, and their docstrings were rewritten to say exactly that (#"``clear()`` itself imports nothing"). Both stale docstrings still claim an "``except ImportError`` guard in ``clear()``" - there is none - and a "cycle-safe local import", and both carry an inline comment claiming the poison exercises that guard. **The fix is executable, not a respell**: give each test a reachable failure mode or retire it, which is why it could not land in a docs-only cycle. Two citation defects ride the same edit, and they take OPPOSITE dispositions: the connection twin's `spec-030-connection_field-0_0_9` P3b label has **zero** occurrences in that spec (the label was homed in `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`, so retarget the companion), while the relay twin's `spec-032 Decision 8` pointer is CORRECT - that Decision does pin the node-field ledger and its `registry.clear()` co-clear - and must not be "fixed". Recorded by the spec-028 residual cycle as F9 (`docs/builder/DONE/build-028-orders-0_0_8.md`) and deferred there because respelling either asserts another card's contract; **re-derived 2026-08-27, and the re-derivation found the larger defect** - F9 graded it a stale docstring, and it is a test that cannot fail.
- The `workstream A/B/C/D` vocabulary names a build-plan partition that is documented **nowhere**, while live optimizer and connection code cross-references it. `workstream [A-D]` and the plan's own name, "connection window rigor", both grep **0** across `docs/` outside per-cycle `bld-*` scratchpads that close with their cycle. **Re-derived 2026-08-27: 35 occurrences across live `.py`, identical at HEAD and in the working tree** - 15 in `django_strawberry_framework/` (`connection.py` 7, `optimizer/lateral_fetch.py` 3, `optimizer/plans.py` 2, `optimizer/nested_planner.py` 1, `optimizer/selections.py` 1, `optimizer/walker.py` 1) and 20 in tests and examples (`tests/test_relay_connection.py` 8, `examples/fakeshop/test_query/test_library_api.py` 6, `tests/optimizer/test_walker.py` 3, `tests/optimizer/test_plans.py` 2, `tests/optimizer/test_selections.py` 1). The spec-027 residual cycle held this item "pending cohort F, not dropped" at a measured 12 package sites (`docs/builder/DONE/build-027-filters-0_0_8.md`); the package figure is 15 and the tree figure is 35, so **quote neither older number**. **Take it whole or not at all** - a partial claim fix is the residual cycle's dominant defect, and the package/test split runs straight through paired sites: `connection.py` #"the workstream-B defensive tail" is cited BY `tests/test_relay_connection.py` #"The workstream-B defensive tail in ``_resolve_from_window``". **The repair is a re-point, not a deletion, and it differs by letter.** B and C are spec-033's: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` documents the retained partition marker row and the conditional `_dst_total_count` under their real names (Decisions 4 and 5 as of this writing); `spec-030-connection_field-0_0_9.md` documents neither, so do not send them there. Read the Decision numbers off spec-033 at the time of the fix rather than from this bullet - that spec is under reconciliation as of 2026-08-27 and its numbering may move. D is different: those sites already carry `strawberry-django #697`, an upstream ticket the standing rule keeps and which already carries the why, so the plan-partition parenthetical can simply go (`optimizer/walker.py` #"the strawberry-django #697 bug class"). Six of the eleven files are dirty under the concurrent spec-033 cycle at the time of writing; re-measure at the opening rather than trusting the per-file split above.
- `tests/test_ci_governance.py`'s first docstring line still reads "Governance tests for the CI workflow definitions." while the module's own next paragraph says it holds **two** corpora - the least-privilege posture in `.github/workflows/` AND the first-party Python sources, whose `extensions=` construction shape is a per-request performance contract no assertion inside a single test module can hold repo-wide. The first line is the one `scripts/build_tree_md.py` renders, and `docs/TREE.md` carries it **twice**, once under each render root; both rendered sites carry the narrow claim (re-verified 2026-08-27). The `.py` edit is inside this card's fence, but the regenerate is **not optional** - CI runs `build_tree_md.py --check`, so a docstring edit without the render fails the build. Do both in one change at this card's Slice 5 doc-wrap, beside the GLOSSARY items, and never hand-edit the rendered tail. Recorded by the spec-029 residual cycle as Slice 2's Amendment 1 (`docs/builder/DONE/build-029-consumer_dx_cleanup-0_0_9.md`) and homed here for that regeneration cost. Scope note: this card's WP batches do not currently name `tests/test_ci_governance.py` or `docs/TREE.md`, so the file coverage is something this card's own planning must establish rather than something the board already asserts.
- Two absent pins on the shared input-namespace teardown helpers, both re-derived absent 2026-08-27. `tests/utils/test_inputs.py` pins `utils/inputs.py::_safe_import` twice - `::test_safe_import_returns_none_for_unimportable_module` (a name absent from `sys.modules` and unimportable) and `::test_safe_import_returns_none_for_missing_attribute_on_importable_module` (an importable module, absent attribute). Still unpinned: **(a)** `_safe_import` returning `None` for a **cold submodule of a poisoned package**, which is a third state and not either existing one; **(b)** `utils/inputs.py::clear_generated_input_namespace` making **exactly two** `_safe_import` calls - `utils/inputs.py` #"factory_cls = _safe_import(factory_module" and #"set_root = _safe_import(set_module" - for which no call-count assertion exists anywhere in the file. Both add executable statements, which is why the spec-028 residual cycle (D2, `docs/builder/DONE/build-028-orders-0_0_8.md`) deferred them out of a zero-boundary cycle and homed them here. **Pairs with this card's `clear()`-tolerance item above, and (a) is the seam between them**: state (a) is precisely what `::test_clear_tolerates_unimportable_filter_submodules` and its order twin create when they poison the package and its `inputs` module, and it is pinned today only indirectly, through a test asserting that `clear()` does not raise. Land the two items in the same opening or the same hole is left open from the other side. Scope note: this card's WP batches do not currently name `utils/inputs.py` or `tests/utils/test_inputs.py`.
- `docs/GLOSSARY.md`'s `Multi-database cooperation` entry states axis 3 flatly - "generated `Prefetch` child querysets do NOT inherit the root alias" - with no time qualifier, and the package has routed alias-late since well after `0.0.7`. The claim is true only at plan-construction: `optimizer/walker.py::_build_child_queryset` starts from `related_model._default_manager.all()` and threads no root alias. Three shipped sites decide the alias at fetch time instead, all re-verified present 2026-08-27 - `optimizer/single_parent_fetch.py` #"child_qs = spec.pristine_child_queryset.using(queryset.db)", `optimizer/nested_planner.py` #"correct alias-late predicate at fetch time", and `filters/sets.py` #"child_manager.using(parent_db).all()". **The spec side is already repaired and is the wording to copy**: `spec-023-multi_db-0_0_7.md`'s Decision 3 axis-3 bullet now reads "do NOT inherit the root queryset's `_db` **at plan-construction time**" and goes on to state that routing for a generated child is alias-late, decided against the parent rows actually in hand, naming two of the three sites. The GLOSSARY entry is the surviving unqualified restatement and it is the surface a consumer actually reads. Recorded by the spec-023 residual cycle as D2 (`docs/builder/DONE/build-023-multi_db-0_0_7.md`) and left open there because `GLOSSARY.md` is DB-generated: edit the `GlossaryTerm.body` in the fakeshop glossary app and re-render with `scripts/build_glossary_md.py`. Rides the same ORM edit and the same render as this card's `SyncMisuseError` glossary item. Never hand-edit the rendered file.
- The package's `strawberry.Schema(...)` docstring examples disagree with each other about `config=strawberry_config()`, and the file that settles the argument is about to be deleted. **Re-derived 2026-08-27: exactly four multi-line construction examples exist in package docstrings, and one carries the registration** - `extensions/debug.py` (module docstring) **yes**; `extensions/resource_policy.py::DjangoResourcePolicyExtension` (class docstring) no; `optimizer/extension.py` (module docstring) no; `optimizer/extension.py` (the singleton-in-a-factory method docstring) no. Population boundary, because the greppable token over-collects: a package-wide grep for `(strawberry\.Schema|DjangoSchema)\(` returns 25 hits, of which 21 are inline prose in the ``strawberry.Schema(...)`` form, the `class DjangoSchema(strawberry.Schema):` definition, or an error-message string - only those four open a constructor block. `scalars.py`'s `strawberry_config` docstring names the pattern inline without building an example and is adjacent, not a member. **The precedent-setting file is the one that goes away**: the debug-extraction card's Slice 2 deletes `extensions/debug.py`, and that card lands ahead of this one on this card's own `0.0.15` line, so by the time this card opens the population is three non-compliant sites and no in-package precedent - which is the sequencing that puts it here rather than leaving it to drift. **Homed, not decided**: whether a topic-scoped illustration (an optimizer example, a resource-policy example) should carry an unrelated `config=` line is a doc-style call for the maintainer, not a defect a spec cycle may settle. Either answer is cheap; three examples answering it differently is not. Recorded by the spec-025 residual cycle at its reopening (`docs/builder/DONE/build-025-scalar_map_helper-0_0_7.md`), which also recorded the instrument trap that travels with it: **count on `config=strawberry_config`, never on `config=strawberry_config()`** - the empty parens miss `extra_scalar_map=` call sites. Scope note carried forward from that cycle: this card's WP batches name `extensions/resource_policy.py` but not `optimizer/extension.py`, so two of the three target files are not established by the board text.
- `django_strawberry_framework/optimizer/plans.py::window_partition_for_prefetch` has zero production callers behind six tests, and the decisive evidence is a failability result rather than an argument. Production derives the relation partition from the join descriptor instead: mutating `optimizer/join_taxonomy.py::_partition_expr` (read by the shim AND by production) and mutating `optimizer/nested_fetch.py::attach_windowed_prefetch`'s `partition_by=` (read only by production) fail the SAME two rows both times - the restored shared-child test's - and NEITHER fails any row of the shim's own six-row family. Two of the six also pin an `OptimizerError` no production path can emit, while `exceptions.py` documents that raise as a live error mode. The question is existence, not style - delete the shim with its tests, or route production through it - so it needs the maintainer, not a sweep. This card's WP-D already opens `plans.py` for the Decision-4/5/8 strictness accounting and already names `plans.py::apply_window_pagination` in its byte-mirror pair with `lateral_fetch.py::build_lateral_sql`. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- Relocate the `to_attr` grammar to `django_strawberry_framework/utils/connections.py`. `connection.py` imports `_extend_only_projection`, `_relation_connection_to_attr` and `_relation_connection_to_attr_for_key` from `optimizer/nested_planner.py` and uses the latter two at the resolver's per-key probe. `spec-033` Decision 11 created `utils/connections.py` as "a neutral, cycle-safe home" precisely so the plan side and the resolve side share one source, and the `to_attr` grammar is as much a cursor-parity contract as the bounds are. **Note the corrected grounds: the privacy of the imported names is NOT the argument.** A cross-module `_`-private import is established house convention here - 76 statements across 45 modules, measured tree-wide - and on that basis the sibling flag against `optimizer/extension.py` importing `_active_strategy` is CLOSED as not-a-defect and should not be re-raised. The argument is placement, and there is no behavior change. Pairs with this card's C12 underscore-alias deletion: both open the walker/planner seam. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- One shared `_COERCION_ERRORS` constant under `utils/`. The tuple `except (ValueError, TypeError, AttributeError, KeyError, IndexError)` occurs **16 times across 3 files** - `connection.py` 11, `auth/mutations.py` 4, `utils/sessions.py` 1. **Match on the SET of exception names, never on the literal:** an exact-shape regex first reported 15 across 2 because the third site is written in the exploded multi-line trailing-comma layout this repo enforces, which is the same wrapped-source blind spot that defeated five other counts in that cycle. `except` accepts a tuple name, so the consolidation is mechanical. **`utils/sessions.py` carries a six-member superset (it adds `ImportError`) and must not be folded in.** No existing WP batch owns `utils/` or `auth/`; this needs its own partition. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- Name `_optimizer_runtime_prefixes`. The **string literal** occurs twice, both inside `getattr`, in one module (`optimizer/walker.py`); `optimizer/selections.py` carries the same name as a keyword argument. It is a cross-seam attribute-name grammar with no named constant - Low on its merits and cheap. Recorded with its measurement corrected: an earlier heading called it "a bare literal in two modules", which that finding's own body did not claim. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- `django_strawberry_framework/connection.py::_resolve_from_window`'s keyset legs are separable: 323 lines / 26 branch nodes, more than twice the file's next entry. The branch fan-out is the cross-product of four `FetchMode` shapes, the marker/probe split, and the keyset fork, and splitting the keyset legs out would roughly halve each half. **Explicitly not a defect** - the shape predicates already delegate to `utils/connections.py` rather than being re-spelled - so take it only if a WP batch is opening the function anyway. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- Resolve the one catalogued fail-open in the cascade walk: `django_strawberry_framework/permissions.py::_is_unsupported_forward_edge` #"getattr(field, \"is_relation\", False)" is a `getattr`-default on the fail-closed-vs-skip decision, and the two predicates beside it on the same line use plain attribute access, so the one `getattr` is inconsistent with its own line. **Unreachable today, so this is hardening and not a bug fix**: the sole caller is `::_edge_plan`, whose only input is `model._meta.get_fields()`, every member of which defines `is_relation` as a class attribute. Two paths, and the choice is the whole item - **(a)** read `field.is_relation` directly so an unanswerable shape raises rather than being silently classified a non-relation, or **(b)** keep it and record the closed-population argument in the docstring so a later reader does not "fix" it into a real fallback. Recorded 2026-08-28 by the spec-034 residual cycle (R1a finding M1).
- Delete the dead cascade edge helpers rather than extracting them: `django_strawberry_framework/permissions.py::_cascadable_edges` has exactly one reader (`::_cascadable_edge_names`) and `::_cascadable_edge_names` has **zero production readers** - one import and three call sites, all in `tests/test_permissions.py`. Every production path (`_validate_fields`, the preflight, `_walk`) calls `_edge_plan(model)` directly; `c68aecab` moved them there and left the pair vestigial. Paths: **(a)** delete `_cascadable_edges` and inline `_edge_plan(model).cascadable`, **(b)** delete both and let the three test sites read the plan directly as `tests/test_permissions.py` already does elsewhere, or **(c)** keep both as documented test seams. **Low value; should gate nothing** - it is listed here only because a DRY pass that finds the duplication without the reader counts would extract it instead of deleting it. Reader counts re-derived twice, 2026-08-28, by the spec-034 residual cycle (R1a DRY D1).
- One stale `TODO(spec-035)` build-phase anchor survives in a live fakeshop test, in a file this card's `workstream A/B/C/D` vocabulary item already opens (that item measures 6 of its 35 sites in the same file). `examples/fakeshop/test_query/test_library_api.py:3680` reads `# TODO(spec-035): extend this live connection-fragment block with the matching-type relation-planning acceptance test required by the test_query README.` It is the **P3a live matching-type test**, which spec-035's deferred G3 test plan carries forward to the abstract-return optimizer entry card, and it is the **only** `TODO(spec-035` occurrence left in the tree - the spec-035 residual cycle retargeted the other four to `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)` and this one takes the same head. **Why it was left:** the file was baseline-dirty with a concurrent session's work through that whole cycle (+91 lines at 2026-09-01), so no worker could edit or revert it under `AGENTS.md` 34. Nothing is owed beyond the head swap; the design it points at lives in `BACKLOG.md` `polymorphic_interface_connections` under **Carries forward (spec-035 G3 deferral)**. **Do not delete the anchor** - it is the live-coverage half of that card's R1 test plan, not dead scaffolding. Recorded 2026-09-01; full derivation at `git show 8c05f7fc:docs/builder/bld-035-final.md` item D1.

#### Definition of done

- [ ] `lint-imports` green in CI and pre-commit with the four boundary contracts; no `optimizer._*` import outside `optimizer/`; the optimizer's package-internal contract is declared in `optimizer/__init__.py`.
- [ ] The four extras install and resolve in isolated venvs; runtime guards unchanged.
- [ ] Every WP-B/C/D candidate landed or recorded rejected-with-reason in the spec; the deliberate-duplication ledger preserved.
- [ ] Plain-form mutations run inside `pipeline_alias_guard` + `authorization_phase` with live coverage (approved behavior change); `editable_input_fields` strictness tightening covered (approved behavior change).
- [ ] Full suite green under `fail_under = 100`; zero error-string assertion edits outside the two approved behavior changes; optimizer bench deltas at noise level.
- [ ] Version quintet at `0.0.15`, GLOSSARY flips for every card on the line, CHANGELOG entry, card flipped Done, KANBAN regenerated, `import_spec_terms` green.

#### Files likely touched

- `pyproject.toml` (import-linter config + extras), CI workflow, `.pre-commit-config.yaml`
- `django_strawberry_framework/optimizer/__init__.py` + its three cross-boundary consumers (`types/resolvers.py`, `mutations/resolvers.py`, `connection.py`)
- The four DRY axes: `filters/sets.py`, `orders/sets.py`, `sets_mixins.py`, `mutations/{sets,inputs,resolvers,permissions}.py`, `forms/{sets,inputs,resolvers}.py`, `rest_framework/{sets,inputs,resolvers,serializer_converter}.py`, `utils/*`, `connection.py`, `keyset.py`, `optimizer/*`, `types/{base,finalizer,resolvers,relay}.py`

#### Architectural posture

- No package split - the boundary becomes formal, not physical: `import-linter` contracts give ~90% of a split's discipline at ~2% of its cost, and are the prep work a real split would need anyway.
- Error-string byte-preservation policy: every consolidation renders existing messages byte-identically; family differences become parameters (noun, citation tail, accessor), never averaged prose. The pinned tests are the enforcement mechanism.
- Phase sequencing: mechanical -> structural -> contract-level. The per-family traversal descriptor (WP-B) is the substrate for WP-C's mixin work; the skeleton folds land before anyone touches the delete path again.
- Hot-path exclusions: nothing touches `_IndexedList.append_unique`, `included_field_selections`, `_merge_aliased_selections`, or resolver bodies. Expected measured perf cost ~zero despite the maintainer accepting a small cost.

#### Why it matters

- The maintainer's pain point: the package (~47.3k lines, ~19.7k code) has grown to the point of alignment fatigue. A pip-package split was investigated and rejected on evidence (the optimizer is bidirectionally fused to the type system; ecosystem precedent is uniformly against standalone framework-coupled optimizers).
- The split instinct pointed at real work: the optimizer/core boundary exists only by convention (private `optimizer._context` is imported from two subsystems; nothing enforces any seam), and four subsystem axes carry verified duplication.
- Four parallel audits (sets family, inputs/converters, resolvers, root+optimizer+utils) produced 32 verified consolidation candidates totaling ~1,100-1,300 lines, plus a do-not-touch ledger of deliberate duplication so future passes don't re-litigate.

#### Dependencies

- Sequenced behind DONE-044-0.0.14: card 044 owns the `0.0.14` joint cut and its TODO anchors sit on the version-quintet sites; this card's Slice 5 (and its quintet anchors) wait until that cut lands.
- Also sequenced behind TODO-ALPHA-052-0.0.15: the debug extraction lands first on this card's own `0.0.15` line and removes `extensions/debug.py`, so this card's import-linter leaf wording (contract 3) and its extras additions (Decision 5) build on the post-extraction tree - hold all slices until that card wraps.

#### Open question

- Two safe-direction costs in the middleware-ordering audit, deliberately left unpinned by any test so a contract sentence is not frozen before it is written. First, a chain spelled `[boundary, csrf, boundary]` is refused at startup, because the audit keeps the *last* boundary index and the *first* CSRF index. Second, two adjacent boundary entries measure the body twice, because `process_view` calls `view._enforce_request_boundary`, not `::_enforce_request_boundary_once`. Decide which is contract; only then does a row pin it.
- Whether the package owes a controlled response to a callback that forges the private boundary marker over a `view_class` carrying a *callable* of the probed name whose boundary then raises. Measured identically on Python 3.14/Django 6.0 and at the 3.10/5.2 floor: it passes the probe, is constructed, and a non-`HTTPException` leaves `process_view` uncaught. If taken, the change is `except Exception` around `view._enforce_request_boundary(request)` in `process_view`, and its cost is that the guard sits across the body cap's own errors and across a package mount's genuinely broken boundary - which is deliberately as loud with the middleware installed as without it. Three independent passes recommended against the code path. Until it is decided, no permanent test row may assert today's uncontrolled outcome as contract.

#### Note

- Do not consolidate the `SERVER_NAME` / `SERVER_PORT` repetition in `consumers.py::_host_validation_request`. It mirrors `django/core/handlers/asgi.py::ASGIRequest.__init__`'s own if/else item for item, and that mirror is what the projection's oracle row asserts against. Examined and rejected, twice.
- Do not give the cross-tree test helpers (`_capped_view`, `_strawberry_patch_opted_out`, `_multipart_body` / `_multipart_bytes`) a shared home. No shared home exists between the package tier and the fakeshop live tier, creating one means adding an `__init__.py` to a test tree that deliberately has none, and the duplication is the cheaper trade. Ruled and re-ruled; do not re-raise per helper.
- Examined and explicitly not a defect: `filters/sets.py`'s `models.DurationField -> DurationFilter` row. It reads as contradicting the consumer docs, which say `DurationField` is absent from `types/converters.py::SCALAR_MAP` and raises `ConfigurationError` at type creation. The row is a deliberate mirror of django-filter's own table and becomes reachable exactly when a consumer registers the `SCALAR_MAP` entry the corrected docs tell them to register. Do not re-flag it on a DRY sweep.

#### Card references

- Dependency: `DONE-044-0.0.14` - Response-extensions debug middleware
- Dependency: `TODO-ALPHA-052-0.0.15` - Extract DjangoDebugExtension into the standalone django-strawberry-debug package
- Dependency: The list-field card lands first on the shared `0.0.15` line; this card lands last and its Slice-5 quintet waits for every `0.0.15` card. -> `WIP-ALPHA-050-0.0.15` - `DjangoListField` argument surface: `offset` / `limit` and `orderBy`
- Dependency: Shares every file in the parity-gap card's Files-likely-touched list except `types/converters.py`, so this card is sequenced behind it (the edge that card's DoD owed, landed at the 2026-08-29 board review). -> `TODO-ALPHA-051-0.0.15` - Upstream parity-gap closure

## To Do - Alpha (0.1.0)

Cards required to reach feature parity with both upstreams (`⚛️ graphene-django` and `🍓 strawberry-graphql-django`). Cards target `0.0.x` patches on the road to **0.1.0**; the remaining alpha work spans three joint-cut lines - `0.0.15` (050-053, DRY squeeze owns the cut), `0.0.16` (054-055, federation owns the cut), and `0.0.17` (056 solo). The final card in this column is the `0.1.0` release itself (cleanup, verification, alpha → beta cut-over). Cards in NNN order = planned ship order; dependency and parallelism notes live on each card.

<a id="pluggable_field_conversion_registry"></a>
### [TODO-ALPHA-054-0.0.16 - Pluggable field-conversion registry](KANBAN.html#pluggable_field_conversion_registry)

- Priority: Medium-high
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: To Do
- Relative size: M
- Labels: `converters`, `public-api`, `registry`, `scalar-map`, `scalars`, `types`

#### Planning note

Created 2026-08-29 from the DIV-033 discussion: turn the field-conversion escape hatch from process-global dict mutation into a scoped, bundle-shaped, callable-capable registry. Extensibility parity with graphene-django's public converter hook, and the prerequisite for the GIS backlog card and the dynamic-schemas card. No schema-visible change for existing consumers.

#### Dependencies

- `TODO-ALPHA-051-0.0.15` - Upstream parity-gap closure

#### Scope

- Class-attribute scoping: SCALAR_MAP / FIELD_OUTPUT_TYPE_MAP resolution moves from module-global-only to a layered lookup resolved at Meta-class creation time - per-type Meta override, then DjangoType base-class attribute (inherited via Python MRO, the DRF ModelSerializer.serializer_field_mapping shape), then the framework default maps. The module-level dicts remain the bottom layer so every existing registration keeps working; two apps in one process stop colliding because each app's base class carries its own map.
- Bundle-shaped entries: a registration value grows from a bare scalar to a bundle - scalar, optional read-output type, optional resolver-attach hook, optional filter-side scalar. The file family (FileField/ImageField -> DjangoFileType/DjangoImageType + resolvers._attach_file_resolvers) migrates onto it as the first in-tree registration, deleting its hard-coded special cases.
- Callable converters for structured/container fields: an entry value may be a callable converter(field, type_name, *, recurse) returning the annotation, with recurse a bound re-entry into convert_scalar. The hard-coded ArrayField/HStoreField branches in convert_scalar are deleted and re-registered as the first two callable entries; outer nullability widening stays framework-owned so converters cannot get it wrong; ConfigurationError rejection of invalid shapes stays converter-raised.
- One registry, both sides: the filter-input converter (filters/inputs.py via scalar_for_field) resolves through the same registry so a registered type appears consistently on read output and filter arguments.
- The fail-closed contract is unchanged: an unregistered field class still raises ConfigurationError naming the registration hook; nothing silently degrades to str.
- No schema-visible change for existing consumers: fakeshop SDL is byte-identical before and after the refactor, asserted by a test.

#### Definition of done

- [ ] Registry resolution order (Meta override -> base-class attribute -> framework default) specified in the spec and pinned by tests, including the two-apps-one-process collision case.
- [ ] File family and postgres container fields migrated onto bundle/callable entries with their hard-coded branches deleted from convert_scalar and resolvers.
- [ ] Filter-input side resolves through the same registry, with a test pinning read/filter consistency for a consumer-registered type.
- [ ] Fakeshop SDL byte-identity test proves no schema-visible change for existing consumers.
- [ ] Escape-hatch documentation (converters.py docstring and any doc pages naming SCALAR_MAP registration) updated to the registry surface, with the old form still working and documented as the bottom layer.

#### Files likely touched

- `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/filters/inputs.py`
- `tests/types/test_converters.py`, `tests/filters/`

#### Verified in upstream

- graphene-django's convert_django_field is a @singledispatch callable registry (converter.py) and is the public hook third-party packages extend (graphene-gis adds GeoDjango support through it) - extensibility is itself a parity surface.
- DRF ModelSerializer.serializer_field_mapping (rest_framework/serializers.py) is the class-attribute scoping precedent: subclass-and-override, MRO-inherited - the DRF-idiom shape this framework follows.
- strawberry-graphql-django 0.82.1 ships geo scalars in-tree instead of a hook; the registry is how this package answers that surface without acquiring GDAL/GEOS system dependencies.

#### Why it matters

- The documented escape hatch (SCALAR_MAP[FieldCls] = <scalar>) is today raw process-global dict mutation: no scoping, no validation, no resolver or container story. Changing extension architecture after 0.1.0 means migrating consumers, so the reshape must land in alpha.
- Prerequisite for the GIS / GeoDjango backlog card (its recipe-vs-satellite open question is decided by how much this registry can carry) and for the dynamic-schemas card (dataType spec entries resolve through registered converters).

#### Card references

- Related: This registry decides how much of the GIS card a consumer-side recipe can cover. -> `BACKLOG-STABLE-076-1.1.0` - GIS / GeoDjango field-type support (geo scalars)
- Related: The doc-debt card documents the new registry surface from its own solo `0.0.17` line; the `0.0.16` release state is owned by the federation card's cut. -> `TODO-ALPHA-056-0.0.17` - Alpha documentation-debt discharge
- Dependency: The parity-gap card's `GeneratedField` entry lands in the converter table this card migrates onto the registry; sequenced behind it. -> `TODO-ALPHA-051-0.0.15` - Upstream parity-gap closure

<a id="apollo_federation_as_the_standalone_django_strawberry_federation_package"></a>
### [TODO-ALPHA-055-0.0.16 - Apollo Federation as the standalone django-strawberry-federation package](KANBAN.html#apollo_federation_as_the_standalone_django_strawberry_federation_package)

- Priority: Medium-high
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: To Do
- Relative size: L
- Labels: `packaging`, `public-api`, `schema`

#### Planning note

Maintainer decision 2026-08-29 on the parity register's federation cut blocker: the Apollo Federation subgraph surface (🍓 ships it as the whole `strawberry_django/federation/` subpackage - `type.py`, `field.py`, `resolve.py`) lands as a standalone satellite package on the django-strawberry-debug pattern, never in core. Core-refused because federation couples the schema surface to a third-party protocol that evolves on Apollo's schedule and serves one deployment shape (a subgraph behind an Apollo gateway); the satellite gets its own release cadence for spec churn. Unlike the debug extraction this is greenfield-in-satellite, not a code move - and unlike django-strawberry-debug the satellite DOES depend on django-strawberry-framework, because entity resolution and the Meta surface build on core seams. Supersedes the retired BACKLOG `apollo_federation_meta_surface` row (its Meta sketch - `federation = {"keys": [...], "shareable": [...], "tag": ...}` - carries forward as the satellite's declaration shape).

#### Dependencies

- `TODO-ALPHA-053-0.0.15` - Boundary hardening and system-wide DRY squeeze

#### Scope

- Slice 1 - in-repo seams, the only slice that touches this repo's package source: pin `DjangoSchema` as deliberately subclass-friendly (a stated contract with a test, not an accident), because a federated consumer needs `strawberry.federation.Schema`'s directive/entity machinery AND `DjangoSchema`'s transaction-spanning mutation context in one class, so the satellite must be able to build a `DjangoFederationSchema` on both; audit that everything entity resolution needs - registry lookup, finalizer participation, GlobalID/node identity - is reachable through public API under the import-linter boundary contracts the DRY-squeeze card lands, and add any missing public seam here rather than letting the satellite import `_private` internals.
- Slice 2 - the satellite: new repo riodw/django-strawberry-federation depending on django-strawberry-framework and strawberry-graphql's federation support; `DjangoFederationSchema`; the DRF-idiom Meta surface (`Meta.federation = {"keys": [...], "shareable": [...], "tag": ...}`) emitting Federation 2 directives - Meta declarations, never decorators; `_entities` resolution routed through the target type's `get_queryset` so row visibility holds for gateway entity fetches exactly as it does for root fields; own suite, CI matrix, README; 0.1.0 published to PyPI.
- Slice 3 - framework docs fold-in: `[federation]` optional-dependencies extra pointing at the satellite; GLOSSARY entry via the DB; the migration-guides card's 🍓 guide maps `strawberry_django`'s federation subpackage to the satellite; the beta release card's parity carve-out cites the package; the BACKLOG `apollo_federation_meta_surface` row is retired (done at carding, recorded here).

#### Definition of done

- [ ] `DjangoSchema` subclass-friendliness is a pinned contract: a test constructs a subclass combining it with `strawberry.federation.Schema` machinery (or the seam equivalent) and the docstring states the contract.
- [ ] The satellite needs zero `_private` imports from django-strawberry-framework - verifiable under the import-linter contracts; any seam it needed was made public here first.
- [ ] django-strawberry-federation 0.1.0 on PyPI: `DjangoFederationSchema`, Meta-driven `@key` / `@shareable` / `@tag`, entity resolution through `get_queryset` (a hidden row is as unreachable via `_entities` as via a root field, proven by test), supergraph-composition + `_entities` round-trip integration coverage.
- [ ] `pip install django-strawberry-framework[federation]` resolves in an isolated venv; with the extra absent, nothing in core imports or references the satellite.
- [ ] Guides note and GLOSSARY entry land; the beta release card's parity claim cites the package for the federation carve-out.
- [ ] Full suite green under `fail_under = 100` for the in-repo slice. Version quintet at `0.0.16`, GLOSSARY status flips for the line, CHANGELOG entry - this card lands last on the `0.0.16` line (after the registry) and owns the joint cut.

#### Files likely touched

- `django_strawberry_framework/schema.py` (subclass-friendliness contract + docstring)
- Public seam additions only if the Slice 1 audit finds a gap (registry / finalizer / node identity access)
- `pyproject.toml` (`[federation]` extra), GLOSSARY via DB, guides fold-in
- Everything else lives in the new riodw/django-strawberry-federation repo

#### Verified in upstream

- 🍓 ships federation as `strawberry_django/federation/` (`type.py`, `field.py`, `resolve.py`): Federation 2 directives and entity resolution. ⚛ ships none, so this is single-upstream parity.
- strawberry-graphql core ships `strawberry.federation` (federation-aware Schema, directive types), which is what the satellite composes rather than reimplements.

#### Dependencies

- Slice 1's public-seam audit runs against the import-linter boundary contracts this card lands.

#### Note

- Renumber consequence: inserted at 054 (after the DRY-squeeze card whose boundary contracts Slice 1 depends on), shifting the 19 cards then numbered 054-072 up by one to 055-073; the board DB's text columns were re-swept for full card ids in the same pass.

#### Card references

- Dependency: Slice 1's public-seam audit runs against the import-linter boundary contracts this card lands. -> `TODO-ALPHA-053-0.0.15` - Boundary hardening and system-wide DRY squeeze
- Related: The satellite pattern this card follows - with the inverse dependency posture: debug has no core dependency, federation requires one. -> `TODO-ALPHA-052-0.0.15` - Extract DjangoDebugExtension into the standalone django-strawberry-debug package
- Related: Owes the federation note in the strawberry-graphql-django guide: upstream's federation subpackage maps to django-strawberry-federation. -> `TODO-BETA-071-0.1.8` - Migration and adoption guides
- Related: The parity claim's federation carve-out cites this card's satellite package. -> `TODO-ALPHA-057-0.1.0` - Beta release (cleanup, verification, alpha → beta)

<a id="alpha_documentation_debt_discharge"></a>
### [TODO-ALPHA-056-0.0.17 - Alpha documentation-debt discharge](KANBAN.html#alpha_documentation_debt_discharge)

- Priority: Medium
- Status: To Do
- Relative size: XL
- Labels: `internal`

#### Planning note

Documentation-consistency debt accumulated across the alpha line, split off the beta release card so it has a definition of done that can fail.

#### Dependencies

- `TODO-ALPHA-054-0.0.16` - Pluggable field-conversion registry
- `TODO-ALPHA-055-0.0.16` - Apollo Federation as the standalone django-strawberry-federation package

#### Scope

- `docs/GLOSSARY.md` has no `DjangoSchema` entry, so the schema constructor's two policy arguments are described only from the `ErrorPolicy` / `ResourcePolicy` side. The spec-006 residual cycle closed the roster half: `DjangoSchema` and `DjangoMutationExecutionContext` now carry Public-exports bullets whose glosses link the entries that describe them, so what remains open is only whether either name earns an entry and anchor of its own. Card 047's closeout removed the dangling `#djangoschema` links rather than authoring the entry, matching how the `ErrorPolicy` entries already name the class without linking it; deciding whether the entry should exist is still open. Two adjacent completeness gaps in the same section, both measured by that cycle and both editorial calls rather than contract violations. First, `## Public exports` carries group bullets for `extensions`, `testing` and `auth` but none for `views`, `routers` or `middleware.debug_toolbar` - each of which already has its own glossary entry and is deliberately NOT root-exported, because for those families the dotted import path is the opt-in boundary rather than a consolation for failing the re-export gate. Second, the `DjangoSchema` bullet is a fourth site for the construction-time fact its two linked entries and the class docstring already state; it collapses to one line if and only if the entry above is authored, so trimming it first would leave the name a gloss documenting nothing and two foreign anchors with no stated relevance - strictly worse than the duplication.
- Decide whether a `-rationale.md` companion in `docs/SPECS/appx/` is owed by every shipped spec or only by one whose cycle produced it, and make the directory consistent either way. Re-measured 2026-08-26 after the spec-031 residual cycle authored `031`'s companion: `docs/SPECS/` holds 56 spec files, 20 carry no `-rationale.md`, and 2 carry no `-terms.csv` either (`spec-054-graph_substrate-0_1_1` and `spec-064-structural_templates-0_1_6`, both unshipped). Restricted to the population this decision actually governs - the 49 shipped specs - 36 have a companion and 13 do not (`spec-032` through `spec-043`, plus `spec-049`); the remaining 7 gaps are unshipped specs that have had no cycle, so they are not in the population. This supersedes the 2026-08-25 reading of 21-carry-none / 35-have / 14-do-not, which itself superseded the 2026-08-15 reading of 13-have / 36-do-not, and the two supersessions differ in kind. The 08-15 to 08-25 one changed the SHAPE and not only the numbers: the have-side stopped being two small cohorts and became one long run plus one, contiguous from `spec-001` to `spec-030` alongside `spec-044` through `spec-048`, because that first cohort has been extended card by card since. The 08-25 to 08-26 one changed only the BOUNDARY, and by exactly one - the run now reads `spec-001` to `spec-031` alongside `spec-044` through `spec-048` - and it moved for precisely the reason the prior reading had already named: the run is extended card by card, and `031` was the next card. So the gap is no longer 'everything predating the practice' but a bounded 13-spec island between two runs, whose leading edge each residual cycle pushes forward by one: closing `030` made `spec-031` the edge and made the island visible at all, and closing `031` has now made `spec-032` the edge. This bullet previously read that `spec-048-secure_output_defaults-0_0_14.md` was the one file missing a companion where 044 through 047 all had one; that framing was wrong twice over, and both errors are worth keeping visible so the rewrite is not re-reverted. The named file acquired its companion (29,962 bytes), and the four-of-five reading mistook a cohort boundary for a defect - it pointed at the single spec sitting on the edge of the new-practice block and made what is now a 13-file policy question look like a one-file tidy-up. What actually turns on the decision is scheduling, not consistency: answering "every shipped spec" commits the board to 13 residual cycles of the kind spec-001 through spec-008 have been receiving, so the answer belongs beside this card's rationale-template and spec/rationale-checker items rather than in a documentation sweep.
- `README.md:62`'s `0.0.14` paragraph describes `main`'s router shape inside the released version's sentence. Chosen framing on record: lead with the marker, the shape `docs/README.md:128` and `TODAY.md:384` already use.
- `BACKLOG.md:1616` and `:1661` describe the protocol router as serving HTTP + WebSocket in the present tense.
- Promote a spec/rationale consistency checker into `scripts/`. Nothing there matches `link|anchor|overlap` today, so every documentation pass hand-writes its own. The checks each spec-plus-rationale pair owes: link scaffold (defs / uses / undefined / orphan), the 10 canonical group headers in positional order, alphabetical order within group, on-disk resolution of every def target with the fragment stripped and URLs excluded, in-page anchors slugged by a markup-rendering slugger, an inline cross-file-link sweep, a rule-27 raw `path:NN` sweep, and a maximal-shared-shingle scan - the only thing that turns "it was a move, not a copy" into a measurement. Four slugger defects, each measured on an independent hand-roll of this checker, to encode as its regression tests. (a) A heading that is itself a reference link, slugged without rendering the markup out first: the link-definition key survives into the slug, so a correct in-page anchor reports as dangling. (b) Whitespace runs collapsed. GitHub replaces spaces one at a time, so a heading with a double space slugs to a double hyphen; a checker that collapses runs reports a false PASS - the only silent defect of the four, and so the most dangerous to leave unencoded. (c) Code spans deleted rather than masked before reference links are matched. A label spelled as a code span collapses to an empty label, which the usual bracket-capture pattern cannot match; one run reported 3 spec and 12 rationale false orphans from this alone. Mask span content to same-length filler instead, preserving the brackets. (d) `_` stripped as an emphasis marker before slugging. It destroys `django_types`, so the anchor for a heading naming `spec-001-django_types-0_0_1.md` reports unresolved against a correct link definition - a false positive whose natural fix is to corrupt a good link. Defect (d) is the argument for a tool rather than more prose: it was measured, written into a hand-off, and re-introduced from scratch two rounds later by a reader who had that hand-off. (e) Shingle tokenization, and it fails OPEN like defect (b) rather than loudly. A phrase-shaped duplicate check must tokenize on word characters (`[A-Za-z0-9_]+`) and case-fold, because Markdown emphasis and punctuation sit INSIDE the window and shift token positions without changing the words: the spec-006 residual cycle's first move-verification reported 0 non-scaffold overlaps where a word-character tokenizer finds 3, because `**all four**` and `**iff**` produce disjoint shingles from an identical word sequence. That is the second independent measurement of the rule this card's methodology note already carries out of the spec-005 cycle, arrived at without reference to it - which is the same argument defect (d) makes, and the argument for encoding the rule as a test rather than restating it in prose a third time. The scan also owes a control pair before any number it reports means anything: spec-006's companion measured 180 non-scaffold 8-word shingles against its sibling companions where the 006/005 control measured 247, so the higher-looking figure was the LESS coupled one and an unquoted overlap count is not a finding.
- `docs/SPECS/spec-002-optimizer-0_0_2.md` carries no status-shaped section any more. The spec-002 residual cycle discharged most of them - `## Open questions` and `## Current state` are gone, and `## Shipped slices` and `## Implementation checklist` survive the argument on their merits, since a past-tense fact about what shipped is not a promise about the present. The last one, `## Visibility status`, was retired by the spec-006 residual cycle as a cross-spec duplicate under the single-ownership law: the section existed because `spec-006-public_surface-0_0_3.md` asked for a copy, and both of spec-006's citing bullets were retired with it, so nothing in spec-006 names the section. The companion `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` no longer defines a `#visibility-status` link target either, and the sentence that used it now names `## Shipped slices` as what absorbed the removed content; the discharge and its reasoning are recorded in that companion's `## The discharged deferral`. `spec-003-optimizer_nested_prefetch_chains-0_0_2.md` no longer carries its when-O4-ships instruction at all - the 2026-08-07 reconciliation deleted the section - so nothing in spec-003 names these headings any more.
- Swept 2026-08-07: all 32 occurrences of the dead card id `TODO-BETA-053-0.1.5` across 10 files (TODAY.md, seven archived specs, `apps/products/schema.py`, `test_query/test_products_api.py`) now read `TODO-BETA-062-0.1.5`, after confirming 062 is the natural host - its scope (node / nodes, `totalCount`, the subscription surface) covers every referencing subject.
- `import_spec_terms::_sync_spec_mentions` orphans GlossarySpecMention rows instead of repointing them: it deletes only rows at the NEW spec_path, never the old one, so every spec archive leaves the pre-archive path rows behind forever. The accumulated orphans have been reaped (0 remain), but the cause is unfixed and the next archive recreates them.
- `spec-003-optimizer_nested_prefetch_chains-0_0_2.md` was reconciled on 2026-08-07 and three of the four stale sites this card carried are closed: the pre-reconciliation `plan_optimizations` arity and the present-tense `_collect_scalar_only_fields` are rewritten, and the discharged when-O4-ships instruction is deleted along with the parent-spec sweep item it carried. The fourth is a live DIVERGENCE this card must settle rather than sweep: this card's prescription was to replace the spec's opening claim so it states that O4 is shipped and that its record is this spec's, and the reconciliation deliberately rejected that disposition - a spec states its contract and never narrates its own shipping status - with the reasoning and the rejected alternative recorded in `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` under its `## Problem statement` entry. Neither surface has been partial-fixed toward the other; settling which one moves is this card's closeout call. The prior instruction not to sweep up spec-006's two citations of `## Visibility status` is spent: the spec-006 residual cycle retired both bullets with the heading they named, so nothing in spec-006 references the section.
- `docs/GLOSSARY.md` dates `DjangoOptimizerExtension` and `only()` projection to `0.0.2`, matching card `DONE-002-0.0.2`'s target version, while `CHANGELOG.md`'s `[0.0.2]` entry calls the extension early and depth-1 and its `[0.0.3]` entry dates the end-to-end optimizer surface - selection-tree planning, `select_related`, nested `Prefetch` chains, same-query recursion, `only()` projection, and `get_queryset`-aware `Prefetch` downgrade - to `0.0.3`. Whether a shipped-version stamp names first-shipped or complete is an editorial call about the glossary's dating convention for a subsystem that shipped across two releases, and it is not unilaterally correctable: `GlossaryTerm.body`, the card's target version, the card id, and the spec filename ending `-0_0_2.md` must move together. This card owns the CHANGELOG promotion, so the decision belongs on it.
- `DONE-003-0.0.2`'s `Verified in upstream` note is imprecise about which upstream function rebases: `strawberry_django/optimizer.py::_get_hints_from_django_relation`'s rebasing block moves entries out of its local store with the `path__` prefix STRIPPED (and is inert - that store is constructed empty), while the prefix-adding rebase lives in the sibling `::_get_hints_from_django_field`. The two sub-claims the parity argument rests on (`level=level + 1` recursion and `Prefetch(path, queryset=field_qs)` emission) are exact. Fold a one-clause correction into this card's closeout alongside its other spec-003 record work; a standalone edit of a shipped Done card's historical note buys no reader anything on its own.
- The spec rationale companion file is on its sixteenth hand-reproduced instance. Re-measured 2026-08-26 by re-running the three-section shape check over every companion rather than re-counting files: `docs/SPECS/appx/` holds 36 `-rationale.md` companions, and 16 of them carry all three of `## How to read this file`, `## Provenance of this record` and `## Entries keyed to the spec` - the companions to `spec-001-django_types-0_0_1` through `spec-016-fieldmeta_consolidation-0_0_6`, still one contiguous run - each rebuilding that shape by hand along with the deliberative-companion opener, `## Standing notes`, and the link-definition scaffold at `docs/SPECS/appx/` depth. Eight carry two of the three, twelve carry one, and none carries zero. This supersedes the 2026-08-14 reading of 8 of 13, whose all-three cohort ended at `spec-008-definition_order_independence-0_0_4`: that 13 was the rationale-companion population of the day (those eight plus the five `0.0.14` companions, not 13 files in the directory - `docs/SPECS/appx/` also holds a `-terms.csv` per spec), and it is 36 now because each residual cycle since has authored one. The wider population is not decay to nothing but decay in two steps, in spec order: `spec-001` through `spec-016` carry three; `spec-017-deferred_scalars-0_0_6` through `spec-022-export_schema-0_0_7` carry `## Provenance of this record` plus `## Entries keyed to the spec`; `spec-023-multi_db-0_0_7` through `spec-031-globalid_encoding-0_0_9` carry `## Provenance of this record` alone. A same-day reading of this measurement put `spec-016-fieldmeta_consolidation-0_0_6` outside the cohort as a lone break carrying no provenance; that was an instrument artifact and is recorded so it is not re-derived. Its heading reads `## Provenance of this record - a reconstruction, not a move`, and an exact heading match misses a heading carrying a suffix where a substring match finds it. Grade these three headings by prefix, never by equality: `spec-016` is the only companion of the 36 where the two instruments disagree, so a spot-check of any other file would have confirmed the wrong reading. `## Provenance of this record` now stands at 34 of 36 and is a convention in fact; the other two headings, at 20 and 22, are not. The five `0.0.14` companions still carry one or two of the three (`044` and `046` how-to-read only, `045` provenance only, `047` and `048` both of those), which is itself part of the decision: the shape is either a template or a convention only the early cycles followed. Decide whether it becomes a documented template; the natural home is beside the spec/rationale consistency checker this card already scopes. Fold in one sizing question the spec-007 residual cycle raised: that pair still measures 46,045 bytes of rationale against a 2,983-byte spec, a 15.4x ratio, but the comparison it was set against has moved. The next-highest of the thirteen pairs then was 4.3x (`spec-002-optimizer-0_0_2`); over the 36 pairs now it is 10.3x (`spec-012-version_release_alignment-0_0_4`, 28,943 bytes of rationale against a 2,814-byte spec), with `spec-014-testing_shift-0_0_4` at 8.8x and `spec-013-real_m2m_coverage-0_0_4` at 7.3x behind it. So spec-007 is no longer a lone outlier but the head of a small tiny-spec/large-rationale tail, every member of it `0_0_4`-era. Not a defect and not that cycle's to fix, but if the template lands it should say whether a companion that large owes an index or a split.
- Decide whether `scripts/check_spec_glossary.py` should strip code spans in `REF_USE_PATTERN`. Today a glossary link whose only body carrier sits inside a code span still counts as a link; a checker that started stripping code spans would drop every such anchor and break the affected done cards' `import_spec_terms` chains. Run a repo-wide count of code-span-only carriers before changing anything - this is the same span-masking question as slugger defect (c) in this card's checker item, landing on the opposite answer (count them rather than drop them).
- Worker memory does not survive a concurrent build, and the loss is silent. `docs/builder/worker-memory/` is shared, gitignored, and reseeded empty by every build's pre-flight (`worker-0.md` step 5; `BUILD.md` `### Worker memory`), while `START.md` documents several sessions running builds on one checkout. So the second session to start a build destroys the first's memory before that build's closeout reads it - and `worker-0.md` `## Closeout job` step 2 is the only pass that ever reads all four. Measured on the spec-003 cycle: at closeout all four files read `# Worker N memory - build 004`, and the spec-003 entries were unrecoverable. Fix by namespacing the files per build, or by making pre-flight archive rather than delete, or by moving the closeout read earlier; whichever, pre-flight must stop being able to delete a build's memory that its own closeout has not harvested.
- `scripts/clean_up.py` has no concurrency guard and can destroy another session's live work. Its `('docs/builder', 'bld-*.md')` glob deletes every cycle's artifacts, not the caller's, and it also clears the shared `docs/builder/worker-memory/` and `docs/shadow/`. Running it at the close of the spec-003 cycle would have deleted two untracked spec-004 artifacts, one of them at `Status: planned` and written six minutes earlier - unrecoverable, since untracked files are not in git. It is the sanctioned way to end a cycle and the repo is documented as concurrently worked, so this will recur. Scope deletion to a caller-supplied cycle (`--card NNN`), or refuse when a targeted artifact is untracked or not `final-accepted`.
- The builder corpus states rules correctly and they still get missed, because they sit far from the point of use. Two measurements from the spec-003 cycle, one gap and one placement problem. (a) GAP: `worker-1.md` `### Performing the rationale move` decides what stays in a spec by asking whether a SENTENCE is deliberation or instruction - but a load-bearing rule can be an ordering constraint with no sentence form. Three of the six rules rescued out of spec-003's deleted pseudo-code fences existed only as the sequence of two lines (`_record_relation_access` before the elision short-circuit; the `only_fields` guard before connector injection; `cacheable = False` before the child build), and a seventh was missed on the first pass and caught only by review. Every rationale extraction that cuts pseudo-code hits this; five cycles have. (b) PLACEMENT: `BUILD.md` `## Claims are proven mechanically` already says to count occurrences rather than matching lines, and six of the cycle's thirteen findings were still miscounts, twice by exactly that `grep -c` mechanism. More prose is not the fix - the rule is right and unread. Both are corpus edits bound by `BUILD.md` `## The corpus ratchet`, so each needs the bytes it retires named before it lands. (c) A third measurement, from the spec-006 residual cycle, of (b)'s shape and pointing at (b)'s fix. Six instances in one cycle of RIGHT SUBSTANCE, LOOSE CITATION - a checklist box whose claim holds while the evidence it cites does not re-derive: an evidence formula requiring `git diff <spec>` to be empty, which was unsatisfiable from the moment that cycle's own reconciliation pass rewrote the spec uncommitted; a quoted heading carrying an ASCII hyphen where the heading on disk carries an em dash, so the quoted string greps to 0; marker occurrence counts measured over four docs and dispatched over five; and `CardItem.order` values checked as though they were rendered ordinals, which fails against a correct render because the order sequence is sparse. Four more were confined to a scratchpad, including a model cited as `GlossaryDocument` where the row is `apps.kanban.models.BoardDoc` with `namespace='glossary'`. The sharpest instance sat inside a sentence claiming re-derivation - the measurement had been re-derived and the attribution clause riding on it had not - so the countermeasure is that a re-derivation claim must scope to every clause it stands over, and an auditor re-derives the citation rather than only the substance. Converges from the other direction with this card's note-section quantifier rule; two cycles reaching one rule independently is the argument for stating it once in `BUILD.md` rather than a third time on a card. (d) Two rules measured by the spec-008 residual cycle, same ratchet bucket. First, the recurring pointer defect: a reference resolves and its destination does not carry the claim it was cited for. The two separating tests are subject match and explicit forwarding by name - a pointer landing on a section about the right subject is not thereby a pointer to the claim, and the only pointer that survives a later edit of its destination is one the destination names. This card's spec-010 rule-27 item is a population of exactly that defect, which is the argument for stating it in `BUILD.md` rather than once per spec. Second, its mechanical cousin, and the sharper of the two because it explains why gates miss it: before trusting a mechanical check, state what the tool actually reads. A line-oriented tool applied to a quantity that is not a line was that cycle's most repeated error, and the general form is that the tool's input is not the thing under test - `grep` sees source literals while the runtime sees their concatenation, so `testing/relay.py::global_id_for`'s message is split across adjacent string literals and a source grep returns 0 for text that is present in the raised string; a link audit reads a heading list while the claim lives in the body; and `cardinalit` appears only in prose while the code spells it `FieldMeta.is_many_side`, which is how a reported "9 occurrences, 0 validators" travelled three un-re-derived hops against a real 42 lines in 12 files. Converges with (b) from the opposite direction: (b) says count occurrences rather than matching lines, and this says a count means nothing until the population counted is the one the claim is about. (e) A placement defect in `ARTIFACT.md`, same bucket. `ARTIFACT.md:3` and `:181` make the top-level header `Status:` line canonical and `:187` makes the body append-only, and the spec-008 cycle still ran five state transitions with that header reading `planned`, because each pass appended a `## Status` section and none rewrote the header. Both rules are stated and both are correct; nothing sits at the point of use telling a pass writing its block that the header is what dispatch reads. The dispatcher's half of the same defect is that Worker 0 ticked two checklist boxes off a subagent's return message rather than the artifact, which `worker-0.md` already forbids - so the countermeasure is a placement edit at the write site, not a third statement of the rule.
- The spec-005 residual cycle closed early with its documentation-and-archive round never dispatched; that round's verification chain lands here, beside the definition-of-done box that already owns the doc cross-check. (a) Durable-doc audit, with three inputs already established and re-usable: `docs/README.md` has no `## Current surface` section and no reference to spec-005 anywhere, which is what makes the spec's two retired README obligations undischargeable rather than corrections owed; `docs/GLOSSARY.md`'s `Meta.interfaces` and `Meta.primary` entries are already correct, and the `Meta.primary` entry already carries the full four-case ambiguity table with both error strings, which is why the reconciled spec points there instead of restating it; and the three still-deferred keys are labeled by release (`0.1.1` / `0.1.2` / `0.1.3`), never by spec. Compare `iterdump()` semantics rather than file bytes and verify by two-consecutive-regenerate byte-stability - `docs/GLOSSARY.md` is routinely dirty from a concurrent cycle's regenerate. (b) Re-run the three-direction cross-reference sweep - references to spec-005, its own 8 link definitions, and the rationale companion's outbound links at `docs/SPECS/appx/` depth (`../../GLOSSARY.md` for a `docs/` target, `../spec-NNN-*.md` for a `docs/SPECS/` sibling). All 27 definitions resolved when last measured; nobody has re-measured since commit `bca1ccf1`. (c) Re-verify `SpecDoc.path` for card 5 and that `card.glossary_links.count()` equals the 7 rows of `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-terms.csv` - a green `check_spec_glossary` does not prove the DB-side count, which is why it is a separate obligation, and the DB has been written by concurrent sessions since the last reading. (d) Run the writing form of `import_spec_terms`; only the read-only `--check` form was ever invoked.
- Add a source-symbol-citation check to the spec/rationale consistency checker this card already scopes: nothing in the repository verifies that a `path::Symbol` citation in a spec names a symbol that still exists. Measured instance: spec-005 cited `convert_relation` as the symbol a relation resolves through, and it is gone from the package entirely. It was found by a human-driven sweep and would have survived every automated gate that cycle ran - `check_spec_glossary` validates glossary anchors, not source symbols. The checker must distinguish a live spec's claim from a shipped spec's history: `spec-008`, `spec-009`, `spec-010` and `spec-019` all name `convert_relation` in the present tense and are correct as history, so a checker that flags them reproduces the documentation-sweep error this board has already ruled against twice.
- `CHANGELOG.md`'s `0.0.8` entry states the release's documentation context only as design-doc pointers: `CHANGELOG.md #"The documentation surface was synchronized for the 0.0.8 cycle"` cites `spec-027-filters-0_0_8.md` and `spec-028-orders-0_0_8.md` through reference links, so a reader of the release record has to leave it to learn what shipped. Decide whether that entry states the shipped surface itself or stays a pointer. Two measurements taken 2026-08-14 frame the decision: the file is 437 lines / 100,289 bytes, and the `0.0.4` onboarding-docs card's board claim that "`CHANGELOG.md` is condensed and no longer relies on design-doc pointers for release context" was true when it was written and describes neither property now. That row is correct history on a Done card and is NOT to be edited, which is precisely why the live decision needs a home here. Raised and deferred by the spec-007 residual cycle: `AGENTS.md` rule 21 closes `CHANGELOG.md` to a build cycle, and this card owns the CHANGELOG promotion.
- `CONTRIBUTING.md #"Spec filename pattern"` cites a `docs/builder/BUILD.md` heading that does not exist: `grep -c 'Spec filename pattern' docs/builder/BUILD.md` returns 0, and the real heading is `## Spec and build-plan filename pattern`. Correct the citation, and cross-check the rest of that paragraph's workflow claims against `BUILD.md` in the same pass rather than fixing four words alone - the paragraph also describes the spec working location and the archival opt-in, both of which `BUILD.md` now states itself. Found by the spec-007 residual cycle, which had no license to touch `CONTRIBUTING.md`; this card's documentation cross-check is the natural owner, and its definition-of-done box now names the file.
- `scripts/check_trailing_commas.py` walks git-ignored paths, so an unscoped `--check` exits 1 on a file no commit can contain. Measured 2026-08-14: a tree-wide run reports `1 layout violation` against an agent-memory file under `.claude/`, which `.gitignore:170` ignores wholesale, while the `source-layout` pre-commit hook is unaffected by construction because pre-commit passes it staged paths and an ignored path is never staged. No repository file is implicated, so this is a false red that costs a reader a re-derivation rather than a defect - and it cost one: a build cycle reported it as another session's file on the strength of the directory alone. Either teach the walker to skip ignored paths via `git check-ignore`, or state in the script's docstring that it is scoped-run-only and the hook is the gate. Same doc-tooling family as this card's `import_spec_terms` orphan and `clean_up.py` concurrency items.
- `spec-009-rich_schema_architecture-0_0_4.md #"### Layer 3: Finalization trigger"` presented hybrid auto-finalization as the preferred direction after the spec-008 reconciliation established the direction was REJECTED; the Layer-3 text was corrected at `f3c94642` and the full spec-009 residual reconciliation cycle completed 2026-08-16 (`docs/builder/bld-009-final.md`) - Layer 3 now states the explicit `finalize_django_types()` call is the sole trigger and nothing auto-finalizes, and the whole spec was reconciled clause-by-clause against shipped code (no correctness defect, no silent omission; six never-built features adjudicated DROP AND SCRUB on parity grounds, with the reasoning in the spec's `-rationale.md` companion). The pointer half was discharged earlier by the spec-010 residual cycle (2026-08-15). Nothing remains for this card from the spec-009 side; the bullet stands as the record that the no-card-of-its-own residual-cycle disposition held here too.
- `spec-010-foundation-0_0_4.md`'s rule-27 debt is CLOSED - re-measured 2026-08-15 at the spec-010 residual cycle's wrap: zero in-repo raw `path:NN` citations remain, and the 20 occurrences on 14 lines that survive are all pinned third-party prior art at a named upstream version (`strawberry_django` / `graphene` / `graphene_django`), which `AGENTS.md` rule 27 does not reach and which keep their line numbers by design. `## Note on source line references`, the section that institutionalized the practice and was this bullet's stated blocker, was retired whole by an earlier rationale pass and no longer exists in the spec. Nothing is owed; the bullet stays as the record so a later sweep does not re-derive the 2026-08-14 measurement (42 occurrences, 20 in-repo) against a spec that no longer carries the debt.
- The `Verified in upstream` section's per-bullet completion state is unpopulated board-wide, which leaves this card's parity-audit definition-of-done box unmeasurable from the board. Measured 2026-08-14: 101 items across 43 cards, 87 of them `is_complete=False`, and `CardItem.verified_at` set on exactly ZERO - so the auditable half of the machinery (`verified_at` / `verified_by` / `verification_kind`, written by `services.verify_item`) has never been exercised for this section at all. The 14 ticked items sit entirely on cards 1 through 27 and only cards 24 and 25 are fully ticked, so the convention was followed early and then abandoned rather than never adopted - which is why the current state cannot be read as "nothing has been verified". Decide which it is before the parity audit runs: either a tick means an upstream claim was re-derived and 87 are owed, or the section is a prose record whose checkbox carries no contract and the flags should be normalized. Do not backfill ticks as tidy-up - a tick nobody re-derived is worse than an unticked bullet, and `verify_item` exists precisely so the difference is recorded. Raised by the spec-008 residual cycle against `DONE-008-0.0.4`'s two entries; the board-wide measurement is what turned a single-card observation into this card's.
- Sweep the `[spec-011]` renumber artifact across the documentation tree: 43 standing occurrences across 13 files mostly mean the pre-renumber `spec-011`, which is today `docs/SPECS/spec-015-relay_interfaces-0_0_5.md` (this card's namesake spec was created at `81e4704d` while `spec-011-relay_interfaces-0_0_5.md` still held the number; the renumber landed at `df13b644`). Two files define a `[spec-011]` link resolving to `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` while their prose means the relay spec: `docs/SPECS/spec-032-full_relay-0_0_9.md` and `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`. Same defect class as the swept dead card id `TODO-BETA-053-0.1.5` this card already records (32 occurrences across 10 files, repointed to 062 on 2026-08-07). Measured 2026-08-15 by the spec-011 residual cycle (`docs/builder/bld-011-final.md`), which deliberately did not partial-fix it: correcting one file leaves the cluster divergently rather than uniformly wrong. The six package-source and test occurrences are carried by `TODO-ALPHA-053-0.0.15`, whose WP batches open those files. The `[spec-013]` sibling of this cluster is documentation-only and lands whole on this sweep, with no half for `TODO-ALPHA-053-0.0.15` (measured 2026-08-16 by the spec-013 residual cycle, `docs/builder/bld-013-final.md`): `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` carries **six occurrences - five uses plus the definition line all five depend on**, so renaming the uses without `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md #"[spec-013]: spec-017-deferred_scalars-0_0_6.md"` dangles all five: one in the `Predecessors:` line, two in a single sentence under `## Problem statement`, one under `### Decision 4`, one under `### Decision 5`, and the definition itself. The target already resolves correctly to `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` - only the label is the pre-renumber artifact. Re-derived 2026-08-17 by the spec-017 residual cycle (`docs/builder/build-017-deferred_scalars-0_0_6.md`), where the spec-013 cycle's "five" counts the uses only; do not carry the smaller figure forward. A fourth surface of the same cluster is `CHANGELOG.md #"Tracked as [013-deferred_scalar_conversions-0.0.6]"`, whose `[0.0.6]` `BigInt` bullet names the pre-renumber label in prose where the card is `DONE-017-0.0.6`; its link definition resolves correctly, so the label alone is the artifact, and it lands here rather than alone because `AGENTS.md` rule 21 closes `CHANGELOG.md` to a build cycle and this card owns the CHANGELOG promotion. **Neither `docs/SPECS/spec-018-meta_primary-0_0_6.md` nor `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` is part of this population any more.** Each carried one Prior-`0.0.6`-card note naming the pre-renumber filenames `spec-013-deferred_scalars` and `spec-014-meta_primary` - today the archived real-M2M stub and `docs/SPECS/spec-018-meta_primary-0_0_6.md` respectively - and each was retired by that spec's own residual cycle in favour of post-renumber card ids: spec-018 on 2026-08-18 (`DONE-016-0.0.6`, `DONE-017-0.0.6`, that card, `DONE-019-0.0.6`), and spec-019 the same day on the spec-018 precedent. Re-derived 2026-08-18 after the spec-019 cycle: `grep -c 'spec-013'` and `grep -c 'spec-014'` each report **0** for both specs in the working tree and **1** each for both at their own cycles' parent commits. Do not re-add either from an older reading of this bullet. **Neither spec was ever in the `[spec-011]` half of the cluster** - `grep -c 'spec-011'` returns 0 for both before and after their cycles - so the 43-across-13 figure at the head of this bullet is untouched by either departure and must not be decremented for them. A fifth surface, the same shape as the fourth and landing here for the same two reasons: `CHANGELOG.md #"Tracked as [015-consumer_override_semantics_scalar_fields-0.0.6]"`, whose `[0.0.6]` annotation-only-scalar-override bullet names the pre-renumber label in prose where the card is `DONE-019-0.0.6`. Its reference-style definition (`[card-consumer-override-semantics-scalar-fields]`) resolves correctly, so the label alone is the artifact; `AGENTS.md` rule 21 closes `CHANGELOG.md` to a build cycle and this card owns the CHANGELOG promotion, and half-fixing a cluster leaves it divergently rather than uniformly wrong. Deferred deliberately by the spec-019 residual cycle 2026-08-18, whose one authorized `CHANGELOG.md` correction was a separate false mechanism claim in the same `[0.0.6]` entry - so that entry has already been opened once without this label being touched, by decision rather than oversight.
- Add an unused-link-definition check to the spec/rationale consistency checker this card already scopes (the defs / uses / undefined / orphan scaffold check): measured 2026-08-15 by the spec-011 residual cycle, 23 files carry 71 link definitions no body reference uses (largest: `KANBAN.md` 28, DB-generated; `spec-051` 6; `spec-050` and `spec-055` 5 each; `CHANGELOG.md` 5), including an unused `[backlog]` definition in eight archived specs (`spec-011`, `spec-012`, `spec-013`, `spec-016`, `spec-024`, `spec-026`, `spec-036`, `spec-055`). Invisible to both existing checkers - `scripts/check_trailing_commas.py` enforces only the header scaffold and `scripts/check_spec_glossary.py` only glossary terms. `docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md` deliberately contributes two (`[backlog]`, `[kanban]`) so it is not the single exception in the 23-file pattern; the sweep retires all 71 at once. Re-measured 2026-08-16 by the spec-009 residual cycle under an explicitly stated rule (corpus: 267 git-tracked `.md` files; a definition is a line matching `^[ref]:`; a use is the full `[text][ref]`, collapsed `[ref][]`, or shortcut `[ref]` form): **70 definitions across 23 files**, where `spec-055` now carries 4 not 5 and `docs/SPECS/spec-028-orders-0_0_8.md`'s unused `[relay]` is in the set. **Do not simply overwrite 71 with 70 - the two readings are different instruments, not one drift.** R4's edit consuming `spec-055`'s `[kanban]` accounts for exactly one, but the 2026-08-15 reading also records `docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md` as deliberately contributing two where the 2026-08-16 reading finds one, so the totals agree by coincidence of offsetting deltas rather than by agreement. **The sweep must pin the use-detection rule FIRST and re-derive once**, then retire the population in one pass; adopting either figure without restating its rule reproduces the corpus-definition defect this card's sibling bullet records. Neither reading is flagged by any checker: `scripts/check_trailing_commas.py --check` exits 0 on both `spec-055` and `spec-028`.
- The boilerplate 'expand it into the full builder-format spec' preamble is **DISCHARGED board-wide**: re-derived 2026-08-19, **zero** files under `docs/SPECS/spec-*.md` carry it. This bullet previously stated the population as three - `spec-016`, `spec-024`, `spec-026` - and that figure was already stale when last read: measured at the parent commit of the spec-026 residual cycle, `spec-016` and `spec-024` were each **0** and only `spec-026` was **1**, so the true remaining figure was one, not three. Each of the three was retired by its own residual cycle MOVING the preamble into that spec's `docs/SPECS/appx/spec-NNN-...-rationale.md` companion, which is where the surviving occurrences legitimately live: a `grep -rl` across `docs/` now returns only those companions plus per-cycle `docs/builder/` artifacts quoting them, and **none of those is an edit**. Do not re-derive three, four, or five from an older reading of this bullet, and do not "fix" the companion copies - the move is the fix. What remains open on this card is unchanged and is the question this count was only ever a symptom of: whether a `-rationale.md` companion is owed by every shipped spec or only by one whose cycle produced it, which is this card's separate rationale-companion decision above.
- `AGENTS.md` rule 31's version-parity concern is **DISSOLVED**: the release is single-sourced in `django_strawberry_framework/__init__.py` `__version__`, and hatchling derives the pyproject packaging metadata from it via `[tool.hatch.version]`, so `pyproject.toml` carries `dynamic = ["version"]` and no second literal exists. The item as written asked for a gate pinning `pyproject.toml` `[project].version` against `__version__`; that literal is gone, so nothing remains to pin and no gate is owed. `tests/base/test_init.py::test_version` is the single pin on the one surviving literal. Recorded 2026-08-26, when the mechanical two-source comparison was removed from `scripts/bug_hunt.py::_package_release` together with the tests that pinned its bypass. `uv.lock`'s `django-strawberry-framework` root entry is the one remaining independent copy and stays out of scope here.
- ONE repo-wide sweep, in place of N one-clause fixes: does any archived spec's `0.0.X` deferral have a card? Sized by the spec-009 residual cycle at 56 archived specs, ~34 carrying a deferral-plus-version line, ~190-200 candidate lines (`docs/builder/bld-009-final.md` `### Deferred work catalog` items 5-11 carry the full grading). Folds in: `spec-034-permissions-0_0_10.md`'s four `TODO-BETA-046-0.1.1` citations - 3 live-claim sites (`:220`, `:224`, `:307`) to repoint at the FieldSet card, and 1 revision-log bullet (`:14`) that is a DECIDED NON-EDIT (true as history: `046` was the live id on 2026-06-14, before the 2026-07-30 renumber, so rewriting it would falsify a real record); `spec-028`'s two orphaned `0.0.9` deferrals - `DjangoListField` orderBy-argument integration (`:195`/`:1191`, no card anywhere: needs the spec-009-style card-or-drop parity adjudication before the `1.0.0` freeze) and the position-side-channel leak-closing design (`:734`, verify first: the shipped OrderSet per-field `check_<field>_permission` gates may already discharge it; if a real gap survives, the node-sentinel redaction card is the board's leak-posture home); `spec-027`'s "lands when `DjangoConnectionField` ships in `0.0.9`" auto-generation sentence (scrub to match `spec-028` Decision 12's standing-non-goal precedent; the wording depends on the dynamic-set-factories answer carried by the DRY-squeeze card's WP-D); the `DONE-028-0.0.8` card body still saying Layer 6 is "deferred to `0.0.9`" (DB edit plus regenerate); `spec-028`'s 7 `WIP-ALPHA-*` citations and the `WIP-ALPHA-*` prefixes in `connection.py` / `types/finalizer.py` / `types/relay.py`; and the 8 raw `Decision N line NN` refs in package source violating AGENTS.md rule 27 (the live-code halves coordinate with the DRY-squeeze card's WP batches, which already own this shape). Two cautions: honour the spec-034 3+1 split, and do not mistake `orders/factories.py`'s "standing deferred Non-goal" wording for an orphaned deferral - it names no version and no owner. Two method rules the sweep inherits from the cycle that sized it. **State corpus exclusions by BASENAME, not by path prefix - a path prefix silently fails on an archived copy.** That cycle's two token sweeps measured over different permanent corpora without either noticing: a path-prefix reading excluded 137 files under `docs/builder/bld-`, `docs/builder/build-`, `docs/review/` and `docs/dry/` for 620 files, while a basename reading (per-cycle build documents excluded wherever they live) gave 606; **the 14-file difference is a directory, not a file** - every one sits under `docs/builder/DONE/`, whose paths begin `docs/builder/DONE/build-` and so escape the `docs/builder/build-` prefix. The recorded figures 15/5 for `TODO-BETA-046-0.1.1` and 27/9 for `DjangoModelType` are each correct under the rule they were computed with and **must not move**. The part worth carrying: **two independent agreeing re-derivations did not catch the mismatch**, because each instrument inherited the corpus definition from the thing it was checking; only running one population under both readings did. Second, when this sweep opens `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md`, its `## Standing notes` "three sites" bullet is **DELIBERATELY stale and owed a correction** - the measured count is four (`filters/sets.py` is the fourth applier) and the spec's own opener was already corrected to "four sites"; it was left because that cycle held the rationale append-only, and the staleness is stated in-file five lines above it. Correct it in the first pass that has the rationale open without that constraint.
- Cross-spec rot into `docs/SPECS/spec-010-foundation-0_0_4.md` from the spec-009 scrubs, 2 live sites: `#"custom field classes"` still lists that phrase among what spec-009 describes, which is exactly the `DjangoModelField` claim the spec-009 residual cycle scrubbed as its D1 - spec-009 no longer describes it, so drop the phrase; and `#"is the right helper for the day"` still names `get_strawberry_annotations` as the helper for a future consumer-override contract, a borrow scrubbed as D3 whose opposite spec-009 now states (provenance is solved structurally by the `consumer_*_fields` frozensets on `django_strawberry_framework/types/definition.py::DjangoTypeDefinition`), so retire the sentence. Carried unrepaired for ten consecutive passes because every pass treated spec-010 as a concurrent cycle's read-only file. **The third site is CLOSED**: the `#"### Layer 3: Finalization trigger"` anchor was repaired by the spec-010 residual cycle (2026-08-15) and now correctly records the auto-trigger direction as not adopted - re-verified 2026-08-16, do not re-raise it. Measured by the spec-009 residual cycle (`docs/builder/bld-009-final.md` deferred-work catalog items 1-3).
- Board-DB spec-path rot: the sweep is PART-DISCHARGED; only the maintainer-decision half is left. `CardItem` text cites specs as `docs/spec-NNN-...`; the fix is an ORM edit plus regenerate, and the disposition splits three ways. **(a) DISCHARGED 2026-08-19 - renumber residue, 4 occurrences across 3 cards** (cards 057, 058 which carries TWO, and 060). Each predicted its own spec under the pre-2026-07-30-renumber number, so an author following the instruction would have created a file violating `AGENTS.md` rule 26 (`NNN` = card number). Only the number was corrected; `docs/` was KEPT, because rule 26 makes it the correct directory for a not-yet-authored spec and a blanket `docs/` -> `docs/SPECS/` rewrite is WRONG here. **(b) DISCHARGED 2026-08-19 - 3 occurrences on cards 055 and 056**, where the spec already exists AND is archived: the number was right and the directory stale, so these were repointed to `docs/SPECS/`. **(c) OPEN, and the only part still needing a decision - 13 occurrences across 12 `CardItem` rows on 8 DONE cards (028 carrying three, 029 / 030 / 032 carrying two each, and 033 / 034 / 035 / 045 one each), probably NON-EDITS.** Each spec was authored at `docs/` per rule 26 and swept to `docs/SPECS/` by a LATER cycle, so the bullet is true as history and repointing it would claim the card added the file somewhere it did not; same grading as the spec-034 `#"Revision 2"` bullet this card's deferral sweep already protects. Whether a Done card's DoD should stay a historical record or become navigable is a maintainer contract call. **Re-derived 2026-08-25 by the spec-030 residual cycle, classifying every `docs/spec-` token in `CardItem.text` on path existence, and the 2026-08-19 re-derivation does not survive it:** (c) is 13 occurrences on 8 cards, not 10 on 5 - cards 034, 035 and 045 each carry exactly ONE (`definition_of_done` on 034 and 045, `files_touched` on 035), so the 2026-08-19 claim that they carry ZERO and were named in error is itself false, and the 12-on-8 figure it overturned was the closer of the two readings. The self-check that catches this without re-measuring anything is already inside this bullet: (a) 4 + (b) 3 + (c) 10 sums to 17, which cannot be reconciled with the same sentence's correct occurrence total of 20, and 20 - 4 - 3 recovers (c) = 13 exactly. **Keep both corrections visible so the rewrite is not re-reverted a third time.** (a) still holds at 4 occurrences on cards 057, 058 (two) and 060, every one correctly left at `docs/` per rule 26; (b) is confirmed discharged, with zero `docs/spec-` tokens left on cards 055 and 056. One counting-basis caution for whoever opens this: a per-spec reading of the rendered `KANBAN.md` and a per-card reading of `CardItem` rows agree here only because each card cites its OWN spec, and 13 occurrences sit on 12 rows because one `note` row on card 028 carries the path twice - so state which basis a future count used. Originally enumerated 2026-08-16 by the spec-009 residual cycle (`docs/builder/bld-009-final.md` catalog item 21, which recorded only card 055's DoD site). The source/test half of this same defect is carried by `TODO-ALPHA-053-0.0.15`.
- Add a cited-substring uniqueness check to the spec/rationale consistency checker this card already scopes, alongside its source-symbol-citation and unused-link-definition siblings: `AGENTS.md` rule 27 requires a `#"substring"` citation to name a UNIQUE substring in its target file, and nothing verifies it. Two measured instances, both in `docs/SPECS/spec-015-relay_interfaces-0_0_5.md` and both predating the cycle that found them: `pyproject.toml #"version ="` matches 2 times and `django_strawberry_framework/types/finalizer.py #"_attach_relation_resolvers"` matches 3. Both point at the right place, which is why they were recorded rather than tightened - rewriting a working anchor to buy uniqueness is exactly how that cycle's one High-severity finding started: its reconciliation pass reworded four cited spec sentences and silently retired the anchors seven shipped source and test sites quote, via an inserted "the", a dropped "explicitly" and a dropped parenthetical. So the checker reports non-uniqueness and does not repair it, and any pass that does tighten an anchor must sweep the citing source in the same change. The checker owes the reflow case too - a citing comment that is line-wrapped splits its own quoted substring across a line break and goes invisible to the plain grep rule 27 depends on, which is a defect in the CITING file rather than the cited one, and whose measured instance is carried by `TODO-ALPHA-053-0.0.15`. Measured 2026-08-16 by the spec-015 residual cycle (`docs/builder/bld-015-final.md` deferred-work catalog item 6). A third measured instance, 2026-08-18 by the spec-022 residual cycle: `docs/SPECS/spec-022-export_schema-0_0_7.md` cites `docs/GLOSSARY.md` #"[Schema export management command](#schema-export-management-command)" at `:53`, `:572` and `:574`, and that exact string matches **5** times in the target - the Index-table row `:210`, the group roster `:253`, two `**See also:**` rows `:532` and `:1833`, and the `## Schema introspection management command` entry body `:1829` - so no shorter form buys uniqueness either. Making it unique means citing the whole index-table row, which is a form question across every spec that cites a `docs/GLOSSARY.md` index row rather than a spec-022 repair; that cycle fixed only the rendering half, wrapping each #"..." token in a code span so the quoted text stops rendering as a link to a nonexistent spec anchor. The published population was 3 and is 5. **A fourth measured instance, 2026-09-01 by the spec-035 residual cycle, and the first of the opposite kind - an anchor that is unique only by luck.** `tests/optimizer/test_walker.py::test_enable_only_defaults_enabled_without_info` cites `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md #"defaults to enabled"`, four common words carrying no `G2` / `info` / `operation` token. It resolves **exactly once** today, which is all rule 27 requires, so there is nothing to repair and it must not be rewritten on this item's own reasoning above. It is recorded because it is the shape the checker should *warn* on rather than fail: an anchor whose substring stops being unique the moment the target grows one more sentence using that phrasing. A pass already editing that docstring for another reason should prefer ``#"`info.operation` defaults to enabled"``. Full derivation at `git show 8c05f7fc:docs/builder/bld-035-final.md` item D8.
- Three rule-27 source-reference spellings left by the spec-016 consolidation in files no `TODO-ALPHA-053-0.0.15` WP batch opens, so they belong to this card's repo-wide sweep rather than that card's fold-into-the-batch convention. `django_strawberry_framework/registry.py`'s module docstring carries **two** in one reader list - `types.converters.resolved_relation_annotation` and its sibling `types.converters.convert_choices_to_enum` - where rule 27 requires `django_strawberry_framework/types/converters.py::resolved_relation_annotation` and `django_strawberry_framework/types/converters.py::convert_choices_to_enum`; the spec-016 cycle recorded only the first, and fixing one of two entries in the same list would leave that list divergently rather than uniformly spelled, so they move as a pair. `django_strawberry_framework/types/converters.py::convert_scalar` carries the third as a slash-and-dot hybrid, `types/base._build_annotations`, where rule 27 requires `django_strawberry_framework/types/base.py::_build_annotations`. All three name live symbols with one definition each, so none is a stale reference and none is urgent - only the spelling is wrong. Same class as this card's existing item on the 8 raw `Decision N line NN` refs in package source, and it inherits the same coordination rule: if either file is opened by a `TODO-ALPHA-053-0.0.15` WP batch first, the live-code half sequences there instead. Measured 2026-08-17 by the spec-016 residual cycle (`docs/builder/bld-016-final.md` deferred-work catalog items 3 and 4, the second entry in `registry.py` measured at homing time).
- The `DONE-017-0.0.6` card body asserts a contract the package retired two releases later: it says the Strawberry class-direct-to-`scalar()` `DeprecationWarning` is suppressed at the definition site behind a tight `warnings.catch_warnings()` filter. No suppression exists at `HEAD` - `DONE-025-0.0.7` removed it (`docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` Decision 6), and `django_strawberry_framework/scalars.py` now defines `BigInt` as a bare `NewType`, binds behaviour through Strawberry's no-warning `name=`-only `strawberry.scalar(...)` overload, and registers it via `_PACKAGE_SCALAR_MAP` behind the public `django_strawberry_framework/scalars.py::strawberry_config` factory. DB-backed, so the fix is an ORM edit plus regenerate - the same instrument as this card's board-DB spec-path-rot bullet, but NOT the same grading: that bullet's (c) sites are true as history, whereas this one asserts the suppression in the present tense as shipped behaviour and is simply false. Population measured 2026-08-17 by the spec-017 residual cycle (`docs/builder/build-017-deferred_scalars-0_0_6.md`, catalog item MF-1), twice - rendered and DB-side: 4 occurrences of `suppress*` in the rendered card body, from `CardItem` 703 (note), 713 (test plan) and 715 (note) plus `CardReference` 62 (`raw_text`, card 39 -> card 47) on card `id=39`. **Rows 715 and 62 are byte-identical and must be amended together** or the rendered card contradicts itself, and the FK-backed card-reference placeholder both of them carry must be preserved verbatim. Exact current and replacement text for all four rows is in `docs/builder/build-017-deferred_scalars-0_0_6.md` `### MF-1 replacement text`, folded there as this cycle's per-round artifacts were deleted at closeout. Post-edit verification: the occurrence count drops to 3, all past-tense, with zero occurrences of the phrase `is suppressed at the definition site`.
- The `DONE-018-0.0.6` card body names a symbol the package made private the day before that card shipped: `CardItem` 723 (`note`, order 6) reads "`finalize_django_types()` runs `audit_primary_ambiguity()` first", where the live symbol is `django_strawberry_framework/types/finalizer.py::_audit_primary_ambiguity`, private since commit `13d8dac5` (2026-05-18). DB-backed, so the fix is an ORM edit plus regenerate - the same instrument as this card's board-DB spec-path-rot bullet and the same grading as its `DONE-017-0.0.6` suppression bullet: the sentence names a public API in the present tense and is simply false, not true-as-history. **One row, not two.** The spec-018 residual cycle's hand-off (`docs/builder/build-018-meta_primary-0_0_6.md` `## Closeout record` hand-off 1; the `bld-018-final.md` artifact it was first recorded in is deleted, and lives only in commit `b5b2af81`) also charged this body with quoting the retired duplicate-primary message `"<new> is already declared primary as <existing>"`; that half was derived from the verbatim card-body copy held in `docs/SPECS/appx/spec-018-meta_primary-0_0_6-rationale.md` and does NOT hold against the board. Re-derived 2026-08-18, before this bullet existed: the substring `declared primary` returned zero `CardItem` rows, zero `CardReference` rows, and zero occurrences in the rendered `KANBAN.md`. It returns one of each now, and that one is **this bullet's own quotation of the retired message** - re-measure by excluding this row, not by reading the raw count as evidence the second edit exists. Do not go looking for it. Post-edit verification: `audit_primary_ambiguity` unprefixed by an underscore returns zero rows on card 18 and exactly one board-wide - `CardItem` 1331, this card's sibling `TODO-ALPHA-053-0.0.15` bullet, which already spells it `types/finalizer.py::_audit_primary_ambiguity` and is NOT an edit. Independent of the naming fix and deliberately not folded into it: **10 of this card's 15 `note` items end mid-sentence** (rows 720, 721, 722, 723, 725, 726, 727, 728, 732, 733), an import-time truncation predating every residual cycle, so row 723 is both stale and clipped. Repairing the clip means recovering ten bullets' lost text from the card's own history and is a card-wide decision this bullet does not authorize; fix the symbol name without extending the sentence.
- `CHANGELOG.md`'s whole `## [0.0.7]` section labels every card by its pre-2026-07-30-renumber number: **14 occurrences across 7 distinct labels**, all between `CHANGELOG.md #"## [0.0.7] - "` and the `## [0.0.6]` heading, every one the visible-text half of a `[label][ref-id]` reference-style link. Label -> live card id (occurrences): `016-djangolistfield_non_relay_list-0.0.7` -> `DONE-020-0.0.7` (1); `017-appspy_and_django_app_config-0.0.7` -> `DONE-021-0.0.7` (1); `018-schema_export_management_command-0.0.7` -> `DONE-022-0.0.7` (**5**); `019-multi_database_cooperation_contract-0.0.7` -> `DONE-023-0.0.7` (1); `046-django_trac_37064_hardening_safe_wrap_connection_method-0.0.7` -> `DONE-024-0.0.7` (2); `047-warning_free_scalar_registration_via_strawberryconfigscalar_map-0.0.7` -> `DONE-025-0.0.7` (3); `048-scalar_conversion_end_to_end_coverage_in_the_fakeshop_example-0.0.7` -> `DONE-026-0.0.7` (1). **Nothing is broken and no post-renumber label survives in the section**, so it is uniformly rather than divergently stale: all 7 reference definitions resolve (`[card-djangolistfield-non-relay-list]: KANBAN.md#djangolistfield_non_relay_list` and its six siblings) because the anchors are slug-based, not number-based - the visible labels alone are the artifact. Same shape, same boundary and the same `AGENTS.md` rule 21 reason as the `[013-deferred_scalar_conversions-0.0.6]` and `[015-consumer_override_semantics_scalar_fields-0.0.6]` CHANGELOG label surfaces this card's `[spec-011]` documentation sweep already carries: `CHANGELOG.md` is closed to a build cycle and this card owns the CHANGELOG promotion, so correct all 14 in one change or none. **Count trap, measured 2026-08-18 by the spec-020 residual cycle and corrected here:** that cycle's catalog (`docs/builder/build-020-list_field-0_0_7.md` `## Deferred-work homing` item 1) stated the population as one occurrence per label with `046` twice - effectively 8 - because it enumerated distinct labels and spot-checked only the repeat it happened to see. `018` occurs 5 times and `047` 3. Enumerate per label with `grep -o`; a label list is not a population.
- `DONE-020-0.0.7`'s `#### Package files` lists `django_strawberry_framework/apps.py`, which is `DONE-021-0.0.7`'s subject and not that card's. Verified in the DB 2026-08-18: `CardPathLink` rows of kind `changed` link `apps.py` to BOTH card 20 (alongside `django_strawberry_framework/__init__.py` and `django_strawberry_framework/list_field.py`) and card 21, where it is the sole entry. Board-DB-backed, so the fix is an ORM edit deleting the card-20 link plus a `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py` regenerate - never a hand-edit of the generated `KANBAN.md`. Same mechanism as this card's 20-occurrence board-DB spec-path-rot item. **One correction to how the spec-020 residual cycle recorded this** (`docs/builder/build-020-list_field-0_0_7.md` `## Deferred-work homing` item 2): it said a DB fix 'would be overwritten by the next `manage.py import_card_files`'. That command does replace each named card's linked file set exactly, but **no card-files JSON is checked into the repo** - the only `"cards"`-keyed JSON anywhere is written by `examples/fakeshop/apps/kanban/tests/test_commands.py` into `tmp_path` - so there is no stored input that would re-apply the error and a DB fix is durable. The residual risk is narrower than stated: that whoever next hand-authors a JSON for card 20 copies the same wrong file list. Carry the correction with the fix.
- `docs/GLOSSARY.md`'s `## Schema introspection management command` entry (`DONE-029-0.0.9`) states no selector-rejection contract at all, while its sibling `## Schema export management command` now does. Measured 2026-08-18 by the spec-022 residual cycle: a sweep for `relative module path` / `module path is empty` / `_imports` / `selector validator` over `docs/GLOSSARY.md` returns exactly one line, the export entry's. Not fixable by copying that sentence - `inspect_django_type` reaches `django_strawberry_framework/management/commands/_imports.py::_validate_absolute_module_path` through BOTH helpers and therefore under two labels (`schema selector` via `import_module_symbol_or_command_error` at `inspect_django_type.py:134`, `dotted object path` via `import_string_or_command_error` at `:165`), and the second helper raises a third rejection `export_schema` cannot reach, `_imports.py` #"is not a valid dotted object path: a module path is required." So the introspection entry owes THREE rejections written against its own command, not two. Reuse the export entry's `docs/GLOSSARY.md` #"rejected by the shared `_imports` selector validator" phrasing for the two shared shapes, so a rename of the validator greps to both sites. DB-backed: the entry is a `GlossaryTerm` row, edited through the ORM and re-rendered, never hand-edited in `docs/GLOSSARY.md`.
- `CHANGELOG.md` records the `0.0.7` `export_schema` command as shipped but carries none of the four behaviors that landed after that cut, and no later release section adds them either: whitespace-only `--path` rejection (`7f04c5b2`), the `(OSError, ValueError)` widening plus `newline=""` byte-identity (`fd3825a2`), and both malformed-selector rejections (`61f6726c`). Measured 2026-08-18 over the whole file: `whitespace` 0, `relative module` 0, `module path is empty` 0, `byte-identit` 0, `newline=` 0, `ending=` 0. This is NOT staleness of the kind the glossary had - a changelog records what each release said, and the spec-022 rationale companion's Decision 5 entry records the standing call that the `0.0.7` text is a faithful quotation of already-shipped prose, which the spec-022 integration pass proved rather than accepted (the spec's 607-character `## Doc updates` prescription is present in `CHANGELOG.md` verbatim). So the open item is a maintainer decision about what the file is for: if it is meant to be complete rather than historically faithful, those four are the missing entries under whichever release carried them, and this card's `[0.1.0]` promotion is where they land. `docs/README.md` needs nothing - its one pointer bullet at `:113` makes no error-shape or byte-identity claim.
- Specs cite verification evidence by interpreter-versioned `.venv/lib/python3.NN/site-packages/...` path, which rots on every interpreter bump. Measured 2026-08-18 across `*.md` and `*.py`, excluding per-cycle `docs/builder/` artifacts: **24 `python3.10` occurrences across 3 files** - `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` 19, `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md` 3, `docs/SPECS/spec-022-export_schema-0_0_7.md` 2 - against 73 `python3.14` occurrences, and the shared `.venv` is `python3.14`, so none of the 24 paths exists today although every symbol they name does. The spec-022 cycle graded its own 5 and deliberately left them: they are authoring-time provenance rather than contract, that spec's floor genuinely is Python 3.10, and rewriting them to the shared `.venv`'s interpreter would encode a number that moves on the next bump. That makes this a repo-wide convention decision - whether a spec may cite a `.venv` path at all, and what replaces it - rather than a per-spec repair, which is why it lands here and not on the specs. **The population is the correction:** the spec-022 deferred-work catalog published it as 5, because that figure counted only the two files the cycle itself owned; `spec-025` carries 19 more and was never in view.
- Add a generated-target class to the spec/rationale consistency checker this card already scopes, alongside its source-symbol-citation, unused-link-definition and cited-substring-uniqueness siblings: a #"substring" citation whose target is a script-rendered document (`docs/TREE.md`, `KANBAN.md`, `docs/GLOSSARY.md`) goes dead every time that document regenerates, through no edit to the citing spec, so the rot is invisible to the spec's own review. Measured 2026-08-18 in `docs/SPECS/spec-022-export_schema-0_0_7.md` with a fence-aware per-line resolver that decodes `\"` before the substring test: 47 citations, of which `docs/TREE.md` 11 dead / 3 live and `KANBAN.md` 1 dead. Cross-spec, not spec-022-specific - every archived spec citing `docs/TREE.md` has it, which is why no single spec's reconciliation can close it. **Carry the rule and the parse rate, never a bare digit:** that cycle's own catalog published 47 tokens / 44 parsed / 11 resolve / 33 dead, and an independent resolver run at homing time parsed all 47 and scored 25 resolve / 22 dead, the two differing almost entirely in how each attributed a target on a line naming two candidate files. Two hand-rolled resolvers disagreeing by that margin is the argument for the checker, and a line naming two candidate targets is its first regression test.
- The `DONE-026-0.0.7` card body carries two stale census sentences, both true when written and false at HEAD; the fix is a board-DB `CardItem` edit plus a `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py` regenerate. Same shape and same boundary as this card's `DONE-017-0.0.6` and `DONE-018-0.0.6` stale-card-body bullets. (i) `CardItem` 762 (`note`, order 2) ends "the only `SET_NULL` ondelete in the example tree, and the only cross-model FK in the scalars app" and **both clauses are false**: `on_delete=models.SET_NULL` occurs **4** times across `examples/fakeshop/apps/*/models.py` (twice in `apps/kanban/models.py`, plus the `tag` FK on `examples/fakeshop/apps/scalars/models.py::ScalarSpecimen` and the `partner` FK on `examples/fakeshop/apps/scalars/models.py::NullableScalarSpecimen`), and the scalars app declares **two** cross-model FKs (`tag` -> `ScalarSpecimenTag`, `partner` -> `ScalarSpecimen`). Count occurrences with `grep -o | wc -l`, never `grep -c`, which counts lines. (ii) `CardItem` 763 (`note`, order 3) claims the pairing exercises "upstream code paths no other example app reaches" and names five - **four of the five were already reached by `apps/library` at this card's own ship commit `2701eb88`** (8 models, 7 sibling `DjangoType` classes, a 7-`CreateModel` initial migration), and the fifth, `SET_NULL` ondelete behavior, is false at HEAD by (i). The claim that survives measurement is narrower: the per-column nullable / non-null converter-branch mirror, which no other example app carries - the two models share 11 identical column names, all required on one side and all `null=True` on the other. **Take (i) and (ii) together** - one card body, one regenerate - and take the corrected wording from `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` (`## Card snapshot`, `### Decision 1`, `### Decision 3`), which already states it, rather than rewriting it: the argument is in `docs/SPECS/appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md` (`D2 and D3`, `D4`). Deferred by the spec-026 residual cycle 2026-08-19, which was fenced to spec files and `.py` files. **The live-source half of this same defect is already CLOSED** by that cycle - four prose passages in `examples/fakeshop/apps/scalars/models.py` and `examples/fakeshop/test_query/test_scalars_api.py` - so this bullet is the board half only and must not re-open the source.
- `CHANGELOG.md`'s `[0.0.7]` entry for `DONE-026-0.0.7` carries three errors in one paragraph, and this card owns them because `AGENTS.md` rule 21 closes `CHANGELOG.md` to a build cycle and this card owns the CHANGELOG promotion. All three sit between `CHANGELOG.md #"## [0.0.7] - "` and the `## [0.0.6]` heading. (i) It says "Three tests in `tests/types/test_converters.py` ... are removed" and names the three `big_integer` / `positive_big_integer` ones; commit `a5c89c98` removed **six**, the missing three being `test_json_field_maps_to_json_scalar_in_schema`, `test_json_field_nullable_in_schema`, and `test_json_field_round_trips_dict_via_schema_execution`. (ii) The same paragraph says "(eight tests" where the ship module carried **nine**, and its enumeration lists eight; the omitted ninth is `test_scalar_specimen_introspects_json_scalar_in_both_shapes`. **One JSON-shaped omission produced both numbers** - the absorbed JSON introspection test (ii) drops is the same test whose three retired JSON counterparts (i) drops - so fix them together or the paragraph stays half right. (iii) It repeats the retired exclusivity shape as "surfaces no other example app touches" over four named paths, falsified exactly as the board copy is. The corrected figures are already normative in `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` (`## Test plan`, definition-of-done items 9 and 11), so this is a transcription from the spec and not a re-derivation. Deferred by the spec-026 residual cycle 2026-08-19, fenced to spec files and `.py` files.
- `docs/GLOSSARY.md`'s three `030` entries never state that `totalCount` selection-gating is directive-resolved, so a consumer reading only the glossary cannot tell whether a `@skip`-ed `totalCount` still costs a query. Measured by the spec-030 residual cycle: a section-scoped sweep for `@skip` / `@include` / `directive` / `should_include` inside the `DjangoConnectionField`, `DjangoConnection` and `Meta.connection` entries returns 0 in all three, while the same vocabulary occurs 4 times in `docs/SPECS/spec-030-connection_field-0_0_9.md`. The gate is `django_strawberry_framework/optimizer/selections.py::should_include`, live-pinned by `examples/fakeshop/test_query/test_library_api.py::test_genre_connection_total_count_skip_include_no_count`. DB-backed regenerate; the spec itself needs no change, which is why that cycle left it open here.
- The already-sliced-`QuerySet` `GraphQLError` is documented in neither `CHANGELOG.md` nor `docs/GLOSSARY.md`: `grep -ciE 'pre-sliced|already-sliced|already sliced|pre sliced'` returns 0 in both. `django_strawberry_framework/connection.py::_guard_source_not_pre_sliced` converts a raw boundary `TypeError` into a clear error when a consumer `resolver=` hands the field an already-sliced queryset - a consumer-visible error contract on shipped surface. The spec-030 residual cycle contracted it in the spec at six sites, so only the two standing docs are outstanding, and it explains WHY the gap existed: the guard reached the package through a commit naming no card and no spec, so no card's documentation obligation ever covered it. Text edit for the changelog plus a DB-backed regenerate for the glossary.
- Decide whether the `notes` column of a spec's `-terms.csv` is contract text that needs a gate or scratch that must stop asserting statuses. `scripts/check_spec_glossary.py::load_terms` validates only the `term,anchor` pair against real glossary headings and never reads `notes`, so that column can assert arbitrary statuses indefinitely with no instrument objecting - and the spec-030 residual cycle found the gap had already bitten, twice over: `030`'s column had drifted to 12 stale cells, several to the opposite of their own spec, and `csv.DictReader` - the parser BOTH readers use, `check_spec_glossary.py::load_terms` and the fakeshop `import_spec_terms` command - was silently truncating 8 of 50 `notes` cells at the first unquoted comma, so part of the column never reached the glossary DB at all. That cycle reconciled `030`'s cells under an explicit scope amendment and 0 of 50 now truncate, but the fix changed a file, not the database: those cells reach the DB only when the importer next runs without `--check`. Sits beside this card's existing `REF_USE_PATTERN` code-span decision - same script, separate decision.
- Add an inline-link-TEXT check to the spec/rationale consistency checker this card already scopes, distinct from its on-disk-resolution check: a resolution-based sweep reports a clean file BY CONSTRUCTION whenever the reference-style definitions are correct and the visible link text is wrong. The spec-030 residual cycle hit the first such population - `docs/SPECS/spec-030-connection_field-0_0_9.md` named its own pre-archival path in prose at 7 occurrences over 5 lines while every `[ref-id]:` definition resolved, so the anchor checker every slice of that cycle used reported the file clean. The instrument that works reconstructs the visible path and classifies it by prefix. `030`'s own sites are closed, but the same archival sweep produced every archived spec, so the latent population spans all of `docs/SPECS/` - and it needs the same three-way classification as this card's board-DB spec-path bullet (rot / correct-in-advance under rule 26 / pre-canonical unnumbered name), never a blanket `docs/` to `docs/SPECS/` rewrite.
- Decide where the shipped keyset-cursor feature is documented, as ONE decision rather than three: `Meta.cursor_field` is public, finalization-validated surface with no owning spec, no `docs/GLOSSARY.md` heading, and no `CHANGELOG.md` entry. Measured by the spec-030 residual cycle: no file under `docs/SPECS/` or `docs/` carries `keyset` or `cursor` in its name; 8 files under `docs/SPECS/` mention `cursor_field` and 6 of those use the `Meta.cursor_field` spelling, yet none has it as its subject - a recount must say WHICH spelling it used, because the two populations differ by `spec-010-foundation-0_0_4.md` and `spec-054-graph_substrate-0_1_1.md`; `grep -c '^## Meta.cursor_field' docs/GLOSSARY.md` is 0 while two entry bodies reference the key as though a reader could look it up, and every other `Meta` key has a heading; and `grep -ci keyset CHANGELOG.md` and `grep -c cursor_field CHANGELOG.md` are both 0. The surface is real - `cursor_field` sits in `ALLOWED_META_KEYS`, is two-stage validated (`django_strawberry_framework/types/base.py::_validate_cursor_field` at class creation plus `validate_cursor_field_columns` at finalization), has 31 occurrences in `django_strawberry_framework/keyset.py`, and raises at four `GraphQLError` sites in `django_strawberry_framework/connection.py` (`_keyset_order_state` three times, `_resolve_keyset_connection` once). `spec-030` Decision 9 correctly attributes the dispatch seam to `connection.py` and the codec to `keyset.py`, which routes those raise sites away from `030` and leaves them owned by nothing. A fourth site is stale in the same direction: `BACKLOG.md`'s `stable_cursor_field` entry still describes the feature in the future tense under its `What we'd do` heading, although it shipped as item 39 sub-feature 3 in commit `51421e54`. Answering 'it owes a spec' spawns a card; answering 'it does not' still owes the glossary heading, the changelog entry and the backlog retitle. Recorded on this card rather than as a new card of its own because inserting one between this card and the `1.0.0` cut shifts every board number from 053 upward by one, and because the spec-or-not question is undecided - creating the card would assert the answer.
- `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md` #"the two milestone rows now cite board cards" claims `docs/README.md`'s two milestone rows cite board cards `052` and `067` through reference-style links. Measured 2026-08-25: `docs/README.md` cites NO card number at all - neither its `0.1.0` row (#"beta release: feature parity") nor its `1.0.0` row (#"stable release: full") carries a card reference in any form. Both digits are wrong and so is the claim's subject, which is why this is the ONE site the 2026-08-25 card-renumber sweep left deliberately unshifted: moving `052` to `053` would have produced a differently-false sentence while implying the claim had been verified. The same sentence's history half (the literal ids `BETA-033-0.1.0` and `STABLE-042-1.0.0` it says were replaced) is correct as history and is not in scope.
- A spec's `-terms.csv` `notes` column carries live card references and they rot silently, because no gate reads that column. Measured 2026-08-25: four cells were stale by one before the renumber sweep even started - `spec-055-fieldset-0_1_1-terms.csv` said `Meta.search_fields` is owned by card `054` (it is owned by the search card), and `spec-056-search_fields-0_1_2-terms.csv` attributed the joint `0.1.2` cut to card `055` in two separate cells and named `053+054` as the two `DEFERRED_META_KEYS` members that land first. All four were written when `FieldSet` was card `053` and search was card `054`; commit `e8a873f9` re-homed those companion FILES without touching their CONTENT. This is the concrete failure behind this card's `notes`-column gating question: the sweep had to repair them at +2 rather than +1, and only a hand review found them.
- `docs/SPECS/spec-058-graph_substrate-0_1_1.md` #"### Decision 10 - joint cut at" had a heading its own in-file links could not reach: the heading punctuates as "joint cut at `0.1.1`: release state" (colon) while both links to it spelled the slug `...-at-011--release-state-...` (the double hyphen a spaced em dash produces). Measured 2026-08-25 while re-syncing heading/anchor pairs through the card renumber. REPAIRED 2026-08-29 in the spec-stem rename sweep by moving the LINK side to match the heading, because the sweep changed the heading numeral and would otherwise have left the pair broken in a second way; the sibling `spec-060-search_fields-0_1_2.md` Decision 10 pair was repaired the same way. The general fix is still owed: this card scopes the spec-consistency checker, and `spec-060`'s Decision 11 heading/link pair (5 links) is the same defect, still open.
- Bare card numerals that were ALREADY stale before the insert-at-052 renumber, so the renumber's +1 does not repair them - each needs a read against its live referent (a +6 after the 2026-08-29 board inserts), not a shift. Measured 2026-08-25, eight sites in two surfaces the renumber deliberately left alone because a numeral wrong in BOTH numberings is a separate defect. (a) Board DB, `Card.planning_note` - a column no renumber has ever swept, on `TODO-BETA-060-0.1.2` (`card-054-owned completion bookkeeping`, `Spec-054: Decision 7`) and `TODO-BETA-061-0.1.2` (`card 054's Meta.search_fields surface`, `card 054's spec text`, `glossary promotion out of card 054's intermediate status`); every one names the SEARCH card, which was 054 only before the 2026-08-08 graph-substrate insert and is 060 today. (b) Board DB, `CardItem` text on `TODO-BETA-061-0.1.2` - scope items and one `definition_of_done` item reading `Card 054 deliberately ships only unprefixed OR-of-icontains search`, `Card 054 ships Meta.search_fields to main`, and `its card-054 intermediate status`, all three the same search-card referent. (c) Two spec-body label/target mismatches the renumber preserved verbatim rather than half-correcting: `docs/SPECS/spec-055-fieldset-0_1_1.md #"Meta.search_fields"` renders the link text `spec-055` over a target resolving to `spec-056-search_fields-0_1_2.md`, and `docs/SPECS/spec-056-search_fields-0_1_2.md` pairs `spec-054` with `TODO-BETA-058-0.1.1` for the same `FieldSet` referent - DISCHARGED 2026-08-29 by the spec-stem rename sweep, which set each link text from its ref-id target and repointed the pair onto `spec-059`/`spec-060`; parts (a) and (b) remain open - a spec stem and a card id one apart, so exactly one of the pair is wrong. Verify each referent before editing: a blanket +1 over this population would make (a) and (b) wrong in a new direction.
- `tests/test_relay_connection.py` has no safe default for a bare `Decision N`, and the exposure is growing. Re-measured across the concurrent commit `24125be6`: **24 references / 16 bare**, up from 20 / 16 at `db7ecb1a`. The module docstring cites `spec-032` while the body carries live references belonging to `spec-030`, `spec-032`, `spec-033` and `spec-047`. **Every reference reads correct today, so there is no live defect** - it is deferred work on three grounds: the file offers a reader no single default to fall back on; the sweep just raised the density of mixed qualified/bare references in it; and the failure mode is silent, a wrong resolution that READS as correct - the same shape already found and closed once in `connection.py`, whose declared `Spec:` line points at `spec-030`'s topically-adjacent Decision 6. Remedy: qualify every bare reference with its `spec-0NN` prefix. **Not a spec edit.** Pairs with this card's existing item on the 8 raw `Decision N line NN` refs in package source and inherits the same coordination rule: if a `051` WP batch opens the file first, the work sequences there. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- Extend `scripts/check_citations.py` to resolve `spec-<NNN> Decision <N>` occurring in first-party `.py` against the `### Decision <N>` headings of `docs/SPECS/spec-<NNN>-*.md`, alongside this card's source-symbol, unused-link-definition, cited-substring-uniqueness and generated-target checker siblings. **Record the caveat with the item, or the gate creates a false sense of coverage: it would have caught NONE of the four instances that motivated it.** The general class is that a prose reference from source into a spec Decision is invisible to every gate this repository has - `check_citations.py` resolves `path::Symbol` and deliberately excludes `docs/`, so it sees neither an ordinal INSIDE a Decision's item list, nor a citation by a Decision's heading text, nor a citation to a Decision that exists but does not state the claim. The extension catches only citations to a NON-EXISTENT Decision. The durable instrument is the spec-side convention already landed in `spec-033` Decision 6's introduction - a citation naming the arm by CONTENT carries its own claim, so target and claim are checkable in one read. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- `docs/TREE.md`'s optimizer entries cannot describe the seven post-ship modules `spec-033` Decision 11 now names (`nested_fetch`, `join_taxonomy`, `nested_planner`, `single_parent_fetch`, `keyset`, `selections`, `utils/connections`). It is script-rendered by `scripts/build_tree_md.py` from module docstrings, so **the fix is a docstring-plus-regenerate change, not a doc edit, and both halves must land in the SAME change** - a hand-edit of the generated tail is reverted by the next render. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- `docs/GLOSSARY.md`'s `## Strictness mode` entry still lists "divergent aliases" among the shapes that fall back per parent, which the idea-#2 inversion (`57cbd32a` / `9580e84e`) retired: divergent aliased pagination arguments are now PLANNED, one window per response key. DB-generated - edit the fakeshop glossary app's `GlossaryTerm.body` and re-render with `scripts/build_glossary_md.py`, never hand-edit. **This is the only stale connection-optimizer entry, and the correction matters:** `## Connection-aware optimizer planning` is NOT stale - it already describes marker rows, the conditional count and n+1 probe, `last: 0`, the argument-conflict fallback, the strategy seam and keyset `Meta.cursor_field`, and the reconciliation used it as its voice reference. Rides the same ORM edit and render as this card's other glossary items. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- `DONE-033-0.0.9`'s card body was never read against the reconciled `spec-033`. The reconciliation rewrote Decisions 4, 5, 6, 8, 9 and 11 and renamed two Decision headings, so any card prose describing four numbered fallback shapes, an unconditional `_dst_total_count`, divergent aliases falling back, or the Decision 9 module placement is stale. The card was read-only that cycle and used only to adjudicate card ids. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- `scripts/check_citations.py` implements one of AGENTS.md rule 27's three citation forms and cannot see a citation that wraps a line, so its green result is narrower than it reads. Re-measured 2026-08-27: `uv run python scripts/check_citations.py` prints `OK: 836 citations resolve (738 in 431 .py files, 98 in KANBAN.md)`, and three populations sit outside that denominator. (a) **Wrapped citations, 9 occurrences across 8 first-party `.py` files** - `git grep -nP '\.py::\s*$' -- '*.py'` finds them in `django_strawberry_framework/filters/__init__.py`, `django_strawberry_framework/orders/__init__.py`, `django_strawberry_framework/exceptions.py` (two: `utils/connections.py::assert_window_fetch_mode` and `optimizer/plans.py::window_partition_for_prefetch`), `django_strawberry_framework/utils/policies.py`, `tests/test_list_field.py` (two), `tests/optimizer/test_extension.py` and `tests/orders/test_composition.py`, plus a tenth wrapping the PATH half in `examples/fakeshop/test_query/test_products_api.py`. All nine symbols resolve today when forced through the gate's own `scripts/check_citations.py::candidate_paths` and `scripts/check_citations.py::module_symbols`, so this is unmonitored surface rather than live rot - but the failability proof is decisive: `scripts/check_citations.py::CITATION_RE` yields one match for a bogus symbol cited on one line and **zero** for the identical bogus symbol with a newline plus comment prefix between `::` and the name, because the path class `[\w./]*` never crosses a newline. (b) **The `#"substring"` pinpoint form is never parsed at all, and 10 sites are dead right now.** 169 pinpoints across 40 first-party `.py` files, 58 of which name an explicit target file; the ten that no longer resolve are `tests/test_list_field.py` citing `django_strawberry_framework/list_field.py::DjangoListField #"return _post_process_consumer_sync("` (twice) and `#"return await _post_process_consumer_async("` (twice) where the target now calls both helpers inside a multi-line expression with no `return` on the same line; `tests/test_list_field.py` citing `AGENTS.md #"Package source lives in django_strawberry_framework"` where rule 6 reads `Package source in`; `tests/optimizer/test_multi_db.py` citing `AGENTS.md #"Test through real usage and prefer the example project"` where rule 10 reads `Test through real usage, prefer the example project`; `tests/test_list_field.py` citing `docs/TREE.md #"single-file Layer-3 module"`, retired by a regenerate; `tests/test_list_field.py` citing `docs/SPECS/spec-020-list_field-0_0_7.md #"Optional ``resolver=`` constructor argument that overrides the default"`, zero matches; `tests/test_list_field.py` citing `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync #"returned a coroutine in a sync"`, a phrase that occurs nowhere in the package and survives only in the two tests asserting it; and `tests/types/test_resolvers.py` citing `django_strawberry_framework/types/resolvers.py::_build_fk_id_stub #"instance = root if hasattr(root, "_state") else None"` where the target now reads `getattr(root, "_state", None) is not None`. (c) **`scripts/check_citations.py #"FAMILY_SUFFIXES = ("_", ".")"` fails open on every dunder**: 10 occurrences in 8 files are skipped, and 7 of them are ordinary single symbols that resolve when forced - `routers.py::__all__`, `error_policy.py::ErrorPolicy.__post_init__`, `utils/permissions.py::ChannelsRequestAdapter.__getattr__` and four `types/base.py::DjangoType.__init_subclass__` - so a dunder rename is invisible to the gate that exists to catch renames. **Three audit clauses do not survive re-derivation and must not generate work.** Mid-path splits are already handled: `main/` and `packages/` in `scripts/check_citations.py #"UPSTREAM_PREFIXES"` are exactly the post-hyphen fragments a hyphenated path truncates to, and every hyphenated cited path in the tree is an absolute upstream checkout path, which is settled convention. Case variants are zero - `git grep -nE '\.(PY|Py|pY)::'` returns nothing tree-wide, against a positive control of 18 `.py::` hits in `django_strawberry_framework/optimizer/plans.py` alone. And the `docs/` exclusion, while real, is currently EMPTY of defects: the seven standing documents outside the gate (`docs/GLOSSARY.md` 16 citations, `BACKLOG.md` 13, `docs/SPECS/NEXT.md` 5, `CHANGELOG.md` 3, `docs/TREE.md` 2, `docs/README.md` 1, `AGENTS.md` 1) carry 41 citations and zero rot. **The exclusion set any extension must carry**: `SYNTHETIC_SOURCES` stays (fixtures, not claims), and the illustrative example in `docs/SPECS/NEXT.md` is the same class - an `e.g.` teaching the citation form over a symbol that exists nowhere in the tree, so widening scope to standing docs without an illustrative-example exemption manufactures a false red on its first run; the spec archive stays out (1660 citations, 75 unresolvable, most correct-as-history); absolute upstream paths stay; and the three genuine prefix families (`filters/sets.py::FilterSet.`, `tests/types/test_resolvers.py::test_check_n1_`, `tests/optimizer/test_extension.py::test_strictness_raise_`) keep their skip. Fix: narrow the family skip so a name matching `__\w+__` is checked rather than skipped; fold a `::`-terminated or `/`-terminated comment or docstring continuation onto its successor line before matching, with the bogus-wrapped-symbol case as the regression test; and add a `#"substring"` resolver for pinpoints that name a target file, seeded with the ten measured dead sites. Distinct from this card's `spec-<NNN> Decision <N>` extension item, which adds a new REFERENCE KIND and explicitly catches none of its motivating instances, and from its cited-substring-uniqueness item, which measures uniqueness on the SPEC side and does not resolve a `.py`-side pinpoint at all. **Amended 2026-09-01 by the spec-035 residual cycle: the dead-pinpoint seed list is 9, not 10.** `tests/types/test_resolvers.py` citing `django_strawberry_framework/types/resolvers.py::_build_fk_id_stub #"instance = root if hasattr(root, "_state") else None"` was retargeted to the live #"instance = root if getattr(root, "_state", None) is not None else None" and now resolves exactly once (`git show 8c05f7fc:docs/builder/bld-035-final.md` D12); the other nine measured sites are unchanged. Keep the discharged site in the regression seed for the `#"substring"` resolver this item scopes - it is the only one of the ten whose rot was caused by a rename in package source rather than by a reflow, so it is the resolver's sharpest positive control.
- The numbered-item citation vocabulary (`Decision N`, `Finding N`, `Revision N`, `Spec-NNN`) is spelled four ways across first-party source and only the anchorless minority is a defect, so the population must be graded by ANCHOR before anything is swept. Re-measured 2026-08-27 over a stated corpus - the 431 git-tracked `.py` files under `django_strawberry_framework/`, `tests/`, `examples/` and `scripts/`, which is the only denominator that means anything here since a tree-wide `git grep -ohP '\bDecision \d+'` over all tracked files returns 7731 against 1265 in this corpus. Of those 1265 `Decision N` occurrences across 155 files, 882 are qualified by an adjacent `spec-NNN` and **383 are bare across 85 files**. Grading the 383 by whether the CONTAINING FILE establishes which spec it means - never by distance to the nearest spec mention - gives 62 in files naming exactly one spec (the accepted convention, leave them), 306 in files naming more than one, and 15 in files naming none. Two of that last group, both in `examples/fakeshop/apps/products/filters.py`, are anchored by a card id rather than a spec stem (`its Decision 11` under a `DONE-034-0.0.10` opener) and are a false positive of any spec-NNN-only instrument, so **the defect population is 13 occurrences across 4 files**: `django_strawberry_framework/permissions.py` carries 8 (`#"(Decision 10). The runner is also the shared sealed visibility boundary"`, `#"cascadable edges (Decision 5 step 1)"` and six more) and names no spec anywhere in the file; `tests/test_apps.py` carries 3 inside its AppConfig expectation table; `django_strawberry_framework/optimizer/hints.py` and `django_strawberry_framework/management/commands/inspect_django_type.py` carry 1 each. The same grading applied to the sibling families: `Finding N` is 19 occurrences across 4 files, 8 of them qualified as `spec-038-form_mutations-0_0_12 Finding N` and **11 bare** (`tests/forms/test_sets.py` 4, `tests/forms/test_resolvers.py` 3, `tests/mutations/test_resolvers.py` 3, `tests/rest_framework/test_sets.py` 1); `Revision N` is 13 occurrences across 4 files, 8 qualified and **5 bare, all in `examples/fakeshop/test_query/test_library_api.py`**, a file naming 15 distinct specs; and the lowercase-qualifier spelling `spec Decision N` is exactly 4 sites, but **the earlier characterization of them is wrong** - `django_strawberry_framework/list_field.py` and `tests/test_list_field.py` both declare `Spec: docs/SPECS/spec-020-list_field-0_0_7.md` in their module docstring, so their bare `spec` resolves, leaving only `django_strawberry_framework/filters/factories.py #"spec Decision 4"` (file names spec-027 and spec-030) and `tests/types/test_resolvers.py #"per spec Decision 5"` (file names five specs, no declaration) unanchored. The remedy for all 30 unanchored occurrences is one of two mechanisms already in the tree: prefix the reference with its `spec-NNN`, or add the `Spec: docs/SPECS/spec-NNN-...` module-docstring line that 9 first-party `.py` files already carry - the second is cheaper for `permissions.py`, which owns 8 of the 13. **`Spec-NNN` capital-S is a separate question and needs a MAINTAINER RULING, not a sweep**: all 52 `.py` occurrences are sentence-initial docstring openers (`"""Spec-027: choice-enum filter clause coerces via Strawberry enum."""`), zero are mid-sentence, so none is rot - the cost is purely that a plain `grep spec-0` census misses them. Option (a) declare sentence-initial capitalization legitimate, change nothing on disk, and oblige every future census to carry the case-insensitive spelling; option (b) forbid it and reword 52 `.py` openers plus 25 `docs/SPECS/appx/*-rationale.md` sites so the stem is always literal, after which a case-sensitive grep is complete. **The exclusion set, without which this bullet generates defects.** The `.md` figure is 123 and decomposes as 121 in `docs/*.md` plus 2 in `KANBAN.md`; of the 123, **96 sit in per-cycle build documents and are excluded by BASENAME wherever they live** (`build-*`, `bld-*`, `dry-*`), per this card's own established corpus rule, leaving 27 standing sites of which 25 are in `docs/SPECS/appx/*-rationale.md`. The 2 `KANBAN.md` sites are DB-generated `Spec-054: Decision 7` strings on `TODO-BETA-060-0.1.2` and are **already owned by this card's already-stale-bare-card-numerals item** - do not re-home them, and never hand-edit `KANBAN.md` or `KANBAN.html` for them. Card-id anchors are valid anchors. Archived specs naming a retired symbol in the present tense are correct as history. The 306 bare-in-a-multi-spec-file occurrences are NOT this bullet's fix list - one file of that population, `tests/test_relay_connection.py`, is already carried by this card's own item, and the two readings differ by instrument and date, not by drift: that item records 24 references / 16 bare, where a same-day count of `\bDecision \d+` alone gives 22 / 12, so **restate the rule before adopting either figure**. Two measurement rules the sweep inherits: count occurrences with `grep -oh | wc -l`, never `grep -c`, which counts lines and produced the per-file table that first looked like a 123-vs-121 contradiction; and `\b` is PCRE only - `git grep -E '\bDecision [0-9]+'` returns **0 tree-wide**, a control that did not run reading exactly like a clean sweep, so every command here must be `-P` and must be paired with a positive control.
- Shipped specs `spec-034` through `spec-039` carry 75 `TODO-ALPHA/BETA-*` card ids and the population will not survive a blanket `TODO-` -> `DONE-` rewrite: only a minority of it is mechanical. Re-measured 2026-08-27 with `grep -ohE 'TODO-(ALPHA|BETA)[A-Za-z0-9._-]*' docs/SPECS/spec-03[4-9]*.md | sort | uniq -c` - 75 occurrences at 034=20, 035=0, 036=13, 037=19, 038=10, 039=13, so the count and the distribution hold, but the claim that every one names a card that is `DONE-` today does not, and neither does "mechanical". **3 named the live fakeshop-activation card**: the `TODO-BETA-062-0.1.5` sites in `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` were exactly right until the 2026-08-29 board inserts moved that card to `TODO-BETA-066-0.1.5`; they are now stale by one and owed the +1 by the renumber's tree sweep - a renumber, never a lifecycle flip. **4 are already owned** by this card's repo-wide archived-spec deferral sweep, whose `spec-034` clause splits the four `TODO-BETA-046-0.1.1` citations into three live-claim repoints plus one revision-log decided-non-edit; do not re-raise them, and carry the reason they are not a prefix flip - card 046 today is `DONE-046-0.0.14` (transport security) while the FieldSet referent is `TODO-BETA-059-0.1.1`, so `DONE-046-0.1.1` would be false in subject, number and version at once. **6 name an id that has never existed in any numbering**: `TODO-ALPHA-035-0.0.11` (card 035 shipped at `0.0.10`), every one a quotation of the `scalars.py` docstring's own error inside a sentence that declares it stale, so a flip manufactures `DONE-035-0.0.11`; the same quotation trap covers `TODO-ALPHA-033-0.0.10` twice and `TODO-ALPHA-027-0.0.10` plus its slash-compound sibling. The remaining 62 do name a card that is `DONE-` today, but they split three ways and only the third is mechanical: **(a)** sites whose enclosing sentence is history and true only in its own tense - 9 in `- **Revision N**` log bullets and 4 in card-wrap `#"to Done with the next"` slice instructions, where de-tensing is the fix and a prefix flip falsifies a real record; **(b)** verbatim quotations of text that has since changed, which a flip makes differently false - 4 sites quoting `docs/TREE.md`'s "planned by `TODO-ALPHA-0NN-...`" predicted-path rows, 4 quoting products-schema markers, 5 quoting card-body text the board has since rewritten into structured card-reference placeholders resolved at render time, and the 4 `#"Upload staged seam (TODO-ALPHA-037-0.0.11)"` rule-27 citations plus `#"Future scalars (e.g. ``Upload`` per TODO-ALPHA-035-0.0.11) land here."`, all five of which are **dangling today** because `django_strawberry_framework/mutations/inputs.py` no longer carries that comment and `django_strawberry_framework/scalars.py`'s module docstring now reads `spec-037` with no card id at all; **(c)** the clean prefix-only remainder, dominated by `spec-038` / `spec-039`'s downstream pointers, where `spec-034` contributes exactly one (`#"The `0.0.10` patch line is shared with"`). Three claim-sites in class (b) are additionally **false on their own date** and need de-tensing rather than renumbering: `TODAY.md` carries zero `TODO-ALPHA-033` (`grep -c 'TODO-ALPHA-033' TODAY.md` returns 0) and `examples/fakeshop/apps/products/schema.py` already reads `DONE-034-0.0.10`, so the `#"Stale card-id reference in `TODAY.md`"` ledger entry, which Slice 0 moved into `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`, describes a defect that no longer exists. **Four grammars, and a sweep that knows one leaves three wrong**: full id (70), version-less id (5 - `TODO-ALPHA-037` twice, `-038`, `-039`, `-027`), the slash compound `TODO-ALPHA-027/034` in `spec-034`'s Revision 8 bullet where one regex match hides a second card number, and bare backticked three-digit numerals, **338** across the six files (034=9, 035=4, 036=16, 037=28, 038=111, 039=170) carrying no lifecycle prefix at all. Do not widen into the 338 - every one names a card below 052 that the insert-at-052 renumber never touched (and, being below 050, the 2026-08-29 board inserts leave alone as well), and a bare numeral asserts no lifecycle state - with one exception no existing item reaches: `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md #"but the live kanban card is"` asserts the FieldSet owner is `046`, an active falsehood today (it is 059) and invisible to any `TODO-BETA-046-0.1.1` sweep. **Nothing moves with the text**: all 38 linked occurrences carry the id as visible link text over one generic `[kanban]: ../../KANBAN.md` definition, and zero of the 75 sit in a link definition, a heading, or an in-page anchor - so unlike a slug-anchored surface this rewrite cannot break a link, and unlike an in-flight spec it opens no `.py`, so no `TODO-ALPHA-053-0.0.15` WP batch is a prerequisite. **The residue is a half-finished sweep, and the files prove their own target spelling**: the same six already carry `DONE-034-0.0.10` 14 times, `DONE-036-0.0.11` 13, `DONE-035-0.0.10` 12, `DONE-033-0.0.9` 11, `DONE-037-0.0.11` 10, `DONE-038-0.0.12` 7, `DONE-039-0.0.13` 3 and `DONE-040-0.0.13` 1, and one sentence appears verbatim in three siblings spelled two ways - `spec-035` reads `DONE-` at `#"so `<NNN>` is"` and `spec-034`'s copy of that sentence now lives in `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` while `spec-036` still reads `TODO-ALPHA-036-0.0.11`. Fix: one documentation pass over the six files that classifies per site before editing - flip class (c), de-tense class (a), leave class (b) verbatim, and never lifecycle-flip the 3 `062` ids (the tree sweep renumbers them to `066`) or touch the 4 homed `046` ids. **One maintainer ruling is owed and should be taken once for the whole class**: whether a shipped spec's verbatim quotation of a source comment that has since been deleted keeps the quotation and accepts a rule-27 citation that no longer resolves, or is restated as a symbol path into the live text (`django_strawberry_framework/mutations/inputs.py` and `django_strawberry_framework/scalars.py` both now say `spec-037`), losing the record of what the seam looked like before it shipped. **The source-side half rides this same pass and cannot be split from it**: `examples/fakeshop/apps/products/schema.py` carries 18 rotted occurrences - `TODO-BETA-046-0.1.1` x7, `TODO-BETA-047-0.1.2` x5, `TODO-BETA-049-0.1.3` x6 - whose live referents are `TODO-BETA-059-0.1.1` / `TODO-BETA-060-0.1.2` / `TODO-BETA-062-0.1.3`, beside one `TODO-BETA-062-0.1.5` that was correct until the 2026-08-29 board inserts and now needs only the +1 to `TODO-BETA-066-0.1.5` (the fakeshop-activation card is still To Do) - **never a lifecycle flip**. The coupling is the reason it is not a separate item: four of the class-(b) leave-verbatim rulings above hold *because the source still reads the old id*, so renumbering the source without the specs falsifies them and renumbering the specs without the source strips their justification. Measured 2026-08-28 by the spec-034 residual cycle (`grep -o 'TODO-[A-Z]*-[0-9]*-[0-9.]*' examples/fakeshop/apps/products/schema.py | sort | uniq -c`).
- Thirteen prose citations into shipped specs address their target by line number, and **every one checked resolves to unrelated text at HEAD** - these are false pointers, not style nits. Re-measured 2026-08-27: `grep -rnE '\blines? [0-9]+' --include='*.py' . | grep -v '/.venv/'` returns 26 physical lines tree-wide, of which the spec-citation subset is **13 citations on 12 lines across 5 files** - `django_strawberry_framework/optimizer/walker.py::_record_relation_access` #"Decision 4 / edge case line 315"; `tests/optimizer/test_walker.py::test_mutation_scalar_only_connection_window_no_only`, `::test_subscription_operation_gated` and `::test_enable_only_defaults_enabled_without_info`; `tests/optimizer/test_extension.py::test_root_fragment_pagination_variable_shares_cache`, `::test_fragment_carried_nested_pagination_variable_collected`, `::test_pagination_var_collection_is_syntactic_superset` and `::_categories_list_schema`; `tests/mutations/test_sets.py::test_bind_dedupes_full_set_fields_with_bare_create` (two) and `::test_bind_dedupes_fields_with_complementary_exclude` (two); and `examples/fakeshop/config/settings.py` #"NOTE(spec-039)". **Two of those files and three of those citations are invisible to the obvious grep**, which is the part to carry: a flat `line [0-9]+` misses the four plural `lines NN` spellings, and no single-line pattern at all sees a citation wrapped across two comment lines - `settings.py` breaks after #"Decision 13 / spec line", `::_categories_list_schema` after #"so the plan is cacheable (spec line", and `::test_bind_dedupes_fields_with_complementary_exclude` after #"Decision 6 line 334 / Edge cases line", so any census must scan line pairs as well as lines. **The resolutions, which are the whole content of this item**: in `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` the `## Edge cases and constraints` section runs one bullet per line and all three citations are off by one or two - `line 315` lands on the G1 async-guard bullet where the claim is `#"every projection writer checks the gate, not just scalar appends"`, `line 317` lands on the Decision 5 consumer-`only()` bullet where the claim is `#"subscription operations are gated identically"`, and `line 320` lands on the connection-field-gated-by-construction bullet where the claim is `#"a missing `info` *or* `info.operation` defaults to enabled"`. In `docs/SPECS/spec-036-mutations-0_0_11.md`, `Decision 6 line 334` lands on the field-set-derivation bullet while the identity claim it asserts is `#"A generated input type's identity is its **complete shape**"`, and `Edge cases line 509` lands on the delete-snapshot bullet - that one is wrong in its **section** as well as its line, because the dedupe contract is not in `## Edge cases and constraints` at all but in Decision 6 at `#"the canonical full editable shape"`. In `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` the reconciliation that rewrote Decisions 4 through 6 pushed all three targets roughly thirty lines: `Decision 7 line 346` and `line 347` now land inside Decision 9 (one of them on a blank line, the other on a rationale-companion pointer) and `spec line 350` lands on a blank line under the Decision 10 heading, where the real targets are Decision 7's `#"the collector tracks depth at the spread site"`, `#"The collection is a syntactic superset by design"` and `#"Cacheable plans and visibility-bearing targets are disjoint"`. In `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` the `settings.py` citation is self-refuting on its face - it reads `Decision 13 / spec line 969` while Decision 13 begins far below 969, and 969 is a Decision 11 allowed-key bullet; the claim it wants is Decision 13's `#"only if a serializer needs the app registry"`. Fix: replace each line number with the spec's `spec-0NN Decision N` plus the cited substring above, and qualify the four bare `Decision 7` / `Decision 4` references with their `spec-0NN` prefix while the files are open - the same defect this card already carries for `tests/test_relay_connection.py`, here in three further files. **Do not sweep**, and the false-positive classes are the majority of the tree-wide 26: the 12 coverage-target comments in `tests/types/test_resolvers.py` and `tests/test_exceptions.py` cite live package source rather than a spec and belong to a live-code batch, not a documentation pass (they are separately rotting - `types/resolvers.py` has moved under at least three of them - but they are not this item); `tests/test_export_dry_review.py #"line 1"` is a string literal asserting on produced output; `scripts/check_trailing_commas.py #"against line 1"` is docstring prose describing behavior; and no live `TODO(spec-NNN Slice N)` anchor carries a line number, so none is at risk. **One maintainer ruling is owed**, on `tests/orders/test_sets.py #"per cookbook line 280"` and `tests/orders/test_factories.py #"cookbook lines 124-130"`: the referent is `django-graphene-filters`' `examples/cookbook/` prior art, which this card's `spec-010` rule-27 bullet already acquitted as outside rule 27's reach - but that acquittal is for a citation pinned at a named upstream version, and neither of these names a file or a version, so either complete them to an upstream path plus pinned version and keep the line numbers under the carve-out, or drop the line numbers and cite the upstream symbol. **Not blocked**: re-checked 2026-08-27, the spec-033 cycle committed at `a51213d7` and `git status --short` shows no dirty `.py`, so `tests/optimizer/test_walker.py` and `tests/optimizer/test_extension.py` are clean and all 13 sites can land in one pass; only `optimizer/walker.py` sits in package source, so if a `TODO-ALPHA-053-0.0.15` WP batch opens that one file first, that single citation sequences there and the other twelve do not wait on it. Supersedes the "8 raw `Decision N line NN` refs in package source" clause this card's repo-wide archived-spec deferral sweep folds in: re-derived, the population is 13, not 8, and only one of the 13 is in package source. **Re-derived 2026-09-01 by the spec-035 residual cycle (`git show 8c05f7fc:docs/builder/bld-035-final.md` deferred-work catalog D4/D5): the population is now 9, not 13, and this item's own instrument cannot see all 9.** The four spec-035-owned citations named above (`optimizer/walker.py::_record_relation_access` #"Decision 4 / edge case line 315" and the three `tests/optimizer/test_walker.py` sites) were replaced with `spec-035 Decision N` plus a `#"substring"` anchor by that cycle and are DISCHARGED - do not re-raise them, and note that its fifth fix, `tests/types/test_resolvers.py::test_fk_id_elision_falls_back_when_consumer_only_defers_fk` #"spec-035 edge case 316", was **invisible to this item's `\blines? [0-9]+` instrument** because the citation spelled the numeral without the word `line`; a census of this class must scan `edge case NNN` as well as `lines? NNN` (both spellings now return 0 for spec-035). The remaining spec-citation subset is **9 citations across 3 files** - `tests/mutations/test_sets.py` 4 (spec-036), `tests/optimizer/test_extension.py` 4 (spec-033), `examples/fakeshop/config/settings.py` 1 (spec-039) - with the resolutions above still correct for each. Two consequences for sequencing: the tree-wide count for `\blines? [0-9]+` over the 433-file corpus is now **24 physical occurrences**, not 26, decomposing as 8 of this item's 9 (the wrapped `settings.py` site stays invisible to any single-line pattern) plus 12 live-source self-citations plus the 2 cookbook sites plus the 2 acquitted false positives; and **the package-source dependency is gone** - `optimizer/walker.py` was the only one of the 13 in package source, so this item no longer sequences behind a `TODO-ALPHA-053-0.0.15` WP batch opening that file and all 9 remaining sites can land in one documentation pass. **The nine remaining sites, inlined so this item no longer depends on a builder artifact for its addresses** (`site | citation as flattened | owning spec`): `tests/mutations/test_sets.py:1034` | `spec-036 Decision 6 line 334` | spec-036; `tests/mutations/test_sets.py:1039` | `spec-036 Edge cases line 509` | spec-036; `tests/mutations/test_sets.py:1073` | `spec-036 Decision 6 line 334` | spec-036; `tests/mutations/test_sets.py:1073` | `Edge cases line 509` | spec-036; `tests/optimizer/test_extension.py:1718` | `Decision 7 line 346` | spec-033; `tests/optimizer/test_extension.py:1754` | `Decision 7 line 346` | spec-033; `tests/optimizer/test_extension.py:1817` | `Decision 7 line 347` | spec-033; `tests/optimizer/test_extension.py:2248` | `spec line 350` (names **no** spec, and wraps) | spec-033, by the file's header comment; `examples/fakeshop/config/settings.py:74` | `Decision 13 / spec line # 969` (wraps, with a `#` between `line` and the number) | spec-039. Note `tests/optimizer/test_extension.py` was inside the spec-035 cycle's writable cohort - those four are out of scope by **spec ownership**, not file ownership, and were deliberately left. Two instrument lessons ride with the list: a `line`-without-`s?` pattern is blind to the plural (`cookbook lines 124-130`), and a comment-continuation `#` between the token and the number defeats any `\s+`-only pattern.
- `DONE-028-0.0.8` and `DONE-029-0.0.9` each carry card-body prose the package now contradicts, and both are board-DB rows, so the fix is a `CardItem` edit plus a `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py` regenerate - never a hand-edit of the generated `KANBAN.md`. Same instrument and same grading as this card's `DONE-017-0.0.6` suppression and `DONE-026-0.0.7` census bullets. **(a) `DONE-028-0.0.8`, the `note` row opening #"Shipped the ordering subsystem in `0.0.8`"** says in the present tense that the apply pipeline runs `check_permissions` with active-input-only scope. No `check_permissions` exists under `django_strawberry_framework/orders/` at HEAD - it shipped there at `11d9fbe0` and was removed at `9e864f59` - and the live surface is `django_strawberry_framework/sets_mixins.py::ActiveInputPermissionMixin._run_permission_checks`, which `django_strawberry_framework/orders/sets.py::OrderSet` inherits rather than defines - cite the defining class, since a citation naming the subclass resolves to nothing. Take the replacement wording from the reconciled spec, which already states it three times, rather than rewriting: `docs/SPECS/spec-028-orders-0_0_8.md #"No instance-method `check_permissions` is shipped on `OrderSet`"`. **Do not sweep the name**: `django_strawberry_framework/filters/sets.py::FilterSet.check_permissions` is a live delegate, and a `CardItem` on `DONE-034-0.0.10` asks a live open question about the filter-side spelling; both stay. Re-measured 2026-08-27, every other symbol that row names resolves at HEAD (`order_input_type`, `clear_order_input_namespace`, `_helper_referenced_ordersets`, `_bind_ordersets`, `_owner_definition`, `LazyRelatedClassMixin`, `ClassBasedTypeNameMixin`, `apply_sync`, `apply_async`), so `check_permissions` is its only false one. The same row also carries **three `rev3` breadcrumbs** - a review-round name, which the no-process-provenance rule keeps out of shipped prose - at #"per H1 of `spec-028-orders-0_0_8` rev3", #"per B3 of rev3" and #"per H3 of rev3"; `grep -o rev3 KANBAN.md | wc -l` and the same over `KANBAN.html` both return 3, and a `CardItem` / `CardReference` / `planning_note` sweep returns exactly one row board-wide. Every other `rev3` in the tree sits in a `docs/SPECS/appx/*-rationale.md` revision-history section, which is where that vocabulary belongs; commit `471d4c6b` swept it from code comments and never reached the board. **Two sub-claims against this row do NOT survive re-derivation and must not be "fixed": the "exactly 14 live HTTP tests" figure and the five-name `orders.py` roster are correct as attributions of what the card grew.** The order block of `examples/fakeshop/test_query/test_library_api.py` holds 16 test functions today (measured 2026-08-27; `git diff HEAD --` on that path is empty, so the working tree equals HEAD despite an earlier dirty snapshot), and the file's own header comment #"The two out-of-card additions are" names both extras as `spec-030` work; `examples/fakeshop/apps/library/orders.py` declares 7 OrderSets, the two beyond the roster (`PeriodicalOrder`, `IssueOrder`) added by the keyset-cursor commit `51421e54`; and the four-direction NULLS parametrization the row describes as `DESC_NULLS_LAST` post-dates the ship (`20b2c960`, 2026-06-04, against `11d9fbe0`, 2026-06-01). **(b) `DONE-029-0.0.9`, the `scope` row opening #"Strawberry `extensions=[instance]` factory-callable migration"** instructs the reader to replace the deprecated instance form with `extensions=[DjangoOptimizerExtension]` (class) or `extensions=[lambda: DjangoOptimizerExtension()]` (factory callable). `spec-029` Decision 3 forbids **both** as cold-cache-per-request regressions and sanctions only a factory over a construction-site-scoped singleton, and `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form` fails the build on either. That gate reads first-party `.py` only, so the board is the one surface still teaching the banned spelling while the shipped code disagrees with it: `examples/fakeshop/config/schema.py #"extensions=[lambda: _optimizer]"`, with `TODAY.md`, `GOAL.md` and `CHANGELOG.md` matching (287 `extensions=[` sites tree-wide, 184 lambda-form, measured 2026-08-27 excluding `.venv/`, `docs/builder/` and `docs/review/`). **Not violations, do not sweep:** a bare `DjangoDebugExtension` / `DjangoErrorPolicyExtension` / consumer extension class is correct by contract - only the optimizer carries a shared cache - and `tests/test_ci_governance.py`'s planted-corpus strings are the gate's own positive controls. The same card body cites a test module that has never existed, `examples/fakeshop/tests/test_commands.py`, in one `scope` row and one `definition_of_done` row; the command's real coverage is `examples/fakeshop/tests/test_inspect_django_type.py` and `tests/management/test_inspect_django_type.py`. `examples/fakeshop/apps/kanban/tests/test_commands.py` DOES exist and is the false positive a bare `test_commands.py` grep returns - this card's own `DONE-020-0.0.7` `apps.py` bullet cites it legitimately. Reword the migration row to the Decision 3 form, repoint the two citing rows at the two real modules, and in the same edit reword the `definition_of_done` row reading #"replaced with the factory-callable equivalent", since a bare "factory callable" names the construction Decision 3 rejects.
- Two structural defects sit in the spec companion `-terms.csv` surface, one extending a population this card already owns and one a new defect class with no owner. **(a) is more stale `notes` cells** - the column governed by this card's #"Decide whether the `notes` column of a spec's `-terms.csv` is contract text" ruling item and measured for card-id rot by its #"A spec's `-terms.csv` `notes` column carries live card references" sibling; neither names this file. `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv` carries five stale cells and **only two are the card-id kind**: the `DjangoFileType` and `DjangoImageType` rows say the pair "will ship alongside `Upload` in `TODO-ALPHA-028-0.0.11`", where the owner is `DONE-037-0.0.11` (shipped) and card 28 is the ordering card; the other three are the `Upload scalar` row still calling it the next planned scalar, the `DjangoOptimizerExtension` row teaching `extensions=[DjangoOptimizerExtension()]` (the form `spec-029` Decision 3 retired, and the same defect this card's `DONE-029-0.0.9` card-body bullet fixes on the board), and the `Strictness mode` row, a discharged authoring instruction asking that the `strawberry_config` entry be ordered between `Specialized scalar conversions` and `Strictness mode` - where it now sits. The sibling `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv` also carries retired contract vocabulary in the same column, but that half is owned by this card's retired-scalar-vocabulary bullet, which measures it at 3 rows / 4 phrase instances including a spelling no `scalar-only` grep can see; do not measure it twice. **A second, mechanical half of the same column, measured 2026-08-27**: `csv.DictReader`, the parser both readers use, drops everything after the first unquoted comma into its `None` restkey, and `5 of 44` cells in the `spec-029` CSV and `2 of 17` in the `spec-025` CSV truncate today (count rows where the `None` key is non-empty; `spec-030` is `0 of 50` and `spec-046` `0 of 37`, so this is per-file, not universal). The truncation is what reaches the board - the `GlossarySpecMention` row for `spec-029`'s `Meta.nullable_overrides` stores notes ending at "scalar-only" and loses the rest - so quote every cell containing a comma as part of the same edit. **(b) is a different defect class: a MISSING ROW, invisible to the gate by construction rather than by an ungated column.** `DONE-046-0.0.14` authored **8** `docs/GLOSSARY.md` entries at `0.0.14` and `docs/SPECS/appx/spec-046-transport_security-0_0_14-terms.csv` lists none of them. Measured 2026-08-27 by slugging every `##` heading in `docs/GLOSSARY.md` whose body cites `spec-046` and differencing against the CSV's `anchor` column: 10 entries cite it, 8 are absent - `djangographqlview`, `request-body-cap`, `utf-8-wire-contract`, `websocket-consumer-injection-seam`, `websocket-revalidation-window`, `connection-scoped-revocation`, `websocket-host-boundary`, `graphqlrequestbodyboundarymiddleware`. **Eight, not the six or seven a first pass reports**: the spec's own #"and the new terms this card authors" paragraph enumerates seven and omits the Decision 18 middleware entry, which cites `spec-046` like the rest. All 8 carry zero `GlossarySpecMention` rows and zero `CardGlossaryTerm` links, except `request-body-cap`, linked to `DONE-047-0.0.14` because that sibling's CSV cites it - so card 046 links none of the eight entries it created while a sibling links one of them. **The sibling proof that this is an omission, not a convention**: the same difference over the `0.0.14` cohort gives `spec-047` 4 citing entries and 0 absent, its own authored `Execution resource policy` included; `spec-046` is the only member of the cohort with a gap. `scripts/check_spec_glossary.py` cannot see it - `scripts/check_spec_glossary.py::load_terms` reads `term,anchor` only and validates each CSV row forward into `docs/GLOSSARY.md` and the spec body, never asking the reverse question - and it passes `spec-046` today at 37 terms. Two constraints bind the fix: `import_spec_terms::Command._load_rows` raises a `CommandError` on a duplicate `anchor` within one CSV while `check_spec_glossary.py::load_terms` tolerates many terms mapping to one anchor, so the CSV is the stricter reader and every added row needs a distinct anchor (none of the 8 collides with the 37 already there); and `spec-046` carries zero link definitions for all 8 anchors, so adding the rows without also adding reference-style uses and defs - or running `scripts/check_spec_glossary.py --auto-link` - turns that pass into a failure. Fix order: correct (a)'s cells and quote the comma-bearing ones, add (b)'s 8 rows plus their spec links, then re-run `manage.py import_spec_terms` without `--check` to push the corrected cells into `GlossarySpecMention.notes` and the card's `CardGlossaryTerm` links, and regenerate `docs/GLOSSARY.md` and the board. `import_spec_terms --check` compares only the ordered anchor list, so it passes over the truncated notes today and will keep passing after (a) lands - the notes half has no verification at all, which is exactly the ruling this card's `notes`-column item owes.
- `CHANGELOG.md`'s `[0.0.9]` entry for the two nullability-override `Meta` keys is the last uncorrected copy of a sentence its two standing siblings already fixed, and one of its two retired phrases is now outright false. `CHANGELOG.md #"decouple a scalar field's GraphQL nullability"` and the same paragraph's #"scalar-only, and the override flips" both describe the overrides as scalar-scoped, while the shipped boundary is non-relation: `django_strawberry_framework/types/base.py::_validate_nullability_override_targets` rejects relation targets by name and `django_strawberry_framework/types/base.py::_build_annotations` threads the `force_nullable` tri-state into `convert_field_output`, which since `0.0.11` also covers the file/image output objects, so `required_overrides` can force a non-null `DjangoFileType!`. `docs/GLOSSARY.md`'s #"**Non-relation scope.**" paragraph and `docs/README.md #"the scope is non-relation model fields"` already carry the corrected wording, and the `docs/README.md` bullet is a near-word-for-word twin of the CHANGELOG paragraph, so the replacement text does not have to be invented. Re-measured 2026-08-27 by `grep -n -o "scalar field[a-z']*" CHANGELOG.md` plus `grep -n "scalar-only" CHANGELOG.md`: 4 plus 1 occurrences across 3 lines of one file, of which exactly the 2 in this paragraph are in scope. **Do not sweep the other 3**, all in the `[0.0.6]` section beginning `CHANGELOG.md #"Annotation-only scalar field overrides on"`: they name the `Scalar field override semantics` contract, which has its own shipped `docs/GLOSSARY.md` heading and is genuinely scalar-scoped, so they are live vocabulary rather than history to be tolerated. Two siblings diverge on re-derivation: `docs/SPECS/spec-034-permissions-0_0_10.md` no longer carries `scalar-only` anywhere and is DISCHARGED, while `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv` is still live on 3 rows / 4 phrase instances - the `Meta.nullable_overrides` row twice, `Meta.required_overrides` once, plus a fourth spelling on the `Relation handling` row reading "Decision 10 scopes overrides to scalars", which no sweep keyed on `scalar-only` or on the two `Meta.` rows can see. That CSV's `notes` column is loaded into the board DB by `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py`, so the same text sits at three `GlossarySpecMention` rows and the fix is a file edit **plus** re-running that importer, not a file edit alone; this is the retired-vocabulary half of that column and is distinct both from the two existing items asking whether `notes` needs a gate and recording that it carries rotting card references, and from this card's terms-CSV structural bullet, which cedes the `spec-029` vocabulary rows here and keeps the `spec-025` stale cells, the missing `spec-046` rows and the comma-truncation defect. One deliberate keep: `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md #"Claim this Decision may no longer make: that the overrides are scalar-only"` states the retirement on purpose and must survive verbatim.
- Two calls this card cannot make for itself, one a ruling and one a correction the ruling request turned out to be masking. **The ruling.** `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` DoD item 15 requires the board to carry a Done body pinned verbatim in that spec's `## Doc updates` section - a 2,348-character blockquote - and closes #"so this spec pins the body, not the number", but `KANBAN.md` is rendered from `CardItem` rows by `scripts/build_kanban_md.py`, so there is no body to pin, only rows. Measured by ORM 2026-08-27 the card carries 2 items totalling 292 characters, and `grep -rc "Past-tense Done body" docs/SPECS/*.md` puts the same pattern in 6 archived specs (`spec-020`, `spec-021`, `spec-022`, `spec-025`, `spec-027`, `spec-028`) whose Done cards measure 4/1318, 3/729, 4/1247, 2/292, 4/1227 and 10/5854 items/characters - six shipped specs each carrying a DoD item that reads as unmet. Option one, strike the verbatim pin from all six and reduce item 15 to what a spec can own (the card is Done, its rows name the spec by structured filename): the six DoDs become honest, and nothing downstream moves because `docs/SPECS/NEXT.md` already instructs a spec author that `KANBAN.md` is generated and to edit the database. Option two, keep the blockquotes as a record of intended-at-ship wording and add one clause to each saying the board renders rows and the pin is historical: nothing is deleted, but six DoD items stay permanently unsatisfiable and every future reconciliation re-grades them. Neither option is a sweep's to assume. **The correction.** The competing-version-bump-policy question dissolves on re-derivation: `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md #"the version bump belongs to the **joint cut**"` and `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md #"The version bump that closes the cut belongs to the last card to ship in it"` state one rule at two levels of detail, and `docs/GLOSSARY.md`'s `## Joint version cut` entry already unifies them - the bump is #"owned by the **last** card to land", "the joint cut - never by an individual card's slices". Re-measured 2026-08-27, 37 files cite that anchor, every spec from `spec-041` forward defers to it rather than restating the rule, `spec-050` Decision 12 and `spec-051` Decision 11 both cite it and both name which card lands last and why, and no site anywhere states the rejected form. What is genuinely broken is the rule's membership list, not its ownership clause: `pyproject.toml` now carries `dynamic = ["version"]` with `[tool.hatch.version]` reading `__version__`, so the quintet's first member does not exist, yet `docs/GLOSSARY.md #"the version quintet: "` still leads with `[project].version`. 14 forward-looking prose sites across 7 files still instruct a future worker to move it - the glossary entry, `CONTRIBUTING.md #"Bump the version in both places before tagging a release"`, `docs/SPECS/NEXT.md`, and the Slice-5 text of `spec-055` - the sibling Slice-5 sites in `spec-050`, `spec-051` and `spec-053` were corrected to the triplet at the 2026-08-29 spec claims audit, shrinking the measured 14-site population; the survivors span multiple spellings (`spec-055` writes "`pyproject.toml` `version`", invisible to a `[project].version` grep). The board half is a DB edit plus regenerate: two `CardItem` rows name `pyproject.toml` in a version-bump line, two more list it as touched by one, and the `Release readiness checklist` `BoardDoc` opens by asserting a `pyproject.toml`-to-`__init__.py` parity that no longer has two sides. `docs/GLOSSARY.md` is DB-generated, so its half is a glossary-DB edit plus regenerate. This is the prose population, not the gate question the existing `AGENTS.md` rule 31 item settles - that item scopes itself to whether a gate is owed and concludes none is. **Do not sweep** the archived `0.0.13` and `0.0.14` specs whose Slice-5 text describes a cut that already happened; those are correct in their own tense.
- `docs/TREE.md` renders `__init__.py` in its three upstream reference trees and in none of its own four, and states nowhere that this is deliberate. Re-measured 2026-08-27, `grep -c "__init__" docs/TREE.md` returns 25 occurrences, all above the generator delimiter `docs/TREE.md #"## django_strawberry_framework (current on-disk layout)"` and 0 below it - every one is in the hand-captured `graphene_django` / `strawberry_django` / `django_graphene_filters` trees, which keep the file. The omission below the delimiter is real and load-bearing rather than cosmetic: `scripts/build_tree_md.py` defines `IGNORED_TREE_FILENAMES = frozenset({"__init__.py"})`, and `scripts/build_tree_md.py::folder_description` reads that same file's docstring as the containing **directory's** comment and fails the render outright when it is missing, so 51 `__init__.py` files across the three rendered roots (15 under `django_strawberry_framework/`, 17 under `tests/`, 19 under `examples/fakeshop/`) are not dropped but promoted one level up into the line that describes their package. A reader has no way to learn this from the document: the file's head already carries a `docs/TREE.md #"Filters applied:"` sentence enumerating what the upstream trees exclude, and that list does not mention `__init__.py`, so the contrast makes the framework-side omission read as an accident rather than a rule. Fix: one sentence saying that a package's `__init__.py` is rendered as its directory's description line rather than as a leaf, and that a directory without one fails the render. Two placements with different costs - the file head above the delimiter is hand-maintained and takes a plain edit, while both generated section preambles are written by `scripts/build_tree_md.py` (the `Source:` line and the target-layout paragraph), so putting the sentence there is a script change plus a regenerate. Nothing here is a hand edit of the generated tail. Pairs with this card's `docs/TREE.md` optimizer-entries item, which is the same docstring-plus-regenerate discipline on the rendered body.
- Two durable citations point at nothing, and neither is reachable by any gate. First, the board-DB `Reference` doc titled `Decision: FilterSet subclassing unsupported` ends "Ref: spec-021 pre-merge review M-filters-3 / H-filters-3", where `spec-021` means the pre-renumber filters spec - proven by the git rename record, `docs/spec-021-filters-0_0_8.md` to `docs/SPECS/spec-027-filters-0_0_8.md` (with its `-terms.csv` renamed alongside), not inferred from the topic - while today's `spec-021` is the unrelated `apps.py` / `AppConfig` spec, so the reference currently resolves to a real file about the wrong subject, the worst failure mode available. The row is doubly dangling: `M-filters-3` and `H-filters-3` are defined in no document at all, their only other tree occurrence being a docstring on the subclassing-rejection test in `tests/filters/test_factories.py`. Fix is an ORM edit on that `BoardDoc` plus `scripts/build_kanban_md.py` and `scripts/build_kanban_html.py`; the choice is whether to repoint the stem at `spec-027-filters-0_0_8.md` or to drop the trailing `Ref:` line entirely, since the decision's own body already states the rationale and the id set it cites has no definition to reach. Second, and a maintainer ruling rather than a fix: whether `AGENTS.md` rule 27 governs `CHANGELOG.md` at all. Measured 2026-08-27 that file carries 0 raw `path:NN` references, 3 compliant `path::Symbol` citations, 14 dotted package import paths, and 33 bare `` `path.py` `` references with neither symbol nor `#"substring"` pinpoint. `scripts/check_citations.py` sets `MARKDOWN_SOURCES = ("KANBAN.md",)` and puts `docs/` out of scope, so nothing checks `CHANGELOG.md` in either direction. The dotted forms are the crux and cannot be swept mechanically, because the same spelling means two different things: `django_strawberry_framework.testing` in a release note is a consumer import path that rule 27's `path::Symbol` shape would corrupt, while a private helper named inside `optimizer/plans.py` is a source reference rule 27 does cover. Option one, `CHANGELOG.md` joins the gate's markdown corpus under the same real-rot-only rule `KANBAN.md` gets, with dotted package paths declared user-facing API and exempt: 3 citations start being verified, the 33 bare file references need a decision of their own, and the exemption has to be expressed in the script rather than in prose. Option two, `CHANGELOG.md` stays out of scope as a release record rather than a source-reference surface: nothing changes today, and the question stops being re-raised each cycle only if the exclusion is written down. **Do not treat the 14 dotted import paths as violations** under either option without the exemption being settled first.
- Five Done cards carry 14 unticked `definition_of_done` items whose substance verifiably landed, so the boxes are bookkeeping rather than open obligations. Measured by ORM 2026-08-27 across every `done` card: card 35 (2 items), card 44 (6), card 46 (1), card 47 (3), card 49 (2). **Card 35's two must stay unticked** - both open "**[DEFERRED to the abstract-return optimizer entry card**" and are deliberate deferral markers, not incomplete work; the sweep population is the other 12. Card 46's single box is the one worth stating precisely, because it is the only one whose verification is split: it reads "Full suite green at 100% coverage (maintainer/CI gate); ruff + trailing-comma clean; manage.py check + makemigrations --check clean", and its first three clauses are gated on every push and PR by `.github/workflows/django.yml` (which runs `ruff check`, `ruff format --check`, `scripts/check_trailing_commas.py --check` and owns the `fail_under = 100` node) while its last two are gated by nothing - neither that workflow nor `.pre-commit-config.yaml` runs either Django management check. Re-derived rather than assumed: `manage.py makemigrations --check --dry-run` reports "No changes detected" and `manage.py check` reports "System check identified no issues (0 silenced)" at HEAD, so every clause holds. Fix is an ORM edit setting `is_complete=True` on the 12 non-deferral items plus `scripts/build_kanban_md.py` and `scripts/build_kanban_html.py`; `CardItem` also carries `verified_at` / `verified_by` / `verification_kind`, all null on every one of the 14, so the tick should record which instrument established it rather than land as a bare boolean - and for card 46's box that instrument is CI for three clauses and a manual run for two, which is itself the argument for either adding the two management checks to the hygiene job or narrowing the box to what a gate can prove. Note the renderers do not read `is_complete` for these rows' display state, so the tick is a data correction rather than a visible one; this pairs with this card's existing item recording that the `Verified in upstream` section's per-bullet completion state is unpopulated board-wide.
- `docs/SPECS/spec-017-deferred_scalars-0_0_6.md`'s `## Non-goals` never excludes PostgreSQL range fields, leaving the one spec that owned the deferred-scalar boundary silent on the field class an incoming `graphene-django` schema is most likely to carry across it. Re-derived 2026-08-28 rather than taken from the finding's own wording: that section carries **nine** bullets of which **four** are postgres-scoped (no multi-dimensional `ArrayField`; no outer `choices` on `ArrayField` / `HStoreField`; no dedicated `HStore` scalar; no postgres driver in dev dependencies), not the seven the finding claims, and `grep -c RangeField docs/SPECS/spec-017-deferred_scalars-0_0_6.md` returns 0 - the spec's four `range` hits are all the `BigInt` 32-bit / int64 sense. The behavior is already true in code and only the record is missing: `django_strawberry_framework/types/converters.py` soft-imports `ArrayField` and `HStoreField` only, and every other `django.contrib.postgres.fields` class falls through `django_strawberry_framework/types/converters.py::scalar_for_field` to `ConfigurationError`. The owed bullet states the exclusion and names the recourse - a consumer-registered scalar for the range type, the same escape hatch every other deferred scalar uses - and grounds it in the contract rather than in effort: `graphene-django` maps every range field to `List(base)`, and a two-element list cannot round-trip a two-ended interval's per-end inclusivity. Spell the postgres class by its full dotted path in the bullet, because the package already ships an unrelated `django_strawberry_framework/filters/base.py::RangeField` (the `django_filters` form field behind `RangeFilter`) and a bare `RangeField` greps to the filter surface instead. Text edit in one archived spec; no code, no glossary, no board row.
- No standing document says where dataloaders sit, so a migrant arriving from `graphene-django`'s N+1 chapter cannot tell whether they are supported here, discouraged, or replaced. Measured 2026-08-28: a case-insensitive `dataloader` grep returns 0 in `docs/GLOSSARY.md`, `README.md`, `docs/README.md`, `CHANGELOG.md`, `TODAY.md`, `BACKLOG.md`, `docs/TREE.md` and `KANBAN.md` - eight for eight - and the only occurrence anywhere in the tree is a one-clause follow-up aside in `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md`. What is owed is two facts and not a recommendation: `strawberry.dataloader.DataLoader` ships with the engine and is available unchanged (nothing in this package wraps, patches or competes with it - import-checked in the project venv 2026-08-28), and this package's own answer to N+1 is the optimizer plus strictness, so a consumer reaches for a dataloader only where the optimizer has no plan to make. Two homes, one sentence each: a clause on the `docs/GLOSSARY.md` `## Strictness mode` entry, which already owns the N+1-detection vocabulary and is DB-generated - edit the fakeshop glossary app's `GlossaryTerm.body` and re-render with `scripts/build_glossary_md.py`, never hand-edit - and a line in `README.md`'s `## Is this for you?` section beside the existing `Strictness / N+1 detection` bullet, which is a plain text edit. Rides the same ORM edit and render as this card's other glossary items. The `0.1.8` migration guides get a one-line mention of the same fact, but that half is the migration-guides card's and explicitly not this one's.
- `README.md` never tells a migrant that unregistered relation targets fail loudly, and that is the first thing many of them will hit: `graphene-django` silently drops the field and `strawberry-graphql-django` falls back to a `DjangoModelType { pk }`, while this package raises at `finalize_django_types()` with an error naming source model, source field and target model (`django_strawberry_framework/types/finalizer.py::_format_unresolved_targets_error`). Re-derived 2026-08-28, and the finding narrows in the process: the FACT is already documented twice - `docs/GLOSSARY.md`'s `## Definition-order independence` entry states the error and its most common cause, and `docs/README.md` #"The most common failure mode is forgetting to import a module" states the same beside its finalization instruction - so what is missing is not the behavior but its MIGRATION framing, which exists in no file. The note is one or two sentences in `README.md`'s `## Is this for you?` section, where the two `Coming from ...?` paragraphs already address exactly this reader and neither mentions it. It has to name what each upstream does instead, because "we raise here" is only actionable to someone who knows their old schema was quietly dropping the field. Deliberately minimal and deliberately early: the full guides are the migration-and-adoption-guides card at `0.1.8` and are NOT this card's scope, and the beta-claim carve-out sentence belongs to the beta release card. Plain text edit, one file.
- `docs/GLOSSARY.md`'s `## Choice enum generation` entry understates a shipped capability: it opens "`CharField` / `TextField` with `choices=...` generates a Strawberry enum", while the code enums ANY field that declares choices. Verified 2026-08-28 in `django_strawberry_framework/types/converters.py::convert_scalar`, which resolves the column through `django_strawberry_framework/types/converters.py::scalar_for_field` and then substitutes `django_strawberry_framework/types/converters.py::convert_choices_to_enum` whenever `django_strawberry_framework/types/converters.py::_field_has_choices` is true - there is no field-class test anywhere on that path. The corrected sentence needs the two real exclusions, which are rejections rather than pass-throughs: outer `choices` on an `ArrayField` and on an `HStoreField` each raise `ConfigurationError` (ambiguous at the GraphQL boundary; declare `choices` on `base_field` for an element-level enum). Integer choices work - `_sanitize_member_name` casts to `str`, so an `IntegerChoices` value becomes `MEMBER_1`, pinned at `tests/types/test_converters.py::test_choice_member_name_sanitization` - which makes us STRICTER than `strawberry-graphql-django`, which skips them, and the current wording surrenders that parity claim in the one document the `0.1.0` parity audit reads. Record the evidence boundary while correcting it: no example model carries an integer-choices column, so the live `/graphql/` tier does not pin this and the support rests on the package test plus the audit's live probe. DB-generated - edit the fakeshop glossary app's `GlossaryTerm.body` and re-render with `scripts/build_glossary_md.py`, never hand-edit; rides the same ORM edit and render as this card's other glossary items.
- `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`'s `## Choice field enum generation` section rejects the label-based alternative on a false premise: its opening sentence says `graphene-django` and `strawberry-graphql-django` sanitize labels, and both in fact sanitize VALUES, exactly as we do. Verified directly against the reference checkout 2026-08-28 - `graphene_django/converter.py::get_choices` iterates `(value, help_text)` pairs and builds each member name with `convert_choice_name(value)`, using the label only as the member description. Only the premise is wrong and the argument that survives it must stay intact: labels are display strings consumers translate or restyle, coupling the schema to them is fragile, and the `MEMBER_<digit>` prefix is the known and accepted cost. So the fix rewrites the attribution, not the verdict - the alternative was weighed on its own merits, and the value path is PARITY with both upstreams rather than a divergence from them. It is load-bearing in exactly that direction: anyone reading this rationale during the `0.1.0` parity audit currently reads a divergence where none exists, and would file one. Text edit in one archived rationale companion; the spec's own `## Choice field enum generation` section is correct and needs no change.
- `KANBAN.md`'s `### Still not implemented` list names `permissions.py` among the Layer 3 subsystems that are "still planned only", and it shipped at `0.0.10` (`DONE-034-0.0.10`, `docs/SPECS/spec-034-permissions-0_0_10.md`): `django_strawberry_framework/permissions.py` is on disk, root-exported and glossary-documented. Two corrections to the finding's own routing before it is actioned. FIRST, this is not a `CardItem`. Located 2026-08-28 by an ORM sweep over every text column in the kanban app, the sentence lives in `BoardDoc` pk 4 (`namespace="kanban"`, `key="snapshot"`, kind `Reference`, title `Snapshot`), so the edit is `BoardDoc.body` plus a `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py` regenerate - a `CardItem`-scoped sweep returns nothing here and reads as already-fixed. SECOND, only ONE of that bullet's four entries is wrong: `aggregates/` and `fieldset.py` are genuinely absent, and `utils/queryset.py` is a deliberate near-miss a sweep must not "fix" - it is `BACKLOG.md`'s item-36 "promote embedded helpers to `utils/queryset.py` only when a second subsystem needs them", a planned singular module, NOT a typo for the shipped `django_strawberry_framework/utils/querysets.py`. Deleting the one line leaves the other three correct.
- `Meta.nested_fields` and `NestedSerializerConfig` are shipped, root-exported, live-tested surface with zero presence in any standing document. Measured 2026-08-28: a combined `nested_fields` / `NestedSerializerConfig` grep returns 0 in `docs/GLOSSARY.md`, `README.md`, `docs/README.md`, `CHANGELOG.md`, `TODAY.md`, `BACKLOG.md`, `docs/TREE.md` and `KANBAN.md` - eight for eight, so this is ABSENT rather than merely not-lookupable, which is the distinction this card's `Meta.cursor_field` bullet had to make and the reason that one is a decision and this one is not. The surface is real: `django_strawberry_framework/rest_framework/inputs.py::NestedSerializerConfig` is the explicit per-field opt-in for nested serializer inputs (`Meta.nested_fields = {"shelves": NestedSerializerConfig()}`), it is exported from the package root through the lazy attribute map in `django_strawberry_framework/__init__.py`, a nested field NOT named in the map still fails loud, and the whole path is pinned over `/graphql/` by `examples/fakeshop/test_query/test_library_api.py::test_create_branch_with_nested_shelves_over_http` beside its hidden-target and validation-path siblings. What is owed is a `## Meta.nested_fields` glossary heading - every other `Meta` key has one - covering the opt-in, the fail-loud default for an un-named nested field, and the contract that the consumer's own serializer `create()` performs the nested write (the framework never auto-saves the relation). DB-generated: add the `GlossaryTerm` row and re-render with `scripts/build_glossary_md.py`, never hand-edit. The changelog half is owed too and is not a judgement call - the feature shipped at `0.0.13` under `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`, and that release's `## [0.0.13]` entry describes `SerializerMutation` without mentioning nested inputs at all.
- Two standing records disagree about top-level batch create / update / delete, and they differ in both the surface named and the disposition. `docs/SPECS/spec-036-mutations-0_0_11.md` #"Nested writes / bulk mutations" defers the shape as "not on the alpha roadmap", and its parenthetical attributes batch create to strawberry-django's `ParsedObject` / `ParsedObjectList` connect-create-disconnect family - that is, to NESTED writes. The surface actually at issue is a different and top-level one: `strawberry_django/mutations/fields.py::DjangoCreateMutation.resolver` accepts a `list[Input]` argument on the mutation field itself, verified against the reference checkout 2026-08-28. Its verdict is a permanent refusal, not a deferral, so the spec currently reads as though the surface is merely waiting for a later release. The refusal: a list argument multiplies the per-row attestation and locking contract while the pinned `node` / `result` + `errors` payload has no shape in which to report per-row outcomes, so partial success would be unreportable. The answer is serial top-level mutation fields, which the GraphQL spec already executes in order and which `django_strawberry_framework/schema.py::DjangoSchema` gives an independent transaction each, plus the carded mutation idempotency keys for safe retry. What is owed: split the two surfaces in that out-of-scope entry and state the top-level one as refused.
- `docs/SPECS/spec-034-permissions-0_0_10.md` routes a capability to a `BACKLOG.md` home that was never created, so the package's answer to object-level permission backends is recorded nowhere. That spec's out-of-scope entry #"Object-level permission backends (guardian-style) and per-field permission" says post-`1.0.0` differentiation would go through `BACKLOG.md`; measured 2026-08-28, a case-insensitive `guardian` grep over `BACKLOG.md` returns 0, so the pointer resolves to nothing. The missing record is a composition note rather than a refusal of the need: binding a specific third-party permission backend into framework queryset construction would couple the package to that backend's table layout, and the composition point is already public - a consumer calls `get_objects_for_user(info.context.request.user, "app.view_thing", queryset)` from the type's own `get_queryset`, which composes with filters, orders, connections, node refetch and the cascade because every one of them runs through the same hardened visibility boundary. Decide the home first, then write it once: either create the `BACKLOG.md` row that spec promises, or restate the spec entry so it stops pointing at a row that does not exist.
- `docs/SPECS/spec-038-form_mutations-0_0_12.md` #"### Reference-package parity checkpoint" carries no verdict on `graphene_django/forms/types.py::DjangoFormInputObjectType`, the one graphene-django forms surface that otherwise-thorough table omits. Measured 2026-08-28: `DjangoFormInputObjectType` greps to 0 in that spec, so the omission is silent rather than deferred, and a reader auditing forms parity against it finds a gap with no disposition. The verdict that belongs in the table is a refusal, and the card's own design already supplies the reasoning: a standalone form-derived input object exists upstream so a hand-written Relay mutation can borrow a form's shape as a nested `data:` argument, which is a workaround for not having a form mutation flavor rather than a capability of one. Here `Meta.form_class` on `DjangoModelFormMutation` / `DjangoFormMutation` generates inputs bound to the mutation that validates them. Add the row so the absence reads as decided rather than missed.
- The node-identity refusal is recorded for graphene-django's spelling and not for strawberry-graphql-django's, so half of it is invisible to a migrant searching the other name. Measured 2026-08-28: `lookup_field` resolves across `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` at five sites including its out-of-scope entry, while a combined `key_attr` / `DEFAULT_PK_FIELD_NAME` grep over `docs/`, `BACKLOG.md`, `KANBAN.md` and `README.md` returns 0. Those are strawberry-graphql-django's spelling of the same idea - `strawberry_django/settings.py` `DEFAULT_PK_FIELD_NAME` plus `key_attr` on the relay node - and one argument rejects both: resolving a global ID against a configurable non-pk column makes node identity a function of settings, so the same opaque ID then means different rows in two deployments of the same schema. The answer is the pk, with a consumer-authored resolver where a natural key must be addressable. Add the second spelling beside the recorded one; a verdict that names only one upstream's word for a surface both ship is a half-recorded verdict.
- BACKLOG.md's 'Moved out of this file' section states items 36/37/38 'move to `AGENTS.md` / `CONTRIBUTING.md`' (public-surface promotion discipline; shared queryset introspection helpers - note the shipped module is `utils/querysets.py`, plural, not the `utils/queryset.py` the note names; layered manual relation override test policy). Verified 2026-08-29: none of the three rules is present in either target file - the transfer never landed. Land the three rules (or record where each actually belongs) and correct the BACKLOG note.
- Twelve live-source `(line NNN)` self-citations and the two `cookbook line(s)` sites have no owning card, because this card's line-number-citation item explicitly routes them to "a live-code batch, not a documentation pass" and no batch names them. Measured 2026-09-01 by the spec-035 residual cycle over the 433-file `.py` corpus with a per-file `re.sub(r"\s+", " ", text)` flatten (the only instrument that survives both a wrap and a `#` comment-continuation): `grep -rnoE '\(lines? [0-9]+' --include='*.py'` returns **9 in `tests/types/test_resolvers.py`** (`:1797, :1802, :1808, :1817, :1828, :1908, :1915, :1920, :1931`) and **3 in `tests/test_exceptions.py`** (`:459, :464, :481`), plus `tests/orders/test_sets.py:169` #"per cookbook line 280" and `tests/orders/test_factories.py:250` #"cookbook lines 124-130" whose upstream-prior-art ruling this card already carries. These cite a live package source file's own line numbers, which `AGENTS.md` rule 27 wants as `path::Symbol` or `#"substring"`, and they are actively rotting: `types/resolvers.py` has moved under at least three of them. **Routing rule, not a sweep:** each site folds into whichever `TODO-ALPHA-053-0.0.15` WP batch legitimately opens its file, and only the residue no batch opens belongs to this card - the same boundary this card's spec-016 rule-27 item already draws. Precedent for the fix shape: the spec-035 residual cycle closed one citation of exactly this class in `tests/types/test_resolvers.py` (`git show 8c05f7fc:docs/builder/bld-035-final.md` D12) because that cycle already owned the file, replacing the line number with a `path::Symbol #"substring"` pair and proving the anchor resolves exactly once - do that, never a bare `path:NN` to `path::Symbol` mechanical rewrite, since three of these targets have moved and the symbol must be re-read against the live body first.
- A `path::Symbol` citation that names a method without its owning class is legal to `scripts/check_citations.py` and ambiguous to a reader, and the convention question must be settled before this card's source-symbol-citation checker item can decide what to flag. **The population has three grammars and any single-grammar instrument under-reports it** - re-derived 2026-09-01 by the spec-035 residual cycle by `ast` classification of every package `def` (top-level function / class method / nested closure) rather than by grep, over one spec/rationale pair. (a) The inline ``path.py::method`` form: **9** in `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` (`extension.py::_build_cache_key` 4, `extension.py::_optimize` 4 counting the 1 spelled `optimizer/extension.py::_optimize`, and `types/resolvers.py::forward_resolver` 1 - that last one is a **nested closure** inside `types/resolvers.py::_make_relation_resolver`, so no class qualifier would even fix it) and **3** in `docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md`. (b) The markdown reference-link form ``[`method`][label]``, which carries the path in the link definition and the class nowhere: **6** in the spec and **1** in the companion, every one of them `_optimize`. (c) The bare prose span naming a method on an instance rather than a class (`registry.model_for_type` 5 / `registry.definition_for_graphql_name` 1 in the spec, 2 / 1 in the companion): **6** and **3** - a distinct defect class, since these are qualified by an object name, not unqualified. Totals **21** and **7**. **The 15 / 6 / 5 figures already recorded in `git show 8c05f7fc:docs/builder/bld-035-final.md` D10 reproduce exactly** - they are (a) plus (c), and the 5 is the raw count of the fully-qualified `DjangoOptimizerExtension._optimize` the spec *also* uses, 4 of them with a ``path.py::`` prefix; grammar (b) is the only addition, and it is the majority of the companion's sites. That the same document spells both forms is the strongest argument this is a convention call and not a per-document fix. Nothing here is rotten - the gate resolves every one of these spellings - so the cost is purely that a class-scoped rename is checkable against the qualified form and not the bare one. **Decide the rule, then measure; do not scale this figure** - it is one pair out of 60-plus archived specs, and the grammar decomposition, not the total, is what transfers. If the ruling is "qualify always", the checker item gains a warning class and grammar (b) needs a resolver that reads the link definition; if it is "bare is legitimate where the module-level name is unique", write the exemption into the script rather than into prose, or every later cycle re-raises it. Either way the nested-closure site and the instance-qualified prose spans need their own rulings, because neither is fixed by adding a class name.

#### Definition of done

- [ ] Every `Scope` bullet on this card is either discharged in the tree or explicitly deferred onto a named card with a recorded reason. Modeled on the beta release card's parity-audit gate: `DONE` or explicitly deferred, never silently dropped.
- [ ] Each discharged bullet's claim is re-derived at close rather than trusted from the bullet text: a finding's grep vocabulary is not its population, and several bullets here record their own counting-basis traps.
- [ ] `docs/GLOSSARY.md` and `docs/TREE.md` are regenerated from their generators (never hand-edited) after the sweeps land, and `KANBAN.md` / `KANBAN.html` are regenerated from the board DB.
- [ ] `scripts/check_citations.py`, `scripts/check_spec_glossary.py`, and `scripts/check_trailing_commas.py --check` pass over every file the card touched.

#### Files likely touched

- `docs/SPECS/*.md` and `docs/SPECS/appx/*` - the archived-spec cohort carrying the stale claims
- `docs/GLOSSARY.md`, `docs/TREE.md` - both generated; regenerate, never hand-edit
- `CHANGELOG.md`, `README.md`, `docs/README.md`, `BACKLOG.md`, `CONTRIBUTING.md`
- `scripts/` - the spec/rationale consistency checker several bullets scope
- `examples/fakeshop/db.sqlite3` - the board-DB half of the card-text and spec-path sweeps

#### Why it matters

- The alpha line accumulated 48 documentation-consistency findings between 2026-08-05 and 2026-08-25, each one deferred onto the beta release card by a residual reconciliation cycle. That card's `Definition of done` is release mechanics - version bump, changelog promotion, matrix pass, tag, publish - and not one of its eight items gates a single finding, so at cut time the whole population would have been dropped silently rather than deferred deliberately.
- `AGENTS.md` rule 5 forbids defer-the-real-fix sequencing, and an ungated bullet parked on a release card is exactly that shape. Gating them from inside the release card would keep a documentation sweep inside a release cut; this card is the root-cause fix - the debt owns a card, owns a gate, and blocks the `0.1.0` cut through a dependency edge instead of through prose.

#### Open question

- Whether `scripts/archive_spec.py` should exist, and whether it warrants its own card rather than riding this one. NEXT.md Step 8 is ~120 lines of hand-run steps that has already produced two standing-doc defects and 14 orphan-row pairs. Three directions of cross-reference rewriting, a group-relocation obligation invisible to every checker, and a DB sync inseparable from the physical move are all mechanizable.

#### Note

- Documentation-debt card, no package behavior: nothing in `django_strawberry_framework/` changes shape here beyond comment and docstring citations. Split off the beta release card on 2026-08-25, when that card's `Scope` had reached 48 bullets / 74,148 characters against a `Definition of done` that gated none of them.
- Process questions carried out of the retired builder artifacts. These are BUILD-flow questions, not release work, and several may be moot once that flow is replaced - re-home or drop them rather than treating them as this card's scope. (1) Whether the weakly-pinned failability rule is applied literally: twelve boundaries from one round fail the 0-or-1-row test, of which the reviewer judged four to deserve a second row on merit and six adequate on merit, so a literal reading re-loops all twelve; and the rule says "never a recorded exception" while a review artifact recorded one, so the rule needs either a narrow carve-out or that entry becomes revision-needed. (2) Whether the WebSocket-revocation design owes a hot-path number: it holds one connection-local lock through the outbound send, which meets the hot-path definition and which the spec itself calls a hot path; either declare it and re-loop for a before/after number (`_instrument_revalidation`'s `probe.reads` is already the instrument) or waive it explicitly. (3) `AGENTS.md:15` mandates repo-wide `ruff format` / `ruff check --fix` while all four worker role files tell workers to scope them to their own files, because this tree carries concurrent uncommitted work that a repo-wide write-mode run reformats; the role files defer to `AGENTS.md` on conflict, so the scoping instruction is inert until reconciled. Six-plus passes have raised it. (4) Whether a `bld-custodian-*` artifact name is admissible under the build-artifact naming rule. (5) Whether "a downstream doc more accurate than the spec means the contract moved" becomes a first-class integration sweep step: the tell fired four times in one card and located two of nine corrections before an auditor did. (6) Whether `AGENTS.md` rule 27's raw-`path:NN` exemption should name `docs/builder/build-*.md` alongside the per-cycle scratchpads it already lists. The rule exempts artifacts "that close with their cycle" and a committed build plan does not close, but 9 of the 11 plans in `docs/builder/` carry the shape anyway - measured 2026-08-14 by `grep -Ec '[A-Za-z0-9_/.-]+[.](py|md|toml|cfg|yaml|yml):[0-9]+'` over `docs/builder/build-*.md`, with only `build-045-visibility_boundary-0_0_14.md` and `build-048-secure_output_defaults-0_0_17.md` at zero. Either the exemption widens or nine committed files are in violation; both readings are defensible and neither is a sweep's to assume. (7) Whether a durable figure must name the commit it was measured at, and whether it was measured against committed or working-tree state. Escalated by the spec-007 residual cycle's second review round and never acted on. (8) That cycle's own answer to (7), offered as the candidate rule: **a quantifier is a measurement, so only the command that produced it may write it - and for a historical quantifier that command names a commit, not the working tree.** It is proposed against a measured population - eleven passes of one cycle produced ten instances of a single defect class, an unmeasured quantifier in durable prose, and the class mutated each time a catching discipline closed its previous form: bare numbers first, then "only"-shaped universals once numbers were being re-derived, then historical absolutes once present-tense universals were being grepped. A present-tense grep cannot test a past-tense claim, which is how that cycle's one High-severity finding arrived. The class has already been found independently on the neighbouring boundary-hardening card, whose `types/base.py::_format_unknown_fields_error` item records that "every defect in this item's own history was a numeral standing in for a population" - two cycles reaching the same rule by different routes is the argument for stating it once in `BUILD.md` rather than a third time in a card. Corpus-ratchet bound like every entry here, and the ratchet is the live objection: this note is already the longest on the board, so a rule that lands as more prose in the same place is the thing it warns against.
- Two spec omissions in the WebSocket revalidation decision, each a one-clause addition whenever a pass legitimately opens it. Neither makes anything in the spec false. (1) Why the last-validated timestamp lives on the ASGI `scope` rather than beside the lock and the flag on the consumer instance is stated nowhere: `consumers.py:209-214`'s comment on `_REVALIDATED_AT_SCOPE_KEY` explains only the key's collision-safe namespacing, and neither the spec nor the rationale gives a reason. It belongs to whoever decided it. (2) How the outbound gate reaches the consumer's lock is nowhere stated; the two hops are `websocket.ws_consumer` (the adapter seam) and `handler.view` (admission), and `ws_consumer` appears in the spec zero times.
- Deliberate no-ops, recorded so a future sweep neither reads them as live claims nor "fixes" them. The closed `docs/review/`, `docs/dry/` and `docs/bug_hunt/` scratchpads still assert the retired "UTF-16 succeeds" contract - they are closed per-cycle records, leave them. The revalidation DRY bullet prices the delegates by `await` count in a way that is true on the natural reading but not literally. The implementation-plan row reading "the adapter-level outbound-frame gate, *its* connection-local lock and *its* one close code" states no ownership location, so it is not false but wants one word if a later pass touches the table. The rationale's Decision 19 historical block still contains "only a factory" on purpose, as the prior spec wording. Two spec phrases describing shipped `0.0.14` behaviour ("This is the only new refusal", "previously a Channels-routed deployment never reached that adapter at") were ruled no-change and are not history-narration defects. One more deliberate no-op, from the spec-007 residual cycle. The "three-minute path" phrasing that survives in this board and in the `KANBAN.html` payload is a render of the `0.0.4` onboarding-docs card's own `CardItem`, and it is accurate history: `docs/README.md` carried a `## Three-minute path` heading, added and deleted the same day by that card's own commits `83c25963` and `3a4d40b7`. Editing the board row would falsify a correct record of what the card did. Recorded because the phrase reads like drift to every sweep that meets it - the reconciled `spec-007-onboarding_docs_spec_consolidation-0_0_4.md` and its rationale companion both name only sections that exist, which leaves the board row as the sole surviving mention. One more, from the spec-013 residual cycle: `docs/builder/DONE/build-007-onboarding_docs_spec_consolidation-0_0_4.md`'s byte ranking names "spec-013 (1,669 bytes)" where the reconciled stub now measures 5,739 bytes - a closed cycle's dated measurement, correct at its commit; leave it. One more, from the spec-015 residual cycle (2026-08-16): the `## Slice checklist` boxes in `docs/SPECS/spec-015-relay_interfaces-0_0_5.md` are all `- [ ]` and **must stay that way**. The spec is archived and shipped for `DONE-015-0.0.5`; its `Status:` line is the source of truth for shipped state and the checklist is preserved as the historical build sequence, so unticked boxes on a shipped spec are the correct rendering rather than an unfinished cycle. That cycle deliberately did not tick them. The same reading applies to every archived spec carrying a slice checklist - do not sweep them.
- Three further deliberate no-ops, recorded so a sweep does not "fix" them. `docs/README.md`'s counted-body section was examined for a clause about body-reading project middleware and ruled no-change: the decision does not require it, `views.py::_run_after_csrf_check` already carries it in bold for a code reader, and the counted half of that section states its own honest boundary, so the code docstring is the authoritative statement. Separately, the revalidation DRY note prices the WebSocket delegates by `await` count in a way that is true on the natural reading but not literally - each handler body has two `await` expressions and the adapter's `send_json` has two `await`s and two `super()` references. Third: `docs/GLOSSARY.md`'s `## OrderSet` entry carries no position-side-channel note while its `## RelatedOrder` sibling carries #"Position-side-channel note:", and the asymmetry is correct. `docs/SPECS/spec-028-orders-0_0_8.md` Decision 8 step 4 once claimed both entries called the leak out; the reconciliation measured that claim false in exactly one of its two subjects and corrected the spec down to name `RelatedOrder` alone, on the ground that the `RelatedOrder` declaration is what creates the exposure so the warning sits where a consumer writes one. The leak the Decision describes is relation-shaped throughout - ordering visible parent rows by a hidden related column, defended by the parent-side `check_<branch>_permission` gate fired through active-branch double-dispatch - so a parallel note on `OrderSet` would assert a contract the spec deliberately declines to assert. Recorded because the gap reads like an omission to every sweep that meets it, and because that same cycle's own pre-check reported that NEITHER entry carried the note, which would have deleted a true sentence: a two-subject claim needs two measurements. Do not author the missing note. The only live question left is whether the `OrderSet` entry should gain a one-clause pointer saying a security note lives on its `RelatedOrder` sibling, which is an editorial preference and a `docs/GLOSSARY.md` DB edit plus regenerate if taken.
- Three measured methodology rules carried out of the spec-005 residual cycle's per-cycle scratchpads, which close with their cycle and leave the rules homeless. Corpus-ratchet edits, same bucket as the process questions above, so each needs the bytes it retires named before it lands. (1) `git log -S<identifier>` searches for changes in how often a name is written, not for changes in the value it names - a key added to or removed from a `frozenset` literal moves no occurrence count, so `-S` sees such a commit only when something else in the same commit also moves the count. The evidence must travel with the rule, since the whole claim is that the hazard is invisible when it bites: `-S'ALLOWED_META_KEYS'` returns 14 commits but recovers only 9 of 13 definitions and 15 of 17 keys - `cursor_field` and `filesystem_path_fields` never appear in any blob it returns. To establish what values a constant has ever held, replay the definition over every revision of the file. (2) `git show <commit>:<path>` on a pre-rename revision exits 128 writing only to stderr, so a replay loop that reads stdout drops the oldest revisions and reports a clean number; resolve each blob at the path the file had at that commit. Carry the corrected demonstration, not the cycle's first one: the stdout-only replay of `ALLOWED_META_KEYS` loses two revisions and its summary numbers do not move at all, which is a sharper picture of a silent failure than a number that visibly changes. (3) Drive move-verification off `git diff -U0` line by line, never off spans chosen by the worker who made the edits - a span-sampled check cannot detect a sentence nobody made into a span, and one cycle's "17 hand-chosen spans, 17/17 pass" missed a cut sentence the diff-driven walk found immediately. Its companion: a cut-not-copy shingle count is tokenizer-dependent and means nothing unquoted - the same two files measured 0, 3, or 4 non-scaffold overlaps at n=8 depending only on whether a comma and a `#` are tokens. The prescription that warning implies, so it is not stated as a separate row: a phrase-shaped duplicate check tokenizes on word characters (`[A-Za-z0-9_]+`), case-folds, and windows over the token stream at n=8. Three facts the sentence above does not carry - the tokenizer itself; the failure DIRECTION, since a whitespace tokenizer leaves punctuation and Markdown emphasis attached to tokens and shifts window positions without changing any word, so it fails OPEN and once reported 0 overlap where 3 restated passages existed; and the non-finding guard, that an 8-word-shingle count of 180 non-scaffold against a 247 control for an unrelated pair means the corpus is LESS coupled than the control, so a raw shingle number must never be reported as a finding without its control beside it.
- Two one-clause additions to `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` whenever a pass legitimately opens it, plus one decision that should be taken deliberately rather than as tidy-up. (1) `## How to read this file` should state that two claims in the file are the only surviving copies of claims the spec may no longer make - the `@strawberry.type`-rewrites-`cls.__annotations__` override diagnosis, condensed in the consumer-override entry, and the "must update this contract spec accordingly" instruction, quoted verbatim at `:247` - and that no future sync pass may align either to the corrected spec, because deleting either deletes the record the companion exists to carry. The two members had to be found by two different methods (a condensation appears in no verbatim scan), which is why the class is worth stating rather than leaving to a reader's grep. (2) The open decision: layer 1 carries exactly four present-tense sentences about spec content the reconciliation has since falsified - the population was established rather than sampled - and all four are disclosed by a single `## How to read this file` clause rather than edited. Whether they stay is a decision about whether the rationale's first layer is a record or a description. The precedent cuts both ways on purpose: `## Standing note` was edited, because it is an analytical coda whose factual premise measured false, while the four record sentences were deliberately left.
- Examined and deliberately NOT repaired by the spec-009 residual cycle, recorded so a later pass does not re-open them as new. `docs/SPECS/spec-028-orders-0_0_8.md`'s `## Doc updates` blockquotes of a card body and of a `CHANGELOG.md` bullet the shipped changelog never carried are left verbatim: editing a quote so it no longer matches its target is a worse defect than the staleness. That spec's `## Risks and open questions` `Ordering`-enum fallback offering `ASC_DISTINCT` / `DESC_DISTINCT` is a NON-FINDING, not a defect - the section's own preamble declares every item carries a fallback if implementation reveals the preferred answer is wrong, so a demand-contingent revisit of a rejection is the section's declared shape and asserts nothing false about shipped code; **it was graded identically four times, please do not open it a fifth**. That spec's `### Decision 3` heading still reading "Five-layer port plus a deferred Layer 6" is KEPT: the heading slug carries 6 in-file uses that a retitle would dangle, and the word names no version and no owner, so heading-vs-body agreement here is a preference not a defect. In `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`, the registry-state sentence satisfied across two objects (registry-global `is_finalized` vs per-type `DjangoTypeDefinition.finalized`) is NOT false - a future tightening should say which object holds which half - and three absolutes were examined and not raised: "Phase 2 is the only window" (true under its resolver scope), the three-applier enumeration (correct as scoped), and "across every cardinality". Finally, five items closed IN that cycle must not be re-deferred: the async `SyncMisuseError` coverage gap (promoted to a permanent test, not deferred), spec-028 Decision 12's DISTINCT ON / Layer 6 deferral (fixed - discharged by the row-preserving `Min`/`Max` ordering, not postponed), card 055's two stale `DjangoModelField` / BACKLOG-38 references (fixed in the DB), the two clauses those fixes falsified (fixed), and `scripts/check_trailing_commas.py` on `tests/test_connection.py` (re-measured at final state and RESOLVED).
- Card numerals rot in three distinct grammars and a sweep that knows only one leaves the other two silently wrong. Measured 2026-08-25 across the insert-at-052 renumber: (a) full card ids (`TODO-BETA-058-0.1.1`) - 136 occurrences; (b) spec filename stems, slugged and bare (`spec-055-fieldset-0_1_1`, `spec-055`) - 81 occurrences; together 34 files. (c) BARE three-digit numerals in prose (`card 055`, `card-055/056/058/065/069`, `055 / 056 / 058 / 065 / 069`) - 173 occurrences across 11 files, the LARGEST population and the only one invisible to any grep for `spec-` or `TODO-`. Thirteen of (c)'s sites were themselves invisible to the first numeral pattern because a `-` prefix looks like a card-id tail; nine sit in heading-anchor pairs (three headings and the six links into them), where heading and links must move together or the anchor breaks. Two forms must NOT be shifted: a sentence describing a PAST renumber is true only in the numbering of its own time (de-number it), and a heading that carries its own seat number re-breaks on every future insert (de-number that too). A rename map derived from the files ON DISK is systematically incomplete: a card with no spec written yet still names the file it will get, and that name carries the card number. Three such planned names sat in board-DB card text (`spec-057-pg_full_text_search-0_1_2`, `spec-058-aggregates-0_1_3`, `spec-060-node_sentinel-0_1_4`, all shown here post-shift), correct before the renumber and wrong after it, and no disk-file map could see them - they surfaced only from an independent postcondition that resolved every spec-filename reference in the tree against `docs/SPECS/`. Two blind spots in the sweep itself, both fail-open: the numeral pattern's trailing lookahead `(?![-.\w])` rejects a match followed by `.` as well as by `-`, so every SENTENCE-FINAL card number (`- **Adversarial graph suite** - card 068.`) survived every pass - 15 file sites across five files, found only by re-scanning for the shape the pattern could not see. And the board-DB pass and the file pass ran DIFFERENT rule sets: the DB pass carried card-id and spec-stem rules but no bare-numeral rule at all, and read only `CardItem.text` and `BoardDoc.body`, leaving 10 bare numerals in card text and 5 `CardReference.raw_text` rows (the graph-substrate amendment note, one per consumer card) citing the substrate spec by its pre-renumber stem. Enumerate the text-bearing COLUMNS before sweeping the DB, and run one rule set over both surfaces.
- **Builder-corpus rule, from the spec-033 residual cycle's own process record:** `BUILD.md`'s dispatch loop keys off a `Status:` line that a worker writes BEFORE it finishes appending its report, so the line is not a completion signal. It cost that cycle a full review round - a pass-2 re-review was dispatched off `Status: built` while the builder was still writing, so the reviewer graded a 424-line artifact that had already reached 897 lines, and raised a confident `Medium` that was false against the finished file. **The durable fix is a dispatch rule, not a worker fault: wait for the agent's own completion signal, never for the file to change.** `docs/builder/ARTIFACT.md` `## Status field ownership` defines who SETS the line but not when it may be READ, and that gap is where the defect lives. Governed by the corpus ratchet. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- Sole card on the `0.0.17` line: owns the `0.0.17` cut - version quintet, GLOSSARY status flip, and CHANGELOG entry.

#### Card references

- Dependency: This card lands on its own `0.0.17` line after the `0.0.16` cut, owns the solo `0.0.17` cut, and documents the registry surface. -> `TODO-ALPHA-054-0.0.16` - Pluggable field-conversion registry
- Dependency: This card lands on its own `0.0.17` line after the `0.0.16` cut; the federation `[federation]` extra and carve-out citation land before it. -> `TODO-ALPHA-055-0.0.16` - Apollo Federation as the standalone django-strawberry-federation package

<a id="beta_release_cleanup_verification_alpha_beta"></a>
### [TODO-ALPHA-057-0.1.0 - Beta release (cleanup, verification, alpha → beta)](KANBAN.html#beta_release_cleanup_verification_alpha_beta)

- Priority: High
- Status: To Do
- Relative size: M
- Labels: `cleanup`, `internal`, `release`, `tests`
- Spec: [spec-057-beta_release-0_1_0.md](docs/SPECS/spec-057-beta_release-0_1_0.md)

#### Predicted files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`tests/base/test_init.py`](tests/base/test_init.py)

#### Dependencies

- `TODO-ALPHA-056-0.0.17` - Alpha documentation-debt discharge

#### Scope

- Version bump to `0.1.0` across the single-sourced `__version__` and everything derived from it, plus `uv.lock`.
- A fresh dated `## [0.1.0]` section authored atop the patch entries (no `[Unreleased]` block exists to promote) with the cumulative Added / Changed / Fixed / Removed roll-up.
- Consumer-facing docs cross-checked against the actual shipped surface, with every "shipped" / "planned" label re-derived rather than trusted.
- The upstream-parity audit pass: every parity claim either `DONE` or explicitly deferred with a recorded reason.
- Full support-matrix test pass at 100% package coverage, then tag and publish.

#### Definition of done

- [ ] Every other Alpha card (`DONE-013-0.0.4` through `DONE-044-0.0.14` plus `DONE-024-0.0.7` and `DONE-045-0.0.14`) is in `DONE`. The alpha documentation-debt card (`TODO-ALPHA-056-0.0.17`) is `DONE` as well: its own gate is that every bullet it carries is discharged or explicitly deferred onto a named card.
- [ ] Full test pass under each supported `(Python, Django, Strawberry)` combination.
- [ ] Coverage stays at 100% for the package source tree.
- [ ] Version bumped to `0.1.0` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock`.
- [ ] A fresh `## [0.1.0] - YYYY-MM-DD` entry authored atop `CHANGELOG.md`'s patch entries (the repo keeps no `[Unreleased]` block) with a one-paragraph release summary plus the cumulative Added / Changed / Fixed / Removed sections covering `0.0.6` through the last shipped alpha patch.
- [ ] `README.md`, `docs/README.md`, `CONTRIBUTING.md`, `docs/GLOSSARY.md`, and `docs/TREE.md` cross-checked against the actual shipped surface; "shipped" / "planned" status markers updated.
- [ ] Audit pass against the parity findings: every ⚛️ and 🍓 card from the two upstream audits is either `DONE` or explicitly deferred with a recorded reason.
- [ ] The beta parity claim carries a carve-out sentence for per-field read permissions: `0.1.0` ships no per-field read permission at all, where strawberry-graphql-django ships `IsAuthenticated` / `HasPerm` / `HasRetvalPerm` / `HasSourcePerm` with SQL pre-filtering and schema directives. The raise-only `check_<field>_permission` gates arrive with the `FieldSet` card at `0.1.1` (spec-059), and the full declarative capability is the post-`1.0.0` `declarative_row_and_field_permissions` row in `BACKLOG.md`. The absence is a missing capability, not the refused `fail_silently` extension shape.
- [ ] The beta parity claim carries a carve-out sentence for model `@property` auto-binding: strawberry-graphql-django auto-types `@model_property` / `@model_cached_property` and plain `property` / `cached_property` from their return annotation, and `0.1.0` binds none of them. The `FieldSet` card delivers resolver-computed fields with `Meta.depends_on` at `0.1.1` but requires a paired `resolve_<field>`, so a migrant's `@property` fields do not auto-bind at `0.1.0` or `0.1.1` either; the owners are the post-`1.0.0` `computed_fields_binding` and `computed_field_optimizer_hints` rows in `BACKLOG.md`.
- [ ] The beta parity claim carries a carve-out sentence for the migration path itself: unregistered relation targets fail loudly at type finalization -- deliberate and argued in spec-009 as error-only, where graphene-django silently drops the field and strawberry-graphql-django falls back to a pk-only type -- and it is the first break many migrants hit, but the guides that would explain it are the Migration and adoption guides card at `0.1.8`. The `0.1.0` claim must state plainly that the migration path is documented later rather than reading as though the guides ship with the beta.
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
- release card.
- release-blocking.
- final card in the Alpha queue; gates the alpha → beta milestone.

#### Open question

- Upstream argument rejections are masked by the secure-output defaults. The fix is for the package to raise Strawberry's relay/pagination argument rejections as `GraphQLError` carrying an audited `extensions.code`, which brings them under the untouched branch of the structural masking rule without loosening it. Not licensed by spec-048; needs a card or an explicit deferral reason in this card's parity audit.
- The debug extension's caps are not configurable, deliberately: `AGENTS.md` says add a settings key only when the feature that needs it lands, and a deployment wanting a different ceiling is a deployment running the extension in production. Revisit only if a real consumer need appears.

#### Note

- release / verification card — gates the alpha → beta cut; not an upstream-parity feature.
- release / verification card, no new subsystem: full `(Python, Django, Strawberry)` matrix pass, 100% coverage, version bump to `0.1.0`, CHANGELOG promotion, doc status cross-check, parity audit, tag + publish.

#### Card references

- Related: Every other Alpha card (`DONE-013-0.0.4` through `DONE-044-0.0.14` plus `DONE-024-0.0.7` and `DONE-045-0.0.14`) is in `DONE`. -> `DONE-013-0.0.4` - Real M2M coverage
- Related: Every other Alpha card (`DONE-013-0.0.4` through `DONE-044-0.0.14` plus `DONE-024-0.0.7` and `DONE-045-0.0.14`) is in `DONE`. -> `DONE-044-0.0.14` - Response-extensions debug middleware
- Related: Every other Alpha card (`DONE-013-0.0.4` through `DONE-044-0.0.14` plus `DONE-024-0.0.7` and `DONE-045-0.0.14`) is in `DONE`. -> `DONE-024-0.0.7` - Django Trac #37064 hardening + `safe_wrap_connection_method`
- Related: Every other Alpha card (`DONE-013-0.0.4` through `DONE-044-0.0.14` plus `DONE-024-0.0.7` and `DONE-045-0.0.14`) is in `DONE`. -> `DONE-045-0.0.14` - Sealed get_queryset visibility-boundary policy artifacts
- Dependency: The alpha documentation-debt card discharges before the 0.1.0 cut. -> `TODO-ALPHA-056-0.0.17` - Alpha documentation-debt discharge

## To Do - Beta (1.0.0)

Cards that complete the django-graphene-filters Layer-3 richness on top of parity (`fields_class`, `aggregate_class`, `search_fields`, plus pre-stable cleanup). Each card targets its own `0.1.x` patch within the road to **1.0.0**. The final card in this column is the `1.0.0` release itself (API freeze, cleanup, verification, beta → stable cut-over). Cards in NNN order = planned ship order.

<a id="graph_substrate_shared_graph_policy_and_dependency_planning"></a>
### [TODO-BETA-058-0.1.1 - Graph substrate: shared graph policy and dependency planning](KANBAN.html#graph_substrate_shared_graph_policy_and_dependency_planning)

- Priority: High
- Status: To Do
- Relative size: L
- Labels: `internal`, `layer-3`, `optimizer`, `permissions`, `query-planning`
- Spec: [spec-058-graph_substrate-0_1_1.md](docs/SPECS/spec-058-graph_substrate-0_1_1.md)

#### Predicted files

- `django_strawberry_framework/extensions/graph.py` (planned)
- `django_strawberry_framework/graph/` (planned)
- `django_strawberry_framework/utils/predicates.py` (planned)
- [`examples/fakeshop/test_query/`](examples/fakeshop/test_query/)
- `tests/graph/` (planned)

#### Planning note

The first of two graph foundation cards — the framework-internal graph-planning vocabulary (`GraphPathPlan`, `PredicatePlan`, `EdgeScope`, `FieldDependencyPlan`, `RowIdentityProof`) plus the operation-scoped dependency memo, extracted into one shared `django_strawberry_framework/graph/` package boundary **before** `FieldSet` (TODO-BETA-059-0.1.1), search (TODO-BETA-060-0.1.2), and `AggregateSet` (TODO-BETA-062-0.1.3) freeze three private versions of the same machinery. Driven by a production audit of a five-root, graph-shaped schedule calendar; the general case is any multi-root dashboard whose roots traverse overlapping relation paths under per-viewer visibility. The consumer surface stays Meta-declared (`Meta.edge_scopes`; sidecar `Set` classes) — never stacked decorators, never a parallel imperative registration API; the plan objects themselves are internal vocabulary, not shipped API. The second foundation card (structural optimization templates + nested sidecar batching) is deliberately not this card.

#### Dependencies

- `TODO-ALPHA-053-0.0.15` - Boundary hardening and system-wide DRY squeeze

#### Scope

- Slice 1 — `graph/` package + operation dependency memo: `graph/memo.py` (`operation_scope()` bracket, `get_or_compute(info, key, factory)`, `graph.scope_key` pre-baking viewer identity and `queryset.db`), installed by both `DjangoOptimizerExtension.on_execute` and a new optimizer-independent `extensions/graph.py::GraphSubstrateExtension`; execution-scoped, immutable-values-only, async single-flight, exception-safe.
- Slice 2 — `graph/paths.py`: frozen `GraphPathPlan` over the shipped relation classifier, the longest-resolvable-prefix path/lookup splitter, `GraphPathPlanSet` grouping keyed on the complete relation chain plus a terminal-is-relation flag, exact owning-`DjangoTypeDefinition` identity with injected type references, and per-hop target-visibility metadata; `graph/proofs.py`: the `RowIdentityProof` lattice.
- Slice 3 — `PredicatePlan` compiler: first relocate the row-preserving primitives to `utils/predicates.py` (a pure ORM leaf; `optimizer/predicates.py` stays as a re-export shim), then `any_of` / `all_of` / `not_` / `direct(Q)` (to-one paths only) / `related(path, Q)` / `same_related_row(path, conditions)` compiling as a strictly sequential fold through `correlated_inner_root` + `attach_exists` with one combined outer `.filter()`, no framework-introduced `DISTINCT`, and a `RowIdentityProof` on every compiled shape.
- Slice 4 — `graph/edges.py` `EdgeScope` (request-bound factories returning predicates, compiled narrow-only onto the child queryset at `_build_child_queryset` after target visibility) + `graph/dependencies.py` `FieldDependencyPlan(columns=...)` + `Meta.edge_scopes` as a net-new `ALLOWED_META_KEYS` entry + live fakeshop activation (`Loan.confidential`, the `LoanType` visibility hook with `Meta.primary`, the `BookType` hook rewrite, `edge_scopes` on `BookType.loans`, live HTTP tests with one-vs-one-hundred-parents query-count equality).
- Slice 5 — docs + card wrap: TREE / GLOSSARY / tracked-path constants regeneration, glossary entries for the five plan objects and the memo, record the amendment obligations on the five consumer cards, flip this card.
- Layering: `optimizer/`, `filters/`, and `types/` import `graph/`; `graph/` imports neither `optimizer/` nor the type registry — type references are injected by callers as opaque `DjangoTypeDefinition` handles.

#### Definition of done

- [ ] `graph/` package ships the plan objects and the memo as frozen dataclasses; no request value storable in any structural object; `graph/` imports neither `optimizer/` nor the type registry.
- [ ] `get_or_compute` proven live and in package tests: sync, async single-flight, both cancellation directions, exception-propagation-then-retry, absent-store degradation, request isolation, alias/viewer keying; works with and without the optimizer extension.
- [ ] `PredicatePlan` compiles as a sequential fold with one combined outer `.filter()`, N distinct reserved aliases for N correlated branches, typed input errors, `direct` over a to-many path rejected, and no compiler-added multiplying outer join or `DISTINCT`.
- [ ] `Meta.edge_scopes` validates two-stage at type creation (a net-new `ALLOWED_META_KEYS` entry); factories return predicates compiled narrow-only via `graph.apply` after target visibility; strictness keys publish only after attachment; no fail-open path (prefetched, per-parent fallback, or optimizer-off).
- [ ] `FieldDependencyPlan(columns=...)` plus the shorthand normalizer shipped — only the members the `FieldSet` card consumes at `0.1.1`; no consumer-less vocabulary members.
- [ ] Live fakeshop activation landed (`Loan.confidential` + migration, the `LoanType` secondary type with `Meta.primary`, the `BookType` hook rewrite preserving the repair-exclusion contract) with parent-count-independent query counts on the windowed path; schema-module tuples swept.
- [ ] 100% package coverage; live-first placement respected; tracked-path constants regenerated; TREE / GLOSSARY / `test_query` README updated.
- [ ] Version quintet and `CHANGELOG.md` untouched — the `0.1.1` release state is owned by the `FieldSet` card's joint cut.

#### Architectural posture

- **Amendment obligation** — per the spec's Decision 1, TODO-BETA-059-0.1.1, TODO-BETA-060-0.1.2, TODO-BETA-062-0.1.3, TODO-BETA-069-0.1.6, and TODO-BETA-072-0.1.8 must be amended to consume the substrate rather than reimplement it, and the amendments must land on those cards before any of them starts — not at this card's Slice 5. `RowIdentityProof` ships as metadata only; the enforcement gate belongs to the sibling structural-templates / nested-sidecar-batching card (TODO-BETA-068-0.1.6).

#### Why it matters

- Five planned Layer 3 surfaces — `FieldSet` (TODO-BETA-059-0.1.1), search (TODO-BETA-060-0.1.2), aggregation (TODO-BETA-062-0.1.3), explain (TODO-BETA-069-0.1.6), and the adversarial suite (TODO-BETA-072-0.1.8) — each need path classification, row-preserving predicate composition, edge-scoped child visibility, or field-dependency vocabulary; without one substrate each ships a private twin and the divergent abstractions freeze at the `1.0.0` API surface.
- Row multiplication through to-many joins silently corrupts consumer permission filters today: a to-many hop inside an outer `Q` multiplies rows, and the audited production case hits it on every root. `PredicatePlan` makes correlated, row-preserving composition a public, refuse-on-misuse API.
- Query growth for every shipped shape is bounded by selection, never by parent row count: `queries(1 parent) == queries(100 parents)`.
- An operation-scoped dependency memo makes cross-root shared computation (viewer grants, audience sets) single-compute per request, with and without the optimizer extension.

#### Dependencies

- The boundary/DRY squeeze freezes optimizer subsystem boundaries; the `graph/` package must sit below them, and Slice 3's predicate relocation composes with the post-squeeze tree.

#### Open question

- How does the cascade cross a to-many edge - hide the parent, or narrow the list? `spec-034` shipped `apply_cascade_permissions` over forward single-column FK / O2O edges only and left M2M and reverse relations out of scope, obligating a follow-up that was never carded. **This card is where the question is decided** rather than a card of its own: Slice 4's `graph/edges.py` `EdgeScope` already compiles child-visibility predicates narrow-only at `_build_child_queryset` after target visibility, and this card's own premise - that a to-many hop inside an outer `Q` multiplies rows - is the same hazard in a different dress. The two answers are not interchangeable and one must be chosen explicitly: **narrow the list** (the parent survives, its related list shows only visible targets) matches `EdgeScope`'s narrow-only compilation but leaks the parent's existence; **hide the parent** (a parent with any invisible target drops out) matches `spec-034` Decision 6's row-exclusion posture, which was chosen precisely to avoid an existence leak, but is not expressible as a narrow-only child predicate. Surfaced 2026-08-28 by the spec-034 residual cycle discharging that spec's Slice 5 obligation; the full deliberation is in `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` under `## Risks and open questions`.

#### Note

- `docs/SPECS/spec-058-graph_substrate-0_1_1.md` is the card's spec of record (written; five slices planned).

#### Card references

- Dependency: The boundary/DRY squeeze freezes optimizer subsystem boundaries; the `graph/` package must sit below them, and Slice 3's predicate relocation composes with the post-squeeze tree. -> `TODO-ALPHA-053-0.0.15` - Boundary hardening and system-wide DRY squeeze
- Related: Amendment obligation: `FieldSet` normalizes `Meta.depends_on` into `FieldDependencyPlan` and consumes the substrate's field-dependency vocabulary instead of a private map shape. -> `TODO-BETA-059-0.1.1` - `FieldSet` declarative field-level behavior (`Meta.fields_class`)
- Related: Amendment obligation: search path planning moves onto `GraphPathPlan` / `GraphPathPlanSet` (path classification + arm grouping); `LOOKUP_PREFIXES` rejection and permission dispatch stay card-local. -> `TODO-BETA-060-0.1.2` - `Meta.search_fields` support
- Related: Amendment obligation: related / permissioned aggregation consumes `EdgeScope` for child visibility instead of a private child-visibility hook. -> `TODO-BETA-062-0.1.3` - Aggregation subsystem
- Related: Amendment obligation: explain reads the substrate's plan objects (and the sibling card's operation plan map) rather than reconstructing plan state. -> `TODO-BETA-069-0.1.6` - Optimizer explain mode
- Related: Amendment obligation: the adversarial suite gains graph-substrate targets (memo isolation, predicate compilation, edge-scope fail-closed paths). -> `TODO-BETA-072-0.1.8` - Adversarial non-live test suite
- Related: The sibling foundation card: owns reproductions R1, R7, R8, and R10, the row-identity enforcement gate, and the structural/bound split this card's plan objects prepare. -> `TODO-BETA-068-0.1.6` - Structural optimization templates and nested sidecar batching

<a id="fieldset_declarative_field_level_behavior_metafields_class"></a>
### [TODO-BETA-059-0.1.1 - `FieldSet` declarative field-level behavior (`Meta.fields_class`)](KANBAN.html#fieldset_declarative_field_level_behavior_metafields_class)

- Priority: High
- Status: To Do
- Relative size: M
- Labels: `fieldsets`, `layer-3`, `public-api`
- Spec: [spec-059-fieldset-0_1_1.md](docs/SPECS/spec-059-fieldset-0_1_1.md)

#### Predicted files

- `django_strawberry_framework/fieldset/` (planned)

#### Planning note

Strawberry port of django-graphene-filters' `AdvancedFieldSet` — the declarative field-level behavior layer that the cookbook drives via `Meta.fields_class`. The cookbook shape: a consumer-authored `class GalaxyFieldSet(FieldSet)` carries `resolve_<field>(self, root, info)` overrides for custom resolution, `check_<field>_permission(self, info)` denial gates that raise before resolve runs, and class-level annotations like `display_name: str | None = strawberry.field(description="...")` for computed fields the Django model does not have. Pointed at by `Meta.fields_class = GalaxyFieldSet` on the owning `DjangoType`. This is the smallest Layer-3 surface by file count but the most novel by semantic surface area — the resolver-override contract, the redaction-vs-denial split, and the computed-field annotation discipline all live here.

#### Dependencies

- `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

#### Scope

- Cookbook anchor: the `fields.py` example in `GOAL.md` and the `recipes/fields.py` in the django-graphene-filters cookbook are the canonical shapes. Tiered date visibility (staff → full datetime, perm-holder → day precision, authenticated → month precision, anonymous → year precision) plus redaction-vs-denial (`resolve_is_private` returns `False` for non-staff = redaction; `check_updated_date_permission` raises for anonymous = denial) plus computed-field annotations (`display_name: str | None = strawberry.field(...)` with `resolve_display_name`) are the three patterns the FieldSet contract must support cleanly.
- Class shape: `class FooFieldSet(FieldSet)` with `class Meta: model = Foo`. The body holds three flavors of declarations: `resolve_<field>(self, root, info)` (custom resolver, overrides the auto-generated one for `<field>`), `check_<field>_permission(self, info)` (denial gate; raises `GraphQLError` or returns silently — runs before `resolve_<field>` for this request), and class-level annotated attributes (computed fields the model does not have; paired with a `resolve_<field>` method).
- Wiring: `DjangoType.Meta.fields_class = FooFieldSet` binds the fieldset at finalizer phase 2.5 (the same seam `filterset_class` / `orderset_class` use). At type-creation time the framework wires each `resolve_<field>` / `check_<field>_permission` into the owning `DjangoType`'s resolver chain so consumers do not have to subclass the type or hand-attach decorators.
- Composes with `DjangoType.Meta.fields`: declaring `Meta.fields = ("id", "name", ...)` on the owning type stays the source of truth for which model fields surface; `FieldSet` only customizes resolution / permission for fields already in `Meta.fields` AND declares any computed fields via class-level annotations.
- Optimizer cooperation: a `resolve_<field>` that touches ORM data (e.g. tiered date redaction reads `root.created_date`) must NOT defeat the optimizer's `only_fields` projection. The fieldset declares which model columns its resolvers depend on via `Meta.depends_on = {"resolve_created_date": ("created_date",), ...}` (or auto-introspection if reliably available); the optimizer adds those columns to the `only()` projection so the resolver does not trigger a deferred-field fetch.
- Composability with `apply_cascade_permissions` (`DONE-034-0.0.10`): a `check_<field>_permission` gate that raises does NOT short-circuit cascade visibility; the cascade narrows the queryset first, then field-level gates run on whatever survives. A field denial does not leak existence — null fields and denials look identical to the client.
- **Consume-the-substrate amendment** (TODO-BETA-058-0.1.1): normalize `Meta.depends_on` into `FieldDependencyPlan` rather than a private map shape — the concrete column tuple stays as shorthand, and the expanded dependency kinds (relation traversals, annotations, contextual prefetches, batch assemblers, selection-sensitive activation, strictness metadata) ship here as the vocabulary's first consumer. The two-halves rule holds: relation traversals extend `select_related` / `prefetch_related` **and** column reads extend the `only()` projection. Strictness observes undeclared computed relation access where the selection makes it detectable. Without this, `FieldSet` optimizes a simple computed display name but cannot safely optimize a computed field over related rows.

#### Definition of done

- [ ] Add `docs/SPECS/spec-059-fieldset-0_1_1.md` covering the `resolve_<field>` override contract, the `check_<field>_permission` denial-vs-redaction guidance, the computed-field annotation discipline (`display_name: str | None = strawberry.field(...)`), and the optimizer `depends_on` contract.
- [ ] Implement `django_strawberry_framework/fieldset/` (package, mirroring the `filters/` shape) with `base.py` (FieldSet class + metaclass), `factories.py` (resolver-binding factory), and a per-fieldset finalizer hook in `types/finalizer.py` phase 2.5.
- [ ] `FieldSet` accepts `class Meta: model = Foo` only; field declarations are method-based (`resolve_<field>`, `check_<field>_permission`) plus class-level computed-field annotations. No `Meta.fields` on the FieldSet itself — the owning `DjangoType.Meta.fields` is the single source of truth for the model-field surface.
- [ ] Optimizer `Meta.depends_on` contract: when a `resolve_<field>` reads model columns the owning type's `Meta.fields` does not surface, the FieldSet declares them via `Meta.depends_on`; the optimizer adds those columns to the `only_fields` projection.
- [ ] Promote `Meta.fields_class` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the resolver-binding pipeline applies end-to-end; this card owns the promotion (spec-059 Decision 8), and the table-driven binder generalization is owned by the aggregation card (`TODO-BETA-062-0.1.3`).
- [ ] Tests under `tests/fieldset/` mirror the source one-to-one. Live HTTP coverage under `examples/fakeshop/test_query/` exercises tiered visibility (staff vs perm-holder vs authenticated vs anonymous), redaction (non-staff sees `is_private = False`), denial (anonymous raises on `updated_date`), and a computed field (`display_name` resolves only for authenticated users).
- [ ] Composability tests: `FieldSet` + `FilterSet` (a field with a `check_<field>_permission` gate is still filterable by an authorized user); `FieldSet` + `OrderSet` (same for ordering); `FieldSet` + `apply_cascade_permissions` (cascade narrows first, then field gates run — no existence leak).

#### Foundation-slice seam

- `DjangoTypeDefinition.fields_class` is the forward-reserved slot the collection phase will populate.
- `Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (no custom Strawberry field class is required for it; spec-059 Decision 11 pins resolver wrapping as the mechanism that carries the gate).
- Phase-2.5 finalizer wiring follows the shipped `_bind_filtersets` / `_bind_ordersets` pattern. New helper `_bind_fieldsets` (or the equivalent dispatched form when `TODO-BETA-062-0.1.3` lands) binds each `Meta.fields_class` to its owning `DjangoTypeDefinition` so resolvers and gates are wired before schema construction.
- Per-field resolver attachment: the existing `_attach_relation_resolvers` already accepts a `skip_field_names` set so consumer-authored fields are not clobbered; FieldSet-bound `resolve_<field>` extends that skip-set so the FieldSet's resolver wins over the auto-generated scalar resolver.
- Custom Strawberry field class — django-graphene-filters' `AdvancedFieldSet` works with a custom field type that carries the `check_<field>_permission` gate at resolve time. That question is settled without one: spec-059 pins **resolver wrapping** as the mechanism (Decision 11 — the wrapper captures the generated resolver and delegates to it as the cascade's step 3), upstream-parity and zero-config with zero overhead on unmanaged fields. Mapping the gate onto Strawberry's `strawberry.field(permission_classes=...)` is likewise rejected: `BasePermission.has_permission(source, info, **kwargs)` is class-per-policy with a fixed message contract, cannot host the gate-then-override cascade ordering, and would synthesize a permission class per managed field for no consumer benefit; a custom `DjangoModelField` field class is unnecessary machinery for the same reason.
- Slot realized in `DONE-034-0.0.10`: `DjangoTypeDefinition.fields_class` is now declared as an inert `type | None = None` sidecar (spec-034 Decision 2 — the structural mirror of the shipped `filterset_class` / `orderset_class` slots). It has no populator yet and stays `None`; `Meta.fields_class` remains in `DEFERRED_META_KEYS` (still rejected at validation). This card's `_bind_fieldsets` is what populates the slot and promotes the key end-to-end.

#### Architectural posture

- Non-goal — node-level sentinel redaction. The upstream `django_graphene_filters/object_type.py::AdvancedDjangoObjectType.get_node` / `_make_sentinel` (`is_redacted=True`) masks a hidden non-null FK target in place instead of dropping the row. The package deliberately did **not** adopt this tier (spec-034 Decision 6 chose row-exclusion), and `FieldSet` does **not** revive it. The redaction taxonomy is two-tier: relation/row visibility = queryset narrowing (`apply_cascade_permissions`, which is why the fakeshop `view_<model>` hooks cascade rather than keep a row with a sentinel FK), field visibility = `FieldSet` (redact value / deny). There is no third node-sentinel tier — `FieldSet` redaction runs only on fields of rows that already survived the cascade; it never masks a relation target to keep an otherwise-hidden row visible. It is now tracked as an explicit, opt-in tier — `TODO-BETA-064-0.1.4` (`Meta.redaction_mode`) — for consumers who explicitly want strict django-graphene-filters node-sentinel parity; it stays opt-in (not the default) because it conflicts with the row-narrowing model.

#### Why it matters

- `FieldSet` is the smallest Layer 3 surface and can define field-selection semantics used by `DjangoConnectionField`.
- It bridges the existing `DjangoType.Meta.fields` behavior and future connection/query APIs.
- Field-level visibility is the only cookbook surface where redaction (return a safe value) and denial (raise an error) need to be distinct. Filter / order / cascade all use queryset narrowing — they remove rows. FieldSet is the one place where a row stays visible but a field is either redacted or guarded behind an error. Without it, the cookbook's `is_private` and `description` patterns are not portable.
- Computed fields (annotations like `display_name: str | None = strawberry.field(...)` paired with `resolve_display_name`) are the cookbook's escape hatch for fields the Django model does not have. The framework currently has no declarative way to add them without subclassing `DjangoType`; the FieldSet is the home for that contract.

#### Dependencies

- `DjangoConnectionField` (`DONE-030-0.0.9`) - `FieldSet` composes on top of the shipped connection-field surface.

#### Open question

- Promotion-owner conflict RESOLVED at the 2026-08-29 board review, per the pinned preferred answer in `docs/SPECS/spec-059-fieldset-0_1_1.md` `## Risks and open questions` (Decision 8): this card owns the `Meta.fields_class` promotion, and the later table-driven dispatch generalization is owned by the aggregation card (the Layer-3 Meta key promotion card that briefly owned it was retired into the aggregation card at the same review). The `#### Definition of done` was reworded to match, and the spec text was reworded to name the aggregation card in the 2026-08-29 renumber sweep, so no residue remains. Originally measured by the spec-009 residual cycle (`docs/builder/bld-009-final.md` deferred-work catalog item 20).

#### Note

- the smallest Layer-3 subsystem: `fieldset.py` + `docs/SPECS/spec-059-fieldset-0_1_1.md` + tests; defines field-selection semantics the connection field consumes. Meta-driven.

#### Card references

- Dependency: `DjangoConnectionField` (`DONE-030-0.0.9`) - `FieldSet` composes on top of the shipped connection-field surface. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- Related: `DONE-034-0.0.10` - Permissions subsystem
- Related: The table-driven Meta-key binder generalization this card's `_bind_fieldsets` would otherwise hard-code a third helper for is owned by the aggregation card (absorbed from the retired promotion card). -> `TODO-BETA-062-0.1.3` - Aggregation subsystem
- Related: `TODO-BETA-064-0.1.4` - Opt-in node-sentinel redaction tier (`Meta.redaction_mode`)
- Dependency: Amendment source: the graph substrate ships the shared planning vocabulary this card must consume instead of reimplementing (spec-058 Decision 1 — the amendment lands at the substrate card's creation, not at its Slice 5). -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

<a id="metasearch_fields_support"></a>
### [TODO-BETA-060-0.1.2 - `Meta.search_fields` support](KANBAN.html#metasearch_fields_support)

- Priority: High
- Status: To Do
- Relative size: M
- Labels: `connections`, `filters`, `public-api`, `search`
- Spec: [spec-060-search_fields-0_1_2.md](docs/SPECS/spec-060-search_fields-0_1_2.md)

#### Predicted files

- [`django_strawberry_framework/filters/`](django_strawberry_framework/filters/)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- `tests/filters/test_search_fields.py` (planned)

#### Planning note

Strawberry analogue of django-graphene-filters' `Meta.search_fields`. The cookbook shape is a tuple of model-field paths including relation-traversal entries: `search_fields = ("name", "description", "object_type__name", "object_type__description")`. The framework adds a single `search: String` argument to `DjangoConnectionField` consumers; when supplied, the framework fans the input across every declared path as an OR'd `icontains` filter and joins the resulting Q-object into the queryset. Relation paths use Django's standard double-underscore lookup syntax; the framework relies on Django's existing relation traversal rather than a custom resolver. Both dependencies have shipped (`DONE-027-0.0.8` Filtering and `DONE-030-0.0.9` `DjangoConnectionField`); the card is planned but unblocked. To-many relation paths compile row-preserving: a correlated EXISTS branch through the shared predicate compiler (optimizer/predicates.py, pre-card groundwork), never a search-driven .distinct() — the root query keeps no membership join and totalCount stays a flat COUNT(*). Second adversarial review (2026-07-22) hardened the contracts: one strict finalize-time plan builder (the utils/relations.py classifier + lookup validator is the only path acceptance oracle; no get_model_field second oracle); the runtime entry point is a queryset compiler (apply_search_sync/_async), not a Q builder; relational search is visibility-aware (every to-many hop composes the hop target type's visibility queryset into the EXISTS body, so a hidden related row never qualifies a visible root — the step is sync/async twinned, not colorless); search honors the declaring type's FilterSet check_<field>_permission gates (a viewer may search a path exactly when they could filter by it — the fakeshop Category name gate is the live proof); a documented SEARCH_MAX_LENGTH=256 input cap with a typed error; duplicate/padded declarations rejected; Slice 4 adds the library to-many live surface (GenreType search_fields=("name", "books__title") over allLibraryGenresConnection) because all four staged products declarations are forward-only; Slice 5 moves the GLOSSARY entry to "implemented on main; release pending the joint 0.1.2 cut" instead of leaving it falsely planned.

Second Part 1 adversarial review (2026-07-22) formalized the groundwork as this spec's pre-card Slice 0 (docs/row-preserving-predicates-part1-plan.md Rev 4) with card-054-owned completion bookkeeping (GLOSSARY/TREE/KANBAN fold-in + OptimizerError raise-site docs), adopted the compositional multiset contract (framework predicates are pure selections: never multiply rows, never collapse consumer duplicates; global distinct removed), refined Decision 12 (direct relational branches carry per-branch hop visibility themselves, AND'd only into their own OR arm - never delegated to cascade) and Decision 13 (active search fires every APPLICABLE FilterSet gate; Meta.search_fields is the grant for ungated paths; alias/prefix/HIDE_FLAT_FILTERS gate semantics pinned).

Cross-spec Medtrics-reproduction review (2026-07-22): part1-plan is Rev 5 and this spec gained Decision 14. Enacted: (a) the multiset contract is anchored to GOAL.md (predicates are selections over consumer-shaped querysets, never a normalization boundary; the DRF endpoint response is never the multiset oracle); (b) reverse-FK-after-to-one (forward FK -> reverse FK -> forward FK) is a named classifier/adapter category, separate from M2M; (c) one shared Medtrics reproduction fixture (Loan.book -> Book.loans -> Loan.patron -> Patron.email, four named loans, ordered-sequence oracle incl. the duplicated pre-rewrite sequence) consumed at three levels: Part 1 adapter test, this card's live LoanType search integration test (acceptance-only DjangoConnectionField(LoanType), search_fields = (note, book__loans__patron__email), exact ordered IDs + totalCount + page boundaries), and package SQL-shape tests (correlated EXISTS, not JOIN+DISTINCT or a scalar aggregate); (d) Decision 14: search scope is type-definition-wide and immutable (no request/resolver/connection mutation of the tuple; different surfaces use distinct DjangoTypes; no field-level override without a demonstrated use case); (e) row-boundary phrase oracle (red/dwarf vs red dwarf) making StringAgg observably wrong, live + SQL-shape; (f) borrowing/migration docs state both intentional DRF SearchFilter divergences together (phrase semantics, static scope). The Medtrics StringAgg patch is explicitly NOT prior art to adopt.

Critical-evaluation fixes (2026-07-22): part1-plan is Rev 6. Enacted after the post-anchor deep evaluation: (1) the LoanType search_fields declaration is permanent type-wide surface on the EXISTING LoanType (Decision 14 cross-ref); acceptance-only describes only the added DjangoConnectionField exposure, the existing list field gains nothing; (2) Decision 12 pins root-model-as-hop-target recursion (LoanType visibility composes into inner loan rows of book__loans; deliberate divergence from the Part 1 raw-traversal filter: adapter) + a hidden-inner-loan live test; (3) dead C.5 fallback clause removed (LoanFilter exists); (4) same-table inner aliasing (library_loan re-entered inside EXISTS) is a named Slice B SQL-shape assertion; C.4 gains nullable-intermediate-to-one-hop and to_field rows; fixture oracles assert captured pks; three fixture levels tier-assigned; (5) Slice A note: legacy path_traverses_to_many is not the defect site, the category proves classify_path first_many_index; (6) live suites must use graphql_client.py helpers and route registry-mutating fixtures through schema_reload/project_schema_override (beyond settings-dependent); (7) test_query/README.md suite-description updates added to Slice D and Slice 5 bookkeeping; (8) confirmed no types/relay.py setting anchor exists, SEARCH_MAX_LENGTH stays a Decision 11 module constant. Code TODO anchors in utils/relations.py and optimizer/predicates.py synced.

Implementation-gate review enacted (2026-07-22): five blockers folded into the spec —
(1) P0-1 Decision 12 one-.filter()-call same-related-row rule (Q tree per relational arm, shared-inner-alias assertion, leak counterexamples incl. book__loans re-entry);
(2) P0-2 exact-owner re-entry: build_search_path_plan(definition, paths) signature, frozen exact-owner reference, secondary-type regression;
(3) P1-3 async permission gates via run_in_one_sync_boundary (Decision 6), live async ORM-reading-gate regression;
(4) P1-4 named path-driven permission-plan helper in utils/permissions.py built post-_bind_filtersets, permission-plan test matrix, assign-after-both retry safety;
(5) P1-5 active_search canonical home moved to utils/connections.py with filters/search.py re-export, lazy-subpackage import pin extended.
Plus Decision 14 multi-type migration mechanics (Meta.primary, separate FilterSets, GlobalID strategy) and a DoD gate bullet. Part 1 plan unchanged (review: ready in principle).

Follow-up multiplicity review enacted (2026-07-22): five findings folded in. Part 1 plan bumped to Rev 7 — prior-art statement corrected (admin lookup_spawns_duplicates DOES detect reverse FK via PathInfo.m2m; old "misses reverse FK" reading was false), PathInfo named Slice A SQL-multiplicity authority beside relation_kind() semantic topology (many_side = any(path_info.m2m), target from path_infos[-1].to_opts; frozen plan keeps package-owned values only), admin helper banned from production (test differential oracle only, valid paths, never sole oracle), reverse-FK category rationale recast detection->compilation, exact acceptance floor Python 3.10 + Django==5.2.0 in sequencing steps 4/9. Spec-058: Decision 7 gains the finding-4 rationale (fixture exists because detection is insufficient; runtime consumes frozen plan, never calls admin helper, never a search_requires_distinct boolean); Test plan + DoD gain the exact-floor live reproduction requirement. Architecture unchanged per review verdict.

Coverage-gap audit (2026-07-31): a cross-check of the spec against the to-many search reproduction guide found two acceptance items with no home in the card -- consumer .only() / .defer() compatibility, and proof that selection-driven N+1 optimization is unchanged by the row-preserving predicate compiler (search + selected relations against a no-search control). Both are now scope + definition-of-done bullets here and Test-plan/DoD entries in the spec, and Slice 4 lists them among the composability cases. The spec's Slice 5 now enumerates the four Slice-0 fold-in obligations with their state (OptimizerError raise site, docs/TREE.md predicate modules, test_query/README.md paragraphs, and the GLOSSARY filterset multiset paragraph all landed with the Part 1 groundwork -- Slice 5 audits them present rather than rewriting them), leaving only the KANBAN fold-in outstanding. Same audit: this card's spec bullet named the pre-convention `docs/spec-search_fields.md`, which never existed; it now names the real spec. The stale-pointer sweep corrected the same defect on cards 34, 36, 39, 53, 55, 56, and 58.

#### Dependencies

- `DONE-027-0.0.8` - Filtering subsystem
- `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

#### Scope

- Cookbook anchor: the `recipes/schema.py` example shipped with django-graphene-filters declares `search_fields = ("name", "description", "object_type__name", "object_type__description")` — flat field names AND relation-traversal paths in the same tuple. The framework must accept both shapes identically; relation traversal is built on Django's standard `<rel>__<field>` lookup syntax.
- Argument shape: a single `search: String` argument on the connection field. Empty/null/whitespace-only input is a no-op (queryset passes through unchanged). Non-empty input produces a single Q-object that OR's `<path>__icontains=<input>` across every declared path. Paths that traverse a to-many relation (reverse FK, M2M, generic) compile as correlated EXISTS branches OR'd with the direct-path predicates — one root row stays one SQL row through counting and pagination; JOIN-plus-DISTINCT is rejected as the implementation strategy.
- Composition with `filterset_class`: `search` and `filter` compose by intersection — the resulting queryset matches every declared filter AND the search OR-clause. The argument-factory machinery is shared between `filterset_class` and `search_fields`, so adding `search` does not duplicate the factory infrastructure.
- Composition with `get_queryset`: search runs against the post-visibility queryset (visibility narrows first), so a user cannot search for hidden rows by guessing field values. Relational search is additionally visibility-AWARE: every to-many hop composes the hop target type's own visibility queryset inside the correlated EXISTS body, so a visible parent can never match through a related row hidden on its own GraphQL surface.
- Composition with the selection optimizer: search contributes NOTHING to the cached OptimizationPlan (no request value, no only/select_related/prefetch_related entry) and the plan contributes no predicate. An active search must leave selection-driven N+1 optimization observably unchanged (live search + selected-relations case paired against a no-search control on query count and select_related/prefetch_related work), and must compose onto a consumer .only() / .defer() queryset without widening or discarding the deferred field set or adding a selected column -- the correlated EXISTS attaches through .alias(), never .annotate(), so the reserved _dst_ name never reaches the SELECT list.
- **Consume-the-substrate amendment** (TODO-BETA-058-0.1.1): search path planning moves onto `GraphPathPlan` / `GraphPathPlanSet` (path classification plus chain-keyed arm grouping) and to-many compilation onto `PredicatePlan`; search must not own the only correct graph compiler. `LOOKUP_PREFIXES` prefix rejection and the permission-dispatch plan stay card-local — they are search policy, not substrate. **Deferred R3 arm recorded here:** a hidden related row must not be able to qualify a visible root through search (the substrate card proves the edge-selection half; this card owns the search-qualification half). **Fixture dependency:** the `LoanType` visibility hook with `Meta.primary` and the secondary-type root-model re-entry surface are created by the substrate card — consume them, do not duplicate them.

#### Definition of done

- [ ] `docs/SPECS/spec-060-search_fields-0_1_2.md` is the card's spec of record (written).
- [ ] Search-fields argument generation lives in `django_strawberry_framework/filters/` and reuses the same DRF-style Meta surface and argument-factory machinery as `filterset_class`.
- [ ] Single `search: String` argument surfaces on `DjangoConnectionField` consumers and produces an OR'd `icontains` queryset filter across every declared field path, compiled row-preserving: direct paths as plain Q predicates, to-many paths as correlated EXISTS branches via the shared predicate compiler; no search-driven `.distinct()`; root `alias_map` free of membership joins; `totalCount` counts the row-preserving queryset directly.
- [ ] Promote `Meta.search_fields` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the pipeline applies it end-to-end; this card owns the promotion, and the table-driven binder generalization is owned by the aggregation card (`TODO-BETA-062-0.1.3`).
- [ ] Tests under `tests/filters/test_search_fields.py` covering single-field, relation-path, and combined-with-filterset cases.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` exercising a search across at least one relation path. Includes the library to-many proof: GenreType search over allLibraryGenresConnection (one genre, two matching books -> one edge, totalCount == 1, EXISTS in the emitted SQL, no search-driven SELECT DISTINCT).
- [ ] SQL-shape regression tests pin the row-preserving compilation: root query `alias_map` excludes membership/child tables, `query.distinct is False`, EXISTS present exactly when a declared path is to-many, and the `totalCount` SQL has no distinct-wrapper subquery.
- [ ] Relational search is visibility-aware (per-hop related-type visibility composed into the EXISTS body via the shared apply_type_visibility_sync/_async helpers) and honors FilterSet check_<field>_permission gates for every declared path (shared utils/permissions.py machinery, loud raise) — proven live with anonymous/staff Category-name-gate tests and a hidden-related-row test.
- [ ] Input hygiene ships the shared active_search predicate (single definition consumed by the pipeline no-op gate AND the non-queryset sidecar guard, so whitespace input is never an observable error), the documented SEARCH_MAX_LENGTH=256 cap with a typed GraphQL error, and one typed combined-queryset preflight for direct-only and to-many plans alike.
- [ ] Predicate/selection independence is proven: with an active to-many search the built OptimizationPlan is identical to the no-search plan for the same selection and carries no request value; the live search + selected-relations case matches its no-search control on query count and select_related/prefetch_related work; and search composes onto consumer .only() / .defer() querysets without widening the deferred set or adding a selected column.

#### Files likely touched

- `django_strawberry_framework/filters/` (search support)
- `django_strawberry_framework/types/base.py` (Meta validation; promote key)
- `tests/filters/test_search_fields.py` (new)
- `examples/fakeshop/apps/products/schema.py` (activation)
- `django_strawberry_framework/connection.py` (synthesized `search:` argument; pipeline step)
- `django_strawberry_framework/optimizer/predicates.py` + `django_strawberry_framework/utils/relations.py` (consumed: pre-card row-preserving predicate compiler + structured path walker)
- examples/fakeshop/apps/library/schema.py (GenreType search_fields activation — the live to-many surface)

#### Verified in upstream

- `django-graphene-filters` exposes `Meta.search_fields = ("name", "description", "category__name")` — a tuple of model-field paths. The connection field gains a single `search: String` argument that fans out across the listed fields as an OR'd `icontains` filter, traversing relations through Django's standard ORM lookup syntax.

#### Why it matters

- `Meta.search_fields` is one of the five django-graphene-filters Layer-3 Meta keys explicitly listed in [`GOAL.md`][goal] alongside `filterset_class`, `orderset_class`, `aggregate_class`, and `fields_class`. Without it the package cannot claim full DGF parity at 1.0.0.
- Currently `search_fields` is in `DEFERRED_META_KEYS` and rejected at validation time. The fakeshop products schema stages four commented `search_fields` tuples awaiting this card's activation slice; `TODO-BETA-066-0.1.5` (Fakeshop GraphQL schema activation) is now scoped to the `node` / `nodes` entry points plus the `totalCount` opt-in and no longer gates them.

#### Dependencies

- `DONE-027-0.0.8` (Filtering subsystem) — the argument factory is shared.
- `DONE-030-0.0.9` (`DjangoConnectionField`) — the `search: String` argument surfaces on connection fields.

#### Note

- a single `search: String` argument fanning out as an OR'd `icontains` across declared field paths; reuses `DONE-027-0.0.8`'s argument-factory machinery. Spec + tests + live HTTP + Meta-key promotion.

#### Card references

- Dependency: both dependencies have shipped: `DONE-027-0.0.8` (Filtering) and `DONE-030-0.0.9` (DjangoConnectionField) landed before this card. -> `DONE-027-0.0.8` - Filtering subsystem
- Related: Promote `Meta.search_fields` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the pipeline applies it end-to-end; this card owns the promotion, and the table-driven binder generalization is owned by `TODO-BETA-062-0.1.3`. -> `TODO-BETA-062-0.1.3` - Aggregation subsystem
- Dependency: both dependencies have shipped: `DONE-027-0.0.8` (Filtering) and `DONE-030-0.0.9` (DjangoConnectionField) landed before this card. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- Related: Currently `search_fields` is in `DEFERRED_META_KEYS` and rejected at validation time. The fakeshop products schema stages four commented `search_fields` tuples awaiting this card's activation slice; `TODO-BETA-066-0.1.5` (Fakeshop GraphQL schema activation) is now scoped to the `node` / `nodes` entry points plus the `totalCount` opt-in and no longer gates them. -> `TODO-BETA-066-0.1.5` - Fakeshop GraphQL schema activation
- Related: a single `search: String` argument fanning out as an OR'd `icontains` across declared field paths; reuses `DONE-027-0.0.8`'s argument-factory machinery. Spec + tests + live HTTP + Meta-key promotion. -> `DONE-027-0.0.8` - Filtering subsystem
- Dependency: Amendment source: the graph substrate ships the shared planning vocabulary this card must consume instead of reimplementing (spec-058 Decision 1 — the amendment lands at the substrate card's creation, not at its Slice 5). -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

<a id="postgres_full_text_search_filter_primitives"></a>
### [TODO-BETA-061-0.1.2 - Postgres full-text search filter primitives](KANBAN.html#postgres_full_text_search_filter_primitives)

- Priority: Medium
- Status: To Do
- Relative size: M
- Labels: `filters`, `public-api`, `search`

#### Predicted files

- [`django_strawberry_framework/filters/base.py`](django_strawberry_framework/filters/base.py)
- [`django_strawberry_framework/filters/inputs.py`](django_strawberry_framework/filters/inputs.py)
- [`examples/fakeshop/test_query/`](examples/fakeshop/test_query/)
- `tests/filters/test_pg_full_text.py` (planned)

#### Planning note

Strawberry analogue of django-graphene-filters' Postgres full-text search family. The cookbook ships `AnnotatedFilter` (base) plus `SearchQueryFilter`, `SearchRankFilter`, and `TrigramFilter` in `django_graphene_filters/filters.py`, with matching `SearchQueryFilterInputType` / `SearchRankFilterInputType` / `TrigramFilterInputType` input shapes in `django_graphene_filters/input_types.py`. These add Postgres-only `searchQuery` / `searchRank` / `trigram` filter inputs to FilterSets on Postgres-backed models, layered on `django.contrib.postgres.search`. Distinct from `Meta.search_fields` (basic OR'd `icontains`); this is the ranked / weighted / similarity full-text surface. Planned; gated on `TODO-BETA-060-0.1.2` (basic search lands first) and shares `DONE-027-0.0.8`'s filter-argument-factory machinery.

Coverage-gap audit (2026-07-31): this card also owns the JOINT 0.1.2 release cut for card 054's `Meta.search_fields` surface -- the version quintet, the CHANGELOG entry (explicit maintainer grant required), README / docs README shipped-surface wording, GOAL/TODAY release status, and the glossary promotion out of card 054's intermediate status. That ownership previously lived only in card 054's spec text, so it was invisible from this card; it is now a scope + definition-of-done bullet. Same audit: this card's spec bullet named the pre-convention `docs/spec-pg_full_text_search.md`; it now names the AGENTS.md spec-<NNN>-<topic>-<version> path.

#### Dependencies

- `DONE-027-0.0.8` - Filtering subsystem
- `TODO-BETA-060-0.1.2` - `Meta.search_fields` support

#### Scope

- Cookbook anchor: `django_graphene_filters/filters.py` ships `AnnotatedFilter` -> `SearchQueryFilter` / `SearchRankFilter` / `TrigramFilter`; `django_graphene_filters/input_types.py` ships the paired `SearchQueryFilterInputType` / `SearchRankFilterInputType` / `TrigramFilterInputType`. Port the four filter classes plus their input shapes onto the Strawberry side.
- `AnnotatedFilter` base: annotate the queryset with a computed column (`SearchVector` / `SearchRank` / `TrigramSimilarity`) under a generated alias, then filter on that alias. The Strawberry-side annotation derives at materialization via the existing `convert_filter_to_input_annotation` path rather than a Graphene `input_type` constructor arg.
- `SearchQueryFilter`: `SearchVector` + `SearchQuery` full-text match with configurable search config, vector weights, and `search_type` (plain / phrase / raw / websearch).
- `SearchRankFilter`: `SearchRank` weighting with `weights` / `cover_density` / `normalization` options.
- `TrigramFilter`: `pg_trgm` `TrigramSimilarity` / `TrigramWordSimilarity` with a `kind` selector and a similarity threshold.
- Postgres-only: degrade with a clear `ConfigurationError` (or skip the filter) on non-Postgres backends; never emit a malformed query on SQLite.
- Prefix-shortcut operators are owned by this card. Card 054 deliberately ships only unprefixed OR-of-`icontains` search and rejects declarations beginning with `^`, `=`, `@`, or `$`. This card decides which shortcuts enter the ported surface and must pin a clear fail-closed non-Postgres contract for `@`; none of the four is considered shipped by card 054.
- Joint `0.1.2` release cut is owned by this card. Card 054 ships `Meta.search_fields` to `main` but deliberately touches no release-state artifact, so this card carries them for BOTH cards: the `0.1.2` version quintet, the CHANGELOG entry (which needs the maintainer's explicit grant per AGENTS.md), README / docs README shipped-surface wording, GOAL/TODAY release status, and the promotion of the `Meta.search_fields` glossary entry from "implemented on main; release pending the joint 0.1.2 cut" to shipped.

#### Definition of done

- [ ] Add `docs/SPECS/spec-057-pg_full_text_search-0_1_2.md`.
- [ ] `AnnotatedFilter` + `SearchQueryFilter` / `SearchRankFilter` / `TrigramFilter` ship in `django_strawberry_framework/filters/` and reuse the shared DRF-style Meta surface + argument-factory machinery from `DONE-027-0.0.8`.
- [ ] Paired input types (`SearchQueryFilterInputType` / `SearchRankFilterInputType` / `TrigramFilterInputType`) generate with stable class-derived names.
- [ ] Backend guard: a clear typed error on non-Postgres backends rather than a malformed query.
- [ ] Tests under `tests/filters/test_pg_full_text.py` covering each filter, the weight/config options, and the non-Postgres guard.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` against a Postgres-backed model (gated on a Postgres test backend; skipped under the default SQLite run).
- [ ] The joint `0.1.2` cut ships for both cards: the `0.1.2` version quintet is bumped, the CHANGELOG entry is written under the maintainer's explicit grant, README / docs README shipped-surface wording and GOAL/TODAY release status are moved for `Meta.search_fields` AND this card's full-text surface, and the `Meta.search_fields` glossary entry is promoted from its card-054 intermediate status to shipped.

#### Files likely touched

- `django_strawberry_framework/filters/base.py` (new filter classes)
- `django_strawberry_framework/filters/inputs.py` (new input types)
- `tests/filters/test_pg_full_text.py` (new)
- `examples/fakeshop/test_query/` (Postgres-gated HTTP coverage)

#### Verified in upstream

- The only cookbook filter-surface gap found in the 0.0.7 DRY-cycle kwarg-parity audit; every other `django_graphene_filters` filter primitive is already shipped in `DONE-027-0.0.8`.

#### Why it matters

- The Postgres full-text family is part of django-graphene-filters' shipped filter surface; recreating it is in scope for cookbook parity (`GOAL.md` "Working reference").
- `Meta.search_fields` (`TODO-BETA-060-0.1.2`) only covers OR'd `icontains`; ranked / weighted / similarity search is a distinct capability the cookbook ships and basic search does not.

#### Dependencies

- `TODO-BETA-060-0.1.2` (`Meta.search_fields`) -- basic search lands first; this is the advanced full-text surface.
- `DONE-027-0.0.8` (Filtering subsystem) -- the filter-argument-factory machinery is shared.

#### Note

- Postgres-only filter family (`SearchQuery` / `SearchRank` / `Trigram`) layered on `django.contrib.postgres.search`; cookbook port of `django_graphene_filters` `filters.py` + `input_types.py`. Spec + tests + Postgres-gated HTTP coverage.

#### Card references

- Dependency: `TODO-BETA-060-0.1.2` (`Meta.search_fields`) -- basic search lands first; this is the advanced full-text surface. -> `TODO-BETA-060-0.1.2` - `Meta.search_fields` support
- Related: `Meta.search_fields` (`TODO-BETA-060-0.1.2`) only covers OR'd `icontains`; ranked / weighted / similarity search is a distinct capability the cookbook ships and basic search does not. -> `TODO-BETA-060-0.1.2` - `Meta.search_fields` support
- Dependency: `DONE-027-0.0.8` (Filtering subsystem) -- the filter-argument-factory machinery is shared. -> `DONE-027-0.0.8` - Filtering subsystem
- Related: The only cookbook filter-surface gap found in the 0.0.7 DRY-cycle kwarg-parity audit; every other `django_graphene_filters` filter primitive is already shipped in `DONE-027-0.0.8`. -> `DONE-027-0.0.8` - Filtering subsystem

<a id="aggregation_subsystem"></a>
### [TODO-BETA-062-0.1.3 - Aggregation subsystem](KANBAN.html#aggregation_subsystem)

- Priority: Medium-high
- Status: To Do
- Relative size: L
- Labels: `aggregations`, `filters`, `layer-3`, `public-api`

#### Predicted files

- `django_strawberry_framework/aggregates/` (planned)

#### Planning note

Strawberry port of django-graphene-filters' `AdvancedAggregateSet` — declarative per-type aggregation via `Meta.aggregate_class`. Mirrors the shipped Filtering and Ordering architecture (six-layer lazy-resolution pipeline; finalizer phase-2.5 binding; per-module input-class namespace) but emits `strawberry.type` output types (not input) and adds a sync/async `compute` / `acompute` split. The cookbook shape: `AggregateSet` subclasses declare `Meta.fields = {"name": ["count", "min", "max", "mode", "uniques"], ...}`, per-stat `check_<field>_<statname>_permission` gates, custom-stat `compute_<field>_<statname>` methods registered via `Meta.custom_stats = {...}`, `RelatedAggregate` for cross-relation traversal, and a `get_child_queryset` cascade hook for related aggregates.

#### Dependencies

- `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

#### Scope

- `Sum`, `Count`, `Avg`, `Min`, `Max`, `GroupBy`
- `AggregateSet`
- GraphQL argument/result factories
- `Meta.aggregate_class` promotion
- Cookbook anchor: django-graphene-filters' `recipes/aggregates.py` declares `class ObjectTypeAggregate(AggregateSet)` with `Meta.fields = {"name": ["count", "min", "max", "mode", "uniques"], "description": ["count", "min", "max"]}` and `Meta.custom_stats = {"centroid": graphene.String}` paired with a `compute_value_centroid(self, queryset)` method (`recipes/aggregates.py:73-90`). The Strawberry port carries this shape verbatim with `OrderSet` → `AggregateSet` substitution and the `compute` / `acompute` sync/async split.
- Built-in stat surface: `count`, `min`, `max`, `mode`, `uniques`, plus the Django aggregate primitives `Sum`, `Count`, `Avg`, `Min`, `Max`, `GroupBy`. The cookbook ships every one as a per-field option on `Meta.fields`; this card pins the same surface.
- `RelatedAggregate("TargetAggregate", field_name="...")` for relation-traversed aggregates (e.g. `celestial_bodies = RelatedAggregate("CelestialBodyAggregate", field_name="galaxy")` on a `GalaxyAggregate`). Accepts a class reference, an absolute import path, or an unqualified name for circular references — the same lazy-resolution contract `RelatedFilter` and `RelatedOrder` ship.
- `Meta.custom_stats = {"<statname>": <return_type>}` declares consumer-defined stats; the framework expects a paired `compute_<field>_<statname>(self, queryset)` method that returns a value matching the declared type. Cookbook example: `Meta.custom_stats = {"centroid": graphene.String}` paired with `compute_value_centroid(self, queryset)` returning the computed centroid string (`recipes/aggregates.py:73-90`).
- Per-stat permission: `check_<field>_<statname>_permission(self, request)` gates a specific (field, stat) pair (cookbook example: `check_name_uniques_permission` raises for non-staff so non-staff cannot see the unique-name distribution while still seeing `count` / `min` / `max`). Mirrors the per-field permission gate in `FilterSet` / `OrderSet` but keyed on the (field, stat) tuple, not just the field.
- `get_child_queryset(self, rel_name, rel_agg)` cascade hook on `AggregateSet` lets a parent aggregate enforce a cascade rule on its children (cookbook example: a shared `_private_aware_child_qs` that filters out `is_private=True` rows when traversing through a `RelatedAggregate`). Composes with `apply_cascade_permissions` (`DONE-034-0.0.10`).
- Sync / async `compute(self, info, queryset) -> <Output>` and `async def acompute(self, info, queryset) -> <Output>` — same dual-shape contract `FilterSet.apply_sync` / `apply_async` ships. Selection-set-aware: only the aggregate output fields the GraphQL query actually selects are computed; the optimizer plan-cache infrastructure drives the selected-fields detection so a 20-stat aggregate output type does not eagerly compute all 20 when the consumer asked for 3.
- Output-type emission: each `AggregateSet` emits a `@strawberry.type`-decorated output class named `<AggregateSet>OutputType` (e.g. `ObjectTypeAggregateOutputType`) materialized in a per-module `aggregates.outputs` namespace — disjoint from `filters.inputs` / `orders.inputs`, mirroring the per-module namespace pattern.
- Config knobs (parity watch-item, carried over from the django-graphene-filters parity review): DGF's aggregate subsystem ships tunable safety limits and an async opt-in as settings — `AGGREGATE_MAX_VALUES`, `AGGREGATE_MAX_UNIQUES`, and `ASYNC_AGGREGATES` (`django_graphene_filters/conf.py`). This card captures the `compute` / `acompute` split and the stat surface but not these config knobs; the spec must confirm they are in scope when `spec-aggregates` is authored, or consciously drop them.
- **Consume-the-substrate amendment** (TODO-BETA-058-0.1.1): related and permissioned aggregation consumes `EdgeScope` for child visibility, `GraphPathPlan` for relation-path classification, and `FieldDependencyPlan` for dependency declaration — no aggregate-private child-visibility abstraction beside `get_child_queryset`. Child aggregates must carry row-identity and cardinality semantics: aggregate fan-out across a many-join is a planner error by default, never a silently multiplied result. **Deferred R3 arm recorded here:** a hidden child must not contribute to a count or an aggregate.
- Optional (absorbed from the retired promotion card): fold the finalizer's per-key binding (`_bind_filtersets` / `_bind_ordersets` / `_bind_fieldsets`) into one dispatched, table-driven form so promoting a Meta key is a data change rather than a new helper per key.

#### Definition of done

- [ ] Add `django_strawberry_framework/aggregates/`.
- [ ] Add mirrored `tests/aggregates/`.
- [ ] Promote `Meta.aggregate_class` only when aggregation is applied end-to-end.
- [ ] Decide result type naming and grouping semantics.
- [ ] Validate generated queryset aggregation paths.
- [ ] Keep aggregation declarations composable with filters, ordering, and connection field behavior.
- [ ] Add `docs/SPECS/spec-058-aggregates-0_1_3.md` covering: `AggregateSet` / `RelatedAggregate` class shape; the `count`/`min`/`max`/`mode`/`uniques` built-in stat surface; `Meta.custom_stats` + `compute_<field>_<statname>` contract; per-stat `check_<field>_<statname>_permission` gating; `get_child_queryset` cascade hook; sync/async `compute` / `acompute` split; selection-set-aware computation; output-type emission and the `aggregates.outputs` namespace.
- [ ] Live HTTP coverage in `examples/fakeshop/test_query/` exercises a real cookbook-shaped aggregate: a parent type with `RelatedAggregate` traversal, a custom stat, a per-stat permission gate, and a selection-set test confirming only the selected stats are computed.
- [ ] Composability with the shipped sidecars: filter narrows first → order is a no-op for aggregate output → aggregate computes against the filtered + cascade-permissioned queryset. Pinned by a single test that exercises all three at once.

#### Foundation-slice seam

- `DjangoTypeDefinition.aggregate_class` is the populated slot.
- The cookbook reference (`AdvancedAggregateSet.compute` / `acompute`) splits sync and async paths; this lines up with the existing async-resolver support in the optimizer.
- Selection-set-aware aggregate computation will reuse the optimizer plan-cache infrastructure, since the aggregate output type's selected fields drive which annotations are computed.

#### Architectural posture

- Concurrency / scatter-gather seam (design guidance carried over from the django-graphene-filters parity review; net-new value, **not** a DGF-parity item). The package has zero query concurrency today, partly deliberate — `relay.py::DjangoNodesField` chooses sequential awaits over `asyncio.gather`, citing Django async-ORM connection safety. Parallelism only pays for genuinely independent queries on separate connections, never naive fan-out over one shared connection/cursor. Hard constraints any gather seam must respect: (1) each thread worker opens a thread-local connection it must close (`close_old_connections`), so the sync pool is small and bounded (≈2–3), NOT `max_workers=NUM_CORES` — except the independent-DB shard case, where core-scaling is correct; (2) the `chunk_size = ceil(count / NUM_CORES)` PK-range partition is a win ONLY when the reduction runs in Python (mode / uniques / percentile / `Counter`), never for a SQL-native aggregate (`Count`/`Sum`/`Min`/`Max`/`Avg`), which adds round-trips and loses index efficiency; (3) the example project runs on SQLite (serializes), so any speedup must be benchmarked on Postgres/MySQL — the 100%-coverage suite cannot prove it under the default runner.
- Where it pays to invest — the `AggregateSet` gather seam (this card). Independent stats that cannot fold into one `.aggregate()` (mode / uniques / percentile / the `Counter`-based custom `compute_*` stats above) are each their own scan, and the PK-range partition applies to their Python reduction; DB-native stats MUST stay single-query (let SQL do it). `acompute` already implies the async seam — build the gather seam (a sync bounded-pool plus the async `acompute` path) into this card from the start rather than retrofitting it. Design it once here: it is reused by the BACKLOG `matrix_dimensions_and_measures` (item 32 — per-measure fan-out + chunked-partition reduction over the heaviest 10M-row / percentile / pivot surface; design its executor with a parallel reduce from the start) and `sharding_aware_optimizer` (item 41 — multi-shard compose over independent DBs / connections: zero GIL contention, no shared-connection hazard, per-shard count/sum/min/max compose; the one place `max_workers=NUM_CORES` is literally correct) cards.
- Async-path constraint. Every async path today wraps its sync body in `sync_to_async(..., thread_sensitive=True)` — `FilterSet.apply_async`, `OrderSet.apply_async`, `aapply_cascade_permissions`, `resolve_mutation_async` — which serializes them onto one asgiref worker. That is a deliberate connection / consumer-hook safety choice, not a bug, but it is the constraint the async `acompute` gather must design around: the gather must run genuinely independent units on their own connections and never re-enter the shared sensitive thread.
- Adjacent optimizer seams investigated (non-aggregation, recorded here so they are not lost — both marginal / deferred): (a) root-connection `totalCount ∥ page slice` — when `Meta.connection` opts into `totalCount`, the count runs serially after the slice via `count()` / `acount()` on the same filtered queryset (`connection.py::_attach_count_sync` / `_attach_count_async`); the two are independent and package-owned, but it is the smallest standalone win and marginal unless the count rivals the page cost, on a parallelizing backend only. (b) parallel independent top-level `prefetch_related` — plain to-many list / M2M siblings still issue N serial `WHERE parent_id IN (...)` scans inside Django's `prefetch_related_objects`; `OptimizationPlan.apply` returns a lazy queryset and Strawberry/Django owns materialization, so parallelizing means the package takes over materialization in the resolvers it controls (per the root-cause rule — NOT monkeypatching `prefetch_related_objects`). High risk; defer behind a Postgres benchmark.
- Ruled out, on the record: the single root list query (`list_field.py`, nothing to split); `resolve_nodes` (`relay.py`, already one `pk__in` per type — optimal within one DB, don't parallelize the single-DB case); `FilterSet` / `OrderSet` `apply_*` (queryset builders, no fan-out); the `0.0.11` mutations (single-row, single-transaction); `finalize_django_types()` (CPU/GIL-bound and contractually single-threaded); and DB-native aggregates. Do not retrofit concurrency onto shipped code without a Postgres benchmark.

#### Note

- full subsystem, parallel to Ordering: reuses `DONE-027-0.0.8`'s six-layer architecture but emits `strawberry.type` output types (not input) and adds the sync/async `compute` / `acompute` split. New `aggregates/` subpackage + `docs/SPECS/spec-058-aggregates-0_1_3.md` + tests.
- Absorbs the retired Layer-3 Meta key promotion card (2026-08-29 board review): `Meta.aggregate_class` is the last `DEFERRED_META_KEYS` member left to promote and its promotion is already this card's DoD - `filterset_class` / `orderset_class` are already in `ALLOWED_META_KEYS`, `fields_class` promotion is owned by the `FieldSet` card, and `search_fields` promotion by the `Meta.search_fields` card. The board-wide rule the retired card carried holds unchanged: do not move a key from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` until the pipeline applies it end-to-end.
- No version quintet or CHANGELOG entry - the `0.1.3` release state is owned by the mutation-idempotency card's joint cut, which lands last on the line.

#### Card references

- Related: full subsystem, parallel to Ordering: reuses `DONE-027-0.0.8`'s six-layer architecture but emits `strawberry.type` output types (not input) and adds the sync/async `compute` / `acompute` split. New `aggregates/` subpackage + `docs/SPECS/spec-058-aggregates-0_1_3.md` + tests. -> `DONE-027-0.0.8` - Filtering subsystem
- Related: `DONE-034-0.0.10` - Permissions subsystem
- Dependency: Amendment source: the graph substrate ships the shared planning vocabulary this card must consume instead of reimplementing (spec-058 Decision 1 — the amendment lands at the substrate card's creation, not at its Slice 5). -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

<a id="mutation_idempotency_keys"></a>
### [TODO-BETA-063-0.1.3 - Mutation idempotency keys](KANBAN.html#mutation_idempotency_keys)

- Priority: High
- Status: To Do
- Relative size: M
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

- Shipped baseline (given, commit 1b06c39e): every top-level mutation field already runs inside an always-on `transaction.atomic()` wrap, with `Meta.select_for_update` available to lock the affected rows. This card builds on that baseline and adds idempotency only — it introduces no new transaction opt-in.
- Add `Meta.idempotency_key = "request_id"` and `Meta.idempotency_ttl = 86400` backed by a durable package-owned idempotency record. A database uniqueness constraint over the fully scoped key serializes concurrent first attempts; the stored terminal response and status are the replay source of truth.
- Create the idempotency reservation and mutation side effects in the same database transaction, and persist the successful terminal response before that transaction commits. Validation, permission, completion, and database failures roll back both. `django.core.cache` may accelerate committed replays only; it is never the authority.
- Keep the surface DRF-shaped and mutation-local: declaration lives on each `DjangoMutation.Meta`, with safe defaults and no global setting required.

#### Definition of done

- [ ] New or amended mutation spec documents the idempotency Meta keys (`Meta.idempotency_key` / `Meta.idempotency_ttl`), durable-record schema and migration, canonical scope key, reservation state machine, TTL/reclamation behavior, terminal-response replay, concurrent retry semantics, and failure rollback rules.
- [ ] A unique durable reservation participates in the same always-on atomic boundary as the mutation write. The successful terminal response is stored before commit; a concurrent duplicate waits for or reads that committed outcome and never executes the mutation body twice. Any cache write is post-commit acceleration only.
- [ ] The durable idempotency key is scoped by mutation class, key value, authenticated principal or anonymous scope, and a canonical digest of operation arguments so unrelated calls cannot collide; reuse with a different digest fails loudly.
- [ ] Tests cover concurrent same-key submissions, a client retry after the database commit but before response receipt/cache fill, stale-reservation recovery and TTL expiry, successful replay, validation/completion/exception rollback, cache unavailability, and sync/async mutation paths where supported.
- [ ] Live `/graphql/` coverage exercises a real fakeshop mutation twice with the same idempotency key and proves the second response replays without a second write; a database-backed concurrency regression proves simultaneous duplicates also write once.

#### Foundation-slice seam

- `DONE-036-0.0.11` owns the base `DjangoMutation` class, generated input types, and shared `errors: list[FieldError]` envelope; this card layers safety semantics onto that lifecycle instead of inventing a separate mutation primitive.
- DRF serializer and Form-based mutation cards inherit the same atomic/idempotency implementation through the shared mutation base once their adapters land.

#### Files likely touched

- `django_strawberry_framework/mutations/` plus the package-owned durable idempotency model and migration.
- `tests/mutations/` plus live fakeshop GraphQL mutation tests.
- `docs/GLOSSARY.md` and the mutation spec when the feature ships.

#### Verified in upstream

- Neither graphene-django nor strawberry-graphql-django ships mutation idempotency; this is a differentiator rather than an upstream-parity card.

#### Why it matters

- Stripe-style idempotency is production table stakes for payment, order, and inventory writes, but Django GraphQL packages leave it to each app.
- Combining the always-on transaction with a durable unique reservation and terminal-response replay makes generated mutations safe across retries, client timeouts, duplicate submissions, concurrent workers, and cache/process loss.

#### Dependencies

- Builds on the core DjangoMutation lifecycle and generated input envelope from DONE-036-0.0.11.

#### Note

- Revised score after the durable concurrency design: Realistic 9/10, Impact 8/10, Difficulty 6/10; the database record, migration, state machine, and crash/concurrency matrix make this a medium slice.
- Owns the joint `0.1.3` cut: the version quintet and the CHANGELOG entry (under the maintainer's explicit grant) land here for both `0.1.3` cards; this card lands last on the line. Re-versioned `0.1.7` -> `0.1.3` at the 2026-08-29 board review: high priority, no unshipped dependency, and it fills the slot the retired Layer-3 Meta key promotion card vacated.

#### Card references

- Dependency: Builds on the core DjangoMutation lifecycle and generated input envelope from DONE-036-0.0.11. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="opt_in_node_sentinel_redaction_tier_metaredaction_mode"></a>
### [TODO-BETA-064-0.1.4 - Opt-in node-sentinel redaction tier (`Meta.redaction_mode`)](KANBAN.html#opt_in_node_sentinel_redaction_tier_metaredaction_mode)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required)
- Status: To Do
- Relative size: L
- Labels: `layer-3`, `permissions`, `public-api`, `security`

#### Predicted files

- `django_strawberry_framework/permissions/` (planned)
- [`django_strawberry_framework/types/`](django_strawberry_framework/types/)

#### Planning note

Strawberry port of django-graphene-filters' node-level sentinel redaction — the third redaction tier the package deferred in spec-034 Decision 6 (row-exclusion) and re-confirmed as a `FieldSet` Non-goal (`TODO-BETA-059-0.1.1`). Upstream `django_graphene_filters/object_type.py::AdvancedDjangoObjectType` exposes it as public SDL: `is_redacted = graphene.Boolean(...)` (`:137`), `resolve_is_redacted` (`:151`), `_make_sentinel` (`:200`), and a `get_node` (`:251`) that returns a `pk=0` sentinel in place of a hidden row so a non-null FK to a hidden target still resolves. This card recreates that surface behind an explicit per-`DjangoType` opt-in so a django-graphene-filters consumer relying on `isRedacted` / sentinel masking can port verbatim, without disturbing the default row-narrowing model.

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

- [ ] Add `docs/SPECS/spec-060-node_sentinel-0_1_4.md` covering the `Meta.redaction_mode` switch, sentinel-chain semantics, the `isRedacted` SDL contract, the `get_node` override, and reconciliation with `apply_cascade_permissions`; state the existence-leak trade-off and why the tier is opt-in.
- [ ] Implement the sentinel-row factory and node-resolution hook (extending the `permissions/` surface) plus the `isRedacted` field and `Meta.redaction_mode` wiring on `DjangoType`.
- [ ] `Meta.redaction_mode` defaults to `"exclude"`; all existing schemas and tests stay unchanged under the default. The `"sentinel"` machinery is wired only when the mode is set.
- [ ] Tests mirror the source one-to-one; live HTTP coverage exercises a hidden non-null FK target resolving to a `pk=0` sentinel with `isRedacted = true`, a normal row reading `isRedacted = false`, and `get_node` on a hidden id returning the sentinel in `"sentinel"` mode vs `null` in `"exclude"` mode.
- [ ] Composability tests: `"sentinel"` mode + `apply_cascade_permissions` — the top-level cascade still narrows rows; sentinels appear only for relation targets of surviving rows (no row resurrection, no double counting).
- [ ] Amend the `FieldSet` (`TODO-BETA-059-0.1.1`) Architectural-posture note so its node-sentinel "Non-goal" cross-references this card as the realized opt-in tier.

#### Verified in upstream

- ⚛️ `graphene_django` — `django_graphene_filters/object_type.py::AdvancedDjangoObjectType` exposes node-sentinel redaction as public SDL: `is_redacted = graphene.Boolean(...)` (`:137`), `resolve_is_redacted` (`:151`), `_make_sentinel` (`:200`), and a `get_node` (`:251`) that returns a `pk=0` sentinel in place of a hidden non-null FK target. This card ports that surface behind an opt-in.

#### Architectural posture

- This card is the explicit, opt-in reversal of spec-034 Decision 6. The default stays row-exclusion — the existence-leak-free model; this tier exists only so the one public django-graphene-filters behavior with no analog (`isRedacted` / sentinel FK masking) is portable for consumers who explicitly choose it. It does not become the default and does not weaken the cascade for `"exclude"` schemas.

#### Why it matters

- Closes the single remaining django-graphene-filters public-surface gap recorded by the parity review (finding P2): node-sentinel redaction was the only public upstream behavior with no equivalent and no card — a deliberate non-goal under `spec-034-permissions-0_0_10` Decision 6's row-exclusion model. This converts a buried non-goal into a tracked, opt-in parity feature.
- Lets a django-graphene-filters consumer relying on `isRedacted` / sentinel FK masking migrate verbatim instead of re-architecting around row-exclusion.

#### Dependencies

- `DONE-034-0.0.10` (Permissions subsystem) — extends the `apply_cascade_permissions` / `get_queryset` cascade; this tier reconciles sentinels with cascade narrowing.
- `DONE-032-0.0.9` (Full Relay story) — overrides the shipped `get_node` node-resolution seam.

#### Note

- No version quintet or CHANGELOG entry - the `0.1.4` release state is owned by the choice-enum naming card's joint cut, which lands last on the line.

#### Card references

- Dependency: `DONE-034-0.0.10` (Permissions subsystem) — extends the `apply_cascade_permissions` / `get_queryset` cascade; this tier reconciles sentinels with cascade narrowing. -> `DONE-034-0.0.10` - Permissions subsystem
- Dependency: `DONE-032-0.0.9` (Full Relay story) — overrides the shipped `get_node` node-resolution seam. -> `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)
- Related: Amends the `FieldSet` node-sentinel Non-goal note (`TODO-BETA-059-0.1.1`) — this card is the realized opt-in tier that note defers to. -> `TODO-BETA-059-0.1.1` - `FieldSet` declarative field-level behavior (`Meta.fields_class`)

<a id="stable_choice_enum_naming_override"></a>
### [TODO-BETA-065-0.1.4 - Stable choice enum naming override](KANBAN.html#stable_choice_enum_naming_override)

- Priority: Low-medium
- Status: To Do
- Relative size: S
- Labels: `choice-enums`, `public-api`, `schema`, `stable-api`

#### Predicted files

- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`tests/types/test_converters.py`](tests/types/test_converters.py)

#### Dependencies

- `TODO-ALPHA-051-0.0.15` - Upstream parity-gap closure

#### Scope

- Add a stable override surface such as `Meta.choice_enum_names = {"status": "ItemStatusEnum"}`.

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

#### Verified in upstream

- Parity target - graphene-django's global choice-enum renaming, two settings in `graphene_django/settings.py`: `DJANGO_CHOICE_FIELD_ENUM_CUSTOM_NAME` takes an import-path string, resolved with `import_string` inside `converter.py`'s `generate_enum_name` and called with the model field, so one callable renames every generated enum process-wide; `DJANGO_CHOICE_FIELD_ENUM_V2_NAMING` is a second global flag selecting an alternate naming template (`ItemStatus` in place of the default `ShopItemStatusChoices`), and exists only to give the first shape a softer alternative. This card supersedes both rather than porting them: a process-wide callable makes the schema's type names a function of settings rather than of the declarations that produced them, so `Meta.choice_enum_names` puts the name beside the declaration it names and leaves every field that does not set it on the generated default.

#### Open question

- Decide whether this belongs in the consumer-overrides spec or a small choice-enum follow-up spec.

#### Note

- bounded override surface (`Meta.choice_enum_names`) preserving `(model, field)` enum reuse; touches `base.py` / `converters.py` / `registry.py` + tests.
- Choice fields generate Strawberry enums and cache them by `(model, field_name)`.
- The first `DjangoType` to read a choice column wins the generated enum's GraphQL name.
- This is deterministic for a fixed import order but still makes schema naming dependent on which type imports first.
- Preserve enum reuse by `(model, field_name)` while making the published schema name explicit when consumers need it.
- Owns the joint `0.1.4` cut: the version quintet and the CHANGELOG entry (under the maintainer's explicit grant) land here for both `0.1.4` cards; this card lands last on the line.

#### Card references

- Dependency: The parity-gap card lands the `django-choices-field` enum-reuse behaviour whose naming surface and cache contract this card stabilizes. -> `TODO-ALPHA-051-0.0.15` - Upstream parity-gap closure

<a id="fakeshop_graphql_schema_activation"></a>
### [TODO-BETA-066-0.1.5 - Fakeshop GraphQL schema activation](KANBAN.html#fakeshop_graphql_schema_activation)

- Priority: Medium
- Status: To Do
- Relative size: M
- Labels: `example-app`, `graphql-api`, `relay`, `schema`

#### Planning note

The product-catalog root schema is already live: four `DjangoConnectionField` roots with their filtersets, ordersets, and mutations are wired and served (the Relay decisions in `DONE-032-0.0.9` shipped). The remaining unclaimed activation is the Relay `node` / `nodes` root entry points plus the connection `totalCount` opt-in; per-subsystem activation (fieldsets, search, aggregates) is owned by the Slice 4 of the respective Layer-3 subsystem cards, not here.

#### Dependencies

- `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)

#### Scope

- Add a subscription surface to the fakeshop example so subscription behaviour can be exercised at the live tier. Today there is no subscription app anywhere in `examples/fakeshop`, and `django.test.Client` cannot reach a WebSocket, so every subscription row in the suite is a consumer-tier substitution.
- Wire the Relay `node` (single refetch) and `nodes` (batch refetch) root entry points and the connection `totalCount` opt-in on the product-catalog roots, leaving non-opting connections unchanged - the activation half the DoD gates; previously the DoD stated it while Scope named only the subscription surface (scope/DoD mismatch closed at the 2026-08-29 board review).

#### Definition of done

- [ ] Wire the Relay `node` (single-object refetch) and `nodes` (batch refetch) root entry points into the fakeshop product-catalog schema, built on the shipped Relay story (`DONE-032-0.0.9`).
- [ ] Add the connection `totalCount` opt-in on the product-catalog `DjangoConnectionField` roots, leaving connections that do not opt in unchanged.
- [ ] Add in-process `schema.execute_sync` coverage under `examples/fakeshop/apps/products/tests/` for the `node` / `nodes` entry points and `totalCount`.
- [ ] Add live `/graphql/` coverage under `examples/fakeshop/test_query/` exercising a `node` refetch by GlobalID, a `nodes` batch refetch, and a `totalCount` query.
- [ ] The per-event error-policy masking rows run at the live tier against that surface, replacing the consumer-tier substitution in `tests/test_routers.py` that spec-048 carried forward: two events on both WebSocket protocols, each frame carrying the policy message and its own correlation id, plus the `error_policy={"enabled": False}` control row.

#### Note

- narrow example-wiring card: the product-catalog root schema is already activated (four connection roots + filtersets/ordersets/mutations); this card adds only the `node` / `nodes` entry points and the `totalCount` opt-in, with in-process + live HTTP tests.
- `examples/fakeshop/apps/products/schema.py` already serves the four `DjangoConnectionField` roots (`allCategories` / `allItems` / `allProperties` / `allEntries`) with filtersets, ordersets, permissions, and mutations; it does not yet add the `node` / `nodes` entry points or a `totalCount` opt-in — this card adds those.
- The `node` / `nodes` entry points build on the shipped Relay story and `totalCount` is a package-owned connection opt-in; neither needs a further Layer-3 subsystem to land here.
- No version quintet or CHANGELOG entry - the `0.1.5` release state is owned by the product-catalog test card's joint cut, which lands last on the line.

#### Card references

- Dependency: The product-catalog root schema is already live; the remaining node / nodes entry points and totalCount opt-in build on the shipped Relay story (`DONE-032-0.0.9`). -> `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)
- Related: Historical gate, retyped related: the recut scope (node / nodes + totalCount) does not depend on the Meta-key promotion work, which the aggregation card absorbed at the 2026-08-29 board review. -> `TODO-BETA-062-0.1.3` - Aggregation subsystem

<a id="product_catalog_layer_3_http_graphql_tests"></a>
### [TODO-BETA-067-0.1.5 - Product-catalog Layer 3 HTTP GraphQL tests](KANBAN.html#product_catalog_layer_3_http_graphql_tests)

- Priority: Medium
- Status: To Do
- Relative size: S
- Labels: `example-app`, `graphql-api`, `layer-3`, `tests`

#### Dependencies

- `TODO-BETA-062-0.1.3` - Aggregation subsystem
- `TODO-BETA-066-0.1.5` - Fakeshop GraphQL schema activation

#### Scope

- Add a per-app test for `examples/fakeshop/apps/products/services.py::seed_cascade_split` under `examples/fakeshop/apps/products/tests/`. Every other public helper in that module is covered; this one is reached only through the live cascade rows. Example apps sit outside the `fail_under` gate, so this is a test-surface asymmetry rather than a coverage gap, and it lands naturally beside this card's in-process `schema.execute_sync` work. Recorded 2026-08-28 by the spec-034 residual cycle (R1c finding L1).

#### Definition of done

- [ ] Add live `/graphql/` acceptance tests under `examples/fakeshop/test_query/` for the activated product-catalog schema, reusing the library app's placement and schema-reload pattern.
- [ ] Cover the product-catalog connection / query fields and the other activated Layer 3 public surfaces end-to-end over HTTP.
- [ ] Keep per-app in-process `schema.execute_sync` tests under `examples/fakeshop/apps/products/tests/`; live HTTP tests stay under `examples/fakeshop/test_query/`.

#### Why it matters

- The library app already has live `/graphql/` acceptance tests under `examples/fakeshop/test_query/`.

#### Test plan

- bounded test suite: live `/graphql/` acceptance tests for the activated product-catalog schema, reusing the library app's placement + schema-reload pattern.

#### Open question

- Does the redundant `view_<model>` branch in the four fakeshop permission hooks stay? Each hook's `elif user and user.has_perm("products.view_<model>")` arm evaluates to the same expression as the fall-through it precedes, so it cannot change the result and costs a permission-table read per request per type. It is **spec-conformant** - `spec-034` Slice 4 and Decision 6's consumer-recipe divergence both demand it - so collapsing it is a contract change, not a cleanup. Paths: **(a)** keep it and record in the spec *why* a redundant branch is deliberate, **(b)** collapse each hook and add a spec sentence saying the grant is deliberately not a branch, or **(c)** give the branch different behaviour, which reverses Decision 6's recorded divergence and belongs to `TODO-BETA-064-0.1.4` rather than here. **A collapse is now safe to attempt**: the spec-034 residual cycle's R3 landed parametrized staff rows in `examples/fakeshop/test_query/test_products_api.py` that assert the `view_<model>` actor explicitly for all four models, so a mistake in the collapse fails loudly. Recorded 2026-08-28 (R1c finding M1, escalated as contract-level).

#### Note

- activating the product-catalog fakeshop GraphQL schema
- connection/query fields and other Layer 3 public surfaces
- Future product-catalog HTTP tests should use the same placement and schema-reload pattern.
- In-process `schema.execute_sync` tests still go under `examples/fakeshop/apps/products/tests/`.
- Owns the joint `0.1.5` cut: the version quintet and the CHANGELOG entry (under the maintainer's explicit grant) land here for both `0.1.5` cards; this card lands last on the line.

#### Card references

- Dependency: Depends on the activated product-catalog schema; these HTTP tests exercise the surface that card wires. -> `TODO-BETA-066-0.1.5` - Fakeshop GraphQL schema activation
- Dependency: The acceptance sweep lands after the Layer-3 trio so it sees every activated Layer-3 surface; the aggregation card is the last of the trio. -> `TODO-BETA-062-0.1.3` - Aggregation subsystem

<a id="structural_optimization_templates_and_nested_sidecar_batching"></a>
### [TODO-BETA-068-0.1.6 - Structural optimization templates and nested sidecar batching](KANBAN.html#structural_optimization_templates_and_nested_sidecar_batching)

- Priority: High
- Status: To Do
- Relative size: L
- Labels: `internal`, `optimizer`, `performance`, `query-planning`
- Spec: [spec-068-structural_templates-0_1_6.md](docs/SPECS/spec-068-structural_templates-0_1_6.md)

#### Predicted files

- [`django_strawberry_framework/connection.py`](django_strawberry_framework/connection.py)
- [`django_strawberry_framework/optimizer/`](django_strawberry_framework/optimizer/)
- [`examples/fakeshop/test_query/`](examples/fakeshop/test_query/)
- [`tests/optimizer/`](tests/optimizer/)

#### Planning note

The second of two graph foundation cards, sibling to the graph substrate (TODO-BETA-058-0.1.1). Where the substrate ships the shared planning vocabulary, this card ships the optimizer architecture that consumes it — four pillars: (1) the structural/bound plan split (`StructuralOptimizationTemplate` cacheable across requests, `BoundOptimizationPlan` request-local, `OptimizationPlan` produced by binding); (2) root-subtree structural cache keys replacing whole-operation AST keys; (3) nested sidecar batching — filtered/ordered/search-bearing nested connections stop executing per parent; (4) the operation plan map replacing last-wins introspection, plus `RowIdentityProof` enforcement at the window gate. Seated immediately ahead of explain (TODO-BETA-069-0.1.6), which renders the plan map and shares the `0.1.6` joint cut. No new consumer surface — every object is internal optimizer vocabulary; the observable contract is query counts, cache behavior, explain completeness, and strict-mode errors.

#### Dependencies

- `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

#### Scope

- Slice 1 — template/bound core: `optimizer/templates.py` with frozen `StructuralOptimizationTemplate` (relative paths, field dependency graph, visibility binding slots, nested argument slots, row-identity proof recipe) and `BoundOptimizationPlan` (absolute paths, database alias, visibility querysets, concrete `Prefetch` objects, normalized argument values); the normalized root-subtree fingerprint builder; the binding pipeline producing today's `OptimizationPlan`; package tests proving bind-equivalence with directly-walked plans. Behavior-neutral by design.
- Slice 2 — cache rekey, response-path rebasing, operation plan map: `DjangoOptimizerExtension._build_cache_key` moves to the subtree fingerprint (exact owning type identity, root field/return type, normalized subtree selection, only the directive/pagination slots referenced inside the subtree, strategy config); templates store relative paths and binding rebases them under the actual alias; `_publish_plan_to_context` publishes the plan map keyed by root execution identity while the legacy `DST_OPTIMIZER_PLAN` last-wins key is retained for the explain card to retire.
- Slice 3 — nested sidecar batching: `optimizer/sidecar.py` with the eight-step normalization (edge-scoped child base -> FilterSet once -> OrderSet once -> deterministic order -> row-identity proof -> partition by parent join key -> window/lateral page -> attach per response-key `to_attr`); `_divergent_key_windows` plans argument-bearing response keys instead of abandoning them; `connection.py::_build_relation_connection_resolver` consumes the batched result attribute; the request-bound sidecar plan cache; per-alias batching.
- Slice 4 — row-identity enforcement + live activation: `unwindowable_child_queryset_reason` composes with the `RowIdentityProof` grades; strict targets raise a targeted unproven-row-identity error, non-strict targets fall back visibly, no automatic `DISTINCT`; the live fakeshop matrix (R1 five-root cache isolation, R7 ordered nested batching, R8 gate arms, R10 plan-map completeness, the R3 filtered arm promoted from characterized to asserted-equal query counts).
- Slice 5 — docs + card wrap: TREE / GLOSSARY / `test_query` README updates, audit the explain-card amendment is honored, flip this card. Version quintet, `CHANGELOG.md`, and release prose untouched — owned by the explain card's `0.1.6` joint cut.
- Changed seams: `optimizer/extension.py` (`_build_cache_key`, `_publish_plan_to_context`), `optimizer/walker.py` (`_plan_prefetch_relation` — visibility becomes a binding slot, not `cacheable = False`), `optimizer/nested_planner.py` (`_divergent_key_windows`), `optimizer/nested_fetch.py` (`unwindowable_child_queryset_reason`), `connection.py` (`_build_relation_connection_resolver`). New modules consume `graph/` and are not imported by it.

#### Definition of done

- [ ] `StructuralOptimizationTemplate` / `BoundOptimizationPlan` ship frozen; no request value storable in any structural object; the adversarial construction test raises.
- [ ] The plan cache keys by root-subtree fingerprint; the R1 matrix is green live (isolation, aliasing, re-embedding, full-hit repeat).
- [ ] Visibility-bearing relation templates are cross-request cacheable; `get_queryset` binds per request; one bound child recipe per relation/argument/scope key per request.
- [ ] Filtered/ordered/search-bearing nested connections batch with query counts independent of parent count (exact per-backend equalities, never inequalities); per-alias batching proven; the R3 filtered arm asserts equalities.
- [ ] Strict mode refuses unproven window shapes with a targeted error; non-strict falls back visibly; no code path injects `DISTINCT`.
- [ ] The operation plan map is complete and deterministic under reversed async completion order; the legacy key still serves existing readers.
- [ ] Sync and async agree across every arm; the no-extension and `OptimizerHint.SKIP` arms are unchanged; 100% package coverage; live-first placement respected.
- [ ] Version quintet and `CHANGELOG.md` untouched — the `0.1.6` release state is owned by the explain card's joint cut.

#### Architectural posture

- **Amendment obligations recorded at this card's creation** — explain (TODO-BETA-069-0.1.6) consumes the operation plan map and retires the legacy `DST_OPTIMIZER_PLAN` key; the adversarial suite (TODO-BETA-072-0.1.8) gains template-store, binding-boundary, and proof-gate targets. This card changes the introspection data, not its readers — the legacy key stays last-wins until explain rewires.
- No request value — user, tenant, queryset, database alias, or argument value — is storable in any structural object (the substrate card's posture, extended verbatim); enforced structurally and tested adversarially. Pluggable nested-fetch strategies must consume the sidecar normalization and the `RowIdentityProof` gate — a strategy that self-certifies child row identity would reopen the window-safety hole in a new backend. The framework never injects `DISTINCT` to launder an unproven shape.

#### Why it matters

- Whole-operation cache keys churn sibling plans: five roots across 32 combinations of five binary directive/pagination choices can occupy 160 entries of a 256-cap cache that evicts a quarter when full; toggling one root's `@include` variable invalidates every sibling's plan.
- Request-bound visibility poisons cacheability: one `get_queryset`-bearing child type marks the entire parent plan `cacheable = False`, so the most security-sensitive types are exactly the ones that replan on every request.
- Filtered/ordered nested connections execute per parent: one hundred parents with a filtered child connection issue one hundred (or, with `totalCount`, two hundred) child statements. The substrate card pinned this arm as characterized-only and assigned closing it here.
- Introspection is last-wins and windows are unproven: a five-root operation exposes only the last-published plan (completion-order dependent under async), and the window gate passes a consumer join that multiplies child rows — corrupting `totalCount`, page boundaries, and next-page flags.

#### Dependencies

- Gated on the substrate landing first: `EdgeScope` supplies the visibility-scoped child base the sidecar pipeline normalizes, `RowIdentityProof` is the vocabulary the window gate enforces, `FieldDependencyPlan` feeds the template's dependency graph, and the operation memo is the request-local tier the binding reuses.

#### Note

- `docs/SPECS/spec-068-structural_templates-0_1_6.md` is the card's spec of record (written; five slices planned).
- **Spec-of-record obligation carried in from the spec-033 residual cycle: the nested-connection fetch-strategy seam has no owning spec, and that is a root cause, not a loose end.** No file under `docs/SPECS/` takes the seam as its subject, so nine later commits reshaped `spec-033`'s shipped contracts with nothing forcing its record to follow - `57cbd32a`, `9580e84e`, `51421e54`, `6912ca92`, `991d5120`, `deeb53b4`, `de2601e9`, `841e56d6`, `567cc6d0` - and every attribution in that cycle had to be by COMMIT rather than by card. Three of that card's contracts silently inverted post-ship as a result. `CHANGELOG.md`'s `0.0.14` "Pluggable nested-connection fetch-strategy seam" bullet is currently the seam's ONLY standing-doc record anywhere. `docs/SPECS/spec-068-structural_templates-0_1_6.md` must therefore claim the ALREADY-SHIPPED seam - the three backends, the runtime single-parent fast path, the strategy-refusal arm - and not only the new machinery this card adds, or the same silent inversion recurs against a second spec. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- **Slice 4 additionally owns the strictness diagnostic for refused windows.** `django_strawberry_framework/types/resolvers.py::_check_n1` answers "the fast-path `to_attr` is present on `root`", not "the window was actually consumed": it re-derives from the attribute an answer `connection.py::_build_relation_connection_resolver` computed one branch earlier and discarded, so **three refusal arms read as "served" and `"raise"` stays silent on a real per-parent query.** Demonstrated with a 3-row temp test, not argued. No data-correctness impact - only the diagnostic goes quiet. **It is a contract change, not a bug fix:** `spec-033` Decision 8 states the condition as "the fast-path `to_attr` is absent on `root`", so the shipped code is correct against its spec and the shipped probe is the one Decision 8 prescribes. Recommended direction is to thread the resolver's already-computed boolean rather than re-derive it. Lands naturally with this card's row-identity gate, which introduces the targeted refusal error this diagnostic should ride. Measured 2026-08-27 by the spec-033 residual reconciliation cycle (`docs/builder/DONE/build-033-connection_optimizer-0_0_9.md`, whose folded-in deferred-work catalog carries the full measurement).
- Claims the spec-033 Decision-6 deferral 'Windowed planning for sidecar-filtered nested connections' (docs/SPECS/spec-033-connection_optimizer-0_0_9.md, Deferred list: 'no card yet, surfaced for the maintainer at wrap time') - Slice 3's `_divergent_key_windows` planning of argument-bearing response keys is that design surface; spec-068 must record the claim so the archived spec's deferral has a named home.

#### Card references

- Dependency: Gated on the substrate landing first: `EdgeScope` supplies the visibility-scoped child base the sidecar pipeline normalizes, `RowIdentityProof` is the vocabulary the window gate enforces, `FieldDependencyPlan` feeds the template's dependency graph, and the operation memo is the request-local tier the binding reuses. -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning
- Related: Amendment obligation: explain renders the operation plan map (every root exactly once, shared dependencies with hit counts, redacted scope values) and retires the legacy last-wins `DST_OPTIMIZER_PLAN` context key. -> `TODO-BETA-069-0.1.6` - Optimizer explain mode
- Related: Amendment obligation: the adversarial suite gains structural-template targets (template-store keying/under-keying, the structural/bound binding boundary, proof-gate refusal paths, sidecar cache isolation). -> `TODO-BETA-072-0.1.8` - Adversarial non-live test suite

<a id="optimizer_explain_mode"></a>
### [TODO-BETA-069-0.1.6 - Optimizer explain mode](KANBAN.html#optimizer_explain_mode)

- Priority: High
- Status: To Do
- Relative size: M
- Labels: `debugging`, `developer-tools`, `graphql-api`, `optimizer`, `performance`, `query-planning`

#### Predicted files

- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`examples/fakeshop/test_query/`](examples/fakeshop/test_query/)
- [`tests/optimizer/`](tests/optimizer/)

#### Planning note

Promoted from BACKLOG.md item 7 as a pre-1.0 differentiator: expose the optimizer plan already stashed on the GraphQL context as an opt-in response-extension payload so consumers can see exactly what the Django ORM optimizer planned for a request.

#### Dependencies

- `TODO-BETA-068-0.1.6` - Structural optimization templates and nested sidecar batching

#### Scope

- Add an opt-in Strawberry response extension for optimizer explain output, exposed through the GraphQL response `extensions` map under a stable package-owned key.
- Serialize the existing `info.context.dst_optimizer_plan` data into a JSON-safe payload instead of re-planning the query.
- Include the ORM planning facts developers need to debug performance: `select_related`, `prefetch_related` / `Prefetch` chains, `only()` projection, optimizer hints, FK-id elisions, and strictness decisions where available.
- Provide a request-level activation surface such as a header or context flag; keep explain output off by default.
- Guarantee explain mode is observational only: enabling it must not change SQL planning, resolver behavior, GraphQL data shape, or query results.
- **Consume-the-substrate amendment** (TODO-BETA-058-0.1.1, TODO-BETA-068-0.1.6): render the operation plan map instead of the single last-wins `info.context.dst_optimizer_plan`, and retire that legacy context key once this card lands (the sibling card publishes the map alongside it precisely so this card owns the cutover). Each entry exposes root field / type / model, structural template fingerprint and cache hit or miss, request binding identity without secret values, select / prefetch / computed dependencies, direct and correlated predicate branches, contextual edge scopes, nested strategy and sidecar plan, row-identity proof, fallback reasons, estimated query families, strictness keys, database alias, and whether total count and page share a statement. Shared operation dependencies appear once with redacted keys and hit / miss counts; the map stays complete and deterministic under any async completion order.

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

#### Note

- Original backlog score: Realistic 10/10, Impact 8/10, Difficulty 2/10; bang-for-buck score 40.0.

#### Card references

- Related: Amendment source: the graph substrate ships the shared planning vocabulary this card must consume instead of reimplementing (spec-058 Decision 1 — the amendment lands at the substrate card's creation, not at its Slice 5). -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning
- Dependency: Amendment source: the sibling foundation card ships the structural/bound plan split, the operation plan map, and the row-identity enforcement gate this card consumes. -> `TODO-BETA-068-0.1.6` - Structural optimization templates and nested sidecar batching

<a id="configurable_filterlogic_key_namespace_filter_keyand_keyor_keynot_key"></a>
### [TODO-BETA-070-0.1.7 - Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`)](KANBAN.html#configurable_filterlogic_key_namespace_filter_keyand_keyor_keynot_key)

- Priority: Low
- Parity: ⚛️ graphene-django (Required)
- Status: To Do
- Relative size: M
- Labels: `config`, `filters`, `public-api`

#### Predicted files

- [`django_strawberry_framework/conf.py`](django_strawberry_framework/conf.py)
- [`django_strawberry_framework/filters/inputs.py`](django_strawberry_framework/filters/inputs.py)
- [`django_strawberry_framework/filters/sets.py`](django_strawberry_framework/filters/sets.py)
- [`django_strawberry_framework/utils/connections.py`](django_strawberry_framework/utils/connections.py)

#### Planning note

Promoted from BACKLOG.md as the remaining django-graphene-filters configuration-parity gap: recreate the configurable filter-tree key namespace — `DJANGO_GRAPHENE_FILTERS` `FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY` (`django_graphene_filters/conf.py:13-16`, defaults `filter`/`and`/`or`/`not`). The package currently hardcodes the GraphQL names (`_LOGIC_KEYS` at `filters/inputs.py:131`, `CONNECTION_FILTER_KWARG` at `utils/connections.py:41`); this card makes them settings-driven while keeping the defaults and the default SDL byte-for-byte unchanged.

#### Dependencies

- `DONE-027-0.0.8` - Filtering subsystem
- `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)

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

- This recreates the one DGF filtering configuration surface with no package analogue. The fixed wire names were a deliberate simplification; this card makes them configurable behind settings while keeping the defaults — and the byte-for-byte default SDL — unchanged. The cost is moving `_LOGIC_KEYS` off the import-time fast path to a settings-resolved value; the spec pins the resolution point so import ordering stays correct. It does not change the default schema and only the GraphQL wire names are configurable — the Python attribute names stay fixed.

#### Why it matters

- Closes the remaining django-graphene-filters configuration-surface gap: `DJANGO_GRAPHENE_FILTERS` `FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY` has no package analogue.
- Lets a django-graphene-filters consumer who renamed their filter-tree keys (e.g. to avoid clashing with an existing `filter`/`and`/`or`/`not` model field) migrate without a breaking schema rename.

#### Dependencies

- `DONE-027-0.0.8` (Filtering subsystem) — owns `_LOGIC_KEYS` and the filter-tree input-type generation whose wire names this card makes configurable.
- `DONE-030-0.0.9` (`DjangoConnectionField`) — owns the `filter` argument (`CONNECTION_FILTER_KWARG`) that `FILTER_KEY` renames.

#### Note

- Sole card on the `0.1.7` line: owns the `0.1.7` cut - version quintet and CHANGELOG entry (under the maintainer's explicit grant).

#### Card references

- Dependency: `DONE-027-0.0.8` (Filtering subsystem) — owns `_LOGIC_KEYS` and the filter-tree input-type generation whose wire names this card makes configurable. -> `DONE-027-0.0.8` - Filtering subsystem
- Dependency: `DONE-030-0.0.9` (`DjangoConnectionField`) — owns the `filter` argument (`CONNECTION_FILTER_KWARG`) that `FILTER_KEY` renames. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)

<a id="migration_and_adoption_guides"></a>
### [TODO-BETA-071-0.1.8 - Migration and adoption guides](KANBAN.html#migration_and_adoption_guides)

- Priority: Medium
- Status: To Do
- Relative size: L
- Labels: `docs`, `guides`, `public-api`

#### Dependencies

- `TODO-BETA-070-0.1.7` - Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`)

#### Scope

- Add a `graphene-django` migration guide covering `DjangoObjectType` to `DjangoType`, enum/field conversion differences, query optimizations, and Relay caveats.
- Add a `strawberry-graphql-django` migration guide covering decorator-to-`Meta` translation, optimizer differences, `get_queryset`, and optimizer hints.
- Add concise notes for DRF / django-filter users mapping serializers/filtersets/orders into the planned Layer 3 surfaces.
- Decide whether the cookbook migration recipe should name `DjangoSchema` rather than plain `strawberry.Schema`. The cookbook port is query-only, so plain `Schema` is correct as written, but a reader who later adds a generated mutation hits the write pipeline refusing to run under it. Changing the recipe changes spec-044 migration story, which is why it was left.
- Document the choice-enum member-name collision as a hard build break in the `graphene-django` guide: upstream dedups two choice values that sanitize to the same enum member by appending a positional suffix derived from how many names it has already converted, so the client-visible member name is a function of `choices` declaration order; `django_strawberry_framework/types/converters.py::build_enum_from_choices` instead raises `ConfigurationError` naming both colliding values. A model that builds under `graphene-django` fails to build here, at type-creation time and before any query runs, so the guide must name the fix: rename one side or split the field.
- Document the choices-to-enum default in both guides: `graphene-django` converts choice columns to enums by default but ships the global `DJANGO_CHOICE_FIELD_ENUM_CONVERT` switch plus a per-type `convert_choices_to_enum` opt-out, and `strawberry-graphql-django` leaves choice columns as raw scalars by default behind `GENERATE_ENUMS_FROM_CHOICES`; here `django_strawberry_framework/types/converters.py::convert_choices_to_enum` always generates the enum and there is no global or per-type opt-out at all. For a `strawberry-graphql-django` migrant that is a whole-schema difference on every choice column; for a `graphene-django` migrant it hits every column the opt-out had covered. The only opt-out here is a consumer-authored annotation on that column, so the guide states the default once up front rather than field by field.
- Document the accepted request content types beside the UTF-8 wire-contract note: `graphene-django`'s view also parses `application/graphql` bodies and `application/x-www-form-urlencoded` / `multipart/form-data` form posts, and honours a `?pretty` query parameter on the response; this package accepts `application/json` only, plus `multipart/form-data` when the view is constructed with `multipart_uploads_enabled`. Anything else is a 400 'Unsupported content type' from the engine before the document is parsed, so a migrant reusing a `graphene-django` curl recipe or client sees the request rejected rather than executed, and response formatting is the client's job here.
- Document mutation atomicity in the `graphene-django` guide: upstream's `ATOMIC_MUTATIONS` is opt-in and off by default, settable globally or per database through the `DATABASES` entry, whereas `django_strawberry_framework/schema.py::DjangoMutationExecutionContext` holds every generated top-level mutation's transaction open through response completion unconditionally, with no setting that turns it off. Ours is the stronger guarantee, but the setting name and the opt-in to always-on flip are stated nowhere, so the migrant searching for `ATOMIC_MUTATIONS` needs one sentence saying it no longer exists and why.
- Map upstream's per-field manager and page-cap knobs onto their analogs here: `graphene-django`'s `on="manager"` picks a named model manager for a list or connection field and its per-field `max_limit=` caps page size (`strawberry-graphql-django` spells the same cap `max_results=`). Here the manager choice is a consumer resolver or `get_queryset` returning a `Manager`, which is coerced to a queryset, and the cap is the schema-wide `max_list_rows` on `django_strawberry_framework/resource_policy.py::ResourcePolicy`. The note must say that `django_strawberry_framework/list_field.py::DjangoListField` caps SILENTLY - `django_strawberry_framework/resource_policy.py::bounded_rows` slices the result, so an over-large request returns a short page with no error, where `graphene-django` asserts `first <= max_limit` and errors.
- Add a one-line dataloader note to both guides: `strawberry.dataloader` ships with the engine and is available unchanged, so a migrant's existing dataloaders keep working, but this package's own answer to N+1 is the query optimizer plus strictness rather than a dataloader layer. One line only here; the fuller GLOSSARY / README statement belongs to the alpha documentation-debt card.
- Document the unregistered relation target as the loudest migration break, because it is the first thing many migrants hit: `graphene-django` silently drops a relation whose target model has no registered type (its `dynamic_type` returns `None`) and `strawberry-graphql-django` falls back to a `pk`-only `DjangoModelType`, while `django_strawberry_framework/types/finalizer.py::_format_unresolved_targets_error` raises `ConfigurationError` at finalization listing every unresolved target. The guide must say the failure is deliberate, not a bug, and name the two fixes - declare a `DjangoType` for the target model, or exclude the field.
- Name `DurationField` as a graphene-django migration break: `graphene_django/converter.py::convert_field_to_float` registers `models.DurationField` alongside `models.FloatField`, so a migrant's duration column shipped as a `Float` of seconds, and here it raises `ConfigurationError` at type creation until the consumer registers a scalar through `django_strawberry_framework/types/converters.py` #"SCALAR_MAP". That is the deferred-scalar posture and it is deliberate - a bare `Float` loses the unit, and a consumer who needs a duration on the wire is better served choosing the representation than inheriting seconds-as-float by default - so the guide's job is to name `Float` as what they are replacing, which makes the fix mechanical. Verified against both reference trees 2026-08-28: this is single-upstream, `strawberry-graphql-django` has no `DurationField` handling at all. Do NOT extend the note to `BinaryField`: `graphene_django` has no `BinaryField` registration and no `Base64` reference anywhere in the package (`graphene.Base64` exists in graphene core, but nothing wires it to the field), so `BinaryField` raising here is not a divergence from either upstream.
- Give both guides an upstream-settings disposition table, because a migrant's first move is to search for the key they used to set and silence reads as a bug rather than a decision. Four config surfaces have no equivalent here and each owes one line saying so and why. (a) `strawberry-graphql-django`'s `TYPE_DESCRIPTION_FROM_MODEL_DOCSTRING` (`strawberry_django/settings.py`, default `False`) publishes the model docstring as the GraphQL type description; here it is `Meta.description`, defaulting to the `DjangoType`'s own docstring, and the setting is not reproduced because Django synthesizes a `Model(field, field, ...)` docstring for every model that does not define one - so upstream's setting publishes a generated field list for exactly the models nobody documented. (b) `graphene-django`'s four GraphiQL knobs `SUBSCRIPTION_PATH`, `GRAPHIQL_HEADER_EDITOR_ENABLED`, `GRAPHIQL_SHOULD_PERSIST_HEADERS` and `GRAPHIQL_INPUT_VALUE_DEPRECATION` (`graphene_django/settings.py`) configure a development IDE the package does not own; here the engine's IDE is selected per mount with the inherited `graphql_ide=` keyword on `django_strawberry_framework/views.py::DjangoGraphQLView`, and `SUBSCRIPTION_PATH` is structurally moot because the WebSocket route is the router's `websocket_url_pattern`, not a hint rendered into HTML. (c) `graphene-django`'s `MAX_VALIDATION_ERRORS` caps how many validation errors a rejected document reports; here `django_strawberry_framework/resource_policy.py::ResourcePolicy` bounds the document BEFORE validation runs rather than truncating the report afterwards. (d) `strawberry_django/extensions/django_validation_cache.py::DjangoValidationCache` caches validation verdicts in a Django cache backend; there is no equivalent and it is refused rather than merely absent - a poisoned entry in a shared cross-process store is a schema-wide correctness failure rather than a slow request, and upstream documents its own default key function as unsafe for memcached. The in-process plan cache covers the performance need; document-level parse/validation reuse is the post-`1.0.0` `operation_document_and_plan_cache` row in `BACKLOG.md`, deliberately a bounded per-process LRU. All four verified against the reference trees 2026-08-28.
- Document the two `strawberry-graphql-django` mutation write surfaces that do not exist here, in that guide's write chapter. FIRST, filter-selected bulk update / delete: upstream's `strawberry_django/mutations/fields.py::DjangoUpdateMutation.instance_level_update` writes a predicate-selected row set, gated by `ALLOW_MUTATIONS_WITHOUT_FILTERS` (`strawberry_django/settings.py`, default `False`). Here the generated write pipeline's guarantee is locate-one then lock then authorize then attest, and a predicate-selected row set carries none of the four - which is why upstream needed a settings-level safety valve to make the shape survivable at all. The migration is one row per operation, located through the target type's `get_queryset`; a genuine bulk write becomes a consumer-authored mutation owning its own authorization story. SECOND, `through_defaults`: upstream's `strawberry_django/mutations/resolvers.py::update_m2m` writes intermediate-table columns through a relation input, which here would make a relation argument silently responsible for rows in a third table and contradicts the replace-only M2M contract. The migration is a consumer-authored mutation over the through model itself, an ordinary model with an ordinary write surface. Both verified against the reference checkout 2026-08-28.
- Document the per-field permission ladder as the largest single `strawberry-graphql-django` translation - it is that library's most-used surface and nothing here replaces it field-for-field. Upstream ships `strawberry_django/permissions.py::DjangoPermissionExtension` with `IsAuthenticated`, `HasPerm`, `HasSourcePerm` and `HasRetvalPerm` applied per field as Strawberry extensions. Here the read side is `get_queryset` for row visibility plus `django_strawberry_framework/permissions.py::apply_cascade_permissions` for its transitive closure, and the write side is `Meta.permission_classes`. The guide must say WHY the shape is not reproduced, not only that it is absent: upstream's `fail_silently` degradation chain resolves a denial to `None`, `[]`, an empty queryset or `OperationInfo` depending on the return type, so an authorization outcome depends on schema shape and a denial becomes indistinguishable from an empty result - the opposite of this package's fail-loud posture. Scope boundary for whoever writes this: the decorator SHAPE is refused permanently, but the read-side CAPABILITY is only deferred, and the beta parity claim's carve-out for it already lives on the beta release card. This guide item states the translation; it must not restate the carve-out.
- Document the mutation error-payload shape change in the `strawberry-graphql-django` guide, because it breaks client documents rather than server code. Upstream returns errors as a member of the payload union (`OperationInfo` in `strawberry_django/mutations/fields.py`), so every mutation's success type is conditional on the client selecting the right branch, and a client that omits the error branch silently receives an empty selection instead of a failure. Here the payload shape is fixed and errors arrive in the `FieldError` envelope, always in the same place. The migration is mechanical but touches every mutation document a migrant ships: drop the `... on OperationInfo` inline fragment and select the `errors` field instead. The argument for the fixed shape is in `docs/SPECS/spec-036-mutations-0_0_11.md`.
- Document the batched-request response shape in the `graphene-django` guide: upstream's `graphene_django/views.py::GraphQLView.get_response` wraps each batched operation in a synthetic per-entry `id` / `status` envelope and collapses the HTTP status to the maximum across entries, so one failing operation changes the status seen for every sibling. Here batching is the engine's own, enabled per schema through Strawberry's `batching_config` and OFF by default, and an enabled batch returns a plain JSON array under one status with no synthetic envelope. The guide must name both halves - the response shape change AND that batching has to be turned on at all - because a migrant whose client batches gets a flat 400 "Batching is not enabled" on the first request rather than a shape difference to notice later.

#### Definition of done

- [ ] New docs are added for the two major migration paths.
- [ ] README and `GLOSSARY.md` link to the migration docs.
- [ ] Guides distinguish shipped migration steps from planned Layer 3 migration targets.

#### Files likely touched

- future migration docs under `docs/`
- `docs/README.md`
- `docs/GLOSSARY.md`

#### Note

- docs-only but substantial: two full migration guides (graphene-django → and strawberry-graphql-django →) plus DRF / django-filter mapping notes, with README / GLOSSARY links. No code.
- The package is intentionally shaped for teams coming from `django-filter`, DRF, `graphene-django`, and `strawberry-graphql-django`.
- The feature docs explain the positioning, but there are no dedicated migration guides yet.
- No version quintet or CHANGELOG entry - the `0.1.8` release state is owned by the adversarial-suite card's joint cut, which lands last on the line.

#### Card references

- Dependency: The final configurable filter/logic key namespace (`TODO-BETA-070-0.1.7`) must ship first so both migration guides describe the released public surface. -> `TODO-BETA-070-0.1.7` - Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`)

<a id="adversarial_non_live_test_suite"></a>
### [TODO-BETA-072-0.1.8 - Adversarial non-live test suite](KANBAN.html#adversarial_non_live_test_suite)

- Priority: Medium-high
- Status: To Do
- Relative size: L
- Labels: `adversarial-testing`, `hardening`, `tests`

#### Predicted files

- [`examples/fakeshop/test_query/README.md`](examples/fakeshop/test_query/README.md)
- [`tests/`](tests/)

#### Dependencies

- `TODO-BETA-068-0.1.6` - Structural optimization templates and nested sidecar batching
- `TODO-BETA-070-0.1.7` - Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`)

#### Scope

- Hostile wire values: bad-base64 / wrong-`type_name` GlobalIDs, oversized `in` lists, unicode / emoji / null bytes, `strawberry.UNSET` / `None` across every operator-bag slot.
- Add a row distinguishing `consumers.py::_attempt_close`'s `ABANDONED` record from `settle`'s cancel-and-await. The two boundaries are currently jointly pinned - the same pair of rows fails for either mutation - so neither is independently proven.
- `tests/test_views.py::_strawberry_patch_opted_out` lacks the live copy's `assert strawberry_patches._patch_is_installed() is False`, so nothing pins that the package-tier simulation really un-installed the patch.
- Re-anchor failability manifest entry 6 onto the middleware-ordering audit's decision expression rather than its initialization line, if the manifest is ever re-derived. Anchoring an aggregate inside the guard under test is the trap: one measured attempt reported four rows rather than zero, which would have passed the acceptance rule while measuring a third of its boundary. A zero gets graded; a plausible count gets graded by nobody.
- Pin `optimizer/hints.py::OptimizerHint.prefetch`'s interaction with a target type's custom `get_queryset`. A consumer-supplied `Prefetch` is used verbatim, so the hinted child queryset bypasses `utils/querysets.py::apply_type_visibility_sync` - deliberate, per `optimizer/walker.py::_apply_hint`, and unpinned in either direction (`tests/optimizer/test_hints.py` contains no `get_queryset` occurrence). An unpinned deliberate divergence on a data-isolation path is indistinguishable from a bug to the next reader, and is exactly what a future refactor can "fix" silently. Two rows close it, one a positive control.
- **Consume-the-substrate amendment** (TODO-BETA-058-0.1.1, TODO-BETA-068-0.1.6): add graph-substrate and structural-template attack targets — five-root operations; related-row existence leaks; selected-child leakage past a visible parent; same-related-row authorization false positives; custom-visibility outer fan-out; duplicate child rows under windows; whole-operation cache fragmentation; operation-memo scope isolation (viewer, tenant, database alias, cancellation); async plan-map ordering; structural-template under-keying (a referenced directive or pagination slot missing from the fingerprint must fail closed to a walk, never to a wrong reuse); the structural/bound binding boundary (no request value constructible into a structural object); proof-gate refusal paths; and snapshot consistency in the PostgreSQL tier.
- `tests/types/test_definition_order.py::test_filterset_class_resolves_across_module_boundary`'s module eviction is weaker than its comment claims. The row pops two fixture modules from `sys.modules` and re-imports them with `from tests.types.fixtures import branch_module, shelf_module`, under a comment asserting the pop makes the next import re-execute the module. Measured by the spec-010 residual cycle (2026-08-15): it does not - the parent package's still-set attribute satisfies the `from ... import`, so the stale module object comes back and `sys.modules` is never repopulated. The row passes today only because nothing imports those fixture modules first, a latent order dependence of exactly the class invisible below a full parallel run. The fix is one `importlib.import_module` per module plus a corrected comment - the same substitution that cycle's builder was forced into for its own rows, which is how the weakness was found.
- `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver` does NOT pin the collection-phase consumer-authored short-circuit - never cite it as though it does. Measured twice in the spec-010 residual cycle, by the builder's and the reviewer's failability runs independently: with the relation branch of the short-circuit in `types/base.py::_build_annotations` deleted, every assertion in that row still passes, because the synthesized placeholder resolves back to the same class and the row's `consumer_*` set assertions read state computed in `__init_subclass__` rather than in `_build_annotations`. The short-circuit is pinned instead by the four override-shape rows that cycle landed in the same file. If a discriminating assertion is ever wanted, it must observe `_build_annotations`' own effect (pending-relation suppression), not the resolved schema, which is identical either way.
- Add a `FAKESHOP_SHARDED`-gated row asserting the `.db` alias of a `Prefetch` child built under an active cascade. `tests/optimizer/test_multi_db.py` has **zero** `cascad` occurrences and no sharded file exercises the cascade inside a prefetch child, so the alias-late routing the package performs there is asserted nowhere. **Not a skipped contract** - `spec-034` pins nothing for that bullet - which is exactly why it belongs in an adversarial pass rather than in a conformance repair. The documentation half of the same seam is already owned by `TODO-ALPHA-056-0.0.17`'s `Multi-database cooperation` glossary item; this is the executable half. Recorded 2026-08-28 by the spec-034 residual cycle (R1b finding L2).

#### Definition of done

- [ ] A dedicated adversarial suite under `tests/` exercises the categories above; every hostile input fails LOUDLY with a typed error rather than crashing.
- [ ] Root `tests/` holds only genuinely-unreachable-from-live cases plus the new adversarial ones; any remaining live-reachable duplicates are pruned (per `examples/fakeshop/test_query/README.md`).
- [ ] Coverage stays at 100% without relying on the pruned duplicates.

#### Files likely touched

- new adversarial test modules under `tests/`
- `examples/fakeshop/test_query/README.md` (cross-reference the adversarial-vs-unreachable split)

#### Why it matters

- `fail_under = 100` proves every LINE executes, not that the code is CORRECT under abuse. The failures that matter — deeply nested logic trees, malformed / wrong-`type_name` GlobalIDs, cyclic `RelatedFilter` graphs, conflicting multi-owner reuse, UNSET/None permutations, oversized `Meta.fields = "__all__"` expansions, unicode / null-byte / oversized values — are exactly the ones a happy-path live query never exercises.

#### Note

- An in-process `tests/` (NON-`/graphql/`) hardening pass whose goal is to BREAK the framework, not to earn line coverage. Live-reachable coverage already lives in `examples/fakeshop/test_query/` per its README rule; the root `tests/` tree is reserved for cases a live query cannot reach — fill it with hostile / pathological inputs rather than coverage duplicates.
- Root `tests/` historically mixed genuinely-unreachable-from-live cases with some that merely duplicated coverage already earned by the live `test_query/` suites (a first prune of redundant filter unit tests landed alongside `DONE-027-0.0.8`).
- There is no deliberate "try to break it" suite; adversarial inputs are covered only incidentally.
- Property-based / fuzz-style tests (e.g. Hypothesis) for the filter input normalizer, GlobalID decode/validate, and `Meta.fields = "__all__"` expansion.
- Pathological structure: logic-tree nesting past `_MAX_LOGIC_DEPTH`, cyclic / self-referential `RelatedFilter` graphs, conflicting multi-owner reuse, proxy / MTI model mixing.
- Scale / resource: very large `"__all__"` field sets and many-relation BFS; assert every failure surfaces as `ConfigurationError` / `GraphQLError` (never a bare traceback) and finalize stays bounded.
- Extend the same philosophy to the future order / aggregate / fieldset subsystems as they land.
- Owns the joint `0.1.8` cut: the version quintet and the CHANGELOG entry (under the maintainer's explicit grant) land here for both `0.1.8` cards; this card lands last on the line.

#### Card references

- Related: Root `tests/` historically mixed genuinely-unreachable-from-live cases with some that merely duplicated coverage already earned by the live `test_query/` suites (a first prune of redundant filter unit tests landed alongside `DONE-027-0.0.8`). -> `DONE-027-0.0.8` - Filtering subsystem
- Dependency: The final configurable filter/logic key namespace (`TODO-BETA-070-0.1.7`) must ship first so the adversarial suite exercises the released public surface before the stable gate. -> `TODO-BETA-070-0.1.7` - Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`)
- Related: Amendment source: the graph substrate ships the shared planning vocabulary this card must consume instead of reimplementing (spec-058 Decision 1 — the amendment lands at the substrate card's creation, not at its Slice 5). -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning
- Dependency: Amendment source: the sibling foundation card ships the structural/bound plan split, the operation plan map, and the row-identity enforcement gate this card consumes. -> `TODO-BETA-068-0.1.6` - Structural optimization templates and nested sidecar batching

<a id="stable_release_api_freeze_cleanup_verification_beta_stable"></a>
### [TODO-STABLE-073-1.0.0 - Stable release (API freeze, cleanup, verification, beta → stable)](KANBAN.html#stable_release_api_freeze_cleanup_verification_beta_stable)

- Priority: Critical
- Status: To Do
- Relative size: L
- Labels: `cleanup`, `release`, `stable-api`, `tests`

#### Predicted files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`tests/base/test_init.py`](tests/base/test_init.py)

#### Planning note

planned; this is the final card in the Beta queue and gates the beta → stable milestone

#### Dependencies

- `TODO-BETA-072-0.1.8` - Adversarial non-live test suite

#### Definition of done

- [ ] Every other Beta card (`TODO-BETA-058-0.1.1` through `TODO-BETA-072-0.1.8`) is in `DONE`.
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

#### Note

- the heaviest release card: API freeze + `__all__` audit, a security review of every input surface (mutations / filters / GlobalID decoding), full async + sync matrix, version bump to `1.0.0`, CHANGELOG, backlog refresh, tag + publish + announcement.

#### Card references

- Related: Every other Beta card (`TODO-BETA-058-0.1.1` through `TODO-BETA-072-0.1.8`) is in `DONE`. -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning
- Related: Every other Beta card (`TODO-BETA-058-0.1.1` through `TODO-BETA-072-0.1.8`) is in `DONE`. -> `TODO-BETA-072-0.1.8` - Adversarial non-live test suite
- Dependency: The final Beta card discharges before the `1.0.0` cut - the dependency edge replaces prose, mirroring the beta release card's edge on the doc-debt card. -> `TODO-BETA-072-0.1.8` - Adversarial non-live test suite

<a id="dynamic_schemas_from_datatype_specs_synthetic_unmanaged_models"></a>
### [TODO-STABLE-074-1.1.0 - Dynamic schemas from dataType specs (synthetic unmanaged models)](KANBAN.html#dynamic_schemas_from_datatype_specs_synthetic_unmanaged_models)

- Priority: Low-medium
- Status: To Do
- Relative size: L
- Labels: `metadata`, `public-api`, `schema`, `types`

#### Planning note

Created 2026-08-29 from the DIV-033 discussion. Post-1.0 greenfield: neither graphene-django nor strawberry-graphql-django has anything like it. Depends on the pluggable field-conversion registry; the chosen shape (compile specs into synthetic unmanaged Django models) was picked over a model-free converter path because it rides the entire existing pipeline instead of forking one.

#### Dependencies

- `TODO-ALPHA-054-0.0.16` - Pluggable field-conversion registry

#### Scope

- A dataType-spec compiler: a declarative description of fields and relations (the 'set of dataTypes') is compiled at setup time into synthetic unmanaged Django model classes (type(name, (models.Model,), attrs) with Meta.managed = False and db_table pointed at an existing or external table), which then feed the unchanged DjangoType pipeline - converters, choice enums, FilterSets, ordering, optimizer, visibility, connections - so a dynamic schema gets every framework guarantee a hand-written model gets.
- Spec field entries resolve through the pluggable field-conversion registry, so consumer-registered and callable converters work identically for synthetic and hand-written models.
- Compiler discipline: a keyed cache so repeated compilation of the same spec returns the same model class (dynamic model creation registers in Django's app registry; per-request re-creation leaks), a stable dedicated app_label for synthetic models, and a defined error surface (ConfigurationError) for invalid specs.
- Non-goal: schema mutation at request time. Specs are read at setup/import time; a changed spec is a process restart, exactly like an edited models.py.

#### Definition of done

- [ ] Compiler + keyed cache + stable app_label shipped with ConfigurationError coverage for invalid specs.
- [ ] A worked example against an external/unmanaged table (fakeshop or a docs recipe) proving filters, ordering, and the optimizer run unmodified over a synthetic model.
- [ ] Documentation of the setup-time-only contract and the spec format.

#### Why it matters

- The framework already reverse-engineers a GraphQL schema from model inputs; this closes the loop for sources that have a table shape but no models.py - external/legacy databases, inspectdb-style integration, multi-tenant column catalogs - without forking a second conversion path.

#### Dependencies

- Spec field entries resolve through the registry; the registry's callable-converter shape must be settled first.

#### Open question

- Ownership story: where dataType specs live (Python dicts, a settings entry, a file format), who validates them, and what the migration posture is when a spec changes shape against a live table.
- Relation entries between two synthetic models vs a synthetic model and a real one - the FK target resolution order needs a rule before the compiler exists.

#### Card references

- Dependency: Spec field entries resolve through the registry; the registry's callable-converter shape must be settled first. -> `TODO-ALPHA-054-0.0.16` - Pluggable field-conversion registry
- Related: Same DIV-033 discussion; a geo-bearing external table would exercise both cards. -> `BACKLOG-STABLE-076-1.1.0` - GIS / GeoDjango field-type support (geo scalars)

## Done

Shipped cards, newest first. Each retains its spec link, parity claims, and completion evidence; the WIP / DONE spec map indexes card to spec file.

<a id="dependency_and_ci_hardening_refresh_django_locks_add_audit_automation_least_privilege_ci"></a>
### [DONE-049-0.0.14 - Dependency and CI hardening: refresh Django locks, add audit automation, least-privilege CI](KANBAN.html#dependency_and_ci_hardening_refresh_django_locks_add_audit_automation_least_privilege_ci)

- Priority: High
- Status: Done
- Relative size: M
- Labels: `internal`
- Spec: [spec-049-dependency_ci_hardening-0_0_14.md](docs/SPECS/spec-049-dependency_ci_hardening-0_0_14.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Hard dependency](docs/GLOSSARY.md#hard-dependency) | shipped |
| [Soft dependency](docs/GLOSSARY.md#soft-dependency) | shipped (`0.0.13`) |
| [`require_optional_module`](docs/GLOSSARY.md#require_optional_module) | shipped (`0.0.14`) |
| [Per-operation extension isolation](docs/GLOSSARY.md#per-operation-extension-isolation) | shipped (`0.0.14`) |
| [Live-first coverage mandate](docs/GLOSSARY.md#live-first-coverage-mandate) | shipped (`0.0.4`) |
| [Joint version cut](docs/GLOSSARY.md#joint-version-cut) | shipped (`0.0.13`) |

#### Planning note

Security-audit remediation program, card 4 of 4. S6 is independently time-sensitive and may be expedited at maintainer discretion.

#### Dependencies

- `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation

#### Scope

- uv.lock refresh (>=5.2.16 / >=6.0.7); keep + relabel the 5.2.0 compatibility cell.
- Dependency-audit + scheduled-security + auto-update workflows (pip-audit/dependabot shape).
- .github/workflows: least-privilege permissions, persist-credentials, SHA/digest pins, timeouts.
- Slice 5 doc fold-in landed DB-side at the release: the `Hard dependency` glossary entry now carries the secure-version statement - a declared floor is an API-compatibility bound frozen at release time, never advice about which version is safe to run - written into the fakeshop glossary DB and re-rendered with `scripts/build_glossary_md.py` rather than hand-edited into the generated file.
- The card shipped with no `SpecDoc` row, so `KANBAN.md` rendered it without a spec link. The row was seeded at the release, and the spec has since been archived, so the link resolves to `docs/SPECS/spec-049-dependency_ci_hardening-0_0_14.md` with its terms companion under `docs/SPECS/appx/`.
- `README.md`, `docs/README.md` and `TODAY.md` prose are hand-edited and were left for this card's DB-regeneration pass rather than done piecemeal.

#### Definition of done

- [ ] Locks refreshed to the patched Django releases; audit + auto-update automation added; CI runs least-privilege with immutable action/image pins and job timeouts.
- [ ] Governance files only (no package-source/SDL change, no coverage exposure); CI green.

#### Architectural posture

- Refresh uv.lock to at least Django 5.2.16 and 6.0.7 for their respective Python markers. KEEP the exact Django 5.2.0 compatibility CI cell but label it compatibility-only and never use it for deployment examples or security assertions -- compatibility support and secure-deployment support are different contracts.
- Add an automated dependency audit on pull requests and a scheduled run (audit the production resolution + optional extras; handle the intentional 5.2.0 compatibility environment separately); add automated update coverage for Python dependencies and GitHub Actions. State that production users must install the newest patch in their supported Django series; the Django>=5.2 floor is not a secure-version recommendation.
- CI least privilege: top-level permissions: contents: read, with only the exact additional grant to the one step/job that needs it; persist-credentials: false on every non-pushing checkout; pin every action to a reviewed full commit SHA (keep the readable version comment); pin the Postgres image by digest; add timeout-minutes to every networked/test job.

#### Why it matters

- S6 (High): uv.lock resolves Django 5.2.14 (py<3.12) and 6.0.5 (py>=3.12), but the Django project shipped security releases 5.2.16 and 6.0.7 (CVE-2026-48588, a shared-cache private-data exposure) plus 5.2.15/6.0.6 fixing five more issues in the currently locked versions. No dependency-audit command, scheduled security workflow, or update configuration exists.
- S7 (Medium): the test job grants contents: write though only the Coveralls upload consumes the token (which does not need repo-write); checkout persists its credential by default; first-party actions use mutable major tags and Postgres uses postgres:16; networked/test jobs have no timeout-minutes.

#### Dependencies

- Sequenced behind card 046 in the staged security program; S6 independently urgent.

#### Test plan

- The dependency audit runs on the production resolution + extras and handles the 5.2.0 environment separately; the refreshed lock still resolves the whole matrix.
- CI permission and pin assertions where mechanically testable; the exact 5.2.0 compatibility cell still proves API compatibility with the advertised floor.

#### Open question

- pip-audit vs safety vs osv for the audit step, and dependabot vs a scheduled uv upgrade job: the spec picks concrete tooling.
- Repository-level default token permissions (spec-049 Decision 3) is a GitHub settings change, not a file in the tree - maintainer action, and nothing in a build can verify it.
- `osv-scanner`'s inner image tag stays mutable (spec-049 Decision 4); pinning it would need a fork. Recorded in the spec's risks rather than fixed.
- The workflow `timeout-minutes` values are estimates, not measured p95s (spec-049 Decision 7).
- `CHANGELOG.md`'s `0.0.14` entry predates this program: it is dated 2026-07-20 and covers cards `DONE-041` through `DONE-044`, so none of the four security cards that target the same patch version appear in it. `AGENTS.md` reserves `CHANGELOG.md` to the maintainer, so closing that gap is maintainer action rather than a card task.

#### Card references

- Dependency: Sequenced behind card 046 in the staged security program; S6 independently urgent. -> `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation

<a id="secure_output_and_error_defaults_drop_file_path_fail_closed_debug_prod_error_policy"></a>
### [DONE-048-0.0.14 - Secure output and error defaults: drop file path, fail-closed debug, prod error policy](KANBAN.html#secure_output_and_error_defaults_drop_file_path_fail_closed_debug_prod_error_policy)

- Priority: High
- Status: Done
- Relative size: M
- Labels: `internal`
- Spec: [spec-048-secure_output_defaults-0_0_14.md](docs/SPECS/spec-048-secure_output_defaults-0_0_14.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`Meta.filesystem_path_fields`](docs/GLOSSARY.md#metafilesystem_path_fields) | shipped (`0.0.14`) |
| [`DjangoFilePathType`](docs/GLOSSARY.md#djangofilepathtype) | shipped (`0.0.14`) |
| [`DjangoImagePathType`](docs/GLOSSARY.md#djangoimagepathtype) | shipped (`0.0.14`) |
| [`ErrorPolicy`](docs/GLOSSARY.md#errorpolicy) | shipped (`0.0.14`) |
| [`DjangoErrorPolicyExtension`](docs/GLOSSARY.md#djangoerrorpolicyextension) | shipped (`0.0.14`) |
| [`DjangoFileType`](docs/GLOSSARY.md#djangofiletype) | shipped (`0.0.11`) |
| [`DjangoImageType`](docs/GLOSSARY.md#djangoimagetype) | shipped (`0.0.11`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) | shipped |
| [`Meta.nullable_overrides`](docs/GLOSSARY.md#metanullable_overrides) | shipped (`0.0.9`) |
| [`Meta.required_overrides`](docs/GLOSSARY.md#metarequired_overrides) | shipped (`0.0.9`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Specialized scalar conversions](docs/GLOSSARY.md#specialized-scalar-conversions) | shipped (`0.0.6`) |
| [`Upload` scalar](docs/GLOSSARY.md#upload-scalar) | shipped (`0.0.11`) |
| [Schema audit](docs/GLOSSARY.md#schema-audit) | shipped (`0.0.3`) |
| [`DjangoDebugExtension`](docs/GLOSSARY.md#djangodebugextension) | shipped (`0.0.14`) |
| [Developer-only debug posture](docs/GLOSSARY.md#developer-only-debug-posture) | shipped (`0.0.14`) |
| [Debug payload availability](docs/GLOSSARY.md#debug-payload-availability) | shipped (`0.0.14`) |
| [Debug SQL row](docs/GLOSSARY.md#debug-sql-row) | shipped (`0.0.14`) |
| [Debug exception row](docs/GLOSSARY.md#debug-exception-row) | shipped (`0.0.14`) |
| [Django debug-cursor capture](docs/GLOSSARY.md#django-debug-cursor-capture) | shipped (`0.0.14`) |
| [Reference-counted cursor coordinator](docs/GLOSSARY.md#reference-counted-cursor-coordinator) | shipped (`0.0.14`) |
| [Bounded query-log rollover](docs/GLOSSARY.md#bounded-query-log-rollover) | shipped (`0.0.14`) |
| [Async SQL-capture boundary](docs/GLOSSARY.md#async-sql-capture-boundary) | shipped (`0.0.14`) |
| [Masking-extension ordering](docs/GLOSSARY.md#masking-extension-ordering) | shipped (`0.0.14`) |
| [Response-extension merge semantics](docs/GLOSSARY.md#response-extension-merge-semantics) | shipped (`0.0.14`) |
| [Response-extensions debug middleware](docs/GLOSSARY.md#response-extensions-debug-middleware) | shipped (`0.0.14`) |
| [Debug-toolbar middleware](docs/GLOSSARY.md#debug-toolbar-middleware) | shipped (`0.0.14`) |
| [Graphene debug migration](docs/GLOSSARY.md#graphene-debug-migration) | shipped (`0.0.14`) |
| [Strawberry extension lifecycle](docs/GLOSSARY.md#strawberry-extension-lifecycle) | shipped (`0.0.14`) |
| [Per-operation extension isolation](docs/GLOSSARY.md#per-operation-extension-isolation) | shipped (`0.0.14`) |
| [Execution resource policy](docs/GLOSSARY.md#execution-resource-policy) | shipped (`0.0.14`) |
| [`ResourcePolicy`](docs/GLOSSARY.md#resourcepolicy) | shipped (`0.0.14`) |
| [`DjangoResourcePolicyExtension`](docs/GLOSSARY.md#djangoresourcepolicyextension) | shipped (`0.0.14`) |
| [`FieldError` envelope](docs/GLOSSARY.md#fielderror-envelope) | shipped (`0.0.11`) |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [`SerializerMutation`](docs/GLOSSARY.md#serializermutation) | shipped (`0.0.13`) |
| [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) | shipped (`0.0.11`) |
| [`DjangoModelFormMutation`](docs/GLOSSARY.md#djangomodelformmutation) | shipped (`0.0.12`) |
| [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) | shipped (`0.0.5`) |
| [`request_from_info`](docs/GLOSSARY.md#request_from_info) | shipped (`0.0.8`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [Probe URLconf](docs/GLOSSARY.md#probe-urlconf) | shipped (repository test pattern) |
| [`seed_data`](docs/GLOSSARY.md#seed_data) | shipped |
| [Live-first coverage mandate](docs/GLOSSARY.md#live-first-coverage-mandate) | shipped (`0.0.4`) |
| [Joint version cut](docs/GLOSSARY.md#joint-version-cut) | shipped (`0.0.13`) |
| [Single-upstream parity](docs/GLOSSARY.md#single-upstream-parity) | shipped |

#### Planning note

Security-audit remediation program, card 3 of 4.

#### Dependencies

- `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation

#### Scope

- converters.py: remove DjangoFileType.path from the default field set (name/size/url remain; opt-in path).
- extensions/debug.py: settings.DEBUG fail-closed gate + allow_unsafe_production ack + payload caps.
- schema.py: DjangoSchema production error policy (log + correlation id + stable message under DEBUG=False).

#### Definition of done

- [x] path removed from the safe default; debug extension fails closed under DEBUG=False with an explicit ack; DjangoSchema has a production error policy.
- [x] Full suite green at 100% coverage; hygiene clean; migration note + docs fold-in.

#### Architectural posture

- Remove path from the public generated type's safe default (default output limited to name/size/url). A filesystem path requires an explicit server-owned field or a loud Meta opt-in; do not mask path failures while still exposing successful absolute paths. Justified pre-1.0 compatibility break + migration note.
- DjangoDebugExtension fails closed when settings.DEBUG is false unless an explicit constructor acknowledgement (DjangoDebugExtension(allow_unsafe_production=True)); add the __init__ it currently lacks and preserve fresh-per-operation instances. Cap the number and serialized byte size of SQL and exception rows.
- DjangoSchema gets a first-class production error policy: under DEBUG=False, unexpected exceptions log server-side with a correlation identifier and return a stable, non-sensitive message; deliberate client-facing framework errors (validation envelopes, audited GraphQLError codes) retain their contract; consumer code may explicitly opt out.

#### Why it matters

- S5 (High): DjangoFileType.path returns FieldFile.path and its description says 'the absolute filesystem path'; DjangoImageType inherits it. Every generated file/image output offers clients a server-internal path (usernames, release dirs, container mounts, tenant layout) whenever the storage backend supports one.
- S8 (Medium): DjangoDebugExtension returns interpolated SQL values, exception messages/types, and traceback paths, and operates independently of settings.DEBUG -- a single production schema-list entry silently activates the disclosure. It has no __init__ today.
- S10 (Medium): DjangoSchema centralizes mutation integrity but offers no production error policy; unhandled resolver/hook exceptions return their literal message to clients unless the consumer adds MaskErrors or overrides process_errors.

#### Dependencies

- Sequenced behind card 046 in the staged security program (independent code).

#### Test plan

- Default SDL lacks path; remote-storage failures still degrade safely for retained fields; any explicit path opt-in is absent unless deliberately declared.
- DEBUG=False rejects the debug extension by default; the explicit acknowledgement works; fresh-instance isolation intact; payload limits truncate deterministically; the aggregate fakeshop schema stays debug-free.
- Error policy distinguishes parse/validation errors, audited client-safe GraphQL errors, permission denials, and unexpected resolver/hook exceptions; sync/async parity; the correlation id (not the sensitive original message) reaches the client.

#### Open question

- The opt-in shape for an explicit filesystem-path field (Meta key vs server-only field): the spec decides.
- Correlation-id format + where it is logged, and whether the stable client message is configurable: the spec pins it.

#### Card references

- Dependency: Sequenced behind card 046 in the staged security program (independent code). -> `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation

<a id="execution_resource_policy_central_budget_object_value_cardinality_walker"></a>
### [DONE-047-0.0.14 - Execution resource policy: central budget object + value-cardinality walker](KANBAN.html#execution_resource_policy_central_budget_object_value_cardinality_walker)

- Priority: High
- Status: Done
- Relative size: L
- Labels: `internal`
- Spec: [spec-047-resource_policy-0_0_14.md](docs/SPECS/spec-047-resource_policy-0_0_14.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Execution resource policy](docs/GLOSSARY.md#execution-resource-policy) | shipped (`0.0.14`) |
| [`ResourcePolicy`](docs/GLOSSARY.md#resourcepolicy) | shipped (`0.0.14`) |
| [`DjangoResourcePolicyExtension`](docs/GLOSSARY.md#djangoresourcepolicyextension) | shipped (`0.0.14`) |
| [Value-budget walker](docs/GLOSSARY.md#value-budget-walker) | shipped (`0.0.14`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`Meta.relation_shapes`](docs/GLOSSARY.md#metarelation_shapes) | shipped (`0.0.9`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [`DjangoNodesField`](docs/GLOSSARY.md#djangonodesfield) | shipped (`0.0.9`) |
| [`Upload` scalar](docs/GLOSSARY.md#upload-scalar) | shipped (`0.0.11`) |
| [Request-body cap](docs/GLOSSARY.md#request-body-cap) | shipped (`0.0.14`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter) | shipped (`0.0.8`) |
| [`filter_input_type`](docs/GLOSSARY.md#filter_input_type) | shipped (`0.0.8`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`SerializerMutation`](docs/GLOSSARY.md#serializermutation) | shipped (`0.0.13`) |
| [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) | shipped (`0.0.11`) |
| [`DjangoModelFormMutation`](docs/GLOSSARY.md#djangomodelformmutation) | shipped (`0.0.12`) |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |
| [Strawberry extension lifecycle](docs/GLOSSARY.md#strawberry-extension-lifecycle) | shipped (`0.0.14`) |
| [Per-operation extension isolation](docs/GLOSSARY.md#per-operation-extension-isolation) | shipped (`0.0.14`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [Probe URLconf](docs/GLOSSARY.md#probe-urlconf) | shipped (repository test pattern) |
| [`seed_data`](docs/GLOSSARY.md#seed_data) | shipped |
| [Live-first coverage mandate](docs/GLOSSARY.md#live-first-coverage-mandate) | shipped (`0.0.4`) |
| [Joint version cut](docs/GLOSSARY.md#joint-version-cut) | shipped (`0.0.13`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) | shipped (`0.0.9`) |
| [Single-upstream parity](docs/GLOSSARY.md#single-upstream-parity) | shipped |
| [`max_value_depth`](docs/GLOSSARY.md#max_value_depth) | shipped (`0.0.14`) |

#### Planning note

Security-audit remediation program, card 2 of 4.

#### Dependencies

- `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation

#### Scope

- New immutable resource-policy object + schema-construction normalization + context threading.
- Value-budget walker over coerced inputs (iterative, cycle-safe, py3.10).
- types/base.py DEFAULT_RELATION_SHAPE 'both' -> 'connection'; DjangoListField bound.

#### Definition of done

- [ ] Immutable resource policy consumed by schema/fields/optimizer/transports; per-field narrowing only.
- [ ] Value-budget walker rejects before ORM access; DEFAULT_RELATION_SHAPE default is 'connection'; raw lists bounded.
- [ ] Full suite green at 100% coverage; hygiene clean; docs fold-in.

#### Architectural posture

- One immutable resource-policy object consumed by DjangoSchema, collection fields, the optimizer, and the transports: max document tokens, max selection/alias count after fragment expansion, max depth, max page size, max raw-list rows, max aggregate collection cost, optional execution deadline. Normalize and validate once at schema construction; thread the immutable result through request context (mirror the optimizer's DST_OPTIMIZER_* context seam). Per-field overrides may only narrow unless an explicit trusted-schema declaration widens.
- Extend the policy with one iterative, cycle-safe value-budget walker charging total input nodes, container width, membership-list items, node-refetch ids, relation ids per mutation and in aggregate, nested serializer rows, upload count / per-file bytes / aggregate bytes, and scalar byte size where a parser/validator is nonlinear. Stop before decoding ids or touching the ORM once the budget is exhausted.
- Change the secure default for many-side relations from 'both' to 'connection'. A raw list requires explicit opt-in and an enforced maximum; DjangoListField gets a required/effective bound (documenting it as dangerous is not enough).

#### Why it matters

- S3 (High): neither the package nor the example installs a token / query-depth / complexity / selection-count limiter, and there is no page-size / raw-list-row / aggregate-row budget. DjangoListField evaluates an unbounded queryset, and DEFAULT_RELATION_SHAPE='both' exposes a raw many-side list alongside the bounded connection, so a client bypasses the connection cap via the list sibling.
- S4 (High): document limits do not constrain variable-supplied values. A tiny query can carry an unlimited ids list (DjangoNodesField preserves duplicates positionally), unlimited in-lookup values, an and/or filter tree of unbounded width/node count, unlimited M2M ids, wide nested serializer lists, and uploads with no aggregate byte / file-count / per-file cap.

#### Dependencies

- Depends on card 046: the resource policy is consumed by the transports fixed there, and the program is staged transport-first.

#### Test plan

- Token / expanded-selection / alias / depth / aggregate-cost boundaries; fragments and directives cannot evade accounting; the same field under many aliases is charged many times.
- A connection's relay_max_results cannot be bypassed through a generated list sibling; raw root and relation lists stop at the configured maximum.
- Each input family under/at/over boundary, including a tiny query with a large variable payload; duplicate ids; empty lists; multiple bounded fields whose aggregate exceeds the request budget; proof of zero ORM work after rejection; sync/async parity with one typed error code.

#### Open question

- Default budget values (token/selection/depth/page/rows/cost) and which are settings-overridable vs schema-construction-only: the spec pins concrete numbers.
- Whether 'both'->'connection' needs a one-release deprecation shim or is a clean alpha break like card 046: the spec decides.

#### Card references

- Dependency: Depends on card 046: the resource policy is consumed by the transports fixed there, and the program is staged transport-first. -> `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation

<a id="transport_security_django_owned_http_bounded_body_utf_8_wire_ws_revalidation"></a>
### [DONE-046-0.0.14 - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation](KANBAN.html#transport_security_django_owned_http_bounded_body_utf_8_wire_ws_revalidation)

- Priority: Critical
- Status: Done
- Relative size: L
- Labels: `internal`
- Spec: [spec-046-transport_security-0_0_14.md](docs/SPECS/spec-046-transport_security-0_0_14.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoGraphQLProtocolRouter`](docs/GLOSSARY.md#djangographqlprotocolrouter) | shipped (`0.0.14`) |
| [Soft dependency](docs/GLOSSARY.md#soft-dependency) | shipped (`0.0.13`) |
| [Hard dependency](docs/GLOSSARY.md#hard-dependency) | shipped |
| [PEP 562 lazy export](docs/GLOSSARY.md#pep-562-lazy-export) | shipped (`0.0.13`) |
| [`require_optional_module`](docs/GLOSSARY.md#require_optional_module) | shipped (`0.0.14`) |
| [Eviction-simulated absence](docs/GLOSSARY.md#eviction-simulated-absence) | shipped (`0.0.13`) |
| [Channels request adapter](docs/GLOSSARY.md#channels-request-adapter) | shipped (`0.0.14`) |
| [`request_from_info`](docs/GLOSSARY.md#request_from_info) | shipped (`0.0.8`) |
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | shipped (`0.0.13`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [`DjangoModelPermission`](docs/GLOSSARY.md#djangomodelpermission) | shipped (`0.0.11`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`Upload` scalar](docs/GLOSSARY.md#upload-scalar) | shipped (`0.0.11`) |
| [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) | shipped (`0.0.11`) |
| [`FieldError` envelope](docs/GLOSSARY.md#fielderror-envelope) | shipped (`0.0.11`) |
| [`DjangoNodesField`](docs/GLOSSARY.md#djangonodesfield) | shipped (`0.0.9`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) | shipped (`0.0.14`) |
| [Probe URLconf](docs/GLOSSARY.md#probe-urlconf) | shipped (repository test pattern) |
| [Schema reload discipline](docs/GLOSSARY.md#schema-reload-discipline) | shipped |
| [`seed_data`](docs/GLOSSARY.md#seed_data) | shipped |
| [Live-first coverage mandate](docs/GLOSSARY.md#live-first-coverage-mandate) | shipped (`0.0.4`) |
| [Single-upstream parity](docs/GLOSSARY.md#single-upstream-parity) | shipped |
| [Joint version cut](docs/GLOSSARY.md#joint-version-cut) | shipped (`0.0.13`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |
| [Developer-only debug posture](docs/GLOSSARY.md#developer-only-debug-posture) | shipped (`0.0.14`) |
| [Debug-toolbar middleware](docs/GLOSSARY.md#debug-toolbar-middleware) | shipped (`0.0.14`) |
| [`DjangoDebugExtension`](docs/GLOSSARY.md#djangodebugextension) | shipped (`0.0.14`) |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [Cookbook parity](docs/GLOSSARY.md#cookbook-parity) | planned through `1.0.0` |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`DjangoFileType`](docs/GLOSSARY.md#djangofiletype) | shipped (`0.0.11`) |
| [`DjangoImageType`](docs/GLOSSARY.md#djangoimagetype) | shipped (`0.0.11`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [Django `AppConfig`](docs/GLOSSARY.md#django-appconfig) | shipped (`0.0.7`) |

#### Planning note

Security-audit remediation program, card 1 of 4. Amends spec-041 (channels_router). Explicit 0.0.14 alpha breaking change.

#### Scope

- S1: redesign the router protocol split (required Django-ASGI HTTP ownership; remove direct Channels HTTP; exact WebSocket routing via websocket_url_pattern).
- S2: package-owned cumulative request-body cap on the GraphQL HTTP path + documented proxy/server cap.
- S9: strict UTF-8 wire decode before json.loads; translate UnicodeDecodeError to the controlled 400; invert UTF-16/32/BOM success tests to 400; decide and document the UTF-8-BOM policy; reconcile _cross_web_patches._patched_body against the new HTTP path.
- S11: WebSocket consumer-class/factory injection seam + actor revalidation at TWO checkpoints (operation admission and every information-bearing outbound operation frame), so a revoked actor can neither admit another operation nor emit another next/data/error frame; revocation is connection-scoped and closes the whole socket (4403 Forbidden); optional explicit bounded revalidation window.
- S12 (transport slice only): migration note (old vs new asgi.py + the required urlpatterns entry) + transport deployment guidance (CSRF, cache/Vary, security headers, IDE/GET controls). The broader S12 deployment-contract docs belong to the later cards' doc slices.

#### Definition of done

- [x] Router HTTP branch no longer instantiates GraphQLHTTPConsumer; django_application is required and omitting it fails at construction; websocket_url_pattern exact-matches; WebSocket Origin/auth wrappers + consumer injection seam in place.
- [x] Cumulative request-body cap enforced pre-parse on GraphQL HTTP + documented proxy/server cap.
- [x] Wire JSON is UTF-8-only; UTF-16/32 success tests inverted to 400.
- [x] WebSocket actor revalidation at both the admission and the outbound-frame checkpoint, with connection-scoped revocation, via the injection seam.
- [x] Migration note + transport deployment docs authored; spec-041 amended.
- [ ] Full suite green at 100% coverage (maintainer/CI gate); ruff + trailing-comma clean; manage.py check + makemigrations --check clean.

#### Architectural posture

- RECOMMENDED DIRECTION (maintainer-pinned; the spec turns each bullet into a numbered Decision with alternatives-rejected rationale). Clean protocol split as an explicit alpha breaking change: the 0.0.14 byte-compatible upstream constructor contract is intentionally broken. The documented API freeze begins at 1.0.0, so correcting a confirmed security-boundary error during alpha is preferable to preserving an unsafe migration convenience.
- HTTP dispatches directly to a REQUIRED consumer-supplied Django ASGI application. The router must NOT instantiate or route to GraphQLHTTPConsumer. The GraphQL HTTP endpoint is declared in the consumer's Django URLconf using the normal Strawberry Django view, so it inherits the full MIDDLEWARE stack.
- Require django_application rather than deriving it internally; the consumer calls get_asgi_application() at the normal point in asgi.py (avoids Django init-order ambiguity). Omitting django_application must fail clearly at construction -- do not retain an unsafe compatibility fallback.
- WebSocket remains the package-owned Channels composition: exact GraphQL route -> DjangoWebSocketHostValidator (Host) -> AllowedHostsOriginValidator (Origin) -> AuthMiddlewareStack -> the GraphQL WebSocket consumer, with the Host validator outermost so Host and Origin are two separate checks in that order. Rename/narrow url_pattern to a WebSocket-only websocket_url_pattern with exact matching as the secure default; Django URLconf independently owns HTTP path matching.
- Add a WebSocket consumer-class/factory injection seam for S11 without implementing a second GraphQL protocol engine; the injected class must still sit inside the package's Host/Origin and authentication wrappers. Per-operation session revalidation is a WebSocket concern layered through that seam and must not delay or complicate the S1 HTTP correction.
- S1 does not dispose of S2: still define and test an explicit cumulative request-body limit (count received bytes, do not trust Content-Length; reject at the limit before JSON parse / schema execution) and document the reverse-proxy / ASGI-server limit. Routing through Django restores the authoritative middleware lifecycle but must not be represented as automatically providing every transport resource bound.

#### Why it matters

- S1 (Blocker): routers.py wires the HTTP branch as AuthMiddlewareStack(URLRouter([re_path(url_pattern, GraphQLHTTPConsumer.as_asgi(...))])). That turns the session cookie into an authenticated actor but bypasses Django's MIDDLEWARE entirely -- SecurityMiddleware, CsrfViewMiddleware, CommonMiddleware / ALLOWED_HOSTS, and all consumer tenant/rate-limit/audit/cache/security-header middleware. Confirmed by source and a probe (POST Host: evil.example -> 200).
- S1 route overmatch: url_pattern default '^graphql' is a prefix regex, so /graphql-admin and /graphqlanything are claimed by the GraphQL consumer before the Django fallback -- a path the deployment believes Django owns.
- S2 (Blocker): the routed AsyncHttpConsumer buffers the whole body via b''.join(self.body) with no application cap; DATA_UPLOAD_MAX_MEMORY_SIZE is never consulted because Django's ASGI handler is bypassed. Unauthenticated memory amplification before JSON parsing or schema execution.
- S9 (Medium): _cross_web_patches._patched_body returns raw bytes so json.loads auto-detects UTF-16/32; RFC 8259 requires UTF-8 on the wire. Accepting other encodings creates a proxy/WAF/access-log parser differential.
- S11 (Medium): the WebSocket scope user is captured at handshake and never revalidated; a logout/password-reset/disable/revocation from another request or admin action is not reflected on the established connection.
- S1 and S2 block moving off the current 'not production' alpha posture; a framework's secure architecture cannot depend on every consumer independently discovering these gaps.

#### Test plan

- Django middleware / configured security headers execute on the GraphQL HTTP route; a project middleware sentinel runs; a hostile Host is rejected on HTTP (not only WebSocket).
- Cookie-authenticated mutations cover missing, wrong, and correct CSRF tokens (Client(enforce_csrf_checks=True)).
- An authenticated GET response is non-cacheable or varies on Cookie.
- /graphql and /graphql/ match per an explicit policy while /graphql-admin and /graphqlanything reach Django or 404.
- Body cap: no Content-Length; declared below/at/above; declared-small-but-streamed-over; multi-fragment crossing; JSON / malformed JSON / multipart; an early 413 proving neither JSON parse nor schema execution ran; parity across the py3.10 / Django 5.2.0 floor and the current stack.
- S9: UTF-16/32 (BOM and BOM-less) -> 400; ordinary UTF-8 preserved; malformed UTF-8 -> 400; the chosen UTF-8-BOM direction.
- S11: establish a socket, revoke/flush/disable via a separate request, prove the next operation is denied without reconnecting; existing WebSocket Origin/auth direction tests remain intact.

#### Open question

- Where the app-level body cap lives on the new Django-view HTTP path (a package GraphQL-view subclass vs. documented DATA_UPLOAD_MAX_MEMORY_SIZE + a thin wrapper): the spec decides.
- Whether the package ships a thin GraphQL HTTP view wrapper or points consumers directly at strawberry-django's GraphQLView: the spec decides and documents the exact urlpatterns entry.
- UTF-8 BOM: accept-and-strip vs reject (RFC 8259 permits either): the spec picks one and documents it.

<a id="sealed_get_queryset_visibility_boundary_policy_artifacts"></a>
### [DONE-045-0.0.14 - Sealed get_queryset visibility-boundary policy artifacts](KANBAN.html#sealed_get_queryset_visibility_boundary_policy_artifacts)

- Priority: High
- Status: Done
- Relative size: S
- Labels: `docs`, `internal`, `permissions`, `security`
- Spec: [spec-045-visibility_boundary-0_0_14.md](docs/SPECS/spec-045-visibility_boundary-0_0_14.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Sealed execution queryset](docs/GLOSSARY.md#sealed-execution-queryset) | shipped (`0.0.14`) |
| [Visibility boundary](docs/GLOSSARY.md#visibility-boundary) | shipped (`0.0.14`) |
| [Prove-then-clone AST trust](docs/GLOSSARY.md#prove-then-clone-ast-trust) | shipped (`0.0.14`) |
| [Callable shadow defect](docs/GLOSSARY.md#callable-shadow-defect) | shipped (`0.0.14`) |
| [Prefetch alias threading](docs/GLOSSARY.md#prefetch-alias-threading) | shipped (`0.0.14`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) | shipped (`0.0.5`) |

#### Scope

- Documentation-only slice over the already-landed sealed get_queryset visibility boundary (commit 60998b17). Authors the governing numbered security decisions, this card's spec, and the five new glossary terms; closes the deferred [P2] policy-artifact residual in `spec-045-visibility_boundary-0_0_14`.
- Depends on the sealed-boundary implementation commit 60998b17 (the code this card documents; already landed).

#### Definition of done

- [x] Numbered security decisions authored covering the changed contract: untrusted-object rebuild, prove-then-clone AST trust, identity-fast-path removal, Prefetch rebuild + alias threading, queryset-shape rejections, and the typed error contract.
- [x] Spec docs/SPECS/spec-045-visibility_boundary-0_0_14.md authored with its companion *-terms.csv.
- [x] GLOSSARY entries imported for the five new terms via the fakeshop glossary DB and docs/GLOSSARY.md regenerated.
- [x] KANBAN.md / KANBAN.html regenerated from the kanban DB with this card in Done.
- [x] The prior [P2] policy-artifact residual recorded as closed in `spec-045-visibility_boundary-0_0_14`.

#### Files likely touched

- `django_strawberry_framework/utils/querysets.py`
- `django_strawberry_framework/permissions.py`
- `django_strawberry_framework/optimizer/walker.py`

#### Why it matters

- The sealed boundary changed the accepted queryset shapes, identity/cache behavior, aliases, errors, and query execution of the framework's single data-leak-critical seam. Repository policy requires a governing numbered security decision, a KANBAN card, a spec, and a GLOSSARY update for exactly such a change; commit 60998b17 and the adversarial review rounds recorded in `spec-045-visibility_boundary-0_0_14` closed the correctness work but deferred these artifacts. This card discharges that deferral so the standing documentation matches the implemented security contract.

#### Decision

- **Threat model: a mistaken hook, not an in-process adversary.** The boundary defends against a `get_queryset` hook that returns wrong query state - a dropped predicate, a foreign or shadowed object, a wrong table, a sliced or projected shape, an injected cache, a re-routed alias, or AST the sealed query would share with the candidate. A consumer who deliberately crafts an object to reach a Django or adapter dispatch site is OUT of scope: they already execute code in the process, so no in-interpreter walk is a trust boundary against them (the same stance the framework takes on process-wide monkeypatching). Canonical reconstruction is the terminating mechanism - the sealed query is a framework-owned rebuild with every bound value normalized to an exact inert copy, not the candidate graph proven safe - so the boundary is CLOSED to further dispatch-path expansion. Decision 8 of `spec-045-visibility_boundary-0_0_14`.

#### Note

- Documents: commit 60998b17 - sealed get_queryset visibility boundary.
- Closes: the [P2] residual "The standing guarantee and historical note declare the unsafe boundary complete", recorded in `spec-045-visibility_boundary-0_0_14` (the deferred policy-artifact residual only; the correctness findings were closed by the adversarial review rounds).
- Post-ship: Decision 8 added after the 0.0.14 cut. It records canonical reconstruction (superseding the prove-then-retain limitation Decision 2 shipped with), closes the two bound-parameter residuals (`Lookup.rhs`, `Value.value`) rather than carrying them to a further card, and ends the crafted-object review loop. A newly found dispatch path reachable only by a deliberately crafted object is no longer a defect of this boundary; an ordinary-consumer path that loses the predicate, a Django release adding a slot legitimate queries populate, or a demonstrated row leak still is.

<a id="response_extensions_debug_middleware"></a>
### [DONE-044-0.0.14 - Response-extensions debug middleware](KANBAN.html#response_extensions_debug_middleware)

- Priority: Low
- Parity: ⚛️ graphene-django (Required)
- Status: Done
- Relative size: M
- Labels: `debugging`, `graphql-api`, `middleware`
- Spec: [spec-044-debug_extension-0_0_14.md](docs/SPECS/spec-044-debug_extension-0_0_14.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Response-extensions debug middleware](docs/GLOSSARY.md#response-extensions-debug-middleware) | shipped (`0.0.14`) |
| [`DjangoDebugExtension`](docs/GLOSSARY.md#djangodebugextension) | shipped (`0.0.14`) |
| [Strawberry extension lifecycle](docs/GLOSSARY.md#strawberry-extension-lifecycle) | shipped (`0.0.14`) |
| [Per-operation extension isolation](docs/GLOSSARY.md#per-operation-extension-isolation) | shipped (`0.0.14`) |
| [Debug payload availability](docs/GLOSSARY.md#debug-payload-availability) | shipped (`0.0.14`) |
| [Response-extension merge semantics](docs/GLOSSARY.md#response-extension-merge-semantics) | shipped (`0.0.14`) |
| [Django debug-cursor capture](docs/GLOSSARY.md#django-debug-cursor-capture) | shipped (`0.0.14`) |
| [Reference-counted cursor coordinator](docs/GLOSSARY.md#reference-counted-cursor-coordinator) | shipped (`0.0.14`) |
| [Bounded query-log rollover](docs/GLOSSARY.md#bounded-query-log-rollover) | shipped (`0.0.14`) |
| [Async SQL-capture boundary](docs/GLOSSARY.md#async-sql-capture-boundary) | shipped (`0.0.14`) |
| [Debug SQL row](docs/GLOSSARY.md#debug-sql-row) | shipped (`0.0.14`) |
| [Debug exception row](docs/GLOSSARY.md#debug-exception-row) | shipped (`0.0.14`) |
| [Masking-extension ordering](docs/GLOSSARY.md#masking-extension-ordering) | shipped (`0.0.14`) |
| [Developer-only debug posture](docs/GLOSSARY.md#developer-only-debug-posture) | shipped (`0.0.14`) |
| [Graphene debug migration](docs/GLOSSARY.md#graphene-debug-migration) | shipped (`0.0.14`) |
| [Cookbook parity](docs/GLOSSARY.md#cookbook-parity) | planned through `1.0.0` |
| [Probe URLconf](docs/GLOSSARY.md#probe-urlconf) | shipped (repository test pattern) |
| [Hard dependency](docs/GLOSSARY.md#hard-dependency) | shipped |
| [Debug-toolbar middleware](docs/GLOSSARY.md#debug-toolbar-middleware) | shipped (`0.0.14`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`DjangoGraphQLProtocolRouter`](docs/GLOSSARY.md#djangographqlprotocolrouter) | shipped (`0.0.14`) |
| [Channels request adapter](docs/GLOSSARY.md#channels-request-adapter) | shipped (`0.0.14`) |
| [`require_optional_module`](docs/GLOSSARY.md#require_optional_module) | shipped (`0.0.14`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) | shipped (`0.0.14`) |
| [Joint version cut](docs/GLOSSARY.md#joint-version-cut) | shipped (`0.0.13`) |
| [Live-first coverage mandate](docs/GLOSSARY.md#live-first-coverage-mandate) | shipped (`0.0.4`) |
| [Schema reload discipline](docs/GLOSSARY.md#schema-reload-discipline) | shipped |
| [`seed_data`](docs/GLOSSARY.md#seed_data) | shipped |
| [Soft dependency](docs/GLOSSARY.md#soft-dependency) | shipped (`0.0.13`) |
| [Eviction-simulated absence](docs/GLOSSARY.md#eviction-simulated-absence) | shipped (`0.0.13`) |
| [PEP 562 lazy export](docs/GLOSSARY.md#pep-562-lazy-export) | shipped (`0.0.13`) |
| [Single-upstream parity](docs/GLOSSARY.md#single-upstream-parity) | shipped |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |
| [Plan cache](docs/GLOSSARY.md#plan-cache) | shipped (`0.0.3`) |
| [Multi-database cooperation](docs/GLOSSARY.md#multi-database-cooperation) | shipped (`0.0.7`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [Django Trac #37064 hardening](docs/GLOSSARY.md#django-trac-37064-hardening) | shipped (`0.0.7`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |

#### Package files

- [`django_strawberry_framework/extensions/debug.py`](django_strawberry_framework/extensions/debug.py)
- [`tests/extensions/`](tests/extensions/)

#### Definition of done

- [ ] Implement `django_strawberry_framework/extensions/debug.py` as a Strawberry `SchemaExtension` that captures SQL and exceptions for the in-flight operation and attaches them to the response `extensions` map (key: `debug`).
- [ ] Pin the **exposure mechanism** (response-`extensions` map vs. schema-level `_debug` field) and the **fidelity choice** (cursor-wrap port vs. `connection.queries`) in the spec; default both to the simpler choice (response-`extensions` map + `connection.queries`) unless the spec authoring round chooses otherwise.
- [ ] Output shape mirrors graphene's `DjangoDebugSQL` / `DjangoDebugException` field names where the chosen fidelity supports them; document any shape narrowing (e.g., omitted Postgres-specific fields) explicitly.
- [ ] Off by default; opt-in via the extensions list passed to `strawberry.Schema(...)`.
- [ ] Tests under `tests/extensions/test_debug.py` against a fakeshop request that emits SQL.
- [ ] Documented as the response-side counterpart to `DONE-042-0.0.14`.

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
- graphene-django ships an in-response `DjangoDebug` SQL/exception subsystem; strawberry-graphql-django ships none.

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

- `graphene-django` ships a debug subsystem that exposes the executed SQL queries and raised exceptions for each GraphQL request via a `DjangoDebug` object. This is different from `DONE-042-0.0.14` (django-debug-toolbar SQL panel UI): graphene's mechanism is **inside the GraphQL response**, so frontend clients and Apollo DevTools can read it without the toolbar. Both mechanisms are useful and not mutually exclusive.
- A Strawberry-native equivalent is a small `SchemaExtension` that captures SQL (through `django.db.connection.queries` or via a port of graphene's cursor-wrap mechanism — see Architectural posture) and exceptions and attaches the result to the response's `extensions` map.
- `strawberry-graphql-django` ships **no** equivalent (no file references `connection.queries` and no `*debug*` module exists outside the toolbar middleware tracked by `DONE-042-0.0.14`); this card is graphene-django parity only.
- developer experience.

#### Note

- distinct from `DONE-042-0.0.14` (Django debug toolbar).
- a Strawberry `SchemaExtension` that captures SQL + exceptions into `extensions['debug']`; one design choice between porting graphene's cursor-wrap and reading `connection.queries`. Single extension module + tests.

#### Card references

- Related: Documented as the response-side counterpart to `DONE-042-0.0.14`. -> `DONE-042-0.0.14` - Debug-toolbar middleware

<a id="test_client_helper"></a>
### [DONE-043-0.0.14 - Test client helper](KANBAN.html#test_client_helper)

- Priority: Low
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `graphql-api`, `test-client`, `tests`, `uploads`
- Spec: [spec-043-test_client-0_0_14.md](docs/SPECS/spec-043-test_client-0_0_14.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) | shipped (`0.0.14`) |
| [`Upload` scalar](docs/GLOSSARY.md#upload-scalar) | shipped (`0.0.11`) |
| [Soft dependency](docs/GLOSSARY.md#soft-dependency) | shipped (`0.0.13`) |
| [Eviction-simulated absence](docs/GLOSSARY.md#eviction-simulated-absence) | shipped (`0.0.13`) |
| [PEP 562 lazy export](docs/GLOSSARY.md#pep-562-lazy-export) | shipped (`0.0.13`) |
| [Joint version cut](docs/GLOSSARY.md#joint-version-cut) | shipped (`0.0.13`) |
| [Live-first coverage mandate](docs/GLOSSARY.md#live-first-coverage-mandate) | shipped (`0.0.4`) |
| [Schema reload discipline](docs/GLOSSARY.md#schema-reload-discipline) | shipped |
| [`seed_data`](docs/GLOSSARY.md#seed_data) | shipped |
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | shipped (`0.0.13`) |
| [Debug-toolbar middleware](docs/GLOSSARY.md#debug-toolbar-middleware) | shipped (`0.0.14`) |
| [Response-extensions debug middleware](docs/GLOSSARY.md#response-extensions-debug-middleware) | shipped (`0.0.14`) |
| [`DjangoGraphQLProtocolRouter`](docs/GLOSSARY.md#djangographqlprotocolrouter) | shipped (`0.0.14`) |
| [`FieldError` envelope](docs/GLOSSARY.md#fielderror-envelope) | shipped (`0.0.11`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`request_from_info`](docs/GLOSSARY.md#request_from_info) | shipped (`0.0.8`) |
| [`safe_wrap_connection_method`](docs/GLOSSARY.md#safe_wrap_connection_method) | shipped (`0.0.7`) |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |

#### Package files

- [`django_strawberry_framework/testing/client.py`](django_strawberry_framework/testing/client.py)

#### Dependencies

- `DONE-037-0.0.11` - Upload scalar and file / image field mapping

#### Scope

- `test/client.py` (sync + async `TestClient`, a `GraphQLTestMixin`, two `(Mixin, TestCase)` combos), endpoint setting, multipart-upload support; several design decisions to pin; switch the fakeshop tests over.

#### Definition of done

- [x] Implement `django_strawberry_framework/testing/client.py` exposing `TestClient` / `AsyncTestClient` (per the inheritance shape pinned above) plus a `GraphQLTestMixin` and two concrete `(Mixin, TestCase)` / `(Mixin, TransactionTestCase)` combinations for the unittest crowd.
- [x] Mixin carries `assertResponseNoErrors` / `assertResponseHasErrors` helpers (or the equivalent named for the chosen `.query()` return type).
- [x] Project-wide endpoint settings key (working name `GRAPHQL_TESTING_ENDPOINT`, final name pinned during implementation) under `DJANGO_STRAWBERRY_FRAMEWORK`, with constructor / per-call override.
- [x] Multipart file-upload support on `request()` so consumers can drive `Upload`-scalar mutations from the same helper once `DONE-037-0.0.11` ships.
- [x] Live HTTP tests under `examples/fakeshop/test_query/` switch to the helper.
- [x] Tests under `tests/testing/test_client.py`.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/test/client.py` — `TestClient` (subclasses Strawberry's `strawberry.test.BaseGraphQLTestClient`), `AsyncTestClient` (subclasses `TestClient`, takes an `AsyncClient`, overrides `.query()` and `.login()`). The `.query()` / `.mutate()` API surface lives on the upstream `BaseGraphQLTestClient`; strawberry-django adds Django-specific `request()`, `login()`, and the async `query()` override. `request()` switches to `format="multipart"` when `files=` is provided.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/utils/testing.py` — module-level `graphql_query` function; `GraphQLTestMixin` (the reusable mixin carrying `.query(...)`, `assertResponseNoErrors`, `assertResponseHasErrors`); `GraphQLTestCase` (`(GraphQLTestMixin, TestCase)`); `GraphQLTransactionTestCase` (`(GraphQLTestMixin, TransactionTestCase)`).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/settings.py #"TESTING_ENDPOINT"` — graphene reads `TESTING_ENDPOINT` (default `/graphql`) from its own settings dict so the testing helper has a project-wide override knob.
- both upstreams ship a GraphQL test client / mixin.

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
- developer experience.

#### Dependencies

- `DONE-037-0.0.11` (Upload scalar) — the file-upload helper path lights up once Upload-scalar inputs exist; the helper itself ships without it but gains a tested path here.

#### Card references

- Dependency: `DONE-037-0.0.11` (Upload scalar) — the file-upload helper path lights up once Upload-scalar inputs exist; the helper itself ships without it but gains a tested path here. -> `DONE-037-0.0.11` - Upload scalar and file / image field mapping
- Related: Multipart file-upload support on `request()` so consumers can drive `Upload`-scalar mutations from the same helper once `DONE-037-0.0.11` ships. -> `DONE-037-0.0.11` - Upload scalar and file / image field mapping

<a id="debug_toolbar_middleware"></a>
### [DONE-042-0.0.14 - Debug-toolbar middleware](KANBAN.html#debug_toolbar_middleware)

- Priority: Low
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `debugging`, `django-integration`, `middleware`
- Spec: [spec-042-debug_toolbar-0_0_14.md](docs/SPECS/spec-042-debug_toolbar-0_0_14.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Debug-toolbar middleware](docs/GLOSSARY.md#debug-toolbar-middleware) | shipped (`0.0.14`) |
| [Response-extensions debug middleware](docs/GLOSSARY.md#response-extensions-debug-middleware) | shipped (`0.0.14`) |
| [Soft dependency](docs/GLOSSARY.md#soft-dependency) | shipped (`0.0.13`) |
| [PEP 562 lazy export](docs/GLOSSARY.md#pep-562-lazy-export) | shipped (`0.0.13`) |
| [Eviction-simulated absence](docs/GLOSSARY.md#eviction-simulated-absence) | shipped (`0.0.13`) |
| [`require_optional_module`](docs/GLOSSARY.md#require_optional_module) | shipped (`0.0.14`) |
| [Joint version cut](docs/GLOSSARY.md#joint-version-cut) | shipped (`0.0.13`) |
| [Live-first coverage mandate](docs/GLOSSARY.md#live-first-coverage-mandate) | shipped (`0.0.4`) |
| [Schema reload discipline](docs/GLOSSARY.md#schema-reload-discipline) | shipped |
| [`seed_data`](docs/GLOSSARY.md#seed_data) | shipped |
| [Single-upstream parity](docs/GLOSSARY.md#single-upstream-parity) | shipped |
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | shipped (`0.0.13`) |
| [`DjangoGraphQLProtocolRouter`](docs/GLOSSARY.md#djangographqlprotocolrouter) | shipped (`0.0.14`) |
| [`SerializerMutation`](docs/GLOSSARY.md#serializermutation) | shipped (`0.0.13`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) | shipped (`0.0.14`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [Django `AppConfig`](docs/GLOSSARY.md#django-appconfig) | shipped (`0.0.7`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [FK-id elision](docs/GLOSSARY.md#fk-id-elision) | shipped (`0.0.3`) |
| [`request_from_info`](docs/GLOSSARY.md#request_from_info) | shipped (`0.0.8`) |
| [`Upload` scalar](docs/GLOSSARY.md#upload-scalar) | shipped (`0.0.11`) |
| [Django Trac #37064 hardening](docs/GLOSSARY.md#django-trac-37064-hardening) | shipped (`0.0.7`) |

#### Package files

- [`django_strawberry_framework/middleware/debug_toolbar.py`](django_strawberry_framework/middleware/debug_toolbar.py)

#### Definition of done

- [x] Implement `django_strawberry_framework/middleware/debug_toolbar.py` exposing a `DebugToolbarMiddleware` that **subclasses** `debug_toolbar.middleware.DebugToolbarMiddleware` and overrides `process_view` + `_postprocess` for the two injection paths above.
- [x] Ship the matching template asset at `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`; the middleware renders it via `render_to_string(...)` into HTML responses for the GraphiQL view.
- [x] Introspection-query skip behavior preserved (no payload injection when `operationName == "IntrospectionQuery"`).
- [x] `debug_toolbar` is a soft dependency: top-level package import must succeed without `django-debug-toolbar` installed; the middleware module raises `ImportError` with an install hint when actually imported.
- [x] In-process test against a fakeshop request that emits SQL, covering both the GraphiQL HTML path and the JSON operation path.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/middlewares/debug_toolbar.py` — `DebugToolbarMiddleware` (subclasses upstream `debug_toolbar.middleware.DebugToolbarMiddleware`); module-level `_get_payload` helper; `_HTML_TYPES` constant for content-type sniffing.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html` — HTML snippet rendered into the GraphiQL response; ships as a template asset alongside the Python module.
- strawberry-graphql-django ships a debug-toolbar middleware; graphene-django ships none.

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
- developer experience.

#### Note

- subclass django-debug-toolbar's middleware with two injection paths (GraphiQL HTML + `/graphql/` JSON), a template asset, introspection-skip behavior, and a soft dependency. Single module + tests.

<a id="channels_asgi_router_migration_aid"></a>
### [DONE-041-0.0.14 - Channels ASGI router (migration aid)](KANBAN.html#channels_asgi_router_migration_aid)

- Priority: Low
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: S
- Labels: `asgi`, `channels`, `django-integration`
- Spec: [spec-041-channels_router-0_0_14.md](docs/SPECS/spec-041-channels_router-0_0_14.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoGraphQLProtocolRouter`](docs/GLOSSARY.md#djangographqlprotocolrouter) | shipped (`0.0.14`) |
| [Soft dependency](docs/GLOSSARY.md#soft-dependency) | shipped (`0.0.13`) |
| [PEP 562 lazy export](docs/GLOSSARY.md#pep-562-lazy-export) | shipped (`0.0.13`) |
| [Eviction-simulated absence](docs/GLOSSARY.md#eviction-simulated-absence) | shipped (`0.0.13`) |
| [`require_optional_module`](docs/GLOSSARY.md#require_optional_module) | shipped (`0.0.14`) |
| [`request_from_info`](docs/GLOSSARY.md#request_from_info) | shipped (`0.0.8`) |
| [Channels request adapter](docs/GLOSSARY.md#channels-request-adapter) | shipped (`0.0.14`) |
| [Joint version cut](docs/GLOSSARY.md#joint-version-cut) | shipped (`0.0.13`) |
| [Live-first coverage mandate](docs/GLOSSARY.md#live-first-coverage-mandate) | shipped (`0.0.4`) |
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | shipped (`0.0.13`) |
| [`SerializerMutation`](docs/GLOSSARY.md#serializermutation) | shipped (`0.0.13`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`FieldError` envelope](docs/GLOSSARY.md#fielderror-envelope) | shipped (`0.0.11`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`DjangoModelPermission`](docs/GLOSSARY.md#djangomodelpermission) | shipped (`0.0.11`) |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) | shipped (`0.0.14`) |
| [Debug-toolbar middleware](docs/GLOSSARY.md#debug-toolbar-middleware) | shipped (`0.0.14`) |
| [Response-extensions debug middleware](docs/GLOSSARY.md#response-extensions-debug-middleware) | shipped (`0.0.14`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [strawberry_config](docs/GLOSSARY.md#strawberry_config) | shipped (`0.0.7`) |
| [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) | shipped (`0.0.5`) |
| [`Upload` scalar](docs/GLOSSARY.md#upload-scalar) | shipped (`0.0.11`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) | shipped (`0.0.9`) |
| [`DjangoMutationField`](docs/GLOSSARY.md#djangomutationfield) | shipped (`0.0.11`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |

#### Package files

- [`django_strawberry_framework/routers.py`](django_strawberry_framework/routers.py)
- [`django_strawberry_framework/utils/imports.py`](django_strawberry_framework/utils/imports.py)
- [`django_strawberry_framework/utils/permissions.py`](django_strawberry_framework/utils/permissions.py)
- [`tests/test_routers.py`](tests/test_routers.py)
- [`tests/utils/test_imports.py`](tests/utils/test_imports.py)
- [`tests/utils/test_inputs.py`](tests/utils/test_inputs.py)
- [`tests/utils/test_permissions.py`](tests/utils/test_permissions.py)

#### Definition of done

- [x] Implement `django_strawberry_framework/routers.py` exposing `DjangoGraphQLProtocolRouter` (final name pinned during implementation).
- [x] `channels` is a soft dependency: top-level package import must not fail if `channels` is not installed. The helper wraps `channels` imports lazily and raises `ImportError` with an install hint when it is actually called.
- [x] Tests under `tests/test_routers.py` exercise both the channels-present and channels-absent paths.
- [x] Migration guide (`TODO-BETA-071-0.1.8`) gains a one-row entry in its "symbol equivalents" table mapping `AuthGraphQLProtocolTypeRouter` → `DjangoGraphQLProtocolRouter`, so the symbol rename is documented in one canonical location.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/routers.py` — `AuthGraphQLProtocolTypeRouter` wrapping `ProtocolTypeRouter`, `URLRouter`, `AllowedHostsOriginValidator`, `AuthMiddlewareStack`, plus `GraphQLHTTPConsumer` / `GraphQLWSConsumer`.
- strawberry-graphql-django ships a Channels `ProtocolTypeRouter` helper; graphene-django ships none.

#### Architectural posture

- The router helper must use a **distinctly-ours symbol name** (working name: `DjangoGraphQLProtocolRouter`) so the module is unambiguously ours and does not impersonate the upstream API. This respects the [`GOAL.md`][goal] non-goal "a thin wrapper around `strawberry-graphql-django`".
- Migration ergonomics are preserved by the upstream-equivalent mapping in the migration guide (`TODO-BETA-071-0.1.8`), not by copying the symbol name. A migrant changes one import line: `from strawberry_django.routers import AuthGraphQLProtocolTypeRouter` → `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`.

#### Why it matters

- `strawberry-graphql-django` ships a small `routers.py` that builds a `ProtocolTypeRouter` over `GraphQLHTTPConsumer` and `GraphQLWSConsumer` for consumers using Channels. The module is ~30 lines but is the single import that makes ASGI / WebSocket migration painless.
- Shipping a functionally-equivalent helper lets strawberry-graphql-django migrants update one import line in their ASGI entrypoint. This card exists primarily to reduce migration friction, not to expand the API surface.
- small slice; explicit migration aid.

#### Note

- small `routers.py` (~30 lines) with a soft `channels` dependency; tests for both channels-present and channels-absent paths. Pure migration-aid card.

#### Card references

- Related: Migration guide (`TODO-BETA-071-0.1.8`) gains a one-row entry in its "symbol equivalents" table mapping `AuthGraphQLProtocolTypeRouter` → `DjangoGraphQLProtocolRouter`, so the symbol rename is documented in one canonical location. -> `TODO-BETA-071-0.1.8` - Migration and adoption guides

<a id="auth_mutations_login_logout_register"></a>
### [DONE-040-0.0.13 - Auth mutations (login / logout / register)](KANBAN.html#auth_mutations_login_logout_register)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `auth`, `mutations`, `public-api`
- Spec: [spec-040-auth_mutations-0_0_13.md](docs/SPECS/spec-040-auth_mutations-0_0_13.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | shipped (`0.0.13`) |
| [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) | shipped (`0.0.11`) |
| [`DjangoMutationField`](docs/GLOSSARY.md#djangomutationfield) | shipped (`0.0.11`) |
| [`DjangoFormMutation`](docs/GLOSSARY.md#djangoformmutation) | shipped (`0.0.12`) |
| [`DjangoModelPermission`](docs/GLOSSARY.md#djangomodelpermission) | shipped (`0.0.11`) |
| [`FieldError` envelope](docs/GLOSSARY.md#fielderror-envelope) | shipped (`0.0.11`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`SerializerMutation`](docs/GLOSSARY.md#serializermutation) | shipped (`0.0.13`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) | shipped (`0.0.5`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) | shipped (`0.0.5`) |
| [Input type generation](docs/GLOSSARY.md#input-type-generation) | shipped (`0.0.11`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |
| [`DjangoGraphQLProtocolRouter`](docs/GLOSSARY.md#djangographqlprotocolrouter) | shipped (`0.0.14`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) | shipped (`0.0.14`) |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) | shipped (`0.0.7`) |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [Strictness mode](docs/GLOSSARY.md#strictness-mode) | shipped (`0.0.3`) |

#### Definition of done

- [x] Implement `django_strawberry_framework/auth/` with `login_mutation`, `logout_mutation`, `register_mutation`, and a `current_user` query helper, each composable with the existing permissions surface.
- [x] Mirrored tests under `tests/auth/`.
- [x] Documented as opt-in: consumers must import explicitly; auth mutations are not injected into every schema.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/auth/` — `mutations.py` (login / logout / register), `queries.py` (`current_user`), `utils.py`.
- strawberry-graphql-django ships a small auth-mutations module.

#### Why it matters

- `strawberry-graphql-django` ships a small auth-mutations module so consumers don't have to hand-wire the most common Django auth flows. Natural follow-on once general mutations land.

#### Dependencies

- depends on `DONE-036-0.0.11`.

#### Note

- new `auth/` module (`login` / `logout` / `register` + `current_user` query helper) composing with permissions; builds on DONE-036-0.0.11's mutation infra. Mirrored tests; opt-in import.

#### Card references

- Related: depends on `DONE-036-0.0.11`. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="drf_serializer_mutations_serializermutation"></a>
### [DONE-039-0.0.13 - DRF serializer mutations (`SerializerMutation`)](KANBAN.html#drf_serializer_mutations_serializermutation)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Status: Done
- Relative size: L
- Labels: `mutations`, `public-api`, `serializers`
- Spec: [spec-039-serializer_mutations-0_0_13.md](docs/SPECS/spec-039-serializer_mutations-0_0_13.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`SerializerMutation`](docs/GLOSSARY.md#serializermutation) | shipped (`0.0.13`) |
| [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) | shipped (`0.0.11`) |
| [`DjangoMutationField`](docs/GLOSSARY.md#djangomutationfield) | shipped (`0.0.11`) |
| [`DjangoModelFormMutation`](docs/GLOSSARY.md#djangomodelformmutation) | shipped (`0.0.12`) |
| [`DjangoFormMutation`](docs/GLOSSARY.md#djangoformmutation) | shipped (`0.0.12`) |
| [`DjangoModelPermission`](docs/GLOSSARY.md#djangomodelpermission) | shipped (`0.0.11`) |
| [`FieldError` envelope](docs/GLOSSARY.md#fielderror-envelope) | shipped (`0.0.11`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) | shipped (`0.0.1`) |
| [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) | shipped (`0.0.5`) |
| [`Upload` scalar](docs/GLOSSARY.md#upload-scalar) | shipped (`0.0.11`) |
| [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) | shipped (`0.0.10`) |
| [`get_queryset` visibility hook](docs/GLOSSARY.md#get_queryset-visibility-hook) | shipped (`0.0.1`) |
| [Input type generation](docs/GLOSSARY.md#input-type-generation) | shipped (`0.0.11`) |
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | shipped (`0.0.13`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [`only()` projection](docs/GLOSSARY.md#only-projection) | shipped (`0.0.2`) |
| [Scalar field conversion](docs/GLOSSARY.md#scalar-field-conversion) | shipped (`0.0.1`+) |
| [Choice enum generation](docs/GLOSSARY.md#choice-enum-generation) | shipped (`0.0.1`) |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |
| [`Meta.model`](docs/GLOSSARY.md#metamodel) | shipped |
| [`Meta.primary`](docs/GLOSSARY.md#metaprimary) | shipped (`0.0.6`) |
| [`Meta.fields`](docs/GLOSSARY.md#metafields) | shipped |
| [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) | shipped |
| [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) | shipped (`0.0.9`) |
| [Relay Node integration](docs/GLOSSARY.md#relay-node-integration) | shipped (`0.0.5`) |
| [RELAY_GLOBALID_STRATEGY](docs/GLOSSARY.md#relay_globalid_strategy) | shipped (`0.0.9`) |
| [`Meta.globalid_strategy`](docs/GLOSSARY.md#metaglobalid_strategy) | shipped (`0.0.9`) |
| [Relation handling](docs/GLOSSARY.md#relation-handling) | shipped (`0.0.1`+) |
| [Specialized scalar conversions](docs/GLOSSARY.md#specialized-scalar-conversions) | shipped (`0.0.6`) |
| [`BigInt` scalar](docs/GLOSSARY.md#bigint-scalar) | shipped (`0.0.6`) |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |

#### Package files

- [`django_strawberry_framework/rest_framework/`](django_strawberry_framework/rest_framework/)
- [`tests/rest_framework/`](tests/rest_framework/)

#### Dependencies

- `DONE-036-0.0.11` - Mutations + auto-generated Input types

#### Definition of done

- [x] Add `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`.
- [x] Implement `django_strawberry_framework/rest_framework/` exposing `SerializerMutation` (final name pinned during implementation) on the DRF-style Meta surface: `Meta.serializer_class`, `Meta.lookup_field`, `Meta.model_operations`, `Meta.optional_fields`.
- [x] Serializer-field → Strawberry input mapping lives in `rest_framework/serializer_converter.py`, dual-purposed for inputs and outputs (mirroring graphene's `is_input=True` flag).
- [x] `rest_framework` is a soft dependency: package import must succeed without DRF installed; the helper raises `ImportError` with an install hint when actually called.
- [x] Validation errors surface through the shared `errors: list[FieldError]` envelope from `DONE-036-0.0.11`, populated from `serializer.errors`.
- [x] Tests under `tests/rest_framework/`.
- [x] Live HTTP coverage under `examples/fakeshop/test_query/` exercising a `ModelSerializer` mutation.

#### Files likely touched

- `django_strawberry_framework/rest_framework/` (new)
- `tests/rest_framework/` (new)
- `examples/fakeshop/apps/products/schema.py`

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/mutation.py` — `SerializerMutationOptions` carrying `lookup_field`, `model_class`, `model_operations=["create", "update"]`, `serializer_class`, `optional_fields`; `SerializerMutation` class; `fields_for_serializer(serializer, only_fields, exclude_fields, is_input=False, convert_choices_to_enum=True, lookup_field=None, optional_fields=())` helper.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/serializer_converter.py` — DRF-field → GraphQL-type registry; same module covers input and output via `is_input` flag.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/types.py` — shared `ErrorType` envelope.
- graphene-django ships `SerializerMutation`; the highest-leverage write-side feature for DRF migrants.

#### Why it matters

- `graphene-django` ships `SerializerMutation`, which builds a mutation from a DRF `Serializer` / `ModelSerializer`. This is the highest-leverage write-side feature for DRF migrants — they already have serializers defined and want to reuse them in GraphQL.
- [`GOAL.md`][goal] explicitly names DRF as a target migration source ("keep the public API familiar to Django, DRF, and django-filter users"). Shipping `SerializerMutation` is on-mission, not just a parity item.

#### Dependencies

- `DONE-036-0.0.11` — general mutation infrastructure (including the shared `errors` envelope).

#### Note

- no on-board predecessor.
- new `rest_framework/` subpackage (serializer converter dual-purposed for inputs + outputs, plus `SerializerMutation`); soft DRF dependency. Reuses DONE-036-0.0.11's infra + error envelope. Spec + tests + live HTTP.

#### Card references

- Dependency: `DONE-036-0.0.11` — general mutation infrastructure (including the shared `errors` envelope). -> `DONE-036-0.0.11` - Mutations + auto-generated Input types
- Related: Validation errors surface through the shared `errors: list[FieldError]` envelope from `DONE-036-0.0.11`, populated from `serializer.errors`. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="form_based_mutations_django_forms_modelforms"></a>
### [DONE-038-0.0.12 - Form-based mutations (Django Forms / ModelForms)](KANBAN.html#form_based_mutations_django_forms_modelforms)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Status: Done
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
| [`SerializerMutation`](docs/GLOSSARY.md#serializermutation) | shipped (`0.0.13`) |
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | shipped (`0.0.13`) |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |
| [`OrderSet`](docs/GLOSSARY.md#orderset) | shipped (`0.0.8`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |

#### Package files

- [`django_strawberry_framework/forms/`](django_strawberry_framework/forms/)
- [`tests/forms/`](tests/forms/)

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
- graphene-django ships `DjangoFormMutation` / `DjangoModelFormMutation`.

#### Why it matters

- `graphene-django` ships `DjangoFormMutation` and `DjangoModelFormMutation`: mutation classes that consume a Django `Form` / `ModelForm` and translate field validation + `cleaned_data` into a GraphQL mutation surface. Many graphene-django consumers rely on this as their write-side abstraction because it reuses validation they already have.
- Without an equivalent, graphene-django migrants must rewrite every form-backed mutation against the lower-level mutation surface from `DONE-036-0.0.11`.

#### Dependencies

- `DONE-036-0.0.11` — general mutation infrastructure (input-type generation, mutation-field plumbing) is the foundation form mutations attach to.

#### Note

- no on-board predecessor.
- new `forms/` subpackage (form-field converter + `Form`/`ModelForm` mutation classes) on the DRF-style Meta surface; reuses DONE-036-0.0.11's mutation infra + shared error envelope. Spec + tests + live HTTP.

#### Card references

- Dependency: `DONE-036-0.0.11` — general mutation infrastructure (input-type generation, mutation-field plumbing) is the foundation form mutations attach to. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types
- Related: Validation errors surface through the shared `errors: list[FieldError]` envelope defined in `DONE-036-0.0.11`, populated from `form.errors`. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="upload_scalar_and_file_image_field_mapping"></a>
### [DONE-037-0.0.11 - Upload scalar and file / image field mapping](KANBAN.html#upload_scalar_and_file_image_field_mapping)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
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
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [`FilterSet`](docs/GLOSSARY.md#filterset) | shipped (`0.0.8`) |

#### Package files

- [`django_strawberry_framework/mutations/`](django_strawberry_framework/mutations/)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`tests/types/test_converters.py`](tests/types/test_converters.py)

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
- strawberry-graphql-django maps `FileField` / `ImageField` to `Upload` (input) and file/image output types.

#### Why it matters

- `strawberry-graphql-django` maps `FileField` / `ImageField` to `Upload` on the input side and to `DjangoFileType` / `DjangoImageType` (with `name` / `path` / `size` / `url`) on the output side. Without it, every consumer that touches user uploads has to hand-roll the mapping.

#### Note

- pairs with `DONE-036-0.0.11` for the write side.
- bounded converter-table addition: `FileField` / `ImageField` → file/image output types on read, `Upload` on the input side. Touches `converters.py` + mutation input mapping + tests. Pairs with `DONE-036-0.0.11`.

#### Card references

- Related: Mutation input-type generation (`DONE-036-0.0.11`) maps the same fields to Strawberry's `Upload` scalar. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="mutations_auto_generated_input_types"></a>
### [DONE-036-0.0.11 - Mutations + auto-generated Input types](KANBAN.html#mutations_auto_generated_input_types)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
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
| [`SerializerMutation`](docs/GLOSSARY.md#serializermutation) | shipped (`0.0.13`) |
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | shipped (`0.0.13`) |
| [Per-field permission hooks](docs/GLOSSARY.md#per-field-permission-hooks) | planned for `0.1.1` |
| [`FieldSet`](docs/GLOSSARY.md#fieldset) | planned for `0.1.1` |
| [Cross-subsystem invariants](docs/GLOSSARY.md#cross-subsystem-invariants) | planned for 1.0.0 |

#### Package files

- [`django_strawberry_framework/mutations/`](django_strawberry_framework/mutations/)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`tests/mutations/`](tests/mutations/)

#### Dependencies

- `DONE-018-0.0.6` - Multiple DjangoTypes per model with `Meta.primary`
- `DONE-034-0.0.10` - Permissions subsystem

#### Definition of done

- [x] Add `docs/SPECS/spec-036-mutations-0_0_11.md`.
- [x] Implement `django_strawberry_framework/mutations/` (sets, fields, resolvers, input-type generation) on the DRF-style Meta surface (`Meta.input_class`, `Meta.partial_input_class`, etc.).
- [x] Auto-generated input types respect the relation-override contract pinned in `DONE-010-0.0.4`.
- [x] Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `DONE-038-0.0.12`, `DONE-039-0.0.13`, and `DONE-040-0.0.13`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings).
- [x] Tests under `tests/mutations/`.
- [x] Live HTTP coverage under `examples/fakeshop/test_query/` exercising the products write surface.

#### Files likely touched

- `django_strawberry_framework/mutations/` (new)
- `django_strawberry_framework/types/base.py`
- `tests/mutations/` (new)
- `examples/fakeshop/apps/products/schema.py`

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/mutations/` — `mutations.py` (create/update/delete classes), `fields.py` (`DjangoMutationField`), `resolvers.py` (sync/async write resolvers), `types.py` (input-type generation).
- mutations are the single largest unscoped gap vs strawberry-graphql-django (create / update / delete + auto-generated Input / PartialInput types).

#### Why it matters

- Mutations are the single largest unscoped gap against `strawberry-graphql-django`. Consumers migrating from strawberry-graphql-django will notice the missing write side immediately.
- `strawberry-django` exposes `create`, `update`, `delete`, custom mutations, and auto-generated `Input` / `PartialInput` types per model. These compose with permissions and the optimizer.

#### Dependencies

- `DONE-018-0.0.6` (`Meta.primary`) — explicit primary type drives mutation target resolution.
- `DONE-034-0.0.10` (permissions) — write mutations need to compose with `apply_cascade_permissions`.

#### Note

- no on-board predecessor.
- `DONE-027-0.0.8`-scale. The single largest unscoped gap versus strawberry-graphql-django. New `mutations/` subpackage (sets / fields / resolvers / input-type generation) + spec + tests + live HTTP, plus the shared `errors: list[FieldError]` envelope reused by DONE-038-0.0.12 / DONE-039-0.0.13 / DONE-040-0.0.13.

#### Card references

- Dependency: `DONE-018-0.0.6` (`Meta.primary`) — explicit primary type drives mutation target resolution. -> `DONE-018-0.0.6` - Multiple DjangoTypes per model with `Meta.primary`
- Related: Auto-generated input types respect the relation-override contract pinned in `DONE-010-0.0.4`. -> `DONE-010-0.0.4` - 0.0.4 foundation slice (definition-order independence)
- Dependency: `DONE-034-0.0.10` (permissions) — write mutations need to compose with `apply_cascade_permissions`. -> `DONE-034-0.0.10` - Permissions subsystem
- Related: Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `DONE-038-0.0.12`, `DONE-039-0.0.13`, and `DONE-040-0.0.13`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings). -> `DONE-038-0.0.12` - Form-based mutations (Django Forms / ModelForms)
- Related: Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `DONE-038-0.0.12`, `DONE-039-0.0.13`, and `DONE-040-0.0.13`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings). -> `DONE-039-0.0.13` - DRF serializer mutations (`SerializerMutation`)
- Related: Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `DONE-038-0.0.12`, `DONE-039-0.0.13`, and `DONE-040-0.0.13`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings). -> `DONE-040-0.0.13` - Auth mutations (login / logout / register)
- Related: `DONE-027-0.0.8`-scale. The single largest unscoped gap versus strawberry-graphql-django. New `mutations/` subpackage (sets / fields / resolvers / input-type generation) + spec + tests + live HTTP, plus the shared `errors: list[FieldError]` envelope reused by DONE-038-0.0.12 / DONE-039-0.0.13 / DONE-040-0.0.13. -> `DONE-027-0.0.8` - Filtering subsystem

<a id="optimizer_robustness_hardening_upstream_comparison_guards"></a>
### [DONE-035-0.0.10 - Optimizer robustness hardening (upstream-comparison guards)](KANBAN.html#optimizer_robustness_hardening_upstream_comparison_guards)

- Priority: Medium-high
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
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
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | shipped (`0.0.13`) |
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
- `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` - new (lives at the live working path; the `docs/SPECS/` archive move is the next spec author's batched sweep, never per-card).

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

#### Note

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
- Status: Done
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
| [Auth mutations](docs/GLOSSARY.md#auth-mutations) | shipped (`0.0.13`) |
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

Strawberry port of graphene-django's `apply_cascade_permissions(cls, queryset, info)` from `django_graphene_filters.permissions`. The cookbook line `return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)` is the canonical consumer surface — a single composable helper that walks the model graph at call time, runs each owner type's `get_queryset(qs, info)` against the related queryset, and returns a queryset that respects per-type row-level visibility across every traversed FK / OneToOne edge. Integrates with the optimizer's `Prefetch` downgrade so cascaded relations stay N+1-safe; per-field permission hooks via the reserved `Meta.fields_class` slot are deferred to the later FieldSet work (`TODO-BETA-059-0.1.1`), not shipped in this card.

#### Dependencies

- `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)

#### Scope

- `apply_cascade_permissions`
- reserved `Meta.fields_class` slot for per-field permission hooks; the per-field read-gate itself ships with the later FieldSet work (`TODO-BETA-059-0.1.1`), not in this card
- Optimizer cooperation: cascaded relations downgrade to `Prefetch(queryset=...)` so visibility filters survive the join (carries the existing `get_queryset` → `Prefetch` downgrade contract across the cascade walk).
- composable permission rules that remain visible from the owning type/query surface
- Public callable surface: `apply_cascade_permissions(cls, queryset, info, fields=None)` returns a queryset; optional `fields=` argument scopes the cascade to specific FK names. Both sync and async variants ship; async variant uses `sync_to_async` around the cascade walker to stay event-loop-safe.
- Walks the model graph via `registry.iter_definitions()` (shipped 0.0.4) — for each FK / OneToOne whose target type has a `get_queryset`, build a subquery from that type's visibility and intersect into the caller's queryset.
- Cycle detection via a `ContextVar` "seen" set so self-referential or mutually-referential type graphs do not recurse infinitely; cycle break returns the partially-narrowed queryset without raising.
- Single-column FK / O2O scope only: relations without a single-column `column` attribute (composite FKs, generic relations) are skipped explicitly. M2M and reverse-FK visibility are out of scope for this card and tracked as deferred follow-ups.
- Nullable FK rows preserved — a `NULL` FK does not reference a hidden target so the parent row is not dropped from the result.
- Multi-DB / sharding safety: the per-edge target visibility subquery is pinned to the caller's database alias via `.using(qs._db)` so shard-aware querysets do not accidentally cross databases.

#### Definition of done

- [x] Add `docs/SPECS/spec-034-permissions-0_0_10.md`.
- [x] Implement `django_strawberry_framework/permissions.py` or a `permissions/` package if the surface grows.
- [x] Add `tests/test_permissions.py`.
- [x] Define the `Meta` surface for per-field permissions and promote keys only when applied end-to-end.
- [x] Use real fakeshop permission users through `services.create_users(1)` in example tests where the system-under-test is the example project.
- [x] Check all permission-related ORM paths for N+1 behavior.
- [x] `apply_cascade_permissions` exported from the public surface (`from django_strawberry_framework import apply_cascade_permissions`). Both sync and async-aware variants ship together.
- [x] The four upstream invariants are each pinned by a dedicated test: ContextVar cycle guard; single-column FK/O2O scope; multi-DB pinning to the caller's alias; nullable-FK rows preserved.
- [x] Reconcile open question: how the existing per-field FILTER-denial gate (`check_<field>_permission` on `FilterSet` / `OrderSet`) composes with the new cascade visibility. Decision recorded in `docs/SPECS/spec-034-permissions-0_0_10.md` before the implementation pass starts; tests pin both shapes.
- [x] Cascade composes with `DjangoConnectionField` (`DONE-030-0.0.9`): a connection field whose wrapped type's `get_queryset` calls `apply_cascade_permissions` produces a Relay connection where every edge's nested relations respect the same cascade rule.
- [x] Live HTTP coverage in `examples/fakeshop/test_query/` exercises real fakeshop permission users (via `services.create_users(1)`) across a 2-deep FK cascade. Real users, not mocked `info.context.user`.

#### Foundation-slice seam

- `apply_cascade_permissions(cls, queryset, info)` walks the model graph at call time; `registry.iter_definitions()` (shipped in 0.0.4) is the public iterator that walk uses to find each owner type's `get_queryset`.
- `_attach_relation_resolvers` already accepts a `skip_field_names` set so consumer-authored fields are not clobbered; field-level permission hooks (`fields_class`) extend the same skip-set semantics.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py::DjangoObjectType.get_queryset` is graphene_django's per-type visibility hook, applied to related fields by `converter.py`'s `CustomField.wrap_resolve` (which routes FK/O2O resolution through `_type.get_queryset` unless `bypass_get_queryset` is set) — the same per-type visibility contract this card's `apply_cascade_permissions` automates by walking FK/O2O edges into each target type's `get_queryset`, so the graphene_django parity is required.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/utils/utils.py::bypass_get_queryset` is graphene_django's explicit per-resolver escape hatch from that visibility hook, confirming graphene_django scopes permission filtering per-relation rather than cascading it; this card's cascade walk is the required-parity superset that propagates the same `get_queryset` visibility across the model graph.
- django-graphene-filters ships rich cascade + per-field permissions; strawberry-graphql-django's per-field story is weaker (🍓 parity-adjacent).

#### Why it matters

- for the fakeshop example and real usage.
- permissions/visibility is security-relevant and blocks the fakeshop real-usage story.

#### Dependencies

- `DjangoType.get_queryset`
- optimizer `Prefetch` downgrade
- future `DjangoConnectionField`

#### Open question

- Open question — hidden-FK semantics: when a parent row references a hidden target, choose between excluding the parent row, nulling the FK field, or returning a sentinel. The upstream uses sentinels; the Strawberry side has to pick before the cascade lands. Pinned in `docs/SPECS/spec-034-permissions-0_0_10.md`.
- Open question — cascade performance: subquery-per-FK (one extra round-trip per FK in the cascade) vs a single annotated pass (one query that joins every cascaded relation). The upstream is subquery-per-FK; benchmark both before committing.
- Open question — M2M / reverse-relation visibility: the upstream cascade explicitly skips M2M and reverse FK. Decide whether to extend coverage here or defer to a sibling card; if deferring, name the follow-up card in the spec.
- Open question — `check_permissions` API surface: does the existing per-field filter-denial `check_<field>_permission(self, request)` survive in its current form, get renamed to disambiguate from the new field-level read gate (`FieldSet.check_<field>_permission(info)` per `TODO-BETA-059-0.1.1`), or get deprecated in favor of a unified shape? Spec must answer before implementation.

#### Note

- full subsystem: `apply_cascade_permissions`, per-field `Meta` permission hooks, and optimizer `Prefetch`-downgrade integration. New `permissions.py` (or package) + `docs/SPECS/spec-034-permissions-0_0_10.md` + tests.

#### Card references

- Dependency: future `DjangoConnectionField` -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- Related: `TODO-BETA-059-0.1.1` - `FieldSet` declarative field-level behavior (`Meta.fields_class`)

<a id="connection_aware_optimizer_planning"></a>
### [DONE-033-0.0.9 - Connection-aware optimizer planning](KANBAN.html#connection_aware_optimizer_planning)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
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

#### Definition of done

- [x] New spec at `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (the canonical structured filename).
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
- strawberry-graphql-django plans connection selections natively; graphene-django has only rudimentary connection-aware optimization (⚛️ parity-adjacent).

#### Dependencies

- gated on `DONE-030-0.0.9` / Relay decisions.

#### Note

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

- Related: gated on `DONE-030-0.0.9` / Relay decisions. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)

<a id="full_relay_story_node_connection_root_validation"></a>
### [DONE-032-0.0.9 - Full Relay story (Node + Connection + Root + validation)](KANBAN.html#full_relay_story_node_connection_root_validation)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
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
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) | shipped (`0.0.14`) |
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

- `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)

#### Scope

- **Required arguments**: `first: Int`, `after: String`, `last: Int`, `before: String`. Backward pagination (`last`/`before`) is required by the Relay spec.
- Reverse-FK and M2M relations on those types expose their Connection counterparts

#### Definition of done

- [x] New spec: `docs/SPECS/spec-032-full_relay-0_0_9.md` covering all eight goals above with worked examples and decision rationale.
- [x] `DjangoNodeField` and `DjangoNodesField` exported from the package public surface; both wired through the registry's GlobalID decode path and the per-type `get_queryset`.
- [x] Reverse-FK and M2M relations on `relay.Node`-implementing types expose their Connection counterparts; `Meta.relation_shapes` opt-out documented.
- [x] Cursor pagination math passes the package's hand-authored Relay-spec conformance suite (the `first`/`after`/`last`/`before`/`pageInfo` edge cases), against both a root connection and a synthesized relation connection.
- [x] `Meta.connection = {"total_count": True}` adds a `totalCount` field that runs `qs.count()` on the unpaginated post-filter queryset.
- [x] Filter / order arguments accepted on Connection fields when the corresponding `*_class` is declared on the type.
- [x] Permission-aware Node lookup: `node(id:)` returns `null` for hidden rows; no existence leak via error timing.
- [x] Six schema-validation diagnostics from Goal 6 raise `ConfigurationError` with the documented messages.
- [x] `django_strawberry_framework.testing.relay` module exposes `global_id_for(type_cls, id)` and `decode_global_id(gid)`.
- [x] The fakeshop `library` HTTP test suite gains Relay-shaped queries (refetch, paginated connection, cursor round-trip, `totalCount`). Fakeshop `products` activation lights up the full Relay surface as part of `TODO-BETA-066-0.1.5`.
- [x] 100% coverage across the new code paths; tests pin both happy paths and every validation failure.

#### Files likely touched

- `django_strawberry_framework/testing/relay.py` (new) — test helpers

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py::DjangoObjectType.get_node` implements the Relay `Node` interface by running `cls.get_queryset(model.objects, info).get(pk=id)`, so graphene_django's full Relay story routes single-object id lookups through the type's visibility hook — the same Node + global-id + permission-aware root surface this card assembles, hence required parity.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py::resolve_model_nodes` (and `resolve_model_node`) resolve `relay.GlobalID` values to model instances while running the type's `get_queryset` (via `run_type_get_queryset`), and `DjangoListConnection.resolve_connection` provides the connection half — together the Node + Connection + validated-root Relay story this card mirrors, so the strawberry_django parity is required.

#### Dependencies

- `DONE-030-0.0.9` (`DjangoConnectionField`) — **hard dependency**; this card unblocks when DONE-030-0.0.9 lands.
- `DONE-027-0.0.8` (Filtering subsystem) — soft dependency for the filter argument on Connections.
- `DONE-028-0.0.8` (Ordering subsystem) — soft dependency for the orderBy argument on Connections.
- `DONE-033-0.0.9` (Connection-aware optimizer planning) — ships in parallel; the Node entry points and the relation-as-Connection upgrade both rely on the walker recognizing `edges { node { ... } }`.
- `DONE-034-0.0.10` (Permissions subsystem) — soft dependency; the Node entry points respect `get_queryset` immediately and integrate with declared permissions when DONE-034-0.0.10 lands.

#### Decision

- ~~`GlobalID` mapping decision~~ — Strawberry-supplied `id: GlobalID!` from the Relay interface replaces the synthesized `id: int!`; Django primary key remains projected as a connector column for the optimizer (Decision 2 of [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-015]).
- Non-Strawberry-interface classes in `Meta.interfaces` → rejected at validation with the offending class name.

#### Note

- eight-goal umbrella for the complete Relay surface (Root `node`/`nodes` fields, relation-as-Connection upgrade, cursor contracts, permission integration, schema-validation diagnostics, test helpers, fakeshop activation). New `relay.py` + `test/relay.py` + finalizer changes + spec. Cursor mechanics overlap with DONE-030-0.0.9; this card is the connective tissue tying it all together.
- ~~`Meta.interfaces` design~~ — `Meta.interfaces` accepted end-to-end for any Strawberry interface; `(relay.Node,)` activates the Node foundation.
- ~~Default `resolve_*` injection~~ — `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes` defaults injected when `relay.Node` is in `Meta.interfaces`; consumer overrides preserved via Strawberry's `__func__` identity test.
- ~~`is_type_of` injection~~ — Unconditional on every `DjangoType`; consumer-declared `is_type_of` preserved.
- ~~`CompositePrimaryKey` rejection~~ — Django 5.2+ composite-pk models raise `ConfigurationError` at finalization with the documented escape hatch (`id: relay.NodeID[...]` annotation).
- `node(id: GlobalID!): Node` — single-object refetch. Decodes the GlobalID, dispatches to the type's `resolve_node`, returns the resolved object. Returns `null` if the GlobalID decodes to a type/ID the requesting user can't see (respects `get_queryset`).
- `nodes(ids: [GlobalID!]!): [Node]!` — batch refetch. Decodes each GlobalID, dispatches per-type to `resolve_nodes` (batched), returns results in input order. Missing IDs become `null` entries (preserves positional correspondence).
- **Implicit upgrade** (default): every `DjangoType` whose `Meta.interfaces` includes `relay.Node` automatically exposes its reverse-FK and M2M relations as Connections in addition to the existing `list[T]` shape. Field names follow a stable convention (`itemsConnection: ItemConnection` alongside `items: list[Item]`).
- **Explicit-only**: consumers who want only Connections (or only lists) on a relation declare `Meta.relation_shapes = {"items": "connection"}` (or `"list"`, or `"both"` — `"both"` is the default for Relay types).
- **Cursor format**: opaque base64-encoded payload by default (`b64("offset:N")`). Documented as opaque — clients must not parse it. `Meta.cursor_field` for stable column-based cursors is **out of scope** for this card; lives in BETTER item 39 sub-feature 3.
- **`pageInfo`**: emits the four standard fields (`hasNextPage`, `hasPreviousPage`, `startCursor`, `endCursor`) with correct semantics — including the spec-mandated *"the connection MUST resolve `hasNextPage` correctly even when the consumer didn't request it"* invariant.
- **Edge cases**: `first: 0` returns empty edges + `pageInfo`. `first: N` with N > remaining rows returns the actual remainder. `after` cursor for a row that no longer exists falls through to the next existing row (no error). Both `first` and `last` in the same query is rejected with a typed error.
- **`totalCount`**: an opt-in field on every Connection (`Meta.connection = {"total_count": True}`). When selected, runs `qs.count()` on the *unpaginated* queryset (post-filter, pre-slice). Documented as the canonical Relay-compatible total-count surface.
- `filter: <Type>FilterInput` — generated from `Meta.filterset_class` (composes with `DONE-027-0.0.8`)
- `orderBy: [<Type>OrderInput!]` — generated from `Meta.orderset_class` (composes with `DONE-028-0.0.8`)
- `search: String` — generated from `Meta.search_fields` (composes with `TODO-BETA-060-0.1.2` — note: search is `1.0.0` scope, ships after `0.1.0`; until then, search arg is absent)
- decode the GlobalID server-side (never trust the client's claim of which type the ID belongs to)
- dispatch to the resolved type's `resolve_node` (which honors `cls.get_queryset(qs, info)`)
- return `null` for rows the user can't see (not an error — the Relay spec requires `null`, not an exception)
- never reveal *existence* of hidden rows through error timing or status codes
- `relay.GlobalID`, `relay.NodeID[...]`, `relay.Connection`, `relay.ListConnection`, `relay.Edge`, `relay.PageInfo` in `Meta.interfaces` → rejected with a message naming the helper and explaining it's a scalar / annotation / field-type rather than an interface.
- `Meta.connection = {...}` declared on a type that doesn't include `relay.Node` in `Meta.interfaces` → rejected with a message suggesting either remove the `connection` key or add `relay.Node` to interfaces.
- A `DjangoNodeField()` query field on a schema with **no** `DjangoType`s declaring `relay.Node` → rejected at finalization with *"node lookup configured but no Node types registered."*
- `node(id:)` and `nodes(ids:)` resolve real product / category / item / entry GlobalIDs
- Live HTTP tests under `examples/fakeshop/test_query/` exercise the full Relay query shape (refetch, paginated connection, cursor round-trip, `totalCount`)
- Type-rename GlobalID migrations (Django-migrations-style history that lets old-format IDs decode alongside new)
- Polymorphic connections (`Connection[Interface]` with auto-dispatched concrete types per edge)
- `Meta.cursor_field` for stable cursors keyed on a deterministic column
- Auto-upgrade reverse FK / M2M to Connection based on a row-count threshold
- Refetchable container schema metadata for `useRefetchableFragment`
- Permission-aware cursor decoding (cursor decode re-runs `get_queryset` so privileged cursors don't leak)
- `django_strawberry_framework/connection.py` — main implementation (shipped as part of `DONE-030-0.0.9`)
- `django_strawberry_framework/relay.py` (new) — `DjangoNodeField`, `DjangoNodesField`, GlobalID decode dispatch
- `django_strawberry_framework/types/base.py` — `Meta.connection` / `Meta.relation_shapes` validation
- `django_strawberry_framework/types/finalizer.py` — auto-upgrade reverse-FK / M2M to Connection
- `tests/test_relay_node_field.py`, `tests/test_relay_connection.py` (new)
- `examples/fakeshop/test_query/test_library_api.py` — Relay-shape HTTP tests
- `examples/fakeshop/apps/products/schema.py` — Relay surface activation (lit up at fakeshop activation time)
- `docs/SPECS/spec-032-full_relay-0_0_9.md` (new)
- `docs/GLOSSARY.md` — Relay surface description
- Relay node refetch from Apollo / Relay Compiler clients (the *"Relay just works"* end state for `1.0.0`)
- Fakeshop product-catalog Relay activation (Goal 8)
- Per-type `useFragment` / `useRefetchableFragment` patterns (mechanics; the schema-side `@refetchable` directive support lives in BETTER item 39 sub-feature 5)
- Every BETTER item 39 sub-feature builds on this card's mechanics
- Fakeshop products-app activation (`examples/fakeshop/apps/products/schema.py`): replace the four `Query` list resolvers (`all_categories` / `all_items` / `all_properties` / `all_entries`) with `DjangoConnectionField`s for the 1-to-1 `django-graphene-filters` cookbook mirror (connections-only — the cookbook Query is `all_object_types = AdvancedDjangoFilterConnectionField(ObjectTypeNode)` with no list resolvers). The four `*Type` classes are already Relay-Node-shaped with `filterset_class` / `orderset_class` wired, so only the root-field shape changes; `relay.node()` / root `Node.Field` refetch is the separate root-Node goal of this card. Deferred from the `DONE-030-0.0.9` (`DjangoConnectionField`) cycle and gated on `DONE-033-0.0.9` (connection-aware optimizer): a `0.0.9` `DjangoConnectionField` derives an empty optimizer plan, so a connections-only products conversion must land with DONE-033-0.0.9 to avoid regressing the `test_products_optimizer_*` SQL-shape coverage.

#### Card references

- Dependency: blocked on `DONE-030-0.0.9` (`DjangoConnectionField`). When the connection field lands, this card unblocks and ships in the same release. The post-`1.0.0` "Relay magic" differentiators (type-rename GlobalID migrations, polymorphic connections, stable cursors, refetchable containers, permission-aware cursor decoding) live separately in [`BACKLOG.md`][backlog] item 39 — they extend this story rather than block it. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- Related: `filter: <Type>FilterInput` — generated from `Meta.filterset_class` (composes with `DONE-027-0.0.8`) -> `DONE-027-0.0.8` - Filtering subsystem
- Related: `orderBy: [<Type>OrderInput!]` — generated from `Meta.orderset_class` (composes with `DONE-028-0.0.8`) -> `DONE-028-0.0.8` - Ordering subsystem
- Related: `search: String` — generated from `Meta.search_fields` (composes with `TODO-BETA-060-0.1.2` — note: search is `1.0.0` scope, ships after `0.1.0`; until then, search arg is absent) -> `TODO-BETA-060-0.1.2` - `Meta.search_fields` support
- Related: `DONE-030-0.0.9` (`DjangoConnectionField`) — **hard dependency**; this card unblocks when DONE-030-0.0.9 lands. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- Related: `DONE-033-0.0.9` (Connection-aware optimizer planning) — ships in parallel; the Node entry points and the relation-as-Connection upgrade both rely on the walker recognizing `edges { node { ... } }`. -> `DONE-033-0.0.9` - Connection-aware optimizer planning
- Related: `DONE-034-0.0.10` (Permissions subsystem) — soft dependency; the Node entry points respect `get_queryset` immediately and integrate with declared permissions when DONE-034-0.0.10 lands. -> `DONE-034-0.0.10` - Permissions subsystem
- Related: The fakeshop `library` HTTP test suite gains Relay-shaped queries (refetch, paginated connection, cursor round-trip, `totalCount`). Fakeshop `products` activation lights up the full Relay surface as part of `TODO-BETA-066-0.1.5`. -> `TODO-BETA-066-0.1.5` - Fakeshop GraphQL schema activation

<a id="django_model_based_globalid_encoding"></a>
### [DONE-031-0.0.9 - Django-model-based GlobalID encoding](KANBAN.html#django_model_based_globalid_encoding)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
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

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene/relay/node.py::Node.to_global_id` — graphene-django Relay nodes encode the GlobalID as base64 `<GraphQL type name>:<id>` (type-name-anchored). Tagged **parity-adjacent, not required**: the type-anchored convention itself already shipped at parity in `DONE-015-0.0.5` (the Relay-supplied `id: GlobalID!`). This card preserves that exact convention as the opt-in `type` strategy and makes a Django-model-anchored payload (`app_label.model:id`, e.g. `products.item:42`) the new default — extending the upstream GlobalID surface with a Django-idiomatic encoding neither upstream offers.
- `strawberry.relay.GlobalID` (consumed by strawberry-graphql-django; `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py` wires the Relay node types) encodes `to_base64(type_name, node_id)` — also type-name-anchored. Same parity-adjacent relationship: the standard convention stays available as the `type` strategy, while the model-anchored default plus the `Meta.globalid_strategy` override and the `RELAY_GLOBALID_STRATEGY` setting are the beyond-parity differentiator. Tagged `adjacent` (not `required`) for both upstreams so the Alpha cut stays parity-honest — GlobalID parity proper was met in `DONE-015-0.0.5`.

#### Why it matters

- The standard Relay convention bakes the GraphQL type name into durable object identity. In Django apps the model is the durable thing; the GraphQL type is a refactor-friendly facade.
- Getting this right before `1.0.0` lets consumers rename GraphQL types without invalidating every cached GlobalID. Waiting until after Full Relay ships turns the same decision into migration work.

#### Note

- Original backlog score: Realistic 9/10, Impact 8/10, Difficulty 3/10; bang-for-buck score 24.0.
- Legitimate legacy mode remains available: projects that intentionally scope identity by GraphQL type can opt into the `type` strategy per type or project-wide.

#### Card references

- Related: This card should land before Full Relay because root `node(id:)`, `nodes(ids:)`, and refetch helpers make GlobalID encoding a public durability contract. -> `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)
- Related: `DjangoConnectionField` can land before this card because connection pagination does not require changing the Relay GlobalID payload. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- Related: `DONE-015-0.0.5` - 0.0.5 Relay interfaces and Node foundation

<a id="djangoconnectionfield_relay_connection_field"></a>
### [DONE-030-0.0.9 - `DjangoConnectionField` (Relay connection field)](KANBAN.html#djangoconnectionfield_relay_connection_field)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
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

Strawberry analogue of graphene-django's `AdvancedDjangoFilterConnectionField`. Wires the shipped Layer-3 sidecars into a Relay-shaped connection: accepts `filter:` from `Meta.filterset_class` (`DONE-027-0.0.8`), `orderBy:` from `Meta.orderset_class` (`DONE-028-0.0.8`), plus `first`/`after`/`last`/`before` cursor pagination and opt-in `totalCount`. The `search:` arg activates when `TODO-BETA-060-0.1.2` lands; `FieldSet` selection composition is layered in by `TODO-BETA-059-0.1.1`. Central read-side primitive — every Layer-3 argument composes through this field.

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

- [x] Add `docs/SPECS/spec-030-connection_field-0_0_9.md`.
- [x] Implement `django_strawberry_framework/connection.py`.
- [x] Add `tests/test_connection.py`.
- [x] Decide whether full Relay support belongs here or a separate `relay/` subpackage.
- [x] Promote `DjangoConnectionField` only when end-to-end schema usage is tested.
- [x] When the wrapped type declares `Meta.filterset_class`, the connection field exposes `filter: <Type>FilterInput` and routes input values through the filterset's `apply_sync` / `apply_async` pair.
- [x] When the wrapped type declares `Meta.orderset_class`, the connection field exposes `orderBy: [<Type>OrderInput!]` and routes through the orderset's `apply_sync` / `apply_async` pair.
- [x] Connection field composes with `cls.get_queryset(queryset, info)` — visibility scoping runs before any filter / order / cursor work.
- [x] Optimizer cooperation: the connection-aware planner (`DONE-033-0.0.9`) layers on without retrofit; this card ships against the existing flat-selection walker and the connection-aware walker takes over when DONE-033-0.0.9 lands.
- [x] Live HTTP coverage in `examples/fakeshop/test_query/` exercises a real round-trip with filter + orderBy + cursor + totalCount on a Relay-Node-shaped type.

#### Foundation-slice seam

- `finalize_django_types()` is the single architectural entry point that `DjangoConnectionField(DjangoType)` (and `DjangoNodeField`) will auto-trigger as their wrapper.
- An auto-trigger wrapper must respect the single-threaded-setup window: either be constrained to schema-construction time, or acquire a real lock around the finalizer.
- Connection-aware optimizer planning is its own follow-up slice (`DONE-033-0.0.9`); the foundation slice did not exercise nested connection prefetch shapes.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/fields.py::DjangoConnectionField.connection_resolver` is graphene_django's Relay connection field: it reads `first`/`last`/`before`/`after`, enforces the `first`-or-`last` guard, runs the type's `get_queryset` for visibility, then slices via `resolve_connection` — the exact composition (`get_queryset` -> filter -> order -> cursor slice) this card's `DjangoConnectionField` ships, so the graphene_django parity is required.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/field.py::StrawberryDjangoConnectionExtension.resolve` resolves a Django queryset and hands it to `connection_type.resolve_connection(nodes, info, before=, after=, first=, last=, max_results=)`, layering the relay pagination args on top of the field's auto-derived filter/order arguments — the Strawberry-side analogue of graphene's filter-connection field this card targets, making the strawberry_django parity required.
- both upstreams ship Relay-shaped connection fields.

#### Dependencies

- `FilterSet` (`DONE-027-0.0.8`)
- `OrderSet` (`DONE-028-0.0.8`)
- Relay/interface decisions
- `FieldSet` — **deferred to `TODO-BETA-059-0.1.1`** (post-Alpha); field-selection composition is layered on after the connection field ships, not a 0.0.9 blocker.
- `DjangoType` consumer-DX cleanup pass (`DONE-029-0.0.9`) - schema-construction examples are current before `DjangoConnectionField` becomes the new consumer pattern.

#### Note

- Filtering and Ordering ship before this card lands, so `DjangoConnectionField` consumes the existing filter and order argument factories on day one. `FieldSet` selection composition is layered in by `TODO-BETA-059-0.1.1`; the `search:` arg activates when `TODO-BETA-060-0.1.2` lands.
- the central read-side primitive — the Relay surface and all Layer-3 arguments compose through it.
- central Relay-shaped connection field plus cursor-pagination math; the integration point that filters / orders / aggregation / field-selection / optimizer all compose through. New `connection.py` + `docs/SPECS/spec-030-connection_field-0_0_9.md` + tests.

#### Card references

- Dependency: `FilterSet` (`DONE-027-0.0.8`) -> `DONE-027-0.0.8` - Filtering subsystem
- Related: Connection-aware optimizer planning is its own follow-up slice (`DONE-033-0.0.9`); the foundation slice did not exercise nested connection prefetch shapes. -> `DONE-033-0.0.9` - Connection-aware optimizer planning
- Dependency: `OrderSet` (`DONE-028-0.0.8`) -> `DONE-028-0.0.8` - Ordering subsystem
- Related: once filters/orders are stable. FieldSet integration is deferred to `TODO-BETA-059-0.1.1` — `DjangoConnectionField` ships against the Layer-2 surface in 0.0.9 and gains field-selection composition when FieldSet lands. -> `TODO-BETA-059-0.1.1` - `FieldSet` declarative field-level behavior (`Meta.fields_class`)
- Dependency: `DjangoType` consumer-DX cleanup pass (`DONE-029-0.0.9`) - schema-construction examples are current before `DjangoConnectionField` becomes the new consumer pattern. -> `DONE-029-0.0.9` - `DjangoType` consumer-DX cleanup pass
- Related: `TODO-BETA-060-0.1.2` - `Meta.search_fields` support

<a id="djangotype_consumer_dx_cleanup_pass"></a>
### [DONE-029-0.0.9 - `DjangoType` consumer-DX cleanup pass](KANBAN.html#djangotype_consumer_dx_cleanup_pass)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
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
- **Slice 3** — `Meta.nullable_overrides` GraphQL-layer nullability override. New public `Meta` key (and possibly a companion `Meta.required_overrides`) letting consumers decouple the GraphQL type's nullability from the underlying Django column without an `AlterField` migration or a custom resolver. Implemented inside `django_strawberry_framework/types/base.py` and `django_strawberry_framework/types/converters.py`'s scalar-resolution path. Tests in `tests/types/test_converters.py` (override + collision cases) plus a live HTTP test on the library or scalars app demonstrating the override flipping the GraphQL type's nullability without touching the model column. **Requires spec**: `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` — open design decisions include dict-of-name vs tuple-set per direction, interaction with `Meta.exclude`, error behavior when both override sets name the same field, choice-field interaction, and FK / reverse-FK interaction.

#### Definition of done

- [x] **Slice 1**: every `extensions=[DjangoOptimizerExtension()]` instance form replaced with the factory-callable equivalent in tests, examples, and consumer-facing docs. `uv run pytest` shows zero `DeprecationWarning` about Strawberry extension instances. CHANGELOG entry under `[Unreleased]` `### Changed`.
- [x] **Slice 2**: `django_strawberry_framework/management/commands/inspect_django_type.py` ships with module + class docstring, `add_arguments` taking a positional `type_dotted_path`, and `handle` printing the resolved field table. Tests via `examples/fakeshop/tests/test_commands.py` using `call_command`. `docs/GLOSSARY.md` adds an entry; `docs/TREE.md` lists the new module under `management/commands/`. CHANGELOG entry under `[Unreleased]` `### Added`.
- [x] **Slice 3**: `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` written and reviewed; `Meta.nullable_overrides` (and `Meta.required_overrides` if the spec confirms it) implemented; tests cover override-applies, override-rejects-unknown-field, override-collides-with-other-direction error, and override-on-choice-field. `docs/GLOSSARY.md` adds an entry; live HTTP test in `examples/fakeshop/test_query/` demonstrates the override flipping nullability for a real model field. CHANGELOG entry under `[Unreleased]` `### Added`.

#### Foundation-slice seam

- Slice 1 has no foundation interaction; it's a sweep across already-shipped surfaces.
- Slice 2 reads `DjangoTypeDefinition` populated by `finalize_django_types()`; the command is a strict consumer of the existing introspection surface.
- Slice 3 plugs into `DjangoType._build_annotations` (the converter loop in `django_strawberry_framework/types/base.py`) and the scalar-resolution path in `django_strawberry_framework/types/converters.py`. No finalizer changes — overrides apply at type-construction time, before finalization.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py::DjangoObjectType.__init_subclass_with_meta__` is graphene_django's consumer type-declaration surface, deriving GraphQL field nullability from the Django column (`required = not (field.blank or field.null)` in `converter.py`) and policing `Meta` keys like `fields`/`exclude`/`filterset_class` — the same `DjangoType`/`Meta` DX this card's cleanup pass refines (including the `Meta.nullable_overrides` decoupling), so the graphene_django parity is required.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py::is_optional` decides a `DjangoType` field's nullability straight from `model_field.null`/`blank`, with no consumer hook to override it independent of the column — the gap this card's `Meta.nullable_overrides` (Slice 3) closes against the strawberry_django type-definition surface, making the strawberry_django parity required.

#### Note

- three independent slices: Slice 1 `extensions=` factory-form sweep (XS, ~30 min, no spec), Slice 2 `inspect_django_type` command (S, sub-1-day), Slice 3 `Meta.nullable_overrides` (M, needs spec, deferrable to `0.0.9`). Smallest of the three `0.0.8` cards.
- **Slice 1**: defensive — both upstreams already use the factory-callable form in their consumer docs. Strawberry's removal runway is multiple releases, but landing the migration in 0.0.8 keeps the package's surface aligned with the upstream recommendation.
- **Slice 2**: differentiating — neither `graphene-django` nor `strawberry-graphql-django` ships an equivalent `manage.py inspect_*` diagnostic for their type definitions. Consumers currently introspect by hand against the GraphQL schema after construction. This command moves that diagnostic to the type-definition layer, before schema construction.
- **Slice 3**: ⚛️&🍓 required — `strawberry_django.field(required=True/False)` allows per-field GraphQL nullability override against the Django column's native nullability. `graphene_django` allows the same via `DjangoObjectType.Meta.fields` plus per-field overrides on the type class. This card surfaces the same capability through a single `Meta`-key dict that the rest of the package's `Meta`-shaped API already prefers.

<a id="ordering_subsystem"></a>
### [DONE-028-0.0.8 - Ordering subsystem](KANBAN.html#ordering_subsystem)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
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

#### Definition of done

- [x] Add `docs/SPECS/spec-028-orders-0_0_8.md`.
- [x] Add `django_strawberry_framework/orders/`.
- [x] Add mirrored `tests/orders/`.
- [x] Promote `Meta.orderset_class` only when ordering is applied end-to-end.
- [x] Support simple fields and relation paths.
- [x] Define interaction with filters and connection field.
- [x] Keep ordering declarations introspectable from the owning type/query surface.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField.resolve_queryset` special-cases the `order_by` filter argument (`to_snake_case(v)` before passing it into the filterset), so graphene_django exposes ordering through django-filter's `OrderingFilter` as a first-class connection argument — the directly-comparable ordering surface this card ships, hence required parity.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/ordering.py::apply` walks an `order` type via `process_order` and emits `queryset.order_by(*args)`, where each field resolves through `Ordering.resolve` (the `ASC`/`DESC` plus `NULLS_FIRST`/`NULLS_LAST` enum) into a Django `OrderBy` — the same per-field, list-shaped ordering input this card's `orderBy` argument provides, so the strawberry_django parity is required.

#### Note

- Shipped the ordering subsystem in `0.0.8`. [`OrderSet`][glossary-orderset], [`RelatedOrder`][glossary-relatedorder], and [`Meta.orderset_class`][glossary-metaorderset_class] (promoted out of `DEFERRED_META_KEYS`) land at [`django_strawberry_framework/orders/`][orders] across five files (`base.py`, `sets.py`, `factories.py`, `inputs.py`, `__init__.py`); `tests/orders/` mirrors the layout. Five-layer lazy-resolution pipeline borrowed from `django-graphene-filters` with the same Strawberry-adapted Layer 5 the Filtering subsystem just shipped (`Annotated[\"TypeName\", strawberry.lazy(\"django_strawberry_framework.orders.inputs\")]` over module globals); the shared `LazyRelatedClassMixin` is reused from the neutral `sets_mixins` module via sibling import (per H1 of `spec-028-orders-0_0_8` rev3 — `sets_mixins.py` carries both `LazyRelatedClassMixin` and `ClassBasedTypeNameMixin` for the set family). Layer 6 (dynamic OrderSet generation) deferred to `0.0.9` alongside `DjangoConnectionField` per Decision 12 of `docs/SPECS/spec-028-orders-0_0_8.md`. The public `Ordering` enum borrowed verbatim from `strawberry-django` (six members: ASC / DESC / ASC_NULLS_FIRST / ASC_NULLS_LAST / DESC_NULLS_FIRST / DESC_NULLS_LAST) — NULLS positioning honored via Django `F(value).asc/desc(nulls_first=...)` expressions. The list-shaped `orderBy: [<T>OrderInputType!]` argument's element order IS the tie-breaker mechanism. The **resolver-facing API is the classmethod pair `OrderSet.apply_sync(input_value, queryset, info)` and `OrderSet.apply_async(input_value, queryset, info)`** (sync resolvers call the former; async resolvers await the latter), mirroring the shipped filter subsystem's shape. The apply pipeline runs `check_permissions` with **active-input-only scope** (per-field `check_<field>_permission` gates fire only when the consumer's input names the field); extracts the request from `info.context.request` (with an `isinstance(info.context, HttpRequest)` fallback); applies `queryset.order_by(*OrderBy_expressions)` after visibility scoping (`<OwnerType>.get_queryset`) and after optional filter narrowing (`<TypeName>Filter.apply_*`). The new `order_input_type(BranchOrder)` helper produces the resolver-annotation shape; the finalizer enforces orphan validation by raising `ConfigurationError` for any OrderSet referenced via `order_input_type` but never wired via `Meta.orderset_class` (tracked via `_helper_referenced_ordersets`). `registry.clear()` co-clears the order input namespace via `clear_order_input_namespace()` AND clears `_helper_referenced_ordersets` — alongside the already-shipped filter clears. Per-package input-class namespace is separate from the model-to-`DjangoType` registry AND from the filter-input namespace (`Meta.primary` design preserved). `Meta.orderset_class` promotion runs through finalizer phase 2.5 via `_bind_ordersets()` with four ordered subpasses mirroring the filter side's discipline; the phase binds `_owner_definition`, calls `get_fields()` only after all owners are bound, materializes each generated input class as a module global of `django_strawberry_framework.orders.inputs` before `strawberry.Schema(...)` runs. [`examples/fakeshop/apps/library/`][fakeshop-library] grows `orders.py` (carrying `BranchOrder` / `ShelfOrder` / `BookOrder` / `LoanOrder` / `PatronOrder`) and `orders_genre.py` (carrying `GenreOrder` — cross-module fixture for the Layer-2 absolute-import-path test) wired through `Meta.orderset_class`; root resolvers accept `order_by:` via `order_input_type(<Name>Order)` annotations and call `<OwnerType>.get_queryset(...)` then optionally `<TypeName>Filter.apply_*` then `OrderSet.apply_*`. [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] grows exactly 14 live HTTP tests covering scalar ASC / scalar DESC_NULLS_LAST on `Book.subtitle` (per B3 of rev3) / forward-FK / reverse-FK with denormalized-multiplicity-pinned / M2M absolute-import-path RelatedOrder / flat-shorthand path (`shelf__code` → `shelfCode`) / filter + order composition / optimizer cooperation / root `get_queryset` honoring / split-pair active-input-only scalar `check_<field>_permission` (denies-for-active + quiet-for-inactive) / active-branch relation-level permission gate (`check_shelves_permission` per H3 of rev3) / multi-field priority via list-element ordering / empty-list no-op / null-direction no-op. Spec: `docs/SPECS/spec-028-orders-0_0_8.md`. After this card moves to Done, `0.0.9` follow-up cards can start; no version files change here unless the maintainer explicitly gives the version-bump command.

#### Card references

- Related: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField #"order_by"` — connection field accepts an `order_by` argument that composes through `django_filters.OrderingFilter` declared on the FilterSet. Graphene has no separate ordering primitive; ⚛️ parity is met by the filter subsystem (`DONE-027-0.0.8`) rather than this card. -> `DONE-027-0.0.8` - Filtering subsystem

<a id="filtering_subsystem"></a>
### [DONE-027-0.0.8 - Filtering subsystem](KANBAN.html#filtering_subsystem)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
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

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField.resolve_queryset` instantiates the type's `Meta.filterset_class` with the GraphQL args as `data`, calls `filterset.is_valid()`, and returns `filterset.qs` (raising `ValidationError` from `filterset.form.errors` otherwise) — this is the same filterset-driven, validation-gated queryset narrowing this card ships, so the graphene_django parity is required.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/filters.py::apply` runs `process_filters(...)` over a strawberry filter type and applies the resulting `Q` via `queryset.filter(q)`, with `StrawberryDjangoFieldFilters.arguments` auto-deriving the `filters:` argument from the type definition — the consumer-facing filter-input surface this card mirrors, making the strawberry_django parity required.
- both upstreams ship a FilterSet / filter surface; `django-graphene-filters` is the cookbook source.

#### Note

- the milestone anchor: six-layer lazy-resolution filtering pipeline, `FilterSet` / `RelatedFilter` / `Meta.filterset_class`, parity-floor filter primitives, finalizer phase-2.5 wiring, 14 live HTTP tests.

<a id="scalar_conversion_end_to_end_coverage_in_the_fakeshop_example"></a>
### [DONE-026-0.0.7 - Scalar conversion end-to-end coverage in the fakeshop example](KANBAN.html#scalar_conversion_end_to_end_coverage_in_the_fakeshop_example)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `example-app`, `graphql-api`, `scalars`, `tests`
- Spec: [spec-026-scalar_conversion_fakeshop-0_0_7.md](docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`BigInt` scalar](docs/GLOSSARY.md#bigint-scalar) | shipped (`0.0.6`) |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |
| [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types) | shipped (`0.0.4`) |

#### Scope

- Full non-null wire-format sweep covering every field on `ScalarSpecimen`
- All-NULL nullable wire format covering every nullable converter branch

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py` converts the full Django field set to GraphQL scalars via singledispatch: `convert_big_int_field` (`BigIntegerField → graphene.BigInt`), `convert_field_to_uuid` (`UUIDField`), `convert_json_field_to_string` (`JSONField`), `convert_datetime_to_string`/`convert_date_to_string`, `convert_field_to_decimal`. This card moves the framework's equivalent numeric/date/JSON/UUID converter rows to live `/graphql/` HTTP coverage in both nullable and non-null shapes (incl. a real `BigIntegerField` on `Patron`), a direct match against graphene-django's scalar-conversion feature, justifying the graphene_django required claim.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py::field_type_map` maps the same set (`BigIntegerField → int`, `DateField → datetime.date`, `DateTimeField → datetime.datetime`, `DecimalField → decimal.Decimal`, `UUIDField → uuid.UUID`, `JSONField → strawberry.scalars.JSON`); this card's `ScalarSpecimen`/`NullableScalarSpecimen` example app plus eight live HTTP tests exercise the framework's equivalent conversion end-to-end in both shapes, a direct match justifying the strawberry_django required claim. (Both claims pre-exist and are kept; the card is example/test coverage but the behavior under test is genuine scalar-conversion parity, not pure housekeeping.)
- both upstreams ship scalar conversion for the full numeric / date / JSON / UUID set; this card moves those converter rows to live `/graphql/` HTTP coverage in both nullable and non-null shapes.

#### Note

- new `apps.scalars` example app (paired non-null / nullable models, self-FK + cross-model `SET_NULL` FK) + eight live HTTP tests + a real-domain `BigIntegerField` on `Patron`.
- `ScalarSpecimen` — every scalar field non-null, exposed via `ScalarSpecimenType`. Adds an intra-model self-FK `parent` (`related_name="children"`) so the example exercises self-referential FK planning under the optimizer.
- `NullableScalarSpecimen` — every scalar field nullable (`null=True, blank=True`), exposed via `NullableScalarSpecimenType`. Adds a cross-model FK `partner: ForeignKey(ScalarSpecimen, on_delete=SET_NULL, related_name="nullable_partners")` — the only `SET_NULL` ondelete in the example tree, and the only cross-model FK in the scalars app.
- The pairing is deliberate (not a single model with paired fields). It exercises **upstream code paths no other example app reaches**: Django's two-`CreateModel` initial migration path, the registry / `finalize_django_types()` resolving sibling `DjangoType` classes in one app, Strawberry type registration across sibling types in one schema build, the optimizer planning across two managed models in one query, and `SET_NULL` ondelete behavior.
- `apps.scalars.schema` composes two root resolvers (`all_scalar_specimens`, `all_nullable_scalar_specimens`) into the project root `Query` at [`examples/fakeshop/config/schema.py`][example-schema]; `ScalarsConfig` lands in `INSTALLED_APPS` at [`examples/fakeshop/config/settings.py`][settings].
- Signed-negative `BigInt` round-trip
- `BigInt`-at-zero edge case
- Schema introspection asserting `BigInt` converter resolves correctly in both shapes (`NON_NULL` on `ScalarSpecimenType`; bare `SCALAR` on `NullableScalarSpecimenType`)
- Cross-model `partner` FK linkage round-trip
- Reverse-FK `nullablePartners` exposure
- Self-FK `parent` / `children` traversal

<a id="warning_free_scalar_registration_via_strawberryconfigscalar_map"></a>
### [DONE-025-0.0.7 - Warning-free scalar registration via `StrawberryConfig.scalar_map`](KANBAN.html#warning_free_scalar_registration_via_strawberryconfigscalar_map)

- Priority: Medium
- Status: Done
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

#### Verified in upstream

- package-specific scalar-registration plumbing (`StrawberryConfig.scalar_map` via `strawberry_config()`); not an upstream-parity primitive.

#### Note

- `strawberry_config()` factory registering `BigInt` via `scalar_map` and removing the deprecation-suppression block; a documented breaking change in alpha.

<a id="django_trac_37064_hardening_safe_wrap_connection_method"></a>
### [DONE-024-0.0.7 - Django Trac #37064 hardening + `safe_wrap_connection_method`](KANBAN.html#django_trac_37064_hardening_safe_wrap_connection_method)

- Priority: Low
- Status: Done
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

#### Verified in upstream

- defensive hardening unique to this package; neither upstream ships a Django Trac #37064 patch.

#### Note

- two-half defense for Trac #37064: a package-level unwrap patch (auto-applied at app-load) plus the cooperative `safe_wrap_connection_method` helper + tests.

<a id="multi_database_cooperation_contract"></a>
### [DONE-023-0.0.7 - Multi-database cooperation contract](KANBAN.html#multi_database_cooperation_contract)

- Priority: Low
- Parity: 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
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

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py` builds N+1-avoidance plans out of `django.db.models.Prefetch` objects (imported at line 18; `prefetch_related: list[PrefetchType]`) but specifies no multi-database cooperation contract (a grep of the module for `.using(`, `_db`, `router`, `db_for_read` returns nothing). This card pins that exact seam for the framework's `Prefetch`-based optimizer — `OptimizerHint.prefetch(Prefetch(queryset=...using('shard_b')))` round-tripping with `_db` intact through plan construction (`tests/optimizer/test_multi_db.py`) — so it is adjacent: it underpins/extends the same prefetch-plan subsystem strawberry-graphql-django owns, adding a multi-DB guarantee the upstream leaves unspecified.
- graphene-django has no comparable prefetch-plan optimizer and likewise no multi-DB handling (grep of `graphene_django/*.py` for `.using(`/`_db`/`router`/`db_for_read` returns nothing), so no graphene_django claim is honest here; the contract this card pins (`.using()` preservation, router-aware FK-id stubs, `Prefetch._db` round-trip) is purely a function of the framework's optimizer, which is the strawberry-graphql-django-comparable subsystem.
- multi-DB is a Django capability neither upstream specifies a contract around (⚛️&🍓 parity-adjacent); pinning ours smooths the migrant story.

#### Note

- pin the multi-DB cooperation contract (router-aware FK-id stubs, `.using()` preservation, `Prefetch` `_db` round-trip) + tests; zero production-code change.

<a id="schema_export_management_command"></a>
### [DONE-022-0.0.7 - Schema export management command](KANBAN.html#schema_export_management_command)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
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
| [`DjangoGraphQLProtocolRouter`](docs/GLOSSARY.md#djangographqlprotocolrouter) | shipped (`0.0.14`) |
| [Debug-toolbar middleware](docs/GLOSSARY.md#debug-toolbar-middleware) | shipped (`0.0.14`) |
| [Response-extensions debug middleware](docs/GLOSSARY.md#response-extensions-debug-middleware) | shipped (`0.0.14`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) | shipped (`0.0.14`) |

#### Package files

- [`django_strawberry_framework/management/__init__.py`](django_strawberry_framework/management/__init__.py)
- [`django_strawberry_framework/management/commands/__init__.py`](django_strawberry_framework/management/commands/__init__.py)
- [`django_strawberry_framework/management/commands/export_schema.py`](django_strawberry_framework/management/commands/export_schema.py)
- [`django_strawberry_framework/scalars.py`](django_strawberry_framework/scalars.py)

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/management/commands/export_schema.py::Command` is the `manage.py export_schema` command: positional `schema` arg, optional `--path`, `import_module_symbol` resolution, `isinstance(..., strawberry.Schema)` guard, SDL via `print_schema`, and `CommandError` paths. This card ships the same-named command with the identical positional `schema` / `--path` / `print_schema` / `CommandError` contract, a direct feature match justifying the strawberry_django required claim.
- graphene-django's nearest analog `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/management/commands/graphql_schema.py::Command` is a deliberately different `graphql_schema` command (`--schema`/`--out`/`--indent`/`--watch`, JSON-or-`.graphql` output via `schema.introspect()`), which the card explicitly flags as parity-adjacent and not borrowed; correctly excluded from the claim set.
- strawberry-graphql-django ships `manage.py export_schema`; graphene-django's different `graphql_schema` command is parity-adjacent (deliberately not borrowed).

#### Note

- one management command (positional `schema`, `--path`, SDL via `print_schema`, `CommandError` paths) + tests.

<a id="appspy_and_django_app_config"></a>
### [DONE-021-0.0.7 - `apps.py` and Django app config](KANBAN.html#appspy_and_django_app_config)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
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
| [`DjangoGraphQLProtocolRouter`](docs/GLOSSARY.md#djangographqlprotocolrouter) | shipped (`0.0.14`) |
| [Debug-toolbar middleware](docs/GLOSSARY.md#debug-toolbar-middleware) | shipped (`0.0.14`) |
| [Response-extensions debug middleware](docs/GLOSSARY.md#response-extensions-debug-middleware) | shipped (`0.0.14`) |
| [`TestClient`](docs/GLOSSARY.md#testclient) | shipped (`0.0.14`) |
| [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) | shipped (`0.0.14`) |
| [Upstream patches](docs/GLOSSARY.md#upstream-patches) | shipped |

#### Package files

- [`django_strawberry_framework/apps.py`](django_strawberry_framework/apps.py)

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/apps.py::StrawberryDjangoConfig` is a minimal `AppConfig` (just `name` and `verbose_name`) enabling `INSTALLED_APPS`-driven discovery; this card ships the equivalent `DjangoStrawberryFrameworkConfig` `AppConfig`, a direct feature match that justifies the strawberry_django required claim.
- both upstreams ship an `apps.py` `AppConfig` for `INSTALLED_APPS`-driven discovery.

#### Note

- tiny `AppConfig` (two class attributes, no `ready()` body in this card's own diff) + tests; the `ready()` body that ships in `0.0.7` arrived with sibling card `DONE-024-0.0.7`, dispatching the single Django patch applier, and the Strawberry and `cross_web` appliers followed at `0.0.11`.

<a id="djangolistfield_non_relay_list"></a>
### [DONE-020-0.0.7 - `DjangoListField` (non-Relay list)](KANBAN.html#djangolistfield_non_relay_list)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Status: Done
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

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/fields.py::DjangoListField` is graphene-django's non-Relay list primitive: it wraps the underlying type in `List(NonNull(...))`, exposes `get_manager()`/`get_queryset` cooperation, and coerces `Manager`/`QuerySet` results in `list_resolver`. This card ships the same-named `DjangoListField` factory (`Manager → QuerySet` coercion, sync/async `get_queryset`, outer-list nullability) for the Strawberry stack; required because it is a direct feature match against a primitive strawberry-graphql-django does not provide.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py::field_type_map` maps only relation kinds (`ManyToManyField`, `ManyToOneRel`) to `list[DjangoModelType]` and offers no standalone consumer-facing list field; this confirms the card's premise that strawberry-graphql-django has no non-Relay list-field primitive, so the single `graphene_django` required claim is the honest sole match.
- graphene-django ships `DjangoListField`; strawberry-graphql-django has no non-Relay list-field primitive.

#### Note

- `DjangoListField` factory: default + consumer resolver, `Manager → QuerySet` coercion, sync/async `get_queryset`, outer-list nullability, root-gated optimizer cooperation.

<a id="consumer_override_semantics_scalar_fields"></a>
### [DONE-019-0.0.6 - Consumer override semantics (scalar fields)](KANBAN.html#consumer_override_semantics_scalar_fields)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
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

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::_process_type` only injects `strawberry.auto` for model fields lacking a consumer annotation (`for f in model_fields: if existing_annotations.get(f.name): continue`), so a consumer-authored scalar annotation is authoritative and is never overwritten by the synthesized field — exactly this card's consumer-annotation-overrides-synthesized contract — making the claim `required`; the adjacent `MAP_AUTO_ID_AS_GLOBAL_ID` guard that drops `id` from `model_fields` to avoid clobbering the relay `GlobalID` also mirrors this card's `relay.Node` `id`-collision handling.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py::DjangoObjectType.__init_subclass_with_meta__` yanks consumer-declared class-attribute fields via `yank_fields_from_attrs` alongside the auto-`construct_fields` model conversion, so a field a consumer declares on the type takes precedence over the auto-generated scalar — graphene_django supports the same consumer-authored scalar-override-on-a-model-type feature, so the claim is `required`.
- both upstreams support consumer-authored scalar field overrides on model-backed types.

#### Test plan

- End-to-end test pinned the override surviving `strawberry.type(...)`
- 100% coverage was reached across `tests/types/test_definition_order.py`

#### Decision

- **`relay.Node` `id` collision rejected at type-creation time.** A consumer

#### Note

- annotation/assigned scalar-override contract (four-corner matrix), `relay.Node` `id`-collision rejection, cross-type choice-enum cache semantics.
- `DjangoType.__init_subclass__` collected `consumer_annotated_scalar_fields`
- `DjangoTypeDefinition` gained `consumer_annotated_scalar_fields: frozenset[str]`.
- The previously-skipped `test_consumer_annotation_overrides_synthesized`
- **Consumer annotation overrides are authoritative.** `_build_annotations`'s
- No new public API. No `Meta.field_overrides = {...}`-style key. Opt-out
- The four `consumer_*_fields` sets on `DjangoTypeDefinition`
- Resolver / metadata overrides for scalars stay on the assigned
- Type-annotation overrides are the consumer's responsibility for runtime

<a id="multiple_djangotypes_per_model_with_metaprimary"></a>
### [DONE-018-0.0.6 - Multiple DjangoTypes per model with `Meta.primary`](KANBAN.html#multiple_djangotypes_per_model_with_metaprimary)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
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

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::_process_type` gives every Django type its own `is_type_of` closure returning `isinstance(obj, (cls, model))` (with a `get_strawberry_type_cast` short-circuit) and keeps no model-to-type registry at all, so multiple types can back the same model and disambiguation rides on `is_type_of`/`strawberry.cast` rather than an explicit primary flag; this card's registry storing many types per model with an explicit `Meta.primary` selection plus a finalize-time ambiguity audit extends and formalizes that implicit upstream behavior, making the link `adjacent`. graphene_django has no equivalent — `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/registry.py::Registry.register` stores exactly one type per model (`self._registry[cls._meta.model] = cls`), so no claim is made there.
- 🍓 parity-adjacent (strawberry-graphql-django has an implicit primary-type concept via `is_type_of`; graphene-django ships no equivalent) — not required on either side.

#### Test plan

- 100% coverage across `tests/test_registry.py`, `tests/types/test_base.py`,

#### Decision

- Two primary types for the same model: rejected at registration time

#### Note

- registry stores multiple types per model, `Meta.primary` flag, ambiguity audit at finalize, relation-deferral, optimizer origin-type threading.
- Registry stores multiple types per model (`_types: dict[Model, list[Type]]`).
- New `Meta.primary: bool` flag (default `False`); validated in `_validate_meta`.
- `registry.register(..., *, primary: bool = False) -> bool` and
- New registry surface: `primary_for(model)`, `types_for(model)`,
- `registry.get(model)` returns the primary if declared, else the single
- `finalize_django_types()` runs `audit_primary_ambiguity()` first: any
- Relation conversion in `types/base.py` defers all **auto-synthesized**
- Optimizer planning threads the resolved origin Strawberry type from
- Schema audit (`optimizer/extension.py`) iterates every reachable
- `model_for_type` continues to work for any registered type so
- `DjangoTypeDefinition` gains `primary: bool = False`.
- Single-type-no-primary stays backward compatible: `registry.get(model)`
- `Meta.primary` is a per-class declaration, not a registry-level
- Already-shipped consumer relation overrides (direct annotation

<a id="deferred_scalar_conversions"></a>
### [DONE-017-0.0.6 - Deferred scalar conversions](KANBAN.html#deferred_scalar_conversions)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
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

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py::convert_big_int_field` maps `models.BigIntegerField` to graphene's `BigInt` scalar (defined at `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene/types/scalars.py::BigInt`), and the same module maps `models.JSONField`/`HStoreField` to `JSONString` and `ArrayField` to `List` — graphene_django ships a direct `BigIntegerField -> BigInt`-scalar conversion plus JSON/Array/HStore handlers matching this card, so the claim is `required`.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py::field_type_map` maps `json.JSONField` to `strawberry.scalars.JSON` and resolves `ArrayField` to a nested `list[...]` via `_resolve_array_field_type`, giving strawberry_django direct equivalents for this card's `JSONField -> strawberry.scalars.JSON` and `ArrayField` conversions; the same map routes `BigIntegerField`/`PositiveBigIntegerField` to plain `int` (no dedicated big-int scalar), so the JSON/Array conversion parity is the `required` anchor on this side.
- both upstreams ship scalar conversion for `BigIntegerField` / `JSONField` / `HStoreField` / `ArrayField`, etc.

#### Test plan

- 100% coverage via `tests/test_scalars.py` (new flat file) and `tests/types/test_converters.py` (extended). Includes a `test_package_import_does_not_emit_strawberry_deprecation_warning` guard so future regressions to the suppression are explicit.

#### Note

- `BigInt` scalar + strict parser/serializer, `JSONField` / `ArrayField` / `HStoreField` conversion, `SCALAR_MAP` value-type widening.
- Public `BigInt` scalar (`django_strawberry_framework/scalars.py`, `NewType`-based) with the Strawberry class-direct-to-`scalar()` `DeprecationWarning` suppressed at the definition site so consumers see no warning at import time.
- Strict `BigInt` parser via regex `^(0|-?[1-9][0-9]*)$` — rejects `bool`, `float`, empty / whitespace-padded strings, non-decimal strings, underscores, plus signs, leading zeroes, `-0`, and Unicode digits.
- Strict `BigInt` serializer — rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`.
- `BigIntegerField → BigInt` and `PositiveBigIntegerField → BigInt` in `SCALAR_MAP`. `BigAutoField` preserved as `int` (no override recourse at the time; annotation-override recourse now available via `DONE-019-0.0.6`).
- `JSONField → strawberry.scalars.JSON` in `SCALAR_MAP`.
- `ArrayField` and `HStoreField` mapped via sentinel-guarded branches in `convert_scalar`. `HStoreField` not added to `SCALAR_MAP`.
- `ArrayField` rejects nested arrays and outer `choices` with `ConfigurationError`.
- `SCALAR_MAP`'s declared value type widened from `dict[type[models.Field], type]` to `dict[type[models.Field], Any]`.
- `BigInt` added to `django_strawberry_framework.__all__`; `tests/base/test_init.py`'s pinned `__all__` and `__version__` assertions updated.
- Atomic version-bump quintet: `pyproject.toml`, `__init__.py`, `tests/base/test_init.py`, `docs/GLOSSARY.md` package-version line, `uv.lock`.
- Docs: `docs/GLOSSARY.md`, `docs/README.md`, `README.md`, `docs/TREE.md`, `TODAY.md`, `CHANGELOG.md`.
- The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` is suppressed at the definition site (tight `warnings.catch_warnings()` filter). The package import surface is therefore clean. Migration to a `StrawberryConfig.scalar_map`-based design is roadmapped as `DONE-025-0.0.7` — that path is a real public-API change (consumers using `BigInt` directly will merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`), not an internal-only refactor.

#### Card references

- Related: `BigAutoField` preserved as `int` before scalar override recourse shipped in `DONE-019-0.0.6`. -> `DONE-019-0.0.6` - Consumer override semantics (scalar fields)
- Related: The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` is suppressed at the definition site (tight `warnings.catch_warnings()` filter). The package import surface is therefore clean. Migration to a `StrawberryConfig.scalar_map`-based design is roadmapped as `DONE-025-0.0.7` — that path is a real public-API change (consumers using `BigInt` directly will merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`), not an internal-only refactor. -> `DONE-025-0.0.7` - Warning-free scalar registration via `StrawberryConfig.scalar_map`

<a id="fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement"></a>
### [DONE-016-0.0.6 - `FieldMeta` single-source-of-truth consolidation and mirror retirement](KANBAN.html#fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
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
- internal metadata-architecture refactor; no consumer-visible API change.
- Internal refactor only; no `Meta` key changes, no public surface changes, no consumer-visible behavior changes. Existing tests pass without modification.

#### Files likely touched

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/extension.py`

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py::_get_model_hints` sources per-type optimization metadata from a single canonical place — `getattr(get_django_definition(object_definition.origin), 'store', None)` (and per-field `getattr(field, 'store', None)`), where `get_django_definition` (`/Users/riordenweber/projects/strawberry-django-main/strawberry_django/utils/typing.py::get_django_definition`) returns the one `__strawberry_django_definition__` on the type rather than any parallel copy; this card's retirement of the legacy class-attribute mirrors so the optimizer reads `FieldMeta` only from `DjangoTypeDefinition.field_map` via `registry.get_definition(...)` aligns the framework's metadata-sourcing posture with strawberry_django's single-definition design, but it is an internal SSoT refactor with no consumer-visible surface, so the link is `adjacent`, not `required`.

#### Why it matters

- Three reader sites were re-deriving relation shape via `relation_kind(field)` + raw `getattr(field, ...)` instead of reading the `FieldMeta` already on `DjangoTypeDefinition.field_map` — duplicating logic and creating drift surface for any future relation-flag addition.
- `DjangoType.__init_subclass__` was writing legacy class-attribute mirrors (`cls._optimizer_field_map`, `cls._optimizer_hints`) that survived `registry.clear()`, then four optimizer sites read those mirrors instead of the canonical `DjangoTypeDefinition`. Two parallel sources of field metadata with no enforced consistency.

#### Note

- consolidate field metadata onto `DjangoTypeDefinition` (single source of truth) and retire legacy class-attribute mirrors across ~7 reader sites.
- Commit `de35a62` (`refactor(types,optimizer): consolidate metadata onto DjangoTypeDefinition`).
- `CHANGELOG.md` (under `[Unreleased] → Changed`)
- Originally tracked as `BACKLOG.md` item 35 ("`FieldMeta` single-source-of-truth consolidation and mirror retirement"). Promoted to a DONE card and removed from `BACKLOG.md` when the work shipped — per `BACKLOG.md`'s "graduate into a `KANBAN.md` card when scheduled" workflow. This is the first `BACKLOG.md` item to graduate; the precedent for shipped items: strike-through with SHIPPED status is fine while the item awaits a release; once a release is imminent, move the item to a `KANBAN.md` `DONE` card and delete it from `BACKLOG.md` so the strategic-differentiation file doesn't keep pointing at completed architecture debt.
- The consolidation eliminates ~7 sites of duplicated relation-shape logic and removes legacy class-attribute residue that previously survived `registry.clear()`. Single source of truth for field metadata reduces drift surface whenever Django adds a new relation flag or changes a descriptor attribute.

<a id="005_relay_interfaces_and_node_foundation"></a>
### [DONE-015-0.0.5 - 0.0.5 Relay interfaces and Node foundation](KANBAN.html#005_relay_interfaces_and_node_foundation)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
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

#### Scope

- `Meta.interfaces` accepted end-to-end for any Strawberry interface.
- Four Relay node resolver defaults injected when `relay.Node` is declared (canonical order: `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes`); consumer-declared overrides are preserved via Strawberry's `__func__` identity test.
- Automatic synthesized `id: int!` suppression when `relay.Node` is in `Meta.interfaces`; the Relay-supplied `id: GlobalID!` is used instead.
- `is_type_of` injection is unconditional for every `DjangoType` (Relay-declared or not); consumer-declared `is_type_of` is preserved.
- Models whose primary key is a Django 5.2+ `CompositePrimaryKey` raise `ConfigurationError` at finalization; declare an explicit `id: relay.NodeID[...]` annotation or remove `relay.Node` from `Meta.interfaces` to remediate.
- Both sync and async paths for `_resolve_node_default` / `_resolve_nodes_default`; async `get_queryset` hooks are awaited on the async branch and rejected with `ConfigurationError` on the sync branch.
- `Meta.interfaces` promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`.
- Package version bumped to `0.0.5` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock`.

#### Foundation-slice seam

- `Meta.interfaces` is the first `0.0.4`-reserved `DjangoTypeDefinition` slot that ships end-to-end through finalizer phase 2.5; subsequent Layer 3 subsystems plug into the same architectural seam.

#### Files likely touched

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/relay.py`
- `django_strawberry_framework/types/finalizer.py`
- `tests/types/test_relay_interfaces.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_relay_id_projection.py`
- `tests/test_registry.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `CHANGELOG.md`
- `docs/GLOSSARY.md`
- `docs/README.md`
- `TODAY.md`
- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::_process_type` injects the four relay defaults (`resolve_id`, `resolve_id_attr`, `resolve_node`, `resolve_nodes`) when `issubclass(cls, relay.Node)` and preserves a consumer-declared resolver via the `existing_resolver.__func__ is getattr(relay.Node, attr).__func__` identity test, and unconditionally installs `is_type_of` unless already in `cls.__dict__` — strawberry_django ships exactly this Node-wiring contract, so the card's `relay.Node`-default injection plus `__func__`-preserving override and unconditional `is_type_of` is `required` against it.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py::DjangoObjectType` accepts a `Meta.interfaces` tuple, auto-enables a Relay `Connection` when any interface `issubclass(interface, Node)`, and provides `get_node`/`get_queryset`/`resolve_id`/`is_type_of` for Node-backed model types (with the global `id` resolved as a `GlobalID` via `graphene.relay.node.AbstractNode`) — graphene_django offers the same end-to-end `Meta.interfaces`-with-Node feature this card matches, so the claim is `required`.
- both upstreams ship Relay Node interfaces; this shipped our 🍓-shaped Relay Node integration.

#### Architectural posture

- Borrowed patterns from `strawberry-django` (spec "Borrowing posture", Decision 3). The override discriminator triad stays distinct across the three injection sites: `__dict__` membership for `is_type_of`, tuple membership for id suppression, `__func__` identity for the four `resolve_*` defaults.

#### Note

- Relay Node foundation: `Meta.interfaces`, four `resolve_*` defaults, `id: GlobalID!` suppression, `is_type_of` injection, composite-PK rejection, sync + async node resolution.
- `examples/fakeshop/apps/library/schema.py` (`GenreType` declares `Meta.interfaces = (relay.Node,)`)

<a id="move_test_fixture_out_of_example_settings"></a>
### [DONE-014-0.0.4 - Move test fixture out of example settings](KANBAN.html#move_test_fixture_out_of_example_settings)

- Priority: Low
- Status: Done
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

#### Scope

- Removed `tests.fixtures.apps.TestsCardinalityConfig` from the example project.
- Removed the old unmanaged cardinality fixture files under `tests/fixtures/`.
- Package tests that need OneToOne / M2M / cardinality coverage now use real models from `examples/fakeshop/apps/library/`.

#### Files likely touched

- `examples/fakeshop/config/settings.py`
- `examples/fakeshop/apps/library/models.py`
- `docs/SPECS/spec-014-testing_shift-0_0_4.md`
- `AGENTS.md`
- `docs/TREE.md`

#### Why it matters

- test hygiene.

<a id="real_m2m_coverage"></a>
### [DONE-013-0.0.4 - Real M2M coverage](KANBAN.html#real_m2m_coverage)

- Priority: Medium
- Status: Done
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

#### Scope

- Replaced test-only M2M/cardinality fixtures with real managed models in the `library` example app.
- Added package-level and HTTP-level coverage for M2M traversal and optimizer planning.

#### Files likely touched

- `examples/fakeshop/apps/library/models.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `tests/types/test_definition_order.py`
- `tests/optimizer/test_definition_order.py`

#### Why it matters

- test hygiene.

<a id="004_version_and_release_alignment"></a>
### [DONE-012-0.0.4 - 0.0.4 version and release alignment](KANBAN.html#004_version_and_release_alignment)

- Priority: Low
- Status: Done
- Relative size: XS
- Labels: `internal`, `release`, `versioning`
- Spec: [spec-012-version_release_alignment-0_0_4.md](docs/SPECS/spec-012-version_release_alignment-0_0_4.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`) |

#### Scope

- Package metadata, runtime version, lockfile, tests, and changelog now agree on `0.0.4`.
- The changelog entry is condensed for the alpha release and covers the actual commit range through 2026-05-08.

#### Files likely touched

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`

#### Note

- release housekeeping (version alignment).
- align package metadata / runtime version / lockfile / tests / changelog on `0.0.4`.

<a id="stale_placeholder_cleanup"></a>
### [DONE-011-0.0.4 - Stale placeholder cleanup](KANBAN.html#stale_placeholder_cleanup)

- Priority: Low
- Status: Done
- Relative size: XS
- Labels: `cleanup`, `docs`, `internal`, `tests`
- Spec: [spec-011-stale_placeholder_cleanup-0_0_4.md](docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) | shipped (`0.0.4`) |
| [Scalar field override semantics](docs/GLOSSARY.md#scalar-field-override-semantics) | shipped (`0.0.6`) |

#### Scope

- Replaced stale M2M and forward-reference skips with definition-order tests.
- Scalar field override semantics is a separate concern from definition order and is owned by `DONE-019-0.0.6`, which ships it at `0.0.6`.

#### Files likely touched

- `tests/types/test_definition_order.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_definition_order.py`

#### Why it matters

- internal test/doc cleanup.

#### Note

- `DONE-019-0.0.6`

#### Card references

- Related: Scalar field override semantics is a separate concern from definition order and ships at `0.0.6`. -> `DONE-019-0.0.6` - Consumer override semantics (scalar fields)

<a id="004_foundation_slice_definition_order_independence"></a>
### [DONE-010-0.0.4 - 0.0.4 foundation slice (definition-order independence)](KANBAN.html#004_foundation_slice_definition_order_independence)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
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

#### Foundation-slice seam

- The forward-reserved slots on `DjangoTypeDefinition` are the architectural seam where the cookbook-shaped Layer 3 subsystems plug in (each subsystem moves its `Meta` key out of `DEFERRED_META_KEYS`, populates the matching slot in collection, and consumes it during finalization or in `DjangoConnectionField`).
- The pending-resolution pattern (record at class creation, resolve at finalization, fail loud on missing target with named source model / field / target) generalizes directly to lazy related class references for `RelatedFilter`, `RelatedOrder`, and `RelatedAggregate`.

#### Files likely touched

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

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py::convert_onetoone_field_to_djangomodel` (and the sibling FK / M2M converters) wrap related-type resolution in `graphene.Dynamic(dynamic_type)` callables that look up `registry.get_type_for_model(model)` only when the schema is built, giving graphene definition-order independence for relations; this slice ships the equivalent capability through `finalize_django_types()`'s three-phase finalizer that resolves a `PendingRelation` registry against registered `DjangoType`s before `strawberry.type(cls)` runs, so the claim is adjacent because it matches the observable behavior via an explicit collected-types finalize gate rather than graphene's per-field deferred callables.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::_process_type` achieves cross-type relation resolution by forcing relation annotations to `strawberry.auto` and clearing `StrawberryAnnotation.__resolve_cache__` so Strawberry re-evaluates forward references after all types are decorated, with no first-class pending-relation registry; this card's `PendingRelation` / `add_pending_relation` / `finalize_django_types()` foundation delivers the same definition-order-independent relation resolution but as an explicit registry-plus-finalizer mechanism with a `PendingRelationAnnotation` sentinel that errors if `strawberry.Schema(...)` is built early, so the claim is adjacent because the framework underpins and diverges from strawberry_django's implicit lazy-annotation approach rather than matching its public API at parity.

#### Note

- internal Layer-2 foundation (`DjangoTypeDefinition`, finalizer, pending-relation resolution) — enables the parity subsystems rather than being one itself.
- definition-order-independent finalizer, pending-relation registry, manual-override contract, real cardinality coverage — the seam every Layer-3 subsystem plugs into.
- The previous foundation-slice in-progress cards have been retired; this card is their successor in Done.

<a id="rich_schema_architecture"></a>
### [DONE-009-0.0.4 - Rich schema architecture](KANBAN.html#rich_schema_architecture)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
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

#### Scope

- Lay out the long-term architecture for filters, orders, aggregates, connections, permissions, and fieldsets.
- Compare Graphene, django-graphene-filters, and strawberry-graphql-django patterns against this package's DRF-shaped API.
- Define how the 0.0.4 foundation slice becomes the base for later Layer 3 subsystems.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::type` is the public `@strawberry_django.type(model)` entrypoint that generates a Strawberry type from a Django model and (via `_process_type`) wires relations, filters, ordering, and pagination as decorator kwargs; this card lays out the package's long-term Layer-3 architecture (filters, orders, aggregates, connections, permissions, fieldsets) over a DRF-shaped API and explicitly compares strawberry_django patterns, so it is adjacent because the planned architecture extends and reshapes that upstream surface rather than matching one of its features at parity.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py::convert_field_to_list_or_connection` shows graphene's relation-to-connection/list dispatch keyed off `_type._meta.connection` / `filter_fields` / `filterset_class` on the related `DjangoObjectType`; this card's scope explicitly contrasts Graphene/django-graphene-filters patterns when defining how the foundation slice becomes the base for later connection/filter subsystems, so the claim is adjacent because the package's DRF-shaped layered architecture differs from graphene's Meta-flag dispatch rather than reaching parity with a single graphene feature.

#### Note

- Architecture design record paired with the narrower 0.0.4 foundation implementation spec.

<a id="definition_order_independence_design"></a>
### [DONE-008-0.0.4 - Definition-order independence design](KANBAN.html#definition_order_independence_design)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
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

#### Scope

- Frame the class-definition-time relation-resolution problem.
- Compare options for preserving concrete related `DjangoType`s without import-order coupling.
- Set the failure-mode requirements that the 0.0.4 foundation slice implements.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py::convert_field_to_djangomodel` converts every Django relation field into a `graphene.Dynamic(dynamic_type)` whose `dynamic_type` defers `registry.get_type_for_model(model)` to schema-build time (`graphene/types/dynamic.py::Dynamic.get_type`), so a related `DjangoObjectType` need not exist when the owning type is defined; this card frames the same class-definition-time relation-resolution problem but proposes an explicit pending-relation/finalizer design rather than per-field lazy callables, so the claim is adjacent (it underpins and differs from graphene's surface, not a parity match of a public feature).
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::_process_type` resolves relation annotations per class at decoration time by resetting `StrawberryAnnotation.__resolve_cache__` and forcing relation fields back to `strawberry.auto` so Strawberry re-evaluates forward references later, with no global collected-types finalize gate; this card compares that import-order-coupling-avoidance approach against the package's planned design, so it is adjacent because the framework's proposed deferred-finalize architecture extends and differs from strawberry_django's lazy-annotation mechanism rather than matching it at parity.

#### Note

- Problem-space design record for definition-order independence.

<a id="004_onboarding_docs_and_spec_consolidation"></a>
### [DONE-007-0.0.4 - 0.0.4 onboarding docs and spec consolidation](KANBAN.html#004_onboarding_docs_and_spec_consolidation)

- Priority: Medium
- Status: Done
- Relative size: S
- Labels: `docs`, `internal`, `release`
- Spec: [spec-007-onboarding_docs_spec_consolidation-0_0_4.md](docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md)

#### Glossary terms

| Term | Status |
| --- | --- |
| [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) | shipped (`0.0.2`) |

#### Scope

- Root `README.md` is the canonical documentation map and operational entry point.
- `docs/README.md` is code-first: quickstart, three-minute path, optimizer behavior, and status.
- `docs/GLOSSARY.md` is the capability catalog with value-led optimizer language and comparison table.
- `docs/TREE.md` is the detailed layout/test-tree reference.
- `CHANGELOG.md` is condensed and no longer relies on design-doc pointers for release context.
- Completed design-doc content is folded into durable docs, while remaining specs preserve design history and follow-up work.

#### Files likely touched

- `README.md`
- `docs/README.md`
- `docs/GLOSSARY.md`
- `docs/TREE.md`
- `CHANGELOG.md`

#### Why it matters

- internal docs cleanup / spec consolidation — no upstream-parity surface.

#### Note

- onboarding-doc consolidation across README / docs / CHANGELOG; completed spec content folded into durable docs.
- Future in-flight design docs use the `docs/spec-<NNN>-<topic>-<0_0_X>.md` convention (NNN matches the KANBAN card number; see `docs/builder/BUILD.md` "Spec filename pattern"), then get folded into durable docs when shipped.

<a id="documentationstatus_positioning_for_shipped_layer_2"></a>
### [DONE-006-0.0.3 - Documentation/status positioning for shipped Layer 2](KANBAN.html#documentationstatus_positioning_for_shipped_layer_2)

- Priority: Medium
- Status: Done
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

#### Scope

- `docs/README.md` gives a quickstart, package positioning, optimizer value, and status.
- `docs/GLOSSARY.md` describes shipped, planned, deferred, and alpha-constrained capabilities.
- `docs/TREE.md` preserves detailed package/test tree responsibilities.

#### Files likely touched

- `docs/README.md`
- `docs/GLOSSARY.md`
- `docs/TREE.md`

#### Why it matters

- internal docs / status-positioning card — no upstream-parity surface.

#### Note

- docs pass: `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md` quickstart + status positioning.
- User-facing docs avoid internal slice shorthand; maintainer docs can still use it where useful.

<a id="djangotype_contract_and_boundary"></a>
### [DONE-005-0.0.3 - DjangoType contract and boundary](KANBAN.html#djangotype_contract_and_boundary)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent)
- Status: Done
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

#### Scope

- Document the alpha one-model-one-type registry constraint.
- Reject unsupported or deferred `Meta` keys instead of accepting unwired surface area.
- Remove consumer override promises that the implementation cannot honor yet.

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/registry.py::Registry.register` stores one type per model (`self._registry[cls._meta.model] = cls`, last-write-wins, with the multiple-types assertion left commented out) and `types.py::validate_fields` only `warnings.warn`s when `Meta.fields`/`exclude` name unknown fields -- this card tightens both: it documents the same one-model-one-type registry constraint as a hard alpha boundary and raises (rather than warns) on unsupported/deferred `Meta` keys, so it is adjacent to graphene's looser model-to-type registry and field-validation surface, narrowing rather than matching it.

#### Note

- Contract companion to the 0.0.3 public-surface documentation pass.

<a id="optimizer_beyond_slices_b1_b8"></a>
### [DONE-004-0.0.3 - Optimizer beyond slices B1-B8](KANBAN.html#optimizer_beyond_slices_b1_b8)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
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

#### Scope

- B1: plan cache keyed by selected operation AST, directive variables, model, root runtime path, and the resolver's origin Strawberry type
- B2: forward-FK-id elision
- B3: strictness mode (`off`, `warn`, `raise`)
- B4: `Meta.optimizer_hints` with `OptimizerHint`
- B5: plan introspection via context
- B6: schema-build-time audit
- B7: precomputed optimizer field metadata
- B8: queryset diffing against consumer-applied `select_related`, `prefetch_related`, and `Prefetch`

#### Files likely touched

- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/hints.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/plans.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_hints.py`
- `tests/optimizer/test_field_meta.py`
- `tests/optimizer/test_plans.py`

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py::optimize` is strawberry-django's optimization entry point: it short-circuits when `is_optimized(qs)` (a per-queryset already-optimized flag set via `get_queryset_config(qs).optimized`) and otherwise applies the accumulated `OptimizerStore` to the queryset -- the same production-grade extension surface this card extends, where B1's AST-keyed plan cache and B8's `diff_plan_for_queryset` per-path reconciliation against consumer `select_related`/`prefetch_related`/`Prefetch` go beyond strawberry-django's single boolean guard, so the existing required claim covers the shared apply-optimizations-once core that these beyond-slices features build on.

#### Note

- continuation of DONE-002-0.0.2's optimizer lineage (⚛️ parity-adjacent).
- eight optimizer sub-features B1–B8: AST plan cache, FK-id elision, strictness modes, `OptimizerHint`, context plan introspection, schema audit, precomputed field metadata, queryset diffing.
- B8 went beyond the initial simple exact-match diff and now handles subtree-aware prefetch reconciliation.
- Fragment-spread directive and multi-operation cache-key bugs have been fixed in source; the alpha-review entries that recorded them (the B1 plan-cache key in `spec-004-optimizer_beyond-0_0_3`) are now historical.

#### Card references

- Related: continuation of DONE-002-0.0.2's optimizer lineage (⚛️ parity-adjacent). -> `DONE-002-0.0.2` - Optimizer O1-O6 foundation

<a id="optimizer_o4_nested_prefetch_chains"></a>
### [DONE-003-0.0.2 - Optimizer O4 nested prefetch chains](KANBAN.html#optimizer_o4_nested_prefetch_chains)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
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

#### Scope

- Plan depth > 1 relation selections from the root optimizer pass.
- Emit nested `Prefetch` objects for many-side branches that need shaped child querysets.
- Recurse through single-valued relation chains with `select_related` and `only()` fields intact.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py::_get_hints_from_django_relation` builds a depth>1 nested plan by recursing through `_get_model_hints(..., level=level + 1)`, rebasing the child `OptimizerStore`'s `only`/`select_related` under the relation path, and emitting `Prefetch(path, queryset=field_qs)` for many-side branches -- the identical behavior this card ships in `optimizer/walker.py` (`_build_prefetch_child_queryset` recurses one level deeper and `_plan_prefetch_relation` emits `Prefetch(lookup_path, queryset=child_queryset)`, while `_plan_select_relation` recurses through single-valued chains preserving `select_related` + `only()`), so O4 nested-prefetch-chain planning is required parity with strawberry-django's nested relation hinting.

#### Note

- Design record for the O4 slice split out from the broader optimizer foundation.

<a id="optimizer_o1_o6_foundation"></a>
### [DONE-002-0.0.2 - Optimizer O1-O6 foundation](KANBAN.html#optimizer_o1_o6_foundation)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
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

#### Scope

- generated relation resolvers
- selection-tree walker
- root-gated optimizer extension
- nested `Prefetch` chains
- same-query `select_related` recursion
- `only()` projection
- custom `get_queryset` downgrade to `Prefetch`

#### Files likely touched

- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/plans.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_walker.py`
- `tests/optimizer/test_plans.py`

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py::DjangoOptimizerExtension` is strawberry-django's N+1 solver: a `SchemaExtension` whose `resolve` walks the selection tree, builds an `OptimizerStore` (lists of `only`/`select_related`/`prefetch_related`), and applies it to the root queryset, with `_get_prefetch_queryset` running the target type's `get_queryset` inside generated `Prefetch` objects -- the same root-gated extension, selection-tree walker, `select_related`/`only()` projection, nested `Prefetch` chains, and custom-`get_queryset`-downgrade-to-`Prefetch` behavior this card's O1-O6 foundation ships, so it is required parity with strawberry-django's optimizer extension.
- strawberry-graphql-django ships a heavy optimizer extension; graphene-django has only `select_related_field` (⚛️ parity-adjacent).

#### Note

- heavy optimizer extension: relation resolvers, selection-tree walker, root-gated planning, nested `Prefetch` chains, `only()` projection, `get_queryset` downgrade.
- Shipped behavior is consolidated into `docs/GLOSSARY.md`; source/tests are the truth for optimizer behavior.

<a id="djangotype_core_foundation"></a>
### [DONE-001-0.0.1 - DjangoType core foundation](KANBAN.html#djangotype_core_foundation)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
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

#### Scope

- `DjangoType` base class
- Meta validation
- scalar conversion
- relation conversion
- choice enums
- type registry
- relation resolvers
- `get_queryset` hook and `has_custom_get_queryset`

#### Files likely touched

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `tests/types/test_base.py`
- `tests/types/test_converters.py`
- `tests/types/test_resolvers.py`

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py::DjangoObjectType` is graphene's model-backed type: a nested `Meta` declares `model`/`fields`/`exclude`, `construct_fields` selects model fields, `convert_choice_field_to_enum` (`converter.py`) turns Django `choices` into GraphQL enums, `Registry.register` (`registry.py`) maps model to type, and a classmethod `get_queryset(queryset, info)` scopes visibility -- the exact surface `DjangoType` ships (base class, Meta validation, scalar/relation conversion, choice enums, registry, `get_queryset` hook), so this is required parity with graphene's canonical type-generation feature.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py::_process_type` is strawberry-django's adapter behind `@strawberry_django.type`: it reads `model`/`fields`/`exclude`, marks model fields `strawberry.auto`, and records a `StrawberryDjangoDefinition` in the registry, while `queryset.py::run_type_get_queryset` invokes the type's `get_queryset(qs, info)` -- the same model-to-Strawberry-type contract and same `get_queryset` visibility hook `DjangoType` implements, so this is required parity with strawberry-django's core type surface.
- `DjangoObjectType` (graphene-django) / `@strawberry_django.type` (strawberry-graphql-django) are the namesake primitive.

#### Architectural posture

- The public shape is intentionally narrow and explicit.

#### Decision

- Deferred Meta keys are rejected, not silently accepted.

#### Note

- core foundational subsystem: `DjangoType` base, Meta validation, scalar/relation conversion, choice enums, type registry, relation resolvers, `get_queryset` hook.
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
[glossary-metaorderset_class]: docs/GLOSSARY.md#metaorderset_class
[glossary-multi-database-cooperation]: docs/GLOSSARY.md#multi-database-cooperation
[glossary-optimizerhint]: docs/GLOSSARY.md#optimizerhint
[glossary-orderset]: docs/GLOSSARY.md#orderset
[glossary-relatedfilter]: docs/GLOSSARY.md#relatedfilter
[glossary-relatedorder]: docs/GLOSSARY.md#relatedorder
[glossary-safe-wrap-connection-method]: docs/GLOSSARY.md#safe_wrap_connection_method
[glossary-strawberry-config]: docs/GLOSSARY.md#strawberry_config

<!-- docs/SPECS/ -->
[spec-015]: docs/SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-020]: docs/SPECS/spec-020-list_field-0_0_7.md
[spec-023]: docs/SPECS/spec-023-multi_db-0_0_7.md
[spec-027]: docs/SPECS/spec-027-filters-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[apps]: django_strawberry_framework/apps.py
[converters]: django_strawberry_framework/types/converters.py
[django-patches]: django_strawberry_framework/_django_patches.py
[filters]: django_strawberry_framework/filters/
[orders]: django_strawberry_framework/orders/
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
[fakeshop-test-library]: examples/fakeshop/test_query/test_library_api.py
[kanban-app]: examples/fakeshop/apps/kanban/
[fakeshop-test-multi-db]: examples/fakeshop/test_query/test_multi_db.py
[settings]: examples/fakeshop/config/settings.py
[test-library-api]: examples/fakeshop/test_query/test_library_api.py
[test-scalars-api]: examples/fakeshop/test_query/test_scalars_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
