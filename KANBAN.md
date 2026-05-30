# django-strawberry-framework Kanban

Last refreshed: 2026-05-28

This board summarizes what is shipped, what has recently landed, and what remains to finish based on the current code, tests, docs, and release-readiness notes. It is intentionally written as a project-management view: each card has a status, priority, scope, and a practical definition of done.

## Card ID format

Every card uses the form `<STATUS>[-<MILESTONE>]-NNN-X.Y.Z`:

- `<STATUS>` — the column the card lives in: `TODO` (committed to a milestone, not yet active), `WIP` (actively being worked), `BLOCKED` (waiting on a dependency), or `DONE` (shipped). Updated when the card moves between columns.
- `<MILESTONE>` *(optional)* — the development phase the card lives in while it's still pre-shipping: `ALPHA` (pre-`0.1.0`), `BETA` (post-`0.1.0` / pre-`1.0.0`), or `STABLE` (post-`1.0.0`). Used on `TODO`, `WIP`, and `BLOCKED` cards. The two release cards themselves are tagged with the phase they usher in: `TODO-BETA-037-0.1.0` is the alpha → beta cut-over and `TODO-STABLE-046-1.0.0` is the beta → stable cut-over. **Dropped when the card ships** — `DONE` cards use the bare `DONE-NNN-X.Y.Z` form (no milestone segment). The card's version tag (`X.Y.Z`) already encodes which phase the shipment belongs to, and the bare form keeps the shipped-card cluster compact and uniform across the package's history.
- `NNN` — a 3-digit sequence number indicating the order the card was completed (`DONE` cards) or is planned to be completed (every other card, ordered by planned ship version, ties broken by intra-version dependency order). **Unlike status, milestone, and version, this number is not stable** — it is recomputed whenever a card's position in the shipping sequence changes (reordered, new card inserted between two existing cards, version-tag bumped). Use the card title, not the NNN, when referencing a card from long-lived documents.
- `X.Y.Z` — the package version the card shipped in (Done cards) or is planned to ship in (everything else). Alpha cards span `0.0.6` through `0.0.12` leading up to `0.1.0`; Beta cards span `0.1.1` through `0.1.6` leading up to `1.0.0`. The `0.1.0` and `1.0.0` tags are reserved for the two release cards themselves. Anything beyond `1.0.0` lives in [`BACKLOG.md`][backlog], not here.

For install, local development, testing, and the canonical documentation map, start from [`README.md`][readme].

## Relative size

Every card carries a `Relative size:` estimate on a five-point
T-shirt scale **anchored to the shipped Filtering subsystem (`DONE-021-0.0.8`) =
XL** — the largest card the package has shipped (a 1,290-line spec plus a full
six-layer lazy-resolution pipeline). The size is a planning estimate of build
effort, not a commitment:

- **XS** — trivial / mechanical; ≲½ day; one small module or a bookkeeping edit; no spec.
- **S** — small; ~1 day; one module + tests; light or no spec.
- **M** — moderate; a few days; multi-file, a real spec, a handful of design decisions.
- **L** — large subsystem; ~a week; new subpackage, full spec, broad integration.
- **XL** — very large subsystem at `DONE-021-0.0.8` scale.

On `DONE` cards the size is a retrospective estimate of the build effort the
card represented; their `Priority` and `Severity` tags are likewise best-effort
retrospective values (neither was tracked while the work was active). Cards in
the To-Do-Alpha column and the Done column carry the full tag block (`Priority`
/ `Parity` / `Severity` / `Status` / `Relative size`), with any explanatory text
demoted to a bullet under its label.

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
- 0.0.4 foundation slice has shipped (card `DONE-006-0.0.4`):
  - `DjangoTypeDefinition` is the canonical per-type metadata object stashed at `cls.__django_strawberry_definition__`, with forward-reserved slots (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`) ready for Layer 3 to populate.
  - `finalize_django_types()` resolves pending relations, attaches generated relation resolvers, and runs `strawberry.type(cls, ...)` for every collected type. Re-exported from `django_strawberry_framework` and `django_strawberry_framework.types`.
  - Pending-relation registry (`PendingRelation`, `add_pending_relation`, `iter_pending_relations`, `discard_pending`, `is_finalized`, `mark_finalized`, extended `clear`) supports definition-order-independent FK / reverse FK / forward + reverse OneToOne / forward + reverse M2M / multi-cycle graphs.
  - Manual relation override contract (`consumer_annotated_relation_fields` vs `consumer_assigned_relation_fields`): annotation-only overrides keep the generated relation resolver; `strawberry.field(resolver=...)` / `@strawberry.field` overrides suppress it.
  - Fail-loud unresolved-target finalization error names source model, source field, and target model.
  - OneToOne / M2M cardinality coverage now uses the real `library` example app; the old `tests.fixtures.apps.TestsCardinalityConfig` fixture app has been removed.
- 0.0.5 shipped after this foundation slice and is recorded separately as `DONE-011-0.0.5`.
- 0.0.6 shipped as the patch closing the foundation phase: `DONE-012-0.0.6` (`FieldMeta` consolidation), `DONE-013-0.0.6` (deferred scalar conversions), `DONE-014-0.0.6` (multiple `DjangoType`s per model with `Meta.primary`), and `DONE-015-0.0.6` (consumer override semantics for scalar fields).
- Test suite structure has caught up with the package shape:
  - `tests/optimizer/` covers `extension.py`, `walker.py`, `plans.py`, `hints.py`, `field_meta.py`, and `definition_order.py`.
  - `tests/types/` covers `base.py`, `converters.py`, `resolvers.py`, `definition_order.py`, and `definition_order_schema.py`.
  - `tests/test_registry.py` covers idempotency / phase-1 atomicity / phase-2/3 partial-mutation / pending-set cleanup / class-mutation residue.
  - `tests/utils/` covers utility modules.
  - The full suite runs through `uv run pytest`, including package tests, example-project tests, and live `/graphql/` HTTP tests, with 100% package coverage.

### In progress

- `0.0.7` shipped 2026-05-27 with seven cards: `DONE-016-0.0.7` (`DjangoListField`), `DONE-017-0.0.7` (`apps.py` and Django app config), `DONE-018-0.0.7` (schema-export management command), `DONE-019-0.0.7` (multi-database cooperation contract), `DONE-046-0.0.7` (Django Trac #37064 hardening + `safe_wrap_connection_method` consumer helper), `DONE-047-0.0.7` (warning-free scalar registration via `StrawberryConfig.scalar_map`), and `DONE-048-0.0.7` (scalar conversion end-to-end coverage in the fakeshop example with the new `apps.scalars` app plus a `BigIntegerField` on `apps.library.Patron`). Full card detail lives under the `## Done` board column below. Tag: `0.0.7` at commit `72f6cd9`.
- `0.0.8` is the active patch. `WIP-ALPHA-022-0.0.8` (Ordering subsystem) is queued for next implementation alongside `WIP-ALPHA-023-0.0.8` (`DjangoType` consumer-DX cleanup pass); the Filtering subsystem shipped as `DONE-021-0.0.8`. The remaining two cards stay grouped under the same column for the joint `0.0.8` cut. The last `0.0.8` card to ship owns the version bump from `0.0.7` per Decision 10 of `docs/SPECS/spec-016-list_field-0_0_7.md`.
- Strategic differentiation roadmap (post-`0.0.6`) captured in [`BACKLOG.md`][backlog]: items neither `graphene-django` nor `strawberry-graphql-django` ship cleanly that should land on the roadmap once parity items are shipped.

### Still not implemented

- Layer 3 public subsystems are still planned only:
  - `orders/`
  - `aggregates/`
  - `fieldset.py`
  - `connection.py`
  - `permissions.py`
  - `utils/queryset.py`
- Layer 3 still needs the original goal-level contract: declarative filtering, ordering, aggregation, and permission rules configured through `Meta`, composable with each other, and introspectable from one type definition.
- Several DjangoType contract gaps remain:
  - stable choice-enum naming override, because the first `DjangoType` to read a choice field currently wins the enum name
- Optimizer follow-up ideas remain outside the shipped B1-B8 surface:
  - model-property / cached-property optimization hints
  - connection-aware planning for Relay-style nested connection selections (new card `TODO-ALPHA-026-0.0.9`)
- Test/example hygiene items surfaced by the foundation slice review have moved into the testing-shift docs and backlog: package-level override tests intentionally pin Strawberry internals while HTTP tests pin the consumer-visible override contract ([`BACKLOG.md`][backlog] item 38).
- The library GraphQL schema is real and wired into the project schema; the product-catalog Layer 3 aspirational schema block remains commented until those subsystems ship.

## Board columns

## In progress

Two WIP cards remain in the `0.0.8` cohort after the Filtering subsystem shipped as `DONE-021-0.0.8`: `WIP-ALPHA-022-0.0.8 — Ordering subsystem` and `WIP-ALPHA-023-0.0.8 — `DjangoType` consumer-DX cleanup pass` are queued under the same column so the patch-level scope is visible at a glance and the cards stay grouped for the joint cut (`⚛️&🍓` parity for the Layer-3 read-side plus the consumer-DX cleanup pass). The last `0.0.8` card to ship owns the version bump from `0.0.7` per Decision 10 of `docs/SPECS/spec-016-list_field-0_0_7.md`.

## To Do - Alpha (0.1.0)

Cards required to reach feature parity with both upstreams (`⚛️ graphene-django` and `🍓 strawberry-graphql-django`). Each card targets its own `0.0.x` patch within the road to **0.1.0**. The final card in this column is the `0.1.0` release itself (cleanup, verification, alpha → beta cut-over). Cards in NNN order = planned ship order; dependency and parallelism notes live on each card.

## To Do - Beta (1.0.0)

Cards that complete the django-graphene-filters Layer-3 richness on top of parity (`fields_class`, `aggregate_class`, `search_fields`, plus pre-stable cleanup). Each card targets its own `0.1.x` patch within the road to **1.0.0**. The final card in this column is the `1.0.0` release itself (API freeze, cleanup, verification, beta → stable cut-over). Cards in NNN order = planned ship order.

## Blocked

## Done

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
- Strategic differentiation candidates (features neither `graphene-django` nor `strawberry-graphql-django` ship cleanly) live in [`BACKLOG.md`][backlog]. When a `BACKLOG.md` item is scheduled, promote it to a `TODO-NNN-X.Y.Z` or `TODO-NNN-X.Y.Z` card here and cross-reference back.

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
[spec-021]: docs/spec-021-filters-0_0_8.md

<!-- docs/SPECS/ -->
[spec-011]: docs/SPECS/spec-011-relay_interfaces-0_0_5.md
[spec-016]: docs/SPECS/spec-016-list_field-0_0_7.md
[spec-019]: docs/SPECS/spec-019-multi_db-0_0_7.md

<!-- docs/builder/ -->
[build-020-scalar-map-helper-0-0-7]: docs/builder/build-020-scalar_map_helper-0_0_7.md

<!-- django_strawberry_framework/ -->
[apps]: django_strawberry_framework/apps.py
[converters]: django_strawberry_framework/types/converters.py
[django-patches]: django_strawberry_framework/_django_patches.py
[filters]: django_strawberry_framework/filters/
[plans]: django_strawberry_framework/optimizer/plans.py
[resolvers]: django_strawberry_framework/types/resolvers.py
[test-init]: django_strawberry_framework/test/__init__.py
[wrap]: django_strawberry_framework/test/_wrap.py

<!-- tests/ -->
[test-converters]: tests/types/test_converters.py
[test-multi-db]: tests/optimizer/test_multi_db.py
[test-resolvers]: tests/types/test_resolvers.py

<!-- examples/ -->
[db-shard-b.sqlite3]: examples/fakeshop/db_shard_b.sqlite3
[example-schema]: examples/fakeshop/config/schema.py
[fakeshop-library]: examples/fakeshop/apps/library/
[fakeshop-test-multi-db]: examples/fakeshop/test_query/test_multi_db.py
[settings]: examples/fakeshop/config/settings.py
[test-library-api]: examples/fakeshop/test_query/test_library_api.py
[test-scalars-api]: examples/fakeshop/test_query/test_scalars_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
